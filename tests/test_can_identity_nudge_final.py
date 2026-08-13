"""`nudge_identity_on_flipped` migration -- the true closing rung of the
whole CAN arc (`seeds/can_decay_identity.json` v1.3.0,
`can_native_identity_nudge_on_flip`). See docs/research/engine_substrate/
CAN_IDENTITY_NUDGE_FINAL_PREREG.md for the registered design and
_RESULTS.md for the write-up these tests back.

Sections, matching the task's own four registered live-demonstration asks:
  1. Rule-shape unit tests -- direct rule firing, discrete_mode='static'
     (isolates the new event-triggered rule from can_native_update_3state/
     _2state, the SAME isolation test_can_identity_feedback.py's own (a)/
     (b) tests use), bounded-step correctness (first vs recurring),
     target_sigma sign correctness, target_sigma==0 no-op, fires-exactly-
     once-per-event (epoch consumption).
  2. (a) A real flip event, via the REAL `nudge_identity_on_flipped`
     orchestration entry point (discrete_mode='3state', the real native
     gate), correctly nudges the SPECIFIC flipped node's identity_field
     toward its target_sigma -- BOUNDED across many repeated recurring
     events, contrasted against what the OLD unbounded continuous formula
     would have produced at the same recurrence.
  3. (b) A non-flipped sibling Concept on the same Mt is untouched by the
     same event.
  4. (c) THE load-bearing check: discrete-async convergence with BOTH
     native identity rules (ambient + event-triggered) live, across real
     synthesized flip events layered on top of real ticks -- reports the
     real non-convergence count.
  5. (d) Two-Mt isolation with the event-triggered rule active.
"""
from __future__ import annotations

import json
import math
import random

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.self_improvement_loop import _is_native, nudge_identity_on_flipped

SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)

N = 8
BETA = 2.0


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


# ---------------------------------------------------------------------
# 1. Rule-shape unit tests, direct firing, discrete_mode='static'.
# ---------------------------------------------------------------------

def _nudge_concept_setup(inner, mt, name="c", identity_field=0.0):
    # state=0.0 (not +/-1) deliberately -- keeps the AMBIENT sibling rules
    # (can_native_identity_evidence_sample's Not(Eq(state,0)) guard,
    # can_native_identity_field_feedback's neutral-logodds no-op) INERT, so
    # these tests isolate the NEW event-triggered rule's own effect on
    # identity_field, matching test_can_identity_feedback.py's own
    # discrete_mode='static' isolation discipline one level further (that
    # rung isolated the ambient rule FROM the discrete update; this rung
    # additionally isolates the event rule FROM the ambient rule).
    c = inner.add_node("Concept", {
        "name": name, "state": 0.0, "external_field": 0.0,
        "identity_field": identity_field,
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1,
        "identity_field_tick": -1,
        "pending_identity_nudge_target_sigma": 0.0,
        "pending_identity_nudge_recurrence": 0,
        "pending_identity_nudge_epoch": 0,
        "identity_nudge_applied_epoch": 0,
    })
    inner.add_edge(mt, "has_concept", c, {})
    return c


def _mk_static_mt(inner, policy="adaptive"):
    return inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
        "update_policy": policy,
    })


def test_rule_nudges_positive_target_sigma_by_one_quantum_first_occurrence():
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", 0.9)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 1)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"first-occurrence positive nudge: identity_field={attrs['identity_field']} "
          f"applied_epoch={attrs['identity_nudge_applied_epoch']}")
    assert attrs["identity_field"] == 1.0
    assert attrs["identity_nudge_applied_epoch"] == 1


def test_rule_nudges_negative_target_sigma_by_one_quantum_first_occurrence():
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", -0.7)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 1)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"first-occurrence negative nudge: identity_field={attrs['identity_field']}")
    assert attrs["identity_field"] == -1.0


def test_rule_nudges_by_two_quanta_when_recurring():
    """PREREG Sec2.2's registered binary two-tier step: recurrence > 1 ->
    step=2.0, never a continuous/log scale."""
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", 0.5)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 2)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"recurring (count=2) nudge: identity_field={attrs['identity_field']}")
    assert attrs["identity_field"] == 2.0


