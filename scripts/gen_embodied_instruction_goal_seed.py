#!/usr/bin/env python3
"""Generate the receipt-evidenced natural-language-to-humanoid Goal bridge.

The bridge is deliberately narrow.  A locally verified instruction may propose
an output-null generic Goal tree around the currently situated embodied
capability.  The verified imperative authorises the mission, but never an
actuator command; the existing developmental plan remains the sole route to
motor output.  A later causally closed receipt confirms competence rather than
retroactively authorising learning.  Teacher evidence (including LLM evidence)
is therefore never an execution authority.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Exists(source, var, predicate):
    return {"type": "Exists", "source": source, "var_name": var,
            "predicate": predicate}
def Neighbours(name, edge):
    return {"type": "Neighbours", "node": V(name), "edge_type": edge,
            "any_type": False}
def T(term): return {"__term__": term}
def Count(source): return {"type": "Count", "source": source}
def P0(name, key): return {"type": "Plus", "items": [A(name, key), L(0)]}
def Text(*parts): return {"__term__": {"type": "StringConcat", "parts": list(parts)}}


def production(name, src, edge, tgt):
    return {
        "provenance": f"embodied_instruction_goal:{name}",
        "src": {"type": src, "var": "src"},
        "edge_type": edge,
        "tgt": {"type": tgt, "var": "tgt"},
    }


def no_proposal_for(interpretation):
    return Not(Exists(
        {"type": "NodesOfType", "node_type": "EmbodiedInstructionGoalProposal"},
        "known_proposal",
        Exists(Neighbours("known_proposal", "derives_from_interpretation"),
               "known_interpretation", Eq(V("known_interpretation"), V(interpretation))),
    ))


def proposal_rule():
    return {
        "name": "eig_propose_order_n_humanoid_goal_from_locally_verified_instruction",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A locally verified imperative authorises an output-null "
                   "mission, never a motor command. The developmental plan "
                   "selects every actual capability and action.",
        "match": [
            ["agent", "holds_interpretation", "interpretation"],
            ["interpretation", "interprets", "message"],
            ["interpretation", "has_understanding_check", "check"],
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "capability"],
        ],
        "where": And(
            Eq(A("interpretation", "status"), L("verified")),
            Eq(A("check", "status"), L("verified")),
            # This is the authority boundary: replayed teacher evidence may
            # help understanding, but it cannot alone propose bodily action.
            Eq(P0("interpretation", "local_grounded"), L(1)),
            Or(
                Exists(Neighbours("episode", "grounded_in_embodied_simulator_connection"),
                       "connection", Eq(P0("connection", "current_attachment"), L(1))),
                # Isolated graph-only unit fixtures have no attachment
                # boundary. Real retained bodies always do, and must be
                # scoped by current_attachment.
                Eq(Count(Neighbours("agent", "has_embodied_simulator_connection")), L(0)),
            ),
            Or(
                And(Eq(A("capability", "status"), L("active")),
                    Eq(A("step", "status"), L("active"))),
                And(Eq(A("capability", "status"), L("available")),
                    Eq(A("step", "status"), L("ready")),
                    Not(Exists(Neighbours("episode", "has_active_embodied_developmental_capability"),
                               "active_capability", L(True))),
                    Not(Exists(Neighbours("plan", "has_selected_learning_plan_step"),
                               "active_step", L(True))),
                    Not(Exists(Neighbours("plan", "has_learning_plan_step"), "lower_step",
                               And(Eq(A("lower_step", "status"), L("ready")),
                                   Lt(A("lower_step", "ordinal"), A("step", "ordinal"))))),
                ),
                # A verified top-down mission may reopen the exact held
                # developmental frontier after a metacognitive check-in has
                # suspended it.  It does not invent a new program or bypass
                # the process: the companion lease rule below reauthorises
                # the same graph-owned supervisor.
                And(Eq(A("capability", "status"), L("meta_suspended")),
                    Eq(A("step", "status"), L("meta_suspended")),
                    Not(Exists(Neighbours("episode", "has_active_embodied_developmental_capability"),
                               "active_capability", L(True))),
                    Not(Exists(Neighbours("plan", "has_selected_learning_plan_step"),
                               "active_step", L(True))),
                    Not(Exists(Neighbours("plan", "has_learning_plan_step"), "ready_step",
                               And(Eq(A("ready_step", "status"), L("ready")),
                                   Exists(Neighbours("ready_step", "plans_learning_capability"),
                                          "ready_capability",
                                          Eq(A("ready_capability", "status"), L("available")))))),
                    Not(Exists(Neighbours("plan", "has_learning_plan_step"), "lower_step",
                               And(Eq(A("lower_step", "status"), L("meta_suspended")),
                                   Lt(A("lower_step", "ordinal"), A("step", "ordinal"))))),
                ),
            ),
            no_proposal_for("interpretation"),
        ),
        "effects": [
            ["add_node", "proposal", "EmbodiedInstructionGoalProposal", {
                "status": "accepted", "order_n": 2,
                "predicate": T(A("interpretation", "predicate")),
                "content": T(A("interpretation", "content")),
                "integer_native": 1, "output_authority": 0,
                "confirmation_required": 1,
                # Immutable causal frontier: only a subsequently minted
                # external request can become this mission's evidence.
                "baseline_trial_seq": T(P0("session", "trial_seq")),
            }],
            ["add_node", "root", "Goal", {
                "kind": "humanoid_embodied_instruction",
                "status": "active", "order_n": 2,
                "predicate": T(A("interpretation", "predicate")),
                "content": T(A("interpretation", "content")),
                "progress_units": 0, "resolved_units": 0,
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "enact", "Goal", {
                "kind": "enact_embodied_capability", "status": "active",
                "order_n": 1, "progress_units": 0, "resolved_units": 0,
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "verify", "Goal", {
                "kind": "verify_embodied_receipt", "status": "active",
                "order_n": 1, "progress_units": 0, "resolved_units": 0,
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "agent", "has_embodied_instruction_goal_proposal", "proposal"],
            ["add_edge", "proposal", "derives_from_interpretation", "interpretation"],
            ["add_edge", "proposal", "proposes_goal", "root"],
            ["add_edge", "proposal", "requires_embodied_capability", "capability"],
            ["add_edge", "episode", "has_active_embodied_developmental_capability", "capability"],
            ["add_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["add_edge", "agent", "has_goal", "root"],
            ["add_edge", "root", "grounds_learning_capability", "capability"],
            ["add_edge", "root", "supervises_embodied_episode", "episode"],
            ["add_edge", "root", "has_subgoal", "enact"],
            ["add_edge", "root", "has_subgoal", "verify"],
            ["add_edge", "enact", "grounds_learning_capability", "capability"],
            ["add_edge", "verify", "grounds_learning_capability", "capability"],
            ["add_node", "reply", "Message", {
                "from": "agent",
                "text": Text(
                    L("I have an attached embodied world and am pursuing "),
                    A("interpretation", "predicate"),
                    L(" through the developmental controller."),
                ),
            }],
            ["add_edge", "reply", "responds_to", "message"],
            ["add_edge", "agent", "sent", "reply"],
            ["set_attr", "capability", "status", "active"],
            ["set_attr", "step", "status", "active"],
        ],
    }


def abstain_rule():
    """Give a graph-owned explanation when no developmental route is ready.

    This is deliberately a proposal with an explicit ``abstained`` state rather
    than a host fallback.  It records that the language was understood while
    refusing to invent a motor authority.
    """
    return {
        "name": "eig_abstain_when_no_ready_embodied_developmental_capability_exists",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A verified instruction without an active or ready graph-selected developmental capability is understood but not enacted.",
        "match": [
            ["agent", "holds_interpretation", "interpretation"],
            ["interpretation", "interprets", "message"],
            ["interpretation", "has_understanding_check", "check"],
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
        ],
        "where": And(
            Eq(A("interpretation", "status"), L("verified")),
            Eq(A("check", "status"), L("verified")),
            Eq(P0("interpretation", "local_grounded"), L(1)),
            Not(Exists(Neighbours("episode", "has_active_embodied_developmental_capability"),
                       "active_capability", L(True))),
            Not(Exists(Neighbours("plan", "has_selected_learning_plan_step"),
                       "active_step", L(True))),
            Not(Exists(Neighbours("plan", "has_learning_plan_step"), "ready_step",
                       And(Eq(A("ready_step", "status"), L("ready")),
                           Exists(Neighbours("ready_step", "plans_learning_capability"),
                                  "ready_capability",
                                  Eq(A("ready_capability", "status"), L("available")))))),
            Not(Exists(Neighbours("plan", "has_learning_plan_step"), "suspended_step",
                       And(Eq(A("suspended_step", "status"), L("meta_suspended")),
                           Exists(Neighbours("suspended_step", "plans_learning_capability"),
                                  "suspended_capability",
                                  Eq(A("suspended_capability", "status"), L("meta_suspended")))))),
            no_proposal_for("interpretation"),
        ),
        "effects": [
            ["add_node", "proposal", "EmbodiedInstructionGoalProposal", {
                "status": "abstained", "order_n": 2,
                "predicate": T(A("interpretation", "predicate")),
                "content": T(A("interpretation", "content")),
                "integer_native": 1, "output_authority": 0,
                "abstention_reason": "no_ready_embodied_developmental_capability",
            }],
            ["add_edge", "agent", "has_embodied_instruction_goal_proposal", "proposal"],
            ["add_edge", "proposal", "derives_from_interpretation", "interpretation"],
            ["add_node", "reply", "Message", {
                "from": "agent",
                "text": Text(L("I understood the embodied instruction, but no ready developmental capability is currently available.")),
            }],
            ["add_edge", "reply", "responds_to", "message"],
            ["add_edge", "agent", "sent", "reply"],
        ],
    }


def open_confirmation_rule():
    return {
        "name": "eig_open_receipt_confirmation_for_proposed_humanoid_goal",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Snapshot integer success evidence at proposal time.  A "
                   "confirmation needs a strictly later observed improvement, "
                   "not a language-model verdict or an already-held success.",
        "match": [
            ["proposal", "proposes_goal", "root"],
            ["proposal", "requires_embodied_capability", "capability"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("accepted")),
            Not(Exists(Neighbours("proposal", "requires_embodied_goal_confirmation"),
                       "known_confirmation", L(True))),
        ),
        "effects": [
            ["add_node", "confirmation", "EmbodiedInstructionGoalConfirmation", {
                "status": "awaiting_competence_receipt",
                # MEASURED PROGRESS, not a met developmental criterion. These
                # were the same attribute until 2026-08-07, when the two writers
                # were found sharing `success_count`: ordinal 0 read 200 against
                # 147 attempts (173 from this notion, 27 from the criterion) and
                # its MASTERY was declared off the inflated figure.
                "baseline_positive_progress_units": T(P0("capability", "positive_progress_count")),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "proposal", "requires_embodied_goal_confirmation", "confirmation"],
            ["add_edge", "confirmation", "confirms_goal", "root"],
            ["add_edge", "confirmation", "confirms_capability", "capability"],
        ],
    }


def confirm_from_receipt_rule():
    return {
        "name": "eig_confirm_goal_only_from_later_closed_embodied_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The confirming datum is the first positive causally "
                   "bound developmental receipt plus a new capability success "
                   "unit.  Earlier zero-yield receipts remain inspectable but "
                   "cannot consume confirmation.  No text, "
                   "teacher evidence, direct actuator command, or float enters "
                   "this transition.",
        "match": [
            ["proposal", "proposes_goal", "root"],
            ["proposal", "requires_embodied_goal_confirmation", "confirmation"],
            ["confirmation", "confirms_capability", "capability"],
            ["proposal", "has_embodied_mission_trial_request", "request"],
            ["request", "has_embodied_learning_trial_receipt", "receipt"],
            ["confirmation", "has_mission_bound_embodied_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("accepted")),
            Eq(A("confirmation", "status"), L("awaiting_competence_receipt")),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("receipt", "success_delta_units"), L(0)),
            Gt(P0("capability", "positive_progress_count"),
               A("confirmation", "baseline_positive_progress_units")),
            Not(Exists(Neighbours("confirmation", "grounded_in_embodied_receipt"),
                       "known_receipt", L(True))),
        ),
        "effects": [
            ["set_attr", "confirmation", "status", "confirmed"],
            ["set_attr", "proposal", "status", "confirmed"],
            ["set_attr", "root", "progress_units", 1],
            ["set_attr", "root", "resolved_units", 1],
            ["add_edge", "confirmation", "grounded_in_embodied_receipt", "receipt"],
        ],
    }


def supervise_developmental_goal_rule():
    return {
        "name": "eig_mission_supervises_selected_developmental_goal",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Natural language sets the mission boundary. The generic "
                   "developmental plan still chooses the current capability; "
                   "the mission only adopts that graph-selected goal as an "
                   "order-N subgoal.",
        "match": [
            ["root", "supervises_embodied_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "pursues_goal", "developmental_goal"],
        ],
        "where": And(
            Eq(A("root", "status"), L("active")),
            Eq(A("developmental_goal", "status"), L("active")),
            Not(Exists(Neighbours("root", "has_subgoal"), "known_goal",
                       Eq(V("known_goal"), V("developmental_goal")))),
        ),
        "effects": [
            ["add_edge", "root", "has_subgoal", "developmental_goal"],
        ],
    }


def renew_mission_supervisory_lease_rule():
    """Make a verified order-N mission an explicit supervisor continuation.

    A metacognitive release preserves the selected capability and process for
    later re-evaluation.  A locally grounded embodied mission is such new
    information: it reopens that exact pair and gives the process a fresh
    graph-owned lease.  No host command, new program, or test-authored
    threshold participates.
    """
    return {
        "name": "eig_renew_supervisory_lease_for_verified_embodied_mission",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A verified instruction is top-down evidence that the held embodied frontier is again worth pursuing; it renews the existing process rather than bypassing it.",
        "match": [
            ["proposal", "proposes_goal", "root"],
            ["proposal", "requires_embodied_capability", "capability"],
            ["root", "supervises_embodied_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "capability"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "supervises_learning_plan_step", "step"],
            ["process", "supervises_learning_capability", "capability"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("accepted")),
            Not(Exists(Neighbours("proposal", "has_embodied_mission_lease_renewal"),
                       "known_renewal", L(True))),
        ),
        "effects": [
            ["add_node", "renewal", "EmbodiedMissionLeaseRenewal", {
                "status": "renewed", "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "proposal", "has_embodied_mission_lease_renewal", "renewal"],
            ["add_edge", "renewal", "renews_cognitive_process", "process"],
            ["add_edge", "episode", "has_active_embodied_developmental_capability", "capability"],
            ["add_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["set_attr", "capability", "status", "active"],
            ["set_attr", "step", "status", "active"],
            ["set_attr", "capability", "activation_receipt_seq", T(P0(
                "episode", "latest_development_receipt_seq"
            ))],
            ["set_attr", "process", "status", "monitoring"],
            ["set_attr", "process", "continuation_authority", 1],
            ["set_attr", "process", "lease_generation", T({
                "type": "Plus", "items": [P0("process", "lease_generation"), L(1)]
            })],
            ["set_attr", "process", "last_checkin_epoch", T(P0(
                "policy", "cognitive_epoch"
            ))],
            ["set_attr", "process", "renew_before_epoch", T({
                "type": "Plus", "items": [
                    P0("policy", "cognitive_epoch"),
                    P0("process", "checkin_span_units"),
                ]
            })],
            ["set_attr", "process", "next_checkin_epoch", T({
                "type": "Plus", "items": [
                    P0("policy", "cognitive_epoch"),
                    P0("process", "checkin_span_units"),
                ]
            })],
            ["set_attr", "process", "baseline_effort_units", T(P0(
                "step", "evidence_spent_units"
            ))],
            ["set_attr", "process", "checkin_count", T({
                "type": "Plus", "items": [P0("process", "checkin_count"), L(1)]
            })],
            ["set_attr", "policy", "enabled", 1],
            ["set_attr", "episode", "cognitive_continuation_authority", 1],
            ["set_attr", "episode", "cognitive_checkin_terminal", 0],
        ],
    }


def bind_mission_request_rule():
    """Bind a mission to the *exact* subsequent external request it adopted."""
    return {
        "name": "eig_bind_embodied_mission_to_exact_external_trial_request",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The root mission retains every distinct post-baseline session request pursuing one of its graph-selected developmental subgoals.  This is an ordered causal provenance set, not a one-shot latch: an early unproductive probe must not sever later competent evidence, and unrelated or historical requests remain inadmissible.",
        "match": [
            ["proposal", "proposes_goal", "root"],
            ["root", "supervises_embodied_episode", "episode"],
            ["root", "has_subgoal", "developmental_goal"],
            ["episode", "has_embodied_learning_session", "session"],
            ["session", "has_grounded_external_trial_request", "request"],
            ["request", "pursues_goal", "developmental_goal"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("accepted")),
            Gt(A("request", "attempt_ordinal"),
               A("proposal", "baseline_trial_seq")),
            Not(Exists(Neighbours("proposal", "has_embodied_mission_trial_request"),
                       "known_request", Eq(V("known_request"), V("request")))),
        ),
        "effects": [
            ["add_edge", "proposal", "has_embodied_mission_trial_request", "request"],
            ["add_edge", "request", "for_embodied_instruction_goal", "root"],
        ],
    }


def bind_mission_receipt_rule():
    """Carry exact request provenance through its causal receipt."""
    return {
        "name": "eig_bind_embodied_mission_to_exact_causal_trial_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Every exact receipt minted by a mission-bound request remains available as causal provenance.  Confirmation later consumes the first positive receipt, rather than treating an early zero-yield probe as terminal evidence.",
        "match": [
            ["proposal", "requires_embodied_goal_confirmation", "confirmation"],
            ["proposal", "has_embodied_mission_trial_request", "request"],
            ["request", "has_embodied_learning_trial_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Not(Exists(Neighbours("confirmation", "has_mission_bound_embodied_receipt"),
                       "known_receipt", Eq(V("known_receipt"), V("receipt")))),
        ),
        "effects": [
            ["add_edge", "confirmation", "has_mission_bound_embodied_receipt", "receipt"],
            ["add_edge", "receipt", "grounds_embodied_instruction_goal", "proposal"],
        ],
    }


def manifest():
    return {
        "id": "embodied_instruction_goal",
        "version": "1.0.0",
        "depends_on": [
            "instruction_understanding", "cognitive_supervision",
            "humanoid_developmental_curriculum",
        ],
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "description": "Graph-native bridge from a locally verified natural-language "
                       "InstructionInterpretation to an output-null active generic "
                       "order-N humanoid mission. The developmental plan remains the "
                       "only motor authority. Competence confirmation requires a later "
                       "causally closed embodied receipt and new integer capability "
                       "success evidence; LLM and other teacher evidence are never "
                       "authoritative for bodily action.",
        "nodes": [],
        "edges": [],
        "productions": [
            production("agent_proposal", "Agent", "has_embodied_instruction_goal_proposal", "EmbodiedInstructionGoalProposal"),
            production("proposal_interpretation", "EmbodiedInstructionGoalProposal", "derives_from_interpretation", "InstructionInterpretation"),
            production("proposal_goal", "EmbodiedInstructionGoalProposal", "proposes_goal", "Goal"),
            production("proposal_capability", "EmbodiedInstructionGoalProposal", "requires_embodied_capability", "EmbodiedSituatedDevelopmentalCapability"),
            production("proposal_confirmation", "EmbodiedInstructionGoalProposal", "requires_embodied_goal_confirmation", "EmbodiedInstructionGoalConfirmation"),
            production("confirmation_goal", "EmbodiedInstructionGoalConfirmation", "confirms_goal", "Goal"),
            production("confirmation_capability", "EmbodiedInstructionGoalConfirmation", "confirms_capability", "EmbodiedSituatedDevelopmentalCapability"),
            production("confirmation_receipt", "EmbodiedInstructionGoalConfirmation", "grounded_in_embodied_receipt", "Node"),
            production("proposal_request", "EmbodiedInstructionGoalProposal", "has_embodied_mission_trial_request", "EmbodiedExternalTrialRequest"),
            production("request_goal", "EmbodiedExternalTrialRequest", "for_embodied_instruction_goal", "Goal"),
            production("confirmation_bound_receipt", "EmbodiedInstructionGoalConfirmation", "has_mission_bound_embodied_receipt", "EmbodiedLearningTrialReceipt"),
            production("receipt_instruction_goal", "EmbodiedLearningTrialReceipt", "grounds_embodied_instruction_goal", "EmbodiedInstructionGoalProposal"),
            production("proposal_lease_renewal", "EmbodiedInstructionGoalProposal", "has_embodied_mission_lease_renewal", "EmbodiedMissionLeaseRenewal"),
            production("goal_subgoal", "Goal", "has_subgoal", "Goal"),
            production("goal_capability", "Goal", "grounds_learning_capability", "EmbodiedSituatedDevelopmentalCapability"),
            production("goal_episode", "Goal", "supervises_embodied_episode", "EmbodiedDevelopmentEpisode"),
            production("agent_goal", "Agent", "has_goal", "Goal"),
        ],
        "rules": [proposal_rule(), abstain_rule(), open_confirmation_rule(),
                  supervise_developmental_goal_rule(), renew_mission_supervisory_lease_rule(), bind_mission_request_rule(),
                  bind_mission_receipt_rule(), confirm_from_receipt_rule()],
    }


if __name__ == "__main__":
    print(json.dumps(manifest(), indent=2) + "\n", end="")
