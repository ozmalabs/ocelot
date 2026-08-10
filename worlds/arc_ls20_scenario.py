"""arc_ls20_scenario — RUNG 218000: an ls20-SHAPED planning/execution scenario.

Closes the ls20 loop see -> understand -> DO on offline ls20-shaped scenarios
(mechanism proven; live-ls20 benchmark value needs ARC_API_KEY, absent — the
named frontier, exactly as 216000/217000). This module is the MECHANICAL world
adapter + the episode driver; ALL planning DECISIONS live in the graph rules
(domains/ls20_planning_seed.py). The adapter does only:

  PERCEIVE  — render the carried symbol + the goal form and SEE them through the
              216000 pixel eye (recover_grid_from_render); write the perceptual
              facts the rules read (symbol_matches_goal by integer-native
              normalised set-equality; which stations exist / are used; the
              required-transform key the graph-native 217000 sd-loop recognised).
  ACT       — read the rule-chosen waypoint off the graph and STEP the avatar one
              cell toward it (greedy Manhattan — routing EXECUTION, the analogue
              of slide_flood/hop_descend_gradient, not a planning decision).
  WORLD     — apply a station's transform to the carried symbol when the avatar is
              on it (the ls20 mechanic: "the symbol must go through various
              transformations"); score WIN/LOSE at the goal by exact set equality
              (the oracle). Pure world physics.

There is NO Python `if goal_reached` / path-search selecting the agent's move: the
waypoint is written by the rules; the step is geometry toward it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc import (  # noqa: E402
    _render_screen, recover_grid_from_render, cells_to_signature, SHAPE_DIM_TYPES,
)
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from domains.ls20_planning_seed import RULES  # noqa: E402

DT = SHAPE_DIM_TYPES
BG = 0

# ---- the ls20-shaped symbol corpus (chiral polyominoes; real ls20 palette) ---
CORPUS = {
    "F": ([(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)], 9),
    "L": ([(0, 0), (1, 0), (2, 0), (2, 1)], 11),
    "S": ([(0, 1), (1, 1), (2, 0), (2, 1), (3, 0)], 8),
    "Y": ([(0, 1), (1, 0), (1, 1), (2, 1), (3, 1)], 14),
    "P": ([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)], 12),
    "G": ([(0, 0), (1, 0), (2, 0), (2, 1), (0, 2), (0, 1)], 6),
}
RECOLOUR_MAP = {9: 8, 11: 14, 8: 9, 14: 11, 12: 6, 6: 12}


# ---- transforms (world physics; ground truth by construction) ----------------
def _reposition(cells, margin=0):
    mr = min(r for r, c, v in cells); mc = min(c for r, c, v in cells)
    return [(r - mr + margin, c - mc + margin, v) for (r, c, v) in cells]


def apply_transform(cells, family, param):
    """The ls20 mechanic: transform the carried symbol's (r,c,v) cells."""
    if family == "rotate":
        out = list(cells)
        for _ in range(int(param)):
            out = [(c, -r, v) for (r, c, v) in out]
        return _reposition(out)
    if family == "reflect":
        if param == "c":
            return _reposition([(r, -c, v) for (r, c, v) in cells])
        return _reposition([(-r, c, v) for (r, c, v) in cells])
    if family == "recolour":
        return _reposition([(r, c, param.get(v, v)) for (r, c, v) in cells])
    raise ValueError(family)


def canonical_key(family, param):
    """The transform's canonical key — the token stations and the recognised
    required-transform are matched on (a categorical sign, integer-native)."""
    if family == "rotate":
        return f"rot90:{int(param)}"
    if family == "reflect":
        return f"refl:{param}"
    if family == "recolour":
        pairs = sorted(f"v{a}>v{b}" for a, b in param.items() if a != b)
        return "recolour:" + ",".join(pairs)
    return "other"


# ---- seeing (216000 pixel eye) -----------------------------------------------
def render_and_see(cells, canvas=20):
    g = [[BG] * canvas for _ in range(canvas)]
    for (r, c, v) in _reposition(cells):
        if 0 <= r < canvas and 0 <= c < canvas:
            g[r][c] = int(v)
    screen = _render_screen(g, canvas, canvas).astype(np.uint8)
    seen = np.asarray(recover_grid_from_render(screen), dtype=np.int32)
    out = []
    for r in range(seen.shape[0]):
        for c in range(seen.shape[1]):
            if int(seen[r, c]) != BG:
                out.append((r, c, int(seen[r, c])))
    return out


def _normset(cells):
    if not cells:
        return frozenset()
    mr = min(r for r, c, v in cells); mc = min(c for r, c, v in cells)
    return frozenset((r - mr, c - mc, v) for r, c, v in cells)


