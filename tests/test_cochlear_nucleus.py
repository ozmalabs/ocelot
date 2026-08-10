"""Cochlear-nucleus tests — onset detection, envelope tracking, and
cross-band broadband coincidence, all running entirely in the Rust
substrate primitive."""
from __future__ import annotations

import numpy as np
import pytest

srs = pytest.importorskip("substrate_rs")

from domains.cochlear_nucleus_adapter import CnParams, process_audio
from substrate.seed_loader import manifest_for


# A small cochlear filterbank spanning the speech band.
_BANDS = [200.0, 400.0, 800.0, 1500.0, 3000.0]
_FS = 22050


def _attach(sub):
    """Load the audio + cochlear_nucleus seeds."""
    for seed_id in ("audio", "cochlear_nucleus"):
        try:
            sub.load_seed_manifest(manifest_for(seed_id))
        except Exception:
            pass


def _silent_then_tone_bursts(burst_hzs: list[float],
                               burst_s: float = 0.15,
                               gap_s: float = 0.2,
                               lead_silence_s: float = 0.1,
                               fs: int = _FS) -> np.ndarray:
    """Build [silence, tone, gap, tone, gap, …] — one burst per
    entry in burst_hzs. Bursts have a fast amplitude ramp so the
    onset detector has a clean transient to bite on."""
    lead = np.zeros(int(lead_silence_s * fs), dtype=np.float32)
    gap = np.zeros(int(gap_s * fs), dtype=np.float32)
    n_burst = int(burst_s * fs)
    t = np.arange(n_burst, dtype=np.float32) / fs
    chunks: list[np.ndarray] = [lead]
    for hz in burst_hzs:
        tone = 0.4 * np.sin(2 * np.pi * hz * t).astype(np.float32)
        # 5 ms attack ramp.
        a = max(1, int(0.005 * fs))
        ramp = np.linspace(0.0, 1.0, a).astype(np.float32)
        tone[:a] *= ramp
        tone[-a:] *= ramp[::-1]
        chunks.append(tone)
        chunks.append(gap)
    return np.concatenate(chunks)


def test_seed_installs_productions():
    sub = srs.Substrate()
    _attach(sub)
    grammar = sub.grammar_to_json()
    edge_types = {p["edge_type"] for p in grammar["productions"]}
    assert "has_onset_event" in edge_types
    assert "has_envelope" in edge_types
    assert "has_broadband_onset" in edge_types


