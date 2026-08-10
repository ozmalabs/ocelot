"""arc_ls20_flash_live — RUNG 223000 LIVE half: run the FLASH-ONSET-GUIDED model
on REAL ARC-AGI-3 ls20 frames (bounded n). The HONEST test of the owner's claim
on real data: does flash-onset attention separate the moving avatar from static
structure / mark the consume event and IMPROVE the live change-set F1 over
222000's blind live NULL (0.0)?

The SAME graph-native machinery: the REAL GraphEye 2-D onset stream runs on the
real frame transitions (mapped to luminance); the fg_pick_flash rule attends the
brightest onset (the flash); the windowed region feeds the IDENTICAL 222000
sd-loop. The change-set F1 of the flash-guided per-cell prediction is compared to
the PERSISTENCE null and to the 222000 blind arm on the SAME real frames.

HONEST SCOPE. If the flash-guided model does NOT beat blind/persistence in the
budget, the null is reported STRAIGHT + WHAT the flash DID localise (the onset
firing pattern on real contacts) -- partial progress is a real result, never a
hidden failure. Bounded n (== API calls). NEVER prints/commits the key. If the API
is unreachable / rejected / rate-limited, STOP and report -- NEVER fabricate.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_flash_live.py \
        --game ls20-9607627b --steps 50
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
from worlds.arc_ls20_flash import (  # noqa: E402
    OnsetEye, FlashAgent, discover_flash_separate, discover_blind, luma,
)
from worlds.arc_ls20_percell import score_prediction, ACTIONS as AGENT_ACTIONS  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402

MAX_OBJ = 120


def _stat(xs):
    xs = np.asarray(xs, dtype=float)
    return {"n": int(xs.size), "mean": (float(xs.mean()) if xs.size else None),
            "first_half_mean": (float(xs[:len(xs) // 2].mean()) if xs.size >= 2 else None),
            "second_half_mean": (float(xs[len(xs) // 2:].mean()) if xs.size >= 2 else None)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--steps", type=int, default=50, help="live steps (== API calls)")
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

    print(f"=== RUNG 223000 LIVE — FLASH-ONSET-GUIDED model on REAL ls20 ({args.game}) ===")
    grid = f.grid
    prev = np.asarray(grid, dtype=np.int32)
    H, W = prev.shape
    print(f"RESET ok: state={f.state.value} levels_completed={f.score} "
          f"grid={H}x{W} available={env.available_actions}")

    # the onset eye on the REAL frame grid (mapped to luminance). n = max(H, W)
    # (square retina). The flash on real avatar<->shape contact is a bright
    # transient the general onset stream detects.
    eye_n = max(H, W)
    eye = OnsetEye(eye_n)
    # pad helper: the eye is square; embed the (H,W) grid at the top-left.
    def _square(g):
        s = np.zeros((eye_n, eye_n), dtype=np.int32)
        s[:g.shape[0], :g.shape[1]] = g
        return s
    eye.adapt(_square(prev), frames=10)

    agent = FlashAgent(arm="flash_separate")
    blind = FlashAgent(arm="blind")
    real_to_agent = {}
    roundtrip_ok = True
    flash_f1, blind_f1, persist_f1 = [], [], []
    learned_first = 0
    onset_frames = 0
    onset_fired = 0
    onset_localisations = []   # centroid of the attended flash per step (diag)
    i = 0
    for step in range(args.steps):
        rec = recover_grid_from_render(_render_screen(prev.tolist(), H, W))
        if not np.array_equal(np.asarray(rec), prev):
            roundtrip_ok = False
        avail = list(env.available_actions) or []
        if not avail:
            break
        real_act = avail[i % len(avail)]; i += 1
        if real_act not in real_to_agent:
            real_to_agent[real_act] = AGENT_ACTIONS[len(real_to_agent) % len(AGENT_ACTIONS)]
        aname = real_to_agent[real_act]

        had_prior = agent.hypothesis(aname) is not None
        pred_flash = agent.predict_next(prev, aname)
        pred_blind = blind.predict_next(prev, aname)

        try:
            f = env.step(real_act)
        except Exception as e:
            print(f"LIVE step failed — STOP (no fabricated number): {e}")
            break
        cur = np.asarray(f.grid, dtype=np.int32)

        # ---- the flash onset on the REAL transition (general onset stream) ----
        events = eye.onset_on_transition(_square(prev), _square(cur), flash_cells=None)
        onset_frames += 1
        if events:
            onset_fired += 1
            events.sort(key=lambda e: -e[2])
            onset_localisations.append((events[0][0], events[0][1], round(events[0][2], 1)))
        centre = agent.attend_flash(events)

        if had_prior:
            flash_f1.append(score_prediction(prev, cur, pred_flash)["f1_strict"])
            blind_f1.append(score_prediction(prev, cur, pred_blind)["f1_strict"])
            persist_f1.append(score_prediction(prev, cur, prev.copy())["f1_strict"])
        else:
            learned_first += 1

        # UPDATE both models on the SAME real transition.
        agent.observe(aname, prev, cur, centre)
        blind.observe(aname, prev, cur, None)

        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    eye.stop()
    sc = env.close_scorecard()
    fstat, bstat, pstat = _stat(flash_f1), _stat(blind_f1), _stat(persist_f1)
    flash_beats_blind = (fstat["mean"] is not None and bstat["mean"] is not None
                         and fstat["mean"] > bstat["mean"])
    flash_beats_persist = (fstat["mean"] is not None and pstat["mean"] is not None
                           and fstat["mean"] > pstat["mean"])

    result = {
        "rung": 223000, "tag": args.tag, "game": args.game,
        "commitment": "flash-onset-guided per-cell model on REAL ls20; change-set "
                      "F1 vs the 222000 blind arm AND the persistence null, honest, "
                      "bounded n. If it does not beat them, the null is reported "
                      "STRAIGHT + what the flash localised.",
        "n_live_steps": step + 1, "final_state": f.state.value,
        "levels_completed_SIDE_EFFECT": f.score,
        "perception_roundtrip_ok_on_live": roundtrip_ok,
        "n_repeat_obs_scored": len(flash_f1),
        "n_first_obs_no_prior": learned_first,
        "flash_guided_changeset_f1": fstat,
        "blind_changeset_f1": bstat,
        "persistence_changeset_f1": pstat,
        "flash_beats_blind": flash_beats_blind,
        "flash_beats_persistence": flash_beats_persist,
        "onset_stream_on_real_frames": {
            "n_frames": onset_frames,
            "n_frames_with_onset": onset_fired,
            "onset_fire_rate": (onset_fired / onset_frames if onset_frames else None),
            "sample_argmax_onset_localisations_row_col_db": onset_localisations[:20],
            "note": "WHAT the flash localised on real frames: the general onset "
                    "stream fires on transient brightenings in the real ls20 video; "
                    "these are the candidate flash/contact events the attention "
                    "routes to. Reported straight whether or not the per-cell model "
                    "converged.",
        },
        "scorecard_closed": bool(sc),
        "honest_scope": "bounded n; the OFFLINE powered sample-efficiency teeth are "
                        "the deliverable. Real ls20 dynamics may still not be a clean "
                        "single-object transform even with flash attention; the "
                        "number here is what the live budget actually produced.",
    }
    out = _ROOT / "results" / f"arc_ls20_flash_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    print(f"\nlive steps={result['n_live_steps']} final_state={result['final_state']} "
          f"levels_completed(SIDE EFFECT)={result['levels_completed_SIDE_EFFECT']}")
    print(f"perception roundtrip on live frames: {roundtrip_ok}")
    print(f"repeat-obs scored={len(flash_f1)} first-obs(no prior)={learned_first}")
    print(f"onset stream fired on {onset_fired}/{onset_frames} real frames")
    print(f"FLASH-guided change-set F1: mean={fstat['mean']}")
    print(f"BLIND (222000) change-set F1: mean={bstat['mean']}")
    print(f"PERSISTENCE change-set F1: mean={pstat['mean']}")
    print(f"flash beats blind: {flash_beats_blind}  flash beats persistence: {flash_beats_persist}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
