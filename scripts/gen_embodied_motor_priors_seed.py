"""Generate shared graph-native priors for embodied motor learning."""
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


def AO(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def P0(var, key):
    return Plus(A(var, key), L(0.0))


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


def If(cond, then, other):
    return {
        "type": "IfThenElse",
        "cond": cond,
        "then": then,
        "other": other,
    }


def Max(*items):
    return {"type": "Max", "items": list(items)}


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


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def T(term):
    return {"__term__": term}


PRIOR_KINDS = (
    (
        "embodiment",
        "Connected components, constraints, effectors and load paths are "
        "discoverable relational structure.",
    ),
    (
        "controllability",
        "Interventions reveal delayed, state-conditioned causal influence.",
    ),
    (
        "momentum_exchange",
        "Effectors may exchange momentum through contacts, wheels, reaction "
        "mass, thrusters or surrounding fluid; infer causal roles from "
        "receipts rather than body-part names.",
    ),
    (
        "energetics",
        "Prefer useful task work per free-energy expenditure while respecting "
        "power, regeneration, heat and finite storage constraints.",
    ),
    (
        "viability",
        "Prefer predicted states that remain recoverable over merely "
        "instantaneously stable states.",
    ),
    (
        "support",
        "Contacts may bear load, propel, pivot, brake or provide leverage.",
    ),
    (
        "composition",
        "Independent compatible actions may combine; interaction residuals "
        "must be learned from receipts.",
    ),
    (
        "temporal_continuity",
        "Useful actions persist, terminate on sensed events and form "
        "receipt-grounded transitions.",
    ),
    (
        "hybrid_manoeuvre",
        "Compose contact and free-flight capabilities across sensed phases: "
        "prepare, impulse, coast, arrest and recover are learned temporal "
        "roles rather than body-plan-specific commands.",
    ),
    (
        "redundancy",
        "Effectors with overlapping causal roles may substitute after damage.",
    ),
    (
        "chunking",
        "Repeated safe trajectories may consolidate into reusable programs.",
    ),
)


def recognize_episode_rule(edge_type: str, name: str):
    current = Neighbours("agent", "has_embodied_motor_episode")
    return {
        "name": name,
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Recognize an existing domain episode as an instance of "
        "the shared embodied motor relation without changing its authority.",
        "match": [["agent", edge_type, "episode"]],
        "where": Not(Exists(
            current,
            "known_episode",
            Eq(V("known_episode"), V("episode")),
        )),
        "effects": [[
            "add_edge",
            "agent",
            "has_embodied_motor_episode",
            "episode",
        ]],
    }


def bind_prior_rule():
    bound = Neighbours("episode", "uses_embodied_motor_prior")
    return {
        "name": "emp_bind_defeasible_prior_to_motor_episode",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["agent", "has_embodied_motor_prior", "prior"],
        ],
        "where": Not(Exists(
            bound,
            "bound_prior",
            Eq(A("bound_prior", "kind"), A("prior", "kind")),
        )),
        "effects": [[
            "add_edge",
            "episode",
            "uses_embodied_motor_prior",
            "prior",
        ]],
    }


def open_locomotor_state_rule():
    states = Neighbours("episode", "has_embodied_locomotor_state")
    return {
        "name": "emp_open_locomotor_continuity_state",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "uses_embodied_motor_prior", "prior"],
        ],
        "where": And(
            Eq(A("prior", "kind"), L("temporal_continuity")),
            Eq(Count(states), L(0.0)),
        ),
        "effects": [
            ["add_node", "state", "EmbodiedLocomotorState", {
                "initialized": 0.0,
                "measured_state_seq": -1.0,
                "previous_x": 0.0,
                "previous_y": 0.0,
                "start_x": 0.0,
                "start_y": 0.0,
                "path_length": 0.0,
                "last_directed_step": 0.0,
                "forward_reversal_count": 0.0,
                "support_switch_count": 0.0,
                "locomotor_cycle_count": 0.0,
                "last_support_phase": 0.0,
                "last_support_switch_request_seq": 0.0,
                "mean_support_phase_actions": 0.0,
                "reset_processed_seq": 0.0,
                "energetic_window_seq": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_embodied_locomotor_state",
                "state",
            ],
        ],
    }


def recognize_receipt_rule(
    trial_edge: str,
    model_edge: str,
    outcome_edge: str,
    name: str,
    *,
    unless_model_edge: str | None = None,
):
    receipts = Neighbours("episode", "has_embodied_motor_receipt")
    credited = Neighbours("model", "has_embodied_motor_receipt")
    trial_receipts = Neighbours("trial", "has_embodied_motor_receipt")
    normalization_needed = Or(
        Not(Exists(
            receipts,
            "known_receipt",
            Eq(V("known_receipt"), V("outcome")),
        )),
        Not(Exists(
            credited,
            "credited_receipt",
            Eq(V("credited_receipt"), V("outcome")),
        )),
        Not(Exists(
            trial_receipts,
            "trial_receipt",
            Eq(V("trial_receipt"), V("outcome")),
        )),
    )
    if unless_model_edge is not None:
        excluded_models = Neighbours("trial", unless_model_edge)
        normalization_needed = And(
            Eq(Count(excluded_models), L(0.0)),
            normalization_needed,
        )
    return {
        "name": name,
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Normalize a domain receipt and its credited opaque "
        "effector model into the shared embodied vocabulary.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", trial_edge, "trial"],
            ["trial", model_edge, "model"],
            ["trial", outcome_edge, "outcome"],
        ],
        "where": normalization_needed,
        "effects": [
            [
                "add_edge",
                "episode",
                "has_embodied_motor_receipt",
                "outcome",
            ],
            [
                "add_edge",
                "model",
                "has_embodied_motor_receipt",
                "outcome",
            ],
            [
                "add_edge",
                "trial",
                "has_embodied_motor_receipt",
                "outcome",
            ],
        ],
    }


