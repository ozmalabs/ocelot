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


def _agent(self_improvement=1, authoring=1):
    from substrate.world_adapter import WorldAdapter
    a = WorldAdapter(seeds=("prediction_world", "prediction_self_improvement"))
    a.inner.set_attr(a.s.nodes("PredictionPolicy")[0], "self_improvement", int(self_improvement))
    a.inner.set_attr(a.s.nodes("PredictionPolicy")[0], "authoring", int(authoring))
    return a


def _live(a, n, seed_base=1000):
    for i in range(n):
        pw.run_episode(a, seed=seed_base + i)
        while pw.run_experiments(a) or pw.run_residual_fits(a):
            pass
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


def _authored(a):
    return [a.s.node(k)["attrs"] for k in a.s.nodes("PredictorCandidate")
            if a.s.node(k)["attrs"].get("authored") == 1]


def _concerns(a):
    return [(a.s.node(c)["attrs"]["level"], a.s.node(c)["attrs"]["status"]) for c in a.s.nodes("SelfConcern")
            if a.s.node(c)["attrs"].get("kind") == "prediction_surprise"]


def test_three_arms_authoring_carries_it_through_level_5():
    """on: masters all five levels with models it authored (a composite at
    L4, two residual-fitted context layers at L5); no_authoring: only its
    born-with models, stuck at L4; off: notices but cannot change, stuck at L2."""
    on, no_auth, off = _agent(1), _agent(1, 0), _agent(0)
    cur_on, cur_na, cur_off = (_live(a, 60, seed_base=2024) for a in (on, no_auth, off))

    assert cur_on["current_level"] == 5 and cur_on["mastered_through"] == 5
    authored = _authored(on)
    assert (4, "composition", "") in [(k["authored_level"], k["authored_by"], k["sig"]) for k in authored]
    p = on.s.node(on.s.nodes("Predictor")[0])["attrs"]
    # the held model: the L4 composite with both context layers, fitted from its own L5 residual
    assert (p["mask"], p["n_layers"], p["ctx_bits"]) == (ACC1 | RATIO, 2, 3)
    assert p["sig"].startswith("+reversal") and p["sig"].endswith("+after_reversal")
    assert len(on.s.nodes("Adoption")) == 5

    assert cur_na["current_level"] == 4 and cur_na["mastered_through"] == 3
    assert _authored(no_auth) == [] and len(no_auth.s.nodes("ResidualFit")) == 0
    assert (4, "exhausted") in _concerns(no_auth)

    assert cur_off["current_level"] == 2 and len(off.s.nodes("Experiment")) == 0
    assert len(off.s.nodes("Adoption")) == 0 and _authored(off) == []
    assert _concerns(off) == [(2, "open")]     # it still notices


def test_layered_model_beats_its_parent_on_held_out_bounce_under_gravity():
    """The authored layers, replayed on unseen level-5 episodes: the residual
    fits generalise and cost nothing on level 3."""
    a = _agent(1)
    _live(a, 60, seed_base=2024)
    p = pw.model_of(a.s.node(a.s.nodes("Predictor")[0])["attrs"])
    held = [pw.simulate(5, 10**6 + s) for s in range(5)]
    layered = sum(pw.replay(t, p) for t in held) / 5
    parent = sum(pw.replay(t, ACC1 | RATIO) for t in held) / 5
    assert layered < 0.16 and parent > 0.5
    assert sum(pw.replay(pw.simulate(3, 10**6 + s), p) for s in range(5)) / 5 < 0.05


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
                                      "candidate_sig": "", "control_sig": p["sig"],
                                      "candidate_name": f"m{mask}"})
        d = S.add_node("SeedDelta", {"variation_op": "predictor_edit", "candidate_form": "f",
                                     "candidate_reflect": 0, "candidate_rank": rank, "candidate_mask": mask,
                                     "candidate_name": f"m{mask}", "control_form": p["form"],
                                     "control_reflect": p["reflect"], "control_mask": p["mask"],
                                     "control_name": p["model"], "candidate_sig": "",
                                     "control_sig": p["sig"]})
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


