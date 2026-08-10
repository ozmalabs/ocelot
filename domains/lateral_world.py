"""lateral_world — RUNG 7 world adapter: the retina's horizontal-cell anatomy.

ARCHITECTURE (CLAUDE.md). A WORLD ADAPTER and nothing else. It does exactly
three mechanical things, in the same split `wave_world.py` and `onoff_world.py`
already use:

  1. LAY OUT the anatomy — mint one `HCell` and two `LBipolar` (ON/OFF) per
     `RetinaCell`, and wire the radius-2 ring (`neighbour2`) exactly as
     `WaveWorld.__init__` wires the radius-1 ring (`neighbour`). Positional
     geometry: WHICH cells are adjacent is a fact about a grid. WHAT travels
     along those edges, whether anything does, and with what gain, is entirely
     the rules' business (`seeds/vision_lateral.json`).
  2. WRITE MECHANICAL FACTS — the per-cell neighbour COUNTS (`n_nb1`, `n_nb2`),
     which are pure grid geometry (edge cells have fewer neighbours), so the
     pooling rule can take a true MEAN at the boundary instead of fabricating a
     dark surround. Same class of fact as rung 6's `n_on`/`n_off`.
  3. READ BACK — pure queries (`channels`, `gains`, `residuals`).

NO DECISIONS. There is no `if lateral`, no `if learn_gain`, no `if radius2` in
this file: every ablation is DATA on the `LatParams` node that the RULES read
(PROTOCOL §0), and a source-grep gate in
`tests/test_vision_lateral_migrated.py` enforces it.

WHY `neighbour2` IS NOT THE ANSWER IN DISGUISE. The adapter states adjacency,
never influence. `g1`/`g2` initialise at `lat_g0 = 0.0` — the layer begins as a
PURE CENTRE with no surround whatsoever — and the centre-surround profile is
grown by `lat_learn_gain`. Handing over a DoG kernel (as
`substrate_rs/vision.py::lgn_pair` does, `origin="dog"`) is the bolt-on error
PROTOCOL §0 names; stating which cells touch which is the same fact rung 1
already stated and is what `wv_propagate` has run on since.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from domains.wave_world import WaveWorld, _add_edge

# The radius-2 ring under the same Manhattan metric the radius-1 ring uses
# (`WaveWorld` wires the 4-neighbourhood). The grid's own adjacency at the next
# distance out — no profile, no weighting, just who touches whom.
_RING2 = [(dr, dc) for dr in range(-2, 3) for dc in range(-2, 3)
          if abs(dr) + abs(dc) == 2]


# --------------------------------------------------------------------------- #
#  1 + 2. ANATOMY (mechanical geometry)
# --------------------------------------------------------------------------- #
def add_lateral_retina(world: WaveWorld) -> dict:
    """Mint the horizontal-cell + bipolar anatomy over an existing WaveWorld.

    Returns `{"hcells": {(r,c): nid}, "bipolars": {(r,c,pol): nid}}`.

    Wires, all of them positional facts about a grid:
        RetinaCell -neighbour2-> RetinaCell   (the radius-2 ring)
        Retina     -has_hcell->  HCell        (binds the clock for the rules)
        RetinaCell -pools_to->   HCell        (whose surround this HCell pools)
        Retina     -has_lbipolar-> LBipolar
        HCell      -rectifies_to-> LBipolar   (the residual this bipolar splits)

    `Retina -has_hcell->` and `RetinaCell -pools_to->` are DISTINCT edge types
    on purpose: two same-type incoming edges on one node is a recorded
    `run_rules` matching hazard in this tree.
    """
    s = world.s

    # The radius-2 ring — the same mechanical geometry statement WaveWorld makes
    # for the 4-neighbourhood, one distance further out. Symmetric, like the
    # radius-1 ring (each adjacency added once from each endpoint).
    for (r, c), n in world.cells.items():
        for dr, dc in _RING2:
            m = world.cells.get((r + dr, c + dc))
            if m is not None:
                _add_edge(s, n, "neighbour2", m)

    hcells: dict[tuple[int, int], Any] = {}
    bipolars: dict[tuple[int, int, int], Any] = {}
    for (r, c), cell in world.cells.items():
        # The neighbour COUNTS: pure grid geometry. Written here, not computed
        # by a second Fold, so a cell at the retina's edge pools a true MEAN
        # rather than dividing by a fixed divisor that would fabricate a dark
        # surround where the retina simply ends.
        n_nb1 = float(len(s.neighbours(cell, "neighbour")))
        n_nb2 = float(len(s.neighbours(cell, "neighbour2")))
        h = s.add_node("HCell", {
            "row": float(r), "col": float(c),
            "h1": 0.0, "h2": 0.0, "pool_step": -1.0,
            # STARTS AS A PURE CENTRE. The surround is grown, never installed.
            "g1": 0.0, "g2": 0.0, "gain_step": -1.0,
            "resid": 0.0, "resid_step": -1.0,
            "n_nb1": n_nb1, "n_nb2": n_nb2})
        _add_edge(s, world.retina, "has_hcell", h)
        _add_edge(s, cell, "pools_to", h)
        hcells[(r, c)] = h
        for pol in (1, -1):
            b = s.add_node("LBipolar", {
                "row": float(r), "col": float(c), "polarity": float(pol),
                "bursting": 0.0, "bstep": -1.0})
            _add_edge(s, world.retina, "has_lbipolar", b)
            _add_edge(s, h, "rectifies_to", b)
            bipolars[(r, c, pol)] = b
    return {"hcells": hcells, "bipolars": bipolars}


# --------------------------------------------------------------------------- #
#  3. THE FREEZE  (rung 6's lesson: `oja=0` IS NOT A FREEZE)
# --------------------------------------------------------------------------- #
def freeze_lateral(world: WaveWorld) -> None:
    """A REAL freeze of this seed's learning: `LatParams.frozen = 1`.

    ONE flag, carried in the `where` of every learning rule in
    `seeds/vision_lateral.json`, so no rule can learn while it is set regardless
    of which other rule is selected. Contrast `WaveParams.oja = 0`, which
    *enables* `bh_potentiate`/`bh_depress`/`bh_scale` — the trap that moved rung
    5's "frozen" weights by up to 47.9 per probe.

    Also pins the wave seed's plasticity the way `rung6_lib` does (`oja` stays
    SELECTED so the `bh_*` rules stay gated OFF, with `oja_eta = 0` making
    `oja_learn` an identity). Rung 7 mints no `Unit`/`Synapse` at all, so
    nothing there can move regardless; this is belt-and-braces so a probe is a
    probe.
    """
    for p in world.s.nodes("LatParams"):
        world.s.set_attr(p, "frozen", 1.0)
    for p in world.s.nodes("WaveParams"):
        world.s.set_attr(p, "oja", 1.0)      # keep bh_* gated OFF ...
        world.s.set_attr(p, "oja_eta", 0.0)  # ... and oja_learn an identity
        world.s.set_attr(p, "bcm", 0.0)


def thaw_lateral(world: WaveWorld) -> None:
    """Undo `freeze_lateral`'s LatParams flag only (mirrors onoff_world.thaw)."""
    for p in world.s.nodes("LatParams"):
        world.s.set_attr(p, "frozen", 0.0)


