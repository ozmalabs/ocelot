"""test_live_eye — stage 3, end-to-end: the ACTUAL product artifact
(`scripts/fb_pipe.py`) run as a real subprocess, writing into a JBWF
shared-memory buffer that `Substrate.fb_attach`/`fb_sample` (the Rust
eye) reads and segments -- standalone of `worlds/browser.py`'s CDP
screencast writer (`worlds/browser.py`'s `_start_live_eye` is the SAME
consumer side of this exact contract; this file proves the contract
itself against the real writer script rather than a bespoke Python
stand-in, which is what `tests/test_fb_vision.py` uses via
`tests/fb_writer.py`).

Covers:
  (a) the moving-rectangle test pattern (`fb_pipe.py --test-pattern`'s
      `gen_test_pattern_frame`) is tracked as ONE persistent Region node
      identity across >= 5 samples as it moves -- the same cross-frame
      identity assertion as
      `test_fb_vision.py::test_fb_sample_tracks_moving_rect_as_same_region_identity`,
      but driving the real subprocess writer instead of a raw `FbWriter`.
  (b) once the writer is stopped, a repeated `fb_sample` on an unchanged
      `frame_seq` fast-paths to `unchanged: True` with no new Region
      churn -- same fast path, same subprocess-driven proof.
  (c) BEST-EFFORT bonus: if a real `/dev/video0` capture device is
      present and readable AND `ffmpeg` is on PATH, attempt one short
      real webcam frame through the same pipeline. This does not gate
      the suite -- skipped (not failed) on any unavailability/error, per
      the task spec ("not required to pass/assert anything strong").

Skips the WHOLE FILE if `/dev/shm` isn't a writable directory (no POSIX
shm on this platform/sandbox) -- same requirement `tests/test_fb_vision.py`
has, just checked directly here since this file drives a real subprocess
writer rather than importing a fixture that already assumes it.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time

import pytest

pytest.importorskip("substrate_rs")

if not os.path.isdir("/dev/shm") or not os.access("/dev/shm", os.W_OK):
    pytest.skip("no writable /dev/shm on this platform -- POSIX shm unavailable",
                allow_module_level=True)

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGION_GROUPING_SEED = os.path.join(ROOT, "seeds", "region_grouping.json")
FB_PIPE = os.path.join(ROOT, "scripts", "fb_pipe.py")

# Small-but-nontrivial: meaningful segmentation, fast to sample/tick.
GRID_W, GRID_H = 32, 24


def _fresh():
    """A core-booted WorldAdapter carrying ONLY the region_grouping seed
    (the generic WorldInstance->Region Γ productions fb_sample's
    has_region/within edges need to admit) -- mirrors
    tests/test_fb_vision.py's fixture exactly."""
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(REGION_GROUPING_SEED)), None)
    return wa


def _mk_game(wa):
    return wa.s.add_node("WorldInstance", {"world_type": "Game", "frame": 0.0})


def _non_ground_regions(wa):
    out = []
    for nid in wa.inner.nodes("Region"):
        a = wa.inner.node(nid)["attrs"]
        if a.get("is_ground"):
            continue
        out.append({
            "id": nid,
            "minr": int(a["minr"]), "minc": int(a["minc"]),
            "maxr": int(a["maxr"]), "maxc": int(a["maxc"]),
        })
    return out


def _shm_name(tag: str) -> str:
    return f"/jbw_fb_live_eye_test_{tag}_{os.getpid()}"


def _wait_for_first_frame(wa, name, game, timeout_s=8.0):
    """Poll fb_attach + fb_sample until the writer SUBPROCESS (not yet
    guaranteed to have even started its event loop) has produced at
    least one real frame (frame_seq > 0). Process startup + first frame
    write isn't instantaneous -- retry both the attach (the shm object
    may not exist yet) and the sample (frame_seq starts at 0)."""
    deadline = time.monotonic() + timeout_s
    fb_id = None
    last_result = None
    while time.monotonic() < deadline:
        if fb_id is None:
            try:
                fb_id = wa.inner.fb_attach(name)
            except ValueError:
                time.sleep(0.05)
                continue
        last_result = wa.inner.fb_sample(fb_id, game, GRID_W, GRID_H)
        if last_result["frame_seq"] > 0:
            return fb_id
        time.sleep(0.05)
    raise TimeoutError(
        f"no frame from {name!r} within {timeout_s}s (last_result={last_result})")


# --------------------------------------------------------------------------
# (a) + (b) real fb_pipe.py subprocess -> moving-rect tracking + unchanged
#     fast path once stopped.
# --------------------------------------------------------------------------

