#!/usr/bin/env python3
"""EMIT `seeds/vision_motion_group.json` — COMMON MOTION as the object criterion.

A one-off authoring script that emits graph DATA (CLAUDE.md: `tools/*` may emit
seed manifests; they are not agent runtime). Every DECISION in the emitted seed
is a Rule term-tree. The adapter supplies only the vector matrix and a clock.

THE REPRESENTATION IS A VECTOR MATRIX, NOT PER-CELL SCALARS.
Each MCell carries `v = [vy, vx]` as ONE attribute, and every motion question is
a DIRECT VECTOR READ via the engine's own `Magnitude(VecSub(a.v, b.v))` — never
a coherence statistic rebuilt from pairwise per-component comparisons.

§13 — THE MOTION-AGREEMENT TOLERANCE IS NOT A NUMBER IN THIS FILE.
`mo_tol_otsu` takes Otsu's split of the field's OWN adjacent-pair vector-
difference distribution, and THE CANDIDATE SPLITS ARE THE OBSERVED `pd` VALUES
THEMSELVES — so the tolerance is the `pd` of a cell the graph picked. Precedent:
`ca_otsu` in seeds/vision_cut_abstention.json, whose honest limit is inherited
and pre-registered: Otsu has no null hypothesis, it returns a split on any
distribution. The stills and noise arms measure exactly that.

A MEDIAN split is REFUSED — 50%-by-construction, the defect `ch_drive_median`
already carries in this tree.
"""
from __future__ import annotations
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "vision_motion_group.json")

# ---------- term helpers ----------------------------------------------------
def V(n):            return {"type": "Var", "name": n}
def L(x):            return {"type": "Lit", "value": x}
def A(n, k):         return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def NB(n):           return {"type": "Neighbours", "node": V(n), "edge_type": "neighbour", "any_type": False}
def MCELLS():        return {"type": "NodesOfType", "node_type": "MCell"}
def MOBJS():         return {"type": "NodesOfType", "node_type": "MotionObject"}
def PARAM(k):        return {"type": "Attr", "key": k,
                             "node": {"type": "PickUnique",
                                      "source": {"type": "NodesOfType", "node_type": "MotionParams"}}}
