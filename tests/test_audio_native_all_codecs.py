"""Phase 14c — native listening for Vorbis / Opus / AAC / FLAC.

Same pattern as MP3 (Phase 14b): parse the bitstream's structural
fields directly into graph nodes. The agent reads what the encoder
wrote — codec config, block sizes, channel coupling, subframe
prediction strategies — without decoding any audio samples.

Per-codec headline structural info:

* **Vorbis**: packet_type (audio/header) + mode_index (block-size
  hint: short/long).
* **Opus**: TOC byte → mode (SILK/Hybrid/CELT), bandwidth, frame
  size (ms), stereo flag, packing code.
* **AAC**: ADTS header (when present) or AudioSpecificConfig from
  codec extradata — profile (LC / Main / HE-AAC), sample rate,
  channel config.
* **FLAC**: frame header (block size, sample rate, channel mode —
  including mid/side coupling) + per-channel subframe type
  (CONSTANT / VERBATIM / FIXED-N / LPC-N), which encodes how
  predictable each channel was.
"""
from __future__ import annotations

import os
import tempfile

import av
import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")
a = pytest.importorskip("substrate_rs.audio")


def _encode_tone(path: str, codec: str, ext: str, *,
                 sample_rate: int, tone_hz: float = 440.0,
                 duration_s: float = 1.0, mono: bool = True,
                 chunk: int = 1024) -> str:
    """Encode a sine wave as a tiny file in `codec`."""
    container = av.open(path, mode="w")
    layout = "mono" if mono else "stereo"
    stream = container.add_stream(codec, rate=sample_rate)
    stream.codec_context.layout = layout
    n = int(sample_rate * duration_s)
    t = np.arange(n) / sample_rate
    samples = (0.3 * np.sin(2 * np.pi * tone_hz * t)).astype(np.float32)
    if not mono:
        samples = np.stack([samples, samples], axis=0)
    else:
        samples = samples.reshape(1, -1)
    fmt = "flt" if mono else "fltp"
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


# Per-codec fixtures — each runs `parse_stream` + `parse_native` and
# returns the substrate + the stream NodeID so the test body can
# query the resulting graph.


def _setup(s, path: str):
    cnid = a.open_container(s, path)
    snid = a.add_stream(s, cnid)
    a.parse_stream(s, cnid, snid)
    minted = a.parse_native(s, cnid, snid)
    return cnid, snid, minted


# --- Vorbis -----------------------------------------------------------


@pytest.fixture
def vorbis_path():
    f = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    f.close()
    _encode_tone(f.name, "libvorbis", "ogg", sample_rate=44100)
    yield f.name
    os.unlink(f.name)


def test_vorbis_native_parse_annotates_packet_type(s, vorbis_path):
    cnid, snid, minted = _setup(s, vorbis_path)
    assert minted > 0
    audio_frames = 0
    for fid in s.neighbours(snid, a.HAS_FRAME):
        ptype = s.node(fid)["attrs"].get("vorbis_packet_type")
        assert ptype in ("audio", "header")
        if ptype == "audio":
            audio_frames += 1
    assert audio_frames > 0


def test_vorbis_audio_packets_carry_block_size_hint(s, vorbis_path):
    cnid, snid, minted = _setup(s, vorbis_path)
    found = False
    for fid in s.neighbours(snid, a.HAS_FRAME):
        for info in s.neighbours(fid, a.HAS_CODEC_INFO):
            attrs = s.node(info)["attrs"]
            assert s.node(info)["type"] == a.VORBIS_PACKET_INFO
            assert attrs["packet_type"] == "audio"
            assert attrs["block_size_hint"] in ("short", "long")
            found = True
    assert found, "expected at least one VorbisPacketInfo node"


# --- Opus -------------------------------------------------------------


@pytest.fixture
def opus_path():
    # Opus only supports 8/12/16/24/48 kHz sample rates.
    f = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    f.close()
    _encode_tone(f.name, "libopus", "ogg", sample_rate=48000, chunk=960)
    yield f.name
    os.unlink(f.name)