def set_lat_params(world: WaveWorld, **kw) -> None:
    """Blind-write floats onto the LatParams node. Mechanical: this function
    does not read, branch on, or interpret any flag — the RULES do."""
    for p in world.s.nodes("LatParams"):
        for k, v in kw.items():
            world.s.set_attr(p, k, float(v))


def install_gains(world: WaveWorld, hcells: dict, g1: float, g2: float) -> None:
    """Hand-set every horizontal cell's gains. FOR CALIBRATION AND CONTROLS
    ONLY — never a claim of emergence. This is how the ideal-DoG reference and
    the fixed-gain control are installed, exactly as rung 6's
    `install_signed_rf` installs its ideal split-Gabor reference."""
    for h in hcells.values():
        world.s.set_attr(h, "g1", float(g1))
        world.s.set_attr(h, "g2", float(g2))


# --------------------------------------------------------------------------- #
#  4. READ-OUT (pure query)
# --------------------------------------------------------------------------- #
def channels(world: WaveWorld, bipolars: dict) -> tuple[np.ndarray, np.ndarray]:
    """The (h, w) ON and OFF bipolar activity this step. Pure query."""
    on = np.zeros((world.h, world.w), np.float32)
    off = np.zeros((world.h, world.w), np.float32)
    for (r, c, pol), b in bipolars.items():
        v = float(world.s.node(b)["attrs"]["bursting"])
        (on if pol > 0 else off)[r, c] = v
    return on, off


def residuals(world: WaveWorld, hcells: dict) -> np.ndarray:
    """The (h, w) residual field `c - g1*h1 - g2*h2`. Pure query."""
    a = np.zeros((world.h, world.w), np.float32)
    for (r, c), h in hcells.items():
        a[r, c] = float(world.s.node(h)["attrs"]["resid"])
    return a


def gains(world: WaveWorld, hcells: dict) -> np.ndarray:
    """The (n_cells, 2) learned surround gains [g1, g2]. Pure query."""
    return np.array([[float(world.s.node(h)["attrs"]["g1"]),
                      float(world.s.node(h)["attrs"]["g2"])]
                     for h in hcells.values()], np.float64)


__all__ = ["add_lateral_retina", "freeze_lateral", "thaw_lateral",
           "set_lat_params", "install_gains", "channels", "residuals", "gains"]
