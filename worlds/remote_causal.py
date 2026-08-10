"""remote_causal — RUNG 228000: REMOTE CAUSATION — the MECHANICAL world adapter +
probe/episode drivers for the exhaustion-first interventional remote-causal loop.

ALL decisions live in the graph rules (domains/remote_causal_seed.py). The adapter
does only:

  PERCEIVE  — write the perception facts the rules read (symbol_matches_goal;
              known_option_tried; each salient object's visited/interacted/is_local;
              the OBSERVED interventional facts eff_act/eff_noop/passive_cooccur).
  PROBE     — run the interventional do-contrast as WORLD PHYSICS: observe whether
              the REMOTE target B changes when the agent DID interact with an object
              (eff_act) vs did NOT (eff_noop). Pure world response; the RULE decides
              confirm/refute from the contrast.
  ACT       — read the rule-chosen waypoint and STEP toward it (greedy Manhattan).
              No rule chose a waypoint (causal_prior) -> cycle a fixed action seq.
  WORLD     — OPERATE an object when the avatar arrives at it as the chosen
              destination; committing the operate applies the remote effect to B
              (B matches). Pass at the block by the oracle.

There is NO Python deciding the causal link, the exploration target, or the move.

Two board FLAVOURS share the SAME rules and adapter, proving domain-agnosticism:
  * "ls20"  — a CROSS (remote switch) whose operate rotates the carried SHAPE.
  * "doom"  — a LEVER (remote switch) whose operate opens a remote DOOR.
The flavour only changes the object LABELS + goal wording (cosmetic); the graph
structure and every rule are identical.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from domains.remote_causal_seed import RULES  # noqa: E402

# a fixed blind action cycle (the causal_prior "never explores" baseline)
_CYCLE = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Up, Right, Down, Left


# ===========================================================================
# THE PROBE WORLD-MODEL — a tiny deterministic world whose response to the
# interventional do-operation is OBSERVED (not asserted). eff_act/eff_noop come
# from actually running the world under (intervene) vs (no-op); the RULE decides
# confirm/refute. `truth` is the scenario ground truth:
#   controls[obj_id]  — does operating this object CAUSE B to change? (real link)
#   spontaneous       — does B change on its own regardless of any operate?
# ===========================================================================
def _world_B_changes(truth, obj_id, intervene):
    """Run one trial: return True iff the remote target B changes when we either
    intervene on obj_id (do(obj)) or do nothing (no-op), under this world's ground
    truth. This is the world's PHYSICS — the agent only OBSERVES the outcome."""
    changed = False
    if intervene and truth["controls"].get(obj_id, False):
        changed = True          # operating a true cause changes B
    if truth["spontaneous"]:
        changed = True          # B drifts on its own regardless
    return changed


def observe_intervention(truth, obj_id):
    """The agent's interventional observation of one object: run the do-probe
    (intervene) and the no-op probe, and note passive co-occurrence. Returns the
    three integer flags the rules read. A REVERSIBLE test — B is not committed."""
    eff_act = 1.0 if _world_B_changes(truth, obj_id, intervene=True) else 0.0
    eff_noop = 1.0 if _world_B_changes(truth, obj_id, intervene=False) else 0.0
    # passive co-occurrence: over the episode B changed at all (a true cause was
    # operated somewhere, or B drifted) AND this object was present -> it co-occurs.
    episode_changed = truth["spontaneous"] or any(truth["controls"].values())
    passive = 1.0 if episode_changed else 0.0
    return eff_act, eff_noop, passive


