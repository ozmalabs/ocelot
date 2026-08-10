"""Generate the graph-native, proof-carrying self-change reasoning seed.

This is authoring tooling only.  Every diagnosis, comparison, selection, and
keep/reject decision emitted here runs as graph data in the Rust rule engine.
The host supplies observations and measured trial outcomes; it does not select
the repair.
"""
from __future__ import annotations

import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def N(var, key):
    return {"type": "Plus", "items": [A(var, key), L(0)]}


def Zero(var, key):
    return Eq(N(var, key), L(0))


def Positive(var, key):
    return Gt(N(var, key), L(0))


def And(*items):
    return {"type": "And", "items": list(items)}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def neighbours(var, edge_type):
    return {"type": "Neighbours", "node": V(var), "edge_type": edge_type}


def dyn(term):
    return {"__term__": term}


def edge_production(src, edge_type, tgt):
    return {
        "provenance": f"seed:self_change_reasoning:{edge_type}",
        "src": {"type": src, "var": "x"},
        "edge_type": edge_type,
        "tgt": {"type": tgt, "var": "y"},
        "where": None,
        "weight": L(1),
    }


def observe_gap_rule():
    return {
        "name": "sc_observe_gap",
        "comment": (
            "Convert a mechanical FaultProbe into the explicit beginning of a "
            "SelfChange.  The probe contains measurements, never a diagnosis."
        ),
        "match": [["agent", "observes_fault_probe", "probe"]],
        "where": And(
            Zero("probe", "change_opened"),
            Gt(
                {
                    "type": "Plus",
                    "items": [
                        N("probe", "false_negative"),
                        N("probe", "false_positive"),
                        N("probe", "relation_counterfactual"),
                        N("probe", "outcome_mismatch"),
                        N("probe", "cost_excess"),
                    ],
                },
                L(0),
            ),
        ),
        "effects": [
            [
                "add_node",
                "gap",
                "ObservedGap",
                {
                    "status": "observed",
                    "case_id": dyn(A("probe", "case_id")),
                    "target_uid": dyn(A("probe", "target_uid")),
                    "expected_revision": dyn(A("probe", "expected_revision")),
                    "baseline_hash": dyn(A("probe", "baseline_hash")),
                },
            ],
            [
                "add_node",
                "sc",
                "SelfChange",
                {
                    "status": "diagnosing",
                    "case_id": dyn(A("probe", "case_id")),
                    "target_uid": dyn(A("probe", "target_uid")),
                    "expected_revision": dyn(A("probe", "expected_revision")),
                    "selected": 0,
                },
            ],
            ["add_node", "noop", "ControlArm", {"kind": "no_op", "required": 1}],
            [
                "add_node",
                "placebo",
                "ControlArm",
                {"kind": "same_size_placebo", "required": 1},
            ],
            ["add_edge", "agent", "considers_change", "sc"],
            ["add_edge", "sc", "observed_as", "gap"],
            ["add_edge", "gap", "from_probe", "probe"],
            ["add_edge", "sc", "has_noop_control", "noop"],
            ["add_edge", "sc", "has_placebo_control", "placebo"],
            ["set_attr", "probe", "change_opened", 1],
        ],
    }


PATCH_FAMILIES = (
    (
        "threshold_adjustment",
        "where",
        1,
        1,
        And(Positive("probe", "false_negative"),
            Positive("probe", "threshold_sensitivity")),
        "Relax or move one threshold while preserving the surrounding guard.",
    ),
    (
        "guard_strengthening",
        "where",
        2,
        1,
        And(Positive("probe", "false_positive"),
            Positive("probe", "context_sensitivity")),
        "Add the smallest discriminator that excludes the failing context.",
    ),
    (
        "relation_addition",
        "where",
        3,
        2,
        Positive("probe", "relation_counterfactual"),
        "Add one causally supported relation to the match or guard.",
    ),
    (
        "effect_substitution",
        "effect",
        4,
        2,
        And(Positive("probe", "outcome_mismatch"),
            Positive("probe", "effect_counterfactual")),
        "Substitute one effect while keeping the triggering conditions fixed.",
    ),
    (
        "firing_budget_guard",
        "where",
        2,
        1,
        And(Positive("probe", "cost_excess"),
            Positive("probe", "repeated_noop_firings")),
        "Add an idempotence or epoch guard around repeated no-op firing.",
    ),
)


