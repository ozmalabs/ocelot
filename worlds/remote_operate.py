"""remote_operate — RUNG 230000: PERFORM THE ACTION ON THE CROSS — the MECHANICAL
world adapter + episode drivers.

THE OWNER INSIGHT (229 -> 230). 229 REACHED and "interacted with" the cross but
observed 0 distal change, because "interacted" meant co-located / bumped — the agent
never issued the game's ACTION (use/select) ON the cross. Here the agent EXHAUSTS
THE ACTION SPACE at the reached object: it tries EVERY available action on it (the
movement actions AND the interact/use action), OBSERVES the real before->after, and
the rules DISCOVER which action actuates it (produces an observable remote change).
The elicited change flows into 229's rcg_ground (causes(object, effect)).

ALL decisions live in the graph rules (domains/remote_operate_seed.py for the
action-exhaustion + discover; domains/remote_causal_ground_seed.py for the grounding
+ pass). The adapter does only:

  ENUMERATE  — write the AVAILABLE game actions as GameAction{action_id, ordinal,
               is_movement, tried} nodes (is_movement is a mechanical property of the
               ARC-AGI-3 action set: ACTION1-4 moves, ACTION5/6 interact/click).
  ISSUE      — read the rule-chosen g.try_action and issue THAT action AT the object;
               the world responds (only the true operate action actuates).
  OBSERVE    — compare the remote thing BEFORE vs AFTER (a real array diff) and write
               an ActionOutcome{action_id, remote_changed, effect_kind} (for 230's
               discover) + a 229 Observation{interact, remote_changed, cause_id,
               effect_kind} (for 229's ground). All OBSERVED, never asserted.
  ACT        — once a fact is grounded, read the rule-chosen waypoint and STEP toward
               it; OPERATE the object on arrival; pass.

There is NO Python deciding the actuator, the discovery, the grounding, or the move.
The world's GROUND TRUTH (which action actuates) is randomized per scenario and
never read by the agent — the agent tries and reads the OBSERVED outcome.
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
from domains.remote_operate_seed import RULES as OP_RULES  # noqa: E402
from domains.remote_causal_ground_seed import RULES as GROUND_RULES  # noqa: E402


# The ARC-AGI-3 action set (the SAME contract the live env exposes). ACTION1-4 are
# directional moves; ACTION5 is interact/select/execute; ACTION6 is a coordinate
# click. is_movement is a mechanical property of the action, not a decision.
MOVEMENTS = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
INTERACTS = ["ACTION5", "ACTION6"]
ACTION_ORDINAL = {"ACTION1": 1, "ACTION2": 2, "ACTION3": 3, "ACTION4": 4,
                  "ACTION5": 5, "ACTION6": 6}


def _make_shape(rng):
    g = np.zeros((4, 4), dtype=np.int32)
    g[0, :3] = 1
    g[:2, 0] = 1
    g[3, 3] = rng.integers(0, 2)
    return g


def observe_change(before, after):
    """OBSERVE the before->after remote change (perception). 'rotation' iff AFTER
    equals a 90-degree rotation of BEFORE, else 'change'; 'none' if unchanged."""
    if np.array_equal(before, after):
        return 0.0, "none"
    kind = "rotation" if np.array_equal(after, np.rot90(before)) else "change"
    return 1.0, kind


class OperateWorld:
    """The remote-thing world. Only the TRUE operate action, issued AT the object,
    actuates the remote thing (Family A). Family B: no action actuates (inert /
    triggered elsewhere)."""

    def __init__(self, rng, operable, true_operate_action):
        self.rng = rng
        self.remote = _make_shape(rng)
        self.operable = operable                    # A: True, B: False
        self.true_op = true_operate_action          # a NON-movement action id, or None

    def issue(self, action_id, at_object):
        before = self.remote.copy()
        if at_object and self.operable and action_id == self.true_op:
            self.remote = np.rot90(self.remote)
        return before, self.remote.copy()


class OperatePlanner:
    """The composed 230+229 substrate. The DECISION is graph-native (both rule sets
    on one Game node: op_policy drives 230; arm='observe' drives 229)."""

    def __init__(self, op_policy, actions, object_id="cross", obj_rc=(5, 5), goal_rc=(0, 0)):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in OP_RULES:
            self.n.add_rule(r)
        for r in GROUND_RULES:
            self.n.add_rule(r)
        self.object_id = object_id
        self.g = self.s.add_node("Game", {
            # 230 flags
            "operate_on": 1.0, "op_policy": op_policy, "at_object": 0.0,
            "discovered": 0.0, "try_action": "", "try_is_movement": 0.0,
            "try_ordinal": 0.0, "object_id": object_id,
            "operate_action": "", "discovered_is_movement": 0.0, "discovered_effect": "",
            # 229 flags (grounding + pass) on the SAME node
            "ground_on": 1.0, "arm": "observe", "symbol_matches_goal": 0.0,
            "waypoint": "", "wp_r": 0.0, "wp_c": 0.0,
            "goal_r": float(goal_rc[0]), "goal_c": float(goal_rc[1]),
            "seek_obj": "", "grounded": 0.0, "grounded_cause": "", "grounded_effect": "",
            "act_on_grounded": 0.0})
        p = self.s.add_node("Ping", {})
        self.n.add_edge_unchecked(self.g, "has_ping", p)
        # the reached salient object (the cross)
        self.o = self.s.add_node("SalientObject", {
            "obj_id": object_id, "r": float(obj_rc[0]), "c": float(obj_rc[1]),
            "salient": 1.0, "visited": 1.0, "interacted": 0.0})
        self.n.add_edge_unchecked(self.g, "has_object", self.o)
        # ENUMERATE the available actions as GameAction nodes (mechanical).
        self.actions = {}
        for aid in actions:
            an = self.s.add_node("GameAction", {
                "action_id": aid, "ordinal": float(ACTION_ORDINAL[aid]),
                "is_movement": 1.0 if aid in MOVEMENTS else 0.0, "tried": 0.0})
            self.n.add_edge_unchecked(self.g, "has_action", an)
            self.actions[aid] = an

    def set_game(self, **kw):
        for k, v in kw.items():
            self.n.set_attr(self.g, k, v)

    def get(self, k):
        return self.s.node(self.g)["attrs"].get(k)

    def add_outcome(self, *, action_id, remote_changed, effect_kind):
        oc = self.s.add_node("ActionOutcome", {
            "action_id": action_id, "remote_changed": float(remote_changed),
            "effect_kind": effect_kind})
        self.n.add_edge_unchecked(self.g, "has_outcome", oc)
        return oc

    def add_observation(self, *, interact, remote_changed, cause_id, effect_kind):
        obs = self.s.add_node("Observation", {
            "interact": float(interact), "remote_changed": float(remote_changed),
            "cause_id": cause_id, "effect_kind": effect_kind})
        self.n.add_edge_unchecked(self.g, "has_obs", obs)
        return obs

    def run(self):
        self.n.run_rules()

    def facts(self):
        out = []
        for cf in self.s.neighbours(self.g, "has_causal_fact"):
            at = self.s.node(cf)["attrs"]
            out.append({"cause": at.get("cause"), "effect": at.get("effect"),
                        "status": at.get("status"), "source": at.get("source")})
        return out

    def operates_edges(self):
        """Read the discovered Operates node(s): (action, object, effect)."""
        out = []
        for op in self.s.neighbours(self.g, "has_operates"):
            at = self.s.node(op)["attrs"]
            out.append({"action": at.get("action"), "object": at.get("object"),
                        "effect": at.get("effect")})
        return out


# ===========================================================================
# THE EXHAUSTION DRIVE — at the reached object, exhaust the ACTION space. The
# adapter issues the RULE-chosen action, observes, writes the outcome + the 229
# observation, and re-runs the rules (which discover + ground). NO Python decision.
# ===========================================================================
def _natural_timeline(pl, n_noint=3):
    """Write a clean natural timeline (real steps, no interaction, no change) BEFORE
    reaching the object — the negative evidence 229's rcg_ground reads. All OBSERVED."""
    for _ in range(n_noint):
        pl.add_observation(interact=0.0, remote_changed=0.0, cause_id="", effect_kind="none")


