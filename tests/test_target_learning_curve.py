"""P20 development check: both fresh and mapped target arms learn in both worlds."""
from evaluation.process_mastery.target_learning_curve import run_development_panel


def test_development_learning_curve_runs_both_adapters_across_both_pairs():
    result = run_development_panel(streams_per_pair=1)
    assert result["status"] == "development_only"
    assert result["domain_pairs"] == ["heat_to_thermal", "lever_to_latch"]
    assert len(result["records"]) == 4
    assert all(row["target_actions"] > 0 and row["native_rule_steps"] > 0
               and row["graph"]["nodes"] > 0 for row in result["records"])
    assert result["paired_auc_difference_mapped_minus_fresh"] < 0
    assert result["resources"]["mapped_source"]["mean_source_information_units"] > 0
    for pair in result["domain_pairs"]:
        rows = [row for row in result["records"] if pair in row["stream_id"]]
        assert {row["arm"] for row in rows} == {"fresh", "mapped_source"}
        fresh = next(row for row in rows if row["arm"] == "fresh")
        mapped = next(row for row in rows if row["arm"] == "mapped_source")
        assert fresh["curve"][-1] == {"target_interactions": 2, "success": 1}
        assert mapped["curve"][-1] == {"target_interactions": 3, "success": 1}
        assert mapped["map_status"] == "verified"
        assert mapped["target_effect_status"] == "verified"
