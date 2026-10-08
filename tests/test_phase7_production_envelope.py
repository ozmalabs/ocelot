"""Focused tests for the bounded Phase 7 production-shaped envelope."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from evaluation.phase7_production_envelope import (  # noqa: E402
    PROFILE_EVENT_IDS,
    SCHEMA,
    compare_seed_profile_corpus,
    measure_production_envelope,
)
from substrate.boot_profiles import load_conversation_seed_profile  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
import evaluation.phase7_production_envelope as phase7  # noqa: E402
import substrate.world_adapter as world_adapter  # noqa: E402


def test_project_rss_cap_is_150_mib_across_active_envelopes():
    expected = 150 * 1024 * 1024
    from evaluation.phase7_semantic_event_envelope import (
        RSS_GROWTH_LIMIT as semantic_rss_limit,
    )
    from evaluation.native_cycle_measurement import (
        _RSS_GROWTH_LIMIT as native_rss_limit,
    )

    assert phase7.RSS_GROWTH_LIMIT == expected
    assert semantic_rss_limit == expected
    assert native_rss_limit == expected
    assert world_adapter._PROCESS_HEAP_TRIM_RSS_LIMIT_BYTES == expected


def test_connected_prepass_uses_same_mechanical_tokens_as_message_ingress():
    events = [
        {"signal": "Can you check the pump?"},
        {"signal": "Blorf, please."},
    ]

    assert phase7._event_content_candidates(events) == [
        "blorf", "can", "check", "please", "pump", "the", "you",
    ]
    assert WorldAdapter.lexical_candidates(events[0]["signal"]) == [
        "can", "you", "check", "the", "pump",
    ]


def test_heap_trim_skips_allocator_scan_below_rss_cap_and_runs_at_cap(monkeypatch):
    calls = []
    monkeypatch.setattr(world_adapter, "_PROCESS_HEAP_TRIM_UNAVAILABLE", False)
    monkeypatch.setattr(world_adapter, "_PROCESS_HEAP_TRIM_FUNCTION",
                        lambda _padding: calls.append("trim") or 1)
    monkeypatch.setattr(world_adapter, "_current_process_rss_bytes",
                        lambda: world_adapter._PROCESS_HEAP_TRIM_RSS_LIMIT_BYTES - 1)
    assert world_adapter._trim_reclaimable_process_heap() is False
    assert calls == []

    monkeypatch.setattr(world_adapter, "_current_process_rss_bytes",
                        lambda: world_adapter._PROCESS_HEAP_TRIM_RSS_LIMIT_BYTES)
    assert world_adapter._trim_reclaimable_process_heap() is True
    assert calls == ["trim"]


@pytest.fixture(scope="module")
def report():
    return measure_production_envelope()


def test_production_envelope_has_structural_graph_and_resource_evidence(report):
    assert report["schema"] == SCHEMA
    assert report["event_count"] == len(PROFILE_EVENT_IDS)
    assert len(report["observations"]) == len(PROFILE_EVENT_IDS)
    assert report["errors"] == []
    assert report["graph_growth"]["nodes"] > 0
    assert report["graph_growth"]["discourse_events"] == len(PROFILE_EVENT_IDS)
    # This is an observation gate, not a disguised pass condition.  The
    # current cold communication workload records the bound explicitly; the
    # Phase 7 exit remains yellow while the measured value is false.
    assert report["resource_assertions"]["rss_measured"] is True
    assert isinstance(report["resource_assertions"]["rss_growth_bounded"], bool)
    assert report["resource_assertions"]["steady_state_rss_growth_bounded"] is True
    # Zero is valid when there are no lazy first-event imports or measurable
    # post-boot RSS growth; this envelope measures growth and must not require
    # the old reference-label-driven cold-start allocation shape.
    assert report["cold_start_rss_growth_bytes"] >= 0
    assert report["steady_state_rss_growth_bytes"] >= 0
    assert report["surface_text_used_as_semantics"] is False
    assert report["turn_boundary_required"] is False


def test_production_envelope_preserves_typed_non_turn_and_overlap_evidence(report):
    rows = {row["id"]: row for row in report["observations"]}
    overlap = rows["overlap_signal"]
    assert overlap["interaction_mode"] == "non_turn"
    assert overlap["interaction_relation"] == "overlap"
    assert overlap["literal_form"] == "fragment"
    assert overlap["event_payload_relation"] == "overlap"
    assert overlap["event_payload_literal_form"] in {None, ""}
    assert overlap["cognitive_disposition"] == "defer"


def test_production_envelope_replay_is_structurally_deterministic(report):
    assert report["replay_equal"] is True
    assert report["replay_difference"] is None


def test_production_envelope_exposes_boot_and_event_cost_without_semantic_use(report):
    assert report["boot_elapsed_ms"] >= 0.0
    assert report["boot_rss_growth_bytes"] >= 0
    assert report["boot_and_event_rss_growth_bytes"] >= 0
    assert isinstance(
        report["resource_assertions"]["boot_and_event_rss_growth_bounded"],
        bool,
    )
    assert len(report["rss_samples"]) == len(PROFILE_EVENT_IDS)
    assert all(sample["elapsed_ms"] >= 0.0
               and sample["rss_delta_bytes"] >= 0
               for sample in report["rss_samples"])
    assert all("graph_delta" in sample for sample in report["rss_samples"])
    assert all(
        sample["pending_io_dispatch"]["call_count"] >= 0
        and sample["pending_io_dispatch"]["total_ms"] >= 0.0
        and sample["pending_io_dispatch"]["max_ms"] >= 0.0
        for sample in report["rss_samples"]
    )
    assert report["surface_text_used_as_semantics"] is False


def test_connected_profile_prepass_grounds_instruction_without_execution(report):
    selected = measure_production_envelope(seed_profile="conversation")

    assert selected["seed_profile"] == "conversation"
    assert selected["replay_equal"] is True
    assert selected["errors"] == report["errors"] == []
    assert selected["resource_assertions"]["rss_measured"] is True

    # The connected profile's ingress-token prepass selects lexical providers,
    # making grounding parity available before the turn. This is still not
    # action execution: the graph reports the instruction as handled without
    # claiming an execution faculty/world is attached.
    full_action = next(
        row for row in report["observations"] if row["id"] == "direct_action"
    )
    connected_action = next(
        row for row in selected["observations"] if row["id"] == "direct_action"
    )
    assert full_action["interpretation"]["grounding_status"] == "candidate_grounded"
    assert full_action["message"]["communication_route"] == "goal_only"
    assert connected_action["interpretation"]["grounding_status"] == "candidate_grounded"
    assert connected_action["message"]["communication_route"] == "goal_only"
    assert connected_action["message"]["instruction_outcome"] == "handled"
    assert any(goal.get("kind") == "instruction" and goal.get("event_bound")
               for goal in connected_action["turn"]["goals"])


def test_seed_content_and_instruction_closure_restore_direct_action_parity():
    comparison = compare_seed_profile_corpus(
        event_ids=["direct_action"],
        content_keys=["open", "the", "north"],
        scoped_content_refs={
            "wordnet_common_objects": [
                {"type": "Concept", "name": "gate"},
            ],
        },
    )
    full = comparison["profiles"]["full"]["observations"][0]
    connected_run = comparison["profiles"]["conversation"]
    connected = connected_run["observations"][0]

    assert connected_run["selection_complete"] is True
    assert connected_run["content_slices"]["learned_lexicon"][
        "matched_node_count"] == 3
    assert comparison["structural_parity"]["equal"] is True
    assert connected == full


def test_info_status_trace_parity_prefers_specific_topic_grounding():
    comparison = compare_seed_profile_corpus(
        event_ids=["info_status"],
        content_keys=["what", "the", "sensor", "status"],
    )

    assert comparison["structural_parity"]["equal"] is True
    full = comparison["profiles"]["full"]["observations"][0]
    connected = comparison["profiles"]["conversation"]["observations"][0]
    expected_path = (
        "CommunicationInterpretation -> HeldAnswer -> "
        "TopicGroundingEvidence")
    assert full["interpretation"]["grounding_evidence_path"] == expected_path
    assert connected["interpretation"]["grounding_evidence_path"] == expected_path


def test_structural_parity_strips_commitment_graph_identity_numbers():
    from evaluation.phase7_production_envelope import _parity_value

    value = {
        "kind": "supported_event_bound_reflective_answer",
        "graph_linked_to_turn": True,
        "evidence_id": 120,
        "production_receipt_id": 121,
    }

    assert _parity_value(value) == {
        "kind": "supported_event_bound_reflective_answer",
        "graph_linked_to_turn": True,
    }


def test_scoped_lexical_content_refs_preserve_single_event_parity():
    from evaluation.conversational_manifold_phase0 import load_corpus
    from substrate.boot_all import load_all_seeds

    event = next(
        row for row in load_corpus()["events"]
        if row["id"] == "standalone_assertion"
    )
    full = WorldAdapter(seeds=())
    load_all_seeds(full)
    full_reply = full.converse(
        event["signal"], speech_act=phase7._speech_act(event),
        context=phase7._runtime_context(event)) or ""
    full_observation = phase7._stable_observation(
        full, event, full_reply, full._last_turn_inbound)

    connected = WorldAdapter(seeds=())
    report = load_conversation_seed_profile(
        connected,
        scoped_content_refs={
            "learned_lexicon": [
                {"type": "Concept", "name": "the"},
                {"type": "Concept", "name": "sky"},
                {"type": "Concept", "name": "blue"},
            ],
            "colour_meaning": [
                {"type": "Concept", "name": "blue"},
            ],
        },
    )
    connected_reply = connected.converse(
        event["signal"], speech_act=phase7._speech_act(event),
        context=phase7._runtime_context(event)) or ""
    connected_observation = phase7._stable_observation(
        connected, event, connected_reply, connected._last_turn_inbound)

    assert report["selection_complete"] is True
    assert report["selection"]["unresolved"][
        "missing_scoped_content_refs"] == []
    assert report["content_slices"]["learned_lexicon"][
        "matched_node_count"] == 3
    assert connected_observation == full_observation


def test_connected_profile_candidate_prepass_matches_eight_event_corpus():
    comparison = compare_seed_profile_corpus(
        event_ids=PROFILE_EVENT_IDS,
    )

    assert comparison["profiles"]["conversation"]["selection_complete"] is True
    assert comparison["structural_parity"]["equal"] is True
    assert comparison["structural_parity"]["matched_event_count"] == len(
        PROFILE_EVENT_IDS)
    assert comparison["structural_parity"]["mismatches"] == []
    assert comparison["content_candidate_prepass"]["corpus_labels_used"] is False
    assert comparison["profiles"]["full"]["errors"] == []
    assert comparison["profiles"]["conversation"]["errors"] == []
    assert comparison["profiles"]["conversation"]["selection_complete"] is True
    prepass_events = comparison["profiles"]["conversation"][
        "content_prepass_events"]
    assert len(prepass_events) == len(PROFILE_EVENT_IDS)
    assert all(event["seed_loading_performed"] is False
               for event in prepass_events)


def test_connected_profile_first_event_does_not_load_extra_seed_manifests():
    class LoadRecordingInner:
        def __init__(self, inner):
            self._inner = inner
            self.loaded_seed_ids = []

        def __getattr__(self, name):
            method = getattr(self._inner, name)
            if name != "load_seed_manifest":
                return method

            def load_seed_manifest(manifest, *args, **kwargs):
                self.loaded_seed_ids.append(manifest.get("id"))
                return method(manifest, *args, **kwargs)

            return load_seed_manifest

    from evaluation.conversational_manifold_phase0 import load_corpus

    content_keys = [
        "are", "how", "you", "north", "open", "the", "closed", "no",
        "it", "move", "there", "hello", "answer", "think", "behind",
        "describe", "object",
    ]
    agent = WorldAdapter(seeds=())
    selection = load_conversation_seed_profile(
        agent, content_keys=content_keys)
    recorder = LoadRecordingInner(agent.inner)
    agent.inner = recorder
    event = next(
        event for event in load_corpus()["events"]
        if event["id"] == PROFILE_EVENT_IDS[0]
    )

    agent.converse(
        event["signal"],
        speech_act=phase7._speech_act(event),
        context=phase7._runtime_context(event),
    )

    assert selection["selection_complete"] is True
    assert selection["loaded"] == len(
        selection["selection"]["selected_seed_ids"])
    assert recorder.loaded_seed_ids == []


def test_phase7_runtime_inputs_ignore_corpus_parse_and_evidence_labels():
    event = {
        "signal": "Open the hatch.", "event_mode": "turn_compatible",
        "interaction_relation": "standalone", "literal_form": "declarative",
        "evidence": ["explicit_failure"],
    }
    assert phase7._speech_act(event) == "request"
    assert phase7._runtime_context(event) == {
        "interaction_mode": "turn_compatible",
        "interaction_relation": "standalone",
    }


def test_graph_content_evidence_uses_only_resolved_referents_and_edges():
    agent = WorldAdapter(seeds=())
    inbound = agent.s.add_node("Message", {"text": "ignored surface"})
    first_mention = agent.s.add_node("Mention", {"text": "surface one"})
    second_mention = agent.s.add_node("Mention", {"text": "surface two"})
    sensor = agent.s.add_node("Concept", {"name": "sensor"})
    signal = agent.s.add_node("Concept", {"name": "signal"})
    sensor_theory = agent.s.add_node("Microtheory", {"name": "sensors"})
    unrelated = agent.s.add_node("Concept", {"name": "not_resolved"})
    agent.inner.add_edge_unchecked(inbound, "has_mention", first_mention)
    agent.inner.add_edge_unchecked(inbound, "has_mention", second_mention)
    agent.inner.add_edge_unchecked(first_mention, "refers_to", sensor)
    agent.inner.add_edge_unchecked(second_mention, "refers_to", signal)
    agent.inner.add_edge_unchecked(sensor_theory, "has_concept", sensor)
    agent.inner.add_edge_unchecked(sensor, "measures", signal)
    agent.inner.add_edge_unchecked(sensor, "related_to", unrelated)

    evidence = phase7._resolved_graph_content_evidence(
        agent, inbound, indexed_edge_types=("measures", "related_to"),
        content_node_provenance={sensor.value: {
            "seed_id": "sensor_seed", "type": "Concept", "name": "sensor",
        }})

    assert evidence == {
        "refs": [
            {"type": "Concept", "name": "sensor"},
            {"type": "Concept", "name": "signal"},
        ],
        "ref_contexts": [{
            "ref": {"type": "Concept", "name": "sensor"},
            "group_keys": ["microtheory:sensors"],
        }],
        "graph_provider_refs": [{
            "ref": {"type": "Concept", "name": "sensor"},
            "seed_id": "sensor_seed",
        }],
        "connections": [{
            "src": {"type": "Concept", "name": "sensor"},
            "edge": "measures",
            "tgt": {"type": "Concept", "name": "signal"},
        }],
    }


def test_graph_ref_plan_uses_cached_connection_index_fail_closed(monkeypatch):
    index = {
        "lexicon": {
            "group_keys": ["microtheory:lexicon"],
            "named_content_refs": [
                {"type": "Concept", "name": "signal"},
            ],
            "content_connections": [],
        },
        "sensor_domain": {
            "group_keys": ["microtheory:sensors"],
            "named_content_refs": [
                {"type": "Concept", "name": "sensor"},
                {"type": "Concept", "name": "signal"},
            ],
            "content_connections": [{
                "src": {"type": "Concept", "name": "sensor"},
                "edge": "measures",
                "tgt": {"type": "Concept", "name": "signal"},
            }],
            "depends_on": [],
            "content_dependencies": [],
            "missing_dependencies": [],
            "missing_content_references": [],
        },
    }
    index["lexicon"].update({
        "depends_on": [], "content_dependencies": [],
        "missing_dependencies": [], "missing_content_references": [],
    })
    monkeypatch.setattr(phase7, "_read_seed_index", lambda _seed_dir: (index, {}))

    plan = phase7._resolve_graph_ref_plan([{
        "id": "sensor_event",
        "refs": [
            {"type": "Concept", "name": "sensor"},
            {"type": "Concept", "name": "signal"},
        ],
        "connections": [],
        "ref_contexts": [
            {"ref": {"type": "Concept", "name": "sensor"},
             "group_keys": ["microtheory:sensors"]},
            {"ref": {"type": "Concept", "name": "signal"},
             "group_keys": ["microtheory:sensors"]},
        ],
    }])

    assert plan["surface_text_used"] is False
    assert plan["expected_labels_used"] is False
    assert plan["scoped_content_refs"] == {
        "sensor_domain": [
            {"type": "Concept", "name": "sensor"},
            {"type": "Concept", "name": "signal"},
        ],
    }
    assert plan["provider_scope_resolution_complete"] is True
    assert plan["seed_provider_coverage_complete"] is True
    assert plan["selection_closure_complete"] is True


def test_graph_ref_plan_loader_requires_full_coverage_metadata(tmp_path):
    path = tmp_path / "prepass.json"
    path.write_text(json.dumps({
        "seed_profile": "full",
        "event_count": 1,
        "errors": [],
        "graph_ref_plan": {
            "method": "live_graph_referents_and_direct_edges_v1",
            "scoped_content_refs": {"lexicon": []},
            "event_plans": [{"event_id": "e1"}],
        },
    }), encoding="utf-8")

    plan, event_ids = phase7._load_graph_ref_plan(str(path))
    assert plan["scoped_content_refs"] == {"lexicon": []}
    assert event_ids == ["e1"]

    path.write_text(json.dumps({
        "seed_profile": "conversation",
        "graph_ref_plan": {"method": "live_graph_referents_and_direct_edges_v1"},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="full-profile"):
        phase7._load_graph_ref_plan(str(path))

    path.write_text(json.dumps({
        "seed_profile": "full",
        "event_count": 1,
        "errors": ["failed"],
        "graph_ref_plan": {
            "method": "live_graph_referents_and_direct_edges_v1",
            "scoped_content_refs": {},
            "event_plans": [{"event_id": "e1"}],
        },
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="execution errors"):
        phase7._load_graph_ref_plan(str(path))


def test_profile_comparison_rejects_incomplete_seed_selection(monkeypatch):
    def fake_run(_events, *, seed_profile, **_kwargs):
        return {
            "observations": [{"id": "sample"}],
            "errors": [],
            "seed_profile": seed_profile,
            "selection_complete": (
                False if seed_profile == "conversation" else None),
        }

    monkeypatch.setattr(phase7, "_run", fake_run)
    comparison = phase7.compare_seed_profile_corpus(
        corpus={"events": [{"id": "sample"}]}, event_ids=["sample"])

    assert comparison["structural_parity"]["mismatch_count"] == 0
    assert comparison["structural_parity"][
        "conversation_seed_selection_complete"] is False
    assert comparison["structural_parity"]["equal"] is False


def test_replay_measurement_reuses_explicit_content_candidates(monkeypatch):
    calls = []

    def fake_run(events, *, seed_profile, content_keys, **_kwargs):
        keys = sorted(set(content_keys))
        calls.append((seed_profile, keys))
        return {
            "event_ids": [event["id"] for event in events],
            "event_count": len(events),
            "observations": [{"id": events[0]["id"]}],
            "errors": [],
            "seed_profile": seed_profile,
            "content_keys": keys,
            "scoped_content_refs": {},
            "content_slices": {},
            "selected_seed_ids": ["conversation"],
            "selection_unresolved": {},
            "graph_growth": {},
            "surface_text_used_as_semantics": False,
            "turn_boundary_required": False,
        }

    monkeypatch.setattr(phase7, "_run", fake_run)
    report = measure_production_envelope(
        corpus={"events": [{"id": "sample"}]},
        event_ids=["sample"],
        seed_profile="conversation",
        content_keys=["north", "open", "north"],
    )

    assert calls == [
        ("conversation", ["north", "open"]),
        ("conversation", ["north", "open"]),
    ]
    assert report["content_keys"] == ["north", "open"]
    assert report["replay_equal"] is True


def test_replay_measurement_reuses_typed_scoped_content_refs(monkeypatch):
    calls = []
    requested = {"learned_lexicon": [
        {"type": "Concept", "name": "north"},
        {"type": "Concept", "name": "open"},
    ]}

    def fake_run(events, *, seed_profile, content_keys,
                 scoped_content_refs, **_kwargs):
        calls.append((seed_profile, content_keys, scoped_content_refs))
        return {
            "event_ids": [event["id"] for event in events],
            "event_count": len(events),
            "observations": [{"id": events[0]["id"]}],
            "errors": [],
            "seed_profile": seed_profile,
            "content_keys": sorted(set(content_keys)),
            "scoped_content_refs": scoped_content_refs,
            "content_slices": {},
            "selected_seed_ids": ["learned_lexicon"],
            "selection_unresolved": {},
            "graph_growth": {},
            "surface_text_used_as_semantics": False,
            "turn_boundary_required": False,
        }

    monkeypatch.setattr(phase7, "_run", fake_run)
    report = measure_production_envelope(
        corpus={"events": [{"id": "sample"}]},
        event_ids=["sample"],
        seed_profile="conversation",
        scoped_content_refs=requested,
    )

    assert calls == [
        ("conversation", (), requested),
        ("conversation", (), requested),
    ]
    assert report["scoped_content_refs"] == requested
    assert report["replay_equal"] is True


def test_scoped_content_refs_select_exact_ambiguous_name_providers():
    from substrate.boot_all import _read_seed_index, _select_seed_ids
    from substrate.boot_core import CORE_SEEDS
    from substrate.boot_profiles import CONVERSATION_SEED_ANCHORS

    index, _ = _read_seed_index("seeds")
    refs = {
        "learned_lexicon": [
            {"type": "Concept", "name": "the"},
            {"type": "Concept", "name": "sky"},
            {"type": "Concept", "name": "blue"},
            {"type": "Concept", "name": "are"},
        ],
        "colour_meaning": [{"type": "Concept", "name": "blue"}],
    }

    selected, unresolved = _select_seed_ids(
        index,
        seed_ids=set(CORE_SEEDS) | set(CONVERSATION_SEED_ANCHORS),
        scoped_content_refs=refs,
    )

    assert "learned_lexicon" in selected
    assert "colour_meaning" in selected
    assert not any(unresolved.values())
