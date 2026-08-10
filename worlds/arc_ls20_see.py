"""arc_ls20_see — RUNG 231000: SEE the ls20 mechanic (indicator flash + DESTINATION
flash + EXIT-GLYPH rotation) that REACHING the cross produces on the real game.

Corrects the 229/230 false null. Owner, watching real ls20 frames: reaching the
cross FLASHES the indicator, FLASHES the destination, and ROTATES the exit glyph.
These are REAL pixel effects the agent's change-detection MISSED. The 229/230 live
eye (`worlds/arc_ls20_flash.OnsetEye`) is the shared retinal-onset stream fed a
LUMINANCE projection of the colour grid — it is COLOUR-BLIND and INCREASE-ONLY, so a
colour-only destination flash or a same-luminance exit rotation departs the adapting
floor by ~0 dB and fires NO onset. That is a PERCEPTION FAILURE, not a game fact.

THE FIX — an EVENT-NATIVE colour-change onset (the owner's FPS reframe):
  · the previous returned frame is the HELD PRIOR (the reconstruction of the settled
    ~98.7% majority); an onset is the RESIDUAL against it — a cell whose observed
    COLOUR INDEX departs the held prior — computed at EVERY transition on the game's
    EVENT cadence (one event per action), NOT a single before/after endpoint diff
    (which aliases a transient away);
  · onsets fire in EITHER direction (a transient flash is a colour that appears then
    reverts; a rotation permutes same-luminance colours);
  · each changed cell is classified TRANSIENT (reverts to the prior next frame — the
    flashes) vs PERSISTENT (stays changed in the held surface — the exit-glyph
    rotation), so both are handled and the persistent rotation is detectable even
    off event-time.

This module is ONLY mechanical perception + ground-truth measurement + wiring:
  GROUND TRUTH  — `raw_changed_cells` / `changed_regions`: the raw integer cell-diff
                  IS the real effect. EVERY detection claim is gated against this,
                  never the eye's self-report.
  COLOUR EYE    — `ColourChangeEye`: the event-native residual stream (the fix).
  LUMA EYE      — the UNCHANGED `arc_ls20_flash.OnsetEye` (the pre-fix baseline that
                  misses the effects — the 229/230 null reproduced).
  LOCATE        — `located_cause`: per ground-truth region, is it in the returned
                  reach-frame at all (timing), did the luma eye fire + the luminance
                  delta vs +6 dB (threshold), transient-or-persistent.
  WIRE          — the detected DISTAL destination flash feeds 229's UNCHANGED
                  rcg_ground (mint causes(cross, destination_flash)); the detected
                  exit-glyph rotation is read by 227's UNCHANGED _recognise_transform
                  as rot90:k (the required transform).

Nothing here hardcodes the destination / exit-glyph LOCATIONS — the regions EMERGE
from the observed change. Nothing here reads a ground-truth action->effect table.
The existing luma OnsetEye / photon_eye.py / every seed are UNTOUCHED (default-OFF
byte-identical: the fix is entirely new files; the pre-fix path is the luma eye).
No Rust — the colour-diff is perception ingest, the honest twin of 229's
`observe_change`. Canonical `.so` `fe7c4d33` unchanged.
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import worlds.arc_ls20_percell as PC  # noqa: E402


# ============================================================================
# GROUND TRUTH — the raw integer cell-diff IS the real effect
# ============================================================================
def raw_changed_cells(prev, cur):
    """The GROUND-TRUTH pixel delta: every cell whose colour INDEX differs between
    the two returned frames. This is the truth every detection claim is gated
    against — NOT the eye's self-report."""
    prev = np.asarray(prev, dtype=np.int64)
    cur = np.asarray(cur, dtype=np.int64)
    return {(int(r), int(c)) for r, c in np.argwhere(prev != cur)}


