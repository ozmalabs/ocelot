"""ETA-SWEEP — the shared harness for the §2 / 8D confirmatory run.

THE QUESTION (8D, unanswered for three rungs)
----------------------------------------------
8D declared a §2 failure: *"there is NO eta at which the learning rule is both
CONVERGENT and LOAD-BEARING"* (5e-4 near-vacuous; higher eta moves the weights
but runs on). **That was measured on the BARE cortex — below model L (the
wave-isotropy rung) and WITHOUT a terminating settling loop.** The settling
layer is where GCAL's orientation actually comes from. Now it exists
(`seeds/vision_settle.json`, load-ordered BEFORE `vision_onoff` so the learning
rule reads a SETTLED sheet) and — with cycle detection (`w.detect_cycles`) — it
TERMINATES. This harness runs the developmental learning loop ON the settled
sheet and asks the 2x2 8D said is empty, per eta:

    (a) does the LEARNING converge?   drift(t) = ||w(t)-w(t-D)|| / ||w(t)|| -> 0
    (b) is it LOAD-BEARING?           Delta_OSI = OSI(trained) - OSI(untrained)
                                      above the SESOI, cells alive (n_dead=0)

and, because "orientation appeared" does NOT prove a mechanism (GCAL makes
orientation from ISOTROPIC DISKS, and the wave-isotropy rung measured the input
covariance's oriented eigenpair NEAR-DEGENERATE, lambda2/lambda3 = 1.0907, so the
preferred angle is predicted to be a COIN FLIP):

    (c) is the MAP STRUCTURED?        per-cell preferred orientation - is it
                                      spatially organised / across-seed
                                      reproducible, or an independent coin flip?

WHAT IS FIXED, AND WHY (no magic numbers, PROTOCOL §13)
-------------------------------------------------------
* SHEET: n_side=3, connectivity=8. SMALL BY NECESSITY: rho(M) -> 1 as the sheet
  grows (0.45 -> 0.87 over n_side 3->6), so a GCAL-scale sheet settles
  arbitrarily slowly REGARDLESS of termination. connectivity=8 is the
  non-bipartite sheet that actually settles (rho<1); connectivity=4 is bipartite
  (lambda_min=-1) and only terminates by round-off luck. Neither is tuned.
* SETTLING ON during development (settle=1.0, detect_cycles=True); OFF for the
  PROBE (settle=0.0). The probe is 8D's CALIBRATED instrument (IDEAL 0.9989,
  FLOOR 0.2691, n_dead 0), and it was calibrated in the NON-settling
  feedforward regime; probing with settling on would be an UNCALIBRATED
  instrument (PROTOCOL §5). The mechanism under test is the LEARNING rule
  reading a settled sheet; the probe reads the learned feedforward RF.
* develop_retina=3000 (rung 7's), train>=3200 (PROTOCOL §2's minimum horizon),
  eta is the SWEPT independent variable (PROTOCOL §4/§13 — declared in advance).
* The learning rule, the probe, theta adaptation: rung 6/7/8's committed
  machinery, REUSED unchanged (no seed edited; PROTOCOL §11.4).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import THETAS, cell_stats  # noqa: E402
from domains.lateral_world import set_lat_params  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from domains.settle_world import set_settle_params  # noqa: E402
from scripts.rung8_lib import PERIOD, develop_retina, freeze_all  # noqa: E402
from scripts.rung8b_lib import theta_of, weights_of  # noqa: E402
from scripts.rung8c_ensemble_transfer import adapt_theta_on_probe  # noqa: E402
from scripts.settle_lib import build_sheet  # noqa: E402

# --- FIXED design constants (declared; none tuned) --------------------------
N_SIDE = 3
CONNECTIVITY = 8
DEVELOP = 3000          # rung 7's retina fixed-point horizon
TRAIN = 3200            # PROTOCOL §2's minimum convergence horizon
DELTA = 200             # drift checkpoint window
ADAPT = 2000            # theta adaptation on the probe ensemble (rung 8C's)
SESOI = 0.0595          # rung 6's smallest OSI effect of interest, adopted


def _drift_trace(w, us, *, train, delta, eta):
    """Train the cortex on the settled sheet; checkpoint ||w|| and drift."""
    set_params(w, frozen=0.0, oo_eta=eta)
    if w.s.nodes("LatParams"):
        set_lat_params(w, frozen=1.0)          # only the cortex learns
    prev = np.asarray(weights_of(w, us), float)
    hist = []
    for t in range(1, train + 1):
        w.step(ignite_k=1 if t % 5 == 0 else 0)
        if t % delta == 0:
            cur = np.asarray(weights_of(w, us), float)
            nrm = float(np.linalg.norm(cur))
            drift = float(np.linalg.norm(cur - prev)) / (nrm if nrm > 0 else 1.0)
            hist.append((t, nrm, drift))
            prev = cur
    return hist


def arm(seed, eta, *, trained, n_side=N_SIDE, connectivity=CONNECTIVITY,
        develop=DEVELOP, train=TRAIN, delta=DELTA, adapt=ADAPT):
    """One arm on the SETTLING sheet. `trained=False` is eta-independent (the
    in-run OSI floor); `trained=True` runs the developmental learning loop.

    Returns per-cell OSI, per-cell preferred orientation + lattice position,
    n_dead, ||w|| init/final, the drift trajectory, and theta."""
    w, us, n_edges = build_sheet(seed=seed, n_side=n_side,
                                 connectivity=connectivity, settle=1.0,
                                 bubble=0.0, eta=eta, channels="lateral")
    w.detect_cycles = True                      # PROTOCOL §11.4 opt-in
    develop_retina(w, develop)                  # retina to fixed point, cortex inert
    w0 = np.asarray(weights_of(w, us), float)
    norm0 = float(np.linalg.norm(w0))
    hist = []
    if trained:
        hist = _drift_trace(w, us, train=train, delta=delta, eta=eta)
    w1 = np.asarray(weights_of(w, us), float)
    norm1 = float(np.linalg.norm(w1))
    dw = float(np.abs(w1 - w0).max())
    rel_move = float(np.linalg.norm(w1 - w0) / (norm0 if norm0 > 0 else 1.0))

    # PROBE — feedforward (settle=0), 8D's calibrated instrument.
    set_settle_params(w, settle=0.0)
    adapt_theta_on_probe(w, adapt)
    set_params(w, homeo=0.0)
    freeze_all(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    osi = np.asarray(st["osi"], float)
    pref = np.array([float(THETAS[int(np.argmax(tc[i]))]) for i in range(len(us))])
    alive = (tc > 1e-9).sum(axis=1)
    pos = np.array([[float(w.s.node(u)["attrs"]["cy"]),
                     float(w.s.node(u)["attrs"]["cx"])] for u in us])

    return {
        "seed": seed, "eta": eta, "trained": bool(trained),
        "osi": osi, "osi_mean": float(osi.mean()),
        "pref": pref, "pos": pos,
        "alive": alive.astype(int), "n_dead": int((alive == 0).sum()),
        "norm0": norm0, "norm1": norm1, "dw": dw, "rel_move": rel_move,
        "hist": hist, "theta": float(theta_of(w).mean()),
        "n_edges": int(n_edges), "n_cells": len(us),
    }


def drift_final_first(hist, *, tail=4, head=4):
    """(drift in the LAST `tail` windows, drift in the FIRST `head` windows).
    Convergence (§2) = the final drift falls toward 0 relative to the first."""
    if not hist:
        return 0.0, 0.0
    d = [x[2] for x in hist]
    return float(np.mean(d[-tail:])), float(np.mean(d[:head]))


# --------------------------------------------------------------------------- #
#  MAP STRUCTURE — orientation is defined mod 180, so every angle enters as a
#  unit vector at 2*theta. A "coin flip" is iid-uniform preferred orientation;
#  a MAP is spatial organisation (neighbours alike) and/or across-seed
#  reproducibility (a position prefers the same angle across seeds). Both
#  signatures are tested against a PERMUTATION null (PROTOCOL §4 — the unit of
#  analysis is the SEED).
# --------------------------------------------------------------------------- #
def _unit(pref_deg):
    a = np.radians(2.0 * np.asarray(pref_deg, float))
    return np.column_stack([np.cos(a), np.sin(a)])


def neighbour_similarity(pref_deg, pos, *, connectivity=CONNECTIVITY):
    """Mean cos(2*theta_i - 2*theta_j) over lattice-NEIGHBOUR cell pairs.
    High => neighbouring cells share orientation => a smooth/organised map."""
    v = _unit(pref_deg)
    P = np.asarray(pos, float)
    ys = sorted(set(P[:, 0]))
    xs = sorted(set(P[:, 1]))
    dy = min((b - a for a, b in zip(ys, ys[1:])), default=1.0) or 1.0
    dx = min((b - a for a, b in zip(xs, xs[1:])), default=1.0) or 1.0
    idx = {(round(P[i, 0]), round(P[i, 1])): i for i in range(len(P))}
    if connectivity == 4:
        offs = [(dy, 0), (0, dx)]
    else:
        offs = [(a * dy, b * dx) for a in (0, 1) for b in (-1, 0, 1)
                if (a, b) in [(0, 1), (1, -1), (1, 0), (1, 1)]]
    sims = []
    for (cy, cx), i in idx.items():
        for oy, ox in offs:
            j = idx.get((round(cy + oy), round(cx + ox)))
            if j is not None:
                sims.append(float(v[i] @ v[j]))
    return float(np.mean(sims)) if sims else 0.0


def neighbour_similarity_null(pref_deg, pos, *, connectivity=CONNECTIVITY,
                              n_perm=200, rng=None):
    """The same statistic under RANDOM permutation of preferred orientation
    across cell POSITIONS (destroys spatial structure, keeps the orientation
    histogram). The seed-level null for `neighbour_similarity`."""
    rng = rng or np.random.default_rng(0)
    pref = np.asarray(pref_deg, float)
    vals = np.empty(n_perm)
    for k in range(n_perm):
        vals[k] = neighbour_similarity(rng.permutation(pref), pos,
                                       connectivity=connectivity)
    return float(vals.mean()), float(vals.std())


def across_seed_R(pref_by_seed):
    """pref_by_seed: (n_seed, n_cell) preferred orientation in degrees, cells
    aligned by lattice position. Per position, the resultant length R of the
    doubled angles across seeds; returns the mean over positions. R->1 =>
    a position prefers the SAME angle across seeds (reproducible); R at the
    uniform floor => a coin flip."""
    A = np.asarray(pref_by_seed, float)
    n_seed = A.shape[0]
    Rs = []
    for c in range(A.shape[1]):
        v = _unit(A[:, c])
        Rs.append(float(np.linalg.norm(v.mean(axis=0))))
    return float(np.mean(Rs)), n_seed


def across_seed_R_null(pref_by_seed, *, n_perm=1000, rng=None):
    """The coin-flip null for `across_seed_R`. Per-position shuffling of seed
    labels is a NO-OP (R depends only on the multiset of angles at a position),
    so the null POOLS every angle over all seeds AND positions and reassigns at
    random, destroying position-specificity while KEEPING the overall
    orientation histogram (a global orientation bias is not position structure).
    Observed R > null => a position prefers a reproducible angle across seeds
    beyond any global bias."""
    rng = rng or np.random.default_rng(0)
    A = np.asarray(pref_by_seed, float)
    flat = A.reshape(-1)
    vals = np.empty(n_perm)
    for k in range(n_perm):
        S = rng.permutation(flat).reshape(A.shape)
        vals[k], _ = across_seed_R(S)
    return float(vals.mean()), float(vals.std())


def global_orientation_bias(pref_by_seed):
    """The resultant length of ALL preferred angles pooled (doubled). 0 => the
    orientation histogram is uniform (no global bias); ->1 => every cell prefers
    one angle. A WEAK structure signal, orthogonal to position-reproducibility;
    reported so a global bias is not mistaken for a map (nor a map missed)."""
    A = np.asarray(pref_by_seed, float).reshape(-1)
    v = _unit(A)
    return float(np.linalg.norm(v.mean(axis=0)))
