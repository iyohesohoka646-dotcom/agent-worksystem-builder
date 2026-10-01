from __future__ import annotations

import json
import hashlib
import re
import sqlite3
import uuid
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .contracts import AWBError, atomic_write, canonical, digest, file_digest, inside, read_json, validate_record, write_json
from .locking import mutation


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier(prefix):
    return f"{prefix}-{uuid.uuid4().hex}"


TRANSITIONS = {
    "evaluating": {"awaiting_approval", "implementing", "needs_human", "cancelled"},
    "awaiting_approval": {"implementing", "needs_human", "cancelled"},
    "implementing": {"verifying", "needs_human", "cancelled", "rolled_back"},
    "verifying": {"deciding", "needs_human", "cancelled"},
    "deciding": {"accepted", "rolled_back", "implementing", "needs_human", "cancelled"},
    "needs_human": {"evaluating", "implementing", "verifying", "deciding", "cancelled"},
    "accepted": set(), "rolled_back": set(), "cancelled": set(),
}

CONTRACT_KINDS = {"architecture", "profile", "exploration"}
RECORD_METADATA = {"id", "kind", "revision", "created_at", "updated_at", "status", "review_ids", "contract_digest", "reopen_reason"}


def contract_payload(record):
    return {k: v for k, v in record.items() if k not in RECORD_METADATA}


