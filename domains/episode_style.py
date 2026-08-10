"""episode_style — RUN 42, PHASE 1: EPISODE STYLE NORMALIZATION.

Pure geometry estimator + canonicalizer (a capability class, CLAUDE.md's "pure capability
classes" bucket — ToolBox/GraphEye's own class — NOT a world adapter, NOT agent state, NOT a
decision: every function here is a deterministic numeric transform of point arrays, with no
conditional over graph state and no held Term it substitutes for). No agent reasoning lives
here; the AGENT's verdict (`domains.abs_read.parse_marginal_verdict`) is unchanged by this
module — this module only changes what raw ink the verdict is computed FROM, mechanically,
the same way RUN 37C's `DropDegenerateFilter` (`scripts/jabberwock_omniglot_run37c_hygiene.py`)
mechanically changes which strokes survive ingest.

THE MECHANISM (RUN 42 human-gap plan, PHASE 1): every eval episode's 20 exemplars share ONE
drawer (`ex_drawer`, one physical writer). That writer's STYLE — shear/slant, aspect ratio,
curvature bias — is a nuisance dimension the existing SC+TPS+parse-marginal verdict does NOT
absorb (`domains/glyph_motor_world._normalize`'s own docstring: "Slant / rotation / jitter
survive — that is the residual a 'hand' imposes"). RUN 40 (commit 45dc2855) found exemplar-
token badness drives mid+far verdict errors. This module estimates a drawer's systematic
shear/aspect bias from its 20 exemplars (pooled — noise-cancelling) and removes it
("canonicalization" toward the population-typical, zero-shear/unit-aspect origin), on the
claim that canonical-form exemplars are, on average, closer to an arbitrary OTHER drawer's
query than the idiosyncratic raw exemplar is (regression toward the mean).

PRE-REGISTERED ESTIMATORS (stated once, here, before any RUN 42 eval number exists):

  SHEAR:  a single moment-based deskew estimate (the standard OCR/document-deskew estimator):
          on the RUN-36-normalized glyph's pooled point cloud ("run-36 normalization" =
          `domains.omniglot_world`'s sibling — this module's own `normalize_glyph`, a direct,
          cited port of `scripts.jabberwock_omniglot_run36_failures._normalize_glyph`: joint
          center + abs-max over every stroke concatenated, then per-stroke normalize),
              shear_hat = Cov(x, y) / Var(y)
          A shape family with genuinely independent x/y has Cov(x,y) ≈ 0; a systematic shear
          bias s (x' = x + s·y) injects Cov(x,y) ≈ s·Var(y), so this recovers s. Pooling over
          20 glyphs (drawn from 20 DIFFERENT letter shapes, each individually anisotropic in
          its own idiosyncratic way) cancels per-letter noise and leaves the shared writer bias
          — the SAME "pool many instances, the systematic residual survives averaging, the
          idiosyncratic one does not" idea `seeds/writer_dimensions.json`'s `wd_infer_writer`
          rule uses (there: an agreement-count threshold over discrete pose deltas; here: a
          continuous mean over 20 continuous estimates — no discrete agreement gate is needed
          because there is no discreteness to gate on).

  ASPECT: a single symmetric log-variance-ratio estimate,
              aspect_log_hat = 0.5 · log(Var(y) / Var(x))
          on the SAME normalized point cloud. A shape family with isotropic extent has
          Var(y) ≈ Var(x) (aspect_log ≈ 0); a systematic h/w bias shows as a nonzero pooled
          mean. (log-ratio, not raw h/w, so the correction below is symmetric and area-
          preserving — see `canonicalize_strokes`.)

  CURVATURE BIAS (report-only — PRE-REGISTERED NOT APPLIED, per the RUN 42 brief's "optionally
          ... report but only apply if pre-registered" clause; this run does not pre-register
          applying it): mean absolute per-sample turn angle divided by total arc length,
          averaged over strokes with >=3 points, on the same normalized glyph.

  BOTH shear_hat and aspect_log_hat are ratios of second moments (Cov/Var, Var/Var) — provably
  invariant to any uniform additional translation + positive scalar rescaling of the input
  point cloud (any such factor cancels in the ratio). `domains.glyph_motor_world._normalize`
  (used downstream by `abs_read.stage_parse_char`'s whole-figure trajectory AND by
  `domains.canonical_parse.canonical_parts`'s own per-part normalize) is EXACTLY such a
  transform (center to centroid, scale to unit RMS radius — one isotropic scalar, no shear, no
  per-axis anisotropy). Consequence, stated explicitly so a reviewer need not re-derive it:
  applying `canonicalize_strokes` directly to a glyph's RAW (un-normalized) stroke points and
  letting the existing pipeline re-normalize afterward produces the IDENTICAL final geometry as
  normalizing first, canonicalizing, and denormalizing — `normalize(canonicalize(raw))` ==
  `normalize(canonicalize(normalize(raw)))` for this reason. `StyleCanonFilter` below exploits
  this: it canonicalizes at the RAW `load_strokes` boundary (one hook point, no denormalize
  step needed), while the ESTIMATION step above still explicitly runs `normalize_glyph` first,
  per the brief's literal pre-registration and for estimator transparency (bbox/curvature reads
  are easiest to reason about in a normalized frame even though the ratio estimators do not,
  strictly, require it).

QUERY-SIDE (RUN 42 pre-registration, stated once): the query gets the SAME estimator class
applied to its OWN single glyph (noisier — one glyph, not twenty — but unbiased: the estimator
is a plain sample statistic of the SAME family, not fit to any target). Query-side
canonicalization IS ARM-SEPARATED, by construction of the ARM plan: ARM E canonicalizes
exemplars only; ARM EQ canonicalizes exemplars AND the query.
"""
from __future__ import annotations