# ===========================================================================
# THE PLANNER SUBSTRATE (rules install; the DECISION is graph-native)
# ===========================================================================
class RemotePlanner:
    """Holds the game + salient-object nodes + the remote_causal rules. Each step
    the adapter stamps perception facts and run_rules() drives exhaust -> explore ->
    posit -> confirm -> act -> pass (the graph's decision)."""

    def __init__(self, arm, objects, goal_rc):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "remote_on": 1.0, "arm": arm, "symbol_matches_goal": 0.0,
            "known_option_tried": 0.0, "explore_mode": 0.0, "waypoint": "",
            "wp_r": 0.0, "wp_c": 0.0, "goal_r": float(goal_rc[0]), "goal_c": float(goal_rc[1]),
            "seek_obj": "", "attributed_remote": 0.0, "attributed_obj": "",
            "act_on_confirmed": 0.0, "affect": ""})
        p = self.s.add_node("Ping", {})
        self.n.add_edge_unchecked(self.g, "has_ping", p)
        self.objects = {}
        for o in objects:
            on = self.s.add_node("SalientObject", {
                "obj_id": o["obj_id"], "r": float(o["r"]), "c": float(o["c"]),
                "is_local": float(o["is_local"]), "salient": 1.0,
                "visited": 0.0, "interacted": 0.0,
                "eff_act": 0.0, "eff_noop": 0.0, "passive_cooccur": 0.0,
                "link_status": "none"})
            self.n.add_edge_unchecked(self.g, "has_object", on)
            self.objects[o["obj_id"]] = on

    def set_game(self, **kw):
        for k, v in kw.items():
            self.n.set_attr(self.g, k, v)

    def mark_object(self, obj_id, **kw):
        on = self.objects[obj_id]
        for k, v in kw.items():
            self.n.set_attr(on, k, v)

    def step_decide(self):
        self.n.set_attr(self.g, "waypoint", "")
        self.n.run_rules()
        a = self.s.node(self.g)["attrs"]
        return {"waypoint": a.get("waypoint") or "",
                "wp": (int(round(a.get("wp_r") or 0)), int(round(a.get("wp_c") or 0))),
                "seek_obj": a.get("seek_obj") or "",
                "explore_mode": float(a.get("explore_mode") or 0.0),
                "attributed_remote": float(a.get("attributed_remote") or 0.0),
                "attributed_obj": a.get("attributed_obj") or "",
                "act_on_confirmed": float(a.get("act_on_confirmed") or 0.0),
                "affect": a.get("affect") or ""}

    def read_posits(self):
        out = []
        for q in self.s.neighbours(self.g, "has_posit"):
            at = self.s.node(q)["attrs"]
            out.append({"obj_id": at.get("obj_id"), "status": at.get("status"),
                        "is_local": float(at.get("is_local") or 0.0)})
        return out

    def confirmed(self):
        return {p["obj_id"] for p in self.read_posits() if p["status"] == "confirmed"}


# ===========================================================================
# EXPERIMENT 2 — the ATTRIBUTION vignette (the HEADLINE). The agent has
# explored + interacted (given); it OBSERVES the interventional facts via the
# probe world-model and the rules produce the confirmed/refuted verdict.
# ===========================================================================
def run_attribution_vignette(truth, objects, arm):
    """One attribution vignette. `objects` are salient objects (already reached +
    interacted); the adapter OBSERVES each object's interventional facts by running
    the probe world-model, stamps them, and the rules decide the causal verdict."""
    pl = RemotePlanner(arm, objects, goal_rc=(0, 0))
    pl.set_game(known_option_tried=1.0, explore_mode=1.0)
    for o in objects:
        eff_act, eff_noop, passive = observe_intervention(truth, o["obj_id"])
        pl.mark_object(o["obj_id"], visited=1.0, interacted=1.0,
                       eff_act=eff_act, eff_noop=eff_noop, passive_cooccur=passive)
    pl.step_decide()
    conf = pl.confirmed()
    remote_objs = {o["obj_id"] for o in objects if o["is_local"] == 0}
    local_objs = {o["obj_id"] for o in objects if o["is_local"] == 1}
    a = pl.s.node(pl.g)["attrs"]
    return {"arm": arm, "confirmed": sorted(conf),
            "attributed_remote": float(a.get("attributed_remote") or 0.0),
            "attributed_obj": a.get("attributed_obj") or "",
            "confirmed_remote": sorted(conf & remote_objs),
            "confirmed_local": sorted(conf & local_objs)}


