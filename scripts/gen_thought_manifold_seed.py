#!/usr/bin/env python3
"""Generate the graph-owned ThoughtManifold segment controller (P4.E2.2)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "thought_manifold.json"
AREA = "thought_manifold"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def T(x): return {"__term__": x}
def projection(source, episode, policy, field):
    return {"type": "FutureManifoldProjection", "episode": V(episode),
            "policy": V(policy), "source": V(source), "field": field}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(a, b): return {"type": "Plus", "items": [a, b]}
def FilterList(src, var, predicate):
    return {"type": "FilterList", "source": src, "var_name": var,
            "predicate": predicate}
def Count(src): return {"type": "Count", "source": src}
def In(member, container):
    return {"type": "In", "member": member, "container": container}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def DictGet(dict_value, key): return {"type": "DictGet", "dict": dict_value, "key": key}
def Round(value, digits): return {"type": "Round", "value": value, "ndigits": L(digits)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Union(a, b):
    return {"type": "Union", "a": a, "b": b}
def IndexAt(seq, index):
    return {"type": "IndexAt", "seq": seq, "index": L(index)}
def Slice(seq, start, stop):
    return {"type": "Slice", "seq": seq, "start": start, "stop": stop}
def Append(seq, item):
    return {"type": "Append", "seq": seq, "item": item}
def Fold(source, var, acc, init, body):
    return {"type": "Fold", "source": source, "var_name": var,
            "acc_name": acc, "init": init, "body": body}
def Json(value):
    return {"type": "ToJsonString", "value": value}
def StringConcat(*parts):
    return {"type": "StringConcat", "parts": list(parts)}
def Exists(source, var, predicate):
    return {"type": "Exists", "source": source, "var_name": var,
            "predicate": predicate}


def signature_keys(signature):
    static_keys = {"type": "MapList", "source": A(signature, "coordinates"),
                   "var_name": "coordinate",
                   "value": StringConcat(
                       IndexAt(V("coordinate"), 0), L("|"),
                       IndexAt(V("coordinate"), 1), L("|"),
                       Json(IndexAt(V("coordinate"), 2)))}
    dynamic_keys = {"type": "MapList",
                    "source": N(signature, "has_projected_coordinate"),
                    "var_name": "projected_coordinate",
                    "value": A("projected_coordinate", "coordinate_key")}
    return Union(static_keys, dynamic_keys)


def project_aperture_coordinate_rule(*, dark=False):
    grain = DictGet(A("observer", "grain"), A("raw", "dimension"))
    quantum = {"type": "IfThenElse", "cond": Eq(grain, L(None)),
               "then": A("raw", "global_quantum"), "other": grain}
    rounded = Round(Div(A("raw", "raw_value"), quantum), 0)
    clipped = {"type": "Max", "items": [
        {"type": "Minus", "a": L(0), "b": A("raw", "half_width")},
        {"type": "Min", "items": [A("raw", "half_width"), rounded]}]}
    resolved = Or(Eq(A("observer", "resolves"), L(None)),
                  In(A("raw", "dimension"), A("observer", "resolves")))
    if dark:
        guard = Or(Not(resolved), Eq(clipped, L(0)), Eq(clipped, L(None)))
        effects = [["set_attr", "raw", "projection_status", "dark"]]
        name = "tm_mark_dark_aperture_coordinate"
    else:
        guard = And(resolved, Not(Eq(clipped, L(0))), Not(Eq(clipped, L(None))))
        key = StringConcat(A("raw", "dimension"), L("|"),
                           A("raw", "predicate"), L("|"), Json(clipped))
        effects = [["add_node", "projected", "ThoughtProjectedSignatureCoordinate", {
                        "dimension": T(A("raw", "dimension")),
                        "predicate": T(A("raw", "predicate")),
                        "value": T(clipped), "coordinate_key": T(key),
                        "provenance_kind": "observer_aperture_projection"}],
                   ["add_edge", "raw", "has_aperture_projection", "projected", {}],
                   ["add_edge", "signature", "has_projected_coordinate", "projected", {}],
                   ["set_attr", "raw", "projection_status", "projected"]]
        name = "tm_project_aperture_coordinate_natively"
    return {"name": name, "area": AREA,
            "order": 4 if not dark else 5,
            "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_thought_manifold_policy", "policy"],
                      ["ag", "has_thought_manifold", "manifold"],
                      ["manifold", "uses_aperture_observer", "observer"],
                      ["manifold", "has_raw_signature_coordinate", "raw"],
                      ["signature", "has_raw_coordinate", "raw"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("manifold", "controller_mode"), L("aperture_grain")),
                         Eq(A("raw", "projection_status"), L("pending")), guard),
            "effects": effects}


def assemble_admitted_signature_rule():
    raw = N("signature", "has_raw_coordinate")
    pending = Exists(raw, "raw_coordinate",
                     Eq(A("raw_coordinate", "projection_status"), L("pending")))
    return {"name": "tm_assemble_native_admitted_signature", "area": AREA,
            "order": 6, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_thought_manifold_policy", "policy"],
                      ["ag", "has_thought_manifold", "manifold"],
                      ["manifold", "uses_aperture_observer", "observer"],
                      ["manifold", "has_setpoint_signature", "signature"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("manifold", "controller_mode"), L("aperture_grain")),
                         Not(Eq(A("manifold", "admitted_signature_ready"), L(True))),
                         Not(pending)),
            "effects": [["set_attr", "manifold", "admitted_signature",
                         T(signature_keys("signature"))],
                        ["set_attr", "manifold", "admitted_signature_ready", True]]}


def account_segment_rule(*, funded=False, aperture=False):
    reached = A("segment", "topics_thought")
    if aperture:
        signature_nodes = N("segment", "has_topic_signature")
        reached_signatures = FilterList(
            signature_nodes, "topic_signature",
            In(A("topic_signature", "topic"), reached))
        trajectory_signature = Fold(
            reached_signatures, "topic_signature", "signature_acc", L([]),
            Union(V("signature_acc"), signature_keys("topic_signature")))
        deviation = Count(FilterList(
            trajectory_signature, "coordinate",
            Not(In(V("coordinate"), A("manifold", "admitted_signature")))))
    else:
        outside = FilterList(reached, "concept",
                             And(Not(Eq(V("concept"), L(None))),
                                 Not(In(V("concept"), A("manifold", "tube_region")))))
        deviation = Count(outside)
    # The concept-region tube itself is admissible frontier evidence, matching
    # the legacy controller's ability to continue through an unseen in-region
    # concept even when the current segment did not happen to mention it.
    frontier_source = reached if aperture else Union(reached, A("manifold", "tube_region"))
    fresh = FilterList(
        frontier_source, "frontier_topic",
        And(Not(Eq(V("frontier_topic"), L(None))),
            Not(Eq(V("frontier_topic"), A("manifold", "topic"))),
            Not(In(V("frontier_topic"), A("manifold", "seen_topics")))))
    if aperture:
        in_tube = FilterList(
            fresh, "tube_topic",
            Exists(
                FilterList(signature_nodes, "signature_for_topic",
                           Eq(A("signature_for_topic", "topic"), V("tube_topic"))),
                "signature_for_topic",
                Exists(signature_keys("signature_for_topic"), "coordinate",
                       In(V("coordinate"), A("manifold", "admitted_signature")))))
    else:
        in_tube = FilterList(fresh, "tube_topic",
                             In(V("tube_topic"), A("manifold", "tube_region")))
    frontier = {"type": "IfThenElse",
                "cond": {"type": "Gt", "a": Count(in_tube), "b": L(0)},
                "then": in_tube, "other": fresh}
    next_topic = IndexAt(frontier, 0)
    buffer_capacity = {"type": "IfThenElse",
                       "cond": {"type": "Gt",
                                "a": A("manifold", "detached_buffer_capacity"),
                                "b": L(0)},
                       "then": A("manifold", "detached_buffer_capacity"),
                       "other": L(64)}
    wide = {"type": "Gte", "a": deviation,
            "b": A("manifold", "deviation_wide_quanta")}
    narrow = {"type": "Lte", "a": deviation,
              "b": A("manifold", "deviation_converge_quanta")}
    widened = {"type": "Min", "items": [A("policy", "width_max"),
                                           Plus(A("manifold", "width"),
                                                A("manifold", "widen_step"))]}
    narrowed = {"type": "Max", "items": [L(0),
                                           {"type": "Minus", "a": A("manifold", "width"),
                                            "b": A("manifold", "narrow_step")}]}
    next_width = {"type": "IfThenElse", "cond": wide, "then": widened,
                  "other": {"type": "IfThenElse", "cond": narrow,
                            "then": narrowed, "other": A("manifold", "width")}}
    match = [["ag", "has_thought_manifold_policy", "policy"],
             ["ag", "has_thought_manifold", "manifold"],
             ["manifold", "has_pending_thought_segment", "segment"]]
    where = [Eq(A("policy", "enabled"), L(1.0)),
             Eq(A("manifold", "status"), L("running")),
             Eq(A("segment", "status"), L("ready"))]
    if funded:
        match.extend([["ag", "has_network_mode_state", "mode"],
                      ["manifold", "has_segment_request", "request"],
                      ["segment", "has_segment_generation_funding", "request"]])
        where.extend([Eq(A("manifold", "funding_required"), L(True)),
                      Eq(A("request", "status"), L("consumed")),
                      Eq(A("request", "segment_index"), A("manifold", "segment_index")),
                      Eq(A("request", "debited_epoch"), A("mode", "epoch"))])
    else:
        where.append(Not(Eq(A("manifold", "funding_required"), L(True))))
    if aperture:
        where.extend([Eq(A("manifold", "controller_mode"), L("aperture_grain")),
                      Eq(A("manifold", "admitted_signature_ready"), L(True))])
    else:
        where.append(Not(Eq(A("manifold", "controller_mode"), L("aperture_grain"))))
    return {
        "name": ("tm_account_funded_aperture_segment" if funded and aperture else
                 "tm_account_aperture_segment" if aperture else
                 "tm_account_funded_segment_and_steer_width" if funded else
                 "tm_account_segment_and_steer_width"), "area": AREA,
        "order": 10, "latency_class": "hard_realtime", "batch": False,
        "match": match, "where": And(*where),
        "effects": [
            ["add_node", "step", "ThoughtManifoldStep", {
                "index": T(A("manifold", "segment_index")),
                "topic": T(A("manifold", "topic")),
                "width": T(A("manifold", "width")),
                "deviation": T(deviation),
                "reached": T(reached),
                "segment_stop": T(A("segment", "stop_reason")),
                "next_width": T(next_width),
                "frontier_candidates": T(frontier),
                "next_topic": T(next_topic),
                # Numeric paths use the same native projection contract as
                # cognition-manifold candidates. Topic imagery remains
                # detached and cannot acquire grounding from this audit.
                "projection_shape": T(projection("segment", "manifold", "policy", "shape_snapshot")),
                "projection_resolved": T(projection("segment", "manifold", "policy", "resolved")),
                "projection_support": T(projection("segment", "manifold", "policy", "support")),
                "projection_loss": T(projection("segment", "manifold", "policy", "loss")),
                "projection_information_loss": T(projection("segment", "manifold", "policy", "information_loss")),
                "projection_horizon": T(projection("segment", "manifold", "policy", "horizon")),
                "provenance_kind": "candidate_imagery",
            }],
            ["add_edge", "manifold", "has_thought_manifold_step", "step", {}],
            ["add_edge", "step", "ingests_thought_segment", "segment", {}],
            ["set_attr", "segment", "status", "consumed"],
            ["set_attr", "manifold", "detached_buffer",
             T(Slice(Fold(reached, "buffer_item", "buffer_acc",
                          A("manifold", "detached_buffer"),
                          Append(V("buffer_acc"), V("buffer_item"))),
                     {"type": "Minus", "a": L(0),
                      "b": buffer_capacity},
                     L(None)))],
            ["set_attr", "manifold", "width", T(next_width)],
            ["set_attr", "manifold", "topic", T(A("step", "next_topic"))],
            ["set_attr", "manifold", "seen_topics",
             T(Union(A("manifold", "seen_topics"), reached))],
            ["set_attr", "manifold", "segment_index",
             T(Plus(A("manifold", "segment_index"), L(1)))],
            ["set_attr", "manifold", "status", T({
                "type": "IfThenElse",
                "cond": {"type": "Or", "items": [
                    Eq(A("segment", "stop_reason"), L("novelty_stalled")),
                    Eq(A("segment", "stop_reason"), L("no_topic")),
                    Eq(Count(reached), L(0)),
                    Eq(A("step", "next_topic"), L(None)),
                    {"type": "Gte", "a": Plus(A("manifold", "segment_index"), L(1)),
                     "b": A("manifold", "max_segments")},
                ]},
                "then": L("complete"), "other": L("running")})],
        ],
    }


def select_initial_topic_rule():
    candidates = A("manifold", "candidate_topics")
    in_tube = FilterList(candidates, "initial_topic",
                         In(V("initial_topic"), A("manifold", "tube_region")))
    selected = {"type": "IfThenElse",
                "cond": {"type": "Gt", "a": Count(in_tube), "b": L(0)},
                "then": IndexAt(in_tube, 0),
                "other": IndexAt(candidates, 0)}
    return {
        "name": "tm_select_initial_topic_from_candidate_tube",
        "area": AREA, "order": 0, "latency_class": "hard_realtime",
        "batch": False,
        "match": [["ag", "has_thought_manifold_policy", "policy"],
                  ["ag", "has_thought_manifold", "manifold"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("manifold", "status"), L("pending")),
                     Eq(A("manifold", "topic"), L(None)),
                     {"type": "Gt", "a": Count(candidates), "b": L(0)}),
        "effects": [["set_attr", "manifold", "topic", T(selected)],
                    ["set_attr", "manifold", "seen_topics", T(L([]))],
                    ["set_attr", "manifold", "status", "running"]],
    }


def construct_concept_region_rule():
    ancestors = {"type": "MapList",
                 "source": {"type": "ReachableFrom",
                            "node": A("manifold", "anchor_node"),
                            "edge_type": "causal_influence"},
                 "var_name": "ancestor_node",
                 "value": A("ancestor_node", "name")}
    region = Append(ancestors, A("manifold", "anchor_topic"))
    return {
        "name": "tm_construct_concept_region_from_graph",
        "area": AREA, "order": -1, "latency_class": "hard_realtime",
        "batch": False,
        "match": [["ag", "has_thought_manifold_policy", "policy"],
                  ["ag", "has_thought_manifold", "manifold"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("manifold", "status"), L("pending")),
                     Eq(A("manifold", "region_explicit"), L(False))),
        "effects": [["set_attr", "manifold", "tube_region", T(region)]],
    }


def request_funded_segment_rule():
    prior = Exists(N("manifold", "has_segment_request"), "old_request",
                   Eq(A("old_request", "segment_index"),
                      A("manifold", "segment_index")))
    request_key = StringConcat(L("thought-manifold:"), A("manifold", "run_key"), L(":"),
                               Json(A("manifold", "segment_index")))
    return {
        "name": "tm_request_funded_segment_generation", "area": AREA,
        "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_thought_manifold_policy", "policy"],
                  ["ag", "has_thinking_budget", "budget"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_thought_manifold", "manifold"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("budget", "enabled"), L(1.0)),
                     Eq(A("manifold", "funding_required"), L(True)),
                     Eq(A("manifold", "status"), L("running")),
                     Not(prior)),
        "effects": [["add_node", "request", "ThinkingBudgetRequest", {
                         "requester_kind": "thought_manifold_segment",
                         "request_key": T(request_key),
                         "status": "pending", "cost": T(A("manifold", "segment_cost")),
                         "requested_epoch": T(A("mode", "epoch")),
                         "segment_index": T(A("manifold", "segment_index"))}],
                     ["add_edge", "manifold", "has_segment_request", "request", {}],
                     ["add_edge", "ag", "has_thinking_budget_request", "request", {}],
                     ["add_edge", "request", "draws_on_thinking_budget", "budget", {}]]
    }


def close_unfunded_segment_rule():
    return {
        "name": "tm_close_segment_without_enabled_budget", "area": AREA,
        "order": 2, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_thought_manifold_policy", "policy"],
                  ["ag", "has_thought_manifold", "manifold"],
                  ["ag", "has_thinking_budget", "budget"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("manifold", "funding_required"), L(True)),
                     Eq(A("manifold", "status"), L("running")),
                     Not(Eq(A("budget", "enabled"), L(1.0)))),
        "effects": [["set_attr", "manifold", "status", "complete"],
                    ["set_attr", "manifold", "stop_reason", "budget_disabled"]]
    }


def deny_unfunded_segment_rule():
    return {
        "name": "tm_terminate_denied_segment_without_retry", "area": AREA,
        "order": 3, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_thought_manifold", "manifold"],
                  ["manifold", "has_segment_request", "request"]],
        "where": And(Eq(A("manifold", "funding_required"), L(True)),
                     Eq(A("manifold", "status"), L("running")),
                     Eq(A("request", "segment_index"), A("manifold", "segment_index")),
                     Eq(A("request", "status"), L("denied"))),
        "effects": [["set_attr", "manifold", "status", "complete"],
                    ["set_attr", "manifold", "stop_reason", "budget_denied"]]
    }


def expire_stale_segment_rule():
    return {
        "name": "tm_expire_segment_after_budget_epoch_change", "area": AREA,
        "order": 4, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_thought_manifold", "manifold"],
                  ["manifold", "has_segment_request", "request"]],
        "where": And(Eq(A("manifold", "funding_required"), L(True)),
                     Eq(A("manifold", "status"), L("running")),
                     Eq(A("request", "segment_index"), A("manifold", "segment_index")),
                     Eq(A("request", "status"), L("approved")),
                     Not(Eq(A("request", "debited_epoch"), A("mode", "epoch")))),
        "effects": [["set_attr", "request", "status", "expired"],
                    ["set_attr", "manifold", "status", "complete"],
                    ["set_attr", "manifold", "stop_reason", "stale_funding"]]
    }


def record_segment_funding_rule():
    return {
        "name": "tm_record_funded_segment_generation", "area": AREA,
        "order": 9, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_thought_manifold", "manifold"],
                  ["manifold", "has_pending_thought_segment", "segment"],
                  ["manifold", "has_segment_request", "request"]],
        "where": And(Eq(A("manifold", "funding_required"), L(True)),
                     Eq(A("segment", "status"), L("ready")),
                     Eq(A("request", "status"), L("approved")),
                     Eq(A("request", "segment_index"), A("manifold", "segment_index")),
                     Eq(A("request", "debited_epoch"), A("mode", "epoch"))),
        "effects": [["add_edge", "segment", "has_segment_generation_funding", "request", {}],
                    ["set_attr", "request", "status", "consumed"]]
    }


def build_seed():
    edges = [
        ("Agent", "has_thought_manifold_policy", "ThoughtManifoldPolicy"),
        ("Agent", "has_thought_manifold", "ThoughtManifold"),
        ("ThoughtManifold", "has_pending_thought_segment", "ThoughtSegmentInput"),
        ("ThoughtSegmentInput", "has_topic_signature", "ThoughtTopicSignature"),
        ("ThoughtManifold", "uses_aperture_observer", "Observer"),
        ("ThoughtManifold", "has_setpoint_signature", "ThoughtTopicSignature"),
        ("ThoughtManifold", "has_raw_signature_coordinate", "ThoughtRawSignatureCoordinate"),
        ("ThoughtTopicSignature", "has_raw_coordinate", "ThoughtRawSignatureCoordinate"),
        ("ThoughtTopicSignature", "has_projected_coordinate", "ThoughtProjectedSignatureCoordinate"),
        ("ThoughtRawSignatureCoordinate", "has_aperture_projection", "ThoughtProjectedSignatureCoordinate"),
        ("ThoughtSegmentInput", "has_segment_generation_funding", "ThinkingBudgetRequest"),
        ("ThoughtManifold", "has_thought_manifold_step", "ThoughtManifoldStep"),
        ("ThoughtManifoldStep", "ingests_thought_segment", "ThoughtSegmentInput"),
    ]
    return {
        "id": "thought_manifold", "version": "1.5.0", "self_load_only": True,
        "depends_on": ["thinking_budget"], "area": AREA,
        "description": "Graph-owned discrete ThoughtManifold segment accounting and width control; candidate imagery has no grounding authority.",
        "nodes": [{"local_id": 0, "type": "ThoughtManifoldPolicy",
                   "attrs": {"name": "thought_manifold_policy", "enabled": 0.0,
                             "width_max": 8,
                             "future_manifold_projection_budget": 0.0,
                             "future_manifold_physical_horizon": 0.0}}],
        "edges": [{"src": {"role": "agent_root"},
                    "type": "has_thought_manifold_policy", "tgt": {"local": 0},
                    "attrs": {}, "provenance": "thought_manifold:policy"}],
        "productions": [{"src": {"type": src, "var": "src"},
                         "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"},
                         "where": None, "weight": L(1.0),
                         "provenance": f"thought_manifold:{edge}:{src}:{tgt}"}
                        for src, edge, tgt in edges],
        "rules": [construct_concept_region_rule(), select_initial_topic_rule(),
                  request_funded_segment_rule(), close_unfunded_segment_rule(),
                  deny_unfunded_segment_rule(), expire_stale_segment_rule(),
                  project_aperture_coordinate_rule(),
                  project_aperture_coordinate_rule(dark=True),
                  assemble_admitted_signature_rule(),
                  record_segment_funding_rule(), account_segment_rule(),
                  account_segment_rule(funded=True),
                  account_segment_rule(aperture=True),
                  account_segment_rule(funded=True, aperture=True)],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
