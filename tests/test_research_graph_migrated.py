"""Phase-one research graph persistence and mechanical ledger checks."""
from __future__ import annotations

import json

import pytest

from scripts.ocelot_research import ResearchError, ResearchGraph, load_graph


def _graph(tmp_path):
    return ResearchGraph.create("Does extension help solve residual CNF?",
                                root=tmp_path, mode="deductive",
                                roots=["/repo/ge", "/repo/ocelot"],
                                investigation_id="demo")


def test_create_record_link_and_reload_are_json_serializable(tmp_path):
    graph = _graph(tmp_path)
    question = graph.state()["nodes"][0]
    claim = graph.record("Claim", wording="Extension makes every residual easier.",
                         scope="all residual CNFs", claim_type="hypothesis",
                         author="researcher", status="open", limitations=["unbounded"])
    evidence = graph.record("Evidence", description="Hard residual construction")
    edge = graph.link(evidence["id"], "opposes", claim["id"],
                      provenance={"author": "researcher"}, rationale="counterexample")

    loaded = load_graph("demo", root=tmp_path)
    state = loaded.state()
    assert state["schema_version"] == 1
    assert [n["id"] for n in state["nodes"]] == [question["id"], claim["id"], evidence["id"]]
    assert state["edges"] == [edge]
    assert len(state["events"]) == 4  # initial question, claim, evidence, edge
    assert loaded.inspect(claim["id"])["related_nodes"][0]["id"] == evidence["id"]
    json.dumps(state)


def test_invalid_types_and_unknown_edge_endpoints_are_rejected(tmp_path):
    graph = _graph(tmp_path)
    with pytest.raises(ResearchError, match="unknown node type"):
        graph.record("Citation")
    with pytest.raises(ResearchError, match="claim_type"):
        graph.record("Claim", claim_type="guess")
    with pytest.raises(ResearchError, match="endpoints"):
        graph.link("missing", "supports", "question-0001")
    with pytest.raises(ResearchError, match="unknown edge type"):
        graph.link("question-0001", "proves", "question-0001")
    with pytest.raises(ResearchError, match="incompatible"):
        graph.link("question-0001", "supports", "question-0001")


def test_edge_vocabulary_enforces_endpoint_types(tmp_path):
    graph = _graph(tmp_path)
    claim = graph.record("Claim", wording="A claim")
    frame = graph.record("Frame", boundary="system")
    assumption = graph.record("Assumption", wording="closed domain")
    protocol = graph.record("Protocol", title="finite check")
    run = graph.record("Run", status="failed")

    assert graph.link(claim["id"], "scoped_by", frame["id"])["type"] == "scoped_by"
    assert graph.link(claim["id"], "assumes", assumption["id"])["type"] == "assumes"
    assert graph.link(protocol["id"], "tests", run["id"])["type"] == "tests"
    with pytest.raises(ResearchError, match="incompatible"):
        graph.link(frame["id"], "tests", claim["id"])
    with pytest.raises(ResearchError, match="incompatible"):
        graph.link(run["id"], "produced", protocol["id"])


def test_source_can_oppose_claim_and_transitive_inspection_walks_graph(tmp_path):
    graph = _graph(tmp_path)
    claim = graph.record("Claim", wording="Claim")
    evidence = graph.record("Evidence", description="counterexample")
    source = graph.record("Source", locator="paper.md#L10")
    graph.link(source["id"], "opposes", claim["id"])
    graph.link(evidence["id"], "derived_from", source["id"])

    inspected = graph.inspect(claim["id"], transitive=True)
    assert {node["id"] for node in inspected["related_nodes"]} == {source["id"], evidence["id"]}
    assert len(inspected["edges"]) == 2
    assert inspected["transitive"] is True


def test_check_surfaces_missing_claim_fields_without_truth_verdict(tmp_path):
    graph = _graph(tmp_path)
    claim = graph.record("Claim", wording="A bounded claim")
    check = graph.check()
    missing = {issue.get("field") for issue in check["issues"]}
    assert {"scope", "claim_type", "author", "status"} <= missing
    assert check["truth_assessed"] is False
    assert check["ok"] is False
    report = graph.export()
    assert claim["id"] in report["markdown"]
    assert "Truth is not assessed" in report["markdown"]
    assert report["bundle"]["investigation_id"] == "demo"


def test_supersession_is_an_append_only_relationship(tmp_path):
    graph = _graph(tmp_path)
    first = graph.record("Claim", wording="first wording", scope="narrow",
                         claim_type="inference", author="A", status="superseded")
    second = graph.record("Claim", wording="corrected wording", scope="narrow",
                          claim_type="inference", author="A", status="open")
    graph.link(second["id"], "supersedes", first["id"], rationale="corrected scope")
    before = graph.state()
    loaded = load_graph("demo", root=tmp_path)
    assert loaded.state()["nodes"] == before["nodes"]
    assert len(loaded.state()["events"]) == 4
    assert loaded.state()["edges"][0]["type"] == "supersedes"


def test_atomic_persistence_leaves_no_temp_file(tmp_path):
    graph = _graph(tmp_path)
    graph.record("Frame", boundary="unknown", state={"value": "not_applicable", "reason": "not specified"})
    assert graph.path.is_file()
    assert not list(graph.path.parent.glob(".*.tmp"))


def test_confirmatory_mode_is_recorded(tmp_path):
    graph = ResearchGraph.create("Predeclared question", root=tmp_path,
                                 mode="confirmatory", investigation_id="confirm")
    assert graph.state()["mode"] == "confirmatory"


def test_reserved_fields_and_save_failure_do_not_mutate_graph(tmp_path, monkeypatch):
    graph = _graph(tmp_path)
    before = graph.state()
    with pytest.raises(ResearchError, match="reserved"):
        graph.record("Claim", id="spoof")
    def fail_save():
        raise OSError("disk unavailable")
    monkeypatch.setattr(graph, "_save", fail_save)
    with pytest.raises(OSError):
        graph.record("Frame", boundary="test")
    assert graph.state() == before


def test_load_rejects_filename_identity_mismatch(tmp_path):
    graph = _graph(tmp_path)
    raw = json.loads(graph.path.read_text(encoding="utf-8"))
    raw["investigation_id"] = "other"
    graph.path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ResearchError, match="does not match"):
        load_graph("demo", root=tmp_path)


def test_load_rejects_event_log_that_does_not_cover_graph(tmp_path):
    graph = _graph(tmp_path)
    raw = json.loads(graph.path.read_text(encoding="utf-8"))
    raw["events"].clear()
    graph.path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ResearchError, match="event log"):
        load_graph("demo", root=tmp_path)


@pytest.mark.parametrize("tamper", ["event_order", "event_payload", "materialized_node"])
def test_load_rejects_event_log_replay_mismatch(tmp_path, tamper):
    graph = _graph(tmp_path)
    graph.record("Claim", wording="claim")
    raw = json.loads(graph.path.read_text(encoding="utf-8"))
    if tamper == "event_order":
        raw["events"][0], raw["events"][1] = raw["events"][1], raw["events"][0]
    elif tamper == "event_payload":
        raw["events"][1]["node"]["wording"] = "altered event"
    else:
        raw["nodes"][1]["wording"] = "altered node"
    graph.path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ResearchError, match="event log"):
        load_graph("demo", root=tmp_path)
