#!/usr/bin/env python3
"""Generate the graph-native, integer-only embodied learning session.

This is deliberately a coordination seed.  It does not replace the embodied
development DAG, motor synthesis, counterfactual runner, reset selection, or
Pareto faculty.  It gives their already-public graph interfaces one persistent
owner and turns a selected program plus declared affordances into an external
trial request.  A world adapter may only publish the request's evidence.
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
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def N(name, edge): return {"type": "Neighbours", "node": V(name), "edge_type": edge}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var, "predicate": predicate,
}
def Count(source): return {"type": "Count", "source": source}
def Sum(source, var, value): return {
    "type": "Sum", "source": source, "var_name": var, "value": value,
}


def absent(source, var="prior"):
    return Not(Exists(source, var, L(True)))


def no_matching_neighbour(node, edge, var, predicate):
    """A graph-native absence guard over the session's retained history."""
    return Not(Exists(N(node, edge), var, predicate))


def no_active_counterfactual():
    return no_matching_neighbour(
        "session", "has_counterfactual_embodied_trial", "prior_trial",
        {"type": "In", "member": A("prior_trial", "status"),
         "container": L(["counterfactual_running", "counterfactual_done"])},
    )


def no_requested_external_trial():
    return no_matching_neighbour(
        "session", "has_grounded_external_trial_request", "prior_request",
        Eq(A("prior_request", "status"), L("requested")),
    )


def declared(name, key):
    """PRESENT, as opposed to present-and-zero. `Eq(Attr, Lit None)` is true
    only for a MISSING key, which is the one place absent and zero can be told
    apart in this engine."""
    return Not(Eq(A(name, key), L(None)))


def carry_observed_support_topology_rule():
    """SUPPORT TOPOLOGY, DECIDED BY THE GRAPH FROM THE WORLD'S MEASUREMENT.

    Four `development_*` fields in this family are read by the curriculum and
    written by nothing: `development_post_support_count` (156 reads),
    `development_support_topology_changed` (73), `development_support_gain`
    (30), `development_support_extent_gain` (16). All four are answerable from
    ONE measurement -- the set of links in ground contact before and after the
    trial -- which the world already computes and the transducer now publishes.

    `surface_contact_mapping` (ordinal 3) sat at 61 attempts and 0 successes on
    exactly the first of these, the same shape that held stage 0 for thirteen
    hours and stage 1 until its coverage field was written.

    THE TRAP THIS FAMILY IS ESPECIALLY PRONE TO: a body resting on the floor
    has a STABLE support topology, so "changed" is genuinely 0 most of the time
    and that zero is a real measurement. But an ABSENT reading must not report
    "unchanged" -- unobserved and unchanged are different facts. So this rule
    fires ONLY when the evidence declares the topology was observed, and writes
    nothing at all otherwise: the fields stay ABSENT rather than becoming a
    fabricated zero, and every consumer reading them through `+ 0` therefore
    refuses rather than scoring a success it did not observe.
    """
    changed = {"type": "IfThenElse",
               "cond": Not(Eq(A("evidence", "support_contact_links_before"),
                              A("evidence", "support_contact_links_after"))),
               "then": L(1), "other": L(0)}
    # RAW READS, DELIBERATELY. The `where` below already requires both counts
    # to be `declared(...)`, so coalescing them here would add nothing except a
    # second, weaker story about what absence means — and the guard-coalescing
    # lint is right to flag that: a reader that says `+ 0` is claiming absence
    # is survivable, and here it is not, it is impossible.
    after = A("evidence", "support_contact_count_after")
    before = A("evidence", "support_contact_count_before")
    return {
        "name": "els_carry_observed_support_topology_to_causal_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "The world measures WHICH links touch the ground; this rule decides "
            "what that means for the curriculum. Guarded on the evidence's own "
            "observation flag so an unread topology leaves the fields ABSENT "
            "instead of asserting an unchanged one."
        ),
        "match": [
            ["receipt", "grounded_in_external_trial_evidence", "evidence"],
        ],
        "where": And(
            # OBSERVED, not merely zero. Both the flag and the two link sets
            # must be present before any of this can be asserted.
            declared("evidence", "support_contact_observed"),
            declared("evidence", "support_contact_links_before"),
            declared("evidence", "support_contact_links_after"),
            declared("evidence", "support_contact_count_after"),
            declared("evidence", "support_contact_count_before"),
            Not(declared("receipt", "development_support_observed")),
        ),
        "effects": [
            ["set_attr", "receipt", "development_support_observed", 1],
            ["set_attr", "receipt", "development_post_support_count", {"__term__": after}],
            ["set_attr", "receipt", "development_support_topology_changed", {"__term__": changed}],
            ["set_attr", "receipt", "development_support_gain",
             {"__term__": {"type": "Minus", "a": after, "b": before}}],
            ["set_attr", "receipt", "development_support_extent_gain",
             {"__term__": {"type": "IfThenElse", "cond": Gt(after, before),
                           "then": L(1), "other": L(0)}}],
        ],
    }