def correct_verdict(res, family, truth, objects):
    """Ground-truth correctness of the causal verdict.
       Family A (confounded remote): confirm the true remote cause AND not the local
         distractor -> attributed across space to exactly the true cause.
       Family B (coincidence): confirm NOTHING (refuse)."""
    true_causes = sorted(k for k, v in truth["controls"].items() if v)
    if family == "A":
        return (res["confirmed"] == true_causes
                and res["attributed_remote"] == 1.0
                and res["attributed_obj"] in true_causes)
    else:  # B: coincidence -> nothing should be confirmed
        return res["confirmed"] == []


# ===========================================================================
# EXPERIMENT 1 & 3 — the GRID episode (exhaustion -> explore -> intervene ->
# discover -> act -> pass). Reused for reach-cross (Exp1) and pass (Exp3).
# ===========================================================================
def _greedy_step(pos, target):
    r, c = pos; tr, tc = target
    if r != tr:
        return (r + (1 if tr > r else -1), c)
    if c != tc:
        return (r, c + (1 if tc > c else -1))
    return (r, c)


def _cycle_step(pos, step, H, W):
    dr, dc = _CYCLE[step % len(_CYCLE)]
    nxt = (pos[0] + dr, pos[1] + dc)
    if not (0 <= nxt[0] < H and 0 <= nxt[1] < W):
        return pos
    return nxt


def run_grid_episode(scn, arm, budget=120, trace=False):
    """Play one genuinely-REMOTE board with one arm. The transform provider is a
    REMOTE switch (no local station); B matches ONLY after the switch is OPERATED
    (committed) — which the rules choose only after CONFIRMING the remote link.

    Returns outcome incl. reached_cross (G-exhaustion), attributed_remote, and win
    (G-pass-via-remote)."""
    truth = scn["truth"]
    objects = scn["objects"]
    H, W = scn["H"], scn["W"]
    block = tuple(scn["block_rc"])
    cross_id = scn["remote_obj_id"]
    cross_rc = tuple(scn["remote_obj_rc"])

    pl = RemotePlanner(arm, objects, goal_rc=block)
    pos = tuple(scn["avatar_rc"])
    b_matches = False
    known_tried = False
    operated = set()
    reached_cross = False
    tr_log = []

    for step in range(budget):
        pl.set_game(symbol_matches_goal=1.0 if b_matches else 0.0,
                    known_option_tried=1.0 if known_tried else 0.0)
        dec = pl.step_decide()
        if trace:
            tr_log.append({"step": step, "pos": pos, "waypoint": dec["waypoint"],
                           "wp": dec["wp"], "explore_mode": dec["explore_mode"],
                           "attributed_remote": dec["attributed_remote"],
                           "b_matches": b_matches})
        wp = dec["waypoint"]

        if wp == "":
            # no rule chose a move (causal_prior after known-probe) -> blind cycle
            pos = _cycle_step(pos, step, H, W)
            continue

        if wp == "goal":
            # routing to the block: step toward it
            if pos == block:
                if b_matches:
                    return _out(arm, True, step, "passed", reached_cross, dec, pl, tr_log)
                # probe the block AS-IS -> observed: did NOT pass (known option fails).
                known_tried = True
                # the block-probe physically TOUCHES any object co-located with the
                # block (the local distractor) -> it is visited + interacted here, so
                # the only UN-VISITED salient thing left to explore is the remote switch.
                for o in objects:
                    if o["is_local"] == 1 and (o["r"], o["c"]) == block:
                        ea, en, pa = observe_intervention(truth, o["obj_id"])
                        pl.mark_object(o["obj_id"], visited=1.0, interacted=1.0,
                                       eff_act=ea, eff_noop=en, passive_cooccur=pa)
                # nudge off the block so we are not frozen on it
                pos = _cycle_step(pos, step, H, W)
                continue
            pos = _greedy_step(pos, block)
            continue

        if wp == "object":
            target = dec["wp"]
            if pos == tuple(target):
                # ARRIVED at a salient object.
                oid = dec["seek_obj"]
                if oid == cross_id:
                    reached_cross = True
                # PROBE (reversible interventional test): observe eff_act/eff_noop/passive
                eff_act, eff_noop, passive = observe_intervention(truth, oid)
                pl.mark_object(oid, visited=1.0, interacted=1.0,
                               eff_act=eff_act, eff_noop=eff_noop, passive_cooccur=passive)
                # COMMIT the operate ONLY when the rules are acting on a CONFIRMED
                # link (act_on_confirmed) — that is when the effect is applied to B.
                if dec["act_on_confirmed"] == 1.0 and oid not in operated:
                    if truth["controls"].get(oid, False):
                        b_matches = True     # the remote effect: B now matches
                    operated.add(oid)
                continue
            pos = _greedy_step(pos, target)
            continue

    return _out(arm, False, budget, "timeout", reached_cross, pl.step_decide(), pl, tr_log)