def candidate_rule(family, field, mdl_cost, blast_radius, predicate, description):
    marker = f"candidate_{family}"
    return {
        "name": f"sc_hypothesise_{family}",
        "comment": (
            f"Minimal candidate family {family}.  It is proposed from observed "
            "structural/behavioural evidence, not from a supplied answer key."
        ),
        "match": [
            ["sc", "observed_as", "gap"],
            ["gap", "from_probe", "probe"],
        ],
        "where": And(Zero("probe", marker), predicate),
        "effects": [
            [
                "add_node",
                "hyp",
                "CausalHypothesis",
                {
                    "family": family,
                    "status": "candidate",
                    "case_id": dyn(A("probe", "case_id")),
                    "explanation": description,
                },
            ],
            [
                "add_node",
                "spec",
                "ChangeSpec",
                {
                    "family": family,
                    "field": field,
                    "minimality": "single_local_edit",
                    "status": "specified",
                },
            ],
            [
                "add_node",
                "patch",
                "RulePatch",
                {
                    "family": family,
                    "field": field,
                    "target_uid": dyn(A("probe", "target_uid")),
                    "expected_revision": dyn(A("probe", "expected_revision")),
                    "expected_content_hash": dyn(A("probe", "baseline_hash")),
                    "proposed_clause": dyn(A("probe", f"{family}_clause")),
                    "inverse_clause": dyn(A("probe", "live_clause")),
                    "mdl_cost": mdl_cost,
                    "blast_radius": blast_radius,
                    "status": "proposed",
                    "state": "proposed",
                    "obligations_minted": 0,
                    "proofs_passed": 0,
                    "trial_complete": 0,
                },
            ],
            ["add_edge", "gap", "supports_hypothesis", "hyp"],
            ["add_edge", "hyp", "proposes_spec", "spec"],
            ["add_edge", "spec", "specifies_patch", "patch"],
            ["add_edge", "sc", "has_hypothesis", "hyp"],
            ["add_edge", "sc", "has_spec", "spec"],
            ["add_edge", "sc", "has_patch", "patch"],
            ["set_attr", "probe", marker, 1],
        ],
    }


def proof_obligations_rule():
    obligations = (
        ("po_causal", "ProofObligation", "causal_gain", "proof_causal"),
        ("po_invariant", "ProofObligation", "protected_invariants", "proof_invariant"),
        ("po_noop", "ProofObligation", "beats_no_op_control", "proof_noop"),
        ("po_placebo", "ProofObligation", "beats_same_size_placebo", "proof_placebo"),
        ("po_budget", "ProofObligation", "resource_budget", "proof_budget"),
        ("po_repeat", "ProofObligation", "replication", "proof_replication"),
    )
    effects = []
    for var, node_type, kind, edge in obligations:
        effects.append([
            "add_node",
            var,
            node_type,
            {"kind": kind, "status": "open"},
        ])
        effects.append(["add_edge", "patch", edge, var])
    effects.extend([
        ["set_attr", "patch", "obligations_minted", 1],
        ["set_attr", "patch", "state", "awaiting_trial"],
    ])
    return {
        "name": "sc_mint_proof_obligations",
        "comment": (
            "Every patch must carry causal, invariant, two-control, budget, and "
            "replication obligations before it can enter a trial."
        ),
        "match": [["sc", "has_patch", "patch"]],
        "where": Zero("patch", "obligations_minted"),
        "effects": effects,
    }


