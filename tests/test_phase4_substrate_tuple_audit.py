"""The substrate audit prevents accidental promotion of partial cognition."""

from evaluation.phase4_substrate_tuple_audit import audit_phase4_tuple_sources


def test_seed_audit_finds_no_complete_unapproved_phase4_tuple():
    report = audit_phase4_tuple_sources(".")
    assert report["exact_count"] == 0
    assert all(item["type"] in report["approved_source_types"] for item in report["exact"])


def test_dual_process_seed_is_a_near_match_not_a_phase4_source():
    report = audit_phase4_tuple_sources(".")
    # Its dimensions live in production terms rather than a complete node
    # record, so the seed audit must not mistake that substrate for a source.
    assert not [item for item in report["exact"] if item["path"] == "seeds/dual_process_core.json"]
