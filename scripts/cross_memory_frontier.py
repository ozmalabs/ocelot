"""Cross the frontier: prove the agent's memory_self_management faculty bounds its own
state BY ITS COMPRESSION SELECTOR (not a hand-authored list). Simulate rounds where a
SATURATING type (a recurring store that condenses) and a FIREHOSE type (per-input
scratch) both grow; show the selector keeps the saturating one and forgets the
firehose, node_count stays bounded, and state persists to disk.

The saturating type here is a CUSTOM type ('LearnedX') NOT on any keep-list — so a
PASS proves the SELECTOR (saturation = compression) decided to keep it, not a list.
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs                                    # noqa: E402
from substrate_rs import Production, NodePattern              # noqa: E402
from domains import memory_self_management as msm             # noqa: E402

STATE = "/tmp/jabberwock_state/mem.json"
BUDGET = 3000


def _decl(s, t):
    s.add_production(Production(src=NodePattern(type=t, var="a"), edge_type="self_link",
                               tgt=NodePattern(type=t, var="b"), where=None,
                               weight=None, provenance="memtest").to_dict())


def main():
    s = srs.Substrate()
    _decl(s, "LearnedX")     # a recurring store that CONDENSES (saturates)
    _decl(s, "BulkY")        # the per-input firehose
    fac = msm.MemorySelfManagement(budget_nodes=BUDGET)

    # per-round adds: LearnedX SATURATES (40,8,2,1,1); BulkY is a constant FIREHOSE.
    learned_adds = [40, 8, 2, 1, 1]
    print("=" * 78)
    print("CROSSING THE FRONTIER — the agent bounds its own memory by its selector")
    print(f"  budget = {BUDGET} nodes; LearnedX (saturating, NOT on any keep-list) vs "
          f"BulkY (firehose)")
    print("=" * 78)
    print(f"  {'round':>5} {'+LearnedX':>9} {'+BulkY':>7} {'peak':>7} {'after':>7} "
          f"{'forgot':>22} {'LearnedX kept':>13}")
    for r, la in enumerate(learned_adds, 1):
        for _ in range(la):
            s.add_node("LearnedX", {"r": r})
        for _ in range(5000):
            s.add_node("BulkY", {"r": r})
        peak = s.node_count()
        tr = fac.observe_and_bound(s, persist_path=STATE)
        lx = len(s.nodes("LearnedX"))
        print(f"  {r:>5} {la:>9} {5000:>7} {peak:>7} {tr['total_after']:>7} "
              f"{str(tr['forgot']):>22} {lx:>13}")

    print("\n  VERDICT:")
    final = s.node_count()
    lx = len(s.nodes("LearnedX")); by = len(s.nodes("BulkY"))
    ok_bounded = final < BUDGET + 5000
    ok_kept = lx == sum(learned_adds)            # every saturating instance kept
    ok_forgot = by == 0                          # firehose forgotten
    print(f"    node_count bounded across rounds (< budget+1 firehose): {ok_bounded} "
          f"(final {final})")
    print(f"    saturating LearnedX KEPT by the selector (not a list): {ok_kept} "
          f"({lx}/{sum(learned_adds)})")
    print(f"    firehose BulkY FORGOTTEN: {ok_forgot} ({by} left)")
    print(f"    state persisted to disk: {os.path.exists(STATE)} ({STATE})")
    print(f"    MemorySummary nodes (consolidated learning kept): "
          f"{len(s.nodes('MemorySummary'))}")
    print("=" * 78)
    return 0 if (ok_bounded and ok_kept and ok_forgot) else 1


if __name__ == "__main__":
    raise SystemExit(main())
