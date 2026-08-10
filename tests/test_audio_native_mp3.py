"""Phase 14b — listening natively to MP3.

The encoder ran an MDCT filterbank and wrote the per-band coefficients
into the bitstream. Decoding to PCM and then re-running an STFT
throws the encoder's analysis away. We "listen natively" by parsing
the MP3 bitstream directly into graph nodes — frame headers + per-
granule side info — so the agent can identify transients, track
loudness, and read mode switches without ever decoding samples.

Biology: the cochlea's basilar membrane IS a mechanical filter bank.
The MP3 bitstream's MDCT subbands are the closest digital analog.
The natural primitive of hearing is per-band energy over time; the
bitstream already holds it.
"""
from __future__ import annotations

import os
import tempfile

import av
import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")
a = pytest.importorskip("substrate_rs.audio")


def _make_mp3(path: str, *, duration_s: float = 1.0,
              tone_hz: float = 440.0,
              add_transient_at: float | None = None,
              sample_rate: int = 44100,
              bit_rate: int = 128000,
              stereo: bool = False) -> str:
    """Synthesise an MP3 with a tone and (optionally) a single sharp
    transient at the given time. Transients should provoke the
    encoder to use SHORT blocks (its way of avoiding pre-echo).

    PyAV's MP3 encoder defaults to stereo regardless of input frame
    layout, so we force the codec context's layout explicitly."""
    container = av.open(path, mode="w")
    layout = "stereo" if stereo else "mono"
    stream = container.add_stream("mp3", rate=sample_rate)
    stream.codec_context.layout = layout
    stream.codec_context.bit_rate = bit_rate
    # For mono use packed "flt" (1, n). For stereo use planar "fltp"
    # (n_channels, n) — what PyAV actually wants for multichannel.
    fmt = "flt" if not stereo else "fltp"
    n = int(sample_rate * duration_s)
    t = np.arange(n) / sample_rate
    samples = (0.3 * np.sin(2 * np.pi * tone_hz * t)).astype(np.float32)
    if add_transient_at is not None:
        i = int(add_transient_at * sample_rate)
        samples[i:i + 200] += 0.8
    if stereo:
        samples = np.stack([samples, samples], axis=0)
    else:
        samples = samples.reshape(1, -1)
    chunk = 1152
    for start in range(0, n, chunk):
        sub = samples[:, start:start + chunk]
        if sub.shape[1] < chunk:
            sub = np.pad(sub, ((0, 0), (0, chunk - sub.shape[1])))
        frame = av.AudioFrame.from_ndarray(sub, format=fmt, layout=layout)
        frame.sample_rate = sample_rate
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


@pytest.fixture
def s():
    sub = srs.Substrate()
    a.seed_audio_grammar(sub)
    a.seed_native_codec_grammar(sub)
    return sub


@pytest.fixture
def mp3_with_transient():
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    _make_mp3(f.name, duration_s=2.0, tone_hz=440.0,
              add_transient_at=1.0, sample_rate=44100)
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def mp3_pure_tone():
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    _make_mp3(f.name, duration_s=1.0, tone_hz=440.0,
              add_transient_at=None, sample_rate=44100)
    yield f.name
    os.unlink(f.name)


# --- Header parse: free metadata the agent gets per-frame ---------


