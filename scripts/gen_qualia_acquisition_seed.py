#!/usr/bin/env python3
"""Generate graph rules for funded episode-grounded qualia acquisition."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "qualia_acquisition.json"
AREA = "qualia_acquisition"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def N(node, edge): return {"type": "Neighbours", "node": V(node), "edge_type": edge, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(value): return {"type": "Not", "arg": value}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def In(member, values): return {"type": "In", "member": member, "container": L(values)}
def Exists(source, var, predicate): return {"type": "Exists", "source": source, "var_name": var, "predicate": predicate}
def Count(source): return {"type": "Count", "source": source}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Concat(*parts): return {"type": "StringConcat", "parts": list(parts)}
def Json(value): return {"type": "ToJsonString", "value": value}
def Append(seq, item): return {"type": "Append", "seq": seq, "item": item}


def candidate_key(owner, feature):
    return Concat(Json(owner), L(":"), feature)


def dimension_id(owner, feature):
    return Concat(L("phenomenal:acquired:"), Json(owner), L(":"), feature)


def request_key():
    return Concat(L("qa-probe:"), Json(A("ep", "owner_id")), L(":"),
                  A("ev", "event_id"), L(":"), A("f", "feature_id"),
                  L(":"), Json(A("f", "source_epoch")))


def request_rule():
    prior = Exists(N("ag", "has_thinking_budget_request"), "old",
                  Eq(A("old", "requester_key"), request_key()))
    return {
        "name": "qa_request_funded_observation_probe", "area": AREA,
        "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_thinking_budget", "budget"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_experience_episode", "ep"],
                  ["ep", "has_experience_event", "ev"],
                  ["ev", "has_episode_feature", "f"],
                  ["f", "has_outcome_receipt", "receipt"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("budget", "enabled"), L(1.0)),
                     Eq(A("ep", "status"), L("observed")),
                     Eq(A("ev", "status"), L("observed")),
                     Eq(A("receipt", "status"), L("observed")),
                     Eq(A("receipt", "evidence_status"), L("observed")),
                     Eq(A("f", "status"), L("observed")),
                     Eq(A("receipt", "owner_id"), A("ep", "owner_id")),
                     Eq(A("f", "owner_id"), A("ep", "owner_id")),
                     Eq(A("receipt", "episode_id"), A("ep", "episode_id")),
                     Eq(A("receipt", "event_id"), A("ev", "event_id")),
                     Eq(A("receipt", "feature_id"), A("f", "feature_id")),
                     Eq(A("receipt", "source_epoch"), A("f", "source_epoch")),
                     Eq(A("receipt", "model_epoch"), A("f", "model_epoch")),
                     Eq(A("receipt", "frame_epoch"), A("f", "frame_epoch")),
                     Eq(A("f", "source_epoch"), A("ev", "source_epoch")),
                     Eq(A("f", "model_epoch"), A("ev", "model_epoch")),
                     Eq(A("f", "frame_epoch"), A("ev", "frame_epoch")),
                     Eq(A("f", "is_missing"), L(False)),
                     Not(Eq(A("f", "feature_key"), L(None))),
                     Not(Eq(A("f", "feature_value"), L(None))),
                     Gt(A("pol", "max_event_refs"), L(0)),
                     Lt(Count(N("ag", "has_thinking_budget_request")),
                        A("pol", "max_event_refs")),
                     Not(prior)),
        "effects": [
            ["add_node", "req", "ThinkingBudgetRequest", {
                "requester_kind": "qualia_acquisition_probe",
                "requester_key": T(request_key()),
                "source_key": T(A("ev", "event_id")),
                "source_epoch": T(A("f", "source_epoch")),
                "requested_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(Plus(A("mode", "epoch"), L(1))),
                "cost": T(A("pol", "probe_cost")), "status": "pending",
            }],
            ["add_edge", "ag", "has_thinking_budget_request", "req", {}],
            ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
            ["add_edge", "req", "funds_feature_observation", "f", {}],
        ],
    }


def witness_rule():
    prior = Exists(N("ag", "has_qualia_acquisition_witness"), "old",
                  And(Eq(A("old", "feature_id"), A("f", "feature_id")),
                      Eq(A("old", "source_epoch"), A("f", "source_epoch"))))
    attrs = {
        "witness_id": T(Concat(A("ep", "owner_id"), L(":"), A("ev", "event_id"),
                               L(":"), A("f", "feature_id"))),
        "owner_id": T(A("ep", "owner_id")),
        "episode_id": T(A("ep", "episode_id")),
        "event_id": T(A("ev", "event_id")),
        "context_id": T(A("ep", "context_id")),
        "action_id": T(A("ev", "action_id")),
        "frame_id": T(A("ev", "frame_id")),
        "feature_id": T(A("f", "feature_id")),
        "feature_key": T(A("f", "feature_key")),
        "feature_family": T(A("f", "feature_family")),
        "feature_value": T(A("f", "feature_value")),
        "value_kind": T(A("f", "value_kind")),
        "grain": T(A("f", "grain")),
        "consequence_kind": T(A("receipt", "consequence_kind")),
        "consequence_value": T(A("receipt", "consequence_value")),
        "source_epoch": T(A("f", "source_epoch")),
        "model_epoch": T(A("f", "model_epoch")),
        "frame_epoch": T(A("f", "frame_epoch")),
        "status": "observed",
    }
    return {
        "name": "qa_mint_funded_episode_witness", "area": AREA,
        "order": 2, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_experience_episode", "ep"],
                  ["ep", "has_experience_event", "ev"],
                  ["ev", "has_episode_feature", "f"],
                  ["f", "has_outcome_receipt", "receipt"],
                  ["req", "funds_feature_observation", "f"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("req", "status"), L("approved")),
                     Eq(A("ep", "status"), L("observed")),
                     Eq(A("ev", "status"), L("observed")),
                     Eq(A("receipt", "status"), L("observed")),
                     Eq(A("receipt", "evidence_status"), L("observed")),
                     Eq(A("receipt", "owner_id"), A("ep", "owner_id")),
                     Eq(A("receipt", "episode_id"), A("ep", "episode_id")),
                     Eq(A("receipt", "event_id"), A("ev", "event_id")),
                     Eq(A("receipt", "feature_id"), A("f", "feature_id")),
                     Eq(A("receipt", "source_epoch"), A("f", "source_epoch")),
                     Eq(A("receipt", "model_epoch"), A("f", "model_epoch")),
                     Eq(A("receipt", "frame_epoch"), A("f", "frame_epoch")),
                     Not(prior)),
        "effects": [
            ["add_node", "w", "QualiaAcquisitionWitness", attrs],
            ["add_edge", "ag", "has_qualia_acquisition_witness", "w", {}],
            ["add_edge", "w", "witnesses_feature", "f", {}],
            ["add_edge", "w", "witnesses_episode", "ep", {}],
            ["add_edge", "w", "witnesses_event", "ev", {}],
            ["add_edge", "w", "witnesses_outcome", "receipt", {}],
            ["add_edge", "req", "funds_witness", "w", {}],
        ],
    }


def _witness_repeat_matches():
    # Three distinct episode/context witnesses; the third repeats either of
    # the two observed value→consequence relations.
    mapping = Or(
        And(Eq(A("w3", "feature_value"), A("w1", "feature_value")),
            Eq(A("w3", "consequence_value"), A("w1", "consequence_value"))),
        And(Eq(A("w3", "feature_value"), A("w2", "feature_value")),
            Eq(A("w3", "consequence_value"), A("w2", "consequence_value"))))
    return And(
        Eq(A("w1", "status"), L("observed")),
        Eq(A("w2", "status"), L("observed")),
        Eq(A("w3", "status"), L("observed")),
        Eq(A("w1", "owner_id"), A("w2", "owner_id")),
        Eq(A("w1", "owner_id"), A("w3", "owner_id")),
        Eq(A("w1", "feature_key"), A("w2", "feature_key")),
        Eq(A("w1", "feature_key"), A("w3", "feature_key")),
        Eq(A("w1", "feature_family"), A("w2", "feature_family")),
        Eq(A("w1", "feature_family"), A("w3", "feature_family")),
        Eq(A("w1", "model_epoch"), A("w2", "model_epoch")),
        Eq(A("w1", "model_epoch"), A("w3", "model_epoch")),
        Eq(A("w1", "frame_epoch"), A("w2", "frame_epoch")),
        Eq(A("w1", "frame_epoch"), A("w3", "frame_epoch")),
        Lt(A("w1", "event_id"), A("w2", "event_id")),
        Lt(A("w2", "event_id"), A("w3", "event_id")),
        Not(Eq(A("w1", "episode_id"), A("w2", "episode_id"))),
        Not(Eq(A("w1", "episode_id"), A("w3", "episode_id"))),
        Not(Eq(A("w2", "episode_id"), A("w3", "episode_id"))),
        Not(Eq(A("w1", "context_id"), A("w2", "context_id"))),
        Not(Eq(A("w1", "context_id"), A("w3", "context_id"))),
        Not(Eq(A("w2", "context_id"), A("w3", "context_id"))),
        Not(Eq(A("w1", "feature_value"), A("w2", "feature_value"))),
        Not(Eq(A("w1", "consequence_value"), A("w2", "consequence_value"))),
        mapping)


def propose_axis_rule():
    key = candidate_key(A("w1", "owner_id"), A("w1", "feature_key"))
    prior = Exists(N("ag", "has_qualia_axis_candidate"), "old",
                   Eq(A("old", "candidate_key"), key))
    attrs = {
        "candidate_key": T(key),
        "dimension_id": T(dimension_id(A("w1", "owner_id"), A("w1", "feature_key"))),
        "owner_id": T(A("w1", "owner_id")),
        "feature_key": T(A("w1", "feature_key")),
        "feature_family": T(A("w1", "feature_family")),
        "value_kind": T(A("w1", "value_kind")),
        "model_epoch": T(A("w1", "model_epoch")),
        "frame_epoch": T(A("w1", "frame_epoch")),
        "status": "proposed", "support_threshold": 3.0,
        "revision_count": 0.0, "created_epoch": T(A("mode", "epoch")),
    }
    return {
        "name": "qa_propose_axis_after_recurrent_consequence_residual",
        "area": AREA, "order": 10, "latency_class": "background", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_qualia_acquisition_witness", "w1"],
                  ["ag", "has_qualia_acquisition_witness", "w2"],
                  ["ag", "has_qualia_acquisition_witness", "w3"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Lt(Count(N("ag", "has_qualia_axis_candidate")), A("pol", "max_candidates")),
                     Gt(A("pol", "max_event_refs"), L(0)),
                     Lt(Count(N("ag", "has_qualia_acquisition_witness")),
                        A("pol", "max_event_refs")),
                     _witness_repeat_matches(), Not(prior)),
        "effects": [
            ["add_node", "candidate", "QualiaAxisCandidate", attrs],
            ["add_edge", "ag", "has_qualia_axis_candidate", "candidate", {}],
            ["add_edge", "candidate", "has_acquisition_witness", "w1", {}],
            ["add_edge", "candidate", "has_acquisition_witness", "w2", {}],
            ["add_edge", "candidate", "has_acquisition_witness", "w3", {}],
        ],
    }


def attach_later_witness_rule():
    return {
        "name": "qa_attach_same_feature_witness_to_candidate", "area": AREA,
        "order": 11, "latency_class": "background", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  ["ag", "has_qualia_acquisition_witness", "w"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     In(A("candidate", "status"), ["proposed", "validated", "contested"]),
                     Eq(A("candidate", "owner_id"), A("w", "owner_id")),
                     Eq(A("candidate", "feature_key"), A("w", "feature_key")),
                     Not(Exists(N("candidate", "has_acquisition_witness"), "old",
                                Eq(A("old", "witness_id"), A("w", "witness_id"))))),
        "effects": [["add_edge", "candidate", "has_acquisition_witness", "w", {}]],
    }


def _candidate_maps(w1, w2, wn):
    return And(
        Eq(A("w1", "owner_id"), A("candidate", "owner_id")),
        Eq(A("w2", "owner_id"), A("candidate", "owner_id")),
        Eq(A("wn", "owner_id"), A("candidate", "owner_id")),
        Eq(A("w1", "feature_key"), A("candidate", "feature_key")),
        Eq(A("w2", "feature_key"), A("candidate", "feature_key")),
        Eq(A("wn", "feature_key"), A("candidate", "feature_key")),
        Eq(A("w1", "model_epoch"), A("candidate", "model_epoch")),
        Eq(A("wn", "model_epoch"), A("candidate", "model_epoch")),
        Eq(A("w1", "frame_epoch"), A("candidate", "frame_epoch")),
        Eq(A("wn", "frame_epoch"), A("candidate", "frame_epoch")),
        Not(Eq(A("w1", "feature_value"), A("w2", "feature_value"))),
        Not(Eq(A("w1", "consequence_value"), A("w2", "consequence_value"))),
        Or(And(Eq(A("wn", "feature_value"), A("w1", "feature_value")),
               Eq(A("wn", "consequence_value"), A("w1", "consequence_value"))),
           And(Eq(A("wn", "feature_value"), A("w2", "feature_value")),
               Eq(A("wn", "consequence_value"), A("w2", "consequence_value")))))


def validation_rule(positive=True):
    result = "positive" if positive else "negative"
    # The candidate's frozen three recurrence witnesses carry two distinct mappings;
    # fresh validation must repeat one of those mappings in an unused context.
    consistency = And(
        Eq(A("w1", "owner_id"), A("candidate", "owner_id")),
        Eq(A("w2", "owner_id"), A("candidate", "owner_id")),
        Eq(A("wn", "owner_id"), A("candidate", "owner_id")),
        Eq(A("w1", "feature_key"), A("candidate", "feature_key")),
        Eq(A("w2", "feature_key"), A("candidate", "feature_key")),
        Eq(A("wn", "feature_key"), A("candidate", "feature_key")),
        Eq(A("wn", "model_epoch"), A("candidate", "model_epoch")),
        Eq(A("wn", "frame_epoch"), A("candidate", "frame_epoch")),
        Lt(A("w1", "event_id"), A("w2", "event_id")),
        Not(Eq(A("w1", "feature_value"), A("w2", "feature_value"))),
        Not(Eq(A("w1", "consequence_value"), A("w2", "consequence_value"))),
        Or(And(Eq(A("wn", "feature_value"), A("w1", "feature_value")),
               Eq(A("wn", "consequence_value"), A("w1", "consequence_value"))),
           And(Eq(A("wn", "feature_value"), A("w2", "feature_value")),
               Eq(A("wn", "consequence_value"), A("w2", "consequence_value")))))
    prior = Exists(N("candidate", "has_acquisition_validation"), "old",
                   Eq(A("old", "event_id"), A("wn", "event_id")))
    earlier_support = Exists(N("candidate", "has_acquisition_witness"), "earlier",
                             Lt(A("earlier", "event_id"), A("w1", "event_id")))
    support_episode = Exists(N("candidate", "has_acquisition_witness"), "support",
                             Or(Eq(A("support", "episode_id"), A("wn", "episode_id")),
                                Eq(A("support", "context_id"), A("wn", "context_id"))))
    attrs = {
        "event_id": T(A("wn", "event_id")), "episode_id": T(A("wn", "episode_id")),
        "context_id": T(A("wn", "context_id")), "owner_id": T(A("wn", "owner_id")),
        "feature_value": T(A("wn", "feature_value")),
        "observed_consequence": T(A("wn", "consequence_value")),
        "result": result, "revision_round": T(A("candidate", "revision_count")),
        "source_epoch": T(A("wn", "source_epoch")),
        "model_epoch": T(A("wn", "model_epoch")),
        "frame_epoch": T(A("wn", "frame_epoch")),
    }
    where = And(Eq(A("pol", "enabled"), L(1.0)),
                In(A("candidate", "status"), ["proposed", "contested"]),
                consistency,
                Not(support_episode), Not(prior))
    effects = [["add_node", "v", "QualiaAcquisitionValidation", attrs],
               ["add_edge", "candidate", "has_acquisition_validation", "v", {}],
               ["add_edge", "v", "validates_witness", "wn", {}]]
    if not positive:
        contradiction = And(
            Eq(A("w1", "owner_id"), A("candidate", "owner_id")),
            Eq(A("w2", "owner_id"), A("candidate", "owner_id")),
            Eq(A("wn", "owner_id"), A("candidate", "owner_id")),
            Eq(A("w1", "feature_key"), A("candidate", "feature_key")),
            Eq(A("w2", "feature_key"), A("candidate", "feature_key")),
            Eq(A("wn", "feature_key"), A("candidate", "feature_key")),
            Eq(A("wn", "model_epoch"), A("candidate", "model_epoch")),
            Eq(A("wn", "frame_epoch"), A("candidate", "frame_epoch")),
            Lt(A("w1", "event_id"), A("w2", "event_id")),
            Not(Eq(A("w1", "feature_value"), A("w2", "feature_value"))),
            Not(Eq(A("w1", "consequence_value"), A("w2", "consequence_value"))),
            Or(And(Eq(A("wn", "feature_value"), A("w1", "feature_value")),
                   Not(Eq(A("wn", "consequence_value"), A("w1", "consequence_value")))),
               And(Eq(A("wn", "feature_value"), A("w2", "feature_value")),
                   Not(Eq(A("wn", "consequence_value"), A("w2", "consequence_value"))))))
        where = And(Eq(A("pol", "enabled"), L(1.0)),
                    Eq(A("candidate", "status"), L("validated")),
                    Eq(A("dim", "name"), A("candidate", "dimension_id")),
                    contradiction, Not(support_episode), Not(prior), Not(earlier_support))
        effects += [["set_attr", "candidate", "status", "contested"],
                    ["set_attr", "dim", "acquisition_status", "contested"],
                    ["set_attr", "candidate", "revision_count", 1.0]]
    return {
        "name": "qa_record_%s_fresh_outcome_validation" % result,
        "area": AREA, "order": 20 if positive else 21,
        "latency_class": "background", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  *([ ["ag", "has_qualia_dimension", "dim"] ] if not positive else []),
                  ["candidate", "has_acquisition_witness", "w1"],
                  ["candidate", "has_acquisition_witness", "w2"],
                  ["ag", "has_qualia_acquisition_witness", "wn"]],
        "where": where, "effects": effects,
    }


def adoption_rule():
    statuses = ["proposed"]
    round_cond = Eq(A("candidate", "revision_count"), L(0.0))
    attrs = {
        "name": T(A("candidate", "dimension_id")),
        "family": "phenomenal",
        "source": T(Concat(L("experience:"), A("candidate", "feature_key"))),
        "owner_id": T(A("candidate", "owner_id")),
        "seeded": 0.0,
        "acquired": 1.0,
        "acquisition_status": "standing",
        "acquisition_revision": T(A("candidate", "revision_count")),
        "gloss": "Episode distinction supported by fresh observed outcomes.",
    }
    return {
        "name": "qa_adopt_axis_after_two_fresh_contexts",
        "area": AREA, "order": 30,
        "latency_class": "background", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  ["candidate", "has_acquisition_validation", "v1"],
                  ["candidate", "has_acquisition_validation", "v2"],
                  ["ag", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     In(A("candidate", "status"), statuses), round_cond,
                     Eq(A("v1", "result"), L("positive")),
                     Eq(A("v2", "result"), L("positive")),
                     Eq(A("v1", "revision_round"), A("candidate", "revision_count")),
                     Eq(A("v2", "revision_round"), A("candidate", "revision_count")),
                     Not(Eq(A("v1", "event_id"), A("v2", "event_id"))),
                     Not(Eq(A("v1", "context_id"), A("v2", "context_id"))),
                     Not(Eq(A("v1", "episode_id"), A("v2", "episode_id"))),
                     Not(Exists(N("ag", "has_qualia_dimension"), "old_dim",
                                Eq(A("old_dim", "name"), A("candidate", "dimension_id"))))),
        "effects": [["add_node", "dim", "QualiaDimension", attrs],
                    ["add_edge", "ag", "has_qualia_dimension", "dim", {}],
                    ["set_attr", "candidate", "status", "validated"],
                    ["set_attr", "candidate", "validated_epoch", T(A("mode", "epoch"))]],
    }


def restore_after_revision_rule():
    return {
        "name": "qa_restore_axis_after_two_fresh_revision_contexts",
        "area": AREA, "order": 32, "latency_class": "background", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  ["ag", "has_qualia_dimension", "dim"],
                  ["candidate", "has_acquisition_validation", "v1"],
                  ["candidate", "has_acquisition_validation", "v2"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("candidate", "status"), L("contested")),
                     Gt(A("candidate", "revision_count"), L(0.0)),
                     Eq(A("dim", "name"), A("candidate", "dimension_id")),
                     Eq(A("v1", "result"), L("positive")),
                     Eq(A("v2", "result"), L("positive")),
                     Eq(A("v1", "revision_round"), A("candidate", "revision_count")),
                     Eq(A("v2", "revision_round"), A("candidate", "revision_count")),
                     Not(Eq(A("v1", "event_id"), A("v2", "event_id"))),
                     Not(Eq(A("v1", "context_id"), A("v2", "context_id"))),
                     Not(Eq(A("v1", "episode_id"), A("v2", "episode_id")))),
        "effects": [["set_attr", "candidate", "status", "validated"],
                    ["set_attr", "dim", "acquisition_status", "standing"],
                    ["set_attr", "dim", "acquisition_revision", T(A("candidate", "revision_count"))],
                    ["set_attr", "candidate", "validated_epoch", T(A("mode", "epoch"))]],
    }


def acquired_signature_rule():
    prior = Exists(N("ag", "has_signature_source"), "old",
                   And(Eq(A("old", "source_id"), L("qualia_acquisition")),
                       Eq(A("old", "signature_key"),
                          Concat(A("candidate", "candidate_key"), L(":"), A("w", "event_id"))),
                       Eq(A("old", "source_epoch"), A("w", "source_epoch"))))
    dim = A("candidate", "dimension_id")
    coord = Append(Append(Append(Append(Append(L([]), dim), A("w", "value_kind")),
                                  A("w", "feature_value")), L(False)), A("w", "grain"))
    attrs = {
        "schema_version": 1,
        "signature_key": T(Concat(A("candidate", "candidate_key"), L(":"), A("w", "event_id"))),
        "source_id": "qualia_acquisition",
        "source_kind": "acquired_episode_feature",
        "owner_id": T(A("candidate", "owner_id")),
        "source_epoch": T(A("w", "source_epoch")),
        "model_epoch": T(A("w", "model_epoch")),
        "frame_epoch": T(A("w", "frame_epoch")),
        "frame_id": T(A("w", "frame_id")),
        "episode_id": T(A("w", "episode_id")),
        "event_id": T(A("w", "event_id")),
        "evidence_status": "observed",
        "dimension_ids": T(Append(L([]), dim)),
        "coordinates": T(Append(L([]), coord)),
        "standing_coordinates": [], "live_overlay": [], "status": "current",
    }
    return {
        "name": "qa_redecode_acquired_axis_from_episode_witness",
        "area": AREA, "order": 40, "latency_class": "background", "batch": False,
        "match": [["ag", "has_qualia_acquisition_policy", "pol"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  ["candidate", "has_acquisition_witness", "w"],
                  ["w", "witnesses_episode", "ep"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("candidate", "status"), L("validated")),
                     Eq(A("candidate", "owner_id"), A("w", "owner_id")),
                     Eq(A("candidate", "feature_key"), A("w", "feature_key")),
                     Not(prior)),
        "effects": [["add_node", "src", "CognitionSignatureSource", attrs],
                    ["add_edge", "ag", "has_signature_source", "src", {}],
                    ["add_edge", "src", "projects_episode", "ep", {}],
                    ["add_edge", "src", "uses_acquisition_witness", "w", {}]],
    }


def build_seed():
    relations = [
        ("Agent", "has_qualia_acquisition_policy", "QualiaAcquisitionPolicy"),
        ("Agent", "has_experience_episode", "ExperienceEpisode"),
        ("ExperienceEpisode", "has_experience_event", "ExperienceEvent"),
        ("ExperienceEvent", "has_episode_feature", "ExperienceFeatureObservation"),
        ("ExperienceFeatureObservation", "has_outcome_receipt", "ExperienceOutcomeReceipt"),
        ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("ThinkingBudgetRequest", "funds_feature_observation", "ExperienceFeatureObservation"),
        ("Agent", "has_qualia_acquisition_witness", "QualiaAcquisitionWitness"),
        ("QualiaAcquisitionWitness", "witnesses_feature", "ExperienceFeatureObservation"),
        ("QualiaAcquisitionWitness", "witnesses_episode", "ExperienceEpisode"),
        ("QualiaAcquisitionWitness", "witnesses_event", "ExperienceEvent"),
        ("QualiaAcquisitionWitness", "witnesses_outcome", "ExperienceOutcomeReceipt"),
        ("Agent", "has_qualia_axis_candidate", "QualiaAxisCandidate"),
        ("QualiaAxisCandidate", "has_acquisition_witness", "QualiaAcquisitionWitness"),
        ("QualiaAxisCandidate", "has_acquisition_validation", "QualiaAcquisitionValidation"),
        ("QualiaAcquisitionValidation", "validates_witness", "QualiaAcquisitionWitness"),
        ("Agent", "has_qualia_dimension", "QualiaDimension"),
        ("Agent", "has_signature_source", "CognitionSignatureSource"),
        ("CognitionSignatureSource", "projects_episode", "ExperienceEpisode"),
        ("CognitionSignatureSource", "uses_acquisition_witness", "QualiaAcquisitionWitness"),
    ]
    rules = [request_rule(), witness_rule(), propose_axis_rule(),
             validation_rule(True), validation_rule(False),
             adoption_rule(), restore_after_revision_rule(),
             acquired_signature_rule()]
    return {
        "id": "qualia_acquisition", "version": "1.0.0",
        "depends_on": ["experience_signature", "thinking_budget", "qualia_space"],
        "self_load_only": True, "area": AREA,
        "description": (
            "P7.03: funded graph-rule acquisition of phenomenal dimensions from "
            "recurrent, owner-scoped observed feature/consequence episodes, with "
            "fresh validation, retained counterevidence, revision and re-decoding."),
        "microtheory": {"name": AREA,
                        "description": "Acquire only source-witnessed distinctions that predict fresh consequences."},
        "nodes": [{"local_id": 0, "type": "QualiaAcquisitionPolicy",
                   "attrs": {"name": "qualia_acquisition_policy", "enabled": 0.0,
                             "recurrence_episodes": 3.0, "fresh_validation_episodes": 2.0,
                             "max_candidates": 32.0, "max_event_refs": 200.0,
                             "max_grain_values": 8.0, "probe_cost": 1.0}}],
        "edges": [{"src": {"role": "agent_root"},
                   "type": "has_qualia_acquisition_policy", "tgt": {"local": 0},
                   "attrs": {}}],
        "productions": [
            {"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
             "src": {"type": src, "var": "src"}, "edge_type": edge,
             "tgt": {"type": tgt, "var": "tgt"}}
            for src, edge, tgt in relations
        ],
        "rules": rules,
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
