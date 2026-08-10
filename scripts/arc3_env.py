"""arc3_env — a FAITHFUL OFFLINE re-implementation of the ARC-AGI-3 interaction
protocol, for building + testing the interactive world-modeling loop WITHOUT
live-API access.

WHY OFFLINE. ARC-AGI-3 is the interactive ARC benchmark (turn-based game
environments; infer rules + goal by ACTING; build a world model; plan). The
live public-preview environments (ft09 / ls20 / vc33) are served from
https://three.arcprize.org/api/... and REQUIRE an ARC_API_KEY:

    $ curl -s -X POST https://three.arcprize.org/api/scorecard/open -d '{}'
    {"error":"NOT_AUTHORIZED","message":"no key provided"}
    $ curl -s https://three.arcprize.org/api/games
    unauthorized

No key is present in this environment (env has no ARC_API_KEY). So the loop is
exercised against a FAITHFUL re-implementation of the PUBLISHED protocol — NOT
the real games (their rules are private). What is faithful here is the
INTERACTION CONTRACT, copied from the public spec (docs.arcprize.org):

  · GRID:   up to 64x64, integer cell values 0..15 (color/state indices),
            (0,0) top-left, (x, y) addressing.
  · FRAME:  the observation is a list of 1..N grids (each a list-of-rows).
  · ACTIONS: RESET, ACTION1 (up), ACTION2 (down), ACTION3 (left),
            ACTION4 (right), ACTION5 (interact/select/execute), ACTION6(x, y)
            (a coordinate action; x,y in 0..63), ACTION7 (undo).
  · STATE:  GameState in {NOT_PLAYED, NOT_FINISHED, WIN, GAME_OVER}.
  · step(action) -> Frame{ game_id, guid, state, score, frame }, exactly the
            shape the real SDK's env.step() returns.

THE GAMES BELOW ARE NOT the private ARC-3 games. They are small original
grid-games with the SAME interaction contract, written so the AGENT side
(arc3_agent.py) sees ONLY the protocol — never the rules. The rules live HERE,
behind step(); the agent must INFER them from observed transitions. This is the
honest substitute for the live env: it lets the world-modeling loop be built and
measured end-to-end; the SAME agent code would drive the real API by swapping
this Env for an HTTP client (the contract is identical).

NO substrate dependency here — this is purely the WORLD ADAPTER (the env). The
reasoning lives in arc3_agent.py.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

Grid = List[List[int]]


# ===========================================================================
# THE PUBLISHED PROTOCOL — actions + state, copied from the ARC-3 spec.
# ===========================================================================

class GameState(str, Enum):
    NOT_PLAYED = "NOT_PLAYED"
    NOT_FINISHED = "NOT_FINISHED"
    WIN = "WIN"
    GAME_OVER = "GAME_OVER"


# The 7 simple actions + the coordinate action. ACTION6 carries (x, y).
RESET = "RESET"
ACTION1 = "ACTION1"   # up
ACTION2 = "ACTION2"   # down
ACTION3 = "ACTION3"   # left
ACTION4 = "ACTION4"   # right
ACTION5 = "ACTION5"   # interact / select / execute
ACTION6 = "ACTION6"   # coordinate action (x, y)
ACTION7 = "ACTION7"   # undo

SIMPLE_ACTIONS = [ACTION1, ACTION2, ACTION3, ACTION4, ACTION5]


@dataclass
class Frame:
    """The step() return value — the exact shape the real SDK exposes."""
    game_id: str
    guid: str
    state: GameState
    score: int
    frame: List[Grid]       # 1..N grids
    action_input: Optional[Tuple[str, Optional[Tuple[int, int]]]] = None

    @property
    def grid(self) -> Grid:
        """Convenience: the first (and here only) grid of the frame."""
        return self.frame[0]


# ===========================================================================
# THE ENV BASE — the interaction contract. Subclasses supply the hidden rules.
# ===========================================================================

class Arc3Env:
    """Base class implementing the protocol; the rules are in subclasses.

    The agent only ever calls reset() and step(action[, coord]) and reads the
    returned Frame. It never reaches into the env's hidden state.
    """

    game_id: str = "base"
    grid_h: int = 8
    grid_w: int = 8

    def __init__(self) -> None:
        self._guid = f"{self.game_id}-guid"
        self._state = GameState.NOT_PLAYED
        self._score = 0
        self._steps = 0
        self._init_world()

    # -- to be supplied by subclasses ------------------------------------
    def _init_world(self) -> None:
        raise NotImplementedError

    def _render(self) -> Grid:
        """Project the hidden world state to the visible grid."""
        raise NotImplementedError

    def _apply(self, action: str, coord: Optional[Tuple[int, int]]) -> None:
        """Mutate the hidden world state for an action; set state/score."""
        raise NotImplementedError

    # -- the protocol (fixed) --------------------------------------------
    def reset(self) -> Frame:
        self._state = GameState.NOT_FINISHED
        self._score = 0
        self._steps = 0
        self._init_world()
        return self._frame(action_input=(RESET, None))

    def step(self, action: str, coord: Optional[Tuple[int, int]] = None,
             reasoning=None) -> Frame:
        # `reasoning` is part of the live contract (it routes the agent's narration to
        # the API replay). The offline env has no replay, so it accepts and ignores it —
        # honouring the SAME step() signature so the world adapter is byte-for-byte
        # identical whether it wraps the live or the offline env.
        if self._state in (GameState.WIN, GameState.GAME_OVER):
            # Terminal: only RESET re-enters play (mirrors the real env).
            return self._frame(action_input=(action, coord))
        if action == RESET:
            return self.reset()
        self._steps += 1
        self._apply(action, coord)
        return self._frame(action_input=(action, coord))

    def _frame(self, action_input) -> Frame:
        return Frame(
            game_id=self.game_id,
            guid=self._guid,
            state=self._state,
            score=self._score,
            frame=[copy.deepcopy(self._render())],
            action_input=action_input,
        )


# ===========================================================================
# GAME A — "navigate": a movable agent-cell on a grid must reach a goal-cell,
# avoiding wall-cells. The agent must INFER: which color is itself, which
# directions ACTION1..4 map to, that walls block, that reaching the goal WINS.
# ===========================================================================

EMPTY, AGENT, GOAL, WALL = 0, 3, 4, 5


class NavigateEnv(Arc3Env):
    game_id = "navigate"
    grid_h = 8
    grid_w = 8

    def _init_world(self) -> None:
        self._ar, self._ac = 6, 1          # agent start (row, col)
        self._gr, self._gc = 1, 6          # goal
        self._walls = {(3, 3), (3, 4), (4, 3), (4, 4), (2, 6)}

    def _render(self) -> Grid:
        g = [[EMPTY] * self.grid_w for _ in range(self.grid_h)]
        for (r, c) in self._walls:
            g[r][c] = WALL
        g[self._gr][self._gc] = GOAL
        g[self._ar][self._ac] = AGENT
        return g

    def _apply(self, action, coord):
        dr, dc = 0, 0
        if action == ACTION1:   dr = -1     # up
        elif action == ACTION2: dr = +1     # down
        elif action == ACTION3: dc = -1     # left
        elif action == ACTION4: dc = +1     # right
        # ACTION5 / ACTION6 do nothing in this game.
        nr, nc = self._ar + dr, self._ac + dc
        if 0 <= nr < self.grid_h and 0 <= nc < self.grid_w and (nr, nc) not in self._walls:
            self._ar, self._ac = nr, nc
        if (self._ar, self._ac) == (self._gr, self._gc):
            self._state = GameState.WIN
            self._score = 1


# ===========================================================================
# GAME B — "switches": three switch-cells must all be toggled ON (ACTION6 click
# on a switch toggles it). When all three are ON, WIN. The agent must INFER:
# that ACTION6(x,y) on a switch flips its color, that the goal is all-on, and
# that simple actions do nothing. Distinct mechanic from GAME A (coordinate
# action, no movable avatar) — proves the loop isn't navigate-specific.
# ===========================================================================

OFF, ON = 1, 2


class SwitchesEnv(Arc3Env):
    game_id = "switches"
    grid_h = 6
    grid_w = 6

    def _init_world(self) -> None:
        self._switches = {(1, 1): False, (2, 4): False, (4, 2): False}

    def _render(self) -> Grid:
        g = [[EMPTY] * self.grid_w for _ in range(self.grid_h)]
        for (r, c), on in self._switches.items():
            g[r][c] = ON if on else OFF
        return g

    def _apply(self, action, coord):
        if action == ACTION6 and coord is not None:
            x, y = coord            # (x, y) -> (col, row)
            cell = (y, x)
            if cell in self._switches:
                self._switches[cell] = not self._switches[cell]
        if all(self._switches.values()):
            self._state = GameState.WIN
            self._score = 1


# ===========================================================================
# GAME C — "collect" (a MEDIUM test, between switches and the live frontier).
# The grid holds TARGET cells (one colour) scattered among DISTRACTOR cells (two
# other colours). An ACTION6 click on a TARGET removes it and scores +1 (a GRADED
# reward — a foothold: partial progress is visible); a click on a distractor or
# empty does nothing. WIN when every target is collected. The agent must INDUCE
# *which colour* is collectable — the win-rule is "click colour-T → it ceases →
# reward", with position abstracted across the several collection events and the
# two distractor colours excluded. Harder than switches (discrimination among
# colours, multiple sub-goals, generalise over position) yet crackable and
# debuggable (graded score shows how far it gets).
# ===========================================================================

TARGET, DISTRACTOR_A, DISTRACTOR_B = 4, 5, 6


class CollectEnv(Arc3Env):
    game_id = "collect"
    grid_h = 8
    grid_w = 8

    def _init_world(self) -> None:
        # Targets (collectable) at varied positions, so the win-rule generalises
        # over POSITION (abstracted) and keys on COLOUR. Distractors of two other
        # colours that clicking never rewards (the discrimination to induce).
        self._targets = {(1, 2), (2, 6), (4, 4), (5, 1), (6, 5)}
        self._distractors = {(1, 5): DISTRACTOR_A, (3, 2): DISTRACTOR_B,
                             (4, 6): DISTRACTOR_A, (6, 2): DISTRACTOR_B}

    def _render(self) -> Grid:
        g = [[EMPTY] * self.grid_w for _ in range(self.grid_h)]
        for (r, c), v in self._distractors.items():
            g[r][c] = v
        for (r, c) in self._targets:
            g[r][c] = TARGET
        return g

    def _apply(self, action, coord):
        if action == ACTION6 and coord is not None:
            x, y = coord            # (x, y) -> (col, row)
            cell = (y, x)
            if cell in self._targets:
                self._targets.discard(cell)   # collected: it ceases
                self._score += 1              # GRADED reward — the foothold
        if not self._targets:
            self._state = GameState.WIN


# ===========================================================================
# GAME D — "symmetry" (a MEDIUM test for AESTHETIC GROUNDING). Every cell is
# coloured (A or B, never empty); an ACTION6 click toggles a cell A<->B. A few
# cells break vertical (mirror) symmetry. WIN when the grid is symmetric — score
# ONLY on win (all-or-nothing, NO graded foothold). The only signal that leads to
# the win is the AESTHETIC gradient: each toggle that makes the grid more
# symmetric (more compressible / beautiful) is intrinsically rewarding, and the
# win sits at the gradient's peak. Tests whether beauty-as-compression can crack a
# game that gives no external reward until solved.
# ===========================================================================

COL_A, COL_B = 4, 5


class SymmetryEnv(Arc3Env):
    game_id = "symmetry"
    grid_h = 4
    grid_w = 4

    def _init_world(self) -> None:
        # Base: all A (trivially symmetric), a symmetric B-pattern, then a few
        # cells flipped to BREAK symmetry — the errors the agent must fix.
        self._cells = {(r, c): COL_A for r in range(self.grid_h)
                       for c in range(self.grid_w)}
        for cell in ((0, 1), (0, 2), (3, 0), (3, 3)):   # symmetric B pairs (ok)
            self._cells[cell] = COL_B
        for cell in ((1, 0), (2, 3)):                   # asymmetric ERRORS to fix
            self._cells[cell] = COL_B

    def _render(self) -> Grid:
        g = [[EMPTY] * self.grid_w for _ in range(self.grid_h)]
        for (r, c), v in self._cells.items():
            g[r][c] = v
        return g

    def _symmetric(self) -> bool:
        for r in range(self.grid_h):
            for c in range(self.grid_w):
                if self._cells[(r, c)] != self._cells[(r, self.grid_w - 1 - c)]:
                    return False
        return True

    def _apply(self, action, coord):
        if action == ACTION6 and coord is not None:
            x, y = coord
            cell = (y, x)
            if cell in self._cells:
                self._cells[cell] = COL_B if self._cells[cell] == COL_A else COL_A
        if self._symmetric():
            self._state = GameState.WIN
            self._score = 1


# ===========================================================================
# GAMES E/F/G — more pattern kinds, to prove AESTHETIC GROUNDING is not mirror-
# specific. Same shape as SymmetryEnv (cells toggle A<->B, win all-or-nothing on a
# target REGULARITY) — the agent must crack each by climbing the SAME aesthetic
# gradient, recognising whichever pattern the win-state exhibits.
# ===========================================================================


class _TogglePatternEnv(Arc3Env):
    """Base: a full A/B grid the agent toggles; WIN when ``_satisfied`` holds."""
    grid_h = 4
    grid_w = 4
    _errors = ()
    _base = ()

    def _init_world(self) -> None:
        self._cells = {(r, c): COL_A for r in range(self.grid_h)
                       for c in range(self.grid_w)}
        for cell in self._base:
            self._cells[cell] = COL_B
        for cell in self._errors:
            self._cells[cell] = COL_B if self._cells[cell] == COL_A else COL_A

    def _render(self) -> Grid:
        g = [[EMPTY] * self.grid_w for _ in range(self.grid_h)]
        for (r, c), v in self._cells.items():
            g[r][c] = v
        return g

    def _satisfied(self) -> bool:
        raise NotImplementedError

    def _apply(self, action, coord):
        if action == ACTION6 and coord is not None:
            x, y = coord
            cell = (y, x)
            if cell in self._cells:
                self._cells[cell] = COL_B if self._cells[cell] == COL_A else COL_A
        if self._satisfied():
            self._state = GameState.WIN
            self._score = 1


class RotateEnv(_TogglePatternEnv):           # win = 180° rotational symmetry
    game_id = "rotate"
    _base = ((0, 1), (3, 2), (1, 0), (2, 3))   # rot-180 pairs (consistent)
    _errors = ((0, 0), (2, 1))                  # break it

    def _satisfied(self) -> bool:
        h, w = self.grid_h, self.grid_w
        return all(self._cells[(r, c)] == self._cells[(h - 1 - r, w - 1 - c)]
                   for r in range(h) for c in range(w))


class UniformEnv(_TogglePatternEnv):           # win = all one colour
    game_id = "uniform"
    _base = ((0, 1), (2, 3), (3, 0))            # a few B among A

    def _satisfied(self) -> bool:
        return len(set(self._cells.values())) == 1


class PeriodicEnv(_TogglePatternEnv):          # win = row-period-2 (rows 0,1 tile)
    game_id = "periodic"
    _base = ((0, 1), (2, 1), (1, 3), (3, 3))    # period-2 consistent pairs
    _errors = ((2, 0), (3, 2))                  # break the tiling

    def _satisfied(self) -> bool:
        h, w = self.grid_h, self.grid_w
        return all(self._cells[(r, c)] == self._cells[(r % 2, c)]
                   for r in range(h) for c in range(w))


# ===========================================================================
# GAME H — "draw the cool S": an ARBITRARY, NON-symmetric FORM. Built-in symmetry
# / period / uniform bases CANNOT crack it — only a LEARNED form template can. The
# agent ACQUIRES the S (by perceiving it once), then draws it on a blank canvas by
# climbing the aesthetic gradient toward that held form. Proves aesthetics is the
# agent's OPEN repertoire of forms, not a fixed catalogue.
# ===========================================================================

# The cool S (5×5), the cells that are "drawn" (colour B); rest is background A.
S_FORM = {(0, 1), (0, 2), (0, 3), (1, 1), (2, 1), (2, 2), (2, 3),
          (3, 3), (4, 1), (4, 2), (4, 3)}


class DrawSEnv(Arc3Env):
    game_id = "draw_s"
    grid_h = 5
    grid_w = 5

    def __init__(self, show: bool = False) -> None:
        self._show = show          # show=True renders the S (for acquisition)
        super().__init__()

    def _init_world(self) -> None:
        self._cells = {(r, c): COL_A for r in range(self.grid_h)
                       for c in range(self.grid_w)}
        if self._show:
            for cell in S_FORM:
                self._cells[cell] = COL_B

    def _render(self) -> Grid:
        return [[self._cells[(r, c)] for c in range(self.grid_w)]
                for r in range(self.grid_h)]

    def _satisfied(self) -> bool:
        return all((self._cells[(r, c)] == COL_B) == ((r, c) in S_FORM)
                   for r in range(self.grid_h) for c in range(self.grid_w))

    def _apply(self, action, coord):
        if action == ACTION6 and coord is not None:
            x, y = coord
            cell = (y, x)
            if cell in self._cells:
                self._cells[cell] = COL_B if self._cells[cell] == COL_A else COL_A
        if self._satisfied():
            self._state = GameState.WIN
            self._score = 1


class CollectAllEnv(CollectEnv):
    """ALL-OR-NOTHING collect: clicking a target removes it, but the score rises
    ONLY when the LAST one is gone (win). No graded foothold — by its own play the
    agent never sees a reward until it has already solved it, so it cannot learn
    the win-rule by trial-and-error. The case where WATCHING A REPLAY is the only
    way in: the demonstration shows the win, the agent learns it, then plays."""
    game_id = "collect_all"

    def _apply(self, action, coord):
        if action == ACTION6 and coord is not None:
            x, y = coord
            cell = (y, x)
            if cell in self._targets:
                self._targets.discard(cell)        # removed, but NO graded score
        if not self._targets:
            self._state = GameState.WIN
            self._score = 1                        # reward only at the very end


ENVS = {
    "navigate": NavigateEnv,
    "switches": SwitchesEnv,
    "collect": CollectEnv,
    "collect_all": CollectAllEnv,
    "symmetry": SymmetryEnv,
    "rotate": RotateEnv,
    "uniform": UniformEnv,
    "periodic": PeriodicEnv,
    "draw_s": DrawSEnv,
}


if __name__ == "__main__":
    # smoke test: drive each env by hand to confirm the contract + a win exists.
    e = NavigateEnv()
    f = e.reset()
    print("navigate reset state:", f.state, "score:", f.score, "grid", len(f.grid), "x", len(f.grid[0]))
    # walk up to row 1 then right to col 6 (goal at 1,6); start (6,1)
    path = [ACTION1] * 5 + [ACTION4] * 5
    for a in path:
        f = e.step(a)
    print("navigate after path:", f.state, "score:", f.score)

    e2 = SwitchesEnv()
    f = e2.reset()
    for (r, c) in [(1, 1), (2, 4), (4, 2)]:
        f = e2.step(ACTION6, (c, r))   # (x=col, y=row)
    print("switches after toggles:", f.state, "score:", f.score)
