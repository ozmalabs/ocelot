"""Development-only paired goal-action and cross-context transfer panel."""
from __future__ import annotations

from dataclasses import asdict
import time
from typing import Iterable

from evaluation.ousiometrics.native_adapter import NativeOusiometricInvestigation
from evaluation.ousiometrics.worlds import (
    FactorProfile, SocialRepairWorld, ToolInterventionWorld,
)

PRIMARY_ARMS = (
    "shared_basis_64bit_fixed_l1",
    "eq4_rotation_64bit_fixed_l1",
)
CONTROL_ARMS = (
    "shared_basis_64bit_transported_l1",
    "eq4_rotation_64bit_transported_l1",
    "random_rotation_dev_64bit_fixed_l1",
    "eq4_rotation_8bit_fixed_l1",
)
LEARNING_HORIZONS = (0, 1, 2, 4)
TRAINING_ACTIONS = ("apply_small", "apply_large", "apply_small", "apply_large")
SOCIAL_TRAINING_ACTIONS = ("clarify", "fulfill", "repair", "ignore")


def _verified_action(learner: NativeOusiometricInvestigation, *, world: ToolInterventionWorld,
                     action: str, split: str = "training") -> dict:
    before = world.agent_view()
    if action not in before["available_actions"]:
        return {"verified": False, "authorized": False, "action": action,
                "event_id": None, "goal_satisfied": False}
    receipt = world.apply_action(action, source_epoch=3, model_epoch=2, frame_epoch=1)
    verified = world.verify_receipt(receipt) and receipt.action_authorized
    if verified:
        projected = learner.ingest_verified_world_receipt(
            world=world, receipt=receipt, before_view=before, split=split)
    else:
        projected = None
    return {"verified": bool(verified), "authorized": bool(receipt.action_authorized),
            "action": action, "event_id": receipt.event_id,
            "goal_satisfied": bool(receipt.goal_satisfied),
            "adverse_consequence": bool(receipt.adverse_consequence),
            "projection_verified": bool(projected and projected.verified)}


def _score_checkpoint(frame_id: str, *, profile: FactorProfile, seed: int,
                      horizon: int, source_profile: FactorProfile,
                      source_actions: tuple[str, ...]) -> dict:
    """Fit on one matched source prefix, verify changed-map target evidence, then score fresh."""
    started = time.perf_counter()
    learner = NativeOusiometricInvestigation(frame_id, budget=1000.0)
    source_rows = []
    for index, action in enumerate(source_actions[:horizon]):
        source = ToolInterventionWorld(
            source_profile, seed=seed + 100 + index,
            episode_id=f"source-{seed}-{index}",
            context_id=f"source-context-{seed}-{index}")
        source_rows.append(_verified_action(learner, world=source, action=action))

    # A changed consequence map and a new object/context are calibrated using
    # one ordinary, world-verified target action on every representation arm.
    target_calibration = ToolInterventionWorld(
        profile, seed=seed + 500, episode_id=f"target-calibration-{seed}-{horizon}",
        context_id=f"target-calibration-context-{seed}-{horizon}")
    calibration = _verified_action(learner, world=target_calibration,
                                   action="apply_small", split="training")
    learner.learner.settle()

    world = ToolInterventionWorld(
        profile, seed=seed + 900 + horizon,
        episode_id=f"score-{seed}-{horizon}",
        context_id=f"fresh-score-context-{seed}-{horizon}")
    before = world.agent_view()
    legal = tuple(action for action in before["available_actions"]
                  if action in {"apply_small", "apply_large"})
    target = float(before["task"]["target"])
    decision = learner.select_goal_action(
        query_id=f"goal-query:{seed}:{horizon}", coordinates=before["coordinates"],
        legal_actions=legal, goal_value=target - 0.5)
    selected = decision.get("action_id") if decision else None
    receipt_row = _verified_action(learner, world=world, action=selected) if selected else None
    receipt_verified = bool(receipt_row and receipt_row["verified"])
    success = bool(receipt_verified and receipt_row["goal_satisfied"])
    footprint = learner.graph_footprint()
    accounting = learner.learner.accounting
    frame = learner.frame
    # AUC is computed across independent scored checkpoint worlds by the panel.
    # No outcome is dropped, including abstentions and failed proposals.
    return {
        "frame_id": frame_id, "seed": int(seed), "horizon": int(horizon),
        "world_family": world.family, "source_profile": asdict(source_profile),
        "target_profile": asdict(profile), "source_contexts": [
            f"source-context-{seed}-{index}" for index in range(horizon)],
        "source_bindings": ["standard-tool" for _ in range(horizon)],
        "target_calibration_context": target_calibration.context_id,
        "target_calibration_binding": target_calibration.object_id,
        "score_context": world.context_id, "target_binding": world.object_id,
        "target_changed_from_source": profile != source_profile,
        "source_training": source_rows, "target_calibration": calibration,
        "target_verification_before_score": bool(calibration["verified"]
                                                  and calibration["projection_verified"]),
        "decision": decision, "action": selected,
        "receipt_verified": receipt_verified, "goal_satisfied": success,
        "goal_error": decision.get("goal_error") if decision else None,
        "adverse_consequence": bool(receipt_row and receipt_row.get("adverse_consequence")),
        "status": "scored" if receipt_verified else "abstained_or_unverified",
        "target_actions": int(accounting.target_actions),
        "evidence_events": len(learner._events),
        "native_steps": int(learner.native_steps + accounting.native_rule_steps),
        # Each source, calibration and scored receipt passes the simulator's
        # exact equality verifier before it can enter the graph.
        "exact_checks": int(sum(row["verified"] for row in source_rows)
                            + calibration["verified"] + receipt_verified),
        "query_count": int(len(learner.s.nodes("OusiometricMetricQuery"))),
        "failed_or_abstained_actions": int(not receipt_verified),
        "failed_proposals": int(not selected or not receipt_verified),
        "frame_mapping_bits": float(frame["forward_inverse_map_bits"]),
        "metric_policy_bits": float(frame["metric_policy_bits"]),
        "coordinate_bits": float(frame["coordinates_bits"]),
        "total_representation_bits": float(frame["total_representation_bits"]),
        "decoder_graph_bytes": int(footprint["bytes"]),
        "decoder_graph_nodes": int(footprint["nodes"]),
        "wall_time_seconds": time.perf_counter() - started,
        "thinking_budget_remaining": [float(learner.s.node(n)["attrs"].get("remaining", 0.0))
                                      for n in learner.s.nodes("ThinkingBudget")],
        "heldout_used_for_selection": False,
    }