class Store:
    def __init__(self, project):
        self.project = Path(project).resolve()
        self.root = inside(self.project, ".worksystem-build")
        self.path = inside(self.project, self.root / "state.sqlite")
        if not self.path.is_file():
            raise AWBError("project", "Project is not initialized; run awb init")
        with self.connection() as db:
            if self.meta(db, "schema_version") != 1:
                raise AWBError("schema", "Unsupported state schema version")
        self.publish_accepted_spec()

    def accepted_spec(self, db=None):
        if db is None:
            with self.connection() as connection:
                return self.accepted_spec(connection)
        return self.meta(db, "accepted_spec") or {"schema_version": 1, "revision": 0, "files": {}}

    def publish_accepted_spec(self):
        spec = self.accepted_spec()
        if not spec["revision"]:
            return
        for path in (self.root / "specs" / (spec["cycle_id"] + ".json"), self.root / "system.spec.json"):
            path = inside(self.project, path)
            current = read_json(path) if path.exists() else None
            if current == spec:
                continue
            known = [c.get("accepted_spec") for c in self.list("cycle") if c.get("accepted_spec")]
            if current is not None and current not in known:
                raise AWBError("drift", "Accepted specification view has unrecognized manual changes")
            write_json(path, spec)

    @classmethod
    def initialize(cls, project, goal):
        goal = validate_record("goal", goal)
        project = Path(project).resolve()
        project.mkdir(parents=True, exist_ok=True)
        root = inside(project, ".worksystem-build")
        if root.exists():
            raise AWBError("project", "Project state already exists")
        root.mkdir()
        with closing(sqlite3.connect(root / "state.sqlite")) as db, db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;
                CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE records(id TEXT PRIMARY KEY, kind TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE history(id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(id, revision));
                CREATE TABLE evidence(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            """)
            for key, value in {"schema_version": 1, "build_id": identifier("build"), "goal_revision": goal["revision"], "goal_digest": digest(goal), "goal_history": {str(goal["revision"]): digest(goal)}}.items():
                db.execute("INSERT INTO meta VALUES (?, ?)", (key, json.dumps(value)))
            write_json(root / "goals" / f"{goal['revision']:06}.json", goal)
            write_json(root / "goal.json", goal)
        return cls(project)

    @contextmanager
    def connection(self, write=False):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            if write:
                db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def meta(db, key):
        row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def goal(self):
        with self.connection() as db:
            revision, expected = self.meta(db, "goal_revision"), self.meta(db, "goal_digest")
            history = self.meta(db, "goal_history") or {str(revision): expected}
        for number, expected_hash in history.items():
            historical = read_json(inside(self.project, self.root / "goals" / f"{int(number):06}.json"))
            if digest(historical) != expected_hash:
                raise AWBError("drift", "Committed goal history has drifted")
        goal = validate_record("goal", read_json(inside(self.project, self.root / "goals" / f"{revision:06}.json")))
        if digest(goal) != expected:
            raise AWBError("drift", "Immutable goal history has drifted")
        mirror = inside(self.project, self.root / "goal.json")
        current = read_json(mirror) if mirror.exists() else None
        if current != goal:
            known = current is not None and digest(current) in history.values()
            if current is not None and not known:
                raise AWBError("drift", "Goal view has manual drift; reconcile before resuming")
            write_json(mirror, goal)
        return goal

    def original_goal(self):
        """Oldest committed request; old projects keep only their actual available history."""
        with self.connection() as db:
            history = self.meta(db, "goal_history") or {str(self.meta(db, "goal_revision")): self.meta(db, "goal_digest")}
        number = min(int(n) for n in history)
        original = read_json(inside(self.project, self.root / "goals" / f"{number:06}.json"))
        if digest(original) != history[str(number)]:
            raise AWBError("drift", "Original goal history has drifted")
        return original

    @mutation
    def update_goal(self, goal, expected_revision):
        goal = validate_record("goal", goal)
        previous = self.goal()
        if goal["revision"] != expected_revision + 1 or goal["id"] != previous["id"]:
            raise AWBError("revision", "Goal revision must increase by one with the same ID")
        with self.connection(write=True) as db:
            if self.meta(db, "goal_revision") != expected_revision:
                raise AWBError("revision", "Stale goal revision")
            target = inside(self.project, self.root / "goals" / f"{goal['revision']:06}.json")
            if target.exists() and read_json(target) != goal:
                raise AWBError("drift", "Uncommitted goal revision exists; reconcile it")
            write_json(target, goal)
            db.execute("UPDATE meta SET value=? WHERE key='goal_revision'", (json.dumps(goal["revision"]),))
            db.execute("UPDATE meta SET value=? WHERE key='goal_digest'", (json.dumps(digest(goal)),))
            history = self.meta(db, "goal_history") or {str(previous["revision"]): digest(previous)}
            history[str(goal["revision"])] = digest(goal)
            db.execute("INSERT OR REPLACE INTO meta VALUES ('goal_history', ?)", (json.dumps(history),))
            for row in db.execute("SELECT payload FROM records WHERE kind IN ('architecture','profile','exploration')").fetchall():
                record = json.loads(row[0])
                record.update(status="reopened" if record["kind"] == "exploration" else "stale",
                              reopen_reason="Goal changed; reconsider affected decisions", revision=record["revision"] + 1)
                self._put(db, record)
        write_json(self.root / "goal.json", goal)
        return goal

    @staticmethod
    def _put(db, record, fresh=False):
        data = canonical(record).decode("utf-8")
        if fresh:
            db.execute("INSERT INTO records VALUES (?, ?, ?, ?)", (record["id"], record["kind"], record["revision"], data))
        else:
            db.execute("UPDATE records SET revision=?, payload=? WHERE id=?", (record["revision"], data, record["id"]))
        db.execute("INSERT INTO history VALUES (?, ?, ?)", (record["id"], record["revision"], data))

    def create(self, kind, payload):
        if kind not in {"cycle", "run", "attempt", "review", "change", "probe"} | CONTRACT_KINDS:
            raise AWBError("schema", "Unknown state entity kind")
        if kind in CONTRACT_KINDS:
            payload = validate_record(kind, payload)
        record = dict(payload) | {"schema_version": 1, "id": identifier(kind), "kind": kind, "revision": 1, "created_at": now()}
        record.setdefault("status", "evaluating" if kind == "cycle" else "pending")
        if kind == "cycle":
            if record["status"] != "evaluating" or not record.get("hypothesis"):
                raise AWBError("state", "A cycle needs a hypothesis and starts evaluating")
            record["goal_revision"] = self.goal()["revision"]
        with self.connection(write=True) as db:
            self._put(db, record, fresh=True)
        return record

    @mutation
    def record_contract(self, kind, payload, entity_id=None, expected_revision=None):
        if kind not in CONTRACT_KINDS:
            raise AWBError("schema", "Unknown construction contract")
        payload = validate_record(kind, contract_payload(payload))
        goal = self.goal()
        if payload["goal_revision"] != goal["revision"]:
            raise AWBError("revision", "Contract requires the current goal revision")
        if kind == "architecture":
            known = {r["id"] for r in goal["requirements"] if r["status"] != "replaced"}
            if {r for a in payload["acceptance"] for r in a["requirement_ids"]} - known:
                raise AWBError("schema", "Architecture acceptance references an unknown requirement")
            if payload["intelligence_profile_id"]:
                p = self.get(payload["intelligence_profile_id"])
                if p["kind"] != "profile" or p["goal_revision"] != goal["revision"]:
                    raise AWBError("revision", "Architecture profile is missing or stale")
        questions = [d["question"] for d in payload.get("decisions", []) if d["consequential"]]
        if kind == "profile":
            questions += [f"Authorize {r['operation']} for {r['id']} from {r['source']}?"
                          for r in payload["resources"] if r["operation"] != "use"]
        status = ("decided" if payload.get("decision") else "open") if kind == "exploration" else "ready"
        binding = digest(payload)
        changes = payload | {"status": "needs_human" if questions else status, "contract_digest": binding, "review_ids": []}
        if entity_id:
            with self.connection(write=True) as db:
                old = self.get(entity_id, db)
                if old["kind"] != kind or old["revision"] != expected_revision:
                    raise AWBError("revision", "Contract update requires its kind and current revision")
                record = changes | {"id": old["id"], "kind": kind, "revision": old["revision"] + 1,
                                    "created_at": old["created_at"], "updated_at": now()}
                self._put(db, record)
        else:
            record = self.create(kind, changes)
        if questions:
            review = self.request_review(record["id"], binding, ["authorize_contract"], {"questions": questions})
            record = self.update(record["id"], record["revision"], {"review_ids": [review["id"]]})
        return record

    def require_contract(self, entity_id, kind):
        record = self.get(entity_id)
        if record["kind"] != kind or record["goal_revision"] != self.goal()["revision"] or record["status"] in {"stale", "reopened"}:
            raise AWBError("revision", "Construction contract is stale or has the wrong kind")
        if digest(contract_payload(record)) != record.get("contract_digest"):
            raise AWBError("drift", "Construction contract changed outside its revisioned interface")
        if record["status"] == "needs_human" and not record.get("review_ids"):
            raise AWBError("decision", "Consequential decision requires a saved user answer")
        for review_id in record.get("review_ids", []):
            answer = self.review_answer(review_id, record["contract_digest"], record["goal_revision"], ["authorize_contract"])
            if not answer or answer.get("approved") is not True:
                raise AWBError("decision", "Consequential decision is unresolved or declined")
        if kind == "architecture" and record.get("intelligence_profile_id"):
            self.require_contract(record["intelligence_profile_id"], "profile")
        return record

    def require_cycle_contracts(self, cycle):
        records = {}
        if cycle.get("architecture_id"):
            records["architecture"] = self.require_contract(cycle["architecture_id"], "architecture")
            selected = records["architecture"]["intelligence_profile_id"]
            if cycle.get("profile_id") and cycle["profile_id"] != selected:
                raise AWBError("configuration", "Cycle profile conflicts with the architecture intelligence profile")
        else:
            selected = cycle.get("profile_id")
        if selected:
            records["profile"] = self.require_contract(selected, "profile")
        return records

    def get(self, entity_id, db=None):
        if db is None:
            with self.connection() as connection:
                return self.get(entity_id, connection)
        row = db.execute("SELECT payload FROM records WHERE id=?", (entity_id,)).fetchone()
        if not row:
            raise AWBError("missing", f"Unknown record: {entity_id}")
        return json.loads(row[0])

    def list(self, kind=None):
        with self.connection() as db:
            rows = db.execute("SELECT payload FROM records" + (" WHERE kind=?" if kind else ""), (kind,) if kind else ())
            return [json.loads(row[0]) for row in rows]

    def history(self, entity_id):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT payload FROM history WHERE id=? ORDER BY revision", (entity_id,))]

    def update(self, entity_id, expected_revision, changes):
        if set(changes) & {"id", "kind", "revision", "schema_version", "created_at"}:
            raise AWBError("state", "Identity fields cannot be changed")
        with self.connection(write=True) as db:
            record = self.get(entity_id, db)
            if record["revision"] != expected_revision:
                raise AWBError("revision", "Stale record revision")
            if record["kind"] == "cycle" and "status" in changes:
                raise AWBError("state", "Use record_transition for cycle status")
            record.update(changes)
            record["revision"] += 1
            self._put(db, record)
        return record

    @mutation
    def record_transition(self, entity_id, expected_revision, transition, evidence_refs):
        self.goal()
        if transition in {"implementing", "accepted"}:
            candidate = self.get(entity_id)
            self.require_cycle_contracts(candidate)
        with self.connection(write=True) as db:
            record = self.get(entity_id, db)
            if record["revision"] != expected_revision:
                raise AWBError("revision", "Stale record revision")
            if record["kind"] != "cycle" or transition not in TRANSITIONS.get(record["status"], set()):
                raise AWBError("state", "Illegal cycle transition")
            if transition == "accepted":
                goal_revision = self.meta(db, "goal_revision")
                if not evidence_refs or record["goal_revision"] != goal_revision:
                    raise AWBError("evidence", "Acceptance requires current goal-bound evidence")
                for ref in evidence_refs:
                    report = self.check_evidence(ref, db)
                    if report["entity_id"] != entity_id or report["bindings"].get("goal_revision") != goal_revision or not report["passed"]:
                        raise AWBError("evidence", "Acceptance evidence failed or belongs to another cycle")
                    for kind in ("architecture", "profile"):
                        if record.get(kind + "_id") and report["bindings"].get(kind + "_id") != record[kind + "_id"]:
                            raise AWBError("evidence", "Acceptance evidence belongs to another construction contract")
                if record.get("change_id"):
                    change = self.get(record["change_id"], db)
                    current = self.accepted_spec(db)
                    if change["status"] != "applied" or change.get("baseline_spec_revision", 0) != current["revision"]:
                        raise AWBError("revision", "Candidate is unapplied or based on a stale accepted specification")
                    for ref in evidence_refs:
                        if self.check_evidence(ref, db)["bindings"].get("candidate_digest") != change["candidate_digest"]:
                            raise AWBError("evidence", "Acceptance evidence is not bound to this candidate")
                    files = dict(change["baseline"].get("files", {}))
                    for entry in change["entries"]:
                        if entry["after_hash"] is None:
                            files.pop(entry["path"], None)
                        else:
                            files[entry["path"]] = entry["after_hash"]
                    spec = {"schema_version": 1, "revision": current["revision"] + 1,
                            "cycle_id": entity_id, "goal_revision": goal_revision, "files": files}
                    record["accepted_spec"] = spec
                    db.execute("INSERT OR REPLACE INTO meta VALUES ('accepted_spec', ?)", (canonical(spec).decode(),))
            record.update(status=transition, revision=record["revision"] + 1, evidence_refs=list(evidence_refs), updated_at=now())
            self._put(db, record)
        if transition == "accepted":
            self.publish_accepted_spec()
        return record

    def add_evidence(self, entity_id, artifacts, checks, bindings, expected_hashes=None):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", entity_id):
            raise AWBError("evidence", "Invalid evidence entity identifier")
        if not checks or any(type(v) is not bool for v in checks.values()):
            raise AWBError("evidence", "Evidence needs explicit boolean checks")
        report = {"schema_version": 1, "id": identifier("evidence"), "entity_id": entity_id, "bindings": bindings,
                  "checks": checks, "passed": all(checks.values()), "artifacts": [], "created_at": now()}
        for index, path in enumerate(artifacts):
            path = inside(self.project, path)
            if not path.is_file():
                raise AWBError("evidence", "Evidence artifact is missing")
            snapshot = inside(self.project, self.root / "evidence" / entity_id / report["id"] / f"{index:04}.bin")
            content = path.read_bytes()
            observed = hashlib.sha256(content).hexdigest()
            name = path.relative_to(self.project).as_posix()
            if expected_hashes is not None and expected_hashes.get(name) != observed:
                raise AWBError("evidence", "Artifact changed after verification", path=name)
            atomic_write(snapshot, content)
            report["artifacts"].append({"path": path.relative_to(self.project).as_posix(), "sha256": file_digest(snapshot),
                                        "snapshot": snapshot.relative_to(self.project).as_posix()})
        if not report["artifacts"]:
            raise AWBError("evidence", "Evidence needs at least one artifact")
        target = inside(self.project, self.root / "evidence" / entity_id / f"{report['id']}.json")
        write_json(target, report)
        with self.connection(write=True) as db:
            db.execute("INSERT INTO evidence VALUES (?, ?)", (report["id"], canonical(report).decode()))
        return report

    def check_evidence(self, evidence_id, db=None):
        if db is None:
            with self.connection() as connection:
                return self.check_evidence(evidence_id, connection)
        row = db.execute("SELECT payload FROM evidence WHERE id=?", (evidence_id,)).fetchone()
        if not row:
            raise AWBError("evidence", "Unknown evidence")
        report = json.loads(row[0])
        from .verification import check_verifier_binding
        check_verifier_binding(report["bindings"])
        for dependency, expected in report["bindings"].get("execution_dependencies", {}).items():
            if not Path(dependency).is_file() or file_digest(Path(dependency)) != expected:
                raise AWBError("evidence", "Execution dependency drifted; revalidation required")
        for kind in ("architecture", "profile"):
            key = kind + "_id"
            if report["bindings"].get(key):
                contract = self.get(report["bindings"][key], db)
                if contract.get("contract_digest") != report["bindings"][kind + "_digest"] or contract.get("status") in {"stale", "reopened"}:
                    raise AWBError("evidence", f"Bound {kind} contract changed; revalidation required")
        for absent in report["bindings"].get("absent_paths", []):
            if inside(self.project, absent).exists():
                raise AWBError("evidence", "An expected absent evidence target was recreated")
        verifier_hash = report["bindings"].get("verifier_sha256")
        if verifier_hash and file_digest(Path(__file__).with_name("verification.py")) != verifier_hash:
            raise AWBError("evidence", "Verifier changed; evidence requires revalidation")
        path = inside(self.project, self.root / "evidence" / report["entity_id"] / f"{evidence_id}.json")
        if read_json(path) != report:
            raise AWBError("evidence", "Evidence report has drifted")
        for artifact in report["artifacts"]:
            if artifact.get("snapshot"):
                snapshot = inside(self.project, artifact["snapshot"])
                if not snapshot.is_file() or file_digest(snapshot) != artifact["sha256"]:
                    raise AWBError("evidence", "Historical evidence snapshot has drifted")
            path = inside(self.project, artifact["path"])
            if not path.is_file() or file_digest(path) != artifact["sha256"]:
                raise AWBError("evidence", "Evidence artifact is missing or has drifted")
        return report

    def request_review(self, entity_id, input_digest, actions, question):
        return self.create("review", {"entity_id": entity_id, "input_digest": input_digest, "goal_revision": self.goal()["revision"],
                                      "actions": actions, "question": question, "status": "needs_human"})

    def approve(self, review_id, answer, actor):
        self.goal()
        with self.connection(write=True) as db:
            record = self.get(review_id, db)
            if record["kind"] != "review" or record["status"] != "needs_human":
                raise AWBError("approval", "Review is not pending")
            if record["goal_revision"] != self.meta(db, "goal_revision"):
                raise AWBError("approval", "stale approval request")
            if not actor or not isinstance(answer, dict):
                raise AWBError("approval", "An explicit actor and structured answer are required")
            record.update(status="approved", answer=answer, actor=actor, revision=record["revision"] + 1)
            self._put(db, record)
        return record

    def review_answer(self, review_id, input_digest, goal_revision, actions=None):
        record = self.get(review_id)
        if record["kind"] != "review" or record["input_digest"] != input_digest or record["goal_revision"] != goal_revision:
            raise AWBError("approval", "stale approval binding")
        if actions is not None and record["actions"] != actions:
            raise AWBError("approval", "stale approval action binding")
        return record.get("answer") if record["status"] == "approved" else None
