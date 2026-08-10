"""THE BLIND SPOT — a GROUNDED retinal field, not a sample array: the gates.

Gates PROTOCOL §0 (the fill DECISION is graph DATA, never a Python branch), §1
(the instrument is positive-controlled — the blind spot is REAL and the fill
TRACKS the surround), §7 (the four discrimination claims), §9 (the seed ships
INERT), §13 (the blind-spot geometry is a named STRUCTURAL param; the fill and the
decay fall out). The headline: the hole is INVISIBLE because it is filled from
BELIEF, a contour is bridged AS a contour, an ambiguous surround is HELD OPEN, and
the belief REVISES when the eye moves — while an interpolation control blurs and
confabulates. LOCAL / O(N), not the O(N^2) drive.
"""
from __future__ import annotations

import ast
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.seed_registry  # noqa: F401,E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains import ground_world as gw  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

H = W = 16
BC, BR = (8, 8), 2.0


def _world(interp=0.0, ground=1.0, h=H, w=W, bc=BC, br=BR):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
    wd = WaveWorld(s, h=h, w=w, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=bc, blind_radius=br)
    gw.set_ground_params(wd, ground=ground, interp=interp)
    return wd, anat


def _blind_idx(anat):
    rs, cs = zip(*sorted(anat["blind"]))
    return np.array(rs), np.array(cs)


# --------------------------------------------------------------------------- #
#  PROTOCOL §9 — the seed ships INERT
# --------------------------------------------------------------------------- #
def test_the_seed_ships_inert_so_every_committed_result_reproduces():
    path = os.path.join(ROOT, "seeds", "vision_ground.json")
    with open(path) as fh:
        man = json.load(fh)
    attrs = man["nodes"][0]["attrs"]
    assert attrs["ground"] == 0.0, "vision_ground must ship INERT (ground=0, §9)"
    assert attrs["interp"] == 0.0, "the interpolation control must ship OFF (§9)"


def test_ground_off_is_completely_inert():
    """ground=0 => no rule fires => the blind hole is never filled."""
    wd, anat = _world(ground=0.0)
    f = np.zeros((H, W)); f[8, :] = 1.0
    gw.present(wd, anat, f)
    ri, ci = _blind_idx(anat)
    assert float(gw.filled(wd, anat)[ri, ci].sum()) == 0.0, (
        "ground=0 must leave the hole unfilled — the seed is not selected")


# --------------------------------------------------------------------------- #
#  PROTOCOL §0 — the fill DECISION is graph DATA, not a Python branch
# --------------------------------------------------------------------------- #
def test_no_python_decides_the_fill_the_ablations_are_graph_data():
    """No branch on `ground`/`interp` in the adapter: every fill decision is a
    RULE reading GroundParams. Parses the source and inspects each if/while TEST
    (docstrings/comments invisible), the same gate rung 7 uses."""
    path = os.path.join(ROOT, "domains", "ground_world.py")
    with open(path) as fh:
        tree = ast.parse(fh.read())
    flags = {"ground", "interp"}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.If, ast.While, ast.IfExp)):
            continue
        src = ast.unparse(node.test)
        for f in flags:
            assert f not in src, (
                f"`{src}` branches on the ablation flag `{f}` in ground_world.py "
                "— the fill is a RULE's decision, not the adapter's (PROTOCOL §0)")


# --------------------------------------------------------------------------- #
#  THE INSTRUMENT (PROTOCOL §1) — the blind spot is REAL, the fill TRACKS
# --------------------------------------------------------------------------- #
def test_the_blind_spot_is_real_a_marker_inside_is_not_sensed():
    scene = np.zeros((H, W)); scene[8, 8] = 5.0
    wd, anat = _world()
    gw.present(wd, anat, scene)
    assert (8, 8) in anat["blind"], "the marker must lie in the blind spot"
    assert np.isnan(gw.raw_sensor(wd, anat)[8, 8]), (
        "the raw sensor must report NO DATA in the blind spot — if it senses the "
        "marker directly, the hole is fake and every fill claim is meaningless")


def test_the_fill_tracks_the_surround_not_a_stored_default():
    """Move the bar; the bridge moves with it, the rest of the hole stays clean —
    so the fill is GROUNDING the surround, not replaying a stored pattern."""
    for row in (7, 8, 9):
        wd, anat = _world(); f = np.zeros((H, W)); f[row, :] = 1.0
        gw.present(wd, anat, f)
        fld = gw.belief_field(wd, anat)
        on = [(r, c) for (r, c) in anat["blind"] if r == row]
        off = [(r, c) for (r, c) in anat["blind"] if r != row]
        assert on, f"row {row} must cross the blind spot"
        assert all(abs(fld[r, c] - 1.0) <= 1e-6 for (r, c) in on), (
            f"the bar on row {row} was not bridged")
        assert all(abs(fld[r, c]) <= 1e-6 for (r, c) in off), (
            f"the surround leaked off row {row} — the fill is not clean")


def test_a_blank_surround_invents_no_structure():
    """A surround with NO structure (uniform, random value) must invent NO
    contour and NO ambiguity — grounding does not hallucinate. Seeds 30000-30019
    (a subset of the pre-registered floor block)."""
    for sd in range(30000, 30020):
        v = float(np.random.default_rng(sd).uniform(0.1, 0.9))
        wd, anat = _world(); gw.present(wd, anat, np.full((H, W), v))
        ri, ci = _blind_idx(anat)
        assert int(gw.contour(wd, anat)[ri, ci].sum()) == 0
        assert int(gw.ambig(wd, anat)[ri, ci].sum()) == 0
        # ... and the hole is filled with the surround value (invisible).
        assert float(np.max(np.abs(gw.belief_field(wd, anat)[ri, ci] - v))) <= 1e-6


