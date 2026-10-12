"""Non-cognitive daemon status and read-only graph debugging surfaces."""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import jabberwock_daemon as daemon  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("instruction_understanding"), agent.agent)
    return agent


def test_daemon_conversation_boot_uses_connected_seed_prepass(monkeypatch, tmp_path):
    import substrate.boot_profiles as boot_profiles

    called = []

    def _profile(agent, **kwargs):
        called.append((agent, kwargs))
        return {
            "loaded": 7,
            "total": 7,
            "concepts": 3,
            "selection_complete": True,
            "failed": [],
            "runtime_modules_warmed": ["domains.comprehend_text"],
        }

    monkeypatch.setattr(
        boot_profiles, "load_conversation_seed_profile", _profile)
    adapter, booted_from = daemon.boot(tmp_path, "conversation")

    assert booted_from == "seeds"
    assert called == [(adapter, {
        "content_keys": (), "content_candidates": None,
        "scoped_content_refs": None,
        "content_prepass_manifest_digest": None,
        "incremental_content_loading": True,
    })]
    assert isinstance(adapter, WorldAdapter)
    assert daemon._checkpoint_seed_profile(adapter) == "conversation"


def test_conversation_content_manifest_is_canonical_and_validated(tmp_path):
    path = tmp_path / "prepass.json"
    path.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["valley", "can", "valley"],
        "scoped_content_refs": {
            "sensors": [{"type": "Concept", "name": "signal"},
                        {"type": "Concept", "name": "sensor"}],
        },
    }), encoding="utf-8")

    first = daemon._load_conversation_content_prepass(path)
    path.write_text(json.dumps({
        "scoped_content_refs": {
            "sensors": [{"name": "sensor", "type": "Concept"},
                        {"name": "signal", "type": "Concept"}],
        },
        "content_candidates": ["can", "valley"],
        "schema": "conversation_content_prepass.v1",
    }), encoding="utf-8")
    second = daemon._load_conversation_content_prepass(path)

    assert first["digest"] == second["digest"]
    assert first["sealed"] is False
    assert first["content_candidates"] == ["can", "valley"]
    assert first["scoped_content_refs"]["sensors"] == [
        {"type": "Concept", "name": "sensor"},
        {"type": "Concept", "name": "signal"},
    ]
    path.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["  "],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty strings"):
        daemon._load_conversation_content_prepass(path)
    path.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["valley"],
        "sealed": "yes",
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="sealed must be a boolean"):
        daemon._load_conversation_content_prepass(path)


def test_manifest_boot_preloads_closure_and_keeps_connected_fallback(
        monkeypatch, tmp_path):
    import substrate.boot_profiles as boot_profiles

    manifest = tmp_path / "prepass.json"
    manifest.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["sensor"],
    }), encoding="utf-8")
    received = {}

    def _profile(agent, **kwargs):
        received.update(kwargs)
        return {"loaded": 1, "total": 1, "concepts": 1,
                "selection_complete": True, "failed": []}

    monkeypatch.setattr(
        boot_profiles, "load_conversation_seed_profile", _profile)
    adapter, booted_from = daemon.boot(
        tmp_path / "fresh", "conversation", content_manifest=manifest)

    assert booted_from == "seeds"
    assert received["content_candidates"] == ["sensor"]
    assert received["incremental_content_loading"] is True
    assert received["content_prepass_manifest_digest"]


