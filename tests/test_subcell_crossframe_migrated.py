"""GATE for block 149000-149999 — SUB-CELL CROSS-FRAME REGISTRATION.

Precision belongs in the cross-frame offset, not the in-frame grid. The
per-frame displacement is `Hom(frame,frame)`, a cross-frame map where a
continuous parameter is admissible, its observable the STEPPED finer-unit
INTEGER rendering. This gate proves, ALL READ FROM THE GRAPH and each able to
fail:

  1. ORACLE CHAIN — a known SUB-CELL parabola: the INTEGER centroid floors while
     sub-cell registration -> finer-unit position -> the robust witness mints
     order-2 with accel_fine == a_cell * S (the KNOWN acceleration in finer units).
  2. CONTROLS — const-velocity mints no order-2 curvature; static mints nothing;
     noise floors (registration of noise does not confabulate coherent order-2).
  3. INVARIANT GUARD — NO in-frame coordinate is ever a float. The registration
     sensor returns finer-unit INTEGERS; the position stream is all int; the graph
     Observation's coordinate slots read back as int. (The forbidden move is a
     sub-pixel FLOAT centroid / a float in a frame coordinate.)
  4. REAL CLIP — the recovered coefficient (CONFIRM: nonzero >0 downward accel in
     finer units where the integer centroid floored; or the isolated DEGRADE),
     read from the committed graph-minted result. Judged by the COEFFICIENT.
  5. BYTE-IDENTITY OFF — the new mechanism lives in NEW files only; no existing
     engine / sensor / seed / carve file is touched, so every committed result
     reproduces exactly with the new path off (default).

Cross-process stability: the carve's region ids are a per-process HashMap
artifact, so the gate asserts the robust GRAPH-READ verdict (the minted coeff),
NEVER an exact d2 constancy or an exact trajectory.
"""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import subcell_crossframe_measure as M  # noqa: E402
from domains import falling_world as fw  # noqa: E402
from domains.subcell_register import register_residual_offset  # noqa: E402

RESULTS = os.path.join(ROOT, "results", "subcell_crossframe_measure.json")


# ─────────────────────────── 1. ORACLE CHAIN (graph) ─────────────────────────

def test_oracle_chain_recovers_known_subcell_acceleration():
    """The registration+witness chain recovers the KNOWN sub-cell accel in finer
    units; the integer centroid floors on the SAME sub-cell parabola. From graph."""
    orc = M.part_oracle()
    # integer centroid floors — no order-2 acceleration read.
    assert orc["integer_centroid"]["accel_coeff"] in (None, 0), \
        f"integer centroid should FLOOR on a sub-cell parabola: {orc['integer_centroid']}"
    # sub-cell recovers the KNOWN acceleration in finer units (== a_cell * S).
    target = orc["target_accel_fine"]
    got = orc["subcell"]["accel_coeff"]
    assert orc["subcell"]["status"] == "time_inferred", orc["subcell"]
    assert got is not None and got > 0, f"sub-cell must recover a positive accel: {got}"
    assert got == target, f"accel_fine {got} != known target a_cell*S {target}"


# ───────────────────────────── 2. CONTROLS (graph) ───────────────────────────

def test_controls_hold():
    ctl = M.part_controls()
    # const-velocity: registration must NOT manufacture curvature.
    assert ctl["const_velocity_subcell"]["accel_coeff"] in (None, 0), \
        f"const-velocity manufactured curvature: {ctl['const_velocity_subcell']}"
    # static: nothing coherent to accelerate.
    assert ctl["static_subcell"]["accel_coeff"] in (None, 0), ctl["static_subcell"]
    # noise: registration of incoherent frames must not confabulate order-2.
    assert ctl["noise_subcell"]["accel_coeff"] in (None, 0), ctl["noise_subcell"]


# ──────────────────── 3. INVARIANT GUARD — no in-frame float ──────────────────