# ---- the graph-native recogniser (217000 sd-loop) ----------------------------
def recognise_required_key(symbol_cells, goal_cells, _see=render_and_see):
    """Recognise the transform relating the SEEN symbol to the SEEN goal form via
    the GENERAL sd-loop (TransformDecode/DimInfer) — the same op 217000 measured.
    Graph-native recognition; returns the canonical key, or None if not recognised
    (refused) or an identity/other verdict. NOTHING ls20-specific.

    `_see` is the seeing function (default: the clean 216000 pixel eye). RUNG
    221000 passes a NOISE-injecting seer to measure convergence under perceptual
    degradation (the 219000 sweep); the default keeps every existing caller
    byte-identical."""
    base_sig = cells_to_signature(_see(symbol_cells))
    goal_sig = cells_to_signature(_see(goal_cells))
    # Pure-function memo keyed on the SEEN signatures (the recognition is a
    # deterministic function of them). Collapses the many-episode measure to a few
    # boots — clean observations repeat exactly; sub-threshold noise recovers the
    # same grid. Output-identical, so every existing caller is byte-unchanged.
    _ck = (tuple(tuple(r) for r in base_sig), tuple(tuple(r) for r in goal_sig))
    if _ck in _RECOG_MEMO:
        return _RECOG_MEMO[_ck]
    val = _recognise_sigs(base_sig, goal_sig)
    _RECOG_MEMO[_ck] = val
    return val


_RECOG_MEMO = {}