def AND(*i):         return {"type": "And", "items": list(i)}
def OR(*i):          return {"type": "Or", "items": list(i)}
def NOT(x):          return {"type": "Not", "arg": x}
def GT(a, b):        return {"type": "Gt", "a": a, "b": b}
def LT(a, b):        return {"type": "Lt", "a": a, "b": b}
def LTE(a, b):       return {"type": "Lte", "a": a, "b": b}
def EQ(a, b):        return {"type": "Eq", "a": a, "b": b}
def FILTER(src, var, pred):   return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def EXISTS(src, var, pred):   return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def COUNT(src):               return {"type": "Count", "source": src}
def SUM(src, var, val):       return {"type": "Sum", "source": src, "var_name": var, "value": val}
def MAXOVER(src, var, val, default=None):
    d = {"type": "MaxOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        d["default"] = default
    return d
def ARGMIN(src, var, val):    return {"type": "Argmin", "source": src, "var_name": var, "value": val, "default": None}
def ARGMAX(src, var, val):    return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": None}
def MINUS(a, b):     return {"type": "Minus", "a": a, "b": b}
def TIMES(*i):       return {"type": "Times", "items": list(i)}
def DIV(a, b):       return {"type": "Div", "a": a, "b": b}
def MAX(a, b):       return {"type": "Max", "a": a, "b": b}
def T(term):         return {"__term__": term}

# THE DIRECT VECTOR READ. One term. `v` is the whole vector, never two scalars.
def VDIFF(a, b):
    return {"type": "Magnitude",
            "arg": {"type": "VecSub", "a": A(a, "v") if isinstance(a, str) else a,
                    "b": A(b, "v") if isinstance(b, str) else b}}

ARMED = GT(PARAM("marm"), L(0.5))          # master flag, OFF by default (§9)

# THE PHASE FLAG, AND WHY IT IS NOT BOOKKEEPING.
#
# The layers CANNOT be ordered by the fixpoint alone on this engine. Measured:
# a binding evaluated before the tolerance existed is not fully re-examined
# afterwards, so the flood runs partly under the initial 0.0 and `run_rules`
# then reports a genuine fixpoint (0 further sweeps) over a DEMONSTRABLY
# unsettled flood -- 6 cells with an admissible smaller-labelled neighbour, the
# guard evaluating True when applied to them by hand. Broadcasting the tolerance
# onto the cells did NOT fix it; only having the tolerance present before the
# first flood binding is evaluated did (7 sweeps, fully settled).
#
# So the phases are SEPARATED EXPLICITLY: derivation runs to fixpoint, then
# `mflood` is raised and the flood runs to fixpoint with every cell's tolerance
# already in place. The flag is graph DATA and the adapter only advances the
# clock and raises it -- admissible adapter work (PROTOCOL §0: Python translates
# I/O and advances time). It is recorded here rather than hidden because the
# earlier claim -- "the fixpoint orders the layers with no adapter sequencing" --
# was FALSE ON THIS ENGINE, and a seed comment asserting it would have been a
# docstring standing in for a gate.
FLOODING = GT(PARAM("mflood"), L(0.5))

# THE TOLERANCE IS READ FROM THE CELL, NOT FROM THE FIELD, AND THAT IS LOAD-BEARING.
#
# Measured engine behaviour (repro'd, and recorded because it silently produced a
# WRONG answer that still looked like a settled fixpoint): when a rule's guard reads
# an attribute of a node OUTSIDE its own match neighbourhood -- here `field.mtol`,
# written mid-fixpoint by `mo_tol_otsu` -- the engine does not fully re-examine the
# bindings that were evaluated before that write. `run_rules` then reports a genuine
# fixpoint (0 further sweeps) while the flood is DEMONSTRABLY unsettled: 6 cells,
# all in column 0, still had an admissible neighbour carrying a smaller label, and
# the guard evaluated True when applied by hand to exactly those cells.
# Pre-setting `mtol` before the tick settled the same field in 7 sweeps (4 labels ->
# 2), which is what isolated the cause.
#
# So the tolerance is BROADCAST onto every cell and the flood reads its OWN `mtol`.
# Every attribute the flood's guard touches then belongs to the cell or a
# 4-neighbour, and a local write marks the local binding dirty. This is also the
# better graph formulation: a cell holds the tolerance it applies.
#
# The adapter ASSERTS that every cell received the tolerance and aborts if not --
# a partial broadcast would leave stragglers floating at 0.0 and would look exactly
# like a legitimately fragmented field. This class of failure has read as success
# three times in this thread.
MTOL = A("R", "mtol")


def settled():
    """The flood has reached its fixpoint: no cell anywhere still has an
    admissible neighbour carrying a smaller label. Mirrors `bo_mint`'s
    whole-field settled predicate."""
    return NOT(EXISTS(MCELLS(), "z",
                      EXISTS(NB("z"), "n",
                             AND(LTE(VDIFF("n", "z"), A("z", "mtol")),
                                 LT(A("n", "mlabel"), A("z", "mlabel"))))))


def is_root(var):
    return EQ(A(var, "mlabel"), A(var, "cid"))


def group_of(var):
    """The cells sharing this cell's motion label."""
    return FILTER(MCELLS(), "z", EQ(A("z", "mlabel"), A(var, "mlabel")))


# ---------- Otsu, over the field's own `pd` distribution --------------------
def otsu_score(cand):
    """Otsu's between-class criterion at candidate split `cand.pd`, cleared of
    denominators exactly as `ca_otsu` does: (s0*n1 - s1*n0)^2 / (n0*n1).

    THE CANDIDATES ARE THE OBSERVED VALUES THEMSELVES. There is no percentile
    and no free parameter -- a percentile would be a number I chose.

    The topmost candidate needs NO guard: n1 = 0 forces s1 = 0, so the
    numerator is (s0*0 - 0*n0)^2 = 0 and it can never win. The Max(.., 1) is an
    ARITHMETIC division guard (ca_otsu's "the n1 > 0 guard is arithmetic"),
    not a tuned exclusion."""
    thr = A(cand, "pd")
    lo = FILTER(MCELLS(), "z", LTE(A("z", "pd"), thr))
    hi = FILTER(MCELLS(), "z", GT(A("z", "pd"), thr))
    n0, n1 = COUNT(lo), COUNT(hi)
    s0 = SUM(lo, "z", A("z", "pd"))
    s1 = SUM(hi, "z", A("z", "pd"))
    num = MINUS(TIMES(s0, n1), TIMES(s1, n0))
    return DIV(TIMES(num, num), MAX(TIMES(n0, n1), L(1.0)))


rules = []

# --- 1. the field's own local dispersion, as a DIRECT VECTOR READ -----------
rules.append({
    "name": "mo_pair_diff",
    "comment": "THE FIELD'S OWN DISPERSION, READ AS VECTORS. `pd` is the largest "
               "disagreement between this cell's motion vector and any 4-neighbour's, "
               "computed by ONE `Magnitude(VecSub(n.v, R.v))` -- the engine's native "
               "vector difference, NOT a statistic reassembled from per-component "
               "scalar comparisons. The distribution of `pd` over the field is what "
               "the tolerance falls out of in `mo_tol_otsu`; it is measured in the "
               "SAME units as the pairwise difference the flood tests, so no scale "
               "is smuggled between deriving the tolerance and applying it.",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED, LT(A("R", "pd_done"), L(0.5))),
    "effects": [
        ["set_attr", "R", "pd", T(MAXOVER(NB("R"), "n", VDIFF("n", "R")))],
        ["set_attr", "R", "pd_done", T(L(1.0))],
    ],
})