def _auc(points: list[dict]) -> float:
    """Trapezoidal AUC over fixed horizons; every checkpoint contributes its outcome."""
    if len(points) < 2:
        return float(points[0]["goal_satisfied"]) if points else 0.0
    points = sorted(points, key=lambda row: row["horizon"])
    width = points[-1]["horizon"] - points[0]["horizon"]
    if width <= 0:
        return sum(float(row["goal_satisfied"]) for row in points) / len(points)
    area = sum((points[i]["horizon"] - points[i - 1]["horizon"])
               * (float(points[i]["goal_satisfied"])
                  + float(points[i - 1]["goal_satisfied"])) / 2
               for i in range(1, len(points)))
    return area / width


def run_tool_trial(frame_id: str, *, profile: FactorProfile, seed: int,
                   intervention_order: Iterable[str] = TRAINING_ACTIONS) -> dict:
    """Run one matched horizon series with fresh scoring worlds per checkpoint."""
    actions = tuple(intervention_order)
    horizons = tuple(h for h in LEARNING_HORIZONS if h <= len(actions))
    source_profile = FactorProfile(.2, 0.0, 0.0, 0.0, 0.0, novelty=0.0)
    target_capacity = profile.effect_capacity if abs(profile.effect_capacity - .2) > 1e-9 else .8
    profile = FactorProfile(target_capacity, profile.adverse_probability,
                            profile.constraint_strength, profile.pleasantness_bias,
                            profile.outcome_noise, novelty=max(.8, profile.novelty))
    checkpoints = [_score_checkpoint(frame_id, profile=profile, seed=seed,
                                     horizon=horizon, source_profile=source_profile,
                                     source_actions=actions)
                  for horizon in horizons]
    return {
        "frame_id": frame_id, "seed": int(seed),
        "world_family": "tool_intervention",
        "source_profile": asdict(source_profile), "target_profile": asdict(profile),
        "checkpoints": checkpoints,
        "learning_curve": [float(row["goal_satisfied"]) for row in checkpoints],
        "learning_horizons": [int(row["horizon"]) for row in checkpoints],
        "learning_auc": _auc(checkpoints),
        "target_verification_at_every_horizon": all(
            row["target_verification_before_score"] for row in checkpoints),
        "heldout_used_for_selection": False,
    }


