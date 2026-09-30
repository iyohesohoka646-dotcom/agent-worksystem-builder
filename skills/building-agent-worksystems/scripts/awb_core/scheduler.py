import re
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from .contracts import AWBError, digest, file_digest, inside, read_json, write_json
from .execution import Budget, execute_node, preflight, can_replay, dependency_hashes
from .intent import write_handoff
from .locking import project_lock, Cancellation, mutation


def validate_graph(graph):
    nodes = graph.get("nodes", [])
    if not nodes or len(nodes) > 100:
        raise AWBError("graph", "A graph requires 1–100 nodes")
    ids = [n.get("id", "") for n in nodes]
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", key) for key in ids) or len({x.lower() for x in ids}) != len(ids):
        raise AWBError("graph", "Node identifiers must be safe and unique")
    dependencies = {n["id"]: set(n.get("after", [])) for n in nodes}
    for node in nodes:
        if not dependencies[node["id"]] <= set(ids):
            raise AWBError("graph", "Unknown dependency")
        repeat = node.get("repeat", 1)
        if type(repeat) is not int or not 1 <= repeat <= 10:
            raise AWBError("graph", "Node repetition is bounded to 1–10")
        if node.get("when") and node["when"].get("node") not in dependencies[node["id"]]:
            raise AWBError("graph", "Branch condition must refer to a direct dependency")
    completed = set()
    while len(completed) < len(ids):
        ready = {key for key, deps in dependencies.items() if key not in completed and deps <= completed}
        if not ready:
            raise AWBError("graph", "Graph contains a cycle")
        completed |= ready
    return graph


def plan_from_selection(selection, catalog):
    nodes = []
    for step in selection.get("steps", []):
        if set(step) - {"id", "after"} or step.get("id") not in catalog:
            raise AWBError("policy", "Planner requested an unapproved node or argument")
        nodes.append(dict(catalog[step["id"]]) | {"after": step.get("after", [])})
    return validate_graph({"nodes": nodes})


@mutation
def run_graph(store, graph, task, max_calls, max_seconds, concurrency=1, run_id=None):
    validate_graph(graph)
    if type(concurrency) is not int or not 1 <= concurrency <= 8:
        raise AWBError("graph", "Concurrency must be between one and eight")
    context = {"offline": store.goal()["offline"]}
    for node in graph["nodes"]:
        preflight(node, context)
    if run_id is None:
        run = store.create("run", {"workflow": "graph", "status": "running", "goal_revision": store.goal()["revision"],
                                  "graph": graph, "task": task, "binding": digest({"graph": graph, "task": task}),
                                  "max_calls": max_calls, "remaining_seconds": max_seconds, "concurrency": concurrency,
                                  "calls_reserved": 0, "nodes": {}, "peak_concurrency": 0, "reused_nodes": 0})
        run_id = run["id"]
    with project_lock(store, run_id):
        return _run(store, run_id, graph, task, max_calls, concurrency)


