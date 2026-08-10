"""arc3_switches_offline_introspect — same fully-featured fixed agent on the
OFFLINE `switches` env, but the measurement loop CONTINUES PAST the first win
(resetting the episode) and SNAPSHOTS the agent's own EffectObjective node every
tick, so we can read out the provisional -> reward-confirmed takeover and whether
the agent RE-DRIVES the confirmed objective to win deliberately.

Boot is byte-identical to the live ARC3_FULL=1 path:
    install_full_seed_set(agent)  +  arc3_thin_handle(env, agent)
and the per-action loop is the same choose/observe/learn cadence as
run_curious_live. The ONLY differences from arc3_switches_offline_full are:
  (1) on WIN we RESET and keep playing (instead of break) — so we can see whether
      the now-confirmed objective is re-achieved deliberately, and
  (2) we read agent._effect_objective_node's attrs each tick (pure introspection
      over the agent's OWN graph — no decision, no new reasoner).
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

from arc3_env import SwitchesEnv  # noqa: E402
from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402
from domains.arc3_full_seed import install_full_seed_set  # noqa: E402
from domains.order_n_world_model import order_n_curiosity_weights  # noqa: E402
from arc3_live_experiment import _changed_celltypes, _changed_cells  # noqa: E402


def _objective_snapshot(agent):
    nid = getattr(agent, "_effect_objective_node", None)
    if nid is None:
        return None
    a = agent.mind_graph.node(nid).attrs
    return {
        "provisional": bool(a.get("provisional")),
        "support": int(a.get("support", 0)),
        "n_events": len(a.get("objective_events", [])),
        "events": list(a.get("objective_events", [])),
        # Objective-order AbS state (the unification): which action the win-rule
        # hypothesis predicts reward for, its running objective-level synthesis
        # error EMA, and the disconfirmed set.
        "target_action": a.get("target_action"),
        "obj_synth_err_ema": round(float(a.get("synthesis_error_ema", 0.0)), 3),
        "abs_passes": int(a.get("abs_passes", 0)),
        "disconfirmed": list(a.get("disconfirmed_actions", [])),
    }


def _structural_goal_present(agent) -> bool:
    return getattr(agent, "_structural_objective_goal", None) is not None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--actions", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    random.seed(args.seed)

    print("=== ARC-3 OFFLINE INTROSPECT :: switches (full stack, continues past win) ===")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    rep = install_full_seed_set(agent)
    print(f"  [ARC3_FULL] concepts {rep['concepts_before']} -> {rep['concepts_after']}  "
          f"seeds={rep['seeds_installed']}(fail={rep['seeds_failed']})")
    handle = arc3_thin_handle(SwitchesEnv(), agent)
    agent.set_compute_limit(50.0 * float(args.actions))

    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    transitions = []
    cell_transitions = []
    actions_chosen = Counter()
    best_score = ctx["score"]
    wins = []                       # action indices where a WIN landed
    first_win = None
    provisional_first_seen = None   # first tick a provisional objective existed
    confirmed_at = None             # first tick the objective flipped to confirmed
    obj_log = []                    # (action_idx, snapshot) when it changes
    curiosity_w = {}
    prev_obj = None
    # Objective-order AbS introspection (the unification under test):
    target_sequence = []            # the pursued win-rule target_action over time (SHIFT?)
    obj_surprise_trace = []         # per-tick objective_synthesis_error on agent_root
    surprise_emotion_trace = []     # per-tick UNIFIED surprise emotion sample
    refute_events = []              # (action_idx, action_disconfirmed)
    prev_disconfirmed = set()
    prev_target = None

    for i in range(args.actions):
        actions = handle["legal_actions"](substrate, ctx)
        if not actions:
            break
        action = agent.choose_action(substrate, ctx, actions, handle)
        chosen_kind = canonical_action_kind(action)
        actions_chosen[chosen_kind] += 1

        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)

        q_before = agent.quality_of_position(substrate)
        pre = substrate
        substrate, ctx = handle["apply_action"](substrate, ctx, action)

        changed = _changed_celltypes(pre, substrate)
        transitions.append((chosen_kind, changed))
        cell_transitions.append((chosen_kind, _changed_cells(pre, substrate)))

        agent.observe(substrate)
        q_after = agent.quality_of_position(substrate)
        agent.record_action_outcome(
            chosen_kind, agent.last_world_novelty,
            max(0.0, q_before - q_after), agent.boredom_count(substrate),
            ctx.get("tick", 0), terminal_delta=(1.0 if ctx["won"] else 0.0),
            frontier_after=agent.last_freshening_count,
        )

        # --- introspect the agent's OWN objective node (no decision here) ---
        snap = _objective_snapshot(agent)
        # The objective-order surprise the agent surfaced on agent_root this tick,
        # and the UNIFIED surprise emotion sample (perceptual OR violated-reward).
        a_root = agent.mind_graph.node(agent.agent_root).attrs
        obj_surprise_trace.append(round(float(a_root.get("objective_synthesis_error", 0.0)), 3))
        surprise_emotion_trace.append(round(float(agent._emotion_sample("surprise")), 3))
        # The pursued win-rule target (does it SHIFT across the run, or monomania?).
        cur_target = snap["target_action"] if snap else None
        if cur_target is not None and cur_target != prev_target:
            target_sequence.append((i + 1, cur_target))
            prev_target = cur_target
        # Refute events: a newly disconfirmed action = the surprise/assessment
        # dropped a guess (the SHIFT mechanism firing).
        cur_dis = set(getattr(agent, "_winrule_disconfirmed_actions", set()))
        for a_dis in (cur_dis - prev_disconfirmed):
            refute_events.append((i + 1, a_dis))
        prev_disconfirmed = cur_dis
        if snap is not None:
            if snap["provisional"] and provisional_first_seen is None:
                provisional_first_seen = i + 1
            if (not snap["provisional"]) and confirmed_at is None:
                confirmed_at = i + 1
            if snap != prev_obj:
                obj_log.append((i + 1, snap))
                prev_obj = snap

        if ctx["score"] > best_score:
            best_score = ctx["score"]

        if ctx["won"]:
            wins.append(i + 1)
            if first_win is None:
                first_win = i + 1
            # keep playing: reset a fresh episode so we can see re-achievement.
            substrate, ctx = handle["reset"]()
            agent.observe(substrate)
            best_score = ctx["score"]

        if (i + 1) % 4 == 0:
            curiosity_w = order_n_curiosity_weights(cell_transitions)
        if (i + 1) % 8 == 0:
            agent.grow_gamma()
            agent.insight(layer=1)
        if (i + 1) % 16 == 0:
            agent.discover_relations()
            agent.discover_theorems()

    print("\n================ RESULT ================")
    print(f"  total actions            : {len(transitions)}")
    print(f"  WINS at actions          : {wins}  (count={len(wins)})")
    print(f"  first win at action      : {first_win}")
    print(f"  actions chosen (by kind) : {dict(actions_chosen)}")
    print("\n  -- EffectObjective machinery (read from the agent's own node) --")
    print(f"    provisional first seen @ : {provisional_first_seen}")
    print(f"    structural goal minted   : {_structural_goal_present(agent)}")
    print(f"    confirmed (non-provisional) first @ : {confirmed_at}")
    final = _objective_snapshot(agent)
    print(f"    FINAL objective snapshot : {final}")
    print("\n  -- objective node change log (action_idx, snapshot) --")
    for idx, snap in obj_log:
        print(f"    @{idx}: provisional={snap['provisional']} "
              f"support={snap['support']} n_events={snap['n_events']} "
              f"events={snap['events']}")

    # re-achievement: did wins land AFTER the objective got confirmed?
    if confirmed_at is not None:
        post = [w for w in wins if w > confirmed_at]
        print(f"\n  wins AFTER objective confirmed: {post} "
              f"(deliberate re-achievement = {'YES' if post else 'no'})")

    # === OBJECTIVE-ORDER AbS (the unification under test) ===
    print("\n  -- objective-order AbS (win-rule unified into the manifold) --")
    nonzero_surprise = [(idx + 1, v) for idx, v in enumerate(obj_surprise_trace) if v > 0.0]
    print(f"    objective_synthesis_error: max={max(obj_surprise_trace) if obj_surprise_trace else 0.0} "
          f"  ticks>0={len(nonzero_surprise)}/{len(obj_surprise_trace)}")
    print(f"    objective surprise (first 40 ticks): {obj_surprise_trace[:40]}")
    print(f"    UNIFIED surprise emotion (first 40): {surprise_emotion_trace[:40]}")
    print(f"    surprise emotion: max={max(surprise_emotion_trace) if surprise_emotion_trace else 0.0} "
          f"  ticks>0={sum(1 for v in surprise_emotion_trace if v > 0.0)}/{len(surprise_emotion_trace)}")
    print(f"    pursued win-rule target SHIFT sequence (action_idx, target):")
    for idx, tgt in target_sequence:
        print(f"      @{idx}: {tgt}")
    print(f"    distinct win-rule targets pursued: "
          f"{len({t for _, t in target_sequence})} "
          f"(monomaniacal = {'YES' if len({t for _, t in target_sequence}) <= 1 else 'NO'})")
    print(f"    REFUTE events (action_idx, action_disconfirmed): {refute_events}")
    print(f"    final disconfirmed set: {sorted(prev_disconfirmed)}")
    return locals()


if __name__ == "__main__":
    main(sys.argv[1:])
