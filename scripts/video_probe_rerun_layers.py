#!/usr/bin/env python3
"""VIDEO PROBE RE-RUN — arms A8 (the sd/identity layer's scale) and A9
(attribution: batch-apply isolated on ONE engine).

Pre-registration: `VISION_VIDEO_PROBE_RERUN_PREREG.md`, committed BEFORE this ran
at `fcc194c5`.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***
No seed is edited on disk, no rule added, no default changed, no Rust touched.
A9's batch-off arm points `wave_world._CHANGE_SEED` at a TEMPORARY copy of the
seed with the `batch` key stripped -- the batch-apply rung's own `off_new`
control mechanism, reused verbatim: the flag is graph DATA, so the control varies
the DATA, not the code path. The temp file is deleted; the repo is untouched.

ARCHITECTURE (CLAUDE.md): every function here is mechanical I/O -- decode a
frame, build tuples, add nodes, run the fixpoint, read counters. No conditional
over graph state decides anything the agent should decide.

WHY A8 EXISTS. THREE rungs in a row -- scale-split, batch-apply, locality-index
-- each closed with the IDENTICAL bound: "ONE workload (the retina drive; the
sd/identity layer is NOT measured)." That is a blind spot declared three times
and never filled. If the drive path went quadratic -> linear, the sd/identity
layer is the most likely place for the wall to have RELOCATED.

EVERY HEADLINE HERE IS A COUNT, NOT A DURATION. Wall-clock is recorded once,
with its load state, and enters no exponent and no share.

USAGE
    python scripts/video_probe_rerun_layers.py --out results/video_probe_rerun_layers.json
"""
from __future__ import annotations

import argparse
import gc
import importlib.util as _iu
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint pins its OWN tree's engine,
# BEFORE any substrate_rs import.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from domains import wave_world  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import (  # noqa: E402
    add_lateral_retina, set_lat_params)

# The committed video-probe instrument, imported WHOLE -- the frame decode, the
# quantizer and the log-log fit are ITS code, not a reimplementation. A
# comparison is worth nothing if the two sides are two different objects.
_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

AUDIT = _native.Substrate
DT = ["pred", "coord:r", "coord:c", "val"]

# A8's declared sweep (prereg §3/A8). Sides, not cell counts: N is READ from the
# emitted signature, never set (§13).
A8_SIDES = [4, 6, 8, 10, 12, 14, 16]
A8_K = 2
# A9's declared sweep -- the SAME grid list S5 fits, so the two are comparable.
A9_SIZES = [12, 16, 24, 32]
A9_TICKS = 20
A9_WARMUP = 5
IGNITE_EVERY = vp.IGNITE_EVERY


# --------------------------------------------------------------------------- #
#  machine state -- a number without it is a rumour (§0.1 corollary)
# --------------------------------------------------------------------------- #
def load_state() -> dict:
    with open("/proc/loadavg") as fh:
        parts = fh.read().split()
    return {"load1": float(parts[0]), "load5": float(parts[1]),
            "load15": float(parts[2]), "procs": parts[3]}


def counters() -> dict:
    return dict(AUDIT.scale_audit_snapshot())


def fit(xs, ys):
    """log-log least squares -- the video probe's own fit, same form."""
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


# --------------------------------------------------------------------------- #
#  A8 -- the sd/identity layer, driven exactly as the §2.4b seam probe drove it
# --------------------------------------------------------------------------- #
def frame_to_cells(frame, k):
    """The seam, hand-built -- byte-for-byte `video_probe_explore_seam.py`'s
    encoding: a quantized real frame as `["cell", r, c, "v<k>"]` tuples, non-zero
    cells only (value 0 is ground). The most charitable encoding there is."""
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


