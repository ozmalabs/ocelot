#!/usr/bin/env python3
"""VIDEO PROBE RE-RUN — EXPLORATORY: the sd/identity layer, measured a DIFFERENT
WAY, because the pre-registered statistic turned out BLIND.

*** THIS IS AN EXPLORATORY PROBE. IT IS NOT A PRE-REGISTERED RESULT. ***
Nothing in `VISION_VIDEO_PROBE_RERUN_RESULTS.md`'s headline rests on it. It
follows the precedent of the original probe's §2.4b: an exploratory arm whose
only job is to make the NEXT pre-registration precise.

WHY IT EXISTS. Arm A8 pre-registered a COUNTED-OPERATION exponent for the
sd/identity layer, gated G1-G4. **All four gates PASSED and the answer was
still unusable**: every `scale_audit` counter is BYTE-IDENTICAL between a
12-cell and a 142-cell signature (21 candidates, 68 rule enumerations, 1 FFI
call, at every point) while wall-clock goes 7 ms -> 93 ms.

THE DIAGNOSIS, and it is architectural: **the sd/identity layer's work is
invisible to graph-level instrumentation because a signature is an ATTRIBUTE,
not a subgraph.** N cells live inside ONE node's attribute list, so the graph
the rule engine matches over is CONSTANT in N; all the cost is inside
`ShapeDecode` / `TransformDecode` Term EVALUATION, which the audit does not
count. Taken literally the pre-registered rule reads e_sd = 0.0 and concludes
"not binding, the wall fell" -- a fluent wrong answer of exactly the kind
PROTOCOL §1 exists to prevent. It is therefore reported as UNINTERPRETABLE on
its own statistic, and NOT rescued by redefining the statistic (§5).

WHAT THIS PROBE ADDS. Two axes, both wall-clock, both with load state recorded,
both explicitly NOT load-independent and therefore explicitly NOT a share:

  E1  the N axis   -- the SAME workload A8 declared, timed instead of counted
  E2  the CODEBOOK axis -- the axis NOBODY has measured. A8's workload holds
      exactly ONE signature. Real recognition decodes against MANY. If the
      identity layer's wall is anywhere, K is the more likely axis than N,
      and no rung has ever put a number on it.

USAGE
    python scripts/video_probe_rerun_sd_explore.py
"""
from __future__ import annotations

import argparse
import gc
import importlib.util as _iu
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

DT = ["pred", "coord:r", "coord:c", "val"]
K_QUANT = 2
REPEATS = 5


def load_state() -> dict:
    with open("/proc/loadavg") as fh:
        p = fh.read().split()
    return {"load1": float(p[0]), "load5": float(p[1]), "load15": float(p[2])}


def fit(xs, ys):
    if len(xs) < 3:
        return None
    x, y = np.log10(np.asarray(xs, float)), np.log10(np.asarray(ys, float))
    A = np.vstack([x, np.ones_like(x)]).T
    (m, b), res, *_ = np.linalg.lstsq(A, y, rcond=None)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    ss_res = float(res[0]) if len(res) else 0.0
    return {"exponent": float(m), "intercept": float(b),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot else None,
            "n_points": len(xs)}


def frame_to_cells(frame, k=K_QUANT):
    q = vp._quantize(frame, k)
    return [["cell", r, c, f"v{v}"]
            for r, row in enumerate(q) for c, v in enumerate(row) if v]


