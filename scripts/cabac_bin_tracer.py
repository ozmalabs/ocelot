"""CABAC bin tracer — independent Python decoder + I-slice walker
that records every (label, ctx_idx, bin_val, p_state_before,
val_mps_before) tuple while parsing a byte stream from our Rust
encoder.

Goal: pinpoint exactly which bin (and which context) our Rust
walker emits differently from what a spec-compliant decoder
(libavcodec) would read. Two independent paths:

  1. Self-consistency check: our Rust encoder → this Python
     reference decoder. If it reads the same bins we wrote, our
     CABAC engine is correct (matching the cross-validation in
     tests/test_cabac_vs_reference.py).

  2. Trace inspection: print the (label, ctx, bin) sequence and
     compare against ITU-T §7.3.5 to find structural divergence
     — e.g., wrong syntax-element order, wrong context offset,
     spurious bins.

The Python reference is intentionally separate from our Rust
engine — it implements CABAC + the I-slice walker directly from
the spec.

Usage:
  python scripts/cabac_bin_tracer.py [--mb-width N --mb-height M]
                                     [--cbp HEX]

Default: 1×1 picture, 1 MB, CBP=0xF (the failing case). Prints
the bin-by-bin trace for the single MB.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Reuse the cross-validated engine pieces (RANGE_TAB_LPS, TRANS_IDX_*,
# PyCabacDecoder).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from test_cabac_vs_reference import (
    RANGE_TAB_LPS, TRANS_IDX_MPS, TRANS_IDX_LPS, PyCabacDecoder,
)
from substrate_rs._native import Substrate as NativeSubstrate
from substrate_rs import Substrate as WrappedSubstrate


# H.264 CABAC context init tables — fetched from our engine via a
# small round-trip helper. Equivalent to loading from
# cabac_init_tables.rs at startup.
def get_init_table(slice_type: str, init_idc: int = 0) -> list[tuple[int, int]]:
    """Return the (m, n) pairs for ctxIdx 0..1023, sourced from
    our Rust engine's authoritative tables."""
    s = NativeSubstrate()
    return s.cabac_init_table(slice_type, init_idc)


# Spec-compliant context init: §9.3.1.1.1
def init_ctx_from_mn(m: int, n: int, slice_qp: int) -> list[int]:
    qpy = max(0, min(51, slice_qp))
    pre = ((m * qpy) >> 4) + n
    pre = max(1, min(126, pre))
    if pre <= 63:
        return [63 - pre, 0]   # [p_state_idx, val_mps]
    return [pre - 64, 1]


def init_contexts(slice_type: str, init_idc: int, slice_qp: int) -> list[list[int]]:
    table = get_init_table(slice_type, init_idc)
    return [init_ctx_from_mn(m, n, slice_qp) for (m, n) in table]


class TraceEvent(NamedTuple):
    label: str
    ctx_idx: int
    bin_val: int
    p_state_before: int
    val_mps_before: int


class TracingPyDecoder(PyCabacDecoder):
    """Subclass that records every decode_bin / decode_bypass /
    decode_terminate call with the bin value, context index, and
    context state at the moment of decoding."""

    def __init__(self, buf: bytes, contexts: list[list[int]]):
        super().__init__(buf)
        self.contexts = contexts
        self.trace: list[TraceEvent] = []

    def decode_bin_ctx(self, ctx_idx: int, label: str) -> int:
        ctx = self.contexts[ctx_idx]
        p_before, mps_before = ctx[0], ctx[1]
        bin_val = self.decode_bin(ctx)
        self.trace.append(TraceEvent(label, ctx_idx, bin_val,
                                     p_before, mps_before))
        return bin_val

    def decode_bypass_t(self, label: str) -> int:
        bin_val = self.decode_bypass()
        self.trace.append(TraceEvent(label, -1, bin_val, -1, -1))
        return bin_val

    def decode_terminate_t(self, label: str) -> int:
        """§9.3.3.2.4 — terminate read. Self-contained; doesn't
        use a regular ctx."""
        self.range -= 2
        if self.offset >= self.range:
            bin_val = 1
        else:
            bin_val = 0
            self._renorm()
        self.trace.append(TraceEvent(label, -2, bin_val, -1, -1))
        return bin_val