def evidence_match():
    return [
        ["sc", "has_patch", "patch"],
        ["patch", "proof_causal", "po_causal"],
        ["patch", "proof_invariant", "po_invariant"],
        ["patch", "proof_noop", "po_noop"],
        ["patch", "proof_placebo", "po_placebo"],
        ["patch", "proof_budget", "po_budget"],
        ["patch", "proof_replication", "po_repeat"],
        ["patch", "candidate_evidence", "ev"],
        ["sc", "has_noop_control", "noop"],
        ["noop", "has_evidence", "noop_ev"],
        ["sc", "has_placebo_control", "placebo"],
        ["placebo", "has_evidence", "placebo_ev"],
    ]


def evidence_passes():
    return And(
        Gt(N("ev", "causal_gain"),
           {"type": "Plus", "items": [N("noop_ev", "causal_gain"), L(5)]}),
        Gt(N("ev", "causal_gain"),
           {"type": "Plus", "items": [N("placebo_ev", "causal_gain"), L(5)]}),
        Zero("ev", "protected_regressions"),
        Lte(N("ev", "resource_cost"), N("ev", "resource_budget")),
        Gte(N("ev", "replications"), L(2)),
        Gte(N("ev", "replicated_gain"), L(5)),
        Eq(A("noop_ev", "arm"), L("no_op")),
        Eq(A("placebo_ev", "arm"), L("same_size_placebo")),
    )


def trial_pass_rule():
    return {
        "name": "sc_trial_discharge_proofs",
        "comment": (
            "A patch passes only when it beats both a no-op and a same-size "
            "placebo, preserves protected invariants, stays in budget, and "
            "replicates.  These are conjunctions, never an aggregate score."
        ),
        "match": evidence_match(),
        "where": And(
            Zero("patch", "trial_complete"),
            evidence_passes(),
        ),
        "effects": [
            [
                "add_node",
                "trial",
                "Trial",
                {
                    "status": "passed",
                    "candidate_gain": dyn(N("ev", "causal_gain")),
                    "noop_gain": dyn(N("noop_ev", "causal_gain")),
                    "placebo_gain": dyn(N("placebo_ev", "causal_gain")),
                },
            ],
            ["add_edge", "patch", "has_trial", "trial"],
            ["set_attr", "po_causal", "status", "discharged"],
            ["set_attr", "po_invariant", "status", "discharged"],
            ["set_attr", "po_noop", "status", "discharged"],
            ["set_attr", "po_placebo", "status", "discharged"],
            ["set_attr", "po_budget", "status", "discharged"],
            ["set_attr", "po_repeat", "status", "discharged"],
            ["set_attr", "patch", "proofs_passed", 1],
            ["set_attr", "patch", "trial_complete", 1],
            ["set_attr", "patch", "state", "trial_passed"],
            ["set_attr", "patch", "measured_gain", dyn(N("ev", "causal_gain"))],
        ],
    }


def trial_reject_rule():
    return {
        "name": "sc_trial_reject_unproven",
        "comment": (
            "Negative result is first-class evidence.  A measured patch that "
            "fails any preregistered obligation is retained as rejected rather "
            "than silently retried."
        ),
        "match": evidence_match(),
        "where": And(
            Zero("patch", "trial_complete"),
            Not(evidence_passes()),
        ),
        "effects": [
            ["add_node", "trial", "Trial", {"status": "rejected", "falsified": 1}],
            ["add_edge", "patch", "has_trial", "trial"],
            ["set_attr", "patch", "proofs_passed", 0],
            ["set_attr", "patch", "trial_complete", 1],
            ["set_attr", "patch", "state", "rejected"],
        ],
    }


