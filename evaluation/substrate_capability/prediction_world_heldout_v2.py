#!/usr/bin/env python3
"""Held-out levels over many draws, and whether the agent's learned search
makes later improvement cheaper (2026-10-10). Pre-registered in
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_V3_20261010.md.

For each of D draws (draw d: heldout_levels(int(hash[:8], 16) + 7919*d, 8),
level ids 101 + 8d + j), each level and each seed base, four arms, each
starting from the same state:
  on_trained        the curriculum (60 episodes), then the level; its search
                    statistics (PredictionOperatorStat) as the curriculum left them
  on_trained_reset  the same trained agent (a fork), statistics reset to zero
  on_trained_flat   the same trained agent, meta_search off (every untried
                    candidate trialled at once, as in loop 1.3.0)
  on_naive          a newborn agent dropped straight into the level
The trained agent is trained once per seed base per worker and forked
(fork_full_copy_experiment), so every trained arm starts from an identical
copy. Up to BUDGET episodes at the level, stopping at robust mastery.

Usage: <this> <draw_hash> [draws=6]
Writes evaluation/reports/prediction_world_heldout_v2_<draw_hash[:8]>_20261010.json.
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
K_LEVELS = 8
SEED_BASES = (1000, 2024, 5000, 9000)
ARMS = ("on_trained", "on_trained_reset", "on_trained_flat", "on_naive")
_TRAINED = {}


def _settle(pw, a):
    n_exp = n_fit = 0
    while True:
        done, fits = pw.run_experiments(a), pw.run_residual_fits(a)
        n_exp, n_fit = n_exp + len(done), n_fit + len(fits)
        if not done and not fits:
            return n_exp, n_fit


class _Fork:
    """A copy of a trained agent: the native substrate deep-copied, wrapped
    the way WorldAdapter wraps it."""
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


def job(args):
    seed_base, arm, level, spec, draw = args
    from domains import prediction_world as pw
    pw.LEVELS[level] = spec
    t0 = time.time()
    a = _newborn() if arm == "on_naive" else _trained(pw, seed_base)
    S, I = a.s, a.inner
    pol, cur = S.nodes("PredictionPolicy")[0], S.nodes("PredictionCurriculum")[0]
    if arm == "on_trained_reset":
        for o in S.nodes("PredictionOperatorStat"):
            for k in ("tried", "supported", "adopted"):
                I.set_attr(o, k, 0)
    I.set_attr(pol, "meta_search", 0 if arm == "on_trained_flat" else 1)
    start_model = pw.model_of(S.node(S.nodes("Predictor")[0])["attrs"])
    fresh = [pw.simulate(level, 10**7 + s) for s in range(5)]
    initial = sum(pw.replay(t, start_model) for t in fresh) / 5
    n_adopt0, n_auth0 = len(S.nodes("Adoption")), sum(
        1 for k in S.nodes("PredictorCandidate") if S.node(k)["attrs"].get("authored") == 1)
    I.set_attr(cur, "current_level", level)
    I.set_attr(cur, "max_level", level)
    exps = fits = 0
    mastered_at, curve = None, []
    for i in range(BUDGET):
        ep = pw.run_episode(a, seed=seed_base + 100000 + level * 100 + i)
        curve.append(round(ep["mean_surprise"], 4))
        e, f = _settle(pw, a)
        exps, fits = exps + e, fits + f
        if S.node(cur)["attrs"].get("mastered_through") == level:
            mastered_at = i + 1
            break
    p = S.node(S.nodes("Predictor")[0])["attrs"]
    final = sum(pw.replay(t, pw.model_of(p)) for t in fresh) / 5
    return {"draw": draw, "seed_base": seed_base, "arm": arm, "level": level,
            "mastered": mastered_at is not None, "episodes_to_master": mastered_at, "episodes": len(curve),
            "experiments": exps, "residual_fits": fits, "adoptions": len(S.nodes("Adoption")) - n_adopt0,
            "authored": sum(1 for k in S.nodes("PredictorCandidate")
                            if S.node(k)["attrs"].get("authored") == 1) - n_auth0,
            "initial_surprise": round(initial, 4), "final_surprise": round(final, 4),
            "final_model": p.get("model"), "surprise_curve": curve, "elapsed_s": round(time.time() - t0, 1)}


def sign_test(wins, losses):
    """Two-sided exact binomial sign test p-value (ties dropped)."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def paired(rows, a, b, key, lower_is_better=True):
    idx = {(r["draw"], r["seed_base"], r["level"]): r for r in rows if r["arm"] == b}
    w = l = t = 0
    diffs = []
    for r in rows:
        if r["arm"] != a:
            continue
        o = idx[(r["draw"], r["seed_base"], r["level"])]
        x, y = r[key], o[key]
        diffs.append(x - y)
        if x == y:
            t += 1
        elif (x < y) == lower_is_better:
            w += 1
        else:
            l += 1
    return {"a": a, "b": b, "key": key, "a_better": w, "b_better": l, "ties": t,
            "mean_diff_a_minus_b": round(sum(diffs) / len(diffs), 4), "sign_test_p": round(sign_test(w, l), 5)}


