import json
import pytest
from test_state import goal


def api():
    try:
        from awb_core.materials import run_materials, resume_materials
        from awb_core.verification import verify_materials
        from awb_core.state import Store
        from awb_core.contracts import AWBError
    except ImportError:
        pytest.fail("Material workflow not implemented")
    return run_materials, resume_materials, verify_materials, Store, AWBError


def inputs(tmp_path):
    folder = tmp_path / "输入 材料"
    folder.mkdir()
    (folder / "研究.md").write_text("研究发现：实验结果需要复核。", encoding="utf-8")
    (folder / "步骤.txt").write_text("操作步骤：打开目录，然后运行程序。", encoding="utf-8")
    (folder / "混合.txt").write_text("研究方法包括以下操作步骤。", encoding="utf-8")
    return folder


def test_materials_wait_for_review_and_resume_without_reclassifying(tmp_path):
    run, resume, verify, Store, _ = api()
    db = Store.initialize(tmp_path, goal())
    folder = inputs(tmp_path)
    result = run(db, folder)
    assert result["status"] == "needs_human"
    assert len(result["items"]) == 3
    review = next(r for r in db.list("review") if r["status"] == "needs_human")
    db.approve(review["id"], {"category": "research"}, "test-user")
    result = resume(Store(tmp_path), result["id"])
    assert result["status"] == "completed"
    assert result["classification_count"] == 3
    assert result["model_calls"] == 0
    assert verify(db, result["id"])["passed"]
    records = [json.loads(line) for line in (tmp_path / result["outputs"]["jsonl"]).read_text(encoding="utf-8").splitlines()]
    assert {r["category"] for r in records} == {"research", "procedure"}
    assert (folder / "混合.txt").read_text(encoding="utf-8") == "研究方法包括以下操作步骤。"


def test_changed_input_and_goal_invalidate_resume(tmp_path):
    run, resume, _, Store, error = api()
    db = Store.initialize(tmp_path, goal())
    folder = inputs(tmp_path)
    result = run(db, folder)
    (folder / "混合.txt").write_text("different", encoding="utf-8")
    with pytest.raises(error, match="changed"):
        resume(db, result["id"])


def test_corrupt_export_is_detected(tmp_path):
    run, resume, verify, Store, error = api()
    db = Store.initialize(tmp_path, goal())
    folder = inputs(tmp_path)
    result = run(db, folder)
    for r in db.list("review"):
        db.approve(r["id"], {"category": "research"}, "user")
    result = resume(db, result["id"])
    (tmp_path / result["outputs"]["jsonl"]).write_text('{}\n', encoding="utf-8")
    assert verify(db, result["id"])["passed"] is False


def test_invalid_human_answer_does_not_complete_run(tmp_path):
    run, resume, _, Store, error = api()
    db = Store.initialize(tmp_path, goal())
    result = run(db, inputs(tmp_path))
    db.approve(db.list("review")[0]["id"], {"category": "invented"}, "user")
    with pytest.raises(error, match="category"):
        resume(db, result["id"])


def test_source_quote_and_semantic_reference_are_independently_checked(tmp_path):
    run, resume, verify, Store, _ = api()
    db = Store.initialize(tmp_path, goal())
    result = run(db, inputs(tmp_path))
    db.approve(db.list("review")[0]["id"], {"category": "other"}, "user")
    result = resume(db, result["id"])
    expected = {"混合.txt": "research", "研究.md": "research", "步骤.txt": "procedure"}
    report = verify(db, result["id"], expected)
    assert report["checks"]["reference_categories"] is False
    assert report["checks"]["source_quotes"] is True
    assert report["passed"] is False
