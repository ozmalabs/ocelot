#!/usr/bin/env python3
"""Emit seeds/vision_lighting.json — LIGHTING / APPEARANCE INVARIANCE (FRONTIER T3)
as pure graph data (NO new Rust).

See VISION_LIGHTING_PREREG.md. The illuminant is a low-D CROSS-FRAME map (a diagonal
/ von Kries multiplicative map on the cone coordinates); lighting-invariant
recognition is therefore DISCOVER-THE-ILLUMINANT-AND-TAKE-WHAT-IT-LEAVES-FIXED --
the same shape as the geometric-nuisance crossings (similarity / generator
discovery), moved from geometry to appearance.

An ObjSurface carries integer cones (cL,cM,cS) = (rL*gL, rM*gM, rS*gS): the
reflectance r is the stable IN-FRAME property (integer lattice) and the illuminant g
is the CROSS-FRAME map. Rendering is EXACT integer, so the frame/continuum invariant
holds with NO tolerance and NO magic number anywhere.

  li_frame_stats  the frame's OWN per-channel MaxOver anchor (aL,aM,aS) and Sum
                  (sL,sM,sS) over Neighbours(frame,"has_surface"). Frame-scoped --
                  no global population grab. The anchor is the frame's measured
                  dynamic-range ceiling, NOT a constant (sec 13's "a fraction of a
                  dynamic range the system measures for itself").
  li_inclass      DISCOVERS whether the lighting change is IN-CLASS, without needing
                  surface correspondence: under a diagonal map EVERY order statistic
                  scales by the same per-channel gain, so a_ch*ref.s_ch ==
                  s_ch*ref.a_ch must hold for all three channels (exact integer
                  cross-multiplication -- the ratio is cross-frame, so it is never
                  divided, only cross-multiplied). Holds => mint an Illuminant
                  carrying the discovered gain as an exact (numer,denom) PAIR and set
                  illum_inclass=1. Fails => nothing minted; a spatially-varying
                  (multi-illuminant) change is REFUSED, not force-normalised.
  li_mint         MDL-gated mint of a SurfaceIdentity in the REFERENCE frame:
                  Count(same exact cone triple) >= m_min, with m_min=2 FALLING OUT of
                  d=3 (a prototype costs d integers and saves d-1 per member => pays
                  iff m > d/(d-1) = 1.5 => m >= 2; sec 13). Canonical-representative
                  + Not(Exists) guards make it batch-safe. Stores the prototype
                  (pL,pM,pS) AND its own frame's anchor (paL,paM,paS). UNSUPERVISED.
  li_recognize    THE INVARIANT. A surface in a TEST frame matches a SurfaceIdentity
                  iff illum_inclass=1 AND, per channel, c_ch*pa_ch == p_ch*a_ch --
                  the reflectance RELATIVE TO THE FRAME'S OWN ANCHOR. The illuminant
                  cancels identically; what it leaves fixed is the invariant.
  li_raw_recognize  THE RAW BASELINE (the untangling-style control, colour/category's
                  exact-match memorization pattern): matches iff the raw cones are
                  EQUAL. Under any gain this CONFUSES -- the measured contrast that
                  makes the discounting load-bearing.

Flag-gated on LightingParams.lighting, OFF by default (sec 9). NO new Rust: reuses
Count/Filter/NodesOfType/Neighbours/MaxOver/Sum/Exists/Not/Eq/Gt/Lt/Times/And.

BOUNDED: the DIAGONAL illuminant class ONLY. Multi-illuminant scenes, shadows,
penumbrae, interreflections and spatially-varying light are NOT solved -- the
mechanism can only REFUSE them (li_inclass). That is the NAMED FRONTIER.

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_lighting.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms) -----------------------------------
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}
def Times(a, b):
    """Times takes an `items` LIST (`jsonio.rs:1274`), NOT a/b.

    Written as a/b first, this parsed to an EMPTY PRODUCT on both sides — and an
    empty product is 1, so `Eq(Times(...), Times(...))` was `Eq(1,1)` = TRUE for
    EVERY surface against EVERY identity: a silent UNIVERSAL CONTAINER that passed
    invariance perfectly (VISION_PROTOCOL §1.1). It was caught by the discrimination
    probe, not by the invariance arm — which is exactly why §1.1 demands the floor.
    """
    return {"type": "Times", "items": [a, b]}
def Not(x):             return {"type": "Not", "arg": x}
def And(items):         return {"type": "And", "items": items}
def NodesOf(t):         return {"type": "NodesOfType", "node_type": t}
def Nbrs(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}
def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src):         return {"type": "Count", "source": src}
def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def MaxOver(src, var, value):
    return {"type": "MaxOver", "source": src, "var_name": var, "value": value}
def Sum(src, var, value):
    return {"type": "Sum", "source": src, "var_name": var, "value": value}
def PickLP():
    return {"type": "PickUnique", "source": NodesOf("LightingParams")}
def term(x):            return {"__term__": x}


CH = ["L", "M", "S"]        # the three cone channels
D_CONE = 3                  # coordinate dimensionality -> m_min = 2 (sec 13)
M_MIN = 2


def ENABLED():
    return Gt(A(PickLP(), "lighting"), Lit(0.5))


def surfaces_of(frame):
    """The frame's OWN surfaces — hub-scoped, never a global NodesOfType grab."""
    return Nbrs(frame, "has_surface")