def _recognise_sigs(base_sig, goal_sig):
    """The boot + sd-loop recognition core, a pure function of the two SEEN
    signatures (memoised by recognise_required_key). Unchanged from the pre-221000
    body except for being factored out of the caller."""
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.add_node("ShapeSignature", {"name": "sym", "signature": json.dumps(base_sig),
                                  "kind": "faculty", "faculty": "sym", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal_sig, "key": ["probe"],
                                     "status": "decoded", "residual": goal_sig,
                                     "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    if at.get("status") != "recognized_transformed" or at.get("covered_by") != "sym":
        return None
    for n in s.neighbours(obs, "has_transform"):
        t = s.node(n)["attrs"]
        gen = t.get("generator")
        if gen == "rotation90":
            return f"rot90:{int(t.get('k') or 0)}"
        if gen == "reflection_r":
            return "refl:r"
        if gen == "reflection_c":
            return "refl:c"
        kinds = {tr.get("kind") for tr in (t.get("transforms") or [])}
        if "subst" in kinds:
            pairs = []
            for tr in t.get("transforms") or []:
                if tr.get("kind") == "subst":
                    for a, b in (tr.get("delta") or []):
                        pairs.append(f"{a}>{b}")
            return "recolour:" + ",".join(sorted(pairs))
        if kinds and kinds <= {"shift"}:
            return "translate"
    return None


# ---- the planner substrate (rules install; the DECISION is graph-native) -----
class Planner:
    """Holds the game + station nodes + the ls20_planning rules; each step the
    adapter stamps perception facts and run_rules() writes the waypoint."""

    def __init__(self, arm, stations, goal_rc):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        self.inner = self.n      # quanta_flood_step(agent,...) reads agent.inner / agent.s / agent.agent
        self.agent = self.ag
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {"plan_on": 1.0, "arm": arm,
                                          "symbol_matches_goal": 0.0,
                                          "any_station_used": 0.0, "req_key": "",
                                          "waypoint": "", "wp_r": 0.0, "wp_c": 0.0,
                                          "goal_r": float(goal_rc[0]), "goal_c": float(goal_rc[1])})
        p = self.s.add_node("Ping", {})
        self.n.add_edge_unchecked(self.g, "has_ping", p)
        self.stations = []
        for i, st in enumerate(stations):
            sn = self.s.add_node("Station", {"key": st["key"], "r": float(st["r"]),
                                             "c": float(st["c"]), "used": 0.0,
                                             "order": float(i)})
            self.n.add_edge_unchecked(self.g, "has_station", sn)
            self.stations.append(sn)

    def step_decide(self, matches, any_used, req_key, used_flags):
        self.n.set_attr(self.g, "symbol_matches_goal", 1.0 if matches else 0.0)
        self.n.set_attr(self.g, "any_station_used", 1.0 if any_used else 0.0)
        self.n.set_attr(self.g, "req_key", req_key or "")
        self.n.set_attr(self.g, "waypoint", "")
        for sn, uf in zip(self.stations, used_flags):
            self.n.set_attr(sn, "used", 1.0 if uf else 0.0)
        self.n.run_rules()
        a = self.s.node(self.g)["attrs"]
        return {"waypoint": a.get("waypoint") or "",
                "wp": (int(round(a.get("wp_r") or 0)), int(round(a.get("wp_c") or 0))),
                "affect": a.get("affect") or "", "salient": a.get("salient_mismatch") or 0.0}

    # ---- RUNG 220000: the quanta ROUTER (execution only; DECISIONS untouched) ----
    _DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1), "Select": (0, 0)}

    def setup_quanta(self, walls, H, W):
        """Wire the SAME map machinery the maze/Doom use into this planner substrate
        (mechanical world-adapter DATA, once per episode): load the general nav seed
        closure (navigation_modes + affordance_basis + quanta_navigation), select
        quanta mode, STAMP the whole grid as a `has_cell` occupancy belief (161000
        format: wall cells = value 4, floor = value 1; a COMPLETE belief -> zero
        frontier quanta), and declare the 4-move Control basis on an is_self Region
        (the qf hop rules Dot-pick the action against this chain — N-dim, no hardcoded
        directions). No ls20-special routing: this is the identical setup as
        scripts/maze_run.setup_quanta, driven by pose-lists + a Control basis."""
        import json as _json, os as _os
        from substrate.seed_loader import engine_rules_only, SEED_DIR
        S, I = self.s, self.n
        for sid in ("navigation_modes", "affordance_basis", "quanta_navigation"):
            d = _json.load(open(_os.path.join(str(SEED_DIR), f"{sid}.json")))
            I.load_seed_manifest(engine_rules_only(d), self.ag)
        I.set_attr(self.g, "nav_repr", "quanta")
        I.set_attr(self.g, "slide", 1.0); I.set_attr(self.g, "ground", 4.0)
        self.H, self.W = int(H), int(W)
        self.walls = set(tuple(w) for w in walls)
        self.passable = [1]                     # floor is passable; the wall value 4 is absent -> impassable
        for r in range(self.H):
            for c in range(self.W):
                v = float(_WALL_V) if (r, c) in self.walls else 1.0
                cid = S.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                                   "col": float(c), "value": v})
                I.add_edge_unchecked(self.g, "has_cell", cid)
        sr = S.add_node("Region", {"is_self": 1.0})
        I.add_edge_unchecked(self.g, "has_region", sr)
        for name, (dr, dc) in self._DISP.items():
            if name == "Select":
                continue
            cr = S.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc),
                                                "dz": 0.0, "cname": name})
            I.add_edge_unchecked(sr, "responds_via", cr)
        self._goal_node = None

    def _reflect_goal(self, wp):
        """Mechanical: the rule-written waypoint (wp_r/wp_c) -> a committed_goal{world:1,
        pose} the qf flood roots on. The coords are already graph attrs; the adapter only
        reflects them onto the goal node the router reads (no decision)."""
        S, I = self.s, self.n
        if self._goal_node is None:
            self._goal_node = S.add_node("Goal", {"committed": 1.0, "world": 1.0})
            I.add_edge_unchecked(self.g, "committed_goal", self._goal_node)
        I.set_attr(self._goal_node, "pose", [int(wp[0]), int(wp[1])])

    def quanta_route_step(self, pos, wp):
        """ONE quanta-routed step toward the rule-chosen waypoint: reflect the waypoint
        onto the world==1 goal, fire the shared quanta_flood_step (space_quantize +
        qf_* Bellman/portal flood), read the qf-chosen action off the game, and apply it
        with wall collision. The ONLY decision is the qf_* rules' `chosen_action`; this
        moves the avatar by it (a wall-blocked move is refused -> stall)."""
        from domains.spatial_sense import quanta_flood_step
        S, I = self.s, self.n
        self._reflect_goal(wp)
        I.set_attr(self.g, "chosen_action", "")
        quanta_flood_step(self, self.g, pos, (1, 1), self.passable, 1,
                          (self.H, self.W), focus=([0, 0], [self.H - 1, self.W - 1]))
        act = S.node(self.g)["attrs"].get("chosen_action") or ""
        dr, dc = self._DISP.get(act, (0, 0))
        nxt = (pos[0] + dr, pos[1] + dc)
        if not (0 <= nxt[0] < self.H and 0 <= nxt[1] < self.W) or nxt in self.walls:
            return pos          # collision / off-grid: refused -> stall (as greedy stalls)
        return nxt


