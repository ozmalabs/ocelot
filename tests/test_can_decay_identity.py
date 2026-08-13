"""Native decay + identity dynamics (seeds/can_decay_identity.json), layered
on top of seeds/can_native_reimplementation.json exactly like seeds/
evidence_axis_infer.json's own precedent. See docs/research/engine_substrate/
CAN_DECAY_IDENTITY_PREREG.md for the registered design and
CAN_DECAY_IDENTITY_RESULTS.md for the write-up these tests back.

Closes CAN_CONSUMER_MIGRATION_RESULTS.md Sec1 row 6's blockers (a) decay and
(c) identity dynamics ONLY -- blocker (b) (Hebbian materialization) is a
sibling rung's exact scope and is not touched anywhere in this file.

Three live demonstrations, matching the task's own three registered asks:
  (a) test_evidence_decay_* -- a real evidence count decaying toward zero
      under a native, integrality-preserving rule, gated by the SAME
      mt_allows(mt, "allow_h_drift") policy axis the continuous mechanism
      uses (all three policy cases: adaptive-allows, frozen-blocks,
      hybrid-default-allows/hybrid-explicitly-blocks).
  (b) test_identity_evidence_* -- a real per-Concept sigma trajectory
      producing a graded "identity commitment" reading via the SAME
      non-materializing log-odds render the causal-strength axis already
      uses, with a consistently-committed Concept reading strictly stronger
      than a flip-flopping one (mirrors "flips average to zero -> identity
      decays", can_ops.rs:774).
  (c) test_recurrence_boost_* -- whether nudge_identity_on_flipped's
      log-scaled recurrence boost is already provided for free by the
      evidence-axis render (it is, STRUCTURALLY -- both are natural-log-
      scaled, diminishing-marginal-return functions of a repetition count --
      but NOT the same formula, since the counts being scaled are different
      signals in origin; reported precisely, per PREREG Sec2's registered
      prediction).
"""
from __future__ import annotations

import json
import math

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from substrate_rs import Term

SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def _isolated_pair(inner, policy="adaptive", extra_mt_attrs=None):
    """discrete_mode='static' so item-3's relaxation rules never interfere
    -- the SAME isolation discipline test_can_native_reimplementation.py's
    own _isolated_pair already uses, for the SAME documented reason."""
    attrs = {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
             "update_policy": policy}
    if extra_mt_attrs:
        attrs.update(extra_mt_attrs)
    mt = inner.add_node("Microtheory", attrs)
    a = inner.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    return mt, a, b


def _coact_between(inner, a, b):
    """Find the Coactivation node anchoring the a->b evidence ledger -- the
    SAME traversal test_can_native_reimplementation.py's own helper uses."""
    for c in inner.neighbours(a, "coactivated_with"):
        if b in inner.neighbours(c, "coactivation_of"):
            return c
    return None


def _log_odds_term(node_var, confirm_key, disconfirm_key):
    """The cross-frame log-odds RENDER, generalised to any (confirm, disconfirm)
    attr pair on any bound node var -- the SAME Term shape
    test_can_native_reimplementation.py::_log_odds_term already established
    for the Hebbian axis, reused here (not modified) for both this rung's
    evidence ledgers."""
    return Term(
        "Log",
        arg=Term(
            "Div",
            a=Term("Plus", items=[
                Term("Attr", node=Term("Var", name=node_var), key=confirm_key),
                Term("Lit", value=1),
            ]),
            b=Term("Plus", items=[
                Term("Attr", node=Term("Var", name=node_var), key=disconfirm_key),
                Term("Lit", value=1),
            ]),
        ),
    )


def _reinforce_hebbian_pair(inner, mt, a, b, through_tick):
    """Drive can_tick from 0 (note) through `through_tick` (inclusive),
    running run_rules() each step -- mints on tick 1 (recurrence), then
    reinforces (evidence_confirm += 1) on every subsequent tick, exactly
    matching test_hebbian_reweight_end_to_end_unblocks_v1_graded_reweighting's
    own drive pattern."""
    inner.run_rules(1000)  # tick 0: note
    for tick in range(1, through_tick + 1):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)


