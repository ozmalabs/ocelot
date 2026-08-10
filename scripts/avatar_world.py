"""avatar_world — Stage 1 of the jabberwock's curriculum: 'I exist; what I control.'

The agent's design, Stage 1: "World: my avatar in empty space; I emit actions; nothing else moves. Learn:
control_from_response + the action_delta map (my controls). Mastered when: action-conditioned error for my
Region drops below passive error — I can predict where I'll be after an action."

So this world is a 2x2 avatar the agent moves with Up/Down/Left/Right; nothing else moves; the walls just
clamp (no death yet — that is Stage 2). Same Arc3Env contract; the agent perceives it through the same eye.
Avatar = value 9 on background 0.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]
AV = 9
BG = 0
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}  # up/down/left/right


class AvatarEnv(Arc3Env):
    """A 2x2 avatar the agent moves; nothing else changes; walls clamp (no death)."""

    game_id = "avatar"
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
        if action in _DIR:
            dr, dc = _DIR[action]
            nr, nc = self._r + dr, self._c + dc
            if 0 <= nr and nr + 1 < self.grid_h:    # clamp (don't move off the world; no death in Stage 1)
                self._r = nr
            if 0 <= nc and nc + 1 < self.grid_w:
                self._c = nc
        self._state = GameState.NOT_FINISHED