def test_no_composite_without_a_local_winner_or_when_off():
    for si, local in ((1, 0.45), (0, 0.0)):
        a = _agent(si)
        _set_level(a, 3)
        trials = [(m, m.bit_length() - 1, 0.5, local, 1.0) for m in (2, 4, 8, 16, 32)]
        sc, _ = _synthetic(a, trials)
        assert _authored(a) == []
        # nothing to compose: when on, the agent asks where its residual lives instead
        assert len(a.s.nodes("ResidualFit")) == (1 if si == 1 else 0)
        if si == 1:
            assert a.s.node(sc)["attrs"]["status"] == "exhausted"


def test_residual_fit_authors_a_layer_on_the_heaviest_atom():
    """A done ResidualFit: the agent authors its current model plus a layer on
    the atom holding the most residual (where the fit helps), and reopens."""
    a = _agent(1)
    _set_level(a, 3)
    S, I = a.s, a.inner
    trials = [(m, m.bit_length() - 1, 0.5, 0.45, 1.0) for m in (2, 4, 8, 16, 32)]
    sc, _ = _synthetic(a, trials)
    (rf,) = S.nodes("ResidualFit")
    for bit, atom, resid, gain in ((1, "reversal", 10.0, 9.0), (2, "after_reversal", 20.0, -1.0)):
        c = S.add_node("ResidualCell", {"ctx_bit": bit, "atom": atom, "kind": "new", "mode": "level",
                                        "residual_sum": resid, "fit_gain": gain,
                                        **{f"{ax}{j}": float(j) for ax in "xy" for j in range(5)}})
        I.add_edge_unchecked(rf, "has_cell", c)
    I.set_attr(rf, "status", "done")
    I.run_rules()
    (k,) = _authored(a)
    # after_reversal holds more residual but its fit does not help: only reversal is authored
    assert (k["sig"], k["n_layers"], k["ctx_bits"], k["l0_bit"], k["l0_y2"], k["l0_y4"]) == (
        "+reversal", 1, 1, 1, 2.0, 4.0)
    assert k["mask"] == VEL and k["name"] == "velocity + reversal layer"
    assert S.node(sc)["attrs"]["status"] == "open"


def _layered_agent():
    """An agent at level 3 holding velocity+reflect | acceleration+reflect with
    two layers, its concern exhausted with nothing to compose."""
    a = _agent(1)
    _set_level(a, 3)
    S, I = a.s, a.inner
    p = S.nodes("Predictor")[0]
    model = {"mask": 2 | ACC1, "model": "m", "n_layers": 2, "ctx_bits": 3, "sig": "+reversal+after_reversal",
             "l0_bit": 1, "l1_bit": 2, **{f"l{i}_{ax}{j}": 0.5 for i in range(2) for ax in "xy" for j in range(5)}}
    for key, v in model.items():
        I.set_attr(p, key, v)
    return a


def test_revision_refits_one_of_its_own_layers():
    """1.3.0: a refit cell revises a layer the model holds -- same layers,
    that layer's coefficients replaced, the others kept."""
    a = _layered_agent()
    S, I = a.s, a.inner
    trials = [(m, m.bit_length() - 1, 0.5, 0.45, 1.0) for m in (1, 2, 4, 8, 16, 32)]
    sc, _ = _synthetic(a, trials)
    (rf,) = S.nodes("ResidualFit")
    c = S.add_node("ResidualCell", {"ctx_bit": 2, "atom": "after_reversal", "kind": "refit", "mode": "pooled",
                                    "residual_sum": 5.0, "fit_gain": 2.0,
                                    **{f"{ax}{j}": 9.0 for ax in "xy" for j in range(5)}})
    I.add_edge_unchecked(rf, "has_cell", c)
    I.set_attr(rf, "status", "done")
    I.run_rules()
    (k,) = [k for k in _authored(a) if k["authored_by"] == "residual_refit"]
    assert (k["n_layers"], k["ctx_bits"], k["l0_bit"], k["l1_bit"]) == (2, 3, 1, 2)
    assert (k["l0_x0"], k["l1_x0"], k["l1_y4"]) == (0.5, 9.0, 9.0)
    assert k["sig"] == "+reversal+after_reversal~after_reversal@3/pooled"


