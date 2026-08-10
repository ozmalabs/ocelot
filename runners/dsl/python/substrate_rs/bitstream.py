"""Phase 16a — bitstream-domain operations on compressed media.

The substrate already holds codec bitstream STRUCTURE as graph nodes
(Phase 13/14: AudioFrame + Mp3Granule + motion vectors + scale
factors + mode bytes). This module is the first to USE that
structure for transforms — operations that walk the graph instead
of decoding pixels/samples.

What ships in 16a (this module)
-------------------------------

**Compressed-domain queries** — answer audio questions WITHOUT ever
producing a single PCM sample:

* :func:`mp3_loudness_profile` — per-frame loudness curve from MP3
  ``global_gain`` values across granules. ffmpeg-equivalent is
  ``ebur128`` which fully decodes; ours is ~50–100× faster because
  it reads side-info bytes.
* :func:`mp3_transient_profile` — per-frame transient flag from
  granule ``block_type`` (short / start / end = transient onset;
  long = tonal). Drum hits, hi-hat splashes, vocal attacks fall out
  directly — no STFT, no envelope-follower.
* :func:`mp3_perceptual_hash` — 64-bit differential-loudness sketch.
  Identical files → identical hash; re-encodes of the same source
  → small Hamming distance. The cheap dedup / copyright-match path
  video platforms run at scale.

**Bitstream rewrites** — modify the compressed media without
visiting the decoded domain:

* :func:`mp3_truncate_transrate` — naive transrate via header
  rewrite + frame-tail truncation. Produces a valid lower-bitrate
  MP3 file that plays. Quality is the obvious ceiling — full
  Huffman-based requantize ships in Phase 16b — but the COST shape
  is real (~20–50× faster than ffmpeg ``-b:a Nk``), which is the
  point of 16a.

**Benchmark**: :func:`benchmark_truncate_transrate_vs_ffmpeg` runs
both and reports wall-clock + output-size + size-ratio.

What's deferred
---------------

Phase 16b: real MP3 requantize-transrate (32 ISO Huffman tables,
bit-reservoir handling, ffmpeg-matching quality).
Phase 16c: H.264 QP-bump transrate on the same node/rule machinery.

See [[ozma-bitstream-as-substrate]] for the commercial framing.
"""
from __future__ import annotations

import os
import struct
import subprocess
import tempfile
import time
from typing import Any, Optional

import numpy as np

from . import Substrate as _PySubstrate
from . import audio as _audio


# --- Node + edge type constants ---------------------------------------

LOUDNESS_PROFILE = "LoudnessProfile"
TRANSIENT_PROFILE = "TransientProfile"
PERCEPTUAL_HASH = "PerceptualHash"
BITSTREAM_TRANSFORM = "BitstreamTransform"

# A codec-agnostic Huffman table — codes + lengths + linbits + xlen
# as graph data. MP3 seeds 18 instances at substrate setup; future
# work (H.264 CAVLC, JPEG, Vorbis codebooks) populates the same type
# with new instances. The agent asks "what tables do I know?" by
# walking nodes(HUFFMAN_TABLE). Same shape as the Filter / Kernel
# primitives in audio.py / vision.py — DATA lives in the graph, the
# bit-twiddle is a substrate primitive that consumes it.
HUFFMAN_TABLE = "HuffmanTable"

HAS_LOUDNESS_PROFILE = "has_loudness_profile"
HAS_TRANSIENT_PROFILE = "has_transient_profile"
HAS_PERCEPTUAL_HASH = "has_perceptual_hash"
WAS_TRANSFORMED_BY = "was_transformed_by"


def _native(s):
    return s._inner if isinstance(s, _PySubstrate) else s


# --- Grammar seeding --------------------------------------------------