def _run(store, run_id, graph, task, max_calls, concurrency):
    run = store.get(run_id)
    if run.get("workflow") != "graph" or run["goal_revision"] != store.goal()["revision"] or run["binding"] != digest({"graph": graph, "task": task}):
        raise AWBError("drift", "Graph, task or goal changed; create a new run")
    if max_calls != run["max_calls"] or concurrency != run["concurrency"]:
        raise AWBError("budget", "Resuming cannot silently change the approved budget or concurrency")
    if run["status"] == "cancelled":
        raise AWBError("run", "Cancelled run cannot be replayed")
    if run["remaining_seconds"] <= 0:
        return store.update(run_id, run["revision"], {"status": "budget_exhausted"})
    started = time.monotonic()
    nodes = {n["id"]: n for n in graph["nodes"]}
    done, active, reservations, results = set(), {}, {}, dict(run["nodes"])
    cancel = Cancellation(store, run_id)
    reused, stop_reason = 0, None
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        while len(done) < len(nodes):
            done_before = len(done)
            if cancel.is_set():
                stop_reason = "cancelled"
            remaining = run["remaining_seconds"]
            for key, node in nodes.items():
                if key in done or key in active.values() or not set(node.get("after", [])) <= done:
                    continue
                parent_results = {parent: results[parent].get("result") for parent in node.get("after", [])}
                dependencies = dependency_hashes(node, store.project)
                binding = digest({"node": node, "parents": parent_results, "task": task, "files": dependencies})
                previous = results.get(key)
                if previous and previous.get("fingerprint") == binding and previous.get("status") == "completed":
                    path = inside(store.project, previous["output_path"])
                    if path.is_file() and file_digest(path) == previous["sha256"]:
                        done.add(key)
                        reused += 1
                        continue
                if previous and previous.get("status") != "skipped" and not can_replay(node):
                    stop_reason = "needs_human"
                    break
                condition = node.get("when")
                if any(results[p]["status"] == "skipped" for p in node.get("after", [])) or (condition and (parent_results[condition["node"]] or {}).get(condition["key"]) != condition["equals"]):
                    results[key] = {"status": "skipped", "fingerprint": binding, "result": None}
                    done.add(key)
                    continue
                required = node.get("repeat", 1) * (1 + node.get("retries", 0))
                if stop_reason or len(active) >= concurrency:
                    continue
                if run["calls_reserved"] + required > max_calls or run["remaining_seconds"] <= 0:
                    stop_reason = "budget_exhausted"
                    continue
                directory = inside(store.project, store.root / "runs" / run_id / "nodes" / key)
                results[key] = {"status": "running", "fingerprint": binding, "result": None}
                allowance = min(node["timeout"] * required, run["remaining_seconds"])
                run = store.update(run_id, run["revision"], {"status": "running", "nodes": results,
                                   "remaining_seconds": run["remaining_seconds"] - allowance,
                                   "calls_reserved": run["calls_reserved"] + required,
                                   "peak_concurrency": max(run["peak_concurrency"], len(active) + 1)})
                future = pool.submit(_node, node, task, parent_results, directory, allowance, store.goal()["offline"], cancel)
                active[future] = key
                reservations[key] = (allowance, time.monotonic())
            if not active:
                if len(done) > done_before and not stop_reason:
                    continue
                break
            finished, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in finished:
                key = active.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    error = exc.as_dict() if isinstance(exc, AWBError) else {"code": "worker", "message": str(exc)}
                    result = {"status": "budget_exhausted" if error["code"] == "budget" else "failed", "error": error, "result": None}
                allowance, launched = reservations.pop(key)
                refund = max(0, allowance - (time.monotonic() - launched))
                result["fingerprint"] = results[key]["fingerprint"]
                path = inside(store.project, store.root / "runs" / run_id / "nodes" / key / "output.json")
                write_json(path, result)
                result.update(output_path=path.relative_to(store.project).as_posix(), sha256=file_digest(path))
                results[key] = result
                if result["status"] == "completed":
                    done.add(key)
                else:
                    stop_reason = result["status"]
                run = store.update(run_id, run["revision"], {"nodes": results, "remaining_seconds": run["remaining_seconds"] + refund})
            if stop_reason and not active:
                break
    status = "completed" if len(done) == len(nodes) else stop_reason or "failed"
    run = store.update(run_id, run["revision"], {"nodes": results, "status": status, "reused_nodes": reused,
                       "remaining_seconds": max(0, run["remaining_seconds"])})
    write_handoff(store)
    return run


def _node(node, task, parents, directory, seconds, offline, cancel):
    previous, result = None, None
    budget = Budget(node.get("repeat", 1) * (1 + node.get("retries", 0)), seconds)
    for iteration in range(node.get("repeat", 1)):
        result = execute_node(node, {"task": task, "upstream": parents, "previous_iteration": previous},
                              {"workspace": directory / str(iteration), "offline": offline, "cancel": cancel}, budget)
        if result["status"] != "completed":
            break
        previous = result["result"]
    return result | {"iterations": iteration + 1}
