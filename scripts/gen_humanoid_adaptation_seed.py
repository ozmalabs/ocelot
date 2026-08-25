"""Generate graph-native opaque-joint learning and humanoid balance rules."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMANOID_MANIFOLD_DIMENSIONS = (
    "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
)


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def AO(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def P0(var, key):
    return Plus(A(var, key), L(0.0))


def PI0(var, key):
    """Integer-default attribute read for integer-native cognitive rules."""
    return Plus(A(var, key), L(0))


def N0(node, key):
    return (
        P0(node, key)
        if isinstance(node, str)
        else Plus(AO(node, key), L(0.0))
    )


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def IDiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def Sqrt(arg):
    return {"type": "Sqrt", "arg": arg}


def Abs(arg):
    return {"type": "Abs", "arg": arg}


def Neg(arg):
    return {"type": "Neg", "arg": arg}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Neighbours(var, edge_type):
    return {
        "type": "Neighbours",
        "node": V(var),
        "edge_type": edge_type,
        "any_type": False,
    }


def Filter(source, var_name, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Count(source):
    return {"type": "Count", "source": source}


def Pick(source):
    return {"type": "Pick", "source": source}


def EvalSubgraph(node):
    return {"type": "EvalSubgraph", "node": node}


def SetT(*items):
    return {"type": "SetT", "items": list(items)}


def Vec(*items):
    return {"type": "Vec", "items": list(items)}


def Nth(items, index):
    return {"type": "Nth", "items": items, "index": index}


def StringConcat(*parts):
    return {"type": "StringConcat", "parts": list(parts)}


def ToJsonString(value):
    return {"type": "ToJsonString", "value": value}


def FromJsonString(text):
    return {"type": "FromJsonString", "text": text}


def Sum(source, var_name, value):
    return {
        "type": "Sum",
        "source": source,
        "var_name": var_name,
        "value": value,
    }


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Argmin(source, var_name, value, default):
    return {
        "type": "Argmin",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def T(term):
    return {"__term__": term}


def If(cond, then, other):
    return {
        "type": "IfThenElse",
        "cond": cond,
        "then": then,
        "other": other,
    }


def Max(*items):
    return {"type": "Max", "items": list(items)}


def MaxOver(source, var_name, value, default):
    return {
        "type": "MaxOver",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def Min(*items):
    return {"type": "Min", "items": list(items)}


def body_z_x(var, prefix):
    qx = P0(var, f"{prefix}_qx")
    qy = P0(var, f"{prefix}_qy")
    qz = P0(var, f"{prefix}_qz")
    qw = P0(var, f"{prefix}_qw")
    return Times(
        L(2.0),
        Plus(Times(qx, qz), Times(qy, qw)),
    )


def body_z_y(var, prefix):
    qx = P0(var, f"{prefix}_qx")
    qy = P0(var, f"{prefix}_qy")
    qz = P0(var, f"{prefix}_qz")
    qw = P0(var, f"{prefix}_qw")
    return Times(
        L(2.0),
        Minus(Times(qy, qz), Times(qx, qw)),
    )


def body_z_z(var, prefix):
    qx = P0(var, f"{prefix}_qx")
    qy = P0(var, f"{prefix}_qy")
    return Minus(
        L(1.0),
        Times(L(2.0), Plus(Times(qx, qx), Times(qy, qy))),
    )


def phase_context_distance(model):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    errors = (
        Minus(P0(model, "anchor_z_x"), body_z_x("episode", "state")),
        Minus(P0(model, "anchor_z_y"), body_z_y("episode", "state")),
        Times(
            lookahead,
            Minus(P0(model, "anchor_wx"), P0("episode", "state_wx")),
        ),
        Times(
            lookahead,
            Minus(P0(model, "anchor_wy"), P0("episode", "state_wy")),
        ),
        Div(
            Minus(P0(model, "anchor_vx"), P0("episode", "state_vx")),
            velocity_scale,
        ),
        Div(
            Minus(P0(model, "anchor_vy"), P0("episode", "state_vy")),
            velocity_scale,
        ),
        Div(
            Minus(P0(model, "anchor_vz"), P0("episode", "state_vz")),
            velocity_scale,
        ),
        Div(
            Minus(
                P0(model, "anchor_lateral_offset"),
                P0("episode", "lateral_offset"),
            ),
            P0("episode", "standing_reference_z"),
        ),
    )
    return Plus(*(Times(error, error) for error in errors))


def phase_trial_context_distance(model):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    errors = (
        Minus(P0(model, "anchor_z_x"), body_z_x("trial", "pre")),
        Minus(P0(model, "anchor_z_y"), body_z_y("trial", "pre")),
        Times(
            lookahead,
            Minus(P0(model, "anchor_wx"), P0("trial", "pre_wx")),
        ),
        Times(
            lookahead,
            Minus(P0(model, "anchor_wy"), P0("trial", "pre_wy")),
        ),
        Div(
            Minus(P0(model, "anchor_vx"), P0("trial", "pre_vx")),
            velocity_scale,
        ),
        Div(
            Minus(P0(model, "anchor_vy"), P0("trial", "pre_vy")),
            velocity_scale,
        ),
        Div(
            Minus(P0(model, "anchor_vz"), P0("trial", "pre_vz")),
            velocity_scale,
        ),
        Div(
            Minus(
                P0(model, "anchor_lateral_offset"),
                P0("trial", "pre_lateral_offset"),
            ),
            P0("episode", "standing_reference_z"),
        ),
    )
    return Plus(*(Times(error, error) for error in errors))


def phase_receipt_radius_energy():
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    changes = (
        Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        Times(
            lookahead,
            Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx")),
        ),
        Times(
            lookahead,
            Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy")),
        ),
        Div(
            Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx")),
            velocity_scale,
        ),
        Div(
            Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy")),
            velocity_scale,
        ),
        Div(
            Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz")),
            velocity_scale,
        ),
    )
    return Plus(*(Times(change, change) for change in changes))


def qualitative_sign(value):
    """Integer sign used for receipt-backed prediction contradiction."""
    return If(
        Gt(value, L(0)),
        L(1),
        If(Lt(value, L(0)), L(-1), L(0)),
    )


def predicted_directed_sign():
    return qualitative_sign(Times(
        A("episode", "heading_x"),
        A("trial", "predicted_dvx"),
    ))


def observed_directed_sign():
    # The interface quantizes displacement relative to the currently requested
    # heading.  Its sign is categorical evidence; cognition adds no float
    # tolerance or elapsed-time expiry.
    return qualitative_sign(PI0("outcome", "development_directed_units"))


def phase_prediction_authoritative(model):
    # Missing authority fields belong to pre-migration initialized models and
    # remain usable until a receipt explicitly contradicts them.  A model with
    # an invalidation receipt must be re-grounded before selection can recur.
    return Or(
        Eq(PI0(model, "prediction_authority"), L(1)),
        And(
            Eq(PI0(model, "prediction_authority"), L(0)),
            Eq(PI0(model, "prediction_invalidation_count"), L(0)),
        ),
    )


def nearest_phase_context(candidate):
    peers = Filter(
        PHASE_MODELS,
        "context_peer",
        And(
            Eq(
                A("context_peer", "token"),
                A(candidate, "token"),
            ),
            Eq(
                P0("context_peer", "support_phase"),
                P0(candidate, "support_phase"),
            ),
            Gt(P0("context_peer", "initialized"), L(0.5)),
            phase_prediction_authoritative("context_peer"),
        ),
    )
    exact_peers = Filter(
        peers,
        "shape_peer",
        Eq(
            A("shape_peer", "configuration_shape"),
            A("episode", "state_motor_configuration_shape"),
        ),
    )
    eligible_peers = Filter(
        peers,
        "eligible_peer",
        Or(
            Eq(
                A("eligible_peer", "configuration_shape"),
                A("episode", "state_motor_configuration_shape"),
            ),
            Eq(Count(exact_peers), L(0.0)),
        ),
    )
    return Argmin(
        eligible_peers,
        "context_peer",
        phase_context_distance("context_peer"),
        V(candidate),
    )


MODELS = Neighbours("episode", "has_humanoid_action_model")
PROBES = Filter(
    MODELS,
    "candidate",
    Lt(P0("candidate", "tonic_default"), L(0.5)),
)
UNSAMPLED = Filter(
    PROBES,
    "candidate",
    Lt(P0("candidate", "experience_count"), P0("policy", "babble_samples")),
)
LEARNED = Filter(
    PROBES,
    "candidate",
    Gt(P0("candidate", "experience_count"), L(0.5)),
)
TONIC = Filter(
    MODELS,
    "candidate",
    Gt(P0("candidate", "tonic_default"), L(0.5)),
)
PHASE_MODELS = Neighbours(
    "episode",
    "has_humanoid_phase_action_model",
)
LOCAL_PHASE_MODELS = Filter(
    PHASE_MODELS,
    "active_phase_model",
    And(
        Eq(
            P0("active_phase_model", "support_phase"),
            P0("episode", "current_support_phase"),
        ),
        Gt(P0("active_phase_model", "initialized"), L(0.5)),
        phase_prediction_authoritative("active_phase_model"),
        Eq(
            P0("active_phase_model", "context_id"),
            N0(
                nearest_phase_context("active_phase_model"),
                "context_id",
            ),
        ),
    ),
)
NONSTAGNANT_PHASE_MODELS = Filter(
    LOCAL_PHASE_MODELS,
    "nonstagnant_phase_model",
    Or(
        Gt(P0("episode", "last_directed_step"), L(0.0)),
        Not(Eq(
            A("nonstagnant_phase_model", "token"),
            A("episode", "last_locomotor_token"),
        )),
    ),
)
ACTIVE_PHASE_MODELS = Filter(
    LOCAL_PHASE_MODELS,
    "active_phase_model",
    Or(
        Gt(P0("episode", "last_directed_step"), L(0.0)),
        Not(Eq(
            A("active_phase_model", "token"),
            A("episode", "last_locomotor_token"),
        )),
        Eq(Count(NONSTAGNANT_PHASE_MODELS), L(0.0)),
    ),
)
SYNERGIES = Neighbours("episode", "has_humanoid_synergy_model")
PROBEABLE_SYNERGIES = Filter(
    SYNERGIES,
    "candidate",
    And(
        Gt(P0("candidate", "initialized"), L(0.5)),
        Eq(P0("candidate", "probed"), L(0.0)),
    ),
)
APPROVED_SYNERGIES = Filter(
    SYNERGIES,
    "candidate",
    Gt(P0("candidate", "approved"), L(0.5)),
)
PROBED_SYNERGIES = Filter(
    SYNERGIES,
    "candidate",
    Gt(P0("candidate", "probed"), L(0.5)),
)
GET_UP_MODELS = Neighbours("episode", "has_humanoid_get_up_action_model")
UNTRIED_GET_UP_MODELS = Filter(
    GET_UP_MODELS,
    "get_up_candidate",
    Eq(P0("get_up_candidate", "experience_count"), L(0.0)),
)
RECOVERY_BASINS = Neighbours(
    "episode",
    "has_humanoid_recovery_basin",
)
CURRENT_RECOVERY_BASINS = Neighbours(
    "episode",
    "has_current_humanoid_recovery_basin",
)
ACTIVE_RECOVERY_PROGRAMS = Neighbours(
    "episode",
    "has_active_humanoid_recovery_program",
)
SELECTED_RECOVERY_PRIMARIES = Neighbours(
    "episode",
    "has_selected_humanoid_recovery_primary",
)
SITUATED_LOCOMOTION_CONTEXTS = Neighbours(
    "episode",
    "has_current_humanoid_situated_locomotion_context",
)

BODY_SHAPES = Neighbours("agent", "has_humanoid_body_shape_library")


def situated_locomotion_context_active():
    """Whether deliberate locomotion currently owns its postural reference."""
    return Gt(Count(SITUATED_LOCOMOTION_CONTEXTS), L(0))


def intentional_situated_locomotion_requested():
    """Graph-held intent which owns a safe non-canonical future path.

    Locomotion is one such path, but supported developmental exploration also
    deliberately visits low and non-upright configurations.  Protective
    support changes the viable manifold; it must therefore suppress canonical
    pose recovery while structural interrupt authority remains intact.
    """
    return And(
        Eq(A("episode", "phase"), L("locomotion")),
        Eq(PI0("episode", "evaluation_active"), L(1)),
        Eq(PI0("episode", "developmental_curriculum_active"), L(1)),
        Not(Eq(A("episode", "developmental_goal"), L("inactive"))),
        Or(
            Eq(PI0("episode", "locomotion_drive_active"), L(1)),
            Eq(PI0(
                "episode", "caregiver_protective_support_available"
            ), L(1)),
        ),
    )


def contextual_posture_cost(z_x, z_y):
    """Canonical upright cost has no authority over an owned trajectory."""
    return If(
        situated_locomotion_context_active(),
        L(0),
        Plus(Times(z_x, z_x), Times(z_y, z_y)),
    )


def receipt_material_viability_breach(outcome="outcome"):
    """Structural power and heat limits a task context cannot waive."""
    power_limit = And(
        Gt(P0("episode", "state_maximum_power_watts"), L(0)),
        Gt(
            P0(outcome, "peak_power_watts"),
            P0("episode", "state_maximum_power_watts"),
        ),
    )
    thermal_limit = And(
        Gt(P0("episode", "state_thermal_capacity_joules"), L(0)),
        Gt(
            P0(outcome, "thermal_load_joules"),
            P0("episode", "state_thermal_capacity_joules"),
        ),
    )
    return Or(
        Eq(PI0("episode", "sensorimotor_interrupt_required"), L(1)),
        Eq(PI0("episode", "reset_requested"), L(1)),
        Eq(PI0(outcome, "sensorimotor_interrupt_required"), L(1)),
        Eq(PI0(outcome, "reset_requested"), L(1)),
        power_limit,
        thermal_limit,
    )


SYNERGY_EFFECT_KEYS = (
    "mean_dzx",
    "mean_dzy",
    "mean_dwx",
    "mean_dwy",
    "mean_dvx",
    "mean_dvy",
    "mean_dvz",
)

CONSOLIDATED_MOTOR_PRIOR_FIELDS = (
    "experience_count",
    "mean_prediction_error_energy",
    "mean_lateral_prediction_error_energy",
    "mean_directed_advance",
    "mean_input_energy_joules",
    "support_loss_ema",
    "support_deficit_ema",
    "response_frames",
    "recall_count",
    "consolidation_count",
    "mean_dzx",
    "mean_dzy",
    "mean_dwx",
    "mean_dwy",
    "mean_dvx",
    "mean_dvy",
    "mean_dvz",
    "mean_rate_dzx",
    "mean_rate_dzy",
    "mean_rate_dwx",
    "mean_rate_dwy",
    "mean_rate_dvx",
    "mean_rate_dvy",
    "mean_rate_dvz",
)


def body_shape_decode(candidate, field):
    return {
        "type": "ShapeDecode",
        "goal": A("episode", "body_shape_signature"),
        "codebook_type": "HumanoidBodyShapeSignature",
        "codebook_scope": SetT(A(candidate, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def exact_body_shape_candidates():
    """Held body shapes that exactly cover the current mechanical signature."""

    return Filter(
        BODY_SHAPES,
        "body_shape_candidate",
        And(
            Eq(
                Count(body_shape_decode("body_shape_candidate", "residual")),
                L(0.0),
            ),
            Eq(
                body_shape_decode("body_shape_candidate", "covered_count"),
                Count(A("episode", "body_shape_signature")),
            ),
            Eq(
                A("body_shape_candidate", "physics_time_step"),
                A("episode", "physics_time_step"),
            ),
            Eq(
                A("body_shape_candidate", "gravity_acceleration"),
                A("episode", "gravity_acceleration"),
            ),
            Eq(
                A("body_shape_candidate", "joint_twitch_radians"),
                A("episode", "joint_twitch_radians"),
            ),
            Eq(
                A("body_shape_candidate", "maximum_joint_force"),
                A("episode", "maximum_joint_force"),
            ),
            Eq(
                A("body_shape_candidate", "position_gain"),
                A("episode", "position_gain"),
            ),
            Eq(
                A("body_shape_candidate", "velocity_gain"),
                A("episode", "velocity_gain"),
            ),
        ),
    )


def audit_held_body_shape_rule():
    dynamics_match = And(*[
        Eq(A("shape", field), A("episode", field))
        for field in (
            "physics_time_step",
            "gravity_acceleration",
            "joint_twitch_radians",
            "maximum_joint_force",
            "position_gain",
            "velocity_gain",
        )
    ])
    return {
        "name": "ha_audit_held_body_shape_recognition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -1,
        "batch": False,
        "comment": "Publish the exact shape-math recognition coordinates as output-null diagnostics before warm-start selection.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_body_shape_library", "shape"],
        ],
        "where": And(
            Eq(P0("episode", "body_shape_initialized"), L(0)),
            Eq(A("shape", "name"), A("episode", "body_shape_name")),
            Eq(P0("episode", "body_shape_audit_complete"), L(0)),
        ),
        "effects": [
            ["set_attr", "episode", "body_shape_audit_residual_count", T(
                Count(body_shape_decode("shape", "residual"))
            )],
            ["set_attr", "episode", "body_shape_audit_covered_count", T(
                body_shape_decode("shape", "covered_count")
            )],
            ["set_attr", "episode", "body_shape_audit_signature_count", T(
                Count(A("episode", "body_shape_signature"))
            )],
            ["set_attr", "episode", "body_shape_audit_dynamics_match", T(If(
                dynamics_match, L(1), L(0)
            ))],
            ["set_attr", "episode", "body_shape_audit_complete", 1],
        ],
    }


def recognize_body_shape_rule():
    return {
        "name": "ha_recognize_held_body_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Warm-start compatibility is ordinary exact-cover "
        "ShapeDecode over a name-free kinematic relation system. Controller "
        "dynamics are separately exact so a morphology match cannot silently "
        "authorize a program learned under different actuation.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_body_shape_library", "shape"],
        ],
        "where": And(
            Eq(P0("episode", "body_shape_initialized"), L(0.0)),
            Exists(
                exact_body_shape_candidates(),
                "exact_shape",
                Eq(V("exact_shape"), V("shape")),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "recognizes_humanoid_body_shape",
                "shape",
            ],
            ["set_attr", "episode", "body_shape_initialized", 1.0],
            ["set_attr", "episode", "warm_start_shape_recognized", 1.0],
        ],
    }


def recognize_late_restored_body_shape_rule():
    already_recognized = Exists(
        Neighbours("episode", "recognizes_humanoid_body_shape"),
        "recognized_shape",
        Eq(V("recognized_shape"), V("shape")),
    )
    is_exact = Exists(
        exact_body_shape_candidates(),
        "exact_shape",
        Eq(V("exact_shape"), V("shape")),
    )
    return {
        "name": "ha_recognize_late_restored_body_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Assimilate an exact shape library that arrived after body ingest. The late memory remains output-null; this only opens normal member rebinding and local verification.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_body_shape_library", "shape"],
        ],
        "where": And(
            Eq(P0("episode", "body_shape_initialized"), L(1)),
            Eq(A("shape", "source"), L("library")),
            Gt(Count(Neighbours(
                "shape", "stores_humanoid_motor_program"
            )), L(0)),
            Not(already_recognized),
            is_exact,
        ),
        "effects": [
            ["add_edge", "episode", "recognizes_humanoid_body_shape", "shape"],
            ["set_attr", "episode", "warm_start_shape_recognized", 1],
            ["set_attr", "episode", "late_shape_library_recognition_count", T(
                Plus(P0("episode", "late_shape_library_recognition_count"), L(1))
            )],
        ],
    }


def mint_body_shape_rule():
    return {
        "name": "ha_mint_novel_body_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "If no held morphology exactly covers the sensed relation "
        "system, mint that residual as a new body-shape codebook entry. The "
        "name is only a mechanical identity; novelty is decided by ShapeDecode.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "body_shape_initialized"), L(0.0)),
            Eq(Count(exact_body_shape_candidates()), L(0.0)),
        ),
        "effects": [
            ["add_node", "shape", "HumanoidBodyShapeSignature", {
                "name": T(A("episode", "body_shape_name")),
                "signature": T(A("episode", "body_shape_signature")),
                "physics_time_step": T(
                    A("episode", "physics_time_step")
                ),
                "gravity_acceleration": T(
                    A("episode", "gravity_acceleration")
                ),
                "joint_twitch_radians": T(
                    A("episode", "joint_twitch_radians")
                ),
                "maximum_joint_force": T(
                    A("episode", "maximum_joint_force")
                ),
                "position_gain": T(A("episode", "position_gain")),
                "velocity_gain": T(A("episode", "velocity_gain")),
                "source": "experience",
            }],
            [
                "add_edge",
                "agent",
                "has_humanoid_body_shape_library",
                "shape",
            ],
            [
                "add_edge",
                "episode",
                "recognizes_humanoid_body_shape",
                "shape",
            ],
            ["set_attr", "episode", "body_shape_initialized", 1.0],
            ["set_attr", "episode", "warm_start_shape_recognized", 0.0],
        ],
    }


def exact_motor_program_shape(program, candidate, field):
    return {
        "type": "ShapeDecode",
        "goal": If(
            Eq(A(program, "signature"), L(None)),
            L([]),
            A(program, "signature"),
        ),
        "codebook_type": "HumanoidMotorProgram",
        "codebook_scope": SetT(If(
            Eq(A(candidate, "name"), L(None)),
            L("__missing_motor_program_shape_name__"),
            A(candidate, "name"),
        )),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def library_motor_programs(shape="shape"):
    return Filter(
        Neighbours(shape, "stores_humanoid_motor_program"),
        "library_program",
        Eq(A("library_program", "status"), L("library")),
    )


def duplicate_library_program_candidates(program="program", shape="shape"):
    return Filter(
        Neighbours(shape, "stores_humanoid_motor_program"),
        "duplicate_candidate",
        And(
            Not(Eq(V(program), V("duplicate_candidate"))),
            Not(Eq(A("duplicate_candidate", "name"), L(None))),
            Not(Eq(A("duplicate_candidate", "signature"), L(None))),
            Eq(A("duplicate_candidate", "status"), L("library")),
            Lt(
                P0("duplicate_candidate", "library_slot"),
                P0(program, "library_slot"),
            ),
            Eq(Count(exact_motor_program_shape(
                program, "duplicate_candidate", "residual"
            )), L(0.0)),
            Eq(
                exact_motor_program_shape(
                    program, "duplicate_candidate", "covered_count"
                ),
                Count(A(program, "signature")),
            ),
        ),
    )


def open_library_program_shape_audit_rule():
    return {
        "name": "ha_open_changed_library_motor_program_shape_audit",
        "area": "embodied_sensorimotor",
        "latency_class": "hard_realtime",
        "order": -2,
        "batch": True,
        "comment": "Enter ShapeDecode only when the imported program "
        "population changed since this program's last deduplication audit.",
        "match": [["shape", "stores_humanoid_motor_program", "program"]],
        "where": And(
            Eq(A("program", "status"), L("library")),
            Not(Eq(A("program", "name"), L(None))),
            Not(Eq(A("program", "signature"), L(None))),
            Not(Eq(
                P0("program", "library_shape_audit_population"),
                Count(library_motor_programs()),
            )),
            Eq(Count(Filter(
                Neighbours("shape", "has_pending_library_program_shape_audit"),
                "pending_program",
                Eq(V("pending_program"), V("program")),
            )), L(0)),
        ),
        "effects": [[
            "add_edge", "shape",
            "has_pending_library_program_shape_audit", "program",
        ]],
    }


def recognize_duplicate_library_program_shape_rule():
    """Collapse imported duplicates with the engine's shape mathematics."""
    return {
        "name": "ha_shape_decode_duplicate_library_motor_program",
        "area": "embodied_sensorimotor",
        "latency_class": "hard_realtime",
        "order": -1,
        "batch": False,
        "comment": "Treat motor programs as relation systems. ShapeDecode, "
        "not host tuple comparison, recognizes an imported program already "
        "covered by an earlier codebook entry under the same body shape.",
        "match": [
            ["shape", "has_pending_library_program_shape_audit", "program"],
            ["shape", "stores_humanoid_motor_program", "canonical"],
        ],
        "where": And(
            Not(Eq(V("program"), V("canonical"))),
            Not(Eq(A("program", "name"), L(None))),
            Not(Eq(A("canonical", "name"), L(None))),
            Not(Eq(A("program", "signature"), L(None))),
            Not(Eq(A("canonical", "signature"), L(None))),
            Eq(A("program", "status"), L("library")),
            Eq(A("canonical", "status"), L("library")),
            Lt(
                P0("canonical", "library_slot"),
                P0("program", "library_slot"),
            ),
            Eq(
                Count(exact_motor_program_shape(
                    "program", "canonical", "residual"
                )),
                L(0.0),
            ),
            Eq(
                exact_motor_program_shape(
                    "program", "canonical", "covered_count"
                ),
                Count(A("program", "signature")),
            ),
        ),
        "effects": [
            ["set_attr", "program", "status", "shape_duplicate"],
            ["set_attr", "program", "shape_duplicate", 1.0],
            [
                "del_edge", "shape",
                "stores_humanoid_motor_program", "program",
            ],
            [
                "add_edge", "shape",
                "stores_duplicate_humanoid_motor_program", "program",
            ],
            [
                "add_edge", "program",
                "is_shape_duplicate_of_humanoid_program", "canonical",
            ],
            [
                "del_edge", "shape",
                "has_pending_library_program_shape_audit", "program",
            ],
        ],
    }


def close_unique_library_program_shape_audit_rule():
    return {
        "name": "ha_close_unique_library_motor_program_shape_audit",
        "area": "embodied_sensorimotor",
        "latency_class": "hard_realtime",
        "order": 0,
        "batch": True,
        "comment": "A zero-residual duplicate search is stable until the "
        "library population changes; retain that negative shape evidence.",
        "match": [
            ["shape", "has_pending_library_program_shape_audit", "program"],
            ["shape", "stores_humanoid_motor_program", "program"],
        ],
        "where": Eq(
            Count(duplicate_library_program_candidates()), L(0)
        ),
        "effects": [
            ["set_attr", "program", "library_shape_audit_population", T(
                Count(library_motor_programs())
            )],
            [
                "del_edge", "shape",
                "has_pending_library_program_shape_audit", "program",
            ],
        ],
    }


def motor_plan_hint_decode(hint, field):
    return {
        "type": "ShapeDecode",
        "goal": A("episode", "motor_plan_query_signature"),
        "codebook_type": "EmbodiedMotorPlanHint",
        "codebook_scope": SetT(A(hint, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def select_motor_plan_task_context_rule():
    desired_context = If(
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        L("self_takeoff"),
        L("locomotion"),
    )
    desired_signature = If(
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        A("episode", "motor_plan_self_takeoff_query_signature"),
        A("episode", "motor_plan_locomotion_query_signature"),
    )
    return {
        "name": "ha_select_active_motor_plan_task_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -50,
        "comment": "The graph changes its plan-search question with the "
        "active drive. This recruits takeoff priors only during self-authored "
        "takeoff and restores locomotion priors when that drive closes.",
        "match": [["agent", "has_humanoid_episode", "episode"]],
        "where": And(
            Not(Eq(
                A("episode", "motor_plan_active_query_context"),
                desired_context,
            )),
            Not(Eq(
                A("episode", "motor_plan_locomotion_query_signature"),
                L(None),
            )),
            Not(Eq(
                A("episode", "motor_plan_self_takeoff_query_signature"),
                L(None),
            )),
        ),
        "effects": [
            [
                "set_attr", "episode", "motor_plan_active_query_context",
                T(desired_context),
            ],
            [
                "set_attr", "episode", "motor_plan_query_signature",
                T(desired_signature),
            ],
        ],
    }


def consider_motor_plan_hint_rule():
    """Install a matched long plan as an order-0 basin, without cognition."""
    considered = Neighbours("episode", "considers_humanoid_motor_plan_hint")
    already_considered = Exists(
        considered,
        "considered_hint",
        Eq(V("considered_hint"), V("hint")),
    )
    return {
        "name": "ha_consider_shape_matched_motor_plan_hint",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A plan hint is an output-null relation system. Exact "
        "task-shape coverage makes it a cheap default search basin. It does "
        "not itself recruit System 2: typed residual/surprise boundaries own "
        "that escalation. The hint never selects a token, enacts a program, "
        "or marks an action ready.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_embodied_motor_plan_hint_library", "hint"],
        ],
        "where": And(
            Eq(PI0("hint", "output_authority"), L(0)),
            Not(already_considered),
            Eq(Count(motor_plan_hint_decode("hint", "residual")), L(0)),
            Eq(
                motor_plan_hint_decode("hint", "covered_count"),
                Count(A("episode", "motor_plan_query_signature")),
            ),
        ),
        "effects": [
            ["add_edge", "episode", "considers_humanoid_motor_plan_hint", "hint"],
            ["set_attr", "episode", "motor_plan_hint_count", T(
                Plus(PI0("episode", "motor_plan_hint_count"), L(1))
            )],
        ],
    }


def exact_plan_hint_stage_shape(program, stage, field):
    return {
        "type": "ShapeDecode",
        "goal": A(program, "signature"),
        "codebook_type": "EmbodiedMotorPlanHintStage",
        "codebook_scope": SetT(A(stage, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def bind_motor_plan_hint_stage_basin_rule():
    """Associate an exact local chunk with a hinted stage as a search seed."""
    suggested = Neighbours(
        "stage", "suggests_humanoid_motor_program_basin"
    )
    already_suggested = Exists(
        suggested,
        "suggested_program",
        Eq(V("suggested_program"), V("program")),
    )
    return {
        "name": "ha_bind_motor_plan_hint_stage_search_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A harvested stage points System 2 to the exact local "
        "program ordinal from which it was derived. This indexed identity "
        "join is evidence about where to search, never actuator authority.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "considers_humanoid_motor_plan_hint", "hint"],
            ["hint", "has_embodied_motor_plan_hint_stage", "stage"],
            ["episode", "has_humanoid_motor_program", "program"],
            [
                "program", "realizes_embodied_motor_routing_shape",
                "routing_shape",
            ],
        ],
        "where": And(
            Eq(PI0("hint", "output_authority"), L(0)),
            Eq(PI0("stage", "output_authority"), L(0)),
            Eq(
                PI0("stage", "requires_observed_consequence_shape"),
                L(0),
            ),
            Eq(A("program", "status"), L("grounded")),
            Not(Eq(A("stage", "source_program_ordinal"), L(None))),
            Not(already_suggested),
            Eq(
                PI0("stage", "source_program_ordinal"),
                PI0("program", "ordinal"),
            ),
        ),
        "effects": [
            [
                "add_edge", "stage",
                "suggests_humanoid_motor_program_basin", "program",
            ],
            [
                "add_edge", "episode",
                "has_humanoid_motor_program_basin_seed", "program",
            ],
            ["set_attr", "episode", "motor_plan_basin_seed_count", T(
                Plus(PI0("episode", "motor_plan_basin_seed_count"), L(1))
            )],
        ],
    }


def routed_plan_hint_stage_shape(stage, program, field):
    return {
        "type": "ShapeDecode",
        "goal": If(
            Eq(A(stage, "routing_signature"), L(None)),
            L([]),
            A(stage, "routing_signature"),
        ),
        "codebook_type": "HumanoidMotorProgram",
        "codebook_scope": SetT(If(
            Eq(A(program, "name"), L(None)),
            L("__missing_routed_motor_program_name__"),
            A(program, "name"),
        )),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def bind_abstract_plan_hint_stage_basin_rule():
    """Route conceptual stages through a shared task/phase shape alphabet."""
    suggested = Neighbours(
        "stage", "suggests_humanoid_motor_program_basin"
    )
    already_suggested = Exists(
        suggested,
        "suggested_program",
        Eq(V("suggested_program"), V("program")),
    )
    return {
        "name": "ha_route_abstract_motor_plan_hint_stage_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "background",
        "batch": False,
        "comment": "Biological and robotics priors share only task-context "
        "and task-phase relations with body-local programs. Their canonical "
        "routing-shape index joins abstract stages to improving search "
        "basins; exact tokens and actuator authority remain local and "
        "receipt-gated.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "considers_humanoid_motor_plan_hint", "hint"],
            ["hint", "has_embodied_motor_plan_hint_stage", "stage"],
            ["episode", "has_humanoid_motor_program", "program"],
            [
                "program", "realizes_embodied_motor_routing_shape",
                "routing_shape",
            ],
        ],
        "where": And(
            Eq(PI0("hint", "output_authority"), L(0)),
            Eq(PI0("stage", "output_authority"), L(0)),
            Eq(
                PI0("stage", "requires_observed_consequence_shape"),
                L(0),
            ),
            Eq(A("program", "status"), L("grounded")),
            Not(Eq(A("stage", "motor_task_context"), L(None))),
            Not(Eq(A("stage", "motor_task_phase"), L(None))),
            Not(already_suggested),
            Eq(
                A("stage", "motor_task_context"),
                A("routing_shape", "motor_task_context"),
            ),
            Eq(
                A("stage", "motor_task_phase"),
                A("routing_shape", "motor_task_phase"),
            ),
        ),
        "effects": [
            [
                "add_edge", "stage",
                "suggests_humanoid_motor_program_basin", "program",
            ],
            [
                "add_edge", "episode",
                "has_humanoid_motor_program_basin_seed", "program",
            ],
            ["set_attr", "episode", "motor_plan_basin_seed_count", T(
                Plus(PI0("episode", "motor_plan_basin_seed_count"), L(1))
            )],
        ],
    }


def classify_grounded_program_routing_shape_rule():
    """Index a grounded local program once by its task/phase shape."""
    return {
        "name": "ha_classify_grounded_program_routing_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A receipt-grounded program enters the shared routing "
        "index by exact equality of its task-context and task-phase relations. "
        "The routing node is already the canonical decoded shape: decoding "
        "again through non-unique situated program names would add ambiguity "
        "and quadratic work without adding evidence. The small relation "
        "alphabet avoids the hint-stage by learned-program Cartesian scan "
        "while preserving exact body-local identity.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_embodied_motor_routing_shape", "shape"],
            ["episode", "has_humanoid_motor_program", "program"],
        ],
        "where": And(
            Eq(A("program", "status"), L("grounded")),
            Not(Eq(A("program", "name"), L(None))),
            Not(Eq(A("program", "signature"), L(None))),
            Eq(
                Count(Neighbours(
                    "program", "realizes_embodied_motor_routing_shape"
                )),
                L(0),
            ),
            Eq(
                A("shape", "motor_task_context"),
                A("program", "motor_task_context"),
            ),
            Eq(
                A("shape", "motor_task_phase"),
                A("program", "motor_task_phase"),
            ),
        ),
        "effects": [
            [
                "add_edge", "program",
                "realizes_embodied_motor_routing_shape", "shape",
            ],
            [
                "add_edge", "episode",
                "has_unrouted_grounded_humanoid_motor_program", "program",
            ],
        ],
    }


def request_grounded_program_routing_rule():
    """Run the expensive hint decoder once when a new program can use it."""
    return {
        "name": "ha_request_grounded_program_routing",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A newly indexed grounded program recruits only the "
        "plan-hint routing sheet. The quadratic shape decoders therefore run "
        "at a relevant graph event, never on unrelated motor receipts.",
        "match": [
            [
                "agent", "has_humanoid_motor_plan_hint_routing_task_set",
                "routing_tasks",
            ],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode", "has_unrouted_grounded_humanoid_motor_program",
                "program",
            ],
            [
                "program", "realizes_embodied_motor_routing_shape",
                "routing_shape",
            ],
        ],
        "where": And(
            Eq(A("program", "status"), L("grounded")),
            Eq(P0("program", "motor_plan_hint_routing_requested"), L(0.0)),
            Gt(Count(Neighbours(
                "episode", "considers_humanoid_motor_plan_hint"
            )), L(0)),
        ),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "new_grounded_motor_program_hint_routing",
                "epoch": T(P0("episode", "state_seq")),
                "provenance_kind": "graph_authored_plan_hint_routing",
            }],
            ["add_edge", "escalation", "about_context", "program"],
            [
                "add_edge", "escalation", "recruits_task_set",
                "routing_tasks",
            ],
            [
                "set_attr", "program",
                "motor_plan_hint_routing_requested", 1.0,
            ],
            [
                "del_edge", "episode",
                "has_unrouted_grounded_humanoid_motor_program", "program",
            ],
            ["set_attr", "episode", "motor_plan_hint_escalation_count", T(
                Plus(
                    P0("episode", "motor_plan_hint_escalation_count"),
                    L(1.0),
                )
            )],
        ],
    }


def classify_grounded_program_consequence_shape_rule():
    """Index a receipt-grounded program by categorical situated consequence."""
    return {
        "name": "ha_classify_grounded_program_consequence_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A grounded program joins the observed-motion consequence "
        "alphabet by exact integer/string relation equality. Continuous plant "
        "measurements remain at the interface; the index holds only their "
        "categorical receipt.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "agent", "has_embodied_motor_consequence_routing_shape",
                "shape",
            ],
            ["episode", "has_humanoid_motor_program", "program"],
        ],
        "where": And(
            Eq(A("program", "status"), L("grounded")),
            Not(Eq(
                A("program", "observed_height_energy_relation"),
                L(None),
            )),
            Eq(
                Count(Neighbours(
                    "program", "realizes_embodied_motor_consequence_shape"
                )),
                L(0),
            ),
            Eq(
                A("shape", "motor_task_context"),
                A("program", "motor_task_context"),
            ),
            Eq(
                A("shape", "motor_task_phase"),
                A("program", "motor_task_phase"),
            ),
            Eq(
                A("shape", "height_energy_relation"),
                A("program", "observed_height_energy_relation"),
            ),
        ),
        "effects": [[
            "add_edge", "program",
            "realizes_embodied_motor_consequence_shape", "shape",
        ]],
    }


def bind_indexed_bootstrap_stage_basin_rule():
    """Expose each indexed local program as an output-null basin once."""
    basin_programs = Neighbours(
        "episode", "has_humanoid_motor_program_search_index"
    )
    already_seeded = Exists(
        basin_programs,
        "seeded_program",
        Eq(V("seeded_program"), V("program")),
    )
    return {
        "name": "ha_bind_indexed_bootstrap_stage_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A shared routing-shape node indexes each grounded local "
        "program once. General hints remain topology/search evidence; only a "
        "currently matching observed consequence transition becomes an active "
        "composer basin. The edge grants no actuator authority.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "program", "realizes_embodied_motor_routing_shape",
                "shape",
            ],
            ["episode", "has_humanoid_motor_program", "program"],
        ],
        "where": And(
            Eq(A("program", "status"), L("grounded")),
            Not(already_seeded),
        ),
        "effects": [
            [
                "add_edge", "shape",
                "suggests_humanoid_motor_program_basin", "program",
            ],
            [
                "add_edge", "episode",
                "has_humanoid_motor_program_search_index", "program",
            ],
            ["set_attr", "episode", "motor_plan_search_index_count", T(
                Plus(PI0("episode", "motor_plan_search_index_count"), L(1))
            )],
        ],
    }


def bind_warm_program_member_rule():
    return {
        "name": "ha_bind_warm_motor_program_member",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Bind each serialized opaque member fact back onto the "
        "current body's phase-conditioned actuator model by graph equality. "
        "The loader restores facts only; it never maps or selects actuators.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["shape", "stores_humanoid_motor_program", "program"],
            ["program", "has_humanoid_library_motor_member", "member"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_model",
            ],
        ],
        "where": And(
            Eq(A("program", "status"), L("library")),
            Eq(A("member", "token"), A("phase_model", "token")),
            Eq(
                P0("member", "support_phase"),
                P0("phase_model", "support_phase"),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "program",
                "includes_humanoid_phase_action_model",
                "phase_model",
            ],
        ],
    }


def activate_warm_program_rule():
    current_programs = Neighbours("episode", "has_humanoid_motor_program")
    stored_programs = Neighbours("shape", "stores_humanoid_motor_program")
    verified_trajectory_endpoint = And(
        Eq(A("program", "motor_task_context"), L("self_takeoff")),
        Eq(P0("program", "trajectory_verified"), L(1.0)),
    )
    already_active = Exists(
        current_programs,
        "current_program",
        Or(
            Eq(V("current_program"), V("program")),
            And(
                verified_trajectory_endpoint,
                Eq(
                    A("current_program", "motor_task_context"),
                    L("self_takeoff"),
                ),
                Eq(P0("current_program", "trajectory_verified"), L(1.0)),
                Eq(
                    P0("current_program", "jump_schema_id"),
                    P0("program", "jump_schema_id"),
                ),
                Eq(
                    P0("current_program", "ordinal"),
                    P0("program", "ordinal"),
                ),
            ),
        ),
    )
    schema_equivalent_programs = Filter(
        stored_programs,
        "schema_program",
        And(
            Eq(A("schema_program", "motor_task_context"), L("self_takeoff")),
            Eq(P0("schema_program", "trajectory_verified"), L(1.0)),
            Eq(
                P0("schema_program", "jump_schema_id"),
                P0("program", "jump_schema_id"),
            ),
            Eq(
                P0("schema_program", "ordinal"),
                P0("program", "ordinal"),
            ),
        ),
    )
    canonical_schema_program = Argmin(
        schema_equivalent_programs,
        "schema_program",
        P0("schema_program", "library_slot"),
        V("program"),
    )
    return {
        "name": "ha_activate_shape_matched_motor_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A restored program becomes an active prior only after "
        "ShapeDecode recognized its body and every opaque member rebound to "
        "the present actuator graph. Shape memory retains coordinated "
        "population programs rather than body-local singleton habits. A "
        "singleton endpoint is admitted only when a recovered whole trajectory "
        "verified it. It remains output-null until the normal motor gate "
        "releases it.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["shape", "stores_humanoid_motor_program", "program"],
        ],
        "where": And(
            Eq(A("program", "status"), L("library")),
            Eq(P0("program", "memory_eligible"), L(1.0)),
            Or(
                Gt(P0("program", "member_count"), L(1.0)),
                verified_trajectory_endpoint,
            ),
            Or(
                Not(verified_trajectory_endpoint),
                Eq(V("program"), canonical_schema_program),
            ),
            Eq(
                Count(Neighbours(
                    "program",
                    "includes_humanoid_phase_action_model",
                )),
                P0("program", "member_count"),
            ),
            Not(already_active),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "has_humanoid_motor_program",
                "program",
            ],
            ["set_attr", "program", "status", "grounded"],
            ["set_attr", "program", "source", "shape_warm_start"],
            [
                "set_attr",
                "program",
                "warm_start_requires_verification",
                1.0,
            ],
            ["set_attr", "program", "warm_start_verified", 0.0],
            ["set_attr", "program", "lifetime_recall_count", 0.0],
            ["set_attr", "program", "last_memory_update_request_seq", 0.0],
            ["set_attr", "program", "last_recall_request_seq", 0.0],
            ["set_attr", "program", "library_consolidation_seq", 0.0],
            *[
                [
                    "set_attr",
                    "program",
                    f"consolidated_{field}",
                    T(P0("program", field)),
                ]
                for field in CONSOLIDATED_MOTOR_PRIOR_FIELDS
            ],
            ["set_attr", "episode", "warm_start_program_count", T(
                Plus(P0("episode", "warm_start_program_count"), L(1.0))
            )],
        ],
    }


def bind_warm_motor_transition_source_rule():
    candidates = Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "source_candidate",
        And(
            Eq(
                P0("source_candidate", "ordinal"),
                P0("transition", "from_program_ordinal"),
            ),
            Eq(
                A("source_candidate", "motor_task_context"),
                A("transition", "motor_task_context"),
            ),
            Eq(
                P0("source_candidate", "jump_schema_id"),
                P0("transition", "jump_schema_id"),
            ),
        ),
    )
    selected = Argmin(
        candidates, "source_candidate",
        P0("source_candidate", "member_count"), V("previous"),
    )
    return {
        "name": "ha_bind_shape_transition_source_endpoint",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Resolve one restored transition endpoint before the "
        "edge is activated, avoiding a repeated endpoint cross product.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["shape", "stores_humanoid_motor_transition", "transition"],
            ["episode", "has_humanoid_motor_program", "previous"],
        ],
        "where": And(
            Eq(A("transition", "status"), L("library")),
            Eq(P0("transition", "trajectory_verified"), L(1.0)),
            Eq(V("previous"), selected),
            Not(Exists(
                Neighbours("previous", "has_humanoid_motor_transition"),
                "known_transition",
                Eq(V("known_transition"), V("transition")),
            )),
        ),
        "effects": [[
            "add_edge", "previous", "has_humanoid_motor_transition", "transition",
        ]],
    }


def bind_warm_motor_transition_target_rule():
    candidates = Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "target_candidate",
        And(
            Eq(
                P0("target_candidate", "ordinal"),
                P0("transition", "next_program_ordinal"),
            ),
            Eq(
                A("target_candidate", "motor_task_context"),
                A("transition", "motor_task_context"),
            ),
            Eq(
                P0("target_candidate", "jump_schema_id"),
                P0("transition", "jump_schema_id"),
            ),
        ),
    )
    selected = Argmin(
        candidates, "target_candidate",
        P0("target_candidate", "member_count"), V("memory"),
    )
    return {
        "name": "ha_bind_shape_transition_target_endpoint",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["shape", "stores_humanoid_motor_transition", "transition"],
            ["episode", "has_humanoid_motor_program", "memory"],
        ],
        "where": And(
            Eq(A("transition", "status"), L("library")),
            Eq(P0("transition", "trajectory_verified"), L(1.0)),
            Eq(V("memory"), selected),
            Eq(Count(Neighbours(
                "transition", "continues_with_humanoid_motor_program"
            )), L(0)),
        ),
        "effects": [[
            "add_edge", "transition",
            "continues_with_humanoid_motor_program", "memory",
        ]],
    }


def activate_warm_motor_transition_rule():
    return {
        "name": "ha_activate_shape_matched_motor_transition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Restore a developmental edge only after shape decoding "
        "has rebound both endpoint programs to the current body.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["shape", "stores_humanoid_motor_transition", "transition"],
            ["previous", "has_humanoid_motor_transition", "transition"],
            ["transition", "continues_with_humanoid_motor_program", "memory"],
        ],
        "where": And(
            Eq(A("transition", "status"), L("library")),
            Eq(P0("transition", "trajectory_verified"), L(1.0)),
            Eq(
                P0("transition", "from_program_ordinal"),
                P0("previous", "ordinal"),
            ),
            Eq(
                P0("transition", "next_program_ordinal"),
                P0("memory", "ordinal"),
            ),
            Eq(
                A("previous", "motor_task_context"),
                A("transition", "motor_task_context"),
            ),
            Eq(
                A("memory", "motor_task_context"),
                A("transition", "motor_task_context"),
            ),
            Eq(
                P0("previous", "jump_schema_id"),
                P0("transition", "jump_schema_id"),
            ),
            Eq(
                P0("memory", "jump_schema_id"),
                P0("transition", "jump_schema_id"),
            ),
        ),
        "effects": [
            ["add_edge", "episode", "has_humanoid_motor_transition", "transition"],
            ["add_edge", "previous", "has_humanoid_motor_transition", "transition"],
            ["add_edge", "transition", "continues_with_humanoid_motor_program", "memory"],
            ["set_attr", "transition", "status", "grounded"],
            ["set_attr", "transition", "source", "shape_warm_start"],
        ],
    }


def partial_trajectory_program(program="program"):
    """A safe, retained intermediate that improved the projected future.

    It is not terminal capability success.  Its counterexample provenance is
    kept while the exact motor shape remains available to order-N planning.
    """
    return And(
        Eq(P0(program, "partial_trajectory_evidence"), L(1.0)),
        Gt(P0(program, "development_vertical_velocity_progress_sum_units"), L(0.0)),
        Gt(P0(program, "member_count"), L(1.0)),
        Eq(P0(program, "memory_eligible"), L(1.0)),
        Eq(P0(program, "receipt_learned"), L(1.0)),
    )


def store_program_by_body_shape_rule():
    stored = Neighbours("shape", "stores_humanoid_motor_program")
    whole_trajectory_candidate = And(
        Eq(A("program", "motor_task_context"), L("self_takeoff")),
        Eq(P0("program", "trajectory_verified"), L(1.0)),
    )
    partial_trajectory_candidate = partial_trajectory_program()
    is_stored = Exists(
        stored,
        "stored_program",
        Or(
            Eq(V("stored_program"), V("program")),
            And(
                whole_trajectory_candidate,
                Eq(
                    A("stored_program", "motor_task_context"),
                    L("self_takeoff"),
                ),
                Eq(P0("stored_program", "trajectory_verified"), L(1.0)),
                Eq(
                    P0("stored_program", "jump_schema_id"),
                    P0("program", "jump_schema_id"),
                ),
                Eq(
                    P0("stored_program", "ordinal"),
                    P0("program", "ordinal"),
                ),
            ),
        ),
    )
    boundary = Eq(
        P0("episode", "library_consolidation_requested"),
        L(1.0),
    )
    warm_repertoire_succeeded = And(
        Eq(P0("episode", "warm_start_shape_recognized"), L(1.0)),
        Not(Lt(
            P0("episode", "directed_progress"),
            P0("shape", "best_directed_progress"),
        )),
        Not(Lt(
            P0("episode", "walking_minimum_height"),
            Times(
                P0("policy", "minimum_upright_height_fraction"),
                P0("episode", "standing_reference_z"),
            ),
        )),
    )
    initial_candidate = And(
        Eq(P0("program", "memory_eligible"), L(1.0)),
            Or(
                whole_trajectory_candidate,
                partial_trajectory_candidate,
                And(
                Gt(P0("program", "mean_directed_advance"), L(0.0)),
                Lt(
                    motor_model_uncertainty("program"),
                    Div(
                        P0("program", "mean_directed_advance"),
                        P0("episode", "standing_reference_z"),
                    ),
                ),
            ),
        ),
        Eq(P0("program", "receipt_learned"), L(1.0)),
        Or(
            Eq(
                P0("episode", "warm_start_shape_recognized"),
                L(0.0),
            ),
            Eq(
                P0("program", "warm_start_requires_verification"),
                L(1.0),
            ),
            whole_trajectory_candidate,
            partial_trajectory_candidate,
        ),
        Not(is_stored),
    )
    boundary_candidate = And(
        boundary,
        is_stored,
        Lt(
            P0("program", "library_consolidation_seq"),
            P0("episode", "library_consolidation_seq"),
        ),
        Or(
            Eq(P0("program", "memory_eligible"), L(1.0)),
            warm_repertoire_succeeded,
        ),
    )
    return {
        "name": "ha_store_grounded_program_by_body_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Mint confidence-qualified coordinated programs into the "
        "body-shape codebook. At a lifetime boundary select the transferred "
        "programs as a repertoire: if their whole embodied trajectory matches "
        "or beats the shape's held best, restore individually inhibited chunks "
        "from the slow prior. Singleton habits remain lifetime-local.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["episode", "has_humanoid_motor_program", "program"],
        ],
        "where": And(
            Or(
                Eq(A("program", "status"), L("grounded")),
                And(
                    Eq(A("program", "status"), L("counterexample_observed")),
                    partial_trajectory_candidate,
                ),
            ),
            Or(
                Gt(P0("program", "member_count"), L(1.0)),
                whole_trajectory_candidate,
            ),
            Or(initial_candidate, boundary_candidate),
        ),
        "effects": [
            [
                "add_edge",
                "shape",
                "stores_humanoid_motor_program",
                "program",
            ],
            ["set_attr", "program", "shape_indexed", 1.0],
            ["set_attr", "program", "memory_eligible", T(If(
                And(boundary, warm_repertoire_succeeded),
                L(1.0),
                P0("program", "memory_eligible"),
            ))],
            ["set_attr", "shape", "best_directed_progress", T(If(
                boundary,
                Max(
                    P0("shape", "best_directed_progress"),
                    P0("episode", "directed_progress"),
                ),
                P0("shape", "best_directed_progress"),
            ))],
            *[
                [
                    "set_attr",
                    "program",
                    field,
                    T(If(
                        boundary,
                        If(
                            Eq(
                                P0(
                                    "episode",
                                    "warm_start_shape_recognized",
                                ),
                                L(1.0),
                            ),
                            P0(
                                "program",
                                f"consolidated_{field}",
                            ),
                            P0("program", field),
                        ),
                        P0("program", field),
                    )),
                ]
                for field in CONSOLIDATED_MOTOR_PRIOR_FIELDS
            ],
            [
                "set_attr",
                "program",
                "warm_start_requires_verification",
                T(If(
                    boundary,
                    L(1.0),
                    P0(
                        "program",
                        "warm_start_requires_verification",
                    ),
                )),
            ],
            ["set_attr", "program", "warm_start_verified", T(If(
                boundary,
                L(0.0),
                P0("program", "warm_start_verified"),
            ))],
            [
                "set_attr",
                "program",
                "last_memory_update_request_seq",
                T(P0("program", "last_memory_update_request_seq")),
            ],
            ["set_attr", "program", "last_recall_request_seq", T(
                P0("program", "last_recall_request_seq")
            )],
            ["set_attr", "program", "library_consolidation_seq", T(If(
                boundary,
                P0("episode", "library_consolidation_seq"),
                P0("program", "library_consolidation_seq"),
            ))],
        ],
    }


def request_motor_library_consolidation_rule():
    """Recruit the slow library sheet from graph-visible memory events."""
    stored = Neighbours("shape", "stores_humanoid_motor_program")
    is_stored = Exists(
        stored,
        "stored_program",
        Eq(V("stored_program"), V("program")),
    )
    initial_candidate = And(
        Or(
            Eq(A("program", "status"), L("grounded")),
            And(
                Eq(A("program", "status"), L("counterexample_observed")),
                partial_trajectory_program(),
            ),
        ),
        Eq(P0("program", "memory_eligible"), L(1.0)),
        Eq(P0("program", "receipt_learned"), L(1.0)),
        Or(
            Gt(P0("program", "member_count"), L(1.0)),
            And(
                Eq(A("program", "motor_task_context"), L("self_takeoff")),
                Eq(P0("program", "trajectory_verified"), L(1.0)),
            ),
            partial_trajectory_program(),
        ),
        Or(
            Not(Eq(A("episode", "phase"), L("locomotion"))),
            Eq(A("program", "motor_task_context"), L("self_takeoff")),
        ),
        Not(is_stored),
        Eq(P0("program", "library_escalation_requested"), L(0.0)),
    )
    boundary_candidate = And(
        Eq(P0("episode", "library_consolidation_requested"), L(1.0)),
        is_stored,
        Lt(
            P0("program", "last_library_escalation_seq"),
            P0("episode", "library_consolidation_seq"),
        ),
    )
    return {
        "name": "ha_request_motor_library_consolidation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A newly grounded coordinated program outside active "
        "locomotion, or an explicit lifetime boundary, recruits the shared "
        "integration task set. Active movement leaves programs in working "
        "motor memory so offline shape-library consolidation cannot lengthen "
        "the control loop. The slow sheet still decides whether and how the "
        "program enters the library; the host supplies no retention policy.",
        "match": [
            [
                "agent",
                "has_embodied_integration_task_set",
                "integration_tasks",
            ],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["episode", "has_humanoid_motor_program", "program"],
        ],
        "where": Or(initial_candidate, boundary_candidate),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "humanoid_motor_library_consolidation",
                "epoch": T(P0("episode", "library_consolidation_seq")),
                "provenance_kind": "graph_authored_motor_consolidation",
            }],
            [
                "add_edge",
                "program",
                "has_system_two_escalation",
                "escalation",
            ],
            ["add_edge", "escalation", "about_context", "program"],
            [
                "add_edge",
                "escalation",
                "recruits_task_set",
                "integration_tasks",
            ],
            ["set_attr", "program", "library_escalation_requested", 1.0],
            ["set_attr", "program", "last_library_escalation_seq", T(
                P0("episode", "library_consolidation_seq")
            )],
        ],
    }


def store_verified_motor_transition_by_body_shape_rule():
    stored = Neighbours("shape", "stores_humanoid_motor_transition")
    return {
        "name": "ha_store_verified_motor_transition_by_body_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Persist only whole-trajectory-verified developmental "
        "edges whose endpoint chunks already belong to the same body shape.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["shape", "stores_humanoid_motor_program", "previous"],
            ["shape", "stores_humanoid_motor_program", "memory"],
            ["previous", "has_humanoid_motor_transition", "transition"],
            ["transition", "continues_with_humanoid_motor_program", "memory"],
        ],
        "where": And(
            Eq(P0("transition", "trajectory_verified"), L(1.0)),
            Not(Exists(
                stored,
                "stored_transition",
                Eq(V("stored_transition"), V("transition")),
            )),
        ),
        "effects": [
            ["add_edge", "shape", "stores_humanoid_motor_transition", "transition"],
            ["set_attr", "transition", "shape_indexed", 1.0],
        ],
    }


def withdraw_unsafe_program_from_shape_rule():
    whole_trajectory_candidate = And(
        Eq(A("program", "motor_task_context"), L("self_takeoff")),
        Eq(P0("program", "trajectory_verified"), L(1.0)),
    )
    partial_trajectory_candidate = partial_trajectory_program()
    return {
        "name": "ha_withdraw_unsafe_program_from_body_shape_library",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Reject invalid structure immediately. An unsafe held "
        "compound is inhibited for the current lifetime but remains attached "
        "to its repertoire until boundary-level embodied selection decides "
        "whether the jointly expressed set improved the shape's trajectory.",
        "match": [
            ["agent", "has_humanoid_body_shape_library", "shape"],
            ["shape", "stores_humanoid_motor_program", "program"],
        ],
        "where": And(
            Not(Or(
                whole_trajectory_candidate,
                partial_trajectory_candidate,
            )),
            Or(
                Not(Gt(P0("program", "member_count"), L(1.0))),
                And(
                    Or(
                        Eq(P0("program", "memory_eligible"), L(0.0)),
                        Not(Gt(
                            P0("program", "mean_directed_advance"),
                            L(0.0),
                        )),
                    ),
                    Not(Eq(
                        P0(
                            "program",
                            "warm_start_requires_verification",
                        ),
                        L(1.0),
                    )),
                ),
            ),
        ),
        "effects": [
            [
                "del_edge",
                "shape",
                "stores_humanoid_motor_program",
                "program",
            ],
            ["set_attr", "program", "shape_indexed", 0.0],
        ],
    }


def initialize_response_horizon_rule():
    actuator_root = IDiv(Sqrt(Count(MODELS)), L(1.0))
    actuator_dimension = If(
        Lt(Times(actuator_root, actuator_root), Count(MODELS)),
        Plus(actuator_root, L(1.0)),
        actuator_root,
    )
    gravity_horizon_frames = Div(
        Sqrt(Div(
            P0("episode", "standing_reference_z"),
            P0("policy", "gravity_acceleration"),
        )),
        P0("episode", "physics_time_step"),
    )
    body_scaled_horizon = Max(
        L(1.0),
        IDiv(gravity_horizon_frames, actuator_dimension),
    )
    initial_horizon = If(
        Gt(P0("episode", "control_integration_frames"), L(0.0)),
        Min(
            body_scaled_horizon,
            P0("episode", "control_integration_frames"),
        ),
        body_scaled_horizon,
    )
    return {
        "name": "ha_initialize_body_scaled_response_horizon",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Derive the initial motor horizon from the body's measured "
        "gravity-fall time, physics clock, and discovered actuator "
        "dimensionality; no host command-rate constant participates.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "response_horizon_initialized"), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
            Gt(P0("episode", "standing_reference_z"), L(0.0)),
            Gt(P0("episode", "physics_time_step"), L(0.0)),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "nominal_response_frames",
                T(initial_horizon),
            ],
            [
                "set_attr",
                "episode",
                "response_frames",
                T(initial_horizon),
            ],
            ["set_attr", "episode", "response_horizon_initialized", 1.0],
            [
                "set_attr",
                "episode",
                "compound_response_interval",
                T(P0(
                    "policy",
                    "gait_surprise_confirmation_receipts",
                )),
            ],
        ],
    }


def focus_topology_sensitive_response_horizon_rule():
    actuator_root = IDiv(Sqrt(Count(MODELS)), L(1.0))
    actuator_dimension = If(
        Lt(Times(actuator_root, actuator_root), Count(MODELS)),
        Plus(actuator_root, L(1.0)),
        actuator_root,
    )
    focused_frames = Max(
        L(1.0),
        IDiv(
            P0("trial", "response_frames"),
            Max(L(1.0), actuator_dimension),
        ),
    )
    prediction_scale = Div(
        focused_frames,
        P0("trial", "response_frames"),
    )
    return {
        "name": "ha_focus_topology_sensitive_response_horizon",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 100,
        "comment": "Supported ballistic tasks focus proprioceptive sampling "
        "by the discovered actuator dimensionality. The graph preserves the "
        "selected action and scales its predicted consequence to the shorter "
        "hold, allowing contact loss and momentum sign changes to be observed "
        "before a new synthesis. One physics receipt is the irreducible floor, "
        "not a controller-rate constant.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
        ],
        "where": And(
            Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
            Eq(A("trial", "motor_task_context"), L("self_takeoff")),
            Gt(P0("episode", "active_support_count"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(1.0)),
            Eq(A("trial", "status"), L("issued")),
            Eq(
                P0("trial", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Gt(P0("trial", "response_frames"), focused_frames),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    T(Times(
                        P0("episode", f"selected_predicted_{key}"),
                        prediction_scale,
                    )),
                ]
                for key in (
                    "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                )
            ],
            [
                "set_attr", "episode", "selected_response_frames",
                T(focused_frames),
            ],
            *[
                [
                    "set_attr",
                    "trial",
                    f"predicted_{key}",
                    T(Times(
                        P0("trial", f"predicted_{key}"),
                        prediction_scale,
                    )),
                ]
                for key in (
                    "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                )
            ],
            [
                "set_attr", "trial", "response_frames", T(focused_frames),
            ],
            [
                "set_attr", "episode", "topology_focused_response_count",
                T(Plus(
                    P0("episode", "topology_focused_response_count"),
                    L(1.0),
                )),
            ],
        ],
    }


def motor_selection_effects(best, decision_kind, response_frames=None):
    if response_frames is None:
        response_frames = P0("episode", "response_frames")
    return [
        ["set_attr", "episode", "selected_token", T(AO(best, "token"))],
        [
            "set_attr",
            "episode",
            "selected_secondary_token",
            T(AO(best, "token")),
        ],
        [
            "set_attr",
            "episode",
            "selected_response_frames",
            T(response_frames),
        ],
        ["set_attr", "episode", "selected_predicted_dvx", 0.0],
        ["set_attr", "episode", "selected_predicted_dvy", 0.0],
        ["set_attr", "episode", "selected_predicted_dvz", 0.0],
        ["set_attr", "episode", "decision_kind", decision_kind],
        ["set_attr", "episode", "action_ready", 1.0],
        ["set_attr", "episode", "decision_seq", T(
            P0("episode", "request_seq")
        )],
        ["set_attr", "episode", "decision_count", T(
            Plus(P0("episode", "decision_count"), L(1.0))
        )],
    ]


def choose_babble_rule():
    best = Argmin(
        UNSAMPLED,
        "candidate",
        P0("candidate", "ordinal"),
        V("episode"),
    )
    return {
        "name": "ha_choose_opaque_joint_babble",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Systematically twitch each opaque non-tonic actuator.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("calibration")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                Count(Neighbours(
                    "episode",
                    "has_current_humanoid_motor_fixation",
                )),
                L(0.0),
            ),
            Gt(Count(UNSAMPLED), L(0.0)),
        ),
        "effects": motor_selection_effects(best, "motor_babble"),
    }


def correction_cost(candidate):
    lookahead = Sqrt(
        Div(
            P0("episode", "standing_reference_z"),
            P0("policy", "gravity_acceleration"),
        )
    )
    predicted_z_x = Plus(
        body_z_x("episode", "state"),
        N0(candidate, "mean_dzx"),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wy"),
                N0(candidate, "mean_dwy"),
            ),
        ),
    )
    predicted_z_y = Minus(
        Plus(
            body_z_y("episode", "state"),
            N0(candidate, "mean_dzy"),
        ),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wx"),
                N0(candidate, "mean_dwx"),
            ),
        ),
    )
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    downward_velocity = Min(
        L(0.0),
        Plus(
            P0("episode", "state_vz"),
            N0(candidate, "mean_dvz"),
        ),
    )
    normalized_downward_velocity = Div(
        downward_velocity,
        velocity_scale,
    )
    return If(
        situated_locomotion_context_active(),
        L(0),
        Plus(
            Times(predicted_z_x, predicted_z_x),
            Times(predicted_z_y, predicted_z_y),
            Times(
                normalized_downward_velocity,
                normalized_downward_velocity,
            ),
        ),
    )


def choose_balance_rule():
    best = Argmin(
        LEARNED,
        "candidate",
        correction_cost("candidate"),
        V("episode"),
    )
    return {
        "name": "ha_choose_learned_balance_twitch",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Project measured angular velocity over the body's "
        "gravity-derived fall timescale and choose the learned opaque twitch "
        "with minimum predicted body-axis departure.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("recovery")),
            Eq(A("episode", "mode"), L("adaptive_graph")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(Count(LEARNED), L(0.0)),
        ),
        "effects": motor_selection_effects(
            best,
            "learned_balance",
            Max(
                L(1.0),
                IDiv(
                    P0("episode", "response_frames"),
                    P0("policy", "gait_surprise_confirmation_receipts"),
                ),
            ),
        ),
    }


def initialize_synergy_model_rule():
    return {
        "name": "ha_initialize_compound_synergy_prior",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Initialize a compatible pair with the explicit additive "
        "prediction of its two independently receipt-learned parents.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_synergy_model", "synergy"],
            ["synergy", "has_humanoid_synergy_primary", "primary"],
            ["synergy", "has_humanoid_synergy_secondary", "secondary"],
        ],
        "where": And(
            Eq(P0("synergy", "initialized"), L(0.0)),
            Gt(P0("primary", "experience_count"), L(0.5)),
            Gt(P0("secondary", "experience_count"), L(0.5)),
        ),
        "effects": [
            [
                "set_attr",
                "synergy",
                f"predicted_{key[5:]}",
                T(Plus(P0("primary", key), P0("secondary", key))),
            ]
            for key in SYNERGY_EFFECT_KEYS
        ] + [
            ["set_attr", "synergy", "support_loss_ema", T(
                Div(
                    Plus(
                        P0("primary", "support_loss_ema"),
                        P0("secondary", "support_loss_ema"),
                    ),
                    L(2.0),
                )
            )],
            ["set_attr", "synergy", "support_deficit_ema", T(
                Div(
                    Plus(
                        P0("primary", "support_deficit_ema"),
                        P0("secondary", "support_deficit_ema"),
                    ),
                    L(2.0),
                )
            )],
            ["set_attr", "synergy", "mean_input_energy_joules", T(
                Plus(
                    P0("primary", "mean_input_energy_joules"),
                    P0("secondary", "mean_input_energy_joules"),
                )
            )],
            ["set_attr", "synergy", "initialized", 1.0],
        ],
    }


def synergy_effect_magnitude(candidate, prefix):
    return Plus(*[
        Times(
            N0(candidate, f"{prefix}_{key[5:]}"),
            N0(candidate, f"{prefix}_{key[5:]}"),
        )
        for key in SYNERGY_EFFECT_KEYS
    ])


def choose_synergy_probe_rule():
    anchored = Filter(
        PROBEABLE_SYNERGIES,
        "candidate",
        Or(
            Eq(
                P0("candidate", "ordinal_a"),
                P0("episode", "synergy_probe_anchor_ordinal"),
            ),
            Eq(
                P0("candidate", "ordinal_b"),
                P0("episode", "synergy_probe_anchor_ordinal"),
            ),
        ),
    )
    best = Argmin(
        anchored,
        "candidate",
        synergy_effect_magnitude("candidate", "predicted"),
        V("episode"),
    )
    probe_frames = Max(
        L(1.0),
        IDiv(P0("episode", "response_frames"), L(2.0)),
    )
    horizon_scale = Div(
        probe_frames,
        P0("episode", "response_frames"),
    )
    return {
        "name": "ha_choose_staged_synergy_probe",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "From a reset posture, probe the untested compatible pair "
        "with the smallest predicted additive body effect at a contracted "
        "horizon.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("synergy_calibration")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "synergy_calibration_complete"), L(0.0)),
            Gt(Count(anchored), L(0.0)),
            Lt(
                Count(PROBED_SYNERGIES),
                P0("policy", "synergy_probe_budget"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                AO(best, "token_a")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(best, "token_b")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                probe_frames
            )],
            ["set_attr", "episode", "selected_predicted_dvx", T(
                Times(horizon_scale, AO(best, "predicted_dvx"))
            )],
            ["set_attr", "episode", "selected_predicted_dvy", T(
                Times(horizon_scale, AO(best, "predicted_dvy"))
            )],
            ["set_attr", "episode", "selected_predicted_dvz", T(
                Times(horizon_scale, AO(best, "predicted_dvz"))
            )],
            ["set_attr", "episode", "decision_kind", "synergy_probe"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def link_synergy_trial_rule():
    linked = Neighbours("trial", "uses_humanoid_synergy_model")
    return {
        "name": "ha_link_compound_trial_to_synergy_model",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Link only the live issued trial.  The token index binds "
        "its exact first-member synergy before the second member is verified, "
        "so retained motor history cannot turn this into a trial-by-synergy "
        "Cartesian scan.",
        "index_hints": [{
            "for_var": "synergy",
            "via_var": "trial",
            "via_key": "token",
            "node_type": "HumanoidSynergyModel",
            "this_key": "token_a",
        }],
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["episode", "has_humanoid_synergy_model", "synergy"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Not(Eq(A("trial", "token"), A("trial", "secondary_token"))),
            Eq(A("trial", "token"), A("synergy", "token_a")),
            Eq(
                A("trial", "secondary_token"),
                A("synergy", "token_b"),
            ),
            Eq(Count(linked), L(0.0)),
        ),
        "effects": [[
            "add_edge",
            "trial",
            "uses_humanoid_synergy_model",
            "synergy",
        ]],
    }


def learn_synergy_probe_rule():
    horizon_scale = Div(
        P0("trial", "response_frames"),
        P0("episode", "response_frames"),
    )
    observed = {
        "dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "dwx": Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx")),
        "dwy": Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy")),
        "dvx": Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx")),
        "dvy": Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy")),
        "dvz": Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz")),
    }
    residuals = {
        key: Minus(
            value,
            Times(
                horizon_scale,
                P0("synergy", f"predicted_{key}"),
            ),
        )
        for key, value in observed.items()
    }
    residual_magnitude = Sqrt(Plus(*[
        Times(value, value) for value in residuals.values()
    ]))
    post_tilt = Sqrt(Plus(
        Times(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "post"),
        ),
        Times(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "post"),
        ),
    ))
    support_preserved = Or(
        Not(Or(
            Gt(P0("outcome", "pre_support_0_force"), L(0.0)),
            Gt(P0("outcome", "pre_support_1_force"), L(0.0)),
        )),
        Gt(P0("outcome", "post_support_0_force"), L(0.0)),
        Gt(P0("outcome", "post_support_1_force"), L(0.0)),
    )
    safe = And(
        Not(Gt(
            residual_magnitude,
            P0("episode", "single_action_effect_envelope"),
        )),
        Not(Gt(
            post_tilt,
            P0("episode", "single_action_tilt_envelope"),
        )),
        Gt(
            P0("outcome", "post_z"),
            Times(
                P0("policy", "minimum_upright_height_fraction"),
                P0("episode", "standing_reference_z"),
            ),
        ),
    )
    return {
        "name": "ha_learn_compound_interaction_residual",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Credit the reset-isolated compound receipt to its exact "
        "pair, store observed non-additive residuals, and approve only pairs "
        "inside the single-action safety envelope.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_synergy_model", "synergy"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("synergy_probe")),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
            Eq(P0("synergy", "probed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "synergy", f"mean_{key}", T(value)]
            for key, value in observed.items()
        ] + [
            ["set_attr", "synergy", f"residual_{key}", T(value)]
            for key, value in residuals.items()
        ] + [
            ["set_attr", "synergy", "residual_magnitude", T(
                residual_magnitude
            )],
            ["set_attr", "synergy", "probed", 1.0],
            ["set_attr", "synergy", "experience_count", 1.0],
            ["set_attr", "synergy", "support_loss_ema", T(If(
                support_preserved,
                L(0.0),
                L(1.0),
            ))],
            ["set_attr", "synergy", "support_deficit_ema", T(
                support_deficit_observation()
            )],
            [
                "set_attr",
                "synergy",
                "mean_input_energy_joules",
                T(P0("outcome", "input_energy_joules")),
            ],
            ["set_attr", "synergy", "approved", T(
                If(safe, L(1.0), L(0.0))
            )],
            ["set_attr", "synergy", "rejected", T(
                If(safe, L(0.0), L(1.0))
            )],
            [
                "set_attr",
                "episode",
                "synergy_probe_anchor_ordinal",
                T(Plus(
                    P0("episode", "synergy_probe_anchor_ordinal"),
                    L(1.0),
                )),
            ],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "synergy_learned"],
        ],
    }


def close_synergy_calibration_rule():
    return {
        "name": "ha_close_staged_synergy_calibration",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("synergy_calibration")),
            Eq(P0("episode", "synergy_calibration_complete"), L(0.0)),
            Not(Lt(
                Count(PROBED_SYNERGIES),
                P0("policy", "synergy_probe_budget"),
            )),
        ),
        "effects": [
            ["set_attr", "episode", "synergy_calibration_complete", 1.0],
        ],
    }


def support_center(axis):
    """Contact-conditioned support centroid from graph-mirrored foot geometry."""
    support_0 = Gt(P0("episode", "state_support_0_force"), L(0.0))
    support_1 = Gt(P0("episode", "state_support_1_force"), L(0.0))
    midpoint = Div(
        Plus(
            P0("episode", f"state_support_0_{axis}"),
            P0("episode", f"state_support_1_{axis}"),
        ),
        L(2.0),
    )
    return If(
        And(support_0, support_1),
        midpoint,
        If(
            support_0,
            P0("episode", f"state_support_0_{axis}"),
            If(
                support_1,
                P0("episode", f"state_support_1_{axis}"),
                midpoint,
            ),
        ),
    )


def residual_regimes():
    return Neighbours("policy", "has_humanoid_residual_regime")


def core_curiosity_score():
    """Evaluate decision_core's graph-held action score for candidate ``c``."""
    return EvalSubgraph(Pick(Neighbours("agent", "action_score_term")))


def curiosity_candidates():
    return Filter(
        residual_regimes(),
        "c",
        Gt(core_curiosity_score(), L(0.0)),
    )


def gait_attractors():
    return Neighbours("policy", "has_humanoid_gait_attractor")


RESIDUAL_REGIME_MEMORY_FIELDS = (
    "sample_count",
    "selection_count",
    "completed_windows",
    "mean_directed_step",
    "mean_abs_lateral_step",
    "mean_tilt",
    "mean_height_deficit",
    "mean_support_deficit",
    "mean_normalized_energy",
    "mean_aerial_occupancy",
    "mean_double_support_occupancy",
    "fast_prediction_residual",
    "slow_prediction_residual",
    "learning_progress",
    "q",
    "asym_count",
    "novelty",
    "unsafe_receipt_count",
)


def matching_residual_regime_memories():
    return Filter(
        Neighbours("shape", "stores_humanoid_residual_regime_memory"),
        "known_memory",
        Eq(
            P0("known_memory", "ordinal"),
            P0("regime", "ordinal"),
        ),
    )


def restore_shape_residual_regime_memory_rule():
    return {
        "name": "ha_restore_shape_indexed_residual_regime_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Restore the graph's completed gait/regime sweep for the "
        "recognized body shape so a new lifetime continues the curriculum "
        "instead of repeatedly relearning the first walking regimes.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["policy", "has_humanoid_residual_regime", "regime"],
            [
                "shape",
                "stores_humanoid_residual_regime_memory",
                "memory",
            ],
        ],
        "where": And(
            Eq(P0("memory", "ordinal"), P0("regime", "ordinal")),
            Eq(P0("regime", "sample_count"), L(0.0)),
            Gt(P0("memory", "sample_count"), L(0.0)),
        ),
        "effects": [
            *[
                ["set_attr", "regime", field, T(P0("memory", field))]
                for field in RESIDUAL_REGIME_MEMORY_FIELDS
            ],
            ["set_attr", "regime", "restored_from_shape", 1.0],
        ],
    }


def mint_shape_residual_regime_memory_rule():
    memories = matching_residual_regime_memories()
    return {
        "name": "ha_mint_shape_indexed_residual_regime_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "At the explicit lifetime boundary retain explored gait "
        "hypotheses under the recognized body shape.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["policy", "has_humanoid_residual_regime", "regime"],
        ],
        "where": And(
            Eq(P0("episode", "library_consolidation_requested"), L(1.0)),
            Gt(P0("regime", "sample_count"), L(0.0)),
            Eq(Count(memories), L(0.0)),
        ),
        "effects": [
            ["add_node", "memory", "HumanoidResidualRegimeMemory", {
                "ordinal": T(P0("regime", "ordinal")),
                "gait_ordinal": T(P0("regime", "gait_ordinal")),
                **{
                    field: T(P0("regime", field))
                    for field in RESIDUAL_REGIME_MEMORY_FIELDS
                },
                "updated_in_lifetime": 1.0,
            }],
            [
                "add_edge",
                "shape",
                "stores_humanoid_residual_regime_memory",
                "memory",
            ],
        ],
    }


def update_shape_residual_regime_memory_rule():
    return {
        "name": "ha_update_shape_indexed_residual_regime_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Refresh one restored gait hypothesis after another "
        "receipt-grounded lifetime.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["policy", "has_humanoid_residual_regime", "regime"],
            [
                "shape",
                "stores_humanoid_residual_regime_memory",
                "memory",
            ],
        ],
        "where": And(
            Eq(P0("episode", "library_consolidation_requested"), L(1.0)),
            Eq(P0("memory", "ordinal"), P0("regime", "ordinal")),
            Eq(P0("memory", "updated_in_lifetime"), L(0.0)),
            Gt(P0("regime", "sample_count"), L(0.0)),
        ),
        "effects": [
            *[
                ["set_attr", "memory", field, T(P0("regime", field))]
                for field in RESIDUAL_REGIME_MEMORY_FIELDS
            ],
            ["set_attr", "memory", "updated_in_lifetime", 1.0],
        ],
    }


def active_gait_attractor():
    matching = Filter(
        gait_attractors(),
        "gait_candidate",
        Eq(
            P0("gait_candidate", "ordinal"),
            P0("episode", "active_gait_attractor_ordinal"),
        ),
    )
    return Argmin(
        matching,
        "gait_candidate",
        P0("gait_candidate", "ordinal"),
        V("policy"),
    )


def active_residual_regime():
    matching = Filter(
        residual_regimes(),
        "regime_candidate",
        Eq(
            P0("regime_candidate", "ordinal"),
            P0("episode", "active_residual_regime_ordinal"),
        ),
    )
    return Argmin(
        matching,
        "regime_candidate",
        P0("regime_candidate", "ordinal"),
        V("policy"),
    )


def trial_regime_eligibility_attrs():
    """Immutable action-time controller identity for later receipt credit."""
    return {
        "residual_regime_ordinal": T(
            P0("episode", "active_residual_regime_ordinal")
        ),
        "gait_attractor_ordinal": T(
            P0("episode", "active_gait_attractor_ordinal")
        ),
    }


def bind_initial_residual_regime_rule():
    selected = Argmin(
        residual_regimes(),
        "candidate",
        P0("candidate", "ordinal"),
        V("policy"),
    )
    active = Neighbours(
        "episode",
        "evaluates_humanoid_residual_regime",
    )
    return {
        "name": "ha_bind_initial_gait_residual_regime",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Begin the graph sweep at its least ordinal hypothesis. "
        "The explicit episode edge, not a mutable scalar, is authoritative.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["policy", "has_humanoid_residual_regime", "regime"],
        ],
        "where": And(
            Eq(Count(active), L(0.0)),
            Eq(P0("regime", "ordinal"), AO(selected, "ordinal")),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "evaluates_humanoid_residual_regime",
                "regime",
            ],
            ["set_attr", "episode", "active_gait_attractor_ordinal", T(
                P0("regime", "gait_ordinal")
            )],
            ["set_attr", "episode", "active_residual_regime_ordinal", T(
                P0("regime", "ordinal")
            )],
        ],
    }


def residual_regime_topology_error(regime):
    """Distance between observed contact occupancy and a gait hypothesis."""
    denominator = P0("policy", "gait_attractor_interval_count")
    return Plus(
        Abs(Minus(
            AO(regime, "mean_aerial_occupancy"),
            Div(AO(regime, "target_aerial_intervals"), denominator),
        )),
        Abs(Minus(
            AO(regime, "mean_double_support_occupancy"),
            Div(
                AO(regime, "target_double_support_intervals"),
                denominator,
            ),
        )),
    )


def residual_regime_realized_gait(regime):
    topology_tolerance = Div(
        L(2.0),
        P0("policy", "gait_attractor_interval_count"),
    )
    return And(
        Not(Gt(residual_regime_topology_error(regime), topology_tolerance)),
        Or(
            Eq(AO(regime, "target_aerial_intervals"), L(0.0)),
            Gt(AO(regime, "mean_aerial_occupancy"), L(0.0)),
        ),
    )


def contextual_regime_pose_coordinate(regime, key):
    """Neutralize canonical pose coordinates for an owned trajectory."""
    return If(
        situated_locomotion_context_active(),
        L(0),
        AO(regime, key),
    )


def residual_regime_dominated(candidate):
    alternatives = Filter(
        residual_regimes(),
        "alternative",
        And(
            Not(Lt(
                P0("alternative", "sample_count"),
                P0("policy", "support_phase_prior_strength"),
            )),
            residual_regime_realized_gait(V("alternative")),
            Not(Eq(V("alternative"), candidate)),
            Not(Lt(
                P0("alternative", "mean_directed_step"),
                AO(candidate, "mean_directed_step"),
            )),
            Not(Gt(
                P0("alternative", "mean_abs_lateral_step"),
                AO(candidate, "mean_abs_lateral_step"),
            )),
            Not(Gt(
                contextual_regime_pose_coordinate(
                    V("alternative"), "mean_tilt"
                ),
                contextual_regime_pose_coordinate(candidate, "mean_tilt"),
            )),
            Not(Gt(
                contextual_regime_pose_coordinate(
                    V("alternative"), "mean_height_deficit"
                ),
                contextual_regime_pose_coordinate(
                    candidate, "mean_height_deficit"
                ),
            )),
            Not(Gt(
                P0("alternative", "mean_support_deficit"),
                AO(candidate, "mean_support_deficit"),
            )),
            Not(Gt(
                P0("alternative", "mean_normalized_energy"),
                AO(candidate, "mean_normalized_energy"),
            )),
            Not(Gt(
                residual_regime_topology_error(V("alternative")),
                residual_regime_topology_error(candidate),
            )),
            Not(Gt(
                P0("alternative", "unsafe_receipt_count"),
                AO(candidate, "unsafe_receipt_count"),
            )),
            Or(
                Gt(
                    P0("alternative", "mean_directed_step"),
                    AO(candidate, "mean_directed_step"),
                ),
                Lt(
                    P0("alternative", "mean_abs_lateral_step"),
                    AO(candidate, "mean_abs_lateral_step"),
                ),
                Lt(
                    contextual_regime_pose_coordinate(
                        V("alternative"), "mean_tilt"
                    ),
                    contextual_regime_pose_coordinate(
                        candidate, "mean_tilt"
                    ),
                ),
                Lt(
                    contextual_regime_pose_coordinate(
                        V("alternative"), "mean_height_deficit"
                    ),
                    contextual_regime_pose_coordinate(
                        candidate, "mean_height_deficit"
                    ),
                ),
                Lt(
                    P0("alternative", "mean_support_deficit"),
                    AO(candidate, "mean_support_deficit"),
                ),
                Lt(
                    P0("alternative", "mean_normalized_energy"),
                    AO(candidate, "mean_normalized_energy"),
                ),
                Lt(
                    residual_regime_topology_error(V("alternative")),
                    residual_regime_topology_error(candidate),
                ),
                Lt(
                    P0("alternative", "unsafe_receipt_count"),
                    AO(candidate, "unsafe_receipt_count"),
                ),
            ),
        ),
    )
    return Gt(Count(alternatives), L(0.0))


def residual_regime_context_choice_key(regime):
    """Select one frontier dimension from current graph-held need.

    This is intentionally not a weighted utility. The current body/task state
    chooses a single objective; Argmin then compares candidates only along
    that coordinate of the already non-dominated frontier.
    """
    balance_urgent = And(
        Not(situated_locomotion_context_active()),
        Gt(
            P0("episode", "tilt_magnitude"),
            P0("episode", "learned_gait_tilt_envelope"),
        ),
    )
    path_urgent = Gt(
        Abs(P0("episode", "lateral_offset")),
        P0("policy", "maximum_lateral_drift_metres"),
    )
    task_open = Eq(P0("episode", "locomotion_drive_active"), L(1.0))
    return If(
        balance_urgent,
        contextual_regime_pose_coordinate(regime, "mean_tilt"),
        If(
            path_urgent,
            AO(regime, "mean_abs_lateral_step"),
            If(
                task_open,
                Neg(AO(regime, "mean_directed_step")),
                AO(regime, "mean_normalized_energy"),
            ),
        ),
    )


def locomotor_viability_gate():
    gait = active_gait_attractor()
    z_x = body_z_x("episode", "state")
    z_y = body_z_y("episode", "state")
    tilt = Sqrt(Plus(Times(z_x, z_x), Times(z_y, z_y)))
    # The optimizer may explore within the learned viability envelope, but it
    # cannot buy task progress by widening that hard reflex boundary.
    tilt_budget = Max(
        P0("policy", "target_froude_speed"),
        P0("episode", "learned_gait_tilt_envelope"),
    )
    tilt_gate = Min(
        L(1.0),
        Max(L(0.0), Minus(L(1.0), Div(tilt, tilt_budget))),
    )
    minimum_height = Times(
        P0("policy", "minimum_upright_height_fraction"),
        P0("episode", "standing_reference_z"),
    )
    height_gate = Min(
        L(1.0),
        Max(
            L(0.0),
            Div(
                Minus(P0("episode", "state_z"), minimum_height),
                Max(
                    L(0.001),
                    Minus(
                        P0("episode", "standing_reference_z"),
                        minimum_height,
                    ),
                ),
            ),
        ),
    )
    grounded = Or(
        Gt(P0("episode", "state_support_0_force"), L(0.0)),
        Gt(P0("episode", "state_support_1_force"), L(0.0)),
    )
    support_phase_authorized = Or(
        grounded,
        Gt(AO(gait, "flight_phase_authority"), L(0.5)),
    )
    available = And(
        support_phase_authorized,
        Eq(P0("episode", "recovery_mode"), L(0.0)),
        Eq(P0("episode", "locomotion_drive_active"), L(1.0)),
    )
    pose_gate = If(
        situated_locomotion_context_active(),
        L(1),
        Min(tilt_gate, height_gate),
    )
    return If(available, pose_gate, L(0.0))


def forward_task_cost(predicted_dvx, frames=None):
    """Keep locomotion residual open, or reproduce legacy velocity regulation."""
    if frames is None:
        frames = P0("episode", "response_frames")
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    target_velocity = Times(
        P0("episode", "heading_x"),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    predicted_velocity = Plus(
        P0("episode", "state_vx"),
        predicted_dvx,
    )
    instantaneous_error = Div(
        Minus(predicted_velocity, target_velocity),
        velocity_scale,
    )
    action_duration = Times(
        frames,
        P0("episode", "physics_time_step"),
    )
    predicted_directed_step = Times(
        P0("episode", "heading_x"),
        Plus(
            P0("episode", "state_vx"),
            Times(L(0.5), predicted_dvx),
        ),
        action_duration,
    )
    predicted_progress = Plus(
        P0("episode", "lifetime_completed_progress"),
        P0("episode", "directed_progress"),
        predicted_directed_step,
    )
    persistent_residual = Div(
        Max(
            L(0.0),
            Minus(
                P0("episode", "target_directed_progress_m"),
                predicted_progress,
            ),
        ),
        P0("episode", "standing_reference_z"),
    )
    return If(
        Gt(
            P0("policy", "persistent_task_residual_authority"),
            L(0.5),
        ),
        Times(
            Div(
                AO(
                    active_residual_regime(),
                    "residual_gain_numerator",
                ),
                P0("policy", "support_phase_prior_strength"),
            ),
            Plus(
                L(1.0),
                Div(
                    AO(
                        active_gait_attractor(),
                        "elastic_impulse_numerator",
                    ),
                    P0("policy", "support_phase_prior_strength"),
                ),
            ),
            locomotor_viability_gate(),
            persistent_residual,
            persistent_residual,
        ),
        Times(instantaneous_error, instantaneous_error),
    )


def takeoff_task_cost(predicted_dvz):
    """Open a vertical velocity residual only for an active takeoff task."""
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    target_velocity = Times(
        P0("episode", "self_takeoff_target_velocity_scale"),
        Div(
            velocity_scale,
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    normalized_error = Div(
        Minus(
            Plus(P0("episode", "state_vz"), predicted_dvz),
            target_velocity,
        ),
        velocity_scale,
    )
    return If(
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        Times(
            P0("policy", "support_phase_prior_strength"),
            normalized_error,
            normalized_error,
        ),
        L(0.0),
    )


def motor_task_context():
    return If(
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        L("self_takeoff"),
        L("locomotion"),
    )


def grounded_motor_program_name(program="plan"):
    """Graph-native mechanical identity; never a semantic body-part label."""
    return StringConcat(
        L("situated_motor_program:"),
        ToJsonString(A(program, "request_seq")),
    )


def grounded_motor_program_signature(program="plan", phase=None):
    """Build the minimal task/phase relation system used by ShapeDecode."""
    phase = motor_task_phase() if phase is None else phase
    return FromJsonString(StringConcat(
        L('[["motor_task_context",'),
        ToJsonString(A(program, "motor_task_context")),
        L('],["motor_task_phase",'),
        ToJsonString(phase),
        L("]]"),
    ))


def observed_height_energy_relation(outcome="outcome"):
    """Categorise a physical receipt without retaining a cognitive float."""
    height_change = Minus(
        PI0(outcome, "post_z"),
        PI0(outcome, "pre_z"),
    )
    return If(
        Gt(height_change, L(0)),
        L("increasing"),
        If(
            Lt(height_change, L(0)),
            L("decreasing"),
            L("held"),
        ),
    )


def motor_residual_context():
    return If(
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        L("self_takeoff"),
        If(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            L("recovery_locomotion"),
            L("locomotion"),
        ),
    )


def motor_task_phase(outcome="outcome"):
    pre_supported = Or(
        Gt(P0(outcome, "pre_support_0_force"), L(0.0)),
        Gt(P0(outcome, "pre_support_1_force"), L(0.0)),
    )
    post_supported = Or(
        Gt(P0(outcome, "post_support_0_force"), L(0.0)),
        Gt(P0(outcome, "post_support_1_force"), L(0.0)),
    )
    return If(
        And(pre_supported, post_supported),
        L("preparation"),
        If(
            And(pre_supported, Not(post_supported)),
            L("launch"),
            If(
                And(Not(pre_supported), Not(post_supported)),
                L("flight"),
                L("landing"),
            ),
        ),
    )


def support_preview_cost(predicted_dvx, predicted_dvy):
    """Preview the linear-inverted-pendulum capture point over support."""
    regime = active_residual_regime()
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    capture_x = Plus(
        P0("episode", "state_x"),
        Times(
            lookahead,
            Plus(P0("episode", "state_vx"), predicted_dvx),
        ),
    )
    capture_y = Plus(
        P0("episode", "state_y"),
        Times(
            lookahead,
            Plus(P0("episode", "state_vy"), predicted_dvy),
        ),
    )
    forward_margin = Times(
        Div(
            AO(regime, "viability_scale_numerator"),
            Times(
                P0("policy", "support_phase_prior_strength"),
                P0("episode", "support_sensor_count"),
            ),
        ),
        P0("episode", "standing_reference_z"),
    )
    lateral_margin = Plus(
        Times(
            Div(
                AO(regime, "viability_scale_numerator"),
                Times(
                    P0("policy", "support_phase_prior_strength"),
                    P0("policy", "support_phase_prior_strength"),
                ),
            ),
            P0("episode", "standing_reference_z"),
        ),
        Times(
            Div(L(1.0), P0("episode", "support_sensor_count")),
            Abs(Minus(
                P0("episode", "state_support_0_y"),
                P0("episode", "state_support_1_y"),
            )),
        ),
    )
    forward_excess = Max(
        L(0.0),
        Minus(Abs(Minus(capture_x, support_center("x"))), forward_margin),
    )
    lateral_excess = Max(
        L(0.0),
        Minus(Abs(Minus(capture_y, support_center("y"))), lateral_margin),
    )
    normalized_forward = Div(
        forward_excess,
        P0("episode", "standing_reference_z"),
    )
    normalized_lateral = Div(
        lateral_excess,
        P0("episode", "standing_reference_z"),
    )
    grounded = Or(
        Gt(P0("episode", "state_support_0_force"), L(0.0)),
        Gt(P0("episode", "state_support_1_force"), L(0.0)),
    )
    return Times(
        P0("policy", "support_geometry_preview_authority"),
        If(grounded, L(1.0), L(0.0)),
        Plus(
            Times(
                P0("episode", "support_sensor_count"),
                normalized_forward,
                normalized_forward,
            ),
            Times(
                P0("policy", "support_phase_prior_strength"),
                normalized_lateral,
                normalized_lateral,
            ),
        ),
    )


def support_preview_lateral_cost(predicted_dvy):
    regime = active_residual_regime()
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    capture_y = Plus(
        P0("episode", "state_y"),
        Times(
            lookahead,
            Plus(P0("episode", "state_vy"), predicted_dvy),
        ),
    )
    lateral_margin = Plus(
        Times(
            Div(
                AO(regime, "viability_scale_numerator"),
                Times(
                    P0("policy", "support_phase_prior_strength"),
                    P0("policy", "support_phase_prior_strength"),
                ),
            ),
            P0("episode", "standing_reference_z"),
        ),
        Times(
            Div(L(1.0), P0("episode", "support_sensor_count")),
            Abs(Minus(
                P0("episode", "state_support_0_y"),
                P0("episode", "state_support_1_y"),
            )),
        ),
    )
    excess = Max(
        L(0.0),
        Minus(
            Abs(Minus(capture_y, support_center("y"))),
            lateral_margin,
        ),
    )
    normalized = Div(excess, P0("episode", "standing_reference_z"))
    grounded = Or(
        Gt(P0("episode", "state_support_0_force"), L(0.0)),
        Gt(P0("episode", "state_support_1_force"), L(0.0)),
    )
    return If(
        grounded,
        Times(
            P0("policy", "support_geometry_preview_authority"),
            P0("policy", "support_phase_prior_strength"),
            normalized,
            normalized,
        ),
        L(0.0),
    )


def gait_support_loss_cost(candidate):
    """Price contact topology by the active gait; never label it a fault."""
    return Times(
        AO(active_gait_attractor(), "support_transition_cost_numerator"),
        N0(candidate, "support_loss_ema"),
    )


def foveated_program_exploration_value(candidate):
    """Value an exact singleton program over its projected outcome shape.

    Outcome coordinates are residual samples, not distinct action identities.
    Aggregate every shape leaf produced by the same singleton in the same
    entry context before granting authority; otherwise a single lucky child
    remains permanently optimistic while contrary sibling shapes accumulate.
    """
    development = Pick(Neighbours(
        "episode", "projects_embodied_development"
    ))
    candidate_token = (
        A(candidate, "token")
        if isinstance(candidate, str)
        else AO(candidate, "token")
    )
    leaves = Filter(
        {
            "type": "Neighbours",
            "node": development,
            "edge_type": "has_embodied_locomotor_phenotype",
            "any_type": False,
        },
        "exploration_leaf",
        And(
            Eq(A("exploration_leaf", "action_intent"), L("learned_walk")),
            Eq(
                A("exploration_leaf", "developmental_capability"),
                A("episode", "active_developmental_capability"),
            ),
            Eq(
                P0("exploration_leaf", "pre_orientation_class"),
                P0("episode", "state_gravity_relative_orientation_class"),
            ),
            Eq(
                P0("exploration_leaf", "pre_whole_body_support_count"),
                P0("episode", "active_support_count"),
            ),
            Eq(A("exploration_leaf", "primary_token"), candidate_token),
            # A primary option can establish this exact program without
            # guessing only when the observed program was the singleton.
            Eq(
                A("exploration_leaf", "secondary_token"),
                candidate_token,
            ),
            Exists(
                Neighbours(
                    "exploration_leaf",
                    "refines_locomotor_phenotype_family",
                ),
                "ambiguous_program_parent",
                Eq(
                    P0("ambiguous_program_parent", "refinement_required"),
                    L(1),
                ),
            ),
        ),
    )
    occurrence_count = Sum(
        leaves, "program_shape_leaf", P0("program_shape_leaf", "occurrence_count")
    )
    directed_units = Sum(
        leaves, "program_shape_leaf", P0("program_shape_leaf", "sum_directed_units")
    )
    translation_units = Sum(
        leaves, "program_shape_leaf", P0("program_shape_leaf", "sum_translation_units")
    )
    directed_consistency = Sum(
        leaves,
        "program_shape_leaf",
        P0("program_shape_leaf", "sum_directed_consistency"),
    )
    evidence_window = N0(development, "development_evidence_window")
    recoverability = Min(
        L(1.0),
        Plus(
            N0(development, "protective_support_available"),
            N0(development, "embodiment_reset_reachable"),
        ),
    )
    return If(
        And(
            Gt(occurrence_count, L(0)),
            Gt(directed_units, L(0)),
            Gt(
                directed_consistency,
                Minus(occurrence_count, directed_consistency),
            ),
            Lt(occurrence_count, evidence_window),
        ),
        Times(
            P0("policy", "foveated_program_exploration_authority"),
            recoverability,
            Div(directed_units, Max(L(1), translation_units)),
            Div(
                Max(L(0), Minus(evidence_window, occurrence_count)),
                Max(L(1), evidence_window),
            ),
        ),
        L(0),
    )


def walking_cost(candidate):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    target_velocity = Times(
        P0("episode", "heading_x"),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    predicted_velocity = Plus(
        P0("episode", "state_vx"),
        N0(candidate, "mean_dvx"),
    )
    normalized_velocity_error = Div(
        Minus(predicted_velocity, target_velocity),
        velocity_scale,
    )
    normalized_lateral_velocity = Div(
        Minus(
            Plus(
                P0("episode", "state_vy"),
                N0(candidate, "mean_dvy"),
            ),
            Times(
                Minus(
                    L(0.0),
                    Div(
                        P0("episode", "lateral_offset"),
                        P0("episode", "standing_reference_z"),
                    ),
                ),
                P0("policy", "target_froude_speed"),
                velocity_scale,
            ),
        ),
        velocity_scale,
    )
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    normalized_lateral_position = Div(
        Plus(
            P0("episode", "lateral_offset"),
            Times(
                lookahead,
                Plus(
                    P0("episode", "state_vy"),
                    N0(candidate, "mean_dvy"),
                ),
            ),
        ),
        P0("episode", "standing_reference_z"),
    )
    normalized_energy = Div(
        N0(candidate, "mean_input_energy_joules"),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
            P0("episode", "standing_reference_z"),
        ),
    )
    return Plus(
        correction_cost(candidate),
        forward_task_cost(N0(candidate, "mean_dvx")),
        takeoff_task_cost(N0(candidate, "mean_dvz")),
        Times(
            normalized_lateral_velocity,
            normalized_lateral_velocity,
        ),
        Times(
            normalized_lateral_position,
            normalized_lateral_position,
        ),
        normalized_energy,
        gait_support_loss_cost(candidate),
        support_preview_cost(
            N0(candidate, "mean_dvx"),
            N0(candidate, "mean_dvy"),
        ),
    )


def support_deficit_observation(outcome="outcome"):
    """Body-weight-normalized missing support load from a raw receipt."""
    support_load_fraction = Div(
        Plus(
            P0(outcome, "post_support_0_force"),
            P0(outcome, "post_support_1_force"),
        ),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
        ),
    )
    return If(
        Or(
            Gt(P0(outcome, "pre_support_0_force"), L(0.0)),
            Gt(P0(outcome, "pre_support_1_force"), L(0.0)),
        ),
        Max(
            L(0.0),
            Minus(L(1.0), Min(L(1.0), support_load_fraction)),
        ),
        L(0.0),
    )


def walking_pair_cost(primary, secondary):
    synergy = Argmin(
        approved_exact_synergies(primary, secondary),
        "synergy_candidate",
        P0("synergy_candidate", "ordinal"),
        primary,
    )
    horizon_scale = Div(
        Max(
            L(1.0),
            IDiv(P0("episode", "response_frames"), L(2.0)),
        ),
        P0("episode", "response_frames"),
    )

    def compound_effect(key):
        return Plus(
            Times(
                horizon_scale,
                Plus(
                    AO(primary, key),
                    P0(secondary, key),
                ),
            ),
            AO(synergy, f"residual_{key[5:]}"),
        )

    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    predicted_z_x = Plus(
        body_z_x("episode", "state"),
        compound_effect("mean_dzx"),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wy"),
                compound_effect("mean_dwy"),
            ),
        ),
    )
    predicted_z_y = Minus(
        Plus(
            body_z_y("episode", "state"),
            compound_effect("mean_dzy"),
        ),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wx"),
                compound_effect("mean_dwx"),
            ),
        ),
    )
    target_velocity = Times(
        P0("episode", "heading_x"),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    predicted_velocity = Plus(
        P0("episode", "state_vx"),
        compound_effect("mean_dvx"),
    )
    normalized_velocity_error = Div(
        Minus(predicted_velocity, target_velocity),
        velocity_scale,
    )
    normalized_lateral_velocity = Div(
        Plus(
            P0("episode", "state_vy"),
            compound_effect("mean_dvy"),
        ),
        velocity_scale,
    )
    normalized_energy = Div(
        Plus(
            AO(primary, "mean_input_energy_joules"),
            P0(secondary, "mean_input_energy_joules"),
        ),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
            P0("episode", "standing_reference_z"),
        ),
    )
    support_loss_risk = Max(
        Div(
            Plus(
                AO(primary, "support_loss_ema"),
                P0(secondary, "support_loss_ema"),
            ),
            L(2.0),
        ),
        AO(synergy, "support_loss_ema"),
    )
    support_deficit_risk = Max(
        Div(
            Plus(
                AO(primary, "support_deficit_ema"),
                P0(secondary, "support_deficit_ema"),
            ),
            L(2.0),
        ),
        AO(synergy, "support_deficit_ema"),
    )
    return Plus(
        contextual_posture_cost(predicted_z_x, predicted_z_y),
        forward_task_cost(compound_effect("mean_dvx")),
        takeoff_task_cost(compound_effect("mean_dvz")),
        Times(
            normalized_lateral_velocity,
            normalized_lateral_velocity,
        ),
        normalized_energy,
        Times(
            AO(
                active_gait_attractor(),
                "support_transition_cost_numerator",
            ),
            support_loss_risk,
        ),
        Times(
            P0("policy", "support_phase_prior_strength"),
            support_deficit_risk,
        ),
        support_preview_cost(
            compound_effect("mean_dvx"),
            compound_effect("mean_dvy"),
        ),
    )


def local_effect_magnitude(candidate):
    return Plus(*[
        Times(N0(candidate, key), N0(candidate, key))
        for key in (
            "mean_dzx",
            "mean_dzy",
            "mean_dwx",
            "mean_dwy",
            "mean_dvx",
            "mean_dvy",
            "mean_dvz",
        )
    ])


def approved_exact_synergies(primary, secondary):
    secondary_token = (
        A(secondary, "token")
        if isinstance(secondary, str)
        else AO(secondary, "token")
    )
    return Filter(
        APPROVED_SYNERGIES,
        "synergy_candidate",
        Or(
            And(
                Eq(
                    A("synergy_candidate", "token_a"),
                    AO(primary, "token"),
                ),
                Eq(
                    A("synergy_candidate", "token_b"),
                    secondary_token,
                ),
            ),
            And(
                Eq(
                    A("synergy_candidate", "token_b"),
                    AO(primary, "token"),
                ),
                Eq(
                    A("synergy_candidate", "token_a"),
                    secondary_token,
                ),
            ),
        ),
    )


def choose_walking_primary_rule():
    primary = Argmin(
        ACTIVE_PHASE_MODELS,
        "candidate",
        walking_cost("candidate"),
        V("episode"),
    )
    return {
        "name": "ha_select_learned_walking_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Select the primary learned twitch before independently "
        "searching for a compatible simultaneous movement.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(0.0)),
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(0.0)),
            Eq(current_motor_programs(), L(0.0)),
            Gt(Count(ACTIVE_PHASE_MODELS), L(0.0)),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "selected_primary_token",
                T(AO(primary, "token")),
            ],
            [
                "set_attr",
                "episode",
                "selected_primary_context_id",
                T(N0(primary, "context_id")),
            ],
            ["set_attr", "episode", "motor_primary_ready", 1.0],
            ["set_attr", "episode",
             "selected_manifold_refinement_exploration_value", T(
                 foveated_program_exploration_value(primary)
             )],
            ["set_attr", "episode", "motor_primary_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def active_phase_model_predicate(candidate):
    """The existing support/state-local eligibility predicate for a primitive."""
    return And(
        Eq(
            P0(candidate, "support_phase"),
            P0("episode", "current_support_phase"),
        ),
        Gt(P0(candidate, "initialized"), L(0.5)),
        phase_prediction_authoritative(candidate),
        Eq(
            P0(candidate, "context_id"),
            N0(nearest_phase_context(candidate), "context_id"),
        ),
        Or(
            Gt(P0("episode", "last_directed_step"), L(0.0)),
            Not(Eq(
                A(candidate, "token"),
                A("episode", "last_locomotor_token"),
            )),
            Eq(Count(NONSTAGNANT_PHASE_MODELS), L(0.0)),
        ),
    )


def clear_stale_shared_walking_primary_rule():
    return {
        "name": "ha_clear_stale_shared_walking_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A primary-ready latch belongs to the request that "
        "authored it. Clear a prior request's unconsumed latch before the "
        "shared collapse is prepared; no later program may consume that "
        "primary under a newer sensor epoch.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(PI0("policy", "shared_motor_collapse_enabled"), L(1)),
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(PI0("episode", "recovery_mode"), L(0)),
            Eq(PI0("episode", "action_ready"), L(0)),
            Eq(PI0("episode", "motor_primary_ready"), L(1)),
            Eq(current_motor_programs(), L(0)),
            Gt(
                PI0("episode", "request_seq"),
                PI0("episode", "motor_primary_request_seq"),
            ),
        ),
        "effects": [[
            "set_attr", "episode", "motor_primary_ready", 0,
        ]],
    }


def prepare_shared_walking_primary_rule():
    valuation = A("phase_model", "motor_option_valuation_snapshot")
    walking_cost_index = 0
    exploration_value_index = 1
    return {
        "name": "ha_prepare_shared_walking_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Expose only support- and state-local primitive experts. "
        "Their grounded value is the negated existing whole-body walking cost; "
        "the shared collapse chooses the primary without body-specific logic.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_model",
            ],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(0.0)),
            Eq(current_motor_programs(), L(0.0)),
            active_phase_model_predicate("phase_model"),
            Lt(
                P0("phase_model", "motor_decision_value_epoch"),
                P0("episode", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "phase_model", "motor_option_valuation_snapshot", T(
                Vec(
                    walking_cost("phase_model"),
                    foveated_program_exploration_value("phase_model"),
                )
            )],
            [
                "add_edge",
                "episode",
                "has_motor_decision_option",
                "phase_model",
            ],
            ["set_attr", "phase_model", "available", 1.0],
            ["set_attr", "phase_model", "ordinal", T(
                P0("phase_model", "ordinal")
            )],
            ["set_attr", "phase_model", "default_value", 0.0],
            ["set_attr", "phase_model", "grounded_value", T(Plus(
                Minus(L(0.0), Nth(valuation, walking_cost_index)),
                Nth(valuation, exploration_value_index),
            ))],
            ["set_attr", "phase_model",
             "manifold_refinement_exploration_value", T(
                 Nth(valuation, exploration_value_index)
             )],
            ["set_attr", "episode",
             "maximum_manifold_refinement_exploration_value", T(Max(
                 P0(
                     "episode",
                     "maximum_manifold_refinement_exploration_value",
                 ),
                 Nth(valuation, exploration_value_index),
             ))],
            ["set_attr", "episode",
             "manifold_refinement_exploration_valuation_count", T(Plus(
                 P0(
                     "episode",
                     "manifold_refinement_exploration_valuation_count",
                 ),
                 If(
                     Gt(
                         Nth(valuation, exploration_value_index),
                         L(0),
                     ),
                     L(1),
                     L(0),
                 ),
             ))],
            ["set_attr", "phase_model", "motor_decision_value_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "phase_model", "motor_option_schema_ready", 1.0],
            [
                "set_attr",
                "phase_model",
                "motor_option_value_provenance",
                "grounded_support_conditioned_whole_body_walking_cost",
            ],
        ],
    }


def retire_inactive_shared_walking_primary_rule():
    return {
        "name": "ha_retire_inactive_shared_walking_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Remove phase/context experts that are no longer local "
        "before the next atomic collapse; they remain learned graph memory.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_model",
            ],
            [
                "episode",
                "has_motor_decision_option",
                "phase_model",
            ],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Not(active_phase_model_predicate("phase_model")),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_motor_decision_option",
                "phase_model",
            ],
            ["set_attr", "phase_model", "available", 0.0],
        ],
    }


def arm_shared_walking_primary_rule():
    unprepared = Filter(
        ACTIVE_PHASE_MODELS,
        "candidate",
        Not(Eq(
            P0("candidate", "motor_decision_value_epoch"),
            P0("episode", "request_seq"),
        )),
    )
    return {
        "name": "ha_arm_shared_walking_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Arm primary competition only when every currently local "
        "phase model carries a grounded value from this sensor epoch.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(0.0)),
            Eq(current_motor_programs(), L(0.0)),
            Gt(Count(ACTIVE_PHASE_MODELS), L(0.0)),
            Eq(Count(unprepared), L(0.0)),
            Eq(P0("episode", "decision_armed"), L(0.0)),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_published_decision_epoch"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
            ["set_attr", "episode", "decision_status", "armed"],
        ],
    }


def release_shared_walking_primary_rule():
    return {
        "name": "ha_release_shared_walking_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Translate the exact shared verdict into the existing "
        "analysis-by-synthesis primary slot. Program recall, arbitrary compound "
        "expansion, reflexes, and recovery retain their own graph pathways.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "primary",
            ],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(A("episode", "decision_status"), L("published")),
            Eq(
                P0("episode", "selected_decision_epoch"),
                P0("episode", "request_seq"),
            ),
            Eq(A("episode", "selected_option_ref"), V("primary")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "selected_primary_token",
                T(A("primary", "token")),
            ],
            [
                "set_attr",
                "episode",
                "selected_primary_context_id",
                T(P0("primary", "context_id")),
            ],
            ["set_attr", "episode", "motor_primary_ready", 1.0],
            ["set_attr", "episode",
             "selected_manifold_refinement_exploration_value", T(P0(
                 "primary", "manifold_refinement_exploration_value"
             ))],
            ["set_attr", "episode", "motor_primary_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def bundle_members(plan="plan"):
    return Neighbours(plan, "includes_humanoid_phase_action_model")


def native_humanoid_composition_enabled():
    """Use the shared native MotorCompose primitive for full-fidelity AbS."""
    return Gt(
        P0("policy", "native_humanoid_composition_enabled"),
        L(0.5),
    )


def native_motor_compose_member(candidate="candidate"):
    return {
        "type": "MotorCompose",
        "episode": V("episode"),
        "policy": V("policy"),
        "candidate": V(candidate),
    }


def takeoff_effort_projection(program="plan"):
    return {
        "type": "FutureManifoldProjection",
        "episode": V("episode"),
        "policy": V("policy"),
        "source": V(program),
        "field": "takeoff_effort_snapshot",
    }


def takeoff_effort_prepared(program="plan"):
    return Or(
        Not(Eq(A(program, "motor_task_context"), L("self_takeoff"))),
        Eq(
            P0(program, "takeoff_effort_audit_seq"),
            P0("episode", "request_seq"),
        ),
    )


def current_motor_programs():
    return Plus(
        Count(Neighbours(
            "episode",
            "has_active_humanoid_motor_program",
        )),
        Count(Neighbours(
            "episode",
            "has_ready_humanoid_motor_program",
        )),
    )


def available_bundle_candidates(plan="plan"):
    members = bundle_members(plan)
    return Filter(
        PHASE_MODELS,
        "bundle_candidate",
        And(
            Eq(
                P0("bundle_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Gt(P0("bundle_candidate", "initialized"), L(0.5)),
            Eq(
                P0("bundle_candidate", "context_id"),
                N0(
                    nearest_phase_context("bundle_candidate"),
                    "context_id",
                ),
            ),
            Not(Exists(
                members,
                "member",
                Eq(
                    P0("member", "actuator_group"),
                    P0("bundle_candidate", "actuator_group"),
                ),
            )),
            Or(
                Gt(
                    P0("episode", "self_takeoff_drive_active"),
                    L(0.5),
                ),
                Not(Exists(
                    members,
                    "member",
                    Eq(
                        Count(approved_exact_synergies(
                            V("member"),
                            "bundle_candidate",
                        )),
                        L(0.0),
                    ),
                )),
            ),
        ),
    )


def integer_body_z_x(var, prefix):
    """Integer-literal body-axis projection for newly authored cognition."""
    qx = PI0(var, f"{prefix}_qx")
    qy = PI0(var, f"{prefix}_qy")
    qz = PI0(var, f"{prefix}_qz")
    qw = PI0(var, f"{prefix}_qw")
    return Times(L(2), Plus(Times(qx, qz), Times(qy, qw)))


def integer_body_z_y(var, prefix):
    """Integer-literal companion to :func:`integer_body_z_x`."""
    qx = PI0(var, f"{prefix}_qx")
    qy = PI0(var, f"{prefix}_qy")
    qz = PI0(var, f"{prefix}_qz")
    qw = PI0(var, f"{prefix}_qw")
    return Times(L(2), Minus(Times(qy, qz), Times(qx, qw)))


def motor_receipt_memory_viable(outcome="outcome"):
    """General receipt viability shared by every motor-memory pathway.

    Canonical upright pose is relevant only when no situated locomotor
    trajectory owns the postural reference. Support loss, loading and unusual
    pose remain learned consequence/Pareto evidence. Only graph-held material
    interrupts, reset requests, or breached power/thermal limits withdraw
    memory authority from an intentionally owned trajectory.
    """
    post_tilt = Sqrt(Plus(
        Times(
            integer_body_z_x(outcome, "post"),
            integer_body_z_x(outcome, "post"),
        ),
        Times(
            integer_body_z_y(outcome, "post"),
            integer_body_z_y(outcome, "post"),
        ),
    ))
    canonical_pose_viable = And(
        Gt(
            PI0(outcome, "post_z"),
            Times(
                PI0("policy", "minimum_upright_height_fraction"),
                PI0("episode", "standing_reference_z"),
            ),
        ),
        Not(Gt(
            post_tilt,
            Max(
                PI0("episode", "single_action_tilt_envelope"),
                PI0("episode", "learned_gait_tilt_envelope"),
            ),
        )),
    )
    return And(
        Or(
            situated_locomotion_context_active(),
            canonical_pose_viable,
        ),
        Not(receipt_material_viability_breach(outcome)),
    )


def integer_phase_context_distance(model):
    """State-local phase distance without non-integer cognitive literals."""
    velocity_scale = Sqrt(Times(
        PI0("policy", "gravity_acceleration"),
        PI0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        PI0("episode", "standing_reference_z"),
        PI0("policy", "gravity_acceleration"),
    ))
    errors = (
        Minus(
            PI0(model, "anchor_z_x"),
            integer_body_z_x("episode", "state"),
        ),
        Minus(
            PI0(model, "anchor_z_y"),
            integer_body_z_y("episode", "state"),
        ),
        Times(
            lookahead,
            Minus(
                PI0(model, "anchor_wx"),
                PI0("episode", "state_wx"),
            ),
        ),
        Times(
            lookahead,
            Minus(
                PI0(model, "anchor_wy"),
                PI0("episode", "state_wy"),
            ),
        ),
        Div(
            Minus(
                PI0(model, "anchor_vx"),
                PI0("episode", "state_vx"),
            ),
            velocity_scale,
        ),
        Div(
            Minus(
                PI0(model, "anchor_vy"),
                PI0("episode", "state_vy"),
            ),
            velocity_scale,
        ),
        Div(
            Minus(
                PI0(model, "anchor_vz"),
                PI0("episode", "state_vz"),
            ),
            velocity_scale,
        ),
        Div(
            Minus(
                PI0(model, "anchor_lateral_offset"),
                PI0("episode", "lateral_offset"),
            ),
            PI0("episode", "standing_reference_z"),
        ),
    )
    return Plus(*(Times(error, error) for error in errors))


def integer_nearest_phase_context(candidate):
    """Return the nearest learned context using integer-native terms."""
    peers = Filter(
        PHASE_MODELS,
        "integer_context_peer",
        And(
            Eq(
                A("integer_context_peer", "token"),
                A(candidate, "token"),
            ),
            Eq(
                PI0("integer_context_peer", "support_phase"),
                PI0(candidate, "support_phase"),
            ),
            Eq(PI0("integer_context_peer", "initialized"), L(1)),
        ),
    )
    exact_peers = Filter(
        peers,
        "integer_shape_peer",
        Eq(
            A("integer_shape_peer", "configuration_shape"),
            A("episode", "state_motor_configuration_shape"),
        ),
    )
    eligible_peers = Filter(
        peers,
        "integer_eligible_peer",
        Or(
            Eq(
                A("integer_eligible_peer", "configuration_shape"),
                A("episode", "state_motor_configuration_shape"),
            ),
            Eq(Count(exact_peers), L(0)),
        ),
    )
    return Argmin(
        eligible_peers,
        "integer_nearest_peer",
        integer_phase_context_distance("integer_nearest_peer"),
        V(candidate),
    )


def integer_exact_synergies(primary, secondary):
    """Exact independent-effector pairs without anatomy or fault gates.

    Probe labels and support/load outcomes are evidence on the pair, not an
    exclusion class.  An untested pair is therefore a curiosity candidate
    with zero experience rather than an unavailable action.
    """
    primary_token = (
        A(primary, "token")
        if isinstance(primary, str)
        else AO(primary, "token")
    )
    secondary_token = (
        A(secondary, "token")
        if isinstance(secondary, str)
        else AO(secondary, "token")
    )
    return Filter(
        SYNERGIES,
        "integer_synergy_candidate",
        Or(
                And(
                    Eq(
                        A("integer_synergy_candidate", "token_a"),
                        primary_token,
                    ),
                    Eq(
                        A("integer_synergy_candidate", "token_b"),
                        secondary_token,
                    ),
                ),
                And(
                    Eq(
                        A("integer_synergy_candidate", "token_b"),
                        primary_token,
                    ),
                    Eq(
                        A("integer_synergy_candidate", "token_a"),
                        secondary_token,
                    ),
                ),
            ),
    )


def compound_curiosity_candidates(plan="plan"):
    """Compatible local independent effectors available to curiosity."""
    members = bundle_members(plan)
    return Filter(
        PHASE_MODELS,
        "curiosity_candidate",
        And(
            Eq(
                PI0("curiosity_candidate", "support_phase"),
                PI0("episode", "current_support_phase"),
            ),
            Eq(PI0("curiosity_candidate", "initialized"), L(1)),
            Eq(
                PI0("curiosity_candidate", "context_id"),
                Plus(
                    AO(
                        integer_nearest_phase_context(
                            "curiosity_candidate"
                        ),
                        "context_id",
                    ),
                    L(0),
                ),
            ),
            Not(Exists(
                members,
                "curiosity_existing_member",
                Eq(
                    PI0("curiosity_existing_member", "actuator_group"),
                    PI0("curiosity_candidate", "actuator_group"),
                ),
            )),
            Not(Exists(
                members,
                "curiosity_member_without_pair",
                Eq(
                    Count(integer_exact_synergies(
                        V("curiosity_member_without_pair"),
                        "curiosity_candidate",
                    )),
                    L(0),
                ),
            )),
        ),
    )


def compound_pair_experience(plan, candidate):
    """Receipt count for this exact graph-defined set of pair memories."""
    return Sum(
        bundle_members(plan),
        "curiosity_experience_member",
        Sum(
            integer_exact_synergies(
                V("curiosity_experience_member"),
                candidate,
            ),
            "curiosity_pair_memory",
            PI0("curiosity_pair_memory", "experience_count"),
        ),
    )


def compound_curiosity_target_order():
    """Evidence-derived assembly order for persistent residual exploration.

    Pair observations grow quadratically with assembly width, so the square
    root of failed evidence windows is the corresponding order estimate. The
    singleton origin supplies the additive one; candidate/group exhaustion
    remains the hard structural ceiling.
    """
    development = Pick({
        "type": "Neighbours",
        "node": V("episode"),
        "edge_type": "projects_embodied_development",
        "any_type": False,
    })
    capability = Pick({
        "type": "Neighbours",
        "node": development,
        "edge_type": "has_active_embodied_developmental_capability",
        "any_type": False,
    })
    failed_windows = Div(
        Plus(AO(capability, "failure_count"), L(0)),
        Max(
            L(1),
            Plus(AO(development, "development_evidence_window"), L(0)),
        ),
    )
    return If(
        And(
            Eq(A("plan", "motor_task_context"), L("self_takeoff")),
            Gt(PI0("episode", "self_takeoff_drive_active"), L(0)),
        ),
        Plus(
            L(1),
            Max(L(1), IDiv(Sqrt(failed_windows), L(1))),
        ),
        L(2),
    )


def compound_curiosity_can_expand():
    return And(
        Lt(PI0("plan", "member_count"), compound_curiosity_target_order()),
        Gt(Count(compound_curiosity_candidates()), L(0)),
    )


def integer_candidate_pair_residual(plan, candidate, key):
    """Exact calibrated nonlinear residual for integer-native expansion."""
    return Sum(
        bundle_members(plan),
        "curiosity_residual_member",
        Plus(
            AO(
                Argmin(
                    integer_exact_synergies(
                        V("curiosity_residual_member"),
                        candidate,
                    ),
                    "curiosity_residual_memory",
                    PI0("curiosity_residual_memory", "ordinal"),
                    V("curiosity_residual_member"),
                ),
                f"residual_{key}",
            ),
            L(0),
        ),
    )


def candidate_pair_residual(plan, candidate, key):
    members = bundle_members(plan)
    exact = approved_exact_synergies(V("member"), candidate)
    synergy = Argmin(
        exact,
        "synergy_candidate",
        P0("synergy_candidate", "ordinal"),
        V("member"),
    )
    return Sum(
        members,
        "member",
        N0(synergy, f"residual_{key}"),
    )


def bundle_synthesis_cost(plan="plan", addition=None):
    extra = L(0.0) if addition is None else L(1.0)
    count = Plus(P0(plan, "member_count"), extra)
    compound = Gt(count, L(1.0))
    frames = If(
        compound,
        Max(
            L(1.0),
            IDiv(P0("episode", "response_frames"), L(2.0)),
        ),
        P0("episode", "response_frames"),
    )
    horizon_scale = Div(frames, P0("episode", "response_frames"))

    def predicted(key):
        accumulated = P0(plan, f"sum_{key}")
        interaction = P0(plan, f"interaction_sum_{key}")
        if addition is not None:
            accumulated = Plus(
                accumulated,
                N0(addition, f"mean_{key}"),
            )
            interaction = Plus(
                interaction,
                candidate_pair_residual(plan, addition, key),
            )
        pair_horizon_scale = If(compound, L(1.0), L(0.0))
        return Plus(
            Times(horizon_scale, accumulated),
            Times(pair_horizon_scale, interaction),
        )

    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    predicted_z_x = Plus(
        body_z_x("episode", "state"),
        predicted("dzx"),
        Times(
            lookahead,
            Plus(P0("episode", "state_wy"), predicted("dwy")),
        ),
    )
    predicted_z_y = Minus(
        Plus(body_z_y("episode", "state"), predicted("dzy")),
        Times(
            lookahead,
            Plus(P0("episode", "state_wx"), predicted("dwx")),
        ),
    )
    target_velocity = Times(
        P0("episode", "heading_x"),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    forward_error = Div(
        Minus(
            Plus(P0("episode", "state_vx"), predicted("dvx")),
            target_velocity,
        ),
        velocity_scale,
    )
    lateral_error = Div(
        Minus(
            Plus(P0("episode", "state_vy"), predicted("dvy")),
            Times(
                Minus(
                    L(0.0),
                    Div(
                        P0("episode", "lateral_offset"),
                        P0("episode", "standing_reference_z"),
                    ),
                ),
                P0("policy", "target_froude_speed"),
                velocity_scale,
            ),
        ),
        velocity_scale,
    )
    lateral_position_error = Div(
        Plus(
            P0("episode", "lateral_offset"),
            Times(
                lookahead,
                Plus(P0("episode", "state_vy"), predicted("dvy")),
            ),
        ),
        P0("episode", "standing_reference_z"),
    )
    members = bundle_members(plan)
    accumulated_energy = Sum(
        members,
        "energy_member",
        P0("energy_member", "mean_input_energy_joules"),
    )
    if addition is not None:
        accumulated_energy = Plus(
            accumulated_energy,
            N0(addition, "mean_input_energy_joules"),
        )
    normalized_energy = Div(
        Times(horizon_scale, accumulated_energy),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
            P0("episode", "standing_reference_z"),
        ),
    )
    structural_cost = Div(
        Max(L(0.0), Minus(count, L(1.0))),
        Times(
            Max(L(1.0), P0("episode", "motor_effector_group_count")),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    compression_cost = If(
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        Times(
            P0("policy", "takeoff_motor_compression_authority"),
            P0("episode", "self_takeoff_compression_scale"),
            Plus(normalized_energy, structural_cost),
        ),
        L(0.0),
    )
    return Plus(
        contextual_posture_cost(predicted_z_x, predicted_z_y),
        forward_task_cost(predicted("dvx"), frames),
        takeoff_task_cost(predicted("dvz")),
        Times(lateral_error, lateral_error),
        Times(lateral_position_error, lateral_position_error),
        compression_cost,
        support_preview_cost(predicted("dvx"), predicted("dvy")),
    )


def motor_model_consequence(model, key, frames=None):
    if frames is None:
        frames = P0(model, "response_frames")
    return Times(P0(model, f"mean_rate_{key}"), frames)


def motor_memory_cost(memory="memory"):
    """Evaluate a grounded population program in the present body state."""
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    predicted_z_x = Plus(
        body_z_x("episode", "state"),
        motor_model_consequence(memory, "dzx"),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wy"),
                motor_model_consequence(memory, "dwy"),
            ),
        ),
    )
    predicted_z_y = Minus(
        Plus(
            body_z_y("episode", "state"),
            motor_model_consequence(memory, "dzy"),
        ),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wx"),
                motor_model_consequence(memory, "dwx"),
            ),
        ),
    )
    target_velocity = Times(
        P0("episode", "heading_x"),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    forward_error = Div(
        Minus(
            Plus(
                P0("episode", "state_vx"),
                motor_model_consequence(memory, "dvx"),
            ),
            target_velocity,
        ),
        velocity_scale,
    )
    target_lateral_velocity = Times(
        Minus(
            L(0.0),
            Div(
                P0("episode", "lateral_offset"),
                P0("episode", "standing_reference_z"),
            ),
        ),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    predicted_lateral_velocity = Plus(
        P0("episode", "state_vy"),
        motor_model_consequence(memory, "dvy"),
    )
    lateral_error = Div(
        Minus(
            predicted_lateral_velocity,
            target_lateral_velocity,
        ),
        velocity_scale,
    )
    lateral_position_error = Div(
        Plus(
            P0("episode", "lateral_offset"),
            Times(lookahead, predicted_lateral_velocity),
        ),
        P0("episode", "standing_reference_z"),
    )
    return Plus(
        contextual_posture_cost(predicted_z_x, predicted_z_y),
        forward_task_cost(
            motor_model_consequence(memory, "dvx"),
            P0(memory, "response_frames"),
        ),
        takeoff_task_cost(motor_model_consequence(memory, "dvz")),
        Times(lateral_error, lateral_error),
        Times(lateral_position_error, lateral_position_error),
        support_preview_cost(
            motor_model_consequence(memory, "dvx"),
            motor_model_consequence(memory, "dvy"),
        ),
    )


def motor_memory_lateral_cost(memory="memory"):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    target_lateral_velocity = Times(
        Minus(
            L(0.0),
            Div(
                P0("episode", "lateral_offset"),
                P0("episode", "standing_reference_z"),
            ),
        ),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    predicted_lateral_velocity = Plus(
        P0("episode", "state_vy"),
        motor_model_consequence(memory, "dvy"),
    )
    lateral_velocity_error = Div(
        Minus(
            predicted_lateral_velocity,
            target_lateral_velocity,
        ),
        velocity_scale,
    )
    lateral_position_error = Div(
        Plus(
            P0("episode", "lateral_offset"),
            Times(lookahead, predicted_lateral_velocity),
        ),
        P0("episode", "standing_reference_z"),
    )
    return Plus(
        Times(lateral_velocity_error, lateral_velocity_error),
        Times(lateral_position_error, lateral_position_error),
        support_preview_lateral_cost(
            motor_model_consequence(memory, "dvy")
        ),
    )


def primitive_lateral_cost(primary="primary"):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    target_lateral_velocity = Times(
        Minus(
            L(0.0),
            Div(
                P0("episode", "lateral_offset"),
                P0("episode", "standing_reference_z"),
            ),
        ),
        P0("policy", "target_froude_speed"),
        velocity_scale,
    )
    predicted_lateral_velocity = Plus(
        P0("episode", "state_vy"),
        P0(primary, "mean_dvy"),
    )
    lateral_velocity_error = Div(
        Minus(
            predicted_lateral_velocity,
            target_lateral_velocity,
        ),
        velocity_scale,
    )
    lateral_position_error = Div(
        Plus(
            P0("episode", "lateral_offset"),
            Times(lookahead, predicted_lateral_velocity),
        ),
        P0("episode", "standing_reference_z"),
    )
    return Plus(
        Times(lateral_velocity_error, lateral_velocity_error),
        Times(lateral_position_error, lateral_position_error),
        support_preview_lateral_cost(P0(primary, "mean_dvy")),
    )


def motor_error_energy(observed, predicted):
    """Dimensionless sensory-prediction error between two consequences."""
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    error_z_x = Plus(
        Minus(observed["dzx"], predicted["dzx"]),
        Times(
            lookahead,
            Minus(observed["dwy"], predicted["dwy"]),
        ),
    )
    error_z_y = Minus(
        Minus(observed["dzy"], predicted["dzy"]),
        Times(
            lookahead,
            Minus(observed["dwx"], predicted["dwx"]),
        ),
    )
    error_v_x = Div(
        Minus(observed["dvx"], predicted["dvx"]),
        velocity_scale,
    )
    error_v_y = Div(
        Minus(observed["dvy"], predicted["dvy"]),
        velocity_scale,
    )
    error_v_z = Div(
        Minus(observed["dvz"], predicted["dvz"]),
        velocity_scale,
    )
    return Plus(
        Times(error_z_x, error_z_x),
        Times(error_z_y, error_z_y),
        Times(error_v_x, error_v_x),
        Times(error_v_y, error_v_y),
        Times(error_v_z, error_v_z),
    )


def motor_lateral_error_energy(observed, predicted):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    error_z_y = Minus(
        Minus(observed["dzy"], predicted["dzy"]),
        Times(
            lookahead,
            Minus(observed["dwx"], predicted["dwx"]),
        ),
    )
    error_v_y = Div(
        Minus(observed["dvy"], predicted["dvy"]),
        velocity_scale,
    )
    return Plus(
        Times(error_z_y, error_z_y),
        Times(error_v_y, error_v_y),
    )


def motor_consequence_error_energy(
    observed,
    model="memory",
    frames=None,
):
    if frames is None:
        frames = P0("trial", "response_frames")
    return motor_error_energy(
        observed,
        {
            key: motor_model_consequence(model, key, frames)
            for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
        },
    )


def motor_lateral_consequence_error_energy(
    observed,
    model="memory",
    frames=None,
):
    if frames is None:
        frames = P0("trial", "response_frames")
    return motor_lateral_error_energy(
        observed,
        {
            key: motor_model_consequence(model, key, frames)
            for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
        },
    )


def motor_model_uncertainty(model="memory"):
    """Uncertainty of the learned mean, reduced only by exact receipts.

    A novel conditional edge carries its difference from the endpoint's
    marginal model as one prior pseudo-observation. Exact transition receipts
    then dilute that contextual novelty without mislabelling it fit residual.
    """
    count = Max(L(1.0), P0(model, "experience_count"))
    return Div(
        Plus(
            P0(model, "mean_prediction_error_energy"),
            Div(P0(model, "context_novelty_energy"), count),
        ),
        count,
    )


def motor_model_lateral_uncertainty(model="memory"):
    count = Max(L(1.0), P0(model, "experience_count"))
    return Div(
        Plus(
            P0(model, "mean_lateral_prediction_error_energy"),
            Div(P0(model, "context_lateral_novelty_energy"), count),
        ),
        count,
    )


def motor_memory_rank_cost(memory="memory"):
    return Plus(
        motor_memory_cost(memory),
        motor_model_uncertainty(memory),
        Div(
            P0(memory, "mean_input_energy_joules"),
            Times(
                P0("episode", "body_mass"),
                P0("policy", "gravity_acceleration"),
                P0("episode", "standing_reference_z"),
            ),
        ),
        Times(
            AO(
                active_gait_attractor(),
                "support_transition_cost_numerator",
            ),
            P0(memory, "support_loss_ema"),
        ),
        Minus(
            L(0.0),
            Div(
                P0(memory, "mean_directed_advance"),
                P0("episode", "standing_reference_z"),
            ),
        ),
    )


def canonical_motor_memory_rank(memory="memory"):
    """Prefer experienced shape priors, then stable local identity."""
    return If(
        Eq(
            P0(memory, "warm_start_requires_verification"),
            L(1.0),
        ),
        Minus(
            L(0.0),
            Plus(P0(memory, "experience_count"), L(1.0)),
        ),
        Plus(P0(memory, "ordinal"), L(1.0)),
    )


def compound_output_permitted():
    return And(
        Eq(P0("episode", "evaluation_active"), L(1.0)),
        Gt(P0("episode", "support_sensor_count"), L(0.0)),
        Not(Gt(
            Sqrt(Times(
                P0("episode", "lateral_offset"),
                P0("episode", "lateral_offset"),
            )),
            P0("policy", "maximum_lateral_drift_metres"),
        )),
        Or(
            Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
            Not(Lt(
                Minus(
                    P0("episode", "decision_count"),
                    P0("episode", "last_compound_decision_count"),
                ),
                P0("episode", "compound_response_interval"),
            )),
        ),
        Or(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            situated_locomotion_context_active(),
            Not(Gt(
                P0("episode", "tilt_magnitude"),
                P0("episode", "learned_gait_tilt_envelope"),
            )),
        ),
    )


def motor_memory_output_permitted(memory="memory"):
    """Separate mastered motor chunks from de-novo compound exploration."""
    evaluation_safe = And(
        Eq(P0("episode", "evaluation_active"), L(1.0)),
        Or(
            situated_locomotion_context_active(),
            Not(Gt(
                P0("episode", "tilt_magnitude"),
                P0("episode", "learned_gait_mean_tilt"),
            )),
        ),
    )
    verified_takeoff_stage = And(
        Eq(A(memory, "motor_task_context"), L("self_takeoff")),
        Eq(P0(memory, "trajectory_verified"), L(1.0)),
        Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
        Eq(P0("episode", "self_takeoff_compression_scale"), L(0.0)),
        Eq(P0("episode", "upright"), L(1.0)),
        Eq(P0("episode", "recovery_mode"), L(0.0)),
    )
    return Or(
        verified_takeoff_stage,
        And(
            Eq(P0(memory, "member_count"), L(1.0)),
            Eq(P0("episode", "evaluation_active"), L(1.0)),
            Not(compound_output_permitted()),
        ),
        And(
            Gt(P0(memory, "member_count"), L(1.0)),
            Or(
                And(
                    Eq(
                        P0(
                            memory,
                            "warm_start_requires_verification",
                        ),
                        L(1.0),
                    ),
                    evaluation_safe,
                ),
                And(
                    Eq(
                        P0(
                            memory,
                            "warm_start_requires_verification",
                        ),
                        L(0.0),
                    ),
                    compound_output_permitted(),
                ),
            ),
        ),
    )


def grounded_motor_memories():
    return Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "memory_candidate",
        And(
            Eq(A("memory_candidate", "status"), L("grounded")),
            Eq(P0("memory_candidate", "memory_eligible"), L(1.0)),
            Gt(P0("memory_candidate", "member_count"), L(0.0)),
            Eq(
                A("memory_candidate", "motor_task_context"),
                motor_task_context(),
            ),
            Or(
                Eq(
                    A("memory_candidate", "motor_residual_context"),
                    motor_residual_context(),
                ),
                And(
                    Eq(
                        A("memory_candidate", "motor_residual_context"),
                        L(None),
                    ),
                    Eq(motor_residual_context(), L("locomotion")),
                ),
            ),
            Eq(
                P0("memory_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Eq(
                A("memory_candidate", "primary_token"),
                A("episode", "selected_primary_token"),
            ),
            Eq(
                P0("memory_candidate", "primary_context_id"),
                P0("episode", "selected_primary_context_id"),
            ),
            Or(
                Not(Eq(
                    A("memory_candidate", "motor_task_context"),
                    L("locomotion"),
                )),
                Eq(
                    A("memory_candidate", "configuration_shape"),
                    L(None),
                ),
                Eq(
                    A("memory_candidate", "configuration_shape"),
                    A("episode", "state_motor_configuration_shape"),
                ),
            ),
            motor_memory_output_permitted("memory_candidate"),
            Or(
                Eq(
                    P0(
                        "memory_candidate",
                        "warm_start_requires_verification",
                    ),
                    L(0.0),
                ),
                Eq(
                    P0("memory_candidate", "warm_start_verified"),
                    L(1.0),
                ),
                And(
                    Eq(
                        A("memory_candidate", "motor_task_context"),
                        L("self_takeoff"),
                    ),
                    Eq(
                        P0("memory_candidate", "trajectory_verified"),
                        L(1.0),
                    ),
                    Eq(
                        P0("episode", "self_takeoff_compression_scale"),
                        L(0.0),
                    ),
                ),
            ),
        ),
    )


def verified_takeoff_stage_transitions(stage="stage_candidate"):
    return Filter(
        Neighbours(stage, "has_humanoid_motor_transition"),
        "stage_transition",
        And(
            Eq(A("stage_transition", "status"), L("grounded")),
            Eq(P0("stage_transition", "memory_eligible"), L(1.0)),
            Eq(P0("stage_transition", "trajectory_verified"), L(1.0)),
            Eq(
                P0("stage_transition", "jump_schema_id"),
                P0(stage, "jump_schema_id"),
            ),
            Gt(P0("stage_transition", "response_frames"), L(0.0)),
        ),
    )


def verified_takeoff_stage_response_frames(stage="memory"):
    transitions = verified_takeoff_stage_transitions(stage)
    temporal_edge = Argmin(
        transitions,
        "stage_transition",
        P0("stage_transition", "ordinal"),
        V(stage),
    )
    return Max(
        P0(stage, "response_frames"),
        AO(temporal_edge, "response_frames"),
    )


def verified_takeoff_stages():
    return Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "stage_candidate",
        And(
            Eq(A("stage_candidate", "status"), L("grounded")),
            Eq(P0("stage_candidate", "memory_eligible"), L(1.0)),
            Eq(A("stage_candidate", "motor_task_context"), L("self_takeoff")),
            Eq(P0("stage_candidate", "trajectory_verified"), L(1.0)),
            Eq(
                P0("stage_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Gt(P0("stage_candidate", "member_count"), L(0.0)),
            Gt(
                verified_takeoff_stage_response_frames("stage_candidate"),
                L(0.0),
            ),
        ),
    )


def recall_verified_takeoff_stage_rule():
    stages = verified_takeoff_stages()
    best = Argmin(
        stages,
        "stage_candidate",
        motor_memory_rank_cost("stage_candidate"),
        V("episode"),
    )
    members = Neighbours(
        "memory",
        "includes_humanoid_phase_action_model",
    )
    primary_members = Filter(
        members,
        "stage_member",
        Eq(A("stage_member", "token"), A("memory", "primary_token")),
    )
    primary = Argmin(
        primary_members,
        "stage_member",
        P0("stage_member", "ordinal"),
        V("memory"),
    )
    secondary_options = Filter(
        members,
        "stage_member",
        Not(Eq(A("stage_member", "token"), A("memory", "primary_token"))),
    )
    secondary = Argmin(
        secondary_options,
        "stage_member",
        P0("stage_member", "ordinal"),
        primary,
    )
    return {
        "name": "ha_prepare_verified_takeoff_stage",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "F-16-style stage firing for a recovered takeoff schema: "
        "each whole-trajectory-verified population stage competes from its own "
        "current support-topology precondition instead of waiting for an ordinal "
        "predecessor or matching the walking primitive selector's primary token. "
        "Duration comes from the stage receipt or its verified outgoing temporal "
        "edge, allowing a compound schema root to fire without inventing a "
        "host-side or magic-number horizon. "
        "Compression keeps these defaults output-null so analysis by synthesis "
        "can construct a different realization.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_program", "memory"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
            Eq(P0("episode", "self_takeoff_compression_scale"), L(0.0)),
            Eq(P0("episode", "upright"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(1.0)),
            Eq(current_motor_programs(), L(0.0)),
            Gt(Count(stages), L(0.0)),
            Eq(V("memory"), best),
        ),
        "effects": [
            ["add_node", "preparation", "HumanoidMotorPreparation", {
                "request_seq": T(P0("episode", "request_seq")),
                "status": "output_null",
                "preparation_kind": "takeoff_stage",
                "direct_path_cost": T(motor_memory_cost("memory")),
                "indirect_path_cost": T(motor_model_uncertainty("memory")),
                "lateral_indirect_path_cost": T(
                    motor_model_lateral_uncertainty("memory")
                ),
                "gated_cost": T(motor_memory_rank_cost("memory")),
                "primitive_cost": T(motor_memory_rank_cost("memory")),
                "lateral_cost": T(motor_memory_lateral_cost("memory")),
                "primitive_lateral_cost": T(
                    motor_memory_lateral_cost("memory")
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "add_edge",
                "preparation",
                "prepares_humanoid_motor_program",
                "memory",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("memory", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                verified_takeoff_stage_response_frames("memory")
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    T(motor_model_consequence(
                        "memory",
                        key,
                        verified_takeoff_stage_response_frames("memory"),
                    )),
                ]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "learned_takeoff_stage"],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "motor_primary_ready", 0.0],
            ["set_attr", "episode", "motor_preparation_count", T(
                Plus(P0("episode", "motor_preparation_count"), L(1.0))
            )],
        ],
    }


def equivalent_motor_memories(plan="plan"):
    """Return grounded programs with exactly the same structural members."""
    plan_members = Neighbours(
        plan,
        "includes_humanoid_phase_action_model",
    )
    candidates = Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "memory_candidate",
        And(
            Eq(A("memory_candidate", "status"), L("grounded")),
            Eq(
                A("memory_candidate", "motor_task_context"),
                A(plan, "motor_task_context"),
            ),
            Eq(
                A("memory_candidate", "motor_residual_context"),
                A(plan, "motor_residual_context"),
            ),
            Eq(
                P0("memory_candidate", "support_phase"),
                P0(plan, "support_phase"),
            ),
            Eq(
                P0("memory_candidate", "primary_context_id"),
                P0(plan, "primary_context_id"),
            ),
            Or(
                Eq(A(plan, "configuration_shape"), L(None)),
                Eq(
                    A("memory_candidate", "configuration_shape"),
                    A(plan, "configuration_shape"),
                ),
            ),
            Eq(
                P0("memory_candidate", "member_count"),
                P0(plan, "member_count"),
            ),
            Eq(
                Count(Filter(
                    plan_members,
                    "plan_member",
                    Not(Exists(
                        Neighbours(
                            "memory_candidate",
                            "includes_humanoid_phase_action_model",
                        ),
                        "memory_member",
                        Eq(
                            A("memory_member", "token"),
                            A("plan_member", "token"),
                        ),
                    )),
                )),
                L(0.0),
            ),
        ),
    )
    return candidates


def recall_motor_memory_rule():
    memories = grounded_motor_memories()
    best = Argmin(
        memories,
        "memory_candidate",
        motor_memory_rank_cost("memory_candidate"),
        V("episode"),
    )
    members = Neighbours(
        "memory",
        "includes_humanoid_phase_action_model",
    )
    secondary_options = Filter(
        members,
        "member",
        Not(Eq(
            A("member", "token"),
            A("memory", "primary_token"),
        )),
    )
    secondary = Argmin(
        secondary_options,
        "member",
        P0("member", "ordinal"),
        V("primary"),
    )
    verified_transferred_default = And(
        Eq(PI0("memory", "warm_start_requires_verification"), L(1)),
        Eq(PI0("memory", "warm_start_verified"), L(1)),
    )
    return {
        "name": "ha_reassociate_grounded_motor_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Keep grounded population programs output-null until one "
        "fits the present support context and predicts lower task error than "
        "the best primitive. A transferred default that earned its local "
        "verification receipt remains a System-1 default while its exact "
        "memory updates online. Release that existing cortical-style "
        "repertoire state without reconstruction or host selection.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "primary",
            ],
            ["episode", "has_humanoid_motor_program", "memory"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "regime_applied_ordinal"), L(0.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(1.0)),
            Eq(current_motor_programs(), L(0.0)),
            Gt(Count(memories), L(0.0)),
            motor_memory_output_permitted("memory"),
            Eq(A("primary", "token"), A("episode", "selected_primary_token")),
            Eq(
                P0("memory", "primary_context_id"),
                P0("episode", "selected_primary_context_id"),
            ),
            Eq(
                P0("primary", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Eq(V("memory"), best),
            Or(
                verified_transferred_default,
                Lt(
                    motor_memory_rank_cost("memory"),
                    walking_cost("primary"),
                ),
            ),
            Or(
                verified_transferred_default,
                Not(Gt(
                    Plus(
                        motor_memory_lateral_cost("memory"),
                        motor_model_lateral_uncertainty("memory"),
                    ),
                    primitive_lateral_cost("primary"),
                )),
            ),
        ),
        "effects": [
            ["add_node", "preparation", "HumanoidMotorPreparation", {
                "request_seq": T(P0("episode", "request_seq")),
                "status": "output_null",
                "preparation_kind": "memory",
                "direct_path_cost": T(motor_memory_cost("memory")),
                "indirect_path_cost": T(
                    motor_model_uncertainty("memory")
                ),
                "lateral_indirect_path_cost": T(
                    motor_model_lateral_uncertainty("memory")
                ),
                "gated_cost": T(motor_memory_rank_cost("memory")),
                "primitive_cost": T(walking_cost("primary")),
                "lateral_cost": T(
                    motor_memory_lateral_cost("memory")
                ),
                "primitive_lateral_cost": T(
                    primitive_lateral_cost("primary")
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "add_edge",
                "preparation",
                "prepares_humanoid_motor_program",
                "memory",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("memory", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("memory", "response_frames")
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    T(motor_model_consequence("memory", key)),
                ]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "learned_walk"],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "motor_primary_ready", 0.0],
            ["set_attr", "episode", "motor_preparation_count", T(
                Plus(P0("episode", "motor_preparation_count"), L(1.0))
            )],
        ],
    }


def outgoing_motor_transitions(previous="previous"):
    return Neighbours(previous, "has_humanoid_motor_transition")


def eligible_motor_transitions(previous="previous"):
    return Filter(
        outgoing_motor_transitions(previous),
        "transition_candidate",
        And(
            Eq(A("transition_candidate", "status"), L("grounded")),
            Eq(P0("transition_candidate", "memory_eligible"), L(1.0)),
            Eq(
                A("transition_candidate", "motor_task_context"),
                motor_task_context(),
            ),
            Or(
                Eq(
                    A("transition_candidate", "motor_task_context"),
                    L("locomotion"),
                ),
                And(
                    Eq(
                        P0("transition_candidate", "trajectory_verified"),
                        L(1.0),
                    ),
                    Eq(
                        P0("episode", "self_takeoff_compression_scale"),
                        L(0.0),
                    ),
                ),
            ),
            Or(
                Not(Eq(
                    A("transition_candidate", "motor_task_context"),
                    L("locomotion"),
                )),
                Eq(
                    P0("transition_candidate", "prediction_error_measured"),
                    L(1.0),
                ),
            ),
            Eq(
                P0("transition_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Exists(
                Neighbours(
                    "transition_candidate",
                    "continues_with_humanoid_motor_program",
                ),
                "target_memory",
                Or(
                    Not(Eq(
                        A("transition_candidate", "motor_task_context"),
                        L("locomotion"),
                    )),
                    Eq(
                        A("target_memory", "configuration_shape"),
                        L(None),
                    ),
                    Eq(
                        A("target_memory", "configuration_shape"),
                        A("episode", "state_motor_configuration_shape"),
                    ),
                ),
            ),
        ),
    )


def recall_motor_sequence_rule():
    transitions = eligible_motor_transitions()
    best = Argmin(
        transitions,
        "transition_candidate",
        motor_memory_rank_cost("transition_candidate"),
        V("previous"),
    )
    members = Neighbours(
        "memory",
        "includes_humanoid_phase_action_model",
    )
    secondary_options = Filter(
        members,
        "member",
        Not(Eq(
            A("member", "token"),
            A("memory", "primary_token"),
        )),
    )
    secondary = Argmin(
        secondary_options,
        "member",
        P0("member", "ordinal"),
        V("primary"),
    )
    return {
        "name": "ha_advance_grounded_motor_sequence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Treat the last safe output-potent population state as "
        "temporal context. Follow the best grounded outgoing transition only "
        "when its conditional forward model beats the best primitive in the "
        "present body state. The receipt-updated graph, not Python, advances "
        "the motor trajectory.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "previous",
                "has_humanoid_motor_transition",
                "transition",
            ],
            [
                "transition",
                "continues_with_humanoid_motor_program",
                "memory",
            ],
            [
                "memory",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "regime_applied_ordinal"), L(0.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(1.0)),
            Eq(current_motor_programs(), L(0.0)),
            motor_memory_output_permitted("memory"),
            Gt(Count(transitions), L(0.0)),
            Eq(V("transition"), best),
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Eq(A("memory", "motor_task_context"), motor_task_context()),
            Eq(
                P0("memory", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Eq(A("primary", "token"), A("memory", "primary_token")),
            Eq(
                P0("primary", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Lt(
                motor_memory_rank_cost("transition"),
                walking_cost("primary"),
            ),
            Not(Gt(
                Plus(
                    motor_memory_lateral_cost("transition"),
                    motor_model_lateral_uncertainty("transition"),
                ),
                primitive_lateral_cost("primary"),
            )),
        ),
        "effects": [
            ["add_node", "preparation", "HumanoidMotorPreparation", {
                "request_seq": T(P0("episode", "request_seq")),
                "status": "output_null",
                "preparation_kind": "sequence",
                "direct_path_cost": T(
                    motor_memory_cost("transition")
                ),
                "indirect_path_cost": T(
                    motor_model_uncertainty("transition")
                ),
                "lateral_indirect_path_cost": T(
                    motor_model_lateral_uncertainty("transition")
                ),
                "gated_cost": T(
                    motor_memory_rank_cost("transition")
                ),
                "primitive_cost": T(walking_cost("primary")),
                "lateral_cost": T(
                    motor_memory_lateral_cost("transition")
                ),
                "primitive_lateral_cost": T(
                    primitive_lateral_cost("primary")
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "add_edge",
                "preparation",
                "prepares_humanoid_motor_transition",
                "transition",
            ],
            [
                "add_edge",
                "preparation",
                "prepares_humanoid_motor_program",
                "memory",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("memory", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("transition", "response_frames")
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    T(motor_model_consequence("transition", key)),
                ]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "learned_walk"],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "motor_primary_ready", 0.0],
            ["set_attr", "episode", "motor_preparation_count", T(
                Plus(P0("episode", "motor_preparation_count"), L(1.0))
            )],
        ],
    }


def release_prepared_motor_memory_rule():
    return {
        "name": "ha_release_prepared_motor_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Model thalamic disinhibition as a distinct graph event: "
        "the direct task advantage releases an output-null preparation only "
        "after paying its receipt-learned indirect uncertainty cost.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "preparation",
                "prepares_humanoid_motor_program",
                "memory",
            ],
        ],
        "where": And(
            Eq(A("preparation", "status"), L("output_null")),
            Eq(
                P0("preparation", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Or(
                And(
                    Eq(
                        A("preparation", "preparation_kind"),
                        L("memory"),
                    ),
                    Or(
                        And(
                            Eq(
                                PI0(
                                    "memory",
                                    "warm_start_requires_verification",
                                ),
                                L(1),
                            ),
                            Eq(
                                PI0("memory", "warm_start_verified"),
                                L(1),
                            ),
                        ),
                        Lt(
                            P0("preparation", "gated_cost"),
                            P0("preparation", "primitive_cost"),
                        ),
                    ),
                ),
                And(
                    Eq(
                        A("preparation", "preparation_kind"),
                        L("takeoff_stage"),
                    ),
                    Eq(A("memory", "motor_task_context"), L("self_takeoff")),
                    Eq(P0("memory", "trajectory_verified"), L(1.0)),
                    Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
                    Eq(
                        P0("episode", "self_takeoff_compression_scale"),
                        L(0.0),
                    ),
                    Eq(P0("episode", "upright"), L(1.0)),
                    Eq(P0("episode", "recovery_mode"), L(0.0)),
                ),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "recalls_humanoid_motor_program",
                "memory",
            ],
            [
                "del_edge",
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            ["set_attr", "preparation", "status", "output_potent"],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
            ["set_attr", "episode", "last_compound_decision_count", T(
                If(
                    Gt(P0("memory", "member_count"), L(1.0)),
                    P0("episode", "decision_count"),
                    P0("episode", "last_compound_decision_count"),
                )
            )],
            ["set_attr", "episode", "motor_memory_recall_count", T(
                Plus(
                    P0("episode", "motor_memory_recall_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "warm_start_memory_recall_count", T(
                Plus(
                    P0("episode", "warm_start_memory_recall_count"),
                    If(
                        Eq(
                            P0(
                                "memory",
                                "warm_start_requires_verification",
                            ),
                            L(1.0),
                        ),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "episode", "motor_preparation_release_count", T(
                Plus(
                    P0("episode", "motor_preparation_release_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "memory", "last_recall_request_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "memory", "recall_count", T(
                Plus(P0("memory", "recall_count"), L(1.0))
            )],
            ["set_attr", "memory", "lifetime_recall_count", T(
                Plus(P0("memory", "lifetime_recall_count"), L(1.0))
            )],
            ["set_attr", "memory", "consolidation_count", T(
                Plus(P0("memory", "consolidation_count"), L(1.0))
            )],
        ],
    }


def release_prepared_motor_sequence_rule():
    return {
        "name": "ha_release_prepared_motor_sequence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Release one prepared temporal successor through the same "
        "direct/indirect gate while preserving its predecessor-conditioned "
        "forward model and timing coordinate.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "preparation",
                "prepares_humanoid_motor_transition",
                "transition",
            ],
            [
                "preparation",
                "prepares_humanoid_motor_program",
                "memory",
            ],
        ],
        "where": And(
            Eq(A("preparation", "status"), L("output_null")),
            Eq(
                A("preparation", "preparation_kind"),
                L("sequence"),
            ),
            Eq(
                P0("preparation", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Lt(
                P0("preparation", "gated_cost"),
                P0("preparation", "primitive_cost"),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "recalls_humanoid_motor_transition",
                "transition",
            ],
            [
                "add_edge",
                "episode",
                "recalls_humanoid_motor_program",
                "memory",
            ],
            [
                "del_edge",
                "episode",
                "has_active_humanoid_motor_preparation",
                "preparation",
            ],
            ["set_attr", "preparation", "status", "output_potent"],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
            ["set_attr", "episode", "last_compound_decision_count", T(
                If(
                    Gt(P0("memory", "member_count"), L(1.0)),
                    P0("episode", "decision_count"),
                    P0("episode", "last_compound_decision_count"),
                )
            )],
            ["set_attr", "episode", "motor_memory_recall_count", T(
                Plus(
                    P0("episode", "motor_memory_recall_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "warm_start_memory_recall_count", T(
                Plus(
                    P0("episode", "warm_start_memory_recall_count"),
                    If(
                        Eq(
                            P0(
                                "memory",
                                "warm_start_requires_verification",
                            ),
                            L(1.0),
                        ),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "episode", "motor_sequence_recall_count", T(
                Plus(
                    P0("episode", "motor_sequence_recall_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "motor_preparation_release_count", T(
                Plus(
                    P0("episode", "motor_preparation_release_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "memory", "last_recall_request_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "memory", "recall_count", T(
                Plus(P0("memory", "recall_count"), L(1.0))
            )],
            ["set_attr", "memory", "lifetime_recall_count", T(
                Plus(P0("memory", "lifetime_recall_count"), L(1.0))
            )],
            ["set_attr", "transition", "last_recall_request_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "transition", "recall_count", T(
                Plus(P0("transition", "recall_count"), L(1.0))
            )],
        ],
    }


def choose_walking_rule():
    allow_expansion = compound_output_permitted()
    return {
        "name": "ha_choose_learned_walking_twitch",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Collapse every currently open motor residual into one "
        "graph-native outcome. Ordinary locomotion begins from its best "
        "support-conditioned primitive; upright recovery begins from the "
        "support-conditioned correction selected by the same forward models. "
        "The one motor-program node may recruit arbitrary effectors and is "
        "later grounded as a reusable compound rather than multiplexing two "
        "independent commands.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "primary",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_primary_ready"), L(1.0)),
            Eq(current_motor_programs(), L(0.0)),
            Eq(A("primary", "token"), A("episode", "selected_primary_token")),
            Eq(
                P0("primary", "context_id"),
                P0("episode", "selected_primary_context_id"),
            ),
            Eq(
                P0("primary", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Or(
                Eq(PI0("episode", "recovery_mode"), L(1)),
                Eq(
                    PI0("policy", "shared_motor_collapse_enabled"),
                    L(0),
                ),
                And(
                    Eq(
                        PI0("episode", "motor_primary_request_seq"),
                        PI0("episode", "request_seq"),
                    ),
                    Eq(
                        PI0("episode", "selected_decision_epoch"),
                        PI0("episode", "request_seq"),
                    ),
                    Eq(A("episode", "selected_option_ref"), V("primary")),
                ),
            ),
        ),
        "effects": [
            ["add_node", "plan", "HumanoidMotorProgram", {
                "request_seq": T(P0("episode", "request_seq")),
                "ordinal": T(P0("episode", "request_seq")),
                "status": "building",
                "motor_task_context": T(motor_task_context()),
                "motor_residual_context": T(motor_residual_context()),
                "collapse_kind": T(If(
                    Eq(P0("episode", "recovery_mode"), L(1.0)),
                    L("compound_recovery_locomotion"),
                    L("locomotion"),
                )),
                "open_residual_count": T(If(
                    Eq(P0("episode", "recovery_mode"), L(1.0)),
                    L(2.0),
                    L(1.0),
                )),
                "motor_task_phase": "unresolved",
                "support_phase": T(
                    P0("episode", "current_support_phase")
                ),
                "primary_token": T(A("primary", "token")),
                "primary_context_id": T(P0("primary", "context_id")),
                "configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "member_count": 1.0,
                # Exploration authority is evidence about an exact singleton
                # program. Preserve that identity through synthesis instead
                # of allowing the selected primary to recruit an unobserved
                # secondary composition.
                "allow_expansion": T(If(
                    Gt(
                        P0(
                            "episode",
                            "selected_manifold_refinement_exploration_value",
                        ),
                        L(0),
                    ),
                    L(0.0),
                    If(allow_expansion, L(1.0), L(0.0)),
                )),
                **{
                    f"sum_{key}": T(P0("primary", f"mean_{key}"))
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                **{
                    f"interaction_sum_{key}": 0.0
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                "receipt_learned": 0.0,
                "memory_eligible": 0.0,
                "experience_count": 0.0,
                "mean_prediction_error_energy": 0.0,
                "mean_lateral_prediction_error_energy": 0.0,
                "consolidation_count": 0.0,
                "recall_count": 0.0,
                "lifetime_recall_count": 0.0,
                "last_recall_request_seq": 0.0,
                "last_memory_update_request_seq": 0.0,
                **{
                    f"mean_{key}": 0.0
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                **{
                    f"mean_rate_{key}": 0.0
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                "synthesis_yield_required": 0.0,
                "native_composition_attached": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "resumes_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "plan",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
            ["add_node", "frontier", "HumanoidMotorProgramFrontier", {
                "generation": 1.0,
                "status": "open",
            }],
            [
                "add_edge",
                "plan",
                "has_humanoid_motor_program_frontier",
                "frontier",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("primary", "token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("primary", "token")
            )],
            ["set_attr", "episode", "decision_kind", "learned_walk"],
            ["set_attr", "episode", "selected_collapse_kind", T(If(
                Eq(P0("episode", "recovery_mode"), L(1.0)),
                L("compound_recovery_locomotion"),
                L("locomotion"),
            ))],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
            ["set_attr", "episode", "motor_primary_ready", 0.0],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0.0],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"),
                If(
                    Eq(P0("episode", "recovery_mode"), L(1.0)),
                    L(1.0),
                    L(0.0),
                ),
            ))],
        ],
    }


def stamp_future_manifold_audit_contract_rule():
    """Copy the opt-in multi-frame risk contract onto each motor program.

    This is intentionally only graph bookkeeping.  The native projection
    evaluator owns certification/rejection; the disabled branch must remain
    the legacy humanoid selector and therefore records ``disabled`` without
    evaluating any future path.
    """
    enabled = Gt(P0("policy", "future_manifold_enabled"), L(0.5))
    return {
        "name": "ha_stamp_future_manifold_audit_contract",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_program", "program"],
        ],
        "where": And(
            Eq(P0("program", "future_manifold_audit_initialized"), L(0.0)),
            Or(
                Eq(A("program", "status"), L("building")),
                Eq(A("program", "status"), L("ready")),
            ),
        ),
        "effects": [
            ["set_attr", "program", "future_manifold_audit_initialized", 1.0],
            ["set_attr", "program", "future_manifold_policy_enabled", T(If(enabled, L(1.0), L(0.0)))],
            ["set_attr", "program", "future_manifold_temporal_anchors_enabled", T(If(And(enabled, Gt(P0("policy", "future_manifold_temporal_anchors_enabled"), L(0.5))), L(1.0), L(0.0)))],
            ["set_attr", "program", "future_manifold_local_refinement_enabled", T(If(And(enabled, Gt(P0("policy", "future_manifold_local_refinement_enabled"), L(0.5))), L(1.0), L(0.0)))],
            ["set_attr", "program", "future_manifold_anchor_schedule", T(If(enabled, L("dense_1_2_3_loglog_far"), L("disabled")))],
            ["set_attr", "program", "future_manifold_risk_gate", T(If(enabled, L("multi_frame"), L("disabled")))],
            ["set_attr", "program", "future_manifold_projection_resolved", 0.0],
            ["set_attr", "program", "future_manifold_projection_reason", T(If(enabled, L("pending"), L("disabled")))],
            ["set_attr", "program", "future_manifold_projection_budget", T(P0("policy", "future_manifold_projection_budget"))],
            ["set_attr", "program", "future_manifold_physical_horizon", T(P0("episode", "response_frames"))],
            ["set_attr", "program", "future_manifold_anchor_budget", T(P0("policy", "future_manifold_projection_budget"))],
            ["set_attr", "program", "future_manifold_refinement_budget", T(P0("policy", "future_manifold_max_refinements"))],
            ["set_attr", "program", "future_manifold_shape_order_budget", T(P0("policy", "future_manifold_max_shape_order"))],
            ["set_attr", "program", "future_manifold_multi_frame_risk_required", T(If(enabled, L(1.0), L(0.0)))],
        ],
    }


def materialize_learning_safety_context_rule():
    """Publish recoverability evidence for the generic risk gate.

    This is a graph contract, not a host-side override.  The context remains
    present when incomplete so diagnostics can distinguish an unsafe or
    undeclared environment from a missing projection.
    """
    development = "development"
    verified = Gt(
        P0(development, "safe_learning_environment_declared"), L(0.5)
    )
    return {
        "name": "ha_materialize_generic_learning_safety_context",
        "area": "generic_future_option_risk",
        "latency_class": "hard_realtime",
        "comment": "Publish graph-owned recovery evidence before the native "
        "future-manifold gate evaluates a candidate. Exploration budgets are "
        "ceilings: current support, load, pose, recovery latency and horizon "
        "determine the dimension-specific fraction actually available.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", development],
        ],
        "where": Eq(Count(Neighbours("episode", "has_learning_safety_context")), L(0.0)),
        "effects": [
            ["add_node", "safety", "LearningSafetyContext", {
                "verified": T(If(verified, L(1.0), L(0.0))),
                "reset_reachable": T(P0(development, "embodiment_reset_reachable")),
                "reset_cost_units": T(P0(development, "embodiment_reset_cost_units")),
                "protective_support_available": T(P0(development, "protective_support_available")),
                "protective_support_effectiveness": T(P0(development, "protective_support_effectiveness")),
                "recovery_path_count": T(Plus(
                    P0(development, "embodiment_reset_reachable"),
                    P0(development, "protective_support_available"),
                )),
                "required_horizon_units": T(P0(development, "safe_learning_required_horizon_units")),
                "minimum_width_relaxation": T(P0(development, "safe_learning_minimum_width_relaxation")),
                "information_loss_allowance": T(P0(development, "safe_learning_information_loss_allowance")),
                "exploration_width_budget": T(P0(development, "safe_learning_minimum_width_relaxation")),
                "exploration_information_budget": T(P0(development, "safe_learning_information_loss_allowance")),
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_learning_safety_context", "safety"],
        ],
    }


def establish_future_manifold_bounds_rule():
    """Derive the initial acceptable path tube from receipt-learned effects.

    The host supplies no limits and sees no candidate prediction.  Once the
    support-conditioned phase alphabet is familiar, the graph takes the
    componentwise envelope of its initialized, receipt-grounded local models.
    This licenses singleton-scale motion while requiring compound programs to
    preserve the same learned path width.
    """
    models = Filter(
        Neighbours("episode", "has_humanoid_phase_action_model"),
        "candidate",
        And(
            Gt(P0("candidate", "initialized"), L(0.5)),
            Gt(P0("candidate", "experience_count"), L(0.0)),
        ),
    )
    bounds = {
        key: MaxOver(
            models,
            "candidate",
            Abs(P0("candidate", f"mean_{key}")),
            L(0.0),
        )
        for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
    }
    safe_learning_projection_ready = Exists(
        Neighbours("episode", "has_learning_safety_context"),
        "learning_safety",
        Eq(P0("learning_safety", "verified"), L(1.0)),
    )
    projection_context_ready = Or(
        Gt(P0("episode", "phase_adaptation_complete"), L(0.5)),
        And(
            Gt(P0("episode", "developmental_curriculum_active"), L(0.5)),
            Eq(A("episode", "developmental_goal"), L("locomotion")),
        ),
        safe_learning_projection_ready,
    )
    return {
        "name": "ha_establish_future_manifold_bounds",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Gt(P0("policy", "future_manifold_enabled"), L(0.5)),
            Gt(P0("policy", "future_manifold_temporal_anchors_enabled"), L(0.5)),
            projection_context_ready,
            Eq(P0("episode", "manifold_bounds_ready"), L(0.0)),
            Gt(Count(models), L(0.0)),
        ),
        "effects": [
            *[
                ["set_attr", "episode", f"manifold_bound_{key}", T(bound)]
                for key, bound in bounds.items()
            ],
            ["set_attr", "episode", "manifold_bounds_ready", 1.0],
            [
                "set_attr",
                "episode",
                "manifold_bounds_provenance",
                "receipt_grounded_phase_action_envelope",
            ],
        ],
    }


def resume_motor_program_rule():
    return {
        "name": "ha_resume_yielded_motor_program_synthesis",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A mechanical scheduler may deliver the declared resume "
        "edge; only the graph clears its yield state and reopens synthesis.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("building")),
            Eq(P0("plan", "synthesis_yield_required"), L(1.0)),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "request_seq"),
            ),
        ),
        "effects": [[
            "set_attr",
            "plan",
            "synthesis_yield_required",
            0.0,
        ]],
    }


def retire_stale_motor_program_synthesis_rule():
    """Withdraw a losing synthesis channel before the next request.

    A somatomotor wave, recalled program, or other decision channel can make
    the episode action-ready while an ordinary analysis-by-synthesis program
    is still building.  Such a program is evidence from the old request, not
    work that may be resumed against a later sensed state.
    """
    return {
        "name": "ha_retire_stale_motor_program_synthesis",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -2,
        "batch": True,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_active_humanoid_motor_program",
                "plan",
            ],
        ],
        "where": And(
            Lt(P0("plan", "request_seq"), P0("episode", "request_seq")),
            Or(
                Eq(A("plan", "status"), L("building")),
                Eq(
                    A("plan", "status"),
                    L("somatomotor_wave_building"),
                ),
            ),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_active_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "resumes_humanoid_motor_program",
                "plan",
            ],
            ["set_attr", "plan", "status", "superseded"],
            [
                "set_attr",
                "plan",
                "supersession_reason",
                "competing_program_committed_for_request",
            ],
            [
                "set_attr",
                "plan",
                "superseded_at_request_seq",
                T(P0("episode", "request_seq")),
            ],
        ],
    }


def audit_takeoff_compound_frontier_rule():
    """Expose the live order-escalation preconditions before collapse."""
    return {
        "name": "ha_audit_takeoff_compound_frontier",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -2,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            [
                "development",
                "has_active_embodied_developmental_capability",
                "capability",
            ],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("building")),
            Eq(A("plan", "motor_task_context"), L("self_takeoff")),
            Eq(PI0("plan", "takeoff_compound_audit_ready"), L(0)),
        ),
        "effects": [
            ["set_attr", "plan", "takeoff_compound_audit_ready", 1],
            ["set_attr", "plan", "takeoff_compound_candidate_count", T(
                Count(compound_curiosity_candidates())
            )],
            ["set_attr", "plan", "takeoff_compound_allow_expansion", T(
                PI0("plan", "allow_expansion")
            )],
            ["set_attr", "plan", "takeoff_compound_failure_count", T(
                PI0("capability", "failure_count")
            )],
            ["set_attr", "plan", "takeoff_compound_success_count", T(
                PI0("capability", "success_count")
            )],
            ["set_attr", "plan", "takeoff_compound_evidence_window", T(
                PI0("development", "development_evidence_window")
            )],
            ["set_attr", "plan", "takeoff_compound_target_order", T(
                compound_curiosity_target_order()
            )],
        ],
    }


def persistent_compound_curiosity_residual():
    persistent_locomotion_residual = And(
        Eq(A("plan", "motor_task_context"), L("locomotion")),
        Eq(PI0("episode", "locomotion_drive_active"), L(1)),
        Gt(PI0("episode", "locomotion_residual_m"), L(0)),
        Gt(PI0("episode", "gait_surprise_streak"), L(0)),
        Not(Lt(
            PI0("episode", "gait_surprise_streak"),
            PI0("policy", "gait_surprise_confirmation_receipts"),
        )),
    )
    persistent_takeoff_residual = And(
        Eq(A("plan", "motor_task_context"), L("self_takeoff")),
        Gt(PI0("episode", "self_takeoff_drive_active"), L(0)),
        Exists(
            Neighbours("episode", "projects_embodied_development"),
            "compound_development",
            Exists(
                Neighbours(
                    "compound_development",
                    "has_active_embodied_developmental_capability",
                ),
                "compound_capability",
                And(
                    Eq(
                        A("compound_capability", "evidence_kind"),
                        L("support_reducing_elevation"),
                    ),
                    Lt(
                        PI0("compound_capability", "success_count"),
                        PI0(
                            "compound_development",
                            "development_evidence_window",
                        ),
                    ),
                    Not(Lt(
                        PI0("compound_capability", "failure_count"),
                        PI0(
                            "compound_development",
                            "development_evidence_window",
                        ),
                    )),
                ),
            ),
        ),
    )
    return Or(persistent_locomotion_residual, persistent_takeoff_residual)


def open_compound_curiosity_selection_rule():
    selected_edges = Neighbours(
        "plan", "has_selected_humanoid_compound_curiosity_candidate"
    )
    return {
        "name": "ha_open_persistent_compound_curiosity_selection",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -4,
        "batch": False,
        "comment": "Persistent task residual opens an explicit candidate "
        "comparison lease; ordinary fixpoints do not join the full phase "
        "alphabet to every building program.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
            ["plan", "has_humanoid_motor_program_frontier", "frontier"],
            ["plan", "includes_humanoid_phase_action_model", "primary"],
        ],
        "where": And(
            Or(
                Eq(PI0("policy", "native_humanoid_composition_enabled"), L(0)),
                Eq(PI0("episode", "self_takeoff_drive_active"), L(0)),
            ),
            Eq(A("plan", "status"), L("building")),
            Eq(A("frontier", "status"), L("open")),
            Eq(PI0("plan", "synthesis_yield_required"), L(0)),
            Eq(PI0("plan", "request_seq"), PI0("episode", "request_seq")),
            Eq(PI0("plan", "allow_expansion"), L(1)),
            Lt(PI0("plan", "member_count"), compound_curiosity_target_order()),
            Eq(PI0("policy", "persistent_task_residual_authority"), L(1)),
            Eq(PI0("episode", "sensorimotor_interrupt_required"), L(0)),
            Eq(PI0("episode", "reset_requested"), L(0)),
            persistent_compound_curiosity_residual(),
            Eq(A("primary", "token"), A("plan", "primary_token")),
            Eq(Count(selected_edges), L(0)),
            Lt(
                PI0("plan", "compound_curiosity_candidate_audit_seq"),
                PI0("episode", "request_seq"),
            ),
            Eq(Count(Neighbours(
                "plan", "has_open_compound_curiosity_selection"
            )), L(0)),
        ),
        "effects": [[
            "add_edge", "plan", "has_open_compound_curiosity_selection", "episode",
        ]],
    }


def select_compound_curiosity_candidate_rule():
    """Select the least-understood compatible pair after persistent surprise."""
    candidates = compound_curiosity_candidates()
    selected = Argmin(
        candidates,
        "curiosity_option",
        compound_pair_experience("plan", "curiosity_option"),
        V("plan"),
    )
    selected_edges = Neighbours(
        "plan",
        "has_selected_humanoid_compound_curiosity_candidate",
    )
    return {
        "name": "ha_curiosity_selects_persistent_singleton_compound",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -3,
        "comment": "When a smaller assembly repeatedly leaves its task "
        "residual open, choose the compatible next effector with least "
        "receipt experience. Locomotion uses confirmed prediction surprise; a "
        "self-takeoff task uses a complete failed developmental evidence "
        "window. The candidate alphabet, "
        "independent effector groups, context and receipt-backed pair "
        "compatibility all come from the graph. Support and load remain "
        "learned tradeoffs unless a material interrupt is present; there is "
        "no body-specific width or action-count schedule.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
            ["plan", "has_open_compound_curiosity_selection", "episode"],
            [
                "plan",
                "has_humanoid_motor_program_frontier",
                "frontier",
            ],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "candidate",
            ],
        ],
        "where": And(
            Eq(A("plan", "status"), L("building")),
            Eq(A("frontier", "status"), L("open")),
            Eq(
                PI0("plan", "request_seq"),
                PI0("episode", "request_seq"),
            ),
            Eq(V("candidate"), selected),
            Eq(Count(selected_edges), L(0)),
        ),
        "effects": [
            [
                "set_attr", "plan",
                "compound_curiosity_pre_expansion_candidate_count",
                T(Count(candidates)),
            ],
            [
                "set_attr",
                "plan",
                "compound_curiosity_pair_experience",
                T(compound_pair_experience("plan", "candidate")),
            ],
            [
                "add_edge",
                "plan",
                "has_selected_humanoid_compound_curiosity_candidate",
                "candidate",
            ],
            [
                "set_attr",
                "plan",
                "compound_selection_kind",
                "persistent_residual_surprise_curiosity",
            ],
            ["set_attr", "plan", "compound_curiosity_selection_count", T(
                Plus(PI0("plan", "compound_curiosity_selection_count"), L(1))
            )],
            [
                "del_edge", "plan",
                "has_open_compound_curiosity_selection", "episode",
            ],
        ],
    }


def close_empty_compound_curiosity_selection_rule():
    return {
        "name": "ha_close_empty_compound_curiosity_selection",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -2,
        "batch": False,
        "comment": "An empty compatible alphabet is negative evidence for "
        "this request and is reconsidered when the sensed request advances.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["plan", "has_open_compound_curiosity_selection", "episode"],
        ],
        "where": Eq(Count(compound_curiosity_candidates()), L(0)),
        "effects": [
            ["set_attr", "plan", "compound_curiosity_candidate_audit_seq", T(
                PI0("episode", "request_seq")
            )],
            [
                "del_edge", "plan",
                "has_open_compound_curiosity_selection", "episode",
            ],
        ],
    }


def expand_compound_curiosity_program_rule():
    """Turn a graph-selected intervention into an exact motor program."""
    keys = ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
    return {
        "name": "ha_curiosity_expands_exact_compound_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -2,
        "comment": "Commit the selected compatible effector into one exact "
        "order-N intervention. The ordinary receipt path then grounds the "
        "whole nonlinear program and refines every exact pair residual.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
            [
                "plan",
                "has_humanoid_motor_program_frontier",
                "frontier",
            ],
            [
                "plan",
                "has_selected_humanoid_compound_curiosity_candidate",
                "candidate",
            ],
        ],
        "where": And(
            Eq(A("plan", "status"), L("building")),
            Eq(A("frontier", "status"), L("open")),
            Eq(PI0("plan", "synthesis_yield_required"), L(0)),
            Eq(
                PI0("plan", "request_seq"),
                PI0("episode", "request_seq"),
            ),
            Eq(PI0("plan", "allow_expansion"), L(1)),
            Lt(
                PI0("plan", "member_count"),
                compound_curiosity_target_order(),
            ),
            Gt(
                Count(integer_exact_synergies(
                    Argmin(
                        bundle_members(),
                        "curiosity_primary_member",
                        PI0("curiosity_primary_member", "ordinal"),
                        V("plan"),
                    ),
                    "candidate",
                )),
                L(0),
            ),
        ),
        "effects": [
            ["set_attr", "frontier", "status", "expanded"],
            ["set_attr", "plan", "synthesis_yield_required", 1],
            [
                "del_edge",
                "episode",
                "resumes_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "plan",
                "has_selected_humanoid_compound_curiosity_candidate",
                "candidate",
            ],
            [
                "add_edge",
                "plan",
                "includes_humanoid_phase_action_model",
                "candidate",
            ],
            *[
                ["set_attr", "plan", f"sum_{key}", T(Plus(
                    PI0("plan", f"sum_{key}"),
                    PI0("candidate", f"mean_{key}"),
                ))]
                for key in keys
            ],
            *[
                [
                    "set_attr",
                    "plan",
                    f"interaction_sum_{key}",
                    T(Plus(
                        PI0("plan", f"interaction_sum_{key}"),
                        integer_candidate_pair_residual(
                            "plan", "candidate", key
                        ),
                    )),
                ]
                for key in keys
            ],
            ["set_attr", "plan", "member_count", T(Plus(
                PI0("plan", "member_count"),
                L(1),
            ))],
            ["add_node", "next_frontier", "HumanoidMotorProgramFrontier", {
                "generation": T(Plus(
                    PI0("frontier", "generation"),
                    L(1),
                )),
                "status": "open",
            }],
            [
                "add_edge",
                "plan",
                "has_humanoid_motor_program_frontier",
                "next_frontier",
            ],
        ],
    }


def expand_motor_program_rule():
    available = available_bundle_candidates()
    best = Argmin(
        available,
        "candidate_option",
        bundle_synthesis_cost("plan", "candidate_option"),
        V("plan"),
    )
    return {
        "name": "ha_abs_expand_motor_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Analysis-by-synthesis matching pursuit: add the "
        "independent primitive whose forward-synthesized body consequence "
        "most reduces residual error. Strict improvement and one primitive "
        "per discovered actuator group make arbitrary-width search finite.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
            [
                "plan",
                "has_humanoid_motor_program_frontier",
                "frontier",
            ],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "candidate",
            ],
        ],
        "where": And(
            Not(native_humanoid_composition_enabled()),
            Eq(A("plan", "status"), L("building")),
            Eq(A("frontier", "status"), L("open")),
            Eq(P0("plan", "synthesis_yield_required"), L(0.0)),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(P0("plan", "allow_expansion"), L(1.0)),
            Eq(A("candidate", "token"), AO(best, "token")),
            Eq(
                P0("candidate", "context_id"),
                N0(best, "context_id"),
            ),
            Eq(
                P0("candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Gt(P0("candidate", "initialized"), L(0.5)),
            Not(Exists(
                bundle_members(),
                "existing_member",
                Eq(
                    P0("existing_member", "actuator_group"),
                    P0("candidate", "actuator_group"),
                ),
            )),
            Lt(
                bundle_synthesis_cost("plan", "candidate"),
                bundle_synthesis_cost("plan"),
            ),
        ),
        "effects": [
            ["set_attr", "frontier", "status", "expanded"],
            ["set_attr", "plan", "synthesis_yield_required", 1.0],
            [
                "del_edge",
                "episode",
                "resumes_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "plan",
                "includes_humanoid_phase_action_model",
                "candidate",
            ],
            *[
                ["set_attr", "plan", f"sum_{key}", T(Plus(
                    P0("plan", f"sum_{key}"),
                    P0("candidate", f"mean_{key}"),
                ))]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            *[
                ["set_attr", "plan", f"interaction_sum_{key}", T(Plus(
                    P0("plan", f"interaction_sum_{key}"),
                    candidate_pair_residual("plan", "candidate", key),
                ))]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "plan", "member_count", T(
                Plus(P0("plan", "member_count"), L(1.0))
            )],
            ["add_node", "next_frontier", "HumanoidMotorProgramFrontier", {
                "generation": T(Plus(
                    P0("frontier", "generation"),
                    L(1.0),
                )),
                "status": "open",
            }],
            [
                "add_edge",
                "plan",
                "has_humanoid_motor_program_frontier",
                "next_frontier",
            ],
        ],
    }


def native_expand_motor_program_rule():
    """Attach the exact native composition as one snapshot-parallel batch.

    MotorCompose computes the complete plan with the same support-local,
    synergy-aware cost as the interpreted cascade. The close rule reduces the
    selected member subgraph into sums and pair residuals after attachment, so
    no Python resume pump or interpreted global Argmin remains.
    """
    return {
        "name": "ha_native_expand_motor_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -1,
        "batch": True,
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
            ["episode", "has_humanoid_phase_action_model", "candidate"],
        ],
        "where": And(
            native_humanoid_composition_enabled(),
            Eq(A("plan", "status"), L("building")),
            Not(Eq(
                A("plan", "compound_selection_kind"),
                L("persistent_residual_surprise_curiosity"),
            )),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(native_motor_compose_member(), L(1)),
            Not(Exists(
                bundle_members(),
                "existing_member",
                Eq(V("existing_member"), V("candidate")),
            )),
        ),
        "effects": [
            [
                "add_edge",
                "plan",
                "includes_humanoid_phase_action_model",
                "candidate",
            ],
            ["set_attr", "plan", "native_composition_attached", 1.0],
        ],
    }


def close_motor_program_rule():
    members = bundle_members()
    available = available_bundle_candidates()
    secondary_options = Filter(
        members,
        "member",
        Not(Eq(A("member", "token"), A("plan", "primary_token"))),
    )
    secondary = Argmin(
        secondary_options,
        "member",
        P0("member", "ordinal"),
        V("primary"),
    )
    effective_member_count = If(
        native_humanoid_composition_enabled(),
        Count(members),
        P0("plan", "member_count"),
    )

    def native_interaction_sum(key):
        return Sum(
            members,
            "left_member",
            Sum(
                Filter(
                    members,
                    "right_member",
                    Lt(
                        P0("left_member", "ordinal"),
                        P0("right_member", "ordinal"),
                    ),
                ),
                "right_member",
                N0(
                    Argmin(
                        approved_exact_synergies(
                            V("left_member"),
                            V("right_member"),
                        ),
                        "native_synergy",
                        P0("native_synergy", "ordinal"),
                        V("left_member"),
                    ),
                    f"residual_{key}",
                ),
            ),
        )

    command_frames = Max(
        L(1.0),
        If(
            Gt(effective_member_count, L(1.0)),
            IDiv(P0("episode", "response_frames"), L(2.0)),
            P0("episode", "response_frames"),
        ),
    )
    horizon_scale = Div(
        command_frames,
        P0("episode", "response_frames"),
    )
    pair_horizon_scale = If(
        Gt(effective_member_count, L(1.0)),
        L(1.0),
        L(0.0),
    )
    return {
        "name": "ha_abs_close_motor_program_at_synthesis_fixpoint",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Close the arbitrary motor program exactly when no "
        "remaining independent primitive improves its forward synthesis. "
        "Compound programs use the causally calibrated pair-probe horizon.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
            [
                "plan",
                "has_humanoid_motor_program_frontier",
                "frontier",
            ],
            [
                "plan",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
        ],
        "where": And(
            Eq(A("plan", "status"), L("building")),
            Eq(A("frontier", "status"), L("open")),
            Eq(P0("plan", "synthesis_yield_required"), L(0.0)),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(A("primary", "token"), A("plan", "primary_token")),
            Or(
                Not(Eq(
                    A("plan", "compound_selection_kind"),
                    L("persistent_residual_surprise_curiosity"),
                )),
                Not(compound_curiosity_can_expand()),
            ),
            Or(
                And(
                    native_humanoid_composition_enabled(),
                    Or(
                        Eq(
                            A("plan", "compound_selection_kind"),
                            L("persistent_residual_surprise_curiosity"),
                        ),
                        Eq(
                            P0("plan", "native_composition_attached"),
                            L(1.0),
                        ),
                        Not(Exists(
                            PHASE_MODELS,
                            "native_candidate",
                            And(
                                Eq(
                                    native_motor_compose_member(
                                        "native_candidate"
                                    ),
                                    L(1),
                                ),
                                Not(Exists(
                                    members,
                                    "native_member",
                                    Eq(
                                        V("native_member"),
                                        V("native_candidate"),
                                    ),
                                )),
                            ),
                        )),
                    ),
                ),
                And(
                    Not(native_humanoid_composition_enabled()),
                    Or(
                        Eq(P0("plan", "allow_expansion"), L(0.0)),
                        Not(Exists(
                            available,
                            "improving_candidate",
                            Lt(
                                bundle_synthesis_cost(
                                    "plan",
                                    "improving_candidate",
                                ),
                                bundle_synthesis_cost("plan"),
                            ),
                        )),
                    ),
                ),
            ),
        ),
        "effects": [
            ["set_attr", "plan", "member_count", T(
                effective_member_count
            )],
            ["set_attr", "plan", "compound_curiosity_terminal_candidate_count", T(
                Count(compound_curiosity_candidates())
            )],
            ["set_attr", "plan", "compound_curiosity_terminal_target_order", T(
                compound_curiosity_target_order()
            )],
            *[
                ["set_attr", "plan", f"sum_{key}", T(If(
                    native_humanoid_composition_enabled(),
                    Sum(
                        members,
                        "native_sum_member",
                        P0("native_sum_member", f"mean_{key}"),
                    ),
                    P0("plan", f"sum_{key}"),
                ))]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            *[
                ["set_attr", "plan", f"interaction_sum_{key}", T(If(
                    native_humanoid_composition_enabled(),
                    native_interaction_sum(key),
                    P0("plan", f"interaction_sum_{key}"),
                ))]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "frontier", "status", "closed"],
            ["set_attr", "plan", "status", "ready"],
            [
                "del_edge",
                "episode",
                "resumes_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "has_active_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "has_ready_humanoid_motor_program",
                "plan",
            ],
            ["set_attr", "plan", "response_frames", T(command_frames)],
            ["set_attr", "plan", "predicted_cost", T(
                If(
                    native_humanoid_composition_enabled(),
                    L(0.0),
                    bundle_synthesis_cost("plan"),
                )
            )],
            [
                "set_attr",
                "episode",
                "selected_secondary_token",
                T(AO(secondary, "token")),
            ],
            [
                "set_attr",
                "episode",
                "selected_response_frames",
                T(command_frames),
            ],
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    T(Plus(
                        Times(
                            horizon_scale,
                            If(
                                native_humanoid_composition_enabled(),
                                Sum(
                                    members,
                                    "native_prediction_member",
                                    P0(
                                        "native_prediction_member",
                                        f"mean_{key}",
                                    ),
                                ),
                                P0("plan", f"sum_{key}"),
                            ),
                        ),
                        Times(
                            pair_horizon_scale,
                            If(
                                native_humanoid_composition_enabled(),
                                native_interaction_sum(key),
                                P0("plan", f"interaction_sum_{key}"),
                            ),
                        ),
                    )),
                ]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "last_compound_decision_count", T(
                If(
                    Gt(effective_member_count, L(1.0)),
                    P0("episode", "decision_count"),
                    P0("episode", "last_compound_decision_count"),
                )
            )],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def project_takeoff_effort_ratio_rule():
    snapshot = A("plan", "takeoff_effort_projection_snapshot")
    supported = Nth(snapshot, 0)
    required = Nth(snapshot, 1)
    selected = Nth(snapshot, 2)
    residual = Nth(snapshot, 3)
    authorized = Nth(snapshot, 4)
    effect_keys = ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
    return {
        "name": "ha_project_least_takeoff_effort_inside_future_manifold",
        "area": "generic_future_option_risk",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": False,
        "comment": "After member synthesis, derive the target-to-predicted recruitment ratio and use it only when the complete scaled held program remains inside every foveated manifold bound. Unsupported or escaping proposals retain normal unit effort.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_ready_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("ready")),
            Eq(A("plan", "motor_task_context"), L("self_takeoff")),
            Eq(P0("plan", "request_seq"), P0("episode", "request_seq")),
            Not(Eq(
                P0("plan", "takeoff_effort_audit_seq"),
                P0("episode", "request_seq"),
            )),
        ),
        "effects": [
            ["set_attr", "plan", "takeoff_effort_projection_snapshot", T(
                takeoff_effort_projection()
            )],
            ["set_attr", "plan", "takeoff_effort_supported", T(supported)],
            ["set_attr", "plan", "takeoff_effort_required_ratio", T(required)],
            ["set_attr", "plan", "motor_effort_ratio", T(selected)],
            ["set_attr", "plan", "takeoff_effort_residual_ratio", T(residual)],
            ["set_attr", "plan", "takeoff_effort_authorized", T(authorized)],
            ["set_attr", "episode", "selected_motor_weight_a", T(selected)],
            ["set_attr", "episode", "selected_motor_weight_b", T(selected)],
            *[
                ["set_attr", "episode", f"selected_predicted_{key}", T(If(
                    Gt(supported, L(0)),
                    Nth(snapshot, 5 + index),
                    P0("episode", f"selected_predicted_{key}"),
                ))]
                for index, key in enumerate(effect_keys)
            ],
            ["set_attr", "plan", "takeoff_effort_audit_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def correction_pair_cost(primary, secondary):
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    predicted_z_x = Plus(
        body_z_x("episode", "state"),
        AO(primary, "mean_dzx"),
        AO(secondary, "mean_dzx"),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wy"),
                AO(primary, "mean_dwy"),
                AO(secondary, "mean_dwy"),
            ),
        ),
    )
    predicted_z_y = Minus(
        Plus(
            body_z_y("episode", "state"),
            AO(primary, "mean_dzy"),
            AO(secondary, "mean_dzy"),
        ),
        Times(
            lookahead,
            Plus(
                P0("episode", "state_wx"),
                AO(primary, "mean_dwx"),
                AO(secondary, "mean_dwx"),
            ),
        ),
    )
    return contextual_posture_cost(predicted_z_x, predicted_z_y)


def get_up_model_cost(model):
    """Focus one recovery consequence without adding unlike objectives."""
    normalized_height = Div(
        P0("episode", "state_z"),
        P0("episode", "standing_reference_z"),
    )
    alignment_deficit = Minus(
        L(1.0),
        body_z_z("episode", "state"),
    )
    height_deficit = Minus(
        P0("policy", "minimum_upright_height_fraction"),
        normalized_height,
    )
    ordinary_recovery = If(
        Gt(alignment_deficit, height_deficit),
        Minus(L(0.0), P0(model, "mean_alignment_gain")),
        Minus(L(0.0), P0(model, "mean_height_gain")),
    )
    return If(
        Eq(A("episode", "developmental_goal"), L("configuration_reversal")),
        Minus(L(0), PI0(model, "reversal_success_count")),
        If(
            Eq(
                A("episode", "developmental_goal"),
                L("surface_contact_mapping"),
            ),
            Minus(L(0), PI0(model, "support_topology_change_count")),
            If(
                Or(
                    Eq(
                        A("episode", "developmental_goal"),
                        L("segmental_stabilization"),
                    ),
                    Eq(
                        A("episode", "developmental_goal"),
                        L("reduced_support_equilibrium"),
                    ),
                ),
                Minus(L(0), PI0(model, "stable_partial_motion_count")),
                If(
        Eq(A("episode", "developmental_goal"), L("orientation_change")),
        Minus(L(0), Abs(PI0(model, "mean_alignment_gain"))),
        If(
            Eq(A("episode", "developmental_goal"), L("support_discovery")),
            Minus(L(0), PI0(model, "mean_whole_body_support_gain")),
            If(
                Eq(
                    A("episode", "developmental_goal"),
                    L("supported_translation"),
                ),
                Minus(L(0), PI0(model, "mean_translation_gain")),
                If(
                    Or(
                        Eq(A("episode", "developmental_goal"), L("height_gain")),
                        Eq(
                            A("episode", "developmental_goal"),
                            L("support_reducing_elevation"),
                        ),
                    ),
                    Minus(L(0), PI0(model, "mean_height_gain")),
                    ordinary_recovery,
                ),
            ),
        )))),
    )


def recovery_action_context_cost(action):
    """Focus one Pareto coordinate from the largest embodied deficit."""
    normalized_height = Div(
        P0("episode", "state_z"),
        P0("episode", "standing_reference_z"),
    )
    alignment_deficit = Minus(
        L(1.0),
        body_z_z("episode", "state"),
    )
    height_deficit = Minus(
        P0("policy", "minimum_upright_height_fraction"),
        normalized_height,
    )
    ordinary_recovery = If(
        And(
            Eq(P0("episode", "active_support_count"), L(0.0)),
            Eq(P0("episode", "state_contact_count_raw"), L(0.0)),
        ),
        Minus(L(0.0), N0(action, "mean_contact_gain")),
        If(
            Not(recovery_state_is_quiet()),
            Minus(L(0.0), N0(action, "mean_motion_reduction")),
            If(
                Gt(alignment_deficit, height_deficit),
                Minus(L(0.0), N0(action, "mean_alignment_gain")),
                Minus(L(0.0), N0(action, "mean_height_gain")),
            ),
        ),
    )
    return If(
        Eq(A("episode", "developmental_goal"), L("orientation_change")),
        Minus(L(0), Abs(PI0(action, "mean_alignment_gain"))),
        If(
            Eq(A("episode", "developmental_goal"), L("support_discovery")),
            Minus(L(0), PI0(action, "mean_whole_body_support_gain")),
            If(
                Eq(
                    A("episode", "developmental_goal"),
                    L("supported_translation"),
                ),
                Minus(L(0), PI0(action, "mean_translation_gain")),
                If(
                    Eq(A("episode", "developmental_goal"), L("height_gain")),
                    Minus(L(0), PI0(action, "mean_height_gain")),
                    ordinary_recovery,
                ),
            ),
        ),
    )


def recovery_focused_deficit():
    normalized_height = Div(
        P0("episode", "state_z"),
        P0("episode", "standing_reference_z"),
    )
    alignment_deficit = Minus(
        L(1.0),
        body_z_z("episode", "state"),
    )
    height_deficit = Minus(
        P0("policy", "minimum_upright_height_fraction"),
        normalized_height,
    )
    return If(
        Gt(alignment_deficit, height_deficit),
        alignment_deficit,
        height_deficit,
    )


def recovery_focused_gain(action):
    normalized_height = Div(
        P0("episode", "state_z"),
        P0("episode", "standing_reference_z"),
    )
    alignment_deficit = Minus(
        L(1.0),
        body_z_z("episode", "state"),
    )
    height_deficit = Minus(
        P0("policy", "minimum_upright_height_fraction"),
        normalized_height,
    )
    ordinary_gain = If(
        Gt(alignment_deficit, height_deficit),
        N0(action, "mean_alignment_gain"),
        N0(action, "mean_height_gain"),
    )
    return If(
        Eq(A("episode", "developmental_goal"), L("orientation_change")),
        Abs(PI0(action, "mean_alignment_gain")),
        If(
            Eq(A("episode", "developmental_goal"), L("support_discovery")),
            PI0(action, "mean_whole_body_support_gain"),
            If(
                Eq(
                    A("episode", "developmental_goal"),
                    L("supported_translation"),
                ),
                PI0(action, "mean_translation_gain"),
                ordinary_gain,
            ),
        ),
    )


def recovery_motion_energy(prefix):
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    return Plus(
        *[
            Times(
                Div(P0("outcome", f"{prefix}_{key}"), velocity_scale),
                Div(P0("outcome", f"{prefix}_{key}"), velocity_scale),
            )
            for key in ("vx", "vy", "vz")
        ],
        *[
            Times(
                Times(lookahead, P0("outcome", f"{prefix}_{key}")),
                Times(lookahead, P0("outcome", f"{prefix}_{key}")),
            )
            for key in ("wx", "wy")
        ],
    )


def recovery_current_motion_energy():
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    lookahead = Sqrt(Div(
        P0("episode", "standing_reference_z"),
        P0("policy", "gravity_acceleration"),
    ))
    return Plus(
        *[
            Times(
                Div(P0("episode", f"state_{key}"), velocity_scale),
                Div(P0("episode", f"state_{key}"), velocity_scale),
            )
            for key in ("vx", "vy", "vz")
        ],
        *[
            Times(
                Times(lookahead, P0("episode", f"state_{key}")),
                Times(lookahead, P0("episode", f"state_{key}")),
            )
            for key in ("wx", "wy")
        ],
    )


def recovery_state_is_quiet():
    one_tick_velocity = Times(
        P0("episode", "gravity_acceleration"),
        P0("episode", "physics_time_step"),
    )
    joint_velocity_budget = Times(
        Max(L(1.0), P0("episode", "state_joint_count")),
        one_tick_velocity,
        one_tick_velocity,
    )
    angular_budget = Div(
        one_tick_velocity,
        P0("episode", "standing_reference_z"),
    )
    return And(
        Lt(Abs(P0("episode", "state_vx")), one_tick_velocity),
        Lt(Abs(P0("episode", "state_vy")), one_tick_velocity),
        Lt(Abs(P0("episode", "state_vz")), one_tick_velocity),
        Lt(Abs(P0("episode", "state_wx")), angular_budget),
        Lt(Abs(P0("episode", "state_wy")), angular_budget),
        Lt(P0("episode", "state_joint_velocity_energy"), joint_velocity_budget),
    )


def recovery_basin_actions(basin="basin"):
    return Neighbours(basin, "has_humanoid_recovery_basin_action")


def recovery_basin_singletons(basin="basin"):
    return Filter(
        recovery_basin_actions(basin),
        "basin_action_candidate",
        Eq(P0("basin_action_candidate", "member_count"), L(1.0)),
    )


def recovery_support_count(prefix):
    return Plus(
        If(
            Gt(P0("outcome", f"{prefix}_support_0_force"), L(0.0)),
            L(1.0),
            L(0.0),
        ),
        If(
            Gt(P0("outcome", f"{prefix}_support_1_force"), L(0.0)),
            L(1.0),
            L(0.0),
        ),
    )


def recovery_support_gain():
    return Minus(recovery_support_count("post"), recovery_support_count("pre"))


def recovery_contact_gain():
    return Minus(
        P0("outcome", "contact_count"),
        P0("outcome", "pre_contact_count"),
    )


def recovery_whole_body_support_gain():
    return Minus(
        P0("outcome", "post_whole_body_support_count"),
        P0("outcome", "pre_whole_body_support_count"),
    )


def recovery_translation_gain():
    dx = Minus(P0("outcome", "post_x"), P0("outcome", "pre_x"))
    dy = Minus(P0("outcome", "post_y"), P0("outcome", "pre_y"))
    return Div(
        Sqrt(Plus(Times(dx, dx), Times(dy, dy))),
        P0("episode", "standing_reference_z"),
    )


def recovery_motion_reduction():
    return Minus(
        recovery_motion_energy("pre"),
        recovery_motion_energy("post"),
    )


def recovery_normalized_energy():
    return Div(
        P0("outcome", "input_energy_joules"),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
            P0("episode", "standing_reference_z"),
        ),
    )


def recovery_normalized_peak_load():
    return Div(
        P0("outcome", "peak_contact_force_newtons"),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
        ),
    )


RECOVERY_MAXIMIZE_FIELDS = (
    "mean_height_gain",
    "mean_alignment_gain",
    "mean_support_gain",
    "mean_contact_gain",
    "mean_motion_reduction",
    "mean_translation_gain",
    "mean_whole_body_support_gain",
)
RECOVERY_MINIMIZE_FIELDS = (
    "mean_normalized_energy",
    "mean_normalized_peak_load",
)


def recovery_action_dominated(candidate, basin="basin"):
    alternatives = Filter(
        recovery_basin_actions(basin),
        "recovery_alternative",
        And(
            Not(Eq(V("recovery_alternative"), candidate)),
            *[
                Not(Lt(
                    P0("recovery_alternative", field),
                    N0(candidate, field),
                ))
                for field in RECOVERY_MAXIMIZE_FIELDS
            ],
            *[
                Not(Gt(
                    P0("recovery_alternative", field),
                    N0(candidate, field),
                ))
                for field in RECOVERY_MINIMIZE_FIELDS
            ],
            Or(
                *[
                    Gt(
                        P0("recovery_alternative", field),
                        N0(candidate, field),
                    )
                    for field in RECOVERY_MAXIMIZE_FIELDS
                ],
                *[
                    Lt(
                        P0("recovery_alternative", field),
                        N0(candidate, field),
                    )
                    for field in RECOVERY_MINIMIZE_FIELDS
                ],
            ),
        ),
    )
    return Gt(Count(alternatives), L(0.0))


def recovery_action_frontier(basin="basin"):
    return Filter(
        recovery_basin_actions(basin),
        "recovery_frontier_candidate",
        Not(recovery_action_dominated(V("recovery_frontier_candidate"), basin)),
    )


def recovery_action_has_progress(action):
    return Or(*[
        Gt(N0(action, field), L(0.0))
        for field in RECOVERY_MAXIMIZE_FIELDS
    ])


def recovery_outcome_has_progress():
    return Or(
        Gt(
            Div(
                Minus(P0("outcome", "post_z"), P0("outcome", "pre_z")),
                P0("episode", "standing_reference_z"),
            ),
            L(0.0),
        ),
        Gt(
            Minus(
                body_z_z("outcome", "post"),
                body_z_z("outcome", "pre"),
            ),
            L(0.0),
        ),
        Gt(recovery_support_gain(), L(0.0)),
        Gt(recovery_contact_gain(), L(0.0)),
        Gt(recovery_motion_reduction(), L(0.0)),
        And(
            Eq(
                A("episode", "developmental_goal"),
                L("supported_translation"),
            ),
            Gt(recovery_translation_gain(), L(0)),
        ),
    )


def recovery_successor_is_dominated_by_previous():
    post_height = Div(
        P0("outcome", "post_z"),
        P0("episode", "standing_reference_z"),
    )
    post_alignment = body_z_z("outcome", "post")
    post_support = recovery_support_count("post")
    post_contact = P0("outcome", "contact_count")
    post_motion = recovery_motion_energy("post")
    return And(
        Not(Lt(P0("previous", "normalized_height"), post_height)),
        Not(Lt(P0("previous", "vertical_alignment"), post_alignment)),
        Not(Lt(P0("previous", "support_count"), post_support)),
        Not(Lt(P0("previous", "contact_count"), post_contact)),
        Not(Gt(P0("previous", "motion_energy"), post_motion)),
        Or(
            Gt(P0("previous", "normalized_height"), post_height),
            Gt(P0("previous", "vertical_alignment"), post_alignment),
            Gt(P0("previous", "support_count"), post_support),
            Gt(P0("previous", "contact_count"), post_contact),
            Lt(P0("previous", "motion_energy"), post_motion),
        ),
    )


def recovery_successor_has_postural_progress():
    return Or(
        Gt(
            Div(
                P0("outcome", "post_z"),
                P0("episode", "standing_reference_z"),
            ),
            P0("previous", "normalized_height"),
        ),
        Gt(
            body_z_z("outcome", "post"),
            P0("previous", "vertical_alignment"),
        ),
        Gt(
            recovery_support_count("post"),
            P0("previous", "support_count"),
        ),
        Gt(
            P0("outcome", "contact_count"),
            P0("previous", "contact_count"),
        ),
        And(
            Eq(
                A("episode", "developmental_goal"),
                L("supported_translation"),
            ),
            Gt(recovery_translation_gain(), L(0)),
        ),
    )


def recovery_outcome_approaches_program_target():
    """Keep target approach as a vector, allowing temporary tradeoffs.

    A recovery stage may exchange support, contact, or motion for height and
    alignment. Requiring every target distance to improve would silently
    scalarize that physical choice into a monotone safety gate.
    """
    pre_distances = (
        Abs(Minus(
            Div(
                P0("outcome", "pre_z"),
                P0("episode", "standing_reference_z"),
            ),
            P0("program", "target_normalized_height"),
        )),
        Abs(Minus(
            body_z_z("outcome", "pre"),
            P0("program", "target_vertical_alignment"),
        )),
        Abs(Minus(
            recovery_support_count("pre"),
            P0("program", "target_support_count"),
        )),
        Abs(Minus(
            P0("outcome", "pre_contact_count"),
            P0("program", "target_contact_count"),
        )),
        Abs(Minus(
            recovery_motion_energy("pre"),
            P0("program", "target_motion_energy"),
        )),
    )
    post_distances = (
        Abs(Minus(
            Div(
                P0("outcome", "post_z"),
                P0("episode", "standing_reference_z"),
            ),
            P0("program", "target_normalized_height"),
        )),
        Abs(Minus(
            body_z_z("outcome", "post"),
            P0("program", "target_vertical_alignment"),
        )),
        Abs(Minus(
            recovery_support_count("post"),
            P0("program", "target_support_count"),
        )),
        Abs(Minus(
            P0("outcome", "contact_count"),
            P0("program", "target_contact_count"),
        )),
        Abs(Minus(
            recovery_motion_energy("post"),
            P0("program", "target_motion_energy"),
        )),
    )
    return Or(*[
            Lt(post_distance, pre_distance)
            for pre_distance, post_distance in zip(
                pre_distances,
                post_distances,
                strict=True,
            )
        ])


def recovery_outcome_dominated(basin="previous"):
    height_gain = Div(
        Minus(P0("outcome", "post_z"), P0("outcome", "pre_z")),
        P0("episode", "standing_reference_z"),
    )
    alignment_gain = Minus(
        body_z_z("outcome", "post"),
        body_z_z("outcome", "pre"),
    )
    alternatives = Filter(
        recovery_basin_actions(basin),
        "recovery_alternative",
        And(
            Not(Lt(P0("recovery_alternative", "mean_height_gain"), height_gain)),
            Not(Lt(
                P0("recovery_alternative", "mean_alignment_gain"),
                alignment_gain,
            )),
            Not(Lt(
                P0("recovery_alternative", "mean_support_gain"),
                recovery_support_gain(),
            )),
            Not(Lt(
                P0("recovery_alternative", "mean_contact_gain"),
                recovery_contact_gain(),
            )),
            Not(Lt(
                P0("recovery_alternative", "mean_motion_reduction"),
                recovery_motion_reduction(),
            )),
            Not(Gt(
                P0("recovery_alternative", "mean_normalized_energy"),
                recovery_normalized_energy(),
            )),
            Not(Gt(
                P0("recovery_alternative", "mean_normalized_peak_load"),
                recovery_normalized_peak_load(),
            )),
            Or(
                Gt(P0("recovery_alternative", "mean_height_gain"), height_gain),
                Gt(
                    P0("recovery_alternative", "mean_alignment_gain"),
                    alignment_gain,
                ),
                Gt(
                    P0("recovery_alternative", "mean_support_gain"),
                    recovery_support_gain(),
                ),
                Gt(
                    P0("recovery_alternative", "mean_contact_gain"),
                    recovery_contact_gain(),
                ),
                Gt(
                    P0("recovery_alternative", "mean_motion_reduction"),
                    recovery_motion_reduction(),
                ),
                Lt(
                    P0("recovery_alternative", "mean_normalized_energy"),
                    recovery_normalized_energy(),
                ),
                Lt(
                    P0("recovery_alternative", "mean_normalized_peak_load"),
                    recovery_normalized_peak_load(),
                ),
            ),
        ),
    )
    return Gt(Count(alternatives), L(0.0))


def untried_recovery_models(basin="basin"):
    return Filter(
        GET_UP_MODELS,
        "get_up_candidate",
        Not(Exists(
            recovery_basin_singletons(basin),
            "tried_action",
            Eq(
                A("tried_action", "primary_token"),
                A("get_up_candidate", "token"),
            ),
        )),
    )


def mint_recovery_basin_rule():
    return {
        "name": "ha_mint_situated_recovery_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "On entry to fallen-body recovery, anchor a temporary "
        "basin to the sensed configuration and dimensionless body state. "
        "The basin is a situated search frame, not a canonical posture.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(Count(CURRENT_RECOVERY_BASINS), L(0.0)),
        ),
        "effects": [
            ["add_node", "basin", "HumanoidRecoveryBasin", {
                "ordinal": T(Plus(
                    P0("episode", "recovery_basin_count"),
                    L(1.0),
                )),
                "status": "candidate",
                "configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "normalized_height": T(Div(
                    P0("episode", "state_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "vertical_alignment": T(body_z_z("episode", "state")),
                "support_count": T(P0("episode", "active_support_count")),
                "contact_count": T(P0("episode", "state_contact_count_raw")),
                "motion_energy": T(Plus(
                    Times(
                        P0("episode", "state_vx"),
                        P0("episode", "state_vx"),
                    ),
                    Times(
                        P0("episode", "state_vy"),
                        P0("episode", "state_vy"),
                    ),
                    Times(
                        P0("episode", "state_vz"),
                        P0("episode", "state_vz"),
                    ),
                )),
                "visit_count": 1.0,
                "transition_confirmed": 1.0,
                "warm_start_tested": 1.0,
                "composition_settling_tested": 0.0,
                "reanchor_after_request_seq": T(
                    P0("episode", "request_seq")
                ),
                "request_seq": T(P0("episode", "request_seq")),
            }],
            [
                "add_edge", "episode", "has_humanoid_recovery_basin", "basin"
            ],
            [
                "add_edge",
                "episode",
                "has_current_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "episode", "recovery_basin_count", T(Plus(
                P0("episode", "recovery_basin_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_basin_start_attempt", T(
                P0("episode", "get_up_attempt_count")
            )],
        ],
    }


def recall_shape_recovery_basin_rule():
    stored = Neighbours("shape", "stores_humanoid_recovery_basin")
    useful = Filter(
        stored,
        "stored_basin_candidate",
        Exists(
            recovery_basin_actions("stored_basin_candidate"),
            "stored_action_candidate",
            recovery_action_has_progress("stored_action_candidate"),
        ),
    )
    nearest = Argmin(
        useful,
        "stored_basin_candidate",
        Plus(
            Abs(Minus(
                Div(
                    P0("episode", "state_z"),
                    P0("episode", "standing_reference_z"),
                ),
                P0("stored_basin_candidate", "normalized_height"),
            )),
            Abs(Minus(
                body_z_z("episode", "state"),
                P0("stored_basin_candidate", "vertical_alignment"),
            )),
        ),
        V("basin"),
    )
    return {
        "name": "ha_recall_shape_indexed_recovery_basin_hint",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A settled fallen body recalls the closest useful recovery "
        "basin held by its exact decoded body shape. A transient falling sample "
        "is not an indexing frame. The recalled basin is "
        "only a search hint: its action must earn a fresh receipt from the "
        "present configuration and load.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["shape", "stores_humanoid_recovery_basin", "stored_basin"],
        ],
        "where": And(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(A("basin", "status"), L("situated")),
            Eq(P0("basin", "warm_start_tested"), L(1.0)),
            Eq(Count(Neighbours(
                "basin", "inherits_humanoid_recovery_actions_from"
            )), L(0.0)),
            Gt(Count(useful), L(0.0)),
            Eq(V("stored_basin"), nearest),
        ),
        "effects": [
            [
                "add_edge",
                "basin",
                "inherits_humanoid_recovery_actions_from",
                "stored_basin",
            ],
            ["set_attr", "basin", "warm_start_tested", 0.0],
            ["set_attr", "basin", "source", "shape_recovery_warm_start"],
        ],
    }


def store_recovery_basin_by_body_shape_rule():
    stored = Neighbours("shape", "stores_humanoid_recovery_basin")
    return {
        "name": "ha_store_recovery_basin_by_body_shape",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "At the explicit lifetime boundary, retain situated "
        "recovery basins with a receipt-positive action under the already "
        "decoded body shape. This reuses the motor library's morphology "
        "index instead of introducing a canonical home pose.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            ["episode", "has_humanoid_recovery_basin", "basin"],
        ],
        "where": And(
            Eq(P0("episode", "library_consolidation_requested"), L(1.0)),
            Eq(A("basin", "status"), L("situated")),
            Exists(
                recovery_basin_actions(),
                "basin_action_candidate",
                And(
                    recovery_action_has_progress("basin_action_candidate"),
                    Not(recovery_action_dominated(
                        V("basin_action_candidate"),
                        "basin",
                    )),
                ),
            ),
            Not(Exists(
                stored,
                "stored_basin_candidate",
                Eq(V("stored_basin_candidate"), V("basin")),
            )),
        ),
        "effects": [
            [
                "add_edge",
                "shape",
                "stores_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "basin", "shape_indexed", 1.0],
            ["set_attr", "basin", "source", "experience"],
        ],
    }


def settle_recovery_basin_rule():
    post_support = Plus(
        If(Gt(P0("outcome", "post_support_0_force"), L(0.0)), L(1.0), L(0.0)),
        If(Gt(P0("outcome", "post_support_1_force"), L(0.0)), L(1.0), L(0.0)),
    )
    pre_support = Plus(
        If(Gt(P0("outcome", "pre_support_0_force"), L(0.0)), L(1.0), L(0.0)),
        If(Gt(P0("outcome", "pre_support_1_force"), L(0.0)), L(1.0), L(0.0)),
    )
    return {
        "name": "ha_settle_candidate_recovery_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "The first fallen sample is not yet a stable posture. "
        "Hold it as a candidate until a verified receipt shows dissipating "
        "motion or increased support, then anchor the basin to that sensed "
        "state without inventing a home configuration.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "starts_from_humanoid_recovery_basin", "basin"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("basin", "status"), L("candidate")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Or(
                recovery_state_is_quiet(),
                Gt(post_support, pre_support),
            ),
        ),
        "effects": [
            ["set_attr", "basin", "status", "situated"],
            ["set_attr", "basin", "configuration_shape", T(
                A("outcome", "post_motor_configuration_shape")
            )],
            ["set_attr", "basin", "normalized_height", T(Div(
                P0("outcome", "post_z"),
                P0("episode", "standing_reference_z"),
            ))],
            ["set_attr", "basin", "vertical_alignment", T(
                body_z_z("outcome", "post")
            )],
            ["set_attr", "basin", "support_count", T(post_support)],
            ["set_attr", "basin", "contact_count", T(
                P0("outcome", "contact_count")
            )],
            ["set_attr", "basin", "motion_energy", T(
                recovery_motion_energy("post")
            )],
            ["set_attr", "basin", "settled_request_seq", T(
                P0("trial", "request_seq")
            )],
        ],
    }


def link_recovery_trial_basin_rule():
    return {
        "name": "ha_bind_recovery_trial_to_situated_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode", "has_current_humanoid_recovery_basin", "basin"
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
        ],
        "where": And(
            Or(
                Eq(A("trial", "decision_kind"), L("get_up_explore")),
                Eq(A("trial", "decision_kind"), L("get_up_exploit")),
                Eq(A("trial", "decision_kind"), L("get_up_program")),
                Eq(A("trial", "decision_kind"), L("get_up_reanchor")),
            ),
            Eq(P0("trial", "request_seq"), P0("episode", "request_seq")),
            Eq(
                Count(Neighbours(
                    "trial", "starts_from_humanoid_recovery_basin"
                )),
                L(0.0),
            ),
        ),
        "effects": [[
            "add_edge", "trial", "starts_from_humanoid_recovery_basin", "basin"
        ]],
    }


def update_active_recovery_program_rule():
    target_relative = Or(
        Eq(
            A("program", "termination_kind"),
            L("stored_successor_approach_or_pareto_loss"),
        ),
        Eq(
            A("program", "termination_kind"),
            L("stored_launch_approach_or_pareto_loss"),
        ),
        Eq(
            A("program", "termination_kind"),
            L("basin_reanchor_or_pareto_loss"),
        ),
    )
    settling = Eq(
        A("program", "termination_kind"),
        L("settle_until_quiet"),
    )
    relevant_progress = Or(
        And(
            target_relative,
            recovery_outcome_approaches_program_target(),
        ),
        And(
            settling,
            Not(recovery_state_is_quiet()),
            Gt(recovery_motion_reduction(), L(0.0)),
        ),
        And(
            Not(Or(target_relative, settling)),
            recovery_outcome_has_progress(),
        ),
    )
    progress = And(
        relevant_progress,
        Not(recovery_outcome_dominated("basin")),
    )
    return {
        "name": "ha_update_condition_terminated_recovery_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Keep an option open while fresh receipts remain on its "
        "non-dominated successor approach; otherwise terminate it.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_recovery_program", "program"],
            ["program", "starts_from_humanoid_recovery_basin", "basin"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "starts_from_humanoid_recovery_basin", "basin"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Or(
                Eq(A("program", "status"), L("armed")),
                Eq(A("program", "status"), L("active")),
            ),
            Or(
                Eq(A("trial", "decision_kind"), L("get_up_exploit")),
                Eq(A("trial", "decision_kind"), L("get_up_program")),
                Eq(A("trial", "decision_kind"), L("get_up_reanchor")),
            ),
            Eq(A("trial", "token"), A("program", "primary_token")),
            Eq(
                A("trial", "secondary_token"),
                A("program", "secondary_token"),
            ),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "recovery_program_evaluated"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "program", "last_receipt_progress", T(If(
                progress, L(1.0), L(0.0)
            ))],
            ["set_attr", "program", "status", T(If(
                progress, L("active"), L("terminated")
            ))],
            ["set_attr", "program", "last_request_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "program", "repeat_count", T(Plus(
                P0("program", "repeat_count"), L(1.0)
            ))],
            ["set_attr", "outcome", "recovery_program_evaluated", 1.0],
        ],
    }


def retire_recovery_program_rule():
    return {
        "name": "ha_retire_condition_terminated_recovery_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_recovery_program", "program"],
            ["program", "starts_from_humanoid_recovery_basin", "basin"],
        ],
        "where": Or(
            Eq(A("program", "status"), L("terminated")),
            Eq(P0("episode", "upright"), L(1.0)),
            Not(Exists(
                CURRENT_RECOVERY_BASINS,
                "current_recovery_basin",
                Eq(V("current_recovery_basin"), V("basin")),
            )),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_active_humanoid_recovery_program",
                "program",
            ],
            ["set_attr", "program", "status", "retained"],
            ["set_attr", "episode", "selected_motor_weight_a", 1.0],
            ["set_attr", "episode", "selected_motor_weight_b", 1.0],
            ["set_attr", "basin", "composition_settling_tested", 0.0],
            ["set_attr", "episode", "recovery_program_termination_count", T(
                Plus(
                    P0("episode", "recovery_program_termination_count"),
                    L(1.0),
                )
            )],
        ],
    }


def continue_recovery_program_rule():
    return {
        "name": "ha_continue_condition_terminated_recovery_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["episode", "has_active_humanoid_recovery_program", "program"],
            ["program", "starts_from_humanoid_recovery_basin", "basin"],
        ],
        "where": And(
            Eq(A("program", "status"), L("active")),
            Eq(P0("program", "last_receipt_progress"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                A("program", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("program", "secondary_token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("program", "response_frames")
            )],
            ["set_attr", "episode", "selected_motor_weight_a", T(
                P0("program", "motor_weight_a")
            )],
            ["set_attr", "episode", "selected_motor_weight_b", T(
                P0("program", "motor_weight_b")
            )],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", T(If(
                Eq(
                    A("program", "execution_decision_kind"),
                    L("get_up_reanchor"),
                ),
                L("get_up_reanchor"),
                L("get_up_program"),
            ))],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_program_repeat_count", T(Plus(
                P0("episode", "recovery_program_repeat_count"), L(1.0)
            ))],
        ],
    }


def choose_recovery_basin_reanchor_rule():
    return {
        "name": "ha_reanchor_between_situated_recovery_probes",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "After a local singleton probe displaces a retained "
        "recovery posture, replay the receipt-backed option that established "
        "that basin before probing another opaque effector. The basin is an "
        "observed experimental frame, not a canonical body pose; fresh "
        "receipts terminate an unsuccessful return.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["episode", "has_humanoid_motor_trial", "probe"],
            ["probe", "starts_from_humanoid_recovery_basin", "basin"],
            ["probe", "has_humanoid_transition", "probe_outcome"],
        ],
        "where": And(
            Eq(A("probe", "decision_kind"), L("get_up_explore")),
            Gt(
                P0("probe", "request_seq"),
                P0("basin", "reanchor_after_request_seq"),
            ),
            Eq(P0("probe_outcome", "receipt_verified"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(ACTIVE_RECOVERY_PROGRAMS), L(0.0)),
            Gt(Count(untried_recovery_models()), L(0.0)),
            Not(Eq(A("basin", "incoming_primary_token"), L(None))),
            Not(Eq(
                A("episode", "state_motor_configuration_shape"),
                A("basin", "configuration_shape"),
            )),
        ),
        "effects": [
            ["add_node", "program", "HumanoidRecoveryProgram", {
                "status": "armed",
                "termination_kind": "basin_reanchor_or_pareto_loss",
                "execution_decision_kind": "get_up_reanchor",
                "primary_token": T(A("basin", "incoming_primary_token")),
                "secondary_token": T(
                    A("basin", "incoming_secondary_token")
                ),
                "response_frames": T(P0("basin", "incoming_response_frames")),
                "motor_weight_a": T(Max(
                    L(1.0), P0("basin", "incoming_motor_weight_a")
                )),
                "motor_weight_b": T(Max(
                    L(1.0), P0("basin", "incoming_motor_weight_b")
                )),
                "last_receipt_progress": 0.0,
                "repeat_count": 0.0,
                "last_request_seq": T(P0("episode", "request_seq")),
                "launch_configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "target_normalized_height": T(
                    P0("basin", "normalized_height")
                ),
                "target_vertical_alignment": T(
                    P0("basin", "vertical_alignment")
                ),
                "target_support_count": T(P0("basin", "support_count")),
                "target_contact_count": T(P0("basin", "contact_count")),
                "target_motion_energy": T(P0("basin", "motion_energy")),
            }],
            [
                "add_edge", "episode",
                "has_active_humanoid_recovery_program", "program",
            ],
            [
                "add_edge", "basin",
                "has_humanoid_recovery_program", "program",
            ],
            [
                "add_edge", "program",
                "starts_from_humanoid_recovery_basin", "basin",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("basin", "incoming_primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("basin", "incoming_secondary_token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("basin", "incoming_response_frames")
            )],
            ["set_attr", "episode", "selected_motor_weight_a", T(Max(
                L(1.0), P0("basin", "incoming_motor_weight_a")
            ))],
            ["set_attr", "episode", "selected_motor_weight_b", T(Max(
                L(1.0), P0("basin", "incoming_motor_weight_b")
            ))],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_reanchor"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_program_count", T(Plus(
                P0("episode", "recovery_program_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_reanchor_count", T(Plus(
                P0("episode", "recovery_reanchor_count"), L(1.0)
            ))],
            ["set_attr", "basin", "reanchor_after_request_seq", T(
                P0("probe", "request_seq")
            )],
        ],
    }


def choose_basin_get_up_exploration_rule():
    untried = untried_recovery_models()
    best = Argmin(
        untried,
        "get_up_candidate",
        P0("get_up_candidate", "ordinal"),
        V("basin"),
    )
    return {
        "name": "ha_explore_situated_recovery_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Explore the opaque actuator alphabet again after a "
        "receipt-confirmed change of recovery basin. Effects are local to "
        "the current body state instead of being smeared across all falls.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode", "has_current_humanoid_recovery_basin", "basin"
            ],
            [
                "episode", "has_humanoid_get_up_action_model", "get_up_model"
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Gt(Count(untried), L(0.0)),
            Eq(P0("get_up_model", "ordinal"), N0(best, "ordinal")),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                A("get_up_model", "token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("get_up_model", "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("episode", "nominal_response_frames")
            )],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_explore"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
        ],
    }


def route_recalled_recovery_successor_rule():
    return {
        "name": "ha_route_recalled_recovery_successor",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "When a warm lifetime reproduces a retained transition, "
        "route its new live basin to the stored successor frontier. The stored "
        "actions remain hints and require fresh receipts.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["basin", "inherits_humanoid_recovery_actions_from", "live_previous"],
            [
                "live_previous",
                "inherits_humanoid_recovery_actions_from",
                "stored_previous",
            ],
            [
                "stored_previous",
                "continues_to_humanoid_recovery_basin",
                "stored_successor",
            ],
        ],
        "where": And(
            Eq(
                A("basin", "configuration_shape"),
                A("stored_successor", "configuration_shape"),
            ),
            Eq(
                P0("basin", "support_count"),
                P0("stored_successor", "support_count"),
            ),
            Not(Lt(
                P0("basin", "contact_count"),
                P0("stored_successor", "contact_count"),
            )),
            Not(Gt(
                P0("basin", "motion_energy"),
                P0("stored_successor", "motion_energy"),
            )),
        ),
        "effects": [
            [
                "del_edge",
                "basin",
                "inherits_humanoid_recovery_actions_from",
                "live_previous",
            ],
            [
                "add_edge",
                "basin",
                "inherits_humanoid_recovery_actions_from",
                "stored_successor",
            ],
            ["set_attr", "basin", "source", "recalled_recovery_path"],
            ["set_attr", "basin", "warm_start_tested", 0.0],
            ["set_attr", "episode", "recovery_path_recall_count", T(Plus(
                P0("episode", "recovery_path_recall_count"),
                L(1.0),
            ))],
        ],
    }


def choose_recalled_recovery_path_transition_rule():
    current_motion_energy = recovery_current_motion_energy()
    return {
        "name": "ha_test_recalled_recovery_path_transition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Test the compound that caused a retained successor edge "
        "when the live body re-enters its receipt-derived dynamical context. "
        "Decoded configuration, contact topology, and the observed normalized "
        "motion-energy ceiling gate release without a clock or canonical pose. "
        "It remains a hint: "
        "the present body and load must provide a fresh receipt.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["basin", "inherits_humanoid_recovery_actions_from", "stored_previous"],
            [
                "stored_previous",
                "continues_to_humanoid_recovery_basin",
                "stored_successor",
            ],
        ],
        "where": And(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(ACTIVE_RECOVERY_PROGRAMS), L(0.0)),
            Eq(P0("basin", "warm_start_tested"), L(0.0)),
            Not(Eq(A("stored_successor", "incoming_primary_token"), L(None))),
            Eq(
                A("episode", "state_motor_configuration_shape"),
                A("stored_successor", "incoming_configuration_shape"),
            ),
            Eq(
                P0("episode", "active_support_count"),
                P0("stored_successor", "incoming_support_count"),
            ),
            Eq(
                P0("episode", "state_contact_count_raw"),
                P0("stored_successor", "incoming_contact_count"),
            ),
            Not(Gt(
                current_motion_energy,
                P0("stored_successor", "incoming_motion_energy"),
            )),
        ),
        "effects": [
            ["add_node", "program", "HumanoidRecoveryProgram", {
                "status": "armed",
                "termination_kind": "stored_successor_approach_or_pareto_loss",
                "primary_token": T(
                    A("stored_successor", "incoming_primary_token")
                ),
                "secondary_token": T(
                    A("stored_successor", "incoming_secondary_token")
                ),
                "response_frames": T(
                    P0("stored_successor", "incoming_response_frames")
                ),
                "motor_weight_a": T(Max(
                    L(1.0),
                    P0("stored_successor", "incoming_motor_weight_a"),
                )),
                "motor_weight_b": T(Max(
                    L(1.0),
                    P0("stored_successor", "incoming_motor_weight_b"),
                )),
                "last_receipt_progress": 0.0,
                "repeat_count": 0.0,
                "last_request_seq": T(P0("episode", "request_seq")),
                "launch_configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "launch_normalized_height": T(Div(
                    P0("episode", "state_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "launch_vertical_alignment": T(
                    body_z_z("episode", "state")
                ),
                "launch_support_count": T(
                    P0("episode", "active_support_count")
                ),
                "launch_contact_count": T(
                    P0("episode", "state_contact_count_raw")
                ),
                "launch_motion_energy": T(current_motion_energy),
                "target_normalized_height": T(
                    P0("stored_successor", "normalized_height")
                ),
                "target_vertical_alignment": T(
                    P0("stored_successor", "vertical_alignment")
                ),
                "target_support_count": T(
                    P0("stored_successor", "support_count")
                ),
                "target_contact_count": T(
                    P0("stored_successor", "contact_count")
                ),
                "target_motion_energy": T(
                    P0("stored_successor", "motion_energy")
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_recovery_program",
                "program",
            ],
            [
                "add_edge",
                "basin",
                "has_humanoid_recovery_program",
                "program",
            ],
            [
                "add_edge",
                "program",
                "starts_from_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("stored_successor", "incoming_primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("stored_successor", "incoming_secondary_token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("stored_successor", "incoming_response_frames")
            )],
            ["set_attr", "episode", "selected_motor_weight_a", T(Max(
                L(1.0),
                P0("stored_successor", "incoming_motor_weight_a"),
            ))],
            ["set_attr", "episode", "selected_motor_weight_b", T(Max(
                L(1.0),
                P0("stored_successor", "incoming_motor_weight_b"),
            ))],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_exploit"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_warm_start_count", T(Plus(
                P0("episode", "recovery_warm_start_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_path_hint_count", T(Plus(
                P0("episode", "recovery_path_hint_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_program_count", T(Plus(
                P0("episode", "recovery_program_count"), L(1.0)
            ))],
            ["set_attr", "basin", "warm_start_tested", 1.0],
        ],
    }


def choose_recovery_basin_warm_start_rule():
    inherited_actions = recovery_basin_actions("previous")
    frontier = Filter(
        inherited_actions,
        "warm_frontier_candidate",
        And(
            recovery_action_has_progress("warm_frontier_candidate"),
            Not(recovery_action_dominated(
                V("warm_frontier_candidate"),
                "previous",
            )),
        ),
    )
    best = Argmin(
        frontier,
        "warm_frontier_candidate",
        recovery_action_context_cost("warm_frontier_candidate"),
        V("previous"),
    )
    return {
        "name": "ha_test_prior_recovery_basin_hint",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A newly promoted recovery basin tests the best positive "
        "action from its predecessor once as an output-null warm-start hint. "
        "The new basin receives its own receipt; prior effects are not copied "
        "as facts about the new body state.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["basin", "inherits_humanoid_recovery_actions_from", "previous"],
            [
                "previous",
                "has_humanoid_recovery_basin_action",
                "hint_action",
            ],
        ],
        "where": And(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(ACTIVE_RECOVERY_PROGRAMS), L(0.0)),
            Eq(P0("basin", "warm_start_tested"), L(0.0)),
            Eq(Count(Neighbours(
                "previous",
                "continues_to_humanoid_recovery_basin",
            )), L(0.0)),
            Gt(Count(frontier), L(0.0)),
            Eq(V("hint_action"), best),
        ),
        "effects": [
            ["add_node", "program", "HumanoidRecoveryProgram", {
                "status": "armed",
                "termination_kind": "basin_exit_or_pareto_loss",
                "primary_token": T(A("hint_action", "primary_token")),
                "secondary_token": T(A("hint_action", "secondary_token")),
                "response_frames": T(P0("hint_action", "response_frames")),
                "motor_weight_a": T(Max(
                    L(1.0), P0("hint_action", "motor_weight_a")
                )),
                "motor_weight_b": T(Max(
                    L(1.0), P0("hint_action", "motor_weight_b")
                )),
                "last_receipt_progress": 0.0,
                "repeat_count": 0.0,
                "last_request_seq": T(P0("episode", "request_seq")),
                "launch_configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "launch_normalized_height": T(Div(
                    P0("episode", "state_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "launch_vertical_alignment": T(
                    body_z_z("episode", "state")
                ),
                "launch_support_count": T(
                    P0("episode", "active_support_count")
                ),
                "launch_contact_count": T(
                    P0("episode", "state_contact_count_raw")
                ),
                "launch_motion_energy": T(
                    recovery_current_motion_energy()
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_recovery_program",
                "program",
            ],
            [
                "add_edge",
                "basin",
                "has_humanoid_recovery_program",
                "program",
            ],
            [
                "add_edge",
                "program",
                "starts_from_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("hint_action", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("hint_action", "secondary_token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("hint_action", "response_frames")
            )],
            ["set_attr", "episode", "selected_motor_weight_a", T(Max(
                L(1.0), P0("hint_action", "motor_weight_a")
            ))],
            ["set_attr", "episode", "selected_motor_weight_b", T(Max(
                L(1.0), P0("hint_action", "motor_weight_b")
            ))],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_exploit"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_warm_start_count", T(Plus(
                P0("episode", "recovery_warm_start_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_program_count", T(Plus(
                P0("episode", "recovery_program_count"), L(1.0)
            ))],
            ["set_attr", "basin", "warm_start_tested", 1.0],
        ],
    }


def settle_before_recovery_composition_rule():
    tonic = Argmin(
        TONIC,
        "tonic_candidate",
        P0("tonic_candidate", "ordinal"),
        V("episode"),
    )
    return {
        "name": "ha_stabilize_before_recovery_composition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "After the local actuator survey, hold the present "
        "situated configuration while receipts show useful damping. This "
        "co-contraction stage separates settling from inverse-recruited "
        "postural movement without a clock or canonical pose.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            ["episode", "has_humanoid_action_model", "tonic_model"],
        ],
        "where": And(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(ACTIVE_RECOVERY_PROGRAMS), L(0.0)),
            Eq(Count(untried_recovery_models()), L(0.0)),
            Eq(P0("basin", "composition_settling_tested"), L(0.0)),
            Not(recovery_state_is_quiet()),
            Gt(Count(TONIC), L(0.0)),
            Eq(V("tonic_model"), tonic),
        ),
        "effects": [
            ["add_node", "program", "HumanoidRecoveryProgram", {
                "status": "armed",
                "termination_kind": "settle_until_quiet",
                "primary_token": T(A("tonic_model", "token")),
                "secondary_token": T(A("tonic_model", "token")),
                "response_frames": T(P0("episode", "nominal_response_frames")),
                "motor_weight_a": 1.0,
                "motor_weight_b": 1.0,
                "last_receipt_progress": 0.0,
                "repeat_count": 0.0,
                "last_request_seq": T(P0("episode", "request_seq")),
            }],
            [
                "add_edge", "episode",
                "has_active_humanoid_recovery_program", "program",
            ],
            [
                "add_edge", "basin",
                "has_humanoid_recovery_program", "program",
            ],
            [
                "add_edge", "program",
                "starts_from_humanoid_recovery_basin", "basin",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("tonic_model", "token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("tonic_model", "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("episode", "nominal_response_frames")
            )],
            ["set_attr", "episode", "selected_motor_weight_a", 1.0],
            ["set_attr", "episode", "selected_motor_weight_b", 1.0],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_exploit"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_program_count", T(Plus(
                P0("episode", "recovery_program_count"), L(1.0)
            ))],
            ["set_attr", "basin", "composition_settling_tested", 1.0],
        ],
    }


def select_recovery_composition_primary_rule():
    singletons = recovery_basin_singletons()
    frontier_singletons = Filter(
        singletons,
        "frontier_singleton",
        Not(recovery_action_dominated(V("frontier_singleton"))),
    )
    actions = recovery_basin_actions()
    primary = Argmin(
        frontier_singletons,
        "primary_candidate",
        recovery_action_context_cost("primary_candidate"),
        V("basin"),
    )
    compatible = Filter(
        singletons,
        "secondary_candidate",
        And(
            Not(Eq(
                A("secondary_candidate", "primary_token"),
                A("primary_action", "primary_token"),
            )),
            Not(Eq(
                P0("secondary_candidate", "primary_actuator_group"),
                P0("primary_action", "primary_actuator_group"),
            )),
            Not(Exists(
                actions,
                "pair_memory",
                And(
                    Eq(P0("pair_memory", "member_count"), L(2.0)),
                    Or(
                        And(
                            Eq(
                                A("pair_memory", "primary_token"),
                                A("primary_action", "primary_token"),
                            ),
                            Eq(
                                A("pair_memory", "secondary_token"),
                                A("secondary_candidate", "primary_token"),
                            ),
                        ),
                        And(
                            Eq(
                                A("pair_memory", "primary_token"),
                                A("secondary_candidate", "primary_token"),
                            ),
                            Eq(
                                A("pair_memory", "secondary_token"),
                                A("primary_action", "primary_token"),
                            ),
                        ),
                    ),
                ),
            )),
        ),
    )
    return {
        "name": "ha_select_recovery_composition_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Bind the context-selected Pareto primary once so the "
        "compound chooser avoids a Cartesian action-pair expansion.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
            [
                "basin",
                "has_humanoid_recovery_basin_action",
                "primary_action",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(ACTIVE_RECOVERY_PROGRAMS), L(0.0)),
            Eq(Count(SELECTED_RECOVERY_PRIMARIES), L(0.0)),
            Eq(Count(untried_recovery_models()), L(0.0)),
            Eq(V("primary_action"), primary),
            Gt(Count(compatible), L(0.0)),
        ),
        "effects": [[
            "add_edge",
            "episode",
            "has_selected_humanoid_recovery_primary",
            "primary_action",
        ]],
    }


def choose_basin_get_up_composition_rule():
    singletons = recovery_basin_singletons()
    actions = recovery_basin_actions()

    def pair_untried(primary_token, secondary_token):
        return Not(Exists(
            actions,
            "pair_memory",
            And(
                Eq(P0("pair_memory", "member_count"), L(2.0)),
                Or(
                    And(
                        Eq(A("pair_memory", "primary_token"), primary_token),
                        Eq(A("pair_memory", "secondary_token"), secondary_token),
                    ),
                    And(
                        Eq(A("pair_memory", "primary_token"), secondary_token),
                        Eq(A("pair_memory", "secondary_token"), primary_token),
                    ),
                ),
            ),
        ))

    compatible = Filter(
        singletons,
        "secondary_candidate",
        And(
            Not(Eq(
                A("secondary_candidate", "primary_token"),
                A("primary_action", "primary_token"),
            )),
            Not(Eq(
                P0("secondary_candidate", "primary_actuator_group"),
                P0("primary_action", "primary_actuator_group"),
            )),
            pair_untried(
                A("primary_action", "primary_token"),
                A("secondary_candidate", "primary_token"),
            ),
        ),
    )
    secondary = Argmin(
        compatible,
        "secondary_candidate",
        recovery_action_context_cost("secondary_candidate"),
        V("primary_action"),
    )
    response_frames = P0("episode", "nominal_response_frames")
    pair_focused_gain = Plus(
        recovery_focused_gain("primary_action"),
        recovery_focused_gain("secondary_action"),
    )
    inverse_recruitment = If(
        And(
            recovery_state_is_quiet(),
            Gt(P0("episode", "state_contact_count_raw"), L(0.0)),
            Gt(pair_focused_gain, L(0.0)),
        ),
        Max(
            L(1.0),
            Div(recovery_focused_deficit(), pair_focused_gain),
        ),
        L(1.0),
    )
    return {
        "name": "ha_compose_situated_recovery_action",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "After local singleton exploration, combine the two "
        "best receipt-backed effectors from different mechanical groups. "
        "Each firing keeps the body-derived nominal horizon; the open recovery "
        "program, rather than a second duration mechanism, controls persistence.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode", "has_current_humanoid_recovery_basin", "basin"
            ],
            [
                "episode",
                "has_selected_humanoid_recovery_primary",
                "primary_action",
            ],
            [
                "basin",
                "has_humanoid_recovery_basin_action",
                "secondary_action",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(ACTIVE_RECOVERY_PROGRAMS), L(0.0)),
            Eq(Count(untried_recovery_models()), L(0.0)),
            Gt(Count(compatible), L(0.0)),
            Eq(V("secondary_action"), secondary),
        ),
        "effects": [
            ["add_node", "program", "HumanoidRecoveryProgram", {
                "status": "armed",
                "termination_kind": "basin_exit_or_pareto_loss",
                "primary_token": T(A("primary_action", "primary_token")),
                "secondary_token": T(A("secondary_action", "primary_token")),
                "response_frames": T(response_frames),
                "motor_weight_a": T(inverse_recruitment),
                "motor_weight_b": T(inverse_recruitment),
                "last_receipt_progress": 0.0,
                "repeat_count": 0.0,
                "last_request_seq": T(P0("episode", "request_seq")),
                "launch_configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "launch_normalized_height": T(Div(
                    P0("episode", "state_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "launch_vertical_alignment": T(
                    body_z_z("episode", "state")
                ),
                "launch_support_count": T(
                    P0("episode", "active_support_count")
                ),
                "launch_contact_count": T(
                    P0("episode", "state_contact_count_raw")
                ),
                "launch_motion_energy": T(
                    recovery_current_motion_energy()
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_active_humanoid_recovery_program",
                "program",
            ],
            [
                "add_edge",
                "basin",
                "has_humanoid_recovery_program",
                "program",
            ],
            [
                "add_edge",
                "program",
                "starts_from_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("primary_action", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("secondary_action", "primary_token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                response_frames
            )],
            ["set_attr", "episode", "selected_motor_weight_a", T(
                inverse_recruitment
            )],
            ["set_attr", "episode", "selected_motor_weight_b", T(
                inverse_recruitment
            )],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_exploit"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_attempt_count", T(Plus(
                P0("episode", "get_up_attempt_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_action_count", T(Plus(
                P0("episode", "recovery_action_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_composition_count", T(Plus(
                P0("episode", "recovery_composition_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_program_count", T(Plus(
                P0("episode", "recovery_program_count"), L(1.0)
            ))],
            [
                "del_edge",
                "episode",
                "has_selected_humanoid_recovery_primary",
                "primary_action",
            ],
            [
                "set_attr",
                "episode",
                "get_up_exploitation_start_attempt",
                T(If(
                    Eq(
                        P0("episode", "get_up_exploitation_start_attempt"),
                        L(0.0),
                    ),
                    P0("episode", "get_up_attempt_count"),
                    P0("episode", "get_up_exploitation_start_attempt"),
                )),
            ],
        ],
    }


def learn_recovery_basin_action_rule():
    matching = Filter(
        recovery_basin_actions(),
        "existing_action",
        And(
            Eq(A("existing_action", "primary_token"), A("trial", "token")),
            Eq(
                A("existing_action", "secondary_token"),
                A("trial", "secondary_token"),
            ),
            Eq(
                A("existing_action", "configuration_shape"),
                A("outcome", "pre_motor_configuration_shape"),
            ),
            Eq(
                P0("existing_action", "motor_weight_a"),
                P0("trial", "motor_weight_a"),
            ),
            Eq(
                P0("existing_action", "motor_weight_b"),
                P0("trial", "motor_weight_b"),
            ),
        ),
    )
    secondary_model = Pick(Filter(
        GET_UP_MODELS,
        "secondary_model",
        Eq(A("secondary_model", "token"), A("trial", "secondary_token")),
    ))
    height_gain = Div(
        Minus(P0("outcome", "post_z"), P0("outcome", "pre_z")),
        P0("episode", "standing_reference_z"),
    )
    alignment_gain = Minus(
        body_z_z("outcome", "post"),
        body_z_z("outcome", "pre"),
    )
    pareto_measurements = {
        "mean_support_gain": recovery_support_gain(),
        "mean_contact_gain": recovery_contact_gain(),
        "mean_whole_body_support_gain": (
            recovery_whole_body_support_gain()
        ),
        "mean_translation_gain": recovery_translation_gain(),
        "mean_motion_reduction": recovery_motion_reduction(),
        "mean_normalized_energy": recovery_normalized_energy(),
        "mean_normalized_peak_load": recovery_normalized_peak_load(),
    }
    return {
        "name": "ha_learn_situated_recovery_basin_action",
        "area": "adaptive_learning",
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_get_up_action_model", "get_up_model"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "starts_from_humanoid_recovery_basin", "basin"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("get_up_model", "token"), A("trial", "token")),
            Not(Eq(
                A("trial", "decision_kind"),
                L("get_up_reanchor"),
            )),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "recovery_basin_action_learned"), L(0.0)),
            Eq(Count(matching), L(0.0)),
        ),
        "effects": [
            ["add_node", "basin_action", "HumanoidRecoveryBasinAction", {
                "primary_token": T(A("trial", "token")),
                "secondary_token": T(A("trial", "secondary_token")),
                "primary_actuator_group": T(
                    P0("get_up_model", "actuator_group")
                ),
                "secondary_actuator_group": T(
                    N0(secondary_model, "actuator_group")
                ),
                "member_count": T(If(
                    Eq(A("trial", "token"), A("trial", "secondary_token")),
                    L(1.0),
                    L(2.0),
                )),
                "experience_count": 1.0,
                "mean_height_gain": T(height_gain),
                "mean_alignment_gain": T(alignment_gain),
                **{
                    key: T(value)
                    for key, value in pareto_measurements.items()
                },
                "response_frames": T(P0("trial", "response_frames")),
                "motor_weight_a": T(P0("trial", "motor_weight_a")),
                "motor_weight_b": T(P0("trial", "motor_weight_b")),
                "configuration_shape": T(
                    A("outcome", "pre_motor_configuration_shape")
                ),
                "post_configuration_shape": T(
                    A("outcome", "post_motor_configuration_shape")
                ),
                "pre_normalized_height": T(Div(
                    P0("outcome", "pre_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "post_normalized_height": T(Div(
                    P0("outcome", "post_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "pre_vertical_alignment": T(body_z_z("outcome", "pre")),
                "post_vertical_alignment": T(body_z_z("outcome", "post")),
                "pre_support_count": T(recovery_support_count("pre")),
                "post_support_count": T(recovery_support_count("post")),
                "pre_contact_count": T(P0("outcome", "pre_contact_count")),
                "post_contact_count": T(P0("outcome", "contact_count")),
                "pre_motion_energy": T(recovery_motion_energy("pre")),
                "post_motion_energy": T(recovery_motion_energy("post")),
                "last_update_request_seq": T(P0("trial", "request_seq")),
            }],
            [
                "add_edge",
                "basin",
                "has_humanoid_recovery_basin_action",
                "basin_action",
            ],
            ["set_attr", "outcome", "recovery_basin_action_learned", 1.0],
            ["set_attr", "episode", "recovery_basin_action_count", T(Plus(
                P0("episode", "recovery_basin_action_count"), L(1.0)
            ))],
        ],
    }


def update_recovery_basin_action_rule():
    height_gain = Div(
        Minus(P0("outcome", "post_z"), P0("outcome", "pre_z")),
        P0("episode", "standing_reference_z"),
    )
    alignment_gain = Minus(
        body_z_z("outcome", "post"),
        body_z_z("outcome", "pre"),
    )
    pareto_measurements = {
        "mean_support_gain": recovery_support_gain(),
        "mean_contact_gain": recovery_contact_gain(),
        "mean_whole_body_support_gain": (
            recovery_whole_body_support_gain()
        ),
        "mean_translation_gain": recovery_translation_gain(),
        "mean_motion_reduction": recovery_motion_reduction(),
        "mean_normalized_energy": recovery_normalized_energy(),
        "mean_normalized_peak_load": recovery_normalized_peak_load(),
    }
    count = Plus(P0("basin_action", "experience_count"), L(1.0))
    return {
        "name": "ha_update_situated_recovery_basin_action",
        "area": "adaptive_learning",
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "starts_from_humanoid_recovery_basin", "basin"],
            [
                "basin",
                "has_humanoid_recovery_basin_action",
                "basin_action",
            ],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Not(Eq(
                A("trial", "decision_kind"),
                L("get_up_reanchor"),
            )),
            Eq(A("basin_action", "primary_token"), A("trial", "token")),
            Eq(
                A("basin_action", "secondary_token"),
                A("trial", "secondary_token"),
            ),
            Eq(
                A("basin_action", "configuration_shape"),
                A("outcome", "pre_motor_configuration_shape"),
            ),
            Eq(
                P0("basin_action", "motor_weight_a"),
                P0("trial", "motor_weight_a"),
            ),
            Eq(
                P0("basin_action", "motor_weight_b"),
                P0("trial", "motor_weight_b"),
            ),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "recovery_basin_action_learned"), L(0.0)),
            Lt(
                P0("basin_action", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "basin_action", "mean_height_gain", T(Plus(
                P0("basin_action", "mean_height_gain"),
                Div(
                    Minus(height_gain, P0("basin_action", "mean_height_gain")),
                    count,
                ),
            ))],
            ["set_attr", "basin_action", "mean_alignment_gain", T(Plus(
                P0("basin_action", "mean_alignment_gain"),
                Div(
                    Minus(
                        alignment_gain,
                        P0("basin_action", "mean_alignment_gain"),
                    ),
                    count,
                ),
            ))],
            *[
                ["set_attr", "basin_action", key, T(Plus(
                    P0("basin_action", key),
                    Div(
                        Minus(value, P0("basin_action", key)),
                        count,
                    ),
                ))]
                for key, value in pareto_measurements.items()
            ],
            ["set_attr", "basin_action", "experience_count", T(count)],
            ["set_attr", "basin_action", "last_update_request_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "basin_action", "post_configuration_shape", T(
                A("outcome", "post_motor_configuration_shape")
            )],
            ["set_attr", "basin_action", "post_normalized_height", T(Div(
                P0("outcome", "post_z"),
                P0("episode", "standing_reference_z"),
            ))],
            ["set_attr", "basin_action", "post_vertical_alignment", T(
                body_z_z("outcome", "post")
            )],
            ["set_attr", "basin_action", "post_support_count", T(
                recovery_support_count("post")
            )],
            ["set_attr", "basin_action", "post_contact_count", T(
                P0("outcome", "contact_count")
            )],
            ["set_attr", "basin_action", "post_motion_energy", T(
                recovery_motion_energy("post")
            )],
            ["set_attr", "outcome", "recovery_basin_action_learned", 1.0],
        ],
    }


def promote_recovery_basin_rule():
    support_gain = Gt(recovery_support_gain(), L(0.0))
    contact_gain = Gt(recovery_contact_gain(), L(0.0))
    metastable_or_supported = Or(
        recovery_state_is_quiet(),
        support_gain,
        contact_gain,
    )
    return {
        "name": "ha_promote_receipt_confirmed_recovery_basin",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Promote a new situated recovery basin only when a "
        "receipt-confirmed compound crosses the current posture boundary. "
        "Singleton receipts remain local affordance evidence, so transient "
        "support changes cannot restart the alphabet survey. A changed decoded "
        "configuration must become quiet or acquire foot/general-body contact. "
        "The transition must improve at least one postural coordinate; lower "
        "motion alone updates the present basin instead of fragmenting it. Action "
        "dominance controls command reuse but cannot erase a newly observed "
        "body state; transition energy and peak load stay on the path for later "
        "Pareto choice, while the non-dominated action frontier remains the "
        "source of reusable commands. This prevents one slowly settling posture from "
        "fragmenting into many basins while leaving intermediate recovery "
        "milestones unnamed.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode", "has_current_humanoid_recovery_basin", "previous"
            ],
            [
                "previous", "has_humanoid_recovery_program", "program"
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "starts_from_humanoid_recovery_basin", "previous"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("previous", "status"), L("situated")),
            Not(Eq(
                A("trial", "decision_kind"),
                L("get_up_reanchor"),
            )),
            Eq(P0("trial", "request_seq"), P0("episode", "request_seq")),
            Eq(A("program", "primary_token"), A("trial", "token")),
            Eq(
                A("program", "secondary_token"),
                A("trial", "secondary_token"),
            ),
            Eq(
                P0("program", "last_request_seq"),
                P0("trial", "request_seq"),
            ),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "recovery_basin_considered"), L(0.0)),
            And(
                Eq(
                    Count(untried_recovery_models("previous")),
                    L(0.0),
                ),
                Gt(P0("trial", "bundle_member_count"), L(1.0)),
            ),
            recovery_outcome_has_progress(),
            recovery_successor_has_postural_progress(),
            Not(recovery_successor_is_dominated_by_previous()),
            Not(Eq(
                A("previous", "configuration_shape"),
                A("outcome", "post_motor_configuration_shape"),
            )),
            metastable_or_supported,
            Eq(P0("episode", "upright"), L(0.0)),
        ),
        "effects": [
            ["add_node", "basin", "HumanoidRecoveryBasin", {
                "ordinal": T(Plus(
                    P0("episode", "recovery_basin_count"), L(1.0)
                )),
                "status": "situated",
                "configuration_shape": T(
                    A("outcome", "post_motor_configuration_shape")
                ),
                "normalized_height": T(Div(
                    P0("outcome", "post_z"),
                    P0("episode", "standing_reference_z"),
                )),
                "vertical_alignment": T(body_z_z("outcome", "post")),
                "support_count": T(recovery_support_count("post")),
                "contact_count": T(P0("outcome", "contact_count")),
                "motion_energy": T(recovery_motion_energy("post")),
                "transition_normalized_energy": T(
                    recovery_normalized_energy()
                ),
                "transition_normalized_peak_load": T(
                    recovery_normalized_peak_load()
                ),
                "visit_count": 1.0,
                "transition_confirmed": 1.0,
                "warm_start_tested": 0.0,
                "composition_settling_tested": 0.0,
                "reanchor_after_request_seq": T(
                    P0("trial", "request_seq")
                ),
                "request_seq": T(P0("trial", "request_seq")),
                "incoming_primary_token": T(A("trial", "token")),
                "incoming_secondary_token": T(
                    A("trial", "secondary_token")
                ),
                "incoming_response_frames": T(
                    P0("program", "response_frames")
                ),
                "incoming_motor_weight_a": T(
                    P0("program", "motor_weight_a")
                ),
                "incoming_motor_weight_b": T(
                    P0("program", "motor_weight_b")
                ),
                "incoming_configuration_shape": T(
                    A("program", "launch_configuration_shape")
                ),
                "incoming_normalized_height": T(
                    P0("program", "launch_normalized_height")
                ),
                "incoming_vertical_alignment": T(
                    P0("program", "launch_vertical_alignment")
                ),
                "incoming_support_count": T(
                    P0("program", "launch_support_count")
                ),
                "incoming_contact_count": T(
                    P0("program", "launch_contact_count")
                ),
                "incoming_motion_energy": T(
                    P0("program", "launch_motion_energy")
                ),
            }],
            [
                "add_edge", "episode", "has_humanoid_recovery_basin", "basin"
            ],
            [
                "add_edge",
                "previous",
                "continues_to_humanoid_recovery_basin",
                "basin",
            ],
            [
                "add_edge",
                "basin",
                "inherits_humanoid_recovery_actions_from",
                "previous",
            ],
            [
                "del_edge",
                "episode",
                "has_current_humanoid_recovery_basin",
                "previous",
            ],
            [
                "add_edge",
                "episode",
                "has_current_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "episode", "recovery_basin_count", T(Plus(
                P0("episode", "recovery_basin_count"), L(1.0)
            ))],
            ["set_attr", "episode", "recovery_basin_transition_count", T(Plus(
                P0("episode", "recovery_basin_transition_count"), L(1.0)
            ))],
            ["set_attr", "episode", "get_up_exploitation_start_attempt", 0.0],
            ["set_attr", "episode", "recovery_basin_start_attempt", T(
                P0("episode", "get_up_attempt_count")
            )],
            ["set_attr", "outcome", "recovery_basin_considered", 1.0],
        ],
    }


def retire_recovery_basin_rule():
    return {
        "name": "ha_retire_current_recovery_basin_on_viability",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Retire a fallen-body basin only from a newer raw-state "
        "receipt that establishes viability, or from an acknowledged body "
        "reset. A stale upright flag from before the probe cannot erase the "
        "experimental recovery frame.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_recovery_basin", "basin"],
        ],
        "where": Or(
            And(
                Eq(PI0("episode", "upright"), L(1)),
                Eq(PI0("episode", "state_is_receipt"), L(1)),
                Gt(
                    PI0("episode", "state_seq"),
                    PI0("basin", "request_seq"),
                ),
            ),
            Gt(
                P0("episode", "body_reset_seq"),
                P0("episode", "body_reset_processed_seq"),
            ),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_current_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "basin", "status", "retained"],
            ["set_attr", "episode", "get_up_exploitation_start_attempt", 0.0],
            ["set_attr", "episode", "recovery_basin_start_attempt", 0.0],
        ],
    }


def request_get_up_reset_rule():
    return {
        "name": "ha_request_new_get_up_attempt_after_impasse",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "After the complete opaque actuator alphabet has been "
        "tried and a further alphabet-length interval produces no recovery "
        "improvement, declare a graph-level get-up impasse. The mechanical "
        "boundary may reset the body, but the learned graph persists.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(UNTRIED_GET_UP_MODELS), L(0.0)),
            Gt(
                Minus(
                    P0("episode", "get_up_attempt_count"),
                    Max(
                        P0("episode", "get_up_last_improvement_attempt"),
                        Max(
                            P0(
                                "episode",
                                "get_up_exploitation_start_attempt",
                            ),
                            P0("episode", "recovery_basin_start_attempt"),
                        ),
                    ),
                ),
                Count(GET_UP_MODELS),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "reset_requested", 1.0],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0.0],
            ["set_attr", "episode", "get_up_reset_count", T(
                Plus(P0("episode", "get_up_reset_count"), L(1.0))
            )],
        ],
    }


def acknowledge_body_reset_rule():
    return {
        "name": "ha_resume_lifetime_after_mechanical_body_reset",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Consume a reset receipt only after the graph requested a "
        "new get-up attempt. Clear transient control state while preserving "
        "all learned action, program, transition, and recovery models.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": Gt(
            P0("episode", "body_reset_seq"),
            P0("episode", "body_reset_processed_seq"),
        ),
        "effects": [
            ["set_attr", "episode", "lifetime_completed_progress", T(
                Plus(
                    P0("episode", "lifetime_completed_progress"),
                    P0("episode", "directed_progress"),
                )
            )],
            ["set_attr", "episode", "body_reset_processed_seq", T(
                P0("episode", "body_reset_seq")
            )],
            ["set_attr", "episode", "reset_requested", 0.0],
            ["set_attr", "episode", "recovery_mode", 0.0],
            ["set_attr", "episode", "recovery_entry_open", 0.0],
            ["set_attr", "episode", "gait_surprise_streak", 0.0],
            ["set_attr", "episode", "motor_primary_ready", 0.0],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0.0],
            ["set_attr", "episode", "get_up_exploitation_start_attempt", 0.0],
            ["set_attr", "episode", "recovery_basin_start_attempt", 0.0],
            ["set_attr", "episode", "get_up_last_improvement_attempt", T(
                P0("episode", "get_up_attempt_count")
            )],
            ["set_attr", "episode", "locomotion_measurements_initialized", 0.0],
            ["set_attr", "episode", "last_unilateral_support", 0.0],
            ["set_attr", "episode", "current_support_phase", 0.0],
        ],
    }


def choose_get_up_exploration_rule():
    best = Argmin(
        UNTRIED_GET_UP_MODELS,
        "get_up_candidate",
        P0("get_up_candidate", "ordinal"),
        V("episode"),
    )
    return {
        "name": "ha_explore_whole_body_get_up_action",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "When fallen, systematically try the entire opaque "
        "actuator alphabet. This includes arm, trunk, and leg actuators when "
        "the body has them, without supplying anatomical labels to the graph. "
        "This is the pre-basin fallback; once a situated recovery basin exists, "
        "its local explorer exclusively owns the decision fields.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_get_up_action_model",
                "get_up_model",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(CURRENT_RECOVERY_BASINS), L(0.0)),
            Gt(Count(UNTRIED_GET_UP_MODELS), L(0.0)),
            Eq(P0("get_up_model", "ordinal"), N0(best, "ordinal")),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                A("get_up_model", "token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("get_up_model", "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("episode", "nominal_response_frames")
            )],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_explore"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
            ["set_attr", "episode", "get_up_attempt_count", T(
                Plus(P0("episode", "get_up_attempt_count"), L(1.0))
            )],
            ["set_attr", "episode", "recovery_action_count", T(
                Plus(P0("episode", "recovery_action_count"), L(1.0))
            )],
        ],
    }


def choose_get_up_exploitation_rule():
    best = Argmin(
        GET_UP_MODELS,
        "get_up_candidate",
        get_up_model_cost("get_up_candidate"),
        V("episode"),
    )
    return {
        "name": "ha_exploit_learned_whole_body_get_up_action",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Before a situated basin exists, repeat the action whose "
        "verified receipts best increased normalized height and body vertical "
        "alignment. Basin-local exploitation exclusively owns later choices.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_get_up_action_model",
                "get_up_model",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "reset_requested"), L(0.0)),
            Eq(Count(CURRENT_RECOVERY_BASINS), L(0.0)),
            Eq(Count(UNTRIED_GET_UP_MODELS), L(0.0)),
            Eq(P0("get_up_model", "ordinal"), N0(best, "ordinal")),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                A("get_up_model", "token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("get_up_model", "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("episode", "nominal_response_frames")
            )],
            ["set_attr", "episode", "selected_predicted_dvx", 0.0],
            ["set_attr", "episode", "selected_predicted_dvy", 0.0],
            ["set_attr", "episode", "selected_predicted_dvz", 0.0],
            ["set_attr", "episode", "decision_kind", "get_up_exploit"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
            ["set_attr", "episode", "get_up_attempt_count", T(
                Plus(P0("episode", "get_up_attempt_count"), L(1.0))
            )],
            ["set_attr", "episode", "recovery_action_count", T(
                Plus(P0("episode", "recovery_action_count"), L(1.0))
            )],
        ],
    }


def choose_gait_recovery_primary_rule():
    support_models = Filter(
        PHASE_MODELS,
        "recovery_candidate",
        And(
            Eq(
                P0("recovery_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Gt(P0("recovery_candidate", "initialized"), L(0.5)),
        ),
    )
    primary = Argmin(
        support_models,
        "candidate",
        correction_cost("candidate"),
        V("episode"),
    )
    return {
        "name": "ha_select_gait_recovery_primary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Select the learned primary balance correction before "
        "collapsing the still-open locomotion and recovery residuals through "
        "the shared arbitrary-width motor-program synthesis. This controller "
        "owns upright instability; once the body is classified fallen, the "
        "situated get-up manifold exclusively owns motor selection.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "upright"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "motor_recovery_primary_ready"), L(0.0)),
            Gt(Count(support_models), L(0.0)),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "selected_recovery_primary_token",
                T(AO(primary, "token")),
            ],
            [
                "set_attr",
                "episode",
                "selected_primary_token",
                T(AO(primary, "token")),
            ],
            [
                "set_attr",
                "episode",
                "selected_primary_context_id",
                T(N0(primary, "context_id")),
            ],
            [
                "set_attr",
                "episode",
                "motor_recovery_primary_ready",
                1.0,
            ],
            ["set_attr", "episode", "motor_primary_ready", 1.0],
        ],
    }


def choose_tonic_control_rule():
    best = Argmin(
        TONIC,
        "candidate",
        P0("candidate", "ordinal"),
        V("episode"),
    )
    return {
        "name": "ha_choose_tonic_posture_control",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Matched control arm selects only the body's tonic default.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Or(
                Eq(A("episode", "phase"), L("recovery")),
                Eq(A("episode", "phase"), L("locomotion")),
            ),
            Eq(A("episode", "mode"), L("tonic_posture_control")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(Count(TONIC), L(0.0)),
        ),
        "effects": motor_selection_effects(
            best,
            "tonic_control",
            If(
                Eq(A("episode", "phase"), L("recovery")),
                Max(
                    L(1.0),
                    IDiv(
                        P0("episode", "response_frames"),
                        P0(
                            "policy",
                            "gait_surprise_confirmation_receipts",
                        ),
                    ),
                ),
                P0("episode", "response_frames"),
            ),
        ),
    }


def issued_trials_for_current_request():
    return Filter(
        Neighbours("episode", "has_humanoid_motor_trial"),
        "current_issued_trial",
        And(
            Eq(A("current_issued_trial", "status"), L("issued")),
            Eq(
                P0("current_issued_trial", "request_seq"),
                P0("episode", "request_seq"),
            ),
        ),
    )


def retire_stale_ready_motor_authority_rule():
    return {
        "name": "ha_retire_ready_motor_authority_at_request_boundary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Ready is one-request output authority, never persistent "
        "memory state. A newer sensed request expires an unconsumed edge; a "
        "previously learned program remains grounded evidence, while an "
        "unreceipted synthesis is retained only as superseded analysis.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_ready_humanoid_motor_program", "program"],
        ],
        "where": And(
            Lt(
                P0("program", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(P0("program", "developmental_orientation_bundle"), L(0.0)),
        ),
        "effects": [
            [
                "del_edge", "episode",
                "has_ready_humanoid_motor_program", "program",
            ],
            ["set_attr", "program", "status", T(If(
                Eq(P0("program", "receipt_learned"), L(1.0)),
                L("grounded"),
                L("superseded"),
            ))],
            ["set_attr", "program", "open_residual_count", 0.0],
            ["set_attr", "program", "authority_expired_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def developmental_trajectory_projection(source: str, field: str):
    return {
        "type": "FutureManifoldProjection",
        "episode": V("episode"),
        "policy": V("policy"),
        "source": V(source),
        "field": field,
    }


def release_selected_developmental_trajectory_rule():
    """Release a selected path before ordinary motor choice can commit."""
    members = Neighbours("memory", "includes_humanoid_phase_action_model")
    primary = Filter(
        members,
        "trajectory_primary_member",
        Eq(
            A("trajectory_primary_member", "token"),
            A("memory", "primary_token"),
        ),
    )
    secondary = Argmin(
        Filter(
            members,
            "trajectory_secondary_member",
            Not(Exists(
                primary,
                "known_trajectory_primary",
                Eq(
                    V("known_trajectory_primary"),
                    V("trajectory_secondary_member"),
                ),
            )),
        ),
        "ranked_trajectory_secondary",
        P0("ranked_trajectory_secondary", "ordinal"),
        Pick(primary),
    )
    gate_active = And(
        Gt(P0("policy", "future_manifold_enabled"), L(0.0)),
        Gt(P0("episode", "manifold_bounds_ready"), L(0.0)),
    )
    path_projection = lambda field: developmental_trajectory_projection(
        "path", field
    )
    release_allowed = Or(
        Not(gate_active),
        And(
            Gt(path_projection("support"), L(0.0)),
            Gt(path_projection("resolved"), L(0.0)),
            Eq(
                path_projection("information_loss"),
                L(0.0),
            ),
            Or(
                Eq(
                    path_projection("effort_supported"),
                    L(0.0),
                ),
                Gt(
                    path_projection("effort_authorized"),
                    L(0.0),
                ),
            ),
        ),
    )
    return {
        "name": "ha_release_selected_developmental_order_n_trajectory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The motor executor consumes a System-2-selected path "
        "before ordinary recovery or locomotion can commit the request. Each "
        "collapse releases one grounded program through the existing exact "
        "trial and receipt machinery.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_policy", "policy"],
            ["episode", "projects_embodied_development", "development"],
            [
                "development",
                "has_active_embodied_developmental_capability",
                "capability",
            ],
            ["capability", "has_selected_embodied_program_path", "path"],
            ["path", "contains_embodied_program_transition", "transition"],
            [
                "capability",
                "has_current_embodied_program_transition_source",
                "transition",
            ],
            ["transition", "continues_with_embodied_program", "memory"],
        ],
        "where": And(
            Or(
                Gt(Count(A("capability", "desired_body_state_signature")), L(0.0)),
                gate_active,
            ),
            Gt(P0("path", "depth"), L(1.0)),
            Eq(P0("transition", "verified"), L(1.0)),
            Eq(A("memory", "status"), L("grounded")),
            Or(
                Eq(P0("memory", "memory_eligible"), L(1.0)),
                And(
                    Eq(P0("memory", "experience_retained"), L(1.0)),
                    Eq(
                        P0(
                            "episode",
                            "caregiver_protective_support_available",
                        ),
                        L(1.0),
                    ),
                ),
            ),
            release_allowed,
            Gt(Count(primary), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(Count(issued_trials_for_current_request()), L(0.0)),
            Eq(Count(ready_motor_programs_for_current_request()), L(0.0)),
        ),
        "effects": [
            ["set_attr", "memory", "status", "ready"],
            ["set_attr", "memory", "request_seq", T(
                P0("episode", "request_seq")
            )],
            [
                "set_attr", "memory", "collapse_kind",
                "developmental_order_n_trajectory",
            ],
            ["set_attr", "memory", "open_residual_count", 1.0],
            ["set_attr", "path", "trajectory_replay_issued_seq", T(
                P0("episode", "request_seq")
            )],
            [
                "set_attr", "memory",
                "selected_path_projection_request_seq",
                T(P0("episode", "request_seq")),
            ],
            [
                "set_attr", "memory",
                "selected_path_projection_depth",
                T(P0("path", "depth")),
            ],
            [
                "set_attr", "memory",
                "selected_path_narrativium_snapshot",
                T(path_projection("narrativium_snapshot")),
            ],
            *[
                [
                    "set_attr", "memory",
                    f"selected_path_narrativium_reachable_{key}",
                    T(Nth(
                        A("memory", "selected_path_narrativium_snapshot"),
                        index,
                    )),
                ]
                for index, key in enumerate(HUMANOID_MANIFOLD_DIMENSIONS)
            ],
            *[
                [
                    "set_attr", "memory",
                    f"selected_path_narrativium_retained_{key}",
                    T(Nth(
                        A("memory", "selected_path_narrativium_snapshot"),
                        len(HUMANOID_MANIFOLD_DIMENSIONS) + index,
                    )),
                ]
                for index, key in enumerate(HUMANOID_MANIFOLD_DIMENSIONS)
            ],
            [
                "add_edge", "episode",
                "has_ready_humanoid_motor_program", "memory",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("memory", "primary_token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(Max(
                L(1.0), P0("transition", "response_frames")
            ))],
            ["set_attr", "episode", "selected_motor_weight_a", 1.0],
            ["set_attr", "episode", "selected_motor_weight_b", 1.0],
            *[
                ["set_attr", "episode", f"selected_predicted_{key}", 0.0]
                for key in (
                    "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                )
            ],
            ["set_attr", "episode", "decision_kind", "learned_walk"],
            [
                "set_attr", "episode", "selected_collapse_kind",
                "developmental_order_n_trajectory",
            ],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1.0)
            ))],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def ready_motor_programs_for_current_request():
    return Filter(
        Neighbours("episode", "has_ready_humanoid_motor_program"),
        "current_ready_program",
        And(
            Eq(A("current_ready_program", "status"), L("ready")),
            Eq(
                P0("current_ready_program", "request_seq"),
                P0("episode", "request_seq"),
            ),
        ),
    )


def selected_ready_motor_program():
    """Stable output-null choice after every candidate passed its own gate."""
    return Argmin(
        ready_motor_programs_for_current_request(),
        "ranked_ready_program",
        P0("ranked_ready_program", "request_seq"),
        V("episode"),
    )


def open_trial_rule():
    secondary_model = Pick(Filter(
        Neighbours("episode", "has_humanoid_action_model"),
        "secondary_candidate",
        Eq(
            A("secondary_candidate", "token"),
            A("episode", "selected_secondary_token"),
        ),
    ))
    mechanically_distinct_secondary = And(
        Not(Eq(
            A("model", "token"),
            AO(secondary_model, "token"),
        )),
        Not(Eq(
            P0("model", "actuator_group"),
            N0(secondary_model, "actuator_group"),
        )),
    )
    committed_secondary_token = If(
        mechanically_distinct_secondary,
        AO(secondary_model, "token"),
        A("model", "token"),
    )
    return {
        "name": "ha_open_receipt_backed_motor_trial",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Commit the graph-selected opaque action against the "
        "body-derived mechanical topology. Distinct tokens for the same "
        "actuator group collapse to the primary singleton, so concurrent "
        "proposal settlement cannot author contradictory joint commands.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_action_model", "model"],
        ],
        "where": And(
            Not(Eq(
                A("episode", "decision_kind"),
                L("learned_walk"),
            )),
            Eq(P0("episode", "action_ready"), L(1.0)),
            Eq(A("model", "token"), A("episode", "selected_token")),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_trial_request_seq"),
            ),
            Eq(Count(issued_trials_for_current_request()), L(0)),
        ),
        "effects": [
            ["add_node", "trial", "HumanoidMotorTrial", {
                "request_seq": T(P0("episode", "request_seq")),
                "motor_task_context": T(motor_task_context()),
                **trial_regime_eligibility_attrs(),
                "token": T(A("model", "token")),
                "secondary_token": T(committed_secondary_token),
                "motor_weight_a": T(
                    P0("episode", "selected_motor_weight_a")
                ),
                "motor_weight_b": T(
                    P0("episode", "selected_motor_weight_b")
                ),
                "response_frames": T(
                    P0("episode", "selected_response_frames")
                ),
                "predicted_dvx": T(
                    P0("episode", "selected_predicted_dvx")
                ),
                "predicted_dvy": T(
                    P0("episode", "selected_predicted_dvy")
                ),
                "predicted_dvz": T(
                    P0("episode", "selected_predicted_dvz")
                ),
                **{
                    f"predicted_{key}": T(
                        P0("episode", f"selected_predicted_{key}")
                    )
                    for key in ("dzx", "dzy", "dwx", "dwy")
                },
                "bundle_member_count": T(If(
                    mechanically_distinct_secondary,
                    L(2.0),
                    L(1.0),
                )),
                "model_response_frames": T(
                    P0("episode", "response_frames")
                ),
                "decision_kind": T(A("episode", "decision_kind")),
                "support_phase": T(
                    P0("episode", "current_support_phase")
                ),
                "status": "issued",
                "pre_z": T(P0("episode", "state_z")),
                "pre_qx": T(P0("episode", "state_qx")),
                "pre_qy": T(P0("episode", "state_qy")),
                "pre_qz": T(P0("episode", "state_qz")),
                "pre_qw": T(P0("episode", "state_qw")),
                "pre_wx": T(P0("episode", "state_wx")),
                "pre_wy": T(P0("episode", "state_wy")),
                "pre_vx": T(P0("episode", "state_vx")),
                "pre_vy": T(P0("episode", "state_vy")),
                "pre_vz": T(P0("episode", "state_vz")),
                "pre_lateral_offset": T(
                    P0("episode", "lateral_offset")
                ),
            }],
            ["add_edge", "episode", "has_humanoid_motor_trial", "trial"],
            ["add_edge", "trial", "uses_humanoid_action_model", "model"],
            ["set_attr", "episode", "last_trial_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def open_motor_program_trial_rule():
    candidate_models = Filter(
        Neighbours("episode", "has_humanoid_action_model"),
        "program_action_candidate",
        Eq(
            A("program_action_candidate", "token"),
            A("plan", "primary_token"),
        ),
    )
    selected_model = Argmin(
        candidate_models,
        "ranked_program_action_model",
        P0("ranked_program_action_model", "context_id"),
        V("episode"),
    )
    return {
        "name": "ha_open_synthesized_motor_program_trial",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Open an arbitrary bundle trial from the program's own "
        "member edges. This structural dependency makes the fixpoint "
        "incrementally visible without a host-side pump.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_ready_humanoid_motor_program", "plan"],
            [
                "plan",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
            ["episode", "has_humanoid_action_model", "model"],
        ],
        "where": And(
            Eq(V("plan"), selected_ready_motor_program()),
            Eq(V("model"), selected_model),
            Eq(A("plan", "status"), L("ready")),
            takeoff_effort_prepared(),
            Eq(A("primary", "token"), A("plan", "primary_token")),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_trial_request_seq"),
            ),
            Eq(Count(issued_trials_for_current_request()), L(0)),
        ),
        "effects": [
            ["add_node", "trial", "HumanoidMotorTrial", {
                "request_seq": T(P0("episode", "request_seq")),
                "motor_task_context": T(motor_task_context()),
                **trial_regime_eligibility_attrs(),
                "token": T(A("model", "token")),
                "secondary_token": T(
                    A("episode", "selected_secondary_token")
                ),
                "response_frames": T(
                    P0("episode", "selected_response_frames")
                ),
                "motor_weight_a": T(P0(
                    "episode", "selected_motor_weight_a"
                )),
                "motor_weight_b": T(P0(
                    "episode", "selected_motor_weight_b"
                )),
                "motor_effort_ratio": T(P0(
                    "plan", "motor_effort_ratio"
                )),
                **{
                    key: T(P0("plan", key))
                    for key in (
                        "takeoff_effort_supported",
                        "takeoff_effort_required_ratio",
                        "takeoff_effort_residual_ratio",
                        "takeoff_effort_authorized",
                    )
                },
                **{
                    f"predicted_{key}": T(
                        P0("episode", f"selected_predicted_{key}")
                    )
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                "bundle_member_count": T(
                    P0("plan", "member_count")
                ),
                "model_response_frames": T(
                    P0("episode", "response_frames")
                ),
                "decision_kind": "learned_walk",
                "collapse_kind": T(A("plan", "collapse_kind")),
                "open_residual_count": T(
                    P0("plan", "open_residual_count")
                ),
                "motor_memory_recalled": T(If(
                    Eq(P0("plan", "receipt_learned"), L(1.0)),
                    L(1.0),
                    L(0.0),
                )),
                "expected_directed_advance": T(
                    P0("plan", "mean_directed_advance")
                ),
                "support_phase": T(
                    P0("episode", "current_support_phase")
                ),
                "status": "issued",
                "pre_z": T(P0("episode", "state_z")),
                "pre_qx": T(P0("episode", "state_qx")),
                "pre_qy": T(P0("episode", "state_qy")),
                "pre_qz": T(P0("episode", "state_qz")),
                "pre_qw": T(P0("episode", "state_qw")),
                "pre_wx": T(P0("episode", "state_wx")),
                "pre_wy": T(P0("episode", "state_wy")),
                "pre_vx": T(P0("episode", "state_vx")),
                "pre_vy": T(P0("episode", "state_vy")),
                "pre_vz": T(P0("episode", "state_vz")),
                "pre_lateral_offset": T(
                    P0("episode", "lateral_offset")
                ),
            }],
            ["add_edge", "episode", "has_humanoid_motor_trial", "trial"],
            ["add_edge", "trial", "uses_humanoid_action_model", "model"],
            [
                "add_edge",
                "trial",
                "enacts_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "has_ready_humanoid_motor_program",
                "plan",
            ],
            ["set_attr", "episode", "last_trial_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def open_canonical_synthesis_trial_rule():
    eligible = Filter(
        equivalent_motor_memories(),
        "eligible_canonical",
        Eq(P0("eligible_canonical", "memory_eligible"), L(1.0)),
    )
    canonical = Argmin(
        eligible,
        "eligible_canonical",
        canonical_motor_memory_rank("eligible_canonical"),
        V("plan"),
    )
    return {
        "name": "ha_bind_synthesized_structure_to_canonical_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Analysis by synthesis still authors the exact action. If "
        "that structure already has a safe grounded population memory, enact "
        "the stable node and credit its receipt instead of creating another "
        "request-identity memory. The current synthesis, not memory prediction, "
        "supplies actuator authority.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_ready_humanoid_motor_program", "plan"],
            ["episode", "has_humanoid_motor_program", "memory"],
            [
                "memory",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
            [
                "primary",
                "generalizes_humanoid_action_model",
                "model",
            ],
        ],
        "where": And(
            Eq(V("plan"), selected_ready_motor_program()),
            Eq(A("plan", "status"), L("ready")),
            takeoff_effort_prepared(),
            Gt(P0("plan", "member_count"), L(0.0)),
            Gt(Count(eligible), L(0.0)),
            Eq(V("memory"), canonical),
            Eq(A("primary", "token"), A("plan", "primary_token")),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_trial_request_seq"),
            ),
            Eq(Count(issued_trials_for_current_request()), L(0)),
        ),
        "effects": [
            ["add_node", "trial", "HumanoidMotorTrial", {
                "request_seq": T(P0("episode", "request_seq")),
                "motor_task_context": T(motor_task_context()),
                **trial_regime_eligibility_attrs(),
                "token": T(A("model", "token")),
                "secondary_token": T(
                    A("episode", "selected_secondary_token")
                ),
                "response_frames": T(
                    P0("episode", "selected_response_frames")
                ),
                "motor_weight_a": T(P0(
                    "episode", "selected_motor_weight_a"
                )),
                "motor_weight_b": T(P0(
                    "episode", "selected_motor_weight_b"
                )),
                "motor_effort_ratio": T(P0(
                    "plan", "motor_effort_ratio"
                )),
                **{
                    key: T(P0("plan", key))
                    for key in (
                        "takeoff_effort_supported",
                        "takeoff_effort_required_ratio",
                        "takeoff_effort_residual_ratio",
                        "takeoff_effort_authorized",
                    )
                },
                **{
                    f"predicted_{key}": T(
                        P0("episode", f"selected_predicted_{key}")
                    )
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                "bundle_member_count": T(P0("plan", "member_count")),
                "model_response_frames": T(
                    P0("episode", "response_frames")
                ),
                "decision_kind": "learned_walk",
                "collapse_kind": T(A("plan", "collapse_kind")),
                "open_residual_count": T(
                    P0("plan", "open_residual_count")
                ),
                "motor_memory_recalled": 0.0,
                "motor_memory_structurally_reused": 1.0,
                "support_phase": T(
                    P0("episode", "current_support_phase")
                ),
                "status": "issued",
                "pre_z": T(P0("episode", "state_z")),
                "pre_qx": T(P0("episode", "state_qx")),
                "pre_qy": T(P0("episode", "state_qy")),
                "pre_qz": T(P0("episode", "state_qz")),
                "pre_qw": T(P0("episode", "state_qw")),
                "pre_wx": T(P0("episode", "state_wx")),
                "pre_wy": T(P0("episode", "state_wy")),
                "pre_vx": T(P0("episode", "state_vx")),
                "pre_vy": T(P0("episode", "state_vy")),
                "pre_vz": T(P0("episode", "state_vz")),
                "pre_lateral_offset": T(
                    P0("episode", "lateral_offset")
                ),
            }],
            ["add_edge", "episode", "has_humanoid_motor_trial", "trial"],
            ["add_edge", "trial", "uses_humanoid_action_model", "model"],
            [
                "add_edge",
                "trial",
                "enacts_humanoid_motor_program",
                "memory",
            ],
            [
                "add_edge",
                "trial",
                "synthesized_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "has_ready_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "has_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "has_consolidated_humanoid_motor_program",
                "plan",
            ],
            ["set_attr", "plan", "status", "reassociated_duplicate"],
            ["set_attr", "plan", "receipt_learned", 1.0],
            ["set_attr", "memory", "consolidation_count", T(
                Plus(P0("memory", "consolidation_count"), L(1.0))
            )],
            ["set_attr", "episode", "motor_memory_structural_reuse_count", T(
                Plus(
                    P0("episode", "motor_memory_structural_reuse_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "last_trial_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def open_motor_sequence_trial_rule():
    return {
        "name": "ha_open_receipt_advanced_motor_sequence_trial",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Make one learned transition output-potent. The new trial "
        "links both the stable subprogram and the conditional transition "
        "state so its receipt can update the exact temporal model.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "recalls_humanoid_motor_transition",
                "transition",
            ],
            ["episode", "recalls_humanoid_motor_program", "memory"],
            [
                "episode",
                "has_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "preparation",
                "prepares_humanoid_motor_transition",
                "transition",
            ],
            [
                "transition",
                "continues_with_humanoid_motor_program",
                "memory",
            ],
            [
                "memory",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
            [
                "primary",
                "generalizes_humanoid_action_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("transition", "status"), L("grounded")),
            Eq(P0("transition", "memory_eligible"), L(1.0)),
            Eq(A("preparation", "status"), L("output_potent")),
            Eq(
                P0("preparation", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Eq(A("primary", "token"), A("memory", "primary_token")),
            Eq(
                P0("transition", "last_recall_request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(
                P0("memory", "last_recall_request_seq"),
                P0("episode", "request_seq"),
            ),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_trial_request_seq"),
            ),
            Eq(Count(issued_trials_for_current_request()), L(0)),
        ),
        "effects": [
            ["add_node", "trial", "HumanoidMotorTrial", {
                "request_seq": T(P0("episode", "request_seq")),
                "motor_task_context": T(motor_task_context()),
                **trial_regime_eligibility_attrs(),
                "token": T(A("model", "token")),
                "secondary_token": T(
                    A("episode", "selected_secondary_token")
                ),
                "response_frames": T(
                    P0("episode", "selected_response_frames")
                ),
                **{
                    f"predicted_{key}": T(
                        P0("episode", f"selected_predicted_{key}")
                    )
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                "bundle_member_count": T(
                    P0("memory", "member_count")
                ),
                "model_response_frames": T(
                    P0("episode", "response_frames")
                ),
                "decision_kind": "learned_walk",
                "motor_memory_recalled": 1.0,
                "expected_directed_advance": T(
                    P0("memory", "mean_directed_advance")
                ),
                "motor_sequence_recalled": 1.0,
                "motor_transition_ordinal": T(
                    P0("transition", "ordinal")
                ),
                "support_phase": T(
                    P0("episode", "current_support_phase")
                ),
                "status": "issued",
                "pre_z": T(P0("episode", "state_z")),
                "pre_qx": T(P0("episode", "state_qx")),
                "pre_qy": T(P0("episode", "state_qy")),
                "pre_qz": T(P0("episode", "state_qz")),
                "pre_qw": T(P0("episode", "state_qw")),
                "pre_wx": T(P0("episode", "state_wx")),
                "pre_wy": T(P0("episode", "state_wy")),
                "pre_vx": T(P0("episode", "state_vx")),
                "pre_vy": T(P0("episode", "state_vy")),
                "pre_vz": T(P0("episode", "state_vz")),
                "pre_lateral_offset": T(
                    P0("episode", "lateral_offset")
                ),
            }],
            ["add_edge", "episode", "has_humanoid_motor_trial", "trial"],
            ["add_edge", "trial", "uses_humanoid_action_model", "model"],
            [
                "add_edge",
                "trial",
                "enacts_humanoid_motor_program",
                "memory",
            ],
            [
                "add_edge",
                "trial",
                "enacts_humanoid_motor_transition",
                "transition",
            ],
            [
                "add_edge",
                "trial",
                "released_from_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "del_edge",
                "episode",
                "recalls_humanoid_motor_transition",
                "transition",
            ],
            [
                "del_edge",
                "episode",
                "recalls_humanoid_motor_program",
                "memory",
            ],
            ["set_attr", "episode", "last_trial_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def open_recalled_motor_program_trial_rule():
    return {
        "name": "ha_open_reassociated_motor_memory_trial",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Convert one graph-selected output-null motor memory into "
        "an output-potent trial. The trial is a new causal event while its "
        "arbitrary member set remains on the grounded repertoire node.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recalls_humanoid_motor_program", "memory"],
            [
                "episode",
                "has_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "preparation",
                "prepares_humanoid_motor_program",
                "memory",
            ],
            [
                "memory",
                "includes_humanoid_phase_action_model",
                "primary",
            ],
            [
                "primary",
                "generalizes_humanoid_action_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Eq(A("preparation", "status"), L("output_potent")),
            Or(
                Eq(
                    A("preparation", "preparation_kind"),
                    L("memory"),
                ),
                Eq(
                    A("preparation", "preparation_kind"),
                    L("takeoff_stage"),
                ),
            ),
            Eq(
                P0("preparation", "request_seq"),
                P0("episode", "request_seq"),
            ),
            Eq(A("primary", "token"), A("memory", "primary_token")),
            Eq(
                P0("memory", "last_recall_request_seq"),
                P0("episode", "request_seq"),
            ),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_trial_request_seq"),
            ),
            Eq(Count(issued_trials_for_current_request()), L(0)),
        ),
        "effects": [
            ["add_node", "trial", "HumanoidMotorTrial", {
                "request_seq": T(P0("episode", "request_seq")),
                "motor_task_context": T(motor_task_context()),
                **trial_regime_eligibility_attrs(),
                "token": T(A("model", "token")),
                "secondary_token": T(
                    A("episode", "selected_secondary_token")
                ),
                "response_frames": T(
                    P0("episode", "selected_response_frames")
                ),
                **{
                    f"predicted_{key}": T(
                        P0("episode", f"selected_predicted_{key}")
                    )
                    for key in (
                        "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                    )
                },
                "bundle_member_count": T(
                    P0("memory", "member_count")
                ),
                "model_response_frames": T(
                    P0("episode", "response_frames")
                ),
                "decision_kind": T(If(
                    Eq(
                        A("preparation", "preparation_kind"),
                        L("takeoff_stage"),
                    ),
                    L("learned_takeoff_stage"),
                    L("learned_walk"),
                )),
                "motor_memory_recalled": 1.0,
                "expected_directed_advance": T(
                    P0("memory", "mean_directed_advance")
                ),
                "support_phase": T(
                    P0("episode", "current_support_phase")
                ),
                "status": "issued",
                "pre_z": T(P0("episode", "state_z")),
                "pre_qx": T(P0("episode", "state_qx")),
                "pre_qy": T(P0("episode", "state_qy")),
                "pre_qz": T(P0("episode", "state_qz")),
                "pre_qw": T(P0("episode", "state_qw")),
                "pre_wx": T(P0("episode", "state_wx")),
                "pre_wy": T(P0("episode", "state_wy")),
                "pre_vx": T(P0("episode", "state_vx")),
                "pre_vy": T(P0("episode", "state_vy")),
                "pre_vz": T(P0("episode", "state_vz")),
                "pre_lateral_offset": T(
                    P0("episode", "lateral_offset")
                ),
            }],
            ["add_edge", "episode", "has_humanoid_motor_trial", "trial"],
            ["add_edge", "trial", "uses_humanoid_action_model", "model"],
            [
                "add_edge",
                "trial",
                "enacts_humanoid_motor_program",
                "memory",
            ],
            [
                "add_edge",
                "trial",
                "released_from_humanoid_motor_preparation",
                "preparation",
            ],
            [
                "del_edge",
                "episode",
                "recalls_humanoid_motor_program",
                "memory",
            ],
            ["set_attr", "episode", "last_trial_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def initialize_phase_model_rule():
    return {
        "name": "ha_initialize_support_phase_action_model",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Graph-initialize each support-conditioned model from its "
        "verified posture-local parent model.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_model",
            ],
            [
                "phase_model",
                "generalizes_humanoid_action_model",
                "model",
            ],
        ],
        "where": And(
            Eq(P0("phase_model", "initialized"), L(0.0)),
            Gt(P0("model", "experience_count"), L(0.5)),
        ),
        "effects": [
            ["set_attr", "phase_model", key, T(P0("model", key))]
            for key in (
                "mean_dzx",
                "mean_dzy",
                "mean_dwx",
                "mean_dwy",
                "mean_dvx",
                "mean_dvy",
                "mean_dvz",
                "mean_input_energy_joules",
                "support_loss_ema",
                "support_deficit_ema",
            )
        ] + [
            [
                "set_attr",
                "phase_model",
                "experience_count",
                T(P0("policy", "support_phase_prior_strength")),
            ],
            ["set_attr", "phase_model", "initialized", 1.0],
            ["set_attr", "phase_model", "prediction_authority", 1],
            ["set_attr", "phase_model", "prediction_confirmation_count", 0],
            ["set_attr", "phase_model", "prediction_invalidation_count", 0],
            ["set_attr", "phase_model", "prediction_reground_count", 0],
            ["set_attr", "phase_model", "last_prediction_receipt_seq", 0],
            ["set_attr", "phase_model", "invalidated_receipt_seq", 0],
            ["set_attr", "phase_model", "last_reground_receipt_seq", 0],
            ["set_attr", "phase_model", "prediction_grounding_status", "prior_grounded"],
        ],
    }


def link_active_phase_model_rule():
    linked = Neighbours("trial", "uses_humanoid_phase_action_model")
    return {
        "name": "ha_link_walking_trial_to_support_phase_model",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "enacts_humanoid_motor_program",
                "plan",
            ],
            [
                "plan",
                "includes_humanoid_phase_action_model",
                "phase_model",
            ],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(
                P0("trial", "support_phase"),
                P0("phase_model", "support_phase"),
            ),
            Not(Exists(
                linked,
                "linked_model",
                Eq(V("linked_model"), V("phase_model")),
            )),
        ),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_model",
            ],
        ],
    }


def measure_gait_prediction_error_rule():
    observed_dvx = Minus(
        P0("outcome", "post_vx"),
        P0("outcome", "pre_vx"),
    )
    observed_dvy = Minus(
        P0("outcome", "post_vy"),
        P0("outcome", "pre_vy"),
    )
    observed_dvz = Minus(
        P0("outcome", "post_vz"),
        P0("outcome", "pre_vz"),
    )
    residual_vx = Minus(
        observed_dvx,
        P0("trial", "predicted_dvx"),
    )
    residual_vy = Minus(
        observed_dvy,
        P0("trial", "predicted_dvy"),
    )
    residual_vz = Minus(
        observed_dvz,
        P0("trial", "predicted_dvz"),
    )
    prediction_error = Sqrt(Plus(
        Times(residual_vx, residual_vx),
        Times(residual_vy, residual_vy),
        Times(residual_vz, residual_vz),
    ))
    familiarizing = Eq(
        P0("episode", "evaluation_active"),
        L(0.0),
    )
    outside_envelope = Gt(
        prediction_error,
        P0("episode", "learned_gait_prediction_error_envelope"),
    )
    next_surprise_streak = {
        "type": "IfThenElse",
        "cond": outside_envelope,
        "then": Plus(P0("episode", "gait_surprise_streak"), L(1.0)),
        "other": L(0.0),
    }
    sufficiently_confirmed = Not(Lt(
        next_surprise_streak,
        P0("policy", "gait_surprise_confirmation_receipts"),
    ))
    tilt_outside_envelope = Gt(
        P0("episode", "tilt_magnitude"),
        P0("episode", "learned_gait_tilt_envelope"),
    )
    should_enter_recovery = Or(
        tilt_outside_envelope,
        And(
            outside_envelope,
            sufficiently_confirmed,
            Not(Lt(
                P0("episode", "tilt_magnitude"),
                P0("episode", "learned_gait_mean_tilt"),
            )),
        ),
    )
    canonical_recovery_verdict = Or(
        Eq(P0("episode", "upright"), L(0.0)),
        And(
            Not(Eq(
                A("trial", "motor_task_context"),
                L("self_takeoff"),
            )),
            should_enter_recovery,
        ),
    )
    should_recover = If(
        situated_locomotion_context_active(),
        receipt_material_viability_breach(),
        canonical_recovery_verdict,
    )
    return {
        "name": "ha_measure_gait_prediction_error_and_interrupt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Compare each verified horizontal velocity consequence "
        "with the active support-phase model. Learn the largest normal "
        "residual and vestibular tilt range during familiarization; "
        "interrupt immediately on a structural power or thermal verdict. "
        "Outside an intentionally owned developmental trajectory, excessive "
        "tilt or persistent prediction surprise also recruits recovery.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "prediction_error_measured"), L(0.0)),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "latest_gait_prediction_error",
                T(prediction_error),
            ],
            [
                "set_attr",
                "episode",
                "walking_peak_prediction_error",
                T({
                    "type": "IfThenElse",
                    "cond": familiarizing,
                    "then": {
                        "type": "Max",
                        "items": [
                            P0(
                                "episode",
                                "walking_peak_prediction_error",
                            ),
                            prediction_error,
                        ],
                    },
                    "other": P0(
                        "episode",
                        "walking_peak_prediction_error",
                    ),
                }),
            ],
            [
                "set_attr",
                "episode",
                "gait_surprise_streak",
                T({
                    "type": "IfThenElse",
                    "cond": familiarizing,
                    "then": P0("episode", "gait_surprise_streak"),
                    "other": next_surprise_streak,
                }),
            ],
            [
                "set_attr",
                "episode",
                "recovery_mode",
                T({
                    "type": "IfThenElse",
                    "cond": familiarizing,
                    "then": P0("episode", "recovery_mode"),
                    "other": {
                        "type": "IfThenElse",
                        "cond": should_recover,
                        "then": L(1.0),
                        "other": L(0.0),
                    },
                }),
            ],
            [
                "set_attr",
                "outcome",
                "prediction_error",
                T(prediction_error),
            ],
            [
                "set_attr",
                "outcome",
                "prediction_error_measured",
                1.0,
            ],
        ],
    }


def tune_response_horizon_rule():
    effective_nominal = Max(
        L(1.0),
        If(
            Gt(P0("episode", "nominal_response_frames"), L(0.0)),
            P0("episode", "nominal_response_frames"),
            P0("episode", "response_frames"),
        ),
    )
    shortened = Max(
        L(1.0),
        IDiv(P0("episode", "response_frames"), L(2.0)),
    )
    relaxed = If(
        Lt(
            P0("episode", "response_frames"),
            effective_nominal,
        ),
        Plus(P0("episode", "response_frames"), L(1.0)),
        effective_nominal,
    )
    tuned = If(
        Eq(P0("episode", "evaluation_active"), L(0.0)),
        effective_nominal,
        If(
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            If(
                Eq(P0("episode", "aerial_active"), L(1.0)),
                effective_nominal,
                shortened,
            ),
            relaxed,
        ),
    )
    return {
        "name": "ha_tune_response_horizon_from_prediction_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Contract the motor hold horizon for grounded prediction "
        "or vestibular recovery. With no aerodynamic effector, an already "
        "aerial body instead retains the body/gravity-derived nominal horizon "
        "until contact returns; stable grounded receipts then relax one "
        "physics frame at a time toward that same horizon.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "prediction_error_measured"), L(1.0)),
            Eq(P0("outcome", "response_horizon_tuned"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "response_frames", T(tuned)],
            ["set_attr", "outcome", "response_horizon_tuned", 1.0],
        ],
    }


def tune_compound_interval_rule():
    prediction_outside_envelope = Gt(
        P0("outcome", "prediction_error"),
        P0("episode", "learned_gait_prediction_error_envelope"),
    )
    post_tilt = Sqrt(Plus(
        Times(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "post"),
        ),
        Times(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "post"),
        ),
    ))
    canonical_pose_unsafe = Or(
        Gt(
            post_tilt,
            P0("episode", "learned_gait_tilt_envelope"),
        ),
        Not(Gt(
            P0("outcome", "post_z"),
            Times(
                P0("policy", "minimum_upright_height_fraction"),
                P0("episode", "standing_reference_z"),
            ),
        )),
    )
    unsafe_outcome = Or(
        receipt_material_viability_breach(),
        And(
            Not(situated_locomotion_context_active()),
            canonical_pose_unsafe,
        ),
    )
    directed_advance = Times(
        P0("episode", "heading_x"),
        Minus(
            P0("outcome", "post_x"),
            P0("outcome", "pre_x"),
        ),
    )
    productive_receipt = And(
        Not(unsafe_outcome),
        Gt(directed_advance, L(0.0)),
    )
    body_derived_interval = Max(
        L(1.0),
        IDiv(
            P0("policy", "gait_surprise_confirmation_receipts"),
            Sqrt(P0("policy", "support_phase_prior_strength")),
        ),
    )
    inhibited_interval = Times(
        body_derived_interval,
        Sqrt(P0("policy", "support_phase_prior_strength")),
    )
    next_interval = If(
        unsafe_outcome,
        inhibited_interval,
        If(
            productive_receipt,
            body_derived_interval,
            If(
                prediction_outside_envelope,
                inhibited_interval,
                body_derived_interval,
            ),
        ),
    )
    return {
        "name": "ha_tune_compound_movement_interval",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Use the learned gait envelope and exact task receipt as a "
        "reversible interaction schedule. Unsafe or unproductive surprise "
        "inhibits the rejected program but only spaces global exploration by "
        "the body-derived confirmation horizon; it cannot exponentially "
        "suppress unrelated combinations. Safe forward surprise returns to "
        "the body-derived baseline so its causal model can become precise.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Not(Eq(A("trial", "token"), A("trial", "secondary_token"))),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "prediction_error_measured"), L(1.0)),
            Eq(P0("outcome", "compound_interval_tuned"), L(0.0)),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "compound_response_interval",
                T(next_interval),
            ],
            ["set_attr", "outcome", "compound_interval_tuned", 1.0],
        ],
    }


def account_recovery_entry_rule():
    return {
        "name": "ha_account_recovery_mode_entry",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Count the actual graph state transition into recovery, "
        "independent of whether vestibular prediction, contact loss, or the "
        "shared sensorimotor interrupt authored it.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "evaluation_active"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "recovery_entry_open"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "recovery_entry_open", 1.0],
            ["set_attr", "episode", "recovery_mode_entries", T(
                Plus(P0("episode", "recovery_mode_entries"), L(1.0))
            )],
        ],
    }


def hold_deliberate_task_controller_rule():
    return {
        "name": "ha_hold_deliberate_task_controller_authority",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "An upright body executing a deliberate takeoff keeps the "
        "task controller active. Walking recovery is a competing controller, "
        "not a fault handler; it may pre-empt only after a body-limit verdict.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
            Eq(P0("episode", "upright"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "episode", "recovery_mode", 0.0],
            ["set_attr", "episode", "recovery_entry_open", 0.0],
        ],
    }


def exit_gait_recovery_rule():
    return {
        "name": "ha_exit_gait_recovery_inside_learned_envelope",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Release the postural controller once vestibular tilt is "
        "back inside the learned gait envelope and downward centre-of-mass "
        "motion has been arrested. This returns authority at a receipt-backed "
        "viability boundary rather than demanding an average pose.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "evaluation_active"), L(1.0)),
            Eq(P0("episode", "aerial_active"), L(0.0)),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
            Eq(P0("episode", "recovery_entry_open"), L(1.0)),
            Eq(P0("episode", "upright"), L(1.0)),
            Lt(
                P0("episode", "tilt_magnitude"),
                P0("episode", "learned_gait_tilt_envelope"),
            ),
            Not(Lt(P0("episode", "state_vz"), L(0.0))),
        ),
        "effects": [
            ["set_attr", "episode", "recovery_mode", 0.0],
            ["set_attr", "episode", "recovery_entry_open", 0.0],
            ["set_attr", "episode", "recovery_mode_exits", T(
                Plus(P0("episode", "recovery_mode_exits"), L(1.0))
            )],
        ],
    }


def learn_rule():
    observed_dzx = Minus(
        body_z_x("outcome", "post"),
        body_z_x("outcome", "pre"),
    )
    observed_dzy = Minus(
        body_z_y("outcome", "post"),
        body_z_y("outcome", "pre"),
    )
    observed_dwx = Minus(
        P0("outcome", "post_wx"),
        P0("outcome", "pre_wx"),
    )
    observed_dwy = Minus(
        P0("outcome", "post_wy"),
        P0("outcome", "pre_wy"),
    )
    observed_dvx = Minus(
        P0("outcome", "post_vx"),
        P0("outcome", "pre_vx"),
    )
    observed_dvy = Minus(
        P0("outcome", "post_vy"),
        P0("outcome", "pre_vy"),
    )
    observed_dvz = Minus(
        P0("outcome", "post_vz"),
        P0("outcome", "pre_vz"),
    )
    effect_magnitude = Sqrt(Plus(*[
        Times(value, value)
        for value in (
            observed_dzx,
            observed_dzy,
            observed_dwx,
            observed_dwy,
            observed_dvx,
            observed_dvy,
            observed_dvz,
        )
    ]))
    post_tilt = Sqrt(Plus(
        Times(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "post"),
        ),
        Times(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "post"),
        ),
    ))
    count = Plus(P0("model", "experience_count"), L(1.0))
    support_loss = If(
        And(
            Or(
                Gt(P0("outcome", "pre_support_0_force"), L(0.0)),
                Gt(P0("outcome", "pre_support_1_force"), L(0.0)),
            ),
            Not(Or(
                Gt(P0("outcome", "post_support_0_force"), L(0.0)),
                Gt(P0("outcome", "post_support_1_force"), L(0.0)),
            )),
        ),
        L(1.0),
        L(0.0),
    )
    support_deficit = support_deficit_observation()

    def mean(key, observation):
        return Plus(
            P0("model", key),
            Div(Minus(observation, P0("model", key)), count),
        )

    return {
        "name": "ha_learn_opaque_joint_consequence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Learn local body-axis and angular-rate effects only from "
        "verified pre/post simulator receipts.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_action_model", "model"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("motor_babble")),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "model", "mean_dzx", T(
                mean("mean_dzx", observed_dzx)
            )],
            ["set_attr", "model", "mean_dzy", T(
                mean("mean_dzy", observed_dzy)
            )],
            ["set_attr", "model", "mean_dwx", T(
                mean("mean_dwx", observed_dwx)
            )],
            ["set_attr", "model", "mean_dwy", T(
                mean("mean_dwy", observed_dwy)
            )],
            ["set_attr", "model", "mean_dvx", T(
                mean("mean_dvx", observed_dvx)
            )],
            ["set_attr", "model", "mean_dvy", T(
                mean("mean_dvy", observed_dvy)
            )],
            ["set_attr", "model", "mean_dvz", T(
                mean("mean_dvz", observed_dvz)
            )],
            ["set_attr", "model", "mean_input_energy_joules", T(
                mean(
                    "mean_input_energy_joules",
                    P0("outcome", "input_energy_joules"),
                )
            )],
            ["set_attr", "model", "support_loss_ema", T(
                mean("support_loss_ema", support_loss)
            )],
            ["set_attr", "model", "support_deficit_ema", T(
                mean("support_deficit_ema", support_deficit)
            )],
            ["set_attr", "model", "experience_count", T(count)],
            ["set_attr", "model", "last_update_request_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "episode", "single_action_effect_envelope", T(
                Max(
                    P0("episode", "single_action_effect_envelope"),
                    effect_magnitude,
                )
            )],
            ["set_attr", "episode", "single_action_tilt_envelope", T(
                Max(
                    P0("episode", "single_action_tilt_envelope"),
                    post_tilt,
                )
            )],
            ["set_attr", "outcome", "observed_dzx", T(observed_dzx)],
            ["set_attr", "outcome", "observed_dzy", T(observed_dzy)],
            ["set_attr", "outcome", "observed_dwx", T(observed_dwx)],
            ["set_attr", "outcome", "observed_dwy", T(observed_dwy)],
            ["set_attr", "outcome", "observed_dvx", T(observed_dvx)],
            ["set_attr", "outcome", "observed_dvy", T(observed_dvy)],
            ["set_attr", "outcome", "observed_dvz", T(observed_dvz)],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "learned"],
        ],
    }


def specialize_phase_context_rule():
    observed = {
        "mean_dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "mean_dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "mean_dwx": Minus(
            P0("outcome", "post_wx"),
            P0("outcome", "pre_wx"),
        ),
        "mean_dwy": Minus(
            P0("outcome", "post_wy"),
            P0("outcome", "pre_wy"),
        ),
        "mean_dvx": Minus(
            P0("outcome", "post_vx"),
            P0("outcome", "pre_vx"),
        ),
        "mean_dvy": Minus(
            P0("outcome", "post_vy"),
            P0("outcome", "pre_vy"),
        ),
        "mean_dvz": Minus(
            P0("outcome", "post_vz"),
            P0("outcome", "pre_vz"),
        ),
    }
    horizon_scale = Div(
        P0("trial", "response_frames"),
        P0("trial", "model_response_frames"),
    )
    return {
        "name": "ha_specialize_surprising_support_phase_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A surprising single-action receipt creates a new local "
        "forward-model expert anchored to its exact pre-action configuration "
        "and body state. Configuration identity selects an expert but does "
        "not by itself prove that another expert is needed; measured context "
        "distance supplies that evidence.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_model",
            ],
            [
                "phase_model",
                "generalizes_humanoid_action_model",
                "model",
            ],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("episode", "evaluation_active"), L(1.0)),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "context_specialized"), L(0.0)),
            Eq(P0("trial", "bundle_member_count"), L(1.0)),
            Eq(P0("phase_model", "context_grounded"), L(1.0)),
            Gt(
                phase_trial_context_distance("phase_model"),
                P0("phase_model", "context_radius_energy"),
            ),
        ),
        "effects": [
            ["add_node", "specialized", "HumanoidPhaseActionModel", {
                "token": T(A("phase_model", "token")),
                "ordinal": T(P0("phase_model", "ordinal")),
                "support_phase": T(P0("phase_model", "support_phase")),
                "actuator_group": T(P0("phase_model", "actuator_group")),
                "context_id": T(P0("episode", "next_phase_context_id")),
                "context_grounded": 1.0,
                "configuration_shape": T(
                    A("outcome", "pre_motor_configuration_shape")
                ),
                "initialized": 1.0,
                "experience_count": 1.0,
                "prediction_authority": 1,
                "prediction_confirmation_count": 1,
                "prediction_invalidation_count": 0,
                "prediction_reground_count": 0,
                "last_prediction_receipt_seq": T(
                    PI0("trial", "request_seq")
                ),
                "invalidated_receipt_seq": 0,
                "last_reground_receipt_seq": 0,
                "prediction_grounding_status": "receipt_grounded",
                "last_update_request_seq": T(
                    P0("trial", "request_seq")
                ),
                "anchor_z_x": T(body_z_x("outcome", "pre")),
                "anchor_z_y": T(body_z_y("outcome", "pre")),
                "anchor_wx": T(P0("outcome", "pre_wx")),
                "anchor_wy": T(P0("outcome", "pre_wy")),
                "anchor_vx": T(P0("outcome", "pre_vx")),
                "anchor_vy": T(P0("outcome", "pre_vy")),
                "anchor_vz": T(P0("outcome", "pre_vz")),
                "anchor_lateral_offset": T(
                    P0("trial", "pre_lateral_offset")
                ),
                "context_radius_energy": T(
                    phase_receipt_radius_energy()
                ),
                **{
                    key: T(Div(value, horizon_scale))
                    for key, value in observed.items()
                },
                "mean_input_energy_joules": T(Div(
                    P0("outcome", "input_energy_joules"),
                    horizon_scale,
                )),
                "support_loss_ema": T(If(
                    And(
                        Or(
                            Gt(
                                P0("outcome", "pre_support_0_force"),
                                L(0.0),
                            ),
                            Gt(
                                P0("outcome", "pre_support_1_force"),
                                L(0.0),
                            ),
                        ),
                        Not(Or(
                            Gt(
                                P0("outcome", "post_support_0_force"),
                                L(0.0),
                            ),
                            Gt(
                                P0("outcome", "post_support_1_force"),
                                L(0.0),
                            ),
                        )),
                    ),
                    L(1.0),
                    L(0.0),
                )),
                "support_deficit_ema": T(
                    support_deficit_observation()
                ),
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_phase_action_model",
                "specialized",
            ],
            [
                "add_edge",
                "specialized",
                "generalizes_humanoid_action_model",
                "model",
            ],
            ["set_attr", "episode", "next_phase_context_id", T(
                Plus(P0("episode", "next_phase_context_id"), L(1.0))
            )],
            ["set_attr", "phase_model", "last_update_request_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "outcome", "context_specialized", 1.0],
        ],
    }


def confirm_phase_prediction_rule():
    return {
        "name": "ha_confirm_local_phase_prediction_from_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A verified, identifiable receipt confirms a local model "
        "when predicted and observed motion have the same sign relative to "
        "the currently requested heading. Confirmation is integer evidence, "
        "not elapsed-time freshness.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_model",
            ],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(PI0("outcome", "receipt_verified"), L(1)),
            Eq(PI0("outcome", "context_specialized"), L(0)),
            Eq(PI0("trial", "bundle_member_count"), L(1)),
            phase_prediction_authoritative("phase_model"),
            Lt(
                PI0("phase_model", "last_prediction_receipt_seq"),
                PI0("trial", "request_seq"),
            ),
            Eq(predicted_directed_sign(), observed_directed_sign()),
        ),
        "effects": [
            [
                "set_attr",
                "phase_model",
                "prediction_confirmation_count",
                T(Plus(
                    PI0("phase_model", "prediction_confirmation_count"),
                    L(1),
                )),
            ],
            [
                "set_attr",
                "phase_model",
                "last_prediction_receipt_seq",
                T(PI0("trial", "request_seq")),
            ],
            [
                "set_attr",
                "phase_model",
                "prediction_grounding_status",
                "receipt_confirmed",
            ],
        ],
    }


def invalidate_stale_phase_prediction_rule():
    return {
        "name": "ha_invalidate_stale_local_phase_prediction",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "An identifiable verified receipt whose directed-motion "
        "sign contradicts the issued prediction immediately withdraws that "
        "local model's selection authority. No clock, timeout, fixed residual "
        "tolerance, or Python policy participates.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_model",
            ],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(PI0("outcome", "receipt_verified"), L(1)),
            Eq(PI0("outcome", "context_specialized"), L(0)),
            Eq(PI0("trial", "bundle_member_count"), L(1)),
            phase_prediction_authoritative("phase_model"),
            Lt(
                PI0("phase_model", "last_prediction_receipt_seq"),
                PI0("trial", "request_seq"),
            ),
            Not(Eq(predicted_directed_sign(), observed_directed_sign())),
        ),
        "effects": [
            ["set_attr", "phase_model", "prediction_authority", 0],
            [
                "set_attr",
                "phase_model",
                "prediction_invalidation_count",
                T(Plus(
                    PI0("phase_model", "prediction_invalidation_count"),
                    L(1),
                )),
            ],
            [
                "set_attr",
                "phase_model",
                "last_prediction_receipt_seq",
                T(PI0("trial", "request_seq")),
            ],
            [
                "set_attr",
                "phase_model",
                "invalidated_receipt_seq",
                T(PI0("trial", "request_seq")),
            ],
            [
                "set_attr",
                "phase_model",
                "prediction_grounding_status",
                "receipt_contradicted",
            ],
        ],
    }


def reground_invalidated_phase_prediction_rule():
    observed = {
        "mean_dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "mean_dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "mean_dwx": Minus(
            P0("outcome", "post_wx"),
            P0("outcome", "pre_wx"),
        ),
        "mean_dwy": Minus(
            P0("outcome", "post_wy"),
            P0("outcome", "pre_wy"),
        ),
        "mean_dvx": Minus(
            P0("outcome", "post_vx"),
            P0("outcome", "pre_vx"),
        ),
        "mean_dvy": Minus(
            P0("outcome", "post_vy"),
            P0("outcome", "pre_vy"),
        ),
        "mean_dvz": Minus(
            P0("outcome", "post_vz"),
            P0("outcome", "pre_vz"),
        ),
    }
    horizon_scale = Div(
        P0("trial", "response_frames"),
        P0("trial", "model_response_frames"),
    )
    return {
        "name": "ha_reground_invalidated_local_phase_prediction",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "The same contradictory verified receipt re-anchors the "
        "bounded local expert in place. Authority returns only after every "
        "consequence and context anchor has been replaced by that receipt; no "
        "unbounded expert population or host-side retraining is introduced.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_model",
            ],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(PI0("outcome", "receipt_verified"), L(1)),
            Eq(PI0("outcome", "context_specialized"), L(0)),
            Eq(PI0("trial", "bundle_member_count"), L(1)),
            Eq(PI0("phase_model", "prediction_authority"), L(0)),
            Eq(
                PI0("phase_model", "invalidated_receipt_seq"),
                PI0("trial", "request_seq"),
            ),
            Lt(
                PI0("phase_model", "last_reground_receipt_seq"),
                PI0("trial", "request_seq"),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "phase_model",
                key,
                T(Div(value, horizon_scale)),
            ]
            for key, value in observed.items()
        ] + [
            [
                "set_attr",
                "phase_model",
                "mean_input_energy_joules",
                T(Div(
                    P0("outcome", "input_energy_joules"),
                    horizon_scale,
                )),
            ],
            [
                "set_attr",
                "phase_model",
                "support_loss_ema",
                T(If(
                    And(
                        Or(
                            Gt(P0("outcome", "pre_support_0_force"), L(0)),
                            Gt(P0("outcome", "pre_support_1_force"), L(0)),
                        ),
                        Not(Or(
                            Gt(P0("outcome", "post_support_0_force"), L(0)),
                            Gt(P0("outcome", "post_support_1_force"), L(0)),
                        )),
                    ),
                    L(1),
                    L(0),
                )),
            ],
            [
                "set_attr",
                "phase_model",
                "support_deficit_ema",
                T(support_deficit_observation()),
            ],
            ["set_attr", "phase_model", "experience_count", 1],
            ["set_attr", "phase_model", "anchor_z_x", T(
                body_z_x("outcome", "pre")
            )],
            ["set_attr", "phase_model", "anchor_z_y", T(
                body_z_y("outcome", "pre")
            )],
            *[
                ["set_attr", "phase_model", f"anchor_{key}", T(
                    P0("outcome", f"pre_{key}")
                )]
                for key in ("wx", "wy", "vx", "vy", "vz")
            ],
            [
                "set_attr",
                "phase_model",
                "anchor_lateral_offset",
                T(P0("trial", "pre_lateral_offset")),
            ],
            [
                "set_attr",
                "phase_model",
                "context_radius_energy",
                T(phase_receipt_radius_energy()),
            ],
            [
                "set_attr",
                "phase_model",
                "configuration_shape",
                T(A("outcome", "pre_motor_configuration_shape")),
            ],
            ["set_attr", "phase_model", "context_grounded", 1],
            [
                "set_attr",
                "phase_model",
                "last_update_request_seq",
                T(PI0("trial", "request_seq")),
            ],
            ["set_attr", "phase_model", "prediction_authority", 1],
            [
                "set_attr",
                "phase_model",
                "prediction_reground_count",
                T(Plus(
                    PI0("phase_model", "prediction_reground_count"),
                    L(1),
                )),
            ],
            [
                "set_attr",
                "phase_model",
                "last_reground_receipt_seq",
                T(PI0("trial", "request_seq")),
            ],
            [
                "set_attr",
                "phase_model",
                "prediction_grounding_status",
                "receipt_regrounded",
            ],
            ["set_attr", "outcome", "phase_prediction_regrounded", 1],
        ],
    }


def learn_phase_consequence_rule():
    observed = {
        "mean_dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "mean_dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "mean_dwx": Minus(
            P0("outcome", "post_wx"),
            P0("outcome", "pre_wx"),
        ),
        "mean_dwy": Minus(
            P0("outcome", "post_wy"),
            P0("outcome", "pre_wy"),
        ),
        "mean_dvx": Minus(
            P0("outcome", "post_vx"),
            P0("outcome", "pre_vx"),
        ),
        "mean_dvy": Minus(
            P0("outcome", "post_vy"),
            P0("outcome", "pre_vy"),
        ),
        "mean_dvz": Minus(
            P0("outcome", "post_vz"),
            P0("outcome", "pre_vz"),
        ),
    }
    count = Plus(P0("phase_model", "experience_count"), L(1.0))
    horizon_scale = Div(
        P0("trial", "response_frames"),
        P0("trial", "model_response_frames"),
    )
    support_loss = If(
        And(
            Or(
                Gt(P0("outcome", "pre_support_0_force"), L(0.0)),
                Gt(P0("outcome", "pre_support_1_force"), L(0.0)),
            ),
            Not(Or(
                Gt(P0("outcome", "post_support_0_force"), L(0.0)),
                Gt(P0("outcome", "post_support_1_force"), L(0.0)),
            )),
        ),
        L(1.0),
        L(0.0),
    )
    support_deficit = support_deficit_observation()

    def mean(key):
        residual = Minus(
            observed[key],
            P0("trial", f"predicted_{key[5:]}"),
        )
        credited_full_horizon = Plus(
            P0("phase_model", key),
            Div(
                residual,
                Times(
                    P0("trial", "bundle_member_count"),
                    horizon_scale,
                ),
            ),
        )
        return Plus(
            P0("phase_model", key),
            Div(
                Minus(
                    credited_full_horizon,
                    P0("phase_model", key),
                ),
                count,
            ),
        )

    return {
        "name": "ha_learn_support_phase_consequence_online",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Update a primitive forward model only from an identifiable "
        "single-member receipt. Multi-member residuals stay on their exact "
        "motor program instead of being smeared across underdetermined causes.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_model",
            ],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("episode", "online_phase_learning"), L(1.0)),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "context_specialized"), L(0.0)),
            Eq(P0("trial", "bundle_member_count"), L(1.0)),
            Lt(
                P0("phase_model", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
            Or(
                Eq(P0("phase_model", "context_grounded"), L(0.0)),
                Not(Gt(
                    phase_trial_context_distance("phase_model"),
                    P0("phase_model", "context_radius_energy"),
                )),
            ),
            Or(
                Lt(
                    P0("phase_model", "experience_count"),
                    Plus(
                        P0("policy", "support_phase_prior_strength"),
                        L(1.0),
                    ),
                ),
            ),
        ),
        "effects": [
            ["set_attr", "phase_model", key, T(mean(key))]
            for key in observed
        ] + [
            ["set_attr", "phase_model", "mean_input_energy_joules", T(
                Plus(
                    P0("phase_model", "mean_input_energy_joules"),
                    Div(
                        Minus(
                            Div(
                                P0("outcome", "input_energy_joules"),
                                horizon_scale,
                            ),
                            P0(
                                "phase_model",
                                "mean_input_energy_joules",
                            ),
                        ),
                        count,
                    ),
                )
            )],
            ["set_attr", "phase_model", "support_loss_ema", T(
                Plus(
                    P0("phase_model", "support_loss_ema"),
                    Div(
                        Minus(
                            support_loss,
                            P0("phase_model", "support_loss_ema"),
                        ),
                        count,
                    ),
                )
            )],
            ["set_attr", "phase_model", "support_deficit_ema", T(
                Plus(
                    P0("phase_model", "support_deficit_ema"),
                    Div(
                        Minus(
                            support_deficit,
                            P0("phase_model", "support_deficit_ema"),
                        ),
                        count,
                    ),
                )
            )],
            ["set_attr", "phase_model", "experience_count", T(count)],
            ["set_attr", "phase_model", "anchor_z_x", T(If(
                Eq(P0("phase_model", "context_grounded"), L(0.0)),
                body_z_x("outcome", "pre"),
                P0("phase_model", "anchor_z_x"),
            ))],
            ["set_attr", "phase_model", "anchor_z_y", T(If(
                Eq(P0("phase_model", "context_grounded"), L(0.0)),
                body_z_y("outcome", "pre"),
                P0("phase_model", "anchor_z_y"),
            ))],
            *[
                ["set_attr", "phase_model", f"anchor_{key}", T(If(
                    Eq(P0("phase_model", "context_grounded"), L(0.0)),
                    P0("outcome", f"pre_{key}"),
                    P0("phase_model", f"anchor_{key}"),
                ))]
                for key in ("wx", "wy", "vx", "vy", "vz")
            ],
            ["set_attr", "phase_model", "anchor_lateral_offset", T(If(
                Eq(P0("phase_model", "context_grounded"), L(0.0)),
                P0("trial", "pre_lateral_offset"),
                P0("phase_model", "anchor_lateral_offset"),
            ))],
            ["set_attr", "phase_model", "context_radius_energy", T(If(
                Eq(P0("phase_model", "context_grounded"), L(0.0)),
                phase_receipt_radius_energy(),
                P0("phase_model", "context_radius_energy"),
            ))],
            ["set_attr", "phase_model", "configuration_shape", T(If(
                Eq(P0("phase_model", "context_grounded"), L(0.0)),
                A("outcome", "pre_motor_configuration_shape"),
                A("phase_model", "configuration_shape"),
            ))],
            ["set_attr", "phase_model", "context_grounded", 1.0],
            [
                "set_attr",
                "phase_model",
                "last_update_request_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def finish_phase_program_learning_rule():
    members = Neighbours("trial", "uses_humanoid_phase_action_model")
    programs = Neighbours("trial", "enacts_humanoid_motor_program")
    eligible_pending = Filter(
        members,
        "member",
        And(
            Eq(P0("trial", "bundle_member_count"), L(1.0)),
            Lt(
                P0("member", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
            Or(
                Lt(
                    P0("member", "experience_count"),
                    Plus(
                        P0("policy", "support_phase_prior_strength"),
                        L(1.0),
                    ),
                ),
            ),
        ),
    )
    updated = Or(
        Exists(
            members,
            "member",
            Eq(
                P0("member", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        Exists(
            programs,
            "program",
            Eq(
                P0("program", "last_memory_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        Exists(
            SYNERGIES,
            "synergy",
            Eq(
                P0("synergy", "last_program_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
    )
    discovered_context = Exists(
        members,
        "member",
        And(
            Eq(
                P0("member", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
            Eq(
                P0("member", "experience_count"),
                Plus(
                    P0("policy", "support_phase_prior_strength"),
                    L(1.0),
                ),
            ),
        ),
    )
    return {
        "name": "ha_finish_arbitrary_program_credit_assignment",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Close one walking receipt only after every eligible "
        "motor-program member has received its share of the residual.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
            Eq(Count(eligible_pending), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "last_phase_learning_request_seq", T(
                If(
                    discovered_context,
                    P0("trial", "request_seq"),
                    P0("episode", "last_phase_learning_request_seq"),
                )
            )],
            ["set_attr", "episode", "phase_adaptation_complete", T(
                If(
                    And(
                        discovered_context,
                        Eq(
                            P0("episode", "evaluation_active"),
                            L(0.0),
                        ),
                    ),
                    L(0.0),
                    P0("episode", "phase_adaptation_complete"),
                )
            )],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "episode", "last_locomotor_token", T(
                A("trial", "token")
            )],
            ["set_attr", "trial", "status", T(If(
                updated,
                L("adapted_online"),
                L("observed_control"),
            ))],
        ],
    }


def learn_motor_program_receipt_rule():
    observed = {
        "dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "dwx": Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx")),
        "dwy": Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy")),
        "dvx": Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx")),
        "dvy": Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy")),
        "dvz": Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz")),
    }
    support_preserved = Or(
        Not(Or(
            Gt(P0("outcome", "pre_support_0_force"), L(0.0)),
            Gt(P0("outcome", "pre_support_1_force"), L(0.0)),
        )),
        Gt(P0("outcome", "post_support_0_force"), L(0.0)),
        Gt(P0("outcome", "post_support_1_force"), L(0.0)),
    )
    safe_memory = And(
        Gt(P0("plan", "member_count"), L(0.0)),
        motor_receipt_memory_viable(),
    )
    initial_prediction_error = motor_error_energy(
        observed,
        {
            key: P0("trial", f"predicted_{key}")
            for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
        },
    )
    initial_lateral_prediction_error = motor_lateral_error_energy(
        observed,
        {
            key: P0("trial", f"predicted_{key}")
            for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
        },
    )
    directed_advance = Times(
        P0("episode", "heading_x"),
        Minus(
            P0("outcome", "post_x"),
            P0("outcome", "pre_x"),
        ),
    )
    return {
        "name": "ha_ground_synthesized_motor_program_from_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Retain the exact arbitrary program and its nonlinear "
        "whole-bundle residual as a grounded analysis-by-synthesis record.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "plan"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("plan", "receipt_learned"), L(0.0)),
        ),
        "effects": [
            *[
                ["set_attr", "plan", f"observed_{key}", T(value)]
                for key, value in observed.items()
            ],
            *[
                ["set_attr", "plan", f"mean_{key}", T(value)]
                for key, value in observed.items()
            ],
            *[
                [
                    "set_attr",
                    "plan",
                    f"mean_rate_{key}",
                    T(Div(value, P0("trial", "response_frames"))),
                ]
                for key, value in observed.items()
            ],
            *[
                ["set_attr", "plan", f"residual_{key}", T(Minus(
                    value,
                    P0("trial", f"predicted_{key}"),
                ))]
                for key, value in observed.items()
            ],
            ["set_attr", "plan", "receipt_learned", 1.0],
            ["set_attr", "plan", "name", T(
                grounded_motor_program_name("plan")
            )],
            ["set_attr", "plan", "signature", T(
                grounded_motor_program_signature("plan")
            )],
            ["set_attr", "plan", "motor_task_phase", T(
                motor_task_phase()
            )],
            ["set_attr", "plan", "observed_height_energy_relation", T(
                observed_height_energy_relation()
            )],
            ["set_attr", "plan", "experience_count", 1.0],
            [
                "set_attr",
                "plan",
                "mean_directed_advance",
                T(directed_advance),
            ],
            [
                "set_attr",
                "plan",
                "mean_input_energy_joules",
                T(P0("outcome", "input_energy_joules")),
            ],
            ["set_attr", "plan", "support_loss_ema", T(If(
                support_preserved,
                L(0.0),
                L(1.0),
            ))],
            ["set_attr", "plan", "support_deficit_ema", T(
                support_deficit_observation()
            )],
            [
                "set_attr",
                "plan",
                "mean_prediction_error_energy",
                T(initial_prediction_error),
            ],
            [
                "set_attr",
                "plan",
                "mean_lateral_prediction_error_energy",
                T(initial_lateral_prediction_error),
            ],
            ["set_attr", "plan", "last_memory_update_request_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "plan", "memory_eligible", T(If(
                safe_memory,
                L(1.0),
                L(0.0),
            ))],
            ["set_attr", "plan", "status", "grounded"],
        ],
    }


def update_recalled_motor_memory_rule():
    observed = {
        "dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "dwx": Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx")),
        "dwy": Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy")),
        "dvx": Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx")),
        "dvy": Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy")),
        "dvz": Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz")),
    }
    count = Plus(P0("memory", "experience_count"), L(1.0))
    prediction_error = motor_consequence_error_energy(observed)
    lateral_prediction_error = motor_lateral_consequence_error_energy(
        observed
    )
    support_preserved = Or(
        Not(Or(
            Gt(P0("outcome", "pre_support_0_force"), L(0.0)),
            Gt(P0("outcome", "pre_support_1_force"), L(0.0)),
        )),
        Gt(P0("outcome", "post_support_0_force"), L(0.0)),
        Gt(P0("outcome", "post_support_1_force"), L(0.0)),
    )
    receipt_viable = motor_receipt_memory_viable()

    def mean(key):
        return Plus(
            P0("memory", f"mean_{key}"),
            Div(
                Minus(
                    observed[key],
                    P0("memory", f"mean_{key}"),
                ),
                count,
            ),
        )

    def mean_rate(key):
        observed_rate = Div(
            observed[key],
            P0("trial", "response_frames"),
        )
        return Plus(
            P0("memory", f"mean_rate_{key}"),
            Div(
                Minus(
                    observed_rate,
                    P0("memory", f"mean_rate_{key}"),
                ),
                count,
            ),
        )

    mean_prediction_error = Plus(
        P0("memory", "mean_prediction_error_energy"),
        Div(
            Minus(
                prediction_error,
                P0("memory", "mean_prediction_error_energy"),
            ),
            count,
        ),
    )
    mean_lateral_prediction_error = Plus(
        P0("memory", "mean_lateral_prediction_error_energy"),
        Div(
            Minus(
                lateral_prediction_error,
                P0("memory", "mean_lateral_prediction_error_energy"),
            ),
            count,
        ),
    )
    tuned_response_frames = If(
        Gt(
            prediction_error,
            P0("memory", "mean_prediction_error_energy"),
        ),
        Max(
            L(1.0),
            Minus(P0("memory", "response_frames"), L(1.0)),
        ),
        Min(
            P0("episode", "response_frames"),
            Plus(P0("memory", "response_frames"), L(1.0)),
        ),
    )
    next_response_frames = If(
        Or(
            And(
                Eq(
                    P0("trial", "motor_memory_structurally_reused"),
                    L(1.0),
                ),
                Eq(
                    P0("memory", "warm_start_requires_verification"),
                    L(1.0),
                ),
                Eq(P0("memory", "warm_start_verified"), L(0.0)),
            ),
            Eq(P0("memory", "partial_trajectory_evidence"), L(1.0)),
        ),
        P0("trial", "response_frames"),
        tuned_response_frames,
    )
    directed_advance = Times(
        P0("episode", "heading_x"),
        Minus(
            P0("outcome", "post_x"),
            P0("outcome", "pre_x"),
        ),
    )
    mean_directed_advance = Plus(
        P0("memory", "mean_directed_advance"),
        Div(
            Minus(
                directed_advance,
                P0("memory", "mean_directed_advance"),
            ),
            count,
        ),
    )
    mean_input_energy = Plus(
        P0("memory", "mean_input_energy_joules"),
        Div(
            Minus(
                P0("outcome", "input_energy_joules"),
                P0("memory", "mean_input_energy_joules"),
            ),
            count,
        ),
    )
    mean_support_loss = Plus(
        P0("memory", "support_loss_ema"),
        Div(
            Minus(
                If(support_preserved, L(0.0), L(1.0)),
                P0("memory", "support_loss_ema"),
            ),
            count,
        ),
    )
    mean_support_deficit = Plus(
        P0("memory", "support_deficit_ema"),
        Div(
            Minus(
                support_deficit_observation(),
                P0("memory", "support_deficit_ema"),
            ),
            count,
        ),
    )
    takeoff_future_retained = And(
        Eq(P0("memory", "partial_trajectory_evidence"), L(1.0)),
        Eq(A("memory", "motor_task_context"), L("self_takeoff")),
        Or(
            And(
                Eq(
                    P0("memory", "selected_path_projection_request_seq"),
                    P0("trial", "request_seq"),
                ),
                Gt(
                    P0(
                        "memory",
                        "selected_path_narrativium_retained_dvz",
                    ),
                    L(0.0),
                ),
            ),
            And(
                Gt(
                    developmental_trajectory_projection(
                        "memory", "support"
                    ),
                    L(0.0),
                ),
                Gt(
                    developmental_trajectory_projection(
                        "memory", "resolved"
                    ),
                    L(0.0),
                ),
                Gt(
                    developmental_trajectory_projection(
                        "memory",
                        "narrativium_retained_dvz",
                    ),
                    L(0.0),
                ),
            ),
        ),
    )
    retains_transferred_value = Or(
        Eq(
            P0("memory", "warm_start_requires_verification"),
            L(0.0),
        ),
        Eq(
            P0("trial", "motor_memory_structurally_reused"),
            L(1.0),
        ),
        takeoff_future_retained,
        Not(Lt(
            directed_advance,
            P0("trial", "expected_directed_advance"),
        )),
    )
    return {
        "name": "ha_update_reassociated_motor_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A recalled population program receives its own exact "
        "sensory consequence. Update the stable repertoire trajectory as a "
        "whole and withdraw it from output-potent recall after a material "
        "viability breach rather than treating situated pose, support or "
        "load tradeoffs as faults or misassigning error to members.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Or(
                Eq(P0("trial", "motor_memory_recalled"), L(1.0)),
                Eq(
                    P0("trial", "motor_memory_structurally_reused"),
                    L(1.0),
                ),
            ),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("memory", "receipt_learned"), L(1.0)),
            Lt(
                P0("memory", "last_memory_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [[
                "set_attr",
                "memory",
                f"mean_{key}",
                T(mean(key)),
            ]
            for key in observed
        ] + [
            [
                "set_attr",
                "memory",
                f"mean_rate_{key}",
                T(mean_rate(key)),
            ]
            for key in observed
        ] + [
            ["set_attr", "memory", "motor_task_phase", T(
                motor_task_phase()
            )],
            ["set_attr", "memory", "experience_count", T(count)],
            [
                "set_attr",
                "memory",
                "mean_directed_advance",
                T(mean_directed_advance),
            ],
            [
                "set_attr",
                "memory",
                "mean_input_energy_joules",
                T(mean_input_energy),
            ],
            ["set_attr", "memory", "support_loss_ema", T(
                mean_support_loss
            )],
            ["set_attr", "memory", "support_deficit_ema", T(
                mean_support_deficit
            )],
            [
                "set_attr",
                "memory",
                "mean_prediction_error_energy",
                T(mean_prediction_error),
            ],
            [
                "set_attr",
                "memory",
                "mean_lateral_prediction_error_energy",
                T(mean_lateral_prediction_error),
            ],
            [
                "set_attr",
                "memory",
                "response_frames",
                T(next_response_frames),
            ],
            [
                "set_attr",
                "memory",
                "last_memory_update_request_seq",
                T(P0("trial", "request_seq")),
            ],
            ["set_attr", "memory", "warm_start_verified", 1.0],
            ["set_attr", "memory", "memory_eligible", T(If(
                And(receipt_viable, retains_transferred_value),
                L(1.0),
                L(0.0),
            ))],
        ],
    }


def consolidate_equivalent_motor_program_rule():
    """Credit a synthesized duplicate to its canonical structural memory."""
    observed = {
        "dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "dwx": Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx")),
        "dwy": Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy")),
        "dvx": Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx")),
        "dvy": Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy")),
        "dvz": Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz")),
    }
    candidates = equivalent_motor_memories()
    canonical = Argmin(
        candidates,
        "canonical_candidate",
        canonical_motor_memory_rank("canonical_candidate"),
        V("plan"),
    )
    count = Plus(P0("memory", "experience_count"), L(1.0))
    prediction_error = motor_consequence_error_energy(observed, "memory")
    lateral_prediction_error = motor_lateral_consequence_error_energy(
        observed,
        "memory",
    )
    receipt_viable = motor_receipt_memory_viable()

    def mean(key):
        return Plus(
            P0("memory", f"mean_{key}"),
            Div(
                Minus(observed[key], P0("memory", f"mean_{key}")),
                count,
            ),
        )

    def mean_rate(key):
        observed_rate = Div(
            observed[key],
            P0("trial", "response_frames"),
        )
        return Plus(
            P0("memory", f"mean_rate_{key}"),
            Div(
                Minus(
                    observed_rate,
                    P0("memory", f"mean_rate_{key}"),
                ),
                count,
            ),
        )

    mean_prediction_error = Plus(
        P0("memory", "mean_prediction_error_energy"),
        Div(
            Minus(
                prediction_error,
                P0("memory", "mean_prediction_error_energy"),
            ),
            count,
        ),
    )
    mean_lateral_prediction_error = Plus(
        P0("memory", "mean_lateral_prediction_error_energy"),
        Div(
            Minus(
                lateral_prediction_error,
                P0("memory", "mean_lateral_prediction_error_energy"),
            ),
            count,
        ),
    )
    next_response_frames = If(
        Gt(
            prediction_error,
            P0("memory", "mean_prediction_error_energy"),
        ),
        Max(
            L(1.0),
            Minus(P0("memory", "response_frames"), L(1.0)),
        ),
        Min(
            P0("episode", "response_frames"),
            Plus(P0("memory", "response_frames"), L(1.0)),
        ),
    )
    directed_advance = Times(
        P0("episode", "heading_x"),
        Minus(
            P0("outcome", "post_x"),
            P0("outcome", "pre_x"),
        ),
    )
    mean_directed_advance = Plus(
        P0("memory", "mean_directed_advance"),
        Div(
            Minus(
                directed_advance,
                P0("memory", "mean_directed_advance"),
            ),
            count,
        ),
    )
    return {
        "name": "ha_consolidate_equivalent_motor_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Structurally identical analysis-by-synthesis programs "
        "share one canonical population memory. Credit the verified duplicate "
        "receipt to that memory and rewire temporal learning to the stable "
        "node instead of fragmenting experience by request identity. The "
        "same situated/material receipt viability predicate governs initial, "
        "recalled and consolidated memory authority.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_program", "plan"],
            ["episode", "has_humanoid_motor_program", "memory"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "plan"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("plan", "receipt_learned"), L(0.0)),
            Eq(V("memory"), canonical),
            Not(Eq(V("plan"), V("memory"))),
        ),
        "effects": [
            [
                "set_attr",
                "memory",
                f"mean_{key}",
                T(mean(key)),
            ]
            for key in observed
        ] + [
            [
                "set_attr",
                "memory",
                f"mean_rate_{key}",
                T(mean_rate(key)),
            ]
            for key in observed
        ] + [
            ["set_attr", "memory", "experience_count", T(count)],
            [
                "set_attr",
                "memory",
                "mean_directed_advance",
                T(mean_directed_advance),
            ],
            [
                "set_attr",
                "memory",
                "mean_prediction_error_energy",
                T(mean_prediction_error),
            ],
            [
                "set_attr",
                "memory",
                "mean_lateral_prediction_error_energy",
                T(mean_lateral_prediction_error),
            ],
            [
                "set_attr",
                "memory",
                "response_frames",
                T(next_response_frames),
            ],
            ["set_attr", "memory", "memory_eligible", T(If(
                receipt_viable,
                L(1.0),
                L(0.0),
            ))],
            ["set_attr", "memory", "consolidation_count", T(
                Plus(P0("memory", "consolidation_count"), L(1.0))
            )],
            ["set_attr", "memory", "last_memory_update_request_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "plan", "receipt_learned", 1.0],
            ["set_attr", "plan", "memory_eligible", 0.0],
            ["set_attr", "plan", "status", "consolidated_duplicate"],
            ["set_attr", "trial", "motor_memory_consolidated", 1.0],
            [
                "del_edge",
                "episode",
                "has_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "has_consolidated_humanoid_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "trial",
                "enacts_humanoid_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "trial",
                "enacts_humanoid_motor_program",
                "memory",
            ],
            [
                "add_edge",
                "trial",
                "synthesized_humanoid_motor_program",
                "plan",
            ],
        ],
    }


def observed_motor_consequence(outcome="outcome"):
    return {
        "dzx": Minus(
            body_z_x(outcome, "post"),
            body_z_x(outcome, "pre"),
        ),
        "dzy": Minus(
            body_z_y(outcome, "post"),
            body_z_y(outcome, "pre"),
        ),
        "dwx": Minus(P0(outcome, "post_wx"), P0(outcome, "pre_wx")),
        "dwy": Minus(P0(outcome, "post_wy"), P0(outcome, "pre_wy")),
        "dvx": Minus(P0(outcome, "post_vx"), P0(outcome, "pre_vx")),
        "dvy": Minus(P0(outcome, "post_vy"), P0(outcome, "pre_vy")),
        "dvz": Minus(P0(outcome, "post_vz"), P0(outcome, "pre_vz")),
    }


def situated_motor_fixation_is_stable():
    """A supported, locally quiet configuration can serve as a fixation.

    The tolerance is derived from the acceleration gravity can add in one
    physics tick.  It therefore scales with the world rather than encoding a
    privileged posture or a tuned humanoid-specific speed.
    """
    one_tick_velocity = Times(
        P0("episode", "gravity_acceleration"),
        P0("episode", "physics_time_step"),
    )
    joint_velocity_budget = Times(
        Max(L(1.0), P0("episode", "state_joint_count")),
        one_tick_velocity,
        one_tick_velocity,
    )
    return And(
        Gt(P0("episode", "active_support_count"), L(0.0)),
        Lt(Abs(P0("episode", "state_vx")), one_tick_velocity),
        Lt(Abs(P0("episode", "state_vy")), one_tick_velocity),
        Lt(Abs(P0("episode", "state_vz")), one_tick_velocity),
        Lt(P0("episode", "state_joint_velocity_energy"), joint_velocity_budget),
    )


def mint_situated_motor_fixation_rule():
    return {
        "name": "ha_mint_situated_motor_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Treat a supported quiet configuration as a temporary "
        "experimental fixation. It is a sensed, strictly local platform.",
        "match": [["agent", "has_humanoid_episode", "episode"]],
        "where": And(
            Eq(
                Count(Neighbours("episode", "has_current_humanoid_motor_fixation")),
                L(0.0),
            ),
            situated_motor_fixation_is_stable(),
        ),
        "effects": [
            ["add_node", "fixation", "HumanoidMotorFixation", {
                "joint_configuration": T(A("episode", "state_joint_configuration")),
                "configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "state_seq": T(P0("episode", "state_seq")),
                "support_count": T(P0("episode", "active_support_count")),
                "observation_count": 1.0,
                "reference_kind": "current_sensed_configuration",
                "status": "confirmed",
            }],
            ["add_edge", "episode", "has_humanoid_motor_fixation", "fixation"],
            ["add_edge", "episode", "has_current_humanoid_motor_fixation", "fixation"],
            ["set_attr", "episode", "motor_fixation_count", T(
                Plus(P0("episode", "motor_fixation_count"), L(1.0))
            )],
        ],
    }


def refresh_situated_motor_fixation_rule():
    return {
        "name": "ha_refresh_situated_motor_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Repeatedly sensing the same stable configuration adds "
        "confidence to that local fixation without inventing an origin.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_motor_fixation", "fixation"],
        ],
        "where": And(
            situated_motor_fixation_is_stable(),
            Eq(
                A("fixation", "configuration_shape"),
                A("episode", "state_motor_configuration_shape"),
            ),
            Gt(P0("episode", "state_seq"), P0("fixation", "state_seq")),
        ),
        "effects": [
            ["set_attr", "fixation", "state_seq", T(P0("episode", "state_seq"))],
            ["set_attr", "fixation", "support_count", T(
                P0("episode", "active_support_count")
            )],
            ["set_attr", "fixation", "observation_count", T(
                Plus(P0("fixation", "observation_count"), L(1.0))
            )],
        ],
    }


def reanchor_motor_fixation_after_fixture_reset_rule():
    return {
        "name": "ha_reanchor_motor_fixation_after_fixture_reset",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A declared mechanical reset invalidates the old local "
        "frame but preserves learned models; the sensed stable fixture becomes "
        "the new situated reference without implying a universal origin.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_motor_fixation", "previous"],
        ],
        "where": And(
            Gt(
                P0("episode", "motor_fixture_reset_seq"),
                P0("episode", "motor_fixture_reset_processed_seq"),
            ),
            situated_motor_fixation_is_stable(),
        ),
        "effects": [
            ["add_node", "fixation", "HumanoidMotorFixation", {
                "joint_configuration": T(A("episode", "state_joint_configuration")),
                "configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "state_seq": T(P0("episode", "state_seq")),
                "support_count": T(P0("episode", "active_support_count")),
                "observation_count": 1.0,
                "reference_kind": "mechanical_fixture_reset_receipt",
                "status": "confirmed",
            }],
            ["del_edge", "episode", "has_current_humanoid_motor_fixation", "previous"],
            ["add_edge", "episode", "has_current_humanoid_motor_fixation", "fixation"],
            ["add_edge", "episode", "has_humanoid_motor_fixation", "fixation"],
            ["set_attr", "previous", "status", "invalidated_by_fixture_reset"],
            ["set_attr", "episode", "motor_fixture_reset_processed_seq", T(
                P0("episode", "motor_fixture_reset_seq")
            )],
            ["set_attr", "episode", "motor_fixation_count", T(
                Plus(P0("episode", "motor_fixation_count"), L(1.0))
            )],
        ],
    }


def invalidate_candidate_fixation_after_fixture_reset_rule():
    return {
        "name": "ha_invalidate_candidate_fixation_after_fixture_reset",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_candidate_humanoid_motor_fixation", "candidate"],
        ],
        "where": Gt(
            P0("episode", "motor_fixture_reset_seq"),
            P0("candidate", "fixture_reset_seq"),
        ),
        "effects": [
            ["del_edge", "episode", "has_candidate_humanoid_motor_fixation", "candidate"],
            ["set_attr", "candidate", "status", "invalidated_by_fixture_reset"],
            ["set_attr", "candidate", "fixture_reset_seq", T(
                P0("episode", "motor_fixture_reset_seq")
            )],
        ],
    }


def propose_situated_motor_fixation_rule():
    return {
        "name": "ha_propose_situated_motor_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A single quiet observation proposes a candidate basin; "
        "it cannot move the active motor reference yet.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_motor_fixation", "previous"],
        ],
        "where": And(
            Eq(
                Count(Neighbours("episode", "has_candidate_humanoid_motor_fixation")),
                L(0.0),
            ),
            situated_motor_fixation_is_stable(),
            Not(Eq(
                A("previous", "configuration_shape"),
                A("episode", "state_motor_configuration_shape"),
            )),
            Gt(P0("episode", "state_seq"), P0("previous", "state_seq")),
        ),
        "effects": [
            ["add_node", "fixation", "HumanoidMotorFixation", {
                "joint_configuration": T(A("episode", "state_joint_configuration")),
                "configuration_shape": T(
                    A("episode", "state_motor_configuration_shape")
                ),
                "state_seq": T(P0("episode", "state_seq")),
                "support_count": T(P0("episode", "active_support_count")),
                "observation_count": 1.0,
                "reference_kind": "current_sensed_configuration",
                "fixture_reset_seq": T(P0("episode", "motor_fixture_reset_seq")),
                "status": "candidate",
            }],
            ["add_edge", "episode", "has_candidate_humanoid_motor_fixation", "fixation"],
            ["add_edge", "episode", "has_humanoid_motor_fixation", "fixation"],
            ["set_attr", "episode", "motor_fixation_count", T(
                Plus(P0("episode", "motor_fixation_count"), L(1.0))
            )],
        ],
    }


def refresh_candidate_motor_fixation_rule():
    return {
        "name": "ha_refresh_candidate_motor_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Repeated stable observations accumulate evidence for a "
        "candidate without changing command authority.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_candidate_humanoid_motor_fixation", "candidate"],
        ],
        "where": And(
            situated_motor_fixation_is_stable(),
            Eq(
                A("candidate", "configuration_shape"),
                A("episode", "state_motor_configuration_shape"),
            ),
            Gt(P0("episode", "state_seq"), P0("candidate", "state_seq")),
        ),
        "effects": [
            ["set_attr", "candidate", "state_seq", T(P0("episode", "state_seq"))],
            ["set_attr", "candidate", "joint_configuration", T(
                A("episode", "state_joint_configuration")
            )],
            ["set_attr", "candidate", "observation_count", T(
                Plus(P0("candidate", "observation_count"), L(1.0))
            )],
        ],
    }


def reject_stale_candidate_motor_fixation_rule():
    return {
        "name": "ha_reject_stale_candidate_motor_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A different later configuration breaks settlement and "
        "removes the candidate's promotion authority.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_candidate_humanoid_motor_fixation", "candidate"],
        ],
        "where": And(
            Gt(P0("episode", "state_seq"), P0("candidate", "state_seq")),
            Or(
                Not(situated_motor_fixation_is_stable()),
                Not(Eq(
                    A("candidate", "configuration_shape"),
                    A("episode", "state_motor_configuration_shape"),
                )),
            ),
        ),
        "effects": [
            ["del_edge", "episode", "has_candidate_humanoid_motor_fixation", "candidate"],
            ["set_attr", "candidate", "status", "unsettled"],
        ],
    }


def transition_situated_motor_fixation_rule():
    return {
        "name": "ha_transition_situated_motor_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Promote a repeatedly settled candidate while retaining "
        "the transition from the previous local motor frame.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_motor_fixation", "previous"],
            ["episode", "has_candidate_humanoid_motor_fixation", "fixation"],
        ],
        "where": And(
            situated_motor_fixation_is_stable(),
            Eq(
                A("fixation", "configuration_shape"),
                A("episode", "state_motor_configuration_shape"),
            ),
            Gt(
                P0("fixation", "observation_count"),
                Minus(
                    P0("policy", "gait_surprise_confirmation_receipts"),
                    L(1.0),
                ),
            ),
        ),
        "effects": [
            ["del_edge", "episode", "has_current_humanoid_motor_fixation", "previous"],
            ["del_edge", "episode", "has_candidate_humanoid_motor_fixation", "fixation"],
            ["add_edge", "episode", "has_current_humanoid_motor_fixation", "fixation"],
            ["add_edge", "previous", "continues_to_humanoid_motor_fixation", "fixation"],
            ["set_attr", "fixation", "status", "confirmed"],
            ["set_attr", "previous", "status", "retained"],
            ["set_attr", "episode", "motor_configuration_transition_count", T(
                Plus(P0("episode", "motor_configuration_transition_count"), L(1.0))
            )],
        ],
    }


def issue_motor_efference_copy_rule():
    return {
        "name": "ha_issue_situated_motor_efference_copy",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Bind each issued motor trial to the stable configuration "
        "from which it was generated, as the motor analogue of a saccade copy.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_motor_fixation", "fixation"],
            ["episode", "has_humanoid_motor_trial", "trial"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Eq(
                Count(Neighbours("trial", "has_humanoid_motor_efference_copy")),
                L(0.0),
            ),
        ),
        "effects": [
            ["add_node", "copy", "HumanoidMotorEfferenceCopy", {
                "request_seq": T(P0("trial", "request_seq")),
                "reference_joint_configuration": T(
                    A("fixation", "joint_configuration")
                ),
                "primary_token": T(A("trial", "token")),
                "secondary_token": T(A("trial", "secondary_token")),
                "response_frames": T(P0("trial", "response_frames")),
                "status": "issued",
            }],
            ["add_edge", "trial", "has_humanoid_motor_efference_copy", "copy"],
            ["add_edge", "copy", "issued_from_humanoid_motor_fixation", "fixation"],
            ["set_attr", "episode", "motor_efference_copy_count", T(
                Plus(P0("episode", "motor_efference_copy_count"), L(1.0))
            )],
        ],
    }


def bind_situated_motor_reference_rule():
    advances_verified_program = Exists(
        Neighbours("episode", "has_humanoid_motor_preparation"),
        "reference_preparation",
        And(
            Or(
                Eq(
                    A("reference_preparation", "preparation_kind"),
                    L("memory"),
                ),
                Eq(
                    A("reference_preparation", "preparation_kind"),
                    L("sequence"),
                ),
            ),
            Eq(A("reference_preparation", "status"), L("output_potent")),
            Eq(
                P0("reference_preparation", "request_seq"),
                P0("episode", "request_seq"),
            ),
        ),
    )
    uses_current_configuration = Or(
        Eq(A("episode", "decision_kind"), L("tonic_control")),
        Eq(A("episode", "decision_kind"), L("learned_walk")),
        Eq(A("episode", "decision_kind"), L("somatomotor_wave")),
        advances_verified_program,
    )
    return {
        "name": "ha_bind_situated_motor_reference",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Resolve an issued command around the graph's current "
        "stable fixation. The reference is local, replaceable, and explicit.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_current_humanoid_motor_fixation", "fixation"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(1.0)),
            Eq(
                P0("episode", "decision_seq"),
                P0("episode", "request_seq"),
            ),
            Lt(
                P0("episode", "motor_reference_request_seq"),
                P0("episode", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "selected_motor_reference_positions", T(
                If(
                    uses_current_configuration,
                    L(None),
                    A("fixation", "joint_configuration"),
                )
            )],
            ["set_attr", "episode", "selected_motor_reference_shape", T(
                A("fixation", "configuration_shape")
            )],
            ["set_attr", "episode", "selected_motor_reference_kind", T(If(
                uses_current_configuration,
                L("current_sensed_configuration"),
                L("graph_situated_fixation"),
            ))],
            ["set_attr", "episode", "motor_reference_request_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def confirm_motor_efference_copy_rule():
    return {
        "name": "ha_confirm_situated_motor_efference_copy",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A later mechanical receipt confirms the issued copy and "
        "records both its expected displacement and reference residual.",
        "match": [
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_motor_efference_copy", "copy"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("copy", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "copy", "status", "confirmed"],
            ["set_attr", "copy", "post_joint_configuration", T(
                A("outcome", "post_joint_configuration")
            )],
            ["set_attr", "copy", "command_displacement_energy", T(
                P0("outcome", "motor_command_displacement_energy")
            )],
            ["set_attr", "copy", "reference_error_energy", T(
                P0("outcome", "motor_reference_error_energy")
            )],
            ["set_attr", "episode", "motor_efference_confirmation_count", T(
                Plus(
                    P0("episode", "motor_efference_confirmation_count"),
                    L(1.0),
                )
            )],
        ],
    }


def matching_motor_transitions(previous="previous", current="memory"):
    return Filter(
        outgoing_motor_transitions(previous),
        "matching_transition",
        And(
            Eq(
                P0("matching_transition", "next_program_ordinal"),
                P0(current, "ordinal"),
            ),
            Eq(
                A("matching_transition", "motor_task_context"),
                A(current, "motor_task_context"),
            ),
        ),
    )


def request_motor_sequence_consolidation_rule():
    """Recruit the offline sheet for a genuinely novel compound transition.

    Consecutive verified programs are available to the hard motor sheet, but
    minting a durable temporal edge is consolidation work.  Make that
    asynchronous boundary explicit in the graph instead of relying on some
    unrelated lifetime/library request to happen to open the integration
    sheet later.
    """
    existing = matching_motor_transitions()
    return {
        "name": "ha_request_motor_sequence_consolidation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A novel receipt-confirmed compound successor recruits "
        "the existing embodied integration sheet. The fast sheet identifies "
        "the consolidation opportunity; the background sheet alone authors "
        "the durable transition.",
        "match": [
            [
                "agent",
                "has_embodied_integration_task_set",
                "integration_tasks",
            ],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "motor_sequence_consolidation_requested"), L(0.0)),
            Eq(
                A("previous", "motor_task_context"),
                A("memory", "motor_task_context"),
            ),
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Gt(P0("memory", "member_count"), L(0.0)),
            Lt(
                P0("episode", "last_motor_sequence_receipt_seq"),
                P0("trial", "request_seq"),
            ),
            Eq(Count(existing), L(0.0)),
        ),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "novel_verified_humanoid_motor_sequence",
                "epoch": T(P0("trial", "request_seq")),
                "provenance_kind": "graph_authored_motor_consolidation",
            }],
            [
                "add_edge",
                "outcome",
                "has_system_two_escalation",
                "escalation",
            ],
            ["add_edge", "escalation", "about_context", "outcome"],
            [
                "add_edge",
                "escalation",
                "recruits_task_set",
                "integration_tasks",
            ],
            [
                "set_attr",
                "outcome",
                "motor_sequence_consolidation_requested",
                1.0,
            ],
        ],
    }


def update_motor_sequence_transition_rule():
    observed = observed_motor_consequence()
    count = Plus(P0("transition", "experience_count"), L(1.0))
    prediction_error = motor_consequence_error_energy(
        observed,
        "transition",
    )
    lateral_prediction_error = motor_lateral_consequence_error_energy(
        observed,
        "transition",
    )

    def mean(key):
        return Plus(
            P0("transition", f"mean_{key}"),
            Div(
                Minus(
                    observed[key],
                    P0("transition", f"mean_{key}"),
                ),
                count,
            ),
        )

    def mean_rate(key):
        observed_rate = Div(
            observed[key],
            P0("trial", "response_frames"),
        )
        return Plus(
            P0("transition", f"mean_rate_{key}"),
            Div(
                Minus(
                    observed_rate,
                    P0("transition", f"mean_rate_{key}"),
                ),
                count,
            ),
        )

    mean_prediction_error = Plus(
        P0("transition", "mean_prediction_error_energy"),
        Div(
            Minus(
                prediction_error,
                P0("transition", "mean_prediction_error_energy"),
            ),
            count,
        ),
    )
    mean_lateral_prediction_error = Plus(
        P0("transition", "mean_lateral_prediction_error_energy"),
        Div(
            Minus(
                lateral_prediction_error,
                P0(
                    "transition",
                    "mean_lateral_prediction_error_energy",
                ),
            ),
            count,
        ),
    )
    next_response_frames = If(
        Gt(
            prediction_error,
            P0("transition", "mean_prediction_error_energy"),
        ),
        Max(
            L(1.0),
            Minus(P0("transition", "response_frames"), L(1.0)),
        ),
        Min(
            P0("memory", "response_frames"),
            Plus(P0("transition", "response_frames"), L(1.0)),
        ),
    )

    return {
        "name": "ha_update_grounded_motor_sequence_transition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A safe verified compound receipt advances the temporal "
        "context and updates the exact predecessor-conditioned consequence. "
        "This learns a trajectory transition rather than smearing the "
        "receipt over either endpoint.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "previous",
                "has_humanoid_motor_transition",
                "transition",
            ],
            [
                "transition",
                "continues_with_humanoid_motor_program",
                "memory",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(
                A("previous", "motor_task_context"),
                A("memory", "motor_task_context"),
            ),
            Eq(
                A("transition", "motor_task_context"),
                A("memory", "motor_task_context"),
            ),
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Gt(P0("memory", "member_count"), L(0.0)),
            Lt(
                P0("episode", "last_motor_sequence_receipt_seq"),
                P0("trial", "request_seq"),
            ),
            Lt(
                P0("transition", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "transition",
                f"mean_{key}",
                T(mean(key)),
            ]
            for key in observed
        ] + [
            [
                "set_attr",
                "transition",
                f"mean_rate_{key}",
                T(mean_rate(key)),
            ]
            for key in observed
        ] + [
            ["set_attr", "transition", "experience_count", T(count)],
            [
                "set_attr",
                "transition",
                "mean_prediction_error_energy",
                T(mean_prediction_error),
            ],
            [
                "set_attr",
                "transition",
                "mean_lateral_prediction_error_energy",
                T(mean_lateral_prediction_error),
            ],
            [
                "set_attr",
                "transition",
                "response_frames",
                T(next_response_frames),
            ],
            ["set_attr", "transition", "memory_eligible", 1.0],
            ["set_attr", "transition", "prediction_error_measured", 1.0],
            [
                "set_attr",
                "transition",
                "last_update_request_seq",
                T(P0("trial", "request_seq")),
            ],
            [
                "del_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "add_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "memory",
            ],
            [
                "set_attr",
                "episode",
                "last_motor_sequence_receipt_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def learn_motor_sequence_transition_rule():
    observed = observed_motor_consequence()
    existing = matching_motor_transitions()
    # The transition's initial forward model is this exact receipt, so its fit
    # residual is the additive identity. It remains output-null until another
    # occurrence supplies an out-of-sample prediction error.
    initial_prediction_error = L(0.0)
    initial_lateral_prediction_error = L(0.0)
    context_novelty = motor_consequence_error_energy(observed, "memory")
    context_lateral_novelty = motor_lateral_consequence_error_energy(
        observed,
        "memory",
    )
    return {
        "name": "ha_consolidate_motor_sequence_transition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Consolidate a new edge between consecutive safe compound "
        "population states. Its initial forward model is the observed "
        "successor receipt; a later independent occurrence must measure its "
        "prediction error before graph-native reassociation can release it.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(
                A("previous", "motor_task_context"),
                A("memory", "motor_task_context"),
            ),
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Gt(P0("memory", "member_count"), L(0.0)),
            Lt(
                P0("episode", "last_motor_sequence_receipt_seq"),
                P0("trial", "request_seq"),
            ),
            Eq(Count(existing), L(0.0)),
        ),
        "effects": [
            ["add_node", "transition", "HumanoidMotorTransition", {
                "ordinal": T(Plus(
                    P0("episode", "motor_sequence_transition_count"),
                    L(1.0),
                )),
                "status": "grounded",
                "memory_eligible": 1.0,
                "motor_task_context": T(
                    A("memory", "motor_task_context")
                ),
                "from_task_phase": T(
                    A("previous", "motor_task_phase")
                ),
                "next_task_phase": T(A("memory", "motor_task_phase")),
                "task_request_seq": T(P0(
                    "episode", "curriculum_pending_recovery_request_seq"
                )),
                "trajectory_verified": 0.0,
                "support_phase": T(P0("memory", "support_phase")),
                "response_frames": T(P0("trial", "response_frames")),
                "from_program_ordinal": T(P0("previous", "ordinal")),
                "next_program_ordinal": T(P0("memory", "ordinal")),
                "experience_count": 1.0,
                "prediction_error_measured": 0.0,
                "context_novelty_energy": T(context_novelty),
                "context_lateral_novelty_energy": T(
                    context_lateral_novelty
                ),
                "mean_prediction_error_energy": T(
                    initial_prediction_error
                ),
                "mean_lateral_prediction_error_energy": T(
                    initial_lateral_prediction_error
                ),
                "recall_count": 0.0,
                "last_recall_request_seq": 0.0,
                "last_update_request_seq": T(
                    P0("trial", "request_seq")
                ),
                **{
                    f"mean_{key}": T(value)
                    for key, value in observed.items()
                },
                **{
                    f"mean_rate_{key}": T(Div(
                        value,
                        P0("trial", "response_frames"),
                    ))
                    for key, value in observed.items()
                },
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_motor_transition",
                "transition",
            ],
            [
                "add_edge",
                "previous",
                "has_humanoid_motor_transition",
                "transition",
            ],
            [
                "add_edge",
                "transition",
                "continues_with_humanoid_motor_program",
                "memory",
            ],
            [
                "del_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "add_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "memory",
            ],
            [
                "set_attr",
                "episode",
                "motor_sequence_transition_count",
                T(Plus(
                    P0("episode", "motor_sequence_transition_count"),
                    L(1.0),
                )),
            ],
            [
                "set_attr",
                "episode",
                "last_motor_sequence_receipt_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def break_motor_sequence_on_task_context_change_rule():
    return {
        "name": "ha_break_motor_sequence_on_task_context_change",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A deliberate jump and ordinary locomotion are distinct "
        "temporal schemas. Clear the predecessor when the active drive changes "
        "so a walking chunk cannot become the first phase of a jump.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
        ],
        "where": Not(Eq(
            A("previous", "motor_task_context"),
            motor_task_context(),
        )),
        "effects": [[
            "del_edge",
            "episode",
            "last_verified_humanoid_motor_program",
            "previous",
        ]],
    }


def prime_motor_sequence_context_rule():
    current_context = Neighbours(
        "episode",
        "last_verified_humanoid_motor_program",
    )
    return {
        "name": "ha_prime_motor_sequence_from_verified_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "The first safe compound receipt establishes an "
        "output-potent temporal context. Later compound receipts can then "
        "consolidate graph edges from this state.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(A("memory", "status"), L("grounded")),
            Eq(P0("memory", "memory_eligible"), L(1.0)),
            Gt(P0("memory", "member_count"), L(0.0)),
            Lt(
                P0("episode", "last_motor_sequence_receipt_seq"),
                P0("trial", "request_seq"),
            ),
            Eq(Count(current_context), L(0.0)),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "memory",
            ],
            [
                "set_attr",
                "episode",
                "last_motor_sequence_receipt_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def invalidate_motor_sequence_transition_rule():
    return {
        "name": "ha_invalidate_unsafe_motor_sequence_transition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "An unsafe compound receipt makes the exact temporal edge "
        "output-null and breaks its active trajectory context.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "previous",
                "has_humanoid_motor_transition",
                "transition",
            ],
            [
                "transition",
                "continues_with_humanoid_motor_program",
                "memory",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Gt(P0("memory", "member_count"), L(1.0)),
            Eq(P0("memory", "memory_eligible"), L(0.0)),
            Lt(
                P0("episode", "last_motor_sequence_receipt_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "transition", "memory_eligible", 0.0],
            [
                "del_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "set_attr",
                "episode",
                "last_motor_sequence_receipt_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def break_motor_sequence_context_rule():
    matching = matching_motor_transitions()
    return {
        "name": "ha_break_unsafe_motor_sequence_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Break a high-level compound trajectory after an unsafe "
        "receipt even when that exact transition has never been seen before.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Gt(P0("memory", "member_count"), L(1.0)),
            Eq(P0("memory", "memory_eligible"), L(0.0)),
            Lt(
                P0("episode", "last_motor_sequence_receipt_seq"),
                P0("trial", "request_seq"),
            ),
            Eq(Count(matching), L(0.0)),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
            [
                "set_attr",
                "episode",
                "last_motor_sequence_receipt_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def break_motor_sequence_on_recovery_rule():
    return {
        "name": "ha_break_motor_sequence_on_recovery",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Recovery changes the control regime, so the previously "
        "active locomotor trajectory is no longer valid temporal context.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "last_verified_humanoid_motor_program",
                "previous",
            ],
        ],
        "where": Or(
            Eq(A("episode", "phase"), L("recovery")),
            Eq(P0("episode", "recovery_mode"), L(1.0)),
        ),
        "effects": [[
            "del_edge",
            "episode",
            "last_verified_humanoid_motor_program",
            "previous",
        ]],
    }


def learn_identifiable_pair_program_rule():
    observed = {
        "dzx": Minus(
            body_z_x("outcome", "post"),
            body_z_x("outcome", "pre"),
        ),
        "dzy": Minus(
            body_z_y("outcome", "post"),
            body_z_y("outcome", "pre"),
        ),
        "dwx": Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx")),
        "dwy": Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy")),
        "dvx": Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx")),
        "dvy": Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy")),
        "dvz": Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz")),
    }
    horizon_scale = Div(
        P0("trial", "response_frames"),
        P0("trial", "model_response_frames"),
    )
    count = Plus(P0("synergy", "experience_count"), L(1.0))
    support_preserved = Or(
        Not(Or(
            Gt(P0("outcome", "pre_support_0_force"), L(0.0)),
            Gt(P0("outcome", "pre_support_1_force"), L(0.0)),
        )),
        Gt(P0("outcome", "post_support_0_force"), L(0.0)),
        Gt(P0("outcome", "post_support_1_force"), L(0.0)),
    )

    def residual(key):
        measured = Minus(
            observed[key],
            Times(
                horizon_scale,
                Plus(
                    P0("first", f"mean_{key}"),
                    P0("second", f"mean_{key}"),
                ),
            ),
        )
        return Plus(
            P0("synergy", f"residual_{key}"),
            Div(
                Minus(
                    measured,
                    P0("synergy", f"residual_{key}"),
                ),
                count,
            ),
        )

    return {
        "name": "ha_learn_identifiable_pair_program_residual",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A two-member receipt has one identifiable interaction "
        "term, so refine that exact reusable pair residual online. Wider "
        "program residuals remain whole-program facts until an intervention "
        "can disambiguate their higher-order causes.  The first-member token "
        "index keeps unrelated retained synergies outside this receipt-local "
        "learning pass.",
        "index_hints": [{
            "for_var": "synergy",
            "via_var": "first",
            "via_key": "token",
            "node_type": "HumanoidSynergyModel",
            "this_key": "token_a",
        }],
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "plan"],
            ["trial", "has_humanoid_transition", "outcome"],
            [
                "plan",
                "includes_humanoid_phase_action_model",
                "first",
            ],
            [
                "plan",
                "includes_humanoid_phase_action_model",
                "second",
            ],
            ["episode", "has_humanoid_synergy_model", "synergy"],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("learned_walk")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("plan", "member_count"), L(2.0)),
            Lt(P0("first", "ordinal"), P0("second", "ordinal")),
            Eq(A("synergy", "token_a"), A("first", "token")),
            Eq(A("synergy", "token_b"), A("second", "token")),
            Lt(
                P0("synergy", "last_program_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "synergy",
                f"residual_{key}",
                T(residual(key)),
            ]
            for key in observed
        ] + [
            ["set_attr", "synergy", "support_loss_ema", T(
                Plus(
                    P0("synergy", "support_loss_ema"),
                    Div(
                        Minus(
                            If(support_preserved, L(0.0), L(1.0)),
                            P0("synergy", "support_loss_ema"),
                        ),
                        count,
                    ),
                )
            )],
            ["set_attr", "synergy", "support_deficit_ema", T(
                Plus(
                    P0("synergy", "support_deficit_ema"),
                    Div(
                        Minus(
                            support_deficit_observation(),
                            P0("synergy", "support_deficit_ema"),
                        ),
                        count,
                    ),
                )
            )],
            ["set_attr", "synergy", "mean_input_energy_joules", T(
                Plus(
                    P0("synergy", "mean_input_energy_joules"),
                    Div(
                        Minus(
                            P0("outcome", "input_energy_joules"),
                            P0(
                                "synergy",
                                "mean_input_energy_joules",
                            ),
                        ),
                        count,
                    ),
                )
            )],
            ["set_attr", "synergy", "experience_count", T(count)],
            [
                "set_attr",
                "synergy",
                "last_program_update_request_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def close_phase_adaptation_rule():
    return {
        "name": "ha_close_phase_adaptation_after_alphabet_quiet",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Close online specialization after no new contextual "
        "receipt for more decisions than the support-conditioned actuator "
        "alphabet.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "evaluation_active"), L(0.0)),
            Eq(P0("episode", "online_phase_learning"), L(1.0)),
            Eq(P0("episode", "phase_adaptation_complete"), L(0.0)),
            Gt(P0("episode", "last_phase_learning_request_seq"), L(0.0)),
            Gt(
                Minus(
                    P0("episode", "request_seq"),
                    P0("episode", "last_phase_learning_request_seq"),
                ),
                Count(PHASE_MODELS),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "learned_gait_tilt_envelope",
                T(P0("episode", "walking_peak_tilt")),
            ],
            [
                "set_attr",
                "episode",
                "learned_gait_vx_envelope",
                T(P0("episode", "walking_peak_abs_vx")),
            ],
            [
                "set_attr",
                "episode",
                "learned_gait_vy_envelope",
                T(P0("episode", "walking_peak_abs_vy")),
            ],
            [
                "set_attr",
                "episode",
                "learned_gait_prediction_error_envelope",
                T(P0("episode", "walking_peak_prediction_error")),
            ],
            [
                "set_attr",
                "episode",
                "learned_gait_mean_tilt",
                T(P0("episode", "walking_mean_tilt")),
            ],
            ["set_attr", "episode", "phase_adaptation_complete", 1.0],
        ],
    }


def learn_get_up_consequence_rule():
    height_gain = Div(
        Minus(P0("outcome", "post_z"), P0("outcome", "pre_z")),
        P0("episode", "standing_reference_z"),
    )
    alignment_gain = Minus(
        body_z_z("outcome", "post"),
        body_z_z("outcome", "pre"),
    )
    count = Plus(P0("get_up_model", "experience_count"), L(1.0))
    mean_height_gain = Plus(
        P0("get_up_model", "mean_height_gain"),
        Div(
            Minus(
                height_gain,
                P0("get_up_model", "mean_height_gain"),
            ),
            count,
        ),
    )
    mean_alignment_gain = Plus(
        P0("get_up_model", "mean_alignment_gain"),
        Div(
            Minus(
                alignment_gain,
                P0("get_up_model", "mean_alignment_gain"),
            ),
            count,
        ),
    )
    translation_gain = recovery_translation_gain()
    whole_body_support_gain = recovery_whole_body_support_gain()
    mean_translation_gain = Plus(
        PI0("get_up_model", "mean_translation_gain"),
        Div(
            Minus(
                translation_gain,
                PI0("get_up_model", "mean_translation_gain"),
            ),
            count,
        ),
    )
    mean_whole_body_support_gain = Plus(
        PI0("get_up_model", "mean_whole_body_support_gain"),
        Div(
            Minus(
                whole_body_support_gain,
                PI0("get_up_model", "mean_whole_body_support_gain"),
            ),
            count,
        ),
    )
    improved = recovery_outcome_has_progress()
    return {
        "name": "ha_learn_whole_body_get_up_consequence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Credit each fallen-body recovery receipt to the exact "
        "opaque actuator that caused it. Height and body-axis alignment are "
        "raw consequences; no arm, leg, or posture semantics are supplied.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_get_up_action_model",
                "get_up_model",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Or(
                Eq(A("trial", "decision_kind"), L("get_up_explore")),
                Eq(A("trial", "decision_kind"), L("get_up_exploit")),
                Eq(A("trial", "decision_kind"), L("get_up_program")),
            ),
            Eq(
                A("get_up_model", "token"),
                A("trial", "token"),
            ),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Lt(
                P0("get_up_model", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "get_up_model",
                "mean_height_gain",
                T(mean_height_gain),
            ],
            [
                "set_attr",
                "get_up_model",
                "mean_alignment_gain",
                T(mean_alignment_gain),
            ],
            [
                "set_attr",
                "get_up_model",
                "mean_translation_gain",
                T(mean_translation_gain),
            ],
            [
                "set_attr",
                "get_up_model",
                "mean_whole_body_support_gain",
                T(mean_whole_body_support_gain),
            ],
            [
                "set_attr",
                "get_up_model",
                "reversal_success_count",
                T(Plus(
                    PI0("get_up_model", "reversal_success_count"),
                    PI0("outcome", "development_reversal"),
                )),
            ],
            [
                "set_attr",
                "get_up_model",
                "support_topology_change_count",
                T(Plus(
                    PI0("get_up_model", "support_topology_change_count"),
                    PI0("outcome", "development_support_topology_changed"),
                )),
            ],
            [
                "set_attr",
                "get_up_model",
                "stable_partial_motion_count",
                T(Plus(
                    PI0("get_up_model", "stable_partial_motion_count"),
                    If(
                        And(
                            Eq(
                                PI0("outcome", "development_configuration_changed"),
                                L(1),
                            ),
                            Eq(
                                PI0("outcome", "development_motion_nonamplifying"),
                                L(1),
                            ),
                        ),
                        L(1),
                        L(0),
                    ),
                )),
            ],
            [
                "set_attr",
                "get_up_model",
                "experience_count",
                T(count),
            ],
            [
                "set_attr",
                "get_up_model",
                "last_update_request_seq",
                T(P0("trial", "request_seq")),
            ],
            [
                "set_attr",
                "episode",
                "get_up_last_improvement_attempt",
                T(If(
                    improved,
                    P0("episode", "get_up_attempt_count"),
                    P0("episode", "get_up_last_improvement_attempt"),
                )),
            ],
            ["set_attr", "episode", "get_up_success_count", T(
                Plus(
                    P0("episode", "get_up_success_count"),
                    If(
                        Eq(P0("episode", "upright"), L(1.0)),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "outcome", "get_up_height_gain", T(height_gain)],
            [
                "set_attr", "outcome", "get_up_translation_gain",
                T(translation_gain),
            ],
            [
                "set_attr",
                "outcome",
                "get_up_alignment_gain",
                T(alignment_gain),
            ],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "learned_get_up"],
        ],
    }


def close_control_trial_rule():
    return {
        "name": "ha_close_nonlearning_control_trial",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Or(
                Eq(A("episode", "phase"), L("recovery")),
                Eq(A("episode", "phase"), L("locomotion")),
            ),
            Eq(A("trial", "status"), L("issued")),
            Not(Eq(A("trial", "decision_kind"), L("learned_walk"))),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "observed_control"],
        ],
    }


def learn_residual_regime_rule():
    count = Plus(P0("regime", "sample_count"), L(1.0))

    def mean(key, observation):
        return Plus(
            P0("regime", key),
            Div(Minus(observation, P0("regime", key)), count),
        )

    directed_step = Times(
        P0("episode", "heading_x"),
        Minus(P0("outcome", "post_x"), P0("outcome", "pre_x")),
    )
    lateral_step = Abs(Minus(
        P0("outcome", "post_y"),
        P0("outcome", "pre_y"),
    ))
    post_z_x = body_z_x("outcome", "post")
    post_z_y = body_z_y("outcome", "post")
    tilt = Sqrt(Plus(
        Times(post_z_x, post_z_x),
        Times(post_z_y, post_z_y),
    ))
    minimum_height = Times(
        P0("policy", "minimum_upright_height_fraction"),
        P0("episode", "standing_reference_z"),
    )
    height_deficit = Div(
        Max(
            L(0.0),
            Minus(minimum_height, P0("outcome", "post_z")),
        ),
        P0("episode", "standing_reference_z"),
    )
    support_deficit = support_deficit_observation()
    unsafe_observation = Or(
        receipt_material_viability_breach(),
        And(
            Not(situated_locomotion_context_active()),
            Gt(height_deficit, L(0.0)),
        ),
    )
    post_support_0 = Gt(
        P0("outcome", "post_support_0_force"),
        L(0.0),
    )
    post_support_1 = Gt(
        P0("outcome", "post_support_1_force"),
        L(0.0),
    )
    aerial_occupancy = If(
        And(Not(post_support_0), Not(post_support_1)),
        L(1.0),
        L(0.0),
    )
    double_support_occupancy = If(
        And(post_support_0, post_support_1),
        L(1.0),
        L(0.0),
    )
    normalized_energy = Div(
        P0("outcome", "input_energy_joules"),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
            P0("episode", "standing_reference_z"),
        ),
    )
    observations = (
        ("mean_directed_step", directed_step),
        ("mean_abs_lateral_step", lateral_step),
        ("mean_tilt", tilt),
        ("mean_height_deficit", height_deficit),
        ("mean_support_deficit", support_deficit),
        ("mean_normalized_energy", normalized_energy),
        ("mean_aerial_occupancy", aerial_occupancy),
        ("mean_double_support_occupancy", double_support_occupancy),
    )
    prediction_residual = Plus(*[
        Abs(Minus(observation, P0("regime", key)))
        for key, observation in observations
    ])
    fast_prediction_residual = Plus(
        P0("regime", "fast_prediction_residual"),
        Div(
            Minus(
                prediction_residual,
                P0("regime", "fast_prediction_residual"),
            ),
            P0("episode", "support_sensor_count"),
        ),
    )
    slow_prediction_residual = Plus(
        P0("regime", "slow_prediction_residual"),
        Div(
            Minus(
                prediction_residual,
                P0("regime", "slow_prediction_residual"),
            ),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    learning_progress = Max(
        L(0.0),
        Minus(slow_prediction_residual, fast_prediction_residual),
    )
    unresolved_asymmetry = Max(
        L(0.0),
        Minus(P0("policy", "support_phase_prior_strength"), count),
    )
    return {
        "name": "ha_learn_persistent_residual_regime",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Attribute exact progress, path, balance, support and energy "
        "receipts to the active graph-held residual/viability regime. A "
        "body-derived receipt window closes without Python scoring or tuning.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["policy", "has_humanoid_residual_regime", "regime"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "evaluation_active"), L(1.0)),
            Eq(
                P0("policy", "persistent_task_residual_authority"),
                L(1.0),
            ),
            Eq(
                P0("regime", "ordinal"),
                P0("trial", "residual_regime_ordinal"),
            ),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "residual_regime_learned"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "regime", "mean_directed_step", T(
                mean("mean_directed_step", directed_step)
            )],
            ["set_attr", "regime", "mean_abs_lateral_step", T(
                mean("mean_abs_lateral_step", lateral_step)
            )],
            ["set_attr", "regime", "mean_tilt", T(
                mean("mean_tilt", tilt)
            )],
            ["set_attr", "regime", "mean_height_deficit", T(
                mean("mean_height_deficit", height_deficit)
            )],
            ["set_attr", "regime", "mean_support_deficit", T(
                mean("mean_support_deficit", support_deficit)
            )],
            ["set_attr", "regime", "mean_normalized_energy", T(
                mean("mean_normalized_energy", normalized_energy)
            )],
            ["set_attr", "regime", "mean_aerial_occupancy", T(
                mean("mean_aerial_occupancy", aerial_occupancy)
            )],
            [
                "set_attr",
                "regime",
                "mean_double_support_occupancy",
                T(mean(
                    "mean_double_support_occupancy",
                    double_support_occupancy,
                )),
            ],
            [
                "set_attr",
                "regime",
                "fast_prediction_residual",
                T(fast_prediction_residual),
            ],
            [
                "set_attr",
                "regime",
                "slow_prediction_residual",
                T(slow_prediction_residual),
            ],
            [
                "set_attr",
                "regime",
                "learning_progress",
                T(learning_progress),
            ],
            ["set_attr", "regime", "q", T(fast_prediction_residual)],
            [
                "set_attr",
                "regime",
                "asym_count",
                T(unresolved_asymmetry),
            ],
            ["set_attr", "regime", "novelty", T(learning_progress)],
            ["set_attr", "regime", "sample_count", T(count)],
            ["set_attr", "regime", "unsafe_receipt_count", T(
                Plus(
                    P0("regime", "unsafe_receipt_count"),
                    If(unsafe_observation, L(1.0), L(0.0)),
                )
            )],
            ["set_attr", "outcome", "residual_regime_learned", 1.0],
        ],
    }


def residual_regime_selection_effects():
    return [
        ["set_attr", "active_regime", "completed_windows", T(
            Plus(P0("active_regime", "completed_windows"), L(1.0))
        )],
        ["set_attr", "episode", "active_gait_attractor_ordinal", T(
            P0("regime", "gait_ordinal")
        )],
        ["set_attr", "episode", "active_residual_regime_ordinal", T(
            P0("regime", "ordinal")
        )],
        ["set_attr", "episode", "residual_regime_window_sample_count", 0.0],
        ["set_attr", "episode", "residual_regime_window_complete", 0.0],
        ["set_attr", "episode", "residual_regime_selection_count", T(
            Plus(
                P0("episode", "residual_regime_selection_count"),
                L(1.0),
            )
        )],
        ["set_attr", "regime", "selection_count", T(
            Plus(P0("regime", "selection_count"), L(1.0))
        )],
    ]


def explore_residual_regime_rule():
    curious = curiosity_candidates()
    selected = Argmin(
        curious,
        "c",
        Neg(core_curiosity_score()),
        V("policy"),
    )
    active_window_complete = Not(Lt(
        P0("active_regime", "sample_count"),
        Times(
            Plus(
                P0("active_regime", "completed_windows"),
                L(1.0),
            ),
            P0("policy", "support_phase_prior_strength"),
        ),
    ))
    return {
        "name": "ha_curiosity_selects_coordination_experiment",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "After a receipt window, evaluate decision_core's own "
        "graph-held curiosity score over coordination hypotheses. "
        "Prediction residual is cost, unresolved structure is asymmetry, and "
        "compressible learning progress is novelty.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["policy", "has_humanoid_residual_regime", "active_regime"],
            ["policy", "has_humanoid_residual_regime", "regime"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "regime_applied_ordinal"), L(0.0)),
            Eq(
                P0("policy", "persistent_task_residual_authority"),
                L(1.0),
            ),
            Eq(
                P0("active_regime", "ordinal"),
                P0("episode", "active_residual_regime_ordinal"),
            ),
            active_window_complete,
            Gt(Count(curious), L(0.0)),
            Eq(P0("regime", "ordinal"), AO(selected, "ordinal")),
        ),
        "effects": residual_regime_selection_effects(),
    }


def exploit_residual_regime_rule():
    curious = curiosity_candidates()
    pareto = Filter(
        residual_regimes(),
        "candidate",
        And(
            Not(Lt(
                P0("candidate", "sample_count"),
                P0("policy", "support_phase_prior_strength"),
            )),
            residual_regime_realized_gait(V("candidate")),
            Not(residual_regime_dominated(V("candidate"))),
        ),
    )
    selected = Argmin(
        pareto,
        "candidate",
        residual_regime_context_choice_key(V("candidate")),
        V("policy"),
    )
    active_window_complete = Not(Lt(
        P0("active_regime", "sample_count"),
        Times(
            Plus(
                P0("active_regime", "completed_windows"),
                L(1.0),
            ),
            P0("policy", "support_phase_prior_strength"),
        ),
    ))
    return {
        "name": "ha_select_pareto_persistent_residual_regime",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "After the graph completes its sweep, reject dominated "
        "regimes across progress, path, balance, support and energy. Current "
        "graph-held need focuses one frontier dimension without scalarizing "
        "or weighting unlike objectives.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["policy", "has_humanoid_residual_regime", "active_regime"],
            ["policy", "has_humanoid_residual_regime", "regime"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "regime_applied_ordinal"), L(0.0)),
            Eq(
                P0("policy", "persistent_task_residual_authority"),
                L(1.0),
            ),
            Eq(
                P0("active_regime", "ordinal"),
                P0("episode", "active_residual_regime_ordinal"),
            ),
            active_window_complete,
            Eq(Count(curious), L(0.0)),
            Gt(Count(pareto), L(0.0)),
            Eq(P0("regime", "ordinal"), AO(selected, "ordinal")),
        ),
        "effects": residual_regime_selection_effects(),
    }


def open_situated_locomotion_context_rule():
    return {
        "name": "ha_open_intentional_situated_locomotion_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "When safe developmental intent deliberately opens a "
        "non-canonical future path, mint explicit graph ownership of the "
        "trajectory. It is not a pose "
        "target: the owned trajectory may remain dynamically unbalanced while "
        "structural power and thermal limits retain hard-reflex authority.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            intentional_situated_locomotion_requested(),
            Eq(Count(SITUATED_LOCOMOTION_CONTEXTS), L(0)),
        ),
        "effects": [
            ["add_node", "context", "HumanoidSituatedLocomotionContext", {
                "status": "active",
                "developmental_goal": T(A("episode", "developmental_goal")),
                "trajectory_ownership": 1,
                "pose_target_authority": 0,
                "material_limit_authority": 1,
                "opened_state_seq": T(PI0("episode", "state_seq")),
            }],
            [
                "add_edge",
                "episode",
                "has_current_humanoid_situated_locomotion_context",
                "context",
            ],
            ["set_attr", "episode", "situated_locomotion_context_active", 1],
        ],
    }


def close_situated_locomotion_context_rule():
    return {
        "name": "ha_close_intentional_situated_locomotion_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Withdraw the temporary attractor when deliberate "
        "locomotion closes or changes developmental goal. Canonical posture "
        "then regains authority without deleting the contextual receipt.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_current_humanoid_situated_locomotion_context",
                "context",
            ],
        ],
        "where": Or(
            Not(intentional_situated_locomotion_requested()),
            Not(Eq(
                A("context", "developmental_goal"),
                A("episode", "developmental_goal"),
            )),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_current_humanoid_situated_locomotion_context",
                "context",
            ],
            ["set_attr", "context", "status", "retired"],
            ["set_attr", "episode", "situated_locomotion_context_active", 0],
        ],
    }


def measure_rule():
    z_x = body_z_x("episode", "state")
    z_y = body_z_y("episode", "state")
    tilt = Sqrt(Plus(Times(z_x, z_x), Times(z_y, z_y)))
    first_recovery_measurement = And(
        Eq(A("episode", "phase"), L("recovery")),
        Eq(P0("episode", "recovery_measurements_initialized"), L(0.0)),
    )
    upright = Gt(
        P0("episode", "state_z"),
        Times(
            P0("policy", "minimum_upright_height_fraction"),
            P0("episode", "standing_reference_z"),
        ),
    )
    locomotor_viability_breached = And(
        Eq(A("episode", "phase"), L("locomotion")),
        Eq(PI0("episode", "evaluation_active"), L(1)),
        Not(situated_locomotion_context_active()),
        Not(upright),
    )
    return {
        "name": "ha_measure_raw_humanoid_balance",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Measure vestibular and height state directly. A body "
        "below its graph-held upright envelope recruits recovery from raw "
        "perception unless the situated developmental graph is deliberately "
        "learning locomotion in that configuration. A discovered crawl or "
        "cruise basin is not a fall merely because it is not upright.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": Gt(
            P0("episode", "state_seq"),
            P0("episode", "measured_state_seq"),
        ),
        "effects": [
            ["set_attr", "episode", "body_z_axis_x", T(z_x)],
            ["set_attr", "episode", "body_z_axis_y", T(z_y)],
            ["set_attr", "episode", "tilt_magnitude", T(tilt)],
            ["set_attr", "episode", "upright", T(
                {
                    "type": "IfThenElse",
                    "cond": upright,
                    "then": L(1.0),
                    "other": L(0.0),
                }
            )],
            ["set_attr", "episode", "recovery_mode", T(If(
                locomotor_viability_breached,
                L(1.0),
                P0("episode", "recovery_mode"),
            ))],
            ["set_attr", "episode", "minimum_height_seen", T(
                {
                    "type": "IfThenElse",
                    "cond": first_recovery_measurement,
                    "then": P0("episode", "state_z"),
                    "other": {
                        "type": "Min",
                        "items": [
                            P0("episode", "minimum_height_seen"),
                            P0("episode", "state_z"),
                        ],
                    },
                }
            )],
            ["set_attr", "episode", "peak_tilt_seen", T(
                {
                    "type": "IfThenElse",
                    "cond": first_recovery_measurement,
                    "then": tilt,
                    "other": {
                        "type": "Max",
                        "items": [
                            P0("episode", "peak_tilt_seen"),
                            tilt,
                        ],
                    },
                }
            )],
            ["set_attr", "episode", "recovery_measurements_initialized", T(
                {
                    "type": "IfThenElse",
                    "cond": Eq(A("episode", "phase"), L("recovery")),
                    "then": L(1.0),
                    "other": P0(
                        "episode",
                        "recovery_measurements_initialized",
                    ),
                }
            )],
            ["set_attr", "episode", "measured_state_seq", T(
                P0("episode", "state_seq")
            )],
        ],
    }


def measure_locomotion_rule():
    z_x = body_z_x("episode", "state")
    z_y = body_z_y("episode", "state")
    tilt = Sqrt(Plus(Times(z_x, z_x), Times(z_y, z_y)))
    first = Eq(
        P0("episode", "locomotion_measurements_initialized"),
        L(0.0),
    )
    support_0 = Gt(P0("episode", "state_support_0_force"), L(0.0))
    support_1 = Gt(P0("episode", "state_support_1_force"), L(0.0))
    aerial = And(Not(support_0), Not(support_1))
    double_support = And(support_0, support_1)
    unilateral_support = {
        "type": "IfThenElse",
        "cond": And(support_0, Not(support_1)),
        "then": L(1.0),
        "other": {
            "type": "IfThenElse",
            "cond": And(support_1, Not(support_0)),
            "then": L(2.0),
            "other": L(0.0),
        },
    }
    directed_progress = Times(
        P0("episode", "heading_x"),
        Minus(
            P0("episode", "state_x"),
            P0("episode", "locomotion_start_x"),
        ),
    )
    total_directed_progress = Plus(
        P0("episode", "lifetime_completed_progress"),
        directed_progress,
    )
    locomotion_residual = Max(
        L(0.0),
        Minus(
            P0("episode", "target_directed_progress_m"),
            total_directed_progress,
        ),
    )
    lateral_offset = Minus(
        P0("episode", "state_y"),
        P0("episode", "locomotion_start_y"),
    )
    abs_vx = Abs(P0("episode", "state_vx"))
    abs_vy = Abs(P0("episode", "state_vy"))
    familiarizing = Eq(
        P0("episode", "evaluation_active"),
        L(0.0),
    )
    next_tilt_sample_count = Plus(
        P0("episode", "walking_tilt_sample_count"),
        L(1.0),
    )
    support_switched = And(
        Not(first),
        Gt(unilateral_support, L(0.0)),
        Gt(P0("episode", "last_unilateral_support"), L(0.0)),
        Not(Eq(
            unilateral_support,
            P0("episode", "last_unilateral_support"),
        )),
    )
    return {
        "name": "ha_measure_directed_locomotion_and_support",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Measure directed travel and alternating unilateral "
        "support from raw graph-mirrored state.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "state_is_receipt"), L(1.0)),
            Gt(
                P0("episode", "state_seq"),
                P0("episode", "locomotion_measured_state_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "locomotion_start_x", T({
                "type": "IfThenElse",
                "cond": first,
                "then": P0("episode", "state_x"),
                "other": P0("episode", "locomotion_start_x"),
            })],
            ["set_attr", "episode", "locomotion_start_y", T({
                "type": "IfThenElse",
                "cond": first,
                "then": P0("episode", "state_y"),
                "other": P0("episode", "locomotion_start_y"),
            })],
            ["set_attr", "episode", "directed_progress", T({
                "type": "IfThenElse",
                "cond": first,
                "then": L(0.0),
                "other": directed_progress,
            })],
            ["set_attr", "episode", "maximum_directed_progress", T({
                "type": "IfThenElse",
                "cond": first,
                "then": L(0.0),
                "other": {
                    "type": "Max",
                    "items": [
                        P0("episode", "maximum_directed_progress"),
                        directed_progress,
                    ],
                },
            })],
            ["set_attr", "episode", "locomotion_residual_m", T(
                If(
                    first,
                    P0("episode", "target_directed_progress_m"),
                    locomotion_residual,
                )
            )],
            ["set_attr", "episode", "locomotion_drive_active", T(
                If(Gt(locomotion_residual, L(0.0)), L(1.0), L(0.0))
            )],
            ["set_attr", "episode", "lateral_offset", T({
                "type": "IfThenElse",
                "cond": first,
                "then": L(0.0),
                "other": lateral_offset,
            })],
            ["set_attr", "episode", "maximum_lateral_excursion", T({
                "type": "IfThenElse",
                "cond": first,
                "then": L(0.0),
                "other": {
                    "type": "Max",
                    "items": [
                        P0("episode", "maximum_lateral_excursion"),
                        Abs(lateral_offset),
                    ],
                },
            })],
            ["set_attr", "episode", "walking_minimum_height", T({
                "type": "IfThenElse",
                "cond": first,
                "then": P0("episode", "state_z"),
                "other": {
                    "type": "Min",
                    "items": [
                        P0("episode", "walking_minimum_height"),
                        P0("episode", "state_z"),
                    ],
                },
            })],
            ["set_attr", "episode", "walking_peak_tilt", T({
                "type": "IfThenElse",
                "cond": first,
                "then": tilt,
                "other": {
                    "type": "Max",
                    "items": [
                        P0("episode", "walking_peak_tilt"),
                        tilt,
                    ],
                },
            })],
            ["set_attr", "episode", "walking_mean_tilt", T({
                "type": "IfThenElse",
                "cond": familiarizing,
                "then": Plus(
                    P0("episode", "walking_mean_tilt"),
                    Div(
                        Minus(
                            tilt,
                            P0("episode", "walking_mean_tilt"),
                        ),
                        next_tilt_sample_count,
                    ),
                ),
                "other": P0("episode", "walking_mean_tilt"),
            })],
            ["set_attr", "episode", "walking_tilt_sample_count", T({
                "type": "IfThenElse",
                "cond": familiarizing,
                "then": next_tilt_sample_count,
                "other": P0("episode", "walking_tilt_sample_count"),
            })],
            ["set_attr", "episode", "walking_peak_abs_vx", T({
                "type": "IfThenElse",
                "cond": first,
                "then": abs_vx,
                "other": {
                    "type": "Max",
                    "items": [
                        P0("episode", "walking_peak_abs_vx"),
                        abs_vx,
                    ],
                },
            })],
            ["set_attr", "episode", "walking_peak_abs_vy", T({
                "type": "IfThenElse",
                "cond": first,
                "then": abs_vy,
                "other": {
                    "type": "Max",
                    "items": [
                        P0("episode", "walking_peak_abs_vy"),
                        abs_vy,
                    ],
                },
            })],
            ["set_attr", "episode", "support_alternations", T(
                Plus(
                    P0("episode", "support_alternations"),
                    {
                        "type": "IfThenElse",
                        "cond": support_switched,
                        "then": L(1.0),
                        "other": L(0.0),
                    },
                )
            )],
            ["set_attr", "episode", "aerial_samples", T(
                Plus(
                    P0("episode", "aerial_samples"),
                    {
                        "type": "IfThenElse",
                        "cond": aerial,
                        "then": L(1.0),
                        "other": L(0.0),
                    },
                )
            )],
            ["set_attr", "episode", "double_support_samples", T(
                Plus(
                    P0("episode", "double_support_samples"),
                    If(double_support, L(1.0), L(0.0)),
                )
            )],
            ["set_attr", "episode", "support_topology_samples", T(
                Plus(P0("episode", "support_topology_samples"), L(1.0))
            )],
            ["set_attr", "episode", "aerial_active", T(If(
                aerial,
                L(1.0),
                L(0.0),
            ))],
            ["set_attr", "episode", "last_unilateral_support", T({
                "type": "IfThenElse",
                "cond": Gt(unilateral_support, L(0.0)),
                "then": unilateral_support,
                "other": P0("episode", "last_unilateral_support"),
            })],
            ["set_attr", "episode", "current_support_phase", T(
                unilateral_support
            )],
            ["set_attr", "episode", "locomotion_measurements_initialized", 1.0],
            ["set_attr", "episode", "locomotion_measured_state_seq", T(
                P0("episode", "state_seq")
            )],
        ],
    }


def expose_motor_decision_option_rule():
    """Initialize neutral shared-collapse fields on primitive joint models."""
    return {
        "name": "ha_expose_motor_decision_option",
        "area": "embodied_sensorimotor",
        "latency_class": "background",
        "comment": "Initialize domain-neutral fields without exposing a base "
        "model as a current option. Support-conditioned phase experts author "
        "the grounded options used for learned walking-primary competition.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_action_model", "model"],
        ],
        "where": Eq(P0("model", "motor_option_schema_ready"), L(0.0)),
        "effects": [
            ["set_attr", "model", "available", 1.0],
            ["set_attr", "model", "ordinal", T(P0("model", "ordinal"))],
            ["set_attr", "model", "default_value", 0.0],
            ["set_attr", "model", "learned_value", 0.0],
            ["set_attr", "model", "grounded_value", 0.0],
            ["set_attr", "model", "decision_experience_count", 0.0],
            ["set_attr", "model", "motor_option_schema_ready", 1.0],
            [
                "set_attr",
                "model",
                "motor_option_value_provenance",
                "neutral_schema_ready_phase_experts_hold_authority",
            ],
        ],
    }


def request_primitive_learning_rule():
    """Recruit plasticity without expanding calibration into full cognition."""
    return {
        "name": "ha_request_primitive_motor_learning",
        "area": "humanoid_sensorimotor_adaptation",
        "order": -5,
        "latency_class": "hard_realtime",
        "comment": "A verified primitive twitch recruits only the shared "
        "adaptive-learning sheet. Support-phase trials enter the full shared "
        "multimodal receipt lifecycle; calibration twitches do not mint an "
        "unbounded efference/evidence population.",
        "match": [
            [
                "agent",
                "has_embodied_adaptive_learning_task_set",
                "task_set",
            ],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_action_model", "model"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(
                Count(Neighbours(
                    "trial",
                    "uses_humanoid_phase_action_model",
                )),
                L(0.0),
            ),
            Eq(
                P0("outcome", "primitive_learning_escalation_requested"),
                L(0.0),
            ),
        ),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "verified_humanoid_primitive_receipt",
                "epoch": T(P0("episode", "state_seq")),
                "provenance_kind": "graph_authored_motor_plasticity",
            }],
            [
                "add_edge",
                "outcome",
                "has_system_two_escalation",
                "escalation",
            ],
            ["add_edge", "escalation", "about_context", "outcome"],
            ["add_edge", "escalation", "recruits_task_set", "task_set"],
            [
                "set_attr",
                "outcome",
                "primitive_learning_escalation_requested",
                1.0,
            ],
        ],
    }


HUMANOID_SOFT_REALTIME_RULES = {
    "ha_close_staged_synergy_calibration",
    "ha_tune_response_horizon_from_prediction_receipt",
    "ha_tune_compound_movement_interval",
    "ha_learn_opaque_joint_consequence",
    "ha_learn_compound_interaction_residual",
    "ha_confirm_local_phase_prediction_from_receipt",
    "ha_reground_invalidated_local_phase_prediction",
    "ha_learn_support_phase_consequence_online",
    "ha_learn_identifiable_pair_program_residual",
    "ha_update_reassociated_motor_memory",
    "ha_finish_arbitrary_program_credit_assignment",
    "ha_ground_synthesized_motor_program_from_receipt",
    "ha_update_grounded_motor_sequence_transition",
    "ha_close_phase_adaptation_after_alphabet_quiet",
    "ha_learn_whole_body_get_up_consequence",
    "ha_learn_situated_recovery_basin_action",
    "ha_update_situated_recovery_basin_action",
}

HUMANOID_BACKGROUND_RULES = {
    "ha_store_grounded_program_by_body_shape",
    "ha_consolidate_equivalent_motor_program",
    "ha_consolidate_motor_sequence_transition",
    "ha_expose_motor_decision_option",
}

HUMANOID_ON_DEMAND_HINT_RULES = {
    "ha_bind_motor_plan_hint_stage_search_basin",
    "ha_route_abstract_motor_plan_hint_stage_basin",
}


def apply_biological_schedule(manifest_dict):
    """Put motor work on the graph-held sheet matching its deadline.

    The shared sensorimotor core already recruits ``adaptive_learning`` and
    ``embodied_sensorimotor`` from verified physical receipts. Reusing those
    areas makes plasticity and consolidation interruptible without creating a
    body-specific host scheduler. Unlisted rules stay on the hard sheet:
    sensing, viability, action release, safety withdrawal, and bounded
    episode/bootstrap bookkeeping.
    """
    known = (
        HUMANOID_SOFT_REALTIME_RULES
        | HUMANOID_BACKGROUND_RULES
        | HUMANOID_ON_DEMAND_HINT_RULES
    )
    authored = {rule["name"] for rule in manifest_dict["rules"]}
    missing = known - authored
    if missing:
        raise ValueError(f"scheduled humanoid rules are absent: {sorted(missing)}")
    for rule in manifest_dict["rules"]:
        if rule["name"] in HUMANOID_SOFT_REALTIME_RULES:
            rule["area"] = "adaptive_learning"
            rule["latency_class"] = "soft_realtime"
        elif rule["name"] in HUMANOID_BACKGROUND_RULES:
            rule["area"] = "embodied_sensorimotor"
            rule["latency_class"] = "background"
        elif rule["name"] in HUMANOID_ON_DEMAND_HINT_RULES:
            rule["area"] = "humanoid_motor_plan_hint_routing"
            rule["latency_class"] = "background"
    return manifest_dict


def manifest():
    # These are contact-cycle hypotheses, not speed bands.  Their order gives
    # a biologically grounded topology continuum: walking has double support
    # and no flight; progressively more impulsive attractors trade that for
    # aerial/elastic phases.  Receipts decide whether a body actually realizes
    # a hypothesis and the graph is free to select any attractor at any speed.
    # NO RULE READS THE NAMES -- and that is the whole of what was measured.
    # Measured on the emitted seed: zero rules reference `coordination_family`,
    # `gait_name`, or any of "walking", "jogging", "running", "sprinting".
    # This says nothing about NON-rule readers, and there are two, enumerated
    # (rung 4, 2026-08-10, KeyError: 'name' after a full 600-action run):
    #   scripts/jabberwock_humanoid_walk.py:4136  -- reports active_gait_attractor
    #   tests/test_humanoid_adaptation_migrated.py:352 -- asserts the gait_name set
    # An earlier revision of this comment read "THE NAMES WERE READ BY NOTHING",
    # which was false: it characterised the readers instead of enumerating them,
    # so it stayed true-sounding while two readers existed. Enumerate, never
    # characterise. What every rule DOES read is the
    # ordinal and its arithmetic derivatives -- target_aerial_intervals
    # (= ordinal), target_double_support_intervals (= count - ordinal),
    # flight_phase_authority (= ordinal > 0), elastic_impulse_numerator,
    # support_transition_cost_numerator -- 75/16/12/26/26/16 references
    # respectively.
    #
    # So this was never four gaits. It is ONE PARAMETER sampled at four points,
    # with a folk name glued to each sample: a duty-cycle continuum from
    # full double support to full flight. Naming its samples is the same move
    # as calling a lungfish a fish -- the label groups by surface resemblance
    # while the structure that generates the diversity is a single axis, and
    # no better definition rescues it. A shuffle, a skip, a crawl or a hop is
    # not a point on this axis at all, so no name here could ever cover them.
    #
    # The parameter is kept because the graph genuinely uses it. The taxonomy
    # is removed because nothing does.
    gait_attractor_count = 4
    gait_interval_count = gait_attractor_count - 1
    support_sensor_count = 2
    support_regime_count = support_sensor_count + 1
    gait_attractor_nodes = [
        {
            "local_id": 2 + gait_ordinal,
            "type": "HumanoidGaitAttractor",
            "attrs": {
                "ordinal": float(gait_ordinal),
                "target_aerial_intervals": float(gait_ordinal),
                "target_double_support_intervals": float(
                    gait_interval_count - gait_ordinal
                ),
                "flight_phase_authority": float(gait_ordinal > 0),
                "elastic_impulse_numerator": float(gait_ordinal),
                "support_transition_cost_numerator": float(
                    gait_interval_count - gait_ordinal
                ),
            },
        }
        for gait_ordinal in range(gait_attractor_count)
    ]

    # Three support regimes arise mechanically from two support sensors plus
    # the no-contact regime.  Their order-N Cartesian composition with each
    # gait attractor supplies the initial controller frontier.
    residual_regime_rows = tuple(
        (
            gait_ordinal,
            residual_numerator,
            viability_numerator,
        )
        for gait_ordinal in range(gait_attractor_count)
        for residual_numerator in range(1, support_regime_count + 1)
        for viability_numerator in range(1, support_regime_count + 1)
    )
    first_residual_local_id = 2 + gait_attractor_count
    residual_regime_nodes = [
        {
            "local_id": first_residual_local_id + ordinal,
            "type": "HumanoidResidualRegime",
            "attrs": {
                "ordinal": float(ordinal),
                "gait_ordinal": float(gait_ordinal),
                "target_aerial_intervals": float(gait_ordinal),
                "target_double_support_intervals": float(
                    gait_interval_count - gait_ordinal
                ),
                "residual_gain_numerator": float(residual_numerator),
                "viability_scale_numerator": float(viability_numerator),
                "sample_count": 0.0,
                "completed_windows": 0.0,
                "selection_count": 0.0,
                "unsafe_receipt_count": 0.0,
                "q": 0.0,
                "asym_count": float(support_regime_count ** 2),
                "novelty": 0.0,
                "fast_prediction_residual": 0.0,
                "slow_prediction_residual": 0.0,
                "learning_progress": 0.0,
                "mean_directed_step": 0.0,
                "mean_abs_lateral_step": 0.0,
                "mean_tilt": 0.0,
                "mean_height_deficit": 0.0,
                "mean_support_deficit": 0.0,
                "mean_normalized_energy": 0.0,
                "mean_aerial_occupancy": 0.0,
                "mean_double_support_occupancy": 0.0,
            },
        }
        for ordinal, (
            gait_ordinal,
            residual_numerator,
            viability_numerator,
        ) in enumerate(residual_regime_rows)
    ]
    motor_plan_hint_task_local_id = (
        first_residual_local_id + len(residual_regime_rows)
    )
    return apply_biological_schedule({
        "id": "humanoid_adaptation",
        "version": "1.32.0",
        "depends_on": [
            "decision_core",
            "embodied_motor_priors",
            "motor_decision_collapse",
            "embodied_capability_bootstrap",
            "cmu_motion_topology_bootstrap",
        ],
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "description": "Learn local balance effects for an articulated body "
        "through opaque joint twitches and receipt-backed graph mutation, "
        "with reflex, adaptive, and consolidation work on distinct graph-held "
        "deadline sheets.",
        "nodes": [
            {
                "local_id": 1,
                "type": "HumanoidPolicy",
                "attrs": {
                    "babble_samples": 1.0,
                    "gravity_acceleration": 9.81,
                    "minimum_upright_height_fraction": 0.75,
                    "target_froude_speed": 0.06,
                    "support_phase_prior_strength": 9.0,
                    "gait_attractor_interval_count": float(
                        gait_interval_count
                    ),
                    "gait_surprise_confirmation_receipts": 0.0,
                    "shared_motor_collapse_enabled": 1.0,
                    "native_humanoid_composition_enabled": 1.0,
                    # Whole-body future-manifold fallback is deliberately
                    # opt-in.  The ordinary support-local humanoid selector
                    # remains the exact gate-off baseline until a runtime
                    # agent explicitly enables multi-frame certification.
                    "future_manifold_enabled": 0.0,
                    "future_manifold_temporal_anchors_enabled": 0.0,
                    "future_manifold_local_refinement_enabled": 0.0,
                    "future_manifold_projection_budget": 16.0,
                    "future_manifold_physical_horizon": 0.0,
                    "future_manifold_anchor_growth": 2.0,
            "future_manifold_max_shape_order": 1.0,
            "future_manifold_max_refinements": 16.0,
            # One unchanged projected tick is sufficient to close a local
            # developmental replay certificate.  The native evaluator still
            # extends or refines when the state moves; this only supplies the
            # previously missing termination contract for the temporally
            # foveated path.
            "future_manifold_path_fixed_point_run": 1.0,
            "support_geometry_preview_authority": 0.0,
                    "persistent_task_residual_authority": 0.0,
                    "takeoff_motor_compression_authority": 1.0,
                },
            },
            *gait_attractor_nodes,
            *residual_regime_nodes,
            {
                "local_id": motor_plan_hint_task_local_id,
                "type": "SystemTwoTaskSet",
                "attrs": {
                    "area": "humanoid_motor_plan_hint_routing",
                    "enabled": 1,
                    "provenance_kind": "on_demand_plan_hint_routing",
                },
            },
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_humanoid_policy",
                "tgt": {"local": 1},
                "attrs": {},
            },
            *[
                {
                    "src": {"local": 1},
                    "type": "has_humanoid_gait_attractor",
                    "tgt": {"local": 2 + gait_ordinal},
                    "attrs": {},
                }
                for gait_ordinal in range(gait_attractor_count)
            ],
            *[
                {
                    "src": {"local": 1},
                    "type": "has_humanoid_residual_regime",
                    "tgt": {
                        "local": first_residual_local_id + ordinal,
                    },
                    "attrs": {},
                }
                for ordinal in range(len(residual_regime_rows))
            ],
            *[
                {
                    "src": {"local": 2 + gait_ordinal},
                    "type": "realizes_humanoid_gait_with_regime",
                    "tgt": {
                        "local": first_residual_local_id + ordinal,
                    },
                    "attrs": {},
                }
                for ordinal, (
                    gait_ordinal,
                    _,
                    _,
                ) in enumerate(residual_regime_rows)
            ],
            {
                "src": {"role": "agent_root"},
                "type": "has_humanoid_motor_plan_hint_routing_task_set",
                "tgt": {"local": motor_plan_hint_task_local_id},
                "attrs": {},
            },
        ],
        "productions": [
            {
                "provenance": "humanoid_adaptation:agent_policy",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_humanoid_policy",
                "tgt": {"type": "HumanoidPolicy", "var": "policy"},
            },
            {
                "provenance": "humanoid_adaptation:plan_hint_routing_tasks",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": (
                    "has_humanoid_motor_plan_hint_routing_task_set"
                ),
                "tgt": {
                    "type": "SystemTwoTaskSet",
                    "var": "routing_tasks",
                },
            },
            {
                "provenance": "humanoid_adaptation:agent_episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_humanoid_episode",
                "tgt": {"type": "HumanoidEpisode", "var": "episode"},
            },
            {
                "provenance": "humanoid_adaptation:situated_locomotion_context",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": (
                    "has_current_humanoid_situated_locomotion_context"
                ),
                "tgt": {
                    "type": "HumanoidSituatedLocomotionContext",
                    "var": "context",
                },
            },
            {
                "provenance": "humanoid_adaptation:residual_regime",
                "src": {"type": "HumanoidPolicy", "var": "policy"},
                "edge_type": "has_humanoid_residual_regime",
                "tgt": {
                    "type": "HumanoidResidualRegime",
                    "var": "regime",
                },
            },
            {
                "provenance": "humanoid_adaptation:gait_attractor",
                "src": {"type": "HumanoidPolicy", "var": "policy"},
                "edge_type": "has_humanoid_gait_attractor",
                "tgt": {
                    "type": "HumanoidGaitAttractor",
                    "var": "gait",
                },
            },
            {
                "provenance": "humanoid_adaptation:gait_regime",
                "src": {
                    "type": "HumanoidGaitAttractor",
                    "var": "gait",
                },
                "edge_type": "realizes_humanoid_gait_with_regime",
                "tgt": {
                    "type": "HumanoidResidualRegime",
                    "var": "regime",
                },
            },
            {
                "provenance": "humanoid_adaptation:active_gait_regime",
                "src": {
                    "type": "HumanoidEpisode",
                    "var": "episode",
                },
                "edge_type": "evaluates_humanoid_residual_regime",
                "tgt": {
                    "type": "HumanoidResidualRegime",
                    "var": "regime",
                },
            },
            {
                "provenance": "humanoid_adaptation:body_shape_library",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_humanoid_body_shape_library",
                "tgt": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
            },
            {
                "provenance": "humanoid_adaptation:embodied_motor_plan_hint_library",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_motor_plan_hint_library",
                "tgt": {
                    "type": "EmbodiedMotorPlanHint",
                    "var": "hint",
                },
            },
            {
                "provenance": "humanoid_adaptation:embodied_motor_plan_hint_stage",
                "src": {"type": "EmbodiedMotorPlanHint", "var": "hint"},
                "edge_type": "has_embodied_motor_plan_hint_stage",
                "tgt": {
                    "type": "EmbodiedMotorPlanHintStage",
                    "var": "stage",
                },
            },
            {
                "provenance": "humanoid_adaptation:considered_motor_plan_hint",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "considers_humanoid_motor_plan_hint",
                "tgt": {"type": "EmbodiedMotorPlanHint", "var": "hint"},
            },
            {
                "provenance": "humanoid_adaptation:plan_hint_body_shape",
                "src": {"type": "EmbodiedMotorPlanHint", "var": "hint"},
                "edge_type": "derived_from_humanoid_body_shape",
                "tgt": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
            },
            {
                "provenance": "humanoid_adaptation:plan_hint_program_basin",
                "src": {
                    "type": "EmbodiedMotorPlanHintStage",
                    "var": "stage",
                },
                "edge_type": "suggests_humanoid_motor_program_basin",
                "tgt": {"type": "HumanoidMotorProgram", "var": "program"},
            },
            {
                "provenance": "humanoid_adaptation:motor_routing_shape",
                "src": {"type": "HumanoidMotorProgram", "var": "program"},
                "edge_type": "realizes_embodied_motor_routing_shape",
                "tgt": {
                    "type": "EmbodiedMotorRoutingShape",
                    "var": "routing_shape",
                },
            },
            {
                "provenance": (
                    "humanoid_adaptation:unrouted_grounded_motor_program"
                ),
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": (
                    "has_unrouted_grounded_humanoid_motor_program"
                ),
                "tgt": {"type": "HumanoidMotorProgram", "var": "program"},
            },
            {
                "provenance": "humanoid_adaptation:motor_consequence_shape",
                "src": {"type": "HumanoidMotorProgram", "var": "program"},
                "edge_type": "realizes_embodied_motor_consequence_shape",
                "tgt": {
                    "type": "EmbodiedMotorConsequenceRoutingShape",
                    "var": "consequence_shape",
                },
            },
            {
                "provenance": "humanoid_adaptation:routing_shape_program_basin",
                "src": {
                    "type": "EmbodiedMotorRoutingShape",
                    "var": "routing_shape",
                },
                "edge_type": "suggests_humanoid_motor_program_basin",
                "tgt": {"type": "HumanoidMotorProgram", "var": "program"},
            },
            {
                "provenance": "humanoid_adaptation:episode_program_basin_seed",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_program_basin_seed",
                "tgt": {"type": "HumanoidMotorProgram", "var": "program"},
            },
            {
                "provenance": "humanoid_adaptation:episode_program_search_index",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_program_search_index",
                "tgt": {"type": "HumanoidMotorProgram", "var": "program"},
            },
            {
                "provenance": "humanoid_adaptation:recognized_body_shape",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "recognizes_humanoid_body_shape",
                "tgt": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
            },
            {
                "provenance": "humanoid_adaptation:shape_motor_program",
                "src": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
                "edge_type": "stores_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:duplicate_shape_program",
                "src": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
                "edge_type": "stores_duplicate_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:program_shape_identity",
                "src": {
                    "type": "HumanoidMotorProgram",
                    "var": "duplicate",
                },
                "edge_type": "is_shape_duplicate_of_humanoid_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "canonical",
                },
            },
            {
                "provenance": "humanoid_adaptation:shape_residual_memory",
                "src": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
                "edge_type": "stores_humanoid_residual_regime_memory",
                "tgt": {
                    "type": "HumanoidResidualRegimeMemory",
                    "var": "memory",
                },
            },
            {
                "provenance": "humanoid_adaptation:library_program_member",
                "src": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
                "edge_type": "has_humanoid_library_motor_member",
                "tgt": {
                    "type": "HumanoidLibraryMotorMember",
                    "var": "member",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_model",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_action_model",
                "tgt": {"type": "HumanoidActionModel", "var": "model"},
            },
            {
                "provenance": "humanoid_adaptation:episode_trial",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_trial",
                "tgt": {"type": "HumanoidMotorTrial", "var": "trial"},
            },
            {
                "provenance": "humanoid_adaptation:episode_motor_fixation",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_fixation",
                "tgt": {"type": "HumanoidMotorFixation", "var": "fixation"},
            },
            {
                "provenance": "humanoid_adaptation:episode_current_motor_fixation",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_current_humanoid_motor_fixation",
                "tgt": {"type": "HumanoidMotorFixation", "var": "fixation"},
            },
            {
                "provenance": "humanoid_adaptation:episode_candidate_motor_fixation",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_candidate_humanoid_motor_fixation",
                "tgt": {"type": "HumanoidMotorFixation", "var": "fixation"},
            },
            {
                "provenance": "humanoid_adaptation:motor_fixation_transition",
                "src": {"type": "HumanoidMotorFixation", "var": "previous"},
                "edge_type": "continues_to_humanoid_motor_fixation",
                "tgt": {"type": "HumanoidMotorFixation", "var": "fixation"},
            },
            {
                "provenance": "humanoid_adaptation:trial_efference_copy",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "has_humanoid_motor_efference_copy",
                "tgt": {"type": "HumanoidMotorEfferenceCopy", "var": "copy"},
            },
            {
                "provenance": "humanoid_adaptation:efference_copy_fixation",
                "src": {"type": "HumanoidMotorEfferenceCopy", "var": "copy"},
                "edge_type": "issued_from_humanoid_motor_fixation",
                "tgt": {"type": "HumanoidMotorFixation", "var": "fixation"},
            },
            {
                "provenance": "humanoid_adaptation:episode_phase_model",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_phase_action_model",
                "tgt": {
                    "type": "HumanoidPhaseActionModel",
                    "var": "phase_model",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_synergy_model",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_synergy_model",
                "tgt": {
                    "type": "HumanoidSynergyModel",
                    "var": "synergy",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_get_up_model",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_get_up_action_model",
                "tgt": {
                    "type": "HumanoidGetUpActionModel",
                    "var": "get_up_model",
                },
            },
            {
                "provenance": "humanoid_adaptation:get_up_action_model",
                "src": {
                    "type": "HumanoidGetUpActionModel",
                    "var": "get_up_model",
                },
                "edge_type": "generalizes_humanoid_action_model",
                "tgt": {
                    "type": "HumanoidActionModel",
                    "var": "model",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_recovery_basin",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_recovery_basin",
                "tgt": {"type": "HumanoidRecoveryBasin", "var": "basin"},
            },
            {
                "provenance": "humanoid_adaptation:current_recovery_basin",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_current_humanoid_recovery_basin",
                "tgt": {"type": "HumanoidRecoveryBasin", "var": "basin"},
            },
            {
                "provenance": "humanoid_adaptation:recovery_basin_action",
                "src": {"type": "HumanoidRecoveryBasin", "var": "basin"},
                "edge_type": "has_humanoid_recovery_basin_action",
                "tgt": {
                    "type": "HumanoidRecoveryBasinAction",
                    "var": "basin_action",
                },
            },
            {
                "provenance": "humanoid_adaptation:active_recovery_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_active_humanoid_recovery_program",
                "tgt": {
                    "type": "HumanoidRecoveryProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:selected_recovery_primary",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_selected_humanoid_recovery_primary",
                "tgt": {
                    "type": "HumanoidRecoveryBasinAction",
                    "var": "basin_action",
                },
            },
            {
                "provenance": "humanoid_adaptation:basin_recovery_program",
                "src": {"type": "HumanoidRecoveryBasin", "var": "basin"},
                "edge_type": "has_humanoid_recovery_program",
                "tgt": {
                    "type": "HumanoidRecoveryProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:program_start_basin",
                "src": {
                    "type": "HumanoidRecoveryProgram",
                    "var": "program",
                },
                "edge_type": "starts_from_humanoid_recovery_basin",
                "tgt": {"type": "HumanoidRecoveryBasin", "var": "basin"},
            },
            {
                "provenance": "humanoid_adaptation:shape_recovery_basin",
                "src": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
                "edge_type": "stores_humanoid_recovery_basin",
                "tgt": {
                    "type": "HumanoidRecoveryBasin",
                    "var": "basin",
                },
            },
            {
                "provenance": "humanoid_adaptation:recovery_basin_transition",
                "src": {"type": "HumanoidRecoveryBasin", "var": "previous"},
                "edge_type": "continues_to_humanoid_recovery_basin",
                "tgt": {"type": "HumanoidRecoveryBasin", "var": "basin"},
            },
            {
                "provenance": "humanoid_adaptation:recovery_basin_hint",
                "src": {"type": "HumanoidRecoveryBasin", "var": "basin"},
                "edge_type": "inherits_humanoid_recovery_actions_from",
                "tgt": {"type": "HumanoidRecoveryBasin", "var": "previous"},
            },
            {
                "provenance": "humanoid_adaptation:trial_recovery_basin",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "starts_from_humanoid_recovery_basin",
                "tgt": {"type": "HumanoidRecoveryBasin", "var": "basin"},
            },
            {
                "provenance": "humanoid_adaptation:episode_motor_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_archived_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_consolidated_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_active_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_active_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_ready_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_ready_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_resumes_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "resumes_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_recalls_program",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "recalls_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_preparation",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_preparation",
                "tgt": {
                    "type": "HumanoidMotorPreparation",
                    "var": "preparation",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_active_preparation",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_active_humanoid_motor_preparation",
                "tgt": {
                    "type": "HumanoidMotorPreparation",
                    "var": "preparation",
                },
            },
            {
                "provenance": "humanoid_adaptation:preparation_program",
                "src": {
                    "type": "HumanoidMotorPreparation",
                    "var": "preparation",
                },
                "edge_type": "prepares_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:preparation_transition",
                "src": {
                    "type": "HumanoidMotorPreparation",
                    "var": "preparation",
                },
                "edge_type": "prepares_humanoid_motor_transition",
                "tgt": {
                    "type": "HumanoidMotorTransition",
                    "var": "transition",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_motor_transition",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_motor_transition",
                "tgt": {
                    "type": "HumanoidMotorTransition",
                    "var": "transition",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_recalls_transition",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "recalls_humanoid_motor_transition",
                "tgt": {
                    "type": "HumanoidMotorTransition",
                    "var": "transition",
                },
            },
            {
                "provenance": "humanoid_adaptation:episode_motor_context",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "last_verified_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:program_transition",
                "src": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
                "edge_type": "has_humanoid_motor_transition",
                "tgt": {
                    "type": "HumanoidMotorTransition",
                    "var": "transition",
                },
            },
            {
                "provenance": "humanoid_adaptation:transition_program",
                "src": {
                    "type": "HumanoidMotorTransition",
                    "var": "transition",
                },
                "edge_type": "continues_with_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:program_frontier",
                "src": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
                "edge_type": "has_humanoid_motor_program_frontier",
                "tgt": {
                    "type": "HumanoidMotorProgramFrontier",
                    "var": "frontier",
                },
            },
            {
                "provenance": "humanoid_adaptation:program_phase_member",
                "src": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
                "edge_type": "includes_humanoid_phase_action_model",
                "tgt": {
                    "type": "HumanoidPhaseActionModel",
                    "var": "phase_model",
                },
            },
            {
                "provenance": "humanoid_adaptation:program_curiosity_candidate",
                "src": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
                "edge_type": (
                    "has_selected_humanoid_compound_curiosity_candidate"
                ),
                "tgt": {
                    "type": "HumanoidPhaseActionModel",
                    "var": "phase_model",
                },
            },
            {
                "provenance": "humanoid_adaptation:synergy_primary",
                "src": {
                    "type": "HumanoidSynergyModel",
                    "var": "synergy",
                },
                "edge_type": "has_humanoid_synergy_primary",
                "tgt": {"type": "HumanoidActionModel", "var": "model"},
            },
            {
                "provenance": "humanoid_adaptation:synergy_secondary",
                "src": {
                    "type": "HumanoidSynergyModel",
                    "var": "synergy",
                },
                "edge_type": "has_humanoid_synergy_secondary",
                "tgt": {"type": "HumanoidActionModel", "var": "model"},
            },
            {
                "provenance": "humanoid_adaptation:phase_general_model",
                "src": {
                    "type": "HumanoidPhaseActionModel",
                    "var": "phase_model",
                },
                "edge_type": "generalizes_humanoid_action_model",
                "tgt": {
                    "type": "HumanoidActionModel",
                    "var": "model",
                },
            },
            {
                "provenance": "humanoid_adaptation:trial_model",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "uses_humanoid_action_model",
                "tgt": {"type": "HumanoidActionModel", "var": "model"},
            },
            {
                "provenance": "humanoid_adaptation:trial_outcome",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "has_humanoid_transition",
                "tgt": {"type": "HumanoidTransition", "var": "outcome"},
            },
            {
                "provenance": "humanoid_adaptation:trial_phase_model",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "uses_humanoid_phase_action_model",
                "tgt": {
                    "type": "HumanoidPhaseActionModel",
                    "var": "phase_model",
                },
            },
            {
                "provenance": "humanoid_adaptation:trial_synergy_model",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "uses_humanoid_synergy_model",
                "tgt": {
                    "type": "HumanoidSynergyModel",
                    "var": "synergy",
                },
            },
            {
                "provenance": "humanoid_adaptation:trial_motor_program",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "enacts_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:trial_synthesized_program",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "synthesized_humanoid_motor_program",
                "tgt": {
                    "type": "HumanoidMotorProgram",
                    "var": "program",
                },
            },
            {
                "provenance": "humanoid_adaptation:trial_motor_transition",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "enacts_humanoid_motor_transition",
                "tgt": {
                    "type": "HumanoidMotorTransition",
                    "var": "transition",
                },
            },
            {
                "provenance": "humanoid_adaptation:trial_preparation",
                "src": {"type": "HumanoidMotorTrial", "var": "trial"},
                "edge_type": "released_from_humanoid_motor_preparation",
                "tgt": {
                    "type": "HumanoidMotorPreparation",
                    "var": "preparation",
                },
            },
        ],
        "rules": [
            recognize_body_shape_rule(),
            recognize_late_restored_body_shape_rule(),
            mint_body_shape_rule(),
            open_library_program_shape_audit_rule(),
            recognize_duplicate_library_program_shape_rule(),
            close_unique_library_program_shape_audit_rule(),
            select_motor_plan_task_context_rule(),
            consider_motor_plan_hint_rule(),
            classify_grounded_program_routing_shape_rule(),
            request_grounded_program_routing_rule(),
            classify_grounded_program_consequence_shape_rule(),
            bind_indexed_bootstrap_stage_basin_rule(),
            bind_motor_plan_hint_stage_basin_rule(),
            bind_abstract_plan_hint_stage_basin_rule(),
            restore_shape_residual_regime_memory_rule(),
            bind_warm_program_member_rule(),
            activate_warm_program_rule(),
            bind_warm_motor_transition_source_rule(),
            bind_warm_motor_transition_target_rule(),
            activate_warm_motor_transition_rule(),
            request_motor_library_consolidation_rule(),
            mint_shape_residual_regime_memory_rule(),
            update_shape_residual_regime_memory_rule(),
            store_program_by_body_shape_rule(),
            store_verified_motor_transition_by_body_shape_rule(),
            withdraw_unsafe_program_from_shape_rule(),
            open_situated_locomotion_context_rule(),
            close_situated_locomotion_context_rule(),
            measure_rule(),
            acknowledge_body_reset_rule(),
            measure_locomotion_rule(),
            hold_deliberate_task_controller_rule(),
            initialize_response_horizon_rule(),
            focus_topology_sensitive_response_horizon_rule(),
            choose_babble_rule(),
            initialize_phase_model_rule(),
            initialize_synergy_model_rule(),
            choose_synergy_probe_rule(),
            close_synergy_calibration_rule(),
            retire_stale_ready_motor_authority_rule(),
            release_selected_developmental_trajectory_rule(),
            choose_balance_rule(),
            account_recovery_entry_rule(),
            mint_recovery_basin_rule(),
            recall_shape_recovery_basin_rule(),
            settle_recovery_basin_rule(),
            retire_recovery_basin_rule(),
            update_active_recovery_program_rule(),
            retire_recovery_program_rule(),
            continue_recovery_program_rule(),
            exit_gait_recovery_rule(),
            request_get_up_reset_rule(),
            route_recalled_recovery_successor_rule(),
            choose_recalled_recovery_path_transition_rule(),
            choose_recovery_basin_warm_start_rule(),
            choose_recovery_basin_reanchor_rule(),
            choose_basin_get_up_exploration_rule(),
            settle_before_recovery_composition_rule(),
            select_recovery_composition_primary_rule(),
            choose_basin_get_up_composition_rule(),
            choose_get_up_exploration_rule(),
            choose_get_up_exploitation_rule(),
            choose_gait_recovery_primary_rule(),
            explore_residual_regime_rule(),
            exploit_residual_regime_rule(),
            clear_stale_shared_walking_primary_rule(),
            prepare_shared_walking_primary_rule(),
            retire_inactive_shared_walking_primary_rule(),
            arm_shared_walking_primary_rule(),
            release_shared_walking_primary_rule(),
            choose_walking_primary_rule(),
            recall_verified_takeoff_stage_rule(),
            recall_motor_sequence_rule(),
            release_prepared_motor_sequence_rule(),
            recall_motor_memory_rule(),
            release_prepared_motor_memory_rule(),
            materialize_learning_safety_context_rule(),
            establish_future_manifold_bounds_rule(),
            stamp_future_manifold_audit_contract_rule(),
            retire_stale_motor_program_synthesis_rule(),
            choose_walking_rule(),
            resume_motor_program_rule(),
            audit_takeoff_compound_frontier_rule(),
            open_compound_curiosity_selection_rule(),
            select_compound_curiosity_candidate_rule(),
            close_empty_compound_curiosity_selection_rule(),
            expand_compound_curiosity_program_rule(),
            expand_motor_program_rule(),
            native_expand_motor_program_rule(),
            close_motor_program_rule(),
            project_takeoff_effort_ratio_rule(),
            choose_tonic_control_rule(),
            open_motor_sequence_trial_rule(),
            open_recalled_motor_program_trial_rule(),
            open_canonical_synthesis_trial_rule(),
            open_motor_program_trial_rule(),
            open_trial_rule(),
            link_recovery_trial_basin_rule(),
            link_synergy_trial_rule(),
            link_active_phase_model_rule(),
            measure_gait_prediction_error_rule(),
            specialize_phase_context_rule(),
            confirm_phase_prediction_rule(),
            invalidate_stale_phase_prediction_rule(),
            reground_invalidated_phase_prediction_rule(),
            tune_response_horizon_rule(),
            tune_compound_interval_rule(),
            learn_residual_regime_rule(),
            learn_rule(),
            learn_synergy_probe_rule(),
            learn_phase_consequence_rule(),
            learn_identifiable_pair_program_rule(),
            update_recalled_motor_memory_rule(),
            consolidate_equivalent_motor_program_rule(),
            finish_phase_program_learning_rule(),
            learn_motor_program_receipt_rule(),
            break_motor_sequence_on_task_context_change_rule(),
            request_motor_sequence_consolidation_rule(),
            update_motor_sequence_transition_rule(),
            learn_motor_sequence_transition_rule(),
            invalidate_motor_sequence_transition_rule(),
            break_motor_sequence_context_rule(),
            prime_motor_sequence_context_rule(),
            break_motor_sequence_on_recovery_rule(),
            close_phase_adaptation_rule(),
            promote_recovery_basin_rule(),
            learn_recovery_basin_action_rule(),
            update_recovery_basin_action_rule(),
            store_recovery_basin_by_body_shape_rule(),
            learn_get_up_consequence_rule(),
            close_control_trial_rule(),
            request_primitive_learning_rule(),
            expose_motor_decision_option_rule(),
            mint_situated_motor_fixation_rule(),
            refresh_situated_motor_fixation_rule(),
            reanchor_motor_fixation_after_fixture_reset_rule(),
            invalidate_candidate_fixation_after_fixture_reset_rule(),
            propose_situated_motor_fixation_rule(),
            refresh_candidate_motor_fixation_rule(),
            reject_stale_candidate_motor_fixation_rule(),
            transition_situated_motor_fixation_rule(),
            bind_situated_motor_reference_rule(),
            issue_motor_efference_copy_rule(),
            confirm_motor_efference_copy_rule(),
        ],
    })


def main() -> int:
    output = ROOT / "seeds" / "humanoid_adaptation.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
