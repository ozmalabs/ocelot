"""motion_texture_diagnostic — IS BACKGROUND TEXTURE LOAD-BEARING?

NOT PRE-REGISTERED. A diagnostic on the SENSOR with GROUND TRUTH, prompted by
the standing literature point that segmentation-by-common-motion depends on the
background being textured: an untextured field can make the mechanism fail for
a STIMULUS reason rather than because the criterion is wrong. That is exactly
the kind of property that turns into a phantom mechanism failure, so it is
measured rather than assumed.

THE STIMULUS HAS KNOWN GROUND TRUTH. A whole frame translated by exactly one
block means EVERY block's true displacement is the same known vector. Any block
whose estimated vector differs is a SENSOR ERROR, and can be attributed
directly. So this asks: does the block-match sensor fail specifically where the
image is flat?

This changes no measure and re-runs no registered arm (§5: a diagnosis is not a
rescue). It exists to say whether the registered global-pan failure is the
criterion's fault or the sensor's.

Pure numpy. No substrate, no seeds drawn.
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
NCELL = GRID // BLOCK
CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def block_texture(frame):
    """Per-block standard deviation of luminance — the texture the block match
    has to work with. One number per motion cell, same lattice as the vectors."""
    f = np.asarray(frame, float)
    b = (f[:NCELL * BLOCK, :NCELL * BLOCK]
         .reshape(NCELL, BLOCK, NCELL, BLOCK).transpose(0, 2, 1, 3))
    return b.std(axis=(2, 3))


def pan_ground_truth(frame, shift=BLOCK):
    """Translate the whole frame by exactly one block. EVERY block's true
    displacement is (shift, shift); any deviation is a sensor error."""
    panned = np.roll(np.roll(frame, shift, axis=0), shift, axis=1)
    vf = mgw.vector_field(frame, panned, BLOCK)
    truth = np.array([float(shift), float(shift)])
    err = np.linalg.norm(vf - truth, axis=-1)
    return vf, err, block_texture(frame)


def main():
    vp = _vp()
    out = {}
    for name, epi, pin in CORPORA:
        frames, meta = vp.jellyfin_frames(8, every=1, start_s=300,
                                          size=GRID, episode_index=epi)
        if not str(meta.get("episode_id", "")).startswith(pin):
            raise SystemExit(f"{name} PIN MISMATCH. RUN VOID.")
        texs, errs = [], []
        for f in frames:
            _, e, t = pan_ground_truth(f)
            errs.append(e.ravel())
            texs.append(t.ravel())
        tex = np.concatenate(texs)
        err = np.concatenate(errs)
        wrong = err > 0

        # Texture QUARTILES of the field's own distribution — a partition of the
        # observed values, not a chosen cut point.
        qs = np.quantile(tex, [0.25, 0.50, 0.75])
        bands = [("Q1 flattest", tex <= qs[0]),
                 ("Q2", (tex > qs[0]) & (tex <= qs[1])),
                 ("Q3", (tex > qs[1]) & (tex <= qs[2])),
                 ("Q4 most textured", tex > qs[2])]
        rows = [{"band": lbl,
                 "n_blocks": int(m.sum()),
                 "mean_block_std": float(tex[m].mean()),
                 "sensor_error_rate": float(wrong[m].mean()),
                 "mean_vector_error": float(err[m].mean())}
                for lbl, m in bands]

        out[name] = {
            "meta": {k: meta.get(k) for k in ("episode_id", "name")},
            "overall_sensor_error_rate_on_known_pan": float(wrong.mean()),
            "block_texture_quartiles": [float(q) for q in qs],
            "share_blocks_with_zero_texture": float((tex == 0).mean()),
            "by_texture_band": rows,
        }
        print(name, json.dumps(out[name], indent=1), flush=True)

    path = os.path.join(ROOT, "results", "motion_texture_diagnostic.json")
    with open(path, "w") as fh:
        json.dump({"stimulus": "whole frame translated by exactly one block; "
                               "every block's true displacement is known",
                   "corpora": out}, fh, indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