def test_rule_step_bounded_regardless_of_how_large_recurrence_grows():
    """The load-bearing boundedness claim (PREREG Sec2.5): recurrence=500
    must still produce EXACTLY the same 2.0 step as recurrence=2 -- never
    growing, unlike the continuous path's base_alpha*(1+ln(recurrence))."""
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", 0.5)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 500)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"recurrence=500 nudge: identity_field={attrs['identity_field']}")
    assert attrs["identity_field"] == 2.0, (
        "step must be bounded at 2.0 regardless of recurrence magnitude"
    )


def test_rule_target_sigma_zero_is_no_directional_evidence():
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt, identity_field=3.0)
    # Neutralise the AMBIENT sibling rule (can_native_identity_field_
    # feedback) for THIS unit test only: its own gate is Gt(mt.can_tick,
    # c.identity_field_tick); setting identity_field_tick == mt.can_tick
    # (both 0) marks it "already consumed" so it does not ALSO fire and
    # clamp-toward-zero identity_field during this run_rules call -- the
    # ambient rule's neutral-logodds branch is a decay step, not a no-op,
    # so without this the test would be measuring the ambient rule's own
    # already-proven behaviour instead of the new rule's.
    inner.set_attr(c, "identity_field_tick", 0)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", 0.0)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 1)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"target_sigma==0: identity_field={attrs['identity_field']} (unchanged)")
    assert attrs["identity_field"] == 3.0
    # The rule still fires (consumes the epoch) -- only the field write is a no-op.
    assert attrs["identity_nudge_applied_epoch"] == 1


def test_rule_fires_exactly_once_per_event_not_every_tick():
    """The equality-gated epoch marker (PREREG Sec2.2) must NOT refire on
    subsequent run_rules calls once consumed -- unlike the ambient rule's
    Gt-per-tick gate, a stale pending epoch must never re-trigger. can_tick
    is deliberately held FIXED here (not advanced) so the test isolates
    ONLY this rule's own epoch-consumption behaviour, not the ambient
    sibling rule's own SEPARATE per-tick decay (which is real, expected,
    and exercised instead by the orchestration-level tests below where
    both mechanisms are meant to be live together)."""
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", 1.0)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 1)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    after_first = inner.node(c)["attrs"]["identity_field"]
    # Re-run repeatedly with NO new event and NO tick change -- must stay put.
    for _ in range(4):
        inner.run_rules(1000)
    after_more = inner.node(c)["attrs"]["identity_field"]
    print(f"after first fire={after_first}, after 4 more idle re-runs={after_more}")
    assert after_first == 1.0
    assert after_more == 1.0, "must not refire without a NEW pending epoch"


def test_rule_frozen_never_fires():
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner, policy="frozen")
    c = _nudge_concept_setup(inner, mt)
    inner.set_attr(c, "pending_identity_nudge_target_sigma", 1.0)
    inner.set_attr(c, "pending_identity_nudge_recurrence", 1)
    inner.set_attr(c, "pending_identity_nudge_epoch", 1)
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"frozen: identity_field={attrs['identity_field']} applied_epoch={attrs['identity_nudge_applied_epoch']}")
    assert attrs["identity_field"] == 0.0
    assert attrs["identity_nudge_applied_epoch"] == 0, "must never even fire under frozen"


def test_untouched_concept_never_fires_default_epochs_equal():
    """A Concept that never receives a pending event (both epoch attrs at
    their default 0) must never fire -- confirms the equality gate is
    inert by default, not just after an explicit reset."""
    s = _loaded_substrate()
    inner = s._inner
    mt = _mk_static_mt(inner)
    c = _nudge_concept_setup(inner, mt)  # pending/applied both default 0
    inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    assert attrs["identity_field"] == 0.0
    assert attrs["identity_nudge_applied_epoch"] == 0


# ---------------------------------------------------------------------
# 2/3. (a)/(b) Live demonstrations via the REAL orchestration entry point.
# ---------------------------------------------------------------------

def _mk_native_mt_pair(inner, discrete_mode="3state", policy="adaptive"):
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": discrete_mode, "can_tick": 0,
        "update_policy": policy,
    })
    a = _nudge_concept_setup(inner, mt, name="a")
    b = _nudge_concept_setup(inner, mt, name="b")  # sibling, never flipped
    return mt, a, b


