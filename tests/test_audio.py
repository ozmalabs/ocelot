"""Phase 14 — audio as graph data.

Two halves: primitives (AudioBuffer + Filter + cochlear filterbank +
STFT) and format parsing (audio container/stream/frame via PyAV).

Headline property (shared with vision): every receptive field is
graph data the agent can read, edit, compose. A Gammatone filter is
a Filter node with `weights` bytes attr — the agent's standard DSL
queries it like any other node.

Bridge: STFT returns an Image node, so the V1 cortex (Gabor banks,
V2 corner detectors, Hebbian learning) composes on top of audio.
This is how speech recognition works — and the agent gets it for
free because spectrograms ARE images in the substrate.
"""
from __future__ import annotations

import math
import os
import tempfile

import numpy as np
import pytest

# OPTIONAL DEPENDENCIES (red-test triage 2026-08-12): absent 'av' is a SKIP with a
# named reason on the tests that need it, never a red. See tests/optional_deps.py.
from optional_deps import requires as _requires_optional  # noqa: E402



srs = pytest.importorskip("substrate_rs")
a = pytest.importorskip("substrate_rs.audio")
v = pytest.importorskip("substrate_rs.vision")


@pytest.fixture
def s():
    sub = srs.Substrate()
    a.seed_audio_grammar(sub)
    return sub


# --- AudioBuffer bridge ----------------------------------------------


def test_audio_buffer_round_trip(s):
    samples = np.linspace(-1, 1, 100, dtype=np.float32)
    nid = a.audio_from_array(s, samples, sample_rate=22050)
    back = a.audio_to_array(s, nid)
    np.testing.assert_array_equal(back, samples)
    n, c, fs = a.audio_shape(s, nid)
    assert (n, c, fs) == (100, 1, 22050)


def test_audio_buffer_stereo_round_trip(s):
    rng = np.random.RandomState(0)
    samples = rng.randn(50, 2).astype(np.float32)
    nid = a.audio_from_array(s, samples, sample_rate=44100)
    back = a.audio_to_array(s, nid)
    np.testing.assert_array_equal(back, samples)
    n, c, fs = a.audio_shape(s, nid)
    assert (n, c, fs) == (50, 2, 44100)


def test_audio_buffer_attrs_visible_to_dsl(s):
    samples = np.zeros(1000, dtype=np.float32)
    nid = a.audio_from_array(s, samples, sample_rate=16000)
    duration = s.evaluate(srs.Attr(srs.Lit(nid), "duration_s"))
    rate = s.evaluate(srs.Attr(srs.Lit(nid), "sample_rate"))
    assert duration == pytest.approx(1000 / 16000)
    assert rate == 16000


# --- Filter primitives + biology-named constructors ------------------


def test_filter_round_trip(s):
    h = np.array([1.0, -2.0, 1.0, -2.0, 1.0], dtype=np.float32)
    nid = a.filter_from_array(s, "manual", h, fs=22050)
    back = a.filter_to_array(s, nid)
    np.testing.assert_array_equal(back, h)
    d = a.filter_describe(s, nid)
    assert d["name"] == "manual"
    assert d["length"] == 5
    assert d["sample_rate"] == 22050


def test_gammatone_filter_attrs_introspectable(s):
    """Filter introspection via the standard DSL — Gammatone receptive
    fields are graph data."""
    g = a.gammatone(s, fc=1000.0, fs=22050)
    name = s.evaluate(srs.Attr(srs.Lit(g), "name"))
    origin = s.evaluate(srs.Attr(srs.Lit(g), "origin"))
    length = s.evaluate(srs.Attr(srs.Lit(g), "length"))
    assert "fc=1000" in name
    assert origin == "gammatone"
    assert length > 0


