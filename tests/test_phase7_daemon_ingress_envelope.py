from evaluation.phase7_daemon_ingress_envelope import (
    SCHEMA,
    measure_daemon_ingress_envelope,
)


def test_daemon_chat_entrypoint_prepasses_before_parse_and_ingest(monkeypatch):
    from types import SimpleNamespace
    from scripts import jabberwock_daemon as daemon

    calls = []

    class Adapter:
        def classify_speech_act(self, text):
            calls.append(("classify", text))
            return "question"

        def ingest_turn(self, text, *, speech_act):
            calls.append(("ingest", text, speech_act))
            return SimpleNamespace(value=91)

    monkeypatch.setattr(
        daemon, "prepass_conversation_turn",
        lambda _adapter, text: calls.append(("prepass", text)))
    state = SimpleNamespace(adapter=Adapter(), pending_turns={})

    turn_id = daemon._ingest_daemon_chat_turn(
        state, "Did the sensor report it?")

    assert turn_id == 91
    assert calls == [
        ("prepass", "Did the sensor report it?"),
        ("classify", "Did the sensor report it?"),
        ("ingest", "Did the sensor report it?", "question"),
    ]
    assert state.pending_turns == {91: "Did the sensor report it?"}


def test_signal_only_daemon_ingress_uses_native_authority_without_external_io():
    report = measure_daemon_ingress_envelope(
        event_ids=["question_unavailable"],
        content_keys=[
            "answer", "are", "behind", "closed", "describe", "hello",
            "how", "it", "move", "no", "north", "object", "open",
            "the", "there", "think", "you",
        ],
    )

    assert report["event_count"] == 1
    assert report["schema"] == SCHEMA
    assert report["seed_selection_complete"] is True
    prepass = report["observations"][0]["content_prepass"]
    assert prepass["status"] == "loaded"
    assert prepass["selection_complete"] is True
    assert report["interpretation_count"] == 1
    assert report["disposition_authority_count"] == 1
    assert report["observations"][0]["cognitive_disposition"] == "blocked"
    # The fixed-corpus literal-form reference is not passed into this live text
    # boundary; the parser derives it from the inbound signal. Interaction
    # relation is separate typed transport evidence and is preserved by Phase
    # 6R.
    assert report["observations"][0]["literal_form"] == "interrogative"
    assert report["observations"][0]["interaction_relation"] == "standalone"
    assert report["external_io_performed"] is False
    assert report["errors"] == []
    assert report["resource_assertions"]["ingress_latency_bounded"] is True
    assert report["resource_assertions"]["native_cycle_latency_bounded"] is True
    assert report["rss_limit_bytes"] == 200 * 1024 * 1024


def test_daemon_ingress_can_measure_default_shadow_read_path():
    report = measure_daemon_ingress_envelope(
        event_ids=["standalone_assertion"], shadow_read=True)

    assert report["shadow_read_enabled"] is True
    assert report["deep_ingest_enabled"] is True
    assert report["seed_selection_complete"] is True
    assert report["errors"] == []


def test_daemon_ingress_graph_type_census_partitions_node_growth():
    report = measure_daemon_ingress_envelope(
        event_ids=["standalone_assertion"], graph_type_census=True)

    census = report["graph_type_census"]
    assert census is not None
    assert sum(census["before"].values()) == report["graph_before"]["nodes"]
    assert sum(census["after"].values()) == report["graph_after"]["nodes"]
    assert sum(census["growth"].values()) == report["graph_growth"]["nodes"]
    assert census["growth"]
    assert census["retention_details"]["Message"]["count"] > 0
    assert census["retention_details"]["Message"]["isolated_node_count"] == 0
    unknown = census["retention_details"]["Unknown"]
    assert unknown["count"] > 0
    assert unknown["isolated_node_count"] == 0
    sample = unknown["sample_nodes"][0]
    assert sample["attribute_keys"]
    assert sample["incoming_neighbors"]
    assert all(row["type"] == "Intent" for row in sample["incoming_neighbors"])
    assert sample["outgoing_neighbors"] == []


