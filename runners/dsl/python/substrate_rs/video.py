"""Video as graph data — parse the FORMAT, not the rendered output.

The proposition: a video file is already a structured document. The
encoder did the hard work of finding what changed, where, and how —
that work is preserved in the bitstream as I/P/B frame structure,
motion vectors per macroblock, skip blocks, coding cost per region.
Decoding to pixels DESTROYS this structure. So we don't decode — we
parse the format directly into graph nodes the agent can read.

Biology angle: the retina doesn't ship raw photons to cortex; it
ships structured signals (gain-controlled, centre-surround,
motion-onset). Similarly, the video bitstream is already structured.
Reading the motion vectors the encoder wrote is the right substrate
analogue of MT/V5 reading its inputs from V1 — it's signals, not
pixels.

Node types
----------
:data:`VIDEO_CONTAINER`
    The file. Attrs: ``path``, ``format``, ``duration_s``, ``n_streams``.
:data:`VIDEO_STREAM`
    One stream inside the container. Attrs: ``codec``, ``width``,
    ``height``, ``framerate``, ``pixel_format``, ``stream_index``.
:data:`FRAME`
    A packet's decoded-header (we read the header, not the pixels).
    Attrs: ``pts``, ``dts``, ``pict_type`` (``I``/``P``/``B``),
    ``key_frame``, ``coded_size``, ``frame_index``,
    ``time_s``. The pixels are NOT in here — see ``decode_frame``.
:data:`MOTION_VECTOR`
    One motion vector the encoder wrote, per macroblock. Attrs:
    ``src_x`` / ``src_y`` / ``dst_x`` / ``dst_y`` / ``dx`` / ``dy``
    / ``w`` / ``h`` / ``source`` (forward/backward).

Edges
-----
:data:`HAS_STREAM`  Container → Stream
:data:`HAS_FRAME`   Stream → Frame
:data:`FOLLOWS`     Frame → previous Frame (decode-order chain)
:data:`HAS_MV`      Frame → MotionVector
:data:`MV_FROM`     MotionVector → source Frame (B-frames can reference both directions)

What the agent gets to do without ever decoding pixels
------------------------------------------------------
* Scene cuts: ``nodes(FRAME)`` filtered to ``pict_type == "I"`` (sub-ms).
* "Where's the most motion?": group MV magnitudes by ``frame_index``,
  argmax.
* "How visually complex is each frame?": ``Frame.coded_size`` —
  larger means harder to predict, i.e. more new content.
* "Show me the busiest second": bucket Frames by ``time_s // 1``,
  sum coded_size.
* "What was on screen at t=23.5s?": find the Frame at that pts,
  then ``decode_frame`` (one decode, on demand).

When the agent actually needs pixels, :func:`decode_frame` returns
an :class:`Image` node compatible with :mod:`substrate_rs.vision`
— so the whole vision pipeline (V1 / V2 / V4 / Hebbian learning)
composes on top of this. The agent zooms in by decoding; otherwise
it works at the bitstream level.
"""
from __future__ import annotations

from typing import Any, Iterator, Optional

import numpy as np

try:
    import av
    from av.sidedata.sidedata import Type as _SideDataType
    _HAS_AV = True
except ImportError:  # pragma: no cover
    av = None
    _SideDataType = None
    _HAS_AV = False

from . import Substrate as _PySubstrate

# AV_CODEC_FLAG2_EXPORT_MVS — set on the codec context to make the
# decoder copy the encoder's motion vectors into frame side-data.
_FLAG2_EXPORT_MVS = 1 << 28

# Pict-type codes PyAV exposes as strings. (libav constants:
# AV_PICTURE_TYPE_I = 1, P = 2, B = 3, S/SI/SP = 4-6.)
_PICT_NAMES = {"1": "I", "2": "P", "3": "B", "4": "S", "5": "SI", "6": "SP"}

# --- Node + edge type constants ----------------------------------------

VIDEO_CONTAINER = "VideoContainer"
VIDEO_STREAM = "VideoStream"
FRAME = "Frame"
MOTION_VECTOR = "MotionVector"

HAS_STREAM = "has_stream"
HAS_FRAME = "has_frame"
FOLLOWS = "follows"           # decode-order chain
HAS_MV = "has_motion_vector"
MV_FROM = "mv_from"           # MV references its source frame


