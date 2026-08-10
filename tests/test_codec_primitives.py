"""Phase 16b/16c — universal codec primitives in the Rust runner.

Tests the orthogonal building blocks every entropy-coded format needs:
``BitsAt`` / ``BitsWrite`` for any binary format, plus
``HuffmanDecodeStream`` / ``HuffmanEncodeStream`` (the `huffman`
optional feature block in ISA §3.3) that consume graph-resident
HuffmanTable nodes. MP3 requantize, H.264 QP-bump, JPEG transcoding,
Vorbis bitrate change all express as Rules composing these.
"""
from __future__ import annotations

import pytest


srs = pytest.importorskip("substrate_rs")
ao = pytest.importorskip("substrate_rs.audio")
bs = pytest.importorskip("substrate_rs.bitstream")


from substrate_rs import (
    Lit, Substrate, Vec,
    BitsAt, BitsAtAll, BitsWrite, BitsWriteAll,
    HuffmanDecodeStream, HuffmanEncodeStream,
    ExpGolombDecode, ExpGolombDecodeSigned,
    ExpGolombEncode, ExpGolombEncodeSigned,
)


# --- universal bit-field read/write ---------------------------------


def test_bits_at_reads_msb_first():
    s = Substrate()
    # 0xAB = 0b10101011
    buf = b"\xab"
    # Top 4 bits = 1010 = 10
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(0), Lit(4)).to_dict(), {}) == 10
    # Next 4 bits = 1011 = 11
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(4), Lit(4)).to_dict(), {}) == 11
    # Whole byte
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(0), Lit(8)).to_dict(), {}) == 0xAB


def test_bits_at_spans_byte_boundary():
    s = Substrate()
    # Two bytes 0xAB 0xCD; read 8 bits starting at bitpos 4
    # = low 4 of byte 0 + top 4 of byte 1 = 1011 1100 = 0xBC
    buf = b"\xab\xcd"
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(4), Lit(8)).to_dict(), {}) == 0xBC


def test_bits_at_out_of_range_returns_none():
    s = Substrate()
    buf = b"\xab"
    # 16 bits requested but only 8 available → None.
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(0), Lit(16)).to_dict(), {}) is None


def test_bits_write_into_empty_buffer():
    s = Substrate()
    # 5 = 0b101 written into empty buffer at bitpos 0 with 3 bits.
    # MSB-packed: 1010 0000 = 0xA0
    res = s._inner.evaluate(
        BitsWrite(Lit(b""), Lit(0), Lit(5), Lit(3)).to_dict(), {})
    assert res == b"\xa0"


def test_bits_write_extends_buffer_as_needed():
    s = Substrate()
    # Write 0xDEAD (16 bits) starting at bit 4 into empty buffer.
    # Final buf is 3 bytes (since we span 20 bits past start).
    res = s._inner.evaluate(
        BitsWrite(Lit(b""), Lit(4), Lit(0xDEAD), Lit(16)).to_dict(), {})
    assert len(res) == 3
    # Read back via BitsAt and verify.
    rb = s._inner.evaluate(
        BitsAt(Lit(res), Lit(4), Lit(16)).to_dict(), {})
    assert rb == 0xDEAD


def test_bits_at_all_batches_reads():
    """`BitsAtAll` reads N bit-fields in ONE runner call. Symmetric
    to BitsWriteAll. Avoids per-field Python↔Rust round-trips when
    walking codec tables."""
    s = Substrate()
    buf = b"\xAB\xCD\xEF\x12"
    reads = Vec(items=[
        Vec(items=[Lit(0), Lit(8)]),    # 0xAB
        Vec(items=[Lit(8), Lit(8)]),    # 0xCD
        Vec(items=[Lit(4), Lit(8)]),    # 0xBC (spans boundary)
        Vec(items=[Lit(16), Lit(16)]),  # 0xEF12
        Vec(items=[Lit(0), Lit(1)]),    # MSB
    ])
    res = s._inner.evaluate(
        BitsAtAll(Lit(buf), reads).to_dict(), {})
    assert tuple(res) == (0xAB, 0xCD, 0xBC, 0xEF12, 1)


def test_bits_at_all_underflow_returns_none():
    s = Substrate()
    # 8-byte read past end of 1-byte buffer.
    reads = Vec(items=[
        Vec(items=[Lit(0), Lit(8)]),
        Vec(items=[Lit(8), Lit(8)]),  # underflow
    ])
    assert s._inner.evaluate(
        BitsAtAll(Lit(b"\xAB"), reads).to_dict(), {}) is None


def test_bits_write_all_batches_into_one_copy():
    """`BitsWriteAll` applies many writes to ONE buffer copy. Use case:
    JPEG QT bump (64 bytes), Huffman table swap, multi-field PPS edit."""
    s = Substrate()
    # Six writes spanning byte boundaries + varying widths.
    writes = Vec(items=[
        Vec(items=[Lit(0), Lit(0xAB), Lit(8)]),       # byte 0
        Vec(items=[Lit(8), Lit(0xCD), Lit(8)]),       # byte 1
        Vec(items=[Lit(20), Lit(0xF), Lit(4)]),       # mid-byte
        Vec(items=[Lit(24), Lit(0xDEAD), Lit(16)]),   # extends buffer
        Vec(items=[Lit(48), Lit(1), Lit(1)]),         # single bit
        Vec(items=[Lit(56), Lit(0x12), Lit(8)]),
    ])
    res = s._inner.evaluate(
        BitsWriteAll(Lit(b""), writes).to_dict(), {})
    # Round-trip — read each field back via BitsAt.
    for bp, val, n in [(0, 0xAB, 8), (8, 0xCD, 8), (20, 0xF, 4),
                       (24, 0xDEAD, 16), (48, 1, 1), (56, 0x12, 8)]:
        got = s._inner.evaluate(
            BitsAt(Lit(res), Lit(bp), Lit(n)).to_dict(), {})
        assert got == val, f"bp={bp}: expected {val:#x} got {got:#x}"


def test_bits_write_all_matches_bits_write_chain():
    """BitsWriteAll must produce identical bytes to a sequential
    BitsWrite chain applying the same operations in the same order."""
    s = Substrate()
    ops = [(0, 0x12, 8), (5, 0x3F, 6), (16, 0xCAFE, 16),
           (50, 0xA5, 8), (100, 0xFFFF, 16)]
    chain_buf = b""
    for bp, val, n in ops:
        chain_buf = s._inner.evaluate(
            BitsWrite(Lit(chain_buf), Lit(bp), Lit(val),
                      Lit(n)).to_dict(), {})
    writes = Vec(items=[Vec(items=[Lit(bp), Lit(val), Lit(n)])
                        for bp, val, n in ops])
    batch_buf = s._inner.evaluate(
        BitsWriteAll(Lit(b""), writes).to_dict(), {})
    assert batch_buf == chain_buf, (
        f"chain={chain_buf.hex()} batch={batch_buf.hex()}")


def test_bits_write_then_bits_at_round_trip():
    s = Substrate()
    for value, nbits in [(0, 1), (1, 1), (0xAB, 8),
                          (0x12345, 17), (0xDEADBEEF, 32)]:
        written = s._inner.evaluate(
            BitsWrite(Lit(b""), Lit(0), Lit(value), Lit(nbits)).to_dict(),
            {})
        rb = s._inner.evaluate(
            BitsAt(Lit(written), Lit(0), Lit(nbits)).to_dict(), {})
        assert rb == value, (
            f"round-trip failed for value={value:x}, nbits={nbits}: "
            f"wrote {written!r}, read back {rb:x}")


# --- universal Huffman encode/decode --------------------------------


@pytest.fixture
def s_with_huff():
    sub = Substrate()
    ao.seed_audio_grammar(sub)
    ao.seed_native_codec_grammar(sub)
    bs.seed_bitstream_grammar(sub)
    bs.seed_mp3_huffman_tables(sub)
    return sub


def test_huffman_encode_decode_round_trip_table_1(s_with_huff):
    """Encode + decode round-trip via MP3 Huffman table 1 (the
    smallest big_values table). Demonstrates the primitives
    compose for one codec; identical machinery works for every
    other Huffman-based codec by passing a different table NodeID."""
    s = s_with_huff
    table_1 = bs.list_huffman_tables(s, codec="mp3")[0]
    # Table 1 is 2x2 — values 0 and 1 in each slot. Test all 4 pairs.
    test_pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]
    pair_terms = Vec(items=[Vec(items=[Lit(x), Lit(y)])
                            for x, y in test_pairs])
    enc = s._inner.evaluate(
        HuffmanEncodeStream(buffer=Lit(b""), bitpos=Lit(0),
                            pairs=pair_terms,
                            table=Lit(table_1)).to_dict(), {})
    buf, final_bp = enc[0], enc[1]
    dec = s._inner.evaluate(
        HuffmanDecodeStream(buffer=Lit(buf), bitpos=Lit(0),
                            table=Lit(table_1),
                            n_pairs=Lit(4)).to_dict(), {})
    decoded_pairs, dec_bp = dec[0], dec[1]
    assert decoded_pairs == tuple(tuple(p) for p in test_pairs)
    assert dec_bp == final_bp