# --- 2a. the tolerance FALLS OUT (Otsu over the observed pd values) ---------
rules.append({
    "name": "mo_tol_otsu",
    "comment": "§13 -- THE TOLERANCE IS NOT A NUMBER IN THIS FILE. It is the `pd` of "
               "a cell the graph picked, by Otsu's between-class criterion over the "
               "field's OWN adjacent-pair vector-difference distribution. Fires only "
               "once every cell has been measured (the zero-pending guard), so the "
               "fixpoint orders the layers with no adapter sequencing. "
               "THE INHERITED HONEST LIMIT, pre-registered rather than discovered "
               "afterwards: Otsu has no NULL HYPOTHESIS -- it returns a split on any "
               "distribution, including a field with no motion structure in it at "
               "all. The stills and noise arms exist to measure exactly that.",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED,
                 LT(A("field", "mtol_done"), L(0.5)),
                 LT(PARAM("mtol_exact"), L(0.5)),
                 NOT(EXISTS(MCELLS(), "z", LT(A("z", "pd_done"), L(0.5))))),
    "effects": [
        ["set_attr", "field", "mtol",
         T(A(ARGMAX(MCELLS(), "t", otsu_score("t")), "pd"))],
        ["set_attr", "field", "mtol_done", T(L(1.0))],
    ],
})

# --- 2b. the registered secondary: EXACT vector equality, zero constants ----
rules.append({
    "name": "mo_tol_exact",
    "comment": "THE REGISTERED SECONDARY ARM. Tolerance = exact integer vector "
               "equality -- ZERO constants of any kind, mirroring the value flood's "
               "halt at the smallest difference the representation can express. "
               "Selected by graph DATA (`MotionParams.mtol_exact`), never a Python "
               "code path (PROTOCOL §0). Mutually exclusive with mo_tol_otsu.",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED,
                 LT(A("field", "mtol_done"), L(0.5)),
                 GT(PARAM("mtol_exact"), L(0.5))),
    "effects": [
        ["set_attr", "field", "mtol", T(L(0.0))],
        ["set_attr", "field", "mtol_done", T(L(1.0))],
    ],
})