# ---------------------------------------------------------------------------
# li_frame_stats -- the frame's own per-channel anchor (max) and sum.
# ---------------------------------------------------------------------------
LI_FRAME_STATS = {
    "name": "li_frame_stats",
    "comment": (
        "The frame's OWN per-channel order statistics: the ANCHOR a_ch = "
        "MaxOver(frame's surfaces, c_ch) and the SUM s_ch = Sum(...). Scoped by "
        "Neighbours(frame,'has_surface') -- the frame's own population, NOT a global "
        "NodesOfType grab (VISION_PROTOCOL sec 12.1). The anchor is the frame's "
        "MEASURED dynamic-range ceiling, which under a diagonal illuminant scales "
        "exactly with the illuminant -- so dividing by it makes the appearance code "
        "RELATIVE, which is sec 13's whole corollary (ratios transfer, absolutes do "
        "not). NO constant is introduced. The stats_done guard makes the rule fire "
        "once per frame so run_rules converges. Flag-gated, OFF by default (sec 9)."
    ),
    # Matched through a surface edge so the rule only ever sees a frame that HAS a
    # population (a frame with no surfaces has no anchor to speak of -- an empty
    # MaxOver would read as a lookup, sec 1.1). Every binding of a given frame writes
    # the SAME values, and stats_done makes it idempotent, so run_rules converges.
    "match": [["frame", "has_surface", "anysurf"]],
    "where": And([
        ENABLED(),
        Lt(A(V("frame"), "stats_done"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "frame", "aL",
         term(MaxOver(surfaces_of(V("frame")), "w", A(V("w"), "cL")))],
        ["set_attr", "frame", "aM",
         term(MaxOver(surfaces_of(V("frame")), "w", A(V("w"), "cM")))],
        ["set_attr", "frame", "aS",
         term(MaxOver(surfaces_of(V("frame")), "w", A(V("w"), "cS")))],
        ["set_attr", "frame", "sL",
         term(Sum(surfaces_of(V("frame")), "w", A(V("w"), "cL")))],
        ["set_attr", "frame", "sM",
         term(Sum(surfaces_of(V("frame")), "w", A(V("w"), "cM")))],
        ["set_attr", "frame", "sS",
         term(Sum(surfaces_of(V("frame")), "w", A(V("w"), "cS")))],
        ["set_attr", "frame", "stats_done", term(Lit(1.0))],
    ],
}


def _stat_consistent(test, ref, ch):
    """a_ch/s_ch == ref.a_ch/ref.s_ch, as EXACT integer cross-multiplication.

    Under a diagonal (von Kries) illuminant EVERY order statistic of the frame
    scales by the SAME per-channel gain g_ch, so the anchor:sum ratio is INVARIANT.
    Under a spatially-varying illuminant the max and the sum pick up different
    effective gains and the ratio generically diverges. This is the in-class test,
    and it needs NO surface correspondence -- only that the two frames show the same
    scene. Cross-multiplied so the ratio (a cross-frame quantity) is never divided:
    exact integers, no float, no tolerance.
    """
    return Eq(Times(A(test, "a" + ch), A(ref, "s" + ch)),
              Times(A(test, "s" + ch), A(ref, "a" + ch)))


# ---------------------------------------------------------------------------
# li_inclass -- DISCOVER whether the lighting change is in-class, and mint the map.
# ---------------------------------------------------------------------------
LI_INCLASS = {
    "name": "li_inclass",
    "comment": (
        "DISCOVERS whether the lighting change between this frame and its reference "
        "frame is IN-CLASS (a diagonal / von Kries map). The test is an "
        "ORDER-STATISTIC CONSISTENCY: under a diagonal map every statistic scales by "
        "the same per-channel gain, so anchor:sum must agree between the frames on "
        "ALL THREE channels (exact integer cross-multiplication). It requires NO "
        "surface correspondence -- so it is not circular with recognition, which is "
        "what it gates. If it HOLDS: mint an Illuminant carrying the discovered gain "
        "as an exact (numer,denom) PAIR per channel (the ratio is the CROSS-FRAME "
        "map, held intensionally -- never divided into a float, per the "
        "frame/continuum invariant) and set illum_inclass=1. If it FAILS: nothing is "
        "minted and illum_inclass stays 0, so li_recognize cannot fire -- a "
        "spatially-varying (multi-illuminant) change is REFUSED rather than blindly "
        "normalised. That refusal is the whole difference between an invariance and "
        "a universal container (sec 1.1). Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Lt(A(V("frame"), "illum_inclass"), Lit(0.5)),
        Gt(A(V("frame"), "stats_done"), Lit(0.5)),
        Gt(A(V("ref"), "stats_done"), Lit(0.5)),
        _stat_consistent(V("frame"), V("ref"), "L"),
        _stat_consistent(V("frame"), V("ref"), "M"),
        _stat_consistent(V("frame"), V("ref"), "S"),
    ]),
    "effects": [
        ["add_node", "ill", "Illuminant", {
            # the discovered gain per channel, as an exact ratio PAIR (never a float)
            "gL_num": term(A(V("frame"), "aL")), "gL_den": term(A(V("ref"), "aL")),
            "gM_num": term(A(V("frame"), "aM")), "gM_den": term(A(V("ref"), "aM")),
            "gS_num": term(A(V("frame"), "aS")), "gS_den": term(A(V("ref"), "aS")),
            "minted": term(Lit(1.0)),
        }],
        ["add_edge", "frame", "has_illuminant", "ill"],
        ["set_attr", "frame", "illum_inclass", term(Lit(1.0))],
    ],
}


def cones_eq(x, ref):
    """The exact cone triple of x equals that of ref (the grouping key -- colour
    identity's exact-Count clustering, with NO magic radius)."""
    return And([Eq(A(x, "c" + ch), A(ref, "c" + ch)) for ch in CH])


def same_cone_members(frame, ref):
    """The frame's own surfaces sharing ref's exact cone triple (the kind's members)."""
    return Filter(Nbrs(frame, "has_surface"), "q", cones_eq(V("q"), ref))


def proto_eq(sid, ref):
    """A held SurfaceIdentity's prototype equals ref's raw cone triple."""
    return And([Eq(A(sid, "p" + ch), A(ref, "c" + ch)) for ch in CH])


# ---------------------------------------------------------------------------
# li_mint -- MDL-gated mint of a SurfaceIdentity in the REFERENCE frame.
# ---------------------------------------------------------------------------
LI_MINT = {
    "name": "li_mint",
    "comment": (
        "DYNAMIC QUANTIZATION (mint) of a SurfaceIdentity from the REFERENCE frame. "
        "Gates: (1) lighting>0.5; (2) THE MDL GATE -- Count(surfaces in this frame "
        "with the same EXACT cone triple) >= 2 = m_min, which FALLS OUT of d=3 (a "
        "prototype costs d integers and saves d-1 per member, so it pays iff "
        "m > d/(d-1) = 1.5, i.e. m >= 2 -- NO magic number, VISION_PROTOCOL sec 13); "
        "(3) the CANONICAL-REPRESENTATIVE guard -- only the min-sidx member of a "
        "cone triple may mint, so under batch tick exactly ONE identity per distinct "
        "reflectance is minted; (4) Not(Exists SurfaceIdentity at this triple) -- "
        "recognize-not-re-mint across passes. Effects: add the SurfaceIdentity "
        "carrying the prototype cones (pL,pM,pS) AND ITS OWN FRAME'S ANCHOR "
        "(paL,paM,paS) -- the anchor must travel with the prototype, because the "
        "invariant is the reflectance RELATIVE to the frame it was seen in. "
        "UNSUPERVISED: no label is read. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"]],
    "where": And([
        ENABLED(),
        Gt(A(V("frame"), "is_reference"), Lit(0.5)),
        Gt(A(V("frame"), "stats_done"), Lit(0.5)),
        {"type": "Gte",
         "a": Count(same_cone_members(V("frame"), V("R"))),
         "b": Lit(M_MIN)},
        Not(Exists(Nbrs(V("frame"), "has_surface"), "p",
                   And([cones_eq(V("p"), V("R")),
                        Lt(A(V("p"), "sidx"), A(V("R"), "sidx"))]))),
        Not(Exists(NodesOf("SurfaceIdentity"), "si", proto_eq(V("si"), V("R")))),
    ]),
    "effects": [
        ["add_node", "sid", "SurfaceIdentity", {
            "pL": term(A(V("R"), "cL")),
            "pM": term(A(V("R"), "cM")),
            "pS": term(A(V("R"), "cS")),
            "paL": term(A(V("frame"), "aL")),
            "paM": term(A(V("frame"), "aM")),
            "paS": term(A(V("frame"), "aS")),
            "members": term(Count(same_cone_members(V("frame"), V("R")))),
            "sid_key": term(A(V("R"), "sidx")),
            "minted": term(Lit(1.0)),
        }],
        ["add_edge", "frame", "has_identity", "sid"],
    ],
}


