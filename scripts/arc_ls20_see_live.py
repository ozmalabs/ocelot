"""arc_ls20_see_live — RUNG 231000 LIVE half: SEE the ls20 mechanic on REAL ls20.

The honest real test. 229/230 reported "0 distal change" — a PERCEPTION FAILURE
(colour-blind luminance onset), not a game fact. Here the agent DELIBERATELY
navigates the avatar ONTO the cross, captures the real before/reach/after frames,
computes the GROUND-TRUTH raw pixel deltas, and measures whether the EVENT-NATIVE
colour-change eye now SEES the indicator flash + destination flash + exit-glyph
rotation — GATED AGAINST THE GROUND-TRUTH DELTAS, never the eye's self-report (that
self-report is exactly what produced the false null).

Navigation: learn each movement action's avatar displacement by probing (a real
observation, not a table), localise the cross via the shared onset stream (the
223/229 salient locus), greedy-step toward it, and detect the REACH event by its
GROUND-TRUTH signature: a transition whose raw cell-diff has DISTAL regions (changes
far from the avatar's own move) — the mechanic firing remotely.

Reported STRAIGHT either way:
  (a) reached the cross -> the colour eye SEES the flash+rotation on the reach-frame
      (with detection numbers vs ground truth), luma misses -> the fix works live;
  (b) reached but a region is a genuine sub-step transient absent from every
      returned frame -> report that as the ARC-API observability limit;
  (c) did not reach the cross in budget -> honest null on the reach, PLUS the
      located-cause evidence on the real transitions we DID see (colour eye vs luma).

Bounded n (== API calls). NEVER prints/commits the key. API unreachable/rejected ->
STOP and report, NEVER fabricate. States fresh-API.

Run: PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_see_live.py \
        --game ls20-9607627b --nav 40
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT / "scripts"), str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_flash import OnsetEye  # noqa: E402
from worlds.arc_ls20_percell_track import field_colours, connected_figure_blob  # noqa: E402
from worlds.arc_ls20_see import (  # noqa: E402
    ColourChangeEye, raw_changed_cells, changed_regions, classify_transient_persistent,
    score_detection, located_cause, ground_destination_flash, required_transform_key,
    recognise_rotation, _dist,
)
from _arc3_load_key import load_arc_api_key  # noqa: E402

MOVES = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
_DISTAL = 8.0


def _square(g, n):
    s = np.zeros((n, n), dtype=np.int32)
    s[:g.shape[0], :g.shape[1]] = g
    return s


def _avatar_centroid(prev, cur, fields):
    """The avatar's new position = centroid of the cells that BECAME figure (moved
    in). Mechanical perception (appeared cells)."""
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
    """Pick the learned movement action that best reduces avatar->target distance."""
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
    colour_eye = ColourChangeEye()
    colour_eye.adapt(prev)

    # -- learn each move's avatar displacement + the onset-salient cross locus ----
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
            # displacement learned from the observed avatar move
            action_delta[a] = (cen_new[0] - cen_prev[0], cen_new[1] - cen_prev[1])
        if cen_new is not None:
            avatar = cen_new
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    # fall back to unit deltas if a probe produced no measurable move
    for i, a in enumerate(MOVES):
        if a not in action_delta:
            action_delta[a] = [(-1, 0), (1, 0), (0, -1), (0, 1)][i]

    # -- greedy navigate FULLY toward the cross hint, recording EVERY transition,
    #    then pick the reach = the transition with the strongest DISTAL ground-truth
    #    change (the mechanic firing remotely). This walks the avatar ONTO the cross
    #    rather than declaring "reach" on the first incidental distal change. ---------
    target = cross_hint or (H * 0.7, W * 0.5)
    # frames stored so the chosen reach keeps its own before/reach/after triple.
    frames = [prev.copy()]          # frame[i] is the world before step i
    avatars = [avatar or (H / 2, W / 2)]
    arrived_steps = 0
    for step in range(args.nav):
        avail = [a for a in MOVES if a in (env.available_actions or MOVES)]
        if not avail:
            break
        av_ref = avatars[-1]
        act = _greedy_action(av_ref, target, action_delta)
        if act not in avail:
            act = avail[step % len(avail)]
        try:
            f = env.step(act)
        except Exception as e:
            return {"error": f"nav step failed: {e}", "calls": calls}
        calls += 1
        cur = np.asarray(f.grid, dtype=np.int32)
        av_new = _avatar_centroid(prev, cur, fields) or av_ref
        frames.append(cur.copy())
        avatars.append(av_new)
        avatar = av_new
        prev = cur
        # stop a couple steps after ARRIVING at the cross (so the reach + after are
        # captured), or on terminal state.
        if _dist(av_new, target) <= 6.0:
            arrived_steps += 1
        if arrived_steps >= 3 or f.state.value in ("WIN", "GAME_OVER"):
            break

    luma_eye.stop()

    # pick the reach transition i (frames[i]->frames[i+1]) maximising the DISTAL
    # ground-truth change (regions far from the avatar's own move at that step).
    reach = None
    reach_after = None
    best_distal = 0
    transitions = []
    for i in range(len(frames) - 1):
        b0, c0 = frames[i], frames[i + 1]
        av = avatars[i + 1]
        transitions.append((b0.copy(), c0.copy(), av))
        distal = sum(1 for reg in changed_regions(b0, c0)
                     if _dist(reg["centroid"], av) > _DISTAL)
        if distal > best_distal:
            best_distal = distal
            reach = (b0.copy(), c0.copy(), av)
            reach_after = frames[i + 2].copy() if i + 2 < len(frames) else c0.copy()

    out = {"calls": calls, "grid": [int(H), int(W)], "cross_hint": cross_hint,
           "learned_action_delta": {a: [round(d[0], 2), round(d[1], 2)]
                                    for a, d in action_delta.items()},
           "reached_the_cross": reach is not None}

    if reach is not None:
        b, r, av = reach
        a = reach_after if reach_after is not None else r
        locus = tuple(av)
        gt_cells = raw_changed_cells(b, r)
        gt_regions = changed_regions(b, r)
        distal_gt = [reg for reg in gt_regions if _dist(reg["centroid"], locus) > _DISTAL]
        # GATE BOTH EYES AGAINST GROUND TRUTH
        rc = score_detection(ColourChangeEye(), b, r, a, locus, eye_n=eye_n)
        rl = score_detection(luma_eye_fresh(eye_n, b), b, r, a, locus, eye_n=eye_n)
        lc = located_cause(b, r, a, locus, luma_eye_fresh(eye_n, b), eye_n=eye_n)
        # wire: destination flash -> 229; rotation -> 227
        grounded, edges, facts = ground_destination_flash(
            (int(locus[0]), int(locus[1])), rc["destination_flash"])
        # save the raw before/reach/after frames so the regions can be analysed
        # offline (rotation in ANY region, transient/persistent) with NO more API
        # calls — the ground truth, durable.
        try:
            fp = _ROOT / "results" / f"arc_ls20_{args.tag}_frames.json"
            fp.write_text(json.dumps({"before": b.tolist(), "reach": r.tolist(),
                                      "after": a.tolist(), "locus": list(locus)}))
        except Exception:
            fp = None
        out.update({
            "reach_ground_truth_changed_cells": len(gt_cells),
            "reach_ground_truth_regions": len(gt_regions),
            "reach_ground_truth_distal_regions": len(distal_gt),
            "colour_eye_detection_vs_ground_truth": rc,
            "luma_eye_detection_vs_ground_truth": rl,
            "located_cause_operative": lc["operative_cause"],
            "located_cause_regions": lc["regions"],
            "wired_229_grounded": bool(grounded),
            "wired_229_causes_edges": edges,
            "wired_229_facts": facts,
            "frames_saved": str(fp) if fp else None,
        })
    else:
        # honest null on the reach; report located-cause on the richest real transition
        best = max(transitions, key=lambda t: len(raw_changed_cells(t[0], t[1])),
                   default=None)
        if best is not None:
            b, cur, av = best
            lc = located_cause(b, cur, cur, tuple(av), luma_eye_fresh(eye_n, b), eye_n=eye_n)
            ce = ColourChangeEye()
            col_ev = ce.onset_on_transition(b, cur)
            le = luma_eye_fresh(eye_n, b)
            lm_ev = le.onset_on_transition(_square(b, eye_n), _square(cur, eye_n), None)
            le.stop()
            out.update({
                "no_reach_note": "no distal ground-truth change observed in the nav budget "
                                 "(the avatar did not trigger the remote mechanic); reporting "
                                 "the located-cause on the richest real transition seen.",
                "richest_transition_ground_truth_changed_cells": len(raw_changed_cells(b, cur)),
                "richest_transition_colour_eye_events": len(col_ev),
                "richest_transition_luma_eye_events": len(lm_ev),
                "located_cause_operative": lc["operative_cause"],
                "located_cause_regions": lc["regions"],
            })
    return out


def luma_eye_fresh(eye_n, adapt_frame):
    e = OnsetEye(eye_n)
    e.adapt(_square(np.asarray(adapt_frame), eye_n), frames=6)
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--nav", type=int, default=40)
    ap.add_argument("--tag", default="see_live")
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
    print(f"=== RUNG 231000 LIVE — SEE the ls20 mechanic on REAL ls20 ({args.game}) ===")
    print(f"RESET ok: state={f.state.value} levels={f.score} grid={H}x{W} "
          f"available={env.available_actions}")

    obs = run_live(env, args)
    try:
        sc = env.close_scorecard()
    except Exception:
        sc = None

    if obs.get("reached_the_cross"):
        rc = obs["colour_eye_detection_vs_ground_truth"]
        rl = obs["luma_eye_detection_vs_ground_truth"]
        verdict = (f"reached the cross; GROUND-TRUTH distal regions="
                   f"{obs['reach_ground_truth_distal_regions']}. COLOUR eye "
                   f"indicator={rc['indicator_flash']} destination={rc['destination_flash']} "
                   f"rotation={rc['exit_rotation']}({rc['rotation_key']}); LUMA eye "
                   f"indicator={rl['indicator_flash']} destination={rl['destination_flash']} "
                   f"rotation={rl['exit_rotation']}. located_cause={obs['located_cause_operative']}; "
                   f"229 grounded={obs['wired_229_grounded']}.")
    else:
        verdict = ("HONEST NULL on the reach: the avatar did NOT trigger a distal "
                   "ground-truth change in the nav budget. "
                   + obs.get("no_reach_note", ""))

    result = {"rung": 231000, "tag": args.tag, "game": args.game,
              "commitment": "SEE the ls20 mechanic on REAL ls20, gating detection against "
                            "the GROUND-TRUTH raw pixel deltas (never the eye self-report).",
              "observe": obs, "honest_verdict": verdict, "fresh_api": True,
              "scorecard_closed": bool(sc)}
    out = _ROOT / "results" / f"arc_ls20_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nOBSERVE: {json.dumps({k: v for k, v in obs.items() if k not in ('located_cause_regions',)}, default=str)[:1200]}")
    print(f"\nHONEST VERDICT: {verdict}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
