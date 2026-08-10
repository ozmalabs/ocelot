"""STTPipeline end-to-end tests — ingest / teach / transcribe.

The substrate-native STT loop: teach the agent labels for known
sounds, then transcribe new audio against the learned vocabulary.
Everything graph-resident — Phonemes, AcousticSigns, denotes
edges to Concepts — and inspectable.
"""
from __future__ import annotations

import numpy as np
import pytest

srs = pytest.importorskip("substrate_rs")

from domains.stt_pipeline import STTParams, STTPipeline


_FS = 22050


def _tone(hz: float, dur: float = 0.5,
            fs: int = _FS) -> np.ndarray:
    n = int(dur * fs)
    t = np.arange(n, dtype=np.float32) / fs
    a = max(1, int(0.02 * fs))
    ramp = np.linspace(0, 1, a, dtype=np.float32)
    x = (0.4 * np.sin(2 * np.pi * hz * t)).astype(np.float32)
    x[:a] *= ramp
    x[-a:] *= ramp[::-1]
    return x


def _bandlimited_noise(lo_hz: float, hi_hz: float,
                         dur: float = 0.5,
                         fs: int = _FS) -> np.ndarray:
    n = int(dur * fs)
    rng = np.random.default_rng(42)
    x = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    spec *= (freqs >= lo_hz) & (freqs <= hi_hz)
    y = np.fft.irfft(spec, n=n).astype(np.float32)
    peak = float(np.max(np.abs(y)) or 1.0)
    return (0.4 * y / peak).astype(np.float32)


def _two_tone_with_gap(hz1: float, hz2: float,
                          burst_dur: float = 0.4,
                          gap_dur: float = 0.4,
                          fs: int = _FS) -> np.ndarray:
    """Two distinct tone bursts with silence between — a stand-in
    for two words separated by a pause. The gap is long enough to
    cross the default gap_threshold_ms in lexical_access."""
    return np.concatenate([
        _tone(hz1, burst_dur, fs),
        np.zeros(int(gap_dur * fs), dtype=np.float32),
        _tone(hz2, burst_dur, fs),
    ])


def test_attach_is_idempotent():
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    p.attach(sub)  # no exception
    p.attach(sub)


def test_ingest_returns_heard_signs():
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    signs = p.ingest(sub, _tone(400.0))
    assert signs, "ingest should mint at least one sign"
    for s in signs:
        assert sub.node(s)["type"] == "AcousticSign"


def test_teach_grounds_signs_to_concept():
    """Teaching with a label creates a Concept{name=label} and
    wires `sign --denotes--> Concept` for every sign produced."""
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    result = p.teach(sub, _tone(400.0), "alpha")
    assert result["signs_grounded"] >= 1
    concept_id = result["concept_id"]
    assert sub.node(concept_id)["attrs"]["name"] == "alpha"
    for sig in result["signs"]:
        denoted = list(sub.neighbours(sig, "denotes"))
        assert concept_id in denoted


def test_transcribe_returns_label_for_taught_audio():
    """Teach alpha, then transcribe the same audio. Recognised."""
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    p.teach(sub, _tone(400.0), "alpha")
    text = p.transcribe(sub, _tone(400.0))
    # First (and likely only) label in transcript is "alpha".
    assert "alpha" in text.split(), (
        f"expected 'alpha' in transcript; got {text!r}")


def test_transcribe_distinguishes_taught_labels():
    """Teach two distinct sounds with different labels. Transcribe
    new audio matching each label — they should come back
    distinct."""
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    p.teach(sub, _tone(400.0), "low")
    p.teach(sub, _bandlimited_noise(3000.0, 8000.0), "high")
    t_low = p.transcribe(sub, _tone(400.0))
    t_high = p.transcribe(sub, _bandlimited_noise(3000.0, 8000.0))
    assert "low" in t_low.split(), (
        f"low-tone audio should transcribe to 'low'; got {t_low!r}")
    assert "high" in t_high.split(), (
        f"high-noise audio should transcribe to 'high'; got {t_high!r}")


def test_multi_word_segmentation_produces_two_signs():
    """A single stream containing two tone bursts separated by
    silence should produce TWO Utterances (one per word) with
    potentially distinct AcousticSigns."""
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    samples = _two_tone_with_gap(400.0, 800.0,
                                    burst_dur=0.3, gap_dur=0.3)
    signs = p.ingest(sub, samples)
    # The stream should produce at least 2 Utterance nodes (one
    # per gap-delimited chunk). Each carries its heard_as edge to
    # an AcousticSign.
    n_utts = 0
    streams = [n for n in sub.nodes("AudioStream")]
    for stream in streams:
        for utt in sub.in_neighbours(stream, "from_stream"):
            if sub.node(utt)["type"] == "Utterance":
                n_utts += 1
    assert n_utts >= 2, (
        f"two-word audio should produce at least 2 Utterances; "
        f"got {n_utts}")


def test_vocabulary_introspection():
    """After teaching, the agent's vocabulary is queryable."""
    sub = srs.Substrate()
    p = STTPipeline()
    p.attach(sub)
    p.teach(sub, _tone(400.0), "low")
    p.teach(sub, _bandlimited_noise(3000.0, 8000.0), "high")
    vocab = p.vocabulary(sub)
    assert "low" in vocab
    assert "high" in vocab
    # Sign NodeIDs are real graph data.
    for label, sig in vocab.items():
        assert sub.node(sig)["type"] == "AcousticSign"