def test_daemon_textless_expected_acts_release_or_fail_closed():
    keys = [
        "answer", "are", "behind", "closed", "describe", "hello",
        "how", "it", "move", "no", "north", "object", "open",
        "the", "there", "think", "you",
    ]
    for event_id, expected_act in (
            ("standalone_assertion", "acknowledgment"),
            ("response_yes", "grant")):
        report = measure_daemon_ingress_envelope(
            event_ids=[event_id], content_keys=keys)

        lifecycle = report["graph_reply_candidates"][0]
        assert report["observations"][0]["reply_present"] is True, event_id
        assert lifecycle["graph_text_reply_ready"] is True, event_id
        assert len(lifecycle["messages"]) >= 2, event_id
        assert lifecycle["messages"][0]["speech_acts"] == [expected_act]
        assert lifecycle["messages"][0]["text_present"] is False
        assert lifecycle["messages"][-1]["floor"] == 1.0
        assert lifecycle["messages"][-1]["text_present"] is True
        assert lifecycle["reply_expectation"] == "expected"
        assert lifecycle["expected_response_acts"] == [expected_act]
        if event_id == "standalone_assertion":
            assert report["observations"][0]["explicit_error"] is False
            receipts = report["observations"][0]["production_receipts"]
            assert len(receipts) == 1
            assert receipts[0]["parse_back_mode"] == \
                "conversation_standalone_assertion_graph"
            assert receipts[0]["status"] == "released"
        else:
            assert report["observations"][0]["explicit_error"] is True
            assert report["observations"][0]["production_receipts"] == []


def test_daemon_releases_graph_selected_social_turn_through_production_gate():
    for event_id in ("social_greeting", "social_thanks"):
        report = measure_daemon_ingress_envelope(
            event_ids=[event_id],
            content_keys=[
                "answer", "are", "behind", "closed", "describe", "hello",
                "how", "it", "move", "no", "north", "object", "open",
                "the", "there", "think", "you",
            ],
        )

        assert report["turn_completion_count"] == 1, event_id
        assert report["pending_turn_count"] == 0, event_id
        assert report["observations"][0]["reply_present"] is True, event_id
        candidate = report["graph_reply_candidates"][0]
        assert candidate["graph_text_reply_ready"] is True, event_id
        assert candidate["messages"][0]["text_present"] is True, event_id
        receipts = report["observations"][0]["production_receipts"]
        assert len(receipts) == 1, (event_id, receipts)
        assert receipts[0]["parse_back_mode"] == "conversation_social_graph"
        assert receipts[0]["status"] == "released"


def test_daemon_releases_common_ground_ack_and_terminalizes_no_response():
    report = measure_daemon_ingress_envelope(
        event_ids=["acknowledgement", "response_no"],
        content_keys=[
            "answer", "are", "behind", "closed", "describe", "hello",
            "how", "it", "move", "no", "north", "object", "open",
            "the", "there", "think", "you",
        ],
        complete_host_actions=True,
        drain_timeout_s=2.0,
    )

    assert report["pending_turn_count"] == 0
    assert report["turn_completion_count"] == 2
    assert report["reply_release_count"] == 1
    assert report["no_reply_terminal_count"] == 1
    assert [sample["terminal_status"] for sample in report["samples"]] == [
        "reply_released", "no_response_expected",
    ]
    ack, no_reply = report["observations"]
    assert ack["reply_present"] is True
    assert ack["explicit_error"] is False
    assert ack["production_receipts"][0]["status"] == "released"
    assert ack["production_receipts"][0]["semantic_intent"] == \
        "acknowledge_receipt_without_endorsement"
    assert no_reply["reply_present"] is False
    assert [row["reply_expectation"] for row in
            report["graph_reply_candidates"]] == [
                "expected", "not_expected",
            ]
    assert report["graph_reply_candidates"][0][
        "expected_response_acts"] == ["acknowledgment"]
    assert report["graph_reply_candidates"][0]["graph_text_reply_ready"] is True
    assert report["graph_reply_candidates"][1]["graph_text_reply_ready"] is False


