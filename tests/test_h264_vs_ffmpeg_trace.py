"""End-to-end validation: our H.264 walker vs ffmpeg's trace_headers.

ffmpeg ships a bitstream filter `trace_headers` that dumps every
SPS/PPS/slice-header field's bit position and value:

  [trace_headers] 9   slice_type                  0001000 = 7
  [trace_headers] 16  pic_parameter_set_id              1 = 0
  ...

That's exact ground-truth from libavcodec's parse. This file
parses that trace, runs our own walker on the same NAL bytes,
and diffs field-by-field. Bit positions and values must match
modulo the 8-bit NAL header offset (ffmpeg measures from NAL
header start; ours measures from RBSP start).

If anything diverges — a wrong field width, missing conditional,
mis-aligned cabac_alignment_one_bit — the diff catches it.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
import pytest

srs = pytest.importorskip("substrate_rs")

from tests.test_h264_slice_header_walk import (
    BitReader, parse_sps_pps, strip_emulation, walk_slice_header,
)


def _ffmpeg_available():
    return shutil.which("ffmpeg") is not None


@pytest.fixture(scope="module")
def parrot_bytes():
    p = Path("/tmp/parrot/parrot.h264")
    if not p.exists():
        pytest.skip("parrot.h264 not extracted")
    return p.read_bytes()


def _run_trace_headers(path: Path) -> str:
    """Run ffmpeg with trace_headers bsf, capture all output."""
    r = subprocess.run(
        ["ffmpeg", "-loglevel", "info",
         "-i", str(path), "-c:v", "copy",
         "-bsf:v", "trace_headers",
         "-f", "null", "-"],
        capture_output=True, text=True)
    # trace_headers writes to stderr.
    return r.stderr


_TRACE_LINE_RE = re.compile(
    r"\[trace_headers @ [^\]]+\]\s+"
    r"(\d+)\s+"           # bit position
    r"(\S+)\s+"           # field name
    r"\S+\s*=\s*"         # bin string
    r"(-?\d+)"            # value
)
_TRACE_SECTION_RE = re.compile(
    r"\[trace_headers @ [^\]]+\]\s+"
    r"(Sequence Parameter Set|Picture Parameter Set|Slice Header)$"
)


def _parse_trace_sections(trace_text: str):
    """Split trace output into per-NAL-unit field lists.
    Returns list of (kind, fields) where fields is
    list of (bit_pos, name, value)."""
    sections = []
    current_kind = None
    current_fields = []
    for line in trace_text.splitlines():
        m = _TRACE_SECTION_RE.match(line.strip())
        if m:
            if current_kind:
                sections.append((current_kind, current_fields))
            current_kind = m.group(1)
            current_fields = []
            continue
        m = _TRACE_LINE_RE.match(line.strip())
        if m and current_kind:
            bp, name, val = int(m.group(1)), m.group(2), int(m.group(3))
            current_fields.append((bp, name, val))
    if current_kind:
        sections.append((current_kind, current_fields))
    return sections


def test_trace_headers_parses_sanely(parrot_bytes):
    """The ffmpeg trace output is well-formed and we can parse it."""
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not installed")
    trace = _run_trace_headers(Path("/tmp/parrot/parrot.h264"))
    sections = _parse_trace_sections(trace)
    section_kinds = [s[0] for s in sections]
    assert "Sequence Parameter Set" in section_kinds
    assert "Picture Parameter Set" in section_kinds
    assert "Slice Header" in section_kinds


def test_our_walker_matches_ffmpeg_p_slice(parrot_bytes):
    """For the parrot's first P-slice (after the IDR), every field
    in our walker's output must MATCH ffmpeg's trace_headers
    output, field-by-field, value-by-value.

    Bit positions are translated: ffmpeg reports from NAL header
    start (8 bits offset); our walker reports from RBSP start.
    """
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not installed")
    trace = _run_trace_headers(Path("/tmp/parrot/parrot.h264"))
    sections = _parse_trace_sections(trace)
    slice_sections = [(k, f) for k, f in sections if k == "Slice Header"]
    assert len(slice_sections) >= 2, "need IDR + at least one P slice"

    # The FIRST P-slice is the SECOND slice header (the first is IDR).
    _, p_fields = slice_sections[1]

    # Locate that same P-slice NAL in our bytes.
    sps_pps = parse_sps_pps(parrot_bytes)
    # The trace lists slices in stream order — find the first
    # non-IDR slice (nut=1).
    i = 0
    nut_count = 0
    target = None
    while i < len(parrot_bytes) - 4:
        if parrot_bytes[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif parrot_bytes[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        nri = (parrot_bytes[i+sc] >> 5) & 3
        nut = parrot_bytes[i+sc] & 0x1F
        j = i + sc + 1
        while j < len(parrot_bytes) - 3:
            if (parrot_bytes[j:j+3] == b"\x00\x00\x01"
                    or parrot_bytes[j:j+4] == b"\x00\x00\x00\x01"):
                break
            j += 1
        if nut == 1 and nri != 0:
            target = (i, sc, j, nri)
            break
        i += sc
    assert target is not None

    i, sc, j, nri = target
    slice_rbsp = strip_emulation(parrot_bytes[i + sc + 1 : j])
    info = walk_slice_header(
        slice_rbsp, sps_pps, sps_pps,
        nal_ref_idc=nri, is_idr=False)

    # Map ffmpeg's reported fields (bit-position relative to NAL
    # start, includes the 8-bit NAL header) to OUR walker's
    # equivalent values.
    #
    # ffmpeg includes the NAL header (bits 0-7) in its bit count,
    # so for our walker (which starts AT the RBSP) we subtract 8.
    ffmpeg_fields = {name: (bp, val) for (bp, name, val) in p_fields}

    # Field-by-field check. The mapping from our walker's keys to
    # ffmpeg's names is straightforward for most fields:
    checks = [
        ("first_mb_in_slice", "first_mb_in_slice"),
        ("slice_type_raw",    "slice_type"),
        ("pps_id",            "pic_parameter_set_id"),
        ("frame_num",         "frame_num"),
        ("pic_order_cnt_lsb", "pic_order_cnt_lsb"),
        ("num_ref_idx_active_override_flag",
                              "num_ref_idx_active_override_flag"),
        ("cabac_init_idc",    "cabac_init_idc"),
        ("slice_qp_delta",    "slice_qp_delta"),
        ("disable_deblocking_filter_idc",
                              "disable_deblocking_filter_idc"),
    ]
    for our_key, ff_name in checks:
        assert ff_name in ffmpeg_fields, (
            f"{ff_name} not in ffmpeg trace; got {list(ffmpeg_fields)}")
        ff_val = ffmpeg_fields[ff_name][1]
        our_val = info[our_key]
        assert our_val == ff_val, (
            f"field {ff_name} diverged: our={our_val} vs ffmpeg={ff_val}")

    # If override_flag is set, num_ref_idx_l0_active_minus1 is in the
    # bitstream and ffmpeg traces it.
    if info["num_ref_idx_active_override_flag"]:
        assert "num_ref_idx_l0_active_minus1" in ffmpeg_fields
        assert (info["num_ref_idx_l0_active_minus1"]
                == ffmpeg_fields["num_ref_idx_l0_active_minus1"][1])

    # CABAC start: ffmpeg traces `cabac_alignment_one_bit` repeatedly
    # then the next bit is byte-aligned. The FIRST occurrence's
    # position is where our `header_end_bp` lands (modulo +8 for the
    # NAL header).
    cabac_align_positions = [bp for (bp, name, _) in p_fields
                              if name == "cabac_alignment_one_bit"]
    assert cabac_align_positions, "no cabac_alignment in trace"
    ff_header_end = cabac_align_positions[0]
    our_header_end = info["header_end_bp"]
    assert our_header_end + 8 == ff_header_end, (
        f"header end position diverged: our (RBSP-relative) "
        f"{our_header_end} + 8 = {our_header_end + 8} vs "
        f"ffmpeg (NAL-relative) {ff_header_end}"
    )


def test_our_walker_matches_ffmpeg_idr_slice(parrot_bytes):
    """The IDR slice: shorter than P-slice (no ref_pic_list_mod /
    pred_weight_table / dec_ref_pic_marking for non-IDR), but has
    `idr_pic_id` + `no_output_of_prior_pics_flag` /
    `long_term_reference_flag` instead. Field-by-field match."""
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not installed")
    trace = _run_trace_headers(Path("/tmp/parrot/parrot.h264"))
    sections = _parse_trace_sections(trace)
    idr_section = next((f for (k, f) in sections if k == "Slice Header"), None)
    assert idr_section is not None

    # Confirm this is IDR via slice_type == 7 (I) and nal_unit_type == 5.
    fields_by_name = {n: (bp, v) for (bp, n, v) in idr_section}
    assert fields_by_name["nal_unit_type"][1] == 5
    assert fields_by_name["slice_type"][1] == 7

    sps_pps = parse_sps_pps(parrot_bytes)
    # Find first IDR (nut=5).
    i = 0
    target = None
    while i < len(parrot_bytes) - 4:
        if parrot_bytes[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif parrot_bytes[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        nri = (parrot_bytes[i+sc] >> 5) & 3
        nut = parrot_bytes[i+sc] & 0x1F
        if nut == 5:
            j = i + sc + 1
            while j < len(parrot_bytes) - 3:
                if (parrot_bytes[j:j+3] == b"\x00\x00\x01"
                        or parrot_bytes[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            target = (i, sc, j, nri)
            break
        i += sc
    assert target is not None

    i, sc, j, nri = target
    slice_rbsp = strip_emulation(parrot_bytes[i + sc + 1 : j])
    info = walk_slice_header(
        slice_rbsp, sps_pps, sps_pps,
        nal_ref_idc=nri, is_idr=True)

    # Cross-check the IDR-specific fields.
    assert info["slice_type_raw"] == fields_by_name["slice_type"][1]
    assert info["idr_pic_id"] == fields_by_name["idr_pic_id"][1]
    assert info["slice_qp_delta"] == fields_by_name["slice_qp_delta"][1]
    # `pic_order_cnt_lsb` for IDR is in the trace too.
    if "pic_order_cnt_lsb" in fields_by_name:
        assert (info["pic_order_cnt_lsb"]
                == fields_by_name["pic_order_cnt_lsb"][1])


def test_our_walker_matches_ffmpeg_all_slices(parrot_bytes):
    """Repeat the check for the FIRST 10 slices in the parrot —
    catches any slice where the conditional walking differs
    (e.g. slices with non-trivial ref_pic_list_modification or
    pred_weight_table sub-structures)."""
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not installed")
    trace = _run_trace_headers(Path("/tmp/parrot/parrot.h264"))
    sections = _parse_trace_sections(trace)
    slice_sections = [(k, f) for k, f in sections if k == "Slice Header"]

    sps_pps = parse_sps_pps(parrot_bytes)

    # Find first 10 slice NALs in our bytes.
    nals = []
    i = 0
    while i < len(parrot_bytes) - 4 and len(nals) < 10:
        if parrot_bytes[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif parrot_bytes[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        nri = (parrot_bytes[i+sc] >> 5) & 3
        nut = parrot_bytes[i+sc] & 0x1F
        j = i + sc + 1
        while j < len(parrot_bytes) - 3:
            if (parrot_bytes[j:j+3] == b"\x00\x00\x01"
                    or parrot_bytes[j:j+4] == b"\x00\x00\x00\x01"):
                break
            j += 1
        if nut in (1, 5):  # slice or IDR
            nals.append((i, sc, j, nri, nut))
        i += sc

    matches = 0
    mismatches = []
    for idx, (i, sc, j, nri, nut) in enumerate(nals):
        if idx >= len(slice_sections):
            break
        slice_rbsp = strip_emulation(parrot_bytes[i + sc + 1 : j])
        try:
            info = walk_slice_header(
                slice_rbsp, sps_pps, sps_pps,
                nal_ref_idc=nri, is_idr=(nut == 5))
        except Exception as e:
            mismatches.append(f"slice {idx}: walker raised {e!r}")
            continue
        _, ff_fields = slice_sections[idx]
        ff_map = {n: v for (_, n, v) in ff_fields}
        # Cross-check the FUNDAMENTAL invariants: slice_type, qp,
        # cabac_init_idc (if present). These three are what the
        # CABAC stack needs from the slice header.
        checks = []
        if info["slice_type_raw"] != ff_map.get("slice_type"):
            checks.append(f"slice_type {info['slice_type_raw']} vs "
                          f"{ff_map.get('slice_type')}")
        if info["slice_qp_delta"] != ff_map.get("slice_qp_delta"):
            checks.append(f"qp_delta {info['slice_qp_delta']} vs "
                          f"{ff_map.get('slice_qp_delta')}")
        if "cabac_init_idc" in ff_map:
            if info.get("cabac_init_idc") != ff_map["cabac_init_idc"]:
                checks.append(f"cabac_init_idc "
                              f"{info.get('cabac_init_idc')} vs "
                              f"{ff_map['cabac_init_idc']}")
        if checks:
            mismatches.append(f"slice {idx}: " + ", ".join(checks))
        else:
            matches += 1
    print(f"\n  slice walker vs ffmpeg trace: "
          f"{matches}/{matches + len(mismatches)} slices match")
    for m in mismatches:
        print(f"    MISMATCH: {m}")
    assert not mismatches, mismatches
