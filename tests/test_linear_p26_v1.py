"""P26 frozen allocation, world boundary, and matched-arm runner checks."""
from __future__ import annotations

from copy import deepcopy

import pytest

from evaluation.process_mastery.analyze_linear_p26_v1 import _analysis, _validate
from evaluation.process_mastery.evidence_search_worlds import (
    FAMILIES, EvidenceSearchWorld, generate_evidence_search_pool, selector_views,
)
from evaluation.process_mastery.linear_p26_v1 import (
    ARMS, CONTROL_KINDS, HELDOUT_CONTROLS_PER_KIND, HELDOUT_STREAMS_PER_CELL,
    PRIOR_NUMERIC_INTERVALS, _parse_preregistration_freeze, allocation, run_payload,
)
from evaluation.process_mastery.target_learning_worlds import WorldReceipt


def test_p26_allocation_is_fixed_disjoint_and_complete():
    plan = allocation("heldout")
    assert plan["streams_per_family_load_cell"] == HELDOUT_STREAMS_PER_CELL == 200
    assert plan["controls_per_kind"] == HELDOUT_CONTROLS_PER_KIND == 100
    assert len(plan["stream_cells"]) == len(FAMILIES) * 2
    assert all(cell["arms"] == list(ARMS) for cell in plan["stream_cells"])
    seeds = [seed for cell in plan["stream_cells"] for key in
             ("stream_seeds", "train_pool_seeds", "heldout_pool_seeds")
             for seed in cell[key]]
    seeds.extend(seed for values in plan["control_seeds"].values() for seed in values)
    assert len(seeds) == len(set(seeds))
    assert not any(lo <= seed <= hi for seed in seeds
                   for lo, hi in PRIOR_NUMERIC_INTERVALS)
    with pytest.raises(ValueError):
        allocation("heldout", streams_per_cell=1)


def test_p26_freeze_gate_requires_one_machine_record():
    assert _parse_preregistration_freeze(
        b"# P26 freeze\n\nP26_FREEZE_JSON: {\"code_commit\":\"abc\"}\n") == {
            "code_commit": "abc"}
    with pytest.raises(RuntimeError, match="one P26_FREEZE_JSON"):
        _parse_preregistration_freeze(b"# P26 freeze\n")
    with pytest.raises(RuntimeError, match="invalid JSON"):
        _parse_preregistration_freeze(b"P26_FREEZE_JSON: {broken}\n")


def test_p26_world_keeps_scorer_labels_and_heldout_out_of_selector_view():
    pool = generate_evidence_search_pool(split="heldout", draws=(0,), seed=261001,
        family=FAMILIES[0], initial_state=tuple(range(7)))
    public = pool.task_pool()[0]
    assert "relation_class" not in public
    assert "witness" not in public
    assert "solvable" not in public
    assert all("after_value" not in row for row in public["evidence_opportunities"])
    with pytest.raises(ValueError, match="selector access"):
        selector_views(pool)


def test_p26_world_emits_typed_receipt_only_after_authorized_execution():
    pool = generate_evidence_search_pool(split="train", draws=(1,), seed=261002,
        family=FAMILIES[0], initial_state=tuple(range(7)))
    task = pool.task_pool()[0]
    world = EvidenceSearchWorld(task, pool.scorer_only[0])
    opportunity = task["evidence_opportunities"][0]
    with pytest.raises(ValueError, match="authorized training"):
        world.execute({**opportunity, "split": "heldout"})
    receipt = world.execute(opportunity)
    assert isinstance(receipt, WorldReceipt)
    assert receipt.status == "observed" and receipt.action_authorized
    assert world.verify_receipt(receipt)


def test_p26_development_panel_has_matched_pools_and_executable_controls():
    payload = run_payload("development", streams_per_cell=1, controls_per_kind=1)
    failures, _ = _validate(payload)
    assert failures == []
    analysis = _analysis(payload)
    assert analysis["structural_status"] == "VALID"
    assert analysis["primary"]["gain_reselected_stronger_control"]["n"] == 4
    assert set(analysis["primary"]["pairwise_residual_minus_control"]) == {"fixed", "random"}
    assert payload["provenance"]["runtime_attestation"]["status"] == "ATTESTED"
    assert {row["kind"] for row in payload["integrity_controls"]} == set(CONTROL_KINDS)
    for stream in payload["streams"]:
        assert len({arm["train_pool_sha256"] for arm in stream["arms"]}) == 1
        assert {arm["arm"] for arm in stream["arms"]} == set(ARMS)
        search = stream["native_search"]
        assert len(search["attempt_records"]) == search["attempts"]
        assert search["adoption_approvals"] == search["world_receipts"] == 0
        if search["candidate_records"]:
            assert search["candidate_gate_probe"]["reason"] == "candidate_not_adopted"
            assert search["candidate_gate_probe"]["authorize_calls"] == 0
            assert search["candidate_gate_probe"]["world_transition_calls"] == 0
        else:
            assert search["candidate_gate_probe"]["status"] == "NO_CANDIDATE"


def test_p26_analyzer_rejects_selector_pool_or_receipt_tampering():
    payload = run_payload("development", streams_per_cell=1, controls_per_kind=1)
    changed_pool = deepcopy(payload)
    changed_pool["streams"][0]["arms"][1]["train_pool_sha256"] = "0" * 64
    failures, _ = _validate(changed_pool)
    assert any("selector_pool_identity_mismatch" in item for item in failures)

    changed_receipt = deepcopy(payload)
    changed_receipt["integrity_controls"] = [
        {**row, "replay_added_exposure": True} if row["kind"] == "receipt_replay" else row
        for row in changed_receipt["integrity_controls"]]
    failures, _ = _validate(changed_receipt)
    assert "receipt_replay_changed_exposure" in failures
