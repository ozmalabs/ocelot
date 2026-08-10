#!/usr/bin/env python3
"""Cache the REAL-VIDEO corpus this rung measures on -> `results/gapseam_starts.npz`.

Pure I/O, no content decision.  The episode is a POSITIONAL pick into the
sorted catalogue (`episode_index=0`, the same convention the video-probe rung
used), and every start time comes from a FIXED grid -- no start is selected for
its motion content, and all eight are reported in the results.

    PYTHONPATH=runners/dsl/python:. python3 scripts/pixelseam_corpus.py

Kept separate from `scripts/pixelseam_measure.py` so the measurement runs off a
COMMITTED artifact rather than a live network fetch: a rung whose corpus is
re-decoded per run cannot be reproduced once the source moves.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# The frame decoder is the video-probe rung's, reused verbatim rather than
# re-implemented -- two decoders would be two corpora.
_SRC = open(os.path.join(ROOT, "scripts", "video_probe_measure.py")).read()
_NS: dict = {"os": os, "sys": sys, "np": np, "ROOT": ROOT}
exec(_SRC[_SRC.index("def jellyfin_frames"):_SRC.index("def bsds_frame")], _NS)

START_GRID = [60, 180, 300, 420, 540, 660, 780, 900]
N_FRAMES = 24
SIZE = 48
EPISODE_INDEX = 0


def main() -> int:
    print(provenance_line())
    out, meta = {}, None
    for st in START_GRID:
        fr, m = _NS["jellyfin_frames"](N_FRAMES, every=1, start_s=st, size=SIZE,
                                       episode_index=EPISODE_INDEX)
        out[str(st)] = fr
        meta = meta or m
        d = np.abs(np.diff(fr, axis=0)).reshape(len(fr) - 1, -1)
        print("  start=%3d  frames=%d  mean|diff| %.3f  max pixel |diff| %.1f"
              % (st, len(fr), d.mean(), d.max()), flush=True)
    np.savez(os.path.join(ROOT, "results", "gapseam_starts.npz"), **out)
    json.dump(meta, open(os.path.join(ROOT, "results",
                                      "gapseam_frames48_meta.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