def boot_sd():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def run_once(target_cells, held_signatures):
    """Hold `held_signatures` in the codebook, present `target_cells`, time the
    fixpoint. `held_signatures[0]` is the target's own signature, so the
    recognition is always the same difficulty -- only the codebook SIZE varies."""
    gc.collect()
    s, ag, native = boot_sd()
    for i, sig in enumerate(held_signatures):
        s.add_node("ShapeSignature",
                   {"name": f"held{i}", "signature": json.dumps(sig),
                    "kind": "faculty", "faculty": f"held{i}", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": target_cells, "key": ["probe"],
                      "status": "decoded", "residual": target_cells,
                      "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    t0 = time.perf_counter()
    err = None
    try:
        native.run_rules()
    except Exception as e:                       # noqa: BLE001
        err = f"{type(e).__name__}: {e}"
    ms = (time.perf_counter() - t0) * 1000.0
    st = s.node(obs)["attrs"].get("status")
    return ms, st, err


def timed(target_cells, held, repeats=REPEATS):
    """Repeat and report the MEDIAN plus the spread. A single wall-clock sample
    on a shared machine is a rumour; a median of 5 with its spread reported is
    a measurement with a stated precision."""
    samples, statuses, errs = [], set(), set()
    for _ in range(repeats):
        ms, st, err = run_once(target_cells, held)
        samples.append(ms)
        statuses.add(st)
        if err:
            errs.add(err)
    return {"ms_median": statistics.median(samples),
            "ms_min": min(samples), "ms_max": max(samples),
            "ms_spread_frac": (max(samples) - min(samples)) / max(statistics.median(samples), 1e-9),
            "samples": samples, "statuses": sorted(statuses),
            "recognized": all(st in ("recognized", "recognized_transformed")
                              for st in statuses),
            "errors": sorted(errs)}


# --------------------------------------------------------------------------- #
def e1_n_axis(sides):
    """E1 -- the N axis. A8's declared workload, timed instead of counted."""
    rows = []
    for g in sides:
        f, _m = vp.jellyfin_frames(2, every=2, start_s=300, size=g)
        cells = frame_to_cells(np.asarray(f[0][:g, :g], np.float32))
        t = timed(cells, [cells])
        t.update({"side": g, "n_cells": len(cells)})
        rows.append(t)
        print(f"  [E1] side={g:3d} n_cells={len(cells):4d} "
              f"{t['ms_median']:8.1f} ms (spread {t['ms_spread_frac']*100:.1f}%) "
              f"{t['statuses']}", flush=True)
    live = [r for r in rows if r["recognized"]]
    return {"axis": "N (signature cells), codebook K=1", "rows": rows,
            "all_recognized": all(r["recognized"] for r in rows),
            "fit_ms_vs_cells": fit([r["n_cells"] for r in live],
                                   [r["ms_median"] for r in live])}


def e2_codebook_axis(side, ks):
    """E2 -- the CODEBOOK axis, the one nobody has measured.

    The target and its held twin are FIXED; only the number of OTHER held
    signatures varies. Decoys are REAL frames from later in the same episode,
    not synthetic -- a decoy that is trivially separable would flatter the
    scaling."""
    n_needed = max(ks)
    f, _m = vp.jellyfin_frames(2 + n_needed * 4, every=2, start_s=300, size=side)
    target = frame_to_cells(np.asarray(f[0][:side, :side], np.float32))
    decoys = [frame_to_cells(np.asarray(fr[:side, :side], np.float32))
              for fr in f[1:]]
    decoys = [d for d in decoys if d]
    rows = []
    for K in ks:
        held = [target] + decoys[:K - 1]
        if len(held) < K:
            print(f"  [E2] K={K}: only {len(held)} distinct held sigs available "
                  f"— point SKIPPED, not padded", flush=True)
            continue
        t = timed(target, held)
        t.update({"K_codebook": K, "n_held": len(held), "n_cells": len(target)})
        rows.append(t)
        print(f"  [E2] K={K:3d} n_cells={len(target):4d} "
              f"{t['ms_median']:9.1f} ms (spread {t['ms_spread_frac']*100:.1f}%) "
              f"{t['statuses']}", flush=True)
    live = [r for r in rows if r["recognized"]]
    return {"axis": "K (codebook size), N fixed", "side": side, "rows": rows,
            "all_recognized": all(r["recognized"] for r in rows) if rows else False,
            "fit_ms_vs_K": fit([r["K_codebook"] for r in live],
                               [r["ms_median"] for r in live])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/video_probe_rerun_sd_explore.json")
    ap.add_argument("--e2-side", type=int, default=12)
    a = ap.parse_args()

    prov = provenance_line()
    print(f"[provenance] {prov}", flush=True)
    out = {"provenance": prov,
           "kind": "EXPLORATORY — NOT a pre-registered result (see module docstring)",
           "prereg": "VISION_VIDEO_PROBE_RERUN_PREREG.md",
           "why": ("arm A8's pre-registered COUNTED statistic is structurally "
                   "blind to this layer: a signature is an ATTRIBUTE, not a "
                   "subgraph, so the matched graph is constant in N"),
           "repeats_per_point": REPEATS,
           "load_state_at_start": load_state()}

    print("[E1] the N axis (A8's workload, timed):", flush=True)
    out["E1_n_axis"] = e1_n_axis([4, 6, 8, 10, 12, 14, 16])
    print(f"  -> fit {out['E1_n_axis']['fit_ms_vs_cells']}", flush=True)

    print(f"[E2] the CODEBOOK axis at side={a.e2_side}:", flush=True)
    out["E2_codebook_axis"] = e2_codebook_axis(a.e2_side, [1, 2, 4, 8, 16, 32])
    print(f"  -> fit {out['E2_codebook_axis']['fit_ms_vs_K']}", flush=True)

    out["load_state_at_end"] = load_state()
    with open(os.path.join(ROOT, a.out), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
