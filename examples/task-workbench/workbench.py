"""Standalone target application. Its business state never initializes the AWB Builder journal."""
import argparse
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from awb_core.adapters.app_server import AppServerClient
from awb_core.contracts import AWBError, digest, file_digest, inside, read_json, validate_record, write_json
from awb_core.execution import Budget, execute_node
from awb_core.intelligence import compile_profile, app_server_command


class Workbench:
    def __init__(self, data, profile):
        self.data = Path(data).resolve()
        self.data.mkdir(parents=True, exist_ok=True)
        self.profile = validate_record("profile", profile)
        self.lock, self.clients, self.workers, self.submitted = threading.RLock(), {}, [], set()
        with self.db() as db:
            db.executescript("""
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, version INTEGER NOT NULL, payload TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS versions(task_id TEXT, version INTEGER, payload TEXT, PRIMARY KEY(task_id,version));
              CREATE TABLE IF NOT EXISTS approvals(task_id TEXT, version INTEGER, digest TEXT, actor TEXT, PRIMARY KEY(task_id,version));
              CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, task_id TEXT, version INTEGER, payload TEXT, UNIQUE(task_id,version));
              CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, task_id TEXT, payload TEXT);
            """)
            # Never replay an interrupted effect automatically after process restart.
            for row in db.execute("SELECT payload FROM tasks").fetchall():
                task = json.loads(row[0])
                if task["status"] == "running":
                    task.update(status="needs_human", reason="Previous process exited; inspect attempt artifacts before a new version")
                    self._save(db, task)
            for row in db.execute("SELECT id,payload FROM attempts").fetchall():
                attempt = json.loads(row[1])
                if attempt["status"] == "running":
                    attempt.update(status="interrupted", reason="Process restart; inspect artifacts, no automatic retry")
                    db.execute("UPDATE attempts SET payload=? WHERE id=?", (json.dumps(attempt), row[0]))

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.data / "workbench.sqlite", timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _save(self, db, task):
        value = json.dumps(task, ensure_ascii=False)
        db.execute("INSERT OR REPLACE INTO tasks VALUES (?,?,?)", (task["id"], task["version"], value))

    def task(self, task_id):
        with self.db() as db:
            row = db.execute("SELECT payload FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise AWBError("missing", "Unknown task")
        return json.loads(row[0])

    def tasks(self):
        with self.db() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM tasks ORDER BY rowid DESC")]

    def workspace(self, task_id):
        task = self.task(task_id)
        return inside(self.data, f"tasks/{task['id']}/v{task['version']}")

    def _version(self, db, task_id, version, goal, expected, inputs):
        if not isinstance(goal, str) or not goal.strip() or not isinstance(expected, dict) or not expected or not isinstance(inputs, str):
            raise AWBError("task", "Provide a goal, independent expected JSON and text input")
        workspace = inside(self.data, f"tasks/{task_id}/v{version}")
        workspace.mkdir(parents=True, exist_ok=False)
        (workspace / "input.txt").write_text(inputs, encoding="utf-8")
        task = {"id": task_id, "version": version, "goal": goal, "expected": expected,
                "input_sha256": file_digest(workspace / "input.txt"), "status": "draft", "thread_id": None}
        self._save(db, task)
        db.execute("INSERT INTO versions VALUES (?,?,?)", (task_id, version, json.dumps(task, ensure_ascii=False)))
        return task

    def create_task(self, goal, expected, inputs=""):
        with self.lock, self.db() as db:
            return self._version(db, uuid.uuid4().hex, 1, goal, expected, inputs)

    def update_task(self, task_id, version, goal, expected, inputs=""):
        with self.lock, self.db() as db:
            current = self.task(task_id)
            if current["version"] != version or current["status"] == "running":
                raise AWBError("version", "Task version is stale or executing")
            return self._version(db, task_id, version + 1, goal, expected, inputs)

    def _binding(self, task):
        path = self.workspace(task["id"]) / "input.txt"
        if file_digest(path) != task["input_sha256"]:
            raise AWBError("drift", "Input drift invalidates approval; create a new task version")
        return digest({"id": task["id"], "version": task["version"], "goal": task["goal"], "expected": task["expected"],
                       "input_sha256": task["input_sha256"], "profile": self.profile})

    def approve(self, task_id, version, actor="local-user"):
        with self.lock, self.db() as db:
            task = self.task(task_id)
            if task["version"] != version or task["status"] != "draft" or not actor:
                raise AWBError("approval", "Approval requires the current draft version and explicit actor")
            binding = self._binding(task)
            db.execute("INSERT OR REPLACE INTO approvals VALUES (?,?,?,?)", (task_id, version, binding, actor))
            task["status"] = "approved"
            self._save(db, task)
        return task

    def attempts(self, task_id):
        with self.db() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM attempts WHERE task_id=? ORDER BY rowid", (task_id,))]

    def event(self, task_id, payload):
        with self.db() as db:
            db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (task_id, json.dumps(payload, ensure_ascii=False)))

    def events(self, task_id):
        with self.db() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM events WHERE task_id=? ORDER BY id", (task_id,))]

    def _codex_executor(self, task, workspace, logs):
        config = compile_profile(self.profile)
        if config["mode"] not in {"mixed", "noninteractive"}:
            raise AWBError("configuration", "This profile has no noninteractive intelligence")
        config.update(id="task-execution", cwd=str(workspace), side_effect="unknown", input_files=["input.txt"],
                      output_schema={"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"], "additionalProperties": False})
        prompt = {"instruction": task["goal"], "input": "input.txt", "output": "result.json", "expected": task["expected"],
                  "constraints": "Create the real result.json. Preserve input.txt. Stay within this workspace. No new installs, services or credentials."}
        return execute_node(config, prompt, {"workspace": logs, "project": workspace}, Budget(self.profile["budget"]["max_calls"], self.profile["budget"]["max_seconds"]))

    def execute(self, task_id, executor=None):
        with self.lock, self.db() as db:
            task = self.task(task_id)
            previous = db.execute("SELECT id FROM attempts WHERE task_id=? AND version=?", (task_id, task["version"])).fetchone()
            if previous:
                raise AWBError("attempt", "This task version already has an attempt; preserve it and create a new version")
            approval = db.execute("SELECT digest FROM approvals WHERE task_id=? AND version=?", (task_id, task["version"])).fetchone()
            if task["status"] != "approved" or not approval or approval[0] != self._binding(task):
                raise AWBError("approval", "Execution requires approval bound to current inputs, version and profile")
            attempt_id = uuid.uuid4().hex
            attempt = {"id": attempt_id, "task_id": task_id, "version": task["version"], "status": "running", "simulated_executor": executor is not None}
            db.execute("INSERT INTO attempts VALUES (?,?,?,?)", (attempt_id, task_id, task["version"], json.dumps(attempt)))
            task["status"] = "running"
            self._save(db, task)
        workspace, logs = self.workspace(task_id), inside(self.data, f"attempts/{attempt_id}")
        logs.mkdir(parents=True)
        try:
            result = (executor or self._codex_executor)(task, workspace, logs)
            output = inside(workspace, "result.json")
            try:
                output_matches = digest(read_json(output)) == digest(task["expected"])
            except AWBError:
                output_matches = False
            verification = {"output_matches": output_matches, "input_preserved": file_digest(workspace / "input.txt") == task["input_sha256"],
                            "execution_completed": result.get("status") == "completed"}
            attempt.update(status="verified" if all(verification.values()) else "failed", verification=verification,
                           execution_status=result.get("status"), error_code=result.get("error", {}).get("code"),
                           output_sha256=file_digest(output) if output.is_file() else None)
        except (AWBError, OSError, ValueError) as exc:
            attempt.update(status="failed", error_code=getattr(exc, "code", "io"), verification={"execution_completed": False})
        write_json(logs / "attempt.json", attempt)
        with self.lock, self.db() as db:
            db.execute("UPDATE attempts SET payload=? WHERE id=?", (json.dumps(attempt), attempt_id))
            current = self.task(task_id)
            current.update(status=attempt["status"], verification=attempt["verification"])
            self._save(db, current)
        self.event(task_id, {"kind": "execution", "attempt": attempt})
        return attempt

    def submit(self, task_id):
        with self.lock, self.db() as db:
            task = self.task(task_id)
            approval = db.execute("SELECT digest FROM approvals WHERE task_id=? AND version=?", (task_id, task["version"])).fetchone()
            if task_id in self.submitted or task["status"] != "approved" or not approval or approval[0] != self._binding(task):
                raise AWBError("approval", "Submission requires a current, approved task with no pending execution")
            if db.execute("SELECT id FROM attempts WHERE task_id=? AND version=?", (task_id, task["version"])).fetchone():
                raise AWBError("attempt", "This version already has an attempt")
            self.submitted.add(task_id)
        def worker():
            try:
                self.execute(task_id)
            except (AWBError, OSError) as exc:
                self.event(task_id, {"kind": "submission_error", "code": getattr(exc, "code", "io")})
            finally:
                with self.lock:
                    self.submitted.discard(task_id)
        thread = threading.Thread(target=worker, daemon=True)
        self.workers.append(thread)
        thread.start()
        return {"status": "submitted"}

    def discuss(self, task_id, text):
        task = self.task(task_id)
        config = compile_profile(self.profile)
        if config["mode"] not in {"mixed", "interactive"}:
            raise AWBError("configuration", "This profile has no interactive intelligence")
        Budget(self.profile["budget"]["max_calls"], self.profile["budget"]["max_seconds"]).reserve()
        config = config | {"sandbox": "read-only", "workspace_write_authorized": False}
        with self.lock:
            if task_id in self.clients:
                raise AWBError("session", "Discussion is already active; answer its request or wait")
            client = AppServerClient(app_server_command(config), self.workspace(task_id),
                inside(self.data, f"discussions/{uuid.uuid4().hex}"), config)
            # Reserve before starting the asynchronous transport; concurrent callers cannot double-start.
            self.clients[task_id] = client
        def worker():
            started = time.monotonic()
            try:
                with client:
                    thread = client.resume_thread(task["thread_id"]) if task["thread_id"] else client.start_thread()
                    with self.lock, self.db() as db:
                        current = self.task(task_id)
                        current["thread_id"] = thread
                        self._save(db, current)
                    turn = client.start_turn(thread, f"Task: {task['goal']}\nDiscuss only; no implementation or new resource installation.\nUser: {text}")
                    while True:
                        remaining = self.profile["budget"]["max_seconds"] - (time.monotonic() - started)
                        if remaining <= 0:
                            client.interrupt(thread, turn["id"])
                            raise AWBError("budget", "Discussion wall-clock deadline exhausted")
                        event = client.next_event(timeout=remaining)
                        self.event(task_id, event)
                        if event.get("method") == "turn/completed" and event["params"]["turn"]["id"] == turn["id"]:
                            break
            except (AWBError, OSError) as exc:
                self.event(task_id, {"kind": "discussion_error", "code": getattr(exc, "code", "transport")})
            finally:
                with self.lock:
                    self.clients.pop(task_id, None)
        thread = threading.Thread(target=worker, daemon=True)
        self.workers.append(thread)
        thread.start()
        return {"status": "started", "simulated_user": False}

    def respond(self, task_id, request_id, result):
        client = self.clients.get(task_id)
        if not client:
            raise AWBError("approval", "No active discussion request")
        client.respond_approval(request_id, result)
        self.event(task_id, {"kind": "user_reply", "request_id": request_id, "result": result})
        return {"status": "answered"}

    def close(self):
        for client in list(self.clients.values()):
            client.close()


