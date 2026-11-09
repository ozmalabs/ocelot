from __future__ import annotations

from pathlib import Path

import pytest

from worlds.bigville_ocelot_adapter import BigvilleOcelotResident


_BIGVILLE_ROOT = Path(__file__).resolve().parents[2] / "bigville"

pytestmark = pytest.mark.skipif(
    not (_BIGVILLE_ROOT / "bigville" / "seeds" / "bigville_actor_decision.json").is_file(),
    reason="standalone Bigville checkout is not present")


@pytest.fixture(autouse=True)
def _bigville_root(monkeypatch):
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))


def _resident():
    resident = BigvilleOcelotResident("CheckpointAda")
    resident.seed_character(
        identity={"occupation": "teacher"},
        personality={
            "emotional_core_enabled": 1.0,
            "talkativeness": 0.9,
            "social_dispositions": {"Ben": {"regard": 0.7, "trust": 0.6}},
        },
        memories=[{"memory_id": "m1", "content": "A private memory."}],
        held_frames=["core_emotions"],
    )
    return resident


def test_resident_checkpoint_round_trip_preserves_graph_and_python_state(tmp_path):
    resident = _resident()
    resident._emotion_epoch = 7.0
    resident._emotion_history.append({"epoch": 7.0, "emotion": "curiosity"})
    resident._observed_object_ids.add("notice:1")
    resident.heard_events["event:1"] = {"strength": 0.5}
    resident.told_events[("Ben", "event:1")] = 3
    resident.decide_speech("Ben", arousal=0.0)
    before_counts = (resident.s.node_count(), resident.s.edge_count())
    before_ids = {int(node.value) for node in resident.s.nodes()}

    checkpoint = tmp_path / "resident-checkpoint"
    resident.save(checkpoint)
    restored = BigvilleOcelotResident.load(checkpoint)

    assert (restored.s.node_count(), restored.s.edge_count()) == before_counts
    assert {int(node.value) for node in restored.s.nodes()} == before_ids
    assert restored.name == "CheckpointAda"
    assert restored.identity == resident.identity
    assert restored.personality == resident.personality
    assert restored.memories == resident.memories
    assert restored.held_frame_seeds == resident.held_frame_seeds
    assert restored._emotion_epoch == 7.0
    assert restored._emotion_history[-1]["emotion"] == "curiosity"
    assert restored._observed_object_ids == {"notice:1"}
    assert restored.heard_events == resident.heard_events
    assert restored.told_events == resident.told_events
    assert restored.speech_choices["Ben"]["kind"] == resident.speech_choices["Ben"]["kind"]
    assert restored._emotion_appraisal is not None
    assert restored._resident_can["mt"] is not None
    assert len(restored._speech_options) == len(resident._speech_options)


def test_restored_resident_continues_decision_and_speech(tmp_path):
    resident = _resident()
    resident._ensure_speech_graph()
    checkpoint = tmp_path / "resident-checkpoint"
    resident.save(checkpoint)
    left = BigvilleOcelotResident.load(checkpoint)
    right = BigvilleOcelotResident.load(checkpoint)

    options = [
        {"action": "rest", "score": 0.0},
        {"action": "move", "target": "north", "score": 4.0},
    ]
    left.replace_options(options)
    right.replace_options(options)
    assert left.decide() == right.decide()
    left_speech = left.decide_speech("Ben", arousal=0.0)
    right_speech = right.decide_speech("Ben", arousal=0.0)
    assert left_speech["kind"] == right_speech["kind"]
    assert left_speech.get("text") == right_speech.get("text")


def test_checkpoint_rejects_unsupported_python_state(tmp_path):
    resident = _resident()
    resident.heard_events["bad"] = object()
    with pytest.raises(TypeError, match="unsupported resident checkpoint value"):
        resident.save(tmp_path / "resident-checkpoint")
    assert not (tmp_path / "resident-checkpoint" / "manifest.json").exists()


def test_resident_python_state_codec_preserves_frozenset_type():
    from substrate_rs import NodeID

    value = frozenset({"heard", "seen"})
    encoded = BigvilleOcelotResident._checkpoint_encode(value)
    restored = BigvilleOcelotResident._checkpoint_decode(encoded, NodeID)
    assert restored == value
    assert type(restored) is frozenset


def test_checkpoint_rejects_corrupted_graph_file(tmp_path):
    resident = _resident()
    checkpoint = tmp_path / "resident-checkpoint"
    resident.save(checkpoint)
    manifest = __import__("json").loads((checkpoint / "manifest.json").read_text())
    graph = checkpoint / manifest["generation"] / "mind.json"
    graph.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        BigvilleOcelotResident.load(checkpoint)


def test_restored_document_cache_keeps_reads_idempotent(tmp_path):
    pytest.importorskip("nltk")
    resident = _resident()
    text = "Each player begins with 1500 dollars. A player who cannot pay is bankrupt."
    first = resident.ingest_document(text, name="rules")
    checkpoint = tmp_path / "resident-checkpoint"
    resident.save(checkpoint)
    restored = BigvilleOcelotResident.load(checkpoint)
    before = (restored.s.node_count(), restored.s.edge_count())

    assert restored.ingest_document(text, name="rules") == first
    assert (restored.s.node_count(), restored.s.edge_count()) == before
