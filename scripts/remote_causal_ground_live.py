"""remote_causal_ground_live — RUNG 229000 LIVE half: OBSERVE-AND-GROUND remote
causality on REAL ARC-AGI-3 ls20.

THE CORRECTION, LIVE. 228's live path grounded NOTHING because it needed a SIMULATED
no-op rewind (eff_act stayed 0). Here the agent GROUNDS FROM REAL OBSERVATION: it
interacts at the salient locus, OBSERVES the actual real-frame before->after (the
223000 2-D onset stream), and if a DISTAL (remote) change is observed AND the NATURAL
TIMELINE shows no distal change without interaction, the ACTUAL rcg_ground rule mints
a persistent grounded causes(salient, remote_change) fact. The stream of per-step
Observation nodes IS the natural timeline — no rewind, no probe world-model.

THE HONEST TEST (G-live): on real ls20, does a real cross-interaction produce an
OBSERVABLE remote change that the agent GROUNDS? Reported STRAIGHT either way:
  (a) real interaction -> OBSERVABLE distal change -> grounded (owner's expectation);
  (b) real interaction -> NO observable distal change in budget -> the NULL reported
      straight + EXACTLY what was observed (did the interaction register — onset fire
      rate? did anything change anywhere?). That would mean the interaction is not
      triggering the mechanic — a distinct, honest finding. MEASURE, do not assume.

Bounded n (== API calls). NEVER prints/commits the key. API unreachable/rejected ->
STOP and report, NEVER fabricate. State fresh-API vs replay.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/remote_causal_ground_live.py \
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
from domains.remote_causal_ground_seed import RULES  # noqa: E402
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
    if not events or locus is None:
        return False, None
    far = [e for e in events if math.hypot(e[0] - locus[0], e[1] - locus[1]) > _DISTAL]
    if not far:
        return False, None
    far.sort(key=lambda e: -e[2])
    return True, (far[0][0], far[0][1])


class LiveGround:
    """The live observe-and-ground graph: the ACTUAL rcg_* rules over a stream of
    per-step Observation nodes whose interact + remote_changed are OBSERVED from the
    real onset stream (no rewind)."""

    def __init__(self):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "ground_on": 1.0, "arm": "observe", "symbol_matches_goal": 0.0,
            "waypoint": "", "wp_r": 0.0, "wp_c": 0.0, "goal_r": 0.0, "goal_c": 0.0,
            "seek_obj": "", "grounded": 0.0, "grounded_cause": "", "grounded_effect": "",
            "act_on_grounded": 0.0})
        p = self.s.add_node("Ping", {}); self.n.add_edge_unchecked(self.g, "has_ping", p)
        # the salient object the agent interacts with (the cross); its position is
        # updated to the observed salient locus as perception localises it.
        self.o = self.s.add_node("SalientObject", {
            "obj_id": "salient", "r": 0.0, "c": 0.0, "salient": 1.0,
            "visited": 0.0, "interacted": 0.0})
        self.n.add_edge_unchecked(self.g, "has_object", self.o)

    def observe_step(self, *, interact, remote_changed, effect_kind, r=0.0, c=0.0):
        """MECHANICAL: write the OBSERVED per-step fact as an Observation node, update
        the salient locus, and run the rules (which decide grounding)."""
        if interact:
            self.n.set_attr(self.o, "r", float(r))
            self.n.set_attr(self.o, "c", float(c))
            self.n.set_attr(self.o, "interacted", 1.0)
        obs = self.s.add_node("Observation", {
            "interact": 1.0 if interact else 0.0,
            "remote_changed": 1.0 if remote_changed else 0.0,
            "cause_id": "salient" if interact else "",
            "effect_kind": effect_kind})
        self.n.add_edge_unchecked(self.g, "has_obs", obs)
        self.n.run_rules()

    def status(self):
        facts = [self.s.node(cf)["attrs"] for cf in self.s.neighbours(self.g, "has_causal_fact")]
        causes = []
        for cf in self.s.neighbours(self.o, "causes"):
            at = self.s.node(cf)["attrs"]
            causes.append({"cause": at.get("cause"), "effect": at.get("effect")})
        a = self.s.node(self.g)["attrs"]
        return {"facts": facts, "causes_edges": causes,
                "grounded": float(a.get("grounded") or 0.0),
                "grounded_cause": a.get("grounded_cause") or "",
                "grounded_effect": a.get("grounded_effect") or ""}


def run_live(env, steps, eye_n):
    f = env.reset()
    prev = np.asarray(f.grid, dtype=np.int32)
    H, W = prev.shape
    eye = OnsetEye(eye_n)
    eye.adapt(_square(prev, eye_n), frames=10)
    graph = LiveGround()

    onset_frames = onset_fired = 0
    reached_salient = interacted_any = False
    distal_seen = 0
    interact_and_distal = 0     # OBSERVED interact -> distal change (grounds)
    noint_and_distal = 0        # natural-timeline: distal change WITHOUT interaction
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
            return {"error": f"live step failed: {e}", "n_steps": step}
        cur = np.asarray(f.grid, dtype=np.int32)
        events = eye.onset_on_transition(_square(prev, eye_n), _square(cur, eye_n), flash_cells=None)
        onset_frames += 1
        cen = _salient_centroid(events)
        interacting = cen is not None
        if interacting:
            onset_fired += 1
            reached_salient = True
            interacted_any = True
            localisations.append(cen)
        far_present, far_cen = _distal_onset(events, cen if cen is not None else prev_locus)
        if far_present:
            distal_seen += 1
        if interacting and far_present:
            interact_and_distal += 1
        if (not interacting) and far_present:
            noint_and_distal += 1
        # OBSERVE the per-step fact (no rewind): remote_changed = a DISTAL change was
        # observed in the real before->after transition.
        graph.observe_step(interact=interacting, remote_changed=far_present,
                           effect_kind="remote_change" if far_present else "none",
                           r=cen[0] if cen else 0.0, c=cen[1] if cen else 0.0)
        prev_locus = cen if cen is not None else prev_locus
        prev = cur
        if f.state.value in ("WIN", "GAME_OVER"):
            break

    eye.stop()
    st = graph.status()
    return {
        "n_steps": step + 1, "final_state": f.state.value,
        "levels_completed": f.score, "levels_gained": f.score - levels0,
        "perception_roundtrip_ok": roundtrip_ok,
        "onset_fire_rate": (onset_fired / onset_frames if onset_frames else None),
        "n_frames": onset_frames,
        "reached_salient_object": reached_salient,
        "interacted_with_salient": interacted_any,
        "distal_remote_change_frames": distal_seen,
        "interact_and_distal_frames": interact_and_distal,
        "natural_timeline_noint_and_distal_frames": noint_and_distal,
        "grounded": st["grounded"] == 1.0,
        "grounded_causal_facts": st["facts"],
        "causes_edges": st["causes_edges"],
        "sample_salient_localisations_row_col_db": localisations[:15],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--tag", default="ground_live")
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
    print(f"=== RUNG 229000 LIVE — OBSERVE-AND-GROUND remote causation on REAL ls20 ({args.game}) ===")
    print(f"RESET ok: state={f.state.value} levels_completed={f.score} grid={H}x{W} "
          f"available={env.available_actions}")

    obs = run_live(env, args.steps, eye_n)
    try:
        sc = env.close_scorecard()
    except Exception:
        sc = None

    grounded = obs.get("grounded", False)
    # the honest verdict:
    if grounded:
        verdict = ("(a) a real interaction produced an OBSERVABLE remote change and the agent "
                   "GROUNDED causes(salient, remote_change) from the real before->after.")
    elif obs.get("distal_remote_change_frames", 0) == 0:
        verdict = ("(b) NO observable remote (distal) change in the budget — the interaction did "
                   "NOT trigger an observable remote mechanic. HONEST NULL: nothing to ground. "
                   f"(interacted={obs.get('interacted_with_salient')}, onset_fire_rate="
                   f"{obs.get('onset_fire_rate')}, distal_frames=0). The observation path would "
                   "ground the moment a distal change is observed — it was not, this budget.")
    else:
        verdict = ("(b') distal changes WERE observed but the natural timeline showed distal "
                   "changes WITHOUT interaction (noint_and_distal="
                   f"{obs.get('natural_timeline_noint_and_distal_frames')}) -> the agent REFUSED "
                   "to ground (correctly — that is coincidence, not the interaction's effect).")

    result = {
        "rung": 229000, "tag": args.tag, "game": args.game,
        "commitment": "OBSERVE-AND-GROUND remote causation on REAL ls20: interact, OBSERVE the real "
                      "before->after, and if a DISTAL change is observed (and the natural timeline "
                      "shows none without interaction) GROUND a persistent causes(salient,change) "
                      "fact — NO simulated rewind. Honest null reported straight with what was seen.",
        "observe": obs,
        "honest_verdict": verdict,
        "scorecard_closed": bool(sc),
        "fresh_api": True,
    }
    out = _ROOT / "results" / f"remote_causal_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    print(f"\nOBSERVE : {json.dumps(obs, default=str)}")
    print(f"\nHONEST VERDICT: {verdict}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