def test_gammatone_response_peaks_near_centre_frequency(s):
    """A Gammatone filter applied to a sine wave at its centre
    frequency should produce a much larger response than at a far-
    off frequency. The defining property of a tuned filter."""
    fs = 22050
    duration_s = 0.1
    t = np.arange(int(fs * duration_s)) / fs
    # Sine at 1 kHz vs 5 kHz; build a 1 kHz Gammatone.
    g_nid = a.gammatone(s, fc=1000.0, fs=fs)
    sine_1k = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    sine_5k = np.sin(2 * np.pi * 5000 * t).astype(np.float32)
    buf_1k = a.audio_from_array(s, sine_1k, sample_rate=fs)
    buf_5k = a.audio_from_array(s, sine_5k, sample_rate=fs)
    resp_1k = a.audio_to_array(s, a.convolve_1d(s, buf_1k, g_nid))
    resp_5k = a.audio_to_array(s, a.convolve_1d(s, buf_5k, g_nid))
    # 1 kHz Gammatone should respond much more strongly to 1 kHz
    # input than to 5 kHz input.
    e_1k = float(np.mean(resp_1k ** 2))
    e_5k = float(np.mean(resp_5k ** 2))
    assert e_1k > 5.0 * e_5k, (
        f"1 kHz response should dominate; got 1k={e_1k:.3f} 5k={e_5k:.3f}")


def test_lowpass_attenuates_high_frequencies(s):
    """A 1 kHz lowpass should pass a 500 Hz sine and attenuate a
    5 kHz sine."""
    fs = 22050
    t = np.arange(int(fs * 0.1)) / fs
    lp = a.lowpass(s, cutoff=1000.0, fs=fs, length=129)
    s500 = np.sin(2 * np.pi * 500 * t).astype(np.float32)
    s5k = np.sin(2 * np.pi * 5000 * t).astype(np.float32)
    b500 = a.audio_from_array(s, s500, sample_rate=fs)
    b5k = a.audio_from_array(s, s5k, sample_rate=fs)
    o500 = a.audio_to_array(s, a.convolve_1d(s, b500, lp))
    o5k = a.audio_to_array(s, a.convolve_1d(s, b5k, lp))
    e_pass = float(np.mean(o500 ** 2))
    e_stop = float(np.mean(o5k ** 2))
    # The pass-band should be at least 5× the stop-band energy.
    assert e_pass > 5.0 * e_stop


def test_convolve_1d_wires_provenance(s):
    """convolve_1d wires `produced_by` + `from_input` exactly like
    the vision convolve — provenance graph is uniform."""
    buf = a.audio_from_array(s, np.zeros(100, dtype=np.float32), sample_rate=22050)
    f = a.lowpass(s, cutoff=1000.0)
    out = a.convolve_1d(s, buf, f)
    assert s.neighbours(out, a.PRODUCED_BY) == [f]
    assert s.neighbours(out, a.FROM_INPUT) == [buf]


# --- Cochlear bank ----------------------------------------------------


def test_cochlea_returns_n_gammatones_at_ascending_frequencies(s):
    bank = a.cochlea(s, n_bands=8, fs=22050, low_hz=100, high_hz=4000)
    assert len(bank) == 8
    # Extract fc from each filter's name and verify ascending.
    fcs = []
    for nid in bank:
        name = s.node(nid)["attrs"]["name"]
        # gammatone:fc=NNN.NHz,...
        fc_str = name.split("fc=")[1].split("Hz")[0]
        fcs.append(float(fc_str))
    assert fcs == sorted(fcs), f"cochlea fcs should ascend: {fcs}"
    # Spaced on the ERB scale — low frequencies more densely packed
    # (the biological property). Verify by checking gaps grow.
    gaps = [fcs[i + 1] - fcs[i] for i in range(len(fcs) - 1)]
    # Each successive gap should be larger than the previous (ERB grows).
    for i in range(1, len(gaps)):
        assert gaps[i] >= gaps[i - 1] * 0.9, (
            f"ERB spacing should grow; gaps={gaps}")


def test_a1_responses_one_per_filter(s):
    """Like vision.v1_responses — apply every filter to the same
    input in parallel. Returns one AudioBuffer per band."""
    fs = 22050
    samples = np.random.RandomState(0).randn(2000).astype(np.float32)
    buf = a.audio_from_array(s, samples, sample_rate=fs)
    bank = a.cochlea(s, n_bands=8, fs=fs)
    responses = a.a1_responses(s, buf, bank)
    assert len(responses) == 8
    # Each response is a real AudioBuffer of length samples.
    for r in responses:
        n, c, fs2 = a.audio_shape(s, r)
        assert c == 1
        assert fs2 == fs
    # Each response's provenance points back to the source buffer
    # AND to its filter.
    for r, f in zip(responses, bank):
        assert s.neighbours(r, a.FROM_INPUT) == [buf]
        assert s.neighbours(r, a.PRODUCED_BY) == [f]


# --- STFT bridge → vision -----------------------------------------------