def test_manifest_boot_preloads_provider_and_lazily_loads_new_connected_content(
        tmp_path):
    manifest = tmp_path / "prepass.json"
    manifest.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["valley"],
    }), encoding="utf-8")

    adapter, booted_from = daemon.boot(
        tmp_path / "fresh", "conversation", content_manifest=manifest)
    profile_state = adapter._conversation_seed_profile_state

    assert booted_from == "seeds"
    assert profile_state["incremental_content_loading"] is True
    assert profile_state["content_prepass_manifest_digest"] == \
        daemon._load_conversation_content_prepass(manifest)["digest"]
    assert "valley" in profile_state["provider_seed_ids_by_key"]
    assert adapter._concept_by_name("valley") is not None

    from substrate.boot_profiles import load_conversation_content_candidates
    # The pre-pass installed the connected provider for `valley` before the
    # first turn; later content can still resolve and load its own provider.
    result = load_conversation_content_candidates(adapter, ["sensor"])
    assert result["status"] == "loaded"
    assert adapter._concept_by_name("sensor") is not None

    checkpoint = tmp_path / "hybrid-prepass.save"
    adapter.save(checkpoint)
    adapter = WorldAdapter.load(str(checkpoint))
    assert adapter._conversation_seed_profile_state[
        "incremental_content_loading"] is True
    assert adapter._concept_by_name("valley") is not None
    assert adapter._concept_by_name("sensor") is not None
    resumed = load_conversation_content_candidates(adapter, ["signal"])
    assert resumed["status"] == "loaded"
    assert adapter._concept_by_name("signal") is not None

    before = adapter.s.node_count()
    result = load_conversation_content_candidates(
        adapter, ["not-a-preloaded-content-key"])
    assert result["status"] == "unavailable"
    assert result["not_preloaded"] == ["not-a-preloaded-content-key"]
    assert adapter.s.node_count() == before


def test_explicitly_sealed_manifest_rejects_later_connected_content(tmp_path):
    manifest = tmp_path / "sealed-prepass.json"
    manifest.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["valley"],
        "sealed": True,
    }), encoding="utf-8")
    adapter, booted_from = daemon.boot(
        tmp_path / "fresh-sealed", "conversation", content_manifest=manifest)
    assert booted_from == "seeds"
    assert adapter._conversation_seed_profile_state[
        "incremental_content_loading"] is False
    before = adapter.s.node_count()
    from substrate.boot_profiles import load_conversation_content_candidates
    result = load_conversation_content_candidates(adapter, ["sensor"])
    assert result["status"] == "preload_only_unavailable"
    assert result["not_preloaded"] == ["sensor"]
    assert adapter.s.node_count() == before


def test_legacy_sealed_manifest_checkpoint_migrates_to_hybrid_default(tmp_path):
    manifest = tmp_path / "prepass.json"
    manifest.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["valley"],
    }), encoding="utf-8")
    prepass = daemon._load_conversation_content_prepass(manifest)
    adapter, _ = daemon.boot(
        tmp_path / "checkpoints", "conversation", content_manifest=manifest)
    # Reproduce the previous manifest digest/serialized profile state, whose
    # contract treated every manifest as sealed.
    adapter._conversation_seed_profile_state[
        "content_prepass_manifest_digest"] = \
        daemon._legacy_content_prepass_digest(prepass)
    adapter._conversation_seed_profile_state[
        "incremental_content_loading"] = False
    snapshot = tmp_path / "checkpoints" / "snapshot-conversation.save"
    adapter.save(snapshot)

    resumed, source = daemon.boot(
        tmp_path / "checkpoints", "conversation", content_manifest=manifest)
    state = resumed._conversation_seed_profile_state
    assert source == "checkpoint"
    assert state["incremental_content_loading"] is True
    assert state["content_prepass_manifest_digest"] == prepass["digest"]
    from substrate.boot_profiles import load_conversation_content_candidates
    result = load_conversation_content_candidates(resumed, ["sensor"])
    assert result["status"] == "loaded"
    assert resumed._concept_by_name("sensor") is not None


