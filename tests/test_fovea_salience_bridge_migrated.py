"""THE FOVEA/SALIENCE BRIDGE — the migrated gate (VISION_FOVEA_SALIENCE_BRIDGE_PREREG.md).

160000. 159000 proved salience-driven foveation but SELECTED the fovea with a numpy
argmax/top-K in Python (`select_fovea`'s `scored.sort(key=-peak)[:top_k]`) — an agent
DECISION in Python, forbidden by CLAUDE.md. This rung MIGRATES that decision into the
graph: the fovea is resolved by the substrate's own LOG-WEIGHTED ADMISSIBLE selection
(grammar.rs: Γ is the weighted admissibility grammar, selection ∝ exp(w); the MAP reading
is `ArgminUnique(admissible-candidates, Neg(w))`, w = Log(salience) + goal_logweight).

  A1 — the fovea is chosen by the GRAPH, no Python argmax/max/sort decides it (source +
       structural: without run_rules no candidate is flagged; the engine sets is_fovea).
  A2 — it works: the graph fovea == the retired numpy select_fovea top-1 AND lands on the
       GT object (synthetic movers; E1M1 graph==numpy, skipped if WAD/VizDoom absent).
  A3 — log-weighted co-presence: bottom-up alone → the salient; a co-present top-down goal
       log-weight shifts the resolution MONOTONE + continuous (crossover at the log-weight
       tie, where ArgminUnique refuses); a strong bottom-up WINS the race.
  A4 — admissibility governs: a high-weight INADMISSIBLE candidate never wins (Γ gates
       before weighting).
"""
import inspect
import math
import os

import numpy as np
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from domains import fovea_bridge as fb  # noqa: E402
from scripts.salience_foveation_probe import (  # noqa: E402
    synth_fovea_scene, salience_field, select_fovea, _coarsen)


# ----------------------------------------------------------------------
#  scene builders (mechanical; the DECISION is never here)
# ----------------------------------------------------------------------
def _one_mover_field(F=2):
    vy, vx, Z, foe, mover, app, bg = synth_fovea_scene()
    gh, gw = vy.shape
    vy_c = np.rint(_coarsen(vy, F) / F); vx_c = np.rint(_coarsen(vx, F) / F)
    mover_c = _coarsen(mover.astype(float), F) > 0.25
    sal_c, valid_c, _ = salience_field(vy_c, vx_c)
    return sal_c, valid_c, mover_c


def _two_mover_field(F=2):
    vy, vx, Z, foe, base_mover, app, bg = synth_fovea_scene()
    gh, gw = vy.shape
    yy, xx = np.mgrid[0:gh, 0:gw].astype(float)
    vx[base_mover] = 3.0 * (xx[base_mover] - foe[0]) / Z[base_mover]
    vy[base_mover] = 3.0 * (yy[base_mover] - foe[1]) / Z[base_mover]
    mr = 2.5
    ma = ((xx - gw * 0.34) ** 2 + (yy - gh * 0.34) ** 2) <= mr ** 2
    mb = ((xx - gw * 0.66) ** 2 + (yy - gh * 0.34) ** 2) <= mr ** 2
    vx[ma] = 0.0; vy[ma] = 9.0      # faster mover => higher tangential salience
    vx[mb] = 0.0; vy[mb] = 5.0      # slower mover
    vy_c = np.rint(_coarsen(vy, F) / F); vx_c = np.rint(_coarsen(vx, F) / F)
    ma_c = _coarsen(ma.astype(float), F) > 0.25
    sal_c, valid_c, _ = salience_field(vy_c, vx_c)
    return sal_c, valid_c, ma_c


# ======================================================================
#  A1 — THE DECISION IS THE GRAPH'S, NOT PYTHON'S
# ======================================================================
def test_A1_resolution_path_has_no_python_selection():
    """SOURCE AUDIT (able to fail): the resolution path — resolve_fovea / read_fovea /
    ingest_candidates — contains NO Python argmax/max/min/sort over candidates. The only
    selection allowed is the engine's inside run_rules; Python reads is_fovea back."""
    src = "\n".join(inspect.getsource(f) for f in
                    (fb.resolve_fovea, fb.read_fovea, fb.ingest_candidates))
    for forbidden in ("argmax", "sorted(", ".sort(", " max(", " min(", "np.max", "np.min"):
        assert forbidden not in src, f"resolution path smuggles a Python selection: {forbidden!r}"
    assert "run_rules" in src, "the resolution must run the engine"
    assert "is_fovea" in src, "the fovea must be READ from the graph attr the engine sets"


