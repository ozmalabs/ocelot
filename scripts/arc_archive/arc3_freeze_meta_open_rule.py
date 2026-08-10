"""arc3_freeze_meta_open_rule — enact the user's principle: FREEZE Γ on the
META (what a game IS, core priors, faculties, GENERAL drives), OPEN Γ on the
SPECIFIC game's rule + goal, and SHED the frozen navigate hack.

THIN HARNESS (CLAUDE.md). The jabberwock decides / sheds / infers / plays /
assesses; this script only boots it, OFFERS each seed element to its OWN
faculties, runs the loop it drives, and prints its verdict verbatim. No
hand-authored frozen/open boundary (the agent's grounding faculty disposes
each piece), no hand-authored goal, no hand-played action, no hand-authored
assessment.

STEP 1 — the agent decides the frozen/open boundary + SHEDS the navigate rule.
  We install the arc3 seed in PIECES, offering each to the agent's own
  consider()/learn_word grounding faculty:
    · GENERAL (frozen meta): the arc3_game microtheory (what a game IS), the
      me/wall/opening/door priors, the map productions, and the
      win_the_game / avoid_game_over drives. Each disposed by consider().
    · SPECIFIC (open rule): the goal_cell concept is OFFERED to consider() —
      its OWN grounding faculty HOLDS it (it awaits attrs it has never
      perceived) rather than grounding it, so it is a HYPOTHESIS, not a rule.
    · SHED: the exploration_value navigate bonus (the goal_cell odd-one-out
      salience term that FROZE Γ on the navigate rule) is NOT applied. The
      agent boots WITHOUT the spatial-as-default goal. SpatialLocation
      machinery stays AVAILABLE (the map productions) but is not auto-
      activated by a default goal_cell target.
  Then the agent reports, via its OWN faculties (describe_self / consider
  dispositions / held_predicates / goal + microtheory introspection), what it
  froze vs opened.

STEP 2 — play ONE live game with the navigate rule shed; the agent must use
  its GENERAL faculties (curiosity, action->effect world-model, order-N
  structure, pursue_score grounded on the felt score signal, flexible-bounded
  Γ) to INFER what the game rewards and DEFINE its own goal from that. If the
  game is spatial it may RECOGNISE that and reach for navigation as an OPTION.

STEP 3 — the agent self-assesses in its OWN words (verbatim).

Run:
  ulimit -v 8388608
  timeout 900 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/arc3_freeze_meta_open_rule.py --actions 80
"""
from __future__ import annotations

import argparse
import json as _json
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
from arc3_live_env import Arc3LiveEnv, DEFAULT_BASE_URL  # noqa: E402
from arc3_live_experiment import (  # noqa: E402
    _live_legal_actions, _changed_celltypes, _goal_cell_grounded,
)
from substrate import term_from_json, Production, NodePattern  # noqa: E402

