import sys
import pytest
from test_state import goal


def api():
    try:
        from awb_core.scheduler import run_graph, validate_graph, plan_from_selection
        from awb_core.state import Store
        from awb_core.contracts import AWBError
    except ImportError:
        pytest.fail("Bounded graph scheduling not implemented")
    return run_graph, validate_graph, plan_from_selection, Store, AWBError


def node(name, after=(), delay=0):
    return {"id": name, "backend": "command", "argv": [sys.executable, "-c",
             f"import json,time; time.sleep({delay}); print(json.dumps({{'value': '{name}'}}))"],
            "allowed_executables": [sys.executable], "trusted": True, "after": list(after),
            "timeout": 3, "output_schema": {"type": "object", "required": ["value"]}}


def test_parallel_outputs_are_isolated_and_resume_reuses_results(tmp_path):
    run, _, _, Store, _ = api()
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    graph = {"nodes": [node("a", delay=0.1), node("b", delay=0.1), node("c", ["a", "b"])]}
    result = run(db, graph, {}, max_calls=3, max_seconds=10, concurrency=2)
    assert result["status"] == "completed"
    assert 1 <= result["peak_concurrency"] <= 2
    assert len({r["output_path"] for r in result["nodes"].values()}) == 3
    again = run(db, graph, {}, max_calls=3, max_seconds=10, concurrency=2, run_id=result["id"])
    assert again["calls_reserved"] == result["calls_reserved"]
    assert again["reused_nodes"] == 3


def test_cycles_unknown_dependencies_and_unapproved_planner_tools_are_rejected():
    _, validate, plan, _, error = api()
    for graph in [{"nodes": [node("a", ["b"]), node("b", ["a"])]}, {"nodes": [node("a", ["missing"])]}]:
        with pytest.raises(error):
            validate(graph)
    with pytest.raises(error):
        plan({"steps": [{"id": "shell", "after": []}]}, {"a": node("a")})
    assert plan({"steps": [{"id": "a", "after": []}]}, {"a": node("a")})["nodes"][0]["argv"] == node("a")["argv"]


def test_budget_exhaustion_preserves_completed_node(tmp_path):
    run, _, _, Store, _ = api()
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    graph = {"nodes": [node("a"), node("b", ["a"])]}
    result = run(db, graph, {}, max_calls=1, max_seconds=10)
    assert result["status"] == "budget_exhausted"
    assert result["nodes"]["a"]["status"] == "completed"
    assert "b" not in result["nodes"]


def test_branch_skip_and_bounded_repetition(tmp_path):
    run, _, _, Store, error = api()
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    b = node("b", ["a"]) | {"when": {"node": "a", "key": "value", "equals": "no"}}
    graph = {"nodes": [node("a") | {"repeat": 2}, b]}
    result = run(db, graph, {}, max_calls=3, max_seconds=10)
    assert result["nodes"]["b"]["status"] == "skipped"
    assert result["nodes"]["a"]["iterations"] == 2
    with pytest.raises(error):
        run(db, {"nodes": [node("x") | {"repeat": 999}]}, {}, max_calls=999, max_seconds=10)