# ---------------------------------------------------------------------
# (a) Decay of the native Hebbian evidence ledger.
# ---------------------------------------------------------------------

def test_evidence_decay_erodes_toward_zero_when_adaptive_and_unreinforced():
    """PREREG Sec1's registered prediction, ADAPTIVE case: after minting +
    reinforcing an edge to (confirm=4, disconfirm=0), stopping reinforcement
    (one Concept's state -> 0, so can_native_hebbian_reweight's own guard
    stops firing) and advancing 7 more ticks under an ADAPTIVE Mt must decay
    evidence_confirm linearly toward zero, one quantum per tick, and FLOOR
    there -- never negative."""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, policy="adaptive")
    _reinforce_hebbian_pair(inner, mt, a, b, through_tick=4)
    coact = _coact_between(inner, a, b)
    attrs = inner.node(coact)["attrs"]
    assert (attrs["evidence_confirm"], attrs["evidence_disconfirm"]) == (4, 0), (
        "must reach the same (4,0) reinforced state test_can_native_reimplementation.py's "
        f"own end-to-end test establishes; got {attrs}"
    )

    inner.set_attr(a, "state", 0.0)  # stop reinforcing -- reweight's own guard now excludes this pair
    trajectory = []
    for tick in range(5, 12):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
        c = inner.node(coact)["attrs"]["evidence_confirm"]
        assert isinstance(c, int), f"tick {tick}: decayed count must stay a real int, got {type(c)}"
        trajectory.append(c)
    print(f"decay trajectory (adaptive, unreinforced from tick 5): confirm={trajectory}")
    assert trajectory == [3, 2, 1, 0, 0, 0, 0], (
        f"expected a strict 1-per-tick linear decrement floored at 0, got {trajectory}"
    )
    assert inner.node(coact)["attrs"]["evidence_disconfirm"] == 0, "disconfirm was already 0, must stay floored there"


def test_evidence_decay_blocked_when_frozen():
    """PREREG Sec1, FROZEN case: the SAME setup, but the Mt's update_policy
    is 'frozen' -- mt_allows(mt,'allow_h_drift') is False unconditionally in
    the continuous mechanism, and this rule's own Term re-expression must
    agree.

    UPDATED (post-merge with CAN_HEBBIAN_MATERIALIZATION_RESULTS.md, commit
    f24e359): can_native_hebbian_mint/reweight are now themselves policy-
    gated (Or(policy-switch, plasticity_override>0)), so under a FROZEN Mt
    with no override, reinforcement never accrues in the first place --
    evidence_confirm/disconfirm stay (0,0) from mint through the end of the
    run. This is a stricter, more coherent invariant than the one originally
    registered here (frozen means frozen for BOTH halves of the ledger, not
    just decay), not a weakening of it -- confirmed live, not assumed."""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, policy="frozen")
    _reinforce_hebbian_pair(inner, mt, a, b, through_tick=4)
    coact = _coact_between(inner, a, b)
    before = dict(inner.node(coact)["attrs"])
    assert (before["evidence_confirm"], before["evidence_disconfirm"]) == (0, 0), (
        "a FROZEN Mt with no plasticity_override must block reinforcement "
        f"itself (Hebbian policy gate), not just decay; got {before}"
    )

    inner.set_attr(a, "state", 0.0)
    for tick in range(5, 12):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    after = inner.node(coact)["attrs"]
    print(f"frozen, unreinforced through tick 11: confirm={after['evidence_confirm']} disconfirm={after['evidence_disconfirm']} "
          f"decay_tick={after.get('decay_tick')}")
    assert (after["evidence_confirm"], after["evidence_disconfirm"]) == (0, 0), (
        f"a FROZEN Mt must never decay OR reinforce -- expected unchanged (0,0), got "
        f"({after['evidence_confirm']}, {after['evidence_disconfirm']})"
    )
    assert after.get("decay_tick") is None, "decay_tick must never be written when the policy blocks decay entirely"


