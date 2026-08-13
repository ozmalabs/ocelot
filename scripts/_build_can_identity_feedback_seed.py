"""One-off authoring script: appends `can_native_identity_field_feedback`
to seeds/can_decay_identity.json programmatically, to avoid a hand-typo in a
nested Term-tree -- the same `tools/*`-class precedent
`scripts/_build_can_decay_identity_seed.py`/`scripts/
_build_can_external_field_decay_seed.py` already used (CLAUDE.md names this
class explicitly: "one-off authoring/capture scripts that EMIT seed
manifests"; not agent runtime).

See docs/research/engine_substrate/CAN_IDENTITY_FEEDBACK_PREREG.md for the
registered design this encodes.

Idempotent: if a rule of this name already exists in the seed, it is
REPLACED (not duplicated) so this script can be re-run safely. Also bumps
the seed's top-level description and the `can_native_identity_as_evidence_
axis` concept's `why` field to the resolved status, and appends the new
`can_native_identity_field_feedback` Concept doc node + DimensionGenerator,
mirroring `_build_can_external_field_decay_seed.py`'s own v1.0.0 -> v1.1.0
convention (this bump is v1.1.0 -> v1.2.0).
"""
from __future__ import annotations

import json

SEED_PATH = "seeds/can_decay_identity.json"


