"""Mechanical observation boundary for the humanoid kinematics study.

This module supplies opaque topology and body-relative endpoint receipts. It
does not select actions, fit models, classify anatomy, or solve kinematics.
"""
from __future__ import annotations

from statistics import fmean
from typing import Any, Iterable


def _edge(agent, source, edge_type: str, target) -> None:
    agent.inner.add_edge_unchecked(source, edge_type, target, {})


def install_opaque_kinematic_topology(
    agent,
    episode,
    body_shape_signature: Iterable[tuple[Any, ...]],
) -> int:
    """Transduce the sensed parent relation system into graph nodes."""
    relations = tuple(body_shape_signature)
    link_relations = tuple(
        relation for relation in relations if relation[0] == "link"
    )
    support_indices = {
        int(relation[2])
        for relation in relations
        if relation[0] == "support"
    }
    nodes = {}
    for _, link_index, parent_index, joint_type in link_relations:
        link = agent.s.add_node("HumanoidKinematicLink", {
            "ordinal": float(link_index),
            "parent_ordinal": float(parent_index),
            "joint_type": float(joint_type),
            "support_sensor": float(int(link_index) in support_indices),
            "terminal": 0.0,
        })
        nodes[int(link_index)] = link
        _edge(agent, episode, "has_humanoid_kinematic_link", link)
    for _, link_index, parent_index, _ in link_relations:
        parent = nodes.get(int(parent_index))
        child = nodes[int(link_index)]
        if parent is not None:
            _edge(
                agent,
                parent,
                "has_humanoid_kinematic_child",
                child,
            )
    coordinates = {}
    for relation in relations:
        if relation[0] != "actuator":
            continue
        actuator_ordinal = int(relation[1])
        joint_index = int(relation[2])
        if actuator_ordinal in coordinates:
            continue
        coordinate = agent.s.add_node("HumanoidKinematicCoordinate", {
            "ordinal": float(actuator_ordinal),
            "joint_index": float(joint_index),
            "position": 0.0,
            "velocity": 0.0,
            "state_seq": 0.0,
        })
        coordinates[actuator_ordinal] = coordinate
        _edge(
            agent,
            episode,
            "has_humanoid_kinematic_coordinate",
            coordinate,
        )
    for edge_type, model_type in (
        ("controls_humanoid_kinematic_coordinate", "HumanoidActionModel"),
        (
            "controls_humanoid_kinematic_coordinate",
            "HumanoidPhaseActionModel",
        ),
    ):
        for model in agent.s.nodes(model_type):
            attrs = agent.s.node(model)["attrs"]
            group = attrs.get("actuator_group")
            if group is None:
                continue
            coordinate = coordinates.get(int(group))
            if coordinate is not None:
                _edge(agent, model, edge_type, coordinate)
    agent.inner.set_attr(episode, "kinematics_study_active", 1.0)
    agent.tick()
    return sum(
        agent.s.node(link)["attrs"].get("terminal") == 1.0
        for link in nodes.values()
    )


def update_kinematic_coordinates(
    agent,
    episode,
    observation: dict[str, Any],
    *,
    state_seq: int,
) -> int:
    """Mechanically mirror opaque joint coordinates into graph state."""
    coordinates = {
        int(agent.s.node(node)["attrs"]["ordinal"]): node
        for node in agent.inner.neighbours(
            episode,
            "has_humanoid_kinematic_coordinate",
        )
    }
    updated = 0
    for row in observation.get("joints", ()):
        coordinate = coordinates.get(int(row["ordinal"]))
        if coordinate is None:
            continue
        agent.inner.set_attr(
            coordinate,
            "position",
            float(row["position"]),
        )
        agent.inner.set_attr(
            coordinate,
            "velocity",
            float(row["velocity"]),
        )
        agent.inner.set_attr(coordinate, "state_seq", float(state_seq))
        updated += 1
    return updated


def _actuator_coordinate(
    agent,
    trial,
    observation: dict[str, Any],
) -> tuple[bool, float]:
    """Read the selected opaque actuator group's raw joint coordinate."""
    action_models = agent.inner.neighbours(
        trial,
        "uses_humanoid_action_model",
    )
    groups = {
        int(agent.s.node(model)["attrs"]["actuator_group"])
        for model in action_models
        if "actuator_group" in agent.s.node(model)["attrs"]
    }
    if len(groups) != 1:
        return False, 0.0
    group = next(iter(groups))
    matches = tuple(
        row for row in observation.get("joints", ())
        if int(row["ordinal"]) == group
    )
    if len(matches) != 1:
        return False, 0.0
    return True, float(matches[0]["position"])


