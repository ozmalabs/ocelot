"""phi_change_magnitude_diagnostic — WHAT IS C1's "CHANGE WITHOUT MOTION"?

DESCRIPTIVE, POST-HOC, AND LABELLED AS SUCH. It rescues nothing and revises no
registered measure (PROTOCOL §5): M6's four-way classification is reported
exactly as pre-registered. This adds the one statistic needed to READ it
honestly (§8).

M6 splits at EXACTLY ZERO, which is constant-free (§13) and therefore maximally
liberal: a block whose luminance moved by 0.001 counts as "changed". So
"80% of C1 cells changed without producing a vector" is only interesting if
that change is VISIBLE change rather than numerical residue.

The reference point used here FALLS OUT and is not tuned: the corpus is decoded
from an 8-BIT source, so **1.0 is the source encoding's own quantization step**.
A block whose maximum pixel excursion is below one 8-bit level did not change in
the signal — it changed in the arithmetic of the area-downsample. That is the
natural, non-arbitrary place to look, and it is the ONLY reference level
reported.

Draws NO seeds — pure numpy over decoded frames.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

from domains import motion_group_world as mgw                # noqa: E402

GRID, BLOCK = 72, 4
NCELL = GRID // BLOCK
N_PAIRS, N_FRAMES = 40, 45
STEP_8BIT = 1.0            # the SOURCE ENCODING's own quantization step
CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))


def main():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)

    out = {"provenance": ep.provenance_line(),
           "what": "DESCRIPTIVE post-hoc diagnostic; revises no registered "
                   "measure. Reference level 1.0 = the 8-bit source's own "
                   "quantization step, not a tuned threshold.",
           "seeds_drawn": 0}

    for name, epi, pin in CORPORA:
        frames, meta = vp.jellyfin_frames(N_FRAMES, every=1, start_s=300,
                                          size=GRID, episode_index=epi)
        if not str(meta.get("episode_id", "")).startswith(pin):
            raise SystemExit(f"{name} PIN MISMATCH. RUN VOID.")
        cnm_deltas, all_deltas, frame_max = [], [], []
        sub_step_cnm = tot_cnm = 0
        for t in range(min(N_PAIRS, len(frames) - 1)):
            a, b = np.asarray(frames[t], float), np.asarray(frames[t + 1], float)
            frame_max.append(float(np.abs(a - b).max()))
            d = np.abs(a - b).reshape(NCELL, BLOCK, NCELL, BLOCK).max(axis=(1, 3))
            nzv = mgw.vector_field(a, b, BLOCK).any(axis=-1)
            cnm = (d > 0.0) & ~nzv
            all_deltas.append(d.ravel())
            cnm_deltas.append(d[cnm])
            tot_cnm += int(np.count_nonzero(cnm))
            sub_step_cnm += int(np.count_nonzero(d[cnm] < STEP_8BIT))
        cd = np.concatenate(cnm_deltas) if cnm_deltas else np.array([])
        ad = np.concatenate(all_deltas)
        out[name] = {
            "episode_id": meta.get("episode_id"),
            "n_pairs": min(N_PAIRS, len(frames) - 1),
            "frame_max_abs_diff": {"mean": float(np.mean(frame_max)),
                                   "min": float(np.min(frame_max)),
                                   "max": float(np.max(frame_max))},
            "pairs_with_zero_total_change": int(sum(1 for m in frame_max if m == 0.0)),
            "block_delta_all": {q: float(np.percentile(ad, q))
                                for q in (50, 75, 90, 95, 99)},
            "change_without_motion": {
                "n": tot_cnm,
                "delta_percentiles": {q: float(np.percentile(cd, q))
                                      for q in (50, 75, 90, 95, 99)} if cd.size else None,
                "n_below_one_8bit_step": sub_step_cnm,
                "frac_below_one_8bit_step": (sub_step_cnm / tot_cnm) if tot_cnm else None,
                "max_delta": float(cd.max()) if cd.size else None,
            },
        }
        print(name, json.dumps(out[name], default=str)[:520], flush=True)

    p = os.path.join(ROOT, "results", "phi_change_magnitude.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("wrote", p)


if __name__ == "__main__":
    main()
