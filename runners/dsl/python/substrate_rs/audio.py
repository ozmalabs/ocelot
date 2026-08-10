"""Audio as graph data — primitives + bitstream parsing.

Mirrors :mod:`substrate_rs.vision` (kernels as primitives) and
:mod:`substrate_rs.video` (format-parse the bitstream). Audio is
1-D where vision is 2-D; the substrate machinery is identical
otherwise.

Biology
-------
The cochlea is a literal frequency-domain analyser — the basilar
membrane acts as a mechanical filter bank. Each inner hair cell
fires in response to vibration in a narrow frequency band; this is
**tonotopic** organisation (Békésy 1960). The Gammatone filter
(Patterson 1976; Glasberg & Moore 1990) is the engineering analog
of one cochlear channel; a bank of them across frequency is the
substrate of biological pitch / formant / phoneme perception, just
as a Gabor bank is the substrate of biological orientation
perception.

So this module does for hearing what :mod:`substrate_rs.vision`
does for sight: lift the receptive fields out of opaque DSP code
and into graph data the agent can read / edit / compose.

Two halves
----------

**Primitives** — graph-resident audio data:

* :data:`AUDIO_BUFFER` — samples + rate + channels + dtype
* :data:`FILTER` — 1-D impulse response (audio's Kernel analog)
* Constructors: ``gammatone``, ``lowpass``, ``highpass``,
  ``bandpass``, ``mel_filterbank``, ``filter_from_array``
* Biology-shaped banks: ``cochlea`` (Gammatone × N at ERB-spaced
  centre frequencies — the A1 column equivalent)
* Operations: ``convolve_1d`` (apply Filter to Buffer), ``stft``
  (STFT → spectrogram Image — chains into the V1 cortex), and
  ``a1_responses`` (apply every band of a cochlea bank in parallel).

**Format parse** — bitstream of an audio container:

* :data:`AUDIO_CONTAINER` / :data:`AUDIO_STREAM` /
  :data:`AUDIO_FRAME` node types via PyAV.
* ``open_container`` / ``add_stream`` / ``parse_stream`` walk the
  bitstream into graph nodes (codec, sample rate, channels,
  per-frame size, pts) without decoding samples.
* ``decode_frame`` is the explicit "render this one frame to
  samples" path — produces an :data:`AUDIO_BUFFER` the agent can
  feed to its cochlear filter bank.

A spectrogram is just an Image
------------------------------
``stft`` returns an :class:`substrate_rs.vision.Image` node.
That's the bridge: any graph-resident vision capability — V1
Gabors, V2 corners, pooling, Hebbian learning — composes
seamlessly on top of audio. This is exactly how speech recognition
works: time-frequency images convolved with 2-D feature detectors.
The agent gets it for free because spectrograms ARE images in the
substrate.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Optional

import numpy as np

try:
    import av
    _HAS_AV = True
except ImportError:  # pragma: no cover
    av = None
    _HAS_AV = False

from . import Substrate as _PySubstrate


# --- Node + edge type constants -----------------------------------------

AUDIO_BUFFER = "AudioBuffer"
FILTER = "Filter"

AUDIO_CONTAINER = "AudioContainer"
AUDIO_STREAM = "AudioStream"
AUDIO_FRAME = "AudioFrame"

# Edge types (reuse vision's strings where semantics match — the
# agent's queries don't have to distinguish "this came from a vision
# kernel" vs "this came from a filter".)
HAS_STREAM = "has_stream"
HAS_FRAME = "has_frame"
FOLLOWS = "follows"
PRODUCED_BY = "produced_by"
FROM_INPUT = "from_input"


def _native(s):
    return s._inner if isinstance(s, _PySubstrate) else s


# --- Grammar seeding ----------------------------------------------------

def seed_audio_grammar(s, namespace: str | None = None) -> int:
    """Add productions for AudioBuffer / Filter / Container / Stream /
    Frame + relationship edges. Returns count added."""
    from . import NodePattern, Production
    inner = _native(s)

    def _t(name: str) -> str:
        if namespace is None or ":" in name:
            return name
        return f"{namespace}:{name}"

    prods = []

    def _perm(src_type, edge_type, tgt_type, prov):
        prods.append(Production(
            src=NodePattern(type=_t(src_type), var="src"),
            edge_type=edge_type,
            tgt=NodePattern(type=_t(tgt_type), var="tgt"),
            where=None, weight=None, provenance=prov,
        ))

    # Primitive provenance edges (mirror vision module).
    _perm(AUDIO_BUFFER, PRODUCED_BY, FILTER, "audio:buffer_produced_by_filter")
    _perm(AUDIO_BUFFER, FROM_INPUT, AUDIO_BUFFER, "audio:buffer_from_input")
    # Cross-modal STFT bridge: the spectrogram is an Image but its
    # `from_input` points at the AudioBuffer it was computed from.
    # Without this production Γ rejects the STFT provenance edge as
    # Type-1 (the vision grammar doesn't know about AudioBuffer).
    _perm("Image", FROM_INPUT, AUDIO_BUFFER, "audio:spectrogram_from_buffer")
    # Format-parse edges (mirror video module).
    _perm(AUDIO_CONTAINER, HAS_STREAM, AUDIO_STREAM, "audio:container_has_stream")
    _perm(AUDIO_STREAM, HAS_FRAME, AUDIO_FRAME, "audio:stream_has_frame")
    _perm(AUDIO_FRAME, FOLLOWS, AUDIO_FRAME, "audio:frame_follows_frame")

    for p in prods:
        inner.add_production(p.to_dict())
    return len(prods)


# --- AudioBuffer bridge: numpy ↔ graph node ----------------------------

def audio_from_array(s, samples: np.ndarray, sample_rate: int,
                     channels: int | None = None,
                     origin: str = "external") -> Any:
    """Create an AudioBuffer node carrying `samples`. Accepts shape
    (n,) for mono or (n, channels) for multichannel. Stores raw
    bytes in `samples` attr + rate / channels / dtype metadata.
    Returns the new NodeID.
    """
    inner = _native(s)
    if samples.ndim == 1:
        n = samples.shape[0]
        c = 1
    elif samples.ndim == 2:
        n, c = samples.shape
    else:
        raise ValueError(
            f"audio samples must be 1-D or 2-D; got shape {samples.shape}")
    if channels is not None:
        c = channels
    return inner.add_node(AUDIO_BUFFER, {
        "n_samples": int(n),
        "channels": int(c),
        "sample_rate": int(sample_rate),
        "dtype": str(samples.dtype),
        "duration_s": float(n) / float(sample_rate) if sample_rate > 0 else 0.0,
        "samples": samples.tobytes(),
        "origin": origin,
    })


def audio_to_array(s, buffer_nid) -> np.ndarray:
    """Reconstruct the numpy samples from a Buffer node."""
    inner = _native(s)
    a = inner.node(buffer_nid)["attrs"]
    arr = np.frombuffer(a["samples"], dtype=np.dtype(a["dtype"]))
    if int(a["channels"]) > 1:
        return arr.reshape(int(a["n_samples"]), int(a["channels"]))
    return arr


def audio_shape(s, buffer_nid) -> tuple[int, int, int]:
    """``(n_samples, channels, sample_rate)`` — cheap accessor without
    deserialising the sample bytes."""
    inner = _native(s)
    a = inner.node(buffer_nid)["attrs"]
    return int(a["n_samples"]), int(a["channels"]), int(a["sample_rate"])


# --- Filter bridge: numpy ↔ graph node ---------------------------------

def filter_from_array(s, name: str, weights: np.ndarray,
                      fs: int | None = None,
                      origin: str = "user_authored") -> Any:
    """Mint a Filter node from a 1-D impulse response. Stored as
    float32 bytes + length / fs (sample rate the filter was designed
    for) / name / origin. ``fs`` is metadata — the convolver
    doesn't enforce that filter and buffer rates match (but should
    in practice)."""
    if weights.ndim != 1:
        raise ValueError(f"filter weights must be 1-D, got {weights.shape}")
    w = weights.astype(np.float32, copy=False)
    inner = _native(s)
    return inner.add_node(FILTER, {
        "name": name,
        "length": int(len(w)),
        "dtype": "float32",
        "weights": w.tobytes(),
        "sample_rate": int(fs) if fs is not None else 0,
        "origin": origin,
    })


def filter_to_array(s, filter_nid) -> np.ndarray:
    """Reconstruct the float32 impulse response from a Filter node."""
    inner = _native(s)
    a = inner.node(filter_nid)["attrs"]
    arr = np.frombuffer(a["weights"], dtype=np.dtype(a["dtype"]))
    return arr.reshape(int(a["length"]))


def filter_describe(s, filter_nid) -> dict:
    """Cheap snapshot — name, length, fs, weight stats. For the
    agent's introspection."""
    inner = _native(s)
    a = inner.node(filter_nid)["attrs"]
    arr = np.frombuffer(a["weights"], dtype=np.dtype(a["dtype"]))
    return {
        "name": a["name"],
        "length": int(a["length"]),
        "sample_rate": int(a.get("sample_rate", 0)),
        "origin": a.get("origin", ""),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "energy": float((arr * arr).sum()),
    }


