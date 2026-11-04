"""P7.02 graph tests for observed, source-bound episode signatures."""
import json

import pytest
from substrate_rs import _native

from scripts.gen_cognition_signature_seed import build_seed as build_signature_seed
from scripts.gen_experience_signature_seed import OUT, build_seed


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    sig = s.load_seed_manifest(build_signature_seed(), ag)
    assert sig.get("rules_skipped") == [], sig
    exp = s.load_seed_manifest(build_seed(), ag)
    assert exp.get("rules_skipped") == [], exp
    s.set_attr(s.nodes("CognitionSignaturePolicy")[0], "enabled", 1.0)
    s.set_attr(s.nodes("ExperienceSignaturePolicy")[0],
               "enabled", 1.0 if enabled else 0.0)
    return s, ag


def _tick(s):
    for _ in range(20):
        if not s.run_rules(1000):
            return
    raise AssertionError("experience signature rules did not reach a fixpoint")


def _episode(s, ag, *, owner="owner-a", episode="episode-1", event_id="event-1",
             source_epoch=3, model_epoch=2, frame_epoch=5, frame_id="frame-1",
             modality="tool_contact", features=None, receipt_overrides=None):
    episode_node = s.add_node("ExperienceEpisode", {
        "owner_id": owner, "episode_id": episode, "status": "observed"})
    event = s.add_node("ExperienceEvent", {
        "owner_id": owner, "episode_id": episode, "event_id": event_id,
        "action_id": "action-1", "status": "observed", "frame_id": frame_id,
        "modality": modality,
        "source_epoch": source_epoch, "model_epoch": model_epoch,
        "frame_epoch": frame_epoch,
        "features": features if features is not None else [
            ["contact", "finite_number", 0.7, False, 0],
            ["duration", "finite_number", 2.0, False, 0]],
        "live_overlay": [["current-affect", "finite_number", 0.2, False, 0]],
    })
    attrs = {"receipt_id": "receipt-1", "outcome_id": "outcome-1",
             "owner_id": owner, "episode_id": episode, "event_id": event_id,
             "action_id": "action-1", "source_epoch": source_epoch,
             "model_epoch": model_epoch, "frame_epoch": frame_epoch,
             "status": "observed", "evidence_status": "observed"}
    attrs.update(receipt_overrides or {})
    receipt = s.add_node("ExperienceOutcomeReceipt", attrs)
    s.add_edge(ag, "has_experience_episode", episode_node)
    s.add_edge(episode_node, "has_experience_event", event)
    s.add_edge(event, "has_experience_outcome_receipt", receipt)
    return episode_node, event, receipt


def test_episode_produces_signature():
    assert json.loads(OUT.read_text()) == build_seed()
    s, ag = _boot()
    _, event, receipt = _episode(s, ag)
    _tick(s)
    sources = [n for n in s.neighbours(event, "has_signature_source")
               if s.node(n)["attrs"].get("source_kind") == "experience_event"]
    assert len(sources) == 1
    attrs = s.node(sources[0])["attrs"]
    assert attrs["evidence_status"] == "observed"
    assert attrs["owner_id"] == "owner-a"
    assert attrs["source_epoch"] == 3
    assert attrs["model_epoch"] == 2
    assert attrs["frame_epoch"] == 5
    assert attrs["event_id"] == "event-1"
    assert attrs["receipt_id"] == s.node(receipt)["attrs"]["receipt_id"]
    assert attrs["dimension_ids"] == ("experience:event_features",)
    assert attrs["coordinates"][0][1] == "sequence_ref"
    descriptors = [n for n in s.neighbours(ag, "has_cognition_signature")
                   if s.node(n)["attrs"].get("source_kind") == "experience_event"]
    assert len(descriptors) == 1
    assert s.neighbours(sources[0], "projects_episode_event") == [event]


def test_wrong_episode_receipt_rejected():
    s, _ag = _boot()
    _, event, _ = _episode(s, _ag, receipt_overrides={"episode_id": "episode-other"})
    _tick(s)
    assert not s.neighbours(event, "has_signature_source")


def test_live_overlay_not_standing_commitment():
    s, _ag = _boot()
    _, event, _ = _episode(s, _ag)
    _tick(s)
    source = next(n for n in s.neighbours(event, "has_signature_source")
                  if s.node(n)["attrs"].get("source_kind") == "experience_event")
    attrs = s.node(source)["attrs"]
    assert attrs["standing_coordinates"] == ()
    assert attrs["live_overlay"] == [["current-affect", "finite_number", 0.2, False, 0]]


def test_no_experience_no_signature():
    s, ag = _boot()
    _tick(s)
    assert not s.nodes("CognitionSignatureSource")
    assert not s.nodes("CognitionSignatureDescriptor")


@pytest.mark.parametrize("epoch_field", ["source_epoch", "model_epoch", "frame_epoch"])
def test_stale_receipt_epochs_rejected(epoch_field):
    s, ag = _boot()
    _, event, _ = _episode(s, ag, receipt_overrides={epoch_field: -1})
    _tick(s)
    assert not s.neighbours(event, "has_signature_source")


def test_unsupported_modality_rejected():
    s, ag = _boot()
    _, event, _ = _episode(s, ag, modality="text_label")
    _tick(s)
    assert not s.neighbours(event, "has_signature_source")


def test_missing_feature_coordinate_is_preserved_not_imputed():
    s, ag = _boot()
    _, event, _ = _episode(s, ag, features=[
        ["contact", "finite_number", None, True, 0]])
    _tick(s)
    source = next(n for n in s.neighbours(event, "has_signature_source")
                  if s.node(n)["attrs"].get("source_kind") == "experience_event")
    feature_ref = s.node(source)["attrs"]["coordinates"][0][2]
    assert feature_ref == [["contact", "finite_number", None, True, 0]]


def test_other_owner_receipt_rejected():
    s, ag = _boot()
    _, event, _ = _episode(s, ag, receipt_overrides={"owner_id": "owner-b"})
    _tick(s)
    assert not s.neighbours(event, "has_signature_source")


def test_target_labels_are_not_projected():
    s, ag = _boot()
    _, event, _ = _episode(s, ag)
    s.set_attr(event, "target_dimension", "safety")
    s.set_attr(event, "expected_class", "positive")
    _tick(s)
    source = next(n for n in s.neighbours(event, "has_signature_source")
                  if s.node(n)["attrs"].get("source_kind") == "experience_event")
    attrs = s.node(source)["attrs"]
    assert "target_dimension" not in attrs and "expected_class" not in attrs


def test_signature_policy_disabled_by_default():
    s, ag = _boot(enabled=False)
    _episode(s, ag)
    _tick(s)
    assert not s.nodes("CognitionSignatureSource")