# --------------------------------------------------------------------------- #
#  THE FOUR DISCRIMINATION CLAIMS (PROTOCOL §7)
# --------------------------------------------------------------------------- #
def test_H1_structure_survives_grounding_not_blur_interpolation():
    """A contour crossing the blind spot is bridged AS a contour under grounding
    (a STEP) and BLURRED under interpolation (a RAMP)."""
    frame = np.zeros((H, W)); frame[8, :] = 1.0
    on_bar = sorted((r, c) for (r, c) in _world()[1]["blind"] if r == 8)

    wg, ag = _world(interp=0.0); gw.present(wg, ag, frame)
    fg = gw.belief_field(wg, ag)
    wi, ai = _world(interp=1.0); gw.present(wi, ai, frame)
    fi = gw.belief_field(wi, ai)

    err_g = float(np.mean([abs(fg[r, c] - 1.0) for (r, c) in on_bar]))
    err_i = float(np.mean([abs(fi[r, c] - 1.0) for (r, c) in on_bar]))
    assert err_g <= 0.05, f"grounding did not bridge the contour (err {err_g:.3f})"
    assert err_i > 0.2, f"interpolation did not blur (err {err_i:.3f}) — no control"
    # the cross-bar edge is SHARP (a step) under grounding, washed out under interp
    assert (fg[8, 8] - fg[7, 8]) > 0.9, "the bridged contour must be a sharp step"
    assert (fi[8, 8] - fi[7, 8]) < 0.5, "interpolation must wash the edge out"


def test_H2_the_hole_is_invisible_under_a_consistent_fill():
    """The headline reproduction of the phenomenology: a uniform field over the
    blind spot reads continuous — no void, no seam."""
    v = 0.7
    wd, anat = _world(); gw.present(wd, anat, np.full((H, W), v))
    f = gw.belief_field(wd, anat); ri, ci = _blind_idx(anat)
    assert not np.any(np.isnan(f)), "a NaN in the field = a visible void"
    assert float(np.max(np.abs(f[ri, ci] - v))) <= 1e-6, (
        "the blind spot must be INVISIBLE — filled with the surround belief")


def test_H3_hidden_when_covered_and_revealed_and_revised_when_the_eye_moves():
    """A thing entirely inside the blind spot is INVISIBLE (filled with the
    surround belief — the falsifiable, human-matching behaviour); when the eye
    moves it APPEARS and the belief REVISES."""
    scene = np.zeros((H, W)); scene[8, 8] = 3.0
    wd, anat = _world()
    gw.present(wd, anat, scene)                       # covered
    assert abs(float(gw.belief_field(wd, anat)[8, 8])) <= 1e-6, (
        "the covered marker must be invisible (filled with the surround's 0)")
    gw.present(wd, anat, scene, eye_offset=(0, -4))   # the eye moves
    assert abs(float(gw.belief_field(wd, anat)[8, 12]) - 3.0) <= 1e-6, (
        "after the eye moves the marker must APPEAR — the belief must revise")


def test_H4_an_ambiguous_surround_is_held_open_not_confabulated():
    """Two admissible continuations (a same-row contour A and a same-col contour
    B != A) meet at a blind cell: grounding HOLDS IT OPEN; interpolation invents a
    single mean. The unambiguous control commits confidently."""
    f = np.zeros((H, W)); f[8, :] = 1.0; f[:, 8] = 2.0
    wg, ag = _world(); gw.present(wg, ag, f)
    amb, fil, fld = gw.ambig(wg, ag), gw.filled(wg, ag), gw.belief_field(wg, ag)
    ri, ci = _blind_idx(ag)
    assert amb[8, 8] > 0.5 and fil[8, 8] < 0.5, (
        "the ambiguous crossing must be HELD OPEN (gambig=1, unfilled)")
    assert int(amb[ri, ci].sum()) == 1, "exactly the crossing is ambiguous"
    assert abs(fld[8, 6] - 1.0) <= 1e-6 and abs(fld[6, 8] - 2.0) <= 1e-6, (
        "both contours must still CONTINUE away from the crossing")

    wi, ai = _world(interp=1.0); gw.present(wi, ai, f)
    assert gw.ambig(wi, ai)[8, 8] < 0.5 and gw.filled(wi, ai)[8, 8] > 0.5, (
        "interpolation must COMMIT a single value at the crossing, never hold "
        "open — it confabulates where grounding refuses")

    wc, ac = _world(); fc = np.zeros((H, W)); fc[8, :] = 1.0; gw.present(wc, ac, fc)
    assert gw.ambig(wc, ac)[8, 8] < 0.5 and abs(float(gw.belief_field(wc, ac)[8, 8]) - 1.0) <= 1e-6, (
        "the UNAMBIGUOUS control must commit the grounded continuation confidently")


# --------------------------------------------------------------------------- #
#  SCALING — LOCAL / O(N), not the O(N^2) drive
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_the_field_is_LOCAL_O_N_not_the_O_N2_drive():
    import time
    sizes = [16, 24, 32, 48]
    Ns, Ts = [], []
    for S in sizes:
        wd, anat = _world(h=S, w=S, bc=(S // 2, S // 2))
        f = np.zeros((S, S)); f[S // 2, :] = 1.0
        gw.present(wd, anat, f)                       # warm
        t0 = time.perf_counter()
        for _ in range(3):
            gw.present(wd, anat, f)
        Ts.append((time.perf_counter() - t0) / 3); Ns.append(S * S)
    p = float(np.polyfit(np.log(Ns), np.log(Ts), 1)[0])
    assert p <= 1.2, (
        f"grounding scaled as N^{p:.2f} — a super-linear field is the O(N^2) "
        "drive reintroduced; the grounding must be LOCAL")
