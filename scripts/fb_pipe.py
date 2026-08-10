#!/usr/bin/env python3
"""fb_pipe.py — universal writer for the jabberwock shm vision contract.

The Rust runtime (`runners/dsl/src/framebuffer.rs`) READS a POSIX
shared-memory framebuffer at its own tick pace: attach, seqlock-style
sample, hand pixels to `Substrate::segment_and_track`. This script is
the WRITER side, and it is deliberately source-agnostic: pipe raw
BGRA8888 frames from ANY process into stdin and this becomes a live
vision feed the agent can perceive — a screen, a webcam, a video file,
an RTSP stream, a game, a synthetic test pattern, whatever produces
pixels.

    <anything producing raw BGRA frames> | fb_pipe.py --width W --height H

## Wire contract (fixed — must match runners/dsl/src/framebuffer.rs)

A POSIX shm object (name e.g. "/jbw_fb_0", visible as
/dev/shm/jbw_fb_0) containing a 64-byte little-endian header followed
immediately by the pixel payload:

    offset  size  field
    0       4     magic       u32 LE  = 0x4A425746 ("JBWF")
    4       4     version     u32 LE  = 1
    8       4     width       u32 LE  (pixels)
    12      4     height      u32 LE  (pixels)
    16      4     stride      u32 LE  (bytes per row, = width*4 here)
    20      4     format      u32 LE  = 1 (BGRA8888)
    24      8     frame_seq   u64 LE  (monotonic; bumped AFTER each
                                        complete frame write)
    32      32    reserved    (zero-filled)
    64      ...   payload: height * stride bytes, row-major BGRA

Writer discipline (seqlock, matches the Rust reader's expectations):
pixels are written FIRST, frame_seq is bumped SECOND, and frame_seq is
NEVER bumped mid-write. Readers compare frame_seq before/after copying
the payload to detect a torn read.

## Why stdin, not a built-in capture backend

This script does not know how to talk to X11, V4L2, or a video
codec — and it shouldn't: keeping capture out-of-process means ANY
tool that can emit a raw BGRA byte stream becomes a valid input, with
no coupling between this writer and a capture library. ffmpeg is the
easiest way to get raw BGRA out of almost anything; see the one-liners
below. `--test-pattern` covers the zero-dependency case (no ffmpeg, no
video source at all) so the whole shm vision path can be smoke-tested
in isolation.

## ffmpeg one-liners

(a) X11 screen capture, a 1280x720 region at offset 100,100 on :0, 30fps:

    ffmpeg -f x11grab -video_size 1280x720 -framerate 30 \\
        -i :0.0+100,100 \\
        -f rawvideo -pix_fmt bgra - \\
      | python3 scripts/fb_pipe.py --name /jbw_fb_0 --width 1280 --height 720

(b) Webcam via V4L2 (Linux), 640x480:

    ffmpeg -f v4l2 -video_size 640x480 -i /dev/video0 \\
        -f rawvideo -pix_fmt bgra - \\
      | python3 scripts/fb_pipe.py --name /jbw_fb_0 --width 640 --height 480

(c) Video file, looped forever, decoded to its native size (probe it
    first with `ffprobe -show_streams file.mp4` for WxH):

    ffmpeg -stream_loop -1 -i file.mp4 \\
        -f rawvideo -pix_fmt bgra - \\
      | python3 scripts/fb_pipe.py --name /jbw_fb_0 --width W --height H

(d) RTSP stream (prefer TCP transport for reliability):

    ffmpeg -rtsp_transport tcp -i rtsp://user:pass@host/stream \\
        -f rawvideo -pix_fmt bgra - \\
      | python3 scripts/fb_pipe.py --name /jbw_fb_0 --width W --height H

In every case, `-f rawvideo -pix_fmt bgra -` is the load-bearing part:
it tells ffmpeg to emit headerless, tightly-packed (stride == width*4)
BGRA8888 frames on stdout with no container framing, which is exactly
what this script expects on stdin. `--fps-cap` on this side is
usually preferable to `-r` on the ffmpeg side when the *reader*'s tick
pace is what actually matters — the reader samples whenever it likes,
so this writer's job is to keep the buffer fresh, not to match any
particular rate.

## Usage

    # Real source, capped publish rate, unlink on exit:
    ffmpeg ... -f rawvideo -pix_fmt bgra - \\
      | python3 scripts/fb_pipe.py --width 640 --height 480 --fps-cap 30 --stats

    # Zero-dependency smoke test, no video source at all:
    python3 scripts/fb_pipe.py --test-pattern --width 160 --height 120 --stats

    # Attach to an object created (and kept) elsewhere:
    python3 scripts/fb_pipe.py --attach --name /jbw_fb_0 --width 640 --height 480 < frames.raw
"""
from __future__ import annotations

