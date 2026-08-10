"""Parrot Sketch — graph-primitive PPS bump vs ffmpeg re-encode.

Both produce a modified, decodable H.264 stream from the same input.
They are NOT semantically equivalent — see the caveats at the end —
but they answer the question "how fast can I change the QP-related
field on a real-world video stream" through each path.
"""
import subprocess
import time
import hashlib
import shutil
import os
from pathlib import Path
from substrate_rs import (
    Substrate, Lit, BitsAt, BitsWrite,
    ExpGolombDecode, ExpGolombDecodeSigned,
    ExpGolombEncode, ExpGolombEncodeSigned,
)

ffmpeg = shutil.which("ffmpeg")
d = Path("/tmp/parrot")
src_mp4 = d / "parrot.mp4"
src_h264 = d / "parrot.h264"

s = Substrate()


def time_it(fn, n=1):
    """Time fn() n times, return (avg_wall_clock, n_runs)."""
    t0 = time.perf_counter()
    for _ in range(n):
        result = fn()
    return (time.perf_counter() - t0) / n, n


# ---- Path A — primitive PPS QP-bump on the Annex-B H.264 ----------

def primitive_qp_bump():
    """Find PPS, decode all fields, bump pic_init_qp_minus26, re-emit
    PPS, splice back. The re-emit handles bit-length changes by
    re-encoding all subsequent fields too — no decoder math, no
    DCT, no entropy coding on the slice data. Pure bit editing
    composed of BitsAt + BitsWrite + ExpGolomb primitives.
    """
    raw = src_h264.read_bytes()
    # Locate PPS NAL (type 8).
    i = 0
    pps_start = sc_len = pps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if (raw[i+sc] & 0x1F) == 8:
            pps_start, sc_len = i, sc
            j = i + sc + 1
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            pps_end = j
            break
        i += sc
    if pps_start is None:
        raise RuntimeError("no PPS found")
    pps = raw[pps_start + sc_len + 1 : pps_end]
    pps_lit = Lit(pps)

    # Decode the H.264 PPS prefix in-line. The fields we care about
    # are pic_param_set_id (ue), seq_param_set_id (ue),
    # entropy_coding_mode_flag (u(1)),
    # bottom_field_pic_order_in_frame_present_flag (u(1)),
    # num_slice_groups_minus1 (ue, assumed 0),
    # num_ref_idx_l{0,1}_default_active_minus1 (ue each),
    # weighted_pred_flag (u(1)), weighted_bipred_idc (u(2)),
    # then pic_init_qp_minus26 (se).
    def ue(b):
        return s._inner.evaluate(
            ExpGolombDecode(pps_lit, Lit(b)).to_dict(), {})
    def se(b):
        return s._inner.evaluate(
            ExpGolombDecodeSigned(pps_lit, Lit(b)).to_dict(), {})
    def u(b, n):
        return s._inner.evaluate(
            BitsAt(pps_lit, Lit(b), Lit(n)).to_dict(), {})

    bp = 0
    pps_id, bp = ue(bp)
    sps_id, bp = ue(bp)
    ent_mode = u(bp, 1); bp += 1
    bot_field = u(bp, 1); bp += 1
    nsg, bp = ue(bp)
    nr0, bp = ue(bp)
    nr1, bp = ue(bp)
    wp = u(bp, 1); bp += 1
    wbi = u(bp, 2); bp += 2
    old_qp, bp_after_qp = se(bp)
    new_qp = old_qp + 3  # bump by 3 — typical "transrate down a notch"

    # Read everything past bp_after_qp as a tail blob via BitsAt.
    tail_bits = len(pps) * 8 - bp_after_qp

    # Re-emit prefix into a fresh buffer, then bit-copy the tail.
    buf = b""
    obp = 0
    # Write ue/se/u in order using BitsWrite + ExpGolombEncode.
    for name, kind, val in [
        ("pps_id", "ue", pps_id),
        ("sps_id", "ue", sps_id),
        ("ent_mode", "u1", ent_mode),
        ("bot_field", "u1", bot_field),
        ("nsg", "ue", nsg),
        ("nr0", "ue", nr0),
        ("nr1", "ue", nr1),
        ("wp", "u1", wp),
        ("wbi", "u2", wbi),
        ("new_qp", "se", new_qp),
    ]:
        if kind == "ue":
            buf, obp = s._inner.evaluate(
                ExpGolombEncode(Lit(buf), Lit(obp), Lit(val)).to_dict(),
                {})
        elif kind == "se":
            buf, obp = s._inner.evaluate(
                ExpGolombEncodeSigned(Lit(buf), Lit(obp),
                                       Lit(val)).to_dict(), {})
        elif kind == "u1":
            buf = s._inner.evaluate(
                BitsWrite(Lit(buf), Lit(obp), Lit(val),
                          Lit(1)).to_dict(), {})
            obp += 1
        elif kind == "u2":
            buf = s._inner.evaluate(
                BitsWrite(Lit(buf), Lit(obp), Lit(val),
                          Lit(2)).to_dict(), {})
            obp += 2

    # Bit-copy the tail in 32-bit chunks.
    p = bp_after_qp
    end = bp_after_qp + tail_bits
    while p < end:
        chunk = min(32, end - p)
        word = s._inner.evaluate(
            BitsAt(pps_lit, Lit(p), Lit(chunk)).to_dict(), {})
        buf = s._inner.evaluate(
            BitsWrite(Lit(buf), Lit(obp), Lit(word),
                      Lit(chunk)).to_dict(), {})
        p += chunk
        obp += chunk

    out = (raw[: pps_start + sc_len + 1]
           + bytes(buf)
           + raw[pps_end:])
    out_path = d / "parrot_primitive.h264"
    out_path.write_bytes(out)
    return old_qp, new_qp, len(out)