def _native(s):
    return s._inner if isinstance(s, _PySubstrate) else s


# --- Grammar seeding ---------------------------------------------------

def seed_video_grammar(s) -> int:
    """Add productions for VideoContainer / VideoStream / Frame /
    MotionVector + the relationship edges. Returns count added."""
    if not _HAS_AV:
        raise RuntimeError("PyAV is required for substrate_rs.video")
    from . import NodePattern, Production
    inner = _native(s)
    prods = []

    def _perm(src_type: str, edge_type: str, tgt_type: str, prov: str):
        prods.append(Production(
            src=NodePattern(type=src_type, var="src"),
            edge_type=edge_type,
            tgt=NodePattern(type=tgt_type, var="tgt"),
            where=None, weight=None, provenance=prov,
        ))

    _perm(VIDEO_CONTAINER, HAS_STREAM, VIDEO_STREAM, "video:container_has_stream")
    _perm(VIDEO_STREAM, HAS_FRAME, FRAME, "video:stream_has_frame")
    _perm(FRAME, FOLLOWS, FRAME, "video:frame_follows_frame")
    _perm(FRAME, HAS_MV, MOTION_VECTOR, "video:frame_has_mv")
    _perm(MOTION_VECTOR, MV_FROM, FRAME, "video:mv_from_frame")

    for p in prods:
        inner.add_production(p.to_dict())
    return len(prods)


# --- Container + stream ingest -----------------------------------------

class _ContainerHandle:
    """Tracks an open PyAV container + the parsed-stream state. Stored
    in a process-local registry keyed by the Container NodeID's int
    value so the substrate stays Python-serialisable (we can't put a
    PyAV object on a graph node attr). The agent re-opens via
    :func:`reopen_container` after a load."""

    __slots__ = ("path", "av_container", "stream_index", "frame_map", "frame_index_seq")

    def __init__(self, path: str, av_container, stream_index: int):
        self.path = path
        self.av_container = av_container
        self.stream_index = stream_index
        # frame_map: int frame_index → Frame NodeID — lets us look up
        # the graph node we minted for a given decode-order frame, so
        # later operations (decode_frame, motion_summary) don't have
        # to re-walk the graph.
        self.frame_map: dict[int, Any] = {}
        self.frame_index_seq: int = 0


_OPEN_CONTAINERS: dict[int, _ContainerHandle] = {}


def open_container(s, path: str) -> Any:
    """Open `path` via PyAV; mint a VideoContainer node carrying the
    container-level metadata. Returns the Container NodeID. The
    actual av.Container handle is held in a process-local registry —
    nothing about a live decoder belongs in graph attrs.
    """
    if not _HAS_AV:
        raise RuntimeError("PyAV is required for substrate_rs.video")
    container = av.open(path)
    inner = _native(s)
    nid = inner.add_node(VIDEO_CONTAINER, {
        "path": path,
        "format": container.format.long_name or container.format.name,
        "duration_s": float(container.duration / 1_000_000) if container.duration else 0.0,
        "n_streams": len(container.streams),
        "size_bytes": container.size if hasattr(container, "size") else 0,
    })
    # Keep the av handle alive in the process registry.
    # We don't auto-open a stream — the caller picks which stream to
    # parse via `parse_stream`. Most files have multiple (video,
    # audio, subtitles); the agent decides which to pull into graph.
    _OPEN_CONTAINERS[nid.value] = _ContainerHandle(
        path=path, av_container=container, stream_index=-1)
    return nid


def reopen_container(s, container_nid) -> None:
    """Re-attach the PyAV container handle for a previously-opened
    Container node (e.g. after persistence load). The caller is
    responsible for calling this before any parse_stream /
    decode_frame on the re-loaded substrate."""
    if not _HAS_AV:
        raise RuntimeError("PyAV is required for substrate_rs.video")
    inner = _native(s)
    path = inner.node(container_nid)["attrs"]["path"]
    container = av.open(path)
    _OPEN_CONTAINERS[container_nid.value] = _ContainerHandle(
        path=path, av_container=container, stream_index=-1)


def close_container(container_nid) -> None:
    """Release the PyAV handle. The graph nodes survive."""
    handle = _OPEN_CONTAINERS.pop(container_nid.value, None)
    if handle is not None:
        handle.av_container.close()


