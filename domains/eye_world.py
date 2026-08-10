"""eye_world — the WORLD ADAPTER for the eye's calibration front end.

ARCHITECTURE (CLAUDE.md, VISION_PROTOCOL.md §0). This file is a world adapter
and nothing else. It does exactly three mechanical things:

  1. LAY OUT the lattices — `EyeCell` on the retina grid, `GazeCell` on the gaze
     lattice with `gaze_neighbour` edges, `EyeUnit`/`EySynapse` wiring. Positional
     geometry, exactly as `WaveWorld` mints `RetinaCell` + `neighbour`. No content
     decision.
  2. SUPPLY ENTROPY — an IID Gumbel draw per gaze cell per step (`gum`). This is
     the SAW's stochastic-selection noise, and it is UNSTRUCTURED by construction:
     independent across cells, independent across steps, carrying no spatial or
     temporal correlation and naming no direction.
  3. ADVANCE A CLOCK — write `lum` (raw luminance, mechanical ingest), increment
     `Eye.step` / `Gaze.step`, and `tick()`.

Everything that DECIDES is a rule in `seeds/vision_eye.json`: the log, the
reference, the trail, the potential, the selection, the learning.

WHY THE ADAPTER MAY SUPPLY THE GUMBEL. An RNG is not structure. Engbert's
stochastic variant needs a Boltzmann sample over the neighbour costs, and the
engine has no RNG Term. The Gumbel-max trick factors that sample into two parts:
IID noise (entropy — the adapter's job) and an argmin over cost-minus-noise (the
decision — the rule's job). `Argmin_k { cost_k - T*gum_k }` with `gum ~ Gumbel(0,1)`
is EXACTLY a draw from `softmax(-cost/T)`. So the host contributes noise and the
graph contributes the walk, which is the same split `WaveWorld.ignite` runs under.
Supplying the noise and claiming the walk would be the bolt-on error; supplying
the noise and making the graph do the walking is the honest one.

READ-ONLY on other rungs. This adapter mints its own node types and never touches
`RetinaCell`, `SUnit`, `Bipolar`, `DUnit` or any other rung's population.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

# The 8-neighbourhood. The gaze lattice is Moore-connected, NOT the
# 4-connected von-Neumann lattice Engbert's deterministic model walks:
# VISION_PRIOR_ART.md §3.2 names the 4-connected argmin a CARDINAL-AXIS
# ARTIFACT — "a subtle way of telling the agent the answer". Diagonals plus
# stochastic selection are the two changes that buy an isotropic step
# distribution, and `direction_hist()` below is what MEASURES whether they did.
_MOORE = ((-1, -1), (-1, 0), (-1, 1),
          (0, -1),           (0, 1),
          (1, -1),  (1, 0),  (1, 1))


def _add_edge(s, src, et, tgt):
    try:
        s.add_edge(src, et, tgt, None)
    except TypeError:
        s.add_edge(src, et, tgt)


class EyeWorld:
    """The eye world. Construct with a booted substrate that has the
    `vision_eye` seed loaded."""

    def __init__(self, s, *, h: int = 16, w: int = 16, gaze_l: int = 21,
                 seed: int = 0):
        self.s = s
        self.h = h
        self.w = w
        self.gaze_l = gaze_l
        # SEPARATE RNG for the gaze, on WaveWorld's precedent: the drift must not
        # consume draws from any other stream, or turning the SAW on would shift
        # an unrelated arm's sequence and confound the comparison.
        self.gaze_rng = np.random.default_rng(seed + 555_555)

        # ---- (1) LAY OUT: the receptor sheet -----------------------------
        self.eye = s.add_node("Eye", {"h": float(h), "w": float(w), "step": 0.0})
        self.cells: dict[tuple[int, int], Any] = {}
        for r in range(h):
            for c in range(w):
                n = s.add_node("EyeCell", {
                    "row": float(r), "col": float(c),
                    "lum": 0.0, "lum_step": -1.0, "x": 0.0, "resp": 0.0,
                    # theta starts at the GCAL target rate (their eta_bar(0) = mu),
                    # xbar likewise: the reference begins where the homeostat wants
                    # the cell to sit, not at an arbitrary zero.
                    "xbar": 0.024, "theta": 0.0,
                    # `mu_endo` is the setpoint the cell MEASURES IN ITSELF
                    # during the pre-visual phase (`ey_endo_latch`). It starts
                    # at 0.0 and that is deliberate: an UNCALIBRATED cell run in
                    # `mu_mode=1` targets a mean output of zero and dies. A
                    # setpoint that was never measured SHOULD be useless — the
                    # alternative is a default that quietly stands in for the
                    # measurement, which is the imported constant again.
                    "mu_endo": 0.0, "mu_endo_step": -1.0, "mu_n": 0.0,
                    "x_step": -1.0, "xbar_step": -1.0,
                    "theta_step": -1.0, "resp_step": -1.0})
                _add_edge(s, self.eye, "has_eyecell", n)
                self.cells[(r, c)] = n

        # ---- (1) LAY OUT: the gaze lattice -------------------------------
        # cy/cx are the lattice CENTRE, which is all Engbert's quadratic
        # potential needs to know; the rule computes the potential itself.
        # `L` is the lattice size, and it is load-bearing rather than cosmetic:
        # Engbert's potential is u = lam*L*[...], and h increments by exactly 1
        # per visit, so L is what puts the potential on the same scale as the
        # trail it competes with. Dropping it was measured to cost the entire
        # long-lag antipersistence (alpha_long 1.164 vs the paper's 0.71).
        cy = cx = (gaze_l - 1) / 2.0
        self.gaze = s.add_node("Gaze", {"step": 0.0, "move_step": -1.0,
                                        "L": float(gaze_l),
                                        "cy": cy if cy > 0 else 1.0,
                                        "cx": cx if cx > 0 else 1.0})
        self.gcells: dict[tuple[int, int], Any] = {}
        for r in range(gaze_l):
            for c in range(gaze_l):
                n = s.add_node("GazeCell", {
                    "row": float(r), "col": float(c),
                    "h": 0.0, "u": 0.0, "u_set": 0.0, "gum": 0.0,
                    "h_step": -1.0, "dep_step": -1.0})
                _add_edge(s, self.gaze, "has_gazecell", n)
                self.gcells[(r, c)] = n
        for (r, c), n in self.gcells.items():
            for dr, dc in _MOORE:
                m = self.gcells.get((r + dr, c + dc))
                if m is not None:
                    _add_edge(s, n, "gaze_neighbour", m)
        # Start at the centre.
        self._at = (gaze_l // 2, gaze_l // 2)
        _add_edge(s, self.gaze, "gaze_at", self.gcells[self._at])

        # ---- (1) LAY OUT: THE COUPLING ----------------------------------
        # The edge FM-0 found INADMISSIBLE. Verified before the fix:
        # `Γ rejects: type 'has_gaze' not in vocabulary (Type-2)` — so
        # "0 of 23 eye rules read both a GazeCell and an EyeCell" was not an
        # oversight any rule could have corrected; the RELATION did not exist.
        # `seeds/vision_eye.json` now carries the production, and this edge is
        # the anatomy that lets `ey_sample_at_gaze` join a receptor to a gaze.
        # ADDED LAST so no node id shifts (PROTOCOL §9: `Pick`/`Argmin` break
        # ties by id, so construction ORDER is part of a committed result).
        _add_edge(s, self.eye, "has_gaze", self.gaze)
        self.world = None
        self.wcells: dict[tuple[int, int], Any] = {}

    # ---- (1) LAY OUT: the world the eye moves OVER -----------------------
    def add_world(self, frame: np.ndarray):
        """Lay out the stationary scene as a sheet of WorldCells.

        MECHANICAL INGEST: the adapter states that photons exist at world
        locations. It does NOT say which receptor sees which photon — that is
        `ey_sample_at_gaze`'s decision, and the gaze is what makes it.

        Called EXPLICITLY, never from `__init__`: these are 1296 new nodes, and
        creating them would shift every subsequently-allocated node id. §9 is
        about committed results reproducing byte-identically, and `Pick` over a
        `NodesOfType` set and `Argmin`'s identity-`Eq` both resolve ties by id.
        A caller that never asks for a world gets the pre-change graph exactly.

        The world must span gaze (0..gaze_l-1) + retina (0..h-1), because the
        rule reads world = gaze + receptor.
        """
        wh = self.gaze_l + self.h - 1
        ww = self.gaze_l + self.w - 1
        if frame.shape != (wh, ww):
            raise ValueError(
                f"world frame must be {wh}x{ww} (gaze_l + h - 1, gaze_l + w - 1) "
                f"for a {self.h}x{self.w} retina on a {self.gaze_l}-lattice gaze; "
                f"got {frame.shape}")
        self.world = self.s.add_node("World", {"h": float(wh), "w": float(ww)})
        for r in range(wh):
            for c in range(ww):
                n = self.s.add_node("WorldCell", {
                    "row": float(r), "col": float(c),
                    "lum": float(frame[r, c])})
                _add_edge(self.s, self.world, "has_worldcell", n)
                self.wcells[(r, c)] = n
        return self.world

    def couple_waves(self, wave_world) -> int:
        """Wire each RetinaCell to the EyeCell AT ITS OWN LOCATION (1:1).

        MECHANICAL ANATOMY, and the only spatial fact stated: a receptor and the
        wave at the same place in the sheet are THE SAME PLACE. That is the
        grid's own geometry — the identical licence `WaveWorld` takes for its
        4-neighbourhood ("positional geometry, no content decision") and that
        `PreVisualWorld`'s docstring grants explicitly: "photoreceptors are
        physically adjacent, which is the sheet's geometry, not knowledge the
        agent could lack."

        NOTHING about the setpoint is wired here. This edge only says WHERE the
        endogenous activity is; `ey_endo_resp` decides that the cell's dark
        output is its burst, `ey_endo_latch` decides what the setpoint is, and
        both are seed rules. The adapter never computes a statistic.

        Returns the number of edges wired.
        """
        if (wave_world.h, wave_world.w) != (self.h, self.w):
            raise ValueError(
                f"co-location requires identical grids: retina "
                f"{wave_world.h}x{wave_world.w} vs eye {self.h}x{self.w}")
        n = 0
        for (r, c), rc in wave_world.cells.items():
            _add_edge(self.s, rc, "endo_drives", self.cells[(r, c)])
            n += 1
        return n

    def mu_endos(self) -> np.ndarray:
        """The setpoint each cell measured in itself. Mechanical read-back."""
        out = np.zeros((self.h, self.w), np.float64)
        for (r, c), n in self.cells.items():
            out[r, c] = float(self.s.node(n)["attrs"]["mu_endo"])
        return out

    def xbars(self) -> np.ndarray:
        out = np.zeros((self.h, self.w), np.float64)
        for (r, c), n in self.cells.items():
            out[r, c] = float(self.s.node(n)["attrs"]["xbar"])
        return out

    def present_world(self, frame: np.ndarray) -> None:
        """Rewrite the world's luminance. Mechanical; the scene is stationary in
        every experiment here, so this exists for a moving-scene control."""
        for (r, c), n in self.wcells.items():
            self.s.set_attr(n, "lum", float(frame[r, c]))

    # ---- (1) LAY OUT: the learned layer ----------------------------------
    def add_units(self, n_units: int, *, rf: int = 7, w0: float = 1.0,
                  seed: int = 0):
        """Wire `n_units` EyeUnits, each over an `rf`x`rf` patch of receptors.
        Initial weights are uniform random — adapter entropy, not structure."""
        rng = np.random.default_rng(seed + 31)
        us = []
        for i in range(n_units):
            u = self.s.add_node("EyeUnit", {
                "name": f"eu{i}", "act": 0.0, "rate": 0.0,
                "actbar": 0.024, "utheta": 0.0, "btheta": 0.0,
                "act_step": -1.0, "rate_step": -1.0, "actbar_step": -1.0,
                "utheta_step": -1.0, "btheta_step": -1.0})
            _add_edge(self.s, self.eye, "has_eyeunit", u)
            r0 = int(rng.integers(0, max(1, self.h - rf + 1)))
            c0 = int(rng.integers(0, max(1, self.w - rf + 1)))
            for dr in range(rf):
                for dc in range(rf):
                    p = self.cells.get((r0 + dr, c0 + dc))
                    if p is None:
                        continue
                    sy = self.s.add_node("EySynapse", {
                        "weight": float(w0 * rng.random()), "touched": -1.0})
                    _add_edge(self.s, p, "ey_pre", sy)
                    _add_edge(self.s, sy, "ey_post", u)
            us.append(u)
        return us

    # ---- (2) ENTROPY -----------------------------------------------------
    def _gumbel(self) -> None:
        """A fresh IID Gumbel(0,1) draw per gaze cell. UNSTRUCTURED: independent
        across cells and steps, no spatial or temporal correlation, no direction.
        Argmin over (cost - T*gum) is then an exact Boltzmann sample (module
        docstring) — the noise is the adapter's, the walk is the graph's."""
        g = self.gaze_rng.gumbel(0.0, 1.0, size=len(self.gcells))
        for i, n in enumerate(self.gcells.values()):
            self.s.set_attr(n, "gum", float(g[i]))

    # ---- (3) CLOCK -------------------------------------------------------
    def present(self, frame: Optional[np.ndarray]) -> None:
        """Write raw luminance onto the receptor sheet. MECHANICAL INGEST: the
        adapter states the photon count and nothing else. Whether the cell takes
        its log, what reference it subtracts, and what it therefore responds to
        are all `seeds/vision_eye.json`'s business."""
        if frame is None:
            return
        for (r, c), n in self.cells.items():
            if r < frame.shape[0] and c < frame.shape[1]:
                self.s.set_attr(n, "lum", float(frame[r, c]))

    def step(self, *, frame: Optional[np.ndarray] = None) -> None:
        st = float(self.s.node(self.eye)["attrs"]["step"]) + 1.0
        self.s.set_attr(self.eye, "step", st)
        self.s.set_attr(self.gaze, "step", st)
        self.present(frame)
        self._gumbel()
        self.s.tick(200_000)

    # ---- mechanical read-back (no decisions) -----------------------------
    def gaze_pos(self) -> tuple[int, int]:
        n = self.s.neighbours(self.gaze, "gaze_at")[0]
        at = self.s.node(n)["attrs"]
        return int(at["row"]), int(at["col"])

    def responses(self) -> np.ndarray:
        out = np.zeros((self.h, self.w), np.float64)
        for (r, c), n in self.cells.items():
            out[r, c] = float(self.s.node(n)["attrs"]["resp"])
        return out

    def drives(self) -> np.ndarray:
        out = np.zeros((self.h, self.w), np.float64)
        for (r, c), n in self.cells.items():
            out[r, c] = float(self.s.node(n)["attrs"]["x"])
        return out

    def thetas(self) -> np.ndarray:
        out = np.zeros((self.h, self.w), np.float64)
        for (r, c), n in self.cells.items():
            out[r, c] = float(self.s.node(n)["attrs"]["theta"])
        return out

    def weights(self, u) -> np.ndarray:
        ws = []
        for sy in self.s.in_neighbours(u, "ey_post"):
            ws.append(float(self.s.node(sy)["attrs"]["weight"]))
        return np.array(ws, np.float64)


