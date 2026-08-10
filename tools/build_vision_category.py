#!/usr/bin/env python3
"""Emit seeds/vision_category.json — CATEGORY-LEVEL RECOGNITION (FRONTIER T2): a
category as an MDL-minted AXIS-CODEBOOK REGION, as pure graph data (NO new Rust).

See VISION_CATEGORY_PREREG.md. Generalizes the colour-identity MDL mint
(VISION_COLOUR_IDENTITY_RESULTS.md) from a POINT (an exact colour value) to a REGION
(a MinOver/MaxOver box over object axes), so an UNSEEN instance is recognized by
PROJECTION-CONTAINMENT (generalization, not memorization). An ObjItem carries an
integer coordinate split into a DISCRETE part-signature (d0,d1 — the grouping key,
shared exactly by a kind, exactly like colour's exact-value grouping) and CONTINUOUS
proportion axes (v0,v1 — the within-category variation and the generalization
extent):

  cat_mint      MINTS an ObjCategory quantum where instances of a kind CLUSTER (>= 3
                share the exact discrete signature = m_min, which FALLS OUT of
                d_disc=2: m > d/(d-1) = 2) and MDL COMPRESSES (the shared signature
                stored once per category, not once per member). Records the signature,
                member count, canonical-member EXEMPLAR (ex_v0,ex_v1) and the REGION
                box (MinOver/MaxOver of the members' v0,v1). Canonical-representative
                (min-oidx member mints) + Not(Exists ObjCategory@signature) guards
                make it batch-safe (exactly one category per kind).
  cat_recognize RECOGNIZES an ObjItem as an ObjCategory iff its signature matches AND
                its (v0,v1) is CONTAINED in the box (Lte both bounds both axes). This
                is the projection into the held subspace — the GENERALIZATION readout
                (an unseen interior coordinate is recognized) AND the FLOOR (an
                out-of-box or novel-signature instance is refused, not force-assigned).
  cat_memorize  the MEMORIZATION CONTROL: mem_recognized=1 iff (v0,v1) EXACTLY equals
                a category's stored EXEMPLAR. A memorizer recognizes only exact stored
                exemplars; a held-out interior instance gets 0. The DiCarlo-style
                control — containment GENERALIZES what exact-match MEMORIZES.

Flag-gated on CategoryParams.identity, OFF by default (§9). NO new Rust: reuses
Count/Filter/NodesOfType/MinOver/MaxOver/Exists/Not/Eq/Gt/Gte/Lte/And + run_rules.
The in-frame coordinate is INTEGER; the continuous lives ONLY in the cross-frame
containment comparison (the frame/continuum invariant). Category minting is
UNSUPERVISED (no label is read by any rule).

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_category.py
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
def MaxOver(src, var, value):
    return {"type": "MaxOver", "source": src, "var_name": var, "value": value}
def PickCP():
    return {"type": "PickUnique", "source": NodesOf("CategoryParams")}
def term(x):            return {"__term__": x}


R = V("R")


def sig_eq(x, ref):
    """The DISCRETE part-signature (d0,d1) of x equals that of ref — the grouping
    key that clusters a kind WITHOUT a magic radius (colour's exact-Count mechanism
    applied to the signature sub-coordinate)."""
    return And([Eq(A(x, "d0"), A(ref, "d0")), Eq(A(x, "d1"), A(ref, "d1"))])


def same_sig_members(ref):
    """The set of ObjItems sharing ref's discrete signature (the kind's members)."""
    return Filter(NodesOf("ObjItem"), "q", sig_eq(V("q"), ref))


def ENABLED():
    return Gt(A(PickCP(), "identity"), Lit(0.5))


# ---------------------------------------------------------------------------
# cat_mint -- DYNAMIC QUANTIZATION (mint), MDL count-gated + region box.
# ---------------------------------------------------------------------------
CAT_MINT = {
    "name": "cat_mint",
    "comment": (
        "DYNAMIC QUANTIZATION (colour's ci_mint_category, generalized from a POINT "
        "to a REGION): MINT an ObjCategory quantum for a kind where its instances "
        "CLUSTER in the object axis space and MDL COMPRESSES. Gates: (1) "
        "identity>0.5; (2) THE MDL GATE -- Count(same exact discrete signature) >= 3 "
        "= m_min, which FALLS OUT of d_disc=2 (a category pays iff m > d/(d-1) = 2, "
        "so m>=3 -- the shared signature is stored ONCE per category instead of once "
        "per member; NO magic number, VISION_PROTOCOL sec 13); (3) the "
        "CANONICAL-REPRESENTATIVE guard -- only the min-oidx member of a signature "
        "may mint, so under batch s.tick() (all bindings snapshotted before any "
        "effect) exactly ONE member per DISTINCT signature passes and mints exactly "
        "ONE category per kind (the ground rung's 'single unified rule' lesson, the "
        "colour rung's fix -- NOT a magic threshold); (4) Not(Exists ObjCategory at "
        "this signature) -- recognize-not-re-mint across passes / re-presentations. "
        "Effects: add the ObjCategory carrying the discrete signature (d0,d1), the "
        "member count, the canonical minter's EXEMPLAR (ex_v0,ex_v1 -- used by the "
        "memorization control), and the REGION BOX (v0lo/v0hi/v1lo/v1hi = "
        "MinOver/MaxOver of the members' v0,v1 -- the box extent FALLS OUT of the "
        "members' own spread, no magic radius), and link has_category. UNSUPERVISED: "
        "no label is read. Flag-gated on identity>0.5, OFF by default (sec 9)."
    ),
    "match": [["scene", "has_obj", "R"]],
    "where": And([
        ENABLED(),
        Gte(Count(same_sig_members(R)), Lit(3)),
        Not(Exists(NodesOf("ObjItem"), "p",
                   And([sig_eq(V("p"), R), Lt(A(V("p"), "oidx"), A(R, "oidx"))]))),
        Not(Exists(NodesOf("ObjCategory"), "cat", sig_eq(V("cat"), R))),
    ]),
    "effects": [
        ["add_node", "cat", "ObjCategory", {
            "d0": term(A(R, "d0")),
            "d1": term(A(R, "d1")),
            "members": term(Count(same_sig_members(R))),
            "ex_v0": term(A(R, "v0")),
            "ex_v1": term(A(R, "v1")),
            "v0lo": term(MinOver(same_sig_members(R), "m", A(V("m"), "v0"))),
            "v0hi": term(MaxOver(same_sig_members(R), "m", A(V("m"), "v0"))),
            "v1lo": term(MinOver(same_sig_members(R), "m", A(V("m"), "v1"))),
            "v1hi": term(MaxOver(same_sig_members(R), "m", A(V("m"), "v1"))),
            "minted": term(Lit(1.0)),
        }],
        ["add_edge", "scene", "has_category", "cat"],
    ],
}


# ---------------------------------------------------------------------------
# cat_recognize -- projection into the held subspace: signature match AND box
#   containment. The GENERALIZATION readout AND the floor.
# ---------------------------------------------------------------------------
CAT_RECOGNIZE = {
    "name": "cat_recognize",
    "comment": (
        "RECOGNIZE an ObjItem as an ObjCategory iff its discrete signature matches "
        "AND its (v0,v1) is CONTAINED in the category's REGION box "
        "(v0lo<=v0<=v0hi AND v1lo<=v1<=v1hi -- Lte, the continuous cross-frame "
        "comparison; in-frame coords stay integer). This is the PROJECTION into the "
        "held axis subspace: a NEVER-SEEN interior coordinate is recognized "
        "(GENERALIZATION by interpolation), while an out-of-box or novel-signature "
        "instance leaves cat_recognized at its 0 init (REFUSED -- the FLOOR colour's "
        "nearest-assignment lacked, and the proof the box is LOAD-BEARING, sec 13.2). "
        "Sets cat_recognized=1 and the recognized signature cat_sig0/cat_sig1. "
        "Effect values are constant once set, so run_rules converges (no re-fire). "
        "Flag-gated on identity>0.5, OFF by default (sec 9)."
    ),
    "match": [["scene", "has_obj", "R"]],
    "where": And([
        ENABLED(),
        Exists(NodesOf("ObjCategory"), "c", And([
            sig_eq(V("c"), R),
            Lte(A(V("c"), "v0lo"), A(R, "v0")),
            Lte(A(R, "v0"), A(V("c"), "v0hi")),
            Lte(A(V("c"), "v1lo"), A(R, "v1")),
            Lte(A(R, "v1"), A(V("c"), "v1hi")),
        ])),
    ]),
    "effects": [
        ["set_attr", "R", "cat_recognized", term(Lit(1.0))],
        ["set_attr", "R", "cat_sig0", term(A(R, "d0"))],
        ["set_attr", "R", "cat_sig1", term(A(R, "d1"))],
    ],
}


# ---------------------------------------------------------------------------
# cat_memorize -- the MEMORIZATION CONTROL (exact-exemplar match).
# ---------------------------------------------------------------------------
CAT_MEMORIZE = {
    "name": "cat_memorize",
    "comment": (
        "The MEMORIZATION CONTROL (colour's exact-match, in-seed): mem_recognized=1 "
        "iff the ObjItem's (v0,v1) EXACTLY equals some ObjCategory's stored EXEMPLAR "
        "(ex_v0,ex_v1) with a matching signature. A memorizer recognizes ONLY exact "
        "stored exemplars, so a held-out interior instance (coords never trained) "
        "gets mem_recognized=0 while cat_recognize gives 1 -- the DiCarlo-style "
        "control that proves the region GENERALIZES what exact-match MEMORIZES. "
        "Flag-gated on identity>0.5, OFF by default (sec 9)."
    ),
    "match": [["scene", "has_obj", "R"]],
    "where": And([
        ENABLED(),
        Exists(NodesOf("ObjCategory"), "c", And([
            sig_eq(V("c"), R),
            Eq(A(V("c"), "ex_v0"), A(R, "v0")),
            Eq(A(V("c"), "ex_v1"), A(R, "v1")),
        ])),
    ]),
    "effects": [
        ["set_attr", "R", "mem_recognized", term(Lit(1.0))],
    ],
}


SEED = {
    "id": "vision_category",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "CATEGORY-LEVEL RECOGNITION (FRONTIER T2) -- a category as an MDL-minted "
        "AXIS-CODEBOOK REGION. Generalization to a KIND: a NEW instance never seen "
        "before is recognized as a member of a known category by its PROJECTION "
        "falling into a held category subspace (a chair you have never seen, known "
        "as a chair). Generalizes the colour-identity MDL mint from a POINT (an "
        "exact colour value) to a REGION (a MinOver/MaxOver box over object axes), "
        "the Chang-Tsao axis-code picture at the abstract-coordinate grain: an "
        "ObjItem is a projection onto axes split into a DISCRETE part-signature "
        "(d0,d1 -- the grouping key, shared exactly by a kind) and CONTINUOUS "
        "proportion axes (v0,v1 -- the within-category variation and generalization "
        "extent). cat_mint mints an ObjCategory where a kind's instances cluster "
        "(Count(same signature) >= 3 = m_min, FALLS OUT of d_disc=2) and MDL "
        "compresses, recording the signature, exemplar and REGION box; "
        "cat_recognize recognizes by signature-match AND box-containment (the "
        "generalization readout AND the floor); cat_memorize is the exact-exemplar "
        "MEMORIZATION control. NO new Rust: reuses "
        "Count/Filter/NodesOfType/MinOver/MaxOver/Exists/Not/Eq/Gt/Gte/Lte/And + "
        "run_rules. In-frame coordinate INTEGER; the continuous lives ONLY in the "
        "cross-frame containment comparison (the frame/continuum invariant). "
        "UNSUPERVISED (no label read). BOUNDED: axes GIVEN not learned from pixels; "
        "axis-aligned BOX region; interpolation within the box (extrapolation "
        "refused); discrete-similarity regime -- NOT lighting/deformation/style, NOT "
        "the learned axis-codebook at natural-image scale (the named frontiers). "
        "Flag-gated on CategoryParams.identity, OFF by default (sec 9 -- default 0 "
        "=> byte-identical, seed inert). See VISION_CATEGORY_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_category_mt",
        "label": ("category-level recognition: a category as an MDL-minted "
                  "axis-codebook region, generalization by projection-containment"),
    },
    "nodes": [
        {"local_id": 0, "type": "CategoryParams", "attrs": {"identity": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [CAT_MINT, CAT_RECOGNIZE, CAT_MEMORIZE],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_category.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
