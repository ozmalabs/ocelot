"""cortex_sheet — RUNG 4 world adapter: the cortical sheet's geometry + the
map read-out.

ARCHITECTURE (CLAUDE.md). This is a WORLD ADAPTER and a pure READ-OUT. It does
exactly two mechanical things:

  1. LAY OUT the cortical sheet — mint Units at RETINOTOPIC receptive-field
     centres and wire `cortical_neighbour` edges. Positional geometry, exactly
     like `WaveWorld.__init__` wiring the retina's own 4-neighbourhood. No
     content decision: WHAT travels along a `cortical_neighbour` edge, and
     whether anything does, is `seeds/vision_maps.json`'s business
     (`vm_burst_lateral`), gated by `MapParams.lateral` — graph data.

  2. READ the map back out — a Unit's preferred orientation from its receptive
     field, and the smoothness of the resulting map. Pure query over graph
     state, exactly like `WaveWorld.receptive_field`.

WHY RETINOTOPY IS THE ADAPTER'S JOB AND NOT A CHEAT. Real V1 is retinotopic:
neighbouring cells look at neighbouring (heavily overlapping) parts of the
retina. That is anatomy — the wiring an animal is born with — not something a
learning rule discovers, and it is the same KIND of fact as the retina's grid
adjacency, which `wave_world` already states. Superimposed ON that retinotopy is
the ORIENTATION map, which is what rung 4 measures and what the graph must make.

The distinction matters for the honest reading of the result: because
cortical neighbours have overlapping receptive fields, they see partly-shared
input, so some map smoothness could arise WITHOUT any lateral interaction. That
is exactly why `lateral=0` is run as an arm rather than assumed null, and why
the pre-registered mechanism test is the INTERACTION (lateral ON vs OFF) and not
merely "ON beats its own shuffled null" (PROTOCOL 4: test the interaction, not
the simple effect, whenever the no-mechanism control is non-null).
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from domains.wave_world import WaveWorld, _add_edge


# --------------------------------------------------------------------------- #
#  1. GEOMETRY — the cortical sheet (mechanical wiring, no decisions)
# --------------------------------------------------------------------------- #
def retinotopic_centres(world: WaveWorld, gh: int, gw: int, *, rf: int = 7) -> list:
    """The (cy, cx) retinal centre for each of the `gh` x `gw` sheet positions,
    in row-major order. A linear (retinotopic) map from cortical position to
    retinal position, spanning the legal centre range for an `rf` x `rf`
    receptive field. Pure arithmetic."""
    half = rf // 2
    lo_y, hi_y = half, world.h - 1 - half
    lo_x, hi_x = half, world.w - 1 - half
    ys = (np.linspace(lo_y, hi_y, gh) if gh > 1
          else np.array([(lo_y + hi_y) / 2.0]))
    xs = (np.linspace(lo_x, hi_x, gw) if gw > 1
          else np.array([(lo_x + hi_x) / 2.0]))
    return [(int(round(ys[i])), int(round(xs[j])))
            for i in range(gh) for j in range(gw)]


def add_cortex(world: WaveWorld, gh: int, gw: int, *, rf: int = 7,
               w0: float = 1.0, jitter: float = 0.05,
               init: str = "multiplicative") -> list:
    """Mint a `gh` x `gw` cortical sheet of Units and wire it.

    Two mechanical facts, and only these two:

      * RETINOTOPY — unit (i, j) looks at retinal centre `retinotopic_centres`
        gives it. Anatomy; see the module docstring.
      * ADJACENCY — a 4-neighbourhood `cortical_neighbour` edge between sheet
        positions, the exact mirror of the retina's own 4-neighbourhood in
        `WaveWorld.__init__`. Symmetric (both directions wired), because
        cortical adjacency is symmetric.

    Units are minted by `WaveWorld.add_units` with the `centres` argument (a
    strictly-additive default-None parameter — `centres=None` keeps the
    committed random placement byte-identical), so the Unit/Synapse wiring is
    the SAME code the committed results ran through. Sheet position is stored on
    the Unit as `sheet_row`/`sheet_col` — an observed positional fact the
    read-out queries, never read by any rule.

    Returns the Units in row-major sheet order."""
    centres = retinotopic_centres(world, gh, gw, rf=rf)
    units = world.add_units(gh * gw, rf=rf, w0=w0, jitter=jitter,
                            centres=centres, init=init)
    grid: dict[tuple[int, int], Any] = {}
    for k, u in enumerate(units):
        i, j = divmod(k, gw)
        world.s.set_attr(u, "sheet_row", float(i))
        world.s.set_attr(u, "sheet_col", float(j))
        grid[(i, j)] = u
    for (i, j), u in grid.items():
        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            v = grid.get((i + di, j + dj))
            if v is not None:
                _add_edge(world.s, u, "cortical_neighbour", v)
    return units


def sheet_pairs(gh: int, gw: int) -> list:
    """The cortically-adjacent (index, index) pairs of a `gh` x `gw` sheet, each
    once. Row-major indices, matching `add_cortex`'s return order. The pairs the
    smoothness measure averages over — the same 4-neighbourhood `add_cortex`
    wires. Pure arithmetic."""
    out = []
    for i in range(gh):
        for j in range(gw):
            k = i * gw + j
            if i + 1 < gh:
                out.append((k, (i + 1) * gw + j))
            if j + 1 < gw:
                out.append((k, i * gw + (j + 1)))
    return out


# --------------------------------------------------------------------------- #
#  2. READ-OUT — preferred orientation + map smoothness (pure query)
# --------------------------------------------------------------------------- #
def _spectral_moment(rf_w: np.ndarray, n: int = 16) -> complex:
    """The power-weighted circular second moment of the receptive field's
    Fourier energy: Sum_k p_k * exp(2i*theta_k) / Sum_k p_k.

    This is EXACTLY the quantity `anisotropy` already returns the MAGNITUDE of
    (rung 1/2's committed readout). Rung 4 needs the PHASE of the same complex
    number, which is the orientation that energy is concentrated at. Using one
    moment for both keeps the map readout and the tuning readout commensurable
    rather than introducing a second, differently-behaved instrument."""
    g = np.asarray(rf_w, float)
    if g.ndim == 1:
        m = int(round(len(g) ** 0.5))
        g = g.reshape(m, m)
    g = g - g.mean()
    F = np.abs(np.fft.fftshift(np.fft.fft2(g, (n, n)))) ** 2
    yy, xx = np.mgrid[:n, :n]
    dy, dx = yy - n // 2, xx - n // 2
    r = np.hypot(dy, dx)
    m = r > 0.5
    th = np.arctan2(dy, dx)[m]
    p = F[m]
    if p.sum() <= 0:
        return 0j
    return complex((p * np.exp(2j * th)).sum() / p.sum())


def preferred_orientation(rf_w: np.ndarray) -> float:
    """A Unit's preferred orientation in DEGREES, in [0, 180).

    The phase of the receptive field's spectral second moment, halved. Pure
    query on the weights the rules made.

    HONEST SCOPE: this is the orientation the RF's Fourier energy is
    concentrated at, which is perpendicular to the orientation of the bar/edge
    the unit prefers. That is a CONSTANT offset applied to every unit alike, so
    it cannot affect any smoothness statistic (which reads only DIFFERENCES
    between units) — it is named so the absolute number is not misread as a
    bar angle."""
    z = _spectral_moment(rf_w)
    if z == 0:
        return 0.0
    return float(np.degrees(np.angle(z) / 2.0) % 180.0)


def orientation_selectivity(rf_w: np.ndarray) -> float:
    """The MAGNITUDE of the same moment — i.e. `anisotropy`, how strongly tuned
    the unit is. Reported alongside the map so a smooth map of untuned units
    cannot be mistaken for a result."""
    return float(abs(_spectral_moment(rf_w)))


def orientation_difference(a: float, b: float) -> float:
    """|a - b| for ORIENTATIONS (mod 180 degrees), in [0, 90].

    Orientation is an axial quantity: 179 degrees and 1 degree are 2 apart, not
    178. Getting this wrong would inflate every difference and flatter the null
    exactly as much as the data, so it is gated by a test."""
    d = abs(float(a) - float(b)) % 180.0
    return float(min(d, 180.0 - d))


def map_smoothness(thetas, pairs) -> float:
    """MEAN |delta preferred-orientation| over cortically-adjacent unit pairs,
    in degrees. LOWER = SMOOTHER = more map-like.

    Uniformly random orientations give 45 degrees in expectation (the mean of
    the axial difference of two uniform angles). A perfectly smooth map gives
    ~0. This is the rung-4 statistic."""
    ps = list(pairs)
    if not ps:
        return float("nan")
    return float(np.mean([orientation_difference(thetas[i], thetas[j])
                          for i, j in ps]))


def shuffled_null(thetas, pairs, *, n_perm: int = 200, seed: int = 0) -> float:
    """The smoothness expected if the SAME tuning values sat at RANDOM cortical
    positions: mean `map_smoothness` over `n_perm` random permutations.

    THE RIGHT NULL. Permuting positions destroys topography while holding the
    tuning DISTRIBUTION exactly fixed, so the comparison cannot be won by
    changing how tuned, how many, or how distributed the units are — only by
    where they SIT relative to each other. (An absolute threshold on
    `map_smoothness` would be won by any arm that made its units share one
    orientation, which is not a map.)"""
    th = np.asarray(thetas, float)
    rng = np.random.default_rng(seed)
    ps = list(pairs)
    return float(np.mean([map_smoothness(rng.permutation(th), ps)
                          for _ in range(n_perm)]))


def map_stats(world: WaveWorld, units, gh: int, gw: int, *,
              n_perm: int = 200, seed: int = 0) -> dict:
    """Read the whole map out of the graph. Pure query.

    `d` is the RUNG-4 STATISTIC: observed smoothness MINUS its shuffled-position
    null, in degrees. NEGATIVE = the map is smoother than chance = topography."""
    thetas = [preferred_orientation(world.receptive_field(u)) for u in units]
    sel = [orientation_selectivity(world.receptive_field(u)) for u in units]
    ps = sheet_pairs(gh, gw)
    obs = map_smoothness(thetas, ps)
    null = shuffled_null(thetas, ps, n_perm=n_perm, seed=seed)
    return {"smoothness": obs, "null": null, "d": obs - null,
            "thetas": thetas, "selectivity": float(np.mean(sel)),
            "n_pairs": len(ps)}


__all__ = ["retinotopic_centres", "add_cortex", "sheet_pairs",
           "preferred_orientation", "orientation_selectivity",
           "orientation_difference", "map_smoothness", "shuffled_null",
           "map_stats"]