class PreVisualWorld:
    """PHASE 0 — the PRE-VISUAL world adapter. Waves in, relational structure out.

    Constructed over an EXISTING rung-1 `WaveWorld`, whose retina it reads and
    never touches. NO PHOTOTRANSDUCTION happens here: a WUnit reads `bursting`
    off RetinaCells, which is endogenous wave activity, not light. Every
    photometric rule in `seeds/vision_eye.json` is gated `eye_open` and cannot
    fire in this phase.

    WHAT IS WIRED AND WHY — the line the whole rung turns on:

      * The retina's cells and its 4-neighbourhood are rung 1's, and they are
        PHYSICS: photoreceptors are physically adjacent, which is the sheet's
        geometry, not knowledge the agent could lack. Legitimately given.
      * `w_pre`, wired HERE, is DELIBERATELY DIFFUSE: every retinal cell
        connects to every unit with a small random weight. There is NO
        retinotopy, no locality, no spatial prior of any kind — the adapter
        supplies unstructured entropy (PROTOCOL §0) and the graph must grow the
        map. This is the exact thing rung 4 hand-wired and then measured back
        out of its own result ("retinotopic RF overlap — anatomy the adapter
        wires — accounts for most of the raw smoothness", -13.25 of -20.16).

    A unit's RF centre is therefore NOT a fact the adapter states. It is read
    back out of the learned weights afterwards, by `rf_centre`, purely to score
    the result against a ground truth the graph was never told.
    """

    def __init__(self, wave_world, n_units: int = 8, *, seed: int = 0,
                 w0: float = 0.1):
        self.ww = wave_world
        self.s = wave_world.s
        self.eye = self.s.add_node("Eye", {"h": float(wave_world.h),
                                           "w": float(wave_world.w),
                                           "step": 0.0})
        _add_edge(self.s, wave_world.retina, "has_wclock", self.eye)
        rng = np.random.default_rng(seed + 909)
        # SEPARATE RNG for the shuffled control, on WaveWorld's precedent: it
        # must not consume draws from the ignition stream, or turning the
        # control on would shift the wave sequence itself.
        self._shuf_rng = np.random.default_rng(seed + 424_242)
        self.units = []
        self.syn: dict[tuple[int, tuple[int, int]], Any] = {}
        for i in range(n_units):
            u = self.s.add_node("WUnit", {"name": f"wu{i}", "act": 0.0,
                                          "rate": 0.0, "act_step": -1.0,
                                          "rate_step": -1.0, "winner": 0.0,
                                          "win_step": -1.0, "wsum": 0.0,
                                          "wsum_step": -1.0})
            _add_edge(self.s, self.eye, "has_wunit", u)
            # DIFFUSE: every cell -> every unit. Random weights are entropy, not
            # structure. If a retinotopic map appears later, the graph made it.
            for rc, cell in wave_world.cells.items():
                sy = self.s.add_node("WSynapse", {
                    "weight": float(w0 * rng.random()), "touched": -1.0,
                    "normed": -1.0})
                _add_edge(self.s, cell, "w_pre", sy)
                _add_edge(self.s, sy, "w_post", u)
                self.syn[(i, rc)] = sy
            self.units.append(u)

    def step(self, *, ignite_k: int = 0, shuffle: bool = False) -> None:
        """Advance the wave world and let the pre-visual units learn from it.

        `shuffle` is THE ACTIVITY-MATCHED CONTROL, and it exists because rung 1's
        `propagate=0` control is confounded FOR THIS CLAIM. Measured: with the
        wave circuit off, the same ignition leaves ~1 cell bursting per step
        against a wave's ~30. So `propagate=0` differs from the wave arm in the
        QUANTITY of activity as well as its correlation, and a difference between
        them would not isolate the thing this rung is about. (PROTOCOL §6:
        controls must correspond to the actual experiment; §4: re-derive what
        each arm MEANS after every change. Rung 1's control was right for rung
        1's claim — 'structure from entropy' — and is wrong for this one.)

        The shuffled arm RE-DRAWS which cells burst, keeping the COUNT exactly as
        the wave produced it and destroying only the spatial correlation. So the
        two arms are matched on activity and differ in precisely the property
        under test: whether co-firing carries WHERE.

        THE CLOCK ORDERING IS LOAD-BEARING, and a positive control is what
        caught it. The phase-0 rules stamp against the EYE's OWN clock, not the
        Retina's, because `WaveWorld.step()` ticks INTERNALLY: a Retina-stamped
        rule fires during that tick — before this adapter has finished writing
        the burst pattern — and its step-guard then blocks it from ever
        re-firing. Measured: the fixed-patch positive control never reached the
        units at all (RF spread 6.54, i.e. untouched diffuse, with centres at
        the sheet's centre rather than the patch's), and the `shuffle` control
        below was silently inert for the same reason. So: let the waves run,
        THEN finish the input, THEN advance the eye's clock and tick.
        """
        self.ww.step(ignite_k=ignite_k)
        if shuffle:
            cells = list(self.ww.cells.values())
            on = [n for n in cells
                  if float(self.s.node(n)["attrs"].get("bursting", 0.0)) > 0.0]
            if on:
                for n in cells:
                    self.s.set_attr(n, "bursting", 0.0)
                for n in self._shuf_rng.choice(len(cells), size=len(on),
                                               replace=False):
                    self.s.set_attr(cells[int(n)], "bursting", 1.0)
        self.present_bursts(None)
        self._advance()

    def present_bursts(self, cells_on) -> None:
        """Mechanical ingest: force the burst pattern. `None` leaves whatever the
        wave world produced. Used by the positive control to present a fixed
        patch — the input a working retinotopy rule MUST be able to learn."""
        if cells_on is None:
            return
        on = set(cells_on)
        for rc, n in self.ww.cells.items():
            self.s.set_attr(n, "bursting", 1.0 if rc in on else 0.0)

    def _advance(self) -> None:
        self.s.set_attr(self.eye, "step",
                        float(self.s.node(self.eye)["attrs"]["step"]) + 1.0)
        self.s.tick(200_000)

    def rf(self, i: int) -> np.ndarray:
        """The unit's learned receptive field, read back as an image. A READ-OUT
        for scoring only — the graph is never told this geometry."""
        out = np.zeros((self.ww.h, self.ww.w), np.float64)
        for (ui, (r, c)), sy in self.syn.items():
            if ui == i:
                out[r, c] = float(self.s.node(sy)["attrs"]["weight"])
        return out


