"""Live demonstration harness for seeds/dispute_severity_from_beliefs.json.

Per docs/research/psychology_affect/DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md
Sec3. Pure world-adapter/harness code: mints a BeliefDisagreement (two
predication triples + social context), calls `run_rules()`, and reads back
the COMPUTED issue_severity and the resulting dispute outcome. No severity
value is chosen by this script -- StructSim computes it.

Run: python3 scripts/dispute_severity_from_beliefs_demo.py
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
    "seeds/dispute_severity_from_beliefs.json",
]


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def dispute_from_beliefs(inner, *, claim_pred, truth_pred, band_code, witnesses,
                         audience_gain=0.15, label=""):
    claims = inner.add_node("HeldBelief", {"pred": list(claim_pred)})
    truth = inner.add_node("HeldBelief", {"pred": list(truth_pred)})
    bd = inner.add_node("BeliefDisagreement", {
        "label": label, "band_code": band_code, "audience_gain": audience_gain})
    inner.add_edge(bd, "claims", claims, {})
    inner.add_edge(bd, "truth", truth, {})
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(bd, "has_witness", w, {})
    inner.run_rules(50)
    bridged = inner.neighbours(bd, "bridged_to")
    if not bridged:
        return {"label": label, "issue_severity": None, "outcome": "no_dispute_minted"}
    ctx = bridged[0]
    sig = inner.neighbours(ctx, "has_signal")[0]
    ctx_attrs = inner.node(ctx)["attrs"]
    sig_attrs = inner.node(sig)["attrs"]
    return {"label": label, "issue_severity": ctx_attrs["issue_severity"],
            "outcome": sig_attrs["outcome"]}


def main():
    s = _loaded_substrate()
    inner = s._inner

    print("=" * 78)
    print("IDENTICAL BELIEFS -> NO DISPUTE MINTED (PREREG Sec3 prediction 1, revised)")
    print("=" * 78)
    r = dispute_from_beliefs(
        inner, label="claim matches the rulebook exactly",
        claim_pred=["pays_pot", "free_parking", False],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    print("%-45s severity=%s -> %s" % (r["label"], r["issue_severity"], r["outcome"]))
    print("(found live: severity=0.0 alone does NOT floor the downstream")
    print(" pressure formula -- 3 strangers' ambient audience pressure alone")
    print(" pushed it to 'escalate' with no real disagreement behind it.")
    print(" Fixed by gating the bridge itself on a genuine residual existing.)")

    print()
    print("=" * 78)
    print("PARTIAL CONTRADICTION (the Free Parking myth) -- PREREG prediction 2")
    print("=" * 78)
    r = dispute_from_beliefs(
        inner, label="one slot flipped (pays_pot: True vs False)",
        claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    print("%-45s severity=%.3f -> %s" % (r["label"], r["issue_severity"], r["outcome"]))
    print("(the OLD hand-picked demo value for this exact scenario was 0.9 --")
    print(" the computed residual is genuinely different, not chosen to match)")

    print()
    print("=" * 78)
    print("TOTAL DISAGREEMENT -> HIGHEST SEVERITY (PREREG prediction 3)")
    print("=" * 78)
    r = dispute_from_beliefs(
        inner, label="shares nothing with the truth",
        claim_pred=["collects_rent", "boardwalk", "double"],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    print("%-45s severity=%.3f -> %s" % (r["label"], r["issue_severity"], r["outcome"]))

    print()
    print("=" * 78)
    print("END TO END: a computed, non-cherry-picked severity still produces")
    print("a sensible, non-degenerate range of outcomes (PREREG prediction 4)")
    print("=" * 78)
    close_friends = dispute_from_beliefs(
        inner, label="close friends, one-slot contradiction, private",
        claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=5, witnesses=[])
    strangers = dispute_from_beliefs(
        inner, label="strangers, total disagreement, witnessed",
        claim_pred=["collects_rent", "boardwalk", "double"],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    for r in (close_friends, strangers):
        print("%-45s severity=%.3f -> %s" % (r["label"], r["issue_severity"], r["outcome"]))


if __name__ == "__main__":
    main()
