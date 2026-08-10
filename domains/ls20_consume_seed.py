"""ls20_consume_seed — RUNG 225000: the FLASH-CONSUME MARKING as graph rules.

Folds 223000's flash onset localisation onto 224000's object-permanence tracker to
close the trail/consume residual. The flash LOCATION decision is 223's fg_pick_flash
(reused, not duplicated here); this seed adds only the graph-held CONSUME MODEL: the
discovered trail value T (a ConsumeHypothesis on the game), minted/confirmed/revised
by observation exactly as ls20_percell's pc_mint/pc_confirm/pc_revise grow the shift
Hypothesis. The adapter reads the attended flash location (fg_pick_flash) + the
discovered T (this seed) and renders the marking mechanically -- the same split
224000 uses for the translate (shift Hypothesis in graph; render in Python).

  cm_mint_consume    -- first observed trail value with no ConsumeHypothesis yet ->
                        mint one carrying the DISCOVERED value T (from the adapter-
                        stamped obs_consume_value perception fact).
  cm_confirm_consume -- re-observed the SAME value -> conf += 1 (compress).
  cm_revise_consume  -- observed a DIFFERENT value -> revise T (the trail colour
                        can change; the model tracks it, never hardcodes it).

The DECISION "which cells are consumed" is the flash localisation (fg_pick_flash,
graph) intersected with the tracker's VACATED set (224, graph shift); the VALUE is
this ConsumeHypothesis (graph); the marking RENDER is mechanical adapter I/O. There
is NO consume table -- the value is minted from observation, the location from the
flash. Guarded on consume_on==1 (default-OFF, byte-identical otherwise), the arm,
and the consume_obs phase (distinct from every pc_* / attend_flash phase). No Rust,
no new Term -- ordinary match+where+effect rules.
"""
from __future__ import annotations

import json
from pathlib import Path


def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def Not(a):      return {"type": "Not", "arg": a}
def Plus(a, b):  return {"type": "Plus", "items": [a, b]}
def T(term):     return {"__term__": term}


def Neigh(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}


def Exists(source, var="_x"):
    return {"type": "Exists", "source": source, "var_name": var,
            "predicate": {"type": "Lit", "value": True}}


def _on():
    """Guard: consume modelling ON for this game AND the 222000 Percell arm."""
    return And(Eq(A("g", "consume_on"), L(1.0)), Eq(A("g", "arm"), L("percell")))


def _phase():
    return Eq(A("g", "phase"), L("consume_obs"))


def _has_value():
    """A real trail value was observed this step (obs_consume_value != 0)."""
    return Not(Eq(A("g", "obs_consume_value"), L(0.0)))


def _rules():
    rules = []

    # -- MINT: first observed trail value, no ConsumeHypothesis yet ---------------
    rules.append({
        "name": "cm_mint_consume",
        "comment": "RESIDUAL->MODEL: a consume was observed (obs_consume_value != 0) "
                   "and there is no ConsumeHypothesis yet -> mint one carrying the "
                   "DISCOVERED trail value T. add_node_if_absent guards a double-mint.",
        "match": [["g", "has_consume_state", "cs"]],  # single hub edge -> fires once
        "where": And(_on(), _phase(), _has_value(),
                     Not(Exists(Neigh(V("g"), "has_consume"), "h"))),
        "effects": [["add_node_if_absent", "hyp", "ConsumeHypothesis",
                     {"value": T(A("g", "obs_consume_value")), "conf": 1.0,
                      "kind": "trail_value"}],
                    ["add_edge", "g", "has_consume", "hyp"]],
    })

    # -- CONFIRM: re-observed the same trail value -> compress (conf += 1) --------
    rules.append({
        "name": "cm_confirm_consume",
        "comment": "RESIDUAL->COMPRESS: observed value == held T -> conf += 1.",
        "match": [["g", "has_consume", "h"]],
        "where": And(_on(), _phase(), _has_value(),
                     Eq(A("h", "value"), A("g", "obs_consume_value"))),
        "effects": [["set_attr", "h", "conf", T(Plus(A("h", "conf"), L(1.0)))]],
    })

    # -- REVISE: observed a different trail value -> track it (never hardcode) ----
    rules.append({
        "name": "cm_revise_consume",
        "comment": "RESIDUAL->REVISE: observed value != held T -> revise T to the "
                   "observed trail value (the trail colour can change; tracked).",
        "match": [["g", "has_consume", "h"]],
        "where": And(_on(), _phase(), _has_value(),
                     Not(Eq(A("h", "value"), A("g", "obs_consume_value")))),
        "effects": [["set_attr", "h", "value", T(A("g", "obs_consume_value"))],
                    ["set_attr", "h", "conf", 1.0]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "ls20_consume",
        "version": "1.0.0",
        "depends_on": ["ls20_flash"],
        "area": "retina",
        "description": (
            "ls20 FLASH-CONSUME MARKING (block 225000): folds 223000's flash onset "
            "localisation onto 224000's object-permanence tracker to close the trail/"
            "consume residual. The flash LOCATION is 223's fg_pick_flash (reused); "
            "this seed adds the graph-held CONSUME MODEL -- a ConsumeHypothesis "
            "carrying the DISCOVERED trail value T, minted/confirmed/revised by "
            "observation (cm_mint/cm_confirm/cm_revise) exactly as pc_* grow the "
            "shift Hypothesis. The consumed-cell SET = the flash localisation "
            "(fg_pick_flash) intersected with the tracker's VACATED footprint (224); "
            "the VALUE is this ConsumeHypothesis; the marking render is mechanical "
            "adapter I/O -- the same split 224 uses for the translate. NO consume "
            "table: value minted from observation, location from the flash. Guarded "
            "on consume_on==1 (default-OFF, byte-identical otherwise), the arm, and "
            "the consume_obs phase. No Rust; reuses the ls20_flash + ls20_percell "
            "machinery."),
        "microtheory": {
            "name": "ls20_consume",
            "description": "A move drops/consumes cells (a trail); the flash "
                           "localises WHERE, the discovered ConsumeHypothesis "
                           "supplies WHAT, the tracker's vacated set supplies WHICH.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = (Path(path) if path else
         Path(__file__).resolve().parent.parent / "seeds" / "ls20_consume.json")
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
