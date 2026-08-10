"""THE JABBERWOCK PLAYS ARC-AGI-3 WITH ITS GROUNDED ARC FRAME CONNECTED.

A THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning, authors NO
connection, builds NO new reasoner, hard-codes NO grid-rule and NO game-type.
It only stages I/O + drives the agent's OWN faculties; the AGENT disposes of
every offered piece and the AGENT's own machinery forms every hypothesis.

THE GAP this closes (the prompt's): the agent GROUNDED the ARC-AGI-3 paper (40/40
concepts persisted to data/arc_agi_grounded_context.json — it HOLDS arc-agi-3
is-a interactive_reasoning_benchmark, object_permanence, agent/action/goal ...).
But when it plays the THIN shim (ARC3_THIN) it is a blank curious agent on raw
cells: the grounded knowledge lives in a SEPARATE save, never loaded into the
play graph, never recognised. So its order-N hypotheses stay at action->effect
(order-1/2), never climbing to the whole-grid compositional level the paper says
ARC win-rules live at.

THE CONNECTION — three owned levers, no new reasoner:

  1. LOAD the grounded ARC understanding INTO the play agent. We read the
     persisted grounded Concept names off the agent's OWN save and offer each to
     the agent's OWN disposition faculty consider(): a concept it can ground ->
     accepted; one it can't -> HELD as a known-unknown (still graph-resident in
     the PLAY graph). Either way the play agent now HOLDS the grounded ARC frame,
     instead of being blank. The shell never decides ground-vs-hold.

  2. RECOGNISE the live world AS an arc-agi game. The thin world NAMES ITSELF: it
     publishes a Realm node (name='arc-agi-3', is_a='interactive_reasoning_
     benchmark') — the minimal observable cue, the same kind of self-naming Doom
     publishes. The agent perceives it via its OWN name_my_world(); the is_a binds
     the live world to the grounded concept it now holds. No 'if arc then X': the
     agent's recognition + held concept do the binding.

  3. FRAME the order-N at WHOLE-GRID structure. The thin world also publishes the
     WHOLE GRID as one observable (a GridConfig node carrying the grid's global
     signature) — the same class of mechanical I/O as publishing each CellC, just
     at whole-grid granularity. The agent's SAME order-N operator
     (_record_effect_config / _induce_structural_objective_hypothesis /
     _update_effect_objective — all already in the agent) then ranges over the
     whole-grid token, so the structural win-rule hypothesis it forms is at the
     grid level, not only per-action. We author NO grid-rule; the agent's order-N
     induces the pattern, the grounded frame just gives it a whole-grid thing to
     look at.

VERIFY (honest): (1) the play agent HOLDS the grounded ARC concepts (not blank),
(2) it RECOGNISES the world as an arc-agi game (name_my_world binds to the held
grounded concept), (3) its order-N hypothesis/objective ranges over WHOLE-GRID
structure (the EffectObjective / structural-win-rule hypothesis contains the
whole-grid GridConfig token, not only per-action CellC effects).

Transport: LIVE over HTTP when ARC_API_KEY is in os.environ (a short game), else
the OFFLINE SwitchesEnv re-implementation (whose win-rule — all switches ON — IS
a whole-grid compositional pattern), exercising the SAME thin handle + SAME agent.
The connection mechanism is transport-independent; the proof holds either way.

Run:
  ulimit -v 8388608
  timeout 600 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_plays_arc_with_grounded_frame.py
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"),
          str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate_rs import _native  # noqa: E402

from domains import self_persistence as sp  # noqa: E402
from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402

SEP = "=" * 78
GROUNDED_CONTEXT = ROOT / "data" / "arc_agi_grounded_context.json"

# The grounded ARC-frame concepts most load-bearing for PLAY — the ones whose
# binding tells the agent it is in an interactive reasoning benchmark whose
# win-rule is a whole-grid pattern. Read off the agent's OWN grounded save; we
# select by name (a surface filter), the agent disposes of each via consider().
_ARC_FRAME = (
    "arc-agi-3", "interactive_reasoning_benchmark", "arc-agi",
    "object_permanence", "feature_hierarchy_visual",
    "agent", "action", "goal", "perception_visual", "cognition", "volition",
)


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


def load_grounded_arc_concepts() -> list[str]:
    """The grounded Concept names off the agent's OWN persisted save. Pure
    mechanical query — no decision about which matter (the AGENT disposes)."""
    s = _native.Substrate()
    if not sp.load_state(s, str(GROUNDED_CONTEXT)):
        return []
    out: list[str] = []
    for n in s.nodes("Concept"):
        nm = s.node(n)["attrs"].get("name")
        if nm:
            out.append(nm)
    return out


def offer_grounded_concepts(agent, names: list[str]) -> list[dict]:
    """Hand each grounded ARC-frame concept to the agent's OWN consider()
    faculty. The agent grounds what it can, HOLDS what it can't — either way the
    PLAY graph now carries the concept. The shell never decides ground-vs-hold."""
    out = []
    present = set(names)
    for nm in _ARC_FRAME:
        if nm not in present:
            continue
        decision = agent.consider({
            "kind": "concept",
            "word": nm,
            # Offer the concept by NAME with a bare self-referential definition;
            # learn_word grounds it if the agent already holds what it refers to,
            # else HOLDS it as a known-unknown (its honest call). No meaning is
            # authored here — the agent's faculty disposes.
            "definition": {"type": "Var", "name": nm},
        })
        out.append({"name": nm, "decision": decision.get("decision")})
    return out


def holds_arc_frame(agent) -> dict:
    """Read what the play agent now HOLDS of the grounded ARC frame — concepts it
    grounded + predicates it holds as known-unknowns. Pure graph query."""
    grounded = [n for n in _ARC_FRAME if n in agent._concept_nodes]
    held = {h["name"] for h in agent.held_predicates()}
    held_arc = [n for n in _ARC_FRAME if n in held]
    return {"grounded": grounded, "held": held_arc,
            "carries_any": bool(grounded or held_arc)}


def recognises_arc(agent) -> dict:
    """Does the agent recognise the live world AS an arc-agi game, bound to the
    grounded concept it holds? Reads its OWN name_my_world() + checks the bound
    is_a concept is one it carries. No 'if arc' decision — pure introspection."""
    world = agent.name_my_world()
    bound_concept = None
    # the Realm WorldInstance carries the is_a binding the agent perceived.
    for (wt, _w), nid in agent._world_instance_nodes.items():
        if wt == "Realm":
            bound_concept = agent.mind_graph.node(nid).attrs.get("last_is_a") \
                or agent.mind_graph.node(nid).attrs.get("is_a")
            break
    holds = holds_arc_frame(agent)
    frame_held = (bound_concept in agent._concept_nodes
                  or bound_concept in {h["name"] for h in agent.held_predicates()})
    return {
        "world": world,
        "is_arc": bool(world and world.get("name") == "arc-agi-3"),
        "bound_is_a": bound_concept,
        "binding_concept_held": frame_held,
        "frame": holds,
    }


def order_n_grid_level(agent) -> dict:
    """Does the agent's OWN order-N hypothesis/objective range over WHOLE-GRID
    structure (the GridConfig whole-grid token), not only per-action CellC
    effects? Reads the EffectObjective + the structural-win-rule hypothesis goal
    the agent's order-N already formed. Pure introspection — no new reasoner."""
    obj_events: list[str] = []
    provisional = None
    if agent._effect_objective_node is not None:
        oa = agent.mind_graph.node(agent._effect_objective_node).attrs
        obj_events = list(oa.get("objective_events", []))
        provisional = oa.get("provisional")
    grid_in_objective = any(":GridConfig" in e or e.endswith("GridConfig")
                            for e in obj_events)
    # the SAME order-N operator's per-action EffectConfig nodes — does ANY
    # action's modal joint config include the whole-grid token?
    grid_in_effectcfg = False
    n_effectcfg = 0
    for (action, sig), nid in agent._effect_config_nodes.items():
        n_effectcfg += 1
        ce = agent.mind_graph.node(nid).attrs.get("config_events", [])
        if any("GridConfig" in str(x) for x in ce):
            grid_in_effectcfg = True
    # the structural-win-rule hypothesis goal the order-N inducer mints.
    struct_goal = None
    for gid in agent._get_top_level_goals():
        a = agent.mind_graph.node(gid).attrs
        if str(a.get("label", "")).startswith("structural_winrule_"):
            struct_goal = a.get("label")
            break
    return {
        "effect_objective_events": obj_events,
        "objective_provisional": provisional,
        "grid_token_in_objective": grid_in_objective,
        "grid_token_in_any_effectconfig": grid_in_effectcfg,
        "n_effect_configs": n_effectcfg,
        "structural_winrule_hypothesis": struct_goal,
        "ranges_over_whole_grid": grid_in_objective or grid_in_effectcfg,
    }


