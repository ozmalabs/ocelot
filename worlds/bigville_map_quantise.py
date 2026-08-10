"""bigville_map_quantise -- block 341000/342000: MULTIPLE QUANTISATIONS of the generated map.

The generated town (block 340000) is a containment hierarchy Town ⊃ Place ⊃ Room. Routing
over it is HIERARCHICAL and LANDMARK-BASED, not a town-wide flood (342000 rework): people do
not hold a distance field over every cell -- they route to LANDMARKS in steps ("head to the
church; once there, find the counsel room"), which is far cheaper and its cost is INDEPENDENT
of town size. The three grains fall straight out of the hierarchy:

    coarse (landmarks) -- Places + the Square; a short hop-chain src -> Square -> dst
    building (interior) -- the room door-chain WITHIN a building, refined only where you are
    room (tiles)        -- a LAZY, FOVEATED tile grid inside ONE focused room (bump / squeeze)

Cost: a landmark route touches only the two endpoint buildings' rooms + the landmark chain --
O(path), invariant to how many OTHER buildings exist. A town-wide flood touches ~every room.
The fine (tile) grain is materialised only for a room in focus; it makes BUMPING (two bodies,
one tile) and SQUEEZE-PAST (stepping onto an occupied tile) visible.

A WORLD ADAPTER: mechanical projection + reads over the generated map's own graph. No agent
decisions, and -- per the routing critique -- no town-wide flood.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_map_generator import BigvilleMapGenerator   # noqa: E402


class QuantisedMap:
    def __init__(self, *, seed=0, spec=None):
        self.gen = BigvilleMapGenerator(spec=spec, seed=seed).generate()
        self.eng = self.gen.eng
        self._tiles = {}          # (place, room_kind) -> {(tx,ty): cell}
        self._occupy = {}         # body name -> (place, room_kind, tx, ty)

    # ------------------------------------------------------------------ landmark routing
    def _room_kinds(self, place):
        return [k for _, k in self.gen._room_list[place]]

    def _interior(self, place, from_kind, to_kind):
        """Steps along the door-chain WITHIN one building (foveated -- only this building).
        The generator chains rooms, so this is a slice, O(rooms in this building)."""
        kinds = self._room_kinds(place)
        a, b = kinds.index(from_kind), kinds.index(to_kind)
        rng = range(a, b + 1) if a <= b else range(a, b - 1, -1)
        return [f"{place}:{kinds[i]}" for i in rng]

    def landmark_route(self, src_place, src_room, dst_place, dst_room):
        """Route to LANDMARKS in steps. Returns the coarse landmark chain, the human-readable
        step list, and `touched` (nodes examined -- invariant to town size)."""
        if src_place == dst_place:
            steps = self._interior(src_place, src_room, dst_room)
            return {"landmarks": [src_place], "steps": steps, "touched": len(steps)}
        # exit the source building to its entrance, cross the square, enter the target building
        entrance_src = self._room_kinds(src_place)[0]
        entrance_dst = self._room_kinds(dst_place)[0]
        out_steps = self._interior(src_place, src_room, entrance_src)
        in_steps = self._interior(dst_place, entrance_dst, dst_room)
        steps = out_steps + ["Square"] + in_steps
        landmarks = [src_place, "Square", dst_place]
        # touched: the two endpoint interiors + the landmark chain -- NOT the whole town
        touched = len(out_steps) + len(in_steps) + len(landmarks)
        return {"landmarks": landmarks, "steps": steps, "touched": touched}

    def flood_cost_would_be(self):
        """What a town-wide fine flood would touch: ~every room in the town (+ the square).
        For contrast with the landmark route's town-size-invariant cost."""
        return 1 + sum(len(self.gen._room_list[p]) for p in self.gen.places())

    # ------------------------------------------------------------------ lazy fine grain
    def focus(self, place, room_kind, *, w=2, h=2):
        """FOVEATED: materialise a w×h tile grid inside ONE room, on demand. Unfocused rooms
        stay tile-less. Returns the tile count."""
        key = (place, room_kind)
        if key in self._tiles:
            return len(self._tiles[key])
        room = self.gen.room_node(place, room_kind)
        grid = {}
        for ty in range(h):
            for tx in range(w):
                grid[(tx, ty)] = self.eng.add_node("Tile", {"tx": float(tx), "ty": float(ty),
                                                            "in_room": self.eng.node(room)["attrs"]["name"]})
        for (tx, ty), c in grid.items():
            self.eng.add_edge_unchecked(room, "has_tile", c)
            for (dx, dy) in ((1, 0), (0, 1)):
                nb = grid.get((tx + dx, ty + dy))
                if nb is not None:
                    self.eng.add_edge_unchecked(c, "tile_adj", nb)
                    self.eng.add_edge_unchecked(nb, "tile_adj", c)
        self._tiles[key] = grid
        return len(grid)

    def tiles_in(self, place, room_kind):
        return len(self._tiles.get((place, room_kind), {}))

    # ------------------------------------------------------------------ bump / squeeze-past
    def occupy(self, body, place, room_kind, tx, ty):
        assert (place, room_kind) in self._tiles, "focus the room first (fine grain is lazy)"
        self._occupy[body] = (place, room_kind, tx, ty)

    def is_bump(self, a, b):
        return self._occupy.get(a) is not None and self._occupy.get(a) == self._occupy.get(b)

    def tile_occupant(self, place, room_kind, tx, ty):
        for body, loc in self._occupy.items():
            if loc == (place, room_kind, tx, ty):
                return body
        return None

    def must_squeeze_past(self, mover, place, room_kind, tx, ty):
        occ = self.tile_occupant(place, room_kind, tx, ty)
        return occ is not None and occ != mover
