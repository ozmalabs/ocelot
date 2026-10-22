from evaluation.process_mastery.linear_p19_v1 import (
    BASE_SEED,
    HELDOUT_OFFSET,
    allocation,
    run_control,
    run_trial,
)


def test_p19_allocation_has_disjoint_development_and_heldout_blocks():
    development = allocation("development")
    heldout = allocation("heldout")
    assert len(development["tasks"]) == 32
    assert len(heldout["tasks"]) == 800
    assert len(development["controls"]) == len(heldout["controls"]) == 100
    assert all(item["seed"] >= HELDOUT_OFFSET + BASE_SEED
               for item in heldout["tasks"])
    assert {item["seed"] for item in development["tasks"]}.isdisjoint(
        {item["seed"] for item in heldout["tasks"]})
    assert {item["kind"] for item in heldout["controls"]} == {
        "impossible_goal", "illegal_action", "precondition_failure"}


def test_p19_native_primitive_comparator_executes_receipt_backed_plan():
    result = run_trial("irreversible_objects", "multi_step_constraint",
                       BASE_SEED + 20_000, "native_primitive_search")
    assert result["status"] == "COMPLETED"
    assert result["solved"]
    assert 0 < result["primitives"] <= 8
    assert result["model_queries"] <= 4_096
    assert result["receipts"]


def test_p19_control_world_rejects_illegal_and_precondition_actions_without_mutation():
    for kind, seed in (("illegal_action", BASE_SEED + 100_000),
                       ("precondition_failure", BASE_SEED + 100_001),
                       ("impossible_goal", BASE_SEED + 100_002)):
        assert run_control(kind, seed)["state_unchanged"]
