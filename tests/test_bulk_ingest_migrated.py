"""BULK PyO3 LUMINANCE INGEST — the durable gate.

Pre-registration: `VISION_SCALE_BULK_INGEST_PREREG.md` (block 132000-132999).
Results: `VISION_SCALE_BULK_INGEST_RESULTS.md`.

WHAT THIS GUARDS. 131000 proved the O(N^2) drive wall is spent (batched drive
LINEAR) and NAMED the residual as the linear per-cell constant (16.8 us/cell),
of which the adapter's per-cell luminance write is a batchable part. This rung
replaces that per-cell Python->Rust loop (`node()` + 3x`set_attr` per cell) with
ONE whole-field crossing (`set_attr_each`), gated on an opt-in `bulk_ingest`
flag (DEFAULT OFF, the `detect_cycles` precedent). The claim is that the bulk
path is EXACT — it removes crossings without moving one bit of state.

Three halves, and this file gates all three:

  1. CORRECTNESS — the per-cell state the drive phase produces must be BITWISE
     identical with `bulk_ingest` on and off, on a battery of grids AND with a
     frame smaller than the grid (the in-bounds subset path). Compared by exact
     `repr`, never toleranced (a tolerance here would be PROTOCOL §5 metric
     surgery on the one check that matters).
  2. THE WIRING — `set_attr_each` must exist on the native substrate and the
     adapter must actually call it under the flag; without it the bulk path is
     inert or absent.
  3. THE DEFAULT — an un-opted world must take the committed per-cell path
     (PROTOCOL §9: defaults preserve committed results).
"""
from __future__ import annotations

import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytest.importorskip("substrate_rs")

import domains.seed_registry  # noqa: F401,E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina, set_lat_params  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from substrate_rs import _native  # noqa: E402

# Every attribute the drive phase can touch, plus the downstream wave attributes
# that would reveal drift ESCAPING the phase. Fixed here so the comparison
# cannot later be narrowed to whatever happens to match (§5).
CELL_ATTRS = (
    "driven", "dstep_med", "dstep_on", "dstep_off", "dstep_sus",
    "lum_ref", "ref_n", "ref_step",
    "lum_raw", "lum_prev", "lum_seen",
    "state", "activated_at", "last_burst",
)

TICKS = 8


def _frames(g, n=6, seed=11, crop=None):
    """A smooth drifting field — the same construction the measurement uses.
    `crop` (h, w) yields frames SMALLER than the grid, to exercise the
    in-bounds subset path (`r < frame.shape[0] and c < frame.shape[1]`)."""
    rng = np.random.default_rng(seed)
    base = rng.random((g + n + 2, g + n + 2)).astype(np.float32)
    for _ in range(6):
        base = (base + np.roll(base, 1, 0) + np.roll(base, -1, 0)
                + np.roll(base, 1, 1) + np.roll(base, -1, 1)) / 5.0
    h, w = (g, g) if crop is None else crop
    return [np.ascontiguousarray(base[i:i + h, i:i + w]) for i in range(n)]


