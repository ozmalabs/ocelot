"""Audio perception, migrated — the agent HEARS on the seed-booted WorldAdapter
(no CuriousAgent). The cochlea / gammatone / STFT / utterance-recognition are all
Rust primitives (substrate_rs.audio + .speech), already graph-resident; this
covers the agent-side faculty CuriousAgent's AudioWorld used to own: open a
graph-resident AcousticLexicon, decode a file, and mint a Message{source: audio}
per detected utterance with its AcousticSign attached via `has_mention`.

Mechanical I/O over the Rust speech pipeline. The downstream intent-firing
(intent_from_claim + speech-bridge denotes->refers_to) is the conversation/intent
RULE layer, exercised via tick()/run_rules() once those rules fire on the booted
agent — separate from this perception faculty and kept in the AudioWorld bench.
"""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

av = pytest.importorskip("av")
srs = pytest.importorskip("substrate_rs")
pytest.importorskip("substrate_rs.audio")
pytest.importorskip("substrate_rs.speech")

from substrate.world_adapter import WorldAdapter


# --- audio synthesis helpers (same shape as test_audio_world) -----------

def _encode(path, samples, *, sample_rate=22050, chunk=1024):
    container = av.open(path, mode="w")
    stream = container.add_stream("mp3", rate=sample_rate)
    stream.codec_context.layout = "mono"
    s = samples.astype(np.float32).reshape(1, -1)
    n = s.shape[1]
    for start in range(0, n, chunk):
        sub = s[:, start:start + chunk]
        if sub.shape[1] < chunk:
            sub = np.pad(sub, ((0, 0), (0, chunk - sub.shape[1])))
        frame = av.AudioFrame.from_ndarray(sub, format="flt", layout="mono")
        frame.sample_rate = sample_rate
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()


def _utterance(hz, duration_s=0.4, sample_rate=22050):
    n = int(sample_rate * duration_s)
    t = np.arange(n) / sample_rate
    tone = np.sin(2 * np.pi * hz * t).astype(np.float32)
    env = np.ones(n, dtype=np.float32)
    a_n = int(0.05 * sample_rate)
    env[:a_n] = np.linspace(0, 1, a_n)
    env[-a_n:] = np.linspace(1, 0, a_n)
    return tone * env * 0.3


def _multi(specs, gap_s=0.3, sample_rate=22050):
    chunks = []
    for hz, dur in specs:
        chunks.append(_utterance(hz, dur, sample_rate))
        chunks.append(np.zeros(int(gap_s * sample_rate), dtype=np.float32))
    return np.concatenate(chunks)


@pytest.fixture
def mp3_path():
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    _encode(f.name, _multi([(440, 0.4), (880, 0.4), (440, 0.4)]))
    try:
        yield f.name
    finally:
        try:
            os.unlink(f.name)
        except OSError:
            pass


# --- tests --------------------------------------------------------------

def test_lexicon_opens_as_graph_node():
    wa = WorldAdapter()
    lex = wa.open_audio_lexicon(name="audio_test")
    node = wa.s.node(lex)
    assert node["type"] == "AcousticLexicon"
    assert node["attrs"].get("name") == "audio_test"


def test_lexicon_open_is_idempotent():
    wa = WorldAdapter()
    a = wa.open_audio_lexicon(name="audio_test")
    b = wa.open_audio_lexicon(name="audio_test")
    assert a == b
    # distinct names -> distinct lexicons
    c = wa.open_audio_lexicon(name="other")
    assert c != a


def test_ingest_file_writes_messages_with_acoustic_mentions(mp3_path):
    wa = WorldAdapter()
    results = wa.ingest_audio_file(mp3_path, lexicon_name="audio_test",
                                   match_threshold=0.80)
    assert len(results) >= 1, results
    for r in results:
        assert "message" in r and "sign" in r
        msg = wa.s.node(r["message"])
        assert msg["type"] == "Message"
        assert msg["attrs"].get("source") == "audio"
        if r["sign"] is not None:
            mentions = set(wa.inner.neighbours(r["message"], "has_mention"))
            assert r["sign"] in mentions


def test_recognised_signs_grow_in_the_lexicon(mp3_path):
    wa = WorldAdapter()
    assert wa.audio_signs("audio_test") == []
    wa.ingest_audio_file(mp3_path, lexicon_name="audio_test")
    assert len(wa.audio_signs("audio_test")) >= 1


def test_heard_utterance_is_comprehended_into_an_intent(mp3_path):
    """End-to-end hear -> comprehend: with comprehend=True each audio Message is
    comprehension-ready (has_speech_act + sent_by), so comprehend() fires the
    seeded intent Rules and builds an Intent per heard utterance. This is the
    audio analogue of test_audio_world's running-agent-processes-audio test, on
    the migrated (no-CuriousAgent) path."""
    wa = WorldAdapter()
    results = wa.ingest_audio_file(mp3_path, lexicon_name="audio_test",
                                   comprehend=True)
    assert len(results) >= 1
    wa.comprehend()
    for r in results:
        it = wa.intent_of(r["message"])
        assert it is not None, f"no Intent built for audio Message {r['message']}"
        assert wa.s.node(it)["type"] == "Intent"
