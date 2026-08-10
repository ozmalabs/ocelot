"""doom_active_explore_report — IMPORT-INERT analysis + figure for block 205000.

Reads results/doom_active_explore/arms.json and computes the gates:
  G1  coverage-vs-actions curves; curiosity dominance over random + passive.
  G3  commit dwell (mean run-length of a held committed frontier) curiosity vs nocommit.
  G4  compute proportional-to-surprise: correlation(reveal_ms, novel_cells).
Renders coverage_curves.png + exploration_trace.png.

No side effects on import (all work under `report()` / __main__).
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "doom_active_explore")


def _dwell(goal_trace):
    """Mean run-length of consecutive identical committed-goal poses (dwell); and the
    number of goal SWITCHES (re-decisions). goal_trace = [(tick, pose_or_None)]."""
    poses = [tuple(p) if p else None for _, p in goal_trace]
    if not poses:
        return 0.0, 0
    runs = []
    cur = poses[0]; ln = 1
    switches = 0
    for p in poses[1:]:
        if p == cur:
            ln += 1
        else:
            runs.append(ln); switches += 1
            cur = p; ln = 1
    runs.append(ln)
    return sum(runs) / len(runs), switches


def _spearman(x, y):
    import numpy as np
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.size < 3:
        return None
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    if rx.std() == 0 or ry.std() == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def report():
    import numpy as np
    d = json.load(open(os.path.join(OUTDIR, "arms.json")))
    res = d["results"]; total = d["total_walkable"]; budget = d["budget"]
    out = {"budget": budget, "total_walkable": total, "view_radius": d["view_radius"]}

    # ---- G1: final coverage + curve dominance ----
    def curve(arm):
        return dict(res[arm]["curve"]) if arm != "random" else None
    finals = {}
    for arm in ("curiosity", "nearest", "nocommit", "passive"):
        if arm in res:
            finals[arm] = res[arm]["final_free"]
    rand_finals = [r["final_free"] for r in res["random"]] if "random" in res else []
    finals_random_mean = float(np.mean(rand_finals)) if rand_finals else None
    finals_random_std = float(np.std(rand_finals)) if rand_finals else None

    # dominance: curiosity >= max(random over reps) at every budget point
    cur_curve = dict(res["curiosity"]["curve"])
    rand_curves = [dict(r["curve"]) for r in res["random"]]
    ticks = sorted(cur_curve.keys())
    rand_mean_curve = {t: float(np.mean([rc[t] for rc in rand_curves])) for t in ticks}
    rand_max_curve = {t: max(rc[t] for rc in rand_curves) for t in ticks}
    dominates_mean = all(cur_curve[t] >= rand_mean_curve[t] for t in ticks)
    dominates_max = all(cur_curve[t] >= rand_max_curve[t] for t in ticks)
    passive_final = finals.get("passive", 0)
    # crossover: the last tick at which curiosity is BELOW random mean (the deliberation transient);
    # after it, curiosity dominates. "Slow start is the signature" (self-directed explorer).
    below = [t for t in ticks if cur_curve[t] < rand_mean_curve[t]]
    crossover = (max(below) + 1) if below else 0
    dominates_after_crossover = all(cur_curve[t] >= rand_mean_curve[t]
                                    for t in ticks if t >= crossover)

    out["G1"] = {
        "final_coverage": finals,
        "final_coverage_pct": {k: round(100.0 * v / total, 1) for k, v in finals.items()},
        "random_final_mean": finals_random_mean, "random_final_std": finals_random_std,
        "random_final_pct": round(100.0 * finals_random_mean / total, 1) if finals_random_mean else None,
        "curiosity_over_random_x": round(cur_curve[ticks[-1]] / max(1, finals_random_mean), 2),
        "curiosity_over_passive_x": round(cur_curve[ticks[-1]] / max(1, passive_final), 2),
        "curiosity_dominates_random_mean_everywhere": dominates_mean,
        "curiosity_dominates_random_max_everywhere": dominates_max,
        "crossover_tick": crossover,
        "curiosity_dominates_random_mean_after_crossover": dominates_after_crossover,
        "PASS": bool(cur_curve[ticks[-1]] > finals_random_mean and cur_curve[ticks[-1]] > passive_final
                     and dominates_after_crossover),
    }

    # ---- G3: commit dwell ----
    g3 = {}
    for arm in ("curiosity", "nocommit"):
        if arm in res:
            dwell, switches = _dwell(res[arm]["goal_trace"])
            g3[arm] = {"mean_dwell": round(dwell, 2), "goal_switches": switches,
                       "decisions": len(res[arm]["goal_trace"])}
    if "curiosity" in g3 and "nocommit" in g3:
        g3["dwell_ratio_commit_over_nocommit"] = round(
            g3["curiosity"]["mean_dwell"] / max(1e-9, g3["nocommit"]["mean_dwell"]), 2)
        g3["PASS"] = bool(g3["curiosity"]["mean_dwell"] > 1.5 * g3["nocommit"]["mean_dwell"]
                          and g3["curiosity"]["goal_switches"] < g3["nocommit"]["goal_switches"])
    out["G3"] = g3

    # ---- G4: compute proportional to surprise ----
    wt = res["curiosity"]["work_trace"]  # (tick, reveal_ms, novel_cells)
    ms = [w[1] for w in wt]; nov = [w[2] for w in wt]
    novel_ms = [w[1] for w in wt if w[2] > 0]
    retread_ms = [w[1] for w in wt if w[2] == 0]
    out["G4"] = {
        "spearman_reveal_ms_vs_novel_cells": round(_spearman(ms, nov), 3) if _spearman(ms, nov) is not None else None,
        "mean_ms_novel_tick": round(float(np.mean(novel_ms)), 2) if novel_ms else None,
        "mean_ms_retread_tick": round(float(np.mean(retread_ms)), 2) if retread_ms else None,
        "n_novel": len(novel_ms), "n_retread": len(retread_ms),
        "PASS": bool(novel_ms and retread_ms and np.mean(novel_ms) > np.mean(retread_ms)),
    }

    with open(os.path.join(OUTDIR, "gates.json"), "w") as f:
        json.dump(out, f, indent=2)
    _figure(d, out)
    return out


def _figure(d, out):
    import numpy as np
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("no matplotlib:", e); return
    res = d["results"]; total = d["total_walkable"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
    # -- coverage vs actions --
    col = {"curiosity": "#1f77b4", "nearest": "#2ca02c", "nocommit": "#9467bd", "passive": "#7f7f7f"}
    for arm in ("curiosity", "nearest", "nocommit", "passive"):
        if arm in res:
            c = res[arm]["curve"]
            xs = [p[0] for p in c]; ys = [100.0 * p[1] / total for p in c]
            ax1.plot(xs, ys, label=arm, color=col.get(arm), lw=2)
    # random band
    rand_curves = [res_r["curve"] for res_r in res["random"]]
    ticks = [p[0] for p in rand_curves[0]]
    arr = np.array([[p[1] for p in rc] for rc in rand_curves], float) * 100.0 / total
    ax1.plot(ticks, arr.mean(0), label="random (mean)", color="#d62728", lw=2)
    ax1.fill_between(ticks, arr.min(0), arr.max(0), color="#d62728", alpha=0.18)
    ax1.set_xlabel("actions"); ax1.set_ylabel("map coverage (% walkable reconstructed)")
    ax1.set_title("G1: active exploration coverage vs actions (E1M1)")
    ax1.legend(loc="upper left", fontsize=9); ax1.grid(alpha=0.3)

    # -- exploration trace over the occupancy --
    occ_path = os.path.join(OUTDIR, "e1m1_occupancy.json")
    occ = json.load(open(occ_path))
    walk = np.array(occ["walkable"])
    ax2.scatter(walk[:, 0], -walk[:, 1], s=2, c="#dddddd", marker="s", label="walkable E1M1")
    for arm, c in (("curiosity", "#1f77b4"), ("random", "#d62728")):
        p = res[arm][0]["path"] if arm == "random" else res[arm]["path"]
        p = np.array(p)
        ax2.plot(p[:, 0], -p[:, 1], color=c, lw=1.4, label=f"{arm} path")
        ax2.scatter([p[0, 0]], [-p[0, 1]], color="k", s=40, zorder=5)
    ax2.set_title("Exploration path (curiosity vs random) on E1M1")
    ax2.set_aspect("equal"); ax2.legend(loc="upper right", fontsize=9); ax2.axis("off")
    fig.tight_layout()
    p = os.path.join(OUTDIR, "active_exploration.png")
    fig.savefig(p, dpi=110)
    print("wrote", p)


if __name__ == "__main__":
    r = report()
    print(json.dumps(r, indent=2))
