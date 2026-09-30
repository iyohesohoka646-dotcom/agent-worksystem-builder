import pytest

from awb_core.contracts import AWBError, validate_record


def test_public_node_contract_validates_replay_authority():
    node = {"id": "work", "backend": "command", "timeout": 2, "output_schema": {"type": "object"}, "side_effect": "none"}
    assert validate_record("node", node) == node
    with pytest.raises(AWBError):
        validate_record("node", node | {"side_effect": "idempotent"})
    with pytest.raises(AWBError):
        validate_record("node", node | {"id": "../escape"})
    assert validate_record("node", node | {"side_effect": "idempotent", "idempotency_key": "charge-42"})


def test_public_result_contract_rejects_unrecognized_completion():
    result = {"schema_version": 1, "attempt_id": "attempt-1", "node_id": "work", "backend": "command",
              "status": "completed", "result": {"ok": True}, "verification": "unverified", "usage": {"cost": None},
              "logs": {"stdout": "attempts/a/stdout.log", "stderr": "attempts/a/stderr.log"}}
    assert validate_record("result", result) == result
    with pytest.raises(AWBError):
        validate_record("result", result | {"status": "model_claims_success"})
