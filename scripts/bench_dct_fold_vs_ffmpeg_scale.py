"""DCT-domain 2:1 fold vs ffmpeg pixel-domain scale.

Measures the H.264 DCT-domain 4-to-1 fold primitive and
compares against ffmpeg's pixel-domain scale filter and against
ffmpeg's full decode->scale->encode transcode pipeline.

Result preview (12-core, June 2026):

  Our fold (4K -> 1080p, one luma plane):  ~35 ms
  ffmpeg scale filter (single-frame call): 36-58 ms (incl. startup)
  ffmpeg full transcode 60 frames 4K->1080p: ~10 ms/frame

The honest finding: ffmpeg's full decode-scale-encode pipeline
is FASTER than our DCT fold alone. libx264 + libswscale are
heavily optimised (SIMD, multi-threaded, vectorised); our fold
is unoptimised f64 scalar Rust. The "skip decode/encode"
architectural advantage doesn't materialise when libx264 turns
those steps into nearly-free SIMD operations.

Where DCT-domain processing IS expected to win:
  - GPU encode pipelines where decode/re-encode crosses the
    PCIe boundary (DCT rewrite stays on host)
  - Energy: no entropy coding work
  - Live streams where re-encode adds latency
  - Bit-exact provenance: input coefficients pass through
    unchanged at the same spatial location

None of those show up in single-machine CPU wall-clock. This
benchmark documents that.
"""
import shutil
import subprocess
import time
from pathlib import Path

from substrate_rs._native import Substrate


def time_our_fold(n_output_blocks: int) -> float:
    """Time the fold over `n_output_blocks` output 4x4 blocks.
    Each fold consumes 4 input blocks.

    Uses the in-Rust benchmark function so the per-block call
    overhead is bounded.
    """
    s = Substrate()
    return s.h264_dct_fold_bench(n_output_blocks, True)


def time_our_fold_via_python_list(n_output_blocks: int) -> float:
    """Time the fold including Python-side list construction.

    This is the realistic "Python caller" path: build the input
    list, marshal across FFI, fold, marshal back. Useful as a
    floor when the surrounding pipeline is in Python.
    """
    s = Substrate()
    # Realistic input: low-frequency-dominated coefficients.
    one_block = [120, -10, 5, 0,  -8, 6, 1, 0,  2, 1, 0, 0,  0, 0, 0, 0]
    coefs = (one_block * 4) * n_output_blocks
    t = time.perf_counter()
    out = s.h264_dct_fold_many(coefs)
    elapsed = time.perf_counter() - t
    assert len(out) == n_output_blocks * 16
    return elapsed


def time_ffmpeg_scale(scaler: str) -> float:
    """Time ffmpeg downscaling a synthetic 4K YUV frame to 1080p.

    Synthetic frame avoids the need to download Big Buck Bunny
    just for the scale-filter throughput number. Uses lavfi
    `color` source -> scale -> rawvideo sink.
    """
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc=size=3840x2160:rate=1:duration=1",
        "-vf", f"scale=1920:1080:flags={scaler}",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-",
    ]
    # Time the whole call; ffmpeg startup is fixed cost, but
    # for a single-frame run it dominates. Repeat to amortise.
    runs = 3
    times = []
    for _ in range(runs):
        t = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, check=True)
        times.append(time.perf_counter() - t)
        # Sanity: 1080p YUV420p = 1920*1080*1.5 bytes
        assert len(proc.stdout) == int(1920 * 1080 * 1.5), \
            f"unexpected ffmpeg output size {len(proc.stdout)}"
    return min(times)


