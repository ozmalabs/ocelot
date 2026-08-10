"""mixed_world — a world with SELF + AUTONOMOUS + BACKGROUND, so the agent can discover the decomposition.

The agent's design: the N dimensions are discovered by how they behave under the loop — CONTROLLABLE (moves
by my action), AUTONOMOUS (moves without me — the world's own dynamics), INVARIANT (never moves). To discover
that, the world must contain all three. Here: a 4x4 AVATAR (value 9) the agent moves; a 4x4 AUTONOMOUS block
(value 8) that drifts on its own regardless of the agent; and the static background (invariant). This is the
structure of a real game seen from a camera: your piece, the other movers, the fixed board.

Both blocks are 4x4 so the eye tracks their identity across motion (a 2x2 moving diagonally is re-IDed).
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]
SELF = 9
AUTO = 8
JIT = 14            # a "jitterer": an autonomous block that CHANGES its own velocity (high velocity-
BG = 0              # variability, but still action-INDEPENDENT — the case the velvar proxy gets wrong)
SZ = 4
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}


class MixedEnv(Arc3Env):
    """A controlled avatar (9) + an autonomous drifter (8) + static background. Self, world, board."""

    game_id = "mixed"
    grid_h = 24
    grid_w = 24

    def _init_world(self) -> None:
        self._ar, self._ac = 4, 4                # avatar top-left (the agent moves it)
        self._dr, self._dc = 14, 14              # autonomous (constant velocity) block top-left
        self._dvr, self._dvc = -1, 1             # its own constant velocity (up-right), bounces
        self._jr, self._jc = 4, 16               # jitterer top-left
        self._jvr, self._jvc = 1, 0              # jitterer velocity; it REVERSES periodically (action-independent)
        self._t = 0

    def _blit(self, g, r, c, v):
        for dr in range(SZ):
            for dc in range(SZ):
                g[r + dr][c + dc] = v

    def _render(self) -> Grid:
        g = [[BG] * self.grid_w for _ in range(self.grid_h)]
        self._blit(g, self._dr, self._dc, AUTO)
        self._blit(g, self._jr, self._jc, JIT)
        self._blit(g, self._ar, self._ac, SELF)             # avatar drawn last (on top if overlapping)
        return g

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        # the avatar moves by the agent's action (clamped to the world).
        if action in _DIR:
            dr, dc = _DIR[action]
            nr, nc = self._ar + dr, self._ac + dc
            if 0 <= nr and nr + SZ - 1 < self.grid_h:
                self._ar = nr
            if 0 <= nc and nc + SZ - 1 < self.grid_w:
                self._ac = nc
        # the autonomous (constant-velocity) block moves on its OWN, regardless of the agent.
        ndr, ndc = self._dr + self._dvr, self._dc + self._dvc
        if ndr < 0 or ndr + SZ - 1 >= self.grid_h:
            self._dvr = -self._dvr; ndr = self._dr + self._dvr
        if ndc < 0 or ndc + SZ - 1 >= self.grid_w:
            self._dvc = -self._dvc; ndc = self._dc + self._dvc
        self._dr, self._dc = ndr, ndc
        # the JITTERER reverses its own velocity every 3 ticks (high velocity-variability, but ENTIRELY
        # action-independent — the velvar proxy mistakes it for controllable; action-correlation does not).
        self._t += 1
        if self._t % 3 == 0:
            self._jvr = -self._jvr
        njr = self._jr + self._jvr
        if njr < 0 or njr + SZ - 1 >= self.grid_h:
            self._jvr = -self._jvr; njr = self._jr + self._jvr
        self._jr = njr
        self._state = GameState.NOT_FINISHED
