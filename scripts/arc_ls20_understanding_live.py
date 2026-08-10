"""arc_ls20_understanding_live — RUNG 221000 LIVE half: run the understanding
loop's PERCEPTION + next-effect RESIDUAL on REAL live ls20 frames (bounded n).

HONEST SCOPE. The offline measure is the deliverable (the station->transform
mechanic, learned by curiosity + predict-and-residual, gated + powered). This live
half is the real-world confirmation that the SAME machinery RUNS on real content:

  · PERCEPTION survives — each real symbolic frame round-trips through the 216000
    pixel eye (_render_screen -> recover_grid_from_render), replicating 219000.
  · NEXT-EFFECT RESIDUAL (surprise) — the general predict-and-residual: the agent
    HOLDS the current frame as its order-0 prediction of the next, acts, and the
    RESIDUAL (fraction of cells that changed) is the surprise. A per-ACTION effect
    model is minted (mean changed-cell fraction per action id) — the live twin of
    the offline station->transform hypotheses — and its per-action prediction
    residual (|observed change - modelled mean change|) is tracked to show whether
    the action-effect surprise DROPS as each action is re-observed.
  · WIN AS A SIDE EFFECT — `levels_completed` is LOGGED downstream; never optimised.

Bounded n (== API calls). NEVER prints/commits the key. If the API is unreachable
/ rejected / rate-limited, STOP and report -- NEVER fabricate a number.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_understanding_live.py \
        --game ls20-9607627b --steps 40
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT / "scripts"), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc import _render_screen, recover_grid_from_render  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402


def _changed_fraction(a, b):
    a = np.asarray(a, dtype=np.int32); b = np.asarray(b, dtype=np.int32)
    if a.shape != b.shape:
        return 1.0
    return float((a != b).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--steps", type=int, default=40, help="live steps (== API calls)")
    ap.add_argument("--tag", default="live")
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

    print(f"=== RUNG 221000 LIVE — understanding machinery on REAL ls20 ({args.game}) ===")
    grid = f.grid
    print(f"RESET ok: state={f.state.value} levels_completed={f.score} "
          f"grid={len(grid)}x{len(grid[0])} available={env.available_actions}")

    # per-action effect model: mean changed-cell fraction (the live 'hypothesis').
    act_mean = {}        # action -> running mean changed fraction
    act_count = {}       # action -> times observed
    held_residual = []   # order-0 (held-frame) surprise per step
    act_pred_resid = []  # per-action prediction residual (|obs - modelled mean|)
    surprise_first = []  # 1 if this action was NEVER seen before (novelty), else 0
    roundtrip_ok = True
    prev = grid
    i = 0
    for step in range(args.steps):
        # perception survival: round-trip the real frame through the pixel eye.
        h = len(prev); w = len(prev[0]) if h else 0
        rec = recover_grid_from_render(_render_screen(prev, h, w))
        if not np.array_equal(np.asarray(rec), np.asarray(prev)):
            roundtrip_ok = False
        avail = list(env.available_actions) or []
        if not avail:
            break
        act = avail[i % len(avail)]; i += 1
        try:
            f = env.step(act)
        except Exception as e:
            print(f"LIVE step failed — STOP (no fabricated number): {e}")
            break
        cur = f.grid
        obs_change = _changed_fraction(prev, cur)
        held_residual.append(obs_change)               # order-0 held-prediction surprise
        # per-action predict-and-residual (the live hypothesis test).
        if act in act_mean:
            act_pred_resid.append(abs(obs_change - act_mean[act]))
            surprise_first.append(0.0)
            n = act_count[act] + 1
            act_mean[act] += (obs_change - act_mean[act]) / n
            act_count[act] = n
        else:
            surprise_first.append(1.0)                 # first observation -> mint
            act_mean[act] = obs_change; act_count[act] = 1
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    sc = env.close_scorecard()

    def stat(xs):
        xs = np.asarray(xs, dtype=float)
        return {"n": int(xs.size), "mean": (float(xs.mean()) if xs.size else None),
                "first_half_mean": (float(xs[:len(xs)//2].mean()) if xs.size >= 2 else None),
                "second_half_mean": (float(xs[len(xs)//2:].mean()) if xs.size >= 2 else None)}

    result = {
        "rung": 221000, "tag": args.tag, "game": args.game,
        "commitment": "the understanding machinery's perception + predict-and-residual "
                      "surprise RUN on REAL live ls20; winning is logged, never optimised.",
        "n_live_steps": len(held_residual),
        "final_state": f.state.value, "levels_completed_SIDE_EFFECT": f.score,
        "perception_roundtrip_ok_on_live": roundtrip_ok,
        "held_prediction_surprise": stat(held_residual),
        "per_action_effect_model": {str(a): {"mean_changed_fraction": act_mean[a],
                                             "count": act_count[a]} for a in act_mean},
        "per_action_prediction_residual": stat(act_pred_resid),
        "action_novelty_first_obs": stat(surprise_first),
        "scorecard_closed": bool(sc),
        "honest_scope": "bounded n; the OFFLINE station->transform understanding is the "
                        "deliverable. This confirms perception survives + the surprise "
                        "signal is real on live content. The full live mechanic is NOT "
                        "claimed learned in bounded n.",
    }
    out = _ROOT / "results" / f"arc_ls20_understanding_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    print(f"\nlive steps={result['n_live_steps']} final_state={result['final_state']} "
          f"levels_completed(SIDE EFFECT)={result['levels_completed_SIDE_EFFECT']}")
    print(f"perception roundtrip on live frames: {roundtrip_ok}")
    hr = result["held_prediction_surprise"]
    print(f"held-prediction surprise (changed-cell fraction): mean={hr['mean']} "
          f"first_half={hr['first_half_mean']} second_half={hr['second_half_mean']}")
    pr = result["per_action_prediction_residual"]
    print(f"per-action prediction residual: mean={pr['mean']} "
          f"first_half={pr['first_half_mean']} second_half={pr['second_half_mean']} "
          f"(drop = the action-effect model tightening)")
    print("per-action effect model (mean changed fraction | count):")
    for a in act_mean:
        print(f"    {a}: {act_mean[a]:.4f} | {act_count[a]}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
