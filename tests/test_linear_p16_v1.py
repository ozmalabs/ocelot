from evaluation.process_mastery.analyze_linear_p16_v1 import analyze, _integrity_controls
from evaluation.process_mastery.linear_p16_v1 import run


def test_p16_development_selfcheck_covers_both_native_arms_and_controls():
    scorecard = run(split="development", self_check=True)
    report = analyze(scorecard)
    tampering = _integrity_controls(scorecard)

    assert report["registered_conformance_status"] == "PASS", report["failures"]
    assert report["rows"] == 8
    assert report["paired_worlds"] == 4
    assert all(control["passed"] == control["n"] == 2
               for control in report["controls"].values())
    assert tampering["passed"] == tampering["n"] == 5
    assert all(report["families"][family][arm]["receipt_verified"] == 2
               for family in ("permutation", "state_dependent_tool")
               for arm in ("primitive_search", "graph_expression"))
