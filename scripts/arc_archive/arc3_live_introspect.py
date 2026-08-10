"""arc3_live_introspect — the LIVE ARC-AGI-3 transport (Arc3LiveEnv), full stack,
but the per-action loop SNAPSHOTS the agent's own objective-AbS state every tick
so we can read out, ON LIVE GAMES, whether the unified win-rule objective:
  (a) forms a provisional hypothesis at all (does any action repeat to modal>=2),
  (b) generates objective-level synthesis error (surprise) while it stays
      unrewarded, and
  (c) SHIFTS the pursued win-rule across candidates (refute -> next), rather than
      fixating monomaniacally — the exact behaviour the unification was meant to
      give on live games, where the reward path never confirms.

Boot + loop are byte-faithful to ``run_curious_live`` (install_full_seed_set +
arc3_thin_handle + _live_legal_actions stride menu + order-N menu biasing). The
ONLY additions are read-only snapshots of the agent's OWN nodes each tick — the
same fields ``arc3_switches_offline_introspect`` reads — and the live transport
(real HTTP env) over the live /api/games list. No new reasoning, no decision.

Key from os.environ['ARC_API_KEY'] only (loaded by load_arc_api_key from the
gitignored .env); its value is NEVER printed.
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


def _objective_snapshot(agent):
    nid = getattr(agent, "_effect_objective_node", None)
    if nid is None:
        return None
    a = agent.mind_graph.node(nid).attrs
    return {
        "provisional": bool(a.get("provisional")),
        "support": int(a.get("support", 0)),
        "n_events": len(a.get("objective_events", [])),
        "target_action": a.get("target_action"),
        "obj_synth_err_ema": round(float(a.get("synthesis_error_ema", 0.0)), 3),
        "abs_passes": int(a.get("abs_passes", 0)),
    }


def play_game(game_id: str, n_actions: int, coord_stride: int, seed: int,
              order_n: bool = True):
    random.seed(seed)
    env = Arc3LiveEnv(game_id)
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    rep = install_full_seed_set(agent)
    handle = arc3_thin_handle(env, agent)
    agent.set_compute_limit(50.0 * float(n_actions))

    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    transitions = []
    cell_transitions = []
    actions_chosen = Counter()
    best_score = ctx["score"]
    wins = []
    avail_seen = set()
    curiosity_w = {}

    provisional_first = None
    confirmed_at = None
    target_sequence = []            # (action_idx, pursued win-rule target)
    refute_events = []              # (action_idx, action_disconfirmed)
    obj_surprise_trace = []
    surprise_emotion_trace = []
    prev_target = None
    prev_disconfirmed = set()
    n_c6_clicked = 0

    for i in range(n_actions):
        avail_seen.update(env.available_actions)
        actions = _live_legal_actions(handle, substrate, ctx, env, coord_stride)
        if not actions:
            actions = _live_legal_actions(handle, substrate, ctx, env, 1)
        if not actions:
            break
        if order_n:
            actions = _order_n_biased_menu(actions, curiosity_w, k_explore=8,
                                           rng=random)

        action = agent.choose_action(substrate, ctx, actions, handle)
        chosen_kind = canonical_action_kind(action)
        actions_chosen[chosen_kind] += 1
        if chosen_kind.startswith("c6@"):
            n_c6_clicked += 1

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

        # --- read-only introspection of the agent's OWN objective-AbS state ---
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

    distinct_targets = len({t for _, t in target_sequence})
    nz_surprise = sum(1 for v in obj_surprise_trace if v > 0.0)
    held = agent._held_winrule()
    return {
        "game": game_id,
        "actions": len(transitions),
        "seq_probes_constructed": getattr(agent, "_seq_probes_constructed", 0),
        "implied_rules": len(getattr(agent, "_implied_rule_nodes", {})),
        "held_winrule": (held[1] if held else None),
        "available_seen": sorted(avail_seen),
        "best_score": best_score,
        "wins": wins,
        "c6_clicks": n_c6_clicked,
        "actions_chosen": dict(actions_chosen),
        "provisional_first": provisional_first,
        "confirmed_at": confirmed_at,
        "target_sequence": target_sequence,
        "distinct_targets": distinct_targets,
        "monomaniacal": distinct_targets <= 1,
        "refute_events": refute_events,
        "obj_surprise_max": max(obj_surprise_trace) if obj_surprise_trace else 0.0,
        "obj_surprise_ticks_nonzero": nz_surprise,
        "surprise_emotion_max": max(surprise_emotion_trace) if surprise_emotion_trace else 0.0,
        "final_objective": _objective_snapshot(agent),
        "concepts": rep.get("concepts_after"),
        "scorecard": scorecard,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=None)
    ap.add_argument("--max-games", type=int, default=5)
    ap.add_argument("--actions", type=int, default=300)
    ap.add_argument("--coord-stride", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if not load_arc_api_key():
        print("BLOCKER: ARC_API_KEY not available; aborting.")
        return 2
    print(f"key present: True  (length={len(os.environ['ARC_API_KEY'])})")

    if args.game:
        games = [args.game]
    else:
        games = _list_games(DEFAULT_BASE_URL)[:args.max_games]

    print("=== ARC-3 LIVE INTROSPECT :: objective-AbS unification on live games ===")
    print(f"games={len(games)}  actions={args.actions}  coord_stride={args.coord_stride}")

    results = []
    for gi, g in enumerate(games):
        print(f"\n---- game {gi+1}/{len(games)}: {g} ----", flush=True)
        try:
            r = play_game(g, args.actions, args.coord_stride, args.seed)
        except Exception as e:
            print(f"    ERROR {type(e).__name__}: {e}")
            continue
        results.append(r)
        print(f"  available_actions seen : {r['available_seen']}")
        print(f"  best_score             : {r['best_score']}   wins={r['wins']}")
        print(f"  c6 clicks chosen       : {r['c6_clicks']}  "
              f"(action kinds: {r['actions_chosen']})")
        print(f"  sequence probes built  : {r['seq_probes_constructed']} "
              f"(PhiMap-covered compositional tests)")
        print(f"  implied rules / WIN-RULE: {r['implied_rules']} rules, "
              f"held win-rule target = {r['held_winrule']}")
        print(f"  -- objective-AbS (the unification under test) --")
        print(f"    provisional first seen : {r['provisional_first']}")
        print(f"    confirmed at           : {r['confirmed_at']}")
        print(f"    objective surprise     : max={r['obj_surprise_max']} "
              f"ticks>0={r['obj_surprise_ticks_nonzero']}/{r['actions']}")
        print(f"    surprise emotion max   : {r['surprise_emotion_max']}")
        print(f"    pursued win-rule SHIFT : {r['distinct_targets']} distinct "
              f"(monomaniacal={'YES' if r['monomaniacal'] else 'NO'})")
        for idx, tgt in r['target_sequence']:
            print(f"        @{idx}: {tgt}")
        print(f"    REFUTE events          : {r['refute_events']}")
        print(f"    final objective        : {r['final_objective']}")
        sc = r["scorecard"]
        if sc:
            print(f"  server scorecard         : "
                  f"levels_completed={sc.get('total_levels_completed')} "
                  f"score={sc.get('score')}")

    print("\n================ SUMMARY ================")
    scored = [r for r in results if r["best_score"] > 0 or r["wins"]]
    shifted = [r for r in results if not r["monomaniacal"]]
    formed = [r for r in results if r["provisional_first"] is not None]
    print(f"  games played             : {len(results)}")
    print(f"  games that SCORED/won    : {[r['game'] for r in scored]}")
    print(f"  games where objective FORMED: {[r['game'] for r in formed]}")
    print(f"  games where hypothesis SHIFTED (non-monomaniacal): "
          f"{[r['game'] for r in shifted]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
