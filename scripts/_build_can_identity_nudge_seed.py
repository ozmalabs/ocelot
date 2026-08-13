"""One-off authoring script: appends `can_native_identity_nudge_on_flip`
to seeds/can_decay_identity.json programmatically, the SAME `tools/*`-class
precedent `scripts/_build_can_identity_feedback_seed.py`/`scripts/
_build_can_external_field_decay_seed.py` already used (CLAUDE.md names this
class explicitly: "one-off authoring/capture scripts that EMIT seed
manifests"; not agent runtime).

See docs/research/engine_substrate/CAN_IDENTITY_NUDGE_FINAL_PREREG.md for
the registered design this encodes.

Idempotent: if a rule/concept/generator of this name already exists in the
seed, it is REPLACED (not duplicated) so this script can be re-run safely.
Bumps the seed's top-level description (v1.2.0 -> v1.3.0) and the
`can_native_identity_as_evidence_axis` concept's `why` field to the resolved
status, and appends the new `can_native_identity_nudge_on_flip` Concept doc
node + DimensionGenerator, mirroring the v1.1.0 -> v1.2.0 convention.

THIS RUNG DOES NOT TOUCH `can_native_identity_field_feedback` (the ambient
rule, local_id 5's generator, or its own Concept doc node) -- confirmed by
this script only ever appending/replacing entries whose NAME matches this
rung's own new rule/concept/generator names.
"""
from __future__ import annotations

import json

SEED_PATH = "seeds/can_decay_identity.json"