def test_revision_prunes_components_and_drops_its_last_layer():
    """1.3.0: with nothing to compose, the agent also authors its model minus
    each base component, and minus its last layer."""
    a = _layered_agent()
    trials = [(m, m.bit_length() - 1, 0.5, 0.45, 1.0) for m in (1, 2, 4, 8, 16, 32)]
    _synthetic(a, trials)
    by = {}
    for k in _authored(a):
        by.setdefault(k["authored_by"], []).append(k)
    assert sorted(k["mask"] for k in by["prune_component"]) == [2, ACC1]
    assert all(k["n_layers"] == 2 for k in by["prune_component"])
    (d,) = by["drop_layer"]
    assert (d["mask"], d["n_layers"], d["ctx_bits"], d["l0_bit"], d["l1_bit"]) == (2 | ACC1, 1, 1, 1, 0)
    # authored once: running the rules again adds nothing
    n = len(_authored(a))
    a.inner.run_rules()
    assert len(_authored(a)) == n


def _lucky_streak_agent(surprises):
    """An agent at the last level (5) with recorded episodes of these mean
    surprises under its current model."""
    a = _agent(0)
    S, I = a.s, a.inner
    _set_level(a, 5)
    for i, m in enumerate(surprises):
        e = S.add_node("PredictionEpisode", {"seq": i, "level": 5, "level_index": i + 1, "mean_surprise": m,
                                             "scored": 1, "seed": i, "trace": "{}"})
        I.add_edge_unchecked(a.agent, "has_prediction_episode", e)
    I.run_rules()
    return a.s.node(a.s.nodes("PredictionCurriculum")[0])["attrs"]


def test_robust_mastery_ignores_a_lucky_streak():
    """1.4.0: mastery needs the upper confidence bound of the last 5 episodes'
    mean at or under the floor, not three lucky episodes in a row."""
    lucky = _lucky_streak_agent([0.25, 0.22, 0.24, 0.14, 0.13, 0.14])
    assert lucky.get("mastered_through") != 5
    steady = _lucky_streak_agent([0.25, 0.10, 0.11, 0.09, 0.10, 0.11])
    assert steady.get("mastered_through") == 5


def _stat(a, kind, world_kind="open"):
    (o,) = [o for o in a.s.nodes("PredictionOperatorStat") if a.s.node(o)["attrs"]["kind"] == kind
            and a.s.node(o)["attrs"]["world_kind"] == world_kind]
    return o


def test_operator_record_counts_judged_trials():
    a = _agent(0)
    S, I = a.s, a.inner
    sc, (x0, x1) = _synthetic(a, [(ACC, 2, 0.5, 0.0, 0.4), (ACC1, 3, 0.5, 0.0, 0.2)])
    for x in (x0, x1):
        I.set_attr(x, "candidate_operator", "base")
        I.set_attr(x, "world_kind", "open")
    I.run_rules()
    st = S.node(_stat(a, "base"))["attrs"]
    assert (st["tried"], st["supported"], st["adopted"]) == (2, 2, 1)


def _concern_with_composite(a, base=(10, 0), comp=(2, 2)):
    S, I = a.s, a.inner
    _set_level(a, 3)
    for kind, (tried, sup) in (("base", base), ("composition", comp)):
        I.set_attr(_stat(a, kind), "tried", tried)
        I.set_attr(_stat(a, kind), "supported", sup)
    k = S.add_node("PredictorCandidate", {"form": "select", "reflect": -1, "authored": 1,
                                          "authored_by": "composition", "mask": ACC1 | RATIO, "sig": "",
                                          "rank": 12, "name": "comp", "n_layers": 0, "ctx_bits": 0})
    I.add_edge_unchecked(a.agent, "has_predictor_candidate", k)
    sc = S.add_node("SelfConcern", {"kind": "prediction_surprise", "status": "open", "level": 3})
    I.add_edge_unchecked(a.agent, "has_self_concern", sc)
    I.run_rules()
    return sorted(S.node(x)["attrs"].get("candidate_name") for x in S.nodes("Experiment"))


