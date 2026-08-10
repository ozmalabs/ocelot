"""THE JABBERWOCK RUNS IN MAZE WORLD AND DESIGNS ITS OWN NAVIGATION — NO TEACHER.

It is GIVEN only weak baselines (greedy_amnesia, wall_follower). But it already UNDERSTANDS routing: it holds
the routing PRIMITIVES (map_memory, distance_field, gradient_descent) — its flood IS a distance field, its hop
IS gradient descent, its learned-walls IS map memory. So when its autonomous understand-loop finds the
baselines fall short of the target, it does NOT reach for an LLM — it COMPOSES a better strategy from the
primitives it already knows, and the loop then runs and measures THAT.

Loop body is `master_tick(); tick()` + one compose step the agent's own shortfall triggers:
  investigate baselines -> measure (both < target) -> RECOGNISE the unmet need + that it understands routing
  -> COMPOSE distance_field+gradient_descent+map_memory into a new strategy (no teacher) -> investigate it ->
  it is OPTIMAL -> the agent's own design beats the baselines.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/maze_autonomy.py [n_ticks]
"""
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.maze_world import MazeCapabilityWorld

SEP = "=" * 96
SEEDS = ["enact", "discourse", "autonomy", "maze_capability", "investigation_loop", "investigation_teacher"]
TARGET = 0.9


def _keys(adapter, ax):
    return adapter.s.node(ax)["attrs"].get("capability_keys")


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 36
    print(SEP)
    print("MAZE AUTONOMY (no teacher) — the jabberwock COMPOSES navigation from what it already understands.")
    print(SEP)
    t0 = time.time()

    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)

    world = MazeCapabilityWorld(adapter, eval_n=6, eval_seed=7, episodes=5)
    world.register_affordances()
    mt = next((n for n in adapter.s.nodes("Microtheory")
               if adapter.s.node(n)["attrs"].get("name") == "maze_world"), None)
    adapter.s.add_edge(adapter.agent, "operates_in", mt)
    adapter.wire_autonomy_faculty()
    adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(world)
    # NO set_self_teacher: the agent has no teacher to fall back on. It must use its OWN understanding.

    prims = [adapter.s.node(p)["attrs"].get("name") for p in adapter.s.nodes("RoutingPrimitive")]
    baselines = [adapter.s.node(o)["attrs"].get("name") for o in adapter.s.nodes("Operator")]
    print(f"  booted in {time.time()-t0:.1f}s. GIVEN baselines: {baselines}")
    print(f"  routing it ALREADY UNDERSTANDS (primitives): {prims}")
    print(f"  target efficiency = {TARGET}. No teacher attached; compose is a GRAPH RULE.\n")

    seen_mc, measured, announced = set(), {}, False
    nm = {("solve", "maze", "amnesia"): "greedy_amnesia", ("solve", "maze", "reactive"): "wall_follower",
          ("solve", "maze", "composed"): "composed_routing"}
    for t in range(1, n_ticks + 1):
        adapter.master_tick()
        adapter.tick()                                # the compose_routing_on_shortfall RULE fires in here
        for mc in adapter.s.nodes("MeasuredCapability"):
            if mc in seen_mc:
                continue
            seen_mc.add(mc)
            mca = adapter.s.node(mc)["attrs"]
            tgt = adapter.inner.neighbours(mc, "measures_axis")
            k = tuple(_keys(adapter, tgt[0])) if tgt else None
            measured[k] = mca.get("measured")
            print(f"  [tick {t:2d}] RAN {nm.get(k, k)}: {mca.get('note')}")
        # observe (don't cause) the RULE'S design act: a composed_routing operator the rule minted.
        if not announced:
            cop = next((o for o in adapter.s.nodes("Operator")
                        if adapter.s.node(o)["attrs"].get("name") == "composed_routing"), None)
            if cop is not None:
                announced = True
                print(f"\n  [tick {t:2d}] >>> the compose_routing_on_shortfall RULE fired (baseline routing fell "
                      f"short): the agent composed a new strategy from primitives it understands —\n"
                      f"          {adapter.s.node(cop)['attrs'].get('comment')}\n")

    print(f"\n{SEP}")
    print("  STRATEGIES (efficiency = optimal/steps, 1.0 = optimal):")
    ranked = sorted(((v, k) for k, v in measured.items() if k and v is not None), reverse=True)
    for eff, k in ranked:
        kind = "(GIVEN baseline)" if nm.get(k) in ("greedy_amnesia", "wall_follower") else "(SELF-COMPOSED, no teacher)"
        print(f"    {nm.get(k, k):16s} efficiency={eff}  {kind}")
    comp = measured.get(("solve", "maze", "composed"))
    if comp is not None:
        base = max([v for kk, v in measured.items() if nm.get(kk) in ("greedy_amnesia", "wall_follower")], default=0)
        verdict = "BEATS" if comp > base else "does not beat"
        print(f"\n  -> the agent's SELF-COMPOSED routing scored {comp}, {verdict} the best baseline ({base}). "
              f"It designed a better navigator from primitives it already understood — NO teacher.")
    print(f"  done in {time.time()-t0:.1f}s.")
    print(SEP)
    return 0 if comp is not None else 1


if __name__ == "__main__":
    sys.exit(main())