def test_native_parse_annotates_frame_with_mp3_header(s, mp3_pure_tone):
    """parse_native walks every Frame node and adds mp3_* attrs
    drawn directly from the bitstream header — version, layer,
    bitrate, sample rate, channel mode. None of this requires
    decoding samples."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    n_frames = a.parse_stream(s, cnid, snid)
    assert n_frames > 0
    n_granules = a.parse_native(s, cnid, snid)
    assert n_granules > 0
    # Each frame now carries mp3_* header attrs.
    sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
    attrs = s.node(sample_fid)["attrs"]
    assert attrs["mp3_version"] == "MPEG1"
    assert attrs["mp3_layer"] == "III"
    assert attrs["mp3_bitrate_kbps"] == 128
    assert attrs["mp3_sample_rate_hz"] == 44100
    assert attrs["mp3_channel_mode"] == "mono"


def test_native_parse_via_dsl_queries(s, mp3_pure_tone):
    """The agent can ask "what bitrate is this frame?" via the
    standard DSL — the mp3_* attrs are just graph data."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
    bitrate = s.evaluate(srs.Attr(srs.Lit(sample_fid), "mp3_bitrate_kbps"))
    layer = s.evaluate(srs.Attr(srs.Lit(sample_fid), "mp3_layer"))
    assert bitrate == 128
    assert layer == "III"


# --- Per-granule side info: the real "native listening" ----------


def test_parse_native_mints_granules(s, mp3_pure_tone):
    """For MPEG-1 Layer III mono, each frame has 2 granules. After
    parse_native, AudioFrame nodes have HAS_GRANULE edges to
    Mp3Granule nodes."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    frames = s.neighbours(snid, a.HAS_FRAME)
    # MPEG-1 Layer III mono: 2 granules × 1 channel = 2 per frame.
    sample_fid = next(iter(frames))
    granules = s.neighbours(sample_fid, a.HAS_GRANULE)
    assert len(granules) == 2
    # Each granule node has the expected attrs.
    g_attrs = s.node(granules[0])["attrs"]
    assert "block_type" in g_attrs
    assert g_attrs["block_type"] in ("long", "short", "mixed", "start", "end")
    assert "global_gain" in g_attrs
    assert "part2_3_length" in g_attrs


def test_pure_tone_yields_mostly_long_blocks(s, mp3_pure_tone):
    """A steady 440 Hz sine is the textbook case for LONG blocks
    (576-sample MDCT — fine frequency resolution, coarse time
    resolution). The encoder should pick long blocks throughout."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    all_block_types = []
    for fid in s.neighbours(snid, a.HAS_FRAME):
        for gid in s.neighbours(fid, a.HAS_GRANULE):
            all_block_types.append(s.node(gid)["attrs"]["block_type"])
    long_fraction = sum(1 for bt in all_block_types if bt == "long") / max(
        len(all_block_types), 1)
    # Steady tone — long blocks should dominate (>90%).
    assert long_fraction > 0.9, (
        f"steady tone should yield mostly long blocks; got {long_fraction:.2%}")


def test_transient_frames_detected_from_short_blocks(s, mp3_with_transient):
    """A transient burst should provoke the encoder to use SHORT or
    transition (start/end) blocks for the frames around it. The
    agent identifies these frames natively, no PCM decoding.

    transient_frames returns the AudioFrame NodeIDs whose granules
    contain non-long block types."""
    cnid = a.open_container(s, mp3_with_transient)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    transients = a.transient_frames(s, snid)
    # The encoder MUST pick non-long blocks somewhere in a 2s tone
    # with a single sharp transient — the whole point of MDCT
    # block-switching is to handle exactly this case (pre-echo
    # avoidance).
    assert len(transients) >= 1, (
        "expected the encoder to use short/mixed blocks around the "
        "transient; got none")
    # And the transient frames cluster near t=1.0s where we placed it.
    transient_times = sorted(
        float(s.node(f)["attrs"]["time_s"]) for f in transients)
    # At least one transient frame is within ±0.2s of where we placed
    # the impulse.
    assert any(abs(t - 1.0) < 0.2 for t in transient_times), (
        f"transient times {transient_times} should bracket t=1.0")


