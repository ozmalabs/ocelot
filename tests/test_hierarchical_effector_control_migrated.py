from __future__ import annotations

import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "hierarchical_effector_control.json"


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _scope(agent, topology, token, children):
    scope = agent.s.add_node("EmbodiedControlSubsection", {
        "scope_token": token,
        "scope_kind": "named",
        "status": "ready",
        "member_count": 0,
        "integer_native": 1,
        "output_authority": 0,
    })
    _edge(agent, topology, "has_embodied_control_subsection", scope)
    for child in children:
        _edge(agent, scope, "contains_embodied_control_subsection", child)
    return scope


def _binding(agent, parent, scope, child_program, operator="superpose"):
    binding = agent.s.add_node("EmbodiedProgramBinding", {
        "composition_operator": operator,
        "status": "open",
    })
    _edge(agent, parent, "includes_embodied_program_binding", binding)
    _edge(agent, binding, "targets_embodied_control_subsection", scope)
    _edge(agent, binding, "invokes_embodied_child_motor_program", child_program)
    return binding


def _body(agent, width=5):
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    effectors = []
    for ordinal in range(width):
        effector = agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "channel_ordinal": ordinal,
        })
        effectors.append(effector)
        _edge(agent, topology, "has_embodied_effector", effector)
    assert agent.tick() > 0
    singletons = {}
    for scope in agent.s.neighbours(topology, "has_embodied_control_subsection"):
        attrs = agent.s.node(scope)["attrs"]
        if attrs.get("scope_kind") != "singleton":
            continue
        member = agent.s.neighbours(scope, "addresses_embodied_effector")
        assert len(member) == 1
        singletons[member[0]] = scope
    assert set(singletons) == set(effectors)
    return topology, effectors, singletons


def test_seed_is_reproducible_generic_and_wired_into_embodied_core():
    from scripts.gen_hierarchical_effector_control_seed import manifest

    assert json.loads(SEED.read_text(encoding="utf-8")) == manifest()
    text = SEED.read_text(encoding="utf-8").lower()
    for forbidden in ("left_arm", "right_arm", "leg", "joint", "f16"):
        assert forbidden not in text

    core = json.loads(
        (ROOT / "seeds" / "embodied_sensorimotor_core.json").read_text(
            encoding="utf-8"
        )
    )
    assert "hierarchical_effector_control" in core["depends_on"]


def test_nested_overlapping_subsections_unroll_exact_program_assignments():
    agent = WorldAdapter(seeds=("hierarchical_effector_control",))
    topology, effectors, singleton = _body(agent)

    limb_1 = _scope(agent, topology, "limb_1", [singleton[effectors[0]]])
    limb_2 = _scope(agent, topology, "limb_2", [singleton[effectors[1]]])
    limb_3 = _scope(agent, topology, "limb_3", [singleton[effectors[2]]])
    limb_5 = _scope(agent, topology, "limb_5", [singleton[effectors[4]]])
    limbs_2_3_5 = _scope(
        agent, topology, "limbs_2_3_5", [limb_2, limb_3, limb_5]
    )

    quux = agent.s.add_node("MotorProgram", {"token": "QUUX"})
    foo = agent.s.add_node("MotorProgram", {"token": "FOO"})
    bar = agent.s.add_node("MotorProgram", {"token": "BAR"})
    program = agent.s.add_node("EmbodiedHierarchicalControlProgram", {
        "token": "A",
        "status": "assembling",
    })
    _edge(agent, agent.agent, "has_embodied_hierarchical_control_program", program)
    _binding(agent, program, limb_1, quux)
    _binding(agent, program, limb_2, foo)
    _binding(agent, program, limbs_2_3_5, bar)

    assert agent.tick() > 0
    assert agent.s.node(program)["attrs"]["status"] == "ready"
    assert agent.s.node(program)["attrs"]["binding_count"] == 3
    assert agent.s.node(program)["attrs"]["assignment_count"] == 5

    assignments = agent.s.neighbours(
        program, "has_embodied_effector_program_assignment"
    )
    actual = set()
    for assignment in assignments:
        effector = agent.s.neighbours(assignment, "targets_embodied_effector")
        child = agent.s.neighbours(
            assignment, "invokes_embodied_child_motor_program"
        )
        assert len(effector) == len(child) == 1
        actual.add((
            agent.s.node(effector[0])["attrs"]["ordinal"],
            agent.s.node(child[0])["attrs"]["token"],
        ))
    assert actual == {
        (0, "QUUX"),
        (1, "FOO"),
        (1, "BAR"),
        (2, "BAR"),
        (4, "BAR"),
    }


