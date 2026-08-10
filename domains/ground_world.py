"""ground_world — THE BLIND SPOT world adapter (a GROUNDED retinal field).

ARCHITECTURE (CLAUDE.md). A WORLD ADAPTER and nothing else. It does exactly the
mechanical things a world adapter may:

  1. LAY OUT the anatomy — mark which RetinaCells are SENSED (have a
     photoreceptor) and which fall in the BLIND SPOT (the optic disc — no
     photoreceptors, no data ever). The blind-spot geometry (centre offset from
     the fovea, radius) is a STRUCTURAL CONSTRUCTION PARAMETER of the eye, named
     as a knob (PROTOCOL §13): the optic nerve must exit somewhere. What FALLS
     OUT is the FILLING, which is the rules' business.
  2. STATE OBSERVATIONS — for a sensed cell, write the photon it receives
     (`gobs`) and adopt it as a directly grounded belief (gbel=gobs, gfilled=1,
     gconf=1). For a blind cell, write NOTHING (no data). Clearing a blind cell's
     stale fill before a new observation is mechanical bookkeeping.
  3. ADVANCE THE GROUNDING — bump the clock and call `run_rules` (`s.tick`, all
     bindings per sweep — the O(N) path), so the grounding rules FILL the hole.
     NEVER `apply_rule_once` per binding (the O(N^2) drive PROTOCOL condemns).
  4. READ BACK — pure queries (the belief field, the raw sensor, filled/conf/
     ambig masks).

NO DECISIONS. There is no `if ground`, no `if interp` in this file: every fill
decision is a RULE in `seeds/vision_ground.json` reading `GroundParams`
(PROTOCOL §0). A source-grep gate enforces it.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from domains.wave_world import WaveWorld


# --------------------------------------------------------------------------- #
#  1. ANATOMY — the sensor, and the structural hole in it
# --------------------------------------------------------------------------- #
def add_grounded_field(world: WaveWorld, *, blind_center: tuple[int, int],
                       blind_radius: float, fovea: Optional[tuple[int, int]] = None
                       ) -> dict:
    """Give every RetinaCell a grounded-belief record, and carve the blind spot.

    `blind_center` (row, col) and `blind_radius` are the STRUCTURAL construction
    parameters of the optic disc — a named design knob, not a fall-out. A cell is
    BLIND (gsensed=0) iff it lies within `blind_radius` of `blind_center`.

    Returns `{"cells": {(r,c): nid}, "blind": set((r,c)), "fovea": (r,c)}`.
    """
    s = world.s
    br, bc = blind_center
    fovea = fovea or (world.h // 2, world.w // 2)
    blind: set[tuple[int, int]] = set()
    for (r, c), n in world.cells.items():
        d2 = (r - br) ** 2 + (c - bc) ** 2
        is_blind = d2 <= blind_radius * blind_radius
        if is_blind:
            blind.add((r, c))
        # The belief record. Sensed cells default ungrounded until an observation;
        # blind cells are never grounded directly (no gobs is ever written).
        s.set_attr(n, "gsensed", 0.0 if is_blind else 1.0)
        s.set_attr(n, "gobs", 0.0)
        s.set_attr(n, "gbel", 0.0)
        s.set_attr(n, "gfilled", 0.0)
        s.set_attr(n, "gconf", 0.0)
        s.set_attr(n, "gcont", 0.0)
        s.set_attr(n, "gcax", 0.0)
        s.set_attr(n, "gambig", 0.0)
        s.set_attr(n, "glabel_step", -999.0)
    return {"cells": dict(world.cells), "blind": blind, "fovea": fovea}


def set_ground_params(world: WaveWorld, **kw) -> None:
    """Blind-write floats onto the GroundParams node. Mechanical: this function
    does not read, branch on, or interpret any flag — the RULES do."""
    for p in world.s.nodes("GroundParams"):
        for k, v in kw.items():
            world.s.set_attr(p, k, float(v))


# --------------------------------------------------------------------------- #
#  2 + 3. OBSERVE then GROUND
# --------------------------------------------------------------------------- #
def present(world: WaveWorld, anat: dict, frame: np.ndarray, *,
            eye_offset: tuple[int, int] = (0, 0), max_sweeps: int = 200_000) -> None:
    """State the frame the eye sees THIS fixation, then let the rules ground it.

    `eye_offset` (dr, dc) shifts the scene under the eye — a saccade/drift. The
    photoreceptor at retinal (r, c) samples world (r+dr, c+dc). The blind spot is
    fixed to the RETINA, so a saccade moves the WORLD past it: a thing hidden in
    the blind spot at one fixation is sensed at another. Mechanical: `world(...)`
    is the scene; nothing here decides what is seen.

    Every step: CLEAR each blind cell's stale fill (bookkeeping), WRITE each
    sensed cell's observation as a directly grounded belief, bump the clock, and
    run the grounding rules to a fixpoint via `run_rules` (NOT apply_rule_once).
    """
    s = world.s
    dr, dc = eye_offset
    # Bump the clock so gr_label re-labels this fixation (once per step).
    st = float(s.node(world.retina)["attrs"]["step"]) + 1.0
    s.set_attr(world.retina, "step", st)
    H, W = frame.shape
    for (r, c), n in anat["cells"].items():
        if (r, c) in anat["blind"]:
            # No data. Clear any stale fill so this fixation re-grounds fresh.
            s.set_attr(n, "gfilled", 0.0)
            s.set_attr(n, "gbel", 0.0)
            s.set_attr(n, "gconf", 0.0)
            s.set_attr(n, "gcont", 0.0)
            s.set_attr(n, "gcax", 0.0)
            s.set_attr(n, "gambig", 0.0)
            continue
        wr, wc = r + dr, c + dc
        v = float(frame[wr, wc]) if (0 <= wr < H and 0 <= wc < W) else 0.0
        s.set_attr(n, "gobs", v)
        s.set_attr(n, "gbel", v)          # a sensed cell is grounded directly ...
        s.set_attr(n, "gfilled", 1.0)     # ... it is filled with confidence 1 ...
        s.set_attr(n, "gconf", 1.0)       # ... by the observation itself.
        s.set_attr(n, "gcont", 0.0)       # gr_label decides the contour label.
        s.set_attr(n, "gcax", 0.0)
        s.set_attr(n, "gambig", 0.0)
    # THE GROUNDING: run_rules to a fixpoint. All bindings per sweep (O(N)); the
    # blind-spot diameter is a fixed anatomical constant, so the sweep count does
    # not grow with the grid — total O(N). NEVER the O(N^2) apply_rule_once drive.
    s.tick(max_sweeps)


# --------------------------------------------------------------------------- #
#  4. READ-OUT (pure query)
# --------------------------------------------------------------------------- #
def belief_field(world: WaveWorld, anat: dict) -> np.ndarray:
    """The (h, w) grounded belief `gbel` — what the field HOLDS at each location,
    sensed or filled. Pure query."""
    a = np.full((world.h, world.w), np.nan, np.float64)
    for (r, c), n in anat["cells"].items():
        a[r, c] = float(world.s.node(n)["attrs"]["gbel"])
    return a


def raw_sensor(world: WaveWorld, anat: dict) -> np.ndarray:
    """What the RAW SENSOR reports: the observation at sensed cells, NaN in the
    blind spot (no data). This is the sample array — the thing the grounded field
    is NOT. Pure query."""
    a = np.full((world.h, world.w), np.nan, np.float64)
    for (r, c), n in anat["cells"].items():
        if (r, c) not in anat["blind"]:
            a[r, c] = float(world.s.node(n)["attrs"]["gobs"])
    return a


def _mask(world: WaveWorld, anat: dict, key: str) -> np.ndarray:
    a = np.zeros((world.h, world.w), np.float64)
    for (r, c), n in anat["cells"].items():
        a[r, c] = float(world.s.node(n)["attrs"][key])
    return a


def filled(world, anat): return _mask(world, anat, "gfilled")
def conf(world, anat): return _mask(world, anat, "gconf")
def ambig(world, anat): return _mask(world, anat, "gambig")
def contour(world, anat): return _mask(world, anat, "gcont")


def blind_mask(world: WaveWorld, anat: dict) -> np.ndarray:
    a = np.zeros((world.h, world.w), np.float64)
    for (r, c) in anat["blind"]:
        a[r, c] = 1.0
    return a


__all__ = ["add_grounded_field", "set_ground_params", "present", "belief_field",
           "raw_sensor", "filled", "conf", "ambig", "contour", "blind_mask"]
