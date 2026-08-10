"""GATE — splat over time: the eye BUILDS a fixed scene (seed block 179000).

Pins, at the mechanism grain, the four falsifiable facts of
VISION_SPLAT_OVER_TIME_PREREG.md, each ABLE TO FAIL on a true flat curve:

  1. BUILD        — accumulating reconstruction error drops toward an asymptote.
  2. ACCUMULATION — a stateless (fresh-eye-per-tick) control stays FLAT, and the
                    accumulating end-error is a large factor below it. THIS is
                    the accumulation signal: if the eye stopped persisting its
                    adapting floor across ticks, the accumulating arm would look
                    like the stateless arm and this gate would FAIL.
  3. COST-BEND    — per-tick compute (onset-event count) drains as the scene
                    grounds, and a BRIGHTENING perturbation re-raises it.
  4. FOVEA        — the re-raised compute localizes to the perturbed patch
                    (implicit sharpening ≡ explicit spent-looks).

Self-contained and mechanical: it ticks the eye on a fixed stimulus, reads
`adaptation`/`caught_quanta` attributes, and counts `RetinalOnsetEvent` nodes.
No agent decision, no Rust, no Term. Small retina (8×8) for speed.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye  # noqa: E402

NAZ = NEL = 8
R = 0.15
L_BG, L_HI = 20, 200
BLOCK = (2, 6, 1, 4)     # rows 2..5, cols 1..3 — bright block
PATCH = (1, 4, 5, 8)     # rows 1..3, cols 5..7 — dim in A, brightened in B
ROD_NM = 498.0


def _scene(perturb=False):
    s = np.full((NEL, NAZ), L_BG, int)
    r0, r1, c0, c1 = BLOCK
    s[r0:r1, c0:c1] = L_HI
    if perturb:
        p0, p1, q0, q1 = PATCH
        s[p0:p1, q0:q1] = L_HI
    return s


def _patch_cells():
    p0, p1, q0, q1 = PATCH
    return {(c, r) for r in range(p0, p1) for c in range(q0, q1)}


def _packets(scene):
    return [{"col": c, "row": r, "wavelength_nm": ROD_NM, "count": int(scene[r, c])}
            for r in range(NEL) for c in range(NAZ) if scene[r, c] > 0]


def _make_eye(adapt_rate=R):
    return GraphEye(n_az=NAZ, n_el=NEL, adapt_rate=adapt_rate,
                    context={"retina_2d": True, "synchronous": True,
                             "worker_capacity": 1, "onset_threshold_db": 6.0,
                             "onset_refractory_epochs": 0.0}).build()


def _tick(eye, scene):
    eye.submit_photons_2d(_packets(scene))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _fields(eye):
    a = np.zeros((NEL, NAZ)); c = np.zeros((NEL, NAZ))
    for r in range(NEL):
        for col in range(NAZ):
            rod = eye._receptors[(r * NAZ + col, "rod")]
            at = eye.substrate.node(rod)["attrs"]
            a[r, col] = float(at.get("adaptation", 0.0))
            c[r, col] = float(at.get("caught_quanta", 0.0))
    return a, c


def _err(a, c):
    return float(np.mean(np.abs(a - c)) / max(np.mean(c), 1e-9))


def _onset_cells(eye, epoch):
    out = []
    for nid in eye.substrate.nodes("RetinalOnsetEvent"):
        at = eye.substrate.node(nid)["attrs"]
        if "row_index" in at and int(round(float(at["epoch"]))) == int(epoch):
            out.append((int(at["column_index"]), int(at["row_index"])))
    return out


def _run():
    """One accumulating run (build 12 ticks on A, perturb ticks 13-16 on B) plus
    a stateless control. Cached across the assertions in this module."""
    T1, T2 = 16, 20
    eye = _make_eye()
    E, C, cells = [], [], []
    for t in range(1, T2 + 1):
        _tick(eye, _scene(perturb=(t > T1)))
        a, c = _fields(eye)
        E.append(_err(a, c)); C.append(len(_onset_cells(eye, t)))
        cells.append(_onset_cells(eye, t))
    eye.stop()
    # stateless control — fresh eye each tick, scene A once
    sE, sC = [], []
    for _ in range(T1):
        e2 = _make_eye()
        _tick(e2, _scene())
        a, c = _fields(e2)
        sE.append(_err(a, c)); sC.append(len(_onset_cells(e2, 1)))
        e2.stop()
    return {"T1": T1, "T2": T2, "E": E, "C": C, "cells": cells,
            "sE": sE, "sC": sC}


_CACHE = {}


def run():
    if "r" not in _CACHE:
        _CACHE["r"] = _run()
    return _CACHE["r"]


# --------------------------------------------------------------- HEADLINE 1 ----
def test_build_curve_drops_toward_asymptote():
    d = run(); T1 = d["T1"]; build = d["E"][:T1]
    # monotone within numerical slack (able to fail on a non-building curve)
    assert all(build[i + 1] <= build[i] + 0.02 for i in range(len(build) - 1))
    assert build[-1] < 0.12                       # asymptote
    assert build[-1] < 0.25 * build[0]            # >=4x reduction


def test_stateless_control_is_flat_and_accumulation_gap_is_large():
    d = run()
    sE = d["sE"]
    assert np.std(sE) < 0.02 and np.mean(sE) > 0.5     # control FLAT, no build
    # THE ACCUMULATION SIGNAL — able to fail if the floor stops persisting.
    assert d["E"][d["T1"] - 1] < 0.3 * float(np.mean(sE))


# --------------------------------------------------------------- HEADLINE 2 ----
def test_cost_drains_as_scene_grounds():
    d = run(); T1 = d["T1"]; C = d["C"][:T1]
    assert C[0] >= 0.5 * NAZ * NEL                 # initial surprise is broad
    assert C[-1] <= 0.10 * C[0]                    # compute drains >=90%


def test_stateless_cost_stays_high_and_flat():
    d = run(); sC = d["sC"]
    assert np.mean(sC) >= 0.5 * NAZ * NEL
    assert np.std(sC) < 0.10 * max(np.mean(sC), 1e-9)


def test_perturbation_reraises_compute():
    d = run(); T1 = d["T1"]
    plateau = float(np.mean(d["C"][T1 - 3:T1]))    # ~0, grounded
    c_perturb = d["C"][T1]                          # tick T1+1
    n_patch = len(_patch_cells())
    assert c_perturb >= 0.5 * n_patch
    assert c_perturb > plateau                      # surprise returns


# --------------------------------------------------------------- HEADLINE 3 ----
def test_reraised_compute_localizes_to_the_perturbed_patch():
    d = run(); T1 = d["T1"]
    explicit = set()
    for t in range(T1, min(T1 + 4, d["T2"])):       # post-perturb window
        explicit |= set(d["cells"][t])
    patch = _patch_cells()
    inter = len(explicit & patch); union = len(explicit | patch)
    assert union > 0 and inter / union >= 0.5       # onsets localize to patch
