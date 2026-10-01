"""Persisted grill and adaptive exploration. Native host supplies semantic judgment."""
from .contracts import AWBError
from .cycle import stagnation
from .intent import propose_next_action, write_handoff
from .state import contract_payload


def next_action(store, uncertainties=()):
    goal = store.goal()
    budget = goal.get("budget", {})
    for maximum, used in (("max_calls", "used_calls"), ("max_seconds", "used_seconds"), ("max_cycles", "used_cycles")):
        if maximum in budget and budget.get(used, 0) >= budget[maximum]:
            return {"action": "budget_exhausted", "goal_revision": goal["revision"], "reason": f"{maximum} reached; checkpoint retained"}
    for contract in store.list():
        if contract["kind"] in {"architecture", "profile"} and contract["status"] == "needs_human":
            try:
                store.require_contract(contract["id"], contract["kind"])
            except AWBError:
                return {"action": "needs_human", "contract_id": contract["id"], "review_ids": contract.get("review_ids", []),
                        "goal_revision": goal["revision"], "reason": "Resolve the saved consequential decision"}
    issues, facts, reopened = list(uncertainties), {}, set()
    for record in store.list("exploration"):
        question = record["question"]
        if record["status"] == "reopened":
            reopened.add(question["id"])
        if record["status"] in {"decided", "answered"} and record["goal_revision"] == goal["revision"]:
            facts[question["id"]] = record.get("answer", record["decision"])
            continue
        issues.append({"id": question["id"], "impact": question["impact"] * question["uncertainty"],
                       "question": question["text"], "consequential": question["consequential"],
                       "probe": record["strategy"] if question["discoverable"] else None,
                       "reason": record["strategy"]["reason"], "exploration_id": record["id"]})
    current_goal = goal | {"answers": {key: value for key, value in goal.get("answers", {}).items() if key not in reopened}}
    action = propose_next_action(current_goal, {"facts": facts, "stagnation": stagnation(store.list("cycle"))}, issues)
    if action.get("uncertainty_id"):
        item = next(i for i in issues if i["id"] == action["uncertainty_id"])
        action["exploration_id"] = item.get("exploration_id")
    return action


def answer_question(store, entity_id, answer, source):
    record = store.get(entity_id)
    if record["kind"] != "exploration" or not isinstance(answer, dict) or not answer.get("reason"):
        raise AWBError("exploration", "An exploration answer needs a reason and an existing question")
    if source not in {"user", "environment", "experiment"}:
        raise AWBError("exploration", "Inferences do not count as confirmed answers")
    if record["question"]["consequential"] and source != "user":
        raise AWBError("decision", "A consequential choice requires the user's answer")
    payload = contract_payload(record) | {"goal_revision": store.goal()["revision"], "decision": answer,
                                           "answer": {"source": source, "value": answer}}
    result = store.record_contract("exploration", payload, entity_id, record["revision"])
    write_handoff(store)
    return result


def reopen_question(store, entity_id, reason):
    record = store.get(entity_id)
    if record["kind"] != "exploration" or not reason:
        raise AWBError("exploration", "Reopening needs an exploration and observed reason")
    result = store.update(entity_id, record["revision"], {"status": "reopened", "reopen_reason": reason})
    write_handoff(store)
    return result