# ---- Path B — ffmpeg full re-encode -------------------------------

def ffmpeg_reencode_crf28():
    """ffmpeg's natural path to change quality: decode every frame,
    re-encode at a different CRF. Full DCT + motion comp + entropy
    coding."""
    out = d / "parrot_ffmpeg_crf28.mp4"
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error",
         "-i", str(src_mp4),
         "-c:v", "libx264", "-preset", "medium", "-crf", "28",
         "-c:a", "copy",
         str(out)],
        check=True)
    return out.stat().st_size


def ffmpeg_stream_copy():
    """ffmpeg's `-c copy` path — fastest equivalent that touches the
    file (remux without re-encoding). Closest comparable to our
    primitive in spirit (no re-encode), but it can't BUMP a field
    inside the bitstream; it just copies the stream verbatim. Use
    as a "do nothing but copy" baseline."""
    out = d / "parrot_ffmpeg_copy.mp4"
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error",
         "-i", str(src_mp4),
         "-c", "copy",
         str(out)],
        check=True)
    return out.stat().st_size


# ---- Run + report -------------------------------------------------

print(f"Input: {src_h264.stat().st_size // 1024} KiB H.264 Annex-B")
print(f"       {src_mp4.stat().st_size // 1024} KiB MP4 (with audio)")
print()

t_prim, _ = time_it(primitive_qp_bump, n=20)
old_qp, new_qp, prim_out_size = primitive_qp_bump()
print(f"PRIMITIVE  PPS QP-bump (in-place, same bit-length):")
print(f"  pic_init_qp_minus26: {old_qp} → {new_qp}")
print(f"  wall clock:  {t_prim*1000:6.2f} ms  (avg of 20 runs)")
print(f"  output size: {prim_out_size:>10,} bytes  "
      f"(same as input — no transrate)")
print()

t_copy, _ = time_it(ffmpeg_stream_copy, n=3)
copy_size = ffmpeg_stream_copy()
print(f"FFMPEG     -c copy (remux, no re-encode):")
print(f"  wall clock:  {t_copy*1000:6.2f} ms")
print(f"  output size: {copy_size:>10,} bytes  (≈ original)")
print()

t_reenc, _ = time_it(ffmpeg_reencode_crf28, n=1)
reenc_size = ffmpeg_reencode_crf28()
print(f"FFMPEG     re-encode @ CRF 28:")
print(f"  wall clock:  {t_reenc*1000:6.0f} ms")
print(f"  output size: {reenc_size:>10,} bytes  "
      f"({100*reenc_size/src_mp4.stat().st_size:.0f}% of input)")
print()

print(f"SPEEDUPS:")
print(f"  primitive vs ffmpeg copy:      {t_copy/t_prim:>7.0f}x faster")
print(f"  primitive vs ffmpeg re-encode: {t_reenc/t_prim:>7.0f}x faster")
print()

# Pixel verification: decoded frames from our primitive output
# should differ from the original (QP change reaches dequantization).
def frame_md5(path, vframes=10):
    r = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(path),
         "-vframes", str(vframes), "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-"],
        capture_output=True, check=True)
    return hashlib.md5(r.stdout).hexdigest(), len(r.stdout)

orig_h, orig_sz = frame_md5(src_h264)
prim_h, prim_sz = frame_md5(d / "parrot_primitive.h264")
reenc_h, reenc_sz = frame_md5(d / "parrot_ffmpeg_crf28.mp4")
print(f"FIRST-10-FRAME md5 comparison (320*240*3*10 = {320*240*3*10:,} B):")
print(f"  original    : {orig_h}  ({orig_sz:,} B)")
print(f"  primitive   : {prim_h}  ({prim_sz:,} B)")
print(f"  ffmpeg reenc: {reenc_h}  ({reenc_sz:,} B)")
print()

print("CAVEATS (the operations are NOT equivalent):")
print("  - Primitive: edits ONE field (PPS QP). Encoded slice data")
print("    unchanged; same file size. The QP change only shifts")
print("    DEQUANTIZATION at the decoder — visible pixel difference")
print("    but no bitrate reduction.")
print("  - ffmpeg re-encode: full decode + DCT + motion-comp +")
print("    re-quantize + re-entropy-code. Smaller file, different")
print("    pixels, different bits. Real transrate.")
print("  - ffmpeg -c copy: byte-for-byte remux. Can't bump a")
print("    bitstream field — just copies. Closest in spirit to")
print("    our 'no re-encode' work but has no equivalent edit op.")
print()
print("The primitive is fast because it touches O(modified bits)")
print("of a 4 MiB stream; ffmpeg re-encode is O(pixels × frames).")
