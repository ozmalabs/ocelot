"""lighting_l3b_world — the world adapter for ADVANCED LIGHTING RUNG L3b
(THE ANCHOR OF THE ANCHOR; VISION_LIGHTING_L3B_PREREG.md).

Mechanical I/O ONLY (PROTOCOL §0 / CLAUDE.md). This file:

  * builds frames by DELEGATING to `lighting_l3_world.add_frame` (L3's adapter,
    imported READ-ONLY and NOT edited — §11 rule 4), which delegates to L2's,
    which delegates to `lighting_world.add_frame`. So `round(reflectance ×
    gain)`, the `pos` layout, the `Locale` hubs, `in_locale`/`sits_in` and
    `locale_adj` all have ONE source of truth across T3, L1, L2, L3 and L3b, and
    every arm is comparable by construction;
  * adds NEUTRAL INITS for the `l3b_*` readback attributes on the surfaces and
    the locales, so an absent attribute can never be mistaken for a computed 0
    (§1.1 — an absence must never read as a value);
  * blind-writes the OFF-by-default flag, ticks, and reads attrs back.

**IT ADDS NO EDGE AND NO STRUCTURE OF ITS OWN.** The leave-one-out pool, the
two recorded deviations, the corroboration, the verdict and the two refusals are
ALL `vision_lighting_l3b` seed rules. The leave-one-out exclusion quantifies
over the `has_locale` edges L2's adapter already drew.

It makes NO percept decision. The ground-truth `material` is carried for the
RUNNER's scoring only and is NEVER read by any seed rule.
"""
from __future__ import annotations

from domains import lighting_l3_world as l3w

CH = ("L", "M", "S")

# The neutral inits. `-1.0` marks "no value was written" for the id/residual/
# deviation readouts (they can never legitimately be negative), `0.0` for the
# flags and counts. Same convention L2's and L3's adapters use.
_SURF_INIT = (("l3b_recognized", 0.0), ("l3b_id", -1.0), ("l3b_resid", -1.0),
              ("l3b_ncand", 0.0))
_LOC_INIT = (("l3b_pooled", 0.0), ("l3b_corr", 0.0), ("l3b_dev_done", 0.0),
             ("l3b_dev_cheb", -1.0), ("l3b_dev_loo", -1.0),
             ("l3b_GL", 0.0), ("l3b_GM", 0.0), ("l3b_GS", 0.0))


def add_frame(s, *, reflectances, gain, is_reference: bool = False,
              start_sidx: int = 0, radius: int = None) -> dict:
    """Build a LightFrame via L3's adapter, then add L3b's neutral inits."""
    kw = {} if radius is None else {"radius": radius}
    handle = l3w.add_frame(s, reflectances=reflectances, gain=gain,
                           is_reference=is_reference, start_sidx=start_sidx, **kw)
    for nid in handle["surface_ids"]:
        for k, v in _SURF_INIT:
            s.set_attr(nid, k, v)
    for loc in handle["locale_ids"]:
        for k, v in _LOC_INIT:
            s.set_attr(loc, k, v)
    return handle


def link_reference(s, test_handle: dict, ref_handle: dict) -> None:
    """Point a test frame at its reference frame (frame-level, exactly as T3/L1/L2/L3)."""
    l3w.link_reference(s, test_handle, ref_handle)


def set_flag(s, *, lighting_l3b: float) -> None:
    """Blind-write the L3b flag on every LightingL3bParams node. No read, no branch."""
    for p in s.nodes("LightingL3bParams"):
        s.set_attr(p, "lighting_l3b", float(lighting_l3b))


def tick(s, max_steps: int = 200_000) -> int:
    return l3w.tick(s, max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def recognition(s, nid: int) -> dict:
    """The recognition readback for one ObjSurface (mechanical).

    Carries SEVEN arms read off the SAME node in the SAME graph — T3's `lit_*`,
    L1's `l1_*`, L2's `l2_*`, L2's global-anchor `l2g_*`, L3's `l3_*` (which IS
    L3b's LEAVE-ONE-OUT ABLATION, being `l3b_recognize` with the corroboration
    conjunct swapped back), L3's V4-LESIONED `l3l_*`, and L3b's mutually
    corroborated `l3b_*`. That is what makes every contrast in this rung ONE
    measurement rather than several experiments.
    """
    r = dict(l3w.recognition(s, nid))
    a = s.node(nid)["attrs"]
    g = lambda k, d=0.0: float(a.get(k, d))  # noqa: E731 — mechanical accessor
    r.update({
        "l3b_recognized": int(round(g("l3b_recognized"))),
        "l3b_id": int(round(g("l3b_id", -1.0))),
        "l3b_resid": g("l3b_resid", -1.0),
        "l3b_ncand": int(round(g("l3b_ncand"))),
        "l3b_status": a.get("l3b_status", ""),
    })
    return r


def locale_readout(s, handle: dict, i: int) -> dict:
    """The per-locale L3/L3b readback (mechanical). `dev_cheb` is the locale's
    deviation from L3's SELF-INCLUDING pool — 0 at the centre BY CONSTRUCTION —
    and `dev_loo` its deviation from the LEAVE-ONE-OUT pool."""
    a = s.node(handle["locale_ids"][i])["attrs"]
    base = l3w.locale_estimate(s, handle, i)
    return {**base,
            "pooled_loo": float(a.get("l3b_pooled", 0.0)),
            "corr_loo": float(a.get("l3b_corr", 0.0)),
            "dev_cheb": float(a.get("l3b_dev_cheb", -1.0)),
            "dev_loo": float(a.get("l3b_dev_loo", -1.0)),
            **{("Gloo" + ch): float(a.get("l3b_G" + ch, 0.0)) for ch in CH}}


def n_corroborated_locales(s, handle: dict) -> int:
    """How many locales the OTHER locales corroborated — the rung's own
    contribution, counted."""
    return sum(1 for loc in handle["locale_ids"]
               if float(s.node(loc)["attrs"].get("l3b_corr", 0.0)) > 0.5)


def n_identities(s) -> int:
    return l3w.n_identities(s)
