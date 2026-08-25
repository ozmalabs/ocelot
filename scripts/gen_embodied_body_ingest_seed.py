#!/usr/bin/env python3
"""Generate graph recognition of a mechanically attached embodied world.

The PyBullet boundary publishes only observed connection, morphology, opaque
actuator and world-capability facts.  This seed is deliberately the other half
of that boundary: it decides in the graph when those facts constitute a
situated humanoid learning environment.  It never names an actuator command,
motor program, goal, duration, or reset scenario.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def N(name, edge):
    return {"type": "Neighbours", "node": V(name), "edge_type": edge}
def Exists(source, var, predicate):
    return {"type": "Exists", "source": source, "var_name": var,
            "predicate": predicate}
def T(term): return {"__term__": term}
def Count(source): return {"type": "Count", "source": source}
def Filter(source, var, predicate): return {"type": "Filter", "source": source, "var_name": var, "predicate": predicate}


def absent(source, var="known"):
    return Not(Exists(source, var, L(True)))


def materialize_body_and_world_rule():
    return {
        "name": "ebi_recognize_connected_pybullet_humanoid_as_situated_body_and_world",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A raw connected body observation plus real reset, pose-fixture and trial capabilities is sufficient for the graph to recognize a situated learning environment. The adapter supplies facts; this rule supplies the category.",
        "match": [
            ["agent", "has_embodied_simulator_connection", "connection"],
            ["connection", "observes_embodied_raw_body", "raw_body"],
            ["connection", "has_embodied_world_capability", "reset"],
            ["connection", "has_embodied_world_capability", "pose_fixture"],
            ["connection", "has_embodied_world_capability", "physical_trial"],
        ],
        "where": And(
            Eq(A("connection", "status"), L("connected")),
            Eq(A("connection", "adapter_kind"), L("pybullet_humanoid")),
            Eq(A("raw_body", "observation_status"), L("observed")),
            Eq(A("raw_body", "body_class"), L("articulated_humanoid")),
            Eq(A("reset", "capability_kind"), L("reset_to_declared_fixture")),
            Eq(A("pose_fixture", "capability_kind"), L("declared_pose_fixture")),
            Eq(A("physical_trial", "capability_kind"), L("grounded_physical_trial")),
            Eq(A("reset", "available"), L(1)),
            Eq(A("pose_fixture", "available"), L(1)),
            Eq(A("physical_trial", "available"), L(1)),
            absent(N("connection", "materializes_embodied_body_schema")),
        ),
        "effects": [
            ["add_node", "body", "EmbodiedBodySchema", {
                "schema_status": "situated_observed",
                "body_identity": T(A("raw_body", "body_identity")),
                "body_class": T(A("raw_body", "body_class")),
                "joint_count": T(A("raw_body", "joint_count")),
                "actuator_count": T(A("raw_body", "actuator_count")),
                "support_channel_count": T(A("raw_body", "support_channel_count")),
                "morphology_epoch": T(A("raw_body", "observation_event_ordinal")),
                "observation_event_ordinal": T(A("raw_body", "observation_event_ordinal")),
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "world", "EmbodiedLearningWorld", {
                "world_status": "situated_connected",
                "world_identity": T(A("connection", "connection_identity")),
                "adapter_kind": T(A("connection", "adapter_kind")),
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "connection", "materializes_embodied_body_schema", "body"],
            ["add_edge", "connection", "materializes_embodied_learning_world", "world"],
            ["add_edge", "body", "grounded_in_embodied_raw_body", "raw_body"],
            ["add_edge", "world", "grounded_in_embodied_simulator_connection", "connection"],
            ["add_edge", "world", "has_embodied_reset_capability", "reset"],
            ["add_edge", "world", "has_embodied_pose_fixture_capability", "pose_fixture"],
            ["add_edge", "world", "has_embodied_physical_trial_capability", "physical_trial"],
        ],
    }


def materialize_motor_bootstrap_contract_rule():
    return {
        "name": "ebi_materialize_integer_motor_bootstrap_contract_from_raw_interface",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The body boundary declares only integer actuator and measurement interface limits. The graph materializes a reusable contract; it intentionally contains no trial duration, axis, sign or preferred program.",
        "match": [
            ["connection", "materializes_embodied_learning_world", "world"],
            ["connection", "has_embodied_raw_motor_interface", "raw_interface"],
        ],
        "where": And(
            Eq(A("raw_interface", "integer_native"), L(1)),
            absent(N("world", "has_embodied_motor_bootstrap_contract")),
        ),
        "effects": [
            ["add_node", "contract", "EmbodiedMotorBootstrapContract", {
                "minimum_actuation_frames": T(A("raw_interface", "minimum_actuation_frames")),
                "maximum_observation_horizon_frames": T(A("raw_interface", "maximum_observation_horizon_frames")),
                "simulator_weight_scale_units": T(A("raw_interface", "simulator_weight_scale_units")),
                "minimum_nonzero_weight_units": T(A("raw_interface", "minimum_nonzero_weight_units")),
                "displacement_units_per_metre": T(A("raw_interface", "displacement_units_per_metre")),
                "energy_units_per_joule": T(A("raw_interface", "energy_units_per_joule")),
                "load_units_per_newton": T(A("raw_interface", "load_units_per_newton")),
                "maximum_joint_force_units": T(A("raw_interface", "maximum_joint_force_units")),
                "maximum_actuator_bundle_members": T(A("raw_interface", "maximum_actuator_bundle_members")),
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "world", "has_embodied_motor_bootstrap_contract", "contract"],
            ["add_edge", "contract", "grounded_in_embodied_raw_motor_interface", "raw_interface"],
        ],
    }


def materialize_measurement_projection_affordance_rule():
    return {
        "name": "ebi_materialize_cartesian_measurement_projection_affordances",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Every declared Cartesian axis/sign projection becomes an equally available graph affordance. The rule carries no preference over direction or frame.",
        "match": [
            ["contract", "grounded_in_embodied_raw_motor_interface", "raw_interface"],
            ["raw_interface", "has_embodied_raw_measurement_projection", "raw_projection"],
        ],
        "where": And(
            Eq(A("raw_projection", "projection_kind"), L("cartesian_displacement")),
            Eq(A("raw_projection", "available"), L(1)),
            Not(Exists(
                N("contract", "has_embodied_measurement_projection"),
                "known_projection",
                And(
                    Eq(A("known_projection", "axis"), A("raw_projection", "axis")),
                    Eq(A("known_projection", "sign"), A("raw_projection", "sign")),
                ),
            )),
        ),
        "effects": [
            ["add_node", "projection", "EmbodiedMeasurementProjectionAffordance", {
                "projection_kind": "cartesian_displacement",
                "axis": T(A("raw_projection", "axis")),
                "sign": T(A("raw_projection", "sign")),
                "available": 1, "grounded": 1, "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "contract", "has_embodied_measurement_projection", "projection"],
            ["add_edge", "projection", "grounded_in_embodied_raw_measurement_projection", "raw_projection"],
        ],
    }


def bind_opaque_affordances_rule():
    return {
        "name": "ebi_bind_observed_opaque_actuator_affordances_to_situated_body",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Each body-side opaque actuator token is retained as an observed affordance. The rule does not rank, select or interpret any token.",
        "match": [
            ["connection", "materializes_embodied_body_schema", "body"],
            ["connection", "observes_embodied_raw_body", "raw_body"],
            ["raw_body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            Eq(A("affordance", "available"), L(1)),
            Not(Exists(
                N("body", "has_opaque_embodied_actuator_affordance"),
                "known_affordance", Eq(V("known_affordance"), V("affordance")),
            )),
        ),
        "effects": [
            ["add_edge", "body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
    }


def bind_mechanical_effector_topology_rule():
    return {
        "name": "ebi_bind_observed_direct_effector_topology_to_situated_body",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A mechanically observed direct link adjacency is retained as a local composition constraint. It does not make a motor program or select a command; receipt-grounded motor synthesis decides whether it is useful.",
        "match": [
            ["connection", "materializes_embodied_body_schema", "body"],
            ["connection", "observes_embodied_raw_body", "raw_body"],
            ["raw_body", "has_embodied_raw_effector_topology_relation", "relation"],
        ],
        "where": And(
            Eq(A("relation", "relation_kind"), L("directed_mechanical_link_adjacency")),
            Eq(A("relation", "mechanical_path_length"), L(1)),
            Eq(A("relation", "grounded"), L(1)),
            Eq(A("relation", "integer_native"), L(1)),
            Not(Exists(
                N("body", "has_opaque_embodied_effector_topology_relation"),
                "known_relation", Eq(V("known_relation"), V("relation")),
            )),
        ),
        "effects": [[
            "add_edge", "body", "has_opaque_embodied_effector_topology_relation", "relation",
        ]],
    }


def materialize_pose_affordance_rule():
    return {
        "name": "ebi_materialize_pose_affordance_from_observed_fixture_capability",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A declared pose fixture is a capability fact, not a hidden home pose. It permits an enabled situated pose-affordance but does not choose a fixture or reset scenario.",
        "match": [
            ["connection", "materializes_embodied_learning_world", "world"],
            ["connection", "has_embodied_world_capability", "pose_fixture"],
        ],
        "where": And(
            Eq(A("pose_fixture", "capability_kind"), L("declared_pose_fixture")),
            Eq(A("pose_fixture", "available"), L(1)),
            absent(N("world", "has_embodied_pose_affordance")),
        ),
        "effects": [
            ["add_node", "pose", "EmbodiedPoseAffordance", {
                "enabled": 1, "source": "observed_declared_pose_fixture",
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "world", "has_embodied_pose_affordance", "pose"],
            ["add_edge", "pose", "grounded_in_embodied_world_capability", "pose_fixture"],
        ],
    }


def activate_developmental_learning_rule():
    return {
        "name": "ebi_activate_developmental_learning_from_grounded_physical_trial_capability",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A recognized world that can execute grounded physical trials is an available developmental learning process. This is graph state inferred from an observed capability, not a Python start command.",
        "match": [
            ["episode", "has_embodied_learning_world", "world"],
            ["world", "has_embodied_physical_trial_capability", "physical_trial"],
            ["world", "has_embodied_reset_capability", "reset"],
        ],
        "where": And(
            Eq(A("physical_trial", "available"), L(1)),
            Eq(A("reset", "available"), L(1)),
            Not(Eq(
                A("episode", "developmental_deployment_mode"), L(1)
            )),
            Eq({"type": "Plus", "items": [A("episode", "development_learning_active"), L(0)]}, L(0)),
        ),
        "effects": [
            ["set_attr", "episode", "development_learning_active", 1],
            ["set_attr", "episode", "embodiment_reset_available", 1],
        ],
    }


def materialize_declared_reset_scenario_rule():
    return {
        "name": "ebi_materialize_declared_initial_fixture_as_situated_reset_scenario",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The configured initial fixture becomes one observed reset option. It is explicitly a situated option, not a canonical home configuration, and the graph remains free to select among later fixtures.",
        "match": [
            ["connection", "materializes_embodied_development_episode", "episode"],
            ["connection", "has_embodied_raw_reset_fixture", "fixture"],
        ],
        "where": And(
            Eq(A("fixture", "fixture_kind"), L("declared_initial_base_quarter_turns")),
            Eq(A("fixture", "available"), L(1)),
            absent(N("connection", "materializes_embodied_reset_scenario")),
        ),
        "effects": [
            ["add_node", "scenario", "EmbodiedResetScenario", {
                "name": "declared_initial_fixture",
                "ordinal": T(A("fixture", "fixture_event_ordinal")),
                "target_goal": "any", "enabled": 1, "selection_count": 0,
                "fixture_quarter_turn_x": T(A("fixture", "fixture_quarter_turn_x")),
                "fixture_quarter_turn_y": T(A("fixture", "fixture_quarter_turn_y")),
                "fixture_quarter_turn_z": T(A("fixture", "fixture_quarter_turn_z")),
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "connection", "materializes_embodied_reset_scenario", "scenario"],
            ["add_edge", "episode", "has_embodied_reset_scenario", "scenario"],
            ["add_edge", "scenario", "grounded_in_embodied_raw_reset_fixture", "fixture"],
        ],
    }


def request_initial_situated_reset_rule():
    return {
        "name": "ebi_request_graph_selected_initial_situated_reset_for_active_learning",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Once the existing developmental plan has selected a live capability, it may request a reset without specifying a scenario. The development seed's ordinary least-used-scenario rule performs the selection.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["episode", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "has_embodied_reset_scenario", "scenario"],
        ],
        "where": And(
            Eq(A("step", "status"), L("active")),
            Eq(A("capability", "status"), L("active")),
            Eq(A("scenario", "enabled"), L(1)),
            Eq(A("episode", "initial_situated_experiment_established"), L(0)),
            absent(N("episode", "has_active_embodied_reset_request")),
        ),
        "effects": [
            ["add_node", "request", "EmbodiedResetRequest", {
                "status": "requested", "cause": "initial_situated_experiment",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "episode", "has_embodied_reset_request", "request"],
            ["add_edge", "episode", "has_active_embodied_reset_request", "request"],
            ["add_edge", "request", "revises_learning_plan_step", "step"],
        ],
    }


def close_initial_situated_reset_rule():
    return {
        "name": "ebi_close_established_initial_situated_reset_request",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The initialization request only establishes which "
        "declared fixture grounds the first experiment; it has no mechanical "
        "output authority. Once the ordinary scenario selector resolves it, "
        "retain it as history but release the active-request frontier for "
        "later evidence-driven situated experiments.",
        "match": [
            ["episode", "has_active_embodied_reset_request", "request"],
        ],
        "where": And(
            Eq(A("request", "cause"), L("initial_situated_experiment")),
            Eq(A("request", "output_authority"), L(0)),
            Eq(A("request", "reinstantiation_spec_ready"), L(1)),
        ),
        "effects": [
            ["set_attr", "request", "status", "initial_fixture_established"],
            ["set_attr", "episode", "initial_situated_experiment_established", 1],
            [
                "del_edge", "episode",
                "has_active_embodied_reset_request", "request",
            ],
        ],
    }


def open_situated_episode_rule():
    return {
        "name": "ebi_open_situated_humanoid_development_episode_from_recognized_environment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Opening an episode is a graph consequence of recognized situated resources. It creates no goal or motor command; downstream developmental cognition owns those choices.",
        "match": [
            ["agent", "has_embodied_simulator_connection", "connection"],
            ["connection", "materializes_embodied_body_schema", "body"],
            ["connection", "materializes_embodied_learning_world", "world"],
            ["world", "has_embodied_pose_affordance", "pose"],
        ],
        "where": And(
            Eq(A("pose", "enabled"), L(1)),
            absent(N("connection", "materializes_embodied_development_episode")),
        ),
        "effects": [
            ["add_node", "episode", "EmbodiedDevelopmentEpisode", {
                "status": "situated_ready", "body_class": "articulated_humanoid",
                "initial_situated_experiment_established": 0,
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "agent", "has_embodied_development_episode", "episode"],
            ["add_edge", "connection", "materializes_embodied_development_episode", "episode"],
            ["add_edge", "episode", "has_embodied_body_schema", "body"],
            ["add_edge", "episode", "has_embodied_learning_world", "world"],
            ["add_edge", "episode", "grounded_in_embodied_simulator_connection", "connection"],
        ],
    }


def mark_strictly_newest_attachment_rule():
    return {
        "name": "ebi_mark_strictly_newest_embodied_attachment_as_current",
        "area": "general_cognition", "latency_class": "hard_realtime",
        "comment": "A strictly greater mechanically observed attachment ordinal makes the new connection current and retires older attachment authority. Equal legacy ordinals deliberately do not break ties.",
        "match": [["agent", "has_embodied_simulator_connection", "connection"],
                  ["agent", "has_embodied_simulator_connection", "older"]],
        "where": And(
            Gt(A("connection", "attachment_event_ordinal"), A("older", "attachment_event_ordinal")),
            Not(Exists(N("agent", "has_embodied_simulator_connection"), "greater",
                       Gt(A("greater", "attachment_event_ordinal"), A("connection", "attachment_event_ordinal")))),
            Eq(Count(Filter(N("agent", "has_embodied_simulator_connection"), "same",
                            Eq(A("same", "attachment_event_ordinal"), A("connection", "attachment_event_ordinal")))), L(1)),
        ),
        "effects": [["set_attr", "connection", "current_attachment", 1]],
    }


def retire_noncurrent_attachment_rule():
    return {"name": "ebi_retire_embodied_attachment_with_strictly_newer_successor",
            "area": "general_cognition", "latency_class": "hard_realtime",
            "match": [["agent", "has_embodied_simulator_connection", "connection"]],
            "where": Exists(N("agent", "has_embodied_simulator_connection"), "greater",
                            Gt(A("greater", "attachment_event_ordinal"), A("connection", "attachment_event_ordinal"))),
            "effects": [["set_attr", "connection", "current_attachment", 0]]}


def mark_only_attachment_as_current_rule():
    return {
        "name": "ebi_mark_only_embodied_attachment_as_current",
        "area": "general_cognition", "latency_class": "hard_realtime",
        "comment": "A sole mechanically attached world is current by cardinality. Multiple equal legacy ordinals remain intentionally unselected until a strictly newer attachment arrives.",
        "match": [["agent", "has_embodied_simulator_connection", "connection"]],
        "where": Eq(Count(N("agent", "has_embodied_simulator_connection")), L(1)),
        "effects": [["set_attr", "connection", "current_attachment", 1]],
    }


def production(name, src, edge, tgt):
    return {
        "provenance": f"embodied_body_ingest:{name}",
        "src": {"type": src, "var": "src"},
        "edge_type": edge,
        "tgt": {"type": tgt, "var": "tgt"},
    }


def manifest() -> dict:
    return {
        "id": "embodied_body_ingest",
        "version": "1.1.0",
        "depends_on": ["embodied_learning_session"],
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "description": "Graph-native recognition of raw grounded PyBullet humanoid connection, morphology, opaque actuator and reset/pose/trial capability facts. Python only ingests these facts; no float, program, actuator selection, goal or reset choice crosses the boundary.",
        "nodes": [], "edges": [],
        "productions": [
            production("agent_connection", "Agent", "has_embodied_simulator_connection", "EmbodiedSimulatorConnection"),
            production("connection_raw_body", "EmbodiedSimulatorConnection", "observes_embodied_raw_body", "EmbodiedRawBodyObservation"),
            production("connection_capability", "EmbodiedSimulatorConnection", "has_embodied_world_capability", "EmbodiedWorldCapability"),
            production("connection_motor_interface", "EmbodiedSimulatorConnection", "has_embodied_raw_motor_interface", "EmbodiedRawMotorInterface"),
            production("connection_raw_reset_fixture", "EmbodiedSimulatorConnection", "has_embodied_raw_reset_fixture", "EmbodiedRawResetFixture"),
            production("raw_affordance", "EmbodiedRawBodyObservation", "has_opaque_embodied_actuator_affordance", "EmbodiedOpaqueActuatorAffordance"),
            production("raw_effector_topology", "EmbodiedRawBodyObservation", "has_embodied_raw_effector_topology_relation", "EmbodiedRawEffectorTopologyRelation"),
            production("raw_projection", "EmbodiedRawMotorInterface", "has_embodied_raw_measurement_projection", "EmbodiedRawMeasurementProjection"),
            production("connection_body", "EmbodiedSimulatorConnection", "materializes_embodied_body_schema", "EmbodiedBodySchema"),
            production("connection_world", "EmbodiedSimulatorConnection", "materializes_embodied_learning_world", "EmbodiedLearningWorld"),
            production("body_raw", "EmbodiedBodySchema", "grounded_in_embodied_raw_body", "EmbodiedRawBodyObservation"),
            production("body_affordance", "EmbodiedBodySchema", "has_opaque_embodied_actuator_affordance", "EmbodiedOpaqueActuatorAffordance"),
            production("body_effector_topology", "EmbodiedBodySchema", "has_opaque_embodied_effector_topology_relation", "EmbodiedRawEffectorTopologyRelation"),
            production("world_connection", "EmbodiedLearningWorld", "grounded_in_embodied_simulator_connection", "EmbodiedSimulatorConnection"),
            production("world_reset", "EmbodiedLearningWorld", "has_embodied_reset_capability", "EmbodiedWorldCapability"),
            production("world_pose_fixture", "EmbodiedLearningWorld", "has_embodied_pose_fixture_capability", "EmbodiedWorldCapability"),
            production("world_trial", "EmbodiedLearningWorld", "has_embodied_physical_trial_capability", "EmbodiedWorldCapability"),
            production("world_motor_contract", "EmbodiedLearningWorld", "has_embodied_motor_bootstrap_contract", "EmbodiedMotorBootstrapContract"),
            production("contract_raw_motor_interface", "EmbodiedMotorBootstrapContract", "grounded_in_embodied_raw_motor_interface", "EmbodiedRawMotorInterface"),
            production("contract_projection", "EmbodiedMotorBootstrapContract", "has_embodied_measurement_projection", "EmbodiedMeasurementProjectionAffordance"),
            production("projection_raw", "EmbodiedMeasurementProjectionAffordance", "grounded_in_embodied_raw_measurement_projection", "EmbodiedRawMeasurementProjection"),
            production("pose_capability", "EmbodiedPoseAffordance", "grounded_in_embodied_world_capability", "EmbodiedWorldCapability"),
            production("connection_episode", "EmbodiedSimulatorConnection", "materializes_embodied_development_episode", "EmbodiedDevelopmentEpisode"),
            production("connection_reset_scenario", "EmbodiedSimulatorConnection", "materializes_embodied_reset_scenario", "EmbodiedResetScenario"),
            production("episode_reset_scenario", "EmbodiedDevelopmentEpisode", "has_embodied_reset_scenario", "EmbodiedResetScenario"),
            production("scenario_raw_fixture", "EmbodiedResetScenario", "grounded_in_embodied_raw_reset_fixture", "EmbodiedRawResetFixture"),
            production("episode_connection", "EmbodiedDevelopmentEpisode", "grounded_in_embodied_simulator_connection", "EmbodiedSimulatorConnection"),
        ],
        "rules": [
            materialize_body_and_world_rule(),
            materialize_motor_bootstrap_contract_rule(),
            materialize_measurement_projection_affordance_rule(),
            bind_opaque_affordances_rule(),
            bind_mechanical_effector_topology_rule(),
            materialize_pose_affordance_rule(),
            activate_developmental_learning_rule(),
            materialize_declared_reset_scenario_rule(),
            open_situated_episode_rule(),
            mark_only_attachment_as_current_rule(),
            mark_strictly_newest_attachment_rule(),
            retire_noncurrent_attachment_rule(),
            request_initial_situated_reset_rule(),
            close_initial_situated_reset_rule(),
        ],
    }


if __name__ == "__main__":
    output = ROOT / "seeds" / "embodied_body_ingest.json"
    output.write_text(json.dumps(manifest(), indent=2) + "\n", encoding="utf-8")
    print(output)