def session_open_rule():
    return {
        "name": "els_open_persistent_embodied_learning_session",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The world boundary publishes body-schema and world tokens; a rule, not the adapter, decides that they constitute one durable learning session.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_body_schema", "body"],
            ["episode", "has_embodied_learning_world", "world"],
        ],
        "where": absent(N("episode", "has_embodied_learning_session")),
        "effects": [
            ["add_node", "session", "EmbodiedLearningSession", {
                "status": "active", "trial_seq": 0, "evidence_seq": 0,
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "episode", "has_embodied_learning_session", "session"],
            ["add_edge", "session", "has_embodied_body_schema", "body"],
            ["add_edge", "session", "observes_embodied_learning_world", "world"],
        ],
    }


def bind_plan_frontier_goal_rule():
    return {
        "name": "els_bind_active_order_n_goal_plan_and_frontier",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The session follows the developmental seed's selected step and capability frontier; order-N goal structure remains owned by the generic Goal graph.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "pursues_goal", "goal"],
            ["episode", "has_active_embodied_developmental_capability", "frontier"],
        ],
        "where": And(
            Eq(A("goal", "status"), L("active")),
            absent(N("session", "has_active_embodied_goal")),
        ),
        "effects": [
            ["add_edge", "session", "has_learning_plan", "plan"],
            ["add_edge", "session", "has_active_embodied_goal", "goal"],
            ["add_edge", "session", "has_developmental_frontier", "frontier"],
            ["add_edge", "session", "has_selected_learning_plan_step", "step"],
            ["set_attr", "goal", "order_n", {"__term__": {
                "type": "Max", "items": [
                    L(1), Count(N("goal", "has_subgoal")),
                ],
            }}],
        ],
    }


def bind_motor_material_rule():
    return {
        "name": "els_bind_existing_motor_hint_and_program",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Motor priors and programs are produced by their own embodied seeds. The session records the selected pair without interpreting opaque actuator contents.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["episode", "has_embodied_motor_episode", "motor_episode"],
            ["motor_episode", "uses_embodied_motor_prior", "hint"],
            ["motor_episode", "has_embodied_motor_program", "program"],
        ],
        "where": And(
            Eq(A("program", "integer_native"), L(1)),
            absent(N("session", "has_selected_embodied_motor_program")),
        ),
        "effects": [
            ["add_edge", "session", "uses_embodied_motor_hint", "hint"],
            ["add_edge", "session", "has_selected_embodied_motor_program", "program"],
        ],
    }


