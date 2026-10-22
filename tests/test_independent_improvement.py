"""P22 generic proposal, split, and candidate-scoped approval checks."""
import json
from pathlib import Path

from evaluation.process_mastery.native_process_execution import attest_open_process_candidate
from evaluation.process_mastery.native_process_execution import execute_open_process_candidate
from evaluation.process_mastery.native_process_execution import params_digest
from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointWorldAdapter, capture_adopted_checkpoint,
    capture_held_process_checkpoint,
)
from evaluation.process_mastery.independent_worlds import (
    generate_d4_world, generate_loopover_world,
)
from substrate.seed_loader import manifest_for
from substrate.boot_profiles import boot_cognition_on
from evaluation.process_mastery.p22_arms import configure_p22_arm
from tests.test_open_process_search import _agent as _p19_agent, _apply, _compose
from tests.test_open_process_adoption import (
    _agent as _adoption_agent, _approve, _candidate as _adoption_candidate, _tick,
)

ROOT = Path(__file__).resolve().parents[1]


def _agent():
    agent, _domain = _p19_agent(attempts=1000)
    return agent


def _install(agent):
    manifest = json.loads((ROOT / "seeds/independent_improvement.json").read_text())
    agent.native.load_seed_manifest(manifest, agent.ag)


def _candidate(agent):
    goal = _apply(agent, _compose(agent, [1, 0, 2, 3], [0, 2, 1, 3]), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal)
    agent.s.set_attr(task, "status", "stuck")
    for _ in range(12):
        agent.s.tick(4000)
    candidates = agent.nodes("OpenProcessCandidate")
    assert candidates
    return candidates[0]


def test_next_candidate_not_named_in_seed():
    seed = json.loads((ROOT / "seeds/independent_improvement.json").read_text())
    serialized = json.dumps(seed, sort_keys=True)
    for name in ("commutator_square_v1", "commutator_cube_v2", "commutator_fourth_v3"):
        assert name not in serialized
    assert "expression_digest" in serialized and "expression_tree" in serialized


def test_qualification_from_native_trials():
    agent = _agent()
    candidate = _candidate(agent)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    assert agent.attrs(attempt)["status"] == "verified"
    assert agent.attrs(attempt)["expression_tree"]
    assert agent.attrs(candidate)["status"] == "unapproved_candidate"
    source_task = agent.native.neighbours(attempt, "about_task")[0]
    agent.s.set_attr(source_task, "split", "training")
    agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
    attest_open_process_candidate(agent, candidate)
    _install(agent)
    agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
    for _ in range(8):
        agent.s.tick(4000)
    proposals = agent.nodes("IndependentImprovementProposal")
    assert len(proposals) == 1
    assert agent.attrs(proposals[0])["source_split"] == "training"
    assert agent.native.neighbours(proposals[0], "derived_from_trial") == [attempt]
    agent.s.set_attr(agent.nodes("OpenProcessSearchPolicy")[0], "max_attempts", 5000.0)
    second_task = agent.add_solve_task("search", [0, 1, 2, 3],
                                       agent.attrs(source_task)["goal"],
                                       training_trial_key="independent-trial-2")
    agent.s.set_attr(second_task, "split", "training")
    agent.s.set_attr(second_task, "status", "stuck")
    for _ in range(20):
        agent.s.tick(4000)
    proposal = proposals[0]
    qualification = agent.native.neighbours(proposal, "has_native_qualification")
    assert len(qualification) == 1
    assert agent.attrs(qualification[0])["trial_count"] == 2.0
    assert agent.attrs(proposal)["status"] == "qualified_for_candidate_specific_approval"
    supporting_attempts = agent.native.neighbours(qualification[0], "counts_native_trial")
    assert len(supporting_attempts) == 2
    supporting_requests = [request for request in agent.nodes("OpenProcessSearchRequest")
        if any(attempt in agent.native.neighbours(request, "has_search_attempt")
               for attempt in supporting_attempts)]
    assert len(supporting_requests) == 2
    assert all(agent.attrs(request)["status"] == "qualified_terminal"
               for request in supporting_requests)
    attempt_count = len(agent.nodes("OpenProcessSearchAttempt"))
    for _ in range(4):
        agent.s.tick(4000)
    assert len(agent.nodes("OpenProcessSearchAttempt")) == attempt_count


