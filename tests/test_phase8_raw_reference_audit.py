from evaluation.phase8_raw_reference_audit import audit_raw_reference_runs


def _run(system, ids, *, failures=None, protocol="phase8a-fixed-phase0-corpus-v3"):
    if system == "eliza_floor":
        observations = [{"case_id": case_id, "output": "response"}
                        for case_id in ids]
    elif system in {"small_llm", "modern_llm"}:
        observations = [{"case_id": case_id,
                         "response": {"stdout": "response"}}
                        for case_id in ids]
    else:
        observations = [{"case_id": case_id, "response": "response"}
                        for case_id in ids]
    run = {
        "system": system,
        "protocol_id": protocol,
        "observations": observations,
        "collection_failures": failures or [],
        "scorecard": {"collection_status": "unavailable"},
    }
    if protocol == "phase8a-fixed-phase0-corpus-v5-event-context-history8":
        run["input_profile"] = "event_context_v5_history8"
        if system in {"eliza_floor", "small_llm", "modern_llm"}:
            run["session_history_limit"] = 8
    return run


def test_raw_reference_audit_checks_case_binding_without_scoring():
    corpus = {"protocol_id": "phase8a-fixed-phase0-corpus-v3",
              "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "eliza_floor": _run("eliza_floor", ["a", "b"]),
        "small_llm": _run("small_llm", ["a", "b"]),
        "modern_llm": _run("modern_llm", ["a", "b"]),
    })
    assert result["status"] == "incomplete"
    rows = {row["system"]: row for row in result["rows"]}
    assert result["status_counts"] == {
        "complete_raw": 1, "incomplete_raw": 2, "missing": 2,
    }
    assert rows["small_llm"]["minimum_run_count"] == 2
    assert rows["modern_llm"]["complete_run_count"] == 1
    assert result["score_interpretation_performed"] is False
    assert result["surface_text_used_as_evidence"] is False


def test_raw_reference_audit_fails_closed_on_duplicate_or_failed_case():
    corpus = {"protocol_id": "p", "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "eliza_floor": _run("eliza_floor", ["a", "a"], protocol="p"),
        "small_llm": _run("small_llm", ["a", "b"], failures=[{"case_id": "b"}], protocol="p"),
        "modern_llm": [
            _run("modern_llm", ["a", "b"], protocol="p"),
            _run("modern_llm", ["a", "b"], protocol="p"),
        ],
    })
    rows = {row["system"]: row for row in result["rows"]}
    assert rows["eliza_floor"]["status"] == "incomplete_raw"
    assert rows["eliza_floor"]["duplicate_case_count"] == 1
    assert rows["small_llm"]["status"] == "incomplete_raw"
    assert rows["small_llm"]["collection_failure_count"] == 1
    assert rows["modern_llm"]["status"] == "complete_raw"
    assert rows["modern_llm"]["run_count"] == 2


def test_raw_reference_audit_accepts_explicit_matched_input_protocol():
    corpus = {"protocol_id": "phase8a-fixed-phase0-corpus-v5-event-context-history8",
              "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "small_llm": [
            _run("small_llm", ["a", "b"],
                 protocol="phase8a-fixed-phase0-corpus-v5-event-context-history8"),
            _run("small_llm", ["a", "b"],
                 protocol="phase8a-fixed-phase0-corpus-v5-event-context-history8"),
        ],
    })
    row = next(item for item in result["rows"]
               if item["system"] == "small_llm")
    assert row["status"] == "complete_raw"
    assert row["run_count"] == 2
    assert row["protocol_match"] is True
    assert row["runs"][0]["input_profile_match"] is True
    assert result["status"] == "incomplete"
    assert result["human_reference_status"] == "missing"
    assert result["score_interpretation_performed"] is False


def test_v5_audit_rejects_run_with_protocol_label_but_wrong_profile():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    run = _run("modern_llm", ["a", "b"], protocol=protocol)
    run["input_profile"] = "isolated_signal_v4"
    corpus = {"protocol_id": protocol,
              "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {"modern_llm": [run, run]})
    row = next(item for item in result["rows"]
               if item["system"] == "modern_llm")
    assert row["status"] == "incomplete_raw"
    assert row["complete_run_count"] == 0
    assert row["runs"][0]["protocol_match"] is False
    assert row["runs"][0]["input_profile_match"] is False


def test_v5_audit_rejects_v4_signal_only_eliza_run():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol,
              "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        # A v4 signal-only ELIZA run must not be accepted as matched v5.
        "eliza_floor": _run("eliza_floor", ["a", "b"],
                            protocol="phase8a-fixed-phase0-corpus-v4"),
        "small_llm": [
            _run("small_llm", ["a", "b"], protocol=protocol),
            _run("small_llm", ["a", "b"], protocol=protocol),
        ],
        "modern_llm": [
            _run("modern_llm", ["a", "b"], protocol=protocol),
            _run("modern_llm", ["a", "b"], protocol=protocol),
        ],
    })
    rows = {row["system"]: row for row in result["rows"]}
    assert rows["eliza_floor"]["status"] == "incomplete_raw"
    assert rows["eliza_floor"]["complete_run_count"] == 0
    assert rows["base_human"]["status"] == "missing"
    assert rows["advanced_human"]["status"] == "missing"
    assert rows["small_llm"]["status"] == "complete_raw"
    assert rows["modern_llm"]["status"] == "complete_raw"
    assert result["status"] == "incomplete"
    assert result["score_interpretation_performed"] is False


