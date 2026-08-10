"""GATE — held surface: the SURFACE-level reconstruction BUILDS graph-natively
(seed block 180000; closes 179000 residual #1).

Pins, at the mechanism grain, the falsifiable facts of
VISION_HELD_SURFACE_PREREG.md, each ABLE TO FAIL on a flat curve or a frozen
surface:

  1. BUILD        — the persistent held-surface error (held vs true) drops toward
                    an asymptote as the graph rule `held_surface_accumulate`
                    EMA-integrates the noisy per-tick observation.
  2. ACCUMULATION — a STATELESS single-tick carve (the raw per-tick observation,
                    never integrated) stays FLAT above the denoised asymptote;
                    the held surface sits a clear factor below it. If the rule
                    stopped persisting the held surface across ticks, the
                    accumulating arm would look stateless and this gate FAILS.
  3. DECAY        — after the scene MOVES, the held surface UPDATES toward the new
                    content (object-permanence-WITH-forgetting), while a FROZEN
                    (lr=0-at-perturb) variant stays STUCK at the old content.

Self-contained and mechanical: it builds the eye, opts in to the held surface
(loads the additive `held_surface` seed + adds the config/cell nodes), ticks a
small (8x8) shot-noisy fixed scene, and reads `value`/`obs` attributes off the
`HeldSurfaceCell` nodes. The accumulation is the graph rule under `run_rules()`.
No agent decision, no Rust, no Term.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye              # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

NAZ = NEL = 8
LR = 0.15
L_BG, L_HI = 20, 200
BLOCK_A = (2, 6, 1, 4)     # rows 2..5, cols 1..3 — bright block in A
BLOCK_B = (2, 6, 4, 7)     # rows 2..5, cols 4..6 — block MOVED in B
ROD_NM = 498.0
T1, T2 = 30, 55
SEED = 180000


def _flat(c, r):
    return r * NAZ + c


def _scene(block):
    s = np.full((NEL, NAZ), L_BG, int)
    r0, r1, c0, c1 = block
    s[r0:r1, c0:c1] = L_HI
    return s


def _packets(scene, rng=None):
    out = []
    for r in range(NEL):
        for c in range(NAZ):
            lam = int(scene[r, c])
            cnt = int(rng.poisson(lam)) if rng is not None else lam
            if cnt > 0:
                out.append({"col": c, "row": r, "wavelength_nm": ROD_NM, "count": cnt})
    return out


def _make_eye(lr):
    eye = GraphEye(n_az=NAZ, n_el=NEL, adapt_rate=LR,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1, "onset_threshold_db": 6.0,
                            "onset_refractory_epochs": 0.0}).build()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("held_surface"), eye._agent)
    params = eye.substrate.add_node("HeldSurfaceParams", {"enabled": 1.0, "lr": float(lr)})
    inner.add_edge_unchecked(eye._retina, "has_held_surface_params", params)
    hs = {}
    for r in range(NEL):
        for c in range(NAZ):
            node = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0, "obs": 0.0, "row": r, "col": c,
                "cell_index": _flat(c, r), "epoch": 0.0})
            inner.add_edge_unchecked(eye._cells[_flat(c, r)], "has_held_surface_cell", node)
            hs[(c, r)] = node
    return eye, params, hs


def _tick(eye, scene, rng):
    eye.submit_photons_2d(_packets(scene, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _field(eye, hs, key):
    out = np.zeros((NEL, NAZ))
    for r in range(NEL):
        for c in range(NAZ):
            out[r, c] = float(eye.substrate.node(hs[(c, r)])["attrs"].get(key, 0.0))
    return out


def _err(est, truth):
    return float(np.mean(np.abs(est - truth)) / max(np.mean(truth), 1e-9))


def _true(block):
    eye, _p, hs = _make_eye(LR)
    _tick(eye, _scene(block), rng=None)
    t = _field(eye, hs, "obs")
    eye.stop()
    return t


def _run_arm(freeze):
    eye, params, hs = _make_eye(LR)
    rng = np.random.default_rng(SEED)
    held, obs = [], []
    for t in range(1, T2 + 1):
        if t == T1 + 1 and freeze:
            eye.substrate.set_attr(params, "lr", 0.0)
        _tick(eye, _scene(BLOCK_A) if t <= T1 else _scene(BLOCK_B), rng)
        held.append(_field(eye, hs, "value"))
        obs.append(_field(eye, hs, "obs"))
    eye.stop()
    return held, obs


_CACHE = {}


def _data():
    if "d" not in _CACHE:
        true_A, true_B = _true(BLOCK_A), _true(BLOCK_B)
        acc_held, acc_obs = _run_arm(freeze=False)
        fr_held, _ = _run_arm(freeze=True)
        acc_EA = [_err(acc_held[t], true_A) for t in range(T1)]
        sl_EA = [_err(acc_obs[t], true_A) for t in range(T1)]
        acc_EB = [_err(acc_held[t], true_B) for t in range(T1, T2)]
        fr_EB = [_err(fr_held[t], true_B) for t in range(T1, T2)]
        _CACHE["d"] = dict(acc_EA=acc_EA, sl_EA=sl_EA, acc_EB=acc_EB, fr_EB=fr_EB)
    return _CACHE["d"]


# --------------------------------------------------------------- HEADLINE 1 ----
def test_surface_build_curve_drops_toward_asymptote():
    d = _data(); b = d["acc_EA"]
    asymptote = float(np.mean(b[-3:]))
    assert asymptote < 0.12                         # denoised asymptote (able to fail flat)
    assert asymptote < 0.2 * b[0]                   # >=5x reduction, gist -> reconstruction


def test_stateless_control_is_flat_and_accumulation_gap_is_real():
    d = _data()
    sl = d["sl_EA"]; asymptote = float(np.mean(d["acc_EA"][-3:]))
    assert np.std(sl) / max(np.mean(sl), 1e-9) < 0.20     # single-tick carve FLAT (no build)
    assert np.mean(sl) > 1.8 * asymptote                  # sits above the denoised asymptote
    # THE ACCUMULATION SIGNAL — fails if the held surface stops persisting.
    assert asymptote < 0.6 * float(np.mean(sl))


# --------------------------------------------------------------- HEADLINE 2 ----
def test_decay_is_real_accumulating_follows_and_frozen_stays_stuck():
    d = _data()
    acc_B = d["acc_EB"]; fr_B = d["fr_EB"]
    tail_acc = float(np.mean(acc_B[-3:])); tail_fr = float(np.mean(fr_B[-3:]))
    assert tail_acc < 0.12                          # accumulating FOLLOWS the moved scene
    assert tail_acc < 0.4 * acc_B[0]                # error decreases across the perturb phase
    assert tail_fr > 0.4                            # FROZEN stays STUCK at the old content
    assert tail_acc < 0.3 * tail_fr                 # the gap IS the decay signal