def test_evidence_decay_hybrid_axis_explicit_and_default():
    """PREREG Sec3's registered Term re-expression of mt_allows's HYBRID
    branch: allow_h_drift explicitly 0 blocks decay; allow_h_drift ABSENT
    defaults to allowed (matching Python's `.get(axis, True)`), confirmed
    live against the real engine, not merely asserted from reading term.rs."""
    # Explicit hybrid block.
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, policy="hybrid", extra_mt_attrs={"allow_h_drift": 0})
    _reinforce_hebbian_pair(inner, mt, a, b, through_tick=4)
    coact = _coact_between(inner, a, b)
    inner.set_attr(a, "state", 0.0)
    for tick in range(5, 9):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    blocked = inner.node(coact)["attrs"]
    print(f"hybrid allow_h_drift=0: confirm={blocked['evidence_confirm']} (must stay 4)")
    assert blocked["evidence_confirm"] == 4, "explicit hybrid allow_h_drift=0 must block decay"

    # Default hybrid (attr absent) allows decay.
    s2 = _loaded_substrate()
    inner2 = s2._inner
    mt2, a2, b2 = _isolated_pair(inner2, policy="hybrid")  # no allow_h_drift attr at all
    _reinforce_hebbian_pair(inner2, mt2, a2, b2, through_tick=4)
    coact2 = _coact_between(inner2, a2, b2)
    inner2.set_attr(a2, "state", 0.0)
    for tick in range(5, 9):
        inner2.set_attr(mt2, "can_tick", tick)
        inner2.run_rules(1000)
    allowed = inner2.node(coact2)["attrs"]
    print(f"hybrid allow_h_drift absent (default True): confirm={allowed['evidence_confirm']} (must reach 0)")
    assert allowed["evidence_confirm"] == 0, "hybrid with allow_h_drift unset must default to allowed, per Python's .get(axis, True)"


def test_evidence_decay_never_races_reinforcement_in_the_same_tick():
    """The live correction recorded in seeds/can_decay_identity.json's own
    module comment: a first draft gated decay ONLY on 'can_tick advanced',
    which raced can_native_hebbian_reweight on every reinforcing tick (a
    same-magnitude +1/-1 cancels exactly, unlike the continuous mechanism
    where decay_rate << eta). This test is the regression guard for that
    fix: reinforcing every tick for 6 ticks must show MONOTONIC growth, not
    a flat line."""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, policy="adaptive")
    inner.run_rules(1000)
    for tick in range(1, 6):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    coact = _coact_between(inner, a, b)
    confirm = inner.node(coact)["attrs"]["evidence_confirm"]
    print(f"persistent reinforcement through tick 5: evidence_confirm={confirm} (must be 5, not 0 or 1)")
    assert confirm == 5, (
        f"persistent reinforcement must NOT be canceled by a simultaneously-eligible decay rule "
        f"firing the same tick -- expected 5 (one +1 per tick, ticks 1-5), got {confirm}"
    )


# ---------------------------------------------------------------------
# (b) Identity dynamics as a second evidence axis.
# ---------------------------------------------------------------------

def _committed_concept_setup(inner, mt):
    c = inner.add_node("Concept", {
        "name": "c", "state": 1.0, "external_field": 0.0, "identity_field": 0.0,
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1,
    })
    inner.add_edge(mt, "has_concept", c, {})
    return c


