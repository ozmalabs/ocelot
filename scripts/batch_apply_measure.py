"""BATCH-APPLY THE DRIVE RULES — before/after, on ONE binary where possible.

Pre-registration: `VISION_BATCH_APPLY_PREREG.md`, committed at 767f0850 BEFORE
any Rust/seed/adapter edit.

*** THE HEADLINE IS A COUNT. Wall-clock appears once, labelled, with its load
state, and is excluded from every share. ***

WHAT THIS MEASURES, AND WHY IT REUSES `scale_split_measure`
-----------------------------------------------------------
The prereg fixed the statistic as "the SAME instrument the scale rung merged,
so the numbers are directly comparable". That is taken literally: the sweep
point, the bucket definition, the log-log `fit`, the liveness gate and the
conservation asserts are IMPORTED from `scripts/scale_split_measure.py` rather
than reimplemented. A reimplementation would be a second instrument, and this
arc has caught eleven inert ones.

THE THREE ARMS
--------------
  off_baseline   unmodified tree, baseline engine   -- the "before"
  off_new        new engine, batch flag STRIPPED    -- the §9 inertness control
  on_new         new engine, batch flag LIVE        -- the intervention

`off_new` vs `off_baseline` proves the new Rust is inert when unused (a
CROSS-binary check). `on_new` vs `off_new` is the intervention measured on ONE
binary, so the before/after difference cannot be confounded by which binary
produced it.

HOW `--batch off` IS EXPRESSED
------------------------------
NOT by a conditional in the adapter -- that would be an agent decision in
Python (CLAUDE.md), and it would also make the "off" arm a different code path
rather than the same path with different DATA. Instead the arm points
`wave_world._CHANGE_SEED` at a temp copy of `domain_data/vision_change.json` with the
`batch` key stripped from every rule. The flag is graph DATA; the control arm
varies the data and nothing else. On the unmodified tree the strip is a no-op
(no flag is present), which is what makes the same script run on both engines.

BYTE-IDENTITY (prereg D1.3)
---------------------------
`state_record` dumps every attribute the drive phase can touch, per cell, as
EXACT `repr` floats -- never rounded, never toleranced. The prereg calls a
tolerance here metric surgery on the one gate that matters, so there is none.
`state_digest` is a sha256 over that record for compact comparison; the full
record is kept so a mismatch can be localised to a cell and an attribute
instead of merely detected.

USAGE
    python scripts/batch_apply_measure.py --arm off_baseline \
        --out results/batch_apply_off_baseline.json
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint pins its OWN tree's engine.
# MUST precede any `substrate_rs` import -- this rung ADDS RUST, so without it
# the process would measure the canonical tree's binary and the whole rung
# would be a measurement of source that did not produce it.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
import domains.wave_world as wave_world  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina, set_lat_params  # noqa: E402

# THE SAME INSTRUMENT, IMPORTED -- not reimplemented (see module docstring).
import scripts.scale_split_measure as SS  # noqa: E402

AUDIT = _native.Substrate

# Set from --keep-state-record. Off by default: see `point()`.
KEEP_STATE_RECORD = False

# Attributes the drive phase can touch, plus the downstream wave attributes
# that would reveal drift leaking out of the phase. Fixed here, before any
# comparison, so the byte-identity gate cannot be narrowed to whatever happens
# to match (§5).
CELL_ATTRS = (
    # written by the five ch_* rules
    "driven", "dstep_med", "dstep_on", "dstep_off", "dstep_sus",
    "lum_ref", "ref_n", "ref_step",
    # written by the adapter, read by the rules -- included so a corrupted
    # READ side would show up too
    "lum_raw", "lum_prev", "lum_seen",
    # downstream: the wave rules run in tick() AFTER the drive phase, so any
    # drift escaping the phase lands here
    "state", "activated_at", "last_burst",
)


def _strip_batch_seed() -> str:
    """A temp copy of `domain_data/vision_change.json` with `batch` stripped from
    every rule. The control arm varies the DATA, not the code path."""
    src = os.path.join(ROOT, "domain_data", "vision_change.json")
    with open(src) as fh:
        seed = json.load(fh)
    for r in seed.get("rules", []):
        r.pop("batch", None)
    fd, path = tempfile.mkstemp(suffix="_vision_change_nobatch.json")
    with os.fdopen(fd, "w") as fh:
        json.dump(seed, fh)
    return path


def _seed_batch_flags() -> dict:
    """What the seed ACTUALLY says, read back from the file -- so the report
    records the flag state rather than asserting it."""
    with open(os.path.join(ROOT, "domain_data", "vision_change.json")) as fh:
        seed = json.load(fh)
    return {r["name"]: bool(r.get("batch", False)) for r in seed.get("rules", [])}


def _drive_dispatch_name() -> str:
    """WHICH native method `_drive_phase` calls, read out of the source rather
    than assumed. §12.3: a claim about the path must be pinned to the code."""
    src = os.path.join(ROOT, "domains", "wave_world.py")
    with open(src) as fh:
        body = fh.read()
    for name in ("apply_rule_batch", "apply_rule_once"):
        if f"nat.{name}(idx)" in body:
            return name
    return "<unrecognised>"


def build_world(g, *, batch: bool):
    """Boot the assembled eye exactly as `scale_split_measure.counted_point`
    does for the eye arm -- same seeds, same params, same lateral wiring."""
    s, ag, _ = SS._boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)
    return s, ag, world


def state_record(s, world) -> list:
    """Every drive-touchable attribute, per cell, in a canonical order, as
    EXACT reprs. No rounding, no tolerance (prereg D1.3)."""
    out = []
    for key in sorted(world.cells):
        at = s.node(world.cells[key])["attrs"]
        out.append([list(key)] + [repr(at.get(a)) for a in CELL_ATTRS])
    return out


def state_digest(rec) -> str:
    h = hashlib.sha256()
    for row in rec:
        h.update(repr(row).encode())
    return h.hexdigest()[:16]


def point(g, *, batch: bool, ticks=None, warmup=None):
    """One grid: run the committed schedule, read the counters AND the state.

    Liveness is a HARD GATE, and the conservation asserts are the imported
    instrument's own -- a split that does not add up is a broken split."""
    ticks = SS.TICKS if ticks is None else ticks
    warmup = SS.WARMUP if warmup is None else warmup
    gc.collect()
    s, ag, world = build_world(g, batch=batch)
    frames = SS._frames(g)
    SS._run(world, warmup, g, "constant", frames)
    chk0 = SS._checksum(s, world)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    s._inner.reset_rule_costs()
    t0 = time.perf_counter()
    SS._run(world, ticks, g, "constant", frames)
    wall_ms = (time.perf_counter() - t0) / ticks * 1000.0
    AUDIT.scale_audit_set_enabled(False)
    c = SS.counters()

    chk1 = SS._checksum(s, world)
    if chk0 == chk1:
        raise SystemExit(f"FROZEN WORLD at g={g}: checksum {chk0} did not move.")
    if c["cand_enum"] == 0:
        raise SystemExit(f"DEAD INSTRUMENT at g={g}: zero candidates enumerated.")

    # §6.4 CONSERVATION -- the imported instrument's own gate.
    assert c["cand_enum_first"] + c["cand_enum_repeat"] == c["cand_enum"], (g, c)
    assert (c["cand_enum_scan"] + c["cand_enum_local"] + c["cand_enum_hinted"]
            == c["cand_enum"]), (g, c)
    assert c["where_evals_first"] + c["where_evals_repeat"] == c["where_evals"], (g, c)

    rec = state_record(s, world)
    row = {
        "grid": g, "cells": g * g, "batch": batch,
        "checksum_before": chk0, "checksum_after": chk1,
        "counters": c,
        "buckets": SS.buckets(c),
        "shares": SS.shares(c),
        "shares_reattributed_CROSS_EPOCH": SS.shares_reattributed(c),
        "cross_epoch": SS.reattributed(c, ticks=ticks),
        "state_digest": state_digest(rec),
        # The FULL record is ~3 MB per arm and is deliberately NOT committed:
        # the digest is a sha256 over the exact reprs, so it is strictly
        # stronger evidence per byte, and the DURABLE localiser is
        # `tests/test_batch_apply_migrated.py`, which does the full per-cell
        # comparison in-process and names the differing cell and attribute.
        # `--keep-state-record` restores the dump for a live investigation.
        **({"state_record": rec} if KEEP_STATE_RECORD else {}),
        # THE ONE CONTAMINABLE NUMBER. Recorded, labelled, excluded from every
        # share (prereg D3).
        "wall_ms_per_tick_CONTAMINABLE": wall_ms,
    }
    del world, s, ag
    return row


