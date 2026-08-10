#!/usr/bin/env python3
"""Emit seeds/vision_style.json — STYLE AS A DISCOVERED DIMENSION (FRONTIER T5): a
style as a per-SOURCE COHERENT offset on a DISCOVERED continuous axis, as pure graph
data (NO new Rust).

See VISION_STYLE_PREREG.md. Category (T2) captures the KIND (the discrete
part-signature) and leaves the CONTINUOUS within-category variation unexplained — the
region box is a blob. STYLE is the claim that the blob has structure: part of the
within-category variation is a COHERENT per-source offset, shared by everything ONE
source makes and DIFFERING across sources.

The mechanism is T2's continuous axes + the Omniglot writer-dimension rung's
per-source coherence mint (seeds/writer_dimensions.json — 'the writer's physical
limits become IMPLIED dimensions'; per-instance a delta is noise, POOLED across one
hand's output it is a coherent quantum coordinate), joined by Minus and Neighbours:

  sty_project      PROJECTS a recognized ObjItem into ITS OWN category's frame:
                   dv0 = v0 - c.v0lo, dv1 = v1 - c.v1lo. The anchor is the category's
                   MinOver box origin — derived from the members' own spread, NO magic
                   radius — and it is what makes an offset comparable ACROSS KINDS (a
                   raw coordinate is not: different kinds live in different parts of
                   the axis space). Gated on CONTAINMENT, so T2's floor is inherited:
                   an unrecognized / out-of-box item is NEVER projected.
  sty_mint_a0/a1   MINT an ObjStyle where >= 3 of ONE source's projected items agree
                   EXACTLY on THAT AXIS's offset. ONE RULE PER AXIS — so nothing tells
                   the mechanism which axis carries the style: a source coherent only
                   on axis 0 mints exactly one style, ON AXIS 0, and the minted node
                   RECORDS the axis it found. THE AXIS IS DISCOVERED. m_min = 3 FALLS
                   OUT of d_style = 2 (a style is an (axis, delta) PAIR; membership is
                   FREE because the source is OBSERVED, so it pays iff m > d_style = 2
                   — VISION_PROTOCOL sec 13, and the same >= 3 the writer rung used).
  sty_recognize_a0/a1
                   RECOGNIZE an item as being in a held style iff its offset equals a
                   held style's delta on that axis. SOURCE-BLIND: neither rule reads
                   the `produced` edge or any source attribute — which is exactly what
                   makes DISCRIMINATION a genuinely RISKED test (sec 13.1). Separate
                   per-axis attributes so the two rules can never race.
  sty_memorize     the MEMORIZATION CONTROL (T2's cat_memorize, in-seed): fires iff the
                   item's RAW (v0,v1) exactly equals a style's stored exemplar.

Flag-gated on StyleParams.style, OFF by default (sec 9). Every ENABLED guard is
ABSENCE-TOLERANT — Count(Filter(NodesOfType(StyleParams), ...)) >= 1, deliberately NOT
PickUnique, which returns None on an absent params node and would silently change
behaviour (the agnosia rung's lesson).

`Times` is NOT used anywhere in this seed. T3's caught defect: Times takes an `items`
LIST (runners/dsl/src/jsonio.rs:1274), so an a/b form parses to an EMPTY PRODUCT (= 1)
and can silently make an invariant Eq(1,1) — true for everything.

NO new Rust: reuses Minus (jsonio.rs:1270) / MinOver (jsonio.rs:1174) / Neighbours
(jsonio.rs:1121) / Count / Filter / NodesOfType / Exists / Not / Eq / And / Gt / Gte /
Lt / Lte + run_rules. In-frame coordinates stay INTEGER; the offset is an integer
difference within one frame's lattice (the frame/continuum invariant is untouched —
no real-valued quantity is introduced anywhere).

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_style.py
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
def Gte(a, b):          return {"type": "Gte", "a": a, "b": b}
def Lte(a, b):          return {"type": "Lte", "a": a, "b": b}
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}
def Minus(a, b):        return {"type": "Minus", "a": a, "b": b}
def Not(x):             return {"type": "Not", "arg": x}
def And(items):         return {"type": "And", "items": items}
def NodesOf(t):         return {"type": "NodesOfType", "node_type": t}
def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src):         return {"type": "Count", "source": src}
def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def MinOver(src, var, value):
    return {"type": "MinOver", "source": src, "var_name": var, "value": value}
def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type,
            "any_type": False}
def term(x):            return {"__term__": x}


R = V("R")
W = V("W")

# m_min FALLS OUT of d_style = 2 (see the module docstring / VISION_STYLE_PREREG sec 1.4).
D_STYLE = 2
M_MIN = 3


def ENABLED():
    """ABSENCE-TOLERANT flag guard (NOT PickUnique — which returns None on an absent
    params node and silently changes behaviour elsewhere)."""
    return Gte(Count(Filter(NodesOf("StyleParams"), "sp",
                            Gt(A(V("sp"), "style"), Lit(0.5)))), Lit(1))


def sig_eq(x, ref):
    """x's DISCRETE part-signature equals ref's — T2's grouping key (build_vision_
    category.py:79). Unchanged, and NOT re-derived: this seed reads T2's own attrs."""
    return And([Eq(A(x, "d0"), A(ref, "d0")), Eq(A(x, "d1"), A(ref, "d1"))])


