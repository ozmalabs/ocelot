"""Offline verification (no network) that the thin shim's RAW cells now drive
the agent's OWN spatial perception + goal invention. A tiny synthetic env feeds
the thin handle; we introspect the agent's mind_graph after a few ticks.

NOT a live game and NOT an equivalence harness — just a boot + a few ticks +
read the agent's own surfaces. Key is never read here."""
from __future__ import annotations
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from arc3_env import Frame, GameState  # noqa: E402
from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402


class _TinyEnv:
    """A 5x5 toy: a couple of coloured blobs + one distinct (rare) cell. The
    env is static-ish; one cell shifts per step so the diff has something to
    mark. game_id present for the handle name. NO rules — just frames."""
    game_id = "tiny"
    available_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4",
                         "ACTION5", "ACTION6"]

    def __init__(self):
        self._t = 0
        # base grid: a 2x2 colour-3 blob, a colour-4 blob, one rare colour-7.
        self._base = [
            [0, 3, 3, 0, 0],
            [0, 3, 3, 0, 7],
            [0, 0, 0, 4, 4],
            [0, 0, 0, 4, 4],
            [0, 0, 0, 0, 0],
        ]

    def _grid(self):
        g = [row[:] for row in self._base]
        # move the rare cell down one each tick (gives the diff a mark).
        rr = 1 + (self._t % 3)
        g[1][4] = 0
        g[rr][4] = 7
        return g

    def reset(self):
        self._t = 0
        return Frame(game_id=self.game_id, guid="g", state=GameState.NOT_FINISHED,
                     score=0, frame=[self._grid()])

    def step(self, action, coord=None):
        self._t += 1
        return Frame(game_id=self.game_id, guid="g", state=GameState.NOT_FINISHED,
                     score=0, frame=[self._grid()])


def main():
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    env = _TinyEnv()
    handle = arc3_thin_handle(env, agent)
    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    invented_seen = []
    for i in range(12):
        actions = handle["legal_actions"](substrate, ctx)
        action = agent.choose_action(substrate, ctx, actions, handle)
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)
        if (i + 1) % 4 == 0:
            agent.insight(layer=1)
        # snapshot any invented goal labels live
        for gid in agent._get_top_level_goals():
            lbl = agent.mind_graph.node(gid).attrs.get("label", "")
            if lbl.startswith("invented_") and lbl not in invented_seen:
                invented_seen.append(lbl)

    # === INTROSPECTION — the agent's own surfaces ===
    # A perceived place = any cell the spatial prior gave a position
    # (type-agnostic: the grid's many CellC<v> colours all count).
    n_spatial = sum(1 for (_wt, _w), nid in agent._world_instance_nodes.items()
                    if isinstance(agent.mind_graph.node(nid).attrs.get(
                        "last_x_bin"), (int, float)))
    n_adjacency = 0
    for (_wt, _w), nid in agent._world_instance_nodes.items():
        n_adjacency += len(list(agent.mind_graph.out_edges(nid, "adjacent_to")))
    n_locations = len(list(agent.mind_graph.out_edges(
        agent.agent_root, "mapped_region")))
    n_directions = len(getattr(agent, "_direction_nodes", {}))
    edge_types = sorted(agent._instance_edge_types_registered)
    locus_type = agent._locus_type
    cur_locus = agent.current_locus_wi

    # exploration_value re-engagement: does choose_next_goal now return a cell?
    exploration_target = None
    try:
        exploration_target = agent._pick_goal(horizon=8)
    except Exception as e:
        exploration_target = f"ERR {type(e).__name__}: {e}"

    # active invented goals (the wants edges)
    active_goals = [agent.mind_graph.node(g).attrs.get("label", "")
                    for g, _p in agent._get_goals()]
    invented_active = [(agent.mind_graph.node(g).attrs.get("label", ""),
                        agent.mind_graph.node(g).attrs.get("priority"))
                       for g in agent._get_top_level_goals()
                       if agent.mind_graph.node(g).attrs.get(
                           "label", "").startswith("invented_")]

    print("=== HELP 1: automatic grid -> spatial perception ===")
    print(f"  locus/place type derived     : {locus_type}")
    print(f"  spatial place cells formed   : {n_spatial}")
    print(f"  adjacent_to edges (4-nbr)    : {n_adjacency}")
    print(f"  Direction nodes interned     : {n_directions}")
    print(f"  region Locations (mapped)    : {n_locations}")
    print(f"  instance edge types          : {edge_types}")
    print(f"  current_locus_wi set         : {cur_locus is not None}")
    et_ok = exploration_target is not None and not isinstance(
        exploration_target, str)
    print(f"  exploration_value _pick_goal : "
          f"{'a cell (re-engaged)' if et_ok else exploration_target}")
    print()
    print("=== HELP 2: invent a goal when goalless ===")
    print(f"  invented goals (verbatim)    : {invented_seen}")
    print(f"  invented goals active (pursued): {invented_active}")
    print(f"  agent wants-target goals     : {active_goals}")

    ok1 = (n_spatial >= 2 and n_adjacency > 0 and len(edge_types) > 0
           and cur_locus is not None)
    ok2 = len(invented_seen) > 0 and len(invented_active) > 0
    print()
    print(f"HELP1 spatial perception formed : {ok1}")
    print(f"HELP2 goal invented + pursued   : {ok2}")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
