"""arc_ls20_triple_live — RUNG 232000 LIVE half: ISOLATE THE CLEAN TRIPLE on REAL
ls20 via RESIDUAL-AFTER-EXPLAINING-THE-AVATAR.

231 corrected the false null (the colour eye SEES a remote change the luma eye is
blind to) but could not ISOLATE the owner's clean triple: real ls20 has NO no-op
action, so the reach-frame raw diff MIXES the avatar's move with the effects.

The fix (held-prediction, NO no-op needed): drive 224's object-permanence tracker
alongside the nav — at every step PREDICT the next frame by translating the tracked
avatar (the learned per-action shift, graph data on a Percell), BEFORE stepping.
On the reach transition, the RESIDUAL against the stored avatar-prediction is the
surprise = the indicator + destination flash + exit-glyph rotation, with the avatar
removed. Precise nav walks the avatar ONTO the cross CELL (not merely near the
locus); the triple firing certifies the on-cell reach. Every claim is gated against
the GROUND-TRUTH raw pixel deltas, never the eye's self-report.

Reported STRAIGHT either way (all three separated + rotation recognised, or only
partial — an honest result). Bounded n == API calls. Never prints/commits the key.
API unreachable -> STOP and report, NEVER fabricate. States fresh-API.

Run: PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_triple_live.py \
        --game ls20-9607627b --nav 60
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

from worlds.arc_ls20_flash import OnsetEye  # noqa: E402
from worlds.arc_ls20_percell_track import field_colours, connected_figure_blob, LiveObjectTracker  # noqa: E402
from worlds.arc_ls20_percell import Percell, ACTIONS  # noqa: E402
from worlds.arc_ls20_see import (  # noqa: E402
    raw_changed_cells, changed_regions, _dist,
)
from worlds.arc_ls20_triple import isolate_triple, raw_diff_isolation  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402

MOVES = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
_DISTAL = 8.0


def _square(g, n):
    s = np.zeros((n, n), dtype=np.int32)
    s[:g.shape[0], :g.shape[1]] = g
    return s


def _avatar_centroid(prev, cur, fields):
    changed = [tuple(x) for x in np.argwhere(np.asarray(prev) != np.asarray(cur))]
    appeared = [(r, c) for (r, c) in changed
                if int(prev[r, c]) in fields and int(cur[r, c]) not in fields]
    seeds = appeared if appeared else changed
    if not seeds:
        return None
    blob = connected_figure_blob(np.asarray(cur), seeds, fields, cap=64)
    src = blob if blob else set(seeds)
    arr = np.array(list(src), dtype=float)
    return (float(arr[:, 0].mean()), float(arr[:, 1].mean()))


def _salient_onset_locus(events):
    if not events:
        return None
    events = sorted(events, key=lambda e: -e[2])
    return (float(events[0][0]), float(events[0][1]))


def _greedy_action(avatar, target, action_delta):
    best, best_d = None, 1e18
    for a, (dr, dc) in action_delta.items():
        nr, nc = avatar[0] + dr, avatar[1] + dc
        d = _dist((nr, nc), target)
        if d < best_d:
            best_d, best = d, a
    return best


def run_live(env, args):
    f = env.reset()
    prev = np.asarray(f.grid, dtype=np.int32)
    H, W = prev.shape
    eye_n = max(H, W)
    fields = field_colours(prev, 2)

    luma_eye = OnsetEye(eye_n)
    luma_eye.adapt(_square(prev, eye_n), frames=10)

    # the graph-native avatar model (224 tracker + Percell holding the shift data)
    agent = Percell()
    tracker = LiveObjectTracker(agent, cap=64, n_field=2)
    real_to_agent = {}

    def aname(real_act):
        if real_act not in real_to_agent:
            real_to_agent[real_act] = ACTIONS[len(real_to_agent) % len(ACTIONS)]
        return real_to_agent[real_act]

    # -- learn each move's avatar displacement + feed the tracker + find the cross --
    action_delta = {}
    avatar = None
    cross_hint = None
    calls = 1
    for a in MOVES:
        if a not in (env.available_actions or MOVES):
            continue
        try:
            f = env.step(a)
        except Exception as e:
            return {"error": f"probe step failed: {e}", "calls": calls}
        calls += 1
        cur = np.asarray(f.grid, dtype=np.int32)
        ev = luma_eye.onset_on_transition(_square(prev, eye_n), _square(cur, eye_n), None)
        loc = _salient_onset_locus(ev)
        if loc is not None:
            cross_hint = loc
        cen_prev = _avatar_centroid(prev, cur, fields) if avatar is None else avatar
        cen_new = _avatar_centroid(prev, cur, fields)
        if cen_prev is not None and cen_new is not None:
            action_delta[a] = (cen_new[0] - cen_prev[0], cen_new[1] - cen_prev[1])
        if cen_new is not None:
            avatar = cen_new
        tracker.observe(prev, cur, aname(a))     # learn the per-action shift (graph)
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    for i, a in enumerate(MOVES):
        if a not in action_delta:
            action_delta[a] = [(-1, 0), (1, 0), (0, -1), (0, 1)][i]

    target = cross_hint or (H * 0.7, W * 0.5)
    # -- PRECISE nav: step toward the cross, PREDICTING each next frame BEFORE the
    #    step (the tracker is stateful), until the avatar is ON the cross cell. Store
    #    frame[i], the action, the avatar, and the avatar-PREDICTED next frame. ------
    frames = [prev.copy()]
    avatars = [avatar or (H / 2, W / 2)]
    actions_taken = []
    predicted_next = []          # predicted_next[i] = avatar-prediction of frames[i+1]
    on_cell_steps = 0
    for step in range(args.nav):
        avail = [a for a in MOVES if a in (env.available_actions or MOVES)]
        if not avail:
            break
        av_ref = avatars[-1]
        act = _greedy_action(av_ref, target, action_delta)
        if act not in avail:
            act = avail[step % len(avail)]
        an = aname(act)
        pred = np.asarray(tracker.predict(prev, an), dtype=np.int32)  # BEFORE stepping
        try:
            f = env.step(act)
        except Exception as e:
            return {"error": f"nav step failed: {e}", "calls": calls}
        calls += 1
        cur = np.asarray(f.grid, dtype=np.int32)
        av_new = _avatar_centroid(prev, cur, fields) or av_ref
        frames.append(cur.copy())
        avatars.append(av_new)
        actions_taken.append(act)
        predicted_next.append(pred)
        tracker.observe(prev, cur, an)
        prev = cur
        # ON-CELL = avatar centroid within ~1.5 cells of the cross locus (not the
        # 231 locus-only radius of 6). Dwell a couple steps so reach + after land.
        if _dist(av_new, target) <= 1.5:
            on_cell_steps += 1
        if on_cell_steps >= 2 or f.state.value in ("WIN", "GAME_OVER"):
            break

    luma_eye.stop()

    # save EVERY nav frame + avatar + action + avatar-prediction, durable, so the
    # reach can be re-analysed offline with NO more API calls.
    try:
        allfp = _ROOT / "results" / f"arc_ls20_{args.tag}_allframes.json"
        allfp.write_text(json.dumps({
            "frames": [g.tolist() for g in frames],
            "avatars": [list(a) for a in avatars],
            "actions": actions_taken,
            "predicted_next": [np.asarray(p).tolist() for p in predicted_next],
            "target": list(target)}))
    except Exception:
        allfp = None

    # pick the reach transition = the ON-CELL ARRIVAL step where (a) the avatar
    # centroid lands on the cross cell AND (b) the tracker actually predicted the
    # avatar move (a NON-TRIVIAL prediction: predicted_next differs from before) —
    # only then is the residual a real avatar-explained residual, not the raw diff.
    # Among qualifying arrivals, prefer the strongest distal ground-truth change.
    reach_i = None
    best = (-1, -1)   # (predicted_nontrivial, distal_count)
    for i in range(len(frames) - 1):
        av = avatars[i + 1]
        on_cell = _dist(av, target) <= 2.5
        if not on_cell:
            continue
        nontrivial = int(len(raw_changed_cells(frames[i], predicted_next[i])) > 0)
        distal = sum(1 for reg in changed_regions(frames[i], frames[i + 1])
                     if _dist(reg["centroid"], av) > _DISTAL)
        if (nontrivial, distal) > best:
            best = (nontrivial, distal)
            reach_i = i
    # fallback: if no on-cell arrival, the closest-approach transition (reported as
    # NOT certified on-cell).
    if reach_i is None and len(frames) > 1:
        reach_i = min(range(len(frames) - 1), key=lambda i: _dist(avatars[i + 1], target))

    out = {"calls": calls, "grid": [int(H), int(W)], "cross_hint": cross_hint,
           "learned_action_delta": {a: [round(d[0], 2), round(d[1], 2)]
                                    for a, d in action_delta.items()},
           "min_avatar_dist_to_cross": round(min(_dist(a, target) for a in avatars), 2),
           "reached_the_cross_cell": bool(reach_i is not None
                                          and min(_dist(a, target) for a in avatars) <= 2.5),
           "reach_transition_index": reach_i}

    if reach_i is not None:
        before = frames[reach_i]
        reach = frames[reach_i + 1]
        after = frames[reach_i + 2] if reach_i + 2 < len(frames) else reach.copy()
        locus = tuple(avatars[reach_i + 1])
        predicted = predicted_next[reach_i]

        # THE ISOLATION — residual after explaining the avatar (gated vs ground truth)
        iso = isolate_triple(before, reach, after, None, actions_taken[reach_i], locus,
                             predicted=predicted)
        raw = raw_diff_isolation(before, reach, after, locus)

        # ground-truth cross-check: the raw diff (no explanation) size, and whether it
        # contains the avatar cells (the confound the residual removes).
        gt_regions = changed_regions(before, reach)
        avatar_cells = iso["avatar_cells"]
        raw_contains_avatar = bool(avatar_cells and avatar_cells <= raw["changed_cells"])

        # save the frames so the isolation can be re-analysed offline with NO more
        # API calls (the durable ground truth).
        try:
            fp = _ROOT / "results" / f"arc_ls20_{args.tag}_frames.json"
            fp.write_text(json.dumps({
                "before": before.tolist(), "reach": reach.tolist(),
                "after": after.tolist(), "predicted": np.asarray(predicted).tolist(),
                "locus": list(locus), "action": actions_taken[reach_i]}))
        except Exception:
            fp = None

        out.update({
            "reach_ground_truth_changed_cells": len(raw["changed_cells"]),
            "reach_ground_truth_regions": len(gt_regions),
            "n_residual_after_explaining_avatar": iso["n_residual"],
            "n_avatar_explained_cells": iso["n_avatar"],
            "residual_excludes_avatar": iso["residual_excludes_avatar"],
            "residual_avatar_overlap": iso["avatar_overlap"],
            "raw_diff_contains_avatar (the 231 confound)": raw_contains_avatar,
            "isolated_indicator_flash": iso["indicator_flash"],
            "isolated_destination_flash": iso["destination_flash"],
            "isolated_exit_rotation": iso["exit_rotation"],
            "rotation_key": iso["rotation_key"],
            "all_three_isolated": iso["all_three"],
            "n_residual_regions": len(iso["regions"]),
            "residual_region_kinds": [
                {"size": r["size"], "dist": round(r["dist_from_locus"], 1),
                 "distal": r["distal"], "transient": r["transient"]}
                for r in iso["regions"]],
            "frames_saved": str(fp) if fp else None,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--nav", type=int, default=60)
    ap.add_argument("--tag", default="triple_live")
    args = ap.parse_args()

    if not load_arc_api_key():
        print("could not load ARC_API_KEY — ABORTING (no number without auth)")
        return 1
    try:
        from arc3_live_env import Arc3LiveEnv
        env = Arc3LiveEnv(args.game)
        f = env.reset()
    except Exception as e:
        print(f"LIVE API UNREACHABLE / REJECTED — STOP (no fabricated number): {e}")
        return 2
    H, W = np.asarray(f.grid).shape
    print(f"=== RUNG 232000 LIVE — ISOLATE THE CLEAN TRIPLE on REAL ls20 ({args.game}) ===")
    print(f"RESET ok: state={f.state.value} levels={f.score} grid={H}x{W} "
          f"available={env.available_actions}")

    obs = run_live(env, args)
    try:
        sc = env.close_scorecard()
    except Exception:
        sc = None

    if obs.get("reached_the_cross_cell") and "all_three_isolated" in obs:
        verdict = (
            f"reached the cross cell (min avatar->cross dist "
            f"{obs['min_avatar_dist_to_cross']}). RESIDUAL-after-explaining-the-avatar: "
            f"n_residual={obs['n_residual_after_explaining_avatar']} of "
            f"{obs['reach_ground_truth_changed_cells']} raw changed; "
            f"excludes_avatar={obs['residual_excludes_avatar']} "
            f"(raw diff contains avatar={obs['raw_diff_contains_avatar (the 231 confound)']}). "
            f"ISOLATED indicator={obs['isolated_indicator_flash']} "
            f"destination={obs['isolated_destination_flash']} "
            f"rotation={obs['isolated_exit_rotation']}({obs['rotation_key']}); "
            f"ALL THREE={obs['all_three_isolated']}.")
    elif "n_residual_after_explaining_avatar" in obs:
        verdict = (
            f"reached a reach transition but NOT certified on-cell (min dist "
            f"{obs['min_avatar_dist_to_cross']}). PARTIAL — residual isolated "
            f"indicator={obs.get('isolated_indicator_flash')} "
            f"destination={obs.get('isolated_destination_flash')} "
            f"rotation={obs.get('isolated_exit_rotation')}; "
            f"excludes_avatar={obs.get('residual_excludes_avatar')}. Reported straight.")
    else:
        verdict = f"no reach transition found in budget; {obs.get('error', '')}".strip()

    result = {"rung": 232000, "tag": args.tag, "game": args.game,
              "commitment": "ISOLATE THE CLEAN TRIPLE on REAL ls20 via residual-after-"
                            "explaining-the-avatar; gate against GROUND-TRUTH deltas, "
                            "never the eye self-report.",
              "observe": obs, "honest_verdict": verdict, "fresh_api": True,
              "scorecard_closed": bool(sc)}
    out = _ROOT / "results" / f"arc_ls20_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nOBSERVE: {json.dumps({k: v for k, v in obs.items() if k != 'residual_region_kinds'}, default=str)[:1400]}")
    print(f"\nHONEST VERDICT: {verdict}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