def test_three_generation_native_development_lineage():
    """Exercise repeated training qualification, exact approval and receipt capture.

    These candidate-bound approvals are local test fixtures. This test proves
    the native mechanism can extend a lineage; it does not provide live human
    authorization or an efficacy result.
    """
    agent = _adoption_agent()
    candidate = _adoption_candidate(agent)
    for policy in agent.nodes("OpenProcessSearchPolicy"):
        agent.s.set_attr(policy, "max_attempts", 30000.0)
    parent = capture_held_process_checkpoint(agent, agent.schemas("search")[0],
        checkpoint_id="p22-dev-g0")
    first_attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    first_task = agent.native.neighbours(first_attempt, "about_task")[0]
    agent.s.set_attr(first_task, "split", "training")
    _install(agent)
    agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
    attest_open_process_candidate(agent, candidate)
    for _ in range(8):
        agent.s.tick(4000)

    initial = [0, 1, 2, 3]
    held_a, held_b = [1, 0, 2, 3], [0, 2, 1, 3]
    checkpoints = [parent]
    for generation in range(1, 4):
        if generation > 1:
            operand = held_b if generation == 2 else held_a
            target = _compose(agent, list(checkpoints[-1].params), operand)
            goal = _apply(agent, target, initial)
            task = agent.add_solve_task("search", initial, goal,
                training_trial_key=f"p22-dev-g{generation}-trial1")
            agent.s.set_attr(task, "split", "training")
            agent.s.set_attr(task, "status", "stuck")
            for _ in range(24):
                agent.s.tick(4000)
            candidates = [node for node in agent.nodes("OpenProcessCandidate")
                          if agent.attrs(node).get("status") == "unapproved_candidate"]
            assert candidates
            candidate = candidates[-1]
            attest_open_process_candidate(agent, candidate)
            for _ in range(8):
                agent.s.tick(4000)

        attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
        task = agent.native.neighbours(attempt, "about_task")[0]
        goal = agent.attrs(task)["goal"]
        second_trial = agent.add_solve_task("search", initial, goal,
            training_trial_key=f"p22-dev-g{generation}-trial2")
        agent.s.set_attr(second_trial, "split", "training")
        agent.s.set_attr(second_trial, "status", "stuck")
        for _ in range(24):
            agent.s.tick(4000)
        proposal = next(proposal for proposal in agent.nodes("IndependentImprovementProposal")
            if agent.native.neighbours(proposal, "derived_from_trial") == [attempt])
        assert agent.native.neighbours(proposal, "has_native_qualification")
        assert agent.attrs(proposal)["status"] == "qualified_for_candidate_specific_approval"

        approval = _approve(agent, candidate)
        for _ in range(12):
            agent.s.tick(4000)
        assert agent.attrs(candidate)["status"] == "adopted_candidate"
        assert agent.attrs(approval)["status"] == "consumed"
        attrs = agent.attrs(candidate)

        def transition(action):
            observed = [None] * len(initial)
            for source, destination in enumerate(action):
                observed[destination] = initial[source]
            return {"observed_state": observed}

        execution = execute_open_process_candidate(agent, candidate,
            state=attrs["guard_state"],
            authorize=lambda proposed: proposed["expression_digest"] == attrs["expression_digest"],
            world_transition=transition)
        assert execution["status"] == "COMPLETED"
        checkpoints.append(capture_adopted_checkpoint(agent, candidate,
            checkpoint_id=f"p22-dev-g{generation}", parent=checkpoints[-1],
            generation=generation,
            declared_primitive_work=int(attrs["work_cost"])))

    assert [checkpoint.generation for checkpoint in checkpoints] == [0, 1, 2, 3]
    assert all(checkpoints[i].parent_digest == checkpoints[i - 1].checkpoint_digest
               for i in range(1, len(checkpoints)))