def owning_categories(ref):
    """The ObjCategory (T2 mints exactly ONE per discrete signature) whose signature
    matches ref AND whose REGION BOX CONTAINS ref — i.e. exactly T2's cat_recognize
    condition (build_vision_category.py:167-170). A singleton set when ref is
    recognized, EMPTY when it is not: gating on Count >= 1 inherits T2's floor
    (novel-signature and out-of-box items are never projected)."""
    c = V("c")
    return Filter(NodesOf("ObjCategory"), "c", And([
        sig_eq(c, ref),
        Lte(A(c, "v0lo"), A(ref, "v0")),
        Lte(A(ref, "v0"), A(c, "v0hi")),
        Lte(A(c, "v1lo"), A(ref, "v1")),
        Lte(A(ref, "v1"), A(c, "v1hi")),
    ]))


def anchor(ref, key):
    """The owning category's box ORIGIN on one axis, in EFFECT position. MinOver over
    the singleton set = that category's value (the same MinOver T2 used to BUILD the
    box, read back here). Only evaluated when the where-clause has already established
    Count(owning_categories) >= 1."""
    return MinOver(owning_categories(ref), "c", A(V("c"), key))


# ---------------------------------------------------------------------------
# sty_project -- the WITHIN-CATEGORY coordinate (what a style can be coherent in).
# ---------------------------------------------------------------------------
STY_PROJECT = {
    "name": "sty_project",
    "comment": (
        "PROJECT a recognized ObjItem into ITS OWN category's frame: dv0 = v0 - "
        "c.v0lo, dv1 = v1 - c.v1lo, where c is the ObjCategory whose signature "
        "matches AND whose region box CONTAINS the item (exactly T2's cat_recognize "
        "condition, build_vision_category.py:167-170). THE ANCHOR IS THE CATEGORY'S "
        "OWN MinOver BOX ORIGIN -- derived from the members' own spread, NO magic "
        "radius, no tolerance -- and it is what makes an offset COMPARABLE ACROSS "
        "KINDS: a RAW coordinate is not comparable (kind A and kind B occupy different "
        "parts of the axis space), a within-category offset is. Gating on containment "
        "INHERITS T2's floor: a novel-signature or out-of-box item is NEVER projected, "
        "so it can never contribute to or be recognized by a style. The anchor is "
        "fetched in effect position by MinOver over the singleton owning-category set. "
        "Guard: dv_set != 1 (idempotent -- fires once per item, so run_rules "
        "converges). BOUND (pre-registered, arm L): the anchor is the box origin, so "
        "offsets are cross-kind coherent only while every kind's anchor is set "
        "consistently -- a kind whose training coverage omits the anchor-defining "
        "source shifts, and coherence there correctly FAILS rather than being patched. "
        "Flag-gated on style>0.5, OFF by default (sec 9)."
    ),
    "match": [["scene", "has_obj", "R"]],
    "where": And([
        ENABLED(),
        Gte(Count(owning_categories(R)), Lit(1)),
        Not(Eq(A(R, "dv_set"), Lit(1.0))),
    ]),
    "effects": [
        ["set_attr", "R", "dv0", term(Minus(A(R, "v0"), anchor(R, "v0lo")))],
        ["set_attr", "R", "dv1", term(Minus(A(R, "v1"), anchor(R, "v1lo")))],
        ["set_attr", "R", "dv_set", term(Lit(1.0))],
    ],
}


