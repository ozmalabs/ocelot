"""lighting_world — a world adapter for LIGHTING / APPEARANCE INVARIANCE
(VISION_LIGHTING_PREREG.md).

Mechanical I/O ONLY (PROTOCOL §0 / CLAUDE.md): builds LightFrame nodes each holding
a population of ObjSurface nodes (integer cone triples cL,cM,cS = reflectance ×
illuminant, rendered EXACTLY — the in-frame integer lattice), links a test frame to
its reference frame, blind-writes the OFF-by-default flag, ticks to a fixpoint, and
reads the discovered Illuminant / minted SurfaceIdentity / per-surface recognition
attrs back.

It makes NO percept decision. The anchor, the in-class discovery, the MDL-gated
mint, the anchor-relative invariant and the raw baseline are ALL in the
vision_lighting seed rules (li_frame_stats / li_inclass / li_mint / li_recognize /
li_raw_recognize); this file only translates a reflectance×illuminant field into
graph nodes and reads attrs out.

Supplying (cL,cM,cS) per surface is mechanical ingest — exactly like
colour_identity_world supplies (cL,cM,cS) and category_world supplies (d0,d1,v0,v1).
The RENDERING (reflectance × gain) is done here because it is world physics, not a
percept: the agent never sees the reflectance or the gain, only the product. A
ground-truth `material` may be attached for the RUNNER's scoring, but it is NEVER
read by any seed rule (minting is unsupervised).
"""
from __future__ import annotations

CH = ("L", "M", "S")


def add_frame(s, *, reflectances: list[dict], gain, is_reference: bool = False,
              start_sidx: int = 0) -> dict:
    """Create a LightFrame + one ObjSurface per reflectance, rendered under `gain`.

    `reflectances` entries are dicts with integer rL,rM,rS and an optional
    `material` (runner bookkeeping only). `gain` is either a 3-tuple applied to
    EVERY surface (a diagonal / von Kries illuminant — the in-class case) or a LIST
    of per-surface 3-tuples (a spatially-varying illuminant — the OUT-OF-CLASS
    case). Rendering is exact integer multiplication, so the observation stays on the
    in-frame integer lattice.

    Returns a handle {frame, surface_ids, next_sidx, meta}.
    """
    frame = s.add_node("LightFrame", {
        "is_reference": 1.0 if is_reference else 0.0,
        "stats_done": 0.0, "illum_inclass": 0.0,
        "aL": 0.0, "aM": 0.0, "aS": 0.0, "sL": 0.0, "sM": 0.0, "sS": 0.0,
    })
    handle = {"frame": frame, "surface_ids": [], "next_sidx": start_sidx, "meta": []}
    for i, refl in enumerate(reflectances):
        g = gain[i] if isinstance(gain, list) else gain
        add_surface(s, handle, refl, g)
    return handle


def add_surface(s, handle: dict, refl: dict, gain) -> int:
    """Add ONE ObjSurface to a frame, rendered under `gain`. Mechanical.

    `gain` entries may be INTEGER (T3's exact-rendering class — the product is
    already on the lattice) or REAL (rung L1). A real gain is rendered through
    `round()`, which is what GROUNDING IS: the observation is stepped by
    construction, so the in-frame coordinate stays an integer while the gain
    itself — a CROSS-FRAME quantity — is allowed to be real. `round()` of an
    integer product is that product, so integer gains render BYTE-IDENTICALLY to
    the pre-L1 code path and T3's committed numbers are unmoved.

    This is WORLD PHYSICS, not a percept: the agent never sees the reflectance or
    the gain, only their rendered product.
    """
    sidx = handle["next_sidx"]
    handle["next_sidx"] = sidx + 1
    cones = {("c" + ch): float(round(float(refl["r" + ch]) * float(gain[k])))
             for k, ch in enumerate(CH)}
    n = s.add_node("ObjSurface", {
        **cones,
        "sidx": float(sidx),
        # readback / recognition attrs, neutral init:
        "lit_recognized": 0.0, "lit_id": -1.0,
        "raw_recognized": 0.0, "raw_id": -1.0,
        # rung-L1 readback attrs, neutral init (L1-only namespace — L1 never
        # writes a T3 attr, so both arms are readable from ONE graph):
        "l1_recognized": 0.0, "l1_id": -1.0, "l1_resid": -1.0,
    })
    # add_edge_unchecked: EXTERNAL world scaffolding (frame membership), not an agent
    # claim — bypasses Γ exactly like category_world / colour_identity_world.
    s.add_edge_unchecked(handle["frame"], "has_surface", n)
    handle["surface_ids"].append(n)
    handle["meta"].append({**refl, "gain": tuple(float(x) for x in gain),
                           "sidx": sidx})
    return n


