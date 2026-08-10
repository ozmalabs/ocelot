"""lighting_l2_world — the world adapter for ADVANCED LIGHTING RUNG L2
(SPATIALLY-VARYING ILLUMINANT / RETINEX; VISION_LIGHTING_L2_PREREG.md).

Mechanical I/O ONLY (PROTOCOL §0 / CLAUDE.md). This file:

  * builds frames by DELEGATING to `lighting_world.add_frame` (T3/L1's adapter,
    imported READ-ONLY and NOT edited — §11 rule 4), so the rendering
    `round(reflectance × gain)` has ONE source of truth across T3, L1 and L2 and
    the three arms are comparable by construction;
  * writes each surface's `pos` — its position in the scene's spatial layout.
    This is WORLD LAYOUT, exactly the same class of mechanical ingest as the
    cone triple: the adapter knows where things are because it built the world;
  * builds one `Locale` hub per position and links the surfaces of that
    position's NEIGHBOURHOOD into it (`in_locale`), plus each surface to its own
    centre locale (`sits_in`). **The locale CONTAINS ITS OWN CENTRE**, which is
    what preserves L1's `r/a ≤ 1` — the property its ONE-LATTICE-STEP bound is
    derived from — verbatim at locale grain;
  * blind-writes the OFF-by-default flag, ticks, and reads attrs back.

**IT DRAWS NO CROSS-FRAME LOCALE EDGE.** Pairing a test locale with its
reference counterpart is the GRAPH's decision, made by the `l2_pair` rule as an
`Eq(pos,pos)` join across `compares_to`. The adapter supplies positions; the
rule supplies the pairing.

It makes NO percept decision. The local anchor, the per-locale admission, the
rendered continuous verdict, the refusal, the candidate count and the ablation
control are ALL `vision_lighting_l2` seed rules. The ground-truth `material` is
carried for the RUNNER's scoring only and is NEVER read by any seed rule.
"""
from __future__ import annotations

from domains import lighting_world as lw

CH = ("L", "M", "S")

# The locale RADIUS. Not a tuned width: 1 is the SMALLEST neighbourhood that has
# a neighbour at all — the double-opponent local-contrast grain. It is exposed as
# an argument only so the reported-only radius probe (prereg §3) can be run as
# graph SHAPE rather than as a Python branch; the headline is pre-registered at 1.
RADIUS = 1


def add_frame(s, *, reflectances, gain, is_reference: bool = False,
              start_sidx: int = 0, radius: int = RADIUS) -> dict:
    """Build a LightFrame with its surfaces, positions and Locale hubs.

    `reflectances` and `gain` are passed straight through to
    `lighting_world.add_frame` (single source of truth for the rendering).
    Positions are the index in `reflectances` — a 1-D chain, which is the
    world's layout, not a percept.
    """
    handle = lw.add_frame(s, reflectances=reflectances, gain=gain,
                          is_reference=is_reference, start_sidx=start_sidx)
    n = len(handle["surface_ids"])
    for i, nid in enumerate(handle["surface_ids"]):
        s.set_attr(nid, "pos", float(i))
        # L2 readback attrs, neutral init (L2-only namespace — L2 never writes a
        # T3 or L1 attribute, so all three arms are readable from ONE graph):
        for k, v in (("l2_recognized", 0.0), ("l2_id", -1.0), ("l2_resid", -1.0),
                     ("l2_ncand", 0.0), ("l2g_recognized", 0.0),
                     ("l2g_id", -1.0), ("l2g_resid", -1.0)):
            s.set_attr(nid, k, v)
    handle["locale_ids"] = []
    for i in range(n):
        loc = s.add_node("Locale", {
            "pos": float(i), "l2_loc_done": 0.0, "l2_paired": 0.0,
            "l2_slowvar": 0.0, "l2_n": 0.0,
            **{("l2_a" + ch): 0.0 for ch in CH},
            **{("l2_m" + ch): 0.0 for ch in CH},
            **{("l2_ra" + ch): 0.0 for ch in CH},
            **{("l2_rm" + ch): 0.0 for ch in CH},
        })
        # add_edge_unchecked: EXTERNAL world scaffolding (spatial layout), not an
        # agent claim — bypasses Γ exactly like `has_surface` in lighting_world.
        s.add_edge_unchecked(handle["frame"], "has_locale", loc)
        for j in range(max(0, i - radius), min(n, i + radius + 1)):
            s.add_edge_unchecked(loc, "in_locale", handle["surface_ids"][j])
        s.add_edge_unchecked(handle["surface_ids"][i], "sits_in", loc)
        handle["locale_ids"].append(loc)
    # Locale ADJACENCY — spatial layout again, the same class of mechanical
    # ingest. `l2_slowvar` quantifies over these to ask whether the field is
    # slowly varying HERE; it is symmetric because "adjacent" is.
    for i in range(n - 1):
        s.add_edge_unchecked(handle["locale_ids"][i], "locale_adj",
                             handle["locale_ids"][i + 1])
        s.add_edge_unchecked(handle["locale_ids"][i + 1], "locale_adj",
                             handle["locale_ids"][i])
    return handle


