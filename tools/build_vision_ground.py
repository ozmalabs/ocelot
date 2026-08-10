#!/usr/bin/env python3
"""Emit seeds/vision_ground.json — the GROUNDED-FIELD / BLIND-SPOT seed.

An AUTHORING TOOL that emits graph DATA (like the other tools/* seed builders):
it constructs the Term-trees programmatically so the deeply-nested rule bodies
are not hand-written JSON. It makes NO decisions and holds NO agent state.

THE MECHANISM (PROTOCOL / CLAUDE.md §0 — the DECISION is in the RULES):

Each RetinaCell holds a grounded belief. A SENSED cell (photoreceptor present)
is grounded directly by its observation; a BLIND cell (the optic disc — no
data, gsensed=0) is FILLED FROM the surround by grounding. The blind spot is
invisible because it is filled from belief, a contour is bridged AS a contour
because the contour's AXIS is carried and only propagates along it, and an
ambiguous surround is HELD OPEN because two admissible continuations conflict.

Every rule folds a cell over its OWN 4-neighbourhood (`Neighbours`/`Filter`/
`Count`/`Sum`, exactly `vision_lateral`'s LOCAL pattern) — O(1) per cell, O(N)
per run_rules sweep, NOT the O(N^2) `apply_rule_once` drive. Ships INERT
(ground=0, interp=0) so every committed result reproduces byte-identically
(PROTOCOL §9).
"""
from __future__ import annotations
import json
import os

EPS = 1e-9  # float-equality tolerance for DISCRETE belief values (0/1/2 ...) —
#            not a tuned parameter: it separates exact-equal from not-equal.

# --------------------------------------------------------------------------- #
#  Term-tree constructors (mechanical JSON builders)
# --------------------------------------------------------------------------- #
def var(name): return {"type": "Var", "name": name}
def lit(v): return {"type": "Lit", "value": v}
def attr(node, key): return {"type": "Attr", "node": node, "key": key}
def a(name, key): return attr(var(name), key)  # attr of a bound var by name


def params(key):
    """Read a GroundParams config float (PickUnique PANICS on >1 — §12.3)."""
    return attr({"type": "PickUnique",
                 "source": {"type": "NodesOfType", "node_type": "GroundParams"}}, key)


def nbrs(cvar="c"):
    return {"type": "Neighbours", "node": var(cvar),
            "edge_type": "neighbour", "any_type": False}


def flt(pred, nvar="n", cvar="c"):
    return {"type": "Filter", "source": nbrs(cvar), "var_name": nvar, "predicate": pred}


def count(src): return {"type": "Count", "source": src}
def summ(src, value, nvar="n"): return {"type": "Sum", "source": src, "var_name": nvar, "value": value}
def exists(src, pred, nvar="n"): return {"type": "Exists", "source": src, "var_name": nvar, "predicate": pred}

def eq(x, y): return {"type": "Eq", "a": x, "b": y}
def lt(x, y): return {"type": "Lt", "a": x, "b": y}
def gt(x, y): return {"type": "Gt", "a": x, "b": y}
def gte(x, y): return {"type": "Gte", "a": x, "b": y}
def ltee(x, y): return {"type": "Lte", "a": x, "b": y}
def AND(*items): return {"type": "And", "items": list(items)}
def OR(*items): return {"type": "Or", "items": list(items)}
def NOT(x): return {"type": "Not", "arg": x}
def plus(*items): return {"type": "Plus", "items": list(items)}
def minus(x, y): return {"type": "Minus", "a": x, "b": y}
def times(*items): return {"type": "Times", "items": list(items)}
def div(x, y): return {"type": "Div", "a": x, "b": y}
def Abs(x): return {"type": "Abs", "arg": x}
def Min(*items): return {"type": "Min", "items": list(items)}
def Max(*items): return {"type": "Max", "items": list(items)}
def ite(cond, then, other): return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


# --------------------------------------------------------------------------- #
#  Reusable neighbour-sets (all LOCAL to cell c)
# --------------------------------------------------------------------------- #
def sensed_same_row():   # sensed neighbours in the same row as c
    return flt(AND(gt(a("n", "gsensed"), lit(0.5)), eq(a("n", "row"), a("c", "row"))))
def sensed_same_col():
    return flt(AND(gt(a("n", "gsensed"), lit(0.5)), eq(a("n", "col"), a("c", "col"))))
def sensed_same_row_eq():   # ... AND observing the SAME value as c
    return flt(AND(gt(a("n", "gsensed"), lit(0.5)), eq(a("n", "row"), a("c", "row")),
                   ltee(Abs(minus(a("n", "gobs"), a("c", "gobs"))), lit(EPS))))
def sensed_same_col_eq():
    return flt(AND(gt(a("n", "gsensed"), lit(0.5)), eq(a("n", "col"), a("c", "col")),
                   ltee(Abs(minus(a("n", "gobs"), a("c", "gobs"))), lit(EPS))))