# ---------------------------------------------------------------------------
# sty_mint_a{0,1} -- DYNAMIC QUANTIZATION at the SOURCE grain: mint a style where one
#   source's offsets COHERE on ONE axis. ONE RULE PER AXIS => the axis is DISCOVERED.
# ---------------------------------------------------------------------------
def _agreeing_pool(dv_key):
    """The set of THIS source's projected items whose offset on `dv_key` agrees
    EXACTLY with R's. Neighbours(W, 'produced') is the per-source pool -- exactly the
    writer rung's Neighbours(w,'wrote_transform') hop (writer_dimensions.json:228).
    Agreement is EXACT equality: no radius, no tolerance (the colour / T2 / writer
    discipline)."""
    q = V("q")
    return Filter(Neighbours(W, "produced"), "q", And([
        Eq(A(q, "dv_set"), Lit(1.0)),
        Eq(A(q, dv_key), A(R, dv_key)),
    ]))


def _mint_rule(axis: int):
    dv_key = f"dv{axis}"
    return {
        "name": f"sty_mint_a{axis}",
        "comment": (
            f"MINT an ObjStyle where >= {M_MIN} of ONE source's projected items agree "
            f"EXACTLY on AXIS {axis}'s within-category offset ({dv_key}). THE STYLE IS "
            "A DISCOVERED DIMENSION: there is ONE RULE PER AXIS and BOTH run on EVERY "
            "source, so nothing tells the mechanism which axis carries the style -- a "
            "source whose axis-"
            f"{axis} offsets cohere while its other axis varies freely mints EXACTLY "
            f"ONE style, on axis {axis}, and the minted node RECORDS the axis it "
            "found. A source that coheres on neither mints NOTHING (the coherence "
            "crux: a mechanism that mints a style for ANY source would be a universal "
            "container and is disqualified). This is the Omniglot writer-dimension "
            "mint one level up (writer_dimensions.json:228 -- pool per source, require "
            ">= 3 exact agreement, mint the implied dimension); per-instance an offset "
            "is noise, POOLED across one source's output it is a coherent quantum "
            "coordinate. MDL: m_min = 3 FALLS OUT of d_style = 2 -- a style is an "
            "(axis, delta) PAIR (2 units: WHICH axis + WHAT offset) and membership is "
            "FREE because the source is OBSERVED (the produced edge), so the style "
            "pays iff m > d_style = 2 <=> m >= 3 (VISION_PROTOCOL sec 13; NOT tuned, "
            "and the same >= 3 the writer rung derived). Guards: (a) the "
            "CANONICAL-REPRESENTATIVE guard -- only the min-oidx member of an agreeing "
            "pool may mint, so under batch tick() (all bindings snapshotted before any "
            "effect) exactly ONE member mints exactly ONE style per (source, axis, "
            "delta); (b) Not Exists an ObjStyle already at this (src, axis, delta) -- "
            "recognize-not-re-mint across passes. Records src / axis / delta / members "
            "and the minting instance's RAW exemplar (ex_v0, ex_v1) for the "
            "memorization control. UNSUPERVISED: no label is read; the SOURCE is an "
            "observable (which hand produced it), not a category label. Flag-gated on "
            "style>0.5, OFF by default (sec 9)."
        ),
        "match": [["W", "produced", "R"]],
        "where": And([
            ENABLED(),
            Eq(A(R, "dv_set"), Lit(1.0)),
            Gte(Count(_agreeing_pool(dv_key)), Lit(M_MIN)),
            # canonical representative: no agreeing sibling with a smaller oidx
            Not(Exists(_agreeing_pool(dv_key), "p",
                       Lt(A(V("p"), "oidx"), A(R, "oidx")))),
            # mint-once at this (src, axis, delta)
            Not(Exists(NodesOf("ObjStyle"), "st", And([
                Eq(A(V("st"), "src"), A(W, "sid")),
                Eq(A(V("st"), "axis"), Lit(float(axis))),
                Eq(A(V("st"), "delta"), A(R, dv_key)),
            ]))),
        ]),
        "effects": [
            ["add_node", "st", "ObjStyle", {
                "src": term(A(W, "sid")),
                "axis": term(Lit(float(axis))),
                "delta": term(A(R, dv_key)),
                "members": term(Count(_agreeing_pool(dv_key))),
                "ex_v0": term(A(R, "v0")),
                "ex_v1": term(A(R, "v1")),
                "minted": term(Lit(1.0)),
            }],
            ["add_edge", "W", "has_style", "st"],
        ],
    }