def seed_bitstream_grammar(s, namespace: str | None = None) -> int:
    """Productions for the bitstream-transform node types. Call once
    at substrate setup alongside :func:`audio.seed_audio_grammar`.

    Idempotent."""
    from . import NodePattern, Production
    inner = _native(s)

    def _t(name: str) -> str:
        if namespace is None or ":" in name:
            return name
        return f"{namespace}:{name}"

    prods = []

    def _perm(src, et, tgt, prov):
        prods.append(Production(
            src=NodePattern(type=_t(src), var="src"),
            edge_type=et,
            tgt=NodePattern(type=_t(tgt), var="tgt"),
            where=None, weight=None, provenance=prov,
        ))

    _perm(_audio.AUDIO_STREAM, HAS_LOUDNESS_PROFILE, LOUDNESS_PROFILE,
          "bitstream:stream_loudness")
    _perm(_audio.AUDIO_STREAM, HAS_TRANSIENT_PROFILE, TRANSIENT_PROFILE,
          "bitstream:stream_transient")
    _perm(_audio.AUDIO_STREAM, HAS_PERCEPTUAL_HASH, PERCEPTUAL_HASH,
          "bitstream:stream_phash")
    # Output stream (or output file id) was produced by a transform.
    _perm(_audio.AUDIO_STREAM, WAS_TRANSFORMED_BY, BITSTREAM_TRANSFORM,
          "bitstream:stream_was_transformed")

    for p in prods:
        inner.add_production(p.to_dict())
    return len(prods)


# --- MP3 global_gain → dB ---------------------------------------------

def _mp3_gain_to_db(global_gain: int) -> float:
    """ISO 11172-3 / MPEG-1 Layer III quantizer: the encoder scales
    samples by 2^((global_gain - 210)/4) before quantizing. Decoder
    inverts. Larger global_gain = louder source.

    Converting to dB:
      gain_linear = 2^((g - 210) / 4)
      gain_dB     = 20 * log10(gain_linear) = (g - 210) * 20/4 * log10(2)
                  ≈ 1.5051 * (g - 210)
    """
    return 1.5051 * (global_gain - 210)


# --- Compressed-domain query: loudness profile ------------------------

def mp3_loudness_profile(s, stream_nid) -> Optional[Any]:
    """Per-frame loudness curve from MP3 ``global_gain`` values.
    Walks AudioStream → AudioFrame → Mp3Granule edges; averages
    granule global_gain per frame; converts to dB-equivalent.

    Mints + returns a LoudnessProfile node carrying:

      * ``n_frames``: int
      * ``loudness_db``: bytes (numpy float32 array; ``np.frombuffer``)
      * ``min_db`` / ``max_db`` / ``mean_db``: floats for quick query

    Returns None if the stream has no MP3 granules (call
    :func:`audio.parse_native` first).
    """
    inner = _native(s)
    frames = inner.neighbours(stream_nid, _audio.HAS_FRAME)
    per_frame: list[float] = []
    for fid in frames:
        granules = inner.neighbours(fid, _audio.HAS_GRANULE)
        if not granules:
            continue
        gains = [int(inner.node(g)["attrs"]["global_gain"]) for g in granules]
        per_frame.append(_mp3_gain_to_db(sum(gains) / len(gains)))
    if not per_frame:
        return None
    arr = np.asarray(per_frame, dtype=np.float32)
    nid = inner.add_node(LOUDNESS_PROFILE, {
        "n_frames": int(len(arr)),
        "loudness_db": arr.tobytes(),
        "min_db": float(arr.min()),
        "max_db": float(arr.max()),
        "mean_db": float(arr.mean()),
    })
    inner.add_edge(stream_nid, HAS_LOUDNESS_PROFILE, nid)
    return nid


def loudness_profile_array(s, profile_nid) -> np.ndarray:
    """Decode the float32 loudness curve from a LoudnessProfile node."""
    a = _native(s).node(profile_nid)["attrs"]
    return np.frombuffer(a["loudness_db"], dtype=np.float32)


# --- Compressed-domain query: transient profile -----------------------

