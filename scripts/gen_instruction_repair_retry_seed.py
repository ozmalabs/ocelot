#!/usr/bin/env python3
"""Emit seeds/instruction_repair_retry.json (tranche 6): AGENT-INITIATED retry.

The graph decides, the daemon hook executes (the conversation_steering
precedent). `irr_request_retry` marks a promoted instruction SelfConcern
`retry_requested=1` when, for its capability key, the agent's own experiments
have produced more non-supported verdicts (refuted/inconclusive) than retries
already requested, none is supported, none is still requested/running, and
retries < InstructionRetryPolicy.max_retries. `jabberwock_daemon._concern_tick`
executes a marked concern by the existing teardown + re-promote, then clears
the mark. A retry asks the SAME held cue_route_pick, which excludes routes
already refuted/inconclusive for the verb, so each retry tries a new route;
when none remains the builder abstains and the loop stops on its own.

v1.1.0 (tranche 7): the concern kinds a retry applies to are policy DATA
(`concern_kinds`, default ["instruction"] -- unchanged behaviour). Adding
"reported" opts a reported concern into the same retry; the knob_edit builder
excludes knobs already non-supported for the concern, so a retry moves a
different knob.

v1.2.0 (tranche 10): `irr_cancel_stale_retry` clears a pending retry mark once
any of the concern's experiments is supported. The family judges
(knob/datum_feedback/shape_mint) override the generic judge's provisional
outcome in the same fixpoint, so irr_request_retry could mark a retry on the
provisional 'inconclusive' that the family judge then turned into
'supported'; the daemon then tore down and re-promoted an already-adopted
concern (measured: tranche-10 knob grain probe).

v1.3.0 (tranche 11): an `abstained` experiment (the picked builder produced
an empty delta, closed before dispatch by self_optimisation's
close_abstained_variant) also counts as non-supported, so the agent's own
retry moves to another family.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = lambda n: {"type": "Var", "name": n}
A = lambda n, k: {"type": "Attr", "node": V(n), "key": k}
L = lambda v: {"type": "Lit", "value": v}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Not = lambda x: {"type": "Not", "arg": x}
OR0 = lambda x: {"type": "IfThenElse", "cond": Eq(x, L(None)), "then": L(0), "other": x}
exps = lambda pred: {"type": "Count", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "Experiment"},
                     "var_name": "e", "predicate": {"type": "And", "items": [Eq(A("e", "axis_tag"), A("st", "name")), pred]}}}
NONSUP = exps({"type": "In", "member": A("e", "outcome"), "container": L(["refuted", "inconclusive", "abstained"])})
SUP = exps(Eq(A("e", "outcome"), L("supported")))
LIVE = exps({"type": "And", "items": [{"type": "In", "member": A("e", "status"), "container": L(["requested", "running"])},
                                     Eq(A("e", "outcome"), L(None))]})
RETRIES = OR0(A("sc", "retry_count"))
seed = {
    "id": "instruction_repair_retry", "version": "1.3.0", "depends_on": [], "description": __doc__,
    "nodes": [{"local_id": 0, "type": "InstructionRetryPolicy", "attrs": {"name": "instruction_repair_retry", "enabled": 1, "max_retries": 2, "concern_kinds": ["instruction"]}}],
    "edges": [{"src": {"role": "agent_root"}, "type": "has_instruction_retry_policy", "tgt": {"local": 0}, "attrs": {}}],
    "productions": [],
    "rules": [{
        "name": "irr_request_retry",
        "comment": "Agent-initiated retry of a promoted instruction concern whose own experiments failed (see seed description).",
        "match": [["ag", "has_instruction_retry_policy", "pol"], ["ag", "has_self_concern", "sc"], ["sc", "promoted_to", "st"]],
        "where": {"type": "And", "items": [
            Eq(A("pol", "enabled"), L(1)),
            {"type": "In", "member": A("sc", "kind"), "container": A("pol", "concern_kinds")},
            Eq(A("sc", "status"), L("promoted")),
            Not(Eq(A("sc", "retry_requested"), L(1))),
            {"type": "Gt", "a": NONSUP, "b": RETRIES},
            Eq(SUP, L(0)), Eq(LIVE, L(0)),
            {"type": "Lt", "a": RETRIES, "b": A("pol", "max_retries")},
        ]},
        "effects": [["set_attr", "sc", "retry_requested", 1],
                    ["set_attr", "sc", "retry_count", {"__term__": {"type": "Plus", "items": [RETRIES, L(1)]}}]],
    }, {
        "name": "irr_cancel_stale_retry",
        "comment": "A pending retry mark is stale once the concern has a supported experiment (a family judge overrode a provisional verdict).",
        "match": [["ag", "has_instruction_retry_policy", "pol"], ["ag", "has_self_concern", "sc"], ["sc", "promoted_to", "st"]],
        "where": {"type": "And", "items": [Eq(A("sc", "retry_requested"), L(1)), {"type": "Gt", "a": SUP, "b": L(0)}]},
        "effects": [["set_attr", "sc", "retry_requested", 0],
                    ["set_attr", "sc", "retry_count", {"__term__": {"type": "Minus", "a": RETRIES, "b": L(1)}}]],
    }],
}
(ROOT / "seeds/instruction_repair_retry.json").write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("wrote seeds/instruction_repair_retry.json")
