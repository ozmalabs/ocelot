"""toy_hat — the CLEAN sense-hat that PROVES the cortex loop is sound (NO domain gap).

The audio hat carries a synthetic-vs-real DOMAIN GAP: the cortex re-renders with
espeak, but the heard items are real recordings, so the compare cannot separate the
true word (commit da783064 — the failure is the audio hat's compare, not the loop).
This toy hat removes that confound: the "heard" item and every synthesized candidate
are rendered the SAME WAY (the same render()), so there is NO synthetic-vs-real gap.
If the IDENTICAL CortexLoop recognises the shape here while factoring out the
transform (held-out transforms = the analogue of held-out speakers), the loop is
sound and the audio failure is quarantined to the audio hat.

The sense:
  · CONTENT = a shape from a small set (a glyph stamped on a grid).
  · STYLE   = a transform: rotation (0/90/180/270), scale (0..2), translation (dx,dy).
  · render(shape, style) -> an NxN feature grid as an ORDERED trajectory of rows
    (N frames x N bands) — the SAME shape the agent's DtwTo reads, so compare is the
    agent's owned graph op (no net, no fit), identical in KIND to the audio hat.
  · encode(grid) = the grid is already in feature space (the "heard" item is a render
    under an unknown transform — exactly like a clip from an unknown speaker).
  · synth(shape, style) = render(shape, style)  -> NO domain gap by construction.
  · compare(a, b) = DtwTo(a, b), the agent's native trajectory residual.

Held-out test items = shapes under UNSEEN transforms (transforms not in the library),
never banked — the analogue of held-out speakers.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from domains.hat import Hat
from domains.fuzzy_smooth import multiscale_grid
from scripts.dtw_trajectory_loso import _Pred, _V, _Attr

# The toy compare is an OWNED graph op: L2 distance over the flat feature grid =
# Magnitude(VecSub(a, b)). No DTW (a 2D grid has no time axis to warp), no net, no fit.
_TOY_FEAT_ATTR = "toy_feat"


def _vecsub(a, b):
    return {"type": "VecSub", "a": a, "b": b}


def _magnitude(a):
    return {"type": "Magnitude", "arg": a}


# ---------------------------------------------------------------------------
# The base glyphs (content). Each is a stroke set drawn on a unit canvas
# [-1,1]^2, rasterised under a transform. A small, distinguishable set.
# ---------------------------------------------------------------------------

def _seg(p0, p1, n=24):
    return [(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
            for t in np.linspace(0.0, 1.0, n)]


def _circle(r=0.7, n=64):
    return [(r * math.cos(a), r * math.sin(a))
            for a in np.linspace(0.0, 2 * math.pi, n)]


_SHAPES: Dict[str, List[Tuple[float, float]]] = {
    # a vertical/horizontal cross
    "plus": _seg((0, -0.8), (0, 0.8)) + _seg((-0.8, 0), (0.8, 0)),
    # a square outline
    "square": (_seg((-0.7, -0.7), (0.7, -0.7)) + _seg((0.7, -0.7), (0.7, 0.7)) +
               _seg((0.7, 0.7), (-0.7, 0.7)) + _seg((-0.7, 0.7), (-0.7, -0.7))),
    # a diagonal X
    "ex": _seg((-0.7, -0.7), (0.7, 0.7)) + _seg((-0.7, 0.7), (0.7, -0.7)),
    # a triangle outline
    "tri": (_seg((0, 0.8), (0.75, -0.6)) + _seg((0.75, -0.6), (-0.75, -0.6)) +
            _seg((-0.75, -0.6), (0, 0.8))),
    # a circle
    "circle": _circle(0.7),
    # an L
    "ell": _seg((-0.5, 0.8), (-0.5, -0.6)) + _seg((-0.5, -0.6), (0.6, -0.6)),
    # a T
    "tee": _seg((-0.7, 0.7), (0.7, 0.7)) + _seg((0, 0.7), (0, -0.7)),
    # a horizontal bar pair (=)
    "eq": _seg((-0.7, 0.3), (0.7, 0.3)) + _seg((-0.7, -0.3), (0.7, -0.3)),
}


class ToyHat(Hat):
    """A clean render-based sense. Style = (rotation, scale, dx, dy). The library is a
    grid of seen transforms; the test items use UNSEEN transforms (held out)."""

    name = "toy"

    def __init__(self, substrate, grid_n: int = 16, seed: int = 20240610,
                 shapes: List[str] = None, smooth_scales=None, render_blur: bool = True):
        self.s = substrate
        self.N = int(grid_n)
        self.shapes = list(shapes) if shapes else list(_SHAPES.keys())
        # FUZZY compare: smooth the feature grid at this set of blur scales (sigmas,
        # in grid cells) before the L2 residual. [0.0] == the rigid (un-smoothed)
        # compare. A multi-element list = a blur pyramid (coarse-to-fine). Swept by
        # the test harness to find the scale that removes low-res aliasing without
        # erasing the shape.
        self.smooth_scales = list(smooth_scales) if smooth_scales else [0.0]
        # render_blur=True keeps the historical render-time box blur (a pre-smoothed
        # front end). Set False to rasterise RAW 1-pixel strokes -> true aliasing, so
        # the compare-time smoothing is the ONLY smoothing (isolates the fuzzy effect).
        self.render_blur = bool(render_blur)
        self._resid_term = _Pred(_magnitude(_vecsub(
            _Attr(_V("q"), _TOY_FEAT_ATTR), _Attr(_V("c"), _TOY_FEAT_ATTR))))
        self.qn = substrate.add_node("ToyHatQ", {"origin": "toyhat_q"})
        self.cn = substrate.add_node("ToyHatCand", {"origin": "toyhat_c"})
        self._render_cache: Dict[Tuple, Any] = {}
        # style axes (the library / seen transforms): rotations, scales, translations.
        # Rotation library spans the circle on a 60-degree grid (seen angles); the
        # held-out test uses angles OFF this grid (e.g. 30/45/...), reached by the
        # adapt's finer rotation steps. Scale/translation libraries are coarse; the
        # held-out test uses off-grid scales/translations too.
        self._rot_grid = [0, 60, 120, 180, 240, 300]
        self._scale_grid = [0.8, 1.0, 1.2]
        self._trans_grid = [-2, 0, 2]
        self._library: List[Tuple[str, Dict[str, Any], Any]] = []
        self._build_library(seed)

    # ---- rendering (the world; render IS synth, hence no domain gap) ----
    def _render(self, shape: str, style: Dict[str, Any]) -> Any:
        key = (shape, int(style["rot"]), round(float(style["scale"]), 3),
               int(style["dx"]), int(style["dy"]))
        cached = self._render_cache.get(key)
        if cached is not None:
            return cached
        pts = _SHAPES[shape]
        rot = math.radians(style["rot"])
        cr, sr = math.cos(rot), math.sin(rot)
        sc = float(style["scale"])
        N = self.N
        grid = np.zeros((N, N), dtype=np.float64)
        half = (N - 1) / 2.0
        for (x, y) in pts:
            xr = (x * cr - y * sr) * sc
            yr = (x * sr + y * cr) * sc
            # map [-1,1] -> pixel, then translate by (dx,dy) pixels.
            px = int(round(half + xr * half * 0.9)) + int(style["dx"])
            py = int(round(half - yr * half * 0.9)) + int(style["dy"])
            if 0 <= px < N and 0 <= py < N:
                grid[py, px] = 1.0
        # Gaussian-ish smoothing so the L2 metric is tolerant to sub-pixel / small
        # misalignment (an overlap measure, not a hard pixel-XOR). A separable blur
        # applied a few times approximates a Gaussian; this is the feature front end.
        feat_grid = grid
        if self.render_blur:
            for _ in range(3):
                b = feat_grid.copy()
                b[1:, :] += 0.5 * feat_grid[:-1, :]
                b[:-1, :] += 0.5 * feat_grid[1:, :]
                b[:, 1:] += 0.5 * feat_grid[:, :-1]
                b[:, :-1] += 0.5 * feat_grid[:, 1:]
                feat_grid = b
        # normalise so total energy is comparable across shapes (different stroke counts).
        nrm = float(np.linalg.norm(feat_grid)) + 1e-9
        feat_grid = feat_grid / nrm
        # FUZZY compare: smooth the (N x N) feature grid at the hat's blur scales
        # (a pyramid) before flattening. multiscale_grid([0.0]) is the rigid grid;
        # larger sigmas remove the high-frequency aliasing that breaks the L2 metric
        # at small N. Per-scale L2 keeps the metric balanced across scales.
        feat_vec = multiscale_grid(feat_grid, self.smooth_scales)
        feat = tuple(float(v) for v in feat_vec)    # flat (multi-scale) feature grid
        self._render_cache[key] = feat
        return feat

    # ---- the three core methods ----
    def encode(self, raw: Any) -> Any:
        # raw is already a rendered grid (heard item under an unknown transform).
        if isinstance(raw, tuple):
            return raw
        return tuple(float(v) for v in np.asarray(raw, dtype=np.float64).reshape(-1))

    def synth(self, shape: str, style: Dict[str, Any]) -> Any:
        return self._render(shape, style)

    def compare(self, a: Any, b: Any) -> float:
        if a is None or b is None:
            return float("inf")
        self.s.set_attr(self.qn, _TOY_FEAT_ATTR, a)
        self.s.set_attr(self.cn, _TOY_FEAT_ATTR, b)
        d = self.s.evaluate(self._resid_term, {"q": self.qn, "c": self.cn})
        return float(d) if d is not None else float("inf")

    # ---- search scaffolding ----
    def contents(self):
        return self.shapes

    def style_init(self) -> Dict[str, Any]:
        return {"rot": 0, "scale": 1.0, "dx": 0, "dy": 0}

    def n_stages(self) -> int:
        return 2

    def style_neighbours(self, style: Dict[str, Any], stage: int) -> Iterable[Dict[str, Any]]:
        scale_step = [0.2, 0.1][stage]
        trans_step = [2, 1][stage]
        rot_step = [30, 15][stage]          # coarse -> finer angle off the library grid
        out = []
        # rotation axis: 90-degree quadrants (stage 0), then 30-degree refinement
        # (stage 1) so off-grid held-out angles are reachable.
        for drot in (rot_step, -rot_step):
            c = dict(style); c["rot"] = (style["rot"] + drot) % 360
            out.append(c)
        # scale axis (continuous).
        for ds in (scale_step, -scale_step):
            c = dict(style); c["scale"] = round(min(2.0, max(0.4, style["scale"] + ds)), 3)
            if abs(c["scale"] - style["scale"]) > 1e-9:
                out.append(c)
        # translation axes (continuous, in pixels).
        for dd in (trans_step, -trans_step):
            c = dict(style); c["dx"] = style["dx"] + dd
            out.append(c)
            c = dict(style); c["dy"] = style["dy"] + dd
            out.append(c)
        return out

    def library(self):
        return self._library

    def close(self):
        self.s.remove_node(self.qn)
        self.s.remove_node(self.cn)

    # ---- library (seen transforms) ----
    def _build_library(self, seed: int):
        # the SEEN transforms: every rotation on the grid x a small scale set, centred.
        # Rotation coverage is the priority (it is the hardest axis for the metric);
        # scale/translation are seeded coarsely and finished by the adapt.
        self._seen_styles = [{"rot": r, "scale": sc, "dx": 0, "dy": 0}
                             for r in self._rot_grid for sc in self._scale_grid]
        for sh in self.shapes:
            for st in self._seen_styles:
                self._library.append((sh, dict(st), self._render(sh, st)))

    # ---- held-out test set (UNSEEN transforms; never banked) ----
    def held_out_test(self, n_per_shape: int, seed: int):
        """Generate (shape, raw_grid) test items under transforms NOT in the library
        (rotations off the 90-grid, scales/translations off the grid). The analogue of
        held-out speakers. Returns a list of (shape, raw_features)."""
        rng = random.Random(seed + 999)
        seen_rots = set(self._rot_grid)
        # held-out angles strictly OFF the 60-degree library grid.
        off_rots = [a for a in range(0, 360, 15) if a not in seen_rots]
        items = []
        for sh in self.shapes:
            for _ in range(n_per_shape):
                style = {
                    "rot": rng.choice(off_rots),                 # unseen rotation
                    "scale": round(rng.uniform(0.7, 1.3), 3),    # off-grid scale
                    "dx": rng.choice([-3, -2, -1, 1, 2, 3]),     # nonzero translation
                    "dy": rng.choice([-3, -2, -1, 1, 2, 3]),
                }
                items.append((sh, self._render(sh, style)))
        rng.shuffle(items)
        return items
