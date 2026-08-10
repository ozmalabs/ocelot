"""exemplar_expand — RUN 43, PHASE 3: EXEMPLAR EXPANSION UNDER A BACKGROUND-CALIBRATED
VARIATION MODEL.

Pure geometry: background calibration (estimators over already-loaded stroke arrays) + a
deterministic variant-stroke generator + a mechanical I/O-redirection filter. A capability
class (CLAUDE.md's "pure capability classes" bucket, `episode_style.py`'s own precedent) — NOT
a world adapter, NOT agent state, NOT a decision. Every function here is a deterministic
numeric transform of point arrays or a plain mean/std reduction; the ONLY decisions this run
makes (which candidate wins, min-over-a-set) are held `MinOver`/`Argmin` Terms evaluated by the
gate script (`scripts/jabberwock_omniglot_run43_expand.py`), never here — mirrors
`episode_style.py`'s own division of labour (estimate/canonicalize here, verdict there)
exactly, and this module's own source-audit test enforces it the same way that module's does.

THE MECHANISM (see the launch brief / commit history for the full derivation): RUN 40 found
exemplar-token badness drives the mid+far verdict error bands — comparing a query to ONE raw
render of a class is comparing against a possibly-unrepresentative token. This module estimates,
from the 5 LEARN alphabets' own within-class drawer-to-drawer spread, how much four WRITER
dimensions typically vary for one character across different physical writers — global
ROTATION, SHEAR (RUN 42, commit c95efc96, proved shear is writer-specific, not script-specific —
its own binding law this run obeys: never vary ASPECT, that dimension is alphabet-characteristic,
not writer-characteristic), a GLOBAL LOG-SCALE (reported for completeness, NOT rendered — see
"WHY NO GLOBAL SCALE VARIANT" below), and PER-STROKE POSE JITTER (position/orientation/scale of
each stroke relative to the whole glyph, RUN 34's `pose_x/pose_y/pose_o/pose_s` naming). The
gate script then renders K=8 deterministic variants of each candidate's raw strokes (grid, not
RNG — pre-registered, reproducible) and scores a candidate as the MIN pairwise error over its
own {original, 8 variants} set — the mechanism's actual claim: the exemplar SET, not one token,
is what should stand for a class.

PRE-REGISTERED ESTIMATORS (stated here, before any RUN 43 eval number exists — none of these
four numbers is fit to, or adjusted against, the eval; `calibrate_or_load` freezes them to
`results/run43_checkpoints/calibration.json` the first time they are computed and every
subsequent call in this run reads that frozen file back verbatim):

  SHEAR: `episode_style.estimate_shear` (Cov(x,y)/Var(y) on the RUN-36-normalized pooled point
  cloud), REUSED VERBATIM — RUN 42 already validated this exact estimator as writer-specific.
  Not re-derived here.

  ROTATION: the classic 2x2-covariance PRINCIPAL-AXIS ANGLE,
      angle = 0.5 * atan2(2*Cov(x,y), Var(x) - Var(y))
  on the same RUN-36-normalized pooled point cloud (`estimate_rotation_angle`). This is a LINE
  angle, not a vector angle — it is only defined modulo pi (a principal axis has no inherent
  "forward" direction), so all pooling below uses the standard DOUBLE-ANGLE circular-statistics
  trick (`pool_rotation`: average exp(2i*angle), the pooled angle is half the argument of that
  mean — the same "double the angle, do ordinary circular stats, halve it back" idiom
  `seeds/writer_dimensions.json`'s own `orient_delta` agreement-count pooling sidesteps by using
  a discrete threshold instead; this module needs a continuous magnitude, hence circular mean+
  residual-std rather than a discrete vote).

  LOG-SCALE: `log(scale)` where `scale` is the SAME joint abs-max scale factor `episode_style.
  normalize_glyph` computes and divides out (i.e. this is the RAW, PRE-normalization size of
  the glyph in pixel-space) — a genuine "does this writer draw big or small" trait.

  PER-STROKE POSE (position/orientation/scale of ONE stroke relative to the WHOLE GLYPH's own
  RUN-36-normalized frame, `stroke_pose`): `pose_x, pose_y` = the stroke's own centroid in that
  frame; `pose_o` = the SAME principal-axis-angle estimator applied to just this stroke's own
  points, minus the whole glyph's own principal-axis angle (wrapped to (-pi/2, pi/2]) — "how
  this stroke's local orientation differs from the figure's overall orientation"; `pose_s` =
  log of the stroke's own point cloud's RMS radius about its own centroid (the whole figure's
  RMS radius is 1 by `normalize_glyph`'s own construction, so this reads directly as a
  log-ratio). ALL FOUR are properties of ONE glyph — they are not yet a "jitter" (noise) measure
  by themselves; see `calibrate_background` for how the WITHIN-CLASS SPREAD across drawers, at a
  FIXED draw-order stroke slot, turns them into a magnitude.

  BACKGROUND POOLING (`calibrate_background`): for every character class in the 5 LEARN
  alphabets (`omniglot_world.alphabets("background")[:learn_n]`, ALL characters and ALL drawers
  per class — no held-out subsampling; a background-sample cost check (this module's own
  authoring notes) found <0.5ms/file, so the full ~3100-file background population is cheap
  enough to use whole, not a documented-and-capped prefix like the eval protocol's own 10/20
  test-alphabet prefixes), each of the four per-glyph estimates above is computed for EVERY
  drawer, the CLASS-LEVEL MEAN is subtracted (rotation via `pool_rotation`'s own circular mean),
  and the RESIDUALS are pooled across EVERY class into one population per dimension — the
  population's STANDARD DEVIATION is the calibrated magnitude `render_variant` samples at
  (Z_QUANTILE = 0.6745, the standard normal p25/p75 z-score, per the launch brief's own "K=8
  variants at the p25/p75 of each dim" instruction). Per-stroke pose is pooled the same way,
  but ADDITIONALLY held fixed at one draw-order STROKE SLOT k (0-indexed, restricted to
  `k < min(len(strokes) for every drawer in this class)`, the SAME "the shortest drawer sets the
  comparison length" convention `run25_number._block_spec`'s own `n_drawers = min(...)` idiom
  already uses elsewhere in this arc) before pooling across classes, so a jitter residual is
  genuinely "how much does THIS stroke, in THIS class, vary drawer-to-drawer" — never a spurious
  cross-stroke comparison.

WHY NO GLOBAL SCALE VARIANT (a documented negative-by-construction, not a discovered null): the
comparator this run's `render_variant` output ultimately feeds
(`domains.abs_read.stage_parse_char` -> `glyph_motor_world.to_trajectory[_strokes]` for the
whole-figure feature, `domains.canonical_parse.canonical_parts` for the per-part features) both
RE-NORMALIZE translation and ISOTROPIC scale from scratch on every call (`glyph_motor_world.
_normalize`'s own docstring: "Translation + scale invariance ... Slant / rotation / jitter
survive"). An ISOTROPIC rescale of the whole raw glyph before that renormalization is
mathematically CANCELLED exactly by it — multiplying every point by a constant k changes the
RMS-radius scale factor by the same k, so the renormalized output is bit-for-bit unchanged.
Rendering a "global scale" variant would therefore be a STRUCTURAL no-op, not an engagement
test; `log_scale_std` is still measured and reported (the launch brief's own "report the
calibrated variation magnitudes ... per dim" instruction, and RUN 28's "report engagement
separately from outcome" law extends to "report a dimension even when its non-engagement is
provable, not just observed") but is EXCLUDED from `VARIANT_GRID`. The PER-STROKE `pose_s`
component (a stroke's scale RELATIVE TO THE OTHER STROKES in the same figure) is the writer-
scale dimension that DOES survive whole-figure renormalization, and is rendered as part of
`pose_jitter` below.

VARIANT GRID (`render_variant`, K=8, deterministic — no RNG anywhere in this module, the
launch brief's own "deterministic grid not RNG" option): four dims x two signs,
    rotation(-1), rotation(+1), shear(-1), shear(+1),
    pose_jitter(-1), pose_jitter(+1), combined(-1), combined(+1)
`combined` applies all three (rotation + shear + pose_jitter) at once, at the SAME
Z_QUANTILE-scaled magnitude, per dim — a calibrated echo of RUN 25 C3's/`glyph_motor_world.
write_with_hand`'s own "vary everything at once" shape, included so the gate's own per-dim
enrichment table can show whether isolating a dimension or perturbing everything jointly is
what fixes/breaks an episode. `pose_jitter`'s per-stroke application alternates sign by
draw-order stroke index (`i % 2`) — a fixed, non-random pattern approximating independent
per-stroke noise (every stroke does NOT move the same way, unlike the three rigid/whole-figure
dims) without introducing an RNG this run would then have to seed and report.

I/O REDIRECTION (`VariantStrokesFilter`, `variant_key`): mirrors `episode_style.
StyleCanonFilter`'s exact monkeypatch idiom (patch `omniglot_world.load_strokes` for the life of
a `with` block) — the one difference is the substituted value is an ALREADY-COMPUTED variant
stroke list (this module's own `render_variant` output) keyed by a SYNTHETIC virtual key
(`variant_key(real_path, k)`, a string containing a NUL byte — provably never a real filesystem
path) rather than a per-real-path style dict recomputed inside the patched call. This lets the
gate script stage a variant through the UNCHANGED `abs_read.stage_parse_char` exactly as if it
were a 20th real file, so the comparator itself (`parse_marginal_pair_error`) is provably
untouched — only which ink `stage_parse_char` sees for a given (synthetic) path changes.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np

from domains import episode_style as es

Z_QUANTILE = 0.6745    # standard normal p25/p75 z-score, per the launch brief's own instruction.

VARIANT_DIMS = ("rotation", "shear", "pose_jitter", "combined")
VARIANT_GRID = (
    ("rotation", -1), ("rotation", 1),
    ("shear", -1), ("shear", 1),
    ("pose_jitter", -1), ("pose_jitter", 1),
    ("combined", -1), ("combined", 1),
)


# ===================================================================================================
# ESTIMATORS -- rotation (new) + log-scale (new) + per-stroke pose (new); shear is `episode_
# style.estimate_shear`, reused verbatim (imported, never re-derived).
# ===================================================================================================
def _wrap_half_pi(a: float) -> float:
    """Wrap an angle (radians) into (-pi/2, pi/2] -- the residue class of a LINE angle (a
    principal axis has no forward direction, so pi and 0 are the same axis)."""
    return float((a + np.pi / 2.0) % np.pi - np.pi / 2.0)


def estimate_rotation_angle(strokes: list) -> float:
    """0.5*atan2(2*Cov(x,y), Var(x)-Var(y)) on the run-36-normalized pooled point cloud -- the
    principal-axis angle of the glyph's own point cloud, in (-pi/2, pi/2]. 0.0 for a degenerate
    glyph (<2 points, or a perfectly isotropic cloud where the axis is undefined)."""
    normed, _, _ = es.normalize_glyph(strokes)
    pts = np.concatenate([s for s in normed if s.shape[0] >= 1], axis=0) if normed else np.zeros((0, 2))
    if pts.shape[0] < 2:
        return 0.0
    vx, vy = float(np.var(pts[:, 0])), float(np.var(pts[:, 1]))
    cxy = float(np.cov(pts[:, 0], pts[:, 1], bias=True)[0, 1])
    if abs(vx - vy) < 1e-12 and abs(cxy) < 1e-12:
        return 0.0
    return _wrap_half_pi(0.5 * float(np.arctan2(2.0 * cxy, vx - vy)))


def pool_rotation(angles: list) -> tuple:
    """Circular mean + per-item residuals of a list of LINE angles (radians, any wrap) via the
    double-angle trick: average exp(2i*angle) (a full vector, no wrap ambiguity), the pooled
    angle is half that mean vector's own argument. Residuals are each input's own signed
    difference from the pooled mean, wrapped to (-pi/2, pi/2]. Returns (mean_angle, residuals);
    `(0.0, [0.0]*len(angles))` for an empty input list (never a crash)."""
    if not angles:
        return 0.0, []
    z = np.mean(np.exp(2.0j * np.asarray(angles, dtype=float)))
    mean_angle = _wrap_half_pi(0.5 * float(np.angle(z))) if abs(z) > 1e-12 else 0.0
    residuals = [_wrap_half_pi(a - mean_angle) for a in angles]
    return mean_angle, residuals


def estimate_log_scale(strokes: list) -> float:
    """log of the RAW (pre-normalization) joint abs-max scale factor `episode_style.
    normalize_glyph` itself divides out -- the glyph's own absolute size in pixel-space. 0.0
    (log(1)) for a degenerate/empty glyph."""
    if not strokes:
        return 0.0
    allpts = np.concatenate([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes], axis=0)
    if allpts.shape[0] == 0:
        return 0.0
    center = allpts.mean(0)
    scale = float(np.abs(allpts - center).max())
    return float(np.log(scale)) if scale > 1e-9 else 0.0


def stroke_pose(normed_stroke: np.ndarray, whole_angle: float) -> tuple:
    """`(pose_x, pose_y, pose_o, pose_s)` of ONE already-run-36-normalized stroke's point array,
    relative to the WHOLE GLYPH's own frame (`normalize_glyph` already centered+scaled the
    whole glyph, so `pose_x/pose_y` -- this stroke's own centroid -- are directly in that
    frame). `pose_o` = this stroke's own `estimate_rotation_angle`-style principal angle minus
    `whole_angle` (the caller's own already-computed whole-glyph angle), wrapped. `pose_s` =
    log(this stroke's own RMS radius about its own centroid) -- the whole glyph's RMS radius is
    1 by `normalize_glyph`'s own construction, so this is directly a log-ratio. A degenerate
    (<1 point) stroke returns `(0.0, 0.0, 0.0, 0.0)`; a single-point stroke returns its own
    position with `pose_o=pose_s=0.0` (no local orientation/extent to measure)."""
    arr = np.asarray(normed_stroke, dtype=float).reshape(-1, 2)
    if arr.shape[0] == 0:
        return 0.0, 0.0, 0.0, 0.0
    c = arr.mean(axis=0)
    if arr.shape[0] < 2:
        return float(c[0]), float(c[1]), 0.0, 0.0
    centered = arr - c
    vx, vy = float(np.var(centered[:, 0])), float(np.var(centered[:, 1]))
    cxy = float(np.cov(centered[:, 0], centered[:, 1], bias=True)[0, 1])
    local_angle = (0.0 if (abs(vx - vy) < 1e-12 and abs(cxy) < 1e-12)
                   else _wrap_half_pi(0.5 * float(np.arctan2(2.0 * cxy, vx - vy))))
    pose_o = _wrap_half_pi(local_angle - whole_angle)
    rms = float(np.sqrt((centered ** 2).sum(axis=1).mean()))
    pose_s = float(np.log(rms)) if rms > 1e-9 else 0.0
    return float(c[0]), float(c[1]), pose_o, pose_s


# ===================================================================================================
# BACKGROUND CALIBRATION -- pool within-class residuals across the 5 LEARN alphabets.
# ===================================================================================================
DEFAULT_LEARN_N = 5


def calibrate_background(*, learn_n: int = DEFAULT_LEARN_N) -> dict:
    """Compute the four calibrated writer-dim magnitudes (shear/rotation/log_scale std +
    per-stroke pose_x/y/o/s std) from the WITHIN-CLASS drawer-to-drawer spread across every
    character in the first `learn_n` `omniglot_world.alphabets("background")` alphabets (ALL
    characters, ALL drawers per class -- see module docstring's cost note). `drop_degenerate=
    True` on every load (RUN 37C hygiene, matching the eval protocol's own ingest condition).
    Mechanical aggregation only -- no decision, no argmin/argmax, a plain mean/std reduction
    per dimension. Returns a flat, JSON-serializable dict (`calibrate_or_load` freezes it)."""
    import domains.omniglot_world as ow

    alphs = ow.alphabets("background")[:learn_n]
    shear_res, rot_res, scale_res = [], [], []
    pose_res = {"x": [], "y": [], "o": [], "s": []}
    n_classes = 0
    n_glyphs = 0

    for alph in alphs:
        for cdir in ow.characters(alph, "background"):
            files = ow.drawings(cdir)
            all_strokes = [ow.load_strokes(p, drop_degenerate=True) for p in files]
            all_strokes = [s for s in all_strokes if s]
            if len(all_strokes) < 2:
                continue
            n_classes += 1
            n_glyphs += len(all_strokes)

            shears = [es.estimate_shear(s) for s in all_strokes]
            m_shear = float(np.mean(shears))
            shear_res.extend(v - m_shear for v in shears)

            angles = [estimate_rotation_angle(s) for s in all_strokes]
            _, rot_resid = pool_rotation(angles)
            rot_res.extend(rot_resid)

            scales = [estimate_log_scale(s) for s in all_strokes]
            m_scale = float(np.mean(scales))
            scale_res.extend(v - m_scale for v in scales)

            min_k = min(len(s) for s in all_strokes)
            normed_list = [es.normalize_glyph(s)[0] for s in all_strokes]
            for k in range(min_k):
                vals = {"x": [], "y": [], "o": [], "s": []}
                for gi in range(len(all_strokes)):
                    px, py, po, ps = stroke_pose(normed_list[gi][k], angles[gi])
                    vals["x"].append(px)
                    vals["y"].append(py)
                    vals["o"].append(po)
                    vals["s"].append(ps)
                for dim in "xyos":
                    m = float(np.mean(vals[dim]))
                    pose_res[dim].extend(v - m for v in vals[dim])

    def _std(lst):
        return float(np.std(lst)) if lst else 0.0

    return dict(
        learn_alphabets=list(alphs), n_classes=n_classes, n_glyphs=n_glyphs,
        shear_std=_std(shear_res), n_shear_samples=len(shear_res),
        rotation_std=_std(rot_res), n_rotation_samples=len(rot_res),
        log_scale_std=_std(scale_res), n_scale_samples=len(scale_res),
        pose_x_std=_std(pose_res["x"]), pose_y_std=_std(pose_res["y"]),
        pose_o_std=_std(pose_res["o"]), pose_s_std=_std(pose_res["s"]),
        n_pose_samples=len(pose_res["x"]),
    )


def save_calibration(calib: dict, path: str) -> None:
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(calib, f, indent=1)


def load_calibration(path: str) -> dict:
    import json
    with open(path) as f:
        return json.load(f)


def calibrate_or_load(path: str, *, learn_n: int = DEFAULT_LEARN_N) -> dict:
    """PRE-REGISTRATION FREEZE: if `path` already exists, read it back VERBATIM (never
    recomputed, never adjusted) -- the mechanics `tests/test_exemplar_expand_migrated.py`'s own
    freeze test checks directly (write a sentinel file, confirm it comes back unchanged). Only
    computes+saves when the file is genuinely absent (the FIRST call of a fresh run)."""
    if os.path.exists(path):
        return load_calibration(path)
    calib = calibrate_background(learn_n=learn_n)
    save_calibration(calib, path)
    return calib


# ===================================================================================================
# VARIANT RENDERING -- deterministic, calibrated, writer-dims-only.
# ===================================================================================================
def _apply_rotation(strokes: list, angle: float) -> list:
    """Rotate every point (all strokes, jointly) by `angle` radians about their pooled
    centroid. Commutes exactly with the downstream `_normalize`'s own center+isotropic-scale
    (rotation about ANY point differs from rotation about the eventual normalized centroid by a
    pure translation, which normalization removes) -- an EXACT, not approximate, invariance."""
    if not strokes:
        return strokes
    allpts = np.concatenate([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes], axis=0)
    if allpts.shape[0] == 0:
        return [np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes]
    c = allpts.mean(axis=0)
    ca, sa = float(np.cos(angle)), float(np.sin(angle))
    R = np.array([[ca, -sa], [sa, ca]])
    out = []
    for s in strokes:
        arr = np.asarray(s, dtype=float).reshape(-1, 2)
        out.append((arr - c) @ R.T + c if arr.shape[0] else arr)
    return out


def _apply_shear(strokes: list, shear: float) -> list:
    """Inject `x' = x + shear*y` -- the ADDITIVE twin of `episode_style.canonicalize_strokes`'s
    own REMOVAL formula (`x' = x - shear*y`); same sign convention
    `tests/test_episode_style_migrated.py::_apply_shear` already establishes for injection.
    Applied directly to raw (un-centered) coordinates -- exact under downstream
    center+isotropic-scale normalization, per that module's own invariance note."""
    out = []
    for s in strokes:
        arr = np.asarray(s, dtype=float).reshape(-1, 2).copy()
        if arr.shape[0]:
            arr[:, 0] = arr[:, 0] + shear * arr[:, 1]
        out.append(arr)
    return out


def _apply_pose_jitter(strokes: list, d: float, calib: dict) -> list:
    """Per-STROKE deterministic pose perturbation (position + own-centroid rotation + own-
    centroid scale), sign alternating by draw-order stroke index (`i % 2`) so strokes do NOT
    all move the same way (a rigid whole-figure transform would be redundant with `rotation`/
    `shear` above) -- the calibrated magnitude for each of the four pose sub-dims comes straight
    from `calib` (`pose_x_std`/`pose_y_std`/`pose_o_std`/`pose_s_std`), scaled by `d` (already
    Z_QUANTILE-scaled by the caller). Missing calib keys default to 0.0 (an honest no-op for
    that sub-dim, never a crash)."""
    px_std = float(calib.get("pose_x_std", 0.0))
    py_std = float(calib.get("pose_y_std", 0.0))
    po_std = float(calib.get("pose_o_std", 0.0))
    ps_std = float(calib.get("pose_s_std", 0.0))
    out = []
    for i, s in enumerate(strokes):
        arr = np.asarray(s, dtype=float).reshape(-1, 2).copy()
        if arr.shape[0] == 0:
            out.append(arr)
            continue
        sign_i = 1.0 if (i % 2 == 0) else -1.0
        mag = sign_i * d
        c = arr.mean(axis=0)
        ang = mag * po_std
        ca, sa = float(np.cos(ang)), float(np.sin(ang))
        R = np.array([[ca, -sa], [sa, ca]])
        arr = (arr - c) @ R.T
        arr = arr * float(np.exp(mag * ps_std))
        arr = arr + c
        arr[:, 0] += mag * px_std
        arr[:, 1] += mag * py_std
        out.append(arr)
    return out


def render_variant(strokes: list, dim: str, sign: int, calib: dict, *,
                    z: float = Z_QUANTILE, quantize: bool = True,
                    grid: Optional[float] = None) -> list:
    """ONE calibrated variant of `strokes` (a list of raw, pre-normalization per-stroke point
    arrays -- the SAME `omniglot_world.load_strokes` return shape) along `dim` (one of
    `VARIANT_DIMS`) at `sign` (-1 or +1), magnitude `z * calib[<dim>_std]` (`z` defaults to
    `Z_QUANTILE`). `dim="combined"` applies rotation + shear + pose_jitter together, each at
    its OWN calibrated std, same `z*sign` multiplier. `quantize=True` (default -- the launch
    brief's own recommendation) additionally passes every stroke through `mouse_model.
    quantize_to_grid` so the rendered variant carries the SAME pixel-lattice sensor artifact a
    real corpus file has (comparing corpus-like ink to corpus-like ink, not a smooth synthetic
    to a quantized real file). Deterministic -- no RNG. Never mutates `strokes`."""
    if dim not in VARIANT_DIMS:
        raise ValueError(f"unknown variant dim {dim!r}, expected one of {VARIANT_DIMS}")
    out = [np.asarray(s, dtype=float).reshape(-1, 2).copy() for s in strokes]
    d = float(sign) * float(z)
    if dim in ("rotation", "combined"):
        out = _apply_rotation(out, d * float(calib.get("rotation_std", 0.0)))
    if dim in ("shear", "combined"):
        out = _apply_shear(out, d * float(calib.get("shear_std", 0.0)))
    if dim in ("pose_jitter", "combined"):
        out = _apply_pose_jitter(out, d, calib)
    if quantize:
        from domains import mouse_model as mm
        g = grid if grid is not None else mm.DEFAULT_GRID_PX
        out = [mm.quantize_to_grid(s, grid=g) for s in out]
    return out


def render_variant_set(strokes: list, calib: dict, *, grid_spec=VARIANT_GRID,
                        quantize: bool = True) -> list:
    """`[render_variant(strokes, dim, sign, calib, quantize=quantize) for (dim, sign) in
    grid_spec]` -- the FULL K-variant set for one candidate's raw strokes, in `grid_spec` order
    (index k in the returned list <-> `grid_spec[k]`, the convention the gate script's own
    `variant_key(path, k)` numbering relies on)."""
    return [render_variant(strokes, dim, sign, calib, quantize=quantize)
            for (dim, sign) in grid_spec]


# ===================================================================================================
# I/O REDIRECTION -- mechanical, mirrors `episode_style.StyleCanonFilter` exactly.
# ===================================================================================================
_VARIANT_KEY_SEP = "\x00variant"


def variant_key(path: str, k: int) -> str:
    """A SYNTHETIC key for candidate `path`'s k-th rendered variant -- contains a NUL byte, so
    it is provably never a real filesystem path (`os.path` / `open` would reject it outright),
    guaranteeing a variant key can never collide with, or accidentally disk-read, a real
    Omniglot motor file."""
    return f"{path}{_VARIANT_KEY_SEP}{k}"


class VariantStrokesFilter:
    """`with VariantStrokesFilter(variants_by_key): ...` -- for the life of the block,
    `domains.omniglot_world.load_strokes(key)` returns `variants_by_key[key]` directly (no disk
    read) when `key` is a registered synthetic `variant_key(...)`; every other (real) path
    passes through to the original loader unchanged. Exactly `episode_style.StyleCanonFilter`'s
    own monkeypatch idiom, substituting a full precomputed stroke list instead of a per-path
    style dict recomputed against a fresh real load."""

    def __init__(self, variants_by_key: dict):
        self.variants_by_key = variants_by_key

    def __enter__(self):
        import domains.omniglot_world as ow
        self._ow = ow
        self._orig = ow.load_strokes
        orig = self._orig
        variants_by_key = self.variants_by_key

        def _patched(path, *a, **kw):
            if path in variants_by_key:
                return variants_by_key[path]
            return orig(path, *a, **kw)

        ow.load_strokes = _patched
        return self

    def __exit__(self, *exc):
        self._ow.load_strokes = self._orig
        return False


__all__ = [
    "Z_QUANTILE", "VARIANT_DIMS", "VARIANT_GRID", "DEFAULT_LEARN_N",
    "estimate_rotation_angle", "pool_rotation", "estimate_log_scale", "stroke_pose",
    "calibrate_background", "save_calibration", "load_calibration", "calibrate_or_load",
    "render_variant", "render_variant_set", "variant_key", "VariantStrokesFilter",
]
