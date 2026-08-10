"""MazeWorld — a SIMPLE, OFFLINE, FAST maze game for the jabberwock to play and learn in.

Why a maze: ls20 is slow (network per frame) and a DYNAMIC puzzle (the model never settles). A static maze is
the clean fast ground where the jabberwock's nav faculty is EXACT and it can run thousands of cheap steps to
LEARN. The learning is genuine: the jabberwock is given PARTIAL OBSERVABILITY — its map starts optimistic
(every cell looks passable) and it discovers a wall only by BUMPING it (a flood-approved move that yields no
motion -> the learned-block faculty marks that (cell,direction) dead). Re-playing the same maze it REMEMBERS
the walls (blocks persist) and goes straight to the exit: steps-per-episode fall = self-improvement.

This is a WORLD ADAPTER (a thin pipe, per the architecture rule): it generates/holds the true maze, ingests it
as Cells the agent reads, and translates a move action into a position change. NO agent decisions live here —
the flood, the hop, and the block-learning are the agent's Rust/graph faculty.
"""
from __future__ import annotations


def gen_maze(n: int, seed: int):
    """Recursive-backtracker (randomized DFS) maze on a (2n+1)x(2n+1) grid. 0 = passage, 1 = wall.
    Deterministic from `seed` (no Math.random needed — a tiny LCG). Returns (grid, start, exit)."""
    H = W = 2 * n + 1
    grid = [[1] * W for _ in range(H)]
    state = (seed * 2654435761 + 1) & 0xFFFFFFFF

    def rnd(m):
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state % m

    def carve(r, c):
        grid[r][c] = 0
        dirs = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        for _ in range(len(dirs)):                      # shuffle in place (Fisher-Yates with the LCG)
            j = rnd(len(dirs))
            dirs[0], dirs[j] = dirs[j], dirs[0]
            dr, dc = dirs.pop(0)
            nr, nc = r + dr, c + dc
            if 1 <= nr < H - 1 and 1 <= nc < W - 1 and grid[nr][nc] == 1:
                grid[r + dr // 2][c + dc // 2] = 0      # knock out the wall between
                carve(nr, nc)

    import sys
    lim = sys.getrecursionlimit()
    sys.setrecursionlimit(max(lim, H * W + 100))
    carve(1, 1)
    sys.setrecursionlimit(lim)
    return grid, (1, 1), (H - 2, W - 2)


class MazeWorld:
    """Thin pipe: hold the true maze + avatar position; ingest the grid as Cells (all FLOOR — the agent's
    optimistic map; walls are LEARNED, not given); move the avatar one cell if the true maze allows it."""

    FLOOR = 4

    def __init__(self, agent, grid, start, exit):
        self.agent = agent
        self.s = agent.s
        self.I = agent.inner
        self.grid = grid
        self.H = len(grid)
        self.W = len(grid[0])
        self.start = start
        self.exit = exit
        self.pos = start
        self.cells: dict[tuple[int, int], object] = {}
        self.game = None

    # --- INGEST: the maze grid -> Cell nodes (all floor) + neighbour edges + a Game node. -----------------
    def ingest(self):
        S, I = self.s, self.I
        self.game = S.add_node("WorldInstance", {"world_type": "Game", "frame": 0.0})
        for r in range(self.H):
            for c in range(self.W):
                # EVERY position is a Cell the agent sees as FLOOR. The agent does not get the wall map; it
                # learns walls by bumping. (A wall cell simply can never be entered — apply() refuses it.)
                nid = S.add_node("WorldInstance",
                                 {"world_type": "Cell", "row": float(r), "col": float(c), "value": float(self.FLOOR)})
                self.cells[(r, c)] = nid
                I.add_edge_unchecked(self.game, "has_cell", nid)
        # 4-neighbour lattice (slide_flood walks this to build its (r,c)->Node index)
        for (r, c), nid in self.cells.items():
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                m = self.cells.get((r + dr, c + dc))
                if m is not None:
                    I.add_edge_unchecked(nid, "neighbour", m)
        return self.game

    def cell(self, rc):
        return self.cells.get(rc)

    def passable(self, rc):
        r, c = rc
        return 0 <= r < self.H and 0 <= c < self.W and self.grid[r][c] == 0

    # --- APPLY: one move. Returns (moved, solved). The agent's only world feedback. --------------------
    def apply(self, action):
        disp = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}.get(action)
        if disp is None:
            return False, self.pos == self.exit
        tgt = (self.pos[0] + disp[0], self.pos[1] + disp[1])
        moved = self.passable(tgt)
        if moved:
            self.pos = tgt
        return moved, self.pos == self.exit


# ======================================================================================================
#  Strategy solvers + the CAPABILITY WORLD (for the agent's autonomous self-design loop)
# ======================================================================================================

