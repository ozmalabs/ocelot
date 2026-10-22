"""P17 counterexample retention, retirement and context-split controls."""
import json

from test_qualia_behavior import _axis, _boot, _fresh, _tick


def test_counterexample_removes_stale_influence_and_is_retained():
    s, ag = _boot()
    _, dim, _ = _axis(s, ag)
    _fresh(s, ag, 1, outcome="unexpected", context="later-context")
    _tick(s)
    assert s.node(dim)["attrs"]["acquisition_status"] == "retired"
    assert s.node(s.nodes("QualiaBehaviorPrediction")[0])["attrs"]["status"] == "contradicted"
    counterexamples = s.nodes("QualiaCounterexample")
    assert len(counterexamples) == 1
    ce = s.node(counterexamples[0])["attrs"]
    assert ce["predicted_consequence"] == "restored"
    assert ce["observed_consequence"] == "unexpected"
    assert ce["status"] == "verified"
    _fresh(s, ag, 2)
    _tick(s)
    assert len(s.nodes("QualiaBehaviorPrediction")) == 1


def _counterexample(s, ag, i, context, consequence):
    ce = s.add_node("QualiaCounterexample", {
        "counterexample_key": f"ce-{i}", "owner_id": "owner-a",
        "episode_id": f"episode-{i}", "context_id": context,
        "feature_key": "contact-pattern", "feature_value": "rough",
        "dimension_id": "phenomenal:acquired:owner-a:contact-pattern",
        "predicted_consequence": "restored", "observed_consequence": consequence,
        "status": "verified"})
    s.add_edge(ag, "has_qualia_counterexample", ce)
    return ce


def test_context_split_requires_repeated_verified_evidence():
    s, ag = _boot()
    _axis(s, ag)
    _counterexample(s, ag, 1, "context-a", "restored")
    _counterexample(s, ag, 2, "context-b", "damaged")
    _tick(s)
    assert not s.nodes("QualiaContextSplit")
    c3 = _counterexample(s, ag, 3, "context-a", "restored")
    c4 = _counterexample(s, ag, 4, "context-b", "damaged")
    _tick(s)
    splits = s.nodes("QualiaContextSplit")
    assert len(splits) == 1
    attrs = s.node(splits[0])["attrs"]
    assert attrs["verified"] is True
    assert attrs["evidence_count"] == 4.0
    assert {attrs["context_a"], attrs["context_b"]} == {"context-a", "context-b"}
    assert {attrs["consequence_a"], attrs["consequence_b"]} == {"restored", "damaged"}
    assert {c3, c4}.issubset(set(s.neighbours(splits[0], "supported_by")))


def test_save_load_preserves_counterexamples_and_revisions():
    s, ag = _boot()
    _, dim, _ = _axis(s, ag)
    _fresh(s, ag, 1, outcome="unexpected")
    _tick(s)
    snapshot = json.loads(json.dumps(s.graph_to_dict()))
    restored, _ = _boot()
    restored.graph_from_dict(snapshot)
    dim2 = next(n for n in restored.nodes("QualiaDimension")
                if restored.node(n)["attrs"].get("name") ==
                "phenomenal:acquired:owner-a:contact-pattern")
    assert restored.node(dim2)["attrs"]["acquisition_status"] == "retired"
    ce = restored.nodes("QualiaCounterexample")
    assert len(ce) == 1
    assert restored.node(ce[0])["attrs"]["observed_consequence"] == "unexpected"
