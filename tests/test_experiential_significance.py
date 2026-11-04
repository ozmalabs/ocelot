"""P17 standing relevance and recheck controls from verified outcomes."""
from test_qualia_behavior import _axis, _boot, _fresh, _tick


def test_significance_earned_from_outcomes():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1, outcome="restored", context="repair-context")
    _tick(s)
    _fresh(s, ag, 2, outcome="restored", context="repair-context")
    _tick(s)
    significance = s.nodes("ExperientialSignificance")
    assert len(significance) == 1
    assert s.node(significance[0])["attrs"]["status"] == "standing"
    assert s.node(significance[0])["attrs"]["support_count"] == 2.0


def test_same_feature_different_context_distinguished():
    s, ag = _boot()
    _axis(s, ag)
    for ix, context in enumerate(("context-a", "context-a", "context-b", "context-b"), 1):
        _fresh(s, ag, ix, outcome="restored", context=context)
        _tick(s)
    significance = {s.node(n)["attrs"]["context_id"]: s.node(n)["attrs"]
                    for n in s.nodes("ExperientialSignificance")}
    assert set(significance) == {"context-a", "context-b"}
    assert all(row["effect_category"] == "supportive" for row in significance.values())


def test_relevance_changes_attention():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1, outcome="restored", context="same")
    _tick(s)
    _fresh(s, ag, 2, outcome="restored", context="same")
    _tick(s)
    assert {s.node(n)["attrs"]["attention_priority"]
            for n in s.nodes("QualiaBehaviorPrediction")} == {"reuse_candidate"}


def test_confident_wrong_prediction_is_rechecked():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1, outcome="unexpected", context="counterexample")
    _tick(s)
    assert len(s.nodes("QualiaCounterexample")) == 1
    assert s.node(s.nodes("QualiaDimension")[-1])["attrs"]["acquisition_status"] == "retired"
