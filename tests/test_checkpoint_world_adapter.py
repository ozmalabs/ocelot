from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter, capture_adopted_checkpoint,
    capture_held_process_checkpoint,
)
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate, execute_open_process_candidate,
)
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world, generate_loopover_world, p22_seed,
)
from evaluation.process_mastery.harness import Agent
from tests.test_open_process_search import _compose
from tests.test_open_process_adoption import _agent as _adoption_agent, _approve, _candidate, _tick


def _adapter():
    agent = Agent(track_i=False)
    return agent, CheckpointWorldAdapter(agent.native, primitive_work_ceiling=8,
                                        allow_unattested_fixtures=True)


def _checkpoints(agent, *, full_work=2, ancestor_work=2):
    left, right = [1, 0, 2, 3], [0, 2, 1, 3]
    full = CheckpointExpression("full-g1", "ancestor", "expr-full",
                                tuple(_compose(agent, left, right)), full_work)
    ancestor = CheckpointExpression("ancestor", "ancestor", "expr-ancestor",
                                    tuple(left), ancestor_work)
    return full, ancestor


def test_all_arms_same_world_and_compute():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    adaptive = CheckpointExpression("adaptive", "ancestor", "expr-adaptive",
                                    full.params, 2)
    invention = CheckpointExpression("invention", "ancestor", "expr-invention",
                                     full.params, 2)
    worlds = [{"world_id": f"world-{i}", "initial_state": [0, 1, 2, 3],
               "goal_state": [1, 2, 0, 3]} for i in range(3)]
    result = adapter.compare((ancestor, adaptive, invention, full), worlds)
    assert result["same_worlds"]
    assert result["efficiency_comparable"]
    assert all([x["world_id"] for x in row["outcomes"]] == [row["world_id"]] * 4
               for row in result["rows"])


def test_efficiency_uses_cumulative_lineage_work_and_ceiling():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent, full_work=2, ancestor_work=2)
    costly_full = CheckpointExpression("full-g3", "parent", "expr-full",
        full.params, 2, generation=3, cumulative_primitive_work=9)
    low_cost_ancestor = CheckpointExpression("ancestor-g3", "parent", "expr-ancestor",
        ancestor.params, 2, generation=3, cumulative_primitive_work=6)
    world = {"world_id": "same-world", "initial_state": [0, 1, 2, 3],
             "goal_state": [1, 2, 0, 3]}
    result = adapter.compare((low_cost_ancestor, costly_full), [world])
    assert not result["efficiency_comparable"]
    assert [outcome["status"] for outcome in result["rows"][0]["outcomes"]] == [
        "scored", "work_denied"]
    assert result["rows"][0]["outcomes"][1]["cumulative_primitive_work"] == 9


def test_comparison_rejects_vacuous_panels_and_duplicate_checkpoint_ids():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    try:
        adapter.compare((ancestor, full), [])
    except ValueError as exc:
        assert "at least one common world" in str(exc)
    else:
        raise AssertionError("empty world panel was accepted")
    duplicate = CheckpointExpression(full.checkpoint_id, "ancestor", "other",
                                     full.params, 2)
    try:
        adapter.compare((ancestor, full, duplicate), [{
            "world_id": "one", "initial_state": [0, 1, 2, 3],
            "goal_state": [1, 2, 0, 3]}])
    except ValueError as exc:
        assert "identities must be unique" in str(exc)
    else:
        raise AssertionError("duplicate checkpoint identity was accepted")


def test_scoring_rejects_malformed_permutations_and_negative_work():
    agent, adapter = _adapter()
    world = {"world_id": "valid", "initial_state": [0, 1, 2, 3],
             "goal_state": [1, 2, 0, 3]}
    malformed = CheckpointExpression("bad-permutation", "ancestor", "bad",
                                     (0, 1, 1, 3), 1)
    try:
        adapter.score(malformed, **world)
    except ValueError as exc:
        assert "finite permutation" in str(exc)
    else:
        raise AssertionError("malformed process was scored as an ordinary failure")
    negative_cost = CheckpointExpression("negative-work", "ancestor", "valid",
                                         (0, 1, 2, 3), -1)
    try:
        adapter.score(negative_cost, **world)
    except ValueError as exc:
        assert "nonnegative integer" in str(exc)
    else:
        raise AssertionError("negative declared work was accepted")


