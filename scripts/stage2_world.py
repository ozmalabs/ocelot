"""stage2_world — Stage 2 of the jabberwock's curriculum: 'the boundary is destruction.'

The agent's design, Stage 2: "World: stage 1 + walls/edges. Learn: termination_prior — forward-rollout finds
no surviving trajectory through the boundary; I avoid it understood as loss of the Region all my agency
depends on. Mastered when: I stop predicting myself surviving the boundary; death rate falls with NO death
handler." So unlike Stage 1 (walls clamp), here moving the avatar off the world ENDS it (GAME_OVER). The
agent must avoid it by ROLLING ITS MODEL FORWARD (cy + action_delta) and seeing no continuation beyond the
world — not by dying and learning. Avatar = value 9 on background 0.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]
AV = 9
BG = 0
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}


class AvatarDeathEnv(Arc3Env):
    """A 2x2 avatar; moving it OFF the world is destruction (GAME_OVER) — the boundary is fatal."""

    game_id = "avatar_death"
    grid_h = 14
    grid_w = 14

    def _init_world(self) -> None:
        self._r, self._c = 6, 6

    def _render(self) -> Grid:
        g = [[BG] * self.grid_w for _ in range(self.grid_h)]
        for dr in (0, 1):
            for dc in (0, 1):
                g[self._r + dr][self._c + dc] = AV
        return g

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        if action not in _DIR:
            return
        dr, dc = _DIR[action]
        nr, nc = self._r + dr, self._c + dc
        if nr < 0 or nr + 1 >= self.grid_h or nc < 0 or nc + 1 >= self.grid_w:
            self._state = GameState.GAME_OVER       # off the world = destruction (no clamp)
            return
        self._r, self._c = nr, nc