def test_opus_toc_decodes_mode_bandwidth_frame_size(s, opus_path):
    cnid, snid, minted = _setup(s, opus_path)
    assert minted > 0
    first_audio = next(
        f for f in s.neighbours(snid, a.HAS_FRAME)
        if s.neighbours(f, a.HAS_CODEC_INFO))
    info = next(iter(s.neighbours(first_audio, a.HAS_CODEC_INFO)))
    attrs = s.node(info)["attrs"]
    # Sensible decoded fields.
    assert attrs["mode"] in ("SILK", "Hybrid", "CELT")
    assert attrs["bandwidth"] in ("NB", "MB", "WB", "SWB", "FB")
    assert attrs["frame_size_ms"] in (2.5, 5.0, 10.0, 20.0, 40.0, 60.0)
    # libopus encoding a pure sine at 48k mono → typically CELT,
    # full-band (FB), 20ms frames at default settings.
    # We don't pin the exact choice (encoder may pick differently
    # for different content) but we assert SOMETHING was decoded.
    assert 0 <= int(attrs["config"]) <= 31
    assert int(attrs["code"]) in (0, 1, 2, 3)


def test_opus_frame_attrs_visible_to_dsl(s, opus_path):
    cnid, snid, minted = _setup(s, opus_path)
    first_audio = next(
        f for f in s.neighbours(snid, a.HAS_FRAME)
        if s.neighbours(f, a.HAS_CODEC_INFO))
    # The agent's DSL can query the headline attrs directly.
    mode = s.evaluate(srs.Attr(srs.Lit(first_audio), "opus_mode"))
    bandwidth = s.evaluate(srs.Attr(srs.Lit(first_audio), "opus_bandwidth"))
    assert mode in ("SILK", "Hybrid", "CELT")
    assert bandwidth in ("NB", "MB", "WB", "SWB", "FB")


# --- AAC --------------------------------------------------------------


@pytest.fixture
def aac_path():
    f = tempfile.NamedTemporaryFile(suffix=".m4a", delete=False)
    f.close()
    _encode_tone(f.name, "aac", "m4a", sample_rate=44100)
    yield f.name
    os.unlink(f.name)


def test_aac_native_parse_extracts_profile_and_sample_rate(s, aac_path):
    cnid, snid, minted = _setup(s, aac_path)
    assert minted > 0
    info = next(iter(
        s.neighbours(
            next(iter(s.neighbours(snid, a.HAS_FRAME))), a.HAS_CODEC_INFO)))
    attrs = s.node(info)["attrs"]
    assert s.node(info)["type"] == a.AAC_FRAME_INFO
    # m4a → raw AAC framing (no ADTS).
    assert attrs.get("framing") in ("raw_AAC", "ADTS")
    # LC (Low Complexity) is the dominant choice for general AAC.
    assert attrs["profile"] in ("LC", "Main", "SSR", "LTP")
    assert attrs["sample_rate_hz"] == 44100


def test_aac_frame_carries_aac_attrs_for_agent_introspection(s, aac_path):
    cnid, snid, minted = _setup(s, aac_path)
    sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
    profile = s.evaluate(srs.Attr(srs.Lit(sample_fid), "aac_profile"))
    sample_rate = s.evaluate(srs.Attr(srs.Lit(sample_fid), "aac_sample_rate_hz"))
    framing = s.evaluate(srs.Attr(srs.Lit(sample_fid), "aac_framing"))
    assert profile in ("LC", "Main", "SSR", "LTP")
    assert sample_rate == 44100
    assert framing in ("raw_AAC", "ADTS")


# --- FLAC -------------------------------------------------------------


@pytest.fixture
def flac_path():
    f = tempfile.NamedTemporaryFile(suffix=".flac", delete=False)
    f.close()
    _encode_tone(f.name, "flac", "flac", sample_rate=44100, mono=False)
    yield f.name
    os.unlink(f.name)


def test_flac_frame_header_decodes_block_size_and_channels(s, flac_path):
    cnid, snid, minted = _setup(s, flac_path)
    assert minted > 0
    sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
    info = next(iter(s.neighbours(sample_fid, a.HAS_CODEC_INFO)))
    attrs = s.node(info)["attrs"]
    assert s.node(info)["type"] == a.FLAC_FRAME_INFO
    # Block size is a positive power-of-2-ish FLAC standard size.
    assert attrs["block_size"] > 0
    assert attrs["sample_rate_hz"] == 44100
    # Stereo FLAC: channels=2; channel_mode may be `independent` or
    # one of the coupling modes (left_side / right_side / mid_side).
    assert attrs["channels"] == 2
    assert attrs["channel_mode"] in (
        "independent", "left_side", "right_side", "mid_side")
    assert attrs["blocking_strategy"] in ("fixed", "variable")


