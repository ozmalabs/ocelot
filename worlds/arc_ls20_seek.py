"""arc_ls20_seek — RUNG 227000: THE GAME IS COMMUNICATING — a posit-and-test
semiosis scenario that DISCOVERS the flash's meaning, then acts (seek-and-transform).

MECHANICAL world adapter + episode driver. ALL decisions (which meaning the flash
carries; whether to seek; which move) live in the graph rules
(domains/ls20_seek_seed.py). The adapter does only:

  PERCEIVE   — SEE the carried shape + the block's required form through the 216000
               pixel eye; write the perceptual facts the rules read
               (symbol_matches_goal by integer-native set-equality; flash_present;
               the 217000 sd-loop req_key; which stations exist/are used).
  INGEST     — instantiate the GENERAL communicative vocabulary (SignMeaning nodes,
               seed data) and link them to the game (`knows_meaning`). Uniform — it
               does NOT choose the meaning; the rules mint posits + decide.
  ACT        — read the rule-chosen waypoint and STEP toward it (greedy Manhattan /
               220000 quanta flood). For the cycling / no-test path (no waypoint),
               cycle a fixed action sequence (the "just cycling" baseline).
  WORLD      — apply a station's transform when the avatar arrives at it; OBSERVE
               the test probe (arriving at the block AS-IS: did it pass? any harm?);
               pass at the block by exact set equality (the oracle).

There is NO Python deciding the flash's MEANING or the agent's MOVE.
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
from domains.ls20_seek_seed import RULES, VOCAB  # noqa: E402
from worlds.arc_ls20_scenario import (  # noqa: E402
    make_scenario, render_and_see, recognise_required_key, apply_transform,
    _normset, _reposition, _greedy_step,
)

# a fixed blind action cycle (the "just cycling" baseline the owner saw)
_CYCLE = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Up, Right, Down, Left


class SeekPlanner:
    """Holds the game + station nodes + the general communicative vocabulary + the
    ls20_seek rules. Each step the adapter stamps perception facts and run_rules()
    mints/tests posits and writes the waypoint (the graph's decision)."""

    def __init__(self, arm, stations, goal_rc):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "seek_on": 1.0, "arm": arm, "symbol_matches_goal": 0.0,
            "flash_present": 0.0, "req_key": "", "transform_required": 0.0,
            "test_observed": 0.0, "observed_accept": 0.0, "observed_harm": 0.0,
            "confirmed_meaning": "", "waypoint": "", "wp_r": 0.0, "wp_c": 0.0,
            "goal_r": float(goal_rc[0]), "goal_c": float(goal_rc[1])})
        p = self.s.add_node("Ping", {})
        self.n.add_edge_unchecked(self.g, "has_ping", p)
        # INGEST the GENERAL communicative vocabulary (seed data) — the rules mint
        # a Posit per meaning. Uniform; no meaning is chosen here.
        for m in VOCAB:
            sm = self.s.add_node("SignMeaning", {
                "meaning": m["meaning"], "pred_accept": float(m["pred_accept"]),
                "pred_harm": float(m["pred_harm"]), "implies_change": float(m["implies_change"])})
            self.n.add_edge_unchecked(self.g, "knows_meaning", sm)
        self.stations = []
        for i, st in enumerate(stations):
            sn = self.s.add_node("Station", {"key": st["key"], "r": float(st["r"]),
                                             "c": float(st["c"]), "used": 0.0,
                                             "order": float(i)})
            self.n.add_edge_unchecked(self.g, "has_station", sn)
            self.stations.append(sn)

    def step_decide(self, *, matches, req_key, used_flags, flash_present,
                    test_observed, observed_accept, observed_harm):
        n, g = self.n, self.g
        n.set_attr(g, "symbol_matches_goal", 1.0 if matches else 0.0)
        n.set_attr(g, "req_key", req_key or "")
        n.set_attr(g, "flash_present", 1.0 if flash_present else 0.0)
        n.set_attr(g, "test_observed", 1.0 if test_observed else 0.0)
        n.set_attr(g, "observed_accept", float(observed_accept))
        n.set_attr(g, "observed_harm", float(observed_harm))
        n.set_attr(g, "waypoint", "")
        for sn, uf in zip(self.stations, used_flags):
            n.set_attr(sn, "used", 1.0 if uf else 0.0)
        n.run_rules()
        a = self.s.node(g)["attrs"]
        return {"waypoint": a.get("waypoint") or "",
                "wp": (int(round(a.get("wp_r") or 0)), int(round(a.get("wp_c") or 0))),
                "confirmed_meaning": a.get("confirmed_meaning") or "",
                "transform_required": float(a.get("transform_required") or 0.0),
                "affect": a.get("affect") or ""}

    def read_posits(self):
        """Read the Posit Hypothesis nodes the rules minted (mechanical query)."""
        out = []
        for q in self.s.neighbours(self.g, "has_posit"):
            at = self.s.node(q)["attrs"]
            out.append({"meaning": at.get("meaning"), "status": at.get("status")})
        return out