def _inverse_rotate(
    vector: tuple[float, float, float],
    quaternion_xyzw: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    """Rotate a world vector into the quaternion's local frame."""
    x, y, z = vector
    qx, qy, qz, qw = quaternion_xyzw
    # Unit-quaternion inverse is its conjugate.
    qx, qy, qz = -qx, -qy, -qz
    tx = 2.0 * (qy * z - qz * y)
    ty = 2.0 * (qz * x - qx * z)
    tz = 2.0 * (qx * y - qy * x)
    return (
        x + qw * tx + (qy * tz - qz * ty),
        y + qw * ty + (qz * tx - qx * tz),
        z + qw * tz + (qx * ty - qy * tx),
    )


def _body_relative_link_positions(
    observation: dict[str, Any],
) -> dict[int, tuple[float, float, float]]:
    base = tuple(float(value) for value in observation["base_position"])
    orientation = tuple(
        float(value) for value in observation["base_orientation_xyzw"]
    )
    positions = {}
    for row in observation["links"]:
        world = tuple(float(value) for value in row["link_frame_position"])
        offset = tuple(world[index] - base[index] for index in range(3))
        positions[int(row["index"])] = _inverse_rotate(offset, orientation)
    return positions


def add_kinematic_receipt_points(
    agent,
    episode,
    trial,
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    request_seq: int,
    receipt_verified: bool,
    external_event_frames: int,
) -> int:
    """Create pointwise measured receipts for graph-side model updates."""
    episode_attrs = agent.s.node(episode)["attrs"]
    if episode_attrs.get("kinematics_study_active") != 1.0:
        return 0
    pre = _body_relative_link_positions(before)
    post = _body_relative_link_positions(after)
    trial_attrs = agent.s.node(trial)["attrs"]
    pre_coordinate_valid, pre_coordinate = _actuator_coordinate(
        agent,
        trial,
        before,
    )
    post_coordinate_valid, post_coordinate = _actuator_coordinate(
        agent,
        trial,
        after,
    )
    coordinate_observed = pre_coordinate_valid and post_coordinate_valid
    enacted_bundle_width = len(tuple(dict.fromkeys(
        after.get("last_actuator_tokens", ())
    )))
    created = 0
    for point in agent.inner.neighbours(
        episode,
        "has_humanoid_kinematic_link",
    ):
        point_attrs = agent.s.node(point)["attrs"]
        if point_attrs.get("terminal") != 1.0:
            continue
        ordinal = int(point_attrs["ordinal"])
        if ordinal not in pre or ordinal not in post:
            continue
        displacement = tuple(
            post[ordinal][axis] - pre[ordinal][axis] for axis in range(3)
        )
        transition = agent.s.add_node("HumanoidKinematicTransition", {
            "request_seq": float(request_seq),
            "phase": str(episode_attrs.get("phase", "")),
            "decision_kind": str(trial_attrs.get("decision_kind", "")),
            "support_phase": float(trial_attrs.get("support_phase", 0.0)),
            "bundle_member_count": float(enacted_bundle_width),
            "point_ordinal": float(ordinal),
            "response_frames": float(trial_attrs["response_frames"]),
            "receipt_verified": float(receipt_verified),
            "external_event_frames": float(external_event_frames),
            "observed_dx": displacement[0],
            "observed_dy": displacement[1],
            "observed_dz": displacement[2],
            "actuator_coordinate_observed": float(coordinate_observed),
            "pre_actuator_coordinate": pre_coordinate,
            "post_actuator_coordinate": post_coordinate,
            "global_predicted_dx": 0.0,
            "global_predicted_dy": 0.0,
            "global_predicted_dz": 0.0,
            "phase_predicted_dx": 0.0,
            "phase_predicted_dy": 0.0,
            "phase_predicted_dz": 0.0,
            "interaction_predicted_dx": 0.0,
            "interaction_predicted_dy": 0.0,
            "interaction_predicted_dz": 0.0,
            "global_prediction_error": 0.0,
            "phase_prediction_error": 0.0,
            "interaction_prediction_error": 0.0,
            "global_model_count": 0.0,
            "phase_model_count": 0.0,
            "synergy_model_count": 0.0,
            "global_experience": 0.0,
            "phase_experience": 0.0,
            "synergy_experience": 0.0,
            "prediction_measured": 0.0,
            "selected_approach_ordinal": 0.0,
            "arbitrated_prediction_error": 0.0,
            "arbitration_prior_sample_count": 0.0,
            "arbitration_measured": 0.0,
        })
        _edge(
            agent,
            trial,
            "has_humanoid_kinematic_transition",
            transition,
        )
        _edge(
            agent,
            transition,
            "observes_humanoid_kinematic_link",
            point,
        )
        created += 1
    return created


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    return fmean(float(row[key]) for row in rows) if rows else 0.0


def summarize_kinematics_study(agent, standing_reference_z: float):
    """Serialize evaluator metrics without making control decisions."""
    rows = [
        dict(agent.s.node(node)["attrs"])
        for node in agent.s.nodes("HumanoidKinematicTransition")
        if (
            agent.s.node(node)["attrs"].get("prediction_measured") == 1.0
            and agent.s.node(node)["attrs"].get("arbitration_measured") == 1.0
        )
    ]
    rows.sort(key=lambda row: (
        float(row["request_seq"]),
        float(row["point_ordinal"]),
    ))
    normalized = []
    for row in rows:
        copy = dict(row)
        copy["global_normalized_error"] = (
            float(row["global_prediction_error"]) / standing_reference_z
        )
        copy["phase_normalized_error"] = (
            float(row["phase_prediction_error"]) / standing_reference_z
        )
        copy["interaction_normalized_error"] = (
            float(row["interaction_prediction_error"])
            / standing_reference_z
        )
        copy["arbitrated_normalized_error"] = (
            float(row["arbitrated_prediction_error"])
            / standing_reference_z
        )
        normalized.append(copy)

    def aggregate(selected):
        global_error = _mean(selected, "global_normalized_error")
        phase_error = _mean(selected, "phase_normalized_error")
        interaction_error = _mean(
            selected,
            "interaction_normalized_error",
        )
        arbitrated_error = _mean(
            selected,
            "arbitrated_normalized_error",
        )
        return {
            "receipt_count": len(selected),
            "global_mean_normalized_error": global_error,
            "phase_mean_normalized_error": phase_error,
            "interaction_mean_normalized_error": interaction_error,
            "arbitrated_mean_normalized_error": arbitrated_error,
            "phase_error_advantage": global_error - phase_error,
            "phase_relative_error_reduction": (
                (global_error - phase_error) / global_error
                if global_error > 0.0
                else 0.0
            ),
            "interaction_error_advantage_over_global": (
                global_error - interaction_error
            ),
            "interaction_relative_error_reduction_over_global": (
                (global_error - interaction_error) / global_error
                if global_error > 0.0
                else 0.0
            ),
            "interaction_error_advantage_over_phase": (
                phase_error - interaction_error
            ),
            "arbitrated_error_advantage_over_global": (
                global_error - arbitrated_error
            ),
            "arbitrated_relative_error_reduction_over_global": (
                (global_error - arbitrated_error) / global_error
                if global_error > 0.0
                else 0.0
            ),
            "approach_selection_counts": {
                "global": sum(
                    int(row["selected_approach_ordinal"]) == 0
                    for row in selected
                ),
                "phase": sum(
                    int(row["selected_approach_ordinal"]) == 1
                    for row in selected
                ),
                "interaction": sum(
                    int(row["selected_approach_ordinal"]) == 2
                    for row in selected
                ),
            },
        }

    phases = sorted({str(row["phase"]) for row in normalized})
    point_ordinals = sorted({
        int(row["point_ordinal"]) for row in normalized
    })
    return {
        "study_owner": "rust_graph",
        "evaluator_role": "paired_prequential_scoring_only",
        "terminal_point_count": len(point_ordinals),
        "measured_point_receipt_count": len(normalized),
        "overall": aggregate(normalized),
        "single_action": aggregate([
            row for row in normalized
            if float(row["bundle_member_count"]) == 1.0
        ]),
        "compound_action": aggregate([
            row for row in normalized
            if float(row["bundle_member_count"]) > 1.0
        ]),
        "seen_synergy_compound_action": aggregate([
            row for row in normalized
            if float(row["bundle_member_count"]) > 1.0
            and float(row["synergy_model_count"]) > 0.0
        ]),
        "unseen_synergy_compound_action": aggregate([
            row for row in normalized
            if float(row["bundle_member_count"]) > 1.0
            and float(row["synergy_model_count"]) == 0.0
        ]),
        "by_phase": {
            phase: aggregate([
                row for row in normalized if row["phase"] == phase
            ])
            for phase in phases
        },
        "by_terminal_point": {
            str(ordinal): aggregate([
                row for row in normalized
                if int(row["point_ordinal"]) == ordinal
            ])
            for ordinal in point_ordinals
        },
        "by_support_phase": {
            str(int(support_phase)): aggregate([
                row for row in normalized
                if int(row["support_phase"]) == support_phase
            ])
            for support_phase in sorted({
                int(row["support_phase"]) for row in normalized
            })
        },
        "prequential_receipts": normalized,
    }