def test_huffman_handles_negative_values_via_sign_bits(s_with_huff):
    """Non-zero coefficients carry a sign bit appended after the
    Huffman code. Round-trip verifies the encoder + decoder agree on
    sign-bit placement."""
    s = s_with_huff
    table_1 = bs.list_huffman_tables(s, codec="mp3")[0]
    test_pairs = [(1, -1), (-1, 1), (-1, -1)]
    pair_terms = Vec(items=[Vec(items=[Lit(x), Lit(y)])
                            for x, y in test_pairs])
    enc = s._inner.evaluate(
        HuffmanEncodeStream(buffer=Lit(b""), bitpos=Lit(0),
                            pairs=pair_terms,
                            table=Lit(table_1)).to_dict(), {})
    dec = s._inner.evaluate(
        HuffmanDecodeStream(buffer=Lit(enc[0]), bitpos=Lit(0),
                            table=Lit(table_1),
                            n_pairs=Lit(3)).to_dict(), {})
    assert dec[0] == tuple(tuple(p) for p in test_pairs)


def test_huffman_encode_at_nonzero_bitpos(s_with_huff):
    """Encode starting mid-buffer (after a header field) — the
    real use case in codec rewrites where you BitsWrite a header
    then HuffmanEncodeStream the payload."""
    s = s_with_huff
    table_1 = bs.list_huffman_tables(s, codec="mp3")[0]
    # Pretend we've written 12 header bits already.
    header = s._inner.evaluate(
        BitsWrite(Lit(b""), Lit(0), Lit(0xABC), Lit(12)).to_dict(), {})
    # Now encode pairs into the same buffer starting at bit 12.
    pair_terms = Vec(items=[Vec(items=[Lit(1), Lit(1)]),
                            Vec(items=[Lit(0), Lit(1)])])
    enc = s._inner.evaluate(
        HuffmanEncodeStream(buffer=Lit(header), bitpos=Lit(12),
                            pairs=pair_terms,
                            table=Lit(table_1)).to_dict(), {})
    buf = enc[0]
    # Header survives.
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(0), Lit(12)).to_dict(), {}) == 0xABC
    # Payload decodes at bit 12.
    dec = s._inner.evaluate(
        HuffmanDecodeStream(buffer=Lit(buf), bitpos=Lit(12),
                            table=Lit(table_1),
                            n_pairs=Lit(2)).to_dict(), {})
    assert dec[0] == ((1, 1), (0, 1))


def test_huffman_encode_advances_bitpos(s_with_huff):
    """`HuffmanEncodeStream` returns (buffer, new_bitpos). The new
    bitpos must equal the original bitpos plus the total bits
    written. Lets rules chain encode operations via Let bindings."""
    s = s_with_huff
    table_1 = bs.list_huffman_tables(s, codec="mp3")[0]
    pair = Vec(items=[Vec(items=[Lit(1), Lit(0)])])
    # Pair (1, 0): Huffman code is length 3 (t1l[2] = 3) + 1 sign bit
    # for x=1 (y=0 needs no sign) = 4 bits total.
    enc = s._inner.evaluate(
        HuffmanEncodeStream(buffer=Lit(b""), bitpos=Lit(0),
                            pairs=pair,
                            table=Lit(table_1)).to_dict(), {})
    assert enc[1] == 4


# --- end-to-end: modify a real MP3 frame header via primitives -------


def test_primitives_modify_mp3_bitrate_field():
    """Phase 16c proof-of-shape — use the universal primitives to
    MODIFY a real MP3 frame header (the bitrate_idx field at bits
    12-15 of the 32-bit header). Demonstrates the primitives
    compose to a real codec transform — the SAME field
    `mp3_truncate_transrate` mutates, but now graph-native.

    MP3 frame header layout (32 bits, big-endian):
      bits 0-10:  sync word (0xFFE)
      bits 11-12: MPEG version
      bits 13-14: layer
      bit  15:    protection bit
      bits 16-19: bitrate_idx  ← we read + modify this
      bits 20-21: sample_rate_idx
      ...

    Synthetic MPEG-1 Layer III, 192 kbps, 44.1 kHz, mono, no CRC:
      0xFFFB9040 = 1111 1111 1111 1011 1001 0000 0100 0000
    """
    s = Substrate()
    # Header bytes: 0xFF 0xFB 0x90 0x40
    header = b"\xff\xfb\x90\x40"

    # Read bitrate_idx at bits 16-19. 0x90 = 1001 0000;
    # bits 16-19 = 1001 = 9 (= 128 kbps in V1L3 table).
    # Wait the example claims 192 kbps which is idx 11 = 1011.
    # Let me recompute: 0xFB = 1111 1011, 0x90 = 1001 0000.
    # bits 12-15: 1011 = 11 → MPEG-1 + layer III + no CRC. ✓
    # bits 16-19: 1001 = 9 → 128 kbps (V1L3 table[9]). So actual
    # encoded rate is 128 kbps, not 192. Adjust assertions.
    bitrate_idx = s._inner.evaluate(
        BitsAt(Lit(header), Lit(16), Lit(4)).to_dict(), {})
    assert bitrate_idx == 9, f"expected idx 9 (128 kbps); got {bitrate_idx}"

    # Now modify: change bitrate_idx to 5 (= 64 kbps). Write via
    # BitsWrite. Result should match same byte pattern with bits
    # 16-19 changed from 1001 to 0101.
    # Original byte 2 = 0x90 = 1001 0000. After change to 0101 0000 = 0x50.
    modified = s._inner.evaluate(
        BitsWrite(Lit(header), Lit(16), Lit(5), Lit(4)).to_dict(), {})
    assert modified[0] == 0xFF, "sync byte 0 preserved"
    assert modified[1] == 0xFB, "sync byte 1 preserved"
    assert modified[2] == 0x50, (
        f"byte 2 should be 0x50 (bitrate_idx=5); got {modified[2]:#x}")
    assert modified[3] == 0x40, "byte 3 (sample-rate / etc.) preserved"

    # Read back to confirm.
    new_idx = s._inner.evaluate(
        BitsAt(Lit(modified), Lit(16), Lit(4)).to_dict(), {})
    assert new_idx == 5

    # Original buffer unchanged (BitsWrite is pure).
    assert header == b"\xff\xfb\x90\x40"


# --- universal Exp-Golomb encode/decode (H.264 / HEVC / VVC) ---------


def test_exp_golomb_decode_known_values():
    """ITU-T H.264 Table 9-1: ue(v) ↔ codeword.
        0   → 1
        1   → 010
        2   → 011
        3   → 00100
        4   → 00101
        5   → 00110
        6   → 00111
        7   → 0001000
    """
    s = Substrate()
    cases = [
        (0, 0b1, 1),
        (1, 0b010, 3),
        (2, 0b011, 3),
        (3, 0b00100, 5),
        (4, 0b00101, 5),
        (5, 0b00110, 5),
        (6, 0b00111, 5),
        (7, 0b0001000, 7),
    ]
    for value, bits, nbits in cases:
        # Pack the codeword MSB-first into a buffer.
        buf = s._inner.evaluate(
            BitsWrite(Lit(b""), Lit(0), Lit(bits), Lit(nbits)).to_dict(), {})
        dec = s._inner.evaluate(
            ExpGolombDecode(Lit(buf), Lit(0)).to_dict(), {})
        assert dec is not None, f"decode returned None for value={value}"
        got, new_bp = dec[0], dec[1]
        assert got == value, f"value: expected {value}, got {got}"
        assert new_bp == nbits, (
            f"new_bp: expected {nbits}, got {new_bp}")


