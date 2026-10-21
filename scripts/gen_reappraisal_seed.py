#!/usr/bin/env python3
"""Generate P5.G2.2's opt-in, evidence-checked reappraisal rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "reappraisal.json"
AREA = "reappraisal"

APPRAISAL_KEYS = [
    "appraised", "residual", "residual_prev", "learning_progress", "threat",
    "threat_c0", "threat_half_life", "threat_last_refresh", "threat_now_epoch",
    "t_present", "threat_precision", "threat_persists", "valued_goal",
    "goal_blocked", "blocker_present", "contamination", "attachment",
    "regroundable", "was_engaged", "v_max", "step", "step_prev", "attach_v0",
    "attach_k_now", "attach_k_prev", "value_progress", "individual_benefit",
    "individual_cost", "supergraph_contribution", "collective_success",
    "collective_success_prev", "contribution_by_self", "observed_by_other",
    "happiness", "fulfilment_value", "total_value", "act_endorsed", "n_fired",
    "action_tendency", "emotion", "valence", "arousal", "hit_surprise",
    "hit_fear", "hit_anxiety", "hit_anger", "hit_frustration", "hit_disgust",
    "hit_joy", "hit_sadness", "hit_curiosity", "hit_boredom", "hit_fulfilment",
    "hit_pride",
]


def V(n): return {"type": "Var", "name": n}
def L(x): return {"type": "Lit", "value": x}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(x): return {"__term__": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Exists(src, var, predicate):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": predicate}


def _claim_without_current_support():
    current_source_evidence = Exists(
        N("event", "has_reappraisal_evidence"), "event_evidence",
        And(Eq(V("event_evidence"), V("support")),
            Eq(A("event_evidence", "status"), L("current")),
            Eq(A("event_evidence", "source_epoch"), A("event", "source_epoch"))))
    has_support = Exists(
        N("claim", "supported_by"), "support",
        And(current_source_evidence,
            Eq(A("support", "source_epoch"), A("event", "source_epoch"))))
    return Exists(N("frame", "has_interpretation_claim"), "claim", Not(has_support))


def _claim_with_current_contradiction():
    current_contradiction = Exists(
        N("claim", "contradicted_by"), "counter_evidence",
        And(Exists(
                N("event", "has_reappraisal_evidence"), "event_counter",
                Eq(V("event_counter"), V("counter_evidence"))),
            Eq(A("counter_evidence", "status"), L("current")),
            Eq(A("counter_evidence", "source_epoch"), A("event", "source_epoch"))))
    return Exists(N("frame", "has_interpretation_claim"), "claim", current_contradiction)


def _prior_view():
    return Exists(N("ag", "has_reappraisal_view"), "old",
                  And(Exists(N("frame", "produced_reappraisal_view"), "produced",
                             Eq(V("produced"), V("old"))),
                      Exists(N("old", "based_on_reappraisal_event"), "old_event",
                             Eq(V("old_event"), V("event"))),
                      Eq(A("old", "source_event_id"), A("event", "event_id")),
                      Eq(A("old", "source_epoch"), A("event", "source_epoch"))))


def materialize_rule():
    appraisal_attrs = {key: T(A("frame", key)) for key in APPRAISAL_KEYS}
    appraisal_attrs.update({
        "source_event_id": T(A("event", "event_id")),
        "source_epoch": T(A("event", "source_epoch")),
        "frame_id": T(A("frame", "frame_id")),
    })
    view_attrs = {
        "source_event_id": T(A("event", "event_id")),
        "source_epoch": T(A("event", "source_epoch")),
        "frame_id": T(A("frame", "frame_id")),
        "candidate_index": T(A("frame", "candidate_index")),
        "status": "adopted",
        "evidence_preserved": True,
        "forced_constraints_preserved": True,
        "probe_requester_key": T(A("request", "requester_key")),
        "appraisal_result": T(A("frame", "appraisal_result")),
    }
    evidence_guard = And(Not(_claim_without_current_support()),
                         Not(_claim_with_current_contradiction()))
    return {
        "name": "ra_materialize_funded_supported_appraisal_view",
        "area": AREA,
        "order": 10,
        "latency_class": "hard_realtime",
        "match": [["ag", "has_reappraisal_policy", "pol"],
                  ["ag", "has_reappraisal_event", "event"],
                  ["event", "has_candidate_reappraisal_frame", "frame"],
                  ["event", "has_reappraisal_appraisal_hub", "hub"],
                  ["frame", "has_funded_probe", "request"],
                  ["ag", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("request", "requester_kind"), L("cognition_aperture_probe")),
                      Eq(A("request", "status"), L("consumed")),
                      Eq(A("request", "debited_epoch"), A("mode", "epoch")),
                      Eq(A("request", "source_epoch"), A("event", "source_epoch")),
                      Eq(A("frame", "aperture_source_key"), A("request", "source_key")),
                      Eq(A("frame", "aperture_authority"), L("chosen")),
                      Eq(A("frame", "source_epoch"), A("event", "source_epoch")),
                      Eq(A("frame", "forced_constraints"), A("event", "forced_constraints")),
                      Gt(A("frame", "candidate_index"), L(0)),
                      Lt(A("frame", "candidate_index"), L(3)),
                      evidence_guard,
                      Not(_prior_view())),
        "effects": [
            ["add_node", "appraisal", "Appraisal", appraisal_attrs],
            ["add_node", "view", "ReappraisalView", view_attrs],
            ["add_edge", "hub", "has_appraisal", "appraisal", {}],
            ["add_edge", "ag", "has_reappraisal_view", "view", {}],
            ["add_edge", "view", "based_on_reappraisal_event", "event", {}],
            ["add_edge", "view", "selected_interpretation_frame", "frame", {}],
            ["add_edge", "view", "derived_appraisal", "appraisal", {}],
            ["add_edge", "view", "funded_by_probe", "request", {}],
            ["add_edge", "frame", "produced_reappraisal_view", "view", {}],
        ],
    }


def build_seed():
    return {
        "id": "reappraisal",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": ["core_emotions", "cognition_aperture"],
        "description": (
            "P5.G2.2 opt-in evidence-checked appraisal views. Requires an already "
            "consumed, same-epoch P4 chosen-aperture probe; preserves source event "
            "and forced constraints and feeds a separate Appraisal into core_emotions."
        ),
        "microtheory": {"name": "reappraisal", "description": "evidence-preserving alternate appraisal views"},
        "nodes": [{"local_id": 0, "type": "ReappraisalPolicy", "attrs": {"enabled": 0.0, "maximum_candidates": 2}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_reappraisal_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [
            {"provenance": "reappraisal:agent_event", "src": {"type": "Agent", "var": "ag"},
             "edge_type": "has_reappraisal_event", "tgt": {"type": "ReappraisalEvent", "var": "event"}},
            {"provenance": "reappraisal:event_frame", "src": {"type": "ReappraisalEvent", "var": "event"},
             "edge_type": "has_candidate_reappraisal_frame", "tgt": {"type": "ReappraisalFrame", "var": "frame"}},
            {"provenance": "reappraisal:event_hub", "src": {"type": "ReappraisalEvent", "var": "event"},
             "edge_type": "has_reappraisal_appraisal_hub", "tgt": {"type": "EmotionHub", "var": "hub"}},
            {"provenance": "reappraisal:frame_probe", "src": {"type": "ReappraisalFrame", "var": "frame"},
             "edge_type": "has_funded_probe", "tgt": {"type": "ThinkingBudgetRequest", "var": "request"}},
            {"provenance": "reappraisal:frame_claim", "src": {"type": "ReappraisalFrame", "var": "frame"},
             "edge_type": "has_interpretation_claim", "tgt": {"type": "InterpretationClaim", "var": "claim"}},
            {"provenance": "reappraisal:claim_evidence", "src": {"type": "InterpretationClaim", "var": "claim"},
             "edge_type": "supported_by", "tgt": {"type": "ReappraisalEvidence", "var": "evidence"}},
            {"provenance": "reappraisal:claim_counter_evidence", "src": {"type": "InterpretationClaim", "var": "claim"},
             "edge_type": "contradicted_by", "tgt": {"type": "ReappraisalEvidence", "var": "evidence"}},
            {"provenance": "reappraisal:event_evidence", "src": {"type": "ReappraisalEvent", "var": "event"},
             "edge_type": "has_reappraisal_evidence", "tgt": {"type": "ReappraisalEvidence", "var": "evidence"}},
            {"provenance": "reappraisal:view_event", "src": {"type": "ReappraisalView", "var": "view"},
             "edge_type": "based_on_reappraisal_event", "tgt": {"type": "ReappraisalEvent", "var": "event"}},
            {"provenance": "reappraisal:view_frame", "src": {"type": "ReappraisalView", "var": "view"},
             "edge_type": "selected_interpretation_frame", "tgt": {"type": "ReappraisalFrame", "var": "frame"}},
            {"provenance": "reappraisal:view_appraisal", "src": {"type": "ReappraisalView", "var": "view"},
             "edge_type": "derived_appraisal", "tgt": {"type": "Appraisal", "var": "appraisal"}},
            {"provenance": "reappraisal:view_probe", "src": {"type": "ReappraisalView", "var": "view"},
             "edge_type": "funded_by_probe", "tgt": {"type": "ThinkingBudgetRequest", "var": "request"}},
            {"provenance": "reappraisal:frame_view", "src": {"type": "ReappraisalFrame", "var": "frame"},
             "edge_type": "produced_reappraisal_view", "tgt": {"type": "ReappraisalView", "var": "view"}},
        ],
        "rules": [materialize_rule()],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n")
