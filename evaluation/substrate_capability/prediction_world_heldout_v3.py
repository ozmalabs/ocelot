#!/usr/bin/env python3
"""Held-out levels over many draws for loop 1.5.0 (2026-10-10): experts
(scope-confined change), provenance credit in the search record, and
self-proposed changes to the agent's own search policy. Pre-registered in
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_V4_20261010.md.

Phase 1 (per seed base): train the agent on the curriculum; switch its
meta_proposals on and let its graph propose policy changes (MetaProposal);
measure every proposal against a control on PRACTICE levels the agent draws
itself (heldout_levels(10**9 + seed_base, P) -- a seed range no evaluation
uses), each a fork of the trained agent: practice-level surprise plus the
surprise its final model adds on the curriculum levels, and experiments
spent; write the results back and let the graph judge and adopt.

Phase 2: for each draw / level / seed base, five arms from the same state:
  on_trained            the curriculum-trained agent (1.5.0: experts on, its
                        own search record, policy as born)
  on_trained_noexperts  the same, experts off
  on_trained_reset      the same, search record zeroed
  on_trained_meta       the same, with the policy its own proposals adopted
  on_naive              a newborn
Up to BUDGET episodes at the level, stopping at robust mastery. Per run:
final surprise on fresh episodes of the level, the surprise the final model
adds on the curriculum levels (retention harm), experiments.

Usage: <this> <draw_hash> [draws=6]
Writes evaluation/reports/prediction_world_heldout_v3_<draw_hash[:8]>_20261010.json.
"""
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

CURRICULUM_EPISODES = 60
BUDGET = 30
PRACTICE_BUDGET = 20
PRACTICE_LEVELS = 6
K_LEVELS = 8
SEED_BASES = (1000, 2024, 5000, 9000)
ARMS = ("on_trained", "on_trained_noexperts", "on_trained_reset", "on_trained_meta", "on_naive")
POLICY_PARAMS = ("retention_weight", "meta_min_yield", "meta_min_trials", "min_gain")
_TRAINED = {}


def _settle(pw, a):
    n_exp = 0
    while True:
        done, fits = pw.run_experiments(a), pw.run_residual_fits(a)
        n_exp += len(done)
        if not done and not fits:
            return n_exp


class _Fork:
    def __init__(self, parent):
        import substrate_rs
        from substrate.world_adapter import _AdapterNativeFacade
        native = parent.s._inner._native.fork_full_copy_experiment()
        self.inner = _AdapterNativeFacade(native)
        self.s = substrate_rs.Substrate.__new__(substrate_rs.Substrate)
        self.s._inner = self.inner
        self.agent = parent.agent


def _newborn():
    from substrate.world_adapter import WorldAdapter
    return WorldAdapter(seeds=("prediction_world", "prediction_self_improvement"))


def _trained(pw, seed_base):
    if seed_base not in _TRAINED:
        a = _newborn()
        for i in range(CURRICULUM_EPISODES):
            pw.run_episode(a, seed=seed_base + i)
            _settle(pw, a)
        _TRAINED[seed_base] = a
    return _Fork(_TRAINED[seed_base])


def _retention_harm(pw, start_model, final_model):
    harm = 0.0
    for lv in range(1, 6):
        ts = [pw.simulate(lv, 10**7 + s) for s in range(3)]
        before = sum(pw.replay(t, start_model) for t in ts) / 3
        after = sum(pw.replay(t, final_model) for t in ts) / 3
        harm += max(0.0, after - before)
    return harm


def _at_level(pw, a, level, seed0, budget, retention=True):
    S, I = a.s, a.inner
    cur = S.nodes("PredictionCurriculum")[0]
    start_model = pw.model_of(S.node(S.nodes("Predictor")[0])["attrs"])
    fresh = [pw.simulate(level, 10**7 + s) for s in range(5)]
    initial = sum(pw.replay(t, start_model) for t in fresh) / 5
    n_adopt0 = len(S.nodes("Adoption"))
    I.set_attr(cur, "current_level", level)
    I.set_attr(cur, "max_level", level)
    exps, mastered_at, curve = 0, None, []
    for i in range(budget):
        ep = pw.run_episode(a, seed=seed0 + i)
        curve.append(round(ep["mean_surprise"], 4))
        exps += _settle(pw, a)
        if S.node(cur)["attrs"].get("mastered_through") == level:
            mastered_at = i + 1
            break
    p = S.node(S.nodes("Predictor")[0])["attrs"]
    final_model = pw.model_of(p)
    final = sum(pw.replay(t, final_model) for t in fresh) / 5
    harm = _retention_harm(pw, start_model, final_model) if retention else 0.0
    return {"mastered": mastered_at is not None, "episodes_to_master": mastered_at, "episodes": len(curve),
            "experiments": exps, "adoptions": len(S.nodes("Adoption")) - n_adopt0,
            "initial_surprise": round(initial, 4), "final_surprise": round(final, 4),
            "retention_harm": round(harm, 4), "final_model": p.get("model"), "surprise_curve": curve}