def test_tonal_frames_dominate_pure_tone(s, mp3_pure_tone):
    """In a pure tone, virtually every frame should be classified
    tonal (all granules long blocks)."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    all_frames_with_granules = [
        f for f in s.neighbours(snid, a.HAS_FRAME)
        if s.neighbours(f, a.HAS_GRANULE)
    ]
    tonal = a.tonal_frames(s, snid)
    # Most (>80%) of frames-with-granules are pure-long.
    fraction = len(tonal) / max(len(all_frames_with_granules), 1)
    assert fraction > 0.8, (
        f"pure tone should be {len(all_frames_with_granules)} tonal "
        f"frames; got {len(tonal)} (fraction={fraction:.2%})")


# --- Loudness + bitrate trajectories --------------------------------


def test_loudness_trajectory_tracks_global_gain(s, mp3_pure_tone):
    """global_gain is the encoder's per-granule loudness. Mean gain
    over time gives a coarse volume envelope without sample peaks."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    trajectory = a.loudness_trajectory(s, snid)
    assert len(trajectory) > 0
    # Time stamps strictly non-decreasing.
    times = [t for t, _ in trajectory]
    assert times == sorted(times)
    # global_gain values are non-negative integers in 0-255 range.
    for _, g in trajectory:
        assert 0 <= g <= 255


def test_bitrate_over_time_for_cbr_returns_constant(s, mp3_pure_tone):
    """CBR (constant bitrate) MP3 has the same bitrate per frame.
    Our test files are CBR at 128 kbps."""
    cnid = a.open_container(s, mp3_pure_tone)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    profile = a.bitrate_over_time(s, snid)
    assert len(profile) > 0
    bitrates = [br for _, br in profile]
    assert all(br == 128 for br in bitrates), (
        f"CBR file should have constant 128 kbps; got {set(bitrates)}")


# --- The headline: identify drum hits without decoding samples -----


def test_agent_finds_transients_without_decoding_any_samples(s, mp3_with_transient):
    """The complete native-listening demo: the agent identifies
    where in the audio the dynamic events are, **without ever
    decoding any audio samples** — purely from MDCT block-type
    decisions the encoder wrote into the bitstream.
    """
    cnid = a.open_container(s, mp3_with_transient)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    a.parse_native(s, cnid, snid)
    # The agent's DSL query: "What times have transients?"
    transients = a.transient_frames(s, snid)
    transient_times = [
        float(s.node(f)["attrs"]["time_s"]) for f in transients]
    print(f"\n  detected {len(transients)} transient frames at times "
          f"{[f'{t:.2f}s' for t in sorted(transient_times)]}")
    # We synthesised the file with a single transient at t=1.0s; the
    # encoder's response (short blocks) is detected at the agent's
    # graph level, samples never touched.
    assert len(transients) >= 1
    # NO AudioBuffer nodes should exist — we never called decode_frame.
    buffers = s.nodes(a.AUDIO_BUFFER)
    assert len(buffers) == 0, (
        f"native listening shouldn't materialise any samples; "
        f"found {len(buffers)} AudioBuffer nodes")


def test_stereo_mp3_yields_4_granules_per_frame(s):
    """MPEG-1 Layer III stereo: 2 granules × 2 channels = 4 per
    frame. Confirms the side-info parser handles the n_channels
    branch correctly."""
    f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    f.close()
    _make_mp3(f.name, duration_s=0.5, tone_hz=440.0, stereo=True)
    try:
        cnid = a.open_container(s, f.name)
        snid = a.add_stream(s, cnid)
        a.parse_stream(s, cnid, snid)
        a.parse_native(s, cnid, snid)
        # The encoder may pick stereo OR joint_stereo; either way
        # n_channels == 2 → 4 granules.
        sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
        granules = s.neighbours(sample_fid, a.HAS_GRANULE)
        assert len(granules) == 4, (
            f"stereo frame should have 4 granules (2 gr × 2 ch); "
            f"got {len(granules)}")
        # Each granule carries its (gr, ch) coordinates.
        coords = sorted(
            (int(s.node(g)["attrs"]["granule"]),
             int(s.node(g)["attrs"]["channel"]))
            for g in granules)
        assert coords == [(0, 0), (0, 1), (1, 0), (1, 1)]
    finally:
        os.unlink(f.name)