def _anchor_relative_match(surf, frame, sid, ch):
    """c_ch / a_ch == p_ch / pa_ch, as EXACT integer cross-multiplication.

    THE INVARIANT. Under a diagonal illuminant both the surface's cone value and the
    frame's anchor are multiplied by the SAME per-channel gain, so the ratio between
    them is exactly what the illuminant LEAVES FIXED. Cross-multiplied: the ratio is
    a cross-frame quantity and is never divided into a float (no rounding, no
    tolerance, no threshold).
    """
    return Eq(Times(A(surf, "c" + ch), A(sid, "pa" + ch)),
              Times(A(sid, "p" + ch), A(frame, "a" + ch)))


# ---------------------------------------------------------------------------
# li_recognize -- THE INVARIANT: anchor-relative reflectance match.
# ---------------------------------------------------------------------------
LI_RECOGNIZE = {
    "name": "li_recognize",
    "comment": (
        "THE LIGHTING INVARIANT. A surface in a TEST frame is recognized as a held "
        "SurfaceIdentity iff (a) the frame's lighting change was DISCOVERED to be "
        "in-class (illum_inclass=1 -- so an out-of-class change can never be "
        "force-matched) and (b) its cone value RELATIVE TO ITS OWN FRAME'S ANCHOR "
        "equals the prototype's value relative to the anchor of the frame the "
        "prototype was minted in, on ALL THREE channels (exact integer "
        "cross-multiplication). The illuminant cancels identically: this is "
        "'discover the cross-frame map and take what it leaves fixed'. Sets "
        "lit_recognized=1 and lit_id (the identity's key). A surface whose "
        "reflectance was never minted, or whose frame is out-of-class, leaves "
        "lit_recognized at its 0 init -- REFUSED, not force-assigned, which is the "
        "floor a nearest-assignment mechanism cannot produce. "
        "THE IDENTITY IS BOUND BY THE MATCH, NOT SELECTED IN THE EFFECT: the second "
        "match pattern binds `sid` by traversing from the REFERENCE frame's own "
        "has_identity hub, so the pairing (surface, identity) is decided by the "
        "rule's own matcher and lit_id is read straight off the BOUND node. An "
        "earlier version selected the identity inside the effect with "
        "Pick/PickUnique(Filter(NodesOfType('SurfaceIdentity'), ...)); PickUnique "
        "PANICKED with 3 candidates, proving the filter predicate was not applied in "
        "effect position and that Pick would have written a SILENT WRONG ANSWER "
        "(VISION_PROTOCOL sec 12.3 -- the ambiguous read made loud, then fixed the "
        "way the panic message itself prescribes: traverse from the owning hub "
        "instead of selecting globally). Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["refframe", "has_identity", "sid"]],
    "where": And([
        ENABLED(),
        Gt(A(V("frame"), "illum_inclass"), Lit(0.5)),
        Gt(A(V("frame"), "stats_done"), Lit(0.5)),
        And([_anchor_relative_match(V("R"), V("frame"), V("sid"), ch)
             for ch in CH]),
    ]),
    "effects": [
        ["set_attr", "R", "lit_recognized", term(Lit(1.0))],
        ["set_attr", "R", "lit_id", term(A(V("sid"), "sid_key"))],
    ],
}


# ---------------------------------------------------------------------------
# li_raw_recognize -- THE RAW BASELINE (no discounting) -- the control.
# ---------------------------------------------------------------------------
LI_RAW_RECOGNIZE = {
    "name": "li_raw_recognize",
    "comment": (
        "THE RAW BASELINE / untangling-style control (colour identity's and "
        "category's exact-match MEMORIZATION pattern, here as the NO-DISCOUNTING "
        "arm): raw_recognized=1 iff the surface's RAW cone triple exactly equals a "
        "SurfaceIdentity's prototype -- the illuminant is not factored at all. Under "
        "any non-identity gain the raw values move and this CONFUSES, while "
        "li_recognize does not. The measured (raw_correct, lit_correct) pair is what "
        "makes the discounting LOAD-BEARING rather than decorative (sec 13.2). "
        "Deliberately NOT gated on illum_inclass -- the baseline must be the honest "
        "no-mechanism condition (sec 6), not a crippled copy of the treatment. Like "
        "li_recognize it binds the identity BY THE MATCH (from the reference frame's "
        "has_identity hub), so the two arms are read the SAME way and the comparison "
        "between them is apples-to-apples. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["refframe", "has_identity", "sid"]],
    "where": And([
        ENABLED(),
        proto_eq(V("sid"), V("R")),
    ]),
    "effects": [
        ["set_attr", "R", "raw_recognized", term(Lit(1.0))],
        ["set_attr", "R", "raw_id", term(A(V("sid"), "sid_key"))],
    ],
}


SEED = {
    "id": "vision_lighting",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "LIGHTING / APPEARANCE INVARIANCE (FRONTIER T3) -- the illuminant as a low-D "
        "CROSS-FRAME map, discovered and factored, with recognition invariant to what "
        "it leaves fixed. An ObjSurface carries integer cones (cL,cM,cS) = reflectance "
        "x illuminant: the reflectance is the stable IN-FRAME property (integer "
        "lattice), the illuminant a diagonal (von Kries) CROSS-FRAME map. "
        "li_frame_stats reads the frame's OWN per-channel anchor (max) and sum "
        "(hub-scoped via Neighbours, no global grab); li_inclass DISCOVERS whether the "
        "change is in-class by an ORDER-STATISTIC CONSISTENCY test needing no surface "
        "correspondence, and mints an Illuminant holding the gain as an exact "
        "(numer,denom) pair -- refusing a spatially-varying change outright; li_mint "
        "MDL-mints a SurfaceIdentity (m_min=2 FALLS OUT of d=3) carrying the prototype "
        "AND its frame's anchor; li_recognize matches by ANCHOR-RELATIVE reflectance "
        "via exact integer cross-multiplication (the illuminant cancels identically); "
        "li_raw_recognize is the no-discounting RAW BASELINE control. NO new Rust: "
        "reuses Count/Filter/NodesOfType/Neighbours/MaxOver/Sum/Exists/Not/Eq/Gt/Lt/"
        "Times/And + run_rules. NO magic number: the anchor is the frame's own "
        "measured ceiling, m_min falls out of d=3, and every comparison is exact "
        "integer cross-multiplication (no threshold, no tolerance). BOUNDED: the "
        "DIAGONAL illuminant class ONLY -- multi-illuminant scenes, shadows, "
        "penumbrae and spatially-varying light are NOT solved, only REFUSED (the "
        "NAMED FRONTIER); the global reflectance/illuminant ambiguity is intrinsic "
        "and unresolved by construction. Flag-gated on LightingParams.lighting, OFF "
        "by default (sec 9 -- default 0 => byte-identical, seed inert). See "
        "VISION_LIGHTING_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_lighting_mt",
        "label": ("lighting/appearance invariance: the illuminant as a discovered "
                  "low-D cross-frame map, factored by an anchor-relative code"),
    },
    "nodes": [
        {"local_id": 0, "type": "LightingParams", "attrs": {"lighting": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [LI_FRAME_STATS, LI_INCLASS, LI_MINT, LI_RECOGNIZE, LI_RAW_RECOGNIZE],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_lighting.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
