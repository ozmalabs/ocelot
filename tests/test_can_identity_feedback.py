"""Identity-feedback (`seeds/can_decay_identity.json` v1.2.0,
`can_native_identity_field_feedback`) -- the FEEDBACK half of identity
dynamics, closing the gap `CAN_DECAY_IDENTITY_RESULTS.md`/`CAN_MT_SCOPED_
RULES_RESULTS.md`/`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` all named and
declined to build. See docs/research/engine_substrate/
CAN_IDENTITY_FEEDBACK_PREREG.md for the registered design and
_RESULTS.md for the write-up these tests back.

Four live demonstrations, matching the task's own four registered asks:
  (a) test_identity_field_grows_and_commits_under_consistent_sigma --
      consistent sigma, discrete_mode='static' (isolates the feedback rule
      from can_native_update_3state/_2state, the SAME isolation
      test_can_decay_identity.py's own reading-half test already uses) --
      identity_field moves in ONE direction, monotonically, never negative.
  (b) test_identity_field_decays_toward_zero_under_flip_flop_sigma -- same
      isolation, flip-flopping sigma -- identity_field ends at/near zero,
      mirroring can_ops.rs:774's own docstring.
  (c) test_discrete_async_convergence_holds_with_identity_feedback_active --
      THE load-bearing check. A real 60-draw sample (30 coarse + 30 fine),
      discrete_mode='3state' (the deadzone case, the named theoretical
      risk), each draw driven across multiple real ticks with the
      identity-feedback rule live in the SAME run_rules fixpoint as
      can_native_update_3state -- reports the real non-convergence count.
      A secondary, non-headline 60-draw sweep repeats this for '2state'.
  (d) test_two_mt_isolation_holds_with_identity_feedback_active -- reuses
      test_can_mt_scoped_consumers.py's own _isolated_pair pattern, confirms
      the new rule never perturbs an untouched sibling Mt.
"""
from __future__ import annotations

import json
import math
import random

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from substrate_rs import Term

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


def _log_odds_term(node_var, confirm_key, disconfirm_key):
    """The SAME non-materializing log-odds render Term
    test_can_decay_identity.py::_log_odds_term already establishes --
    reused here unmodified, purely to CROSS-CHECK the rule's own internal
    sign logic against an independent evaluation, not to duplicate it."""
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


# ---------------------------------------------------------------------
# (a)/(b) The feedback rule's own shape, isolated from the discrete
# update (discrete_mode='static'), mirroring the reading-half tests'
# own isolation discipline exactly.
# ---------------------------------------------------------------------

def _feedback_concept_setup(inner, mt, name="c"):
    c = inner.add_node("Concept", {
        "name": name, "state": 1.0, "external_field": 0.0, "identity_field": 0.0,
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1,
        "identity_field_tick": -1,
    })
    inner.add_edge(mt, "has_concept", c, {})
    return c


