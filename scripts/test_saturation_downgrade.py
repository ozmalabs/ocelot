"""Verify the saturation fix: the gap selector now downgrades a capability the agent
believes is SATURATED (its own measured yardstick met its target), so the next genuine
frontier surfaces. Builds the agent's axes, ranks (cross-speaker clustering #1), then
records the agent's clustering measurement (0.69 >= its 0.65 target = saturated) and
re-ranks. NO Python decision — saturation is read off the agent's MeasuredCapability and
the score Term does the downgrade.

Run: python -m scripts.test_saturation_downgrade
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_decides_speech import _build_mind
from domains.relational_invariance_findings import install_relational_invariance_findings
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp

CLUSTER_KEYS = ["unsupervised-clustering", "cross-speaker-clustering", "cross-speaker"]


def top(rows, n=4):
    for r in rows[:n]:
        print(f"    payoff={r['payoff']:3d} score={r['score']:8d} "
              f"sat={r.get('saturation', 0):.2f}  {r['capability_keys'][:3]}")


def main():
    sub = _build_mind()
    install_relational_invariance_findings(sub)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    print("=" * 78)
    print("BEFORE — the agent's ranking (no saturation belief recorded):")
    print("=" * 78)
    rows0 = gp.rank_gaps(sub)
    top(rows0)
    print(f"\n  #1 = {rows0[0]['capability_keys'][:3]}  (payoff {rows0[0]['payoff']})")

    # The agent records its OWN measurement of the now-built capability: cross-speaker
    # clustering reached 0.69 purity, above its 0.65 target -> it believes it SATURATED.
    gp.record_measured_capability(
        sub, CLUSTER_KEYS, measured=0.69, target=0.65,
        metric="cluster_purity", note="spectral-shape front-end + nuisance-conditioning")

    print("\n" + "=" * 78)
    print("AFTER — agent recorded clustering measured 0.69 >= target 0.65 (SATURATED):")
    print("=" * 78)
    rows1 = gp.rank_gaps(sub)
    # annotate saturation for display
    for r in rows1:
        ax = r["axis_id"]
        r["saturation"] = float(sub.node(ax)["attrs"].get("saturation", 0.0))
    top(rows1)
    cl = next((r for r in rows1 if "cross-speaker-clustering" in r["capability_keys"]), None)
    print(f"\n  clustering now: payoff {cl['payoff']} sat {cl['saturation']:.2f} "
          f"score {cl['score']}  (was #1)")
    print(f"  NEW #1 = {rows1[0]['capability_keys'][:3]}  (payoff {rows1[0]['payoff']})")
    print("=" * 78)
    moved = rows0[0]["capability_keys"][:1] != rows1[0]["capability_keys"][:1]
    print("  saturation downgrade " + ("WORKS — the next frontier surfaced."
                                       if moved else "did NOT change the pick."))


if __name__ == "__main__":
    main()
