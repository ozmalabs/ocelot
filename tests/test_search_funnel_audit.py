"""P23.03 attempt lineage, novelty deduplication, and cost accounting."""
from pathlib import Path

from evaluation.process_mastery.search_funnel_audit import audit_branch


ROOT = Path(__file__).resolve().parents[1]
D4 = ROOT / "evaluation/process_mastery/results/"


def _d4_branch():
    return audit_branch(D4 / "p22_training_panel_registered_root_d4_g2_"
        "0992_0993_ticks120_depth3.json")


def test_funnel_conserves_attempt_counts():
    report = _d4_branch()
    assert report["cumulative_graph_attempts"] == (
        report["inherited_graph_attempts"] + report["attempts"]["new"])
    assert report["attempts"]["status_count_conserved"]
    assert sum(report["attempts"]["by_status"].values()) == report["attempts"]["new"]
    assert report["request_attempt_total_cumulative"] == report["cumulative_graph_attempts"]
    assert report["funnel"]["attempt_to_expression_gap_is_uninstrumented"] == \
        report["attempts"]["unlinked_from_candidate_summary"]


def test_duplicate_effect_not_new_candidate():
    report = _d4_branch()
    assert "#57642" in report["candidate_effect_duplicates"]
    assert "#46754" in report["candidate_effects_excluded_as_identity_or_parent_held"]
    assert report["funnel"]["new_legal_unique_effects"] == 0


def test_trial_budget_distinguished_from_search_budget():
    report = _d4_branch()
    assert report["request_attempt_ceiling_each"]
    assert report["candidate_transfer_depth"] == 3
    assert report["funnel"]["new_independent_goal_trials"] == 882
    assert report["independent_trial_budget"].startswith(
        "not a search-attempt ceiling")
    assert report["funnel"]["attempts_new"] == 20_000

    loopover = audit_branch(D4 / "p22_training_panel_registered_root_loopover_g1_"
        "0980_0983_ticks120_depth3.json")
    assert loopover["candidate_transfer_depth"] == 3
    assert loopover["funnel"]["new_independent_goal_trials"] == 0
    assert loopover["request_attempt_headroom_total"] == 0
    assert loopover["global_attempt_headroom"] > 0


def test_rejection_has_exact_predicate_and_parent():
    report = _d4_branch()
    rejections = {row["candidate_id"]: row for row in report["candidate_rejections"]}
    assert rejections["#46754"]["predicate"] == \
        "iip_novel_effect_guard.active_or_adopted_effect"
    assert rejections["#57642"]["predicate"] == "unique_effect_deduplication"
    for row in rejections.values():
        assert row["parent_checkpoint_id"] == "p22-d4-g2-84854777d0e3"
        assert row["parent_checkpoint_digest"] == \
            "d8a916474c8e3bafd44dda0082fd7c71ccb3dac1c0a2daf9bbe7f759c70fb4df"
        assert row["source_attempt_ids"]