def _attr(node_var: str, key: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": node_var}, "key": key}


def _lit(value) -> dict:
    return {"type": "Lit", "value": value}


def _policy_or() -> dict:
    """Byte-identical subtree to the Or(...) policy gate the other three
    rules in this seed already use -- re-expressing
    mt_allows(mt, "allow_h_drift") as a Term."""
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


def _logodds_term(node_var: str, confirm_key: str, disconfirm_key: str) -> dict:
    """The SAME non-materializing log-odds render Term
    `test_can_native_reimplementation.py::_log_odds_term`/
    `test_can_decay_identity.py::_log_odds_term` already build in Python
    test code, re-expressed here as rule-effect Term JSON (this rung's own
    novelty: the FIRST rule to consume this render as a WRITE decision
    rather than an on-demand read)."""
    c = _attr(node_var, confirm_key)
    d = _attr(node_var, disconfirm_key)
    return {
        "type": "Log",
        "arg": {
            "type": "Div",
            "a": {"type": "Plus", "items": [c, _lit(1)]},
            "b": {"type": "Plus", "items": [d, _lit(1)]},
        },
    }


def _clamp_toward_zero_term(node_var: str, key: str) -> dict:
    """max(x-1, 0) when x>0; min(x+1, 0) when x<0; unchanged at x==0.
    BYTE-IDENTICAL shape to can_native_external_field_decay's own clamp,
    reused here for the neutral-log-odds (flip-flop) branch only (PREREG
    Sec2.1)."""
    x = _attr(node_var, key)
    return {
        "type": "IfThenElse",
        "cond": {"type": "Gt", "a": x, "b": _lit(0)},
        "then": {
            "type": "Max",
            "items": [
                {"type": "Minus", "a": x, "b": _lit(1)},
                _lit(0),
            ],
        },
        "other": {
            "type": "IfThenElse",
            "cond": {"type": "Lt", "a": x, "b": _lit(0)},
            "then": {
                "type": "Min",
                "items": [
                    {"type": "Plus", "items": [x, _lit(1)]},
                    _lit(0),
                ],
            },
            "other": x,
        },
    }


def build_rule() -> dict:
    identity_field = _attr("c", "identity_field")
    logodds = _logodds_term("c", "identity_evidence_confirm", "identity_evidence_disconfirm")
    new_identity_field = {
        "type": "IfThenElse",
        "cond": {"type": "Gt", "a": logodds, "b": _lit(0)},
        "then": {"type": "Plus", "items": [identity_field, _lit(1)]},
        "other": {
            "type": "IfThenElse",
            "cond": {"type": "Lt", "a": logodds, "b": _lit(0)},
            "then": {"type": "Minus", "a": identity_field, "b": _lit(1)},
            "other": _clamp_toward_zero_term("c", "identity_field"),
        },
    }
    return {
        "name": "can_native_identity_field_feedback",
        "comment": (
            "v1.2.0. The FEEDBACK half of identity dynamics, closing the gap "
            "CAN_DECAY_IDENTITY_RESULTS.md Sec2/CAN_MT_SCOPED_RULES_RESULTS.md "
            "Sec5/CAN_EXTERNAL_FIELD_DECAY_RESULTS.md Sec6 all named and "
            "explicitly declined to build: writes identity_field FROM the "
            "already-built, non-materializing identity log-odds render "
            "(can_native_identity_evidence_sample's own confirm/disconfirm "
            "ledger), so can_native_update_3state/_2state's own local-field "
            "sum (which already reads identity_field six times, seeds/"
            "can_native_reimplementation.json lines 166/250/350/434/566/652) "
            "actually feels it. DESIGN (CAN_IDENTITY_FEEDBACK_PREREG.md Sec2, "
            "registered before this script was run): a FIXED 1-quantum step "
            "toward the SIGN of the current logodds render -- "
            "logodds>0 -> identity_field+1, logodds<0 -> identity_field-1, "
            "logodds==0 (neutral/flip-flop) -> the SAME Max/Min "
            "clamp-toward-zero can_native_external_field_decay already uses. "
            "A magnitude-scaled (not merely sign-scaled) step -- reusing the "
            "render's own ln-scaled magnitude, or nudge_identity_on_flipped's "
            "own recurrence-boosted alpha -- was investigated and REJECTED: "
            "a per-tick step that GROWS in size is exactly the shape the "
            "discrete-async Lyapunov/energy convergence argument "
            "(CAN_NATIVE_REIMPLEMENTATION_RESULTS.md Sec2) does not want "
            "perturbing its bias term with; a FIXED quantum (same shape "
            "as every decay rule in this seed) is the stability-preferred "
            "choice, confirmed by the paired convergence sweep "
            "(CAN_IDENTITY_FEEDBACK_RESULTS.md Sec3). Own epoch attr "
            "(identity_field_tick), independent of identity_evidence_tick/ "
            "identity_decay_tick's own schedules. No same-tick-race guard: "
            "confirmed by direct grep (PREREG Sec3) that identity_field has "
            "ZERO writers anywhere in either native seed before this rule -- "
            "this is the FIRST writer, mirroring external_field's own "
            "situation exactly. Policy-gated: mt_allows(mt, 'allow_h_drift'), "
            "the SAME axis every other rule in this seed uses. Boundedness: "
            "under LITERALLY sustained single-direction evidence forever, "
            "identity_field grows without a hard cap (no -beta*identity_field "
            "decay term is built here, out of scope per the task) -- this "
            "mirrors evidence_confirm's OWN existing unbounded-growth design "
            "exactly (PREREG Sec2.4), not a new gap; within any finite "
            "observed run it is of course bounded, and this rung's live "
            "demonstrations report real, finite numbers. See "
            "CAN_IDENTITY_FEEDBACK_PREREG.md / _RESULTS.md."
        ),
        "match_type": "Concept",
        "match": [["mt", "has_concept", "c"]],
        "where": {
            "type": "And",
            "items": [
                {
                    "type": "Gt",
                    "a": _attr("mt", "can_tick"),
                    "b": _attr("c", "identity_field_tick"),
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
                "identity_field_tick",
                {"__term__": _attr("mt", "can_tick")},
            ],
        ],
    }


NEW_DESCRIPTION = (
    "Native decay + identity dynamics, closing two of consumer 6's three named "
    "blockers (CAN_CONSUMER_MIGRATION_RESULTS.md Sec1 row 6: 'decay ... no "
    "native analog proposed anywhere'; 'identity dynamics ... no native design "
    "exists at all'; Blocker B (Hebbian materialization) is a SIBLING rung's "
    "exact scope, not touched here). DECAY: the continuous mt_decay_h/"
    "mt_decay_J (can_ops.rs) are multiplicative (h <- (1-gamma)*h) -- a "
    "category error applied to an in-frame integer count (0.999*7 is not an "
    "integer). The integrality-preserving native analog is a fixed-quantum "
    "LINEAR decrement toward zero, exactly translate's own v -> v + offset[j] "
    "step (shape_decode.rs::apply_translate_once, offset=-1) PLUS an "
    "absorbing floor at 0 that plain translate does not have (registered "
    "explicitly as a deviation, not silently added) -- applied to the ONE "
    "in-frame integer quantity the native Hebbian mechanism already holds, "
    "evidence_confirm/evidence_disconfirm on a Coactivation ledger "
    "(seeds/can_native_reimplementation.json v1.1.0). IDENTITY: a Concept's "
    "per-tick sigma reading is a confirm/disconfirm-shaped evidence stream "
    "about its OWN typical state, tracked on the SAME evidence-ledger idiom "
    "the Hebbian causal-strength axis already uses (own counters, own "
    "strictly-later-tick epoch gate, own non-materializing log-odds render) "
    "-- the READING half. v1.2.0 (CAN_IDENTITY_FEEDBACK_PREREG.md/_RESULTS.md) "
    "closes the FEEDBACK half: can_native_identity_field_feedback writes "
    "identity_field FROM that render (fixed 1-quantum step toward the "
    "render's sign; neutral/flip-flop decays toward zero via the SAME "
    "Max/Min clamp can_native_external_field_decay uses), so "
    "can_native_update_3state/_2state's own local-field sum -- which reads "
    "identity_field but until v1.2.0 was written by no rule anywhere -- "
    "actually feels the identity-evidence axis. Convergence of the discrete-"
    "async update WITH this feedback active is measured, not assumed: see "
    "CAN_IDENTITY_FEEDBACK_RESULTS.md Sec3 for the real non-convergence count "
    "across a real multi-tick draw sample. Both new rules re-express "
    "mt_allows(mt, 'allow_h_drift') (self_improvement_loop.py) as a Term (a "
    "graph decision, not a Python one) rather than relying on a Python policy "
    "check the way the continuous wrappers do. Zero new Rust anywhere in this "
    "seed -- Attr/EdgeAttr/Eq/Not/And/Or/Gt/Lt/Plus/Minus/Max/Min/IfThenElse/"
    "Log/Div all pre-existed and are reused as-is. See "
    "CAN_DECAY_IDENTITY_PREREG.md / _RESULTS.md. v1.1.0 "
    "(CAN_EXTERNAL_FIELD_DECAY_PREREG.md/_RESULTS.md) added "
    "can_native_external_field_decay, closing CAN_MT_SCOPED_RULES_RESULTS.md "
    "Sec4c's remaining maybe_decay_h blocker: external_field is read six "
    "times by can_native_update_3state/_2state's own local-field formula but "
    "written by no rule anywhere -- that rule was the first writer. Unlike "
    "the two rules above, external_field is a SIGNED float with no native "
    "accumulation rule (set exogenously, not grown +1 per tick by any rule "
    "this arc built), so the existing one-sided integer-floor body (Gt(x,0) "
    "then x-1) does not transfer verbatim -- it is generalised (not "
    "redesigned) to a symmetric clamp-toward-zero via Max/Min (pre-existing "
    "Rust Terms, already used declaratively elsewhere in this tree, e.g. "
    "seeds/arousal_window_coreg.json), registered as that rung's one explicit "
    "deviation, mirroring how the floor-at-0 deviation from bare translate "
    "was registered explicitly in v1.0.0. No same-tick-race guard was needed "
    "there (unlike can_native_evidence_decay's own fix): confirmed by direct "
    "grep that no native rule, and no Python module including "
    "can_counterfactual.py, ever writes external_field -- decay is the ONLY "
    "writer that attr ever gets, so there is no reinforcement event to race "
    "against. v1.2.0's own same-tick-race check (PREREG Sec3) found the "
    "identical structural situation for identity_field -- zero pre-existing "
    "writers, so no race guard is needed there either."
)

NEW_IDENTITY_AXIS_WHY = (
    "Closes CAN_CONSUMER_MIGRATION_RESULTS.md row 6 blocker (c), BOTH halves "
    "as of v1.2.0. The READING half reuses the SAME evidence-ledger idiom the "
    "Hebbian causal-strength axis already uses (own counters, own "
    "strictly-later-tick epoch gate, own non-materializing log-odds render) "
    "with zero new machinery. The FEEDBACK half -- materializing the reading "
    "back into identity_field so it participates in can_native_update_3state's "
    "own local-field sum, the way the continuous h_id does -- is now BUILT "
    "(can_native_identity_field_feedback, CAN_IDENTITY_FEEDBACK_PREREG.md/"
    "_RESULTS.md): a fixed 1-quantum step toward the render's sign, its own "
    "epoch gate, the SAME policy gate every other rule in this seed uses. "
    "Convergence of the discrete-async update with this feedback loop active "
    "was measured directly (not assumed) against a real multi-tick draw "
    "sample -- see CAN_IDENTITY_FEEDBACK_RESULTS.md Sec3 for the real "
    "numbers and verdict."
)

NEW_FEEDBACK_CONCEPT = {
    "name": "can_native_identity_field_feedback",
    "definition": (
        "v1.2.0. A native writer of identity_field, closing the identity-"
        "feedback gap can_native_identity_as_evidence_axis's own v1.1.0 "
        "'why' field named as unresolved: a fixed 1-quantum step toward the "
        "SIGN of the current identity_evidence log-odds render each strictly-"
        "later external tick (neutral/flip-flop reading decays "
        "identity_field toward zero via the same Max/Min clamp "
        "can_native_external_field_decay uses), gated by the SAME "
        "allow_h_drift policy axis every rule in this seed checks."
    ),
    "why": (
        "identity_field is read by can_native_update_3state/_2state's own "
        "local-field sum but was written by no rule anywhere before v1.2.0 "
        "(confirmed by direct grep, CAN_IDENTITY_FEEDBACK_PREREG.md Sec3 -- "
        "the SAME class of check CAN_EXTERNAL_FIELD_DECAY_RESULTS.md Sec0 "
        "ran for external_field). A magnitude/recurrence-scaled step was "
        "investigated and rejected on stability grounds (a growing per-tick "
        "bias perturbation threatens the discrete-async update's own "
        "Lyapunov convergence argument); a fixed quantum matches every "
        "other rule in this seed and was validated against a real "
        "convergence sweep before being adopted (CAN_IDENTITY_FEEDBACK_"
        "RESULTS.md Sec3)."
    ),
}

NEW_GENERATOR = {
    "local_id": 5,
    "type": "DimensionGenerator",
    "attrs": {
        "name": "identity_field_feedback",
        "kind": "translate",
        "coord_dims": [0],
        "params": [1],
        "offset": [1],
        "_note": (
            "v1.2.0 (CAN_IDENTITY_FEEDBACK_PREREG/_RESULTS.md). Documents the "
            "SAME translate-by-1 SHAPE local_id 1/2/4 already declare, applied "
            "to identity_field -- with the sign of the step chosen by the "
            "current identity log-odds render, not fixed to a single "
            "direction (offset=[1] documents the QUANTUM magnitude only; the "
            "actual rule flips the sign via IfThenElse on the render, and "
            "falls back to local_id 4's own Max/Min clamp-toward-zero body "
            "in the neutral/flip-flop case). Declarative only, never "
            "literally invoked at runtime -- matching local_id 1/2/4's own "
            "convention."
        ),
    },
}


def main() -> None:
    with open(SEED_PATH) as f:
        seed = json.load(f)

    seed["description"] = NEW_DESCRIPTION

    for concept in seed["concepts"]:
        if concept["name"] == "can_native_identity_as_evidence_axis":
            concept["why"] = NEW_IDENTITY_AXIS_WHY
            break
    else:
        raise SystemExit("can_native_identity_as_evidence_axis concept not found")

    concept_names = {c["name"] for c in seed["concepts"]}
    if NEW_FEEDBACK_CONCEPT["name"] not in concept_names:
        seed["concepts"].append(NEW_FEEDBACK_CONCEPT)

    gen_names = {n["attrs"].get("name") for n in seed["nodes"] if n.get("type") == "DimensionGenerator"}
    if NEW_GENERATOR["attrs"]["name"] not in gen_names:
        seed["nodes"].append(NEW_GENERATOR)

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