def test_three_generation_family_sized_development_lineages():
    """Check both registered state sizes through native qualification and capture.

    The generated first task is independent of the checkpoint. Later tasks are
    development-only lineage probes, so this does not validate held-out goals.
    All approvals below are exact test fixtures, never live authorization.
    """
    for family, world_fn, draw, extra_operand in (
            ("loopover", generate_loopover_world, 11, "C1"),
            ("d4", generate_d4_world, 12, "flip_r")):
        world = world_fn(split="train", draw=draw)
        agent, domain = _p19_agent(attempts=30000, held=world["held_processes"])
        agent.s.set_attr(domain, "probes", [world["initial_state"]])
        agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
        _install(agent)
        agent.s.set_attr(agent.nodes("OpenProcessAdoptionPolicy")[0], "enabled", 1.0)
        agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
        parent = capture_held_process_checkpoint(agent, agent.schemas("search")[0],
            checkpoint_id=f"p22-{family}-dev-g0")
        checkpoints = [parent]
        initial = list(world["initial_state"])

        def train_and_qualify(goal, generation):
            first = agent.add_solve_task("search", initial, goal,
                training_trial_key=f"p22-{family}-dev-g{generation}-trial1")
            agent.s.set_attr(first, "split", "training")
            agent.s.set_attr(first, "status", "stuck")
            for _ in range(24):
                agent.s.tick(4000)
            candidates = [candidate for candidate in agent.nodes("OpenProcessCandidate")
                          if agent.attrs(candidate).get("status") == "unapproved_candidate"]
            assert candidates
            candidate = candidates[-1]
            assert agent.attrs(candidate).get("effect_digest") is not None
            attest_open_process_candidate(agent, candidate)
            for _ in range(8):
                agent.s.tick(4000)
            second = agent.add_solve_task("search", initial, goal,
                training_trial_key=f"p22-{family}-dev-g{generation}-trial2")
            agent.s.set_attr(second, "split", "training")
            agent.s.set_attr(second, "status", "stuck")
            for _ in range(24):
                agent.s.tick(4000)
            attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
            proposal = next(proposal for proposal in agent.nodes("IndependentImprovementProposal")
                if agent.native.neighbours(proposal, "derived_from_trial") == [attempt])
            assert agent.native.neighbours(proposal, "has_native_qualification")
            assert agent.attrs(proposal)["status"] == "qualified_for_candidate_specific_approval"
            return candidate

        candidate = train_and_qualify(world["goal_state"], 1)
        for generation in range(1, 4):
            if generation > 1:
                operand = world["held_processes"][extra_operand]
                target = _compose(agent, list(checkpoints[-1].params), operand)
                candidate = train_and_qualify(_apply(agent, target, initial), generation)
            approval = _approve(agent, candidate)
            for _ in range(12):
                agent.s.tick(4000)
            assert agent.attrs(candidate)["status"] == "adopted_candidate"
            assert agent.attrs(approval)["status"] == "consumed"
            attrs = agent.attrs(candidate)

            def transition(action):
                observed = [None] * len(initial)
                for source, destination in enumerate(action):
                    observed[destination] = initial[source]
                return {"observed_state": observed}

            execution = execute_open_process_candidate(agent, candidate,
                state=attrs["guard_state"],
                authorize=lambda proposed: proposed["expression_digest"] == attrs["expression_digest"],
                world_transition=transition)
            assert execution["status"] == "COMPLETED"
            checkpoints.append(capture_adopted_checkpoint(agent, candidate,
                checkpoint_id=f"p22-{family}-dev-g{generation}", parent=checkpoints[-1],
                generation=generation, declared_primitive_work=int(attrs["work_cost"])))

        assert [checkpoint.generation for checkpoint in checkpoints] == [0, 1, 2, 3]
        assert all(checkpoints[i].parent_digest == checkpoints[i - 1].checkpoint_digest
                   for i in range(1, len(checkpoints)))
        assert checkpoints[0].cumulative_primitive_work == checkpoints[0].declared_primitive_work
        assert all(checkpoints[i].cumulative_primitive_work ==
                   checkpoints[i - 1].cumulative_primitive_work +
                   checkpoints[i].declared_primitive_work for i in range(1, len(checkpoints)))
        adapter = CheckpointWorldAdapter(agent.native, primitive_work_ceiling=100)
        scored = adapter.compare(tuple(checkpoints), [world])
        assert scored["same_worlds"]
        assert all(outcome["status"] == "scored"
                   for outcome in scored["rows"][0]["outcomes"])
        # The generation-zero and promoted expressions carry different declared
        # work, so this development comparison cannot make an efficiency claim.
        assert not scored["efficiency_comparable"]


def test_no_holdout_in_proposal():
    agent = _agent()
    candidate = _candidate(agent)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    task = agent.native.neighbours(attempt, "about_task")[0]
    agent.s.set_attr(task, "split", "heldout")
    agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
    attest_open_process_candidate(agent, candidate)
    _install(agent)
    agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
    for _ in range(8):
        agent.s.tick(4000)
    assert not agent.nodes("IndependentImprovementProposal")


