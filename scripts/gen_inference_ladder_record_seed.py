#!/usr/bin/env python3
"""Generate the read-only inference-ladder winner recorder seed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREA = "inference_ladder_record"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return {"type": "Not", "arg": Eq(a, b)}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Count(source): return {"type": "Count", "source": source}
def N(var, edge): return {"type": "Neighbours", "node": V(var), "edge_type": edge, "any_type": False}


def rule(name, where, winner):
    return {"name": name, "area": AREA, "order": 20,
            "latency_class": "hard_realtime",
            "match": [["agent", "observed", "obs"]],
            "where": where,
            "effects": [["set_attr", "obs", "ladder_winner", winner]]}


def build():
    no_gen = Eq(Count(N("obs", "gen_minted")), L(0))
    return {
        "id": "inference_ladder_record", "version": "1.0.0",
        "self_load_only": True, "depends_on": ["shape_decode_loop"], "area": AREA,
        "description": "SLO readout that records which existing inference rung explained an Observation, without changing inference decisions.",
        "microtheory": {"name": AREA, "description": "One-shot auditable inference winner labels."},
        "nodes": [], "edges": [],
        "productions": [{
            "provenance": "seed:inference_ladder_record:observed:Agent:Observation",
            "src": {"type": "Agent", "var": "src"}, "edge_type": "observed",
            "tgt": {"type": "Observation", "var": "tgt"}}],
        "rules": [
            rule("ilr_gen_linear", {"type": "And", "items": [
                Eq(A("obs", "status"), L("recognized_transformed")),
                Eq(A("obs", "ladder_winner"), L(None)),
                {"type": "Exists", "source": N("obs", "gen_minted"), "var_name": "g", "predicate": L(True)}]}, "gen_linear"),
            rule("ilr_dim_grain", {"type": "And", "items": [
                Eq(A("obs", "status"), L("recognized_transformed")),
                Eq(A("obs", "ladder_winner"), L(None)), no_gen,
                Gt(A("obs", "dim_grain"), L(0))]}, "dim_grain"),
            rule("ilr_dim", {"type": "And", "items": [
                Eq(A("obs", "status"), L("recognized_transformed")),
                Eq(A("obs", "ladder_winner"), L(None)), no_gen,
                {"type": "Or", "items": [Eq(A("obs", "dim_grain"), L(None)), Eq(A("obs", "dim_grain"), L(0))]}]}, "dim"),
            rule("ilr_quantum", {"type": "And", "items": [
                Eq(A("obs", "status"), L("minted")),
                Eq(A("obs", "ladder_winner"), L(None)), no_gen]}, "quantum"),
        ],
    }


def main():
    (ROOT / "seeds" / "inference_ladder_record.json").write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