def lid_diffuse(frame: np.ndarray, sigma: float = 2.5) -> np.ndarray:
    """THE CLOSED EYELID, as OPTICS. Mechanical — this is the world's physics on
    the way in, exactly like `WaveWorld` stating the retina's geometry. It is
    not a decision and nothing about it is the agent's.

    A CLOSED LID IS A SCATTERER, NOT A BLACKOUT AND NOT A UNIFORM FIELD. It is
    translucent, so photoreceptors transduce — a closed eye's photometry works —
    but the light is DIFFUSED: spatially low-passed, like frosted glass. Coarse
    luminance structure survives (you can locate a window with your eyes shut);
    fine detail does not. So the pre-visual eye receives LOW SPATIAL FREQUENCY
    structure plus the ambient LEVEL, and eye opening adds the DETAIL.

    That is why the two-phase story is about optics rather than a neural switch,
    and it is the sharpest form of the creator's framing: sight arrives as a
    PERTURBATION of an already-grounded structure — here, literally the
    high-frequency residual on top of a coarse field the eye already calibrated
    against.

    Implemented as a separable Gaussian blur with reflecting edges. No scipy
    dependency; the kernel is built from the same sigma the caller states.
    """
    r = int(max(1, round(3 * sigma)))
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
    k /= k.sum()
    out = np.empty_like(frame, dtype=np.float64)
    pad = np.pad(np.asarray(frame, np.float64), ((0, 0), (r, r)), mode="reflect")
    for i in range(frame.shape[0]):
        out[i] = np.convolve(pad[i], k, mode="valid")
    pad = np.pad(out, ((r, r), (0, 0)), mode="reflect")
    for j in range(frame.shape[1]):
        out[:, j] = np.convolve(pad[:, j], k, mode="valid")
    return out