def test_daemon_honors_native_no_reply_slots_including_nonturn_repair():
    report = measure_daemon_ingress_envelope(
        event_ids=["overlap_signal", "fragment_question",
                   "continuation_answer", "offer_repair",
                   "question_unavailable", "repair_missing"],
        complete_host_actions=True,
        drain_timeout_s=2.0,
    )

    assert report["pending_turn_count"] == 0
    assert report["turn_completion_count"] == 6
    assert report["reply_release_count"] == 0
    assert report["no_reply_terminal_count"] == 6
    assert report["turn_completion_status_counts"] == {
        "no_response_expected": 6,
    }
    assert all(not item["reply_present"] and not item["explicit_error"]
               for item in report["observations"])
    missing = next(item for item in report["observations"]
                   if item["id"] == "repair_missing")
    assert missing["cognitive_disposition"] == "repair"
    assert missing["interpretation"]["arbitration_basis"] == \
        "nonturn_knowledge_deficit_repair"
    assert [row["reply_expectation"] for row in
            report["graph_reply_candidates"]] == ["not_expected"] * 6


def test_daemon_learning_questions_request_grounding_without_answering():
    report = measure_daemon_ingress_envelope(
        event_ids=["question_weather", "info_explanation"],
        complete_host_actions=True,
        offline_retrieval_miss=True,
        drain_timeout_s=2.0,
    )

    assert report["turn_completion_status_counts"] == {"reply_released": 2}
    assert report["reply_release_count"] == 2
    for observation in report["observations"]:
        assert observation["cognitive_disposition"] == "learn"
        assert observation["reply_present"] is True
        assert observation["explicit_error"] is False
        assert len(observation["production_receipts"]) == 1
        receipt = observation["production_receipts"][0]
        assert receipt["status"] == "released"
        assert receipt["parse_back_mode"] == "conversation_action_graph"
        assert receipt["semantic_intent"] == "request"
        assert receipt["semantic_event"] == "repair"
        assert receipt["coverage"] == 1.0
        assert receipt["withhold_reasons"] == []
        assert observation["turn"]["answer_commitment"] is None


def test_daemon_missing_world_question_asks_for_context_only():
    report = measure_daemon_ingress_envelope(
        event_ids=["info_world", "unavailable_world"],
        complete_host_actions=True,
        offline_retrieval_miss=True,
        drain_timeout_s=2.0,
    )

    assert report["turn_completion_status_counts"] == {
        "reply_released": 2,
    }
    context_question, imperative = report["observations"]
    assert context_question["cognitive_disposition"] == "blocked"
    assert context_question["interpretation"]["arbitration_basis"] == (
        "missing_world_information_request")
    assert context_question["reply_present"] is True
    assert context_question["explicit_error"] is False
    assert len(context_question["production_receipts"]) == 1
    assert context_question["production_receipts"][0][
        "parse_back_mode"] == "conversation_action_graph"
    assert context_question["turn"]["answer_commitment"] is None
    # The synchronous action-specific honest-no-world path is not an
    # interrogative context request; do not broaden this clarification gate.
    assert imperative["cognitive_disposition"] == "blocked"
    assert imperative["explicit_error"] is False
    assert len(imperative["production_receipts"]) == 1
    assert imperative["production_receipts"][0][
        "semantic_intent"] == "act"
    assert imperative["production_receipts"][0][
        "parse_back_mode"] == "conversation_action_graph"
    assert imperative["turn"]["answer_commitment"] is None


