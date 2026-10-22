#!/usr/bin/env python3
"""Generate the opt-in P14 proof-carrying process adoption gate."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import (A, And, Eq, Exists, In, L, N, Not, OFFLINE_AREA, Or,
                              V, policy_on, productions, rule)  # noqa: E402

SEED_ID = "process_proof_adoption"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def valid_proof(law="law", proof="proof", schema="s", domain="d", requirement="req"):
    return And(
        Eq(A(law, "status"), L("checked")),
        Eq(A(law, "proven"), L(1)),
        Eq(A(law, "claim"), A(requirement, "required_law")),
        Eq(A(law, "family"), A(domain, "name")),
        Eq(A(law, "proof_kind"), L("native_structural_rule")),
        Eq(A(law, "proof_rule"), L("parity_commutator_even_v1")),
        Eq(A(proof, "status"), L("checked")),
        Eq(A(proof, "checker"), L("process_laws_seed_v1")),
        Eq(A(proof, "rule"), L("parity_commutator_even_v1")),
        Eq(A(proof, "family"), A(domain, "name")),
        Eq(A(proof, "family_digest"), A(domain, "family_digest")),
        Eq(A(proof, "model_digest"), A(domain, "model_digest")),
        Eq(A(proof, "family_epoch"), A(domain, "source_epoch")),
        Eq(A(proof, "process_epoch"), A(domain, "source_epoch")),
        Eq(A(proof, "model_epoch"), A(domain, "model_epoch")),
        Eq(A(proof, "frame_epoch"), A(domain, "frame_epoch")),
        Eq(A(proof, "process_params"), A(schema, "params")),
        Eq(A(proof, "statement_digest"), A(law, "statement_digest")),
        Eq(A(proof, "assumptions_digest"), A(law, "assumptions_digest")),
    )


def build():
    specs = [
        ("Agent", "has_process_proof_adoption_policy", "ProcessProofAdoptionPolicy"),
        ("ProcessProofAdoptionPolicy", "requires_proof_for", "ProcessProofRequirement"),
        ("ProcessProofRequirement", "applies_to", "ProcessDomain"),
        ("Agent", "has_process_schema", "ProcessSchema"),
        ("Agent", "has_process_law", "ProcessLaw"),
        ("ProcessLaw", "has_proof_reference", "LawProofReference"),
        ("ProcessLaw", "about_process", "ProcessSchema"),
    ]
    base = [
        ["agent", "has_process_proof_adoption_policy", "pol"],
        ["pol", "requires_proof_for", "req"],
        ["req", "applies_to", "d"],
        ["agent", "has_process_domain", "d"],
        ["agent", "has_process_schema", "s"],
    ]
    law_bind = [
        ["agent", "has_process_law", "law"],
        ["law", "about_process", "s"],
        ["law", "has_proof_reference", "proof"],
    ]
    admitted = And(
        policy_on(), Eq(A("req", "required"), L(1)),
        Eq(A("req", "required_law"), A("law", "claim")),
        Eq(A("s", "domain"), A("d", "name")),
        Eq(A("s", "invented"), L(1)),
        Eq(A("s", "kind"), L("permutation")),
        valid_proof(),
    )
    approve = rule(
        "ppa_adopt_with_current_matching_proof", OFFLINE_AREA, 20,
        "For explicitly registered domains, keep a process active only when its checked law proof is attached to that exact process and matches family/model/process/frame identity, constructor parameters and statement assumptions.",
        base + law_bind,
        And(admitted, In(A("s", "status"), L(["active", "proof_blocked"]))),
        [["set_attr", "s", "status", "active"],
         ["set_attr", "s", "proof_adoption_status", "approved"],
         ["set_attr", "s", "proof_adopted_params", {"__term__": A("s", "params")}],
         ["set_attr", "s", "proof_adopted_family", {"__term__": A("d", "name")}],
         ["set_attr", "s", "proof_adopted_family_digest", {"__term__": A("d", "family_digest")}],
         ["set_attr", "s", "proof_adopted_model_digest", {"__term__": A("d", "model_digest")}],
         ["set_attr", "s", "proof_adopted_source_epoch", {"__term__": A("d", "source_epoch")}],
         ["set_attr", "s", "proof_adopted_model_epoch", {"__term__": A("d", "model_epoch")}],
         ["set_attr", "s", "proof_adopted_frame_epoch", {"__term__": A("d", "frame_epoch")}],
         ["set_attr", "s", "proof_statement_digest", {"__term__": A("law", "statement_digest")}],
         ["set_attr", "s", "proof_assumptions_digest", {"__term__": A("law", "assumptions_digest")}],
         ["set_attr", "s", "proof_checker", {"__term__": A("proof", "checker")}],
         ["set_attr", "s", "external_action_authorized", 0]],
    )
    no_valid_proof = Not(Exists(
        N("agent", "has_process_law"), "law",
        And(In(V("s"), N("law", "about_process")),
            Exists(N("law", "has_proof_reference"), "proof", valid_proof()))))
    block = rule(
        "ppa_block_registered_process_without_current_proof", OFFLINE_AREA, 21,
        "An invented process in a proof-required domain is excluded from active use/adoption until a matching current proof exists.",
        base,
        And(policy_on(), Eq(A("req", "required"), L(1)),
            Eq(A("s", "domain"), A("d", "name")), Eq(A("s", "invented"), L(1)),
            In(A("s", "status"), L(["active", "proof_blocked"])),
            Not(Eq(A("s", "proof_adoption_status"), L("invalidated"))), no_valid_proof),
        [["set_attr", "s", "status", "proof_blocked"],
         ["set_attr", "s", "proof_adoption_status", "blocked"],
         ["set_attr", "s", "proof_adoption_reason", "missing_or_mismatched_current_proof"]],
    )
    invalidate = rule(
        "ppa_invalidate_changed_process_binding", OFFLINE_AREA, 19,
        "A changed parameter vector or source/model/frame epoch invalidates proof-carrying adoption before the process can remain active.",
        base,
        And(policy_on(), Eq(A("req", "required"), L(1)),
            Eq(A("s", "domain"), A("d", "name")), Eq(A("s", "invented"), L(1)),
            Eq(A("s", "proof_adoption_status"), L("approved")),
            Not(Eq(A("s", "proof_adopted_params"), A("s", "params")))),
        [["set_attr", "s", "status", "proof_blocked"],
         ["set_attr", "s", "proof_adoption_status", "invalidated"],
         ["set_attr", "s", "proof_adoption_reason", "process_parameters_changed"]],
    )
    epoch_invalidate = rule(
        "ppa_invalidate_changed_domain_epoch", OFFLINE_AREA, 18,
        "A changed family/model/frame epoch invalidates an earlier adoption binding.",
        base,
        And(policy_on(), Eq(A("req", "required"), L(1)),
            Eq(A("s", "domain"), A("d", "name")), Eq(A("s", "invented"), L(1)),
            Eq(A("s", "proof_adoption_status"), L("approved")),
            Or(Not(Eq(A("s", "proof_adopted_family"), A("d", "name"))),
               Not(Eq(A("s", "proof_adopted_family_digest"), A("d", "family_digest"))),
               Not(Eq(A("s", "proof_adopted_model_digest"), A("d", "model_digest"))),
               Not(Eq(A("s", "proof_adopted_source_epoch"), A("d", "source_epoch"))),
               Not(Eq(A("s", "proof_adopted_model_epoch"), A("d", "model_epoch"))),
               Not(Eq(A("s", "proof_adopted_frame_epoch"), A("d", "frame_epoch"))))),
        [["set_attr", "s", "status", "proof_blocked"],
         ["set_attr", "s", "proof_adoption_status", "invalidated"],
         ["set_attr", "s", "proof_adoption_reason", "domain_epoch_changed"]],
    )
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": ["process_laws"],
        "self_load_only": True,
        "area": OFFLINE_AREA,
        "description": "P14.03: proof-carrying process adoption in explicitly registered domains only. Exact current process, law, proof reference and domain identities are required. This gate does not authorize external actions.",
        "nodes": [{"local_id": 0, "type": "ProcessProofAdoptionPolicy", "attrs": {
            "name": "process_proof_adoption_policy", "enabled": 0.0}},
        ],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_process_proof_adoption_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs),
        "rules": [epoch_invalidate, invalidate, approve, block],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
