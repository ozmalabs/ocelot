"""Test graph-native directed walking on a full articulated humanoid."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
from itertools import combinations
import json
import multiprocessing
import os
from pathlib import Path
import sys
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.pybullet_humanoid_world import (  # noqa: E402
    HUMANOID_ASSET,
    HumanoidBodyConfiguration,
    PyBulletHumanoidWorld,
)
from domains.pybullet_humanoid_trial_transducer import (  # noqa: E402
    PyBulletHumanoidTrialTransducer,
)
from domains.humanoid_kinematics_study import (  # noqa: E402
    install_opaque_kinematic_topology,
    summarize_kinematics_study,
)
from domains.embodied_graph_transducer import (  # noqa: E402
    enact_graph_force_request,
)
from domains.embodied_effector_topology import (  # noqa: E402
    bind_effector_models,
    install_name_free_effector_topology,
)
from domains.embodied_pareto import (  # noqa: E402
    evaluate_pareto_profile,
    install_pareto_profile,
    pareto_frontier,
    publish_pareto_candidate,
)
from domains.embodied_motor_shapes import (  # noqa: E402
    motor_program_shape_signature,
)
from domains import faculty_autogenesis  # noqa: E402
from scripts.gen_embodied_development_seed import (  # noqa: E402
    CAPABILITIES,
)
from scripts.jabberwock_humanoid_adaptation import (  # noqa: E402
    _body_axis_tilt,
    _close_action,
    _edge,
    _enact_graph_command,
    _gravity_relative_orientation_class,
    _gravity_relative_up_axis,
    _model_rows,
    _one_node,
    _request_action,
    _write_state,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_walking_v1.json"
MOTOR_LIBRARY_VERSION = 25
DEVELOPMENTAL_CURRICULUM_CONTRACT_VERSION = 1


def developmental_curriculum_contract() -> dict[str, Any]:
    """Return the exact developmental ontology this runner can consume.

    Capability names are ordered because their ordinals are part of the
    graph's curriculum frontier.  The digest covers every ontology field that
    determines capability identity or graph reachability; a library from an
    older curriculum must never be partially recalled by name coincidence.
    """
    ontology = [
        {
            "name": row["name"],
            "goal": row["goal"],
            "evidence_kind": row["evidence"],
            "ecology": row["ecology"],
            "requires": list(row["requires"]),
        }
        for row in CAPABILITIES
    ]
    encoded = json.dumps(
        ontology,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return {
        "schema_version": DEVELOPMENTAL_CURRICULUM_CONTRACT_VERSION,
        "capability_names": [row["name"] for row in ontology],
        "ontology_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _validate_developmental_curriculum_contract(
    library: dict[str, Any],
) -> dict[str, Any] | int:
    expected = developmental_curriculum_contract()
    supplied = library.get("developmental_curriculum_contract")
    if supplied is None:
        raise ValueError(
            "incompatible humanoid developmental library: "
            "missing developmental_curriculum_contract"
        )
    if not isinstance(supplied, dict):
        raise ValueError(
            "incompatible humanoid developmental library: "
            "developmental_curriculum_contract is not an object"
        )
    for key in ("schema_version", "capability_names", "ontology_sha256"):
        if supplied.get(key) != expected[key]:
            raise ValueError(
                "incompatible humanoid developmental library: curriculum "
                f"contract mismatch for {key}; expected "
                f"{expected[key]!r}, got {supplied.get(key)!r}"
            )
    return expected


# PER-TERM COST DECOMPOSITION -- observability only, mechanical read.
# `CONTACT_WRENCH_PREREG.md` registered "report per-term contributions; a
# measure with one live component has replaced one category with another".
# The nine terms were summed in one expression and never individually
# visible, so rung 3 changed behaviour drastically by adding ONE of nine
# with no way to see which of the nine decides.  Nothing here feeds a
# decision: it reads a thread-local the Rust composer writes and appends.
_COST_TERM_SAMPLES: list[dict[str, float]] = []
_COST_TERM_ERROR: str | None = None


def _sample_cost_terms() -> None:
    """Append the winning plan's nine components, if the composer ran.

    The composer writes the slot on every `cost` evaluation and `compose`
    re-scores the WINNER last, so a read after a tick is that tick's
    decision.  When no composition happened the slot still holds the
    PREVIOUS decision, which would read as a fresh sample -- so an exact
    repeat of the immediately preceding sample is dropped.  That also drops
    genuinely identical consecutive decisions; stated here rather than
    discovered later, and it biases toward FEWER samples, never toward a
    value that was not actually computed.
    """
    # NO BARE SWALLOW. The first instrumented run returned samples: 0
    # because `humanoid_cost_terms` was built into the .so but never
    # re-exported by substrate_rs/__init__.py, so every call raised
    # AttributeError -- and an `except Exception: return` here turned a
    # hard wiring fault into an empty result that looked like a finding.
    # An instrument that hides its own failure is worse than none, so a
    # missing readout is recorded LOUDLY and once.
    global _COST_TERM_ERROR
    import substrate_rs
    if not hasattr(substrate_rs, "humanoid_cost_terms"):
        if _COST_TERM_ERROR is None:
            _COST_TERM_ERROR = "substrate_rs.humanoid_cost_terms not exported"
            print(f"COST TERM READOUT UNAVAILABLE: {_COST_TERM_ERROR}", flush=True)
        return
    terms = substrate_rs.humanoid_cost_terms()
    if not terms or any(v != 0.0 for v in terms.values()) is False:
        return
    if _COST_TERM_SAMPLES and _COST_TERM_SAMPLES[-1] == terms:
        return
    _COST_TERM_SAMPLES.append(terms)


def _cost_term_summary() -> dict[str, object]:
    """Median / mean / share-of-total per term, over the samples taken."""
    if not _COST_TERM_SAMPLES:
        return {"samples": 0, "unavailable_reason": _COST_TERM_ERROR}
    import statistics
    names = list(_COST_TERM_SAMPLES[0].keys())
    medians = {n: statistics.median([s[n] for s in _COST_TERM_SAMPLES])
               for n in names}
    means = {n: statistics.fmean([s[n] for s in _COST_TERM_SAMPLES])
             for n in names}
    total = sum(means.values())
    share = {n: (means[n] / total if total else 0.0) for n in names}
    return {
        "samples": len(_COST_TERM_SAMPLES),
        "median": medians,
        "mean": means,
        "share_of_mean_total": share,
        "dominant_term": max(share, key=share.get),
        "dominant_share": max(share.values()),
    }


def _tick_agent(
    agent: WorldAdapter,
    *,
    service_system_two: bool = False,
) -> dict[str, Any]:
    """Tick cognition and service graph-requested faculty construction I/O."""
    if service_system_two:
        report = agent.dual_process_tick()
    else:
        report = agent.tick()
    _sample_cost_terms()
    # A status-keyed I/O service check, not a host decision: the graph has
    # already requested synthesis. Once every need is terminal, ordinary
    # motor ticks pay no program-synthesis scan cost.
    if any(
        agent.s.node(need)["attrs"].get("status")
        in {"requested", "synthesizing"}
        for need in agent.s.nodes("FacultyNeed")
    ):
        faculty_autogenesis.pump(agent)
    return report


def _service_requested_system_two(agent: WorldAdapter) -> bool:
    """Service graph-requested deliberation before the next motor decision."""
    requested = [
        escalation
        for escalation in agent.s.nodes("SystemTwoEscalation")
        if agent.s.node(escalation)["attrs"].get("status") == "requested"
    ]
    if not requested:
        return False
    _tick_agent(agent, service_system_two=True)
    # Soft cognition is output-null. Publish its selected relation back to
    # hard realtime so the ordinary motor gate can consume it on this sensed
    # state; this is scheduler handoff, not another world prediction.
    _tick_agent(agent)
    return True


def _cognitive_continuation_authorised(
    agent: WorldAdapter,
    episode,
    development_context,
) -> bool:
    """Read the authority owned by the process under supervision.

    Developmental cognition lives on ``development_context``.  The humanoid
    episode remains the fallback for non-developmental protocols; it must not
    shadow a withdrawal made on the developmental process.
    """
    if development_context is None:
        authority = agent.s.node(episode)["attrs"].get(
            "cognitive_continuation_authority"
        )
        return type(authority) is int and authority == 1

    development_attrs = agent.s.node(development_context)["attrs"]
    if (
        development_attrs.get("developmental_deployment_mode") == 1
        and development_attrs.get("development_learning_active") == 0
    ):
        # A frozen controller has no learning process to lease. This closes
        # only the developmental continuation question; situated actuator
        # authority remains wholly owned by the ordinary motor/manifold gate.
        return True

    plans = agent.inner.neighbours(
        development_context, "has_self_directed_learning_plan"
    )
    if plans and all(
        agent.s.node(plan)["attrs"].get("status") == "completed"
        for plan in plans
    ):
        # The finite learning process has discharged its own risk gate. Motor
        # enactment is still governed by the ordinary situated manifold gate;
        # requiring a fictional selected learning step here would make
        # successful development disable deployment.
        return True
    selected_steps = {
        step
        for plan in plans
        for step in agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        )
    }
    active_processes = [
        process
        for process in agent.inner.neighbours(
            development_context, "has_cognitive_process"
        )
        if selected_steps.intersection(agent.inner.neighbours(
            process, "supervises_learning_plan_step"
        ))
        and (
            agent.s.node(process)["attrs"].get("status")
            in {"monitoring", "checking_in"}
            or (
                agent.s.node(process)["attrs"].get("status")
                == "replan_required"
                and agent.s.node(process)["attrs"].get(
                    "replan_release_complete", 0
                ) != 1
            )
        )
    ]
    if len(active_processes) != 1:
        return False
    process = active_processes[0]
    attrs = agent.s.node(process)["attrs"]
    policies = agent.inner.neighbours(
        process, "governed_by_cognitive_supervision_policy"
    )
    if len(policies) != 1:
        return False
    policy_attrs = agent.s.node(policies[0])["attrs"]
    authority = attrs.get("continuation_authority")
    generation = attrs.get("lease_generation")
    renew_before = attrs.get("renew_before_epoch")
    next_evidence = attrs.get("next_checkin_evidence_units")
    steps = agent.inner.neighbours(
        process, "supervises_learning_plan_step"
    )
    evidence = (
        agent.s.node(steps[0])["attrs"].get("evidence_spent_units")
        if len(steps) == 1 else None
    )
    epoch = policy_attrs.get("cognitive_epoch")
    enabled = policy_attrs.get("enabled")
    return (
        type(authority) is int
        and authority == 1
        and type(generation) is int
        and type(renew_before) is int
        and type(epoch) is int
        and type(enabled) is int
        and enabled == 1
        and type(next_evidence) is int
        and type(evidence) is int
        and evidence < next_evidence
    )


def _cognitive_authority_resolution_signature(
    agent: WorldAdapter,
    episode,
    development_context,
) -> tuple[Any, ...]:
    """Return the decision-relevant shape of a withheld-authority settle.

    Cognitive epochs are intentionally absent: elapsed scheduler time is not
    progress.  A repeated signature therefore means another output-null cycle
    cannot justify silently trying again.  Conversely, a changed selected
    step, process lease, escalation, or terminal decision is real progress and
    permits the graph to finish its bounded multi-cycle handoff.
    """
    context = development_context if development_context is not None else episode
    plans = tuple(sorted(
        agent.inner.neighbours(context, "has_self_directed_learning_plan"),
        key=str,
    ))
    selected_steps = tuple(sorted(
        (
            (plan, step)
            for plan in plans
            for step in agent.inner.neighbours(
                plan, "has_selected_learning_plan_step"
            )
        ),
        key=lambda pair: (str(pair[0]), str(pair[1])),
    ))
    step_ids = {
        step
        for plan in plans
        for step in agent.inner.neighbours(plan, "has_learning_plan_step")
    }
    steps = tuple(
        (
            step,
            agent.s.node(step)["attrs"].get("status"),
            agent.s.node(step)["attrs"].get("selection_count"),
            agent.s.node(step)["attrs"].get("revision_count"),
        )
        for step in sorted(step_ids, key=str)
    )
    processes = tuple(
        (
            process,
            attrs.get("status"),
            attrs.get("continuation_authority"),
            attrs.get("lease_generation"),
            attrs.get("renew_before_epoch"),
            attrs.get("next_checkin_evidence_units"),
            attrs.get("replan_release_complete"),
            tuple(sorted(
                agent.inner.neighbours(
                    process, "supervises_learning_plan_step"
                ),
                key=str,
            )),
        )
        for process in sorted(
            agent.inner.neighbours(context, "has_cognitive_process"),
            key=str,
        )
        for attrs in (agent.s.node(process)["attrs"],)
    )
    escalations = tuple(
        (node, agent.s.node(node)["attrs"].get("status"))
        for node in sorted(agent.s.nodes("SystemTwoEscalation"), key=str)
    )
    scheduler_turns = tuple(
        (node, agent.s.node(node)["attrs"].get("system_two_turn_owed"))
        for node in sorted(agent.s.nodes("DualProcessPolicy"), key=str)
        if agent.s.node(node)["attrs"].get("enabled") == 1
    )
    terminal = agent.s.node(context)["attrs"].get(
        "cognitive_checkin_terminal", 0
    )
    return (
        terminal,
        plans,
        selected_steps,
        steps,
        processes,
        escalations,
        scheduler_turns,
    )


def _settle_cognitive_continuation_authority(
    agent: WorldAdapter,
    episode,
    development_context,
) -> tuple[bool, int]:
    """Service authority until granted, halted, or a transition repeats."""
    seen_transitions: set[tuple[Any, ...]] = set()
    cycles = 0
    context = development_context if development_context is not None else episode
    while not _cognitive_continuation_authorised(
        agent, episode, development_context
    ):
        plans = agent.inner.neighbours(
            context, "has_self_directed_learning_plan"
        )
        plan_steps = [
            step
            for plan in plans
            for step in agent.inner.neighbours(
                plan, "has_learning_plan_step"
            )
        ]
        if plan_steps and all(
            agent.s.node(step)["attrs"].get("status") == "completed"
            for step in plan_steps
        ):
            return False, cycles
        if agent.s.node(context)["attrs"].get(
            "cognitive_checkin_terminal", 0
        ) == 1:
            return False, cycles
        before = _cognitive_authority_resolution_signature(
            agent, episode, development_context
        )
        report = _tick_agent(agent, service_system_two=True)
        cycles += 1
        if _cognitive_continuation_authorised(
            agent, episode, development_context
        ):
            return True, cycles
        after = _cognitive_authority_resolution_signature(
            agent, episode, development_context
        )
        report_signature = tuple(sorted(
            (
                str(key),
                repr(value),
            )
            for key, value in (report or {}).items()
            if key not in {"trace", "task_summary"}
        ))
        transition = (before, after, report_signature)
        if transition in seen_transitions:
            return False, cycles
        seen_transitions.add(transition)
    return True, cycles


def _cognitive_process_snapshots(
    agent: WorldAdapter,
    context,
) -> list[dict[str, Any]]:
    """Expose which selected step each supervision lease actually governs."""
    selected = {
        step
        for plan in agent.inner.neighbours(
            context, "has_self_directed_learning_plan"
        )
        for step in agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        )
    }
    snapshots = []
    for process in agent.s.nodes("CognitiveProcess"):
        supervised = agent.inner.neighbours(
            process, "supervises_learning_plan_step"
        )
        snapshots.append({
            **{
                key: agent.s.node(process)["attrs"].get(key)
                for key in (
                    "status",
                    "continuation_authority",
                    "lease_generation",
                    "renew_before_epoch",
                    "next_checkin_epoch",
                    "last_checkin_evidence_units",
                    "next_checkin_evidence_units",
                    "checkin_span_evidence_units",
                    "checkin_count",
                )
            },
            "supervised_steps": [
                {
                    "name": agent.s.node(step)["attrs"].get("name"),
                    "status": agent.s.node(step)["attrs"].get("status"),
                    "evidence_spent_units": agent.s.node(step)["attrs"].get(
                        "evidence_spent_units"
                    ),
                    "selected": int(step in selected),
                }
                for step in supervised
            ],
        })
    return snapshots


def _development_progress_snapshot(
    agent: WorldAdapter,
    episode,
    development_context,
) -> dict[str, Any]:
    """Mechanically expose graph-owned developmental state to an observer.

    This is an interface projection, not a second learning policy: every value
    is copied from the live graph after a closed motor receipt.  It lets an
    out-of-process daemon report what the cognitive process selected without
    reaching into, steering, or serialising the whole embodied graph.
    """
    episode_attrs = agent.s.node(episode)["attrs"]
    if development_context is None:
        return {
            "stage_ordinal": int(episode_attrs.get("developmental_stage_ordinal", 0)),
            "goal": str(episode_attrs.get("developmental_goal", "inactive")),
            "active_capability": "inactive",
            "mastery_count": 0,
            "retained_experience_count": 0,
            "selected_learning_step": "inactive",
            "checkin_count": len(list(agent.s.nodes("CognitiveCheckIn"))),
            "replan_count": 0,
            "continuation_authority": int(
                _cognitive_continuation_authorised(
                    agent, episode, development_context
                )
            ),
        }

    development_attrs = agent.s.node(development_context)["attrs"]
    selected_names: list[str] = []
    for plan in agent.inner.neighbours(
        development_context, "has_self_directed_learning_plan"
    ):
        for step in agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        ):
            selected_names.append(str(
                agent.s.node(step)["attrs"].get("name", "unnamed")
            ))
    checkins = list(agent.s.nodes("CognitiveCheckIn"))
    return {
        "stage_ordinal": int(episode_attrs.get("developmental_stage_ordinal", 0)),
        "goal": str(episode_attrs.get(
            "developmental_goal",
            development_attrs.get(
                "active_embodied_developmental_goal", "inactive"
            ),
        )),
        "active_capability": str(development_attrs.get(
            "active_embodied_developmental_capability", "inactive"
        )),
        "mastery_count": int(development_attrs.get(
            "embodied_developmental_mastery_count", 0
        )),
        "retained_experience_count": int(development_attrs.get(
            "retained_developmental_experience_count", 0
        )),
        "selected_learning_step": (
            selected_names[0] if len(selected_names) == 1 else "unresolved"
        ),
        "checkin_count": len(checkins),
        "replan_count": sum(
            agent.s.node(checkin)["attrs"].get("status")
            == "replan_required"
            for checkin in checkins
        ),
        "continuation_authority": int(
            _cognitive_continuation_authorised(
                agent, episode, development_context
            )
        ),
    }


def _developmental_frontier_diagnostics(
    agent: WorldAdapter,
    development_context,
) -> dict[str, Any]:
    """Expose the graph frontier and its first blocking prerequisites."""
    if development_context is None:
        return {
            "active": None,
            "frontier": [],
            "unresolved_prerequisites": [],
        }

    capabilities = list(agent.inner.neighbours(
        development_context,
        "has_embodied_developmental_capability",
    ))
    rows = []
    evidence_window = int(
        agent.s.node(development_context)["attrs"].get(
            "development_evidence_window", 0
        )
    )
    for capability in capabilities:
        attrs = agent.s.node(capability)["attrs"]
        prerequisites = list(agent.inner.neighbours(
            capability,
            "requires_embodied_developmental_capability",
        ))
        contexts = list(agent.inner.neighbours(
            capability, "has_embodied_developmental_context"
        ))
        trajectories = list(agent.inner.neighbours(
            capability, "has_embodied_program_trajectory"
        ))
        paths = list({
            path
            for trajectory in trajectories
            for path in agent.inner.neighbours(
                trajectory, "has_pareto_candidate"
            )
        })
        transitions = list(agent.inner.neighbours(
            capability, "has_embodied_program_transition"
        ))
        current_transition_sources = set(agent.inner.neighbours(
            capability,
            "has_current_embodied_program_transition_source",
        ))
        current_context_paths = [
            path
            for path in paths
            if current_transition_sources.intersection(
                agent.inner.neighbours(
                    path, "contains_embodied_program_transition"
                )
            )
        ]
        attempts = int(attrs.get("attempt_count", 0))
        successes = int(attrs.get("success_count", 0))
        unresolved = [
            str(agent.s.node(prerequisite)["attrs"].get("name", "unknown"))
            for prerequisite in prerequisites
            if agent.s.node(prerequisite)["attrs"].get("status") != "mastered"
        ]
        rows.append({
            "name": str(attrs.get("name", "unknown")),
            "ordinal": int(attrs.get("ordinal", 0)),
            "status": str(attrs.get("status", "unknown")),
            "attempt_count": attempts,
            "success_count": successes,
            "failure_count": int(attrs.get("failure_count", 0)),
            "retention_count": int(attrs.get("retention_count", 0)),
            "evidence_window": evidence_window,
            "attempts_remaining": max(0, evidence_window - attempts),
            "successes_remaining": max(0, evidence_window - successes),
            "context_count": len(contexts),
            "contexts_required": len(prerequisites) + 1,
            "contexts_remaining": max(
                0, len(prerequisites) + 1 - len(contexts)
            ),
            "desired_relation_count": len(
                attrs.get("desired_body_state_signature") or ()
            ),
            "trajectory_count": len(trajectories),
            "verified_transition_count": len(transitions),
            "manifold_admissible_current_transition_count": len(
                current_transition_sources
            ),
            "trajectory_path_count": len(paths),
            "current_context_trajectory_path_count": len(
                current_context_paths
            ),
            "maximum_trajectory_depth": max((
                int(agent.s.node(path)["attrs"].get("depth", 0))
                for path in paths
            ), default=0),
            "trajectory_replay_count": int(attrs.get(
                "trajectory_replay_count", 0
            )),
            "activation_receipt_seq": int(attrs.get(
                "activation_receipt_seq", 0
            )),
            "retention_start_seq": int(attrs.get("retention_start_seq", 0)),
            "warm_start_requires_verification": int(attrs.get(
                "warm_start_requires_verification", 0
            )),
            "unresolved_prerequisites": sorted(unresolved),
        })
    rows.sort(key=lambda row: (row["ordinal"], row["name"]))
    active = [
        row for row in rows
        if row["status"] == "active"
    ]
    frontier = [
        row for row in rows
        if row["status"] in {"available", "warm_available", "retention_due"}
        and not row["unresolved_prerequisites"]
    ]
    unresolved = [
        {
            "name": row["name"],
            "ordinal": row["ordinal"],
            "status": row["status"],
            "prerequisites": row["unresolved_prerequisites"],
        }
        for row in rows
        if row["unresolved_prerequisites"]
    ]
    return {
        "active": active[0] if len(active) == 1 else None,
        "frontier": frontier,
        "unresolved_prerequisites": unresolved,
    }


def _body_shape_name(signature: tuple[tuple[Any, ...], ...]) -> str:
    encoded = json.dumps(
        signature,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return "humanoid_body_shape:" + hashlib.sha256(encoded).hexdigest()


def _restore_signature_value(value: Any) -> Any:
    """Restore tuple identity lost at the JSON persistence boundary.

    The value layer deliberately distinguishes tuple shape from mutable list
    sequence. JSON has only arrays, so signature fields must be retyped at the
    interface before they enter cognition; otherwise exact-body recall becomes
    silently impossible after a disk round trip.
    """
    if isinstance(value, list):
        return tuple(_restore_signature_value(item) for item in value)
    if isinstance(value, dict):
        return {
            key: _restore_signature_value(item) for key, item in value.items()
        }
    return value


def _restore_library_attrs(row: dict[str, Any]) -> dict[str, Any]:
    attrs = dict(row["attrs"])
    for key in tuple(attrs):
        if key == "signature" or key.endswith("_signature"):
            attrs[key] = _restore_signature_value(attrs[key])
    return attrs


def _library_row_preference(row: dict[str, Any]) -> tuple[Any, ...]:
    """Prefer the most evidenced copy of one persisted semantic fact."""
    attrs = row.get("attrs", row)
    evidence = sum(
        float(attrs.get(key, 0) or 0)
        for key in (
            "experience_count",
            "sample_count",
            "success_count",
            "productive_count",
            "request_seq",
        )
    )
    return (
        int(attrs.get("updated_in_lifetime", 0) or 0),
        evidence,
        len(attrs.get("signature", ()) or ()),
        len(row.get("members", ()) or ()),
        len(row.get("stages", ()) or ()),
        len(row.get("actions", ()) or ()),
        json.dumps(row, sort_keys=True, separators=(",", ":")),
    )


def _coalesce_library_rows(
    rows: list[dict[str, Any]],
    identity_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Collapse repeated persisted facts without collapsing distinct facts."""
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        attrs = row.get("attrs", row)
        identity = None
        for field in identity_fields:
            value = attrs.get(field)
            if value is not None:
                identity = (
                    field,
                    json.dumps(value, sort_keys=True, separators=(",", ":")),
                )
                break
        if identity is None:
            identity = (
                "row",
                json.dumps(row, sort_keys=True, separators=(",", ":")),
            )
        previous = selected.get(identity)
        if previous is None or _library_row_preference(row) > (
            _library_row_preference(previous)
        ):
            selected[identity] = row
    # Dict replacement preserves the first semantic fact's position.  The
    # inputs are already deterministically ordered, so replacing its value
    # retains domain order (notably trajectory and residual ordinals).
    return list(selected.values())


def _coalesce_body_shape_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge repeated lifetimes of the same physical body shape.

    A continuation reloads a retained shape and the current lifetime also
    recognizes that shape.  Persisting both graph nodes made every generation
    multiply identical priors and eventually turned learning into an
    ever-growing search.  Merge by shape identity while retaining the most
    evidenced copy of each nested memory.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        attrs = row.get("attrs", {})
        identity_value = attrs.get("name", attrs.get("signature"))
        identity = json.dumps(
            identity_value, sort_keys=True, separators=(",", ":")
        )
        grouped.setdefault(identity, []).append(row)

    merged = []
    child_identities = {
        "programs": ("name", "signature", "ordinal"),
        "motor_transitions": ("name", "signature", "ordinal"),
        "coordination_challenges": ("name", "signature", "ordinal"),
        "residual_regimes": ("name", "signature", "ordinal"),
        "recovery_basins": (
            "name", "configuration_shape", "signature", "ordinal"
        ),
    }
    for duplicates in grouped.values():
        preferred = max(duplicates, key=_library_row_preference)
        combined = {"attrs": dict(preferred.get("attrs", {}))}
        for collection, identity_fields in child_identities.items():
            children = [
                child
                for duplicate in duplicates
                for child in duplicate.get(collection, ())
            ]
            combined[collection] = _coalesce_library_rows(
                children, identity_fields
            )
        merged.append(combined)
    merged.sort(key=lambda row: str(row["attrs"].get("name", "")))
    return merged


def _coalesce_plan_hint_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _coalesce_library_rows(rows, ("name", "signature", "ordinal"))


def _run_caregiver_scaffold(
    agent: WorldAdapter,
    episode,
    world: PyBulletHumanoidWorld,
) -> list[dict[str, Any]]:
    """Transduce graph-requested passive motion without assigning agency."""
    mode = str(agent.s.node(episode)["attrs"].get(
        "caregiver_scaffold_mode", "contingent"
    ))
    if mode not in {"contingent", "scrambled"}:
        raise ValueError(f"unsupported caregiver scaffold mode: {mode!r}")
    agent.inner.set_attr(episode, "caregiver_scaffold_session_active", 1)
    _tick_agent(agent)
    fields = agent.inner.neighbours(episode, "has_somatomotor_wave_field")
    if len(fields) != 1:
        raise RuntimeError("caregiver scaffold requires one somatomotor field")
    cells = agent.inner.neighbours(
        fields[0],
        "has_somatomotor_wave_cell",
    )
    cells_by_channel = {}
    for candidate_cell in cells:
        candidate_effectors = agent.inner.neighbours(
            candidate_cell, "represents_embodied_effector"
        )
        if len(candidate_effectors) != 1:
            raise RuntimeError("passive scaffold cell lacks one effector")
        candidate_channel = int(agent.s.node(candidate_effectors[0])[
            "attrs"
        ]["channel_ordinal"])
        cells_by_channel[candidate_channel] = candidate_cell
    ordered_channels = tuple(sorted(cells_by_channel))
    trace = []
    receipt_seq = 0
    # One request per effector, one vestibular bounce, then a reset-matched
    # passive/support pair for the independent exafferent support model.
    for _ in range(len(cells) + 3):
        requests = agent.inner.neighbours(
            episode,
            "requests_passive_somatomotor_scaffold",
        )
        if requests:
            if len(requests) != 1:
                raise RuntimeError("graph requested multiple passive effectors")
            cell = requests[0]
            effectors = agent.inner.neighbours(
                cell,
                "represents_embodied_effector",
            )
            if len(effectors) != 1:
                raise RuntimeError("passive scaffold cell lacks one effector")
            requested_channel = int(
                agent.s.node(effectors[0])["attrs"]["channel_ordinal"]
            )
            actual_channel = requested_channel
            if mode == "scrambled" and len(ordered_channels) > 1:
                requested_index = ordered_channels.index(requested_channel)
                actual_channel = ordered_channels[
                    (requested_index + 1) % len(ordered_channels)
                ]
            actual_cell = cells_by_channel[actual_channel]
            observation = world.scaffold_joint_cycle(actual_channel)
            receipt_seq += 1
            receipt = agent.s.add_node("SomatomotorScaffoldReceipt", {
                "scaffold_seq": receipt_seq,
                "scaffold_kind": "passive_effector_cycle",
                "exafferent": 1,
                "efference_copy_present": 0,
                "configuration_changed": int(
                    observation["scaffold_configuration_changed"]
                ),
                "requested_channel_ordinal": requested_channel,
                "actual_channel_ordinal": actual_channel,
                "caregiver_contingent": int(
                    requested_channel == actual_channel
                ),
                "positive_excursion_units": int(observation[
                    "scaffold_positive_excursion_units"
                ]),
                "negative_excursion_units": int(observation[
                    "scaffold_negative_excursion_units"
                ]),
                "return_residual_units": int(observation[
                    "scaffold_return_residual_units"
                ]),
                "coupled_channel_count": int(observation[
                    "scaffold_coupled_channel_count"
                ]),
                "receipt_processed": 0,
                "output_authority": 0,
                "integer_native": 1,
            })
            _edge(
                agent,
                episode,
                "has_somatomotor_scaffold_receipt",
                receipt,
            )
            _edge(
                agent,
                receipt,
                "scaffolds_somatomotor_wave_cell",
                actual_cell,
            )
            trace.append({
                "kind": "passive_effector_cycle",
                "requested_channel_ordinal": requested_channel,
                "actual_channel_ordinal": actual_channel,
                "caregiver_contingent": int(
                    requested_channel == actual_channel
                ),
                "configuration_changed": int(
                    observation["scaffold_configuration_changed"]
                ),
                "positive_excursion_units": int(observation[
                    "scaffold_positive_excursion_units"
                ]),
                "negative_excursion_units": int(observation[
                    "scaffold_negative_excursion_units"
                ]),
                "return_residual_units": int(observation[
                    "scaffold_return_residual_units"
                ]),
                "coupled_channel_count": int(observation[
                    "scaffold_coupled_channel_count"
                ]),
                "exafferent": 1,
                "efference_copy_present": 0,
            })
            _tick_agent(agent)
            continue
        attrs = agent.s.node(episode)["attrs"]
        if int(attrs.get("caregiver_bounce_requested", 0)) == 1:
            observation = world.scaffold_body_bounce()
            receipt_seq += 1
            receipt = agent.s.add_node("SomatomotorScaffoldReceipt", {
                "scaffold_seq": receipt_seq,
                "scaffold_kind": "passive_body_bounce",
                "exafferent": 1,
                "efference_copy_present": 0,
                "load_changed": int(observation["scaffold_load_changed"]),
                "vertical_direction": int(observation[
                    "scaffold_vertical_direction"
                ]),
                "support_count_change": int(observation[
                    "scaffold_support_count_change"
                ]),
                "receipt_processed": 0,
                "output_authority": 0,
                "integer_native": 1,
            })
            _edge(
                agent,
                episode,
                "has_somatomotor_scaffold_receipt",
                receipt,
            )
            trace.append({
                "kind": "passive_body_bounce",
                "load_changed": int(observation["scaffold_load_changed"]),
                "vertical_direction": int(observation[
                    "scaffold_vertical_direction"
                ]),
                "support_count_change": int(observation[
                    "scaffold_support_count_change"
                ]),
                "exafferent": 1,
                "efference_copy_present": 0,
            })
            _tick_agent(agent)
            continue
        calibration_kind = str(attrs.get(
            "caregiver_support_calibration_kind", ""
        ))
        if (
            int(attrs.get("caregiver_support_calibration_requested", 0)) == 1
            and calibration_kind in {"baseline", "supported"}
        ):
            models = agent.inner.neighbours(
                episode, "has_caregiver_support_action_model"
            )
            if len(models) != 1:
                raise RuntimeError(
                    "caregiver support calibration requires one action model"
                )
            before = world.reset()
            observation = world.step(
                "humanoid_actuator_000",
                caregiver_protective_support=(calibration_kind == "supported"),
            )
            before_up = _gravity_relative_up_axis(tuple(
                float(value) for value in before["base_orientation_xyzw"]
            ))
            after_up = _gravity_relative_up_axis(tuple(
                float(value) for value in observation["base_orientation_xyzw"]
            ))
            before_angular = tuple(float(value) for value in before[
                "base_angular_velocity"
            ])
            after_angular = tuple(float(value) for value in observation[
                "base_angular_velocity"
            ])
            before_linear = tuple(float(value) for value in before[
                "base_linear_velocity"
            ])
            after_linear = tuple(float(value) for value in observation[
                "base_linear_velocity"
            ])
            observed = {
                "dzx": after_up[0] - before_up[0],
                "dzy": after_up[1] - before_up[1],
                "dwx": after_angular[0] - before_angular[0],
                "dwy": after_angular[1] - before_angular[1],
                "dvx": after_linear[0] - before_linear[0],
                "dvy": after_linear[1] - before_linear[1],
                "dvz": after_linear[2] - before_linear[2],
            }
            receipt_seq += 1
            receipt = agent.s.add_node("CaregiverSupportCalibrationReceipt", {
                "scaffold_seq": receipt_seq,
                "calibration_kind": calibration_kind,
                "exafferent": 1,
                "efference_copy_present": 0,
                "receipt_processed": 0,
                "support_applied": int(observation.get(
                    "caregiver_protective_support_applied", 0
                )),
                "pre_z_x": before_up[0],
                "pre_z_y": before_up[1],
                "pre_wx": before_angular[0],
                "pre_wy": before_angular[1],
                "pre_vx": before_linear[0],
                "pre_vy": before_linear[1],
                "pre_vz": before_linear[2],
                "pre_lateral_offset": float(before["base_position"][1]),
                **{f"observed_{axis}": value for axis, value in observed.items()},
                "output_authority": 0,
                "integer_native": 1,
            })
            _edge(
                agent,
                episode,
                "has_caregiver_support_calibration_receipt",
                receipt,
            )
            _edge(
                agent,
                receipt,
                "calibrates_caregiver_support_action_model",
                models[0],
            )
            trace.append({
                "kind": f"protective_support_{calibration_kind}",
                "exafferent": 1,
                "efference_copy_present": 0,
                "support_applied": int(observation.get(
                    "caregiver_protective_support_applied", 0
                )),
                **{f"observed_{axis}": value for axis, value in observed.items()},
            })
            _tick_agent(agent)
            continue
        break
    if int(agent.s.node(episode)["attrs"].get(
        "caregiver_scaffold_handoff_ready", 0
    )) != 1:
        # Noncontingent help is still a real external event, but it cannot be
        # a permission gate on self-authored development. Close only this
        # passive calibration opportunity and let the graph explore cold.
        agent.inner.set_attr(
            episode, "caregiver_scaffold_session_active", 0
        )
        agent.inner.set_attr(episode, "caregiver_scaffold_unresolved", 1)
        agent.inner.set_attr(
            episode, "caregiver_passive_scaffold_withdrawn", 1
        )
        agent.inner.set_attr(episode, "caregiver_scaffold_withdrawn", 1)
    return trace