def test_direct_mechanical_topology_exposes_each_rooted_distal_subsection():
    agent = WorldAdapter(seeds=("hierarchical_effector_control",))
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    effectors = []
    for ordinal, depth in enumerate((1, 2, 3)):
        effector = agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "channel_ordinal": ordinal,
            "mount_depth": depth,
        })
        effectors.append(effector)
        _edge(agent, topology, "has_embodied_effector", effector)
    for ordinal, (source, target) in enumerate(zip(effectors, effectors[1:])):
        relation = agent.s.add_node("EmbodiedEffectorRelation", {
            "ordinal": ordinal,
            "mechanical_path_known": 1,
            "mechanical_path_length": 1,
        })
        _edge(agent, topology, "has_embodied_effector_relation", relation)
        _edge(agent, relation, "has_embodied_effector_source", source)
        _edge(agent, relation, "has_embodied_effector_target", target)

    assert agent.tick() > 0
    rooted = {}
    for scope in agent.s.neighbours(topology, "has_embodied_control_subsection"):
        if agent.s.node(scope)["attrs"].get("scope_kind") != "rooted_subsection":
            continue
        root = agent.s.neighbours(scope, "rooted_at_embodied_effector")
        assert len(root) == 1
        rooted[root[0]] = scope

    assert set(rooted) == set(effectors)
    assert set(agent.s.neighbours(
        rooted[effectors[0]], "addresses_embodied_effector"
    )) == set(effectors)
    assert set(agent.s.neighbours(
        rooted[effectors[1]], "addresses_embodied_effector"
    )) == set(effectors[1:])
    assert agent.s.neighbours(
        rooted[effectors[2]], "addresses_embodied_effector"
    ) == [effectors[2]]


def test_immutable_topology_closes_static_builders_but_keeps_new_scopes_live():
    agent = WorldAdapter(seeds=("hierarchical_effector_control",))
    episode = agent.s.add_node("HumanoidEpisode", {})
    topology = agent.s.add_node("EmbodiedEffectorTopology", {
        "effector_count": 2,
        "relation_count": 1,
        "topology_facts_complete": 1,
    })
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    effectors = []
    for ordinal in range(2):
        effector = agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "mount_depth": ordinal,
        })
        effectors.append(effector)
        _edge(agent, topology, "has_embodied_effector", effector)
    relation = agent.s.add_node("EmbodiedEffectorRelation", {
        "mechanical_path_known": 1,
        "mechanical_path_length": 1,
    })
    _edge(agent, topology, "has_embodied_effector_relation", relation)
    _edge(agent, relation, "has_embodied_effector_source", effectors[0])
    _edge(agent, relation, "has_embodied_effector_target", effectors[1])

    assert agent.tick() > 0
    assert agent.s.node(topology)["attrs"]["subsection_hierarchy_ready"] == 1

    rooted = next(
        scope for scope in agent.s.neighbours(
            topology, "has_embodied_control_subsection"
        )
        if agent.s.node(scope)["attrs"].get("scope_kind") == "rooted_subsection"
        and agent.s.neighbours(scope, "rooted_at_embodied_effector")
        == [effectors[0]]
    )
    learned = _scope(agent, topology, "later_learned_scope", [rooted])
    assert agent.tick() > 0
    assert set(agent.s.neighbours(
        learned, "addresses_embodied_effector"
    )) == set(effectors)


def test_overlap_without_explicit_superposition_fails_closed():
    agent = WorldAdapter(seeds=("hierarchical_effector_control",))
    topology, effectors, singleton = _body(agent, width=1)
    scope = _scope(agent, topology, "one_part", [singleton[effectors[0]]])
    first = agent.s.add_node("MotorProgram", {"token": "FIRST"})
    second = agent.s.add_node("MotorProgram", {"token": "SECOND"})
    program = agent.s.add_node("EmbodiedHierarchicalControlProgram", {
        "token": "ambiguous",
        "status": "assembling",
    })
    _edge(agent, agent.agent, "has_embodied_hierarchical_control_program", program)
    _binding(agent, program, scope, first, operator="superpose")
    _binding(agent, program, scope, second, operator="exclusive")

    assert agent.tick() > 0
    attrs = agent.s.node(program)["attrs"]
    assert attrs["status"] == "rejected"
    assert attrs["rejection_reason"] == "unresolved_effector_overlap"
    assert agent.s.neighbours(
        program, "has_conflicting_embodied_effector"
    ) == [effectors[0]]