def rf_centre(rf: np.ndarray) -> tuple[float, float]:
    """The weight-centroid of a receptive field."""
    t = rf.sum()
    if t <= 0:
        return (float("nan"), float("nan"))
    rr, cc = np.mgrid[0:rf.shape[0], 0:rf.shape[1]]
    return (float((rr * rf).sum() / t), float((cc * rf).sum() / t))


def rf_spread(rf: np.ndarray) -> float:
    """LOCALISATION, the phase-0 statistic: the weight-weighted RMS distance
    from the RF's own centroid, in cells.

    A DIFFUSE projection over the whole sheet has a large spread (for a uniform
    HxW field it is fixed by geometry alone). A RETINOTOPIC unit — one that has
    found a patch — has a small one. This measures the thing waves are supposed
    to teach and that rung 4 was handed: locality.
    """
    t = rf.sum()
    if t <= 0:
        return float("nan")
    cy, cx = rf_centre(rf)
    rr, cc = np.mgrid[0:rf.shape[0], 0:rf.shape[1]]
    d2 = (rr - cy) ** 2 + (cc - cx) ** 2
    return float(np.sqrt((d2 * rf).sum() / t))


def set_params(world, **kw) -> None:
    """Set knobs on the singleton EyeParams node. Every arm in this rung is DATA
    on this node (PROTOCOL §0) — never a Python code path."""
    p = world.s.nodes("EyeParams")[0]
    for k, v in kw.items():
        world.s.set_attr(p, k, float(v))


