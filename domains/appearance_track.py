"""APPEARANCE-TRACKED ASSOCIATION — a mechanical tracker-association SENSOR
(block 151000-151999).

A carved region is chained to a prior one by its GREY APPEARANCE (normalized
cross-correlation of the grey patch at the region's INTEGER centroid), robust to
the motion-field flicker and mask-shape wobble that births spurious new Region
ids and fragments a real moving object into short runs. This is mechanical
PERCEPTION — a tracker association criterion, exactly like the overlap /
nearest-centroid / velocity-predictive phases already inside
`segment_motion_and_track` — NOT an agent decision:

  * it reads ONLY pixel patches + the carve's own centroid/count (no graph
    state, no `if` over graph state);
  * the association is `argmax NCC` — it FALLS OUT (best-correlation), there is
    NO tuned acceptance threshold (§13). The one declared residual is the patch
    half-size `HALF` (a resolution residual, like `block` / `S`).

GATED, DEFAULT OFF, BYTE-IDENTICAL WHEN OFF: `longest_run(track, enabled=False)`
reproduces the existing "largest non-ground region, chained by Rust Region id"
trajectory EXACTLY (it simply defers to `_id_chain_largest`). The appearance
path runs only under `enabled=True`.

INVARIANT (§ frame/continuum): patches are read at INTEGER centroids
(`int(round(cy))`, `int(round(cx))`); NCC is a CROSS-FRAME comparison — it lives
in `Hom(frame, frame)`, the only place a continuous quantity is admissible, and
its inputs are stepped pixel grids. NO float is ever written into an in-frame
coordinate here. The tracked run carries the carve's own `cy/cx` unchanged; they
reach any order-N witness only via `round()`, exactly as the existing pipeline.
"""
from __future__ import annotations

import numpy as np

# ── DECLARED RESOLUTION RESIDUAL (§13) — patch half-size in cells. Like
#    `block`/`S`: it sets the grain of the appearance template, it is NOT tuned
#    against any acceptance threshold (there is none — association is argmax). ──
HALF = 3


def grey_patch(frame: np.ndarray, cy: float, cx: float, half: int = HALF) -> np.ndarray:
    """A fixed `(2*half+1)^2` grey patch centred at the INTEGER centroid
    (round(cy), round(cx)), zero-padded at the frame edge (background is black).
    Reads pixels only; the centre is an integer in-frame coordinate."""
    r = int(round(cy))
    c = int(round(cx))
    h, w = frame.shape
    out = np.zeros((2 * half + 1, 2 * half + 1), dtype=np.float64)
    for i, rr in enumerate(range(r - half, r + half + 1)):
        if 0 <= rr < h:
            for j, cc in enumerate(range(c - half, c + half + 1)):
                if 0 <= cc < w:
                    out[i, j] = float(frame[rr, cc])
    return out


def ncc(a: np.ndarray, b: np.ndarray) -> float:
    """Zero-mean, unit-norm cross-correlation of two equal-shape grey patches.
    A cross-frame comparison (continuous, admissible in Hom(frame,frame)).
    Returns 0.0 when either patch has no variance (nothing to correlate)."""
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _largest(regs):
    return max(regs, key=lambda r: r["count"]) if regs else None


def _id_chain_largest(track):
    """The EXISTING trajectory: per frame the largest non-ground region, chained
    by adjacent Region-id equality; longest such run. Byte-identical to
    `subcell_crossframe_measure.longest_run_indexed(carve_track_indexed(...))`
    when `track` is that per-frame (fi, largest|None) list."""
    best, cur = [], []
    for fi, b in track:
        if b is None:
            cur = []
            continue
        rec = {"fi": fi, "cy": b["cy"], "cx": b["cx"], "count": b["count"], "id": b["id"]}
        if cur and rec["id"] == cur[-1]["id"]:
            cur.append(rec)
        else:
            cur = [rec]
        if len(cur) > len(best):
            best = list(cur)
    return best


