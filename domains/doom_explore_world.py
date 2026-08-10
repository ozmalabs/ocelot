"""doom_explore_world — the MECHANICAL world adapter for CONTROLLED-MOTOR active
exploration on REAL E1M1 geometry (block 205000).

NO agent decision lives here (CLAUDE.md). Three mechanical jobs, all sensor->graph
or graph->sensor translation; every WHERE-TO-GO decision is a rule/net in
seeds/quanta_navigation.json + seeds/doom_active_exploration.json:

  extract_e1m1_occupancy   run VizDoom E1M1 ONCE, read the sector blocking linedefs
                           (exact level geometry), flood the connected walkable
                           region from the player start over 64-unit cardinal steps
                           that do not cross a blocking line -> a ground-truth
                           occupancy grid. Cached to results/ (reproducible).

  reveal_in_view           the idealised eye: emit ObsCells (walk/depth_free/
                           depth_wall) for the walkable cells within a sensor radius
                           of the avatar that have unobstructed line-of-sight. This
                           is the NAMED idealisation that DECOUPLES sensing from the
                           motor policy (the real depth-from-motion eye is off-real-
                           time AND forward-only, which would confound the coverage
                           comparison -- see the prereg). unknown = ABSENCE.

  apply_action             read the graph's chosen control token and step the avatar
                           one cell in that cardinal direction (idealised motor). No
                           decision -- the direction was chosen by the graph.

The map ACCUMULATION + FRONTIER + curiosity + commit + nav are all rules; this file
only reveals, ticks the existing doom_map_ingest cadence, and moves the avatar.
"""
from __future__ import annotations

import json
import math
import os

CELL = 64.0
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "results", "doom_active_explore", "e1m1_occupancy.json")

# Absolute 4-direction cardinal motor (idealised): the maze's proven ControlResponse
# scheme (fixed dr,dc), so the quanta-nav qf_hop_* Dot-pick works out of the box.
DISP = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}


# --------------------------------------------------------------------- geometry
def _seg_intersect(ax, ay, bx, by, cx, cy, dx, dy):
    """True iff segment A-B properly crosses segment C-D (standard orientation test)."""
    def ccw(px, py, qx, qy, rx, ry):
        return (ry - py) * (qx - px) - (qy - py) * (rx - px)
    d1 = ccw(cx, cy, dx, dy, ax, ay)
    d2 = ccw(cx, cy, dx, dy, bx, by)
    d3 = ccw(ax, ay, bx, by, cx, cy)
    d4 = ccw(ax, ay, bx, by, dx, dy)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    return False


def _blocking_lines():
    """Read E1M1's blocking linedefs (exact wall geometry) from VizDoom's sector info.
    ORACLE geometry extraction -- run ONCE, mechanical."""
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.set_doom_game_path(WAD); g.set_doom_scenario_path(WAD); g.set_doom_map("E1M1")
    g.set_screen_resolution(vzd.ScreenResolution.RES_160X120)
    g.set_sectors_info_enabled(True)
    for v in (vzd.GameVariable.POSITION_X, vzd.GameVariable.POSITION_Y):
        g.add_available_game_variable(v)
    g.set_window_visible(False); g.set_mode(vzd.Mode.PLAYER)
    g.init(); g.new_episode()
    st = g.get_state()
    lines = []
    for s in st.sectors:
        for l in s.lines:
            if l.is_blocking:
                lines.append((l.x1, l.y1, l.x2, l.y2))
    px = float(g.get_game_variable(vzd.GameVariable.POSITION_X))
    py = float(g.get_game_variable(vzd.GameVariable.POSITION_Y))
    g.close()
    return lines, (px, py)