def test_exp_golomb_encode_known_values():
    """Encode side of Table 9-1: value → packed codeword bits."""
    s = Substrate()
    cases = [
        (0, 0b1, 1),
        (1, 0b010, 3),
        (2, 0b011, 3),
        (3, 0b00100, 5),
        (7, 0b0001000, 7),
    ]
    for value, expected_bits, nbits in cases:
        enc = s._inner.evaluate(
            ExpGolombEncode(Lit(b""), Lit(0), Lit(value)).to_dict(), {})
        buf, new_bp = enc[0], enc[1]
        assert new_bp == nbits, (
            f"new_bp for {value}: expected {nbits}, got {new_bp}")
        got = s._inner.evaluate(
            BitsAt(Lit(buf), Lit(0), Lit(nbits)).to_dict(), {})
        assert got == expected_bits, (
            f"bits for {value}: expected {expected_bits:b}, got {got:b}")


def test_exp_golomb_round_trip_unsigned():
    """Round-trip a spread of unsigned values: small, byte-boundary,
    large (exercises multi-byte codewords)."""
    s = Substrate()
    for value in [0, 1, 2, 7, 14, 15, 16, 100, 254, 255, 1024, 65535]:
        enc = s._inner.evaluate(
            ExpGolombEncode(Lit(b""), Lit(0), Lit(value)).to_dict(), {})
        buf, end_bp = enc[0], enc[1]
        dec = s._inner.evaluate(
            ExpGolombDecode(Lit(buf), Lit(0)).to_dict(), {})
        assert dec is not None, f"decode None for value={value}"
        got, new_bp = dec[0], dec[1]
        assert got == value, (
            f"round-trip failed: in={value} out={got}")
        assert new_bp == end_bp, (
            f"bitpos drift: encode end={end_bp} decode end={new_bp}")


def test_exp_golomb_signed_table():
    """H.264 §9.1.1 se(v) signed mapping table.
       0 → 0, 1 → 1, 2 → -1, 3 → 2, 4 → -2, 5 → 3, 6 → -3, ...
    """
    s = Substrate()
    for value in [0, 1, -1, 2, -2, 3, -3, 10, -10, 100, -100]:
        enc = s._inner.evaluate(
            ExpGolombEncodeSigned(Lit(b""), Lit(0), Lit(value)).to_dict(),
            {})
        buf, end_bp = enc[0], enc[1]
        dec = s._inner.evaluate(
            ExpGolombDecodeSigned(Lit(buf), Lit(0)).to_dict(), {})
        assert dec is not None, f"decode None for value={value}"
        got, new_bp = dec[0], dec[1]
        assert got == value, (
            f"signed round-trip failed: in={value} out={got}")
        assert new_bp == end_bp


def test_exp_golomb_at_nonzero_bitpos():
    """Decode/encode starting mid-buffer — the real use case for
    H.264 slice headers (Exp-Golomb fields follow a NALU type byte
    and emulation-prevention work)."""
    s = Substrate()
    # Write 8 bits of header, then se(v) = -3 (codeword 6 = 00111
    # → 5 bits) starting at bit 8.
    header = s._inner.evaluate(
        BitsWrite(Lit(b""), Lit(0), Lit(0x67), Lit(8)).to_dict(), {})
    enc = s._inner.evaluate(
        ExpGolombEncodeSigned(Lit(header), Lit(8), Lit(-3)).to_dict(), {})
    buf, end_bp = enc[0], enc[1]
    assert end_bp == 8 + 5
    # Header survives.
    assert s._inner.evaluate(
        BitsAt(Lit(buf), Lit(0), Lit(8)).to_dict(), {}) == 0x67
    # Payload decodes at bit 8.
    dec = s._inner.evaluate(
        ExpGolombDecodeSigned(Lit(buf), Lit(8)).to_dict(), {})
    assert dec[0] == -3
    assert dec[1] == end_bp


def test_exp_golomb_decode_underflow_returns_none():
    """If the buffer can't supply the bits the codeword needs,
    decode returns None (engine-side guard so Rules can decide
    what to do)."""
    s = Substrate()
    # Empty buffer — even the marker bit isn't there.
    assert s._inner.evaluate(
        ExpGolombDecode(Lit(b""), Lit(0)).to_dict(), {}) is None
    # 4 zeros then nothing — needs 4 suffix bits but buffer ends.
    buf = s._inner.evaluate(
        BitsWrite(Lit(b""), Lit(0), Lit(0b00001), Lit(5)).to_dict(), {})
    # Only 5 bits total but the codeword 00001 + 4 suffix needs 9 bits.
    assert s._inner.evaluate(
        ExpGolombDecode(Lit(buf), Lit(0)).to_dict(), {}) is None


def test_exp_golomb_sequence_decode():
    """Decode 3 consecutive ue(v) fields, chaining bitpos —
    the shape every H.264/HEVC parser uses."""
    s = Substrate()
    # Encode values [5, 3, 0] sequentially.
    enc1 = s._inner.evaluate(
        ExpGolombEncode(Lit(b""), Lit(0), Lit(5)).to_dict(), {})
    enc2 = s._inner.evaluate(
        ExpGolombEncode(Lit(enc1[0]), Lit(enc1[1]), Lit(3)).to_dict(), {})
    enc3 = s._inner.evaluate(
        ExpGolombEncode(Lit(enc2[0]), Lit(enc2[1]), Lit(0)).to_dict(), {})
    buf = enc3[0]
    # Decode them back.
    d1 = s._inner.evaluate(ExpGolombDecode(Lit(buf), Lit(0)).to_dict(), {})
    assert d1[0] == 5
    d2 = s._inner.evaluate(
        ExpGolombDecode(Lit(buf), Lit(d1[1])).to_dict(), {})
    assert d2[0] == 3
    d3 = s._inner.evaluate(
        ExpGolombDecode(Lit(buf), Lit(d2[1])).to_dict(), {})
    assert d3[0] == 0


# --- end-to-end: H.264 QP-bump on a real ffmpeg-produced stream -----


def _parse_pps_fields(s, pps_rbsp: bytes):
    """Parse the fixed prefix of an H.264 PPS (§7.3.2.2) up to and
    including pic_init_qp_minus26. Returns dict of field values +
    the bitpos of pic_init_qp_minus26 (so we know where to rewrite).

    Pure composition of BitsAt + ExpGolombDecode + ExpGolombDecodeSigned
    — no per-codec runner primitive."""
    buf = Lit(pps_rbsp)
    bp = 0
    out = {}

    def ue(name, bp):
        v, new_bp = s._inner.evaluate(
            ExpGolombDecode(buf, Lit(bp)).to_dict(), {})
        out[name] = v
        return new_bp

    def se(name, bp):
        v, new_bp = s._inner.evaluate(
            ExpGolombDecodeSigned(buf, Lit(bp)).to_dict(), {})
        out[name] = v
        return new_bp

    def u(name, bp, n):
        out[name] = s._inner.evaluate(
            BitsAt(buf, Lit(bp), Lit(n)).to_dict(), {})
        return bp + n

    bp = ue("pic_parameter_set_id", bp)
    bp = ue("seq_parameter_set_id", bp)
    bp = u("entropy_coding_mode_flag", bp, 1)
    bp = u("bottom_field_pic_order_in_frame_present_flag", bp, 1)
    bp = ue("num_slice_groups_minus1", bp)
    # Skip slice-group-map fields if num_slice_groups_minus1 > 0
    # (production parser needs full §7.3.2.2.1); for our single-group
    # ffmpeg sample this branch is dead.
    assert out["num_slice_groups_minus1"] == 0, (
        "demo handles only single-slice-group streams")
    bp = ue("num_ref_idx_l0_default_active_minus1", bp)
    bp = ue("num_ref_idx_l1_default_active_minus1", bp)
    bp = u("weighted_pred_flag", bp, 1)
    bp = u("weighted_bipred_idc", bp, 2)
    qp_bp = bp
    bp = se("pic_init_qp_minus26", bp)
    qp_end_bp = bp
    return out, qp_bp, qp_end_bp