# --- I-slice MB layer walker per ITU-T §7.3.5 ----------------------

def walk_i_nxn_mb(
    dec: TracingPyDecoder,
    mb_row: int,
    mb_col: int,
    left_mb: dict | None,
    top_mb: dict | None,
) -> dict:
    """Read one I_NxN MB. Returns dict with parsed fields + the
    16-element luma_cbf grid for the NEXT MB's neighbour context.
    """
    out = {"row": mb_row, "col": mb_col}

    # 1. mb_type. I-slice ctx 3 + condTermA + condTermB; both 0 for
    # I_NxN neighbours (or unavailable).
    cond_a = 0 if (left_mb is None or left_mb.get("is_i_nxn", True)) else 1
    cond_b = 0 if (top_mb is None or top_mb.get("is_i_nxn", True)) else 1
    ctx = 3 + cond_a + cond_b
    b0 = dec.decode_bin_ctx(ctx, f"mb_type/bin0[mb={mb_row},{mb_col}]")
    if b0 != 0:
        raise ValueError(f"expected I_NxN (bin0=0); got {b0}")
    out["is_i_nxn"] = True

    # 3. 16 × prev_intra4x4_pred_mode_flag
    for k in range(16):
        b = dec.decode_bin_ctx(68, f"prev_intra4x4/k={k}")
        if b == 0:
            # rem_intra4x4_pred_mode (3 FL bins, ctx 69)
            for j in range(3):
                _ = dec.decode_bin_ctx(69, f"rem_intra4x4/k={k},j={j}")

    # 4. intra_chroma_pred_mode (TU cMax=3, neighbour-aware bin 0)
    la = left_mb.get("chroma_mode") if left_mb else None
    ta = top_mb.get("chroma_mode") if top_mb else None
    cond_a = 1 if (la is not None and la != 0) else 0
    cond_b = 1 if (ta is not None and ta != 0) else 0
    ctx0 = 64 + cond_a + cond_b
    b = dec.decode_bin_ctx(ctx0, "intra_chroma/bin0")
    mode = 0
    if b == 1:
        mode = 1
        b = dec.decode_bin_ctx(67, "intra_chroma/bin1")
        if b == 1:
            mode = 2
            b = dec.decode_bin_ctx(67, "intra_chroma/bin2")
            if b == 1:
                mode = 3
    out["chroma_mode"] = mode

    # 5. CBP luma + chroma
    # cbp_luma: 4 bins, neighbour-aware contexts.
    # Inputs: left_mb_cbp + top_mb_cbp + this_so_far.
    left_cbp = left_mb.get("cbp_luma", 0xF) if left_mb else 0xF
    top_cbp = top_mb.get("cbp_luma", 0xF) if top_mb else 0xF
    nbr_table = [
        (1, 2),   # block 0
        (0, 3),   # block 1 (with this_so_far)
        (3, 0),   # block 2 (left_mb bit 3, this_so_far bit 0)
        (2, 1),   # block 3 (this_so_far bit 2 and 1)
    ]
    this_so_far = 0
    cbp_luma = 0
    for i in range(4):
        if i == 0:
            a_bit = (left_cbp >> 1) & 1
            b_bit = (top_cbp >> 2) & 1
        elif i == 1:
            a_bit = (this_so_far >> 0) & 1
            b_bit = (top_cbp >> 3) & 1
        elif i == 2:
            a_bit = (left_cbp >> 3) & 1
            b_bit = (this_so_far >> 0) & 1
        else:
            a_bit = (this_so_far >> 2) & 1
            b_bit = (this_so_far >> 1) & 1
        cond_a = 0 if a_bit else 1
        cond_b = 0 if b_bit else 1
        ctx = 73 + cond_a + 2 * cond_b
        bit = dec.decode_bin_ctx(ctx, f"cbp_luma/bit{i}")
        cbp_luma |= bit << i
        this_so_far |= bit << i
    out["cbp_luma"] = cbp_luma

    # cbp_chroma: bin 0 (any chroma), bin 1 (AC chroma)
    left_chroma = left_mb.get("cbp_chroma", 0) if left_mb else 0
    top_chroma = top_mb.get("cbp_chroma", 0) if top_mb else 0
    cond_a = 1 if left_chroma != 0 else 0
    cond_b = 1 if top_chroma != 0 else 0
    ctx = 77 + cond_a + 2 * cond_b
    b = dec.decode_bin_ctx(ctx, "cbp_chroma/bin0")
    cbp_chroma = 0
    if b == 1:
        cond_a = 1 if left_chroma == 2 else 0
        cond_b = 1 if top_chroma == 2 else 0
        ctx = 81 + cond_a + 2 * cond_b
        b1 = dec.decode_bin_ctx(ctx, "cbp_chroma/bin1")
        cbp_chroma = 2 if b1 == 1 else 1
    out["cbp_chroma"] = cbp_chroma

    # 6. mb_qp_delta if any CBP bit set
    if cbp_luma != 0 or cbp_chroma != 0:
        prev_zero = left_mb.get("mb_qp_zero", True) if left_mb else True
        ctx = 60 + (0 if prev_zero else 1)
        # mb_qp_delta unary: read 1-bits until a 0
        k = 0
        bin_idx = 0
        while True:
            ctx = 60 + (0 if prev_zero else 1) if bin_idx == 0 \
                  else (62 if bin_idx == 1 else 63)
            b = dec.decode_bin_ctx(ctx, f"mb_qp_delta/bin{bin_idx}")
            bin_idx += 1
            if b == 0:
                break
            k += 1
            if k > 51:
                break
        out["mb_qp_delta_k"] = k
        out["mb_qp_zero"] = (k == 0)
    else:
        out["mb_qp_zero"] = True

    # 7. Luma residual blocks — 16 × CBF + residual_block per
    # spec ordering [0,1,2,3]/[4,5,6,7]/[8,9,10,11]/[12,13,14,15].
    BLOCK_IDX_TO_RC = [
        (0, 0), (0, 1), (1, 0), (1, 1),
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 0), (2, 1), (3, 0), (3, 1),
        (2, 2), (2, 3), (3, 2), (3, 3),
    ]
    RC_TO_BLOCK = [
        [ 0,  1,  4,  5],
        [ 2,  3,  6,  7],
        [ 8,  9, 12, 13],
        [10, 11, 14, 15],
    ]
    this_cbf = [False] * 16
    for i8x8 in range(4):
        if (cbp_luma >> i8x8) & 1 == 0:
            continue
        for i4x4 in range(4):
            block_idx = i8x8 * 4 + i4x4
            br, bc = BLOCK_IDX_TO_RC[block_idx]
            if bc > 0:
                left_cbf = 1 if this_cbf[RC_TO_BLOCK[br][bc - 1]] else 0
            else:
                left_cbf = (1 if (left_mb and
                                  left_mb["luma_cbf"][RC_TO_BLOCK[br][3]])
                            else 0)
            if br > 0:
                top_cbf = 1 if this_cbf[RC_TO_BLOCK[br - 1][bc]] else 0
            else:
                top_cbf = (1 if (top_mb and
                                 top_mb["luma_cbf"][RC_TO_BLOCK[3][bc]])
                           else 0)
            ctx = 93 + left_cbf + 2 * top_cbf
            cbf = dec.decode_bin_ctx(
                ctx, f"luma_cbf/block{block_idx}@({br},{bc})",
            )
            this_cbf[block_idx] = (cbf == 1)
            if cbf:
                # Residual block — sig flags + last flags + level
                # For the diagnostic, just absorb without decoding
                # levels fully — but we MUST read at minimum the
                # significance map.
                _decode_residual_4x4(dec, block_idx)
    out["luma_cbf"] = this_cbf

    # 8. Chroma DC / AC — skipped for this diagnostic (cbp_chroma=0)
    if cbp_chroma >= 1:
        raise NotImplementedError("chroma residual decode not in tracer")

    return out


