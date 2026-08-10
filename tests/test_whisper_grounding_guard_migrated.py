"""Regression and graph-native gates for corrected Whisper grounding."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import whisper_teacher_adapter as teacher
from domains.whisper_grounding_guard import (
    GraphWhisperGroundingGuard,
    PrototypeBank,
    audit_no_python_inference_decision,
    normalize_digit_transcript,
)
from substrate.boot_core import boot_core


ROOT = Path(__file__).resolve().parent.parent


def _guard():
    support = {
        "zero": [
            np.asarray([1.0, 0.0, 0.0]),
            np.asarray([0.98, 0.02, 0.0]),
        ],
        "one": [
            np.asarray([0.0, 1.0, 0.0]),
            np.asarray([0.02, 0.98, 0.0]),
        ],
    }
    bank = PrototypeBank.from_support(support, fold="unit-held-speaker")
    substrate, agent = boot_core(seeds=())
    return GraphWhisperGroundingGuard(substrate, agent, bank)


def test_graph_accepts_matching_admitted_candidate():
    guard = _guard()
    result = guard.infer_embedding([1.0, 0.0, 0.0], "0.")
    assert result["status"] == "decided"
    assert result["winner_label"] == "zero"
    assert result["output_label"] == "zero"
    assert result["action"] == "accept"
    assert result["winner_distance"] <= result["winner_radius"]
    assert result["decision_provenance"] == "graph_argmin_support_radius"
    prototypes = guard.s.nodes("WhisperGroundingPrototype")
    assert len(prototypes) == 2
    assert {
        guard.s.node(prototype)["attrs"]["provenance_kind"]
        for prototype in prototypes
    } == {"learned_from_support_fold"}


def test_graph_corrects_nonempty_decoder_disagreement():
    result = _guard().infer_embedding([1.0, 0.0, 0.0], "one")
    assert result["winner_label"] == "zero"
    assert result["output_label"] == "zero"
    assert result["action"] == "correct"


def test_graph_does_not_invent_output_for_decoder_silence():
    result = _guard().infer_embedding([1.0, 0.0, 0.0], "")
    assert result["output_label"] == ""
    assert result["action"] == "abstain"
    assert result["reason"] == "empty_decoder_proposal"


def test_graph_refuses_candidate_outside_its_support_radius():
    result = _guard().infer_embedding([1.0, 1.0, 0.0], "one")
    assert result["output_label"] == ""
    assert result["action"] == "abstain"
    assert result["reason"] == "outside_training_support"
    assert result["winner_distance"] > result["winner_radius"]


def test_normalizer_is_exact_not_fuzzy():
    assert normalize_digit_transcript(" Five.") == "five"
    assert normalize_digit_transcript("5!") == "five"
    assert normalize_digit_transcript("fife") == "fife"
    assert normalize_digit_transcript("five five") == "five five"


def test_embedding_cache_is_content_addressed_and_bounded(monkeypatch):
    class FakeModel:
        @staticmethod
        def feature_extractor(audio):
            return np.asarray(audio, dtype=np.float32)

        @staticmethod
        def encode(features):
            vector = np.asarray(features, dtype=np.float32)
            return vector.reshape(1, 1, -1)

    monkeypatch.setattr(teacher, "_MODEL", FakeModel())
    monkeypatch.setattr(teacher, "_CACHE_MAX", 2)
    teacher.clear_embedding_cache()

    first = teacher.embed(np.asarray([1.0, 0.0]))
    same_content = teacher.embed(np.asarray([1.0, 0.0]))
    different = teacher.embed(np.asarray([0.0, 1.0]))
    teacher.embed(np.asarray([1.0, 1.0]))

    assert same_content is first
    assert not np.array_equal(first, different)
    assert len(teacher._CACHE) == 2


def test_invalid_historical_forced_score_fails_loudly():
    with pytest.raises(
        teacher.InvalidForcedDecodeScoring,
        match="unscored initial tokens",
    ):
        teacher.forced_decode_topk(np.zeros(1600), ["zero", "one"])
    with pytest.raises(teacher.InvalidForcedDecodeScoring):
        teacher.ForcedDecodeTeacher(["zero", "one"])


def test_decision_is_graph_data_not_python_ranking():
    assert audit_no_python_inference_decision() == []
    manifest = json.loads(
        (ROOT / "seeds" / "whisper_grounding_guard.json").read_text()
    )
    rules = json.dumps(manifest["rules"])
    assert '"type": "Argmin"' in rules
    assert '"type": "Lte"' in rules
    assert {rule["name"] for rule in manifest["rules"]} == {
        "whisper_grounding_accept",
        "whisper_grounding_correct",
        "whisper_grounding_abstain_empty",
        "whisper_grounding_abstain_outside_support",
    }
