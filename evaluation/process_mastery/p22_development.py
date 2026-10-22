"""Reproducible P22 training-proposal probes on non-held-out worlds."""
from __future__ import annotations

from evaluation.process_mastery.checkpoint_world_adapter import (
    score_unapproved_candidate_validation_panel,
)
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2, generate_loopover_world_v2,
)
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate,
)
from evaluation.process_mastery.p22_resource_accounting import (
    snapshot_native_resources,
)
from substrate.seed_loader import manifest_for


_FAMILIES = {
    "d4": (generate_d4_world_v2, 4),
    "loopover": (generate_loopover_world_v2, 9),
}


def run_p22_training_proposal_probe(*, family: str,
                                    training_draws: tuple[int, int],
                                    validation_draws: tuple[int, ...],
                                    search_ticks: int = 30) -> dict:
    """Run native search on two distinct same-goal training worlds and score every proposal.

    The second training draw must independently generate the same task goal so
    native qualification can check the same expression on a distinct world
    identity. Every graph candidate is evaluated; this function never chooses
    or approves a candidate and has no held-out input path.
    """
    if family not in _FAMILIES:
        raise ValueError("unsupported P22 development family")
    generator, size = _FAMILIES[family]
    if (len(training_draws) != 2 or training_draws[0] == training_draws[1]
            or len(set(validation_draws)) != len(validation_draws)
            or not validation_draws
            or any(isinstance(draw, bool) or not isinstance(draw, int)
                   or draw < 0 or draw >= 1000
                   for draw in (*training_draws, *validation_draws))
            or isinstance(search_ticks, bool) or not isinstance(search_ticks, int)
            or search_ticks <= 0):
        raise ValueError("probe requires two distinct training draws and unique validation draws")
    training_worlds = [generator(split="train", draw=draw) for draw in training_draws]
    if (training_worlds[0]["hidden_target_params"]
            != training_worlds[1]["hidden_target_params"]):
        raise ValueError("training draws must independently generate the same qualification goal")
    validation_worlds = [agent_view(generator(split="validation", draw=draw))
                         for draw in validation_draws]
    held = training_worlds[0]["held_processes"]
    if len(training_worlds[0]["initial_state"]) != size:
        raise ValueError("registered world has an unexpected state size")

    agent = Agent(track_i=False, extra_seeds=("open_process_search",),
        policy_overrides={
            "OpenProcessSearchPolicy": {"enabled": 1.0,
                "max_attempts": 30000.0, "max_candidates": 16.0},
            "ProcessSchemaPolicy": {"enabled": 1.0}},
        budget={"enabled": 1.0, "remaining": 100000.0,
            "capacity": 100000.0, "last_refill_epoch": 0.0,
            "refill_per_epoch": 0.0})
    try:
        domain = agent.add_domain("p22-development", "permutation",
            [training_worlds[0]["initial_state"]], held)
        for schema in agent.nodes("ProcessSchema"):
            if agent.attrs(schema).get("domain") == "p22-development":
                agent.s.add_edge(domain, "has_held_process", schema, {})
        agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
        agent.native.load_seed_manifest(manifest_for("independent_improvement"), agent.ag)
        agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)

        for trial, world in enumerate(training_worlds, start=1):
            task = agent.add_solve_task("p22-development", world["initial_state"],
                world["goal_state"], training_trial_key=world["world_id"],
                split="training")
            # The task pool contains an observed impasse so this probe begins
            # at generic native invention, with no host-selected operator.
            agent.s.set_attr(task, "status", "stuck")
            for _ in range(search_ticks):
                agent.s.tick(4000)
            if trial == 1:
                candidates = [candidate for candidate in agent.nodes("OpenProcessCandidate")
                    if agent.attrs(candidate).get("status") == "unapproved_candidate"]
                if not candidates:
                    raise RuntimeError("native search produced no candidate on the first training task")
                for candidate in candidates:
                    attest_open_process_candidate(agent, candidate)

        for candidate in agent.nodes("OpenProcessCandidate"):
            if (agent.attrs(candidate).get("status") == "unapproved_candidate"
                    and agent.attrs(candidate).get("expression_digest_status") != "verified"):
                attest_open_process_candidate(agent, candidate)
        for _ in range(8):
            agent.s.tick(4000)

        candidate_rows = []
        for candidate in agent.nodes("OpenProcessCandidate"):
            attrs = agent.attrs(candidate)
            if attrs.get("status") != "unapproved_candidate":
                continue
            proposals = [proposal for proposal in agent.nodes("IndependentImprovementProposal")
                if agent.native.neighbours(proposal, "proposes_native_candidate") == [candidate]]
            qualifications = [qualification
                for proposal in proposals
                for qualification in agent.native.neighbours(proposal, "has_native_qualification")]
            qualification_rows = []
            for proposal in proposals:
                for qualification in agent.native.neighbours(proposal, "has_native_qualification"):
                    trial_attempts = agent.native.neighbours(qualification, "counts_native_trial")
                    trial_tasks = [agent.native.neighbours(attempt, "about_task")
                                   for attempt in trial_attempts]
                    qualification_rows.append({
                        "qualification_id": str(qualification),
                        "status": agent.attrs(qualification).get("status"),
                        "declared_trial_count": agent.attrs(qualification).get("trial_count"),
                        "attempt_ids": [str(attempt) for attempt in trial_attempts],
                        "task_ids": [str(tasks[0]) if len(tasks) == 1 else None
                                     for tasks in trial_tasks],
                        "training_trial_keys": [agent.attrs(tasks[0]).get("training_trial_key")
                                      if len(tasks) == 1 else None for tasks in trial_tasks],
                    })
            panel = score_unapproved_candidate_validation_panel(
                agent, candidate, validation_worlds)
            candidate_rows.append({
                "candidate_id": str(candidate),
                "expression_digest": attrs.get("expression_digest"),
                "expression_key": attrs.get("expression_key"),
                "params": attrs.get("params"),
                "status": attrs.get("status"),
                "proposal_count": len(proposals),
                "proposals": [{"proposal_id": str(proposal),
                    "status": agent.attrs(proposal).get("status"),
                    "source_attempt_ids": [str(attempt) for attempt in
                        agent.native.neighbours(proposal, "derived_from_trial")]}
                    for proposal in proposals],
                "qualification_count": len(qualifications),
                "qualifications": qualification_rows,
                "panel": panel,
            })
        return {"status": "COMPLETED", "family": family,
            "training_world_ids": [world["world_id"] for world in training_worlds],
            "training_goals_match": True,
            "validation_world_ids": [world["world_id"] for world in validation_worlds],
            "candidate_count": len(candidate_rows), "candidates": candidate_rows,
            "approval_count": len(agent.nodes("OpenProcessAdoptionApproval")),
            "world_receipt_count": len(agent.nodes("OpenProcessWorldReceipt")),
            "resource_snapshot": snapshot_native_resources(agent)}
    finally:
        del agent