def link_reference(s, test_handle: dict, ref_handle: dict) -> None:
    """Point a test frame at its reference frame (the cross-frame comparison the
    in-class discovery reads). Mechanical scaffolding."""
    s.add_edge_unchecked(test_handle["frame"], "compares_to", ref_handle["frame"])


def set_flag(s, *, lighting: float) -> None:
    """Blind-write the flag on every LightingParams node. No read, no branch."""
    for p in s.nodes("LightingParams"):
        s.set_attr(p, "lighting", float(lighting))


def set_flag_l1(s, *, lighting_l1: float) -> None:
    """Blind-write the rung-L1 flag on every LightingL1Params node. No read, no
    branch. Separate from `set_flag` so T3's flag and L1's are independently
    settable and the two arms can be measured from ONE graph."""
    for p in s.nodes("LightingL1Params"):
        s.set_attr(p, "lighting_l1", float(lighting_l1))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def n_identities(s) -> int:
    return len(list(s.nodes("SurfaceIdentity")))


def n_illuminants(s) -> int:
    return len(list(s.nodes("Illuminant")))


def identities(s) -> list[dict]:
    out = []
    for i in s.nodes("SurfaceIdentity"):
        a = s.node(i)["attrs"]
        out.append({k: int(round(float(a.get(k, 0.0))))
                    for k in ("pL", "pM", "pS", "paL", "paM", "paS",
                              "members", "sid_key")})
    out.sort(key=lambda d: d["sid_key"])
    return out


def illuminants(s) -> list[dict]:
    out = []
    for i in s.nodes("Illuminant"):
        a = s.node(i)["attrs"]
        out.append({k: int(round(float(a.get(k, 0.0))))
                    for k in ("gL_num", "gL_den", "gM_num", "gM_den",
                              "gS_num", "gS_den")})
    return out


def frame_attr(s, handle: dict, key: str) -> float:
    return float(s.node(handle["frame"])["attrs"].get(key, 0.0))


def surf_attr(s, nid: int, key: str) -> float:
    return float(s.node(nid)["attrs"].get(key, 0.0))


def recognition(s, nid: int) -> dict:
    """The recognition readback for one ObjSurface (mechanical).

    Carries BOTH arms — T3's exact `lit_*` and rung L1's continuous `l1_*` — read
    off the SAME node in the SAME graph, which is what makes the
    CONTINUOUS-DECIDES contrast a measurement rather than two experiments.
    `l1_status` distinguishes an explicit REFUSAL from a rule that never ran
    (§1.1's dead-arm lesson).
    """
    a = s.node(nid)["attrs"]
    return {
        "cL": int(round(float(a.get("cL", 0.0)))),
        "cM": int(round(float(a.get("cM", 0.0)))),
        "cS": int(round(float(a.get("cS", 0.0)))),
        "sidx": int(round(float(a.get("sidx", -1.0)))),
        "lit_recognized": int(round(float(a.get("lit_recognized", 0.0)))),
        "lit_id": int(round(float(a.get("lit_id", -1.0)))),
        "raw_recognized": int(round(float(a.get("raw_recognized", 0.0)))),
        "raw_id": int(round(float(a.get("raw_id", -1.0)))),
        "l1_recognized": int(round(float(a.get("l1_recognized", 0.0)))),
        "l1_id": int(round(float(a.get("l1_id", -1.0)))),
        "l1_resid": float(a.get("l1_resid", -1.0)),
        "l1_status": a.get("l1_status", ""),
    }


def illuminants_l1(s) -> list[dict]:
    """The REAL per-channel gains L1 discovered (mechanical readback).

    Real-valued because the gain is a CROSS-FRAME map, never an in-frame
    coordinate — the contrast with T3's exact `(numer,denom)` integer pair.
    """
    out = []
    for i in s.nodes("IlluminantL1"):
        a = s.node(i)["attrs"]
        out.append({k: float(a.get(k, 0.0)) for k in ("gL", "gM", "gS")})
    return out


def n_illuminants_l1(s) -> int:
    return len(list(s.nodes("IlluminantL1")))
