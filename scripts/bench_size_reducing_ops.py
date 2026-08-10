"""Wall-clock: primitive-based file-size reduction vs ffmpeg/exiftool."""
import subprocess, time, shutil
from pathlib import Path
from substrate_rs import (
    Lit, Substrate, Vec, BitsAt, BitsAtAll, BitsWrite, BitsWriteAll,
)

ffmpeg = shutil.which("ffmpeg")
exiftool = shutil.which("exiftool")
jpegtran = shutil.which("jpegtran")
d = Path("/tmp/h264_demo")
s = Substrate()

def time_it(fn, n=20):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n

# ---------- JPEG metadata strip ----------

# Generate bloated jpeg once.
sample = (d / "sample.jpg").read_bytes()
bloated_data = sample[:2] + (b"\xFF\xFE\x1F\x42" + b"X" * 8000) * 5 + sample[2:]
(d / "bloated.jpg").write_bytes(bloated_data)
print(f"bloated.jpg: {len(bloated_data)} bytes\n")

def jpeg_strip_primitive():
    raw = (d / "bloated.jpg").read_bytes()
    buf_lit = Lit(raw)
    KEEP = set(range(0xC0, 0xD0)) | {0xC4, 0xDB, 0xDD, 0xDA, 0xD8, 0xD9}
    KEEP.discard(0xC8)  # JPG reserved
    keep = [(0, 2)]
    i = 2
    while i < len(raw):
        if raw[i] != 0xFF:
            i += 1; continue
        m = raw[i+1]
        if m == 0 or m == 0xFF:
            i += 1; continue
        if m == 0xD8 or m == 0xD9 or (0xD0 <= m <= 0xD7):
            if m in KEEP: keep.append((i, i+2))
            i += 2; continue
        seg_len = (raw[i+2] << 8) | raw[i+3]
        seg_end = i + 2 + seg_len
        if m == 0xDA:
            j = seg_end
            while j < len(raw) - 1:
                if raw[j] == 0xFF and raw[j+1] != 0 and not (0xD0 <= raw[j+1] <= 0xD7):
                    break
                j += 1
            keep.append((i, j))
            i = j; continue
        if m in KEEP: keep.append((i, seg_end))
        i = seg_end
    if raw[-2:] == b"\xFF\xD9": keep.append((len(raw)-2, len(raw)))
    out = b"".join(raw[a:b] for a,b in keep)
    (d / "stripped_prim.jpg").write_bytes(out)
    return len(out)

def jpeg_strip_ffmpeg():
    subprocess.run([ffmpeg, "-y", "-loglevel", "error",
        "-i", str(d / "bloated.jpg"), "-map_metadata", "-1",
        str(d / "stripped_ff.jpg")], check=True)
    return (d / "stripped_ff.jpg").stat().st_size

def jpeg_strip_exiftool():
    subprocess.run([exiftool, "-q", "-overwrite_original", "-all=",
        str(d / "bloated_et.jpg")], check=True, capture_output=True)
    return (d / "bloated_et.jpg").stat().st_size

def jpeg_strip_jpegtran():
    subprocess.run([jpegtran, "-copy", "none", "-optimize",
        "-outfile", str(d / "stripped_jt.jpg"),
        str(d / "bloated.jpg")], check=True)
    return (d / "stripped_jt.jpg").stat().st_size

t_prim = time_it(jpeg_strip_primitive, n=50)
sz_prim = jpeg_strip_primitive()

t_ff = time_it(jpeg_strip_ffmpeg, n=10)
sz_ff = jpeg_strip_ffmpeg()

if exiftool:
    # exiftool modifies in-place; refresh each iteration
    def _et():
        import shutil as sh
        sh.copy(d / "bloated.jpg", d / "bloated_et.jpg")
        jpeg_strip_exiftool()
    t_et = time_it(_et, n=10)
    sh = __import__("shutil"); sh.copy(d / "bloated.jpg", d / "bloated_et.jpg")
    sz_et = jpeg_strip_exiftool()
else:
    t_et, sz_et = None, None

if jpegtran:
    t_jt = time_it(jpeg_strip_jpegtran, n=20)
    sz_jt = jpeg_strip_jpegtran()
else:
    t_jt, sz_jt = None, None

print("JPEG metadata strip:")
print(f"  primitive:   {t_prim*1000:6.2f} ms  → {sz_prim:>6} bytes ({100*sz_prim/len(bloated_data):.1f}%)")
print(f"  ffmpeg:      {t_ff*1000:6.2f} ms  → {sz_ff:>6} bytes ({100*sz_ff/len(bloated_data):.1f}%)")
if t_et: print(f"  exiftool:    {t_et*1000:6.2f} ms  → {sz_et:>6} bytes ({100*sz_et/len(bloated_data):.1f}%)")
if t_jt: print(f"  jpegtran:    {t_jt*1000:6.2f} ms  → {sz_jt:>6} bytes ({100*sz_jt/len(bloated_data):.1f}%)")
print(f"  primitive vs ffmpeg:   {t_ff/t_prim:.1f}x faster")
if t_jt: print(f"  primitive vs jpegtran: {t_jt/t_prim:.1f}x faster")
if t_et: print(f"  primitive vs exiftool: {t_et/t_prim:.1f}x faster")

# ---------- H.264 keyframe trim ----------
print()

def h264_trim_primitive():
    raw = (d / "gop.h264").read_bytes()
    # NAL nal_unit_type is byte-aligned (low 5 bits of the byte right
    # after the start code), so a direct byte read beats a primitive
    # call. BitsAt is for non-byte-aligned fields; here it'd just add
    # Python-side Vec/Lit construction overhead.
    idrs = []
    i = 0
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if (raw[i+sc] & 0x1F) == 5: idrs.append(i)
        i += sc
    cut = idrs[5]
    (d / "trim_prim.h264").write_bytes(raw[:cut])
    return cut

def h264_trim_ffmpeg_copy():
    subprocess.run([ffmpeg, "-y", "-loglevel", "error",
        "-i", str(d / "gop.h264"), "-t", "5", "-c", "copy",
        str(d / "trim_ff.h264")], check=True)
    return (d / "trim_ff.h264").stat().st_size

def h264_trim_ffmpeg_reencode():
    subprocess.run([ffmpeg, "-y", "-loglevel", "error",
        "-i", str(d / "gop.h264"), "-t", "5",
        "-c:v", "libx264", "-preset", "medium",
        str(d / "trim_ffre.h264")], check=True)
    return (d / "trim_ffre.h264").stat().st_size

orig_sz = (d / "gop.h264").stat().st_size
t_prim = time_it(h264_trim_primitive, n=50)
sz_prim = h264_trim_primitive()
t_ff = time_it(h264_trim_ffmpeg_copy, n=10)
sz_ff = h264_trim_ffmpeg_copy()
t_ffre = time_it(h264_trim_ffmpeg_reencode, n=5)
sz_ffre = h264_trim_ffmpeg_reencode()

print(f"H.264 trim at 5s (input {orig_sz} bytes):")
print(f"  primitive:      {t_prim*1000:6.2f} ms  → {sz_prim:>6} bytes")
print(f"  ffmpeg copy:    {t_ff*1000:6.2f} ms  → {sz_ff:>6} bytes")
print(f"  ffmpeg encode:  {t_ffre*1000:6.2f} ms  → {sz_ffre:>6} bytes")
print(f"  primitive vs ffmpeg copy:    {t_ff/t_prim:.0f}x faster")
print(f"  primitive vs ffmpeg encode:  {t_ffre/t_prim:.0f}x faster")