def _decode_residual_4x4(dec: TracingPyDecoder, block_idx: int) -> None:
    """Walk one 4x4 luma residual block per §9.3.3.1.1.6 + §9.3.3.2.
    Records bins to the trace. Just enough to advance the position;
    doesn't reconstruct coefficient values precisely."""
    # Luma 4x4: sig_off = 134, last_off = 195, abs_off = 247
    last_sig = -1
    sig_positions = []
    for i in range(15):
        sig = dec.decode_bin_ctx(134 + i, f"blk{block_idx}/sig{i}")
        if sig:
            sig_positions.append(i)
            is_last = dec.decode_bin_ctx(195 + i, f"blk{block_idx}/last{i}")
            if is_last:
                last_sig = i
                break
    if last_sig < 0:
        # position 15 implicit
        sig_positions.append(15)

    num_eq1 = 0
    num_gt1 = 0
    for pos in reversed(sig_positions):
        # coeff_abs_level_minus1: bin 0 ctxIdxInc depends on num_eq1,
        # num_gt1; subsequent bins use ctxIdxInc 5 (constant).
        # The exact formula per §9.3.3.1.1.7 — simplified here.
        ctx_inc = min(num_eq1 + 1, 4) if num_gt1 == 0 else 0
        ctx = 247 + ctx_inc
        b = dec.decode_bin_ctx(ctx, f"blk{block_idx}/abs0@pos{pos}")
        v = 0
        if b == 1:
            # value >= 1, read more bins. Unary with ctxIdxInc 5+.
            n = 1
            while n < 13:
                ctx = 247 + 5 + min(n - 1, 5 - 1)
                b = dec.decode_bin_ctx(ctx, f"blk{block_idx}/abs{n}@pos{pos}")
                if b == 0:
                    break
                n += 1
            else:
                # UEG0 suffix bypass bins — skip; this is an
                # over-simplification but the diagnostic case has
                # all-zero coefs so we never hit this path.
                pass
            v = n
        else:
            v = 0
        _ = dec.decode_bypass_t(f"blk{block_idx}/sign@pos{pos}")
        if v == 0:
            num_eq1 += 1
        else:
            num_gt1 += 1


