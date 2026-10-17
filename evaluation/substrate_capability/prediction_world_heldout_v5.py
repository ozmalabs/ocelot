#!/usr/bin/env python3
"""Held-out levels over many draws for loop 1.7.0 (2026-10-10): the agent's
policy rounds with a judge it selects itself from its own calibration evidence,
against the same rounds under the fixed 1.6.0 judge. Pre-registered in
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_V6_20261010.md.

Phase 1 runs twice per seed base, on the same practice levels:
  calibrated  meta_calibrate on: round 0 is measured on practice set P1 and
              on a second fresh set P2; the graph picks its judge (net / sign /
              tail) by the net its choices realise on P2; rounds 1-2 use it
  fixed       meta_calibrate off, judge 'sign' (1.6.0's)
Phase 2 arms: on_trained (policy as born), on_trained_meta (the calibrated
phase's policy), on_trained_meta_fixed (the fixed phase's policy).
(The text below describing 1.6.0's phase 1 still applies to each phase.)

Phase 1 (per seed base): train the agent on the curriculum; switch its
meta_proposals on; for each of META_ROUNDS rounds its graph proposes policy
changes (MetaProposal) from the policy the earlier rounds left; each is
measured against a control on PRACTICE levels drawn fresh for that round
(heldout_levels(10**9 + seed_base + 7919*(round+1), P) -- a seed range no
evaluation uses, never reused across rounds), each run a fork of the trained
agent carrying the current policy: practice-level surprise plus the surprise
its final model adds on the curriculum levels, experiments spent, and per
level whether the variant's weighed cost is lower or higher than the
control's; the graph judges, adopts and closes the round.

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

Usage: <this> <draw_hash> <first_draw> <end_draw> [meta.json]
  (draws first_draw..end_draw-1; meta.json reuses a phase-1 result, else it
  is computed and written next to the report)
Writes evaluation/reports/prediction_world_heldout_v4_<draw_hash[:8]>_d<first>-<end>_20261010.json.
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
PRACTICE_LEVELS = 8
META_ROUNDS = 3
K_LEVELS = 8
SEED_BASES = (1000, 2024, 5000, 9000)
ARMS = ("on_trained", "on_trained_meta", "on_trained_meta_fixed")
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
    trained agent carrying the current policy, with one parameter scaled, at
    one practice level."""
    seed_base, level, spec, param, factor, policy, pset = args
    from domains import prediction_world as pw
    pw.LEVELS[level] = spec
    a = _trained(pw, seed_base)
    pol = a.s.nodes("PredictionPolicy")[0]
    for k, v in policy.items():
        a.inner.set_attr(pol, k, v)
    if param is not None:
        a.inner.set_attr(pol, param, a.s.node(pol)["attrs"][param] * factor)
    r = _at_level(pw, a, level, seed_base + 500000 + level * 100, PRACTICE_BUDGET)
    return {"seed_base": seed_base, "level": level, "param": param, "factor": factor, "pset": pset,
            "total": r["final_surprise"] + r["retention_harm"], "experiments": r["experiments"],
            "cost": r["final_surprise"] + r["retention_harm"] + 0.001 * r["experiments"]}


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


def _measure(rs, ctl, at):
    v = {r["level"]: r for r in rs if r["param"] == at["param"] and r["factor"] == at["factor"]}
    return v, {
        "control_total": round(sum(r["total"] for r in ctl.values()), 6),
        "variant_total": round(sum(r["total"] for r in v.values()), 6),
        "control_experiments": sum(r["experiments"] for r in ctl.values()),
        "variant_experiments": sum(r["experiments"] for r in v.values()),
        "level_wins": sum(1 for lv in ctl if v[lv]["cost"] < ctl[lv]["cost"] - 1e-9),
        "level_losses": sum(1 for lv in ctl if v[lv]["cost"] > ctl[lv]["cost"] + 1e-9),
        "worst_level_loss": round(max(v[lv]["cost"] - ctl[lv]["cost"] for lv in ctl), 6)}


