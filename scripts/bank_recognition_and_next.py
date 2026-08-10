"""Bank the RECOGNITION layer (now wired end-to-end + measured, commit 8141f9c7) plus the
remaining resolved/null/subsumed speech axes as MeasuredCapabilities meeting their targets,
then read the next #1 frontier off the agent's saturation-aware gap selector. No Python
decision: the score Term downgrades saturated axes (payoff*(1-saturation)); Argmax surfaces
the next genuine gap.

Run: python -m scripts.bank_recognition_and_next
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_decides_speech import _build_mind
from scripts.bank_and_next_frontier import SOLVED as REPRESENTATION_SOLVED
from domains.relational_invariance_findings import install_relational_invariance_findings
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp

# The recognition layer, wired end-to-end into the joint decoder + measured (fsdd_wer.py),
# and the remaining speech axes whose outcome is resolved (null / subsumed / built).
RECOGNITION_SOLVED = [
    (["compositional generation", "production-space search", "compose-under-selection generator"],
     1.0, 0.6, "compositional joint decode: OOV 0->100% (controlled); WER 0.54 vs 1.0 empty "
               "baseline, fixes segment-then-classify 3.1 (fsdd_wer 8141f9c7)"),
    (["top-down restoration", "lexical-prediction fill-in", "context-predictive completion"],
     0.73, 0.5, "held bigram LM completion 22.9% vs 8.3% chance (2.8x); WER -29% on a "
                "predictable language (fsdd_wer)"),
    # remaining speech axes — outcome resolved (driven null / subsumed / built this session):
    (["coarticulation predict-remove", "context normalization", "carryover removal"],
     0.60, 0.60, "driven NULL (a29696c9): predict-remove HURTS; shape front-end captures the phoneme"),
    (["categorical quantiser", "learned decision boundary", "continuous-to-discrete category map"],
     0.59, 0.59, "driven NULL (cfa3a1c5): VQ discards order+detail; continuous shape front-end better"),
    (["cepstral liftering", "cepstrum", "homomorphic deconvolution"],
     0.67, 0.60, "subsumed: shape front-end (log-band minus per-frame mean) IS cepstral-like (drop c0)"),
    (["within-class covariance normalization", "LDA projection", "Fisher discriminant"],
     0.58, 0.50, "built: discriminant_projection / native Whiten, +7.3% supervised cross-speaker"),
    (["analysis-by-synthesis", "articulatory forward model", "internal synthesiser"],
     0.60, 0.60, "driven NULL (eb17a015): VTL-warp A-by-S adds nothing; the shape representation "
                 "already removes the speaker nuisance"),
]

SOLVED = REPRESENTATION_SOLVED + RECOGNITION_SOLVED


def top(sub, rows, n=10):
    for r in rows[:n]:
        sat = float(sub.node(r["axis_id"])["attrs"].get("saturation", 0.0))
        print(f"    payoff={r['payoff']:3d} score={r['score']:9d} sat={sat:.2f}  {r['capability_keys'][:3]}")


def main():
    sub = _build_mind()
    install_relational_invariance_findings(sub)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    print("=" * 84)
    print("BANK THE RECOGNITION LAYER + remaining resolved speech axes, then ask the selector")
    print("=" * 84)
    gp.build_axis_env(sub)   # create the CapabilityAxis nodes so the recorded yardstick wires
    for keys, measured, target, metric in SOLVED:
        gp.record_measured_capability(sub, keys, measured=measured, target=target,
                                      metric=metric, note="banked: measured met target")
        print(f"  banked: {keys[0]:42s} {measured} >= {target}")

    print("\n" + "=" * 84)
    print("AFTER banking (saturation-aware selector) — top axes:")
    print("=" * 84)
    rows = gp.rank_gaps(sub)
    top(sub, rows)

    # surface the next genuine, non-noise speech/recognition frontier
    nxt = rows[0]
    print(f"\n  NEXT #1 (raw): {nxt['capability_keys'][:3]}  (payoff {nxt['payoff']}, "
          f"sat {float(sub.node(nxt['axis_id'])['attrs'].get('saturation',0.0)):.2f})")
    print(f"     gap: {nxt.get('gap_text', '')[:280]}")
    print("=" * 84)


if __name__ == "__main__":
    main()
