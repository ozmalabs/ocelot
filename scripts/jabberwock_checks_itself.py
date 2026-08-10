"""jabberwock_checks_itself — the agent runs the NOT-FOOLING-ITSELF faculty on
proposed self-improvements, live. donkey=0 (no LM, no fit; every verdict is the
Rust term-tree over measured graph attrs).

This is the discipline the developer enforced BY HAND this session, made the
agent's own reflex: for each proposed fix, mint a discriminative ControlProbe
(a case that fails if the fix is fake/overfit), check no-regression, gate on
grounding-reachability — and ACCEPT only if the control discriminates AND no
regression AND grounded. The decision is a graph-resident Rule fired by tick();
the host only mints the claim and RUNS the probe (the measurement instrument).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_checks_itself.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substrate_rs as srs
from domains.self_verification import Claim, verify_claim


# --- the classifier under fix: "high iff value >= 10". The REAL fix uses the
#     true threshold; a FAKE is tuned to a tiny fit set (>=3) and fails a
#     held-out item (the game_theory-stays-anchored control's shape). ---
def real_mech(case):
    val, label = case
    return (val >= 10) == (label == "high")


def fake_tuned(case):
    val, label = case
    return (val >= 3) == (label == "high")


HELD = [(5, "low"), (12, "high")]      # held-out control: fake mis-places (5,'low')
PRIOR = [(20, "high"), (1, "low")]     # previously-holding (no-regression)


def ground_sensor(sub):
    """Support chained to a real sensor reading -> SensorAnchor."""
    ag = sub.add_node("Agent", {})
    perc = sub.add_node("VisionPercept", {})
    sub.add_edge_unchecked(ag, "perceives", perc)
    node = sub.add_node("Collapse", {"label": "support"})
    sub.add_edge_unchecked(node, "grounded_in", perc)
    return node


def ground_loop(sub):
    """A self-referential support loop — confident but reaches no anchor."""
    a = sub.add_node("Collapse", {"label": "a"})
    b = sub.add_node("Collapse", {"label": "b"})
    sub.add_edge_unchecked(a, "grounded_in", b)
    sub.add_edge_unchecked(b, "grounded_in", a)
    return a


def _show(title, r):
    mark = "ACCEPT" if r["accepted"] else "REJECT"
    print(f"  [{mark}] {title}")
    print(f"          discriminates={r['discriminates']} no_regression={r['no_regression']} "
          f"grounded={r['grounded']} anchors={r['anchors']}")
    print(f"          {r['reason']}")
    print()


def main():
    s = srs.Substrate()
    print("=" * 74)
    print("THE JABBERWOCK CHECKS ITSELF — would it have caught me fooling myself?")
    print("=" * 74)
    print()

    # 1. CATCHES A FAKE — a tuned-to-pass claim (this is the 'fooling myself' case).
    fake = verify_claim(s, Claim(
        "this threshold-tune generalizes",
        mechanism=fake_tuned, control_cases=HELD, fake_twin=fake_tuned,
        prior_cases=PRIOR, ground_support=ground_sensor))
    _show("CLAIM: a tuned threshold generalizes (FAKE)", fake)

    # 2. ACCEPTS A REAL — same faculty, opposite verdict.
    real = verify_claim(s, Claim(
        "degree-normalization keeps game_theory anchored",
        mechanism=real_mech, control_cases=HELD, fake_twin=fake_tuned,
        prior_cases=PRIOR, ground_support=ground_sensor))
    _show("CLAIM: degree-norm keeps game_theory anchored (REAL)", real)

    # 3. GROUNDING-REACH GATE — discriminates + no regression, but ungrounded.
    ungrounded = verify_claim(s, Claim(
        "looks right, but reaches no anchor",
        mechanism=real_mech, control_cases=HELD, fake_twin=fake_tuned,
        prior_cases=PRIOR, ground_support=ground_loop))
    _show("CLAIM: a confident but ungrounded basin", ungrounded)

    # 4. THIS-SESSION GUARD MIRROR — token-inflated coverage.
    def genuine(topic):
        rel, _pad = topic
        return rel >= 3

    def inflated_case(case):
        topic, _ = case
        rel, pad = topic
        return ((rel + pad) >= 3) == genuine(topic)   # padding fakes coverage

    infl = verify_claim(s, Claim(
        "microtheory now covers the topic (via more tokens)",
        mechanism=inflated_case, control_cases=[((1, 5), None)],
        fake_twin=lambda c: True == genuine(c[0]),
        prior_cases=(), ground_support=ground_sensor))
    _show("CLAIM: microtheory covers topic (TOKEN-INFLATED)", infl)

    ok = (not fake["accepted"] and real["accepted"]
          and not ungrounded["accepted"] and not infl["accepted"])
    print("-" * 74)
    print(f"GATE: fake REJECTED, real ACCEPTED, ungrounded REJECTED, inflated REJECTED "
          f"-> {'PASS' if ok else 'FAIL'}")
    print("The control decided each verdict in Rust (self_verify_gate rule, tick).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