def test_changed_active_expression_changes_scored_result():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    world = {"world_id": "same", "initial_state": [0, 1, 2, 3],
             "goal_state": [1, 2, 0, 3]}
    assert adapter.score(full, **world)["score"] == 1
    assert adapter.score(ancestor, **world)["score"] == 0


def test_p22_state_perturbation_changes_execution():
    agent, adapter = _adapter()
    full, _ancestor = _checkpoints(agent)
    base = {"world_id": "same-world", "initial_state": [0, 1, 2, 3],
            "goal_state": [1, 2, 0, 3]}
    perturbed = {**base, "initial_state": [3, 2, 1, 0]}
    assert adapter.score(full, **base)["result_state"] == base["goal_state"]
    assert adapter.score(full, **perturbed)["result_state"] != perturbed["goal_state"]


def test_checkpoint_restore_no_state_leak():
    agent, adapter = _adapter()
    full, ancestor = _checkpoints(agent)
    initial = [0, 1, 2, 3]
    world = {"world_id": "isolated", "initial_state": initial,
             "goal_state": [1, 2, 0, 3]}
    first = adapter.score(full, **world)
    second = adapter.score(full, **world)
    assert first == second
    assert initial == [0, 1, 2, 3]


def test_d4_worlds_are_fixed_across_checkpoints_and_not_answer_leaking():
    train = generate_d4_world(split="train", draw=4)
    repeated = generate_d4_world(split="train", draw=4)
    heldout = generate_d4_world(split="heldout", draw=4)
    assert train == repeated
    assert train["world_id"] == agent_view(train)["world_id"]
    assert "hidden_transform_order" not in agent_view(train)
    assert "hidden_target_params" not in agent_view(train)
    assert train["seed"] != heldout["seed"]
    assert p22_seed(family_code=2, split="train", draw=4) == train["seed"]


def test_d4_goal_matches_native_process_composition():
    agent, adapter = _adapter()
    world = generate_d4_world(split="train", draw=9)
    first, second = world["hidden_transform_order"]
    left = world["held_processes"][first]
    right = world["held_processes"][second]
    composed = agent.native.evaluate(
        {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
         "b": {"type": "Var", "name": "b"}}, {"a": left, "b": right})
    checkpoint = CheckpointExpression("d4-composed", "ancestor", "d4-expression",
                                      tuple(composed), 2)
    scored = adapter.score(checkpoint, world_id=world["world_id"],
                           initial_state=world["initial_state"],
                           goal_state=world["goal_state"])
    assert scored["score"] == 1


def test_loopover_goal_matches_native_process_composition():
    agent, adapter = _adapter()
    world = generate_loopover_world(split="train", draw=11)
    first, second = world["hidden_transform_order"]
    composed = agent.native.evaluate(
        {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
         "b": {"type": "Var", "name": "b"}},
        {"a": world["held_processes"][first],
         "b": world["held_processes"][second]})
    checkpoint = CheckpointExpression("loopover-composed", "ancestor",
                                      "loopover-expression", tuple(composed), 2)
    scored = adapter.score(checkpoint, world_id=world["world_id"],
                           initial_state=world["initial_state"],
                           goal_state=world["goal_state"])
    assert scored["score"] == 1
    assert len(world["initial_state"]) == 9


def test_development_world_panels_are_not_at_common_solver_ceiling():
    # This is a development-only ceiling audit. It shows only that the fixed
    # world generators do not make every task trivial for the unchanged native
    # solver; it makes no claim about adaptive or invented-process benefit.
    from evaluation.process_mastery.harness import Agent

    observed = {}
    for family, generator in (("d4", generate_d4_world),
                              ("loopover", generate_loopover_world)):
        agent = Agent(track_i=False, extra_seeds=("process_solving",))
        try:
            for policy in agent.nodes("SolverPolicy"):
                agent.s.set_attr(policy, "enabled", 1.0)
            tasks = []
            for draw in range(32):
                world = generator(split="train", draw=draw)
                domain_name = f"p22-ceiling-audit:{family}:{draw:04d}"
                domain = agent.add_domain(domain_name, "permutation",
                    [world["initial_state"]], world["held_processes"])
                for schema in agent.nodes("ProcessSchema"):
                    if agent.attrs(schema).get("domain") == domain_name:
                        agent.s.add_edge(domain, "has_held_process", schema, {})
                tasks.append(agent.add_solve_task(domain_name,
                    world["initial_state"], world["goal_state"]))
            result = agent.run(max_ticks=300)
            assert result["quiescent"]
            statuses = [agent.attrs(task)["status"] for task in tasks]
            assert all(status in {"solved", "stuck"} for status in statuses)
            assert any(status != "solved" for status in statuses)
            observed[family] = sum(status == "solved" for status in statuses)
        finally:
            del agent
    assert observed == {"d4": 0, "loopover": 11}


