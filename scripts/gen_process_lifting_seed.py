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
    A, And, Count, Eq, Exists, Gt, L, Lte, Lt, Max, N, Not, OFFLINE_AREA,
    PAntiUnifyWitness, PFingerprint, PLiftInstantiate, PSupport, StringConcat, T, V, Vec,
    is_none, not_none, policy_on, productions, rule,
)

SEED_ID = "process_lifting"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def source_family_rule():
    witness = PAntiUnifyWitness(Vec(A("a", "expr_tree"), A("b", "expr_tree")))
    pair = Vec(V("a"), V("b"))
    sizes = Vec(A("da", "size"), A("db", "size"))
    already = Exists(N("agent", "has_lifted_process_family"), "old",
                     Eq(A("old", "source_pair"), pair))
    return rule(
        "pl_mint_witnessed_family", OFFLINE_AREA, 30,
        "Retain a structural family only from two distinct-domain source schemas and their exact anti-unification witnesses.",
        [["agent", "has_process_lifting_policy", "pol"],
         ["agent", "has_process_schema", "a"], ["agent", "has_process_schema", "b"],
         ["agent", "has_process_domain", "da"], ["agent", "has_process_domain", "db"]],
        And(policy_on(), Eq(A("pol", "enabled"), L(1.0)), Lt(V("a"), V("b")),
            Lt(Count(N("agent", "has_lifted_process_family")), A("pol", "max_sources")),
            Eq(A("a", "domain"), A("da", "name")), Eq(A("b", "domain"), A("db", "name")),
            Gt(A("da", "size"), L(1)), Gt(A("db", "size"), L(1)),
            Not(Eq(A("da", "size"), A("db", "size"))),
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
            "source_sizes": T(sizes), "max_source_size": T(Max(A("da", "size"), A("db", "size"))),
            "provenance": "anti_unify_witness", "effect_evaluation": "unverified_template",
        }],
         ["add_edge", "agent", "has_lifted_process_family", "f", {}],
         ["add_edge", "f", "has_source_schema", "a", {}],
         ["add_edge", "f", "has_source_schema", "b", {}]],
        batch=False)


def target_instance_rule():
    params = PLiftInstantiate(A("f", "template"), A("f", "source_sizes"), A("d", "size"))
    fingerprint = PFingerprint(params, A("d", "probes"))
    already = Exists(N("f", "has_lifted_instance"), "old",
                     Eq(A("old", "domain"), A("d", "name")))
    return rule(
        "pl_instantiate_unseen_size", OFFLINE_AREA, 31,
        "Instantiate only size-tracking witnesses on a larger unseen domain, then require an exact native effect fingerprint there.",
        [["agent", "has_process_lifting_policy", "pol"],
         ["agent", "has_lifted_process_family", "f"],
         ["agent", "has_process_domain", "d"]],
        And(policy_on(), Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("pol", "unseen_size_enabled"), L(1.0)),
            Eq(A("f", "status"), L("witnessed_candidate")),
            Eq(A("f", "domain_kind"), A("d", "kind")),
            Gt(A("d", "size"), A("f", "max_source_size")),
            Lte(A("d", "size"), A("pol", "max_size")),
            not_none(A("d", "probes")), not_none(fingerprint),
            Not(Eq(fingerprint, A("d", "identity_fingerprint"))),
            Not(already)),
        [["add_node", "s", "ProcessSchema", {
            "kind": T(L("permutation")), "domain": T(A("d", "name")),
            "domain_kind": T(A("d", "kind")), "name": T(StringConcat(L("lifted:"), A("f", "name"), L(":"), A("d", "name"))),
            "params": T(params), "fingerprint": T(fingerprint), "support": T(PSupport(params)),
            "cost": T(L(1.0)), "provenance": "lifted_from_witness", "operator": "lifted_commutator",
            "expr_tree": T(A("f", "template")), "status": "active", "invented": 1,
            "fingerprint_checked": 1, "dedup_checked": 1, "indexed": 1,
            "effect_evaluation": "exact:native_lift_on_target_probes",
            "verification_receipt": "native_target_domain_fingerprint",
            "model_epoch": T(A("d", "model_epoch")), "frame_epoch": T(A("d", "frame_epoch")),
            "probe_epoch": T(A("d", "probe_epoch")),
        }],
         ["add_edge", "agent", "has_process_schema", "s", {}],
         ["add_edge", "d", "has_held_process", "s", {}],
         ["add_edge", "f", "has_lifted_instance", "s", {}],
         ["add_edge", "s", "lifted_from_family", "f", {}]],
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
            "max_size": 16.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_process_lifting_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, [
            ("Agent", "has_process_lifting_policy", "ProcessLiftingPolicy"),
            ("Agent", "has_lifted_process_family", "LiftedProcessFamily"),
            ("LiftedProcessFamily", "has_source_schema", "ProcessSchema"),
            ("LiftedProcessFamily", "has_lifted_instance", "ProcessSchema"),
            ("ProcessSchema", "lifted_from_family", "LiftedProcessFamily"),
        ]),
        "rules": [source_family_rule(), target_instance_rule()],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
