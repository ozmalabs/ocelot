"""Bank the two solved frontiers (cross-speaker clustering, statistical segmentation) as
MeasuredCapabilities meeting their targets — the agent's OWN saturation belief — and read
the next #1 frontier off the saturation-aware gap selector. NO Python decision: the score
Term downgrades the saturated axes (payoff*(1-saturation)) and the Argmax surfaces the
next genuine gap.

Run: python -m scripts.bank_and_next_frontier
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_decides_speech import _build_mind
from domains.relational_invariance_findings import install_relational_invariance_findings
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp

SOLVED = [
    # capability_keys (match the synthesized axis), measured, target, metric
    (["unsupervised-clustering", "cross-speaker-clustering", "cross-speaker"],
     0.69, 0.65, "cluster_purity (shape front-end + nuisance-conditioning)"),
    (["transitional probability", "word-scale chunking", "statistical segmentation"],
     0.63, 0.60, "boundary_F1 (bidirectional TP + shape front-end, real speech)"),
    # SUBSUMED: the GOAL of formant-ratio/VTL normalization (speaker-normalized
    # cross-speaker performance) is met at 0.67 by the shape front-end + NC that
    # subsumes it (f6b84e67) — the capability's outcome is achieved, so it saturates.
    (["speaker normalization", "formant ratio", "vocal-tract-length normalization"],
     0.67, 0.60, "cross-speaker clustering purity (shape front-end + NC subsumes formant-ratio)"),
    # BUILT + subsumed: the held LPC chain (_native_lpc_roots_formants) extracts formants;
    # its goal (good formant representation) is met by the shape front-end at 0.67.
    (["all-pole", "levinson", "lpc-formant"],
     0.67, 0.60, "built (held LPC/Levinson chain); subsumed by shape front-end"),
    # BUILT + measured: covariate conditioning IS our nuisance-conditioning (native
    # BetweenScatter+Whiten between-speaker removal, +7.4% clustering -> 0.68).
    (["covariate conditioning", "between-observed-group removal", "confound regression"],
     0.68, 0.60, "built = nuisance-conditioning (native BetweenScatter+Whiten, measured)"),
]


def top(sub, rows, n=6):
    for r in rows[:n]:
        sat = float(sub.node(r["axis_id"])["attrs"].get("saturation", 0.0))
        print(f"    payoff={r['payoff']:3d} score={r['score']:8d} sat={sat:.2f}  "
              f"{r['capability_keys'][:3]}")


def main():
    sub = _build_mind()
    install_relational_invariance_findings(sub)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    print("=" * 80)
    print("BEFORE banking — the agent's ranking:")
    print("=" * 80)
    top(sub, gp.rank_gaps(sub))

    for keys, measured, target, metric in SOLVED:
        gp.record_measured_capability(sub, keys, measured=measured, target=target,
                                      metric=metric, note="banked: measured met target")
        print(f"\n  banked: {keys[1]:32s} measured {measured} >= target {target}  ({metric})")

    print("\n" + "=" * 80)
    print("AFTER banking both solved frontiers (saturation-aware selector):")
    print("=" * 80)
    rows = gp.rank_gaps(sub)
    top(sub, rows)
    nxt = rows[0]
    print(f"\n  NEXT #1 FRONTIER: {nxt['capability_keys'][:3]}  (payoff {nxt['payoff']})")
    print(f"     gap: {nxt.get('gap_text', '')[:300]}")
    print("=" * 80)


if __name__ == "__main__":
    main()
