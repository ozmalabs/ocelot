"""H.264 I_NxN MB walker via the Python binding.

Tests the full I-slice round-trip:
  walker.encode(N MBs of luma coefs) → byte buffer → walker.decode
  ⇒ identical coefs back

The Python binding constructs all neighbour state internally;
caller just provides the slice dimensions and per-MB inputs.
"""
import pytest

from substrate_rs import Substrate


@pytest.fixture
def s() -> Substrate:
    return Substrate()


def test_single_mb_round_trip(s: Substrate) -> None:
    """1 MB, one luma block has coefs."""
    coefs = [0] * 256
    coefs[0] = 100   # DC of block 0
    coefs[1] = -8
    coefs[4] = -6
    buf = s._inner.h264_encode_i_slice_luma_only(
        1, 1, 0, 26, coefs, [0b0001],
    )
    back, cbp = s._inner.h264_decode_i_slice_luma_only(
        1, 1, 0, 26, list(buf),
    )
    assert list(back) == coefs
    assert list(cbp) == [0b0001]


def test_full_8x8_block_round_trip(s: Substrate) -> None:
    """All 4 8×8 luma blocks coded (cbp_luma=0xF)."""
    coefs = [0] * 256
    # Populate each 4×4 with a small DC.
    for block in range(16):
        coefs[block * 16] = 40 + block
    buf = s._inner.h264_encode_i_slice_luma_only(
        1, 1, 0, 26, coefs, [0xF],
    )
    back, cbp = s._inner.h264_decode_i_slice_luma_only(
        1, 1, 0, 26, list(buf),
    )
    assert list(back) == coefs
    assert list(cbp) == [0xF]


def test_4x3_slice_round_trip(s: Substrate) -> None:
    """4×3 = 12 MB slice — neighbour state propagates."""
    mb_width, mb_height = 4, 3
    n_mbs = mb_width * mb_height
    luma = []
    for i in range(n_mbs):
        c = [0] * 256
        c[0] = 60 + i      # unique DC per MB
        c[1] = -3
        luma.extend(c)
    buf = s._inner.h264_encode_i_slice_luma_only(
        mb_width, mb_height, 0, 26, luma, [0b0001] * n_mbs,
    )
    back, cbp = s._inner.h264_decode_i_slice_luma_only(
        mb_width, mb_height, 0, 26, list(buf),
    )
    assert list(back) == luma
    assert list(cbp) == [0b0001] * n_mbs


def test_full_1080p_slice_round_trip(s: Substrate) -> None:
    """Full 1088p-aligned slice: 120×68 = 8160 MBs. Realistic load."""
    mb_width, mb_height = 120, 68
    n_mbs = mb_width * mb_height
    luma = []
    for i in range(n_mbs):
        c = [0] * 256
        c[0] = 70 + (i % 30)
        c[1] = -2 + (i % 4)
        c[4] = 1
        luma.extend(c)
    buf = s._inner.h264_encode_i_slice_luma_only(
        mb_width, mb_height, 0, 26, luma, [0b0001] * n_mbs,
    )
    back, cbp = s._inner.h264_decode_i_slice_luma_only(
        mb_width, mb_height, 0, 26, list(buf),
    )
    assert len(back) == len(luma)
    mismatches = sum(1 for a, b in zip(luma, list(back)) if a != b)
    assert mismatches == 0, f"{mismatches}/{len(luma)} samples"


def test_cbp_input_validation(s: Substrate) -> None:
    """Wrong-length inputs raise."""
    with pytest.raises(Exception):
        s._inner.h264_encode_i_slice_luma_only(
            2, 2, 0, 26, [0] * 100, [0] * 4,  # wrong luma length
        )
    with pytest.raises(Exception):
        s._inner.h264_encode_i_slice_luma_only(
            2, 2, 0, 26, [0] * (4 * 256), [0] * 3,  # wrong cbp length
        )
