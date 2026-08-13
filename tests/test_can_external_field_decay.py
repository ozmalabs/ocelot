"""Native `external_field` decay (seeds/can_decay_identity.json v1.1.0,
`can_native_external_field_decay`), closing the LAST remaining blocker in
`CAN_MT_SCOPED_RULES_RESULTS.md` §4c (`maybe_decay_h`). See
docs/research/engine_substrate/CAN_EXTERNAL_FIELD_DECAY_PREREG.md for the
registered design and _RESULTS.md for the write-up these tests back.

Four live demonstrations, matching the task's own four registered asks:
  (a)/(b) test_external_field_decay_* -- a real, signed external_field
      value decaying linearly toward zero (both directions), floored/
      ceilinged at 0, never crossing.
  (c) test_external_field_decay_blocked_when_frozen -- frozen policy blocks
      decay entirely, unchanged value across many ticks.
  (d) test_external_field_decay_composes_with_local_field_formula -- the
      decayed value is genuinely READ by can_native_update_3state's own
      local-field formula: as external_field decays below the atanh(0.5)
      threshold, the Concept's OWN discrete state decision flips.

No same-tick-race test is included here, unlike test_can_decay_identity.py's
own test_evidence_decay_never_races_reinforcement_in_the_same_tick --
PREREG Sec2 registered the prediction, checked by direct grep before
writing the rule, that NO native rule and NO Python module (including
can_counterfactual.py) ever writes external_field, so there is no
reinforcement event for decay to race against. This is confirmed
structurally (by the rule/module source, not merely by these tests failing
to find a race), and is reported as an honest asymmetry with the Hebbian/
identity cases in CAN_EXTERNAL_FIELD_DECAY_RESULTS.md.
"""
from __future__ import annotations

import json
import math

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)

ATANH_HALF = math.atanh(0.5)


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def _isolated_concept(inner, policy="adaptive", extra_mt_attrs=None,
                       external_field=0.0, discrete_mode="static"):
    """discrete_mode='static' isolates the decay ledger from
    can_native_update_3state/_2state, mirroring test_can_decay_identity.py's
    own _isolated_pair isolation discipline -- used for the pure decay-shape
    tests (a)/(b)/(c). The composition test (d) below deliberately uses
    discrete_mode='3state' instead."""
    attrs = {"temperature": 1.0, "discrete_mode": discrete_mode, "can_tick": 0,
             "update_policy": policy}
    if extra_mt_attrs:
        attrs.update(extra_mt_attrs)
    mt = inner.add_node("Microtheory", attrs)
    c = inner.add_node("Concept", {
        "name": "c", "state": 0.0,
        "external_field": external_field, "identity_field": 0.0,
        "external_field_decay_tick": -1,
    })
    inner.add_edge(mt, "has_concept", c, {})
    return mt, c


# ---------------------------------------------------------------------
# (a)/(b) Decay shape -- both signs, floored/ceilinged at zero.
# ---------------------------------------------------------------------

def test_external_field_decay_erodes_positive_field_toward_zero_when_adaptive():
    """PREREG Sec5 point 1: a positive external_field, seeded above
    magnitude 1 (per PREREG Sec1c's registered quantum-mismatch prediction
    -- a field in the codebase's own typical [-1,1] test-harness range
    would fully zero out in a single tick, which would not show a genuine
    multi-tick trajectory), decays by exactly 1 quantum per strictly-later
    external tick under an ADAPTIVE policy, floored at 0, never negative."""
    s = _loaded_substrate()
    inner = s._inner
    mt, c = _isolated_concept(inner, policy="adaptive", external_field=3.5)

    trajectory = []
    for tick in range(8):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
        trajectory.append(inner.node(c)["attrs"]["external_field"])
    print(f"external_field decay trajectory (adaptive, positive, from 3.5): {trajectory}")
    assert trajectory == [2.5, 1.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0], (
        f"expected a strict 1-per-tick linear decrement floored at 0, got {trajectory}"
    )
    assert all(v >= 0.0 for v in trajectory), "must never go negative"


def test_external_field_decay_erodes_negative_field_toward_zero_when_adaptive():
    """The symmetric mirror of the positive case -- PREREG Sec1b's
    registered generalisation (Max/Min clamp, not the one-sided integer-
    floor body the other two ledger rules use) must ceiling a negative
    field at 0, never overshoot into positive territory."""
    s = _loaded_substrate()
    inner = s._inner
    mt, c = _isolated_concept(inner, policy="adaptive", external_field=-3.5)

    trajectory = []
    for tick in range(8):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
        trajectory.append(inner.node(c)["attrs"]["external_field"])
    print(f"external_field decay trajectory (adaptive, negative, from -3.5): {trajectory}")
    assert trajectory == [-2.5, -1.5, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0], (
        f"expected a strict 1-per-tick linear increment ceilinged at 0, got {trajectory}"
    )
    assert all(v <= 0.0 for v in trajectory), "must never go positive"


def test_external_field_decay_blocked_when_frozen():
    """PREREG Sec5 point 3, FROZEN case: mt_allows(mt,'allow_h_drift') is
    False unconditionally for a frozen Mt -- the rule's own Term
    re-expression must agree. external_field must stay byte-unchanged
    across many ticks, and external_field_decay_tick must never advance
    past its initial value."""
    s = _loaded_substrate()
    inner = s._inner
    mt, c = _isolated_concept(inner, policy="frozen", external_field=3.5)

    for tick in range(8):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    after = inner.node(c)["attrs"]
    print(f"frozen, unreinforced through tick 7: external_field={after['external_field']} "
          f"external_field_decay_tick={after.get('external_field_decay_tick')}")
    assert after["external_field"] == 3.5, "a FROZEN Mt must never decay external_field"
    assert after.get("external_field_decay_tick") == -1, (
        "external_field_decay_tick must stay at its initial value -- the rule must never even fire"
    )