def test_manifest_boot_preloads_seed_scoped_typed_content(tmp_path):
    manifest = tmp_path / "typed-prepass.json"
    manifest.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "scoped_content_refs": {
            "learned_lexicon": [
                {"type": "Concept", "name": "sensor"},
            ],
        },
    }), encoding="utf-8")

    adapter, booted_from = daemon.boot(
        tmp_path / "fresh", "conversation", content_manifest=manifest)
    state = adapter._conversation_seed_profile_state

    assert booted_from == "seeds"
    assert state["incremental_content_loading"] is True
    assert adapter._concept_by_name("sensor") is not None
    assert adapter._concept_by_name("valley") is None
    assert state["loaded_typed_content_by_seed"]["learned_lexicon"] == {
        ("Concept", "sensor"),
    }

    checkpoint = tmp_path / "typed-prepass.save"
    adapter.save(checkpoint)
    adapter = WorldAdapter.load(str(checkpoint))
    state = adapter._conversation_seed_profile_state
    assert state["graph_provider_seed_ids_by_ref"]["Concept:sensor"] == [
        "learned_lexicon",
    ]

    cause = adapter.s.add_node(
        "Concept", {"name": "phase8 manifest causal source"})
    sensor = adapter._concept_by_name("sensor")
    adapter.inner.add_edge_unchecked(cause, "causal_influence", sensor)
    semantic = adapter.ingest_semantic_event(
        {
            "speech_act": "question",
            "relation_focus": "reason",
            "relation_scope": "event_specific",
            "relation_target_ref": {"type": "Concept", "name": "sensor"},
            "interaction_relation": "response",
        },
        provider="language_adapter:ja",
        interaction_mode="turn_compatible",
    )
    interpretation = adapter.s.node(semantic["interpretation_id"])["attrs"]
    assert semantic["content_prepass"]["status"] == "already_available"
    assert interpretation["relation_target_status"] == "graph_resolved"
    assert interpretation["relation_support"] == "supported"
    assert interpretation["cognitive_disposition"] == "answer"
    plans = list(adapter.inner.neighbours(
        semantic["interpretation_id"], "has_causal_relation_answer_plan"))
    assert len(plans) == 1
    assert semantic["discourse_event_id"] in adapter.inner.neighbours(
        plans[0], "for_event")


def test_daemon_refuses_checkpoint_with_different_content_manifest(
        monkeypatch, tmp_path):
    adapter = WorldAdapter(seeds=())
    daemon._stamp_checkpoint_seed_profile(adapter, "conversation")
    adapter._conversation_seed_profile_state = {
        "content_prepass_manifest_digest": "old-digest",
    }
    snapshot = tmp_path / "snapshot-conversation.save"
    snapshot.touch()
    monkeypatch.setattr(WorldAdapter, "load", lambda _path: adapter)
    manifest = tmp_path / "prepass.json"
    manifest.write_text(json.dumps({
        "schema": "conversation_content_prepass.v1",
        "content_candidates": ["sensor"],
    }), encoding="utf-8")

    with pytest.raises(RuntimeError, match="does not match the requested conversation content pre-pass"):
        daemon.boot(tmp_path, "conversation", content_manifest=manifest)

    assert snapshot.exists()
    assert adapter._conversation_seed_profile_state[
        "content_prepass_manifest_digest"] == "old-digest"


def test_daemon_refuses_checkpoint_from_different_seed_profile(
        monkeypatch, tmp_path):
    adapter = WorldAdapter(seeds=())
    daemon._stamp_checkpoint_seed_profile(adapter, "full")
    snapshot = tmp_path / "snapshot-full.save"
    snapshot.touch()
    monkeypatch.setattr(WorldAdapter, "load", lambda _path: adapter)

    with pytest.raises(RuntimeError, match="newer checkpoint does not match requested seed profile"):
        daemon.boot(tmp_path, "conversation")

    # The existing graph/checkpoint is never relabelled or overwritten.
    assert daemon._checkpoint_seed_profile(adapter) == "full"
    assert snapshot.exists()


def test_strict_daemon_profile_rejects_ambiguous_legacy_checkpoint(
        monkeypatch, tmp_path):
    adapter = WorldAdapter(seeds=())
    snapshot = tmp_path / "snapshot-legacy.save"
    snapshot.touch()
    monkeypatch.setattr(WorldAdapter, "load", lambda _path: adapter)

    with pytest.raises(RuntimeError, match="legacy checkpoints lack seed-profile identity"):
        daemon.boot(tmp_path, "conversation", strict_profile=True)

    assert daemon._checkpoint_seed_profile(adapter) is None
    assert snapshot.exists()