def _verified_social_action(learner: NativeOusiometricInvestigation, *,
                            world: SocialRepairWorld, action: str) -> dict:
    before = world.agent_view()
    if action not in before["available_actions"]:
        return {"verified": False, "action": action, "event_id": None,
                "goal_satisfied": False}
    receipt = world.apply_action(action, source_epoch=3, model_epoch=2, frame_epoch=1)
    verified = world.verify_receipt(receipt) and receipt.action_authorized
    projected = learner.ingest_verified_world_receipt(
        world=world, receipt=receipt, before_view=before, split="training") if verified else None
    return {"verified": bool(verified), "action": action, "event_id": receipt.event_id,
            "goal_satisfied": bool(receipt.goal_satisfied),
            "adverse_consequence": bool(receipt.adverse_consequence),
            "projection_verified": bool(projected and projected.verified)}


def _score_social_checkpoint(frame_id: str, *, profile: FactorProfile, seed: int,
                             horizon: int, source_profile: FactorProfile,
                             source_actions: tuple[str, ...]) -> dict:
    started = time.perf_counter()
    learner = NativeOusiometricInvestigation(frame_id, budget=1000.0)
    source_rows = []
    for index, action in enumerate(source_actions[:horizon]):
        source = SocialRepairWorld(
            source_profile, seed=seed + 1100 + index,
            episode_id=f"social-source-{seed}-{index}",
            context_id=f"social-source-context-{seed}-{index}")
        source_rows.append(_verified_social_action(learner, world=source, action=action))
    target_calibration = SocialRepairWorld(
        profile, seed=seed + 1500,
        episode_id=f"social-target-calibration-{seed}-{horizon}",
        context_id=f"social-target-calibration-context-{seed}-{horizon}")
    calibration = _verified_social_action(learner, world=target_calibration, action="decline")
    learner.learner.settle()

    world = SocialRepairWorld(
        profile, seed=seed + 1900 + horizon,
        episode_id=f"social-score-{seed}-{horizon}",
        context_id=f"social-fresh-score-context-{seed}-{horizon}")
    before = world.agent_view()
    legal = tuple(before["available_actions"])
    target = float(before["task"]["target"])
    decision = learner.select_goal_action(
        query_id=f"social-goal-query:{seed}:{horizon}", coordinates=before["coordinates"],
        legal_actions=legal, goal_value=target - 0.5)
    selected = decision.get("action_id") if decision else None
    result = (_verified_social_action(learner, world=world, action=selected)
              if selected else None)
    receipt_verified = bool(result and result["verified"])
    success = bool(receipt_verified and result["goal_satisfied"])
    footprint = learner.graph_footprint()
    accounting = learner.learner.accounting
    frame = learner.frame
    return {
        "frame_id": frame_id, "seed": int(seed), "horizon": int(horizon),
        "world_family": world.family, "source_profile": asdict(source_profile),
        "target_profile": asdict(profile),
        "source_contexts": [f"social-source-context-{seed}-{i}" for i in range(horizon)],
        "source_bindings": [f"requester-{seed + 1100 + i}" for i in range(horizon)],
        "target_calibration_context": target_calibration.context_id,
        "target_calibration_binding": target_calibration.object_id,
        "score_context": world.context_id, "target_binding": world.object_id,
        "target_changed_from_source": profile != source_profile,
        "source_training": source_rows, "target_calibration": calibration,
        "target_verification_before_score": bool(calibration["verified"]
                                                  and calibration["projection_verified"]),
        "decision": decision, "action": selected,
        "receipt_verified": receipt_verified, "goal_satisfied": success,
        "goal_error": decision.get("goal_error") if decision else None,
        "adverse_consequence": bool(result and result.get("adverse_consequence")),
        "status": "scored" if receipt_verified else "abstained_or_unverified",
        "target_actions": int(accounting.target_actions),
        "evidence_events": len(learner._events),
        "native_steps": int(learner.native_steps + accounting.native_rule_steps),
        "exact_checks": int(sum(row["verified"] for row in source_rows)
                            + calibration["verified"] + receipt_verified),
        "query_count": int(len(learner.s.nodes("OusiometricMetricQuery"))),
        "failed_or_abstained_actions": int(not receipt_verified),
        "failed_proposals": int(not selected or not receipt_verified),
        "frame_mapping_bits": float(frame["forward_inverse_map_bits"]),
        "metric_policy_bits": float(frame["metric_policy_bits"]),
        "coordinate_bits": float(frame["coordinates_bits"]),
        "total_representation_bits": float(frame["total_representation_bits"]),
        "decoder_graph_bytes": int(footprint["bytes"]),
        "decoder_graph_nodes": int(footprint["nodes"]),
        "wall_time_seconds": time.perf_counter() - started,
        "heldout_used_for_selection": False,
    }


