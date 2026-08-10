"""The jabberwock plays a SIMPLE MAZE, OFFLINE, and SELF-IMPROVES — fast, because there is no network and the
nav model is exact.

It reuses the SAME graph faculty it uses on ls20 — its own Rust rigid-body slide_flood + the graph-native
hop_descend_gradient rule + the learned-block faculty — with slide=1 and a 1x1 body. The agent gets PARTIAL
OBSERVABILITY: its map is optimistic (every cell looks passable), so it heads straight for the exit, BUMPS a
wall (a flood-approved move that yields no motion), LEARNS that (cell,direction) is dead (a `_blk_*` stamp the
flood then routes around), and re-plans. Across episodes of the SAME maze the blocks persist, so it remembers
the walls and goes straight to the exit: steps-per-episode FALL. That fall is the self-improvement.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/maze_run.py
      NAV_REPR=quanta PYTHONPATH=runners/dsl/python:. python3 scripts/maze_run.py   # quanta mode

QUANTA MODE (FLOOD_DESIGN Part C): the SAME script, the SAME mazes, but the map is SpaceQuantum
boxes decoded by the Rust `space_quantize` primitive and every nav decision is a qf_* rule
(seeds/quanta_navigation.json). The host stamps observations (avatar_pose; a bump -> the observed
WALL value + a BlockObs node) and ticks — domains/spatial_sense.quanta_flood_step is the shared
adapt+tick pass. Default is cell mode, byte-identical to the pre-quanta behaviour.
"""
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.maze_world import gen_maze, MazeWorld

DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
WALL = 3.0   # a cell the agent has LEARNED is a wall (by bumping it); both floods (walls=[3]) avoid it


def play_episode(agent, world, max_steps=4000):
    """One run from start to exit. The agent floods, the hop RULE picks the move, a bump LEARNS a wall.
    Returns (steps, bumps, solved)."""
    S, I = agent.s, agent.inner
    game = world.game
    gid = int(str(game).lstrip("#"))
    exit_cell = world.cell(world.exit)
    eid = int(str(exit_cell).lstrip("#"))
    world.pos = world.start
    prev_A = None
    bumps = 0
    # commit the exit as the goal (the hop descends the goal-flood gradient toward it); idempotent.
    if exit_cell not in list(I.neighbours(game, "committed_goal")):
        I.add_edge_unchecked(game, "committed_goal", exit_cell)
    I.set_attr(game, "slide", 1.0); I.set_attr(game, "ground", 4.0)
    for step in range(max_steps):
        A = world.cell(world.pos)
        if prev_A is not None and prev_A != A:
            I.set_attr(prev_A, "is_avatar_cell", 0.0)
        I.set_attr(A, "is_avatar_cell", 1.0); prev_A = A
        I.set_attr(game, "frame", float(step))
        I.set_attr(game, "fresh", 1.0)            # keep cover_stuck at 0 -> no abandon/escape; pure goal nav
        I.set_attr(game, "chosen_action", "")
        # AVATAR flood (slide=1, 1x1 body; walls=[3] = the cells learned-as-walls so far) -> _adist + reached
        I.slide_flood(int(str(A).lstrip("#")), 1, 1, 1, [int(WALL)], 800, step, gid, True, "_adist")
        I.set_attr(game, "flood_epoch", float(step))
        I.run_rules()
        # GOAL flood from the exit -> _dist (the gradient the hop descends)
        I.slide_flood(eid, 1, 1, 1, [int(WALL)], 800, step, gid, False, "_dist")
        I.run_rules()
        act = S.node(game)["attrs"].get("chosen_action") or ""
        if not act:
            return step, bumps, False                # no route on the known map (boxed by learned walls)
        wall_rc = (world.pos[0] + DISP[act][0], world.pos[1] + DISP[act][1])
        moved, solved = world.apply(act)
        if not moved:                                # BUMP: the target CELL is a wall -> mark it impassable
            wc = world.cell(wall_rc)                 # (both floods then avoid it from every side; symmetric)
            if wc is not None and S.node(wc)["attrs"].get("value") != WALL:
                I.set_attr(wc, "value", WALL); bumps += 1
        if solved:
            return step + 1, bumps, True
    return max_steps, bumps, False


def setup_quanta(agent, world):
    """Quanta-mode world wiring (mechanical DATA, once per maze — world-adapter ingest): the mode
    attr; the maze's 4 actions as ControlResponse data on an is_self Region (the maze world KNOWS
    its own action vocabulary — the qf hop rules Dot-pick against this chain, the same chain the
    live arc path grows via affordance_basis); the exit as a Goal{pose} (the same exit-commit the
    cell path does with the exit cell)."""
    S, I = agent.s, agent.inner
    game = world.game
    I.set_attr(game, "nav_repr", "quanta")
    I.set_attr(game, "slide", 1.0); I.set_attr(game, "ground", 4.0)
    sr = S.add_node("Region", {"is_self": 1.0})
    I.add_edge_unchecked(game, "has_region", sr)
    for name, (dr, dc) in DISP.items():
        cr = S.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc), "dz": 0.0,
                                            "cname": name})
        I.add_edge_unchecked(sr, "responds_via", cr)
    g = S.add_node("Goal", {"pose": [int(world.exit[0]), int(world.exit[1])],
                            "committed": 1.0, "world": 1.0})
    I.add_edge_unchecked(game, "committed_goal", g)


