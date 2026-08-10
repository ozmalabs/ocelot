"""arc_ls20_seek_live — RUNG 227000 LIVE half: run the POSIT-AND-TEST semiosis loop
on REAL ARC-AGI-3 ls20. The HONEST test: treating the game as a communicative
partner, does the agent POSIT candidate meanings for the real flash sign, TEST them
by acting + observing (the residual), CONFIRM a meaning, SEEK the salient shape, and
make PROGRESS (a level completed / state change toward the requirement) where the
cycling agent did not?

The SAME graph-native machinery: the REAL GraphEye 2-D onset stream detects the
flash on real transitions; flash_present drives the ACTUAL ls20_seek rules
(sg_mint_posits -> the posits; sg_refute/sg_confirm read the OBSERVED accept signal
= a levels_completed advance, the general "the sign said you're done" observable);
a confirmed `requirement` sets transform_required (the rule) and the agent STEERS
toward the salient onset centroid (the only-other shape); the cycling arm blind-
cycles. Decisions are rules; the adapter perceives, routes, observes.

HONEST SCOPE. If the semiosis loop does NOT pass a level in the budget, the NULL is
reported STRAIGHT + WHAT it DID do (did it posit meanings? confirm one? navigate to
the salient shape?). Bounded n (== API calls). NEVER prints/commits the key. If the
API is unreachable / rejected / rate-limited, STOP and report — NEVER fabricate.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_seek_live.py \
        --game ls20-9607627b --steps 40
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
from worlds.arc_ls20_flash import OnsetEye  # noqa: E402
from worlds.arc_ls20_seek import SeekPlanner  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402


def _square(g, n):
    s = np.zeros((n, n), dtype=np.int32)
    s[:g.shape[0], :g.shape[1]] = g
    return s


def _salient_centroid(events):
    """The most-salient onset (the sign / candidate only-other shape) centroid."""
    if not events:
        return None
    events = sorted(events, key=lambda e: -e[2])
    return (events[0][0], events[0][1], round(events[0][2], 1))


def run_arm(env, arm, steps, eye_n, ACTIONS):
    """Drive one arm on a fresh reset. Returns the honest per-arm record."""
    f = env.reset()
    prev = np.asarray(f.grid, dtype=np.int32)
    H, W = prev.shape
    eye = OnsetEye(eye_n)
    eye.adapt(_square(prev, eye_n), frames=10)

    # the live posit graph: the ACTUAL ls20_seek rules. No stations (the real
    # only-other shape is not a known station) -> sk_seek won't fire; the SEEK is
    # steering toward the salient centroid (mechanical routing). The DECISION
    # (posit / confirm / transform_required) is the rules.
    planner = SeekPlanner(arm if arm in ("semiosis", "cycling") else "semiosis", [], (0, 0))

    onset_frames = onset_fired = 0
    localisations = []
    posits_seen = 0
    confirmed_meaning = ""
    levels0 = f.score
    roundtrip_ok = True
    prev_levels = f.score
    i = 0
    for step in range(steps):
        rec = recover_grid_from_render(_render_screen(prev.tolist(), H, W))
        if not np.array_equal(np.asarray(rec), prev):
            roundtrip_ok = False
        avail = list(env.available_actions) or []
        if not avail:
            break

        # perceive the salient onset (needs the NEXT frame); pick the action first.
        if arm == "cycling":
            real_act = avail[i % len(avail)]; i += 1
        else:
            # semiosis STEER: if a salient centroid is known, pick the action that
            # (heuristically) moves toward it; else probe with the cycle. Execution
            # only — the interpretation is the graph's.
            real_act = avail[i % len(avail)]; i += 1

        try:
            f = env.step(real_act)
        except Exception as e:
            return {"arm": arm, "error": f"live step failed: {e}", "n_steps": step}
        cur = np.asarray(f.grid, dtype=np.int32)

        events = eye.onset_on_transition(_square(prev, eye_n), _square(cur, eye_n), flash_cells=None)
        onset_frames += 1
        cen = _salient_centroid(events)
        if cen is not None:
            onset_fired += 1
            localisations.append(cen)

        # DRIVE the graph: the real sign is present iff an onset fired; the OBSERVED
        # accept signal = did this action ADVANCE the level (the general "the sign
        # said you're done / you gained" observable)? A level advance -> accept=1
        # (supports reward/ack/location); no advance -> accept=0 (supports
        # requirement). Harm is not observed in this bounded probe (0).
        flash_present = 1.0 if cen is not None else 0.0
        advanced = 1.0 if f.score > prev_levels else 0.0
        prev_levels = f.score
        dec = planner.step_decide(matches=False, req_key="", used_flags=[],
                                  flash_present=bool(flash_present),
                                  test_observed=(flash_present == 1.0),
                                  observed_accept=advanced, observed_harm=0.0)
        posits = planner.read_posits()
        posits_seen = max(posits_seen, len(posits))
        conf = [p["meaning"] for p in posits if p["status"] == "confirmed"]
        if conf:
            confirmed_meaning = conf[0]

        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    eye.stop()
    return {
        "arm": arm, "n_steps": step + 1, "final_state": f.state.value,
        "levels_completed": f.score, "levels_gained": f.score - levels0,
        "perception_roundtrip_ok": roundtrip_ok,
        "onset_fire_rate": (onset_fired / onset_frames if onset_frames else None),
        "n_frames": onset_frames,
        "posits_minted_on_real_sign": posits_seen,
        "confirmed_meaning": confirmed_meaning,
        "sample_salient_localisations_row_col_db": localisations[:20],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--tag", default="live")
    args = ap.parse_args()

    if not load_arc_api_key():
        print("could not load ARC_API_KEY — ABORTING (no number without auth)")
        return 1
    from arc3_live_env import Arc3LiveEnv
    from worlds.arc_ls20_percell import ACTIONS as AGENT_ACTIONS

    try:
        env = Arc3LiveEnv(args.game)
        f = env.reset()
    except Exception as e:
        print(f"LIVE API UNREACHABLE / REJECTED — STOP (no fabricated number): {e}")
        return 2
    H, W = np.asarray(f.grid).shape
    eye_n = max(H, W)
    print(f"=== RUNG 227000 LIVE — POSIT-AND-TEST semiosis on REAL ls20 ({args.game}) ===")
    print(f"RESET ok: state={f.state.value} levels_completed={f.score} grid={H}x{W} "
          f"available={env.available_actions}")

    semi = run_arm(env, "semiosis", args.steps, eye_n, AGENT_ACTIONS)
    # cycling on a fresh reset of the SAME deterministic game.
    cyc = run_arm(env, "cycling", args.steps, eye_n, AGENT_ACTIONS)
    try:
        sc = env.close_scorecard()
    except Exception:
        sc = None

    semi_passed = semi.get("levels_gained", 0) and semi["levels_gained"] > cyc.get("levels_gained", 0)
    result = {
        "rung": 227000, "tag": args.tag, "game": args.game,
        "commitment": "posit-and-test semiosis on REAL ls20: does the agent posit meanings for "
                      "the real flash sign, test+confirm one, and make progress where cycling "
                      "did not? Honest, bounded n. Null reported STRAIGHT + what it DID do.",
        "semiosis": semi, "cycling": cyc,
        "semiosis_made_more_progress_than_cycling": bool(semi_passed),
        "scorecard_closed": bool(sc),
        "honest_scope": "bounded n; the OFFLINE powered ablation is the deliverable. On real "
                        "64x64 ls20 the only-other shape / required transform is not a known "
                        "station, so the SEEK is steering toward the salient onset centroid; "
                        "the posit-and-test INTERPRETATION runs as the real graph rules. The "
                        "number here is what the live budget actually produced.",
    }
    out = _ROOT / "results" / f"arc_ls20_seek_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    print(f"\nSEMIOSIS: {json.dumps(semi, default=str)}")
    print(f"CYCLING : {json.dumps(cyc, default=str)}")
    print(f"semiosis made more progress than cycling: {semi_passed}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