def open_energetic_state_rule():
    states = Neighbours("episode", "has_embodied_energetic_state")
    return {
        "name": "emp_open_embodied_energetic_state",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "uses_embodied_motor_prior", "prior"],
        ],
        "where": And(
            Eq(A("prior", "kind"), L("energetics")),
            Eq(Count(states), L(0.0)),
        ),
        "effects": [
            ["add_node", "state", "EmbodiedEnergeticState", {
                "measured_world_step_index": -1.0,
                "measured_motor_epoch": -1.0,
                "reset_processed_seq": 0.0,
                "input_energy_joules": 0.0,
                "absorbed_energy_joules": 0.0,
                "recovered_energy_joules": 0.0,
                "net_energy_joules": 0.0,
                "thermal_load_joules": 0.0,
                "peak_power_watts": 0.0,
                "transport_path_length_metres": 0.0,
                "remaining_energy_joules": 0.0,
                "power_headroom_watts": 0.0,
                "thermal_headroom_joules": 0.0,
                "cost_of_transport": 0.0,
                "transport_economy": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_embodied_energetic_state",
                "state",
            ],
        ],
    }


def reset_energetic_state_rule():
    return {
        "name": "emp_reset_motor_energetics_on_episode_boundary",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "A simulator/body reset starts a new energetic accounting "
        "window while retaining learned effector capability models.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            [
                "episode",
                "has_embodied_energetic_state",
                "state",
            ],
        ],
        "where": Gt(
            P0("episode", "locomotor_prior_reset_seq"),
            P0("state", "reset_processed_seq"),
        ),
        "effects": [
            ["set_attr", "state", "measured_world_step_index", -1.0],
            ["set_attr", "state", "measured_motor_epoch", -1.0],
            ["set_attr", "state", "input_energy_joules", 0.0],
            ["set_attr", "state", "absorbed_energy_joules", 0.0],
            ["set_attr", "state", "recovered_energy_joules", 0.0],
            ["set_attr", "state", "net_energy_joules", 0.0],
            ["set_attr", "state", "thermal_load_joules", 0.0],
            ["set_attr", "state", "peak_power_watts", 0.0],
            ["set_attr", "state", "transport_path_length_metres", 0.0],
            ["set_attr", "state", "remaining_energy_joules", T(
                P0("episode", "state_available_energy_joules")
            )],
            ["set_attr", "state", "power_headroom_watts", T(
                P0("episode", "state_maximum_power_watts")
            )],
            ["set_attr", "state", "thermal_headroom_joules", T(
                P0("episode", "state_thermal_capacity_joules")
            )],
            ["set_attr", "state", "cost_of_transport", 0.0],
            ["set_attr", "state", "transport_economy", 0.0],
            ["set_attr", "state", "reset_processed_seq", T(
                P0("episode", "locomotor_prior_reset_seq")
            )],
            ["set_attr", "state", "energetic_window_seq", T(
                P0("episode", "locomotor_prior_reset_seq")
            )],
            ["set_attr", "episode", "motor_input_energy_joules", 0.0],
            ["set_attr", "episode", "motor_net_energy_joules", 0.0],
            ["set_attr", "episode", "motor_peak_power_watts", 0.0],
            ["set_attr", "episode", "motor_cost_of_transport", 0.0],
            ["set_attr", "episode", "motor_transport_economy", 0.0],
        ],
    }