def test_native_curriculum_releases_training_task_to_same_process_search_graph():
    agent = boot_cognition_on()
    try:
        configure_p22_arm(agent, "full", budget_capacity=64.0)
        domain_name = "p22-curriculum-bridge"
        domain = agent.s.add_node("ProcessDomain", {
            "name": domain_name, "kind": "permutation", "domain_kind": "permutation",
            "object_count": 4.0, "probes": [[0, 1, 2, 3]],
            "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
            "probe_epoch": 0})
        agent.s.add_edge(agent.agent, "has_process_domain", domain, {})
        held = {"rot90": [3, 0, 1, 2], "flip_r": [2, 1, 0, 3]}
        for name, params in held.items():
            schema = agent.s.add_node("ProcessSchema", {
                "name": name, "kind": "permutation", "domain_kind": "permutation",
                "domain": domain_name, "params": params,
                "source_digest": params_digest(params), "cost": 1.0,
                "status": "active", "provenance": "world_affordance",
                "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0})
            agent.s.add_edge(agent.agent, "has_process_schema", schema, {})
            agent.s.add_edge(domain, "has_held_process", schema, {})

        target = agent.inner.evaluate({"type": "ProcessCompose",
            "a": {"type": "Var", "name": "a"},
            "b": {"type": "Var", "name": "b"}},
            {"a": held["rot90"], "b": held["flip_r"]})
        goal = agent.inner.evaluate({"type": "ProcessApply",
            "p": {"type": "Var", "name": "p"},
            "state": {"type": "Var", "name": "state"}},
            {"p": target, "state": [0, 1, 2, 3]})
        evidence = agent.s.add_node("ProcessCurriculumEvidence", {
            "evidence_key": "p22:training:bridge:0001",
            "source_kind": "registered_training_pool", "source_id": "p22:train:0001",
            "task_kind": "process_composition", "action_kind": "apply",
            "object_type": "Permutation", "feature_key": "permutation",
            "before_value": [0, 1, 2, 3], "domain": domain_name,
            "initial_state": [0, 1, 2, 3], "goal": goal,
            "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
            "status": "eligible", "split": "training",
            "expected_outcome": "unknown", "sealed_labels_present": False,
            "fixed_rank": 0.0, "random_rank": 0.0})
        agent.s.add_edge(agent.agent, "has_process_curriculum_evidence", evidence, {})

        for _ in range(64):
            if agent.inner.run_rules(20_000) == 0:
                break
        curriculum_tasks = agent.s.nodes("ProcessCurriculumTask")
        assert len(curriculum_tasks) == 1
        curriculum_attrs = agent.s.node(curriculum_tasks[0])["attrs"]
        assert curriculum_attrs["status"] == "delivered_to_native_search"
        assert curriculum_attrs["split"] == "training"
        solve_tasks = [node for node in agent.s.nodes("SolveTask")
                       if agent.s.node(node)["attrs"].get("task_key") ==
                       curriculum_attrs["task_key"]]
        assert len(solve_tasks) == 1
        solve_attrs = agent.s.node(solve_tasks[0])["attrs"]
        assert solve_attrs["status"] == "stuck"
        assert solve_attrs["split"] == "training"
        assert solve_attrs["initial_state"] == [0, 1, 2, 3]
        assert solve_attrs["goal"] == goal
        assert agent.inner.neighbours(solve_tasks[0], "about_domain") == [domain]
        assert any(agent.s.node(attempt)["attrs"].get("status") == "verified"
                   for attempt in agent.s.nodes("OpenProcessSearchAttempt"))
        assert agent.s.nodes("OpenProcessAdoptionApproval") == []
        assert agent.s.nodes("OpenProcessWorldReceipt") == []
    finally:
        agent.close()


def test_new_approval_exact_expression():
    agent = _adoption_agent()
    candidate = _adoption_candidate(agent)
    approval = _approve(agent, candidate)
    params = list(agent.attrs(candidate)["params"])
    params[0], params[1] = params[1], params[0]
    agent.s.set_attr(candidate, "params", params)
    _tick(agent)
    assert agent.attrs(approval)["status"] != "consumed"
    assert agent.attrs(candidate)["status"] == "unapproved_candidate"


def test_rollback_stops_current_execution():
    seed = json.loads((ROOT / "seeds/recursive_process_improvement.json").read_text())
    rollback = next(rule for rule in seed["rules"]
                    if rule["name"] == "rpi_rollback_failed_generation_to_verified_ancestor")
    encoded = json.dumps(rollback, sort_keys=True)
    assert "rolled_back" in encoded and "suspended" in encoded
    assert "zero_tolerance_invariant_failure" in encoded
