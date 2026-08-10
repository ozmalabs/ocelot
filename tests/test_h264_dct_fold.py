"""H.264 4×4 integer DCT + 2:1 DCT-domain spatial fold tests.

Pins down the math of the fold primitive — the linear map from
four 4×4 H.264-DCT coefficient blocks (covering an 8×8 source
region in pixel space) to one 4×4 coefficient block covering
the same region at half spatial resolution. Used as the inner
kernel of compressed-domain H.264 downscale.

The fold lives in `runners/dsl/src/h264_dct.rs` because it's
dense numerical work; the Python wrapper exposes it via
`Substrate.h264_dct_forward_many` / `h264_dct_inverse_many` /
`h264_dct_fold_many`. These tests verify behaviour at the
binding boundary.
"""
import pytest

from substrate_rs import Substrate


@pytest.fixture
def s() -> Substrate:
    return Substrate()


def test_forward_dct_constant_block_dc_only(s: Substrate) -> None:
    """Cf · constant · Cfᵀ produces DC-only output.

    For input X = c·1₄ₓ₄: Cf · X has row-sums [4, 0, 0, 0]·c on
    each column, so only row 0 is nonzero. Then (Cf · X) · Cfᵀ
    has only [0][0] = c · 4 · 4 = 16c, everything else zero.
    """
    samples = [42] * 16
    coefs = list(s._inner.h264_dct_forward_many(samples))
    assert coefs[0] == 672, f"DC coefficient: got {coefs[0]}, expected 16·42 = 672"
    for i in range(1, 16):
        assert coefs[i] == 0, f"AC[{i}] = {coefs[i]}, expected 0"


def test_forward_inverse_round_trip(s: Substrate) -> None:
    """forward(X) -> inverse() recovers X within 1 unit (rounding)."""
    samples = [50] * 16
    coefs = list(s._inner.h264_dct_forward_many(samples))
    recovered = list(s._inner.h264_dct_inverse_many(coefs))
    for i, (orig, got) in enumerate(zip(samples, recovered)):
        assert abs(orig - got) <= 1, (
            f"round-trip [{i}]: {orig} -> coef -> {got}"
        )


def test_forward_inverse_round_trip_ramp(s: Substrate) -> None:
    """Non-constant input: 0..15 ramp."""
    samples = list(range(16))
    coefs = list(s._inner.h264_dct_forward_many(samples))
    recovered = list(s._inner.h264_dct_inverse_many(coefs))
    for i, (orig, got) in enumerate(zip(samples, recovered)):
        assert abs(orig - got) <= 1, f"ramp[{i}]: {orig} vs {got}"


def test_fold_constant_blocks_yields_constant(s: Substrate) -> None:
    """Four identical constant blocks fold to the same constant.

    Area-average of constant signal is the constant. The fold
    should reproduce that through the DCT round-trip.
    """
    block_coefs = list(s._inner.h264_dct_forward_many([80] * 16))
    # Four identical input blocks.
    folded = list(s._inner.h264_dct_fold_many(block_coefs * 4))
    pixels = list(s._inner.h264_dct_inverse_many(folded))
    for i, p in enumerate(pixels):
        assert abs(p - 80) <= 1, f"folded pixel[{i}] = {p}, expected ~80"


def test_fold_input_shape_validation(s: Substrate) -> None:
    """h264_dct_fold_many requires multiple-of-64 input length."""
    with pytest.raises(Exception):  # PyValueError surfaces as ValueError
        s._inner.h264_dct_fold_many([0] * 63)
    with pytest.raises(Exception):
        s._inner.h264_dct_fold_many([0] * 100)


def test_fold_batch_processes_multiple_outputs(s: Substrate) -> None:
    """64*N input -> 16*N output. Verifies the per-block batching."""
    # Build 3 different sets of 4 input blocks.
    bs = []
    for c in (40, 80, 120):
        coefs = list(s._inner.h264_dct_forward_many([c] * 16))
        bs.extend(coefs * 4)  # 4 identical blocks per group
    folded = list(s._inner.h264_dct_fold_many(bs))
    assert len(folded) == 16 * 3, (
        f"output length {len(folded)} != 48"
    )
    # Decode each output block, check it matches its source constant.
    for i, expected in enumerate((40, 80, 120)):
        block_coefs = folded[i * 16:(i + 1) * 16]
        pixels = list(s._inner.h264_dct_inverse_many(block_coefs))
        for p in pixels:
            assert abs(p - expected) <= 1, (
                f"batch[{i}] pixel: got {p}, expected ~{expected}"
            )


def test_fold_preserves_horizontal_ramp(s: Substrate) -> None:
    """Tiled horizontal ramp 0..7 in pixel domain folds to
    [~0, ~3, ~5, ~7] per row (area-average of pairs)."""
    # Top-left block: columns 0..3, value = column.
    p_left = [c for r in range(4) for c in range(4)]
    # Top-right block: columns 4..7.
    p_right = [c + 4 for r in range(4) for c in range(4)]
    c_left = list(s._inner.h264_dct_forward_many(p_left))
    c_right = list(s._inner.h264_dct_forward_many(p_right))
    # Stack top-left, top-right, bottom-left, bottom-right.
    inp = c_left + c_right + c_left + c_right
    folded = list(s._inner.h264_dct_fold_many(inp))
    pixels = list(s._inner.h264_dct_inverse_many(folded))
    # Each row should be approximately [0 or 1, 2 or 3, 4 or 5, 6 or 7].
    expected_cols = (0, 3, 5, 7)
    for r in range(4):
        for c in range(4):
            got = pixels[r * 4 + c]
            exp = expected_cols[c]
            assert abs(got - exp) <= 1, (
                f"ramp ({r},{c}): got {got}, expected ~{exp}"
            )
