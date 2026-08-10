"""motion_field_diagnostic — WHAT IS ACTUALLY IN THE VECTOR FIELD?

NOT PRE-REGISTERED. This is a diagnostic on the SENSOR, run after the registered
arms, and it can only weaken this rung's claim — it exists to say precisely why
a null is a null. It touches no threshold, changes no measure, and re-runs no
registered arm (§5: a diagnosis is not a rescue).

The question it answers: when the common-motion mechanism declines on real
frames, is that because the scene has no motion-defined objects, or because the
MOTION SIGNAL IS BELOW THE SENSOR'S RESOLUTION at this spatial and temporal
grain? Those are very different findings and the registered arms cannot tell
them apart.

Pure numpy over the vector field. No substrate, no seeds drawn.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import motion_group_world as mgw     # noqa: E402

GRID = 72
BLOCK = 4
N_FRAMES = 45
CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    vp = _vp()
    out = {}
    for name, epi, pin in CORPORA:
        frames, meta = vp.jellyfin_frames(N_FRAMES, every=1, start_s=300,
                                          size=GRID, episode_index=epi)
        if not str(meta.get("episode_id", "")).startswith(pin):
            raise SystemExit(f"{name} PIN MISMATCH. RUN VOID.")
        rows = []
        for stride in (1, 2, 4, 8):
            nz, uniq, maxmag, dlum = [], [], [], []
            for t in range(0, len(frames) - stride, max(1, stride)):
                vf = mgw.vector_field(frames[t], frames[t + stride], BLOCK)
                mag = np.linalg.norm(vf, axis=-1)
                nz.append(float((mag > 0).mean()))
                uniq.append(int(len(np.unique(vf.reshape(-1, 2), axis=0))))
                maxmag.append(float(mag.max()))
                dlum.append(float(np.abs(frames[t + stride] - frames[t]).mean()))
            rows.append({
                "frame_stride": stride,
                "share_cells_with_nonzero_vector": float(np.mean(nz)),
                "distinct_vectors_per_field": float(np.mean(uniq)),
                "max_vector_magnitude": float(np.mean(maxmag)),
                "mean_abs_luminance_change": float(np.mean(dlum)),
                "n_pairs": len(nz),
            })
        out[name] = {"meta": {k: meta.get(k) for k in ("episode_id", "name")},
                     "by_stride": rows}
        print(name, json.dumps(rows, indent=1), flush=True)

    path = os.path.join(ROOT, "results", "motion_field_diagnostic.json")
    with open(path, "w") as fh:
        json.dump({"config": {"GRID": GRID, "BLOCK": BLOCK,
                              "search_radius": BLOCK,
                              "note": "radius = block, from overlap"},
                   "corpora": out}, fh, indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