def select_minimal_rule():
    better = Exists(
        neighbours("sc", "has_patch"),
        "other",
        And(
            Positive("other", "proofs_passed"),
            Lt(N("other", "mdl_cost"), N("patch", "mdl_cost")),
        ),
    )
    return {
        "name": "sc_select_minimal_proven_patch",
        "comment": (
            "Occam/MDL selection: among patches that independently discharged "
            "every obligation, choose the smallest description.  Evidence gates "
            "admissibility; MDL only breaks ties inside the admissible set."
        ),
        "match": [["sc", "has_patch", "patch"]],
        "where": And(
            Zero("sc", "selected"),
            Positive("patch", "proofs_passed"),
            Not(better),
        ),
        "effects": [
            [
                "add_node",
                "canary",
                "Canary",
                {
                    "status": "pending",
                    "protected_regressions": -1,
                    "replicated_gain": 0,
                },
            ],
            ["add_edge", "sc", "selected_patch", "patch"],
            ["add_edge", "patch", "has_canary", "canary"],
            ["set_attr", "patch", "state", "selected_for_canary"],
            ["set_attr", "patch", "selected", 1],
            ["set_attr", "sc", "selected", 1],
            ["set_attr", "sc", "status", "canary"],
        ],
    }


def canary_commit_rule():
    return {
        "name": "sc_canary_requests_commit",
        "comment": (
            "A canary does not mutate the parent by itself.  Passing canary "
            "evidence mints a Commit request carrying the selected RulePatch; "
            "the Rust transaction boundary is the mechanical enactor."
        ),
        "match": [
            ["sc", "selected_patch", "patch"],
            ["patch", "has_canary", "canary"],
            ["canary", "has_canary_evidence", "cev"],
        ],
        "where": And(
            Eq(A("canary", "status"), L("pending")),
            Gte(N("cev", "replicated_gain"), L(5)),
            Zero("cev", "protected_regressions"),
            Gte(N("cev", "replications"), L(2)),
        ),
        "effects": [
            [
                "add_node",
                "commit",
                "Commit",
                {
                    "status": "ready",
                    "enactor": "rust_rule_patch_transaction",
                    "target_uid": dyn(A("patch", "target_uid")),
                    "expected_revision": dyn(A("patch", "expected_revision")),
                },
            ],
            ["add_edge", "sc", "has_commit", "commit"],
            ["add_edge", "commit", "commits_patch", "patch"],
            ["apply_rule_patch", "patch"],
            ["set_attr", "canary", "status", "passed"],
            ["set_attr", "patch", "state", "transaction_queued"],
            ["set_attr", "sc", "status", "commit_ready"],
        ],
    }


def canary_abort_rule():
    passing = And(
        Gte(N("cev", "replicated_gain"), L(5)),
        Zero("cev", "protected_regressions"),
        Gte(N("cev", "replications"), L(2)),
    )
    return {
        "name": "sc_canary_abort",
        "match": [
            ["sc", "selected_patch", "patch"],
            ["patch", "has_canary", "canary"],
            ["canary", "has_canary_evidence", "cev"],
        ],
        "where": And(Eq(A("canary", "status"), L("pending")), Not(passing)),
        "effects": [
            [
                "add_node",
                "abort",
                "Abort",
                {
                    "stage": "canary",
                    "reason": "canary_falsified",
                    "rollback_required": 0,
                },
            ],
            ["add_edge", "sc", "has_abort", "abort"],
            ["add_edge", "abort", "rejects_patch", "patch"],
            ["set_attr", "canary", "status", "failed"],
            ["set_attr", "patch", "state", "aborted"],
            ["set_attr", "sc", "status", "aborted"],
        ],
    }


def exhaust_abort_rule():
    no_passing = Not(Exists(
        neighbours("sc", "has_patch"),
        "p",
        Positive("p", "proofs_passed"),
    ))
    return {
        "name": "sc_abort_exhausted_hypotheses",
        "comment": (
            "The host may close an evidence batch after mechanically running all "
            "arms.  If no patch survived the controls, the graph concludes "
            "abort; it never promotes the least-bad failure."
        ),
        "match": [["sc", "evidence_batch", "batch"]],
        "where": And(
            Eq(A("batch", "status"), L("closed")),
            Eq(A("sc", "status"), L("diagnosing")),
            no_passing,
        ),
        "effects": [
            [
                "add_node",
                "abort",
                "Abort",
                {
                    "stage": "trial",
                    "reason": "no_causally_supported_patch",
                    "rollback_required": 0,
                },
            ],
            ["add_edge", "sc", "has_abort", "abort"],
            ["set_attr", "sc", "status", "aborted"],
        ],
    }


