"""The THINNEST ARC-AGI-3 world shim: raw Frame <-> minimal Substrate, nothing else.

CLAUDE.md, taken seriously: a world adapter only translates external I/O. It does
NOT reason. The fat ``arc3_world`` smuggled cognition into the I/O layer — it built
a SpatialLocation map, ColourClass aggregates, 4-neighbour adjacency, bump-learned
boundaries, and a goal_cell hypothesis. All of that is the AGENT's job.

This shim does the minimum: it talks to the live ARC-AGI-3 API (via Arc3LiveEnv)
and presents each frame as the smallest graph token the agent can perceive:

  · a ``Game`` node  — score / win / over / h / w
  · a ``Body`` self-node (id=SELF_ID) — score / won / over, so observe() folds the
    score the agent FEELS (my_vel_score) for it to ground its own pursue-score drive
  · one raw ``CellC<value>`` node per non-empty cell — id "r_c", row, col, value

No SpatialLocation, no ColourClass, no adjacency, no boundary/passability, no
goal_cell. The jabberwock perceives the raw cells and does EVERYTHING else.

CHANGE-DRIVEN PERCEPTION (mechanical I/O, not cognition): each frame the shim
diffs the grid against the previous frame and marks which cells changed. The full
grid is always present in the substrate (so every faculty sees the whole world),
but the shim publishes, for observe() to attend to ONLY what changed:
  · ``substrate.arc3_self_ids``  — [Body id, Game id] (always re-perceived: score)
  · ``substrate.arc3_dirty_ids`` — node ids of the cells whose value changed this
                                   frame (frame 1: every occupied cell)
  · ``substrate.arc3_changed``   — True when the dirty set is authoritative
Re-perceiving an unchanged cell is wasted work; the marks let observe skip it.
``arc3_present_types`` caches the CellC types present (so interpret_acts_on is
O(distinct colours), not O(cells) per candidate action).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from arc3_env import (  # noqa: E402
    Frame, GameState,
    ACTION1, ACTION2, ACTION3, ACTION4, ACTION5, ACTION6,
)
from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph  # noqa: E402

SELF_ID = "agent_self"

_ACTION_MAP = {"a1": ACTION1, "a2": ACTION2, "a3": ACTION3,
               "a4": ACTION4, "a5": ACTION5}


def _grid_signature(grid) -> str:
    """A WHOLE-GRID structural token: the colour histogram over the full grid as
    one stable string. Pure mechanical aggregation of the external frame (the same
    class of I/O as publishing each CellC), at the WHOLE-GRID granularity instead
    of the per-cell one. Encodes NO game rule — it is just the whole grid rendered
    as one perceivable thing, so a faculty that attends to the whole grid has a
    grid-level observable to read, exactly as the per-cell faculties read CellC.
    Changes whenever the grid's global composition changes, so it drives a
    grid-level perceptual event the agent's order-N can range over."""
    counts: dict[int, int] = {}
    for row in grid:
        for v in row:
            iv = int(v)
            counts[iv] = counts.get(iv, 0) + 1
    return ";".join(f"{k}:{counts[k]}" for k in sorted(counts))