def test_identity_field_grows_and_commits_under_consistent_sigma():
    """PREREG Sec5(a)'s registered prediction: a Concept whose sigma is
    CONSISTENTLY +1 across many ticks must show identity_field moving in
    ONE consistent direction (same sign every step it changes), growing in
    magnitude, never negative -- the fixed 1-quantum-per-tick step (PREREG
    Sec2.1) toward the render's sign."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c = _feedback_concept_setup(inner, mt)

    trajectory = []
    for tick in range(10):
        inner.set_attr(mt, "can_tick", tick)
        inner.set_attr(c, "state", 1.0)
        inner.run_rules(1000)
        trajectory.append(inner.node(c)["attrs"]["identity_field"])

    print(f"identity_field trajectory (consistent sigma=+1, 10 ticks): {trajectory}")
    assert trajectory == [float(i + 1) for i in range(10)], (
        "exactly one +1 quantum per tick under sustained positive sigma"
    )
    assert all(trajectory[i] < trajectory[i + 1] for i in range(len(trajectory) - 1)), (
        "identity_field must grow strictly monotonically under sustained agreement"
    )
    assert all(v >= 0 for v in trajectory), "must never go negative under positive sigma"
    # Bounded WITHIN this finite run (PREREG Sec2.4's honest framing -- no
    # hard cap is built; the bound below is this test's own finite window).
    assert trajectory[-1] == 10.0


def test_identity_field_grows_negative_under_consistent_negative_sigma():
    """The mirror-image direction -- registered as part of the same
    prediction (PREREG Sec2.1's IfThenElse is symmetric)."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c = _feedback_concept_setup(inner, mt)

    trajectory = []
    for tick in range(6):
        inner.set_attr(mt, "can_tick", tick)
        inner.set_attr(c, "state", -1.0)
        inner.run_rules(1000)
        trajectory.append(inner.node(c)["attrs"]["identity_field"])

    print(f"identity_field trajectory (consistent sigma=-1, 6 ticks): {trajectory}")
    assert trajectory == [-float(i + 1) for i in range(6)]
    assert all(v <= 0 for v in trajectory)


def test_identity_field_decays_toward_zero_under_flip_flop_sigma():
    """PREREG Sec5(b): mirrors can_ops.rs:774's own docstring, 'flipping
    sigma averages to near zero -> identity decays toward zero.' 10 ticks,
    same even/odd split test_can_decay_identity.py's own flipper test uses
    -- ends on a tick where confirm==disconfirm (5/5), so the render is
    EXACTLY neutral and the clamp-toward-zero branch fires."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c = _feedback_concept_setup(inner, mt)

    trajectory = []
    for tick in range(10):
        inner.set_attr(mt, "can_tick", tick)
        inner.set_attr(c, "state", 1.0 if tick % 2 == 0 else -1.0)
        inner.run_rules(1000)
        trajectory.append(inner.node(c)["attrs"]["identity_field"])

    attrs = inner.node(c)["attrs"]
    print(f"identity_field trajectory (flip-flop sigma, 10 ticks): {trajectory}")
    print(f"final ledger: confirm={attrs['identity_evidence_confirm']} disconfirm={attrs['identity_evidence_disconfirm']}")
    assert (attrs["identity_evidence_confirm"], attrs["identity_evidence_disconfirm"]) == (5, 5)
    assert trajectory[-1] == 0.0, "an evenly-split ledger must render neutral, decaying identity_field to exactly 0.0"
    assert max(trajectory) <= 1.0, "a flip-flopping Concept must never build meaningful identity commitment"


def test_identity_field_feedback_matches_independent_logodds_sign_readback():
    """Cross-check: the rule's own internal IfThenElse sign decision must
    agree with an INDEPENDENT evaluation of the same log-odds Term via
    Substrate.evaluate (the SAME cross-check discipline test_can_decay_
    identity.py's own tests use for the reading half)."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
        "update_policy": "adaptive",
    })
    c = _feedback_concept_setup(inner, mt)
    for tick in range(7):
        inner.set_attr(mt, "can_tick", tick)
        inner.set_attr(c, "state", 1.0 if tick != 3 else -1.0)  # mostly positive, one dissent
        inner.run_rules(1000)

    term = _log_odds_term("c", "identity_evidence_confirm", "identity_evidence_disconfirm")
    reading = s.evaluate(term, {"c": c})
    identity_field = inner.node(c)["attrs"]["identity_field"]
    print(f"independent logodds readback={reading:.4f} identity_field={identity_field}")
    assert reading > 0, "6 confirms vs 1 disconfirm must render strictly positive"
    assert identity_field > 0, "identity_field must have moved positive, matching the render's sign"


