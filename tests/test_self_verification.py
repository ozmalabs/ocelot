"""test_self_verification — pins domains/self_verification.py, the NOT-FOOLING-
ITSELF faculty: a CLAIM -> mint a discriminative ControlProbe -> gate on
(control discriminates) AND (no regression) AND (grounding-reach), the gate
decided by a graph-resident Rule in Rust (tick), not a Python if/else.

The battery is DISCRIMINATIVE (donkey=0 — no LM, no fit; every verdict comes
from the Rust term-tree over measured graph attrs):

  (1) CATCHES A FAKE (headline): a tuned-to-pass / overfit claim is REJECTED
      because the control (a held-out item) does NOT survive the mechanism.
  (2) ACCEPTS A REAL: the same faculty, opposite verdict — a genuinely-grounded
      claim whose control discriminates (real survives, known-fake fails) +
      no-regression + grounded is ACCEPTED. Same code, verdict flips only on
      whether the control actually discriminates.
  (3) GROUNDING-REACH GATE: a claim that discriminates AND has no regression
      but whose support reaches NO anchor (a confident ungrounded basin) is
      REJECTED anyway.
  (4) THIS-SESSION GUARD MIRROR: a "token-inflated microtheory" style claim (a
      pass achieved by inflation, not real structure) is rejected — the control
      is "does it still hold on a held-out item without the inflation".
  (5) NO-TEETH CONTROL: a control a known-fake twin also passes does NOT
      discriminate -> rejected (can't verify with a toothless control).
  (6) REGRESSION: a change that breaks a previously-holding case is rejected
      even if the control discriminates and it is grounded.
  (7) GRAPH-NATIVE audit: the accept/reject is the `self_verify_gate` Rule's
      `verdict` attr, written by tick() in Rust; cross-checked against a direct
      native evaluate() of the identical verdict term, and a source audit that
      the module holds no Python conjunction deciding acceptance.

A bare `substrate_rs.Substrate()` duck-types as a valid `agent` (same as
tests/test_grounding_reach.py) — no seed boot needed.
"""
from __future__ import annotations

import substrate_rs as srs

from domains import self_verification as sv
from domains.self_verification import Claim, verify_claim


# ---------------------------------------------------------------------------
# The concrete mechanisms. A classifier "high iff value >= 10". The REAL fix
# uses the true threshold; the FAKE is TUNED to a small fit set (>=3) — overfit,
# it fails a held-out item. This is the game_theory-anchored control's shape:
# a real fix keeps the held-out item correctly placed; a tuned threshold moves
# it across.
# ---------------------------------------------------------------------------
def real_mech(case):
    val, label = case
    return (val >= 10) == (label == "high")


def fake_tuned(case):
    val, label = case
    return (val >= 3) == (label == "high")


# Held-out control: a low item at value 5 (real: >=10 -> low OK; fake: >=3 ->
# high, WRONG) and a clear high item. The fake fails the value-5 case.
HELD = [(5, "low"), (12, "high")]
PRIOR = [(20, "high"), (1, "low")]


def _ground_sensor(sub):
    """Support chained to a real SENSOR reading (Agent -perceives-> percept):
    ensure_grounding_edges wires percept -grounded_in-> SensorAnchor."""
    ag = sub.add_node("Agent", {})
    perc = sub.add_node("VisionPercept", {})
    sub.add_edge_unchecked(ag, "perceives", perc)
    node = sub.add_node("Collapse", {"label": "support"})
    sub.add_edge_unchecked(node, "grounded_in", perc)
    return node


def _ground_loop(sub):
    """A self-referential support loop — confident but reaches no anchor."""
    a = sub.add_node("Collapse", {"label": "a"})
    b = sub.add_node("Collapse", {"label": "b"})
    sub.add_edge_unchecked(a, "grounded_in", b)
    sub.add_edge_unchecked(b, "grounded_in", a)
    return a


# ===========================================================================
# (1) CATCHES A FAKE — the headline. A tuned-to-pass claim is rejected.
# ===========================================================================
def test_catches_a_fake_tuned_claim():
    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "this threshold-tune generalizes",
        mechanism=fake_tuned,          # the SUBMITTED mechanism is the fake
        control_cases=HELD,
        fake_twin=fake_tuned,
        prior_cases=PRIOR,
        ground_support=_ground_sensor,
    ))
    assert r["accepted"] is False
    assert r["discriminates"] is False
    assert r["real_pass"] is False      # the fake fails the held-out control
    assert "does NOT survive" in r["reason"]


