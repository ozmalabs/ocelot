#!/usr/bin/env python3
"""Author the domain-neutral, integer-native order-N cognition collapse seed.

The Python in this file only serialises graph data.  Runtime selection,
deepening, publication, and practice all execute as Rust graph rewrites.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def Max(*items):
    return {"type": "Max", "items": list(items)}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(item):
    return {"type": "Not", "arg": item}


def Neighbours(var, edge_type):
    return {
        "type": "Neighbours",
        "node": V(var),
        "edge_type": edge_type,
        "any_type": False,
    }


def Count(source):
    return {"type": "Count", "source": source}


def Filter(source, var_name, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def T(term):
    return {"__term__": term}


def N(var, edge_type):
    return Neighbours(var, edge_type)


ZERO = L(0)
ONE = L(1)


def numeric(var, key):
    """Coerce a present integer-valued graph attribute into numeric context."""
    return Plus(A(var, key), ZERO)


def channel_mode(program="program"):
    return Eq(A(program, "residual_mode"), L("channels"))


def scalar_mode(program="program"):
    return Not(channel_mode(program))


def breached_channels(program="program"):
    return Filter(
        N(program, "has_capability_residual_channel"),
        "channel",
        And(
            Gte(numeric("channel", "precision_quanta"),
                numeric(program, "minimum_precision_quanta")),
            Or(
                Gt(numeric("channel", "observed_quanta"),
                   numeric("channel", "boundary_quanta")),
                Gt(numeric("channel", "control_demand_quanta"),
                   numeric("channel", "proactive_boundary_quanta")),
            ),
        ),
    )


def valid_override_leases(scope="scope", state="state"):
    return Filter(
        N(scope, "receives_capability_override_lease"),
        "candidate_lease",
        And(
            Eq(numeric("candidate_lease", "active"), ONE),
            Gte(numeric(state, "request_epoch"),
                numeric("candidate_lease", "valid_from_epoch")),
            Lte(numeric(state, "request_epoch"),
                numeric("candidate_lease", "expires_after_epoch")),
        ),
    )


def reset_published_rule():
    return {
        "name": "cc_reset_published_outcome",
        "area": "general_cognition",
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A re-armed collapse retracts its previous publication before opening.",
        "match": [["state", "published_capability_outcome", "outcome"]],
        "where": And(
            Eq(A("state", "stage"), L("ready")),
            Eq(numeric("state", "collapse_armed"), ONE),
        ),
        "effects": [["del_edge", "state", "published_capability_outcome", "outcome"]],
    }


def reset_active_rule():
    return {
        "name": "cc_reset_active_program",
        "area": "general_cognition",
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A re-armed collapse restarts from its situated root, never a global home.",
        "match": [["state", "has_active_capability_program", "program"]],
        "where": And(
            Eq(A("state", "stage"), L("ready")),
            Eq(numeric("state", "collapse_armed"), ONE),
        ),
        "effects": [["del_edge", "state", "has_active_capability_program", "program"]],
    }


def open_rule():
    return {
        "name": "cc_open",
        "area": "general_cognition",
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Open one collapse at its scoped order-0 program.",
        "match": [["state", "has_root_capability_program", "program"]],
        "where": And(
            Eq(A("state", "stage"), L("ready")),
            Eq(numeric("state", "collapse_armed"), ONE),
            Eq(Count(N("state", "has_root_capability_program")), ONE),
            Eq(Count(N("state", "has_active_capability_program")), ZERO),
            Eq(Count(N("state", "published_capability_outcome")), ZERO),
        ),
        "effects": [
            ["add_edge", "state", "has_active_capability_program", "program"],
            ["set_attr", "state", "stage", "collapsing"],
            ["set_attr", "state", "status", "collapsing"],
            ["set_attr", "state", "done", 0],
            ["set_attr", "state", "collapse_armed", 0],
            ["set_attr", "state", "synthesis_requested", 0],
            ["set_attr", "state", "current_order", T(numeric("program", "order"))],
            ["set_attr", "state", "deepest_order", T(numeric("program", "order"))],
            ["set_attr", "state", "cognitive_evaluations", 0],
            ["set_attr", "state", "published_outcome_count", 0],
        ],
    }


def compiled_settle_rule():
    return {
        "name": "cc_settle_compiled",
        "area": "general_cognition",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Muscle memory publishes the exact practiced outcome at the lower order.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "compiles_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            scalar_mode(),
            Not(Gt(numeric("program", "residual_quanta"),
                   numeric("program", "capability_boundary_quanta"))),
            Eq(Count(N("program", "compiles_capability_outcome")), ONE),
            Eq(Count(N("state", "published_capability_outcome")), ZERO),
        ),
        "effects": settle_effects("compiled_practice"),
    }


def native_settle_rule():
    return {
        "name": "cc_settle_native",
        "area": "general_cognition",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A held capability boundary settles one native opaque outcome.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "settles_to_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            scalar_mode(),
            Not(Gt(numeric("program", "residual_quanta"),
                   numeric("program", "capability_boundary_quanta"))),
            Eq(Count(N("program", "compiles_capability_outcome")), ZERO),
            Eq(Count(N("program", "settles_to_capability_outcome")), ONE),
            Eq(Count(N("state", "published_capability_outcome")), ZERO),
        ),
        "effects": settle_effects("native_program"),
    }


def settle_effects(provenance):
    return [
        ["add_edge", "state", "published_capability_outcome", "outcome"],
        ["set_attr", "state", "published_outcome_ref", T(V("outcome"))],
        ["set_attr", "state", "published_program_ref", T(V("program"))],
        ["set_attr", "state", "achieved_order", T(numeric("program", "order"))],
        ["set_attr", "state", "current_order", T(numeric("program", "order"))],
        ["set_attr", "state", "cognitive_evaluations",
         T(Plus(numeric("state", "cognitive_evaluations"), ONE))],
        ["set_attr", "state", "published_outcome_count", 1],
        ["set_attr", "state", "publication_provenance", provenance],
        ["set_attr", "state", "status", "settled"],
        ["set_attr", "state", "stage", "settled"],
        ["set_attr", "state", "done", 1],
    ]


def deepen_rule():
    limit_permits = Or(
        Eq(numeric("state", "order_limit_enabled"), ZERO),
        Lte(numeric("higher", "order"), numeric("state", "maximum_order")),
    )
    return {
        "name": "cc_residual_deepen",
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Only surprise outside the held boundary opens the next same-typed program.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "continues_to_higher_order_capability_program", "higher"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            scalar_mode(),
            Gt(numeric("program", "residual_quanta"),
               numeric("program", "capability_boundary_quanta")),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
            limit_permits,
        ),
        "effects": [
            ["add_node_if_absent", "step", "CapabilityCollapseStep", {
                "collapse_state_ref": T(V("state")),
                "program_ref": T(V("program")),
                "request_epoch": T(numeric("state", "request_epoch")),
                "observed_residual_quanta": T(numeric("program", "residual_quanta")),
                "credited": 0,
            }],
            ["add_edge", "state", "has_capability_collapse_step", "step"],
            ["add_edge", "step", "traversed_capability_program", "program"],
            ["del_edge", "state", "has_active_capability_program", "program"],
            ["add_edge", "state", "has_active_capability_program", "higher"],
            ["set_attr", "state", "current_order", T(numeric("higher", "order"))],
            ["set_attr", "state", "deepest_order", T(Max(
                numeric("state", "deepest_order"), numeric("higher", "order")))],
            ["set_attr", "state", "cognitive_evaluations",
             T(Plus(numeric("state", "cognitive_evaluations"), ONE))],
            ["set_attr", "state", "status", "deepened_by_residual"],
        ],
    }


def unresolved_no_higher_rule():
    return unresolved_rule(
        "cc_request_synthesis_no_higher_program",
        Eq(Count(N("program", "continues_to_higher_order_capability_program")), ZERO),
        "unresolved_boundary",
        "No held higher-order program covers the surprise; request synthesis without fabricating an outcome.",
    )


def unresolved_limit_rule():
    return {
        "name": "cc_stop_at_configured_order_limit",
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Configured deployment depth is a resource choice, not an architectural order ceiling.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "continues_to_higher_order_capability_program", "higher"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            scalar_mode(),
            Gt(numeric("program", "residual_quanta"),
               numeric("program", "capability_boundary_quanta")),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
            Eq(numeric("state", "order_limit_enabled"), ONE),
            Gt(numeric("higher", "order"), numeric("state", "maximum_order")),
        ),
        "effects": unresolved_effects("configured_order_limit", 0),
    }


def unresolved_ambiguous_higher_rule():
    return unresolved_rule(
        "cc_request_synthesis_ambiguous_higher_program",
        Gt(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
        "ambiguous_higher_program",
        "A branch is itself an unresolved cognition problem; the core does not pick an arbitrary continuation.",
    )


def unresolved_rule(name, continuation_predicate, reason, comment):
    return {
        "name": name,
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": comment,
        "match": [["state", "has_active_capability_program", "program"]],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            scalar_mode(),
            Gt(numeric("program", "residual_quanta"),
               numeric("program", "capability_boundary_quanta")),
            continuation_predicate,
        ),
        "effects": unresolved_effects(reason, 1),
    }


def unresolved_effects(reason, synthesis_requested):
    return [
        ["set_attr", "state", "status", reason],
        ["set_attr", "state", "unresolved_reason", reason],
        ["set_attr", "state", "synthesis_requested", synthesis_requested],
        ["set_attr", "state", "published_outcome_count", 0],
        ["set_attr", "state", "stage", "unresolved"],
        ["set_attr", "state", "done", 1],
    ]


def unresolved_outcome_rule():
    return {
        "name": "cc_refuse_missing_or_ambiguous_outcome",
        "area": "general_cognition",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A boundary can settle only one held outcome; absence or multiplicity remains explicit.",
        "match": [["state", "has_active_capability_program", "program"]],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            scalar_mode(),
            Not(Gt(numeric("program", "residual_quanta"),
                   numeric("program", "capability_boundary_quanta"))),
            Or(
                Gt(Count(N("program", "compiles_capability_outcome")), ONE),
                And(
                    Eq(Count(N("program", "compiles_capability_outcome")), ZERO),
                    Not(Eq(Count(N("program", "settles_to_capability_outcome")), ONE)),
                ),
            ),
        ),
        "effects": unresolved_effects("missing_or_ambiguous_outcome", 1),
    }


def channel_compiled_settle_rule():
    return {
        "name": "cc_channel_settle_compiled",
        "area": "general_cognition",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "All trusted residual channels are inside their envelopes; publish the practiced basin.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "compiles_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            channel_mode(),
            Eq(Count(breached_channels()), ZERO),
            Eq(Count(N("program", "compiles_capability_outcome")), ONE),
            Eq(Count(N("state", "published_capability_outcome")), ZERO),
        ),
        "effects": settle_effects("compiled_capability_basin"),
    }


def channel_native_settle_rule():
    return {
        "name": "cc_channel_settle_native",
        "area": "general_cognition",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A multidimensional capability envelope settles without collapsing its channels to one score.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "settles_to_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            channel_mode(),
            Eq(Count(breached_channels()), ZERO),
            Eq(Count(N("program", "compiles_capability_outcome")), ZERO),
            Eq(Count(N("program", "settles_to_capability_outcome")), ONE),
            Eq(Count(N("state", "published_capability_outcome")), ZERO),
        ),
        "effects": settle_effects("native_multichannel_program"),
    }


def channel_deepen_rule():
    return {
        "name": "cc_channel_residual_deepen",
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Any trusted reactive or proactive channel outside its envelope opens the next same-typed program.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "continues_to_higher_order_capability_program", "higher"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            channel_mode(),
            Gt(Count(breached_channels()), ZERO),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
            Or(
                Eq(numeric("state", "order_limit_enabled"), ZERO),
                Lte(numeric("higher", "order"), numeric("state", "maximum_order")),
            ),
        ),
        "effects": [
            ["add_node_if_absent", "step", "CapabilityCollapseStep", {
                "collapse_state_ref": T(V("state")),
                "program_ref": T(V("program")),
                "request_epoch": T(numeric("state", "request_epoch")),
                "observed_residual_quanta": 0,
                "residual_kind": "multichannel_envelope",
                "credited": 0,
            }],
            ["add_edge", "state", "has_capability_collapse_step", "step"],
            ["add_edge", "step", "traversed_capability_program", "program"],
            ["del_edge", "state", "has_active_capability_program", "program"],
            ["add_edge", "state", "has_active_capability_program", "higher"],
            ["set_attr", "state", "current_order", T(numeric("higher", "order"))],
            ["set_attr", "state", "deepest_order", T(Max(
                numeric("state", "deepest_order"), numeric("higher", "order")))],
            ["set_attr", "state", "cognitive_evaluations",
             T(Plus(numeric("state", "cognitive_evaluations"), ONE))],
            ["set_attr", "state", "status", "deepened_by_channel_residual"],
        ],
    }


def record_step_channels_rule():
    return {
        "name": "cc_record_traversed_residual_channels",
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Keep every breached dimension as evidence; never collapse the envelope to a scalar score.",
        "match": [
            ["state", "has_capability_collapse_step", "step"],
            ["step", "traversed_capability_program", "program"],
            ["program", "has_capability_residual_channel", "channel"],
        ],
        "where": And(
            Eq(A("step", "residual_kind"), L("multichannel_envelope")),
            Eq(numeric("step", "request_epoch"), numeric("state", "request_epoch")),
            Gte(numeric("channel", "precision_quanta"),
                numeric("program", "minimum_precision_quanta")),
            Or(
                Gt(numeric("channel", "observed_quanta"),
                   numeric("channel", "boundary_quanta")),
                Gt(numeric("channel", "control_demand_quanta"),
                   numeric("channel", "proactive_boundary_quanta")),
            ),
        ),
        "effects": [
            ["add_edge", "step", "traversed_capability_residual_channel", "channel"],
            ["add_node_if_absent", "evidence", "CapabilityChannelPracticeEvidence", {
                "collapse_step_ref": T(V("step")),
                "channel_ref": T(V("channel")),
                "program_ref": T(V("program")),
                "request_epoch": T(numeric("state", "request_epoch")),
                "observed_band_quanta": T(numeric("channel", "observed_quanta")),
                "credited": 0,
            }],
            ["add_edge", "state", "has_capability_channel_practice_evidence", "evidence"],
            ["add_edge", "evidence", "evidences_capability_residual_channel", "channel"],
            ["add_edge", "evidence", "evidences_capability_program", "program"],
        ],
    }


def channel_unresolved_rule():
    return {
        "name": "cc_channel_request_synthesis_no_higher_program",
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An exhausted local envelope continues its default and exposes unresolved channels upward.",
        "match": [["state", "has_active_capability_program", "program"]],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            channel_mode(),
            Gt(Count(breached_channels()), ZERO),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ZERO),
        ),
        "effects": unresolved_effects("unresolved_channel_envelope", 1),
    }


def channel_limit_rule():
    return {
        "name": "cc_channel_stop_at_configured_order_limit",
        "area": "general_cognition",
        "order": 2,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A deployment cap stops local deepening without stopping the subsystem default.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "continues_to_higher_order_capability_program", "higher"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            channel_mode(),
            Gt(Count(breached_channels()), ZERO),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
            Eq(numeric("state", "order_limit_enabled"), ONE),
            Gt(numeric("higher", "order"), numeric("state", "maximum_order")),
        ),
        "effects": unresolved_effects("configured_order_limit", 0),
    }


def channel_outcome_refusal_rule():
    return {
        "name": "cc_channel_refuse_missing_or_ambiguous_outcome",
        "area": "general_cognition",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A contained envelope still requires one coherent outcome for its conflict domain.",
        "match": [["state", "has_active_capability_program", "program"]],
        "where": And(
            Eq(A("state", "stage"), L("collapsing")),
            channel_mode(),
            Eq(Count(breached_channels()), ZERO),
            Or(
                Gt(Count(N("program", "compiles_capability_outcome")), ONE),
                And(
                    Eq(Count(N("program", "compiles_capability_outcome")), ZERO),
                    Not(Eq(Count(N("program", "settles_to_capability_outcome")), ONE)),
                ),
            ),
        ),
        "effects": unresolved_effects("missing_or_ambiguous_outcome", 1),
    }


def continuous_arm_rule():
    return {
        "name": "cc_continuous_arm_requested_cycle",
        "area": "general_cognition_lifecycle",
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A scheduler epoch re-arms a local authority without waiting for any parent controller.",
        "match": [
            ["state", "governs_control_authority_scope", "scope"],
        ],
        "where": And(
            Eq(numeric("state", "continuous_enabled"), ONE),
            Gt(numeric("state", "cycle_request_epoch"),
               numeric("state", "completed_cycle_epoch")),
            Not(Eq(A("state", "stage"), L("collapsing"))),
            Eq(numeric("state", "collapse_armed"), ZERO),
        ),
        "effects": [
            ["set_attr", "state", "request_epoch",
             T(numeric("state", "cycle_request_epoch"))],
            ["set_attr", "state", "stage", "ready"],
            ["set_attr", "state", "cycle_status", "requested"],
            ["set_attr", "state", "collapse_armed", 1],
            ["set_attr", "state", "outcome_verified", 0],
            ["set_attr", "state", "verification_status", "pending"],
        ],
    }


def reset_effective_rule():
    return {
        "name": "cc_reset_effective_outcome",
        "area": "general_cognition_lifecycle",
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Each local cycle recomputes its effective outcome from current defaults and leases.",
        "match": [["state", "effective_capability_outcome", "outcome"]],
        "where": And(
            Eq(A("state", "stage"), L("ready")),
            Eq(numeric("state", "collapse_armed"), ONE),
        ),
        "effects": [["del_edge", "state", "effective_capability_outcome", "outcome"]],
    }


def local_default_rule():
    return {
        "name": "cc_publish_local_default_while_open",
        "area": "general_cognition_lifecycle",
        "order": 1,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The subsystem keeps cycling its fast default while unresolved cognition proceeds elsewhere.",
        "match": [
            ["state", "has_root_capability_program", "program"],
            ["program", "holds_default_capability_outcome", "outcome"],
            ["state", "governs_control_authority_scope", "scope"],
        ],
        "where": And(
            Or(
                Eq(A("state", "stage"), L("collapsing")),
                Eq(A("state", "stage"), L("unresolved")),
            ),
            Eq(Count(N("program", "holds_default_capability_outcome")), ONE),
            Eq(Count(N("state", "effective_capability_outcome")), ZERO),
            Eq(Count(valid_override_leases()), ZERO),
        ),
        "effects": [
            ["add_edge", "state", "effective_capability_outcome", "outcome"],
            ["set_attr", "state", "effective_outcome_provenance", "local_default"],
            ["set_attr", "state", "local_default_active", 1],
        ],
    }


def settled_effective_rule(existing):
    match = [
        ["state", "published_capability_outcome", "outcome"],
        ["state", "governs_control_authority_scope", "scope"],
    ]
    effects = []
    predicate = Eq(Count(N("state", "effective_capability_outcome")), ZERO)
    suffix = "empty"
    if existing:
        match.append(["state", "effective_capability_outcome", "old_outcome"])
        predicate = Not(Eq(V("old_outcome"), V("outcome")))
        effects.append(["del_edge", "state", "effective_capability_outcome", "old_outcome"])
        suffix = "replace_default"
    effects.extend([
        ["add_edge", "state", "effective_capability_outcome", "outcome"],
        ["set_attr", "state", "effective_outcome_provenance", "local_settlement"],
        ["set_attr", "state", "local_default_active", 0],
    ])
    return {
        "name": f"cc_effective_from_settlement_{suffix}",
        "area": "general_cognition_lifecycle",
        "order": 3,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A completed local correction supersedes its provisional default unless a parent lease is active.",
        "match": match,
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            Eq(Count(valid_override_leases()), ZERO),
            predicate,
        ),
        "effects": effects,
    }


def override_effective_rule(existing):
    match = [
        ["state", "governs_control_authority_scope", "scope"],
        ["scope", "receives_capability_override_lease", "lease"],
        ["lease", "overrides_with_capability_outcome", "outcome"],
    ]
    effects = []
    predicate = Eq(Count(N("state", "effective_capability_outcome")), ZERO)
    suffix = "empty"
    if existing:
        match.append(["state", "effective_capability_outcome", "old_outcome"])
        predicate = Not(Eq(V("old_outcome"), V("outcome")))
        effects.append(["del_edge", "state", "effective_capability_outcome", "old_outcome"])
        suffix = "replace"
    effects.extend([
        ["add_edge", "state", "effective_capability_outcome", "outcome"],
        ["set_attr", "state", "effective_outcome_provenance", "scoped_override_lease"],
        ["set_attr", "state", "active_override_lease_ref", T(V("lease"))],
        ["set_attr", "state", "local_default_active", 0],
    ])
    return {
        "name": f"cc_apply_scoped_override_{suffix}",
        "area": "general_cognition_lifecycle",
        "order": 4,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "One valid parent lease changes only this authority scope; the local feedback loop keeps running.",
        "match": match,
        "where": And(
            Eq(Count(valid_override_leases()), ONE),
            Eq(numeric("lease", "active"), ONE),
            Gte(numeric("state", "request_epoch"), numeric("lease", "valid_from_epoch")),
            Lte(numeric("state", "request_epoch"), numeric("lease", "expires_after_epoch")),
            predicate,
        ),
        "effects": effects,
    }


def expire_override_rule():
    return {
        "name": "cc_expire_scoped_override_lease",
        "area": "general_cognition_lifecycle",
        "order": 4,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Authority returns locally when its explicit integer lease expires.",
        "match": [
            ["state", "governs_control_authority_scope", "scope"],
            ["scope", "receives_capability_override_lease", "lease"],
        ],
        "where": And(
            Eq(numeric("lease", "active"), ONE),
            Gt(numeric("state", "cycle_request_epoch"),
               numeric("lease", "expires_after_epoch")),
        ),
        "effects": [
            ["set_attr", "lease", "active", 0],
            ["set_attr", "lease", "status", "expired"],
        ],
    }


def override_conflict_rule():
    return {
        "name": "cc_refuse_overlapping_override_leases",
        "area": "general_cognition_lifecycle",
        "order": 4,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Two authorities cannot silently command the same conflict domain.",
        "match": [["state", "governs_control_authority_scope", "scope"]],
        "where": Gt(Count(valid_override_leases()), ONE),
        "effects": [
            ["set_attr", "state", "override_status", "conflicting_leases"],
            ["set_attr", "state", "synthesis_requested", 1],
        ],
    }


def residual_report_rule():
    return {
        "name": "cc_publish_unresolved_channels_to_parent_scope",
        "area": "general_cognition_residual",
        "order": 5,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "An exhausted subsystem sends only unresolved typed residuals upward, not its entire sensorium.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "has_capability_residual_channel", "channel"],
            ["state", "governs_control_authority_scope", "scope"],
            ["scope", "reports_capability_residual_to", "parent_scope"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("unresolved")),
            channel_mode(),
            Gte(numeric("channel", "precision_quanta"),
                numeric("program", "minimum_precision_quanta")),
            Or(
                Gt(numeric("channel", "observed_quanta"),
                   numeric("channel", "boundary_quanta")),
                Gt(numeric("channel", "control_demand_quanta"),
                   numeric("channel", "proactive_boundary_quanta")),
            ),
        ),
        "effects": [
            ["add_node_if_absent", "report", "CapabilityResidualReport", {
                "collapse_state_ref": T(V("state")),
                "program_ref": T(V("program")),
                "channel_ref": T(V("channel")),
                "request_epoch": T(numeric("state", "request_epoch")),
                "observed_quanta": T(numeric("channel", "observed_quanta")),
                "boundary_quanta": T(numeric("channel", "boundary_quanta")),
                "control_demand_quanta": T(numeric("channel", "control_demand_quanta")),
                "status": "open",
            }],
            ["add_edge", "scope", "has_capability_residual_report", "report"],
            ["add_edge", "report", "describes_capability_residual_channel", "channel"],
            ["add_edge", "report", "escalates_to_control_authority_scope", "parent_scope"],
            ["set_attr", "state", "residual_reported_upward", 1],
        ],
    }


def discover_coupled_authority_rule():
    return {
        "name": "cc_discover_coupled_authority_scopes",
        "area": "general_cognition_authority",
        "order": 5,
        "latency_class": "background",
        "batch": False,
        "comment": "Observed causal interference, not anatomy names, discovers which effectors require joint settlement.",
        "match": [
            ["observation", "first_control_authority_scope", "first_scope"],
            ["observation", "second_control_authority_scope", "second_scope"],
            ["observation", "recommends_joint_control_authority_scope", "joint_scope"],
        ],
        "where": And(
            Gt(numeric("observation", "interference_quanta"),
               numeric("observation", "interference_boundary_quanta")),
            Gte(numeric("observation", "precision_quanta"),
                numeric("observation", "minimum_precision_quanta")),
            Eq(numeric("observation", "processed"), ZERO),
        ),
        "effects": [
            ["add_edge", "first_scope", "requires_joint_settlement_with", "second_scope"],
            ["add_edge", "second_scope", "requires_joint_settlement_with", "first_scope"],
            ["add_edge", "joint_scope", "coordinates_child_control_authority_scope", "first_scope"],
            ["add_edge", "joint_scope", "coordinates_child_control_authority_scope", "second_scope"],
            ["add_node_if_absent", "residual", "CapabilityCouplingResidual", {
                "observation_ref": T(V("observation")),
                "interference_quanta": T(numeric("observation", "interference_quanta")),
                "status": "requires_combined_program",
            }],
            ["add_edge", "joint_scope", "has_capability_coupling_residual", "residual"],
            ["set_attr", "observation", "processed", 1],
        ],
    }


def complete_cycle_rule():
    return {
        "name": "cc_complete_continuous_cycle",
        "area": "general_cognition_lifecycle",
        "order": 9,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Completion advances only the local authority epoch; independent scopes continue at their own rates.",
        "match": [["state", "governs_control_authority_scope", "scope"]],
        "where": And(
            Eq(numeric("state", "continuous_enabled"), ONE),
            Or(
                Eq(A("state", "stage"), L("settled")),
                Eq(A("state", "stage"), L("unresolved")),
            ),
            Gt(numeric("state", "request_epoch"),
               numeric("state", "completed_cycle_epoch")),
        ),
        "effects": [
            ["set_attr", "state", "completed_cycle_epoch",
             T(numeric("state", "request_epoch"))],
            ["set_attr", "state", "cycle_status", "completed"],
        ],
    }


def provision_channel_practice_trace_rule():
    return {
        "name": "cc_provision_channel_practice_trace",
        "area": "general_cognition_learning",
        "order": 3,
        "latency_class": "background",
        "batch": True,
        "comment": "Each residual dimension earns evidence independently at its observed integer band.",
        "match": [
            ["state", "has_capability_channel_practice_evidence", "evidence"],
            ["evidence", "evidences_capability_residual_channel", "channel"],
            ["evidence", "evidences_capability_program", "program"],
            ["state", "published_capability_outcome", "outcome"],
            ["state", "in_capability_context", "context"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            channel_mode(),
            Or(
                Eq(numeric("state", "outcome_verified"), ONE),
                Eq(A("state", "verification_status"), L("failure")),
            ),
            Eq(numeric("evidence", "credited"), ZERO),
        ),
        "effects": [
            ["add_node_if_absent", "trace", "CapabilityChannelPracticeTrace", {
                "program_ref": T(V("program")),
                "channel_ref": T(V("channel")),
                "outcome_ref": T(V("outcome")),
                "residual_band_quanta": T(numeric("evidence", "observed_band_quanta")),
                "receipt_count": 0,
                "failure_receipt_count": 0,
                "consolidated": 0,
            }],
            ["add_edge", "program", "has_capability_channel_practice_trace", "trace"],
            ["add_edge", "trace", "practices_capability_residual_channel", "channel"],
            ["add_edge", "trace", "practices_capability_outcome", "outcome"],
            ["add_edge", "trace", "verified_in_capability_context", "context"],
        ],
    }


def credit_channel_practice_rule(success):
    suffix = "success" if success else "failure"
    verification = (
        Eq(numeric("state", "outcome_verified"), ONE)
        if success else Eq(A("state", "verification_status"), L("failure"))
    )
    effects = [
        ["set_attr", "evidence", "credited", 1 if success else -1],
        ["set_attr", "evidence", "credit_provenance", f"verified_channel_{suffix}"],
    ]
    counter = "receipt_count" if success else "failure_receipt_count"
    effects.insert(0, [
        "set_attr", "trace", counter,
        T(Plus(numeric("trace", counter), ONE)),
    ])
    return {
        "name": f"cc_credit_channel_practice_{suffix}",
        "area": "general_cognition_learning",
        "order": 4,
        "latency_class": "background",
        "batch": False,
        "comment": "Channel evidence is serialized so simultaneous subsystem receipts cannot overwrite one another.",
        "match": [
            ["state", "has_capability_channel_practice_evidence", "evidence"],
            ["evidence", "evidences_capability_residual_channel", "channel"],
            ["evidence", "evidences_capability_program", "program"],
            ["state", "published_capability_outcome", "outcome"],
            ["program", "has_capability_channel_practice_trace", "trace"],
            ["trace", "practices_capability_residual_channel", "channel"],
            ["trace", "practices_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            channel_mode(),
            verification,
            Eq(numeric("evidence", "credited"), ZERO),
            Eq(numeric("trace", "residual_band_quanta"),
               numeric("evidence", "observed_band_quanta")),
        ),
        "effects": effects,
    }


def compile_channel_practice_rule():
    return {
        "name": "cc_compile_channel_capability_boundary",
        "area": "general_cognition_learning",
        "order": 6,
        "latency_class": "background",
        "batch": False,
        "comment": "Evidence expands only its own capability dimension and installs the practiced outcome basin.",
        "match": [
            ["program", "has_capability_channel_practice_trace", "trace"],
            ["trace", "practices_capability_residual_channel", "channel"],
            ["trace", "practices_capability_outcome", "outcome"],
        ],
        "where": And(
            Gte(numeric("trace", "receipt_count"),
                numeric("program", "required_practice_receipts")),
            Gt(numeric("program", "required_practice_receipts"), ZERO),
            Gte(Count(N("trace", "verified_in_capability_context")),
                numeric("program", "required_practice_contexts")),
            Lte(numeric("trace", "failure_receipt_count"),
                numeric("program", "maximum_practice_failures")),
            Lte(numeric("program", "compiled_execution_failure_count"),
                numeric("program", "maximum_practice_failures")),
            Not(Eq(A("program", "learning_status"), L("revaluation_required"))),
            Or(
                Eq(numeric("program", "consolidation_required"), ZERO),
                Eq(numeric("trace", "consolidated"), ONE),
            ),
            Gt(numeric("trace", "residual_band_quanta"),
               numeric("channel", "boundary_quanta")),
        ),
        "effects": [
            ["set_attr", "channel", "boundary_quanta",
             T(numeric("trace", "residual_band_quanta"))],
            ["add_edge", "program", "compiles_capability_outcome", "outcome"],
            ["set_attr", "program", "learning_status", "multichannel_muscle_memory_compiled"],
        ],
    }


def decompile_failed_channel_rule():
    return {
        "name": "cc_decompile_failed_channel_capability",
        "area": "general_cognition_learning",
        "order": 7,
        "latency_class": "background",
        "batch": False,
        "comment": "A failed dimension retracts its learned boundary and reopens the higher-order route.",
        "match": [
            ["program", "has_capability_channel_practice_trace", "trace"],
            ["trace", "practices_capability_residual_channel", "channel"],
            ["trace", "practices_capability_outcome", "outcome"],
            ["program", "compiles_capability_outcome", "outcome"],
        ],
        "where": Gt(
            numeric("trace", "failure_receipt_count"),
            numeric("program", "maximum_practice_failures"),
        ),
        "effects": [
            ["set_attr", "channel", "boundary_quanta",
             T(numeric("channel", "baseline_boundary_quanta"))],
            ["del_edge", "program", "compiles_capability_outcome", "outcome"],
            ["set_attr", "program", "learning_status", "channel_revaluation_required"],
        ],
    }


def credit_compiled_execution_failure_rule():
    return {
        "name": "cc_credit_compiled_execution_failure",
        "area": "general_cognition_learning",
        "order": 6,
        "latency_class": "background",
        "batch": False,
        "comment": "Failure of an automatic execution is direct evidence against the compiled basin, even without deepening.",
        "match": [
            ["state", "has_active_capability_program", "program"],
            ["program", "compiles_capability_outcome", "outcome"],
            ["state", "published_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            Eq(A("state", "verification_status"), L("failure")),
            Not(Eq(A("state", "compiled_failure_processed_epoch"),
                   A("state", "request_epoch"))),
        ),
        "effects": [
            ["set_attr", "program", "compiled_execution_failure_count", T(Plus(
                numeric("program", "compiled_execution_failure_count"), ONE))],
            ["set_attr", "state", "compiled_failure_processed_epoch",
             T(numeric("state", "request_epoch"))],
        ],
    }


def revoke_failed_compiled_outcome_rule():
    return {
        "name": "cc_revoke_failed_compiled_outcome",
        "area": "general_cognition_learning",
        "order": 7,
        "latency_class": "background",
        "batch": False,
        "comment": "Devaluation or repeated execution failure restores the pre-practice envelope and higher-order access.",
        "match": [["program", "compiles_capability_outcome", "outcome"]],
        "where": Gt(
            numeric("program", "compiled_execution_failure_count"),
            numeric("program", "maximum_practice_failures"),
        ),
        "effects": [
            ["del_edge", "program", "compiles_capability_outcome", "outcome"],
            ["set_attr", "program", "capability_boundary_quanta",
             T(numeric("program", "baseline_capability_boundary_quanta"))],
            ["set_attr", "program", "learning_status", "revaluation_required"],
        ],
    }


def reset_failed_compiled_channel_rule():
    return {
        "name": "cc_reset_failed_compiled_channel_boundary",
        "area": "general_cognition_learning",
        "order": 7,
        "latency_class": "background",
        "batch": True,
        "comment": "Every learned dimension of a failed basin returns to its graph-held baseline.",
        "match": [["program", "has_capability_residual_channel", "channel"]],
        "where": And(
            Eq(A("program", "learning_status"), L("revaluation_required")),
            Gt(numeric("channel", "boundary_quanta"),
               numeric("channel", "baseline_boundary_quanta")),
        ),
        "effects": [[
            "set_attr", "channel", "boundary_quanta",
            T(numeric("channel", "baseline_boundary_quanta")),
        ]],
    }


def provision_practice_trace_rule():
    return {
        "name": "cc_provision_verified_practice_trace",
        "area": "general_cognition_learning",
        "order": 3,
        "latency_class": "background",
        "batch": True,
        "comment": "Verified success or failure becomes context- and residual-band-specific evidence.",
        "match": [
            ["state", "has_capability_collapse_step", "step"],
            ["step", "traversed_capability_program", "program"],
            ["state", "published_capability_outcome", "outcome"],
            ["state", "in_capability_context", "context"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            scalar_mode(),
            Or(
                Eq(numeric("state", "outcome_verified"), ONE),
                Eq(A("state", "verification_status"), L("failure")),
            ),
            Eq(numeric("step", "credited"), ZERO),
        ),
        "effects": [
            ["add_node_if_absent", "trace", "CapabilityPracticeTrace", {
                "program_ref": T(V("program")),
                "outcome_ref": T(V("outcome")),
                "residual_band_quanta": T(numeric("step", "observed_residual_quanta")),
                "receipt_count": 0,
                "failure_receipt_count": 0,
                "maximum_practiced_residual_quanta": 0,
                "consolidated": 0,
            }],
            ["add_edge", "program", "has_capability_practice_trace", "trace"],
            ["add_edge", "trace", "practices_capability_outcome", "outcome"],
            ["add_edge", "trace", "verified_in_capability_context", "context"],
        ],
    }


def credit_practice_rule():
    return {
        "name": "cc_credit_verified_practice",
        "area": "general_cognition_learning",
        "order": 4,
        "latency_class": "background",
        "batch": False,
        "comment": "Practice credits a reproduced task-level outcome basin at one evidenced residual band.",
        "match": [
            ["state", "has_capability_collapse_step", "step"],
            ["step", "traversed_capability_program", "program"],
            ["state", "published_capability_outcome", "outcome"],
            ["program", "has_capability_practice_trace", "trace"],
            ["trace", "practices_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            scalar_mode(),
            Eq(numeric("state", "outcome_verified"), ONE),
            Eq(numeric("step", "credited"), ZERO),
            Eq(numeric("trace", "residual_band_quanta"),
               numeric("step", "observed_residual_quanta")),
        ),
        "effects": [
            ["set_attr", "trace", "receipt_count",
             T(Plus(numeric("trace", "receipt_count"), ONE))],
            ["set_attr", "trace", "maximum_practiced_residual_quanta",
             T(Max(numeric("trace", "maximum_practiced_residual_quanta"),
                   numeric("step", "observed_residual_quanta")))],
            ["set_attr", "step", "credited", 1],
            ["set_attr", "step", "credit_provenance", "verified_deeper_settlement"],
        ],
    }


def credit_practice_failure_rule():
    return {
        "name": "cc_credit_verified_practice_failure",
        "area": "general_cognition_learning",
        "order": 4,
        "latency_class": "background",
        "batch": False,
        "comment": "A failed reproduction is evidence against capability, never a successful receipt.",
        "match": [
            ["state", "has_capability_collapse_step", "step"],
            ["step", "traversed_capability_program", "program"],
            ["state", "published_capability_outcome", "outcome"],
            ["program", "has_capability_practice_trace", "trace"],
            ["trace", "practices_capability_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            scalar_mode(),
            Eq(A("state", "verification_status"), L("failure")),
            Eq(numeric("step", "credited"), ZERO),
            Eq(numeric("trace", "residual_band_quanta"),
               numeric("step", "observed_residual_quanta")),
        ),
        "effects": [
            ["set_attr", "trace", "failure_receipt_count",
             T(Plus(numeric("trace", "failure_receipt_count"), ONE))],
            ["set_attr", "step", "credited", -1],
            ["set_attr", "step", "credit_provenance", "verified_failure"],
        ],
    }


def consolidate_practice_rule():
    return {
        "name": "cc_consolidate_practice_trace",
        "area": "general_cognition_learning",
        "order": 5,
        "latency_class": "background",
        "batch": False,
        "comment": "Optional offline consolidation is explicit graph evidence, not assumed from immediate performance.",
        "match": [
            ["trace", "has_capability_consolidation_receipt", "receipt"],
        ],
        "where": And(
            Eq(numeric("receipt", "verified"), ONE),
            Eq(numeric("trace", "consolidated"), ZERO),
        ),
        "effects": [
            ["set_attr", "trace", "consolidated", 1],
            ["set_attr", "trace", "consolidation_epoch",
             T(numeric("receipt", "consolidation_epoch"))],
        ],
    }


def compile_practice_rule():
    return {
        "name": "cc_compile_muscle_memory",
        "area": "general_cognition_learning",
        "order": 5,
        "latency_class": "background",
        "batch": False,
        "comment": "Repeated, context-diverse, failure-bounded evidence compiles a task-level outcome basin downward.",
        "match": [
            ["program", "has_capability_practice_trace", "trace"],
            ["trace", "practices_capability_outcome", "outcome"],
        ],
        "where": And(
            Gte(numeric("trace", "receipt_count"),
                numeric("program", "required_practice_receipts")),
            Gt(numeric("program", "required_practice_receipts"), ZERO),
            Gte(Count(N("trace", "verified_in_capability_context")),
                numeric("program", "required_practice_contexts")),
            Lte(numeric("trace", "failure_receipt_count"),
                numeric("program", "maximum_practice_failures")),
            Lte(numeric("program", "compiled_execution_failure_count"),
                numeric("program", "maximum_practice_failures")),
            Not(Eq(A("program", "learning_status"), L("revaluation_required"))),
            Or(
                Eq(numeric("program", "consolidation_required"), ZERO),
                Eq(numeric("trace", "consolidated"), ONE),
            ),
            Eq(Count(N("program", "compiles_capability_outcome")), ZERO),
        ),
        "effects": [
            ["add_edge", "program", "compiles_capability_outcome", "outcome"],
            ["set_attr", "program", "capability_boundary_quanta", T(Max(
                numeric("program", "capability_boundary_quanta"),
                numeric("trace", "maximum_practiced_residual_quanta")))],
            ["set_attr", "program", "compiled_practice_receipts",
             T(numeric("trace", "receipt_count"))],
            ["set_attr", "program", "compiled_outcome_ref", T(V("outcome"))],
            ["set_attr", "program", "learning_status", "muscle_memory_compiled"],
        ],
    }


def decompile_failed_practice_rule():
    return {
        "name": "cc_decompile_failed_muscle_memory",
        "area": "general_cognition_learning",
        "order": 6,
        "latency_class": "background",
        "batch": False,
        "comment": "Failure or devaluation reopens cognition instead of preserving an unsafe automatic boundary.",
        "match": [
            ["program", "has_capability_practice_trace", "trace"],
            ["trace", "practices_capability_outcome", "outcome"],
            ["program", "compiles_capability_outcome", "outcome"],
        ],
        "where": Gt(
            numeric("trace", "failure_receipt_count"),
            numeric("program", "maximum_practice_failures"),
        ),
        "effects": [
            ["del_edge", "program", "compiles_capability_outcome", "outcome"],
            ["set_attr", "program", "capability_boundary_quanta",
             T(numeric("program", "baseline_capability_boundary_quanta"))],
            ["set_attr", "program", "learning_status", "revaluation_required"],
            ["set_attr", "program", "compiled_practice_receipts", 0],
        ],
    }


def productions():
    specs = [
        ("CapabilityCollapseState", "has_root_capability_program", "CapabilityProgram"),
        ("CapabilityCollapseState", "has_active_capability_program", "CapabilityProgram"),
        ("CapabilityCollapseState", "governs_control_authority_scope", "ControlAuthorityScope"),
        ("CapabilityProgram", "continues_to_higher_order_capability_program", "CapabilityProgram"),
        ("CapabilityProgram", "settles_to_capability_outcome", "CapabilityOutcome"),
        ("CapabilityProgram", "compiles_capability_outcome", "CapabilityOutcome"),
        ("CapabilityProgram", "holds_default_capability_outcome", "CapabilityOutcome"),
        ("CapabilityProgram", "has_capability_residual_channel", "CapabilityResidualChannel"),
        ("CapabilityCollapseState", "published_capability_outcome", "CapabilityOutcome"),
        ("CapabilityCollapseState", "effective_capability_outcome", "CapabilityOutcome"),
        ("CapabilityCollapseState", "has_capability_collapse_step", "CapabilityCollapseStep"),
        ("CapabilityCollapseStep", "traversed_capability_program", "CapabilityProgram"),
        ("CapabilityCollapseStep", "traversed_capability_residual_channel", "CapabilityResidualChannel"),
        ("CapabilityCollapseState", "has_capability_channel_practice_evidence", "CapabilityChannelPracticeEvidence"),
        ("CapabilityChannelPracticeEvidence", "evidences_capability_residual_channel", "CapabilityResidualChannel"),
        ("CapabilityChannelPracticeEvidence", "evidences_capability_program", "CapabilityProgram"),
        ("CapabilityProgram", "has_capability_practice_trace", "CapabilityPracticeTrace"),
        ("CapabilityProgram", "has_capability_channel_practice_trace", "CapabilityChannelPracticeTrace"),
        ("CapabilityPracticeTrace", "practices_capability_outcome", "CapabilityOutcome"),
        ("CapabilityChannelPracticeTrace", "practices_capability_outcome", "CapabilityOutcome"),
        ("CapabilityChannelPracticeTrace", "practices_capability_residual_channel", "CapabilityResidualChannel"),
        ("CapabilityPracticeTrace", "verified_in_capability_context", "CapabilityContext"),
        ("CapabilityChannelPracticeTrace", "verified_in_capability_context", "CapabilityContext"),
        ("CapabilityCollapseState", "in_capability_context", "CapabilityContext"),
        ("CapabilityPracticeTrace", "has_capability_consolidation_receipt", "CapabilityConsolidationReceipt"),
        ("CapabilityChannelPracticeTrace", "has_capability_consolidation_receipt", "CapabilityConsolidationReceipt"),
        ("ControlAuthorityScope", "reports_capability_residual_to", "ControlAuthorityScope"),
        ("ControlAuthorityScope", "has_capability_residual_report", "CapabilityResidualReport"),
        ("CapabilityResidualReport", "describes_capability_residual_channel", "CapabilityResidualChannel"),
        ("CapabilityResidualReport", "escalates_to_control_authority_scope", "ControlAuthorityScope"),
        ("ControlAuthorityScope", "receives_capability_override_lease", "CapabilityOverrideLease"),
        ("CapabilityOverrideLease", "overrides_with_capability_outcome", "CapabilityOutcome"),
        ("ControlCouplingObservation", "first_control_authority_scope", "ControlAuthorityScope"),
        ("ControlCouplingObservation", "second_control_authority_scope", "ControlAuthorityScope"),
        ("ControlCouplingObservation", "recommends_joint_control_authority_scope", "ControlAuthorityScope"),
        ("ControlAuthorityScope", "requires_joint_settlement_with", "ControlAuthorityScope"),
        ("ControlAuthorityScope", "coordinates_child_control_authority_scope", "ControlAuthorityScope"),
        ("ControlAuthorityScope", "has_capability_coupling_residual", "CapabilityCouplingResidual"),
        ("CapabilityOutcome", "preserves_capability_invariant", "CapabilityInvariant"),
        ("CapabilityOutcome", "controls_authority_scope", "ControlAuthorityScope"),
    ]
    return [
        {
            "provenance": f"seed:capability_collapse:{edge_type}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def build():
    rules = [
        continuous_arm_rule(),
        reset_published_rule(),
        reset_active_rule(),
        reset_effective_rule(),
        open_rule(),
        local_default_rule(),
        compiled_settle_rule(),
        native_settle_rule(),
        unresolved_outcome_rule(),
        deepen_rule(),
        unresolved_no_higher_rule(),
        unresolved_limit_rule(),
        unresolved_ambiguous_higher_rule(),
        channel_compiled_settle_rule(),
        channel_native_settle_rule(),
        channel_outcome_refusal_rule(),
        channel_deepen_rule(),
        record_step_channels_rule(),
        channel_unresolved_rule(),
        channel_limit_rule(),
        settled_effective_rule(False),
        settled_effective_rule(True),
        expire_override_rule(),
        override_effective_rule(False),
        override_effective_rule(True),
        override_conflict_rule(),
        residual_report_rule(),
        discover_coupled_authority_rule(),
        provision_channel_practice_trace_rule(),
        credit_channel_practice_rule(True),
        credit_channel_practice_rule(False),
        compile_channel_practice_rule(),
        decompile_failed_channel_rule(),
        credit_compiled_execution_failure_rule(),
        revoke_failed_compiled_outcome_rule(),
        reset_failed_compiled_channel_rule(),
        provision_practice_trace_rule(),
        credit_practice_rule(),
        credit_practice_failure_rule(),
        consolidate_practice_rule(),
        compile_practice_rule(),
        decompile_failed_practice_rule(),
        complete_cycle_rule(),
    ]
    return {
        "id": "capability_collapse",
        "version": "2.0.0",
        "self_load_only": True,
        "depends_on": [],
        "area": "general_cognition",
        "description": (
            "Domain-neutral M-by-N nested control: M parallel authority scopes, each "
            "holding an arbitrary order-N CapabilityProgram chain. Local defaults keep "
            "cycling while typed integer residual channels escalate upward; scoped "
            "top-down leases may constrain the effective outcome without stopping local "
            "feedback. Reactive error and proactive control demand share multidimensional "
            "envelopes. Context-, failure-, and consolidation-bearing practice compiles "
            "task-level outcome basins downward."
        ),
        "microtheory": {
            "name": "capability_collapse",
            "description": (
                "There is no privileged System 2 or organism-wide singleton. Each learned "
                "conflict domain recursively deepens only beyond its capability envelope; "
                "causal interference can discover larger joint domains, and verified "
                "corrections settle back into lower local defaults."
            ),
        },
        "nodes": [],
        "edges": [],
        "productions": productions(),
        "rules": rules,
    }


def main():
    path = ROOT / "seeds" / "capability_collapse.json"
    path.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {path} ({len(build()['rules'])} rules)")


if __name__ == "__main__":
    main()
