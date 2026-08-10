"""arc_ls20_percell_track — RUNG 222000 continuation: a GENERAL object-tracking
per-cell predictor for the LIVE half, given a larger budget.

The offline teeth (block 222000, on main) proved the per-cell TRANSFORM mechanism
decisively (strict changed-cell F1 1.0 vs ~0 nulls, CI-separated). The live half
returned the pre-registered NULL because the whole-frame-colour region selector
cannot isolate the real ls20 avatar: real ls20 has a NESTED field structure
(global mode colour + a local play-field), a MULTI-COLOUR avatar (~{9,11,12}) that
is NOT colour-separable from static structure, and a move+trail/consume dynamic.

This module adds the missing perception: OBJECT PERMANENCE via tracking. It is
GENERAL (no ls20 constants): the field is the frame's dominant colour(s); the
object is the connected FIGURE (non-field) blob that MOVED, tracked across frames;
the per-action SHIFT is learned from the change (appeared-vs-vacated centroid,
robust to static structure) and STORED IN THE GRAPH (a Hypothesis on the Percell
agent). Prediction reads the graph shift and TRANSLATES the tracked object -> a
per-cell next frame. The model stays graph-native (the shift is graph data); the
tracking is mechanical perception (the analogue of segment_and_track).
"""
from __future__ import annotations

import sys
from collections import Counter, deque
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def field_colours(g, k=2):
    """The k most frequent colours in the frame = the field/background (general:
    'the background is the dominant colour(s)', not a hardcoded 0). ls20 has a
    NESTED field (a global colour + a local play-field), so k=2 by default."""
    vals, counts = np.unique(g, return_counts=True)
    order = np.argsort(-counts)
    return set(int(vals[i]) for i in order[:k])


def connected_figure_blob(g, seeds, fields, cap):
    """4-connected BFS over FIGURE cells (value not in `fields`) from `seeds` --
    the moving object as a connected non-field blob. Returns the cell set, or None
    if it exceeds `cap` (not a compact object -> the tracker declines to model)."""
    H, W = g.shape
    fig = ~np.isin(g, list(fields))
    seen = set()
    dq = deque()
    for (r, c) in seeds:
        if 0 <= r < H and 0 <= c < W and fig[r, c] and (r, c) not in seen:
            seen.add((r, c)); dq.append((r, c))
    blob = set()
    while dq:
        r, c = dq.popleft()
        blob.add((r, c))
        if len(blob) > cap:
            return None
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and fig[nr, nc] and (nr, nc) not in seen:
                seen.add((nr, nc)); dq.append((nr, nc))
    return blob if blob else None


class LiveObjectTracker:
    """Object-permanence tracker + graph-native per-action shift model. `agent` is
    a Percell holding the shift Hypotheses; this class supplies the perception
    (which cells are the moving object, what shift each action applies)."""

    def __init__(self, agent, cap=200, n_field=2, shift_mode="centroid"):
        self.agent = agent
        self.cap = cap
        self.n_field = n_field
        # shift_mode selects the shift estimator. "centroid" (default, CORRECT) =
        # the whole-object before->after centroid displacement. "extent" (the BUG
        # caught in validation) = the appeared-vs-vacated edge gap, which measures
        # the object's EXTENT not its displacement (gave 3/5 instead of 1). It is
        # exposed ONLY so the instrument-teeth gate can prove the exact-shift number
        # is EARNED (an extent estimator must score far below the centroid one).
        self.shift_mode = shift_mode
        self.obj = None            # {(r,c): value} — current avatar footprint
        self.local_field = None    # the field colour the object moves over

    def observe(self, prev, cur, action):
        """Learn from one real transition: identify the moving object (connected
        figure blob overlapping the change), learn the per-action shift (appeared-
        vs-vacated centroid), store the shift in the graph, and update the tracked
        object to its new position."""
        fields = field_colours(prev, self.n_field)
        changed = [tuple(x) for x in np.argwhere(prev != cur)]
        if not changed:
            return
        appeared = [(r, c) for (r, c) in changed
                    if int(prev[r, c]) in fields and int(cur[r, c]) not in fields]
        vacated = [(r, c) for (r, c) in changed
                   if int(prev[r, c]) not in fields and int(cur[r, c]) in fields]
        seeds = appeared if appeared else changed
        blob = connected_figure_blob(cur, seeds, fields, self.cap)
        if blob is None:
            self.obj = None        # cannot isolate a compact object -> persistence
            return
        obj_before = dict(self.obj) if self.obj else None
        obj_after = {(r, c): int(cur[r, c]) for (r, c) in blob}
        if vacated:
            self.local_field = Counter(int(cur[r, c]) for (r, c) in vacated).most_common(1)[0][0]
        elif self.local_field is None:
            self.local_field = min(fields)
        # the TRANSLATION is the whole-object centroid displacement (before->after) --
        # NOT the appeared-vs-vacated edge gap (which measures the object's extent).
        # Only learnable once we have a prior object position; else just track.
        if obj_before:
            if self.shift_mode == "extent" and appeared and vacated:
                # THE BUG (instrument teeth only): edge gap = object extent, NOT
                # displacement. For an N-tall object moving 1 cell, appeared is the
                # new leading edge and vacated the old trailing edge, so their
                # centroid gap ~= N (gave 3/5 instead of 1).
                ca = np.array(appeared, dtype=float).mean(0)
                cv = np.array(vacated, dtype=float).mean(0)
                dr = int(round(ca[0] - cv[0])); dc = int(round(ca[1] - cv[1]))
            else:
                cb = np.array(list(obj_before), dtype=float).mean(0)
                ca = np.array(list(obj_after), dtype=float).mean(0)
                dr = int(round(ca[0] - cb[0])); dc = int(round(ca[1] - cb[1]))
            spec = {"key": f"shift:{dr}:{dc}", "region_colour": 0, "gen": "",
                    "k": 0, "dr": dr, "dc": dc, "subst": ""}
            self.agent.attend(action)
            self.agent.observe(action, prev, cur, spec=spec)
        self.obj = obj_after

    def predict(self, cur, action):
        """Predict the per-cell next frame: translate the tracked object by the
        action's learned shift (read from the graph). Persistence fallback when the
        shift is unknown/zero or no object is tracked."""
        h = self.agent.hypothesis(action)
        if h is None or self.obj is None or (h["dr"] == 0 and h["dc"] == 0):
            return cur.copy()
        dr, dc = h["dr"], h["dc"]
        H, W = cur.shape
        g = cur.copy()
        lf = self.local_field if self.local_field is not None else 0
        for (r, c) in self.obj:
            g[r, c] = lf                       # erase old object -> local field
        for (r, c), v in self.obj.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W:
                g[nr, nc] = v                  # draw the shifted object
        return g
