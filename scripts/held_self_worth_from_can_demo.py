"""Live demonstration harness for domains/can_self_worth_bridge.py.

Per docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_PREREG.md
Sec3. Builds two residents' REAL CAN self_worth belief networks, relaxes
each via the engine's own discrete-asynchronous update rule, and feeds
each resident's CONVERGED state through the unchanged rule_dispute_
escalation -> self_conscious_emotions -> rule_dispute_self_conscious_
bridge chain for the IDENTICAL dispute. No held_self_worth value is
chosen by this script -- the CAN network's own relaxation computes it.

Run: python3 scripts/held_self_worth_from_can_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402
from domains.can_self_worth_bridge import ensure_can_seed, relax_resident_self_worth  # noqa: E402

SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]

RESIDENTS = {
    "Confident": {"name": "Confident", "index": 0, "params": {
        "resolution_bins": 8, "arousal": 0.2,
        "prior_world_safe": 0.6, "prior_self_worth": 0.9,
        "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
        "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
        "mood_bias": 0.3,
    }},
    "Insecure": {"name": "Insecure", "index": 1, "params": {
        "resolution_bins": 8, "arousal": 0.2,
        "prior_world_safe": 0.6, "prior_self_worth": 0.1,
        "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
        "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
        "mood_bias": 0.3,
    }},
}


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def dispute_then_appraise(inner, *, issue_severity, band_code, witnesses,
                          held_self_worth, audience_gain=0.15, label=""):
    ctx = inner.add_node("DisputeContext", {
        "label": label, "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
    pattern = inner.add_node("SelfPattern", {"held_self_worth": float(held_self_worth)})
    inner.add_edge(ctx, "has_self_pattern", pattern, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    sc_ctx = inner.neighbours(ctx, "bridged_to")[0]
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    return {
        "label": label, "attribution_locus": inner.node(sc_ctx)["attrs"]["attribution_locus"],
        "emotion": inner.node(sc_sig)["attrs"]["emotion"],
    }


def main():
    s = _loaded_substrate()
    inner = s._inner

    print("=" * 78)
    print("REAL CAN self_worth, two residents, the SAME dispute")
    print("=" * 78)
    can_results = {}
    for name, resident in RESIDENTS.items():
        out = relax_resident_self_worth(inner, resident)
        can_results[name] = out["self_worth"]
        print("%-10s prior_self_worth=%.2f -> real CAN self_worth=%s (%d relaxation steps)" % (
            name, resident["params"]["prior_self_worth"], out["self_worth"], out["steps"]))

    print()
    print("=" * 78)
    print("THE SAME rule dispute, appraised through each resident's REAL,")
    print("independently-relaxed CAN self_worth belief")
    print("=" * 78)
    for name in RESIDENTS:
        r = dispute_then_appraise(
            inner, label="%s: near-strangers, confident contradiction, witnessed" % name,
            issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
            held_self_worth=can_results[name])
        print("%-55s locus=%-13s -> %s" % (r["label"], r["attribution_locus"], r["emotion"]))

    return can_results


if __name__ == "__main__":
    main()