import argparse
import mmap
import os
import signal
import struct
import sys
import time

FB_MAGIC = 0x4A425746  # "JBWF"
FB_VERSION = 1
FB_FORMAT_BGRA8888 = 1
FB_HEADER_LEN = 64
SHM_DIR = "/dev/shm"

# offsets into the 64-byte header
_OFF_MAGIC = 0
_OFF_VERSION = 4
_OFF_WIDTH = 8
_OFF_HEIGHT = 12
_OFF_STRIDE = 16
_OFF_FORMAT = 20
_OFF_SEQ = 24


class _Stop(Exception):
    """Raised from a signal handler to unwind a blocking read/sleep cleanly."""


def _normalize_name(name: str) -> tuple[str, str]:
    """Return (contract_name, shm_basename) for a user-supplied --name.

    The contract (and the Rust reader) refers to the object as
    "/jbw_fb_0" (POSIX shm_open convention: a name with a leading
    slash). The actual file that appears is /dev/shm/jbw_fb_0 — POSIX
    shm objects live directly under /dev/shm on Linux, keyed by the
    name with its single leading slash stripped. Accept the name with
    or without a leading slash from the user and normalize both ways.
    """
    basename = name[1:] if name.startswith("/") else name
    if not basename or "/" in basename:
        raise ValueError(f"invalid shm name {name!r}: must be a single path component")
    return "/" + basename, basename


class FbWriter:
    """Owns the shm object + mmap for one framebuffer, writer side."""

    def __init__(self, name: str, width: int, height: int, *, create: bool, keep: bool):
        self.contract_name, self.basename = _normalize_name(name)
        self.width = width
        self.height = height
        self.stride = width * 4
        self.payload_len = self.height * self.stride
        self.total_len = FB_HEADER_LEN + self.payload_len
        self.keep = keep
        self.path = os.path.join(SHM_DIR, self.basename)
        self._fd = None
        self._mm: mmap.mmap | None = None
        self._owns_object = create  # only unlink an object we created, unless attaching also wants unlink
        self._open(create=create)

    def _open(self, *, create: bool) -> None:
        flags = os.O_RDWR | (os.O_CREAT if create else 0)
        fd = os.open(self.path, flags, 0o666)
        try:
            if create:
                os.ftruncate(fd, self.total_len)
            else:
                actual = os.fstat(fd).st_size
                if actual < self.total_len:
                    raise ValueError(
                        f"shm object {self.contract_name!r} ({self.path}) is {actual} "
                        f"bytes, too small for {self.width}x{self.height} BGRA8888 "
                        f"(need {self.total_len})"
                    )
            self._mm = mmap.mmap(fd, self.total_len)
        finally:
            self._fd = fd  # keep fd open for the lifetime of the mapping

        if create:
            self._write_header()

    def _write_header(self) -> None:
        assert self._mm is not None
        header = struct.pack(
            "<IIIIIIQ",
            FB_MAGIC,
            FB_VERSION,
            self.width,
            self.height,
            self.stride,
            FB_FORMAT_BGRA8888,
            0,  # frame_seq starts at 0
        )
        # header is magic..seq = 4*6 + 8 = 32 bytes; pad to 64 with zero reserved
        header = header + b"\x00" * (FB_HEADER_LEN - len(header))
        self._mm[0:FB_HEADER_LEN] = header

    def frame_seq(self) -> int:
        assert self._mm is not None
        return struct.unpack_from("<Q", self._mm, _OFF_SEQ)[0]

    def write_frame(self, payload: bytes) -> None:
        """Write one complete frame: pixels first, THEN bump frame_seq."""
        assert self._mm is not None
        if len(payload) != self.payload_len:
            raise ValueError(f"expected {self.payload_len} payload bytes, got {len(payload)}")
        self._mm[FB_HEADER_LEN:FB_HEADER_LEN + self.payload_len] = payload
        seq = self.frame_seq() + 1
        struct.pack_into("<Q", self._mm, _OFF_SEQ, seq)

    def close(self) -> None:
        if self._mm is not None:
            try:
                self._mm.close()
            except Exception:
                pass
            self._mm = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None
        if self._owns_object and not self.keep:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass


