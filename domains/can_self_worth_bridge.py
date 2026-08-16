"""can_self_worth_bridge -- sources SelfPattern.held_self_worth from a
resident's REAL, live, PERSISTENT CAN self_worth belief instead of a
hand-picked scalar.

Per docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_PREREG.md and
PERSISTENT_SELF_WORTH_PREREG.md. Pure world-adapter/harness code (CLAUDE.md's
architecture rule): builds a resident's real CAN Microtheory
(worlds/bigville_can_beliefs.py), relaxes it via the engine's OWN
discrete-asynchronous update rule (seeds/can_native_reimplementation.json's
can_native_update_3state, under run_rules()), and reads the converged
self_worth Concept's `state` back. No decision is made here -- the relaxed
belief IS the engine's own Hopfield-style fixpoint, not a Python
computation. A resident appraised more than once on the SAME substrate
REUSES their one persistent network (find_or_build_resident_can) rather
than minting a fresh, reset one each call, and record_incident_outcome
feeds an already-decided appraisal back as evidence so the belief genuinely
drifts across repeated incidents -- the SAME concept_apply_evidence PyO3 op
apply_scenario_evidence already established, mechanically re-applied.

REAL ENGINE GOTCHA (PERSISTENT_SELF_WORTH_PREREG.md Sec1, found live):
concept_apply_evidence mutates external_field OUTSIDE the rule-effect path,
so run_rules()'s incremental dirty-tracking never re-examines the Concept
afterward -- confirmed directly: even a massive evidence application left
`state` unchanged (steps=0) until `force_all_dirty()` was called first.
Every evidence-then-relax call in this module calls it -- do not remove it.

No seed is edited by this module -- can_native_reimplementation.json is
loaded and consumed exactly as tests/test_can_native_reimplementation.py's
own _build_draw / test_bigville_schema_symmetric_fix_makes_all_couplings_
visible_to_native_rule already do.
"""
from __future__ import annotations

from worlds import bigville_can_beliefs as bcb


def _find_resident_node(inner, name: str):
    for node in inner.nodes("Resident"):
        if inner.node(node)["attrs"].get("name") == name:
            return node
    return None


def _concepts_for_resident(inner, resident_node):
    mt = inner.neighbours(resident_node, "has_belief_mt")[0]
    concepts = {}
    for concept in inner.neighbours(mt, "has_concept"):
        concepts[inner.node(concept)["attrs"]["name"]] = concept
    return mt, concepts


def find_or_build_resident_can(inner, resident: dict, *, max_steps: int = 3000) -> dict:
    """The PERSISTENT entry point (PERSISTENT_SELF_WORTH_PREREG.md Sec2):
    if `resident["name"]` already has a Resident node on this substrate,
    reuse its EXISTING Microtheory/Concepts (the SAME network, carrying
    whatever `self_worth` it has drifted to from prior incidents) instead
    of minting a fresh, reset one. Only a genuinely NEW resident gets
    initialized (state/external_field=0.0, discrete_mode='3state') and
    relaxed for the first time. Returns {resident_node, mt, concepts,
    self_worth, steps, is_new}.
    """
    existing = _find_resident_node(inner, resident["name"])
    if existing is not None:
        mt, concepts = _concepts_for_resident(inner, existing)
        steps = inner.run_rules(max_steps)
        self_worth = inner.node(concepts["self_worth"])["attrs"]["state"]
        return {"resident_node": existing, "mt": mt, "concepts": concepts,
                "self_worth": self_worth, "steps": steps, "is_new": False}

    built = bcb.build_resident_can_mt(inner, resident)
    mt = built["mt_node"]
    concepts = built["concepts"]
    # build_resident_can_mt sets identity_field but not state/external_field
    # (confirmed by reading it directly, HELD_SELF_WORTH_FROM_CAN_PREREG.md
    # Sec2) -- initialize them here, mirroring tests/test_can_native_
    # reimplementation.py::_build_draw's own convention exactly.
    for concept in concepts.values():
        inner.set_attr(concept, "state", 0.0)
        inner.set_attr(concept, "external_field", 0.0)
    inner.set_attr(mt, "discrete_mode", "3state")
    inner.set_attr(mt, "can_tick", 0)
    steps = inner.run_rules(max_steps)
    self_worth = inner.node(concepts["self_worth"])["attrs"]["state"]
    return {"resident_node": built["resident_node"], "mt": mt, "concepts": concepts,
            "self_worth": self_worth, "steps": steps, "is_new": True}


def relax_resident_self_worth(inner, resident: dict, *, max_steps: int = 3000) -> dict:
    """Backward-compatible name for find_or_build_resident_can's own
    {self_worth, concepts, mt, steps} shape (HELD_SELF_WORTH_FROM_CAN_
    RESULTS.md's original callers) -- now PERSISTENT: a second call for the
    same resident name reuses the existing, possibly-drifted network."""
    out = find_or_build_resident_can(inner, resident, max_steps=max_steps)
    return {"self_worth": out["self_worth"], "concepts": out["concepts"],
            "mt": out["mt"], "steps": out["steps"]}


def record_incident_outcome(inner, concepts: dict, *, standard_met: bool,
                            attribution_locus: str, alpha: float = 0.3,
                            max_steps: int = 3000):
    """Feed an ALREADY-DECIDED self-conscious appraisal back as evidence on
    the resident's OWN self_worth Concept (PERSISTENT_SELF_WORTH_PREREG.md
    Sec2) -- no new decision, standard_met/attribution_locus were already
    decided by the dispute/self-conscious chain. Gated on attribution_locus
    != 'circumstance': an outcome not attributed to the self at all should
    not move the self-concept (Lewis 1971; Miller 1996) -- a real
    theoretical claim, not an incidental scoping choice. Returns the
    (possibly unchanged) current self_worth state; None input attribution_
    locus is never valid (callers always have a decided one).

    MUST call force_all_dirty() before re-running -- concept_apply_evidence
    writes external_field outside the rule-effect path and run_rules()'s
    incremental dirty-tracking will otherwise silently no-op (PREREG Sec1,
    found live; regression-tested).
    """
    self_worth_concept = concepts["self_worth"]
    if attribution_locus == "circumstance":
        return inner.node(self_worth_concept)["attrs"]["state"]
    evidence = 1.0 if standard_met else -1.0
    inner.concept_apply_evidence(self_worth_concept, evidence, alpha)
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    return inner.node(self_worth_concept)["attrs"]["state"]


def ensure_can_seed(inner) -> None:
    """Idempotently load seeds/can_native_reimplementation.json and install
    worlds/bigville_can_beliefs.py's Gamma productions -- the two pieces a
    caller needs on the substrate BEFORE calling relax_resident_self_worth.
    Guarded by rule_count() so a caller that already loaded the seed (or is
    composing multiple bridges on one substrate) does not reload it."""
    import json
    from substrate.seed_loader import engine_rules_only

    if inner.nodes("CanSelfWorthBridgeSeedLoaded"):
        bcb.install_productions(inner)
        return
    d = json.load(open("seeds/can_native_reimplementation.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    bcb.install_productions(inner)
    inner.add_node("CanSelfWorthBridgeSeedLoaded", {})


__all__ = ["relax_resident_self_worth", "find_or_build_resident_can",
           "record_incident_outcome", "ensure_can_seed"]
