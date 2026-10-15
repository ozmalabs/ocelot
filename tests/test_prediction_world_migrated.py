"""The prediction world (2026-10-10): a graded closed world in which the
agent's own graph rules notice its surprise, try alternative predictor models,
judge them weighed against what they cost on levels already mastered, adopt
the best trade and advance. See scripts/gen_prediction_world.py.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

import pytest  # noqa: E402

from domains import prediction_world as pw  # noqa: E402


def _agent(self_improvement=1):
    from substrate.world_adapter import WorldAdapter
    a = WorldAdapter(seeds=("prediction_world", "prediction_self_improvement"))
    a.inner.set_attr(a.s.nodes("PredictionPolicy")[0], "self_improvement", int(self_improvement))
    return a


def _live(a, n, seed_base=1000):
    for i in range(n):
        pw.run_episode(a, seed=seed_base + i)
        pw.run_experiments(a)
    S = a.s
    return S.node(S.nodes("PredictionCurriculum")[0])["attrs"]


def test_predictor_forms_on_the_fall_level():
    """The graph predictor's forms do what they say: under gravity the
    acceleration model is exact and the velocity model misses by g."""
    tr = pw.simulate(3, 7)
    assert pw.replay(tr, "acceleration", 0) == pytest.approx(0.0, abs=1e-4)
    assert pw.replay(tr, "velocity", 0) == pytest.approx(0.5, abs=1e-4)


def test_velocity_masters_drift():
    assert pw.replay(pw.simulate(1, 3), "velocity", 0) == pytest.approx(0.0, abs=1e-4)


def test_on_arm_improves_itself_off_arm_is_stuck():
    on, off = _agent(1), _agent(0)
    cur_on, cur_off = _live(on, 60), _live(off, 60)
    assert cur_on["current_level"] >= 4 and cur_on["mastered_through"] >= 3
    assert len(on.s.nodes("Adoption")) >= 2
    assert cur_off["current_level"] == 2 and len(off.s.nodes("Experiment")) == 0
    assert len(off.s.nodes("Adoption")) == 0
    # the off arm still notices: its concern is filed and stays open
    st = [off.s.node(c)["attrs"]["status"] for c in off.s.nodes("SelfConcern")
          if off.s.node(c)["attrs"].get("kind") == "prediction_surprise"]
    assert st == ["open"]


def _synthetic(a, trials):
    """A concern with done, unjudged experiments against the current model;
    trials = [(form, reflect, rank, control, variant, retention_harm)]."""
    S, I = a.s, a.inner
    p = S.node(S.nodes("Predictor")[0])["attrs"]
    sc = S.add_node("SelfConcern", {"kind": "prediction_surprise", "status": "open", "level": 3})
    I.add_edge_unchecked(a.agent, "has_self_concern", sc)
    exps = []
    for form, refl, rank, c, v, h in trials:
        x = S.add_node("Experiment", {"game": "prediction_world", "status": "done", "level": 3,
                                      "control_surprise": c, "variant_surprise": v, "retention_harm": h})
        d = S.add_node("SeedDelta", {"variation_op": "predictor_edit", "candidate_form": form,
                                     "candidate_reflect": refl, "candidate_rank": rank,
                                     "control_form": p["form"], "control_reflect": p["reflect"]})
        I.add_edge_unchecked(x, "has_delta", d)
        I.add_edge_unchecked(sc, "tested_by", x)
        exps.append(x)
    I.run_rules()
    return sc, exps


def test_judge_weighs_retention_harm():
    """A large gain at the level is refuted when it costs more on the levels
    already mastered than it gains."""
    a = _agent(0)
    sc, (x,) = _synthetic(a, [("acceleration", 0, 2, 0.5, 0.0, 0.6)])
    at = a.s.node(x)["attrs"]
    assert at["weighed_net"] == pytest.approx(-0.1)
    assert at["outcome"] == "refuted" and at.get("adopted") != 1
    assert a.s.node(a.s.nodes("Predictor")[0])["attrs"]["form"] == "velocity"


def test_adopts_best_weighed_trade_not_simplest_supported():
    a = _agent(0)
    sc, (x0, x1) = _synthetic(a, [("acceleration", 0, 2, 0.5, 0.0, 0.4),
                                  ("acceleration", 1, 3, 0.5, 0.0, 0.2)])
    assert a.s.node(x0)["attrs"]["outcome"] == "supported"
    assert a.s.node(x1)["attrs"]["outcome"] == "supported"
    assert a.s.node(x1)["attrs"].get("adopted") == 1 and a.s.node(x0)["attrs"].get("adopted") != 1
    p = a.s.node(a.s.nodes("Predictor")[0])["attrs"]
    assert (p["form"], p["reflect"]) == ("acceleration", 1)
    assert a.s.node(sc)["attrs"]["status"] == "resolved"


def test_loop_seed_frozen_and_protected():
    from substrate.boot_all import _FROZEN_SEED_IDS
    assert "prediction_self_improvement" in _FROZEN_SEED_IDS
    assert "prediction_world" not in _FROZEN_SEED_IDS     # the part the agent changes
    man = json.loads((ROOT / "seeds/frozen_core_manifest.json").read_text())
    assert "prediction_self_improvement" in man["frozen_seed_ids"]
    loop = json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())
    assert loop["depends_on"] == []
    integ = (ROOT / "seeds/improvement_integrity.json").read_text()
    for t in ("PredictionPolicy", "PredictionCurriculum", "PredictorCandidate"):
        assert f'"{t}"' in integ
