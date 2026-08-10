"""arc_ls20_percell_live_tracked — RUNG 222000 continuation (LARGER BUDGET): the
GENERAL object-tracking per-cell model on REAL ls20.

The base 222000 live half returned the pre-registered NULL because its whole-frame-
colour region selector cannot isolate the real ls20 avatar (nested fields + multi-
colour avatar + trail). This adds OBJECT PERMANENCE (worlds/arc_ls20_percell_track
.LiveObjectTracker): the field is the frame's dominant colour(s); the object is the
connected FIGURE blob that moved, tracked across frames; the per-action shift is
learned from the whole-object centroid displacement and STORED IN THE GRAPH;
prediction translates the tracked object -> a per-cell next frame. Validated on
synthetic dense move+trail scenes (strict-F1 1.0 rigid / 0.86 with trail, vs
persistence 0.0) before spending live budget.

HONEST SCOPE. The number reported is the CHANGE-SET F1 of the tracked prediction vs
the PERSISTENCE null on REAL frames, over the steps where the action had a learned
shift AND an object is tracked. If it does not beat persistence, the null is reported
STRAIGHT. NEVER prints/commits the key. API unreachable/rejected/rate-limited ->
STOP, never fabricate.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_percell_live_tracked.py \
        --game ls20-9607627b --steps 300 --n-field 2 --cap 150
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT / "scripts"), str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc import _render_screen, recover_grid_from_render  # noqa: E402
from worlds.arc_ls20_percell import Percell, score_prediction, ACTIONS  # noqa: E402
from worlds.arc_ls20_percell_track import LiveObjectTracker  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402


def _stat(xs):
    xs = np.asarray(xs, dtype=float)
    out = {"n": int(xs.size), "mean": (float(xs.mean()) if xs.size else None),
           "first_half_mean": (float(xs[:len(xs) // 2].mean()) if xs.size >= 2 else None),
           "second_half_mean": (float(xs[len(xs) // 2:].mean()) if xs.size >= 2 else None)}
    if xs.size >= 2:
        rng = np.random.default_rng(0)
        means = xs[rng.integers(0, xs.size, size=(1000, xs.size))].mean(axis=1)
        out["ci95"] = [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--steps", type=int, default=300, help="live steps (== API calls)")
    ap.add_argument("--n-field", type=int, default=2, help="# dominant colours treated as field")
    ap.add_argument("--cap", type=int, default=150, help="max object-blob cells to track")
    ap.add_argument("--tag", default="live_tracked")
    args = ap.parse_args()

    if not load_arc_api_key():
        print("could not load ARC_API_KEY — ABORTING (no number without auth)")
        return 1
    from arc3_live_env import Arc3LiveEnv
    try:
        env = Arc3LiveEnv(args.game)
        f = env.reset()
    except Exception as e:
        print(f"LIVE API UNREACHABLE / REJECTED — STOP (no fabricated number): {e}")
        return 2

    print(f"=== RUNG 222000 (larger budget) — OBJECT-TRACKING per-cell model on REAL ls20 "
          f"({args.game}) ===")
    grid = f.grid
    print(f"RESET ok: state={f.state.value} levels={f.score} grid={len(grid)}x{len(grid[0])} "
          f"available={env.available_actions} steps_budget={args.steps} n_field={args.n_field} cap={args.cap}")

    agent = Percell()
    trk = LiveObjectTracker(agent, cap=args.cap, n_field=args.n_field)
    real_to_agent = {}
    roundtrip_ok = True
    learned_f1, persist_f1, obj_sizes = [], [], []
    no_prior = 0
    prev = np.asarray(grid, dtype=np.int32)
    i = 0
    step = 0
    for step in range(args.steps):
        h0, w0 = prev.shape
        rec = recover_grid_from_render(_render_screen(prev.tolist(), h0, w0))
        if not np.array_equal(np.asarray(rec), prev):
            roundtrip_ok = False
        avail = list(env.available_actions) or []
        if not avail:
            break
        real_act = avail[i % len(avail)]; i += 1
        if real_act not in real_to_agent:
            real_to_agent[real_act] = ACTIONS[len(real_to_agent) % len(ACTIONS)]
        aname = real_to_agent[real_act]

        had_prior = (agent.hypothesis(aname) is not None) and (trk.obj is not None)
        pred = trk.predict(prev, aname)
        try:
            f = env.step(real_act)
        except Exception as e:
            print(f"LIVE step failed — STOP (no fabricated number): {e}")
            break
        cur = np.asarray(f.grid, dtype=np.int32)
        if had_prior:
            learned_f1.append(score_prediction(prev, cur, pred)["f1_strict"])
            persist_f1.append(score_prediction(prev, cur, prev.copy())["f1_strict"])
        else:
            no_prior += 1
        trk.observe(prev, cur, aname)
        if trk.obj is not None:
            obj_sizes.append(len(trk.obj))
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    sc = env.close_scorecard()
    lf, pf = _stat(learned_f1), _stat(persist_f1)
    beats = (lf["mean"] is not None and pf["mean"] is not None and lf["mean"] > pf["mean"])
    shifts = {ra: {"dr": agent.hypothesis(real_to_agent[ra])["dr"],
                   "dc": agent.hypothesis(real_to_agent[ra])["dc"]}
              for ra in real_to_agent if agent.hypothesis(real_to_agent[ra])}

    result = {
        "rung": 222000, "tag": args.tag, "game": args.game,
        "commitment": "GENERAL object-tracking per-cell model (larger budget) on REAL "
                      "ls20; change-set F1 vs persistence, honest. If it does not beat "
                      "persistence the null is reported STRAIGHT.",
        "steps_budget": args.steps, "n_live_steps": step + 1,
        "n_field": args.n_field, "cap": args.cap,
        "final_state": f.state.value, "levels_completed_SIDE_EFFECT": f.score,
        "perception_roundtrip_ok_on_live": roundtrip_ok,
        "n_scored": len(learned_f1), "n_no_prior_or_untracked": no_prior,
        "median_tracked_object_size": (float(np.median(obj_sizes)) if obj_sizes else None),
        "learned_tracked_changeset_f1": lf,
        "persistence_changeset_f1": pf,
        "learned_beats_persistence": beats,
        "discovered_action_shifts": shifts,
        "honest_scope": "the OFFLINE powered teeth (block 222000, on main) are the "
                        "gated deliverable. This continuation adds object-permanence "
                        "tracking and a larger budget to attack the live mechanic "
                        "directly; the number is what the live budget produced.",
    }
    out = _ROOT / "results" / f"arc_ls20_percell_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    print(f"\nlive steps={step + 1} final={f.state.value} levels={f.score} "
          f"roundtrip={roundtrip_ok}")
    print(f"scored={len(learned_f1)} no_prior/untracked={no_prior} "
          f"median_obj_size={result['median_tracked_object_size']}")
    print(f"LEARNED tracked change-set F1: mean={lf['mean']} "
          f"first_half={lf['first_half_mean']} second_half={lf['second_half_mean']}")
    print(f"PERSISTENCE change-set F1: mean={pf['mean']}")
    print(f"learned BEATS persistence: {beats}")
    print(f"discovered per-action shifts (dr,dc): "
          f"{ {k: (v['dr'], v['dc']) for k, v in shifts.items()} }")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