def floor_band(n_rules: int, ticks: int) -> dict:
    """THE FLOOR FALLS OUT (§13), and its band was registered BEFORE
    measurement (prereg §5): retaining the `while ...: pass` loop costs a
    second, EMPTY quiescence pass per rule that fired. Nothing chosen --
    `n_rules` is read from the seed file, `ticks` from the schedule."""
    return {"n_drive_rules_READ_FROM_SEED": n_rules, "ticks": ticks,
            "floor_low_one_pass_per_rule": n_rules * ticks,
            "floor_high_with_quiescence_pass": 2 * n_rules * ticks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["off_baseline", "off_new", "on_new"])
    ap.add_argument("--sizes", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-state-record", action="store_true",
                    help="dump the full per-cell record (~3 MB/arm) as well as "
                         "its digest; for live investigation of a mismatch")
    a = ap.parse_args()
    global KEEP_STATE_RECORD
    KEEP_STATE_RECORD = a.keep_state_record
    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else SS.SIZES

    # The `off_*` arms strip the flag from the DATA the adapter loads.
    tmp = None
    batch = a.arm == "on_new"
    if not batch:
        tmp = _strip_batch_seed()
        wave_world._CHANGE_SEED = tmp

    prov = provenance_line()
    print(prov, flush=True)
    res = {
        "arm": a.arm, "provenance": prov, "machine": SS._machine(),
        "sizes": sizes, "ticks": SS.TICKS, "warmup": SS.WARMUP,
        "bucket_definition": {k: list(v) for k, v in SS.BUCKET.items()},
        "seed_batch_flags_AS_COMMITTED": _seed_batch_flags(),
        "seed_batch_flags_AS_LOADED_BY_THIS_ARM":
            {} if batch else "<stripped: control arm>",
        "drive_phase_dispatches_to": _drive_dispatch_name(),
        "native_has_apply_rule_batch":
            hasattr(_native.Substrate, "apply_rule_batch"),
        "load_state_at_start": SS._load_state(),
        "floor_band": floor_band(SS.N_DRIVE_RULES, SS.TICKS),
    }
    print(f"  dispatch={res['drive_phase_dispatches_to']} "
          f"native_has_batch={res['native_has_apply_rule_batch']} "
          f"batch_flag_live={batch}", flush=True)

    rows = []
    for g in sizes:
        r = point(g, batch=batch)
        rows.append(r)
        b, ce = r["buckets"], r["cross_epoch"]
        print(f"  g={g:3d} cells={g*g:6d} ops={b['total']:13,d} "
              f"apply_once_calls={ce['apply_once_calls']:8,d} "
              f"digest={r['state_digest']}", flush=True)
    res["sweep"] = rows
    for key, lab in (("buckets.total", "ops_total"), ("buckets.F", "F"),
                     ("buckets.C", "C"), ("buckets.R", "R"),
                     ("counters.cand_enum", "cand_enum")):
        res[f"fit_{lab}"] = SS.fit(rows, key)
    f = res["fit_ops_total"]
    print(f"   counted-op exponent = {f['exponent']:.3f} (r2 {f['r2']:.5f})",
          flush=True)
    # P4: batching removes REPEATED scans; it does not make any scan local.
    res["hypothesis_a"] = SS.hypothesis_a(rows)
    h = res["hypothesis_a"]
    print(f"   (a) scan={h['scan_share_at_largest_grid']:.4f} "
          f"slope={h['survival_log_slope']:.4f} -> {h['verdict']}", flush=True)
    res["load_state_at_end"] = SS._load_state()

    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2, default=str)
    print("wrote", a.out, flush=True)
    if tmp:
        os.unlink(tmp)


if __name__ == "__main__":
    main()