def a8_point(frame, k, *, audit_on=True):
    """ONE sweep point: hold the frame's own signature, present it, run to
    fixpoint, read the counters. Literal self-identity -- the easiest
    recognition that exists."""
    gc.collect()
    cells = frame_to_cells(frame, k)
    s, ag, native = boot_sd()
    s.add_node("ShapeSignature", {"name": "frame0", "signature": json.dumps(cells),
                                  "kind": "faculty", "faculty": "frame0",
                                  "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": cells, "key": ["probe"],
                                     "status": "decoded", "residual": cells,
                                     "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(bool(audit_on))
    t0 = time.perf_counter()
    err = None
    try:
        native.run_rules()
    except Exception as e:                       # noqa: BLE001 -- report, never mask
        err = f"{type(e).__name__}: {e}"
    ms = (time.perf_counter() - t0) * 1000.0
    AUDIT.scale_audit_set_enabled(False)
    c = counters()
    at = s.node(obs)["attrs"]
    status = at.get("status")
    return {
        "n_cells": len(cells), "k": k, "audit_on": bool(audit_on),
        "status": status,
        # G2's liveness half: a frozen or erroring loop is infinitely fast.
        "recognized": status in ("recognized", "recognized_transformed"),
        "error": err,
        "n_axes_minted": len(list(s.nodes("CapabilityAxis"))),
        "counters": c,
        "ops_total": int(sum(c.values())),
        "cand_enum": int(c.get("cand_enum", 0)),
        "ms": ms,
    }


def arm_a8(sides, k):
    """The sd/identity layer's scale, GATED BEFORE ANY NUMBER IS READ."""
    frames = {}
    for g in sides:
        f, _meta = vp.jellyfin_frames(2, every=2, start_s=300, size=g)
        frames[g] = np.asarray(f[0][:g, :g], np.float32)

    # -- G1: zero-when-off, on a LIVE workload (the biggest one) --
    g1 = a8_point(frames[sides[-1]], k, audit_on=False)
    g1_pass = (g1["ops_total"] == 0) and g1["recognized"]

    rows = [a8_point(frames[g], k, audit_on=True) for g in sides]

    # -- G3: determinism, two independent runs, byte-identical counters --
    rerun = [a8_point(frames[g], k, audit_on=True) for g in sides]
    g3_diffs = [
        {"n_cells": a["n_cells"],
         "differing": sorted(kk for kk in set(a["counters"]) | set(b["counters"])
                             if a["counters"].get(kk) != b["counters"].get(kk))}
        for a, b in zip(rows, rerun)]
    g3_pass = all(not d["differing"] for d in g3_diffs)

    # -- G2: liveness -- ops > 0 AND recognized at EVERY point --
    g2_pass = all(r["ops_total"] > 0 and r["recognized"] and not r["error"]
                  for r in rows)
    # -- G4: N must span >= 4x or the fit is meaningless --
    ns = [r["n_cells"] for r in rows]
    g4_span = (max(ns) / max(min(ns), 1)) if ns else 0.0
    g4_pass = g4_span >= 4.0

    gates = {"G1_zero_when_off": {"pass": bool(g1_pass),
                                  "ops_with_audit_off": g1["ops_total"],
                                  "recognized": g1["recognized"]},
             "G2_liveness": {"pass": bool(g2_pass),
                             "statuses": [r["status"] for r in rows]},
             "G3_determinism": {"pass": bool(g3_pass), "diffs": g3_diffs},
             "G4_N_varies": {"pass": bool(g4_pass), "span": g4_span,
                             "n_cells": ns},
             "all_pass": bool(g1_pass and g2_pass and g3_pass and g4_pass)}

    out = {"arm": "A8 — sd/identity layer scale", "k": k, "sides": sides,
           "gates": gates, "rows": rows}
    if gates["all_pass"]:
        out["fit_ops_vs_cells"] = fit(ns, [r["ops_total"] for r in rows])
        out["fit_cand_enum_vs_cells"] = fit(ns, [r["cand_enum"] for r in rows])
        # wall-clock: reported ONCE, never an exponent, never a share.
        out["wall_ms_by_n_cells"] = {r["n_cells"]: r["ms"] for r in rows}
    else:
        out["fit_ops_vs_cells"] = None
        out["verdict_note"] = ("UNINTERPRETABLE — a gate failed; no exponent is "
                               "claimed (prereg §3/A8)")
    return out


# --------------------------------------------------------------------------- #
#  A9 -- attribution. The SAME drive, the SAME engine, ONE bit of seed DATA.
# --------------------------------------------------------------------------- #
def _strip_batch_seed() -> str:
    """A temp copy of `seeds/vision_change.json` with `batch` stripped from every
    rule -- `batch_apply_measure.py::_strip_batch_seed`, verbatim."""
    import tempfile
    with open(os.path.join(ROOT, "seeds", "vision_change.json")) as fh:
        seed = json.load(fh)
    for r in seed.get("rules", []):
        r.pop("batch", None)
    fd, path = tempfile.mkstemp(suffix="_vision_change_nobatch.json")
    with os.fdopen(fd, "w") as fh:
        json.dump(seed, fh)
    return path


def _seed_batch_flags() -> dict:
    with open(os.path.join(ROOT, "seeds", "vision_change.json")) as fh:
        seed = json.load(fh)
    return {r["name"]: bool(r.get("batch", False)) for r in seed.get("rules", [])}


def _drive_dispatch_name() -> str:
    """WHICH native method `_drive_phase` calls, READ OUT OF THE SOURCE rather
    than assumed (§12.3)."""
    with open(os.path.join(ROOT, "domains", "wave_world.py")) as fh:
        body = fh.read()
    for name in ("apply_rule_batch", "apply_rule_once"):
        if f"nat.{name}(idx)" in body:
            return name
    return "<unrecognised>"


def a9_point(g, frames):
    """One grid of the REAL-FRAME drive: counted ops AND wall, same schedule the
    video probe's S5 uses (ignite every 5th tick, real frames every tick)."""
    gc.collect()
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    world = WaveWorld(s, h=g, w=g, seed=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)

    for i in range(A9_WARMUP):
        world.step(ignite_k=0, frame=frames[i % len(frames)].astype(np.float32))

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    t0 = time.perf_counter()
    for i in range(A9_TICKS):
        world.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0,
                   frame=frames[i % len(frames)].astype(np.float32))
    wall_ms = (time.perf_counter() - t0) / A9_TICKS * 1000.0
    AUDIT.scale_audit_set_enabled(False)
    c = counters()

    # liveness: a frozen world is infinitely fast and scales beautifully.
    active = sum(1 for n in world.cells.values()
                 if s.node(n)["attrs"].get("state") == "active")
    return {"grid": g, "cells": g * g, "ops_total": int(sum(c.values())),
            "cand_enum": int(c.get("cand_enum", 0)),
            "epochs_apply_once": int(c.get("epochs_apply_once", 0)),
            "ms_per_tick": wall_ms, "n_active_cells": active,
            "counters": c}


def arm_a9(sizes, frames_by_size):
    # The COMMITTED seed path, captured once. The control restores it exactly --
    # `_CHANGE_SEED` defaults to a real path, not to None, so "reset to None"
    # would silently break the live arm rather than restore it.
    committed_seed_path = wave_world._CHANGE_SEED
    arms = {}
    for label, batch in (("batch_LIVE_as_committed", True),
                         ("batch_STRIPPED_control", False)):
        tmp = None
        if not batch:
            tmp = _strip_batch_seed()
            wave_world._CHANGE_SEED = tmp
        else:
            wave_world._CHANGE_SEED = committed_seed_path
        try:
            rows = [a9_point(g, frames_by_size[g]) for g in sizes]
        finally:
            wave_world._CHANGE_SEED = committed_seed_path
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
        arms[label] = {
            "batch_flag_live": batch,
            "rows": rows,
            "fit_ops_vs_cells": fit([r["cells"] for r in rows],
                                    [r["ops_total"] for r in rows]),
            "fit_wall_vs_cells": fit([r["cells"] for r in rows],
                                     [r["ms_per_tick"] for r in rows]),
            "load_state": load_state(),
        }
    return {"arm": "A9 — attribution (batch-apply isolated on ONE engine)",
            "seed_batch_flags_AS_COMMITTED": _seed_batch_flags(),
            "drive_phase_dispatches_to": _drive_dispatch_name(),
            "native_has_apply_rule_batch":
                hasattr(_native.Substrate, "apply_rule_batch"),
            "arms": arms}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/video_probe_rerun_layers.json")
    ap.add_argument("--skip", default="")
    a = ap.parse_args()
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}

    prov = provenance_line()
    print(f"[provenance] {prov}", flush=True)
    out = {"provenance": prov,
           "prereg": "VISION_VIDEO_PROBE_RERUN_PREREG.md",
           "prereg_sha": "fcc194c5d0e330dde339f29b898b0f0c75e019a8",
           "base_sha": "c6c022f8fc2ab212b130ad3e34a761af6a20aaee",
           "load_state_at_start": load_state()}

    if "a8" not in skip:
        out["A8_sd_identity_scale"] = arm_a8(A8_SIDES, A8_K)
        r = out["A8_sd_identity_scale"]
        print(f"[A8] gates={r['gates']['all_pass']} "
              f"fit={r.get('fit_ops_vs_cells')}", flush=True)
        for row in r["rows"]:
            print(f"     n_cells={row['n_cells']:4d} ops={row['ops_total']:12,d} "
                  f"{row['status']} {row['ms']:.0f}ms", flush=True)

    if "a9" not in skip:
        fbs = {}
        for g in A9_SIZES:
            f, _m = vp.jellyfin_frames(8, every=2, start_s=300, size=g)
            fbs[g] = f
        out["A9_attribution"] = arm_a9(A9_SIZES, fbs)
        for lab, arm in out["A9_attribution"]["arms"].items():
            print(f"[A9] {lab}: ops_exp={arm['fit_ops_vs_cells']['exponent']:.4f} "
                  f"(r2 {arm['fit_ops_vs_cells']['r2']:.5f})  "
                  f"wall_exp={arm['fit_wall_vs_cells']['exponent']:.4f}",
                  flush=True)
            for row in arm["rows"]:
                print(f"      cells={row['cells']:5d} ops={row['ops_total']:14,d} "
                      f"{row['ms_per_tick']:9.3f} ms/tick "
                      f"active={row['n_active_cells']}", flush=True)

    out["load_state_at_end"] = load_state()
    with open(os.path.join(ROOT, a.out), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