def _handle_for(container_nid) -> _ContainerHandle:
    h = _OPEN_CONTAINERS.get(container_nid.value)
    if h is None:
        raise RuntimeError(
            "container handle not open — call reopen_container after a "
            "persistence load, or open_container for a fresh start")
    return h


def add_stream(s, container_nid, stream_index: int = 0,
               export_motion_vectors: bool = True) -> Any:
    """Mint a VideoStream node for the stream at `stream_index` of
    the container. Returns the stream NodeID. Enables MV export on
    the codec context so subsequent `parse_stream` calls can read
    them.
    """
    handle = _handle_for(container_nid)
    stream = handle.av_container.streams[stream_index]
    if stream.type != "video":
        raise ValueError(
            f"stream {stream_index} is type={stream.type!r}, not 'video'")
    if export_motion_vectors:
        stream.codec_context.flags2 |= _FLAG2_EXPORT_MVS
    handle.stream_index = stream_index
    inner = _native(s)
    rate = stream.average_rate
    sid = inner.add_node(VIDEO_STREAM, {
        "stream_index": int(stream_index),
        "codec": stream.codec_context.name,
        "width": int(stream.width),
        "height": int(stream.height),
        "framerate": float(rate) if rate else 0.0,
        "pixel_format": str(stream.pix_fmt) if stream.pix_fmt else "",
        "n_frames": int(stream.frames) if stream.frames else 0,
        "time_base_num": stream.time_base.numerator if stream.time_base else 1,
        "time_base_den": stream.time_base.denominator if stream.time_base else 1,
    })
    inner.add_edge(container_nid, HAS_STREAM, sid)
    return sid


# --- Frame + motion-vector ingest --------------------------------------

def parse_stream(
    s,
    container_nid,
    stream_nid,
    *,
    frame_limit: int | None = None,
    include_motion_vectors: bool = True,
) -> int:
    """Walk the bitstream of `stream_nid`. For each frame mint a
    `Frame` node carrying its header (pict_type, pts, key_frame,
    coded_size, time_s) and — if available and `include_motion_vectors`
    — a `MotionVector` node per encoder-emitted MV.

    The pixels are NOT decoded into Image nodes here. Call
    :func:`decode_frame` on a specific Frame NodeID to materialise its
    pixels.

    Returns the total number of Frame nodes minted.

    ``frame_limit`` caps the ingest (handy for long videos — the agent
    can pull the first N frames into graph, query/skim, decide whether
    to continue).
    """
    handle = _handle_for(container_nid)
    inner = _native(s)
    stream_attrs = inner.node(stream_nid)["attrs"]
    stream_index = int(stream_attrs["stream_index"])
    if handle.stream_index != stream_index:
        raise ValueError(
            f"container handle is on stream {handle.stream_index}; "
            f"requested {stream_index}")
    time_base_num = float(stream_attrs.get("time_base_num", 1))
    time_base_den = float(stream_attrs.get("time_base_den", 1))
    tb = time_base_num / time_base_den if time_base_den else 0.0

    av_stream = handle.av_container.streams[stream_index]
    minted = 0
    prev_frame_nid: Optional[Any] = None
    # Iterate packets + decode their frames (PyAV gives us decoded
    # headers cheaply; we drop the pixel buffer on the floor).
    for packet in handle.av_container.demux(av_stream):
        if packet.size == 0:
            continue
        for frame in packet.decode():
            frame_nid = _mint_frame(
                inner, stream_nid, frame, handle, tb,
                coded_size=int(packet.size))
            if prev_frame_nid is not None:
                inner.add_edge(frame_nid, FOLLOWS, prev_frame_nid)
            prev_frame_nid = frame_nid
            handle.frame_map[handle.frame_index_seq - 1] = frame_nid
            if include_motion_vectors:
                _mint_motion_vectors(inner, frame_nid, frame, handle)
            minted += 1
            if frame_limit is not None and minted >= frame_limit:
                return minted
    return minted


