"""Train through the humanoid curriculum, then run a frozen paired evaluation."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_walk import (
    MOTOR_LIBRARY_VERSION,
    _run_arm,
    developmental_curriculum_contract,
)


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_developmental_curriculum_v1.json"
DEFAULT_LIBRARY = (
    ROOT / "results" / "humanoid_future_manifold_curriculum"
    / "trained_motor_library.json"
)

# These are deliberately finite checkpoints.  A staged run is a single-arm
# probe/training pass; it must not silently turn into the paired experiment.
STAGED_ACTION_BUDGETS = (48, 96, 192, 360)
CAPABILITY_LIBRARY_SEMANTIC_TYPE = (
    "frozen_output_null_developmental_capability_library"
)
MOTOR_LIBRARY_SEMANTIC_TYPE = "frozen_output_null_motor_library"


def _digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _library_metadata(library: dict, protocol: dict) -> dict:
    """Describe library semantics without changing old library files.

    Older artifacts predate explicit metadata.  Their type is inferred from
    their shape and marked as inferred; explicitly supplied metadata is still
    checked and cannot disagree with the protocol.
    """
    explicit_type = library.get("semantic_type") or library.get(
        "library_semantic_type"
    )
    if explicit_type:
        semantic_type = str(explicit_type)
        type_source = "declared"
    elif library.get("developmental_capabilities"):
        semantic_type = CAPABILITY_LIBRARY_SEMANTIC_TYPE
        type_source = "inferred"
    elif library.get("body_shapes"):
        semantic_type = MOTOR_LIBRARY_SEMANTIC_TYPE
        type_source = "inferred"
    else:
        semantic_type = "unknown"
        type_source = "absent"

    contract = library.get("developmental_curriculum_contract")
    contract_digest = (
        contract.get("ontology_sha256") if isinstance(contract, dict) else None
    )
    if contract is not None and contract_digest is None:
        contract_digest = _digest(contract)
    expected_contract = developmental_curriculum_contract()
    expected_digest = expected_contract["ontology_sha256"]
    return {
        "semantic_type": semantic_type,
        "semantic_type_source": type_source,
        "curriculum_contract": contract,
        "curriculum_contract_digest": contract_digest,
        "expected_curriculum_contract_digest": expected_digest,
        "curriculum_contract_present": contract is not None,
        "curriculum_contract_matches": contract == expected_contract,
        "body_shape_count": len(library.get("body_shapes") or []),
        "developmental_capability_count": len(
            library.get("developmental_capabilities") or []
        ),
        "motor_program_count": sum(
            len(shape.get("programs") or [])
            for shape in library.get("body_shapes") or []
        ),
    }


def _read_library_metadata(path: Path, protocol: dict) -> dict:
    """Read metadata without turning an incomplete staged artifact into an exception."""
    metadata = {
        "artifact_path": str(path),
        "artifact_present": path.exists(),
        "artifact_valid_json": False,
    }
    if not path.exists():
        metadata.update({
            "semantic_type": "unknown",
            "semantic_type_source": "absent",
            "curriculum_contract_present": False,
            "curriculum_contract_matches": False,
        })
        return metadata
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        metadata.update({
            "semantic_type": "unknown",
            "semantic_type_source": "invalid",
            "curriculum_contract_present": False,
            "curriculum_contract_matches": False,
            "artifact_error": str(exc),
        })
        return metadata
    if not isinstance(loaded, dict):
        metadata.update({
            "semantic_type": "unknown",
            "semantic_type_source": "invalid",
            "curriculum_contract_present": False,
            "curriculum_contract_matches": False,
            "artifact_error": "library artifact JSON root is not an object",
        })
        return metadata
    metadata.update(_library_metadata(loaded, protocol))
    metadata["artifact_valid_json"] = True
    return metadata


def _metrics(run: dict) -> dict:
    curriculum = run.get("curriculum") or {}
    future_manifold = run.get("future_manifold") or {}
    cognitive = run.get("cognitive_supervision") or {}
    trace = run.get("trace") or []
    recovery_promotion_rows = [
        row for row in trace
        if int(row.get("recovery_promotion_audited", 0)) == 1
    ]
    support_audit_rows = [
        row for row in trace
        if int(row.get("support_counterfactual_audit_seq", 0)) > 0
    ]
    actions_executed = run.get("actions_executed")
    if actions_executed is None:
        actions_executed = len(trace)
    phase_models_after_walk = run.get("phase_models_after_walk") or []
    enacted_token_outcomes = {}
    for token in sorted({str(row.get("selected_token", "")) for row in trace}):
        rows = [row for row in trace if str(row.get("selected_token", "")) == token]
        enacted_token_outcomes[token] = {
            "action_count": len(rows),
            "directed_units": sum(
                int(row.get("development_directed_units", 0)) for row in rows
            ),
            "translation_units": sum(
                int(row.get("development_translation_units", 0)) for row in rows
            ),
            "directed_consistency_count": sum(
                int(row.get("development_directed_consistency", 0)) for row in rows
            ),
        }
    enacted_motor_program_outcomes = {}
    program_keys = sorted({
        "|".join(str(value) for value in row.get("motor_tokens", []))
        for row in trace
    })
    for program_key in program_keys:
        rows = [
            row for row in trace
            if "|".join(
                str(value) for value in row.get("motor_tokens", [])
            ) == program_key
        ]
        enacted_motor_program_outcomes[program_key] = {
            "action_count": len(rows),
            "directed_units": sum(
                int(row.get("development_directed_units", 0)) for row in rows
            ),
            "translation_units": sum(
                int(row.get("development_translation_units", 0)) for row in rows
            ),
            "directed_consistency_count": sum(
                int(row.get("development_directed_consistency", 0))
                for row in rows
            ),
            "decision_kind_counts": dict(Counter(
                str(row.get("decision_kind", "unclassified")) for row in rows
            )),
        }
    enacted_intent_program_outcomes = {}
    intent_program_keys = sorted({
        (
            str(row.get("decision_kind", "unclassified")),
            "|".join(str(value) for value in row.get("motor_tokens", [])),
        )
        for row in trace
    })
    for intent, program_key in intent_program_keys:
        rows = [
            row for row in trace
            if str(row.get("decision_kind", "unclassified")) == intent
            and "|".join(
                str(value) for value in row.get("motor_tokens", [])
            ) == program_key
        ]
        enacted_intent_program_outcomes[
            f"{intent}::{program_key}"
        ] = {
            "intent": intent,
            "program": program_key,
            "action_count": len(rows),
            "directed_units": sum(
                int(row.get("development_directed_units", 0)) for row in rows
            ),
            "translation_units": sum(
                int(row.get("development_translation_units", 0)) for row in rows
            ),
            "directed_consistency_count": sum(
                int(row.get("development_directed_consistency", 0))
                for row in rows
            ),
        }
    enacted_development_context_outcomes = {}
    context_keys = sorted({
        (
            str(row.get("decision_kind", "unclassified")),
            str(row.get("active_developmental_capability", "inactive")),
            int(row.get("orientation_class_before", 0)),
            str(row.get("selected_token", "")),
        )
        for row in trace
    })
    for intent, capability, orientation, token in context_keys:
        rows = [
            row for row in trace
            if str(row.get("decision_kind", "unclassified")) == intent
            and str(row.get(
                "active_developmental_capability", "inactive"
            )) == capability
            and int(row.get("orientation_class_before", 0)) == orientation
            and str(row.get("selected_token", "")) == token
        ]
        key = f"{intent}::{capability}::{orientation}::{token}"
        enacted_development_context_outcomes[key] = {
            "intent": intent,
            "capability": capability,
            "pre_orientation_class": orientation,
            "primary_token": token,
            "action_count": len(rows),
            "directed_units": sum(
                int(row.get("development_directed_units", 0)) for row in rows
            ),
            "translation_units": sum(
                int(row.get("development_translation_units", 0)) for row in rows
            ),
        }

    # _run_arm may publish these directly in a newer build.  The trace forms
    # are accepted as a compatibility fallback for mocked/older builds.
    gate_onset_action = run.get("first_bounds_ready_action")
    if gate_onset_action is None:
        gate_onset_action = run.get("manifold_gate_onset_action")
    if gate_onset_action is None:
        gate_onset_action = future_manifold.get("first_bounds_ready_action")
    post_gate_action_count = run.get("post_gate_action_count")
    if post_gate_action_count is None:
        post_gate_action_count = future_manifold.get("post_gate_action_count")
    if gate_onset_action is None:
        ready_rows = [
            row for row in trace
            if float(row.get("manifold_bounds_ready", row.get(
                "bounds_ready", 0
            ))) > 0.5
        ]
        if ready_rows:
            gate_onset_action = ready_rows[0].get("action")
            if post_gate_action_count is None:
                post_gate_action_count = len(ready_rows)
    gate_evidence_present = (
        gate_onset_action is not None and post_gate_action_count is not None
    )
    return {
        "actions_executed": actions_executed,
        "curriculum_rule_costs": run.get("curriculum_rule_costs", []),
        "subsection_composition": run.get("subsection_composition", {}),
        "developmental_reset_diagnostics": run.get(
            "developmental_reset_diagnostics", {}
        ),
        "directed_progress": run.get("directed_progress", 0.0),
        "first_fall_action": run.get("first_fall_action"),
        "minimum_height": run.get("minimum_height", 0.0),
        "lateral_offset": run.get("lateral_offset", 0.0),
        "support_alternations": run.get("support_alternations", 0),
        "compound_action_count": run.get("compound_action_count", 0),
        "takeoff_action_count": sum(
            float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
            for row in trace
        ),
        "takeoff_action_trace": [
            {
                key: row.get(key)
                for key in (
                    "action",
                    "body_reset_before_action",
                    "active_developmental_capability",
                    "decision_kind",
                    "collapse_kind",
                    "motor_tokens",
                    "motor_bundle_width",
                    "response_frames",
                    "orientation_class_before",
                    "orientation_class_after",
                    "development_elevation_units",
                    "development_vertical_velocity_progress_units",
                    "position_after",
                    "linear_velocity_after",
                    "motor_weight_a",
                    "motor_weight_b",
                    "takeoff_effort_supported",
                    "takeoff_effort_authorized",
                )
            }
            for row in trace
            if float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
        ],
        "takeoff_transition_trace": [
            {
                key: row.get(key)
                for key in (
                    "action",
                    "body_reset_before_action",
                    "active_developmental_capability",
                    "active_developmental_capability_after_action",
                    "self_takeoff_drive_active_after",
                    "support_pattern",
                    "decision_kind",
                    "collapse_kind",
                    "motor_tokens",
                    "motor_bundle_width",
                    "response_frames",
                    "orientation_class_before",
                    "orientation_class_after",
                    "development_elevation_units",
                    "development_vertical_velocity_progress_units",
                    "position_after",
                    "linear_velocity_after",
                )
            }
            for row in trace
            if (
                row.get("active_developmental_capability")
                == "two_foot_jump"
                or float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
                or row.get("collapse_kind") in {
                    "takeoff_derivative_recurrence",
                    "compound_recovery_locomotion",
                }
            )
        ],
        "takeoff_compound_action_count": sum(
            float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
            and int(row.get("motor_bundle_width", 0)) > 1
            for row in trace
        ),
        "takeoff_maximum_motor_bundle_width": max(
            (
                int(row.get("motor_bundle_width", 0))
                for row in trace
                if float(row.get(
                    "self_takeoff_drive_active_after", 0
                )) > 0.5
            ),
            default=0,
        ),
        "takeoff_development_elevation_units": sum(
            int(row.get("development_elevation_units", 0))
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        ),
        "takeoff_positive_elevation_action_count": sum(
            int(row.get("development_elevation_units", 0)) > 0
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        ),
        "takeoff_vertical_velocity_progress_units": sum(
            int(row.get(
                "development_vertical_velocity_progress_units", 0
            ))
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        ),
        "takeoff_positive_vertical_velocity_action_count": sum(
            int(row.get(
                "development_vertical_velocity_progress_units", 0
            )) > 0
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        ),
        "takeoff_outcomes_by_motor_bundle_width": {
            str(width): {
                "action_count": sum(
                    int(row.get("motor_bundle_width", 0)) == width
                    for row in trace
                    if float(row.get(
                        "self_takeoff_drive_active_after", 0
                    )) > 0.5
                ),
                "elevation_units": sum(
                    int(row.get("development_elevation_units", 0))
                    for row in trace
                    if float(row.get(
                        "self_takeoff_drive_active_after", 0
                    )) > 0.5
                    and int(row.get("motor_bundle_width", 0)) == width
                ),
                "vertical_velocity_progress_units": sum(
                    int(row.get(
                        "development_vertical_velocity_progress_units", 0
                    ))
                    for row in trace
                    if float(row.get(
                        "self_takeoff_drive_active_after", 0
                    )) > 0.5
                    and int(row.get("motor_bundle_width", 0)) == width
                ),
                "positive_vertical_velocity_action_count": sum(
                    int(row.get(
                        "development_vertical_velocity_progress_units", 0
                    )) > 0
                    for row in trace
                    if float(row.get(
                        "self_takeoff_drive_active_after", 0
                    )) > 0.5
                    and int(row.get("motor_bundle_width", 0)) == width
                ),
            }
            for width in sorted({
                int(row.get("motor_bundle_width", 0))
                for row in trace
                if float(row.get(
                    "self_takeoff_drive_active_after", 0
                )) > 0.5
            })
        },
        "takeoff_motor_weight_maximum": max(
            (
                max(
                    float(row.get("motor_weight_a", 1.0)),
                    float(row.get("motor_weight_b", 1.0)),
                )
                for row in trace
                if float(row.get(
                    "self_takeoff_drive_active_after", 0
                )) > 0.5
            ),
            default=0.0,
        ),
        "takeoff_above_unit_effort_action_count": sum(
            max(
                float(row.get("motor_weight_a", 1.0)),
                float(row.get("motor_weight_b", 1.0)),
            ) > 1.0
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        ),
        "takeoff_effort_supported_action_count": sum(
            float(row.get("takeoff_effort_supported", 0.0)) > 0.5
            for row in trace
            if float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
        ),
        "takeoff_effort_authorized_action_count": sum(
            float(row.get("takeoff_effort_authorized", 0.0)) > 0.5
            for row in trace
            if float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
        ),
        "takeoff_effort_required_ratio_maximum": max((
            float(row.get("takeoff_effort_required_ratio", 0.0))
            for row in trace
            if float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
        ), default=0.0),
        "takeoff_effort_residual_ratio_maximum": max((
            float(row.get("takeoff_effort_residual_ratio", 0.0))
            for row in trace
            if float(row.get("self_takeoff_drive_active_after", 0)) > 0.5
        ), default=0.0),
        "takeoff_compound_candidate_count_maximum": max(
            (
                int(row.get("takeoff_compound_candidate_count", 0))
                for row in trace
                if float(row.get(
                    "self_takeoff_drive_active_after", 0
                )) > 0.5
            ),
            default=0,
        ),
        **{
            key: max(
                (
                    int(row.get(key, 0))
                    for row in trace
                    if float(row.get(
                        "self_takeoff_drive_active_after", 0
                    )) > 0.5
                ),
                default=0,
            )
            for key in (
                "takeoff_compound_target_order",
                "compound_curiosity_selection_count",
                "compound_curiosity_pre_expansion_candidate_count_maximum",
                "compound_curiosity_terminal_candidate_count_maximum",
                "compound_curiosity_terminal_target_order_maximum",
            )
        },
        "takeoff_compound_expansion_authorized_action_count": sum(
            int(row.get("takeoff_compound_allow_expansion", 0)) == 1
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        ),
        "takeoff_compound_selection_kind_counts": dict(Counter(
            str(row.get("takeoff_compound_selection_kind", "none"))
            for row in trace
            if float(row.get(
                "self_takeoff_drive_active_after", 0
            )) > 0.5
        )),
        "ideal_effort_ratio_final": (
            (run.get("future_manifold") or {}).get("ideal_effort") or {}
        ).get("ratio", 0.0),
        "ideal_effort_evidence_count_final": (
            (run.get("future_manifold") or {}).get("ideal_effort") or {}
        ).get("evidence_count", 0),
        "effort_scale_joules_final": (
            (run.get("future_manifold") or {}).get("ideal_effort") or {}
        ).get("scale_joules", 0.0),
        "effort_gate_audit_count": (
            (future_manifold.get("ideal_effort") or {}).get("audit_count", 0)
        ),
        "effort_gate_supported_audit_count": (
            (future_manifold.get("ideal_effort") or {}).get(
                "supported_audit_count", 0
            )
        ),
        "effort_gate_blocked_audit_count": (
            (future_manifold.get("ideal_effort") or {}).get(
                "blocked_audit_count", 0
            )
        ),
        "effort_gate_compression_audit_count": (
            (future_manifold.get("ideal_effort") or {}).get(
                "compression_audit_count", 0
            )
        ),
        "caregiver_protected_action_count": sum(
            int(row.get("caregiver_protective_support_applied", 0))
            for row in trace
        ),
        "caregiver_support_impulse_newton_seconds": sum(
            float(row.get("caregiver_support_impulse_newton_seconds", 0.0))
            for row in trace
        ),
        "caregiver_support_scale_sum": sum(
            float(row.get("caregiver_support_scale", 0.0))
            for row in trace
        ),
        "caregiver_support_scale_maximum": max(
            (float(row.get("caregiver_support_scale", 0.0)) for row in trace),
            default=0.0,
        ),
        "counterfactual_support_scale_counts": dict(Counter(
            str(float(row.get("caregiver_support_scale", 0.0)))
            for row in trace
            if int(row.get("counterfactual_support_release", 0)) == 1
        )),
        "caregiver_manifold_residual_signed_sums": [
            sum(
                float((row.get("caregiver_manifold_residual") or [0.0] * 7)[index])
                for row in trace
                if int(row.get("caregiver_protective_support_applied", 0)) == 1
            )
            for index in range(7)
        ],
        "caregiver_manifold_residual_absolute_sums": [
            sum(
                abs(float((row.get("caregiver_manifold_residual") or [0.0] * 7)[index]))
                for row in trace
                if int(row.get("caregiver_protective_support_applied", 0)) == 1
            )
            for index in range(7)
        ],
        "caregiver_manifold_decisive_tick_maximum": max(
            (
                float(row.get("caregiver_manifold_decisive_tick", 0.0))
                for row in trace
                if int(row.get("caregiver_protective_support_applied", 0)) == 1
            ),
            default=0.0,
        ),
        "caregiver_protective_support_available": run.get(
            "caregiver_protective_support_available", 0
        ),
        "caregiver_support_models": run.get("caregiver_support_models", []),
        "support_counterfactual_audit_count": len(support_audit_rows),
        "support_counterfactual_loss_improvement_count": sum(
            float((row.get("supported_projection") or {}).get("loss", 0.0))
            < float((row.get("unsupported_projection") or {}).get("loss", 0.0))
            for row in support_audit_rows
        ),
        "support_counterfactual_resolution_gain_count": sum(
            float((row.get("supported_projection") or {}).get("resolved", 0.0))
            > float((row.get("unsupported_projection") or {}).get("resolved", 0.0))
            for row in support_audit_rows
        ),
        "support_counterfactual_escape_count": sum(
            float((row.get("supported_projection") or {}).get("loss", 0.0)) > 0.0
            for row in support_audit_rows
        ),
        "support_counterfactual_recommendation_count": sum(
            int(row.get("support_counterfactual_recommends_support", 0))
            for row in support_audit_rows
        ),
        "support_counterfactual_recommended_and_applied_count": sum(
            int(row.get("support_counterfactual_recommends_support", 0)) == 1
            and int(row.get("caregiver_protective_support_applied", 0)) == 1
            for row in support_audit_rows
        ),
        "support_counterfactual_recommended_not_applied_count": sum(
            int(row.get("support_counterfactual_recommends_support", 0)) == 1
            and int(row.get("caregiver_protective_support_applied", 0)) == 0
            for row in support_audit_rows
        ),
        "support_counterfactual_not_recommended_but_applied_count": sum(
            int(row.get("support_counterfactual_recommends_support", 0)) == 0
            and int(row.get("caregiver_protective_support_applied", 0)) == 1
            for row in support_audit_rows
        ),
        "support_counterfactual_worsening_count": sum(
            float((row.get("supported_projection") or {}).get("loss", 0.0))
            > float((row.get("unsupported_projection") or {}).get("loss", 0.0))
            for row in support_audit_rows
        ),
        "support_counterfactual_applied_predicted_safe_observed_safe_count": sum(
            int(row.get("caregiver_protective_support_applied", 0)) == 1
            and float((row.get("supported_projection") or {}).get("loss", 0.0)) == 0.0
            and int(row.get("observed_projection_escape_count", 0)) == 0
            for row in support_audit_rows
        ),
        "support_counterfactual_applied_predicted_safe_observed_escape_count": sum(
            int(row.get("caregiver_protective_support_applied", 0)) == 1
            and float((row.get("supported_projection") or {}).get("loss", 0.0)) == 0.0
            and int(row.get("observed_projection_escape_count", 0)) > 0
            for row in support_audit_rows
        ),
        "support_counterfactual_recommended_unapplied_observed_escape_count": sum(
            int(row.get("support_counterfactual_recommends_support", 0)) == 1
            and int(row.get("caregiver_protective_support_applied", 0)) == 0
            and int(row.get("observed_projection_escape_count", 0)) > 0
            for row in support_audit_rows
        ),
        "support_counterfactual_not_recommended_unapplied_observed_escape_count": sum(
            int(row.get("support_counterfactual_recommends_support", 0)) == 0
            and int(row.get("caregiver_protective_support_applied", 0)) == 0
            and int(row.get("observed_projection_escape_count", 0)) > 0
            for row in support_audit_rows
        ),
        "support_counterfactual_audits": [
            {
                "action": row.get("action"),
                "selected_token": row.get("selected_token"),
                "support_applied": row.get(
                    "caregiver_protective_support_applied"
                ),
                "recommends_support": row.get(
                    "support_counterfactual_recommends_support"
                ),
                "unsupported": row.get("unsupported_projection"),
                "supported": row.get("supported_projection"),
                "supported_residual": row.get(
                    "supported_projection_residual"
                ),
                "unsupported_bounds": row.get(
                    "unsupported_projection_bounds"
                ),
                "supported_bounds": row.get("supported_projection_bounds"),
                "observed_delta": row.get("observed_projection_delta"),
                "observed_escape_count": row.get(
                    "observed_projection_escape_count"
                ),
            }
            for row in support_audit_rows
        ],
        "caregiver_under_evidenced_unprotected_counts_by_capability": dict(
            Counter(
                row.get("active_developmental_capability", "inactive")
                for row in trace
                if int(row.get("caregiver_protective_support_available", 0)) == 1
                and float(row.get(
                    "developmental_capability_success_count_before_action", 0
                )) < float(row.get("development_evidence_window", 0))
                and int(row.get(
                    "caregiver_protective_support_applied", 0
                )) == 0
            )
        ),
        "caregiver_protected_action_counts_by_capability": dict(Counter(
            row.get("active_developmental_capability", "inactive")
            for row in trace
            if int(row.get("caregiver_protective_support_applied", 0)) == 1
        )),
        "caregiver_protected_action_counts_by_decision_kind": dict(Counter(
            row.get("decision_kind", "unclassified")
            for row in trace
            if int(row.get("caregiver_protective_support_applied", 0)) == 1
        )),
        "decision_kind_counts": dict(Counter(
            row.get("decision_kind", "unclassified") for row in trace
        )),
        "collapse_kind_counts": dict(Counter(
            row.get("collapse_kind", "unclassified") for row in trace
        )),
        "selected_token_counts": dict(Counter(
            row.get("selected_token", "") for row in trace
        )),
        "enacted_token_outcomes": enacted_token_outcomes,
        "enacted_motor_program_outcomes": enacted_motor_program_outcomes,
        "enacted_intent_program_outcomes": enacted_intent_program_outcomes,
        "enacted_development_context_outcomes": (
            enacted_development_context_outcomes
        ),
        "manifold_refinement_exploration_model_count": sum(
            float(row.get("manifold_refinement_exploration_value") or 0.0) > 0.0
            for row in phase_models_after_walk
        ),
        "maximum_manifold_refinement_exploration_value": max(
            float(run.get(
                "maximum_manifold_refinement_exploration_value", 0.0
            )),
            max((
                float(row.get(
                    "manifold_refinement_exploration_value"
                ) or 0.0)
                for row in phase_models_after_walk
            ), default=0.0),
        ),
        "manifold_refinement_exploration_valuation_count": int(run.get(
            "manifold_refinement_exploration_valuation_count", 0
        )),
        "manifold_refinement_question_count": int(run.get(
            "manifold_refinement_question_count", 0
        )),
        "active_manifold_refinement_question_count": int(run.get(
            "active_manifold_refinement_question_count", 0
        )),
        "maximum_manifold_refinement_question_residual_units": int(run.get(
            "maximum_manifold_refinement_question_residual_units", 0
        )),
        "manifold_refinement_scored_model_count": int(run.get(
            "manifold_refinement_scored_model_count", 0
        )),
        "manifold_refinement_positive_progress_model_count": int(run.get(
            "manifold_refinement_positive_progress_model_count", 0
        )),
        "maximum_manifold_refinement_progress_units": int(run.get(
            "maximum_manifold_refinement_progress_units", 0
        )),
        "orientation_class_transition_counts": dict(Counter(
            f"{row.get('orientation_class_before', 0)}->"
            f"{row.get('orientation_class_after', 0)}"
            for row in trace
        )),
        "recovery_mode_action_count": sum(
            float(row.get("recovery_mode_after", 0)) > 0.5
            for row in trace
        ),
        "recovery_mode_at_end": run.get("recovery_mode_at_end", 0),
        "recovery_basin_count": int(run.get("recovery_basin_count", 0)),
        "recovery_basin_transition_count": int(run.get(
            "recovery_basin_transition_count", 0
        )),
        "recovery_basin_action_count": int(run.get(
            "recovery_basin_action_count", 0
        )),
        "recovery_warm_start_count": int(run.get(
            "recovery_warm_start_count", 0
        )),
        "recovery_path_recall_count": int(run.get(
            "recovery_path_recall_count", 0
        )),
        "recovery_path_hint_count": int(run.get(
            "recovery_path_hint_count", 0
        )),
        "recovery_recall_useful_basin_count": int(run.get(
            "recovery_recall_useful_basin_count", 0
        )),
        "recovery_recall_successor_origin_count": int(run.get(
            "recovery_recall_successor_origin_count", 0
        )),
        "recovery_recall_replayable_successor_origin_count": int(run.get(
            "recovery_recall_replayable_successor_origin_count", 0
        )),
        "recovery_recall_admissible_origin_count": int(run.get(
            "recovery_recall_admissible_origin_count", 0
        )),
        "recovery_promotion_audit_count": len(recovery_promotion_rows),
        **{
            f"recovery_promotion_{name}_count": sum(
                int(row.get(f"recovery_promotion_{name}", 0))
                for row in recovery_promotion_rows
            )
            for name in (
                "alphabet_exhausted", "compound", "outcome_progress",
                "postural_progress", "pareto_novel",
                "configuration_changed", "metastable_or_supported", "fallen",
                "structural_ready", "progress_ready", "novel_shape_ready",
                "physical_boundary_ready", "cumulative_boundary_ready",
            )
        },
        **{
            f"recovery_recall_{coordinate}_blocked_origin_count": int(run.get(
                f"recovery_recall_{coordinate}_blocked_origin_count", 0
            ))
            for coordinate in (
                "normalized_height", "vertical_alignment", "support_count",
                "contact_count", "motion_energy",
            )
        },
        "recovery_reanchor_count": int(run.get(
            "recovery_reanchor_count", 0
        )),
        "recovery_program_count": int(run.get(
            "recovery_program_count", 0
        )),
        "recovery_program_repeat_count": int(run.get(
            "recovery_program_repeat_count", 0
        )),
        "recovery_program_termination_count": int(run.get(
            "recovery_program_termination_count", 0
        )),
        "live_recovery_successor_edge_count": sum(
            len(row.get("successor_ordinals") or [])
            for row in (run.get("recovery_basins") or [])
        ),
        "live_recovery_basin_topology": [
            {
                key: row.get(key)
                for key in (
                    "ordinal", "request_seq", "configuration_shape",
                    "incoming_primary_token", "incoming_secondary_token",
                    "incoming_response_frames", "incoming_normalized_height",
                    "normalized_height", "incoming_vertical_alignment",
                    "vertical_alignment", "incoming_motion_energy",
                    "motion_energy", "successor_ordinals",
                )
            } | {"action_count": len(row.get("actions") or [])}
            for row in (run.get("recovery_basins") or [])
        ],
        "post_consolidation_recovery_topology": run.get(
            "post_consolidation_recovery_topology", []
        ),
        "situated_trajectory_context_active_at_end": run.get(
            "situated_trajectory_context_active_at_end", 0
        ),
        "body_reset_count": len(run.get("body_reset_records") or []),
        "body_reset_scenarios": [
            row.get("selected_reset_scenario")
            for row in (run.get("body_reset_records") or [])
        ],
        "maximum_program_width": run.get(
            "maximum_synthesized_motor_program_width", 0
        ),
        "maximum_post_gate_program_width": run.get(
            "maximum_post_gate_motor_program_width",
            max(
                (
                    int(row.get("motor_bundle_width", 0))
                    for row in trace
                    if float(row.get("manifold_bounds_ready", 0.0)) > 0.5
                ),
                default=0,
            ),
        ),
        "curriculum": {
            "stage_ordinal": curriculum.get("stage_ordinal", 0),
            "stage_transition_count": curriculum.get(
                "developmental_stage_transition_count", 0
            ),
            "mastery_count": curriculum.get("mastery_count", 0),
            "goal": curriculum.get("developmental_goal", "inactive"),
            "active_capability": curriculum.get(
                "active_capability", "inactive"
            ),
            "exact_body_recall_count": curriculum.get(
                "exact_body_recall_count", 0
            ),
            "cross_body_warm_start_count": curriculum.get(
                "cross_body_warm_start_count", 0
            ),
            "developmental": curriculum.get("developmental", False),
            "developmental_stages": curriculum.get(
                "developmental_stages", []
            ),
            "locomotor_phenotype_count": curriculum.get(
                "locomotor_phenotype_count", 0
            ),
            "locomotor_phenotype_family_count": curriculum.get(
                "locomotor_phenotype_family_count", 0
            ),
            "locomotor_phenotype_families": curriculum.get(
                "locomotor_phenotype_families", []
            ),
            "locomotor_basin_evidence_window": curriculum.get(
                "locomotor_basin_evidence_window", 0
            ),
            "maximum_locomotor_phenotype_occurrence_count": curriculum.get(
                "maximum_locomotor_phenotype_occurrence_count", 0
            ),
            "locomotor_phenotype_occurrence_histogram": curriculum.get(
                "locomotor_phenotype_occurrence_histogram", {}
            ),
            "locomotor_phenotype_recurrence_leaders": curriculum.get(
                "locomotor_phenotype_recurrence_leaders", []
            ),
            "verified_locomotor_basin_count": curriculum.get(
                "verified_locomotor_basin_count", 0
            ),
            "locomotor_pareto_frontier_count": curriculum.get(
                "locomotor_pareto_frontier_count", 0
            ),
            "retained_experience_count": curriculum.get(
                "retained_experience_count", 0
            ),
            "caregiver_buffered_experience_count": curriculum.get(
                "caregiver_buffered_experience_count", 0
            ),
            "unbuffered_experience_count": curriculum.get(
                "unbuffered_experience_count", 0
            ),
            "sparse_support_ceiling": curriculum.get(
                "sparse_support_ceiling", 0
            ),
            "program_trajectory": curriculum.get("program_trajectory"),
            "development_effector_declared_count": curriculum.get(
                "development_effector_declared_count", 0
            ),
            "development_effector_covered_count": curriculum.get(
                "development_effector_covered_count", 0
            ),
            "development_effector_coverage_complete": curriculum.get(
                "development_effector_coverage_complete", 0
            ),
            "development_effector_coverage_unmeasurable": curriculum.get(
                "development_effector_coverage_unmeasurable", 0
            ),
            "runtime_body_schema_count": curriculum.get(
                "runtime_body_schema_count", 0
            ),
            "runtime_body_affordance_count": curriculum.get(
                "runtime_body_affordance_count", 0
            ),
            "runtime_raw_body_affordance_count": curriculum.get(
                "runtime_raw_body_affordance_count", 0
            ),
            "all_body_schema_count": curriculum.get("all_body_schema_count", 0),
            "all_body_affordance_count": curriculum.get(
                "all_body_affordance_count", 0
            ),
            "all_raw_body_count": curriculum.get("all_raw_body_count", 0),
            "all_raw_body_affordance_count": curriculum.get(
                "all_raw_body_affordance_count", 0
            ),
            "active_capability_diagnostics": curriculum.get(
                "active_capability_diagnostics", {}
            ),
            "developmental_frontier": curriculum.get(
                "developmental_frontier", []
            ),
            "developmental_unresolved_prerequisites": curriculum.get(
                "developmental_unresolved_prerequisites", []
            ),
            "self_learning_plan": curriculum.get("self_learning_plan"),
        },
        "future_manifold": future_manifold,
        "future_manifold_gate_onset_action": gate_onset_action,
        "post_gate_action_count": post_gate_action_count,
        "gate_onset_evidence_present": gate_evidence_present,
        "learning_safety_active": future_manifold.get(
            "learning_safety_active"
        ),
        "cognitive_supervision": cognitive,
        "body_shape_name": run.get("body_shape_name"),
        "actuator_count": run.get("actuator_count"),
        "warm_start_shape_recognized": run.get(
            "warm_start_shape_recognized", 0
        ),
        "warm_start_program_count": run.get("warm_start_program_count", 0),
        "loaded_program_trajectory_shape_count": run.get(
            "motor_library_loaded_program_trajectory_shape_count", 0
        ),
        "loaded_program_trajectory_transition_count": run.get(
            "motor_library_loaded_program_trajectory_transition_count", 0
        ),
        "deployment_program_owner_count": run.get(
            "deployment_program_owner_count", 0
        ),
        "deployment_program_owner_current_context_count": run.get(
            "deployment_program_owner_current_context_count", 0
        ),
        "deployment_program_owner_trajectory_count": run.get(
            "deployment_program_owner_trajectory_count", 0
        ),
        "deployment_program_context_diagnostics": run.get(
            "deployment_program_context_diagnostics", {}
        ),
        "developmental_memory_diagnostics": run.get(
            "developmental_memory_diagnostics", []
        ),
        "late_shape_library_recognition_count": run.get(
            "late_shape_library_recognition_count", 0
        ),
        "partial_trajectory_warm_reuse_count": run.get(
            "partial_trajectory_warm_reuse_count", 0
        ),
        "motor_memory_recall_count": run.get(
            "motor_memory_recall_count", 0
        ),
        "motor_library_loaded_shape_count": run.get(
            "motor_library_loaded_shape_count", 0
        ),
        "motor_library_loaded_program_count": run.get(
            "motor_library_loaded_program_count", 0
        ),
        "motor_library_loaded_developmental_capability_count": run.get(
            "motor_library_loaded_developmental_capability_count", 0
        ),
        "motor_library_saved_shape_count": run.get(
            "motor_library_saved_shape_count", 0
        ),
        "motor_library_saved_program_count": run.get(
            "motor_library_saved_program_count", 0
        ),
        "motor_library_saved_developmental_capability_count": run.get(
            "motor_library_saved_developmental_capability_count", 0
        ),
        "calibration_digest": _digest(run.get("calibration_trace", [])),
        "pre_locomotion_digest": _digest(run.get("pre_locomotion_state", {})),
    }


def _configure(
    protocol: dict,
    actions: int,
    enabled: float,
    *,
    deployment: bool = False,
) -> dict:
    configured = deepcopy(protocol)
    configured["locomotion"]["actions"] = actions
    configured["locomotion"]["modes"] = ["directed_walk"]
    configured["locomotion"]["future_manifold_enabled"] = enabled
    configured["locomotion"][
        "future_manifold_temporal_anchors_enabled"
    ] = enabled
    configured["locomotion"]["developmental_deployment_mode"] = int(
        deployment
    )
    return configured


@contextmanager
def _counterfactual_support_authority(enabled: bool, loss_floor: int):
    """Scope experimental risk-gate authority to exactly one paired arm."""
    names = {
        "HUMANOID_SUPPORT_COUNTERFACTUAL_AUTHORITY": "1" if enabled else "0",
        "HUMANOID_SUPPORT_COUNTERFACTUAL_LOSS_FLOOR": str(loss_floor),
    }
    previous = {name: os.environ.get(name) for name in names}
    os.environ.update(names)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _curriculum_fully_mastered(metrics: dict) -> bool:
    """Recognise graph-authored exhaustion of the finite curriculum."""
    curriculum = metrics.get("curriculum") or {}
    expected = set(developmental_curriculum_contract()["capability_names"])
    mastered = {
        str(stage.get("name"))
        for stage in curriculum.get("developmental_stages") or []
        if isinstance(stage, dict) and stage.get("status") == "mastered"
    }
    return bool(expected) and mastered == expected


def _cognitive_invalid_reasons(metrics: dict) -> list[str]:
    cognitive = metrics.get("cognitive_supervision") or {}
    reasons = []
    if not cognitive:
        return ["cognitive_supervision_evidence_absent"]
    if cognitive.get("experiment_halted_by_checkin", 0):
        reasons.append("cognitive_checkin_terminal")
    if (
        cognitive.get("continuation_authority_at_end") != 1
        and not _curriculum_fully_mastered(metrics)
    ):
        reasons.append("cognitive_continuation_authority_absent")
    return reasons


def _training_completion(
    metrics: dict | None,
    requested_actions: int,
    *,
    library_path: Path,
) -> tuple[bool, list[str]]:
    """Fail closed before a fresh, incomplete artifact reaches paired runs."""
    reasons = []
    if metrics is None:
        return False, ["fresh_training_metrics_absent"]
    if (
        metrics.get("actions_executed") != requested_actions
        and not _curriculum_fully_mastered(metrics)
    ):
        reasons.append("fresh_training_action_budget_not_completed")
    reasons.extend(_cognitive_invalid_reasons(metrics))
    if not library_path.exists():
        reasons.append("fresh_training_library_artifact_absent")
    if metrics.get("motor_library_saved_shape_count", 0) < 1:
        reasons.append("fresh_training_library_shape_evidence_absent")
    return not reasons, reasons


def _locomotion_reached(curriculum: dict) -> bool:
    """Use retained capability evidence, not only the transient active goal."""
    if curriculum.get("goal") == "locomotion":
        return True
    return any(
        stage.get("name") == "independent_walking"
        and stage.get("status") == "mastered"
        for stage in curriculum.get("developmental_stages") or []
        if isinstance(stage, dict)
    )


def _pair_invalid_reasons(
    baseline: dict,
    treatment: dict,
    *,
    evaluation_actions: int,
    calibration_identical: bool,
    pre_locomotion_identical: bool,
    library_metadata: dict,
    protocol_digest: str,
    treatment_protocol_digest: str,
) -> list[str]:
    """Return explicit reasons a paired result cannot support the claim."""
    reasons = []
    if baseline.get("actions_executed") != evaluation_actions or treatment.get(
        "actions_executed"
    ) != evaluation_actions:
        reasons.append("curriculum_action_budget_not_completed")
    if not calibration_identical:
        reasons.append("paired_calibration_mismatch")
    if not pre_locomotion_identical:
        reasons.append("paired_pre_locomotion_state_mismatch")
    if protocol_digest != treatment_protocol_digest:
        reasons.append("paired_protocol_digest_mismatch")

    baseline_future = baseline.get("future_manifold") or {}
    treatment_future = treatment.get("future_manifold") or {}
    if float(baseline_future.get("enabled", 0.0)) > 0.5:
        reasons.append("baseline_manifold_gate_enabled")
    if float(baseline_future.get("temporal_anchors_enabled", 0.0)) > 0.5:
        reasons.append("baseline_temporal_anchors_enabled")
    if float(baseline_future.get("bounds_ready", 0.0)) > 0.5:
        reasons.append("baseline_manifold_bounds_ready")

    treatment_gate_active = bool(
        float(treatment_future.get("enabled", 0.0)) > 0.5
        and float(treatment_future.get("temporal_anchors_enabled", 0.0)) > 0.5
        and float(treatment_future.get("bounds_ready", 0.0)) > 0.5
    )
    if not treatment_gate_active:
        reasons.append("locomotion_manifold_not_reached")
    if treatment_future.get("bounds_provenance") != (
        "receipt_grounded_phase_action_envelope"
    ):
        reasons.append("treatment_bounds_provenance_absent_or_mismatched")
    if treatment.get("learning_safety_active") != 1:
        reasons.append("learning_safety_not_active")

    for label, metrics in (("baseline", baseline), ("treatment", treatment)):
        reasons.extend(
            f"{label}_{reason}" for reason in _cognitive_invalid_reasons(metrics)
        )

    curriculum = treatment.get("curriculum") or {}
    if not _locomotion_reached(curriculum):
        reasons.append("developmental_locomotion_goal_not_reached")

    # Gate-onset evidence is required once a treatment claims activation.  It
    # is optional for old/early probes whose gate is not yet reached.
    if treatment_gate_active and not treatment.get("gate_onset_evidence_present"):
        reasons.append("manifold_gate_onset_evidence_absent")
    if treatment_gate_active and treatment.get("post_gate_action_count", 0) < 1:
        reasons.append("manifold_post_gate_action_evidence_absent")

    if library_metadata.get("semantic_type") == "unknown":
        reasons.append("library_semantic_type_absent")
    if not library_metadata.get("curriculum_contract_matches", True):
        reasons.append("library_curriculum_contract_mismatch")
    return reasons


def _checkpoint(
    metrics: dict,
    *,
    action_budget: int,
    mode: str,
    protocol_digest: str,
    library_metadata: dict | None = None,
    training_complete: bool | None = None,
    training_invalid_reasons: list[str] | None = None,
) -> dict:
    """Summarize one single-arm milestone without launching a paired arm."""
    curriculum = metrics.get("curriculum") or {}
    future = metrics.get("future_manifold") or {}
    goal = curriculum.get("goal", "inactive")
    locomotion_reached = _locomotion_reached(curriculum)
    gate_ready = bool(
        float(future.get("enabled", 0.0)) > 0.5
        and float(future.get("temporal_anchors_enabled", 0.0)) > 0.5
        and float(future.get("bounds_ready", 0.0)) > 0.5
    )
    if mode in {"training", "continue"} and training_complete is False:
        milestone = "incomplete_training"
        recommendation = "do_not_accept_artifact"
    elif gate_ready and locomotion_reached:
        milestone = "manifold_ready"
        recommendation = "paired_evaluation_permitted"
    elif gate_ready:
        milestone = "manifold_ready_pre_locomotion"
        recommendation = "continue_curriculum_before_pairing"
    elif locomotion_reached:
        milestone = "locomotion_reached"
        recommendation = "advance_single_arm_probe_before_pairing"
    elif curriculum.get("stage_ordinal", 0) > 0:
        milestone = "curriculum_advancing"
        recommendation = "continue_to_next_checkpoint"
    else:
        milestone = "pre_locomotion"
        recommendation = "continue_to_next_checkpoint"
    return {
        "mode": mode,
        "action_budget": action_budget,
        "actions_executed": metrics.get("actions_executed", 0),
        "protocol_digest": protocol_digest,
        "library_metadata": library_metadata,
        "training_complete": training_complete,
        "training_invalid_reasons": training_invalid_reasons or [],
        "milestone": milestone,
        "recommendation": recommendation,
        "stage_ordinal": curriculum.get("stage_ordinal", 0),
        "stage_transition_count": curriculum.get("stage_transition_count", 0),
        "mastery_count": curriculum.get("mastery_count", 0),
        "goal": goal,
        "gate_ready": gate_ready,
        "gate_onset_action": metrics.get("future_manifold_gate_onset_action"),
        "post_gate_action_count": metrics.get("post_gate_action_count"),
        "cognitive_invalid_reasons": _cognitive_invalid_reasons(metrics),
        "curriculum_complete": _curriculum_fully_mastered(metrics),
        "action_budget_complete": metrics.get("actions_executed", 0)
        == action_budget,
    }


def run_staged(
    protocol_path: Path,
    *,
    action_budget: int,
    mode: str,
    library_path: Path,
    library_in: Path | None = None,
    trajectory_library_in: Path | None = None,
    drop_program_trajectories: bool = False,
    foveated_exploration_authority: bool = False,
) -> dict:
    """Run exactly one arm at a finite checkpoint.

    ``training`` creates a fresh library. ``continue`` consumes one retained
    library, enables the situated manifold gate, and writes a distinct next
    generation. ``probe`` consumes a library without updating it. No mode runs
    a baseline/treatment pair, so a checkpoint cannot be misreported as one.
    """
    if action_budget not in STAGED_ACTION_BUDGETS:
        raise ValueError(
            "staged action budget must be one of "
            f"{STAGED_ACTION_BUDGETS!r}"
        )
    if mode not in {"training", "continue", "probe"}:
        raise ValueError(
            "staged mode must be 'training', 'continue', or 'probe'"
        )
    if mode in {"continue", "probe"} and library_in is None:
        raise ValueError(f"staged {mode} requires --library-in")
    if mode == "training" and library_in is not None:
        raise ValueError("staged training cannot consume --library-in")
    if trajectory_library_in is not None and drop_program_trajectories:
        raise ValueError(
            "trajectory graft and trajectory ablation are mutually exclusive"
        )
    if mode == "training" and (
        trajectory_library_in is not None or drop_program_trajectories
    ):
        raise ValueError(
            "trajectory graft or ablation requires a retained input library"
        )
    if (
        mode == "continue"
        and library_in is not None
        and library_in.resolve() == library_path.resolve()
    ):
        raise ValueError(
            "staged continuation requires distinct input and output libraries"
        )

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if not protocol.get("curriculum", {}).get("developmental", False):
        raise ValueError("a developmental curriculum protocol is required")
    retained_library = None
    input_library_metadata = None
    if library_in is not None:
        retained_library = json.loads(library_in.read_text(encoding="utf-8"))
        if not isinstance(retained_library, dict):
            raise ValueError("retained motor library must be a JSON object")
        input_library_metadata = _library_metadata(retained_library, protocol)
        if not input_library_metadata.get("curriculum_contract_matches", False):
            raise ValueError(
                "retained motor library curriculum contract does not match"
            )
        if trajectory_library_in is not None:
            trajectory_library = json.loads(
                trajectory_library_in.read_text(encoding="utf-8")
            )
            if not isinstance(trajectory_library, dict):
                raise ValueError("trajectory motor library must be a JSON object")
            trajectory_metadata = _library_metadata(
                trajectory_library, protocol
            )
            if not trajectory_metadata.get(
                "curriculum_contract_matches", False
            ):
                raise ValueError(
                    "trajectory motor library curriculum contract does not match"
                )
            retained_library = deepcopy(retained_library)
            retained_library["version"] = MOTOR_LIBRARY_VERSION
            for key in (
                "program_trajectory_shapes",
                "program_trajectory_endpoint_programs",
            ):
                retained_library[key] = deepcopy(
                    trajectory_library.get(key, [])
                )
            input_library_metadata = _library_metadata(
                retained_library, protocol
            )
            input_library_metadata["trajectory_variant"] = "grafted"
            input_library_metadata["trajectory_source"] = str(
                trajectory_library_in
            )
        elif drop_program_trajectories:
            retained_library = deepcopy(retained_library)
            retained_library["program_trajectory_shapes"] = []
            retained_library["program_trajectory_endpoint_programs"] = []
            input_library_metadata = _library_metadata(
                retained_library, protocol
            )
            input_library_metadata["trajectory_variant"] = "ablated"
    configured = _configure(
        protocol,
        action_budget,
        0.0 if mode == "training" else 1.0,
        deployment=mode == "probe",
    )
    configured["locomotion"][
        "foveated_program_exploration_authority"
    ] = float(foveated_exploration_authority)
    started = time.perf_counter()
    run = _run_arm(
        configured,
        "directed_walk",
        motor_library=retained_library,
        motor_library_out=(
            library_path if mode in {"training", "continue"} else None
        ),
    )
    metrics = _metrics(run)
    training_complete = None
    training_invalid_reasons: list[str] = []
    if mode in {"training", "continue"}:
        training_complete, training_invalid_reasons = _training_completion(
            metrics,
            action_budget,
            library_path=library_path,
        )
        # The artifact is deliberately retained even when this is false.  A
        # staged checkpoint is diagnostic state; it is never allowed to erase
        # evidence of a halted run.
        library_metadata = _read_library_metadata(library_path, protocol)
    else:
        library_metadata = _read_library_metadata(library_in, protocol)
    staged_result_valid = (
        training_complete
        if mode in {"training", "continue"}
        else (
            metrics["actions_executed"] == action_budget
            and not _cognitive_invalid_reasons(metrics)
        )
    )
    result = {
        "experiment": "humanoid_future_manifold_curriculum_staged",
        "protocol_path": str(protocol_path.resolve().relative_to(ROOT)),
        "protocol_digest": _digest(protocol),
        "seed": protocol["seed"],
        "training_actions": (
            action_budget if mode in {"training", "continue"} else None
        ),
        "evaluation_actions": action_budget if mode == "probe" else None,
        "runtime_seconds": time.perf_counter() - started,
        "mode": mode,
        "foveated_exploration_authority": bool(
            foveated_exploration_authority
        ),
        "library_in": str(library_in) if library_in is not None else None,
        "trajectory_library_in": (
            str(trajectory_library_in)
            if trajectory_library_in is not None else None
        ),
        "program_trajectories_ablated": bool(drop_program_trajectories),
        "library_out": (
            str(library_path) if mode in {"training", "continue"} else None
        ),
        "input_library_metadata": input_library_metadata,
        "library_metadata": library_metadata,
        "staged_result_valid": staged_result_valid,
        "training_complete": training_complete,
        "training_invalid_reasons": training_invalid_reasons,
        "metrics": metrics,
    }
    result["checkpoint"] = _checkpoint(
        metrics,
        action_budget=action_budget,
        mode=mode,
        protocol_digest=result["protocol_digest"],
        library_metadata=library_metadata,
        training_complete=training_complete,
        training_invalid_reasons=training_invalid_reasons,
    )
    return result


def run(
    protocol_path: Path,
    *,
    training_actions: int,
    evaluation_actions: int,
    library_path: Path,
    library_in: Path | None = None,
    counterfactual_treatment_authority: bool = False,
    counterfactual_loss_floor: int = 2,
) -> dict:
    if training_actions < 1 or evaluation_actions < 1:
        raise ValueError("training and evaluation actions must be positive")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    curriculum = protocol.get("curriculum")
    if not curriculum or not curriculum.get("developmental", False):
        raise ValueError("a developmental curriculum protocol is required")

    protocol_digest = _digest(protocol)
    curriculum_contract_digest = developmental_curriculum_contract()[
        "ontology_sha256"
    ]

    if library_in is None:
        training_protocol = _configure(protocol, training_actions, 0.0)
        started = time.perf_counter()
        training_run = _run_arm(
            training_protocol,
            "directed_walk",
            motor_library_out=library_path,
        )
        training_seconds = time.perf_counter() - started
        training_metrics = _metrics(training_run)
        training_complete, training_invalid_reasons = _training_completion(
            training_metrics,
            training_actions,
            library_path=library_path,
        )
        if not training_complete:
            raise RuntimeError(
                "fresh training artifact rejected: "
                + ", ".join(training_invalid_reasons)
            )
        del training_run
        gc.collect()
        effective_library_path = library_path
        training_source = "fresh_developmental_curriculum"
    else:
        effective_library_path = library_in
        training_seconds = 0.0
        training_metrics = None
        training_source = "frozen_developmental_curriculum_artifact"

    library_bytes = effective_library_path.read_bytes()
    library_sha256 = hashlib.sha256(library_bytes).hexdigest()
    motor_library = json.loads(library_bytes)
    library_metadata = _library_metadata(motor_library, protocol)

    baseline_protocol = _configure(
        protocol, evaluation_actions, 0.0, deployment=True
    )
    treatment_protocol = _configure(
        protocol, evaluation_actions, 1.0, deployment=True
    )

    started = time.perf_counter()
    with _counterfactual_support_authority(False, counterfactual_loss_floor):
        baseline_run = _run_arm(
            baseline_protocol,
            "directed_walk",
            motor_library=motor_library,
        )
    baseline_seconds = time.perf_counter() - started
    baseline_metrics = _metrics(baseline_run)
    baseline_calibration = _digest(baseline_run["calibration_trace"])
    baseline_pre_locomotion = _digest(baseline_run["pre_locomotion_state"])
    del baseline_run
    gc.collect()

    started = time.perf_counter()
    with _counterfactual_support_authority(
        counterfactual_treatment_authority,
        counterfactual_loss_floor,
    ):
        treatment_run = _run_arm(
            treatment_protocol,
            "directed_walk",
            motor_library=motor_library,
        )
    treatment_seconds = time.perf_counter() - started
    treatment_metrics = _metrics(treatment_run)
    treatment_calibration = _digest(treatment_run["calibration_trace"])
    treatment_pre_locomotion = _digest(
        treatment_run["pre_locomotion_state"]
    )

    treatment_gate_active = bool(
        treatment_metrics["future_manifold"].get("enabled", 0.0) > 0.5
        and treatment_metrics["future_manifold"].get(
            "temporal_anchors_enabled", 0.0
        ) > 0.5
        and treatment_metrics["future_manifold"].get("bounds_ready", 0.0)
        > 0.5
    )
    invalid_reasons = _pair_invalid_reasons(
        baseline_metrics,
        treatment_metrics,
        evaluation_actions=evaluation_actions,
        calibration_identical=baseline_calibration == treatment_calibration,
        pre_locomotion_identical=(
            baseline_pre_locomotion == treatment_pre_locomotion
        ),
        library_metadata=library_metadata,
        protocol_digest=protocol_digest,
        treatment_protocol_digest=protocol_digest,
    )
    action_budget_completed = (
        baseline_metrics["actions_executed"] == evaluation_actions
        and treatment_metrics["actions_executed"] == evaluation_actions
    )
    manifold_test_valid = not invalid_reasons

    return {
        "experiment": "humanoid_future_manifold_curriculum_paired",
        "manifold_test_valid": manifold_test_valid,
        "invalid_reasons": invalid_reasons,
        "action_budget_completed": action_budget_completed,
        "protocol_path": str(protocol_path.resolve().relative_to(ROOT)),
        "protocol_digest": protocol_digest,
        "curriculum_contract_digest": curriculum_contract_digest,
        "seed": protocol["seed"],
        "training_actions": training_actions,
        "evaluation_actions": evaluation_actions,
        "training_source": training_source,
        "counterfactual_treatment_authority": (
            counterfactual_treatment_authority
        ),
        "counterfactual_loss_floor": counterfactual_loss_floor,
        "training_complete": (
            True if library_in is not None else training_complete
        ),
        "training_invalid_reasons": (
            [] if library_in is not None else training_invalid_reasons
        ),
        "training_library": str(
            effective_library_path.resolve().relative_to(ROOT)
        ),
        "training_library_sha256": library_sha256,
        "training_library_metadata": library_metadata,
        "training_runtime_seconds": training_seconds,
        "training": training_metrics,
        "calibration_identical": baseline_calibration == treatment_calibration,
        "pre_locomotion_state_identical": (
            baseline_pre_locomotion == treatment_pre_locomotion
        ),
        "baseline_runtime_seconds": baseline_seconds,
        "treatment_runtime_seconds": treatment_seconds,
        "baseline": baseline_metrics,
        "treatment": treatment_metrics,
        "delta": {
            key: treatment_metrics[key] - baseline_metrics[key]
            for key in (
                "directed_progress",
                "minimum_height",
                "lateral_offset",
                "support_alternations",
                "compound_action_count",
                "maximum_program_width",
            )
        },
        "curriculum_delta": {
            key: treatment_metrics["curriculum"][key]
            - baseline_metrics["curriculum"][key]
            for key in (
                "stage_ordinal",
                "stage_transition_count",
                "mastery_count",
                "exact_body_recall_count",
                "cross_body_warm_start_count",
            )
        },
        "treatment_gate_active": treatment_gate_active,
        "gate_onset": {
            "baseline_action": baseline_metrics.get(
                "future_manifold_gate_onset_action"
            ),
            "treatment_action": treatment_metrics.get(
                "future_manifold_gate_onset_action"
            ),
            "baseline_post_gate_action_count": baseline_metrics.get(
                "post_gate_action_count"
            ),
            "treatment_post_gate_action_count": treatment_metrics.get(
                "post_gate_action_count"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--training-actions", type=int, default=360)
    parser.add_argument("--evaluation-actions", type=int, default=360)
    parser.add_argument("--library-out", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--library-in", type=Path)
    parser.add_argument(
        "--trajectory-library-in",
        type=Path,
        help=(
            "graft only output-null program trajectory shapes/endpoints from "
            "this library onto --library-in for a causal probe"
        ),
    )
    parser.add_argument(
        "--drop-program-trajectories",
        action="store_true",
        help="probe the retained library with program trajectories removed",
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--counterfactual-treatment-authority",
        action="store_true",
        help="enable learned minimum-support risk authority only in treatment",
    )
    parser.add_argument(
        "--counterfactual-loss-floor",
        type=int,
        default=2,
        help="minimum unsupported manifold escape count for treatment support",
    )
    parser.add_argument(
        "--staged-mode",
        choices=("training", "continue", "probe"),
        help=(
            "run one finite checkpoint arm instead of the paired experiment"
        ),
    )
    parser.add_argument(
        "--staged-actions",
        type=int,
        choices=STAGED_ACTION_BUDGETS,
        default=48,
        help="single-arm checkpoint budget (48, 96, 192, or 360)",
    )
    parser.add_argument(
        "--foveated-exploration-authority",
        action="store_true",
        help=(
            "enable capability-local manifold refinement exploration in the "
            "single staged arm"
        ),
    )
    args = parser.parse_args()
    if args.staged_mode is not None:
        result = run_staged(
            args.protocol,
            action_budget=args.staged_actions,
            mode=args.staged_mode,
            library_path=args.library_out,
            library_in=args.library_in,
            trajectory_library_in=args.trajectory_library_in,
            drop_program_trajectories=args.drop_program_trajectories,
            foveated_exploration_authority=(
                args.foveated_exploration_authority
            ),
        )
    else:
        result = run(
            args.protocol,
            training_actions=args.training_actions,
            evaluation_actions=args.evaluation_actions,
            library_path=args.library_out,
            library_in=args.library_in,
            counterfactual_treatment_authority=(
                args.counterfactual_treatment_authority
            ),
            counterfactual_loss_floor=args.counterfactual_loss_floor,
        )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
