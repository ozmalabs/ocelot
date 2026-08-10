"""Short LIVE thin-shim run, then introspect the agent's OWN surfaces for the
two faculties. Key from os.environ only (never printed). Not an equivalence
harness — boots the live env, plays a few actions, reads the agent's graph."""
from __future__ import annotations
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _arc3_load_key import load_arc_api_key  # noqa: E402
os.environ["ARC3_THIN"] = "1"
from arc3_live_experiment import run_curious_live  # noqa: E402


def main():
    if not load_arc_api_key() or not os.environ.get("ARC_API_KEY"):
        print("no key; abort")
        return 2
    # list one game
    from arc3_live_env import DEFAULT_BASE_URL
    from arc3_live_experiment import _list_games
    game = _list_games(DEFAULT_BASE_URL)[0]
    res = run_curious_live(game, n_actions=30, seed=0, coord_stride=16,
                           order_n=True, verbose=False, per_tick_budget_ms=50.0)
    agent = res["agent"]

    n_place = sum(1 for (_wt, _w), nid in agent._world_instance_nodes.items()
                  if isinstance(agent.mind_graph.node(nid).attrs.get(
                      "last_x_bin"), (int, float)))
    n_adj = 0
    for (_wt, _w), nid in agent._world_instance_nodes.items():
        n_adj += len(list(agent.mind_graph.out_edges(nid, "adjacent_to")))
    n_dir = len(getattr(agent, "_direction_nodes", {}))
    n_region = len(list(agent.mind_graph.out_edges(
        agent.agent_root, "mapped_region")))
    invented = [agent.mind_graph.node(g).attrs.get("label", "")
                for g in agent._get_top_level_goals()
                if agent.mind_graph.node(g).attrs.get(
                    "label", "").startswith("invented_")]
    active = [agent.mind_graph.node(g).attrs.get("label", "")
              for g, _p in agent._get_goals()]
    pick = None
    try:
        pick = agent._pick_goal(horizon=8)
    except Exception as e:
        pick = f"ERR {type(e).__name__}"

    print(f"game={game}")
    print("=== HELP 1 (live) ===")
    print(f"  place cells perceived (last_x_bin) : {n_place}")
    print(f"  adjacent_to edges                  : {n_adj}")
    print(f"  Direction nodes interned           : {n_dir}")
    print(f"  region Locations (mapped)          : {n_region}")
    print(f"  exploration_value _pick_goal       : "
          f"{'a cell (re-engaged)' if pick is not None and not isinstance(pick, str) else pick}")
    print("=== HELP 2 (live) ===")
    print(f"  invented goals (verbatim)          : {invented}")
    print(f"  active wants-target goals          : {len(active)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