def meta_phase(ex, pw, calibrate):
    """Phase 1 for one judge regime: rounds of self-proposed policy changes,
    each measured on fresh practice levels; with `calibrate`, round 0 is
    also measured on a second fresh practice set (P2) for the agent's choice
    of judge."""
    agents = {}
    for sb in SEED_BASES:
        a = _newborn()
        for i in range(CURRICULUM_EPISODES):
            pw.run_episode(a, seed=sb + i)
            _settle(pw, a)
        pol = a.s.nodes("PredictionPolicy")[0]
        a.inner.set_attr(pol, "meta_proposals", 1)
        a.inner.set_attr(pol, "meta_calibrate", 1 if calibrate else 0)
        a.inner.run_rules()
        agents[sb] = a
    for rnd in range(META_ROUNDS):
        jobs, pending = [], {}
        for sb, a in agents.items():
            S = a.s
            pol = S.node(S.nodes("PredictionPolicy")[0])["attrs"]
            policy = {k: pol[k] for k in POLICY_PARAMS}
            mine = [m for m in S.nodes("MetaProposal") if S.node(m)["attrs"].get("round") == rnd
                    and S.node(m)["attrs"].get("status") == "requested"]
            if not mine:
                continue
            pending[sb] = mine
            psets = {"P1": pw.heldout_levels(10**9 + sb + 7919 * (rnd + 1), PRACTICE_LEVELS, first_id=901)}
            if calibrate and rnd == 0:
                psets["P2"] = pw.heldout_levels(10**9 + sb + 7919 * 101, PRACTICE_LEVELS, first_id=951)
            props = [(None, None)] + [(S.node(m)["attrs"]["param"], S.node(m)["attrs"]["factor"]) for m in mine]
            for pset, levels in psets.items():
                for lv, spec in levels.items():
                    for param, factor in props:
                        jobs.append((sb, lv, spec, param, factor, policy, pset))
        if not jobs:
            break
        res = list(ex.map(practice_job, jobs, chunksize=4))
        for sb, mine in pending.items():
            S, I = agents[sb].s, agents[sb].inner
            rs1 = [r for r in res if r["seed_base"] == sb and r["pset"] == "P1"]
            rs2 = [r for r in res if r["seed_base"] == sb and r["pset"] == "P2"]
            ctl1 = {r["level"]: r for r in rs1 if r["param"] is None}
            ctl2 = {r["level"]: r for r in rs2 if r["param"] is None}
            for m in mine:
                at = S.node(m)["attrs"]
                _v, meas = _measure(rs1, ctl1, at)
                for k, v in meas.items():
                    I.set_attr(m, k, v)
                if ctl2:
                    v2, _m2 = _measure(rs2, ctl2, at)
                    I.set_attr(m, "p2_net", round(sum(ctl2[lv]["cost"] - v2[lv]["cost"] for lv in ctl2), 6))
                I.set_attr(m, "status", "done")
            I.run_rules()
    out = {}
    for sb, a in agents.items():
        S = a.s
        pol = S.node(S.nodes("PredictionPolicy")[0])["attrs"]
        out[sb] = {"adopted": pol.get("meta_adopted"), "policy": {k: pol[k] for k in POLICY_PARAMS},
                   "judge": pol.get("meta_judge_active"), "judge_values": pol.get("meta_judge_values"),
                   "rounds_closed": pol.get("meta_round"),
                   "proposals": [{k: S.node(m)["attrs"].get(k) for k in (
                       "round", "param", "factor", "net", "level_wins", "level_losses", "worst_level_loss",
                       "p2_net", "outcome_net", "outcome_sign", "outcome_tail", "adopted")}
                       for m in S.nodes("MetaProposal")]}
    return out


def main():
    draw_hash, d0, d1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    meta_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    from domains import prediction_world as pw
    base = int(draw_hash[:8], 16)
    draws = {d: pw.heldout_levels(base + 7919 * d, K_LEVELS, first_id=101 + K_LEVELS * d) for d in range(d0, d1)}
    with ProcessPoolExecutor(max_workers=int(os.environ.get("PW_WORKERS", "12"))) as ex:
        if meta_path and meta_path.exists():
            meta = {k: {int(sb): v for sb, v in m.items()} for k, m in json.loads(meta_path.read_text()).items()}
        else:
            meta = {"calibrated": meta_phase(ex, pw, True), "fixed": meta_phase(ex, pw, False)}
            (ROOT / f"evaluation/reports/prediction_world_heldout_v5_{draw_hash[:8]}_meta_20261010.json").write_text(
                json.dumps(meta, indent=1) + "\n")
        print(json.dumps(meta, indent=1), flush=True)
        policy_of = lambda arm, sb: (meta["calibrated"][sb]["policy"] if arm == "on_trained_meta" else
                                     meta["fixed"][sb]["policy"] if arm == "on_trained_meta_fixed" else {})
        jobs = [(sb, arm, lv, spec, d, policy_of(arm, sb)) for sb in SEED_BASES for d, lv_specs in draws.items()
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
    tests = {}
    rep = {"draw_hash": draw_hash, "draws": draws, "seed_bases": SEED_BASES, "budget": BUDGET,
           "loop_version": json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())["version"],
           "meta_phase": meta, "summary": summary, "tests": tests, "rows": rows}
    out = ROOT / f"evaluation/reports/prediction_world_heldout_v5_{draw_hash[:8]}_d{d0}-{d1}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    print(json.dumps(tests, indent=1))


if __name__ == "__main__":
    main()
