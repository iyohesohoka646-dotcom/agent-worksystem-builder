from .contracts import AWBError, write_json
from .generation import rollback_change
from .intent import write_handoff
from .locking import mutation


def stagnation(cycles):
    if len(cycles) >= 2 and cycles[-1].get("hypothesis") == cycles[-2].get("hypothesis") and all(c.get("refuted") for c in cycles[-2:]):
        return "reassess"
    if len(cycles) >= 3 and all(c.get("progress") is False and c.get("uncertainty_reduced") is False for c in cycles[-3:]):
        return "needs_human"
    return "continue"


@mutation
def apply_decision(store, cycle_id, decision):
    actions = {"accept": "accepted", "revise": "implementing", "replace": "rolled_back", "rollback": "rolled_back",
               "wait": "needs_human", "cancel": "cancelled"}
    if decision.get("action") not in actions or not decision.get("reason"):
        raise AWBError("decision", "A decision needs an action and evidence-based reason")
    cycle = store.get(cycle_id)
    if cycle["kind"] != "cycle":
        raise AWBError("decision", "A build cycle is required")
    refs = decision.get("evidence_refs", [])
    change = store.get(cycle["change_id"]) if cycle.get("change_id") else None
    if decision["action"] == "accept" and change:
        if change["status"] != "applied":
            raise AWBError("decision", "Candidate must be applied before acceptance")
        for ref in refs:
            report = store.check_evidence(ref)
            if report["bindings"].get("candidate_digest") != change["candidate_digest"]:
                raise AWBError("evidence", "Evidence belongs to another candidate")
    if decision["action"] in {"rollback", "replace"} and change:
        rollback_change(store, change["id"])
    # Persist the decision before transition; a failed transition stays visibly unaccepted.
    cycle = store.update(cycle_id, cycle["revision"], {"decision": decision})
    cycle = store.record_transition(cycle_id, cycle["revision"], actions[decision["action"]], refs)
    write_handoff(store)
    return cycle