def _greedy_step(pos, target, walls=None):
    """Row-first Manhattan step toward `target`. With `walls` (a set of (r,c) wall
    cells — the RUNG 220000 addition), a step INTO a wall is REFUSED: the avatar
    stays put (stalls). This is world collision physics, not a planning decision —
    the analogue of a maze bump. On an open layout (walls is None/empty) it is
    byte-identical to the pre-220000 stepper."""
    r, c = pos; tr, tc = target
    if r != tr:
        nxt = (r + (1 if tr > r else -1), c)
    elif c != tc:
        nxt = (r, c + (1 if tc > c else -1))
    else:
        return (r, c)
    if walls and nxt in walls:
        return (r, c)   # collision: refused -> stall
    return nxt


# ---- walls (RUNG 220000) -----------------------------------------------------
_WALL_V = 4   # the real ls20 palette wall value ("dark-grey field/walls", worlds/arc.py)


def _reachable(avatar, targets, walls, H, W):
    """4-connected BFS over non-wall cells: True iff EVERY target is reachable from
    the avatar. Generator-side world construction (admissible adapter I/O — like the
    existing _greedy_path rejection check), NOT an agent path-search: it only VALIDATES
    that a walled layout is solvable; the agent's own routing is the graph qf_* flood."""
    from collections import deque
    seen = {tuple(avatar)}; dq = deque([tuple(avatar)])
    while dq:
        r, c = dq.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in walls and (nr, nc) not in seen:
                seen.add((nr, nc)); dq.append((nr, nc))
    return all(tuple(t) in seen for t in targets)


# ---- the episode (one arm on one scenario) -----------------------------------
def run_episode(scn, arm, budget=200, trace=False, router="greedy"):
    """Play one scenario with one policy arm. Returns an outcome dict. The ONLY
    action-selection is: read the rule-chosen waypoint, step toward it.

    `router` selects EXECUTION only (the 218000 DECISION rules are untouched):
      "greedy" — row-first Manhattan (default; byte-identical to pre-220000, plus
                 wall collision when the scenario carries walls).
      "quanta" — RUNG 220000: route the rule-chosen waypoint with the shared
                 space_quantize + qf_* Bellman/portal flood over a stamped
                 `has_cell` belief. Same nav machinery as maze/Doom; routes around
                 walls the greedy stepper stalls on."""
    goal_seen = render_and_see(scn["goal_cells"])
    goal_norm = _normset(goal_seen)
    req_key = recognise_required_key(scn["symbol_cells"], scn["goal_cells"])
    planner = Planner(arm, scn["stations"], scn["goal_rc"])
    walls = set(tuple(w) for w in scn.get("walls", ()))
    if router == "quanta":
        planner.setup_quanta(walls, scn.get("H", 16), scn.get("W", 16))

    carried = _reposition(scn["symbol_cells"])
    pos = tuple(scn["avatar_rc"])
    used = [False] * len(scn["stations"])
    tr_log = []
    for step in range(budget):
        matches = _normset(render_and_see(carried)) == goal_norm
        dec = planner.step_decide(matches, any(used), req_key, used)
        if trace:
            tr_log.append({"step": step, "pos": pos, "matches": bool(matches),
                           "waypoint": dec["waypoint"], "wp": dec["wp"],
                           "affect": dec["affect"], "req_key": req_key})
        # terminal: at the goal cell -> deliver + score (oracle exact set equality)
        if pos == tuple(scn["goal_rc"]) and dec["waypoint"] == "goal":
            win = matches
            return {"arm": arm, "win": bool(win), "steps": step,
                    "reason": "delivered" if win else "delivered_wrong",
                    "req_key": req_key, "trace": tr_log}
        if dec["waypoint"] == "":
            return {"arm": arm, "win": False, "steps": step, "reason": "no_waypoint",
                    "req_key": req_key, "trace": tr_log}
        pos = (planner.quanta_route_step(pos, dec["wp"]) if router == "quanta"
               else _greedy_step(pos, dec["wp"], walls))
        # world physics: a station transforms the carried symbol when the avatar
        # ARRIVES at it as the chosen destination (deliberate "use", keyed on the
        # rule's waypoint — never an en-route accident). The world responds to the
        # agent's chosen destination; it does not select the move.
        if dec["waypoint"] == "station" and pos == dec["wp"]:
            for i, st in enumerate(scn["stations"]):
                if not used[i] and pos == (st["r"], st["c"]):
                    carried = apply_transform(carried, st["family"], st["param"])
                    used[i] = True
    return {"arm": arm, "win": False, "steps": budget, "reason": "timeout",
            "req_key": req_key, "trace": tr_log}


# ---- scenario generation -----------------------------------------------------
_FAMILIES = [("rotate", 1), ("rotate", 2), ("rotate", 3),
             ("reflect", "c"), ("reflect", "r"), ("recolour", "map")]