# --- Canonical filter constructors -------------------------------------

def gammatone(s, fc: float, fs: int = 22050, order: int = 4,
              duration: float = 0.05) -> Any:
    """One cochlear filter — a Gammatone (Patterson 1976; Glasberg
    & Moore 1990's ERB-aware variant).

        g(t) = a * t^(n-1) * exp(-2π·b·t) * cos(2π·fc·t)

    where ``b = ERB(fc) * 1.019`` and the impulse is zero before
    t=0. `fc` is centre frequency (Hz), `fs` is the design
    sample rate, `order` is the polynomial degree (4 is the
    biological default), `duration` is how long to truncate the
    impulse response in seconds.

    The filter sums to roughly unit energy after normalisation —
    convolution preserves overall loudness.
    """
    n = order
    erb = 24.7 * (4.37 * fc / 1000.0 + 1.0)   # Glasberg & Moore ERB
    b = erb * 1.019
    n_samples = int(round(duration * fs))
    t = np.arange(n_samples).astype(np.float64) / fs
    envelope = (t ** (n - 1)) * np.exp(-2.0 * math.pi * b * t)
    carrier = np.cos(2.0 * math.pi * fc * t)
    g = envelope * carrier
    # Normalise to unit L2 norm so the bank sums to consistent
    # energy across frequencies (otherwise high-freq filters have
    # tiny norms).
    norm = float(np.linalg.norm(g))
    if norm > 0:
        g = g / norm
    return filter_from_array(
        s, name=f"gammatone:fc={fc:.1f}Hz,order={order}",
        weights=g.astype(np.float32), fs=fs, origin="gammatone")


def _windowed_sinc(cutoff: float, fs: int, length: int) -> np.ndarray:
    """The numerator of every windowed-sinc filter — used by
    lowpass / highpass / bandpass below."""
    if length % 2 == 0:
        length += 1
    half = length // 2
    n = np.arange(-half, half + 1).astype(np.float64)
    nyquist = fs / 2.0
    fc_norm = cutoff / nyquist
    # sinc(0) = 1 by convention; numpy.sinc already does the
    # normalised sinc (sin(πx)/(πx)).
    sinc = np.sinc(fc_norm * n)
    # Hann window — minimal sidelobe leakage for a beginner filter.
    window = 0.5 + 0.5 * np.cos(2.0 * math.pi * n / length)
    return (sinc * window).astype(np.float64)


def lowpass(s, cutoff: float, fs: int = 22050, length: int = 65) -> Any:
    """Windowed-sinc lowpass at `cutoff` Hz. Length should be odd
    (forced odd internally) and reasonably long for a sharp
    transition band."""
    h = _windowed_sinc(cutoff, fs, length)
    h /= h.sum()
    return filter_from_array(
        s, name=f"lowpass:fc={cutoff:.1f}Hz",
        weights=h.astype(np.float32), fs=fs, origin="lowpass")


def highpass(s, cutoff: float, fs: int = 22050, length: int = 65) -> Any:
    """Spectral-inversion highpass: 1 − lowpass(cutoff)."""
    h = _windowed_sinc(cutoff, fs, length)
    h /= h.sum()
    centre = len(h) // 2
    inv = -h
    inv[centre] += 1.0
    return filter_from_array(
        s, name=f"highpass:fc={cutoff:.1f}Hz",
        weights=inv.astype(np.float32), fs=fs, origin="highpass")


def bandpass(s, low_hz: float, high_hz: float, fs: int = 22050,
             length: int = 65) -> Any:
    """Bandpass = lowpass(high) − lowpass(low)."""
    h_hi = _windowed_sinc(high_hz, fs, length)
    h_lo = _windowed_sinc(low_hz, fs, length)
    h_hi /= h_hi.sum()
    h_lo /= h_lo.sum()
    bp = h_hi - h_lo
    return filter_from_array(
        s, name=f"bandpass:{low_hz:.1f}-{high_hz:.1f}Hz",
        weights=bp.astype(np.float32), fs=fs, origin="bandpass")


# --- Biology-shaped banks ----------------------------------------------

def cochlea(s, n_bands: int = 32, fs: int = 22050,
            low_hz: float = 80.0, high_hz: float = 8000.0,
            order: int = 4, duration: float = 0.05) -> list:
    """A bank of Gammatone filters at ERB-spaced centre frequencies
    — the engineering analog of one cochlear nerve. Returns the
    list of Filter NodeIDs in ascending frequency.

    ERB spacing puts more filters at low frequencies (matching the
    biological hair-cell density gradient — fine pitch
    discrimination at low frequencies, broader bands above)."""
    # ERB-scale spacing: centre frequencies uniformly distributed on
    # the ERB scale (Glasberg & Moore 1990).
    def erb_inverse(e):
        return (10 ** (e / 21.4) - 1.0) / 0.00437  # Hz
    def erb_scale(f):
        return 21.4 * np.log10(0.00437 * f + 1.0)
    e_lo = erb_scale(low_hz)
    e_hi = erb_scale(high_hz)
    erbs = np.linspace(e_lo, e_hi, n_bands)
    fcs = [erb_inverse(e) for e in erbs]
    return [gammatone(s, fc=fc, fs=fs, order=order, duration=duration)
            for fc in fcs]


def mel_filterbank(s, n_filters: int = 40, fs: int = 22050,
                   low_hz: float = 80.0, high_hz: float = 8000.0,
                   length: int = 65) -> list:
    """A bank of bandpass filters spaced uniformly on the mel scale
    (Stevens 1937). The engineering shortcut for cochlear-like
    perception used by every speech-recognition system from
    Davis & Mermelstein (1980) onwards. Each filter is a triangular
    bandpass centred on its mel frequency.

    Returns the list of Filter NodeIDs in ascending frequency."""
    def hz_to_mel(f):
        return 1127.0 * np.log(1.0 + f / 700.0)
    def mel_to_hz(m):
        return 700.0 * (np.exp(m / 1127.0) - 1.0)
    mels = np.linspace(hz_to_mel(low_hz), hz_to_mel(high_hz), n_filters + 2)
    hz_pts = [mel_to_hz(m) for m in mels]
    out = []
    # Each filter is a bandpass between adjacent mel points.
    for i in range(n_filters):
        lo, hi = hz_pts[i], hz_pts[i + 2]
        out.append(bandpass(s, low_hz=lo, high_hz=hi, fs=fs, length=length))
    return out


# --- Operations: convolve, STFT, A1 responses ---------------------------

def convolve_1d(s, buffer_nid, filter_nid, mode: str = "same",
                origin: str | None = None,
                wire_provenance: bool = True) -> Any:
    """Apply `filter_nid` to `buffer_nid`; return a new AudioBuffer
    NodeID holding the filtered samples. Same provenance shape as
    vision's `convolve`: the output buffer points back to its source
    and filter via :data:`PRODUCED_BY` / :data:`FROM_INPUT` edges.

    `mode` is 'same' (output length = input length) or 'valid'
    (output shrinks by len(filter)-1).
    """
    inner = _native(s)
    samples = audio_to_array(s, buffer_nid).astype(np.float32)
    h = filter_to_array(s, filter_nid).astype(np.float32)
    buf_attrs = inner.node(buffer_nid)["attrs"]
    fs = int(buf_attrs["sample_rate"])
    channels = int(buf_attrs["channels"])
    if samples.ndim == 1:
        out = np.convolve(samples, h, mode=mode).astype(np.float32)
    else:
        # Per-channel 1-D convolution.
        chans = [np.convolve(samples[:, c], h, mode=mode).astype(np.float32)
                 for c in range(channels)]
        out = np.stack(chans, axis=1)
    if origin is None:
        f_name = inner.node(filter_nid)["attrs"].get("name", "filter")
        origin = f"convolve_1d({f_name})"
    out_nid = audio_from_array(s, out, sample_rate=fs,
                               channels=channels, origin=origin)
    if wire_provenance:
        inner.add_edge(out_nid, PRODUCED_BY, filter_nid)
        inner.add_edge(out_nid, FROM_INPUT, buffer_nid)
    return out_nid