def practice_job(args):
    """One practice run for a policy proposal (or the control): a fork of the
    trained agent with one policy parameter scaled, at one practice level."""
    seed_base, level, spec, param, factor = args
    from domains import prediction_world as pw
    pw.LEVELS[level] = spec
    a = _trained(pw, seed_base)
    if param is not None:
        pol = a.s.nodes("PredictionPolicy")[0]
        a.inner.set_attr(pol, param, a.s.node(pol)["attrs"][param] * factor)
    r = _at_level(pw, a, level, seed_base + 500000 + level * 100, PRACTICE_BUDGET)
    return {"seed_base": seed_base, "level": level, "param": param, "factor": factor,
            "total": r["final_surprise"] + r["retention_harm"], "experiments": r["experiments"]}


def job(args):
    seed_base, arm, level, spec, draw, policy = args
    from domains import prediction_world as pw
    pw.LEVELS[level] = spec
    t0 = time.time()
    a = _newborn() if arm == "on_naive" else _trained(pw, seed_base)
    S, I = a.s, a.inner
    pol = S.nodes("PredictionPolicy")[0]
    if arm == "on_trained_noexperts":
        I.set_attr(pol, "experts", 0)
    if arm == "on_trained_reset":
        for o in S.nodes("PredictionOperatorStat"):
            for k in ("tried", "supported", "adopted", "enabled"):
                I.set_attr(o, k, 0)
    if arm == "on_trained_meta":
        for k, v in policy.items():
            I.set_attr(pol, k, v)
    r = _at_level(pw, a, level, seed_base + 100000 + level * 100, BUDGET, retention=(arm != "on_naive"))
    return {"draw": draw, "seed_base": seed_base, "arm": arm, "level": level, **r,
            "elapsed_s": round(time.time() - t0, 1)}


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def paired(rows, a, b, key):
    idx = {(r["draw"], r["seed_base"], r["level"]): r for r in rows if r["arm"] == b}
    w = l = t = 0
    diffs = []
    for r in rows:
        if r["arm"] != a:
            continue
        o = idx[(r["draw"], r["seed_base"], r["level"])]
        x, y = key(r), key(o)
        diffs.append(x - y)
        if abs(x - y) < 1e-9:
            t += 1
        elif x < y:
            w += 1
        else:
            l += 1
    return {"a": a, "b": b, "a_better": w, "b_better": l, "ties": t,
            "mean_diff_a_minus_b": round(sum(diffs) / len(diffs), 4), "sign_test_p": round(sign_test(w, l), 6)}