def _greedy_path(start, goal):
    """The full goal-blind trajectory (row-first greedy) — used to REJECT layouts
    where a straight-to-goal run would accidentally step on a station."""
    pos = tuple(start); cells = {pos}
    for _ in range(200):
        if pos == tuple(goal):
            break
        pos = _greedy_step(pos, goal); cells.add(pos)
    return cells


def make_scenario(rng, H=16, W=16, n_stations=1, walls=False, wall_density=0.20):
    """One ls20-shaped scenario: a chiral symbol, a required non-identity transform,
    a goal form, an avatar, a goal cell, and `n_stations` transform stations (exactly
    ONE of which performs the required transform). Positions are chosen so the
    goal-blind straight path does NOT pass any station (no accidental transforms).

    RUNG 220000 — `walls=True` sprinkles real ls20 wall cells (value 4) at
    `wall_density`, off the avatar/goal/station cells, and GUARANTEES 4-connected
    reachability from the avatar to every station and the goal (BFS retry). This is
    the WALLED regime the map machinery is for: a straight Manhattan run now STALLS
    on structure, and the quanta flood must route around. `walls=False` (default) is
    byte-identical to the pre-220000 open-grid generator."""
    name = rng.choice(list(CORPUS.keys()))
    offs, colour = CORPUS[name]
    symbol = [(r, c, colour) for (r, c) in offs]
    # recolour is restricted to the symbol's OWN colour(s) so the station key
    # matches what the sd-loop actually recognises on this mono-colour symbol
    # (a single categorical swap, not the whole 6-colour cycle).
    rmap = {colour: RECOLOUR_MAP[colour]}

    def _param(f, p):
        return rmap if (f == "recolour") else p

    fam, prm = _FAMILIES[rng.integers(len(_FAMILIES))]
    param = _param(fam, prm)
    goal_cells = apply_transform(symbol, fam, param)
    req_key = canonical_key(fam, param)

    # distractor transforms for extra stations (different keys)
    others = [(f, _param(f, p)) for (f, p) in _FAMILIES
              if canonical_key(f, _param(f, p)) != req_key]

    for _ in range(400):
        avatar = (int(rng.integers(H)), int(rng.integers(W)))
        goal = (int(rng.integers(H)), int(rng.integers(W)))
        if avatar == goal:
            continue
        blind_path = _greedy_path(avatar, goal)
        # station cells: off the blind path, distinct, not on avatar/goal
        occupied = set(blind_path) | {avatar, goal}
        st_cells = []
        ok = True
        for _s in range(n_stations):
            placed = None
            for _try in range(200):
                cell = (int(rng.integers(H)), int(rng.integers(W)))
                if cell not in occupied and cell not in st_cells:
                    placed = cell; break
            if placed is None:
                ok = False; break
            st_cells.append(placed)
        if not ok:
            continue
        # station 0 is the MATCHING one; the rest are distractors
        stations = [{"key": req_key, "r": st_cells[0][0], "c": st_cells[0][1],
                     "family": fam, "param": param}]
        rng.shuffle(others)
        for j in range(1, n_stations):
            f, pp = others[(j - 1) % len(others)]
            stations.append({"key": canonical_key(f, pp), "r": st_cells[j][0],
                             "c": st_cells[j][1], "family": f, "param": pp})
        # for multi-station, shuffle so the matching one is not always order 0
        rng.shuffle(stations)
        # RUNG 220000 walls: sprinkle ls20 wall cells off the critical cells, with a
        # guaranteed 4-connected route avatar -> every station -> goal. A wall layout
        # that traps any critical cell is rejected (retry a fresh sprinkle); if none is
        # found the outer loop re-lays the whole scenario.
        wall_set = set()
        if walls:
            critical = {avatar, goal} | {(s["r"], s["c"]) for s in stations}
            n_walls = int(round(wall_density * H * W))
            placed = False
            for _wtry in range(60):
                cand = set()
                while len(cand) < n_walls:
                    cell = (int(rng.integers(H)), int(rng.integers(W)))
                    if cell not in critical:
                        cand.add(cell)
                targets = [goal] + [(s["r"], s["c"]) for s in stations]
                if _reachable(avatar, targets, cand, H, W):
                    wall_set = cand; placed = True; break
            if not placed:
                continue
        return {"name": name, "family": fam, "param": param, "req_key": req_key,
                "symbol_cells": symbol, "goal_cells": goal_cells,
                "avatar_rc": avatar, "goal_rc": goal, "stations": stations,
                "walls": sorted(wall_set), "H": H, "W": W}
    raise RuntimeError("could not lay out scenario")