from typing import Optional

import numpy as np


# ===================================================================================================
# ESTIMATION — run-36 normalization, then two ratio-of-moments estimators + one report-only one.
# ===================================================================================================
def normalize_glyph(strokes: list) -> tuple:
    """Cited, byte-identical port of `scripts.jabberwock_omniglot_run36_failures.
    _normalize_glyph`: ONE joint center + abs-max scale over every stroke concatenated, then
    each stroke normalized by that shared center/scale (so cross-stroke LAYOUT survives, only
    translation + overall size are removed). Returns (normed_strokes, arclens, total_arclen)."""
    allpts = np.concatenate([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes], axis=0)
    center = allpts.mean(0)
    scale = float(np.abs(allpts - center).max()) or 1e-9
    normed = [(np.asarray(s, dtype=float).reshape(-1, 2) - center) / scale for s in strokes]
    arclens = []
    for s in normed:
        if s.shape[0] < 2:
            arclens.append(0.0)
            continue
        d = np.diff(s, axis=0)
        arclens.append(float(np.sqrt((d ** 2).sum(1)).sum()))
    total = sum(arclens) or 1e-9
    return normed, arclens, total


def _pooled_points(normed_strokes: list) -> np.ndarray:
    pts = [s for s in normed_strokes if s.shape[0] >= 1]
    if not pts:
        return np.zeros((0, 2))
    return np.concatenate(pts, axis=0)


def estimate_shear(strokes: list) -> float:
    """shear_hat = Cov(x, y) / Var(y) on the run-36-normalized, pooled point cloud. 0.0 for a
    degenerate glyph (< 2 points total, or Var(y) ~ 0 -- a flat horizontal glyph has no y-
    variance to measure shear against; an honest 0.0, never a fabricated value)."""
    normed, _, _ = normalize_glyph(strokes)
    pts = _pooled_points(normed)
    if pts.shape[0] < 2:
        return 0.0
    vy = float(np.var(pts[:, 1]))
    if vy < 1e-12:
        return 0.0
    cxy = float(np.cov(pts[:, 0], pts[:, 1], bias=True)[0, 1])
    return cxy / vy


def estimate_aspect_log(strokes: list) -> float:
    """aspect_log_hat = 0.5*log(Var(y)/Var(x)) on the same normalized point cloud. 0.0 for a
    degenerate glyph (< 2 points, or either variance ~ 0)."""
    normed, _, _ = normalize_glyph(strokes)
    pts = _pooled_points(normed)
    if pts.shape[0] < 2:
        return 0.0
    vx, vy = float(np.var(pts[:, 0])), float(np.var(pts[:, 1]))
    if vx < 1e-12 or vy < 1e-12:
        return 0.0
    return 0.5 * float(np.log(vy / vx))


def estimate_curvature_bias(strokes: list) -> float:
    """REPORT-ONLY (pre-registered NOT applied by `canonicalize_strokes`): mean absolute turn
    angle per unit arc length, averaged (arc-length-weighted) over strokes with >=3 points, on
    the run-36-normalized glyph. 0.0 if no stroke qualifies."""
    normed, arclens, _ = normalize_glyph(strokes)
    turn_sum, len_sum = 0.0, 0.0
    for s, arc in zip(normed, arclens):
        if s.shape[0] < 3 or arc < 1e-9:
            continue
        d = np.diff(s, axis=0)
        ang = np.arctan2(d[:, 1], d[:, 0])
        dturn = np.abs(np.diff(ang))
        dturn = np.minimum(dturn, 2.0 * np.pi - dturn)
        turn_sum += float(dturn.sum())
        len_sum += arc
    return (turn_sum / len_sum) if len_sum > 1e-9 else 0.0


def estimate_style(strokes: list) -> dict:
    """One glyph's full style estimate -- the three pre-registered scalars."""
    return dict(shear=estimate_shear(strokes), aspect_log=estimate_aspect_log(strokes),
                curvature_bias=estimate_curvature_bias(strokes))