def test_A1_seed_rule_selects_by_ArgminUnique_over_log_weight():
    """The graph-native selection is the seed rule's ArgminUnique over Neg(Log(salience)+
    goal_logweight) filtered to admissible candidates — the log-weighted admissibility."""
    from substrate.seed_loader import manifest_for
    m = manifest_for("fovea_salience_bridge")
    rule = next(r for r in m["rules"] if r["name"] == "fovea_resolve")
    import json
    body = json.dumps(rule["where"])
    assert '"ArgminUnique"' in body, "the selection must be ArgminUnique (tie-refusing)"
    assert '"Log"' in body and '"salience"' in body, "log-weight must be Log(salience)"
    assert '"goal_logweight"' in body, "the top-down log-weight must be co-present"
    assert '"Filter"' in body and '"on_valid"' in body, "Γ admissibility must gate the source"


def test_A1_decision_comes_from_the_engine_not_python():
    """STRUCTURAL, able to fail: ingest the candidates but DO NOT run the engine — no
    candidate is flagged is_fovea. Only run_rules produces the fovea. The decision is the
    engine's, not Python's."""
    sal, valid, mover_c = _one_mover_field()
    cands, _ = fb.extract_candidates(sal, valid)
    assert cands, "need at least one candidate"
    s, ag, native = fb._boot()
    res = s.add_node("FoveaResolver", {})
    ids = fb.ingest_candidates(s, res, cands)
    assert fb.read_fovea(s, ids) is None, "no fovea before run_rules — Python decides nothing"
    native.run_rules()
    assert fb.read_fovea(s, ids) is not None, "the engine's run_rules resolves the fovea"


# ======================================================================
#  A2 — IT WORKS (reproduces the retired numpy fovea; lands on GT)
# ======================================================================
def test_A2_synth_one_mover_matches_numpy_and_lands_on_gt():
    sal, valid, mover_c = _one_mover_field()
    numpy_fovea, _ = select_fovea(sal, valid, top_k=1)
    np_rc = numpy_fovea[0]["peak_rc"]
    cands, _ = fb.extract_candidates(sal, valid)
    g = fb.resolve_fovea(cands)
    assert g is not None
    g_rc = [int(g["peak_row"]), int(g["peak_col"])]
    assert g_rc == np_rc, f"graph fovea {g_rc} != numpy {np_rc}"
    assert bool(mover_c[g_rc[0], g_rc[1]]), "graph fovea must land on the GT mover"


def test_A2_synth_two_movers_graph_selects_same_as_numpy():
    """A genuine SELECTION among two real competing candidates: the graph Argmax picks the
    same region numpy's top-1 does, and it is the more-salient (faster) mover."""
    sal, valid, ma_c = _two_mover_field()
    cands, _ = fb.extract_candidates(sal, valid)
    assert len(cands) >= 2, "need two competing candidates for a real selection"
    numpy_fovea, _ = select_fovea(sal, valid, top_k=1)
    np_rc = numpy_fovea[0]["peak_rc"]
    g = fb.resolve_fovea(cands)
    g_rc = [int(g["peak_row"]), int(g["peak_col"])]
    assert g_rc == np_rc, f"graph selection {g_rc} != numpy {np_rc}"
    assert bool(ma_c[g_rc[0], g_rc[1]]), "graph selects the faster (more salient) mover"


def _wad_available():
    from scripts.e1m1_salience_probe import WAD_DEFAULT
    if not os.path.exists(WAD_DEFAULT):
        return False
    try:
        import vizdoom  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _wad_available(), reason="E1M1 WAD / VizDoom absent")
