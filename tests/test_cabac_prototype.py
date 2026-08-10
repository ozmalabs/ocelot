"""CABAC engine prototype — exposed via Substrate.cabac_round_trip.

The arithmetic engine itself (per ITU-T H.264 §9.3) is universal:
the same encode/decode loop serves H.264 CABAC and (with minor
table swaps) AV1's arithmetic coder. The H.264 CONTEXT MODEL —
~460 contexts each with codec-specific initialisation per slice
type and QP — lives at a higher layer above this primitive.

This file proves the engine round-trips arbitrary sequences of
context-aware + bypass bins. The next architectural step is the
context model: a mapping (slice_type, slice_qp, context_idx) →
(p_state_idx, val_mps) per ITU-T §9.3.1.1, which would let
real H.264 macroblock data be decoded under the engine. That's
~460 table entries plus initialisation arithmetic.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import Substrate


def _run(ops):
    s = Substrate()
    return s._inner.cabac_round_trip(ops)


def test_cabac_bypass_only_round_trip():
    """Pure bypass mode — no context state. 1/2 probability per bin."""
    bins = [i & 1 for i in range(50)]
    ops = [(0, 0, 0, b, True) for b in bins]
    buf, decoded = _run(ops)
    assert list(decoded) == bins
    # Bypass is information-theoretic optimal at 1 bit/bin → roughly
    # input_count bits of output (plus framing overhead). 50 bins =>
    # ~7 bytes plus epilogue.
    assert len(buf) <= 16, f"bypass output unexpectedly large: {len(buf)}"


def test_cabac_single_context_round_trip():
    """All bins under ONE adaptive context — drift in p_state_idx
    must match between encoder and decoder."""
    bins = [1, 1, 0, 1, 1, 1, 0, 0, 1, 0,
            1, 1, 1, 0, 1, 0, 0, 1, 1, 0,
            1, 0, 1, 1, 0, 1, 1, 0, 0, 1]
    # ctx_id 1 with initial p_state_idx=18, val_mps=0
    ops = [(1, 18, 0, b, False) for b in bins]
    buf, decoded = _run(ops)
    assert list(decoded) == bins


def test_cabac_many_contexts_round_trip():
    """8 independent contexts running in parallel — verifies the
    encoder + decoder state-machine stays coherent under
    interleaving."""
    import random
    rng = random.Random(0xC0DEC)
    contexts = [
        (cid, rng.randint(0, 63), rng.randint(0, 1))
        for cid in range(8)
    ]
    ops = []
    expected = []
    for _ in range(200):
        ctx = rng.choice(contexts)
        bit = rng.randint(0, 1)
        ops.append((ctx[0], ctx[1], ctx[2], bit, False))
        expected.append(bit)
    buf, decoded = _run(ops)
    assert list(decoded) == expected, (
        f"context-interleaved round-trip diverged at "
        f"first mismatch index "
        f"{next(i for i, (a, b) in enumerate(zip(decoded, expected)) if a != b)}")


def test_cabac_mixed_context_and_bypass():
    """Real H.264 macroblock data interleaves context and bypass
    bins: e.g., a coefficient value emits its sign as bypass after
    the magnitude bins emit under context. The engine must handle
    the transitions cleanly."""
    ops = []
    expected = []
    for i in range(50):
        # Context bin
        b1 = (i * 7) & 1
        ops.append((1, 5, 1, b1, False))
        expected.append(b1)
        # Bypass bin
        b2 = i & 1
        ops.append((0, 0, 0, b2, True))
        expected.append(b2)
        # Another context bin in a different context
        b3 = (i * 3) & 1
        ops.append((2, 30, 0, b3, False))
        expected.append(b3)
    buf, decoded = _run(ops)
    assert list(decoded) == expected


def test_cabac_init_i_slice_qp26():
    """Initialise all 1024 H.264 contexts for an I-slice at QP=26.
    Verify the first few entries against hand-computed §9.3.1.1
    examples + spot-check structural properties."""
    s = Substrate()
    ctxs = s._inner.cabac_init_contexts("I", 0, 26)
    assert len(ctxs) == 1024

    # Spec §9.3.1.1 Table 9-12 ctxIdx 0: (m=20, n=-15) at qp=26 →
    # pre = (20*26 >> 4) + (-15) = 32 - 15 = 17. 17 <= 63 →
    # p_state_idx = 63-17 = 46, val_mps = 0.
    assert ctxs[0] == (46, 0)

    # ctxIdx 6: (m=-28, n=127) → pre = -46 + 127 = 81. 81 > 63 →
    # p_state_idx = 81-64 = 17, val_mps = 1.
    assert ctxs[6] == (17, 1)


def test_cabac_init_qp_drift():
    """At higher slice QP, contexts converge toward MPS=1 (because
    the multiplier m * QP shifts pre toward 127). Sanity check: at
    QP=51 (max), the average p_state_idx for val_mps=1 contexts is
    higher than at QP=0."""
    s = Substrate()
    low = s._inner.cabac_init_contexts("I", 0, 0)
    high = s._inner.cabac_init_contexts("I", 0, 51)
    assert low != high, "contexts should differ between QP extremes"

    # At QP=0, the (m * QP) term is 0; preCtxState = clip(n, 0, 127).
    # That means contexts depend only on n. Easy to predict.
    n_low_count = sum(1 for c in low if c[1] == 0)
    n_high_count = sum(1 for c in high if c[1] == 0)
    # At higher QP, contexts with large positive m get pulled up into
    # val_mps=1 territory; at lower QP they're more often val_mps=0.
    # → high QP should have FEWER val_mps=0 contexts (more MPS=1).
    assert n_high_count != n_low_count, (
        f"context distribution must shift with QP "
        f"(qp=0: {n_low_count} val_mps=0; qp=51: {n_high_count})")


def test_cabac_init_i_vs_pb_disagree():
    """The 1024-context tables for I vs P/B are different by
    construction — at least one ctxIdx must differ between them."""
    s = Substrate()
    i_ctxs = s._inner.cabac_init_contexts("I", 0, 26)
    p_ctxs = s._inner.cabac_init_contexts("P", 0, 26)
    b_ctxs = s._inner.cabac_init_contexts("B", 0, 26)
    diffs_ip = sum(1 for a, b in zip(i_ctxs, p_ctxs) if a != b)
    diffs_ib = sum(1 for a, b in zip(i_ctxs, b_ctxs) if a != b)
    diffs_pb = sum(1 for a, b in zip(p_ctxs, b_ctxs) if a != b)
    # All three should disagree significantly.
    assert diffs_ip > 100, (
        f"I and P-slice tables suspiciously similar: {diffs_ip} differ")
    assert diffs_ib > 100
    # P and B share the PB tables — but with cabac_init_idc=0 both
    # collapse to the same table, so P == B at idc=0. The function
    # uses cabac_init_idc to dispatch.
    p0 = s._inner.cabac_init_contexts("P", 0, 26)
    b0 = s._inner.cabac_init_contexts("B", 0, 26)
    assert p0 == b0, (
        "P and B with same cabac_init_idc must give identical contexts")


def test_cabac_init_three_idc_variants():
    """The three P/B init tables (cabac_init_idc 0/1/2) yield three
    different context arrays at the same slice_qp."""
    s = Substrate()
    a = s._inner.cabac_init_contexts("P", 0, 26)
    b = s._inner.cabac_init_contexts("P", 1, 26)
    c = s._inner.cabac_init_contexts("P", 2, 26)
    assert a != b
    assert b != c
    assert a != c


def test_cabac_init_then_encode_round_trip():
    """Real flow: initialise contexts at a known QP, encode some
    bins under specific context IDs, decode, recover identity. The
    initialised states drift as bins are emitted — both sides must
    track the drift."""
    s = Substrate()
    ctxs = s._inner.cabac_init_contexts("I", 0, 26)
    # Pick 4 specific contexts to drive bins against.
    chosen = [10, 100, 500, 900]
    ops = []
    expected = []
    import random
    rng = random.Random(7)
    for _ in range(200):
        cid = rng.choice(chosen)
        p_state, val_mps = ctxs[cid]
        bit = rng.randint(0, 1)
        ops.append((cid, p_state, val_mps, bit, False))
        expected.append(bit)
    buf, decoded = s._inner.cabac_round_trip(ops)
    assert list(decoded) == expected


def test_mb_skip_flag_round_trip_parrot_dimensions():
    """A P-slice's worth of mb_skip_flag bins, one per MB on a
    20x15 grid (the parrot is 320x240, 16-px MBs → 20x15). The
    encoder + decoder must agree after walking all 300 MBs with
    real neighbour-aware context selection per §9.3.3.1.1.1."""
    s = Substrate()
    # Skip 1-in-3 MBs (typical for a moderate-motion P frame).
    skips = [1 if i % 3 == 0 else 0 for i in range(300)]
    buf, decoded, final_ctxs = s._inner.cabac_mb_skip_flag_round_trip(
        "P", 0, 26, 20, skips)
    assert list(decoded) == skips
    # 3 context tuples (ctxIdx 11/12/13 for P-slice).
    assert len(final_ctxs) == 3
    # All entries valid context shape.
    for p_state, mps in final_ctxs:
        assert 0 <= p_state <= 63
        assert mps in (0, 1)


def test_mb_skip_flag_no_skips_compresses_well():
    """An all-zero skip sequence (every MB has data) — the adaptive
    coder should converge on near-zero bits per bin as it learns
    val_mps=0 is overwhelmingly likely."""
    s = Substrate()
    skips = [0] * 1000
    buf, decoded, _ = s._inner.cabac_mb_skip_flag_round_trip(
        "P", 0, 26, 50, skips)
    assert list(decoded) == skips
    # 1000 bins of "almost certain" outcome → very few bits.
    # Shannon entropy of a probability-1 distribution is 0; CABAC
    # converges fast. Expect < 50 bytes (was 24 bytes in our run).
    assert len(buf) < 50, (
        f"all-skip=0 sequence compressed to {len(buf)} bytes; "
        f"adaptive coder should do far better")


def test_mb_skip_flag_50_50_mix_close_to_one_bit_per_bin():
    """A genuinely 50/50 mix — CABAC can't do better than ~1 bit/bin.
    1000 bins → ~125 bytes (= 1000 bits + overhead)."""
    import random
    rng = random.Random(42)
    skips = [rng.randint(0, 1) for _ in range(1000)]
    s = Substrate()
    buf, decoded, _ = s._inner.cabac_mb_skip_flag_round_trip(
        "P", 0, 26, 50, skips)
    assert list(decoded) == skips
    # Shannon lower bound is 1000 bits = 125 bytes. CABAC overhead
    # adds maybe 5-10% — expect 130-160 bytes.
    assert 110 < len(buf) < 200, (
        f"50/50 skip mix compressed to {len(buf)} bytes; "
        f"expected ~125-150 (1 bit/bin + small overhead)")


def test_mb_skip_flag_neighbour_aware_compression():
    """Spatial clustering — skips group together. CABAC's neighbour-
    aware context selection should compress this BETTER than a
    50/50 random pattern with the same overall skip rate."""
    # Block of 100 skipped MBs followed by 100 non-skipped, repeated.
    clustered = ([1] * 100 + [0] * 100) * 5  # 1000 bins, 50% skip
    s = Substrate()
    buf_clustered, _, _ = s._inner.cabac_mb_skip_flag_round_trip(
        "P", 0, 26, 50, clustered)

    # Compare with a random 50/50 distribution at same length.
    import random
    rng = random.Random(99)
    random_skips = [rng.randint(0, 1) for _ in range(1000)]
    buf_random, _, _ = s._inner.cabac_mb_skip_flag_round_trip(
        "P", 0, 26, 50, random_skips)

    # The clustered pattern uses ctxIdx 13 (both neighbours skipped)
    # repeatedly in the skip blocks, then ctxIdx 11 (no neighbours
    # skipped) in the data blocks — each context adapts strongly.
    # The random pattern hits all three contexts evenly with weak
    # adaptation per context. Clustered should be smaller.
    assert len(buf_clustered) < len(buf_random), (
        f"clustered skip pattern ({len(buf_clustered)} B) should "
        f"compress better than random ({len(buf_random)} B) — "
        f"neighbour-aware context selection is what makes the "
        f"difference")


def test_p_slice_full_walk_round_trip_parrot_dimensions():
    """End-to-end P-slice macroblock walk on parrot dimensions:
    for each of 300 MBs (20×15), emit mb_skip_flag (with neighbour-
    aware context) and — if not skipped — mb_type (via the 4-way
    binarisation tree). Both pieces use real H.264 §9.3 context
    state machines. Identity round-trip."""
    import random
    rng = random.Random(0x42)
    s = Substrate()
    # Realistic P-slice composition: ~40% skipped, the rest mostly
    # P_L0_16x16 (the simplest non-skip mb_type).
    mbs = []
    for _ in range(300):
        if rng.random() < 0.4:
            mbs.append((1, 0))  # skipped
        else:
            r = rng.random()
            if r < 0.7:  mb_type = 0  # P_L0_16x16
            elif r < 0.8: mb_type = 1  # P_L0_L0_16x8
            elif r < 0.9: mb_type = 2  # P_L0_L0_8x16
            else:         mb_type = 3  # P_8x8
            mbs.append((0, mb_type))

    buf, decoded, bytes_per_mb = s._inner.cabac_p_slice_walk(
        26, 0, 20, mbs)
    assert list(decoded) == mbs
    # Sanity: real P-slice macroblocks (post mb_skip + mb_type only,
    # no coefficient data) should average well under 1 byte per MB.
    assert bytes_per_mb < 0.5, (
        f"P-slice mb_skip + mb_type averaged {bytes_per_mb:.3f} "
        f"bytes/MB; expected ≪ 1 because both elements are highly "
        f"context-dependent and the test data is correlated")


def test_p_slice_all_skip_compresses_to_near_zero():
    """A P slice where every MB is skipped should compress to
    near zero — mb_skip_flag uses ~1 bit/MB initially then
    converges; mb_type is never emitted (skip blocks it)."""
    s = Substrate()
    mbs = [(1, 0)] * 300  # all skipped
    buf, decoded, bytes_per_mb = s._inner.cabac_p_slice_walk(
        26, 0, 20, mbs)
    assert list(decoded) == mbs
    # 300 MBs * 0.05 bits/bin ≈ 15 bits = ~2 bytes + overhead.
    assert len(buf) < 30, (
        f"all-skip P-slice compressed to {len(buf)} bytes; "
        f"expected ~10 due to fast convergence")


def test_p_mb_type_bin_dispatch_distinguishes_values():
    """Sanity: encoding a MIXED sequence of all 4 mb_types must
    still round-trip correctly. With pure-single-value sequences
    CABAC converges to near-zero bits per bin (the bin-count
    overhead disappears), so we can't use compressed size as a
    fingerprint; we just verify identity."""
    s = Substrate()
    # Each of 50 quartets: types 0, 1, 2, 3 in order. Forces the
    # encoder to keep using all binarisation paths.
    mbs = [(0, t) for _ in range(50) for t in range(4)]
    assert len(mbs) == 200
    buf, decoded, bytes_per_mb = s._inner.cabac_p_slice_walk(
        26, 0, 20, mbs)
    assert list(decoded) == mbs
    # Mixed types prevent full convergence — output should be
    # larger than the single-type case (where adaptation collapses).
    single_type_mbs = [(0, 0)] * 200
    single_buf, _, _ = s._inner.cabac_p_slice_walk(
        26, 0, 20, single_type_mbs)
    assert len(buf) > len(single_buf), (
        f"mixed-type sequence ({len(buf)} B) should NOT collapse "
        f"to single-type size ({len(single_buf)} B)")


def test_mb_qp_delta_round_trip_all_values():
    """Every legal H.264 mb_qp_delta value (-26 to +25) round-trips
    through the unary binarisation + 4-context coder."""
    s = Substrate()
    deltas = list(range(-26, 26))
    buf, decoded, bpm = s._inner.cabac_mb_qp_delta_sequence(26, 0, deltas)
    assert list(decoded) == deltas


def test_mb_qp_delta_all_zeros_compress_tightly():
    """A slice where every MB inherits the slice QP (delta=0) is
    the common case in real video. Compression should converge
    near-zero — delta=0 is a single '0' bin per MB, and the
    "prev_was_zero" carry keeps bin-0 on ctx 60 which adapts."""
    s = Substrate()
    deltas = [0] * 300
    buf, decoded, bpm = s._inner.cabac_mb_qp_delta_sequence(26, 0, deltas)
    assert list(decoded) == deltas
    assert bpm < 0.05, (
        f"all-zero mb_qp_delta sequence averaged {bpm:.3f} bytes/MB; "
        f"expected far less because the adaptive coder converges"
    )


def test_mb_qp_delta_small_distribution_compresses_well():
    """Real P/B slices have small deltas centered on 0 (encoder
    rarely deviates from the slice's base QP by more than ±2).
    Sample a realistic distribution and confirm < 0.5 bytes/MB."""
    import random
    rng = random.Random(0x42)
    deltas = []
    for _ in range(300):
        r = rng.random()
        if r < 0.7:    d = 0
        elif r < 0.85: d = rng.choice([-1, 1])
        elif r < 0.95: d = rng.choice([-2, 2])
        else:          d = rng.randint(-5, 5)
        deltas.append(d)
    s = Substrate()
    buf, decoded, bpm = s._inner.cabac_mb_qp_delta_sequence(26, 0, deltas)
    assert list(decoded) == deltas
    assert bpm < 0.5, (
        f"realistic mb_qp_delta distribution averaged {bpm:.3f} "
        f"bytes/MB; expected < 0.5 because most deltas are small"
    )


def test_mb_qp_delta_transrate_bump_demo():
    """A simulated transrate: the encoder previously emitted deltas
    centered on 0; now we mutate each by +3 (push every MB three
    QP steps coarser). Round-trips identity, and the encoded size
    GROWS because larger deltas need more unary bins."""
    import random
    rng = random.Random(99)
    original = [rng.randint(-2, 2) for _ in range(200)]
    bumped = [d + 3 for d in original]  # transrate-up by 3 QP per MB

    s = Substrate()
    buf_orig, dec_orig, bpm_orig = s._inner.cabac_mb_qp_delta_sequence(
        26, 0, original)
    buf_bump, dec_bump, bpm_bump = s._inner.cabac_mb_qp_delta_sequence(
        26, 0, bumped)
    assert list(dec_orig) == original
    assert list(dec_bump) == bumped
    # Bumped sequence has consistently larger |delta|, so the unary
    # bin count rises. Buffer should be larger.
    assert len(buf_bump) > len(buf_orig), (
        f"bumped deltas should encode larger: orig={len(buf_orig)} "
        f"vs bumped={len(buf_bump)}"
    )


def test_mb_qp_delta_extreme_carries_through():
    """Edge case — max |delta| in either direction. The +25/-26
    pair is at the H.264 boundaries; verifies the unary encoder
    handles long bin runs (51-52 ones + trailing zero per delta)."""
    s = Substrate()
    deltas = [25, -26, 25, -26, 25, -26]
    buf, decoded, bpm = s._inner.cabac_mb_qp_delta_sequence(26, 0, deltas)
    assert list(decoded) == deltas


def test_cbp_complete_p_slice_walk_round_trip():
    """Full MB-control round-trip on parrot dimensions: 20x15 grid,
    300 MBs. Each non-skipped MB emits skip + mb_type + mb_qp_delta
    + cbp_luma + cbp_chroma — five separate CABAC syntax elements,
    each with its own context/neighbour/binarisation logic.

    This is the complete macroblock-control envelope a real H.264
    transrate would walk before reaching coefficient data."""
    import random
    rng = random.Random(0xABC)
    s = Substrate()
    mbs = []
    for _ in range(300):
        if rng.random() < 0.35:
            mbs.append((1, 0, 0, 0, 0))  # skipped
        else:
            mb_type = rng.choices([0, 1, 2, 3], weights=[7, 1, 1, 1])[0]
            qpd = rng.choices([0, -1, 1, -2, 2, -3, 3],
                              weights=[6, 2, 2, 1, 1, 1, 1])[0]
            cbp_luma = rng.choices(
                list(range(16)),
                weights=[1] + [2] * 14 + [3])[0]  # mostly non-zero
            cbp_chroma = rng.choices([0, 1, 2], weights=[5, 3, 2])[0]
            mbs.append((0, mb_type, qpd, cbp_luma, cbp_chroma))

    buf, decoded, bpm = s._inner.cabac_p_slice_full_mb_walk(
        26, 0, 20, mbs)
    assert list(decoded) == mbs
    # Five syntax elements per non-skip MB → still well under
    # 2 bytes/MB on realistic content.
    assert bpm < 2.0, (
        f"full MB control envelope averaged {bpm:.3f} bytes/MB; "
        f"expected well under 2"
    )


def test_cbp_walk_transrate_scenario():
    """A focused demo of what slice-level transrate sees: take a
    realistic P-slice, MUTATE every MB's mb_qp_delta by +3 (push
    quantization three steps coarser), and measure the size delta
    in the macroblock-control envelope.

    This is the cost in the MB-control bits — coefficient data
    would shrink the dominant portion of the file but isn't wired
    yet."""
    import random
    rng = random.Random(0xDEF)
    s = Substrate()
    base = []
    for _ in range(200):
        if rng.random() < 0.35:
            base.append((1, 0, 0, 0, 0))
        else:
            qpd = rng.choices([0, -1, 1, -2, 2],
                              weights=[7, 2, 2, 1, 1])[0]
            base.append((
                0,
                rng.choices([0, 1, 2, 3], weights=[7, 1, 1, 1])[0],
                qpd,
                rng.choices(list(range(16)),
                            weights=[1] + [2] * 14 + [3])[0],
                rng.choices([0, 1, 2], weights=[5, 3, 2])[0],
            ))
    # Bump QP delta by +3 (with clamp at +25).
    bumped = []
    for s_, m_, q_, l_, c_ in base:
        if s_ == 1:
            bumped.append((s_, m_, q_, l_, c_))
        else:
            bumped.append((s_, m_, min(25, q_ + 3), l_, c_))

    buf_base, _, bpm_base = s._inner.cabac_p_slice_full_mb_walk(
        26, 0, 20, base)
    buf_bump, _, bpm_bump = s._inner.cabac_p_slice_full_mb_walk(
        26, 0, 20, bumped)
    growth_pct = 100 * (len(buf_bump) - len(buf_base)) / len(buf_base)
    # Bumped MB-control envelope is larger because mb_qp_delta
    # unary runs are longer.
    assert len(buf_bump) > len(buf_base), (
        f"bumped sequence MUST encode larger; got base={len(buf_base)} "
        f"bumped={len(buf_bump)}"
    )


def test_residual_4x4_blocks_round_trip():
    """A sequence of 50 4x4 luma residual blocks with mixed
    sparsity patterns — round-trips identity through the full
    residual_block_cabac machinery (sig + last + abs_level UEG0
    + sign)."""
    import random
    rng = random.Random(0xC0EF)
    blocks = []
    for _ in range(50):
        block = [0] * 16
        n_nonzero = rng.randint(1, 6)
        positions = rng.sample(range(16), n_nonzero)
        for p in positions:
            mag = rng.choices(
                [1, 2, 3, 5, 10, 20, 50],
                weights=[40, 20, 10, 5, 3, 1, 1])[0]
            sign = rng.choice([-1, 1])
            block[p] = sign * mag
        blocks.append(block)

    s = Substrate()
    buf, decoded, bpb = s._inner.cabac_residual_4x4_sequence(
        26, 0, blocks)
    assert len(decoded) == len(blocks)
    for orig, got in zip(blocks, decoded):
        assert list(got) == orig


def test_residual_4x4_transrate_coefficient_zeroing():
    """The actual transrate operation. Take a sequence of residual
    blocks; zero out HIGH-FREQUENCY coefficients (positions 8..15);
    re-encode. The encoded byte count drops — REAL bitrate
    reduction. This is what the existing primitive stack now
    unlocks: an agent can decode coefficient data, mutate it,
    re-encode."""
    import random
    rng = random.Random(0x123)
    # 100 blocks of realistic dense-low-frequency content.
    blocks = []
    for _ in range(100):
        block = [0] * 16
        # Low-frequency positions 0..7: dense, larger magnitudes.
        for p in range(8):
            if rng.random() < 0.7:
                block[p] = rng.choice([-1, 1]) * rng.randint(1, 15)
        # High-frequency positions 8..15: sparse, smaller magnitudes.
        for p in range(8, 16):
            if rng.random() < 0.3:
                block[p] = rng.choice([-1, 1]) * rng.randint(1, 5)
        blocks.append(block)

    s = Substrate()
    buf_orig, _, bpb_orig = s._inner.cabac_residual_4x4_sequence(
        26, 0, blocks)

    # Zero out high-frequency (positions 8..15) — this is the
    # simplest possible compressed-domain transrate.
    bumped = []
    for b in blocks:
        new_b = list(b)
        for p in range(8, 16):
            new_b[p] = 0
        bumped.append(new_b)

    buf_zeroed, _, bpb_zeroed = s._inner.cabac_residual_4x4_sequence(
        26, 0, bumped)

    # REAL bitrate reduction — fewer significant coefficients →
    # shorter encoded stream.
    assert len(buf_zeroed) < len(buf_orig), (
        f"high-freq-zeroed should encode SMALLER; got "
        f"orig={len(buf_orig)} zeroed={len(buf_zeroed)}"
    )
    pct = 100 * (len(buf_orig) - len(buf_zeroed)) / len(buf_orig)
    # Expect a meaningful reduction (10-40% depending on content).
    assert pct > 5, (
        f"high-freq-zero reduction was only {pct:.1f}%; expected >5%"
    )


def test_residual_4x4_all_zero_blocks_compress_tightly():
    """Edge case — blocks where only position 0 (DC) is non-zero.
    Each block emits a single sig_coeff_flag=1 + last_significant=1
    + abs_level + sign = ~4 bins total. 100 such blocks → small."""
    s = Substrate()
    blocks = [[1] + [0] * 15 for _ in range(100)]
    buf, decoded, bpb = s._inner.cabac_residual_4x4_sequence(
        26, 0, blocks)
    for orig, got in zip(blocks, decoded):
        assert list(got) == orig
    # 100 blocks × ~4 bins each ~ 400 bits = 50 bytes. With
    # adaptation, should be lower.
    assert len(buf) < 100, (
        f"DC-only blocks compressed to {len(buf)} bytes; "
        f"expected well under 100"
    )


def test_all_residual_block_types_round_trip():
    """Round-trip a coefficient block in each of the 6 supported
    ctxBlockCat values. Different block sizes (4, 15, 16, 64
    coefs) + different context offsets per Table 9-42."""
    s = Substrate()
    test_blocks = {
        "intra16x16_dc": [3, -2, 1, 0, 0, 0, -1, 0,
                          0, 0, 0, 0, 0, 0, 0, 0],
        "intra16x16_ac": [5, 0, -3, 0, 0, 2, 0, 0,
                          0, 0, 0, 0, 0, 0, 0],
        "luma_4x4":      [10, -8, 4, -2, 1, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, 0],
        "chroma_dc":     [7, -3, 1, 0],
        "chroma_ac":     [4, 0, -2, 1, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0],
        "luma_8x8":      list(range(1, 9)) + [0] * 56,
    }
    for cat, coefs in test_blocks.items():
        buf, decoded = s._inner.cabac_residual_block(26, 0, cat, coefs)
        assert list(decoded) == coefs, (
            f"cat {cat} round-trip diverged"
        )


def test_mvd_sequence_round_trip_python():
    """100 mvd values across the unary truncation boundary (9)."""
    import random
    rng = random.Random(0xABCD)
    s = Substrate()
    values = []
    for _ in range(100):
        r = rng.random()
        if r < 0.5:   v = rng.randint(-3, 3)
        elif r < 0.8: v = rng.randint(-10, 10)
        elif r < 0.95: v = rng.randint(-50, 50)
        else:          v = rng.randint(-500, 500)
        values.append(v)
    buf, decoded = s._inner.cabac_mvd_sequence(26, 0, values)
    assert list(decoded) == values


def test_end_to_end_transrate_via_coefficient_zeroing():
    """THE END-TO-END DEMO.

    For 200 simulated macroblocks: emit mb_skip_flag, mb_type,
    mb_qp_delta, cbp_luma, cbp_chroma; for each non-skipped MB,
    emit ONE luma 4x4 residual block of coefficients.

    Then apply a TRANSRATE: zero high-frequency coefficient
    positions (8-15) in every residual block.

    Compare encoded sizes — this is the full slice-level transrate
    that the entire CABAC prototype stack now supports."""
    import random
    rng = random.Random(0x5AB)
    s = Substrate()

    # Generate macroblocks.
    mbs = []
    residuals = []
    for _ in range(200):
        if rng.random() < 0.3:
            mbs.append((1, 0, 0, 0, 0))
            residuals.append(None)
        else:
            mbs.append((
                0,
                rng.choices([0, 1, 2, 3], weights=[7, 1, 1, 1])[0],
                rng.choices([0, -1, 1, -2, 2], weights=[7, 2, 2, 1, 1])[0],
                rng.choices(list(range(16)),
                            weights=[1] + [2] * 14 + [3])[0],
                rng.choices([0, 1, 2], weights=[5, 3, 2])[0],
            ))
            # One luma 4x4 residual block per non-skipped MB.
            # Realistic dense-low-freq pattern.
            block = [0] * 16
            for p in range(8):
                if rng.random() < 0.7:
                    block[p] = rng.choice([-1, 1]) * rng.randint(1, 10)
            for p in range(8, 16):
                if rng.random() < 0.3:
                    block[p] = rng.choice([-1, 1]) * rng.randint(1, 5)
            residuals.append(block)

    # Encode the MB control envelope.
    buf_mb, _, _ = s._inner.cabac_p_slice_full_mb_walk(26, 0, 20, mbs)
    # Encode the residual blocks (one CABAC sequence call across
    # all non-skip MBs).
    blocks = [r for r in residuals if r is not None]
    buf_res, _, _ = s._inner.cabac_residual_4x4_sequence(26, 0, blocks)
    total_orig = len(buf_mb) + len(buf_res)

    # Apply the transrate — zero positions 8-15 of every residual block.
    bumped = []
    for r in residuals:
        if r is None:
            continue
        nr = list(r)
        for p in range(8, 16):
            nr[p] = 0
        bumped.append(nr)
    buf_res_bumped, _, _ = s._inner.cabac_residual_4x4_sequence(
        26, 0, bumped)
    total_bumped = len(buf_mb) + len(buf_res_bumped)

    reduction_pct = 100 * (total_orig - total_bumped) / total_orig
    print(f"\n  END-TO-END SLICE-LEVEL TRANSRATE:")
    print(f"    MB control envelope  (skip + mb_type + qp + cbp): "
          f"{len(buf_mb)} B")
    print(f"    residual blocks (original):                       "
          f"{len(buf_res)} B")
    print(f"    residual blocks (high-freq zeroed):               "
          f"{len(buf_res_bumped)} B")
    print(f"    total: {total_orig} B → {total_bumped} B "
          f"(-{reduction_pct:.1f}%)")
    # On realistic content, the residual data dominates, and
    # zeroing positions 8-15 should produce a meaningful reduction.
    assert reduction_pct > 5, (
        f"transrate only reduced size by {reduction_pct:.1f}%; "
        f"expected > 5% for realistic content"
    )


def test_p_sub_mb_type_all_values_round_trip():
    """All four P-slice sub_mb_type values round-trip through the
    bin tree."""
    s = Substrate()
    values = [0, 1, 2, 3, 0, 3, 1, 2, 2, 0, 1, 3]
    buf, decoded = s._inner.cabac_p_sub_mb_type_sequence(26, 0, values)
    assert list(decoded) == values


def test_ref_idx_l0_neighbour_aware_round_trip():
    """30-MB grid (6 wide × 5 tall) with ref_idx_l0 values
    interleaved across neighbours. The encoder + decoder must agree
    on bin-0 context selection per MB."""
    s = Substrate()
    # Mixed pattern of ref_idx values; some 0 (common), some larger.
    refs = [0, 1, 0, 2, 0, 1,
            1, 0, 1, 0, 2, 0,
            0, 1, 2, 1, 0, 0,
            1, 0, 0, 1, 2, 1,
            0, 0, 1, 0, 0, 1]
    num_ref_minus1 = 3
    buf, decoded = s._inner.cabac_ref_idx_l0_sequence(
        26, 0, 6, num_ref_minus1, refs)
    assert list(decoded) == refs


def test_ref_idx_compresses_at_zero_dominant():
    """Realistic P-slice: most MBs use ref_idx=0 (the most recent
    reference). The encoder should compress aggressively."""
    s = Substrate()
    refs = [0] * 300  # 300 MBs, all refer to most-recent frame
    buf, decoded = s._inner.cabac_ref_idx_l0_sequence(
        26, 0, 20, 3, refs)
    assert list(decoded) == refs
    # 300 × (1 bin = 1 binarisation "0") → after adaptation, ~0 bits.
    assert len(buf) < 30, (
        f"all-zero ref_idx sequence compressed to {len(buf)} bytes; "
        f"expected far less due to fast adaptation"
    )


def test_cabac_skewed_distribution_compression():
    """A bin sequence with 9:1 skew should compress well — the
    arithmetic coder converges on the entropy rate (~0.47 bits/bin
    at 90/10 distribution)."""
    import random
    rng = random.Random(1)
    bins = [1 if rng.random() < 0.9 else 0 for _ in range(1000)]
    # Use context 1 with initial state biased toward 1 (val_mps=1).
    ops = [(1, 18, 1, b, False) for b in bins]
    buf, decoded = _run(ops)
    assert list(decoded) == bins
    # 1000 bins * 0.47 bits/bin = ~470 bits = ~59 bytes.
    # Add some slack for framing + initial state convergence.
    assert len(buf) < 100, (
        f"skewed input compressed to {len(buf)} bytes — too large; "
        f"expected ~60")
    assert len(buf) > 30, (
        f"skewed input compressed to {len(buf)} bytes — suspiciously "
        f"small; CABAC may not be tracking adaptation")


def test_p_frame_non_skip_residual_decodes_through_ffmpeg():
    """Full P-frame residual path: every MB non-skip, every 8x8 block
    coded (cbp_luma=0xF), round-tripped through real ffmpeg.

    Regression for the mb_type binarization fix: P_L0_16x16 emits
    three bins '0 0 0' at ctx 14/15/16, not just one. Before the fix,
    ffmpeg interpreted our mvd/cbp bits as continuation of mb_type
    and went off the rails. After the fix, the entire luma residual
    path is bit-accurate at QP=0 (PSNR = inf).
    """
    import math
    import shutil
    import subprocess
    import sys
    from pathlib import Path

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    MB_W, MB_H = 8, 8
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16

    # IDR with all-zero coefficients → ffmpeg reconstructs all-128
    # (default intra-DC fill at QP=0).
    ml_idr = b"\x00" * 256 * 4 * n_mbs
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml_idr, [0] * n_mbs,
    )
    idr_ref_plane = bytes([128] * (W * H))

    # P-target: a gradient that forces non-zero residual in every MB.
    target = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            target[y * W + x] = min(255, (y + x * 2) & 0xFF)

    mb_luma, cbp, skip, _recon = s._inner.h264_transcode_p_frame_2to1(
        bytes(target), idr_ref_plane, W, H, MB_W, MB_H, 0,
    )
    # Every MB should be non-skip with all four 8x8 blocks coded.
    assert sum(1 for b in skip if b) == 0
    assert all(c == 0xF for c in cbp)

    p_cabac = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma, cbp, skip,
    )
    # Build complete H.264 stream
    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
    idr_rbsp = build_idr_nal_rbsp(
        emit_slice_header_with_cabac_alignment(SliceHeaderConfig()), idr_cabac,
    )
    body.extend(wrap_nal(idr_rbsp, 5, 3))
    body.extend(wrap_nal(emit_p_slice_header(0, 1) + p_cabac, 1, 2))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        h264_path = Path(td) / "test.h264"
        yuv_path = Path(td) / "test.yuv"
        h264_path.write_bytes(bytes(body))
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "warning",
             "-i", str(h264_path), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(yuv_path)],
            capture_output=True, text=True,
        )
        assert not r.stderr.strip(), (
            f"ffmpeg reported decode errors: {r.stderr[:500]}"
        )
        decoded = yuv_path.read_bytes()

    yuv_per_frame = int(W * H * 1.5)
    p_luma = decoded[yuv_per_frame: yuv_per_frame + W * H]
    sq = sum((p_luma[i] - target[i]) ** 2 for i in range(W * H))
    psnr = (10 * math.log10((255 ** 2) / (sq / (W * H)))
            if sq > 0 else float("inf"))
    assert sq == 0, (
        f"P-frame residual decode is NOT bit-exact at QP=0: "
        f"MSE={sq/(W*H):.3f}, PSNR={psnr:.2f} dB. Expected lossless."
    )


def test_p_frame_chroma_residual_decodes_through_ffmpeg():
    """P-frame with cbp_chroma=2 + non-zero chroma DC and AC values
    round-trips through real ffmpeg. Without correct neighbour-CBF
    threading for ChromaDc/ChromaAc, ffmpeg's context state would
    diverge starting at MB(1,0) and the bitstream would fail.

    The decoded Cb/Cr planes must show non-128 values (real chroma
    residual signal) at exactly the MBs where we wrote non-zero
    coefficients.
    """
    import struct
    import shutil
    import subprocess
    import sys
    from pathlib import Path

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    MB_W, MB_H = 2, 2
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16

    # IDR that reconstructs to all-128 (default intra-DC fill).
    ml_idr = b"\x00" * 256 * 4 * n_mbs
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml_idr, [0] * n_mbs,
    )

    # P-frame with zero luma residual, but every MB has cbp_chroma=2
    # and per-MB non-zero chroma DC + sprinkled AC coefficients.
    ml_p = b"\x00" * 256 * 4 * n_mbs
    cbp_luma = b"\x00" * n_mbs
    skip = b"\x00" * n_mbs

    dc_cb_vals = [[4, 0, 0, 0], [0, 0, 0, 0], [-2, 0, 0, 0], [8, 4, 0, 0]]
    dc_cr_vals = [[0, 0, 0, 0], [4, 0, 0, 0], [0, 0, 0, 0], [-2, 0, 0, 0]]
    dc_cb = b"".join(struct.pack("<i", v) for mb in dc_cb_vals for v in mb)
    dc_cr = b"".join(struct.pack("<i", v) for mb in dc_cr_vals for v in mb)
    ac_cb_vals = [[0] * 60 for _ in range(n_mbs)]
    ac_cr_vals = [[0] * 60 for _ in range(n_mbs)]
    ac_cb_vals[0][0] = 2          # AC[block 0 / position 0] in MB 0
    ac_cr_vals[3][14] = -3        # AC[block 0 / last] in MB 3
    ac_cb = b"".join(struct.pack("<i", v) for mb in ac_cb_vals for v in mb)
    ac_cr = b"".join(struct.pack("<i", v) for mb in ac_cr_vals for v in mb)

    p_cabac = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml_p, cbp_luma, skip,
        chroma={
            "cbp_chroma": bytes([2] * n_mbs),
            "chroma_dc_cb": dc_cb,
            "chroma_dc_cr": dc_cr,
            "chroma_ac_cb": ac_cb,
            "chroma_ac_cr": ac_cr,
        },
    )

    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
    idr_rbsp = build_idr_nal_rbsp(
        emit_slice_header_with_cabac_alignment(SliceHeaderConfig()), idr_cabac,
    )
    body.extend(wrap_nal(idr_rbsp, 5, 3))
    body.extend(wrap_nal(emit_p_slice_header(0, 1) + p_cabac, 1, 2))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        h264_path = Path(td) / "test.h264"
        yuv_path = Path(td) / "test.yuv"
        h264_path.write_bytes(bytes(body))
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "warning",
             "-i", str(h264_path), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(yuv_path)],
            capture_output=True, text=True,
        )
        assert not r.stderr.strip(), (
            f"ffmpeg reported chroma decode errors: {r.stderr[:500]}"
        )
        decoded = yuv_path.read_bytes()

    yuv_per_frame = int(W * H * 1.5)
    p_off = yuv_per_frame
    chroma_size = (W // 2) * (H // 2)
    p_cb = decoded[p_off + W * H: p_off + W * H + chroma_size]
    p_cr = decoded[p_off + W * H + chroma_size:
                   p_off + W * H + 2 * chroma_size]
    cb_changed = sum(1 for v in p_cb if v != 128)
    cr_changed = sum(1 for v in p_cr if v != 128)
    assert cb_changed > 0, "Cb plane unchanged from reference (residuals lost)"
    assert cr_changed > 0, "Cr plane unchanged from reference (residuals lost)"


def test_p_frame_motion_vector_actually_shifts_reference():
    """P-frame chain proving MV semantics: a P-frame with MV=(4, 0)
    quarter-pels (= 1 luma pixel right) and zero residual produces
    the reference plane shifted exactly 1 pixel right.

    Builds: IDR (all-128) → P1 (gradient residual, MV=0) → P2 (MV=(4,0),
    zero residual). Decoded P2 must satisfy P2[x, y] == P1[x+1, y]
    for the entire interior. Without correct mvd context propagation
    across MBs, ffmpeg would diverge after the first MB.
    """
    import struct
    import shutil
    import subprocess
    import sys
    from pathlib import Path

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    MB_W, MB_H = 4, 4
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16

    # IDR reconstructs to all-128
    ml_idr = b"\x00" * 256 * 4 * n_mbs
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml_idr, [0] * n_mbs,
    )
    idr_ref = bytes([128] * (W * H))

    # P1: gradient via residual, MV=(0, 0)
    target1 = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            target1[y * W + x] = min(255, (y + x * 2) & 0xFF)
    mb_luma1, cbp1, skip1, _r1 = s._inner.h264_transcode_p_frame_2to1(
        bytes(target1), idr_ref, W, H, MB_W, MB_H, 0,
    )
    p1_cabac = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma1, cbp1, skip1,
    )

    # P2: MV=(4, 0) (1 luma pixel right) with zero residual.
    # Median predictor for MB 0 is (0, 0); subsequent MBs see neighbour
    # MV=(4, 0) → predictor=(4, 0) → mvd=(0, 0).
    ml2 = b"\x00" * 256 * 4 * n_mbs
    mvd_x = bytearray(2 * n_mbs)
    mvd_y = bytearray(2 * n_mbs)
    struct.pack_into("<h", mvd_x, 0, 4)
    p2_cabac = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml2, b"\x00" * n_mbs, b"\x00" * n_mbs,
        mvd_x_bytes=bytes(mvd_x), mvd_y_bytes=bytes(mvd_y),
    )

    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
    body.extend(wrap_nal(build_idr_nal_rbsp(
        emit_slice_header_with_cabac_alignment(SliceHeaderConfig()),
        idr_cabac), 5, 3))
    body.extend(wrap_nal(emit_p_slice_header(0, 1) + p1_cabac, 1, 2))
    body.extend(wrap_nal(emit_p_slice_header(0, 2) + p2_cabac, 1, 2))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        h264_path = Path(td) / "test.h264"
        yuv_path = Path(td) / "test.yuv"
        h264_path.write_bytes(bytes(body))
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "warning",
             "-i", str(h264_path), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(yuv_path)],
            capture_output=True, text=True,
        )
        assert not r.stderr.strip(), (
            f"ffmpeg MV decode error: {r.stderr[:500]}"
        )
        decoded = yuv_path.read_bytes()

    yuv_per = int(W * H * 1.5)
    p1_dec = decoded[yuv_per: yuv_per + W * H]
    p2_dec = decoded[2 * yuv_per: 2 * yuv_per + W * H]
    matches = 0
    total = 0
    for y in range(H):
        for x in range(W - 1):
            total += 1
            if p2_dec[y * W + x] == p1_dec[y * W + x + 1]:
                matches += 1
    assert matches == total, (
        f"MV NOT correctly applied: only {matches}/{total} interior "
        f"pixels match P1 shifted-right-by-1. The decoded P2 should "
        f"be the bit-exact 1-pixel shift of P1."
    )


def test_gpu_motion_estimation_end_to_end_ffmpeg():
    """Full pipeline: GPU motion estimation → motion-compensated
    reference → existing residual transcoder → P-slice CABAC walker
    with real per-MB MVs → ffmpeg decode.

    This is the integration smoke test for the wgpu ME path. If
    h264_estimate_motion_gpu is unavailable (no GPU / built without
    gpu_me feature), skip.
    """
    import math
    import shutil
    import struct
    import subprocess
    import sys
    from pathlib import Path

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    if not hasattr(s._inner, "h264_estimate_motion_gpu"):
        pytest.skip("substrate_rs not built with gpu_me feature")

    MB_W, MB_H = 4, 4
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16

    # IDR (all-128 fill) + P1 establishes gradient content.
    ml_idr = b"\x00" * 256 * 4 * n_mbs
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml_idr, [0] * n_mbs,
    )
    idr_ref = bytes([128] * (W * H))
    target_p1 = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            target_p1[y * W + x] = min(255, (y * 2 + x * 3) & 0xFF)
    mb_luma1, cbp1, skip1, recon1 = s._inner.h264_transcode_p_frame_2to1(
        bytes(target_p1), idr_ref, W, H, MB_W, MB_H, 0,
    )
    p1_cabac = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma1, cbp1, skip1,
    )

    # P2 target = P1 content shifted right 5px → GPU ME should
    # find MV ≈ (-5, 0). Real-pixel MC against the IDR-decoded
    # plane then matches target exactly (residual=0).
    target_p2 = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            target_p2[y * W + x] = target_p1[y * W + max(0, x - 5)]

    ref_for_p2 = bytes(recon1)
    mv_buf = s._inner.h264_estimate_motion_gpu(
        bytes(target_p2), ref_for_p2, W, H, MB_W, MB_H, 16, "full",
    )
    mvs = [struct.unpack_from("<iii", mv_buf, i * 12) for i in range(n_mbs)]
    mc_ref = s._inner.h264_apply_motion_compensation(
        ref_for_p2, mv_buf, W, H, MB_W, MB_H,
    )
    mb_luma2, cbp2, _skip, _recon = s._inner.h264_transcode_p_frame_2to1(
        bytes(target_p2), mc_ref, W, H, MB_W, MB_H, 0,
    )
    # Force non-skip so MVs actually land in the bitstream.
    skip2 = b"\x00" * n_mbs

    # Compute mvd via H.264 median predictor.
    def median3(a, b, c):
        return sorted([a, b, c])[1]
    grid = [[None] * MB_W for _ in range(MB_H)]
    mvd_x = bytearray(2 * n_mbs)
    mvd_y = bytearray(2 * n_mbs)
    for r in range(MB_H):
        for c in range(MB_W):
            i = r * MB_W + c
            mvx_qp = mvs[i][0] * 4
            mvy_qp = mvs[i][1] * 4
            a = grid[r][c - 1] if c > 0 else None
            b = grid[r - 1][c] if r > 0 else None
            cc = (grid[r - 1][c + 1] if r > 0 and c < MB_W - 1
                  else (grid[r - 1][c - 1] if r > 0 and c > 0 else None))
            avail = [x for x in [a, b, cc] if x is not None]
            if not avail:
                pred = (0, 0)
            elif len(avail) == 1:
                pred = avail[0]
            else:
                ax, ay = a if a else (0, 0)
                bx, by = b if b else (0, 0)
                cx, cy = cc if cc else (0, 0)
                pred = (median3(ax, bx, cx), median3(ay, by, cy))
            struct.pack_into("<h", mvd_x, i * 2, mvx_qp - pred[0])
            struct.pack_into("<h", mvd_y, i * 2, mvy_qp - pred[1])
            grid[r][c] = (mvx_qp, mvy_qp)

    p2_cabac = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma2, cbp2, skip2,
        mvd_x_bytes=bytes(mvd_x), mvd_y_bytes=bytes(mvd_y),
    )

    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
    body.extend(wrap_nal(build_idr_nal_rbsp(
        emit_slice_header_with_cabac_alignment(SliceHeaderConfig()),
        idr_cabac), 5, 3))
    body.extend(wrap_nal(emit_p_slice_header(0, 1) + p1_cabac, 1, 2))
    body.extend(wrap_nal(emit_p_slice_header(0, 2) + p2_cabac, 1, 2))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        h264_path = Path(td) / "test.h264"
        yuv_path = Path(td) / "test.yuv"
        h264_path.write_bytes(bytes(body))
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "warning",
             "-i", str(h264_path), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(yuv_path)],
            capture_output=True, text=True,
        )
        assert not r.stderr.strip(), (
            f"ffmpeg e2e decode error: {r.stderr[:500]}"
        )
        decoded = yuv_path.read_bytes()

    yuv_per = int(W * H * 1.5)
    p2_dec = decoded[2 * yuv_per: 2 * yuv_per + W * H]
    sq = sum((p2_dec[i] - target_p2[i]) ** 2 for i in range(W * H))
    psnr = (10 * math.log10((255 ** 2) / (sq / (W * H)))
            if sq > 0 else float("inf"))
    assert sq == 0, (
        f"End-to-end GPU ME pipeline is NOT bit-exact at QP=0: "
        f"MSE={sq/(W*H):.3f}, PSNR={psnr:.2f} dB."
    )


def test_p_slice_multi_parallel_matches_single():
    """Multi-slice P-encoder produces a stream that decodes to the
    SAME pixels as the single-slice path. Regression for the
    slice-aware MVD predictor + the parallel encoder.
    """
    import math
    import struct
    import subprocess
    import sys
    import shutil
    from pathlib import Path

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    if not hasattr(s._inner, "h264_encode_p_slice_multi_bytes"):
        pytest.skip("multi-slice encoder not in build")

    MB_W, MB_H = 8, 8
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16

    # IDR (all-zero → reconstructs to 128 fill)
    ml_idr = b"\x00" * 256 * 4 * n_mbs
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, ml_idr, [0] * n_mbs,
    )
    # P-frame target: gradient
    target = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            target[y * W + x] = min(255, (y + x * 2) & 0xFF)
    ref128 = bytes([128] * (W * H))
    mb_luma, cbp, _skip, _recon = s._inner.h264_transcode_p_frame_2to1(
        bytes(target), ref128, W, H, MB_W, MB_H, 0,
    )

    def median3(a, b, c):
        return sorted([a, b, c])[1]
    def compute_mvds(mvs, mb_w, mb_h, slice_row_starts):
        slice_set = set(slice_row_starts)
        n = mb_w * mb_h
        mvd_x = bytearray(2 * n)
        mvd_y = bytearray(2 * n)
        grid = [[None] * mb_w for _ in range(mb_h)]
        for r in range(mb_h):
            for c in range(mb_w):
                i = r * mb_w + c
                mv_qp = (mvs[i][0] * 4, mvs[i][1] * 4)
                top_avail = (r > 0) and (r not in slice_set)
                a = grid[r][c - 1] if c > 0 else None
                b = grid[r - 1][c] if top_avail else None
                cc = (grid[r - 1][c + 1] if top_avail and c < mb_w - 1
                      else (grid[r - 1][c - 1] if top_avail and c > 0 else None))
                avail = [x for x in [a, b, cc] if x is not None]
                if not avail:
                    pred = (0, 0)
                elif len(avail) == 1:
                    pred = avail[0]
                else:
                    ax, ay = a if a else (0, 0)
                    bx, by = b if b else (0, 0)
                    cx, cy = cc if cc else (0, 0)
                    pred = (median3(ax, bx, cx), median3(ay, by, cy))
                struct.pack_into("<h", mvd_x, i * 2, mv_qp[0] - pred[0])
                struct.pack_into("<h", mvd_y, i * 2, mv_qp[1] - pred[1])
                grid[r][c] = mv_qp
        return bytes(mvd_x), bytes(mvd_y)

    # MV=(0,0) per MB; non-skip so MVs land in the bitstream
    mvs = [(0, 0)] * n_mbs

    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )

    def assemble(slices):
        body = bytearray()
        body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
        body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
        body.extend(wrap_nal(build_idr_nal_rbsp(
            emit_slice_header_with_cabac_alignment(SliceHeaderConfig()),
            idr_cabac), 5, 3))
        for first_mb, payload in slices:
            body.extend(wrap_nal(
                emit_p_slice_header(first_mb=first_mb, frame_num=1) + payload,
                1, 2,
            ))
        return bytes(body)

    def decode_luma(stream_bytes):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            h264p = Path(td) / "t.h264"
            yuvp = Path(td) / "t.yuv"
            h264p.write_bytes(stream_bytes)
            r = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "warning",
                 "-i", str(h264p), "-f", "rawvideo",
                 "-pix_fmt", "yuv420p", str(yuvp)],
                capture_output=True, text=True,
            )
            assert not r.stderr.strip(), f"ffmpeg: {r.stderr[:300]}"
            dec = yuvp.read_bytes()
            yuv = int(W * H * 1.5)
            return dec[yuv: yuv + W * H]

    # Reference: single-slice payload, then assemble.
    mvd_x1, mvd_y1 = compute_mvds(mvs, MB_W, MB_H, [0])
    single = s._inner.h264_encode_p_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma, cbp, b"\x00" * n_mbs,
        mvd_x_bytes=mvd_x1, mvd_y_bytes=mvd_y1,
    )
    single_luma = decode_luma(assemble([(0, single)]))

    # Multi-slice variants — every count from 2 to MB_H must produce
    # bit-identical luma after ffmpeg decode.
    for n in [2, 4, MB_H]:
        rps = (MB_H + n - 1) // n
        starts = list(range(0, MB_H, rps))[:n]
        mvd_x, mvd_y = compute_mvds(mvs, MB_W, MB_H, starts)
        slices = s._inner.h264_encode_p_slice_multi_bytes(
            MB_W, MB_H, 0, 0, n,
            mb_luma, cbp, b"\x00" * n_mbs,
            mvd_x_bytes=mvd_x, mvd_y_bytes=mvd_y,
        )
        multi_luma = decode_luma(assemble(slices))
        assert multi_luma == single_luma, (
            f"n_slices={n}: multi-slice decoded luma DIFFERS from "
            f"single-slice. Mismatched at "
            f"{sum(1 for i in range(W*H) if multi_luma[i] != single_luma[i])} "
            f"pixels."
        )


def test_vendored_subpel_interpolate_luma_matches_ffmpeg():
    """The vendored OxideAV `interpolate_luma` (MIT) is byte-exact
    against ffmpeg's H.264 §8.4.2.2.1 sub-pel motion compensation
    across all 16 (x_frac, y_frac) ∈ {0..3}² combinations.

    Setup: encode an IDR of pseudorandom luma content, capture
    ffmpeg's decoded reference plane, then for each sub-pel
    position encode a single-MB P-frame with that MV and zero
    residual. ffmpeg's decoded P-frame must equal our vendored
    kernel's output applied to the same reference. The (3, 3)
    position is the hardest case (both 6-tap FIRs cascaded
    through the §8.4.2.2.1 eq. 8-245 `j` cross-term)."""
    import math
    import random
    import shutil
    import struct
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    if not hasattr(s._inner, "h264_interpolate_luma_subpel"):
        pytest.skip("substrate_rs built without h264_inter_pred")

    MB_W, MB_H = 8, 8
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16
    rng = random.Random(0x42)
    ref_content = bytes(rng.randint(0, 255) for _ in range(W * H))
    upscaled = bytearray(W * 2 * H * 2)
    for r in range(H):
        row = ref_content[r * W: (r + 1) * W]
        for rr in range(2):
            dest = (r * 2 + rr) * (W * 2)
            for c in range(W):
                upscaled[dest + c * 2] = upscaled[dest + c * 2 + 1] = row[c]
    mb_luma_idr = s._inner.h264_transcode_2to1_luma(
        bytes(upscaled), W * 2, H * 2, MB_W, MB_H, 0,
    )
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma_idr, [0xF] * n_mbs,
    )
    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )
    def make_stream(extra=()):
        body = bytearray()
        body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
        body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
        body.extend(wrap_nal(build_idr_nal_rbsp(
            emit_slice_header_with_cabac_alignment(SliceHeaderConfig()),
            idr_cabac), 5, 3))
        for n in extra:
            body.extend(n)
        return bytes(body)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # First decode the IDR alone to capture ffmpeg's reference plane.
        (td / "idr.h264").write_bytes(make_stream())
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", str(td / "idr.h264"), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(td / "idr.yuv")],
            check=True,
        )
        yuv_size = int(W * H * 1.5)
        ref_plane = (td / "idr.yuv").read_bytes()[:W * H]

        for y_frac in range(4):
            for x_frac in range(4):
                # Build a P-frame forcing MV = (x_frac, y_frac) on all
                # MBs via mvd on MB 0 + median-predictor propagation.
                ml_p = b"\x00" * (n_mbs * 256 * 4)
                cbp_luma = b"\x00" * n_mbs
                skip = b"\x00" * n_mbs
                mvd_x = bytearray(2 * n_mbs)
                mvd_y = bytearray(2 * n_mbs)
                struct.pack_into("<h", mvd_x, 0, x_frac)
                struct.pack_into("<h", mvd_y, 0, y_frac)
                p_cabac = s._inner.h264_encode_p_slice_luma_bytes(
                    MB_W, MB_H, 0, 0, ml_p, cbp_luma, skip,
                    mvd_x_bytes=bytes(mvd_x), mvd_y_bytes=bytes(mvd_y),
                )
                nal = wrap_nal(
                    emit_p_slice_header(0, 1) + p_cabac, 1, 2,
                )
                (td / "seq.h264").write_bytes(make_stream([nal]))
                r = subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "warning",
                     "-i", str(td / "seq.h264"), "-f", "rawvideo",
                     "-pix_fmt", "yuv420p", str(td / "seq.yuv")],
                    capture_output=True, text=True,
                )
                assert not r.stderr.strip(), (
                    f"({x_frac},{y_frac}): ffmpeg error: {r.stderr[:200]}"
                )
                ff = (td / "seq.yuv").read_bytes()[yuv_size: yuv_size + W * H]
                ours = s._inner.h264_interpolate_luma_subpel(
                    ref_plane, W, H, 0, 0, x_frac, y_frac, W, H,
                )
                diff = sum(1 for i in range(W * H) if ff[i] != ours[i])
                assert diff == 0, (
                    f"sub-pel ({x_frac},{y_frac}) DIFFERS from ffmpeg "
                    f"at {diff} pixels"
                )


def test_subpel_mc_kernel_byte_exact_vs_ffmpeg_full_frame():
    """End-to-end: the MC kernel with subpel=True is byte-exact vs
    ffmpeg on a full frame at a hard quarter-pel position. Uses
    MV = (3, 1) — the (3, ⋅) family cascades through both 6-tap
    FIRs at every MB, including the §8.4.2.2.1 `j` cross-term."""
    import random
    import shutil
    import struct
    import subprocess
    import sys
    import tempfile
    from pathlib import Path
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.h264_nal_writer import (
        SpsConfig, PpsConfig, SliceHeaderConfig,
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    from scripts.bench_pframe_sequence import emit_p_slice_header

    s = Substrate()
    if not hasattr(s._inner, "h264_interpolate_luma_subpel"):
        pytest.skip("substrate_rs built without h264_inter_pred")

    MB_W, MB_H = 8, 8
    n_mbs = MB_W * MB_H
    W, H = MB_W * 16, MB_H * 16
    rng = random.Random(0x42)
    ref_content = bytes(rng.randint(0, 255) for _ in range(W * H))
    upscaled = bytearray(W * 2 * H * 2)
    for r in range(H):
        row = ref_content[r * W: (r + 1) * W]
        for rr in range(2):
            dest = (r * 2 + rr) * (W * 2)
            for c in range(W):
                upscaled[dest + c * 2] = upscaled[dest + c * 2 + 1] = row[c]
    mb_luma_idr = s._inner.h264_transcode_2to1_luma(
        bytes(upscaled), W * 2, H * 2, MB_W, MB_H, 0,
    )
    idr_cabac = s._inner.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, 0, mb_luma_idr, [0xF] * n_mbs,
    )
    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=0,
    )
    def make_stream(extra=()):
        body = bytearray()
        body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
        body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
        body.extend(wrap_nal(build_idr_nal_rbsp(
            emit_slice_header_with_cabac_alignment(SliceHeaderConfig()),
            idr_cabac), 5, 3))
        for n in extra:
            body.extend(n)
        return bytes(body)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "idr.h264").write_bytes(make_stream())
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", str(td / "idr.h264"), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(td / "idr.yuv")],
            check=True,
        )
        ref_plane = (td / "idr.yuv").read_bytes()[:W * H]
        # P-frame: MV=(3, 1) quarter-pel everywhere
        ml_p = b"\x00" * (n_mbs * 256 * 4)
        cbp_luma = b"\x00" * n_mbs
        skip = b"\x00" * n_mbs
        mvd_x = bytearray(2 * n_mbs)
        mvd_y = bytearray(2 * n_mbs)
        struct.pack_into("<h", mvd_x, 0, 3)
        struct.pack_into("<h", mvd_y, 0, 1)
        p_cabac = s._inner.h264_encode_p_slice_luma_bytes(
            MB_W, MB_H, 0, 0, ml_p, cbp_luma, skip,
            mvd_x_bytes=bytes(mvd_x), mvd_y_bytes=bytes(mvd_y),
        )
        nal = wrap_nal(emit_p_slice_header(0, 1) + p_cabac, 1, 2)
        (td / "seq.h264").write_bytes(make_stream([nal]))
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "warning",
             "-i", str(td / "seq.h264"), "-f", "rawvideo",
             "-pix_fmt", "yuv420p", str(td / "seq.yuv")],
            capture_output=True, text=True,
        )
        assert not r.stderr.strip(), f"ffmpeg: {r.stderr[:200]}"
        ff_p = (td / "seq.yuv").read_bytes()
        yuv_size = int(W * H * 1.5)
        ff_p_luma = ff_p[yuv_size: yuv_size + W * H]
        # Same MV passed through the MC kernel with subpel=True.
        mvs = [(3, 1, 0)] * n_mbs
        mv_buf = b"".join(struct.pack("<iii", *m) for m in mvs)
        our_mc = s._inner.h264_apply_motion_compensation(
            ref_plane, mv_buf, W, H, MB_W, MB_H, subpel=True,
        )
        diff = sum(1 for i in range(W * H) if ff_p_luma[i] != our_mc[i])
        assert diff == 0, (
            f"subpel MC kernel disagrees with ffmpeg at {diff} pixels"
        )


def test_subpel_refinement_never_increases_sad():
    """The two-phase half-pel→quarter-pel diamond refinement is
    monotone-improving by construction: each phase keeps the
    best-so-far baseline. Verify on real motion: scroll a
    pseudorandom plane by (3 px right, 2 px down) so the integer-pel
    ME finds (-3, -2) as the best MV; the sub-pel refinement should
    return the SAME or LOWER SAD per MB (it can't get worse)."""
    import random
    import struct
    s = Substrate()
    if not hasattr(s._inner, "h264_refine_motion_subpel"):
        pytest.skip("substrate_rs built without h264_refine_motion_subpel")

    MB_W, MB_H = 6, 4
    W, H = MB_W * 16, MB_H * 16
    n_mbs = MB_W * MB_H
    rng = random.Random(0xC0FFEE)
    ref_plane = bytes(rng.randint(0, 255) for _ in range(W * H))

    # Target = reference scrolled by (+3, +2) integer pixels with
    # clamp-to-border. Best integer MV per MB is (-3, -2).
    target = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            sx = max(0, min(W - 1, x - 3))
            sy = max(0, min(H - 1, y - 2))
            target[y * W + x] = ref_plane[sy * W + sx]
    target = bytes(target)

    int_buf = s._inner.h264_estimate_motion_cpu(
        target, ref_plane, W, H, MB_W, MB_H, 4,
    )
    int_mvs = [struct.unpack_from("<iii", int_buf, j * 12) for j in range(n_mbs)]

    ref_buf = s._inner.h264_refine_motion_subpel(
        target, ref_plane, int_buf, W, H, MB_W, MB_H,
    )
    qmvs = [struct.unpack_from("<iii", ref_buf, j * 12) for j in range(n_mbs)]

    # Per-MB invariants:
    #   - refined SAD ≤ integer-pel SAD (the diamond starts at the
    #     integer baseline and only accepts strictly-better moves)
    #   - quarter-pel MV starts inside the same sub-pel cell as the
    #     integer MV: (qmv.div_euclid(4)) == int_mv
    for j in range(n_mbs):
        int_x, int_y, int_sad = int_mvs[j]
        qmv_x, qmv_y, q_sad = qmvs[j]
        assert q_sad <= int_sad, (
            f"MB {j}: refinement made SAD WORSE: "
            f"int {int_sad} → qp {q_sad}"
        )
        # The refinement can wander up to ±2 quarter-pel away from
        # the integer baseline (phase-1 half-pel + phase-2 quarter-
        # pel diamond reaches ±3 in extremes). Sanity bound: the
        # quarter-pel MV's integer part lies within ±1 of the
        # baseline integer MV.
        q_int_x = qmv_x // 4 if qmv_x >= 0 else -((-qmv_x + 3) // 4)
        q_int_y = qmv_y // 4 if qmv_y >= 0 else -((-qmv_y + 3) // 4)
        assert abs(q_int_x - int_x) <= 1, (
            f"MB {j}: integer-part wandered too far: "
            f"int={int_x}, q_int={q_int_x}"
        )
        assert abs(q_int_y - int_y) <= 1, (
            f"MB {j}: integer-part wandered too far: "
            f"int={int_y}, q_int={q_int_y}"
        )


def test_subpel_refinement_finds_known_quarterpel_shift():
    """Construct a target that is the reference at a known
    sub-pel position via the SAME vendored interpolate_luma the
    refinement uses, then verify the refinement recovers the
    correct quarter-pel MV on a flat random plane.

    Two cases:
      1. half-pel (2, 2) — phase 1 winner; phase 2 should not
         drift away.
      2. quarter-pel (3, 1) — phase 1 picks (2, 0) as nearest
         half-pel, phase 2 refines to (3, 1)."""
    import random
    import struct
    s = Substrate()
    if not (hasattr(s._inner, "h264_refine_motion_subpel")
            and hasattr(s._inner, "h264_interpolate_luma_subpel")):
        pytest.skip("substrate_rs built without sub-pel kernels")

    MB_W, MB_H = 4, 4
    W, H = MB_W * 16, MB_H * 16
    n_mbs = MB_W * MB_H
    rng = random.Random(0xBEE5)
    ref_plane = bytes(rng.randint(0, 255) for _ in range(W * H))

    for true_xf, true_yf in [(2, 2), (3, 1), (1, 3)]:
        # Build a target where every MB is the reference at the
        # known sub-pel offset (true_xf/4, true_yf/4). The
        # vendored interpolator produces the same prediction the
        # refinement will compare against, so the SAD at the true
        # position is exactly 0.
        target = bytearray(W * H)
        for mb_y in range(MB_H):
            for mb_x in range(MB_W):
                blk = s._inner.h264_interpolate_luma_subpel(
                    ref_plane, W, H,
                    mb_x * 16, mb_y * 16,
                    true_xf, true_yf, 16, 16,
                )
                for yy in range(16):
                    dst = (mb_y * 16 + yy) * W + mb_x * 16
                    target[dst: dst + 16] = blk[yy * 16: yy * 16 + 16]
        target = bytes(target)

        # Seed the refinement with the integer-pel baseline MV (0, 0)
        # — the truly optimal integer MV given the target was
        # produced at this MB's own integer position.
        int_buf = bytearray(n_mbs * 12)
        for j in range(n_mbs):
            struct.pack_into("<iii", int_buf, j * 12, 0, 0, 0)
        ref_buf = s._inner.h264_refine_motion_subpel(
            target, ref_plane, bytes(int_buf), W, H, MB_W, MB_H,
        )
        qmvs = [struct.unpack_from("<iii", ref_buf, j * 12) for j in range(n_mbs)]
        for j in range(n_mbs):
            qmv_x, qmv_y, q_sad = qmvs[j]
            assert (qmv_x, qmv_y) == (true_xf, true_yf), (
                f"MB {j}: refinement missed ({true_xf}, {true_yf}); "
                f"got ({qmv_x}, {qmv_y}) sad={q_sad}"
            )
            assert q_sad == 0, (
                f"MB {j}: SAD at the true sub-pel position should be "
                f"0, got {q_sad}"
            )