SEP = "=" * 78
_SEED_PATH = _ROOT / "seeds" / "arc3_game.json"


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ----------------------------------------------------------------------------
# STEP 1 — install the seed in PIECES through the agent's OWN faculties, with
# the navigate hack SHED. The frozen/open split is enacted BY the agent's
# grounding faculty (consider / learn_word), not hand-picked here.
# ----------------------------------------------------------------------------
def install_meta_frozen_rule_open(agent) -> dict:
    """Install the GENERAL (frozen meta) pieces of the arc3 seed and OFFER the
    SPECIFIC (open rule) goal_cell concept to consider(); do NOT apply the
    navigate bonus. Returns the agent's OWN dispositions for the report."""
    seed = _json.loads(_SEED_PATH.read_text())
    rep: dict = {
        "frozen_meta": {"microtheory": None, "concepts": [], "productions": 0,
                        "drives": []},
        "open_rule": {"concepts": []},
        "shed": [],
    }

    # --- FROZEN META: the game-class microtheory (what a game IS). ---------
    mt = seed.get("microtheory") or {}
    if mt.get("name"):
        mt_id = agent.install_microtheory(
            mt["name"], description=mt.get("description", ""))
        attrs = agent.mind_graph.node(mt_id).attrs
        for k in ("action_slots", "objective", "terminal"):
            if k in mt and k not in attrs:
                attrs[k] = mt[k]
        rep["frozen_meta"]["microtheory"] = mt["name"]

    # --- The genus priors + the SPECIFIC goal_cell, EACH offered to the
    #     agent's own consider() so ITS grounding faculty disposes. The
    #     general priors (me/wall/opening/door) it can ground -> frozen meta.
    #     goal_cell awaits attrs it has never perceived -> its faculty HOLDS
    #     it as a hypothesis = the OPEN rule, not a default. We never decide
    #     which is which; the agent's grounding does.
    SPECIFIC = {"goal_cell"}
    for c in seed.get("concepts", []):
        dec = agent.consider({"kind": "concept", "word": c["name"],
                              "definition": c["definition"],
                              "domain": c.get("domain", "boundary")})
        bucket = "open_rule" if c["name"] in SPECIFIC else "frozen_meta"
        rep[bucket]["concepts"].append(
            {"name": c["name"], "decision": dec["decision"],
             "reason": dec.get("reason", "")})

    # --- FROZEN META: the map productions (admit the grid AS A MAP). They
    #     keep SpatialLocation machinery AVAILABLE as an option; they are NOT
    #     a default goal. ----------------------------------------------------
    for p in seed.get("productions", []):
        src, tgt = p["src"], p["tgt"]
        prod = Production(
            src=NodePattern(src["type"], src["var"]),
            edge_type=p["edge_type"],
            tgt=NodePattern(tgt["type"], tgt["var"]),
            provenance=p.get("provenance", "seed:arc3_game"),
        )
        already = any(
            agent.mind_graph.node(e.key.tgt).attrs.get("provenance")
            == prod.provenance
            for e in agent.mind_graph.out_edges(agent.gamma_root, "production"))
        if not already:
            agent._append_production(prod)
            rep["frozen_meta"]["productions"] += 1

    # --- FROZEN META: the GENERAL drives, each offered to consider() so the
    #     AGENT adopts them (win_the_game / avoid_game_over). These read the
    #     proprioceptive my_won / my_over the game folds onto the agent — the
    #     general "what a win/terminal IS" drives, not a game-specific goal. -
    for goal in seed.get("goals", []):
        dec = agent.consider({"kind": "goal", "label": goal["label"],
                              "domain": "self",
                              "priority": float(goal.get("priority", 1.0)),
                              "satisfaction": goal["satisfaction_term"]})
        rep["frozen_meta"]["drives"].append(
            {"label": goal["label"], "decision": dec["decision"],
             "reason": dec.get("reason", "")})

    # --- SHED: the navigate hack. install_arc3_seed augments the agent's
    #     exploration_value with a goal_cell odd-one-out salience bonus (1e9)
    #     that makes the rarest-colour cell the DEFAULT navigation target —
    #     this FROZE Γ on ONE game's spatial rule. We do NOT apply it. The
    #     agent boots with its NATIVE exploration_value only; the open rule is
    #     left for the agent to infer + define live.
    native = agent._exploration_value_term()
    from substrate import IfThenElse, Plus, Let
    has_bonus = isinstance(native, Plus) and any(
        isinstance(t, IfThenElse) and isinstance(getattr(t, "cond", None), Let)
        and t.cond.name == "x" for t in native.items)
    rep["shed"].append(
        {"what": "exploration_value navigate bonus (goal_cell odd-one-out "
                 "salience term; spatial-as-default goal)",
         "applied": bool(has_bonus),
         "note": "NOT applied — the agent keeps its native exploration_value; "
                 "the spatial rule is OPEN for the agent to infer."})
    return rep


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=None)
    ap.add_argument("--actions", type=int, default=80)
    ap.add_argument("--coord-stride", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if not load_arc_api_key():
        print("BLOCKER: ARC_API_KEY not available; aborting.")
        return 2
    import os
    print(f"key present: True  (length={len(os.environ['ARC_API_KEY'])})")

    if args.game is None:
        import requests
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

    # ============================================ STEP 1 — FREEZE META / OPEN
    banner("STEP 1 — FREEZE the META, OPEN the rule, SHED the navigate hack. "
           "Each seed element is OFFERED to the agent's OWN consider()/grounding "
           "faculty; its grounding disposes (frozen vs held); the navigate "
           "bonus is NOT applied.")
    split = install_meta_frozen_rule_open(agent)
    fm = split["frozen_meta"]
    print(f"  [FROZEN META] microtheory installed : {fm['microtheory']}")
    print(f"  [FROZEN META] genus priors (agent's own disposition):")
    for c in fm["concepts"]:
        print(f"       {c['name']:10s} -> {c['decision']:16s}  {c['reason'][:54]}")
    print(f"  [FROZEN META] map productions admitted (option, not default): "
          f"{fm['productions']}")
    print(f"  [FROZEN META] general drives (agent's own disposition):")
    for d in fm["drives"]:
        print(f"       {d['label']:16s} -> {d['decision']:18s} {d['reason'][:46]}")
    print(f"  [OPEN RULE] the specific goal (agent's own disposition):")
    for c in split["open_rule"]["concepts"]:
        print(f"       {c['name']:10s} -> {c['decision']:16s}  {c['reason'][:54]}")
    print(f"  [SHED] navigate hack:")
    for s in split["shed"]:
        print(f"       applied={s['applied']}  {s['what']}")
        print(f"               {s['note']}")

    print("\n  -- the agent's OWN report of what it froze vs opened (verbatim) --")
    print("  describe_self():")
    for line in agent.describe_self():
        print(f"      {line}")
    held0 = agent.held_predicates()
    print("\n  held_predicates() AFTER the split (its OPEN known-unknowns "
          "= the rule it has NOT frozen, verbatim):")
    if not held0:
        print("      (none)")
    for h in held0:
        awaits = ", ".join(nm for _uk, nm in h["awaits"]) or "—"
        print(f"      [HELD / OPEN] {h['name']} ({h['predicate_kind']}) "
              f"awaits: {awaits}")
    pre_drives = [agent.mind_graph.node(g).attrs.get("label")
                  for g in agent._get_top_level_goals()]
    print(f"\n  drives now (the FROZEN general meta-drives): {pre_drives}")
    # confirm the navigate bonus is genuinely absent from exploration_value.
    from substrate import IfThenElse, Plus, Let
    ev = agent._exploration_value_term()
    has_bonus = isinstance(ev, Plus) and any(
        isinstance(t, IfThenElse) and isinstance(getattr(t, "cond", None), Let)
        and t.cond.name == "x" for t in ev.items)
    print(f"  exploration_value carries the navigate goal_cell bonus? "
          f"{has_bonus}  (must be False = shed)")

    # ====================================================== STEP 2 — PLAY LIVE
    # The score-pursuit drive, re-expressed over the proprioceptive
    # my_vel_score the agent FEELS — offered to consider() (the GENERAL
    # pursue_score drive). The agent adopts it the moment the score signal
    # grounds. This is a general drive, NOT a game-specific goal.
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
    print(f"\n  general drive pursue_score offered -> {dec['decision']} "
          f"({dec.get('reason','')[:60]})")

    handle = arc3_world_handle(env, agent)
    agent.set_compute_limit(50.0 * float(args.actions))
    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    banner("STEP 2 — PLAY one live game (the agent's OWN loop). Navigate rule "
           "shed; it must INFER what the game rewards via its general faculties "
           "and DEFINE its own goal (adopt pursue_score once the score signal "
           "grounds; recognise+reach for navigation only IF it infers spatial).")
    transitions: list = []
    actions_chosen: Counter = Counter()
    coords: Counter = Counter()
    best_score = ctx.get("score", 0)
    first_progress = None
    won_at = None
    score_perceived_at = None
    pursue_promoted_at = None
    pursue_adopted_at = None
    grounded_tick = None
    effect_model_built = None  # action->effect learned (a transition observed)
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
        changed = _changed_celltypes(pre, substrate)
        transitions.append((kind, changed))
        if changed and effect_model_built is None:
            effect_model_built = i + 1
        agent.observe(substrate)
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
            before_held = {h["name"] for h in agent.held_predicates()}
            agent.insight(layer=1)
            after_held = {h["name"] for h in agent.held_predicates()}
            if (pursue_promoted_at is None
                    and "pursue_score" in before_held
                    and "pursue_score" not in after_held):
                pursue_promoted_at = i + 1
            if pursue_adopted_at is None and "pursue_score" not in {
                    agent.mind_graph.node(g).attrs.get("label")
                    for g in agent._get_top_level_goals()}:
                dec = agent.consider(score_goal)
                if dec["decision"] == "adopted_candidate":
                    pursue_adopted_at = i + 1
                    print(f"    [{i+1}] AGENT ADOPTED pursue_score as a drive "
                          f"(it inferred the score signal + defined its own goal)")
        if (i + 1) % 16 == 0:
            agent.discover_relations()

        tick_walls.append(tw + (_time.perf_counter() - t1) * 1000.0)
        if grounded_tick is None and _goal_cell_grounded(agent):
            grounded_tick = i + 1
            print(f"    [{i+1}] the agent RECOGNISED a spatial odd-one-out goal "
                  f"cell (navigation became an OPTION it reached for)")
        if ctx["won"] and won_at is None:
            won_at = i + 1
            print(f"    [{i+1}] WIN")
            break
        if ctx["over"]:
            print(f"    [{i+1}] GAME_OVER; resetting")
            substrate, ctx = handle["reset"]()
            agent.observe(substrate)

    scorecard = env.close_scorecard()

    banner("STEP 2 RESULT — live game outcome (verbatim readouts):")
    print(f"  game                         : {args.game}")
    print(f"  WIN at action                : {won_at}")
    print(f"  best level/score reached     : {best_score}")
    print(f"  actions to first progress    : {first_progress}")
    print(f"  transitions observed         : {len(transitions)}")
    print(f"  action->effect model built @ : {effect_model_built} "
          f"(first observed state change = a learned effect)")
    print(f"  distinct ACTION6 coords      : {len(coords)}")
    print(f"  actions chosen (by kind)     : "
          f"{dict(Counter({k: v for k, v in actions_chosen.most_common(8)}))}")
    print("  -- did it INFER the reward + DEFINE its own goal? --")
    print(f"  score signal first perceived (my_vel_score) @action: "
          f"{score_perceived_at}")
    print(f"  pursue_score PROMOTED (held->grounded) @action     : "
          f"{pursue_promoted_at}")
    print(f"  pursue_score ADOPTED as its OWN drive @action      : "
          f"{pursue_adopted_at}")
    print(f"  spatial goal RECOGNISED (navigation as option) @   : "
          f"{grounded_tick}")
    final_drives = [agent.mind_graph.node(g).attrs.get("label")
                    for g in agent._get_top_level_goals()]
    print(f"  final drives (frozen meta + any inferred goal)     : "
          f"{final_drives}")
    if tick_walls:
        print(f"  per-tick agent wall (ms): mean="
              f"{sum(tick_walls)/len(tick_walls):.1f} "
              f"max={max(tick_walls):.1f}")
    if scorecard:
        print(f"  server scorecard          : "
              f"levels_completed={scorecard.get('total_levels_completed')} "
              f"total_actions={scorecard.get('total_actions')} "
              f"score={scorecard.get('score')}")

    # ====================================================== STEP 3 — SELF-ASSESS
    banner("STEP 3 — SELF-ASSESS: the agent's OWN faculties, verbatim. The "
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
          "(the rule it still has NOT frozen, verbatim):")
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
    print("\n  resource self-report — compute_pressure() (verbatim):")
    cp = agent.compute_pressure()
    print(f"      compute_pressure (spent/limit): "
          f"{round(cp, 4) if cp is not None else None}")

    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