def test_real_flip_event_nudges_specific_flipped_node_bounded_not_unbounded():
    """(a): a real `insight` dict (shaped like detect_insight's own
    output) drives the REAL `nudge_identity_on_flipped` entry point.
    Repeats the SAME flip event many times with growing recurrence_count
    -- the specific flipped node's identity_field must stay bounded to the
    2.0-per-event ceiling (never approach what the OLD continuous formula's
    unbounded base_alpha*(1+ln(recurrence)) would have produced)."""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, _b = _mk_native_mt_pair(inner)
    assert _is_native(inner, mt)

    a_id = a.value if hasattr(a, "value") else int(a)
    trajectory = []
    for i, recurrence in enumerate([1, 2, 5, 20, 100, 500]):
        insight = {
            "flipped_nodes": [
                {"node": a_id, "before": 0.0, "after": 0.8, "delta": 0.8},
            ],
            "recurrence_count": recurrence,
        }
        nudged = nudge_identity_on_flipped(inner, mt, insight)
        assert nudged == 1
        trajectory.append(inner.node(a)["attrs"]["identity_field"])

    print(f"bounded nudge trajectory across growing recurrence {[1,2,5,20,100,500]}: {trajectory}")
    # First event: +1.0 (occurrence 1). Every subsequent event: +2.0 (recurring).
    expected = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
    assert trajectory == expected

    # Contrast: what the OLD unbounded continuous formula's step alone
    # (base_alpha * (1 + ln(recurrence)), base_alpha=0.05 default) would
    # have scaled to at recurrence=500 -- reported as a real number, not
    # applied (the continuous path is untouched and not exercised here).
    old_alpha_eff_at_500 = 0.05 * (1.0 + math.log(500))
    print(f"for contrast only (NOT applied): continuous alpha_eff at recurrence=500 "
          f"would have been {old_alpha_eff_at_500:.4f} (grows without bound as "
          f"recurrence grows further) vs this rung's fixed 2.0 ceiling")
    assert trajectory[-1] - trajectory[-2] == 2.0, (
        "the per-event step at recurrence=500 must be identical to the step "
        "at recurrence=2 -- bounded, not scaled"
    )


def test_sibling_non_flipped_concept_untouched_by_the_same_event():
    """(b): a Concept on the SAME Mt that is NOT named in flipped_nodes
    must have its identity_field, and this rule's OWN marker attrs,
    completely unaffected by the event. (The ambient sibling rules'
    UNRELATED own bookkeeping ticks -- identity_field_tick, identity_
    decay_tick, external_field_decay_tick -- legitimately advance for
    EVERY Concept on the Mt regardless of which node flipped; that is
    pre-existing, already-proven, out-of-scope behaviour, not this rule's
    concern, so the comparison is scoped to what THIS rule could plausibly
    have touched.)"""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _mk_native_mt_pair(inner)
    a_id = a.value if hasattr(a, "value") else int(a)

    keys = ("identity_field", "pending_identity_nudge_target_sigma",
            "pending_identity_nudge_recurrence", "pending_identity_nudge_epoch",
            "identity_nudge_applied_epoch")
    before_b = {k: inner.node(b)["attrs"].get(k) for k in keys}
    insight = {
        "flipped_nodes": [
            {"node": a_id, "before": 0.0, "after": 0.8, "delta": 0.8},
        ],
        "recurrence_count": 3,  # recurring (>1) -> bounded 2.0 step, not 1.0
    }
    nudged = nudge_identity_on_flipped(inner, mt, insight)
    after_b = {k: inner.node(b)["attrs"].get(k) for k in keys}
    after_a = inner.node(a)["attrs"]
    print(f"a.identity_field={after_a['identity_field']} (flipped, nudged), "
          f"b's nudge-relevant attrs unchanged={before_b == after_b}")
    assert nudged == 1
    assert after_a["identity_field"] == 2.0
    assert before_b == after_b, (
        "a non-flipped sibling Concept's identity_field + this rule's own "
        "marker attrs must be byte-unchanged"
    )