def make_server(app, port=8766):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def reply(self, payload, status=200):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def boundary(self):
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in allowed:
                raise AWBError("policy", "Only loopback Host headers are allowed")
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + host for host in allowed}:
                raise AWBError("policy", "Cross-origin task mutations are denied")
        def do_GET(self):
            try:
                self.boundary()
                if self.path == "/":
                    data = Path(__file__).with_name("index.html").read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                elif self.path == "/api/tasks":
                    self.reply(app.tasks())
                elif self.path == "/api/profile":
                    self.reply({"mode": app.profile["mode"], "model": app.profile["model"], "permissions": app.profile["permissions"], "budget": app.profile["budget"]})
                elif self.path.startswith("/api/events/"):
                    self.reply(app.events(self.path.rsplit("/", 1)[-1]))
                else:
                    self.reply({"error": "Unknown route"}, 404)
            except AWBError as exc:
                self.reply(exc.as_dict(), 403 if exc.code == "policy" else 400)
        def do_POST(self):
            try:
                self.boundary()
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 * 1024 or self.headers.get("Content-Type") != "application/json":
                    raise AWBError("request", "Use JSON request bodies under 1 MiB")
                body = json.loads(self.rfile.read(length))
                if self.path == "/api/tasks":
                    result = app.create_task(body["goal"], body["expected"], body.get("input", ""))
                elif self.path == "/api/update":
                    result = app.update_task(body["id"], body["version"], body["goal"], body["expected"], body.get("input", ""))
                elif self.path == "/api/approve":
                    result = app.approve(body["id"], body["version"])
                elif self.path == "/api/execute":
                    result = app.submit(body["id"])
                elif self.path == "/api/discuss":
                    result = app.discuss(body["id"], body["text"])
                elif self.path == "/api/approval":
                    result = app.respond(body["id"], body["request_id"], body["result"])
                else:
                    self.reply({"error": "Unknown route"}, 404)
                    return
                self.reply(result)
            except (AWBError, KeyError, ValueError) as exc:
                error = exc.as_dict() if isinstance(exc, AWBError) else {"message": "Malformed request"}
                self.reply(error, 403 if isinstance(exc, AWBError) and exc.code == "policy" else 400)
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    app = Workbench(args.data, read_json(args.profile))
    server = make_server(app, args.port)
    print(f"Task workbench: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