def stft(s, buffer_nid, win_size: int = 512, hop_size: int = 256,
         origin: str | None = None) -> Any:
    """Short-time Fourier transform of an AudioBuffer. Returns an
    :data:`Image` node (from :mod:`substrate_rs.vision`) holding the
    magnitude spectrogram — frequency × time, float32.

    This is the load-bearing bridge: a spectrogram IS an image in
    the substrate. The agent's V1 cortex (Gabor banks, V2 corner
    detectors, Hebbian learning) all compose on top of audio
    spectrograms automatically. Same machinery, just turned 90°.
    """
    from . import vision as _vision
    samples = audio_to_array(s, buffer_nid).astype(np.float32)
    if samples.ndim > 1:
        # Mix to mono for simplicity — multichannel STFT is per-
        # channel but we keep the output as one image.
        samples = samples.mean(axis=1)
    window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(win_size) / win_size))
    n_frames = max(0, 1 + (len(samples) - win_size) // hop_size)
    n_bins = win_size // 2 + 1
    if n_frames <= 0:
        out = np.zeros((n_bins, 1), dtype=np.float32)
    else:
        out = np.zeros((n_bins, n_frames), dtype=np.float32)
        for t in range(n_frames):
            seg = samples[t * hop_size:t * hop_size + win_size] * window
            spectrum = np.fft.rfft(seg)
            out[:, t] = np.abs(spectrum).astype(np.float32)
    if origin is None:
        origin = f"stft(win={win_size},hop={hop_size})"
    img_nid = _vision.image_from_array(s, out, origin=origin)
    _native(s).add_edge(img_nid, FROM_INPUT, buffer_nid)
    return img_nid


def a1_responses(s, buffer_nid, bank: Iterable) -> list:
    """Apply each Filter in `bank` to `buffer_nid` in parallel.
    Models the parallel response of an A1 cortical column to a
    single auditory input — same shape as :func:`vision.v1_responses`.
    Returns the list of response AudioBuffer NodeIDs."""
    return [convolve_1d(s, buffer_nid, f) for f in bank]


# --- Format parse: audio container / stream / frame --------------------
#
# Mirrors substrate_rs.video. Same lazy posture: parse the bitstream
# into graph nodes (codec metadata, per-frame size + pts) without
# decoding samples; decode_frame is the explicit "render this frame
# to samples" step.

class _AudioContainerHandle:
    """Process-local registry entry (the av.Container can't live on
    a graph attr)."""
    __slots__ = ("path", "av_container", "stream_index", "frame_index_seq",
                 "_pkt_cache")

    def __init__(self, path: str, av_container, stream_index: int):
        self.path = path
        self.av_container = av_container
        self.stream_index = stream_index
        self.frame_index_seq = 0
        # demux-once packet-bytes cache (frame_index -> bytes); built lazily by
        # _packet_bytes_for. Fixes the O(n^2) re-seek-per-frame in native parse.
        self._pkt_cache = None


_OPEN_AUDIO_CONTAINERS: dict[int, _AudioContainerHandle] = {}


def open_container(s, path: str) -> Any:
    """Open an audio file via PyAV; mint an AudioContainer node
    carrying its metadata. Returns the Container NodeID."""
    if not _HAS_AV:
        raise RuntimeError("PyAV is required for substrate_rs.audio format parse")
    container = av.open(path)
    inner = _native(s)
    nid = inner.add_node(AUDIO_CONTAINER, {
        "path": path,
        "format": container.format.long_name or container.format.name,
        "duration_s": float(container.duration / 1_000_000) if container.duration else 0.0,
        "n_streams": len(container.streams),
        "size_bytes": container.size if hasattr(container, "size") else 0,
    })
    _OPEN_AUDIO_CONTAINERS[nid.value] = _AudioContainerHandle(
        path=path, av_container=container, stream_index=-1)
    return nid


def reopen_container(s, container_nid) -> None:
    """Re-attach the PyAV handle after persistence load."""
    if not _HAS_AV:
        raise RuntimeError("PyAV is required for substrate_rs.audio format parse")
    inner = _native(s)
    path = inner.node(container_nid)["attrs"]["path"]
    container = av.open(path)
    _OPEN_AUDIO_CONTAINERS[container_nid.value] = _AudioContainerHandle(
        path=path, av_container=container, stream_index=-1)


def close_container(container_nid) -> None:
    h = _OPEN_AUDIO_CONTAINERS.pop(container_nid.value, None)
    if h is not None:
        h.av_container.close()


def _handle_for(container_nid) -> _AudioContainerHandle:
    h = _OPEN_AUDIO_CONTAINERS.get(container_nid.value)
    if h is None:
        raise RuntimeError(
            "audio container handle not open — call reopen_container "
            "after a persistence load, or open_container for a fresh start")
    return h


def add_stream(s, container_nid, stream_index: int | None = None) -> Any:
    """Mint an AudioStream node for the audio stream at
    `stream_index` (or the first audio stream if None). Returns
    the stream NodeID."""
    handle = _handle_for(container_nid)
    if stream_index is None:
        # First audio stream in the container.
        for i, stream in enumerate(handle.av_container.streams):
            if stream.type == "audio":
                stream_index = i
                break
        if stream_index is None:
            raise ValueError(f"no audio stream in {handle.path}")
    stream = handle.av_container.streams[stream_index]
    if stream.type != "audio":
        raise ValueError(
            f"stream {stream_index} is type={stream.type!r}, not 'audio'")
    handle.stream_index = stream_index
    inner = _native(s)
    # Audio streams don't have a video-style average_rate (it's a
    # per-frame video concept). Sample rate comes from the codec ctx.
    ctx = stream.codec_context
    sid = inner.add_node(AUDIO_STREAM, {
        "stream_index": int(stream_index),
        "codec": ctx.name,
        "sample_rate": int(ctx.sample_rate) if ctx.sample_rate else 0,
        "channels": int(ctx.channels) if hasattr(ctx, "channels") else 0,
        "format": str(ctx.format.name) if ctx.format else "",
        "n_frames": int(stream.frames) if stream.frames else 0,
        "time_base_num": stream.time_base.numerator if stream.time_base else 1,
        "time_base_den": stream.time_base.denominator if stream.time_base else 1,
    })
    inner.add_edge(container_nid, HAS_STREAM, sid)
    return sid


def parse_stream(s, container_nid, stream_nid, *,
                 frame_limit: int | None = None) -> int:
    """Walk the audio bitstream. For each packet mint an AudioFrame
    node with header info (pts, dts, coded_size, time_s). Does NOT
    decode samples — call :func:`decode_frame` for that.

    Returns the total number of AudioFrame nodes minted.
    """
    handle = _handle_for(container_nid)
    inner = _native(s)
    stream_attrs = inner.node(stream_nid)["attrs"]
    stream_index = int(stream_attrs["stream_index"])
    if handle.stream_index != stream_index:
        raise ValueError(
            f"container handle is on stream {handle.stream_index}; "
            f"requested {stream_index}")
    tb_num = float(stream_attrs.get("time_base_num", 1))
    tb_den = float(stream_attrs.get("time_base_den", 1))
    tb = tb_num / tb_den if tb_den else 0.0
    av_stream = handle.av_container.streams[stream_index]
    minted = 0
    prev_nid: Optional[Any] = None
    for packet in handle.av_container.demux(av_stream):
        if packet.size == 0:
            continue
        # We only mint per PACKET (not per decoded frame) — the
        # packet IS the bitstream-level frame for audio.
        fi = handle.frame_index_seq
        handle.frame_index_seq += 1
        pts = packet.pts if packet.pts is not None else 0
        dts = packet.dts if packet.dts is not None else 0
        nid = inner.add_node(AUDIO_FRAME, {
            "frame_index": int(fi),
            "pts": int(pts),
            "dts": int(dts),
            "coded_size": int(packet.size),
            "time_s": float(pts) * tb if pts is not None else 0.0,
            "duration": int(packet.duration) if packet.duration else 0,
        })
        inner.add_edge(stream_nid, HAS_FRAME, nid)
        if prev_nid is not None:
            inner.add_edge(nid, FOLLOWS, prev_nid)
        prev_nid = nid
        minted += 1
        if frame_limit is not None and minted >= frame_limit:
            return minted
    return minted


def decode_frame(s, frame_nid) -> Any:
    """Materialise the samples of `frame_nid` as an AudioBuffer
    node. The lazy render path — like decode_frame in the video
    module, the agent invokes this only when it actually wants
    samples to feed into its cochlear filterbank."""
    inner = _native(s)
    a = inner.node(frame_nid)["attrs"]
    target_idx = int(a["frame_index"])
    # Walk back to the container.
    stream_nid = None
    for src in inner.in_neighbours(frame_nid, HAS_FRAME):
        stream_nid = src
        break
    if stream_nid is None:
        raise RuntimeError(f"audio frame #{frame_nid.value} has no parent stream")
    container_nid = None
    for src in inner.in_neighbours(stream_nid, HAS_STREAM):
        container_nid = src
        break
    if container_nid is None:
        raise RuntimeError(f"audio stream #{stream_nid.value} has no parent container")

    handle = _handle_for(container_nid)
    handle.av_container.seek(0)
    av_stream = handle.av_container.streams[handle.stream_index]
    seen = 0
    for packet in handle.av_container.demux(av_stream):
        if packet.size == 0:
            continue
        if seen >= target_idx:
            # Decode this packet to one or more audio frames; flatten
            # into a single sample array.
            chunks = []
            for frame in packet.decode():
                arr = frame.to_ndarray()
                # PyAV gives planar (channels, samples) or packed
                # (samples,) depending on format — normalise to
                # (samples, channels).
                if arr.ndim == 2 and arr.shape[0] < arr.shape[1]:
                    arr = arr.T
                chunks.append(arr.astype(np.float32))
            samples = np.concatenate(chunks, axis=0) if chunks else np.zeros(
                (0,), dtype=np.float32)
            # MP3 / AAC priming packets at the start of a stream often
            # decode to ZERO samples — they're codec init, not audio.
            # Walk forward to the next non-empty packet so the caller
            # gets real samples.
            if samples.size == 0:
                seen += 1
                continue
            stream_a = inner.node(stream_nid)["attrs"]
            fs = int(stream_a.get("sample_rate", 0))
            channels = int(stream_a.get("channels", 1))
            return audio_from_array(
                s, samples, sample_rate=fs,
                channels=channels if samples.ndim > 1 else 1,
                origin=f"decoded:frame={target_idx}")
        seen += 1
    raise RuntimeError(f"could not seek to audio frame {target_idx}")


# --- Native codec parsing: read the bitstream as the cochlea does -----
#
# Audio codecs (MP3, AAC, Vorbis, Opus) are themselves frequency-
# domain representations — the encoder ran a filterbank / MDCT and
# wrote the per-band coefficients. Decoding to PCM and then running
# an STFT throws that work away.
#
# So we "listen natively": parse the codec's frame structure into
# graph nodes directly. For MP3 we extract per-frame headers + per-
# granule side info — block_type (long/short = tone/transient),
# global_gain (loudness), bit allocation. The agent walks these to
# spot drum hits, loud passages, mode switches — all without ever
# decoding a single sample.
#
# Biology: the cochlea's basilar membrane IS a mechanical filter
# bank. The MP3 bitstream's MDCT subbands are the closest digital
# analog. Decoding to PCM, then re-doing an STFT, is the cochlea
# decoding back to air pressure and then re-listening — pointless.

# Per-codec lookup tables.
# MPEG-1 Layer III bitrate table (kbps).
_MP3_BITRATES_V1L3 = [None, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192,
                     224, 256, 320, None]
# MPEG-2/2.5 Layer III bitrate table.
_MP3_BITRATES_V2L3 = [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128,
                     144, 160, None]
_MP3_SAMPLERATES = {
    "MPEG1":   {0: 44100, 1: 48000, 2: 32000},
    "MPEG2":   {0: 22050, 1: 24000, 2: 16000},
    "MPEG2.5": {0: 11025, 1: 12000, 2: 8000},
}
_MP3_MODES = {0: "stereo", 1: "joint_stereo", 2: "dual_channel", 3: "mono"}
_MP3_BLOCK_TYPES = {0: "long", 1: "start", 2: "short", 3: "end"}


MP3_GRANULE = "Mp3Granule"
VORBIS_PACKET_INFO = "VorbisPacketInfo"
OPUS_PACKET_INFO = "OpusPacketInfo"
AAC_FRAME_INFO = "AacFrameInfo"
FLAC_FRAME_INFO = "FlacFrameInfo"
FLAC_SUBFRAME = "FlacSubframe"

HAS_GRANULE = "has_granule"
HAS_CODEC_INFO = "has_codec_info"
HAS_SUBFRAME = "has_subframe"


def seed_native_codec_grammar(s, namespace: str | None = None) -> int:
    """Add productions for codec-internal node types (Mp3Granule,
    VorbisPacketInfo, OpusPacketInfo, AacFrameInfo, FlacFrameInfo,
    FlacSubframe) + the relationship edges. Call alongside
    :func:`seed_audio_grammar` before any native-parse function."""
    from . import NodePattern, Production
    inner = _native(s)

    def _t(name: str) -> str:
        if namespace is None or ":" in name:
            return name
        return f"{namespace}:{name}"

    pairs = [
        (AUDIO_FRAME, HAS_GRANULE, MP3_GRANULE, "audio:frame_has_mp3_granule"),
        (AUDIO_FRAME, HAS_CODEC_INFO, VORBIS_PACKET_INFO,
            "audio:frame_has_vorbis_info"),
        (AUDIO_FRAME, HAS_CODEC_INFO, OPUS_PACKET_INFO,
            "audio:frame_has_opus_info"),
        (AUDIO_FRAME, HAS_CODEC_INFO, AAC_FRAME_INFO,
            "audio:frame_has_aac_info"),
        (AUDIO_FRAME, HAS_CODEC_INFO, FLAC_FRAME_INFO,
            "audio:frame_has_flac_info"),
        (FLAC_FRAME_INFO, HAS_SUBFRAME, FLAC_SUBFRAME,
            "audio:flac_frame_has_subframe"),
    ]
    for src_t, et, tgt_t, prov in pairs:
        inner.add_production(Production(
            src=NodePattern(type=_t(src_t), var="src"),
            edge_type=et,
            tgt=NodePattern(type=_t(tgt_t), var="tgt"),
            where=None, weight=None,
            provenance=prov,
        ).to_dict())
    return len(pairs)


class _BitReader:
    """Minimal MSB-first bit reader over a byte string. MP3 side info
    is bit-packed; pure-Python parser is plenty fast for the ~30-byte
    side-info regions we read per frame."""
    __slots__ = ("data", "bit_pos")

    def __init__(self, data: bytes):
        self.data = data
        self.bit_pos = 0

    def read(self, n: int) -> int:
        val = 0
        for _ in range(n):
            byte_idx = self.bit_pos >> 3
            bit_idx = 7 - (self.bit_pos & 7)
            if byte_idx >= len(self.data):
                return 0
            val = (val << 1) | ((self.data[byte_idx] >> bit_idx) & 1)
            self.bit_pos += 1
        return val


def _parse_mp3_header(data: bytes) -> Optional[dict]:
    """Parse a 32-bit MP3 frame header. Returns None if the sync word
    is wrong or fields are reserved/invalid."""
    if len(data) < 4:
        return None
    h = int.from_bytes(data[:4], "big")
    if (h & 0xFFE00000) != 0xFFE00000:
        return None
    version_bits = (h >> 19) & 0x3
    layer_bits = (h >> 17) & 0x3
    protection = (h >> 16) & 0x1
    bitrate_idx = (h >> 12) & 0xF
    sr_idx = (h >> 10) & 0x3
    padding = (h >> 9) & 0x1
    channel_mode = (h >> 6) & 0x3
    mode_extension = (h >> 4) & 0x3

    version = {3: "MPEG1", 2: "MPEG2", 0: "MPEG2.5"}.get(version_bits)
    layer = {3: "I", 2: "II", 1: "III"}.get(layer_bits)
    if version is None or layer is None:
        return None
    # Bitrate table picks vary by version + layer; only L III tables
    # implemented here.
    if layer != "III":
        # Other layers parseable too; we focus on the dominant case.
        bitrate = None
    elif version == "MPEG1":
        bitrate = _MP3_BITRATES_V1L3[bitrate_idx]
    else:
        bitrate = _MP3_BITRATES_V2L3[bitrate_idx]
    sample_rate = _MP3_SAMPLERATES.get(version, {}).get(sr_idx)
    if sample_rate is None:
        return None
    return {
        "version": version,
        "layer": layer,
        "bitrate_kbps": bitrate if bitrate is not None else 0,
        "sample_rate_hz": sample_rate,
        "padding": bool(padding),
        "channel_mode": _MP3_MODES.get(channel_mode, "unknown"),
        "mode_extension": int(mode_extension),
        "has_crc": protection == 0,
    }


def _parse_mp3_side_info(data: bytes, mono: bool, version: str) -> Optional[list[dict]]:
    """Parse per-granule side info. Returns a list of dicts, one per
    (granule, channel). Only MPEG-1 Layer III layout implemented;
    others return None.

    Side info layout — MPEG-1 Layer III:
      9 bits main_data_begin
      5 bits private_bits (mono) OR 3 bits (stereo)
      4 × n_channels scfsi
      THEN 2 granules × n_channels:
        12 bits part2_3_length
         9 bits big_values
         8 bits global_gain
         4 bits scalefac_compress
         1 bit  window_switching_flag
         if WSF=1:
           2 bits block_type (0=reserved, 1=start, 2=short, 3=end)
           1 bit mixed_block_flag
           2 × 5 bits table_select
           3 × 3 bits subblock_gain
         else:
           block_type = 0 (long)
           3 × 5 bits table_select
           4 bits region0_count
           3 bits region1_count
         1 bit preflag
         1 bit scalefac_scale
         1 bit count1table_select
    """
    if version != "MPEG1":
        # MPEG-2/2.5 side info is half the size and different layout.
        # Out of scope for the first cut.
        return None
    n_ch = 1 if mono else 2
    expected_size = 17 if mono else 32
    if len(data) < expected_size:
        return None
    br = _BitReader(data)
    br.read(9)                                          # main_data_begin
    br.read(5 if mono else 3)                           # private_bits
    for _ in range(n_ch):
        br.read(4)                                      # scfsi
    main_data_begin = None
    granules: list[dict] = []
    # Re-read main_data_begin (we already consumed it above; track for
    # the caller — Phase 16b's frame rewriter needs it).
    # Actually re-build the bit reader to keep main_data_begin too.
    br2 = _BitReader(data)
    main_data_begin = br2.read(9)
    # Skip the rest of the header bits we already consumed.
    skip = 5 if mono else 3
    br2.read(skip)
    for _ in range(n_ch):
        br2.read(4)
    for gr in range(2):
        for ch in range(n_ch):
            part2_3 = br2.read(12)
            big_values = br2.read(9)
            global_gain = br2.read(8)
            scalefac_compress = br2.read(4)
            wsf = br2.read(1)
            table_selects: list[int] = []
            subblock_gains: list[int] = []
            if wsf:
                bt = br2.read(2)
                mixed = br2.read(1)
                for _ in range(2):
                    table_selects.append(br2.read(5))
                # When WSF=1 there's no region2 table_select on the wire
                # — fill with 0 so the decoder has a consistent shape.
                table_selects.append(0)
                for _ in range(3):
                    subblock_gains.append(br2.read(3))
                region0 = region1 = -1
            else:
                bt = 0
                mixed = 0
                for _ in range(3):
                    table_selects.append(br2.read(5))
                region0 = br2.read(4)
                region1 = br2.read(3)
            preflag = br2.read(1)
            scalefac_scale = br2.read(1)
            count1ts = br2.read(1)
            granules.append({
                "granule": gr,
                "channel": ch,
                "block_type_code": int(bt),
                "block_type": _MP3_BLOCK_TYPES.get(int(bt), "unknown"),
                "mixed_block": bool(mixed),
                "part2_3_length": int(part2_3),
                "big_values": int(big_values),
                "global_gain": int(global_gain),
                "scalefac_compress": int(scalefac_compress),
                "region0_count": int(region0),
                "region1_count": int(region1),
                "preflag": bool(preflag),
                "scalefac_scale": bool(scalefac_scale),
                "count1table_select": bool(count1ts),
                # Phase 16b additions — needed for coefficient decode.
                "table_select_0": int(table_selects[0]),
                "table_select_1": int(table_selects[1]),
                "table_select_2": int(table_selects[2]),
                "subblock_gain_0": int(subblock_gains[0]) if subblock_gains else 0,
                "subblock_gain_1": int(subblock_gains[1]) if subblock_gains else 0,
                "subblock_gain_2": int(subblock_gains[2]) if subblock_gains else 0,
                "main_data_begin": int(main_data_begin),
            })
    return granules


def parse_native_mp3(s, frame_nid) -> int:
    """Parse the MP3 bitstream behind a single AudioFrame node:
    extract header attrs (bitrate, mode, version, layer) and mint
    Mp3Granule child nodes carrying block_type / global_gain / bit
    allocation per granule per channel.

    Returns the number of granule nodes minted (0 if the frame isn't
    parseable MPEG-1 Layer III, e.g. MPEG-2 or a non-MP3 frame).

    The bytes for this packet are obtained via the container handle.
    The caller must have :func:`open_container` / :func:`add_stream`
    / :func:`parse_stream` already done. This function ADDS to the
    Frame node — it doesn't rewalk the bitstream from scratch.
    """
    inner = _native(s)
    # Walk back to container + stream to fetch the packet bytes.
    stream_nid = None
    for src in inner.in_neighbours(frame_nid, HAS_FRAME):
        stream_nid = src
        break
    if stream_nid is None:
        return 0
    container_nid = None
    for src in inner.in_neighbours(stream_nid, HAS_STREAM):
        container_nid = src
        break
    if container_nid is None:
        return 0
    handle = _handle_for(container_nid)
    frame_a = inner.node(frame_nid)["attrs"]
    target_idx = int(frame_a["frame_index"])

    # Re-seek and walk to the target packet to get its bytes.
    handle.av_container.seek(0)
    av_stream = handle.av_container.streams[handle.stream_index]
    seen = 0
    packet_bytes = None
    for packet in handle.av_container.demux(av_stream):
        if packet.size == 0:
            continue
        if seen == target_idx:
            packet_bytes = bytes(packet)
            break
        seen += 1
    if packet_bytes is None:
        return 0

    header = _parse_mp3_header(packet_bytes)
    if header is None:
        return 0
    # Annotate the Frame with codec-level attrs the agent can query
    # via the standard DSL.
    for k, v in header.items():
        inner.set_attr(frame_nid, f"mp3_{k}", v)

    # Side info starts after the 4-byte header + 2 bytes CRC (if any).
    side_start = 4 + (2 if header["has_crc"] else 0)
    mono = header["channel_mode"] == "mono"
    granule_data = _parse_mp3_side_info(
        packet_bytes[side_start:], mono=mono, version=header["version"])
    if granule_data is None:
        return 0
    # Mint Mp3Granule nodes wired to this Frame.
    for g in granule_data:
        gnid = inner.add_node(MP3_GRANULE, g)
        inner.add_edge(frame_nid, HAS_GRANULE, gnid)
    return len(granule_data)


def parse_native(s, container_nid, stream_nid) -> int:
    """Run the codec-specific native parser across every Frame node
    in the graph. Dispatches by the stream's codec attr — currently
    MP3 (granules), Vorbis (mode), Opus (TOC config), AAC (extradata
    + per-packet size), FLAC (frame + subframe headers).

    Returns total structural nodes minted (Mp3Granule /
    VorbisPacketInfo / OpusPacketInfo / AacFrameInfo / FlacFrameInfo
    + FlacSubframe).
    """
    inner = _native(s)
    codec = str(inner.node(stream_nid)["attrs"].get("codec", ""))
    if codec.startswith("mp3"):
        parser = parse_native_mp3
    elif codec == "vorbis":
        parser = parse_native_vorbis
    elif codec == "opus":
        parser = parse_native_opus
    elif codec == "aac":
        parser = parse_native_aac
    elif codec == "flac":
        parser = parse_native_flac
    else:
        return 0
    total = 0
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        total += parser(s, fid)
    return total


# --- Helper: fetch raw packet bytes for a Frame node ------------------

def _packet_bytes_for(s, frame_nid) -> tuple[Any, bytes] | None:
    """Walk back from frame_nid to its container, re-seek, and pull
    the raw packet bytes. Returns ``(stream_nid, bytes)`` or None
    if the frame can't be located.

    Used by every codec-specific parser — same shape as the MP3
    parser's lookup but extracted as a helper for the four new
    codecs."""
    inner = _native(s)
    stream_nid = None
    for src in inner.in_neighbours(frame_nid, HAS_FRAME):
        stream_nid = src
        break
    if stream_nid is None:
        return None
    container_nid = None
    for src in inner.in_neighbours(stream_nid, HAS_STREAM):
        container_nid = src
        break
    if container_nid is None:
        return None
    handle = _handle_for(container_nid)
    target_idx = int(inner.node(frame_nid)["attrs"]["frame_index"])
    # Build the packet-bytes cache ONCE (demux the whole stream a single time),
    # then index it. The previous code re-seeked to 0 and re-demuxed the entire
    # stream FOR EVERY FRAME — O(n^2) over tens of thousands of packets, which
    # the agent's value-for-compute assessment flagged as 83% of pipeline time.
    if handle._pkt_cache is None:
        cache: list[bytes] = []
        handle.av_container.seek(0)
        av_stream = handle.av_container.streams[handle.stream_index]
        for packet in handle.av_container.demux(av_stream):
            if packet.size == 0:
                continue
            cache.append(bytes(packet))
        handle._pkt_cache = cache
    cache = handle._pkt_cache
    if 0 <= target_idx < len(cache):
        return stream_nid, cache[target_idx]
    return None


# --- Vorbis -----------------------------------------------------------

def _parse_vorbis_audio_packet(data: bytes) -> Optional[dict]:
    """Vorbis audio packet starts with:
      bit 0: packet_type (0 for audio packet, 1 for header)
      next k bits: mode_number (k = ilog(n_modes - 1))

    Without parsing the setup-header packet, we don't know n_modes,
    but the most common case is 2 modes (long / short block) so
    k=1. We extract bit 0 (audio flag) + bit 1 (most likely mode).

    Returns dict with packet_type ("audio"/"header"), mode_index (0
    or 1 for the 2-mode common case), or None if the packet is
    empty.
    """
    if len(data) < 1:
        return None
    first = data[0]
    packet_type = first & 0x1
    mode_index = (first >> 1) & 0x1
    return {
        "packet_type": "audio" if packet_type == 0 else "header",
        # mode_index is heuristic: most Vorbis files use a 2-mode
        # setup (long + short blocks). Mode 0 is conventionally the
        # short block in libvorbis output; mode 1 the long block.
        "mode_index": int(mode_index),
        "block_size_hint": "short" if mode_index == 0 else "long",
    }


def parse_native_vorbis(s, frame_nid) -> int:
    """Parse a Vorbis audio packet — extract packet type + mode
    index. Mints one VorbisPacketInfo node per audio packet (header
    packets get no child). Returns 0 or 1."""
    inner = _native(s)
    fetched = _packet_bytes_for(s, frame_nid)
    if fetched is None:
        return 0
    _, data = fetched
    info = _parse_vorbis_audio_packet(data)
    if info is None:
        return 0
    # Annotate the Frame node itself with the packet type.
    inner.set_attr(frame_nid, "vorbis_packet_type", info["packet_type"])
    if info["packet_type"] != "audio":
        return 0
    info_nid = inner.add_node(VORBIS_PACKET_INFO, info)
    inner.add_edge(frame_nid, HAS_CODEC_INFO, info_nid)
    return 1


# --- Opus -------------------------------------------------------------

# Per RFC 6716 §3.1 — the TOC byte's 5-bit config field defines
# (mode, bandwidth, frame_size_ms). 32 entries total.
_OPUS_CONFIG_TABLE: list[tuple[str, str, float]] = [
    # config 0-11: SILK
    ("SILK", "NB",  10.0), ("SILK", "NB",  20.0), ("SILK", "NB",  40.0), ("SILK", "NB",  60.0),
    ("SILK", "MB",  10.0), ("SILK", "MB",  20.0), ("SILK", "MB",  40.0), ("SILK", "MB",  60.0),
    ("SILK", "WB",  10.0), ("SILK", "WB",  20.0), ("SILK", "WB",  40.0), ("SILK", "WB",  60.0),
    # config 12-15: Hybrid
    ("Hybrid", "SWB", 10.0), ("Hybrid", "SWB", 20.0),
    ("Hybrid", "FB",  10.0), ("Hybrid", "FB",  20.0),
    # config 16-31: CELT
    ("CELT", "NB",   2.5), ("CELT", "NB",   5.0), ("CELT", "NB",  10.0), ("CELT", "NB",  20.0),
    ("CELT", "WB",   2.5), ("CELT", "WB",   5.0), ("CELT", "WB",  10.0), ("CELT", "WB",  20.0),
    ("CELT", "SWB",  2.5), ("CELT", "SWB",  5.0), ("CELT", "SWB", 10.0), ("CELT", "SWB", 20.0),
    ("CELT", "FB",   2.5), ("CELT", "FB",   5.0), ("CELT", "FB",  10.0), ("CELT", "FB",  20.0),
]


def _parse_opus_toc(data: bytes) -> Optional[dict]:
    """Opus TOC byte (RFC 6716 §3.1):
      bits 7-3: config (0-31) → (mode, bandwidth, frame_size_ms)
      bit 2:    c (0=mono, 1=stereo)
      bits 1-0: code (0-3, frame packing)

    Returns a dict with the decoded fields, or None on empty input.
    """
    if len(data) < 1:
        return None
    toc = data[0]
    config = (toc >> 3) & 0x1F
    c = (toc >> 2) & 0x1
    code = toc & 0x3
    mode, bandwidth, frame_ms = _OPUS_CONFIG_TABLE[config]
    return {
        "config": int(config),
        "mode": mode,                                         # SILK / Hybrid / CELT
        "bandwidth": bandwidth,                               # NB / MB / WB / SWB / FB
        "frame_size_ms": float(frame_ms),
        "stereo": bool(c),
        "code": int(code),                                    # 0=single, 1=2 frames, 2=2 frames variable, 3=arbitrary
    }


def parse_native_opus(s, frame_nid) -> int:
    """Parse the Opus TOC byte. Annotates the Frame with high-level
    attrs (mode/bandwidth/stereo) AND mints an OpusPacketInfo node
    with the full decoded TOC. Returns 1."""
    inner = _native(s)
    fetched = _packet_bytes_for(s, frame_nid)
    if fetched is None:
        return 0
    _, data = fetched
    info = _parse_opus_toc(data)
    if info is None:
        return 0
    inner.set_attr(frame_nid, "opus_mode", info["mode"])
    inner.set_attr(frame_nid, "opus_bandwidth", info["bandwidth"])
    inner.set_attr(frame_nid, "opus_frame_size_ms", info["frame_size_ms"])
    inner.set_attr(frame_nid, "opus_stereo", info["stereo"])
    info_nid = inner.add_node(OPUS_PACKET_INFO, info)
    inner.add_edge(frame_nid, HAS_CODEC_INFO, info_nid)
    return 1


def annotate_opus_modes(s, container_nid, stream_nid) -> int:
    """CHEAP per-frame opus hint for utterance detection: set opus_mode /
    bandwidth on each AudioFrame from its 1-byte TOC, minting NO OpusPacketInfo
    nodes. `detect_utterances` only reads `opus_mode` off the frame; the full
    OpusPacketInfo node is disposable-tier (value_tier('OpusPacketInfo') ==
    'disposable' — the agent's own verdict), so the speech path uses this
    instead of paying parse_native to mint structure it immediately forgets.
    Returns the number of frames annotated."""
    inner = _native(s)
    codec = str(inner.node(stream_nid)["attrs"].get("codec", ""))
    if codec != "opus":
        return 0
    n = 0
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        fetched = _packet_bytes_for(s, fid)   # O(1) after the one-pass cache
        if fetched is None:
            continue
        info = _parse_opus_toc(fetched[1])
        if info is None:
            continue
        inner.set_attr(fid, "opus_mode", info["mode"])
        inner.set_attr(fid, "opus_bandwidth", info["bandwidth"])
        inner.set_attr(fid, "opus_frame_size_ms", info["frame_size_ms"])
        inner.set_attr(fid, "opus_stereo", info["stereo"])
        n += 1
    return n


# --- AAC --------------------------------------------------------------

# Sampling-frequency table for AAC (ISO/IEC 14496-3 §1.6.3.4).
_AAC_SR_TABLE = [
    96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050,
    16000, 12000, 11025, 8000, 7350, 0, 0, 0,
]
_AAC_PROFILES = {0: "Main", 1: "LC", 2: "SSR", 3: "LTP"}


def _parse_aac_adts(data: bytes) -> Optional[dict]:
    """ADTS frame header (7 bytes, no CRC). Returns None if the sync
    isn't present — m4a-wrapped AAC has raw frames with no ADTS
    header, so callers fall back to whatever PyAV already exposed.
    """
    if len(data) < 7:
        return None
    # ADTS sync is 0xFFF in the top 12 bits.
    if data[0] != 0xFF or (data[1] & 0xF0) != 0xF0:
        return None
    h = int.from_bytes(data[:7], "big")
    # Bit layout from offset 0:
    #   12 sync, 1 ID, 2 layer, 1 protection_absent, 2 profile,
    #   4 sampling_freq_index, 1 private, 3 channel_config,
    #   1 original/copy, 1 home, 1 copyright_id_bit,
    #   1 copyright_id_start, 13 frame_length, 11 buffer_fullness,
    #   2 number_raw_data_blocks
    # Position from MSB of h (56-bit value):
    mpeg_version = "MPEG-4" if ((h >> 43) & 0x1) == 0 else "MPEG-2"
    protection_absent = bool((h >> 40) & 0x1)
    profile_id = (h >> 38) & 0x3
    sr_idx = (h >> 34) & 0xF
    channel_config = (h >> 30) & 0x7
    frame_length = (h >> 13) & 0x1FFF
    return {
        "framing": "ADTS",
        "mpeg_version": mpeg_version,
        "has_crc": not protection_absent,
        "profile": _AAC_PROFILES.get(profile_id, "unknown"),
        "sample_rate_hz": _AAC_SR_TABLE[sr_idx],
        "channel_config": int(channel_config),
        "frame_length": int(frame_length),
    }


def _parse_aac_audio_specific_config(extradata: bytes) -> Optional[dict]:
    """The AudioSpecificConfig (ASC) lives in the codec extradata
    for raw-AAC streams (m4a, mp4). 2 bytes minimum:
      5 bits: audioObjectType (profile + 1)
      4 bits: samplingFrequencyIndex
      4 bits: channelConfiguration
      ... (extension bits)
    """
    if len(extradata) < 2:
        return None
    br = _BitReader(extradata)
    aot = br.read(5)
    sr_idx = br.read(4)
    ch = br.read(4)
    # audioObjectType N corresponds to profile N-1 in the ADTS profile field.
    profile_id = max(0, aot - 1)
    return {
        "framing": "raw_AAC",
        "audio_object_type": int(aot),
        "profile": _AAC_PROFILES.get(profile_id, f"AOT{aot}"),
        "sample_rate_hz": _AAC_SR_TABLE[sr_idx] if sr_idx < 16 else 0,
        "channel_config": int(ch),
    }


def parse_native_aac(s, frame_nid) -> int:
    """Parse an AAC packet. ADTS-framed AAC (`.aac`, `.adts`) yields
    a full ADTS header parse. Raw AAC in m4a/mp4 yields the stream-
    level AudioSpecificConfig (parsed once from extradata) plus the
    packet's coded size as the per-frame structural attr.

    Mints an AacFrameInfo node per frame and returns 1."""
    inner = _native(s)
    fetched = _packet_bytes_for(s, frame_nid)
    if fetched is None:
        return 0
    stream_nid, data = fetched
    # Try ADTS first.
    info = _parse_aac_adts(data)
    if info is None:
        # Raw AAC — look at the stream's extradata (set by libav at
        # stream open, retrievable via PyAV's codec context).
        info = _aac_extradata_info(s, stream_nid)
        if info is None:
            return 0
        # Per-frame: just the packet size.
        info = {**info, "coded_size": len(data)}
    info_nid = inner.add_node(AAC_FRAME_INFO, info)
    inner.add_edge(frame_nid, HAS_CODEC_INFO, info_nid)
    # Annotate the parent Frame with the headline attrs.
    inner.set_attr(frame_nid, "aac_profile", info.get("profile", ""))
    inner.set_attr(frame_nid, "aac_sample_rate_hz", info.get("sample_rate_hz", 0))
    inner.set_attr(frame_nid, "aac_framing", info.get("framing", ""))
    return 1


def _aac_extradata_info(s, stream_nid) -> Optional[dict]:
    """Pull the AudioSpecificConfig from the live PyAV stream's
    codec extradata. Reused across all raw-AAC frames in the same
    stream (the ASC is stream-level, not per-frame)."""
    inner = _native(s)
    container_nid = None
    for src in inner.in_neighbours(stream_nid, HAS_STREAM):
        container_nid = src
        break
    if container_nid is None:
        return None
    handle = _handle_for(container_nid)
    av_stream = handle.av_container.streams[handle.stream_index]
    extradata = av_stream.codec_context.extradata
    if not extradata:
        return None
    return _parse_aac_audio_specific_config(bytes(extradata))


# --- FLAC -------------------------------------------------------------

_FLAC_BLOCK_SIZE_LOOKUP = {
    1: 192, 2: 576, 3: 1152, 4: 2304, 5: 4608,
    8: 256, 9: 512, 10: 1024, 11: 2048, 12: 4096, 13: 8192, 14: 16384, 15: 32768,
}
_FLAC_SAMPLE_RATE_LOOKUP = {
    1: 88200, 2: 176400, 3: 192000,
    4: 8000, 5: 16000, 6: 22050, 7: 24000, 8: 32000, 9: 44100, 10: 48000, 11: 96000,
}


def _parse_flac_frame_header(data: bytes) -> Optional[dict]:
    """FLAC frame header (variable length, min 4 bytes):
      14 bits: sync (0x3FFE)
       1 bit:  reserved
       1 bit:  blocking_strategy (0=fixed, 1=variable)
       4 bits: block_size_code
       4 bits: sample_rate_code
       4 bits: channel_assignment
       3 bits: bit_depth_code
       1 bit:  reserved
       8-56 bits: UTF-8 coded frame/sample number
      [optional 8 or 16 bits extended block size]
      [optional 8 or 16 bits extended sample rate]
       8 bits: CRC-8

    Returns a dict with the parsed structural info, including
    `header_length` so the caller can locate the start of subframes.
    """
    if len(data) < 4:
        return None
    if data[0] != 0xFF or (data[1] & 0xFC) != 0xF8:
        return None
    br = _BitReader(data)
    br.read(14)
    br.read(1)
    blocking = br.read(1)
    bs_code = br.read(4)
    sr_code = br.read(4)
    ch_asgn = br.read(4)
    bd_code = br.read(3)
    br.read(1)  # reserved

    # Skip the UTF-8 coded sample/frame number. Length is 1-7 bytes;
    # the first byte's top bits tell us how many follow.
    n = br.bit_pos // 8
    if n >= len(data):
        return None
    first = data[n]
    if first < 0x80:
        utf8_len = 1
    elif first < 0xC0:
        utf8_len = 1
    elif first < 0xE0:
        utf8_len = 2
    elif first < 0xF0:
        utf8_len = 3
    elif first < 0xF8:
        utf8_len = 4
    elif first < 0xFC:
        utf8_len = 5
    elif first < 0xFE:
        utf8_len = 6
    else:
        utf8_len = 7
    br.bit_pos += utf8_len * 8

    # Extended block size in bytes if block_size_code is 6/7.
    if bs_code == 6:
        ext_bs = br.read(8)
        block_size = ext_bs + 1
    elif bs_code == 7:
        ext_bs = br.read(16)
        block_size = ext_bs + 1
    else:
        block_size = _FLAC_BLOCK_SIZE_LOOKUP.get(bs_code, 0)

    # Extended sample rate.
    if sr_code == 12:
        ext_sr = br.read(8)
        sample_rate = ext_sr * 1000
    elif sr_code == 13:
        ext_sr = br.read(16)
        sample_rate = ext_sr
    elif sr_code == 14:
        ext_sr = br.read(16)
        sample_rate = ext_sr * 10
    else:
        sample_rate = _FLAC_SAMPLE_RATE_LOOKUP.get(sr_code, 0)

    # CRC-8.
    br.read(8)
    header_length_bits = br.bit_pos

    # Channel assignment 0-7 = independent channels (1-8 channels);
    # 8 = left+side, 9 = right+side, 10 = mid+side stereo.
    if ch_asgn <= 7:
        channels = ch_asgn + 1
        channel_mode = "independent"
    elif ch_asgn == 8:
        channels = 2
        channel_mode = "left_side"
    elif ch_asgn == 9:
        channels = 2
        channel_mode = "right_side"
    elif ch_asgn == 10:
        channels = 2
        channel_mode = "mid_side"
    else:
        channels = 0
        channel_mode = "unknown"

    return {
        "blocking_strategy": "variable" if blocking else "fixed",
        "block_size": int(block_size),
        "sample_rate_hz": int(sample_rate),
        "channels": int(channels),
        "channel_mode": channel_mode,
        "bit_depth_code": int(bd_code),
        "header_length_bits": int(header_length_bits),
    }


def _parse_flac_subframe_header(data: bytes, start_bit: int) -> Optional[dict]:
    """One FLAC subframe header (1+ bits, ignoring wasted-bits unary):
       1 bit:  zero (must be 0)
       6 bits: subframe_type
       1 bit:  wasted_bits_flag
       [unary-coded wasted bits count]

    Subframe type encoding:
      000000      → CONSTANT (silence / DC)
      000001      → VERBATIM (raw samples, incompressible)
      001xxx      → reserved
      01xxxx      → reserved
      001000-001100 → FIXED, prediction order 0-4
      1xxxxx      → LPC, prediction order = xxxxx + 1 (1-32)
    """
    if start_bit // 8 >= len(data):
        return None
    br = _BitReader(data)
    br.bit_pos = start_bit
    zero = br.read(1)
    if zero != 0:
        return None
    type_code = br.read(6)
    wasted_flag = br.read(1)
    if wasted_flag:
        # Unary count of leading zeros then a 1. Skip — for parse
        # depth this is enough to know subframe type.
        # Counting wasted bits up to 32 max.
        for _ in range(64):
            bit = br.read(1)
            if bit == 1:
                break

    # Decode subframe type.
    if type_code == 0:
        kind, order = "CONSTANT", 0
    elif type_code == 1:
        kind, order = "VERBATIM", 0
    elif 8 <= type_code <= 12:
        kind, order = "FIXED", type_code - 8
    elif type_code >= 32:
        kind, order = "LPC", (type_code - 31)
    else:
        kind, order = "RESERVED", -1
    return {
        "type_code": int(type_code),
        "type": kind,
        "prediction_order": int(order),
        "wasted_bits": bool(wasted_flag),
        "end_bit": br.bit_pos,
    }


def parse_native_flac(s, frame_nid) -> int:
    """Parse a FLAC frame: frame header + per-channel subframe
    headers. Mints a FlacFrameInfo node carrying block size /
    sample rate / channel assignment + one FlacSubframe per
    channel carrying its prediction strategy.

    Returns 1 (for the FlacFrameInfo) + N subframes.
    """
    inner = _native(s)
    fetched = _packet_bytes_for(s, frame_nid)
    if fetched is None:
        return 0
    _, data = fetched
    hdr = _parse_flac_frame_header(data)
    if hdr is None:
        return 0
    info_nid = inner.add_node(FLAC_FRAME_INFO, hdr)
    inner.add_edge(frame_nid, HAS_CODEC_INFO, info_nid)
    inner.set_attr(frame_nid, "flac_block_size", hdr["block_size"])
    inner.set_attr(frame_nid, "flac_channels", hdr["channels"])
    inner.set_attr(frame_nid, "flac_channel_mode", hdr["channel_mode"])
    inner.set_attr(frame_nid, "flac_blocking_strategy", hdr["blocking_strategy"])

    # Parse the subframe headers. Each subframe starts immediately
    # after the frame header (which is byte-aligned by the trailing
    # CRC-8) — the first subframe begins at header_length_bits.
    # Subframes are bit-packed back-to-back; we stop after `channels`
    # subframes OR if we hit padding/CRC at the end of the frame.
    minted = 1
    cur_bit = hdr["header_length_bits"]
    for ch in range(hdr["channels"]):
        sub = _parse_flac_subframe_header(data, cur_bit)
        if sub is None:
            break
        sub_attrs = dict(sub)
        sub_attrs["channel_index"] = ch
        sub_attrs.pop("end_bit", None)
        sub_nid = inner.add_node(FLAC_SUBFRAME, sub_attrs)
        inner.add_edge(info_nid, HAS_SUBFRAME, sub_nid)
        minted += 1
        # We CAN'T cleanly advance past the subframe body without
        # decoding the residual/Rice-coded data. The subframe HEADER
        # parse is what gives us the agent-useful info (type + order);
        # stop reading subframes after we've inspected each channel's
        # header position. Approximate: assume subframe header is
        # 8 bits long; the actual body follows. This is a simplification
        # — for accurate per-channel parsing the body length must be
        # known. We'll terminate the loop now to avoid mis-parsing.
        break
    return minted


# --- Native-listening query helpers ------------------------------------

def transient_frames(s, stream_nid) -> list:
    """AudioFrame NodeIDs whose granules contain ANY short or mixed
    blocks. These are the encoder's "transient" calls — drum hits,
    plosives, sharp attacks. The agent identifies the dynamic
    moments without ever decoding samples."""
    inner = _native(s)
    out = []
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        for gid in inner.neighbours(fid, HAS_GRANULE):
            bt = inner.node(gid)["attrs"].get("block_type")
            if bt == "short" or bt == "mixed" or inner.node(gid)["attrs"].get("mixed_block"):
                out.append(fid)
                break
    return out


def tonal_frames(s, stream_nid) -> list:
    """AudioFrame NodeIDs where ALL granules are long blocks — pure
    tonal content (sustained pitches, steady tones, vowels). The
    complement of `transient_frames` for granule-having frames."""
    inner = _native(s)
    out = []
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        grans = inner.neighbours(fid, HAS_GRANULE)
        if not grans:
            continue
        if all(inner.node(g)["attrs"].get("block_type") == "long" for g in grans):
            out.append(fid)
    return out


def loudness_trajectory(s, stream_nid) -> list[tuple[float, float]]:
    """Mean global_gain per frame, plotted over time. Returns a list
    of ``(time_s, mean_gain)``. global_gain is the encoder's per-
    granule overall loudness (in dB-like units); tracking it gives
    the agent the volume envelope of the audio without any sample-
    level peak detection."""
    inner = _native(s)
    pts = []
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        a = inner.node(fid)["attrs"]
        t = float(a.get("time_s", 0.0))
        gains = []
        for g in inner.neighbours(fid, HAS_GRANULE):
            gains.append(float(inner.node(g)["attrs"].get("global_gain", 0)))
        if gains:
            pts.append((t, sum(gains) / len(gains)))
    pts.sort()
    return pts


def bitrate_over_time(s, stream_nid) -> list[tuple[float, int]]:
    """Per-frame bitrate read directly from MP3 headers. For VBR
    (variable bitrate) audio this shows the encoder's complexity
    estimate per frame — high bitrate = "this part is hard to
    compress" = more information density."""
    inner = _native(s)
    pts = []
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        a = inner.node(fid)["attrs"]
        t = float(a.get("time_s", 0.0))
        br = int(a.get("mp3_bitrate_kbps", 0))
        if br > 0:
            pts.append((t, br))
    pts.sort()
    return pts


# --- Query helpers ---------------------------------------------------

def total_duration_s(s, stream_nid) -> float:
    """Sum frame durations across the parsed stream — how much audio
    does the agent have in its graph?"""
    inner = _native(s)
    tb_num = float(inner.node(stream_nid)["attrs"].get("time_base_num", 1))
    tb_den = float(inner.node(stream_nid)["attrs"].get("time_base_den", 1))
    tb = tb_num / tb_den if tb_den else 0.0
    total = 0.0
    for f in inner.neighbours(stream_nid, HAS_FRAME):
        total += float(inner.node(f)["attrs"].get("duration", 0)) * tb
    return total


def bitrate_profile(s, stream_nid, n_buckets: int = 50) -> list[float]:
    """Bucket frame coded sizes into ``n_buckets`` over time — the
    agent's cheap snapshot of "how busy is the bitstream over time".
    For VBR (variable-bitrate) audio, peaks correlate with complex
    content (transients, polyphony). Returns one float per bucket
    (mean bytes/frame in that bucket)."""
    inner = _native(s)
    frames = inner.neighbours(stream_nid, HAS_FRAME)
    if not frames:
        return [0.0] * n_buckets
    times = []
    sizes = []
    for f in frames:
        a = inner.node(f)["attrs"]
        times.append(float(a.get("time_s", 0.0)))
        sizes.append(int(a.get("coded_size", 0)))
    t_min, t_max = min(times), max(times)
    span = max(t_max - t_min, 1e-9)
    buckets = [[] for _ in range(n_buckets)]
    for t, sz in zip(times, sizes):
        b = min(n_buckets - 1, int((t - t_min) / span * n_buckets))
        buckets[b].append(sz)
    return [float(np.mean(b)) if b else 0.0 for b in buckets]


__all__ = [
    "AUDIO_BUFFER", "FILTER", "AUDIO_CONTAINER", "AUDIO_STREAM", "AUDIO_FRAME",
    "MP3_GRANULE", "VORBIS_PACKET_INFO", "OPUS_PACKET_INFO",
    "AAC_FRAME_INFO", "FLAC_FRAME_INFO", "FLAC_SUBFRAME",
    "HAS_GRANULE", "HAS_CODEC_INFO", "HAS_SUBFRAME",
    "HAS_STREAM", "HAS_FRAME", "FOLLOWS", "PRODUCED_BY", "FROM_INPUT",
    "seed_audio_grammar", "seed_native_codec_grammar",
    "audio_from_array", "audio_to_array", "audio_shape",
    "filter_from_array", "filter_to_array", "filter_describe",
    "gammatone", "lowpass", "highpass", "bandpass",
    "cochlea", "mel_filterbank",
    "convolve_1d", "stft", "a1_responses",
    "open_container", "reopen_container", "close_container",
    "add_stream", "parse_stream", "decode_frame",
    "parse_native",
    "parse_native_mp3", "parse_native_vorbis", "parse_native_opus",
    "parse_native_aac", "parse_native_flac", "annotate_opus_modes",
    "transient_frames", "tonal_frames",
    "loudness_trajectory", "bitrate_over_time",
    "total_duration_s", "bitrate_profile",
]