def test_v5_audit_accepts_context_bound_eliza_floor_run():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol,
              "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "eliza_floor": _run("eliza_floor", ["a", "b"], protocol=protocol),
    })
    row = next(item for item in result["rows"]
               if item["system"] == "eliza_floor")
    assert row["status"] == "complete_raw"
    assert row["runs"][0]["input_profile_match"] is True
    assert result["score_interpretation_performed"] is False


def test_v5_audit_uses_typed_run_group_when_identity_field_is_null():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol,
              "events": [{"id": "a"}, {"id": "b"}]}
    run = _run("eliza_floor", ["a", "b"], protocol=protocol)
    run["system"] = None
    result = audit_raw_reference_runs(corpus, {"eliza_floor": run})
    row = next(item for item in result["rows"]
               if item["system"] == "eliza_floor")
    assert row["status"] == "complete_raw"
    assert row["runs"][0]["system_identity_match"] is True
    assert row["runs"][0]["system_identity_source"] == "typed_run_group_key"


def test_v5_audit_rejects_conflicting_explicit_run_identity():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol,
              "events": [{"id": "a"}, {"id": "b"}]}
    run = _run("eliza_floor", ["a", "b"], protocol=protocol)
    run["system"] = "small_llm"
    result = audit_raw_reference_runs(corpus, {"eliza_floor": run})
    row = next(item for item in result["rows"]
               if item["system"] == "eliza_floor")
    assert row["status"] == "incomplete_raw"
    assert row["runs"][0]["system_identity_match"] is False


def test_repeated_llm_runs_fail_closed_when_one_seed_is_incomplete():
    corpus = {"protocol_id": "p", "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "small_llm": [
            _run("small_llm", ["a", "b"], protocol="p"),
            _run("small_llm", ["a"], protocol="p"),
        ],
    })
    row = next(item for item in result["rows"] if item["system"] == "small_llm")
    assert row["status"] == "incomplete_raw"
    assert row["complete_run_count"] == 1
    assert row["run_count"] == 2
    assert row["score_interpretation_performed"] is False


def test_repeated_llm_audit_fails_closed_on_non_object_run():
    corpus = {"protocol_id": "p", "events": [{"id": "a"}, {"id": "b"}]}
    result = audit_raw_reference_runs(corpus, {
        "small_llm": [
            _run("small_llm", ["a", "b"], protocol="p"),
            _run("small_llm", ["a", "b"], protocol="p"),
            "invalid-run",
        ],
    })
    row = next(item for item in result["rows"] if item["system"] == "small_llm")
    assert row["status"] == "incomplete_raw"
    assert row["invalid_run_count"] == 1


def test_raw_audit_rejects_case_complete_run_with_missing_response_bodies():
    corpus = {"protocol_id": "p", "events": [{"id": "a"}, {"id": "b"}]}
    run = _run("small_llm", ["a", "b"], protocol="p")
    run["observations"][1]["response"]["stdout"] = "  "

    result = audit_raw_reference_runs(corpus, {"small_llm": [run, run]})

    row = next(item for item in result["rows"] if item["system"] == "small_llm")
    assert row["status"] == "incomplete_raw"
    assert row["complete_run_count"] == 0
    assert row["runs"][0]["missing_response_count"] == 1
    assert row["score_interpretation_performed"] is False


def test_human_raw_audit_requires_nonempty_response_text_per_case():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol, "events": [{"id": "a"}]}
    run = _run("base_human", ["a"], protocol=protocol)
    run["observations"][0]["response"] = ""

    result = audit_raw_reference_runs(corpus, {"base_human": run})

    row = next(item for item in result["rows"] if item["system"] == "base_human")
    assert row["status"] == "incomplete_raw"
    assert row["runs"][0]["missing_response_count"] == 1
    assert result["score_interpretation_performed"] is False


def test_human_reference_summary_tracks_complete_raw_classes():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol, "events": [{"id": "a"}]}
    runs = {
        system: _run(system, ["a"], protocol=protocol)
        for system in ("base_human", "advanced_human")
    }

    result = audit_raw_reference_runs(corpus, runs)

    assert result["human_reference_status"] == "complete_raw"
    assert result["status"] == "incomplete"  # the non-human classes are absent
    assert result["score_interpretation_performed"] is False


def test_human_reference_summary_marks_one_collected_class_incomplete():
    protocol = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
    corpus = {"protocol_id": protocol, "events": [{"id": "a"}]}
    result = audit_raw_reference_runs(corpus, {
        "base_human": _run("base_human", ["a"], protocol=protocol),
    })

    assert result["human_reference_status"] == "incomplete_raw"
