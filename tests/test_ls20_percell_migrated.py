"""RUNG 222000 gates — the PER-CELL live-mechanic model.

The headline is scored on the CHANGE-SET (strict changed-cell F1), NEVER raw
per-cell accuracy (a persistence null aces raw ~99%). The learned per-cell model
must beat BOTH nulls (persistence + the 221000 aggregate-count) and the action->
transform map must be DISCOVERED (no hardcoded table). Default-OFF byte-identical.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_percell import (  # noqa: E402
    Percell, ACTIONS, make_scene, scene_grid, world_next, investigate,
    make_probe_set, score_prediction, discover_spec, AggregateCountNull,
    _apply_spec_to_grid,
)


def _trained_agent(seed=222000):
    ag = Percell()
    investigate(ag, np.random.default_rng(seed))
    return ag


def _bootstrap_lo_hi(xs, reps=400, seed=0):
    xs = np.asarray(xs, dtype=float)
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, xs.size, size=(reps, xs.size))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# ---------------------------------------------------------------------------
# G-percell-teeth — learned change-set strict-F1 CI-separated above BOTH nulls
# ---------------------------------------------------------------------------
def test_percell_teeth_beats_both_nulls_ci_separated():
    ag = _trained_agent()
    agg = AggregateCountNull(seed=7)
    trng = np.random.default_rng(222000)
    for a in ACTIONS:
        for _ in range(2):
            sc = make_scene(trng); cur = scene_grid(sc); nxt = world_next(sc, cur, a)
            agg.observe(a, cur, nxt)
    erng = np.random.default_rng(555)
    learned, pers, aggr = [], [], []
    for _ in range(60):
        sc = make_scene(erng); cur = scene_grid(sc)
        for a in ACTIONS:
            true = world_next(sc, cur, a)
            learned.append(score_prediction(cur, true, ag.predict_next(cur, a))["f1_strict"])
            pers.append(score_prediction(cur, true, cur.copy())["f1_strict"])
            aggr.append(score_prediction(cur, true, agg.predict(cur, a))["f1_strict"])
    lo_l, _ = _bootstrap_lo_hi(learned, seed=1)
    _, hi_p = _bootstrap_lo_hi(pers, seed=2)
    _, hi_a = _bootstrap_lo_hi(aggr, seed=3)
    assert np.mean(learned) > 0.9, f"learned strict-F1 too low: {np.mean(learned)}"
    assert lo_l > hi_p, f"NOT CI-separated above persistence: {lo_l} !> {hi_p}"
    assert lo_l > hi_a, f"NOT CI-separated above aggregate-count: {lo_l} !> {hi_a}"


def test_raw_accuracy_is_the_trap_not_the_gate():
    """Persistence ACES raw per-cell accuracy (~99%) yet scores 0 change-set F1 --
    the pre-registered reason raw accuracy is never the gate."""
    ag = _trained_agent()
    erng = np.random.default_rng(11)
    raw_p, f1_p = [], []
    for _ in range(20):
        sc = make_scene(erng); cur = scene_grid(sc)
        for a in ACTIONS:
            true = world_next(sc, cur, a)
            s = score_prediction(cur, true, cur.copy())
            raw_p.append(s["raw_acc"]); f1_p.append(s["f1_strict"])
    assert np.mean(raw_p) > 0.98, "persistence should ace RAW accuracy"
    assert np.mean(f1_p) == 0.0, "persistence must score ZERO change-set strict-F1"


# ---------------------------------------------------------------------------
# G-mechanic-discovered — all 10 action->Transform hypotheses, no hardcoded map
# ---------------------------------------------------------------------------
def test_all_ten_action_transforms_discovered():
    ag = _trained_agent()
    assert ag.confirmed_count() == len(ACTIONS), "every action's transform must be confirmed"
    expect = {"move_up": "shift:-1:0", "move_down": "shift:1:0",
              "move_left": "shift:0:-1", "move_right": "shift:0:1",
              "rot1": "rotation90:1", "rot2": "rotation90:2", "rot3": "rotation90:3",
              "refl_c": "reflection_c:1", "refl_r": "reflection_r:1",
              "recolour": "subst:11>14"}
    for a, k in expect.items():
        h = ag.hypothesis(a)
        assert h is not None and h["key"] == k, f"{a}: expected {k}, got {h}"
    # region-selector discovered: moves act on the avatar (9), transforms on the symbol (11)
    assert ag.hypothesis("move_up")["region_colour"] == 9
    assert ag.hypothesis("rot1")["region_colour"] == 11


def test_no_hardcoded_action_transform_table_in_agent_path():
    """Source audit: the agent's prediction functions must NOT reference the
    ground-truth _MOVE/_XFORM tables (those are WORLD PHYSICS only)."""
    import inspect
    import worlds.arc_ls20_percell as PC
    banned = ["_MOVE", "_XFORM"]
    for name in ("discover_spec", "_recognise_transform", "_apply_spec_to_grid",
                 "predict_next", "hypothesis"):
        fn = getattr(PC, name, None) or getattr(Percell, name)
        src = inspect.getsource(fn)
        for b in banned:
            assert b not in src, f"agent fn {name} must not reference ground-truth table {b}"
    # and world physics DOES use them (they exist, as ground truth):
    assert "_XFORM" in inspect.getsource(PC.world_next)


# ---------------------------------------------------------------------------
# G-convergence — the change-set surprise DROPS as the model learns
# ---------------------------------------------------------------------------
def test_convergence_surprise_drops():
    ag = Percell()
    probe = make_probe_set(np.random.default_rng(1), 10)
    curve = investigate(ag, np.random.default_rng(222000), probe_scenes=probe)
    assert curve[0] > 0.5, f"surprise should start high, got {curve[0]}"
    assert curve[len(ACTIONS) - 1] == pytest.approx(0.0, abs=1e-9), \
        "surprise should reach 0 once every action is modelled"
    assert curve[-1] < curve[0], "surprise must DROP as the model learns"


# ---------------------------------------------------------------------------
# instrument teeth — the metric PENALISES a mis-specified region (not 1.0 free)
# ---------------------------------------------------------------------------
def test_metric_penalises_wrong_region_selector():
    """A model with the RIGHT transform but the WRONG region colour (applies a
    move's shift to the symbol, not the avatar) scores low change-set F1 -- the
    metric has teeth beyond the count nulls; 1.0 is EARNED by the region-selector."""
    ag = _trained_agent()
    erng = np.random.default_rng(3)
    right, wrong = [], []
    for _ in range(20):
        sc = make_scene(erng); cur = scene_grid(sc)
        true = world_next(sc, cur, "move_right")
        right.append(score_prediction(cur, true, ag.predict_next(cur, "move_right"))["f1_strict"])
        h = dict(ag.hypothesis("move_right")); h["region_colour"] = 11  # wrong object
        wrong.append(score_prediction(cur, true, _apply_spec_to_grid(cur, h))["f1_strict"])
    assert np.mean(right) > 0.9, "right region -> high F1"
    assert np.mean(wrong) < 0.1, "wrong region -> low F1 (the metric penalises location)"


# ---------------------------------------------------------------------------
# G-discipline — the pc_* rules are DEFAULT-OFF (guarded on percell_on==1)
# ---------------------------------------------------------------------------
def test_rules_are_default_off():
    """Without percell_on the rules never fire: a Game with percell_on!=1 and a
    probing edge produces no Hypothesis and no probe_action."""
    from domains.ls20_percell_seed import RULES
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    s, ag = boot_core()
    n = rf._native_eval2(s)
    for r in RULES:
        n.add_rule(r)
    g = s.add_node("Game", {"percell_on": 0.0, "arm": "percell", "phase": "pick"})
    an = s.add_node("Action", {"name": "move_up", "visits": 0.0})
    n.add_edge_unchecked(g, "has_action", an)
    n.run_rules()
    assert not list(s.neighbours(g, "probing")), "no rule may fire with percell_on off"
    assert not list(s.neighbours(an, "has_hyp")), "no hypothesis with percell_on off"


def test_discover_spec_offline_default_is_unguarded():
    """discover_spec's live size-guard defaults OFF (max_obj_cells=None) so the
    offline path is byte-identical (a clean single-object move still recognises)."""
    cur = np.zeros((32, 32), dtype=np.int32)
    for (r, c) in [(5, 5), (6, 5), (7, 5), (7, 6)]:
        cur[r, c] = 9
    nxt = np.zeros((32, 32), dtype=np.int32)
    for (r, c) in [(5, 6), (6, 6), (7, 6), (7, 7)]:
        nxt[r, c] = 9
    spec = discover_spec(cur, nxt)          # no max_obj_cells -> offline path
    assert spec is not None and spec["key"] == "shift:0:1"
