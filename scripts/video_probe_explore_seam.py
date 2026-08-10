#!/usr/bin/env python3
"""VIDEO PROBE — EXPLORATORY: what happens if the pixel→symbol seam is FORCED?

*** THIS IS AN EXPLORATORY PROBE. IT IS NOT A PRE-REGISTERED RESULT. ***
`VISION_VIDEO_PROBE_PREREG.md` §3/S4 decided the seam question by STRUCTURAL
ENUMERATION, and the answer was that no path exists, so the prereg's own decision
rule says: report the absence and stop. Nothing here revises that verdict and no
claim in `VISION_VIDEO_PROBE_RESULTS.md` rests on it.

WHY IT EXISTS ANYWAY. The rung's job includes characterising the first blocker
"precisely enough that the next rung can be pre-registered against it". "No path
exists" does not distinguish two very different worlds:

  (a) the seam is merely UNBUILT — hand-build the tuples and the identity layer
      works on real pixels, so the next rung is a plumbing job; or
  (b) the seam is UNREACHABLE AT THIS GRAIN — the identity layer's input format
      does not survive contact with a real frame's size or statistics, so the
      next rung is an architecture question.

This probe distinguishes them, cheaply, on ONE real frame. Its output is a
DIRECTION for the next pre-registration, never evidence for a claim.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/video_probe_explore_seam.py
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
import importlib.util as _iu  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

DT = ["pred", "coord:r", "coord:c", "val"]


def frame_to_cells(frame, k):
    """The seam, hand-built: a quantized real frame as the identity layer's own
    `["cell", r, c, val]` relation tuples. ONLY non-background cells are emitted
    (value 0 is treated as ground), which is the most charitable possible
    encoding — it is what a segmenter would hand over if one existed."""
    q = vp._quantize(frame, k)
    out = []
    for r, row in enumerate(q):
        for c, v in enumerate(row):
            if v:
                out.append(["cell", r, c, f"v{v}"])
    return out


def boot_sd():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def probe(frame, k, *, hold=True, budget_s=120.0):
    """Hold the frame's own signature in the codebook, then present the SAME
    signature. This is the EASIEST possible recognition — literal self-identity,
    no transform, no novelty. If this does not work, nothing harder will."""
    cells = frame_to_cells(frame, k)
    s, ag, native = boot_sd()
    if hold:
        s.add_node("ShapeSignature", {"name": "frame0", "signature": json.dumps(cells),
                                      "kind": "faculty", "faculty": "frame0",
                                      "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": cells, "key": ["probe"],
                                     "status": "decoded", "residual": cells,
                                     "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    t0 = time.perf_counter()
    timed_out = False
    try:
        native.run_rules()
    except Exception as e:                     # noqa: BLE001 — report, never mask
        return {"k": k, "n_cells": len(cells), "hold": hold,
                "error": f"{type(e).__name__}: {e}",
                "ms": (time.perf_counter() - t0) * 1000.0}
    ms = (time.perf_counter() - t0) * 1000.0
    at = s.node(obs)["attrs"]
    return {"k": k, "n_cells": len(cells), "hold": hold,
            "status": at.get("status"),
            "n_axes_minted": len(list(s.nodes("CapabilityAxis"))),
            "ms": ms, "timed_out": timed_out,
            "recognized": at.get("status") in ("recognized", "recognized_transformed")}


def main():
    prov = provenance_line()
    print(f"[provenance] {prov}", flush=True)
    frames, meta = vp.jellyfin_frames(2, every=2, start_s=300, size=16)
    out = {"provenance": prov,
           "kind": "EXPLORATORY — NOT a pre-registered result",
           "corpus": meta, "rows": []}
    f = frames[0][:16, :16]
    for k in (2, 4):
        for hold in (True, False):
            r = probe(f, k, hold=hold)
            out["rows"].append(r)
            print(f"[seam] k={k} hold={hold} cells={r['n_cells']} "
                  f"-> {r.get('status', r.get('error'))} "
                  f"axes={r.get('n_axes_minted')} {r['ms']:.0f}ms", flush=True)
    # A synthetic 4-cell control: the same machinery on the size the arc uses.
    tiny = [["cell", 0, 0, "v1"], ["cell", 1, 0, "v1"],
            ["cell", 2, 0, "v1"], ["cell", 2, 1, "v1"]]
    s, ag, native = boot_sd()
    s.add_node("ShapeSignature", {"name": "L", "signature": json.dumps(tiny),
                                  "kind": "faculty", "faculty": "L", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": tiny, "key": ["probe"],
                                     "status": "decoded", "residual": tiny,
                                     "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    t0 = time.perf_counter()
    native.run_rules()
    out["synthetic_control_4_cells"] = {
        "status": s.node(obs)["attrs"].get("status"),
        "ms": (time.perf_counter() - t0) * 1000.0, "n_cells": 4}
    print(f"[control] 4-cell synthetic -> "
          f"{out['synthetic_control_4_cells']['status']} "
          f"{out['synthetic_control_4_cells']['ms']:.1f}ms", flush=True)

    p = os.path.join(ROOT, "results", "video_probe_seam_explore.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {p}", flush=True)


if __name__ == "__main__":
    main()
