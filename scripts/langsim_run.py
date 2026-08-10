"""langsim RUNNER (block 243000): run one economy+building episode and dump the
glass-box transcript of REAL graph-emitted utterances + the trade/build ledger.

Usage: python scripts/langsim_run.py [--mode language|none|scrambled] [--T 20]
"""
from __future__ import annotations
import argparse
import os
import sys

_GB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_GB, "runners", "dsl", "python"))
sys.path.insert(0, _GB)

from worlds.langsim_world import LangSimWorld              # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="language",
                    choices=("language", "none", "scrambled"))
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--psychopath", action="store_true",
                    help="all-psychopath population (w_supergraph=0)")
    a = ap.parse_args()
    w = float(0.0) if a.psychopath else 1.0
    world = LangSimWorld([w, w, w, w], mode=a.mode, seed=a.seed)
    out = world.run(T=a.T)
    print("OUTCOME:", out)
    print(f"\n--- REAL utterance transcript (first 12 of {len(world.transcripts)}) ---")
    for t in world.transcripts[:12]:
        print(f"  t{t['tick']:>2} {t['dir']}  say={t['utterance']!r:16} "
              f"heard={t['delivered']!r:16} comprehended_offer={t['comprehended']}")
    print(f"\n--- trade/build ledger (first 10 of {len(world.trade_log)}) ---")
    for r in world.trade_log[:10]:
        print(f"  t{r['tick']:>2} a{r['a']}<->b{r['b']} "
              f"give=({r['chosen_a']},{r['chosen_b']}) "
              f"built=({r['built_a']},{r['built_b']}) value=({r['value_a']},{r['value_b']})")


if __name__ == "__main__":
    main()