def test_flac_frame_has_subframe_per_channel(s, flac_path):
    cnid, snid, minted = _setup(s, flac_path)
    sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
    info = next(iter(s.neighbours(sample_fid, a.HAS_CODEC_INFO)))
    subs = s.neighbours(info, a.HAS_SUBFRAME)
    # We mint at least one subframe (first channel). Full per-channel
    # parsing requires walking subframe bodies; the headline subframe
    # type is what's exposed.
    assert len(subs) >= 1
    sub_attrs = s.node(subs[0])["attrs"]
    assert sub_attrs["type"] in (
        "CONSTANT", "VERBATIM", "FIXED", "LPC", "RESERVED")
    assert sub_attrs["channel_index"] == 0


def test_flac_attrs_visible_to_dsl(s, flac_path):
    cnid, snid, minted = _setup(s, flac_path)
    sample_fid = next(iter(s.neighbours(snid, a.HAS_FRAME)))
    block_size = s.evaluate(srs.Attr(srs.Lit(sample_fid), "flac_block_size"))
    channels = s.evaluate(srs.Attr(srs.Lit(sample_fid), "flac_channels"))
    mode = s.evaluate(srs.Attr(srs.Lit(sample_fid), "flac_channel_mode"))
    assert block_size > 0
    assert channels == 2
    assert mode in ("independent", "left_side", "right_side", "mid_side")


# --- Cross-codec query: count by codec mode --------------------------


def test_codec_dispatch_handles_all_four_codecs_uniformly():
    """One Substrate, one parse_native call, four different codecs —
    each yields its own structural nodes, all introspectable via
    the same DSL."""
    specs = [
        ("libvorbis", "ogg", 44100, a.VORBIS_PACKET_INFO),
        ("libopus", "ogg", 48000, a.OPUS_PACKET_INFO),
        ("aac", "m4a", 44100, a.AAC_FRAME_INFO),
        ("flac", "flac", 44100, a.FLAC_FRAME_INFO),
    ]
    for codec, ext, fs, expected_type in specs:
        s = srs.Substrate()
        a.seed_audio_grammar(s)
        a.seed_native_codec_grammar(s)
        f = tempfile.NamedTemporaryFile(suffix="." + ext, delete=False)
        f.close()
        try:
            _encode_tone(f.name, codec, ext, sample_rate=fs,
                         chunk=960 if codec == "libopus" else 1024)
            cnid, snid, minted = _setup(s, f.name)
            assert minted > 0, f"{codec} produced no structural nodes"
            # At least one node of the expected codec-info type
            # exists in the graph.
            assert len(s.nodes(expected_type)) > 0, (
                f"{codec} should mint {expected_type} nodes")
            # And no audio samples were ever decoded.
            assert len(s.nodes(a.AUDIO_BUFFER)) == 0, (
                f"{codec}: native parse shouldn't materialise samples")
        finally:
            os.unlink(f.name)


def test_agent_can_query_codec_by_name_across_streams():
    """Agent introspection: 'tell me about every codec node in the
    graph, grouped by type'. Native parsing makes the codec a
    first-class graph object."""
    specs = [
        ("libvorbis", "ogg", 44100),
        ("libopus", "ogg", 48000),
        ("aac", "m4a", 44100),
        ("flac", "flac", 44100),
    ]
    s = srs.Substrate()
    a.seed_audio_grammar(s)
    a.seed_native_codec_grammar(s)
    paths = []
    try:
        for codec, ext, fs in specs:
            f = tempfile.NamedTemporaryFile(suffix="." + ext, delete=False)
            f.close()
            paths.append(f.name)
            _encode_tone(f.name, codec, ext, sample_rate=fs,
                         chunk=960 if codec == "libopus" else 1024)
            _setup(s, f.name)
        # Single substrate now holds four codecs' worth of structural
        # nodes. Walk the catalog.
        counts = {
            "VorbisPacketInfo": len(s.nodes(a.VORBIS_PACKET_INFO)),
            "OpusPacketInfo": len(s.nodes(a.OPUS_PACKET_INFO)),
            "AacFrameInfo": len(s.nodes(a.AAC_FRAME_INFO)),
            "FlacFrameInfo": len(s.nodes(a.FLAC_FRAME_INFO)),
        }
        for codec_type, n in counts.items():
            assert n > 0, f"no {codec_type} nodes found"
        print(f"\n  codec node counts in graph: {counts}")
    finally:
        for p in paths:
            if os.path.exists(p):
                os.unlink(p)