def test_external_field_decay_hybrid_axis_explicit_and_default():
    """The SAME hybrid-axis Term re-expression test_can_decay_identity.py's
    own test_evidence_decay_hybrid_axis_explicit_and_default already proves
    for the Hebbian ledger, reused here for external_field: explicit
    allow_h_drift=0 blocks; absent defaults to allowed."""
    s = _loaded_substrate()
    inner = s._inner
    mt, c = _isolated_concept(inner, policy="hybrid",
                               extra_mt_attrs={"allow_h_drift": 0},
                               external_field=3.5)
    for tick in range(5):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    blocked = inner.node(c)["attrs"]["external_field"]
    print(f"hybrid allow_h_drift=0: external_field={blocked} (must stay 3.5)")
    assert blocked == 3.5, "explicit hybrid allow_h_drift=0 must block decay"

    s2 = _loaded_substrate()
    inner2 = s2._inner
    mt2, c2 = _isolated_concept(inner2, policy="hybrid", external_field=3.5)  # no allow_h_drift attr
    for tick in range(5):
        inner2.set_attr(mt2, "can_tick", tick)
        inner2.run_rules(1000)
    allowed = inner2.node(c2)["attrs"]["external_field"]
    print(f"hybrid allow_h_drift absent (default True): external_field={allowed} (must reach 0, 5 ticks of decay from 3.5)")
    assert allowed == 0.0, "hybrid with allow_h_drift unset must default to allowed"


# ---------------------------------------------------------------------
# (d) Composition with the local-field formula can_native_update_3state
# already reads external_field through.
# ---------------------------------------------------------------------

def test_external_field_decay_composes_with_local_field_formula_and_flips_state():
    """PREREG Sec5 point 4: decaying external_field on a LIVE discrete_mode
    Mt (not the isolated 'static' harness the other tests use) must
    genuinely change can_native_update_3state's own local-field/threshold
    decision -- proving the decayed value is READ by the SAME formula that
    already consumes external_field, not just changed in isolation.

    Single Concept, no causal_influence edges (local field = external_field
    + identity_field(=0) + 0), temperature=1.0, threshold=atanh(0.5)~=0.549.
    external_field=3.5 starts well above threshold -> state=+1. As
    can_native_external_field_decay and can_native_update_3state BOTH run
    inside the SAME run_rules_scoped/run_rules fixpoint each tick, the
    state decision must track the POST-decay field once it crosses below
    the threshold: 2.5->+1, 1.5->+1, 0.5->0 (FLIP), 0.0->0."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c = inner.add_node("Concept", {
        "name": "c", "state": 0.0,
        "external_field": 3.5, "identity_field": 0.0,
        "external_field_decay_tick": -1,
    })
    inner.add_edge(mt, "has_concept", c, {})

    field_trajectory = []
    state_trajectory = []
    for tick in range(5):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
        attrs = inner.node(c)["attrs"]
        field_trajectory.append(attrs["external_field"])
        state_trajectory.append(attrs["state"])
    print(f"field trajectory: {field_trajectory}")
    print(f"state trajectory: {state_trajectory}")

    assert field_trajectory == [2.5, 1.5, 0.5, 0.0, 0.0]
    assert state_trajectory == [1.0, 1.0, 0.0, 0.0, 0.0], (
        "the discrete update must FLIP away from +1 once the decayed field "
        f"can no longer clear the atanh(0.5)={ATANH_HALF:.4f} threshold "
        f"(scaled by temperature=1.0); got {state_trajectory}"
    )


def test_external_field_decay_composes_via_scoped_settle_isolated_from_other_mt():
    """The same composition proof, but reached through
    domains.can_native_orchestration.scoped_settle -- the EXACT mechanism
    domains.self_improvement_loop.maybe_decay_h's native branch now calls
    (CAN_EXTERNAL_FIELD_DECAY_RESULTS.md) -- and confirming a SECOND,
    unrelated Mt in the same graph is untouched (CAN_MT_SCOPED_RULES_
    RESULTS.md's own two-Mt isolation guarantee, re-proven for this rule)."""
    from domains.can_native_orchestration import scoped_settle

    s = _loaded_substrate()
    inner = s._inner
    mt_a = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c_a = inner.add_node("Concept", {
        "name": "a", "state": 0.0, "external_field": 3.5, "identity_field": 0.0,
        "external_field_decay_tick": -1,
    })
    inner.add_edge(mt_a, "has_concept", c_a, {})

    mt_b = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c_b = inner.add_node("Concept", {
        "name": "b", "state": 0.0, "external_field": 3.5, "identity_field": 0.0,
        "external_field_decay_tick": -1,
    })
    inner.add_edge(mt_b, "has_concept", c_b, {})

    for tick in range(4):
        inner.set_attr(mt_a, "can_tick", tick)
        scoped_settle(inner, mt_a)
    field_a = inner.node(c_a)["attrs"]["external_field"]
    field_b = inner.node(c_b)["attrs"]["external_field"]
    print(f"scoped to mt_a only, 4 ticks: field_a={field_a} field_b={field_b} (must be unchanged 3.5)")
    assert field_a == 0.0, f"mt_a's own field must have decayed 4 quanta from 3.5 (floored at 0), got {field_a}"
    assert field_b == 3.5, "mt_b must be completely untouched by mt_a's scoped decay"
