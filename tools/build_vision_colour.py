#!/usr/bin/env python3
"""Emit seeds/vision_colour.json — COLOUR SALIENCE: pop-out for the EQUILUMINANT
target, as pure graph data (NO new Rust).

See VISION_COLOUR_PREREG.md. Two rules generalise the eye's surround-relative
difference (vision_lateral's lat_pool/lat_residual idiom) to the cone-opponent
axes L-M and S-(L+M), and combine the chromatic contrast INTERACTIVELY with
luminance salience into Region.residual -- which the unchanged vision_stream rule
then spends a bounded budget over. Flag-gated on ColourParams.{salience,colour},
both OFF by default (§9).

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_colour.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms, same as build_vision_stream.py) ----
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}
def And(items):         return {"type": "And", "items": items}
def Plus(items):        return {"type": "Plus", "items": items}
def Minus(a, b):        return {"type": "Minus", "a": a, "b": b}
def Times(items):       return {"type": "Times", "items": items}
def Div(a, b):          return {"type": "Div", "a": a, "b": b}
def Max(items):         return {"type": "Max", "items": items}
def Sqrt(arg):          return {"type": "Sqrt", "arg": arg}
def Abs(arg):           return {"type": "Abs", "arg": arg}
def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def Neigh(node, edge):  return {"type": "Neighbours", "node": node,
                                "edge_type": edge, "any_type": False}
def Fold(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc,
            "init": init, "body": body}
def PickCP():
    return {"type": "PickUnique",
            "source": {"type": "NodesOfType", "node_type": "ColourParams"}}
def term(x):            return {"__term__": x}


# --- per-cell opponent coordinates (integer, in-frame) -------------------------
# The two chromatic opponent axes + the achromatic (luminance) axis, from the raw
# cone attrs. `node` is a Var term (self R, or a neighbour n).
def RG(node):   return Minus(A(node, "cL"), A(node, "cM"))                    # L-M
def BY(node):   return Minus(A(node, "cS"), Plus([A(node, "cL"), A(node, "cM")]))  # S-(L+M)
def LUM(node):  return Plus([A(node, "cL"), A(node, "cM")])                   # L+M


# --- the surround MEAN of an opponent expression over the neighbour ring -------
# Div(sum over neighbours, count) -- a TRUE mean (edge cells pool fewer neighbours),
# the lat_pool idiom. `expr_of_n` is the opponent value at neighbour Var("n").
def smean(R, expr_of_n):
    ssum = Fold(Neigh(R, "neighbour"), "n", "acc", Lit(0.0),
                Plus([V("acc"), expr_of_n]))
    scount = Fold(Neigh(R, "neighbour"), "n", "acc", Lit(0.0),
                  Plus([V("acc"), Lit(1.0)]))
    return Div(ssum, Max([scount, Lit(1.0)]))


R = V("R")

# csal = ||opponent(R) - surround_mean(opponent)||  (Euclidean opponent-space
# distance from the surround; a CONTINUOUS magnitude, the continuous-in-comparison
# role of the frame/continuum invariant).
_drg = Minus(RG(R), smean(R, RG(V("n"))))
_dby = Minus(BY(R), smean(R, BY(V("n"))))
CSAL = Sqrt(Plus([Times([_drg, _drg]), Times([_dby, _dby])]))
# lsal = |lum(R) - surround_mean(lum)| : the SAME surround-relative difference on
# the achromatic axis (luminance salience / conspicuity).
LSAL = Abs(Minus(LUM(R), smean(R, LUM(V("n")))))


CC_CONTRAST = {
    "name": "cc_contrast",
    "comment": (
        "SURROUND-RELATIVE CONE-OPPONENT CONTRAST -- the eye's centre-surround "
        "difference (vision_lateral's lat_pool/lat_residual idiom) generalised to "
        "the cone-opponent axes. Per cell: csal = the Euclidean opponent-space "
        "DISTANCE of (L-M, S-(L+M)) from its surround mean (a CONTINUOUS contrast "
        "MAGNITUDE -- the continuous-in-comparison role of the frame/continuum "
        "invariant; the in-frame colour coordinate stays integer), and lsal = the "
        "SAME surround-relative difference on the achromatic axis L+M (luminance "
        "salience). Reads ONLY raw cone attrs (self + neighbours) -- NO cross-node "
        "computed dependency, so firing order is irrelevant. The surround mean is "
        "Div(Fold(+neighbour-value), Max(Fold(+1),1)): a TRUE mean that "
        "edge-corrects the ring. Flag-gated on ColourParams.salience>0.5, OFF by "
        "default (§9). Once per cell (cc_done guard)."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        Gt(A(PickCP(), "salience"), Lit(0.5)),
        Lt(A(R, "cc_done"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "R", "csal", term(CSAL)],
        ["set_attr", "R", "lsal", term(LSAL)],
        ["set_attr", "R", "cc_done", term(Lit(1.0))],
    ],
}


# residual = lsal + (colour on ? csal + lsal*csal : 0). The INTERACTIVE combine:
# luminance salience always; plus, when colour is armed, the chromatic contrast
# AND the interaction term lsal*csal -- the parameter-free superadditive form
# (1+lsal)(1+csal)-1, NOT strict addition (§13: the interaction is a product, not a
# tuned weight). colour=0 -> residual=lsal, the luminance path unbroken (ablation
# is graph data, §0). Reads the stored csal/lsal (self-dependency only).
CSAL_A = A(R, "csal")
LSAL_A = A(R, "lsal")
RESIDUAL = Plus([
    LSAL_A,
    Ite(Gt(A(PickCP(), "colour"), Lit(0.5)),
        Plus([CSAL_A, Times([LSAL_A, CSAL_A])]),
        Lit(0.0)),
])

CC_SALIENCE = {
    "name": "cc_salience",
    "comment": (
        "COMBINE colour salience with luminance salience INTERACTIVELY into "
        "Region.residual, which the unchanged vision_stream rule spends a bounded "
        "budget over. residual = lsal + (colour armed ? csal + lsal*csal : 0). The "
        "interaction term lsal*csal makes a BOTH-channel target's salience NOT a "
        "trivial sum (Bauer/Jolicoeur/Cowan reject naive additive-colour); the "
        "combine is the parameter-free (1+lsal)(1+csal)-1 -- no magic weight. With "
        "colour OFF the residual is lsal alone: colour is ADDITIVE capability, it "
        "does not break the luminance path. Flag-gated on ColourParams.salience>0.5 "
        "and gated on cc_done (waits for cc_contrast, data dependency). OFF by "
        "default (§9). Once per cell (sal_done guard)."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        Gt(A(PickCP(), "salience"), Lit(0.5)),
        Gt(A(R, "cc_done"), Lit(0.5)),
        Lt(A(R, "sal_done"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "R", "residual", term(RESIDUAL)],
        ["set_attr", "R", "sal_done", term(Lit(1.0))],
    ],
}


SEED = {
    "id": "vision_colour",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "COLOUR SALIENCE -- colour is the pop-out channel for the EQUILUMINANT "
        "target, where luminance salience is ZERO. Two rules generalise the eye's "
        "surround-relative difference (vision_lateral's lat_pool/lat_residual "
        "centre-surround) to the two cone-opponent axes L-M (red-green) and "
        "S-(L+M) (blue-yellow), orthogonal to luminance L+M: cc_contrast computes "
        "the CONTINUOUS opponent-space DISTANCE of a cell from its surround (the "
        "salience magnitude) and the same difference on the achromatic axis "
        "(luminance salience); cc_salience combines them INTERACTIVELY "
        "(lsal + csal + lsal*csal, the parameter-free superadditive form -- NOT "
        "strict addition; Bauer/Jolicoeur/Cowan) into Region.residual, which the "
        "unchanged vision_stream rule then streams a bounded budget over. So a "
        "near-equiluminant target (zero luminance contrast) with high cone-opponent "
        "contrast becomes salient via COLOUR and is streamed in, where a "
        "luminance-only salience MISSES it -- the 'ripe fruit against foliage' "
        "case. NOT categorical colour (the identity 'what' sign is the named "
        "frontier, out of scope). NO new Rust: reuses Fold/Neighbours/Div/Minus/"
        "Sqrt/Abs/Times + run_rules. In-frame colour coordinate is integer; only "
        "the contrast MAGNITUDE is continuous (the frame/continuum invariant). "
        "Flag-gated on ColourParams.{salience,colour}, both OFF by default (§9). "
        "See VISION_COLOUR_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_colour_mt",
        "label": "colour salience: surround-relative cone-opponent contrast, "
                 "pop-out for the equiluminant target",
    },
    "nodes": [
        {"local_id": 0, "type": "ColourParams",
         "attrs": {"salience": 0.0, "colour": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [CC_CONTRAST, CC_SALIENCE],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_colour.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