def test_checkpoint_roundtrip_preserves_daemon_seed_profile(tmp_path):
    adapter = WorldAdapter(seeds=())
    daemon._stamp_checkpoint_seed_profile(adapter, "conversation")
    adapter._conversation_seed_profile_state = {
        "content_prepass_manifest_digest": "canonical-prepass-digest",
    }

    snapshot = daemon.checkpoint(adapter, tmp_path, keep=2)
    restored = WorldAdapter.load(str(snapshot))

    assert daemon._checkpoint_seed_profile(restored) == "conversation"
    assert restored._conversation_seed_profile_state[
        "content_prepass_manifest_digest"] == "canonical-prepass-digest"


def test_daemon_resume_refreshes_memory_episode_provenance_rule():
    adapter = WorldAdapter(seeds=("memory_core",))
    manifest = manifest_for("memory_core")
    current = next(
        rule for rule in manifest["rules"]
        if rule["name"] == "rule_episode_from_message")
    stale = deepcopy(current)
    stale["effects"] = [
        effect for effect in stale["effects"]
        if not (effect[0] == "add_edge" and
                effect[1:4] == ["ep", "recorded_from_message", "m"])
    ]
    live = list(adapter.inner.export_rules())
    old_index = next(
        index for index, rule in enumerate(live)
        if rule.get("active") and
        rule.get("name") == "rule_episode_from_message")
    adapter.inner.remove_rule(old_index)
    adapter.inner.load_seed_manifest(
        {"id": "memory_core", "rules": [stale]}, adapter.agent)

    assert daemon._reconcile_seed_rules(adapter) >= 1
    reconciled = [
        rule for rule in adapter.inner.export_rules()
        if rule.get("active") and
        rule.get("name") == "rule_episode_from_message"]
    assert len(reconciled) == 1
    assert daemon._canon_rule_body(reconciled[0]) == \
        daemon._canon_rule_body(current)
    assert daemon._reconcile_seed_rules(adapter) == 0


def test_daemon_conversation_boot_rejects_incomplete_seed_closure(
        monkeypatch, tmp_path):
    import substrate.boot_profiles as boot_profiles

    monkeypatch.setattr(
        boot_profiles, "load_conversation_seed_profile",
        lambda _agent, **_kwargs: {
            "selection_complete": False, "failed": []},
    )
    with pytest.raises(RuntimeError, match="connected conversation seed profile failed"):
        daemon.boot(tmp_path, "conversation")


def test_fresh_daemon_default_uses_validated_conversation_profile(
        monkeypatch, tmp_path):
    calls = []
    agent = WorldAdapter(seeds=())

    def _boot(_checkpoint_dir, seeds, *, strict_profile=False,
              content_manifest=None):
        calls.append(seeds)
        assert content_manifest is None
        return agent, "seeds"

    monkeypatch.setattr(daemon, "boot", _boot)
    monkeypatch.setattr(daemon, "init_chat_history", lambda *_args: None)
    monkeypatch.setattr(daemon, "_nudge_promoted_experiments", lambda _agent: 0)
    monkeypatch.setattr(daemon, "checkpoint", lambda *_args: None)
    monkeypatch.setattr(sys, "argv", [
        "jabberwock_daemon", "--once", "--no-http", "--socket", "",
        "--no-attach-libraries", "--ckpt-dir", str(tmp_path / "checkpoints"),
        "--runs-dir", str(tmp_path / "runs"),
    ])

    assert daemon.main() == 0
    assert calls == ["conversation"]
    assert agent.shadow_read is False


