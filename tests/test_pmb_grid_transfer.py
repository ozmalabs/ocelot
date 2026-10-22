from evaluation.process_mastery.grid_transfer_adapter import (
    agent_view, record, source_audit, task,
)


def test_grid_split_provenance():
    train = task("train", 17)
    held = task("heldout", 17)
    assert train.source == held.source == "pmb_generated_d4_v1"
    assert train.seed != held.seed
    assert train.split == "train" and held.split == "heldout"


def test_target_solution_hidden():
    world = task("heldout", 2)
    view = agent_view(world)
    assert "transform" not in view
    assert view["base"] != [] and view["goal"] != []
    assert "affordances" in view


def test_comparator_has_same_affordances():
    world = task("heldout", 9)
    views = [agent_view(world) for _ in ("fresh", "source", "mismatched")]
    assert views[0] == views[1] == views[2]


def test_unavailable_source_reported():
    audit = source_audit()
    assert audit["supported"] == ["pmb_generated_d4_v1"]
    assert "ARC" in audit["unsupported"] and "LS20" in audit["unsupported"]
    assert audit["licenses"]["ARC"] is None


def test_result_records_actual_output_and_no_answer_exposure():
    world = task("heldout", 4)
    rec = record(world, arm="fresh", output=[[0, 1]], exact=False)
    assert rec["actual_output"] == [[0, 1]]
    assert rec["target_solution_exposed"] is False
    assert rec["exact_match"] is False