def test_no_in_frame_coordinate_is_a_float():
    """The registration sensor emits finer-unit INTEGERS; the position stream is
    all int; the graph Observation's coordinate slots read back as int. If any
    float leaked into an in-frame coordinate this fails."""
    a_cell = 0.2
    frames, true_top = M.render_subcell_fall(a_cell=a_cell, n_frames=8, cy0=10.0,
                                             gh=200, gw=64, obj=24,
                                             texseed=149000, texlo=64)
    run = [{"fi": t, "cy": float(round(true_top[t])), "cx": 32.0,
            "count": 576.0, "id": 1} for t in range(8)]
    py, px, diags = M.subcell_position_stream(frames, run)
    # sensor output: finer-unit INTEGERS (never a float coordinate).
    dy, dx, _ = register_residual_offset(frames[0], frames[1],
                                         anchor_prev=(int(round(true_top[0])), 32),
                                         coarse=(int(round(true_top[1])) - int(round(true_top[0])), 0),
                                         count=576.0, S=M.S, search_cells=M.SEARCH_CELLS)
    assert isinstance(dy, int) and isinstance(dx, int), (type(dy), type(dx))
    # the whole finer-unit position stream is integer-typed.
    assert all(isinstance(v, int) for v in py), [type(v).__name__ for v in py]
    assert all(isinstance(v, int) for v in px), [type(v).__name__ for v in px]
    # and the GRAPH sees only integer coordinates.
    s, ag, native = fw.boot_falling()
    fr = [[["obj", int(round(y)), 0, "obj"]] for y in py]
    o = s.add_node("Observation", {"frames": fr, "dim_types": M.DT,
                   "status": "motion_seq_robust", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    graph_frames = s.node(o)["attrs"]["frames"]
    for f in graph_frames:
        for tok in f:
            # coordinate slots are index 1 (row) and 2 (col) per DT.
            assert isinstance(tok[1], int) and not isinstance(tok[1], bool), tok
            assert isinstance(tok[2], int) and not isinstance(tok[2], bool), tok


# ──────────────────────── 4. REAL CLIP (committed graph read) ─────────────────

@pytest.mark.skipif(not os.path.exists(RESULTS),
                    reason="run scripts/subcell_crossframe_measure.py first")
def test_real_clip_mechanism_moves_off_floor_confidence_degrades():
    """Judged by the COEFFICIENT read from the graph mint in the committed run.
    CONFIRM-on-mechanism / DEGRADE-on-real-confidence.

    CONFIRM-on-mechanism (asserted, cross-process stable — reads the committed
    graph-minted coeff, NOT the carve which jitters per process): where the
    INTEGER centroid FLOORED (accel 0 or no order-2), the sub-cell path mints a
    NONZERO order-2 coefficient — the invariant-clean cross-frame precision moved
    the real clip OFF the floor 147000/148000 could not leave.

    DEGRADE-on-real-confidence (recorded, NOT claimed as physical g): there is no
    ground-truth g for this clip in cell-units; the trajectory is short (<=7
    frames) with a glitchy tail; and overlapping windows of the SAME fall recover
    OPPOSITE-sign accel_fine (+1 vs -2) with whole-cell per-pair residuals. So the
    recovered coefficient is NOT confirmed to be the physical acceleration — the
    wall MOVES to trajectory LENGTH/quality (longer, cleaner tracked runs). The
    oracle (deterministic, above) proves the chain recovers a KNOWN sub-cell
    accel, so this is confidence-in-the-real-number, not a broken mechanism."""
    res = json.load(open(RESULTS))
    rows = [r for r in res.get("real", []) if "subcell" in r]
    assert rows, "no real config produced a >=4 run"
    # the wall exists: the integer-centroid readout floored on >=1 config.
    floored = [r for r in rows if r["integer_centroid"]["accel_coeff"] in (None, 0)]
    assert floored, "integer centroid did not floor on ANY real config — no wall to beat"
    # CONFIRM-on-mechanism: sub-cell mints a NONZERO order-2 coeff where the
    # integer centroid floored (graph-minted verdict; stable across processes).
    moved = [r for r in floored
             if r["subcell"]["accel_coeff"] not in (None, 0)
             and r["subcell"]["status"] == "time_inferred"]
    assert moved, ("sub-cell did not mint a nonzero order-2 where the integer "
                   "centroid floored — the mechanism did not move off the floor")
    # DEGRADE-on-real-confidence is RECORDED here (short trajectory + cross-window
    # sign disagreement), never asserted as physical g. These facts must be
    # visible in the committed result for the results doc's honest framing.
    accels = [r["subcell"]["accel_coeff"] for r in rows
              if r["subcell"]["accel_coeff"] not in (None, 0)]
    max_run = max(r["run_len"] for r in rows)
    assert max_run <= 8, "trajectory unexpectedly long — re-examine the DEGRADE framing"
    # (documentation, not a pass/fail sign gate: signs may agree in another run;
    #  the confidence caveat stands on trajectory length + no ground-truth g.)
    _ = {r["label"]: r["subcell"]["accel_coeff"] for r in rows}


# ─────────────────────── 5. BYTE-IDENTITY OFF (diff scope) ────────────────────

# New code/data files introduced by this rung. The byte-identity claim is about
# CODE: no existing engine / sensor / seed / carve file may be touched.
ALLOWED_NEW = {
    "domains/subcell_register.py",
    "scripts/subcell_crossframe_measure.py",
    "tests/test_subcell_crossframe_migrated.py",
    "results/subcell_crossframe_measure.json",
    "VISION_SUBCELL_CROSSFRAME_RESULTS.md",
    "VISION_SUBCELL_CROSSFRAME_PREREG.md",
}
# Documentation-only ledger — NOT a code path, so it cannot affect byte-identity;
# every rung appends its row here (see the 148000 precedent).
ALLOWED_DOC = {"VISION_PROTOCOL.md"}


def test_byte_identity_off_only_new_files_touched():
    """The new mechanism lives in NEW files only — no existing engine / sensor /
    seed / carve file is modified, so every committed result reproduces exactly
    with the new path OFF (it is not wired into any existing default). Proven by
    the diff scope against the rung's base commit."""
    base = "c4814cd58f"
    try:
        out = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", base, "--"],
                             capture_output=True, text=True, timeout=30)
    except Exception as e:  # pragma: no cover
        pytest.skip(f"git unavailable: {e}")
    changed = [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
    # every changed path (relative to the experiment dir) must be an allowed NEW file.
    prefix = "research/experiments/gamma-substrate/"
    rel = [c[len(prefix):] if c.startswith(prefix) else c for c in changed]
    offending = [c for c in rel if c not in ALLOWED_NEW and c not in ALLOWED_DOC]
    assert not offending, f"existing CODE files modified (byte-identity risk): {offending}"
