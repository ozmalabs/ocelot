"""salience_rescore_field — compute the per-region SALIENCE field for the
invariant-comparator base frames, using the UNCHANGED `vision_colour` seed.

Mechanical I/O only (CLAUDE.md / PROTOCOL §0): this script converts a colour
frame into integer cone triples per comparator region, hands them to
`colour_world.add_field`, ticks the substrate to a fixpoint, and reads `csal`
and `lsal` back. The opponent-contrast computation is the seed rule
`cc_contrast` -- no salience is computed here.

`csal` is the PRIMARY (independent) measure: the comparator's frames were
decoded `format="gray"`, so chroma is absent from its input by construction.
`lsal` is the CONFOUNDED secondary, reported only for contrast.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import colour_world as cw  # noqa: E402
from domains import invariant_comparator_world as iw  # noqa: E402

N_BASE = 50

# Hunt-Pointer-Estevez linear sRGB -> LMS, the DECLARED robustness variant of
# the prereg. Published matrix, quoted not tuned; no constant of mine.
HPE = np.array([[0.38971, 0.68898, -0.07868],
                [-0.22981, 1.18340, 0.04641],
                [0.00000, 0.00000, 1.00000]], float)


def cone_cells(rgb_frame, *, mode):
    """One integer cone triple per comparator region (mechanical ingest).

    `rgb_frame` is (24,24,3) in 0..255. Regions are the comparator's OWN 16
    tiles, laid out on the 4x4 grid their origins define.
    """
    cells = []
    for i, (r0, c0) in enumerate(iw.region_origins()):
        tile = rgb_frame[r0:r0 + iw.REGION, c0:c0 + iw.REGION, :]
        mean = tile.reshape(-1, 3).mean(axis=0)          # R,G,B in 0..255
        if mode == "rgb":
            lms = mean                                   # zero free parameters
        elif mode == "hpe":
            lms = HPE @ (mean / 255.0) * 255.0
        else:
            raise ValueError(mode)
        cells.append({"rrow": r0 // iw.REGION, "rcol": c0 // iw.REGION,
                      "cL": int(round(float(lms[0]))),
                      "cM": int(round(float(lms[1]))),
                      "cS": int(round(float(lms[2]))),
                      "region_index": i})
    return cells


def field_for_frame(rgb_frame, *, mode):
    """Boot, ingest, tick to fixpoint, read csal/lsal back. Returns two lists
    indexed by comparator region index."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_stream", "vision_colour"])
    cells = cone_cells(rgb_frame, mode=mode)
    # budget is irrelevant here (we read the salience field, not the stream);
    # it is set to the cell count so nothing is starved.
    h = cw.add_field(s, budget=len(cells), cells=cells, nrows=4, ncols=4)
    cw.set_flags(s, salience=1.0, colour=1.0)
    cw.tick(s)
    csal = cw.read_attr(s, h, "csal")
    lsal = cw.read_attr(s, h, "lsal")
    return csal, lsal


def main():
    frames_dir, out_path = sys.argv[1], sys.argv[2]
    out = {"engine": provenance_line(), "corpora": {}}
    for cid in ("C1", "C2"):
        rgb = np.load(os.path.join(frames_dir, f"frames_{cid}.npz"))["rgb"]
        per_mode = {}
        for mode in ("rgb", "hpe"):
            rows = []
            for t in range(N_BASE):
                csal, lsal = field_for_frame(rgb[t], mode=mode)
                rows.append({"base": t, "csal": csal, "lsal": lsal})
            per_mode[mode] = rows
            print(f"[{cid}/{mode}] {N_BASE} base frames done", flush=True)
        out["corpora"][cid] = per_mode
    with open(out_path, "w") as fh:
        json.dump(out, fh)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
