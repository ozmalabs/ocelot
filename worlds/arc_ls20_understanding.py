"""arc_ls20_understanding — RUNG 221000: the mechanical host adapter + episode
driver for the UNDERSTANDING-driven ls20 agent. Winning is a SIDE EFFECT of
understanding; it is LOGGED, never optimised.

ALL decisions live in the graph rules (seeds/ls20_understanding.json, built by
domains/ls20_understanding_seed.py). This adapter does ONLY mechanical I/O:

  PERCEIVE  — render the probe / the transformed probe / the goal form and SEE
              them through the 216000 pixel eye; RECOGNISE the transform a probed
              station applied (before->after) with the general 217000 sd-loop
              (recognise_required_key, reused verbatim). Stamp the recognised
              `observed_key` the rules read.
  TICK      — drive the phase machinery (pick -> route -> predict -> observe ->
              advance) so the rules' predict strictly precedes observe strictly
              precedes advance. Setting game.phase is mechanical tick scheduling.
  ACT       — read the rule-chosen waypoint off the graph and STEP the avatar one
              cell toward it (greedy Manhattan / quanta flood -- EXECUTION, not a
              decision).
  WORLD     — apply a station's transform to a fresh probe when the avatar reaches
              it (world physics); score WIN/LOSE at the goal by exact set equality
              (the oracle -- scoring only, never fed to a decision).
  MEASURE   — read the surprise (predicted vs observed) and the model accuracy
              (each station's hypothesis key vs the ground-truth transform, an
              ORACLE read for scoring only) each probe cycle.

The world reuses worlds/arc_ls20_scenario's corpus, transforms, and the
graph-native recogniser. No new model, no ls20-special recognition.
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
from domains.ls20_understanding_seed import RULES  # noqa: E402
from worlds.arc_ls20_scenario import (  # noqa: E402
    CORPUS, RECOLOUR_MAP, apply_transform, canonical_key, recognise_required_key,
    render_and_see, _normset, _greedy_step, _reachable,
)

# A single canonical chiral probe the agent brings to every station (a controlled
# test object): the 'L' tetromino, colour 11. Chiral (so rotations/reflections are
# unambiguously recognised) and in-palette. Its colour's recolour partner is 14.
PROBE_NAME = "L"
_probe_offs, _probe_colour = CORPUS[PROBE_NAME]
PROBE = [(r, c, _probe_colour) for (r, c) in _probe_offs]

# The full station transform vocabulary (the mechanic to be understood). Each is a
# ground-truth (family, param); the agent does NOT read this -- it learns the map.
_STATION_FAMILIES = [
    ("rotate", 1), ("rotate", 2), ("rotate", 3),
    ("reflect", "c"), ("reflect", "r"),
    ("recolour", {_probe_colour: RECOLOUR_MAP[_probe_colour]}),
]


def station_truth_key(fam, param):
    return canonical_key(fam, param)


def observe_station(fam, param):
    """The agent's controlled test: apply the station's transform to a FRESH probe
    and RECOGNISE the delta with the general sd-loop. Returns the recognised
    canonical key (graph-native recognition; None if refused)."""
    after = apply_transform(PROBE, fam, param)
    return recognise_required_key(PROBE, after)


class Understand:
    """Holds the game + station nodes + the ls20_understanding rules. The adapter
    stamps perception facts and drives the phase machinery; the rules decide."""

    _DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}

    def __init__(self, arm, stations, goal_rc, router="greedy", H=16, W=16, walls=()):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        self.inner = self.n
        self.agent = self.ag
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "understand_on": 1.0, "arm": arm, "phase": "idle",
            "probe_r": 0.0, "probe_c": 0.0, "observed_key": "", "predicted_key": "none",
            "req_key": "", "symbol_matches_goal": 0.0, "waypoint": "",
            "wp_r": 0.0, "wp_c": 0.0,
            "goal_r": float(goal_rc[0]), "goal_c": float(goal_rc[1])})
        p = self.s.add_node("Ping", {})
        self.n.add_edge_unchecked(self.g, "has_ping", p)
        self.stations = []
        self.truth = []          # ground-truth keys, ORACLE for scoring only
        for i, st in enumerate(stations):
            sn = self.s.add_node("Station", {"r": float(st["r"]), "c": float(st["c"]),
                                             "visits": 0.0, "visited": 0.0, "used": 0.0,
                                             "order": float(i)})
            self.n.add_edge_unchecked(self.g, "has_station", sn)
            self.stations.append(sn)
            self.truth.append(station_truth_key(st["family"], st["param"]))
        self.arm = arm
        self.router = router
        self.H, self.W = int(H), int(W)
        self.walls = set(tuple(w) for w in walls)
        if router == "quanta":
            self._setup_quanta()

    # ---- the WORLD advances to a new level (world op: fresh observances) ------
    def present_level(self, goal_rc):
        """The WORLD presents a new level: it INGESTS the level's observances onto
        the graph (the goal cell it perceives; the fresh physical state -- no station
        has yet transformed the new carried symbol -> used/visited == 0) and clears
        the agent's per-tick decision registers (waypoint/wp -- the scratch the rule
        overwrites each decide tick, the 218000 adapter's established pattern). It
        does NOT touch the agent's MODEL (the hypotheses persist -- that IS the
        reframe: understanding carries across levels) NOR the agent's attention (the
        `probing` edge is created and released by the agent's own pick/advance rules;
        a `level_start` tick lets the agent clear any stale attention itself)."""
        self.n.set_attr(self.g, "goal_r", float(goal_rc[0]))
        self.n.set_attr(self.g, "goal_c", float(goal_rc[1]))
        for k, v in (("symbol_matches_goal", 0.0), ("waypoint", ""), ("req_key", ""),
                     ("wp_r", 0.0), ("wp_c", 0.0), ("predicted_key", "none"),
                     ("observed_key", "")):
            self.n.set_attr(self.g, k, v)
        for sn in self.stations:                 # world physical state: fresh level
            self.n.set_attr(sn, "used", 0.0)
            self.n.set_attr(sn, "visited", 0.0)
        self._tick("level_start")                # agent clears its own stale attention

    # ---- phase tick (mechanical scheduling; rules decide within a phase) ------
    def _tick(self, phase):
        self.n.set_attr(self.g, "phase", phase)
        self.n.run_rules()

    def _read(self, key):
        return self.s.node(self.g)["attrs"].get(key)

    # ---- the curiosity pick (rule writes probe_r/probe_c + the probing edge) --
    def pick(self):
        self._tick("pick")
        return (int(round(self._read("probe_r") or 0)),
                int(round(self._read("probe_c") or 0)))

    def probing_station(self):
        for sn in self.s.neighbours(self.g, "probing"):
            return sn
        return None

    # ---- the model read-out (ORACLE-scored; never fed to a decision) ---------
    def model(self):
        """station index -> its current hypothesis key ('' if unmodelled)."""
        out = []
        for sn in self.stations:
            key = ""
            for h in self.s.neighbours(sn, "has_hyp"):
                key = self.s.node(h)["attrs"].get("key") or ""
                break
            out.append(key)
        return out

    def model_accuracy(self):
        m = self.model()
        correct = sum(1 for k, t in zip(m, self.truth) if k == t)
        return correct / len(self.truth) if self.truth else 0.0

    def confirmed_count(self):
        """# stations whose hypothesis was RE-predicted correctly (conf>=2) AND is
        the ground truth (an honest confirmed-understanding count)."""
        n = 0
        for sn, t in zip(self.stations, self.truth):
            for h in self.s.neighbours(sn, "has_hyp"):
                a = self.s.node(h)["attrs"]
                if (a.get("conf") or 0) >= 2.0 and (a.get("key") or "") == t:
                    n += 1
                break
        return n

    # ---- routing (EXECUTION only) --------------------------------------------
    def _setup_quanta(self):
        import json as _json, os as _os
        from substrate.seed_loader import engine_rules_only, SEED_DIR
        S, I = self.s, self.n
        for sid in ("navigation_modes", "affordance_basis", "quanta_navigation"):
            d = _json.load(open(_os.path.join(str(SEED_DIR), f"{sid}.json")))
            I.load_seed_manifest(engine_rules_only(d), self.ag)
        I.set_attr(self.g, "nav_repr", "quanta")
        I.set_attr(self.g, "slide", 1.0); I.set_attr(self.g, "ground", 4.0)
        self.passable = [1]
        for r in range(self.H):
            for c in range(self.W):
                v = 4.0 if (r, c) in self.walls else 1.0
                cid = S.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                                   "col": float(c), "value": v})
                I.add_edge_unchecked(self.g, "has_cell", cid)
        sr = S.add_node("Region", {"is_self": 1.0})
        I.add_edge_unchecked(self.g, "has_region", sr)
        for name, (dr, dc) in self._DISP.items():
            cr = S.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc),
                                                "dz": 0.0, "cname": name})
            I.add_edge_unchecked(sr, "responds_via", cr)
        self._goal_node = None

    def _route_step(self, pos, target):
        if self.router == "quanta":
            return self._quanta_step(pos, target)
        return _greedy_step(pos, target, self.walls)

    def _quanta_step(self, pos, target):
        from domains.spatial_sense import quanta_flood_step
        S, I = self.s, self.n
        if self._goal_node is None:
            self._goal_node = S.add_node("Goal", {"committed": 1.0, "world": 1.0})
            I.add_edge_unchecked(self.g, "committed_goal", self._goal_node)
        I.set_attr(self._goal_node, "pose", [int(target[0]), int(target[1])])
        I.set_attr(self.g, "chosen_action", "")
        quanta_flood_step(self, self.g, pos, (1, 1), self.passable, 1,
                          (self.H, self.W), focus=([0, 0], [self.H - 1, self.W - 1]))
        act = S.node(self.g)["attrs"].get("chosen_action") or ""
        dr, dc = self._DISP.get(act, (0, 0))
        nxt = (pos[0] + dr, pos[1] + dc)
        if not (0 <= nxt[0] < self.H and 0 <= nxt[1] < self.W) or nxt in self.walls:
            return pos
        return nxt

    def route_to(self, pos, target, budget=200):
        """Walk to `target`; returns (pos, steps). EXECUTION only."""
        steps = 0
        while pos != tuple(target) and steps < budget:
            nxt = self._route_step(pos, target)
            if nxt == pos:      # stalled (wall) -- give up this leg
                break
            pos = nxt; steps += 1
        return pos, steps


# ==========================================================================
# THE INVESTIGATION EPISODE (understand arm) — the HEADLINE convergence.
# ==========================================================================
def investigate(stations, avatar_rc, goal_rc, cycles, router="greedy",
                H=16, W=16, walls=(), record=True, observe_fn=None):
    """Run the curiosity-driven investigation for `cycles` probe cycles. Each
    cycle: the RULE picks the least-modelled station (curiosity); route there;
    PREDICT the effect from the model; OBSERVE the actual effect (sd-loop);
    the RESIDUAL mints/confirms/revises the hypothesis. Returns per-cycle
    surprise + model-accuracy curves + the confirmed-hypothesis count.

    NOTHING here optimises winning; the goal cell is not even routed to."""
    u = Understand("understand", stations, goal_rc, router, H, W, walls)
    pos = tuple(avatar_rc)
    surprise = []; accuracy = []; steps_total = 0
    for t in range(cycles):
        wp = u.pick()
        sn = u.probing_station()
        if sn is None:
            break               # nothing left to pick (should not happen)
        pos, st = u.route_to(pos, wp); steps_total += st
        # PREDICT (from the model) -- strictly before observing.
        u.n.set_attr(u.g, "predicted_key", "none")
        u._tick("predict")
        predicted = u._read("predicted_key")
        # OBSERVE (world physics + sd-loop recognition of THIS station's effect).
        i = u.stations.index(sn)
        fam, param = stations[i]["family"], stations[i]["param"]
        observed = ((observe_fn(fam, param) if observe_fn else observe_station(fam, param))
                    or "unrecognised")
        u.n.set_attr(u.g, "observed_key", observed)
        # RESIDUAL -> model update (mint / confirm / revise).
        u._tick("observe")
        # surprise = the residual the agent would have felt (predicted vs observed)
        surprise.append(0.0 if predicted == observed else 1.0)
        # ADVANCE: count the visit, release the probe.
        u._tick("advance")
        if record:
            accuracy.append(u.model_accuracy())
    return {
        "surprise": surprise,
        "accuracy": accuracy,
        "confirmed": u.confirmed_count(),
        "model": u.model(),
        "truth": u.truth,
        "steps": steps_total,
        "u": u,             # the trained substrate (for the deliver phase)
    }


# ==========================================================================
# THE DELIVER EPISODE (winning as a SIDE EFFECT) — understand arm.
# Uses the LEARNED model (a fresh substrate seeded with the learned hypotheses)
# to solve a level: recognise the required transform, look up the station the
# MODEL says applies it, route there, apply, deliver. Winning is logged.
# ==========================================================================
def make_deliver_substrate(stations, learned_model, router="greedy", H=16, W=16, walls=()):
    """Build ONE understand substrate with the LEARNED hypotheses seeded (they
    persist across levels -- the model transfers). Reused via reset_level."""
    u = Understand("understand", stations, (0, 0), router, H, W, walls)
    for sn, key in zip(u.stations, learned_model):
        if key:
            h = u.s.add_node("Hypothesis", {"key": key, "conf": 2.0, "kind": "station_effect"})
            u.n.add_edge_unchecked(sn, "has_hyp", h)
    return u


def deliver_level(stations, avatar_rc, goal_rc, symbol_cells, goal_cells,
                  learned_model, router="greedy", H=16, W=16, walls=(), budget=400,
                  u=None):
    """Solve one level using a PRE-LEARNED station->transform model. `learned_model`
    is [station_key or '' per station]. Returns win + steps + reason.

    The station is chosen by MODEL MATCH (uh_deliver_route: h.key == req_key), never
    by goal proximity -- winning is downstream of understanding. `u` (optional) is a
    pre-built substrate reused across levels (reset_level)."""
    if u is None:
        u = make_deliver_substrate(stations, learned_model, router, H, W, walls)
    u.present_level(goal_rc)
    req_key = recognise_required_key(symbol_cells, goal_cells)
    u.n.set_attr(u.g, "req_key", req_key or "")
    goal_norm = _normset(render_and_see(goal_cells))
    carried = list(symbol_cells)
    pos = tuple(avatar_rc); used = [False] * len(stations)
    for step in range(budget):
        matches = _normset(render_and_see(carried)) == goal_norm
        u.n.set_attr(u.g, "symbol_matches_goal", 1.0 if matches else 0.0)
        for sn, uf in zip(u.stations, used):
            u.n.set_attr(sn, "used", 1.0 if uf else 0.0)
        u.n.set_attr(u.g, "waypoint", "")
        u._tick("deliver")
        wp = u._read("waypoint") or ""
        wpc = (int(round(u._read("wp_r") or 0)), int(round(u._read("wp_c") or 0)))
        if pos == tuple(goal_rc) and wp == "goal":
            return {"win": bool(matches), "steps": step,
                    "reason": "delivered" if matches else "delivered_wrong",
                    "req_key": req_key}
        if wp == "":
            return {"win": False, "steps": step, "reason": "no_route", "req_key": req_key}
        pos, st = u.route_to(pos, wpc, budget=budget - step)
        if wp == "station" and pos == wpc:
            for i, sd in enumerate(stations):
                if not used[i] and pos == (int(sd["r"]), int(sd["c"])):
                    carried = apply_transform(carried, sd["family"], sd["param"])
                    used[i] = True
    return {"win": False, "steps": budget, "reason": "timeout", "req_key": req_key}


# ==========================================================================
# THE CONTROL (win_bound) — solve a level by optimising GOAL-REACH, NO model.
# It re-searches EVERY level (nearest-to-goal station first), up to `search_budget`
# station-applies. The labelled baseline the reframe is measured against.
# ==========================================================================
def win_bound_level(stations, avatar_rc, goal_rc, symbol_cells, goal_cells,
                    router="greedy", H=16, W=16, walls=(), search_budget=None,
                    budget=600, u=None):
    """win_bound: the FAIR strong control that optimises GOAL-REACH with NO
    persistent model. Each try: pick the untried station NEAREST THE GOAL
    (wb_probe_pick, the win-objective), route there, apply it to a FRESH copy of
    the symbol (backtracking -- a rational per-level searcher that does not corrupt
    state by composing wrong transforms), deliver if it now matches; else mark it
    tried and try the next-nearest, up to `search_budget` applies. Because it holds
    NO cross-level model it RE-SEARCHES every level from scratch.

    Returns win + steps + applies (the per-level re-search cost, re-paid each
    level -- the amortisation gap the understanding arm's model closes)."""
    if search_budget is None:
        search_budget = len(stations)
    if u is None:
        u = Understand("win_bound", stations, goal_rc, router, H, W, walls)
    u.present_level(goal_rc)
    goal_norm = _normset(render_and_see(goal_cells))
    pos = tuple(avatar_rc); applies = 0; steps_total = 0
    # already correct (identity level): deliver immediately.
    if _normset(render_and_see(symbol_cells)) == goal_norm:
        pos, st = u.route_to(pos, goal_rc, budget=budget); steps_total += st
        return {"win": pos == tuple(goal_rc), "steps": steps_total, "applies": 0,
                "reason": "delivered_identity"}
    while applies < search_budget:
        u.n.set_attr(u.g, "symbol_matches_goal", 0.0)
        u.n.set_attr(u.g, "waypoint", "")
        u._tick("pick")                       # nearest-to-goal untried station
        sn = u.probing_station()
        if sn is None:
            return {"win": False, "steps": steps_total, "applies": applies,
                    "reason": "no_station"}
        wpc = (int(round(u._read("wp_r") or 0)), int(round(u._read("wp_c") or 0)))
        pos, st = u.route_to(pos, wpc, budget=budget); steps_total += st
        if pos != wpc:                        # walled off -> skip this station
            u._tick("advance"); continue
        i = u.stations.index(sn)
        trial = apply_transform(list(symbol_cells), stations[i]["family"],
                                stations[i]["param"])
        applies += 1
        if _normset(render_and_see(trial)) == goal_norm:     # this station wins
            pos, st = u.route_to(pos, goal_rc, budget=budget); steps_total += st
            return {"win": pos == tuple(goal_rc), "steps": steps_total,
                    "applies": applies, "reason": "delivered"}
        u._tick("advance")                    # wrong station -> backtrack, next-nearest
    return {"win": False, "steps": steps_total, "applies": applies,
            "reason": "search_exhausted"}
