#!/usr/bin/env python3
"""Held-out levels and the cost of improvement (2026-10-10). Pre-registered in
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_20261010.md;
the agent, its seeds and this harness are frozen at the pre-registration
commit, and the held-out levels are drawn from that commit's hash.

Arms, each run independently per held-out level (the same starting state for
every level, so one hard level does not block the others):
  on_trained            the curriculum (60 episodes) with self-improvement and
                        authoring on, then the held-out level
  no_authoring_trained  the curriculum with authoring off, then the level
  off_trained           the curriculum with self-improvement off, then the level
  on_naive              a newborn agent (self-improvement and authoring on)
                        dropped straight into the level
Per (seed base, arm, level): up to BUDGET episodes at the level, stopping when
the agent's own curriculum marks it mastered (`window` consecutive episodes
at or under the floor). Recorded: mastered, episodes to mastery, experiments
and residual fits the graph requested, models authored, and the final
model's surprise on fresh episodes of the level.

Usage: <this> <draw_hash> [seed_base ...]   (default seed bases 1000 2024 5000 9000)
Writes evaluation/reports/prediction_world_heldout_v1_<draw_hash[:8]>_loop<version>_20261010.json.
"""
import json
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
ARMS = {"on_trained": (1, 1, True), "no_authoring_trained": (1, 0, True), "off_trained": (0, 1, True),
        "on_naive": (1, 1, False)}


def _settle(pw, a):
    n_exp = n_fit = 0
    while True:
        done, fits = pw.run_experiments(a), pw.run_residual_fits(a)
        n_exp, n_fit = n_exp + len(done), n_fit + len(fits)
        if not done and not fits:
            return n_exp, n_fit


def job(args):
    seed_base, arm, level, spec = args
    from substrate.world_adapter import WorldAdapter
    from domains import prediction_world as pw
    pw.LEVELS[level] = spec
    si, authoring, trained = ARMS[arm]
    a = WorldAdapter(seeds=("prediction_world", "prediction_self_improvement"))
    S, I = a.s, a.inner
    pol, cur = S.nodes("PredictionPolicy")[0], S.nodes("PredictionCurriculum")[0]
    I.set_attr(pol, "self_improvement", si)
    I.set_attr(pol, "authoring", authoring)
    t0 = time.time()
    if trained:
        for i in range(CURRICULUM_EPISODES):
            pw.run_episode(a, seed=seed_base + i)
            _settle(pw, a)
    trained_through = S.node(cur)["attrs"].get("mastered_through")
    n_auth0 = sum(1 for k in S.nodes("PredictorCandidate") if S.node(k)["attrs"].get("authored") == 1)
    # the held-out level: the curriculum's current and last level
    I.set_attr(cur, "current_level", level)
    I.set_attr(cur, "max_level", level)
    surprises, exps, fits, mastered_at = [], 0, 0, None
    for i in range(BUDGET):
        ep = pw.run_episode(a, seed=seed_base + 100000 + level * 100 + i)
        surprises.append(round(ep["mean_surprise"], 4))
        e, f = _settle(pw, a)
        exps, fits = exps + e, fits + f
        if S.node(cur)["attrs"].get("mastered_through") == level:
            mastered_at = i + 1
            break
    p = S.node(S.nodes("Predictor")[0])["attrs"]
    model = pw.model_of(p)
    final = sum(pw.replay(pw.simulate(level, 10**7 + s), model) for s in range(5)) / 5
    best_base = min(sum(pw.replay(pw.simulate(level, 10**7 + s), 1 << k) for s in range(5)) / 5 for k in range(6))
    authored = [S.node(k)["attrs"].get("name") for k in S.nodes("PredictorCandidate")
                if S.node(k)["attrs"].get("authored") == 1][n_auth0:]
    return {"seed_base": seed_base, "arm": arm, "level": level, "trained_through": trained_through,
            "mastered": mastered_at is not None, "episodes_to_master": mastered_at, "episodes": len(surprises),
            "experiments": exps, "residual_fits": fits, "authored": authored, "final_model": p.get("model"),
            "final_surprise": round(final, 4), "best_base_model_surprise": round(best_base, 4),
            "surprise_curve": surprises, "elapsed_s": round(time.time() - t0, 1)}


def main():
    draw_hash = sys.argv[1]
    seed_bases = [int(x) for x in sys.argv[2:]] or [1000, 2024, 5000, 9000]
    from domains import prediction_world as pw
    levels = pw.heldout_levels(int(draw_hash[:8], 16), K_LEVELS)
    jobs = [(sb, arm, lv, spec) for sb in seed_bases for arm in ARMS for lv, spec in levels.items()]
    with ProcessPoolExecutor(max_workers=int(os.environ.get("PW_WORKERS", "4"))) as ex:
        rows = list(ex.map(job, jobs))
    summary = {}
    for arm in ARMS:
        r = [x for x in rows if x["arm"] == arm]
        m = [x for x in r if x["mastered"]]
        summary[arm] = {"mastered": len(m), "of": len(r),
                        "mean_episodes_to_master": round(sum(x["episodes_to_master"] for x in m) / len(m), 2) if m else None,
                        "mean_experiments": round(sum(x["experiments"] for x in r) / len(r), 2),
                        "mean_final_surprise": round(sum(x["final_surprise"] for x in r) / len(r), 4)}
    # the paired falling-cost comparison: levels both on arms mastered, same seed base
    pairs = []
    for x in rows:
        if x["arm"] == "on_trained" and x["mastered"]:
            y = next(z for z in rows if z["arm"] == "on_naive" and z["level"] == x["level"]
                     and z["seed_base"] == x["seed_base"])
            if y["mastered"]:
                pairs.append((x["episodes_to_master"], y["episodes_to_master"], x["experiments"], y["experiments"]))
    summary["paired_trained_vs_naive"] = {
        "n": len(pairs),
        "trained_fewer_episodes": sum(1 for a, b, _, _ in pairs if a < b),
        "naive_fewer_episodes": sum(1 for a, b, _, _ in pairs if b < a),
        "ties": sum(1 for a, b, _, _ in pairs if a == b),
        "mean_episodes_trained": round(sum(p[0] for p in pairs) / len(pairs), 2) if pairs else None,
        "mean_episodes_naive": round(sum(p[1] for p in pairs) / len(pairs), 2) if pairs else None,
        "mean_experiments_trained": round(sum(p[2] for p in pairs) / len(pairs), 2) if pairs else None,
        "mean_experiments_naive": round(sum(p[3] for p in pairs) / len(pairs), 2) if pairs else None}
    rep = {"draw_hash": draw_hash, "levels": levels, "seed_bases": seed_bases, "budget": BUDGET,
           "summary": summary, "rows": rows}
    loop_version = json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())["version"]
    rep["loop_version"] = loop_version
    out = ROOT / f"evaluation/reports/prediction_world_heldout_v1_{draw_hash[:8]}_loop{loop_version}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(levels, indent=1))
    print(json.dumps(summary, indent=1))
    for lv in levels:
        print(lv, " ".join(f"{arm}:{sum(x['mastered'] for x in rows if x['arm'] == arm and x['level'] == lv)}"
                           f"/{len(seed_bases)}" for arm in ARMS))


if __name__ == "__main__":
    main()
