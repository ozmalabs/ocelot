"""arc3_live_selfassess — ONE persistent fully-featured jabberwock plays the live
ARC-AGI-3 games in sequence, and BETWEEN EACH GAME performs a FULL SELF-ASSESSMENT
and a SELF-FIX, carrying both forward to the next game.

The discipline (CLAUDE.md + the proven self-diagnose loop): the agent assesses
ITSELF with its OWN faculties, and FIXES what it can with its OWN operators. The
shell only stages I/O and prints the agent's verdicts verbatim. Nothing here
authors an assessment or a fix.

  PLAY (live)   — the agent plays N live actions (thin shim, full stack), with a
                  read-only per-tick snapshot of its objective-AbS state (the
                  win-rule unification: provisional formed? surprise? SHIFT?).
  SELF-ASSESS   — the agent's OWN introspection, verbatim (the same suite as
                  jabberwock_self_assesses_arc_agi3_ability.py):
                    describe_self / drives / ask_for_guidance / held_predicates
                    + ask_about / impasses / op_stats(compute self-report).
  SELF-FIX      — the agent's OWN repair/consolidation operators, applied between
                  games and CARRIED FORWARD (one persistent agent):
                    insight(layer)  -> _reground_predicates (promote held
                                       predicates whose awaited percepts now
                                       exist) + grow
                    grow_gamma()    -> grow productions from accrued stats
                    discover_relations() / discover_theorems()
                  The shell reports the DELTAS (predicates regrounded, concepts /
                  productions / relations / theorems gained) — the fix is the
                  agent's; the shell measures it.
  SUPPLY        — whatever the agent STILL holds-but-cannot-ground after its own
                  fix is printed as its standing ASK (for the assistant to supply
                  by a genus it holds — the only allowed external input).

Key from os.environ['ARC_API_KEY'] only (load_arc_api_key, gitignored .env);
never printed.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["ARC3_THIN"] = "1"
os.environ["ARC3_FULL"] = "1"

from _arc3_load_key import load_arc_api_key  # noqa: E402
from arc3_live_env import Arc3LiveEnv, DEFAULT_BASE_URL  # noqa: E402
from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402
from domains.arc3_full_seed import install_full_seed_set  # noqa: E402
from domains.order_n_world_model import order_n_curiosity_weights  # noqa: E402
from arc3_live_experiment import (  # noqa: E402
    _live_legal_actions, _order_n_biased_menu, _changed_celltypes,
    _changed_cells, _list_games,
)

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP, flush=True)


def _objective_snapshot(agent):
    nid = getattr(agent, "_effect_objective_node", None)
    if nid is None:
        return None
    a = agent.mind_graph.node(nid).attrs
    return {
        "provisional": bool(a.get("provisional")),
        "support": int(a.get("support", 0)),
        "target_action": a.get("target_action"),
        "obj_synth_err_ema": round(float(a.get("synthesis_error_ema", 0.0)), 3),
    }


# ----------------------------------------------------------------------------
# PLAY one live game with the persistent agent. Returns the objective-AbS trace.
# ----------------------------------------------------------------------------
def play_live(agent, game_id, n_actions, coord_stride, seed, order_n=True):
    random.seed(seed)
    env = Arc3LiveEnv(game_id)
    handle = arc3_thin_handle(env, agent)
    agent.set_compute_limit(50.0 * float(n_actions))

    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    transitions, cell_transitions = [], []
    actions_chosen = Counter()
    best_score = ctx["score"]
    wins, avail_seen = [], set()
    curiosity_w = {}
    n_c6 = 0

    provisional_first = confirmed_at = None
    target_sequence, refute_events = [], []
    obj_surprise_trace, surprise_emotion_trace = [], []
    prev_target = None
    prev_disconfirmed = set()

    for i in range(n_actions):
        avail_seen.update(env.available_actions)
        actions = _live_legal_actions(handle, substrate, ctx, env, coord_stride)
        if not actions:
            actions = _live_legal_actions(handle, substrate, ctx, env, 1)
        if not actions:
            break
        if order_n:
            actions = _order_n_biased_menu(actions, curiosity_w, 8, random)

        action = agent.choose_action(substrate, ctx, actions, handle)
        chosen_kind = canonical_action_kind(action)
        actions_chosen[chosen_kind] += 1
        if chosen_kind.startswith("c6@"):
            n_c6 += 1

        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)

        q_before = agent.quality_of_position(substrate)
        pre = substrate
        substrate, ctx = handle["apply_action"](substrate, ctx, action)

        transitions.append((chosen_kind, _changed_celltypes(pre, substrate)))
        cell_transitions.append((chosen_kind, _changed_cells(pre, substrate)))

        agent.observe(substrate)
        q_after = agent.quality_of_position(substrate)
        agent.record_action_outcome(
            chosen_kind, agent.last_world_novelty,
            max(0.0, q_before - q_after), agent.boredom_count(substrate),
            ctx.get("tick", 0), terminal_delta=(1.0 if ctx["won"] else 0.0),
            frontier_after=agent.last_freshening_count,
        )

        snap = _objective_snapshot(agent)
        a_root = agent.mind_graph.node(agent.agent_root).attrs
        obj_surprise_trace.append(
            round(float(a_root.get("objective_synthesis_error", 0.0)), 3))
        surprise_emotion_trace.append(
            round(float(agent._emotion_sample("surprise")), 3))
        cur_target = snap["target_action"] if snap else None
        if cur_target is not None and cur_target != prev_target:
            target_sequence.append((i + 1, cur_target))
            prev_target = cur_target
        cur_dis = set(getattr(agent, "_winrule_disconfirmed_actions", set()))
        for a_dis in (cur_dis - prev_disconfirmed):
            refute_events.append((i + 1, a_dis))
        prev_disconfirmed = cur_dis
        if snap is not None:
            if snap["provisional"] and provisional_first is None:
                provisional_first = i + 1
            if (not snap["provisional"]) and confirmed_at is None:
                confirmed_at = i + 1

        if ctx["score"] > best_score:
            best_score = ctx["score"]
        if ctx["won"]:
            wins.append(i + 1)
            substrate, ctx = handle["reset"]()
            agent.observe(substrate)
            best_score = ctx["score"]

        if order_n and (i + 1) % 4 == 0:
            curiosity_w = order_n_curiosity_weights(cell_transitions)
        if (i + 1) % 8 == 0:
            agent.grow_gamma()
            agent.insight(layer=1)
        if (i + 1) % 16 == 0:
            agent.discover_relations()
            agent.discover_theorems()

    scorecard = None
    try:
        scorecard = env.close_scorecard()
    except Exception:
        pass

    restarts = getattr(env, "_restarts", 0)
    distinct = len({t for _, t in target_sequence})
    return {
        "game": game_id, "actions": len(transitions),
        "available_seen": sorted(avail_seen), "best_score": best_score,
        "wins": wins, "c6_clicks": n_c6, "actions_chosen": dict(actions_chosen),
        "provisional_first": provisional_first, "confirmed_at": confirmed_at,
        "target_sequence": target_sequence, "distinct_targets": distinct,
        "monomaniacal": distinct <= 1, "refute_events": refute_events,
        "obj_surprise_max": max(obj_surprise_trace) if obj_surprise_trace else 0.0,
        "obj_surprise_nonzero": sum(1 for v in obj_surprise_trace if v > 0.0),
        "surprise_emotion_max": max(surprise_emotion_trace) if surprise_emotion_trace else 0.0,
        "reset_restarts": restarts, "scorecard": scorecard,
    }


# ----------------------------------------------------------------------------
# SELF-ASSESS — the agent's OWN faculties, verbatim (no shell judgement).
# ----------------------------------------------------------------------------
def self_assess(agent, play):
    banner("SELF-ASSESS (the agent's OWN faculties, verbatim)")

    print("\n  -- this game's objective-AbS (the win-rule unification) --")
    print(f"    available_actions       : {play['available_seen']}")
    print(f"    best_score / wins        : {play['best_score']} / {play['wins']}"
          f"   (reset-retries={play['reset_restarts']})")
    print(f"    c6 clicks                : {play['c6_clicks']}  "
          f"kinds={play['actions_chosen']}")
    print(f"    provisional first / conf : {play['provisional_first']} / "
          f"{play['confirmed_at']}")
    print(f"    objective surprise       : max={play['obj_surprise_max']} "
          f"ticks>0={play['obj_surprise_nonzero']}/{play['actions']}")
    print(f"    pursued win-rule SHIFT   : {play['distinct_targets']} distinct "
          f"(monomaniacal={'YES' if play['monomaniacal'] else 'NO'})")
    print(f"    REFUTE events            : {play['refute_events']}")

    print("\n  -- describe_self() (verbatim) --")
    for line in agent.describe_self():
        print(f"    {line}")

    print("\n  -- ask_for_guidance() (verbatim) --")
    g = agent.ask_for_guidance()
    print(f"    world it inhabits        : {g['world']}")
    print(f"    kinds it perceives       : {g['i_perceive_kinds']}")
    tried = g['actions_i_have_tried']
    print(f"    actions it has tried     : {len(tried)} kinds: {tried[:12]}"
          f"{' ...' if len(tried) > 12 else ''}")
    print(f"    vocabulary size          : {len(g['my_vocabulary'])} concepts")
    print(f"    what it ASKS             : \"{g['i_ask']}\"")

    print("\n  -- held_predicates() : known-unknowns it CANNOT yet ground --")
    held = agent.held_predicates()
    if not held:
        print("    (none — it grounds everything it holds)")
    for h in held:
        awaits = ", ".join(nm for _uk, nm in h["awaits"]) or "—"
        print(f"    [CANNOT GROUND] {h['name']} ({h['predicate_kind']}) "
              f"— awaits: {awaits}")

    print("\n  -- impasses encountered --")
    print(f"    impasse count            : {len(agent.impasses())}")

    print("\n  -- op self-report (op_stats over ARC-bearing ops) --")
    stats = agent.op_stats()
    for op in ("observe", "choose_action", "quality_of_position", "grow",
               "discover", "routing"):
        st = stats.get(op)
        if st and st.get("count"):
            print(f"    {op:20} mean={st['total_ms']/max(st['count'],1):.3f}ms "
                  f"count={st['count']}")
    return held


# ----------------------------------------------------------------------------
# SELF-FIX — the agent's OWN operators, carried forward. Report deltas only.
# ----------------------------------------------------------------------------
def _counts(agent):
    from collections import Counter as C
    tc = C(n.type for n in agent.mind_graph.nodes())
    return {
        "Concept": len(agent._concept_nodes),
        "nodes": sum(tc.values()),
        "Production": tc.get("Production", 0),
        "held_predicates": len(agent.held_predicates()),
        "relations": tc.get("Relation", 0),
        "theorems": tc.get("Theorem", 0),
    }


def self_fix(agent):
    banner("SELF-FIX (the agent's OWN operators — carried forward to next game)")
    before = _counts(agent)

    # The agent's own repair/consolidation, run deliberately between games.
    regrounded = agent._reground_predicates()      # promote now-groundable holds
    ins = agent.insight(layer=2)                    # deeper insight + grow
    agent.grow_gamma()
    rels = agent.discover_relations()
    thms = agent.discover_theorems()

    after = _counts(agent)
    if isinstance(ins, dict):
        ins_summary = {k: (len(v) if hasattr(v, "__len__") else v)
                       for k, v in ins.items()}
    else:
        ins_summary = ins
    print(f"  predicates REGROUNDED      : {regrounded if regrounded else '—'}")
    print(f"  insight() report           : {ins_summary}")
    print(f"  new relations discovered   : {len(rels)}")
    print(f"  new theorems discovered    : {len(thms)}")
    print(f"  deltas (before -> after):")
    for k in before:
        d = after[k] - before[k]
        flag = "  <== changed" if d else ""
        print(f"    {k:18} {before[k]:6} -> {after[k]:6}  ({d:+d}){flag}")
    return after


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=None)
    ap.add_argument("--max-games", type=int, default=5)
    ap.add_argument("--actions", type=int, default=250)
    ap.add_argument("--coord-stride", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if not load_arc_api_key():
        print("BLOCKER: ARC_API_KEY not available; aborting.")
        return 2
    print(f"key present: True  (length={len(os.environ['ARC_API_KEY'])})")

    games = [args.game] if args.game else _list_games(DEFAULT_BASE_URL)[:args.max_games]

    banner("ONE PERSISTENT JABBERWOCK :: play -> self-assess -> self-fix per game")
    print(f"  games={len(games)}  actions={args.actions}  stride={args.coord_stride}")

    # Boot ONE agent — it persists across every game; fixes accumulate.
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    rep = install_full_seed_set(agent)
    print(f"  [ARC3_FULL] concepts {rep['concepts_before']} -> {rep['concepts_after']}"
          f"  seeds={rep['seeds_installed']}(fail={rep['seeds_failed']})")

    history = []
    for gi, g in enumerate(games):
        banner(f"GAME {gi+1}/{len(games)} : {g}  (PLAY {args.actions} live actions)")
        try:
            play = play_live(agent, g, args.actions, args.coord_stride, args.seed)
        except Exception as e:
            import traceback
            print(f"  ERROR {type(e).__name__}: {e}")
            traceback.print_exc()
            continue
        history.append(play)
        held = self_assess(agent, play)
        after = self_fix(agent)

        # SUPPLY — whatever it STILL cannot ground after its own fix is its
        # standing ask (assistant to supply by a held genus — the only allowed
        # external input). Printed so the gap is explicit and inspectable.
        still_held = agent.held_predicates()
        banner("SUPPLY — what it STILL asks for after self-fix (assistant input)")
        if not still_held:
            print("  (nothing — it grounded everything it held)")
        else:
            for h in still_held:
                q = agent.ask_about(h["name"])
                if q is None:
                    continue
                print(f"  · cannot ground '{q['i_cannot_ground']}' — lacks: "
                      f"{q['because_i_lack']}")
                print(f"    it asks: \"{q['i_ask']}\"")

    banner("RUN SUMMARY")
    print(f"  games played             : {len(history)}")
    print(f"  scored/won               : {[h['game'] for h in history if h['best_score']>0 or h['wins']]}")
    print(f"  objective FORMED         : {[h['game'] for h in history if h['provisional_first'] is not None]}")
    print(f"  hypothesis SHIFTED       : {[h['game'] for h in history if not h['monomaniacal']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