def test_daemon_requests_context_for_native_learning_and_unsupported_choice():
    report = measure_daemon_ingress_envelope(
        event_ids=["info_choice", "learn_uncertain", "repair_clarify",
                   "repair_missing", "blocked_permission"],
        complete_host_actions=True, offline_retrieval_miss=True,
        drain_timeout_s=2.0)

    assert report["turn_completion_status_counts"] == {
        "no_response_expected": 2, "reply_released": 3,
    }
    for observation in report["observations"][:3]:
        assert observation["reply_present"] is True
        assert observation["explicit_error"] is False
        assert len(observation["production_receipts"]) == 1
        receipt = observation["production_receipts"][0]
        assert receipt["status"] == "released"
        assert receipt["parse_back_mode"] == "conversation_action_graph"
        assert receipt["semantic_intent"] == "request"
        assert receipt["semantic_event"] == "repair"
        assert observation["turn"]["answer_commitment"] is None
    choice, uncertainty, reference_repair, nonturn_repair, negative = \
        report["observations"]
    assert choice["interpretation"]["arbitration_basis"] == \
        "indirect_request_force"
    assert choice["communication_route"] == "decision_context_repair_graph"
    assert uncertainty["cognitive_disposition"] == "learn"
    assert uncertainty["communication_route"] == "learning_context_repair_graph"
    assert reference_repair["interpretation"]["language_repair_evidence"] == \
        "unresolved_selection"
    assert reference_repair["communication_route"] == \
        "unresolved_reference_repair_graph"
    assert nonturn_repair["interpretation"]["interaction_mode"] == "non_turn"
    assert nonturn_repair["reply_present"] is False
    assert nonturn_repair["explicit_error"] is False
    assert nonturn_repair["production_receipts"] == []
    # Typed post-settle permission evidence selects blocked; it does not grant
    # authority or infer a reply/clarification.
    assert negative["cognitive_disposition"] == "blocked"
    assert negative["interpretation"]["authority_status"] == "missing"
    assert negative["explicit_error"] is False
    assert negative["reply_present"] is False
    assert negative["production_receipts"] == []


def test_daemon_action_faculty_releases_only_native_selected_requests():
    report = measure_daemon_ingress_envelope(
        event_ids=["direct_action", "action_sensor", "action_defer",
                   "unavailable_world", "response_yes"],
        complete_host_actions=True,
        offline_retrieval_miss=True,
        drain_timeout_s=2.0,
    )

    assert report["turn_completion_status_counts"] == {
        "error": 1, "reply_released": 4,
    }
    assert report["topic_grounding_http_request_count"] == 0
    for observation in report["observations"][:4]:
        assert observation["reply_present"] is True
        assert observation["explicit_error"] is False
        assert any(receipt["status"] == "released"
                   and receipt["parse_back_mode"] == "conversation_action_graph"
                   for receipt in observation["production_receipts"])
        assert observation["turn"]["answer_commitment"] is None
    # An unlinked "Yes, proceed" has defer authority, not action authority.
    assert report["observations"][4]["explicit_error"] is True
    assert report["observations"][4]["production_receipts"] == []


def test_daemon_asks_before_unresolved_standalone_actions_without_acting():
    report = measure_daemon_ingress_envelope(
        event_ids=["unknown_action", "action_unknown", "repair_missing",
                   "blocked_permission"],
        complete_host_actions=True, offline_retrieval_miss=True,
        drain_timeout_s=2.0)

    assert report["turn_completion_status_counts"] == {
        "no_response_expected": 2, "reply_released": 2,
    }
    for observation in report["observations"][:2]:
        assert observation["reply_present"] is True
        assert observation["explicit_error"] is False
        assert observation["communication_route"] == \
            "unresolved_standalone_repair_graph"
        assert observation["turn"]["answer_commitment"] is None
        commitment = observation["turn"]["reply_commitment"]
        assert commitment["graph_linked_to_turn"] is True
        assert commitment["speech_acts"] == ["clarification"]
        assert commitment["trouble_source"] in {"Quorplezap", "Blorf"}
        assert len(observation["production_receipts"]) == 1
        assert observation["production_receipts"][0][
            "parse_back_mode"] == "conversation_action_graph"
    # Continuation repair and missing-permission block retain typed non-turn
    # boundaries without an error or surface reply.
    assert report["observations"][2]["reply_present"] is False
    assert report["observations"][2]["explicit_error"] is False
    assert report["observations"][3]["cognitive_disposition"] == "blocked"
    assert report["observations"][3]["explicit_error"] is False
    assert report["observations"][3]["reply_present"] is False
    assert report["observations"][3]["production_receipts"] == []