def test_meta_search_trials_the_best_yielding_operator_first():
    """1.4.0: with its own record saying base models rarely pass (0 of 10) and
    composites do (2 of 2), the agent trials the composite alone first; with
    meta_search off it trials everything at once."""
    assert _concern_with_composite(_agent(1)) == ["comp"]
    flat = _agent(1)
    flat.inner.set_attr(flat.s.nodes("PredictionPolicy")[0], "meta_search", 0)
    assert len(_concern_with_composite(flat)) == 6


def test_meta_search_skips_a_low_yield_operator():
    """An operator tried meta_min_trials times with yield under meta_min_yield
    is skipped (base at 0 of 20, composite at 2 of 2: the composite alone;
    both at 0 of 20: nothing). 1.6.0: skip_last_resort (off by default) trials
    skipped operators once nothing else is left."""
    assert _concern_with_composite(_agent(1), base=(20, 0), comp=(2, 2)) == ["comp"]
    assert _concern_with_composite(_agent(1), base=(20, 0), comp=(20, 0)) == []
    lr = _agent(1)
    lr.inner.set_attr(lr.s.nodes("PredictionPolicy")[0], "skip_last_resort", 1)
    assert len(_concern_with_composite(lr, base=(20, 0), comp=(20, 0))) == 6


def test_the_record_is_kept_per_kind_of_world():
    """1.6.0: a poor record for base models in BOX worlds does not skip them in
    open space (this concern has no episodes: open by default)."""
    a = _agent(1)
    a.inner.set_attr(_stat(a, "base", "box"), "tried", 20)
    a.inner.set_attr(_stat(a, "composition", "box"), "tried", 20)
    assert len(_concern_with_composite(a, base=(0, 0), comp=(0, 0))) == 6


def test_an_operator_others_built_on_is_never_skipped():
    """1.5.0: base at 0 supported of 20 but credited with enabling a supported
    composite is not skipped: its candidates join the best-yield batch."""
    a = _agent(1)
    a.inner.set_attr(_stat(a, "base"), "enabled", 9)
    names = _concern_with_composite(a, base=(20, 0), comp=(20, 0))
    assert len(names) == 5 and "comp" not in names


def test_an_expert_predicts_where_it_fits():
    """1.5.0: a primary acceleration+reflect model with ratio held as an
    expert predicts damped glide (level 4) nearly as well as ratio alone,
    while the primary alone misses."""
    model = {"mask": ACC1, "x1_mask": RATIO}
    for seed in range(3):
        tr = pw.simulate(4, seed)
        assert pw.replay(tr, model) < 0.1 < pw.replay(tr, ACC1)