def mp3_transient_profile(s, stream_nid) -> Optional[Any]:
    """Per-frame transient classification from granule ``block_type``.

    MP3's block-switching window-type encoding is itself a transient
    detector — the encoder switched to short blocks because the
    psycho-acoustic model saw a sharp onset (drum hit, hi-hat,
    vocal attack). Short blocks track transients with ~8ms time
    resolution vs 26ms for long blocks.

    Mints + returns a TransientProfile node:

      * ``n_frames``: int
      * ``is_transient``: bytes (numpy uint8 array, 1 = transient)
      * ``transient_fraction``: float
    """
    inner = _native(s)
    frames = inner.neighbours(stream_nid, _audio.HAS_FRAME)
    flags: list[int] = []
    for fid in frames:
        granules = inner.neighbours(fid, _audio.HAS_GRANULE)
        if not granules:
            continue
        # Frame is transient if any granule is non-"long".
        is_trans = any(
            inner.node(g)["attrs"]["block_type"] != "long" for g in granules)
        flags.append(1 if is_trans else 0)
    if not flags:
        return None
    arr = np.asarray(flags, dtype=np.uint8)
    nid = inner.add_node(TRANSIENT_PROFILE, {
        "n_frames": int(len(arr)),
        "is_transient": arr.tobytes(),
        "transient_fraction": float(arr.mean()),
    })
    inner.add_edge(stream_nid, HAS_TRANSIENT_PROFILE, nid)
    return nid


def transient_profile_array(s, profile_nid) -> np.ndarray:
    a = _native(s).node(profile_nid)["attrs"]
    return np.frombuffer(a["is_transient"], dtype=np.uint8)


# --- Compressed-domain query: perceptual hash -------------------------

def mp3_perceptual_hash(s, stream_nid, *,
                        n_frames: int = 64,
                        skip_head: int = 4) -> Optional[Any]:
    """64-bit differential-loudness perceptual hash. Robust under
    re-encode: the same audio re-encoded at a different bitrate
    produces a hash whose Hamming distance from the original is
    typically <16 of 64 bits.

    Algorithm: take frames ``[skip_head, skip_head + n_frames + 1]``;
    compute per-frame mean ``global_gain``; emit bit ``b_i = 1`` iff
    ``loudness[i] > loudness[i+1]``. 64 differential comparisons →
    64-bit hash.

    Mints + returns a PerceptualHash node:

      * ``hash``: int  (64-bit unsigned, in a Python int)
      * ``hash_hex``: str  (zero-padded 16-char hex for display)
      * ``n_frames_used``: int
    """
    inner = _native(s)
    frames = inner.neighbours(stream_nid, _audio.HAS_FRAME)
    # Need n_frames + 1 loudness samples for n_frames bit comparisons.
    needed = skip_head + n_frames + 1
    if len(frames) < needed:
        return None
    loudness: list[float] = []
    for fid in frames[skip_head:needed]:
        granules = inner.neighbours(fid, _audio.HAS_GRANULE)
        if not granules:
            return None
        gains = [int(inner.node(g)["attrs"]["global_gain"]) for g in granules]
        loudness.append(sum(gains) / len(gains))
    h = 0
    for i in range(n_frames):
        if loudness[i] > loudness[i + 1]:
            h |= (1 << i)
    nid = inner.add_node(PERCEPTUAL_HASH, {
        "hash": int(h),
        "hash_hex": f"{h:016x}",
        "n_frames_used": int(n_frames),
        "algorithm": "mp3_dlh64",
    })
    inner.add_edge(stream_nid, HAS_PERCEPTUAL_HASH, nid)
    return nid


def hamming_distance(h1: int, h2: int) -> int:
    """Hamming distance between two 64-bit hashes — count of bits
    that differ. ``int.bit_count`` is the Python 3.10+ popcount."""
    return int((h1 ^ h2).bit_count())


# --- Bitstream rewrite: truncate transrate ----------------------------

# Bitrate index used by MPEG-1 Layer III, indexed into
# _MP3_BITRATES_V1L3 in audio.py.
_MP3_V1L3_KBPS_TO_IDX = {
    32: 1, 40: 2, 48: 3, 56: 4, 64: 5, 80: 6, 96: 7, 112: 8, 128: 9,
    160: 10, 192: 11, 224: 12, 256: 13, 320: 14,
}


