#!/usr/bin/env python3
"""Generate funded, regular-window escalation into the existing TimeInfer rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "temporal_escalation.json"
AREA = "temporal_escalation"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def T(x): return {"__term__": x}
def Count(x): return {"type": "Count", "source": x}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Plus(a, b): return {"type": "Plus", "items": [a, b]}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(a, b): return {"type": "Times", "items": [a, b]}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Abs(arg): return {"type": "Abs", "arg": arg}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(source, var, predicate): return {"type": "Filter", "source": source, "var_name": var, "predicate": predicate}
def MapList(source, var, value): return {"type": "MapList", "source": source, "var_name": var, "value": value}
def SortBy(source, var, key): return {"type": "SortBy", "source": source, "var_name": var, "key": key}
def IndexAt(seq, index): return {"type": "IndexAt", "seq": seq, "index": index}
def TimeInfer(win, field):
    return {"type": "TimeInfer", "sequence": A(win, "frames"),
            "codebook_type": "ShapeSignature", "max_b": 8, "field": field}


def assemble_event_window_rule():
    event_set = Filter(N("ag", "has_temporal_frame_event"), "event",
                       And(Eq(A("event", "owner_id"), A("seal", "owner_id")),
                           Eq(A("event", "window_id"), A("seal", "window_id")),
                           Eq(A("event", "source_epoch"), A("seal", "source_epoch")),
                           Eq(A("event", "status"), L("observed"))))
    events = MapList(event_set, "unordered_event", V("unordered_event"))
    ordered = SortBy(events, "ordered_event", A("ordered_event", "sequence_index"))
    count = Count(events)
    index_values = MapList(ordered, "ordered_event", A("ordered_event", "sequence_index"))
    timestamps = MapList(ordered, "ordered_event", A("ordered_event", "timestamp"))
    first_index, second_index = IndexAt(index_values, L(0)), IndexAt(index_values, L(1))
    first_time, second_time = IndexAt(timestamps, L(0)), IndexAt(timestamps, L(1))
    period = Div(Minus(second_time, first_time), Minus(second_index, first_index))
    expected_for_event = Plus(first_time, Times(Minus(A("event", "sequence_index"), first_index), period))
    bad_timestamps = Filter(events, "event",
                            Not(Lte(Abs(Minus(A("event", "timestamp"), expected_for_event)),
                                    A("pol", "timestamp_tolerance"))))
    bad_dimensions = Filter(events, "event", Not(Eq(A("event", "dim_types"), A("seal", "dim_types"))))
    last_index = IndexAt(index_values, Minus(count, L(1)))
    complete = Eq(count, A("seal", "expected_frame_count"))
    identity = Exists(N("ag", "has_temporal_window"), "old",
                      And(Eq(A("old", "owner_id"), A("seal", "owner_id")),
                          Eq(A("old", "window_id"), A("seal", "window_id")),
                          Eq(A("old", "source_epoch"), A("seal", "source_epoch"))))
    regular = And(Gt(period, L(0)), Eq(Count(bad_timestamps), L(0)),
                  Eq(Count(bad_dimensions), L(0)),
                  Eq(Minus(last_index, first_index), Minus(count, L(1))))
    return {"name": "te_assemble_sealed_measured_frame_events", "area": AREA, "order": 0,
            "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_temporal_escalation_policy", "pol"],
                      ["ag", "has_temporal_frame_window_seal", "seal"],
                      ["seal", "seals_temporal_observation", "source"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("seal", "status"), L("closed")),
                         Eq(A("source", "dim_checked"), L(1)),
                         Eq(A("source", "dim_explained"), L(0)),
                         Gte(count, L(3)), Lte(count, L(64)), complete, Not(identity)),
            "effects": [["add_node", "win", "TemporalSequenceWindow", {
                            "window_id": T(A("seal", "window_id")),
                            "owner_id": T(A("seal", "owner_id")),
                            "source_epoch": T(A("seal", "source_epoch")),
                            "first_event_id": T(IndexAt(MapList(ordered, "event", A("event", "event_id")), L(0))),
                            "last_event_id": T(IndexAt(MapList(ordered, "event", A("event", "event_id")), Minus(count, L(1)))),
                            "frames": T(MapList(ordered, "event", A("event", "frame"))),
                            "event_ids": T(MapList(ordered, "event", A("event", "event_id"))),
                            "timestamps": T(timestamps), "dim_types": T(A("seal", "dim_types")),
                            "expected_frame_count": T(A("seal", "expected_frame_count")),
                            "regular_sampling": T(regular), "status": "ready"}],
                        ["add_edge", "ag", "has_temporal_window", "win", {}],
                        ["add_edge", "win", "escalates_observation", "source", {}],
                        ["add_edge", "win", "assembled_from_seal", "seal", {}]]}


def refuse_incomplete_event_window_rule():
    events = Filter(N("ag", "has_temporal_frame_event"), "event",
                    And(Eq(A("event", "owner_id"), A("seal", "owner_id")),
                        Eq(A("event", "window_id"), A("seal", "window_id")),
                        Eq(A("event", "source_epoch"), A("seal", "source_epoch")),
                        Eq(A("event", "status"), L("observed"))))
    return {"name": "te_refuse_incomplete_sealed_event_window", "area": AREA, "order": 0,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_temporal_escalation_policy", "pol"],
                      ["ag", "has_temporal_frame_window_seal", "seal"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("seal", "status"), L("closed")),
                         Not(Eq(Count(events), A("seal", "expected_frame_count"))),
                         Not(Exists(N("ag", "has_temporal_window"), "win",
                                    And(Eq(A("win", "owner_id"), A("seal", "owner_id")),
                                        Eq(A("win", "window_id"), A("seal", "window_id")),
                                        Eq(A("win", "source_epoch"), A("seal", "source_epoch"))))),
                         ),
            "effects": [["set_attr", "seal", "status", "incomplete"]]}


def refuse_event_window_size_rules():
    events = Filter(N("ag", "has_temporal_frame_event"), "event",
                    And(Eq(A("event", "owner_id"), A("seal", "owner_id")),
                        Eq(A("event", "window_id"), A("seal", "window_id")),
                        Eq(A("event", "source_epoch"), A("seal", "source_epoch")),
                        Eq(A("event", "status"), L("observed"))))
    base = [["ag", "has_temporal_escalation_policy", "pol"],
            ["ag", "has_temporal_frame_window_seal", "seal"]]
    return [
        {"name": "te_refuse_short_sealed_event_window", "area": AREA, "order": 0,
         "latency_class": "hard_realtime", "match": base,
         "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("seal", "status"), L("closed")),
                      Eq(Count(events), A("seal", "expected_frame_count")),
                      Lt(Count(events), L(3))),
         "effects": [["set_attr", "seal", "status", "insufficient_witness"]]},
        {"name": "te_refuse_oversized_sealed_event_window", "area": AREA, "order": 0,
         "latency_class": "hard_realtime", "match": base,
         "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("seal", "status"), L("closed")),
                      Eq(Count(events), A("seal", "expected_frame_count")),
                      Gt(Count(events), L(64))),
         "effects": [["set_attr", "seal", "status", "unsupported_window_size"]]},
    ]


def request_rule():
    existing = Exists(N("ag", "has_thinking_budget_request"), "old",
                      And(Eq(A("old", "window_id"), A("win", "window_id")),
                          Eq(A("old", "owner_id"), A("win", "owner_id")),
                          Eq(A("old", "first_event_id"), A("win", "first_event_id")),
                          Eq(A("old", "last_event_id"), A("win", "last_event_id")),
                          Eq(A("old", "source_epoch"), A("win", "source_epoch"))))
    return {"name": "te_request_funded_regular_window", "area": AREA, "order": 1,
            "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_temporal_escalation_policy", "pol"],
                      ["ag", "has_temporal_window", "win"],
                      ["win", "escalates_observation", "source"],
                      ["ag", "has_thinking_budget", "budget"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("budget", "enabled"), L(1.0)),
                         Eq(A("win", "status"), L("ready")),
                         Eq(A("source", "dim_checked"), L(1)),
                         Eq(A("source", "dim_explained"), L(0)),
                         Eq(A("win", "regular_sampling"), L(True)),
                         Gte(Count(A("win", "frames")), L(3)),
                         Lt(Count(A("win", "frames")), L(65)),
                         Not(existing)),
            "effects": [["add_node", "req", "ThinkingBudgetRequest", {
                            "requester_kind": "temporal_escalation",
                            "requester_key": T(A("win", "window_id")),
                            "window_id": T(A("win", "window_id")),
                            "owner_id": T(A("win", "owner_id")),
                            "first_event_id": T(A("win", "first_event_id")),
                            "last_event_id": T(A("win", "last_event_id")),
                            "source_epoch": T(A("win", "source_epoch")),
                            "cost": T(A("pol", "step_cost")), "status": "pending"}],
                        ["add_edge", "ag", "has_thinking_budget_request", "req", {}],
                        ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
                        ["add_edge", "win", "has_temporal_escalation_request", "req", {}]]}


def refusal_rules():
    return [
        {"name": "te_refuse_irregular_window", "area": AREA, "order": 0,
         "latency_class": "hard_realtime",
         "match": [["ag", "has_temporal_escalation_policy", "pol"], ["ag", "has_temporal_window", "win"]],
         "where": And(Eq(A("pol", "enabled"), L(1.0)), Eq(A("win", "status"), L("ready")),
                      Eq(A("win", "regular_sampling"), L(False))),
         "effects": [["set_attr", "win", "status", "unsupported_irregular"]]},
        {"name": "te_refuse_short_window", "area": AREA, "order": 0,
         "latency_class": "hard_realtime",
         "match": [["ag", "has_temporal_escalation_policy", "pol"], ["ag", "has_temporal_window", "win"]],
         "where": And(Eq(A("pol", "enabled"), L(1.0)), Eq(A("win", "status"), L("ready")),
                      Eq(A("win", "regular_sampling"), L(True)), Lt(Count(A("win", "frames")), L(3))),
         "effects": [["set_attr", "win", "status", "insufficient_witness"]]},
        {"name": "te_refuse_oversized_window", "area": AREA, "order": 0,
         "latency_class": "hard_realtime",
         "match": [["ag", "has_temporal_escalation_policy", "pol"], ["ag", "has_temporal_window", "win"]],
         "where": And(Eq(A("pol", "enabled"), L(1.0)), Eq(A("win", "status"), L("ready")),
                      Gt(Count(A("win", "frames")), L(64))),
         "effects": [["set_attr", "win", "status", "unsupported_window_size"]]},
    ]


def approve_rule():
    active = Exists(N("ag", "has_temporal_escalation_lease"), "lease",
                    Eq(A("lease", "status"), L("active")))
    return {"name": "te_materialize_approved_window", "area": AREA, "order": 2,
            "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_temporal_escalation_policy", "pol"],
                      ["ag", "has_network_mode_state", "mode"],
                      ["ag", "has_thinking_budget", "budget"],
                      ["ag", "has_temporal_window", "win"],
                      ["win", "has_temporal_escalation_request", "req"],
                      ["req", "draws_on_thinking_budget", "budget"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("budget", "enabled"), L(1.0)),
                         Eq(A("win", "status"), L("ready")),
                         Eq(A("win", "regular_sampling"), L(True)),
                         Eq(A("req", "status"), L("approved")),
                         Eq(A("req", "debited_epoch"), A("mode", "epoch")),
                         Not(active)),
            "effects": [["add_node", "lease", "TemporalEscalationLease", {
                            "window_id": T(A("win", "window_id")),
                        "owner_id": T(A("win", "owner_id")),
                            "prior_value": T(A("ag", "time_infer_enabled")), "status": "active"}],
                        ["add_edge", "ag", "has_temporal_escalation_lease", "lease", {}],
                        ["add_node", "motion", "Observation", {
                            "key": T(A("win", "window_id")), "frames": T(A("win", "frames")),
                            "dim_types": T(A("win", "dim_types")),
                            "status": "motion_seq", "temporal_bridge": True}],
                        ["add_edge", "ag", "observed", "motion", {}],
                        ["add_edge", "win", "produces_motion_observation", "motion", {}],
                        ["add_edge", "motion", "temporal_source_window", "win", {}],
                        ["set_attr", "ag", "time_infer_enabled", 1.0],
                        ["set_attr", "req", "status", "consumed"],
                        ["set_attr", "win", "status", "submitted_to_time_infer"]]}


def finish_rule():
    terminal = {"type": "Or", "items": [Eq(A("motion", "status"), L("time_inferred")),
                                           Eq(A("motion", "status"), L("time_none"))]}
    restore = {"type": "IfThenElse", "cond": Eq(A("lease", "prior_value"), L(None)),
               "then": L(0.0), "other": A("lease", "prior_value")}
    return {"name": "te_restore_after_time_terminal", "area": AREA, "order": 3,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_temporal_escalation_lease", "lease"],
                      ["win", "has_temporal_escalation_request", "req"],
                      ["win", "produces_motion_observation", "motion"]],
            "where": And(Eq(A("lease", "status"), L("active")), terminal),
            "effects": [["set_attr", "ag", "time_infer_enabled", T(restore)],
                        ["set_attr", "lease", "status", "restored"],
                        ["set_attr", "win", "status", T(A("motion", "status"))],
                        ["set_attr", "req", "outcome", T(A("motion", "status"))]]}


def build_seed():
    edges = [("Agent", "has_temporal_escalation_policy", "TemporalEscalationPolicy"),
             ("Agent", "has_temporal_frame_event", "TemporalFrameEvent"),
             ("Agent", "has_temporal_frame_window_seal", "TemporalFrameWindowSeal"),
             ("TemporalFrameWindowSeal", "seals_temporal_observation", "Observation"),
             ("Agent", "has_temporal_window", "TemporalSequenceWindow"),
             ("TemporalSequenceWindow", "assembled_from_seal", "TemporalFrameWindowSeal"),
             ("TemporalSequenceWindow", "escalates_observation", "Observation"),
             ("TemporalSequenceWindow", "has_temporal_escalation_request", "ThinkingBudgetRequest"),
             ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
             ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
             ("Agent", "has_thinking_budget", "ThinkingBudget"),
             ("Agent", "has_network_mode_state", "NetworkModeState"),
             ("Agent", "has_temporal_escalation_lease", "TemporalEscalationLease"),
             ("Agent", "observed", "Observation"),
             ("TemporalSequenceWindow", "produces_motion_observation", "Observation"),
             ("Observation", "temporal_source_window", "TemporalSequenceWindow")]
    return {"id": "temporal_escalation", "version": "1.1.0", "self_load_only": True,
            "depends_on": ["thinking_budget", "time_axis"], "area": AREA,
            "description": "Assembles sealed graph-held measured frame events in sequence order, accepts only bounded regular windows, then funds the existing TimeInfer verifier; irregular windows are refused and prior time-infer policy is restored.",
            "nodes": [{"local_id": 0, "type": "TemporalEscalationPolicy",
                       "attrs": {"name": "temporal_escalation_policy", "enabled": 0.0,
                                 "step_cost": 1.0, "timestamp_tolerance": 0.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_temporal_escalation_policy",
                       "tgt": {"local": 0}, "attrs": {}, "provenance": "temporal_escalation:policy"}],
            "productions": [{"src": {"type": a, "var": "src"}, "edge_type": e,
                             "tgt": {"type": b, "var": "tgt"}, "where": None,
                             "weight": L(1.0), "provenance": f"temporal_escalation:{e}:{a}:{b}"}
                            for a, e, b in edges],
            "rules": [assemble_event_window_rule(), refuse_incomplete_event_window_rule(),
                      *refuse_event_window_size_rules(),
                      *refusal_rules(), request_rule(), approve_rule(), finish_rule()]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