def extract_e1m1_occupancy(*, cell=CELL, use_cache=True):
    """Ground-truth walkable occupancy of E1M1: the connected component reachable from
    the player start by `cell`-unit cardinal steps whose center-to-center segment does
    NOT cross a blocking linedef. Returns {"walkable": set[(cx,cy)], "start": (cx,cy),
    "bounds": (minx,miny,maxx,maxy)}. Cached JSON (reproducible; run once)."""
    if use_cache and os.path.exists(CACHE):
        with open(CACHE) as f:
            d = json.load(f)
        return {"walkable": set(tuple(p) for p in d["walkable"]),
                "start": tuple(d["start"]), "bounds": tuple(d["bounds"])}
    lines, (spx, spy) = _blocking_lines()
    minx = min(min(l[0], l[2]) for l in lines); maxx = max(max(l[0], l[2]) for l in lines)
    miny = min(min(l[1], l[3]) for l in lines); maxy = max(max(l[1], l[3]) for l in lines)
    c0x, c0y = int(math.floor(spx / cell)), int(math.floor(spy / cell))
    lox, loy = int(math.floor(minx / cell)) - 1, int(math.floor(miny / cell)) - 1
    hix, hiy = int(math.floor(maxx / cell)) + 1, int(math.floor(maxy / cell)) + 1

    def cross_wall(a, b):
        ax = (a[0] + 0.5) * cell; ay = (a[1] + 0.5) * cell
        bx = (b[0] + 0.5) * cell; by = (b[1] + 0.5) * cell
        for (x1, y1, x2, y2) in lines:
            if _seg_intersect(ax, ay, bx, by, x1, y1, x2, y2):
                return True
        return False

    walkable = set()
    stack = [(c0x, c0y)]
    walkable.add((c0x, c0y))
    while stack:
        cur = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (cur[0] + dx, cur[1] + dy)
            if nb in walkable:
                continue
            if not (lox <= nb[0] <= hix and loy <= nb[1] <= hiy):
                continue
            if cross_wall(cur, nb):
                continue
            walkable.add(nb); stack.append(nb)
    out = {"walkable": sorted(list(walkable)), "start": [c0x, c0y],
           "bounds": [lox, loy, hix, hiy]}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump({"walkable": out["walkable"], "start": out["start"],
                   "bounds": out["bounds"]}, f)
    return {"walkable": walkable, "start": (c0x, c0y), "bounds": (lox, loy, hix, hiy)}


# --------------------------------------------------------------------- the world
class DoomExploreWorld:
    """Controlled-motor E1M1 explore world. Holds the ground-truth occupancy + the
    avatar's cell pose; reveals cells in view; applies the graph's chosen cardinal
    step. Decides nothing."""

    def __init__(self, occ, *, view_radius=5):
        self.walkable = occ["walkable"]
        self.start = occ["start"]
        self.bounds = occ["bounds"]
        self.view_radius = int(view_radius)
        self.pos = tuple(occ["start"])
        # a wall cell = a non-walkable cell 4-adjacent to a walkable cell (the boundary)
        self.wall = set()
        for (x, y) in self.walkable:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nb = (x + dx, y + dy)
                if nb not in self.walkable:
                    self.wall.add(nb)

    # ---- eye: reveal-in-view (mechanical, unknown = absence) ----
    def _los_clear(self, a, b):
        """Bresenham-ish supercover: line of sight from cell a to cell b is clear iff no
        wall cell lies strictly between them (occlusion). Avatar sees around obstacles up
        to the sensor radius."""
        (x0, y0), (x1, y1) = a, b
        dx = abs(x1 - x0); dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = x0, y0
        while (cx, cy) != (x1, y1):
            e2 = 2 * err
            if e2 > -dy:
                err -= dy; cx += sx
            if e2 < dx:
                err += dx; cy += sy
            if (cx, cy) == (x1, y1):
                break
            if (cx, cy) in self.wall and (cx, cy) not in self.walkable:
                return False
        return True

    def view_cells(self):
        """(free_cells, wall_cells) currently visible: walkable cells within the sensor
        radius with clear line of sight, plus the boundary wall cells adjacent to them."""
        px, py = self.pos
        R = self.view_radius
        free = []
        walls = set()
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                if dx * dx + dy * dy > R * R:
                    continue
                c = (px + dx, py + dy)
                if c in self.walkable and self._los_clear(self.pos, c):
                    free.append(c)
        for c in free:
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (c[0] + ddx, c[1] + ddy)
                if nb not in self.walkable and nb in self.wall:
                    walls.add(nb)
        return free, sorted(walls)

    # ---- motor: apply the graph's chosen cardinal step (idealised) ----
    def apply(self, control_name):
        """Step one cell in the chosen cardinal direction if walkable; return (moved, newpos).
        A blocked step (into a wall) does not move -- the belief already knows it is a wall."""
        d = DISP.get(control_name)
        if d is None:
            return False, self.pos
        nb = (self.pos[0] + d[0], self.pos[1] + d[1])
        if nb in self.walkable:
            self.pos = nb
            return True, self.pos
        return False, self.pos