def _attr(node_var: str, key: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": node_var}, "key": key}


def _lit(value) -> dict:
    return {"type": "Lit", "value": value}


def _policy_or() -> dict:
    """Byte-identical subtree to the Or(...) policy gate every other rule
    in this seed already uses -- re-expressing mt_allows(mt,
    "allow_h_drift") as a Term."""
    return {
        "type": "Or",
        "items": [
            {"type": "Eq", "a": _attr("mt", "update_policy"), "b": _lit("adaptive")},
            {
                "type": "And",
                "items": [
                    {"type": "Eq", "a": _attr("mt", "update_policy"), "b": _lit("hybrid")},
                    {
                        "type": "Not",
                        "arg": {
                            "type": "Eq",
                            "a": _attr("mt", "allow_h_drift"),
                            "b": _lit(0),
                        },
                    },
                ],
            },
        ],
    }


def build_rule() -> dict:
    identity_field = _attr("c", "identity_field")
    target_sigma = _attr("c", "pending_identity_nudge_target_sigma")
    recurrence = _attr("c", "pending_identity_nudge_recurrence")

    step = {
        "type": "IfThenElse",
        "cond": {"type": "Gt", "a": recurrence, "b": _lit(1)},
        "then": _lit(2.0),
        "other": _lit(1.0),
    }
    new_identity_field = {
        "type": "IfThenElse",
        "cond": {"type": "Gt", "a": target_sigma, "b": _lit(0)},
        "then": {"type": "Plus", "items": [identity_field, step]},
        "other": {
            "type": "IfThenElse",
            "cond": {"type": "Lt", "a": target_sigma, "b": _lit(0)},
            "then": {"type": "Minus", "a": identity_field, "b": step},
            "other": identity_field,
        },
    }
    return {
        "name": "can_native_identity_nudge_on_flip",
        "comment": (
            "v1.3.0 (CAN_IDENTITY_NUDGE_FINAL_PREREG.md/_RESULTS.md). The "
            "EVENT-TRIGGERED sibling of can_native_identity_field_feedback "
            "(v1.2.0) -- closes the LAST of self_improvement_loop.py's seven "
            "operations, nudge_identity_on_flipped, left explicitly unmigrated "
            "by CAN_IDENTITY_FEEDBACK_RESULTS.md Sec6.2 ('this function's "
            "whole point is an IMMEDIATE, LARGER nudge on insight "
            "consolidation ... the ambient rule has no input surface for a "
            "specific target node set, an injected target sigma, or a "
            "recurrence count'). This rule gives it that input surface via "
            "THREE per-Concept marker attrs (pending_identity_nudge_"
            "target_sigma, pending_identity_nudge_recurrence, "
            "pending_identity_nudge_epoch) written ONLY by nudge_identity_"
            "on_flipped's own native branch -- mechanical translation of the "
            "already-computed, substrate-agnostic `insight` dict (detect_"
            "insight, confirmed unmodified and confirmed substrate-agnostic, "
            "PREREG Sec0) into graph attrs, never a Python decision. The "
            "DECISION -- sign from target_sigma, bounded step from "
            "recurrence -- lives entirely in this rule's own IfThenElse "
            "effects, mirroring can_native_identity_field_feedback's own "
            "fixed-quantum-toward-sign shape exactly, with ONE registered "
            "generalisation: the step is BINARY two-tier (1.0 first "
            "occurrence, 2.0 recurring via Gt(pending_identity_nudge_"
            "recurrence, 1)) instead of a single fixed quantum -- preserving "
            "SOME distinct recurrence response while staying strictly bounded "
            "(never the rejected unbounded base_alpha*(1+ln(recurrence)) "
            "shape the continuous path uses). target_sigma==0 fires no "
            "directional change (mirrors can_native_identity_evidence_"
            "sample's own state==0 'no evidence' guard). Own epoch attr "
            "(identity_nudge_applied_epoch), EQUALITY-gated against the "
            "Python-written pending_identity_nudge_epoch (not the Gt-per-tick "
            "pattern the ambient rules use -- this event is sparse and "
            "externally sequenced, not monotonically advancing every tick), "
            "consumed by writing it back so the rule fires exactly once per "
            "event. No same-tick race: all three pending_* attrs plus "
            "identity_nudge_applied_epoch are BRAND NEW names with zero "
            "pre-existing writers or readers anywhere (confirmed by grep, "
            "PREREG Sec2.4) -- only this rule and nudge_identity_on_flipped's "
            "native branch ever touch them. Policy-gated: mt_allows(mt, "
            "'allow_h_drift'), the SAME axis every rule in this seed uses. "
            "Convergence WITH this rule live alongside the ambient feedback "
            "rule AND the discrete update, across real synthesized flip "
            "events (not just ambient ticks), is measured directly -- see "
            "CAN_IDENTITY_NUDGE_FINAL_RESULTS.md Sec3 for the real "
            "non-convergence count. See CAN_IDENTITY_NUDGE_FINAL_PREREG.md / "
            "_RESULTS.md."
        ),
        "match_type": "Concept",
        "match": [["mt", "has_concept", "c"]],
        "where": {
            "type": "And",
            "items": [
                {
                    "type": "Not",
                    "arg": {
                        "type": "Eq",
                        "a": _attr("c", "pending_identity_nudge_epoch"),
                        "b": _attr("c", "identity_nudge_applied_epoch"),
                    },
                },
                _policy_or(),
            ],
        },
        "effects": [
            [
                "set_attr",
                "c",
                "identity_field",
                {"__term__": new_identity_field},
            ],
            [
                "set_attr",
                "c",
                "identity_nudge_applied_epoch",
                {"__term__": _attr("c", "pending_identity_nudge_epoch")},
            ],
        ],
    }


NEW_DESCRIPTION_SUFFIX = (
    " v1.3.0 (CAN_IDENTITY_NUDGE_FINAL_PREREG.md/_RESULTS.md) closes the "
    "LAST of self_improvement_loop.py's seven operations: nudge_identity_"
    "on_flipped, the EVENT-triggered (not ambient) identity nudge fired on "
    "insight consolidation. can_native_identity_nudge_on_flip is the "
    "sibling rule that gives the ambient v1.2.0 mechanism's shape an event "
    "input surface (a specific target node set, an injected target_sigma, "
    "a bounded two-tier recurrence step) it structurally cannot have as a "
    "per-tick ambient sampler -- registered and rejected as a bolt-on to "
    "the ambient rule itself in CAN_IDENTITY_FEEDBACK_RESULTS.md Sec6.2. "
    "Zero new Rust; three brand-new per-Concept marker attrs written only "
    "by nudge_identity_on_flipped's own native branch (mechanical "
    "translation of detect_insight's already-substrate-agnostic dict) and "
    "read only by this one rule."
)

NEW_IDENTITY_AXIS_WHY_SUFFIX = (
    " v1.3.0 additionally closes the EVENT half self_improvement_loop.py's "
    "nudge_identity_on_flipped needed and the ambient v1.2.0 rule "
    "structurally could not provide (CAN_IDENTITY_FEEDBACK_RESULTS.md "
    "Sec6.2): can_native_identity_nudge_on_flip, a sibling rule triggered "
    "by a graph-resident event marker rather than the ambient per-tick "
    "epoch, preserving the event's own target_sigma direction and a "
    "BOUNDED (binary, 1.0/2.0) recurrence-scaled step -- never the "
    "continuous path's unbounded log(recurrence) growth. See "
    "CAN_IDENTITY_NUDGE_FINAL_PREREG.md / _RESULTS.md for the convergence "
    "validation with both native identity rules live alongside real "
    "synthesized flip events."
)

NEW_NUDGE_CONCEPT = {
    "name": "can_native_identity_nudge_on_flip",
    "definition": (
        "v1.3.0. A native, EVENT-triggered writer of identity_field -- the "
        "sibling of can_native_identity_field_feedback (ambient, per-tick) "
        "that closes self_improvement_loop.py's LAST unmigrated operation, "
        "nudge_identity_on_flipped. Fires once per insight-consolidation "
        "event on the SPECIFIC flipped Concepts named by that event, nudging "
        "identity_field toward the event's own injected target_sigma by a "
        "BOUNDED, binary two-tier step (1.0 first occurrence, 2.0 "
        "recurring via the event's own recurrence_count, itself already "
        "graph-resident on the InsightEvent node record_insight writes)."
    ),
    "why": (
        "nudge_identity_on_flipped (domains/self_improvement_loop.py) is "
        "EVENT-triggered with an injected target_sigma + recurrence signal "
        "the ambient can_native_identity_field_feedback rule structurally "
        "cannot read (it only samples AMBIENT sigma, whole-Mt, per tick) -- "
        "CAN_IDENTITY_FEEDBACK_RESULTS.md Sec6.2 investigated routing this "
        "function through the ambient rule and rejected it as a silent "
        "no-op-in-practice that discards the event's own signal. This rule "
        "is the genuinely different mechanism that rung named as the "
        "remaining, real work: a graph-resident event marker (three new "
        "per-Concept attrs, written only by this function's own native "
        "branch) plus a rule whose OWN IfThenElse decides sign (from "
        "target_sigma) and a BOUNDED step (from recurrence, binary not "
        "log-scaled) -- preserving the real signal the ambient rule alone "
        "would have discarded, without reintroducing the unbounded-growth "
        "shape CAN_IDENTITY_FEEDBACK_PREREG.md Sec2.2/2.3 rejected for the "
        "ambient rule. Validated against a real convergence sweep with both "
        "native identity rules live alongside real synthesized flip events "
        "-- see CAN_IDENTITY_NUDGE_FINAL_RESULTS.md Sec3."
    ),
}

NEW_GENERATOR = {
    "local_id": 6,
    "type": "DimensionGenerator",
    "attrs": {
        "name": "identity_nudge_on_flip",
        "kind": "translate",
        "coord_dims": [0],
        "params": [1],
        "offset": [1],
        "_note": (
            "v1.3.0 (CAN_IDENTITY_NUDGE_FINAL_PREREG/_RESULTS.md). Documents "
            "the SAME translate-by-1 SHAPE local_id 1/2/4/5 already declare, "
            "applied to identity_field a SECOND time via a different "
            "trigger (event, not ambient tick) -- with TWO registered "
            "generalisations local_id 5 does not have: (a) the step "
            "MAGNITUDE itself is two-valued (1 or 2, offset=[1] documents "
            "the BASE quantum only; the actual rule doubles it via IfThenElse "
            "on a recurrence flag), and (b) the sign is chosen by an "
            "INJECTED target_sigma (an event's own payload) rather than an "
            "ambient render. Declarative only, never literally invoked at "
            "runtime -- matching local_id 1/2/4/5's own convention."
        ),
    },
}


def main() -> None:
    with open(SEED_PATH) as f:
        seed = json.load(f)

    seed["version"] = "1.3.0"
    if not seed["description"].rstrip().endswith(
        NEW_DESCRIPTION_SUFFIX.strip()
    ):
        seed["description"] = seed["description"] + NEW_DESCRIPTION_SUFFIX

    for concept in seed["concepts"]:
        if concept["name"] == "can_native_identity_as_evidence_axis":
            if not concept["why"].rstrip().endswith(
                NEW_IDENTITY_AXIS_WHY_SUFFIX.strip()
            ):
                concept["why"] = concept["why"] + NEW_IDENTITY_AXIS_WHY_SUFFIX
            break
    else:
        raise SystemExit("can_native_identity_as_evidence_axis concept not found")

    concept_names = {c["name"] for c in seed["concepts"]}
    if NEW_NUDGE_CONCEPT["name"] not in concept_names:
        seed["concepts"].append(NEW_NUDGE_CONCEPT)
    else:
        for i, c in enumerate(seed["concepts"]):
            if c["name"] == NEW_NUDGE_CONCEPT["name"]:
                seed["concepts"][i] = NEW_NUDGE_CONCEPT
                break

    gen_names = {n["attrs"].get("name") for n in seed["nodes"] if n.get("type") == "DimensionGenerator"}
    if NEW_GENERATOR["attrs"]["name"] not in gen_names:
        seed["nodes"].append(NEW_GENERATOR)
    else:
        for i, n in enumerate(seed["nodes"]):
            if n.get("type") == "DimensionGenerator" and n["attrs"].get("name") == NEW_GENERATOR["attrs"]["name"]:
                seed["nodes"][i] = NEW_GENERATOR
                break

    rules = seed["rules"]
    new_rule = build_rule()
    replaced = False
    for i, r in enumerate(rules):
        if r.get("name") == new_rule["name"]:
            rules[i] = new_rule
            replaced = True
            break
    if not replaced:
        rules.append(new_rule)

    with open(SEED_PATH, "w") as f:
        json.dump(seed, f, indent=1)
        f.write("\n")
    print("replaced" if replaced else "appended", new_rule["name"], "in", SEED_PATH)


if __name__ == "__main__":
    main()