# ===========================================================================
# (2) ACCEPTS A REAL — same faculty, opposite verdict. The contrast is pinned:
# only whether the control actually discriminates flips the outcome.
# ===========================================================================
def test_accepts_a_real_grounded_claim():
    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "degree-normalization keeps game_theory anchored",
        mechanism=real_mech,
        control_cases=HELD,
        fake_twin=fake_tuned,           # a known-fake that FAILS the control
        prior_cases=PRIOR,
        ground_support=_ground_sensor,
    ))
    assert r["accepted"] is True
    assert r["discriminates"] is True
    assert r["real_pass"] is True and r["twin_pass"] is False
    assert r["no_regression"] is True
    assert r["grounded"] is True and r["anchors"] == ["SensorAnchor"]


def test_real_and_fake_are_the_same_faculty_opposite_verdict():
    """The load-bearing contrast: identical control + grounding + prior, the
    ONLY difference is whether the submitted mechanism is the real one or the
    tuned fake — and the verdict flips. Same code path, no branch on which."""
    s = srs.Substrate()
    real = verify_claim(s, Claim("real", real_mech, HELD, fake_tuned, PRIOR, _ground_sensor))
    fake = verify_claim(s, Claim("fake", fake_tuned, HELD, fake_tuned, PRIOR, _ground_sensor))
    assert real["accepted"] is True
    assert fake["accepted"] is False


# ===========================================================================
# (3) GROUNDING-REACH GATE — discriminates + no regression, but ungrounded.
# ===========================================================================
def test_grounding_reach_gate_rejects_confident_ungrounded():
    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "looks right, but reaches no anchor",
        mechanism=real_mech,            # genuinely discriminates
        control_cases=HELD,
        fake_twin=fake_tuned,
        prior_cases=PRIOR,
        ground_support=_ground_loop,    # self-loop: no anchor
    ))
    assert r["accepted"] is False
    assert r["discriminates"] is True   # the control DID discriminate
    assert r["no_regression"] is True
    assert r["grounded"] is False
    assert r["anchors"] == []
    assert "UNGROUNDED" in r["reason"]


def test_grounding_gate_is_discriminative_not_confidence():
    """Same discriminating control + no-regression; ONLY grounding differs.
    Grounded -> accept; self-loop -> reject. Grounding, not confidence, saves
    it (mirrors test_grounding_reach scenario d)."""
    s = srs.Substrate()
    grounded = verify_claim(s, Claim("g", real_mech, HELD, fake_tuned, PRIOR, _ground_sensor))
    ungrounded = verify_claim(s, Claim("u", real_mech, HELD, fake_tuned, PRIOR, _ground_loop))
    assert grounded["accepted"] is True
    assert ungrounded["accepted"] is False


# ===========================================================================
# (4) THIS-SESSION GUARD MIRROR — the token-inflated-microtheory shape. A pass
# achieved by INFLATION, not real structure: the control is "does it still hold
# on a held-out topic without the padding". The inflated mechanism fails it.
# ===========================================================================
def test_token_inflation_style_claim_rejected():
    # A microtheory "covers" a topic iff it has >= 3 genuinely-relevant tokens.
    # The INFLATED mechanism pads token count to fake coverage but the padded
    # tokens are irrelevant, so on a held-out topic the padding does not cover.
    def genuine_cover(topic):
        # topic = (relevant_tokens, padded_tokens); real coverage needs relevance
        relevant, _padded = topic
        return relevant >= 3

    def inflated_cover(topic):
        # counts padding toward "coverage" — passes the fit topic, fails held-out
        relevant, padded = topic
        return (relevant + padded) >= 3

    # held-out topic: only 1 relevant token, 5 padded. genuine: NOT covered;
    # inflated: "covered" (WRONG — it's just padding).
    held_topic = [((1, 5), None)]  # control case; mechanism reads case[0]

    def cover_case_mech(case):
        topic, _ = case
        return inflated_cover(topic) == genuine_cover(topic)

    def cover_case_twin(case):
        # the known-fake: always claims coverage (no teeth check reference)
        topic, _ = case
        return True == genuine_cover(topic)

    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "microtheory now covers the topic (via more tokens)",
        mechanism=cover_case_mech,
        control_cases=held_topic,
        fake_twin=cover_case_twin,
        prior_cases=(),
        ground_support=_ground_sensor,
    ))
    assert r["accepted"] is False
    assert r["real_pass"] is False
    assert "does NOT survive" in r["reason"]


# ===========================================================================
# (5) NO-TEETH CONTROL — a control the known-fake twin also passes cannot
# discriminate, so it is rejected even though the mechanism passes it.
# ===========================================================================
def test_toothless_control_rejected():
    # A control everything passes (both real and fake return True on it).
    trivial = [(999, "high")]  # value>=10 -> high, both mechanisms agree
    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "passes a control with no teeth",
        mechanism=real_mech,
        control_cases=trivial,
        fake_twin=real_mech,        # twin passes the same trivial control
        prior_cases=PRIOR,
        ground_support=_ground_sensor,
    ))
    assert r["accepted"] is False
    assert r["discriminates"] is False
    assert r["twin_pass"] is True
    assert "NO teeth" in r["reason"]


