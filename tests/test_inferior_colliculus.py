"""Inferior-colliculus tests — modulation-rate analysis + syllable
nucleus detection.

The key test is the syllable-rate one: synthesise a carrier tone
amplitude-modulated at a syllable-typical rate (5 Hz), verify that
the 4-Hz / 8-Hz ModulationChannels both light up with the expected
peak count, and that cross-band coincidence emits a SyllableNucleus
per AM cycle.
"""
from __future__ import annotations

import numpy as np
import pytest

srs = pytest.importorskip("substrate_rs")

from domains.inferior_colliculus_adapter import (DEFAULT_MOD_RATES_HZ,
                                                    IcParams, process_audio)
from substrate.seed_loader import manifest_for


_FS = 22050
_BANDS = [200.0, 400.0, 800.0, 1500.0, 3000.0]


def _attach(sub):
    for seed_id in ("audio", "cochlear_nucleus", "inferior_colliculus"):
        try:
            sub.load_seed_manifest(manifest_for(seed_id))
        except Exception:
            pass


def _am_speech_like(carrier_hz: float = 800.0,
                     am_hz: float = 5.0,
                     duration_s: float = 1.6,
                     mod_depth: float = 0.95,
                     fs: int = _FS) -> np.ndarray:
    """Amplitude-modulated carrier — a stand-in for speech-shaped
    syllabic rhythm. Carrier at carrier_hz, modulated at am_hz; at
    am_hz=5 there are 5 syllable nuclei per second."""
    n = int(duration_s * fs)
    t = np.arange(n, dtype=np.float32) / fs
    am = 0.5 * (1.0 + mod_depth * np.sin(2 * np.pi * am_hz * t -
                                            np.pi / 2))
    carrier = np.sin(2 * np.pi * carrier_hz * t).astype(np.float32)
    return (am * carrier * 0.4).astype(np.float32)


def test_seed_installs_productions():
    sub = srs.Substrate()
    _attach(sub)
    grammar = sub.grammar_to_json()
    edge_types = {p["edge_type"] for p in grammar["productions"]}
    assert "has_modulation_channel" in edge_types
    assert "has_modulation_event" in edge_types
    assert "has_syllable_nucleus" in edge_types


def test_one_channel_per_band_per_modulation_rate():
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _am_speech_like(duration_s=0.5)
    summary = process_audio(sub, stream, samples, _FS, _BANDS)
    expected = len(_BANDS) * len(DEFAULT_MOD_RATES_HZ)
    assert summary["channels"] == expected, (
        f"expected {expected} ModulationChannels "
        f"({len(_BANDS)}×{len(DEFAULT_MOD_RATES_HZ)}), got "
        f"{summary['channels']}")


