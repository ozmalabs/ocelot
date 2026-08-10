"""bigville_play_run -- record a PLAYABLE TIMELINE of a bigville scenario for the UI.
Runs a watchable town and writes results/bigville_play/play.json: the map, the residents,
and per-frame positions (walking hop-by-hop), speech, and located actions/trades -- all
real graph reads. Feed it to the UI's Play mode to WATCH the scenario unfold.

Usage:  python scripts/bigville_play_run.py [ticks] [cast] [seed]
"""
from __future__ import annotations

import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_play_world import BigvillePlayWorld              # noqa: E402

OUTDIR = os.path.join(_ROOT, "results", "bigville_play")


def main(argv):
    ticks = int(argv[1]) if len(argv) > 1 else 288      # ~8 days, watchable
    cast = int(argv[2]) if len(argv) > 2 else 18
    seed = int(argv[3]) if len(argv) > 3 else 276000
    os.makedirs(OUTDIR, exist_ok=True)

    t0 = time.time()
    w = BigvillePlayWorld(cast=cast, seed=seed)
    w.run_town(T=ticks)
    dt = time.time() - t0
    doc = w.play_doc()
    with open(os.path.join(OUTDIR, "play.json"), "w") as f:
        json.dump(doc, f, separators=(",", ":"))

    n_says = sum(len(fr["says"]) for fr in doc["frames"])
    n_acts = sum(len(fr["acts"]) for fr in doc["frames"])
    print("=== bigville PLAY timeline recorded ===")
    print("cast=%d ticks=%d days=%d frames=%d says=%d acts=%d  (%.1fs)"
          % (cast, ticks, doc["days"], len(doc["frames"]), n_says, n_acts, dt))
    print("residents:", len(doc["residents"]), "shops:", doc["shops"])
    # a couple of sample frames with speech/action so we can eyeball the render
    shown = 0
    for fr in doc["frames"]:
        if (fr["says"] or fr["acts"]) and shown < 6:
            shown += 1
            print("  t%-4d %s %s"
                  % (fr["t"],
                     [s["text"][:60] for s in fr["says"]],
                     [a["text"][:50] for a in fr["acts"]]))
    print("wrote:", os.path.join(OUTDIR, "play.json"),
          "(%.0f KB)" % (os.path.getsize(os.path.join(OUTDIR, "play.json")) / 1024))


if __name__ == "__main__":
    main(sys.argv)
