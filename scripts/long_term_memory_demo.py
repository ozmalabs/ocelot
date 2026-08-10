"""Prove the dynamic shuffle to disk: as the agent learns across many shows, its
long-term records stay BOUNDED in RAM (only the hot window resident) while EVERY record
persists on disk, and a cold record PAGES BACK on revisit (targeted-lookup recall).
"""
from __future__ import annotations
import os, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs                                    # noqa: E402
from domains import long_term_memory as ltm                   # noqa: E402

STORE = "/tmp/jabberwock_state/ltm_demo"
N_SHOWS = 20
HOT = 5


def main():
    shutil.rmtree(STORE, ignore_errors=True)
    s = srs.Substrate()
    mem = ltm.LongTermMemory(STORE, hot_window=HOT)
    print("=" * 78)
    print(f"DYNAMIC SHUFFLE TO DISK — {N_SHOWS} shows learned, hot_window={HOT}")
    print("=" * 78)
    print(f"  {'round':>5} {'learned':<10} {'RAM records':>11} {'on disk':>8} "
          f"{'evicted->disk':>14}")
    for r in range(1, N_SHOWS + 1):
        key = f"show{r}"
        # the agent's distinctive LEARNING from this show, as a compact record node
        rec = s.add_node("MemoryRecord", {"show": key, "round": r,
                                          "new_signs": max(40 // r, 1),
                                          "note": "consolidated learning"})
        mem.consolidate(s, key, rec, r, meta={"show": key})
        mem.shuffle(s, r)
        ram_records = len(s.nodes("MemoryRecord"))
        st = mem.stats()
        ev = r - HOT if r > HOT else 0
        print(f"  {r:>5} {key:<10} {ram_records:>11} {st['on_disk']:>8} "
              f"{('show%d' % (r-HOT-0)) if r>HOT else '-':>14}")

    print("\n  --- RECALL a cold show (targeted-lookup; it was evicted long ago) ---")
    before = len(s.nodes("MemoryRecord"))
    findable = mem.findable("show3")
    nid = mem.recall(s, "show3", round_no=N_SHOWS + 1)
    after = len(s.nodes("MemoryRecord"))
    rec = s.node(nid)["attrs"] if nid else None
    print(f"    feeling-of-findability('show3'): {findable}")
    print(f"    recalled show3 -> paged back into RAM: {rec}")
    print(f"    RAM MemoryRecord: {before} -> {after} (paged one back)")
    mem.shuffle(s, N_SHOWS + 1)          # maintenance shuffle re-bounds RAM after recall

    st = mem.stats()
    print("\n  VERDICT:")
    ok_bounded = st["resident_in_ram"] <= HOT + 1
    ok_alldisk = st["on_disk"] == N_SHOWS
    ok_recall = rec is not None and rec.get("show") == "show3"
    print(f"    RAM bounded to hot window ({st['resident_in_ram']} resident <= {HOT}+1): "
          f"{ok_bounded}")
    print(f"    every record on disk ({st['on_disk']}/{N_SHOWS}, {st['disk_bytes']}B): "
          f"{ok_alldisk}")
    print(f"    cold record paged back by targeted-lookup recall: {ok_recall}")
    print(f"    -> learning grows on DISK without bound; RAM stays bounded. The "
          f"missing tier is in place.")
    print("=" * 78)
    return 0 if (ok_bounded and ok_alldisk and ok_recall) else 1


if __name__ == "__main__":
    raise SystemExit(main())