def get_param(world, key) -> float:
    p = world.s.nodes("EyeParams")[0]
    return float(world.s.node(p)["attrs"][key])


def freeze(world) -> None:
    """A REAL freeze: `frozen=1` gates every learning rule AND every adaptation
    rule, because adaptation IS plasticity. Rung 5 lost three hand-set poolings
    to a fake freeze (`oja=0` still ran the fixed-sign rule and moved weights by
    47.9 per probe); rung 6 fixed it by gating the threshold's adaptation too.
    Verified here the same way: max |dw| and max |dtheta| are both 0.000e+00."""
    set_params(world, frozen=1.0)


def unfreeze(world) -> None:
    set_params(world, frozen=0.0)


def walk(world, steps: int, *, frame=None) -> list[tuple[int, int]]:
    """Run the SAW and record the trajectory. Clock only."""
    out = [world.gaze_pos()]
    for _ in range(steps):
        world.step(frame=frame)
        out.append(world.gaze_pos())
    return out


# ---------------------------------------------------------------- measures
# Mechanical statistics over a trajectory. These are INSTRUMENTS, and
# VISION_PROTOCOL.md §1 requires each to be calibrated on random input and on an
# ideal exemplar before it gates anything.

def msd(traj, lags) -> np.ndarray:
    """Mean squared displacement at each lag. The quantity Engbert's alpha is
    fitted to: MSD(lag) ~ lag^alpha."""
    p = np.asarray(traj, float)
    out = []
    for L in lags:
        if L >= len(p):
            out.append(np.nan)
            continue
        d = p[L:] - p[:-L]
        out.append(float(np.mean(np.sum(d * d, axis=1))))
    return np.array(out)