def meta_phase(ex, pw):
    """Phase 1: the agent proposes policy changes; practice measures them; the
    graph judges and adopts. Returns {seed_base: {"adopted": ..., "policy": {...}, "proposals": [...]}}."""
    out = {}
    agents = {}
    for sb in SEED_BASES:
        a = _newborn()
        for i in range(CURRICULUM_EPISODES):
            pw.run_episode(a, seed=sb + i)
            _settle(pw, a)
        a.inner.set_attr(a.s.nodes("PredictionPolicy")[0], "meta_proposals", 1)
        a.inner.run_rules()
        agents[sb] = a
    jobs = []
    practice = {sb: pw.heldout_levels(10**9 + sb, PRACTICE_LEVELS, first_id=901) for sb in SEED_BASES}
    for sb, a in agents.items():
        props = [(None, None)] + [(a.s.node(m)["attrs"]["param"], a.s.node(m)["attrs"]["factor"])
                                  for m in a.s.nodes("MetaProposal")]
        for lv, spec in practice[sb].items():
            for param, factor in props:
                jobs.append((sb, lv, spec, param, factor))
    res = list(ex.map(practice_job, jobs, chunksize=4))
    for sb, a in agents.items():
        S, I = a.s, a.inner
        mine = [r for r in res if r["seed_base"] == sb]
        ctl = [r for r in mine if r["param"] is None]
        c_tot, c_exp = sum(r["total"] for r in ctl), sum(r["experiments"] for r in ctl)
        for m in S.nodes("MetaProposal"):
            at = S.node(m)["attrs"]
            v = [r for r in mine if r["param"] == at["param"] and r["factor"] == at["factor"]]
            I.set_attr(m, "control_total", round(c_tot, 6))
            I.set_attr(m, "variant_total", round(sum(r["total"] for r in v), 6))
            I.set_attr(m, "control_experiments", c_exp)
            I.set_attr(m, "variant_experiments", sum(r["experiments"] for r in v))
            I.set_attr(m, "status", "done")
        I.run_rules()
        pol = S.node(S.nodes("PredictionPolicy")[0])["attrs"]
        out[sb] = {"adopted": pol.get("meta_adopted"), "policy": {k: pol[k] for k in POLICY_PARAMS},
                   "proposals": [{k: S.node(m)["attrs"].get(k) for k in (
                       "param", "factor", "control_total", "variant_total", "control_experiments",
                       "variant_experiments", "net", "outcome", "adopted")} for m in S.nodes("MetaProposal")]}
    return out


def main():
    draw_hash = sys.argv[1]
    n_draws = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    from domains import prediction_world as pw
    base = int(draw_hash[:8], 16)
    draws = {d: pw.heldout_levels(base + 7919 * d, K_LEVELS, first_id=101 + K_LEVELS * d) for d in range(n_draws)}
    with ProcessPoolExecutor(max_workers=int(os.environ.get("PW_WORKERS", "12"))) as ex:
        meta = meta_phase(ex, pw)
        print(json.dumps(meta, indent=1), flush=True)
        jobs = [(sb, arm, lv, spec, d, meta[sb]["policy"]) for sb in SEED_BASES for d, lv_specs in draws.items()
                for lv, spec in lv_specs.items() for arm in ARMS]
        rows = list(ex.map(job, jobs, chunksize=5))
    cost = lambda r: r["final_surprise"] + r["retention_harm"] + 0.001 * r["experiments"]
    summary = {}
    for arm in ARMS:
        r = [x for x in rows if x["arm"] == arm]
        summary[arm] = {"runs": len(r), "mastered": sum(x["mastered"] for x in r),
                        "mean_final_surprise": round(sum(x["final_surprise"] for x in r) / len(r), 4),
                        "mean_retention_harm": round(sum(x["retention_harm"] for x in r) / len(r), 4),
                        "mean_experiments": round(sum(x["experiments"] for x in r) / len(r), 2),
                        "adoptions": sum(x["adoptions"] for x in r)}
    fs = lambda r: r["final_surprise"]
    tests = {
        "H3_trained_vs_naive_final_surprise": paired(rows, "on_trained", "on_naive", fs),
        "H6_experts_vs_noexperts_final_surprise": paired(rows, "on_trained", "on_trained_noexperts", fs),
        "H6_experts_vs_noexperts_retention_harm": paired(rows, "on_trained", "on_trained_noexperts",
                                                         lambda r: r["retention_harm"]),
        "H4_learned_vs_reset_experiments": paired(rows, "on_trained", "on_trained_reset", lambda r: r["experiments"]),
        "H4_learned_vs_reset_final_surprise": paired(rows, "on_trained", "on_trained_reset", fs),
        "H5_meta_vs_trained_weighed_cost": paired(rows, "on_trained_meta", "on_trained", cost),
        "H5_meta_vs_trained_final_surprise": paired(rows, "on_trained_meta", "on_trained", fs),
    }
    rep = {"draw_hash": draw_hash, "draws": draws, "seed_bases": SEED_BASES, "budget": BUDGET,
           "loop_version": json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())["version"],
           "meta_phase": meta, "summary": summary, "tests": tests, "rows": rows}
    out = ROOT / f"evaluation/reports/prediction_world_heldout_v3_{draw_hash[:8]}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    print(json.dumps(tests, indent=1))


if __name__ == "__main__":
    main()