def test_identity_field_feedback_frozen_never_fires():
    """Policy respect, the SAME allow_h_drift axis every rule in this seed
    checks -- a frozen Mt's identity_field must never move even though the
    evidence ledger (governed by the SAME axis on the sampling rule) also
    never accrues."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "static", "can_tick": 0,
        "update_policy": "frozen",
    })
    c = _feedback_concept_setup(inner, mt)
    for tick in range(8):
        inner.set_attr(mt, "can_tick", tick)
        inner.set_attr(c, "state", 1.0)
        inner.run_rules(1000)
    attrs = inner.node(c)["attrs"]
    print(f"frozen, 8 ticks of sigma=+1: identity_field={attrs['identity_field']} identity_field_tick={attrs.get('identity_field_tick')}")
    assert attrs["identity_field"] == 0.0
    assert attrs.get("identity_field_tick") == -1, "the rule must never even fire under frozen"


# ---------------------------------------------------------------------
# (c) THE load-bearing check: discrete-async convergence with
# identity-feedback active, real draws, real numbers.
# ---------------------------------------------------------------------

def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_draw(seed, coarse, discrete_mode="3state"):
    """BYTE-IDENTICAL construction to test_can_native_reimplementation.py's
    own _build_draw (N=8 complete graph, symmetric causal_influence edges,
    external_field ~ Uniform(-1,1), weight rounded to coarse/fine vocab),
    with the ONE addition this rung needs: both seeds loaded (so the new
    identity-feedback rule is live in the SAME run_rules fixpoint as
    can_native_update_3state/_2state), and the identity-evidence ledger
    attrs pre-initialized (matching test_can_decay_identity.py's own
    _feedback_concept_setup convention)."""
    s = _loaded_substrate()
    inner = s._inner
    pair_rng = random.Random(seed * 31 + N)
    field_rng = random.Random(seed * 53 + N)
    mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": discrete_mode, "can_tick": 0,
        "update_policy": "adaptive",
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
            "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
            "identity_evidence_tick": -1, "identity_decay_tick": -1,
            "identity_field_tick": -1,
        })
        for i in range(N)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
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
N_TICKS = 15  # multiple real ticks per draw -- gives the identity-feedback
              # rule repeated real opportunities to perturb identity_field
              # WHILE the discrete update is also live, exercising the
              # actual risk named in PREREG Sec4.1 (not a single-tick,
              # diminished version of it).


def _drive_and_check_convergence(inner, mt, max_steps=3000):
    """Advances can_tick by 1 and runs run_rules() to fixpoint, at EACH of
    N_TICKS ticks -- returns the count of ticks where the discrete update
    failed to reach a fixpoint within max_steps (0 is the GO bar, PREREG
    Sec4.3)."""
    nonconv_ticks = 0
    for tick in range(1, N_TICKS + 1):
        inner.set_attr(mt, "can_tick", tick)
        steps = inner.run_rules(max_steps)
        if steps >= max_steps:
            nonconv_ticks += 1
    return nonconv_ticks


@pytest.mark.parametrize("discrete_mode", ["3state", "2state"])
def test_discrete_async_convergence_holds_with_identity_feedback_active(discrete_mode):
    """PREREG Sec4 -- the single most important check in this rung. 60 real
    draws (30 coarse + 30 fine), each driven across N_TICKS=15 real ticks
    with can_native_identity_field_feedback live in the SAME run_rules
    fixpoint as can_native_update_3state/_2state. Reports the real
    non-convergence count -- GO iff 0/60 draws show ANY non-convergent
    tick anywhere in their own 15-tick drive."""
    rows = []
    total_nonconv_draws = 0
    total_nonconv_ticks = 0
    for coarse in (True, False):
        nonconv_draws = 0
        nonconv_ticks_this_cond = 0
        for i in range(N_DRAWS):
            seed = 5000 + i
            s, mt, concepts = _build_draw(seed, coarse, discrete_mode)
            inner = s._inner
            # tick 0: let the discrete update settle once before driving
            # further ticks (mirrors _build_draw's own zero-start convention).
            inner.run_rules(3000)
            nonconv = _drive_and_check_convergence(inner, mt)
            if nonconv > 0:
                nonconv_draws += 1
            nonconv_ticks_this_cond += nonconv
        label = "coarse" if coarse else "fine"
        rows.append((label, nonconv_draws, nonconv_ticks_this_cond))
        total_nonconv_draws += nonconv_draws
        total_nonconv_ticks += nonconv_ticks_this_cond
        print(f"[{discrete_mode}] {label:8s} nonconv_draws={nonconv_draws}/{N_DRAWS} "
              f"nonconv_ticks={nonconv_ticks_this_cond}/{N_DRAWS * N_TICKS}")

    print(f"[{discrete_mode}] TOTAL nonconv_draws={total_nonconv_draws}/{2 * N_DRAWS} "
          f"nonconv_ticks={total_nonconv_ticks}/{2 * N_DRAWS * N_TICKS}")

    for label, nonconv_draws, nonconv_ticks in rows:
        assert nonconv_draws == 0, (
            f"identity-feedback ({discrete_mode}) broke convergence on "
            f"{nonconv_draws}/{N_DRAWS} {label} draws ({nonconv_ticks} total "
            f"non-convergent ticks) -- the discrete-async Lyapunov guarantee "
            f"did not survive the feedback loop on this sample"
        )


# ---------------------------------------------------------------------
# (d) Two-Mt isolation with identity-feedback active.
# ---------------------------------------------------------------------

def _isolated_pair(inner, policy="adaptive", discrete_mode="3state"):
    """BYTE-IDENTICAL to test_can_mt_scoped_consumers.py's own
    _isolated_pair (strong equal external fields so the discrete update
    converges both Concepts to the same committed nonzero state)."""
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": discrete_mode, "can_tick": 0,
        "update_policy": policy,
    })
    a = inner.add_node("Concept", {
        "name": "a", "state": 0.0, "external_field": 5.0, "identity_field": 0.0,
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1, "identity_field_tick": -1,
    })
    b = inner.add_node("Concept", {
        "name": "b", "state": 0.0, "external_field": 5.0, "identity_field": 0.0,
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1, "identity_field_tick": -1,
    })
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    return mt, a, b


def test_two_mt_isolation_holds_with_identity_feedback_active():
    """PREREG Sec4.4 / Sec5(d): a second, untouched sibling Mt in the same
    graph must be completely unaffected while the target Mt's
    identity-feedback rule (reached via scoped_settle, the SAME mechanism
    self_improvement_loop.maybe_update_identity's native branch calls) runs
    across multiple ticks."""
    from domains.self_improvement_loop import maybe_update_identity

    s = _loaded_substrate()
    inner = s._inner
    mt_native, a, b = _isolated_pair(inner, policy="adaptive")
    mt_other, c, d = _isolated_pair(inner, policy="adaptive")  # untouched control

    before_other = {n.value: dict(inner.node(n)["attrs"]) for n in (c, d)}

    for tick in range(1, 6):
        inner.set_attr(mt_native, "can_tick", tick)
        maybe_update_identity(inner, mt_native)

    after_other = {n.value: dict(inner.node(n)["attrs"]) for n in (c, d)}
    a_after = inner.node(a)["attrs"]
    b_after = inner.node(b)["attrs"]
    print(f"mt_native after 5 ticks: a.identity_field={a_after['identity_field']} "
          f"b.identity_field={b_after['identity_field']}")
    print(f"mt_other (untouched control) can_tick={inner.node(mt_other)['attrs'].get('can_tick')}")

    for key in ("state", "identity_field", "external_field",
                "identity_evidence_confirm", "identity_evidence_disconfirm"):
        assert before_other[c.value][key] == after_other[c.value][key], (
            f"untouched sibling Mt's Concept c.{key} changed while operating on mt_native -- "
            f"identity-feedback leaked across Mts"
        )
        assert before_other[d.value][key] == after_other[d.value][key], (
            f"untouched sibling Mt's Concept d.{key} changed while operating on mt_native -- "
            f"identity-feedback leaked across Mts"
        )
    assert inner.node(mt_other)["attrs"].get("can_tick", 0) == 0, (
        "the untouched sibling Mt's own can_tick must never advance"
    )