def _mint_frame(inner, stream_nid, frame, handle, time_base: float,
                coded_size: int) -> Any:
    fi = handle.frame_index_seq
    handle.frame_index_seq += 1
    pts = frame.pts if frame.pts is not None else 0
    dts = frame.dts if frame.dts is not None else 0
    nid = inner.add_node(FRAME, {
        "frame_index": int(fi),
        "pts": int(pts),
        "dts": int(dts),
        "key_frame": bool(frame.key_frame),
        "pict_type": _PICT_NAMES.get(str(frame.pict_type), str(frame.pict_type)),
        "coded_size": int(coded_size),
        "time_s": float(pts) * time_base if pts is not None else 0.0,
        "width": int(frame.width) if hasattr(frame, "width") else 0,
        "height": int(frame.height) if hasattr(frame, "height") else 0,
    })
    inner.add_edge(stream_nid, HAS_FRAME, nid)
    return nid


def _mint_motion_vectors(inner, frame_nid, frame, handle) -> int:
    """Mint one MotionVector node per encoder-emitted MV on this
    frame. Returns count. Each MV node carries dx/dy + source/dest
    macroblock coords + block size + which direction (forward vs
    backward source). Cheap (~80 bytes per MV node)."""
    sd = frame.side_data
    if not sd:
        return 0
    mvs = sd.get(_SideDataType.MOTION_VECTORS)
    if mvs is None:
        return 0
    count = 0
    for mv in mvs:
        # `source` is +1 (forward, P-frame) or -1 (backward, B-frame
        # second source). motion_scale is the precision divisor —
        # we store the integer motion_x/y plus the scale so the
        # caller can reconstruct sub-pixel motion if they need.
        scale = int(mv.motion_scale) if mv.motion_scale else 1
        mv_nid = inner.add_node(MOTION_VECTOR, {
            "source": int(mv.source),
            "src_x": int(mv.src_x),
            "src_y": int(mv.src_y),
            "dst_x": int(mv.dst_x),
            "dst_y": int(mv.dst_y),
            # Raw integer motion in quarter-pel units (typical for
            # H.264); divide by motion_scale for pixel units.
            "motion_x": int(mv.motion_x),
            "motion_y": int(mv.motion_y),
            "motion_scale": scale,
            # Convenience: also store the pixel-unit displacement
            # (rounded) so a Filter on |dx|>N doesn't need to know
            # about quarter-pel encoding.
            "dx": int(round(mv.motion_x / scale)),
            "dy": int(round(mv.motion_y / scale)),
            "w": int(mv.w),
            "h": int(mv.h),
        })
        inner.add_edge(frame_nid, HAS_MV, mv_nid)
        count += 1
    return count


# --- On-demand pixel decode -------------------------------------------

def decode_frame(s, frame_nid) -> Any:
    """Materialise the pixels of `frame_nid` as an :class:`Image`
    node compatible with :mod:`substrate_rs.vision`. The substrate's
    whole vision pipeline (V1 / V2 / V4 / Hebbian) composes on top.

    This is the explicit "render" step the agent invokes only when
    it needs pixel-level access. Bitstream-level work (scene cuts,
    motion summaries, coding-cost queries) doesn't need this.
    """
    from . import vision as _vision
    inner = _native(s)
    a = inner.node(frame_nid)["attrs"]
    frame_index = int(a["frame_index"])
    # Find the container by walking back: Frame ← HAS_FRAME ← Stream
    # ← HAS_STREAM ← Container.
    stream_nid = None
    for src in inner.in_neighbours(frame_nid, HAS_FRAME):
        stream_nid = src
        break
    if stream_nid is None:
        raise RuntimeError(f"frame #{frame_nid.value} has no parent stream")
    container_nid = None
    for src in inner.in_neighbours(stream_nid, HAS_STREAM):
        container_nid = src
        break
    if container_nid is None:
        raise RuntimeError(f"stream #{stream_nid.value} has no parent container")

    handle = _handle_for(container_nid)
    # Re-seek to the start and walk forward to the requested frame.
    # PyAV supports seeking but for deterministic test behaviour we
    # rewind and step forward. Cache aware: handle.frame_map already
    # holds NodeIDs; we re-iterate frames until we hit frame_index.
    handle.av_container.seek(0)
    av_stream = handle.av_container.streams[handle.stream_index]
    target_idx = frame_index
    seen = 0
    for packet in handle.av_container.demux(av_stream):
        if packet.size == 0:
            continue
        for frame in packet.decode():
            if seen == target_idx:
                arr = frame.to_ndarray(format="rgb24")
                return _vision.image_from_array(
                    s, arr, origin=f"decoded:frame={frame_index}")
            seen += 1
    raise RuntimeError(f"could not seek to frame index {frame_index}")