def test_stft_returns_image_node(s):
    """STFT produces an Image — chains directly into the V1 cortex.
    This is the bridge between audio and vision the substrate makes
    free."""
    v.seed_vision_grammar(s)
    fs = 22050
    samples = np.random.RandomState(0).randn(8192).astype(np.float32)
    buf = a.audio_from_array(s, samples, sample_rate=fs)
    spec_nid = a.stft(s, buf, win_size=512, hop_size=256)
    # Returned NodeID is an Image.
    assert s.node(spec_nid)["type"] == v.IMAGE
    spec = v.image_to_array(s, spec_nid)
    # Shape: (n_bins, n_frames) where n_bins = win_size/2 + 1.
    assert spec.shape[0] == 257
    assert spec.shape[1] > 0


def test_stft_of_pure_tone_concentrates_energy_at_correct_bin(s):
    """STFT of a 1 kHz sine should have nearly all its energy in
    the bin corresponding to 1 kHz — the defining property of a
    Fourier representation."""
    v.seed_vision_grammar(s)
    fs = 22050
    duration_s = 0.5
    win_size = 1024
    t = np.arange(int(fs * duration_s)) / fs
    sine = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    buf = a.audio_from_array(s, sine, sample_rate=fs)
    spec_nid = a.stft(s, buf, win_size=win_size, hop_size=512)
    spec = v.image_to_array(s, spec_nid)
    # Average over time → frequency profile.
    profile = spec.mean(axis=1)
    peak_bin = int(np.argmax(profile))
    # Expected bin for 1 kHz given fs=22050, win=1024: bin = round(f / fs * win)
    expected_bin = int(round(1000 / fs * win_size))
    assert abs(peak_bin - expected_bin) <= 1, (
        f"peak at bin {peak_bin}, expected {expected_bin}")


def test_v1_cortex_processes_spectrogram(s):
    """Spectrogram → Image → V1 Sobel. Witnesses the cross-modal
    composition: a vision kernel detects edges in a sound's time-
    frequency representation, which is what speech-recognition
    formant-trackers do."""
    v.seed_vision_grammar(s)
    fs = 22050
    # Build a chirp — frequency sweeps from 500 Hz to 2 kHz.
    duration_s = 0.5
    t = np.arange(int(fs * duration_s)) / fs
    f0 = 500
    f1 = 2000
    chirp = np.sin(2 * np.pi * (f0 + (f1 - f0) * t / duration_s) * t).astype(np.float32)
    buf = a.audio_from_array(s, chirp, sample_rate=fs)
    spec_nid = a.stft(s, buf, win_size=1024, hop_size=256)
    # V1 horizontal-edge detector (Sobel-y → detects time-shifts
    # in the spectrogram → frequency changes over time).
    sy = v.sobel(s, dx=0, dy=1)
    edge_nid = v.convolve(s, spec_nid, sy)
    edge = v.image_to_array(s, edge_nid)
    # The chirp has lots of frequency-vs-time structure — the edge
    # detector response should have non-trivial energy.
    assert float(np.abs(edge).mean()) > 0.0


# --- Format parsing ---------------------------------------------------


def _make_test_wav(path: str, duration_s: float = 1.0,
                   frequency_hz: float = 440.0, fs: int = 22050) -> str:
    """Synthesise a tiny sine-wave audio file (MP3-encoded for the
    bitstream-parse tests)."""
    import av
    container = av.open(path, mode="w")
    stream = container.add_stream("mp3", rate=fs)
    stream.codec_context.bit_rate = 64000
    n = int(fs * duration_s)
    t = np.arange(n) / fs
    samples = (0.3 * np.sin(2 * np.pi * frequency_hz * t)).astype(np.float32)
    # MP3 frame size is 1152 samples; chunk and feed.
    chunk = 1152
    for start in range(0, n, chunk):
        sub = samples[start:start + chunk]
        frame = av.AudioFrame.from_ndarray(
            sub.reshape(1, -1), format="flt", layout="mono")
        frame.sample_rate = fs
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


@pytest.fixture
def mp3_path():
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    _make_test_wav(f.name, duration_s=1.0, frequency_hz=440.0)
    yield f.name
    os.unlink(f.name)


@_requires_optional('av')
def test_open_audio_container(s, mp3_path):
    cnid = a.open_container(s, mp3_path)
    node = s.node(cnid)
    assert node["type"] == a.AUDIO_CONTAINER
    assert node["attrs"]["path"] == mp3_path
    assert node["attrs"]["n_streams"] >= 1