def test_h264_qp_bump_same_bit_length_inplace():
    """Phase 16c headline — bump the H.264 quantization parameter
    on a real ffmpeg-encoded stream. Pure composition of the
    universal primitives; ffmpeg verifies the modified bitstream
    still parses + decodes.

    Strategy: parse the 3-byte PPS RBSP, decode pic_init_qp_minus26,
    pick a new QP whose se(v) encoding has the SAME bit-length, then
    overwrite those bits in-place. ffmpeg decodes both streams; we
    confirm the new file is structurally valid + the field round-trips
    to the new value."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample_path = Path("/tmp/h264_demo/sample.h264")
    if not sample_path.exists():
        # Generate on demand.
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p", "-profile:v", "baseline", "-level", "3.0",
            "-g", "30", "-an", "-f", "h264", str(sample_path),
        ], check=True)

    raw = sample_path.read_bytes()
    s = Substrate()

    # Locate first PPS NAL (Annex B start codes + NAL header byte
    # with nal_unit_type == 8).
    def find_nal(buf, target_type):
        i = 0
        while i < len(buf) - 4:
            if buf[i:i+4] == b"\x00\x00\x00\x01":
                sc = 4
            elif buf[i:i+3] == b"\x00\x00\x01":
                sc = 3
            else:
                i += 1
                continue
            if (buf[i+sc] & 0x1F) == target_type:
                # Find end (next start code or EOF).
                j = i + sc + 1
                while j < len(buf) - 3:
                    if (buf[j:j+3] == b"\x00\x00\x01"
                            or buf[j:j+4] == b"\x00\x00\x00\x01"):
                        break
                    j += 1
                return i, sc, j  # start_offset, sc_len, end_offset
            i += sc
        return None

    pps_loc = find_nal(raw, 8)
    assert pps_loc is not None, "no PPS found in sample"
    pps_start, sc_len, pps_end = pps_loc
    pps_rbsp = raw[pps_start + sc_len + 1 : pps_end]

    fields, qp_bp, qp_end_bp = _parse_pps_fields(s, pps_rbsp)

    # Sanity-check ffmpeg's default. Constrained Baseline + ultrafast
    # typically picks pic_init_qp_minus26 = -3 (QP=23). The demo
    # accepts whatever it actually emitted.
    old_minus26 = fields["pic_init_qp_minus26"]
    old_qp = 26 + old_minus26
    old_field_bits = qp_end_bp - qp_bp

    # Pick a new minus26 whose se(v) encoding is the SAME length as
    # the old one. Search the signed range until we find a match.
    new_minus26 = None
    for candidate in range(-25, 26):
        if candidate == old_minus26:
            continue
        enc = s._inner.evaluate(
            ExpGolombEncodeSigned(Lit(b""), Lit(0),
                                  Lit(candidate)).to_dict(), {})
        if enc[1] == old_field_bits:
            new_minus26 = candidate
            break
    assert new_minus26 is not None, (
        f"no same-length QP candidate found for {old_minus26}")
    new_qp = 26 + new_minus26

    # Rewrite the field in place. ExpGolombEncodeSigned writes into
    # a fresh buffer copy starting at qp_bp.
    rewritten, end_bp = s._inner.evaluate(
        ExpGolombEncodeSigned(Lit(pps_rbsp), Lit(qp_bp),
                              Lit(new_minus26)).to_dict(), {})
    assert end_bp == qp_end_bp, "same-length write must end at same bp"
    assert len(rewritten) == len(pps_rbsp), (
        "no buffer growth for same-length write")
    # Bits before qp_bp are unchanged.
    if qp_bp >= 8:
        assert rewritten[: qp_bp // 8] == pps_rbsp[: qp_bp // 8]
    # Bits after qp_end_bp are unchanged.
    if qp_end_bp <= (len(pps_rbsp) - 1) * 8:
        tail_byte = (qp_end_bp + 7) // 8
        assert rewritten[tail_byte:] == pps_rbsp[tail_byte:]

    # Round-trip: re-decode the new PPS via the same primitives,
    # confirm pic_init_qp_minus26 matches what we wrote.
    new_fields, _, _ = _parse_pps_fields(s, rewritten)
    assert new_fields["pic_init_qp_minus26"] == new_minus26, (
        f"round-trip failed: wrote {new_minus26} read "
        f"{new_fields['pic_init_qp_minus26']}")
    # All other PPS fields unchanged.
    for k, v in fields.items():
        if k == "pic_init_qp_minus26":
            continue
        assert new_fields[k] == v, (
            f"field {k} mutated: {v} -> {new_fields[k]}")

    # Splice the modified PPS back into the full stream + write out.
    modified_stream = (raw[: pps_start + sc_len + 1]
                       + rewritten
                       + raw[pps_end:])
    out_path = sample_path.parent / "sample_qpbump.h264"
    out_path.write_bytes(modified_stream)

    # ffmpeg must successfully decode the modified stream (proves the
    # bitstream is still structurally valid). Compare against the
    # original — both should decode the same number of frames.
    def decode_frame_count(path):
        result = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(path),
             "-f", "null", "-"],
            capture_output=True, text=True)
        # Use ffprobe for frame count.
        probe = subprocess.run(
            ["ffprobe", "-loglevel", "error", "-count_frames",
             "-select_streams", "v:0", "-show_entries",
             "stream=nb_read_frames", "-of",
             "default=nokey=1:noprint_wrappers=1", str(path)],
            capture_output=True, text=True, check=True)
        return result.returncode, int(probe.stdout.strip())

    orig_rc, orig_frames = decode_frame_count(sample_path)
    mod_rc, mod_frames = decode_frame_count(out_path)
    assert orig_rc == 0, "original must decode cleanly"
    assert mod_rc == 0, (
        "modified stream must decode cleanly — proves bitstream is valid")
    assert mod_frames == orig_frames, (
        f"frame count must match: orig={orig_frames} mod={mod_frames}")

    # PIXEL-LEVEL PROOF: the QP change must actually affect
    # dequantization. ffmpeg md5 of decoded frames must DIFFER between
    # original and modified (otherwise our bump didn't reach the
    # decoder math).
    def decoded_md5(path):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(path),
             "-f", "framemd5", "-"],
            capture_output=True, text=True, check=True)
        return r.stdout

    orig_md5 = decoded_md5(sample_path)
    mod_md5 = decoded_md5(out_path)
    assert orig_md5 != mod_md5, (
        "decoded pixels identical — QP bump didn't propagate to "
        "dequantization (bitstream change was a no-op?)")

    print(f"\n  H.264 QP-bump demo:")
    print(f"    pic_init_qp_minus26: {old_minus26} -> {new_minus26}")
    print(f"    QP:                  {old_qp} -> {new_qp}")
    print(f"    field bit-length:    {old_field_bits} bits (preserved)")
    print(f"    PPS bytes:           {len(pps_rbsp)} (preserved)")
    print(f"    ffmpeg decoded {mod_frames} frames from modified stream")


def test_h264_qp_bump_different_bit_length_reemit():
    """The harder case — bump the QP to a value whose se(v) encoding
    is a different bit-length, requiring re-emission of every
    subsequent PPS field at the new bitpos. Still pure composition
    of the universal primitives; ffmpeg verifies the result decodes.

    This is what production transrate has to handle when the bit
    budget changes. The agent expresses it as a Rule that walks the
    PPS field structure, re-emitting each into a fresh buffer."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample_path = Path("/tmp/h264_demo/sample.h264")
    if not sample_path.exists():
        pytest.skip("sample not built; same-length test builds it")

    raw = sample_path.read_bytes()
    s = Substrate()

    # Reuse the locator from the prior test.
    i = 0
    pps_start = sc_len = pps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01":
            sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01":
            sc = 3
        else:
            i += 1
            continue
        if (raw[i+sc] & 0x1F) == 8:
            pps_start = i
            sc_len = sc
            j = i + sc + 1
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            pps_end = j
            break
        i += sc
    pps_rbsp = raw[pps_start + sc_len + 1 : pps_end]

    fields, _, _ = _parse_pps_fields(s, pps_rbsp)
    old_minus26 = fields["pic_init_qp_minus26"]

    # Pick a new QP whose se(v) encoding is LONGER. -3 is 5 bits;
    # -10 is 9 bits. Sweep until we find one whose encoded length
    # differs from the original.
    old_enc_len = s._inner.evaluate(
        ExpGolombEncodeSigned(Lit(b""), Lit(0), Lit(old_minus26))
        .to_dict(), {})[1]
    new_minus26 = None
    for candidate in [-10, 10, -15, 15, 5, -5]:
        enc_len = s._inner.evaluate(
            ExpGolombEncodeSigned(Lit(b""), Lit(0), Lit(candidate))
            .to_dict(), {})[1]
        if enc_len != old_enc_len:
            new_minus26 = candidate
            break
    assert new_minus26 is not None

    # Re-emit the full PPS RBSP from scratch with the new QP. Walk
    # the original to capture every field after pic_init_qp_minus26,
    # then re-encode into a fresh buffer using only the primitives.
    # (The parse continues past qp to capture trailing fields needed
    # for re-emission.)

    def parse_full_pps(rbsp):
        """Parse all PPS fields plus the rbsp_trailing_bits offset
        so we can faithfully re-emit."""
        buf = Lit(rbsp)
        bp = 0
        out = {}

        def ue(k, bp):
            v, np = s._inner.evaluate(
                ExpGolombDecode(buf, Lit(bp)).to_dict(), {})
            out[k] = v
            return np

        def se(k, bp):
            v, np = s._inner.evaluate(
                ExpGolombDecodeSigned(buf, Lit(bp)).to_dict(), {})
            out[k] = v
            return np

        def u(k, bp, n):
            out[k] = s._inner.evaluate(
                BitsAt(buf, Lit(bp), Lit(n)).to_dict(), {})
            return bp + n

        bp = ue("pic_parameter_set_id", bp)
        bp = ue("seq_parameter_set_id", bp)
        bp = u("entropy_coding_mode_flag", bp, 1)
        bp = u("bottom_field_pic_order_in_frame_present_flag", bp, 1)
        bp = ue("num_slice_groups_minus1", bp)
        assert out["num_slice_groups_minus1"] == 0
        bp = ue("num_ref_idx_l0_default_active_minus1", bp)
        bp = ue("num_ref_idx_l1_default_active_minus1", bp)
        bp = u("weighted_pred_flag", bp, 1)
        bp = u("weighted_bipred_idc", bp, 2)
        bp = se("pic_init_qp_minus26", bp)
        bp = se("pic_init_qs_minus26", bp)
        bp = se("chroma_qp_index_offset", bp)
        bp = u("deblocking_filter_control_present_flag", bp, 1)
        bp = u("constrained_intra_pred_flag", bp, 1)
        bp = u("redundant_pic_cnt_present_flag", bp, 1)
        # rbsp_trailing_bits: stop bit (1) + zero pad. We don't need
        # to capture them — just re-emit them.
        return out, bp

    fields_full, end_bp = parse_full_pps(pps_rbsp)

    def emit_pps(f):
        """Re-encode a PPS RBSP from its parsed fields via the
        primitives. Returns bytes. Pure composition of
        BitsWrite + ExpGolombEncode + ExpGolombEncodeSigned. BitsWrite
        returns the new buffer; bitpos is tracked here (always advances
        by `n_bits` for fixed-width writes)."""
        buf = b""
        bp = 0

        def write_ue(k):
            nonlocal buf, bp
            buf, bp = s._inner.evaluate(
                ExpGolombEncode(Lit(buf), Lit(bp), Lit(f[k])).to_dict(),
                {})

        def write_se(k):
            nonlocal buf, bp
            buf, bp = s._inner.evaluate(
                ExpGolombEncodeSigned(Lit(buf), Lit(bp),
                                      Lit(f[k])).to_dict(), {})

        def write_u(value, n):
            nonlocal buf, bp
            buf = s._inner.evaluate(
                BitsWrite(Lit(buf), Lit(bp), Lit(value), Lit(n)).to_dict(),
                {})
            bp += n

        write_ue("pic_parameter_set_id")
        write_ue("seq_parameter_set_id")
        write_u(f["entropy_coding_mode_flag"], 1)
        write_u(f["bottom_field_pic_order_in_frame_present_flag"], 1)
        write_ue("num_slice_groups_minus1")
        write_ue("num_ref_idx_l0_default_active_minus1")
        write_ue("num_ref_idx_l1_default_active_minus1")
        write_u(f["weighted_pred_flag"], 1)
        write_u(f["weighted_bipred_idc"], 2)
        write_se("pic_init_qp_minus26")
        write_se("pic_init_qs_minus26")
        write_se("chroma_qp_index_offset")
        write_u(f["deblocking_filter_control_present_flag"], 1)
        write_u(f["constrained_intra_pred_flag"], 1)
        write_u(f["redundant_pic_cnt_present_flag"], 1)
        # rbsp_trailing_bits: stop bit 1 + zero pad to byte boundary.
        write_u(1, 1)
        pad = (8 - (bp & 7)) & 7
        if pad:
            write_u(0, pad)
        return buf

    # Sanity-check round-trip: re-emitting the parsed fields with no
    # mutation reproduces the original PPS bytes exactly.
    round_trip = emit_pps(fields_full)
    assert round_trip == pps_rbsp, (
        f"round-trip drift: orig {pps_rbsp.hex()} != "
        f"emit {round_trip.hex()}")

    # Now mutate the QP and re-emit.
    new_fields = dict(fields_full)
    new_fields["pic_init_qp_minus26"] = new_minus26
    new_pps_rbsp = emit_pps(new_fields)
    # Re-parse to confirm.
    re_parsed, _ = parse_full_pps(new_pps_rbsp)
    assert re_parsed["pic_init_qp_minus26"] == new_minus26
    for k, v in fields_full.items():
        if k == "pic_init_qp_minus26":
            continue
        assert re_parsed[k] == v, f"field {k} mutated unexpectedly"

    # Splice and decode.
    modified = (raw[: pps_start + sc_len + 1]
                + new_pps_rbsp
                + raw[pps_end:])
    out_path = Path("/tmp/h264_demo/sample_qpbump_reemit.h264")
    out_path.write_bytes(modified)
    result = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-f", "null", "-"],
        capture_output=True, text=True)
    assert result.returncode == 0, (
        f"ffmpeg rejected re-emitted PPS: stderr={result.stderr}")
    probe = subprocess.run(
        ["ffprobe", "-loglevel", "error", "-count_frames",
         "-select_streams", "v:0", "-show_entries",
         "stream=nb_read_frames", "-of",
         "default=nokey=1:noprint_wrappers=1", str(out_path)],
        capture_output=True, text=True, check=True)
    n_frames = int(probe.stdout.strip())
    assert n_frames == 30

    print(f"\n  H.264 QP-bump full re-emit demo:")
    print(f"    pic_init_qp_minus26: {old_minus26} -> {new_minus26}")
    print(f"    PPS RBSP:            {len(pps_rbsp)} -> {len(new_pps_rbsp)} bytes")
    print(f"    field bit-length:    {old_enc_len} -> "
          f"{s._inner.evaluate(ExpGolombEncodeSigned(Lit(b''), Lit(0), Lit(new_minus26)).to_dict(), {})[1]} bits")
    print(f"    ffmpeg decoded {n_frames} frames from re-emitted stream")