# --- Query helpers (the agent's most-asked questions) --------------

def scene_cuts(s, stream_nid) -> list:
    """Frame NodeIDs whose pict_type is 'I' — encoder said "I can't
    predict this from the previous frame", which is exactly a scene
    cut (or a regular key-frame interval). Sub-millisecond on a
    multi-hour video because we're walking graph data."""
    inner = _native(s)
    out = []
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        if inner.node(fid)["attrs"].get("pict_type") == "I":
            out.append(fid)
    return out


def motion_summary(s, frame_nid) -> dict:
    """Aggregate stats over this frame's motion vectors: total count,
    mean magnitude, max magnitude, fraction of MVs with non-zero
    motion. Tells the agent "how much is happening in this frame"
    without any pixel work."""
    inner = _native(s)
    mvs = inner.neighbours(frame_nid, HAS_MV)
    if not mvs:
        return {"n_mvs": 0, "mean_mag": 0.0, "max_mag": 0.0,
                "fraction_nonzero": 0.0}
    mags = []
    nonzero = 0
    for mv_nid in mvs:
        a = inner.node(mv_nid)["attrs"]
        dx = float(a.get("dx", 0))
        dy = float(a.get("dy", 0))
        mag = (dx * dx + dy * dy) ** 0.5
        mags.append(mag)
        if dx != 0 or dy != 0:
            nonzero += 1
    return {
        "n_mvs": len(mvs),
        "mean_mag": sum(mags) / len(mags),
        "max_mag": max(mags),
        "fraction_nonzero": nonzero / len(mvs),
    }


def busiest_frames(s, stream_nid, top_k: int = 5) -> list:
    """Top-K Frame NodeIDs by `coded_size`. Larger coded size means
    the frame was hard to predict — more new visual content. Cheap
    proxy for "interesting" without decoding anything."""
    inner = _native(s)
    frames = inner.neighbours(stream_nid, HAS_FRAME)
    ranked = sorted(
        frames,
        key=lambda f: int(inner.node(f)["attrs"].get("coded_size", 0)),
        reverse=True)
    return ranked[:top_k]


def total_bytes_in_graph(s, stream_nid) -> int:
    """Sum of `coded_size` over every Frame — how big is the
    bitstream summary the agent currently holds? Useful for
    sanity checks ('did I parse the whole thing?')."""
    inner = _native(s)
    return sum(
        int(inner.node(f)["attrs"].get("coded_size", 0))
        for f in inner.neighbours(stream_nid, HAS_FRAME))


def frames_in_time_window(s, stream_nid, t_start: float, t_end: float) -> list:
    """Frame NodeIDs whose `time_s` is in [t_start, t_end]. Lets the
    agent ask 'what was happening between t=10 and t=12'."""
    inner = _native(s)
    out = []
    for fid in inner.neighbours(stream_nid, HAS_FRAME):
        t = float(inner.node(fid)["attrs"].get("time_s", 0.0))
        if t_start <= t <= t_end:
            out.append(fid)
    return out


# --- The agent's OWN H.264 keyframe renderer ----------------------------
#
# Unlike `decode_frame` (which hands pixels back from PyAV), this path
# decodes an IDR keyframe to pixels with the agent's OWN CABAC + intra
# decoder (`h264_decode_i_slice_to_pixels`). ffmpeg is used ONLY to
# carve the annexb access unit out of the container — never to decode.
# This is the "renderer it was missing": container bytes -> the agent's
# own pixels -> an Image node the rest of the vision pipeline composes
# on.

