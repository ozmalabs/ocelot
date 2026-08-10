"""arc3_world — world ADAPTER plugging the CuriousAgent (the jabberwock) into
the offline ARC-AGI-3 interaction protocol (scripts/arc3_env.py).

This file is a WORLD ADAPTER, not an agent. Per the project's architecture
rule, all reasoning, modelling, exploration and planning live in the
CuriousAgent (a graph). This module does exactly two mechanical things:

  1. INGEST  — translate an ARC-3 Frame (a grid + score + game-state) into a
               Substrate the agent can observe. Each non-empty cell becomes a
               typed node (``CellC<color>``) carrying its (row, col, value);
               the game's score/state becomes a ``Game`` node. No rule of the
               game is encoded here — colours are opaque indices, directions
               are opaque action names. The agent must DISCOVER which cell is
               itself, what each action does, and what the goal is, purely
               from observed transitions.

  2. EMIT    — expose the four world callables the agent's driver loop needs
               (``reset`` / ``legal_actions`` / ``apply_action`` /
               ``interpret_acts_on``) plus ``preview_safe=False`` (the live
               env is stateful — calling ``step`` to preview would destroy
               world state, so the agent uses its LEARNED action statistics
               instead of simulating, exactly as it does for VizDoom).

The contract mirrors the other world handles (walker_world, doom_world):
a dict of callables consumed by CuriousAgent.choose_action / the driver.

NB: the live ARC-3 API (https://three.arcprize.org) returns 401 without an
ARC_API_KEY (none in this environment), so we drive the FAITHFUL OFFLINE
re-implementation in arc3_env. The agent code is identical to what would
drive the live API — only the Env object behind step() would change.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, Tuple

# arc3_env lives under scripts/ — make it importable without packaging.
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from arc3_env import (  # noqa: E402
    Arc3Env,
    Frame,
    GameState,
    ACTION1, ACTION2, ACTION3, ACTION4, ACTION5, ACTION6,
)

from substrate import (  # noqa: E402
    ConsistencyChecker,
    Grammar,
    Substrate,
    TypedGraph,
)


def _build_substrate(frame: Frame) -> Substrate:
    """Mechanical Frame -> Substrate translation. No game rules here.

    Each non-empty cell of the (first) grid becomes a node typed by its
    colour index. Typing by colour is the only structural choice: it gives
    the agent's co-occurrence / invariant / relation machinery stable
    *kinds* to count over (the same trick walker_world uses with distinct
    Item types). Whether a colour is 'the avatar' or 'a wall' is NOT stated
    — the agent learns that by watching which kind's cells move under which
    action.

    Cell ``id`` is the (row, col) the cell *currently occupies*, so a moving
    avatar keeps changing id (the agent perceives motion) while static walls
    keep theirs (the agent perceives permanence)."""
    g = TypedGraph()
    grid = frame.grid
    h = len(grid)
    w = len(grid[0]) if h else 0

    game_id = g._insert_node("Game", {
        "id": "game",
        "score": int(frame.score),
        "won": frame.state == GameState.WIN,
        "over": frame.state == GameState.GAME_OVER,
        "h": h,
        "w": w,
    })

    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue  # 0 = empty/background; absence is the default
            cell_id = g._insert_node(f"CellC{v}", {
                "id": f"{r}_{c}",
                "row": r,
                "col": c,
                "value": int(v),
                # Binned coords give the agent stable discrete attrs to
                # count co-occurrence over (mirrors walker's x_bin).
                "row_bin": r,
                "col_bin": c,
            })
            g._insert_edge(game_id, "has_cell", cell_id)

    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _occupied_cells(frame: Frame) -> list[Tuple[int, int]]:
    """(col, row) of every non-empty cell — the coordinate targets ACTION6
    can address. We restrict ACTION6 to occupied cells so the action set is
    bounded and meaningful; the agent still discovers WHICH clicks matter."""
    grid = frame.grid
    out: list[Tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                out.append((c, r))   # (x=col, y=row), the env's coord order
    return out


def arc3_world_handle(env: Arc3Env, agent) -> dict:
    """Build the world handle (the 4 callables) for a CuriousAgent.

    ``ctx`` threads the live env's most recent Frame. The env itself holds
    the mutable game state behind step(); ctx only carries the observable
    Frame plus bookkeeping the driver reads (score/state/win)."""

    def reset() -> Tuple[Substrate, dict]:
        frame = env.reset()
        ctx = _ctx_from_frame(frame)
        return _build_substrate(frame), ctx

    def _ctx_from_frame(frame: Frame) -> dict:
        return {
            "frame": frame,
            "score": int(frame.score),
            "won": frame.state == GameState.WIN,
            "over": frame.state == GameState.GAME_OVER,
            "tick": 0,
        }

    def legal_actions(s, ctx) -> list:
        """The 5 simple actions plus one ACTION6 per occupied cell.

        Action tuples are single-element so canonical_action_kind keeps a
        bare, distinct name per action — each gets its own learned stat.
        Directions are opaque ('a1'..'a5'); coordinate clicks are
        'c6_<x>_<y>'. No direction->meaning mapping is supplied."""
        acts: list = [("a1",), ("a2",), ("a3",), ("a4",), ("a5",)]
        for (x, y) in _occupied_cells(ctx["frame"]):
            acts.append((f"c6_{x}_{y}",))
        return acts

    _ACTION_MAP = {
        "a1": ACTION1, "a2": ACTION2, "a3": ACTION3,
        "a4": ACTION4, "a5": ACTION5,
    }

    def _decode(action) -> Tuple[str, Optional[Tuple[int, int]]]:
        name = action[0]
        if name in _ACTION_MAP:
            return _ACTION_MAP[name], None
        # coordinate action: 'c6_<x>_<y>'
        _, xs, ys = name.split("_")
        return ACTION6, (int(xs), int(ys))

    def apply_action(s, ctx, action) -> Tuple[Substrate, dict]:
        """STATEFUL: advances the real env. (preview_safe=False means the
        agent never calls this speculatively — only the committed action
        reaches here.)"""
        env_action, coord = _decode(action)
        frame = env.step(env_action, coord)
        new_ctx = _ctx_from_frame(frame)
        new_ctx["tick"] = ctx.get("tick", 0) + 1
        return _build_substrate(frame), new_ctx

    def interpret_acts_on(s, ctx, action) -> list[str]:
        """Which body-types does this action touch? We do NOT know the
        rules, so we report the kinds PRESENT in the current observation —
        the action is 'directed at' the things the agent can currently see.
        This feeds the agent's acts_on relation (boundary asymmetry); it is
        deliberately rule-agnostic. The agent learns the real effect of each
        action from the observed transition, not from this hint."""
        present: set[str] = set()
        for node in s.graph.nodes():
            if node.type.startswith("CellC"):
                present.add(node.type)
        return sorted(present)

    return {
        "name": f"arc3_{env.game_id}",
        # The live env IS the state; step() mutates it. The agent must not
        # preview by stepping. Falls back to learned action stats.
        "preview_safe": False,
        "reset": reset,
        "legal_actions": legal_actions,
        "apply_action": apply_action,
        "interpret_acts_on": interpret_acts_on,
    }