def exhaust_action_space(pl, world, budget=12):
    """At the object: run the rules to pick the next action to try, issue it AT the
    object, OBSERVE the real before->after, write the outcome + observation, re-run
    the rules (230 discovers, 229 grounds). Returns the per-step trace."""
    pl.set_game(at_object=1.0)
    issued = []           # (action_id, is_movement, remote_changed)
    for _ in range(budget):
        pl.set_game(try_action="")
        pl.run()                              # 230 picks the next untried action
        ta = pl.get("try_action") or ""
        if ta == "":
            break                             # action space exhausted (or discovered)
        is_move = pl.get("try_is_movement")
        # ISSUE the rule-chosen action AT the object; the world responds.
        before, after = world.issue(ta, at_object=True)
        changed, kind = observe_change(before, after)
        # OBSERVE: write the action outcome (for discover) + the 229 observation.
        pl.add_outcome(action_id=ta, remote_changed=changed, effect_kind=kind)
        pl.add_observation(interact=1.0, remote_changed=changed,
                           cause_id=pl.object_id, effect_kind=kind)
        # MECHANICAL bookkeeping: mark the rule-chosen action as issued so the rule
        # advances to the next untried action on the following step (the DECISION of
        # WHICH action is the rule's; this only records that it was issued).
        pl.n.set_attr(pl.actions[ta], "tried", 1.0)
        pl.run()                              # 230 discovers; 229 grounds
        issued.append((ta, float(is_move or 0.0), changed))
        if pl.get("discovered") == 1.0:
            break                             # discovered the operate action -> stop
    return issued


