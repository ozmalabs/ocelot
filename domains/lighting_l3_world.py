"""lighting_l3_world — the world adapter for ADVANCED LIGHTING RUNG L3
(GLOBAL ILLUMINANT INFERENCE; VISION_LIGHTING_L3_PREREG.md).

Mechanical I/O ONLY (PROTOCOL §0 / CLAUDE.md). This file:

  * builds frames by DELEGATING to `lighting_l2_world.add_frame` (L2's adapter,
    imported READ-ONLY and NOT edited — §11 rule 4), which itself delegates the
    rendering to `lighting_world.add_frame`. So `round(reflectance × gain)`, the
    `pos` layout, the `Locale` hubs, `in_locale`/`sits_in` and `locale_adj` all
    have ONE source of truth across T3, L1, L2 and L3, and every arm is
    comparable by construction;
  * adds NEUTRAL INITS for the `l3_*` / `l3l_*` readback attributes on the
    surfaces, the locales and the frame, so an absent attribute can never be
    mistaken for a computed 0 (§1.1 — an absence must never read as a value);
  * blind-writes the OFF-by-default flag, ticks, and reads attrs back.

**IT ADDS NO EDGE AND NO STRUCTURE OF ITS OWN.** The per-locale illuminant
estimate, the SCENE-LEVEL POOL, the anchor CORROBORATION, the verdict, the two
refusals and the V4 lesion are ALL `vision_lighting_l3` seed rules. The pooling
quantifies over the `has_locale` edges L2's adapter already drew.

It makes NO percept decision. The ground-truth `material` is carried for the
RUNNER's scoring only and is NEVER read by any seed rule.
"""
from __future__ import annotations

from domains import lighting_l2_world as l2w

CH = ("L", "M", "S")

# The neutral inits. `-1.0` marks "no value was written" for the id/residual
# readouts (they can never legitimately be negative), `0.0` for the flags and
# counts. This is the same convention L2's adapter uses.
_SURF_INIT = (("l3_recognized", 0.0), ("l3_id", -1.0), ("l3_resid", -1.0),
              ("l3_ncand", 0.0), ("l3l_recognized", 0.0), ("l3l_id", -1.0),
              ("l3l_resid", -1.0))
_LOC_INIT = (("l3_ghat_done", 0.0), ("l3_corr", 0.0),
             ("l3_gL", 0.0), ("l3_gM", 0.0), ("l3_gS", 0.0))
_FRAME_INIT = (("l3_pooled", 0.0), ("l3_n_loc", 0.0),
               ("l3_GL", 0.0), ("l3_GM", 0.0), ("l3_GS", 0.0))


def add_frame(s, *, reflectances, gain, is_reference: bool = False,
              start_sidx: int = 0, radius: int = l2w.RADIUS) -> dict:
    """Build a LightFrame via L2's adapter, then add L3's neutral inits."""
    handle = l2w.add_frame(s, reflectances=reflectances, gain=gain,
                           is_reference=is_reference, start_sidx=start_sidx,
                           radius=radius)
    for nid in handle["surface_ids"]:
        for k, v in _SURF_INIT:
            s.set_attr(nid, k, v)
    for loc in handle["locale_ids"]:
        for k, v in _LOC_INIT:
            s.set_attr(loc, k, v)
    for k, v in _FRAME_INIT:
        s.set_attr(handle["frame"], k, v)
    return handle


def link_reference(s, test_handle: dict, ref_handle: dict) -> None:
    """Point a test frame at its reference frame (frame-level, exactly as T3/L1/L2)."""
    l2w.link_reference(s, test_handle, ref_handle)


def set_flag(s, *, lighting_l3: float) -> None:
    """Blind-write the L3 flag on every LightingL3Params node. No read, no branch."""
    for p in s.nodes("LightingL3Params"):
        s.set_attr(p, "lighting_l3", float(lighting_l3))


def tick(s, max_steps: int = 200_000) -> int:
    return l2w.tick(s, max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def recognition(s, nid: int) -> dict:
    """The recognition readback for one ObjSurface (mechanical).

    Carries SIX arms read off the SAME node in the SAME graph — T3's exact
    `lit_*`, L1's global-continuous `l1_*`, L2's local `l2_*` (which IS L3's
    pooling ABLATION, being l3_recognize minus the corroboration conjunct),
    L2's global-anchor ablation `l2g_*`, L3's corroborated `l3_*`, and L3's
    V4-LESIONED `l3l_*`. That is what makes every contrast in this rung ONE
    measurement rather than several experiments.
    """
    r = dict(l2w.recognition(s, nid))
    a = s.node(nid)["attrs"]
    g = lambda k, d=0.0: float(a.get(k, d))  # noqa: E731 — mechanical accessor
    r.update({
        "l3_recognized": int(round(g("l3_recognized"))),
        "l3_id": int(round(g("l3_id", -1.0))),
        "l3_resid": g("l3_resid", -1.0),
        "l3_ncand": int(round(g("l3_ncand"))),
        "l3_status": a.get("l3_status", ""),
        "l3l_recognized": int(round(g("l3l_recognized"))),
        "l3l_id": int(round(g("l3l_id", -1.0))),
        "l3l_resid": g("l3l_resid", -1.0),
    })
    return r


def scene_estimate(s, handle: dict) -> dict:
    """The frame's POOLED scene-level illuminant estimate (mechanical read)."""
    a = s.node(handle["frame"])["attrs"]
    return {"pooled": float(a.get("l3_pooled", 0.0)),
            "n_loc": float(a.get("l3_n_loc", 0.0)),
            **{("G" + ch): float(a.get("l3_G" + ch, 0.0)) for ch in CH}}


def locale_estimate(s, handle: dict, i: int) -> dict:
    a = s.node(handle["locale_ids"][i])["attrs"]
    return {"ghat_done": float(a.get("l3_ghat_done", 0.0)),
            "corr": float(a.get("l3_corr", 0.0)),
            **{("g" + ch): float(a.get("l3_g" + ch, 0.0)) for ch in CH}}


def n_corroborated_locales(s, handle: dict) -> int:
    """How many locales the scene CORROBORATED. The rung's own contribution,
    counted; it is the population L2 admitted on an assumed anchor."""
    return sum(1 for loc in handle["locale_ids"]
               if float(s.node(loc)["attrs"].get("l3_corr", 0.0)) > 0.5)


def n_identities(s) -> int:
    return l2w.n_identities(s)
