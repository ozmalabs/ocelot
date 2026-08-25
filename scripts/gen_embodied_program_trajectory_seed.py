#!/usr/bin/env python3
"""Generate the generic integer-native program-trajectory budget faculty.

The generator only emits graph data.  Runtime path construction, bounded
extension, Pareto refutation, and final selection are Rust-evaluated Rules.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (  # noqa: E402
    A,
    AO,
    Abs,
    And,
    Argmin,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    If,
    L,
    Lt,
    Max,
    Min,
    Minus,
    Neg,
    Neighbours,
    Not,
    Or,
    Pick,
    PI0,
    Plus,
    T,
    Times,
    V,
)


P0 = PI0


def future_manifold_projection(episode, policy, source: str, field: str):
    return {
        "type": "FutureManifoldProjection",
        "episode": episode,
        "policy": policy,
        "source": V(source),
        "field": field,
    }


def orientation_span(source: str, terminal: str) -> dict:
    """L1 distance in the supplied integer state-shape coordinates."""
    return Plus(*(
        Abs(Minus(
            P0(terminal, f"post_state_axis_{axis}_units"),
            P0(source, f"pre_state_axis_{axis}_units"),
        ))
        for axis in ("x", "y", "z")
    ))


def path_values(
    *,
    orientation: dict,
    task_progress: dict,
    evidence: dict,
    boundary: dict,
    energy: dict,
    peak_load: dict,
) -> list[list]:
    """Create complete, separate integer Pareto coordinates for one path."""
    raw = (
        orientation, task_progress, evidence, boundary, energy, peak_load,
    )
    signed = (
        orientation, task_progress, evidence, boundary,
        Neg(energy), Neg(peak_load),
    )
    effects: list[list] = []
    for ordinal, value in enumerate(signed):
        name = f"path_value_{ordinal}"
        effects.extend((
            ["add_node", name, "ParetoValue", {
                "dimension_ordinal": ordinal,
                "raw_value": T(raw[ordinal]),
                "signed_value": T(value),
                "verified": 1,
                "integer_native": 1,
            }],
            ["add_edge", "path", "has_pareto_value", name],
        ))
    return effects


def open_trajectory_rule() -> dict:
    # The current program is the moving expansion frontier, not trajectory
    # identity.  Keying uniqueness by it opened a fresh depth-one trajectory
    # after every receipt, so a verified chain could never become order N.
    # One owner holds one situated trajectory until its surrounding learning
    # context explicitly retires it.
    situated_trajectories = Neighbours(
        "owner", "has_embodied_program_trajectory"
    )
    minimum_depth = Max(
        L(1), P0("budget", "trajectory_minimum_selection_depth")
    )
    return {
        "name": "ept_open_situated_program_trajectory",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A situated owner requests arbitrary-order program "
        "composition under a horizon held by its current budget context.",
        "match": [
            ["owner", "requests_embodied_program_trajectory", "budget"],
        ],
        "where": And(
            Gt(P0("budget", "trajectory_horizon"), L(0)),
            Eq(Count(situated_trajectories), L(0)),
        ),
        "effects": [
            ["add_node", "trajectory", "ParetoProfile", {
                "kind": "embodied_program_trajectory",
                "dimension_count": 6,
                "horizon": T(P0("budget", "trajectory_horizon")),
                "active_expansion_horizon": T(Min(
                    P0("budget", "trajectory_horizon"), minimum_depth
                )),
                "minimum_selection_depth": T(minimum_depth),
                "expansion_count": 0,
                "initial_transition_population": T(Count(Neighbours(
                    "owner", "has_embodied_program_transition"
                ))),
                "last_foveation_deepening_expansion_count": -1,
                "selection_count": 0,
                "selected_task_progress_units": 0,
                "selected_capability_evidence_units": 0,
                "selected_orientation_preserving_evidence_count": 0,
                "selected_state_shape_residual_units": 0,
                "capacity_pareto_selection_count": 0,
                "capacity_dominated_path_count": 0,
                "last_capacity_candidate_count": 0,
                "last_capacity_frontier_count": 0,
                "late_transition_expansion_allowance": 0,
                "late_transition_expansion_used": 0,
                **{
                    f"selected_conditional_narrativium_retained_{dimension}": 0
                    for dimension in range(7)
                },
                "selection_enabled": 1,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "owner", "has_embodied_program_trajectory", "trajectory"],
            ["add_edge", "trajectory", "uses_embodied_program_budget", "budget"],
        ],
    }


def mint_base_path_rule() -> dict:
    span = orientation_span("transition", "transition")
    boundary = P0("transition", "boundary_transition_count")
    evidence = P0("transition", "capability_evidence_units")
    task_progress = P0("transition", "task_progress_units")
    energy = P0("transition", "energy_units")
    peak_load = P0("transition", "peak_load_units")
    return {
        "name": "ept_mint_verified_order_one_path",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": True,
        "comment": "Every verified edge is the depth-one prefix. Its state "
        "coordinates and costs remain separate Pareto dimensions. Evidence "
        "arriving after the trajectory opened grants only horizon-scaled "
        "incremental composition work.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["owner", "has_embodied_program_transition", "transition"],
            ["transition", "starts_from_embodied_program", "origin_program"],
            ["transition", "continues_with_embodied_program", "terminal_program"],
        ],
        "where": And(
            Eq(P0("trajectory", "selection_enabled"), L(1)),
            Eq(P0("transition", "verified"), L(1)),
            Eq(Count(Neighbours(
                "transition", "has_embodied_program_base_path"
            )), L(0)),
        ),
        "effects": [
            ["add_node", "path", "ParetoCandidate", {
                "kind": "embodied_program_path",
                "depth": 1,
                "origin_orientation_class": T(P0(
                    "transition", "pre_orientation_class"
                )),
                "terminal_orientation_class": T(P0(
                    "transition", "post_orientation_class"
                )),
                **{
                    f"origin_state_axis_{axis}_units": T(P0(
                        "transition", f"pre_state_axis_{axis}_units"
                    ))
                    for axis in ("x", "y", "z")
                },
                **{
                    f"terminal_state_axis_{axis}_units": T(P0(
                        "transition", f"post_state_axis_{axis}_units"
                    ))
                    for axis in ("x", "y", "z")
                },
                "orientation_span_units": T(span),
                "boundary_transition_count": T(boundary),
                "capability_evidence_units": T(evidence),
                "task_progress_units": T(task_progress),
                "energy_units": T(energy),
                "peak_load_units": T(peak_load),
                "replay_count": 0,
                "verified": 1,
                "dominated": 0,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "trajectory", "has_pareto_candidate", "path"],
            ["add_edge", "transition", "has_embodied_program_base_path", "path"],
            ["add_edge", "path", "starts_with_embodied_program_transition", "transition"],
            ["add_edge", "path", "ends_with_embodied_program_transition", "transition"],
            ["add_edge", "path", "starts_from_embodied_program", "origin_program"],
            ["add_edge", "path", "continues_with_embodied_program", "terminal_program"],
            ["add_edge", "path", "contains_embodied_program_transition", "transition"],
            ["add_edge", "path", "contains_embodied_program", "origin_program"],
            ["add_edge", "path", "contains_embodied_program", "terminal_program"],
            [
                "set_attr", "trajectory",
                "late_transition_expansion_allowance", T(Max(
                    P0(
                        "trajectory",
                        "late_transition_expansion_allowance",
                    ),
                    Times(
                        Max(
                            L(0),
                            Minus(
                                Count(Neighbours(
                                    "owner",
                                    "has_embodied_program_transition",
                                )),
                                P0(
                                    "trajectory",
                                    "initial_transition_population",
                                ),
                            ),
                        ),
                        P0("trajectory", "active_expansion_horizon"),
                    ),
                )),
            ],
            *path_values(
                orientation=span,
                task_progress=task_progress,
                evidence=evidence,
                boundary=boundary,
                energy=energy,
                peak_load=peak_load,
            ),
        ],
    }


def refresh_trajectory_horizon_rule() -> dict:
    return {
        "name": "ept_refresh_situated_trajectory_horizon_from_budget",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "An existing trajectory deepens as its situated evidence "
        "window grows. The owner retains one trajectory identity; only the "
        "graph-held expansion horizon changes.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["trajectory", "uses_embodied_program_budget", "budget"],
        ],
        "where": And(
            Eq(P0("trajectory", "selection_enabled"), L(1)),
            Gt(P0("budget", "trajectory_horizon"), L(0)),
            Not(Eq(
                P0("trajectory", "horizon"),
                P0("budget", "trajectory_horizon"),
            )),
        ),
        "effects": [[
            "set_attr", "trajectory", "horizon", T(
                P0("budget", "trajectory_horizon")
            ),
        ], [
            "set_attr", "trajectory", "active_expansion_horizon", T(
                Min(
                    P0("trajectory", "active_expansion_horizon"),
                    P0("budget", "trajectory_horizon"),
                )
            ),
        ]],
    }


def extend_path_rule() -> dict:
    transitions = Neighbours("owner", "has_embodied_program_transition")
    expansion_budget = Plus(
        P0("trajectory", "active_expansion_horizon"),
        Count(transitions),
    )
    legacy_expansion_available = And(
        Lt(P0("trajectory", "expansion_count"), expansion_budget),
        Lt(
            Count(Neighbours("trajectory", "has_pareto_candidate")),
            expansion_budget,
        ),
    )
    incremental_extension = And(
        Gt(P0("transition", "incremental_trajectory_evidence"), L(0)),
        Not(Exists(
            Neighbours("parent", "contains_embodied_program_transition"),
            "nonincremental_prefix_transition",
            Eq(P0(
                "nonincremental_prefix_transition",
                "incremental_trajectory_evidence",
            ), L(0)),
        )),
    )
    late_expansion_available = incremental_extension
    known_extensions = Filter(
        Neighbours("parent", "has_embodied_program_path_extension"),
        "known_extension",
        Exists(
            Neighbours(
                "known_extension", "appends_embodied_program_transition"
            ),
            "known_transition",
            Eq(V("known_transition"), V("transition")),
        ),
    )
    span = Plus(*(
        Abs(Minus(
            P0("transition", f"post_state_axis_{axis}_units"),
            P0("parent", f"origin_state_axis_{axis}_units"),
        ))
        for axis in ("x", "y", "z")
    ))
    boundary = Plus(
        P0("parent", "boundary_transition_count"),
        P0("transition", "boundary_transition_count"),
    )
    evidence = Plus(
        P0("parent", "capability_evidence_units"),
        P0("transition", "capability_evidence_units"),
    )
    task_progress = Plus(
        P0("parent", "task_progress_units"),
        P0("transition", "task_progress_units"),
    )
    energy = Plus(
        P0("parent", "energy_units"),
        P0("transition", "energy_units"),
    )
    peak_load = Max(
        P0("parent", "peak_load_units"),
        P0("transition", "peak_load_units"),
    )
    return {
        "name": "ept_extend_path_with_compatible_verified_transition",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Extend prefixes only through a shared program state and "
        "only while the situated graph horizon remains open. Incremental "
        "work composes wholly incremental chains, so a new observation cannot "
        "unlock an unfinished restored-graph backlog.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["trajectory", "has_pareto_candidate", "parent"],
            ["parent", "starts_with_embodied_program_transition", "first_transition"],
            ["parent", "starts_from_embodied_program", "origin_program"],
            ["parent", "continues_with_embodied_program", "middle_program"],
            ["owner", "has_embodied_program_transition", "transition"],
            ["transition", "starts_from_embodied_program", "middle_program"],
            ["transition", "continues_with_embodied_program", "terminal_program"],
        ],
        "where": And(
            Eq(P0("trajectory", "selection_enabled"), L(1)),
            Eq(A("parent", "kind"), L("embodied_program_path")),
            Eq(P0("parent", "verified"), L(1)),
            Eq(P0("transition", "verified"), L(1)),
            Lt(
                P0("parent", "depth"),
                P0("trajectory", "active_expansion_horizon"),
            ),
            Or(legacy_expansion_available, late_expansion_available),
            Not(Exists(
                Neighbours("parent", "contains_embodied_program"),
                "known_program",
                Eq(V("known_program"), V("terminal_program")),
            )),
            Eq(Count(known_extensions), L(0)),
        ),
        "effects": [
            ["add_node", "path", "ParetoCandidate", {
                "kind": "embodied_program_path",
                "depth": T(Plus(P0("parent", "depth"), L(1))),
                "origin_orientation_class": T(P0(
                    "parent", "origin_orientation_class"
                )),
                "terminal_orientation_class": T(P0(
                    "transition", "post_orientation_class"
                )),
                **{
                    f"origin_state_axis_{axis}_units": T(P0(
                        "parent", f"origin_state_axis_{axis}_units"
                    ))
                    for axis in ("x", "y", "z")
                },
                **{
                    f"terminal_state_axis_{axis}_units": T(P0(
                        "transition", f"post_state_axis_{axis}_units"
                    ))
                    for axis in ("x", "y", "z")
                },
                "orientation_span_units": T(span),
                "boundary_transition_count": T(boundary),
                "capability_evidence_units": T(evidence),
                "task_progress_units": T(task_progress),
                "energy_units": T(energy),
                "peak_load_units": T(peak_load),
                "replay_count": 0,
                "verified": 1,
                "dominated": 0,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "trajectory", "has_pareto_candidate", "path"],
            ["add_edge", "parent", "has_embodied_program_path_extension", "path"],
            ["add_edge", "path", "extends_embodied_program_path", "parent"],
            ["add_edge", "path", "appends_embodied_program_transition", "transition"],
            ["add_edge", "path", "starts_with_embodied_program_transition", "first_transition"],
            ["add_edge", "path", "ends_with_embodied_program_transition", "transition"],
            ["add_edge", "path", "starts_from_embodied_program", "origin_program"],
            ["add_edge", "path", "continues_with_embodied_program", "terminal_program"],
            ["add_edge", "path", "contains_embodied_program_transition", "transition"],
            ["add_edge", "path", "contains_embodied_program", "terminal_program"],
            ["set_attr", "trajectory", "expansion_count", T(Plus(
                P0("trajectory", "expansion_count"), L(1)
            ))],
            ["set_attr", "trajectory", "expansion_budget_units", T(
                expansion_budget
            )],
            [
                "set_attr", "trajectory",
                "late_transition_expansion_used", T(Plus(
                    P0("trajectory", "late_transition_expansion_used"),
                    If(incremental_extension, L(1), L(0)),
                )),
            ],
            *path_values(
                orientation=span,
                task_progress=task_progress,
                evidence=evidence,
                boundary=boundary,
                energy=energy,
                peak_load=peak_load,
            ),
        ],
    }


def inherit_path_transition_rule() -> dict:
    return {
        "name": "ept_inherit_prefix_transition_membership",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": True,
        "match": [
            ["parent", "has_embodied_program_path_extension", "path"],
            ["parent", "contains_embodied_program_transition", "transition"],
        ],
        "where": Not(Exists(
            Neighbours("path", "contains_embodied_program_transition"),
            "known_transition",
            Eq(V("known_transition"), V("transition")),
        )),
        "effects": [[
            "add_edge", "path", "contains_embodied_program_transition", "transition"
        ]],
    }


def inherit_path_program_rule() -> dict:
    return {
        "name": "ept_inherit_prefix_program_membership",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": True,
        "match": [
            ["parent", "has_embodied_program_path_extension", "path"],
            ["parent", "contains_embodied_program", "program"],
        ],
        "where": Not(Exists(
            Neighbours("path", "contains_embodied_program"),
            "known_program",
            Eq(V("known_program"), V("program")),
        )),
        "effects": [[
            "add_edge", "path", "contains_embodied_program", "program"
        ]],
    }


def situate_path_in_current_state_rule() -> dict:
    path_sources = Filter(
        Neighbours("path", "contains_embodied_program_transition"),
        "path_source",
        Exists(
            Neighbours(
                "owner", "has_current_embodied_program_transition_source"
            ),
            "current_source",
            Eq(V("path_source"), V("current_source")),
        ),
    )
    closest = Argmin(
        path_sources,
        "closest_path_source",
        P0("closest_path_source", "current_state_shape_residual_units"),
        V("path"),
    )
    return {
        "name": "ept_situate_path_in_current_state_shape",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": True,
        "comment": "Cache the least residual between a retained path and "
        "the owner's current receipt-grounded transition sources. This is a "
        "situated selection coordinate, not new transition evidence.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["trajectory", "has_pareto_candidate", "path"],
            ["path", "contains_embodied_program_transition", "transition"],
        ],
        "where": And(
            Gt(Count(path_sources), L(0)),
            Eq(V("transition"), closest),
            Not(Eq(
                P0("path", "current_state_shape_residual_units"),
                P0("transition", "current_state_shape_residual_units"),
            )),
        ),
        "effects": [[
            "set_attr", "path", "current_state_shape_residual_units", T(
                P0("transition", "current_state_shape_residual_units")
            ),
        ]],
    }


def select_frontier_path_rule() -> dict:

    def transition_forecast_supported(transition_var: str) -> dict:
        # The receipt which minted a verified transition is its first support
        # observation. Replays then add confirmations or counterexamples. A
        # tie retains the historical fact but suspends its predictive use.
        return Gt(
            Plus(
                L(1),
                P0(transition_var, "situated_forecast_confirmation_count"),
            ),
            P0(transition_var, "situated_forecast_counterexample_count"),
        )

    def is_unblocked_from(path_var: str, transition_var: str) -> dict:
        return And(
            transition_forecast_supported(transition_var),
            Not(Exists(
                Neighbours(
                    path_var,
                    "manifold_blocked_from_embodied_program_transition",
                ),
                "blocked_state_transition",
                Eq(V("blocked_state_transition"), V(transition_var)),
            )),
        )

    def has_next_transition_from_current(path_var: str) -> dict:
        return Or(
            Exists(
                Neighbours(path_var, "contains_embodied_program_transition"),
                "path_next_transition",
                And(
                    Exists(
                        Neighbours(
                            "path_next_transition",
                            "starts_from_embodied_program",
                        ),
                        "path_next_source",
                        Eq(V("path_next_source"), V("current_program")),
                    ),
                    is_unblocked_from(path_var, "path_next_transition"),
                ),
            ),
            Exists(
                Neighbours(
                    "owner", "has_current_embodied_program_transition_source"
                ),
                "current_transition_source",
                Exists(
                    Neighbours(
                        path_var, "contains_embodied_program_transition"
                    ),
                    "path_state_transition",
                    And(
                        Eq(
                            V("path_state_transition"),
                            V("current_transition_source"),
                        ),
                        is_unblocked_from(
                            path_var, "current_transition_source"
                        ),
                    ),
                ),
            ),
        )

    frontier = Filter(
        Neighbours("trajectory", "has_pareto_candidate"),
        "frontier_path",
        And(
            Eq(A("frontier_path", "kind"), L("embodied_program_path")),
            Eq(P0("frontier_path", "verified"), L(1)),
            Not(Lt(
                P0("frontier_path", "depth"),
                P0("trajectory", "minimum_selection_depth"),
            )),
            Or(
                Gt(P0("frontier_path", "orientation_span_units"), L(0)),
                Gt(P0("frontier_path", "task_progress_units"), L(0)),
                Gt(P0("frontier_path", "capability_evidence_units"), L(0)),
            ),
            Eq(
                Count(Neighbours(
                    "frontier_path", "contains_embodied_program_transition"
                )),
                P0("frontier_path", "depth"),
            ),
            Eq(
                Count(Neighbours(
                    "frontier_path", "contains_embodied_program"
                )),
                Plus(P0("frontier_path", "depth"), L(1)),
            ),
            has_next_transition_from_current("frontier_path"),
            Eq(Count(Neighbours(
                "frontier_path", "is_dominated_by_pareto_candidate"
            )), L(0)),
        ),
    )
    # Every frontier member already contains a currently admissible source
    # and survived Pareto refutation. Select the shortest such path, then use
    # the prior situated rank only within that equal-depth subset. This makes
    # temporal foveation a relational restriction, not a weighted preference
    # that a large task coordinate could reverse.
    shallowest = Argmin(
        frontier,
        "shallow_frontier_path",
        P0("shallow_frontier_path", "depth"),
        V("owner"),
    )
    shortest = Filter(
        frontier,
        "shortest_frontier_path",
        Eq(
            P0("shortest_frontier_path", "depth"),
            AO(shallowest, "depth"),
        ),
    )
    manifold_episodes = Neighbours(
        "owner", "projects_future_manifold_in_episode"
    )
    manifold_policies = Neighbours(
        "owner", "uses_future_manifold_policy"
    )
    manifold_context_ready = And(
        Eq(Count(manifold_episodes), L(1)),
        Eq(Count(manifold_policies), L(1)),
    )

    def retained(path_var: str, dimension: int) -> dict:
        return future_manifold_projection(
            Pick(manifold_episodes),
            Pick(manifold_policies),
            path_var,
            f"conditional_narrativium_retained_{dimension}",
        )

    capacity_frontier = Filter(
        shortest,
        "capacity_path",
        Or(
            Not(manifold_context_ready),
            Not(Exists(
                shortest,
                "capacity_alternative",
                And(
                    Not(Eq(
                        V("capacity_alternative"), V("capacity_path")
                    )),
                    *(
                        Not(Lt(
                            retained("capacity_alternative", dimension),
                            retained("capacity_path", dimension),
                        ))
                        for dimension in range(7)
                    ),
                    Or(*(
                        Gt(
                            retained("capacity_alternative", dimension),
                            retained("capacity_path", dimension),
                        )
                        for dimension in range(7)
                    )),
                ),
            )),
        ),
    )
    rank_span = Plus(
        P0("trajectory", "active_expansion_horizon"), L(1)
    )
    selected = Argmin(
        capacity_frontier,
        "frontier_path",
        Plus(
            Times(
                P0(
                    "frontier_path",
                    "current_state_shape_residual_units",
                ),
                rank_span,
                rank_span,
                rank_span,
            ),
            Times(
                Neg(P0("frontier_path", "task_progress_units")),
                rank_span,
                rank_span,
            ),
            Times(
                Neg(P0(
                    "frontier_path", "capability_evidence_units"
                )),
                rank_span,
            ),
            P0("frontier_path", "replay_count"),
        ),
        shallowest,
    )
    return {
        "name": "ept_collapse_frontier_to_one_practice_path",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Pareto removes only refuted paths. Temporal foveation "
        "first restricts choice to the shortest sufficient prefix. When a "
        "situated manifold context exists, a second Pareto restriction "
        "removes only paths dominated in all seven conditional retained-"
        "future dimensions; no scalar capacity score is formed. Situated "
        "task, evidence, and practice coordinates order the surviving "
        "tradeoffs. Receipt counterexamples suspend reuse when they no "
        "longer leave a positive transition forecast evidence ratio. "
        "Selection grants no actuator authority.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["owner", "has_current_embodied_program", "current_program"],
            ["trajectory", "has_pareto_candidate", "path"],
        ],
        "where": And(
            Eq(P0("trajectory", "selection_enabled"), L(1)),
            Gt(Count(frontier), L(0)),
            Eq(V("path"), selected),
            Eq(Count(Neighbours(
                "owner", "has_selected_embodied_program_path"
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "owner", "has_selected_embodied_program_path", "path"],
            ["set_attr", "trajectory", "selection_count", T(Plus(
                P0("trajectory", "selection_count"), L(1)
            ))],
            ["set_attr", "trajectory", "selected_task_progress_units", T(
                Plus(
                    P0("trajectory", "selected_task_progress_units"),
                    P0("path", "task_progress_units"),
                )
            )],
            ["set_attr", "trajectory", "selected_capability_evidence_units", T(
                Plus(
                    P0("trajectory", "selected_capability_evidence_units"),
                    P0("path", "capability_evidence_units"),
                )
            )],
            [
                "set_attr", "trajectory",
                "selected_orientation_preserving_evidence_count", T(Plus(
                    P0(
                        "trajectory",
                        "selected_orientation_preserving_evidence_count",
                    ),
                    If(
                        And(
                            Eq(P0("path", "orientation_span_units"), L(0)),
                            Gt(P0("path", "capability_evidence_units"), L(0)),
                        ),
                        L(1), L(0),
                    ),
                ))
            ],
            ["set_attr", "trajectory", "selected_state_shape_residual_units", T(
                P0("path", "current_state_shape_residual_units")
            )],
            ["set_attr", "trajectory", "last_capacity_candidate_count", T(
                Count(shortest)
            )],
            ["set_attr", "trajectory", "last_capacity_frontier_count", T(
                Count(capacity_frontier)
            )],
            ["set_attr", "trajectory", "capacity_pareto_selection_count", T(
                Plus(
                    P0("trajectory", "capacity_pareto_selection_count"),
                    If(
                        Lt(Count(capacity_frontier), Count(shortest)),
                        L(1), L(0),
                    ),
                )
            )],
            ["set_attr", "trajectory", "capacity_dominated_path_count", T(
                Plus(
                    P0("trajectory", "capacity_dominated_path_count"),
                    Minus(Count(shortest), Count(capacity_frontier)),
                )
            )],
            *[
                [
                    "set_attr", "trajectory",
                    f"selected_conditional_narrativium_retained_{dimension}",
                    T(If(
                        manifold_context_ready,
                        retained("path", dimension),
                        L(0),
                    )),
                ]
                for dimension in range(7)
            ],
        ],
    }


def retract_refuted_selection_rule() -> dict:
    return {
        "name": "ept_retract_selected_path_when_counterexample_arrives",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A later relational counterexample changes the next "
        "collapse; it never interrupts an already issued motor outcome.",
        "match": [
            ["owner", "has_selected_embodied_program_path", "path"],
            ["path", "is_dominated_by_pareto_candidate", "alternative"],
        ],
        "effects": [[
            "del_edge", "owner", "has_selected_embodied_program_path", "path"
        ]],
    }


def deepen_exhausted_trajectory_rule() -> dict:
    blocked_local_paths = Filter(
        Neighbours("trajectory", "has_pareto_candidate"),
        "blocked_local_path",
        And(
            Eq(
                P0("blocked_local_path", "depth"),
                P0("trajectory", "active_expansion_horizon"),
            ),
            Gt(Count(Neighbours(
                "blocked_local_path",
                "manifold_blocked_from_embodied_program_transition",
            )), L(0)),
        ),
    )
    return {
        "name": "ept_deepen_trajectory_after_local_frontier_exhaustion",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Temporal foveation holds farther futures as potential. "
        "Expose one additional order only after the manifold explicitly "
        "blocks a path at the active depth; deeper orders require their own "
        "new local block evidence.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["owner", "has_current_embodied_program", "current_program"],
        ],
        "where": And(
            Eq(P0("trajectory", "selection_enabled"), L(1)),
            Lt(
                P0("trajectory", "active_expansion_horizon"),
                P0("trajectory", "horizon"),
            ),
            Eq(Count(Neighbours(
                "owner", "has_selected_embodied_program_path"
            )), L(0)),
            Gt(Count(blocked_local_paths), L(0)),
            Not(Eq(
                P0(
                    "trajectory",
                    "last_foveation_deepening_expansion_count",
                ),
                P0("trajectory", "expansion_count"),
            )),
        ),
        "effects": [[
            "set_attr", "trajectory", "active_expansion_horizon", T(
                Plus(P0("trajectory", "active_expansion_horizon"), L(1))
            ),
        ], [
            "set_attr", "trajectory", "foveation_deepening_count", T(
                Plus(P0("trajectory", "foveation_deepening_count"), L(1))
            ),
        ], [
            "set_attr", "trajectory",
            "last_foveation_deepening_expansion_count", T(
                P0("trajectory", "expansion_count")
            ),
        ]],
    }


def manifest() -> dict:
    productions = (
        ("request", "Node", "requests_embodied_program_trajectory", "Node"),
        ("trajectory", "Node", "has_embodied_program_trajectory", "ParetoProfile"),
        ("budget", "ParetoProfile", "uses_embodied_program_budget", "Node"),
        ("transition", "ParetoProfile", "has_embodied_program_transition", "Node"),
        ("from_program", "Node", "starts_from_embodied_program", "Node"),
        ("to_program", "Node", "continues_with_embodied_program", "Node"),
        ("base", "Node", "has_embodied_program_base_path", "ParetoCandidate"),
        ("extension", "ParetoCandidate", "has_embodied_program_path_extension", "ParetoCandidate"),
        ("parent", "ParetoCandidate", "extends_embodied_program_path", "ParetoCandidate"),
        ("append", "ParetoCandidate", "appends_embodied_program_transition", "Node"),
        ("first", "ParetoCandidate", "starts_with_embodied_program_transition", "Node"),
        ("last", "ParetoCandidate", "ends_with_embodied_program_transition", "Node"),
        ("selected", "Node", "has_selected_embodied_program_path", "ParetoCandidate"),
        ("current", "Node", "has_current_embodied_program", "Node"),
        (
            "current_transition_source", "Node",
            "has_current_embodied_program_transition_source", "Node",
        ),
        (
            "manifold_blocked_transition", "ParetoCandidate",
            "manifold_blocked_from_embodied_program_transition", "Node",
        ),
        ("path_transition", "ParetoCandidate", "contains_embodied_program_transition", "Node"),
        ("path_program", "ParetoCandidate", "contains_embodied_program", "Node"),
    )
    return {
        "id": "embodied_program_trajectory",
        "version": "1.5.0",
        "depends_on": ["cognitive_pareto"],
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "description": "Arbitrary-order, integer, receipt-grounded program "
        "prefix construction under a situated graph budget, with relational "
        "Pareto refutation and output-null curiosity selection.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": f"embodied_program_trajectory:{name}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for name, src, edge, tgt in productions
        ],
        "rules": [
            open_trajectory_rule(),
            refresh_trajectory_horizon_rule(),
            mint_base_path_rule(),
            extend_path_rule(),
            inherit_path_transition_rule(),
            inherit_path_program_rule(),
            situate_path_in_current_state_rule(),
            retract_refuted_selection_rule(),
            select_frontier_path_rule(),
            deepen_exhausted_trajectory_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_program_trajectory.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