def link_reference(s, test_handle: dict, ref_handle: dict) -> None:
    """Point a test frame at its reference frame (frame-level, exactly as T3/L1).
    NO locale-level edge is drawn here — `l2_pair` derives those."""
    lw.link_reference(s, test_handle, ref_handle)


def set_flag(s, *, lighting_l2: float) -> None:
    """Blind-write the L2 flag on every LightingL2Params node. No read, no branch."""
    for p in s.nodes("LightingL2Params"):
        s.set_attr(p, "lighting_l2", float(lighting_l2))


def tick(s, max_steps: int = 200_000) -> int:
    return lw.tick(s, max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def recognition(s, nid: int) -> dict:
    """The recognition readback for one ObjSurface (mechanical).

    Carries ALL FOUR arms read off the SAME node in the SAME graph — T3's exact
    `lit_*`, L1's global-continuous `l1_*`, L2's local `l2_*` and L2's
    global-anchor ABLATION `l2g_*`. That is what makes the local-vs-global
    contrast one measurement rather than several experiments.
    """
    a = s.node(nid)["attrs"]
    g = lambda k, d=0.0: float(a.get(k, d))  # noqa: E731 — mechanical accessor
    return {
        "pos": int(round(g("pos", -1.0))),
        "sidx": int(round(g("sidx", -1.0))),
        "cL": int(round(g("cL"))), "cM": int(round(g("cM"))),
        "cS": int(round(g("cS"))),
        "lit_recognized": int(round(g("lit_recognized"))),
        "lit_id": int(round(g("lit_id", -1.0))),
        "l1_recognized": int(round(g("l1_recognized"))),
        "l1_id": int(round(g("l1_id", -1.0))),
        "l2_recognized": int(round(g("l2_recognized"))),
        "l2_id": int(round(g("l2_id", -1.0))),
        "l2_resid": g("l2_resid", -1.0),
        "l2_ncand": int(round(g("l2_ncand"))),
        "l2_status": a.get("l2_status", ""),
        "l2g_recognized": int(round(g("l2g_recognized"))),
        "l2g_id": int(round(g("l2g_id", -1.0))),
        "l2g_resid": g("l2g_resid", -1.0),
    }


def locale_attr(s, handle: dict, i: int, key: str) -> float:
    return float(s.node(handle["locale_ids"][i])["attrs"].get(key, 0.0))


def n_slowvar_locales(s, handle: dict) -> int:
    """How many locales the graph DISCOVERED the field to be slowly varying at.
    Reported alongside recognition; it gates nothing (prereg AMENDMENT 1)."""
    return sum(1 for loc in handle["locale_ids"]
               if float(s.node(loc)["attrs"].get("l2_slowvar", 0.0)) > 0.5)


def n_paired_locales(s, handle: dict) -> int:
    return sum(1 for loc in handle["locale_ids"]
               if float(s.node(loc)["attrs"].get("l2_paired", 0.0)) > 0.5)


def frame_attr(s, handle: dict, key: str) -> float:
    return lw.frame_attr(s, handle, key)


def n_identities(s) -> int:
    return lw.n_identities(s)
