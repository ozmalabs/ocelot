#!/usr/bin/env python3
"""Generate bounded, funded graph rules for detached lattice imagery."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from gen_capability_collapse_seed import A, And, Eq, Gte, L, N, Not, Plus, T, V


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def In(member, container):
    return {"type": "In", "member": member, "container": container}


def MapList(source, var, value):
    return {"type": "MapList", "source": source, "var_name": var, "value": value}


def Fold(source, var, acc, init, body):
    return {"type": "Fold", "source": source, "var_name": var,
            "acc_name": acc, "init": init, "body": body}


def IndexAt(seq, idx):
    return {"type": "IndexAt", "seq": seq, "index": L(idx)}


def path_for(request):
    # Angles are quarter-turn indices. The path is supplied as signed steps by
    # the request author so ties are explicit and checked by the guard.
    return A(request, "rotation_steps")


def transform_shape(request):
    direction = IndexAt(path_for("request"), A("request", "step_index"))
    point = V("point")
    rotated = [IndexAt(point, 1), {"type": "Minus", "a": L(0), "b": IndexAt(point, 0)}]
    reflected = [{"type": "Minus", "a": L(0), "b": IndexAt(point, 1)}, IndexAt(point, 0)]
    pair = {"type": "IfThenElse", "cond": Gte(direction, L(0)),
            "then": {"type": "Vec", "items": rotated},
            "other": {"type": "Vec", "items": reflected}}
    raw = MapList(A("request", "current_shape"), "point", pair)
    rows = MapList(raw, "coord", IndexAt(V("coord"), 0))
    cols = MapList(raw, "coord", IndexAt(V("coord"), 1))
    min_row = Fold(rows, "value", "best", L(1000000000),
                   {"type": "IfThenElse", "cond": {"type": "Lt", "a": V("value"), "b": V("best")},
                    "then": V("value"), "other": V("best")})
    min_col = Fold(cols, "value", "best", L(1000000000),
                   {"type": "IfThenElse", "cond": {"type": "Lt", "a": V("value"), "b": V("best")},
                    "then": V("value"), "other": V("best")})
    return MapList(raw, "coord", {"type": "Vec", "items": [
        {"type": "Minus", "a": IndexAt(V("coord"), 0), "b": min_row},
        {"type": "Minus", "a": IndexAt(V("coord"), 1), "b": min_col},
    ]})


def step_rule():
    return {
        "name": "ai_execute_funded_quarter_turn",
        "batch": False,
        "comment": "Execute exactly one funded 90-degree lattice transform and retain its intermediate witness.",
        "match": [["agent", "has_analog_imagery_policy", "policy"],
                  ["agent", "has_thinking_budget", "budget"],
                  ["agent", "has_analog_imagery_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1)),
                      Eq(A("request", "status"), L("running")),
                      Gte(A("budget", "enabled"), L(1)),
                      Gte(A("budget", "remaining"), L(1)),
                      Gte(A("request", "step_index"), L(0)),
                      Lt(A("request", "step_index"), A("policy", "max_steps")),
                      Not(Eq(A("request", "step_index"), A("request", "step_count"))),
                      In(IndexAt(A("request", "rotation_steps"), A("request", "step_index")), L([90, -90])),
                      Lt(A("request", "buffer_size"), A("policy", "max_buffer_size"))),
        "effects": [["add_node", "witness", "ImageryStepWitness", {
                         "step_index": T(A("request", "step_index")),
                         "shape": T(transform_shape("request")),
                         "source_observation": T(A("request", "source_observation")),
                         "grounded": 0}],
                    ["add_edge", "request", "has_imagery_witness", "witness"],
                    ["set_attr", "request", "current_shape", T(transform_shape("request"))],
                    ["set_attr", "request", "step_index", T(Plus(A("request", "step_index"), L(1)))],
                    ["set_attr", "request", "buffer_size", T(Plus(A("request", "buffer_size"), L(1)))],
                    ["set_attr", "budget", "remaining", T(Plus(A("budget", "remaining"), L(-1)))],
                    ["set_attr", "request", "cost", T(Plus(A("request", "cost"), L(1)))]]}


def finish_rule():
    return {
        "name": "ai_finish_verified_detached_rotation",
        "batch": False,
        "comment": "Mark exact shape match as a proposal only; imagery remains ungrounded.",
        "match": [["agent", "has_analog_imagery_policy", "policy"],
                  ["agent", "has_analog_imagery_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1)),
                      Eq(A("request", "status"), L("running")),
                      Eq(A("request", "step_index"), A("request", "step_count"))),
        "effects": [["set_attr", "request", "status", "proposed"],
                    ["set_attr", "request", "shape_verified", T(Eq(A("request", "current_shape"), A("request", "expected_shape")))],
                    ["set_attr", "request", "grounded", 0]],
    }


def exhausted_rule():
    return {
        "name": "ai_stop_when_increment_unfunded",
        "batch": False,
        "match": [["agent", "has_analog_imagery_policy", "policy"],
                  ["agent", "has_thinking_budget", "budget"],
                  ["agent", "has_analog_imagery_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1)),
                      Eq(A("request", "status"), L("running")),
                      Gte(A("request", "step_index"), L(0)),
                      Lt(A("request", "step_index"), A("policy", "max_steps")),
                      Not(Eq(A("request", "step_index"), A("request", "step_count"))),
                      {"type": "Lt", "a": A("budget", "remaining"), "b": L(1)}),
        "effects": [["set_attr", "request", "status", "unresolved"],
                    ["set_attr", "request", "stop_reason", "budget_exhausted"],
                    ["set_attr", "request", "grounded", 0]],
    }


def expire_terminal_buffer_rule():
    return {
        "name": "ai_expire_terminal_imagery_buffer",
        "batch": False,
        "match": [["agent", "has_analog_imagery_policy", "policy"],
                  ["agent", "has_analog_imagery_request", "request"],
                  ["request", "has_imagery_witness", "witness"]],
        "where": And(Eq(A("policy", "enabled"), L(1)),
                      {"type": "In", "member": A("request", "status"),
                       "container": L(["proposed", "unresolved"])},
                      Not(Eq(A("request", "buffer_status"), L("expired")))),
        "effects": [["set_attr", "request", "buffer_status", "expired"],
                    ["set_attr", "witness", "buffer_status", "expired"]],
    }


def reject_unsupported_step_rule():
    direction = IndexAt(A("request", "rotation_steps"), A("request", "step_index"))
    return {
        "name": "ai_refuse_unsupported_rotation_increment",
        "batch": False,
        "match": [["agent", "has_analog_imagery_policy", "policy"],
                  ["agent", "has_analog_imagery_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1)),
                      Eq(A("request", "status"), L("running")),
                      Not(Eq(A("request", "step_index"), A("request", "step_count"))),
                      Not(In(direction, L([90, -90])))),
        "effects": [["set_attr", "request", "status", "unresolved"],
                    ["set_attr", "request", "stop_reason", "unsupported_rotation_step"],
                    ["set_attr", "request", "grounded", 0]],
    }


def reject_overlong_path_rule():
    return {
        "name": "ai_refuse_overlong_rotation_path",
        "batch": False,
        "match": [["agent", "has_analog_imagery_policy", "policy"],
                  ["agent", "has_analog_imagery_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1)),
                      Eq(A("request", "status"), L("running")),
                      {"type": "Gt", "a": A("request", "step_count"), "b": A("policy", "max_steps")}),
        "effects": [["set_attr", "request", "status", "unresolved"],
                    ["set_attr", "request", "stop_reason", "path_exceeds_bound"],
                    ["set_attr", "request", "grounded", 0]],
    }


def build():
    specs = [("Agent", "has_analog_imagery_policy", "AnalogImageryPolicy"),
             ("Agent", "has_analog_imagery_request", "AnalogImageryRequest"),
             ("Agent", "has_thinking_budget", "ThinkingBudget"),
             ("AnalogImageryRequest", "has_imagery_witness", "ImageryStepWitness")]
    return {
        "id": "analog_imagery", "version": "1.0.0", "depends_on": ["thinking_budget"],
        "description": "Default-off bounded, funded, detached quarter-turn imagery on exact lattice signatures.",
        "microtheory": {"name": "analog_imagery", "description": "Compose exact lattice rotations as funded graph-native increments."},
        "nodes": [{"local_id": 0, "type": "AnalogImageryPolicy", "attrs": {"enabled": 0.0, "max_steps": 3.0, "max_buffer_size": 4.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_analog_imagery_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:analog_imagery:{edge}", "src": {"type": src, "var": "src"}, "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in specs],
        "rules": [step_rule(), finish_rule(), exhausted_rule(), reject_unsupported_step_rule(), reject_overlong_path_rule(), expire_terminal_buffer_rule()],
    }


if __name__ == "__main__":
    (ROOT / "seeds" / "analog_imagery.json").write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
