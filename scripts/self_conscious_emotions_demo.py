"""Live demonstration harness for seeds/self_conscious_emotions.json.

Per docs/research/psychology_affect/SELF_CONSCIOUS_EMOTIONS_PREREG.md Sec3.
Pure world-adapter/harness code (CLAUDE.md's architecture rule): this script
MECHANICALLY builds a SelfConsciousContext/WitnessBelief graph per scenario,
calls `run_rules()`, and reads back the emotion the engine's own
`sc_decide_emotion` rule already decided. It contains no emotion decision --
the classification is entirely the engine's nested IfThenElse.

Run: python3 scripts/self_conscious_emotions_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402

SEED_PATH = "seeds/self_conscious_emotions.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    inner.load_seed_manifest(engine_rules_only(d))
    return s


def appraise(inner, *, standard_met, attribution_locus, witness_judgments=(), label=""):
    ctx = inner.add_node("SelfConsciousContext", {
        "label": label, "standard_met": 1.0 if standard_met else 0.0,
        "attribution_locus": attribution_locus,
    })
    for judgment in witness_judgments:
        w = inner.add_node("WitnessBelief", {"judgment": judgment})
        inner.add_edge(ctx, "has_witness_belief", w, {})
    sig = inner.add_node("SelfConsciousSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_appraisal", sig, {})
    inner.run_rules(50)
    attrs = inner.node(sig)["attrs"]
    return {"label": label, "perceived_violation": attrs["perceived_violation"],
            "emotion": attrs["emotion"]}


def main():
    s = _loaded_substrate()
    inner = s._inner

    print("=" * 78)
    print("PRIVATE SHAME / GUILT (PREREG Sec3, predictions 1-2)")
    print("=" * 78)
    for r in (
        appraise(inner, label="broke a promise, blames own character, alone",
                 standard_met=False, attribution_locus="global_self"),
        appraise(inner, label="broke a promise, blames the one lapse, alone",
                 standard_met=False, attribution_locus="specific_act"),
    ):
        print("%-55s -> %s" % (r["label"], r["emotion"]))

    print()
    print("=" * 78)
    print("HUBRISTIC VS AUTHENTIC PRIDE (PREREG Sec3, prediction 3)")
    print("=" * 78)
    for r in (
        appraise(inner, label="won the game, 'I am just better than everyone'",
                 standard_met=True, attribution_locus="global_self"),
        appraise(inner, label="won the game, 'I studied the odds hard this time'",
                 standard_met=True, attribution_locus="specific_act"),
    ):
        print("%-55s -> %s" % (r["label"], r["emotion"]))

    print()
    print("=" * 78)
    print("EMBARRASSMENT REQUIRES EXPOSURE (PREREG Sec3, prediction 4)")
    print("=" * 78)
    private_trip = appraise(inner, label="tripped over the rug, nobody around",
                            standard_met=False, attribution_locus="circumstance")
    public_trip = appraise(inner, label="tripped over the rug, one person saw",
                           standard_met=False, attribution_locus="circumstance",
                           witness_judgments=["violated"])
    for r in (private_trip, public_trip):
        print("%-55s -> %s" % (r["label"], r["emotion"]))

    print()
    print("=" * 78)
    print("EMBARRASSMENT FROM A WITNESS'S MISTAKEN BELIEF (PREREG Sec3, prediction 5)")
    print("=" * 78)
    r = appraise(inner, label="actually complied, but a witness THINKS you didn't",
                standard_met=True, attribution_locus="circumstance",
                witness_judgments=["violated"])
    print("%-55s -> %s" % (r["label"], r["emotion"]))
    print("(standard_met=True -- ground truth is fine -- yet the witness's own,")
    print(" mistaken belief is what the appraisal reads, per Sec2's design)")

    print()
    print("=" * 78)
    print("SHAME/GUILT ARE EXPOSURE-INDEPENDENT (PREREG Sec3, prediction 6)")
    print("=" * 78)
    private_shame = appraise(inner, label="private failure, global attribution, alone",
                             standard_met=False, attribution_locus="global_self")
    public_shame = appraise(inner, label="same failure, global attribution, 3 witnesses",
                            standard_met=False, attribution_locus="global_self",
                            witness_judgments=["violated", "violated", "met"])
    for r in (private_shame, public_shame):
        print("%-55s -> %s" % (r["label"], r["emotion"]))
    print("unchanged by exposure:", private_shame["emotion"] == public_shame["emotion"] == "shame")

    return {
        "private_trip": private_trip, "public_trip": public_trip,
        "private_shame": private_shame, "public_shame": public_shame,
    }


if __name__ == "__main__":
    main()