# --- HEVC: same primitives, different codec, different field structure ---


def _find_hevc_nal(buf, target_type):
    """Locate first HEVC NAL of `target_type`. HEVC NAL header is 2
    bytes (vs H.264's 1); nal_unit_type is bits 1-6 of byte 0."""
    i = 0
    while i < len(buf) - 4:
        # Prefer 4-byte start code over 3-byte where they overlap.
        if buf[i:i+4] == b"\x00\x00\x00\x01":
            sc = 4
        elif buf[i:i+3] == b"\x00\x00\x01":
            sc = 3
        else:
            i += 1
            continue
        nt = (buf[i+sc] >> 1) & 0x3F
        if nt == target_type:
            j = i + sc + 2  # NAL header is 2 bytes in HEVC
            while j < len(buf) - 3:
                if (buf[j:j+3] == b"\x00\x00\x01"
                        or buf[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            return i, sc, j
        i += sc
    return None


def _parse_hevc_pps_full(s, pps_rbsp: bytes):
    """Parse the full HEVC PPS up through the fields needed to round-
    trip-emit it back. Walks ITU-T H.265 §7.3.2.3, the same way
    a production HEVC parser would, but composing only the
    universal primitives."""
    buf = Lit(pps_rbsp)
    bp = 0
    out = {}

    def ue(k, bp):
        v, np = s._inner.evaluate(
            ExpGolombDecode(buf, Lit(bp)).to_dict(), {})
        out[k] = v
        return np

    def se(k, bp):
        v, np = s._inner.evaluate(
            ExpGolombDecodeSigned(buf, Lit(bp)).to_dict(), {})
        out[k] = v
        return np

    def u(k, bp, n):
        out[k] = s._inner.evaluate(
            BitsAt(buf, Lit(bp), Lit(n)).to_dict(), {})
        return bp + n

    bp = ue("pps_pic_parameter_set_id", bp)
    bp = ue("pps_seq_parameter_set_id", bp)
    bp = u("dependent_slice_segments_enabled_flag", bp, 1)
    bp = u("output_flag_present_flag", bp, 1)
    bp = u("num_extra_slice_header_bits", bp, 3)
    bp = u("sign_data_hiding_enabled_flag", bp, 1)
    bp = u("cabac_init_present_flag", bp, 1)
    bp = ue("num_ref_idx_l0_default_active_minus1", bp)
    bp = ue("num_ref_idx_l1_default_active_minus1", bp)
    bp = se("init_qp_minus26", bp)
    bp = u("constrained_intra_pred_flag", bp, 1)
    bp = u("transform_skip_enabled_flag", bp, 1)
    bp = u("cu_qp_delta_enabled_flag", bp, 1)
    if out["cu_qp_delta_enabled_flag"]:
        bp = ue("diff_cu_qp_delta_depth", bp)
    bp = se("pps_cb_qp_offset", bp)
    bp = se("pps_cr_qp_offset", bp)
    bp = u("pps_slice_chroma_qp_offsets_present_flag", bp, 1)
    bp = u("weighted_pred_flag", bp, 1)
    bp = u("weighted_bipred_flag", bp, 1)
    bp = u("transquant_bypass_enabled_flag", bp, 1)
    bp = u("tiles_enabled_flag", bp, 1)
    bp = u("entropy_coding_sync_enabled_flag", bp, 1)
    # tiles_enabled_flag branch: skip if 0 (true for ultrafast default)
    assert out["tiles_enabled_flag"] == 0, (
        "demo handles only non-tiled HEVC streams")
    bp = u("pps_loop_filter_across_slices_enabled_flag", bp, 1)
    bp = u("deblocking_filter_control_present_flag", bp, 1)
    if out["deblocking_filter_control_present_flag"]:
        bp = u("deblocking_filter_override_enabled_flag", bp, 1)
        bp = u("pps_deblocking_filter_disabled_flag", bp, 1)
        if not out["pps_deblocking_filter_disabled_flag"]:
            bp = se("pps_beta_offset_div2", bp)
            bp = se("pps_tc_offset_div2", bp)
    bp = u("pps_scaling_list_data_present_flag", bp, 1)
    assert out["pps_scaling_list_data_present_flag"] == 0, (
        "demo handles only default scaling lists")
    bp = u("lists_modification_present_flag", bp, 1)
    bp = ue("log2_parallel_merge_level_minus2", bp)
    bp = u("slice_segment_header_extension_present_flag", bp, 1)
    bp = u("pps_extension_present_flag", bp, 1)
    assert out["pps_extension_present_flag"] == 0, (
        "demo handles only base HEVC PPS (no extensions)")
    # rbsp_trailing_bits follows; we don't capture them.
    return out, bp


def _emit_hevc_pps(s, f):
    """Re-encode an HEVC PPS RBSP from parsed fields. Inverse of
    `_parse_hevc_pps_full`; same field order, same primitives."""
    buf = b""
    bp = 0

    def write_ue(k):
        nonlocal buf, bp
        buf, bp = s._inner.evaluate(
            ExpGolombEncode(Lit(buf), Lit(bp), Lit(f[k])).to_dict(), {})

    def write_se(k):
        nonlocal buf, bp
        buf, bp = s._inner.evaluate(
            ExpGolombEncodeSigned(Lit(buf), Lit(bp), Lit(f[k])).to_dict(),
            {})

    def write_u(value, n):
        nonlocal buf, bp
        buf = s._inner.evaluate(
            BitsWrite(Lit(buf), Lit(bp), Lit(value), Lit(n)).to_dict(),
            {})
        bp += n

    write_ue("pps_pic_parameter_set_id")
    write_ue("pps_seq_parameter_set_id")
    write_u(f["dependent_slice_segments_enabled_flag"], 1)
    write_u(f["output_flag_present_flag"], 1)
    write_u(f["num_extra_slice_header_bits"], 3)
    write_u(f["sign_data_hiding_enabled_flag"], 1)
    write_u(f["cabac_init_present_flag"], 1)
    write_ue("num_ref_idx_l0_default_active_minus1")
    write_ue("num_ref_idx_l1_default_active_minus1")
    write_se("init_qp_minus26")
    write_u(f["constrained_intra_pred_flag"], 1)
    write_u(f["transform_skip_enabled_flag"], 1)
    write_u(f["cu_qp_delta_enabled_flag"], 1)
    if f["cu_qp_delta_enabled_flag"]:
        write_ue("diff_cu_qp_delta_depth")
    write_se("pps_cb_qp_offset")
    write_se("pps_cr_qp_offset")
    write_u(f["pps_slice_chroma_qp_offsets_present_flag"], 1)
    write_u(f["weighted_pred_flag"], 1)
    write_u(f["weighted_bipred_flag"], 1)
    write_u(f["transquant_bypass_enabled_flag"], 1)
    write_u(f["tiles_enabled_flag"], 1)
    write_u(f["entropy_coding_sync_enabled_flag"], 1)
    write_u(f["pps_loop_filter_across_slices_enabled_flag"], 1)
    write_u(f["deblocking_filter_control_present_flag"], 1)
    if f["deblocking_filter_control_present_flag"]:
        write_u(f["deblocking_filter_override_enabled_flag"], 1)
        write_u(f["pps_deblocking_filter_disabled_flag"], 1)
        if not f["pps_deblocking_filter_disabled_flag"]:
            write_se("pps_beta_offset_div2")
            write_se("pps_tc_offset_div2")
    write_u(f["pps_scaling_list_data_present_flag"], 1)
    write_u(f["lists_modification_present_flag"], 1)
    write_ue("log2_parallel_merge_level_minus2")
    write_u(f["slice_segment_header_extension_present_flag"], 1)
    write_u(f["pps_extension_present_flag"], 1)
    # rbsp_trailing_bits: stop bit + zero pad.
    write_u(1, 1)
    pad = (8 - (bp & 7)) & 7
    if pad:
        write_u(0, pad)
    return buf


def test_hevc_qp_bump_full_reemit():
    """The H.264 demo's twin in HEVC — bump init_qp_minus26 on a
    real ffmpeg-encoded x265 stream. SAME four primitives
    (BitsAt / BitsWrite / ExpGolombDecodeSigned /
    ExpGolombEncodeSigned), DIFFERENT codec, DIFFERENT field layout.

    Proves the architectural claim: the agent learns new codecs by
    writing Rules over per-codec graph structure, not by extending
    the runner. HEVC's PPS has ~25 fields vs H.264's ~14 + different
    field order + extra u(3) bit-pack — all expressed via the same
    Term-tree composition.

    The demo uses full re-emit (not in-place rewrite) because x265's
    default init_qp_minus26=0 codes to 1 bit, leaving no other 1-bit
    candidate. Re-emit is the production-realistic path anyway."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample = Path("/tmp/h264_demo/sample.hevc")
    if not sample.exists():
        sample.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
            "-c:v", "libx265", "-preset", "ultrafast",
            "-tune", "zerolatency", "-pix_fmt", "yuv420p",
            "-x265-params", "log-level=error", "-an", str(sample),
        ]).returncode
        if rc != 0 or not sample.exists():
            pytest.skip("ffmpeg has no libx265 support")

    raw = sample.read_bytes()
    s = Substrate()

    loc = _find_hevc_nal(raw, 34)
    assert loc is not None, "no PPS found in HEVC sample"
    pps_start, sc_len, pps_end = loc
    pps_rbsp = raw[pps_start + sc_len + 2 : pps_end]

    fields, _ = _parse_hevc_pps_full(s, pps_rbsp)
    old_minus26 = fields["init_qp_minus26"]
    old_qp = 26 + old_minus26

    # Round-trip identity — re-emitting parsed fields reproduces the
    # original PPS bytes exactly. The strongest possible parser /
    # emitter correctness check.
    round_trip = _emit_hevc_pps(s, fields)
    assert round_trip == pps_rbsp, (
        f"HEVC PPS round-trip drift:\n"
        f"  orig: {pps_rbsp.hex()}\n"
        f"  emit: {round_trip.hex()}")

    # Pick a meaningfully different QP.
    new_minus26 = 6  # QP=32, distinctly lower quality than QP=26
    new_fields = dict(fields)
    new_fields["init_qp_minus26"] = new_minus26
    new_pps_rbsp = _emit_hevc_pps(s, new_fields)
    re_parsed, _ = _parse_hevc_pps_full(s, new_pps_rbsp)
    assert re_parsed["init_qp_minus26"] == new_minus26
    for k, v in fields.items():
        if k == "init_qp_minus26":
            continue
        assert re_parsed[k] == v, (
            f"HEVC field {k} mutated unexpectedly: {v} -> {re_parsed[k]}")

    # Splice and verify ffmpeg accepts it.
    modified = (raw[: pps_start + sc_len + 2]
                + new_pps_rbsp
                + raw[pps_end:])
    out_path = sample.parent / "sample_hevc_qpbump.hevc"
    out_path.write_bytes(modified)
    result = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-f", "null", "-"],
        capture_output=True, text=True)
    assert result.returncode == 0, (
        f"ffmpeg rejected HEVC PPS re-emit: stderr={result.stderr}")
    probe = subprocess.run(
        ["ffprobe", "-loglevel", "error", "-count_frames",
         "-select_streams", "v:0", "-show_entries",
         "stream=nb_read_frames", "-of",
         "default=nokey=1:noprint_wrappers=1", str(out_path)],
        capture_output=True, text=True, check=True)
    n_frames = int(probe.stdout.strip())
    assert n_frames > 0

    # Pixel-level proof — the QP bump must reach dequantization.
    def frame_md5(path):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(path),
             "-f", "framemd5", "-"],
            capture_output=True, text=True, check=True)
        return r.stdout
    assert frame_md5(sample) != frame_md5(out_path), (
        "HEVC pixels identical — bump did not propagate to decoder")

    print(f"\n  HEVC QP-bump demo:")
    print(f"    init_qp_minus26: {old_minus26} -> {new_minus26}")
    print(f"    QP:              {old_qp} -> {26 + new_minus26}")
    print(f"    PPS RBSP:        {len(pps_rbsp)} -> {len(new_pps_rbsp)} bytes")
    print(f"    round-trip:      bit-exact (no parser drift)")
    print(f"    ffmpeg decoded {n_frames} frames from modified HEVC")
    print(f"    primitives used: SAME 4 as H.264 demo, no new code")


# --- JPEG: third codec family, image (not video), same primitives ----


def test_jpeg_dqt_quantization_table_bump():
    """Cross-family proof — bump the JPEG quantization table on a
    real ffmpeg-encoded .jpg using ONLY BitsAt/BitsWrite. JPEG is
    a completely different codec FAMILY (image, not video), uses
    SOI/EOI marker framing instead of Annex-B NALU, uses Huffman
    rather than Exp-Golomb for entropy. Yet the same universal
    primitives parse + modify it.

    Demonstrates the architectural ceiling: the agent expresses
    JPEG (and PNG, GIF, WebP, AVIF — every image codec) as Rules
    over per-codec graph structure with the same primitive set.
    No JPEG-specific runner code; no Huffman primitives needed for
    a QT bump because the DQT segment is u(8) fields throughout."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample = Path("/tmp/h264_demo/sample.jpg")
    if not sample.exists():
        sample.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x256:rate=1",
            "-frames:v", "1", "-q:v", "5", str(sample),
        ], check=True)

    raw = sample.read_bytes()
    s = Substrate()

    # Walk JPEG markers via BitsAt to find the DQT segment.
    buf_lit = Lit(raw)

    def byte_at(offset):
        return s._inner.evaluate(
            BitsAt(buf_lit, Lit(offset * 8), Lit(8)).to_dict(), {})

    def u16be_at(offset):
        return s._inner.evaluate(
            BitsAt(buf_lit, Lit(offset * 8), Lit(16)).to_dict(), {})

    # Scan for DQT marker (0xFFDB), via the primitives.
    assert byte_at(0) == 0xFF and byte_at(1) == 0xD8, "not a JPEG (no SOI)"
    i = 2
    dqt_offset = None
    while i < len(raw) - 4:
        if byte_at(i) == 0xFF:
            m = byte_at(i + 1)
            if m == 0xDB:  # DQT
                dqt_offset = i
                break
            if m == 0xD8 or m == 0xD9 or (0xD0 <= m <= 0xD7) or m == 0x00:
                i += 2
                continue
            seg_len = u16be_at(i + 2)
            i += 2 + seg_len
        else:
            i += 1
    assert dqt_offset is not None, "no DQT segment in JPEG"

    dqt_len = u16be_at(dqt_offset + 2)
    # DQT body starts after 2-byte marker + 2-byte length.
    body_start = dqt_offset + 4
    body_end = dqt_offset + 2 + dqt_len

    # Parse precision + table id (first byte of body).
    pq_tq = byte_at(body_start)
    precision = pq_tq >> 4  # 0 = 8-bit, 1 = 16-bit
    table_id = pq_tq & 0x0F
    assert precision == 0, "demo handles 8-bit-precision QTs only"
    n_values = 64
    expected_body_len = 1 + n_values
    assert body_end - body_start == expected_body_len, (
        f"DQT body length {body_end - body_start} != "
        f"expected {expected_body_len}; precision/header malformed")

    # Read all 64 Q-values via ONE BitsAtAll call (was 64 individual
    # BitsAt round-trips; the batched primitive runs ~50x faster).
    qt_reads = Vec(items=[
        Vec(items=[Lit((body_start + 1 + k) * 8), Lit(8)])
        for k in range(n_values)])
    old_qt = list(s._inner.evaluate(
        BitsAtAll(buf_lit, qt_reads).to_dict(), {}))

    # Pick a scale that meaningfully changes quality but stays within
    # the 1..255 valid range. 2.0x = aggressive quality reduction
    # (common transrate operation).
    scale = 2
    new_qt = [max(1, min(255, q * scale)) for q in old_qt]

    # Round-trip identity — re-writing the same values reproduces
    # the original bytes. ONE BitsWriteAll call (vs the previous
    # 64-call BitsWrite chain — 64x less buffer copying).
    identity_writes = Vec(items=[
        Vec(items=[Lit((body_start + 1 + k) * 8),
                   Lit(old_qt[k]), Lit(8)])
        for k in range(n_values)])
    rewritten = s._inner.evaluate(
        BitsWriteAll(Lit(raw), identity_writes).to_dict(), {})
    assert rewritten == raw, "JPEG re-write identity failed"

    # Apply the scale via the same one-shot primitive.
    scale_writes = Vec(items=[
        Vec(items=[Lit((body_start + 1 + k) * 8),
                   Lit(new_qt[k]), Lit(8)])
        for k in range(n_values)])
    modified = s._inner.evaluate(
        BitsWriteAll(Lit(raw), scale_writes).to_dict(), {})

    # Same file size (QT bump never changes length).
    assert len(modified) == len(raw)
    # Bytes outside the QT body unchanged.
    assert modified[: body_start + 1] == raw[: body_start + 1]
    assert modified[body_end:] == raw[body_end:]

    # Read back to confirm the bump took.
    mod_lit = Lit(modified)
    for k in range(n_values):
        got = s._inner.evaluate(
            BitsAt(mod_lit, Lit((body_start + 1 + k) * 8),
                   Lit(8)).to_dict(), {})
        assert got == new_qt[k]

    # ffmpeg must still decode the modified JPEG (the bitstream is
    # structurally valid; the visual output is intentionally
    # quantized harder, which would be the actual production
    # use case for a quality-tier downshift).
    out_path = sample.parent / "sample_jpeg_qtbump.jpg"
    out_path.write_bytes(modified)
    result = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-frames:v", "1", "-f", "null", "-"],
        capture_output=True, text=True)
    assert result.returncode == 0, (
        f"ffmpeg rejected JPEG QT-bump: stderr={result.stderr}")

    # Pixel-level proof — decode both JPEGs to raw, hash them, confirm
    # the QT change shifted dequantization.
    def jpeg_pixel_md5(path):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(path),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        import hashlib
        return hashlib.md5(r.stdout).hexdigest()
    assert jpeg_pixel_md5(sample) != jpeg_pixel_md5(out_path), (
        "JPEG decoded pixels identical — QT bump didn't affect output")

    print(f"\n  JPEG QT-bump demo:")
    print(f"    DQT precision:    {precision} (8-bit)")
    print(f"    DQT table id:     {table_id}")
    print(f"    Q-values scaled:  {n_values}, factor {scale}x")
    print(f"    old QT range:     {min(old_qt)}..{max(old_qt)}")
    print(f"    new QT range:     {min(new_qt)}..{max(new_qt)} (clamped 1..255)")
    print(f"    file size:        {len(raw)} bytes (preserved)")
    print(f"    ffmpeg decoded modified JPEG cleanly")
    print(f"    primitives used:  BitsAt + BitsWrite only (no Huffman/Exp-Golomb)")