def main():
    draw_hash = sys.argv[1]
    n_draws = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    from domains import prediction_world as pw
    base = int(draw_hash[:8], 16)
    draws = {d: pw.heldout_levels(base + 7919 * d, K_LEVELS, first_id=101 + K_LEVELS * d) for d in range(n_draws)}
    # one worker per seed base x arm-group keeps each worker's trained cache small; order jobs so a worker
    # mostly sees one seed base
    jobs = [(sb, arm, lv, spec, d) for sb in SEED_BASES for d, lv_specs in draws.items()
            for lv, spec in lv_specs.items() for arm in ARMS]
    with ProcessPoolExecutor(max_workers=int(os.environ.get("PW_WORKERS", "12"))) as ex:
        rows = list(ex.map(job, jobs, chunksize=8))
    summary = {}
    for arm in ARMS:
        r = [x for x in rows if x["arm"] == arm]
        ad = sum(x["adoptions"] for x in r)
        summary[arm] = {"runs": len(r), "mastered": sum(x["mastered"] for x in r),
                        "mean_final_surprise": round(sum(x["final_surprise"] for x in r) / len(r), 4),
                        "mean_initial_surprise": round(sum(x["initial_surprise"] for x in r) / len(r), 4),
                        "mean_experiments": round(sum(x["experiments"] for x in r) / len(r), 2),
                        "adoptions": ad,
                        "experiments_per_adoption": round(sum(x["experiments"] for x in r) / ad, 2) if ad else None}
    tests = {
        "H3_trained_vs_naive_final_surprise": paired(rows, "on_trained", "on_naive", "final_surprise"),
        "H4_learned_vs_reset_experiments": paired(rows, "on_trained", "on_trained_reset", "experiments"),
        "H4_learned_vs_reset_final_surprise": paired(rows, "on_trained", "on_trained_reset", "final_surprise"),
        "H4b_learned_vs_flat_experiments": paired(rows, "on_trained", "on_trained_flat", "experiments"),
        "H4b_learned_vs_flat_final_surprise": paired(rows, "on_trained", "on_trained_flat", "final_surprise"),
        "trained_vs_naive_mastered": paired(rows, "on_trained", "on_naive", "mastered", lower_is_better=False),
    }
    rep = {"draw_hash": draw_hash, "draws": draws, "seed_bases": SEED_BASES, "budget": BUDGET,
           "loop_version": json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())["version"],
           "summary": summary, "tests": tests, "rows": rows}
    out = ROOT / f"evaluation/reports/prediction_world_heldout_v2_{draw_hash[:8]}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    print(json.dumps(tests, indent=1))


if __name__ == "__main__":
    main()
