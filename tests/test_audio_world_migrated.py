"""AudioWorld bench — migrated twin of tests/test_audio_world.py.

All four tests from the CuriousAgent-based bench are covered here on
the seed-booted WorldAdapter (no CuriousAgent). The agent tick thread
is the Rust substrate's own; quiesce is via wa.s.quiesce().

Coverage map (original → migrated):
  test_attach_starts_agent_and_opens_lexicon
    → test_open_audio_lexicon_creates_graph_node
      (lexicon is a graph-resident AcousticLexicon node, checked directly;
       agent tick-thread lifecycle is tested via wa.s.start_agent /
       agent_running / stop_agent on the underlying Substrate)

  test_double_attach_is_idempotent
    → test_open_audio_lexicon_is_idempotent
      (two open_audio_lexicon calls on the same name return the same NodeID;
       a distinct name produces a different NodeID — idempotency is in the
       graph node, not a Python attach method)

  test_ingest_file_writes_messages_with_acoustic_mentions
    → test_ingest_audio_file_writes_messages_with_acoustic_mentions
      (same assertion: every result has message+sign, Message.type==Message,
       source==audio, sign in has_mention neighbours)

  test_running_agent_processes_audio_input_async
    → test_ingest_then_comprehend_builds_intents
      (ingest_audio_file(comprehend=True) makes Messages comprehension-ready;
       wa.comprehend() fires the seeded intent/speech-bridge Rules;
       every audio Message then has an Intent via has_intent — the
       synchronous equivalent of the async tick-thread + quiesce path)
"""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

av = pytest.importorskip("av")
srs = pytest.importorskip("substrate_rs")
_audio = pytest.importorskip("substrate_rs.audio")
_speech = pytest.importorskip("substrate_rs.speech")

from substrate.world_adapter import WorldAdapter


# --- audio synthesis helpers (same shape as test_audio_world.py) --------

def _encode(path: str, codec: str, *, sample_rate: int,
            samples: np.ndarray, chunk: int = 1024) -> str:
    container = av.open(path, mode="w")
    stream = container.add_stream(codec, rate=sample_rate)
    stream.codec_context.layout = "mono"
    n = len(samples)
    samples = samples.astype(np.float32).reshape(1, -1)
    for start in range(0, n, chunk):
        sub = samples[:, start:start + chunk]
        if sub.shape[1] < chunk:
            sub = np.pad(sub, ((0, 0), (0, chunk - sub.shape[1])))
        frame = av.AudioFrame.from_ndarray(sub, format="flt", layout="mono")
        frame.sample_rate = sample_rate
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


def _utterance_audio(tone_hz: float, duration_s: float = 0.4,
                     sample_rate: int = 22050) -> np.ndarray:
    n = int(sample_rate * duration_s)
    t = np.arange(n) / sample_rate
    tone = np.sin(2 * np.pi * tone_hz * t).astype(np.float32)
    env = np.ones(n, dtype=np.float32)
    a_n = int(0.05 * sample_rate)
    env[:a_n] = np.linspace(0, 1, a_n)
    env[-a_n:] = np.linspace(1, 0, a_n)
    return tone * env * 0.3


def _multi_utterance_audio(tone_specs, gap_s=0.3, sample_rate=22050):
    chunks = []
    for hz, dur in tone_specs:
        chunks.append(_utterance_audio(hz, dur, sample_rate))
        chunks.append(np.zeros(int(gap_s * sample_rate), dtype=np.float32))
    return np.concatenate(chunks)


@pytest.fixture
def mp3_path():
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    audio = _multi_utterance_audio([
        (440, 0.4), (880, 0.4), (440, 0.4),
    ], gap_s=0.3, sample_rate=22050)
    _encode(f.name, "mp3", sample_rate=22050, samples=audio)
    try:
        yield f.name
    finally:
        try:
            os.unlink(f.name)
        except OSError:
            pass


# --- tests --------------------------------------------------------------


def test_open_audio_lexicon_creates_graph_node():
    """open_audio_lexicon mints an AcousticLexicon graph-resident node.

    Migrated from test_attach_starts_agent_and_opens_lexicon: the lexicon
    is a graph node (same assertion); the agent tick-thread lifecycle is
    on wa.s (the Substrate), not a CuriousAgent wrapper."""
    wa = WorldAdapter()
    assert wa.s.agent_running() is False
    lex = wa.open_audio_lexicon(name="audio_test")
    # The Lexicon is a graph-resident node.
    node = wa.s.node(lex)
    assert node["type"] == "AcousticLexicon"
    assert node["attrs"].get("name") == "audio_test"
    # The substrate's tick thread starts and stops on demand.
    wa.s.start_agent()
    assert wa.s.agent_running() is True
    wa.s.stop_agent()


def test_open_audio_lexicon_is_idempotent():
    """Two open_audio_lexicon calls on the same name return the same NodeID.

    Migrated from test_double_attach_is_idempotent: idempotency lives in
    the graph (find-or-create by name), not in an attach method."""
    wa = WorldAdapter()
    lex1 = wa.open_audio_lexicon(name="audio_test")
    lex2 = wa.open_audio_lexicon(name="audio_test")
    assert lex1 == lex2
    # A distinct name produces a distinct lexicon node.
    lex_other = wa.open_audio_lexicon(name="audio_other")
    assert lex_other != lex1


def test_ingest_audio_file_writes_messages_with_acoustic_mentions(mp3_path):
    """ingest_audio_file mints Message{source: audio} nodes with AcousticSigns
    attached via has_mention.

    Migrated from test_ingest_file_writes_messages_with_acoustic_mentions:
    same assertions, against wa.s / wa.inner instead of agent.mind_graph."""
    wa = WorldAdapter()
    results = wa.ingest_audio_file(mp3_path, lexicon_name="audio_test",
                                   match_threshold=0.80)
    assert len(results) >= 1, results
    for r in results:
        assert "message" in r and "sign" in r
        mid = r["message"]
        sid = r["sign"]
        msg = wa.s.node(mid)
        assert msg["type"] == "Message"
        assert msg["attrs"].get("source") == "audio"
        # Each Message carries the AcousticSign as a has_mention edge —
        # the speech-bridge Rule will mirror denotes → refers_to so the
        # existing intent Rules treat it as a Mention.
        if sid is not None:
            mentions = set(wa.inner.neighbours(mid, "has_mention"))
            assert sid in mentions


def test_ingest_then_comprehend_builds_intents(mp3_path):
    """End-to-end: ingest audio Messages then fire the intent Rules.

    Migrated from test_running_agent_processes_audio_input_async: the async
    tick-thread + quiesce path maps to the synchronous ingest(comprehend=True)
    + comprehend() path. Both assert that every audio Message gets an Intent
    node via the seeded intent Rules (intent_from_claim fires on Message +
    has_speech_act + sent_by — the three edges comprehend=True adds)."""
    wa = WorldAdapter()
    results = wa.ingest_audio_file(mp3_path, lexicon_name="audio_test",
                                   comprehend=True)
    assert len(results) >= 1
    wa.comprehend()
    for r in results:
        mid = r["message"]
        intents = list(wa.inner.neighbours(mid, "has_intent"))
        assert intents, f"no Intent built for audio Message {mid}"
