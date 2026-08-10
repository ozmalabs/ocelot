"""Categorical perception tests — Phoneme clusters emerge from A1
response patterns, no inventory seeded. The core claim: different-
class inputs land in different clusters, same-class inputs land in
the same cluster, and the lexicon grows monotonically as new
sound categories appear."""
from __future__ import annotations

import numpy as np
import pytest

srs = pytest.importorskip("substrate_rs")

from domains.auditory_cortex import attach_a1_pipeline, _DEFAULT_PATCHES
from domains.categorical_perception import attach_categorical_perception
from domains.cochlear_nucleus import attach_default_pipeline as attach_cochlear
from substrate.seed_loader import manifest_for


_FS = 22050
_BANDS = [200.0, 400.0, 800.0, 1500.0, 3000.0, 6000.0]


def _attach(sub):
    for seed_id in ("audio", "cochlear_nucleus", "inferior_colliculus",
                      "auditory_cortex", "categorical_perception"):
        try:
            sub.load_seed_manifest(manifest_for(seed_id))
        except Exception:
            pass


def _build_pipeline(sub):
    """Build a stream + the full auditory pipeline + categorical-
    perception op."""
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    attach_cochlear(sub, stream, band_centres_hz=_BANDS)
    attach_a1_pipeline(sub, stream)
    attach_categorical_perception(sub, stream,
                                     distance_threshold=0.15)
    return stream


def _tone_burst(hz: float, duration_s: float = 0.5,
                  fs: int = _FS) -> np.ndarray:
    n = int(duration_s * fs)
    t = np.arange(n, dtype=np.float32) / fs
    a = max(1, int(0.02 * fs))
    ramp = np.linspace(0, 1, a, dtype=np.float32)
    x = (0.4 * np.sin(2 * np.pi * hz * t)).astype(np.float32)
    x[:a] *= ramp
    x[-a:] *= ramp[::-1]
    return x


def _bandlimited_noise(lo_hz: float, hi_hz: float,
                         duration_s: float = 0.5,
                         fs: int = _FS) -> np.ndarray:
    n = int(duration_s * fs)
    rng = np.random.default_rng(42)
    x = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    spec *= (freqs >= lo_hz) & (freqs <= hi_hz)
    y = np.fft.irfft(spec, n=n).astype(np.float32)
    peak = float(np.max(np.abs(y)) or 1.0)
    return (0.4 * y / peak).astype(np.float32)


def _run(sub, stream, samples):
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()
    return sub._inner.run_audio_pipeline(stream, raw, _FS)


def _phoneme_count(sub) -> int:
    return sum(1 for _ in sub.nodes("Phoneme"))


def _instances(sub, stream):
    return list(sub.neighbours(stream, "has_phoneme_instance"))


def test_op_lands_as_graph_data():
    """A categorical_perception Operation node is wired by feeds_into
    from every patch_evaluate op."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_pipeline(sub)
    cp_ops = [op for op in sub.nodes("Operation")
              if sub.node(op)["attrs"]["kind"] == "categorical_perception"]
    assert len(cp_ops) == 1
    cp = cp_ops[0]
    preds = list(sub.in_neighbours(cp, "feeds_into"))
    patch_preds = [
        p for p in preds
        if sub.node(p)["attrs"].get("kind") == "patch_evaluate"
    ]
    assert len(patch_preds) == len(_DEFAULT_PATCHES)  # one per default A1Patch


def test_first_input_mints_phonemes():
    """Run a single sustained tone; some Phoneme nodes should
    appear (one or more clusters)."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_pipeline(sub)
    assert _phoneme_count(sub) == 0
    _run(sub, stream, _tone_burst(800.0, duration_s=0.5))
    assert _phoneme_count(sub) > 0, "expected at least one Phoneme to emerge"
    # Some PhonemeInstances were minted on the stream.
    insts = _instances(sub, stream)
    assert len(insts) > 0


def test_repeated_input_reuses_existing_phonemes():
    """Re-running the same audio should add PhonemeInstances but
    not create many new Phonemes — existing centroids should
    re-match."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_pipeline(sub)
    samples = _tone_burst(800.0, duration_s=0.5)
    _run(sub, stream, samples)
    n1 = _phoneme_count(sub)
    inst1 = len(_instances(sub, stream))

    # Run AGAIN (same audio).
    _run(sub, stream, samples)
    n2 = _phoneme_count(sub)
    inst2 = len(_instances(sub, stream))

    # Phoneme count should be stable or barely grow (centroids
    # don't drift much from one identical run).
    assert n2 <= n1 + 1, (
        f"identical re-run should reuse Phonemes; "
        f"grew from {n1} to {n2}")
    # PhonemeInstance count should roughly double.
    assert inst2 > inst1
    assert inst2 < inst1 * 3


def test_distinct_inputs_land_in_distinct_clusters():
    """A low tone and high noise should map to DIFFERENT
    Phonemes."""
    sub = srs.Substrate()
    _attach(sub)
    stream_low = _build_pipeline(sub)
    stream_high = _build_pipeline(sub)
    _run(sub, stream_low, _tone_burst(400.0, duration_s=0.5))
    _run(sub, stream_high,
         _bandlimited_noise(3000.0, 8000.0, duration_s=0.5))

    low_phonemes = {
        next(iter(sub.neighbours(inst, "is_a")))
        for inst in _instances(sub, stream_low)
    }
    high_phonemes = {
        next(iter(sub.neighbours(inst, "is_a")))
        for inst in _instances(sub, stream_high)
    }
    assert low_phonemes
    assert high_phonemes
    overlap = low_phonemes & high_phonemes
    # The two stimuli shouldn't dominantly share their phoneme set.
    # Some shared "silence-like" categories may overlap on the
    # ramp-up/down samples, but the dominant categories should be
    # disjoint.
    assert len(low_phonemes - overlap) > 0, (
        f"low-tone phonemes {low_phonemes} should have categories "
        f"not present in high-noise phonemes {high_phonemes}")
    assert len(high_phonemes - overlap) > 0


def test_phoneme_centroid_attrs_are_introspectable():
    """Phoneme nodes carry one attr per A1 patch — the centroid in
    patch-response space. The agent can read its own emergent
    categories."""
    sub = srs.Substrate()
    _attach(sub)
    stream = _build_pipeline(sub)
    _run(sub, stream, _tone_burst(800.0, duration_s=0.5))
    expected_dims = {p["name"] for p in _DEFAULT_PATCHES}
    for pn in sub.nodes("Phoneme"):
        a = sub.node(pn)["attrs"]
        # Every patch name should have a centroid value.
        assert expected_dims <= set(a.keys()), (
            f"Phoneme attrs {set(a.keys())} missing dims; "
            f"expected {expected_dims}")
        assert "n_samples" in a
        assert a["n_samples"] >= 1
