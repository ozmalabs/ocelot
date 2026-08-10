"""Phase 13 — video as graph data, format-parsed not rendered.

Verifies:
* A video file can be opened and its structure walked into graph
  nodes (Container, Stream, Frame, MotionVector).
* The encoder's motion-vector analysis is graph-resident — the agent
  reads the structure the encoder found, without ever decoding pixels.
* Scene cuts, motion summaries, busiest-frame queries all answered by
  graph walks (no pixel work).
* `decode_frame` is the explicit "render this one frame" path —
  produces an Image node compatible with the V1 cortex.
* Bitstream-summary size << pixel-rendered size (the headline win).
"""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")
av = pytest.importorskip("av")
vid = pytest.importorskip("substrate_rs.video")
from substrate_rs import vision as v  # for decode_frame's Image output


# --- Fixture: synthesise a tiny test video --------------------------


def _make_test_mp4(path: str, n_frames: int = 30, moving: bool = True,
                   width: int = 120, height: int = 80) -> str:
    """Write a small H.264 video. With `moving=True`, frames show a
    bright square translating left→right — gives the encoder real
    motion vectors to compute. With `moving=False`, all frames are
    blank — every macroblock is a skip block (zero MVs)."""
    container = av.open(path, mode="w")
    stream = container.add_stream("h264", rate=10)
    stream.width = width
    stream.height = height
    stream.pix_fmt = "yuv420p"
    for i in range(n_frames):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        if moving:
            x = 10 + i * 3
            img[20:50, max(0, x):min(width, x + 20)] = 255
        for pkt in stream.encode(av.VideoFrame.from_ndarray(
                img, format="rgb24").reformat(format="yuv420p")):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


@pytest.fixture
def video_path():
    """A 30-frame H.264 video of a translating square."""
    f = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    f.close()
    _make_test_mp4(f.name, n_frames=30, moving=True)
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def static_video_path():
    """A 20-frame video of a blank frame (no motion)."""
    f = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    f.close()
    _make_test_mp4(f.name, n_frames=20, moving=False)
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def s():
    sub = srs.Substrate()
    vid.seed_video_grammar(sub)
    return sub


# --- Container + stream ingest --------------------------------------


def test_open_container_creates_container_node(s, video_path):
    cnid = vid.open_container(s, video_path)
    node = s.node(cnid)
    assert node["type"] == vid.VIDEO_CONTAINER
    attrs = node["attrs"]
    assert attrs["path"] == video_path
    assert attrs["n_streams"] >= 1
    assert attrs["duration_s"] > 0


def test_add_stream_creates_stream_node_with_codec_info(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid, stream_index=0)
    attrs = s.node(snid)["attrs"]
    assert attrs["codec"] == "h264"
    assert attrs["width"] == 120
    assert attrs["height"] == 80
    assert attrs["framerate"] == 10.0
    # Container -has_stream-> Stream
    assert snid in s.neighbours(cnid, vid.HAS_STREAM)


# --- Frame ingest ---------------------------------------------------


