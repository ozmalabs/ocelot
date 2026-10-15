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

# base-model masks: bit k = rank k = form_index*2 + reflect
VEL, ACC, ACC1, RATIO = 1 << 0, 1 << 2, 1 << 3, 1 << 4


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
    assert pw.replay(tr, ACC) == pytest.approx(0.0, abs=1e-4)
    assert pw.replay(tr, VEL) == pytest.approx(0.5, abs=1e-4)


def test_velocity_masters_drift():
    assert pw.replay(pw.simulate(1, 3), VEL) == pytest.approx(0.0, abs=1e-4)


def test_composite_uses_the_component_that_fits():
    """A composite (acceleration+reflect | ratio) is exact on glide, where only
    ratio is, and near-exact on fall, where only acceleration is."""
    comp = ACC1 | RATIO
    for seed in range(3):
        assert pw.replay(pw.simulate(4, seed), comp) == pytest.approx(0.0, abs=1e-4)
        assert pw.replay(pw.simulate(4, seed), ACC1) > 0.2
        assert pw.replay(pw.simulate(3, seed), comp) < 0.15


def test_on_arm_improves_itself_off_arm_is_stuck():
    on, off = _agent(1), _agent(0)
    cur_on, cur_off = _live(on, 60), _live(off, 60)
    assert cur_on["current_level"] == 5 and cur_on["mastered_through"] == 4
    assert len(on.s.nodes("Adoption")) == 3
    # level 4 was passed with a model the agent authored itself
    authored = [on.s.node(k)["attrs"] for k in on.s.nodes("PredictorCandidate")
                if on.s.node(k)["attrs"].get("authored") == 1]
    assert [(k["mask"], k["authored_level"]) for k in authored] == [(ACC1 | RATIO, 4)]
    assert on.s.node(on.s.nodes("Predictor")[0])["attrs"]["mask"] == ACC1 | RATIO
    st_on = {on.s.node(c)["attrs"]["level"]: on.s.node(c)["attrs"]["status"] for c in on.s.nodes("SelfConcern")
             if on.s.node(c)["attrs"].get("kind") == "prediction_surprise"}
    assert st_on == {2: "resolved", 3: "resolved", 4: "resolved", 5: "exhausted"}
    assert len(off.s.nodes("PredictorCandidate")) == 6
    assert cur_off["current_level"] == 2 and len(off.s.nodes("Experiment")) == 0
    assert len(off.s.nodes("Adoption")) == 0
    # the off arm still notices: its concern is filed and stays open
    st = [off.s.node(c)["attrs"]["status"] for c in off.s.nodes("SelfConcern")
          if off.s.node(c)["attrs"].get("kind") == "prediction_surprise"]
    assert st == ["open"]


def _synthetic(a, trials):
    """A concern with done, unjudged experiments against the current model;
    trials = [(mask, rank, control, variant, retention_harm)]."""
    S, I = a.s, a.inner
    p = S.node(S.nodes("Predictor")[0])["attrs"]
    sc = S.add_node("SelfConcern", {"kind": "prediction_surprise", "status": "open", "level": 3})
    I.add_edge_unchecked(a.agent, "has_self_concern", sc)
    exps = []
    for mask, rank, c, v, h in trials:
        x = S.add_node("Experiment", {"game": "prediction_world", "status": "done", "level": 3,
                                      "control_surprise": c, "variant_surprise": v, "retention_harm": h,
                                      "candidate_mask": mask, "control_mask": p["mask"],
                                      "candidate_name": f"m{mask}"})
        d = S.add_node("SeedDelta", {"variation_op": "predictor_edit", "candidate_form": "f",
                                     "candidate_reflect": 0, "candidate_rank": rank, "candidate_mask": mask,
                                     "candidate_name": f"m{mask}", "control_form": p["form"],
                                     "control_reflect": p["reflect"], "control_mask": p["mask"],
                                     "control_name": p["model"]})
        I.add_edge_unchecked(x, "has_delta", d)
        I.add_edge_unchecked(sc, "tested_by", x)
        exps.append(x)
    I.run_rules()
    return sc, exps


def test_judge_weighs_retention_harm():
    """A large gain at the level is refuted when it costs more on the levels
    already mastered than it gains."""
    a = _agent(0)
    sc, (x,) = _synthetic(a, [(ACC, 2, 0.5, 0.0, 0.6)])
    at = a.s.node(x)["attrs"]
    assert at["weighed_net"] == pytest.approx(-0.1)
    assert at["outcome"] == "refuted" and at.get("adopted") != 1
    assert a.s.node(a.s.nodes("Predictor")[0])["attrs"]["form"] == "velocity"


def test_adopts_best_weighed_trade_not_simplest_supported():
    a = _agent(0)
    sc, (x0, x1) = _synthetic(a, [(ACC, 2, 0.5, 0.0, 0.4), (ACC1, 3, 0.5, 0.0, 0.2)])
    assert a.s.node(x0)["attrs"]["outcome"] == "supported"
    assert a.s.node(x1)["attrs"]["outcome"] == "supported"
    assert a.s.node(x1)["attrs"].get("adopted") == 1 and a.s.node(x0)["attrs"].get("adopted") != 1
    p = a.s.node(a.s.nodes("Predictor")[0])["attrs"]
    assert p["mask"] == ACC1
    assert a.s.node(sc)["attrs"]["status"] == "resolved"


def _set_level(a, level):
    cur = a.s.nodes("PredictionCurriculum")[0]
    a.inner.set_attr(cur, "current_level", level)


def test_authors_composite_of_control_and_local_winner():
    """An exhausted concern whose best local trial was refuted only on its
    retention cost: the agent authors control | winner and reopens."""
    a = _agent(1)
    _set_level(a, 3)
    S = a.s
    # every base model already tried and refuted, so the concern exhausts;
    # ratio (mask 16) and acceleration (4) cleared the local bar, ratio best
    trials = [(m, r, 0.5, v, 1.0) for m, r, v in
              [(2, 1, 0.5), (4, 2, 0.1), (8, 3, 0.45), (16, 4, 0.0), (32, 5, 0.3)]]
    sc, exps = _synthetic(a, trials)
    authored = [k for k in S.nodes("PredictorCandidate") if S.node(k)["attrs"].get("authored") == 1]
    assert len(authored) == 1
    k = S.node(authored[0])["attrs"]
    assert k["mask"] == VEL | RATIO and k["name"] == "velocity | m16" and k["rank"] == 12
    # reopened, and a trial of the new model is requested
    assert S.node(sc)["attrs"]["status"] == "open"
    req = [x for x in S.nodes("Experiment") if S.node(x)["attrs"].get("status") == "requested"]
    assert [S.node(x)["attrs"]["candidate_mask"] for x in req] == [VEL | RATIO]


def test_does_not_author_without_a_local_winner_or_when_off():
    for si, local in ((1, 0.45), (0, 0.0)):
        a = _agent(si)
        _set_level(a, 3)
        trials = [(m, m.bit_length() - 1, 0.5, local, 1.0) for m in (2, 4, 8, 16, 32)]
        sc, _ = _synthetic(a, trials)
        assert not [k for k in a.s.nodes("PredictorCandidate") if a.s.node(k)["attrs"].get("authored") == 1]
        if si == 1:
            assert a.s.node(sc)["attrs"]["status"] == "exhausted"


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
