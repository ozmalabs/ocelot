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
    Abs,
    And,
    Argmin,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    L,
    Lt,
    Max,
    Minus,
    Neg,
    Neighbours,
    Not,
    PI0,
    Plus,
    T,
    Times,
    V,
)


P0 = PI0


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
    boundary: dict,
    energy: dict,
    peak_load: dict,
) -> list[list]:
    """Create the four complete integer Pareto coordinates for one path."""
    raw = (orientation, boundary, energy, peak_load)
    signed = (orientation, boundary, Neg(energy), Neg(peak_load))
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
    return {
        "name": "ept_open_situated_program_trajectory",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A situated owner requests arbitrary-order program "
        "composition under a horizon held by its current budget context.",
        "match": [
            ["owner", "requests_embodied_program_trajectory", "budget"],
            ["owner", "has_current_embodied_program", "current_program"],
        ],
        "where": And(
            Gt(P0("budget", "trajectory_horizon"), L(0)),
            Eq(Count(situated_trajectories), L(0)),
        ),
        "effects": [
            ["add_node", "trajectory", "ParetoProfile", {
                "kind": "embodied_program_trajectory",
                "dimension_count": 4,
                "horizon": T(P0("budget", "trajectory_horizon")),
                "expansion_count": 0,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "owner", "has_embodied_program_trajectory", "trajectory"],
            ["add_edge", "trajectory", "uses_embodied_program_budget", "budget"],
            ["add_edge", "trajectory", "starts_from_embodied_program", "current_program"],
        ],
    }


def mint_base_path_rule() -> dict:
    span = orientation_span("transition", "transition")
    boundary = P0("transition", "boundary_transition_count")
    energy = P0("transition", "energy_units")
    peak_load = P0("transition", "peak_load_units")
    return {
        "name": "ept_mint_verified_order_one_path",
        "area": "embodied_program_trajectory",
        "latency_class": "soft_realtime",
        "batch": True,
        "comment": "Every verified edge is the depth-one prefix. Its state "
        "coordinates and costs remain separate Pareto dimensions.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["owner", "has_current_embodied_program", "origin_program"],
            ["trajectory", "starts_from_embodied_program", "origin_program"],
            ["owner", "has_embodied_program_transition", "transition"],
            ["transition", "starts_from_embodied_program", "origin_program"],
            ["transition", "continues_with_embodied_program", "terminal_program"],
        ],
        "where": And(
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
            *path_values(
                orientation=span,
                boundary=boundary,
                energy=energy,
                peak_load=peak_load,
            ),
        ],
    }


def extend_path_rule() -> dict:
    transitions = Neighbours("owner", "has_embodied_program_transition")
    expansion_budget = Plus(
        P0("trajectory", "horizon"),
        Count(transitions),
    )
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
        "only while the situated graph horizon remains open.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["owner", "has_current_embodied_program", "origin_program"],
            ["trajectory", "starts_from_embodied_program", "origin_program"],
            ["trajectory", "has_pareto_candidate", "parent"],
            ["parent", "starts_with_embodied_program_transition", "first_transition"],
            ["parent", "starts_from_embodied_program", "origin_program"],
            ["parent", "continues_with_embodied_program", "middle_program"],
            ["owner", "has_embodied_program_transition", "transition"],
            ["transition", "starts_from_embodied_program", "middle_program"],
            ["transition", "continues_with_embodied_program", "terminal_program"],
        ],
        "where": And(
            Eq(A("parent", "kind"), L("embodied_program_path")),
            Eq(P0("parent", "verified"), L(1)),
            Eq(P0("transition", "verified"), L(1)),
            Lt(P0("parent", "depth"), P0("trajectory", "horizon")),
            Lt(P0("trajectory", "expansion_count"), expansion_budget),
            Lt(
                Count(Neighbours("trajectory", "has_pareto_candidate")),
                expansion_budget,
            ),
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
            *path_values(
                orientation=span,
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


def select_frontier_path_rule() -> dict:
    frontier = Filter(
        Neighbours("trajectory", "has_pareto_candidate"),
        "frontier_path",
        And(
            Eq(A("frontier_path", "kind"), L("embodied_program_path")),
            Eq(P0("frontier_path", "verified"), L(1)),
            Gt(P0("frontier_path", "orientation_span_units"), L(0)),
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
            Exists(
                Neighbours("frontier_path", "starts_from_embodied_program"),
                "path_origin",
                Eq(V("path_origin"), V("current_program")),
            ),
            Eq(Count(Neighbours(
                "frontier_path", "is_dominated_by_pareto_candidate"
            )), L(0)),
        ),
    )
    # replay_count is the curiosity/default coordinate.  The multiplier is
    # derived from the held horizon, making depth a bounded tie-break rather
    # than an authored utility coefficient.
    selected = Argmin(
        frontier,
        "frontier_path",
        Plus(
            Times(
                P0("frontier_path", "replay_count"),
                Plus(P0("trajectory", "horizon"), L(1)),
            ),
            Neg(P0("frontier_path", "depth")),
        ),
        V("owner"),
    )
    return {
        "name": "ept_collapse_frontier_to_one_practice_path",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Pareto removes only refuted paths. Curiosity then "
        "collapses the surviving frontier to one least-practised, deepest "
        "prefix; this selection grants no actuator authority.",
        "match": [
            ["owner", "has_embodied_program_trajectory", "trajectory"],
            ["owner", "has_current_embodied_program", "current_program"],
            ["trajectory", "has_pareto_candidate", "path"],
        ],
        "where": And(
            Gt(Count(frontier), L(0)),
            Eq(V("path"), selected),
            Eq(Count(Neighbours(
                "owner", "has_selected_embodied_program_path"
            )), L(0)),
        ),
        "effects": [[
            "add_edge", "owner", "has_selected_embodied_program_path", "path"
        ]],
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
        ("path_transition", "ParetoCandidate", "contains_embodied_program_transition", "Node"),
        ("path_program", "ParetoCandidate", "contains_embodied_program", "Node"),
    )
    return {
        "id": "embodied_program_trajectory",
        "version": "1.0.0",
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
            mint_base_path_rule(),
            extend_path_rule(),
            inherit_path_transition_rule(),
            inherit_path_program_rule(),
            retract_refuted_selection_rule(),
            select_frontier_path_rule(),
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
