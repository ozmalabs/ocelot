"""remote_causal_ground — RUNG 229000: OBSERVE-AND-GROUND remote causality — the
MECHANICAL world adapter + episode drivers.

THE CORRECTION (228 -> 229). 228 grounded the causal link from a probe WORLD-MODEL
that SIMULATED the act-vs-no-op counterfactual (a rewind — offline-only). Here the
link is GROUNDED FROM REAL OBSERVATION: the adapter perceives a remote-thing grid
BEFORE an interaction, applies the world physics, perceives it AFTER, and OBSERVES
the actual before->after change (a real array comparison — the same perception op
the live path runs on real frames). The no-op / negative evidence comes from the
NATURAL TIMELINE (real steps where the agent did NOT interact and the remote thing
did NOT change), NOT a simulated rewind.

ALL decisions live in the graph rules (domains/remote_causal_ground_seed.py). The
adapter does only:

  PERCEIVE  — hold the remote-thing grid; on each real step compare BEFORE vs AFTER
              and OBSERVE `remote_changed` (real diff) + the `effect_kind` (rotation
              if AFTER == rot90(BEFORE), else generic change). Write an Observation
              node {interact, remote_changed, cause_id, effect_kind} — the natural
              timeline as graph data.
  WORLD     — apply the physics: interacting a true cause (or a spontaneous drift)
              changes the remote grid. Pure world response; the RULE decides whether
              to GROUND.
  ACT       — read the rule-chosen waypoint and STEP toward it; OPERATE the object on
              arrival when the rules act on the grounded fact.

There is NO Python deciding the causal link, the grounding, or the move.

`truth`:  controls[obj_id] — does interacting this object rotate the remote thing?
          spontaneous      — does the remote thing rotate on its own, regardless?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from domains.remote_causal_ground_seed import RULES  # noqa: E402


# ===========================================================================
# THE REMOTE-THING PERCEPTION — a small grid whose before->after change is
# OBSERVED (a real array comparison), never asserted. This is the offline twin
# of the live real-frame onset diff.
# ===========================================================================
def _make_shape(rng):
    g = np.zeros((4, 4), dtype=np.int32)
    # an asymmetric shape so a 90-degree rotation is observable
    g[0, :3] = 1
    g[:2, 0] = 1
    g[3, 3] = rng.integers(0, 2)
    return g


def observe_change(before, after):
    """OBSERVE the before->after remote change (perception). Returns
    (remote_changed:0/1, effect_kind). `effect_kind` is OBSERVED, not asserted:
    'rotation' iff AFTER equals a 90-degree rotation of BEFORE, else 'change'."""
    if np.array_equal(before, after):
        return 0.0, "none"
    kind = "rotation" if np.array_equal(after, np.rot90(before)) else "change"
    return 1.0, kind


class GroundWorld:
    """The world whose remote-thing grid is OBSERVED before/after each step."""

    def __init__(self, rng, truth):
        self.rng = rng
        self.truth = truth
        self.remote = _make_shape(rng)

    def step(self, *, interact, obj_id):
        """One world step. Returns (before, after) grids of the remote thing. The
        remote thing rotates iff (interact AND obj_id truly controls it) OR the world
        drifts spontaneously. The adapter OBSERVES the diff — the world only responds."""
        before = self.remote.copy()
        rotate = False
        if interact and self.truth["controls"].get(obj_id, False):
            rotate = True
        if self.truth["spontaneous"]:
            rotate = True
        if rotate:
            self.remote = np.rot90(self.remote)
        return before, self.remote.copy()


# ===========================================================================
# THE PLANNER SUBSTRATE (rules install; the DECISION is graph-native)
# ===========================================================================
class GroundPlanner:
    def __init__(self, arm, objects, goal_rc=(0, 0)):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "ground_on": 1.0, "arm": arm, "symbol_matches_goal": 0.0,
            "waypoint": "", "wp_r": 0.0, "wp_c": 0.0,
            "goal_r": float(goal_rc[0]), "goal_c": float(goal_rc[1]),
            "seek_obj": "", "grounded": 0.0, "grounded_cause": "",
            "grounded_effect": "", "act_on_grounded": 0.0})
        p = self.s.add_node("Ping", {})
        self.n.add_edge_unchecked(self.g, "has_ping", p)
        self.objects = {}
        for o in objects:
            on = self.s.add_node("SalientObject", {
                "obj_id": o["obj_id"], "r": float(o["r"]), "c": float(o["c"]),
                "salient": 1.0, "visited": 0.0, "interacted": 0.0})
            self.n.add_edge_unchecked(self.g, "has_object", on)
            self.objects[o["obj_id"]] = on

    def set_game(self, **kw):
        for k, v in kw.items():
            self.n.set_attr(self.g, k, v)

    def add_observation(self, *, interact, remote_changed, cause_id, effect_kind):
        """MECHANICAL: write the OBSERVED per-step fact as an Observation node (the
        natural timeline as graph data)."""
        obs = self.s.add_node("Observation", {
            "interact": float(interact), "remote_changed": float(remote_changed),
            "cause_id": cause_id, "effect_kind": effect_kind})
        self.n.add_edge_unchecked(self.g, "has_obs", obs)
        return obs

    def step_decide(self):
        self.n.set_attr(self.g, "waypoint", "")
        self.n.run_rules()
        a = self.s.node(self.g)["attrs"]
        return {"waypoint": a.get("waypoint") or "",
                "wp": (int(round(a.get("wp_r") or 0)), int(round(a.get("wp_c") or 0))),
                "seek_obj": a.get("seek_obj") or "",
                "grounded": float(a.get("grounded") or 0.0),
                "grounded_cause": a.get("grounded_cause") or "",
                "grounded_effect": a.get("grounded_effect") or "",
                "act_on_grounded": float(a.get("act_on_grounded") or 0.0)}

    def facts(self):
        out = []
        for cf in self.s.neighbours(self.g, "has_causal_fact"):
            at = self.s.node(cf)["attrs"]
            out.append({"cause": at.get("cause"), "effect": at.get("effect"),
                        "status": at.get("status"), "source": at.get("source")})
        return out

    def causes_edges(self):
        """Read the `causes` edges (cause object -> fact) — the grounded relation."""
        out = []
        for oid, on in self.objects.items():
            for cf in self.s.neighbours(on, "causes"):
                at = self.s.node(cf)["attrs"]
                out.append((oid, at.get("effect")))
        return out


# ===========================================================================
# EXPERIMENT — OBSERVE-AND-GROUND vignette (the HEADLINE). The agent walks a
# NATURAL TIMELINE of real steps (interacting the object on some, not on
# others), OBSERVES the actual remote before->after each step, and the rules
# decide whether to GROUND the causal fact.
# ===========================================================================
def run_ground_vignette(rng, truth, objects, arm, timeline):
    """One observe-and-ground vignette.

    `timeline` is a list of (interact:bool, obj_id_or_None) real steps. Each step the
    world responds, the adapter OBSERVES the remote before->after change, writes an
    Observation, and the rules decide grounding. Returns the grounded facts + the
    fact-absent-before / present-after check."""
    pl = GroundPlanner(arm, objects)
    world = GroundWorld(rng, truth)
    grounded_before = len(pl.facts())
    for interact, obj_id in timeline:
        oid = obj_id if obj_id is not None else ""
        before, after = world.step(interact=interact, obj_id=oid)
        changed, kind = observe_change(before, after)
        # the 'blind' control never observes the effect (its perception is severed)
        if arm == "blind":
            changed, kind = 0.0, "none"
        cause_id = oid if interact else ""
        pl.add_observation(interact=1.0 if interact else 0.0,
                           remote_changed=changed, cause_id=cause_id, effect_kind=kind)
    pl.step_decide()
    facts = pl.facts()
    return {"arm": arm, "grounded_before": grounded_before, "facts": facts,
            "grounded_after": len(facts), "causes_edges": pl.causes_edges(),
            "grounded_flag": pl.step_decide()["grounded"]}


def correct_ground_verdict(res, family, truth):
    """Ground-truth correctness of the grounding verdict.
       Family A (true remote cause): ground EXACTLY the true cause -> rotation.
       Family B (spontaneous coincidence): ground NOTHING (refuse)."""
    true_causes = sorted(k for k, v in truth["controls"].items() if v)
    grounded_causes = sorted({f["cause"] for f in res["facts"]})
    if family == "A":
        return (grounded_causes == true_causes and res["grounded_after"] >= 1
                and all(f["effect"] == "rotation" for f in res["facts"]))
    else:  # B: spontaneous -> nothing should be grounded
        return res["facts"] == []


# ===========================================================================
# KNOWS-AND-ACTS episode — with the fact grounded, route to the cause, operate,
# pass; without it, cannot.
# ===========================================================================
def _greedy_step(pos, target):
    r, c = pos; tr, tc = target
    if r != tr:
        return (r + (1 if tr > r else -1), c)
    if c != tc:
        return (r, c + (1 if tc > c else -1))
    return (r, c)


def run_knows_and_acts_episode(rng, truth, objects, arm, timeline, block_rc, budget=80):
    """First OBSERVE-AND-GROUND over the natural timeline, THEN act on the grounded
    knowledge: read the grounded fact -> seek the cause -> operate it (obtain the
    effect: the remote thing matches) -> pass. Returns win + whether it grounded."""
    pl = GroundPlanner(arm, objects, goal_rc=block_rc)
    world = GroundWorld(rng, truth)
    # phase 1: the natural timeline (observe + ground)
    for interact, obj_id in timeline:
        oid = obj_id if obj_id is not None else ""
        before, after = world.step(interact=interact, obj_id=oid)
        changed, kind = observe_change(before, after)
        if arm == "blind":
            changed, kind = 0.0, "none"
        cause_id = oid if interact else ""
        pl.add_observation(interact=1.0 if interact else 0.0,
                           remote_changed=changed, cause_id=cause_id, effect_kind=kind)
    pl.step_decide()
    grounded = len(pl.facts()) >= 1
    # phase 2: act on the grounded knowledge
    obj_rc = {o["obj_id"]: (int(o["r"]), int(o["c"])) for o in objects}
    pos = tuple(rng.integers(0, 10, size=2).tolist())
    b_matches = False
    operated = set()
    for step in range(budget):
        pl.set_game(symbol_matches_goal=1.0 if b_matches else 0.0)
        dec = pl.step_decide()
        wp = dec["waypoint"]
        if wp == "":
            break  # no knowledge -> no move
        if wp == "goal":
            if pos == tuple(block_rc):
                if b_matches:
                    return {"arm": arm, "win": True, "grounded": grounded, "steps": step}
            pos = _greedy_step(pos, tuple(block_rc))
            continue
        if wp == "object":
            target = tuple(dec["wp"])
            if pos == target:
                oid = dec["seek_obj"]
                if dec["act_on_grounded"] == 1.0 and oid not in operated:
                    if truth["controls"].get(oid, False):
                        b_matches = True  # operating the grounded cause obtains the effect
                    operated.add(oid)
                continue
            pos = _greedy_step(pos, target)
            continue
    return {"arm": arm, "win": False, "grounded": grounded, "steps": budget}


# ===========================================================================
# SCENARIO GENERATION
# ===========================================================================
def make_scenario(rng, family, flavour="ls20"):
    """Family A: the cross truly rotates the remote thing (change ONLY on interact).
       Family B: the remote thing rotates SPONTANEOUSLY (coincidence — not the cross)."""
    cause_id = "cross" if flavour == "ls20" else "lever"
    objects = [{"obj_id": cause_id, "r": int(rng.integers(1, 9)), "c": int(rng.integers(1, 9))}]
    if family == "A":
        truth = {"controls": {cause_id: True}, "spontaneous": False}
    else:  # B: coincidence
        truth = {"controls": {cause_id: False}, "spontaneous": True}
    return {"family": family, "flavour": flavour, "objects": objects, "truth": truth,
            "cause_id": cause_id}


def natural_timeline(rng, cause_id, n_noint=3, n_int=1):
    """A natural timeline: several no-interaction steps (the no-op evidence) then a
    real interaction with the cause. Order shuffled so grounding does not depend on
    step order."""
    tl = [(False, None)] * n_noint + [(True, cause_id)] * n_int
    idx = rng.permutation(len(tl))
    return [tl[i] for i in idx]
