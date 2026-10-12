#!/usr/bin/env python3
"""Emit seeds/aperture_minting.json -- MINTING AT APERTURE and REFINEMENT ALONG IT.

RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md WP1; design MINTING_AT_APERTURE.md.

Two rules, both opt-in per observer (`mint_at_aperture == 1`) or per axis pair:

* `am_mint_at_aperture` -- an observer whose projected decode settled with a
  NON-EMPTY residual mints a CapabilityAxis that INHERITS ITS APERTURE: the
  dimensions it resolved (`resolves`), its `grain`, the frame's `dim_types`, and
  the projected residual it was formed from. A coarse observer is not inventing
  detail -- the mint claims only what it saw at that grain ("you cannot mint
  finer than your grain"). Content-keyed (`add_node_if_absent` on source +
  aperture + residual), so two observers at the same aperture seeing the same
  thing share one axis.

* `am_refine_along_aperture` -- the intensive axis, made a relation. Axis F
  REFINES axis C iff C's aperture is a strict subset of F's AND F's minted
  residual, projected onto C's aperture (unresolved slots collapse to the
  same constant the observer projection uses), equals C's minted residual
  exactly (as sorted relation lists). Refinement is then movement along the
  aperture axis, not a contradiction or a duplicate. Applies to ANY two mints
  carrying WP1 provenance (sd-loop mints record their full-resolution
  dim_types), so a coarse aperture mint links to a later fine sd-loop mint of
  the same thing.

No guard elsewhere reads these; the seed is inert unless an observer opts in
or two provenance-carrying axes exist.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds/aperture_minting.json"
DOT = "\u00b7"


def V(n):
    return {"type": "Var", "name": n}


def A(n, k):
    return {"type": "Attr", "node": V(n), "key": k}


def L(v):
    return {"type": "Lit", "value": v}


def T(t):
    return {"__term__": t}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def nonnull(x):
    return {"type": "Not", "arg": eq(x, L(None))}


def count(x):
    return {"type": "Count", "source": x}


def project(sig, dim_types, aperture):
    """Each relation's slots outside `aperture` collapse to the observer
    projection's constant -- the same quotient seeds/observer_aperture.json
    applies."""
    return {"type": "MapList", "source": sig, "var_name": "rel",
            "value": {"type": "ZipWith", "a": V("rel"), "b": dim_types, "a_name": "slot", "b_name": "dt",
                      "value": {"type": "IfThenElse",
                                "cond": {"type": "In", "member": V("dt"), "container": aperture},
                                "then": V("slot"), "other": L(DOT)}}}


# An observer holding no parts decodes against an empty scope: ShapeDecode
# returns None, and the whole projected percept is unexplained.
RESIDUAL = {"type": "IfThenElse", "cond": eq(A("pv", "ap_residual"), L(None)),
            "then": A("pv", "signature"), "other": A("pv", "ap_residual")}

MINT = {
    "name": "am_mint_at_aperture",
    "comment": "An observer that opted in (mint_at_aperture==1) and whose projected decode SETTLED at the current scope (pv.ap_seen == obs.ap_scope_n, the same settled test ap_decode_percept uses) with a non-empty residual mints a CapabilityAxis that inherits its aperture. Content-keyed: source+observer-independent aperture+residual is the dedup key.",
    "match": [["obs", "projected", "pv"], ["obs", "perceives", "sh"]],
    "where": {"type": "And", "items": [
        eq(A("obs", "mint_at_aperture"), L(1)),
        eq(A("pv", "kind"), L("percept")),
        eq(A("pv", "of_name"), A("sh", "name")),
        eq(A("pv", "ap_gen"), A("obs", "ap_gen")),
        eq(A("pv", "ap_seen"), A("obs", "ap_scope_n")),
        {"type": "Gt", "a": count(RESIDUAL), "b": L(0)},
        {"type": "Not", "arg": eq(A("pv", "aperture_minted"), L(1))},
    ]},
    "effects": [
        ["add_node_if_absent", "axis", "CapabilityAxis", {
            "source": "aperture_mint",
            "minted_aperture": T(A("obs", "resolves")),
            "minted_dim_types": T(A("sh", "dim_types")),
            "minted_from_signature": T({"type": "Sort", "seq": RESIDUAL}),
        }],
        ["set_attr", "axis", "is_axis", 1.0],
        ["set_attr", "axis", "induced", 1.0],
        ["set_attr", "axis", "from_observation", 1.0],
        ["set_attr", "axis", "minted_grain", T(A("obs", "grain"))],
        ["set_attr", "axis", "minted_by_observer", T(A("obs", "name"))],
        ["set_attr", "axis", "minted_of", T(A("pv", "of_name"))],
        ["add_edge", "pv", "minted", "axis"],
        ["set_attr", "pv", "aperture_minted", 1],
    ],
}

# C is coarser than F; both carry WP1 provenance.
STRICT_SUBSET = {"type": "And", "items": [
    eq(count({"type": "Difference", "a": A("c", "minted_aperture"), "b": A("f", "minted_aperture")}), L(0)),
    {"type": "Gt", "a": count({"type": "Difference", "a": A("f", "minted_aperture"), "b": A("c", "minted_aperture")}), "b": L(0)},
]}
REFINE = {
    "name": "am_refine_along_aperture",
    "comment": "Axis f refines axis c iff c's aperture is a strict subset of f's and f's minted residual projected onto c's aperture equals c's minted residual exactly (sorted). Same frame typing required. Adds f -refines_at_aperture-> c once.",
    "match": [["pf", "minted", "f"], ["pc", "minted", "c"]],
    "where": {"type": "And", "items": [
        nonnull(A("f", "minted_aperture")), nonnull(A("c", "minted_aperture")),
        nonnull(A("f", "minted_from_signature")), nonnull(A("c", "minted_from_signature")),
        eq(A("f", "minted_dim_types"), A("c", "minted_dim_types")),
        STRICT_SUBSET,
        eq({"type": "Sort", "seq": project(A("f", "minted_from_signature"), A("f", "minted_dim_types"), A("c", "minted_aperture"))},
           {"type": "Sort", "seq": project(A("c", "minted_from_signature"), A("c", "minted_dim_types"), A("c", "minted_aperture"))}),
        {"type": "Not", "arg": {"type": "In", "member": V("c"),
                                "container": {"type": "Neighbours", "node": V("f"), "edge_type": "refines_at_aperture"}}},
    ]},
    "effects": [["add_edge", "f", "refines_at_aperture", "c"]],
}


def main() -> int:
    seed = {
        "id": "aperture_minting",
        "version": "1.0.0",
        "self_load_only": True,
        "comment": __doc__,
        "depends_on": ["observer_aperture", "shape_decode_loop"],
        "productions": [
            {"provenance": "seed:aperture_minting:minted", "src": {"type": "ObservedShape", "var": "pv"},
             "edge_type": "minted", "tgt": {"type": "CapabilityAxis", "var": "axis"}},
            {"provenance": "seed:aperture_minting:refines", "src": {"type": "CapabilityAxis", "var": "f"},
             "edge_type": "refines_at_aperture", "tgt": {"type": "CapabilityAxis", "var": "c"}},
        ],
        "rules": [MINT, REFINE],
    }
    OUT.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