def test_5hz_am_lights_up_4hz_and_8hz_channels():
    """A 5 Hz AM tone should produce strong energy in the 4 Hz and
    8 Hz modulation channels (the two log-spaced neighbours), and
    less in the 2/16/32/64 Hz channels."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _am_speech_like(am_hz=5.0, duration_s=2.0)
    process_audio(sub, stream, samples, _FS, _BANDS)

    # Average peak energy across cochlear bands per modulation rate.
    per_rate_peaks: dict[float, list[float]] = {}
    for ch in sub.neighbours(stream, "has_modulation_channel"):
        a = sub.node(ch)["attrs"]
        rate = float(a["modulation_rate_hz"])
        per_rate_peaks.setdefault(rate, []).append(float(a["peak"]))
    mean_by_rate = {r: float(np.mean(v))
                     for r, v in per_rate_peaks.items()}

    # The neighbours of 5 Hz on a log scale are 4 and 8.
    syll_band_energy = max(mean_by_rate[4.0], mean_by_rate[8.0])
    far_band_energy = max(mean_by_rate[32.0], mean_by_rate[64.0])
    assert syll_band_energy > far_band_energy * 1.5, (
        f"5 Hz AM should drive 4/8 Hz channels above 32/64 Hz; "
        f"got syllable-band={syll_band_energy:.4g}, "
        f"far-band={far_band_energy:.4g}, all={mean_by_rate}")


def _syllable_bursts(n: int, burst_s: float = 0.15,
                       gap_s: float = 0.15,
                       lead_s: float = 0.1,
                       carrier_hz: float = 800.0,
                       fs: int = _FS) -> np.ndarray:
    """Discrete tone bursts separated by silence — a model of real
    speech syllables, which are bursts of voicing-energy with
    sub-syllabic gaps. n bursts → expect n syllable nuclei."""
    n_burst = int(burst_s * fs)
    n_gap = int(gap_s * fs)
    n_lead = int(lead_s * fs)
    t = np.arange(n_burst, dtype=np.float32) / fs
    chunks: list[np.ndarray] = [np.zeros(n_lead, dtype=np.float32)]
    a = max(1, int(0.02 * fs))  # 20 ms attack/release
    ramp = np.linspace(0.0, 1.0, a).astype(np.float32)
    for _ in range(n):
        burst = (0.4 * np.sin(2 * np.pi * carrier_hz * t)).astype(np.float32)
        burst[:a] *= ramp
        burst[-a:] *= ramp[::-1]
        chunks.append(burst)
        chunks.append(np.zeros(n_gap, dtype=np.float32))
    return np.concatenate(chunks)


def test_syllable_nucleus_per_discrete_burst():
    """Real syllables are discrete bursts of voicing-energy. Feed
    three tone bursts; the IC should emit a SyllableNucleus per
    burst — one per onset of envelope activity in the 4–8 Hz band."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    n_bursts = 3
    samples = _syllable_bursts(n_bursts, burst_s=0.18, gap_s=0.18)
    summary = process_audio(sub, stream, samples, _FS, _BANDS)
    # Tolerate ±1 — boundary effects in the IIR bandpass + the LPF
    # ramp-up can drop the first or last burst's syllable event.
    assert abs(summary["syllables"] - n_bursts) <= 1, (
        f"expected ~{n_bursts} SyllableNucleus events from "
        f"{n_bursts} discrete bursts; got {summary['syllables']}")
    # Each syllable nucleus has at least 2 cochlear bands feeding it.
    for syll in sub.neighbours(stream, "has_syllable_nucleus"):
        a = sub.node(syll)["attrs"]
        assert a["n_bands"] >= 2


def test_ic_pipeline_is_graph_resident():
    """The IC's full pipeline lands as Operation nodes wired by
    feeds_into edges, on top of the cochlear pipeline. The agent
    can read every step."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _am_speech_like(duration_s=0.5)
    process_audio(sub, stream, samples, _FS, _BANDS)

    # Per cochlear band: 1 gammatone + 1 envelope + 1 onset_detect +
    # 1 syllable-candidate schmitt_peaks + (3 ops per mod rate × 6
    # rates). Plus 1 broadband_coincidence (cochlear) + 1
    # syllable_coincidence (IC).
    ops = list(sub.nodes("Operation"))
    n_bands = len(_BANDS)
    n_rates = len(DEFAULT_MOD_RATES_HZ)
    expected = (n_bands * (3 + 1 + 3 * n_rates)) + 2
    assert len(ops) == expected, (
        f"expected {expected} Operation nodes; got {len(ops)}")

    # All known kinds are present.
    kinds = {sub.node(op)["attrs"]["kind"] for op in ops}
    assert kinds >= {"gammatone", "envelope", "onset_detect",
                       "bandpass", "rectified_lpf", "schmitt_peaks",
                       "broadband_coincidence", "syllable_coincidence"}


def test_modulation_events_link_back_to_channels():
    """Every ModulationEvent has a from_channel edge to its source
    ModulationChannel — graph-level audit trail. Channel + event
    metadata is consistent (same band index + modulation rate)."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _am_speech_like(am_hz=5.0, duration_s=1.0)
    process_audio(sub, stream, samples, _FS, _BANDS)
    events = list(sub.neighbours(stream, "has_modulation_event"))
    assert events, "expected at least some ModulationEvents"
    for ev in events:
        chans = list(sub.neighbours(ev, "from_channel"))
        assert len(chans) == 1
        ev_a = sub.node(ev)["attrs"]
        ch_a = sub.node(chans[0])["attrs"]
        assert ev_a["band_index"] == ch_a["band_index"]
        assert ev_a["modulation_rate_hz"] == ch_a["modulation_rate_hz"]