def play_episode_quanta(agent, world, max_steps=4000):
    """One quanta-mode run from start to exit. Identical world-feedback loop to play_episode; the
    difference is purely the map representation: quanta_flood_step decodes SpaceQuantum boxes and
    the qf_* rules pick the move. A bump stamps the observed WALL into the belief (the same
    mechanical value-correction the cell path does) PLUS a BlockObs node — the rules then decide
    interior-split vs portal-flip, and the next pass re-quantizes. Returns (steps, bumps, solved)."""
    from domains.spatial_sense import (quanta_flood_step, record_block_obs, bump_belief_epoch,
                                       mark_belief_change)
    S, I = agent.s, agent.inner
    game = world.game
    world.pos = world.start
    bumps = 0
    pend = False
    for step in range(max_steps):
        I.set_attr(game, "frame", float(step))
        I.set_attr(game, "fresh", 1.0)            # keep cover_stuck at 0 -> no abandon; pure goal nav
        I.set_attr(game, "chosen_action", "")
        # focus = the WHOLE maze (world knowledge: the world's own bounds). The primitive's
        # decode is focus-scoped — quanta outside focus are dropped on refocus — so a world
        # this small keeps its full map decoded; the moving-fovea cadence is the arc path's.
        quanta_flood_step(agent, game, world.pos, (1, 1), [int(MazeWorld.FLOOR)], 1,
                          (world.H, world.W), pending_block=pend,
                          focus=([0, 0], [world.H - 1, world.W - 1]))
        pend = False
        act = S.node(game)["attrs"].get("chosen_action") or ""
        if not act:
            return step, bumps, False             # no route on the known map (qf_closed territory)
        wall_rc = (world.pos[0] + DISP[act][0], world.pos[1] + DISP[act][1])
        prev = world.pos
        moved, solved = world.apply(act)
        if not moved:                             # BUMP: record the observation, the rules decide
            wc = world.cell(wall_rc)
            if wc is not None and S.node(wc)["attrs"].get("value") != WALL:
                I.set_attr(wc, "value", WALL)     # belief correction (same stamp as the cell path)
                mark_belief_change(agent, game, wall_rc, 0 if act in ("Up", "Down") else 1)
                bump_belief_epoch(agent)
                bumps += 1
            record_block_obs(agent, game, prev, DISP[act], step)
            pend = True
        if solved:
            return step + 1, bumps, True
    return max_steps, bumps, False


def reset_marks(agent, world):
    """Clear per-episode perception (is_avatar_cell, visited) but KEEP the learned `_blk_*` walls (memory)."""
    I = agent.inner
    for nid in world.cells.values():
        a = agent.s.node(nid)["attrs"]
        if a.get("is_avatar_cell"):
            I.set_attr(nid, "is_avatar_cell", 0.0)
        if a.get("visited"):
            I.set_attr(nid, "visited", 0.0)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8, help="maze is (2n+1)x(2n+1)")
    ap.add_argument("--episodes", type=int, default=6)
    ap.add_argument("--mazes", type=int, default=3)
    ap.add_argument("--nav-repr", default=os.environ.get("NAV_REPR", "cells"),
                    choices=["cells", "quanta"],
                    help="map representation: 'cells' (legacy slide_flood) or 'quanta' (space_quantize + qf rules)")
    args = ap.parse_args()
    quanta = args.nav_repr == "quanta"

    t0 = time.time()
    print("booting the jabberwock ...", flush=True)
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    print(f"booted in {time.time()-t0:.1f}s. PARTIAL-OBS maze: the agent learns walls by bumping; blocks "
          f"persist across episodes of one maze (memory).\n")
    if quanta:
        print("nav_repr=quanta: SpaceQuantum map (Rust space_quantize) + qf_* rules decide every move.\n",
              flush=True)

    for mi in range(args.mazes):
        grid, start, exit = gen_maze(args.n, seed=100 + mi)
        # NOTE: a fresh WorldAdapter per maze keeps the substrate clean (one Game, no stale cross-maze edges).
        if mi > 0:
            agent = WorldAdapter(seeds=()); load_all_seeds(agent)
        world = MazeWorld(agent, grid, start, exit); world.ingest()
        if quanta:
            setup_quanta(agent, world)
        opt = None
        print(f"=== maze {mi}  ({world.H}x{world.W})  start{start} -> exit{exit} ===", flush=True)
        for ep in range(args.episodes):
            reset_marks(agent, world)
            te = time.time()
            steps, bumps, solved = (play_episode_quanta if quanta else play_episode)(agent, world)
            tag = "solved" if solved else "GAVE UP"
            if solved and opt is None:
                pass
            print(f"  episode {ep}: {tag} in {steps:4d} steps  ({bumps:3d} new walls learned)  "
                  f"[{(time.time()-te)*1000:.0f}ms]", flush=True)
        print()
    print(f"total {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    main()