# ---------------------------------------------------------------------------
# sty_recognize_a{0,1} -- SOURCE-BLIND recognition. This is what makes DISCRIMINATION
#   a genuinely RISKED test (sec 13.1).
# ---------------------------------------------------------------------------
def _held_styles(axis: int, dv_key: str):
    st = V("st")
    return Filter(NodesOf("ObjStyle"), "st", And([
        Eq(A(st, "axis"), Lit(float(axis))),
        Eq(A(st, "delta"), A(R, dv_key)),
    ]))


def _recognize_rule(axis: int):
    dv_key = f"dv{axis}"
    return {
        "name": f"sty_recognize_a{axis}",
        "comment": (
            f"RECOGNIZE an ObjItem as being in a held style on AXIS {axis} iff its "
            f"within-category offset ({dv_key}) EQUALS a held ObjStyle's delta on that "
            "axis. THE RULE IS SOURCE-BLIND -- it matches on the SCENE edge and NEVER "
            "reads the `produced` edge, W, or any source attribute. It is therefore "
            "mechanically POSSIBLE for an item of one source to be recognized as "
            "another source's style, and DISCRIMINATION (no cross-source pollution) is "
            "a RISKED test decided by the deltas alone, not a label lookup (sec 13.1). "
            "This is also the GENERALIZATION readout: a NEW instance with a coordinate "
            "never trained -- in a kind whose (source, kind) pair may itself be new -- "
            "is recognized by its OFFSET, which is the discovered dimension's own "
            "coordinate. Writes PER-AXIS attributes (sty_recognized_a"
            f"{axis} / sty_src_a{axis}) so the two axis rules can NEVER race or "
            "overwrite one another; an item genuinely in a style on both axes is "
            "reported on both, which is the correct semantics. sty_src is read back "
            "with MinOver over the matching styles (two sources sharing an identical "
            "delta on one axis ARE the same style -- a declared bound, sec 8). Effect "
            "values are constant once set, so run_rules converges. Flag-gated on "
            "style>0.5, OFF by default (sec 9)."
        ),
        "match": [["scene", "has_obj", "R"]],
        "where": And([
            ENABLED(),
            Eq(A(R, "dv_set"), Lit(1.0)),
            Gte(Count(_held_styles(axis, dv_key)), Lit(1)),
        ]),
        "effects": [
            ["set_attr", "R", f"sty_recognized_a{axis}", term(Lit(1.0))],
            ["set_attr", "R", f"sty_src_a{axis}",
             term(MinOver(_held_styles(axis, dv_key), "st", A(V("st"), "src")))],
        ],
    }