def ebsp_to_rbsp(ebsp: bytes) -> bytes:
    """§7.4.1.1 inverse — drop emulation prevention bytes."""
    out = bytearray()
    i = 0
    while i < len(ebsp):
        if (i + 2 < len(ebsp) and ebsp[i] == 0 and ebsp[i + 1] == 0
                and ebsp[i + 2] == 3):
            out.append(0)
            out.append(0)
            i += 3
        else:
            out.append(ebsp[i])
            i += 1
    return bytes(out)


def extract_idr_cabac_payload(stream: bytes,
                              log2_max_frame_num: int = 4
                              ) -> tuple[bytes, int]:
    """Locate IDR NAL in an Annex B stream and return (cabac_bytes,
    slice_qp). Parses just enough of the slice header to find the
    CABAC start + read slice_qp_delta. Assumes the stream's PPS
    sets pic_init_qp_minus26 = -3 (the common x264 default for
    flat content); caller can adjust externally.
    """
    rbsp = None
    for i in range(len(stream) - 4):
        if stream[i:i + 4] == b"\x00\x00\x00\x01":
            nt = stream[i + 4] & 0x1F
            if nt == 5:
                rbsp = ebsp_to_rbsp(stream[i + 5:])
                break
        elif stream[i:i + 3] == b"\x00\x00\x01":
            nt = stream[i + 3] & 0x1F
            if nt == 5:
                rbsp = ebsp_to_rbsp(stream[i + 4:])
                break
    if rbsp is None:
        raise ValueError("no IDR NAL in stream")
    bp = 0

    def u(n: int) -> int:
        nonlocal bp
        v = 0
        for k in range(n):
            byte = rbsp[(bp + k) >> 3]
            bit = (byte >> (7 - ((bp + k) & 7))) & 1
            v = (v << 1) | bit
        bp += n
        return v

    def ue() -> int:
        m = 0
        while u(1) == 0 and m < 32:
            m += 1
        if m == 0:
            return 0
        return (1 << m) - 1 + u(m)

    def se() -> int:
        v = ue()
        return (v + 1) // 2 if v & 1 else -(v // 2)

    _first_mb = ue()
    _slice_type = ue()
    _pps_id = ue()
    _frame_num = u(log2_max_frame_num)
    _idr_pic_id = ue()
    _no_out = u(1)
    _long_term = u(1)
    qp_delta = se()
    while bp & 7 != 0:
        u(1)
    return rbsp[bp // 8:], qp_delta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb-width", type=int, default=1)
    ap.add_argument("--mb-height", type=int, default=1)
    ap.add_argument("--cbp", type=str, default="0xF")
    ap.add_argument("--slice-qp", type=int, default=0)
    ap.add_argument("--input-stream", type=str, default=None,
                    help="trace bins from an external H.264 stream "
                         "instead of encoding via our Rust walker")
    ap.add_argument("--pic-init-qp", type=int, default=23,
                    help="pic_init_qp from external stream's PPS "
                         "(used when --input-stream is set)")
    args = ap.parse_args()

    if args.input_stream:
        # Trace bins from an EXTERNAL stream (e.g. ffmpeg-encoded).
        with open(args.input_stream, "rb") as f:
            stream = f.read()
        cabac_bytes, qp_delta = extract_idr_cabac_payload(stream)
        slice_qp = args.pic_init_qp + qp_delta
        print(f"External IDR CABAC: {len(cabac_bytes)} bytes = "
              f"{cabac_bytes.hex()}")
        print(f"  slice_qp = pic_init_qp({args.pic_init_qp}) + "
              f"qp_delta({qp_delta}) = {slice_qp}")
        print()
        buf = cabac_bytes
    else:
        cbp = int(args.cbp, 0)
        n_mbs = args.mb_width * args.mb_height
        s = NativeSubstrate()
        luma = [0] * (n_mbs * 256)
        buf = s.h264_encode_i_slice_luma_only(
            args.mb_width, args.mb_height, 0, args.slice_qp,
            luma, [cbp] * n_mbs,
        )
        print(f"Encoded payload: {len(buf)} bytes = {buf.hex()}")
        print(f"  for {args.mb_width}×{args.mb_height} = {n_mbs} MBs "
              f"with cbp={cbp:#x}, slice_qp={args.slice_qp}")
        print()
        slice_qp = args.slice_qp

    mb_w = args.mb_width
    mb_h = args.mb_height

    # Initialise the Python reference contexts via the same formula
    # as our Rust engine — slice_type=I, slice_qp matches.
    contexts = init_contexts("I", 0, slice_qp)
    dec = TracingPyDecoder(bytes(buf), contexts)

    # Walk all MBs.
    grid: list[list[dict | None]] = [
        [None] * mb_w for _ in range(mb_h)
    ]
    aborted_at: tuple[int, int] | None = None
    for r in range(mb_h):
        if aborted_at:
            break
        for c in range(mb_w):
            left = grid[r][c - 1] if c > 0 else None
            top = grid[r - 1][c] if r > 0 else None
            try:
                mb = walk_i_nxn_mb(dec, r, c, left, top)
            except (ValueError, NotImplementedError) as e:
                print(f"  !! ABORT at MB({r},{c}): {e}")
                print(f"     trace length so far: {len(dec.trace)} bins")
                aborted_at = (r, c)
                break
            grid[r][c] = mb
            # end_of_slice_flag
            is_last = (r == mb_h - 1 and c == mb_w - 1)
            eos = dec.decode_terminate_t(
                f"end_of_slice/mb={r},{c}",
            )
            if eos != (1 if is_last else 0):
                print(f"  !! end_of_slice mismatch at MB({r},{c}): "
                      f"expected {1 if is_last else 0}, got {eos}")

    # Print the trace.
    print("Bin-by-bin trace (label  ctx  bin  p_state→val_mps):")
    for ev in dec.trace:
        if ev.ctx_idx >= 0:
            print(f"  {ev.label:40s}  ctx={ev.ctx_idx:3d}  "
                  f"bin={ev.bin_val}  "
                  f"p={ev.p_state_before:2d} mps={ev.val_mps_before}")
        else:
            kind = "bypass" if ev.ctx_idx == -1 else "term"
            print(f"  {ev.label:40s}  {kind:7s}  "
                  f"bin={ev.bin_val}")
    print()
    print(f"Total bins decoded: {len(dec.trace)}")
    print(f"Bits consumed: {dec.bit_pos} / {len(buf) * 8} buffer bits")


if __name__ == "__main__":
    main()