def test_conversation_checkpoint_resume_reconciles_only_connected_seed_scope(
        tmp_path):
    agent, booted_from = daemon.boot(
        tmp_path, "conversation", strict_profile=True)
    assert booted_from == "seeds"
    profile = agent._conversation_seed_profile_state
    loaded_seed_ids = set(profile["loaded_seed_ids"])
    assert loaded_seed_ids
    assert "f16_flight_path_control" not in loaded_seed_ids

    daemon.checkpoint(agent, tmp_path, keep=2)
    resumed, resumed_from = daemon.boot(
        tmp_path, "conversation", strict_profile=True)

    assert resumed_from == "checkpoint"
    assert resumed._conversation_seed_profile_state["loaded_seed_ids"] == \
        loaded_seed_ids
    active_rule_names = {
        str(rule.get("name")) for rule in resumed.inner.export_rules()
        if rule.get("active")
    }
    assert "f16_sample_axis_margins" not in active_rule_names
    assert any(
        resumed.s.node(node)["attrs"].get("seed_id")
        == "conversation_self_reply"
        for node in resumed.s.nodes("SeedSummary"))


def test_runtime_status_never_reads_graph_or_invokes_cognition():
    state = daemon.DaemonState(_agent(), "test")

    class _NoAccess:
        def __getattribute__(self, name):
            raise AssertionError(f"runtime status touched adapter.{name}")

    state.adapter = _NoAccess()
    status = daemon._runtime_status_dict(state)

    assert status["ok"] is True
    assert status["requires_cognition"] is False
    assert status["ticks"] == 0
    assert status["node_count_snapshot"] > 0


def test_daemon_turn_releases_native_standalone_assertion_receipt():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        "The sky is blue.", speech_act="statement",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    agent.tick()
    agent.comprehend()
    reply = agent.release_graph_selected_response(inbound)

    assert reply == "I heard you."
    assert agent.graph_turn_reply(inbound) == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_standalone_assertion_graph"
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"


def test_daemon_turn_releases_native_reflective_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test-reflective-answer")
    inbound = agent.ingest_turn(
        "How are you organised?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"},
    )

    agent.tick()
    agent.comprehend()
    reply = agent.release_graph_selected_response(inbound)

    assert reply and "organised into" in reply
    assert agent.graph_turn_reply(inbound) == reply
    assert agent._native_reflective_answer_selected(inbound)
    receipt = next(node for node in agent.s.nodes("ProductionGateReceipt")
                   if agent.s.node(node)["attrs"].get("turn_message_id")
                   == int(inbound.value))
    assert agent.s.node(receipt)["attrs"]["status"] == "released"


@pytest.mark.parametrize(("language", "question", "punctuation"), [
    ("es", "¿Qué regla se ejecutó por última vez?", "."),
    ("ja", "最後にどのルールが発火しましたか？", "。"),
])
def test_daemon_turn_releases_multilingual_rule_history_answer(
        language, question, punctuation):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse("Good morning.", speech_act="greeting")
    prior = dict(agent.s.node(
        agent.s.nodes("RuleFiringHistory")[0])["attrs"])
    daemon.DaemonState(agent, f"test-rule-history-{language}")
    inbound = agent.ingest_turn(
        question, speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"},
    )

    agent.tick()
    agent.comprehend()
    agent.settle_post_comprehension_authority([int(inbound.value)])
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation["cognitive_disposition"] == "answer"
    assert interpretation["arbitration_basis"] \
        == "grounded_rule_firing_history"
    assert interpretation["selected_rule_name"] == prior["last_rule_name"]

    reply = agent.release_graph_selected_response(inbound)
    assert reply == prior["last_rule_name"] + punctuation
    assert agent.graph_turn_reply(inbound) == reply
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert receipts
    assert all(item["status"] == "released" for item in receipts)
    assert all(item["parse_back_mode"] == "grounded_comprehension"
               for item in receipts)
    assert all(item["semantic_event"] == "answer_fragment"
               for item in receipts)
    assert all(item["surface"] == reply for item in receipts)
    evidence = agent.inner.neighbours(
        interpretation_id, "has_rule_firing_answer_evidence")
    assert len(evidence) == 1
    evidence_attrs = agent.s.node(evidence[0])["attrs"]
    assert evidence_attrs["source_message_id"] \
        == prior["last_inbound_message_id"]