def read_exact(stream, n: int) -> bytes:
    """Read exactly n bytes from a buffered stream, looping over short reads.

    Returns fewer than n bytes only at genuine EOF (a partial trailing
    frame), which the caller discards.
    """
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def gen_test_pattern_frame(width: int, height: int, frame_idx: int) -> bytes:
    """Synthesize one BGRA8888 frame: a colored rectangle moving over a
    contrasting background, a few cells of motion per frame.

    Pure-stdlib (no numpy) so --test-pattern has zero dependencies
    beyond the interpreter itself.
    """
    bg = (40, 40, 40, 255)      # dark gray background (B, G, R, A)
    fg = (60, 180, 255, 255)    # bright orange-ish rectangle

    rect_w = max(4, width // 6)
    rect_h = max(4, height // 6)
    # cells of motion per frame: bounce the rect around a small grid
    step = max(1, width // 32)
    period_x = max(1, (width - rect_w) // step + 1) or 1
    period_y = max(1, (height - rect_h) // step + 1) or 1
    period = 2 * (period_x + period_y)
    t = frame_idx % period if period > 0 else 0

    # walk the rectangle around the perimeter of its travel box (simple,
    # deterministic, visibly moving a few cells per frame)
    if t < period_x:
        x, y = t * step, 0
    elif t < period_x + period_y:
        x, y = (period_x - 1) * step, (t - period_x) * step
    elif t < 2 * period_x + period_y:
        x, y = (period_x - 1 - (t - period_x - period_y)) * step, (period_y - 1) * step
    else:
        x, y = 0, (period_y - 1 - (t - 2 * period_x - period_y)) * step
    x = max(0, min(x, width - rect_w))
    y = max(0, min(y, height - rect_h))

    bg_row = bytes(bg) * width
    fg_px = bytes(fg)
    rows = []
    for row in range(height):
        if y <= row < y + rect_h:
            row_bytes = bytearray(bg_row)
            row_bytes[x * 4:(x + rect_w) * 4] = fg_px * rect_w
            rows.append(bytes(row_bytes))
        else:
            rows.append(bg_row)
    return b"".join(rows)


class StatsLogger:
    def __init__(self, enabled: bool, interval_s: float = 2.0):
        self.enabled = enabled
        self.interval_s = interval_s
        self.written = 0
        self.dropped = 0
        self._last_log_t = time.monotonic()
        self._last_written_at_log = 0

    def note_written(self) -> None:
        self.written += 1
        self._maybe_log()

    def note_dropped(self) -> None:
        self.dropped += 1
        self._maybe_log()

    def _maybe_log(self) -> None:
        if not self.enabled:
            return
        now = time.monotonic()
        elapsed = now - self._last_log_t
        if elapsed >= self.interval_s:
            delta = self.written - self._last_written_at_log
            eff_fps = delta / elapsed if elapsed > 0 else 0.0
            print(
                f"[fb_pipe] written={self.written} dropped={self.dropped} "
                f"effective_fps={eff_fps:.2f}",
                file=sys.stderr,
                flush=True,
            )
            self._last_log_t = now
            self._last_written_at_log = self.written

    def final(self) -> None:
        if not self.enabled:
            return
        print(
            f"[fb_pipe] final: written={self.written} dropped={self.dropped}",
            file=sys.stderr,
            flush=True,
        )


def build_arg_parser() -> argparse.ArgumentParser:
    epilog = __doc__.split("## ffmpeg one-liners", 1)[1]
    epilog = "## ffmpeg one-liners" + epilog
    parser = argparse.ArgumentParser(
        prog="fb_pipe.py",
        description=(
            "Pipe raw BGRA8888 frames from stdin (or a synthetic test pattern) "
            "into a POSIX shared-memory framebuffer per the jabberwock shm "
            "vision contract, so any pixel-producing process becomes a world "
            "the agent can perceive."
        ),
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", default="/jbw_fb_0", help="shm object name (default: /jbw_fb_0)")
    parser.add_argument("--width", type=int, default=None, help="frame width in pixels (required unless --test-pattern)")
    parser.add_argument("--height", type=int, default=None, help="frame height in pixels (required unless --test-pattern)")
    parser.add_argument("--fps-cap", type=float, default=None, dest="fps_cap",
                         help="drop writes to cap the publish rate to at most N fps "
                              "(the reader samples at its own pace, so dropping is "
                              "correct and buffering is not)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--create", action="store_true", help="create the shm object (default)")
    mode.add_argument("--attach", action="store_true", help="attach to an already-existing shm object")
    parser.add_argument("--keep", action="store_true", help="do not unlink the shm object on exit")
    parser.add_argument("--stats", action="store_true", help="log frames written/dropped/effective fps to stderr")
    parser.add_argument("--test-pattern", action="store_true", dest="test_pattern",
                         help="ignore stdin; generate a synthetic moving-rectangle test pattern (~10fps)")
    parser.add_argument("--test-pattern-frames", type=int, default=None, dest="test_pattern_frames",
                         help="stop after N synthetic frames (default: run until interrupted)")
    return parser


def _install_signal_handlers() -> None:
    def _handler(signum, frame):
        raise _Stop()
    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def run_stdin_source(writer: FbWriter, min_interval: float | None, stats: StatsLogger) -> None:
    stdin = sys.stdin.buffer
    frame_size = writer.payload_len
    last_write_t = None
    while True:
        payload = read_exact(stdin, frame_size)
        if len(payload) < frame_size:
            # EOF with (possibly) a partial trailing frame — discard, exit clean.
            break
        now = time.monotonic()
        if min_interval is not None and last_write_t is not None and (now - last_write_t) < min_interval:
            stats.note_dropped()
            continue
        writer.write_frame(payload)
        last_write_t = now
        stats.note_written()


def run_test_pattern_source(writer: FbWriter, fps: float, max_frames: int | None, stats: StatsLogger) -> None:
    interval = 1.0 / fps if fps > 0 else 0.0
    idx = 0
    next_t = time.monotonic()
    while max_frames is None or idx < max_frames:
        payload = gen_test_pattern_frame(writer.width, writer.height, idx)
        writer.write_frame(payload)
        stats.note_written()
        idx += 1
        next_t += interval
        delay = next_t - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            next_t = time.monotonic()


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.test_pattern:
        width = args.width or 160
        height = args.height or 120
    else:
        if args.width is None or args.height is None:
            parser.error("--width and --height are required unless --test-pattern is used")
        width, height = args.width, args.height

    if width <= 0 or height <= 0:
        parser.error("--width and --height must be positive")

    create = not args.attach  # --create is the default; --attach flips it
    min_interval = (1.0 / args.fps_cap) if args.fps_cap else None
    stats = StatsLogger(enabled=args.stats)

    writer = FbWriter(args.name, width, height, create=create, keep=args.keep)
    _install_signal_handlers()
    try:
        if args.test_pattern:
            run_test_pattern_source(writer, fps=10.0, max_frames=args.test_pattern_frames, stats=stats)
        else:
            run_stdin_source(writer, min_interval=min_interval, stats=stats)
    except _Stop:
        pass
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass
    finally:
        stats.final()
        writer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