def test_daemon_releases_only_native_supported_direct_held_answer():
    report = measure_daemon_ingress_envelope(
        event_ids=["question_referent"], complete_host_actions=True,
        offline_retrieval_miss=True, drain_timeout_s=2.0)

    observation = report["observations"][0]
    assert report["turn_completion_status_counts"] == {"reply_released": 1}
    assert observation["reply_present"] is True
    assert observation["explicit_error"] is False
    # The direct readback consumes an existing supported HeldAnswer; it does
    # not create a new answer commitment in discourse state.
    assert observation["turn"]["answer_commitment"] is None
    assert len(observation["production_receipts"]) == 1
    receipt = observation["production_receipts"][0]
    assert receipt["status"] == "released"
    assert receipt["parse_back_mode"] == "conversation_information_graph"


def test_daemon_selects_native_block_for_unresolved_nonturn_permission():
    report = measure_daemon_ingress_envelope(
        event_ids=["blocked_permission"], complete_host_actions=True,
        drain_timeout_s=2.0)

    assert report["turn_completion_status_counts"] == {
        "no_response_expected": 1,
    }
    observation = report["observations"][0]
    assert observation["cognitive_disposition"] == "blocked"
    assert observation["explicit_error"] is False
    assert observation["reply_present"] is False
    assert observation["interpretation"]["authority_status"] == "missing"


