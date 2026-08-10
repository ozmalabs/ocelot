"""Export a RICH play document (the `play_doc` schema: map/paper/council/institutions
+ per-frame pos/says/acts) from a live BigvilleLivingTownWorld run, so REPLAY mode can
exercise the same rich schema the LIVE stream uses.

Pure mechanical reader: it steps the town and calls `world.play_doc()` (itself a pure
graph read). No agent logic here.

    python -m web.townview.server.export_richplay --ticks 40 --cast 8
"""
from __future__ import annotations
import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run(ticks: int, cast: int, seed: int, out: str):
    from worlds.bigville_living_town_world import BigvilleLivingTownWorld as W
    w = W(cast=cast, seed=seed)
    for _ in range(ticks):
        w.integ_step()
    doc = w.play_doc()          # the full rich contract (map, residents, paper, frames...)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(doc, f)
    ev = sum(len(fr.get("acts", [])) + len(fr.get("says", [])) for fr in doc["frames"])
    print("wrote %s | grid %dx%d | residents %d | frames %d | located-events %d"
          % (out, doc["map"]["w"], doc["map"]["h"], len(doc["residents"]),
             len(doc["frames"]), ev))
    w.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=40)
    ap.add_argument("--cast", type=int, default=8)
    ap.add_argument("--seed", type=int, default=276000)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "townview_richplay", "play.json"))
    a = ap.parse_args()
    run(a.ticks, a.cast, a.seed, a.out)


if __name__ == "__main__":
    main()