def _restore_motor_library(
    agent: WorldAdapter,
    library: dict[str, Any] | None,
) -> dict[str, Any]:
    """Mechanically restore graph facts; graph rules decide their use."""
    if library is None:
        return {"shape_count": 0, "program_count": 0}
    developmental_contract = _validate_developmental_curriculum_contract(
        library
    )
    if library.get("version") not in {
        3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
        20, 21, 22, 23, 24, MOTOR_LIBRARY_VERSION,
    }:
        raise ValueError(
            "unsupported humanoid motor library version: "
            f"{library.get('version')!r}"
        )
    shape_count = 0
    program_count = 0
    transition_count = 0
    challenge_memory_count = 0
    residual_regime_memory_count = 0
    recovery_basin_count = 0
    recovery_basin_action_count = 0
    developmental_capability_count = 0
    developmental_experience_count = 0
    developmental_experience_context_count = 0
    somatomotor_coupling_count = 0
    metacognitive_revision_count = 0
    metacognitive_counterexample_count = 0
    metacognitive_counterexample_context_count = 0
    motor_proposal_shape_memory_count = 0
    motor_proposal_body_shape_memory_count = 0
    motor_proposal_counterexample_count = 0
    caregiver_support_model_count = 0
    locomotor_phenotype_count = 0
    locomotor_phenotype_family_count = 0
    program_trajectory_shape_count = 0
    program_trajectory_transition_count = 0
    program_trajectory_endpoint_program_count = 0
    episodes = agent.s.nodes("HumanoidEpisode")
    if len(episodes) != 1:
        raise ValueError("motor library restore requires one humanoid episode")
    episode = episodes[0]
    family_rows = library.get("locomotor_phenotype_families", [])
    if family_rows:
        developments = agent.s.nodes("EmbodiedDevelopmentEpisode")
        if len(developments) != 1:
            raise ValueError(
                "locomotor phenotype family restore requires one "
                "embodied development episode"
            )
        development = developments[0]
        for family_row in family_rows:
            family_attrs = _restore_library_attrs(family_row)
            signature = family_attrs.get("signature", ())
            if (
                library.get("version") < 18
                or len(signature) < 8
                or tuple(signature[0])[:1] != ("action_intent",)
                or tuple(signature[1])[:1] != ("developmental_capability",)
                or tuple(signature[6])[:1] != ("pre_orientation_class",)
                or tuple(signature[7])[:1] != ("post_orientation_class",)
            ):
                # Earlier families lacked a required causal coordinate or, in
                # v17, incorrectly promoted enacted program to order 0. Their
                # statistics remain in the old artifact, but cannot be imported
                # as evidence into this foveated hierarchy.
                continue
            if family_attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "locomotor phenotype families must be output-null"
                )
            if family_attrs.get("integer_native", 1) != 1:
                raise ValueError(
                    "locomotor phenotype families must be integer-native"
                )
            family_attrs["output_authority"] = 0
            family_attrs["integer_native"] = 1
            family_attrs["shape_order"] = 0
            family_attrs["status"] = "hypothesis"
            family_attrs["refinement_required"] = 0
            family_attrs["selected_refinement_order"] = 0
            family_attrs["shape_residual_kind"] = "unresolved"
            family_attrs["last_receipt_seq"] = 0
            family_attrs["source"] = "library"
            family = agent.s.add_node(
                "EmbodiedLocomotorPhenotypeFamily", family_attrs
            )
            _edge(
                agent,
                development,
                "has_embodied_locomotor_phenotype_family",
                family,
            )
            locomotor_phenotype_family_count += 1
    phenotype_rows = library.get("locomotor_phenotypes", [])
    if phenotype_rows:
        developments = agent.s.nodes("EmbodiedDevelopmentEpisode")
        if len(developments) != 1:
            raise ValueError(
                "locomotor phenotype restore requires one embodied "
                "development episode"
            )
        development = developments[0]
        for phenotype_row in phenotype_rows:
            phenotype_attrs = _restore_library_attrs(phenotype_row)
            signature = phenotype_attrs.get("signature", ())
            if (
                library.get("version") < 20
                or len(signature) < 13
                or tuple(signature[0])[:1] != ("action_intent",)
                or tuple(signature[1])[:1] != ("developmental_capability",)
                or tuple(signature[2])[:1] != ("motor_program",)
                or tuple(signature[3])[:1] != ("pre_distal_support_code",)
                or tuple(signature[4])[:1] != (
                    "pre_whole_body_support_count",
                )
            ):
                continue
            if phenotype_attrs.get("output_authority", 0) != 0:
                raise ValueError("locomotor phenotypes must be output-null")
            if phenotype_attrs.get("integer_native", 1) != 1:
                raise ValueError("locomotor phenotypes must be integer-native")
            phenotype_attrs["output_authority"] = 0
            phenotype_attrs["integer_native"] = 1
            phenotype_attrs["shape_order"] = 1
            phenotype_attrs["status"] = "hypothesis"
            phenotype_attrs["last_receipt_seq"] = 0
            phenotype_attrs["source"] = "library"
            phenotype = agent.s.add_node(
                "EmbodiedLocomotorPhenotype", phenotype_attrs
            )
            _edge(
                agent,
                development,
                "has_embodied_locomotor_phenotype",
                phenotype,
            )
            locomotor_phenotype_count += 1
    for model_row in library.get("caregiver_support_models", []):
        model_attrs = _restore_library_attrs(model_row)
        if model_attrs.get("output_authority", 0) != 0:
            raise ValueError("caregiver support models must be output-null")
        if model_attrs.get("exafferent", 0) != 1:
            raise ValueError("caregiver support models must be exafferent")
        if model_attrs.get("initialized", 0) != 1:
            raise ValueError("caregiver support models must be initialized")
        model_attrs["output_authority"] = 0
        model = agent.s.add_node("CaregiverSupportActionModel", model_attrs)
        _edge(agent, episode, "has_caregiver_support_action_model", model)
        caregiver_support_model_count += 1
    if caregiver_support_model_count:
        agent.inner.set_attr(
            episode, "caregiver_support_calibration_complete", 1
        )
    shapes_by_name = {}
    programs_by_signature = {}
    for shape_row in _coalesce_body_shape_rows(
        library.get("body_shapes", [])
    ):
        shape_attrs = _restore_library_attrs(shape_row)
        shape_attrs["source"] = "library"
        shape = agent.s.add_node(
            "HumanoidBodyShapeSignature",
            shape_attrs,
        )
        _edge(
            agent,
            agent.agent,
            "has_humanoid_body_shape_library",
            shape,
        )
        shapes_by_name[str(shape_attrs["name"])] = shape
        shape_count += 1
        for library_slot, program_row in enumerate(
            shape_row.get("programs", []),
            start=1,
        ):
            program_attrs = _restore_library_attrs(program_row)
            members = [
                dict(member) for member in program_row.get("members", [])
            ]
            program_attrs.pop("motor_tokens", None)
            program_attrs.setdefault("motor_task_context", "locomotion")
            program_attrs.setdefault("motor_task_phase", "preparation")
            program_attrs.setdefault("library_slot", library_slot)
            program_attrs.setdefault(
                "name",
                f"{shape_attrs['name']}:motor_program:{library_slot}",
            )
            retained_signature = program_attrs.get("signature")
            program_attrs["signature"] = motor_program_shape_signature(
                program_attrs,
                members,
            )
            program_attrs["status"] = "library"
            program_attrs["source"] = "library"
            program = agent.s.add_node(
                "HumanoidMotorProgram",
                program_attrs,
            )
            _edge(
                agent,
                shape,
                "stores_humanoid_motor_program",
                program,
            )
            programs_by_signature[program_attrs["signature"]] = program
            if retained_signature:
                # v22 closed the endpoint vocabulary but still keyed its
                # transitions by the live routing label. Accept that label as
                # an import alias; every new snapshot writes canonical
                # structural member identity.
                programs_by_signature[retained_signature] = program
            for member_attrs in members:
                member = agent.s.add_node(
                    "HumanoidLibraryMotorMember",
                    dict(member_attrs),
                )
                _edge(
                    agent,
                    program,
                    "has_humanoid_library_motor_member",
                    member,
                )
            program_count += 1
        for transition_row in shape_row.get("motor_transitions", []):
            transition_attrs = _restore_library_attrs(transition_row)
            transition_attrs["status"] = "library"
            transition_attrs["source"] = "library"
            transition = agent.s.add_node(
                "HumanoidMotorTransition",
                transition_attrs,
            )
            _edge(
                agent,
                shape,
                "stores_humanoid_motor_transition",
                transition,
            )
            transition_count += 1
        for memory_attrs in shape_row.get("coordination_challenges", []):
            attrs = dict(memory_attrs)
            attrs["source"] = "library"
            attrs["updated_in_lifetime"] = 0
            memory = agent.s.add_node("HumanoidChallengeMemory", attrs)
            _edge(
                agent,
                shape,
                "stores_humanoid_challenge_memory",
                memory,
            )
            challenge_memory_count += 1
        for memory_attrs in shape_row.get("residual_regimes", []):
            attrs = dict(memory_attrs)
            attrs["source"] = "library"
            attrs["updated_in_lifetime"] = 0
            memory = agent.s.add_node(
                "HumanoidResidualRegimeMemory",
                attrs,
            )
            _edge(
                agent,
                shape,
                "stores_humanoid_residual_regime_memory",
                memory,
            )
            residual_regime_memory_count += 1
        restored_recovery_basins = []
        for basin_row in shape_row.get("recovery_basins", []):
            basin_attrs = _restore_library_attrs(basin_row)
            basin_attrs["status"] = "situated"
            basin_attrs["source"] = "library"
            basin_attrs["shape_indexed"] = 1
            basin = agent.s.add_node("HumanoidRecoveryBasin", basin_attrs)
            _edge(
                agent,
                shape,
                "stores_humanoid_recovery_basin",
                basin,
            )
            for action_attrs in basin_row.get("actions", []):
                action_attrs = dict(action_attrs)
                action = agent.s.add_node(
                    "HumanoidRecoveryBasinAction",
                    action_attrs,
                )
                _edge(
                    agent,
                    basin,
                    "has_humanoid_recovery_basin_action",
                    action,
                )
                recovery_basin_action_count += 1
            restored_recovery_basins.append((basin_row, basin))
            recovery_basin_count += 1
        for basin_row, basin in restored_recovery_basins:
            for successor_slot in basin_row.get("successor_slots", []):
                slot = int(successor_slot)
                if slot < 0 or slot >= len(restored_recovery_basins):
                    raise ValueError(
                        "recovery basin successor slot is outside its shape "
                        f"library: {slot}"
                    )
                _edge(
                    agent,
                    basin,
                    "continues_to_humanoid_recovery_basin",
                    restored_recovery_basins[slot][1],
                )
    for endpoint_slot, program_row in enumerate(
        library.get("program_trajectory_endpoint_programs", []),
        start=1,
    ):
        program_attrs = _restore_library_attrs(program_row)
        members = [
            dict(member) for member in program_row.get("members", [])
        ]
        program_attrs.pop("motor_tokens", None)
        program_attrs.setdefault("motor_task_context", "locomotion")
        program_attrs.setdefault("motor_task_phase", "execution")
        program_attrs.setdefault(
            "name", f"retained:trajectory_endpoint:{endpoint_slot}"
        )
        retained_signature = program_attrs.get("signature")
        signature = motor_program_shape_signature(program_attrs, members)
        if signature in programs_by_signature:
            continue
        if program_attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "program trajectory endpoint programs must be output-null"
            )
        program_attrs["signature"] = signature
        program_attrs["status"] = "trajectory_endpoint"
        program_attrs["source"] = "library"
        program_attrs["output_authority"] = 0
        program_attrs["trajectory_endpoint_only"] = 1
        program = agent.s.add_node("HumanoidMotorProgram", program_attrs)
        programs_by_signature[signature] = program
        if retained_signature:
            programs_by_signature[retained_signature] = program
        for member_attrs in members:
            member = agent.s.add_node(
                "HumanoidLibraryMotorMember", dict(member_attrs)
            )
            _edge(
                agent, program,
                "has_humanoid_library_motor_member", member,
            )
        program_trajectory_endpoint_program_count += 1

    developments = agent.s.nodes("EmbodiedDevelopmentEpisode")
    policies = agent.inner.neighbours(
        agent.agent, "has_humanoid_policy"
    )
    trajectory_rows_by_goal = {}
    trajectory_keys_by_goal = {}
    for shape_row in library.get("program_trajectory_shapes", []):
        row_attrs = _restore_library_attrs(shape_row)
        goal = str(row_attrs.get("goal", ""))
        combined = trajectory_rows_by_goal.setdefault(goal, {
            "attrs": {
                **row_attrs,
                "name": f"retained:{goal}",
            },
            "transitions": [],
        })
        known = trajectory_keys_by_goal.setdefault(goal, set())
        for transition_row in shape_row.get("transitions", []):
            identity = json.dumps(
                transition_row, sort_keys=True, separators=(",", ":")
            )
            if identity not in known:
                known.add(identity)
                combined["transitions"].append(transition_row)
    for shape_row in trajectory_rows_by_goal.values():
        transition_groups = {}
        for transition_row in shape_row["transitions"]:
            attrs = transition_row["attrs"]
            key = json.dumps(
                (
                    attrs["source_program_signature"],
                    attrs["target_program_signature"],
                    attrs["pre_orientation_class"],
                ),
                sort_keys=True,
                separators=(",", ":"),
            )
            transition_groups.setdefault(key, []).append(transition_row)
        for group in transition_groups.values():
            for axis in ("x", "y", "z"):
                values = [
                    int(row["attrs"][f"pre_state_axis_{axis}_units"])
                    for row in group
                ]
                for row in group:
                    row["attrs"].setdefault(
                        f"pre_state_axis_{axis}_minimum_units", min(values)
                    )
                    row["attrs"].setdefault(
                        f"pre_state_axis_{axis}_maximum_units", max(values)
                    )
        shape_attrs = _restore_library_attrs(shape_row)
        if shape_attrs.get("output_authority", 0) != 0:
            raise ValueError("program trajectory shapes must be output-null")
        shape_attrs["output_authority"] = 0
        shape_attrs["integer_native"] = 1
        shape_attrs["status"] = "retained"
        shape_attrs["source"] = "library"
        owner = agent.s.add_node(
            "Node", shape_attrs
        )
        _edge(
            agent,
            agent.agent,
            "has_retained_embodied_program_trajectory_shape",
            owner,
        )
        for transition_row in shape_row.get("transitions", []):
            transition_attrs = _restore_library_attrs(transition_row)
            source_signature = transition_attrs.pop(
                "source_program_signature"
            )
            target_signature = transition_attrs.pop(
                "target_program_signature"
            )
            source_program = programs_by_signature.get(source_signature)
            target_program = programs_by_signature.get(target_signature)
            if source_program is None or target_program is None:
                # A retained relation cannot be given a different body merely
                # because one of its endpoint programs is absent. Keep the
                # artifact valid, but do not instantiate an ungrounded edge.
                continue
            if transition_attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "program trajectory transitions must be output-null"
                )
            transition_attrs["output_authority"] = 0
            transition_attrs["verified"] = 1
            transition_attrs["experience_retained"] = 1
            transition_attrs["contextual_release_eligible"] = 0
            transition_attrs["source"] = "library"
            transition = agent.s.add_node(
                "ParetoProfile", transition_attrs
            )
            _edge(
                agent, owner,
                "has_embodied_program_transition", transition,
            )
            _edge(
                agent, transition,
                "starts_from_embodied_program", source_program,
            )
            _edge(
                agent, transition,
                "continues_with_embodied_program", target_program,
            )
            program_trajectory_transition_count += 1
        if (
            len(developments) == 1
            and len(policies) == 1
            and str(shape_attrs.get("goal", "")) == "locomotion"
            and int(agent.s.node(developments[0])["attrs"].get(
                "developmental_deployment_mode", 0
            )) == 1
            and agent.inner.neighbours(
                owner, "has_embodied_program_transition"
            )
        ):
            development = developments[0]
            agent.inner.set_attr(
                development,
                "trajectory_horizon",
                max(
                    2,
                    int(agent.s.node(development)["attrs"].get(
                        "development_evidence_window", 2
                    )),
                ),
            )
            agent.inner.set_attr(
                development, "trajectory_minimum_selection_depth", 2
            )
            _edge(
                agent, episode,
                "has_embodied_deployment_program_owner", owner,
            )
            _edge(
                agent, owner,
                "projects_future_manifold_in_episode", episode,
            )
            _edge(
                agent, owner,
                "uses_future_manifold_policy", policies[0],
            )
            _edge(
                agent, owner,
                "requests_embodied_program_trajectory", development,
            )
            agent.inner.set_attr(owner, "status", "situated")
        program_trajectory_shape_count += 1
    plan_hint_count = 0
    plan_hint_stage_count = 0
    for hint_row in _coalesce_plan_hint_rows(library.get("plan_hints", [])):
        hint_attrs = _restore_library_attrs(hint_row)
        if hint_attrs.get("output_authority", 0) != 0:
            raise ValueError("motor plan hints must be output-null")
        hint_attrs["source"] = "library_hint"
        hint = agent.s.add_node("EmbodiedMotorPlanHint", hint_attrs)
        _edge(agent, agent.agent, "has_embodied_motor_plan_hint_library", hint)
        body_shape_name = str(hint_attrs.get("body_shape_name", ""))
        if body_shape_name in shapes_by_name:
            _edge(
                agent,
                hint,
                "derived_from_humanoid_body_shape",
                shapes_by_name[body_shape_name],
            )
        for stage_row in hint_row.get("stages", []):
            stage_attrs = _restore_library_attrs(stage_row)
            if stage_attrs.get("output_authority", 0) != 0:
                raise ValueError("motor plan hint stages must be output-null")
            stage_attrs["source"] = "library_hint"
            stage = agent.s.add_node(
                "EmbodiedMotorPlanHintStage", stage_attrs
            )
            _edge(agent, hint, "has_embodied_motor_plan_hint_stage", stage)
            plan_hint_stage_count += 1
        plan_hint_count += 1
    for memory_row in library.get("developmental_capabilities", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "developmental capability memories must be output-null"
            )
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        memory_attrs["source"] = "library"
        memory = agent.s.add_node(
            "EmbodiedDevelopmentalCapabilityMemory",
            memory_attrs,
        )
        _edge(
            agent,
            agent.agent,
            "has_embodied_developmental_capability_memory",
            memory,
        )
        developmental_capability_count += 1
    for memory_row in library.get("developmental_experiences", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "developmental experience memories must be output-null"
            )
        if memory_attrs.get("integer_native", 1) != 1:
            raise ValueError(
                "developmental experience memories must be integer-native"
            )
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        memory_attrs["source"] = "library"
        memory = agent.s.add_node(
            "EmbodiedDevelopmentalExperienceMemory",
            memory_attrs,
        )
        _edge(
            agent,
            agent.agent,
            "has_embodied_developmental_experience_memory",
            memory,
        )
        for context_row in memory_row.get("contexts", []):
            context_attrs = _restore_library_attrs(context_row)
            if context_attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "developmental experience contexts must be output-null"
                )
            context_attrs["output_authority"] = 0
            context_attrs["integer_native"] = 1
            context = agent.s.add_node(
                "EmbodiedDevelopmentalExperienceContextMemory",
                context_attrs,
            )
            _edge(
                agent,
                memory,
                "has_embodied_developmental_experience_context",
                context,
            )
            developmental_experience_context_count += 1
        developmental_experience_count += 1
    for memory_row in library.get("somatomotor_couplings", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError("somatomotor coupling memories must be output-null")
        if memory_attrs.get("integer_native", 1) != 1:
            raise ValueError("somatomotor coupling memories must be integer-native")
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        for role in ("source", "target"):
            for field in (
                "mount_depth",
                "mount_degree",
                "axis_x_class",
                "axis_y_class",
                "axis_z_class",
            ):
                memory_attrs.setdefault(f"{role}_{field}", 0)
        memory_attrs["source"] = "library"
        memory = agent.s.add_node("SomatomotorCouplingMemory", memory_attrs)
        _edge(
            agent,
            agent.agent,
            "has_somatomotor_coupling_memory",
            memory,
        )
        somatomotor_coupling_count += 1
    for memory_row in library.get("metacognitive_learning_revisions", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "metacognitive learning revision memories must be output-null"
            )
        if memory_attrs.get("integer_native", 1) != 1:
            raise ValueError(
                "metacognitive learning revision memories must be integer-native"
            )
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        memory_attrs["source"] = "library"
        memory = agent.s.add_node(
            "MetacognitiveLearningRevisionMemory", memory_attrs
        )
        _edge(
            agent,
            agent.agent,
            "has_metacognitive_learning_revision_memory",
            memory,
        )
        metacognitive_revision_count += 1
    for memory_row in library.get("metacognitive_learning_counterexamples", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "metacognitive counterexample memories must be output-null"
            )
        if memory_attrs.get("integer_native", 1) != 1:
            raise ValueError(
                "metacognitive counterexample memories must be integer-native"
            )
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        memory_attrs["source"] = "library"
        memory = agent.s.add_node(
            "MetacognitiveLearningCounterexampleMemory", memory_attrs
        )
        _edge(
            agent,
            agent.agent,
            "has_metacognitive_learning_counterexample_memory",
            memory,
        )
        for member_row in memory_row.get("mastery_context", []):
            member_attrs = _restore_library_attrs(member_row)
            if member_attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "metacognitive counterexample context must be output-null"
                )
            member_attrs["output_authority"] = 0
            member_attrs["integer_native"] = 1
            member = agent.s.add_node(
                "MetacognitiveCounterexampleContextMember", member_attrs
            )
            _edge(
                agent,
                memory,
                "has_metacognitive_counterexample_context_member",
                member,
            )
            metacognitive_counterexample_context_count += 1
        metacognitive_counterexample_count += 1
    for memory_row in library.get("motor_proposal_shape_memories", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError("motor proposal shape memories must be output-null")
        if memory_attrs.get("integer_native", 1) != 1:
            raise ValueError("motor proposal shape memories must be integer-native")
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        memory_attrs["source"] = "library"
        memory = agent.s.add_node(
            "EmbodiedMotorProposalShapeMemory", memory_attrs
        )
        _edge(
            agent, agent.agent,
            "has_motor_proposal_shape_memory", memory,
        )
        for body_row in memory_row.get("body_shapes", []):
            body_attrs = _restore_library_attrs(body_row)
            if body_attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "motor proposal body memories must be output-null"
                )
            if body_attrs.get("integer_native", 1) != 1:
                raise ValueError(
                    "motor proposal body memories must be integer-native"
                )
            body_attrs["output_authority"] = 0
            body_attrs["integer_native"] = 1
            body_attrs["source"] = "library"
            body = agent.s.add_node(
                "EmbodiedMotorProposalBodyShapeMemory", body_attrs
            )
            _edge(
                agent, memory,
                "has_motor_proposal_body_shape_memory", body,
            )
            motor_proposal_body_shape_memory_count += 1
        motor_proposal_shape_memory_count += 1
    for memory_row in library.get("motor_proposal_counterexamples", []):
        memory_attrs = _restore_library_attrs(memory_row)
        if memory_attrs.get("output_authority", 0) != 0:
            raise ValueError("motor proposal counterexamples must be output-null")
        if memory_attrs.get("integer_native", 1) != 1:
            raise ValueError("motor proposal counterexamples must be integer-native")
        memory_attrs["output_authority"] = 0
        memory_attrs["integer_native"] = 1
        memory_attrs["source"] = "library"
        memory = agent.s.add_node("MotorProposalCounterexample", memory_attrs)
        _edge(
            agent, agent.agent,
            "has_motor_proposal_counterexample", memory,
        )
        motor_proposal_counterexample_count += 1
    restored = {
        "shape_count": shape_count,
        "program_count": program_count,
        "developmental_curriculum_contract_version": developmental_contract[
            "schema_version"
        ],
        "developmental_curriculum_contract_digest": developmental_contract[
            "ontology_sha256"
        ],
        "developmental_curriculum_contract_capability_count": len(
            developmental_contract["capability_names"]
        ),
    }
    if plan_hint_count:
        restored["plan_hint_count"] = plan_hint_count
    if plan_hint_stage_count:
        restored["plan_hint_stage_count"] = plan_hint_stage_count
    if transition_count:
        restored["transition_count"] = transition_count
    if challenge_memory_count:
        restored["challenge_memory_count"] = challenge_memory_count
    if residual_regime_memory_count:
        restored["residual_regime_memory_count"] = (
            residual_regime_memory_count
        )
    if recovery_basin_count:
        restored["recovery_basin_count"] = recovery_basin_count
    if recovery_basin_action_count:
        restored["recovery_basin_action_count"] = (
            recovery_basin_action_count
        )
    if developmental_capability_count:
        restored["developmental_capability_count"] = (
            developmental_capability_count
        )
    if locomotor_phenotype_family_count:
        restored["locomotor_phenotype_family_count"] = (
            locomotor_phenotype_family_count
        )
    if locomotor_phenotype_count:
        restored["locomotor_phenotype_count"] = locomotor_phenotype_count
    if developmental_experience_count:
        restored["developmental_experience_count"] = (
            developmental_experience_count
        )
    if developmental_experience_context_count:
        restored["developmental_experience_context_count"] = (
            developmental_experience_context_count
        )
    if somatomotor_coupling_count:
        restored["somatomotor_coupling_count"] = somatomotor_coupling_count
    if metacognitive_revision_count:
        restored["metacognitive_revision_count"] = metacognitive_revision_count
    if metacognitive_counterexample_count:
        restored["metacognitive_counterexample_count"] = (
            metacognitive_counterexample_count
        )
    if metacognitive_counterexample_context_count:
        restored["metacognitive_counterexample_context_count"] = (
            metacognitive_counterexample_context_count
        )
    if motor_proposal_shape_memory_count:
        restored["motor_proposal_shape_memory_count"] = (
            motor_proposal_shape_memory_count
        )
    if motor_proposal_body_shape_memory_count:
        restored["motor_proposal_body_shape_memory_count"] = (
            motor_proposal_body_shape_memory_count
        )
    if motor_proposal_counterexample_count:
        restored["motor_proposal_counterexample_count"] = (
            motor_proposal_counterexample_count
        )
    if caregiver_support_model_count:
        restored["caregiver_support_model_count"] = (
            caregiver_support_model_count
        )
    if program_trajectory_shape_count:
        restored["program_trajectory_shape_count"] = (
            program_trajectory_shape_count
        )
    if program_trajectory_transition_count:
        restored["program_trajectory_transition_count"] = (
            program_trajectory_transition_count
        )
    if program_trajectory_endpoint_program_count:
        restored["program_trajectory_endpoint_program_count"] = (
            program_trajectory_endpoint_program_count
        )
    return restored


