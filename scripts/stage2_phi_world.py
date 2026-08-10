"""stage2_phi_world — 'the boundary is destruction', in the N-D representation.

Stage 2 of the agent's curriculum, lifted to phi. A 4x4 avatar (value 9, the agent's controllable Region) on
a background board. Moving it OFF the board is destruction (GAME_OVER) — the boundary is FATAL, there is no
clamp. The agent must avoid it not by dying and learning, but by ROLLING ITS OWN MODEL FORWARD: it holds the
self's controllable basis (resp_<A> = the per-action displacement of phi) from the compensated discriminator,
so it can predict where each action carries the self's bbox and recognise an action whose rollout leaves the
board as having NO modelled continuation = termination. The walls are death, understood as a prior.

4x4 (not 2x2) so the eye keeps a stable identity across motion (a 2x2 mover re-IDs). Starts centred so the
exploration warmup can learn resp safely before the agent takes control.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]
AV = 9
BG = 0
SZ = 4
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}


class AvatarDeathEnv4(Arc3Env):
    """A 4x4 avatar; moving it OFF the world is destruction (GAME_OVER) — the boundary is fatal, no clamp."""

    game_id = "avatar_death4"
    grid_h = 20
    grid_w = 20

    def _init_world(self) -> None:
        self._r, self._c = 8, 8                  # centred, so the warmup can learn resp without hitting a wall

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
            self._state = GameState.GAME_OVER       # off the world = destruction (no clamp)
            return
        self._r, self._c = nr, nc