def _run(g, *, bulk, ticks=TICKS, crop=None):
    """Boot the assembled eye, set the ingest arm via the flag, drive it, and
    return the exact per-cell state record."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    world.bulk_ingest = bool(bulk)
    add_lateral_retina(world)
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)

    frames = _frames(g, crop=crop)
    for i in range(ticks):
        world.step(ignite_k=1 if i % 5 == 0 else 0, frame=frames[i % len(frames)])

    rec = []
    for key in sorted(world.cells):
        at = s.node(world.cells[key])["attrs"]
        rec.append((key, tuple(repr(at.get(a)) for a in CELL_ATTRS)))
    return rec


def _diff(on_rec, off_rec):
    assert len(on_rec) == len(off_rec)
    diffs = []
    for (k1, v1), (k2, v2) in zip(on_rec, off_rec):
        assert k1 == k2
        if v1 != v2:
            diffs.append((k1, [(a, x, y) for a, x, y in zip(CELL_ATTRS, v1, v2)
                               if x != y]))
    return diffs


# --- 2. THE WIRING -----------------------------------------------------------

def test_native_exposes_set_attr_each():
    """Without this method the bulk path cannot run — `set_attr_many` is uniform
    BY CONSTRUCTION and cannot write a different luminance per cell."""
    assert hasattr(_native.Substrate, "set_attr_each"), (
        "engine predates set_attr_each — rebuild via scripts/engine_build.sh")


def test_drive_uses_set_attr_each_under_the_flag():
    with open(os.path.join(ROOT, "domains", "wave_world.py")) as fh:
        body = fh.read()
    assert "self.s.set_attr_each(" in body, (
        "drive() no longer calls set_attr_each — the bulk ingest is silently "
        "reverted and every number in VISION_SCALE_BULK_INGEST_RESULTS.md "
        "would be unreproducible")
    assert 'getattr(self, "bulk_ingest", False)' in body, (
        "the bulk path is no longer gated on the opt-in flag — §9 defaults")


# --- 1. CORRECTNESS ----------------------------------------------------------

@pytest.mark.parametrize("g", [8, 12, 16])
def test_bulk_and_percell_produce_bitwise_identical_state(g):
    """THE GATE. The bulk path reorders the luminance write from per-cell-
    interleaved (lum_prev, lum_raw, lum_seen per cell) to per-key-bulk (all
    lum_prev, then all lum_raw, then all lum_seen). Byte-identity holds because
    the three keys are distinct, no cell reads another cell, and the reads
    gather the INITIAL values before any write. This measures it."""
    on = _run(g, bulk=True)
    off = _run(g, bulk=False)
    diffs = _diff(on, off)
    assert not diffs, (
        f"{len(diffs)} cell(s) differ between bulk and per-cell ingest at "
        f"g={g}. The speedup is NOT byte-identical and MUST NOT ship. "
        f"First 3: {diffs[:3]}")


def test_the_luminance_carry_is_exact():
    """lum_prev <- last frame's lum_raw, lum_seen <- count+1: the read-modify-
    write chain that would break FIRST if the cell<->value alignment failed.
    Asserted separately so a failure names the mechanism, not a cell count."""
    on = _run(12, bulk=True)
    off = _run(12, bulk=False)
    i_prev = CELL_ATTRS.index("lum_prev")
    i_raw = CELL_ATTRS.index("lum_raw")
    i_seen = CELL_ATTRS.index("lum_seen")
    for (k, v1), (_, v2) in zip(on, off):
        assert v1[i_prev] == v2[i_prev], (k, "lum_prev", v1[i_prev], v2[i_prev])
        assert v1[i_raw] == v2[i_raw], (k, "lum_raw", v1[i_raw], v2[i_raw])
        assert v1[i_seen] == v2[i_seen], (k, "lum_seen", v1[i_seen], v2[i_seen])


def test_bulk_and_percell_identical_when_frame_smaller_than_grid():
    """THE IN-BOUNDS SUBSET. The bulk path must replicate the per-cell guard
    `r < frame.shape[0] and c < frame.shape[1]` — cells outside the frame get
    NO write on either arm. A frame cropped below the grid exercises exactly
    the subset logic that a square frame never touches."""
    on = _run(16, bulk=True, crop=(10, 13))
    off = _run(16, bulk=False, crop=(10, 13))
    diffs = _diff(on, off)
    assert not diffs, (
        f"{len(diffs)} cell(s) differ with a cropped (10x13) frame on a 16x16 "
        f"grid — the bulk in-bounds subset diverges from the per-cell guard. "
        f"First 3: {diffs[:3]}")


# --- 3. THE DEFAULT (§9) -----------------------------------------------------

def test_default_world_takes_the_percell_path():
    """A world that never sets `bulk_ingest` must be byte-identical to the
    explicit per-cell arm — that is what makes §9 structural: the committed
    default is untouched."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    world = WaveWorld(s, h=12, w=12, seed=0, fovea_radius=0)
    assert getattr(world, "bulk_ingest", "UNSET") == "UNSET", (
        "a fresh WaveWorld must NOT carry bulk_ingest — the default is the "
        "committed per-cell path, opted into only by an explicit assignment")
    add_lateral_retina(world)
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)
    frames = _frames(12)
    for i in range(TICKS):
        world.step(ignite_k=1 if i % 5 == 0 else 0, frame=frames[i % len(frames)])
    rec = []
    for key in sorted(world.cells):
        at = s.node(world.cells[key])["attrs"]
        rec.append((key, tuple(repr(at.get(a)) for a in CELL_ATTRS)))
    off = _run(12, bulk=False)
    assert _diff(rec, off) == []