def counterfactual_trial_rule():
    hypothesis = json.dumps({
        "nodes": [{
            "key": "selection", "type": "EmbodiedCounterfactualSelection",
            "attrs": {"selected": 1, "integer_native": 1,
                      "output_authority": 0},
        }],
        "edges": [{
            "src": "selection", "type": "counterfactually_selects_program",
            "tgt": "__FOCUS__",
        }],
    }, separators=(",", ":"))
    return {
        "name": "els_request_counterfactual_trial_before_external_trial",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The selected program is injected into detached cognition. Existing learned consequence attributes produce a projection there; the result is explicitly non-oracular and requires external validation.",
        "match": [
            ["session", "has_active_embodied_goal", "goal"],
            ["session", "has_selected_embodied_motor_program", "program"],
        ],
        "where": no_active_counterfactual(),
        "effects": [
            ["add_node", "trial", "Experiment", {
                "status": "counterfactual_running",
                "epistemic_scope": "graph_counterfactual",
                "hypothesis": "selected_motor_program_advances_active_goal",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "request", "ImagineRequest", {
                "status": "requested", "kind": "embodied_motor_rehearsal",
                "hypothesis_template": hypothesis,
                "why": "project_selected_motor_program_consequences",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "session", "has_counterfactual_embodied_trial", "trial"],
            ["add_edge", "trial", "pursues_goal", "goal"],
            ["add_edge", "trial", "tests_embodied_motor_program", "program"],
            ["add_edge", "request", "focuses_on_node", "program"],
            ["add_edge", "request", "rehearses_experiment", "trial"],
            ["add_edge", "trial", "has_counterfactual_request", "request"],
        ],
    }


def counterfactual_projection_rule():
    return {
        "name": "els_project_learned_motor_consequences_in_detached_cognition",
        "area": "default_mode",
        "latency_class": "best_effort",
        "comment": "This fires only in the detached graph because the live graph has no EmbodiedCounterfactualSelection. It reads the selected program's learned integer consequence model; it does not fabricate grounded success.",
        "match": [[
            "selection", "counterfactually_selects_program", "program",
        ]],
        "where": absent(N("selection", "has_counterfactual_motor_projection")),
        "effects": [
            ["add_node", "projection", "EmbodiedCounterfactualMotorProjection", {
                "predicted_forward_units": {"__term__": A("program", "predicted_forward_units")},
                "predicted_vertical_units": {"__term__": A("program", "predicted_vertical_units")},
                "predicted_energy_units": {"__term__": A("program", "predicted_energy_units")},
                "predicted_peak_load_units": {"__term__": A("program", "predicted_peak_load_units")},
                "model_experience_units": {"__term__": A("program", "experience_units")},
                "grounded": 0, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "selection", "has_counterfactual_motor_projection", "projection"],
            ["add_edge", "projection", "projects_selected_program", "program"],
        ],
    }


def retain_counterfactual_projection_rule():
    return {
        "name": "els_retain_detached_motor_projection_as_non_oracular_evidence",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The imagination dispatcher only publishes provenance. This graph rule closes the rehearsal while explicitly requiring a grounded external trial.",
        "match": [[
            "trial", "received_counterfactual_imagination", "imagination",
        ]],
        "where": Eq(A("trial", "status"), L("counterfactual_running")),
        "effects": [
            ["add_edge", "trial", "has_counterfactual_evidence", "imagination"],
            ["set_attr", "trial", "status", "counterfactual_done"],
            ["set_attr", "trial", "evidence_kind", "imagined"],
            ["set_attr", "trial", "requires_external_validation", 1],
        ],
    }


def external_trial_request_rule():
    return {
        "name": "els_request_grounded_external_trial_from_declared_affordances",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Only an explicitly published pose affordance and the developmental seed's already-selected reset scenario can authorize a world trial. The adapter merely reads this request.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["session", "observes_embodied_learning_world", "world"],
            ["session", "has_active_embodied_goal", "goal"],
            ["session", "has_selected_embodied_motor_program", "program"],
            ["session", "has_counterfactual_embodied_trial", "counterfactual"],
            ["world", "has_embodied_pose_affordance", "pose"],
            ["episode", "has_active_embodied_reset_request", "reset"],
            ["reset", "selects_embodied_reset_scenario", "scenario"],
        ],
        "where": And(
            Eq(A("pose", "enabled"), L(1)),
            Eq(A("reset", "status"), L("requested")),
            Eq(A("counterfactual", "status"), L("counterfactual_done")),
            # Historical episodes remain available to imagination and memory,
            # but only the mechanically current attachment may mint new
            # physical authority.  A connection-less episode is the explicit
            # legacy/offline test shape and retains its prior contract.
            Or(
                absent(N("episode", "grounded_in_embodied_simulator_connection")),
                Exists(
                    N("episode", "grounded_in_embodied_simulator_connection"),
                    "connection",
                    Eq(A("connection", "current_attachment"), L(1)),
                ),
            ),
            no_requested_external_trial(),
        ),
        "effects": [
            ["add_node", "request", "EmbodiedExternalTrialRequest", {
                "status": "requested", "attempt_ordinal": {"__term__": {
                    "type": "Plus", "items": [A("session", "trial_seq"), L(1)]
                }},
                "grounded": 1, "integer_native": 1, "output_authority": 0,
                "supervision_priority": {"__term__": {
                    "type": "Plus", "items": [A("session", "trial_seq"), L(1)]
                }},
            }],
            ["add_edge", "session", "has_grounded_external_trial_request", "request"],
            ["add_edge", "request", "pursues_goal", "goal"],
            ["add_edge", "request", "enacts_embodied_motor_program", "program"],
            ["add_edge", "request", "uses_embodied_pose_affordance", "pose"],
            ["add_edge", "request", "uses_embodied_reset_scenario", "scenario"],
            ["set_attr", "session", "trial_seq", {"__term__": {
                "type": "Plus", "items": [A("session", "trial_seq"), L(1)]
            }}],
        ],
    }


def project_grounded_vector_evidence_rule():
    return {
        "name": "els_project_full_grounded_displacement_vector_for_active_goal",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The world adapter reports an entire measured displacement vector once. The graph, rather than the adapter or a six-way program clone, projects the integer vector into the current exploratory goal's movement evidence.",
        "match": [
            ["request", "has_grounded_external_trial_evidence", "evidence"],
            ["request", "pursues_goal", "goal"],
        ],
        "where": And(
            Eq(A("evidence", "proprioceptive_configuration_observed"), L(1)),
            absent(N("evidence", "has_embodied_goal_vector_projection")),
        ),
        "effects": [
            ["add_node", "projection", "EmbodiedGoalVectorProjection", {
                "kind": "cartesian_l1_exploration_progress",
                "x_units": {"__term__": A("evidence", "base_displacement_x_units")},
                "y_units": {"__term__": A("evidence", "base_displacement_y_units")},
                "z_units": {"__term__": A("evidence", "base_displacement_z_units")},
                "goal_progress_units": {"__term__": {
                    "type": "Plus", "items": [
                        {"type": "Abs", "arg": A("evidence", "base_displacement_x_units")},
                        {"type": "Abs", "arg": A("evidence", "base_displacement_y_units")},
                        {"type": "Abs", "arg": A("evidence", "base_displacement_z_units")},
                    ],
                }},
                "proprioceptive_configuration_l1_units": {"__term__": Sum(
                    A("evidence", "proprioceptive_configuration_delta_units"),
                    "delta", {"type": "Abs", "arg": V("delta")},
                )},
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "evidence", "has_embodied_goal_vector_projection", "projection"],
            ["add_edge", "projection", "projects_grounded_evidence", "evidence"],
            ["add_edge", "projection", "projects_for_embodied_goal", "goal"],
            ["set_attr", "evidence", "goal_progress_units", {"__term__": {
                "type": "Plus", "items": [
                    {"type": "Abs", "arg": A("evidence", "base_displacement_x_units")},
                    {"type": "Abs", "arg": A("evidence", "base_displacement_y_units")},
                    {"type": "Abs", "arg": A("evidence", "base_displacement_z_units")},
                ],
            }}],
            ["set_attr", "evidence", "proprioceptive_configuration_l1_units", {"__term__": Sum(
                A("evidence", "proprioceptive_configuration_delta_units"),
                "delta", {"type": "Abs", "arg": V("delta")},
            )}],
        ],
    }


def evidence_rule():
    return {
        "name": "els_retain_grounded_external_evidence_and_close_request",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "World evidence is first-class and is never inferred from a counterfactual result. Receipt publication is mechanical I/O; closure is a graph decision.",
        "match": [
            ["session", "has_grounded_external_trial_request", "request"],
            ["request", "has_grounded_external_trial_evidence", "evidence"],
            ["evidence", "has_embodied_goal_vector_projection", "projection"],
        ],
        "where": And(
            Eq(A("request", "status"), L("requested")),
            Eq(A("evidence", "grounded"), L(1)),
        ),
        "effects": [
            ["add_edge", "session", "has_grounded_external_trial_evidence", "evidence"],
            ["set_attr", "request", "status", "evidenced"],
            ["set_attr", "session", "evidence_seq", {"__term__": {
                "type": "Plus", "items": [A("session", "evidence_seq"), L(1)]
            }}],
        ],
    }


def pareto_evidence_rule():
    values = []
    for ordinal, key, sign in (
        (0, "goal_progress_units", 1),
        (1, "energy_cost_units", -1),
        (2, "peak_load_units", -1),
    ):
        value = f"value_{ordinal}"
        term = A("evidence", key)
        if sign < 0:
            term = {"type": "Neg", "arg": term}
        values.extend((
            ["add_node", value, "ParetoValue", {
                "dimension_ordinal": ordinal, "raw_value": {"__term__": A("evidence", key)},
                "signed_value": {"__term__": term}, "verified": 1, "integer_native": 1,
            }],
            ["add_edge", "candidate", "has_pareto_value", value],
        ))
    return {
        "name": "els_publish_grounded_external_evidence_to_pareto_profile",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Three measured integer coordinates remain distinct: goal progress, energy cost, and peak load. General cognitive_pareto decides dominance; no scalar reward is introduced.",
        "match": [
            ["session", "has_learning_plan", "plan"],
            ["plan", "has_learning_decision_profile", "profile"],
            ["session", "has_grounded_external_trial_evidence", "evidence"],
            ["evidence", "has_embodied_goal_vector_projection", "projection"],
        ],
        "where": And(
            Eq(A("profile", "dimension_count"), L(3)),
            absent(N("evidence", "published_as_pareto_candidate")),
        ),
        "effects": [
            ["add_node", "candidate", "ParetoCandidate", {
                "kind": "grounded_embodied_external_trial", "verified": 1,
                "dominated": 0, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "profile", "has_pareto_candidate", "candidate"],
            ["add_edge", "evidence", "published_as_pareto_candidate", "candidate"],
            ["add_edge", "candidate", "grounded_in_external_trial_evidence", "evidence"],
            *values,
        ],
    }


def causal_receipt_and_learning_rule():
    return {
        "name": "els_close_exact_external_trial_as_causal_development_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "Only exact externally grounded evidence with its request, program, pose, reset scenario, and goal provenance closes a developmental receipt. The same receipt updates integer consequence coordinates and experience; it is not a scalar reward.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["session", "has_grounded_external_trial_request", "request"],
            ["request", "has_grounded_external_trial_evidence", "evidence"],
            ["request", "enacts_embodied_motor_program", "program"],
            ["request", "uses_embodied_pose_affordance", "pose"],
            ["request", "uses_embodied_reset_scenario", "scenario"],
            ["request", "pursues_goal", "goal"],
            ["evidence", "evidence_for_embodied_trial_request", "request"],
            ["evidence", "measures_embodied_motor_program", "program"],
            ["evidence", "under_embodied_pose_affordance", "pose"],
            ["evidence", "from_embodied_reset_scenario", "scenario"],
            ["evidence", "measures_goal", "goal"],
            ["evidence", "has_embodied_goal_vector_projection", "projection"],
            ["session", "has_counterfactual_embodied_trial", "counterfactual"],
            ["counterfactual", "tests_embodied_motor_program", "program"],
            ["episode", "has_active_embodied_reset_request", "reset"],
            ["reset", "selects_embodied_reset_scenario", "scenario"],
        ],
        "where": And(
            Eq(A("request", "status"), L("evidenced")),
            Eq(A("evidence", "grounded"), L(1)),
            Eq(A("counterfactual", "status"), L("counterfactual_done")),
            Eq(A("reset", "status"), L("requested")),
            absent(N("request", "has_embodied_learning_trial_receipt")),
        ),
        "effects": [
            ["add_node", "receipt", "EmbodiedLearningTrialReceipt", {
                "status": "closed", "development_receipt_closed": 1,
                "development_receipt_seq": {"__term__": A("session", "evidence_seq")},
                "goal_progress_units": {"__term__": A("evidence", "goal_progress_units")},
                "energy_cost_units": {"__term__": A("evidence", "energy_cost_units")},
                "peak_load_units": {"__term__": A("evidence", "peak_load_units")},
                "success_delta_units": {"__term__": {
                    "type": "IfThenElse", "cond": Gt(A("evidence", "goal_progress_units"), L(0)),
                    "then": L(1), "other": L(0),
                }},
                # THE DEVELOPMENTAL EVIDENCE VOCABULARY.  The curriculum's
                # acquisition criteria read `development_*` OFF THIS RECEIPT,
                # and an attribute that is never written reads as 0 through the
                # `+ 0` null-coalescing idiom every criterion uses — so a
                # missing measurement is indistinguishable from a failed one
                # and no stage can ever complete.  Both values below are
                # derived from measurements the evidence ALREADY carries; this
                # adds no host measurement and makes no host decision.
                #
                # Whether the body's configuration changed is exactly whether
                # the L1 norm of the proprioceptive delta is non-zero.  Base
                # translation alone is not a sufficient movement sensor (a
                # joint can move while the base stays still), which is why the
                # proprioceptive norm rather than `goal_progress_units` is the
                # right witness for a spontaneous configuration change.
                "development_configuration_changed": {"__term__": {
                    "type": "IfThenElse",
                    "cond": Gt({"type": "Plus", "items": [
                        A("evidence", "proprioceptive_configuration_l1_units"), L(0),
                    ]}, L(0)),
                    "then": L(1), "other": L(0),
                }},
                # Read through from the evidence with a 0 default rather than
                # asserted as a constant: this transducer applies no external
                # disturbance during a trial, but a world that DOES observe one
                # can publish it and the receipt will carry it unchanged.
                "development_external_event": {"__term__": {"type": "Plus", "items": [
                    A("evidence", "development_external_event"), L(0),
                ]}},
                "causal_closed": 1, "grounded": 1,
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "consequence", "EmbodiedLearnedConsequence", {
                "forward_units": {"__term__": A("evidence", "goal_progress_units")},
                "energy_units": {"__term__": A("evidence", "energy_cost_units")},
                "peak_load_units": {"__term__": A("evidence", "peak_load_units")},
                "experience_ordinal": {"__term__": {"type": "Plus", "items": [A("program", "experience_units"), L(1)]}},
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "request", "has_embodied_learning_trial_receipt", "receipt"],
            ["add_edge", "session", "has_causal_embodied_learning_receipt", "receipt"],
            ["add_edge", "episode", "has_embodied_development_receipt", "receipt"],
            ["add_edge", "receipt", "grounded_in_external_trial_evidence", "evidence"],
            ["add_edge", "receipt", "caused_by_embodied_trial_request", "request"],
            ["add_edge", "receipt", "caused_by_embodied_motor_program", "program"],
            ["add_edge", "receipt", "caused_under_embodied_pose_affordance", "pose"],
            ["add_edge", "receipt", "caused_from_embodied_reset_scenario", "scenario"],
            ["add_edge", "receipt", "caused_for_embodied_goal", "goal"],
            ["add_edge", "program", "has_grounded_learned_consequence", "consequence"],
            ["add_edge", "consequence", "grounded_in_causal_receipt", "receipt"],
            # This is the developmental episode's causal watermark.  The
            # planner's activation frontier is compared against it so a
            # receipt can release an active capability once, but can never be
            # re-read as a fresh observation after a later re-selection.
            # Keep it in the same graph transition as the receipt rather than
            # advancing it from daemon ticks or wall-clock time.
            ["set_attr", "episode", "latest_development_receipt_seq",
             {"__term__": A("receipt", "development_receipt_seq")}],
            ["set_attr", "program", "predicted_forward_units", {"__term__": A("evidence", "goal_progress_units")}],
            ["set_attr", "program", "predicted_energy_units", {"__term__": A("evidence", "energy_cost_units")}],
            ["set_attr", "program", "predicted_peak_load_units", {"__term__": A("evidence", "peak_load_units")}],
            ["set_attr", "program", "experience_units", {"__term__": {"type": "Plus", "items": [A("program", "experience_units"), L(1)]}}],
            ["set_attr", "counterfactual", "status", "validated"],
            ["set_attr", "reset", "status", "checkin_complete"],
        ],
    }


def developmental_evidence_rule():
    return {
        "name": "els_publish_receipt_grounded_developmental_evidence",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "The developmental DAG receives a receipt-grounded evidence object. A positive measured displacement contributes one integer capability success unit; non-progress remains retained evidence without laundering itself into success.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["session", "has_developmental_frontier", "capability"],
            ["session", "has_causal_embodied_learning_receipt", "receipt"],
        ],
        "where": absent(N("receipt", "published_as_embodied_developmental_evidence")),
        "effects": [
            ["add_node", "evidence", "EmbodiedDevelopmentalEvidence", {
                "kind": "grounded_external_trial", "success_units": {"__term__": A("receipt", "success_delta_units")},
                "progress_units": {"__term__": A("receipt", "goal_progress_units")},
                "receipt_seq": {"__term__": A("receipt", "development_receipt_seq")},
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "receipt", "published_as_embodied_developmental_evidence", "evidence"],
            ["add_edge", "capability", "has_embodied_developmental_evidence", "evidence"],
            ["add_edge", "evidence", "grounded_in_causal_receipt", "receipt"],
        ],
    }


def count_receipt_grounded_capability_success_rule():
    return {
        # NAME DELIBERATELY RETAINED though it now writes a different attribute.
        # `_reconcile_seed_rules` refreshes a changed rule BY NAME and installs an
        # unknown name additively, so renaming this would leave the old body live
        # on every resumed daemon and have BOTH increment on the same evidence —
        # reintroducing the double-count this change exists to remove.
        "name": "els_count_positive_receipt_as_capability_success",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "MEASURED PROGRESS IS NOT A MET CRITERION. This counts the "
        "world's own positive goal progress (evidence.success_units == 1) into "
        "`positive_progress_count`, which mission confirmation reads. It must "
        "NOT touch `success_count`: that attribute means 'this capability's "
        "developmental criterion was satisfied' and is what mastery and "
        "retention are judged on. Once per published developmental evidence node.",
        "match": [
            ["capability", "has_embodied_developmental_evidence", "evidence"],
            ["evidence", "grounded_in_causal_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("evidence", "success_units"), L(1)),
            absent(N("evidence", "counted_as_capability_success")),
        ),
        "effects": [
            ["set_attr", "capability", "positive_progress_count", {"__term__": {"type": "Plus", "items": [A("capability", "positive_progress_count"), L(0), L(1)]}}],
            ["add_edge", "evidence", "counted_as_capability_success", "capability"],
        ],
    }


def learning_checkin_and_reset_rearm_rule():
    return {
        "name": "els_open_receipt_grounded_learning_checkin_and_reset_rearm",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": "A closed receipt creates a graph-visible check-in and re-arms reset through the developmental scenario already used by the observed trial. The next program is still selected by the plan/Pareto machinery; no host cadence is introduced.",
        "match": [
            ["episode", "has_embodied_learning_session", "session"],
            ["session", "has_causal_embodied_learning_receipt", "receipt"],
            ["receipt", "caused_from_embodied_reset_scenario", "scenario"],
        ],
        "where": And(
            absent(N("receipt", "reviewed_by_embodied_learning_checkin")),
            no_matching_neighbour("episode", "has_active_embodied_reset_request", "active_reset", Eq(A("active_reset", "status"), L("requested"))),
        ),
        "effects": [
            ["add_node", "checkin", "EmbodiedLearningCheckin", {
                "status": "reset_requested", "receipt_seq": {"__term__": A("receipt", "development_receipt_seq")},
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_node", "reset", "EmbodiedResetRequest", {
                "status": "requested", "reason": "receipt_grounded_learning_checkin",
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "session", "has_embodied_learning_checkin", "checkin"],
            ["add_edge", "checkin", "reviews_causal_embodied_receipt", "receipt"],
            ["add_edge", "receipt", "reviewed_by_embodied_learning_checkin", "checkin"],
            ["add_edge", "episode", "has_embodied_reset_request", "reset"],
            ["add_edge", "episode", "has_active_embodied_reset_request", "reset"],
            ["add_edge", "reset", "selects_embodied_reset_scenario", "scenario"],
            ["add_edge", "reset", "caused_by_embodied_receipt", "receipt"],
            ["add_edge", "checkin", "requests_embodied_reset", "reset"],
        ],
    }


def manifest() -> dict:
    return {
        "id": "embodied_learning_session",
        "version": "1.2.0",
        "depends_on": [
            "embodied_development", "embodied_motor_priors", "embodied_motor_program",
            "counterfactual_experiment",
        ],
        "area": "embodied_learning_session",
        "latency_class": "soft_realtime",
        "description": "Persistent graph-native coordination of body/world sessions, active order-N goals, developmental plans/frontiers, existing motor hints/programs, counterfactual rehearsal, affordance-gated external trials, causal developmental receipts, integer learned consequences, receipt-grounded check-ins/reset rearming, and non-scalar Pareto evidence. All in-frame cognition is integer-native.",
        "nodes": [], "edges": [],
        "productions": [
            {"provenance": "embodied_learning_session:episode_body", "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"}, "edge_type": "has_embodied_body_schema", "tgt": {"type": "EmbodiedBodySchema", "var": "body"}},
            {"provenance": "embodied_learning_session:episode_world", "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"}, "edge_type": "has_embodied_learning_world", "tgt": {"type": "EmbodiedLearningWorld", "var": "world"}},
            {"provenance": "embodied_learning_session:world_pose", "src": {"type": "EmbodiedLearningWorld", "var": "world"}, "edge_type": "has_embodied_pose_affordance", "tgt": {"type": "EmbodiedPoseAffordance", "var": "pose"}},
            {"provenance": "embodied_learning_session:episode_session", "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"}, "edge_type": "has_embodied_learning_session", "tgt": {"type": "EmbodiedLearningSession", "var": "session"}},
            {"provenance": "embodied_learning_session:body", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_embodied_body_schema", "tgt": {"type": "EmbodiedBodySchema", "var": "body"}},
            {"provenance": "embodied_learning_session:world", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "observes_embodied_learning_world", "tgt": {"type": "EmbodiedLearningWorld", "var": "world"}},
            {"provenance": "embodied_learning_session:plan", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_learning_plan", "tgt": {"type": "LearningPlan", "var": "plan"}},
            {"provenance": "embodied_learning_session:goal", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_active_embodied_goal", "tgt": {"type": "Goal", "var": "goal"}},
            {"provenance": "embodied_learning_session:frontier", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_developmental_frontier", "tgt": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "frontier"}},
            {"provenance": "embodied_learning_session:hint", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "uses_embodied_motor_hint", "tgt": {"type": "EmbodiedMotorPrior", "var": "hint"}},
            {"provenance": "embodied_learning_session:program", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_selected_embodied_motor_program", "tgt": {"type": "EmbodiedMotorProgram", "var": "program"}},
            {"provenance": "embodied_learning_session:counterfactual", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_counterfactual_embodied_trial", "tgt": {"type": "Experiment", "var": "trial"}},
            {"provenance": "embodied_learning_session:counterfactual_request", "src": {"type": "Experiment", "var": "trial"}, "edge_type": "has_counterfactual_request", "tgt": {"type": "ImagineRequest", "var": "request"}},
            {"provenance": "embodied_learning_session:counterfactual_evidence", "src": {"type": "Experiment", "var": "trial"}, "edge_type": "has_counterfactual_evidence", "tgt": {"type": "Imagination", "var": "imagination"}},
            {"provenance": "embodied_learning_session:request_imagination", "src": {"type": "ImagineRequest", "var": "request"}, "edge_type": "produced_imagination", "tgt": {"type": "Imagination", "var": "imagination"}},
            {"provenance": "embodied_learning_session:trial_imagination", "src": {"type": "Experiment", "var": "trial"}, "edge_type": "received_counterfactual_imagination", "tgt": {"type": "Imagination", "var": "imagination"}},
            {"provenance": "embodied_learning_session:request_focus", "src": {"type": "ImagineRequest", "var": "request"}, "edge_type": "focuses_on_node", "tgt": {"type": "EmbodiedMotorProgram", "var": "program"}},
            {"provenance": "embodied_learning_session:counterfactual_projection", "src": {"type": "EmbodiedCounterfactualSelection", "var": "selection"}, "edge_type": "has_counterfactual_motor_projection", "tgt": {"type": "EmbodiedCounterfactualMotorProjection", "var": "projection"}},
            {"provenance": "embodied_learning_session:external_request", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_grounded_external_trial_request", "tgt": {"type": "EmbodiedExternalTrialRequest", "var": "request"}},
            {"provenance": "embodied_learning_session:external_evidence", "src": {"type": "EmbodiedExternalTrialRequest", "var": "request"}, "edge_type": "has_grounded_external_trial_evidence", "tgt": {"type": "EmbodiedExternalTrialEvidence", "var": "evidence"}},
            {"provenance": "embodied_learning_session:evidence_goal_vector_projection", "src": {"type": "EmbodiedExternalTrialEvidence", "var": "evidence"}, "edge_type": "has_embodied_goal_vector_projection", "tgt": {"type": "EmbodiedGoalVectorProjection", "var": "projection"}},
            {"provenance": "embodied_learning_session:trial_receipt", "src": {"type": "EmbodiedExternalTrialRequest", "var": "request"}, "edge_type": "has_embodied_learning_trial_receipt", "tgt": {"type": "EmbodiedLearningTrialReceipt", "var": "receipt"}},
            {"provenance": "embodied_learning_session:session_receipt", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_causal_embodied_learning_receipt", "tgt": {"type": "EmbodiedLearningTrialReceipt", "var": "receipt"}},
            {"provenance": "embodied_learning_session:receipt_evidence", "src": {"type": "EmbodiedLearningTrialReceipt", "var": "receipt"}, "edge_type": "grounded_in_external_trial_evidence", "tgt": {"type": "EmbodiedExternalTrialEvidence", "var": "evidence"}},
            {"provenance": "embodied_learning_session:program_consequence", "src": {"type": "EmbodiedMotorProgram", "var": "program"}, "edge_type": "has_grounded_learned_consequence", "tgt": {"type": "EmbodiedLearnedConsequence", "var": "consequence"}},
            {"provenance": "embodied_learning_session:consequence_receipt", "src": {"type": "EmbodiedLearnedConsequence", "var": "consequence"}, "edge_type": "grounded_in_causal_receipt", "tgt": {"type": "EmbodiedLearningTrialReceipt", "var": "receipt"}},
            {"provenance": "embodied_learning_session:receipt_developmental_evidence", "src": {"type": "EmbodiedLearningTrialReceipt", "var": "receipt"}, "edge_type": "published_as_embodied_developmental_evidence", "tgt": {"type": "EmbodiedDevelopmentalEvidence", "var": "evidence"}},
            {"provenance": "embodied_learning_session:capability_developmental_evidence", "src": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "capability"}, "edge_type": "has_embodied_developmental_evidence", "tgt": {"type": "EmbodiedDevelopmentalEvidence", "var": "evidence"}},
            {"provenance": "embodied_learning_session:session_checkin", "src": {"type": "EmbodiedLearningSession", "var": "session"}, "edge_type": "has_embodied_learning_checkin", "tgt": {"type": "EmbodiedLearningCheckin", "var": "checkin"}},
            {"provenance": "embodied_learning_session:receipt_checkin", "src": {"type": "EmbodiedLearningTrialReceipt", "var": "receipt"}, "edge_type": "reviewed_by_embodied_learning_checkin", "tgt": {"type": "EmbodiedLearningCheckin", "var": "checkin"}},
            {"provenance": "embodied_learning_session:request_pose", "src": {"type": "EmbodiedExternalTrialRequest", "var": "request"}, "edge_type": "uses_embodied_pose_affordance", "tgt": {"type": "EmbodiedPoseAffordance", "var": "pose"}},
            {"provenance": "embodied_learning_session:request_scenario", "src": {"type": "EmbodiedExternalTrialRequest", "var": "request"}, "edge_type": "uses_embodied_reset_scenario", "tgt": {"type": "EmbodiedResetScenario", "var": "scenario"}},
            {"provenance": "embodied_learning_session:evidence_candidate", "src": {"type": "EmbodiedExternalTrialEvidence", "var": "evidence"}, "edge_type": "published_as_pareto_candidate", "tgt": {"type": "ParetoCandidate", "var": "candidate"}},
        ],
        "rules": [
            carry_observed_support_topology_rule(),
            session_open_rule(), bind_plan_frontier_goal_rule(), bind_motor_material_rule(),
            counterfactual_trial_rule(), counterfactual_projection_rule(),
            retain_counterfactual_projection_rule(),
            external_trial_request_rule(), project_grounded_vector_evidence_rule(), evidence_rule(),
            pareto_evidence_rule(), causal_receipt_and_learning_rule(),
            developmental_evidence_rule(), count_receipt_grounded_capability_success_rule(),
            learning_checkin_and_reset_rearm_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_learning_session.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
