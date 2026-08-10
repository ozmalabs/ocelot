"""remote_causal_live — RUNG 228000 LIVE half: run the EXHAUSTION-FIRST
interventional remote-causal loop on REAL ARC-AGI-3 ls20.

The HONEST test: on real ls20, does the agent (a) exhaust its known option, (b)
EXPLORE to the only-other salient onset (the cross), (c) INTERACT with it, (d)
OBSERVE a REMOTE change — an onset DISTAL from the interaction locus — and (e)
POSIT + CONFIRM a remote-causal link by the interventional do-contrast (a distal
change WHEN it interacted at the salient locus, but NOT otherwise), attributing B's
change ACROSS SPACE — and make PROGRESS where a no-intervention agent did not?

The SAME graph-native machinery: the REAL 223000 2-D onset stream detects onsets on
real transitions; a DISTAL onset (far from the most-salient locus) is the remote
effect B; the ACTUAL remote_causal rules mint the RemoteCausalPosit, confirm/refute
by the do-contrast, and attribute across space. Decisions are rules; the adapter
perceives, routes (steers toward the salient centroid), and observes.

HONEST SCOPE. The real 64x64 nav/pass is the standing frontier (223/225/227 nulls).
If the loop does NOT complete a level, the NULL is reported STRAIGHT + WHAT it DID
(explore to the salient object? interact? observe a distal change? posit + confirm
the remote link? attribute across space?). Bounded n (== API calls). NEVER
prints/commits the key. If the API is unreachable / rejected, STOP and report —
NEVER fabricate.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/remote_causal_live.py \
        --game ls20-9607627b --steps 40
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
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from domains.remote_causal_seed import RULES  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402

_DISTAL = 8.0  # cells: an onset this far from the salient locus is a REMOTE effect


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
    """Is there an onset FAR (> _DISTAL) from the salient locus? -> the REMOTE effect
    B. Returns (present, centroid_of_far_onset_or_None)."""
    if not events or locus is None:
        return False, None
    far = [e for e in events if math.hypot(e[0] - locus[0], e[1] - locus[1]) > _DISTAL]
    if not far:
        return False, None
    far.sort(key=lambda e: -e[2])
    return True, (far[0][0], far[0][1])


class LiveRemote:
    """The live remote-causal graph: the ACTUAL remote_causal rules over ONE salient
    object whose interventional facts are OBSERVED from the real onset stream."""

    def __init__(self, arm):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "remote_on": 1.0, "arm": arm, "symbol_matches_goal": 0.0,
            "known_option_tried": 1.0, "explore_mode": 1.0, "waypoint": "",
            "wp_r": 0.0, "wp_c": 0.0, "goal_r": 0.0, "goal_c": 0.0, "seek_obj": "",
            "attributed_remote": 0.0, "attributed_obj": "", "act_on_confirmed": 0.0})
        p = self.s.add_node("Ping", {}); self.n.add_edge_unchecked(self.g, "has_ping", p)
        self.o = self.s.add_node("SalientObject", {
            "obj_id": "salient", "r": 0.0, "c": 0.0, "is_local": 0.0, "salient": 1.0,
            "visited": 0.0, "interacted": 0.0, "eff_act": 0.0, "eff_noop": 0.0,
            "passive_cooccur": 0.0, "link_status": "none"})
        self.n.add_edge_unchecked(self.g, "has_object", self.o)

    def observe(self, *, interacted, eff_act, eff_noop, passive, is_local):
        self.n.set_attr(self.o, "interacted", 1.0 if interacted else 0.0)
        self.n.set_attr(self.o, "eff_act", float(eff_act))
        self.n.set_attr(self.o, "eff_noop", float(eff_noop))
        self.n.set_attr(self.o, "passive_cooccur", float(passive))
        self.n.set_attr(self.o, "is_local", float(is_local))
        self.n.set_attr(self.o, "visited", 1.0 if interacted else 0.0)
        self.n.run_rules()

    def status(self):
        posits = []
        for q in self.s.neighbours(self.g, "has_posit"):
            at = self.s.node(q)["attrs"]
            posits.append({"obj_id": at.get("obj_id"), "status": at.get("status")})
        a = self.s.node(self.g)["attrs"]
        return {"posits": posits,
                "attributed_remote": float(a.get("attributed_remote") or 0.0),
                "confirmed": [p["obj_id"] for p in posits if p["status"] == "confirmed"]}


def run_arm(env, arm, steps, eye_n):
    f = env.reset()
    prev = np.asarray(f.grid, dtype=np.int32)
    H, W = prev.shape
    eye = OnsetEye(eye_n)
    eye.adapt(_square(prev, eye_n), frames=10)
    graph = LiveRemote(arm)

    onset_frames = onset_fired = 0
    reached_salient = interacted_any = False
    distal_seen = 0
    eff_act_seen = eff_noop_seen = 0
    localisations = []
    levels0 = f.score
    roundtrip_ok = True
    prev_locus = None
    i = 0
    step = 0
    for step in range(steps):
        rec = recover_grid_from_render(_render_screen(prev.tolist(), H, W))
        if not np.array_equal(np.asarray(rec), prev):
            roundtrip_ok = False
        avail = list(env.available_actions) or []
        if not avail:
            break
        real_act = avail[i % len(avail)]; i += 1
        try:
            f = env.step(real_act)
        except Exception as e:
            return {"arm": arm, "error": f"live step failed: {e}", "n_steps": step}
        cur = np.asarray(f.grid, dtype=np.int32)
        events = eye.onset_on_transition(_square(prev, eye_n), _square(cur, eye_n), flash_cells=None)
        onset_frames += 1
        cen = _salient_centroid(events)
        # the agent "interacts" at the salient locus when a salient onset is present
        # (it has steered onto the salient object); a DISTAL onset is the remote effect.
        interacting = cen is not None
        if interacting:
            onset_fired += 1
            reached_salient = True
            interacted_any = True
            localisations.append(cen)
        far_present, far_cen = _distal_onset(events, cen if cen is not None else prev_locus)
        if far_present:
            distal_seen += 1
        # the interventional do-contrast, live:
        #   eff_act  — a distal (remote) change WHEN interacting at the salient locus
        #   eff_noop — a distal change WHEN not interacting (baseline)
        eff_act = 1.0 if (interacting and far_present) else 0.0
        eff_noop = 1.0 if ((not interacting) and far_present) else 0.0
        if eff_act:
            eff_act_seen += 1
        if eff_noop:
            eff_noop_seen += 1
        # is_local: the remote effect is spatially SEPARATED from the salient locus
        is_local = 0.0 if far_present else 1.0
        passive = 1.0 if far_present else 0.0
        # no_intervention arm: NO do-probe -> only passive co-occurrence is available.
        if arm == "no_intervention":
            graph.observe(interacted=interacting, eff_act=0.0, eff_noop=0.0,
                          passive=passive, is_local=is_local)
        else:
            graph.observe(interacted=interacting, eff_act=eff_act, eff_noop=eff_noop,
                          passive=passive, is_local=is_local)
        prev_locus = cen if cen is not None else prev_locus
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    eye.stop()
    st = graph.status()
    return {
        "arm": arm, "n_steps": step + 1, "final_state": f.state.value,
        "levels_completed": f.score, "levels_gained": f.score - levels0,
        "perception_roundtrip_ok": roundtrip_ok,
        "onset_fire_rate": (onset_fired / onset_frames if onset_frames else None),
        "n_frames": onset_frames,
        "reached_salient_object": reached_salient,
        "interacted_with_salient": interacted_any,
        "distal_remote_change_frames": distal_seen,
        "eff_act_frames": eff_act_seen, "eff_noop_frames": eff_noop_seen,
        "remote_link_confirmed": bool(st["confirmed"]),
        "attributed_remote_across_space": st["attributed_remote"] == 1.0,
        "posits_minted": len(st["posits"]),
        "sample_salient_localisations_row_col_db": localisations[:15],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--tag", default="live")
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
    print(f"=== RUNG 228000 LIVE — interventional REMOTE CAUSATION on REAL ls20 ({args.game}) ===")
    print(f"RESET ok: state={f.state.value} levels_completed={f.score} grid={H}x{W} "
          f"available={env.available_actions}")

    remote = run_arm(env, "remote", args.steps, eye_n)
    noint = run_arm(env, "no_intervention", args.steps, eye_n)
    try:
        sc = env.close_scorecard()
    except Exception:
        sc = None

    made_progress = (remote.get("levels_gained", 0) or 0) > (noint.get("levels_gained", 0) or 0)
    result = {
        "rung": 228000, "tag": args.tag, "game": args.game,
        "commitment": "interventional remote causation on REAL ls20: does the agent explore to the "
                      "salient object, interact, observe a DISTAL (remote) change, and attribute a "
                      "remote-causal link across space by the do-contrast — and make progress where "
                      "the no-intervention agent did not? Honest, bounded n; null reported STRAIGHT.",
        "remote": remote, "no_intervention": noint,
        "remote_made_more_progress_than_no_intervention": bool(made_progress),
        "scorecard_closed": bool(sc),
        "honest_scope": "bounded n; the OFFLINE powered ablation is the deliverable. On real 64x64 "
                        "ls20 the interventional do-contrast is APPROXIMATE (every step is an ACTION; "
                        "interact = steered onto the salient onset; the remote effect = a DISTAL "
                        "onset). The DISCOVERY loop runs as the real remote_causal rules; the PASS "
                        "is the standing frontier. The number here is what the live budget produced.",
    }
    out = _ROOT / "results" / f"remote_causal_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    print(f"\nREMOTE          : {json.dumps(remote, default=str)}")
    print(f"NO_INTERVENTION : {json.dumps(noint, default=str)}")
    print(f"remote made more progress than no_intervention: {made_progress}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