def test_A2_e1m1_graph_matches_numpy_topk1():
    """On the REAL E1M1 WAD the graph reproduces numpy's top-1 fovea EXACTLY (the migration
    is faithful). A few candidate frames suffice (booting is per-call); full agreement is in
    the results doc (146/146)."""
    from scripts.e1m1_salience_probe import capture_e1m1, GH, GW, BLOCK, LEVEL
    from scripts.depth_from_motion_probe import _flow_field, FLOOR
    frames = capture_e1m1()
    if frames is None:
        pytest.skip("E1M1 capture unavailable")
    tested = agree = 0
    for fi in range(1, len(frames)):
        if tested >= 6:
            break
        vy_c, vx_c = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
        if (np.sqrt(vy_c ** 2 + vx_c ** 2) > FLOOR).sum() < 8:
            continue
        sal_c, valid_c, _ = salience_field(vy_c, vx_c)
        cands, _ = fb.extract_candidates(sal_c, valid_c)
        if not cands:
            continue
        numpy_fovea, _ = select_fovea(sal_c, valid_c, top_k=1)
        np_rc = numpy_fovea[0]["peak_rc"] if numpy_fovea else None
        g = fb.resolve_fovea(cands)
        g_rc = [int(g["peak_row"]), int(g["peak_col"])] if g else None
        tested += 1
        if np_rc == g_rc:
            agree += 1
    assert tested > 0, "no E1M1 candidate frames found"
    assert agree == tested, f"graph != numpy on {tested - agree}/{tested} E1M1 frames"


# ======================================================================
#  A3 — LOG-WEIGHTED CO-PRESENCE (not selection): monotone shift + race
# ======================================================================
def _AB():
    A = {"peak_rc": [10, 20], "peak": math.exp(2.0), "region_cells": 5, "on_valid": 1,
         "box": [0, 1, 0, 1]}
    B = {"peak_rc": [30, 40], "peak": math.exp(1.0), "region_cells": 4, "on_valid": 1,
         "box": [0, 1, 0, 1]}
    return A, B


def _winner(cands, goal=None):
    w = fb.resolve_fovea(cands, goal_logweights=goal)
    if w is None:
        return "REFUSE"
    return "A" if [int(w["peak_row"]), int(w["peak_col"])] == [10, 20] else "B"


def test_A3_bottom_up_alone_foveates_the_salient():
    A, B = _AB()
    assert _winner([A, B]) == "A"       # Log(s_A)=2 > Log(s_B)=1


def test_A3_topdown_goal_shifts_resolution_monotone_with_crossover():
    """A co-present top-down log-weight g on B shifts the resolution CONTINUOUSLY: A wins
    while w_B<w_A, ArgminUnique REFUSES exactly at the tie (w_B==w_A), B wins once w_B>w_A.
    The override is a weight-shift (monotone in g), not a switch."""
    A, B = _AB()
    gs = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]
    winners = [_winner([A, B], goal=[0.0, g]) for g in gs]
    # crossover is at g = Log(s_A) - Log(s_B) = 1.0
    for g, win in zip(gs, winners):
        if g < 1.0:
            assert win == "A", f"g={g}: expected A, got {win}"
        elif abs(g - 1.0) < 1e-9:
            assert win == "REFUSE", f"g={g}: expected tie-refusal, got {win}"
        else:
            assert win == "B", f"g={g}: expected B, got {win}"
    # MONOTONE: once B wins it never reverts as g rises further
    b_from = [i for i, w in enumerate(winners) if w == "B"]
    assert b_from and all(winners[i] == "B" for i in range(b_from[0], len(winners)))


def test_A3_strong_bottom_up_wins_the_race():
    """The highest log-weight admissible candidate wins whichever way it arrived: a strong
    bottom-up A (w=5) beats B carrying a top-down g=2 (w=1+2=3)."""
    A, B = _AB()
    A_strong = dict(A); A_strong["peak"] = math.exp(5.0)
    assert _winner([A_strong, B], goal=[0.0, 2.0]) == "A"


# ======================================================================
#  A4 — ADMISSIBILITY GOVERNS (Γ gates before weighting)
# ======================================================================
def test_A4_inadmissible_high_weight_candidate_never_wins():
    """An INADMISSIBLE candidate (on_valid=0 — a fovea target on an unobserved cell) is
    excluded from the resolution regardless of its weight: a huge-salience inadmissible B
    never wins over a lower-salience admissible A."""
    A, B = _AB()
    B_huge = dict(B); B_huge["peak"] = math.exp(9.0)   # far more salient than A
    win = _winner([A, B_huge], goal=None)              # but on_valid overridden below
    # sanity: with BOTH admissible the huge-salience B WOULD win —
    assert win == "B"
    # now mark B inadmissible: A (admissible, lower weight) must win.
    w = fb.resolve_fovea([A, B_huge], admissible=[1, 0])
    assert w is not None and [int(w["peak_row"]), int(w["peak_col"])] == [10, 20], \
        "Γ must exclude the inadmissible high-weight candidate before weighting"
