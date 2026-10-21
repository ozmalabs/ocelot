#!/usr/bin/env python3
"""Author the default-off A2.2 decomposition completion rules."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from gen_capability_collapse_seed import A, And, Eq, L, N, Not, Or, T


def Exists(source, var, predicate):
    return {"type": "Exists", "source": source, "var_name": var, "predicate": predicate}


def numeric(var, key):
    return {"type": "Plus", "items": [A(var, key), L(0)]}


def valid_child(child, parent):
    return And(
        Eq(A(child, "completion_status"), L("completed")),
        Eq(numeric(child, "completion_verified"), L(1)),
        Eq(numeric(child, "model_epoch"), numeric(parent, "model_epoch")),
        Eq(numeric(child, "decomposition_epoch"), numeric(parent, "decomposition_epoch")),
    )


def covered_key(parent="ax"):
    return Exists(N(parent, "decomposes_into"), "c", And(
        valid_child("c", parent),
        Exists(N("c", "requires_key"), "ck",
               Eq(A("ck", "name"), A("k", "name"))),
    ))


def completion_rule():
    missing = Exists(N("ax", "requires_key"), "k", Not(covered_key()))
    outstanding = Exists(N("ax", "decomposes_into"), "c", And(
        Exists(N("c", "requires_key"), "ck",
               Exists(N("ax", "requires_key"), "rk",
                      Eq(A("ck", "name"), A("rk", "name")))),
        Not(valid_child("c", "ax")),
    ))
    return {
        "name": "dc_completion_witness_settle_parent",
        "batch": False,
        "comment": "Settle parent saturation and decomposition impasse only with current verified child coverage and no outstanding required child.",
        "match": [["agent", "has_decomposition_completion_policy", "pol"],
                  ["mi", "needs_decomposition", "ax"]],
        "where": And(Eq(numeric("pol", "enabled"), L(1)),
                      Not(missing), Not(outstanding),
                      Not(Eq(A("mi", "completion_witness"), L(1)))),
        "effects": [["set_attr", "ax", "pre_completion_saturation", T(A("ax", "saturation"))],
                    ["set_attr", "ax", "saturation", 1.0],
                    ["set_attr", "ax", "completion_witness", 1],
                    ["set_attr", "mi", "completion_witness", 1],
                    ["set_attr", "mi", "completion_model_epoch", T(numeric("ax", "model_epoch"))],
                    ["set_attr", "mi", "completion_decomposition_epoch", T(numeric("ax", "decomposition_epoch"))],
                    ["set_attr", "mi", "resolved", True],
                    ["set_attr", "mi", "outcome", "decomposition_completed"]],
    }


def invalid_coverage_conditions():
    missing = Exists(N("ax", "requires_key"), "k", Not(covered_key()))
    outstanding = Exists(N("ax", "decomposes_into"), "c", And(
        Exists(N("c", "requires_key"), "ck",
               Exists(N("ax", "requires_key"), "rk",
                      Eq(A("ck", "name"), A("rk", "name")))),
        Not(valid_child("c", "ax")),
    ))
    return missing, outstanding


def invalidate_rule():
    missing, outstanding = invalid_coverage_conditions()
    return {
        "name": "dc_completion_witness_invalidate_stale_epoch",
        "batch": False,
        "comment": "Invalidate a persisted witness and reopen its impasse when either parent epoch changes.",
        "match": [["agent", "has_decomposition_completion_policy", "pol"],
                  ["mi", "needs_decomposition", "ax"]],
        "where": And(Eq(numeric("pol", "enabled"), L(1)),
                      Eq(numeric("mi", "completion_witness"), L(1)),
                      Not(Eq(numeric("mi", "completion_model_epoch"), numeric("ax", "model_epoch")))),
        "effects": [["set_attr", "mi", "completion_witness", 0],
                    ["set_attr", "ax", "completion_witness", 0],
                    ["set_attr", "ax", "saturation", T(A("ax", "pre_completion_saturation"))],
                    ["set_attr", "mi", "resolved", False],
                    ["set_attr", "mi", "outcome", "decomposition_reopened"]],
    }


def invalidate_decomposition_epoch_rule():
    rule = invalidate_rule()
    rule["name"] = "dc_completion_witness_invalidate_stale_decomposition_epoch"
    rule["where"] = And(Eq(numeric("pol", "enabled"), L(1)),
                         Eq(numeric("mi", "completion_witness"), L(1)),
                         Not(Eq(numeric("mi", "completion_decomposition_epoch"), numeric("ax", "decomposition_epoch"))))
    return rule


def invalidate_coverage_rule():
    missing, outstanding = invalid_coverage_conditions()
    return {
        "name": "dc_completion_witness_invalidate_changed_coverage",
        "batch": False,
        "comment": "Reopen and restore pre-completion saturation if current required-key coverage is lost or a required child becomes outstanding.",
        "match": [["agent", "has_decomposition_completion_policy", "pol"],
                  ["mi", "needs_decomposition", "ax"]],
        "where": And(Eq(numeric("pol", "enabled"), L(1)),
                      Eq(numeric("mi", "completion_witness"), L(1)),
                      Or(missing, outstanding)),
        "effects": [["set_attr", "mi", "completion_witness", 0],
                    ["set_attr", "ax", "completion_witness", 0],
                    ["set_attr", "ax", "saturation", T(A("ax", "pre_completion_saturation"))],
                    ["set_attr", "mi", "resolved", False],
                    ["set_attr", "mi", "outcome", "decomposition_reopened"]],
    }


def build():
    productions = [("Agent", "has_decomposition_completion_policy", "DecompositionCompletionPolicy"),
                   ("Impasse", "needs_decomposition", "CapabilityAxis"),
                   ("CapabilityAxis", "requires_key", "CapKey"),
                   ("CapabilityAxis", "decomposes_into", "CapabilityAxis")]
    return {
        "id": "decomposition_completion", "version": "1.0.0", "depends_on": [],
        "description": "Opt-in verified, epoch-scoped completion witnesses for decomposed parent capability axes.",
        "microtheory": {"name": "decomposition_completion", "description": "Settle decomposition parents only on verified current-epoch coverage."},
        "nodes": [{"local_id": 0, "type": "DecompositionCompletionPolicy", "attrs": {"enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_decomposition_completion_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:decomposition_completion:{edge}", "src": {"type": src, "var": "src"}, "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in productions],
        "rules": [invalidate_rule(), invalidate_decomposition_epoch_rule(), invalidate_coverage_rule(), completion_rule()],
    }


if __name__ == "__main__":
    (ROOT / "seeds" / "decomposition_completion.json").write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