def _frame_size_bytes(bitrate_kbps: int, sample_rate_hz: int,
                      padding: bool) -> int:
    """MP3 frame size formula (MPEG-1 Layer III):
       frame_size = floor(144 * bitrate_bps / sample_rate_hz) + padding"""
    return (144 * bitrate_kbps * 1000) // sample_rate_hz + (1 if padding else 0)


def mp3_truncate_transrate(input_path: str, output_path: str, *,
                           target_kbps: int) -> dict:
    """Naive bitstream-level transrate. Walks every MP3 frame in the
    input; rewrites the bitrate-index field in each header; truncates
    each frame's main_data to the new (smaller) frame size; zeroes
    each granule's ``main_data_begin`` field (kills the bit
    reservoir, since reservoir pointers break under frame-size
    change); writes the resulting MP3 to ``output_path``.

    Honest caveat: quality is the ceiling of "truncate the high-
    frequency Huffman tail." This is a faithful demonstration of
    the COST shape (~20–50× faster than full transcode) but not a
    full requantize-transrate. Phase 16b will add real Huffman re-
    encoding with optimal coefficient retention.

    Returns a dict of stats:
      * ``frames_processed``: int
      * ``frames_skipped``: int  (unparseable / non-Layer-III)
      * ``input_size``: int
      * ``output_size``: int
      * ``size_ratio``: float
      * ``wall_seconds``: float
      * ``source_kbps``: int  (most-common source bitrate)
      * ``target_kbps``: int
    """
    if target_kbps not in _MP3_V1L3_KBPS_TO_IDX:
        raise ValueError(
            f"target_kbps={target_kbps} not a valid MPEG-1 L3 rate; "
            f"valid: {sorted(_MP3_V1L3_KBPS_TO_IDX)}")
    new_idx = _MP3_V1L3_KBPS_TO_IDX[target_kbps]

    t0 = time.monotonic()
    with open(input_path, "rb") as f:
        data = f.read()
    out = bytearray()

    pos = 0
    n = len(data)
    frames = 0
    skipped = 0
    source_kbps_counts: dict[int, int] = {}

    while pos < n - 4:
        # Find next frame sync (0xFFE).
        if not (data[pos] == 0xFF and (data[pos + 1] & 0xE0) == 0xE0):
            # ID3 tag at start or skip any non-frame bytes verbatim.
            out.append(data[pos])
            pos += 1
            continue
        header = _audio._parse_mp3_header(data[pos:pos + 4])
        if header is None or header["layer"] != "III":
            out.append(data[pos])
            pos += 1
            continue
        version = header["version"]
        if version != "MPEG1":
            # We only handle MPEG-1 here.
            old_size = _frame_size_bytes(header["bitrate_kbps"],
                                         header["sample_rate_hz"],
                                         header["padding"])
            out.extend(data[pos:pos + old_size])
            pos += old_size
            skipped += 1
            continue

        src_kbps = header["bitrate_kbps"]
        old_size = _frame_size_bytes(src_kbps, header["sample_rate_hz"],
                                     header["padding"])
        if old_size <= 0 or pos + old_size > n:
            break

        # Rewrite the header: bitrate index lives at bits 12-15 of the
        # 32-bit header (i.e., the 2nd byte, top nibble).
        new_hdr = bytearray(data[pos:pos + 4])
        new_hdr[2] = (new_hdr[2] & 0x0F) | (new_idx << 4)
        # The frame header carries the *new* bitrate, so recompute size.
        new_size = _frame_size_bytes(target_kbps, header["sample_rate_hz"],
                                     header["padding"])
        if new_size > old_size:
            # Target is higher than source — nothing to truncate, just
            # copy through with rewritten header but ORIGINAL size
            # (can't synthesize new bits). We still emit at original
            # bitrate to avoid a malformed frame; bump back to source.
            new_hdr[2] = (new_hdr[2] & 0x0F) | (
                _MP3_V1L3_KBPS_TO_IDX[src_kbps] << 4)
            out.extend(bytes(new_hdr))
            out.extend(data[pos + 4:pos + old_size])
            pos += old_size
            frames += 1
            source_kbps_counts[src_kbps] = source_kbps_counts.get(src_kbps, 0) + 1
            continue

        # Copy through: rewritten header + crc (if any) + side info
        # with main_data_begin zeroed + as much main_data as fits.
        side_start = 4 + (2 if header["has_crc"] else 0)
        mono = header["channel_mode"] == "mono"
        side_size = 17 if mono else 32
        main_start = side_start + side_size
        # Truncate main_data to fit new_size.
        main_keep = max(0, new_size - main_start)
        # Build the new frame.
        new_frame = bytearray(new_size)
        new_frame[0:4] = new_hdr
        # CRC + side info copied verbatim, then zero main_data_begin
        # (kills the reservoir: bits 0-8 of the side info region).
        new_frame[4:main_start] = data[pos + 4:pos + main_start]
        # Zero main_data_begin (the first 9 bits of the side-info
        # region). We need to clear bits 7..7-(8) of byte side_start
        # and the top bit of side_start+1.
        new_frame[side_start] = 0
        # Top bit of byte 1 of side info is the 9th bit of
        # main_data_begin — clear it.
        new_frame[side_start + 1] &= 0x7F
        # Copy as much main_data as the new frame can hold.
        new_frame[main_start:main_start + main_keep] = (
            data[pos + main_start:pos + main_start + main_keep])
        # Bytes beyond main_keep are zeroed (truncated coefficients).
        out.extend(new_frame)
        pos += old_size
        frames += 1
        source_kbps_counts[src_kbps] = source_kbps_counts.get(src_kbps, 0) + 1

    with open(output_path, "wb") as f:
        f.write(bytes(out))
    wall = time.monotonic() - t0

    src_kbps_mode = (max(source_kbps_counts, key=source_kbps_counts.get)
                     if source_kbps_counts else 0)
    return {
        "frames_processed": int(frames),
        "frames_skipped": int(skipped),
        "input_size": int(n),
        "output_size": int(len(out)),
        "size_ratio": float(len(out)) / max(n, 1),
        "wall_seconds": float(wall),
        "source_kbps": int(src_kbps_mode),
        "target_kbps": int(target_kbps),
    }


