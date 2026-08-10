#!/usr/bin/env python3
"""ONE-OFF AUTHORING SCRIPT (deletable; not agent runtime) — EMITS the graph
data for seed block 197000, `seeds/dissipation_inference.json`.

The seed is the SHARED DISSIPATIVE-RELAXATION / MAP-INFERENCE dynamics: a single
`batch` rule `df_relax` that settles a field of `FieldCell` nodes toward the
minimum of the quadratic energy E(x)=lam*Σ(x-obs)^2 + Σ_edges(x-x_j)^2 by
red-black exact integer coordinate descent. Read as physics it is a 2nd-law
dissipative relaxation; read as cognition it is MAP inference over a Gaussian
MRF (denoising / filling-in). NO Rust, NO new Term — Sum/Neighbours/Count/IDiv/
Plus/Times/Minus/IfThenElse/Gt/Eq/And/Attr/Var/Lit only. Prereg:
DISSIPATION_IS_INFERENCE_PREREG.md.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


# --- tiny Term-tree helpers (pure JSON emitters) ---
def var(n):            return {"type": "Var", "name": n}
def lit(v):            return {"type": "Lit", "value": v}
def attr(n, k):        return {"type": "Attr", "node": var(n), "key": k}
def plus(*xs):         return {"type": "Plus", "items": list(xs)}
def times(*xs):        return {"type": "Times", "items": list(xs)}
def minus(a, b):       return {"type": "Minus", "a": a, "b": b}
def idiv(a, b):        return {"type": "IDiv", "a": a, "b": b}
def eq(a, b):          return {"type": "Eq", "a": a, "b": b}
def gt(a, b):          return {"type": "Gt", "a": a, "b": b}
def and_(*xs):         return {"type": "And", "items": list(xs)}
def nbrs(n, et):       return {"type": "Neighbours", "node": var(n),
                               "edge_type": et, "any_type": False}
def count(src):        return {"type": "Count", "source": src}
def sum_(src, v, val): return {"type": "Sum", "source": src,
                               "var_name": v, "value": val}
def ite(c, t, o):      return {"type": "IfThenElse", "cond": c, "then": t,
                               "other": o}


def build():
    # num = lam*obs_i + Σ_{j∈adj(i)} val_j
    num = plus(times(attr("f", "lam"), attr("c", "obs")),
               sum_(nbrs("c", "adj"), "j", attr("j", "val")))
    # den = lam + deg_i
    den = plus(attr("f", "lam"), count(nbrs("c", "adj")))
    # cand = round-to-nearest integer argmin = IDiv(2*num + den, 2*den)
    cand = idiv(plus(times(lit(2.0), num), den),
                times(lit(2.0), den))
    # descent : reflected ascent, selected by RelaxField.sign
    new_val = ite(gt(attr("f", "sign"), lit(0.0)),
                  cand,
                  minus(times(lit(2.0), attr("c", "val")), cand))

    rule = {
        "name": "df_relax",
        "batch": True,
        "order": 0,
        "match": [["f", "field_cell", "c"]],
        "where": and_(
            eq(attr("f", "enabled"), lit(1.0)),
            eq(attr("c", "par"), attr("f", "phase")),
        ),
        "effects": [["set_attr", "c", "val", {"__term__": new_val}]],
    }

    seed = {
        "id": "dissipation_inference",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "area": "field",
        "description": (
            "SHARED DISSIPATIVE RELAXATION == MAP INFERENCE (block 197000). ONE "
            "integer dynamics, two frames differing only by a relabel. A field "
            "of FieldCell{val,obs,par} on 4-connected `adj` edges settles toward "
            "the minimum of E(x)=lam*Σ(x-obs)^2 + Σ_edges(x-x_j)^2 by RED-BLACK "
            "EXACT integer coordinate descent: the single `batch` rule df_relax "
            "updates only cells with par==phase, each to its conditional integer "
            "argmin cand=IDiv(2*(lam*obs+Σnbr val)+den, 2*den), den=lam+deg. "
            "Non-adjacent same-colour cells make one half-sweep exact block "
            "coordinate descent, so the integer energy is monotone non-increasing "
            "to a fixed point (PHYSICS: 2nd-law dissipation; the free energy "
            "decreases, entropy is produced). RELABELED (val->MAP estimate, "
            "obs->noisy observation y, lam->likelihood precision, E->neg-log-"
            "posterior) the SAME run is MAP inference over a Gaussian MRF: the "
            "fixed point IS the MAP percept (COGNITION: denoising / filling-in). "
            "RelaxField.sign=-1 flips the SAME rule to reflected ascent "
            "(val<-2*val-cand), forcing E UP (anti-dissipative) -- and the "
            "percept recovery then diverges: break-one-breaks-both. OFF by "
            "default: fires only when a RelaxField{enabled=1} hub exists, which "
            "the measure adapter creates on opt-in; absent it, every existing "
            "path is byte-identical (FieldCell/RelaxField appear in no other "
            "graph). NO Rust, NO new Term."
        ),
        "microtheory": {
            "name": "dissipation_inference",
            "description": (
                "Dissipative relaxation of a field to the minimum of a quadratic "
                "energy IS MAP inference over a Gaussian MRF; the two are one "
                "integer computation read in two frames (the Gibbs distribution "
                "is the posterior; equilibrium is the MAP percept)."
            ),
        },
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "seed:dissipation_inference:field-cell",
                "src": {"type": "RelaxField", "var": "f"},
                "edge_type": "field_cell",
                "tgt": {"type": "FieldCell", "var": "c"},
            },
            {
                "provenance": "seed:dissipation_inference:adjacency",
                "src": {"type": "FieldCell", "var": "a"},
                "edge_type": "adj",
                "tgt": {"type": "FieldCell", "var": "b"},
            },
        ],
        "rules": [rule],
    }
    return seed


def main():
    seed = build()
    out = os.path.join(ROOT, "seeds", "dissipation_inference.json")
    with open(out, "w") as fh:
        json.dump(seed, fh, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