def _cycle_step(pos, step, walls, H, W):
    dr, dc = _CYCLE[step % len(_CYCLE)]
    nxt = (pos[0] + dr, pos[1] + dc)
    if not (0 <= nxt[0] < H and 0 <= nxt[1] < W) or nxt in walls:
        return pos
    return nxt


def _apply_station_if_on(carried, pos, stations, used):
    for i, st in enumerate(stations):
        if not used[i] and pos == (st["r"], st["c"]):
            used[i] = True
            return apply_transform(carried, st["family"], st["param"]), True
    return carried, False


def run_seek_episode(scn, arm, budget=200, trace=False):
    """Play one scenario with one policy arm. Returns an outcome dict incl. the
    posit statuses (what the agent DISCOVERED the flash meant). The block is
    flash-marked (flash_present=1); passing = arriving at the block with the shape
    matching the required transform (oracle exact set equality)."""
    goal_norm = _normset(render_and_see(scn["goal_cells"]))
    req_key = recognise_required_key(scn["symbol_cells"], scn["goal_cells"])
    planner = SeekPlanner(arm, scn["stations"], scn["goal_rc"])
    walls = set(tuple(w) for w in scn.get("walls", ()))
    H, W = scn.get("H", 16), scn.get("W", 16)
    block = tuple(scn["goal_rc"])

    carried = _reposition(scn["symbol_cells"])
    pos = tuple(scn["avatar_rc"])
    used = [False] * len(scn["stations"])
    test_observed = False
    obs_accept = 0.0
    obs_harm = 0.0
    tr_log = []

    for step in range(budget):
        matches = _normset(render_and_see(carried)) == goal_norm
        dec = planner.step_decide(matches=matches, req_key=req_key, used_flags=used,
                                  flash_present=True, test_observed=test_observed,
                                  observed_accept=obs_accept, observed_harm=obs_harm)
        wp = dec["waypoint"]
        if trace:
            tr_log.append({"step": step, "pos": pos, "matches": bool(matches), "waypoint": wp,
                           "wp": dec["wp"], "confirmed_meaning": dec["confirmed_meaning"],
                           "transform_required": dec["transform_required"]})

        # No rule chose a waypoint (cycling / no_test) -> cycle a fixed action seq.
        if wp == "":
            pos = _cycle_step(pos, step, walls, H, W)
            carried, _ = _apply_station_if_on(carried, pos, scn["stations"], used)
            if pos == block and _normset(render_and_see(carried)) == goal_norm:
                return _out(arm, True, step, "cycled_into_pass", req_key, planner, tr_log)
            continue

        # Routing to the block.
        if wp == "goal" and pos == block:
            if matches:
                return _out(arm, True, step, "passed", req_key, planner, tr_log)
            # TEST PROBE: arrived at the block with the shape AS-IS and it did NOT
            # pass (world physics) and no harm. Observe; do NOT terminate — the
            # semiosis rules consume this to refute/confirm the posits. (For
            # hardcode_reward this is the belief-refuting non-pass it never heeds.)
            if not test_observed:
                test_observed = True
                obs_accept = 0.0   # as-is did NOT pass
                obs_harm = 0.0     # no harm
            else:
                # already observed but still routing to the block un-matched with no
                # confirmed change (hardcode_reward / stuck) -> nudge along the cycle
                # so it is not frozen (still cannot pass -> will time out).
                pos = _cycle_step(pos, step, walls, H, W)
            continue

        # Normal step toward the rule-chosen waypoint.
        nxt = _greedy_step(pos, dec["wp"], walls)
        pos = nxt
        # world physics: a station transforms the carried shape when the avatar
        # ARRIVES at it as the chosen destination.
        if wp == "station" and pos == dec["wp"]:
            carried, _ = _apply_station_if_on(carried, pos, scn["stations"], used)

    return _out(arm, False, budget, "timeout", req_key, planner, tr_log)


def _out(arm, win, steps, reason, req_key, planner, tr_log):
    posits = planner.read_posits()
    confirmed = [p["meaning"] for p in posits if p["status"] == "confirmed"]
    refuted = [p["meaning"] for p in posits if p["status"] == "refuted"]
    open_ = [p["meaning"] for p in posits if p["status"] == "open"]
    correct = (confirmed == ["requirement"]
               and set(refuted) == {"reward", "acknowledgement", "location", "warning"})
    return {"arm": arm, "win": bool(win), "steps": steps, "reason": reason,
            "req_key": req_key, "n_posits": len(posits),
            "confirmed": confirmed, "refuted": refuted, "open": open_,
            "correct_meaning_discovered": bool(correct),
            "confirmed_meaning": (planner.s.node(planner.g)["attrs"].get("confirmed_meaning") or ""),
            "trace": tr_log}


def make_seek_scenario(rng, H=16, W=16):
    """One ls20-shaped SEEK scenario: a chiral symbol carried by the avatar, a
    flash-marked block whose requirement is a non-identity transform, and exactly
    ONE other salient shape (the transform provider). Reuses the 218000 generator
    (n_stations=1 == the only-other shape)."""
    scn = make_scenario(rng, H=H, W=W, n_stations=1)
    scn["flash_marked"] = True
    return scn