def _yuv420_to_rgb_bt601(y, u, v, cw, ch, disp_w, disp_h):
    """YUV 4:2:0 (coded planes) -> RGB ndarray (disp_h x disp_w x 3),
    BT.601 full-range-ish, honouring the display crop. Pure numpy
    mechanical translation (no agent decisions)."""
    Y = np.frombuffer(y, dtype=np.uint8).reshape(ch, cw)[:disp_h, :disp_w].astype(np.int32)
    U = np.frombuffer(u, dtype=np.uint8).reshape(ch // 2, cw // 2).astype(np.int32)
    V = np.frombuffer(v, dtype=np.uint8).reshape(ch // 2, cw // 2).astype(np.int32)
    # Upsample chroma 2x (nearest) then crop to display.
    U = U.repeat(2, axis=0).repeat(2, axis=1)[:disp_h, :disp_w]
    V = V.repeat(2, axis=0).repeat(2, axis=1)[:disp_h, :disp_w]
    c = Y - 16
    d = U - 128
    e = V - 128
    r = (298 * c + 409 * e + 128) >> 8
    g = (298 * c - 100 * d - 208 * e + 128) >> 8
    b = (298 * c + 516 * d + 128) >> 8
    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def decode_keyframe_own(s, container_path: str, timestamp_s: float,
                        deblock: bool = True) -> Any:
    """Render the IDR keyframe at/after `timestamp_s` to an Image node
    using the AGENT'S OWN decoder. Returns the Image NodeID.

    Mechanical world-adapter pipeline (no agent decisions in Python):
      1. ffmpeg carves the annexb IDR access unit (copy, no decode).
      2. The harness bit-parses SPS/PPS/slice-header (opaque -> tokens).
      3. The agent's `h264_decode_i_slice_to_pixels` produces YUV.
      4. YUV -> RGB (BT.601) honouring the coded->display crop.
      5. The RGB lands in an Image node via vision.image_from_array.
    """
    import subprocess, tempfile, os
    from . import vision as _vision
    # Import the harness parser (pure bit-twiddling world adapter).
    import importlib
    dm = importlib.import_module("scripts.decode_idr_to_pixels")
    inner = _native(s)

    with tempfile.TemporaryDirectory() as td:
        annexb = os.path.join(td, "k.h264")
        # ffmpeg: carve the access unit ONLY (bitstream copy, no decode).
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", str(timestamp_s),
            "-i", container_path, "-c:v", "copy",
            "-bsf:v", "h264_mp4toannexb", "-frames:v", "1", annexb,
        ], check=True)
        data = open(annexb, "rb").read()

    nals = dm.split_nals(data)
    sps = pps = idr = None
    for nri, nt, rbsp in nals:
        if nt == 7 and sps is None:
            sps = dm.parse_sps(rbsp)
        elif nt == 8 and pps is None:
            pps = dm.parse_pps(rbsp)
        elif nt == 5 and idr is None:
            idr = (nri, rbsp)
    if not (sps and pps and idr):
        raise RuntimeError("could not find SPS/PPS/IDR in carved access unit")

    sps_pps = {**sps, **pps}
    mb_w, mb_h = sps["mb_width"], sps["mb_height"]
    nri, idr_rbsp = idr
    slice_rbsp = dm.strip_eps(idr_rbsp)

    hdr = inner.walk_h264_slice_header(slice_rbsp, sps_pps, nri, True)
    slice_qp = int(hdr["slice_qp"])
    cabac_start = int(hdr["cabac_start_bp"])
    disable_idc = int(hdr.get("disable_deblocking_filter_idc", 0))
    alpha_off = 2 * int(hdr.get("slice_alpha_c0_offset_div2", 0))
    beta_off = 2 * int(hdr.get("slice_beta_offset_div2", 0))

    # THE AGENT'S OWN DECODE.
    y, u, v, *_ = inner.h264_decode_i_slice_to_pixels(
        slice_rbsp, cabac_start, slice_qp, 0, mb_w, mb_h,
        pps.get("chroma_qp_index_offset", 0),
        deblock, disable_idc, alpha_off, beta_off,
    )

    cw, ch = mb_w * 16, mb_h * 16
    disp_w = sps.get("disp_width", cw)
    disp_h = sps.get("disp_height", ch)
    rgb = _yuv420_to_rgb_bt601(y, u, v, cw, ch, disp_w, disp_h)
    return _vision.image_from_array(
        s, rgb, origin=f"own-h264:t={timestamp_s}")


__all__ = [
    "VIDEO_CONTAINER", "VIDEO_STREAM", "FRAME", "MOTION_VECTOR",
    "HAS_STREAM", "HAS_FRAME", "FOLLOWS", "HAS_MV", "MV_FROM",
    "seed_video_grammar",
    "open_container", "reopen_container", "close_container",
    "add_stream", "parse_stream", "decode_frame",
    "decode_keyframe_own",
    "scene_cuts", "motion_summary", "busiest_frames",
    "total_bytes_in_graph", "frames_in_time_window",
]
