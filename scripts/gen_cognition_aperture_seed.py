#!/usr/bin/env python3
"""Generate six typed, owner-scoped Observer aperture adapters (P4.C5.2)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "cognition_aperture.json"
AREA = "cognition_aperture"

ADAPTERS = {
    "reading": "observer:reading",
    "dwell": "observer:dwell",
    "finite_difference_k": "observer:difference_order",
    "qualia_aperture": None,
    "shape_decode_scope": "observer:decode_scope",
    "manifold_mask": "observer:manifold_mask",
}


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def T(t): return {"__term__": t}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Not(x): return {"type": "Not", "arg": x}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def StringConcat(*parts): return {"type": "StringConcat", "parts": list(parts)}
def Filter(src, var, predicate):
    return {"type": "Filter", "source": src, "var_name": var,
            "predicate": predicate}
def SortBy(src, var, key):
    return {"type": "SortBy", "source": src, "var_name": var, "key": key}
def IndexAt(seq, index): return {"type": "IndexAt", "seq": seq, "index": L(index)}


def observer_guard_rule():
    already_guarded = And(Eq(A("obs", "ap_question_funding_required"), L(True)),
                          Eq(A("obs", "p4_aperture_guard_epoch"), A("src", "source_epoch")),
                          Eq(A("obs", "p4_aperture_guard_source"), A("src", "source_key")))
    return {"name": "ca_guard_chosen_observer_questioning", "area": AREA,
            "order": 0, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_cognition_aperture_policy", "pol"],
                      ["ag", "has_network_mode_state", "mode"],
                      ["ag", "has_cognition_aperture_source", "src"],
                      ["src", "applies_to_observer", "obs"],
                      ["obs", "chose_aperture", "ap"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("src", "authority"), L("chosen")),
                         Eq(A("src", "owner_id"), A("obs", "name")),
                         Not(already_guarded)),
            "effects": [["set_attr", "obs", "ap_question_funding_required", True],
                        ["set_attr", "obs", "ap_question_funded", False],
                        ["set_attr", "obs", "p4_aperture_guard_epoch", T(A("src", "source_epoch"))],
                        ["set_attr", "obs", "p4_aperture_guard_source", T(A("src", "source_key"))],
                        ["add_edge", "obs", "has_cognition_aperture_mode", "mode", {}]]}


def question_request_rule():
    threshold = {"type": "IfThenElse", "cond": Eq(A("obs", "ap_question_after"), L(None)),
                 "then": L(1.0), "other": A("obs", "ap_question_after")}
    duplicate = Exists(N("obs", "has_cognition_aperture_request"), "old",
                       And(Eq(A("old", "observer_generation"), A("obs", "ap_gen")),
                           Eq(A("old", "source_key"), A("src", "source_key")),
                           Eq(A("old", "source_epoch"), A("src", "source_epoch"))))
    another_active_request = Exists(N("ag", "has_thinking_budget_request"), "active",
                                    And(Eq(A("active", "requester_kind"),
                                           L("cognition_aperture_probe")),
                                        Or(Eq(A("active", "status"), L("pending")),
                                           Eq(A("active", "status"), L("approved")),
                                           Eq(A("active", "status"), L("authorized")))))
    epoch_question_already_opened = Exists(
        N("ag", "has_thinking_budget_request"), "epoch_question",
        And(Eq(A("epoch_question", "requester_kind"), L("cognition_aperture_probe")),
            Eq(A("epoch_question", "requested_epoch"), A("mode", "epoch"))))
    request_key = StringConcat(L("c5-question:"), A("obs", "name"), L(":"),
                               {"type": "ToJsonString", "value": A("obs", "ap_gen")}, L(":"),
                               A("src", "source_key"), L(":"),
                               {"type": "ToJsonString", "value": A("src", "source_epoch")})
    return {"name": "ca_request_funded_chosen_frame_question", "area": AREA,
            "order": 1, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_cognition_aperture_policy", "pol"],
                      ["ag", "has_thinking_budget", "budget"],
                      ["ag", "has_network_mode_state", "mode"],
                      ["ag", "has_cognition_aperture_source", "src"],
                      ["src", "applies_to_observer", "obs"],
                      ["obs", "chose_aperture", "ap"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("budget", "enabled"), L(1.0)),
                         Eq(A("src", "authority"), L("chosen")),
                         Eq(A("src", "owner_id"), A("obs", "name")),
                         Eq(A("src", "voi_status"), L("positive")),
                         Not(Eq(A("src", "voi_evidence_id"), L(None))),
                         Eq(A("obs", "ap_question_funding_required"), L(True)),
                         Eq(A("obs", "p4_aperture_guard_epoch"), A("src", "source_epoch")),
                         Gte(A("obs", "ap_chosen_dwell"), threshold),
                         Not(duplicate), Not(another_active_request),
                         Not(epoch_question_already_opened)),
            "effects": [["add_node", "req", "ThinkingBudgetRequest", {
                            "requester_kind": "cognition_aperture_probe",
                            "requester_key": T(request_key), "source_key": T(A("src", "source_key")),
                            "source_epoch": T(A("src", "source_epoch")),
                            "observer_generation": T(A("obs", "ap_gen")),
                            "requested_epoch": T(A("mode", "epoch")),
                            "cost": T(A("pol", "probe_cost")), "status": "pending"}],
                        ["add_edge", "ag", "has_thinking_budget_request", "req", {}],
                        ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
                        ["add_edge", "obs", "has_cognition_aperture_request", "req", {}]]}


def authorize_question_rule():
    return {"name": "ca_authorize_same_epoch_debited_question", "area": AREA,
            "order": 2, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_cognition_aperture_policy", "pol"],
                      ["ag", "has_network_mode_state", "mode"],
                      ["ag", "has_cognition_aperture_source", "src"],
                      ["src", "applies_to_observer", "obs"],
                      ["obs", "has_cognition_aperture_request", "req"],
                      ["req", "draws_on_thinking_budget", "budget"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("req", "requester_kind"), L("cognition_aperture_probe")),
                         Eq(A("req", "status"), L("approved")),
                         Eq(A("req", "debited_epoch"), A("mode", "epoch")),
                         Eq(A("req", "requested_epoch"), A("mode", "epoch")),
                         Eq(A("req", "source_epoch"), A("src", "source_epoch")),
                         Eq(A("req", "observer_generation"), A("obs", "ap_gen")),
                         Eq(A("obs", "ap_question_funding_required"), L(True)),
                         Eq(A("obs", "p4_aperture_guard_epoch"), A("src", "source_epoch")),
                         Eq(A("obs", "ap_question_funded"), L(False))),
            "effects": [["set_attr", "obs", "ap_question_funded", True],
                        ["set_attr", "obs", "ap_question_funded_epoch", T(A("mode", "epoch"))],
                        ["set_attr", "req", "status", "authorized"]]}


def arbitrate_question_requests_rule():
    pending = Filter(N("ag", "has_thinking_budget_request"), "candidate",
                     And(Eq(A("candidate", "requester_kind"),
                            L("cognition_aperture_probe")),
                         Eq(A("candidate", "status"), L("pending"))))
    first = IndexAt(SortBy(pending, "candidate", A("candidate", "requester_key")), 0)
    return {"name": "ca_serialize_same_epoch_aperture_requests", "area": AREA,
            "order": 2, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_thinking_budget_request", "req"]],
            "where": And(Eq(A("req", "requester_kind"), L("cognition_aperture_probe")),
                         Eq(A("req", "status"), L("pending")),
                         Not(Eq(V("req"), first))),
            "effects": [["set_attr", "req", "status", "denied"],
                        ["set_attr", "req", "terminal_reason", "serialized_same_epoch"]]}


def deny_or_expire_question_rule():
    denied = Eq(A("req", "status"), L("denied"))
    stale = And(Eq(A("req", "status"), L("approved")),
                Or({"type": "Not", "arg": Eq(A("req", "debited_epoch"), A("mode", "epoch"))},
                   {"type": "Not", "arg": Eq(A("req", "source_epoch"), A("src", "source_epoch"))},
                   {"type": "Not", "arg": Eq(A("req", "observer_generation"), A("obs", "ap_gen"))}))
    return {"name": "ca_close_denied_or_stale_question", "area": AREA,
            "order": 3, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_network_mode_state", "mode"],
                      ["ag", "has_cognition_aperture_source", "src"],
                      ["src", "applies_to_observer", "obs"],
                      ["obs", "has_cognition_aperture_request", "req"]],
            "where": And(Eq(A("req", "requester_kind"), L("cognition_aperture_probe")),
                         Or(denied, stale)),
            "effects": [["set_attr", "obs", "ap_question_funded", False],
                        ["set_attr", "req", "status", T({"type": "IfThenElse", "cond": denied,
                                                               "then": L("denied"), "other": L("expired")})]]}


def restore_question_terminal_rule():
    return {"name": "ca_restore_question_after_terminal_probe", "area": AREA,
            "order": 4, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_cognition_aperture_source", "src"],
                      ["src", "applies_to_observer", "obs"],
                      ["obs", "has_cognition_aperture_request", "req"],
                      ["obs", "probe_projected", "probe"]],
            "where": And(Eq(A("req", "requester_kind"), L("cognition_aperture_probe")),
                         Eq(A("req", "status"), L("authorized")),
                         Eq(A("probe", "kind"), L("probe_percept")),
                         Eq(A("probe", "ap_gen"), A("obs", "ap_gen")),
                         Eq(A("obs", "ap_questioned_gen"), A("obs", "ap_gen"))),
            "effects": [["set_attr", "obs", "ap_question_funded", False],
                        ["set_attr", "req", "status", "consumed"],
                        ["set_attr", "req", "outcome", T(A("probe", "ap_residual"))]]}


def adapter_rule(adapter, dimension):
    prior = Exists(N("ag", "has_cognition_aperture_dimension"), "old",
                   And(Eq(A("old", "source_key"), A("src", "source_key")),
                       Eq(A("old", "source_epoch"), A("src", "source_epoch"))))
    attrs = {
        "adapter_id": adapter,
        "dimension_id": T(A("src", "dimension_id")) if dimension is None else dimension,
        "owner_id": T(A("src", "owner_id")),
        "frame_id": T(A("src", "frame_id")),
        "source_epoch": T(A("src", "source_epoch")),
        "source_key": T(A("src", "source_key")),
        "value_kind": T(A("src", "value_kind")),
        "value": T(A("src", "value")),
        "missing": T(A("src", "missing")),
        "tolerance": T(A("src", "tolerance")),
        "authority": T(A("src", "authority")),
        "status": "current",
    }
    return {"name": f"ca_project_{adapter}", "area": AREA, "order": 20,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_aperture_policy", "pol"],
                      ["ag", "has_cognition_aperture_source", "src"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("src", "adapter_id"), L(adapter)),
                         Not(prior)),
            "effects": [["add_node", "dim", "CognitionApertureDimension", attrs],
                        ["add_edge", "ag", "has_cognition_aperture_dimension", "dim", {}],
                        ["add_edge", "dim", "projects_aperture_source", "src", {}]]}


def stale_rule():
    return {"name": "ca_retire_stale_aperture_dimensions", "area": AREA, "order": 21,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_aperture_dimension", "dim"],
                      ["ag", "has_cognition_aperture_source", "src"]],
            "where": And(Eq(A("dim", "status"), L("current")),
                         Eq(A("dim", "source_key"), A("src", "source_key")),
                         {"type": "Not", "arg": Eq(A("dim", "source_epoch"), A("src", "source_epoch"))}),
            "effects": [["set_attr", "dim", "status", "stale"]]}


def build_seed():
    edges = [("Agent", "has_cognition_aperture_policy", "CognitionAperturePolicy"),
             ("Agent", "has_cognition_aperture_source", "CognitionApertureSource"),
             ("Agent", "has_cognition_aperture_dimension", "CognitionApertureDimension"),
             ("Agent", "has_thinking_budget", "ThinkingBudget"),
             ("Agent", "has_network_mode_state", "NetworkModeState"),
             ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
             ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
             ("Agent", "has_cognition_aperture_source", "CognitionApertureSource"),
             ("Agent", "has_cognition_aperture_dimension", "CognitionApertureDimension"),
             ("CognitionApertureDimension", "projects_aperture_source", "CognitionApertureSource"),
             ("CognitionApertureSource", "applies_to_observer", "Observer"),
             ("Observer", "has_cognition_aperture_mode", "NetworkModeState"),
             ("Observer", "has_cognition_aperture_request", "ThinkingBudgetRequest"),
             ("Observer", "chose_aperture", "Aperture"),
             ("Observer", "probe_projected", "ObservedShape")]
    return {"id": "cognition_aperture", "version": "1.0.0", "self_load_only": True,
            "depends_on": ["cognition_signature", "thinking_budget", "aperture_frame"], "area": AREA,
            "description": "Six explicit typed Observer aperture adapters plus a shared-budget authorization gate for chosen-frame residual probes.",
            "nodes": [{"local_id": 0, "type": "CognitionAperturePolicy",
                       "attrs": {"name": "cognition_aperture_policy", "enabled": 0.0,
                                 "probe_cost": 1.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_cognition_aperture_policy",
                       "tgt": {"local": 0}, "attrs": {}, "provenance": "cognition_aperture:policy"}],
            "productions": [{"src": {"type": src, "var": "src"}, "edge_type": edge,
                             "tgt": {"type": tgt, "var": "tgt"}, "where": None,
                             "weight": L(1.0), "provenance": f"cognition_aperture:{edge}:{src}:{tgt}"}
                            for src, edge, tgt in edges],
            "rules": [observer_guard_rule(), question_request_rule(),
                      arbitrate_question_requests_rule(), authorize_question_rule(),
                      deny_or_expire_question_rule(), restore_question_terminal_rule(),
                      *[adapter_rule(k, v) for k, v in ADAPTERS.items()], stale_rule()]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
