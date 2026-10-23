import json
import hashlib

import pytest

from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter, capture_adopted_checkpoint,
    capture_held_process_checkpoint, capture_passive_checkpoint,
    compare_restored_checkpoint_panel, restore_native_checkpoint_graph,
    score_restored_checkpoint_task,
)
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate, execute_open_process_candidate, params_digest,
)
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world, generate_d4_world_v2,
    generate_loopover_world, generate_loopover_world_v2, p22_seed,
)
from evaluation.process_mastery.harness import Agent
from tests.test_open_process_search import _compose
from tests.test_open_process_adoption import _agent as _adoption_agent, _approve, _candidate, _tick


def _native_rule_work(term_evaluations):
    value = {"schema": "p22_native_rule_work_v1", "store_instance_id": 1,
        "rules": [], "rule_identity_coverage": "COMPLETE",
        "unresolved_rule_indices": [],
        "totals_by_metric": {"term_evaluations": term_evaluations}}
    value["snapshot_sha256"] = hashlib.sha256(json.dumps(value,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return value


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
    for family, generator in (("d4", generate_d4_world_v2),
                              ("loopover", generate_loopover_world_v2)):
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
    assert observed == {"d4": 14, "loopover": 6}


def test_v2_world_generators_have_disjoint_splits_and_varied_independent_goals():
    for family, generator, expected_unique in (
            ("d4", generate_d4_world_v2, (8, 8)),
            ("loopover", generate_loopover_world_v2, (190, 195))):
        train = [generator(split="train", draw=i) for i in range(200)]
        validation = [generator(split="validation", draw=i) for i in range(200)]
        train_ids = {world["world_id"] for world in train}
        validation_ids = {world["world_id"] for world in validation}
        train_seeds = {world["seed"] for world in train}
        validation_seeds = {world["seed"] for world in validation}
        train_goals = {tuple(world["goal_state"]) for world in train}
        validation_goals = {tuple(world["goal_state"]) for world in validation}
        assert len(train_ids) == len(validation_ids) == 200
        assert train_ids.isdisjoint(validation_ids)
        assert train_seeds.isdisjoint(validation_seeds)
        assert (len(train_goals), len(validation_goals)) == expected_unique
        assert all("hidden_target_params" not in agent_view(world)
                   and "hidden_transform_order" not in agent_view(world)
                   for world in train + validation)


def test_v2_generated_goals_match_native_composition_without_exposing_order():
    agent, adapter = _adapter()
    for generator in (generate_d4_world_v2, generate_loopover_world_v2):
        world = generator(split="train", draw=19)
        composed = list(range(len(world["initial_state"])))
        for name in world["hidden_transform_order"]:
            composed = agent.native.evaluate(
                {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
                 "b": {"type": "Var", "name": "b"}},
                {"a": composed, "b": world["held_processes"][name]})
        scored = adapter.score(CheckpointExpression("v2-world-control", "ancestor",
            "v2-composition", tuple(composed), 1), world_id=world["world_id"],
            initial_state=world["initial_state"], goal_state=world["goal_state"])
        assert scored["score"] == 1
        visible = agent_view(world)
        assert "hidden_transform_order" not in visible
        assert "hidden_target_params" not in visible


def test_checkpoint_capture_requires_consumed_exact_approval_and_receipt():
    agent = _adoption_agent()
    candidate = _candidate(agent)
    parent = capture_held_process_checkpoint(agent, agent.schemas("search")[0],
        checkpoint_id="held-ancestor",
        runtime_counters={"native_rule_steps": 12, "native_model_calls": 0,
                          "process_peak_rss_bytes": 64_000_000},
        native_rule_work=_native_rule_work(10))
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
        generation=1, declared_primitive_work=2,
        runtime_counters={"native_rule_steps": 48, "native_model_calls": 0,
                          "process_peak_rss_bytes": 65_000_000},
        native_rule_work=_native_rule_work(20))
    assert checkpoint.generation == 1
    assert checkpoint.parent_digest == parent.checkpoint_digest
    assert checkpoint.approval_id is not None and checkpoint.receipt_id is not None
    assert checkpoint.resource_snapshot_json is not None
    graph_adapter = CheckpointWorldAdapter(agent.native, primitive_work_ceiling=8)
    common_world = {"world_id": "native-checkpoint-causal-control",
        "initial_state": state, "goal_state": predicted}
    ancestor_outcome = graph_adapter.score(parent, **common_world)
    learned_outcome = graph_adapter.score(checkpoint, **common_world)
    assert ancestor_outcome["execution_source"] == "native_checkpoint_graph"
    assert learned_outcome["execution_source"] == "native_checkpoint_graph"
    assert (ancestor_outcome["score"], learned_outcome["score"]) == (0, 1)
    checkpoint_resources = json.loads(checkpoint.resource_snapshot_json)
    assert checkpoint_resources["runtime_counters"] == {
        "native_rule_steps": 48, "native_model_calls": 0,
        "process_peak_rss_bytes": 65_000_000}
    assert checkpoint_resources["native_rule_work"]["totals_by_metric"][
        "term_evaluations"] == 20
    try:
        capture_adopted_checkpoint(agent, candidate,
            checkpoint_id="generation-1-regressed", parent=parent,
            generation=1, declared_primitive_work=2,
            runtime_counters={"native_rule_steps": 11, "native_model_calls": 0,
                              "process_peak_rss_bytes": 65_000_000})
    except ValueError as exc:
        assert "runtime counter regressed" in str(exc)
    else:
        raise AssertionError("descendant checkpoint accepted regressed runtime work")
    try:
        capture_adopted_checkpoint(agent, candidate,
            checkpoint_id="generation-1-rule-work-regressed", parent=parent,
            generation=1, declared_primitive_work=2,
            runtime_counters={"native_rule_steps": 48, "native_model_calls": 0,
                              "process_peak_rss_bytes": 65_000_000},
            native_rule_work=_native_rule_work(9))
    except ValueError as exc:
        assert "native rule work regressed" in str(exc)
    else:
        raise AssertionError("descendant checkpoint accepted regressed native rule work")
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
    assert scored["execution_source"] == "native_checkpoint_graph"
    assert scored["result_state"] == predicted
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


def test_passive_control_checkpoint_advances_without_adoption_evidence():
    agent = _adoption_agent()
    try:
        agent.add_domain("search", "permutation", [[0, 1, 2, 3]],
                         {"p": [1, 0, 2, 3]})
        parent = capture_held_process_checkpoint(agent,
            agent.schemas("search")[0], checkpoint_id="passive-root",
            runtime_counters={"native_rule_steps": 10, "native_model_calls": 0},
            native_rule_work=_native_rule_work(10))
        child = capture_passive_checkpoint(agent, checkpoint_id="passive-g1",
            parent=parent, generation=1, declared_primitive_work=0,
            runtime_counters={"native_rule_steps": 12, "native_model_calls": 0},
            native_rule_work=_native_rule_work(12))
        assert child.parent_digest == parent.checkpoint_digest
        assert child.generation == 1
        assert child.expression_digest == parent.expression_digest
        assert child.params == parent.params
        assert child.approval_id is None and child.receipt_id is None
        assert CheckpointWorldAdapter._checkpoint_digest_valid(child)
        child_snapshot = json.loads(child.resource_snapshot_json)
        assert child_snapshot["runtime_counters"]["native_rule_steps"] == 12
        assert child_snapshot["native_rule_work"]["totals_by_metric"][
            "term_evaluations"] == 12
        adapter = CheckpointWorldAdapter(agent.native, primitive_work_ceiling=10)
        result = adapter.score(child, world_id="passive-control",
            initial_state=list(range(len(child.params))),
            goal_state=list(range(len(child.params))))
        assert result["status"] == "scored"
        with pytest.raises(ValueError, match="runtime counter regressed"):
            capture_passive_checkpoint(agent, checkpoint_id="passive-g2-runtime-regressed",
                parent=child, generation=2, declared_primitive_work=0,
                runtime_counters={"native_rule_steps": 11, "native_model_calls": 0},
                native_rule_work=_native_rule_work(13))
        with pytest.raises(ValueError, match="native rule work regressed"):
            capture_passive_checkpoint(agent, checkpoint_id="passive-g2-work-regressed",
                parent=child, generation=2, declared_primitive_work=0,
                runtime_counters={"native_rule_steps": 13, "native_model_calls": 0},
                native_rule_work=_native_rule_work(11))
        try:
            capture_passive_checkpoint(agent, checkpoint_id="passive-g3",
                parent=child, generation=3, declared_primitive_work=0)
        except ValueError as exc:
            assert "one generation" in str(exc)
        else:
            raise AssertionError("passive checkpoint skipped a generation")
    finally:
        del agent


def test_checkpoint_captures_and_restores_exact_native_graph_snapshot():
    source = _adoption_agent()
    restored = _adoption_agent()
    try:
        source.add_domain("snapshot", "permutation", [[0, 1, 2, 3]],
                          {"swap": [1, 0, 2, 3]})
        checkpoint = capture_held_process_checkpoint(source,
            source.schemas("snapshot")[0], checkpoint_id="graph-snapshot-root")
        frozen_graph = checkpoint.native_graph_snapshot_json
        assert frozen_graph is not None
        assert json.loads(frozen_graph) == source.native.graph_to_dict()
        assert CheckpointWorldAdapter._checkpoint_digest_valid(checkpoint)

        source.s.add_node("PostCheckpointMutation", {"value": 1.0})
        assert checkpoint.native_graph_snapshot_json == frozen_graph
        digest = restore_native_checkpoint_graph(restored, checkpoint)
        assert restored.native.graph_to_dict() == json.loads(frozen_graph)
        assert digest == hashlib.sha256(frozen_graph.encode()).hexdigest()

        tampered = CheckpointExpression(**(
            checkpoint.__dict__ | {"native_graph_snapshot_json": frozen_graph + " "}))
        with pytest.raises(ValueError, match="unattested"):
            restore_native_checkpoint_graph(restored, tampered)
    finally:
        for agent in (source, restored):
            close = getattr(agent.s, "close", None)
            if callable(close):
                close()


def test_restored_checkpoint_runs_fresh_task_through_native_learner():
    from substrate.boot_profiles import boot_cognition_on

    world = agent_view(generate_d4_world_v2(split="train", draw=15))
    source = boot_cognition_on()
    for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
        for policy in source.s.nodes(policy_type):
            source.s.set_attr(policy, "enabled", 1.0)
    domain = source.s.add_node("ProcessDomain", {"name": "checkpoint-root",
        "kind": "permutation", "domain_kind": "permutation",
        "probes": [world["initial_state"]],
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_domain", domain, {})
    params = world["held_processes"]["rot90"]
    schema = source.s.add_node("ProcessSchema", {"name": "rot90", "kind": "permutation",
        "domain": "checkpoint-root", "domain_kind": "permutation",
        "params": params, "source_digest": params_digest(params),
        "status": "active", "provenance": "held", "cost": 1.0,
        "owner_agent": source.agent, "invariants": [],
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_schema", schema, {})
    source.s.add_edge(domain, "has_held_process", schema, {})
    checkpoint = capture_held_process_checkpoint(source,
        schema, checkpoint_id="learner-root")

    def boot():
        agent = boot_cognition_on()
        for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
            for policy in agent.s.nodes(policy_type):
                agent.s.set_attr(policy, "enabled", 1.0)
        return agent

    result = score_restored_checkpoint_task(checkpoint,
        world=world, agent_factory=boot)
    assert result["status"] == "COMPLETED"
    assert result["task_status"] == "solved"
    assert result["score"] == 1
    assert result["quiescent"]
    assert result["approval_events_added"] == result["world_receipts_added"] == 0

    heldout_fixture = dict(world, split="heldout",
        world_id="fixture:d4:heldout:rejected")
    with pytest.raises(ValueError, match="registered scoring split"):
        score_restored_checkpoint_task(checkpoint, world=heldout_fixture,
                                      agent_factory=boot)
    bounded = score_restored_checkpoint_task(checkpoint, world=world,
        agent_factory=boot, cumulative_primitive_ceiling=1,
        native_rule_progress_ceiling=20_000)
    assert bounded["cumulative_primitive_ceiling"] == 1
    assert bounded["primitive_budget_respected"]
    assert bounded["cumulative_primitive_work"] <= 1
    over_budget = capture_held_process_checkpoint(source, schema,
        checkpoint_id="over-budget-root", declared_primitive_work=2)
    with pytest.raises(ValueError, match="exceeds the shared primitive ceiling"):
        score_restored_checkpoint_task(over_budget, world=world,
            agent_factory=lambda: pytest.fail("over-budget checkpoint was booted"),
            cumulative_primitive_ceiling=1)


def test_shared_scoring_profile_enables_fixed_solver_for_lineage_checkpoint():
    from substrate.boot_profiles import boot_cognition_on

    world = agent_view(generate_d4_world_v2(split="train", draw=15))
    source = boot_cognition_on()
    try:
        domain = source.s.add_node("ProcessDomain", {"name": "lineage-root",
            "kind": "permutation", "domain_kind": "permutation",
            "probes": [world["initial_state"]], "source_epoch": 0,
            "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0})
        source.s.add_edge(source.agent, "has_process_domain", domain, {})
        params = world["held_processes"]["rot90"]
        schema = source.s.add_node("ProcessSchema", {
            "name": "rot90", "kind": "permutation", "domain": "lineage-root",
            "domain_kind": "permutation", "params": params,
            "source_digest": params_digest(params), "status": "active",
            "provenance": "held", "cost": 1.0, "owner_agent": source.agent,
            "invariants": [], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "probe_epoch": 0})
        source.s.add_edge(source.agent, "has_process_schema", schema, {})
        source.s.add_edge(domain, "has_held_process", schema, {})
        checkpoint = capture_held_process_checkpoint(source, schema,
            checkpoint_id="lineage-root-disabled-solver")
        digest = checkpoint.checkpoint_digest
    finally:
        source.close()

    result = score_restored_checkpoint_task(checkpoint, world=world,
        agent_factory=boot_cognition_on,
        scoring_policy_profile="p22_frozen_process_scoring_v1")
    assert result["status"] == "COMPLETED"
    assert result["score"] == 1
    assert result["scoring_policy_profile"] == "p22_frozen_process_scoring_v1"
    assert result["disabled_scoring_policies"]["OpenProcessSearchPolicy"] >= 1
    assert result["disabled_scoring_policies"]["OpenProcessAdoptionPolicy"] >= 1
    assert checkpoint.checkpoint_digest == digest


def test_restored_checkpoint_stops_before_unaffordable_primitive_action():
    from substrate.boot_profiles import boot_cognition_on

    world = agent_view(generate_d4_world_v2(split="train", draw=15))
    source = boot_cognition_on()
    try:
        domain = source.s.add_node("ProcessDomain", {"name": "work-budget-root",
            "kind": "permutation", "domain_kind": "permutation",
            "probes": [world["initial_state"]], "source_epoch": 0,
            "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0})
        source.s.add_edge(source.agent, "has_process_domain", domain, {})
        params = world["held_processes"]["rot90"]
        schema = source.s.add_node("ProcessSchema", {
            "name": "rot90", "kind": "permutation", "domain": "work-budget-root",
            "domain_kind": "permutation", "params": params,
            "source_digest": params_digest(params), "status": "active",
            "provenance": "held", "cost": 10.0, "owner_agent": source.agent,
            "invariants": [], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "probe_epoch": 0})
        source.s.add_edge(source.agent, "has_process_schema", schema, {})
        source.s.add_edge(domain, "has_held_process", schema, {})
        checkpoint = capture_held_process_checkpoint(source, schema,
            checkpoint_id="work-budget-root")
    finally:
        source.close()

    result = score_restored_checkpoint_task(checkpoint, world=world,
        agent_factory=boot_cognition_on, cumulative_primitive_ceiling=1,
        scoring_policy_profile="p22_frozen_process_scoring_v1")
    assert result["status"] == "COMPLETED"
    assert result["task_status"] == "budget_exhausted"
    assert result["score"] == 0
    assert result["primitive_budget_respected"]
    assert result["cumulative_primitive_work"] <= 1


def test_heldout_learner_scoring_keeps_assigned_world_out_of_training(monkeypatch):
    from substrate.boot_profiles import boot_cognition_on
    from evaluation.process_mastery import checkpoint_world_adapter as adapter_module

    train_world = agent_view(generate_d4_world_v2(split="train", draw=16))
    heldout_fixture = dict(train_world, split="heldout",
        world_id="fixture:d4:heldout:score")
    monkeypatch.setattr(adapter_module, "generate_d4_world_v2",
        lambda *, split, draw: heldout_fixture if split == "heldout"
        else generate_d4_world_v2(split=split, draw=draw))

    source = boot_cognition_on()
    for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
        for policy in source.s.nodes(policy_type):
            source.s.set_attr(policy, "enabled", 1.0)
    domain = source.s.add_node("ProcessDomain", {"name": "heldout-checkpoint",
        "kind": "permutation", "domain_kind": "permutation",
        "probes": [train_world["initial_state"]], "source_epoch": 0,
        "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_domain", domain, {})
    params = train_world["held_processes"]["rot90"]
    schema = source.s.add_node("ProcessSchema", {"name": "rot90",
        "kind": "permutation", "domain": "heldout-checkpoint",
        "domain_kind": "permutation", "params": params,
        "source_digest": params_digest(params), "status": "active",
        "provenance": "held", "cost": 1.0, "owner_agent": source.agent,
        "invariants": [], "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_schema", schema, {})
    source.s.add_edge(domain, "has_held_process", schema, {})
    checkpoint = capture_held_process_checkpoint(source, schema,
        checkpoint_id="heldout-scoring-root")

    def boot():
        agent = boot_cognition_on()
        for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
            for policy in agent.s.nodes(policy_type):
                agent.s.set_attr(policy, "enabled", 1.0)
        return agent

    result = score_restored_checkpoint_task(checkpoint,
        world=agent_view(heldout_fixture), agent_factory=boot,
        allow_heldout_evaluation=True)
    assert result["split"] == "heldout"
    assert result["status"] == "COMPLETED"
    assert result["task_status"] in {"solved", "stuck"}
    assert result["score"] == int(result["task_status"] == "solved")
    assert result["native_rule_steps"] > 0
    assert result["resource_snapshot"]["cumulative_resources"].get(
        "training_evidence_exposures", 0) == 0
    assert result["resource_snapshot"]["cumulative_resources"].get(
        "training_task_exposures", 0) == 0
    assert result["approval_events_added"] == result["world_receipts_added"] == 0


def test_four_restored_checkpoints_share_registered_world_and_rule_ceiling():
    from substrate.boot_profiles import boot_cognition_on

    world = agent_view(generate_d4_world_v2(split="train", draw=15))
    source = boot_cognition_on()
    for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
        for policy in source.s.nodes(policy_type):
            source.s.set_attr(policy, "enabled", 1.0)
    domain = source.s.add_node("ProcessDomain", {"name": "checkpoint-panel",
        "kind": "permutation", "domain_kind": "permutation",
        "probes": [world["initial_state"]], "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_domain", domain, {})
    params = world["held_processes"]["rot90"]
    schema = source.s.add_node("ProcessSchema", {"name": "rot90",
        "kind": "permutation", "domain": "checkpoint-panel",
        "domain_kind": "permutation", "params": params,
        "source_digest": params_digest(params), "status": "active",
        "provenance": "held", "cost": 1.0, "owner_agent": source.agent,
        "invariants": [], "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_schema", schema, {})
    source.s.add_edge(domain, "has_held_process", schema, {})
    checkpoints = {name: capture_held_process_checkpoint(source, schema,
        checkpoint_id=f"panel-{name}") for name in
        ("unchanged", "adaptive_only", "invention_only", "full")}

    def boot():
        agent = boot_cognition_on()
        for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
            for policy in agent.s.nodes(policy_type):
                agent.s.set_attr(policy, "enabled", 1.0)
        return agent

    result = compare_restored_checkpoint_panel(checkpoints, [world],
        agent_factory=boot, native_rule_progress_ceiling=20_000,
        cumulative_primitive_ceiling=30_000)
    assert result["same_worlds"]
    assert result["same_native_rule_progress_ceiling"]
    assert result["primitive_budgets_respected"]
    assert result["same_cumulative_primitive_work"]
    assert all(result["arms"][arm]["solved_count"] == 1 for arm in checkpoints)
    assert all(result["arms"][arm]["approval_events_added"] == 0
               and result["arms"][arm]["world_receipts_added"] == 0
               for arm in checkpoints)
    assert not result["efficacy_established"]


def test_restored_adaptive_checkpoint_uses_native_curriculum_evidence_path():
    from substrate.boot_profiles import boot_cognition_on

    world = agent_view(generate_d4_world_v2(split="train", draw=15))
    source = boot_cognition_on()
    for policy_type in ("SolverPolicy", "ProcessSchemaPolicy",
                        "ProcessCurriculumPolicy",
                        "IndependentImprovementCurriculumBridgePolicy"):
        for policy in source.s.nodes(policy_type):
            source.s.set_attr(policy, "enabled", 1.0)
            if policy_type == "ProcessCurriculumPolicy":
                source.s.set_attr(policy, "selector_mode", "residual")
                source.s.set_attr(policy, "max_tasks", 1.0)
    domain = source.s.add_node("ProcessDomain", {"name": "adaptive-checkpoint",
        "kind": "permutation", "domain_kind": "permutation",
        "probes": [world["initial_state"]], "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_domain", domain, {})
    params = world["held_processes"]["rot90"]
    schema = source.s.add_node("ProcessSchema", {"name": "rot90",
        "kind": "permutation", "domain": "adaptive-checkpoint",
        "domain_kind": "permutation", "params": params,
        "source_digest": params_digest(params), "status": "active",
        "provenance": "held", "cost": 1.0, "owner_agent": source.agent,
        "invariants": [], "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0, "probe_epoch": 0})
    source.s.add_edge(source.agent, "has_process_schema", schema, {})
    source.s.add_edge(domain, "has_held_process", schema, {})
    checkpoint = capture_held_process_checkpoint(source, schema,
        checkpoint_id="adaptive-curriculum-root")

    result = score_restored_checkpoint_task(checkpoint, world=world,
        agent_factory=boot_cognition_on)
    assert result["task_status"] == "solved"
    resources = result["resource_snapshot"]
    assert resources["resource_counts"]["curriculum_tasks"] == 1
    assert resources["cumulative_resources"]["training_evidence_exposures"] == 1
    assert result["approval_events_added"] == result["world_receipts_added"] == 0