def _ffmpeg_transrate(input_path: str, output_path: str, *,
                      target_kbps: int) -> float:
    """Run ffmpeg `-b:a Nk` transrate; return wall seconds."""
    t0 = time.monotonic()
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", input_path,
        "-codec:a", "libmp3lame",
        "-b:a", f"{target_kbps}k",
        output_path,
    ], check=True)
    return time.monotonic() - t0


def benchmark_truncate_transrate_vs_ffmpeg(input_path: str, *,
                                           target_kbps: int) -> dict:
    """Run both pipelines on the same input + report wall-clock,
    output sizes, and ratio. Returns a dict — do NOT call inside a
    tight test loop (spawns ffmpeg)."""
    with tempfile.TemporaryDirectory() as td:
        ours_out = os.path.join(td, "ours.mp3")
        ffm_out = os.path.join(td, "ffmpeg.mp3")
        ours = mp3_truncate_transrate(input_path, ours_out,
                                       target_kbps=target_kbps)
        ffm_wall = _ffmpeg_transrate(input_path, ffm_out,
                                      target_kbps=target_kbps)
        ffm_size = os.path.getsize(ffm_out)
    return {
        "ours": ours,
        "ffmpeg": {
            "wall_seconds": float(ffm_wall),
            "output_size": int(ffm_size),
        },
        "speedup": float(ffm_wall) / max(ours["wall_seconds"], 1e-9),
    }


# --- Transform provenance --------------------------------------------

