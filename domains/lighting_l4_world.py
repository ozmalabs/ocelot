"""lighting_l4_world — the world adapter for ADVANCED LIGHTING RUNG L4
(SHADOW vs REFLECTANCE EDGES; VISION_LIGHTING_L4_PREREG.md).

Mechanical I/O ONLY (PROTOCOL §0 / CLAUDE.md). This file:

  * renders a grid of REFLECTANCE × ILLUMINANT-GAIN into observed cone triples
    (`round(r × g)` — world physics, the same rendering T3/L1/L2 use) and writes
    one `L4Cell` per grid entry with `crow`/`ccol`/`cid` and the triple;
  * wires the 4-neighbourhood (`l4_neighbour`, both directions) — world layout,
    exactly the same class of mechanical ingest as `border_ownership_world`'s
    `neighbour` edges or `lighting_l2_world`'s `locale_adj`;
  * blind-writes the OFF-by-default flag, ticks, and reads attrs back;
  * exports the graph's OWN `l4_val` decision as a value grid, so the UNMODIFIED
    `vision_border_ownership` seed can be shown it.

**IT MAKES NO PERCEPT DECISION.** Whether an adjacency is an edge, whether that
edge is illuminant or reflectance, and which cells merge into one component are
ALL `vision_lighting_l4` seed rules. The ground-truth material/gain layout is
carried for the RUNNER's scoring only and is NEVER read by any seed rule.

**WHY THE BORDER-OWNERSHIP FIELDS ARE BUILT IN SEPARATE GRAPHS.**
`vision_border_ownership`'s aggregates (`_size`, `_ROOTS`, `_SETTLED`) are global
`NodesOfType("Cell")` grabs, so two `Field`s in one graph would contaminate each
other's component counts. The RAW and L4 conditions therefore run in two fresh
graphs. Copying a value the graph decided (`l4_val`) into a second graph is
mechanical adapter I/O — a pure read-and-write, no conditional, no decision.
There is NO `if`/`else` anywhere in this file (AST-gated by the test suite's
`test_no_python_decision_in_the_adapter`).
"""
from __future__ import annotations

CH = ("L", "M", "S")


def neutral(g: float) -> tuple:
    """A spectrally NEUTRAL illuminant, as the 3-vector it actually is.

    An illuminant is always a per-channel gain; a "neutral" one is the special
    case where the three are equal. Making that explicit is what lets `render`
    stay branchless — and it is also the honest statement of the rung's bound,
    since a CHROMATIC illuminant (three DIFFERENT gains) is exactly the case the
    ratio cue cannot handle.
    """
    return (float(g), float(g), float(g))


def render(reflectance, gain) -> tuple:
    """`round(r × g)` per channel — the WORLD's physics, not a percept.

    `gain` is ALWAYS a 3-vector; use `neutral(g)` for a spectrally flat
    illuminant. The same rendering `lighting_world.add_frame` uses, so L4's
    observations are comparable to T3/L1/L2/L3's by construction.
    """
    return tuple(int(round(reflectance[k] * gain[k])) for k in range(3))


def add_field(s, cones: list[list[tuple]]) -> dict:
    """Create an L4Field + one L4Cell per grid entry, with the 4-neighbourhood.

    `cones[r][c]` is the OBSERVED triple (already rendered). Returns a handle
    {field, cell_ids, index, H, W}; `index[(r,c)]` -> node id.
    """
    H = len(cones)
    W = len(cones[0])
    field = s.add_node("L4Field", {"H": float(H), "W": float(W)})
    index: dict = {}
    cell_ids: list = []
    for r in range(H):
        for c in range(W):
            trip = cones[r][c]
            n = s.add_node("L4Cell", {
                "crow": float(r), "ccol": float(c),
                "cid": float(r * W + c),
                **{("c" + CH[k]): float(trip[k]) for k in range(3)},
                # l4_val init = own cid; the flood drives it DOWN to the
                # ratio-preserving component's minimum (bo_label's idiom).
                "l4_val": float(r * W + c),
                # neutral readback inits, so "never ran" is distinguishable from
                # a written verdict (§1.1 clause 4).
                "l4_margin": -1.0, "l4_marginv": -1.0,
                "l4_npairs": -1.0, "l4_npairsv": -1.0,
                "l4_kind_done": 0.0, "l4_kindv_done": 0.0,
            })
            # add_edge_unchecked: EXTERNAL world scaffolding (grid membership +
            # 4-neighbourhood), not an agent claim — bypasses Γ exactly like
            # border_ownership_world / lighting_l2_world.
            s.add_edge_unchecked(field, "has_l4cell", n)
            index[(r, c)] = n
            cell_ids.append(n)
    for r in range(H):
        for c in range(W):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                inside = (0 <= rr < H) and (0 <= cc < W)
                # No branch: multiply the work by a 0/1 membership fact.
                for _ in range(int(inside)):
                    s.add_edge_unchecked(index[(r, c)], "l4_neighbour",
                                         index[(rr, cc)])
    return {"field": field, "cell_ids": cell_ids, "index": index, "H": H, "W": W}


