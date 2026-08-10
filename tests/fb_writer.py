"""fb_writer — a synthetic BGRA8888 shared-memory framebuffer WRITER,
stdlib only, conforming exactly to the wire contract the Rust reader
(`runners/dsl/src/framebuffer.rs`) implements:

    offset  size  field
    0       4     magic       u32 LE  = 0x4A425746 ("JBWF")
    4       4     version     u32 LE  = 1
    8       4     width       u32 LE  (pixels)
    12      4     height      u32 LE  (pixels)
    16      4     stride      u32 LE  (bytes/row, >= width*4)
    20      4     format      u32 LE  = 1 (BGRA8888)
    24      8     frame_seq   u64 LE  (monotonic; bumped AFTER each
                                       complete frame write)
    32      32    reserved (zero)
    64      ...   payload: height*stride bytes, row-major BGRA

This is the Python stand-in for the browser-side CDP-screencast writer
described in CLAUDE.md ("Python's only job is to keep the buffer
fresh") — used ONLY by tests/test_fb_vision.py to exercise the Rust
reader end-to-end. It is deliberately NOT a `worlds/*` adapter (out of
scope for this primitive's task — the real CDP writer is a separate,
later piece of work); it is test fixture code.

Implementation: a real POSIX shm object, opened the same way
`libc::shm_open` opens one on Linux — as a plain file under
`/dev/shm/<name-without-leading-slash>` (this IS how glibc's
`shm_open` is implemented on Linux; there is no other portable way to
get a byte-identical view without a C extension, and the task
explicitly sanctions "mmap on /dev/shm" as a stdlib-only option).
"""
from __future__ import annotations

import mmap
import os
import struct

MAGIC = 0x4A425746  # "JBWF"
VERSION = 1
FORMAT_BGRA8888 = 1
HEADER_LEN = 64
SHM_DIR = "/dev/shm"

_HEADER_FIELDS = struct.Struct("<IIIIII")  # magic,version,width,height,stride,format
_SEQ_FIELD = struct.Struct("<Q")


class FbWriter:
    """Owns a POSIX shm object at `/dev/shm/<name.lstrip('/')>` and
    writes BGRA8888 frames per the contract above. `name` should
    include the leading `/` the POSIX `shm_open` convention expects
    (e.g. `"/jbw_fb_test_1"`) — pass the SAME string to the Rust side's
    `Substrate.fb_attach(name)`.
    """

    def __init__(self, name: str, width: int, height: int):
        if not name.startswith("/"):
            raise ValueError("shm name must start with '/' (POSIX shm_open convention)")
        self.name = name
        self.width = width
        self.height = height
        self.stride = width * 4
        self.payload_len = height * self.stride
        self.total_len = HEADER_LEN + self.payload_len
        self._path = os.path.join(SHM_DIR, name.lstrip("/"))
        fd = os.open(self._path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.ftruncate(fd, self.total_len)
            self._mmap = mmap.mmap(fd, self.total_len)
        finally:
            os.close(fd)
        self.frame_seq = 0
        self._write_static_header()
        # Zero the payload + seq explicitly (ftruncate on a fresh file
        # already zero-fills, but a REUSED stale path from a prior run
        # might not start clean).
        self._mmap[HEADER_LEN:self.total_len] = bytes(self.payload_len)
        self._mmap[24:32] = _SEQ_FIELD.pack(0)

    def _write_static_header(self) -> None:
        self._mmap[0:24] = _HEADER_FIELDS.pack(
            MAGIC, VERSION, self.width, self.height, self.stride, FORMAT_BGRA8888
        )

    def write_frame(self, pixels: bytes) -> int:
        """`pixels` must be exactly `height*stride` bytes, row-major
        BGRA8888. Writes the payload FIRST, then bumps + stores
        `frame_seq` LAST — the writer half of the seqlock discipline
        the Rust reader depends on. Returns the new frame_seq."""
        if len(pixels) != self.payload_len:
            raise ValueError(
                f"write_frame: expected {self.payload_len} bytes, got {len(pixels)}"
            )
        self._mmap[HEADER_LEN:HEADER_LEN + self.payload_len] = pixels
        self.frame_seq += 1
        self._mmap[24:32] = _SEQ_FIELD.pack(self.frame_seq)
        return self.frame_seq

    def solid_frame(self, bg_bgr: tuple[int, int, int],
                     rect: tuple[int, int, int, int] | None = None,
                     rect_bgr: tuple[int, int, int] | None = None) -> bytearray:
        """Build (but don't write) a payload: solid `bg_bgr` background,
        optionally with one solid-colour rectangle `rect = (x0, y0, w, h)`
        (pixel coords) painted in `rect_bgr`. Returns the bytearray so a
        caller can write_frame it (or mutate it further, e.g. to move
        the rectangle across frames)."""
        bg_px = bytes((*bg_bgr, 255))
        row = bg_px * self.width
        buf = bytearray(row * self.height)
        if rect is not None:
            assert rect_bgr is not None
            rx0, ry0, rw, rh = rect
            rect_px = bytes((*rect_bgr, 255))
            for y in range(max(ry0, 0), min(ry0 + rh, self.height)):
                row_off = y * self.stride
                for x in range(max(rx0, 0), min(rx0 + rw, self.width)):
                    p = row_off + x * 4
                    buf[p:p + 4] = rect_px
        return buf

    def close(self, unlink: bool = True) -> None:
        self._mmap.close()
        if unlink:
            try:
                os.unlink(self._path)
            except FileNotFoundError:
                pass

    def __enter__(self) -> "FbWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