def run_operate_vignette(rng, family, op_policy, seed_actions):
    """One exhaust-actions vignette. Family A: exactly one NON-movement action
    actuates the object (randomized). Family B: no action actuates. Returns the
    discovered operate action, the grounded facts, and the issued-action trace."""
    true_op = None
    operable = (family == "A")
    if operable:
        true_op = INTERACTS[int(rng.integers(0, len(INTERACTS)))]  # randomized actuator
    pl = OperatePlanner(op_policy, seed_actions)
    world = OperateWorld(rng, operable, true_op)
    _natural_timeline(pl)
    issued = exhaust_action_space(pl, world)
    return {
        "family": family, "op_policy": op_policy, "true_operate_action": true_op,
        "discovered": pl.get("discovered") == 1.0,
        "operate_action": pl.get("operate_action") or "",
        "discovered_is_movement": pl.get("discovered_is_movement"),
        "operates_edges": pl.operates_edges(),
        "grounded": pl.get("grounded") == 1.0,
        "facts": pl.facts(),
        "issued": issued,
        "issued_a_non_movement": any(m == 0.0 for (_, m, _) in issued),
        "issued_actions": [a for (a, _, _) in issued],
    }


def correct_discover_verdict(res, family):
    """Family A: discover EXACTLY the true operate action. Family B: discover NOTHING."""
    if family == "A":
        return (res["discovered"] and res["operate_action"] == res["true_operate_action"]
                and res["discovered_is_movement"] == 0.0)
    return (not res["discovered"]) and res["operates_edges"] == []


def correct_ground_verdict(res, family):
    """Family A: ground the causal fact. Family B: ground NOTHING."""
    if family == "A":
        return res["grounded"] and any(f["status"] == "grounded" for f in res["facts"])
    return res["facts"] == []


# ===========================================================================
# THE PASS DRIVE — with the fact grounded during exhaustion, act on knowing it:
# route to the object, operate, obtain the effect, pass. Without grounding, cannot.
# ===========================================================================
def _greedy_step(pos, target):
    r, c = pos; tr, tc = target
    if r != tr:
        return (r + (1 if tr > r else -1), c)
    if c != tc:
        return (r, c + (1 if tc > c else -1))
    return (r, c)


def run_operate_pass_episode(rng, op_policy, seed_actions, obj_rc, block_rc, budget=80):
    """Exhaust the action space at the object (ground the fact), THEN act on the
    grounded knowledge: read the fact -> seek the object -> operate -> obtain the
    effect -> pass. Family A (operable). Returns win + grounded + discovered."""
    true_op = INTERACTS[int(rng.integers(0, len(INTERACTS)))]
    pl = OperatePlanner(op_policy, seed_actions, obj_rc=obj_rc, goal_rc=block_rc)
    world = OperateWorld(rng, True, true_op)
    _natural_timeline(pl)
    exhaust_action_space(pl, world)
    grounded = pl.get("grounded") == 1.0
    discovered = pl.get("discovered") == 1.0
    # act on the grounded knowledge (229's knows-and-acts + pass, reused unchanged)
    pos = tuple(rng.integers(0, 10, size=2).tolist())
    b_matches = False
    operated = set()
    for step in range(budget):
        pl.set_game(symbol_matches_goal=1.0 if b_matches else 0.0)
        pl.set_game(waypoint="")
        pl.run()
        wp = pl.get("waypoint") or ""
        if wp == "":
            break                     # no grounded knowledge -> no move
        if wp == "goal":
            if pos == tuple(block_rc) and b_matches:
                return {"op_policy": op_policy, "win": True, "grounded": grounded,
                        "discovered": discovered, "steps": step}
            pos = _greedy_step(pos, tuple(block_rc))
            continue
        if wp == "object":
            target = (int(round(pl.get("wp_r"))), int(round(pl.get("wp_c"))))
            if pos == target:
                oid = pl.get("seek_obj")
                if pl.get("act_on_grounded") == 1.0 and oid not in operated:
                    b_matches = True   # operating the grounded (operable) object obtains the effect
                    operated.add(oid)
                continue
            pos = _greedy_step(pos, target)
            continue
    return {"op_policy": op_policy, "win": False, "grounded": grounded,
            "discovered": discovered, "steps": budget}


# ===========================================================================
# SCENARIO GENERATION
# ===========================================================================
def full_action_space():
    """The full available action set: 4 movements + 2 interact/click actions."""
    return MOVEMENTS + INTERACTS


def make_scenario(rng, family):
    obj_rc = (int(rng.integers(1, 9)), int(rng.integers(1, 9)))
    return {"family": family, "obj_rc": obj_rc, "actions": full_action_space()}
