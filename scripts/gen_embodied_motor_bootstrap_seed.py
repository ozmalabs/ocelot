#!/usr/bin/env python3
"""Generate graph-native bootstrap proposals from an opaque body interface.

The body boundary publishes only a relation system: opaque actuator tokens,
topology membership, and an integer trial contract.  This seed turns that
observed structure into singleton and already-compatible compound candidates.
It neither names an anatomical actuator nor chooses an action in Python.

An ``EmbodiedMotorProgram`` remains output-null until a graph-owned Pareto
frontier and curiosity collapse select it for a situated developmental goal.
The selected program uses the exact token sequence supplied by the body
boundary, in the same order as its matching integer weights.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def T(term): return {"__term__": term}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def Neg(arg): return {"type": "Neg", "arg": arg}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Times(*items): return {"type": "Times", "items": list(items)}
def Min(*items): return {"type": "Min", "items": list(items)}
def If(cond, then, other): return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def Abs(arg): return {"type": "Abs", "arg": arg}
def StringConcat(*parts): return {"type": "StringConcat", "parts": list(parts)}
def ToJsonString(value): return {"type": "ToJsonString", "value": value}
def N(name, edge): return {"type": "Neighbours", "node": V(name), "edge_type": edge}
def IN(name, edge): return {"type": "InNeighbours", "node": V(name), "edge_type": edge}
def SetT(*items): return {"type": "SetT", "items": list(items)}
def Count(source): return {"type": "Count", "source": source}
def Sum(source, var, value): return {
    "type": "Sum", "source": source, "var_name": var, "value": value,
}
def MapList(source, var, value): return {
    "type": "MapList", "source": source, "var_name": var, "value": value,
}
def Filter(source, var, predicate): return {
    "type": "Filter", "source": source, "var_name": var,
    "predicate": predicate,
}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var,
    "predicate": predicate,
}
def Argmin(source, var, value, default): return {
    "type": "Argmin", "source": source, "var_name": var,
    "value": value, "default": default,
}
def P0(name, key): return Plus(A(name, key), L(0))


CONTRACT_FIELDS = (
    "simulator_weight_scale_units",
    "displacement_units_per_metre",
    "energy_units_per_joule",
    "load_units_per_newton",
)
PARETO_DIMENSIONS = (
    ("untried_local_practice", "maximize"),
    ("topology_coverage", "maximize"),
    ("activation_effort", "minimize"),
    ("structural_novelty", "maximize"),
    ("receipt_grounded_structural_reuse", "maximize"),
    ("receipt_grounded_local_coordination_information", "maximize"),
)


def absent(source, var="existing"):
    return Not(Exists(source, var, L(True)))


def no_bound_selection_for_this_capability():
    """No selection is in flight FOR THE CAPABILITY THIS RESIDUAL IS ABOUT.

    `has_embodied_motor_bootstrap_selection` is a single current-selection
    pointer, released by `emb_retire_settled_motor_selection_and_reopen_pareto_frontier`
    once the trial's receipt closes; the checkin/reset-rearm loop binds the next
    one immediately, so the episode-wide gap is momentary. A SUSPENDED
    capability runs no trials of its own, so it essentially never sees that gap
    open -- its revision was gated on a DIFFERENT capability's in-flight trial.

    Measured 2026-08-07 by cumulative prefix scan on a live 6-hour checkpoint:
    with the spurious `causal_yield_units == 0` test removed, the conjunction
    carries 58 bindings through the entire supervisory state and dies exactly
    here. The bound selection targeted `surface_contact_mapping` (ordinal 3,
    active) while the residual concerned `effector_consequence_survey`
    (ordinal 1, meta_suspended).

    PROPOSING A REVISION IS NOT AN EPISODE-EXCLUSIVE ACT; ENACTING ONE IS. The
    SELECT rule and both ENACT rules rebind the pointer and keep the
    episode-wide guard; only the two PROPOSE rules are scoped to the capability
    the residual concerns, which the selection already declares via
    `targets_developmental_capability`.
    """
    return Not(Exists(
        N("motor_episode", "has_embodied_motor_bootstrap_selection"),
        "bound_selection",
        Exists(
            {"type": "Neighbours", "node": V("bound_selection"),
             "edge_type": "targets_developmental_capability"},
            "bound_capability",
            Eq(V("bound_capability"), V("capability")),
        ),
    ))

def contract_is_usable():
    """Admission check for the mechanical, integer-only trial contract."""
    return And(
        Eq(A("contract", "integer_native"), L(1)),
        Gt(A("contract", "simulator_weight_scale_units"), L(0)),
        Gt(A("contract", "minimum_nonzero_weight_units"), L(0)),
        Gt(A("contract", "minimum_actuation_frames"), L(0)),
        Gt(A("contract", "maximum_observation_horizon_frames"), L(0)),
        Gt(A("contract", "displacement_units_per_metre"), L(0)),
        Gt(A("contract", "energy_units_per_joule"), L(0)),
        Gt(A("contract", "load_units_per_newton"), L(0)),
    )


def _program_attrs(source, members):
    """Map an arbitrary observed member set into transducer-compatible data."""
    return {
        "status": "candidate",
        "integer_native": 1,
        "output_authority": 0,
        "source_affordance_ref": T(V(source)),
        "morphology_epoch": T(A("body", "morphology_epoch")),
        # These are exact, opaque host tokens.  There is no token->limb map.
        "simulator_tokens": T(MapList(members, "member", A("member", "opaque_token"))),
        "simulator_weight_units": T(MapList(
            members, "member", A("contract", "minimum_nonzero_weight_units")
        )),
        **{field: T(A("contract", field)) for field in CONTRACT_FIELDS},
    }


def _prior_attrs(source):
    return {
        "kind": "opaque_topology_exploration",
        "integer_native": 1,
        "output_authority": 0,
        "source_affordance_ref": T(V(source)),
        "morphology_epoch": T(A("body", "morphology_epoch")),
    }


def open_motor_episode_rule():
    return {
        "name": "emb_open_output_null_motor_bootstrap_episode",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A developmental episode with a mechanically observed body opens one output-null candidate container. The adapter never selects a candidate.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_body_schema", "body"],
        ],
        "where": And(
            Eq(A("body", "integer_native"), L(1)),
            absent(N("episode", "has_embodied_motor_episode")),
        ),
        "effects": [
            ["add_node", "motor_episode", "EmbodiedMotorEpisode", {
                "status": "bootstrap_candidates", "integer_native": 1,
                "output_authority": 0,
                "morphology_epoch": T(A("body", "morphology_epoch")),
            }],
            ["add_edge", "episode", "has_embodied_motor_episode", "motor_episode"],
            ["add_edge", "motor_episode", "for_embodied_body_schema", "body"],
        ],
    }


def open_profile_rule():
    return {
        "name": "emb_open_integer_pareto_frontier_for_observed_motor_topology",
        "area": "cognitive_pareto",
        "latency_class": "hard_realtime",
        "comment": "The bootstrap frontier makes novelty, topology coverage, and activation effort explicit rather than hiding a scalar reward in the adapter.",
        "match": [["episode", "has_embodied_motor_episode", "motor_episode"]],
        "where": absent(N("motor_episode", "has_embodied_motor_bootstrap_profile")),
        "effects": [
            ["add_node", "profile", "ParetoProfile", {
                "name": "opaque_motor_topology_bootstrap",
                "dimension_count": len(PARETO_DIMENSIONS),
                "integer_native": 1, "scalarized": 0,
                "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_profile", "profile"],
            *[
                ["add_node", f"dimension_{ordinal}", "ParetoDimension", {
                    "name": name, "ordinal": ordinal, "direction": direction,
                    "integer_native": 1,
                }]
                for ordinal, (name, direction) in enumerate(PARETO_DIMENSIONS)
            ],
            *[
                ["add_edge", "profile", "has_pareto_dimension", f"dimension_{ordinal}"]
                for ordinal in range(len(PARETO_DIMENSIONS))
            ],
        ],
    }


def _candidate_effects(source, members):
    effort = Sum(
        members, "member", Abs(A("contract", "minimum_nonzero_weight_units"))
    )
    count = Count(members)
    return [
        ["add_node_if_absent", "prior", "EmbodiedMotorPrior", _prior_attrs(source)],
        ["add_node_if_absent", "program", "EmbodiedMotorProgram", _program_attrs(source, members)],
        # Identity contains only immutable observed structure. General Pareto
        # mutates dominance and grounded receipts mutate experience, so neither
        # can be a key that mints a duplicate topology candidate.
        ["add_node_if_absent", "candidate", "ParetoCandidate", {
            "kind": "opaque_motor_topology_bootstrap",
            "status": "candidate", "integer_native": 1,
            "output_authority": 0,
            "source_affordance_ref": T(V(source)),
            "morphology_epoch": T(A("body", "morphology_epoch")),
            "member_count": T(count),
            "activation_effort_units": T(effort),
            "actuator_ordinal": T(A(source, "ordinal")),
            # A source may be a topology bundle synthesized from one
            # grounded local consequence.  Plain observed affordances have
            # no such fields and therefore contribute exact integer zero.
            "predicted_forward_units": T(P0(source, "predicted_forward_units")),
            "predicted_energy_units": T(P0(source, "predicted_energy_units")),
            "predicted_peak_load_units": T(P0(source, "predicted_peak_load_units")),
            "unverified_coordination_information_units": T(P0(source, "unverified_coordination_information_units")),
        }],
        ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_candidate", "candidate"],
        ["add_edge", "profile", "has_pareto_candidate", "candidate"],
        ["add_edge", "candidate", "uses_embodied_motor_prior", "prior"],
        ["add_edge", "candidate", "proposes_embodied_motor_program", "program"],
        ["add_edge", "program", "synthesizes_embodied_motor_prior", "prior"],
        ["add_edge", "candidate", "models_opaque_affordance", source],
    ]


def initialize_candidate_state_rule():
    """Attach mutable learning state after immutable identity is minted."""
    return {
        "name": "emb_initialize_mutable_state_on_immutable_motor_candidate",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Candidate/program deduplication keys are observed topology only. This one-shot graph initialization supplies mutable prediction, practice and duration state without making any of it part of identity.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "candidate"],
            ["candidate", "proposes_embodied_motor_program", "program"],
        ],
        "where": absent(N("candidate", "has_embodied_motor_bootstrap_initialization")),
        "effects": [
            ["add_node", "initialization", "EmbodiedMotorBootstrapInitialization", {
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "candidate", "has_embodied_motor_bootstrap_initialization", "initialization"],
            ["set_attr", "candidate", "experience_units", 0],
            # The declared mechanical floor. It is immediately restated from
            # the body's aperture by `emb_apply_body_temporal_aperture_to_program`
            # in the same fixpoint — which is exactly the inheritance a fresh
            # program is owed — so this is a floor, not a starting rung.
            ["set_attr", "program", "simulator_frames", T(A("contract", "minimum_actuation_frames"))],
            # THE HINT, AT ITS NEUTRAL DEFAULT. A program scales the body's
            # aperture; it does not hold one. 0 means "no scaling", declared
            # rather than left absent so the mechanism is visible in the graph.
            # NOTHING MOVES IT YET: a hint is a second-order adaptation and
            # would need evidence that THIS program repeatedly needs more or
            # less than the body baseline. That evidence is not collected, so
            # inventing a rule to move it would be authoring a number, not
            # measuring one.
            # PRESERVED IF ALREADY SET. Declaring the neutral default must not
            # be able to erase a hint some other rule authored: absent becomes
            # 0, present stays. `Eq(Attr, Lit None)` is true only for a MISSING
            # key, which is the one place in this tree where absent and zero can
            # be told apart.
            ["set_attr", "program", "aperture_hint_log_units", T(If(
                Eq(A("program", "aperture_hint_log_units"), L(None)),
                L(0), A("program", "aperture_hint_log_units"),
            ))],
            ["set_attr", "program", "predicted_forward_units", T(A("candidate", "predicted_forward_units"))],
            ["set_attr", "program", "predicted_vertical_units", 0],
            ["set_attr", "program", "predicted_energy_units", T(A("candidate", "predicted_energy_units"))],
            ["set_attr", "program", "predicted_peak_load_units", T(A("candidate", "predicted_peak_load_units"))],
            ["set_attr", "program", "experience_units", 0],
            # These remain separate from local practice.  A structurally
            # transferred model is not local rehearsal, and a cold proposal
            # remains structurally novel even at equal local experience.
            ["set_attr", "candidate", "structural_novelty_units", 1],
            ["set_attr", "candidate", "receipt_grounded_structural_reuse_units", 0],
        ],
    }


def crystallize_receipt_grounded_motor_shape_memory_rule():
    """Retain a successful local program as a ShapeDecode-addressable prior.

    The memory stores a body *relation system*, not a simulator handle.  This
    is important: a later attachment must build a new local opaque program
    with its own tokens, then may inherit only predictions and aperture from a
    structurally decoded, causally successful predecessor.
    """
    return {
        "name": "emb_crystallize_positive_receipt_as_motor_shape_memory",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A positive causal receipt crystallizes one output-null motor memory keyed by the observed body relation shape and local opaque topology. It contains no actuator handle and cannot itself confer competence on a later episode.",
        "match": [
            ["agent", "has_embodied_development_episode", "source_episode"],
            ["source_episode", "has_embodied_body_schema", "source_body"],
            ["source_body", "grounded_in_embodied_raw_body", "source_raw_body"],
            ["source_episode", "has_embodied_motor_episode", "source_motor_episode"],
            ["source_motor_episode", "has_embodied_motor_bootstrap_candidate", "source_candidate"],
            ["source_candidate", "proposes_embodied_motor_program", "source_program"],
            ["source_program", "has_grounded_learned_consequence", "consequence"],
            ["consequence", "grounded_in_causal_receipt", "receipt"],
            ["receipt", "caused_by_embodied_trial_request", "source_request"],
            ["source_proposal", "has_embodied_mission_trial_request", "source_request"],
            ["source_proposal", "proposes_goal", "source_goal"],
        ],
        "where": And(
            Eq(A("receipt", "grounded"), L(1)),
            Gt(A("receipt", "success_delta_units"), L(0)),
            absent(N("source_program", "has_embodied_motor_shape_memory")),
        ),
        "effects": [
            ["add_node", "memory", "EmbodiedMotorShapeMemory", {
                # ShapeDecode's codebook identity is a relation shape plus
                # the opaque topology position; it intentionally omits the
                # attachment-local token string.
                "name": T(StringConcat(
                    L("embodied-motor-receipt:"),
                    ToJsonString(A("source_raw_body", "body_shape_relations")),
                    L(":ordinal:"), ToJsonString(A("source_candidate", "actuator_ordinal")),
                    L(":members:"), ToJsonString(A("source_candidate", "member_count")),
                )),
                "signature": T(A("source_raw_body", "body_shape_relations")),
                "kind": "receipt_grounded_local_motor_program",
                "actuator_ordinal": T(A("source_candidate", "actuator_ordinal")),
                "member_count": T(A("source_candidate", "member_count")),
                "activation_effort_units": T(A("source_candidate", "activation_effort_units")),
                "simulator_frames": T(A("source_program", "simulator_frames")),
                "predicted_forward_units": T(A("source_program", "predicted_forward_units")),
                "predicted_vertical_units": T(A("source_program", "predicted_vertical_units")),
                "predicted_energy_units": T(A("source_program", "predicted_energy_units")),
                "predicted_peak_load_units": T(A("source_program", "predicted_peak_load_units")),
                "experience_units": T(A("source_program", "experience_units")),
                "mission_predicate": T(A("source_proposal", "predicate")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "agent", "has_embodied_motor_shape_memory", "memory"],
            ["add_edge", "source_program", "has_embodied_motor_shape_memory", "memory"],
            ["add_edge", "memory", "derived_from_embodied_motor_program", "source_program"],
            ["add_edge", "memory", "derived_from_pareto_candidate", "source_candidate"],
            ["add_edge", "memory", "grounded_in_causal_embodied_receipt", "receipt"],
            ["add_edge", "memory", "grounded_in_embodied_mission_proposal", "source_proposal"],
            ["add_edge", "memory", "grounded_in_embodied_mission_goal", "source_goal"],
            ["add_edge", "memory", "describes_embodied_body_schema", "source_body"],
        ],
    }


def warm_start_compatible_local_motor_program_rule():
    """Transfer a decoded prior onto the target episode's *local* program."""
    return {
        "name": "emb_warm_start_local_program_from_shape_decoded_receipt_memory",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A new body episode may warm-start only a freshly minted local opaque program. ShapeDecode must explain more target body relations than it leaves residual, and the source receipt/program/candidate remain explicit provenance. Local competence still requires a new grounded receipt.",
        "match": [
            ["agent", "has_embodied_development_episode", "target_episode"],
            ["target_episode", "has_embodied_body_schema", "target_body"],
            ["target_body", "grounded_in_embodied_raw_body", "target_raw_body"],
            ["target_episode", "has_embodied_motor_episode", "target_motor_episode"],
            ["target_motor_episode", "has_embodied_motor_bootstrap_candidate", "target_candidate"],
            ["target_candidate", "has_embodied_motor_bootstrap_initialization", "initialization"],
            ["target_candidate", "proposes_embodied_motor_program", "target_program"],
            ["agent", "has_embodied_motor_shape_memory", "memory"],
            ["memory", "derived_from_embodied_motor_program", "source_program"],
            ["memory", "derived_from_pareto_candidate", "source_candidate"],
            ["memory", "grounded_in_causal_embodied_receipt", "source_receipt"],
        ],
        "where": And(
            Eq(A("source_receipt", "grounded"), L(1)),
            Gt(A("source_receipt", "success_delta_units"), L(0)),
            Eq(A("target_candidate", "actuator_ordinal"), A("memory", "actuator_ordinal")),
            Eq(A("target_candidate", "member_count"), A("memory", "member_count")),
            Eq(A("target_candidate", "activation_effort_units"), A("memory", "activation_effort_units")),
            Gt({
                "type": "ShapeDecode",
                "goal": A("target_raw_body", "body_shape_relations"),
                "codebook_type": "EmbodiedMotorShapeMemory",
                "codebook_scope": SetT(A("memory", "name")),
                "beam": 1, "max_steps": 1, "cand_k": 1,
                "field": "covered_count", "wild_objects": False,
            }, Count({
                "type": "ShapeDecode",
                "goal": A("target_raw_body", "body_shape_relations"),
                "codebook_type": "EmbodiedMotorShapeMemory",
                "codebook_scope": SetT(A("memory", "name")),
                "beam": 1, "max_steps": 1, "cand_k": 1,
                "field": "residual", "wild_objects": False,
            })),
            absent(N("target_candidate", "has_embodied_motor_warm_start")),
        ),
        "effects": [
            ["add_node", "warm_start", "EmbodiedMotorWarmStart", {
                "status": "pending_local_verification",
                "shape_decode_required": 1,
                "local_verification_required": 1,
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "target_candidate", "has_embodied_motor_warm_start", "warm_start"],
            ["add_edge", "target_program", "has_embodied_motor_warm_start", "warm_start"],
            ["add_edge", "warm_start", "transfers_from_embodied_motor_shape_memory", "memory"],
            ["add_edge", "warm_start", "transfers_from_embodied_motor_program", "source_program"],
            ["add_edge", "warm_start", "transfers_from_pareto_candidate", "source_candidate"],
            ["add_edge", "warm_start", "grounded_in_source_embodied_receipt", "source_receipt"],
            ["add_edge", "warm_start", "shape_matches_embodied_body_schema", "target_body"],
            # The token sequence stays local: only measured/predicted state
            # and observation aperture cross the structural mapping.
            ["set_attr", "target_candidate", "structural_novelty_units", 0],
            ["set_attr", "target_candidate", "receipt_grounded_structural_reuse_units", 1],
            # THE APERTURE IS NOT TRANSFERRED. It used to be, and that was the
            # same category error the whole aperture change repairs: a shape
            # memory's frame count is an aperture measured on a DIFFERENT body,
            # and how long you must watch is a fact about THIS body's dynamics
            # against THIS body's resolution. The target reads its own body's
            # climbed exponent through
            # `emb_apply_body_temporal_aperture_to_program` instead.
            # Named cost: a transfer that WOULD be legitimate is the program's
            # relative HINT (this program needs one doubling more than its body
            # baseline). That is not recoverable from what the memory stores —
            # it holds absolute frames, not the source body's exponent — so it
            # is dropped rather than guessed. Predictions still transfer below.
            ["set_attr", "target_program", "predicted_forward_units", T(A("memory", "predicted_forward_units"))],
            ["set_attr", "target_program", "predicted_vertical_units", T(A("memory", "predicted_vertical_units"))],
            ["set_attr", "target_program", "predicted_energy_units", T(A("memory", "predicted_energy_units"))],
            ["set_attr", "target_program", "predicted_peak_load_units", T(A("memory", "predicted_peak_load_units"))],
            ["set_attr", "target_program", "transferred_evidence_units", T(A("memory", "experience_units"))],
            ["set_attr", "target_program", "warm_start_pending_local_verification", 1],
        ],
    }


def verify_warm_started_local_motor_program_rule():
    """Only a fresh target receipt can settle a transferred prior."""
    return {
        "name": "emb_verify_warm_started_local_program_with_new_causal_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Warm-start evidence is a prediction, never competence. A new target-episode causal receipt closes its explicit local verification and clears the pending marker without rewriting source evidence.",
        "match": [
            ["target_program", "has_embodied_motor_warm_start", "warm_start"],
            ["warm_start", "shape_matches_embodied_body_schema", "target_body"],
            ["target_body", "grounded_in_embodied_raw_body", "target_raw_body"],
            ["receipt", "caused_by_embodied_motor_program", "target_program"],
        ],
        "where": And(
            Eq(A("receipt", "grounded"), L(1)),
            Eq(A("target_program", "warm_start_pending_local_verification"), L(1)),
            absent(N("warm_start", "has_local_embodied_motor_verification")),
        ),
        "effects": [
            ["add_node", "verification", "EmbodiedMotorWarmStartVerification", {
                "status": "locally_receipted",
                "success_delta_units": T(A("receipt", "success_delta_units")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "warm_start", "has_local_embodied_motor_verification", "verification"],
            ["add_edge", "verification", "grounded_in_local_embodied_receipt", "receipt"],
            ["add_edge", "verification", "measures_local_embodied_body", "target_body"],
            ["set_attr", "target_program", "warm_start_pending_local_verification", 0],
            ["set_attr", "warm_start", "status", "locally_receipted"],
        ],
    }


def activate_repeat_mission_retention_context_rule():
    """Let an explicitly repeated mission choose reuse over novelty locally."""
    return {
        "name": "emb_activate_shape_matched_repeat_mission_retention_context",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Only a newly accepted mission with the same predicate as the positive source mission may turn a ShapeDecode warm hint into a local retention-verification context. This is a goal-side Pareto preference, not a host toggle or generic warm-first rule.",
        "match": [
            ["target_program", "has_embodied_motor_warm_start", "warm_start"],
            ["warm_start", "transfers_from_embodied_motor_shape_memory", "memory"],
            ["warm_start", "shape_matches_embodied_body_schema", "target_body"],
            ["target_episode", "has_embodied_body_schema", "target_body"],
            ["target_episode", "has_embodied_motor_episode", "target_motor_episode"],
            ["target_motor_episode", "has_embodied_motor_bootstrap_candidate", "target_candidate"],
            ["target_candidate", "proposes_embodied_motor_program", "target_program"],
            ["target_proposal", "requires_embodied_capability", "target_capability"],
            ["target_proposal", "proposes_goal", "target_goal"],
            ["target_goal", "supervises_embodied_episode", "target_episode"],
        ],
        "where": And(
            Eq(A("target_proposal", "status"), L("accepted")),
            Eq(A("target_proposal", "predicate"), A("memory", "mission_predicate")),
            absent(N("target_capability", "has_embodied_motor_retention_context")),
        ),
        "effects": [
            ["add_node", "context", "EmbodiedMotorRetentionContext", {
                "kind": "repeat_mission_local_verification",
                "status": "active",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "target_capability", "has_embodied_motor_retention_context", "context"],
            ["add_edge", "context", "pursues_embodied_instruction_goal", "target_goal"],
            ["add_edge", "context", "grounds_in_shape_matched_motor_memory", "memory"],
            ["add_edge", "context", "uses_embodied_motor_warm_start", "warm_start"],
            ["set_attr", "target_capability", "warm_start_requires_verification", 1],
        ],
    }


def publish_initialized_candidate_pareto_values_rule():
    """Publish a fixed integer Pareto point after candidate initialization."""
    return {
        "name": "emb_publish_initialized_motor_candidate_integer_pareto_coordinates",
        "area": "cognitive_pareto",
        "latency_class": "hard_realtime",
        "comment": "Values are graph objects attached once after mutable state exists. A later novelty update mutates this same coordinate instead of minting another ParetoValue.",
        "match": [
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "candidate"],
            ["candidate", "has_embodied_motor_bootstrap_initialization", "initialization"],
        ],
        "where": absent(N("candidate", "has_pareto_value")),
        "effects": [
            ["add_node", "value_novelty", "ParetoValue", {
                "dimension_ordinal": 0,
                "raw_value": T(A("candidate", "experience_units")),
                "signed_value": T(Neg(A("candidate", "experience_units"))),
                "verified": 1, "integer_native": 1,
            }],
            ["add_node", "value_coverage", "ParetoValue", {
                "dimension_ordinal": 1,
                "raw_value": T(A("candidate", "member_count")),
                "signed_value": T(A("candidate", "member_count")),
                "verified": 1, "integer_native": 1,
            }],
            ["add_node", "value_effort", "ParetoValue", {
                "dimension_ordinal": 2,
                "raw_value": T(A("candidate", "activation_effort_units")),
                "signed_value": T(Neg(A("candidate", "activation_effort_units"))),
                "verified": 1, "integer_native": 1,
            }],
            ["add_node", "value_structural_novelty", "ParetoValue", {
                "dimension_ordinal": 3,
                "raw_value": T(A("candidate", "structural_novelty_units")),
                "signed_value": T(A("candidate", "structural_novelty_units")),
                "verified": 1, "integer_native": 1,
            }],
            ["add_node", "value_reuse", "ParetoValue", {
                "dimension_ordinal": 4,
                "raw_value": T(A("candidate", "receipt_grounded_structural_reuse_units")),
                "signed_value": T(A("candidate", "receipt_grounded_structural_reuse_units")),
                "verified": 1, "integer_native": 1,
            }],
            ["add_node", "value_coordination", "ParetoValue", {
                "dimension_ordinal": 5,
                "raw_value": T(A("candidate", "unverified_coordination_information_units")),
                "signed_value": T(A("candidate", "unverified_coordination_information_units")),
                "verified": 1, "integer_native": 1,
            }],
            ["add_edge", "candidate", "has_pareto_value", "value_novelty"],
            ["add_edge", "candidate", "has_pareto_value", "value_coverage"],
            ["add_edge", "candidate", "has_pareto_value", "value_effort"],
            ["add_edge", "candidate", "has_pareto_value", "value_structural_novelty"],
            ["add_edge", "candidate", "has_pareto_value", "value_reuse"],
            ["add_edge", "candidate", "has_pareto_value", "value_coordination"],
            ["add_node", "ready", "EmbodiedMotorBootstrapParetoReady", {
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "candidate", "has_embodied_motor_bootstrap_pareto_ready", "ready"],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_ready_candidate", "candidate"],
            # Requesting a selection epoch is a distinct causal event from
            # opening it.  The epoch-opening rule is deliberately evaluated
            # before this publisher, so a fully initialized frontier crosses
            # a graph-resident asynchronous boundary rather than relying on
            # a host retry after a same-pass candidate construction burst.
            ["add_node_if_absent", "initial_epoch_request", "EmbodiedMotorSelectionEpochRequest", {
                "kind": "opaque_motor_bootstrap",
                "origin": "initialized_frontier",
                "settled_experience_units": T(Sum(
                    N("motor_episode", "has_embodied_motor_bootstrap_candidate"),
                    "epoch_candidate", A("epoch_candidate", "experience_units"),
                )),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_pending_embodied_motor_selection_epoch_request", "initial_epoch_request"],
        ],
    }


def open_selection_epoch_rule():
    """Open the initial, frontier-publication selection epoch.

    Receipt-triggered epochs use the separate rule below so the receipt is an
    explicit graph edge, rather than an opaque node-reference attribute.
    """
    return {
        "name": "emb_open_pending_motor_selection_epoch",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # Opening is a collapse boundary: a retained/duplicated pending
        # frontier must never fan out into several live epochs in one
        # semi-naive pass.  The selected epoch itself remains graph data.
        "batch": False,
        "comment": "The initialized frontier opens on a later graph pass. Receipt-triggered requests are opened by the receipt-specific epoch rule, preserving their exact causal provenance as a graph edge.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_pending_embodied_motor_selection_epoch_request", "epoch_request"],
        ],
        "where": And(
            absent(N("motor_episode", "has_current_embodied_motor_selection_epoch")),
            absent(N("epoch_request", "grounded_in_embodied_learning_receipt")),
        ),
        "effects": [
            ["add_node", "epoch", "EmbodiedMotorSelectionEpoch", {
                "kind": "opaque_motor_bootstrap",
                "origin": T(A("epoch_request", "origin")),
                "request_ref": T(V("epoch_request")),
                "settled_experience_units": T(A("epoch_request", "settled_experience_units")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["del_edge", "motor_episode", "has_pending_embodied_motor_selection_epoch_request", "epoch_request"],
        ],
    }


def open_grounded_selection_epoch_rule():
    """Open a successor epoch while preserving its exact triggering receipt."""
    return {
        "name": "emb_open_receipt_grounded_motor_selection_epoch",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # As above, settle exactly one causal epoch before evaluating the
        # frontier again.  Without this boundary, every pending historical
        # receipt can appear simultaneously eligible and cause unbounded
        # selection-node growth without a new physical observation.
        "batch": False,
        "comment": "A settled physical receipt opens its own immutable successor epoch. The epoch keeps a first-class receipt edge, so later supervisory repair can only act from the receipt that caused this current epoch, never from retained session history.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_pending_embodied_motor_selection_epoch_request", "epoch_request"],
            ["epoch_request", "grounded_in_embodied_learning_receipt", "receipt"],
        ],
        "where": absent(N("motor_episode", "has_current_embodied_motor_selection_epoch")),
        "effects": [
            ["add_node", "epoch", "EmbodiedMotorSelectionEpoch", {
                "kind": "opaque_motor_bootstrap",
                "origin": T(A("epoch_request", "origin")),
                "request_ref": T(V("epoch_request")),
                "settled_experience_units": T(A("epoch_request", "settled_experience_units")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "epoch", "grounded_in_embodied_learning_receipt", "receipt"],
            ["del_edge", "motor_episode", "has_pending_embodied_motor_selection_epoch_request", "epoch_request"],
        ],
    }


def singleton_candidate_rule():
    members = SetT(V("effector"))
    existing = Filter(
        N("effector", "has_singleton_candidate_in_motor_episode"),
        "known_motor_episode",
        Eq(V("known_motor_episode"), V("motor_episode")),
    )
    return {
        "name": "emb_mint_singleton_prior_and_program_from_opaque_actuator",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Every observed opaque effector becomes one no-authority exploratory candidate. Its exact token crosses unchanged into the program list.",
        "match": [
            ["episode", "has_embodied_body_schema", "body"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_embodied_motor_bootstrap_profile", "profile"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["body", "has_opaque_embodied_actuator_affordance", "effector"],
        ],
        "where": And(
            contract_is_usable(),
            Eq(A("effector", "integer_native"), L(1)),
            Gt(A("effector", "ordinal"), L(-1)),
            # add_node_if_absent is the final transactional identity guard,
            # not a reason to replay a complete candidate's effects forever.
            Eq(Count(existing), L(0)),
        ),
        "effects": _candidate_effects("effector", members) + [[
            "add_edge", "effector", "has_singleton_candidate_in_motor_episode",
            "motor_episode",
        ]],
    }


def backfill_singleton_candidate_identity_rule():
    """Recover the direct singleton identity edge from retained candidates."""
    known = Filter(
        N("effector", "has_singleton_candidate_in_motor_episode"),
        "known_motor_episode",
        Eq(V("known_motor_episode"), V("motor_episode")),
    )
    return {
        "name": "emb_backfill_singleton_candidate_motor_episode_identity",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "candidate"],
            ["candidate", "models_opaque_affordance", "effector"],
        ],
        "where": And(
            Eq(A("candidate", "member_count"), L(1)),
            Eq(Count(known), L(0)),
        ),
        "effects": [[
            "add_edge", "effector", "has_singleton_candidate_in_motor_episode",
            "motor_episode",
        ]],
    }


def suspend_detached_motor_pareto_profile_rule():
    return {
        "name": "emb_suspend_detached_motor_pareto_profile",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "grounded_in_embodied_simulator_connection", "connection"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_embodied_motor_bootstrap_profile", "profile"],
        ],
        "where": And(
            Eq(A("connection", "current_attachment"), L(0)),
            Not(Eq(A("profile", "pareto_suspended"), L(1))),
        ),
        "effects": [["set_attr", "profile", "pareto_suspended", 1]],
    }


def bundle_members():
    return N("bundle", "has_opaque_embodied_actuator_affordance")


def bundle_is_usable():
    members = bundle_members()
    valid_members = Filter(members, "member", And(
        Eq(A("member", "integer_native"), L(1)),
        # A tonic/default hold is a mechanically distinct command in the
        # simulator: it may be sampled alone but cannot join a twitch bundle.
        Eq(A("member", "tonic_default"), L(0)),
    ))
    return And(
        contract_is_usable(),
        Eq(A("bundle", "integer_native"), L(1)),
        Gt(A("bundle", "ordinal"), L(-1)),
        Gt(Count(members), L(1)),
        Not(Gt(Count(members), A("contract", "maximum_actuator_bundle_members"))),
        Eq(Count(valid_members), Count(members)),
    )


def bundle_candidate_rule():
    members = bundle_members()
    return {
        "name": "emb_mint_compound_prior_and_program_from_observed_topology_bundle",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A body may mechanically publish any compatible set as a topology bundle. Composition preserves every member token and never introduces a semantic alias for the bundle.",
        "match": [
            ["episode", "has_embodied_body_schema", "body"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_embodied_motor_bootstrap_profile", "profile"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["body", "has_opaque_actuator_bundle_affordance", "bundle"],
        ],
        "where": bundle_is_usable(),
        "effects": _candidate_effects("bundle", members),
    }


def receipt_grounded_pair_ordinal():
    """A body-relative, collision-free coordinate for an exact pair.

    The observed actuator count is the radix.  This is a topology identity,
    not a policy rank or an anatomy label, and lets ShapeDecode retain the
    pair's structural position across a matching body without importing a
    source token.
    """
    width = A("body", "actuator_count")
    return Plus(
        Times(A("relation", "relation_ordinal"), width, width),
        Times(A("source_effector", "ordinal"), width),
        A("target_effector", "ordinal"),
    )


def bind_topology_relation_effector_rule(*, endpoint: str) -> dict:
    """Resolve one ordinal endpoint into a persistent graph identity edge."""
    if endpoint not in {"source", "target"}:
        raise ValueError(endpoint)
    ordinal_key = f"{endpoint}_group_ordinal"
    edge = f"has_{endpoint}_opaque_embodied_effector"
    return {
        "name": f"emb_bind_direct_topology_{endpoint}_effector_identity",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Resolve an observed mechanical relation endpoint once. "
        "Later motor synthesis joins by this graph edge instead of repeatedly "
        "testing a relation-by-effector Cartesian product.",
        "match": [
            ["body", "has_opaque_embodied_effector_topology_relation", "relation"],
            ["body", "has_opaque_embodied_actuator_affordance", "effector"],
        ],
        "where": And(
            Eq(A("relation", "relation_kind"), L("directed_mechanical_link_adjacency")),
            Eq(A("relation", "mechanical_path_length"), L(1)),
            Eq(A("relation", "grounded"), L(1)),
            Eq(A("effector", "opaque_group_ordinal"), A("relation", ordinal_key)),
            absent(N("relation", edge)),
        ),
        "effects": [["add_edge", "relation", edge, "effector"]],
    }


def materialize_receipt_grounded_local_compound_bundle_rule():
    """Open one local pair proposal from an observed successful singleton.

    This is deliberately narrower than a powerset construction.  A pair can
    appear only by extending an exact receipt-grounded singleton along one
    direct mechanical body-tree relation.  The graph still determines which
    resulting non-dominated proposal is selected, and physical evidence must
    still settle the compound's predicted consequence.
    """
    return {
        "name": "emb_synthesize_local_compound_from_grounded_consequence_and_topology",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # Every admissible relation is evaluated against the same immutable
        # receipt/body snapshot.  Batch materialization therefore preserves
        # branching morphology while allowing one durable completion fact.
        "batch": True,
        "comment": "A positive local singleton consequence may extend through one observed direct effector adjacency. The graph creates an exact two-member opaque bundle with receipt, consequence, source-program and topology provenance; it never enumerates arbitrary actuator sets or issues authority.",
        "match": [
            ["episode", "has_embodied_body_schema", "body"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["body", "has_opaque_embodied_effector_topology_relation", "relation"],
            ["relation", "has_source_opaque_embodied_effector", "source_effector"],
            ["relation", "has_target_opaque_embodied_effector", "target_effector"],
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "source_candidate"],
            ["source_candidate", "models_opaque_affordance", "source_effector"],
            ["source_candidate", "proposes_embodied_motor_program", "source_program"],
            ["source_program", "has_grounded_learned_consequence", "consequence"],
            ["consequence", "grounded_in_causal_receipt", "receipt"],
        ],
        "where": And(
            Not(Eq(A("source_program", "compound_topology_expansion_complete"), L(1))),
            Eq(A("source_candidate", "member_count"), L(1)),
            Eq(A("source_effector", "integer_native"), L(1)),
            Eq(A("target_effector", "integer_native"), L(1)),
            Eq(A("source_effector", "tonic_default"), L(0)),
            Eq(A("target_effector", "tonic_default"), L(0)),
            Eq(A("relation", "relation_kind"), L("directed_mechanical_link_adjacency")),
            Eq(A("relation", "mechanical_path_length"), L(1)),
            Eq(A("relation", "grounded"), L(1)),
            Eq(A("relation", "integer_native"), L(1)),
            Eq(A("source_effector", "opaque_group_ordinal"), A("relation", "source_group_ordinal")),
            Eq(A("target_effector", "opaque_group_ordinal"), A("relation", "target_group_ordinal")),
            Eq(A("receipt", "grounded"), L(1)),
            Eq(A("receipt", "causal_closed"), L(1)),
            Gt(A("receipt", "success_delta_units"), L(0)),
            Gt(A("receipt", "goal_progress_units"), L(0)),
            Not(Eq(V("source_effector"), V("target_effector"))),
            Not(Exists(
                N("source_program", "has_opened_compound_topology_relation"),
                "known_relation", Eq(V("known_relation"), V("relation")),
            )),
        ),
        "effects": [
            ["add_node", "bundle", "OpaqueActuatorBundleAffordance", {
                "kind": "receipt_grounded_direct_topology_pair",
                "ordinal": T(receipt_grounded_pair_ordinal()),
                "member_count": 2,
                # The source receipt makes the *question* valuable, not its
                # answer known.  Interaction forward/energy/load predictions
                # remain zero and explicitly unverified until this exact
                # compound itself receives a physical receipt.
                "predicted_forward_units": 0,
                "predicted_energy_units": 0,
                "predicted_peak_load_units": 0,
                "unverified_coordination_information_units": 1,
                "interaction_prediction_verified": 0,
                "grounded": 1,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "body", "has_opaque_actuator_bundle_affordance", "bundle"],
            ["add_edge", "bundle", "has_opaque_embodied_actuator_affordance", "source_effector"],
            ["add_edge", "bundle", "has_opaque_embodied_actuator_affordance", "target_effector"],
            ["add_edge", "bundle", "grounded_in_embodied_effector_topology_relation", "relation"],
            ["add_edge", "bundle", "grounded_in_source_embodied_motor_program", "source_program"],
            ["add_edge", "bundle", "grounded_in_source_embodied_consequence", "consequence"],
            ["add_edge", "bundle", "grounded_in_source_embodied_receipt", "receipt"],
            ["add_edge", "source_program", "opens_receipt_grounded_compound_bundle", "bundle"],
            ["add_edge", "source_program", "has_opened_compound_topology_relation", "relation"],
            ["set_attr", "source_program", "compound_topology_expansion_complete", 1],
        ],
    }


def backfill_opened_compound_relation_identity_rule():
    known = Filter(
        N("source_program", "has_opened_compound_topology_relation"),
        "known_relation", Eq(V("known_relation"), V("relation")),
    )
    return {
        "name": "emb_backfill_opened_compound_relation_identity",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["bundle", "grounded_in_source_embodied_motor_program", "source_program"],
            ["bundle", "grounded_in_embodied_effector_topology_relation", "relation"],
        ],
        "where": Eq(Count(known), L(0)),
        "effects": [
            [
                "add_edge", "source_program",
                "has_opened_compound_topology_relation", "relation",
            ],
            # A historical bundle is evidence that the former exhaustive
            # rule already opened this immutable program/body topology.
            [
                "set_attr", "source_program",
                "compound_topology_expansion_complete", 1,
            ],
        ],
    }


def open_receipt_grounded_coordination_context_rule():
    """Let the current goal, rather than a host policy, value interaction data."""
    return {
        "name": "emb_open_goal_scoped_coordination_hypothesis_from_singleton_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # One active capability gets one bounded interaction check-in.  A
        # receipt can expose several adjacent bundles in the same graph pass;
        # they remain candidates, but cannot each open a competing context.
        "batch": False,
        "comment": "A still-active goal may spend one bounded local verification on an unknown directly adjacent interaction after a positive singleton receipt. The context records why coordination novelty outranks known singleton efficiency for this goal only.",
        "match": [
            ["episode", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "pursues_goal", "goal"],
            ["bundle", "grounded_in_source_embodied_receipt", "source_receipt"],
            ["source_receipt", "caused_for_embodied_goal", "goal"],
        ],
        "where": And(
            Eq(A("goal", "status"), L("active")),
            Eq(A("capability", "status"), L("active")),
            Eq(A("bundle", "interaction_prediction_verified"), L(0)),
            Eq(P0("capability", "coordination_exploration_required"), L(0)),
            # Several command polarities can share one mechanical neighbour.
            # Collapse the receipt's local hypotheses by their collision-free
            # observed topology ordinal before opening a single context.
            Not(Exists(
                IN("source_receipt", "grounded_in_source_embodied_receipt"),
                "earlier_bundle", And(
                    Eq(A("earlier_bundle", "interaction_prediction_verified"), L(0)),
                    Lt(A("earlier_bundle", "ordinal"), A("bundle", "ordinal")),
                ),
            )),
            absent(N("capability", "has_embodied_motor_coordination_context")),
        ),
        "effects": [
            ["add_node", "context", "EmbodiedMotorCoordinationContext", {
                "kind": "goal_scoped_unverified_local_interaction",
                "status": "open",
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "capability", "has_embodied_motor_coordination_context", "context"],
            ["add_edge", "context", "targets_embodied_goal", "goal"],
            ["add_edge", "context", "grounds_in_source_embodied_receipt", "source_receipt"],
            ["add_edge", "context", "opens_embodied_compound_hypothesis", "bundle"],
            ["set_attr", "capability", "coordination_exploration_required", 1],
        ],
    }


def link_exact_receipt_evidence_to_motor_candidate_rule():
    """Reuse the session's measured 3D Pareto profile, with exact provenance."""
    return {
        "name": "emb_link_existing_verified_progress_energy_load_to_motor_candidate",
        "area": "cognitive_pareto",
        "latency_class": "hard_realtime",
        "comment": "EmbodiedLearningSession already owns the one shared verified progress/energy/load profile. This rule only links its exact evidence candidate back to the selected bootstrap candidate; it never manufactures a second performance profile or treats hypothesis zeros as data.",
        "match": [
            ["selection", "selects_pareto_candidate", "candidate"],
            ["selection", "selects_embodied_motor_program", "program"],
            ["selection", "settled_by_grounded_evidence", "evidence"],
            ["evidence", "published_as_pareto_candidate", "outcome"],
        ],
        "where": And(
            Eq(A("evidence", "grounded"), L(1)),
            Eq(A("outcome", "verified"), L(1)),
            absent(N("candidate", "has_receipt_grounded_motor_outcome")),
        ),
        "effects": [
            ["add_edge", "candidate", "has_receipt_grounded_motor_outcome", "outcome"],
            ["add_edge", "outcome", "measures_embodied_motor_program", "program"],
            ["add_edge", "outcome", "represents_embodied_motor_bootstrap_candidate", "candidate"],
            ["set_attr", "candidate", "predicted_forward_units", T(A("evidence", "goal_progress_units"))],
            ["set_attr", "candidate", "predicted_energy_units", T(A("evidence", "energy_cost_units"))],
            ["set_attr", "candidate", "predicted_peak_load_units", T(A("evidence", "peak_load_units"))],
            ["set_attr", "candidate", "interaction_prediction_verified", T(If(
                Gt(A("candidate", "member_count"), L(1)), L(1), L(0),
            ))],
        ],
    }


def close_goal_scoped_coordination_context_rule():
    return {
        "name": "emb_close_goal_scoped_coordination_hypothesis_on_local_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "One locally receipted compound settles the goal-scoped coordination question and releases the context; later coordination requires a new causal premise rather than an unchecked loop.",
        "match": [
            ["capability", "has_embodied_motor_coordination_context", "context"],
            ["context", "opens_embodied_compound_hypothesis", "bundle"],
            ["candidate", "models_opaque_affordance", "bundle"],
            ["candidate", "proposes_embodied_motor_program", "program"],
            ["receipt", "caused_by_embodied_motor_program", "program"],
        ],
        "where": And(
            Eq(A("context", "status"), L("open")),
            Eq(A("receipt", "grounded"), L(1)),
            Eq(A("receipt", "causal_closed"), L(1)),
            Gt(A("candidate", "member_count"), L(1)),
        ),
        "effects": [
            ["set_attr", "context", "status", "locally_receipted"],
            ["set_attr", "capability", "coordination_exploration_required", 0],
        ],
    }


def frontier_candidates():
    return Filter(N("profile", "has_pareto_candidate"), "frontier", And(
        Eq(A("frontier", "status"), L("candidate")),
        Eq(A("frontier", "integer_native"), L(1)),
        Eq(Count(N("frontier", "is_dominated_by_pareto_candidate")), L(0)),
        Eq(Count(N("frontier", "has_pareto_value")), A("profile", "dimension_count")),
    ))


def is_frontier_candidate(var):
    return And(
        Eq(A(var, "status"), L("candidate")),
        Eq(A(var, "integer_native"), L(1)),
        Eq(Count(N(var, "is_dominated_by_pareto_candidate")), L(0)),
        Eq(Count(N(var, "has_pareto_value")), A("profile", "dimension_count")),
    )


def pareto_coordinate(candidate, dimension_ordinal):
    """Read one declared profile coordinate without scalarising the frontier."""
    return Sum(
        Filter(
            N(candidate, "has_pareto_value"), "coordinate",
            Eq(A("coordinate", "dimension_ordinal"), L(dimension_ordinal)),
        ),
        "coordinate", A("coordinate", "signed_value"),
    )


def lower_opaque_frontier_candidate(candidate="candidate"):
    """Goal-contextual collapse of an otherwise non-scalarized frontier."""
    return Exists(N("profile", "has_pareto_candidate"), "other", And(
        is_frontier_candidate("other"),
        Or(
            # Coordination is an explicit information-seeking tradeoff, not
            # a universal warm-first rule.  A receipt-grounded goal context
            # must open before unknown local interaction can outrank a known
            # singleton's efficiency on this axis.
            And(
                Eq(P0("capability", "coordination_exploration_required"), L(1)),
                Gt(pareto_coordinate("other", 5), pareto_coordinate(candidate, 5)),
            ),
            # Reinstantiation/retention asks for a local verification of an
            # already explained structure.  It therefore resolves the
            # structural-novelty/reuse tradeoff toward the receipt-grounded
            # reuse coordinate, but only under this graph-owned capability
            # context—not as a universal warm-first policy.
            And(
                Eq(A("capability", "warm_start_requires_verification"), L(1)),
                Gt(pareto_coordinate("other", 4), pareto_coordinate(candidate, 4)),
            ),
            # Ordinary discovery retains the opposite preference: a cold
            # unexplained topology is valuable precisely because it expands
            # structural coverage.  Both axes remain Pareto values, never a
            # hidden reward scalar.
            And(
                Eq(A("capability", "warm_start_requires_verification"), L(0)),
                Gt(pareto_coordinate("other", 3), pareto_coordinate(candidate, 3)),
            ),
            And(
                # The ordinal is only an ordinary-discovery tie break.  A
                # live coordination hypothesis has already declared that its
                # verified information coordinate outweighs this opaque
                # structural tie, so it must not be silently undone here.
                Eq(P0("capability", "coordination_exploration_required"), L(0)),
                Eq(pareto_coordinate("other", 4), pareto_coordinate(candidate, 4)),
                Eq(pareto_coordinate("other", 3), pareto_coordinate(candidate, 3)),
                Or(
                    Lt(A("other", "experience_units"), A(candidate, "experience_units")),
                    And(
                        Eq(A("other", "experience_units"), A(candidate, "experience_units")),
                        Lt(A("other", "actuator_ordinal"), A(candidate, "actuator_ordinal")),
                    ),
                ),
            ),
        ),
    ))


def request_selection_after_frontier_ready_rule():
    """Collapse a complete, graph-visible Pareto frontier to one program."""
    return {
        "name": "emb_select_ready_motor_program_from_pareto_frontier",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # The final collapse must see the selection it just emitted before a
        # second ready-candidate match is considered.  This is not a policy
        # preference: it enforces the one-program output invariant and keeps
        # a held residual from minting a duplicate selection every tick.
        "batch": False,
        "comment": "Candidate construction is parallel; this graph rule collapses a complete non-dominated frontier to its lexicographically first opaque candidate. The ready-candidate edge is the event that makes selection admissible—no host tick or magic cadence is involved.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_embodied_motor_bootstrap_profile", "profile"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["motor_episode", "has_embodied_motor_bootstrap_ready_candidate", "candidate"],
            ["profile", "has_pareto_candidate", "candidate"],
            ["candidate", "has_embodied_motor_bootstrap_pareto_ready", "ready"],
            ["candidate", "uses_embodied_motor_prior", "prior"],
            ["candidate", "proposes_embodied_motor_program", "program"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "pursues_goal", "goal"],
            ["episode", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": And(
            Eq(A("goal", "status"), L("active")),
            # A resumed graph can retain more than one unfinished epoch from
            # an interrupted receipt transition.  The most recently settled
            # graph epoch is the only admissible collapse boundary; this is
            # epoch provenance, not a motor score.
            Not(Exists(
                N("motor_episode", "has_current_embodied_motor_selection_epoch"),
                "newer_epoch",
                Gt(P0("newer_epoch", "settled_experience_units"),
                   P0("epoch", "settled_experience_units")),
            )),
            is_frontier_candidate("candidate"),
            Not(lower_opaque_frontier_candidate()),
            absent(N("motor_episode", "has_embodied_motor_bootstrap_selection")),
            absent(N("motor_episode", "has_embodied_motor_program")),
        ),
        "effects": [
            ["add_node", "selection", "EmbodiedMotorBootstrapSelection", {
                # Exact episode/epoch/candidate provenance lets duplicate
                # cleanup inspect a resumed collapse without using host state.
                "motor_episode_ref": T(V("motor_episode")),
                "selection_epoch_ref": T(V("epoch")),
                "selected_candidate_ref": T(V("candidate")),
                "status": "selected", "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["add_edge", "selection", "selects_pareto_candidate", "candidate"],
            ["add_edge", "selection", "selects_embodied_motor_program", "program"],
            ["add_edge", "selection", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "selection", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "selection", "pursues_goal", "goal"],
            ["add_edge", "selection", "targets_developmental_capability", "capability"],
            ["add_edge", "motor_episode", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "motor_episode", "has_embodied_motor_program", "program"],
            ["set_attr", "motor_episode", "status", "selected_for_rehearsal"],
        ],
    }


def retire_superseded_current_selection_epochs_rule():
    """Keep only the epoch that became the graph's actual motor collapse."""
    return {
        "name": "emb_retire_unselected_duplicate_motor_selection_epoch",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An interrupted/resumed receipt transition can retain several current epoch edges. Once a selected program names one exact epoch, the other epoch edges are historical provenance only and must not remain live alternative collapses.",
        "match": [
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["selection", "is_in_embodied_motor_selection_epoch", "selected_epoch"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "other_epoch"],
        ],
        "where": And(
            Not(Eq(V("other_epoch"), V("selected_epoch"))),
            # First reduce duplicate historical selections.  Otherwise two
            # selections can each erase the other's epoch and leave neither
            # live, which is the opposite of a collapse.
            Not(Exists(
                N("motor_episode", "has_embodied_motor_bootstrap_selection"),
                "other_selection", Not(Eq(V("other_selection"), V("selection"))),
            )),
        ),
        "effects": [
            ["del_edge", "motor_episode", "has_current_embodied_motor_selection_epoch", "other_epoch"],
        ],
    }


def retire_superseded_motor_selections_rule():
    """Normalize retained selections before pruning their epoch aliases."""
    return {
        "name": "emb_retire_older_duplicate_motor_selection",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A resumed graph may retain selections from several receipt epochs. The highest settled epoch is the current graph decision; older selection edges remain inspectable nodes but lose live motor authority before epoch cleanup runs.",
        "match": [
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["selection", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "newer_selection"],
            ["newer_selection", "is_in_embodied_motor_selection_epoch", "newer_epoch"],
        ],
        "where": Gt(P0("newer_epoch", "settled_experience_units"),
                    P0("epoch", "settled_experience_units")),
        "effects": [
            ["del_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
        ],
    }


def reopen_exact_duplicate_motor_selection_rule():
    """Re-collapse duplicate retained selections without inventing a winner."""
    return {
        "name": "emb_reopen_exact_duplicate_motor_selection",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "If resume history retained two live selections with the same candidate and program, neither is privileged. Remove both live authority edges and let the ordinary Pareto collapse produce one fresh selection from the retained frontier.",
        "match": [
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["selection", "selects_pareto_candidate", "candidate"],
            ["selection", "selects_embodied_motor_program", "program"],
            ["selection", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["selection", "uses_embodied_motor_prior", "prior"],
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "duplicate"],
            ["duplicate", "selects_pareto_candidate", "candidate"],
            ["duplicate", "selects_embodied_motor_program", "program"],
            ["duplicate", "is_in_embodied_motor_selection_epoch", "epoch"],
        ],
        "where": Not(Eq(V("selection"), V("duplicate"))),
        "effects": [
            ["add_node_if_absent", "dedup", "EmbodiedMotorSelectionDeduplication", {
                "kind": "exact_duplicate_selection_recollapse",
                "motor_episode_ref": T(V("motor_episode")),
                "candidate_ref": T(V("candidate")),
                "program_ref": T(V("program")),
                "epoch_ref": T(V("epoch")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_selection_deduplication", "dedup"],
            ["add_edge", "dedup", "reopens_duplicate_motor_selection", "selection"],
            ["add_edge", "dedup", "reopens_duplicate_motor_selection", "duplicate"],
            ["add_node_if_absent", "replacement", "EmbodiedMotorBootstrapSelection", {
                "status": "selected",
                "kind": "exact_duplicate_selection_recollapse",
                "motor_episode_ref": T(V("motor_episode")),
                "selected_candidate_ref": T(V("candidate")),
                "selected_program_ref": T(V("program")),
                "selection_epoch_ref": T(V("epoch")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "replacement"],
            ["add_edge", "replacement", "selects_pareto_candidate", "candidate"],
            ["add_edge", "replacement", "selects_embodied_motor_program", "program"],
            ["add_edge", "replacement", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "replacement", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "motor_episode", "has_embodied_motor_program", "program"],
            ["add_edge", "motor_episode", "uses_embodied_motor_prior", "prior"],
            ["del_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["del_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "duplicate"],
            ["set_attr", "motor_episode", "status", "selected_for_rehearsal"],
        ],
    }


def reopen_unexecuted_selection_for_coordination_hypothesis_rule():
    """Let a newly grounded interaction question revise an unexecuted default."""
    return {
        "name": "emb_reopen_unexecuted_singleton_for_goal_scoped_coordination_hypothesis",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A receipt-grounded local interaction context can revise one still-unexecuted singleton collapse after its exact compound has a complete Pareto point. The rule never interrupts a requested physical trial and retains the normal selected-for-rehearsal motor state.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "pursues_goal", "goal"],
            ["capability", "has_embodied_motor_coordination_context", "context"],
            ["context", "opens_embodied_compound_hypothesis", "bundle"],
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["selection", "selects_pareto_candidate", "selected_candidate"],
            ["selection", "selects_embodied_motor_program", "selected_program"],
            ["selection", "uses_embodied_motor_prior", "selected_prior"],
            ["selection", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "compound_candidate"],
            ["compound_candidate", "models_opaque_affordance", "bundle"],
            ["compound_candidate", "has_embodied_motor_bootstrap_pareto_ready", "ready"],
            ["compound_candidate", "proposes_embodied_motor_program", "compound_program"],
            ["compound_candidate", "uses_embodied_motor_prior", "compound_prior"],
        ],
        "where": And(
            Eq(A("context", "status"), L("open")),
            Eq(A("selected_candidate", "member_count"), L(1)),
            Eq(A("compound_candidate", "member_count"), L(2)),
            # Authority has not crossed the mechanical boundary.  Incoming
            # enactment edges bind the exact selected program, avoiding a
            # broad session-history test that can suppress valid re-collapse.
            absent(IN("selected_program", "enacts_embodied_motor_program")),
            absent(N("context", "has_coordination_reselection")),
        ),
        "effects": [
            ["add_node", "reselection", "EmbodiedMotorCoordinationReselection", {
                "kind": "pre_dispatch_goal_scoped_coordination_tradeoff",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "context", "has_coordination_reselection", "reselection"],
            ["add_edge", "reselection", "supersedes_embodied_motor_selection", "selection"],
            ["add_edge", "reselection", "opens_embodied_compound_hypothesis", "bundle"],
            # The exact goal-scoped context bundle has a complete published
            # Pareto point; replace the unexecuted singleton atomically.
            ["add_node", "replacement", "EmbodiedMotorBootstrapSelection", {
                "status": "selected",
                "kind": "goal_scoped_coordination_recollapse",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "replacement"],
            ["add_edge", "replacement", "selects_pareto_candidate", "compound_candidate"],
            ["add_edge", "replacement", "selects_embodied_motor_program", "compound_program"],
            ["add_edge", "replacement", "uses_embodied_motor_prior", "compound_prior"],
            ["add_edge", "replacement", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "replacement", "pursues_goal", "goal"],
            ["add_edge", "replacement", "targets_developmental_capability", "capability"],
            ["add_edge", "motor_episode", "has_embodied_motor_program", "compound_program"],
            ["add_edge", "motor_episode", "uses_embodied_motor_prior", "compound_prior"],
            ["del_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["del_edge", "motor_episode", "has_embodied_motor_program", "selected_program"],
            ["del_edge", "motor_episode", "uses_embodied_motor_prior", "selected_prior"],
            ["del_edge", "session", "has_selected_embodied_motor_program", "selected_program"],
            ["del_edge", "session", "uses_embodied_motor_hint", "selected_prior"],
            ["add_edge", "session", "has_selected_embodied_motor_program", "compound_program"],
            ["add_edge", "session", "uses_embodied_motor_hint", "compound_prior"],
            ["set_attr", "motor_episode", "status", "selected_for_rehearsal"],
        ],
    }


def supersede_undispatched_counterfactual_after_coordination_recollapse_rule():
    """Release imagination for the choice atomically superseded above."""
    return {
        "name": "emb_supersede_undispatched_counterfactual_after_coordination_recollapse",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A pre-dispatch coordination re-collapse invalidates only the counterfactual for its exact old program. Physical requests remain protected by the re-collapse gate; the ordinary imagination rule can then project the replacement compound.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_embodied_motor_coordination_context", "context"],
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "replacement"],
            ["replacement", "selects_embodied_motor_program", "replacement_program"],
            ["context", "has_coordination_reselection", "reselection"],
            ["reselection", "supersedes_embodied_motor_selection", "old_selection"],
            ["old_selection", "selects_embodied_motor_program", "old_program"],
            ["session", "has_counterfactual_embodied_trial", "counterfactual"],
            ["counterfactual", "tests_embodied_motor_program", "old_program"],
        ],
        "where": And(
            # A later repair may legitimately select the old program again.
            # In that state the retained reselection is history, not authority:
            # deleting the current counterfactual would oscillate with the
            # ordinary rehearsal rule forever.
            Not(Eq(V("replacement_program"), V("old_program"))),
            absent(IN("old_program", "enacts_embodied_motor_program")),
        ),
        "effects": [
            ["set_attr", "counterfactual", "status", "superseded_before_dispatch"],
            ["del_edge", "session", "has_counterfactual_embodied_trial", "counterfactual"],
        ],
    }


# =====================================================================
# THE OBSERVATION APERTURE BELONGS TO THE BODY.
#
# How long you must watch before a movement exceeds one quantization unit is
# a fact about THE BODY'S dynamics against THE BODY'S measurement resolution.
# It is the same fact whichever program is running, so it must ACCUMULATE and
# SURVIVE program switching.
#
# Measured defect this repairs (live, 49 trials): the aperture was held on the
# PROGRAM, and every switch to a different program restarted the ladder at the
# bottom. 44 of 45 programs sat at 1 frame; one had climbed to 4. The body
# needs >= 8 frames before a 0.085 rad twitch crosses one proprioceptive
# quantum, so the configuration delta was 0 on 100% of trials, the success
# criterion could never evaluate true, and the curriculum could not leave
# ordinal 0. The climb was real and its evidence was thrown away.
#
# REPRESENTATION: a LOG EXPONENT, held on the body, plus a small signed
# exponent HINT held with the program, in the SAME log dimension:
#
#     effective_frames = 2 ** (body_k + program_hint_k)
#
# clamped into the world's declared mechanical bounds. This is the `scale2`
# dimension the tree already has — a base is a dimension, and a ratio in it is
# the additive integer `k` that rung 1 reads for free. Both quantities stay
# IN-FRAME INTEGERS, which the frame/continuum invariant requires, and the
# existing repair already DOUBLES, i.e. it already increments k by 1.
#
# The hint is a SCALING, never an independent aperture: a program that needs
# longer than the body's baseline (a small slow twitch) or shorter (a large
# compound movement) says so as an offset, and inherits every climb the body
# makes. Its neutral default is 0 — no scaling.
# =====================================================================

def body_aperture_log(body="body"):
    """The body's climbed exponent. Absent reads as the neutral 0 (2**0 = 1
    frame), which is the honest floor rather than a silent coarse aperture."""
    return Plus(A(body, "temporal_aperture_log_units"), L(0))


def program_aperture_hint_log(program="program"):
    """The program's SCALING relative to the body, in the same log dimension.
    Absent reads as 0 — no scaling — which is what an unhinted program means."""
    return Plus(A(program, "aperture_hint_log_units"), L(0))


def effective_aperture_frames(body="body", program="program", contract="contract"):
    """minimum_actuation_frames * 2 ** (body_k + hint_k), under the horizon.

    THE EXPONENT SCALES THE WORLD'S DECLARED MINIMUM; it is not an absolute
    frame count. That distinction is load-bearing and was got wrong first: with
    an absolute `2 ** k`, a world declaring a minimum actuation of 13 frames
    absorbed the first four climbs entirely into the floor clamp — the body
    climbed and nothing moved. Anchoring the ladder AT the declared minimum
    makes k mean exactly "doublings above the mechanical baseline", which is
    also precisely what the rule it replaces did (it doubled), so the semantics
    are preserved at every contract rather than only at one.

    The exponent floors at 0 because the contract's minimum is a MECHANICAL
    bound: a program hint may ask for less observation than the body baseline,
    but it cannot ask for less than the world says an actuation takes. The
    horizon clamps the top, and because the assessment that drives the climb
    stops firing once the effective aperture reaches the horizon, the ladder
    terminates on its own.
    """
    return Min(
        Times(
            A(contract, "minimum_actuation_frames"),
            {"type": "Pow", "a": L(2), "b": {"type": "Max", "items": [
                Plus(body_aperture_log(body), program_aperture_hint_log(program)),
                L(0),
            ]}},
        ),
        A(contract, "maximum_observation_horizon_frames"),
    )


def open_body_temporal_aperture_rule():
    """Declare the body's aperture before anything has been measured.

    Provenance travels with it, on the ledger's discipline: `_measured` is 0
    until a receipt has actually driven a climb, so a declared floor is usable
    and is never confusable with an observation.
    """
    return {
        "name": "emb_open_body_temporal_aperture",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "One observation aperture per BODY, opened at the neutral exponent. "
            "It is opened rather than assumed so that the value is present in "
            "the graph with its provenance attached: an absent exponent and a "
            "measured one must not read the same."
        ),
        "match": [["episode", "has_embodied_body_schema", "body"]],
        # ABSENT, not zero: `Eq(Attr, Lit None)` is true only for a missing key,
        # so a body that has already climbed to exponent 0... cannot happen, but
        # a body that has climbed at all is never reset by this rule.
        "where": Eq(A("body", "temporal_aperture_log_units"), L(None)),
        "effects": [
            ["set_attr", "body", "temporal_aperture_log_units", 0],
            ["set_attr", "body", "temporal_aperture_measured", 0],
        ],
    }


def apply_body_aperture_to_program_rule():
    """THE INHERITANCE. A program's frames are a READING of the body's aperture.

    This is the rule that repairs the measured defect: a FRESH, never-enacted
    program does not start at the bottom of the ladder, because its aperture was
    never its own to begin with. It reads the body's climbed exponent scaled by
    its own hint, so every program in the episode moves the moment the BODY
    learns it must watch for longer.

    Unconditional and a pure function of (body, hint, contract), so re-firing
    rewrites the same number and the fixpoint terminates — the same discipline
    the energy ledger's settle rule runs under.
    """
    return {
        "name": "emb_apply_body_temporal_aperture_to_program",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "The observation aperture is a body fact, so the program reads it "
            "rather than owning it. A program-level frame count is no longer "
            "authoritative anywhere: whatever set it, this rule restates it "
            "from the body's exponent and the program's own scaling hint."
        ),
        "match": [
            ["episode", "has_embodied_body_schema", "body"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "candidate"],
            ["candidate", "proposes_embodied_motor_program", "program"],
        ],
        "where": L(True),
        "effects": [
            ["set_attr", "program", "simulator_frames",
             T(effective_aperture_frames())],
            # Legible: where this number came from, and whether the body's part
            # of it was climbed or merely declared.
            ["set_attr", "program", "aperture_source", "body_scaled_hint"],
            ["set_attr", "program", "aperture_body_log_units",
             T(body_aperture_log())],
            ["set_attr", "program", "aperture_measured",
             T(Plus(A("body", "temporal_aperture_measured"), L(0)))],
        ],
    }


def temporal_aperture_is_admissible():
    """Graph evidence that a longer observation, not a new action, is needed.

    The zero outcome must be a real, energized observation with no measured
    configuration change.  The declared mechanical horizon bounds the binary
    expansion, so a failed aperture cannot permanently suppress breadth.
    """
    return And(
        Eq(A("evidence", "grounded"), L(1)),
        Eq(A("evidence", "goal_progress_units"), L(0)),
        Eq(A("evidence", "proprioceptive_configuration_l1_units"), L(0)),
        Gt(A("evidence", "energy_cost_units"), L(0)),
        Lt(A("old_program", "simulator_frames"),
           A("contract", "maximum_observation_horizon_frames")),
    )


def assess_supervisory_temporal_aperture_rule():
    """Materialize the supervisor's temporal-versus-breadth premise once."""
    return {
        "name": "emb_assess_receipt_temporal_aperture_before_motor_revision",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The supervisor first writes one immutable assessment of the exact settled receipt. The two revision proposals consume opposite values of this node, so they cannot race from the same pre-effect graph state.",
        "match": [
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["episode", "has_embodied_learning_session", "session"],
            ["session", "has_causal_embodied_learning_receipt", "receipt"],
            ["receipt", "grounded_in_external_trial_evidence", "evidence"],
            ["receipt", "caused_by_embodied_motor_program", "old_program"],
        ],
        "where": And(
            Eq(A("receipt", "status"), L("closed")),
            Eq(A("receipt", "causal_closed"), L(1)),
            Eq(A("receipt", "grounded"), L(1)),
            absent(N("receipt", "has_embodied_supervisory_temporal_assessment")),
        ),
        "effects": [
            ["add_node", "assessment", "EmbodiedSupervisoryTemporalAssessment", {
                "requires_wider_observation": T(If(
                    temporal_aperture_is_admissible(), L(1), L(0),
                )),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "receipt", "has_embodied_supervisory_temporal_assessment", "assessment"],
            ["add_edge", "assessment", "assesses_embodied_motor_program", "old_program"],
            ["add_edge", "assessment", "grounded_in_embodied_learning_receipt", "receipt"],
        ],
    }


def enact_supervised_motor_program_revision_rule():
    """Enact one supervisor-selected revision and explicitly restore supervision."""
    return {
        "name": "emb_enact_receipt_grounded_motor_program_revision",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Only this graph rule resolves a zero-yield supervisory residual. It enacts either the receipt-grounded breadth alternative or the receipt-grounded temporal aperture alternative, then restores the exact suspended process, policy, step, and capability. The check-in and residual remain auditable; no host bypass exists.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_cognitive_process", "process"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["plan", "has_embodied_motor_program_revision", "revision"],
            ["revision", "has_current_embodied_motor_program_revision_enactment", "enactment"],
            ["revision", "addresses_learning_plan_residual", "residual"],
            ["revision", "grounded_in_embodied_learning_receipt", "receipt"],
            ["revision", "revises_embodied_motor_program", "old_program"],
            ["revision", "selects_pareto_candidate", "candidate"],
            ["revision", "selects_embodied_motor_program", "program"],
            ["revision", "uses_embodied_motor_prior", "prior"],
            ["revision", "continues_learning_plan_step", "step"],
            ["revision", "continues_learning_capability", "capability"],
            ["revision", "continues_goal", "goal"],
            ["revision", "continues_cognitive_process", "process"],
            ["revision", "continues_cognitive_supervision_policy", "policy"],
            ["revision", "responds_to_cognitive_checkin", "checkin"],
        ],
        "where": And(
            Eq(A("episode", "development_learning_active"), L(1)),
            Eq(A("revision", "status"), L("proposed")),
            Eq(A("residual", "status"), L("open")),
            Eq(A("process", "status"), L("replan_required")),
            Eq(A("process", "continuation_authority"), L(0)),
            Eq(A("policy", "enabled"), L(0)),
            Eq(A("step", "status"), L("meta_suspended")),
            Eq(A("capability", "status"), L("meta_suspended")),
            absent(N("motor_episode", "has_embodied_motor_bootstrap_selection")),
            absent(N("motor_episode", "has_embodied_motor_program")),
        ),
        "effects": [
            ["add_node", "selection", "EmbodiedMotorBootstrapSelection", {
                "status": "selected", "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["add_edge", "selection", "selects_pareto_candidate", "candidate"],
            ["add_edge", "selection", "selects_embodied_motor_program", "program"],
            ["add_edge", "selection", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "selection", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "selection", "pursues_goal", "goal"],
            ["add_edge", "selection", "targets_developmental_capability", "capability"],
            ["add_edge", "selection", "enacted_from_embodied_motor_program_revision", "revision"],
            ["add_edge", "motor_episode", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "motor_episode", "has_embodied_motor_program", "program"],
            ["add_edge", "revision", "enacts_embodied_motor_selection", "selection"],
            ["add_edge", "revision", "resolves_learning_plan_residual", "residual"],
            ["add_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["add_edge", "episode", "has_active_embodied_developmental_capability", "capability"],
            ["set_attr", "revision", "status", "enacted"],
            ["set_attr", "residual", "status", "resolved"],
            ["set_attr", "step", "status", "active"],
            ["set_attr", "capability", "status", "active"],
            # This continuation begins *after* the receipt that caused the
            # revision.  Marking that causal boundary prevents the generic
            # developmental frontier from immediately releasing the freshly
            # restored capability as though it were still the old completed
            # action (ed_release_incomplete_experiment_back_to_frontier).
            ["set_attr", "capability", "activation_receipt_seq", T(
                A("receipt", "development_receipt_seq")
            )],
            ["set_attr", "process", "status", "monitoring"],
            ["set_attr", "process", "continuation_authority", 1],
            # Restore a *new lease* rather than only flipping authority.  The
            # supervisor's check-in remains in the graph (now explicitly
            # resolved by this revision), while its old deadline cannot
            # immediately manufacture the same zero-yield replan again.
            ["set_attr", "process", "lease_generation", T(Plus(
                A("process", "lease_generation"), L(1),
            ))],
            ["set_attr", "process", "last_checkin_epoch", T(A("policy", "cognitive_epoch"))],
            ["set_attr", "process", "renew_before_epoch", T(Plus(
                A("policy", "cognitive_epoch"), A("process", "checkin_span_units"),
            ))],
            ["set_attr", "process", "next_checkin_epoch", T(Plus(
                A("policy", "cognitive_epoch"), A("process", "checkin_span_units"),
            ))],
            ["set_attr", "process", "baseline_effort_units", T(A("step", "evidence_spent_units"))],
            ["set_attr", "process", "checkin_count", T(Plus(
                A("process", "checkin_count"), L(1),
            ))],
            ["set_attr", "policy", "enabled", 1],
            ["set_attr", "checkin", "status", "motor_program_revised"],
            ["set_attr", "episode", "cognitive_continuation_authority", 1],
            ["set_attr", "episode", "cognitive_checkin_terminal", 0],
            ["set_attr", "motor_episode", "status", "selected_for_rehearsal"],
        ],
    }


def enact_supervised_temporal_aperture_revision_rule():
    """Enact the same program when a revision intentionally preserves it.

    The matcher is deliberately separate from the ordinary revision enactment:
    rule bindings are injective, so the two program roles in a distinct-probe
    revision cannot express ``old_program is program``.  Authority recovery is
    otherwise the same graph transition.
    """
    return {
        "name": "emb_enact_receipt_grounded_temporal_aperture_revision",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A temporal revision re-enacts its exact causally implicated opaque program, doubles only its graph-owned observation aperture up to the mechanical horizon, and restores the suspended supervisor continuation.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            # The aperture is raised on the BODY, so the body is matched in.
            ["episode", "has_embodied_body_schema", "body"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_cognitive_process", "process"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["plan", "has_embodied_motor_program_revision", "revision"],
            ["revision", "has_current_embodied_motor_program_revision_enactment", "enactment"],
            ["revision", "addresses_learning_plan_residual", "residual"],
            ["revision", "grounded_in_embodied_learning_receipt", "receipt"],
            ["revision", "revises_embodied_motor_program", "program"],
            ["revision", "selects_pareto_candidate", "candidate"],
            ["revision", "selects_embodied_motor_program", "program"],
            ["revision", "uses_embodied_motor_prior", "prior"],
            ["revision", "continues_learning_plan_step", "step"],
            ["revision", "continues_learning_capability", "capability"],
            ["revision", "continues_goal", "goal"],
            ["revision", "continues_cognitive_process", "process"],
            ["revision", "continues_cognitive_supervision_policy", "policy"],
            ["revision", "responds_to_cognitive_checkin", "checkin"],
        ],
        "where": And(
            Eq(A("episode", "development_learning_active"), L(1)),
            Eq(A("revision", "status"), L("proposed")),
            Eq(A("revision", "kind"), L("receipt_grounded_temporal_aperture")),
            Eq(A("residual", "status"), L("open")),
            Eq(A("process", "status"), L("replan_required")),
            Eq(A("process", "continuation_authority"), L(0)),
            Eq(A("policy", "enabled"), L(0)),
            Eq(A("step", "status"), L("meta_suspended")),
            Eq(A("capability", "status"), L("meta_suspended")),
            absent(N("motor_episode", "has_embodied_motor_bootstrap_selection")),
            absent(N("motor_episode", "has_embodied_motor_program")),
        ),
        "effects": [
            ["add_node", "selection", "EmbodiedMotorBootstrapSelection", {
                "status": "selected", "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["add_edge", "selection", "selects_pareto_candidate", "candidate"],
            ["add_edge", "selection", "selects_embodied_motor_program", "program"],
            ["add_edge", "selection", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "selection", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "selection", "pursues_goal", "goal"],
            ["add_edge", "selection", "targets_developmental_capability", "capability"],
            ["add_edge", "selection", "enacted_from_embodied_motor_program_revision", "revision"],
            ["add_edge", "motor_episode", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "motor_episode", "has_embodied_motor_program", "program"],
            ["add_edge", "revision", "enacts_embodied_motor_selection", "selection"],
            ["add_edge", "revision", "resolves_learning_plan_residual", "residual"],
            ["add_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["add_edge", "episode", "has_active_embodied_developmental_capability", "capability"],
            ["set_attr", "revision", "status", "enacted"],
            # RAISE THE BODY, NOT THE PROGRAM. Doubling this program's frames
            # was the defect: the climb was real, and it was discarded the next
            # time a different program was selected. Incrementing the body's
            # exponent by 1 IS the same doubling — 2**(k+1) = 2*2**k — but it
            # is held where it is true, so it survives the switch and every
            # other program inherits it through
            # `emb_apply_body_temporal_aperture_to_program`.
            ["set_attr", "body", "temporal_aperture_log_units",
             T(Plus(body_aperture_log(), L(1)))],
            # Provenance: this exponent has now been CLIMBED from receipts, not
            # merely declared at boot.
            ["set_attr", "body", "temporal_aperture_measured", 1],
            ["set_attr", "residual", "status", "resolved"],
            ["set_attr", "step", "status", "active"],
            ["set_attr", "capability", "status", "active"],
            ["set_attr", "capability", "activation_receipt_seq", T(
                A("receipt", "development_receipt_seq")
            )],
            ["set_attr", "process", "status", "monitoring"],
            ["set_attr", "process", "continuation_authority", 1],
            ["set_attr", "process", "lease_generation", T(Plus(
                A("process", "lease_generation"), L(1),
            ))],
            ["set_attr", "process", "last_checkin_epoch", T(A("policy", "cognitive_epoch"))],
            ["set_attr", "process", "renew_before_epoch", T(Plus(
                A("policy", "cognitive_epoch"), A("process", "checkin_span_units"),
            ))],
            ["set_attr", "process", "next_checkin_epoch", T(Plus(
                A("policy", "cognitive_epoch"), A("process", "checkin_span_units"),
            ))],
            ["set_attr", "process", "baseline_effort_units", T(A("step", "evidence_spent_units"))],
            ["set_attr", "process", "checkin_count", T(Plus(
                A("process", "checkin_count"), L(1),
            ))],
            ["set_attr", "policy", "enabled", 1],
            ["set_attr", "checkin", "status", "motor_program_revised"],
            ["set_attr", "episode", "cognitive_continuation_authority", 1],
            ["set_attr", "episode", "cognitive_checkin_terminal", 0],
            ["set_attr", "motor_episode", "status", "selected_for_rehearsal"],
        ],
    }


def open_motor_program_revision_enactment_rule():
    """Open the immutable enactment event after a revision proposal."""
    return {
        "name": "emb_open_pending_receipt_grounded_motor_program_revision_enactment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Revision proposal and authority restoration are separate causal graph transitions. Opening the request materializes the immutable event that permits enactment; it is not a host retry or an automatic residual dismissal.",
        "match": [
            ["revision", "has_pending_embodied_motor_program_revision_enactment_request", "request"],
        ],
        "where": And(
            Eq(A("revision", "status"), L("proposed")),
            absent(N("revision", "has_current_embodied_motor_program_revision_enactment")),
        ),
        "effects": [
            ["add_node", "enactment", "EmbodiedMotorProgramRevisionEnactment", {
                "kind": T(A("revision", "kind")),
                "request_ref": T(V("request")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "revision", "has_current_embodied_motor_program_revision_enactment", "enactment"],
            ["del_edge", "revision", "has_pending_embodied_motor_program_revision_enactment_request", "request"],
        ],
    }


def propose_supervised_motor_program_revision_rule():
    """Translate a real supervisory residual into a distinct motor probe."""
    return {
        "name": "emb_propose_distinct_motor_program_for_zero_yield_supervisory_residual",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A zero-yield check-in is not ignored. It waits until the currently enacted motor selection has been retired by its physical receipt, then uses the successor epoch's exact receipt to propose a distinct motor program. The proposal cannot itself resolve the residual or restore authority.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_cognitive_process", "process"],
            ["motor_episode", "has_embodied_motor_bootstrap_profile", "profile"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["epoch", "grounded_in_embodied_learning_receipt", "receipt"],
            ["motor_episode", "has_embodied_motor_bootstrap_ready_candidate", "candidate"],
            ["profile", "has_pareto_candidate", "candidate"],
            ["candidate", "has_embodied_motor_bootstrap_pareto_ready", "ready"],
            ["candidate", "uses_embodied_motor_prior", "prior"],
            ["candidate", "proposes_embodied_motor_program", "program"],
            ["plan", "has_learning_plan_residual", "residual"],
            ["residual", "about_learning_plan_step", "step"],
            ["residual", "raised_by_cognitive_checkin", "checkin"],
            ["step", "plans_learning_capability", "capability"],
            ["step", "pursues_goal", "goal"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "supervises_learning_plan_step", "step"],
            ["process", "supervises_learning_capability", "capability"],
            ["session", "has_causal_embodied_learning_receipt", "receipt"],
            ["receipt", "caused_by_embodied_motor_program", "old_program"],
            ["receipt", "grounded_in_external_trial_evidence", "evidence"],
            ["receipt", "has_embodied_supervisory_temporal_assessment", "assessment"],
        ],
        "where": And(
            Eq(A("residual", "status"), L("open")),
            Eq(A("residual", "kind"), L("inefficient_cognitive_process_window")),
            # NO YIELD TEST. `inefficient_cognitive_process_window` IS the hold
            # rules' own verdict -- BOTH `cs_hold_zero_yield_process_for_replanning`
            # and `cs_hold_marginally_dominated_process_for_replanning` mint it --
            # so requiring `causal_yield_units == 0` on top applied a second,
            # stricter test the hold never applied, and left every process held for
            # INEFFICIENCY rather than for producing nothing with no proposer at all.
            #
            # Measured 2026-08-07 on a live 6-hour run: `effector_consequence_survey`
            # (ordinal 1) was held with an open residual carrying
            # `causal_yield_units = 3, evidence_spent_units = 7` -- it had succeeded 7
            # of 22 attempts. Succeeding is what disqualified it from the only escape
            # from `replan_required`, so it stayed `meta_suspended` across every run
            # of this line. Dropping the test makes zero-yield the SPECIAL case of
            # insufficient-yield rather than the only case, and introduces no
            # constant. The proposer stays gated by the suspended step, the suspended
            # capability, the held process, zero continuation authority, the disabled
            # policy, and one-revision-per-residual.
            Eq(A("checkin", "status"), L("replan_required")),
            Eq(A("process", "status"), L("replan_required")),
            Eq(A("process", "continuation_authority"), L(0)),
            Eq(A("policy", "enabled"), L(0)),
            Eq(A("step", "status"), L("meta_suspended")),
            Eq(A("capability", "status"), L("meta_suspended")),
            Eq(A("receipt", "status"), L("closed")),
            Eq(A("receipt", "causal_closed"), L(1)),
            Eq(A("receipt", "grounded"), L(1)),
            Eq(A("evidence", "grounded"), L(1)),
            Eq(A("assessment", "requires_wider_observation"), L(0)),
            # The exact receipt must retire the live selection before its
            # successor epoch may revise a program.  Otherwise a newly
            # opened supervisory residual could incorrectly bind the prior
            # epoch while the current trial is still being settled.
            no_bound_selection_for_this_capability(),
            # The residual is repaired from the newest retained causal
            # receipt.  Historical receipts stay inspectable but cannot
            # reopen a revision for an already superseded motor probe.
            Not(Exists(
                N("session", "has_causal_embodied_learning_receipt"), "newer_receipt",
                Gt(A("newer_receipt", "development_receipt_seq"),
                   A("receipt", "development_receipt_seq")),
            )),
            Eq(A("goal", "status"), L("active")),
            is_frontier_candidate("candidate"),
            Not(lower_opaque_frontier_candidate()),
            Not(Eq(V("program"), V("old_program"))),
            absent(N("residual", "has_embodied_motor_program_revision")),
        ),
        "effects": [
            ["add_node", "revision", "EmbodiedMotorProgramRevision", {
                "status": "proposed", "kind": "receipt_grounded_distinct_motor_program",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "enactment_request", "EmbodiedMotorProgramRevisionEnactmentRequest", {
                "kind": "receipt_grounded_distinct_motor_program",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "plan", "has_embodied_motor_program_revision", "revision"],
            ["add_edge", "residual", "has_embodied_motor_program_revision", "revision"],
            ["add_edge", "revision", "addresses_learning_plan_residual", "residual"],
            ["add_edge", "revision", "grounded_in_embodied_learning_receipt", "receipt"],
            ["add_edge", "revision", "grounded_in_external_trial_evidence", "evidence"],
            ["add_edge", "revision", "revises_embodied_motor_program", "old_program"],
            ["add_edge", "revision", "selects_pareto_candidate", "candidate"],
            ["add_edge", "revision", "selects_embodied_motor_program", "program"],
            ["add_edge", "revision", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "revision", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "revision", "continues_learning_plan_step", "step"],
            ["add_edge", "revision", "continues_learning_capability", "capability"],
            ["add_edge", "revision", "continues_goal", "goal"],
            ["add_edge", "revision", "continues_cognitive_process", "process"],
            ["add_edge", "revision", "continues_cognitive_supervision_policy", "policy"],
            ["add_edge", "revision", "responds_to_cognitive_checkin", "checkin"],
            ["add_edge", "revision", "has_pending_embodied_motor_program_revision_enactment_request", "enactment_request"],
        ],
    }


def propose_supervised_temporal_aperture_revision_rule():
    """Offer observation widening at the same supervisory choice point as breadth."""
    return {
        "name": "emb_propose_temporal_aperture_for_zero_consequence_supervisory_residual",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A zero-yield check-in may mean that the selected action was observed too briefly rather than that its topology was wrong. From the exact newest settled receipt, the supervisor may re-enact the same opaque program at a graph-derived wider aperture. The distinct-program proposal is mutually exclusive and remains the breadth alternative.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_cognitive_process", "process"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["epoch", "grounded_in_embodied_learning_receipt", "receipt"],
            ["motor_episode", "has_embodied_motor_bootstrap_candidate", "candidate"],
            ["candidate", "uses_embodied_motor_prior", "prior"],
            ["candidate", "proposes_embodied_motor_program", "old_program"],
            ["plan", "has_learning_plan_residual", "residual"],
            ["residual", "about_learning_plan_step", "step"],
            ["residual", "raised_by_cognitive_checkin", "checkin"],
            ["step", "plans_learning_capability", "capability"],
            ["step", "pursues_goal", "goal"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "supervises_learning_plan_step", "step"],
            ["process", "supervises_learning_capability", "capability"],
            ["session", "has_causal_embodied_learning_receipt", "receipt"],
            ["receipt", "caused_by_embodied_motor_program", "old_program"],
            ["receipt", "grounded_in_external_trial_evidence", "evidence"],
            ["receipt", "has_embodied_supervisory_temporal_assessment", "assessment"],
        ],
        "where": And(
            Eq(A("residual", "status"), L("open")),
            Eq(A("residual", "kind"), L("inefficient_cognitive_process_window")),
            # NO YIELD TEST. `inefficient_cognitive_process_window` IS the hold
            # rules' own verdict -- BOTH `cs_hold_zero_yield_process_for_replanning`
            # and `cs_hold_marginally_dominated_process_for_replanning` mint it --
            # so requiring `causal_yield_units == 0` on top applied a second,
            # stricter test the hold never applied, and left every process held for
            # INEFFICIENCY rather than for producing nothing with no proposer at all.
            #
            # Measured 2026-08-07 on a live 6-hour run: `effector_consequence_survey`
            # (ordinal 1) was held with an open residual carrying
            # `causal_yield_units = 3, evidence_spent_units = 7` -- it had succeeded 7
            # of 22 attempts. Succeeding is what disqualified it from the only escape
            # from `replan_required`, so it stayed `meta_suspended` across every run
            # of this line. Dropping the test makes zero-yield the SPECIAL case of
            # insufficient-yield rather than the only case, and introduces no
            # constant. The proposer stays gated by the suspended step, the suspended
            # capability, the held process, zero continuation authority, the disabled
            # policy, and one-revision-per-residual.
            Eq(A("checkin", "status"), L("replan_required")),
            Eq(A("process", "status"), L("replan_required")),
            Eq(A("process", "continuation_authority"), L(0)),
            Eq(A("policy", "enabled"), L(0)),
            Eq(A("step", "status"), L("meta_suspended")),
            Eq(A("capability", "status"), L("meta_suspended")),
            Eq(A("receipt", "status"), L("closed")),
            Eq(A("receipt", "causal_closed"), L(1)),
            Eq(A("receipt", "grounded"), L(1)),
            no_bound_selection_for_this_capability(),
            Not(Exists(
                N("session", "has_causal_embodied_learning_receipt"), "newer_receipt",
                Gt(A("newer_receipt", "development_receipt_seq"),
                   A("receipt", "development_receipt_seq")),
            )),
            Eq(A("goal", "status"), L("active")),
            Eq(A("assessment", "requires_wider_observation"), L(1)),
            absent(N("residual", "has_embodied_motor_program_revision")),
        ),
        "effects": [
            ["add_node", "revision", "EmbodiedMotorProgramRevision", {
                "status": "proposed", "kind": "receipt_grounded_temporal_aperture",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "enactment_request", "EmbodiedMotorProgramRevisionEnactmentRequest", {
                "kind": "receipt_grounded_temporal_aperture",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "plan", "has_embodied_motor_program_revision", "revision"],
            ["add_edge", "residual", "has_embodied_motor_program_revision", "revision"],
            ["add_edge", "revision", "addresses_learning_plan_residual", "residual"],
            ["add_edge", "revision", "grounded_in_embodied_learning_receipt", "receipt"],
            ["add_edge", "revision", "grounded_in_external_trial_evidence", "evidence"],
            ["add_edge", "revision", "revises_embodied_motor_program", "old_program"],
            ["add_edge", "revision", "selects_pareto_candidate", "candidate"],
            ["add_edge", "revision", "selects_embodied_motor_program", "old_program"],
            ["add_edge", "revision", "uses_embodied_motor_prior", "prior"],
            ["add_edge", "revision", "is_in_embodied_motor_selection_epoch", "epoch"],
            ["add_edge", "revision", "continues_learning_plan_step", "step"],
            ["add_edge", "revision", "continues_learning_capability", "capability"],
            ["add_edge", "revision", "continues_goal", "goal"],
            ["add_edge", "revision", "continues_cognitive_process", "process"],
            ["add_edge", "revision", "continues_cognitive_supervision_policy", "policy"],
            ["add_edge", "revision", "responds_to_cognitive_checkin", "checkin"],
            ["add_edge", "revision", "has_pending_embodied_motor_program_revision_enactment_request", "enactment_request"],
        ],
    }


def update_novelty_coordinate_rule():
    """Keep the candidate's explicit novelty coordinate receipt-grounded."""
    return {
        "name": "emb_update_bootstrap_novelty_coordinate_after_grounded_receipt",
        "area": "cognitive_pareto",
        "latency_class": "hard_realtime",
        "comment": "Practice changes the untried-structure coordinate, not a hidden reward. The value remains an integer Pareto coordinate and is updated only from a settled physical receipt.",
        "match": [
            ["selection", "selects_pareto_candidate", "candidate"],
            ["selection", "settled_by_grounded_evidence", "evidence"],
            ["candidate", "has_pareto_value", "value"],
        ],
        "where": Eq(A("value", "dimension_ordinal"), L(0)),
        "effects": [
            ["set_attr_if_different", "value", "raw_value", T(A("candidate", "experience_units"))],
            ["set_attr_if_different", "value", "signed_value", T(Neg(A("candidate", "experience_units")))],
        ],
    }


def retire_selection_after_grounded_receipt_rule():
    """Release one settled selection so the graph can choose its next probe.

    The session receives a normal selected program during a trial.  A physical
    receipt is the only transition that retires that exact selection; imagined
    evidence cannot cause a new actuator proposal.
    """
    return {
        "name": "emb_retire_settled_motor_selection_and_reopen_pareto_frontier",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # A retained receipt may be visible through more than one historical
        # path on resume.  Retire one live selection atomically before
        # considering another match, otherwise the same physical observation
        # can mint an unbounded set of successor epochs.
        "batch": False,
        "comment": "A grounded receipt increments practice exactly once, records its provenance, and releases the selected program/prior/request/counterfactual edges. The ordinary graph selection rule—not Python—then chooses the next Pareto-frontier probe.",
        "match": [
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["selection", "selects_pareto_candidate", "candidate"],
            ["selection", "selects_embodied_motor_program", "program"],
            ["selection", "uses_embodied_motor_prior", "prior"],
            ["session", "has_grounded_external_trial_request", "request"],
            ["request", "has_grounded_external_trial_evidence", "evidence"],
            ["request", "enacts_embodied_motor_program", "program"],
            ["evidence", "evidence_for_embodied_trial_request", "request"],
            ["evidence", "measures_embodied_motor_program", "program"],
            ["session", "has_counterfactual_embodied_trial", "counterfactual"],
            ["counterfactual", "tests_embodied_motor_program", "program"],
            ["request", "has_embodied_learning_trial_receipt", "receipt"],
            ["receipt", "grounded_in_external_trial_evidence", "evidence"],
            ["receipt", "caused_by_embodied_motor_program", "program"],
        ],
        "where": And(
            Eq(A("request", "status"), L("evidenced")),
            Eq(A("evidence", "grounded"), L(1)),
            Eq(A("receipt", "status"), L("closed")),
            Eq(A("receipt", "causal_closed"), L(1)),
            Eq(A("receipt", "grounded"), L(1)),
            absent(N("selection", "settled_by_grounded_evidence")),
        ),
        "effects": [
            ["add_edge", "selection", "settled_by_grounded_evidence", "evidence"],
            ["add_edge", "candidate", "has_grounded_motor_bootstrap_evidence", "evidence"],
            ["set_attr", "candidate", "experience_units", T({
                "type": "Plus", "items": [A("candidate", "experience_units"), L(1)],
            })],
            # A receipt requests the successor epoch.  The separate opener
            # consumes this request on the next graph pass, ensuring the
            # selector observes an immutable causal event rather than being
            # stranded behind a same-pass semi-naive cursor.
            ["add_node", "next_epoch_request", "EmbodiedMotorSelectionEpochRequest", {
                "kind": "opaque_motor_bootstrap",
                "origin": "grounded_receipt",
                "settled_receipt_ref": T(V("receipt")),
                "settled_experience_units": T(Plus(
                    Sum(N("motor_episode", "has_embodied_motor_bootstrap_candidate"),
                        "epoch_candidate", A("epoch_candidate", "experience_units")),
                    L(1),
                )),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "next_epoch_request", "grounded_in_embodied_learning_receipt", "receipt"],
            ["add_edge", "motor_episode", "has_pending_embodied_motor_selection_epoch_request", "next_epoch_request"],
            ["del_edge", "motor_episode", "has_current_embodied_motor_selection_epoch", "epoch"],
            ["del_edge", "motor_episode", "has_embodied_motor_bootstrap_selection", "selection"],
            ["del_edge", "motor_episode", "has_embodied_motor_program", "program"],
            ["del_edge", "motor_episode", "uses_embodied_motor_prior", "prior"],
            ["del_edge", "session", "has_selected_embodied_motor_program", "program"],
            ["del_edge", "session", "uses_embodied_motor_hint", "prior"],
            ["del_edge", "session", "has_grounded_external_trial_request", "request"],
            ["del_edge", "session", "has_counterfactual_embodied_trial", "counterfactual"],
            ["set_attr", "motor_episode", "status", "bootstrap_candidates"],
        ],
    }


def manifest() -> dict:
    productions = (
        ("episode_body", "EmbodiedDevelopmentEpisode", "has_embodied_body_schema", "EmbodiedBodySchema"),
        ("episode_motor", "EmbodiedDevelopmentEpisode", "has_embodied_motor_episode", "EmbodiedMotorEpisode"),
        ("episode_connection", "EmbodiedDevelopmentEpisode", "grounded_in_embodied_simulator_connection", "EmbodiedSimulatorConnection"),
        ("world_contract", "EmbodiedLearningWorld", "has_embodied_motor_bootstrap_contract", "EmbodiedMotorBootstrapContract"),
        ("contract_projection", "EmbodiedMotorBootstrapContract", "has_embodied_measurement_projection", "EmbodiedMeasurementProjectionAffordance"),
        ("body_effector", "EmbodiedBodySchema", "has_opaque_embodied_actuator_affordance", "EmbodiedOpaqueActuatorAffordance"),
        ("effector_singleton_episode", "EmbodiedOpaqueActuatorAffordance", "has_singleton_candidate_in_motor_episode", "EmbodiedMotorEpisode"),
        ("body_effector_topology", "EmbodiedBodySchema", "has_opaque_embodied_effector_topology_relation", "EmbodiedRawEffectorTopologyRelation"),
        ("topology_source_effector", "EmbodiedRawEffectorTopologyRelation", "has_source_opaque_embodied_effector", "EmbodiedOpaqueActuatorAffordance"),
        ("topology_target_effector", "EmbodiedRawEffectorTopologyRelation", "has_target_opaque_embodied_effector", "EmbodiedOpaqueActuatorAffordance"),
        ("body_bundle", "EmbodiedBodySchema", "has_opaque_actuator_bundle_affordance", "OpaqueActuatorBundleAffordance"),
        ("bundle_member", "OpaqueActuatorBundleAffordance", "has_opaque_embodied_actuator_affordance", "EmbodiedOpaqueActuatorAffordance"),
        ("bundle_topology", "OpaqueActuatorBundleAffordance", "grounded_in_embodied_effector_topology_relation", "EmbodiedRawEffectorTopologyRelation"),
        ("bundle_source_program", "OpaqueActuatorBundleAffordance", "grounded_in_source_embodied_motor_program", "EmbodiedMotorProgram"),
        ("bundle_source_consequence", "OpaqueActuatorBundleAffordance", "grounded_in_source_embodied_consequence", "EmbodiedLearnedConsequence"),
        ("bundle_source_receipt", "OpaqueActuatorBundleAffordance", "grounded_in_source_embodied_receipt", "EmbodiedLearningTrialReceipt"),
        ("program_opened_compound_relation", "EmbodiedMotorProgram", "has_opened_compound_topology_relation", "EmbodiedRawEffectorTopologyRelation"),
        ("capability_coordination_context", "EmbodiedSituatedDevelopmentalCapability", "has_embodied_motor_coordination_context", "EmbodiedMotorCoordinationContext"),
        ("coordination_goal", "EmbodiedMotorCoordinationContext", "targets_embodied_goal", "Goal"),
        ("coordination_receipt", "EmbodiedMotorCoordinationContext", "grounds_in_source_embodied_receipt", "EmbodiedLearningTrialReceipt"),
        ("coordination_hypothesis", "EmbodiedMotorCoordinationContext", "opens_embodied_compound_hypothesis", "OpaqueActuatorBundleAffordance"),
        ("episode_candidate", "EmbodiedMotorEpisode", "has_embodied_motor_bootstrap_candidate", "ParetoCandidate"),
        ("episode_profile", "EmbodiedMotorEpisode", "has_embodied_motor_bootstrap_profile", "ParetoProfile"),
        ("candidate_program", "ParetoCandidate", "proposes_embodied_motor_program", "EmbodiedMotorProgram"),
        ("candidate_prior", "ParetoCandidate", "uses_embodied_motor_prior", "EmbodiedMotorPrior"),
        ("candidate_initialization", "ParetoCandidate", "has_embodied_motor_bootstrap_initialization", "EmbodiedMotorBootstrapInitialization"),
        ("agent_motor_shape_memory", "Agent", "has_embodied_motor_shape_memory", "EmbodiedMotorShapeMemory"),
        ("program_motor_shape_memory", "EmbodiedMotorProgram", "has_embodied_motor_shape_memory", "EmbodiedMotorShapeMemory"),
        ("candidate_warm_start", "ParetoCandidate", "has_embodied_motor_warm_start", "EmbodiedMotorWarmStart"),
        ("program_warm_start", "EmbodiedMotorProgram", "has_embodied_motor_warm_start", "EmbodiedMotorWarmStart"),
        ("warm_start_memory", "EmbodiedMotorWarmStart", "transfers_from_embodied_motor_shape_memory", "EmbodiedMotorShapeMemory"),
        ("warm_start_source_program", "EmbodiedMotorWarmStart", "transfers_from_embodied_motor_program", "EmbodiedMotorProgram"),
        ("warm_start_source_receipt", "EmbodiedMotorWarmStart", "grounded_in_source_embodied_receipt", "EmbodiedLearningTrialReceipt"),
        ("capability_retention_context", "EmbodiedSituatedDevelopmentalCapability", "has_embodied_motor_retention_context", "EmbodiedMotorRetentionContext"),
        ("retention_context_memory", "EmbodiedMotorRetentionContext", "grounds_in_shape_matched_motor_memory", "EmbodiedMotorShapeMemory"),
        ("retention_context_warm_start", "EmbodiedMotorRetentionContext", "uses_embodied_motor_warm_start", "EmbodiedMotorWarmStart"),
        ("warm_start_local_verification", "EmbodiedMotorWarmStart", "has_local_embodied_motor_verification", "EmbodiedMotorWarmStartVerification"),
        ("verification_receipt", "EmbodiedMotorWarmStartVerification", "grounded_in_local_embodied_receipt", "EmbodiedLearningTrialReceipt"),
        ("candidate_pareto_ready", "ParetoCandidate", "has_embodied_motor_bootstrap_pareto_ready", "EmbodiedMotorBootstrapParetoReady"),
        ("episode_ready_candidate", "EmbodiedMotorEpisode", "has_embodied_motor_bootstrap_ready_candidate", "ParetoCandidate"),
        ("pending_selection_epoch_request", "EmbodiedMotorEpisode", "has_pending_embodied_motor_selection_epoch_request", "EmbodiedMotorSelectionEpochRequest"),
        ("current_selection_epoch", "EmbodiedMotorEpisode", "has_current_embodied_motor_selection_epoch", "EmbodiedMotorSelectionEpoch"),
        ("selection_epoch_request_receipt", "EmbodiedMotorSelectionEpochRequest", "grounded_in_embodied_learning_receipt", "EmbodiedLearningTrialReceipt"),
        ("selection_epoch_receipt", "EmbodiedMotorSelectionEpoch", "grounded_in_embodied_learning_receipt", "EmbodiedLearningTrialReceipt"),
        ("selection", "EmbodiedMotorEpisode", "has_embodied_motor_bootstrap_selection", "EmbodiedMotorBootstrapSelection"),
        ("candidate_measured_outcome", "ParetoCandidate", "has_receipt_grounded_motor_outcome", "ParetoCandidate"),
        ("outcome_program", "ParetoCandidate", "measures_embodied_motor_program", "EmbodiedMotorProgram"),
        ("outcome_bootstrap_candidate", "ParetoCandidate", "represents_embodied_motor_bootstrap_candidate", "ParetoCandidate"),
        ("selected_program", "EmbodiedMotorEpisode", "has_embodied_motor_program", "EmbodiedMotorProgram"),
        ("selected_prior", "EmbodiedMotorEpisode", "uses_embodied_motor_prior", "EmbodiedMotorPrior"),
        ("plan_motor_revision", "LearningPlan", "has_embodied_motor_program_revision", "EmbodiedMotorProgramRevision"),
        ("residual_motor_revision", "LearningPlanResidual", "has_embodied_motor_program_revision", "EmbodiedMotorProgramRevision"),
        ("revision_residual", "EmbodiedMotorProgramRevision", "addresses_learning_plan_residual", "LearningPlanResidual"),
        ("revision_receipt", "EmbodiedMotorProgramRevision", "grounded_in_embodied_learning_receipt", "EmbodiedLearningTrialReceipt"),
        ("revision_program", "EmbodiedMotorProgramRevision", "selects_embodied_motor_program", "EmbodiedMotorProgram"),
        ("revision_candidate", "EmbodiedMotorProgramRevision", "selects_pareto_candidate", "ParetoCandidate"),
        ("revision_selection", "EmbodiedMotorProgramRevision", "enacts_embodied_motor_selection", "EmbodiedMotorBootstrapSelection"),
        ("revision_enactment_request", "EmbodiedMotorProgramRevision", "has_pending_embodied_motor_program_revision_enactment_request", "EmbodiedMotorProgramRevisionEnactmentRequest"),
        ("revision_enactment", "EmbodiedMotorProgramRevision", "has_current_embodied_motor_program_revision_enactment", "EmbodiedMotorProgramRevisionEnactment"),
    )
    return {
        "id": "embodied_motor_bootstrap",
        "version": "1.1.0",
        "depends_on": ["embodied_body_ingest", "cognitive_pareto"],
        "area": "embodied_motor_bootstrap",
        "latency_class": "hard_realtime",
        "description": "Integer-only graph-native bootstrap from mechanically observed opaque actuator affordances and topology bundles. Exact tokens and aligned integer weights are preserved for the external humanoid trial boundary; graph-side Pareto and curiosity expose at most one selected program.",
        "nodes": [], "edges": [],
        "productions": [
            {"provenance": f"embodied_motor_bootstrap:{name}",
             "src": {"type": src, "var": "src"}, "edge_type": edge,
             "tgt": {"type": tgt, "var": "tgt"}}
            for name, src, edge, tgt in productions
        ],
        "rules": [
            open_motor_episode_rule(), open_profile_rule(),
            suspend_detached_motor_pareto_profile_rule(),
            backfill_singleton_candidate_identity_rule(),
            singleton_candidate_rule(),
            bind_topology_relation_effector_rule(endpoint="source"),
            bind_topology_relation_effector_rule(endpoint="target"),
            backfill_opened_compound_relation_identity_rule(),
            materialize_receipt_grounded_local_compound_bundle_rule(),
            open_receipt_grounded_coordination_context_rule(),
            bundle_candidate_rule(),
            initialize_candidate_state_rule(),
            # Retention runs before frontier publication, so a decoded
            # predecessor is visible to the same graph-owned collapse that
            # selects cold candidates.  It never carries external authority.
            crystallize_receipt_grounded_motor_shape_memory_rule(),
            warm_start_compatible_local_motor_program_rule(),
            activate_repeat_mission_retention_context_rule(),
            open_grounded_selection_epoch_rule(),
            open_selection_epoch_rule(),
            publish_initialized_candidate_pareto_values_rule(),
            request_selection_after_frontier_ready_rule(),
            reopen_exact_duplicate_motor_selection_rule(),
            retire_superseded_motor_selections_rule(),
            retire_superseded_current_selection_epochs_rule(),
            reopen_unexecuted_selection_for_coordination_hypothesis_rule(),
            supersede_undispatched_counterfactual_after_coordination_recollapse_rule(),
            # Enactment precedes proposal so the receipt-derived proposal
            # crosses a graph-native asynchronous boundary before authority
            # can be restored.
            enact_supervised_motor_program_revision_rule(),
            enact_supervised_temporal_aperture_revision_rule(),
            open_motor_program_revision_enactment_rule(),
            open_body_temporal_aperture_rule(),
            apply_body_aperture_to_program_rule(),
            assess_supervisory_temporal_aperture_rule(),
            propose_supervised_temporal_aperture_revision_rule(),
            propose_supervised_motor_program_revision_rule(),
            update_novelty_coordinate_rule(),
            link_exact_receipt_evidence_to_motor_candidate_rule(),
            close_goal_scoped_coordination_context_rule(),
            retire_selection_after_grounded_receipt_rule(),
            verify_warm_started_local_motor_program_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_motor_bootstrap.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