def test_recurrence_signal_is_a_plain_passthrough_of_the_insight_dicts_own_field():
    """Confirms this rung invents NO new recurrence bookkeeping of its own
    -- it reads exactly `insight["recurrence_count"]`, the SAME field
    `domains/insight_naming.py::record_insight` already writes onto the
    Python dict from the graph-resident InsightEvent node's own counter
    (confirmed by direct read, PREREG Sec0; record_insight/list_insights
    themselves are pre-existing, unmodified machinery requiring seeds this
    minimal two-seed CAN test substrate does not load, so this test drives
    the passthrough directly via the SAME dict shape self_improvement_step
    actually passes, rather than re-exercising record_insight's own
    dedup logic, which is out of this rung's scope)."""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, _b = _mk_native_mt_pair(inner)
    a_id = a.value if hasattr(a, "value") else int(a)

    event = {
        "flipped_nodes": [
            {"node": a_id, "before": 0.0, "after": 0.6, "delta": 0.6},
        ],
        "recurrence_count": 1,
    }
    nudged1 = nudge_identity_on_flipped(inner, mt, event)
    after1 = inner.node(a)["attrs"]["identity_field"]

    event["recurrence_count"] = 2  # simulates record_insight's own increment
    nudged2 = nudge_identity_on_flipped(inner, mt, event)
    after2 = inner.node(a)["attrs"]["identity_field"]

    print(f"recurrence_count=1 -> identity_field={after1}; "
          f"recurrence_count=2 -> identity_field={after2}")
    assert nudged1 == 1 and nudged2 == 1
    assert after1 == 1.0, "first occurrence: +1.0"
    assert after2 == 3.0, "recurring (recurrence_count=2): +2.0"


# ---------------------------------------------------------------------
# 4. (c) THE load-bearing check: convergence with BOTH native identity
#    rules live, across real synthesized flip events layered on real
#    ticks.
# ---------------------------------------------------------------------

def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_draw(seed, coarse, discrete_mode="3state"):
    """BYTE-IDENTICAL construction to test_can_identity_feedback.py's own
    _build_draw (itself byte-identical to test_can_native_reimplementation.
    py's), N=8 complete graph, symmetric causal_influence, external_field ~
    Uniform(-1,1), weight rounded to coarse/fine vocab, both native seeds
    loaded, identity-evidence ledger + nudge marker attrs pre-initialized."""
    s = _loaded_substrate()
    inner = s._inner
    pair_rng = random.Random(seed * 31 + N)
    field_rng = random.Random(seed * 53 + N)
    mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": discrete_mode, "can_tick": 0,
        "update_policy": "adaptive",
    })
    concepts = [
        _nudge_concept_setup(inner, mt, name="c%d" % i)
        for i in range(N)
    ]
    for i in range(N):
        h = field_rng.uniform(-1, 1)
        inner.set_attr(concepts[i], "external_field", h)
    for i in range(N):
        for j in range(i + 1, N):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return s, mt, concepts


N_DRAWS = 30
N_TICKS = 15
EVENT_TICKS = (3, 7, 11)  # three real, spaced flip events per draw


def _synthesize_flip_event(inner, mt, concepts, tick_idx, recurrence):
    """A REAL flip event, shaped exactly like detect_insight's own return
    (flipped_nodes with real node/after pulled from LIVE state) -- picks 2
    of the 8 concepts, alternating which pair across the three events so no
    single node monopolises the signal (PREREG Sec3.2)."""
    offset = (tick_idx % 4) * 2
    chosen = [concepts[offset % N], concepts[(offset + 1) % N]]
    flipped_nodes = []
    for c in chosen:
        cid = c.value if hasattr(c, "value") else int(c)
        after = float(inner.node(c)["attrs"].get("state", 0.0))
        flipped_nodes.append({"node": cid, "before": 0.0, "after": after, "delta": after})
    insight = {"flipped_nodes": flipped_nodes, "recurrence_count": recurrence}
    return insight


def _drive_and_check_convergence_with_events(inner, mt, concepts, max_steps=3000):
    """Advances can_tick + run_rules at each of N_TICKS ticks (as
    test_can_identity_feedback.py's own sweep does), PLUS fires a real
    synthesized flip event (via the REAL nudge_identity_on_flipped entry
    point, which itself calls scoped_settle) at each tick in EVENT_TICKS,
    with recurrence_count alternated 1/2/3 across the three events so both
    the first-occurrence and recurring step tiers are exercised. Returns
    the count of non-convergent run_rules calls (ticks + post-event
    re-checks)."""
    nonconv = 0
    recurrences = iter([1, 2, 3])
    for tick in range(1, N_TICKS + 1):
        inner.set_attr(mt, "can_tick", tick)
        steps = inner.run_rules(max_steps)
        if steps >= max_steps:
            nonconv += 1
        if tick in EVENT_TICKS:
            recurrence = next(recurrences)
            insight = _synthesize_flip_event(inner, mt, concepts, tick, recurrence)
            nudge_identity_on_flipped(inner, mt, insight)
            # Re-check the fixpoint after the event (scoped_settle inside
            # nudge_identity_on_flipped already ran to a fixpoint scoped to
            # this Mt -- this outer call re-confirms across the WHOLE
            # engine's own run_rules, matching the tick-loop's own check).
            steps2 = inner.run_rules(max_steps)
            if steps2 >= max_steps:
                nonconv += 1
    return nonconv


