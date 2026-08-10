"""complex_cells — RUNG 5 world adapter: the pooling layer's geometry + the
phase-invariance read-out.

ARCHITECTURE (CLAUDE.md). WORLD ADAPTER and pure READ-OUT only. It does exactly
three mechanical things:

  1. LAY OUT the pooling layer — mint `CUnit` nodes and wire `cpre`/`cpost`
     CSynapses from a given set of simple `Unit`s. Positional/anatomical
     wiring, exactly like `cortex_sheet.add_cortex` wiring retinotopy. WHICH
     pooled unit ends up mattering is `seeds/vision_complex.json`'s business
     (`cx_learn`), gated by `ComplexParams` — graph data.

  2. PRESENT a probe stimulus — set the retina's bursts from a grating frame and
     advance the clock. Mechanical ingest, the same kind `WaveWorld.replay_step`
     does.

  3. READ the response back out — F1/F0 and OSI. Pure query.

No decisions: no conditional over graph state chooses what the agent does.

WHY THE PROBE PRESENTS EACH PHASE IN ISOLATION. `wv_unit_activate` counts any
retinal cell that burst within `window_steps` (=2), so a genuinely DRIFTING
presentation lets every unit integrate over three phases and EVERY unit looks
phase-invariant — the instrument would manufacture its own result. Each phase is
therefore presented as an independent static flash (`last_burst` set explicitly
for every cell), and F1/F0 is computed over the resulting phase-response
function. That IS the standard criterion (Skottun et al. 1991 compute the
modulation ratio of the response as a function of grating phase); it is only the
*presentation* that is discretised, and the discretisation is what keeps the
measure honest.

WHY THE READ-OUT RECTIFIES. A firing RATE is nonnegative. Without rectification
a true zero-mean Gabor's mean-over-phase is ~0, so F0 ~ 0, every tuning curve
collapses into noise and the instrument reports OSI=0 for a textbook simple
cell. This was found by the ideal-Gabor positive control BEFORE any gate was run
(PROTOCOL 1) — it is the instrument's single most load-bearing line.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from domains.wave_world import WaveWorld, _add_edge

THETAS = np.arange(0.0, 180.0, 15.0)


# --------------------------------------------------------------------------- #
#  1. GEOMETRY — the pooling layer (mechanical wiring, no decisions)
# --------------------------------------------------------------------------- #
def add_complex_layer(world: WaveWorld, pools, *, cw0: float = 1.0,
                      jitter: float = 0.05, seed: int = 0) -> list:
    """Mint one `CUnit` per entry of `pools` (a list of lists of Units) and wire
    each to the Units it pools via a `CSynapse`.

    WHICH units a CUnit may pool is ANATOMY the adapter wires — the same kind of
    fact as retinotopy in `cortex_sheet` — and it is named as such in the claim.
    What the pooling WEIGHTS become is `cx_learn`'s business. Initial weights are
    uniform `cw0` with a small symmetry-breaking jitter (a tie-break, not
    structure), exactly as `WaveWorld.add_units` does for the simple layer."""
    rng = np.random.default_rng(seed)
    s = world.s
    out = []
    for i, pool in enumerate(pools):
        cu = s.add_node("CUnit", {"name": f"c{i}", "cact": 0.0,
                                  "cact_step": -1.0, "trace": 0.0,
                                  "trace_step": -1.0})
        _add_edge(s, world.retina, "has_cunit", cu)
        for u in pool:
            cs = s.add_node("CSynapse", {
                "cweight": float(max(cw0 * (1.0 + jitter * rng.normal()), 1e-3)),
                "ctouched": -1.0})
            _add_edge(s, u, "cpre", cs)
            _add_edge(s, cs, "cpost", cu)
        out.append(cu)
    return out


def pool_weights(world: WaveWorld, cu, units) -> np.ndarray:
    """Read a CUnit's pooling weights back out, in the order of `units`. Pure
    query."""
    by_pre = {}
    for cs in world.s.in_neighbours(cu, "cpost"):
        pres = world.s.in_neighbours(cs, "cpre")
        if pres:
            by_pre[pres[0]] = float(world.s.node(cs)["attrs"]["cweight"])
    return np.array([by_pre.get(u, 0.0) for u in units], float)


# --------------------------------------------------------------------------- #
#  2. STIMULUS + PRESENTATION (mechanical)
# --------------------------------------------------------------------------- #
def grating(shape, theta_deg: float, phase: float, period: float = 4.0):
    """A zero-mean sinusoidal grating over an (h, w) field. Pure arithmetic."""
    h, w = shape
    yy, xx = np.mgrid[:h, :w]
    th = np.radians(theta_deg)
    proj = xx * np.cos(th) + yy * np.sin(th)
    return np.sin(2 * np.pi * proj / period + phase).astype(np.float32)


def binarize(g) -> np.ndarray:
    """The retina bursts where the grating exceeds its own median (0 for a
    zero-mean grating). The retina IS binary-bursting — this is what it sees."""
    return (np.asarray(g) > 0.0).astype(np.float32)


def present(world: WaveWorld, frame: np.ndarray, *, dstep: float = 10.0) -> float:
    """Present one frame in ISOLATION: set every cell's burst + last_burst from
    it, advance the clock past `window_steps`, and run the rules to fixpoint.

    Mechanical ingest. `last_burst` is set for EVERY cell (st for on, -999 for
    off) so no residue of the previous frame can leak through the unit's
    integration window — that isolation is what the measure's validity rests on.
    """
    s = world.s
    st = float(s.node(world.retina)["attrs"]["step"]) + dstep
    s.set_attr(world.retina, "step", st)
    for (r, c), n in world.cells.items():
        on = (r < frame.shape[0] and c < frame.shape[1] and frame[r, c] > 0.5)
        s.set_attr(n, "bursting", 1.0 if on else 0.0)
        s.set_attr(n, "last_burst", st if on else -999.0)
        s.set_attr(n, "state", "rested")
    for u in s.nodes("Unit"):
        s.set_attr(u, "bursting", 0.0)
    s.tick(200_000)
    return st


def freeze(world: WaveWorld) -> None:
    """FREEZE ALL LEARNING for the duration of a probe. Mechanical.

    THIS IS NOT `oja = 0`. The fixed-sign Butts rules (`bh_potentiate`,
    `bh_depress`) and homeostatic rescaling (`bh_scale`) are each gated on
    `WaveParams.oja == 0.0`, so setting oja=0 does not switch learning OFF — it
    switches the OTHER learning rule ON, and the probe then rewrites the WTA
    winner's synapses on every single presentation. Measured before this
    existed: a `cell_stats` probe moved the simple layer's weights by up to
    47.9 and drove three DIFFERENT hand-set pooling configurations (ideal /
    uniform / blob) to the SAME attractor, so they returned identical scores and
    the instrument was measuring its own learning rather than the units.

    The freeze therefore KEEPS oja selected (so bh_* stay gated off) and sets
    the rates to zero, which makes both update rules exact identities:
        oja_learn: w <- w*(1 - 0*y^2) + 0*y*x  ==  w
        cx_learn : likewise on cweight.
    """
    world.s.set_attr(world.s.nodes("WaveParams")[0], "oja", 1.0)
    world.s.set_attr(world.s.nodes("WaveParams")[0], "oja_eta", 0.0)
    world.s.set_attr(world.s.nodes("WaveParams")[0], "bcm", 0.0)
    for cp in world.s.nodes("ComplexParams"):
        world.s.set_attr(cp, "cx_eta", 0.0)


def _read(world: WaveWorld, nodes, key: str) -> np.ndarray:
    """RECTIFIED read-out: a firing rate is nonnegative. See the module
    docstring — this line is the instrument."""
    return np.array([max(float(world.s.node(n)["attrs"][key]), 0.0)
                     for n in nodes], float)


def phase_response(world: WaveWorld, nodes, theta: float, *, key: str = "act",
                   period: float = 4.0, K: int = 16) -> np.ndarray:
    """The (len(nodes), K) phase-response function at orientation `theta`."""
    out = np.zeros((len(nodes), K))
    for k in range(K):
        present(world, binarize(grating((world.h, world.w), theta,
                                        2 * np.pi * k / K, period)))
        out[:, k] = _read(world, nodes, key)
    return out


def baseline(world: WaveWorld, nodes, *, key: str = "act", n: int = 32,
             seed: int = 99) -> np.ndarray:
    """The response to UNSTRUCTURED fields at the SAME duty cycle (50% on) — the
    model's analogue of a SPONTANEOUS rate: what the node does when nothing
    oriented is present. Standard physiology computes F1/F0 on the EVOKED rate,
    i.e. above spontaneous."""
    rng = np.random.default_rng(seed)
    acc = np.zeros(len(nodes))
    for _ in range(n):
        present(world, (rng.random((world.h, world.w)) > 0.5).astype(np.float32))
        acc += _read(world, nodes, key)
    return acc / n


# --------------------------------------------------------------------------- #
#  3. THE MEASURES (pure functions)
# --------------------------------------------------------------------------- #
def f1f0(R) -> float:
    """The MODULATION RATIO of a phase-response function — the standard
    simple/complex criterion (Skottun et al. 1991):

        SIMPLE  cell: F1/F0 > 1   (response MODULATES with phase)
        COMPLEX cell: F1/F0 < 1   (responds throughout the cycle)

    R must be a nonnegative rate sampled over equally-spaced phases."""
    R = np.asarray(R, float)
    K = len(R)
    F0 = R.mean()
    if F0 <= 1e-9:
        return float("nan")
    ph = 2 * np.pi * np.arange(K) / K
    F1 = 2.0 * abs((R * np.exp(-1j * ph)).sum()) / K
    return float(F1 / F0)


def f1f0_evoked(R, base: float) -> float:
    """F1/F0 of the EVOKED response (above the baseline `baseline` measures)."""
    return f1f0(np.maximum(np.asarray(R, float) - float(base), 0.0))


def osi(tc) -> float:
    """(Rpref - Rorth)/(Rpref + Rorth) over an F0 tuning curve sampled on
    THETAS. A complex cell must be orientation-SELECTIVE — invariance achieved
    by losing tuning is not a complex cell, it is a blob."""
    tc = np.asarray(tc, float)
    j = int(np.argmax(tc))
    jo = (j + len(tc) // 2) % len(tc)
    a, b = tc[j], tc[jo]
    return float((a - b) / (a + b)) if (a + b) > 1e-9 else 0.0


def tuning_curve(world: WaveWorld, nodes, *, key: str = "act",
                 period: float = 4.0, K: int = 16) -> np.ndarray:
    """(len(nodes), len(THETAS)) — F0 (mean over phase) at each orientation."""
    out = np.zeros((len(nodes), len(THETAS)))
    for j, th in enumerate(THETAS):
        out[:, j] = phase_response(world, nodes, float(th), key=key,
                                   period=period, K=K).mean(axis=1)
    return out


def cell_stats(world: WaveWorld, nodes, *, key: str = "act",
               period: float = 4.0, K: int = 16) -> dict:
    """The full rung-5 read-out for a set of nodes. Pure query.

    Returns per-node `f1f0` (raw), `f1f0_evoked`, and `osi`, each measured at
    the node's OWN preferred orientation."""
    tc = tuning_curve(world, nodes, key=key, period=period, K=K)
    base = baseline(world, nodes, key=key)
    o = np.array([osi(tc[i]) for i in range(len(nodes))])
    raw, evo = [], []
    for i in range(len(nodes)):
        th = float(THETAS[int(np.argmax(tc[i]))])
        R = phase_response(world, nodes, th, key=key, period=period, K=K)[i]
        raw.append(f1f0(R))
        evo.append(f1f0_evoked(R, base[i]))
    return {"f1f0": np.array(raw), "f1f0_evoked": np.array(evo), "osi": o,
            "tuning": tc, "baseline": base}