def test_identity_evidence_consistent_state_reads_stronger_than_flipping_state():
    """PREREG Sec2's central registered prediction: a Concept whose sigma is
    CONSISTENTLY +1 across many ticks must read a strictly stronger, growing
    'identity commitment' via the SAME non-materializing log-odds render the
    causal-strength axis already uses, than a Concept whose sigma FLIPS
    every tick -- mirroring can_ops.rs:774's own stated continuous behaviour
    ('flips average to zero -> identity decays toward zero')."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0, "update_policy": "adaptive"})
    consistent = _committed_concept_setup(inner, mt)
    inner.set_attr(consistent, "name", "consistent")
    flipper = inner.add_node("Concept", {
        "name": "flipper", "state": 1.0, "external_field": 0.0, "identity_field": 0.0,
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1,
    })
    inner.add_edge(mt, "has_concept", flipper, {})

    for tick in range(10):
        inner.set_attr(mt, "can_tick", tick)
        inner.set_attr(flipper, "state", 1.0 if tick % 2 == 0 else -1.0)
        inner.run_rules(1000)

    term = _log_odds_term("c", "identity_evidence_confirm", "identity_evidence_disconfirm")
    r_consistent = s.evaluate(term, {"c": consistent})
    r_flipper = s.evaluate(term, {"c": flipper})
    c_attrs = inner.node(consistent)["attrs"]
    f_attrs = inner.node(flipper)["attrs"]
    print(f"consistent: confirm={c_attrs['identity_evidence_confirm']} disconfirm={c_attrs.get('identity_evidence_disconfirm')} "
          f"-> identity_reading={r_consistent:.4f}")
    print(f"flipper:    confirm={f_attrs['identity_evidence_confirm']} disconfirm={f_attrs['identity_evidence_disconfirm']} "
          f"-> identity_reading={r_flipper:.4f}")

    assert c_attrs["identity_evidence_confirm"] == 10, "10 consecutive +1 ticks must all be sampled as confirms"
    assert (f_attrs["identity_evidence_confirm"], f_attrs["identity_evidence_disconfirm"]) == (5, 5), (
        "5 up-ticks and 5 down-ticks must split the ledger evenly"
    )
    assert r_consistent > r_flipper, "the consistently-committed Concept must read a strictly stronger identity"
    assert abs(r_flipper) < 1e-9, "an evenly-split ledger must render EXACTLY neutral (0.0), mirroring the log-odds render's own neutral case"
    assert r_consistent > 0.0, "purely-confirming identity evidence must render strictly positive"

    # Frame/continuum invariant, same guard test_log_odds_render_ranks_evidence_and_never_writes_back
    # already proves for the Hebbian axis: the render must never write back.
    before = {consistent: dict(inner.node(consistent)["attrs"]), flipper: dict(inner.node(flipper)["attrs"])}
    s.evaluate(term, {"c": consistent})
    s.evaluate(term, {"c": flipper})
    for n in (consistent, flipper):
        assert dict(inner.node(n)["attrs"]) == before[n], "the identity reading must never be written back onto the Concept"


def test_identity_evidence_decays_toward_zero_when_unreinforced_and_policy_allows():
    """(a)'s decay shape, reused for the identity ledger (can_native_
    identity_evidence_decay) -- the SAME live correction (skip decay on a
    tick where the sample rule ALSO just fired) applies here from the
    start."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0, "update_policy": "adaptive"})
    c = _committed_concept_setup(inner, mt)

    for tick in range(5):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    grown = inner.node(c)["attrs"]["identity_evidence_confirm"]
    assert grown == 5, f"5 ticks of consistent +1 state must grow confirm to 5, got {grown}"

    inner.set_attr(c, "state", 0.0)  # sampling stops (state==0 excluded); decay now applies
    trajectory = []
    for tick in range(5, 12):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
        trajectory.append(inner.node(c)["attrs"]["identity_evidence_confirm"])
    print(f"identity decay trajectory (unreinforced from tick 5): confirm={trajectory}")
    assert trajectory == [4, 3, 2, 1, 0, 0, 0]


