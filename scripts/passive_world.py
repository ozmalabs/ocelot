"""passive_world — Stage 0 of the jabberwock's own curriculum: a passive world to PREDICT.

The agent's design (docs/jabberwock_game_play_design.md), Stage 0: "I can predict a passive world. World:
static, then one dot moving at constant velocity. No me, no goals. Learn: the constant-velocity forward
model + the surprise signal. Mastered when: per-Region one-step error -> floor on a moving dot."

So this world is just a small block moving at constant velocity, bouncing off the edges (a bounce is the
one discontinuity its constant-velocity prior will be surprised by — honest). Same Arc3Env contract as the
others, so the agent perceives it through the identical eye. The agent does not act here; it only predicts.
Block = value 9 (blue) on background 0; a 2x2 block so the eye tracks it as one translating Region with
drow/dcol (a single cell is re-segmented each frame and shows no motion).
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState

Grid = List[List[int]]
DOT = 9
BG = 0


class PassiveDotEnv(Arc3Env):
    """A 2x2 block translating at constant velocity, bouncing at the walls. The agent's actions are
    ignored — the world evolves on its own; the agent's task is only to PREDICT it."""

    game_id = "passive_dot"
    grid_h = 20
    grid_w = 20
    SZ = 4                                    # block side. A 4x4 block moving (1,1) overlaps 9/16 frame-to-frame,
    transpose = False                        # so the eye TRACKS its identity (a 2x2 diagonal overlaps only 1/4
                                             # and gets re-IDed each frame -> no velocity, no genuine prediction).

    def __init__(self, transpose: bool = False) -> None:
        self.transpose = transpose
        super().__init__()

    def _init_world(self) -> None:
        self._r, self._c = 4, 4              # top-left of the block
        self._vr, self._vc = 1, 1            # constant velocity (down-right) until a bounce flips a component

    def _render(self) -> Grid:
        g = [[BG] * self.grid_w for _ in range(self.grid_h)]
        for dr in range(self.SZ):
            for dc in range(self.SZ):
                g[self._r + dr][self._c + dc] = DOT
        if self.transpose:                   # a DIFFERENT projection of the same dynamics (the decisive test)
            g = [list(row) for row in zip(*g)]
        return g

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        # the world ignores the agent and advances on its own (passive).
        nr, nc = self._r + self._vr, self._c + self._vc
        if nr < 0 or nr + self.SZ - 1 >= self.grid_h:    # bounce vertically
            self._vr = -self._vr
            nr = self._r + self._vr
        if nc < 0 or nc + self.SZ - 1 >= self.grid_w:    # bounce horizontally
            self._vc = -self._vc
            nc = self._c + self._vc
        self._r, self._c = nr, nc
        self._state = GameState.NOT_FINISHED     # never ends — there is nothing to win or lose, only to predict


if __name__ == "__main__":
    env = PassiveDotEnv()
    f = env.reset()
    print(f"reset: {env.grid_h}x{env.grid_w}, block at ({env._r},{env._c}) v=({env._vr},{env._vc})")
    for i in range(6):
        f = env.step("Select")
        print(f"  step{i}: block at ({env._r},{env._c}) v=({env._vr},{env._vc})")