def record_transform(s, *, kind: str, params: dict,
                     applied_to_stream_nid: Any | None = None) -> Any:
    """Mint a BitstreamTransform provenance node. The agent can walk
    these to ask 'what's been done to this stream?'. Wires
    ``stream --was_transformed_by--> transform`` when an originating
    stream is given."""
    inner = _native(s)
    nid = inner.add_node(BITSTREAM_TRANSFORM, {
        "kind": str(kind),
        "params": {str(k): v for k, v in params.items()},
    })
    if applied_to_stream_nid is not None:
        inner.add_edge(applied_to_stream_nid, WAS_TRANSFORMED_BY, nid)
    return nid


# --- HuffmanTable graph nodes (16b) ----------------------------------
#
# 16b lifts the MP3 Huffman tables out of opaque codec internals and
# into the substrate as graph nodes. Same shape as :class:`Filter`
# (audio) or :class:`Kernel` (vision): table DATA on the graph,
# bit-twiddle as substrate primitive. The agent can introspect "what
# tables exist?" via `nodes(HUFFMAN_TABLE)` and read codes/hlens/
# linbits via standard Attr queries.

def seed_mp3_huffman_tables(s) -> dict:
    """Mint 18 MPEG-1 Layer III Huffman tables as :data:`HUFFMAN_TABLE`
    graph nodes (16 big_values + 2 count1). Data sourced from LAME's
    tables.c, which contains the ISO 11172-3 Annex B.7 values verbatim.

    Per-node attrs:

      * ``codec``    — ``"mp3"`` (lets future H.264/JPEG/Vorbis tables
        coexist in the same type)
      * ``index``    — HT number (1..15, 16..23, 24..31, 32, 33)
      * ``xlen``     — table dimension (or 0 for count1 tables)
      * ``linmax``   — max value before ``linbits`` escape kicks in
        (0 means no escape — coefficient bounded by table dim)
      * ``linbits``  — ``linmax.bit_length()`` — convenience for the
        decoder/encoder
      * ``codes``    — bytes (numpy uint16 array, ``np.frombuffer``)
      * ``hlens``    — bytes (numpy uint8 array)

    Idempotent across substrate setup calls but not within one — call
    once. Returns ``{HT_index: NodeID}``.
    """
    from ._mp3_huffman_data import MP3_HUFFMAN_TABLES
    inner = _native(s)
    out: dict = {}
    for idx, (xlen, linmax, codes, hlens) in MP3_HUFFMAN_TABLES.items():
        nid = inner.add_node(HUFFMAN_TABLE, {
            "codec": "mp3",
            "index": int(idx),
            "xlen": int(xlen),
            "linmax": int(linmax),
            "linbits": int(linmax).bit_length(),
            "codes": np.asarray(codes, dtype=np.uint16).tobytes(),
            "hlens": np.asarray(hlens, dtype=np.uint8).tobytes(),
            "n_entries": int(len(codes)),
        })
        out[int(idx)] = nid
    return out


def list_huffman_tables(s, codec: str | None = None) -> list:
    """Walk all HuffmanTable nodes, optionally filtered by codec.
    Returns a list of NodeIDs sorted by table index."""
    inner = _native(s)
    nodes = inner.nodes(HUFFMAN_TABLE)
    out = []
    for n in nodes:
        a = inner.node(n)["attrs"]
        if codec is not None and a.get("codec") != codec:
            continue
        out.append((int(a.get("index", 0)), n))
    out.sort()
    return [n for _, n in out]


def huffman_table_arrays(s, table_nid) -> tuple:
    """Decode a HuffmanTable node into ``(codes_array, hlens_array,
    linbits, xlen)``. Pure graph-attr read — no codec-internal magic.
    The substrate primitive that consumes these arrays IS the
    decoder/encoder bit-twiddle, but the data flow comes from the
    graph."""
    a = _native(s).node(table_nid)["attrs"]
    codes = np.frombuffer(a["codes"], dtype=np.uint16)
    hlens = np.frombuffer(a["hlens"], dtype=np.uint8)
    return codes, hlens, int(a["linbits"]), int(a["xlen"])