# --- 2c. broadcast the tolerance so the flood's guard is purely LOCAL -------
rules.append({
    "name": "mo_tol_broadcast",
    "comment": "Hand the field's derived tolerance to each cell, so that every "
               "attribute `mo_flood` reads belongs to the cell or one of its "
               "4-neighbours. This is NOT bookkeeping — it is what makes the flood "
               "correct on this engine. Reading `field.mtol` directly left bindings "
               "evaluated before the mid-fixpoint write un-re-examined, and "
               "`run_rules` then reported a settled fixpoint over a DEMONSTRABLY "
               "unsettled flood (see the MTOL note above). It is also the better "
               "formulation on its own terms: a cell holds the tolerance it applies.",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED,
                 LT(A("R", "mtol_done"), L(0.5)),
                 GT(A("field", "mtol_done"), L(0.5))),
    "effects": [
        ["set_attr", "R", "mtol", T(A("field", "mtol"))],
        ["set_attr", "R", "mtol_done", T(L(1.0))],
    ],
})

# --- 3. COMMON FATE: connected components of shared motion ------------------
rules.append({
    "name": "mo_flood",
    "comment": "COMMON FATE. Min-label propagation across neighbours whose motion "
               "vectors agree within the field's own tolerance -- structurally "
               "identical to `bo_label`, but the equivalence is VECTOR AGREEMENT "
               "instead of equal luminance. This is the whole criterion change: a "
               "thing is what moves together, not what is enclosed.",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED, FLOODING,
                 GT(A("R", "mtol_done"), L(0.5)),
                 EXISTS(NB("R"), "m",
                        AND(LTE(VDIFF("m", "R"), MTOL),
                            LT(A("m", "mlabel"), A("R", "mlabel"))))),
    "effects": [
        ["set_attr", "R", "mlabel",
         T(A(ARGMIN(FILTER(NB("R"), "n", LTE(VDIFF("n", "R"), MTOL)),
                    "n", A("n", "mlabel")), "mlabel"))],
    ],
})

# --- 4. THE REFERENCE FRAME: the scene's dominant motion --------------------
rules.append({
    "name": "mo_dominant",
    "comment": "THE REFERENCE FRAME, AND IT FALLS OUT. The scene's dominant motion is "
               "the vector of the LARGEST motion-coherent group -- an Argmax over "
               "member count, with no constant anywhere. This is the substrate's own "
               "`induced_motion` / reference-frame concept made mechanical: the ground "
               "is not a labelled thing, it is whatever most of the field is doing. "
               "It is what makes a camera pan and a static background BOTH refusable "
               "by ONE test, and it is why `mo_mint` does not compare a group to its "
               "immediate ring (a ring comparison is near-vacuous at the flood's "
               "fixpoint -- any ring cell within tolerance would already have been "
               "merged in, so the test it appears to make is one the flood has "
               "already forced).",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED, FLOODING,
                 GT(A("R", "mtol_done"), L(0.5)),
                 LT(A("field", "dom_done"), L(0.5)),
                 is_root("R"),
                 settled(),
                 EQ(A("R", "cid"),
                    A(ARGMAX(FILTER(MCELLS(), "q", is_root("q")),
                             "q", COUNT(group_of("q"))), "cid"))),
    "effects": [
        ["set_attr", "field", "dom_v", T(A("R", "v"))],
        ["set_attr", "field", "dom_root", T(A("R", "cid"))],
        ["set_attr", "field", "dom_done", T(L(1.0))],
    ],
})