def SR_contH():  # same-row FILLED contour-H neighbours (a horizontal contour to continue)
    return flt(AND(gt(a("n", "gfilled"), lit(0.5)), gt(a("n", "gcont"), lit(0.5)),
                   ltee(Abs(minus(a("n", "gcax"), lit(1.0))), lit(EPS)),
                   eq(a("n", "row"), a("c", "row"))))
def SC_contV():  # same-col FILLED contour-V neighbours
    return flt(AND(gt(a("n", "gfilled"), lit(0.5)), gt(a("n", "gcont"), lit(0.5)),
                   ltee(Abs(minus(a("n", "gcax"), lit(2.0))), lit(EPS)),
                   eq(a("n", "col"), a("c", "col"))))
def filled_surface():  # FILLED, non-contour (surface) neighbours
    return flt(AND(gt(a("n", "gfilled"), lit(0.5)), lt(a("n", "gcont"), lit(0.5))))
def filled_any():
    return flt(gt(a("n", "gfilled"), lit(0.5)))


def hval(): return div(summ(SR_contH(), a("n", "gbel")), Max(count(SR_contH()), lit(1.0)))
def vval(): return div(summ(SC_contV(), a("n", "gbel")), Max(count(SC_contV()), lit(1.0)))


def blind_unfilled_open():  # the common fill guard: blind, not yet filled, not held-open
    return [gt(params("ground"), lit(0.5)),
            lt(params("interp"), lit(0.5)),
            lt(a("c", "gsensed"), lit(0.5)),
            lt(a("c", "gfilled"), lit(0.5)),
            lt(a("c", "gambig"), lit(0.5))]


def rule(name, comment, where, effects):
    return {"name": name, "comment": comment, "match_type": "RetinaCell",
            "match": [["ret", "has_cell", "c"]], "where": where, "effects": effects}


def seteff(key, term): return ["set_attr", "c", key, {"__term__": term}]


# --------------------------------------------------------------------------- #
#  THE RULES
# --------------------------------------------------------------------------- #
def build_rules():
    rules = []

    # (1) LABEL — a SENSED cell is a contour (with an axis) iff its observation is
    # CONSTANT along one axis and DIFFERS along the other. Structural equality on
    # the OBSERVED value (no threshold, no magic number). Runs once per step,
    # reading only SENSED neighbours so the label is stable within a grounding.
    srE, srT = count(sensed_same_row_eq()), count(sensed_same_row())
    scE, scT = count(sensed_same_col_eq()), count(sensed_same_col())
    is_h = AND(gte(srT, lit(1.0)), ltee(Abs(minus(srE, srT)), lit(EPS)), lt(scE, scT))
    is_v = AND(gte(scT, lit(1.0)), ltee(Abs(minus(scE, scT)), lit(EPS)), lt(srE, srT))
    gcax_term = ite(is_h, lit(1.0), ite(is_v, lit(2.0), lit(0.0)))
    rules.append(rule(
        "gr_label",
        "A SENSED cell is labelled a contour (axis 1 = runs along the row, 2 = "
        "along the column) iff its observation is CONSTANT along that axis and "
        "DIFFERS along the perpendicular one. No magic number: exact equality on "
        "the observed value. Once per step (glabel_step < ret.step).",
        AND(gt(params("ground"), lit(0.5)),
            gt(a("c", "gsensed"), lit(0.5)),
            lt(a("c", "glabel_step"), a("ret", "step"))),
        [seteff("gcax", gcax_term),
         seteff("gcont", ite(gt(gcax_term, lit(0.5)), lit(1.0), lit(0.0))),
         seteff("glabel_step", a("ret", "step"))]))

    # (2) THE UNIFIED GROUNDING FILL — ONE rule so there is NO inter-rule race
    # (a separate surface rule could win a cell before a contour reached it). A
    # blind, unfilled, not-held-open cell fires as soon as ANY neighbour is
    # grounded, and CHOOSES, contour-first:
    #   * CONFLICT (a same-row contour-H value A AND a same-col contour-V value
    #     B != A) -> HELD OPEN: gambig=1, stay unfilled. The anti-confabulation
    #     gate: two admissible fills, invent neither.
    #   * else a same-row contour-H available -> CONTINUE it (value + axis 1);
    #   * else a same-col contour-V available -> CONTINUE it (axis 2);
    #   * else SURFACE: the mean of filled SURFACE (non-contour) neighbours.
    # Because the contour's AXIS is carried and a horizontal contour is only
    # continued to same-row cells, a 1-cell-thin contour is bridged AS a contour
    # instead of blurring to the surround mean. For a symmetric blind spot the
    # contour source is never farther than the surface source, so contour-first
    # bridges the whole span. gconf FALLS OUT of support (summed neighbour conf /
    # the number that could support) — RELATIVE decay = eccentricity fade, no
    # fixed constant.
    nSR, nSC = count(SR_contH()), count(SC_contV())
    nFS = count(filled_surface())
    hv, vv = hval(), vval()
    surf_val = div(summ(filled_surface(), a("n", "gbel")), Max(nFS, lit(1.0)))
    has_H, has_V = gte(nSR, lit(1.0)), gte(nSC, lit(1.0))
    conflict = AND(has_H, has_V, gt(Abs(minus(hv, vv)), lit(EPS)))
    has_contour = OR(has_H, has_V)
    fillable = OR(has_contour, gte(nFS, lit(1.0)))
    confH = Min(div(summ(SR_contH(), a("n", "gconf")), lit(2.0)), lit(1.0))
    confV = Min(div(summ(SC_contV(), a("n", "gconf")), lit(2.0)), lit(1.0))
    confS = Min(div(summ(filled_surface(), a("n", "gconf")), lit(4.0)), lit(1.0))
    val_term = ite(has_H, hv, ite(has_V, vv, surf_val))
    cont_term = ite(has_contour, lit(1.0), lit(0.0))
    cax_term = ite(has_H, lit(1.0), ite(has_V, lit(2.0), lit(0.0)))
    conf_term = ite(has_H, confH, ite(has_V, confV, confS))
    rules.append(rule(
        "gr_fill",
        "The unified grounding fill: contour-first (continue a contour along its "
        "carried axis), else surface (mean of filled surface neighbours), and "
        "HOLD OPEN a conflicting two-continuation surround (gambig=1, stay "
        "unfilled). One rule = no inter-rule race. gconf falls out of support.",
        AND(*blind_unfilled_open(), fillable),
        [seteff("gambig", ite(conflict, lit(1.0), lit(0.0))),
         seteff("gbel", ite(conflict, a("c", "gbel"), val_term)),
         seteff("gcont", ite(conflict, lit(0.0), cont_term)),
         seteff("gcax", ite(conflict, lit(0.0), cax_term)),
         seteff("gconf", ite(conflict, lit(0.0), conf_term)),
         seteff("gfilled", ite(conflict, lit(0.0), lit(1.0)))]))

    # (5) INTERPOLATION CONTROL — the naive baseline (graph DATA, not a Python
    # fork): adopt the mean of ALL filled neighbours, contour and surface alike,
    # with NO structure. Gated on interp>0.5, which suppresses rules 2-4. This is
    # what BLURS a contour and CONFABULATES an ambiguous surround — the thing
    # grounding must beat.
    interp_val = div(summ(filled_any(), a("n", "gbel")), Max(count(filled_any()), lit(1.0)))
    rules.append(rule(
        "gr_interp",
        "INTERPOLATION control (interp=1): mean of ALL filled neighbours, no "
        "structure. Blurs contours and confabulates ambiguity — the baseline.",
        AND(gt(params("ground"), lit(0.5)), gt(params("interp"), lit(0.5)),
            lt(a("c", "gsensed"), lit(0.5)), lt(a("c", "gfilled"), lit(0.5)),
            gte(count(filled_any()), lit(1.0))),
        [seteff("gbel", interp_val),
         seteff("gconf", Min(div(summ(filled_any(), a("n", "gconf")), lit(4.0)), lit(1.0))),
         seteff("gfilled", lit(1.0)),
         seteff("gcont", lit(0.0)),
         seteff("gcax", lit(0.0))]))

    return rules


