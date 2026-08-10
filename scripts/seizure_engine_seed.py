"""Generate the default-OFF seizure-dynamics seed for the REAL (G,Gamma) engine.

This is an AUTHORING tool (emits a seed manifest); it is NOT agent runtime.
The seed adds ONE settlement rule over a CognitiveArea lattice, expressed
entirely with EXISTING DSL arithmetic Terms (Plus/Minus/Neg/Times/Min/Max/Sum/
Neighbours/Attr/Lit). No new Rust Term. The rule is a COMBINATIONAL next-state
production: it reads each area's CURRENT `residual` (+ neighbours' current
`residual` over `projects_to`) and writes `next_residual`; the engine's native
`fold_clock_edge` commits `next_residual -> residual` at the clock edge (the
double-buffered synchronous substep). run_rules reaches a fixpoint because the
rule never mutates its own inputs within a tick (Tarski-monotone; the
down-stroke lives at the clock edge).

DEFAULT OFF: the rule matches ONLY areas carrying a `sz_managed_by` edge to a
SeizureConfig node whose `sz_enabled == 1`. Normal cognition has no such nodes
and no such edge, so the rule is INERT and normal settlement is byte-identical.

The give-dial (`give`) and the positive-feedback gain (`alpha`) are read from
the SeizureConfig node -> tunable graph data, DEFAULT alpha=0 (no positive
feedback => the lattice can only dissipate: the required good null).

Settlement per area i (all quantities read from the CURRENT buffer; `remain`
is the UN-DISSIPATED remainder that gets broadcast, so the give gates
recruitment exactly as in the reference model):
    gen_i      = alpha * min(max(0, R_i - c_gen), gen_cap)      # POSITIVE FEEDBACK (new, default off)
    acc_i      = R_i + drive_i + gen_i                          # accumulated this substep
    settled_i  = tick_i * min(budget, acc_i)                    # local dissipation sink
    shed_i     = give * tick_i * max(0, acc_i - c_gen)          # THE GIVE (shed valve)
    remain_i   = max(0, acc_i - settled_i - shed_i)             # un-dissipated remainder
    push_i     = g * tick_i * remain_i                          # broadcast the remainder out
    received_i = sum_{j~i} 0.25 * push_j                        # recruitment channel in
    next_R_i   = clip( remain_i - push_i + received_i , 0, R_max )
Because push is on `remain` (post-settle-post-shed), a high give leaves little
to broadcast (dies gracefully); give -> 0 broadcasts the whole overload
(recruits neighbours -> traveling wave). alpha = 0 => gen = 0 => the lattice can
only dissipate at any give (the good null: no seizure without positive feedback).
"""
from __future__ import annotations

import json
import os


# ---- Term-JSON builders (existing DSL Terms only) ------------------------
def var(name):
    return {"type": "Var", "name": name}


def lit(v):
    return {"type": "Lit", "value": v}


def attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def times(*items):
    return {"type": "Times", "items": list(items)}


def neg(a):
    return {"type": "Neg", "arg": a}


def tmin(*items):
    return {"type": "Min", "items": list(items)}


def tmax(*items):
    return {"type": "Max", "items": list(items)}


def neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type,
            "any_type": False}


def tsum(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name,
            "value": value}


# ---- The settlement rule -------------------------------------------------
def _remain(C, node, with_drive):
    """The un-dissipated remainder of `node` this substep (post settle+shed).

    Reads the node's CURRENT `residual` (+ its own regeneration + optional
    focal drive), then subtracts the local settlement sink and the give/shed.
    Used both for the area itself (with_drive=True) and inlined per neighbour
    inside the recruitment Sum (with_drive=False; the focal drive is brief and
    local, so neighbours' recruitment reads their residual, not a drive)."""
    give = attr(C, "give")
    alpha = attr(C, "alpha")
    budget = attr(C, "budget")
    c_gen = attr(C, "c_gen")
    gen_cap = attr(C, "gen_cap")

    R = attr(node, "residual")
    tick = attr(node, "ticking")

    gen = times(alpha, tmin(tmax(lit(0.0), minus(R, c_gen)), gen_cap))
    acc_items = [R, gen]
    if with_drive:
        acc_items.insert(1, attr(node, "drive"))
    acc = plus(*acc_items)                                 # accumulated this substep
    settled = times(tick, tmin(budget, acc))               # dissipation sink
    shed = times(give, tick, tmax(lit(0.0), minus(acc, c_gen)))   # THE GIVE / shed
    return tmax(lit(0.0), plus(acc, neg(settled), neg(shed)))     # un-dissipated remainder


def build_settle_rule():
    A = var("area")
    C = var("cfg")
    NB = var("nb")

    g = attr(C, "g")

    remain_self = _remain(C, A, with_drive=True)
    push_self = times(g, attr(A, "ticking"), remain_self)  # broadcast the remainder out

    # recruitment in: 1/4 of each neighbour's remainder-push arrives
    # (absorbing boundary -- off-lattice push is lost).
    push_nb = times(g, attr(NB, "ticking"), _remain(C, NB, with_drive=False))
    received = tsum(
        neighbours(A, "projects_to"),
        "nb",
        times(lit(0.25), push_nb),
    )

    inner = plus(remain_self, neg(push_self), received)
    next_r = tmax(lit(0.0), tmin(attr(C, "r_max"), inner))

    return {
        "name": "sz_settle_next_residual",
        "area": "scheduler",
        "order": 5,
        "latency_class": "best_effort",
        "match": [["area", "sz_managed_by", "cfg"]],
        "where": {
            "type": "Eq",
            "a": attr(C, "sz_enabled"),
            "b": lit(1.0),
        },
        "effects": [
            ["set_attr_if_different", "area", "next_residual",
             {"__term__": next_r}],
        ],
    }


def build_seed():
    return {
        "id": "seizure_dynamics",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": ["cognitive_areas"],
        "area": "scheduler",
        "description": (
            "DEFAULT-OFF tunable seizure capability for the real engine. Adds a "
            "combinational settlement rule over a CognitiveArea lattice: overload "
            "regeneration (positive feedback, gain alpha, DEFAULT 0), a give/shed "
            "valve (give-dial), local dissipation budget, and lateral "
            "broadcast/recruitment over projects_to. Writes next_residual; the "
            "engine's fold_clock_edge commits it. INERT unless an area carries a "
            "sz_managed_by edge to a SeizureConfig with sz_enabled=1 -> normal "
            "cognition byte-identical when absent/off. No new Rust Term."
        ),
        "microtheory": {
            "name": "seizure_dynamics",
            "description": (
                "un-dissipated synchronous residual as a give-failure of async "
                "settlement (glass-box, tunable, default off)"
            ),
        },
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "seed:seizure_dynamics:area-config",
                "src": {"type": "CognitiveArea", "var": "area"},
                "edge_type": "sz_managed_by",
                "tgt": {"type": "SeizureConfig", "var": "cfg"},
            },
        ],
        "rules": [build_settle_rule()],
    }


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "seizure_dynamics.json")
    seed = build_seed()
    with open(out, "w") as f:
        json.dump(seed, f, indent=1)
        f.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
