"""avatar_run_world — a wide avatar world so committed action runs for many frames (multiple self-id
stability windows) without hitting the boundary. 4x4 avatar (value 9), off-board = GAME_OVER, starts left.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]
AV = 9
BG = 0
SZ = 4
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}


class AvatarRunEnv(Arc3Env):
    game_id = "avatar_run"
    grid_h = 20
    grid_w = 48

    def _init_world(self) -> None:
        self._r, self._c = 8, 4

    def _render(self) -> Grid:
        g = [[BG] * self.grid_w for _ in range(self.grid_h)]
        for dr in range(SZ):
            for dc in range(SZ):
                g[self._r + dr][self._c + dc] = AV
        return g

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        if action not in _DIR:
            return
        dr, dc = _DIR[action]
        nr, nc = self._r + dr, self._c + dc
        if nr < 0 or nr + SZ - 1 >= self.grid_h or nc < 0 or nc + SZ - 1 >= self.grid_w:
            self._state = GameState.GAME_OVER
            return
        self._r, self._c = nr, nc