def consolidate_rule():
    return {
        "name": "sc_consolidate_committed_change",
        "comment": (
            "A commit becomes retained knowledge only after the enactor reports "
            "success and independent post-commit evidence survives restart and "
            "cross-context replay."
        ),
        "match": [
            ["sc", "has_commit", "commit"],
            ["commit", "commits_patch", "patch"],
            ["commit", "has_consolidation_evidence", "evidence"],
        ],
        "where": And(
            Eq(A("commit", "status"), L("ready")),
            Eq(A("patch", "status"), L("committed")),
            Positive("evidence", "restart_ok"),
            Positive("evidence", "cross_context_ok"),
            Gte(N("evidence", "retained_gain"), L(5)),
            Zero("evidence", "protected_regressions"),
        ),
        "effects": [
            [
                "add_node",
                "cons",
                "Consolidation",
                {
                    "status": "retained",
                    "new_revision": dyn(A("patch", "result_revision")),
                    "new_hash": dyn(A("patch", "result_content_hash")),
                    "retained_gain": dyn(N("evidence", "retained_gain")),
                },
            ],
            ["add_edge", "sc", "has_consolidation", "cons"],
            ["add_edge", "cons", "consolidates_patch", "patch"],
            ["set_attr", "commit", "status", "consolidated"],
            ["set_attr", "sc", "status", "consolidated"],
        ],
    }


def post_commit_abort_rule():
    retained = And(
        Eq(A("patch", "status"), L("committed")),
        Positive("evidence", "restart_ok"),
        Positive("evidence", "cross_context_ok"),
        Gte(N("evidence", "retained_gain"), L(5)),
        Zero("evidence", "protected_regressions"),
    )
    return {
        "name": "sc_abort_and_request_rollback_after_commit",
        "match": [
            ["sc", "has_commit", "commit"],
            ["commit", "commits_patch", "patch"],
            ["commit", "has_consolidation_evidence", "evidence"],
        ],
        "where": And(Eq(A("commit", "status"), L("ready")), Not(retained)),
        "effects": [
            [
                "add_node",
                "abort",
                "Abort",
                {
                    "stage": "consolidation",
                    "reason": "post_commit_regression",
                    "rollback_required": 1,
                },
            ],
            ["add_edge", "sc", "has_abort", "abort"],
            ["add_edge", "abort", "rejects_patch", "patch"],
            ["set_attr", "commit", "status", "rollback_ready"],
            ["set_attr", "sc", "status", "rollback_ready"],
        ],
    }


def transaction_refusal_rule():
    return {
        "name": "sc_abort_refused_transaction",
        "comment": (
            "The Rust CAS/validator is authoritative.  A refused RulePatch is "
            "turned into explicit graph evidence and never retried unchanged."
        ),
        "match": [
            ["sc", "has_commit", "commit"],
            ["commit", "commits_patch", "patch"],
        ],
        "where": And(
            Eq(A("commit", "status"), L("ready")),
            Eq(A("patch", "status"), L("refused")),
        ),
        "effects": [
            [
                "add_node",
                "abort",
                "Abort",
                {
                    "stage": "transaction",
                    "reason": dyn(A("patch", "reason")),
                    "rollback_required": 0,
                },
            ],
            ["add_edge", "sc", "has_abort", "abort"],
            ["add_edge", "abort", "rejects_patch", "patch"],
            ["set_attr", "commit", "status", "refused"],
            ["set_attr", "sc", "status", "aborted"],
        ],
    }