def test_envelope_channel_per_band():
    """One EnvelopeChannel per cochlear band lands in the graph."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _silent_then_tone_bursts([800.0])
    summary = process_audio(sub, stream, samples, _FS, _BANDS)
    assert summary["envelopes"] == len(_BANDS)
    envs = list(sub.neighbours(stream, "has_envelope"))
    assert len(envs) == len(_BANDS)
    # Each envelope records its band metadata.
    for env in envs:
        attrs = sub.node(env)["attrs"]
        assert attrs["sample_rate"] == _FS
        assert "centre_hz" in attrs
        assert attrs["n_samples"] == len(samples)


def test_onset_fires_on_each_tone_burst():
    """Three tone bursts with clean silent gaps should produce at
    least three broadband onsets (one per burst). Per-band onsets
    may be more (the offset also generates a transient in some
    bands' envelopes), but the broadband-coincidence pass
    should converge on roughly burst-count."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _silent_then_tone_bursts([800.0, 1500.0, 400.0])
    summary = process_audio(sub, stream, samples, _FS, _BANDS)
    assert summary["onsets"] >= 3
    assert summary["broadband"] >= 3, (
        f"expected ≥3 broadband onsets for 3 tone bursts; "
        f"got {summary['broadband']}")
    # Each BroadbandOnset has time, n_bands, member-onset count.
    for broad in sub.neighbours(stream, "has_broadband_onset"):
        a = sub.node(broad)["attrs"]
        assert a["n_bands"] >= 2
        assert a["n_member_onsets"] >= a["n_bands"]


def test_broadband_onsets_are_time_ordered_around_bursts():
    """The broadband-onset times should cluster around each burst's
    actual start moment. Bursts at 0.1, 0.45, 0.8 s (with lead +
    gaps) — verify the detected onsets land within ±50 ms."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _silent_then_tone_bursts([800.0, 1500.0, 400.0],
                                          burst_s=0.15, gap_s=0.2,
                                          lead_silence_s=0.1)
    expected_starts = [0.1, 0.1 + 0.15 + 0.2,
                         0.1 + 2 * (0.15 + 0.2)]
    process_audio(sub, stream, samples, _FS, _BANDS)
    times = sorted(
        sub.node(b)["attrs"]["time_s"]
        for b in sub.neighbours(stream, "has_broadband_onset")
    )
    assert len(times) >= 3
    # For each expected burst start, there must be a detected
    # broadband onset within 50 ms.
    for expected in expected_starts:
        assert any(abs(t - expected) < 0.05 for t in times), (
            f"no broadband onset within 50 ms of expected start "
            f"{expected:.3f} s; got {times}")


def test_pipeline_is_graph_resident():
    """The pipeline isn't a Rust function — it's Operation nodes
    wired by feeds_into edges, fully introspectable. The agent
    should be able to read every step of its own processing."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _silent_then_tone_bursts([800.0])
    process_audio(sub, stream, samples, _FS, _BANDS)

    # n_bands × 3 ops (gammatone, envelope, onset_detect) + 1
    # broadband_coincidence Operation nodes.
    expected_n = len(_BANDS) * 3 + 1
    ops = list(sub.nodes("Operation"))
    assert len(ops) == expected_n, (
        f"expected {expected_n} Operation nodes for "
        f"{len(_BANDS)}-band default pipeline; got {len(ops)}")

    # Categorise by kind.
    by_kind: dict[str, list] = {}
    for op in ops:
        kind = sub.node(op)["attrs"]["kind"]
        by_kind.setdefault(kind, []).append(op)
    assert len(by_kind["gammatone"]) == len(_BANDS)
    assert len(by_kind["envelope"]) == len(_BANDS)
    assert len(by_kind["onset_detect"]) == len(_BANDS)
    assert len(by_kind["broadband_coincidence"]) == 1

    # The pipeline entry edges from stream point at gammatone ops.
    entries = list(sub.neighbours(stream, "has_pipeline_entry"))
    assert len(entries) == len(_BANDS)
    for e in entries:
        assert sub.node(e)["attrs"]["kind"] == "gammatone"

    # Each gammatone feeds_into an envelope that feeds_into an
    # onset_detect that feeds_into the broadband_coincidence.
    bb_op = by_kind["broadband_coincidence"][0]
    for gt in by_kind["gammatone"]:
        envs = list(sub.neighbours(gt, "feeds_into"))
        assert len(envs) == 1
        assert sub.node(envs[0])["attrs"]["kind"] == "envelope"
        onsets = list(sub.neighbours(envs[0], "feeds_into"))
        assert len(onsets) == 1
        assert sub.node(onsets[0])["attrs"]["kind"] == "onset_detect"
        bbs = list(sub.neighbours(onsets[0], "feeds_into"))
        assert len(bbs) == 1 and bbs[0] == bb_op


def test_agent_can_retune_pipeline_by_editing_graph():
    """Editing an Operation's attrs changes the next run's behaviour
    — proves the pipeline is data, not code. Build a fresh
    substrate so we control which ops exist, raise every
    onset_detect threshold past the band peak, verify onsets stop
    firing without changing any code."""
    from domains.cochlear_nucleus import attach_default_pipeline
    samples = _silent_then_tone_bursts([800.0, 1500.0, 400.0])
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()

    # Substrate 1 — default pipeline. Many onsets.
    sub1 = srs.Substrate()
    _attach(sub1)
    stream1 = sub1.add_node("AudioStream",
                              {"codec": "raw_pcm", "sample_rate": _FS})
    attach_default_pipeline(sub1, stream1, band_centres_hz=_BANDS)
    summary1 = sub1._inner.run_audio_pipeline(stream1, raw, _FS)
    assert summary1["onsets"] > 0

    # Substrate 2 — same default pipeline but with onset thresholds
    # cranked up to 60 dB via graph edit. Expect zero onsets.
    sub2 = srs.Substrate()
    _attach(sub2)
    stream2 = sub2.add_node("AudioStream",
                              {"codec": "raw_pcm", "sample_rate": _FS})
    attach_default_pipeline(sub2, stream2, band_centres_hz=_BANDS)
    # 200 dB is far above any physical envelope rise; with this
    # threshold no onset can fire. (Tone-burst envelopes typically
    # peak at ~80 dB above the local floor.)
    for op in sub2.nodes("Operation"):
        if sub2.node(op)["attrs"]["kind"] == "onset_detect":
            sub2.set_attr(op, "threshold_db", 200.0)
    summary2 = sub2._inner.run_audio_pipeline(stream2, raw, _FS)
    assert summary2["onsets"] == 0, (
        f"raised onset_detect threshold should suppress events; "
        f"got {summary2}")


def test_contributed_by_edges_audit_trail():
    """Every BroadbandOnset wires `contributed_by` edges to the
    per-band OnsetEvents that fed into it — graph-level audit
    trail. Member count ≥ n_bands (each band can contribute
    multiple onsets that fall in the coincidence window)."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _silent_then_tone_bursts([800.0, 1500.0])
    process_audio(sub, stream, samples, _FS, _BANDS)
    for broad in sub.neighbours(stream, "has_broadband_onset"):
        members = list(sub.neighbours(broad, "contributed_by"))
        assert len(members) > 0
        # Every member is an OnsetEvent.
        for m in members:
            assert sub.node(m)["type"] == "OnsetEvent"