def development_panel(*, seeds: Iterable[int] = (28091, 28092),
                      profiles: Iterable[FactorProfile] | None = None,
                      frames: Iterable[str] = PRIMARY_ARMS + CONTROL_ARMS,
                      families: Iterable[str] = ("tool_intervention", "social_request_repair")) -> dict:
    """Run all fixed arms on the same deterministic training and scoring allocation."""
    seeds = tuple(int(seed) for seed in seeds)
    frames = tuple(frames)
    families = tuple(families)
    if not set(families) <= {"tool_intervention", "social_request_repair"}:
        raise ValueError("unknown development world family")
    profiles = tuple(profiles or (
        FactorProfile(.8, .0, .0, .0, .0),
        FactorProfile(.8, .8, .0, .0, .0),
    ))
    rows = []
    for seed_index, seed in enumerate(seeds):
        # A seed determines the same consequence map for all arms; map assignment
        # does not depend on frame identity or outcome.
        profile = profiles[seed_index % len(profiles)]
        for frame in frames:
            if "tool_intervention" in families:
                rows.append(run_tool_trial(frame, profile=profile, seed=seed))
            if "social_request_repair" in families:
                source_profile = FactorProfile(.2, 0.0, 0.0, 0.0, 0.0)
                target_capacity = profile.effect_capacity if abs(profile.effect_capacity - .2) > 1e-9 else .8
                target_profile = FactorProfile(target_capacity, profile.adverse_probability,
                                               profile.constraint_strength, profile.pleasantness_bias,
                                               profile.outcome_noise, novelty=.8)
                horizons = tuple(h for h in LEARNING_HORIZONS if h <= len(SOCIAL_TRAINING_ACTIONS))
                checkpoints = [_score_social_checkpoint(
                    frame, profile=target_profile, seed=seed, horizon=horizon,
                    source_profile=source_profile, source_actions=SOCIAL_TRAINING_ACTIONS)
                    for horizon in horizons]
                rows.append({
                    "frame_id": frame, "seed": seed,
                    "world_family": "social_request_repair",
                    "source_profile": asdict(source_profile),
                    "target_profile": asdict(target_profile),
                    "checkpoints": checkpoints,
                    "learning_curve": [float(row["goal_satisfied"]) for row in checkpoints],
                    "learning_horizons": [int(row["horizon"]) for row in checkpoints],
                    "learning_auc": _auc(checkpoints),
                    "target_verification_at_every_horizon": all(
                        row["target_verification_before_score"] for row in checkpoints),
                    "heldout_used_for_selection": False,
                })
    by_arm = {}
    for frame in frames:
        arm = [row for row in rows if row["frame_id"] == frame]
        by_arm[frame] = {
            "n": len(arm),
            "mean_learning_auc": sum(row["learning_auc"] for row in arm) / max(1, len(arm)),
            "mean_success_rate": sum(sum(row["learning_curve"]) / max(1, len(row["learning_curve"]))
                                      for row in arm) / max(1, len(arm)),
            "abstention_rate": sum(sum(c["failed_or_abstained_actions"] for c in row["checkpoints"])
                                    for row in arm) / max(1, sum(len(row["checkpoints"]) for row in arm)),
            "mean_native_steps": sum(sum(c["native_steps"] for c in row["checkpoints"])
                                      for row in arm) / max(1, len(arm)),
            "mean_target_actions": sum(sum(c["target_actions"] for c in row["checkpoints"])
                                        for row in arm) / max(1, len(arm)),
            "mean_decoder_graph_bytes": sum(sum(c["decoder_graph_bytes"] for c in row["checkpoints"])
                                             for row in arm) / max(1, len(arm)),
        }
    by_arm_family = {}
    for frame in frames:
        for family in families:
            arm = [row for row in rows if row["frame_id"] == frame
                   and row["world_family"] == family]
            by_arm_family[f"{frame}:{family}"] = {
                "n": len(arm),
                "mean_learning_auc": sum(row["learning_auc"] for row in arm) / max(1, len(arm)),
                "mean_success_rate": sum(sum(row["learning_curve"]) / max(1, len(row["learning_curve"]))
                                          for row in arm) / max(1, len(arm)),
            }
    return {
        "panel": "p28_tool_action_development_v2", "split": "development",
        "primary_arms": list(PRIMARY_ARMS), "control_arms": list(CONTROL_ARMS),
        "learning_horizons": list(LEARNING_HORIZONS),
        "profiles": [asdict(profile) for profile in profiles],
        "rows": rows, "by_arm": by_arm,
        "by_arm_family": by_arm_family,
        "primary_status": "development_only_no_preregistered_inference",
        "goal_choices_native": True, "host_selects_action": False,
        "all_failures_retained": True,
    }


__all__ = ["CONTROL_ARMS", "LEARNING_HORIZONS", "PRIMARY_ARMS",
           "development_panel", "run_tool_trial"]
