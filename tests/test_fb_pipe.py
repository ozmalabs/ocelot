"""Tests for scripts/fb_pipe.py — the universal shm-framebuffer writer.

No ffmpeg dependency: frames are synthesized in-process and piped to
fb_pipe.py's stdin; the read side reopens the shm object with a plain
mmap (mirroring, but not depending on, the Rust reader in
runners/dsl/src/framebuffer.rs) to check header fields, frame_seq
monotonicity, and payload correctness.
"""
from __future__ import annotations

import mmap
import os
import signal
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FB_PIPE = REPO_ROOT / "scripts" / "fb_pipe.py"
SHM_DIR = Path("/dev/shm")

FB_MAGIC = 0x4A425746
FB_VERSION = 1
FB_FORMAT_BGRA8888 = 1
FB_HEADER_LEN = 64
OFF_SEQ = 24


def unique_name() -> str:
    return f"jbw_fb_test_{uuid.uuid4().hex[:12]}"


def shm_path(name: str) -> Path:
    return SHM_DIR / name.lstrip("/")


def start_writer(name: str, *extra_args: str, stdin_pipe: bool = True) -> subprocess.Popen:
    cmd = [sys.executable, str(FB_PIPE), "--name", name, *extra_args]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if stdin_pipe else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
    )


def wait_for_file(path: Path, min_size: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size >= min_size:
            return
        time.sleep(0.02)
    raise TimeoutError(f"{path} did not appear with size >= {min_size} within {timeout}s")


def wait_for_gone(path: Path, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not path.exists():
            return
        time.sleep(0.02)
    raise TimeoutError(f"{path} still present after {timeout}s")


class ShmReader:
    """Plain-mmap read side used only by tests (not the Rust reader)."""

    def __init__(self, path: Path, total_len: int):
        self.total_len = total_len
        self._fd = os.open(str(path), os.O_RDONLY)
        self._mm = mmap.mmap(self._fd, total_len, prot=mmap.PROT_READ)

    def header(self) -> dict:
        magic, version, width, height, stride, fmt, seq = struct.unpack_from(
            "<IIIIIIQ", self._mm, 0
        )
        return dict(magic=magic, version=version, width=width, height=height,
                    stride=stride, format=fmt, frame_seq=seq)

    def seq(self) -> int:
        return struct.unpack_from("<Q", self._mm, OFF_SEQ)[0]

    def payload(self, payload_len: int) -> bytes:
        return bytes(self._mm[FB_HEADER_LEN:FB_HEADER_LEN + payload_len])

    def close(self) -> None:
        self._mm.close()
        os.close(self._fd)


def make_frame(width: int, height: int, byte_value: int) -> bytes:
    return bytes([byte_value & 0xFF]) * (width * height * 4)


@pytest.fixture
def cleanup_paths():
    paths: list[Path] = []
    yield paths
    for p in paths:
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def test_header_fields_correct(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 8, 8
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    proc = start_writer(name, "--width", str(width), "--height", str(height))
    try:
        wait_for_file(path, total_len)
        reader = ShmReader(path, total_len)
        try:
            hdr = reader.header()
            assert hdr["magic"] == FB_MAGIC
            assert hdr["version"] == FB_VERSION
            assert hdr["width"] == width
            assert hdr["height"] == height
            assert hdr["stride"] == width * 4
            assert hdr["format"] == FB_FORMAT_BGRA8888
            assert hdr["frame_seq"] == 0
        finally:
            reader.close()
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)
    assert proc.returncode == 0


def test_frame_seq_monotonic_and_payload_consistent(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 8, 8
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len
    n_frames = 20

    proc = start_writer(name, "--width", str(width), "--height", str(height))
    try:
        wait_for_file(path, total_len)
        reader = ShmReader(path, total_len)
        try:
            observed_seqs = []
            last_seq = 0
            for i in range(n_frames):
                byte_value = i + 1  # this frame's payload is uniform byte (i+1)
                frame = make_frame(width, height, byte_value)
                proc.stdin.write(frame)
                proc.stdin.flush()
                time.sleep(0.02)  # slow writer: give the reader room to sample

                # Wait for this frame's seq to land (bounded).
                deadline = time.monotonic() + 2.0
                while reader.seq() < i + 1 and time.monotonic() < deadline:
                    time.sleep(0.005)

                # Seqlock-style sample: before/after must match for a
                # coherent read; when they do, the payload byte value
                # must equal the observed seq (frames are written in
                # order, one write per seq value here — no fps cap).
                seq_before = reader.seq()
                payload = reader.payload(payload_len)
                seq_after = reader.seq()
                if seq_before == seq_after and seq_before > 0:
                    expected_byte = seq_before & 0xFF
                    assert payload == bytes([expected_byte]) * payload_len, (
                        f"payload mismatch at seq={seq_before}"
                    )
                observed_seqs.append(seq_after)
                assert seq_after >= last_seq, "frame_seq must never go backwards"
                last_seq = seq_after

            assert observed_seqs[-1] >= n_frames - 1  # allow for timing slop on the very last sample
        finally:
            reader.close()
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)
    assert proc.returncode == 0


def test_unlink_on_exit_default(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 4, 4
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    proc = start_writer(name, "--width", str(width), "--height", str(height))
    wait_for_file(path, total_len)
    proc.stdin.write(make_frame(width, height, 7))
    proc.stdin.close()
    proc.wait(timeout=5)
    assert proc.returncode == 0
    wait_for_gone(path)


def test_keep_flag_preserves_object(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 4, 4
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    proc = start_writer(name, "--width", str(width), "--height", str(height), "--keep")
    wait_for_file(path, total_len)
    proc.stdin.write(make_frame(width, height, 3))
    proc.stdin.close()
    proc.wait(timeout=5)
    assert proc.returncode == 0
    assert path.exists(), "--keep must preserve the shm object after exit"

    reader = ShmReader(path, total_len)
    try:
        assert reader.header()["frame_seq"] == 1
    finally:
        reader.close()
    # cleanup_paths fixture removes the file afterwards


def test_attach_writes_into_existing_object(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 4, 4
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    creator = start_writer(name, "--width", str(width), "--height", str(height), "--keep")
    wait_for_file(path, total_len)
    creator.stdin.write(make_frame(width, height, 1))
    creator.stdin.flush()
    time.sleep(0.1)
    creator.terminate()
    creator.wait(timeout=5)
    assert path.exists(), "creator used --keep, object must survive"

    reader = ShmReader(path, total_len)
    seq_after_creator = reader.header()["frame_seq"]
    reader.close()
    assert seq_after_creator == 1

    attacher = start_writer(name, "--width", str(width), "--height", str(height), "--attach")
    try:
        attacher.stdin.write(make_frame(width, height, 2))
        attacher.stdin.close()
        attacher.wait(timeout=5)
        assert attacher.returncode == 0
    finally:
        pass

    # attach mode does not own the object; it must still be present.
    assert path.exists()
    reader2 = ShmReader(path, total_len)
    try:
        hdr = reader2.header()
        # seq continues from where the creator left off (attach does not reset).
        assert hdr["frame_seq"] == seq_after_creator + 1
        assert reader2.payload(payload_len) == make_frame(width, height, 2)
    finally:
        reader2.close()


def test_partial_trailing_frame_handled_gracefully(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 4, 4
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    proc = start_writer(name, "--width", str(width), "--height", str(height))
    wait_for_file(path, total_len)
    proc.stdin.write(make_frame(width, height, 1))
    proc.stdin.write(make_frame(width, height, 2))
    proc.stdin.write(make_frame(width, height, 3))
    proc.stdin.write(b"\x99" * (payload_len // 2))  # partial trailing frame
    proc.stdin.close()
    proc.wait(timeout=5)

    assert proc.returncode == 0, "partial trailing frame at EOF must not crash the writer"


def test_test_pattern_mode_bounded_frames(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 8, 8
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    proc = start_writer(
        name, "--width", str(width), "--height", str(height),
        "--test-pattern", "--test-pattern-frames", "5",
        stdin_pipe=False,
    )
    proc.wait(timeout=10)
    assert proc.returncode == 0
    # default (no --keep): object should be gone after exit.
    wait_for_gone(path)


def test_test_pattern_mode_signal_terminates_and_cleans_up(cleanup_paths):
    name = unique_name()
    path = shm_path(name)
    cleanup_paths.append(path)
    width, height = 8, 8
    payload_len = width * height * 4
    total_len = FB_HEADER_LEN + payload_len

    proc = start_writer(
        name, "--width", str(width), "--height", str(height), "--test-pattern",
        stdin_pipe=False,
    )
    try:
        wait_for_file(path, total_len)
        reader = ShmReader(path, total_len)
        try:
            hdr = reader.header()
            assert hdr["magic"] == FB_MAGIC
            assert hdr["width"] == width
            assert hdr["height"] == height
            # Let a few frames land.
            deadline = time.monotonic() + 3.0
            while reader.seq() < 2 and time.monotonic() < deadline:
                time.sleep(0.02)
            assert reader.seq() >= 1, "test-pattern mode should be producing frames"
        finally:
            reader.close()
    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)

    assert proc.returncode == 0
    wait_for_gone(path)


def test_width_height_required_without_test_pattern():
    proc = subprocess.run(
        [sys.executable, str(FB_PIPE), "--name", unique_name()],
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
        timeout=5,
    )
    assert proc.returncode != 0
    assert b"required" in proc.stderr.lower() or b"width" in proc.stderr.lower()


def test_help_epilog_mentions_ffmpeg_examples():
    proc = subprocess.run(
        [sys.executable, str(FB_PIPE), "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
        timeout=5,
    )
    assert proc.returncode == 0
    out = proc.stdout.decode()
    assert "x11grab" in out
    assert "v4l2" in out
    assert "rtsp" in out.lower()
    assert "rawvideo" in out
