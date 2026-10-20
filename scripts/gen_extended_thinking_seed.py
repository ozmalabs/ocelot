#!/usr/bin/env python3
"""Generate the opt-in, funded DimInfer/GenInfer extended-thinking executor."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREA = "extended_thinking"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def T(term): return {"__term__": term}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return {"type": "Not", "arg": Eq(a, b)}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Count(source): return {"type": "Count", "source": source}
def N(var, edge): return {"type": "Neighbours", "node": V(var), "edge_type": edge, "any_type": False}
def Exists(source, var, predicate): return {"type": "Exists", "source": source, "var_name": var, "predicate": predicate}
def Filter(source, var, predicate): return {"type": "Filter", "source": source, "var_name": var, "predicate": predicate}
def At(items, index): return {"type": "IndexAt", "seq": items, "index": index}
def Json(value): return {"type": "ToJsonString", "value": value}
def If(cond, then, other): return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def unexplained(obs="obs"):
    return And(
        Eq(A(obs, "dim_checked"), L(1)), Ne(A(obs, "dim_explained"), L(1)),
        Ne(A(obs, "gen_explained"), L(1)),
        Or(*(Eq(A(obs, "status"), L(x)) for x in ("minted", "decoded", "recognized_duplicate"))),
        Gt(Count(A(obs, "dim_types")), L(0)),
    )


def episode_open_guard(obs="obs"):
    return Not(Exists(N(obs, "has_extended_thinking_episode"), "prior_ep",
                       Ne(A("prior_ep", "status"), L("settled"))))


def cache_key(): return Json(A("obs", "key"))


def open_rule(name, ladder_name, cache=False):
    cache_exists = Exists(N("agent", "has_extended_thinking_cache"), "ce",
        And(Eq(A("ce", "key"), cache_key()), Eq(A("ce", "ladder_name"), L(ladder_name))))
    where = [Eq(A("pol", "enabled"), L(1.0)), unexplained(), episode_open_guard()]
    if ladder_name == "dim_grain_ladder":
        where.append(Ne(A("obs", "et_settled_epoch"), A("agent", "codebook_epoch")))
    if ladder_name == "dim_grain_ladder":
        where.append(cache_exists if cache else Not(cache_exists))
    else:
        where.extend([
            Eq(A("prior_dim_ep", "status"), L("settled")),
            Eq(A("prior_dim_ep", "outcome"), L("exhausted")),
            Not(Exists(N("obs", "has_extended_thinking_episode"), "prior_gen_ep",
                       Eq(A("prior_gen_ep", "ladder_name"), L("gen_infer_ladder")))),
        ])
    rule = {
        "name": name, "area": AREA, "order": 10, "latency_class": "hard_realtime",
        "match": [["agent", "has_extended_thinking_policy", "pol"],
                  ["agent", "observed", "obs"],
                  ["agent", "has_relax_ladder", "ladder"]],
        "where": And(*where, Eq(A("ladder", "name"), L(ladder_name))),
        "effects": [
            ["add_node", "ep", "ExtendedThinkingEpisode", {
                "status": "open", "ladder_name": ladder_name,
                "rung_index": T(Minus(A("ce", "rung_index"), L(1))) if cache else 0,
                "steps": 0, "opened_epoch": T(A("mode", "epoch")),
                "prior_value": T(A("agent", "dim_grains") if ladder_name == "dim_grain_ladder" else A("agent", "gen_infer_enabled")),
                "from_cache": 1 if cache else 0,
            }],
            ["add_edge", "obs", "has_extended_thinking_episode", "ep", {}],
            ["add_edge", "agent", "has_extended_thinking_episode", "ep", {}],
            ["add_edge", "ep", "relaxes_ladder", "ladder", {}],
        ],
    }
    if cache:
        rule["match"].append(["agent", "has_network_mode_state", "mode"])
        rule["match"].append(["agent", "has_extended_thinking_cache", "ce"])
        rule["where"] = And(*where, Eq(A("ce", "key"), cache_key()), Eq(A("ce", "ladder_name"), L(ladder_name)), Eq(A("ladder", "name"), L(ladder_name)))
        rule["effects"].append(["set_attr", "ce", "hits", T(Plus(A("ce", "hits"), L(1)))])
    else:
        rule["match"].append(["agent", "has_network_mode_state", "mode"])
    if ladder_name == "gen_infer_ladder":
        rule["match"].append(["obs", "has_extended_thinking_episode", "prior_dim_ep"])
    return rule


def make_rule(name, order, match, where, effects, *, batch=True, comment=""):
    rule = {"name": name, "area": AREA, "order": order,
            "latency_class": "hard_realtime", "match": match,
            "where": where, "effects": effects}
    if not batch: rule["batch"] = False
    if comment: rule["comment"] = comment
    return rule


def step_request():
    enabled_budget_exists = Exists(N("agent", "has_thinking_budget"), "enabled_budget",
        Gte(A("enabled_budget", "enabled"), L(1.0)))
    return make_rule("et_request_step", 11,
        [["agent", "has_extended_thinking_policy", "pol"], ["ep", "relaxes_ladder", "ladder"],
         ["agent", "has_thinking_budget", "budget"], ["agent", "has_network_mode_state", "mode"]],
        And(Eq(A("pol", "enabled"), L(1.0)), Eq(A("ep", "status"), L("open")),
            Or(Gte(A("budget", "enabled"), L(1.0)), Not(enabled_budget_exists)),
            Lt(A("ep", "rung_index"), Minus(Count(A("ladder", "rungs")), L(1)))),
        [["add_node", "req", "ExtendedThinkingStepRequest", {"status": "pending", "cost": T(A("pol", "step_cost")), "requester_kind": "extended_thinking"}],
         ["add_edge", "ep", "has_step_request", "req", {}], ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
         ["set_attr", "ep", "status", "awaiting_budget"]])


def apply_step(name, ladder_name, target_attr, *, gen=False):
    effects = [["add_node", "lease", "ToleranceRelaxLease", {
        "governs": f"agent.{target_attr}", "prior_value": T(A("ep", "prior_value")),
        # Nth is one-based in the substrate Term contract; rung_index is zero-based.
        "relaxed_value": T(At(A("ladder", "rungs"), Plus(A("ep", "rung_index"), L(1)))),
        "rung_index": T(Plus(A("ep", "rung_index"), L(1))),
        "valid_from_epoch": T(A("mode", "epoch")),
        "expires_after_epoch": T(Plus(A("mode", "epoch"), A("pol", "lease_epochs"))),
        "status": "active"}],
        ["add_edge", "ep", "has_relax_lease", "lease", {}],
        ["set_attr", "agent", target_attr, T(A("lease", "relaxed_value"))],
        # sd_redecode re-arms terminal minted/recognized statuses. A miss is
        # "decoded", which that frozen rule does not re-arm, so mark the
        # observation minted before backdating its decode epoch.
        ["set_attr", "obs", "status", "minted"],
        ["set_attr", "obs", "decoded_epoch", T(Minus(A("agent", "codebook_epoch"), L(1)))],
        ["set_attr", "ep", "rung_index", T(Plus(A("ep", "rung_index"), L(1)))],
        ["set_attr", "ep", "steps", T(Plus(A("ep", "steps"), L(1)))],
        ["set_attr", "ep", "status", "probing"], ["set_attr", "req", "status", "consumed"]]
    if gen:
        effects.extend([["set_attr", "obs", "gen_checked", 0], ["set_attr", "obs", "gen_explained", 0]])
    match = [["agent", "has_extended_thinking_policy", "pol"], ["agent", "has_network_mode_state", "mode"],
             ["agent", "observed", "obs"], ["obs", "has_extended_thinking_episode", "ep"],
             ["ep", "relaxes_ladder", "ladder"], ["ep", "has_step_request", "req"]]
    if gen:
        # The default path already minted a quantum axis. Hide its observation
        # edge while GenInfer runs: frozen sd_mint_generator requires that edge
        # population to be empty. Retain a private episode edge for provenance.
        match.append(["obs", "minted", "ax"])
        effects.extend([["add_edge", "ep", "temporarily_hides_quantum", "ax", {}],
                        ["del_edge", "obs", "minted", "ax"]])
    return make_rule(name, 13, match,
        And(Eq(A("pol", "enabled"), L(1.0)), Eq(A("ep", "status"), L("awaiting_budget")), Eq(A("ep", "ladder_name"), L(ladder_name)),
            Eq(A("ladder", "name"), L(ladder_name)), Eq(A("req", "status"), L("approved"))), effects)


def observe_rules():
    out = []
    out.append(make_rule("et_observe_hit", 14,
        [["agent", "observed", "obs"], ["obs", "has_extended_thinking_episode", "ep"], ["obs", "minted", "ax"]],
        And(Eq(A("ep", "status"), L("probing")), Eq(A("ep", "ladder_name"), L("dim_grain_ladder")), Eq(A("obs", "status"), L("recognized_transformed"))),
        [["set_attr", "ep", "status", "hit"], ["set_attr", "ep", "outcome", "hit"],
         ["set_attr", "obs", "accepted_at_relaxed", T(A("ep", "ladder_name"))],
         ["set_attr", "obs", "accepted_rung", T(A("ep", "rung_index"))],
         ["set_attr", "ax", "superseded_by_extended_thinking", 1]]))
    out.append(make_rule("et_observe_gen_hit", 14,
        [["agent", "observed", "obs"], ["obs", "has_extended_thinking_episode", "ep"], ["ep", "temporarily_hides_quantum", "ax"]],
        And(Eq(A("ep", "status"), L("probing")), Eq(A("ep", "ladder_name"), L("gen_infer_ladder")), Eq(A("obs", "status"), L("recognized_transformed"))),
        [["set_attr", "ep", "status", "hit"], ["set_attr", "ep", "outcome", "hit"],
         ["set_attr", "obs", "accepted_at_relaxed", T(A("ep", "ladder_name"))],
         ["set_attr", "obs", "accepted_rung", T(A("ep", "rung_index"))],
         ["add_edge", "obs", "minted", "ax", {}],
         ["set_attr", "ax", "superseded_by_extended_thinking", 1]]))
    out.append(make_rule("et_observe_miss", 14,
        [["agent", "observed", "obs"], ["agent", "has_extended_thinking_episode", "ep"]],
        And(Eq(A("ep", "status"), L("probing")), unexplained(), Gte(A("obs", "decoded_epoch"), A("agent", "codebook_epoch"))),
        [["set_attr", "ep", "status", "miss"]]))
    out.append(make_rule("et_continue_after_miss", 14,
        [["agent", "has_extended_thinking_episode", "ep"], ["ep", "relaxes_ladder", "ladder"]],
        And(Eq(A("ep", "status"), L("miss")), Lt(A("ep", "rung_index"), Minus(Count(A("ladder", "rungs")), L(1)))),
        [["set_attr", "ep", "status", "open"]]))
    out.append(make_rule("et_exhaust", 14,
        [["agent", "has_extended_thinking_episode", "ep"], ["ep", "relaxes_ladder", "ladder"]],
        And(Eq(A("ep", "status"), L("miss")), Gte(A("ep", "rung_index"), Minus(Count(A("ladder", "rungs")), L(1)))),
        [["set_attr", "ep", "status", "exhausted"], ["set_attr", "ep", "outcome", "exhausted"]]))
    out.append(make_rule("et_budget_denied", 14,
        [["agent", "has_extended_thinking_episode", "ep"], ["ep", "has_step_request", "req"]],
        And(Eq(A("ep", "status"), L("awaiting_budget")), Eq(A("req", "status"), L("denied"))),
        [["set_attr", "ep", "status", "denied"], ["set_attr", "ep", "outcome", "denied"]]))
    return out


def settle_rules():
    out = []
    terminal = Or(*(Eq(A("ep", "status"), L(x)) for x in ("hit", "exhausted", "denied", "expired")))
    restore_dim = If(Eq(A("ep", "prior_value"), L(None)),
        A("dim_policy", "dim_grains"), A("ep", "prior_value"))
    out.append(make_rule("et_settle_dim", 15,
        [["agent", "has_extended_thinking_episode", "ep"], ["agent", "has_dim_infer_policy", "dim_policy"], ["ep", "has_relax_lease", "lease"], ["agent", "observed", "obs"]],
        And(Eq(A("ep", "ladder_name"), L("dim_grain_ladder")), terminal, Eq(A("lease", "status"), L("active"))),
        [["set_attr", "agent", "dim_grains", T(restore_dim)], ["set_attr", "lease", "status", "restored"],
         ["set_attr", "ep", "status", "settled"], ["set_attr", "obs", "et_settled_epoch", T(A("agent", "codebook_epoch"))]]))
    out.append(make_rule("et_settle_dim_without_lease", 15,
        [["agent", "has_extended_thinking_episode", "ep"], ["agent", "has_dim_infer_policy", "dim_policy"], ["agent", "observed", "obs"]],
        And(Eq(A("ep", "ladder_name"), L("dim_grain_ladder")), terminal,
            Not(Exists(N("ep", "has_relax_lease"), "l", Eq(A("l", "status"), L("active"))))),
        [["set_attr", "ep", "status", "settled"],
         ["set_attr", "obs", "et_settled_epoch", T(A("agent", "codebook_epoch"))]]))
    restore_gen = If(Eq(A("ep", "prior_value"), L(None)), L(0.0), A("ep", "prior_value"))
    out.append(make_rule("et_settle_gen", 15,
        [["agent", "has_extended_thinking_episode", "ep"], ["ep", "has_relax_lease", "lease"], ["agent", "observed", "obs"]],
        And(Eq(A("ep", "ladder_name"), L("gen_infer_ladder")), terminal, Eq(A("lease", "status"), L("active"))),
        [["set_attr", "agent", "gen_infer_enabled", T(restore_gen)], ["set_attr", "lease", "status", "restored"],
         ["set_attr", "ep", "status", "settled"], ["set_attr", "obs", "et_settled_epoch", T(A("agent", "codebook_epoch"))]]))
    out.append(make_rule("et_settle_gen_without_lease", 15,
        [["agent", "has_extended_thinking_episode", "ep"], ["agent", "observed", "obs"]],
        And(Eq(A("ep", "ladder_name"), L("gen_infer_ladder")), terminal,
            Not(Exists(N("ep", "has_relax_lease"), "l", Eq(A("l", "status"), L("active"))))),
        [["set_attr", "ep", "status", "settled"],
         ["set_attr", "obs", "et_settled_epoch", T(A("agent", "codebook_epoch"))]]))
    return out


def cache_and_expiry_rules():
    cache_hit = make_rule("et_cache_hit", 16,
        [["agent", "observed", "obs"], ["obs", "has_extended_thinking_episode", "ep"],
         ["ep", "relaxes_ladder", "ladder"]],
        And(Eq(A("ep", "status"), L("settled")), Eq(A("ep", "outcome"), L("hit")),
            Eq(A("ep", "ladder_name"), L("dim_grain_ladder")),
            Not(Exists(N("agent", "has_extended_thinking_cache"), "existing_cache",
                And(Eq(A("existing_cache", "key"), Json(A("obs", "key"))),
                    Eq(A("existing_cache", "ladder_name"), L("dim_grain_ladder")))))),
        [["add_node_if_absent", "ce", "ExtendedThinkingCacheEntry", {
            "key": T(Json(A("obs", "key"))), "ladder_name": "dim_grain_ladder",
            "rung_index": T(A("ep", "rung_index")), "hits": 0}],
         ["add_edge", "agent", "has_extended_thinking_cache", "ce", {}]], batch=False)
    expire = make_rule("et_expire_lease", 9,
        [["agent", "has_network_mode_state", "mode"], ["agent", "has_extended_thinking_episode", "ep"],
         ["ep", "has_relax_lease", "lease"]],
        And(Eq(A("lease", "status"), L("active")), Gt(A("mode", "epoch"), A("lease", "expires_after_epoch")),
            Ne(A("ep", "status"), L("settled"))),
        [["set_attr", "ep", "status", "expired"], ["set_attr", "ep", "outcome", "expired"]])
    return [expire, cache_hit]


def productions():
    specs = [
        ("Agent", "has_extended_thinking_policy", "ExtendedThinkingPolicy"),
        ("Agent", "has_relax_ladder", "RelaxLadder"),
        ("Observation", "has_extended_thinking_episode", "ExtendedThinkingEpisode"),
        ("Agent", "has_extended_thinking_episode", "ExtendedThinkingEpisode"),
        ("ExtendedThinkingEpisode", "relaxes_ladder", "RelaxLadder"),
        ("ExtendedThinkingEpisode", "has_step_request", "ExtendedThinkingStepRequest"),
        ("ExtendedThinkingStepRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("ExtendedThinkingEpisode", "has_relax_lease", "ToleranceRelaxLease"),
        ("ExtendedThinkingEpisode", "temporarily_hides_quantum", "CapabilityAxis"),
        ("Agent", "has_extended_thinking_cache", "ExtendedThinkingCacheEntry"),
        ("Observation", "minted", "CapabilityAxis"),
        ("Agent", "has_dim_infer_policy", "DimInferPolicy"),
        ("Agent", "has_network_mode_state", "NetworkModeState"),
        ("Agent", "observed", "Observation"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
    ]
    return [{"provenance": f"seed:extended_thinking:{edge}:{src}:{tgt}",
             "src": {"type": src, "var": "src"}, "edge_type": edge,
             "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in specs]


def build():
    rules = [
        open_rule("et_open_dim_episode", "dim_grain_ladder"),
        open_rule("et_open_dim_episode_from_cache", "dim_grain_ladder", cache=True),
        open_rule("et_open_gen_episode", "gen_infer_ladder"),
        step_request(),
        apply_step("et_apply_dim_step", "dim_grain_ladder", "dim_grains"),
        apply_step("et_apply_gen_step", "gen_infer_ladder", "gen_infer_enabled", gen=True),
        *observe_rules(), *cache_and_expiry_rules(), *settle_rules(),
    ]
    return {
        "id": "extended_thinking", "version": "1.0.0", "self_load_only": True,
        "depends_on": ["shape_decode_loop", "thinking_budget"], "area": AREA,
        "description": "Opt-in bounded executor for funded DimInfer grain and GenInfer widening, targeted re-decode, exact re-verification, and settle-back.",
        "microtheory": {"name": AREA, "description": "Every widening step requires an approved ThinkingBudget request and carries a restoring lease."},
        "nodes": [
            {"local_id": 0, "type": "ExtendedThinkingPolicy", "attrs": {"name": "core_extended_thinking_policy", "enabled": 0.0, "step_cost": 1.0, "lease_epochs": 4.0}},
            {"local_id": 1, "type": "RelaxLadder", "attrs": {"name": "dim_grain_ladder", "governs": "agent.dim_grains", "rungs": [[0], [0, 1], [0, 1, 2]], "rank": 1}},
            {"local_id": 2, "type": "RelaxLadder", "attrs": {"name": "gen_infer_ladder", "governs": "agent.gen_infer_enabled", "rungs": [0.0, 1.0], "rank": 2}},
        ],
        "edges": [
            {"src": {"role": "agent_root"}, "type": "has_extended_thinking_policy", "tgt": {"local": 0}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_relax_ladder", "tgt": {"local": 1}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_relax_ladder", "tgt": {"local": 2}, "attrs": {}},
        ],
        "productions": productions(), "rules": rules,
    }


def main():
    (ROOT / "seeds" / "extended_thinking.json").write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
