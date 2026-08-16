"""can_self_worth_bridge -- sources SelfPattern.held_self_worth from a
resident's REAL, live CAN self_worth belief instead of a hand-picked
scalar.

Per docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_PREREG.md.
Pure world-adapter/harness code (CLAUDE.md's architecture rule): builds a
resident's real CAN Microtheory (worlds/bigville_can_beliefs.py), relaxes
it via the engine's OWN discrete-asynchronous update rule
(seeds/can_native_reimplementation.json's can_native_update_3state, under
run_rules()), and reads the converged self_worth Concept's `state` back.
No decision is made here -- the relaxed belief IS the engine's own
Hopfield-style fixpoint, not a Python computation. This module only
mechanically translates "which resident" into "what does their CAN network
say," exactly as reading a rulebook translates text into a HeldRule.

No seed is edited by this module -- can_native_reimplementation.json is
loaded and consumed exactly as tests/test_can_native_reimplementation.py's
own _build_draw / test_bigville_schema_symmetric_fix_makes_all_couplings_
visible_to_native_rule already do.
"""
from __future__ import annotations

from worlds import bigville_can_beliefs as bcb


def relax_resident_self_worth(inner, resident: dict, *, max_steps: int = 3000) -> dict:
    """Build `resident`'s real CAN Microtheory, relax it, and return
    {self_worth, concepts, mt, steps}. `self_worth` is the converged
    `state` attr on the resident's own `self_worth` Concept -- already on
    the same [-1,1]-ish scale (discrete {-1,0,+1}) SelfPattern.
    held_self_worth uses, no rescaling.

    `resident` is a full worlds/bigville_can_beliefs.py-shaped record
    ({"name", "index", "params": {...}}) -- caller-supplied data, exactly
    as every other rung's inputs have been.
    """
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
    return {"self_worth": self_worth, "concepts": concepts, "mt": mt, "steps": steps}


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


__all__ = ["relax_resident_self_worth", "ensure_can_seed"]