def test_agent_proposes_and_adopts_a_policy_change():
    """1.5.0: with its curriculum mastered and meta_proposals on, the agent
    proposes the policy grammar's changes; measured results written back are
    judged, and the best supported one is adopted into its policy."""
    a = _agent(1)
    S, I = a.s, a.inner
    cur, pol = S.nodes("PredictionCurriculum")[0], S.nodes("PredictionPolicy")[0]
    I.set_attr(cur, "current_level", 5)
    I.set_attr(cur, "mastered_through", 5)
    I.set_attr(pol, "meta_proposals", 1)
    I.run_rules()
    props = S.nodes("MetaProposal")
    assert len(props) == 7
    big = None
    for m in props:
        at = S.node(m)["attrs"]
        good = (at["param"], at["factor"]) == ("meta_min_trials", 0.5)
        ok = (at["param"], at["factor"]) == ("retention_weight", 2.0)
        one_level = (at["param"], at["factor"]) == ("min_gain", 0.5)
        big = m if one_level else big
        # min_gain x0.5 has the biggest net, but carried by one practice level (1 win, 3 losses): refuted
        for k, v in (("control_total", 1.0), ("variant_total", 0.99 if ok else (0.5 if one_level else 1.0)),
                     ("control_experiments", 100), ("variant_experiments", 70 if good else 100),
                     ("level_wins", 1 if one_level else (5 if (good or ok) else 0)),
                     ("level_losses", 3 if one_level else 0), ("status", "done")):
            I.set_attr(m, k, v)
    I.run_rules()
    at = S.node(pol)["attrs"]
    assert S.node(big)["attrs"]["outcome"] == "refuted"
    # nets: meta_min_trials x0.5 = 0.03, retention_weight x2 = 0.01; the best is adopted, only it
    assert at["meta_min_trials"] == 4 and at["retention_weight"] == 1.0
    assert at["meta_adopted"].startswith("meta_min_trials")
    # 1.6.0: the round closed and the next round's proposals start from the adopted policy
    assert at["meta_round"] == 1
    nxt = [S.node(m)["attrs"] for m in S.nodes("MetaProposal") if S.node(m)["attrs"]["round"] == 1]
    assert len(nxt) == 7
    assert [m["current"] for m in nxt if m["param"] == "meta_min_trials"] == [4, 4]


def test_agent_selects_its_judge_from_its_own_calibration():
    """1.7.0: with meta_calibrate on, round 0's proposals carry a second
    practice set's realised net (p2_net). The loosest judge's favourite (big
    net, one lucky level, lost badly elsewhere) realises a loss on P2; the
    tail judge's favourite realises a gain -- the agent adopts the tail
    judge, and adopts that judge's choice."""
    a = _agent(1)
    S, I = a.s, a.inner
    cur, pol = S.nodes("PredictionCurriculum")[0], S.nodes("PredictionPolicy")[0]
    I.set_attr(cur, "current_level", 5)
    I.set_attr(cur, "mastered_through", 5)
    I.set_attr(pol, "meta_proposals", 1)
    I.set_attr(pol, "meta_calibrate", 1)
    I.run_rules()
    for m in S.nodes("MetaProposal"):
        at = S.node(m)["attrs"]
        key = (at["param"], at["factor"])
        # (variant_total, wins, losses, worst_level_loss, p2_net)
        v = {("min_gain", 0.5): (0.5, 5, 3, 0.4, -0.3),               # big net, a heavy tail: P2 loses
             ("meta_min_trials", 0.5): (0.97, 6, 0, 0.01, 0.02),      # modest, safe: P2 gains
             }.get(key, (1.0, 0, 0, 0.0, 0.0))
        for k, x in (("control_total", 1.0), ("variant_total", v[0]), ("control_experiments", 100),
                     ("variant_experiments", 100), ("level_wins", v[1]), ("level_losses", v[2]),
                     ("worst_level_loss", v[3]), ("p2_net", v[4]), ("status", "done")):
            I.set_attr(m, k, x)
    I.run_rules()
    at = S.node(pol)["attrs"]
    assert at["meta_judge_selected"] == 1 and at["meta_judge_active"] == "tail"
    assert at["meta_min_trials"] == 4 and at["min_gain"] == 0.2


def test_loop_seed_frozen_and_protected():
    from substrate.boot_all import _FROZEN_SEED_IDS
    assert "prediction_self_improvement" in _FROZEN_SEED_IDS
    assert "prediction_world" not in _FROZEN_SEED_IDS     # the part the agent changes
    man = json.loads((ROOT / "seeds/frozen_core_manifest.json").read_text())
    assert "prediction_self_improvement" in man["frozen_seed_ids"]
    loop = json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())
    assert loop["depends_on"] == []
    integ = (ROOT / "seeds/improvement_integrity.json").read_text()
    for t in ("PredictionPolicy", "PredictionCurriculum", "PredictorCandidate", "PredictionOperatorStat",
              "MetaProposal"):
        assert f'"{t}"' in integ