def measure_energetics_rule():
    input_energy = Max(L(0.0), P0("outcome", "input_energy_joules"))
    recovered_energy = Max(
        L(0.0),
        P0("outcome", "recovered_energy_joules"),
    )
    cumulative_input = Plus(
        P0("state", "input_energy_joules"),
        input_energy,
    )
    cumulative_recovered = Plus(
        P0("state", "recovered_energy_joules"),
        recovered_energy,
    )
    cumulative_absorbed = Plus(
        P0("state", "absorbed_energy_joules"),
        Max(L(0.0), P0("outcome", "absorbed_energy_joules")),
    )
    net_energy = Max(
        L(0.0),
        Minus(cumulative_input, cumulative_recovered),
    )
    dx = Minus(P0("outcome", "post_x"), P0("outcome", "pre_x"))
    dy = Minus(P0("outcome", "post_y"), P0("outcome", "pre_y"))
    dz = Minus(P0("outcome", "post_z"), P0("outcome", "pre_z"))
    receipt_distance = Sqrt(Plus(
        Times(dx, dx),
        Times(dy, dy),
        Times(dz, dz),
    ))
    path_length = Plus(
        P0("state", "transport_path_length_metres"),
        receipt_distance,
    )
    transport_work_scale = Times(
        P0("episode", "body_mass"),
        P0("episode", "gravity_acceleration"),
        path_length,
    )
    cost_of_transport = If(
        And(Gt(path_length, L(0.0)), Gt(net_energy, L(0.0))),
        Div(net_energy, transport_work_scale),
        L(0.0),
    )
    transport_economy = If(
        Gt(net_energy, L(0.0)),
        Div(transport_work_scale, net_energy),
        L(0.0),
    )
    remaining_energy = If(
        Gt(P0("episode", "state_available_energy_joules"), L(0.0)),
        Max(
            L(0.0),
            Minus(
                P0("episode", "state_available_energy_joules"),
                net_energy,
            ),
        ),
        L(0.0),
    )
    power_headroom = If(
        Gt(P0("episode", "state_maximum_power_watts"), L(0.0)),
        Max(
            L(0.0),
            Minus(
                P0("episode", "state_maximum_power_watts"),
                Max(
                    P0("state", "peak_power_watts"),
                    P0("outcome", "peak_power_watts"),
                ),
            ),
        ),
        L(0.0),
    )
    cumulative_thermal = Plus(
        P0("state", "thermal_load_joules"),
        Max(L(0.0), P0("outcome", "thermal_load_joules")),
    )
    thermal_headroom = If(
        Gt(P0("episode", "state_thermal_capacity_joules"), L(0.0)),
        Max(
            L(0.0),
            Minus(
                P0("episode", "state_thermal_capacity_joules"),
                cumulative_thermal,
            ),
        ),
        L(0.0),
    )
    return {
        "name": "emp_measure_thermodynamic_motor_economy",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Integrate measured actuator work, regeneration, thermal "
        "load and peak power in graph state. Dimensionless transport cost is "
        "derived from body weight and receipt-grounded path length.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            [
                "episode",
                "has_embodied_energetic_state",
                "state",
            ],
            ["episode", "has_embodied_motor_receipt", "outcome"],
        ],
        "where": And(
            Eq(
                P0("outcome", "energetic_window_seq"),
                P0("state", "energetic_window_seq"),
            ),
            Gt(
                P0("outcome", "motor_epoch"),
                P0("state", "measured_motor_epoch"),
            ),
        ),
        "effects": [
            ["set_attr", "state", "net_energy_joules", T(net_energy)],
            ["set_attr", "state", "thermal_headroom_joules", T(
                thermal_headroom
            )],
            ["set_attr", "state", "thermal_load_joules", T(
                cumulative_thermal
            )],
            ["set_attr", "state", "peak_power_watts", T(Max(
                P0("state", "peak_power_watts"),
                P0("outcome", "peak_power_watts"),
            ))],
            ["set_attr", "state", "cost_of_transport", T(
                cost_of_transport
            )],
            ["set_attr", "state", "transport_economy", T(
                transport_economy
            )],
            ["set_attr", "state", "remaining_energy_joules", T(
                remaining_energy
            )],
            ["set_attr", "state", "power_headroom_watts", T(
                power_headroom
            )],
            ["set_attr", "episode", "motor_input_energy_joules", T(
                cumulative_input
            )],
            ["set_attr", "episode", "motor_net_energy_joules", T(
                net_energy
            )],
            ["set_attr", "episode", "motor_peak_power_watts", T(Max(
                P0("state", "peak_power_watts"),
                P0("outcome", "peak_power_watts"),
            ))],
            ["set_attr", "episode", "motor_cost_of_transport", T(
                cost_of_transport
            )],
            ["set_attr", "episode", "motor_transport_economy", T(
                transport_economy
            )],
            [
                "set_attr",
                "episode",
                "motor_transport_path_length_metres",
                T(path_length),
            ],
            [
                "set_attr",
                "state",
                "transport_path_length_metres",
                T(path_length),
            ],
            ["set_attr", "state", "input_energy_joules", T(
                cumulative_input
            )],
            ["set_attr", "state", "absorbed_energy_joules", T(
                cumulative_absorbed
            )],
            ["set_attr", "state", "recovered_energy_joules", T(
                cumulative_recovered
            )],
            ["set_attr", "state", "measured_world_step_index", T(
                P0("outcome", "world_step_index")
            )],
            ["set_attr", "state", "measured_motor_epoch", T(
                P0("outcome", "motor_epoch")
            )],
        ],
    }


def _coupling_regime_from_contact_force():
    """CONTACT-COUPLED vs CONTACT-FREE, from LOAD -- not from a point count.

    `pre_contact_count` counts CONTACT MANIFOLD POINTS. Measured live on the
    humanoid: 8.0 on 224 of 224 transitions, because a flat foot yields ~4 points
    and it is positive whenever any geometry touches anything. Consequence,
    measured: ZERO contact-free capability nodes had ever been opened, on any
    body, ever -- the contact-free half of this representation was
    uninstantiated, so `contact_free_evidence` was 0.0 everywhere and the
    label-free learner only ever learned the grounded case.

    The world adapters now publish `contact_force_newtons`, an instantaneous sum
    of normal-force magnitudes over every contact point involving the body.
    Measured: a drone in flight reads 0.0; a humanoid lifted clear reads 0.0 with
    8 -> 0 contacts; ground bodies read body weight within a few percent.

    PRESENCE-GUARDED, and this is load-bearing. `P0` is attr-or-ZERO and cannot
    tell an absent channel from a measured zero. A body whose driver does not yet
    write the force -- the helicopter today, whose `_outcome_attrs` carries no
    contact fields at all -- would read 0.0 and be classified PERMANENTLY
    CONTACT-FREE: the exact mirror of the bug being fixed, and worse, because it
    would corrupt a body that is currently merely stuck rather than inverted.
    So the force is used only where it is DECLARED, and anything else keeps the
    old count-based reading unchanged.
    """
    return If(
        Not(Eq(A("outcome", "pre_contact_force_newtons"), L(None))),
        If(Gt(P0("outcome", "pre_contact_force_newtons"), L(0.0)), L(1.0), L(0.0)),
        If(Gt(P0("outcome", "pre_contact_count"), L(0.0)), L(1.0), L(0.0)),
    )


def open_effector_capability_rule():
    capabilities = Neighbours("model", "has_embodied_effector_capability")
    coupling_regime = _coupling_regime_from_contact_force()
    vertical_regime = If(
        Gt(P0("outcome", "pre_vz"), L(0.0)),
        L(1.0),
        If(Lt(P0("outcome", "pre_vz"), L(0.0)), L(-1.0), L(0.0)),
    )
    matching_capabilities = Filter(
        capabilities,
        "existing_capability",
        And(
            Eq(
                P0("existing_capability", "coupling_regime"),
                coupling_regime,
            ),
            Eq(
                P0("existing_capability", "vertical_regime"),
                vertical_regime,
            ),
        ),
    )
    return {
        "name": "emp_open_receipt_grounded_effector_capability",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "match": [
            ["model", "has_embodied_motor_receipt", "outcome"],
        ],
        "where": Eq(Count(matching_capabilities), L(0.0)),
        "effects": [
            ["add_node", "capability", "EmbodiedEffectorCapability", {
                "experience_count": 0.0,
                "coupling_regime": T(coupling_regime),
                "vertical_regime": T(vertical_regime),
                "translation_per_joule": 0.0,
                "vertical_per_joule": 0.0,
                "mean_pre_speed": 0.0,
                "flow_speed_variance_sum": 0.0,
                "flow_effect_covariance_sum": 0.0,
                "flow_conditioned_authority_gain": 0.0,
                "contact_coupled_evidence": 0.0,
                "contact_free_evidence": 0.0,
                "peak_power_watts": 0.0,
                "last_world_step_index": -1.0,
            }],
            [
                "add_edge",
                "model",
                "has_embodied_effector_capability",
                "capability",
            ],
        ],
    }