def test_post_comprehension_authority_refresh_needs_typed_graph_links():
    from substrate.boot_profiles import load_conversation_seed_profile
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=())
    load_conversation_seed_profile(agent)
    text = "Can I access the sealed room?"
    inbound = agent.ingest_turn(
        text, speech_act=agent.classify_speech_act(text),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"})
    agent.comprehend()
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    assert agent._permission_request_evidence(inbound) is None

    assert agent.settle_post_comprehension_authority([inbound]) == 0
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["authority_status"] == "not_applicable"
    assert attrs["cognitive_disposition"] is None
    assert attrs["arbitration_basis"] != "missing_permission_authority"


def test_daemon_completes_seed_generated_grounding_before_reply_release(monkeypatch):
    """Exercise the production-shaped generic host action, not a synthetic
    GroundRequest-sourced action, and keep retrieval transport graph-free.
    """
    from substrate.boot_profiles import load_conversation_seed_profile
    from substrate.world_adapter import WorldAdapter
    from scripts import jabberwock_daemon as daemon
    from domains import topic_grounding as tg

    agent = WorldAdapter(seeds=())
    selection = load_conversation_seed_profile(
        agent,
        content_keys=[
            "answer", "are", "behind", "closed", "describe", "hello",
            "how", "it", "move", "no", "north", "object", "open",
            "the", "there", "think", "you", "what", "know", "about",
            "moon",
        ],
    )
    assert selection["selection_complete"] is True
    daemon._ensure_supervisory_scheduler(agent)
    monkeypatch.setattr(tg, "ground_local_attempt",
                        lambda *_args, **_kwargs: {"settled": False, "answer": None})
    monkeypatch.setattr(
        tg, "retrieve_ground_payload",
        lambda query, aspect=None, **_kwargs: {
            "attempts": [{
                "phrase": query,
                "answer": "The Moon is Earth's natural satellite.",
            }],
        },
    )
    monkeypatch.setattr(tg, "detail_local_chunks", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        tg, "retrieve_detail_payload",
        lambda *_args, **_kwargs: ["The Moon has no permanent natural satellites."],
    )
    state = daemon.DaemonState(agent, "daemon-grounding-completion-test")
    text = "What do you know about the moon?"
    inbound = agent.ingest_turn(text, speech_act=agent.classify_speech_act(text))
    state.pending_turns[int(inbound.value)] = text

    try:
        budget, quantum = daemon._async_cycle_budget(agent)
        steps = agent.tick(max_steps=quantum) if quantum else agent.tick()
        if quantum:
            daemon._record_async_cycle_consumption(agent, budget, quantum, steps)
        agent.comprehend()
        assert agent.graph_turn_reply(inbound) is None

        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        host = next(iter(agent.s.nodes("HostActionRequest")))
        ground = next(iter(agent.s.nodes("GroundRequest")))
        search = next(iter(agent.s.nodes("SearchRequest")))
        assert agent.s.node(host)["attrs"]["status"] == "io_pending"
        assert agent.s.node(ground)["attrs"]["status"] == "running"
        assert agent.s.node(search)["attrs"]["status"] == "requested"
        assert agent.graph_turn_reply(inbound) is None

        pending = state.pending_search_host_actions[int(host.value)]
        assert pending["jobs"][0]["kind"] == "ground"
        pending["jobs"][0]["future"].result(timeout=5)
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 1
        assert agent.s.node(host)["attrs"]["status"] == "done"
        assert agent.s.node(ground)["attrs"]["status"] == "done"
        assert agent.s.node(search)["attrs"]["status"] == "superseded"
        assert len(list(agent.inner.neighbours(host, "has_receipt"))) == 1

        for _ in range(4):
            budget, quantum = daemon._async_cycle_budget(agent)
            steps = agent.tick(max_steps=quantum) if quantum else agent.tick()
            if quantum:
                daemon._record_async_cycle_consumption(agent, budget, quantum, steps)
            agent.comprehend()
            if agent.graph_turn_reply(inbound) is not None:
                break
        assert agent.graph_turn_reply(inbound) == \
            "The Moon is Earth's natural satellite."
    finally:
        state.search_io_executor.shutdown(wait=True, cancel_futures=True)


def test_completion_envelope_drains_seed_generated_async_turn(monkeypatch):
    from domains import topic_grounding as tg

    monkeypatch.setattr(tg, "ground_local_attempt",
                        lambda *_args, **_kwargs: {"settled": False, "answer": None})
    monkeypatch.setattr(
        tg, "retrieve_ground_payload",
        lambda query, aspect=None, **_kwargs: {
            "attempts": [{
                "phrase": query,
                "answer": "The Moon is Earth's natural satellite.",
            }],
        },
    )
    monkeypatch.setattr(tg, "detail_local_chunks", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        tg, "retrieve_detail_payload",
        lambda *_args, **_kwargs: ["The Moon has no permanent natural satellites."],
    )
    report = measure_daemon_ingress_envelope(
        corpus={"events": [{
            "id": "seeded_moon_question",
            "signal": "What do you know about the moon?",
        }]},
        content_keys=[
            "answer", "are", "behind", "closed", "describe", "hello",
            "how", "it", "move", "no", "north", "object", "open",
            "the", "there", "think", "you", "what", "know", "about",
            "moon",
        ],
        complete_host_actions=True,
        drain_timeout_s=2.0,
    )

    assert report["seed_selection_complete"] is True
    assert report["host_action_dispatch_performed"] is True
    assert report["retrieval_io_submitted"] is True
    assert report["external_io_performed"] is False
    assert report["topic_grounding_http_request_count"] == 0
    assert report["host_actions_completed"] >= 2
    assert report["turn_completion_count"] == 1
    assert report["pending_turn_count"] == 0
    assert report["pending_host_action_count"] == 0, report["pending_host_actions"]
    assert report["pending_host_action_io_count"] == 0
    assert report["observations"][0]["reply_present"] is True
    assert report["host_action_drain_timed_out"] is False
    assert len(report["search_request_lifecycle"]) >= 1
    assert all("linked_host_actions" in row
               for row in report["search_request_lifecycle"])


def test_completion_envelope_runs_generic_fallback_after_specific_ground_miss(
        monkeypatch):
    from domains import topic_grounding as tg

    monkeypatch.setattr(tg, "ground_local_attempt",
                        lambda *_args, **_kwargs: {"settled": False, "answer": None})
    monkeypatch.setattr(tg, "retrieve_ground_payload",
                        lambda *_args, **_kwargs: {"attempts": []})
    monkeypatch.setattr(tg, "retrieve_search_candidate_payloads",
                        lambda *_args, **_kwargs: [])
    monkeypatch.setattr(tg, "detail_local_chunks", lambda *_args, **_kwargs: [])
    report = measure_daemon_ingress_envelope(
        corpus={"events": [{
            "id": "seeded_moon_question",
            "signal": "What do you know about the moon?",
        }]},
        content_keys=[
            "answer", "are", "behind", "closed", "describe", "hello",
            "how", "it", "move", "no", "north", "object", "open",
            "the", "there", "think", "you", "what", "know", "about",
            "moon",
        ],
        complete_host_actions=True,
        drain_timeout_s=2.0,
    )
    assert report["host_action_drain_timed_out"] is False
    assert report["pending_search_request_count"] == 0, report[
        "search_request_lifecycle"]


def test_unknown_topic_completes_as_graph_selected_repair_without_network(
        monkeypatch):
    """An exhausted unknown-topic lookup must release the native repair."""
    from domains import topic_grounding as tg

    monkeypatch.setattr(
        tg, "ground_local_attempt",
        lambda *_args, **_kwargs: {"settled": False, "answer": None},
    )
    monkeypatch.setattr(
        tg, "retrieve_ground_payload",
        lambda *_args, **_kwargs: {"attempts": []},
    )
    monkeypatch.setattr(tg, "retrieve_search_candidate_payloads",
                        lambda *_args, **_kwargs: [])
    monkeypatch.setattr(tg, "detail_local_chunks", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(tg, "retrieve_detail_payload",
                        lambda *_args, **_kwargs: [])

    report = measure_daemon_ingress_envelope(
        event_ids=["info_unknown"],
        complete_host_actions=True,
        drain_timeout_s=2.0,
    )

    observation = report["observations"][0]
    assert report["seed_selection_complete"] is True
    assert report["host_actions_completed"] >= 1
    assert report["turn_completion_count"] == 1
    assert report["pending_turn_count"] == 0
    assert report["pending_host_action_count"] == 0
    assert report["host_action_drain_timed_out"] is False
    assert report["external_io_performed"] is False
    assert report["topic_grounding_http_request_count"] == 0
    assert observation["cognitive_disposition"] == "repair"
    assert observation["reply_present"] is True
    assert observation["explicit_error"] is False
    receipt = observation["production_receipts"][0]
    assert receipt["status"] == "released"
    assert receipt["semantic_event"] == "repair"
    assert receipt["parse_back_mode"] == "conversation_action_graph"
    assert observation["turn"]["reply_commitment"]["trouble_source"] == "blorf"


def test_full_connected_daemon_replay_terminalizes_with_offline_retrieval():
    """A no-hit host-action drain must close all turns without network I/O."""

    report = measure_daemon_ingress_envelope(
        complete_host_actions=True,
        offline_retrieval_miss=True,
        drain_timeout_s=5.0,
    )

    assert report["seed_selection_complete"] is True
    assert report["event_count"] == 74
    assert report["turn_completion_count"] == 74
    assert report["pending_turn_count"] == 0
    assert report["pending_turn_events"] == []
    assert report["host_action_dispatch_performed"] is True
    assert report["retrieval_fixture"] == "offline_miss"
    assert report["host_actions_completed"] > 0
    assert report["pending_host_action_count"] == 0
    assert report["pending_search_request_count"] == 0
    assert report["host_action_drain_timed_out"] is False
    assert report["external_io_performed"] is False
    assert report["topic_grounding_http_request_count"] == 0

    observations = {row["id"]: row for row in report["observations"]}
    unknown = observations["info_unknown"]
    assert unknown["cognitive_disposition"] == "repair"
    assert unknown["production_receipts"][0]["semantic_event"] == "repair"
    assert unknown["production_receipts"][0]["status"] == "released"
    source_recall = observations["question_source"]
    assert source_recall["communication_route"] == \
        "reported_content_recall_graph"
    assert source_recall["production_receipts"][0]["parse_back_mode"] == \
        "conversation_reported_content_graph"