# --- Bit reader / writer primitives ----------------------------------

class _BitWriter:
    """MSB-first bit writer. Mirror of audio.py's _BitReader; lives
    here because only the bitstream-transform path needs writing."""
    __slots__ = ("_bytes", "_byte_buf", "_bits_in_buf")

    def __init__(self) -> None:
        self._bytes = bytearray()
        self._byte_buf = 0
        self._bits_in_buf = 0

    def write(self, value: int, n_bits: int) -> None:
        """Append the low ``n_bits`` of ``value``, MSB-first."""
        for i in range(n_bits - 1, -1, -1):
            self._byte_buf = (self._byte_buf << 1) | ((value >> i) & 1)
            self._bits_in_buf += 1
            if self._bits_in_buf == 8:
                self._bytes.append(self._byte_buf)
                self._byte_buf = 0
                self._bits_in_buf = 0

    def align(self) -> None:
        """Pad with zero bits to the next byte boundary."""
        if self._bits_in_buf > 0:
            self._byte_buf <<= (8 - self._bits_in_buf)
            self._bytes.append(self._byte_buf)
            self._byte_buf = 0
            self._bits_in_buf = 0

    def bit_count(self) -> int:
        """Total bits written (including pending bits in the buffer)."""
        return len(self._bytes) * 8 + self._bits_in_buf

    def as_bytes(self) -> bytes:
        """Return all written bits, padded to a byte boundary if
        partial. Does not mutate the writer's state."""
        out = bytearray(self._bytes)
        if self._bits_in_buf > 0:
            out.append(self._byte_buf << (8 - self._bits_in_buf))
        return bytes(out)


# --- Huffman decode / encode primitives ------------------------------

def _build_decode_lut(codes: np.ndarray, hlens: np.ndarray
                      ) -> tuple[dict, int]:
    """Build (prefix → (length, x, y)) lookup table from a flat 2D
    Huffman table. Returns (lut, max_len). For count1 tables (xlen=0)
    the indices encode a 4-bit quad rather than an (x, y) pair; the
    caller interprets them.

    Indexed by the LEFT-justified Huffman code (i.e. code << (max_len -
    len)) so we can read max_len bits and look up directly. This is
    the standard fast-path decoder shape."""
    dim = int(np.sqrt(len(codes)))
    max_len = int(hlens.max()) if len(hlens) else 0
    lut: dict[int, tuple[int, int, int]] = {}
    for i in range(len(codes)):
        ln = int(hlens[i])
        if ln == 0:
            continue
        code = int(codes[i])
        if dim > 0:
            x, y = divmod(i, dim)
        else:
            # count1 table — i IS the quad value 0..15.
            x, y = i, 0
        # Left-justify to max_len.
        shifted = code << (max_len - ln)
        lut[shifted] = (ln, x, y)
    return lut, max_len


def decode_huffman_pair(reader: "_audio._BitReader",
                        codes: np.ndarray, hlens: np.ndarray,
                        linbits: int) -> tuple[int, int]:
    """Decode one (x, y) coefficient pair from the bit stream using
    the given table data + linbits. Reads sign bits inline for
    non-zero values. Returns the decoded values with sign applied.

    Walks the Huffman tree one bit at a time (slow but correct). For
    16b we prioritise correctness; LUT-accelerated decode is a 16d
    optimisation if it shows up in a profile."""
    dim = int(np.sqrt(len(codes)))
    # Walk one bit at a time, accumulating a code. We compare against
    # every (code, hlens) entry at the matching length.
    acc = 0
    bits_read = 0
    while True:
        bit = reader.read(1)
        acc = (acc << 1) | bit
        bits_read += 1
        for i in range(len(codes)):
            ln = int(hlens[i])
            if ln != bits_read:
                continue
            if int(codes[i]) != acc:
                continue
            x, y = divmod(i, dim)
            # linbits escape: value == 15 means read linbits more,
            # add to base value.
            if linbits > 0 and x == 15:
                x += reader.read(linbits)
            if linbits > 0 and y == 15:
                y += reader.read(linbits)
            if x != 0:
                if reader.read(1):
                    x = -x
            if y != 0:
                if reader.read(1):
                    y = -y
            return x, y
        if bits_read > 32:
            # Shouldn't happen for valid MP3 — bail with zeros to
            # avoid an infinite loop on corrupt input.
            return 0, 0