def learn_effector_capability_rule():
    dx = Minus(P0("outcome", "post_x"), P0("outcome", "pre_x"))
    dy = Minus(P0("outcome", "post_y"), P0("outcome", "pre_y"))
    dz = Minus(P0("outcome", "post_z"), P0("outcome", "pre_z"))
    translation = Sqrt(Plus(
        Times(dx, dx),
        Times(dy, dy),
        Times(dz, dz),
    ))
    energy = P0("outcome", "input_energy_joules")
    translation_per_joule = If(
        Gt(energy, L(0.0)),
        Div(translation, energy),
        L(0.0),
    )
    vertical_per_joule = If(
        Gt(energy, L(0.0)),
        Div(Abs(dz), energy),
        L(0.0),
    )
    pre_speed = Sqrt(Plus(
        Times(P0("outcome", "pre_vx"), P0("outcome", "pre_vx")),
        Times(P0("outcome", "pre_vy"), P0("outcome", "pre_vy")),
        Times(P0("outcome", "pre_vz"), P0("outcome", "pre_vz")),
    ))
    count = Plus(P0("capability", "experience_count"), L(1.0))
    speed_delta = Minus(
        pre_speed,
        P0("capability", "mean_pre_speed"),
    )
    next_mean_speed = Plus(
        P0("capability", "mean_pre_speed"),
        Div(speed_delta, count),
    )
    next_mean_effect = Plus(
        P0("capability", "translation_per_joule"),
        Div(
            Minus(
                translation_per_joule,
                P0("capability", "translation_per_joule"),
            ),
            count,
        ),
    )
    next_speed_variance = Plus(
        P0("capability", "flow_speed_variance_sum"),
        Times(
            speed_delta,
            Minus(pre_speed, next_mean_speed),
        ),
    )
    next_effect_covariance = Plus(
        P0("capability", "flow_effect_covariance_sum"),
        Times(
            speed_delta,
            Minus(translation_per_joule, next_mean_effect),
        ),
    )
    flow_gain = If(
        Gt(next_speed_variance, L(0.0)),
        Div(next_effect_covariance, next_speed_variance),
        L(0.0),
    )
    coupling_regime = _coupling_regime_from_contact_force()
    vertical_regime = If(
        Gt(P0("outcome", "pre_vz"), L(0.0)),
        L(1.0),
        If(Lt(P0("outcome", "pre_vz"), L(0.0)), L(-1.0), L(0.0)),
    )

    def mean(key, observation):
        return Plus(
            P0("capability", key),
            Div(
                Minus(observation, P0("capability", key)),
                count,
            ),
        )

    return {
        "name": "emp_learn_opaque_effector_causal_capability",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Learn energy-normalized causal roles without assuming "
        "whether an opaque effector is a limb, wheel, rotor, thruster or "
        "aerodynamic surface.",
        "match": [
            ["model", "has_embodied_motor_receipt", "outcome"],
            [
                "model",
                "has_embodied_effector_capability",
                "capability",
            ],
        ],
        "where": And(
            Eq(P0("capability", "coupling_regime"), coupling_regime),
            Eq(P0("capability", "vertical_regime"), vertical_regime),
            Gt(
                P0("outcome", "world_step_index"),
                P0("capability", "last_world_step_index"),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "capability",
                "flow_conditioned_authority_gain",
                T(flow_gain),
            ],
            [
                "set_attr",
                "capability",
                "flow_speed_variance_sum",
                T(next_speed_variance),
            ],
            [
                "set_attr",
                "capability",
                "flow_effect_covariance_sum",
                T(next_effect_covariance),
            ],
            ["set_attr", "capability", "mean_pre_speed", T(
                next_mean_speed
            )],
            ["set_attr", "capability", "translation_per_joule", T(
                next_mean_effect
            )],
            ["set_attr", "capability", "vertical_per_joule", T(
                mean("vertical_per_joule", vertical_per_joule)
            )],
            ["set_attr", "capability", "contact_coupled_evidence", T(
                Plus(
                    P0("capability", "contact_coupled_evidence"),
                    If(
                        Gt(P0("outcome", "contact_count"), L(0.0)),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "capability", "contact_free_evidence", T(
                Plus(
                    P0("capability", "contact_free_evidence"),
                    If(
                        Gt(P0("outcome", "contact_count"), L(0.0)),
                        L(0.0),
                        L(1.0),
                    ),
                )
            )],
            ["set_attr", "capability", "peak_power_watts", T(Max(
                P0("capability", "peak_power_watts"),
                P0("outcome", "peak_power_watts"),
            ))],
            ["set_attr", "capability", "experience_count", T(count)],
            ["set_attr", "capability", "last_world_step_index", T(
                P0("outcome", "world_step_index")
            )],
        ],
    }


def open_effector_assembly_hypothesis_rule():
    assemblies = Neighbours(
        "relation",
        "grounds_embodied_effector_assembly",
    )
    return {
        "name": "emp_open_name_free_effector_assembly_hypothesis",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Turn a mechanically published pair relation into a graph "
        "hypothesis. The boundary supplies path, channel and hard-coupling "
        "facts; receipts alone decide cooperation, redundancy or interference.",
        "match": [
            ["episode", "has_embodied_effector_topology", "topology"],
            ["topology", "has_embodied_effector_relation", "relation"],
            ["relation", "has_embodied_effector_source", "source"],
            ["relation", "has_embodied_effector_target", "target"],
        ],
        "where": And(
            Eq(Count(assemblies), L(0.0)),
            Eq(P0("topology", "learning_enabled"), L(1.0)),
            Eq(P0("source", "tonic_default"), L(0.0)),
            Eq(P0("target", "tonic_default"), L(0.0)),
        ),
        "effects": [
            ["add_node", "assembly", "EmbodiedEffectorAssembly", {
                "status": T(If(
                    Eq(P0("relation", "same_command_channel"), L(1.0)),
                    L("hard_conflict"),
                    If(
                        Eq(
                            P0("relation", "declared_hard_coupling"),
                            L(1.0),
                        ),
                        L("hard_coupled"),
                        L("candidate"),
                    ),
                )),
                "member_count": 2.0,
                "experience_count": 0.0,
                "cooperation_evidence": 0.0,
                "interference_evidence": 0.0,
                "redundancy_evidence": 0.0,
                "common_drive_evidence": 0.0,
                "mean_interaction_residual": 0.0,
                "mean_task_progress": 0.0,
                "mean_energy_joules": 0.0,
                "mean_stability_cost": 0.0,
                "last_receipt_sequence": -1.0,
                "last_support_phase": -1.0,
                "mechanical_path_length": T(
                    P0("relation", "mechanical_path_length")
                ),
                "mechanical_path_known": T(
                    P0("relation", "mechanical_path_known")
                ),
                "declared_hard_coupling": T(
                    P0("relation", "declared_hard_coupling")
                ),
                "same_command_channel": T(
                    P0("relation", "same_command_channel")
                ),
                "provenance_kind": "receipt_grounded_effector_assembly",
            }],
            [
                "add_edge",
                "relation",
                "grounds_embodied_effector_assembly",
                "assembly",
            ],
            [
                "add_edge",
                "assembly",
                "includes_embodied_effector",
                "source",
            ],
            [
                "add_edge",
                "assembly",
                "includes_embodied_effector",
                "target",
            ],
            [
                "add_edge",
                "episode",
                "has_embodied_effector_assembly",
                "assembly",
            ],
        ],
    }


def bridge_humanoid_program_members_rule():
    credited = Neighbours("trial", "uses_embodied_effector_model")
    return {
        "name": "emp_bridge_humanoid_program_members_to_generic_effectors",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Expose every graph-authored program member to the generic "
        "assembly learner; this is relational normalization, not selection.",
        "match": [
            ["trial", "enacts_humanoid_motor_program", "program"],
            [
                "program",
                "includes_humanoid_phase_action_model",
                "phase_model",
            ],
            [
                "phase_model",
                "generalizes_humanoid_action_model",
                "model",
            ],
            ["model", "models_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Not(Exists(
                credited,
                "credited_model",
                Eq(V("credited_model"), V("model")),
            )),
        ),
        "effects": [[
            "add_edge",
            "trial",
            "uses_embodied_effector_model",
            "model",
        ]],
    }


def bridge_generic_program_members_rule():
    credited = Neighbours("trial", "uses_embodied_effector_model")
    return {
        "name": "emp_bridge_generic_program_members_to_effectors",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Normalize arbitrary body-plan motor-program members "
        "into the shared effector assembly learner.",
        "match": [
            ["trial", "enacts_embodied_motor_program", "program"],
            ["program", "includes_embodied_effector_model", "model"],
            ["model", "models_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Not(Exists(
                credited,
                "credited_model",
                Eq(V("credited_model"), V("model")),
            )),
        ),
        "effects": [[
            "add_edge",
            "trial",
            "uses_embodied_effector_model",
            "model",
        ]],
    }


def bridge_domain_trial_model_rule(model_edge: str, name: str):
    credited = Neighbours("trial", "uses_embodied_effector_model")
    return {
        "name": name,
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Normalize an opaque domain model edge; one command model "
        "may mechanically address several physical effectors.",
        "match": [
            ["trial", model_edge, "model"],
            ["model", "models_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Not(Exists(
                credited,
                "credited_model",
                Eq(V("credited_model"), V("model")),
            )),
        ),
        "effects": [[
            "add_edge",
            "trial",
            "uses_embodied_effector_model",
            "model",
        ]],
    }


