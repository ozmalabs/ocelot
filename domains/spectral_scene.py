"""Mechanical 2-D photon scene generator for the colour 2-D eye (stage 4.2).

Graph-external, pure numpy.  Builds Mondrian scenes of ColorChecker patches
and turns them into integer photon packets ``{col, row, wavelength_nm, count}``
for ``GraphEye.submit_photons_2d``.  Cell indexing matches the eye: row-major,
``flat = row * n_az + col``; arrays here are shaped ``(n_el, n_az)``.

Physics is delegated to the frozen ``domains.spectral_forward`` (``sf``):

  per-cell SPD = scale_to_td(illuminant, scene_td) * gain(cell)
                 * reflectance(cell) * filter            (1 nm grid)
  packets      = sf.quantize(SPD, method, seed)        (column -> col,row)

which is exactly ``spd_from_recipe({'kind': 'scene', ...})`` of
``scripts/marys_room_broad_theory.py`` per cell, times an optional scalar gain.

This module decides nothing for the agent.  ``Mondrian.label_map`` and
``expected_catches`` are GROUND TRUTH / test oracles and must never be given
to the eye.  No tuned constants: the only numbers are the declared layout and
the 3% isoluminance criterion stated by the stage-4.2 brief.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from domains import spectral_forward as sf

STEP = 1  # every SPD here lives on the 1 nm grid (sf.grid(1), 391 bins)
BACKGROUND_ID = 0
DEFAULT_BACKGROUND = "neutral 5 (.70 D)"
ISOLUMINANCE_TOL = 0.03  # declared by the stage-4.2 brief (L+M under E)


# --------------------------------------------------------------------------
# spectrum resolution helpers
# --------------------------------------------------------------------------

def _wl() -> np.ndarray:
    return sf.grid(STEP)


def reflectance_spd(spec) -> np.ndarray:
    """Resolve a reflectance spec to an array on the 1 nm grid.
    None -> R == 1 (no surface); str/int -> ColorChecker patch via
    ``sf.reflectance``; array -> validated copy (length 391, >= 0)."""
    if spec is None:
        return np.ones(len(_wl()))
    if isinstance(spec, (str, int, np.integer)):
        return sf.reflectance(spec, STEP)
    arr = np.asarray(spec, dtype=float)
    if arr.shape != _wl().shape or np.any(arr < 0):
        raise ValueError(f"reflectance array must be non-negative, shape {_wl().shape}")
    return arr.copy()


def illuminant_spd(spec, td: float) -> np.ndarray:
    """Illuminant spec ('E' | 'D65' | 'A' | relative array) scaled to ``td``
    retinal troland with ``sf.scale_to_td`` (as spd_from_recipe 'scene')."""
    if isinstance(spec, str):
        rel = sf.illuminant(spec, STEP)
    else:
        rel = np.asarray(spec, dtype=float)
        if rel.shape != _wl().shape or np.any(rel < 0):
            raise ValueError(f"illuminant array must be non-negative, shape {_wl().shape}")
    return sf.scale_to_td(rel, td)


def filter_spd(spec) -> np.ndarray:
    """Pre-receptoral filter transmittance: None -> 1; 'eyelid' -> default
    eyelid OD; array -> as given; dict -> the broad-study recipe filter
    ({'kind': 'eyelid'|'lens'|'macular', ...}) via its frozen helper."""
    if spec is None:
        return np.ones(len(_wl()))
    if isinstance(spec, str):
        if spec.lower() == "eyelid":
            return sf.eyelid_transmittance(step=STEP)
        raise ValueError(f"unknown filter {spec!r}")
    if isinstance(spec, dict):
        from scripts.marys_room_broad_theory import filter_transmittance
        return filter_transmittance(spec, STEP)
    arr = np.asarray(spec, dtype=float)
    if arr.shape != _wl().shape or np.any(arr < 0):
        raise ValueError(f"filter array must be non-negative, shape {_wl().shape}")
    return arr


# --------------------------------------------------------------------------
# scenes
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Mondrian:
    """A flat 2-D scene of rectangular matte patches on a background.

    n_az, n_el: sheet size in cells (cols, rows).
    rects: sequence of ``(patch_id, reflectance, col0, row0, w, h)``;
      reflectance is a ColorChecker name/number, a 391-bin array, or None
      (R == 1).  patch_id must be a positive int, unique.  Later rects
      overwrite earlier ones; rects are clipped to the sheet.
    background: reflectance of cells no rect covers (patch id 0).
    """
    n_az: int
    n_el: int
    rects: tuple = ()
    background: object = DEFAULT_BACKGROUND

    def __post_init__(self):
        rects = tuple(tuple(r) for r in self.rects)
        object.__setattr__(self, "rects", rects)
        if self.n_az <= 0 or self.n_el <= 0:
            raise ValueError("sheet must be at least 1x1")
        ids = [r[0] for r in rects]
        if len(set(ids)) != len(ids) or any(int(i) <= BACKGROUND_ID for i in ids):
            raise ValueError("patch ids must be unique positive ints")
        for r in rects:
            if len(r) != 6 or int(r[4]) <= 0 or int(r[5]) <= 0:
                raise ValueError(f"bad rect {r!r}")

    # -- geometry -----------------------------------------------------------
    def label_map(self) -> np.ndarray:
        """int array (n_el, n_az) of patch ids (0 = background).  GROUND
        TRUTH ONLY -- never given to the eye."""
        lab = np.full((self.n_el, self.n_az), BACKGROUND_ID, dtype=int)
        for pid, _refl, c0, r0, w, h in self.rects:
            c0, r0, w, h = int(c0), int(r0), int(w), int(h)
            cs, ce = max(0, c0), min(self.n_az, c0 + w)
            rs, re = max(0, r0), min(self.n_el, r0 + h)
            if cs < ce and rs < re:
                lab[rs:re, cs:ce] = int(pid)
        return lab

    def patch_ids(self) -> list[int]:
        """Declared patch ids in rect order (excluding background)."""
        return [int(r[0]) for r in self.rects]

    def rect(self, patch_id: int) -> tuple:
        """The rect tuple of ``patch_id``."""
        for r in self.rects:
            if int(r[0]) == int(patch_id):
                return r
        raise KeyError(patch_id)

    def reflectance_of(self, patch_id: int):
        """The reflectance spec of ``patch_id`` (0 -> background)."""
        if int(patch_id) == BACKGROUND_ID:
            return self.background
        return self.rect(patch_id)[1]

    def reflectance_cube(self) -> np.ndarray:
        """float array (n_el, n_az, 391): reflectance of each cell."""
        lab = self.label_map()
        table = {pid: reflectance_spd(self.reflectance_of(pid))
                 for pid in [BACKGROUND_ID] + self.patch_ids()}
        cube = np.empty((self.n_el, self.n_az, len(_wl())))
        for pid, spd in table.items():
            cube[lab == pid] = spd
        return cube


def uniform(n_az: int, n_el: int, reflectance=None) -> Mondrian:
    """A surface-free field: every cell has the same reflectance (None -> R=1,
    i.e. the illuminant itself)."""
    return Mondrian(n_az, n_el, (), reflectance)


# Declared standard layout on a 24x16 sheet: 4x4 patches, one-cell background
# gutters, except the isoluminant pair (ids 6, 7) which share an edge.
# Background neutral 5.  Patches whose L+M catch under E is within 3% of the
# background (blue sky 0.9%, magenta 1.0%) are deliberately left out so every
# patch-background border carries a luminance edge; only the declared pair is
# isoluminant.
STANDARD_LAYOUT = (
    (1, "white 9.5 (.05 D)", 1, 1, 4, 4),
    (2, "red", 6, 1, 4, 4),
    (3, "green", 11, 1, 4, 4),
    (4, "blue", 16, 1, 4, 4),
    (5, "yellow", 1, 6, 4, 4),
    (6, "bluish green", 6, 6, 4, 4),     # isoluminant pair, cols 6-9 ...
    (7, "yellow green", 10, 6, 4, 4),    # ... adjacent at cols 10-13
    (8, "orange", 16, 6, 4, 4),
    (9, "purplish blue", 1, 11, 4, 4),
    (10, "dark skin", 8, 11, 4, 4),
)
STANDARD_WHITE_ID = 1
ISOLUMINANT_PAIR = (6, 7)
STANDARD_N_AZ, STANDARD_N_EL = 24, 16


def standard_mondrian(n_az: int = STANDARD_N_AZ, n_el: int = STANDARD_N_EL,
                      seed: int | None = None) -> Mondrian:
    """The declared standard Mondrian (STANDARD_LAYOUT, background neutral 5).

    seed=None: the declared assignment.  seed=int: a deterministic
    (np.random.default_rng(seed)) permutation of the reflectances among the
    slots other than the white reference (id 1) and the isoluminant pair
    (ids 6, 7), which keep their reflectances and adjacency.  The sheet may be
    larger than 24x16 (layout anchored at the origin), never smaller."""
    if n_az < STANDARD_N_AZ or n_el < STANDARD_N_EL:
        raise ValueError("standard Mondrian needs at least a 24x16 sheet")
    rects = [list(r) for r in STANDARD_LAYOUT]
    if seed is not None:
        fixed = {STANDARD_WHITE_ID, *ISOLUMINANT_PAIR}
        free = [i for i, r in enumerate(rects) if r[0] not in fixed]
        perm = np.random.default_rng(int(seed)).permutation(len(free))
        refls = [rects[i][1] for i in free]
        for k, i in enumerate(free):
            rects[i][1] = refls[int(perm[k])]
    return Mondrian(n_az, n_el, tuple(tuple(r) for r in rects), DEFAULT_BACKGROUND)


# --------------------------------------------------------------------------
# transforms (return new scenes)
# --------------------------------------------------------------------------

def swap_patches(scene: Mondrian, id_a: int, id_b: int) -> Mondrian:
    """Exchange the reflectances of patches ``id_a`` and ``id_b``; geometry
    (rects, z-order, label map) unchanged."""
    ra, rb = scene.reflectance_of(id_a), scene.reflectance_of(id_b)
    if BACKGROUND_ID in (int(id_a), int(id_b)):
        raise ValueError("cannot swap the background")
    new = []
    for r in scene.rects:
        if int(r[0]) == int(id_a):
            r = (r[0], rb) + tuple(r[2:])
        elif int(r[0]) == int(id_b):
            r = (r[0], ra) + tuple(r[2:])
        new.append(r)
    return replace(scene, rects=tuple(new))


def translate_patch(scene: Mondrian, patch_id: int, dcol: int, drow: int) -> Mondrian:
    """Move patch ``patch_id`` by (dcol, drow) cells, keeping its z-order.
    Vacated cells show whatever lies beneath (the background unless an
    earlier rect is there); parts moved off the sheet are clipped."""
    scene.rect(patch_id)  # KeyError if absent
    new = []
    for r in scene.rects:
        if int(r[0]) == int(patch_id):
            r = (r[0], r[1], int(r[2]) + int(dcol), int(r[3]) + int(drow), r[4], r[5])
        new.append(r)
    return replace(scene, rects=tuple(new))


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def _illum_cube(scene: Mondrian, illuminant, scene_td, illum_gain_map,
                illuminant_map) -> np.ndarray:
    """(n_el, n_az, 391) absolute illuminant per cell."""
    shape = (scene.n_el, scene.n_az)
    if illuminant_map is None:
        cube = np.broadcast_to(illuminant_spd(illuminant, scene_td),
                               shape + (len(_wl()),)).copy()
    else:
        idx, specs = illuminant_map
        idx = np.asarray(idx, dtype=int)
        if idx.shape != shape:
            raise ValueError(f"illuminant_map index must have shape {shape}")
        table = [illuminant_spd(s, scene_td) for s in specs]
        cube = np.stack([table[i] for i in idx.ravel()]).reshape(shape + (len(_wl()),))
    if illum_gain_map is not None:
        g = np.asarray(illum_gain_map, dtype=float)
        if g.shape != shape or np.any(g < 0):
            raise ValueError(f"illum_gain_map must be non-negative, shape {shape}")
        cube = cube * g[..., None]
    return cube


def cell_spds(scene: Mondrian, illuminant="E", scene_td: float = 100.0,
              filter=None, illum_gain_map=None, illuminant_map=None) -> np.ndarray:
    """(n_el, n_az, 391) absolute at-retina SPD of every cell:
    illuminant(scaled to scene_td) x gain x reflectance x filter.

    illum_gain_map: optional (n_el, n_az) scalar gain (neutral shadow).
    illuminant_map: optional ``(index_map (n_el, n_az) int, [illuminant
      specs])`` -- a per-cell illuminant (chromatic shadow); each listed
      illuminant is scaled to scene_td independently and it overrides
      ``illuminant``.  Gain applies on top."""
    ill = _illum_cube(scene, illuminant, scene_td, illum_gain_map, illuminant_map)
    return ill * scene.reflectance_cube() * filter_spd(filter)[None, None, :]


def _cell_seed(seed: int, flat: int) -> int:
    """Declared per-cell Poisson seed: SeedSequence([seed, flat])."""
    return int(np.random.SeedSequence([int(seed), int(flat)]).generate_state(1)[0])


def packets_from_spds(spds: np.ndarray, method: str = "cumulative",
                      seed: int | None = None) -> list[dict]:
    """Quantise a (n_el, n_az, 391) SPD cube with ``sf.quantize`` per cell,
    row-major; packets are ``{col, row, wavelength_nm, count}`` (zero bins
    omitted, so an all-zero cell is dark).  method='poisson' requires an
    explicit seed; cell ``flat`` uses ``_cell_seed(seed, flat)``."""
    n_el, n_az = spds.shape[:2]
    if method == "poisson" and seed is None:
        raise ValueError("poisson quantisation requires an explicit seed")
    out: list[dict] = []
    cache: dict = {}
    for row in range(n_el):
        for col in range(n_az):
            spd = spds[row, col]
            if method == "poisson":
                pk = sf.quantize(spd, method=method, seed=_cell_seed(seed, row * n_az + col))
            else:  # deterministic: identical SPDs give identical packets
                key = spd.tobytes()
                pk = cache.get(key)
                if pk is None:
                    pk = cache[key] = sf.quantize(spd, method=method)
            out.extend({"col": col, "row": row, "wavelength_nm": p["wavelength_nm"],
                        "count": p["count"]} for p in pk)
    return out


def render(scene: Mondrian, illuminant="E", scene_td: float = 100.0, filter=None,
           method: str = "cumulative", seed: int | None = None,
           illum_gain_map=None, illuminant_map=None) -> list[dict]:
    """One exposure of ``scene`` as packets for ``GraphEye.submit_photons_2d``.
    See ``cell_spds`` for the SPD and ``packets_from_spds`` for quantisation."""
    return packets_from_spds(
        cell_spds(scene, illuminant, scene_td, filter, illum_gain_map, illuminant_map),
        method=method, seed=seed)


def diffuse(n_az: int, n_el: int, illuminant="E", td: float = 100.0,
            filter="eyelid", method: str = "cumulative",
            seed: int | None = None) -> list[dict]:
    """Eyelid-like diffuse field: every cell receives the same SPD
    illuminant(td) x filter, no surfaces (R == 1)."""
    return render(uniform(n_az, n_el, None), illuminant, td, filter, method, seed)


def adapting_field(scene_or_uniform, wavelength_nm: float, quanta: int) -> list[dict]:
    """Monochromatic uniform adapting field: one packet
    ``{col, row, wavelength_nm, count=quanta}`` per cell (sf.monochromatic
    form).  ``scene_or_uniform``: a Mondrian (its size is used) or
    ``(n_az, n_el)``."""
    if isinstance(scene_or_uniform, Mondrian):
        n_az, n_el = scene_or_uniform.n_az, scene_or_uniform.n_el
    else:
        n_az, n_el = (int(v) for v in scene_or_uniform)
    if int(quanta) <= 0:
        return []
    return [{"col": c, "row": r, "wavelength_nm": p["wavelength_nm"], "count": p["count"]}
            for r in range(n_el) for c in range(n_az)
            for p in sf.monochromatic(wavelength_nm, int(quanta))]


# --------------------------------------------------------------------------
# schedules
# --------------------------------------------------------------------------

def illuminant_change(scene: Mondrian, illuminants, scene_td: float = 100.0,
                      **render_kw) -> list[list[dict]]:
    """One packet list per illuminant, same scene.  Poisson ``seed`` (if any)
    is offset by the exposure index so exposures are independent but
    reproducible."""
    seed = render_kw.pop("seed", None)
    return [render(scene, ill, scene_td,
                   seed=None if seed is None else int(seed) + k, **render_kw)
            for k, ill in enumerate(illuminants)]


def scene_sequence(scenes, illuminant="E", scene_td: float = 100.0,
                   **render_kw) -> list[list[dict]]:
    """One packet list per scene (swap / motion schedules), fixed light.
    Poisson seed offset per exposure as in ``illuminant_change``."""
    seed = render_kw.pop("seed", None)
    return [render(s, illuminant, scene_td,
                   seed=None if seed is None else int(seed) + k, **render_kw)
            for k, s in enumerate(scenes)]


def motion(scene: Mondrian, patch_id: int, steps, illuminant="E",
           scene_td: float = 100.0, **render_kw) -> list[list[dict]]:
    """Move ``patch_id`` along cumulative (dcol, drow) ``steps``; exposure 0
    is the unmoved scene, exposure k follows step k."""
    scenes, cur = [scene], scene
    for dc, dr in steps:
        cur = translate_patch(cur, patch_id, dc, dr)
        scenes.append(cur)
    return scene_sequence(scenes, illuminant, scene_td, **render_kw)


# --------------------------------------------------------------------------
# oracles (tests / reporting only -- never given to the eye)
# --------------------------------------------------------------------------

def _gauss(receptor: str) -> np.ndarray:
    c, bw, _half, _dark = sf.EYE_RECEPTORS[receptor]
    return np.exp(-0.5 * ((_wl() - c) / bw) ** 2)


def catches_of_spd(spd) -> dict:
    """Expected (continuous, dark-free) catches of one SPD:
    sum_l sf.expected_quanta(spd) * exp(-0.5((l-c)/bw)^2) for l, m, s, rod,
    plus 'lm' = l + m."""
    q = sf.expected_quanta(spd)
    out = {r: float(q @ _gauss(r)) for r in ("l", "m", "s", "rod")}
    out["lm"] = out["l"] + out["m"]
    return out


def expected_catches(scene: Mondrian, illuminant="E", td: float = 100.0,
                     filter=None, illum_gain_map=None, illuminant_map=None) -> dict:
    """Per-cell expected catches, dict receptor -> float (n_el, n_az) array
    for 'l', 'm', 's', 'rod', 'lm'.  Gaussian sensors of sf.EYE_RECEPTORS on
    sf.expected_quanta; dark current excluded.  TEST ORACLE ONLY."""
    spds = cell_spds(scene, illuminant, td, filter, illum_gain_map, illuminant_map)
    q = spds * (sf.QUANTA_SCALE * STEP * _wl() / sf.LAMBDA_REF_NM)[None, None, :]
    out = {r: q @ _gauss(r) for r in ("l", "m", "s", "rod")}
    out["lm"] = out["l"] + out["m"]
    return out


def patch_report(scene: Mondrian, illuminant="E", td: float = 100.0) -> list[dict]:
    """Per patch (background first): reflectance, rect, expected L+M catch and
    the eye_capture_model red_green / blue_yellow of its quantised packets."""
    ill = illuminant_spd(illuminant, td)
    rows = []
    for pid in [BACKGROUND_ID] + scene.patch_ids():
        spd = ill * reflectance_spd(scene.reflectance_of(pid))
        m = sf.eye_capture_model(sf.quantize(spd))
        rows.append({"patch_id": pid, "reflectance": scene.reflectance_of(pid),
                     "rect": None if pid == BACKGROUND_ID else tuple(scene.rect(pid)[2:]),
                     "lm": catches_of_spd(spd)["lm"],
                     "red_green": m["red_green"], "blue_yellow": m["blue_yellow"]})
    return rows


# --------------------------------------------------------------------------
# independent random Mondrians (stage-4 replication amendment A1)
# --------------------------------------------------------------------------
# ADDITIVE ONLY: nothing above this line is changed.  The stage-4 held-out
# layouts (standard_mondrian(seed=k)) permute reflectances among fixed,
# gutter-separated slots, and the pipeline is invariant to that (stage-4
# results, "Anomaly").  These generators draw the geometry itself.
#
# Declared rules (no tuned constants; every number is stated by amendment A1):
#   * patch count n ~ U{6..12}; each rect has w, h ~ U{3..7} and a uniform
#     position fully on the sheet; no gutters, so patches may abut or overlap;
#     later rects overwrite earlier ones (Mondrian.label_map is the final
#     visible label map);
#   * reporting-unit constraint: in the final label map every label (each
#     patch AND the background) is non-empty and 4-connected.  A rect that
#     would break this for any label is redrawn (same rng stream), so each
#     declared patch is one connected visible region;
#   * random_mondrian: background ~ U(neutrals 19-24); white 9.5 (patch 19)
#     is a patch iff seed is even, and then never the background; the other
#     patch reflectances are drawn without replacement from the remaining
#     ColorChecker patches, and a draw equal to the background is redrawn;
#     white's z-order slot is uniform;
#   * neutral_mondrian: the SAME geometry as random_mondrian(seed) (the
#     geometry is the first thing drawn from default_rng(seed)); background ~
#     U(neutrals 19-24); every patch ~ U(the five other neutrals), with
#     replacement (6..12 patches cannot be drawn without replacement from 5).

RANDOM_N_PATCHES = (6, 12)          # inclusive
RANDOM_SIDE = (3, 7)                # inclusive, for w and h
NEUTRAL_NUMBERS = (19, 20, 21, 22, 23, 24)
WHITE_NUMBER = 19
RANDOM_MAX_TRIES = 10000            # redraws per rect before giving up (raise)


def colorchecker_name(number: int) -> str:
    """ColorChecker patch name of 1-based ``number`` (19 = white 9.5)."""
    return sf.reflectance_names()[int(number) - 1]


def _four_connected(mask: np.ndarray) -> bool:
    """True iff the True cells of ``mask`` are non-empty and 4-connected."""
    cells = np.argwhere(mask)
    if len(cells) == 0:
        return False
    seen = {tuple(cells[0])}
    stack = [tuple(cells[0])]
    n_el, n_az = mask.shape
    while stack:
        r, c = stack.pop()
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= rr < n_el and 0 <= cc < n_az and mask[rr, cc] and (rr, cc) not in seen:
                seen.add((rr, cc))
                stack.append((rr, cc))
    return len(seen) == len(cells)


def _geometry_label_map(n_az: int, n_el: int, geom) -> np.ndarray:
    return Mondrian(n_az, n_el, tuple((pid, None, c0, r0, w, h)
                                      for pid, c0, r0, w, h in geom)).label_map()


def _labels_ok(lab: np.ndarray, n_patches: int) -> bool:
    return all(_four_connected(lab == pid) for pid in range(BACKGROUND_ID, n_patches + 1))


def _random_geometry(rng: np.random.Generator, n_az: int, n_el: int) -> list[tuple]:
    """``[(pid, col0, row0, w, h), ...]`` in z-order (rng: default_rng(seed),
    consumed first: n, then per rect w, h, col0, row0 with redraws)."""
    lo_s, hi_s = RANDOM_SIDE
    if n_az < hi_s or n_el < hi_s:
        raise ValueError(f"random Mondrian needs a sheet of at least {hi_s}x{hi_s}")
    n = int(rng.integers(RANDOM_N_PATCHES[0], RANDOM_N_PATCHES[1] + 1))
    geom: list[tuple] = []
    for pid in range(1, n + 1):
        for _ in range(RANDOM_MAX_TRIES):
            w = int(rng.integers(lo_s, hi_s + 1))
            h = int(rng.integers(lo_s, hi_s + 1))
            c0 = int(rng.integers(0, n_az - w + 1))
            r0 = int(rng.integers(0, n_el - h + 1))
            cand = geom + [(pid, c0, r0, w, h)]
            if _labels_ok(_geometry_label_map(n_az, n_el, cand), pid):
                geom = cand
                break
        else:
            raise RuntimeError(f"no valid placement for rect {pid} after "
                               f"{RANDOM_MAX_TRIES} draws")
    return geom


def random_mondrian(seed: int, n_az: int = STANDARD_N_AZ,
                    n_el: int = STANDARD_N_EL) -> Mondrian:
    """A genuinely independent random Mondrian (amendment A1), deterministic
    from ``np.random.default_rng(seed)``.  Rules: see the block comment above.
    Patch ids 1..n in z-order; background id 0."""
    seed = int(seed)
    rng = np.random.default_rng(seed)
    geom = _random_geometry(rng, n_az, n_el)
    n = len(geom)
    names = sf.reflectance_names()
    white = colorchecker_name(WHITE_NUMBER)
    white_in = seed % 2 == 0
    neutrals = [colorchecker_name(k) for k in NEUTRAL_NUMBERS]
    bg_choices = [x for x in neutrals if not (white_in and x == white)]
    background = bg_choices[int(rng.integers(0, len(bg_choices)))]
    pool = [x for x in names if x != white]
    refls: list[str] = []
    for i in rng.permutation(len(pool)):          # without replacement
        if len(refls) == n - int(white_in):
            break
        if pool[int(i)] == background:            # equal to background -> redraw
            continue
        refls.append(pool[int(i)])
    if white_in:
        refls.insert(int(rng.integers(0, n)), white)
    rects = tuple((pid, refl, c0, r0, w, h)
                  for (pid, c0, r0, w, h), refl in zip(geom, refls))
    return Mondrian(n_az, n_el, rects, background)


def neutral_mondrian(seed: int, n_az: int = STANDARD_N_AZ,
                     n_el: int = STANDARD_N_EL) -> Mondrian:
    """The achromatic room for ``seed`` (amendment A1): the geometry of
    ``random_mondrian(seed)``; background ~ U(neutrals 19-24); each patch ~
    U(the five neutrals other than the background), with replacement."""
    rng = np.random.default_rng(int(seed))
    geom = _random_geometry(rng, n_az, n_el)
    neutrals = [colorchecker_name(k) for k in NEUTRAL_NUMBERS]
    background = neutrals[int(rng.integers(0, len(neutrals)))]
    others = [x for x in neutrals if x != background]
    rects = tuple((pid, others[int(rng.integers(0, len(others)))], c0, r0, w, h)
                  for pid, c0, r0, w, h in geom)
    return Mondrian(n_az, n_el, rects, background)