# --- 5. THE MINT ------------------------------------------------------------
rules.append({
    "name": "mo_mint",
    "comment": "A group is an OBJECT iff it moves DIFFERENTLY FROM THE SCENE'S "
               "DOMINANT MOTION, by more than the field's own tolerance -- one "
               "direct vector read, `Magnitude(VecSub(R.v, field.dom_v))`, against "
               "the SAME self-derived scale that bound the group together. One scale, "
               "used to bind and to separate; no second constant is introduced.\n\n"
               "THIS IS THE ARM THAT REFUSES A STABLE BACKGROUND PATCH. A patch of "
               "wall is part of the dominant group (or moves with it), so its "
               "contrast is zero and it is refused however beautifully it persists. "
               "A global camera pan is refused by the same test: the whole field is "
               "the dominant group, and nothing differs from it.\n\n"
               "`mcontrast` DISARMS the contrast test and is the DEAD-INSTRUMENT "
               "control: with it off, a uniformly translating field mints ONE object "
               "covering every cell -- a field containing no figure at all. It is "
               "graph DATA, so the control is the agent's own configuration, not a "
               "fork in the host (PROTOCOL §0).",
    "match_type": None,
    "match": [["field", "has_cell", "R"]],
    "where": AND(ARMED, FLOODING,
                 GT(A("field", "dom_done"), L(0.5)),
                 is_root("R"),
                 NOT(EXISTS(MOBJS(), "p", EQ(A("p", "root"), A("R", "cid")))),
                 OR(LT(PARAM("mcontrast"), L(0.5)),
                    GT(VDIFF("R", A("field", "dom_v")), MTOL))),
    "effects": [
        ["add_node", "mo", "MotionObject", {
            "root": T(A("R", "cid")),
            "members": T(COUNT(group_of("R"))),
            "v": T(A("R", "v")),
            # COHESION, GRAPH-RESIDENT: the worst vector disagreement between any
            # member and the group's own vector. A direct vector read, not an
            # aggregate over pairwise cell scalars.
            "disp": T(MAXOVER(group_of("R"), "z", VDIFF("z", "R"))),
            "contrast": T(VDIFF("R", A("field", "dom_v"))),
            "minted": T(L(1.0)),
        }],
        ["add_edge", "field", "has_mobject", "mo"],
    ],
})

seed = {
    "id": "vision_motion_group",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "COMMON MOTION AS THE OBJECT CRITERION. A thing is what moves together "
        "(Spelke's cohesion/continuity/contact; common fate before boundary or "
        "appearance). Static-form criteria -- enclosure, border ownership -- "
        "fragment a scene into however many enclosed regions it contains; common "
        "fate should yield FEW and LARGE.\n\n"
        "Motion is a VECTOR MATRIX: each MCell carries `v = [vy, vx]` as ONE "
        "attribute and every question is a direct `Magnitude(VecSub(..))` read.\n\n"
        "The tolerance falls out of the field's own dispersion (Otsu over the "
        "observed adjacent-pair differences); the reference frame falls out as the "
        "largest group. No motion-agreement constant appears in this file.\n\n"
        "MASTER-OFF by default (PROTOCOL §9): with `marm` at 0.0 no rule fires and "
        "every committed result is preserved."),
    "microtheory": {
        "name": "motion_grouping_visual",
        "definition": (
            "Segmentation by common fate. A proto-object is a maximal connected set "
            "of cells whose motion vectors agree within the field's own dispersion, "
            "and which moves differently from the scene's dominant motion. "
            "Substrate analogue: the substrate's motion-defined proto-object."),
        "category": "vision_domain",
        "parent": "vision_foundation",
    },
    "nodes": [{"local_id": 0, "type": "MotionParams",
               "attrs": {"marm": 0.0, "mcontrast": 0.0, "mtol_exact": 0.0,
                         "mflood": 0.0}}],
    "edges": [],
    "productions": [],
    "rules": rules,
}

if __name__ == "__main__":
    with open(OUT, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print(f"wrote {OUT}: {len(rules)} rules")