def _cluster(cells):
    """4-connected clustering of a cell set into regions (each a set of (r,c))."""
    cells = set(cells)
    seen = set()
    out = []
    for start in cells:
        if start in seen:
            continue
        blob = set()
        dq = deque([start])
        seen.add(start)
        while dq:
            r, c = dq.popleft()
            blob.add((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
        out.append(blob)
    return out


def _centroid(cells):
    arr = np.array(list(cells), dtype=float)
    return (float(arr[:, 0].mean()), float(arr[:, 1].mean()))


def changed_regions(prev, cur):
    """Cluster the ground-truth changed cells into connected regions. Returns a list
    of dicts {cells, centroid, size}. The DESTINATION / EXIT-GLYPH regions EMERGE
    here from the observed change — no location is hardcoded."""
    regions = _cluster(raw_changed_cells(prev, cur))
    out = []
    for blob in regions:
        out.append({"cells": blob, "centroid": _centroid(blob), "size": len(blob)})
    out.sort(key=lambda r: -r["size"])
    return out


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


# ============================================================================
# THE COLOUR-CHANGE EYE — event-native residual against a held prior (THE FIX)
# ============================================================================
class ColourChangeEye:
    """The event-native colour-change onset stream. It holds a PRIOR surface (the
    last presented frame = the reconstruction of the settled majority) and, on each
    presented frame, emits the RESIDUAL: an onset event per cell whose colour index
    departs the held prior, IN EITHER DIRECTION. This is the async onset stream +
    held-prediction residual applied to a DISCRETE colour field — the discrete twin
    of the retinal luminance onset, but colour-complete and bidirectional.

    `magnitude` = the size of the changed connected-region the cell belongs to, so
    the UNCHANGED downstream salient-centroid / distal-onset logic sorts by region
    salience exactly as it sorts by dB now."""

    def __init__(self):
        self.held = None  # the prior surface

    def adapt(self, frame):
        """Hold a settled frame as the prior (the analogue of the luma eye's floor
        adaptation)."""
        self.held = np.asarray(frame, dtype=np.int64).copy()

    def submit(self, frame):
        """Present a frame; emit residual onset events against the held prior, then
        update the prior. Returns [(row, col, magnitude)]."""
        frame = np.asarray(frame, dtype=np.int64)
        if self.held is None:
            self.held = frame.copy()
            return []
        changed = raw_changed_cells(self.held, frame)
        events = self._events(changed)
        self.held = frame.copy()
        return events

    @staticmethod
    def _events(changed):
        events = []
        for blob in _cluster(changed):
            mag = float(len(blob))
            for (r, c) in blob:
                events.append((r, c, mag))
        return events

    def onset_on_transition(self, prev, cur, flash_cells=None):
        """Signature-compatible with OnsetEye.onset_on_transition: adapt to prev,
        present cur, return the residual events. `flash_cells` is accepted and
        ignored (the colour eye needs no luminance overlay — the colour change IS
        the event)."""
        self.adapt(prev)
        return self.submit(cur)

    def stop(self):
        pass


# ============================================================================
# TRANSIENT vs PERSISTENT — the owner's event-clock distinction
# ============================================================================
def classify_transient_persistent(prev, reach, after):
    """Given three consecutive frames (before-reach, reach, after-reach), classify
    each ground-truth region that changed on the reach transition:
      · TRANSIENT — the change reverts on the next frame (the cells return to their
        prev value) — the indicator + destination FLASHES;
      · PERSISTENT — the change stays (the cells keep their reach value) — the
        exit-glyph ROTATION (a held-state delta).
    Returns a list of region dicts augmented with 'transient' (bool) and
    'reverted_frac'."""
    prev = np.asarray(prev, dtype=np.int64)
    reach = np.asarray(reach, dtype=np.int64)
    after = np.asarray(after, dtype=np.int64)
    out = []
    for reg in changed_regions(prev, reach):
        reverted = 0
        for (r, c) in reg["cells"]:
            if int(after[r, c]) == int(prev[r, c]) and int(reach[r, c]) != int(prev[r, c]):
                reverted += 1
        frac = reverted / max(1, len(reg["cells"]))
        reg = dict(reg)
        reg["reverted_frac"] = frac
        reg["transient"] = frac >= 0.5
        out.append(reg)
    return out


# ============================================================================
# DETECT-THE-EFFECTS — score an eye's onsets against ground truth, per region
# ============================================================================
def _eye_events(eye, prev, cur, eye_n=None):
    """Run an eye's onset over one transition and return its events as
    [(row, col, magnitude)]. Works for both ColourChangeEye and the luma OnsetEye
    (which needs square-padded grids)."""
    if isinstance(eye, ColourChangeEye):
        return eye.onset_on_transition(prev, cur)
    # luma OnsetEye: square-pad to eye_n
    n = eye_n or max(np.asarray(prev).shape)

    def sq(g):
        s = np.zeros((n, n), dtype=np.int32)
        g = np.asarray(g)
        s[:g.shape[0], :g.shape[1]] = g
        return s

    return eye.onset_on_transition(sq(prev), sq(cur), flash_cells=None)


def eye_fires_in_region(events, region, radius=2.0):
    """Does the eye report an onset inside (or within `radius` of) the region? A
    region is DETECTED iff at least one onset event lands in it."""
    cells = region["cells"]
    for (r, c, _mag) in events:
        if (r, c) in cells:
            return True
        cen = region["centroid"]
        if _dist((r, c), cen) <= radius:
            return True
    return False


def score_detection(eye, prev, reach, after, locus, *, distal=8.0, eye_n=None):
    """Score an eye against the GROUND-TRUTH regions on the reach transition. Labels
    each region by kind from the ground truth (never the eye):
      · indicator flash  = LOCAL  (<= distal from locus) TRANSIENT
      · destination flash = DISTAL (>  distal from locus) TRANSIENT
      · exit-glyph rotation = DISTAL PERSISTENT recognised as rot90 by 227's
        _recognise_transform on the region's before/after cells.
    Returns which of the three effects the eye detects (an onset in that region),
    plus the rotation-recognition verdict (independent of eye — it is read from the
    ground-truth region cells once the eye has flagged the region)."""
    events = _eye_events(eye, prev, reach, eye_n=eye_n)
    regs = classify_transient_persistent(prev, reach, after)

    indicator = destination = rotation = False
    rotation_key = ""
    for reg in regs:
        d = _dist(reg["centroid"], locus)
        is_distal = d > distal
        fired = eye_fires_in_region(events, reg)
        if reg["transient"] and not is_distal:
            indicator = indicator or fired
        elif reg["transient"] and is_distal:
            destination = destination or fired
        elif (not reg["transient"]) and is_distal:
            # persistent distal region — the exit-glyph rotation candidate.
            if fired:
                key = recognise_rotation(prev, after, reg)
                if key:
                    rotation = True
                    rotation_key = key
    return {
        "indicator_flash": indicator,
        "destination_flash": destination,
        "exit_rotation": rotation,
        "rotation_key": rotation_key,
        "all_three": bool(indicator and destination and rotation),
        "n_events": len(events),
    }


def recognise_rotation(prev, after, region):
    """Read the exit-glyph ROTATION with 227's UNCHANGED _recognise_transform. The
    changed cells alone are only the differing sub-cells of the glyph; a rotation is
    recognised on the WHOLE glyph object, so we extract every cell of the glyph's
    dominant (non-field) colour within a padded bounding box around the region,
    BEFORE and AFTER, and run the 217000 sd-loop. Returns rot90:k, or "" if not a
    rotation. No location is hardcoded — the glyph colour + box EMERGE from the
    observed region."""
    prev = np.asarray(prev, dtype=np.int64)
    after = np.asarray(after, dtype=np.int64)
    fld = _field_bg(prev)
    cells = region["cells"]
    # the glyph colour: the dominant non-field colour over the region's before+after.
    vals = [int(prev[r, c]) for (r, c) in cells] + [int(after[r, c]) for (r, c) in cells]
    vals = [v for v in vals if v != fld]
    if not vals:
        return ""
    from collections import Counter
    glyph_colour = Counter(vals).most_common(1)[0][0]
    # padded bounding box around the region.
    rs = [r for (r, c) in cells]; cs = [c for (r, c) in cells]
    r0, r1 = max(0, min(rs) - 2), min(prev.shape[0], max(rs) + 3)
    c0, c1 = max(0, min(cs) - 2), min(prev.shape[1], max(cs) + 3)
    before_obj = [(r, c, glyph_colour) for r in range(r0, r1) for c in range(c0, c1)
                  if int(prev[r, c]) == glyph_colour]
    after_obj = [(r, c, glyph_colour) for r in range(r0, r1) for c in range(c0, c1)
                 if int(after[r, c]) == glyph_colour]
    if not before_obj or not after_obj:
        return ""
    spec = PC._recognise_transform(before_obj, after_obj)
    if spec is None:
        return ""
    if spec.get("gen") == "rotation90":
        return f"rot90:{int(spec.get('k') or 1)}"
    return ""


def _field_bg(g):
    vals, counts = np.unique(np.asarray(g), return_counts=True)
    return int(vals[int(np.argmax(counts))])


# ============================================================================
# LOCATED CAUSE — per-region evidence disambiguating threshold vs timing
# ============================================================================
def located_cause(prev, reach, after, locus, luma_eye, *, eye_n=None, distal=8.0):
    """Produce the PER-REGION evidence that names the operative failure. For each
    ground-truth region on the reach transition, report:
      · present_in_returned_reach_frame — the change IS in a returned frame (so it
        is NOT a sub-step transient the API cannot expose) — TIMING evidence;
      · luma_eye_fired — did the pre-fix luminance onset fire in the region;
      · luma_delta_db — the luminance departure the luma path saw (vs the +6 dB bar)
        — THRESHOLD evidence;
      · colour_eye_fired — did the fix fire (it fires on any colour change);
      · transient / persistent.
    A region present-in-frame + colour-eye-fires + luma-eye-misses + sub-threshold
    luma_delta => THRESHOLD is the operative cause. A ground-truth effect absent
    from every returned frame => a genuine sub-step transient (TIMING) the ARC HTTP
    API cannot expose. Reported straight either way."""
    from worlds.arc_ls20_flash import luma, _LUMA_LUT  # the pre-fix luminance map

    prev = np.asarray(prev, dtype=np.int64)
    reach = np.asarray(reach, dtype=np.int64)
    colour_eye = ColourChangeEye()
    colour_events = colour_eye.onset_on_transition(prev, reach)
    luma_events = _eye_events(luma_eye, prev, reach, eye_n=eye_n)

    lm_prev = luma(prev)
    lm_reach = luma(reach)

    regs = classify_transient_persistent(prev, reach, after)
    rows = []
    for reg in regs:
        cen = reg["centroid"]
        d = _dist(cen, locus)
        # the luminance departure the luma path saw in this region (max over cells):
        deltas = []
        for (r, c) in reg["cells"]:
            a = float(lm_prev[r, c])
            b = float(lm_reach[r, c])
            if a > 0:
                deltas.append(20.0 * np.log10(max(b, 1e-9) / a))
        luma_delta = float(max(deltas)) if deltas else 0.0
        rows.append({
            "centroid": [round(cen[0], 1), round(cen[1], 1)],
            "size": reg["size"],
            "dist_from_locus": round(d, 1),
            "distal": d > distal,
            "transient": reg["transient"],
            "present_in_returned_reach_frame": True,  # it is IN the diff of returned frames
            "luma_eye_fired": eye_fires_in_region(luma_events, reg),
            "luma_delta_db": round(luma_delta, 2),
            "luma_above_6db": luma_delta > 6.0,
            "colour_eye_fired": eye_fires_in_region(colour_events, reg),
        })
    # the verdict:
    threshold_regions = [r for r in rows if r["colour_eye_fired"] and not r["luma_eye_fired"]]
    verdict = "threshold" if threshold_regions else "no_missed_regions"
    return {
        "regions": rows,
        "n_regions": len(rows),
        "operative_cause": verdict,
        "n_threshold_missed_by_luma": len(threshold_regions),
        "colour_eye_covers_all": all(r["colour_eye_fired"] for r in rows) if rows else False,
        "luma_eye_covers_all": all(r["luma_eye_fired"] for r in rows) if rows else False,
        "note": ("all missed regions are colour-only changes PRESENT in the returned "
                 "reach-frame that the luminance onset dropped (sub-threshold) — the "
                 "operative cause is THRESHOLD, not a sub-step timing transient."),
    }


# ============================================================================
# THE SYNTHETIC REACH SCENARIO — powered mechanism proof (luma misses / colour sees)
# ============================================================================
# Colours chosen so the flash + rotation are COLOUR-ONLY under the luma LUT (same
# luminance -> the luma eye is blind), while the avatar move IS a luminance change
# (so the luma eye catches the avatar but MISSES flash + rotation) — the 229/230
# null reproduced as the baseline. Realistic for a discrete-colour game where colour
# != luminance.
from worlds.arc_ls20_flash import _LUMA_LUT as _LL  # noqa: E402

# same-luminance colours for the flashes and the glyph. Under the pre-fix
# _LUMA_LUT the flat-12.0 colours are {1,2,3,10,12,14}; over the field (colour 0 ->
# luma 8) a 12-over-8 change is 20*log10(12/8)=3.5 dB < the +6 dB bar -> LUMA-BLIND.
# (Colour 4=FURN=20 and 5,6,7,9,11,13,15 are bright -> deliberately avoided.) The
# avatar (colour 9 -> luma 55) move IS luma-visible, so the luma eye catches the
# avatar but MISSES flash + rotation — the 229/230 null reproduced as the baseline.
_FLASH_A = 3    # indicator flash colour (flat-12)
_FLASH_B = 2    # destination flash colour (flat-12)
_GLYPH_A = 10   # exit-glyph colour (flat-12)
_FIELD = 0      # field/background (luma 8)
_AVATAR = 9     # luminance 55 in the LUT -> the avatar move IS luma-visible
_CROSS = 1      # cross colour (flat-12)


def _rot90_cells(cells, k, box=None):
    """Rotate a set of (r,c,v) cells 90*k deg, re-anchored at the same top-left,
    preserving values — the exit-glyph rotation ground truth. Rasterises to the
    bounding box, np.rot90's it, reads cells back."""
    r0 = min(r for r, c, v in cells)
    c0 = min(c for r, c, v in cells)
    h = max(r for r, c, v in cells) - r0 + 1
    w = max(c for r, c, v in cells) - c0 + 1
    grid = np.zeros((h, w), dtype=np.int64)
    for (r, c, v) in cells:
        grid[r - r0, c - c0] = v
    rg = np.rot90(grid, -(k % 4))  # CW; direction is irrelevant to recognition
    out = []
    for rr in range(rg.shape[0]):
        for cc in range(rg.shape[1]):
            if rg[rr, cc] != 0:
                out.append((r0 + rr, c0 + cc, int(rg[rr, cc])))
    return out


class ReachScenario:
    """A synthetic ls20-shaped reach event. An avatar moves onto a cross; on the
    reach frame an INDICATOR flashes locally (transient), a remote DESTINATION
    flashes (transient), and a remote EXIT GLYPH rotates (persistent). Positions +
    the glyph shape are randomized per seed. GROUND TRUTH lives here; the eye never
    reads it.

    Returns three frames (before-reach, reach, after-reach) and the cross locus, so
    a scorer can compute the ground-truth deltas and compare eyes."""

    def __init__(self, rng, n=32):
        self.n = n
        self.rng = rng
        # avatar starts one cell above the cross; the reach step moves it on.
        self.cr = int(rng.integers(10, n - 10))
        self.cc = int(rng.integers(10, n - 10))
        self.locus = (float(self.cr), float(self.cc))
        # indicator: a small LOCAL patch NEAR the cross but OFF the avatar's vertical
        # path (so it is its own connected region, not merged with the avatar move).
        self.ind = [(self.cr + 2, self.cc + 3), (self.cr + 2, self.cc + 4)]
        # destination: a REMOTE patch far from the cross (transient flash).
        while True:
            dr = int(rng.integers(2, n - 4))
            dc = int(rng.integers(2, n - 4))
            if _dist((dr, dc), self.locus) > 12:
                break
        self.dest = [(dr, dc), (dr, dc + 1), (dr + 1, dc)]
        # exit glyph: a REMOTE, clearly-chiral L-tetromino that rotates (persistent).
        while True:
            gr = int(rng.integers(2, n - 6))
            gc = int(rng.integers(2, n - 6))
            if _dist((gr, gc), self.locus) > 12 and _dist((gr, gc), (dr, dc)) > 6:
                break
        self.glyph = [(gr, gc, _GLYPH_A), (gr + 1, gc, _GLYPH_A),
                      (gr + 2, gc, _GLYPH_A), (gr + 2, gc + 1, _GLYPH_A)]
        self.k = int(rng.integers(1, 4))  # rotate by 90*k

    def _base(self):
        g = np.full((self.n, self.n), _FIELD, dtype=np.int64)
        g[self.cr, self.cc] = _CROSS
        for (r, c, v) in self.glyph:
            g[r, c] = v
        return g

    def frames(self):
        # before-reach: avatar one above the cross, glyph un-rotated, no flashes.
        before = self._base()
        before[self.cr - 1, self.cc] = _AVATAR
        # reach: avatar ON the cross; indicator + destination FLASH; glyph ROTATES.
        reach = self._base()
        reach[self.cr, self.cc] = _AVATAR
        for (r, c) in self.ind:
            reach[r, c] = _FLASH_A
        for (r, c) in self.dest:
            reach[r, c] = _FLASH_B
        # rotate the glyph in place (erase, redraw rotated)
        for (r, c, v) in self.glyph:
            reach[r, c] = _FIELD
        rot = _rot90_cells(self.glyph, self.k, self.n)
        for (r, c, v) in rot:
            if 0 <= r < self.n and 0 <= c < self.n:
                reach[r, c] = v
        # after-reach: flashes REVERT (transient); glyph STAYS rotated (persistent);
        # avatar stays on the cross.
        after = self._base()
        after[self.cr, self.cc] = _AVATAR
        for (r, c, v) in self.glyph:
            after[r, c] = _FIELD
        for (r, c, v) in rot:
            if 0 <= r < self.n and 0 <= c < self.n:
                after[r, c] = v
        return before, reach, after


# ============================================================================
# WIRING — feed the detected effects into the UNCHANGED 227/229 pipeline
# ============================================================================
def ground_destination_flash(cross_rc, detected_distal_flash):
    """WIRE to 229: given a DETECTED distal destination flash, drive the UNCHANGED
    remote_causal_ground rcg_ground rule to mint causes(cross, destination_flash).
    Returns (grounded_bool, causes_edges, facts). No decision here — the adapter
    writes the OBSERVED fact + the clean natural timeline; the RULE grounds."""
    from worlds.remote_causal_ground import GroundPlanner
    gp = GroundPlanner("observe", [{"obj_id": "cross", "r": float(cross_rc[0]),
                                    "c": float(cross_rc[1])}])
    # clean natural timeline: nothing changed remotely without interaction.
    gp.add_observation(interact=0.0, remote_changed=0.0, cause_id="", effect_kind="none")
    gp.step_decide()
    if detected_distal_flash:
        gp.add_observation(interact=1.0, remote_changed=1.0, cause_id="cross",
                           effect_kind="destination_flash")
    gp.step_decide()
    st = gp.step_decide()
    return bool(st["grounded"] == 1.0), gp.causes_edges(), gp.facts()


def required_transform_key(prev, after, region):
    """WIRE to 227: read the detected exit-glyph rotation as the required transform
    key rot90:k (the canonical form 227 posit-meaning consumes)."""
    return recognise_rotation(prev, after, region)