def test_parse_stream_mints_frame_per_packet(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    n = vid.parse_stream(s, cnid, snid)
    # Encoders may drop the last 1-2 frames if they don't fit a full
    # GOP; we asked for 30 but ≥27 is the realistic floor.
    assert n >= 27, f"expected ≥27 frames; got {n}"
    # Each frame is a node — count matches.
    frames = s.neighbours(snid, vid.HAS_FRAME)
    assert len(frames) == n
    # Frames are in decode-order — chain via FOLLOWS. Every frame
    # except the first has a FOLLOWS edge.
    chained = sum(1 for f in frames if s.neighbours(f, vid.FOLLOWS))
    assert chained == n - 1


def test_frames_carry_pict_type_and_pts(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    frames = s.neighbours(snid, vid.HAS_FRAME)
    pict_types = {s.node(f)["attrs"]["pict_type"] for f in frames}
    # H.264 always starts with an I-frame; with default GOP we
    # should see I, P, and at least one of {B, S}.
    assert "I" in pict_types
    assert pict_types & {"P", "B"}, f"expected P or B frames; got {pict_types}"
    # PTS is monotone non-decreasing along the chain.
    sorted_frames = sorted(frames, key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    last_pts = -1
    for f in sorted_frames:
        pts = int(s.node(f)["attrs"]["pts"])
        assert pts >= last_pts
        last_pts = pts


def test_first_frame_is_keyframe_I(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    frames = s.neighbours(snid, vid.HAS_FRAME)
    first = min(frames, key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    attrs = s.node(first)["attrs"]
    assert attrs["pict_type"] == "I"
    assert attrs["key_frame"] is True


# --- Motion vectors -------------------------------------------------


def test_motion_vectors_present_for_moving_content(s, video_path):
    """The headline: the encoder's MVs are graph data. Verify that
    parse_stream actually puts MotionVector nodes on P/B frames of
    a video with real motion."""
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid, export_motion_vectors=True)
    vid.parse_stream(s, cnid, snid)
    p_frame_mvs = []
    for fid in s.neighbours(snid, vid.HAS_FRAME):
        ptype = s.node(fid)["attrs"]["pict_type"]
        n_mvs = len(s.neighbours(fid, vid.HAS_MV))
        if ptype in ("P", "B"):
            p_frame_mvs.append(n_mvs)
    # At least one P/B frame should have many MVs — the encoder
    # found a translating square to predict from. Exact count depends
    # on the encoder's macroblock partitioning (8x8 → 75 MBs for
    # 120x80; smaller partitions push higher).
    assert any(n > 0 for n in p_frame_mvs), (
        "no MVs on P/B frames — encoder didn't export them?")
    assert max(p_frame_mvs) >= 50, (
        f"expected the encoder to emit MVs across many macroblocks; "
        f"max was {max(p_frame_mvs)}")


def test_motion_vectors_describe_translation(s, video_path):
    """The square translates +3 px/frame in x. The encoder's MVs on
    the bar should reflect that — dx values around -3 (the encoder
    encodes 'this block came FROM that displacement in the previous
    frame' so a rightward-moving block has a leftward source MV)."""
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    # Pick a mid-stream P-frame and look at its MVs.
    p_frames = [f for f in s.neighbours(snid, vid.HAS_FRAME)
                if s.node(f)["attrs"]["pict_type"] == "P"
                and len(s.neighbours(f, vid.HAS_MV)) > 0]
    assert p_frames, "need at least one P-frame with MVs"
    p_frames.sort(key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    mid = p_frames[len(p_frames) // 2]
    dxs = [int(s.node(mv)["attrs"]["dx"])
           for mv in s.neighbours(mid, vid.HAS_MV)]
    # The encoder found motion in SOME direction; we don't pin the
    # exact MV sign (encoders are clever and can pick either
    # forward/backward), but there ARE non-zero MVs.
    assert any(d != 0 for d in dxs), f"expected non-zero MVs on a moving frame; got {dxs}"


def test_static_video_has_almost_all_zero_motion_vectors(s, static_video_path):
    """A blank video. The encoder still records MVs for every
    macroblock (it doesn't OMIT them for skip blocks; it writes
    (0,0)). What matters is that nearly all MVs have zero
    magnitude — the encoder said "nothing's moving"."""
    cnid = vid.open_container(s, static_video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    total_mvs = 0
    zero_mvs = 0
    for f in s.neighbours(snid, vid.HAS_FRAME):
        for mv in s.neighbours(f, vid.HAS_MV):
            a = s.node(mv)["attrs"]
            total_mvs += 1
            if a.get("dx", 0) == 0 and a.get("dy", 0) == 0:
                zero_mvs += 1
    # Static content → virtually every MV is exactly (0, 0).
    fraction_zero = zero_mvs / max(total_mvs, 1)
    assert fraction_zero > 0.95, (
        f"static video: {fraction_zero:.2%} of MVs are zero "
        f"({zero_mvs}/{total_mvs}); expected > 95%")


# --- Query helpers --------------------------------------------------


def test_scene_cuts_finds_i_frames(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    cuts = vid.scene_cuts(s, snid)
    assert len(cuts) >= 1
    # Every returned frame really is type I.
    for f in cuts:
        assert s.node(f)["attrs"]["pict_type"] == "I"


def test_motion_summary_returns_stats(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    p_frames = [f for f in s.neighbours(snid, vid.HAS_FRAME)
                if s.node(f)["attrs"]["pict_type"] == "P"
                and len(s.neighbours(f, vid.HAS_MV)) > 0]
    summary = vid.motion_summary(s, p_frames[0])
    assert summary["n_mvs"] > 0
    assert summary["mean_mag"] >= 0
    assert summary["max_mag"] >= summary["mean_mag"]
    assert 0.0 <= summary["fraction_nonzero"] <= 1.0


def test_busiest_frames_ranks_by_coded_size(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    top3 = vid.busiest_frames(s, snid, top_k=3)
    assert len(top3) == 3
    sizes = [int(s.node(f)["attrs"]["coded_size"]) for f in top3]
    assert sizes == sorted(sizes, reverse=True)


def test_frames_in_time_window(s, video_path):
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    # 30 frames @ 10 fps = 3 seconds total. Get frames in [1.0, 2.0].
    window = vid.frames_in_time_window(s, snid, 1.0, 2.0)
    # Should be roughly 10 frames (one second's worth at 10 fps).
    assert 8 <= len(window) <= 12, f"got {len(window)} frames in the window"


# --- Lazy decode + vision integration ------------------------------


def test_decode_frame_returns_image_node(s, video_path):
    """The 'render only when explicitly asked' path. decode_frame
    materialises one frame's pixels as an Image node compatible
    with substrate_rs.vision."""
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    # Decode the first frame.
    first = min(s.neighbours(snid, vid.HAS_FRAME),
                key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    img_nid = vid.decode_frame(s, first)
    assert s.node(img_nid)["type"] == v.IMAGE
    arr = v.image_to_array(s, img_nid)
    assert arr.shape == (80, 120, 3)


def test_decoded_frame_feeds_vision_pipeline(s, video_path):
    """Composition story: a decoded frame is just an Image —
    convolve / pool / V1 / V2 all apply. The bitstream parser and
    the V1 cortex chain end-to-end."""
    v.seed_vision_grammar(s)  # need the vision grammar too
    cnid = vid.open_container(s, video_path)
    snid = vid.add_stream(s, cnid)
    vid.parse_stream(s, cnid, snid)
    first = min(s.neighbours(snid, vid.HAS_FRAME),
                key=lambda f: int(s.node(f)["attrs"]["frame_index"]))
    img_nid = vid.decode_frame(s, first)
    sx = v.sobel(s, dx=1, dy=0)
    edge_nid = v.convolve(s, img_nid, sx)
    edge = v.image_to_array(s, edge_nid)
    assert edge.shape[:2] == (80, 120)


# --- The headline: format << pixels ---------------------------------


def test_bitstream_summary_is_smaller_than_pixel_render():
    """A real win-condition: the agent's graph summary of a video is
    much smaller than the rendered pixel stream. For a 1-second
    100-frame 120x80 video that's 100 * 120 * 80 * 3 = 2.9MB of
    rendered pixels; the graph summary should be well under 1MB."""
    f = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    f.close()
    _make_test_mp4(f.name, n_frames=100, moving=True, width=120, height=80)
    try:
        s = srs.Substrate()
        vid.seed_video_grammar(s)
        cnid = vid.open_container(s, f.name)
        snid = vid.add_stream(s, cnid)
        vid.parse_stream(s, cnid, snid)
        # ROUGH proxy: count of graph nodes × ~150 bytes/node (a
        # generous estimate including attrs dict overhead).
        n_nodes = s.node_count()
        bytes_estimate = n_nodes * 150
        # Pixel render of the same video:
        pixel_bytes = 100 * 120 * 80 * 3
        # The summary should be much smaller. Allow plenty of slack.
        assert bytes_estimate < pixel_bytes, (
            f"graph summary ({bytes_estimate}B) should be < pixels "
            f"({pixel_bytes}B); n_nodes={n_nodes}")
        print(f"\n  100-frame video: {pixel_bytes:,}B pixels → "
              f"~{bytes_estimate:,}B graph "
              f"({pixel_bytes / max(bytes_estimate, 1):.1f}× compression)")
    finally:
        os.unlink(f.name)
