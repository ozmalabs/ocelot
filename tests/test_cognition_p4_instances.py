"""P4 transfer instance generation guards (development draws only)."""
import pytest

from evaluation.substrate_capability.cognition_p4_instances_v1 import (
    agent_payload, draw_panel, draw_transfer,
)


def test_disjoint_source_target_ids():
    for direction in ("graph_role", "numeric_sequence"):
        case = draw_transfer(direction, 113, True)
        assert case["source_id"] != case["target_id"]
        if direction == "graph_role":
            source_ids = {node_id for _, node_id in case["source_exposure"]["nodes"]}
            target_ids = {node_id for _, node_id in case["target_problem"]["nodes"]}
            assert source_ids.isdisjoint(target_ids)


def test_generator_deterministic():
    for direction in ("graph_role", "numeric_sequence"):
        assert draw_transfer(direction, 441, False) == draw_transfer(direction, 441, False)


def test_scoring_oracle_never_ingested():
    case = draw_transfer("numeric_sequence", 88, True)
    payload = agent_payload(case)
    assert "scoring_oracle" not in payload
    assert payload["source_exposure"] != case["scoring_oracle"]
    assert payload["target_problem"].get("y") != [case["scoring_oracle"]["next_y"]]
    assert "compatible" not in payload
    assert "seed" not in payload


def test_agent_views_have_two_candidates_without_compatibility_labels():
    def forbidden_keys(value):
        if isinstance(value, dict):
            return {key for key, child in value.items()
                    if key in {"compatible", "status", "scoring_oracle", "seed"}
                    or forbidden_keys(child)}
        if isinstance(value, (list, tuple)):
            return set().union(*(forbidden_keys(item) for item in value)) if value else set()
        return set()

    for family in ("graph_role", "numeric_sequence"):
        panel = draw_panel("1234567890abcdef" * 2 + "12345678", 1000, 1001,
                           development=True)
        row = next(row for row in panel if row["family"] == family
                   and row["case_kind"] == "target")
        for arm in row["arms"].values():
            assert len([role for role, _ in arm["target_problem"]["nodes"]
                        if role == "candidate"]) == 2 if family == "graph_role" else \
                len(arm["target_problem"]["candidates"]) == 2
            assert forbidden_keys(arm) == set()
        assert row["scoring_oracle"]["target_candidate_key"] is not None


def test_graph_role_requires_transfer_between_two_target_candidates():
    compatible = draw_transfer("graph_role", 917, True)
    decoy = draw_transfer("graph_role", 917, False)
    visible = agent_payload(compatible)
    candidate_ids = [node_id for role, node_id in visible["target_problem"]["nodes"]
                     if role == "candidate"]
    assert len(candidate_ids) == 2
    # Agent projection must be non-mutating: the scorer's identifiers remain
    # the raw internal ids after anonymized input has been formed.
    assert compatible["target_problem"]["nodes"][2][1] not in candidate_ids
    assert compatible["scoring_oracle"]["target"] in {
        node_id for _role, node_id in compatible["target_problem"]["nodes"]}
    assert decoy["scoring_oracle"]["target"] is None


def test_development_panel_has_paired_targets_and_separate_decoys():
    panel = draw_panel("0123456789abcdef" * 2 + "01234567", 1000, 1003,
                       development=True)
    # Two directions, three targets per direction, plus three decoys per direction.
    assert len(panel) == 12
    targets = [row for row in panel if row["case_kind"] == "target"]
    decoys = [row for row in panel if row["case_kind"] == "incompatible_decoy"]
    assert len(targets) == len(decoys) == 6
    assert {len(row["arms"]) for row in panel} == {3}
    for row in panel:
        on = row["arms"]["recall_on"]
        off = row["arms"]["recall_off"]
        mismatch = row["arms"]["mismatched_source"]
        assert on["target_problem"] == off["target_problem"] == mismatch["target_problem"]
        assert on["target_digest"] == off["target_digest"] == mismatch["target_digest"]
        assert on["source_exposure"] == off["source_exposure"]
        assert mismatch["source_exposure"] != on["source_exposure"]
        assert "scoring_oracle" not in on and "compatible" not in on and "seed" not in on
        assert "status" not in mismatch["frame_map"]
        assert mismatch["frame_map"] == on["frame_map"]
        assert row["scoring_oracle"]["compatible"] == (row["case_kind"] == "target")


def test_panel_is_deterministic_and_rejects_unregistered_range_or_hash():
    prereg = "fedcba9876543210" * 2 + "fedcba98"
    assert draw_panel(prereg, 1011, 1012, development=True) == draw_panel(
        prereg, 1011, 1012, development=True)
    with pytest.raises(ValueError):
        draw_panel("short", 0, 1)
    with pytest.raises(ValueError):
        draw_panel(prereg, 0, 201)
    with pytest.raises(ValueError):
        draw_panel(prereg, 1000, 1001)