@_requires_optional('av')
def test_add_audio_stream_carries_codec_info(s, mp3_path):
    cnid = a.open_container(s, mp3_path)
    snid = a.add_stream(s, cnid)
    attrs = s.node(snid)["attrs"]
    # Decoder may add a float-suffix variant ("mp3" vs "mp3float").
    assert attrs["codec"].startswith("mp3")
    assert attrs["sample_rate"] == 22050
    assert snid in s.neighbours(cnid, a.HAS_STREAM)


@_requires_optional('av')
def test_parse_audio_stream_mints_frames(s, mp3_path):
    cnid = a.open_container(s, mp3_path)
    snid = a.add_stream(s, cnid)
    n = a.parse_stream(s, cnid, snid)
    assert n > 0
    frames = s.neighbours(snid, a.HAS_FRAME)
    assert len(frames) == n
    # PTS monotone non-decreasing.
    frames_sorted = sorted(frames, key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    last_pts = -1
    for f in frames_sorted:
        pts = int(s.node(f)["attrs"]["pts"])
        assert pts >= last_pts
        last_pts = pts


@_requires_optional('av')
def test_decode_audio_frame_returns_audio_buffer(s, mp3_path):
    """The explicit 'render this audio frame to samples' path."""
    cnid = a.open_container(s, mp3_path)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    first = min(
        s.neighbours(snid, a.HAS_FRAME),
        key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    buf_nid = a.decode_frame(s, first)
    assert s.node(buf_nid)["type"] == a.AUDIO_BUFFER
    samples = a.audio_to_array(s, buf_nid)
    assert samples.size > 0


@_requires_optional('av')
def test_decoded_audio_chains_into_cochlea(s, mp3_path):
    """End-to-end bridge: decode a real MP3 frame → feed to the
    cochlear bank → response set. Bitstream parser + audio
    primitives compose."""
    cnid = a.open_container(s, mp3_path)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    first = min(
        s.neighbours(snid, a.HAS_FRAME),
        key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    buf = a.decode_frame(s, first)
    bank = a.cochlea(s, n_bands=4, fs=22050)
    responses = a.a1_responses(s, buf, bank)
    assert len(responses) == 4


@_requires_optional('av')
def test_bitrate_profile_summarises_stream(s, mp3_path):
    cnid = a.open_container(s, mp3_path)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    profile = a.bitrate_profile(s, snid, n_buckets=10)
    assert len(profile) == 10
    # At least one bucket has non-zero mean size (it's a real audio file).
    assert any(p > 0 for p in profile)


# --- The headline cross-modal property -------------------------------


def test_speech_recognition_shape_is_uniform_with_vision():
    """The architectural punchline: an MP3 → STFT → V1 Sobel
    pipeline is exactly what classical speech-recognition systems
    do (Davis & Mermelstein 1980 onwards). With this stack the
    agent gets it for free — every step is graph data."""
    s = srs.Substrate()
    a.seed_audio_grammar(s)
    v.seed_vision_grammar(s)
    # Synthesise audio with frequency structure.
    fs = 22050
    t = np.arange(int(fs * 0.3)) / fs
    samples = (np.sin(2 * np.pi * 500 * t) +
               0.5 * np.sin(2 * np.pi * 1500 * t)).astype(np.float32)
    buf = a.audio_from_array(s, samples, sample_rate=fs)
    spec = a.stft(s, buf, win_size=1024, hop_size=256)
    sy = v.sobel(s, dx=0, dy=1)
    edges = v.convolve(s, spec, sy)
    # Two-tone signal → two horizontal "ridges" in the spectrogram
    # → horizontal-edge detector responds at both.
    spec_arr = v.image_to_array(s, spec)
    edge_arr = v.image_to_array(s, edges)
    assert spec_arr.shape == edge_arr.shape
    # Spectrogram has the two expected tones — peaks at the right bins.
    profile = spec_arr.mean(axis=1)
    win_size = 1024
    expected_bin_500 = int(round(500 / fs * win_size))
    expected_bin_1500 = int(round(1500 / fs * win_size))
    # Both bins are at least ~20× the mean energy (clear tonal peaks).
    assert profile[expected_bin_500] > 20 * profile.mean()
    assert profile[expected_bin_1500] > 20 * profile.mean()