def _appearance_run(regions_per_frame, grey_frames, half):
    """Chain the tracked object across frames by APPEARANCE. Seed the template
    from the first frame's largest non-ground region; each subsequent frame pick
    the non-ground region whose grey patch has MAX NCC with the running template
    (argmax — no threshold); drift the template to the chosen patch. A frame with
    NO non-ground region breaks the run. Returns the longest consecutive run."""
    best, cur = [], []
    template = None
    for fi, regs in regions_per_frame:
        if not regs:
            cur = []
            template = None
            continue
        if template is None:
            pick = _largest(regs)
        else:
            pick = max(regs, key=lambda r: ncc(
                grey_patch(grey_frames[fi], r["cy"], r["cx"], half), template))
        rec = {"fi": fi, "cy": pick["cy"], "cx": pick["cx"],
               "count": pick["count"], "id": pick["id"]}
        cur = cur + [rec] if cur else [rec]
        template = grey_patch(grey_frames[fi], pick["cy"], pick["cx"], half)
        if len(cur) > len(best):
            best = list(cur)
    return best


def longest_run(track, grey_frames=None, *, enabled: bool = False, half: int = HALF):
    """THE GATED ENTRY POINT.

    `track` is the per-frame `(fi, largest_non_ground|None)` list from the
    existing `carve_track_indexed`.

      enabled=False  -> `_id_chain_largest(track)` — the EXISTING trajectory,
                        BYTE-IDENTICAL (the appearance code never runs).
      enabled=True   -> appearance-tracked run over the same per-frame largest
                        regions, chained by grey-patch NCC (requires
                        `grey_frames`), bridging Region-id flicker.
    """
    if not enabled:
        return _id_chain_largest(track)
    if grey_frames is None:
        raise ValueError("appearance path requires grey_frames")
    rpf = [(fi, [b] if b is not None else []) for fi, b in track]
    return _appearance_run(rpf, grey_frames, half)


def longest_run_all(regions_per_frame, grey_frames, *, half: int = HALF):
    """Appearance run over ALL non-ground regions per frame (not just the
    largest) — used where the largest region itself flickers between objects.
    `regions_per_frame` = list of (fi, [region dicts])."""
    return _appearance_run(regions_per_frame, grey_frames, half)


def track_multi(regions_per_frame, grey_frames, seed_regions, *, half: int = HALF):
    """Track SEVERAL objects at once by appearance, one region per object per
    frame (greedy one-to-one, so distinct objects are NOT merged). `seed_regions`
    is the frame-0 region dict per object. Returns a list of runs (one per seed).
    A per-frame region is claimed by at most one template (highest NCC first)."""
    templates = [grey_patch(grey_frames[regions_per_frame[0][0]],
                            s["cy"], s["cx"], half) for s in seed_regions]
    runs = [[{"fi": regions_per_frame[0][0], "cy": s["cy"], "cx": s["cx"],
              "count": s["count"], "id": s["id"]}] for s in seed_regions]
    for fi, regs in regions_per_frame[1:]:
        avail = list(regs)
        # score every (template, region) pair; assign greedily by descending NCC.
        pairs = []
        for ti, tmpl in enumerate(templates):
            for r in regs:
                pairs.append((ncc(grey_patch(grey_frames[fi], r["cy"], r["cx"], half),
                                  tmpl), ti, r))
        pairs.sort(key=lambda p: p[0], reverse=True)
        taken_t, taken_r = set(), set()
        for score, ti, r in pairs:
            rid = r["id"]
            if ti in taken_t or rid in taken_r:
                continue
            taken_t.add(ti)
            taken_r.add(rid)
            runs[ti].append({"fi": fi, "cy": r["cy"], "cx": r["cx"],
                             "count": r["count"], "id": r["id"]})
            templates[ti] = grey_patch(grey_frames[fi], r["cy"], r["cx"], half)
    return runs
