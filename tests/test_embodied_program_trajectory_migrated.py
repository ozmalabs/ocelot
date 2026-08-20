from __future__ import annotations

import json
from pathlib import Path

from scripts.gen_embodied_program_trajectory_seed import manifest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "embodied_program_trajectory.json"


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_integer_native(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_integer_native(nested)


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _fixture(horizon: int, transitions):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_program_trajectory",))
    owner = agent.s.add_node("FixtureTrajectoryOwner", {})
    budget = agent.s.add_node("FixtureTrajectoryBudget", {
        "trajectory_horizon": horizon,
        "integer_native": 1,
    })
    programs = [
        agent.s.add_node("FixtureProgram", {"ordinal": ordinal})
        for ordinal in range(6)
    ]
    _edge(agent, owner, "requests_embodied_program_trajectory", budget)
    _edge(agent, owner, "has_current_embodied_program", programs[0])
    agent.tick()
    trajectory = agent.inner.neighbours(
        owner, "has_embodied_program_trajectory"
    )[0]
    transition_nodes = []
    for row in transitions:
        transition = agent.s.add_node("FixtureTransition", {
            "verified": 1,
            "pre_orientation_class": row.get("pre_class", 1),
            "post_orientation_class": row.get("post_class", 1),
            "pre_state_axis_x_units": row["pre_x"],
            "pre_state_axis_y_units": 0,
            "pre_state_axis_z_units": 0,
            "post_state_axis_x_units": row["post_x"],
            "post_state_axis_y_units": 0,
            "post_state_axis_z_units": 0,
            "boundary_transition_count": row.get("boundary", 0),
            "energy_units": row["energy"],
            "peak_load_units": row.get("load", 1),
            "integer_native": 1,
        })
        transition_nodes.append(transition)
        _edge(agent, owner, "has_embodied_program_transition", transition)
        _edge(
            agent, transition, "starts_from_embodied_program",
            programs[row["source"]],
        )
        _edge(
            agent, transition, "continues_with_embodied_program",
            programs[row["target"]],
        )
    agent.tick()
    return agent, owner, trajectory, transition_nodes


def test_seed_is_reproducible_generic_integer_and_output_null():
    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    _assert_integer_native(generated)
    encoded = json.dumps(generated).lower()
    for forbidden in (
        "humanoid", "rolling", "joint", "arm", "leg", "pybullet",
        "target_torque", "canonical_pose",
    ):
        assert forbidden not in encoded
    assert '"output_authority": 0' in encoded
    assert "manifold_blocked_from_embodied_program_transition" in encoded
    assert generated["depends_on"] == ["cognitive_pareto"]


def test_graph_budget_alone_opens_order_two_path_and_changes_selection():
    rows = (
        # Best immediate change, but a dead basin.
        {"source": 0, "target": 3, "pre_x": 0, "post_x": 90,
         "energy": 4},
        # Smaller first move opens a boundary-crossing successor.
        {"source": 0, "target": 1, "pre_x": 0, "post_x": 70,
         "energy": 2},
        {"source": 1, "target": 2, "pre_x": 70, "post_x": 100,
         "energy": 2, "boundary": 1, "post_class": 2},
    )
    shallow, shallow_owner, shallow_trajectory, _ = _fixture(1, rows)
    shallow_paths = shallow.inner.neighbours(
        shallow_trajectory, "has_pareto_candidate"
    )
    assert {shallow.s.node(path)["attrs"]["depth"] for path in shallow_paths} == {1}
    shallow_selected = shallow.inner.neighbours(
        shallow_owner, "has_selected_embodied_program_path"
    )
    assert shallow.s.node(shallow_selected[0])["attrs"]["depth"] == 1

    deep, deep_owner, deep_trajectory, _ = _fixture(2, rows)
    deep_paths = deep.inner.neighbours(
        deep_trajectory, "has_pareto_candidate"
    )
    depth_two = [
        path for path in deep_paths
        if deep.s.node(path)["attrs"]["depth"] == 2
    ]
    assert len(depth_two) == 1
    assert deep.s.node(depth_two[0])["attrs"]["boundary_transition_count"] == 1
    selected = deep.inner.neighbours(
        deep_owner, "has_selected_embodied_program_path"
    )
    assert selected == depth_two


def test_moving_current_program_does_not_fragment_situated_trajectory():
    agent, owner, trajectory, _ = _fixture(2, ())
    programs = [
        agent.s.add_node("FixtureProgram", {"ordinal": ordinal})
        for ordinal in (10, 11)
    ]
    current = agent.inner.neighbours(owner, "has_current_embodied_program")[0]
    agent.inner.remove_edge(owner, "has_current_embodied_program", current)
    _edge(agent, owner, "has_current_embodied_program", programs[0])
    agent.tick()
    agent.inner.remove_edge(
        owner, "has_current_embodied_program", programs[0]
    )
    _edge(agent, owner, "has_current_embodied_program", programs[1])
    origin = agent.inner.neighbours(
        trajectory, "starts_from_embodied_program"
    )[0]
    transition = agent.s.add_node("FixtureTransition", {
        "verified": 1,
        "pre_orientation_class": 1,
        "post_orientation_class": 1,
        "pre_state_axis_x_units": 0,
        "pre_state_axis_y_units": 0,
        "pre_state_axis_z_units": 0,
        "post_state_axis_x_units": 10,
        "post_state_axis_y_units": 0,
        "post_state_axis_z_units": 0,
        "boundary_transition_count": 0,
        "energy_units": 1,
        "peak_load_units": 1,
    })
    _edge(agent, owner, "has_embodied_program_transition", transition)
    _edge(agent, transition, "starts_from_embodied_program", origin)
    _edge(
        agent, transition, "continues_with_embodied_program", programs[0]
    )
    agent.tick()
    assert agent.inner.neighbours(
        owner, "has_embodied_program_trajectory"
    ) == [trajectory]
    assert len(agent.inner.neighbours(
        transition, "has_embodied_program_base_path"
    )) == 1


def test_frontier_remains_replayable_from_an_internal_current_program():
    agent, owner, trajectory, transitions = _fixture(2, (
        {"source": 0, "target": 1, "pre_x": 0, "post_x": 10,
         "energy": 1},
        {"source": 1, "target": 2, "pre_x": 10, "post_x": 20,
         "energy": 1},
    ))
    selected = agent.inner.neighbours(
        owner, "has_selected_embodied_program_path"
    )[0]
    agent.inner.remove_edge(
        owner, "has_selected_embodied_program_path", selected
    )
    current = agent.inner.neighbours(
        owner, "has_current_embodied_program"
    )[0]
    middle = agent.inner.neighbours(
        transitions[0], "continues_with_embodied_program"
    )[0]
    agent.inner.remove_edge(owner, "has_current_embodied_program", current)
    _edge(agent, owner, "has_current_embodied_program", middle)
    agent.tick()
    replayable = agent.inner.neighbours(
        owner, "has_selected_embodied_program_path"
    )
    assert len(replayable) == 1
    assert agent.s.node(replayable[0])["attrs"]["depth"] == 2


def test_pareto_refutes_only_dominated_paths_and_keeps_tradeoffs():
    agent, _, trajectory, transitions = _fixture(1, (
        {"source": 0, "target": 1, "pre_x": 0, "post_x": 10,
         "energy": 1, "load": 1},
        {"source": 0, "target": 2, "pre_x": 0, "post_x": 20,
         "energy": 5, "load": 1},
        {"source": 0, "target": 3, "pre_x": 0, "post_x": 5,
         "energy": 2, "load": 1},
    ))
    paths = {
        agent.inner.neighbours(transition, "has_embodied_program_base_path")[0]:
        transition
        for transition in transitions
    }
    by_span = {
        agent.s.node(path)["attrs"]["orientation_span_units"]: path
        for path in paths
    }
    assert not agent.inner.neighbours(
        by_span[10], "is_dominated_by_pareto_candidate"
    )
    assert not agent.inner.neighbours(
        by_span[20], "is_dominated_by_pareto_candidate"
    )
    assert agent.inner.neighbours(
        by_span[5], "is_dominated_by_pareto_candidate"
    )
    frontier = [
        path for path in agent.inner.neighbours(
            trajectory, "has_pareto_candidate"
        )
        if not agent.inner.neighbours(
            path, "is_dominated_by_pareto_candidate"
        )
    ]
    assert {agent.s.node(path)["attrs"]["orientation_span_units"]
            for path in frontier} == {10, 20}


def test_branching_expansion_is_bounded_by_graph_budget_not_authored_depth():
    rows = (
        {"source": 0, "target": 1, "pre_x": 0, "post_x": 10,
         "energy": 1},
        {"source": 0, "target": 2, "pre_x": 0, "post_x": 20,
         "energy": 1},
        {"source": 1, "target": 3, "pre_x": 10, "post_x": 30,
         "energy": 1},
        {"source": 1, "target": 4, "pre_x": 10, "post_x": 40,
         "energy": 1},
        {"source": 2, "target": 4, "pre_x": 20, "post_x": 40,
         "energy": 1},
        {"source": 3, "target": 5, "pre_x": 30, "post_x": 50,
         "energy": 1},
    )
    agent, _, trajectory, _ = _fixture(5, rows)
    attrs = agent.s.node(trajectory)["attrs"]
    assert attrs["expansion_budget_units"] == 5 + len(rows)
    assert attrs["expansion_count"] <= attrs["expansion_budget_units"]
    assert len(agent.inner.neighbours(
        trajectory, "has_pareto_candidate"
    )) <= attrs["expansion_budget_units"]
    assert max(
        agent.s.node(path)["attrs"]["depth"]
        for path in agent.inner.neighbours(trajectory, "has_pareto_candidate")
    ) > 2