def test_daemon_turn_releases_typed_response_acknowledgement_receipt():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test-typed-acknowledgement")
    inbound = agent.ingest_turn(
        "Yes, that is the one.", speech_act="acknowledgment",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    agent.tick()
    agent.comprehend()
    reply = agent.release_graph_selected_response(inbound)

    assert isinstance(reply, str) and reply.strip()
    assert reply.strip().lower().rstrip(".!?") != \
        "error: no communicative response could be generated"
    assert agent.graph_turn_reply(inbound) == reply
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation["evidence_force"] == "acknowledgement"
    assert interpretation["cognitive_disposition"] == "defer"
    assert interpretation["arbitration_basis"] == "typed_acknowledgement"
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["surface"] == reply
    assert receipts[0]["parse_back_mode"] == \
        "conversation_response_acknowledgement_graph"
    assert receipts[0]["semantic_intent"] == \
        "acknowledge_receipt_without_endorsement"


def test_daemon_turn_releases_same_event_grounded_topic_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent._persist_held_answer("sensor status", "nominal")
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        "What is the sensor status?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    agent.tick()
    agent.comprehend()
    reply = agent.release_graph_selected_response(inbound)

    assert reply == "nominal"
    assert agent.graph_turn_reply(inbound) == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_information_graph"
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"


def test_daemon_turn_releases_native_selected_action_repair():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        "Close it.", speech_act="instruction",
        context={"interaction_mode": "turn_compatible"},
    )

    agent.tick()
    agent.comprehend()
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == "typed_unresolved_action_dependency"

    reply = agent.release_graph_selected_response(inbound)

    assert reply == "I don't know 'it' — what does it mean?"
    assert agent.graph_turn_reply(inbound) == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_action_graph"
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["turn_message_id"] == int(inbound.value)


@pytest.mark.parametrize(
    ("text", "interaction_mode", "interaction_relation", "expected_action"),
    [
        ("Run the script.", "turn_compatible", None, "run script"),
        ("Check the pressure.", "non_turn", "standalone",
         "check pressure"),
    ],
)
def test_daemon_turn_releases_graph_selected_world_action_floor(
        text, interaction_mode, interaction_relation, expected_action):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        text, speech_act=agent.classify_speech_act(text),
        context={"interaction_mode": interaction_mode,
                 "interaction_relation": interaction_relation},
    )

    agent.tick()
    agent.comprehend()
    reply = agent.release_graph_selected_response(inbound)

    assert reply and expected_action in reply.lower()
    assert "no world or faculty" in reply.lower()
    assert agent.graph_turn_reply(inbound) == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_instruction_graph"
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["turn_message_id"] == int(inbound.value)
    assert receipts[0]["surface"] == reply


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Fix your grammar.", ("self-concern", "review")),
        ("Improve your florbnax.", ("which part", "say more")),
    ],
)
def test_daemon_turn_releases_graph_selected_self_improvement_reply(
        text, expected):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        text, speech_act="instruction",
        context={"interaction_mode": "turn_compatible"},
    )

    agent.tick()
    agent.comprehend()
    reply = agent.release_graph_selected_response(inbound)

    assert reply and any(phrase in reply.lower() for phrase in expected)
    assert agent.graph_turn_reply(inbound) == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_instruction_graph"
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["turn_message_id"] == int(inbound.value)
    assert receipts[0]["surface"] == reply


