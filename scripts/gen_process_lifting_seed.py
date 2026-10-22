#!/usr/bin/env python3
"""Author the guarded graph-level process lifting seed (P10.02)."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Eq, Exists, L, Lt, N, Not, OFFLINE_AREA, PAntiUnifyWitness,
    StringConcat, T, V, Vec, policy_on, productions, rule,
)

SEED_ID = "process_lifting"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def source_family_rule():
    witness = PAntiUnifyWitness(Vec(A("a", "expr_tree"), A("b", "expr_tree")))
    pair = Vec(V("a"), V("b"))
    already = Exists(N("agent", "has_lifted_process_family"), "old",
                     Eq(A("old", "source_pair"), pair))
    return rule(
        "pl_mint_witnessed_family", OFFLINE_AREA, 30,
        "Retain a structural family only from two distinct-domain source schemas and their exact anti-unification witnesses.",
        [["agent", "has_process_lifting_policy", "pol"],
         ["agent", "has_process_schema", "a"], ["agent", "has_process_schema", "b"]],
        And(policy_on(), Eq(A("pol", "enabled"), L(1.0)), Lt(V("a"), V("b")),
            Not(Eq(A("a", "domain"), A("b", "domain"))),
            Eq(A("a", "kind"), A("b", "kind")),
            Eq(A("a", "domain_kind"), A("b", "domain_kind")),
            Eq(A("a", "operator"), L("commutator")),
            Eq(A("b", "operator"), L("commutator")),
            Not(Eq(A("a", "expr_tree"), L(None))),
            Not(Eq(A("b", "expr_tree"), L(None))), Not(already)),
        [["add_node", "f", "LiftedProcessFamily", {
            "status": "witnessed_candidate", "kind": T(A("a", "kind")),
            "domain_kind": T(A("a", "domain_kind")),
            "template": T(witness), "witness_count": 2,
            "source_pair": T(pair), "source_domains": T(Vec(A("a", "domain"), A("b", "domain"))),
            "provenance": "anti_unify_witness", "effect_evaluation": "unverified_template",
        }],
         ["add_edge", "agent", "has_lifted_process_family", "f", {}],
         ["add_edge", "f", "has_source_schema", "a", {}],
         ["add_edge", "f", "has_source_schema", "b", {}]],
        batch=False)


def build():
    return {
        "id": SEED_ID, "version": "1.0.0", "depends_on": ["process_schema"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "Retain witnessed parametric process families without treating a template as an executable effect.",
        "microtheory": {"name": SEED_ID,
                         "description": "Lift process structure from explicit source witnesses; verify every instance."},
        "nodes": [{"local_id": 0, "type": "ProcessLiftingPolicy", "attrs": {
            "name": "core_process_lifting_policy", "enabled": 0.0,
            "max_sources": 8.0, "max_bindings": 64.0, "unseen_size_enabled": 0.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_process_lifting_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, [
            ("Agent", "has_process_lifting_policy", "ProcessLiftingPolicy"),
            ("Agent", "has_lifted_process_family", "LiftedProcessFamily"),
            ("LiftedProcessFamily", "has_source_schema", "ProcessSchema"),
        ]),
        "rules": [source_family_rule()],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
