"""arc_ls20_consume_live — RUNG 225000 LIVE half: does folding the flash consume-
marking onto the 224000 tracker close part of the real ~0.036 trail residual?

224000's tracker gets live change-set strict-F1 0.9639 on real ls20; the honest
~0.036 gap is the trail/consume residual. This runs BOTH arms on the SAME real
frames: 224-alone (translate) and flash-folded (translate + flash-localised consume
marking). The flash onset is the general GraphEye 2-D onset stream on the real
transition (223's machinery); the consumed VALUE is discovered ORACLE-FREE (the
vacated cells that did not revert to the field). The flash-folded change-set F1 is
compared to 224-alone on the SAME frames.

HONEST SCOPE. If the flash-folded model does NOT beat 224-alone in the budget, the
NULL is reported STRAIGHT + WHAT the flash localised (the real onset firing
pattern). Bounded n (== API calls). NEVER prints/commits the key. If the API is
unreachable / rejected / rate-limited, STOP and report -- NEVER fabricate.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_consume_live.py \
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
from worlds.arc_ls20_percell import score_prediction, ACTIONS  # noqa: E402
from worlds.arc_ls20_consume import ConsumeTracker, OnsetEye  # noqa: E402
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
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--n-field", type=int, default=2)
    ap.add_argument("--cap", type=int, default=150)
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

    print(f"=== RUNG 225000 LIVE — FLASH-CONSUME FOLD on REAL ls20 ({args.game}) ===")
    prev = np.asarray(f.grid, dtype=np.int32)
    H, W = prev.shape
    print(f"RESET ok: state={f.state.value} levels={f.score} grid={H}x{W} "
          f"available={env.available_actions} steps={args.steps}")

    eye_n = max(H, W)
    eye = OnsetEye(eye_n)

    def _square(g):
        s = np.zeros((eye_n, eye_n), dtype=np.int32)
        s[:g.shape[0], :g.shape[1]] = g
        return s
    eye.adapt(_square(prev), frames=10)

    trk_t = ConsumeTracker(mode="translate", cap=args.cap, n_field=args.n_field)
    trk_f = ConsumeTracker(mode="flash", cap=args.cap, n_field=args.n_field)
    real_to_agent = {}
    roundtrip_ok = True
    transl_f1, flash_f1, persist_f1 = [], [], []
    no_prior = 0
    onset_frames = onset_fired = 0
    onset_localisations = []
    i = 0
    step = 0
    for step in range(args.steps):
        rec = recover_grid_from_render(_render_screen(prev.tolist(), H, W))
        if not np.array_equal(np.asarray(rec), prev):
            roundtrip_ok = False
        avail = list(env.available_actions) or []
        if not avail:
            break
        real_act = avail[i % len(avail)]; i += 1
        if real_act not in real_to_agent:
            real_to_agent[real_act] = ACTIONS[len(real_to_agent) % len(ACTIONS)]
        aname = real_to_agent[real_act]

        had = (trk_f.pc.hypothesis(aname) is not None) and (trk_f.trk.obj is not None)
        pred_t = trk_t.predict(prev, aname, [])            # 224-alone (translate)
        try:
            f = env.step(real_act)
        except Exception as e:
            print(f"LIVE step failed — STOP (no fabricated number): {e}")
            break
        cur = np.asarray(f.grid, dtype=np.int32)

        # the flash onset on the REAL transition (general onset stream), then fold.
        events = eye.onset_on_transition(_square(prev), _square(cur), flash_cells=None)
        onset_frames += 1
        if events:
            onset_fired += 1
            ev = sorted(events, key=lambda e: -e[2])[0]
            onset_localisations.append((int(ev[0]), int(ev[1]), round(ev[2], 1)))
        pred_f = trk_f.predict(prev, aname, events)         # flash-folded

        if had:
            transl_f1.append(score_prediction(prev, cur, pred_t)["f1_strict"])
            flash_f1.append(score_prediction(prev, cur, pred_f)["f1_strict"])
            persist_f1.append(score_prediction(prev, cur, prev.copy())["f1_strict"])
        else:
            no_prior += 1

        trk_t.observe(prev, cur, aname)
        trk_f.observe(prev, cur, aname)
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    eye.stop()
    sc = env.close_scorecard()
    tstat, fstat, pstat = _stat(transl_f1), _stat(flash_f1), _stat(persist_f1)
    flash_beats_translate = (fstat["mean"] is not None and tstat["mean"] is not None
                             and fstat["mean"] > tstat["mean"])

    result = {
        "rung": 225000, "tag": args.tag, "game": args.game,
        "commitment": "flash-consume fold on REAL ls20; change-set strict-F1 vs "
                      "224-alone (translate) on the SAME frames. If it does not beat "
                      "224-alone the NULL is reported STRAIGHT + what the flash "
                      "localised. The consumed value is discovered ORACLE-FREE.",
        "steps_budget": args.steps, "n_live_steps": step + 1,
        "n_field": args.n_field, "cap": args.cap,
        "final_state": f.state.value, "levels_completed_SIDE_EFFECT": f.score,
        "perception_roundtrip_ok_on_live": roundtrip_ok,
        "n_scored": len(transl_f1), "n_no_prior_or_untracked": no_prior,
        "translate_224_alone_changeset_f1": tstat,
        "flash_folded_changeset_f1": fstat,
        "persistence_changeset_f1": pstat,
        "flash_folded_beats_224_alone": flash_beats_translate,
        "onset_stream_on_real_frames": {
            "n_frames": onset_frames, "n_frames_with_onset": onset_fired,
            "onset_fire_rate": (onset_fired / onset_frames if onset_frames else None),
            "sample_argmax_onset_localisations_row_col_db": onset_localisations[:20],
            "note": "WHAT the flash localised on real frames -- reported straight "
                    "whether or not the fold closed the residual.",
        },
        "scorecard_closed": bool(sc),
        "honest_scope": "bounded n; the OFFLINE powered ablation is the gated "
                        "deliverable. The number here is what the live budget produced.",
    }
    out = _ROOT / "results" / f"arc_ls20_consume_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    print(f"\nlive steps={step + 1} final={f.state.value} roundtrip={roundtrip_ok}")
    print(f"scored={len(transl_f1)} no_prior/untracked={no_prior}")
    print(f"onset stream fired on {onset_fired}/{onset_frames} real frames")
    print(f"224-ALONE (translate) change-set F1: mean={tstat['mean']}")
    print(f"FLASH-FOLDED change-set F1: mean={fstat['mean']}")
    print(f"PERSISTENCE change-set F1: mean={pstat['mean']}")
    print(f"flash-folded BEATS 224-alone: {flash_beats_translate}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