def set_flag(s, *, lighting_l4: float) -> None:
    """Blind-write the L4 flag on every LightingL4Params node. No read, no branch."""
    for p in s.nodes("LightingL4Params"):
        s.set_attr(p, "lighting_l4", float(lighting_l4))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count (the recurrence depth)."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def cell_attr(s, handle: dict, r: int, c: int, key: str, default: float = 0.0) -> float:
    return float(s.node(handle["index"][(r, c)])["attrs"].get(key, default))


def kind(s, handle: dict, r: int, c: int, axis: str = "h") -> str:
    """The graph's verdict for the adjacency whose LEFT (h) / UPPER (v) cell this
    is. Empty string when no rule fired — a distinguishable absence."""
    key = {"h": "l4_kind", "v": "l4_kindv"}[axis]
    return str(s.node(handle["index"][(r, c)])["attrs"].get(key, ""))


def margin(s, handle: dict, r: int, c: int, axis: str = "h") -> float:
    key = {"h": "l4_margin", "v": "l4_marginv"}[axis]
    return cell_attr(s, handle, r, c, key, -1.0)


def npairs(s, handle: dict, r: int, c: int, axis: str = "h") -> int:
    key = {"h": "l4_npairs", "v": "l4_npairsv"}[axis]
    return int(round(cell_attr(s, handle, r, c, key, -1.0)))


def val_grid(s, handle: dict) -> list[list[int]]:
    """The graph's OWN component decision, as a value grid.

    This is what the UNMODIFIED `vision_border_ownership` seed is shown in the
    L4 condition. A pure read of an attribute a RULE wrote — the adapter decides
    nothing about it.
    """
    return [[int(round(cell_attr(s, handle, r, c, "l4_val")))
             for c in range(handle["W"])] for r in range(handle["H"])]


def luminance_grid(s, handle: dict) -> list[list[int]]:
    """The RAW observed L-cone response, as a value grid — the control condition
    border-ownership is shown when L4 is NOT interposed."""
    return [[int(round(cell_attr(s, handle, r, c, "cL")))
             for c in range(handle["W"])] for r in range(handle["H"])]


def n_components(s, handle: dict) -> int:
    """How many distinct l4_val components the flood settled on (process rule 7's
    literal count, at the component grain)."""
    return len({cell_attr(s, handle, r, c, "l4_val")
                for r in range(handle["H"]) for c in range(handle["W"])})


def written_l4_attrs(s, handle: dict) -> list[str]:
    """Every `l4_*` attribute that departs from its neutral init, anywhere in the
    field. The §9 OFF-day readback: with the flag at 0 this must be empty."""
    neutral = {"l4_margin": -1.0, "l4_marginv": -1.0,
               "l4_npairs": -1.0, "l4_npairsv": -1.0,
               "l4_kind_done": 0.0, "l4_kindv_done": 0.0}
    out = set()
    for nid in handle["cell_ids"]:
        attrs = s.node(nid)["attrs"]
        cid = float(attrs.get("cid", -1.0))
        for k, v in attrs.items():
            moved = {
                "l4_val": float(v) != cid,
                "l4_kind": str(v) != "",
                "l4_kindv": str(v) != "",
            }.get(k, (k in neutral) and float(v) != neutral.get(k, 0.0))
            for _ in range(int(bool(moved)) * int(k.startswith("l4_"))):
                out.add(k)
    return sorted(out)