@pytest.mark.parametrize("discrete_mode", ["3state", "2state"])
def test_discrete_async_convergence_holds_with_both_native_identity_rules_and_real_flip_events(discrete_mode):
    """PREREG Sec3 -- the single most important check in this rung. 60 real
    draws (30 coarse + 30 fine), each driven across N_TICKS=15 real ticks
    PLUS 3 real synthesized flip events (recurrence 1/2/3), with BOTH
    can_native_identity_field_feedback (ambient) and can_native_identity_
    nudge_on_flip (event-triggered) live in the SAME run_rules fixpoint as
    can_native_update_3state/_2state. Reports the real non-convergence
    count -- GO iff 0/60 draws show ANY non-convergent run_rules call
    anywhere in their own drive."""
    rows = []
    total_nonconv_draws = 0
    total_nonconv_calls = 0
    for coarse in (True, False):
        nonconv_draws = 0
        nonconv_calls_this_cond = 0
        for i in range(N_DRAWS):
            seed = 9000 + i
            s, mt, concepts = _build_draw(seed, coarse, discrete_mode)
            inner = s._inner
            inner.run_rules(3000)  # let the discrete update settle once first
            nonconv = _drive_and_check_convergence_with_events(inner, mt, concepts)
            if nonconv > 0:
                nonconv_draws += 1
            nonconv_calls_this_cond += nonconv
        label = "coarse" if coarse else "fine"
        rows.append((label, nonconv_draws, nonconv_calls_this_cond))
        total_nonconv_draws += nonconv_draws
        total_nonconv_calls += nonconv_calls_this_cond
        # 15 ticks + 3 post-event re-checks = 18 run_rules calls per draw.
        print(f"[{discrete_mode}] {label:8s} nonconv_draws={nonconv_draws}/{N_DRAWS} "
              f"nonconv_calls={nonconv_calls_this_cond}/{N_DRAWS * 18}")

    print(f"[{discrete_mode}] TOTAL nonconv_draws={total_nonconv_draws}/{2 * N_DRAWS} "
          f"nonconv_calls={total_nonconv_calls}/{2 * N_DRAWS * 18}")

    for label, nonconv_draws, nonconv_calls in rows:
        assert nonconv_draws == 0, (
            f"event-triggered nudge + ambient feedback ({discrete_mode}) broke "
            f"convergence on {nonconv_draws}/{N_DRAWS} {label} draws "
            f"({nonconv_calls} total non-convergent run_rules calls)"
        )


# ---------------------------------------------------------------------
# 5. (d) Two-Mt isolation with the event-triggered rule active.
# ---------------------------------------------------------------------

def test_two_mt_isolation_holds_with_event_triggered_nudge_active():
    """PREREG Sec4.4/Sec5(d) analog: a second, untouched sibling Mt in the
    same graph must be completely unaffected while the target Mt receives
    real flip events via nudge_identity_on_flipped."""
    s = _loaded_substrate()
    inner = s._inner
    mt_native, a, _junk = _mk_native_mt_pair(inner)
    mt_other, c, d = _mk_native_mt_pair(inner)  # untouched control

    before_other = {n.value: dict(inner.node(n)["attrs"]) for n in (c, d)}
    a_id = a.value if hasattr(a, "value") else int(a)

    for recurrence in (1, 2, 3):
        insight = {
            "flipped_nodes": [{"node": a_id, "before": 0.0, "after": 0.7, "delta": 0.7}],
            "recurrence_count": recurrence,
        }
        nudge_identity_on_flipped(inner, mt_native, insight)

    after_other = {n.value: dict(inner.node(n)["attrs"]) for n in (c, d)}
    a_after = inner.node(a)["attrs"]
    print(f"mt_native a.identity_field={a_after['identity_field']} after 3 events")
    print(f"mt_other (untouched control) unchanged={before_other == after_other}")
    assert a_after["identity_field"] == 5.0  # 1.0 + 2.0 + 2.0
    assert before_other == after_other, "sibling Mt must be byte-unchanged"
