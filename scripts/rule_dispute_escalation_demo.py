"""Live demonstration harness for seeds/rule_dispute_escalation.json.

Per docs/research/engine_substrate/RULE_DISPUTE_ESCALATION_PREREG.md Sec3.
Pure world-adapter/harness code (CLAUDE.md's architecture rule): this script
MECHANICALLY builds a DisputeContext/RuleDisputeSignal pair per scenario,
calls `run_rules()`, and reads back the outcome the engine's own
`rd_decide_outcome` rule already decided. It contains no escalate/defuse
decision -- the label choice is entirely the engine's Argmin call.

Run: python3 scripts/rule_dispute_escalation_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402

SEED_PATH = "seeds/rule_dispute_escalation.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    inner.load_seed_manifest(engine_rules_only(d))
    return s


def decide(inner, *, issue_severity, band_code, witnesses, audience_gain=0.15, label=""):
    """`witnesses` is a list of per-witness closeness values (0.0 for an
    anonymous bystander, higher for someone who'd regulate a disputant --
    PREREG Sec3b, Rung 2). Pass an int for backward-compatible all-anonymous
    witness counts."""
    if isinstance(witnesses, int):
        witnesses = [0.0] * witnesses
    ctx = inner.add_node("DisputeContext", {
        "label": label, "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        witness = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", witness, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    attrs = inner.node(sig)["attrs"]
    return {
        "label": label, "closeness": attrs["closeness"],
        "pressure": attrs["pressure"], "outcome": attrs["outcome"],
    }


def main():
    s = _loaded_substrate()
    inner = s._inner

    print("=" * 78)
    print("PRIMARY SCENARIOS (PREREG Sec3, predictions 2-3)")
    print("=" * 78)

    # The Free Parking myth: Bob claims the pot pays out; the rulebook
    # (scenarios/monopoly_rulebook.txt:151) flatly says it does not.
    close_private = decide(
        inner, label="close friends, ambiguous issue, private aside",
        issue_severity=0.2, band_code=4, witnesses=0)
    rival_public = decide(
        inner, label="near-strangers, confident contradiction, whole table watching",
        issue_severity=0.9, band_code=0, witnesses=3)

    for r in (close_private, rival_public):
        print("%-55s closeness=%.2f pressure=%+.3f -> %s" % (
            r["label"], r["closeness"], r["pressure"], r["outcome"]))

    print()
    print("=" * 78)
    print("INTERACTION SWEEP (PREREG Sec3, prediction 4) -- same public dispute,")
    print("varying only closeness")
    print("=" * 78)
    for band in range(6):
        r = decide(inner, label="band=%d" % band, issue_severity=0.8,
                   band_code=band, witnesses=3)
        print("band_code=%d  closeness=%+.2f  pressure=%+.3f  -> %s" % (
            band, r["closeness"], r["pressure"], r["outcome"]))

    print()
    print("=" * 78)
    print("RIVAL FLOOR CHECK (PREREG Sec3, prediction 5)")
    print("=" * 78)
    stranger = decide(inner, label="stranger", issue_severity=0.8, band_code=0, witnesses=3)
    rival = decide(inner, label="rival", issue_severity=0.8, band_code=-1, witnesses=3)
    print("stranger (band=0): pressure=%+.3f" % stranger["pressure"])
    print("rival    (band=-1): pressure=%+.3f" % rival["pressure"])
    print("rival pressure >= stranger pressure:", rival["pressure"] >= stranger["pressure"])

    print()
    print("=" * 78)
    print("REGULATING WITNESS (PREREG Sec3b, prediction 6) -- near-strangers,")
    print("high severity, 3 witnesses -- one is a disputant's partner")
    print("=" * 78)
    all_anonymous = decide(
        inner, label="3 anonymous witnesses",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0])
    with_partner = decide(
        inner, label="2 anonymous + 1 regulating partner (closeness=0.9)",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.9])
    for r in (all_anonymous, with_partner):
        print("%-55s pressure=%+.3f -> %s" % (r["label"], r["pressure"], r["outcome"]))
    print("partner lowers pressure:", with_partner["pressure"] < all_anonymous["pressure"])
    print("outcome flips escalate -> defuse:",
          all_anonymous["outcome"] == "escalate" and with_partner["outcome"] == "defuse")
    print("(honest null on the flip at THIS severity -- RESULTS.md Sec3b: one")
    print(" witness's bounded regulation (max swing = audience_gain per witness)")
    print(" lowers pressure but cannot overcome a genuinely severe dispute alone)")

    print()
    print("=" * 78)
    print("REGULATING WITNESS -- a BORDERLINE dispute, where the same mechanism")
    print("DOES flip the outcome (RESULTS.md Sec3b's honest range-finding)")
    print("=" * 78)
    borderline_anon = decide(
        inner, label="near-stranger, mild issue, 1 anonymous witness",
        issue_severity=0.1, band_code=1, witnesses=[0.0])
    borderline_partner = decide(
        inner, label="near-stranger, mild issue, 1 regulating partner",
        issue_severity=0.1, band_code=1, witnesses=[0.9])
    for r in (borderline_anon, borderline_partner):
        print("%-55s pressure=%+.3f -> %s" % (r["label"], r["pressure"], r["outcome"]))
    print("outcome flips escalate -> defuse:",
          borderline_anon["outcome"] == "escalate" and borderline_partner["outcome"] == "defuse")

    return {
        "close_private": close_private, "rival_public": rival_public,
        "stranger": stranger, "rival": rival,
        "all_anonymous": all_anonymous, "with_partner": with_partner,
        "borderline_anon": borderline_anon, "borderline_partner": borderline_partner,
    }


if __name__ == "__main__":
    main()