# ---------------------------------------------------------------------------
# sty_memorize -- the MEMORIZATION CONTROL (T2's cat_memorize, in-seed).
# ---------------------------------------------------------------------------
STY_MEMORIZE = {
    "name": "sty_memorize",
    "comment": (
        "The MEMORIZATION CONTROL (T2's cat_memorize, build_vision_category.py:184, "
        "at the style grain): sty_mem_recognized = 1 iff the ObjItem's RAW (v0,v1) "
        "EXACTLY equals some ObjStyle's stored exemplar (ex_v0, ex_v1) -- the raw "
        "coordinate of the instance that minted the style. A memorizer recognizes ONLY "
        "coordinates it stored, so a held-out instance (raw coordinate never trained) "
        "gets 0 while sty_recognize_a* gives 1, because the OFFSET generalizes what "
        "the raw coordinate memorizes. DECLARED ENTAILED (sec 13.1, prereg sec 5): the "
        "held-outs are constructed with unseen raw coordinates, so this control MUST "
        "return 0 -- it is reported as a CONSISTENCY check that the two channels are "
        "distinct, NOT banked as evidence. Flag-gated on style>0.5, OFF by default."
    ),
    "match": [["scene", "has_obj", "R"]],
    "where": And([
        ENABLED(),
        Exists(NodesOf("ObjStyle"), "st", And([
            Eq(A(V("st"), "ex_v0"), A(R, "v0")),
            Eq(A(V("st"), "ex_v1"), A(R, "v1")),
        ])),
    ]),
    "effects": [
        ["set_attr", "R", "sty_mem_recognized", term(Lit(1.0))],
    ],
}


SEED = {
    "id": "vision_style",
    "version": "1.0.0",
    "depends_on": ["vision_category"],
    "description": (
        "STYLE AS A DISCOVERED DIMENSION (FRONTIER T5) -- a style as a per-SOURCE "
        "COHERENT offset on a DISCOVERED continuous axis. Category (T2) captures the "
        "KIND (the discrete part-signature) and leaves the CONTINUOUS within-category "
        "variation unexplained; STYLE is the claim that this variation has structure "
        "-- part of it is a coherent offset shared by everything ONE source makes and "
        "DIFFERING across sources, orthogonally to the kind. sty_project projects a "
        "recognized ObjItem into its own category's frame (dv = v - box origin, the "
        "MinOver anchor that makes offsets comparable ACROSS KINDS; containment-gated, "
        "so T2's floor is inherited); sty_mint_a0/a1 -- ONE RULE PER AXIS, both "
        "running on every source, so THE AXIS IS DISCOVERED -- mint an ObjStyle where "
        ">= 3 of one source's offsets agree EXACTLY on that axis (m_min = 3 FALLS OUT "
        "of d_style = 2: a style is an (axis,delta) PAIR and membership is free "
        "because the source is observed); sty_recognize_a0/a1 recognize an item by "
        "offset, SOURCE-BLIND (no rule reads the produced edge), which makes "
        "discrimination a RISKED test; sty_memorize is the exact-raw-coordinate "
        "MEMORIZATION control. This is the Omniglot writer-dimension mint one level up "
        "('the writer's physical limits become IMPLIED dimensions'; two hands mint "
        "DISTINCT styles, no cross-writer pollution). NO new Rust: reuses Minus / "
        "MinOver / Neighbours / Count / Filter / NodesOfType / Exists / Not / Eq / And "
        "/ Gt / Gte / Lt / Lte + run_rules. Coordinates and offsets are INTEGER "
        "in-frame; no real-valued quantity is introduced (the frame/continuum "
        "invariant is untouched). Agreement is EXACT equality -- no radius, no "
        "tolerance anywhere. BOUNDED: axes GIVEN not learned from pixels; a style is a "
        "CONSTANT offset on ONE axis (not a scaling, rotation or instance-dependent "
        "function); two sources sharing a delta ARE one style; the anchor is the box "
        "origin, so cross-kind coherence requires consistent per-kind coverage; "
        "chance-level false agreement exists over a finite value pool. NOT the learned "
        "axis-codebook at natural-image scale, NOT deformation (the NAMED FRONTIERS). "
        "Flag-gated on StyleParams.style, OFF by default (sec 9 -- default 0 => "
        "byte-identical, seed inert). See VISION_STYLE_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_style_mt",
        "label": ("style as a discovered dimension: a per-source coherent offset on a "
                  "discovered continuous axis of the category's within-kind variation"),
    },
    "nodes": [
        {"local_id": 0, "type": "StyleParams", "attrs": {"style": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [
        STY_PROJECT,
        _mint_rule(0),
        _mint_rule(1),
        _recognize_rule(0),
        _recognize_rule(1),
        STY_MEMORIZE,
    ],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_style.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