def bind_compound_trial_to_effector_assembly_rule():
    enacted = Neighbours("trial", "enacts_embodied_effector_assembly")
    return {
        "name": "emp_bind_compound_trial_to_effector_assembly",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Bind a compound intervention to every pair hypothesis "
        "whose two opaque members it actually enacted.",
        "match": [
            ["trial", "uses_embodied_effector_model", "source_model"],
            ["trial", "uses_embodied_effector_model", "target_model"],
            ["source_model", "models_embodied_effector", "source"],
            ["target_model", "models_embodied_effector", "target"],
            ["assembly", "includes_embodied_effector", "source"],
            ["assembly", "includes_embodied_effector", "target"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Not(Eq(V("source"), V("target"))),
            Eq(P0("assembly", "same_command_channel"), L(0.0)),
            Not(Exists(
                enacted,
                "known_assembly",
                Eq(V("known_assembly"), V("assembly")),
            )),
        ),
        "effects": [[
            "add_edge",
            "trial",
            "enacts_embodied_effector_assembly",
            "assembly",
        ]],
    }


def bind_vector_trial_to_effector_assembly_rule():
    enacted = Neighbours("trial", "enacts_embodied_effector_assembly")
    return {
        "name": "emp_bind_vector_command_trial_to_effector_assembly",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Recognize coactivation hidden inside one precombined "
        "opaque command vector.",
        "match": [
            ["trial", "uses_embodied_effector_model", "model"],
            ["model", "models_embodied_effector", "source"],
            ["model", "models_embodied_effector", "target"],
            ["assembly", "includes_embodied_effector", "source"],
            ["assembly", "includes_embodied_effector", "target"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Not(Eq(V("source"), V("target"))),
            Eq(P0("assembly", "same_command_channel"), L(0.0)),
            Not(Exists(
                enacted,
                "known_assembly",
                Eq(V("known_assembly"), V("assembly")),
            )),
        ),
        "effects": [[
            "add_edge",
            "trial",
            "enacts_embodied_effector_assembly",
            "assembly",
        ]],
    }


def learn_effector_assembly_rule():
    # ``task_progress`` is the shared causal receipt scalar. Domain adapters
    # project their goal-relative displacement onto it mechanically, so the
    # assembly learner never needs anatomy- or vehicle-specific coordinates.
    observed_progress = P0("outcome", "task_progress")
    predicted_progress = P0("trial", "predicted_task_progress")
    residual = Minus(observed_progress, predicted_progress)
    count = Plus(P0("assembly", "experience_count"), L(1.0))
    next_cooperation = Plus(
        P0("assembly", "cooperation_evidence"),
        Max(L(0.0), residual),
    )
    next_interference = Plus(
        P0("assembly", "interference_evidence"),
        Max(L(0.0), Minus(L(0.0), residual)),
    )
    predicted_magnitude = Abs(predicted_progress)
    next_redundancy = Plus(
        P0("assembly", "redundancy_evidence"),
        If(
            Lt(Abs(residual), predicted_magnitude),
            Minus(predicted_magnitude, Abs(residual)),
            L(0.0),
        ),
    )

    def mean(key, observed):
        return Plus(
            P0("assembly", key),
            Div(Minus(observed, P0("assembly", key)), count),
        )

    learned_status = If(
        Eq(P0("assembly", "declared_hard_coupling"), L(1.0)),
        L("hard_coupled"),
        If(
            Gt(next_interference, next_cooperation),
            L("fractionating"),
            If(
                Gt(next_cooperation, next_interference),
                L("cooperative"),
                L("compatible"),
            ),
        ),
    )
    return {
        "name": "emp_learn_effector_assembly_from_compound_receipt",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Accumulate continuous evidence for cooperation, "
        "interference, redundancy and common drive. Broad interfering "
        "assemblies reopen analysis by synthesis instead of becoming faults.",
        "match": [
            ["trial", "enacts_embodied_effector_assembly", "assembly"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Gt(
                P0("outcome", "world_step_index"),
                P0("assembly", "last_receipt_sequence"),
            ),
        ),
        "effects": [
            ["set_attr", "assembly", "status", T(learned_status)],
            ["set_attr", "assembly", "cooperation_evidence", T(
                next_cooperation
            )],
            ["set_attr", "assembly", "interference_evidence", T(
                next_interference
            )],
            ["set_attr", "assembly", "redundancy_evidence", T(
                next_redundancy
            )],
            ["set_attr", "assembly", "common_drive_evidence", T(
                Plus(
                    P0("assembly", "common_drive_evidence"),
                    Div(L(1.0), P0("assembly", "member_count")),
                )
            )],
            ["set_attr", "assembly", "mean_interaction_residual", T(
                mean("mean_interaction_residual", residual)
            )],
            ["set_attr", "assembly", "mean_task_progress", T(
                mean("mean_task_progress", observed_progress)
            )],
            ["set_attr", "assembly", "mean_energy_joules", T(
                mean("mean_energy_joules", P0("outcome", "input_energy_joules"))
            )],
            ["set_attr", "assembly", "last_support_phase", T(
                P0("trial", "support_phase")
            )],
            ["set_attr", "assembly", "experience_count", T(count)],
            ["set_attr", "assembly", "last_receipt_sequence", T(
                P0("outcome", "world_step_index")
            )],
        ],
    }


def reset_locomotor_state_rule():
    return {
        "name": "emp_reset_locomotor_continuity_on_episode_boundary",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Consume an externally observed body/episode boundary "
        "while retaining learned priors and motor models.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            [
                "episode",
                "has_embodied_locomotor_state",
                "state",
            ],
        ],
        "where": Gt(
            P0("episode", "locomotor_prior_reset_seq"),
            P0("state", "reset_processed_seq"),
        ),
        "effects": [
            ["set_attr", "state", "initialized", 0.0],
            ["set_attr", "state", "measured_state_seq", -1.0],
            ["set_attr", "state", "path_length", 0.0],
            ["set_attr", "state", "last_directed_step", 0.0],
            ["set_attr", "state", "forward_reversal_count", 0.0],
            ["set_attr", "state", "support_switch_count", 0.0],
            ["set_attr", "state", "locomotor_cycle_count", 0.0],
            ["set_attr", "state", "last_support_phase", 0.0],
            ["set_attr", "state", "last_support_switch_request_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "state", "mean_support_phase_actions", 0.0],
            ["set_attr", "state", "reset_processed_seq", T(
                P0("episode", "locomotor_prior_reset_seq")
            )],
        ],
    }


def measure_locomotor_continuity_rule():
    first = Eq(P0("state", "initialized"), L(0.0))
    dx = Minus(P0("episode", "state_x"), P0("state", "previous_x"))
    dy = Minus(P0("episode", "state_y"), P0("state", "previous_y"))
    step_length = Sqrt(Plus(Times(dx, dx), Times(dy, dy)))
    directed_step = Times(P0("episode", "heading_x"), dx)
    reversal = And(
        Not(first),
        Lt(
            Times(directed_step, P0("state", "last_directed_step")),
            L(0.0),
        ),
    )
    support_0 = Gt(P0("episode", "state_support_0_force"), L(0.0))
    support_1 = Gt(P0("episode", "state_support_1_force"), L(0.0))
    unilateral = If(
        And(support_0, Not(support_1)),
        L(1.0),
        If(And(support_1, Not(support_0)), L(2.0), L(0.0)),
    )
    observed_support = If(
        Gt(unilateral, L(0.0)),
        unilateral,
        P0("state", "last_support_phase"),
    )
    support_switched = And(
        Not(first),
        Gt(unilateral, L(0.0)),
        Gt(P0("state", "last_support_phase"), L(0.0)),
        Not(Eq(unilateral, P0("state", "last_support_phase"))),
    )
    next_switch_count = Plus(
        P0("state", "support_switch_count"),
        If(support_switched, L(1.0), L(0.0)),
    )
    phase_duration = Minus(
        P0("episode", "request_seq"),
        P0("state", "last_support_switch_request_seq"),
    )
    return {
        "name": "emp_measure_locomotor_continuity_from_receipts",
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "comment": "Track path efficiency, reversal and contact-cycle "
        "evidence from standardized raw receipts. These are graph state, not "
        "host-side gait labels.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            [
                "episode",
                "has_embodied_locomotor_state",
                "state",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(P0("episode", "state_is_receipt"), L(1.0)),
            Gt(
                P0("episode", "state_seq"),
                P0("state", "measured_state_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "state", "start_x", T(
                If(first, P0("episode", "state_x"), P0("state", "start_x"))
            )],
            ["set_attr", "state", "start_y", T(
                If(first, P0("episode", "state_y"), P0("state", "start_y"))
            )],
            ["set_attr", "state", "path_length", T(
                If(
                    first,
                    L(0.0),
                    Plus(P0("state", "path_length"), step_length),
                )
            )],
            ["set_attr", "state", "forward_reversal_count", T(
                Plus(
                    P0("state", "forward_reversal_count"),
                    If(reversal, L(1.0), L(0.0)),
                )
            )],
            ["set_attr", "state", "support_switch_count", T(
                next_switch_count
            )],
            ["set_attr", "state", "locomotor_cycle_count", T(
                IDiv(next_switch_count, L(2.0))
            )],
            ["set_attr", "state", "mean_support_phase_actions", T(
                If(
                    support_switched,
                    Plus(
                        P0("state", "mean_support_phase_actions"),
                        Div(
                            Minus(
                                phase_duration,
                                P0("state", "mean_support_phase_actions"),
                            ),
                            next_switch_count,
                        ),
                    ),
                    P0("state", "mean_support_phase_actions"),
                )
            )],
            ["set_attr", "state", "last_support_switch_request_seq", T(
                If(
                    support_switched,
                    P0("episode", "request_seq"),
                    P0("state", "last_support_switch_request_seq"),
                )
            )],
            ["set_attr", "state", "last_support_phase", T(observed_support)],
            ["set_attr", "state", "last_directed_step", T(
                If(first, L(0.0), directed_step)
            )],
            ["set_attr", "state", "previous_x", T(P0("episode", "state_x"))],
            ["set_attr", "state", "previous_y", T(P0("episode", "state_y"))],
            ["set_attr", "state", "measured_state_seq", T(
                P0("episode", "state_seq")
            )],
            ["set_attr", "state", "initialized", 1.0],
            ["set_attr", "episode", "locomotor_path_length", T(
                If(
                    first,
                    L(0.0),
                    Plus(P0("state", "path_length"), step_length),
                )
            )],
            [
                "set_attr",
                "episode",
                "locomotor_forward_reversal_count",
                T(Plus(
                    P0("state", "forward_reversal_count"),
                    If(reversal, L(1.0), L(0.0)),
                )),
            ],
            ["set_attr", "episode", "locomotor_cycle_count", T(
                IDiv(next_switch_count, L(2.0))
            )],
            ["set_attr", "episode", "last_directed_step", T(
                If(first, L(0.0), directed_step)
            )],
        ],
    }


MOTOR_PRIOR_SOFT_REALTIME_RULES = {
    "emp_open_receipt_grounded_effector_capability",
    "emp_measure_locomotor_continuity_from_receipts",
    "emp_measure_thermodynamic_motor_economy",
    "emp_learn_opaque_effector_causal_capability",
}


def apply_biological_schedule(manifest_dict):
    """Keep causal learning off the immediate motor-release sheet."""
    authored = {rule["name"] for rule in manifest_dict["rules"]}
    missing = MOTOR_PRIOR_SOFT_REALTIME_RULES - authored
    if missing:
        raise ValueError(f"scheduled motor-prior rules are absent: {sorted(missing)}")
    for rule in manifest_dict["rules"]:
        if rule["name"] in MOTOR_PRIOR_SOFT_REALTIME_RULES:
            rule["area"] = "adaptive_learning"
            rule["latency_class"] = "soft_realtime"
    return manifest_dict


def manifest():
    nodes = [
        {
            "local_id": ordinal,
            "type": "EmbodiedMotorPrior",
            "attrs": {
                "kind": kind,
                "description": description,
                "defeasible": 1.0,
                "confidence": 0.5,
                "evidence_count": 0.0,
            },
        }
        for ordinal, (kind, description) in enumerate(PRIOR_KINDS, 1)
    ]
    return apply_biological_schedule({
        "id": "embodied_motor_priors",
        "version": "1.1.0",
        "depends_on": [
            "embodied_pareto_profile",
            "embodied_sensorimotor_core",
            "motor_decision_collapse",
        ],
        "area": "embodied_motor_priors",
        "latency_class": "hard_realtime",
        "description": "Minimal shared priors for relational embodiment, "
        "viability, support, action composition and temporal motor chunks, "
        "with receipt-grounded causal plasticity on the adaptive sheet.",
        "nodes": nodes,
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_motor_prior",
                "tgt": {"local": node["local_id"]},
                "attrs": {},
            }
            for node in nodes
        ],
        "productions": [
            {
                "provenance": "embodied_motor_priors:agent_prior",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_motor_prior",
                "tgt": {"type": "EmbodiedMotorPrior", "var": "prior"},
            },
            {
                "provenance": "embodied_motor_priors:agent_episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_motor_episode",
                "tgt": {"type": "EmbodiedMotorEpisode", "var": "episode"},
            },
            {
                "provenance": "embodied_motor_priors:episode_prior",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "uses_embodied_motor_prior",
                "tgt": {"type": "EmbodiedMotorPrior", "var": "prior"},
            },
            {
                "provenance": "embodied_motor_priors:locomotor_state",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "has_embodied_locomotor_state",
                "tgt": {
                    "type": "EmbodiedLocomotorState",
                    "var": "state",
                },
            },
            {
                "provenance": "embodied_motor_priors:energetic_state",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "has_embodied_energetic_state",
                "tgt": {
                    "type": "EmbodiedEnergeticState",
                    "var": "state",
                },
            },
            {
                "provenance": "embodied_motor_priors:effector_capability",
                "src": {"type": "Unknown", "var": "model"},
                "edge_type": "has_embodied_effector_capability",
                "tgt": {
                    "type": "EmbodiedEffectorCapability",
                    "var": "capability",
                },
            },
            {
                "provenance": "embodied_motor_priors:episode_topology",
                "src": {"type": "Unknown", "var": "episode"},
                "edge_type": "has_embodied_effector_topology",
                "tgt": {
                    "type": "EmbodiedEffectorTopology",
                    "var": "topology",
                },
            },
            {
                "provenance": "embodied_motor_priors:topology_effector",
                "src": {
                    "type": "EmbodiedEffectorTopology",
                    "var": "topology",
                },
                "edge_type": "has_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "embodied_motor_priors:topology_relation",
                "src": {
                    "type": "EmbodiedEffectorTopology",
                    "var": "topology",
                },
                "edge_type": "has_embodied_effector_relation",
                "tgt": {
                    "type": "EmbodiedEffectorRelation",
                    "var": "relation",
                },
            },
            {
                "provenance": "embodied_motor_priors:relation_source",
                "src": {
                    "type": "EmbodiedEffectorRelation",
                    "var": "relation",
                },
                "edge_type": "has_embodied_effector_source",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "embodied_motor_priors:relation_target",
                "src": {
                    "type": "EmbodiedEffectorRelation",
                    "var": "relation",
                },
                "edge_type": "has_embodied_effector_target",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "embodied_motor_priors:relation_assembly",
                "src": {
                    "type": "EmbodiedEffectorRelation",
                    "var": "relation",
                },
                "edge_type": "grounds_embodied_effector_assembly",
                "tgt": {
                    "type": "EmbodiedEffectorAssembly",
                    "var": "assembly",
                },
            },
            {
                "provenance": "embodied_motor_priors:assembly_member",
                "src": {
                    "type": "EmbodiedEffectorAssembly",
                    "var": "assembly",
                },
                "edge_type": "includes_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "embodied_motor_priors:model_effector",
                "src": {"type": "Unknown", "var": "model"},
                "edge_type": "models_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "embodied_motor_priors:trial_model",
                "src": {"type": "Unknown", "var": "trial"},
                "edge_type": "uses_embodied_effector_model",
                "tgt": {"type": "Unknown", "var": "model"},
            },
            {
                "provenance": "embodied_motor_priors:trial_assembly",
                "src": {"type": "Unknown", "var": "trial"},
                "edge_type": "enacts_embodied_effector_assembly",
                "tgt": {
                    "type": "EmbodiedEffectorAssembly",
                    "var": "assembly",
                },
            },
            {
                "provenance": "embodied_motor_priors:trial_receipt",
                "src": {"type": "Unknown", "var": "trial"},
                "edge_type": "has_embodied_motor_receipt",
                "tgt": {"type": "Unknown", "var": "outcome"},
            },
        ],
        "rules": [
            recognize_episode_rule(
                "has_humanoid_episode",
                "emp_recognize_humanoid_motor_episode",
            ),
            recognize_episode_rule(
                "has_embodied_episode",
                "emp_recognize_ground_motor_episode",
            ),
            recognize_episode_rule(
                "has_aerial_episode",
                "emp_recognize_aerial_motor_episode",
            ),
            recognize_episode_rule(
                "has_helicopter_episode",
                "emp_recognize_helicopter_motor_episode",
            ),
            bind_prior_rule(),
            recognize_receipt_rule(
                "has_humanoid_motor_trial",
                "uses_humanoid_phase_action_model",
                "has_humanoid_transition",
                "emp_recognize_humanoid_motor_receipt",
            ),
            recognize_receipt_rule(
                "has_humanoid_motor_trial",
                "uses_humanoid_action_model",
                "has_humanoid_transition",
                "emp_recognize_humanoid_primitive_motor_receipt",
                unless_model_edge="uses_humanoid_phase_action_model",
            ),
            recognize_receipt_rule(
                "has_motor_trial",
                "uses_action_model",
                "has_transition_outcome",
                "emp_recognize_ground_motor_receipt",
            ),
            recognize_receipt_rule(
                "has_aerial_motor_trial",
                "uses_aerial_action_model",
                "has_aerial_transition_outcome",
                "emp_recognize_aerial_motor_receipt",
            ),
            open_locomotor_state_rule(),
            open_energetic_state_rule(),
            open_effector_capability_rule(),
            open_effector_assembly_hypothesis_rule(),
            bridge_humanoid_program_members_rule(),
            bridge_generic_program_members_rule(),
            bridge_domain_trial_model_rule(
                "uses_action_model",
                "emp_bridge_ground_trial_model_to_effectors",
            ),
            bridge_domain_trial_model_rule(
                "uses_aerial_action_model",
                "emp_bridge_aerial_trial_model_to_effectors",
            ),
            bind_compound_trial_to_effector_assembly_rule(),
            bind_vector_trial_to_effector_assembly_rule(),
            reset_locomotor_state_rule(),
            reset_energetic_state_rule(),
            measure_locomotor_continuity_rule(),
            measure_energetics_rule(),
            learn_effector_capability_rule(),
            learn_effector_assembly_rule(),
        ],
    })


def main() -> int:
    output = ROOT / "seeds" / "embodied_motor_priors.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
