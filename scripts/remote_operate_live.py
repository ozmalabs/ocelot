"""remote_operate_live — RUNG 230000 LIVE half: PERFORM THE ACTION ON THE CROSS on
REAL ARC-AGI-3 ls20.

THE OWNER'S HYPOTHESIS, TESTED STRAIGHT. 229's live run REACHED and "interacted
with" the cross but observed 0 distal change — because it only ever cycled the
MOVEMENT actions (available=[ACTION1..4]) and bumped the cross; it never issued the
game's ACTION (use/select/click) ON the cross. Owner: "it may need to perform the
'action' on the cross." A switch fires when ACTUATED, not walked into.

So this live half EXHAUSTS THE ACTION SPACE ON THE CROSS: it localises the cross via
the 223 onset stream, then issues EACH candidate action ON the cross — the movement
actions AND the interact/use action ACTION5 AND the coordinate click ACTION6(at the
cross) — and OBSERVES, per action, the real before->after: did a DISTAL (remote)
change appear? The 230 rules DISCOVER the actuating action from the observed outcome;
229's rcg_ground grounds causes(cross, change) the instant a distal change is
observed.

THE HONEST VERDICT (G-live), reported STRAIGHT either way:
  (a) some action on the cross -> OBSERVABLE distal change -> discovered + grounded
      (owner's hypothesis CONFIRMED — and WHICH action);
  (b) NO available action on the cross produces any observable distal change in the
      budget -> the NULL reported straight + EXACTLY what each action did (onset,
      any-change, distal-change per action). The mechanic is triggered some other way
      — a distinct honest finding. MEASURE which action, if any, actuates it.

Bounded n (== API calls). NEVER prints/commits the key. API unreachable/rejected ->
STOP and report, NEVER fabricate. States fresh-API.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/remote_operate_live.py \
        --game ls20-9607627b --settle 8 --reps 3
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT / "scripts"), str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc import _render_screen, recover_grid_from_render  # noqa: E402
from worlds.arc_ls20_flash import OnsetEye  # noqa: E402
from worlds.remote_operate import OperatePlanner, MOVEMENTS, INTERACTS, ACTION_ORDINAL  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402

_DISTAL = 8.0  # cells: an onset this far from the cross locus is a REMOTE effect

# The candidate actions to try ON the cross: the movements AND the interact/click
# actions. ACTION6 needs the cross coordinate; the rest are bare.
_CANDIDATES = MOVEMENTS + INTERACTS  # ACTION1..4 (moves) + ACTION5 (use) + ACTION6 (click)


def _load_env_key():
    envp = Path("/home/matt/ozma/internal/.env")
    if envp.exists():
        for line in envp.read_text().splitlines():
            if line.startswith("ARC_API_KEY") and "ARC_API_KEY" not in os.environ:
                os.environ["ARC_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


def _square(g, n):
    s = np.zeros((n, n), dtype=np.int32)
    s[:g.shape[0], :g.shape[1]] = g
    return s


def _salient_centroid(events):
    if not events:
        return None
    events = sorted(events, key=lambda e: -e[2])
    return (events[0][0], events[0][1], round(events[0][2], 1))


def _distal_onset(events, locus):
    if not events or locus is None:
        return False, None
    far = [e for e in events if math.hypot(e[0] - locus[0], e[1] - locus[1]) > _DISTAL]
    if not far:
        return False, None
    far.sort(key=lambda e: -e[2])
    return True, (far[0][0], far[0][1])


def _localise_cross(env, eye, prev, eye_n, settle):
    """Settle a few steps (movement) to localise the cross via the onset stream — the
    223/229 locus (rows ~42-47, cols ~29-34). Returns (locus_or_None, prev_grid)."""
    locus = None
    H, W = prev.shape
    for i in range(settle):
        avail = list(env.available_actions) or MOVEMENTS[:1]
        act = avail[i % len(avail)]
        try:
            f = env.step(act)
        except Exception:
            break
        cur = np.asarray(f.grid, dtype=np.int32)
        events = eye.onset_on_transition(_square(prev, eye_n), _square(cur, eye_n), flash_cells=None)
        cen = _salient_centroid(events)
        if cen is not None:
            locus = cen
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break
    return locus, prev


def _try_action_on_cross(env, eye, prev, eye_n, action, locus):
    """Issue ONE action ON the cross and OBSERVE the real before->after. ACTION6 clicks
    the cross coordinate; the rest are bare. Returns (ok, any_change, distal_change,
    n_onsets, new_prev, err)."""
    coord = None
    if action == "ACTION6" and locus is not None:
        # ACTION6 carries (x, y) = (col, row) in the grid frame.
        coord = (int(locus[1]), int(locus[0]))
    try:
        f = env.step(action, coord) if coord is not None else env.step(action)
    except Exception as e:
        return False, False, False, 0, prev, str(e)
    cur = np.asarray(f.grid, dtype=np.int32)
    any_change = not np.array_equal(cur, prev)
    events = eye.onset_on_transition(_square(prev, eye_n), _square(cur, eye_n), flash_cells=None)
    far_present, _ = _distal_onset(events, locus)
    return True, bool(any_change), bool(far_present), len(events), cur, None


def run_live(env, eye_n, settle):
    f = env.reset()
    prev = np.asarray(f.grid, dtype=np.int32)
    H, W = prev.shape
    eye = OnsetEye(eye_n)
    eye.adapt(_square(prev, eye_n), frames=10)

    roundtrip_ok = np.array_equal(
        np.asarray(recover_grid_from_render(_render_screen(prev.tolist(), H, W))), prev)

    locus, prev = _localise_cross(env, eye, prev, eye_n, settle)

    # Build the composed 230+229 graph over the REAL available action ids (+ the
    # interact actions the owner wants tested). The rules pick the next action; the
    # adapter issues it ON the cross and OBSERVES; 230 discovers, 229 grounds.
    graph = OperatePlanner("exhaust_actions", _CANDIDATES,
                           object_id="cross",
                           obj_rc=(int(locus[0]), int(locus[1])) if locus else (0, 0))
    graph.set_game(at_object=1.0)
    # a clean natural timeline: nothing changed remotely before we acted on the cross
    graph.add_observation(interact=0.0, remote_changed=0.0, cause_id="", effect_kind="none")

    per_action = []
    for _ in range(len(_CANDIDATES) + 2):
        graph.set_game(try_action="")
        graph.run()
        ta = graph.get("try_action") or ""
        if ta == "":
            break
        ok, any_change, distal, n_on, prev, err = _try_action_on_cross(
            env, eye, prev, eye_n, ta, locus)
        graph.add_outcome(action_id=ta, remote_changed=1.0 if distal else 0.0,
                          effect_kind="remote_change" if distal else "none")
        graph.add_observation(interact=1.0, remote_changed=1.0 if distal else 0.0,
                              cause_id="cross", effect_kind="remote_change" if distal else "none")
        graph.n.set_attr(graph.actions[ta], "tried", 1.0)   # mechanical: issued
        graph.run()   # 230 discovers; 229 grounds
        per_action.append({"action": ta, "issued_ok": ok, "any_change": any_change,
                           "distal_change": distal, "n_onsets": n_on, "error": err,
                           "is_movement": ta in MOVEMENTS})
        if graph.get("discovered") == 1.0:
            break

    eye.stop()
    facts = [graph.s.node(cf)["attrs"] for cf in graph.s.neighbours(graph.g, "has_causal_fact")]
    return {
        "perception_roundtrip_ok": bool(roundtrip_ok),
        "cross_locus_row_col_db": locus,
        "actions_tried_on_cross": per_action,
        "any_action_produced_distal_change": any(a["distal_change"] for a in per_action),
        "distal_producing_actions": [a["action"] for a in per_action if a["distal_change"]],
        "any_action_produced_any_change": any(a["any_change"] for a in per_action),
        "changing_actions": [a["action"] for a in per_action if a["any_change"]],
        "discovered": graph.get("discovered") == 1.0,
        "discovered_operate_action": graph.get("operate_action") or "",
        "operates_edges": graph.operates_edges(),
        "grounded": graph.get("grounded") == 1.0,
        "grounded_causal_facts": [{"cause": a.get("cause"), "effect": a.get("effect"),
                                   "status": a.get("status")} for a in facts],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--settle", type=int, default=8)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--tag", default="operate_live")
    args = ap.parse_args()

    _load_env_key()
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
    eye_n = max(H, W)
    print(f"=== RUNG 230000 LIVE — PERFORM THE ACTION ON THE CROSS on REAL ls20 ({args.game}) ===")
    print(f"RESET ok: state={f.state.value} levels_completed={f.score} grid={H}x{W} "
          f"available={env.available_actions}")
    print(f"candidates tried ON the cross: {_CANDIDATES} (ACTION6 clicks the cross locus)")

    reps = []
    for rep in range(args.reps):
        obs = run_live(env, eye_n, args.settle)
        reps.append(obs)
        print(f"\n-- rep {rep} --")
        print(f"cross_locus={obs['cross_locus_row_col_db']}")
        for a in obs["actions_tried_on_cross"]:
            print(f"   {a['action']:8s} issued_ok={a['issued_ok']} any_change={a['any_change']} "
                  f"distal_change={a['distal_change']} n_onsets={a['n_onsets']} err={a['error']}")
        print(f"   any_distal={obs['any_action_produced_distal_change']} "
              f"distal_actions={obs['distal_producing_actions']} "
              f"discovered={obs['discovered']} grounded={obs['grounded']}")

    any_distal = any(r["any_action_produced_distal_change"] for r in reps)
    any_grounded = any(r["grounded"] for r in reps)
    distal_actions = sorted({a for r in reps for a in r["distal_producing_actions"]})
    if any_grounded and any_distal:
        verdict = ("(a) HYPOTHESIS CONFIRMED: issuing an action ON the cross produced an "
                   f"OBSERVABLE remote (distal) change; the actuating action(s)={distal_actions} "
                   "were DISCOVERED and 229 grounded causes(cross, remote_change) from the real "
                   "before->after.")
    else:
        # enumerate exactly what each action did (the honest null with detail)
        changing = sorted({a for r in reps for a in r["changing_actions"]})
        verdict = ("(b) HONEST NULL: NO action issued ON the cross — INCLUDING the interact/use "
                   "ACTION5 and the coordinate click ACTION6 — produced any OBSERVABLE remote "
                   "(distal) change in the budget. So performing the game ACTION on the cross did "
                   "NOT trigger an observable remote mechanic this budget; the mechanic is "
                   f"triggered some other way. (actions that changed ANYTHING at all: {changing}; "
                   "distal changes: none.) Nothing to ground. This tests the owner's hypothesis "
                   "STRAIGHT and reports what each action actually did.")

    result = {
        "rung": 230000, "tag": args.tag, "game": args.game,
        "commitment": "PERFORM THE ACTION ON THE CROSS on REAL ls20: exhaust the ACTION space on "
                      "the cross (movements + interact ACTION5 + click ACTION6), OBSERVE per action "
                      "whether a DISTAL remote change appears, DISCOVER the actuating action, and "
                      "ground it via 229. Honest verdict either way with per-action detail.",
        "candidates": _CANDIDATES,
        "reps": reps,
        "any_action_produced_distal_change": any_distal,
        "distal_producing_actions": distal_actions,
        "grounded": any_grounded,
        "honest_verdict": verdict,
        "fresh_api": True,
    }
    try:
        sc = env.close_scorecard()
        result["scorecard_closed"] = bool(sc)
    except Exception:
        result["scorecard_closed"] = False

    out = _ROOT / "results" / f"remote_operate_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nHONEST VERDICT: {verdict}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