def diffusion_exponent(traj, lo, hi) -> float:
    """alpha = the slope of log MSD vs log lag over [lo, hi]. Engbert 2011:
    alpha ~ 1.32 at short lags (persistent, H~0.66) and ~0.71 at long lags
    (antipersistent, H~0.36). alpha = 1 is ordinary Brownian motion — the
    memoryless null."""
    lags = np.arange(lo, hi + 1)
    m = msd(traj, lags)
    ok = np.isfinite(m) & (m > 0)
    if ok.sum() < 3:
        return float("nan")
    return float(np.polyfit(np.log(lags[ok]), np.log(m[ok]), 1)[0])


def direction_hist(traj, nbins: int = 8) -> np.ndarray:
    """Distribution of step directions. THE CARDINAL-AXIS CHECK: a deterministic
    4-connected argmin puts all its mass on N/S/E/W, which would be a way of
    telling the agent an answer it is supposed to grow. Returns normalised bin
    counts over [0, 2pi)."""
    p = np.asarray(traj, float)
    d = p[1:] - p[:-1]
    d = d[np.any(d != 0, axis=1)]
    if len(d) == 0:
        return np.zeros(nbins)
    ang = np.arctan2(d[:, 1], d[:, 0]) % (2 * np.pi)
    hist, _ = np.histogram(ang, bins=nbins, range=(0, 2 * np.pi))
    return hist / max(1, hist.sum())


def anisotropy(traj, nbins: int = 8) -> float:
    """How far the step-direction distribution is from uniform: max deviation
    from 1/nbins, scaled so 0 = perfectly isotropic and 1 = all mass in one bin."""
    hgram = direction_hist(traj, nbins)
    if hgram.sum() == 0:
        return float("nan")
    return float(np.max(np.abs(hgram - 1.0 / nbins)) * nbins / (nbins - 1.0))