def _somatomotor_coupling_snapshot(
    agent: WorldAdapter,
) -> list[dict[str, Any]]:
    """Mechanically serialize experienced, output-null coupling evidence."""
    memories_by_name: dict[str, dict[str, Any]] = {}
    for memory in agent.inner.neighbours(
        agent.agent,
        "has_somatomotor_coupling_memory",
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("output_authority", 0) != 0:
            raise ValueError("somatomotor coupling memories must be output-null")
        if attrs.get("integer_native", 1) != 1:
            raise ValueError("somatomotor coupling memories must be integer-native")
        memories_by_name[str(attrs["name"])] = {"attrs": attrs}

    relation_fields = (
        "same_command_channel",
        "declared_hard_coupling",
        "mechanical_path_known",
        "mechanical_path_length",
        "same_mount",
        "command_polarity_product",
    )
    effector_fields = (
        "mount_depth",
        "mount_degree",
        "axis_x_class",
        "axis_y_class",
        "axis_z_class",
    )
    for episode in agent.inner.neighbours(agent.agent, "has_humanoid_episode"):
        developments = agent.inner.neighbours(
            episode,
            "projects_embodied_development",
        )
        fields = agent.inner.neighbours(episode, "has_somatomotor_wave_field")
        if len(developments) != 1 or len(fields) != 1:
            continue
        experienced: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        signature = agent.s.node(developments[0])["attrs"].get(
            "body_capability_signature",
            (),
        )
        field = fields[0]
        for source in agent.inner.neighbours(
            field,
            "has_somatomotor_wave_cell",
        ):
            source_ordinal = int(
                agent.s.node(source)["attrs"].get("ordinal", 0)
            )
            for coupling in agent.inner.neighbours(
                source,
                "has_somatomotor_wave_coupling",
            ):
                coupling_attrs = agent.s.node(coupling)["attrs"]
                productive = int(coupling_attrs.get("productive_count", 0))
                unproductive = int(
                    coupling_attrs.get("unproductive_count", 0)
                )
                if productive + unproductive == 0:
                    continue
                targets = agent.inner.neighbours(
                    coupling,
                    "targets_somatomotor_wave_cell",
                )
                relations = agent.inner.neighbours(
                    coupling,
                    "grounds_in_embodied_effector_relation",
                )
                if len(targets) != 1 or len(relations) != 1:
                    raise RuntimeError(
                        "experienced somatomotor coupling lacks unique grounding"
                    )
                target_ordinal = int(
                    agent.s.node(targets[0])["attrs"].get("ordinal", 0)
                )
                relation_attrs = agent.s.node(relations[0])["attrs"]
                motif = tuple(
                    int(relation_attrs[name]) for name in relation_fields
                )
                source_effectors = agent.inner.neighbours(
                    source,
                    "represents_embodied_effector",
                )
                target_effectors = agent.inner.neighbours(
                    targets[0],
                    "represents_embodied_effector",
                )
                if len(source_effectors) != 1 or len(target_effectors) != 1:
                    raise RuntimeError(
                        "somatomotor coupling cells lack unique effectors"
                    )
                source_attrs = agent.s.node(source_effectors[0])["attrs"]
                target_attrs = agent.s.node(target_effectors[0])["attrs"]
                local_motif = {
                    f"{role}_{name}": int(attrs.get(name, 0))
                    for role, attrs in (
                        ("source", source_attrs),
                        ("target", target_attrs),
                    )
                    for name in effector_fields
                }
                attrs = {
                    "signature": signature,
                    **dict(zip(relation_fields, motif)),
                    **local_motif,
                    "productive_count": productive,
                    "unproductive_count": unproductive,
                    "output_authority": 0,
                    "integer_native": 1,
                }
                experienced.append((
                    (
                        source_ordinal,
                        target_ordinal,
                        *motif,
                        *(local_motif[name] for name in sorted(local_motif)),
                    ),
                    attrs,
                ))
        shape_name = _body_shape_name(tuple(signature))
        for ordinal, (_, attrs) in enumerate(sorted(experienced), start=1):
            attrs["name"] = f"{shape_name}:somatomotor_coupling:{ordinal}"
            memories_by_name[attrs["name"]] = {"attrs": attrs}

    return [memories_by_name[name] for name in sorted(memories_by_name)]


def _motor_library_snapshot(
    agent: WorldAdapter,
) -> dict[str, Any]:
    """Serialize only facts already minted into the graph's shape library."""
    body_shapes = []
    for shape in agent.inner.neighbours(
        agent.agent,
        "has_humanoid_body_shape_library",
    ):
        shape_attrs = dict(agent.s.node(shape)["attrs"])
        shape_attrs.pop("source", None)
        programs = []
        for program in agent.inner.neighbours(
            shape,
            "stores_humanoid_motor_program",
        ):
            program_attrs = dict(agent.s.node(program)["attrs"])
            program_attrs.pop("source", None)
            program_attrs["status"] = "grounded"
            phase_members = agent.inner.neighbours(
                program,
                "includes_humanoid_phase_action_model",
            )
            if phase_members:
                members = [
                    {
                        "token": attrs["token"],
                        "ordinal": float(attrs["ordinal"]),
                        "support_phase": float(attrs["support_phase"]),
                    }
                    for attrs in (
                        agent.s.node(member)["attrs"]
                        for member in phase_members
                    )
                ]
            else:
                members = [
                    dict(agent.s.node(member)["attrs"])
                    for member in agent.inner.neighbours(
                        program,
                        "has_humanoid_library_motor_member",
                    )
                ]
            members.sort(
                key=lambda row: (
                    float(row["ordinal"]),
                    str(row["token"]),
                )
            )
            programs.append({
                "attrs": program_attrs,
                "members": members,
            })
        programs.sort(
            key=lambda row: (
                float(row["attrs"].get("ordinal", 0.0)),
                str(row["attrs"].get("primary_token", "")),
            )
        )
        coordination_challenges = [
            {
                key: value
                for key, value in agent.s.node(memory)["attrs"].items()
                if key not in {"source", "updated_in_lifetime"}
            }
            for memory in agent.inner.neighbours(
                shape,
                "stores_humanoid_challenge_memory",
            )
        ]
        coordination_challenges.sort(
            key=lambda row: float(row.get("ordinal", 0.0))
        )
        motor_transitions = [
            {
                "attrs": {
                    key: value
                    for key, value in agent.s.node(transition)["attrs"].items()
                    if key != "source"
                },
            }
            for transition in agent.inner.neighbours(
                shape,
                "stores_humanoid_motor_transition",
            )
        ]
        motor_transitions.sort(
            key=lambda row: float(row["attrs"].get("ordinal", 0.0))
        )
        residual_regimes = [
            {
                key: value
                for key, value in agent.s.node(memory)["attrs"].items()
                if key not in {"source", "updated_in_lifetime"}
            }
            for memory in agent.inner.neighbours(
                shape,
                "stores_humanoid_residual_regime_memory",
            )
        ]
        residual_regimes.sort(
            key=lambda row: float(row.get("ordinal", 0.0))
        )
        recovery_basins = []
        all_stored_recovery_basins = agent.inner.neighbours(
            shape,
            "stores_humanoid_recovery_basin",
        )

        def recovery_basin_identity(basin):
            attrs = agent.s.node(basin)["attrs"]
            return (
                float(attrs.get("ordinal", 0.0)),
                json.dumps(
                    attrs.get("configuration_shape"),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                str(attrs.get("incoming_primary_token", "")),
                str(attrs.get("incoming_secondary_token", "")),
                float(attrs.get("incoming_support_count", -1.0)),
                float(attrs.get("incoming_contact_count", -1.0)),
                float(attrs.get("incoming_motion_energy", -1.0)),
            )

        recovery_basin_groups = {}
        for basin in all_stored_recovery_basins:
            recovery_basin_groups.setdefault(
                recovery_basin_identity(basin),
                [],
            ).append(basin)
        selected_by_identity = {
            identity: max(
                members,
                key=lambda basin: (
                    agent.s.node(basin)["attrs"].get("source") != "library",
                    float(agent.s.node(basin)["attrs"].get(
                        "request_seq", 0.0
                    )),
                    str(basin),
                ),
            )
            for identity, members in recovery_basin_groups.items()
        }
        stored_recovery_basins = sorted(
            selected_by_identity.values(),
            key=lambda basin: (
                float(agent.s.node(basin)["attrs"].get("ordinal", 0.0)),
                float(agent.s.node(basin)["attrs"].get("request_seq", 0.0)),
                str(basin),
            ),
        )
        selected_for_basin = {
            basin: selected_by_identity[recovery_basin_identity(basin)]
            for basin in all_stored_recovery_basins
        }
        recovery_basin_slots = {
            basin: slot
            for slot, basin in enumerate(stored_recovery_basins)
        }
        for basin in stored_recovery_basins:
            basin_attrs = {
                key: value
                for key, value in agent.s.node(basin)["attrs"].items()
                if key != "source"
            }
            basin_attrs["status"] = "situated"
            actions = [
                {
                    key: value
                    for key, value in agent.s.node(action)["attrs"].items()
                    if key != "source"
                }
                for action in agent.inner.neighbours(
                    basin,
                    "has_humanoid_recovery_basin_action",
                )
            ]
            actions.sort(key=lambda row: (
                float(row.get("member_count", 0.0)),
                str(row.get("primary_token", "")),
                str(row.get("secondary_token", "")),
            ))
            recovery_basins.append({
                "attrs": basin_attrs,
                "actions": actions,
                "successor_slots": sorted({
                    recovery_basin_slots[selected_for_basin[successor]]
                    for equivalent in recovery_basin_groups[
                        recovery_basin_identity(basin)
                    ]
                    for successor in agent.inner.neighbours(
                        equivalent,
                        "continues_to_humanoid_recovery_basin",
                    )
                    if successor in selected_for_basin
                    and selected_for_basin[successor] in recovery_basin_slots
                }),
            })
        if (
            programs
            or coordination_challenges
            or motor_transitions
            or residual_regimes
            or recovery_basins
        ):
            body_shapes.append({
                "attrs": shape_attrs,
                "programs": programs,
                "motor_transitions": motor_transitions,
                "coordination_challenges": coordination_challenges,
                "residual_regimes": residual_regimes,
                "recovery_basins": recovery_basins,
            })
    body_shapes = _coalesce_body_shape_rows(body_shapes)
    trajectory_fields = (
        "verified",
        "experience_retained",
        "pre_orientation_class",
        "post_orientation_class",
        "pre_state_axis_x_units",
        "pre_state_axis_y_units",
        "pre_state_axis_z_units",
        "pre_state_axis_x_minimum_units",
        "pre_state_axis_y_minimum_units",
        "pre_state_axis_z_minimum_units",
        "pre_state_axis_x_maximum_units",
        "pre_state_axis_y_maximum_units",
        "pre_state_axis_z_maximum_units",
        "post_state_axis_x_units",
        "post_state_axis_y_units",
        "post_state_axis_z_units",
        "boundary_transition_count",
        "energy_units",
        "peak_load_units",
        "capability_evidence_units",
        "task_progress_units",
        "response_frames",
        "integer_native_trajectory",
    )

    def program_signature(program):
        attrs = agent.s.node(program)["attrs"]
        members = [
            agent.s.node(member)["attrs"]
            for relation in (
                "includes_humanoid_phase_action_model",
                "includes_humanoid_action_model",
                "has_humanoid_library_motor_member",
            )
            for member in agent.inner.neighbours(program, relation)
        ]
        return motor_program_shape_signature(attrs, members)

    def trajectory_endpoint_program_row(program):
        attrs = {
            key: value
            for key, value in agent.s.node(program)["attrs"].items()
            if key != "source"
        }
        members = [
            {
                "token": member_attrs["token"],
                "ordinal": float(member_attrs.get("ordinal", ordinal)),
                "support_phase": float(member_attrs.get(
                    "support_phase", attrs.get("support_phase", -1.0)
                )),
            }
            for relation in (
                "includes_humanoid_phase_action_model",
                "includes_humanoid_action_model",
                "has_humanoid_library_motor_member",
            )
            for ordinal, member in enumerate(agent.inner.neighbours(
                program, relation
            ))
            for member_attrs in (agent.s.node(member)["attrs"],)
        ]
        unique_members = {
            (
                str(member["token"]),
                float(member["ordinal"]),
                float(member["support_phase"]),
            ): member
            for member in members
        }
        members = sorted(unique_members.values(), key=lambda member: (
            float(member["ordinal"]), str(member["token"])
        ))
        attrs["signature"] = program_signature(program)
        attrs["status"] = "grounded"
        attrs.setdefault("motor_task_context", "locomotion")
        attrs.setdefault("motor_task_phase", "preparation")
        return {"attrs": attrs, "members": members}

    trajectory_shapes_by_goal = {}
    trajectory_transition_keys_by_goal = {}
    trajectory_endpoint_programs = {}
    trajectory_owners = []
    for development in agent.s.nodes("EmbodiedDevelopmentEpisode"):
        trajectory_owners.extend(agent.inner.neighbours(
            development, "has_embodied_developmental_capability"
        ))
    trajectory_owners.extend(agent.inner.neighbours(
        agent.agent, "has_retained_embodied_program_trajectory_shape"
    ))
    trajectory_owners.extend(
        owner
        for episode in agent.s.nodes("HumanoidEpisode")
        for owner in agent.inner.neighbours(
            episode, "has_embodied_deployment_program_owner"
        )
    )
    for owner in trajectory_owners:
        owner_attrs = agent.s.node(owner)["attrs"]
        transitions = []
        for transition in agent.inner.neighbours(
            owner, "has_embodied_program_transition"
        ):
            transition_attrs = agent.s.node(transition)["attrs"]
            if int(transition_attrs.get("verified", 0)) != 1:
                continue
            sources = agent.inner.neighbours(
                transition, "starts_from_embodied_program"
            )
            targets = agent.inner.neighbours(
                transition, "continues_with_embodied_program"
            )
            if len(sources) != 1 or len(targets) != 1:
                continue
            attrs = {
                key: transition_attrs[key]
                for key in trajectory_fields
                if key in transition_attrs
            }
            attrs.update({
                "source_program_signature": program_signature(sources[0]),
                "target_program_signature": program_signature(targets[0]),
                "output_authority": 0,
            })
            for program in (sources[0], targets[0]):
                endpoint = trajectory_endpoint_program_row(program)
                trajectory_endpoint_programs[json.dumps(
                    endpoint["attrs"]["signature"],
                    sort_keys=True,
                    separators=(",", ":"),
                )] = endpoint
            transitions.append({"attrs": attrs})
        if not transitions:
            continue
        transitions.sort(key=lambda row: json.dumps(
            row["attrs"], sort_keys=True, separators=(",", ":")
        ))
        goal = str(owner_attrs.get(
            "goal", owner_attrs.get("motor_task_context", "locomotion")
        ))
        shape = trajectory_shapes_by_goal.setdefault(goal, {
            "attrs": {
                "name": f"retained:{goal}",
                "goal": goal,
                "motor_task_context": str(owner_attrs.get(
                    "motor_task_context", goal
                )),
                "output_authority": 0,
                "integer_native": 1,
            },
            "transitions": [],
        })
        known = trajectory_transition_keys_by_goal.setdefault(goal, set())
        for transition in transitions:
            identity = json.dumps(
                transition, sort_keys=True, separators=(",", ":")
            )
            if identity not in known:
                known.add(identity)
                shape["transitions"].append(transition)
    trajectory_shapes = list(trajectory_shapes_by_goal.values())
    for shape in trajectory_shapes:
        transition_groups = {}
        for transition in shape["transitions"]:
            attrs = transition["attrs"]
            key = json.dumps(
                (
                    attrs["source_program_signature"],
                    attrs["target_program_signature"],
                    attrs["pre_orientation_class"],
                ),
                sort_keys=True,
                separators=(",", ":"),
            )
            transition_groups.setdefault(key, []).append(transition)
        for group in transition_groups.values():
            for axis in ("x", "y", "z"):
                values = [
                    int(row["attrs"][f"pre_state_axis_{axis}_units"])
                    for row in group
                ]
                for row in group:
                    row["attrs"][
                        f"pre_state_axis_{axis}_minimum_units"
                    ] = min(values)
                    row["attrs"][
                        f"pre_state_axis_{axis}_maximum_units"
                    ] = max(values)
        shape["transitions"].sort(key=lambda row: json.dumps(
            row["attrs"], sort_keys=True, separators=(",", ":")
        ))
    trajectory_shapes.sort(key=lambda row: (
        str(row["attrs"]["goal"]), str(row["attrs"]["name"])
    ))
    stored_program_signatures = {
        json.dumps(
            program["attrs"].get("signature")
            or motor_program_shape_signature(
                program["attrs"], program.get("members", [])
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        for shape in body_shapes
        for program in shape["programs"]
    }
    trajectory_endpoint_program_rows = [
        row
        for signature, row in sorted(trajectory_endpoint_programs.items())
        if signature not in stored_program_signatures
    ]
    plan_hints = []
    for hint in agent.inner.neighbours(
        agent.agent, "has_embodied_motor_plan_hint_library"
    ):
        hint_attrs = {
            key: value
            for key, value in agent.s.node(hint)["attrs"].items()
            if key != "source"
        }
        stages = []
        for stage in agent.inner.neighbours(
            hint, "has_embodied_motor_plan_hint_stage"
        ):
            stages.append({"attrs": {
                key: value
                for key, value in agent.s.node(stage)["attrs"].items()
                if key != "source"
            }})
        stages.sort(key=lambda row: float(row["attrs"].get("ordinal", 0.0)))
        plan_hints.append({"attrs": hint_attrs, "stages": stages})
    plan_hints = _coalesce_plan_hint_rows(plan_hints)
    developmental_capabilities = []
    for memory in agent.inner.neighbours(
        agent.agent,
        "has_embodied_developmental_capability_memory",
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "developmental capability memories must be output-null"
            )
        developmental_capabilities.append({"attrs": attrs})
    developmental_capabilities.sort(
        key=lambda row: (
            str(row["attrs"].get("goal", "")),
            str(row["attrs"].get("name", "")),
        )
    )
    developmental_experiences = []
    for memory in agent.inner.neighbours(
        agent.agent,
        "has_embodied_developmental_experience_memory",
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("status") == "superseded":
            continue
        if attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "developmental experience memories must be output-null"
            )
        contexts = [
            {
                "attrs": {
                    key: value
                    for key, value in agent.s.node(context)["attrs"].items()
                    if key != "source"
                }
            }
            for context in agent.inner.neighbours(
                memory,
                "has_embodied_developmental_experience_context",
            )
        ]
        contexts.sort(
            key=lambda row: json.dumps(
                row["attrs"].get("signature", ()),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        developmental_experiences.append({
            "attrs": attrs,
            "contexts": contexts,
        })
    developmental_experiences.sort(
        key=lambda row: (
            str(row["attrs"].get("goal", "")),
            str(row["attrs"].get("name", "")),
        )
    )
    metacognitive_learning_revisions = []
    for memory in agent.inner.neighbours(
        agent.agent,
        "has_metacognitive_learning_revision_memory",
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("status") == "superseded":
            continue
        if attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "metacognitive learning revision memories must be output-null"
            )
        if attrs.get("integer_native", 1) != 1:
            raise ValueError(
                "metacognitive learning revision memories must be integer-native"
            )
        metacognitive_learning_revisions.append({"attrs": attrs})
    metacognitive_learning_revisions.sort(
        key=lambda row: (
            str(row["attrs"].get("suspended_goal", "")),
            str(row["attrs"].get("redirect_goal", "")),
            str(row["attrs"].get("suspended_capability", "")),
            str(row["attrs"].get("redirect_capability", "")),
            int(row["attrs"].get("order_n", 0)),
        )
    )
    metacognitive_learning_counterexamples = []
    for memory in agent.inner.neighbours(
        agent.agent,
        "has_metacognitive_learning_counterexample_memory",
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("status") == "superseded":
            continue
        if attrs.get("output_authority", 0) != 0:
            raise ValueError(
                "metacognitive counterexample memories must be output-null"
            )
        mastery_context = [
            {"attrs": {
                key: value
                for key, value in agent.s.node(member)["attrs"].items()
                if key != "source"
            }}
            for member in agent.inner.neighbours(
                memory, "has_metacognitive_counterexample_context_member"
            )
        ]
        mastery_context.sort(
            key=lambda row: str(row["attrs"].get("capability_name", ""))
        )
        metacognitive_learning_counterexamples.append({
            "attrs": attrs,
            "mastery_context": mastery_context,
        })
    metacognitive_learning_counterexamples.sort(key=lambda row: (
        str(row["attrs"].get("source_capability", "")),
        str(row["attrs"].get("failed_redirect_capability", "")),
        int(row["attrs"].get("order_n", 0)),
        tuple(
            str(member["attrs"].get("capability_name", ""))
            for member in row.get("mastery_context", ())
        ),
    ))
    motor_proposal_shape_memories = []
    for memory in agent.inner.neighbours(
        agent.agent, "has_motor_proposal_shape_memory"
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("output_authority", 0) != 0:
            raise ValueError("motor proposal shape memories must be output-null")
        if attrs.get("integer_native", 1) != 1:
            raise ValueError("motor proposal shape memories must be integer-native")
        proposal_body_shapes = []
        for body in agent.inner.neighbours(
            memory, "has_motor_proposal_body_shape_memory"
        ):
            body_attrs = {
                key: value
                for key, value in agent.s.node(body)["attrs"].items()
                if key != "source"
            }
            if body_attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "motor proposal body memories must be output-null"
                )
            if body_attrs.get("integer_native", 1) != 1:
                raise ValueError(
                    "motor proposal body memories must be integer-native"
                )
            proposal_body_shapes.append({"attrs": body_attrs})
        proposal_body_shapes.sort(
            key=lambda row: str(row["attrs"].get("name", ""))
        )
        motor_proposal_shape_memories.append({
            "attrs": attrs,
            "body_shapes": proposal_body_shapes,
        })
    motor_proposal_shape_memories.sort(
        key=lambda row: str(row["attrs"].get("name", ""))
    )
    motor_proposal_counterexamples = []
    for memory in agent.inner.neighbours(
        agent.agent, "has_motor_proposal_counterexample"
    ):
        attrs = {
            key: value
            for key, value in agent.s.node(memory)["attrs"].items()
            if key != "source"
        }
        if attrs.get("output_authority", 0) != 0:
            raise ValueError("motor proposal counterexamples must be output-null")
        if attrs.get("integer_native", 1) != 1:
            raise ValueError("motor proposal counterexamples must be integer-native")
        motor_proposal_counterexamples.append({"attrs": attrs})
    motor_proposal_counterexamples.sort(key=lambda row: (
        json.dumps(
            row["attrs"].get("question_signature", ()),
            sort_keys=True,
            separators=(",", ":"),
        ),
        json.dumps(
            row["attrs"].get("body_signature", ()),
            sort_keys=True,
            separators=(",", ":"),
        ),
    ))
    caregiver_support_models = [
        {"attrs": dict(agent.s.node(model)["attrs"])}
        for episode in agent.s.nodes("HumanoidEpisode")
        for model in agent.inner.neighbours(
            episode, "has_caregiver_support_action_model"
        )
        if int(agent.s.node(model)["attrs"].get("initialized", 0)) == 1
    ]
    caregiver_support_models.sort(
        key=lambda row: str(row["attrs"].get("token", ""))
    )
    locomotor_phenotypes = []
    for development in agent.s.nodes("EmbodiedDevelopmentEpisode"):
        for phenotype in agent.inner.neighbours(
            development, "has_embodied_locomotor_phenotype"
        ):
            attrs = {
                key: value
                for key, value in agent.s.node(phenotype)["attrs"].items()
                if key != "source"
            }
            if attrs.get("output_authority", 0) != 0:
                raise ValueError("locomotor phenotypes must be output-null")
            attrs["shape_order"] = 1
            attrs["status"] = "hypothesis"
            attrs["refinement_required"] = 0
            attrs["selected_refinement_order"] = 0
            attrs["shape_residual_kind"] = "unresolved"
            attrs["last_receipt_seq"] = 0
            locomotor_phenotypes.append({"attrs": attrs})
    locomotor_phenotypes.sort(
        key=lambda row: str(row["attrs"].get("key", ""))
    )
    locomotor_phenotype_families = []
    for development in agent.s.nodes("EmbodiedDevelopmentEpisode"):
        for family in agent.inner.neighbours(
            development, "has_embodied_locomotor_phenotype_family"
        ):
            attrs = {
                key: value
                for key, value in agent.s.node(family)["attrs"].items()
                if key != "source"
            }
            if attrs.get("output_authority", 0) != 0:
                raise ValueError(
                    "locomotor phenotype families must be output-null"
                )
            # A Pareto candidate is episode-local relational evidence. The
            # sufficient statistics survive; verification is replayed in the
            # new context before the family can re-enter its frontier.
            attrs["status"] = "hypothesis"
            attrs["last_receipt_seq"] = 0
            locomotor_phenotype_families.append({"attrs": attrs})
    locomotor_phenotype_families.sort(
        key=lambda row: str(row["attrs"].get("key", ""))
    )
    return {
        "version": MOTOR_LIBRARY_VERSION,
        "developmental_curriculum_contract": (
            developmental_curriculum_contract()
        ),
        "body_shapes": body_shapes,
        "program_trajectory_shapes": trajectory_shapes,
        "program_trajectory_endpoint_programs": (
            trajectory_endpoint_program_rows
        ),
        "plan_hints": plan_hints,
        "developmental_capabilities": developmental_capabilities,
        "developmental_experiences": developmental_experiences,
        "somatomotor_couplings": _somatomotor_coupling_snapshot(agent),
        "caregiver_support_models": caregiver_support_models,
        "locomotor_phenotypes": locomotor_phenotypes,
        "locomotor_phenotype_families": locomotor_phenotype_families,
        "metacognitive_learning_revisions": metacognitive_learning_revisions,
        "metacognitive_learning_counterexamples": (
            metacognitive_learning_counterexamples
        ),
        "motor_proposal_shape_memories": motor_proposal_shape_memories,
        "motor_proposal_counterexamples": motor_proposal_counterexamples,
    }


def _request_motor_library_consolidation(
    agent: WorldAdapter,
    episode,
) -> None:
    """Deliver an episode-boundary event; graph rules select retention."""
    attrs = agent.s.node(episode)["attrs"]
    sequence = float(attrs.get("library_consolidation_seq", 0.0)) + 1.0
    agent.inner.set_attr(episode, "library_consolidation_seq", sequence)
    agent.inner.set_attr(episode, "library_consolidation_requested", 1.0)
    _tick_agent(agent)
    agent.inner.set_attr(episode, "library_consolidation_requested", 0.0)


def _configuration(protocol: dict[str, Any]) -> HumanoidBodyConfiguration:
    body = protocol["body"]
    time_step = float(body["time_step_seconds"])
    return HumanoidBodyConfiguration(
        time_step=time_step,
        gravity_acceleration=float(body["gravity_acceleration"]),
        action_frames=1,
        settling_frames=int(body["initial_settling_frames"]),
        joint_twitch_radians=float(body["joint_twitch_radians"]),
        maximum_joint_force=float(body["maximum_joint_force"]),
        position_gain=float(body["position_gain"]),
        velocity_gain=float(body["velocity_gain"]),
        initial_base_quarter_turns=tuple(
            int(value)
            for value in body.get("initial_base_quarter_turns", (0, 0, 0))
        ),
        asset=str(protocol.get("asset", HUMANOID_ASSET)),
    )


def _support_code(observation: dict[str, Any]) -> int:
    support = observation["support_contact_forces"]
    if len(support) != 2:
        raise RuntimeError(
            f"expected two support sensors, found {len(support)}"
        )
    active = tuple(float(row["normal_force"]) > 0.0 for row in support)
    if active == (True, False):
        return 1
    if active == (False, True):
        return 2
    return 0


def _phase_model_rows(agent: WorldAdapter, episode) -> list[dict[str, Any]]:
    rows = []
    for model in agent.inner.neighbours(
        episode,
        "has_humanoid_phase_action_model",
    ):
        attrs = agent.s.node(model)["attrs"]
        rows.append({
            key: attrs.get(key)
            for key in (
                "token",
                "ordinal",
                "support_phase",
                "context_id",
                "context_grounded",
                "configuration_shape",
                "initialized",
                "experience_count",
                "prediction_authority",
                "prediction_confirmation_count",
                "prediction_invalidation_count",
                "prediction_reground_count",
                "prediction_grounding_status",
                "last_prediction_receipt_seq",
                "last_reground_receipt_seq",
                "mean_dzx",
                "mean_dzy",
                "mean_dwx",
                "mean_dwy",
                "mean_dvx",
                "mean_dvy",
                "mean_dvz",
                "mean_input_energy_joules",
                "support_loss_ema",
            )
        })
    return sorted(
        rows,
        key=lambda row: (
            float(row["support_phase"]),
            float(row["ordinal"]),
        ),
    )


def _run_arm(
    protocol: dict[str, Any],
    mode: str,
    *,
    world_factory: Callable[
        [HumanoidBodyConfiguration, int], Any
    ] | None = None,
    motor_library: dict[str, Any] | None = None,
    motor_library_out: Path | None = None,
    observer: Callable[[Any, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    configuration = _configuration(protocol)
    calibration = protocol["calibration"]
    locomotion = protocol["locomotion"]
    evaluation = protocol["evaluation"]
    curriculum = protocol.get("curriculum")
    developmental_curriculum = bool(
        curriculum is not None and curriculum.get("developmental", False)
    )
    seed_names = ["humanoid_adaptation"]
    if mode == "directed_walk":
        seed_names.extend((
            "control_regime_escalation",
            "humanoid_control_regime",
        ))
    if curriculum is not None:
        if developmental_curriculum:
            seed_names.extend((
                "humanoid_developmental_curriculum",
                "embodied_body_ingest",
            ))
        else:
            seed_names.append("humanoid_coordination_curriculum")
        if curriculum.get("kinematics_study", False):
            seed_names.append("humanoid_kinematics_study")
    agent = WorldAdapter(seeds=tuple(seed_names))
    policy = _one_node(agent, "HumanoidPolicy")
    agent.inner.set_attr(
        policy,
        "babble_samples",
        float(calibration["samples_per_non_tonic_actuator"]),
    )
    agent.inner.set_attr(
        policy,
        "minimum_upright_height_fraction",
        float(evaluation["minimum_upright_height_fraction"]),
    )
    agent.inner.set_attr(
        policy,
        "maximum_lateral_drift_metres",
        float(evaluation["maximum_final_lateral_drift_metres"]),
    )
    agent.inner.set_attr(
        policy,
        "gravity_acceleration",
        configuration.gravity_acceleration,
    )
    agent.inner.set_attr(
        policy,
        "target_froude_speed",
        float(locomotion["target_froude_speed"]),
    )
    support_geometry_preview_authority = float(
        locomotion.get("support_geometry_preview_authority", 0.0)
    )
    if support_geometry_preview_authority not in (0.0, 1.0):
        raise ValueError(
            "support_geometry_preview_authority must be 0.0 or 1.0"
        )
    agent.inner.set_attr(
        policy,
        "support_geometry_preview_authority",
        support_geometry_preview_authority,
    )
    persistent_task_residual_authority = float(
        locomotion.get("persistent_task_residual_authority", 0.0)
    )
    if persistent_task_residual_authority not in (0.0, 1.0):
        raise ValueError(
            "persistent_task_residual_authority must be 0.0 or 1.0"
        )
    agent.inner.set_attr(
        policy,
        "persistent_task_residual_authority",
        persistent_task_residual_authority,
    )
    foveated_program_exploration_authority = float(
        locomotion.get("foveated_program_exploration_authority", 0.0)
    )
    if foveated_program_exploration_authority not in (0.0, 1.0):
        raise ValueError(
            "foveated_program_exploration_authority must be 0.0 or 1.0"
        )
    agent.inner.set_attr(
        policy,
        "foveated_program_exploration_authority",
        foveated_program_exploration_authority,
    )
    future_manifold_enabled = float(
        locomotion.get("future_manifold_enabled", 0.0)
    )
    temporal_anchors_enabled = float(
        locomotion.get("future_manifold_temporal_anchors_enabled", 0.0)
    )
    for name, value in (
        ("future_manifold_enabled", future_manifold_enabled),
        (
            "future_manifold_temporal_anchors_enabled",
            temporal_anchors_enabled,
        ),
    ):
        if value not in (0.0, 1.0):
            raise ValueError(f"{name} must be 0.0 or 1.0")
        agent.inner.set_attr(policy, name, value)
    agent.inner.set_attr(
        policy,
        "future_manifold_local_refinement_enabled",
        temporal_anchors_enabled,
    )
    target_directed_progress_m = float(
        locomotion.get("target_directed_progress_m", 3.0)
    )
    if target_directed_progress_m <= 0.0:
        raise ValueError("target_directed_progress_m must be positive")
    world_context = (
        PyBulletHumanoidWorld(
            configuration,
            seed=int(protocol["seed"]),
        )
        if world_factory is None
        else world_factory(configuration, int(protocol["seed"]))
    )
    with world_context as world:
        observation = world.observe()
        if observer is not None:
            observer(world, {
                "phase": "cold_start",
                "action": -1,
                "observation": observation,
                "event": "fresh_graph",
            })
        body_shape_signature = world.body_shape_signature()
        body_shape_name = _body_shape_name(body_shape_signature)
        agent.inner.set_attr(
            policy,
            "support_phase_prior_strength",
            float((len(observation["support_contact_forces"]) + 1) ** 2),
        )
        agent.inner.set_attr(
            policy,
            "gait_surprise_confirmation_receipts",
            float(
                len(observation["base_linear_velocity"])
                * len(observation["support_contact_forces"])
            ),
        )
        standing_reference_z = float(
            observation["body_length_scale"]
            if developmental_curriculum
            else observation["base_position"][2]
        )
        episode = agent.s.add_node("HumanoidEpisode", {
            "mode": mode,
            "phase": "calibration",
            "action_ready": 0.0,
            "request_seq": 0.0,
            "decision_seq": 0.0,
            "decision_count": 0.0,
            "last_trial_request_seq": 0.0,
            "state_seq": 0.0,
            "measured_state_seq": -1.0,
            "standing_reference_z": standing_reference_z,
            "minimum_height_seen": standing_reference_z,
            "peak_tilt_seen": 0.0,
            "recovery_measurements_initialized": 0.0,
            "upright": 1.0,
            "heading_x": float(locomotion["heading_x"]),
            "locomotion_measurements_initialized": 0.0,
            "locomotion_measured_state_seq": -1.0,
            "locomotion_start_x": 0.0,
            "locomotion_start_y": 0.0,
            "directed_progress": 0.0,
            "target_directed_progress_m": target_directed_progress_m,
            "locomotion_residual_m": target_directed_progress_m,
            "locomotion_drive_active": 1.0,
            "active_gait_attractor_ordinal": 0.0,
            "active_residual_regime_ordinal": 0.0,
            "residual_regime_window_sample_count": 0.0,
            "residual_regime_window_complete": 0.0,
            "residual_regime_selection_count": 0.0,
            "maximum_directed_progress": 0.0,
            "lateral_offset": 0.0,
            "maximum_lateral_excursion": 0.0,
            "locomotor_path_length": 0.0,
            "locomotor_forward_reversal_count": 0.0,
            "locomotor_cycle_count": 0.0,
            "last_directed_step": 0.0,
            "last_locomotor_token": "",
            "locomotor_prior_reset_seq": 0.0,
            "walking_minimum_height": standing_reference_z,
            "walking_peak_tilt": 0.0,
            "walking_mean_tilt": 0.0,
            "walking_tilt_sample_count": 0.0,
            "walking_peak_abs_vx": 0.0,
            "walking_peak_abs_vy": 0.0,
            "walking_peak_prediction_error": 0.0,
            "latest_gait_prediction_error": 0.0,
            "gait_surprise_streak": 0.0,
            "support_alternations": 0.0,
            "aerial_samples": 0.0,
            "double_support_samples": 0.0,
            "support_topology_samples": 0.0,
            "aerial_active": 0.0,
            "last_unilateral_support": 0.0,
            "current_support_phase": 0.0,
            "support_sensor_count": float(
                len(observation["support_contact_forces"])
            ),
            "active_support_count": float(sum(
                1 for _row in observation.get(
                    "whole_body_support_contacts", ()
                )
            )),
            "active_distal_support_count": float(sum(
                float(row["normal_force"]) > 0.0
                for row in observation["support_contact_forces"]
            )),
            "online_phase_learning": 1.0,
            "last_phase_learning_request_seq": 0.0,
            "phase_adaptation_complete": 0.0,
            "evaluation_active": 0.0,
            "recovery_mode": 0.0,
            "recovery_mode_entries": 0.0,
            "recovery_mode_exits": 0.0,
            "recovery_action_count": 0.0,
            "learned_gait_tilt_envelope": 0.0,
            "learned_gait_mean_tilt": 0.0,
            "learned_gait_vx_envelope": 0.0,
            "learned_gait_vy_envelope": 0.0,
            "learned_gait_prediction_error_envelope": 0.0,
            "physics_time_step": configuration.time_step,
            "control_integration_frames": float(
                observation.get("control_integration_frames", 0.0)
            ),
            "response_horizon_initialized": 0.0,
            "nominal_response_frames": 0.0,
            "response_frames": 0.0,
            "manifold_bounds_ready": 0.0,
            "manifold_bound_dzx": 0.0,
            "manifold_bound_dzy": 0.0,
            "manifold_bound_dwx": 0.0,
            "manifold_bound_dwy": 0.0,
            "manifold_bound_dvx": 0.0,
            "manifold_bound_dvy": 0.0,
            "manifold_bound_dvz": 0.0,
            "topology_focused_response_count": 0.0,
            "motor_primary_ready": 0.0,
            "selected_primary_context_id": 0.0,
            "motor_recovery_primary_ready": 0.0,
            "compound_response_interval": 0.0,
            "last_compound_decision_count": 0.0,
            "motor_fixation_count": 0.0,
            "motor_configuration_transition_count": 0.0,
            "motor_efference_copy_count": 0.0,
            "motor_efference_confirmation_count": 0.0,
            "motor_reference_request_seq": 0.0,
            "selected_motor_reference_positions": (),
            "selected_motor_reference_shape": (),
            "selected_motor_reference_kind": "unbound",
            "motor_fixture_reset_seq": 0.0,
            "motor_fixture_reset_processed_seq": 0.0,
            "single_action_effect_envelope": 0.0,
            "single_action_tilt_envelope": 0.0,
            "synergy_calibration_complete": 0.0,
            "synergy_probe_anchor_ordinal": 1.0,
            "motor_memory_recall_count": 0.0,
            "motor_memory_structural_reuse_count": 0.0,
            "motor_sequence_recall_count": 0.0,
            "motor_sequence_transition_count": 0.0,
            "last_motor_sequence_receipt_seq": 0.0,
            "motor_preparation_count": 0.0,
            "motor_preparation_release_count": 0.0,
            "reset_requested": 0.0,
            "body_reset_seq": 0.0,
            "body_reset_processed_seq": 0.0,
            "get_up_attempt_count": 0.0,
            "get_up_last_improvement_attempt": 0.0,
            "get_up_exploitation_start_attempt": 0.0,
            "get_up_success_count": 0.0,
            "get_up_reset_count": 0.0,
            "recovery_basin_count": 0.0,
            "recovery_basin_start_attempt": 0.0,
            "recovery_basin_transition_count": 0.0,
            "recovery_basin_action_count": 0.0,
            "recovery_composition_count": 0.0,
            "recovery_warm_start_count": 0.0,
            "recovery_path_recall_count": 0.0,
            "recovery_path_hint_count": 0.0,
            "recovery_reanchor_count": 0.0,
            "recovery_program_count": 0.0,
            "recovery_program_repeat_count": 0.0,
            "recovery_program_termination_count": 0.0,
            "lifetime_completed_progress": 0.0,
            "next_phase_context_id": 0.0,
            "body_shape_name": body_shape_name,
            "body_shape_signature": body_shape_signature,
            "body_shape_initialized": 0.0,
            "warm_start_shape_recognized": 0.0,
            "warm_start_program_count": 0.0,
            "motor_plan_query_signature": (
                ("motor_task", (
                    "locomotion" if mode == "directed_walk" else mode
                )),
            ),
            "motor_plan_active_query_context": (
                "locomotion" if mode == "directed_walk" else mode
            ),
            "motor_plan_locomotion_query_signature": (
                ("motor_task", "locomotion"),
            ),
            "motor_plan_self_takeoff_query_signature": (
                ("motor_task", "self_takeoff"),
            ),
            "motor_plan_hint_count": 0.0,
            "motor_plan_basin_seed_count": 0.0,
            "motor_plan_hint_escalation_count": 0.0,
            "gravity_acceleration": configuration.gravity_acceleration,
            "body_mass": float(observation["body_mass"]),
            "joint_twitch_radians": configuration.joint_twitch_radians,
            "maximum_joint_force": configuration.maximum_joint_force,
            "position_gain": configuration.position_gain,
            "velocity_gain": configuration.velocity_gain,
            "curriculum_active": float(
                curriculum is not None and mode == "directed_walk"
            ),
            "developmental_curriculum_active": int(
                developmental_curriculum and mode == "directed_walk"
            ),
            "somatomotor_wave_enabled": int(
                developmental_curriculum
                and mode == "directed_walk"
                and curriculum.get("somatomotor_waves", True)
            ),
            "caregiver_scaffold_enabled": int(
                developmental_curriculum
                and mode == "directed_walk"
                and curriculum.get("caregiver_scaffolding", False)
            ),
            "caregiver_scaffold_mode": str(
                curriculum.get("caregiver_scaffolding_mode", "contingent")
                if curriculum is not None else "contingent"
            ),
            "caregiver_scaffold_session_active": 0,
            "caregiver_scaffold_request_count": 0,
            "caregiver_scaffold_receipt_count": 0,
            "caregiver_scaffold_handoff_ready": 0,
            "caregiver_scaffold_mismatch_count": 0,
            "caregiver_scaffold_withdrawn": 0,
            "caregiver_passive_scaffold_withdrawn": 0,
            "caregiver_scaffold_unresolved": 0,
            "caregiver_protective_support_available": int(
                developmental_curriculum
                and mode == "directed_walk"
                and curriculum.get("caregiver_scaffolding", False)
            ),
            "caregiver_protective_support_requested": 0,
            "caregiver_support_counterfactual_authority": int(
                os.environ.get(
                    "HUMANOID_SUPPORT_COUNTERFACTUAL_AUTHORITY", "0"
                ) == "1"
            ),
            "caregiver_support_counterfactual_loss_floor": float(
                os.environ.get(
                    "HUMANOID_SUPPORT_COUNTERFACTUAL_LOSS_FLOOR", "1"
                )
            ),
            "caregiver_support_scale": 0.0,
            "caregiver_protected_action_count": 0,
            "caregiver_unbuffered_action_count": 0,
            "caregiver_bounce_requested": 0,
            "caregiver_bounce_completed": 0,
            "caregiver_support_calibration_requested": 0,
            "caregiver_support_calibration_kind": "none",
            "caregiver_support_calibration_complete": 0,
            "developmental_stage_ordinal": 0,
            "developmental_stage_transition_count": 0,
            "developmental_goal": "inactive",
            "developmental_stage_entry_shape": (),
            "developmental_stage_entry_x": 0,
            "developmental_stage_entry_y": 0,
            "developmental_stage_entry_z": 0,
            "developmental_stage_entry_support_count": 0,
            "developmental_stage_entry_support_extent_squared": 0,
            "developmental_stage_entry_upright_receipts": 0,
            "curriculum_challenge_request_seq": 0.0,
            "curriculum_challenge_applied_seq": 0.0,
            "curriculum_active_challenge_ordinal": -1.0,
            "curriculum_last_request_seq": -float(
                (len(observation["support_contact_forces"]) + 1) ** 2
            ),
            "curriculum_last_challenge_cycle_count": 0.0,
            "curriculum_pending_baseline_directed_progress": 0.0,
            "curriculum_pending_baseline_cycle_count": 0.0,
            "curriculum_force_x_body_weights": 0.0,
            "curriculum_force_y_body_weights": 0.0,
            "curriculum_force_z_body_weights": 0.0,
            "curriculum_force_frames": 1.0,
            "curriculum_external_impulse_authority": 1.0,
            "curriculum_completed_challenges": 0.0,
            "curriculum_safe_challenges": 0.0,
            "curriculum_stage_ordinal": 0.0,
            "self_takeoff_drive_active": 0.0,
            "self_takeoff_target_velocity_scale": 0.0,
            "self_takeoff_compression_scale": 0.0,
            "curriculum_recovery_pending": 0.0,
            "curriculum_pending_recovery_request_seq": 0.0,
            "curriculum_warm_memory_count": 0.0,
            "kinematics_study_active": 0.0,
            "kinematics_reprobe_complete": 0.0,
            "kinematic_reach_initialized": 0.0,
            "kinematic_reach_complete": 0.0,
            "kinematic_reach_success": 0.0,
            "kinematic_reach_point_ordinal": -1.0,
            "kinematic_reach_target_mode": "nearest_learned_affordance",
            "kinematic_reach_basis_token_a": "",
            "kinematic_reach_basis_token_b": "",
            "kinematic_reach_basis_group_a": -1.0,
            "kinematic_reach_primary_initialized": 0.0,
            "kinematic_reach_secondary_initialized": 0.0,
            "kinematic_reach_basis_a_dx": 0.0,
            "kinematic_reach_basis_a_dy": 0.0,
            "kinematic_reach_basis_a_dz": 0.0,
            "kinematic_reach_basis_b_dx": 0.0,
            "kinematic_reach_basis_b_dy": 0.0,
            "kinematic_reach_basis_b_dz": 0.0,
            "kinematic_reach_direction_dx": 0.0,
            "kinematic_reach_direction_dy": 0.0,
            "kinematic_reach_direction_dz": 0.0,
            "kinematic_reach_target_dx": 0.0,
            "kinematic_reach_target_dy": 0.0,
            "kinematic_reach_target_dz": 0.0,
            "kinematic_reach_achieved_dx": 0.0,
            "kinematic_reach_achieved_dy": 0.0,
            "kinematic_reach_achieved_dz": 0.0,
            "kinematic_reach_residual_dx": 0.0,
            "kinematic_reach_residual_dy": 0.0,
            "kinematic_reach_residual_dz": 0.0,
            "kinematic_reach_initial_error": 0.0,
            "kinematic_reach_error": 0.0,
            "kinematic_reach_previous_error": 0.0,
            "kinematic_reach_success_threshold": 0.0,
            "kinematic_reach_attempt_count": 0.0,
            "kinematic_reach_attempt_limit": 0.0,
            "kinematic_reach_last_receipt_seq": 0.0,
            "kinematic_reach_goal_seq": 0.0,
            "kinematic_reach_goal_id": 0.0,
            "kinematic_reach_selected_compound": 0.0,
            "kinematic_reach_selected_predicted_dx": 0.0,
            "kinematic_reach_selected_predicted_dy": 0.0,
            "kinematic_reach_selected_predicted_dz": 0.0,
            "regime_monitor_enabled": 0.0,
            "regime_clock_seq": 0.0,
            "regime_evidence_seq": 0.0,
            "regime_evidence_horizon_actions": float(
                len(observation["support_contact_forces"]) ** 2
            ),
            "regime_ordinal": 0.0,
            "regime_max_ordinal": 2.0,
            "regime_escalation_requested": 0.0,
            "regime_escalation_count": 0.0,
            "regime_last_escalation_seq": 0.0,
            "regime_applied_ordinal": 0.0,
            "regime_last_cycle_count": 0.0,
            "regime_best_progress": 0.0,
            "render_first_suspended": 0.0,
            "async_trust_epoch": 0.0,
            "cognitive_continuation_authority": 1,
            "cognitive_checkin_terminal": 0,
        })
        _edge(agent, agent.agent, "has_humanoid_episode", episode)
        development_context = None
        selected_program_path_rows = []
        if developmental_curriculum:
            attached_transducer = PyBulletHumanoidTrialTransducer.for_attached_world(
                configuration,
                world,
                seed=int(protocol["seed"]),
            )
            attached_transducer.publish_body_world_capabilities(agent)
            _tick_agent(agent)
            situated_development_contexts = [
                node
                for node in agent.s.nodes("EmbodiedDevelopmentEpisode")
                if agent.s.node(node)["attrs"].get("status") == "situated_ready"
            ]
            if len(situated_development_contexts) != 1:
                raise RuntimeError(
                    "body ingest must materialize exactly one situated "
                    "development episode"
                )
            development_context = situated_development_contexts[0]
            development_attrs = {
                    "body_capability_signature": tuple(
                        observation["body_capability_signature"]
                    ),
                    "development_evidence_window": int(
                        (len(observation["support_contact_forces"]) + 1) ** 2
                    ),
                    "development_effector_coverage_complete": 0,
                    "development_learning_active": 0,
                    "developmental_deployment_mode": int(
                        locomotion.get("developmental_deployment_mode", 0)
                    ),
                    "latest_development_receipt_seq": 0,
                    "embodied_developmental_mastery_count": 0,
                    "developmental_cross_body_warm_start_count": 0,
                    "developmental_exact_body_recall_count": 0,
                    "development_sparse_support_ceiling": 0,
                    "retained_developmental_experience_count": 0,
                    "caregiver_buffered_experience_count": 0,
                    "unbuffered_experience_count": 0,
                    "embodiment_reset_available": int(
                        protocol["body"].get("reset_available", True)
                    ),
                    "embodiment_reset_reachable": int(
                        protocol["body"].get("reset_available", True)
                    ),
                    "embodiment_reset_cost_units": int(
                        protocol["body"].get(
                            "reset_cost_units", configuration.settling_frames
                        )
                    ),
                    "caregiver_scaffolding_declared": int(
                        curriculum.get("caregiver_scaffolding", False)
                    ),
                    "caregiver_scaffolding_mode": curriculum.get(
                        "caregiver_scaffolding_mode", "undeclared"
                    ),
                    "protective_support_available": int(
                        curriculum.get("protective_support_available", False)
                    ),
                    "protective_support_effectiveness": float(
                        curriculum.get("protective_support_effectiveness", 0.0)
                    ),
                    "safe_learning_required_horizon_units": int(
                        curriculum.get("safe_learning_required_horizon_units", 1)
                    ),
                    "safe_learning_minimum_width_relaxation": float(
                        curriculum.get("safe_learning_minimum_width_relaxation", 0.0)
                    ),
                    "safe_learning_information_loss_allowance": float(
                        curriculum.get("safe_learning_information_loss_allowance", 0.0)
                    ),
                    "safe_learning_environment_declared": int(
                        curriculum.get("safe_learning_environment", False)
                    ),
                    "last_body_reset_cost_units": 0,
                    "embodiment_reset_cost_total_units": 0,
                    "embodiment_generation": 0,
                    "embodiment_reset_iteration_count": 0,
                    "embodiment_terminal": 0,
                    "terminal_receipt_seq": 0,
                    "embodied_reset_requested": 0,
                    "reset_requested": 0,
                    "body_reset_seq": 0,
                    "embodied_reset_processed_seq": 0,
                    "active_embodied_developmental_goal": "inactive",
                    "active_embodied_developmental_capability": "inactive",
                    "cognitive_continuation_authority": 1,
                    "cognitive_checkin_terminal": 0,
                    "output_authority": 0,
                    "integer_native": 1,
                }
            for attr_name, attr_value in development_attrs.items():
                agent.inner.set_attr(
                    development_context, attr_name, attr_value
                )
            _edge(
                agent,
                episode,
                "projects_embodied_development",
                development_context,
            )
            declared_reset_scenarios = curriculum.get(
                "reinstantiation_scenarios",
                ({
                    "name": "declared_initial_fixture",
                    "target_goal": "any",
                    "base_quarter_turns": list(
                        configuration.initial_base_quarter_turns
                    ),
                },),
            )
            for scenario_ordinal, scenario_spec in enumerate(
                declared_reset_scenarios
            ):
                quarter_turns = tuple(scenario_spec["base_quarter_turns"])
                if (
                    len(quarter_turns) != 3
                    or any(
                        isinstance(value, bool)
                        or not isinstance(value, int)
                        for value in quarter_turns
                    )
                ):
                    raise ValueError(
                        "reinstantiation scenario quarter turns must be "
                        "three integers"
                    )
                scenario = agent.s.add_node("EmbodiedResetScenario", {
                    "name": str(scenario_spec["name"]),
                    "ordinal": scenario_ordinal,
                    "target_goal": str(scenario_spec.get(
                        "target_goal", "any"
                    )),
                    "target_capability": str(scenario_spec.get(
                        "target_capability", "any"
                    )),
                    "fixture_quarter_turn_x": quarter_turns[0],
                    "fixture_quarter_turn_y": quarter_turns[1],
                    "fixture_quarter_turn_z": quarter_turns[2],
                    "selection_count": 0,
                    "enabled": int(scenario_spec.get("enabled", True)),
                    "integer_native": 1,
                    "output_authority": 0,
                })
                _edge(
                    agent,
                    development_context,
                    "has_embodied_reset_scenario",
                    scenario,
                )
        control_regime = None
        if mode == "directed_walk":
            control_regime = agent.s.add_node(
                "EmbodiedMotorProgramEpisode",
                {
                    "regime_monitor_enabled": 0.0,
                    "regime_clock_seq": 0.0,
                    "regime_evidence_seq": 0.0,
                    "regime_evidence_horizon_actions": float(
                        len(observation["support_contact_forces"]) ** 2
                    ),
                    "regime_ordinal": 0.0,
                    "regime_max_ordinal": 2.0,
                    "regime_escalation_requested": 0.0,
                    "regime_escalation_count": 0.0,
                    "regime_last_escalation_seq": 0.0,
                    "regime_last_cycle_count": 0.0,
                    "regime_best_progress": 0.0,
                },
            )
            _edge(
                agent,
                episode,
                "has_humanoid_control_regime",
                control_regime,
            )
            _edge(
                agent,
                agent.agent,
                "holds_control_regime",
                control_regime,
            )
        restored_library = _restore_motor_library(agent, motor_library)
        options = world.actuator_options()
        effector_topology = (
            install_name_free_effector_topology(
                agent,
                episode,
                options,
                body_shape_signature,
            )
            if curriculum is not None
            else None
        )
        agent.inner.set_attr(
            episode,
            "motor_effector_group_count",
            float(len({option["actuator_group"] for option in options})),
        )
        action_models = {}
        option_ordinals = {}
        support_regime_count = (
            len(observation["support_contact_forces"]) + 1
        )
        for ordinal, option in enumerate(options):
            model = agent.s.add_node("HumanoidActionModel", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "tonic_default": float(option["tonic_default"]),
                "actuator_group": float(option["actuator_group"]),
                "experience_count": 0.0,
                "mean_dzx": 0.0,
                "mean_dzy": 0.0,
                "mean_dwx": 0.0,
                "mean_dwy": 0.0,
                "mean_dvx": 0.0,
                "mean_dvy": 0.0,
                "mean_dvz": 0.0,
                "mean_input_energy_joules": 0.0,
                "support_loss_ema": 0.0,
                "support_deficit_ema": 0.0,
            })
            actuator = agent.s.add_node("OpaqueHumanoidActuator", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "semantics": "unknown",
            })
            _edge(agent, episode, "has_humanoid_action_model", model)
            _edge(agent, model, "models_humanoid_actuator", actuator)
            action_models[option["token"]] = model
            option_ordinals[option["token"]] = ordinal
            if float(option["tonic_default"]) < 0.5:
                get_up_model = agent.s.add_node(
                    "HumanoidGetUpActionModel",
                    {
                        "token": option["token"],
                        "ordinal": float(ordinal),
                        "actuator_group": float(
                            option["actuator_group"]
                        ),
                        "experience_count": 0.0,
                        "mean_height_gain": 0.0,
                        "mean_alignment_gain": 0.0,
                        "mean_translation_gain": 0.0,
                        "mean_whole_body_support_gain": 0.0,
                        "reversal_success_count": 0,
                        "support_topology_change_count": 0,
                        "stable_partial_motion_count": 0,
                        "last_update_request_seq": 0.0,
                    },
                )
                _edge(
                    agent,
                    episode,
                    "has_humanoid_get_up_action_model",
                    get_up_model,
                )
                _edge(
                    agent,
                    get_up_model,
                    "generalizes_humanoid_action_model",
                    model,
                )
                for support_phase in range(support_regime_count):
                    phase_model = agent.s.add_node(
                        "HumanoidPhaseActionModel",
                        {
                            "token": option["token"],
                            "ordinal": float(ordinal),
                            "support_phase": float(support_phase),
                            "actuator_group": float(
                                option["actuator_group"]
                            ),
                            "context_id": float(
                                ordinal * support_regime_count
                                + support_phase
                            ),
                            "context_grounded": 0.0,
                            "configuration_shape": None,
                            "initialized": 0.0,
                            "experience_count": 0.0,
                            "mean_dzx": 0.0,
                            "mean_dzy": 0.0,
                            "mean_dwx": 0.0,
                            "mean_dwy": 0.0,
                            "mean_dvx": 0.0,
                            "mean_dvy": 0.0,
                            "mean_dvz": 0.0,
                            "mean_input_energy_joules": 0.0,
                            "support_loss_ema": 0.0,
                            "support_deficit_ema": 0.0,
                            "anchor_z_x": 0.0,
                            "anchor_z_y": 0.0,
                            "anchor_wx": 0.0,
                            "anchor_wy": 0.0,
                            "anchor_vx": 0.0,
                            "anchor_vy": 0.0,
                            "anchor_vz": 0.0,
                            "anchor_lateral_offset": 0.0,
                            "context_radius_energy": 0.0,
                        },
                    )
                    _edge(
                        agent,
                        episode,
                        "has_humanoid_phase_action_model",
                        phase_model,
                    )
                    _edge(
                        agent,
                        phase_model,
                        "generalizes_humanoid_action_model",
                        model,
                    )
        if effector_topology is not None:
            bind_effector_models(agent, effector_topology, action_models)
        agent.inner.set_attr(
            episode,
            "next_phase_context_id",
            float(len(options) * support_regime_count),
        )
        kinematics_terminal_point_count = (
            install_opaque_kinematic_topology(
                agent,
                episode,
                body_shape_signature,
            )
            if curriculum is not None
            and curriculum.get("kinematics_study", False)
            else 0
        )

        probe_count = sum(
            float(option["tonic_default"]) < 0.5 for option in options
        )
        non_tonic_options = [
            option
            for option in options
            if float(option["tonic_default"]) < 0.5
        ]
        synergy_count = 0
        for option_a, option_b in combinations(non_tonic_options, 2):
            if option_a["actuator_group"] == option_b["actuator_group"]:
                continue
            synergy = agent.s.add_node("HumanoidSynergyModel", {
                "ordinal": float(synergy_count),
                "token_a": option_a["token"],
                "token_b": option_b["token"],
                "ordinal_a": float(option_ordinals[option_a["token"]]),
                "ordinal_b": float(option_ordinals[option_b["token"]]),
                "initialized": 0.0,
                "probed": 0.0,
                "approved": 0.0,
                "rejected": 0.0,
                "residual_magnitude": 0.0,
                "support_loss_ema": 0.0,
                "support_deficit_ema": 0.0,
                "mean_input_energy_joules": 0.0,
                "experience_count": 0.0,
                "last_program_update_request_seq": 0.0,
                **{
                    f"{prefix}_{axis}": 0.0
                    for prefix in ("predicted", "mean", "residual")
                    for axis in (
                        "dzx",
                        "dzy",
                        "dwx",
                        "dwy",
                        "dvx",
                        "dvy",
                        "dvz",
                    )
                },
            })
            _edge(agent, episode, "has_humanoid_synergy_model", synergy)
            _edge(
                agent,
                synergy,
                "has_humanoid_synergy_primary",
                action_models[option_a["token"]],
            )
            _edge(
                agent,
                synergy,
                "has_humanoid_synergy_secondary",
                action_models[option_b["token"]],
            )
            synergy_count += 1
        agent.inner.set_attr(
            policy,
            "synergy_probe_budget",
            float(probe_count),
        )
        caregiver_scaffold_trace = (
            _run_caregiver_scaffold(agent, episode, world)
            if int(agent.s.node(episode)["attrs"].get(
                "caregiver_scaffold_enabled", 0
            )) == 1
            else []
        )
        calibration_trace = []
        request_seq = 0
        for _ in range(
            probe_count
            * int(calibration["samples_per_non_tonic_actuator"])
        ):
            if calibration["reset_body_before_each_sample"]:
                observation = world.reset()
            request_seq += 1
            before = observation
            token, trial, decision = _request_action(
                agent,
                episode,
                before,
                request_seq=request_seq,
            )
            after = _enact_graph_command(world, token, decision)
            if observer is not None:
                observer(world, {
                    "phase": "motor_babble",
                    "action": request_seq,
                    "observation": after,
                    "event": None,
                    "decision_kind": decision["decision_kind"],
                })
            trial_after = _close_action(
                agent,
                episode,
                trial,
                before,
                after,
                request_seq=request_seq,
            )
            if trial_after.get("status") != "learned":
                raise RuntimeError(
                    "graph did not learn humanoid motor receipt: "
                    f"{trial_after!r}"
                )
            calibration_trace.append({
                "request_seq": request_seq,
                "selected_token": token,
                "selected_secondary_token": decision[
                    "selected_secondary_token"
                ],
                "orientation_class_before": (
                    _gravity_relative_orientation_class(
                        _gravity_relative_up_axis(tuple(
                            float(value) for value in
                            before["base_orientation_xyzw"]
                        ))
                    )
                ),
                "orientation_class_after": (
                    _gravity_relative_orientation_class(
                        _gravity_relative_up_axis(tuple(
                            float(value) for value in
                            after["base_orientation_xyzw"]
                        ))
                    )
                ),
                "response_frames": decision["selected_response_frames"],
                "decision_kind": decision["decision_kind"],
                "collapse_kind": decision.get(
                    "selected_collapse_kind",
                    trial_after.get("collapse_kind", "unclassified"),
                ),
                "open_residual_count": trial_after.get(
                    "open_residual_count",
                    1.0,
                ),
                "caregiver_protective_support_applied": int(after.get(
                    "caregiver_protective_support_applied", 0
                )),
                "caregiver_support_impulse_newton_seconds": float(after.get(
                    "caregiver_support_impulse_newton_seconds", 0.0
                )),
                "base_height": float(after["base_position"][2]),
                "peak_contact_force_newtons": float(after.get(
                    "peak_contact_force_newtons", 0.0
                )),
            })
            observation = after

        agent.inner.set_attr(episode, "phase", "synergy_calibration")
        synergy_trace = []
        for _ in range(synergy_count):
            if (
                agent.s.node(episode)["attrs"].get(
                    "synergy_calibration_complete"
                )
                == 1.0
            ):
                break
            observation = world.reset()
            request_seq += 1
            before = observation
            token, trial, decision = _request_action(
                agent,
                episode,
                before,
                request_seq=request_seq,
            )
            after = _enact_graph_command(world, token, decision)
            if observer is not None:
                observer(world, {
                    "phase": "synergy_learning",
                    "action": request_seq,
                    "observation": after,
                    "event": None,
                    "decision_kind": decision["decision_kind"],
                })
            trial_after = _close_action(
                agent,
                episode,
                trial,
                before,
                after,
                request_seq=request_seq,
            )
            if trial_after.get("status") != "synergy_learned":
                raise RuntimeError(
                    "graph did not learn staged synergy receipt"
                )
            synergy_trace.append({
                "request_seq": request_seq,
                "selected_token": token,
                "selected_secondary_token": decision[
                    "selected_secondary_token"
                ],
                "response_frames": decision["selected_response_frames"],
            })
            observation = after
        if (
            agent.s.node(episode)["attrs"].get(
                "synergy_calibration_complete"
            )
            != 1.0
        ):
            raise RuntimeError("graph did not close synergy calibration")

        kinematics_reprobe_trace = []
        kinematic_reach_trace = []
        kinematic_reach_result = None
        if (
            curriculum is not None
            and curriculum.get("kinematics_study", False)
        ):
            agent.inner.set_attr(episode, "phase", "kinematics_reprobe")
            agent.inner.set_attr(
                episode,
                "kinematics_reprobe_complete",
                0.0,
            )
            agent.inner.set_attr(episode, "action_ready", 0.0)
            reprobe_limit = (
                probe_count
                * len(observation["support_contact_forces"])
            )
            for _ in range(reprobe_limit):
                if (
                    agent.s.node(episode)["attrs"].get(
                        "kinematics_reprobe_complete"
                    )
                    == 1.0
                ):
                    break
                observation = world.reset()
                request_seq += 1
                before = observation
                requested = _request_action(
                    agent,
                    episode,
                    before,
                    request_seq=request_seq,
                    allow_no_action=True,
                )
                if requested is None:
                    if (
                        agent.s.node(episode)["attrs"].get(
                            "kinematics_reprobe_complete"
                        )
                        == 1.0
                    ):
                        break
                    raise RuntimeError(
                        "graph emitted neither a kinematic reprobe nor "
                        "a completed curriculum receipt"
                    )
                token, trial, decision = requested
                after = _enact_graph_command(world, token, decision)
                _close_action(
                    agent,
                    episode,
                    trial,
                    before,
                    after,
                    request_seq=request_seq,
                )
                kinematics_reprobe_trace.append({
                    "request_seq": request_seq,
                    "selected_token": token,
                    "selected_secondary_token": decision[
                        "selected_secondary_token"
                    ],
                    "response_frames": decision[
                        "selected_response_frames"
                    ],
                })
                observation = after
            if (
                agent.s.node(episode)["attrs"].get(
                    "kinematics_reprobe_complete"
                )
                != 1.0
            ):
                raise RuntimeError(
                    "graph did not close kinematic interaction reprobe"
                )

            inverse_reach = curriculum.get("inverse_reach")
            if (
                isinstance(inverse_reach, dict)
                and inverse_reach.get("enabled", False)
            ):
                direction = tuple(
                    float(value)
                    for value in inverse_reach["body_direction"]
                )
                if len(direction) != 3 or not any(direction):
                    raise ValueError(
                        "inverse_reach.body_direction must be a nonzero "
                        "three-vector"
                    )
                observation = world.reset()
                agent.inner.set_attr(
                    episode,
                    "phase",
                    "kinematic_reach",
                )
                target_mode = str(inverse_reach.get(
                    "target",
                    "nearest_learned_affordance",
                ))
                agent.inner.set_attr(
                    episode,
                    "kinematic_reach_target_mode",
                    target_mode,
                )
                for axis, value in zip(("x", "y", "z"), direction):
                    agent.inner.set_attr(
                        episode,
                        f"kinematic_reach_direction_d{axis}",
                        value,
                    )
                agent.inner.set_attr(
                    episode,
                    "kinematic_reach_initialized",
                    0.0,
                )
                agent.inner.set_attr(
                    episode,
                    "kinematic_reach_primary_initialized",
                    0.0,
                )
                agent.inner.set_attr(
                    episode,
                    "kinematic_reach_secondary_initialized",
                    0.0,
                )
                agent.inner.set_attr(
                    episode,
                    "kinematic_reach_complete",
                    0.0,
                )
                agent.inner.set_attr(episode, "action_ready", 0.0)
                _write_state(
                    agent,
                    episode,
                    observation,
                    state_seq=request_seq * 2 + 1,
                    state_is_receipt=True,
                )
                _tick_agent(agent)
                reach_host_safety_bound = (
                    kinematics_terminal_point_count
                    * len(observation["support_contact_forces"])
                )
                for _ in range(reach_host_safety_bound):
                    reach_attrs = agent.s.node(episode)["attrs"]
                    if reach_attrs.get("kinematic_reach_complete") == 1.0:
                        break
                    request_seq += 1
                    before = observation
                    requested = _request_action(
                        agent,
                        episode,
                        before,
                        request_seq=request_seq,
                        allow_no_action=True,
                    )
                    if requested is None:
                        if (
                            agent.s.node(episode)["attrs"].get(
                                "kinematic_reach_complete"
                            )
                            == 1.0
                        ):
                            break
                        raise RuntimeError(
                            "graph emitted neither an inverse reach action "
                            "nor a completed reach verdict"
                        )
                    token, trial, decision = requested
                    after = _enact_graph_command(world, token, decision)
                    _close_action(
                        agent,
                        episode,
                        trial,
                        before,
                        after,
                        request_seq=request_seq,
                    )
                    reach_after = dict(agent.s.node(episode)["attrs"])
                    kinematic_reach_trace.append({
                        "request_seq": request_seq,
                        "selected_token": token,
                        "selected_secondary_token": decision[
                            "selected_secondary_token"
                        ],
                        "selected_compound": decision.get(
                            "kinematic_reach_selected_compound",
                            0.0,
                        ),
                        "predicted_displacement": [
                            decision.get(
                                f"kinematic_reach_selected_predicted_d{axis}",
                                0.0,
                            )
                            for axis in ("x", "y", "z")
                        ],
                        "measured_achieved_displacement": [
                            reach_after[
                                f"kinematic_reach_achieved_d{axis}"
                            ]
                            for axis in ("x", "y", "z")
                        ],
                        "remaining_error": reach_after[
                            "kinematic_reach_error"
                        ],
                    })
                    observation = after
                reach_attrs = dict(agent.s.node(episode)["attrs"])
                if reach_attrs.get("kinematic_reach_complete") != 1.0:
                    kinematic_reach_result = {
                        "status": "reach_horizon_exhausted",
                        "study_owner": "rust_graph",
                        "target_source": target_mode,
                        "body_direction": list(direction),
                        "attempt_count": reach_attrs[
                            "kinematic_reach_attempt_count"
                        ],
                        "attempt_limit": reach_attrs[
                            "kinematic_reach_attempt_limit"
                        ],
                        "trace": kinematic_reach_trace,
                    }
                else:
                    kinematic_reach_result = {
                        "study_owner": "rust_graph",
                        "target_source": target_mode,
                        "body_direction": list(direction),
                        "point_ordinal": reach_attrs[
                            "kinematic_reach_point_ordinal"
                        ],
                        "target_basis_tokens": [
                            reach_attrs["kinematic_reach_basis_token_a"],
                            reach_attrs["kinematic_reach_basis_token_b"],
                        ],
                        "target_displacement": [
                            reach_attrs[f"kinematic_reach_target_d{axis}"]
                            for axis in ("x", "y", "z")
                        ],
                        "achieved_displacement": [
                            reach_attrs[f"kinematic_reach_achieved_d{axis}"]
                            for axis in ("x", "y", "z")
                        ],
                        "initial_error": reach_attrs[
                            "kinematic_reach_initial_error"
                        ],
                        "final_error": reach_attrs[
                            "kinematic_reach_error"
                        ],
                        "success_threshold": reach_attrs[
                            "kinematic_reach_success_threshold"
                        ],
                        "success": reach_attrs["kinematic_reach_success"],
                        "attempt_count": reach_attrs[
                            "kinematic_reach_attempt_count"
                        ],
                        "attempt_limit": reach_attrs[
                            "kinematic_reach_attempt_limit"
                        ],
                        "trace": kinematic_reach_trace,
                    }

        models = _model_rows(agent, episode)
        phase_models_before_walk = _phase_model_rows(agent, episode)
        observation = world.reset()
        agent.inner.set_attr(
            episode,
            "motor_fixture_reset_seq",
            float(agent.s.node(episode)["attrs"].get(
                "motor_fixture_reset_seq",
                0.0,
            )) + 1.0,
        )
        pre_locomotion = observation
        if development_context is not None:
            agent.inner.set_attr(
                development_context,
                "development_learning_active",
                int(not locomotion.get("developmental_deployment_mode", 0)),
            )
        agent.inner.set_attr(episode, "phase", "locomotion")
        _write_state(
            agent,
            episode,
            observation,
            state_seq=request_seq * 2,
            state_is_receipt=True,
        )
        _tick_agent(agent)
        maximum_adaptation_actions = (
            int(
                len(phase_models_before_walk)
                * float(
                    agent.s.node(policy)["attrs"][
                        "support_phase_prior_strength"
                    ]
                )
            )
            if mode == "directed_walk" and not developmental_curriculum
            else 0
        )
        warmup_actions = 0
        warmup_first_fall_action = None
        warmup_learning_events = 0
        warmup_last_learning_action = None
        warmup_height_floor = (
            float(evaluation["minimum_upright_height_fraction"])
            * standing_reference_z
        )
        for warmup_action in range(maximum_adaptation_actions):
            warmup_actions += 1
            _service_requested_system_two(agent)
            request_seq += 1
            before = observation
            token, trial, decision = _request_action(
                agent,
                episode,
                before,
                request_seq=request_seq,
            )
            after = _enact_graph_command(world, token, decision)
            if observer is not None:
                observer(world, {
                    "phase": "gait_adaptation",
                    "action": warmup_action,
                    "observation": after,
                    "event": None,
                    "decision_kind": decision["decision_kind"],
                })
            trial_after = _close_action(
                agent,
                episode,
                trial,
                before,
                after,
                request_seq=request_seq,
            )
            if trial_after.get("status") == "adapted_online":
                warmup_learning_events += 1
                warmup_last_learning_action = warmup_action
            if (
                warmup_first_fall_action is None
                and float(after["base_position"][2]) < warmup_height_floor
            ):
                warmup_first_fall_action = warmup_action
            observation = after
            if (
                agent.s.node(episode)["attrs"].get(
                    "phase_adaptation_complete"
                )
                == 1.0
            ):
                break

        phase_models_after_adaptation = _phase_model_rows(agent, episode)
        phase_adaptation_complete = agent.s.node(episode)["attrs"].get(
            "phase_adaptation_complete"
        )
        observation = world.reset()
        agent.inner.set_attr(
            episode,
            "motor_fixture_reset_seq",
            float(agent.s.node(episode)["attrs"].get(
                "motor_fixture_reset_seq",
                0.0,
            )) + 1.0,
        )
        agent.inner.set_attr(episode, "locomotor_prior_reset_seq", 1.0)
        agent.inner.set_attr(episode, "online_phase_learning", 1.0)
        agent.inner.set_attr(episode, "evaluation_active", 1.0)
        agent.inner.set_attr(episode, "recovery_mode", 0.0)
        for key, value in (
            ("locomotion_measurements_initialized", 0.0),
            ("locomotion_measured_state_seq", -1.0),
            ("locomotion_start_x", 0.0),
            ("locomotion_start_y", 0.0),
            ("directed_progress", 0.0),
            ("locomotion_residual_m", target_directed_progress_m),
            ("locomotion_drive_active", 1.0),
            ("maximum_directed_progress", 0.0),
            ("lateral_offset", 0.0),
            ("maximum_lateral_excursion", 0.0),
            ("locomotor_path_length", 0.0),
            ("locomotor_forward_reversal_count", 0.0),
            ("locomotor_cycle_count", 0.0),
            ("last_directed_step", 0.0),
            ("walking_minimum_height", standing_reference_z),
            ("walking_peak_tilt", 0.0),
            ("walking_peak_abs_vx", 0.0),
            ("walking_peak_abs_vy", 0.0),
            ("walking_peak_prediction_error", 0.0),
            ("latest_gait_prediction_error", 0.0),
            ("support_alternations", 0.0),
            ("aerial_samples", 0.0),
            ("double_support_samples", 0.0),
            ("support_topology_samples", 0.0),
            ("aerial_active", 0.0),
            ("last_unilateral_support", 0.0),
            ("current_support_phase", 0.0),
            ("curriculum_last_request_seq", float(request_seq)),
            ("curriculum_last_challenge_cycle_count", 0.0),
            ("curriculum_pending_baseline_directed_progress", 0.0),
            ("curriculum_pending_baseline_cycle_count", 0.0),
            ("regime_monitor_enabled", 1.0),
            ("regime_clock_seq", float(request_seq)),
            ("regime_evidence_seq", float(request_seq)),
            ("regime_ordinal", 0.0),
            ("regime_escalation_requested", 0.0),
            ("regime_escalation_count", 0.0),
            ("regime_last_escalation_seq", float(request_seq)),
            ("regime_applied_ordinal", 0.0),
            ("regime_last_cycle_count", 0.0),
            ("regime_best_progress", 0.0),
            ("render_first_suspended", 0.0),
            ("async_trust_epoch", float(request_seq)),
        ):
            agent.inner.set_attr(episode, key, value)
        if control_regime is not None:
            for key, value in (
                ("regime_monitor_enabled", 1.0),
                ("regime_clock_seq", float(request_seq)),
                ("regime_evidence_seq", float(request_seq)),
                ("regime_ordinal", 0.0),
                ("regime_escalation_requested", 0.0),
                ("regime_escalation_count", 0.0),
                ("regime_last_escalation_seq", float(request_seq)),
                ("regime_last_cycle_count", 0.0),
                ("regime_best_progress", 0.0),
            ):
                agent.inner.set_attr(control_regime, key, value)
        agent.inner.set_attr(
            episode,
            "last_compound_decision_count",
            agent.s.node(episode)["attrs"]["decision_count"],
        )
        _write_state(
            agent,
            episode,
            observation,
            state_seq=request_seq * 2 + 1,
            state_is_receipt=True,
        )
        _tick_agent(agent)
        height_floor = (
            float(evaluation["minimum_upright_height_fraction"])
            * standing_reference_z
        )
        heading_x = float(locomotion["heading_x"])
        start_x = float(observation["base_position"][0])
        start_y = float(observation["base_position"][1])
        minimum_height = float(observation["base_position"][2])
        peak_tilt = _body_axis_tilt(observation)
        maximum_lateral_excursion = 0.0
        first_fall_action = None
        last_unilateral_support = 0
        support_alternations = 0
        support_patterns: Counter[str] = Counter()
        previous_support_active = [
            float(row["normal_force"]) > 0.0
            for row in observation["support_contact_forces"]
        ]
        last_touchdown_x = [
            float(row["world_position"][0])
            for row in observation["support_contact_forces"]
        ]
        touchdown_advances = []
        trace = []
        cognitive_authority_settlement_cycles = 0
        # Attribute the situated curriculum itself, excluding boot and
        # calibration. The native counters are observational and do not alter
        # rule scheduling or graph state.
        agent.s._inner.reset_rule_costs()
        completed_attempt_progress = 0.0
        body_reset_records = []
        perturbation = locomotion.get("perturbation")
        perturbation_action = (
            int(perturbation["onset_action"])
            if perturbation is not None and "onset_action" in perturbation
            else round(
                float(perturbation["onset_fraction"])
                * int(locomotion["actions"])
            )
            if perturbation is not None
            else None
        )
        locomotion_action_count = int(locomotion["actions"])
        if (
            perturbation_action is not None
            and "post_perturbation_recovery_survey_cycles" in locomotion
        ):
            locomotion_action_count = max(
                locomotion_action_count,
                perturbation_action
                + round(
                    float(locomotion[
                        "post_perturbation_recovery_survey_cycles"
                    ])
                    * len(non_tonic_options)
                ),
            )
        resolved_perturbation_force = None
        for action in range(locomotion_action_count):
            # Mechanical enactment boundary: a graph check-in may withdraw
            # authority. Settle the graph-authored check/replan path without
            # emitting a body command. One bounded cognition cycle is not
            # assumed to equal one completed authority decision: continue
            # only while its semantic state changes, so neither a host retry
            # count nor an infinite epoch-only spin can choose the outcome.
            if not _cognitive_continuation_authorised(
                agent, episode, development_context
            ):
                authorised, settlement_cycles = (
                    _settle_cognitive_continuation_authority(
                        agent, episode, development_context
                    )
                )
                cognitive_authority_settlement_cycles += settlement_cycles
                if not authorised:
                    break
            body_reset_before_action = False
            reset_source = episode
            if (
                development_context is not None
                and agent.s.node(development_context)["attrs"].get(
                    "reset_requested"
                ) == 1
            ):
                reset_source = development_context
            if (
                agent.s.node(reset_source)["attrs"].get("reset_requested")
                == 1.0
            ):
                selected_reset_fixture = None
                selected_reset_scenario = None
                enacted_development_reset_request = None
                if reset_source == development_context:
                    active_reset_requests = agent.inner.neighbours(
                        development_context,
                        "has_active_embodied_reset_request",
                    )
                    if len(active_reset_requests) != 1:
                        raise RuntimeError(
                            "graph reset authority requires one active request"
                        )
                    enacted_development_reset_request = active_reset_requests[0]
                    reset_request_attrs = agent.s.node(
                        enacted_development_reset_request
                    )["attrs"]
                    if reset_request_attrs.get(
                        "reinstantiation_spec_ready", 0
                    ) == 1:
                        selected_reset_fixture = tuple(int(
                            reset_request_attrs[
                                f"fixture_quarter_turn_{axis}"
                            ]
                        ) for axis in ("x", "y", "z"))
                        selected_reset_scenario = str(
                            reset_request_attrs["scenario_name"]
                        )
                completed_attempt_progress += heading_x * (
                    float(observation["base_position"][0]) - start_x
                )
                body_reset_records.append({
                    "before_action": action,
                    "request_seq": request_seq,
                    "completed_attempt_progress": (
                        completed_attempt_progress
                    ),
                    "get_up_attempt_count": agent.s.node(episode)[
                        "attrs"
                    ].get("get_up_attempt_count", 0.0),
                    "selected_reset_scenario": selected_reset_scenario,
                    "selected_reset_fixture": selected_reset_fixture,
                })
                observation = (
                    world.reset(
                        initial_base_quarter_turns=selected_reset_fixture
                    )
                    if selected_reset_fixture is not None
                    else world.reset()
                )
                start_x = float(observation["base_position"][0])
                start_y = float(observation["base_position"][1])
                previous_support_active = [
                    float(row["normal_force"]) > 0.0
                    for row in observation["support_contact_forces"]
                ]
                last_touchdown_x = [
                    float(row["world_position"][0])
                    for row in observation["support_contact_forces"]
                ]
                last_unilateral_support = 0
                # Reset receipts have their own event sequence. A reset can
                # expose a new basin that immediately justifies another reset
                # before any motor action is emitted; reusing request_seq then
                # gives both physical events the same identity and makes the
                # second acknowledgement's strict monotonicity guard false.
                body_reset_seq = 1 + max(
                    int(agent.s.node(episode)["attrs"].get(
                        "body_reset_seq", 0
                    )),
                    int(
                        agent.s.node(development_context)["attrs"].get(
                            "body_reset_seq", 0
                        )
                        if development_context is not None else 0
                    ),
                )
                agent.inner.set_attr(
                    episode,
                    "body_reset_seq",
                    float(body_reset_seq),
                )
                if development_context is not None:
                    reset_cost_units = int(
                        agent.s.node(development_context)["attrs"].get(
                            "embodiment_reset_cost_units", 0
                        )
                    )
                    agent.inner.set_attr(
                        development_context,
                        "last_body_reset_cost_units",
                        reset_cost_units,
                    )
                    agent.inner.set_attr(
                        development_context,
                        "body_reset_seq",
                        body_reset_seq,
                    )
                _write_state(
                    agent,
                    episode,
                    observation,
                    state_seq=request_seq * 2 + 0.5,
                    state_is_receipt=True,
                )
                _tick_agent(agent)
                development_reset_acknowledged = (
                    enacted_development_reset_request is not None
                    and agent.s.node(enacted_development_reset_request)[
                        "attrs"
                    ].get("status") == "enacted"
                    and enacted_development_reset_request not in (
                        agent.inner.neighbours(
                            development_context,
                            "has_active_embodied_reset_request",
                        )
                    )
                )
                motor_reset_acknowledged = (
                    enacted_development_reset_request is None
                    and agent.s.node(reset_source)["attrs"].get(
                        "reset_requested"
                    ) == 0
                )
                if not (
                    development_reset_acknowledged
                    or motor_reset_acknowledged
                ):
                    reset_attrs = agent.s.node(reset_source)["attrs"]
                    raise RuntimeError(
                        "graph did not acknowledge requested body reset: "
                        f"source={'development' if reset_source == development_context else 'motor'} "
                        f"body_reset_seq={reset_attrs.get('body_reset_seq')} "
                        "processed_seq="
                        f"{reset_attrs.get('embodied_reset_processed_seq', reset_attrs.get('body_reset_processed_seq'))} "
                        f"active_request_count={len(agent.inner.neighbours(reset_source, 'has_active_embodied_reset_request'))}"
                    )
                body_reset_before_action = True
            _service_requested_system_two(agent)
            request_seq += 1
            before = observation
            # Stamp the state that governs this decision, not the state after
            # its receipt. Bounds can become ready while `_close_action`
            # processes the receipt; calling that action gated would be one
            # action too early and makes post-gate width unverifiable.
            manifold_bounds_ready_before_action = float(
                agent.s.node(episode)["attrs"].get(
                    "manifold_bounds_ready", 0.0
                )
            )
            if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
                print(
                    f"humanoid_action_phase action={action} request_start",
                    flush=True,
                )
            token, trial, decision = _request_action(
                agent,
                episode,
                before,
                request_seq=request_seq,
            )
            if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
                print(
                    f"humanoid_action_phase action={action} request_done",
                    flush=True,
                )
            active_capability_before_action = {}
            development_evidence_window_before_action = 0
            if development_context is not None:
                active_capabilities = agent.inner.neighbours(
                    development_context,
                    "has_active_embodied_developmental_capability",
                )
                if active_capabilities:
                    active_capability_before_action = dict(agent.s.node(
                        active_capabilities[0]
                    )["attrs"])
                development_evidence_window_before_action = int(
                    agent.s.node(development_context)["attrs"].get(
                        "development_evidence_window", 0
                    )
                )
            committed_programs = [
                *agent.inner.neighbours(
                    trial, "enacts_humanoid_motor_program"
                ),
                *agent.inner.neighbours(
                    trial, "synthesized_humanoid_motor_program"
                ),
            ]
            support_counterfactual_audit = next((
                dict(agent.s.node(program)["attrs"])
                for program in committed_programs
                if int(agent.s.node(program)["attrs"].get(
                    "support_counterfactual_audit_seq", 0
                )) > 0
            ), {})
            committed_program_caregiver_buffered = int(any(
                int(agent.s.node(program)["attrs"].get(
                    "caregiver_buffered_release", 0
                )) == 1
                for program in committed_programs
            ))
            curriculum_event = (
                enact_graph_force_request(
                    agent,
                    episode,
                    world,
                    before,
                    prefix="curriculum",
                )
                if curriculum is not None
                and not developmental_curriculum
                and mode == "directed_walk"
                else None
            )
            perturbation_applied = action == perturbation_action
            if perturbation_applied:
                body_weight = (
                    float(before["body_mass"])
                    * configuration.gravity_acceleration
                )
                resolved_perturbation_force = [
                    float(multiple) * body_weight
                    for multiple in perturbation[
                        "world_frame_force_body_weights"
                    ]
                ]
                world.apply_force_pulse(
                    resolved_perturbation_force,
                    frames=int(perturbation["frames"]),
                )
            after = _enact_graph_command(world, token, decision)
            if observer is not None:
                observer(world, {
                    "phase": "walking",
                    "action": action,
                    "observation": after,
                    "event": (
                        "perturbation"
                        if perturbation_applied
                        else (
                            "body_reset"
                            if body_reset_before_action
                            else None
                        )
                    ),
                    "decision_kind": decision["decision_kind"],
                })
            # The control graph can open a new energetic accounting window
            # while processing this receipt.  Preserve the window stamped on
            # the receipt, rather than reading the possibly advanced episode
            # sequence after `_close_action` ticks the graph.
            receipt_energetic_window_seq = float(
                agent.s.node(episode)["attrs"].get(
                    "locomotor_prior_reset_seq",
                    0.0,
                )
            )
            if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
                print(
                    f"humanoid_action_phase action={action} receipt_start",
                    flush=True,
                )
            trial_after = _close_action(
                agent,
                episode,
                trial,
                before,
                after,
                request_seq=request_seq,
                external_event_frames=(
                    (
                        int(curriculum_event["frames"])
                        if curriculum_event is not None
                        else 0
                    )
                    + (
                        int(perturbation["frames"])
                        if perturbation_applied
                        else 0
                    )
                ),
            )
            if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
                print(
                    f"humanoid_action_phase action={action} receipt_done",
                    flush=True,
                )
            height = float(after["base_position"][2])
            tilt = _body_axis_tilt(after)
            minimum_height = min(minimum_height, height)
            peak_tilt = max(peak_tilt, tilt)
            maximum_lateral_excursion = max(
                maximum_lateral_excursion,
                abs(float(after["base_position"][1]) - start_y),
            )
            if first_fall_action is None and height < height_floor:
                first_fall_action = action
            support_code = _support_code(after)
            active_support = tuple(
                float(row["normal_force"]) > 0.0
                for row in after["support_contact_forces"]
            )
            support_pattern = {
                (False, False): "aerial",
                (True, False): "support_0",
                (False, True): "support_1",
                (True, True): "double_support",
            }[active_support]
            support_patterns[support_pattern] += 1
            for support_ordinal, is_active in enumerate(active_support):
                if is_active and not previous_support_active[support_ordinal]:
                    support_x = float(
                        after["support_contact_forces"][
                            support_ordinal
                        ]["world_position"][0]
                    )
                    touchdown_advances.append(
                        heading_x
                        * (support_x - last_touchdown_x[support_ordinal])
                    )
                    last_touchdown_x[support_ordinal] = support_x
            previous_support_active = list(active_support)
            if (
                support_code > 0
                and last_unilateral_support > 0
                and support_code != last_unilateral_support
            ):
                support_alternations += 1
            if support_code > 0:
                last_unilateral_support = support_code
            graph_state_after = agent.s.node(episode)["attrs"]
            before_up = _gravity_relative_up_axis(tuple(
                float(value) for value in before["base_orientation_xyzw"]
            ))
            after_up = _gravity_relative_up_axis(tuple(
                float(value) for value in after["base_orientation_xyzw"]
            ))
            before_angular = before["base_angular_velocity"]
            after_angular = after["base_angular_velocity"]
            before_linear = before["base_linear_velocity"]
            after_linear = after["base_linear_velocity"]
            observed_projection_delta = [
                float(after_up[0]) - float(before_up[0]),
                float(after_up[1]) - float(before_up[1]),
                float(after_angular[0]) - float(before_angular[0]),
                float(after_angular[1]) - float(before_angular[1]),
                float(after_linear[0]) - float(before_linear[0]),
                float(after_linear[1]) - float(before_linear[1]),
                float(after_linear[2]) - float(before_linear[2]),
            ]
            unsupported_projection_bounds = [
                float(support_counterfactual_audit.get(
                    f"unsupported_projection_bound_{index}", 0.0
                ))
                for index in range(7)
            ]
            supported_projection_bounds = [
                float(support_counterfactual_audit.get(
                    f"supported_projection_bound_{index}", 0.0
                ))
                for index in range(7)
            ]
            observed_projection_bounds = (
                supported_projection_bounds
                if int(after.get(
                    "caregiver_protective_support_applied", 0
                )) == 1
                else unsupported_projection_bounds
            )
            trace.append({
                "action": action,
                "active_residual_regime_ordinal": float(
                    graph_state_after.get(
                        "active_residual_regime_ordinal", 0.0
                    )
                ),
                "active_gait_attractor_ordinal": float(
                    graph_state_after.get(
                        "active_gait_attractor_ordinal", 0.0
                    )
                ),
                "selected_token": token,
                "development_directed_units": int(trial_after.get(
                    "_development_directed_units", 0
                )),
                "development_translation_units": int(trial_after.get(
                    "_development_translation_units", 0
                )),
                "development_elevation_units": int(trial_after.get(
                    "_development_elevation_units", 0
                )),
                "development_vertical_velocity_progress_units": int(
                    trial_after.get(
                        "_development_vertical_velocity_progress_units", 0
                    )
                ),
                "development_directed_consistency": int(trial_after.get(
                    "_development_directed_consistency", 0
                )),
                "selected_secondary_token": decision[
                    "selected_secondary_token"
                ],
                "orientation_class_before": (
                    _gravity_relative_orientation_class(
                        _gravity_relative_up_axis(tuple(
                            float(value) for value in
                            before["base_orientation_xyzw"]
                        ))
                    )
                ),
                "orientation_class_after": (
                    _gravity_relative_orientation_class(
                        _gravity_relative_up_axis(tuple(
                            float(value) for value in
                            after["base_orientation_xyzw"]
                        ))
                    )
                ),
                "motor_tokens": list(after["last_actuator_tokens"]),
                "motor_bundle_width": len(after["last_actuator_tokens"]),
                "takeoff_compound_candidate_count": max((
                    int(agent.s.node(program)["attrs"].get(
                        "takeoff_compound_candidate_count", 0
                    ))
                    for program in committed_programs
                ), default=0),
                "takeoff_compound_allow_expansion": max((
                    int(agent.s.node(program)["attrs"].get(
                        "takeoff_compound_allow_expansion", 0
                    ))
                    for program in committed_programs
                ), default=0),
                "takeoff_compound_target_order": max((
                    int(agent.s.node(program)["attrs"].get(
                        "takeoff_compound_target_order", 0
                    ))
                    for program in committed_programs
                ), default=0),
                "compound_curiosity_selection_count": sum(
                    int(agent.s.node(program)["attrs"].get(
                        "compound_curiosity_selection_count", 0
                    ))
                    for program in committed_programs
                ),
                "compound_curiosity_pre_expansion_candidate_count_maximum": max((
                    int(agent.s.node(program)["attrs"].get(
                        "compound_curiosity_pre_expansion_candidate_count", 0
                    ))
                    for program in committed_programs
                ), default=0),
                "compound_curiosity_terminal_candidate_count_maximum": max((
                    int(agent.s.node(program)["attrs"].get(
                        "compound_curiosity_terminal_candidate_count", 0
                    ))
                    for program in committed_programs
                ), default=0),
                "compound_curiosity_terminal_target_order_maximum": max((
                    int(agent.s.node(program)["attrs"].get(
                        "compound_curiosity_terminal_target_order", 0
                    ))
                    for program in committed_programs
                ), default=0),
                "takeoff_compound_selection_kind": next((
                    str(agent.s.node(program)["attrs"].get(
                        "compound_selection_kind", "none"
                    ))
                    for program in committed_programs
                    if agent.s.node(program)["attrs"].get(
                        "compound_selection_kind"
                    ) is not None
                ), "none"),
                "manifold_bounds_ready": (
                    manifold_bounds_ready_before_action
                ),
                "ideal_effort_ratio": float(graph_state_after.get(
                    "future_manifold_ideal_effort", 0.0
                )),
                "ideal_effort_evidence_count": int(graph_state_after.get(
                    "future_manifold_ideal_effort_evidence_count", 0
                )),
                "effort_scale_joules": float(graph_state_after.get(
                    "future_manifold_effort_scale_joules", 0.0
                )),
                "manifold_effort_audit_count": int(graph_state_after.get(
                    "manifold_effort_audit_count", 0
                )),
                "manifold_effort_supported_audit_count": int(
                    graph_state_after.get(
                        "manifold_effort_supported_audit_count", 0
                    )
                ),
                "manifold_effort_blocked_audit_count": int(
                    graph_state_after.get(
                        "manifold_effort_blocked_audit_count", 0
                    )
                ),
                "manifold_effort_compression_audit_count": int(
                    graph_state_after.get(
                        "manifold_effort_compression_audit_count", 0
                    )
                ),
                "motor_weight_a": float(
                    decision.get("selected_motor_weight_a", 1.0)
                ),
                "motor_weight_b": float(
                    decision.get("selected_motor_weight_b", 1.0)
                ),
                **{
                    key: float(decision.get(key, 0.0))
                    for key in (
                        "motor_effort_ratio",
                        "takeoff_effort_supported",
                        "takeoff_effort_required_ratio",
                        "takeoff_effort_residual_ratio",
                        "takeoff_effort_authorized",
                    )
                },
                "motor_input_energy_joules": float(
                    after["supplied_energy_joules"]
                ),
                "energetic_window_seq": receipt_energetic_window_seq,
                "response_frames": decision["selected_response_frames"],
                "decision_kind": decision["decision_kind"],
                "collapse_kind": decision.get(
                    "selected_collapse_kind",
                    trial_after.get("collapse_kind", "unclassified"),
                ),
                "open_residual_count": trial_after.get(
                    "open_residual_count",
                    1.0,
                ),
                # Preserve the actual exafferent intervention on every
                # developmental action.  A request is only graph intent; the
                # world receipt is the evidence that support was enacted.
                "caregiver_protective_support_applied": int(after.get(
                    "caregiver_protective_support_applied", 0
                )),
                "caregiver_protective_support_requested": int(decision.get(
                    "caregiver_protective_support_requested", 0
                )),
                "caregiver_support_scale": float(after.get(
                    "caregiver_support_scale", 0.0
                )),
                "caregiver_manifold_decisive_tick": float(decision.get(
                    "caregiver_manifold_decisive_tick", 0.0
                )),
                "caregiver_manifold_residual": [
                    float(decision.get(
                        f"caregiver_manifold_residual_{index}", 0.0
                    ))
                    for index in range(7)
                ],
                "support_counterfactual_audit_seq": int(
                    support_counterfactual_audit.get(
                        "support_counterfactual_audit_seq", 0
                    )
                ),
                "unsupported_projection": {
                    field: float(support_counterfactual_audit.get(
                        f"unsupported_projection_{field}", 0.0
                    ))
                    for field in (
                        "support", "resolved", "loss", "information_loss"
                    )
                },
                "supported_projection": {
                    field: float(support_counterfactual_audit.get(
                        f"supported_projection_{field}", 0.0
                    ))
                    for field in (
                        "support", "resolved", "loss", "information_loss",
                        "horizon", "earliest_decisive_tick",
                        "minimum_exafferent_scale",
                    )
                },
                "supported_projection_residual": [
                    float(support_counterfactual_audit.get(
                        f"supported_projection_residual_{index}", 0.0
                    ))
                    for index in range(7)
                ],
                "unsupported_projection_bounds": unsupported_projection_bounds,
                "supported_projection_bounds": supported_projection_bounds,
                "observed_projection_delta": observed_projection_delta,
                "observed_projection_escape_count": sum(
                    abs(delta) > bound
                    for delta, bound in zip(
                        observed_projection_delta, observed_projection_bounds
                    )
                ),
                "support_counterfactual_recommends_support": int(
                    float(support_counterfactual_audit.get(
                        "unsupported_projection_loss", 0.0
                    )) > 0.0
                    and float(support_counterfactual_audit.get(
                        "supported_projection_loss", 0.0
                    )) == 0.0
                ),
                "caregiver_support_force_world": list(after.get(
                    "caregiver_support_force_world", (0.0, 0.0, 0.0)
                )),
                "caregiver_support_torque_world": list(after.get(
                    "caregiver_support_torque_world", (0.0, 0.0, 0.0)
                )),
                "caregiver_protective_support_available": int(decision.get(
                    "caregiver_protective_support_available", 0
                )),
                "developmental_capability_success_count_before_action": int(
                    active_capability_before_action.get("success_count", 0)
                ),
                "development_evidence_window": (
                    development_evidence_window_before_action
                ),
                "sensorimotor_interrupt_required_before_action": int(
                    decision.get("sensorimotor_interrupt_required", 0)
                ),
                "reset_requested_before_action": int(decision.get(
                    "reset_requested", 0
                )),
                "committed_program_caregiver_buffered": (
                    committed_program_caregiver_buffered
                ),
                "counterfactual_support_release": int(any(
                    int(agent.s.node(program)["attrs"].get(
                        "counterfactual_support_release_seq", 0
                    )) == request_seq
                    for program in committed_programs
                )),
                "caregiver_support_impulse_newton_seconds": float(after.get(
                    "caregiver_support_impulse_newton_seconds", 0.0
                )),
                "motor_reference_kind": after.get("motor_reference_kind"),
                "motor_reference_shape": decision.get(
                    "selected_motor_reference_shape"
                ),
                "motor_configuration_shape_after": after.get(
                    "motor_configuration_shape"
                ),
                "predicted_dvx": decision.get("selected_predicted_dvx", 0.0),
                "predicted_dvy": decision.get("selected_predicted_dvy", 0.0),
                "last_directed_step": graph_state_after.get(
                    "last_directed_step",
                    0.0,
                ),
                "last_locomotor_token": graph_state_after.get(
                    "last_locomotor_token",
                    "",
                ),
                "trial_status": trial_after["status"],
                "motor_memory_recalled": trial_after.get(
                    "motor_memory_recalled",
                    0.0,
                ),
                "motor_sequence_recalled": trial_after.get(
                    "motor_sequence_recalled",
                    0.0,
                ),
                "motor_task_context": trial_after.get(
                    "motor_task_context",
                    "unresolved",
                ),
                "motor_memory_consolidated": trial_after.get(
                    "motor_memory_consolidated",
                    0.0,
                ),
                "motor_memory_structurally_reused": trial_after.get(
                    "motor_memory_structurally_reused",
                    0.0,
                ),
                "body_reset_before_action": body_reset_before_action,
                "perturbation_applied": perturbation_applied,
                "curriculum_event": curriculum_event,
                # Attribute the outcome to the capability that selected the
                # action. Processing this receipt may master that capability
                # and activate the next one, which is useful transition state
                # but must not be allowed to relabel the enacted action.
                "active_developmental_capability": (
                    active_capability_before_action.get("name", "inactive")
                ),
                "active_developmental_capability_after_action": (
                    graph_state_after.get(
                        "active_developmental_capability", "inactive"
                    )
                ),
                "developmental_goal": graph_state_after.get(
                    "developmental_goal", "inactive"
                ),
                "position_after": list(after["base_position"]),
                "linear_velocity_after": list(
                    after["base_linear_velocity"]
                ),
                "tilt_after": tilt,
                "gait_prediction_error": graph_state_after[
                    "latest_gait_prediction_error"
                ],
                "gait_surprise_streak": graph_state_after[
                    "gait_surprise_streak"
                ],
                "recovery_mode_after": graph_state_after[
                    "recovery_mode"
                ],
                "recovery_basin_count": graph_state_after.get(
                    "recovery_basin_count", 0.0
                ),
                "recovery_basin_transition_count": graph_state_after.get(
                    "recovery_basin_transition_count", 0.0
                ),
                "recovery_composition_count": graph_state_after.get(
                    "recovery_composition_count", 0.0
                ),
                "recovery_warm_start_count": graph_state_after.get(
                    "recovery_warm_start_count", 0.0
                ),
                "recovery_path_recall_count": graph_state_after.get(
                    "recovery_path_recall_count", 0.0
                ),
                "recovery_path_hint_count": graph_state_after.get(
                    "recovery_path_hint_count", 0.0
                ),
                "recovery_reanchor_count": graph_state_after.get(
                    "recovery_reanchor_count", 0.0
                ),
                "recovery_program_count": graph_state_after.get(
                    "recovery_program_count", 0.0
                ),
                "recovery_program_repeat_count": graph_state_after.get(
                    "recovery_program_repeat_count", 0.0
                ),
                "upright_after": graph_state_after["upright"],
                "whole_body_vertical_momentum_after": graph_state_after[
                    "state_linear_momentum_z"
                ],
                "whole_body_centre_of_mass_height_after": graph_state_after[
                    "state_com_z"
                ],
                "self_takeoff_drive_active_after": graph_state_after[
                    "self_takeoff_drive_active"
                ],
                "self_takeoff_compression_scale_after": graph_state_after[
                    "self_takeoff_compression_scale"
                ],
                "locomotor_path_length": graph_state_after[
                    "locomotor_path_length"
                ],
                "forward_reversal_count": graph_state_after[
                    "locomotor_forward_reversal_count"
                ],
                "locomotor_cycle_count": graph_state_after[
                    "locomotor_cycle_count"
                ],
                "support_code": support_code,
                "support_pattern": support_pattern,
                "support_forces": [
                    float(row["normal_force"])
                    for row in after["support_contact_forces"]
                ],
                "support_positions": [
                    list(row["world_position"])
                    for row in after["support_contact_forces"]
                ],
            })
            if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
                development_progress = (
                    agent.s.node(development_context)["attrs"]
                    if development_context is not None else {}
                )
                print(
                    "humanoid_action_progress "
                    f"action={action} "
                    "capability="
                    f"{graph_state_after.get('active_developmental_capability')} "
                    "resets="
                    f"{development_progress.get('embodiment_reset_iteration_count', 0)}",
                    flush=True,
                )
            if observer is not None:
                observer(world, {
                    "phase": "learning_receipt",
                    "action": action,
                    "action_count": locomotion_action_count,
                    "observation": after,
                    "event": None,
                    "decision_kind": decision["decision_kind"],
                    "development": _development_progress_snapshot(
                        agent, episode, development_context
                    ),
                })
            observation = after

        if development_context is not None:
            # Run the general soft-realtime Pareto faculty after the complete
            # receipt set is available. This schedules graph cognition; it
            # does not rank or choose locomotor basins in Python.
            agent.dual_process_tick()
        final = dict(agent.s.node(episode)["attrs"])
        final_energetic_window_seq = float(
            final.get("locomotor_prior_reset_seq", 0.0)
        )
        trace_input_energy_joules = sum(
            float(row["motor_input_energy_joules"])
            for row in trace
        )
        current_window_trace_input_energy_joules = sum(
            float(row["motor_input_energy_joules"])
            for row in trace
            if float(row["energetic_window_seq"])
            == final_energetic_window_seq
        )
        final_policy = dict(agent.s.node(policy)["attrs"])
        curriculum_challenge_rows = (
            sorted(
                (
                    dict(agent.s.node(challenge)["attrs"])
                    for challenge in agent.inner.neighbours(
                        policy,
                        "has_humanoid_coordination_challenge",
                    )
                ),
                key=lambda row: float(row["ordinal"]),
            )
            if curriculum is not None
            else []
        )
        developmental_stage_rows = (
            sorted(
                (
                    {
                        **dict(agent.s.node(capability)["attrs"]),
                        "context_count": len(agent.inner.neighbours(
                            capability,
                            "has_embodied_developmental_context",
                        )),
                        "prerequisite_count": len(agent.inner.neighbours(
                            capability,
                            "requires_embodied_developmental_capability",
                        )),
                        "warm_start_count": len(agent.inner.neighbours(
                            capability,
                            "warm_starts_from_embodied_developmental_capability",
                        )),
                    }
                    for capability in agent.inner.neighbours(
                        development_context,
                        "has_embodied_developmental_capability",
                    )
                ),
                key=lambda row: str(row["name"]),
            )
            if development_context is not None
            else []
        )
        development_final = (
            dict(agent.s.node(development_context)["attrs"])
            if development_context is not None
            else {}
        )
        developmental_diagnostics = _developmental_frontier_diagnostics(
            agent,
            development_context,
        )
        safety_context_nodes = agent.inner.neighbours(
            episode, "has_learning_safety_context"
        )
        safety_context = (
            dict(agent.s.node(safety_context_nodes[0])["attrs"])
            if len(safety_context_nodes) == 1 else {}
        )
        self_learning_plan_summary = None
        if development_context is not None:
            learning_plans = agent.inner.neighbours(
                development_context,
                "has_self_directed_learning_plan",
            )
            if len(learning_plans) != 1:
                raise RuntimeError(
                    "development requires exactly one self-directed learning plan"
                )
            learning_plan = learning_plans[0]
            learning_steps = []
            for step in agent.inner.neighbours(
                learning_plan, "has_learning_plan_step"
            ):
                attrs = dict(agent.s.node(step)["attrs"])
                planned = agent.inner.neighbours(
                    step, "plans_learning_capability"
                )
                if len(planned) != 1:
                    raise RuntimeError(
                        "learning-plan step must bind exactly one capability"
                    )
                attrs["capability_status"] = agent.s.node(
                    planned[0]
                )["attrs"].get("status", "unknown")
                attrs["prerequisite_step_count"] = len(
                    agent.inner.neighbours(
                        step, "requires_learning_plan_step"
                    )
                )
                learning_steps.append(attrs)
            learning_steps.sort(key=lambda row: int(row.get("ordinal", 0)))
            decision_profiles = agent.inner.neighbours(
                learning_plan, "has_learning_decision_profile"
            )
            selected_decisions = agent.inner.neighbours(
                learning_plan, "has_selected_learning_decision"
            )
            latest_decision = (
                max(
                    (
                        dict(agent.s.node(candidate)["attrs"])
                        for candidate in selected_decisions
                    ),
                    key=lambda row: int(row.get("decision_epoch", 0)),
                )
                if selected_decisions else None
            )
            metacognitive_policies = agent.inner.neighbours(
                learning_plan, "has_metacognitive_learning_policy"
            )
            active_metacognitive_policies = agent.inner.neighbours(
                learning_plan, "has_active_metacognitive_learning_policy"
            )
            metacognitive_residuals = agent.inner.neighbours(
                learning_plan, "has_learning_plan_residual"
            )
            metacognitive_revisions = [
                revision
                for revision in agent.inner.neighbours(
                    learning_plan, "has_learning_plan_revision"
                )
                if agent.inner.neighbours(
                    revision, "redirects_to_learning_plan_step"
                )
            ]
            discrimination_requests = [
                request
                for residual in metacognitive_residuals
                for request in agent.inner.neighbours(
                    residual,
                    "has_learning_policy_discrimination_request",
                )
            ]
            discrimination_rows = []
            for request in discrimination_requests:
                row = dict(agent.s.node(request)["attrs"])
                result_rows = []
                for result_node in agent.inner.neighbours(
                    request, "has_discrimination_result"
                ):
                    result_row = dict(agent.s.node(result_node)["attrs"])
                    result_row["selected_candidate_count"] = len(
                        agent.inner.neighbours(
                            result_node, "selected_policy_candidate"
                        )
                    )
                    result_row["executed_classifier_count"] = len(
                        agent.inner.neighbours(
                            result_node, "executed_classifier"
                        )
                    )
                    result_rows.append(result_row)
                row["results"] = result_rows
                discrimination_rows.append(row)
            metacognitive_revision_rows = []
            for revision in metacognitive_revisions:
                row = dict(agent.s.node(revision)["attrs"])
                revised_steps = agent.inner.neighbours(
                    revision, "revises_learning_plan_step"
                )
                redirect_steps = agent.inner.neighbours(
                    revision, "redirects_to_learning_plan_step"
                )
                row["revised_capabilities"] = sorted(
                    str(agent.s.node(node)["attrs"].get("name", ""))
                    for node in revised_steps
                )
                row["redirect_capabilities"] = sorted(
                    str(agent.s.node(node)["attrs"].get("name", ""))
                    for node in redirect_steps
                )
                metacognitive_revision_rows.append(row)
            metacognitive_revision_rows.sort(key=lambda row: (
                int(row.get("order_n", 0)),
                str(row.get("kind", "")),
                tuple(row.get("revised_capabilities", ())),
            ))
            metacognitive_residual_rows = sorted(
                (
                    dict(agent.s.node(residual)["attrs"])
                    for residual in metacognitive_residuals
                ),
                key=lambda row: (
                    int(row.get("order_n", 0)),
                    str(row.get("kind", "")),
                    str(row.get("status", "")),
                ),
            )
            counterexample_hold_rows = []
            for step in agent.inner.neighbours(
                learning_plan, "has_learning_plan_step"
            ):
                for hold in agent.inner.neighbours(
                    step, "has_learning_policy_counterexample_hold"
                ):
                    row = dict(agent.s.node(hold)["attrs"])
                    row["held_capability"] = str(
                        agent.s.node(step)["attrs"].get("name", "")
                    )
                    counterexample_hold_rows.append(row)
            counterexample_hold_rows.sort(key=lambda row: (
                str(row.get("held_capability", "")),
                str(row.get("status", "")),
                int(row.get("order_n", 0)),
            ))
            self_learning_plan_summary = {
                **dict(agent.s.node(learning_plan)["attrs"]),
                "step_count": len(learning_steps),
                "ready_step_count": sum(
                    row.get("status") == "ready" for row in learning_steps
                ),
                "blocked_step_count": sum(
                    row.get("status") == "blocked" for row in learning_steps
                ),
                "active_step_count": sum(
                    row.get("status") == "active" for row in learning_steps
                ),
                "decision_profile_count": len(decision_profiles),
                "selected_decision_count": len(selected_decisions),
                "latest_decision": latest_decision,
                "metacognition": {
                    "policy_count": len(metacognitive_policies),
                    "active_policy_orders": sorted(
                        int(agent.s.node(policy_node)["attrs"].get(
                            "order_n", 0
                        ))
                        for policy_node in active_metacognitive_policies
                    ),
                    "residual_count": len(metacognitive_residuals),
                    "open_residual_count": sum(
                        agent.s.node(residual)["attrs"].get("status") == "open"
                        for residual in metacognitive_residuals
                    ),
                    "revision_count": len(metacognitive_revisions),
                    "enacted_revision_count": sum(
                        agent.s.node(revision)["attrs"].get("status") == "enacted"
                        for revision in metacognitive_revisions
                    ),
                    "discrimination_request_count": len(
                        discrimination_requests
                    ),
                    "held_classifier_program_count": len(
                        agent.inner.neighbours(
                            agent.agent, "holds_threshold_classifier"
                        )
                    ),
                    "discriminations": discrimination_rows,
                    "suspended_step_count": sum(
                        row.get("status") == "meta_suspended"
                        for row in learning_steps
                    ),
                    "revisions": metacognitive_revision_rows,
                    "residuals": metacognitive_residual_rows,
                    "counterexample_holds": counterexample_hold_rows,
                },
                "steps": learning_steps,
            }
        somatomotor_wave_fields = agent.inner.neighbours(
            episode, "has_somatomotor_wave_field"
        )
        somatomotor_wave_summary = {}
        if somatomotor_wave_fields:
            if len(somatomotor_wave_fields) != 1:
                raise RuntimeError("humanoid episode has multiple somatomotor fields")
            wave_field = somatomotor_wave_fields[0]
            wave_cells = agent.inner.neighbours(
                wave_field, "has_somatomotor_wave_cell"
            )
            wave_programs = agent.inner.neighbours(
                wave_field, "has_somatomotor_wave_program"
            )
            archived_wave_programs = agent.inner.neighbours(
                wave_field, "archives_somatomotor_wave_program"
            )
            all_wave_programs = wave_programs + archived_wave_programs
            wave_couplings = {
                coupling
                for cell in wave_cells
                for coupling in agent.inner.neighbours(
                    cell, "has_somatomotor_wave_coupling"
                )
            }
            somatomotor_wave_summary = {
                **dict(agent.s.node(wave_field)["attrs"]),
                "enabled": int(
                    agent.s.node(episode)["attrs"].get(
                        "somatomotor_wave_enabled", 0
                    )
                ),
                "cell_count": len(wave_cells),
                "coupling_count": len(wave_couplings),
                "program_count": len(all_wave_programs),
                "active_program_count": len(wave_programs),
                "archived_program_count": len(archived_wave_programs),
                "compound_program_count": sum(
                    int(agent.s.node(program)["attrs"].get(
                        "wavefront_width", 0
                    )) > 1
                    for program in all_wave_programs
                ),
                "maximum_wavefront_width": max(
                    (
                        int(agent.s.node(program)["attrs"].get(
                            "wavefront_width", 0
                        ))
                        for program in wave_programs
                    ),
                    default=0,
                ),
                "productive_cell_count": sum(
                    int(agent.s.node(cell)["attrs"].get(
                        "productive_consequence_count", 0
                    )) > 0
                    for cell in wave_cells
                ),
                "strengthened_coupling_count": sum(
                    int(agent.s.node(coupling)["attrs"].get("strength", 0)) > 1
                    for coupling in wave_couplings
                ),
                "fractionated_coupling_count": sum(
                    int(agent.s.node(coupling)["attrs"].get("strength", 0)) == 0
                    for coupling in wave_couplings
                ),
                "productive_coupling_receipt_count": sum(
                    int(agent.s.node(coupling)["attrs"].get(
                        "productive_count", 0
                    ))
                    for coupling in wave_couplings
                ),
                "unproductive_coupling_receipt_count": sum(
                    int(agent.s.node(coupling)["attrs"].get(
                        "unproductive_count", 0
                    ))
                    for coupling in wave_couplings
                ),
                "maximum_coupling_strength": max(
                    (
                        int(agent.s.node(coupling)["attrs"].get(
                            "strength", 0
                        ))
                        for coupling in wave_couplings
                    ),
                    default=0,
                ),
                "warm_prior_pending_count": sum(
                    int(agent.s.node(coupling)["attrs"].get(
                        "warm_prior_rank", 0
                    )) > 0
                    for coupling in wave_couplings
                ),
                "warm_prior_reverified_count": sum(
                    int(agent.s.node(coupling)["attrs"].get(
                        "warm_prior_reverified", 0
                    )) > 0
                    for coupling in wave_couplings
                ),
            }
        active_developmental_capabilities = (
            agent.inner.neighbours(
                development_context,
                "has_active_embodied_developmental_capability",
            )
            if development_context is not None
            else []
        )
        active_developmental_capability_name = (
            str(agent.s.node(active_developmental_capabilities[0])["attrs"].get(
                "name", "inactive"
            ))
            if len(active_developmental_capabilities) == 1
            else "inactive"
        )
        # Trajectories are durable experimental evidence.  Reporting only
        # those owned by the capability that happens to remain active at the
        # final tick made a suspension/mastery erase their observability and
        # previously reported a false zero after order-N work had run.
        situated_developmental_capabilities = (
            agent.inner.neighbours(
                development_context,
                "has_embodied_developmental_capability",
            )
            if development_context is not None
            else []
        )
        deployment_program_owners = agent.inner.neighbours(
            episode, "has_embodied_deployment_program_owner"
        )
        program_trajectory_owners = list({
            *situated_developmental_capabilities,
            *deployment_program_owners,
        })
        program_trajectory_nodes = list({
            trajectory
            for capability in program_trajectory_owners
            for trajectory in agent.inner.neighbours(
                capability, "has_embodied_program_trajectory"
            )
        })
        active_program_trajectory_nodes = [
            trajectory
            for trajectory in program_trajectory_nodes
            if int(agent.s.node(trajectory)["attrs"].get(
                "selection_enabled", 1
            )) == 1
        ]
        program_transition_nodes = list({
            transition
            for capability in program_trajectory_owners
            for transition in agent.inner.neighbours(
                capability, "has_embodied_program_transition"
            )
        })
        program_path_nodes = list({
            path
            for trajectory in program_trajectory_nodes
            for path in agent.inner.neighbours(
                trajectory, "has_pareto_candidate"
            )
        })
        active_capability_transition_nodes = list({
            transition
            for capability in active_developmental_capabilities
            for transition in agent.inner.neighbours(
                capability, "has_embodied_program_transition"
            )
        })
        active_capability_trajectory_nodes = list({
            trajectory
            for capability in active_developmental_capabilities
            for trajectory in agent.inner.neighbours(
                capability, "has_embodied_program_trajectory"
            )
        })
        active_capability_path_nodes = list({
            path
            for trajectory in active_capability_trajectory_nodes
            for path in agent.inner.neighbours(
                trajectory, "has_pareto_candidate"
            )
        })
        selected_program_path_nodes = list({
            path
            for capability in program_trajectory_owners
            for path in agent.inner.neighbours(
                capability, "has_selected_embodied_program_path"
            )
        })
        capability_current_transition_sources = list({
            transition
            for capability in program_trajectory_owners
            for transition in agent.inner.neighbours(
                capability,
                "has_current_embodied_program_transition_source",
            )
        })
        selected_program_path_rows = []
        for capability in program_trajectory_owners:
            capability_attrs = agent.s.node(capability)["attrs"]
            for path in agent.inner.neighbours(
                capability, "has_selected_embodied_program_path"
            ):
                path_attrs = agent.s.node(path)["attrs"]
                path_transitions = set(agent.inner.neighbours(
                    path, "contains_embodied_program_transition"
                ))
                current_sources = set(agent.inner.neighbours(
                    capability,
                    "has_current_embodied_program_transition_source",
                ))
                next_programs = [
                    program
                    for transition in sorted(
                        path_transitions & current_sources,
                        key=str,
                    )
                    for program in agent.inner.neighbours(
                        transition, "continues_with_embodied_program"
                    )
                ]
                phase_members = [
                    member
                    for program in next_programs
                    for member in agent.inner.neighbours(
                        program, "includes_humanoid_phase_action_model"
                    )
                ]
                selected_program_path_rows.append({
                    "capability": capability_attrs.get(
                        "name", capability_attrs.get("goal", "unknown")
                    ),
                    "capability_status": capability_attrs.get(
                        "status", "unknown"
                    ),
                    "reassess_after": sorted(
                        str(agent.s.node(required)["attrs"].get(
                            "name", "unknown"
                        ))
                        for required in agent.inner.neighbours(
                            capability,
                            "reassess_after_learning_capability",
                        )
                    ),
                    "depth": int(path_attrs.get("depth", 0)),
                    "trajectory_replay_issued_seq": int(path_attrs.get(
                        "trajectory_replay_issued_seq", 0
                    )),
                    "next_program_count": len(next_programs),
                    "phase_member_count": len(phase_members),
                    "minimum_member_experience_count": min((
                        float(agent.s.node(member)["attrs"].get(
                            "experience_count", 0.0
                        ))
                        for member in phase_members
                    ), default=0.0),
                    "minimum_member_context_delta_experience_count": min((
                        float(agent.s.node(member)["attrs"].get(
                            "context_delta_experience_count", 0.0
                        ))
                        for member in phase_members
                    ), default=0.0),
                    **{
                        field: path_attrs.get(
                            f"last_manifold_projection_{field}"
                        )
                        for field in (
                            "support", "resolved", "loss",
                            "information_loss", "horizon", "anchor_count",
                            "refinement_count", "termination_code",
                            "exploration_authority",
                            "effort_supported", "projected_effort",
                            "ideal_effort", "effort_scale",
                            "effort_residual", "time_compression",
                            "width_compression", "information_compression",
                            "compression_dimension_count",
                            "manifold_compression", "effort_authorized",
                            *(f"situated_support_{index}"
                              for index in range(7)),
                            *(f"applied_bound_{index}"
                              for index in range(7)),
                        )
                    },
                })
        selected_program_path_rows.sort(key=lambda row: (
            str(row["capability"]), int(row["depth"])
        ))
        ordinary_action_tokens = {
            str(agent.s.node(model)["attrs"].get("token", ""))
            for model in agent.inner.neighbours(
                episode, "has_humanoid_action_model"
            )
        }
        phase_action_keys = {
            (
                str(agent.s.node(model)["attrs"].get("token", "")),
                float(agent.s.node(model)["attrs"].get(
                    "support_phase", -1.0
                )),
            )
            for model in agent.inner.neighbours(
                episode, "has_humanoid_phase_action_model"
            )
        }
        rejected_program_path_rows = []
        for path in program_path_nodes:
            path_attrs = agent.s.node(path)["attrs"]
            rejection_count = int(path_attrs.get(
                "manifold_rejection_count", 0
            ))
            blocked_sources = agent.inner.neighbours(
                path, "manifold_blocked_from_embodied_program_transition"
            )
            if rejection_count <= 0 and not blocked_sources:
                continue
            path_transitions = agent.inner.neighbours(
                path, "contains_embodied_program_transition"
            )
            target_programs = [
                program
                for transition in path_transitions
                for program in agent.inner.neighbours(
                    transition, "continues_with_embodied_program"
                )
            ]
            rejected_program_path_rows.append({
                "depth": int(path_attrs.get("depth", 0)),
                "manifold_rejection_count": rejection_count,
                "blocked_source_count": len(blocked_sources),
                "transition_count": len(path_transitions),
                "origin_count": len(agent.inner.neighbours(
                    path, "starts_from_embodied_program"
                )),
                "terminal_count": len(agent.inner.neighbours(
                    path, "continues_with_embodied_program"
                )),
                "target_program_count": len(target_programs),
                "target_statuses": sorted(
                    str(agent.s.node(program)["attrs"].get(
                        "status", "unknown"
                    ))
                    for program in target_programs
                ),
                "target_library_member_count": sum(
                    len(agent.inner.neighbours(
                        program, "has_humanoid_library_motor_member"
                    ))
                    for program in target_programs
                ),
                "target_ordinary_action_candidate_count": sum(
                    str(agent.s.node(member)["attrs"].get("token", ""))
                    in ordinary_action_tokens
                    for program in target_programs
                    for member in agent.inner.neighbours(
                        program, "has_humanoid_library_motor_member"
                    )
                ),
                "target_phase_action_candidate_count": sum(
                    (
                        str(agent.s.node(member)["attrs"].get("token", "")),
                        float(agent.s.node(member)["attrs"].get(
                            "support_phase", -1.0
                        )),
                    ) in phase_action_keys
                    for program in target_programs
                    for member in agent.inner.neighbours(
                        program, "has_humanoid_library_motor_member"
                    )
                ),
                "target_live_member_count": sum(
                    sum(
                        len(agent.inner.neighbours(program, relation))
                        for relation in (
                            "includes_humanoid_phase_action_model",
                            "includes_humanoid_action_model",
                        )
                    )
                    for program in target_programs
                ),
                **{
                    field: path_attrs.get(
                        f"last_manifold_projection_{field}"
                    )
                    for field in (
                        "support", "resolved", "loss", "information_loss",
                        "horizon", "anchor_count", "refinement_count",
                        "termination_code", "effort_supported",
                        "projected_effort", "ideal_effort", "effort_scale",
                        "effort_residual", "time_compression",
                        "width_compression", "information_compression",
                        "compression_dimension_count", "manifold_compression",
                        "effort_authorized",
                    )
                },
            })
        rejected_program_path_rows.sort(key=lambda row: (
            int(row["depth"]),
            int(row["manifold_rejection_count"]),
            json.dumps(row, sort_keys=True, separators=(",", ":")),
        ))
        episode_effector_models = agent.inner.neighbours(
            episode, "has_embodied_effector_model"
        )
        if not episode_effector_models:
            episode_effector_models = agent.inner.neighbours(
                episode, "has_humanoid_phase_action_model"
            )
        program_trajectory_report = {
            "trajectory_count": len(program_trajectory_nodes),
            "active_trajectory_count": len(active_program_trajectory_nodes),
            "parked_trajectory_count": (
                len(program_trajectory_nodes)
                - len(active_program_trajectory_nodes)
            ),
            "verified_transition_count": len(program_transition_nodes),
            "path_count": len(program_path_nodes),
            "maximum_path_depth": max((
                int(agent.s.node(path)["attrs"].get("depth", 0))
                for path in program_path_nodes
            ), default=0),
            "selected_path_count": len(selected_program_path_nodes),
            "selected_paths": selected_program_path_rows,
            "rejected_paths": rejected_program_path_rows,
            "manifold_rejection_count": sum(
                int(agent.s.node(path)["attrs"].get(
                    "manifold_rejection_count", 0
                ))
                for path in program_path_nodes
            ),
            "contextually_blocked_path_count": sum(
                bool(agent.inner.neighbours(
                    path,
                    "manifold_blocked_from_embodied_program_transition",
                ))
                for path in program_path_nodes
            ),
            "projection_reference_model_count": sum(
                float(agent.s.node(model)["attrs"].get(
                    "activation_magnitude", 0.0
                )) < 0.5
                and float(agent.s.node(model)["attrs"].get(
                    "context_delta_experience_count", 0.0
                )) > 0.0
                for model in episode_effector_models
            ),
            "maximum_expansion_count": max((
                int(agent.s.node(trajectory)["attrs"].get(
                    "expansion_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ), default=0),
            "maximum_expansion_budget_units": max((
                int(agent.s.node(trajectory)["attrs"].get(
                    "expansion_budget_units", 0
                ))
                for trajectory in program_trajectory_nodes
            ), default=0),
            "completed_replay_count": sum(
                int(agent.s.node(capability)["attrs"].get(
                    "trajectory_replay_count", 0
                ))
                for capability in program_trajectory_owners
            ),
            "capability_evidence_transition_count": sum(
                int(agent.s.node(transition)["attrs"].get(
                    "capability_evidence_units", 0
                )) > 0
                for transition in program_transition_nodes
            ),
            "positive_task_progress_transition_count": sum(
                int(agent.s.node(transition)["attrs"].get(
                    "task_progress_units", 0
                )) > 0
                for transition in program_transition_nodes
            ),
            "maximum_task_progress_transition_units": max((
                int(agent.s.node(transition)["attrs"].get(
                    "task_progress_units", 0
                ))
                for transition in program_transition_nodes
            ), default=0),
            "active_capability_positive_task_progress_transition_count": sum(
                int(agent.s.node(transition)["attrs"].get(
                    "task_progress_units", 0
                )) > 0
                for transition in active_capability_transition_nodes
            ),
            "active_capability_maximum_task_progress_transition_units": max((
                int(agent.s.node(transition)["attrs"].get(
                    "task_progress_units", 0
                ))
                for transition in active_capability_transition_nodes
            ), default=0),
            "capability_evidence_path_count": sum(
                int(agent.s.node(path)["attrs"].get(
                    "capability_evidence_units", 0
                )) > 0
                for path in program_path_nodes
            ),
            "positive_task_progress_path_count": sum(
                int(agent.s.node(path)["attrs"].get(
                    "task_progress_units", 0
                )) > 0
                for path in program_path_nodes
            ),
            "active_capability_positive_task_progress_path_count": sum(
                int(agent.s.node(path)["attrs"].get(
                    "task_progress_units", 0
                )) > 0
                for path in active_capability_path_nodes
            ),
            "orientation_preserving_evidence_path_count": sum(
                int(agent.s.node(path)["attrs"].get(
                    "orientation_span_units", 0
                )) == 0
                and int(agent.s.node(path)["attrs"].get(
                    "capability_evidence_units", 0
                )) > 0
                for path in program_path_nodes
            ),
            "current_capability_evidence_transition_count": sum(
                int(agent.s.node(transition)["attrs"].get(
                    "capability_evidence_units", 0
                )) > 0
                for transition in capability_current_transition_sources
            ),
            "selection_count": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "selection_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ),
            "capacity_pareto_selection_count": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "capacity_pareto_selection_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ),
            "capacity_dominated_path_count": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "capacity_dominated_path_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ),
            "maximum_capacity_candidate_count": max((
                int(agent.s.node(trajectory)["attrs"].get(
                    "last_capacity_candidate_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ), default=0),
            "maximum_capacity_frontier_count": max((
                int(agent.s.node(trajectory)["attrs"].get(
                    "last_capacity_frontier_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ), default=0),
            "maximum_selected_conditional_narrativium_retained": [
                max((
                    int(agent.s.node(trajectory)["attrs"].get(
                        "selected_conditional_narrativium_retained_"
                        f"{dimension}",
                        0,
                    ))
                    for trajectory in program_trajectory_nodes
                ), default=0)
                for dimension in range(7)
            ],
            "selected_capability_evidence_units": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "selected_capability_evidence_units", 0
                ))
                for trajectory in program_trajectory_nodes
            ),
            "selected_task_progress_units": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "selected_task_progress_units", 0
                ))
                for trajectory in program_trajectory_nodes
            ),
            "active_capability_selected_task_progress_units": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "selected_task_progress_units", 0
                ))
                for trajectory in active_capability_trajectory_nodes
            ),
            "selected_orientation_preserving_evidence_count": sum(
                int(agent.s.node(trajectory)["attrs"].get(
                    "selected_orientation_preserving_evidence_count", 0
                ))
                for trajectory in program_trajectory_nodes
            ),
            "latest_selected_state_shape_residual_units": max((
                int(agent.s.node(trajectory)["attrs"].get(
                    "selected_state_shape_residual_units", 0
                ))
                for trajectory in program_trajectory_nodes
                if int(agent.s.node(trajectory)["attrs"].get(
                    "selection_count", 0
                )) > 0
            ), default=0),
        }
        locomotor_phenotype_rows = []
        locomotor_phenotype_family_rows = []
        if development_context is not None:
            for phenotype in agent.inner.neighbours(
                development_context, "has_embodied_locomotor_phenotype"
            ):
                row = dict(agent.s.node(phenotype)["attrs"])
                candidates = agent.inner.neighbours(
                    phenotype, "publishes_locomotor_pareto_candidate"
                )
                row["pareto_candidate_count"] = len(candidates)
                row["pareto_dominated"] = int(any(
                    agent.inner.neighbours(
                        candidate, "is_dominated_by_pareto_candidate"
                    )
                    for candidate in candidates
                ))
                locomotor_phenotype_rows.append(row)
            locomotor_phenotype_rows.sort(
                key=lambda row: json.dumps(
                    row.get("signature", ()), separators=(",", ":")
                )
            )
            for family in agent.inner.neighbours(
                development_context,
                "has_embodied_locomotor_phenotype_family",
            ):
                row = dict(agent.s.node(family)["attrs"])
                candidates = agent.inner.neighbours(
                    family, "publishes_locomotor_pareto_candidate"
                )
                row["pareto_candidate_count"] = len(candidates)
                row["pareto_dominated"] = int(any(
                    agent.inner.neighbours(
                        candidate, "is_dominated_by_pareto_candidate"
                    )
                    for candidate in candidates
                ))
                row["refinement_count"] = sum(
                    family in agent.inner.neighbours(
                        phenotype, "refines_locomotor_phenotype_family"
                    )
                    for phenotype in agent.inner.neighbours(
                        development_context, "has_embodied_locomotor_phenotype"
                    )
                )
                locomotor_phenotype_family_rows.append(row)
            locomotor_phenotype_family_rows.sort(
                key=lambda row: json.dumps(
                    row.get("signature", ()), separators=(",", ":")
                )
            )

    directed_progress = completed_attempt_progress + heading_x * (
        float(observation["base_position"][0]) - start_x
    )
    lateral_offset = float(observation["base_position"][1]) - start_y
    phase_models_after_walk = _phase_model_rows(agent, episode)
    phase_before_by_context = {
        (row["token"], row["support_phase"], row["context_id"]): row
        for row in phase_models_after_adaptation
    }

    def phase_counter_delta(counter: str) -> int:
        return int(sum(
            max(
                0.0,
                float(row.get(counter) or 0.0)
                - float(phase_before_by_context.get(
                    (
                        row["token"],
                        row["support_phase"],
                        row["context_id"],
                    ),
                    {},
                ).get(counter) or 0.0),
            )
            for row in phase_models_after_walk
        ))

    deployment_prediction_confirmations = phase_counter_delta(
        "prediction_confirmation_count"
    )
    deployment_prediction_invalidations = phase_counter_delta(
        "prediction_invalidation_count"
    )
    deployment_prediction_regrounds = phase_counter_delta(
        "prediction_reground_count"
    )
    # A contradictory receipt both invalidates and re-grounds one model; count
    # it once as a learning event rather than treating the intentional reset
    # of experience_count as negative learning.
    deployment_learning_events = (
        deployment_prediction_confirmations
        + deployment_prediction_regrounds
    )
    synergy_rows = [
        dict(agent.s.node(model)["attrs"])
        for model in agent.inner.neighbours(
            episode,
            "has_humanoid_synergy_model",
        )
    ]
    residual_regime_rows = sorted(
        (
            dict(agent.s.node(regime)["attrs"])
            for regime in agent.inner.neighbours(
                policy,
                "has_humanoid_residual_regime",
            )
        ),
        key=lambda row: float(row["ordinal"]),
    )
    gait_profile = install_pareto_profile(agent, episode, (
        {"name": "directed_step", "ordinal": 0, "direction": "maximize"},
        {"name": "lateral_step", "ordinal": 1, "direction": "minimize"},
        {"name": "tilt", "ordinal": 2, "direction": "minimize"},
        {"name": "height_deficit", "ordinal": 3, "direction": "minimize"},
        {"name": "support_deficit", "ordinal": 4, "direction": "minimize"},
        {"name": "normalized_energy", "ordinal": 5, "direction": "minimize"},
        {"name": "prediction_residual", "ordinal": 6, "direction": "minimize"},
    ), context="humanoid_gait_regime")
    gait_profile_candidates = {}
    for row in residual_regime_rows:
        if (
            float(row.get("sample_count", 0.0)) <= 0.0
            or float(row.get("unsafe_receipt_count", 0.0)) > 0.0
        ):
            continue
        identity = f"gait_regime:{int(float(row['ordinal']))}"
        gait_profile_candidates[identity] = publish_pareto_candidate(
            agent,
            gait_profile,
            {
                "directed_step": float(row["mean_directed_step"]),
                "lateral_step": float(row["mean_abs_lateral_step"]),
                "tilt": float(row["mean_tilt"]),
                "height_deficit": float(row["mean_height_deficit"]),
                "support_deficit": float(row["mean_support_deficit"]),
                "normalized_energy": float(row["mean_normalized_energy"]),
                "prediction_residual": float(row["fast_prediction_residual"]),
            },
            identity=identity,
        )
    gait_profile_report = evaluate_pareto_profile(agent, gait_profile)
    gait_profile_frontier = {
        agent.s.node(candidate)["attrs"]["identity"]
        for candidate in pareto_frontier(agent, gait_profile)
    }
    gait_profile_rows = [
        {
            "identity": identity,
            "frontier": identity in gait_profile_frontier,
            "dominated_by": sorted(
                agent.s.node(other)["attrs"]["identity"]
                for other in agent.inner.neighbours(
                    candidate,
                    "is_dominated_by_embodied_candidate",
                )
            ),
        }
        for identity, candidate in sorted(gait_profile_candidates.items())
    ]
    gait_attractor_rows = sorted(
        (
            dict(agent.s.node(gait)["attrs"])
            for gait in agent.inner.neighbours(
                policy,
                "has_humanoid_gait_attractor",
            )
        ),
        key=lambda row: float(row["ordinal"]),
    )
    active_gait_ordinal = float(final["active_gait_attractor_ordinal"])
    active_gait = next(
        row
        for row in gait_attractor_rows
        if float(row["ordinal"]) == active_gait_ordinal
    )
    motor_program_rows = []
    programs = list(agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    ))
    programs.extend(agent.inner.neighbours(
        episode,
        "has_consolidated_humanoid_motor_program",
    ))
    for program in programs:
        attrs = dict(agent.s.node(program)["attrs"])
        members = agent.inner.neighbours(
            program,
            "includes_humanoid_phase_action_model",
        )
        attrs["motor_tokens"] = [
            agent.s.node(member)["attrs"]["token"]
            for member in sorted(
                members,
                key=lambda member: float(
                    agent.s.node(member)["attrs"]["ordinal"]
                ),
            )
        ]
        motor_program_rows.append(attrs)
    motor_transition_rows = []
    for transition in agent.inner.neighbours(
        episode,
        "has_humanoid_motor_transition",
    ):
        attrs = dict(agent.s.node(transition)["attrs"])
        successors = agent.inner.neighbours(
            transition,
            "continues_with_humanoid_motor_program",
        )
        if len(successors) != 1:
            successor_rows = [
                (str(successor), dict(agent.s.node(successor)["attrs"]))
                for successor in successors
            ]
            raise RuntimeError(
                "motor transition does not have exactly one successor: "
                f"transition={attrs!r}, successors={successor_rows!r}"
            )
        successor_attrs = agent.s.node(successors[0])["attrs"]
        attrs["next_motor_tokens"] = [
            agent.s.node(member)["attrs"]["token"]
            for member in sorted(
                agent.inner.neighbours(
                    successors[0],
                    "includes_humanoid_phase_action_model",
                ),
                key=lambda member: float(
                    agent.s.node(member)["attrs"]["ordinal"]
                ),
            )
        ]
        attrs["next_program_ordinal"] = successor_attrs["ordinal"]
        motor_transition_rows.append(attrs)
    motor_preparation_rows = [
        dict(agent.s.node(preparation)["attrs"])
        for preparation in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_preparation",
        )
    ]
    get_up_model_rows = [
        dict(agent.s.node(model)["attrs"])
        for model in agent.inner.neighbours(
            episode,
            "has_humanoid_get_up_action_model",
        )
    ]
    recovery_basin_rows = []
    for basin in agent.inner.neighbours(
        episode,
        "has_humanoid_recovery_basin",
    ):
        row = dict(agent.s.node(basin)["attrs"])
        recovery_actions = agent.inner.neighbours(
            basin,
            "has_humanoid_recovery_basin_action",
        )
        profile = install_pareto_profile(agent, basin, (
            {"name": "height_gain", "ordinal": 0, "direction": "maximize"},
            {"name": "alignment_gain", "ordinal": 1, "direction": "maximize"},
            {"name": "support_gain", "ordinal": 2, "direction": "maximize"},
            {"name": "contact_gain", "ordinal": 3, "direction": "maximize"},
            {"name": "motion_reduction", "ordinal": 4, "direction": "maximize"},
            {"name": "normalized_energy", "ordinal": 5, "direction": "minimize"},
            {"name": "normalized_peak_load", "ordinal": 6, "direction": "minimize"},
        ), context="humanoid_recovery_basin")
        candidates = {}
        for action_index, recovery_action in enumerate(recovery_actions):
            attrs = agent.s.node(recovery_action)["attrs"]
            identity = (
                f"recovery:{int(float(row.get('ordinal', 0.0)))}:"
                f"{action_index}:{attrs.get('primary_token', '')}:"
                f"{attrs.get('secondary_token', '')}"
            )
            candidates[recovery_action] = publish_pareto_candidate(
                agent,
                profile,
                {
                    "height_gain": float(attrs.get("mean_height_gain", 0.0)),
                    "alignment_gain": float(attrs.get("mean_alignment_gain", 0.0)),
                    "support_gain": float(attrs.get("mean_support_gain", 0.0)),
                    "contact_gain": float(attrs.get("mean_contact_gain", 0.0)),
                    "motion_reduction": float(attrs.get("mean_motion_reduction", 0.0)),
                    "normalized_energy": float(attrs.get("mean_normalized_energy", 0.0)),
                    "normalized_peak_load": float(attrs.get("mean_normalized_peak_load", 0.0)),
                },
                identity=identity,
            )
        evaluate_pareto_profile(agent, profile)
        frontier = set(pareto_frontier(agent, profile))
        row["actions"] = []
        for recovery_action in recovery_actions:
            attrs = dict(agent.s.node(recovery_action)["attrs"])
            candidate = candidates[recovery_action]
            attrs["pareto_frontier"] = candidate in frontier
            attrs["dominated_by"] = sorted(
                agent.s.node(other)["attrs"]["identity"]
                for other in agent.inner.neighbours(
                    candidate,
                    "is_dominated_by_embodied_candidate",
                )
            )
            row["actions"].append(attrs)
        row["successor_ordinals"] = [
            agent.s.node(successor)["attrs"].get("ordinal", 0.0)
            for successor in agent.inner.neighbours(
                basin,
                "continues_to_humanoid_recovery_basin",
            )
        ]
        recovery_basin_rows.append(row)
    graph_lifetime_progress = (
        float(final.get("lifetime_completed_progress", 0.0))
        + float(final["directed_progress"])
    )
    locomotor_path_length = float(final["locomotor_path_length"])
    locomotor_forward_reversals = float(
        final["locomotor_forward_reversal_count"]
    )
    gait_path_efficiency = (
        max(0.0, graph_lifetime_progress) / locomotor_path_length
        if locomotor_path_length > 0.0
        else 0.0
    )
    forward_reversal_fraction = (
        locomotor_forward_reversals / max(1, len(trace) - 1)
    )
    compound_action_count = sum(
        row["motor_bundle_width"] > 1 for row in trace
    )
    post_gate_rows = [
        row
        for row in trace
        if float(row.get("manifold_bounds_ready", 0.0)) > 0.5
    ]
    first_bounds_ready_action = (
        post_gate_rows[0]["action"] if post_gate_rows else None
    )
    maximum_post_gate_motor_program_width = max(
        (int(row["motor_bundle_width"]) for row in post_gate_rows),
        default=0,
    )
    combined_collapse_rows = [
        row
        for row in trace
        if row.get("collapse_kind") == "compound_recovery_locomotion"
    ]
    effector_assembly_rows = []
    if effector_topology is not None:
        for assembly in agent.inner.neighbours(
            episode,
            "has_embodied_effector_assembly",
        ):
            attrs = dict(agent.s.node(assembly)["attrs"])
            attrs["member_ordinals"] = sorted(
                float(agent.s.node(member)["attrs"]["ordinal"])
                for member in agent.inner.neighbours(
                    assembly,
                    "includes_embodied_effector",
                )
            )
            effector_assembly_rows.append(attrs)
    current_developmental_contract = developmental_curriculum_contract()
    runtime_body_schemas = agent.inner.neighbours(
        episode, "has_embodied_body_schema"
    )
    runtime_raw_bodies = [
        raw_body
        for body_schema in runtime_body_schemas
        for raw_body in agent.inner.neighbours(
            body_schema, "grounded_in_embodied_raw_body"
        )
    ]
    all_body_schemas = list(agent.s.nodes("EmbodiedBodySchema"))
    all_raw_bodies = list(agent.s.nodes("EmbodiedRawBodyObservation"))
    situated_projection_rows = [
        row for row in selected_program_path_rows
        if row.get("exploration_authority") is not None
    ]
    latest_situated_projection = max(
        situated_projection_rows,
        key=lambda row: int(row.get("trajectory_replay_issued_seq", 0)),
        default={},
    )
    subsection_composition_questions = [
        question
        for question in agent.s.nodes("EmbodiedPhysicsQuestion")
        if agent.s.node(question)["attrs"].get("kind")
        == "situated_subsection_composition"
    ]
    subsection_composition_rows = []
    subsection_selected_plan_ids = set()
    subsection_proposal_rows = []
    for question in subsection_composition_questions:
        question_attrs = agent.s.node(question)["attrs"]
        question_capabilities = agent.inner.neighbours(
            question, "targets_learning_capability"
        )
        question_capability_name = (
            agent.s.node(question_capabilities[0])["attrs"].get("name")
            if len(question_capabilities) == 1 else None
        )
        selected_proposals = set(agent.inner.neighbours(
            question, "has_selected_motor_learning_proposal"
        ))
        for proposal in agent.inner.neighbours(
            question, "has_motor_learning_proposal"
        ):
            proposal_attrs = agent.s.node(proposal)["attrs"]
            proposed_plans = agent.inner.neighbours(
                proposal, "proposes_counterfactual_motor_program"
            )
            subsection_proposal_rows.append({
                "status": proposal_attrs.get("status"),
                "eligible": proposal_attrs.get("eligible", 0),
                "selected": int(proposal in selected_proposals),
                "proposed_plan_count": len(proposed_plans),
            })
            if proposal in selected_proposals:
                subsection_selected_plan_ids.update(proposed_plans)
        for plan in agent.inner.neighbours(
            question, "has_counterfactual_motor_program"
        ):
            plan_attrs = agent.s.node(plan)["attrs"]
            if plan_attrs.get("subsection_composition") != 1:
                continue
            subsection_composition_rows.append({
                key: plan_attrs.get(key)
                for key in (
                    "status",
                    "member_count",
                    "primary_token",
                    "secondary_token",
                    "subsection_composition_manifold_admissible",
                    "predicted_evidence_units",
                    "interaction_uncertainty_units",
                    "predicted_energy_units",
                    "predicted_peak_load_units",
                    "predicted_recoverability_units",
                    "subsection_composition_manifold_support",
                    "subsection_composition_manifold_resolved",
                    "subsection_composition_manifold_loss",
                    "subsection_composition_manifold_information_loss",
                    "subsection_composition_manifold_effort_supported",
                    "subsection_composition_manifold_effort_authorized",
                    "physical_verified",
                    "interaction_residual_units",
                    "development_elevation_sum_units",
                    "development_vertical_velocity_progress_sum_units",
                )
            } | {
                "selected": int(plan in subsection_selected_plan_ids),
                "question_status": question_attrs.get("status"),
                "question_request_seq": question_attrs.get("request_seq"),
                "question_capability": question_capability_name,
            })
    subsection_composition_status_counts = Counter(
        str(row.get("status")) for row in subsection_composition_rows
    )
    rule_cost_rows = sorted(
        (
            {
                "rule": name,
                "micros": micros,
                "visits": visits,
                "progressions": progressions,
            }
            for name, micros, visits, progressions
            in agent.s._inner.rule_costs()
            if micros > 0
        ),
        key=lambda row: row["micros"],
        reverse=True,
    )
    developmental_reset_diagnostics = {}
    if development_context is not None:
        development_context_attrs = dict(
            agent.s.node(development_context)["attrs"]
        )
        hot_receipts = sorted(
            (
                dict(agent.s.node(receipt)["attrs"])
                for receipt in agent.inner.neighbours(
                    development_context,
                    "has_embodied_development_receipt",
                )
            ),
            key=lambda attrs: attrs.get("development_receipt_seq", -1),
        )
        reset_requests = [
            dict(agent.s.node(request)["attrs"])
            for request in agent.inner.neighbours(
                development_context,
                "has_active_embodied_reset_request",
            )
        ]
        developmental_reset_diagnostics = {
            "development": {
                key: development_context_attrs.get(key)
                for key in (
                    "latest_development_receipt_seq",
                    "development_evidence_window",
                    "embodiment_reset_available",
                    "embodiment_terminal",
                    "embodied_reset_requested",
                    "reset_requested",
                )
            },
            "latest_hot_receipt": (
                {
                    key: hot_receipts[-1].get(key)
                    for key in (
                        "development_receipt_seq",
                        "development_receipt_closed",
                        "development_experience_retained",
                        "embodiment_destroyed",
                        "development_elevation_units",
                        "development_support_gain",
                        "development_post_support_count",
                    )
                }
                if hot_receipts else None
            ),
            "active_reset_requests": reset_requests,
        }
    ideal_effort_state_rows = sorted(
        (
            dict(agent.s.node(state)["attrs"])
            for state in agent.inner.neighbours(
                episode, "has_embodied_ideal_effort_state"
            )
        ),
        key=lambda row: str(row.get("motor_task_context", "general")),
    )

    def deployment_program_context_row(program):
        attrs = agent.s.node(program)["attrs"]
        return {
            "primary_token": attrs.get("primary_token"),
            "motor_task_context": attrs.get("motor_task_context"),
            "motor_task_phase": attrs.get("motor_task_phase"),
            "status": attrs.get("status"),
            "signature": attrs.get("signature"),
            "phase_member_tokens": sorted(
                str(agent.s.node(member)["attrs"].get("token", ""))
                for member in agent.inner.neighbours(
                    program, "includes_humanoid_phase_action_model"
                )
            ),
            "library_member_tokens": sorted(
                str(agent.s.node(member)["attrs"].get("token", ""))
                for member in agent.inner.neighbours(
                    program, "has_humanoid_library_motor_member"
                )
            ),
        }

    deployment_owners = agent.inner.neighbours(
        episode, "has_embodied_deployment_program_owner"
    )
    developmental_memory_diagnostics = []
    if development_context is not None:
        development_signature = agent.s.node(development_context)["attrs"].get(
            "body_capability_signature"
        )
        instances_by_name = {
            str(agent.s.node(instance)["attrs"].get("name", "")): instance
            for instance in agent.inner.neighbours(
                development_context, "has_embodied_developmental_capability"
            )
        }
        for memory in agent.inner.neighbours(
            agent.agent, "has_embodied_developmental_capability_memory"
        ):
            memory_attrs = agent.s.node(memory)["attrs"]
            capability_name = str(memory_attrs.get("capability_name", ""))
            instance = instances_by_name.get(capability_name)
            instance_attrs = (
                agent.s.node(instance)["attrs"] if instance is not None else {}
            )
            developmental_memory_diagnostics.append({
                "capability_name": capability_name,
                "instance_present": int(instance is not None),
                "signature_matches": int(
                    memory_attrs.get("signature") == development_signature
                ),
                "goal_matches": int(
                    instance is not None
                    and memory_attrs.get("goal") == instance_attrs.get("goal")
                ),
                "evidence_kind_matches": int(
                    instance is not None
                    and memory_attrs.get("evidence_kind")
                    == instance_attrs.get("evidence_kind")
                ),
                "instance_attempt_count": int(instance_attrs.get(
                    "attempt_count", 0
                )),
                "instance_status": instance_attrs.get("status"),
                "exact_recall_edge_count": (
                    len(agent.inner.neighbours(
                        instance,
                        "recalls_exact_embodied_developmental_capability",
                    ))
                    if instance is not None else 0
                ),
            })
        developmental_memory_diagnostics.sort(
            key=lambda row: row["capability_name"]
        )
    result = {
        "curriculum_rule_costs": rule_cost_rows,
        "developmental_reset_diagnostics": developmental_reset_diagnostics,
        "developmental_memory_diagnostics": developmental_memory_diagnostics,
        "mode": mode,
        "developmental_curriculum_contract": current_developmental_contract,
        "developmental_curriculum_contract_digest": (
            current_developmental_contract["ontology_sha256"]
        ),
        "future_manifold": {
            "enabled": final_policy.get("future_manifold_enabled", 0.0),
            "temporal_anchors_enabled": final_policy.get(
                "future_manifold_temporal_anchors_enabled", 0.0
            ),
            "bounds_ready": final.get("manifold_bounds_ready", 0.0),
            "bounds_provenance": final.get(
                "manifold_bounds_provenance", "unavailable"
            ),
            "bounds": {
                key: final.get(f"manifold_bound_{key}", 0.0)
                for key in (
                    "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"
                )
            },
            "learning_safety_context": {
                key: safety_context.get(key, 0)
                for key in (
                    "verified", "reset_reachable", "reset_cost_units",
                    "protective_support_available",
                    "protective_support_effectiveness",
                    "recovery_path_count",
                )
            },
            "learning_safety_active": int(
                safety_context.get("verified", 0) > 0.5
            ),
            "declared_exploration_budgets": {
                key: safety_context.get(key, 0)
                for key in (
                    "required_horizon_units",
                    "exploration_width_budget",
                    "exploration_information_budget",
                )
            },
            "latest_situated_projection": {
                "exploration_authority": latest_situated_projection.get(
                    "exploration_authority", 0.0
                ),
                "support_field": [
                    latest_situated_projection.get(
                        f"situated_support_{index}", 0.0
                    ) for index in range(7)
                ],
                "applied_bounds": [
                    latest_situated_projection.get(
                        f"applied_bound_{index}", 0.0
                    ) for index in range(7)
                ],
            },
            "ideal_effort": {
                "context": final.get(
                    "future_manifold_ideal_effort_context", "general"
                ),
                "ratio": final.get("future_manifold_ideal_effort", 0.0),
                "evidence_count": final.get(
                    "future_manifold_ideal_effort_evidence_count", 0
                ),
                "scale_joules": final.get(
                    "future_manifold_effort_scale_joules", 0.0
                ),
                "audit_count": final.get(
                    "manifold_effort_audit_count", 0
                ),
                "supported_audit_count": final.get(
                    "manifold_effort_supported_audit_count", 0
                ),
                "blocked_audit_count": final.get(
                    "manifold_effort_blocked_audit_count", 0
                ),
                "compression_audit_count": final.get(
                    "manifold_effort_compression_audit_count", 0
                ),
                "situated_states": ideal_effort_state_rows,
            },
        },
        "subsection_composition": {
            "question_count": len(subsection_composition_questions),
            "plan_count": len(subsection_composition_rows),
            "proposal_count": len(subsection_proposal_rows),
            "selected_plan_count": len(subsection_selected_plan_ids),
            "manifold_admissible_plan_count": sum(
                row.get("subsection_composition_manifold_admissible") == 1
                for row in subsection_composition_rows
            ),
            "physical_verified_plan_count": sum(
                row.get("physical_verified") == 1
                for row in subsection_composition_rows
            ),
            "status_counts": dict(subsection_composition_status_counts),
            "proposal_status_counts": dict(Counter(
                str(row.get("status")) for row in subsection_proposal_rows
            )),
            "release_context": {
                key: agent.s.node(episode)["attrs"].get(key)
                for key in (
                    "developmental_curriculum_active",
                    "phase",
                    "sensorimotor_interrupt_required",
                    "reset_requested",
                    "caregiver_protective_support_available",
                    "locomotion_drive_active",
                    "request_seq",
                    "decision_seq",
                    "action_ready",
                    "structural_interrupt_required",
                )
            } | {
                "ready_program_count": len(agent.inner.neighbours(
                    episode, "has_ready_humanoid_motor_program"
                )),
                "active_capability_count": len(
                    active_developmental_capabilities
                ),
                "development_evidence_window": (
                    agent.s.node(development_context)["attrs"].get(
                        "development_evidence_window"
                    )
                    if development_context is not None else None
                ),
                "active_capability": (
                    {
                        key: agent.s.node(
                            active_developmental_capabilities[0]
                        )["attrs"].get(key)
                        for key in (
                            "name", "goal", "developmental_ecology",
                            "success_count", "failure_count",
                            "active_physical_experiment_lease_count",
                        )
                    }
                    if len(active_developmental_capabilities) == 1 else {}
                ),
            },
            "plans": subsection_composition_rows,
            "proposals": subsection_proposal_rows,
        },
        "policy_owner": "rust_graph",
        "first_bounds_ready_action": first_bounds_ready_action,
        "post_gate_action_count": len(post_gate_rows),
        "maximum_post_gate_motor_program_width": (
            maximum_post_gate_motor_program_width
        ),
        "trajectory_architecture": (
            "persistent_residual_support_preview"
            if persistent_task_residual_authority == 1.0
            else "body_trajectory_only"
        ),
        "support_geometry_preview_authority": (
            support_geometry_preview_authority
        ),
        "persistent_task_residual_authority": (
            persistent_task_residual_authority
        ),
        "target_directed_progress_m": target_directed_progress_m,
        "faculty_autogenesis": {
            "need_count": len(list(agent.s.nodes("FacultyNeed"))),
            "installed_count": sum(
                agent.s.node(need)["attrs"].get("status") == "installed"
                for need in agent.s.nodes("FacultyNeed")
            ),
            "meta_faculty_gap_count": len(list(
                agent.s.nodes("MetaFacultyGap")
            )),
            "self_authored_held_count": sum(
                agent.s.node(program)["attrs"].get("self_authored") == 1
                for program in agent.inner.neighbours(
                    agent.agent, "holds_faculty"
                )
            ),
        },
        "cognitive_supervision": {
            "authority_settlement_cycle_count": (
                cognitive_authority_settlement_cycles
            ),
            "process_count": len(list(agent.s.nodes("CognitiveProcess"))),
            "checkin_count": len(list(agent.s.nodes("CognitiveCheckIn"))),
            "continued_count": sum(
                agent.s.node(checkin)["attrs"].get("status") == "continued"
                for checkin in agent.s.nodes("CognitiveCheckIn")
            ),
            "replan_count": sum(
                agent.s.node(checkin)["attrs"].get("status")
                == "replan_required"
                for checkin in agent.s.nodes("CognitiveCheckIn")
            ),
            "continuation_authority_at_end": int(
                _cognitive_continuation_authorised(
                    agent, episode, development_context
                )
            ),
            "experiment_halted_by_checkin": development_final.get(
                "cognitive_checkin_terminal", 0
            ),
            "halt_reason": (
                "cognitive_checkin_terminal"
                if development_final.get("cognitive_checkin_terminal", 0)
                else "none"
            ),
            "processes": _cognitive_process_snapshots(
                agent,
                development_context
                if development_context is not None else episode,
            ),
            "policies": [
                {
                    key: agent.s.node(policy_node)["attrs"].get(key)
                    for key in ("enabled", "cognitive_epoch")
                }
                for policy_node in agent.s.nodes(
                    "CognitiveSupervisionPolicy"
                )
            ],
        },
        "locomotion_residual_m_graph_assessment": final[
            "locomotion_residual_m"
        ],
        "locomotion_drive_active_at_end": final[
            "locomotion_drive_active"
        ],
        "cost_term_decomposition": _cost_term_summary(),
        "active_gait_attractor": active_gait.get("name"),
        "active_gait_attractor_ordinal": active_gait_ordinal,
        "gait_attractors": gait_attractor_rows,
        "active_residual_regime_ordinal": final[
            "active_residual_regime_ordinal"
        ],
        "residual_regime_selection_count": final[
            "residual_regime_selection_count"
        ],
        "residual_control_regimes": residual_regime_rows,
        "gait_pareto_profile": {
            "scalarized": False,
            "dimension_count": 7,
            "candidate_count": len(gait_profile_rows),
            "frontier_count": len(gait_profile_frontier),
            "system_two_steps": gait_profile_report["system_two_steps"],
            "candidates": gait_profile_rows,
        },
        "control_regime": {
            "ordinal": (
                agent.s.node(control_regime)["attrs"].get(
                    "regime_ordinal", 0.0
                )
                if control_regime is not None else 0.0
            ),
            "escalation_count": (
                agent.s.node(control_regime)["attrs"].get(
                    "regime_escalation_count", 0.0
                )
                if control_regime is not None else 0.0
            ),
            "last_escalation_seq": (
                agent.s.node(control_regime)["attrs"].get(
                    "regime_last_escalation_seq", 0.0
                )
                if control_regime is not None else 0.0
            ),
            "evidence_seq": (
                agent.s.node(control_regime)["attrs"].get(
                    "regime_evidence_seq", 0.0
                )
                if control_regime is not None else 0.0
            ),
            "render_first_suspended": final.get(
                "render_first_suspended", 0.0
            ),
            "async_trust_epoch": final.get("async_trust_epoch", 0.0),
        },
        "curriculum": (
            {
                "active": final.get("curriculum_active", 0.0),
                "challenge_count": len(curriculum_challenge_rows),
                "completed_challenges": final.get(
                    "curriculum_completed_challenges",
                    0.0,
                ),
                "safe_challenges": final.get(
                    "curriculum_safe_challenges",
                    0.0,
                ),
                "warm_memory_count": final.get(
                    "curriculum_warm_memory_count",
                    0.0,
                ),
                "stage_ordinal": final.get(
                    (
                        "developmental_stage_ordinal"
                        if developmental_curriculum
                        else "curriculum_stage_ordinal"
                    ),
                    0.0,
                ),
                "challenges": curriculum_challenge_rows,
                "developmental": developmental_curriculum,
                "developmental_curriculum_contract": (
                    current_developmental_contract
                ),
                "developmental_curriculum_contract_digest": (
                    restored_library.get(
                        "developmental_curriculum_contract_digest",
                        current_developmental_contract["ontology_sha256"],
                    )
                ),
                "developmental_library_restored_memory_count": (
                    restored_library.get("developmental_capability_count", 0)
                    + restored_library.get("developmental_experience_count", 0)
                ),
                "development_effector_declared_count": development_final.get(
                    "development_effector_declared_count", 0
                ),
                "development_effector_covered_count": development_final.get(
                    "development_effector_covered_count", 0
                ),
                "development_effector_coverage_complete": development_final.get(
                    "development_effector_coverage_complete", 0
                ),
                "development_effector_coverage_unmeasurable": development_final.get(
                    "development_effector_coverage_unmeasurable", 0
                ),
                "runtime_body_schema_count": len(runtime_body_schemas),
                "runtime_body_affordance_count": sum(
                    len(agent.inner.neighbours(
                        body_schema,
                        "has_opaque_embodied_actuator_affordance",
                    ))
                    for body_schema in runtime_body_schemas
                ),
                "runtime_raw_body_affordance_count": sum(
                    len(agent.inner.neighbours(
                        raw_body,
                        "has_opaque_embodied_actuator_affordance",
                    ))
                    for raw_body in runtime_raw_bodies
                ),
                "all_body_schema_count": len(all_body_schemas),
                "all_body_affordance_count": sum(
                    len(agent.inner.neighbours(
                        body_schema,
                        "has_opaque_embodied_actuator_affordance",
                    ))
                    for body_schema in all_body_schemas
                ),
                "all_raw_body_count": len(all_raw_bodies),
                "all_raw_body_affordance_count": sum(
                    len(agent.inner.neighbours(
                        raw_body,
                        "has_opaque_embodied_actuator_affordance",
                    ))
                    for raw_body in all_raw_bodies
                ),
                "active_capability_diagnostics": developmental_diagnostics[
                    "active"
                ],
                "developmental_frontier": developmental_diagnostics[
                    "frontier"
                ],
                "developmental_unresolved_prerequisites": (
                    developmental_diagnostics["unresolved_prerequisites"]
                ),
                "developmental_goal": final.get(
                    "developmental_goal",
                    development_final.get(
                        "active_embodied_developmental_goal",
                        "inactive",
                    ),
                ),
                "developmental_stage_transition_count": final.get(
                    "developmental_stage_transition_count", 0
                ),
                "developmental_stages": developmental_stage_rows,
                "active_capability": active_developmental_capability_name,
                "mastery_count": development_final.get(
                    "embodied_developmental_mastery_count", 0
                ),
                "cross_body_warm_start_count": development_final.get(
                    "developmental_cross_body_warm_start_count", 0
                ),
                "exact_body_recall_count": development_final.get(
                    "developmental_exact_body_recall_count", 0
                ),
                "sparse_support_ceiling": development_final.get(
                    "development_sparse_support_ceiling", 0
                ),
                "locomotor_phenotype_count": len(locomotor_phenotype_rows),
                "locomotor_phenotype_family_count": len(
                    locomotor_phenotype_family_rows
                ),
                "locomotor_basin_evidence_window": int(
                    development_final.get("development_evidence_window", 0)
                ),
                "maximum_locomotor_phenotype_occurrence_count": max((
                    int(row.get("occurrence_count", 0))
                    for row in locomotor_phenotype_rows
                ), default=0),
                "locomotor_phenotype_occurrence_histogram": dict(Counter(
                    int(row.get("occurrence_count", 0))
                    for row in locomotor_phenotype_rows
                )),
                "locomotor_phenotype_recurrence_leaders": [
                    {
                        key: row.get(key)
                        for key in (
                            "signature",
                            "occurrence_count",
                            "sum_directed_units",
                            "sum_translation_units",
                            "sum_lateral_units",
                            "sum_directed_consistency",
                            "status",
                        )
                    }
                    for row in sorted(
                        locomotor_phenotype_rows,
                        key=lambda item: (
                            -int(item.get("occurrence_count", 0)),
                            json.dumps(item.get("signature", ())),
                        ),
                    )[:8]
                ],
                "verified_locomotor_basin_count": sum(
                    row.get("status") == "verified_basin"
                    for row in (
                        locomotor_phenotype_rows
                        + locomotor_phenotype_family_rows
                    )
                ),
                "locomotor_pareto_frontier_count": sum(
                    row.get("pareto_candidate_count", 0) > 0
                    and row.get("pareto_dominated", 0) == 0
                    for row in (
                        locomotor_phenotype_rows
                        + locomotor_phenotype_family_rows
                    )
                ),
                "locomotor_phenotypes": locomotor_phenotype_rows,
                "locomotor_phenotype_families": (
                    locomotor_phenotype_family_rows
                ),
                "body_capability_signature": development_final.get(
                    "body_capability_signature", ()
                ),
                "somatomotor_waves": somatomotor_wave_summary,
                "program_trajectory": program_trajectory_report,
                "self_directed_learning_plan": self_learning_plan_summary,
                "retained_experience_count": development_final.get(
                    "retained_developmental_experience_count", 0
                ),
                "caregiver_buffered_experience_count": development_final.get(
                    "caregiver_buffered_experience_count", 0
                ),
                "unbuffered_experience_count": development_final.get(
                    "unbuffered_experience_count", 0
                ),
            }
            if curriculum is not None
            else None
        ),
        "kinematics_study": (
            {
                "installed_terminal_point_count": (
                    kinematics_terminal_point_count
                ),
                "reprobe_count": len(kinematics_reprobe_trace),
                "reprobe_trace": kinematics_reprobe_trace,
                "inverse_reach": kinematic_reach_result,
                **summarize_kinematics_study(
                    agent,
                    standing_reference_z,
                ),
            }
            if curriculum is not None
            and curriculum.get("kinematics_study", False)
            else None
        ),
        "fresh_substrate": True,
        "body_shape_name": body_shape_name,
        "body_shape_relation_count": len(body_shape_signature),
        "motor_library_loaded_shape_count": restored_library[
            "shape_count"
        ],
        "motor_library_loaded_program_count": restored_library[
            "program_count"
        ],
        "motor_library_loaded_program_trajectory_shape_count": (
            restored_library.get("program_trajectory_shape_count", 0)
        ),
        "motor_library_loaded_program_trajectory_transition_count": (
            restored_library.get("program_trajectory_transition_count", 0)
        ),
        "deployment_program_owner_count": len(agent.inner.neighbours(
            episode, "has_embodied_deployment_program_owner"
        )),
        "deployment_program_owner_current_context_count": sum(
            len(agent.inner.neighbours(
                owner, "has_current_embodied_program"
            ))
            for owner in agent.inner.neighbours(
                episode, "has_embodied_deployment_program_owner"
            )
        ),
        "deployment_program_owner_trajectory_count": sum(
            len(agent.inner.neighbours(
                owner, "has_embodied_program_trajectory"
            ))
            for owner in agent.inner.neighbours(
                episode, "has_embodied_deployment_program_owner"
            )
        ),
        "deployment_program_context_diagnostics": {
            "last_verified": [
                deployment_program_context_row(program)
                for program in agent.inner.neighbours(
                    episode, "last_verified_humanoid_motor_program"
                )
            ],
            "retained_sources": [
                deployment_program_context_row(program)
                for owner in deployment_owners
                for transition in agent.inner.neighbours(
                    owner, "has_embodied_program_transition"
                )
                for program in agent.inner.neighbours(
                    transition, "starts_from_embodied_program"
                )
            ],
        },
        "motor_library_loaded_plan_hint_count": restored_library.get(
            "plan_hint_count", 0
        ),
        "motor_library_loaded_plan_hint_stage_count": restored_library.get(
            "plan_hint_stage_count", 0
        ),
        "motor_library_loaded_developmental_capability_count": (
            restored_library.get("developmental_capability_count", 0)
        ),
        "motor_library_loaded_developmental_experience_count": (
            restored_library.get("developmental_experience_count", 0)
        ),
        "motor_library_loaded_developmental_experience_context_count": (
            restored_library.get(
                "developmental_experience_context_count", 0
            )
        ),
        "motor_library_loaded_somatomotor_coupling_count": (
            restored_library.get("somatomotor_coupling_count", 0)
        ),
        "motor_library_loaded_metacognitive_revision_count": (
            restored_library.get("metacognitive_revision_count", 0)
        ),
        "motor_library_loaded_metacognitive_counterexample_count": (
            restored_library.get("metacognitive_counterexample_count", 0)
        ),
        "motor_library_loaded_metacognitive_counterexample_context_count": (
            restored_library.get("metacognitive_counterexample_context_count", 0)
        ),
        "motor_library_loaded_motor_proposal_shape_memory_count": (
            restored_library.get("motor_proposal_shape_memory_count", 0)
        ),
        "motor_library_loaded_motor_proposal_body_shape_memory_count": (
            restored_library.get(
                "motor_proposal_body_shape_memory_count", 0
            )
        ),
        "motor_library_loaded_motor_proposal_counterexample_count": (
            restored_library.get("motor_proposal_counterexample_count", 0)
        ),
        "motor_plan_hint_count": final.get("motor_plan_hint_count", 0.0),
        "motor_plan_basin_seed_count": final.get(
            "motor_plan_basin_seed_count", 0.0
        ),
        "motor_plan_basin_binding_count": final.get(
            "motor_plan_basin_seed_count", 0.0
        ),
        "motor_plan_unique_basin_seed_count": len(agent.inner.neighbours(
            episode, "has_humanoid_motor_program_basin_seed"
        )),
        "motor_plan_search_index_count": len(agent.inner.neighbours(
            episode, "has_humanoid_motor_program_search_index"
        )),
        "motor_plan_consequence_index_count": sum(
            bool(agent.inner.neighbours(
                program, "realizes_embodied_motor_consequence_shape"
            ))
            for program in agent.inner.neighbours(
                episode, "has_humanoid_motor_program"
            )
        ),
        "motor_plan_hint_escalation_count": final.get(
            "motor_plan_hint_escalation_count", 0.0
        ),
        "curriculum_library_loaded_memory_count": restored_library.get(
            "challenge_memory_count",
            0,
        ),
        "residual_regime_library_loaded_memory_count": (
            restored_library.get("residual_regime_memory_count", 0)
        ),
        "recovery_library_loaded_basin_count": restored_library.get(
            "recovery_basin_count", 0
        ),
        "recovery_library_loaded_action_count": restored_library.get(
            "recovery_basin_action_count", 0
        ),
        "warm_start_shape_recognized": final[
            "warm_start_shape_recognized"
        ],
        "warm_start_program_count": final["warm_start_program_count"],
        "late_shape_library_recognition_count": final.get(
            "late_shape_library_recognition_count", 0
        ),
        "partial_trajectory_warm_reuse_count": final.get(
            "partial_trajectory_warm_reuse_count", 0
        ),
        "actuator_count": len(options),
        "non_tonic_actuator_count": probe_count,
        "nominal_response_frames": final["nominal_response_frames"],
        "final_response_frames": final["response_frames"],
        "topology_focused_response_count": final.get(
            "topology_focused_response_count", 0.0
        ),
        "final_compound_response_interval": final[
            "compound_response_interval"
        ],
        "final_decision_count": final["decision_count"],
        "final_last_compound_decision_count": final[
            "last_compound_decision_count"
        ],
        "minimum_response_frames": min(
            (row["response_frames"] for row in trace),
            default=0,
        ),
        "maximum_response_frames": max(
            (row["response_frames"] for row in trace),
            default=0,
        ),
        "simulated_locomotion_seconds": sum(
            row["response_frames"] for row in trace
        ) * configuration.time_step,
        "mean_realized_motor_command_rate_hz": (
            len(trace)
            / (
                max(1, sum(row["response_frames"] for row in trace))
                * configuration.time_step
            )
        ),
        "compound_action_count": compound_action_count,
        "compound_action_fraction": (
            compound_action_count / max(1, len(trace))
        ),
        "combined_recovery_locomotion_collapse_count": len(
            combined_collapse_rows
        ),
        "combined_recovery_locomotion_compound_count": sum(
            row["motor_bundle_width"] > 1
            for row in combined_collapse_rows
        ),
        "combined_recovery_locomotion_maximum_width": max(
            (
                row["motor_bundle_width"]
                for row in combined_collapse_rows
            ),
            default=0,
        ),
        "grounded_combined_recovery_locomotion_program_count": sum(
            row.get("motor_residual_context") == "recovery_locomotion"
            and row.get("status") == "grounded"
            and float(row.get("member_count", 0.0)) > 1.0
            for row in motor_program_rows
        ),
        "maximum_motor_bundle_width": max(
            (row["motor_bundle_width"] for row in trace),
            default=0,
        ),
        "effector_assembly_count": len(effector_assembly_rows),
        "learned_effector_assembly_count": sum(
            float(row.get("experience_count", 0.0)) > 0.0
            for row in effector_assembly_rows
        ),
        "cooperative_effector_assembly_count": sum(
            row.get("status") in {"cooperative", "hard_coupled"}
            for row in effector_assembly_rows
        ),
        "fractionating_effector_assembly_count": sum(
            row.get("status") == "fractionating"
            for row in effector_assembly_rows
        ),
        "effector_assemblies": effector_assembly_rows,
        "takeoff_maximum_motor_bundle_width": max(
            (
                row["motor_bundle_width"]
                for row in trace
                if row["self_takeoff_drive_active_after"] == 1.0
            ),
            default=0,
        ),
        "takeoff_motor_input_energy_joules": sum(
            row["motor_input_energy_joules"]
            for row in trace
            if row["self_takeoff_drive_active_after"] == 1.0
        ),
        "takeoff_motor_recruitment_count": sum(
            row["motor_bundle_width"]
            for row in trace
            if row["self_takeoff_drive_active_after"] == 1.0
        ),
        "calibration_trace": calibration_trace,
        "caregiver_scaffold_trace": caregiver_scaffold_trace,
        "caregiver_support_models": [
            dict(agent.s.node(model)["attrs"])
            for model in agent.inner.neighbours(
                episode, "has_caregiver_support_action_model"
            )
        ],
        "caregiver_scaffold_handoff_ready": agent.s.node(episode)[
            "attrs"
        ].get("caregiver_scaffold_handoff_ready", 0),
        "caregiver_scaffold_mismatch_count": agent.s.node(episode)[
            "attrs"
        ].get("caregiver_scaffold_mismatch_count", 0),
        "caregiver_scaffold_unresolved": agent.s.node(episode)[
            "attrs"
        ].get("caregiver_scaffold_unresolved", 0),
        "caregiver_protective_support_available": agent.s.node(episode)[
            "attrs"
        ].get("caregiver_protective_support_available", 0),
        "caregiver_protected_calibration_action_count": sum(
            int(row.get("caregiver_protective_support_applied", 0))
            for row in calibration_trace
        ),
        "caregiver_scaffold_withdrawn_before_active_attempt": agent.s.node(
            episode
        )["attrs"].get("caregiver_scaffold_withdrawn", 0),
        "caregiver_passive_scaffold_withdrawn_before_active_attempt": (
            agent.s.node(episode)["attrs"].get(
                "caregiver_passive_scaffold_withdrawn", 0
            )
        ),
        "somatomotor_passive_body_models": [
            dict(agent.s.node(model)["attrs"])
            for field in agent.inner.neighbours(
                episode, "has_somatomotor_wave_field"
            )
            for cell in agent.inner.neighbours(
                field, "has_somatomotor_wave_cell"
            )
            for model in agent.inner.neighbours(
                cell, "has_somatomotor_passive_body_model"
            )
        ],
        "synergy_calibration_trace": synergy_trace,
        "maximum_synergy_probe_bundle_width": max(
            1 + (
                row["selected_token"]
                != row["selected_secondary_token"]
            )
            for row in synergy_trace
        ),
        "synergy_model_count": len(synergy_rows),
        "synergy_probe_count": sum(
            float(row.get("probed", 0.0)) > 0.5
            for row in synergy_rows
        ),
        "approved_synergy_count": sum(
            float(row.get("approved", 0.0)) > 0.5
            for row in synergy_rows
        ),
        "rejected_synergy_count": sum(
            float(row.get("rejected", 0.0)) > 0.5
            for row in synergy_rows
        ),
        "synergy_models": [
            row
            for row in synergy_rows
            if float(row.get("probed", 0.0)) > 0.5
        ],
        "synthesized_motor_program_count": len(motor_program_rows),
        "grounded_motor_program_count": sum(
            row.get("status") == "grounded"
            for row in motor_program_rows
        ),
        "consolidated_duplicate_program_count": sum(
            row.get("status") == "consolidated_duplicate"
            for row in motor_program_rows
        ),
        "motor_memory_consolidation_count": sum(
            float(row.get("consolidation_count", 0.0))
            for row in motor_program_rows
        ),
        "maximum_synthesized_motor_program_width": max(
            (len(row["motor_tokens"]) for row in motor_program_rows),
            default=0,
        ),
        "motor_memory_recall_count": final["motor_memory_recall_count"],
        "warm_start_memory_recall_count": final.get(
            "warm_start_memory_recall_count",
            0.0,
        ),
        "motor_memory_structural_reuse_count": final[
            "motor_memory_structural_reuse_count"
        ],
        "motor_sequence_recall_count": final[
            "motor_sequence_recall_count"
        ],
        "motor_preparation_count": final["motor_preparation_count"],
        "motor_preparation_release_count": final[
            "motor_preparation_release_count"
        ],
        "output_null_motor_preparation_count": sum(
            row.get("status") == "output_null"
            for row in motor_preparation_rows
        ),
        "output_potent_motor_preparation_count": sum(
            row.get("status") == "output_potent"
            for row in motor_preparation_rows
        ),
        "motor_preparations": motor_preparation_rows,
        "learned_motor_transition_count": len(motor_transition_rows),
        "reusable_motor_transition_count": sum(
            float(row.get("memory_eligible", 0.0)) > 0.5
            for row in motor_transition_rows
        ),
        "maximum_motor_transition_experience_count": max(
            (
                float(row.get("experience_count", 0.0))
                for row in motor_transition_rows
            ),
            default=0.0,
        ),
        "minimum_learned_motor_transition_frames": min(
            (
                float(row.get("response_frames", 0.0))
                for row in motor_transition_rows
            ),
            default=0.0,
        ),
        "maximum_learned_motor_transition_frames": max(
            (
                float(row.get("response_frames", 0.0))
                for row in motor_transition_rows
            ),
            default=0.0,
        ),
        "motor_transitions": motor_transition_rows,
        "reusable_motor_memory_count": sum(
            float(row.get("memory_eligible", 0.0)) > 0.5
            for row in motor_program_rows
        ),
        "maximum_motor_memory_experience_count": max(
            (
                float(row.get("experience_count", 0.0))
                for row in motor_program_rows
            ),
            default=0.0,
        ),
        "maximum_motor_memory_uncertainty": max(
            (
                float(row.get("mean_prediction_error_energy", 0.0))
                / max(1.0, float(row.get("experience_count", 0.0)))
                for row in motor_program_rows
                if float(row.get("memory_eligible", 0.0)) > 0.5
            ),
            default=0.0,
        ),
        "motor_programs": motor_program_rows,
        "models": models,
        "phase_models_before_walk": phase_models_before_walk,
        "phase_models_after_adaptation": phase_models_after_adaptation,
        "phase_models_after_walk": phase_models_after_walk,
        "maximum_manifold_refinement_exploration_value": agent.s.node(
            episode
        )["attrs"].get(
            "maximum_manifold_refinement_exploration_value", 0.0
        ),
        "manifold_refinement_exploration_valuation_count": agent.s.node(
            episode
        )["attrs"].get(
            "manifold_refinement_exploration_valuation_count", 0
        ),
        "adaptation_actions": warmup_actions,
        "familiarization_complete": phase_adaptation_complete,
        "adaptation_first_fall_action": warmup_first_fall_action,
        "adaptation_learning_events": warmup_learning_events,
        "adaptation_last_learning_action": warmup_last_learning_action,
        "deployment_learning_events": deployment_learning_events,
        "deployment_prediction_confirmations": (
            deployment_prediction_confirmations
        ),
        "deployment_prediction_invalidations": (
            deployment_prediction_invalidations
        ),
        "deployment_prediction_regrounds": deployment_prediction_regrounds,
        "learned_gait_envelope": {
            "tilt": final["learned_gait_tilt_envelope"],
            "mean_tilt": final["learned_gait_mean_tilt"],
            "absolute_vx": final["learned_gait_vx_envelope"],
            "absolute_vy": final["learned_gait_vy_envelope"],
            "horizontal_prediction_error": final[
                "learned_gait_prediction_error_envelope"
            ],
        },
        "gait_surprise_confirmation_receipts": final_policy[
            "gait_surprise_confirmation_receipts"
        ],
        "latest_gait_prediction_error": final[
            "latest_gait_prediction_error"
        ],
        "recovery_mode_entries": final["recovery_mode_entries"],
        "recovery_mode_exits": final["recovery_mode_exits"],
        "recovery_action_count": final["recovery_action_count"],
        "recovery_mode_at_end": final["recovery_mode"],
        "situated_trajectory_context_active_at_end": final.get(
            "situated_locomotion_context_active", 0
        ),
        "motor_fixation_count": final.get("motor_fixation_count", 0.0),
        "motor_configuration_transition_count": final.get(
            "motor_configuration_transition_count",
            0.0,
        ),
        "motor_efference_copy_count": final.get(
            "motor_efference_copy_count",
            0.0,
        ),
        "motor_efference_confirmation_count": final.get(
            "motor_efference_confirmation_count",
            0.0,
        ),
        "get_up_attempt_count": final["get_up_attempt_count"],
        "get_up_success_count": final["get_up_success_count"],
        "get_up_reset_count": final["get_up_reset_count"],
        "recovery_basin_count": final.get("recovery_basin_count", 0.0),
        "recovery_basin_transition_count": final.get(
            "recovery_basin_transition_count", 0.0
        ),
        "recovery_basin_action_count": final.get(
            "recovery_basin_action_count", 0.0
        ),
        "recovery_composition_count": final.get(
            "recovery_composition_count", 0.0
        ),
        "recovery_warm_start_count": final.get(
            "recovery_warm_start_count", 0.0
        ),
        "recovery_path_recall_count": final.get(
            "recovery_path_recall_count", 0.0
        ),
        "recovery_path_hint_count": final.get(
            "recovery_path_hint_count", 0.0
        ),
        "recovery_reanchor_count": final.get(
            "recovery_reanchor_count", 0.0
        ),
        "recovery_program_count": final.get(
            "recovery_program_count", 0.0
        ),
        "recovery_program_repeat_count": final.get(
            "recovery_program_repeat_count", 0.0
        ),
        "recovery_program_termination_count": final.get(
            "recovery_program_termination_count", 0.0
        ),
        "recovery_basins": recovery_basin_rows,
        "body_reset_records": body_reset_records,
        "get_up_models": get_up_model_rows,
        "standing_reference_z": standing_reference_z,
        "pre_locomotion_state": {
            "position": list(pre_locomotion["base_position"]),
            "orientation": list(
                pre_locomotion["base_orientation_xyzw"]
            ),
        },
        "perturbation": (
            {
                **perturbation,
                "onset_action": perturbation_action,
                "resolved_world_frame_force_newtons": (
                    resolved_perturbation_force
                ),
            }
            if perturbation is not None
            else None
        ),
        "directed_progress": directed_progress,
        "lifetime_completed_progress_graph_assessment": final[
            "lifetime_completed_progress"
        ],
        "maximum_directed_progress_graph_assessment": final[
            "maximum_directed_progress"
        ],
        "directed_progress_graph_assessment": graph_lifetime_progress,
        "locomotor_path_length_graph_assessment": locomotor_path_length,
        "gait_path_efficiency": gait_path_efficiency,
        "forward_reversal_count_graph_assessment": (
            locomotor_forward_reversals
        ),
        "forward_reversal_fraction": forward_reversal_fraction,
        "locomotor_cycle_count_graph_assessment": final[
            "locomotor_cycle_count"
        ],
        "motor_input_energy_joules_graph_assessment": final.get(
            "motor_input_energy_joules",
            0.0,
        ),
        "motor_input_energy_joules_trace_evaluation_total": (
            trace_input_energy_joules
        ),
        "motor_input_energy_joules_trace_current_window": (
            current_window_trace_input_energy_joules
        ),
        "motor_energetic_window_seq_graph_assessment": (
            final_energetic_window_seq
        ),
        "motor_net_energy_joules_graph_assessment": final.get(
            "motor_net_energy_joules",
            0.0,
        ),
        "motor_peak_power_watts_graph_assessment": final.get(
            "motor_peak_power_watts",
            0.0,
        ),
        "motor_cost_of_transport_graph_assessment": final.get(
            "motor_cost_of_transport",
            0.0,
        ),
        "motor_transport_economy_graph_assessment": final.get(
            "motor_transport_economy",
            0.0,
        ),
        "lateral_offset": lateral_offset,
        "lateral_offset_graph_assessment": final["lateral_offset"],
        "maximum_lateral_excursion": maximum_lateral_excursion,
        "maximum_lateral_excursion_graph_assessment": final[
            "maximum_lateral_excursion"
        ],
        "minimum_height": minimum_height,
        "minimum_height_graph_assessment": final[
            "walking_minimum_height"
        ],
        "height_floor": height_floor,
        "peak_tilt": peak_tilt,
        "peak_tilt_graph_assessment": final["walking_peak_tilt"],
        "first_fall_action": first_fall_action,
        "upright_at_end_graph_assessment": final["upright"],
        "support_alternations": support_alternations,
        "support_alternations_graph_assessment": final[
            "support_alternations"
        ],
        "aerial_samples": support_patterns["aerial"],
        "aerial_samples_per_locomotor_cycle": (
            support_patterns["aerial"]
            / max(1.0, float(final["locomotor_cycle_count"]))
        ),
        "aerial_samples_graph_assessment": final["aerial_samples"],
        "double_support_samples_graph_assessment": final[
            "double_support_samples"
        ],
        "support_topology_samples_graph_assessment": final[
            "support_topology_samples"
        ],
        "support_pattern_counts": dict(support_patterns),
        "touchdown_count": len(touchdown_advances),
        "advancing_touchdown_count": sum(
            advance > 0.0 for advance in touchdown_advances
        ),
        "mean_directed_touchdown_advance": (
            sum(touchdown_advances) / len(touchdown_advances)
            if touchdown_advances
            else 0.0
        ),
        "touchdown_advances": touchdown_advances,
        "locomotion_action_diversity": len({
            row["selected_token"] for row in trace
        }),
        "opaque_actuator_usage_counts": dict(Counter(
            token
            for row in trace
            for token in row["motor_tokens"]
        )),
        "final_position": list(observation["base_position"]),
        "trace": trace,
    }
    if "benchmark_reward" in observation:
        result["benchmark"] = {
            "simulator": observation["simulator"],
            "asset": observation["asset"],
            "revision": observation["benchmark_revision"],
            "final_reward": observation["benchmark_reward"],
            "final_reward_info": observation["benchmark_reward_info"],
            "terminated": observation["benchmark_terminated"],
    }
    if motor_library_out is not None:
        _request_motor_library_consolidation(agent, episode)
        snapshot = _motor_library_snapshot(agent)
        motor_library_out.parent.mkdir(parents=True, exist_ok=True)
        motor_library_out.write_text(
            json.dumps(snapshot, indent=2) + "\n",
            encoding="utf-8",
        )
        result["motor_library_saved_shape_count"] = len(
            snapshot["body_shapes"]
        )
        result["motor_library_saved_program_count"] = sum(
            len(shape["programs"])
            for shape in snapshot["body_shapes"]
        )
        result["motor_library_saved_plan_hint_count"] = len(
            snapshot.get("plan_hints", ())
        )
        result["motor_library_saved_plan_hint_stage_count"] = sum(
            len(hint.get("stages", ()))
            for hint in snapshot.get("plan_hints", ())
        )
        result["motor_library_saved_developmental_capability_count"] = len(
            snapshot.get("developmental_capabilities", ())
        )
        result["motor_library_saved_developmental_experience_count"] = len(
            snapshot.get("developmental_experiences", ())
        )
        result[
            "motor_library_saved_developmental_experience_context_count"
        ] = sum(
            len(memory.get("contexts", ()))
            for memory in snapshot.get("developmental_experiences", ())
        )
        result["motor_library_saved_somatomotor_coupling_count"] = len(
            snapshot.get("somatomotor_couplings", ())
        )
        result["motor_library_saved_metacognitive_revision_count"] = len(
            snapshot.get("metacognitive_learning_revisions", ())
        )
        result["motor_library_saved_metacognitive_counterexample_count"] = len(
            snapshot.get("metacognitive_learning_counterexamples", ())
        )
        result[
            "motor_library_saved_metacognitive_counterexample_context_count"
        ] = sum(
            len(memory.get("mastery_context", ()))
            for memory in snapshot.get(
                "metacognitive_learning_counterexamples", ()
            )
        )
        result["motor_library_saved_motor_proposal_shape_memory_count"] = len(
            snapshot.get("motor_proposal_shape_memories", ())
        )
        result[
            "motor_library_saved_motor_proposal_body_shape_memory_count"
        ] = sum(
            len(memory.get("body_shapes", ()))
            for memory in snapshot.get("motor_proposal_shape_memories", ())
        )
        result["motor_library_saved_motor_proposal_counterexample_count"] = len(
            snapshot.get("motor_proposal_counterexamples", ())
        )
        result["curriculum_library_saved_memory_count"] = sum(
            len(shape.get("coordination_challenges", ()))
            for shape in snapshot["body_shapes"]
        )
        result["residual_regime_library_saved_memory_count"] = sum(
            len(shape.get("residual_regimes", ()))
            for shape in snapshot["body_shapes"]
        )
        result["recovery_library_saved_basin_count"] = sum(
            len(shape.get("recovery_basins", ()))
            for shape in snapshot["body_shapes"]
        )
        result["recovery_library_saved_action_count"] = sum(
            len(basin.get("actions", ()))
            for shape in snapshot["body_shapes"]
            for basin in shape.get("recovery_basins", ())
        )
    return result


def _run_arm_process(
    protocol: dict[str, Any],
    mode: str,
    motor_library: dict[str, Any] | None,
    motor_library_out: Path | None,
) -> tuple[str, dict[str, Any]]:
    """Run one causally independent experiment arm in its own process.

    A process, rather than a Python thread, gives PyBullet and the Rust graph
    an independent world and removes the GIL from the comparison.  The graph
    inside an arm remains an ordered sensor--collapse--action trajectory; only
    whole worlds that cannot observe one another are concurrent.
    """
    return (
        mode,
        _run_arm(
            protocol,
            mode,
            motor_library=motor_library,
            motor_library_out=motor_library_out,
        ),
    )


def _run_independent_arms(
    protocol: dict[str, Any],
    modes: list[str],
    *,
    motor_library: dict[str, Any] | None,
    motor_library_path: Path | None,
    observer: Callable[[Any, dict[str, Any]], None] | None = None,
) -> dict[str, dict[str, Any]]:
    """Evaluate independent worlds concurrently, returning authored order."""
    if len(modes) == 1:
        mode = modes[0]
        return {
            mode: _run_arm(
                protocol,
                mode,
                motor_library=motor_library,
                motor_library_out=(
                    motor_library_path if mode == "directed_walk" else None
                ),
                observer=observer,
            )
        }

    # ``spawn`` avoids inheriting a live PyBullet client or Rust runtime from
    # the caller.  Worker count is body-of-experiment shape, not a tuned
    # constant: one worker for every declared independent arm.
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=len(modes),
        mp_context=context,
    ) as executor:
        futures = {
            mode: executor.submit(
                _run_arm_process,
                protocol,
                mode,
                motor_library,
                motor_library_path if mode == "directed_walk" else None,
            )
            for mode in modes
        }
        completed = {mode: futures[mode].result()[1] for mode in modes}
    return completed


def run_experiment(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    motor_library_path: Path | None = None,
    observer: Callable[[Any, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    motor_library = (
        json.loads(motor_library_path.read_text(encoding="utf-8"))
        if motor_library_path is not None and motor_library_path.exists()
        else None
    )
    modes = protocol["locomotion"]["modes"]
    runs = _run_independent_arms(
        protocol,
        modes,
        motor_library=motor_library,
        motor_library_path=motor_library_path,
        observer=observer,
    )
    walking = runs["directed_walk"]
    tonic = runs.get("tonic_posture_control")
    calibration_identical = (
        walking["calibration_trace"] == tonic["calibration_trace"]
        and walking["pre_locomotion_state"] == tonic["pre_locomotion_state"]
        if tonic is not None
        else None
    )
    evaluation = protocol["evaluation"]
    evaluation_profile = {
        "upright": walking["first_fall_action"] is None,
        "directed_progress": (
            walking["directed_progress"]
            >= float(evaluation["minimum_directed_progress_metres"])
        ),
        "support_alternation": (
            walking["support_alternations"]
            >= int(evaluation["minimum_support_alternations"])
        ),
        "bounded_aerial_occupancy": (
            walking["aerial_samples_per_locomotor_cycle"]
            <= float(evaluation["maximum_aerial_samples_per_locomotor_cycle"])
        ),
        "bounded_lateral_drift": (
            abs(walking["lateral_offset"])
            <= float(evaluation["maximum_final_lateral_drift_metres"])
        ),
    }
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "simulator": protocol["simulator"],
        "asset": HUMANOID_ASSET,
        "policy_owner": "rust_graph",
        "execution": {
            "independent_worlds_parallel": len(modes) > 1,
            "worker_count": len(modes),
            "within_world_trajectory_ordered": True,
        },
        "joint_count": walking["non_tonic_actuator_count"] // 2,
        "opaque_actuator_count": walking["actuator_count"],
        "pre_locomotion_trajectories_identical": calibration_identical,
        "locomotion": protocol["locomotion"],
        "walking": walking,
        "tonic_control": tonic,
        "evaluation_profile": {
            "scalarized": False,
            "dimensions": evaluation_profile,
        },
        "paired_effect": {
            "legacy_scalarized_compatibility_view": True,
            "directed_progress_advantage": (
                walking["directed_progress"] - tonic["directed_progress"]
                if tonic is not None
                else None
            ),
            "walking_passed": (
                all(evaluation_profile.values())
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--motor-library",
        type=Path,
        help=(
            "load graph-minted motor priors from this JSON library and "
            "write the updated directed-walk library back to it"
        ),
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_experiment(
        args.protocol,
        motor_library_path=args.motor_library,
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