def main() -> None:
    # One 4K luma plane downscaled to 1080p:
    #   1080p output = 1920*1080 = 2,073,600 samples
    #   = 129,600 4x4 output blocks
    N_OUT_BLOCKS_1080P = (1920 // 4) * (1080 // 4)
    # 1080p -> 540p:
    N_OUT_BLOCKS_540P = (960 // 4) * (540 // 4)

    print("DCT-domain fold throughput vs ffmpeg scale filter")
    print("=" * 60)

    print(f"\n[1] Our fold: 4K luma plane -> 1080p luma plane")
    print(f"    {N_OUT_BLOCKS_1080P:,} output 4x4 blocks "
          f"({N_OUT_BLOCKS_1080P * 4:,} input blocks)")
    runs = 5
    times = [time_our_fold(N_OUT_BLOCKS_1080P) for _ in range(runs)]
    avg = sum(times) / len(times)
    print(f"    pure-Rust fold:        {avg*1000:7.2f} ms "
          f"(min {min(times)*1000:.2f}, max {max(times)*1000:.2f})")
    py_time = time_our_fold_via_python_list(N_OUT_BLOCKS_1080P)
    print(f"    Python-list path:      {py_time*1000:7.2f} ms")

    print(f"\n[2] Our fold: 1080p luma plane -> 540p luma plane")
    print(f"    {N_OUT_BLOCKS_540P:,} output 4x4 blocks")
    times2 = [time_our_fold(N_OUT_BLOCKS_540P) for _ in range(runs)]
    avg2 = sum(times2) / len(times2)
    print(f"    pure-Rust fold:        {avg2*1000:7.2f} ms "
          f"(min {min(times2)*1000:.2f}, max {max(times2)*1000:.2f})")

    if shutil.which("ffmpeg"):
        print(f"\n[3] ffmpeg scale filter: 4K -> 1080p, single frame")
        for scaler in ("neighbor", "bilinear", "bicubic", "lanczos"):
            t = time_ffmpeg_scale(scaler)
            print(f"    -vf scale flags={scaler:9s}: {t*1000:7.2f} ms")

        print(f"\n[3b] ffmpeg scale filter: 1080p -> 540p, single frame")
        for scaler in ("neighbor", "bilinear", "bicubic", "lanczos"):
            # 1080p -> 540p uses a different lavfi source.
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i",
                "testsrc=size=1920x1080:rate=1:duration=1",
                "-vf", f"scale=960:540:flags={scaler}",
                "-frames:v", "1",
                "-f", "rawvideo", "-pix_fmt", "yuv420p", "-",
            ]
            t = time.perf_counter()
            subprocess.run(cmd, capture_output=True, check=True)
            elapsed = time.perf_counter() - t
            print(f"    -vf scale flags={scaler:9s}: {elapsed*1000:7.2f} ms")
    else:
        print("\nffmpeg not on PATH — skipping ffmpeg portion.")

    # End-to-end transcode comparison on a synthesised clip.
    if shutil.which("ffmpeg"):
        clip = Path("/tmp/bbb_bench/synth_4k_60f.mp4")
        clip.parent.mkdir(parents=True, exist_ok=True)
        if not clip.exists():
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i",
                "testsrc=size=3840x2160:rate=30:duration=2",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                str(clip),
            ], check=True)
        print(f"\n[4] ffmpeg full transcode: 4K -> 1080p H.264, "
              f"60 frames @ 30fps")
        for scaler in ("bilinear", "bicubic", "lanczos"):
            t = time.perf_counter()
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(clip),
                "-vf", f"scale=1920:1080:flags={scaler}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                f"/tmp/bbb_bench/out_1080p_{scaler}.mp4",
            ], check=True)
            wall = time.perf_counter() - t
            per_frame_ms = wall * 1000 / 60
            print(f"    scale={scaler:9s} wall={wall*1000:7.2f} ms  "
                  f"per-frame={per_frame_ms:5.2f} ms")

    print("\n" + "=" * 60)
    print("Honest reading: ffmpeg's full transcode at ~10ms/frame is")
    print("FASTER than our fold-math alone at ~35ms/frame. libx264 +")
    print("libswscale are SIMD/multi-threaded; we are scalar Rust f64.")
    print("DCT-domain wins are architectural (no decode/encode round,")
    print("no entropy coding work, GPU pipeline integration) — not raw")
    print("CPU throughput. The fold is built; making it competitive is")
    print("its own arc (SIMD matvec, i32 fixed-point, sparse-aware).")


if __name__ == "__main__":
    main()