def test_identity_evidence_decay_blocked_when_frozen():
    """(a)'s frozen-blocks-decay case, mirrored for the identity axis."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0, "update_policy": "frozen"})
    c = _committed_concept_setup(inner, mt)
    for tick in range(5):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    before = inner.node(c)["attrs"]["identity_evidence_confirm"]
    print(f"frozen identity ledger before stopping reinforcement: confirm={before}")

    inner.set_attr(c, "state", 0.0)
    for tick in range(5, 12):
        inner.set_attr(mt, "can_tick", tick)
        inner.run_rules(1000)
    after = inner.node(c)["attrs"]["identity_evidence_confirm"]
    print(f"frozen identity ledger after 7 unreinforced ticks: confirm={after} (must be unchanged)")
    assert after == before, "a FROZEN Mt must never decay identity evidence either"


# ---------------------------------------------------------------------
# (c) The recurrence-boost investigation.
# ---------------------------------------------------------------------

def test_recurrence_boost_is_log_scaled_like_the_continuous_nudge_but_not_identical():
    """PREREG Sec2's registered prediction: nudge_identity_on_flipped's
    hand-rolled alpha_eff = base_alpha*(1+ln(max(1,recurrence))) and the
    log-odds render's own natural ln(confirm+1) (when disconfirm==0) are
    BOTH natural-log-scaled, diminishing-marginal-return functions of a
    repetition count -- reported precisely: same SHAPE, not the same
    formula, and not the same underlying count (basin-recurrence vs
    tick-evidence)."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0, "update_policy": "adaptive"})
    c = _committed_concept_setup(inner, mt)
    term = _log_odds_term("c", "identity_evidence_confirm", "identity_evidence_disconfirm")

    checkpoints = (1, 5, 20)
    readings = {}
    tick = 0
    for target_n in checkpoints:
        while inner.node(c)["attrs"]["identity_evidence_confirm"] < target_n:
            inner.set_attr(mt, "can_tick", tick)
            inner.run_rules(1000)
            tick += 1
        readings[target_n] = s.evaluate(term, {"c": c})

    base_alpha = 0.05  # domains/self_improvement_loop.py's own default identity_nudge_alpha
    continuous_boost = {n: base_alpha * (1.0 + math.log(max(1, n))) for n in checkpoints}

    print("n     identity_render=ln(n+1)   continuous_alpha_eff=base*(1+ln(n))")
    for n in checkpoints:
        print(f"{n:<5} {readings[n]:.4f}                     {continuous_boost[n]:.4f}")

    # Both must be strictly increasing and CONCAVE (diminishing marginal
    # return) in the recurrence count -- the shape claim, checked
    # numerically rather than asserted from formula alone.
    render_deltas = [readings[checkpoints[i + 1]] - readings[checkpoints[i]] for i in range(len(checkpoints) - 1)]
    render_marginal_per_step = [d / (checkpoints[i + 1] - checkpoints[i]) for i, d in enumerate(render_deltas)]
    print(f"identity_render marginal gain per additional recurrence, by interval: {render_marginal_per_step}")
    assert readings[1] < readings[5] < readings[20], "identity render must strictly increase with recurrence"
    assert render_marginal_per_step[0] > render_marginal_per_step[1], (
        "the render's marginal gain per additional recurrence must SHRINK (diminishing returns) -- "
        "the same qualitative shape base_alpha*(1+ln(recurrence)) has, confirmed structurally, "
        f"got marginal gains {render_marginal_per_step}"
    )
    # Explicitly NOT claiming numeric identity -- report both numbers, let
    # the record show they differ (registered in PREREG Sec2).
    for n in checkpoints:
        assert readings[n] != continuous_boost[n], (
            "sanity: these are genuinely different formulas over different counts, "
            "not accidentally identical -- if this ever fires equal, the 'not the same "
            "formula' claim above needs re-examination, not silent deletion"
        )