def _build_thin(frame: Frame, prev_grid, game_id_label: str = "live"):
    """Raw frame -> {Realm, Game, Body, GridConfig, CellC<v> per non-empty cell}
    + change marks. The Realm names the world (so the agent's own recognition can
    fire); the GridConfig publishes the WHOLE grid as one observable (so the order-N
    can range over grid-level structure, not only per-cell)."""
    g = TypedGraph()
    grid = frame.grid
    h = len(grid)
    w = len(grid[0]) if h else 0
    won = frame.state == GameState.WIN
    over = frame.state == GameState.GAME_OVER
    game_id = g._insert_node("Game", {
        "id": "game", "score": int(frame.score),
        "won": won, "over": over, "h": h, "w": w,
    })
    body_id = g._insert_node("Body", {
        "id": SELF_ID, "score": int(frame.score), "won": won, "over": over,
    })
    g._insert_edge(body_id, "inhabits", game_id)

    # The world NAMES ITSELF — a Realm the agent perceives via name_my_world().
    # name/map are the observable label (copied to last_name/last_map by observe);
    # is_a binds the perceived world to the grounded concept the agent comprehended
    # from the ARC-AGI-3 paper ('arc-agi-3 is-a interactive_reasoning_benchmark').
    # This is the minimal cue that lets the agent's OWN recognition fire — not a
    # hard-coded 'if arc then X'; the agent disposes of the binding itself.
    realm_id = g._insert_node("Realm", {
        "id": "realm", "name": "arc-agi-3", "map": str(game_id_label),
        "is_a": "interactive_reasoning_benchmark",
    })
    g._insert_edge(body_id, "inhabits", realm_id)

    # The WHOLE GRID as one observable (GridConfig). Its signature changes when the
    # grid's global composition changes, so observe() logs a grid-level perceptual
    # event (object_changed/came_into_view, GridConfig) — giving the SAME order-N
    # operator a whole-grid token to range over, alongside the per-cell CellC ones.
    grid_sig = _grid_signature(grid)
    grid_node = g._insert_node("GridConfig", {
        "id": "grid", "signature": grid_sig, "h": h, "w": w,
        "n_occupied": sum(1 for row in grid for v in row if int(v) != 0),
    })
    g._insert_edge(game_id, "has_grid", grid_node)
    prev_sig = _grid_signature(prev_grid) if prev_grid is not None else None

    occupied: set = set()
    present_types: set = set()
    dirty_ids: set = set()
    # Per-cell VALUE TRANSITIONS this frame — the adapter already diffs the grid,
    # so it mechanically exposes (x, y, from-type, to-type) for every changed cell.
    # The agent reads these as structured change-instances and INDUCES the rule
    # they imply (no reasoning here — pure I/O, the same class as the dirty diff).
    cell_changes: list = []
    # (x=col, y=row) -> the CellC type the agent perceives at that cell. The
    # agent's OWN typing of the cell a click would act ON — interpret_acts_on
    # reads this to give the click its TARGET-TYPE (so same-target-type clicks
    # share an action-type), and legal_actions publishes the type in the action
    # name so the agent learns at the target-type level, not per-coordinate.
    cell_type_at: dict = {}
    for r in range(h):
        row = grid[r]
        prow = prev_grid[r] if (prev_grid is not None and r < len(prev_grid)) else None
        for c in range(w):
            v = int(row[c])
            pv = int(prow[c]) if prow is not None else None
            if v != 0:
                cell = g._insert_node(f"CellC{v}", {
                    "id": f"{r}_{c}", "row": r, "col": c, "value": v,
                })
                g._insert_edge(game_id, "has_cell", cell)
                occupied.add((c, r))   # (x=col, y=row) — the env's coord order
                cell_type_at[(c, r)] = f"CellC{v}"
                present_types.add(f"CellC{v}")
                if pv != v:            # changed value (or first frame) -> dirty
                    dirty_ids.add(cell)
            # A VALUE TRANSITION at this cell (incl. ->empty). Only when there is a
            # prior frame to diff against (first-frame arrivals are came_into_view,
            # not transitions). frm/to are the agent's own CellC<v> types, empty=None.
            if prow is not None and pv != v:
                cell_changes.append({
                    "kind": "cell_value_change",
                    "frm": (f"CellC{pv}" if pv else None),
                    "to": (f"CellC{v}" if v else None),
                    "x": c, "y": r})

    sub = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
    # change-driven perception marks (mechanical I/O — a frame diff). The Realm is
    # always re-perceived (cheap, lets recognition fire each tick); the GridConfig
    # is dirty when its whole-grid signature changed (a grid-level change event).
    self_ids = [body_id, game_id, realm_id]
    sub.arc3_self_ids = self_ids
    if prev_sig is None or prev_sig != grid_sig:
        dirty_ids.add(grid_node)
    sub.arc3_dirty_ids = dirty_ids
    sub.arc3_cell_changes = cell_changes
    sub.arc3_changed = True
    sub.arc3_present_types = sorted(present_types)
    # The coord->target-type map (the agent's own CellC typing of each cell), so
    # interpret_acts_on can resolve the SPECIFIC cell a click acts on.
    sub.arc3_cell_type_at = cell_type_at
    # VISION side-channel — the agent isn't human; it has more senses. Render the
    # grid as an IMAGE (the optic nerve, like doom hands over its screen_buffer) so
    # the agent SEES it through its OWNED visual cortex (GraphEye → contours →
    # VisionPolygons → its seeded shape concepts), correlating that with the
    # symbolic CellC perception. Pure mechanical I/O: each cell → a colour block.
    sub.vision_screen = _render_screen(grid, h, w)
    # CONTEXT HINT to the eye: this is a DISCRETE GRID, not a camera frame — so the
    # cortex extracts exact colour-component figures instead of tracing luminance
    # contours (which on flat blocks finds only the outer outline). cell_px lets it
    # size the area floor to the grid's own scale.
    _cell_px = max(2, _SCREEN_MAX // max(h, w, 1))
    sub.vision_calibration = {"depth_scale": 1.0, "wall_clearance": 0.0,
                              "modality": "grid", "cell_px": _cell_px,
                              # grid dims so the eye's normalized shape coords map
                              # back to CELLS — lets vision LINK each perceived
                              # figure to the world thing it depicts.
                              "grid_shape": (int(h), int(w))}
    return sub, occupied, sub.arc3_present_types, cell_type_at


# A fixed palette: value 0 = black background; non-zero values = distinct hues so
# the visual cortex finds edges at colour boundaries and contours around regions.
_PALETTE = [
    (0, 0, 0), (230, 30, 30), (30, 200, 30), (40, 80, 240), (240, 220, 20),
    (240, 130, 20), (180, 40, 200), (20, 220, 220), (240, 110, 180),
    (140, 90, 40), (150, 150, 150), (120, 240, 120), (120, 160, 240),
    (200, 200, 200), (90, 40, 40), (40, 90, 90),
]
_SCREEN_MAX = 192   # cap the rendered image's largest side (keeps cv2 fast on 64×64)


def _render_screen(grid, h, w):
    """Grid → an (H,W,3) uint8 RGB image, each cell a block of its colour. The
    per-cell block is sized so the largest side stays ≤ _SCREEN_MAX — a 5×5 renders
    large, a 64×64 stays bounded — so the contour front-end has real edges to trace
    without a megapixel frame per tick. Mechanical render."""
    import numpy as np
    cell_px = max(2, _SCREEN_MAX // max(h, w, 1))
    img = np.zeros((max(1, h) * cell_px, max(1, w) * cell_px, 3), dtype=np.uint8)
    for r in range(h):
        row = grid[r]
        for c in range(w):
            col = _PALETTE[int(row[c]) % len(_PALETTE)]
            img[r * cell_px:(r + 1) * cell_px,
                c * cell_px:(c + 1) * cell_px] = col
    return img


def arc3_thin_handle(env, agent) -> dict:
    """The 4-callable world handle over a thin Frame<->Substrate translation."""
    state = {"prev_grid": None}
    game_label = getattr(env, "game_id", "live")

    def _ctx(frame: Frame, occ: set, present: list, cell_type_at: dict) -> dict:
        return {
            "frame": frame,
            "score": int(frame.score),
            "won": frame.state == GameState.WIN,
            "over": frame.state == GameState.GAME_OVER,
            "occupied": occ,
            "present_types": present,
            "cell_type_at": cell_type_at,
            "tick": 0,
        }

    def reset() -> Tuple[Substrate, dict]:
        frame = env.reset()
        state["prev_grid"] = None          # new episode -> first frame is all-dirty
        sub, occ, present, ctype = _build_thin(frame, state["prev_grid"], game_label)
        state["prev_grid"] = [row[:] for row in frame.grid]
        return sub, _ctx(frame, occ, present, ctype)

    def legal_actions(s, ctx) -> list:
        acts: list = [("a1",), ("a2",), ("a3",), ("a4",), ("a5",)]
        # An ACTION6 click's action NAME carries (a) the TARGET-TYPE the agent
        # already perceives at that cell (its CellC<v>), which becomes the
        # click's LEARNING IDENTITY via canonical_action_kind, and (b) the raw
        # x,y, which stay only as the EXECUTION coordinate the API needs. Same-
        # target-type clicks thus share one action-type (modal-config climbs past
        # 2) instead of being ~4100 one-off coordinate strings. The '@' joins so
        # the type and coords are cleanly separable; no game rule encoded.
        ctype = ctx.get("cell_type_at", {})
        for (x, y) in ctx.get("occupied", ()):
            t = ctype.get((x, y), "CellC")
            acts.append((f"c6@{t}@{x}@{y}",))
        return acts

    def _decode(action) -> Tuple[str, Optional[Tuple[int, int]]]:
        name = action[0]
        if name in _ACTION_MAP:
            return _ACTION_MAP[name], None
        # c6@CellC<v>@<x>@<y> — type for learning, x,y for execution.
        parts = name.split("@")
        x, y = int(parts[-2]), int(parts[-1])
        return ACTION6, (x, y)

    def apply_action(s, ctx, action) -> Tuple[Substrate, dict]:
        env_action, coord = _decode(action)
        frame = env.step(env_action, coord)
        sub, occ, present, ctype = _build_thin(frame, state["prev_grid"], game_label)
        state["prev_grid"] = [row[:] for row in frame.grid]
        nc = _ctx(frame, occ, present, ctype)
        nc["tick"] = ctx.get("tick", 0) + 1
        return sub, nc

    def interpret_acts_on(s, ctx, action) -> list[str]:
        # The body-types THIS action touches, in the agent's OWN typing. For an
        # ACTION6 click that is the SPECIFIC cell it acts on — the CellC<v> the
        # agent perceives at the clicked coordinate (resolved from the coord->type
        # map), NOT all present types. So the acts_on relation the click registers,
        # and the action-type it groups under, are its TARGET's type. The simple
        # actions (a1..a5) are not cell-targeted -> all present types (unchanged).
        name = action[0]
        if name.startswith("c6@"):
            parts = name.split("@")
            x, y = int(parts[-2]), int(parts[-1])
            ctype = getattr(s, "arc3_cell_type_at", None)
            if ctype is None:
                ctype = ctx.get("cell_type_at", {})
            t = ctype.get((x, y))
            return [t] if t is not None else []
        cached = getattr(s, "arc3_present_types", None)
        if cached is not None:
            return list(cached)
        return ctx.get("present_types", [])

    return {
        "name": f"arc3_thin_{getattr(env, 'game_id', 'live')}",
        "preview_safe": False,
        "reset": reset,
        "legal_actions": legal_actions,
        "apply_action": apply_action,
        "interpret_acts_on": interpret_acts_on,
    }