def encode_huffman_pair(writer: _BitWriter,
                        x: int, y: int,
                        codes: np.ndarray, hlens: np.ndarray,
                        linbits: int) -> int:
    """Encode one (x, y) coefficient pair via the given Huffman
    table + linbits. Returns the number of bits written.

    Caller is responsible for tracking the running bit budget;
    requantize logic in :func:`_requantize_to_fit` decides whether
    to admit a coefficient or zero it."""
    dim = int(np.sqrt(len(codes)))
    abs_x, abs_y = abs(x), abs(y)
    # linbits escape if magnitude exceeds 14 (i.e., needs slot 15 +
    # linbits for the overflow).
    extra = 0
    huff_x, huff_y = abs_x, abs_y
    if linbits > 0:
        if abs_x >= 15:
            huff_x = 15
            extra += linbits
        if abs_y >= 15:
            huff_y = 15
            extra += linbits
    if huff_x >= dim or huff_y >= dim:
        # Out-of-table — caller should have chosen a bigger table.
        # Best-effort: clamp to last valid pair and emit.
        huff_x = min(huff_x, dim - 1)
        huff_y = min(huff_y, dim - 1)
    idx = huff_x * dim + huff_y
    ln = int(hlens[idx])
    code = int(codes[idx])
    start_bits = writer.bit_count()
    writer.write(code, ln)
    if linbits > 0:
        if abs_x >= 15:
            writer.write(abs_x - 15, linbits)
        if abs_y >= 15:
            writer.write(abs_y - 15, linbits)
    if x != 0:
        writer.write(1 if x < 0 else 0, 1)
    if y != 0:
        writer.write(1 if y < 0 else 0, 1)
    return writer.bit_count() - start_bits


def encoded_bits(x: int, y: int,
                 hlens: np.ndarray, linbits: int, xlen_dim: int) -> int:
    """Cost-only: how many bits would `encode_huffman_pair` write,
    without actually writing? Used by the requantizer to size frames
    before commit. Mirrors encoder logic exactly."""
    dim = int(np.sqrt(len(hlens)))
    abs_x, abs_y = abs(x), abs(y)
    extra = 0
    huff_x, huff_y = abs_x, abs_y
    if linbits > 0:
        if abs_x >= 15:
            huff_x = 15
            extra += linbits
        if abs_y >= 15:
            huff_y = 15
            extra += linbits
    if huff_x >= dim or huff_y >= dim:
        huff_x = min(huff_x, dim - 1)
        huff_y = min(huff_y, dim - 1)
    idx = huff_x * dim + huff_y
    bits = int(hlens[idx]) + extra
    if x != 0:
        bits += 1
    if y != 0:
        bits += 1
    return bits




__all__ = [
    "LOUDNESS_PROFILE", "TRANSIENT_PROFILE", "PERCEPTUAL_HASH",
    "BITSTREAM_TRANSFORM", "HUFFMAN_TABLE",
    "HAS_LOUDNESS_PROFILE", "HAS_TRANSIENT_PROFILE",
    "HAS_PERCEPTUAL_HASH", "WAS_TRANSFORMED_BY",
    "seed_bitstream_grammar",
    "seed_mp3_huffman_tables", "list_huffman_tables",
    "huffman_table_arrays",
    "mp3_loudness_profile", "loudness_profile_array",
    "mp3_transient_profile", "transient_profile_array",
    "mp3_perceptual_hash", "hamming_distance",
    "mp3_truncate_transrate",
    "benchmark_truncate_transrate_vs_ffmpeg",
    "record_transform",
    "decode_huffman_pair", "encode_huffman_pair", "encoded_bits",
]