def _out(arm, win, steps, reason, reached_cross, dec, pl, tr_log):
    a = pl.s.node(pl.g)["attrs"]
    return {"arm": arm, "win": bool(win), "steps": steps, "reason": reason,
            "reached_cross": bool(reached_cross),
            "attributed_remote": float(a.get("attributed_remote") or 0.0),
            "attributed_obj": a.get("attributed_obj") or "",
            "confirmed": sorted(pl.confirmed()),
            "trace": tr_log}


# ===========================================================================
# SCENARIO GENERATION
# ===========================================================================
def make_attribution_scenario(rng, family, flavour="ls20"):
    """One attribution vignette scenario. Family A: a REMOTE cause (cross/lever) that
    truly controls B + a LOCAL distractor at B that only co-occurs. Family B: the same
    two objects but B changes SPONTANEOUSLY (neither controls it)."""
    remote_id = "cross" if flavour == "ls20" else "lever"
    local_id = "glow" if flavour == "ls20" else "torch"
    # place remote object far, local object at B's location (co-located)
    br, bc = int(rng.integers(2, 10)), int(rng.integers(2, 10))
    rr, rc = int(rng.integers(2, 10)), int(rng.integers(2, 10))
    objects = [
        {"obj_id": remote_id, "r": rr, "c": rc, "is_local": 0},
        {"obj_id": local_id, "r": br, "c": bc, "is_local": 1},
    ]
    if family == "A":
        truth = {"controls": {remote_id: True, local_id: False}, "spontaneous": False}
    else:  # B: coincidence
        truth = {"controls": {remote_id: False, local_id: False}, "spontaneous": True}
    return {"family": family, "flavour": flavour, "objects": objects, "truth": truth,
            "remote_obj_id": remote_id, "block_rc": (br, bc)}


def make_remote_board(rng, flavour="ls20", H=12, W=12):
    """One genuinely-REMOTE grid board: an avatar, a block/door B, a REMOTE switch
    (the transform provider — no local station), and a LOCAL distractor at B. B
    matches ONLY after the remote switch is OPERATED. Ground truth = Family A
    (the switch truly controls B; non-spontaneous)."""
    remote_id = "cross" if flavour == "ls20" else "lever"
    local_id = "glow" if flavour == "ls20" else "torch"

    def cell():
        return (int(rng.integers(H)), int(rng.integers(W)))

    while True:
        avatar, block, cross = cell(), cell(), cell()
        if len({avatar, block, cross}) == 3:
            break
    objects = [
        {"obj_id": remote_id, "r": cross[0], "c": cross[1], "is_local": 0},
        {"obj_id": local_id, "r": block[0], "c": block[1], "is_local": 1},
    ]
    truth = {"controls": {remote_id: True, local_id: False}, "spontaneous": False}
    return {"flavour": flavour, "H": H, "W": W, "avatar_rc": avatar, "block_rc": block,
            "remote_obj_id": remote_id, "remote_obj_rc": cross, "objects": objects,
            "truth": truth}