# --------------------------------------------------------------------------- #
#  IDEAL REFERENCE CELLS — for calibrating the instrument (PROTOCOL 1)
# --------------------------------------------------------------------------- #
def gabor(rf: int, theta_deg: float, phase: float, period: float = 4.0,
          sigma: float = 2.0) -> np.ndarray:
    """A Gabor weight matrix. Used ONLY to calibrate the instrument and as the
    positive control's hand-installed simple-cell bank — never in an arm."""
    half = rf // 2
    yy, xx = np.mgrid[-half:half + 1, -half:half + 1]
    th = np.radians(theta_deg)
    xr = xx * np.cos(th) + yy * np.sin(th)
    env = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
    return (env * np.cos(2 * np.pi * xr / period + phase)).astype(np.float32)


def install_weights(world: WaveWorld, u, W_rf: np.ndarray) -> None:
    """Write a known weight matrix onto a Unit's synapses. Mechanical."""
    rf = int(world.s.node(u)["attrs"]["rf"])
    half = rf // 2
    for syn in world.s.in_neighbours(u, "post"):
        at = world.s.node(syn)["attrs"]
        world.s.set_attr(syn, "weight",
                         float(W_rf[int(at["drow"]) + half,
                                    int(at["dcol"]) + half]))


__all__ = ["THETAS", "add_complex_layer", "pool_weights", "grating", "binarize",
           "freeze", "present", "phase_response", "baseline", "f1f0", "f1f0_evoked",
           "osi", "tuning_curve", "cell_stats", "gabor", "install_weights"]