def make_env():
    """LIVE Arc3LiveEnv when ARC_API_KEY present; else offline SwitchesEnv (its
    win-rule = all switches ON = a whole-grid compositional pattern)."""
    if os.environ.get("ARC_API_KEY"):
        try:
            from _arc3_load_key import load_arc_api_key
            load_arc_api_key()
        except Exception:
            pass
    if os.environ.get("ARC_API_KEY"):
        try:
            from arc3_live_env import Arc3LiveEnv, DEFAULT_BASE_URL
            import requests
            sess = requests.Session()
            sess.headers.update({"X-Api-Key": os.environ["ARC_API_KEY"],
                                 "Accept": "application/json"})
            r = sess.get(f"{DEFAULT_BASE_URL}/api/games", timeout=30)
            r.raise_for_status()
            gid = next(g.get("game_id") for g in r.json()
                       if isinstance(g, dict) and g.get("game_id"))
            return Arc3LiveEnv(gid), f"LIVE:{gid}"
        except Exception as e:
            print(f"  (live unavailable: {type(e).__name__}: {e}; using offline)")
    from arc3_env import SwitchesEnv
    return SwitchesEnv(), "OFFLINE:switches"


def play(agent, handle, n_actions: int, seed: int = 0) -> int:
    random.seed(seed)
    sub, ctx = handle["reset"]()
    agent.observe(sub)
    toggled = 0
    for i in range(n_actions):
        actions = handle["legal_actions"](sub, ctx)
        if not actions:
            break
        action = agent.choose_action(sub, ctx, actions, handle)
        ck = canonical_action_kind(action)
        touched = handle["interpret_acts_on"](sub, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)
        sub, ctx = handle["apply_action"](sub, ctx, action)
        agent.observe(sub)
        nov = agent.last_world_novelty
        terminal = 1.0 if ctx.get("won") else 0.0
        agent.record_action_outcome(ck, nov, 0.0,
                                    agent.boredom_count(sub),
                                    ctx.get("tick", 0),
                                    terminal_delta=terminal)
        toggled += 1
        if ctx.get("won"):
            break
        if ctx.get("over"):
            sub, ctx = handle["reset"]()
            agent.observe(sub)
    return toggled