def test_checkpoint_capture_requires_consumed_exact_approval_and_receipt():
    agent = _adoption_agent()
    candidate = _candidate(agent)
    parent = capture_held_process_checkpoint(agent, agent.schemas("search")[0],
        checkpoint_id="held-ancestor")
    try:
        capture_adopted_checkpoint(agent, 999999, checkpoint_id="invalid-generation",
            parent=parent, generation=2, declared_primitive_work=2)
    except ValueError as exc:
        assert "immediate parent" in str(exc)
    else:
        raise AssertionError("skipped generation was accepted")
    digest = attest_open_process_candidate(agent, candidate)
    _approve(agent, candidate)
    _tick(agent)
    assert agent.attrs(candidate)["status"] == "adopted_candidate"
    state = agent.attrs(candidate)["guard_state"]
    predicted = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": agent.attrs(candidate)["params"], "state": state})
    result = execute_open_process_candidate(agent, candidate, state=state,
        authorize=lambda proposal: proposal["expression_digest"] == digest,
        world_transition=lambda action: {"observed_state": predicted})
    assert result["status"] == "COMPLETED"
    checkpoint = capture_adopted_checkpoint(agent, candidate,
        checkpoint_id="generation-1", parent=parent,
        generation=1, declared_primitive_work=2)
    assert checkpoint.generation == 1
    assert checkpoint.parent_digest == parent.checkpoint_digest
    assert checkpoint.approval_id is not None and checkpoint.receipt_id is not None
    assert checkpoint.resource_snapshot_json is not None
    before = checkpoint.checkpoint_digest
    original_params = checkpoint.params
    changed = list(agent.attrs(candidate)["params"])
    changed[0], changed[1] = changed[1], changed[0]
    agent.s.set_attr(candidate, "params", changed)
    assert checkpoint.params == original_params
    assert checkpoint.checkpoint_digest == before
    strict_adapter = CheckpointWorldAdapter(agent.native, primitive_work_ceiling=8)
    world = {"world_id": "frozen", "initial_state": state, "goal_state": predicted}
    scored = strict_adapter.score(checkpoint, **world)
    assert scored["status"] == "scored"
    assert scored["resource_snapshot"]["snapshot_sha256"]
    tampered = CheckpointExpression(checkpoint.checkpoint_id, checkpoint.parent_digest,
        checkpoint.expression_digest, tuple(changed), checkpoint.declared_primitive_work,
        checkpoint.generation, checkpoint.checkpoint_digest, checkpoint.approval_id,
        checkpoint.receipt_id, checkpoint.cumulative_primitive_work,
        checkpoint.resource_snapshot_json)
    try:
        strict_adapter.score(tampered, **world)
    except ValueError as exc:
        assert "attested" in str(exc)
    else:
        raise AssertionError("tampered checkpoint passed strict scoring")
    forged_parent = CheckpointExpression(parent.checkpoint_id, parent.parent_digest,
        parent.expression_digest, parent.params, parent.declared_primitive_work,
        parent.generation, "forged-digest")
    try:
        capture_adopted_checkpoint(agent, candidate, checkpoint_id="forged-child",
            parent=forged_parent, generation=1, declared_primitive_work=2)
    except ValueError as exc:
        assert "immediate parent" in str(exc)
    else:
        raise AssertionError("child checkpoint accepted an unattested parent")
    try:
        capture_adopted_checkpoint(agent, candidate, checkpoint_id="generation-1b",
            parent=checkpoint, generation=2,
            declared_primitive_work=2)
    except ValueError as exc:
        assert "expression" in str(exc)
    else:
        raise AssertionError("mutated candidate was captured as an approved checkpoint")
