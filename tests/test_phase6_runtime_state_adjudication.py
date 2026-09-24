from evaluation.phase6_runtime_state_adjudication import adjudicate_runtime_state


def _event(case_id, state="defer"):
    return {"id": case_id, "expected_state": state}


def test_separates_graph_mismatch_from_interpretation_authority_gap():
    corpus = {"events": [_event("graph"), _event("interpretation"), _event("match")]}
    report = {"runtime_state_diagnostics": [
        {"id": "graph", "observed_state": "act", "match": False,
         "authority": "graph_readback", "source": "graph_resident_goal_lifecycle",
         "evidence_available": True, "release_state": "released"},
        {"id": "interpretation", "observed_state": "act", "match": False,
         "authority": "interpretation_readback_not_disposition",
         "source": "graph_resident_communication_interpretation",
         "evidence_available": True, "release_state": "released"},
        {"id": "match", "observed_state": "defer", "match": True,
         "authority": "graph_readback", "source": "graph_resident_goal_lifecycle",
         "evidence_available": True, "release_state": "released"},
    ]}
    result = adjudicate_runtime_state(report, corpus)
    assert result["status"] == "measured"
    assert result["category_counts"] == {
        "disposition_authority_missing": 1,
        "graph_cognitive_state_mismatch": 1,
        "state_match": 1,
    }
    assert result["reply_text_used_as_evidence"] is False
    assert result["receipt_semantics_used_as_cognitive_state"] is False


def test_missing_diagnostics_fail_closed():
    result = adjudicate_runtime_state(
        {"runtime_state_diagnostics": []}, {"events": [_event("missing")]})
    assert result["status"] == "incomplete"
    assert result["missing_diagnostic_ids"] == ["missing"]


def test_current_corpus_observations_are_reused_without_surface_evidence():
    result = adjudicate_runtime_state(
        {"observations": [{
            "id": "current",
            "expected_state": "defer",
            "observed_state": "repair",
            "state_match": False,
            "cognitive_state_evidence_source":
                "graph_resident_communication_interpretation",
            "cognitive_state_authority":
                "interpretation_readback_not_disposition",
            "cognitive_state_evidence_available": True,
            "release_state": "error",
        }]},
        {"events": [{"id": "current", "expected_state": "defer"}]},
    )
    assert result["status"] == "measured"
    assert result["category_counts"] == {
        "disposition_authority_missing": 1,
    }
    assert result["reply_text_used_as_evidence"] is False
