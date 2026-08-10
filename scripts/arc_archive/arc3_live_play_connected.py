"""arc3_live_play_connected — STEP B: play ONE live ARC-AGI-3 game with the
agent's grounded ARC understanding CONNECTED to its drives (STEP A), and let
the connected understanding (not just the navigate seed) shape play.

A THIN HARNESS (CLAUDE.md): it boots the agent, runs the STEP A connection
(driving the agent's OWN consider() over its grounded ARC understanding + its
seed's declared objective), plays the agent's OWN live loop, and re-offers the
held score-pursuit goal to consider() each insight cadence so the AGENT adopts
it the moment its proprioceptive score signal (my_vel_score) becomes
perceptible. No hand-authored action, no hand-authored connection.

It reuses the existing live machinery verbatim:
  · arc3_live_env.Arc3LiveEnv     — the live HTTP transport (key from os.environ)
  · domains.arc3_world            — the world adapter (grid -> substrate)
  · domains.arc3_seed             — the arc3 meta-rules seed
  · scripts.arc3_live_experiment  — the bounded-menu helpers + heldout eval

Captures: did pursue_score promote/adopt (the connection grounding live), what
the agent perceived, whether the score signal shaped play (best_score, actions
to first progress), and the agent's OWN engagement readouts.

Run:
  ulimit -v 8388608
  timeout 600 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/arc3_live_play_connected.py --game <game_id> --actions 60
"""
from __future__ import annotations

import argparse
import random
import sys
import time as _time
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _arc3_load_key import load_arc_api_key  # noqa: E402
from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_world import arc3_world_handle, SELF_ID  # noqa: E402
from domains.arc3_seed import install_arc3_seed  # noqa: E402
from arc3_live_env import Arc3LiveEnv  # noqa: E402
from arc3_live_experiment import (  # noqa: E402
    _live_legal_actions, _changed_celltypes, _goal_cell_grounded,
)

