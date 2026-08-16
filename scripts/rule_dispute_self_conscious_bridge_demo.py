"""Live demonstration harness for seeds/rule_dispute_self_conscious_bridge.json.

Per docs/research/psychology_affect/
RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md Sec2. Pure world-adapter/
harness code (CLAUDE.md's architecture rule): this script MECHANICALLY
builds a DisputeContext exactly as rule_dispute_escalation_demo.py does,
calls `run_rules()` ONCE, and reads back BOTH the dispute outcome and the
bridged self-conscious emotion the engine's own rules already decided. It
makes no bridging decision itself -- the outcome->attribution_locus mapping
is entirely bridge_dispute_to_self_conscious_context's own effect.

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


def dispute_then_appraise(inner, *, issue_severity, band_code, witnesses, audience_gain=0.15, label=""):
    """witnesses: list of per-witness closeness values, mirroring
    rule_dispute_escalation_demo.py::decide exactly."""
    ctx = inner.add_node("DisputeContext", {
        "label": label, "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    dispute_attrs = inner.node(sig)["attrs"]
    sc_ctx = inner.neighbours(ctx, "bridged_to")[0]
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    emotion_attrs = inner.node(sc_sig)["attrs"]
    witness_belief_count = len(inner.neighbours(sc_ctx, "has_witness_belief"))
    return {
        "label": label, "dispute_outcome": dispute_attrs["outcome"],
        "attribution_locus": inner.node(sc_ctx)["attrs"]["attribution_locus"],
        "emotion": emotion_attrs["emotion"],
        "witness_belief_count": witness_belief_count,
    }


def main():
    s = _loaded_substrate()
    inner = s._inner

    print("=" * 78)
    print("END-TO-END: the SAME two scenarios rule_dispute_escalation_demo.py")
    print("used, now bridged through to a self-conscious emotion")
    print("=" * 78)
    escalated = dispute_then_appraise(
        inner, label="near-strangers, confident contradiction, whole table watching",
        issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0])
    defused = dispute_then_appraise(
        inner, label="close friends, ambiguous issue, private aside",
        issue_severity=0.2, band_code=4, witnesses=[])
    for r in (escalated, defused):
        print("%-55s dispute=%-9s locus=%-13s witnesses=%d -> %s" % (
            r["label"], r["dispute_outcome"], r["attribution_locus"],
            r["witness_belief_count"], r["emotion"]))

    print()
    print("=" * 78)
    print("NEVER EMBARRASSMENT (PREREG Sec2 prediction 3) -- a small sweep")
    print("=" * 78)
    emotions_seen = set()
    for band in (0, 2, 4, 5):
        for severity10 in (2, 5, 8):
            r = dispute_then_appraise(
                inner, issue_severity=severity10 / 10.0, band_code=band,
                witnesses=[0.0, 0.5])
            emotions_seen.add(r["emotion"])
    print("emotions produced across the sweep:", sorted(emotions_seen))
    print("embarrassment ever produced:", "embarrassment" in emotions_seen)

    return {"escalated": escalated, "defused": defused, "emotions_seen": sorted(emotions_seen)}


if __name__ == "__main__":
    main()
