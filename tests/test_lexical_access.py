"""Lexical access tests — phoneme sequences bind to AcousticSigns.

The core claim: re-hearing the same audio reuses the same sign;
the lexicon grows monotonically across runs; an Utterance with
heard_as edge lands per run.
"""
from __future__ import annotations

import numpy as np
import pytest

srs = pytest.importorskip("substrate_rs")

from domains.auditory_cortex import attach_a1_pipeline
from domains.categorical_perception import attach_categorical_perception
from domains.cochlear_nucleus import attach_default_pipeline as attach_cochlear
from domains.lexical_access import attach_lexical_access
from substrate.seed_loader import manifest_for


_FS = 22050
_BANDS = [200.0, 400.0, 800.0, 1500.0, 3000.0, 6000.0]


def _attach(sub):
    for seed_id in ("audio", "cochlear_nucleus", "inferior_colliculus",
                      "auditory_cortex", "categorical_perception",
                      "speech", "lexical_access",
                      "tunable_parameter", "reconsider",
                      "compositional_chunking"):
        try:
            sub.load_seed_manifest(manifest_for(seed_id))
        except Exception:
            pass


def _build_full_pipeline(sub, distance_threshold=0.05):
    """Tight threshold so distinct acoustic shapes don't collapse
    after L2 normalisation."""
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    attach_cochlear(sub, stream, band_centres_hz=_BANDS)
    attach_a1_pipeline(sub, stream)
    attach_categorical_perception(
        sub, stream, distance_threshold=distance_threshold)
    attach_lexical_access(sub, stream)
    return stream


def _tone(hz: float, dur: float = 0.5) -> np.ndarray:
    n = int(dur * _FS)
    t = np.arange(n, dtype=np.float32) / _FS
    a = max(1, int(0.02 * _FS))
    ramp = np.linspace(0, 1, a, dtype=np.float32)
    x = (0.4 * np.sin(2 * np.pi * hz * t)).astype(np.float32)
    x[:a] *= ramp
    x[-a:] *= ramp[::-1]
    return x


def _bandlimited_noise(lo_hz: float, hi_hz: float,
                         duration_s: float = 0.5) -> np.ndarray:
    n = int(duration_s * _FS)
    rng = np.random.default_rng(42)
    x = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0 / _FS)
    spec *= (freqs >= lo_hz) & (freqs <= hi_hz)
    y = np.fft.irfft(spec, n=n).astype(np.float32)
    peak = float(np.max(np.abs(y)) or 1.0)
    return (0.4 * y / peak).astype(np.float32)


def _run(sub, stream, samples):
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()
    return sub._inner.run_audio_pipeline(stream, raw, _FS)


def test_lexicon_starts_empty_and_first_run_mints_a_sign():
    """No AcousticSigns in the substrate initially. First run mints
    at least one."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_full_pipeline(sub)
    assert sum(1 for _ in sub.nodes("AcousticSign")) == 0
    _run(sub, stream, _tone(800.0))
    signs = list(sub.nodes("AcousticSign"))
    assert len(signs) >= 1
    # The sign carries a trajectory attr (multi-channel envelope
    # downsampled to fixed length, unit-normalised).
    assert "trajectory" in sub.node(signs[0])["attrs"]


def test_lexicon_stabilises_with_repetition():
    """Run identical audio many times. After a few rounds the
    phoneme centroids stabilise and re-hearing reuses existing
    signs — lexicon growth flattens and at least one sign
    accumulates multiple hearings."""
    sub = srs.Substrate()
    _attach(sub)
    samples = _tone(800.0)
    lexicon_sizes = []
    for _ in range(6):
        stream = _build_full_pipeline(sub)
        _run(sub, stream, samples)
        lexicon_sizes.append(sum(1 for _ in sub.nodes("AcousticSign")))

    # The lexicon shouldn't grow linearly; later rounds should
    # reuse signs minted in earlier rounds.
    n_runs = len(lexicon_sizes)
    final = lexicon_sizes[-1]
    assert final < n_runs, (
        f"identical audio across {n_runs} runs should reuse signs; "
        f"lexicon trajectory: {lexicon_sizes}")
    # At least one sign accumulated > 1 hearing.
    max_hearings = max(
        int(sub.node(s)["attrs"].get("hearings", 0))
        for s in sub.nodes("AcousticSign")
    )
    assert max_hearings >= 2, (
        f"expected at least one sign with hearings >= 2; "
        f"trajectory {lexicon_sizes}, max hearings {max_hearings}")


def test_distinct_audio_mints_distinct_signs():
    """A low tone vs high noise should produce two different
    AcousticSigns."""
    sub = srs.Substrate()
    _attach(sub)
    stream1 = _build_full_pipeline(sub)
    _run(sub, stream1, _tone(400.0))
    stream2 = _build_full_pipeline(sub)
    _run(sub, stream2, _bandlimited_noise(3000.0, 8000.0))
    signs = list(sub.nodes("AcousticSign"))
    assert len(signs) >= 2

    # The two streams should heard_as different signs (their
    # phoneme sequences should differ).
    def signs_for(stream):
        out = set()
        for utt in sub.in_neighbours(stream, "from_stream"):
            if sub.node(utt)["type"] != "Utterance":
                continue
            for s in sub.neighbours(utt, "heard_as"):
                out.add(s)
        return out

    s1 = signs_for(stream1)
    s2 = signs_for(stream2)
    assert s1 and s2
    assert s1 != s2, (
        f"distinct audio should map to distinct AcousticSigns; "
        f"both went to {s1}")


def test_utterance_carries_provenance():
    """Each run mints an Utterance with from_stream + heard_as
    edges — the audit trail back to which audio was heard as what."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_full_pipeline(sub)
    _run(sub, stream, _tone(800.0))
    utterances = [
        u for u in sub.in_neighbours(stream, "from_stream")
        if sub.node(u)["type"] == "Utterance"
    ]
    assert len(utterances) >= 1
    utt = utterances[0]
    signs = list(sub.neighbours(utt, "heard_as"))
    assert len(signs) == 1
    sign = signs[0]
    assert sub.node(sign)["type"] == "AcousticSign"


def test_sign_trajectory_is_introspectable():
    """An AcousticSign stores its multi-channel trajectory as a
    Tuple of floats — the agent can read its own lexicon entries
    as concrete acoustic shapes."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_full_pipeline(sub)
    _run(sub, stream, _tone(800.0))
    signs = list(sub.nodes("AcousticSign"))
    assert signs
    for sign in signs:
        traj = sub.node(sign)["attrs"]["trajectory"]
        assert isinstance(traj, tuple)
        assert len(traj) > 0
        assert all(isinstance(x, float) for x in traj)