def test_vacuous_control_rejected():
    """A claim with NO control cases cannot discriminate -> rejected."""
    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "no control at all", real_mech, [], fake_tuned, PRIOR, _ground_sensor))
    assert r["accepted"] is False
    assert r["discriminates"] is False
    assert "VACUOUS" in r["reason"]


# ===========================================================================
# (6) REGRESSION — a change that breaks a previously-holding case is rejected.
# ===========================================================================
def test_regression_rejected():
    # mechanism discriminates on the held-out control, but a prior case it used
    # to satisfy now fails.
    def breaks_prior(case):
        val, label = case
        # correct on the held-out control values (5,12) but wrong on prior (20)
        if val == 20:
            return False
        return (val >= 10) == (label == "high")

    s = srs.Substrate()
    r = verify_claim(s, Claim(
        "fix that regresses an old case",
        mechanism=breaks_prior,
        control_cases=HELD,
        fake_twin=fake_tuned,
        prior_cases=PRIOR,          # includes (20,'high') which now fails
        ground_support=_ground_sensor,
    ))
    assert r["accepted"] is False
    assert r["no_regression"] is False
    assert "REGRESSION" in r["reason"]


# ===========================================================================
# (7) GRAPH-NATIVE audit.
# ===========================================================================
def test_verdict_written_by_graph_rule_in_rust():
    """The accept/reject is the self_verify_gate Rule's `verdict` attr, written
    by tick(). The Rule node exists, and the Claim carries the Rust-computed
    verdict + gate attrs."""
    s = srs.Substrate()
    r = verify_claim(s, Claim("g", real_mech, HELD, fake_tuned, PRIOR, _ground_sensor))
    rule_ids = {s.node(n)["attrs"].get("id") for n in s.nodes("Rule")}
    assert sv._GATE_RULE_ID in rule_ids
    at = s.node(r["claim_node"])["attrs"]
    assert "verdict" in at and "g_discriminates" in at
    assert float(at["verdict"]) == 1.0


def test_gate_rule_is_installed_once():
    """The gate Rule is idempotent — repeated verifications reuse one Rule."""
    s = srs.Substrate()
    for _ in range(3):
        verify_claim(s, Claim("g", real_mech, HELD, fake_tuned, PRIOR, _ground_sensor))
    gate_rules = [n for n in s.nodes("Rule")
                  if s.node(n)["attrs"].get("id") == sv._GATE_RULE_ID]
    assert len(gate_rules) == 1


def test_verdict_matches_direct_native_term_eval():
    """The verdict must be the native term-tree's value, not a Python re-decide:
    cross-check the Claim's Rust-written verdict against a direct evaluate() of
    the identical verdict condition over the same nodes."""
    s = srs.Substrate()
    r = verify_claim(s, Claim("g", real_mech, HELD, fake_tuned, PRIOR, _ground_sensor))
    claim_node, probe = r["claim_node"], r["probe_node"]
    from substrate_rs import And, Not, Gt, Attr, Var, Lit, Plus, IfThenElse

    def _b(node, key):
        return Gt(Plus([Attr(Var(node), key), Lit(0)]), Lit(0.5))
    disc = And([_b("probe", "real_pass"), Not(_b("probe", "twin_pass"))])
    cond = And([disc, _b("claim", "no_regression"), _b("claim", "grounded")])
    term = IfThenElse(cond, Lit(1.0), Lit(0.0))
    direct = float(s.evaluate(term, {"claim": claim_node, "probe": probe}))
    assert direct == r["verdict"]


def test_source_holds_no_python_acceptance_decision():
    """Source audit: the accept/reject conjunction lives in the graph term-tree
    (the Rule's `where`/effect), NOT as a Python `and` over the three gates. The
    module must not contain a line that conjuncts discriminates/no_regression/
    grounded to decide acceptance in Python."""
    import inspect
    src = inspect.getsource(sv)
    # `accepted` must be a readback of the Rust `verdict` scalar (a threshold on
    # the graph-written attr), never a Python conjunction of the three gates.
    assert "accepted = verdict >= 0.5" in src
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):        # ignore prose in comments
            continue
        if "accepted" in stripped and " and " in stripped and "=" in stripped:
            raise AssertionError(
                "acceptance appears to be decided by a Python conjunction: " + stripped)
    # the gate conjunction lives in the graph term-tree (an "And" term dict).
    assert sv._VERDICT_COND["type"] == "And"
    assert len(sv._VERDICT_COND["items"]) == 3