def test_daemon_terminalizes_same_event_exhausted_topic_search():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        "What is a blorf?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )
    agent.tick()
    agent.comprehend()

    goal = next(
        node for node in agent.inner.neighbours(agent.agent, "has_goal")
        if agent.s.node(node)["attrs"].get("kind") == "answer_topic"
        and inbound in agent.inner.neighbours(node, "comprehends")
    )
    request = next(iter(agent.inner.neighbours(goal, "search_request")))
    agent.inner.set_attr(request, "status", "failed")
    agent.inner.set_attr(request, "epistemic_status", "unknown")
    agent.inner.set_attr(request, "error", "no candidates")
    # Model the terminal outcome written by the existing topic-reply rule
    # after it observes this exact SearchRequest fail without candidates.
    agent.inner.set_attr(goal, "outcome", "unresolved")
    agent.add_outbound(
        "I don't hold anything about blorf yet.", kind="statement",
        source="agent", inbound=inbound,
    )

    assert agent.s.node(goal)["attrs"].get("outcome") == "unresolved"
    assert agent.release_graph_selected_response(inbound) is None
    assert agent.graph_turn_reply_outcome(inbound) == "explicit_error"
    assert agent.graph_turn_reply(inbound) == \
        "ERROR: no communicative response could be generated."
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_unresolved_information_graph"
    ]
    assert receipts
    assert all(item["status"] == "withheld" for item in receipts)


def test_daemon_releases_graph_selected_standalone_offer_acceptance():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    daemon.DaemonState(agent, "test")
    inbound = agent.ingest_turn(
        "I can check the gate.", speech_act="statement",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    agent.tick()
    agent.comprehend()
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    interpreted = agent.s.node(interpretation)["attrs"]
    assert interpreted["arbitration_basis"] == "typed_ability_action_offer"
    assert interpreted["cognitive_disposition"] == "answer"
    assert agent.graph_turn_reply_outcome(inbound) == "expected"
    reply = agent.release_graph_selected_response(inbound)

    assert reply == "that would be helpful"
    assert agent.graph_turn_reply(inbound) == reply
    assert agent.graph_turn_reply_outcome(inbound) == "reply_ready"
    social_receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
        and agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_social_graph"
    ]
    assert len(social_receipts) == 1
    assert social_receipts[0]["status"] == "released"
    assert social_receipts[0]["semantic_intent"] == "coordinate_socially"
    assert not [
        node for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
        and agent.s.node(node)["attrs"].get("status") == "released"
        and agent.s.node(node)["attrs"].get("semantic_intent")
        == "execute_action"
    ]


def test_graph_helpers_are_paged_filtered_json_safe_and_read_only():
    agent = _agent()
    blob = agent.s.add_node("DebugBlob", {"payload": b"\x00\xff"})
    before = agent.inner.graph_to_dict()

    summary = daemon.debug_graph_summary(agent)
    nodes = daemon.debug_graph_nodes(agent, {"type": ["DebugBlob"], "limit": ["1"]})
    detail = daemon.debug_graph_node(agent, str(blob.value))
    rules = daemon.debug_graph_rules(agent, {"name": ["iu_confirm"], "limit": ["10"]})

    assert summary["read_only"] and summary["node_types"]["DebugBlob"] == 1
    payload = nodes["nodes"][0]["attrs"]["payload"]
    assert nodes["total"] == 1 and payload["kind"] == "bytes" and payload["payload"] == "00ff"
    assert detail is not None and detail["node"]["id"] == blob.value
    assert rules["total"] == 1
    json.dumps({"summary": summary, "nodes": nodes, "detail": detail, "rules": rules})
    assert agent.inner.graph_to_dict() == before