def main():
    rules = [observe_gap_rule()]
    rules.extend(candidate_rule(*row) for row in PATCH_FAMILIES)
    rules.extend([
        proof_obligations_rule(),
        trial_pass_rule(),
        trial_reject_rule(),
        select_minimal_rule(),
        canary_commit_rule(),
        canary_abort_rule(),
        exhaust_abort_rule(),
        transaction_refusal_rule(),
        consolidate_rule(),
        post_commit_abort_rule(),
    ])
    productions = [
        edge_production("Agent", "observes_fault_probe", "FaultProbe"),
        edge_production("Agent", "considers_change", "SelfChange"),
        edge_production("SelfChange", "observed_as", "ObservedGap"),
        edge_production("ObservedGap", "from_probe", "FaultProbe"),
        edge_production("SelfChange", "has_hypothesis", "CausalHypothesis"),
        edge_production("ObservedGap", "supports_hypothesis", "CausalHypothesis"),
        edge_production("CausalHypothesis", "proposes_spec", "ChangeSpec"),
        edge_production("SelfChange", "has_spec", "ChangeSpec"),
        edge_production("ChangeSpec", "specifies_patch", "RulePatch"),
        edge_production("SelfChange", "has_patch", "RulePatch"),
        edge_production("SelfChange", "has_noop_control", "ControlArm"),
        edge_production("SelfChange", "has_placebo_control", "ControlArm"),
        edge_production("ControlArm", "has_evidence", "TrialEvidence"),
        edge_production("RulePatch", "candidate_evidence", "TrialEvidence"),
        edge_production("RulePatch", "proof_causal", "ProofObligation"),
        edge_production("RulePatch", "proof_invariant", "ProofObligation"),
        edge_production("RulePatch", "proof_noop", "ProofObligation"),
        edge_production("RulePatch", "proof_placebo", "ProofObligation"),
        edge_production("RulePatch", "proof_budget", "ProofObligation"),
        edge_production("RulePatch", "proof_replication", "ProofObligation"),
        edge_production("RulePatch", "has_trial", "Trial"),
        edge_production("SelfChange", "selected_patch", "RulePatch"),
        edge_production("RulePatch", "has_canary", "Canary"),
        edge_production("Canary", "has_canary_evidence", "CanaryEvidence"),
        edge_production("SelfChange", "evidence_batch", "EvidenceBatch"),
        edge_production("SelfChange", "has_commit", "Commit"),
        edge_production("Commit", "commits_patch", "RulePatch"),
        edge_production("Commit", "has_consolidation_evidence", "ConsolidationEvidence"),
        edge_production("SelfChange", "has_abort", "Abort"),
        edge_production("Abort", "rejects_patch", "RulePatch"),
        edge_production("SelfChange", "has_consolidation", "Consolidation"),
        edge_production("Consolidation", "consolidates_patch", "RulePatch"),
    ]
    seed = {
        "id": "self_change_reasoning",
        "version": "1.1.0",
        "depends_on": ["self_repair"],
        "capability_keys": [
            "diagnose_self_change",
            "proof_carrying_rule_patch",
            "controlled_self_experiment",
        ],
        "description": (
            "Graph-native proof-carrying self-change reasoning.  Mechanical "
            "FaultProbe measurements become ObservedGap -> CausalHypothesis -> "
            "ChangeSpec/RulePatch -> ProofObligation -> Trial -> Canary -> "
            "Commit|Abort -> Consolidation.  Candidate patches must beat both "
            "no-op and same-size placebo controls, preserve invariants, fit a "
            "resource budget, and replicate. Gains are integer evidence units; "
            "all cognitive quantities are integer. No Python decision."
        ),
        "microtheory": {
            "name": "self_change_reasoning",
            "description": (
                "minimal causal self-repair under proof obligations, controls, "
                "canarying, rollback and consolidation"
            ),
        },
        "nodes": [],
        "edges": [],
        "productions": productions,
        "rules": rules,
    }
    out = os.path.join(ROOT, "seeds", "self_change_reasoning.json")
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    with open(tmp, encoding="utf-8") as fh:
        json.load(fh)
    os.replace(tmp, out)
    print(f"wrote + validated {os.path.relpath(out, ROOT)} ({len(rules)} rules)")


if __name__ == "__main__":
    main()