def pool_style(styles: list) -> dict:
    """Drawer-level pooling: the arithmetic mean of each parameter across a drawer's glyphs --
    RUN 42's continuous analogue of `writer_dimensions.json`'s `wd_infer_writer` discrete
    agreement-count pooling (see module docstring). `styles` is a list of `estimate_style(...)`
    dicts (typically the drawer's own 20 exemplar glyphs)."""
    if not styles:
        return dict(shear=0.0, aspect_log=0.0, curvature_bias=0.0)
    return dict(shear=float(np.mean([s["shear"] for s in styles])),
                aspect_log=float(np.mean([s["aspect_log"] for s in styles])),
                curvature_bias=float(np.mean([s["curvature_bias"] for s in styles])))


# ===================================================================================================
# CANONICALIZATION — apply the INVERSE of an estimated (shear, aspect_log) to raw stroke points.
# ===================================================================================================
def canonicalize_strokes(strokes: list, style: dict) -> list:
    """Remove `style`'s shear and aspect_log from `strokes` (curvature_bias is NEVER applied --
    report-only, pre-registered). Deshear: x' = x - shear*y (removes the estimated Cov(x,y)
    bias). Deaspect: x'' = x'*exp(aspect_log/2), y'' = y*exp(-aspect_log/2) -- an AREA-
    PRESERVING (kx*ky=1) anisotropic rescale chosen so Var(y'')/Var(x'') == 1 exactly when
    `style` was estimated from this SAME glyph (see the derivation: kx/ky = exp(aspect_log),
    and aspect_log = 0.5*log(Var(y)/Var(x)) by construction). Applied directly to `strokes` in
    whatever coordinate frame they arrive in (raw pixel-space from `omniglot_world.load_strokes`
    is the intended caller) -- see the module docstring's invariance note for why this is exact,
    not an approximation, once the downstream pipeline re-normalizes (which every caller here
    does). Deterministic and idempotent: canonicalizing an ALREADY-canonical glyph with the SAME
    style dict a second time is a no-op up to floating point (shear=aspect_log=0 leaves points
    unchanged); applying it twice with the identical nonzero style is NOT a no-op (each call
    subtracts the SAME shear again) -- callers apply it exactly once per glyph, per style."""
    shear = float(style.get("shear", 0.0))
    aspect_log = float(style.get("aspect_log", 0.0))
    kx = float(np.exp(aspect_log / 2.0))
    ky = float(np.exp(-aspect_log / 2.0))
    out = []
    for s in strokes:
        arr = np.asarray(s, dtype=float).reshape(-1, 2).copy()
        if arr.shape[0] == 0:
            out.append(arr)
            continue
        x = arr[:, 0] - shear * arr[:, 1]
        arr[:, 0] = x * kx
        arr[:, 1] = arr[:, 1] * ky
        out.append(arr)
    return out


# ===================================================================================================
# I/O REDIRECTION — mechanical, mirrors `jabberwock_omniglot_run37c_hygiene.DropDegenerateFilter`
# exactly (monkeypatch `omniglot_world.load_strokes` for the life of a `with` block). No decision:
# a path either has a registered style (canonicalize) or does not (pass through unchanged).
# ===================================================================================================
class StyleCanonFilter:
    """`with StyleCanonFilter(style_by_path): ...` -- for the life of the block, every
    `domains.omniglot_world.load_strokes(path)` call for a `path` present in `style_by_path`
    returns `canonicalize_strokes(raw_strokes, style_by_path[path])` instead of the raw strokes;
    every other path (and `load_strokes_t`, untouched) passes through unchanged. Compose with
    `DropDegenerateFilter` by nesting THIS filter INSIDE it
    (`with DropDegenerateFilter(): with StyleCanonFilter(...): ...`) so degenerate strokes are
    dropped BEFORE the style estimate/canonicalization ever sees them."""

    def __init__(self, style_by_path: dict):
        self.style_by_path = style_by_path

    def __enter__(self):
        import domains.omniglot_world as ow
        self._ow = ow
        self._orig = ow.load_strokes
        orig = self._orig
        style_by_path = self.style_by_path

        def _patched(path, *a, **kw):
            strokes = orig(path, *a, **kw)
            style = style_by_path.get(path)
            if style is None:
                return strokes
            return canonicalize_strokes(strokes, style)

        ow.load_strokes = _patched
        return self

    def __exit__(self, *exc):
        self._ow.load_strokes = self._orig
        return False


def style_for_path(path: str, *, loader: Optional[object] = None) -> dict:
    """One glyph's own style estimate, loaded fresh via `omniglot_world.load_strokes` (or
    `loader`, e.g. a `DropDegenerateFilter`-patched one already installed on the module --
    caller's responsibility to have entered that context first, mirroring every other
    `ow.load_strokes(path)` call site in this codebase). Boundary convenience only -- no
    decision; `estimate_style` does the actual work."""
    import domains.omniglot_world as ow
    load = loader or ow.load_strokes
    return estimate_style(load(path))
