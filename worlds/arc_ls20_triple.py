"""arc_ls20_triple — RUNG 232000: ISOLATE THE CLEAN TRIPLE via
RESIDUAL-AFTER-EXPLAINING-THE-AVATAR.

231 fixed the EYE (event-native colour-change onset — it now SEES the colour-only
changes the luma eye missed) but did NOT isolate the owner's clean TRIPLE
(indicator flash + DESTINATION flash + exit-glyph ROTATION). The blocker: real
ls20 has NO no-op action, so every step the avatar MOVES, and the reach-frame raw
diff MIXES the avatar's own movement with the effects (~52 cells, no recognisable
rotation).

THE FIX — the held-prediction principle at whole-frame grain (NO no-op frame
needed): on the reach step, PREDICT the avatar's movement (224's object-permanence
tracker: a translate), then the RESIDUAL — the observed change MINUS the predicted
avatar change — is the SURPRISE: the indicator + destination flash + exit-glyph
rotation. The avatar is ADJACENT IN QUANTA to the cross (231 measured the
per-action jump as (5,0)/(0,5) — one 5-pixel jump is ONE quantum step), so `before`
sits one quantum hop from the cross: the footprint never pixel-merges with it, and
the reach is a single clean quantum-grain translate.

  predicted = tracker.predict(before, action)        # translate the avatar
  avatar_cells = raw_changed_cells(before, predicted) # what the move explains
  residual = raw_changed_cells(predicted, reach)      # the surprise = the effects

Cells the avatar move correctly accounts for (its new cell, its vacated cell, the
covered cross) MATCH between `predicted` and `reach` -> NOT in the residual. The
three effects were never touched by the avatar-translate -> they ARE the residual.
That is the isolation.

This module is ONLY mechanical perception + ground-truth measurement + wiring. It
reuses 224's `LiveObjectTracker` (the shift is graph data on a Percell agent; the
tracking is mechanical perception), 231's `ColourChangeEye` / `raw_changed_cells` /
`recognise_rotation` / `ground_destination_flash` (all UNCHANGED), and 227's
`_recognise_transform` (via `recognise_rotation`). Nothing hardcodes an effect
LOCATION; the regions EMERGE from the residual. No Rust — the residual is integer
cell arithmetic. Canonical `.so` `6829143c` unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 231 colour eye + ground-truth utilities + rotation reader + 229 grounder (UNCHANGED)
from worlds.arc_ls20_see import (  # noqa: E402
    raw_changed_cells, _cluster, _centroid, _dist,
    recognise_rotation, ground_destination_flash, ReachScenario,
    _FIELD, _AVATAR, _CROSS, _FLASH_A, _FLASH_B, _GLYPH_A, _rot90_cells,
)
# 224 object-permanence tracker + the Percell agent that holds the shift graph-data
from worlds.arc_ls20_percell_track import LiveObjectTracker  # noqa: E402
from worlds.arc_ls20_percell import Percell  # noqa: E402


# ============================================================================
# THE RESIDUAL — observed change MINUS predicted avatar change
# ============================================================================
def avatar_explained_cells(before, predicted):
    """The cells the avatar-translate PREDICTION accounts for = the changed cells
    between `before` and the avatar-predicted frame. This is the avatar's explained
    footprint (its vacated cell + its new cell + any cell it covered)."""
    return raw_changed_cells(before, predicted)


def residual_after_avatar(predicted, reach):
    """The held-prediction RESIDUAL: the cells the ACTUAL reach frame differs from
    the AVATAR-EXPLAINED prediction. Cells the avatar move correctly predicted match
    and drop out; the remaining changed cells are the SURPRISING effects."""
    return raw_changed_cells(predicted, reach)


def _classify_cells(before, reach, after, cells, locus, distal=8.0):
    """Cluster a cell set into regions and label each region:
      · transient — reverts on `after` (the flashes) vs persistent (the rotation);
      · distal    — > `distal` from the reach locus (destination / exit glyph) vs
        local (the indicator).
    No location hardcoded; the regions emerge from the cells."""
    before = np.asarray(before, dtype=np.int64)
    reach = np.asarray(reach, dtype=np.int64)
    after = np.asarray(after, dtype=np.int64)
    out = []
    for blob in _cluster(cells):
        reverted = 0
        for (r, c) in blob:
            if int(after[r, c]) == int(before[r, c]) and int(reach[r, c]) != int(before[r, c]):
                reverted += 1
        frac = reverted / max(1, len(blob))
        cen = _centroid(blob)
        out.append({
            "cells": blob, "centroid": cen, "size": len(blob),
            "reverted_frac": frac, "transient": frac >= 0.5,
            "dist_from_locus": _dist(cen, locus), "distal": _dist(cen, locus) > distal,
        })
    out.sort(key=lambda r: -r["size"])
    return out


def isolate_triple(before, reach, after, tracker, action, locus, *, distal=8.0,
                   predicted=None):
    """THE HEADLINE OPERATION. Predict the avatar (224 tracker), take the residual
    against the actual reach frame, cluster + classify it, and read off the three
    isolated effects. Reads NO ground truth — the scorer gates the result against
    the raw cell-diff ground truth externally.

    `predicted` (live path) supplies a PRE-COMPUTED avatar-prediction of the reach
    frame — the tracker is stateful, so the live harness predicts each step BEFORE
    observing it (the 224 precedent) and passes that frame here. When None the
    tracker predicts from `before` directly (the offline path).

    Returns a dict with:
      · residual_cells / avatar_cells / raw_gt_cells — the three cell sets;
      · residual_excludes_avatar / avatar_overlap — the confound-removal evidence;
      · indicator_flash / destination_flash / exit_rotation (+ rotation_key) — the
        structural read (a residual region of that kind exists);
      · regions — the classified residual regions.
    """
    before = np.asarray(before, dtype=np.int64)
    reach = np.asarray(reach, dtype=np.int64)
    after = np.asarray(after, dtype=np.int64)

    if predicted is None:
        predicted = tracker.predict(before, action)
    predicted = np.asarray(predicted, dtype=np.int64)
    avatar_cells = avatar_explained_cells(before, predicted)
    residual = residual_after_avatar(predicted, reach)
    raw_gt = raw_changed_cells(before, reach)

    regions = _classify_cells(before, reach, after, residual, locus, distal=distal)

    indicator = destination = rotation = False
    rotation_key = ""
    ind_region = dest_region = rot_region = None
    for reg in regions:
        if reg["transient"] and not reg["distal"]:
            indicator = True
            ind_region = ind_region or reg
        elif reg["transient"] and reg["distal"]:
            destination = True
            dest_region = dest_region or reg
        elif (not reg["transient"]) and reg["distal"]:
            key = recognise_rotation(before, after, reg)
            if key:
                rotation = True
                rotation_key = key
                rot_region = rot_region or reg

    overlap = residual & avatar_cells
    return {
        "residual_cells": residual,
        "avatar_cells": avatar_cells,
        "raw_gt_cells": raw_gt,
        "n_residual": len(residual),
        "n_avatar": len(avatar_cells),
        "n_raw_gt": len(raw_gt),
        "avatar_overlap": len(overlap),
        "residual_excludes_avatar": len(overlap) == 0,
        "indicator_flash": indicator,
        "destination_flash": destination,
        "exit_rotation": rotation,
        "rotation_key": rotation_key,
        "all_three": bool(indicator and destination and rotation),
        "regions": regions,
        "ind_region": ind_region,
        "dest_region": dest_region,
        "rot_region": rot_region,
    }


def raw_diff_isolation(before, reach, after, locus, *, distal=8.0):
    """The NO-EXPLANATION control: use the raw before->reach diff INSTEAD of the
    avatar-explained residual. It always contains the avatar cells (the confound),
    so `residual_excludes_avatar` is FALSE by construction. Returned in the same
    shape as isolate_triple for a like-for-like comparison."""
    raw = raw_changed_cells(before, reach)
    regions = _classify_cells(before, reach, after, raw, locus, distal=distal)
    return {"changed_cells": raw, "regions": regions, "n_changed": len(raw)}


# ============================================================================
# THE SYNTHETIC TRIPLE-REACH SCENARIO — avatar walks in (quanta-adjacent), reaches
# ============================================================================
class TripleReachScenario(ReachScenario):
    """A synthetic ls20-shaped reach with the avatar's APPROACH included, so 224's
    tracker can LEARN the per-action shift from clean approach transitions and then
    PREDICT the reach frame. The avatar approaches vertically in quantum-grain hops
    of `shift` cells (231 measured 5), so it is one QUANTUM HOP from the cross at
    `before` and NEVER pixel-adjacent to it (the footprint stays clean). On the
    reach step the indicator flashes (local, transient), the destination flashes
    (distal, transient), and the exit glyph rotates (distal, persistent).

    `near_miss=True` produces the reach-certification control: the avatar stops one
    quantum SHORT of the cross and the three effects do NOT fire.

    GROUND TRUTH (effect cells + the avatar cells) lives here; isolate_triple never
    reads it — the scorer gates against it.
    """

    def __init__(self, rng, n=40, shift=5, near_miss=False):
        # place the cross with room for a `shift`-hop approach above it and margins.
        self.n = n
        self.rng = rng
        self.shift = int(shift)
        self.near_miss = bool(near_miss)
        lo = 3 * self.shift + 2
        self.cr = int(rng.integers(lo, n - 6))
        self.cc = int(rng.integers(8, n - 8))
        self.locus = (float(self.cr), float(self.cc))
        # indicator: a LOCAL patch near the cross, off the avatar's vertical column
        # (so it is its own region, never merged with the avatar move).
        self.ind = [(self.cr, self.cc + 3), (self.cr, self.cc + 4)]
        # destination: a REMOTE transient patch.
        while True:
            dr = int(rng.integers(2, n - 4)); dc = int(rng.integers(2, n - 4))
            if _dist((dr, dc), self.locus) > 12:
                break
        self.dest = [(dr, dc), (dr, dc + 1), (dr + 1, dc)]
        # exit glyph: a REMOTE clearly-chiral L-tetromino that rotates (persistent).
        while True:
            gr = int(rng.integers(2, n - 6)); gc = int(rng.integers(2, n - 6))
            if _dist((gr, gc), self.locus) > 12 and _dist((gr, gc), (dr, dc)) > 6:
                break
        self.glyph = [(gr, gc, _GLYPH_A), (gr + 1, gc, _GLYPH_A),
                      (gr + 2, gc, _GLYPH_A), (gr + 2, gc + 1, _GLYPH_A)]
        self.k = int(rng.integers(1, 4))
        s = self.shift
        # approach rows (quantum hops): cr-3s, cr-2s, cr-s(=before), then reach at cr
        # (near_miss: the reach step lands cr-s -> the avatar STOPS one hop short).
        self._approach_rows = [self.cr - 3 * s, self.cr - 2 * s, self.cr - s]
        self._reach_row = (self.cr - s) if near_miss else self.cr
        # avatar-move ground truth on the reach transition (before -> reach cells).
        self.avatar_gt = {(self.cr - s, self.cc), (self._reach_row, self.cc)}
        self.effect_gt = {
            "indicator": set(self.ind),
            "destination": set(self.dest),
            "rotation": None,  # filled after we know the rotated cells
        }

    def _avatar_at(self, row):
        g = self._base()
        g[row, self.cc] = _AVATAR
        return g

    def approach(self):
        """The clean approach frames (avatar walks in, no effects). Feeding these to
        the tracker teaches the per-action shift."""
        return [self._avatar_at(r) for r in self._approach_rows]

    def frames(self):
        """(before, reach, after). before = avatar one quantum hop above the cross;
        reach = avatar on the cross (or one hop short if near_miss) + effects (unless
        near_miss); after = flashes revert, rotation persists, avatar stays."""
        s = self.shift
        before = self._avatar_at(self.cr - s)
        # reach frame
        reach = self._base()
        reach[self._reach_row, self.cc] = _AVATAR
        rot = _rot90_cells(self.glyph, self.k, self.n)
        if not self.near_miss:
            for (r, c) in self.ind:
                reach[r, c] = _FLASH_A
            for (r, c) in self.dest:
                reach[r, c] = _FLASH_B
            for (r, c, v) in self.glyph:
                reach[r, c] = _FIELD
            for (r, c, v) in rot:
                if 0 <= r < self.n and 0 <= c < self.n:
                    reach[r, c] = v
        # after frame
        after = self._base()
        after[self._reach_row, self.cc] = _AVATAR
        if not self.near_miss:
            for (r, c, v) in self.glyph:
                after[r, c] = _FIELD
            for (r, c, v) in rot:
                if 0 <= r < self.n and 0 <= c < self.n:
                    after[r, c] = v
        # the rotation's GROUND-TRUTH CHANGED cells = the symmetric difference of the
        # original and rotated glyph footprints (cells whose value actually changed;
        # cells the rotation maps to themselves do not change and are not in the diff).
        orig_cells = {(r, c) for (r, c, v) in self.glyph}
        rot_cells = {(r, c) for (r, c, v) in rot if 0 <= r < self.n and 0 <= c < self.n}
        self.effect_gt["rotation"] = orig_cells ^ rot_cells
        self.effect_gt["rotation_full"] = rot_cells
        return before, reach, after


def learn_and_isolate(scenario, action="move_down", *, distal=8.0):
    """End-to-end synthetic driver: build a Percell agent + 224 tracker, feed the
    approach so the tracker LEARNS the avatar shift (graph data), then isolate the
    triple on the reach via the residual. Returns (isolation, scenario)."""
    agent = Percell()
    tracker = LiveObjectTracker(agent)
    frames = scenario.approach()
    for i in range(len(frames) - 1):
        tracker.observe(frames[i], frames[i + 1], action)
    before, reach, after = scenario.frames()
    iso = isolate_triple(before, reach, after, tracker, action, scenario.locus, distal=distal)
    return iso, before, reach, after
