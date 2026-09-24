from evaluation.phase8_raw_reference_audit import audit_raw_reference_runs


def _run(system, ids, *, failures=None, protocol="phase8a-fixed-phase0-corpus-v3"):
    return {
        "system": system,
        "protocol_id": protocol,
        "observations": [{"case_id": case_id, "response": {}}
                         for case_id in ids],
        "collection_failures": failures or [],
        "scorecard": {"collection_status": "unavailable"},
    }


def test_raw_reference_audit_checks_case_binding_without_scoring():
    corpus = {"protocol_id": "phase8a-fixed-phase0-corpus-v3",
              "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "eliza_floor": _run("eliza_floor", ["a", "b"]),
        "small_llm": _run("small_llm", ["a", "b"]),
        "modern_llm": _run("modern_llm", ["a", "b"]),
    })
    assert result["status"] == "incomplete"
    assert result["status_counts"] == {"complete_raw": 3, "missing": 2}
    assert result["score_interpretation_performed"] is False
    assert result["surface_text_used_as_evidence"] is False


def test_raw_reference_audit_fails_closed_on_duplicate_or_failed_case():
    corpus = {"protocol_id": "p", "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "eliza_floor": _run("eliza_floor", ["a", "a"], protocol="p"),
        "small_llm": _run("small_llm", ["a", "b"], failures=[{"case_id": "b"}], protocol="p"),
        "modern_llm": _run("modern_llm", ["a", "b"], protocol="p"),
    })
    rows = {row["system"]: row for row in result["rows"]}
    assert rows["eliza_floor"]["status"] == "incomplete_raw"
    assert rows["eliza_floor"]["duplicate_case_count"] == 1
    assert rows["small_llm"]["status"] == "incomplete_raw"
    assert rows["small_llm"]["collection_failure_count"] == 1
    assert rows["modern_llm"]["status"] == "complete_raw"
