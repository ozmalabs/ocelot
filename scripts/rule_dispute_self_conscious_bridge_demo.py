"""Live demonstration harness for seeds/rule_dispute_self_conscious_bridge.json.

Per docs/research/psychology_affect/
RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md Sec2 and
ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md Sec3. Pure world-adapter/harness
code (CLAUDE.md's architecture rule): this script MECHANICALLY builds a
DisputeContext (optionally with a held SelfPattern) exactly as
rule_dispute_escalation_demo.py does, calls `run_rules()` ONCE, and reads
back the dispute outcome, the residual-derived attribution_locus, and the
bridged self-conscious emotion the engine's own rules already decided. It
makes no bridging decision itself.

Run: python3 scripts/rule_dispute_self_conscious_bridge_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402

SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def dispute_then_appraise(inner, *, issue_severity, band_code, witnesses,
                          held_self_worth=None, audience_gain=0.15, label=""):
    """witnesses: list of per-witness closeness values. held_self_worth:
    None (no track record) or a scalar in [-1,1]."""
    ctx = inner.add_node("DisputeContext", {
        "label": label, "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
    if held_self_worth is not None:
        pattern = inner.add_node("SelfPattern", {"held_self_worth": held_self_worth})
        inner.add_edge(ctx, "has_self_pattern", pattern, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    dispute_attrs = inner.node(sig)["attrs"]
    sc_ctx = inner.neighbours(ctx, "bridged_to")[0]
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    emotion_attrs = inner.node(sc_sig)["attrs"]
    return {
        "label": label, "dispute_outcome": dispute_attrs["outcome"],
        "attribution_locus": inner.node(sc_ctx)["attrs"]["attribution_locus"],
        "witness_judgment": inner.node(sc_ctx)["attrs"]["witness_judgment"],
        "emotion": emotion_attrs["emotion"],
    }


def main():
    s = _loaded_substrate()
    inner = s._inner

    print("=" * 78)
    print("ATTRIBUTION AS A RESIDUAL (ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md")
    print("predictions 1-2): the SAME failure, opposite held self-pattern")
    print("=" * 78)
    negative_pattern = dispute_then_appraise(
        inner, label="failure confirms an already-negative self-pattern",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=-0.6)
    positive_pattern = dispute_then_appraise(
        inner, label="SAME failure, but a positive self-pattern (contradicts it)",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=0.6)
    for r in (negative_pattern, positive_pattern):
        print("%-55s locus=%-13s -> %s" % (r["label"], r["attribution_locus"], r["emotion"]))

    print()
    print("=" * 78)
    print("NO TRACK RECORD -> CIRCUMSTANCE, EMBARRASSMENT RECOVERED")
    print("(prediction 3 -- retracts the prior 'never embarrassment' finding)")
    print("=" * 78)
    first_time_private = dispute_then_appraise(
        inner, label="first-time incident, no track record, private",
        issue_severity=0.9, band_code=0, witnesses=[])
    first_time_public = dispute_then_appraise(
        inner, label="SAME first-time incident, witnessed",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0])
    for r in (first_time_private, first_time_public):
        print("%-55s locus=%-13s -> %s" % (r["label"], r["attribution_locus"], r["emotion"]))

    print()
    print("=" * 78)
    print("witness_judgment (audience perception) is UNCHANGED -- still keyed")
    print("to the dispute's own escalate/defuse outcome, not the residual")
    print("=" * 78)
    escalated = dispute_then_appraise(
        inner, label="near-strangers, confident contradiction, witnessed",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=-0.6)
    defused = dispute_then_appraise(
        inner, label="close friends, ambiguous issue, private",
        issue_severity=0.2, band_code=4, witnesses=[],
        held_self_worth=-0.6)
    for r in (escalated, defused):
        print("%-55s dispute=%-9s witness_judgment=%-9s emotion=%s" % (
            r["label"], r["dispute_outcome"], r["witness_judgment"], r["emotion"]))
    print("(witness_judgment differs -- 'violated' vs 'met' -- but the emotion")
    print(" is the SAME 'shame' in both, since attribution_locus=global_self")
    print(" for both (identical held_self_worth) and only the circumstance")
    print(" cell reads witness_judgment at all)")

    return {"negative_pattern": negative_pattern, "positive_pattern": positive_pattern,
            "first_time_private": first_time_private, "first_time_public": first_time_public}


if __name__ == "__main__":
    main()
