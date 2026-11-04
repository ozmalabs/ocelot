#!/usr/bin/env python3
"""Generate the disabled, self-load-only P28 fixed-frame policy seed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.ousiometrics.geometry_reference import PAPER_EQ4_DISPLAY

OUT = ROOT / "seeds" / "ousiometric_frames.json"
AREA = "ousiometric_frames"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Exists(source, name, predicate): return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}
def N(node, edge): return {"type": "Neighbours", "node": V(node), "edge_type": edge, "any_type": False}
def Count(source): return {"type": "Count", "source": source}
def Vec(items): return {"type": "Vec", "items": items}
def Dot(a, b): return {"type": "Dot", "a": a, "b": b}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*items): return {"type": "Times", "items": list(items)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Round(value): return {"type": "Round", "value": value, "ndigits": L(0)}
def IndexAt(seq, index): return {"type": "IndexAt", "seq": seq, "index": L(index)}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def In(member, container): return {"type": "In", "member": member, "container": container}
def Filter(source, name, predicate): return {"type": "Filter", "source": source, "var_name": name, "predicate": predicate}
def SortBy(source, name, key): return {"type": "SortBy", "source": source, "var_name": name, "key": key}
def IndexAt(seq, index): return {"type": "IndexAt", "seq": seq, "index": L(index)}
def Abs(arg): return {"type": "Abs", "arg": arg}
def Concat(*parts): return {"type": "StringConcat", "parts": list(parts)}
def Exists(source, name, predicate): return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}


def coordinate_range_guard(index):
    value = IndexAt(A("ev", "coordinates"), index)
    return And(Gte(value, L(-0.5)), Lte(value, L(0.5)))


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _random_rotation() -> np.ndarray:
    rng = np.random.default_rng(2805)
    q, r = np.linalg.qr(rng.normal(size=(3, 3)))
    q = q @ np.diag(np.sign(np.diag(r)))
    if np.linalg.det(q) < 0:
        q[:, -1] *= -1
    return q


def _frames():
    base = np.eye(3, dtype=np.float64)
    random = _random_rotation()
    definitions = [
        ("shared_basis", "shared-coordinate-basis", base, "displayed source basis"),
        ("eq4_rotation", "published-Eq4-rotation", PAPER_EQ4_DISPLAY, "rounded Eq. 4 display coefficients; mathematical reference only"),
        ("random_rotation_dev", "random-basis", random, "seeded QR rotation; development-control basis"),
    ]
    frames = []
    for name, kind, forward, note in definitions:
        inv = np.linalg.inv(forward)
        for precision in (64, 8):
            for metric in ("fixed_l1", "transported_l1"):
                frame_id = f"{name}_{precision}bit_{metric}"
                matrix = forward.tolist()
                inverse = inv.tolist()
                frames.append({
                    "frame_id": frame_id,
                    "frame_kind": kind,
                    "frame_epoch": 1.0,
                    "source_units": "shared numeric feature coordinates, centered range [-0.5,0.5]",
                    "target_units": "linear coordinates; bounded quantizer range [-1,1]",
                    "forward_direction": "source_to_frame",
                    "inverse_direction": "frame_to_source",
                    "forward_matrix": matrix,
                    "inverse_matrix": inverse,
                    "map_digest": _digest({"forward": matrix, "inverse": inverse}),
                    "precision_bits_per_coordinate": float(precision),
                    "coordinate_count": 3.0,
                    "forward_inverse_map_bits": 18.0 * 64.0,
                    "metric_policy_bits": 64.0,
                    "coordinates_bits": 3.0 * precision,
                    "total_representation_bits": 18.0 * 64.0 + 64.0 + 3.0 * precision,
                    "quantizer_low": -1.0,
                    "quantizer_high": 1.0,
                    "quantizer": "uniform-round-half-to-even" if precision == 8 else "identity-float64",
                    "metric_condition": metric,
                    "frame_note": note,
                    "calibration_status": "synthetic_shared_numeric_coordinates_only",
                    "enabled": False,
                })
    return frames


def _dot_row(row, vector):
    return Dot(Vec([L(float(value)) for value in row]), vector)


def _quantize(value):
    # q(x)=round((x+1)*127.5, 0)/127.5 - 1 for a 256-level [-1,1] grid.
    return Minus(Div(Round(Times(Plus(value, L(1.0)), L(127.5))), L(127.5)), L(1.0))


def _project_rule(frame):
    rows = frame["forward_matrix"]
    exact = Vec([_dot_row(row, A("ev", "coordinates")) for row in rows])
    quantized = Vec([_quantize(_dot_row(row, A("ev", "coordinates"))) for row in rows])
    projected = exact if frame["precision_bits_per_coordinate"] == 64.0 else quantized
    frame_id = frame["frame_id"]
    projection_attrs = {
        "projection_id": T({"type": "StringConcat", "parts": [A("ev", "event_id"), L(":"), L(frame_id)]}),
        "owner_id": T(A("ev", "owner_id")),
        "event_id": T(A("ev", "event_id")),
        "source_epoch": T(A("ev", "source_epoch")),
        "model_epoch": T(A("ev", "model_epoch")),
        "frame_epoch": T(A("pol", "frame_epoch")),
        "frame_id": frame_id,
        "frame_kind": T(A("frame", "frame_kind")),
        "source_coordinates": T(A("ev", "coordinates")),
        "projected_coordinates": T(projected),
        "forward_matrix": T(A("frame", "forward_matrix")),
        "inverse_matrix": T(A("frame", "inverse_matrix")),
        "map_digest": T(A("frame", "map_digest")),
        "precision_bits_per_coordinate": T(A("frame", "precision_bits_per_coordinate")),
        "total_representation_bits": T(A("frame", "total_representation_bits")),
        "quantizer": T(A("frame", "quantizer")),
        "metric_condition": T(A("frame", "metric_condition")),
        "status": "current",
        "evidence_status": "observed",
        "heldout_used_for_selection": False,
    }


    return {
        "name": f"ouf_project_shared_event_{frame_id}",
        "area": AREA,
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["ag", "has_ousiometric_frame_policy", "pol"],
            ["pol", "uses_frame", "frame"],
            ["ag", "has_ousiometric_raw_evidence", "ev"],
        ],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("pol", "owner_id"), A("ev", "owner_id")),
            Eq(A("pol", "source_epoch"), A("ev", "source_epoch")),
            Eq(A("pol", "model_epoch"), A("ev", "model_epoch")),
            Eq(A("pol", "assigned_frame_id"), L(frame_id)),
            Eq(A("frame", "frame_id"), L(frame_id)),
            Eq(A("pol", "frame_epoch"), A("frame", "frame_epoch")),
            Eq(A("ev", "evidence_status"), L("observed")),
            Eq(A("ev", "coordinate_encoding"), L("finite_f64_v1")),
            Eq(Count(A("ev", "coordinates")), L(3)),
            coordinate_range_guard(0), coordinate_range_guard(1), coordinate_range_guard(2),
            Not(Exists(N("ev", "has_frame_projection"), "old",
                       And(Eq(A("old", "frame_id"), L(frame_id)),
                           Eq(A("old", "event_id"), A("ev", "event_id")),
                           Eq(A("old", "frame_epoch"), A("pol", "frame_epoch"))))),
        ),
        "effects": [
            ["add_node", "projection", "OusiometricFrameProjection", projection_attrs],
            ["add_edge", "ag", "has_ousiometric_frame_projection", "projection", {}],
            ["add_edge", "ev", "has_frame_projection", "projection", {}],
            ["add_edge", "projection", "retains_source", "ev", {}],
            ["add_edge", "projection", "uses_frame", "frame", {}],
        ],
    }


def _audit_projection_rule():
    """Consume retained-source and inverse witnesses before adapter use."""
    round_trip = [Lte(Abs(Minus(
        Dot(IndexAt(A("frame", "inverse_matrix"), i),
            Vec([IndexAt(IndexAt(A("frame", "forward_matrix"), k), j)
                 for k in range(3)])),
        L(1.0 if i == j else 0.0))), L(1e-9))
        for i in range(3) for j in range(3)]
    return {
        "name": "ouf_verify_projection_source_and_inverse_witness",
        "area": AREA, "order": 2, "latency_class": "hard_realtime", "batch": False,
        "match": [["projection", "retains_source", "ev"],
                  ["projection", "uses_frame", "frame"]],
        "where": And(Eq(A("projection", "status"), L("current")),
                     Eq(A("projection", "event_id"), A("ev", "event_id")),
                     Eq(A("projection", "owner_id"), A("ev", "owner_id")),
                     Eq(A("projection", "source_epoch"), A("ev", "source_epoch")),
                     Eq(A("projection", "model_epoch"), A("ev", "model_epoch")),
                     Eq(A("projection", "frame_epoch"), A("frame", "frame_epoch")),
                     Eq(A("projection", "source_coordinates"), A("ev", "coordinates")),
                     Eq(A("projection", "inverse_matrix"), A("frame", "inverse_matrix")),
                     Eq(A("projection", "forward_matrix"), A("frame", "forward_matrix")),
                     Eq(A("projection", "map_digest"), A("frame", "map_digest")),
                     Eq(Count(A("projection", "projected_coordinates")), L(3)),
                     *round_trip),
        "effects": [["set_attr", "projection", "status", "verified_current"]],
    }


def _metric_score(query, memory, frame):
    query_values = A(query, "projected_coordinates")
    memory_values = A(memory, "projected_coordinates")
    if frame["metric_condition"] == "transported_l1":
        query_values = Vec([Dot(IndexAt(A("frame", "inverse_matrix"), i), query_values)
                            for i in range(3)])
        memory_values = Vec([Dot(IndexAt(A("frame", "inverse_matrix"), i), memory_values)
                             for i in range(3)])
    return Plus(*(Abs(Minus(IndexAt(query_values, i), IndexAt(memory_values, i)))
                  for i in range(3)))


def _metric_candidate_rule(frame):
    frame_id = frame["frame_id"]
    score = _metric_score("query", "memory", frame)
    candidate_key = Concat(A("query", "query_id"), L(":"), A("memory", "event_id"))
    prior = Exists(N("ag", "has_ousiometric_metric_candidate"), "old",
                   Eq(A("old", "candidate_key"), candidate_key))
    return {
        "name": f"ouf_score_native_l1_memory_{frame_id}", "area": AREA,
        "order": 5, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_ousiometric_frame_policy", "pol"],
                  ["pol", "uses_frame", "frame"],
                  ["ag", "has_ousiometric_metric_query", "query"],
                  ["ag", "has_ousiometric_metric_memory", "memory"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("pol", "assigned_frame_id"), L(frame_id)),
                     Eq(A("frame", "frame_id"), L(frame_id)),
                     Eq(A("query", "frame_id"), L(frame_id)),
                     Eq(A("memory", "frame_id"), L(frame_id)),
                     Eq(A("query", "owner_id"), A("pol", "owner_id")),
                     Eq(A("memory", "owner_id"), A("pol", "owner_id")),
                     Eq(A("query", "frame_epoch"), A("pol", "frame_epoch")),
                     Eq(A("memory", "frame_epoch"), A("pol", "frame_epoch")),
                     Eq(A("memory", "evidence_status"), L("observed")),
                     In(A("memory", "action_id"), A("query", "legal_actions")),
                     Not(prior)),
        "effects": [
            ["add_node", "candidate", "OusiometricMetricCandidate", {
                "candidate_key": T(candidate_key), "query_id": T(A("query", "query_id")),
                "event_id": T(A("memory", "event_id")), "owner_id": T(A("query", "owner_id")),
                "frame_id": frame_id, "frame_epoch": T(A("query", "frame_epoch")),
                "metric_condition": frame["metric_condition"],
                "action_id": T(A("memory", "action_id")),
                "consequence": T(A("memory", "consequence")),
                "distance": T(score), "status": "scored"}],
            ["add_edge", "ag", "has_ousiometric_metric_candidate", "candidate", {}],
            ["add_edge", "query", "has_metric_candidate", "candidate", {}],
            ["add_edge", "candidate", "uses_metric_memory", "memory", {}],
        ],
    }


def _metric_recall_rule():
    better = Exists(N("query", "has_metric_candidate"), "other",
                    And(Eq(A("other", "query_id"), A("query", "query_id")),
                        Or(Lt(A("other", "distance"), A("candidate", "distance")),
                           And(Eq(A("other", "distance"), A("candidate", "distance")),
                               Lt(A("other", "event_id"), A("candidate", "event_id"))))))
    return {
        "name": "ouf_emit_nearest_native_metric_recall", "area": AREA,
        "order": 6, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_ousiometric_metric_query", "query"],
                  ["query", "has_metric_candidate", "candidate"]],
        "where": And(Eq(A("candidate", "status"), L("scored")),
                     Eq(Count(N("query", "has_metric_candidate")),
                        A("query", "candidate_count_expected")),
                     Not(better),
                     Not(Exists(N("ag", "has_ousiometric_metric_recall"), "old",
                                Eq(A("old", "query_id"), A("query", "query_id"))))),
        "effects": [
            ["add_node", "recall", "OusiometricMetricRecall", {
                "query_id": T(A("query", "query_id")), "event_id": T(A("candidate", "event_id")),
                "owner_id": T(A("candidate", "owner_id")), "frame_id": T(A("candidate", "frame_id")),
                "frame_epoch": T(A("candidate", "frame_epoch")),
                "metric_condition": T(A("candidate", "metric_condition")),
                "action_id": T(A("candidate", "action_id")),
                "consequence": T(A("candidate", "consequence")),
                "distance": T(A("candidate", "distance")), "status": "retrieved"}],
            ["add_edge", "ag", "has_ousiometric_metric_recall", "recall", {}],
            ["add_edge", "recall", "retrieves_candidate", "candidate", {}],
        ],
    }


def _metric_consume_rule():
    return {
        "name": "ouf_consume_verified_nearest_metric_recall",
        "area": AREA, "order": 7, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_ousiometric_metric_query", "query"],
                  ["ag", "has_ousiometric_metric_recall", "recall"]],
        "where": And(Eq(A("recall", "status"), L("retrieved")),
                     Eq(A("recall", "query_id"), A("query", "query_id")),
                     Eq(A("recall", "owner_id"), A("query", "owner_id")),
                     Eq(A("recall", "frame_id"), A("query", "frame_id")),
                     In(A("recall", "action_id"), A("query", "legal_actions"))),
        "effects": [["set_attr", "recall", "status", "consumed"]],
    }


def _metric_action_option_rule():
    better = Exists(N("query", "has_metric_candidate"), "other",
        And(Eq(A("other", "query_id"), A("query", "query_id")),
            Eq(A("other", "action_id"), A("candidate", "action_id")),
            Or(Lt(A("other", "distance"), A("candidate", "distance")),
               And(Eq(A("other", "distance"), A("candidate", "distance")),
                   Lt(A("other", "event_id"), A("candidate", "event_id"))))))
    prior = Exists(N("query", "has_action_option"), "old",
                   Eq(A("old", "action_id"), A("candidate", "action_id")))
    return {
        "name": "ouf_emit_nearest_receipt_per_legal_action", "area": AREA,
        "order": 8, "latency_class": "hard_realtime", "batch": False,
        "match": [["query", "has_metric_candidate", "candidate"]],
        "where": And(Eq(A("query", "goal_enabled"), L(True)),
                     Eq(A("candidate", "status"), L("scored")),
                     Eq(Count(N("query", "has_metric_candidate")),
                        A("query", "candidate_count_expected")),
                     Not(better), Not(prior)),
        "effects": [
            ["add_node", "option", "OusiometricMetricActionOption", {
                "query_id": T(A("query", "query_id")),
                "option_id": T(Concat(A("query", "query_id"), L(":"), A("candidate", "action_id"))),
                "owner_id": T(A("candidate", "owner_id")), "frame_id": T(A("candidate", "frame_id")),
                "frame_epoch": T(A("candidate", "frame_epoch")),
                "action_id": T(A("candidate", "action_id")),
                "consequence": T(A("candidate", "consequence")),
                "distance": T(A("candidate", "distance")), "status": "predicted"}],
            ["add_edge", "query", "has_action_option", "option", {}],
            ["add_edge", "option", "uses_metric_candidate", "candidate", {}],
        ],
    }


def _metric_goal_decision_rule():
    better = Exists(N("query", "has_action_option"), "other",
        And(Or(Lt(Abs(Minus(IndexAt(A("other", "consequence"), 0), A("query", "goal_value"))),
                   Abs(Minus(IndexAt(A("option", "consequence"), 0), A("query", "goal_value")))),
               And(Eq(Abs(Minus(IndexAt(A("other", "consequence"), 0), A("query", "goal_value"))),
                      Abs(Minus(IndexAt(A("option", "consequence"), 0), A("query", "goal_value")))),
                   Lt(A("other", "action_id"), A("option", "action_id"))))))
    prior = Exists(N("ag", "has_ousiometric_metric_action_decision"), "old",
                   Eq(A("old", "query_id"), A("query", "query_id")))
    return {
        "name": "ouf_choose_goal_closest_verified_native_outcome", "area": AREA,
        "order": 9, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_ousiometric_metric_query", "query"],
                  ["query", "has_action_option", "option"]],
        "where": And(Eq(A("query", "goal_enabled"), L(True)),
                     Eq(A("option", "status"), L("predicted")),
                     Eq(Count(N("query", "has_action_option")),
                        A("query", "expected_action_count")),
                     Not(better), Not(prior)),
        "effects": [
            ["add_node", "decision", "OusiometricMetricActionDecision", {
                "query_id": T(A("query", "query_id")), "owner_id": T(A("query", "owner_id")),
                "frame_id": T(A("query", "frame_id")),
                "action_id": T(A("option", "action_id")),
                "predicted_consequence": T(A("option", "consequence")),
                "goal_value": T(A("query", "goal_value")),
                "goal_error": T(Abs(Minus(IndexAt(A("option", "consequence"), 0), A("query", "goal_value")))),
                "status": "selected"}],
            ["add_edge", "ag", "has_ousiometric_metric_action_decision", "decision", {}],
            ["add_edge", "query", "selected_action", "decision", {}],
            ["add_edge", "decision", "selects_option", "option", {}],
        ],
    }


def _metric_action_consume_rule():
    return {
        "name": "ouf_consume_goal_selected_legal_action", "area": AREA,
        "order": 10, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_ousiometric_metric_query", "query"],
                  ["query", "selected_action", "decision"]],
        "where": And(Eq(A("decision", "status"), L("selected")),
                     Eq(A("decision", "query_id"), A("query", "query_id")),
                     In(A("decision", "action_id"), A("query", "legal_actions"))),
        "effects": [["set_attr", "decision", "status", "consumed"]],
    }


def build_seed():
    frames = _frames()
    policy_id = 0
    nodes = [{"local_id": policy_id, "type": "OusiometricFramePolicy", "attrs": {
        "name": "p28_ousiometric_frame_policy", "enabled": 0.0,
        "owner_id": "", "source_epoch": -1.0, "model_epoch": -1.0,
        "assigned_frame_id": "", "frame_epoch": 1.0,
        "source_epoch": 0.0, "model_epoch": 0.0,
        "aggregate_map_bits": 1152.0,
        "metric_policy_bits": 64.0,
        "full_precision_total_bits": 1408.0,
        "eight_bit_total_bits": 1240.0,
        "max_coordinates": 3.0,
        "input_range_low": -0.5, "input_range_high": 0.5,
        "default_off": True,
    }}]
    frame_edges = []
    for offset, frame in enumerate(frames, start=1):
        nodes.append({"local_id": offset, "type": "OusiometricFrame", "attrs": frame})
        frame_edges.append({"src": {"local": policy_id}, "type": "uses_frame", "tgt": {"local": offset}, "attrs": {}})
    relations = [
        ("Agent", "has_ousiometric_frame_policy", "OusiometricFramePolicy"),
        ("OusiometricFramePolicy", "uses_frame", "OusiometricFrame"),
        ("Agent", "has_ousiometric_raw_evidence", "OusiometricRawEvidence"),
        ("Agent", "has_ousiometric_frame_projection", "OusiometricFrameProjection"),
        ("OusiometricRawEvidence", "has_frame_projection", "OusiometricFrameProjection"),
        ("OusiometricFrameProjection", "retains_source", "OusiometricRawEvidence"),
        ("OusiometricFrameProjection", "uses_frame", "OusiometricFrame"),
        ("CommonTargetEvidence", "uses_ousiometric_projection", "OusiometricFrameProjection"),
        ("Agent", "has_ousiometric_metric_query", "OusiometricMetricQuery"),
        ("Agent", "has_ousiometric_metric_memory", "OusiometricMetricMemory"),
        ("Agent", "has_ousiometric_metric_candidate", "OusiometricMetricCandidate"),
        ("Agent", "has_ousiometric_metric_recall", "OusiometricMetricRecall"),
        ("OusiometricMetricQuery", "has_metric_candidate", "OusiometricMetricCandidate"),
        ("OusiometricMetricCandidate", "uses_metric_memory", "OusiometricMetricMemory"),
        ("OusiometricMetricRecall", "retrieves_candidate", "OusiometricMetricCandidate"),
        ("Agent", "has_ousiometric_metric_action_decision", "OusiometricMetricActionDecision"),
        ("OusiometricMetricQuery", "has_action_option", "OusiometricMetricActionOption"),
        ("OusiometricMetricActionOption", "uses_metric_candidate", "OusiometricMetricCandidate"),
        ("OusiometricMetricQuery", "selected_action", "OusiometricMetricActionDecision"),
        ("OusiometricMetricActionDecision", "selects_option", "OusiometricMetricActionOption"),
        ("OusiometricMetricMemory", "uses_projection", "OusiometricFrameProjection"),
        ("OusiometricMetricQuery", "uses_projection", "OusiometricFrameProjection"),
        ("ExperienceEvent", "uses_ousiometric_projection", "OusiometricFrameProjection"),
        ("ExperienceFeatureObservation", "derived_from_frame_projection", "OusiometricFrameProjection"),
    ]
    productions = [
        {"provenance": f"seed:{AREA}:{edge}:{src}:{dst}", "src": {"type": src, "var": "src"},
         "edge_type": edge, "tgt": {"type": dst, "var": "tgt"}}
        for src, edge, dst in relations
    ]
    stale = {
        "name": "ouf_invalidate_projection_after_frame_epoch_change",
        "area": AREA, "order": 3, "latency_class": "background", "batch": False,
        "match": [["ag", "has_ousiometric_frame_policy", "pol"],
                  ["ag", "has_ousiometric_frame_projection", "projection"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("projection", "status"), L("verified_current")),
                      Not(Eq(A("projection", "frame_epoch"), A("pol", "frame_epoch")))),
        "effects": [["set_attr", "projection", "status", "stale"],
                    ["set_attr", "projection", "stale_reason", "frame_epoch_changed"]],
    }
    return {
        "id": AREA, "version": "1.0.0", "depends_on": ["core"],
        "self_load_only": True, "area": AREA,
        "description": "P28 disabled experimental fixed frames with full inverse/source provenance and equal-capacity 8/64-bit apertures.",
        "microtheory": {"name": AREA, "description": "A frame is a reversible view over retained observations; it is not a source of new evidence."},
        "nodes": nodes,
        "edges": [{"src": {"role": "agent_root"}, "type": "has_ousiometric_frame_policy", "tgt": {"local": policy_id}, "attrs": {}}] + frame_edges,
        "productions": productions,
        "rules": [_project_rule(frame) for frame in frames] + [_audit_projection_rule(),
                  *[_metric_candidate_rule(frame) for frame in frames],
                  _metric_recall_rule(), _metric_consume_rule(),
                  _metric_action_option_rule(), _metric_goal_decision_rule(),
                  _metric_action_consume_rule(), stale],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(OUT)