def test_fb_pipe_subprocess_tracks_moving_rect_then_goes_unchanged_when_stopped():
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("moving")
    proc = subprocess.Popen(
        [sys.executable, FB_PIPE, "--test-pattern", "--name", name,
         "--width", str(GRID_W), "--height", str(GRID_H)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fb_id = None
    try:
        fb_id = _wait_for_first_frame(wa, name, game)

        # --- (a): sample repeatedly while the rectangle moves; collect
        # >= 5 DISTINCT frames, each with exactly one tracked figure
        # region, and confirm it's the SAME Region node identity every
        # time (the actual point of segment_and_track), while its bbox
        # genuinely moves.
        samples = []
        last_seq = -1
        attempts = 0
        while len(samples) < 5 and attempts < 400:
            attempts += 1
            result = wa.inner.fb_sample(fb_id, game, GRID_W, GRID_H)
            if result["unchanged"] or result["frame_seq"] == last_seq:
                time.sleep(0.02)
                continue
            last_seq = result["frame_seq"]
            figures = _non_ground_regions(wa)
            samples.append((result["frame_seq"], figures))
            time.sleep(0.02)

        assert len(samples) >= 5, (
            f"only observed {len(samples)} distinct frames from the "
            f"fb_pipe.py subprocess within the attempt budget"
        )

        ids_seen = set()
        bboxes_seen = set()
        for seq, figures in samples:
            assert len(figures) == 1, (
                f"expected exactly 1 tracked figure region at frame_seq={seq}, "
                f"got {figures}"
            )
            ids_seen.add(str(figures[0]["id"]))
            bboxes_seen.add((figures[0]["minr"], figures[0]["minc"],
                              figures[0]["maxr"], figures[0]["maxc"]))

        # THE cross-frame identity assertion: one persistent Region node,
        # not a birth+death pair per frame.
        assert len(ids_seen) == 1, (
            f"the moving rectangle should track as ONE persistent Region "
            f"identity across samples, got distinct ids {ids_seen}"
        )
        # And it actually moved (not the same bbox every sample).
        assert len(bboxes_seen) >= 2, (
            f"expected the tracked rectangle's bbox to move across samples, "
            f"got only {bboxes_seen}"
        )

        # --- (b): stop the writer, confirm the fast path fires on a
        # frame_seq that's no longer advancing, with no new Region churn.
        proc.terminate()
        proc.wait(timeout=5)

        # One more sample to pick up whatever the writer's LAST frame
        # was (it may have written between our last sample and the
        # terminate() call above) -- this one may legitimately still
        # report unchanged=False.
        settle = wa.inner.fb_sample(fb_id, game, GRID_W, GRID_H)
        region_count_after_settle = len(wa.inner.nodes("Region"))

        # No further writes are possible (the process is gone) -- every
        # subsequent sample at the SAME frame_seq must fast-path.
        for _ in range(5):
            again = wa.inner.fb_sample(fb_id, game, GRID_W, GRID_H)
            assert again["unchanged"] is True
            assert again["frame_seq"] == settle["frame_seq"]
        assert len(wa.inner.nodes("Region")) == region_count_after_settle
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if fb_id is not None:
            try:
                wa.inner.fb_detach(fb_id)
            except Exception:  # noqa: BLE001 -- best-effort teardown
                pass
        # fb_pipe.py (no --keep) unlinks its own shm object on clean
        # exit (SIGTERM -> _Stop -> finally: writer.close()); this is a
        # best-effort backstop in case that didn't happen (e.g. it was
        # force-killed above).
        try:
            os.unlink(os.path.join("/dev/shm", name.lstrip("/")))
        except FileNotFoundError:
            pass


# --------------------------------------------------------------------------
# (c) BEST-EFFORT bonus: a real webcam frame through the same pipeline,
# if a capture device + ffmpeg are actually available. Never fails the
# suite -- skips on any unavailability or error.
# --------------------------------------------------------------------------

def test_bonus_real_webcam_capture_if_available():
    device = "/dev/video0"
    if not (os.path.exists(device) and os.access(device, os.R_OK)):
        pytest.skip(f"{device} not present/readable -- no real capture device to test")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not on PATH -- can't decode the webcam to raw BGRA")

    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("webcam")
    w, h = 320, 240
    ffmpeg_proc = None
    fb_pipe_proc = None
    fb_id = None
    try:
        # One short real capture, piped straight into fb_pipe.py per the
        # module's own documented one-liner (fb_pipe.py's docstring,
        # case (b)) -- `-frames:v` caps it so this can't hang forever.
        ffmpeg_proc = subprocess.Popen(
            [ffmpeg, "-f", "v4l2", "-video_size", f"{w}x{h}", "-i", device,
             "-frames:v", "30", "-f", "rawvideo", "-pix_fmt", "bgra", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        fb_pipe_proc = subprocess.Popen(
            [sys.executable, FB_PIPE, "--name", name, "--width", str(w), "--height", str(h)],
            cwd=ROOT, stdin=ffmpeg_proc.stdout, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ffmpeg_proc.stdout.close()  # let ffmpeg see SIGPIPE if fb_pipe exits first

        fb_id = _wait_for_first_frame(wa, name, game, timeout_s=8.0)
        result = wa.inner.fb_sample(fb_id, game, GRID_W, GRID_H)
        assert result["frame_seq"] > 0
        # Not asserting anything about content -- a real camera in a
        # sandboxed/headless environment may just show a black frame or
        # test-card noise. The point is only "the real capture path
        # doesn't crash the pipeline," which the assert above already
        # proves (a valid sample was taken).
    except (TimeoutError, OSError, subprocess.SubprocessError) as e:
        pytest.skip(f"real webcam capture unavailable/failed in this sandbox: {e}")
    finally:
        for proc in (fb_pipe_proc, ffmpeg_proc):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        if fb_id is not None:
            try:
                wa.inner.fb_detach(fb_id)
            except Exception:  # noqa: BLE001
                pass
        try:
            os.unlink(os.path.join("/dev/shm", name.lstrip("/")))
        except FileNotFoundError:
            pass