# --- REAL file-size reduction: JPEG metadata strip via primitives ----


def test_jpeg_metadata_strip_reduces_file_size():
    """First demo that produces a SMALLER output file via primitives —
    strip non-essential JPEG markers (APPn / COM / EXIF) which often
    bloat photos with 100s of KB of metadata, leaving only the
    structurally-required segments (SOI / DQT / DHT / SOFn / SOS /
    entropy-coded scan / EOI).

    Real production op (privacy, CDN bandwidth, mobile delivery —
    `exiftool -all=` / `jpegtran -copy none` / `mogrify -strip`
    are the standard tools). Pure composition of BitsAt + byte
    slicing; no codec-specific runner code."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample = Path("/tmp/h264_demo/sample.jpg")
    if not sample.exists():
        sample.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x256:rate=1",
            "-frames:v", "1", "-q:v", "5", str(sample),
        ], check=True)

    # Build a bloated variant by inserting 5 × 8 KB COM segments
    # after SOI — simulates real-world EXIF / ICC profile / XMP
    # bloat (often 100s of KB on phone photos).
    src = sample.read_bytes()
    bloat_payload = b"X" * 8000
    com_segment = b"\xFF\xFE" + (len(bloat_payload) + 2).to_bytes(2, "big") + bloat_payload
    bloated = src[:2] + com_segment * 5 + src[2:]
    bloated_path = Path("/tmp/h264_demo/bloated_strip.jpg")
    bloated_path.write_bytes(bloated)

    s = Substrate()
    raw = bloated_path.read_bytes()
    buf_lit = Lit(raw)

    # Walk markers via BitsAt — collect (offset, marker_type, end)
    # for every segment, identify keepers.
    KEEP_MARKERS = {
        0xC0, 0xC1, 0xC2, 0xC3,  # SOF0..3 (baseline / extended / progressive / lossless)
        0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
        0xC4,  # DHT
        0xDB,  # DQT
        0xDD,  # DRI
        0xDA,  # SOS — plus entropy-coded scan to EOI
        0xD8,  # SOI
        0xD9,  # EOI
    }
    # The strippable set: APPn (0xE0..0xEF), COM (0xFE), and any
    # remaining JPEG-extensions (0xF0..0xFD) — everything not in
    # KEEP_MARKERS.

    def byte_at(off):
        return s._inner.evaluate(
            BitsAt(buf_lit, Lit(off * 8), Lit(8)).to_dict(), {})

    def u16be(off):
        return s._inner.evaluate(
            BitsAt(buf_lit, Lit(off * 8), Lit(16)).to_dict(), {})

    assert byte_at(0) == 0xFF and byte_at(1) == 0xD8, "not a JPEG"
    kept_ranges = [(0, 2)]  # SOI always kept
    i = 2
    stripped_marker_count = 0
    while i < len(raw):
        if byte_at(i) != 0xFF:
            i += 1
            continue
        m = byte_at(i + 1)
        if m == 0x00 or m == 0xFF:
            i += 1
            continue
        if m == 0xD8 or m == 0xD9 or (0xD0 <= m <= 0xD7):
            # markers without length
            if m in KEEP_MARKERS:
                kept_ranges.append((i, i + 2))
            i += 2
            continue
        seg_len = u16be(i + 2)
        seg_end = i + 2 + seg_len
        if m == 0xDA:  # SOS — include the entropy-coded scan up to EOI
            j = seg_end
            while j < len(raw) - 1:
                if (raw[j] == 0xFF and raw[j + 1] != 0x00
                        and not (0xD0 <= raw[j + 1] <= 0xD7)):
                    break
                j += 1
            # Tail (scan + final marker) always kept.
            kept_ranges.append((i, j))
            i = j
            continue
        if m in KEEP_MARKERS:
            kept_ranges.append((i, seg_end))
        else:
            stripped_marker_count += 1
        i = seg_end

    # Append final EOI if present.
    if raw[-2:] == b"\xFF\xD9":
        kept_ranges.append((len(raw) - 2, len(raw)))

    # Splice kept ranges into the output. Pure byte slicing — the
    # primitive role was finding the ranges, not assembling them.
    stripped = b"".join(raw[a:b] for a, b in kept_ranges)
    stripped_path = Path("/tmp/h264_demo/stripped.jpg")
    stripped_path.write_bytes(stripped)

    # File size MUST drop.
    assert len(stripped) < len(raw), (
        f"strip did not shrink file: {len(raw)} -> {len(stripped)}")

    # ffmpeg must decode the stripped version + produce the SAME
    # pixels as the bloated original (metadata strip is pixel-
    # invariant — that's what makes it safe).
    import hashlib

    def pixel_md5(path):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(path),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()

    bloated_md5 = pixel_md5(bloated_path)
    stripped_md5 = pixel_md5(stripped_path)
    assert bloated_md5 == stripped_md5, (
        "metadata strip changed pixels — bug in segment classifier?")

    print(f"\n  JPEG metadata strip demo:")
    print(f"    bloated size:    {len(raw):>7} bytes")
    print(f"    stripped size:   {len(stripped):>7} bytes  "
          f"(-{100*(len(raw)-len(stripped))/len(raw):.1f}%)")
    print(f"    segments stripped: {stripped_marker_count}")
    print(f"    pixel md5: IDENTICAL "
          f"(pixel-invariant operation, safe)")


# --- H.264 trim — real file-size reduction via NAL-level cut ---------


def test_h264_trim_at_keyframe_reduces_file_size():
    """Trim an H.264 stream at an IDR (keyframe) boundary — produces
    a SMALLER output file with no decode/re-encode. Real production
    op (TikTok-style clip, ad-break insertion, content moderation
    cut). The trimmed stream is independently decodable because IDR
    breaks all temporal-reference chains.

    Walk NAL units (start code + nal_unit_type) via BitsAt; locate
    the Nth IDR; truncate. Pure structural — no entropy decode, no
    requantization. Lossless w.r.t. the kept portion."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    src = Path("/tmp/h264_demo/gop.h264")
    if not src.exists():
        src.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=10:size=320x240:rate=30",
            "-c:v", "libx264", "-preset", "medium", "-g", "30",
            "-force_key_frames", "expr:gte(t,n_forced*1)",
            "-pix_fmt", "yuv420p", "-an", str(src),
        ], check=True)

    raw = src.read_bytes()
    s = Substrate()
    raw_lit = Lit(raw)

    # Walk NAL units, collect IDR offsets. Use BitsAt for the
    # nal_unit_type byte read (primitive-only path).
    def nal_type_at(off, sc_len):
        # Type = low 5 bits of first byte after start code.
        return s._inner.evaluate(
            BitsAt(raw_lit, Lit((off + sc_len) * 8 + 3),
                   Lit(5)).to_dict(), {})

    idr_offsets = []
    i = 0
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01":
            sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01":
            sc = 3
        else:
            i += 1
            continue
        if nal_type_at(i, sc) == 5:  # IDR
            idr_offsets.append(i)
        i += sc

    assert len(idr_offsets) >= 3, (
        f"need ≥3 IDRs to demo trim; got {len(idr_offsets)}")

    # Trim at the 5th IDR (~5 seconds into a 10-second 10-IDR stream).
    cut_at = idr_offsets[5]
    trimmed = raw[:cut_at]
    # Need the SPS+PPS preamble before any IDR for independent decode —
    # they're already at the start of the file before idr_offsets[0],
    # so a head-trim preserves them automatically.
    out_path = Path("/tmp/h264_demo/trimmed.h264")
    out_path.write_bytes(trimmed)

    # File size MUST drop.
    assert len(trimmed) < len(raw), "trim did not shrink"
    pct = 100 * (len(raw) - len(trimmed)) / len(raw)

    # ffmpeg must decode the trimmed stream — confirms IDR cut
    # produces an independently-decodable file.
    probe = subprocess.run(
        ["ffprobe", "-loglevel", "error", "-count_frames",
         "-select_streams", "v:0", "-show_entries",
         "stream=nb_read_frames", "-of",
         "default=nokey=1:noprint_wrappers=1", str(out_path)],
        capture_output=True, text=True, check=True)
    n_frames = int(probe.stdout.strip())

    orig_probe = subprocess.run(
        ["ffprobe", "-loglevel", "error", "-count_frames",
         "-select_streams", "v:0", "-show_entries",
         "stream=nb_read_frames", "-of",
         "default=nokey=1:noprint_wrappers=1", str(src)],
        capture_output=True, text=True, check=True)
    n_orig = int(orig_probe.stdout.strip())

    assert n_frames > 0
    assert n_frames < n_orig

    # Pixel verification: kept portion of trimmed must match the
    # equivalent prefix of the original. Decode both to raw, compare.
    import hashlib

    def first_n_frames_md5(path, n):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(path),
             "-vframes", str(n), "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()

    assert first_n_frames_md5(src, n_frames) == first_n_frames_md5(
        out_path, n_frames), (
        "trimmed frames differ from original prefix — IDR cut botched")

    print(f"\n  H.264 keyframe trim demo:")
    print(f"    IDRs found:      {len(idr_offsets)} at {idr_offsets}")
    print(f"    cut at IDR #5:   offset {cut_at}")
    print(f"    orig:            {len(raw):>7} bytes, {n_orig} frames")
    print(f"    trimmed:         {len(trimmed):>7} bytes, "
          f"{n_frames} frames  (-{pct:.1f}%)")
    print(f"    pixel verify:    kept frames bit-identical to original prefix")

