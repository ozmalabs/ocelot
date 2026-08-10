"""dynamics_world — affordance for S4: a controlled self + one autonomous mover (const velocity, bounces).

The HOST provides only the world (the affordance). The agent authors the lead/dodge faculty itself.
1-cell avatar (value 9 = self) + 1-cell mover (value 8 = autonomous; object-permanence now tracks it).
mode='chase': reaching the mover catches it (score+1, respawn). mode='dodge': contact ends the game.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]
SELF, MOVER, BG = 9, 8, 0
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}


class DynamicsEnv(Arc3Env):
    game_id = "dynamics"
    grid_h = 16
    grid_w = 16

    def __init__(self, mode: str = "chase", **kw):
        self.mode = mode
        super().__init__(**kw)

    def _init_world(self) -> None:
        self._ar, self._ac = 8, 3                  # avatar (self)
        self._mr, self._mc = 8, 12                 # mover
        self._mvr, self._mvc = 0, -1               # const velocity (toward avatar), bounces
        self._caught = 0

    def _render(self) -> Grid:
        g = [[BG] * self.grid_w for _ in range(self.grid_h)]
        g[self._mr][self._mc] = MOVER
        g[self._ar][self._ac] = SELF
        return g

    def _respawn_mover(self):
        self._mr, self._mc = 8, self.grid_w - 4
        self._mvr, self._mvc = 0, -1

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        if action in _DIR:
            dr, dc = _DIR[action]
            nr, nc = self._ar + dr, self._ac + dc
            if 0 <= nr < self.grid_h and 0 <= nc < self.grid_w:
                self._ar, self._ac = nr, nc
        # mover: const velocity, reflect at walls
        nmr, nmc = self._mr + self._mvr, self._mc + self._mvc
        if not (0 <= nmr < self.grid_h):
            self._mvr = -self._mvr; nmr = self._mr + self._mvr
        if not (0 <= nmc < self.grid_w):
            self._mvc = -self._mvc; nmc = self._mc + self._mvc
        self._mr, self._mc = nmr, nmc
        contact = (self._ar, self._ac) == (self._mr, self._mc)
        if contact:
            if self.mode == "dodge":
                self._state = GameState.GAME_OVER
            else:
                self._score += 1; self._caught += 1; self._respawn_mover()
        else:
            self._state = GameState.NOT_FINISHED
