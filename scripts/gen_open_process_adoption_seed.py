#!/usr/bin/env python3
"""Generate exact-digest human-gated adoption/rollback rules for P19 candidates."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import A, And, Count, Eq, L, N, Not, OFFLINE_AREA, Or, T, V, policy_on, productions, rule

SEED_ID = "open_process_adoption"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def build():
    specs = [
        ("Agent", "has_open_process_adoption_policy", "OpenProcessAdoptionPolicy"),
        ("Agent", "has_open_process_candidate", "OpenProcessCandidate"),
        ("Agent", "has_open_process_adoption_approval", "OpenProcessAdoptionApproval"),
        ("OpenProcessAdoptionApproval", "approves_open_process_candidate", "OpenProcessCandidate"),
        ("OpenProcessCandidate", "approved_by_open_process_adoption", "OpenProcessAdoptionApproval"),
        ("OpenProcessCandidate", "has_dependent_task", "SolveTask"),
        ("SolveTask", "uses_approved_open_process_candidate", "OpenProcessCandidate"),
        ("OpenProcessCandidate", "has_world_execution_receipt", "OpenProcessWorldReceipt"),
        ("OpenProcessCandidate", "has_expression_digest_receipt", "OpenProcessDigestReceipt"),
        ("SolveTask", "has_open_process_world_receipt", "OpenProcessWorldReceipt"),
        ("OpenProcessCandidate", "adopted_as_process", "ProcessSchema"),
        ("Agent", "has_process_schema", "ProcessSchema"),
        ("ProcessDomain", "has_held_process", "ProcessSchema"),
        ("Agent", "has_process_domain", "ProcessDomain"),
    ]
    match = [
        ["agent", "has_open_process_adoption_policy", "pol"],
        ["agent", "has_open_process_candidate", "candidate"],
        ["candidate", "has_expression_digest_receipt", "digest_receipt"],
        ["agent", "has_open_process_adoption_approval", "approval"],
        ["approval", "approves_open_process_candidate", "candidate"],
        ["agent", "has_process_domain", "domain"],
    ]
    exact_binding = And(
        Eq(A("candidate", "status"), L("unapproved_candidate")),
        Eq(A("candidate", "expression_digest_status"), L("verified")),
        Eq(A("digest_receipt", "status"), L("verified")),
        Eq(A("digest_receipt", "expression_digest"), A("candidate", "expression_digest")),
        Eq(Count(N("candidate", "has_expression_digest_receipt")), L(1)),
        Eq(A("approval", "status"), L("approved")),
        Eq(A("approval", "approval_kind"), L("human")),
        Eq(A("approval", "expression_digest"), A("candidate", "expression_digest")),
        Eq(A("approval", "expression_key"), A("candidate", "expression_key")),
        Eq(A("approval", "expression_tree"), A("candidate", "expression_tree")),
        Eq(A("approval", "effect_digest"), A("candidate", "effect_digest")),
        Eq(A("approval", "params"), A("candidate", "params")),
        Eq(A("approval", "guard_state"), A("candidate", "guard_state")),
        Eq(A("approval", "domain"), A("candidate", "domain")),
        Eq(A("approval", "source_epoch"), A("candidate", "source_epoch")),
        Eq(A("approval", "model_epoch"), A("candidate", "model_epoch")),
        Eq(A("approval", "frame_epoch"), A("candidate", "frame_epoch")),
        Eq(A("candidate", "domain"), A("domain", "name")),
        Eq(A("candidate", "source_epoch"), A("domain", "source_epoch")),
        Eq(A("candidate", "model_epoch"), A("domain", "model_epoch")),
        Eq(A("candidate", "frame_epoch"), A("domain", "frame_epoch")),
    )
    adopt = rule(
        "opa_adopt_exact_human_approved_expression", OFFLINE_AREA, 20,
        "Adopt only the exact expression, finite effect, guard and current source/model/frame binding named by a candidate-specific human approval.",
        match,
        And(policy_on(), exact_binding),
        [["set_attr", "candidate", "status", "adopted_candidate"],
         ["set_attr", "candidate", "adoption_status", "approved"],
         ["set_attr", "candidate", "adopted_expression_digest", {"__term__": A("candidate", "expression_digest")}],
         ["set_attr", "candidate", "adopted_expression_key", {"__term__": A("candidate", "expression_key")}],
         ["set_attr", "candidate", "adopted_expression_tree", {"__term__": A("candidate", "expression_tree")}],
         ["set_attr", "candidate", "adopted_effect_digest", {"__term__": A("candidate", "effect_digest")}],
         ["set_attr", "candidate", "adopted_params", {"__term__": A("candidate", "params")}],
         ["set_attr", "candidate", "adopted_guard_state", {"__term__": A("candidate", "guard_state")}],
         ["set_attr", "candidate", "adopted_domain", {"__term__": A("candidate", "domain")}],
         ["set_attr", "candidate", "adopted_source_epoch", {"__term__": A("candidate", "source_epoch")}],
         ["set_attr", "candidate", "adopted_model_epoch", {"__term__": A("candidate", "model_epoch")}],
         ["set_attr", "candidate", "adopted_frame_epoch", {"__term__": A("candidate", "frame_epoch")}],
         ["add_node", "process", "ProcessSchema", {
            "name": {"__term__": A("candidate", "expression_key")},
            "kind": {"__term__": A("candidate", "kind")},
            "domain_kind": {"__term__": A("candidate", "kind")},
            "domain": {"__term__": A("candidate", "domain")},
            "params": {"__term__": A("candidate", "params")},
            "cost": {"__term__": A("candidate", "work_cost")},
            "status": "pending_world_verification", "invented": 1,
            "provenance": "invented_by:open_process_search",
            "source_digest": "pending_world_verification",
            "owner_agent": {"__term__": V("agent")},
            "source_epoch": {"__term__": A("candidate", "source_epoch")},
            "model_epoch": {"__term__": A("candidate", "model_epoch")},
            "frame_epoch": {"__term__": A("candidate", "frame_epoch")},
            "probe_epoch": {"__term__": L(0.0)},
            "fingerprint": {"__term__": A("candidate", "effect_digest")},
            "fingerprint_checked": 0, "dedup_checked": 0,
            "verification_receipt": "pending_world_verification"}],
         ["add_edge", "candidate", "approved_by_open_process_adoption", "approval", {}],
         ["add_edge", "candidate", "adopted_as_process", "process", {}],
         ["add_edge", "agent", "has_process_schema", "process", {}],
         ["add_edge", "domain", "has_held_process", "process", {}],
         ["set_attr", "approval", "status", "consumed"]],
        batch=False,
    )
    invalidate = rule(
        "opa_invalidate_changed_candidate_and_dependent_plan", OFFLINE_AREA, 10,
        "Invalidate adoption before another action if the approved expression, exact effect, parameters, guard or domain epochs change; revoke any dependent task.",
        [["agent", "has_open_process_adoption_policy", "pol"],
         ["agent", "has_open_process_candidate", "candidate"],
         ["candidate", "approved_by_open_process_adoption", "approval"],
         ["agent", "has_process_domain", "domain"]],
        And(policy_on(), Eq(A("candidate", "status"), L("adopted_candidate")),
            Eq(A("candidate", "adoption_status"), L("approved")),
            Eq(A("candidate", "domain"), A("domain", "name")),
            Or(Not(Eq(A("approval", "status"), L("consumed"))),
               Not(Eq(A("approval", "expression_digest"), A("candidate", "expression_digest"))),
               Not(Eq(A("approval", "expression_key"), A("candidate", "expression_key"))),
               Not(Eq(A("approval", "expression_tree"), A("candidate", "expression_tree"))),
               Not(Eq(A("approval", "effect_digest"), A("candidate", "effect_digest"))),
               Not(Eq(A("approval", "params"), A("candidate", "params"))),
               Not(Eq(A("approval", "guard_state"), A("candidate", "guard_state"))),
               Not(Eq(A("candidate", "expression_digest"), A("candidate", "adopted_expression_digest"))),
               Not(Eq(A("candidate", "expression_key"), A("candidate", "adopted_expression_key"))),
               Not(Eq(A("candidate", "effect_digest"), A("candidate", "adopted_effect_digest"))),
               Not(Eq(A("candidate", "params"), A("candidate", "adopted_params"))),
               Not(Eq(A("candidate", "guard_state"), A("candidate", "adopted_guard_state"))),
               Not(Eq(A("domain", "source_epoch"), A("candidate", "adopted_source_epoch"))),
               Not(Eq(A("domain", "model_epoch"), A("candidate", "adopted_model_epoch"))),
               Not(Eq(A("domain", "frame_epoch"), A("candidate", "adopted_frame_epoch"))),
               Not(Eq(A("candidate", "expression_tree"), A("candidate", "adopted_expression_tree"))))),
        [["set_attr", "candidate", "status", "invalidated"],
         ["set_attr", "candidate", "adoption_status", "invalidated"],
         ["set_attr", "candidate", "invalidation_reason", "approved_expression_or_domain_binding_changed"]],
        batch=False,
    )
    abort = rule(
        "opa_abort_dependent_task_after_revocation", OFFLINE_AREA, 11,
        "Stop a dependent process plan after candidate adoption has been invalidated.",
        [["agent", "has_open_process_candidate", "candidate"],
         ["candidate", "has_dependent_task", "task"]],
        And(Eq(A("candidate", "adoption_status"), L("invalidated")),
            Or(Eq(A("task", "status"), L("active")), Eq(A("task", "status"), L("executing")))),
        [["set_attr", "task", "status", "aborted"],
         ["set_attr", "task", "abort_reason", "adopted_process_invalidated"]], batch=False,
    )
    return {
        "id": SEED_ID, "version": "1.0.0", "depends_on": ["open_process_search"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "P19 candidate-specific expression digest adoption and revocation. Approval is explicit, exact-binding and opt-in.",
        "microtheory": {"name": SEED_ID, "description": "Adopt exact verified process proposals under matching human approval."},
        "nodes": [{"local_id": 0, "type": "OpenProcessAdoptionPolicy", "attrs": {
            "name": "open_process_adoption_policy", "enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_open_process_adoption_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs),
        "rules": [invalidate, abort, adopt],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
