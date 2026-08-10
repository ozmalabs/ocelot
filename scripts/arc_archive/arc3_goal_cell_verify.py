"""arc3_goal_cell_verify — honest verification of the goal_cell + passability
refinement. Drives the EXISTING CuriousAgent on the refined adapter+seed and
introspects, via the agent's own machinery, whether:

  (1) goal_cell GROUNDS to a specific SpatialLocation (the odd-one-out cell)
      and moves OUT of held_predicates;
  (2) the planner produces a route to that goal cell (committed_plan / a
      visit_target goal whose target is the goal cell);
  (3) `passable` is perceived and at least one Boundary is marked impassable
      after failed moves;
  (4) mapped_region > 0.

Then measures navigate WINS: refined (seed + colour-class + passability)
vs the opaque-cell baseline (no seed, current behaviour) over the same
seeds/ticks. Scaffolding only (driver loop + introspection); the agent's
own observe/choose_action/insight do the work.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa
from domains.arc3_world import arc3_world_handle, SELF_ID  # noqa
from domains.arc3_seed import install_arc3_seed  # noqa
from arc3_env import ENVS  # noqa


def _goal_cell_grounded(agent):
    """Read which SpatialLocation(s) the agent's grounded goal_cell holds of
    — pure introspection over the agent's own concept evaluation."""
    if "goal_cell" not in agent._concept_nodes:
        return []
    hits = []
    for (wt, wid), nid in agent._world_instance_nodes.items():
        if wt != "SpatialLocation":
            continue
        try:
            if agent._concept_holds("goal_cell", nid):
                hits.append((wid, nid))
        except Exception:
            pass
    return hits


def _boundary_stats(agent):
    """Boundaries become WorldInstance nodes carrying world_type=='Boundary'
    and the learned `passable` attr — read those, not raw 'Boundary' types."""
    passable = impassable = 0
    seen_passable_attr = False
    for n in agent.mind_graph.nodes():
        if n.attrs.get("world_type") != "Boundary":
            continue
        if "passable" in n.attrs:
            seen_passable_attr = True
            if n.attrs.get("passable"):
                passable += 1
            else:
                impassable += 1
    return seen_passable_attr, passable, impassable


def run(game: str, ticks: int, seed: int, use_seed: bool, verbose=False):
    random.seed(seed)
    env = ENVS[game]()
    agent = CuriousAgent()
    if use_seed:
        agent.my_world_id = SELF_ID
    handle = arc3_world_handle(env, agent)
    report = {}
    if use_seed:
        report["install"] = install_arc3_seed(agent)

    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    ttw = None
    grounded_tick = None
    routed_tick = None
    for i in range(ticks):
        actions = handle["legal_actions"](substrate, ctx)
        if not actions:
            break
        action = agent.choose_action(substrate, ctx, actions, handle)
        kind = canonical_action_kind(action)
        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)
        q_before = agent.quality_of_position(substrate)
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)
        q_after = agent.quality_of_position(substrate)
        agent.record_action_outcome(
            kind, agent.last_world_novelty, max(0.0, q_before - q_after),
            agent.boredom_count(substrate), ctx.get("tick", 0),
            terminal_delta=(1.0 if ctx["won"] else 0.0),
            frontier_after=agent.last_freshening_count)

        if (i + 1) % 8 == 0:
            agent.grow_gamma()
        if (i + 1) % 8 == 0:
            # insight() runs _reground_predicates — promotes goal_cell the
            # moment the colour-class structure it awaits is perceived.
            agent.insight(layer=1)
        if (i + 1) % 16 == 0:
            agent.discover_relations()

        if use_seed and grounded_tick is None and _goal_cell_grounded(agent):
            grounded_tick = i + 1
        if (use_seed and routed_tick is None
                and getattr(agent, "committed_plan", None)):
            routed_tick = i + 1

        if ctx["won"] and ttw is None:
            ttw = i + 1
            if verbose:
                print(f"  WIN at tick {ttw} (use_seed={use_seed})")
            break

    if use_seed:
        hits = _goal_cell_grounded(agent)
        held = [h["name"] for h in agent.held_predicates()]
        seen_pass, npass, nimpass = _boundary_stats(agent)
        n_mapped = len(list(agent.mind_graph.out_edges(
            agent.agent_root, "mapped_region")))
        report["goal_cell_in_concepts"] = "goal_cell" in agent._concept_nodes
        report["goal_cell_in_held"] = "goal_cell" in held
        report["goal_cell_holds_of"] = [w for w, _ in hits]
        report["grounded_at_tick"] = grounded_tick
        report["routed_at_tick"] = routed_tick
        report["committed_plan_len"] = len(getattr(agent, "committed_plan", []))
        report["passable_attr_perceived"] = seen_pass
        report["boundaries_passable"] = npass
        report["boundaries_impassable"] = nimpass
        report["mapped_region"] = n_mapped
        report["instance_edge_types"] = sorted(
            agent._instance_edge_types_registered)
    report["ttw"] = ttw
    return report


def main(argv):
    # Default 1500: the goal_cell GROUNDS + the planner routes within ~10
    # ticks, but the route COMPLETES only after the agent bumps the walls
    # the BFS gradient points through (passability prunes behaviour, not the
    # distance map) — that learning takes a few hundred ticks.
    ticks = int(argv[0]) if argv else 1500
    seeds = int(argv[1]) if len(argv) > 1 else 3
    print(f"=== goal_cell verify :: navigate :: ticks={ticks} seeds={seeds} ===\n")

    print("--- REFINED (seed + colour-class + passability), seed 0 introspection ---")
    rep0 = run("navigate", ticks, 0, use_seed=True, verbose=True)
    print(json.dumps({k: v for k, v in rep0.items() if k != "install"}, indent=2))
    print("install report:", json.dumps(rep0.get("install", {})))

    refined_ttw, baseline_ttw = [], []
    for s in range(seeds):
        r = run("navigate", ticks, s, use_seed=True)
        b = run("navigate", ticks, s, use_seed=False)
        refined_ttw.append(r["ttw"])
        baseline_ttw.append(b["ttw"])
        print(f"  seed {s}: refined ttw={r['ttw']}  baseline ttw={b['ttw']}  "
              f"grounded@{r.get('grounded_at_tick')} routed@{r.get('routed_at_tick')}")

    def fmt(xs):
        hit = [x for x in xs if x is not None]
        if not hit:
            return "never"
        return f"won {len(hit)}/{len(xs)}, mean={sum(hit)/len(hit):.1f}, best={min(hit)}"
    print("\n--- navigate WIN contrast (same seeds/ticks) ---")
    print(f"  refined : {fmt(refined_ttw)}")
    print(f"  baseline: {fmt(baseline_ttw)}")


if __name__ == "__main__":
    main(sys.argv[1:])