SEP = "=" * 78


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# --- the STEP A connection, driven by the agent's OWN consider() faculty ---
def connect_understanding(agent) -> dict:
    """Offer the agent its grounded ARC understanding + its seed's declared
    objective; the AGENT disposes via consider(). Returns the held score-goal
    guidance so the play loop can re-offer it once the score signal grounds."""
    import json as _json
    rep = {"concepts": [], "score_goal": None}
    ctx = _ROOT / "data" / "arc_agi_grounded_context.json"
    grounded_names: list[str] = []
    if ctx.exists():
        with ctx.open() as f:
            d = _json.load(f)
        for n in d.get("nodes", []):
            if n.get("type") == "Concept":
                a = n.get("attrs") or {}
                nm = a.get("name")
                if nm and a.get("definition"):
                    grounded_names.append(nm)
    play_relevant = [c for c in (
        "agent", "action", "goal", "object_permanence", "perception_visual",
        "cognition", "volition", "existence", "location_state")
        if c in grounded_names]
    for name in play_relevant:
        dec = agent.consider({"kind": "concept", "word": name,
                              "definition": {"type": "Var", "name": name}})
        rep["concepts"].append((name, dec["decision"]))
    # the seed's OWN objective ("score_increased_or_win") re-expressed over the
    # proprioceptive my_vel_score the agent FEELS; handed to consider().
    score_goal = {
        "kind": "goal", "label": "pursue_score", "domain": "self",
        "priority": 1.0,
        "satisfaction": {"type": "Gt",
                         "a": {"type": "Attr",
                               "node": {"type": "Var", "name": "agent"},
                               "key": "my_vel_score"},
                         "b": {"type": "Lit", "value": 0}},
    }
    dec = agent.consider(score_goal)
    rep["score_goal"] = (dec["decision"], dec.get("reason", ""))
    return rep, score_goal


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=None)
    ap.add_argument("--actions", type=int, default=60)
    ap.add_argument("--coord-stride", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if not load_arc_api_key():
        print("BLOCKER: ARC_API_KEY not available; aborting.")
        return 2
    import os
    print(f"key present: True  (length={len(os.environ['ARC_API_KEY'])})")

    # pick a game (first public game if unspecified — bounded single game).
    if args.game is None:
        import requests
        from arc3_live_env import DEFAULT_BASE_URL
        sess = requests.Session()
        sess.headers.update({"X-Api-Key": os.environ["ARC_API_KEY"],
                             "Accept": "application/json"})
        r = sess.get(f"{DEFAULT_BASE_URL}/api/games", timeout=30)
        r.raise_for_status()
        args.game = [g["game_id"] for g in r.json() if g.get("game_id")][0]
    print(f"game: {args.game}  action_budget: {args.actions}")

    random.seed(args.seed)
    env = Arc3LiveEnv(args.game)
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    install_arc3_seed(agent)

    # ----------------------------------------------------- STEP A: CONNECT
    banner("STEP A — CONNECT: the agent disposes of its grounded ARC "
           "understanding + its seed's objective via consider() (verbatim):")
    conn, score_goal = connect_understanding(agent)
    for name, dec in conn["concepts"]:
        print(f"  concept {name:18s} -> {dec}")
    print(f"  objective pursue_score   -> {conn['score_goal'][0]}  "
          f"({conn['score_goal'][1][:70]})")
    pre_drives = [agent.mind_graph.node(g).attrs.get("label")
                  for g in agent._get_top_level_goals()]
    print(f"  drives now               : {pre_drives}")
    pursue_promoted_at = None
    pursue_adopted_at = None

    handle = arc3_world_handle(env, agent)
    agent.set_compute_limit(50.0 * float(args.actions))

    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    banner("STEP B — PLAY one live game (the agent's own loop). Per-tick: "
           "choose_action / observe / record; insight re-grounds the held "
           "score-goal; we re-offer it to consider() so the AGENT adopts it "
           "once it can ground my_vel_score.")
    transitions: list = []
    actions_chosen: Counter = Counter()
    coords: Counter = Counter()
    best_score = ctx.get("score", 0)
    first_progress = None
    won_at = None
    score_perceived_at = None
    grounded_tick = None
    tick_walls: list[float] = []

    for i in range(args.actions):
        actions = _live_legal_actions(handle, substrate, ctx, env,
                                      args.coord_stride)
        if not actions:
            actions = _live_legal_actions(handle, substrate, ctx, env, 1)
        if not actions:
            print(f"    [{i}] no legal actions (available={env.available_actions})")
            break

        t0 = _time.perf_counter()
        action = agent.choose_action(substrate, ctx, actions, handle)
        kind = canonical_action_kind(action)
        actions_chosen[kind] += 1
        if kind.startswith("c6_"):
            coords[kind] += 1
        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)
        q_before = agent.quality_of_position(substrate)
        pre = substrate
        tw = (_time.perf_counter() - t0) * 1000.0

        substrate, ctx = handle["apply_action"](substrate, ctx, action)

        t1 = _time.perf_counter()
        transitions.append((kind, _changed_celltypes(pre, substrate)))
        agent.observe(substrate)
        # has the proprioceptive score signal become perceptible yet?
        root_attrs = agent.mind_graph.node(agent.agent_root).attrs
        if score_perceived_at is None and "my_vel_score" in root_attrs:
            score_perceived_at = i + 1
        q_after = agent.quality_of_position(substrate)
        agent.record_action_outcome(
            kind, agent.last_world_novelty, max(0.0, q_before - q_after),
            agent.boredom_count(substrate), ctx.get("tick", 0),
            terminal_delta=1.0 if ctx["won"] else 0.0,
            frontier_after=agent.last_freshening_count)

        if ctx["score"] > best_score:
            best_score = ctx["score"]
            if first_progress is None:
                first_progress = i + 1
                print(f"    [{i+1}] SCORE PROGRESS -> {best_score}")

        if (i + 1) % 8 == 0:
            agent.grow_gamma()
            # the insight pass re-grounds held predicates: pursue_score promotes
            # the moment my_vel_score is perceived. Read whether it promoted.
            before_held = {h["name"] for h in agent.held_predicates()}
            agent.insight(layer=1)
            after_held = {h["name"] for h in agent.held_predicates()}
            if (pursue_promoted_at is None
                    and "pursue_score" in before_held
                    and "pursue_score" not in after_held):
                pursue_promoted_at = i + 1
            # re-offer the score-goal to the agent's consider(): once the
            # dependency (my_vel_score) is met, consider() ADOPTS it as a drive
            # (the agent's own faculty makes the adoption, not us).
            if pursue_adopted_at is None and "pursue_score" not in {
                    agent.mind_graph.node(g).attrs.get("label")
                    for g in agent._get_top_level_goals()}:
                dec = agent.consider(score_goal)
                if dec["decision"] == "adopted_candidate":
                    pursue_adopted_at = i + 1
                    print(f"    [{i+1}] AGENT ADOPTED pursue_score as a drive "
                          f"(my_vel_score now grounds)")
        if (i + 1) % 16 == 0:
            agent.discover_relations()

        tick_walls.append(tw + (_time.perf_counter() - t1) * 1000.0)
        if grounded_tick is None and _goal_cell_grounded(agent):
            grounded_tick = i + 1
        if ctx["won"] and won_at is None:
            won_at = i + 1
            print(f"    [{i+1}] WIN")
            break
        if ctx["over"]:
            print(f"    [{i+1}] GAME_OVER; resetting")
            substrate, ctx = handle["reset"]()
            agent.observe(substrate)

    scorecard = env.close_scorecard()

    banner("STEP B RESULT — the live game outcome (verbatim readouts):")
    print(f"  game                       : {args.game}")
    print(f"  WIN at action              : {won_at}")
    print(f"  best level/score reached   : {best_score}")
    print(f"  actions to first progress  : {first_progress}")
    print(f"  transitions observed       : {len(transitions)}")
    print(f"  distinct ACTION6 coords    : {len(coords)}")
    print(f"  actions chosen (by kind)   : "
          f"{dict(Counter({k: v for k, v in actions_chosen.most_common(8)}))}")
    print("  -- the connection, live --")
    print(f"  score signal first perceived (my_vel_score) @action: "
          f"{score_perceived_at}")
    print(f"  pursue_score PROMOTED (held->grounded) @action     : "
          f"{pursue_promoted_at}")
    print(f"  pursue_score ADOPTED as a drive @action            : "
          f"{pursue_adopted_at}")
    final_drives = [agent.mind_graph.node(g).attrs.get("label")
                    for g in agent._get_top_level_goals()]
    print(f"  final drives                                       : "
          f"{final_drives}")
    print(f"  goal_cell (navigate hack) grounded @action         : "
          f"{grounded_tick}  (the seed bonus; the score drive is the "
          f"connected path)")
    if tick_walls:
        print(f"  per-tick agent wall (ms): mean="
              f"{sum(tick_walls)/len(tick_walls):.1f} "
              f"max={max(tick_walls):.1f}")
    if scorecard:
        print(f"  server scorecard          : "
              f"levels_completed={scorecard.get('total_levels_completed')} "
              f"total_actions={scorecard.get('total_actions')} "
              f"score={scorecard.get('score')}")

    # ====================================================== STEP C: SELF-ASSESS
    # Drive the agent's OWN self-assessment faculties and print them VERBATIM.
    # No grading by the shell.
    banner("STEP C — SELF-ASSESS: the agent's OWN faculties, verbatim. The "
           "shell authors none of this.")
    print("  describe_self():")
    for line in agent.describe_self():
        print(f"      {line}")
    print("\n  ask_for_guidance() — what it perceives / tried / asks (verbatim):")
    g = agent.ask_for_guidance()
    print(f"      world it inhabits   : {g['world']}")
    print(f"      kinds it perceives  : {g['i_perceive_kinds']}")
    print(f"      actions it has tried: {g['actions_i_have_tried']}")
    print("      its self-report (describe()):")
    for line in g["my_report"]:
        print(f"          {line}")
    print(f"      it ASKS: \"{g['i_ask']}\"")
    print("\n  held_predicates() — its honest known-unknowns AFTER play "
          "(verbatim):")
    held = agent.held_predicates()
    if not held:
        print("      (none — it grounds everything it holds)")
    for h in held:
        awaits = ", ".join(nm for _uk, nm in h["awaits"]) or "—"
        print(f"      [CANNOT GROUND] {h['name']} ({h['predicate_kind']}) "
              f"awaits: {awaits}")
        q = agent.ask_about(h["name"])
        if q:
            print(f"          it asks: \"{q['i_ask']}\"")
    print("\n  resource self-report — compute_pressure() + op_stats over its "
          "ARC-bearing ops (verbatim):")
    cp = agent.compute_pressure()
    print(f"      compute_pressure (spent/limit): "
          f"{round(cp, 4) if cp is not None else None}")
    caps = agent.runtime_capabilities()
    for op in ("observe", "choose_action", "quality_of_position",
               "grow", "discover"):
        try:
            mean = caps["op_mean_cost"]({"of": op})
            cnt = caps["op_count"]({"of": op})
            print(f"      {op:22} mean_cost={mean:.4f} ms  count={cnt}")
        except Exception as exc:
            print(f"      {op:22} (faculty error: {exc})")

    sys.stdout.flush()
    # stash the agent for STEP C self-assessment in the same process.
    return 0, agent, {
        "game": args.game, "won_at": won_at, "best_score": best_score,
        "first_progress": first_progress,
        "score_perceived_at": score_perceived_at,
        "pursue_promoted_at": pursue_promoted_at,
        "pursue_adopted_at": pursue_adopted_at,
        "final_drives": final_drives,
        "transitions": len(transitions),
    }


if __name__ == "__main__":
    res = main(sys.argv[1:])
    raise SystemExit(res if isinstance(res, int) else res[0])
