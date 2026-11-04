import copy
import json

import pytest

from evaluation.process_mastery.search_attempt_export import export_attempt_details, main


def _payload():
    return {"result": {"checkpoint": {"native_graph_snapshot_json": json.dumps({
        "nodes": [
            {"id": 1, "type": "OpenProcessSearchAttempt", "attrs": {
                "operator_kind": "compose", "status": "verified",
                "domain": "training-domain", "expression_key": "compose:p:q",
                "effect_digest": [[1, 0, 2, 3]], "work_cost": 2.0}},
            {"id": 2, "type": "OpenProcessCandidate", "attrs": {"status": "unapproved_candidate"}},
            {"id": 3, "type": "SolveTask", "attrs": {"split": "training"}},
            {"id": 4, "type": "OpenProcessSearchRequest", "attrs": {"status": "proposal_recorded"}},
            {"id": 5, "type": "OpenProcessCandidate", "attrs": {"status": "unapproved_candidate"}},
        ],
        "edges": [
            {"src": 2, "tgt": 1, "type": "derived_from_attempt"},
            {"src": 1, "tgt": 5, "type": "extends_candidate"},
            {"src": 1, "tgt": 3, "type": "about_task"},
            {"src": 4, "tgt": 1, "type": "has_search_attempt"},
        ],
    })}}}


def test_attempt_detail_projection_is_read_only_and_contains_provenance():
    payload = _payload()
    before = copy.deepcopy(payload)
    result = export_attempt_details(payload)
    assert payload == before
    assert result["read_only"] is True
    assert result["agent_feedback"] is False
    assert result["attempt_count"] == 1
    row = result["attempts"][0]
    assert row["candidate_ids"] == [2, 5]
    assert row["derived_candidate_ids"] == [2]
    assert row["parent_candidate_ids"] == [5]
    assert row["task_ids"] == [3]
    assert row["request_ids"] == [4]


def test_attempt_detail_projection_accepts_structured_native_identity_fields():
    payload = _payload()
    graph = json.loads(payload["result"]["checkpoint"]["native_graph_snapshot_json"])
    graph["nodes"][0]["attrs"]["domain"] = {"name": "training-domain"}
    graph["nodes"][0]["attrs"]["expression_key"] = {"tree": ["compose", "p", "q"]}
    payload["result"]["checkpoint"]["native_graph_snapshot_json"] = json.dumps(graph)
    result = export_attempt_details(payload)
    assert result["attempt_count"] == 1
    assert result["attempts"][0]["domain"] == {"name": "training-domain"}


def test_attempt_detail_cli_requires_explicit_opt_in(tmp_path):
    source = tmp_path / "source.json"
    output = tmp_path / "details.json"
    source.write_text(json.dumps(_payload()))
    with pytest.raises(SystemExit) as error:
        main(["--input", str(source), "--output", str(output)])
    assert error.value.code == 2
    assert not output.exists()


def test_attempt_detail_cli_writes_only_new_external_report(tmp_path, capsys):
    source = tmp_path / "source.json"
    output = tmp_path / "details.json"
    source.write_text(json.dumps(_payload()))
    main(["--export-attempt-details", "--input", str(source), "--output", str(output)])
    report = json.loads(output.read_text())
    assert report["attempt_count"] == 1
    assert json.loads(source.read_text()) == _payload()
    with pytest.raises(SystemExit) as error:
        main(["--export-attempt-details", "--input", str(source), "--output", str(output)])
    assert error.value.code == 2
