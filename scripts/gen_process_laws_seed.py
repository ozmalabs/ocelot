#!/usr/bin/env python3
"""Generate the bounded P14 process-law checker seed.

The supported checker fragment is one structural permutation law: a concrete
commutator schema over two active same-domain permutation processes is even by
the parity homomorphism into Z2. Observed fingerprints alone never discharge
proof obligations. The seed remains disabled by default.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import (A, And, Eq, Gt, L, N, Not, OFFLINE_AREA, PCommutator,
                              policy_on, productions, rule)  # noqa: E402

SEED_ID = "process_laws"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def build():
    specs = [
        ("Agent", "has_process_laws_policy", "ProcessLawsPolicy"),
        ("Agent", "has_process_law_candidate", "ProcessLaw"),
        ("Agent", "has_process_law", "ProcessLaw"),
        ("ProcessLaw", "about_process", "ProcessSchema"),
        ("ProcessLaw", "has_proof_reference", "LawProofReference"),
        ("ProcessLaw", "has_counterexample", "LawCounterexample"),
        ("ProcessDomain", "contains_process_family", "ProcessSchema"),
    ]
    match = [
        ["agent", "has_process_laws_policy", "pol"],
        ["agent", "has_process_law_candidate", "law"],
        ["law", "about_process", "s"],
        ["s", "has_arg0", "a"],
        ["s", "has_arg1", "b"],
        ["agent", "has_process_domain", "d"],
    ]
    proof_rule = rule(
        "pl_check_permutation_commutator_law", OFFLINE_AREA, 40,
        "Check only the algebraic parity law for an actual commutator schema whose two arguments and source family match the declared finite permutation-domain model. This structural rule is the entire supported proof fragment; finite observations are not premises.",
        match,
        And(policy_on(), Eq(A("law", "status"), L("conjecture")),
            Eq(A("law", "claim"), L("commutator_even")),
            Eq(A("law", "evidence_kind"), L("structural_derivation")),
            Eq(A("law", "family"), A("d", "name")),
            Eq(A("law", "family_digest"), A("d", "family_digest")),
            Eq(A("law", "family_epoch"), A("d", "source_epoch")),
            Eq(A("law", "model_digest"), A("d", "model_digest")),
            Eq(A("law", "model_epoch"), A("d", "model_epoch")),
            Eq(A("law", "frame_epoch"), A("d", "frame_epoch")),
            Eq(A("law", "process_epoch"), A("d", "source_epoch")),
            Eq(A("law", "statement_digest"), L("4e3f9f19059a7254dbc8b885e464eccf69cec770eec50cb43a4d89e01415adb2")),
            Eq(A("law", "assumptions_digest"), L("d055b01ab1e76e1190f7b04e01fe250ab42f5ce6ccc24eaf4dfd84263ec96077")),
            Eq(A("s", "domain"), A("d", "name")),
            Eq(A("s", "kind"), L("permutation")),
            Eq(A("s", "operator"), L("commutator")),
            Eq(A("s", "status"), L("active")),
            Eq(A("s", "params"), PCommutator(A("a", "params"), A("b", "params"))),
            Eq(A("a", "domain"), A("d", "name")),
            Eq(A("b", "domain"), A("d", "name")),
            Eq(A("a", "kind"), L("permutation")),
            Eq(A("b", "kind"), L("permutation")),
            Eq(A("a", "status"), L("active")),
            Eq(A("b", "status"), L("active")),
            Eq(A("law", "assumptions"), L("permutation_group;parity_homomorphism_Z2;operator_semantics_v1")),
            Eq(A("law", "counterexample_count"), L(0))),
        [["set_attr", "law", "status", "checked"],
         ["set_attr", "law", "verdict", "checked_theorem"],
         ["set_attr", "law", "proof_kind", "native_structural_rule"],
         ["set_attr", "law", "proof_rule", "parity_commutator_even_v1"],
         ["set_attr", "law", "proven", 1],
         ["add_edge", "agent", "has_process_law", "law", {}],
         ["add_node", "proof", "LawProofReference", {
             "rule": "parity_commutator_even_v1",
             "statement": "commutator_even",
             "assumptions": "permutation_group;parity_homomorphism_Z2;operator_semantics_v1",
             "statement_digest": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "law"}, "key": "statement_digest"}},
             "assumptions_digest": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "law"}, "key": "assumptions_digest"}},
             "checker": "process_laws_seed_v1",
             "family": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "name"}},
             "family_digest": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "family_digest"}},
             "model_digest": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "model_digest"}},
             "family_epoch": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "source_epoch"}},
             "model_epoch": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "model_epoch"}},
             "frame_epoch": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "frame_epoch"}},
             "process_epoch": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "source_epoch"}},
             "process_params": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": "params"}},
             "status": "checked"}],
         ["add_edge", "law", "has_proof_reference", "proof", {}]], batch=True)
    false_sample_rule = rule(
        "pl_reject_counterexampled_finite_law",
        OFFLINE_AREA, 41,
        "A finite-sample law with an explicit counterexample is rejected; sampling never promotes a law to theorem.",
        [["agent", "has_process_laws_policy", "pol"], ["agent", "has_process_law_candidate", "law"],
         ["law", "has_counterexample", "ce"]],
        And(policy_on(), Eq(A("law", "status"), L("conjecture")),
            Eq(A("law", "evidence_kind"), L("finite_sample")),
            Eq(A("ce", "validated"), L(1)),
            Gt(A("law", "counterexample_count"), L(0))),
        [["set_attr", "law", "status", "rejected"],
         ["set_attr", "law", "verdict", "counterexample"],
         ["set_attr", "law", "proven", 0]])
    counterexample_downgrade = rule(
        "pl_downgrade_counterexampled_checked_law",
        OFFLINE_AREA, 42,
        "A counterexample invalidates a checked law and retains its proof reference as historical evidence.",
        [["agent", "has_process_laws_policy", "pol"], ["agent", "has_process_law_candidate", "law"],
         ["law", "has_counterexample", "ce"]],
        And(policy_on(), Eq(A("law", "status"), L("checked")),
            Eq(A("ce", "validated"), L(1))),
        [["set_attr", "law", "status", "rejected"],
         ["set_attr", "law", "verdict", "counterexample"],
         ["set_attr", "law", "proven", 0]])
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": ["process_schema"],
        "self_load_only": True,
        "area": OFFLINE_AREA,
        "description": "P14.02: disabled-by-default, bounded process-law checking. Only an exact structural commutator parity derivation is checked; empirical fingerprints remain conjectures and validated counterexamples reject claims.",
        "nodes": [{"local_id": 0, "type": "ProcessLawsPolicy", "attrs": {
            "name": "process_laws_policy", "enabled": 0.0,
            "supported_fragment": "permutation_commutator_parity_v1"}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_process_laws_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs),
        "rules": [proof_rule, false_sample_rule, counterexample_downgrade],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
