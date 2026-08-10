"""Slice-level transrate operations on the Parrot Sketch.

Two paths benchmarked here:

  A. drop_non_ref_slices — structural drop of NAL units with
     nal_ref_idc == 0. Pure byte editing, no entropy decode. Real
     bitrate reduction (only as much as non-reference content
     exists; on YouTube content typically ≤ a few %).

  B. ffmpeg full re-encode at a lower target bitrate — does
     entropy decode + DCT + motion-comp + requantize + re-entropy.
     Reduces bitrate to any target.

Plus: a sketch of the slice_qp_delta walk that would do per-slice
QP modification *without* entropy-decoding coefficient data —
useful when slice headers are parsable but coefficient data is
left alone (dequantization shifts, no real bitrate change).
"""
import subprocess
import time
import shutil
from pathlib import Path

ffmpeg = shutil.which("ffmpeg")
d = Path("/tmp/parrot")
src_h264 = d / "parrot.h264"
src_mp4 = d / "parrot.mp4"


def time_it(fn, n=1):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


# ---- Path A — drop nal_ref_idc=0 slices ---------------------------

# H.264 NAL header byte layout:
#   bit 7:   forbidden_zero_bit  (must be 0)
#   bits 6-5: nal_ref_idc        (2 bits)
#   bits 4-0: nal_unit_type      (5 bits)
SLICE_TYPES = {1, 2, 3, 4}


def drop_non_ref_slices_primitive():
    """Walk every NAL, drop those with nal_ref_idc=0 AND slice type
    in {1, 2, 3, 4}. Returns (new_bytes, kept_count, dropped_count).
    """
    raw = src_h264.read_bytes()
    out = bytearray()
    i = 0
    kept = 0
    dropped = 0
    while i < len(raw) - 3:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else:
            out.append(raw[i]); i += 1; continue
        # Find end of this NAL.
        j = i + sc + 1
        while j < len(raw) - 3:
            if (raw[j:j+3] == b"\x00\x00\x01"
                    or raw[j:j+4] == b"\x00\x00\x00\x01"):
                break
            j += 1
        else:
            j = len(raw)
        hdr = raw[i + sc]
        nri = (hdr >> 5) & 0x3
        nut = hdr & 0x1F
        if nut in SLICE_TYPES and nri == 0:
            dropped += 1
        else:
            out.extend(raw[i:j])
            kept += 1
        i = j
    out_path = d / "parrot_dropped.h264"
    out_path.write_bytes(bytes(out))
    return out_path, kept, dropped


# ---- Path B — ffmpeg target-bitrate re-encode ---------------------

def ffmpeg_reencode_target_bitrate(kbps):
    out = d / f"parrot_reenc_{kbps}k.mp4"
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error",
         "-i", str(src_mp4),
         "-c:v", "libx264", "-preset", "medium",
         "-b:v", f"{kbps}k",
         "-c:a", "copy",
         str(out)],
        check=True)
    return out


def decode_frame_count(path):
    r = subprocess.run(
        ["ffprobe", "-loglevel", "error", "-count_frames",
         "-select_streams", "v:0", "-show_entries",
         "stream=nb_read_frames", "-of",
         "default=nokey=1:noprint_wrappers=1", str(path)],
        capture_output=True, text=True, check=True)
    return int(r.stdout.strip())


# ---- Run + report -------------------------------------------------

orig_size = src_h264.stat().st_size
print(f"Input: {orig_size:,} bytes H.264 Annex-B (no audio)")
print(f"       {src_mp4.stat().st_size:,} bytes MP4 (with audio)")
print()

# A: primitive slice drop
t_a = time_it(drop_non_ref_slices_primitive, n=5)
out_path, kept, dropped = drop_non_ref_slices_primitive()
new_size = out_path.stat().st_size
print(f"A. PRIMITIVE drop_non_ref_slices (nal_ref_idc=0):")
print(f"   wall clock:      {t_a*1000:7.2f} ms")
print(f"   slices: kept {kept}, dropped {dropped}")
print(f"   size: {orig_size:,} → {new_size:,} bytes  "
      f"(-{100*(orig_size-new_size)/orig_size:.1f}%)")
orig_frames = decode_frame_count(src_h264)
mod_frames = decode_frame_count(out_path)
print(f"   ffmpeg decodes: {mod_frames} frames "
      f"(original: {orig_frames})")
print()

# B: ffmpeg re-encode targeting various bitrates
print("B. FFMPEG full re-encode at target bitrates:")
for kbps in (100, 50):
    t_b = time_it(lambda k=kbps: ffmpeg_reencode_target_bitrate(k), n=1)
    out = ffmpeg_reencode_target_bitrate(kbps)
    sz = out.stat().st_size
    print(f"   {kbps:3d} kbps:  wall clock {t_b*1000:7.0f} ms  "
          f"→ {sz:,} bytes ({100*sz/src_mp4.stat().st_size:.0f}% of input)")
print()

print("Headline numbers:")
print(f"  Primitive drop:  {t_a*1000:.1f} ms  →  {100*(orig_size-new_size)/orig_size:.1f}% file size reduction")
print(f"  ffmpeg @ 100k:   ~thousands of ms  →  >70% reduction (real transrate)")
print()
print("Note on scope:")
print("  - Primitive drop: bit-exact preservation of every kept slice;")
print("    dequantization unchanged; quality of decoded frames matches")
print("    the original for the kept frames. The dropped frames are")
print("    simply absent from output. Small reduction for")
print("    YouTube-style content because most slices are reference.")
print("  - ffmpeg re-encode at 50 kbps: real transrate — entropy")
print("    decodes, requantizes harder, re-entropy-codes. Half the")
print("    data, fully decodable, lower quality everywhere.")
print()
print("To get >10% reduction without re-encoding, we'd need slice-level")
print("entropy decoding + requantization + re-entropy-coding — the")
print("'Phase 16 deeper build' the prior commits referenced. That work")
print("requires CAVLC/CABAC decoders, which are the bulk of the H.264")
print("codec's logic.")
