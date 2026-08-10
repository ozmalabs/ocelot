#!/usr/bin/env python3
"""arc_run — the canonical ARC-AGI-3 runner for the seed-booted agent.

The agent DERIVES ITS OWN GOALS. Each turn the host loop only:
  perceive -> stamp the world's score/action-budget/steps-since-reset (mechanical I/O)
  -> tick (the agent's rules derive a goal about the most-salient unexplained region,
     pursue it with KNOWN moves, and gate commitment by confidence + order-N risk)
  -> read the agent's `chosen_action` off the graph -> submit it with the agent's reasoning.
No policy, no EXPLORE: the action is whatever the agent's understand-loop decided. The only
host fallback is a bootstrap nudge to MOVE before an avatar is known (you must act to perceive
what you control). All judgement is graph-native (goal_derivation + agency + meter seeds).

  ulimit -v 12000000
  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_run.py [--game ls20-9607627b] [--actions 40]
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _arc3_load_key import load_arc_api_key          # noqa: E402
from worlds.arc import ArcWorld                      # noqa: E402
from substrate.world_adapter import WorldAdapter     # noqa: E402
from substrate.boot_all import load_all_seeds        # noqa: E402
from move_space_planner import V, A, L, And, Not, Eq, Lt, Nb, Exists   # noqa: E402  term helpers
import domains.spatial_sense as _ss                  # noqa: E402  quanta-mode adapt+tick pass

DEFAULT_GAME = "ls20-9607627b"
# Bootstrap ONLY until an avatar is known: you must act to perceive what you control.
# Once the avatar is latched (2 prediction-matched moves) and a goal is derived, `chosen_action` drives.
BOOTSTRAP = ["Up", "Right", "Down", "Left"]
# Each action's KNOWN displacement (the confirmed motion semantics; Up moves up, as a rule).
DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1), "Select": (0, 0)}

# The MOVE-SPACE EXPAND choice as a TICK-FIRED RULE (graph data, not host code). Under pocket_escape, set
# chosen_action to the lowest-order affordance NOT yet tried from the current config — systematic expansion
# of the move-space manifold (a wall is then a residual the collapse faculty learns), never a blind cycle.
# The host only WRITES the observation (at_config + tried edges) and TICKS; it never calls this. The hop is
# guarded off under pocket_escape (grid_navigation.json) so this rule is the sole chosen_action writer there.
MS_CHOOSE_EXPAND = {
    "id": "ms_choose_expand", "name": "ms_choose_expand",
    "match": [["game", "at_config", "C"], ["game", "ms_aff", "aff"]],
    "where": And(
        Eq(A("game", "nav_mode"), L("pocket_escape")),
        Not(Exists(Nb("C", "tried"), "t", Eq(V("t"), V("aff")))),
        Not(Exists(Nb("game", "ms_aff"), "aff2",
            And(Not(Exists(Nb("C", "tried"), "t2", Eq(V("t2"), V("aff2")))),
                Lt(A("aff2", "order"), A("aff", "order")))))),
    "effects": [["set_attr", "game", "chosen_action", {"__term__": A("aff", "name")}]],
}


def _emit_avatar_motion(agent, game, prev_grid, now_grid, dr, dc, max_slide=14) -> int:
    """Mechanical perception (like the eye's cv2 segmentation): find the VALUE-PRESERVING translation
    along the action's KNOWN DIRECTION — the cells whose value LEFT them and REAPPEARED k steps away
    (prev[c]!=now[c] AND now[c+k·dir]==prev[c]). The DIRECTION is known (Up⇒row↓); the MAGNITUDE k (the
    SLIDE distance) is DISCOVERED by searching k and taking the clean translation with the most cells of
    a SINGLE value (a coherent moving thing, not field noise). Those cells ARE the avatar — a thing that
    MOVED — distinguished from a field that recoloured IN PLACE. Agnostic to colour/size/shape/slide.
    Emits one AvatarMotion node (centroid at the avatar's NEW position, count, value, slide). Returns count."""
    S, I = agent.s, agent.inner
    for am in list(S.nodes("AvatarMotion")):           # one per frame
        I.remove_node(am)
    if prev_grid is None or now_grid is None or (dr == 0 and dc == 0):
        return 0
    import numpy as np
    P = np.asarray(prev_grid); N = np.asarray(now_grid)
    if P.shape != N.shape:
        return 0
    ground = int(np.bincount(N.ravel()).argmax())      # modal = floor
    best = None                                        # (move_score, value, k, overlap_k)
    for v in (set(np.unique(P).tolist()) | set(np.unique(N).tolist())):
        if v == ground:
            continue
        prev_cells = list(zip(*[a.tolist() for a in np.where(P == v)]))
        if not (1 <= len(prev_cells) <= 500):          # the avatar is a small element, not the field
            continue
        now_set = set(zip(*[a.tolist() for a in np.where(N == v)]))
        np_ = len(prev_cells)
        ov0 = sum((r, c) in now_set for r, c in prev_cells) / np_     # static baseline (no shift)
        for k in range(1, max_slide + 1):
            kr, kc = dr * k, dc * k
            ovk = sum((r + kr, c + kc) in now_set for r, c in prev_cells) / np_
            ms = ovk - ov0                              # the SET translated as a whole, BETTER than static
            if ovk >= 0.6 and ms > 0.3 and (best is None or ms > best[0]):
                best = (ms, v, k, ovk)
    if best is None:
        return 0
    ms, v, k, ovk = best
    now_cells = list(zip(*[a.tolist() for a in np.where(N == v)]))    # the avatar's NEW position
    cy = sum(r for r, _ in now_cells) / len(now_cells)
    cx = sum(c for _, c in now_cells) / len(now_cells)
    am = S.add_node("AvatarMotion", {"cy": float(cy), "cx": float(cx), "n": float(len(now_cells)),
                                     "rvalue": float(v), "slide": float(k)})
    I.add_edge_unchecked(am, "of_game", game)
    return len(now_cells)


def _cell_index(agent):
    """(row,col) -> Cell node AND id -> Cell node, built ONCE (the grid is static) — mechanical perception
    indexes so the avatar-cell / slide-neighbour / reached-cell lookups are O(1), keeping the nav in µs."""
    idx = getattr(agent, "_cellidx", None)
    if idx is None:
        idx = {}; byid = {}
        S = agent.s
        for c in S.nodes("WorldInstance"):
            a = S.node(c)["attrs"]
            if a.get("world_type") == "Cell":
                idx[(int(a["row"]), int(a["col"]))] = c
                byid[int(str(c).lstrip("#"))] = c
        agent._cellidx = idx; agent._cellbyid = byid
    return idx


def _avatar_cell(agent, acy, acx, ground):
    """The cell at the avatar's TRUE centroid (its own occupant value, not floor). slide_flood seeds here and
    crosses the avatar's own blob generically (self_val read from the seed), so the gradient is centred on the
    avatar -- no floor-cell offset. Fall back to the nearest cell if the centroid is off-grid."""
    idx = _cell_index(agent)
    ar, ac = int(round(acy)), int(round(acx))
    c = idx.get((ar, ac))
    if c is not None:
        return c
    for rad in range(1, 8):
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                c = idx.get((ar + dr, ac + dc))
                if c is not None:
                    return c
    return None


def _avatar_footprint(agent, acy, acx):
    """Measure the avatar BODY's footprint: the connected same-value region under the centroid -> its
    top-left corner + height/width + value. Pure mechanical perception (measuring the body, like the eye
    measures a region). Capped so a floor-valued mis-centroid can't blow up. Returns (rmin,cmin,h,w,val)."""
    import numpy as np
    g = np.asarray(agent._last_grid)
    if g is None or g.ndim != 2:
        return None
    H, W = g.shape
    r0, c0 = int(round(acy)), int(round(acx))
    if not (0 <= r0 < H and 0 <= c0 < W):
        return None
    val = int(g[r0, c0])
    seen = {(r0, c0)}
    stack = [(r0, c0)]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen and int(g[nr, nc]) == val:
                seen.add((nr, nc)); stack.append((nr, nc))
                if len(seen) > 200:            # not a compact body -> the centroid isn't on the avatar
                    return None
    rs = [r for r, c in seen]; cs = [c for r, c in seen]
    return min(rs), min(cs), max(rs) - min(rs) + 1, max(cs) - min(cs) + 1, val


def _wall_values(agent, ground, av_val):
    """The world's BARRIER values: the play border (corner cell) + the dominant structural value (most
    common value that is neither floor nor the avatar's own value). Everything else (floor, features,
    the avatar's body) is walkable. Mechanical perception of which values block, derived not hardcoded."""
    import numpy as np
    g = np.asarray(agent._last_grid)
    border = int(g[0, 0])
    vals, cnts = np.unique(g, return_counts=True)
    cand = {int(v): int(c) for v, c in zip(vals, cnts) if int(v) not in (ground, av_val, border)}
    wall = max(cand, key=cand.get) if cand else border
    walls = {border, wall}
    # FLOOR IS THE SURFACE I STAND ON, NOT THE COMMON COLOUR (prediction_minus_observation: predicted floor =
    # most-common, observed = the colour under my body; the error corrects it). When the avatar's surface
    # (the ring its body sits in, measured in spatial_sense) is NOT the global mode `ground`, the common colour
    # is the VOID, not the floor: make it a wall and free the surface. When surface == ground (ordinary
    # floor-games), this is skipped and the heuristic is unchanged.
    surface = getattr(agent, "_spatial", {}).get("surface_val") if hasattr(agent, "_spatial") else None
    if surface is not None and int(surface) != ground:
        walls.add(ground)
        walls.discard(int(surface))
    # LEARN PASSABILITY FROM MOTION (prediction_minus_observation): any value the avatar has demonstrably
    # moved THROUGH is passable, however the static heuristic guessed — the observation corrects the guess.
    # The border always blocks (never walk off the world).
    learned = getattr(agent, "_spatial", {}).get("passable_vals", set()) if hasattr(agent, "_spatial") else set()
    walls = (walls - {int(v) for v in learned}) | {border}
    return sorted(walls)


_BLK = {(-1, 0): "_blk_u", (1, 0): "_blk_d", (0, -1): "_blk_l", (0, 1): "_blk_r"}
def _blk_attr(disp):
    """The per-cell block attr for a press direction (sign of the displacement). slide_flood refuses a slide
    whose source cell carries this attr -> the agent never re-proposes a move the world already refused."""
    dr, dc = disp
    return _BLK.get((1 if dr > 0 else -1 if dr < 0 else 0, 1 if dc > 0 else -1 if dc < 0 else 0))


def _stamp_near_mover(agent, prev_cells):
    """Stamp `near_mover` on the cells the agent's OWN mover Features occupy (and their 1-ring), so the
    explorable-frontier filter can DROP them — the agent's reasoned fix (jabberwock_reasons_ls20: apply the
    mover/static discriminator it already holds to its frontier). Mechanical perception I/O: it only reads the
    eye's `kind=mover` classification and marks cells; the DECISION to exclude movers is the graph rule.
    Clears last frame's marks first (movers move). Returns the new marked-cell set."""
    S, I = agent.s, agent.inner
    idx = _cell_index(agent)
    for cell in prev_cells:                              # clear last frame's marks (the movers have moved)
        I.set_attr(cell, "near_mover", 0.0)
    now = set()
    for f in S.nodes("Feature"):
        fa = S.node(f)["attrs"]
        if fa.get("kind") != "mover":
            continue
        cy, cx = fa.get("cy"), fa.get("cx")
        if cy is None or cx is None:
            continue
        r, c = int(round(cy)), int(round(cx))
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                cell = idx.get((r + dr, c + dc))
                if cell is not None:
                    I.set_attr(cell, "near_mover", 1.0); now.add(cell)
    return now


def _game_node(agent):
    for n in agent.s.nodes("WorldInstance"):
        if agent.s.node(n)["attrs"].get("world_type") == "Game":
            return n
    return None


def _wire_nav_modes(agent, game):
    """Link the game to the NavMode competitor nodes (game --has_mode--> mode), once. Mechanical wiring so the
    winner-take-all mode-selection rules can bind game + each mode in one match. Idempotent."""
    S, I = agent.s, agent.inner
    have = {S.node(m)["attrs"].get("name") for m in I.neighbours(game, "has_mode")}
    for nm in S.nodes("NavMode"):
        if S.node(nm)["attrs"].get("name") not in have:
            I.add_edge_unchecked(game, "has_mode", nm)


def _action_budget(agent) -> float:
    """The action budget = the (lowest) meter the agent reads — the countdown is a finite
    resource per action. No meter perceived yet -> no budget pressure (large)."""
    vals = [agent.s.node(m)["attrs"].get("meter_value") for m in agent.s.nodes("Mechanic")]
    vals = [v for v in vals if v is not None]
    return float(min(vals)) if vals else 999.0


def _stamp(agent, game, score, steps_since_reset, budget) -> None:
    if game is None:
        return
    I = agent.inner
    I.set_attr(game, "score", float(score or 0))
    I.set_attr(game, "actions_since_reset", float(steps_since_reset))
    I.set_attr(game, "action_budget", float(budget))


def _understanding(agent) -> dict:
    """Read the agent's STANDING WORLD MODEL out of the graph — pure query (the measure is the MODEL,
    not the score): the avatar it controls, the feature it's navigating to, the durable Features it has
    classified + understood, and the map it has explored."""
    from collections import Counter
    S = agent.s
    av = next((e for e in S.nodes("AvatarCandidate") if S.node(e)["attrs"].get("is_avatar")), None)
    ava = S.node(av)["attrs"] if av else {}
    feats = [S.node(f)["attrs"] for f in S.nodes("Feature")]
    resolved = [f for f in feats if f.get("resolved") == 1.0]
    nav = next((S.node(f)["attrs"] for f in S.nodes("Feature")
                if S.node(f)["attrs"].get("is_nav_target") == 1.0), None)
    if nav is not None:
        navtxt = f"a {nav.get('kind')} at ({round(nav.get('cy') or 0)},{round(nav.get('cx') or 0)})"
    else:
        ex = next((S.node(c)["attrs"] for c in S.nodes("WorldInstance")
                   if S.node(c)["attrs"].get("committed") == 1.0), None)
        navtxt = f"unexplored cell @({int(ex.get('row'))},{int(ex.get('col'))})" if ex else None
    g = next((S.node(n)["attrs"] for n in S.nodes("WorldInstance")
              if S.node(n)["attrs"].get("world_type") == "Game"), {})
    ground = g.get("ground")
    cells = [S.node(c)["attrs"] for c in S.nodes("WorldInstance")
             if S.node(c)["attrs"].get("world_type") == "Cell"]
    floor = [a for a in cells if a.get("value") == ground]
    slide = next((S.node(m)["attrs"].get("slide") for m in S.nodes("AvatarMotion")), None)
    return {"has_avatar": av is not None,
            "avatar": (round(ava.get("cy") or 0), round(ava.get("cx") or 0)) if av else None,
            "slide": int(slide) if slide else None, "nav": navtxt,
            "n_features": len(feats), "understood": len(resolved),
            "kinds": dict(Counter(f.get("kind") for f in feats)),
            "roles": dict(Counter(f.get("role") for f in resolved)),
            "loci": len(floor), "visited": sum(1 for a in floor if a.get("visited") == 1.0),
            "walls": len(cells) - len(floor)}


# --- AGENT SPEECH: every frame the world hands the agent a "Describe what you see." instruction; it goes into
# reasoning (the agent's own comprehend -> describe-Goal -> communicate rules), and the jabberwock self-reports
# through its language-production pipeline. The host only RECEIVES the instruction and PRINTS the report (to the
# console AND the ARC reasoning field) — nothing forced. Best-effort: if grounding fails the loop runs silently.
def _do_self_report(agent, scene, prod, gaming_defs):
    """World language-receiver -> reasoning -> self-report, accumulation-free + self-repairing. Each frame is a
    CLEAN recognition->describe cycle: SNAPSHOT the current perception into fresh throwaway Percept nodes (so
    recognition re-runs on the CURRENT kinds — no stale is_a edges, no stale communicate markers), tear down the
    PREVIOUS snapshot + describe-Goals/subgoals + instruction Message (no pile-up); the WORLD receives the
    instruction; the agent RELAXES any over-constrained recognition (self_repair_recognition); the JABBERWOCK
    self-reports. Reusing the persistent Feature nodes across frames was the bug — their is_a edges and the
    communicate rule's per-percept markers persisted, so a Feature recognised static stayed 'stays' after its
    kind flipped to mover, and subgoals never re-minted. Fresh Percepts each frame are the fix."""
    from arc_self_report import world_receive, self_report
    from jabberwock_relaxes_recognition import self_repair_recognition
    s, I = agent.s, agent.inner
    # node ids are recycled from a freelist with no generation, so nodes()/neighbours() can return a freed slot
    # that node() then panics on (the documented has_node contract). Guard every raw id we read.
    def _kind(n):
        return s.node(n)["attrs"].get("kind") if I.has_node(n) else None
    for p in agent.__dict__.get("_sr_percepts", []):      # tear down the PREVIOUS snapshot (cascades is_a/about)
        if I.has_node(p):
            try: I.remove_node(p)
            except Exception: pass
    for g in list(s.nodes("Goal")):                       # clear last frame's describe graph (no accumulation)
        if _kind(g) == "describe_scene":
            for sg in list(I.neighbours(g, "has_subgoal")):
                try: I.remove_node(sg)
                except Exception: pass
            try: I.remove_node(g)
            except Exception: pass
    for m in list(s.nodes("Message")):
        if I.has_node(m) and scene in list(I.neighbours(m, "about")):
            for mn in list(I.neighbours(m, "has_mention")):
                try: I.remove_node(mn)
                except Exception: pass
            try: I.remove_node(m)
            except Exception: pass
    for old in list(I.neighbours(scene, "has_percept")):  # detach the prior snapshot's percept links
        I.remove_edge_unchecked(scene, "has_percept", old)
    snap = []                                             # SNAPSHOT current perception -> fresh Percept nodes
    for f in s.nodes("Feature"):
        if not I.has_node(f):
            continue
        fa = s.node(f)["attrs"]
        if fa.get("cy") is None:
            continue
        p = s.add_node("Percept", dict(fa))               # copy the recognition-relevant attrs (mechanical)
        I.add_edge_unchecked(scene, "has_percept", p)
        snap.append(p)
    agent._sr_percepts = snap
    world_receive(agent, scene, "Describe what you see.")  # the language receiver
    I.run_rules()
    self_repair_recognition(agent, scene, gaming_defs, already=agent._relaxed)   # agent relaxes over-constraints
    I.run_rules()
    _ng, _nsg, lines = self_report(agent, prod)
    return lines


def _do_goal_report(agent, game, prod):
    """World receiver (GOALS) -> reasoning over the agent's DRIVE STATE -> the jabberwock says its aim + what it
    is curious about, in its own voice. Accumulation-free: tear down last frame's report_intent goal + subgoals
    + intent Message; the world receives 'what are you doing, and why?'; tick; emit the assembled frame. The aim
    (the active nav-mode's verb) and the curiosity (the unpredicted mover) are stamped by graph rules
    (nav_intent), not by the host — same receiver->reasoning->produce path as the observations."""
    from arc_self_report import world_receive_intent, self_report
    s, I = agent.s, agent.inner
    for o in list(s.nodes("Object")):                      # tear down last frame's composed whole-object (its
        if I.has_node(o):                                  # cells/shape are rebuilt fresh from current parts —
            try: I.remove_node(o)                          # the body moved, so the union must not accumulate)
            except Exception: pass
    for g in list(s.nodes("Goal")):
        if I.has_node(g) and s.node(g)["attrs"].get("kind") == "report_intent":
            for sg in list(I.neighbours(g, "has_subgoal")):
                try: I.remove_node(sg)
                except Exception: pass
            try: I.remove_node(g)
            except Exception: pass
    for m in list(s.nodes("Message")):
        if I.has_node(m) and game in list(I.neighbours(m, "intent_about")):
            for mn in list(I.neighbours(m, "has_mention")):
                try: I.remove_node(mn)
                except Exception: pass
            try: I.remove_node(m)
            except Exception: pass
    world_receive_intent(agent, game)
    I.run_rules()
    _ng, _nsg, lines = self_report(agent, prod, parent_kind="report_intent")
    return lines


def _setup_speech(agent):
    """Set up the production faculty (canonical bank -> grammar). The describe vocabulary — concept noun/verb
    attrs, shape labels, colour LexEntries — is GRAPH DATA loaded by the seeds (describe_lexicon / gaming /
    shape_library), not grounded here. Returns LanguageProduction or None on failure."""
    try:
        from domains.language_world import LanguageWorld, teacher_stub
        from domains.language_production import LanguageProduction
        from language_test import training_bank
        world = LanguageWorld(agent.inner, training_bank(), teacher_stub); world.run()
        world.teacher_disabled = True
        return LanguageProduction(world)
    except Exception as e:
        print("  [speech setup failed: %s: %s]" % (type(e).__name__, e), flush=True)
        return None


def _reasoning(u: dict, frame: int, steps: int, action: str, bootstrap: bool) -> str:
    bits = [f"frame {frame}."]
    if not u["has_avatar"]:
        bits.append("I don't yet know which token I control — moving to find out.")
    else:
        bits.append(f"I control a {u['slide']}-cell slider at {u['avatar']}.")
        if u["nav"]:
            bits.append(f"Heading to {u['nav']}.")
        bits.append(f"World model: {u['n_features']} things ({u['kinds']}); understood {u['understood']} "
                    f"({u['roles']}); mapped {u['loci']} cells, explored {u['visited']}, {u['walls']} walls.")
    risk = steps / (steps + 30.0)
    bits.append(f"Risk {risk:.2f} (replay-cost of {steps} steps). "
                + ("I act " + action + (" (bootstrap to perceive)" if bootstrap else " to explore + understand.")))
    return " ".join(bits)


def boot_agent(nav_repr: str = "cells"):
    """Boot a fresh seed-booted agent for ARC play: WorldAdapter + every seed,
    the speech/production pipeline, the self-describe faculty, and the
    tick-fired move-space EXPAND rule. Returns (agent, prod, describe_ctx).
    Pure setup — no episode/env involved, so it is reusable by any caller that
    wants a freshly-booted ARC-capable agent (the canonical CLI, or a child
    dispatch process that then boots from a snapshot instead — see
    `arc_child_run.py`)."""
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    print("native eye:", hasattr(agent.inner, "segment"), flush=True)
    prod = _setup_speech(agent)                          # the agent's voice (production pipeline; vocab is seeded)
    print("voice ready:", prod is not None, flush=True)
    describe_ctx = setup_describe(agent, prod)
    agent.inner.add_rule(MS_CHOOSE_EXPAND)   # tick-fired move-space EXPAND choice; the host never calls it
    return agent, prod, describe_ctx


def setup_describe(agent, prod) -> dict:
    """Build the agent's OWN describe faculty (comprehend an instruction -> mint a describe-Goal -> a
    produce-utterance subgoal per recognised thing). The world RECEIVES the instruction; the agent
    self-reports; the host only prints it. Returns a describe_ctx dict consumed by `run_episode`:
    {"enabled": bool, "scene": NodeID|None, "gaming_defs": dict}. Sets agent._relaxed / agent._sr_percepts
    (the self-report bookkeeping `_do_self_report` needs) regardless of success."""
    agent._relaxed = set(); agent._sr_percepts = []
    describe_ctx = {"enabled": False, "scene": None, "gaming_defs": {}}
    try:
        import json as _json2
        from arc_self_report import build_describe_faculty, world_receive, self_report  # noqa: F401
        from jabberwock_relaxes_recognition import self_repair_recognition             # noqa: F401
        if prod is not None:
            build_describe_faculty(agent)
            scene = agent.s.add_node("Scene", {})         # ONE reusable describe-scene (no per-frame accumulation)
            gaming_defs = {c["name"]: c["definition"]
                           for c in _json2.load(open(str(_ROOT / "seeds" / "gaming.json")))["concepts"]}
            describe_ctx = {"enabled": True, "scene": scene, "gaming_defs": gaming_defs}
    except Exception as _e:
        print("  [describe faculty setup failed: %s]" % _e, flush=True)
    return describe_ctx


def run_episode(agent, world, n_actions: int, nav_repr: str = "cells",
                 prod=None, describe_ctx=None, on_frame=None) -> dict:
    """Play `world` for up to `n_actions` turns with the seed-booted `agent` driving every
    action (no host policy — see the module docstring). This is the per-frame loop factored
    out of `main()` so a child dispatch process (`arc_child_run.py`) can reuse it verbatim
    against an offline or live env, after booting the agent from either a fresh seed load or a
    saved snapshot.

    `on_frame`, if given, is called once per applied action with a dict:
    ``{"frame", "action", "score", "reasoning", "self_report", "won", "over"}`` — the exact
    shape a trace-writer (JSONL) or scan_and_dispatch's caller needs; this function makes no
    decisions about what to do with it.

    Returns ``{"frames", "score", "won", "over"}`` — the final episode outcome.
    """
    describe_ctx = describe_ctx or {"enabled": False, "scene": None, "gaming_defs": {}}
    _describe, _scene, _gaming_defs = (describe_ctx["enabled"], describe_ctx["scene"],
                                       describe_ctx["gaming_defs"])
    if not hasattr(agent, "_relaxed"):
        agent._relaxed = set(); agent._sr_percepts = []
    t0 = time.time()
    sub, ctx = world.reset()
    agent.perceive_frame(sub)
    # move-space scaffold the host WRITES (mechanical adapt): affordance nodes + a config-node cache. The
    # tick-fired ms_choose_expand rule reads these during the agent's run_rules; the host never decides.
    _msg = _game_node(agent)
    if nav_repr == "quanta" and _msg is not None:
        # QUANTA MODE (FLOOD_DESIGN Part C): the mode is DATA on the game node; the qf_* rules
        # guard on it and the legacy hop starves naturally (no `_dist` is ever written).
        agent.inner.set_attr(_msg, "nav_repr", "quanta")
    ms_aff = {}
    for _k, _nm in enumerate(("Up", "Down", "Left", "Right")):
        _an = agent.s.add_node("MSAff", {"name": _nm, "order": float(_k)})
        agent.inner.add_edge_unchecked(_msg, "ms_aff", _an); ms_aff[_nm] = _an
    cfg_by_pos = {}; tried_set = set()
    steps = 0
    prev_grid = None
    last_disp = (0, 0)
    last_action = None        # the action submitted last frame (to learn the move-space from the slide it caused)
    last_slide = 1
    # nav SELECTION + progress/abandon live on the graph Features; `visited`/`wall` are now Locus attrs.
    # The host keeps only: the avatar's last position (to detect a blocked move) + the unstick counter.
    prev_av_pos = None        # avatar's last lattice position (to detect a blocked, zero-displacement move)
    nav_stuck = 0             # consecutive frames the avatar didn't move (wall) -> cycle directions out
    prev_avatar_cell = None   # last frame's avatar Cell (to clear its is_avatar_cell flag) — perception only
    blocked = {}              # (cell, blk_attr) -> frame stamped; learned blocks EXPIRE (the world is dynamic)
    BLOCK_TTL = 8             # a no-movement block lasts this many frames, then the avatar retries the direction
    prev_reached = None       # last frame's reachable-cell set (to measure frontier_flux for mover_avoid mode)
    near_mover_cells = set()   # cells currently marked near_mover (cleared+restamped each frame; movers move)
    for i in range(n_actions):
        game = _game_node(agent)
        agent.inner.set_attr(game, "frame", float(i))            # the feature-identity rules key on frame
        budget = _action_budget(agent)
        now_grid = getattr(agent, "_last_grid", None)
        # stamp the known displacement of the action that caused the last transition, then emit the
        # value-preserving-shift cell-set (the avatar's motion) for the rules to confirm/track.
        agent.inner.set_attr(game, "last_drow", float(last_disp[0]))
        agent.inner.set_attr(game, "last_dcol", float(last_disp[1]))
        _emit_avatar_motion(agent, game, prev_grid, now_grid, last_disp[0], last_disp[1])
        prev_grid = now_grid
        _stamp(agent, game, ctx.get("score", 0), steps, budget)
        agent.tick()                          # correlate->latch avatar; derive->pursue->commit
        # SPATIAL navigation: build the floor map from observation, route the avatar toward its
        # derived goal's LOCATION via the navigation cortex (around walls, in slide-units).
        action, navigating = "", False
        S, I = agent.s, agent.inner
        av = next((n for n in S.nodes("AvatarCandidate") if S.node(n)["attrs"].get("is_avatar")), None)
        if av is not None:
            acy = S.node(av)["attrs"].get("cy") or 0; acx = S.node(av)["attrs"].get("cx") or 0
            cur_pos = (round(acy), round(acx))
            # MOVE-SPACE observation — mechanical ADAPT (write what we perceive as graph data): the avatar's
            # current rest pose (at_config) and which affordance it just tried from its previous pose (tried).
            # The CHOICE is the tick-fired ms_choose_expand rule; the host writes data and ticks, never decides.
            cur_cfg = cfg_by_pos.get(cur_pos)
            if cur_cfg is None:
                cur_cfg = S.add_node("Config", {"r": float(cur_pos[0]), "c": float(cur_pos[1])})
                cfg_by_pos[cur_pos] = cur_cfg
            for _old in list(I.neighbours(game, "at_config")):
                I.remove_edge_unchecked(game, "at_config", _old)
            I.add_edge_unchecked(game, "at_config", cur_cfg)
            if prev_av_pos is not None and last_action is not None and (prev_av_pos, last_action) not in tried_set:
                tried_set.add((prev_av_pos, last_action))
                _pcfg = cfg_by_pos.get(prev_av_pos)
                if _pcfg is None:
                    _pcfg = S.add_node("Config", {"r": float(prev_av_pos[0]), "c": float(prev_av_pos[1])})
                    cfg_by_pos[prev_av_pos] = _pcfg
                if last_action in ms_aff:
                    I.add_edge_unchecked(_pcfg, "tried", ms_aff[last_action])
            stuck_now = prev_av_pos is not None and cur_pos == prev_av_pos and last_disp != (0, 0)
            if stuck_now:
                nav_stuck += 1                                   # pressed but didn't move (a wall) -> unstick
            else:
                nav_stuck = 0
            prev_av_pos = cur_pos
            mslide = next((S.node(m)["attrs"].get("slide") for m in S.nodes("AvatarMotion")), None)
            last_slide = int(mslide) if mslide else last_slide   # cache: the avatar slides the same each press
            import numpy as _np
            ground = int(_np.bincount(_np.asarray(now_grid).ravel()).argmax()) if now_grid is not None else 4
            I.set_attr(game, "ground", float(ground)); I.set_attr(game, "slide", float(last_slide))
            I.set_attr(game, "chosen_action", "")                # cleared; the hop RULE writes it, the host reads it
            # PURE PERCEPTION + PIPE. The host does NOT decide — it (1) MEASURES the avatar body (footprint
            # corner + h/w) and the barrier values, stamps is_avatar_cell on the body's corner cell, (2) FIRES
            # the rigid-body slide_flood from it (the spatial sense, like the eye firing cv2) -> `_dist`/`_epoch`/
            # `reached` on the reachable body-positions, (3) ticks the rules (mark_visited/release/select),
            # (4) fires slide_flood from the committed goal -> distance-to-goal, (5) ticks (hop), (6) reads
            # chosen_action. Every nav DECISION is a graph rule in seeds/grid_navigation.json.
            fp = _avatar_footprint(agent, acy, acx)
            walls = _wall_values(agent, ground, fp[4]) if fp else [ground]
            A = _cell_index(agent).get((fp[0], fp[1])) if fp else None
            if (S.node(game)["attrs"].get("nav_repr") or "") == "quanta":
                # QUANTA MODE: same perception stamps, then the shared quanta flood pass instead of
                # the two slide_floods. A pressed-didn't-move outcome becomes a BlockObs node (the
                # qf_stale_on_block_* rules decide split-vs-portal-flip); `_blk_*` stays cell-only.
                if A is not None:
                    I.set_attr(game, "fresh", 0.0 if S.node(A)["attrs"].get("visited") == 1.0 else 1.0)
                    if prev_avatar_cell is not None and prev_avatar_cell != A:
                        I.set_attr(prev_avatar_cell, "is_avatar_cell", 0.0)
                    I.set_attr(A, "is_avatar_cell", 1.0); prev_avatar_cell = A
                _wire_nav_modes(agent, game)
                near_mover_cells = _stamp_near_mover(agent, near_mover_cells)
                _pend = False
                if stuck_now:
                    _ss.record_block_obs(agent, game, cur_pos, last_disp, i)
                    _pend = True
                _ss.bump_belief_epoch(agent)          # a live frame refreshes the belief each turn
                _gg = _np.asarray(now_grid) if now_grid is not None else None
                _vals = sorted(set(int(v) for v in _np.unique(_gg))) if _gg is not None else []
                _passable = [v for v in _vals if v not in set(int(w) for w in walls)]
                _ss.quanta_flood_step(agent, game, cur_pos, ((fp[2], fp[3]) if fp else (1, 1)),
                                      _passable, last_slide,
                                      tuple(_gg.shape) if _gg is not None else (64, 64),
                                      pending_block=_pend)
            elif A is not None:
                fph, fpw = fp[2], fp[3]
                # LEARN passability from the last outcome: the previous press was flood-approved but the avatar
                # did NOT move -> stamp that (cell, direction) dead so this & future floods route around it.
                # Blocks EXPIRE (BLOCK_TTL): the world is dynamic, a move dead now may open later -> retry.
                for (bcell, battr), bf in list(blocked.items()):
                    if i - bf >= BLOCK_TTL:
                        I.set_attr(bcell, battr, 0.0); del blocked[(bcell, battr)]
                if stuck_now:
                    ba = _blk_attr(last_disp)
                    if ba is not None:
                        I.set_attr(A, ba, 1.0); blocked[(A, ba)] = i
                # coverage-progress signal: is the avatar on a cell it has NOT visited before? (read BEFORE the
                # flood's run_rules marks it). The cover_tick rule uses this to reset/advance its no-progress
                # counter; mechanical measurement, the abandon DECISION is a rule.
                I.set_attr(game, "fresh", 0.0 if S.node(A)["attrs"].get("visited") == 1.0 else 1.0)
                if prev_avatar_cell is not None and prev_avatar_cell != A:
                    I.set_attr(prev_avatar_cell, "is_avatar_cell", 0.0)
                I.set_attr(A, "is_avatar_cell", 1.0); prev_avatar_cell = A
                gid = int(str(game).lstrip("#"))
                _wire_nav_modes(agent, game)                     # link game -> NavMode competitors (idempotent)
                near_mover_cells = _stamp_near_mover(agent, near_mover_cells)   # the agent's reasoned fix: mark mover cells
                # POCKET_ESCAPE (the mode the agent chose last frame, if confined): the prober clears stale
                # learned blocks so THIS escape flood can retry directions and find a way out (mechanical).
                if (S.node(game)["attrs"].get("nav_mode") or "") == "pocket_escape" and blocked:
                    for bk in list(blocked.keys()):
                        I.set_attr(bk[0], bk[1], 0.0)
                    blocked.clear()
                I.slide_flood(int(str(A).lstrip("#")), last_slide, fph, fpw, walls, 40, i, gid, True, "_adist")   # avatar flood -> _adist (+reached)
                I.set_attr(game, "flood_epoch", float(i))        # epoch of THIS flood; release_goal keys staleness on it
                # frontier_flux: how much the reachable set CHURNS move-to-move (moving objects) -> drives the
                # mover_avoid mode's activation. Stamped before run_rules so activate_mover_avoid reads it.
                reached_now = set(int(str(n).lstrip("#")) for n in I.neighbours(game, "reached"))
                I.set_attr(game, "frontier_flux", float(len(reached_now ^ prev_reached) if prev_reached else 0))
                prev_reached = reached_now
                agent.inner.run_rules()                          # cover_tick / activate_* / select_mode / abandon / select_seek|escape
                goal = next(iter(I.neighbours(game, "committed_goal")), None)
                if goal is not None:
                    I.slide_flood(int(str(goal).lstrip("#")), last_slide, fph, fpw, walls, 40, i, gid, False, "_dist")  # goal flood -> _dist
                    agent.inner.run_rules()                      # hop_descend_gradient -> game.chosen_action
            act = S.node(game)["attrs"].get("chosen_action") or ""
            if act:
                action, navigating = act, True
            # No host action-decision. chosen_action (read just above) was written by TICK-FIRED rules only:
            # hop_descend_gradient when navigating, and ms_choose_expand under pocket_escape (the move-space
            # EXPAND choice). The host adapted (wrote the observation) and ticked; the graph decided.
        if action == "":                          # no route yet -> the graph's own pick, else bootstrap
            action = S.node(agent.agent)["attrs"].get("chosen_action") or ""
        bootstrap = action == ""
        if bootstrap:
            action = BOOTSTRAP[i % len(BOOTSTRAP)]
        u = _understanding(agent)
        # SELF-REPORT (NOT forced): the WORLD receives an instruction (the language receiver); it goes into
        # REASONING (the agent's own comprehend->describe-Goal->communicate rules); the JABBERWOCK self-reports
        # via its language faculty; the host only PRINTS it. No host-authored utterances.
        report, goals = [], []
        if _describe:
            try:
                report = _do_self_report(agent, _scene, prod, _gaming_defs)   # observations: what I see
                _g = _game_node(agent)
                if _g is not None:
                    goals = _do_goal_report(agent, _g, prod)                  # goals: what I aim at + am curious about
            except Exception:
                report, goals = report, goals
        reasoning = _reasoning(u, i, steps, action, bootstrap)
        voices = []                                              # the agent's own voice -> console + ARC reasoning
        if report:
            voices.append("I see: " + " ".join(report))
        if goals:
            voices.append("I aim: " + " ".join(goals))
        if voices:
            reasoning = "  ||  ".join(voices) + "  ||  " + reasoning
        t = time.time()
        sub, ctx = world.apply((action,), reasoning=reasoning)
        steps += 1
        last_disp = DISP.get(action, (0, 0))                     # known displacement for next frame's correlate
        last_action = action                                     # the move-space planner learns from this next frame
        agent.inner.set_attr(agent.agent, "chosen_action", "")   # derive fresh next frame
        agent.perceive_frame(sub)
        who = (f"avatar@{u['avatar']} slide{u['slide']}" if u["has_avatar"] else "no-avatar")
        _mode = (S.node(_game_node(agent))["attrs"].get("nav_mode") or "—") if _game_node(agent) else "—"
        print(f"  {i+1:3} {action:6} ({(time.time()-t)*1000:4.0f}ms) [{_mode:13s}] {who} -> {u['nav'] or '—'} | "
              f"understood {u['understood']}/{u['n_features']} {u['roles']} | "
              f"map {u['visited']}/{u['loci']} walls={u['walls']}"
              f"{' [bootstrap]' if bootstrap else ''}", flush=True)
        for _v in voices:                                       # -> to the console
            print(f"        🗣  {_v}", flush=True)
        if on_frame is not None:
            on_frame({"frame": i, "action": action, "score": ctx.get("score", 0),
                      "reasoning": reasoning, "self_report": " ".join(report) if report else "",
                      "won": bool(ctx.get("won")), "over": bool(ctx.get("over"))})
        if ctx.get("over") or ctx.get("won"):
            print("  game", "WON" if ctx.get("won") else "OVER"); break

    u = _understanding(agent)
    print(f"\ntotal {time.time()-t0:.1f}s. UNDERSTOOD {u['understood']} of {u['n_features']} features "
          f"(kinds {u['kinds']}, roles {u['roles']}); mapped {u['loci']} cells "
          f"(explored {u['visited']}, walls {u['walls']}); avatar slides {u['slide']} cells/press.", flush=True)
    # the agent states its GOAL in its own voice (graph-native, from its drive state) — not host prose.
    if _describe and prod is not None and _game_node(agent) is not None:
        try:
            final_goal = _do_goal_report(agent, _game_node(agent), prod)
        except Exception:
            final_goal = []
        if final_goal:
            print("\n  [ASKED THE ENTITY: what are you doing, and why?]")
            for ln in final_goal:
                print(f"    🗣  {ln}")
    return {"frames": i + 1, "score": ctx.get("score", 0),
            "won": bool(ctx.get("won")), "over": bool(ctx.get("over"))}


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical ARC-AGI-3 runner (derives its own goals)")
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--actions", type=int, default=40)
    ap.add_argument("--nav-repr", default=os.environ.get("NAV_REPR", "cells"),
                    choices=["cells", "quanta"],
                    help="map representation: 'cells' (legacy slide_flood) or 'quanta' (space_quantize + qf rules)")
    args = ap.parse_args()

    if not load_arc_api_key():
        print("could not load ARC_API_KEY from .env — aborting"); return 1
    from arc3_live_env import Arc3LiveEnv                # noqa: E402
    print(f"connecting {args.game} ...", flush=True)
    env = Arc3LiveEnv(args.game)
    agent, prod, describe_ctx = boot_agent(nav_repr=args.nav_repr)
    world = ArcWorld(env)
    run_episode(agent, world, args.actions, args.nav_repr, prod, describe_ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