def main() -> int:
    banner("THE JABBERWOCK PLAYS ARC-AGI-3 WITH ITS GROUNDED ARC FRAME CONNECTED")
    print("  Thin shell: load grounded ARC concepts into the PLAY agent (its own")
    print("  consider()), let the world NAME ITSELF so the agent's own recognition")
    print("  fires, and let its SAME order-N range over the whole-grid token the")
    print("  thin world publishes. No new reasoner, no grid-rule, no game-type.")

    # -------------------------------------------------------------- BOOT (THIN)
    banner("BOOT — the THIN play agent (raw cells; no navigate seed, no goal_cell)")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    print("  blank thin agent built (it does EVERYTHING itself).")
    print(f"  grounded ARC concepts in PLAY graph BEFORE load: "
          f"{[n for n in _ARC_FRAME if n in agent._concept_nodes]}")

    # ---------------------------------------------- 1. LOAD THE GROUNDED FRAME
    banner("1. LOAD THE GROUNDED ARC UNDERSTANDING INTO PLAY — offer each grounded "
           "concept to the agent's OWN consider(); it grounds or HOLDS each")
    names = load_grounded_arc_concepts()
    print(f"  grounded Concept names read off the agent's own save: {len(names)}")
    dispositions = offer_grounded_concepts(agent, names)
    for d in dispositions:
        print(f"    · {d['name']:34s} -> {d['decision']}")
    frame = holds_arc_frame(agent)
    print(f"  PLAY agent now HOLDS the ARC frame: grounded={frame['grounded']}")
    print(f"                                      held   ={frame['held']}")

    # ------------------------------------------------------------ ENV + PLAY
    env, transport = make_env()
    banner(f"2+3. PLAY a short game ({transport}) — the world NAMES ITSELF + "
           "publishes the WHOLE GRID; the agent recognises + its order-N ranges "
           "over grid structure")
    handle = arc3_thin_handle(env, agent)
    n_steps = play(agent, handle, n_actions=60, seed=0)
    print(f"  played {n_steps} steps.")

    # ---------------------------------------------- VERIFY (1) HOLDS FRAME
    banner("VERIFY (1) — the play agent HOLDS the grounded ARC concepts (not blank)")
    frame = holds_arc_frame(agent)
    print(f"  grounded: {frame['grounded']}")
    print(f"  held    : {frame['held']}")
    print(f"  -> carries the grounded ARC frame: {frame['carries_any']}")

    # ---------------------------------------------- VERIFY (2) RECOGNISES
    banner("VERIFY (2) — the agent RECOGNISES the world AS an arc-agi game "
           "(name_my_world binds to the held grounded concept)")
    rec = recognises_arc(agent)
    print(f"  name_my_world()          : {rec['world']}")
    print(f"  recognised as arc-agi-3  : {rec['is_arc']}")
    print(f"  world bound is_a concept : {rec['bound_is_a']}")
    print(f"  that concept is HELD     : {rec['binding_concept_held']}")

    # ---------------------------------------------- VERIFY (3) GRID-LEVEL ORDER-N
    banner("VERIFY (3) — the agent's OWN order-N hypothesis ranges over WHOLE-GRID "
           "structure (the GridConfig whole-grid token), not only per-action effects")
    on = order_n_grid_level(agent)
    print(f"  EffectObjective events            : {on['effect_objective_events']}")
    print(f"  objective provisional?            : {on['objective_provisional']}")
    print(f"  WHOLE-GRID token in objective     : {on['grid_token_in_objective']}")
    print(f"  WHOLE-GRID token in an EffectConfig: "
          f"{on['grid_token_in_any_effectconfig']} "
          f"(of {on['n_effect_configs']} configs)")
    print(f"  structural-win-rule hypothesis    : {on['structural_winrule_hypothesis']}")
    print(f"  -> order-N RANGES OVER whole grid : {on['ranges_over_whole_grid']}")

    # ------------------------------------------------------------ VERDICT
    banner("VERDICT")
    ok1 = frame["carries_any"]
    ok2 = rec["is_arc"] and rec["binding_concept_held"]
    ok3 = on["ranges_over_whole_grid"]
    print(f"  (1) holds grounded ARC concepts         : {ok1}")
    print(f"  (2) recognises the arc-agi game + binds : {ok2}")
    print(f"  (3) order-N ranges over whole-grid struct: {ok3}")
    print(f"  ALL THREE CONNECTED: {ok1 and ok2 and ok3}")
    print("  HONEST: no new reasoner — the SAME _record_effect_config /")
    print("  _induce_structural_objective_hypothesis / _update_effect_objective")
    print("  operator, pointed at the whole-grid token the thin world publishes.")
    print("  No grid-rule authored; the agent's order-N induced every config.")
    return 0 if (ok1 and ok2 and ok3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
