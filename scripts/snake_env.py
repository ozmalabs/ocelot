"""snake_env — the game of SNAKE as an Arc3Env-contract world (the WORLD, not the agent).

A self-contained Snake environment behind the SAME interaction contract as arc3_env (RESET /
ACTION1..4 = up/down/left/right, GameState, a grid of 0..15 colour indices). The agent plays it
through the EXACT path it would play ARC — `ArcWorld(SnakeEnv())` → perceive_frame → master_tick →
read chosen_action → apply — so nothing about the agent is snake-specific; only this world is.

The rules live HERE, behind step(); the agent must INFER them from observed transitions (what it
controls, that the head moves each step, that food grows it, that walls/self end it). It is the
honest test bed for the curiosity/understanding loop on a game with AUTONOMOUS dynamics (the snake
keeps moving), unlike the turn-static ARC toys.

Colours (arc3 palette): head=9 (blue), body=14 (green), food=8 (red), background=0 (white).
"""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

Grid = List[List[int]]

HEAD, BODY, FOOD, BG = 9, 14, 8, 0
_DIR = {ACTION1: (-1, 0), ACTION2: (1, 0), ACTION3: (0, -1), ACTION4: (0, 1)}  # up/down/left/right


class SnakeEnv(Arc3Env):
    """Snake on a grid. The snake advances one cell per step in its current heading; an
    ACTION1..4 turns it first (a direct reversal into its own neck is ignored, as in classic
    snake). Eating food grows it and scores; a wall or self collision ends the game."""

    game_id = "snake"
    grid_h = 12
    grid_w = 12

    def __init__(self, seed: int = 1234) -> None:
        self._rng = random.Random(seed)
        super().__init__()

    def _init_world(self) -> None:
        r, c = self.grid_h // 2, self.grid_w // 2
        self._snake: List[Tuple[int, int]] = [(r, c), (r, c - 1), (r, c - 2)]  # head first
        self._dir: Tuple[int, int] = (0, 1)                                    # heading right
        self._place_food()

    def _place_food(self) -> None:
        empty = [(r, c) for r in range(self.grid_h) for c in range(self.grid_w)
                 if (r, c) not in self._snake]
        self._food = self._rng.choice(empty) if empty else None
        if self._food is None:
            self._state = GameState.WIN                                        # board filled — perfect game

    def _render(self) -> Grid:
        g = [[BG] * self.grid_w for _ in range(self.grid_h)]
        if self._food is not None:
            g[self._food[0]][self._food[1]] = FOOD
        for i, (r, c) in enumerate(self._snake):
            g[r][c] = HEAD if i == 0 else BODY
        return g

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        # turn (unless a direct reversal into the neck), then advance one cell.
        if action in _DIR:
            dr, dc = _DIR[action]
            if not (len(self._snake) > 1 and (dr, dc) == (-self._dir[0], -self._dir[1])):
                self._dir = (dr, dc)
        hr, hc = self._snake[0]
        nr, nc = hr + self._dir[0], hc + self._dir[1]
        # wall collision
        if not (0 <= nr < self.grid_h and 0 <= nc < self.grid_w):
            self._state = GameState.GAME_OVER
            return
        eating = self._food is not None and (nr, nc) == self._food
        body = self._snake if eating else self._snake[:-1]   # tail vacates unless we grow this step
        if (nr, nc) in body:                                 # self collision
            self._state = GameState.GAME_OVER
            return
        self._snake.insert(0, (nr, nc))
        if eating:
            self._score += 1
            self._place_food()
        else:
            self._snake.pop()


if __name__ == "__main__":
    # Smoke: drive it in a square and print the grid transitions.
    env = SnakeEnv()
    f = env.reset()
    print(f"reset: state={f.state.value} score={f.score} grid={env.grid_h}x{env.grid_w}")
    for a in [ACTION4, ACTION4, ACTION2, ACTION2, ACTION3, ACTION1]:
        f = env.step(a)
        nz = sum(1 for row in f.grid for v in row if v != 0)
        print(f"  {a}: state={f.state.value} score={f.score} cells={nz}")
