#!/usr/bin/env python3
"""Author integer-native output-null graph hints from CMU motion topology."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "data" / "cmu_mocap" / "topology.json"
OUTPUT = ROOT / "seeds" / "cmu_motion_topology_bootstrap.json"


def build() -> dict:
    source = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    nodes: list[dict] = []
    edges: list[dict] = []
    local_id = 1
    consequence_shape_ids: dict[tuple[str, str, str], int] = {}
    consequence_shapes = sorted({
        (
            clip["task_context"],
            stage["phase"],
            stage["height_energy_relation"],
        )
        for clip in source["clips"] for stage in clip["stages"]
    })
    for context, phase, height_energy in consequence_shapes:
        consequence_shape_ids[(context, phase, height_energy)] = local_id
        nodes.append({
            "local_id": local_id,
            "type": "EmbodiedMotorConsequenceRoutingShape",
            "attrs": {
                "name": (
                    f"motor_consequence_shape:{context}:{phase}:"
                    f"{height_energy}"
                ),
                "motor_task_context": context,
                "motor_task_phase": phase,
                "height_energy_relation": height_energy,
                "signature": [
                    ["motor_task_context", context],
                    ["motor_task_phase", phase],
                    ["height_energy_relation", height_energy],
                ],
                "output_authority": 0,
                "integer_native": 1,
            },
        })
        edges.append({
            "src": {"role": "agent_root"},
            "type": "has_embodied_motor_consequence_routing_shape",
            "tgt": {"local": local_id},
            "attrs": {},
        })
        local_id += 1
    for clip_ordinal, clip in enumerate(source["clips"]):
        evidence_id = local_id
        hint_id = local_id + 1
        local_id += 2
        evidence_name = f"motion_topology_evidence:{clip['source']}"
        hint_name = f"motion_topology_hint:{clip['source']}"
        nodes.extend((
            {
                "local_id": evidence_id,
                "type": "ObservedMotionTopologyEvidence",
                "attrs": {
                    "name": evidence_name,
                    "ordinal": clip_ordinal,
                    "source": clip["source"],
                    "description": clip["description"],
                    "dataset": source["dataset"],
                    "dataset_url": source["dataset_url"],
                    "source_amc_sha256": clip["source_amc_sha256"],
                    "frame_rate_hz": clip["frame_rate_hz"],
                    "frame_count": clip["frame_count"],
                    "state_count": clip["state_count"],
                    "transition_count": clip["transition_count"],
                    "opposed_translation_observed": clip[
                        "opposed_translation_observed"
                    ],
                    "raw_pose_values_retained": 0,
                    "output_authority": 0,
                    "integer_native": 1,
                },
            },
            {
                "local_id": hint_id,
                "type": "EmbodiedMotorPlanHint",
                "attrs": {
                    "name": hint_name,
                    "ordinal": clip_ordinal,
                    "signature": [["motor_task", clip["task_context"]]],
                    "motor_task_context": clip["task_context"],
                    "knowledge_kind": "observed_motion_topology_basin_hint",
                    "provenance": clip["source"],
                    "evidence_url": source["dataset_url"],
                    "stage_count": clip["stage_count"],
                    "output_authority": 0,
                    "integer_native": 1,
                },
            },
        ))
        edges.extend((
            {
                "src": {"role": "agent_root"},
                "type": "has_observed_motion_topology_evidence",
                "tgt": {"local": evidence_id},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_motor_plan_hint_library",
                "tgt": {"local": hint_id},
                "attrs": {},
            },
            {
                "src": {"local": evidence_id},
                "type": "supports_embodied_motor_plan_hint",
                "tgt": {"local": hint_id},
                "attrs": {},
            },
        ))

        state_ids: dict[int, int] = {}
        stage_ids: dict[int, int] = {}
        states = {row["id"]: row for row in clip["states"]}
        stages = {row["state_id"]: row for row in clip["stages"]}
        for state_ordinal, state in sorted(states.items()):
            state_id = local_id
            stage_id = local_id + 1
            local_id += 2
            state_ids[state_ordinal] = state_id
            stage_ids[state_ordinal] = stage_id
            stage = stages[state_ordinal]
            signature = [
                ["support_topology", state["support_topology"]],
                ["contact_dimension", state["contact_dimension"]],
                ["height_energy_relation", state["height_energy_relation"]],
                ["kinetic_energy_relation", state["kinetic_energy_relation"]],
                ["translation_relation", state["translation_relation"]],
            ]
            nodes.extend((
                {
                    "local_id": state_id,
                    "type": "ObservedMotionTopologyState",
                    "attrs": {
                        "name": f"{evidence_name}:state:{state_ordinal}",
                        "ordinal": state_ordinal,
                        "signature": signature,
                        "output_authority": 0,
                        "integer_native": 1,
                    },
                },
                {
                    "local_id": stage_id,
                    "type": "EmbodiedMotorPlanHintStage",
                    "attrs": {
                        "name": f"{hint_name}:stage:{stage['ordinal']}",
                        "ordinal": stage["ordinal"],
                        "stage_role": "observed_contact_energy_basin",
                        "motor_task_context": clip["task_context"],
                        "motor_task_phase": stage["phase"],
                        "support_topology": stage["support_topology"],
                        "height_energy_relation": stage[
                            "height_energy_relation"
                        ],
                        "signature": signature,
                        "routing_signature": [
                            ["motor_task_context", clip["task_context"]],
                            ["motor_task_phase", stage["phase"]],
                        ],
                        "requires_observed_consequence_shape": 1,
                        "output_authority": 0,
                        "integer_native": 1,
                    },
                },
            ))
            edges.extend((
                {
                    "src": {"local": evidence_id},
                    "type": "observes_motion_topology_state",
                    "tgt": {"local": state_id},
                    "attrs": {},
                },
                {
                    "src": {"local": hint_id},
                    "type": "has_embodied_motor_plan_hint_stage",
                    "tgt": {"local": stage_id},
                    "attrs": {},
                },
                {
                    "src": {"local": stage_id},
                    "type": "abstracts_observed_motion_topology_state",
                    "tgt": {"local": state_id},
                    "attrs": {},
                },
                {
                    "src": {"local": stage_id},
                    "type": "targets_embodied_motor_consequence_shape",
                    "tgt": {"local": consequence_shape_ids[(
                        clip["task_context"],
                        stage["phase"],
                        stage["height_energy_relation"],
                    )]},
                    "attrs": {},
                },
            ))

        for transition_ordinal, transition in enumerate(clip["transitions"]):
            transition_id = local_id
            local_id += 1
            source_state = int(transition["from_state"])
            target_state = int(transition["to_state"])
            nodes.append({
                "local_id": transition_id,
                "type": "ObservedMotionTopologyTransition",
                "attrs": {
                    "name": (
                        f"{evidence_name}:transition:"
                        f"{source_state}:{target_state}"
                    ),
                    "ordinal": transition_ordinal,
                    "observation_count": transition["count"],
                    "output_authority": 0,
                    "integer_native": 1,
                },
            })
            edges.extend((
                {
                    "src": {"local": evidence_id},
                    "type": "observes_motion_topology_transition",
                    "tgt": {"local": transition_id},
                    "attrs": {},
                },
                {
                    "src": {"local": transition_id},
                    "type": "starts_from_motion_topology_state",
                    "tgt": {"local": state_ids[source_state]},
                    "attrs": {},
                },
                {
                    "src": {"local": transition_id},
                    "type": "continues_to_motion_topology_state",
                    "tgt": {"local": state_ids[target_state]},
                    "attrs": {},
                },
                {
                    "src": {"local": stage_ids[source_state]},
                    "type": "can_transition_to_embodied_motor_plan_hint_stage",
                    "tgt": {"local": stage_ids[target_state]},
                    "attrs": {"observation_count": transition["count"]},
                },
            ))

    productions = (
        ("Agent", "has_observed_motion_topology_evidence", "ObservedMotionTopologyEvidence"),
        ("Agent", "has_embodied_motor_plan_hint_library", "EmbodiedMotorPlanHint"),
        ("ObservedMotionTopologyEvidence", "supports_embodied_motor_plan_hint", "EmbodiedMotorPlanHint"),
        ("ObservedMotionTopologyEvidence", "observes_motion_topology_state", "ObservedMotionTopologyState"),
        ("ObservedMotionTopologyEvidence", "observes_motion_topology_transition", "ObservedMotionTopologyTransition"),
        ("ObservedMotionTopologyTransition", "starts_from_motion_topology_state", "ObservedMotionTopologyState"),
        ("ObservedMotionTopologyTransition", "continues_to_motion_topology_state", "ObservedMotionTopologyState"),
        ("EmbodiedMotorPlanHint", "has_embodied_motor_plan_hint_stage", "EmbodiedMotorPlanHintStage"),
        ("EmbodiedMotorPlanHintStage", "abstracts_observed_motion_topology_state", "ObservedMotionTopologyState"),
        ("Agent", "has_embodied_motor_consequence_routing_shape", "EmbodiedMotorConsequenceRoutingShape"),
        ("EmbodiedMotorPlanHintStage", "targets_embodied_motor_consequence_shape", "EmbodiedMotorConsequenceRoutingShape"),
        ("EmbodiedMotorPlanHintStage", "can_transition_to_embodied_motor_plan_hint_stage", "EmbodiedMotorPlanHintStage"),
    )
    return {
        "id": "cmu_motion_topology_bootstrap",
        "version": "1.0.0",
        "depends_on": ["embodied_capability_bootstrap"],
        "self_load_only": True,
        "area": "general_cognition",
        "latency_class": "background",
        "description": (
            "Output-null contact and energy topology distilled from a "
            "checksum-pinned CMU motion-capture subset."
        ),
        "nodes": nodes,
        "edges": edges,
        "productions": [
            {
                "provenance": f"seed:cmu_motion_topology_bootstrap:{edge_type}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge_type,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for src, edge_type, tgt in productions
        ],
        "rules": [],
    }


def main() -> int:
    payload = build()
    OUTPUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "nodes": len(payload["nodes"]),
        "edges": len(payload["edges"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