def build():
    return {
        "id": "vision_ground",
        "version": "1.0.0",
        "depends_on": ["vision_waves"],
        "description": (
            "THE BLIND SPOT — a GROUNDED retinal field, not a sample array. The "
            "optic disc (gsensed=0, no photoreceptors, no data) is FILLED FROM "
            "the surround by grounding: a contour is bridged AS a contour (its "
            "axis is carried and propagates only along it), a consistent fill "
            "makes the hole invisible, an ambiguous surround is HELD OPEN, and "
            "the belief REVISES when the eye moves. Pure seed rules reusing "
            "vision_lateral's LOCAL Neighbours/Filter/Count/Sum machinery (O(N) "
            "per run_rules sweep, NOT the O(N^2) apply_rule_once drive). The "
            "blind-spot geometry is a STRUCTURAL construction parameter (the "
            "optic nerve must exit somewhere); the FILLING falls out, and the "
            "confidence decay is RELATIVE to surround support. Ships INERT "
            "(ground=0, interp=0) so every committed result reproduces (PROTOCOL "
            "9)."),
        "microtheory": {
            "name": "grounded_retinal_field",
            "description": (
                "Vision is a grounded field: a belief per location, filled from "
                "the surround where the sensor has no data. The blind spot proves "
                "it — a hole in the retina we do not perceive, because the field "
                "grounds the absence from what surrounds it (the edges-are-"
                "grounded-contours principle: transitive, decaying, relative "
                "grounding). Interpolation averages the hole (one invented value, "
                "blur, confabulation); grounding continues the STRUCTURE and holds "
                "genuine ambiguity open."),
        },
        "nodes": [{
            "local_id": 0,
            "type": "GroundParams",
            "attrs": {"ground": 0.0, "interp": 0.0},
        }],
        "edges": [],
        # has_cell is declared by vision_waves (our dependency) — inherited, not
        # re-declared here (a duplicate production would conflict on load).
        "productions": [],
        "rules": build_rules(),
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "vision_ground.json")
    with open(out, "w") as fh:
        json.dump(build(), fh, indent=1)
        fh.write("\n")
    print("wrote", out, "-", len(build()["rules"]), "rules")
