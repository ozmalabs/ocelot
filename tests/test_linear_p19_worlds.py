from evaluation.process_mastery.linear_p19_worlds import (
    expression_actions,
    generate_task,
)


def test_p19_task_generation_is_seeded_and_hides_witness():
    task_a, _, witness_a = generate_task("permutation", "process_effect", 29000001)
    task_b, _, witness_b = generate_task("permutation", "process_effect", 29000001)
    assert task_a == task_b
    assert witness_a == witness_b
    assert len(witness_a) == 3
    assert "witness" not in task_a and "solution" not in task_a


def test_irreversible_object_world_enforces_action_preconditions_and_receipts():
    task, world, witness = generate_task("irreversible_objects", "multi_step_constraint", 29010001)
    assert len(witness) == 4
    rejected = world.transition_sequence(("seal_0",))
    assert rejected["status"] == "rejected"
    assert tuple(world.state) == tuple(task["initial_state"])

    receipt = world.transition_sequence(witness)
    assert receipt["status"] == "verified"
    assert tuple(receipt["observed_state"]) == tuple(task["goal_state"])
    assert world.verify_receipt(receipt)
    altered = dict(receipt, observed_state=[9, 9, 9, 9])
    assert not world.verify_receipt(altered)


def test_native_search_expression_decodes_to_ordered_world_actions():
    tree = ["guard", [0, 0], ["subgoal", [1, 0],
        ["compose", "prepare_0", ["power", 2, "seal_0"]]]]
    assert expression_actions(tree) == ["prepare_0", "seal_0", "seal_0"]
    assert expression_actions(["inverse", "prepare_0"]) is None


def test_irreversible_reachable_graph_is_closed_and_goal_reachable():
    task, world, _ = generate_task("irreversible_objects", "multi_step_constraint", 29010002)
    graph = world.transition_graph()
    states = {tuple(state) for state in graph["states"]}
    assert graph["complete"]
    assert tuple(task["initial_state"]) in states
    assert tuple(task["goal_state"]) in states
