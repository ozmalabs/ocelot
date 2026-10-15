#!/usr/bin/env python3
"""Endemic self-improvement in the prediction world (2026-10-10).

One agent holding the prediction world and its self-improvement loop
(seeds/prediction_world.json, seeds/prediction_self_improvement.json) lives
through N episodes. Each episode is played at whatever level its curriculum
says (domains/prediction_world.run_episode, a fresh seed every episode, so
every live episode is unseen); after each, any Experiment the loop requested
is replayed (run_experiments). Nothing else is scripted: concerns, trials,
verdicts, adoptions and level advances are the graph's.

Arms (same episode seeds):
  on   PredictionPolicy.self_improvement = 1
  off  self_improvement = 0 -- the agent still notices its surprise and files
       concerns, but may not change itself

Reports, per arm: the per-episode level and surprise, the levels mastered,
concerns, experiments (candidate, control, variant, retention, verdict),
adoptions, and the final model's surprise on fresh episodes of every level.

Usage: <this> [episodes=60] [seed_base=1000]
Writes evaluation/reports/prediction_world_rsi_v1_n<N>_s<seed_base>_20261010.json.
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]


def arm(n, self_improvement, seed_base=1000):
    from substrate.world_adapter import WorldAdapter
    from domains import prediction_world as pw
    a = WorldAdapter(seeds=("prediction_world", "prediction_self_improvement"))
    S = a.s
    pol = S.nodes("PredictionPolicy")[0]
    a.inner.set_attr(pol, "self_improvement", int(self_improvement))
    curve, trials = [], []
    t0 = time.time()
    for i in range(n):
        ep = pw.run_episode(a, seed=seed_base + i)
        trials += [dict(r, episode=i) for r in pw.run_experiments(a)]
        p = S.node(S.nodes("Predictor")[0])["attrs"]
        curve.append({**ep, "model": p["model"],
                      "level_after": S.node(S.nodes("PredictionCurriculum")[0])["attrs"]["current_level"]})
    cur = S.node(S.nodes("PredictionCurriculum")[0])["attrs"]
    p = S.node(S.nodes("Predictor")[0])["attrs"]
    concerns = [{k: S.node(c)["attrs"].get(k) for k in ("level", "status", "filed_change_seq")}
                for c in S.nodes("SelfConcern") if S.node(c)["attrs"].get("kind") == "prediction_surprise"]
    exps = []
    for x in S.nodes("Experiment"):
        at = S.node(x)["attrs"]
        d = S.node(list(a.inner.neighbours(x, "has_delta"))[0])["attrs"]
        exps.append({"level": at.get("level"), "candidate": d["candidate_name"], "control_model": d["control_name"],
                     **{k: at.get(k) for k in ("control_surprise", "variant_surprise", "retention_harm",
                                               "retention_by_level", "weighed_net", "outcome", "adopted")}})
    adoptions = [{k: S.node(x)["attrs"].get(k) for k in ("level", "from_model", "to_model")}
                 for x in S.nodes("Adoption")]
    authored = [{k: S.node(x)["attrs"].get(k) for k in ("name", "mask", "rank", "authored_level")}
                for x in S.nodes("PredictorCandidate") if S.node(x)["attrs"].get("authored") == 1]
    final = {lv: round(sum(pw.replay(pw.simulate(lv, 10**6 + s), p["mask"]) for s in range(5)) / 5, 4)
             for lv in pw.LEVELS}
    return {"self_improvement": self_improvement, "episodes": n, "elapsed_s": round(time.time() - t0, 1),
            "final_level": cur["current_level"], "mastered_through": cur.get("mastered_through"),
            "final_model": p["model"], "authored_candidates": authored, "concerns": concerns, "experiments": exps,
            "adoptions": adoptions, "final_model_surprise_by_level": final, "curve": curve}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    seed_base = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    rep = {"seed_base": seed_base, "arms": {"on": arm(n, 1, seed_base), "off": arm(n, 0, seed_base)}}
    out = ROOT / f"evaluation/reports/prediction_world_rsi_v1_n{n}_s{seed_base}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    for name, r in rep["arms"].items():
        print(f"\n== {name}: final level {r['final_level']}, mastered through {r['mastered_through']}, "
              f"model {r['final_model']}, {len(r['experiments'])} experiments, {len(r['adoptions'])} adoptions, {len(r['authored_candidates'])} authored, "
              f"{r['elapsed_s']}s")
        print("   concerns", r["concerns"])
        print("   authored", r["authored_candidates"])
        for x in r["experiments"]:
            print("   exp", x["level"], x["control_model"], "->", x["candidate"], "ctl", x["control_surprise"],
                  "var", x["variant_surprise"], "ret_harm", x["retention_harm"],
                  "net", x["weighed_net"], x["outcome"], "adopted" if x["adopted"] else "")
        print("   final model surprise by level", r["final_model_surprise_by_level"])
        line = " ".join(f"{c['level']}:{c['mean_surprise']:.2f}" for c in r["curve"])
        print("   curve", line)


if __name__ == "__main__":
    main()