def test_http_runtime_and_graph_debug_routes_do_not_tick_agent():
    agent = _agent()
    target = agent.s.add_node("DebugTarget", {"name": "visible"})
    pending_turn = agent.receive_utterance("pending turn")
    no_reply_turn = agent.s.add_node("Message", {"from": "interlocutor"})
    no_reply_intent = agent.s.add_node("Intent", {"name": "statement_update"})
    agent.inner.add_edge_unchecked(no_reply_turn, "has_intent", no_reply_intent)
    error_turn = agent.s.add_node("Message", {"from": "interlocutor"})
    error_intent = agent.s.add_node("Intent", {"name": "answer_request"})
    answer_act = agent.s.add_node("Concept", {"name": "answer"})
    agent.inner.add_edge_unchecked(error_turn, "has_intent", error_intent)
    agent.inner.add_edge_unchecked(error_intent, "expects_response", answer_act)
    error_reply = agent.add_outbound(
        "ERROR: no communicative response could be generated.",
        kind="answer", source="agent", inbound=error_turn,
    )
    agent.inner.set_attr(error_reply, "terminal_outcome", "explicit_error")
    state = daemon.DaemonState(agent, "test")
    state.pending_turns[int(no_reply_turn.value)] = "A completed statement."
    state.pending_turns[int(error_turn.value)] = "An unresolved question."
    server = daemon.JbwHTTPServer(("127.0.0.1", 0), daemon.Handler, state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    response_headers = {}

    def get(path):
        with urllib.request.urlopen(base + path, timeout=5) as response:
            response_headers[path] = dict(response.headers.items())
            return json.load(response)

    try:
        # The request is served by another HTTP thread while this test owns the
        # cognition lock: acquiring AGENT_LOCK in the route would time out.
        with daemon.AGENT_LOCK:
            status = get("/api/runtime/status")
        summary = get("/api/debug/graph")
        nodes = get("/api/debug/graph/nodes?type=DebugTarget&limit=1")
        detail = get(f"/api/debug/graph/nodes/{target.value}")
        edges = get(f"/api/debug/graph/edges?source={target.value}&limit=5")
        rules = get("/api/debug/graph/rules?name=iu_confirm&limit=5")
        pending = get(f"/api/chat/turns/{pending_turn.value}")
        no_reply = get(f"/api/chat/turns/{no_reply_turn.value}")
        explicit_error = get(f"/api/chat/turns/{error_turn.value}")
        reply = agent.s.add_node("Message", {"from": "agent", "text": "settled"})
        agent.inner.add_edge_unchecked(reply, "responds_to", pending_turn)
        completed = get(f"/api/chat/turns/{pending_turn.value}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert status["requires_cognition"] is False and status["ticks"] == 0
    assert response_headers["/api/runtime/status"]["Access-Control-Allow-Origin"] == "*"
    assert "Access-Control-Allow-Origin" not in response_headers["/api/debug/graph"]
    assert summary["read_only"] is True
    assert nodes["total"] == 1 and nodes["nodes"][0]["id"] == target.value
    assert detail["node"]["attrs"]["name"] == "visible"
    assert edges["read_only"] is True
    assert rules["total"] == 1
    assert pending == {"ok": True, "turn_id": pending_turn.value,
                       "status": "pending", "reply_expected": False,
                       "transport_pending": False}
    assert no_reply == {
        "ok": True, "turn_id": no_reply_turn.value,
        "status": "no_response_expected", "reply_expected": False,
        "transport_pending": True,
    }
    assert explicit_error == {
        "ok": True, "turn_id": error_turn.value, "status": "error",
        "reply_expected": True,
        "reply": "ERROR: no communicative response could be generated.",
        "transport_pending": True,
    }
    assert completed == {"ok": True, "turn_id": pending_turn.value,
                         "status": "completed", "reply_expected": False,
                         "reply": "settled",
                         "transport_pending": False}
    assert state.ticks == 0


def test_web_interface_renders_the_cognition_free_runtime_status():
    html = (ROOT / "web" / "index.html").read_text()
    app = (ROOT / "web" / "app.js").read_text()

    assert 'id="runtime-status-bar"' in html
    for field in ("runtime-state", "runtime-tick", "runtime-work", "runtime-nodes",
                  "runtime-actions", "runtime-last-action", "runtime-error"):
        assert f'id="{field}"' in html
    assert 'fetch("/api/runtime/status"' in app
    assert "function updateRuntimeStatus" in app
    assert "RUNTIME_STATUS_POLL_MS" in app