def bfs_optimal(grid, start, exit):
    """Shortest-path length on the TRUE maze — the optimum a strategy is scored against."""
    from collections import deque
    H, W = len(grid), len(grid[0])
    q = deque([(start, 0)]); seen = {start}
    while q:
        (r, c), d = q.popleft()
        if (r, c) == exit:
            return d
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == 0 and (nr, nc) not in seen:
                seen.add((nr, nc)); q.append(((nr, nc), d + 1))
    return 10 ** 9


def wall_follower_steps(grid, start, exit, max_steps=20000):
    """The reactive LEFT-HAND RULE: keep a wall on your left. Solves a simply-connected maze with NO map,
    but walks a long path. A distinct navigation strategy the agent can weigh against its flood nav."""
    H, W = len(grid), len(grid[0])
    D = [(-1, 0), (0, 1), (1, 0), (0, -1)]          # N, E, S, W
    pos, head = start, 1                            # facing East
    op = lambda r, c: 0 <= r < H and 0 <= c < W and grid[r][c] == 0
    for steps in range(max_steps):
        if pos == exit:
            return steps
        for turn in ((head + 3) % 4, head, (head + 1) % 4, (head + 2) % 4):   # left, straight, right, back
            dr, dc = D[turn]; nr, nc = pos[0] + dr, pos[1] + dc
            if op(nr, nc):
                head, pos = turn, (nr, nc); break
        else:
            return max_steps
    return max_steps


class MazeCapabilityWorld:
    """The world the agent's AUTONOMOUS understand-loop investigates. It owns no single maze: each
    investigation runs the bound strategy (the operator the graph chose) on a fresh eval maze and banks an
    efficiency score. The agent decides WHICH strategy to run (frontier_pick + the bind JOIN); this only
    ENACTS the chosen one and measures it — exactly like SpeechWorld.execute. No decision lives here."""

    def __init__(self, adapter, eval_n=6, eval_seed=7, episodes=5):
        self.adapter = adapter
        self.s = adapter.s
        self.eval_n = eval_n
        self.eval_seed = eval_seed
        self.episodes = episodes
        self._nav_agent = None

    def register_affordances(self):
        return None                                  # productions come from the enact/autonomy/maze_capability seeds

    def _nav(self):
        """A cached, fully-booted nav agent (load_all_seeds -> the grid_navigation hop). The flood strategies
        run on THIS agent in isolation; only the scalar score is banked to the autonomy substrate."""
        if self._nav_agent is None:
            from substrate.world_adapter import WorldAdapter
            from substrate.boot_all import load_all_seeds
            a = WorldAdapter(seeds=()); load_all_seeds(a); self._nav_agent = a
        return self._nav_agent

    def _flood_eval(self, grid, start, exit, remember):
        """Run the agent's OWN flood+hop nav over several attempts; with `remember`, learned walls persist
        (converges to optimal), else they are wiped each attempt. Return the final attempt's step count."""
        from scripts.maze_run import play_episode, reset_marks
        a = self._nav()
        nav = MazeWorld(a, grid, start, exit); nav.ingest()
        last = None
        for ep in range(self.episodes):
            reset_marks(a, nav)
            if not remember:                          # forget every learned wall -> re-explore from scratch
                for nid in nav.cells.values():
                    if a.s.node(nid)["attrs"].get("value") == 3.0:
                        a.inner.set_attr(nid, "value", float(nav.FLOOR))
            steps, bumps, solved = play_episode(a, nav, max_steps=4000)
            last = steps if solved else 4000
        return last

    def execute(self, req):
        """Run the strategy the GRAPH chose (req['operator']) on a fresh eval maze, score it by
        efficiency = optimal_path / steps_taken, and write a MeasuredCapability the bank rule reads."""
        from domains.gap_prioritiser import record_measured_capability
        op = req["operator"]
        grid, start, exit = gen_maze(self.eval_n, seed=self.eval_seed)
        optimal = bfs_optimal(grid, start, exit)
        # composed_routing = the agent's OWN routing primitives assembled (map_memory + distance_field +
        # gradient_descent) -> its flood+hop nav WITH memory. The compose_routing_on_shortfall RULE created
        # this operator; this only runs the faculty it names. No teacher.
        if op == "composed_routing":
            steps = self._flood_eval(grid, start, exit, remember=True)
        elif op == "flood_amnesia":
            steps = self._flood_eval(grid, start, exit, remember=False)
        elif op == "wall_follower":
            steps = wall_follower_steps(grid, start, exit)
        else:
            raise ValueError(f"unknown maze operator: {op}")
        eff = round(optimal / max(steps, 1), 3)
        note = f"{op}: {steps} steps vs optimal {optimal} -> eff {eff}"
        return record_measured_capability(
            self.s, req["capability_keys"], measured=eff, target=float(req.get("target", 0.8) or 0.8),
            metric="maze_efficiency", note=note)
