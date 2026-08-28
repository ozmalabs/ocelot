//! H.264 4×4 integer DCT + DCT-domain 2:1 spatial fold.
//!
//! The 4×4 integer transform per H.264 §8.5.8 (Malvar, Sullivan,
//! Srinivasan):
//!
//!   Cf = [[ 1,  1,  1,  1],
//!         [ 2,  1, -1, -2],
//!         [ 1, -1, -1,  1],
//!         [ 1, -2,  2, -1]]
//!
//!   Y = Cf · X · Cfᵀ        (forward)
//!
//! Cf and its companion Ci do NOT form a clean integer inverse;
//! the spec folds residual scaling into the per-coefficient
//! quantisation matrix Mi. To do exact arithmetic on raw
//! (unquantised) coefficients we treat Cf as an ordinary linear
//! operator and use its numerical inverse for the back-transform.
//! Float64 throughout the algebra; round to i32 at the boundary.
//!
//! The 4-to-1 fold:
//!
//!   Input:  four 4×4 coefficient blocks arranged as
//!             [TL][TR]
//!             [BL][BR]
//!           covering an 8×8 source region in pixel space.
//!
//!   Output: one 4×4 coefficient block covering the same region
//!           at half spatial resolution (area-average filter).
//!
//! Reference path: IDCT each input → tile to 8×8 → area-average
//! to 4×4 → DCT. Three transform passes + scratch.
//!
//! Fast path: precomputed 16×64 linear map from `[tl,tr,bl,br]`
//! coefficient concatenation to output coefficients. Since both
//! the DCT and the area-average filter are linear, their
//! composition is a single matrix M. Built once at first call via
//! `OnceLock`; subsequent folds are one matvec.

use std::sync::OnceLock;

// --- H.264 4×4 quantisation (§8.5.10) ------------------------------
//
// Forward quantiser: Z = (|Y| * MF + f) >> qbits, sign(Z) = sign(Y).
// Inverse dequantiser: W' = Z * V << (QP/6).
//
// MF and V are 6-tables indexed by QP%6. Within each table, the
// 16 positions group into three classes by (i%2, j%2):
//   class 0 (DC-positions, both even): high value
//   class 1 (AC-odd-odd, both odd):    low value
//   class 2 (mixed):                   middle value
//
// At QP=0 (qbits=15, f = 32768/3 ≈ 10923 for intra), the forward+
// inverse round-trip is nearly lossless — the small MF/V scaling
// inverts the 16× expansion of the forward Cf transform and the
// 1/64 collapse of the inverse Ci transform.

/// MF[QP%6] flat 4×4 matrix per H.264 spec.
const MF_TABLE: [[i32; 16]; 6] = [
    [
        13107, 8066, 13107, 8066, 8066, 5243, 8066, 5243, 13107, 8066, 13107, 8066, 8066, 5243,
        8066, 5243,
    ],
    [
        11916, 7490, 11916, 7490, 7490, 4660, 7490, 4660, 11916, 7490, 11916, 7490, 7490, 4660,
        7490, 4660,
    ],
    [
        10082, 6554, 10082, 6554, 6554, 4194, 6554, 4194, 10082, 6554, 10082, 6554, 6554, 4194,
        6554, 4194,
    ],
    [
        9362, 5825, 9362, 5825, 5825, 3647, 5825, 3647, 9362, 5825, 9362, 5825, 5825, 3647, 5825,
        3647,
    ],
    [
        8192, 5243, 8192, 5243, 5243, 3355, 5243, 3355, 8192, 5243, 8192, 5243, 5243, 3355, 5243,
        3355,
    ],
    [
        7282, 4559, 7282, 4559, 4559, 2893, 4559, 2893, 7282, 4559, 7282, 4559, 4559, 2893, 4559,
        2893,
    ],
];

/// Forward-quantise a 4×4 luma intra residual block at the given QP.
/// Returns Z (one signed value per position) per ITU-T H.264 §8.5.10
/// with rounding offset f = (1<<qbits)/3 (intra).
///
/// At QP=0 this is approximately Z = Y/2.5; the H.264 dequantiser
/// in any conformant decoder will invert it.
pub fn quantize_intra_4x4(y: &[i32; 16], qp: i32) -> [i32; 16] {
    let qp_mod = (qp.rem_euclid(6)) as usize;
    let qp_div = (qp / 6) as u32;
    let qbits = 15 + qp_div;
    let f = (1i32 << qbits) / 3;
    let mf = &MF_TABLE[qp_mod];
    let mut z = [0i32; 16];
    for k in 0..16 {
        let abs_y = y[k].unsigned_abs() as i64;
        let mag = ((abs_y * mf[k] as i64 + f as i64) >> qbits) as i32;
        z[k] = if y[k] < 0 { -mag } else { mag };
    }
    z
}

/// Inverse dequantisation: W' = Z * V << (QP/6). Used to verify the
/// round-trip without leaving the substrate.
const V_TABLE: [[i32; 16]; 6] = [
    [
        10, 13, 10, 13, 13, 16, 13, 16, 10, 13, 10, 13, 13, 16, 13, 16,
    ],
    [
        11, 14, 11, 14, 14, 18, 14, 18, 11, 14, 11, 14, 14, 18, 14, 18,
    ],
    [
        13, 16, 13, 16, 16, 20, 16, 20, 13, 16, 13, 16, 16, 20, 16, 20,
    ],
    [
        14, 18, 14, 18, 18, 23, 18, 23, 14, 18, 14, 18, 18, 23, 18, 23,
    ],
    [
        16, 20, 16, 20, 20, 25, 20, 25, 16, 20, 16, 20, 20, 25, 20, 25,
    ],
    [
        18, 23, 18, 23, 23, 29, 23, 29, 18, 23, 18, 23, 23, 29, 23, 29,
    ],
];

/// H.264 spec inverse 4×4 transform + add to predictor + clip,
/// matching libavcodec's `ff_h264_idct_add` per ITU-T §8.5.12.
///
/// Input:
///   - `block`: dequantised coefficients (W' per spec).
///   - `pred`:  4×4 predictor pixels (in 0..255).
/// Returns the reconstructed pixel block (0..255).
///
/// Implements the exact integer butterfly form, including the
/// +32 added to DC before the column inverse, the >>1 on rows 1/3
/// (the "half-coefficient" approximation), and the final
/// (z + 0) >> 6 with clip per pixel.
///
/// Replaces the pure-math `inverse_4x4` for the decoder/encoder-
/// reconstruction path: this is the path that needs to be
/// bit-identical to libavcodec for our encoder-reconstructed
/// pixels to match what ffmpeg produces.
/// Spec-§8.5.14 variant of `idct_add_4x4_h264` that takes the
/// prediction as `&[i32; 16]` (unclipped) instead of `&[u8; 16]`.
/// Clips once at the end: `clip1Y(pred[k] + r[k])`. Required for
/// sub-pel motion compensation — the 6-tap FIR (§8.4.2.2.1) can
/// produce values outside `[0, 255]` for some `(x_frac, y_frac)`
/// combinations, and the spec demands those overshoots survive
/// until they're combined with the IDCT residual.
pub fn idct_add_4x4_h264_i32pred(block: &[i32; 16], pred: &[i32; 16]) -> [u8; 16] {
    // H.264 §8.5.12.2 inverse 4x4 transform, matching libavcodec
    // `ff_h264_idct_add` EXACTLY: the first 1-D butterfly pass runs
    // over the four COLUMNS (fixed column index i, varying row via the
    // 4*j stride), then the second pass runs over the four ROWS, with
    // the +32 rounding and >>6 applied in the row pass. The previous
    // code did the passes in the opposite (row-first) order; because
    // the `>>1` half-step is an arithmetic shift (rounds toward -inf,
    // i.e. lossy for odd negatives), the two orderings differ by +-1
    // exactly when an intermediate is odd & negative — which never
    // happened on the smooth synthetic gradients but DID on real
    // textured I_NxN content, producing the +-1..8 pixel errors that
    // compounded through intra prediction. Column-first is the spec /
    // reference order and is bit-exact.
    let mut b = [0i32; 16];
    b.copy_from_slice(block);
    // Stage 1: column inverse (fixed column i, butterfly over rows).
    for i in 0..4 {
        let a = b[i + 4 * 0];
        let c = b[i + 4 * 2];
        let bb = b[i + 4 * 1];
        let d = b[i + 4 * 3];
        let z0 = a + c;
        let z1 = a - c;
        let z2 = (bb >> 1) - d;
        let z3 = bb + (d >> 1);
        b[i + 4 * 0] = z0 + z3;
        b[i + 4 * 1] = z1 + z2;
        b[i + 4 * 2] = z1 - z2;
        b[i + 4 * 3] = z0 - z3;
    }
    // Stage 2: row inverse + final +32, >>6, add pred, clip.
    let mut out = [0u8; 16];
    for i in 0..4 {
        let a = b[4 * i + 0];
        let c = b[4 * i + 2];
        let bb = b[4 * i + 1];
        let d = b[4 * i + 3];
        let z0 = a + c;
        let z1 = a - c;
        let z2 = (bb >> 1) - d;
        let z3 = bb + (d >> 1);
        let r0 = (z0 + z3 + 32) >> 6;
        let r1 = (z1 + z2 + 32) >> 6;
        let r2 = (z1 - z2 + 32) >> 6;
        let r3 = (z0 - z3 + 32) >> 6;
        out[4 * i + 0] = (pred[4 * i + 0] + r0).max(0).min(255) as u8;
        out[4 * i + 1] = (pred[4 * i + 1] + r1).max(0).min(255) as u8;
        out[4 * i + 2] = (pred[4 * i + 2] + r2).max(0).min(255) as u8;
        out[4 * i + 3] = (pred[4 * i + 3] + r3).max(0).min(255) as u8;
    }
    out
}

pub fn idct_add_4x4_h264(block: &[i32; 16], pred: &[u8; 16]) -> [u8; 16] {
    let mut p32 = [0i32; 16];
    for k in 0..16 {
        p32[k] = pred[k] as i32;
    }
    idct_add_4x4_h264_i32pred(block, &p32)
}

/// Single-pass forward-DCT-and-fold for a luma plane: take a u8
/// pixel plane (in_w × in_h) and produce the 2:1-folded H.264 DCT
/// coefficients ready for the next stage. No per-block FFI cost,
/// no intermediate vector allocations per block.
///
/// Output layout: `(in_w/8) * (in_h/8)` output 4×4 blocks in
/// raster order, 16 coefs each. Total length =
/// `(in_w/8) * (in_h/8) * 16` i32s.
///
/// Equivalent to the Python pipeline:
///   forward_dct(every 4×4 block) → fold each 2×2 group via matrix
/// but done entirely on the Rust side.
pub fn fold_luma_plane_to_coefs(plane: &[u8], in_w: usize, in_h: usize) -> Vec<i32> {
    assert_eq!(plane.len(), in_w * in_h);
    assert_eq!(in_w & 7, 0, "in_w must be a multiple of 8");
    assert_eq!(in_h & 7, 0, "in_h must be a multiple of 8");

    let out_bx_count = in_w / 8;
    let out_by_count = in_h / 8;
    let mut out = vec![0i32; out_bx_count * out_by_count * 16];

    for out_by in 0..out_by_count {
        for out_bx in 0..out_bx_count {
            // Forward-DCT the four source 4×4 blocks that feed this
            // output block. The 4 blocks are TL/TR/BL/BR within an
            // 8×8 source region.
            let mut tl = [0i32; 16];
            let mut tr = [0i32; 16];
            let mut bl = [0i32; 16];
            let mut br = [0i32; 16];

            for (target, src_by_off, src_bx_off) in [
                (&mut tl, 0, 0),
                (&mut tr, 0, 1),
                (&mut bl, 1, 0),
                (&mut br, 1, 1),
            ] {
                let src_by = out_by * 2 + src_by_off;
                let src_bx = out_bx * 2 + src_bx_off;
                let mut samples = [0i32; 16];
                for ry in 0..4 {
                    let row_off = (src_by * 4 + ry) * in_w + src_bx * 4;
                    samples[ry * 4 + 0] = plane[row_off + 0] as i32;
                    samples[ry * 4 + 1] = plane[row_off + 1] as i32;
                    samples[ry * 4 + 2] = plane[row_off + 2] as i32;
                    samples[ry * 4 + 3] = plane[row_off + 3] as i32;
                }
                let coefs = forward_4x4(&samples);
                target.copy_from_slice(&coefs);
            }

            // Fold the 4 source blocks → 1 output block.
            let folded = fold_4to1_via_matrix(&tl, &tr, &bl, &br);
            let out_off = (out_by * out_bx_count + out_bx) * 16;
            out[out_off..out_off + 16].copy_from_slice(&folded);
        }
    }
    out
}

/// Inverse-DCT a flat coefficient array (raster of 4×4 blocks)
/// back into a u8 pixel plane. Used after a fold to materialise
/// the downscaled target pixels for downstream intra-prediction.
/// Each coefficient block is independently IDCT'd via our pure-
/// math inverse and clamped to 0..=255.
///
/// Output dimensions: `out_w = blocks_x * 4`, `out_h = blocks_y * 4`.
pub fn coefs_to_luma_plane(coefs: &[i32], blocks_x: usize, blocks_y: usize) -> Vec<u8> {
    assert_eq!(coefs.len(), blocks_x * blocks_y * 16);
    let out_w = blocks_x * 4;
    let out_h = blocks_y * 4;
    let mut plane = vec![0u8; out_w * out_h];
    for by in 0..blocks_y {
        for bx in 0..blocks_x {
            let blk_base = (by * blocks_x + bx) * 16;
            let mut y = [0i32; 16];
            y.copy_from_slice(&coefs[blk_base..blk_base + 16]);
            let x = inverse_4x4(&y);
            for ry in 0..4 {
                let row_off = (by * 4 + ry) * out_w + bx * 4;
                for rx in 0..4 {
                    let v = x[ry * 4 + rx];
                    plane[row_off + rx] = v.max(0).min(255) as u8;
                }
            }
        }
    }
    plane
}

/// Combined 4K-pixels → mb_luma pipeline in a single Rust pass.
///
/// Mathematical short-circuit: the original Python pipeline did
///   forward-DCT → DCT-domain 2:1 fold (via 16×64 linear map) →
///   inverse-DCT → target pixels.
/// But the fold WAS CONSTRUCTED as
///   inverse-DCT → tile to 8×8 → area-average → forward-DCT
/// so the whole chain is just an 8×8 → 4×4 area-average filter:
///   forward · inverse · tile · area-avg · DCT · IDCT
///   = tile · area-avg            (the DCT pair cancels by linearity)
/// We replace the entire forward-fold-inverse sequence with direct
/// 8×8 pixel averaging — algebraically identical, ~100× faster.
///
/// Inputs:
///   - `plane`: 4K luma plane (in_w × in_h).
///   - `in_w`, `in_h`: 4K dimensions.
///   - `mb_w`, `mb_h`: 1080p MB grid. Must satisfy
///     `mb_w * 32 == in_w` and `mb_h * 32 == in_h` (2:1 downscale).
///   - `qp`: slice QP.
///
/// Returns: `mb_w * mb_h * 256` quantised coefficients ready for
/// the CABAC walker.
/// 2:1 area average from 4K → 1080p luma. Tries AVX2 if the
/// target has it, falls back to scalar. The AVX2 path processes
/// 32 output bytes per iteration via two `_mm256_avg_epu8`s; on
/// our 12-core test box this is ~5× faster than the scalar version.
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn area_average_2to1_avx2(
    plane: &[u8],
    in_w: usize,
    out_w: usize,
    out_h: usize,
    target: &mut [u8],
) {
    use core::arch::x86_64::*;
    // We process 32 output bytes at a time. Need 64 input bytes per
    // row, two rows. The horizontal averaging uses _mm256_avg_epu8
    // on two 32-byte halves derived from the 64-byte source.
    // NB: avg_epu8 computes (a + b + 1) >> 1 per byte — nested
    // application gives a result that may differ from the true
    // 4-pixel average by ±1 LSB, well within visual noise.
    assert!(out_w % 32 == 0, "AVX2 path expects out_w % 32 == 0");
    for oy in 0..out_h {
        let row0 = &plane[(2 * oy) * in_w..(2 * oy + 1) * in_w];
        let row1 = &plane[(2 * oy + 1) * in_w..(2 * oy + 2) * in_w];
        let dst = &mut target[oy * out_w..(oy + 1) * out_w];
        let n_chunks = out_w / 32;
        for k in 0..n_chunks {
            // Source: 64 bytes from each row, starting at 64k.
            let src_off = k * 64;
            let r0_a = _mm256_loadu_si256(row0.as_ptr().add(src_off) as *const __m256i);
            let r0_b = _mm256_loadu_si256(row0.as_ptr().add(src_off + 32) as *const __m256i);
            let r1_a = _mm256_loadu_si256(row1.as_ptr().add(src_off) as *const __m256i);
            let r1_b = _mm256_loadu_si256(row1.as_ptr().add(src_off + 32) as *const __m256i);
            // Vertical average per byte: (r0 + r1 + 1) >> 1
            let v_a = _mm256_avg_epu8(r0_a, r1_a); // bytes 0..31 vertically averaged
            let v_b = _mm256_avg_epu8(r0_b, r1_b); // bytes 32..63 vertically averaged
                                                   // Horizontal pair average: combine adjacent bytes.
                                                   // Use unpacklo/unpackhi to interleave then shuffle, or
                                                   // a simpler trick: pack to u16 with maddubs (multiply
                                                   // each byte by 1 + sum adjacent pairs in 16 bits).
            let ones = _mm256_set1_epi8(1);
            // maddubs_epi16(a, b) = sum of adjacent (a[2k]*b[2k] +
            // a[2k+1]*b[2k+1]) packed into 16-bit lanes. With b=1,
            // this is a[2k] + a[2k+1] — exactly the horizontal sum.
            let h_a = _mm256_maddubs_epi16(v_a, ones);
            let h_b = _mm256_maddubs_epi16(v_b, ones);
            // Now h_a / h_b each contain 16 × u16 with the
            // horizontal pair sums. We want to divide by 2 with
            // round-half-up (+1 then >>1).
            let one16 = _mm256_set1_epi16(1);
            let h_a = _mm256_srli_epi16(_mm256_add_epi16(h_a, one16), 1);
            let h_b = _mm256_srli_epi16(_mm256_add_epi16(h_b, one16), 1);
            // Pack back to 32 × u8 with saturation.
            let packed = _mm256_packus_epi16(h_a, h_b);
            // Unfortunately _mm256_packus_epi16 packs PER 128-BIT
            // LANE — so the layout is [a_lo, b_lo, a_hi, b_hi]
            // instead of [a_lo, a_hi, b_lo, b_hi]. Permute to fix.
            let permuted = _mm256_permute4x64_epi64::<0b1101_1000>(packed);
            _mm256_storeu_si256(dst.as_mut_ptr().add(k * 32) as *mut __m256i, permuted);
        }
    }
}

/// Scalar fallback for the area-average path.
fn area_average_2to1_scalar(
    plane: &[u8],
    in_w: usize,
    out_w: usize,
    out_h: usize,
    target: &mut [u8],
) {
    for oy in 0..out_h {
        let row0_off = (2 * oy) * in_w;
        let row1_off = (2 * oy + 1) * in_w;
        let dst_off = oy * out_w;
        for ox in 0..out_w {
            let sx = ox * 2;
            let s = plane[row0_off + sx] as u32
                + plane[row0_off + sx + 1] as u32
                + plane[row1_off + sx] as u32
                + plane[row1_off + sx + 1] as u32;
            target[dst_off + ox] = ((s + 2) >> 2) as u8;
        }
    }
}

/// Public wrapper for the diagnostic binding.
pub fn area_average_2to1_pub(
    plane: &[u8],
    in_w: usize,
    out_w: usize,
    out_h: usize,
    target: &mut [u8],
) {
    area_average_2to1(plane, in_w, out_w, out_h, target);
}

/// Dispatch: AVX2 when available + sizes line up, else scalar.
fn area_average_2to1(plane: &[u8], in_w: usize, out_w: usize, out_h: usize, target: &mut [u8]) {
    #[cfg(target_arch = "x86_64")]
    {
        if out_w % 32 == 0 && is_x86_feature_detected!("avx2") {
            unsafe {
                area_average_2to1_avx2(plane, in_w, out_w, out_h, target);
            }
            return;
        }
    }
    area_average_2to1_scalar(plane, in_w, out_w, out_h, target);
}

/// One output level in a multi-resolution pyramid.
#[derive(Clone, Debug)]
pub struct PyramidLevel {
    pub out_w: usize,
    pub out_h: usize,
    pub mb_w: usize,
    pub mb_h: usize,
    pub mb_luma: Vec<i32>,
}

/// Same shape as `PyramidLevel` but carries the fully-CABAC-encoded
/// payload — used by the parallel transcoder that does both
/// stages inside one Rust call.
#[derive(Clone, Debug)]
pub struct PyramidStream {
    pub out_w: usize,
    pub out_h: usize,
    pub mb_w: usize,
    pub mb_h: usize,
    pub cabac_payload: Vec<u8>,
}

/// A single slice within a multi-slice level.
#[derive(Clone, Debug)]
pub struct PyramidSlice {
    pub first_mb_in_slice: usize,
    pub cabac_payload: Vec<u8>,
}

/// A pyramid level that's been multi-sliced for parallel encoding.
#[derive(Clone, Debug)]
pub struct PyramidLevelMultiSlice {
    pub out_w: usize,
    pub out_h: usize,
    pub mb_w: usize,
    pub mb_h: usize,
    pub slices: Vec<PyramidSlice>,
}

/// Multi-resolution + multi-slice ABR ladder in one Rust call.
/// `slices_per_level` controls how many slices each level is split
/// into for parallel CABAC encoding (more slices = more parallelism
/// but slightly larger payload from re-init of contexts and
/// boundary intra-pred falling back to DC).
///
/// Total parallel work = sum over levels of (slices_per_level[i])
/// threads. With std::thread::scope these all run concurrently
/// up to the CPU's core count.
pub fn transcode_pyramid_multislice(
    plane: &[u8],
    in_w: usize,
    in_h: usize,
    qp: i32,
    n_levels: usize,
    slices_per_level: &[usize],
) -> Vec<PyramidLevelMultiSlice> {
    assert_eq!(plane.len(), in_w * in_h);
    assert_eq!(slices_per_level.len(), n_levels);

    // Phase 1: build the area-average pyramid (sequential; cheap).
    let mut levels_pixels: Vec<(usize, usize, Vec<u8>, usize)> = Vec::with_capacity(n_levels);
    let mut cur_w = in_w;
    let mut cur_h = in_h;
    let mut cur: Vec<u8> = plane.to_vec();
    for i in 0..n_levels {
        let out_w = cur_w / 2;
        let out_h = cur_h / 2;
        let mut target = vec![0u8; out_w * out_h];
        area_average_2to1(&cur, cur_w, out_w, out_h, &mut target);
        levels_pixels.push((out_w, out_h, target.clone(), slices_per_level[i]));
        cur = target;
        cur_w = out_w;
        cur_h = out_h;
    }

    // Phase 2: encode each (level, slice) in parallel.
    // First: assemble per-slice work items, each tagged with its
    // level + slice index so we can re-bucket on collection.
    struct Job {
        level_idx: usize,
        slice_idx: usize,
        first_mb_row: usize,
        last_mb_row: usize, // exclusive
        first_mb_in_slice: usize,
        target: std::sync::Arc<Vec<u8>>,
        out_w: usize,
        out_h: usize,
        mb_w: usize,
    }
    let mut jobs: Vec<Job> = Vec::new();
    let mut per_level_meta: Vec<(usize, usize, usize, usize)> = Vec::new();
    for (level_idx, (out_w, out_h, target, n_slices)) in levels_pixels.into_iter().enumerate() {
        let mb_w = out_w / 16;
        let mb_h = out_h / 16;
        per_level_meta.push((out_w, out_h, mb_w, mb_h));
        let target_arc = std::sync::Arc::new(target);
        // Divide mb_h rows roughly evenly across n_slices.
        let rows_per_slice = (mb_h + n_slices - 1) / n_slices;
        let mut row = 0;
        let mut slice_idx = 0;
        while row < mb_h {
            let last = (row + rows_per_slice).min(mb_h);
            jobs.push(Job {
                level_idx,
                slice_idx,
                first_mb_row: row,
                last_mb_row: last,
                first_mb_in_slice: row * mb_w,
                target: target_arc.clone(),
                out_w,
                out_h,
                mb_w,
            });
            slice_idx += 1;
            row = last;
        }
    }

    // Run all jobs in parallel.
    let results: Vec<(usize, usize, PyramidSlice)> = std::thread::scope(|s| {
        let handles: Vec<_> = jobs
            .into_iter()
            .map(|job| {
                s.spawn(move || {
                    let mb_luma = intra_predict_and_quantise_slice_range(
                        &job.target,
                        job.out_w,
                        job.out_h,
                        job.mb_w,
                        job.first_mb_row,
                        job.last_mb_row,
                        qp,
                    );
                    let n_mbs = (job.last_mb_row - job.first_mb_row) * job.mb_w;
                    let cbp = vec![0xF_u8; n_mbs];
                    let cabac_payload = crate::cabac::encode_i_slice_from_mb_luma(
                        &mb_luma,
                        &cbp,
                        job.mb_w,
                        job.last_mb_row - job.first_mb_row,
                        0,
                        qp,
                    );
                    (
                        job.level_idx,
                        job.slice_idx,
                        PyramidSlice {
                            first_mb_in_slice: job.first_mb_in_slice,
                            cabac_payload,
                        },
                    )
                })
            })
            .collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    });

    // Re-bucket per level + sort by slice index.
    let mut out: Vec<PyramidLevelMultiSlice> = per_level_meta
        .iter()
        .map(|&(out_w, out_h, mb_w, mb_h)| PyramidLevelMultiSlice {
            out_w,
            out_h,
            mb_w,
            mb_h,
            slices: Vec::new(),
        })
        .collect();
    // Group results: per-level vector of (slice_idx, slice)
    let mut buckets: Vec<Vec<(usize, PyramidSlice)>> =
        per_level_meta.iter().map(|_| Vec::new()).collect();
    for (level_idx, slice_idx, slice) in results {
        buckets[level_idx].push((slice_idx, slice));
    }
    for (level_idx, mut bucket) in buckets.into_iter().enumerate() {
        bucket.sort_by_key(|(idx, _)| *idx);
        out[level_idx].slices = bucket.into_iter().map(|(_, s)| s).collect();
    }
    out
}

/// Multi-resolution ABR ladder in a single pass — full version.
/// Builds the area-average pyramid sequentially (cheap), then
/// encodes each level's intra-pred + quant + CABAC IN PARALLEL
/// via `std::thread::scope`. The level-1 encoder is the dominant
/// cost; running everything in parallel collapses the total to
/// max(per-level cost) instead of sum.
pub fn transcode_pyramid_full(
    plane: &[u8],
    in_w: usize,
    in_h: usize,
    qp: i32,
    n_levels: usize,
) -> Vec<PyramidStream> {
    assert_eq!(plane.len(), in_w * in_h);

    // Phase 1: build the area-average pyramid (sequential; cheap).
    let mut levels_pixels: Vec<(usize, usize, Vec<u8>)> = Vec::with_capacity(n_levels);
    let mut cur_w = in_w;
    let mut cur_h = in_h;
    let mut cur: Vec<u8> = plane.to_vec();
    for _ in 0..n_levels {
        let out_w = cur_w / 2;
        let out_h = cur_h / 2;
        assert_eq!(
            out_w & 15,
            0,
            "level output width {} not a multiple of 16",
            out_w
        );
        assert_eq!(
            out_h & 15,
            0,
            "level output height {} not a multiple of 16",
            out_h
        );
        let mut target = vec![0u8; out_w * out_h];
        area_average_2to1(&cur, cur_w, out_w, out_h, &mut target);
        levels_pixels.push((out_w, out_h, target.clone()));
        cur = target;
        cur_w = out_w;
        cur_h = out_h;
    }

    // Phase 2: encode each level in parallel.
    let outputs: Vec<PyramidStream> = std::thread::scope(|s| {
        let handles: Vec<_> = levels_pixels
            .into_iter()
            .map(|(out_w, out_h, target)| {
                s.spawn(move || {
                    let mb_w = out_w / 16;
                    let mb_h = out_h / 16;
                    let n_mbs = mb_w * mb_h;
                    let mb_luma =
                        intra_predict_and_quantise_slice(&target, out_w, out_h, mb_w, mb_h, qp);
                    let cbp = vec![0xF_u8; n_mbs];
                    let cabac_payload = crate::cabac::encode_i_slice_from_mb_luma(
                        &mb_luma, &cbp, mb_w, mb_h, 0, qp,
                    );
                    PyramidStream {
                        out_w,
                        out_h,
                        mb_w,
                        mb_h,
                        cabac_payload,
                    }
                })
            })
            .collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    });
    outputs
}

/// Multi-resolution pyramid transcode in a single pass.
///
/// Builds the standard 2:1 downscale ladder from a 4K input:
///   level 0: in_w/2  × in_h/2   (1080p from 4K)
///   level 1: in_w/4  × in_h/4   (540p)
///   level 2: in_w/8  × in_h/8   (270p)
///   ...
/// Returns `n_levels` output PyramidLevels, each with its own
/// mb_luma vector ready for the CABAC walker.
///
/// Magical aspect: the downscale pyramid is essentially free
/// because each level area-averages its own input, and the
/// encoder cost over the geometric series converges to ~1.33×
/// the cost of encoding the top level alone. So an N-rung ABR
/// ladder costs barely more than one transcode.
///
/// Caller is responsible for ensuring `mb_w * 16` and `mb_h * 16`
/// at each level evenly divide the corresponding output
/// dimensions; in practice this means picking n_levels such that
/// the smallest level's dimensions are still MB-aligned.
pub fn transcode_pyramid_2to1(
    plane: &[u8],
    in_w: usize,
    in_h: usize,
    qp: i32,
    n_levels: usize,
) -> Vec<PyramidLevel> {
    assert_eq!(plane.len(), in_w * in_h);
    let mut levels: Vec<PyramidLevel> = Vec::with_capacity(n_levels);

    // Current "source" for the next downscale step. Owns its bytes
    // after the first iteration.
    let mut cur_w = in_w;
    let mut cur_h = in_h;
    let mut cur: Vec<u8> = plane.to_vec();

    for _ in 0..n_levels {
        let out_w = cur_w / 2;
        let out_h = cur_h / 2;
        assert_eq!(
            out_w & 15,
            0,
            "level output width {} not a multiple of 16",
            out_w
        );
        assert_eq!(
            out_h & 15,
            0,
            "level output height {} not a multiple of 16",
            out_h
        );
        // Downscale this level's input by 2:1 area-average.
        let mut target = vec![0u8; out_w * out_h];
        area_average_2to1(&cur, cur_w, out_w, out_h, &mut target);

        // Encode this level.
        let mb_w = out_w / 16;
        let mb_h = out_h / 16;
        let mb_luma = intra_predict_and_quantise_slice(&target, out_w, out_h, mb_w, mb_h, qp);
        levels.push(PyramidLevel {
            out_w,
            out_h,
            mb_w,
            mb_h,
            mb_luma,
        });

        // Next iteration uses THIS level's pixels as input — that's
        // why the pyramid is cheap: each level's downscale operates
        // on a 4× smaller plane than the previous.
        cur = target;
        cur_w = out_w;
        cur_h = out_h;
    }
    levels
}

pub fn transcode_2to1_luma_plane(
    plane: &[u8],
    in_w: usize,
    in_h: usize,
    mb_w: usize,
    mb_h: usize,
    qp: i32,
) -> Vec<i32> {
    assert_eq!(plane.len(), in_w * in_h);
    let out_w = mb_w * 16;
    let out_h = mb_h * 16;
    assert_eq!(in_w, out_w * 2);
    assert_eq!(in_h, out_h * 2);

    // Step 2+3 collapsed: direct 2:1 area-average from 4K plane
    // straight to the target 1080p plane. The DCT-fold-IDCT chain
    // in the original pipeline reduces algebraically to this.
    let mut target = vec![0u8; out_w * out_h];
    area_average_2to1(plane, in_w, out_w, out_h, &mut target);

    // Step 4: intra-predict + quant on the target plane.
    intra_predict_and_quantise_slice(&target, out_w, out_h, mb_w, mb_h, qp)
}

// --- I-slice intra prediction + transform + quant pipeline --------
//
// Combines the steps that were in the Python pipeline cascade:
//   1. Spec-correct Intra_4x4_DC predictor from already-coded
//      neighbour samples (per §8.3.1.2.1)
//   2. Residual = target - pred
//   3. Forward 4×4 H.264 integer DCT
//   4. Quantise per §8.5.10 (intra-mode f = 2^qbits / 3)
//   5. Save quantised coefs to caller's mb_luma buffer
//   6. Dequantise + spec IDCT-add to track our reconstruction —
//      this is what the decoder uses as future neighbour samples,
//      so it MUST be bit-identical to libavcodec.
//
// Sub-block scan order per H.264 Table 6-2:
//   8×8 block 0 → 4×4 blocks 0,1,2,3
//   8×8 block 1 → 4×4 blocks 4,5,6,7
//   8×8 block 2 → 4×4 blocks 8,9,10,11
//   8×8 block 3 → 4×4 blocks 12,13,14,15
//
// 4×4 block index → (row, col) in MB per Figure 6-12:
//   (Z-scan in MB grid)

/// 4×4 block index → (row, col) within MB (in units of 4×4 blocks).
const BLOCK_IDX_TO_RC: [(usize, usize); 16] = [
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
    (0, 2),
    (0, 3),
    (1, 2),
    (1, 3),
    (2, 0),
    (2, 1),
    (3, 0),
    (3, 1),
    (2, 2),
    (2, 3),
    (3, 2),
    (3, 3),
];

/// MB-level block scan order: which 4×4 block_idx to process in
/// which order. This is what libavcodec / x264 emit per §7.3.5.3.
const SCAN_8X8: [[usize; 4]; 4] = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]];

/// P-frame transcode for one slice, MV=(0,0) per MB.
/// `target`: this frame's downscaled luma pixels.
/// `reference`: the previous frame's reconstructed luma pixels
///             (what the decoder will use as motion-comp source).
/// Returns:
///   - `mb_luma`: quantised residual coefs, one per MB block layout
///   - `cbp_luma_per_mb`: 8×8 CBP nibble per MB (0..15)
///   - `mb_skip_per_mb`: true if the MB had no nonzero coefs
///     (encoder can emit P_Skip = 1 bin instead of a full MB)
///   - `reconstructed`: this frame's reconstructed luma plane
///     (becomes the reference for the next P-frame)
pub fn transcode_p_frame_static_mv0(
    target: &[u8],
    reference: &[u8],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    qp: i32,
) -> (Vec<i32>, Vec<u8>, Vec<bool>, Vec<u8>) {
    assert_eq!(target.len(), plane_w * plane_h);
    assert_eq!(reference.len(), plane_w * plane_h);
    let n_mbs = mb_w * mb_h;
    let mut mb_luma = vec![0i32; n_mbs * 256];
    let mut cbp_per_mb = vec![0u8; n_mbs];
    let mut skip_per_mb = vec![false; n_mbs];
    let mut recon = vec![0u8; plane_w * plane_h];

    // Parallelise across MB rows. Each row is independent for P-frame
    // MV=0 transcoding (no cross-MB state — no intra prediction here,
    // no boundary CBF/MVD threading). One thread per row chunk.
    let n_threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
        .min(mb_h);
    let rows_per_chunk = (mb_h + n_threads - 1) / n_threads;

    // Split the output buffers row-aligned so each thread gets an
    // exclusive &mut slice.
    let luma_per_row = mb_w * 256;
    let mbs_per_row = mb_w;
    let recon_per_row = plane_w * 16;
    let mut luma_remaining: &mut [i32] = &mut mb_luma;
    let mut cbp_remaining: &mut [u8] = &mut cbp_per_mb;
    let mut skip_remaining: &mut [bool] = &mut skip_per_mb;
    let mut recon_remaining: &mut [u8] = &mut recon;

    let mut chunks: Vec<(usize, usize, &mut [i32], &mut [u8], &mut [bool], &mut [u8])> =
        Vec::with_capacity(n_threads);
    let mut row = 0;
    while row < mb_h {
        let last = (row + rows_per_chunk).min(mb_h);
        let n_rows = last - row;
        let (luma_chunk, luma_rest) = luma_remaining.split_at_mut(n_rows * luma_per_row);
        let (cbp_chunk, cbp_rest) = cbp_remaining.split_at_mut(n_rows * mbs_per_row);
        let (skip_chunk, skip_rest) = skip_remaining.split_at_mut(n_rows * mbs_per_row);
        let (recon_chunk, recon_rest) = recon_remaining.split_at_mut(n_rows * recon_per_row);
        luma_remaining = luma_rest;
        cbp_remaining = cbp_rest;
        skip_remaining = skip_rest;
        recon_remaining = recon_rest;
        chunks.push((row, last, luma_chunk, cbp_chunk, skip_chunk, recon_chunk));
        row = last;
    }

    std::thread::scope(|scope| {
        for (start_row, end_row, luma_out, cbp_out, skip_out, recon_out) in chunks {
            scope.spawn(move || {
                transcode_p_frame_rows(
                    target, reference, plane_w, mb_w, start_row, end_row, qp, luma_out, cbp_out,
                    skip_out, recon_out,
                );
            });
        }
    });

    (mb_luma, cbp_per_mb, skip_per_mb, recon)
}

/// Per-row-chunk worker — transcodes MB rows [start_row, end_row)
/// into the caller-supplied output slices. Inputs are shared
/// read-only across all worker threads.
fn transcode_p_frame_rows(
    target: &[u8],
    reference: &[u8],
    plane_w: usize,
    mb_w: usize,
    start_row: usize,
    end_row: usize,
    qp: i32,
    mb_luma_chunk: &mut [i32],
    cbp_chunk: &mut [u8],
    skip_chunk: &mut [bool],
    recon_chunk: &mut [u8],
) {
    for mb_r in start_row..end_row {
        let local_r = mb_r - start_row;
        for mb_c in 0..mb_w {
            let local_mb = local_r * mb_w + mb_c;
            // 16×16 residual = target - reference (MV=0)
            let mut residual_16x16 = [[0i32; 16]; 16];
            for r in 0..16 {
                let row_off = (mb_r * 16 + r) * plane_w + mb_c * 16;
                for c in 0..16 {
                    residual_16x16[r][c] =
                        target[row_off + c] as i32 - reference[row_off + c] as i32;
                }
            }
            let mut any_nonzero_overall = false;
            let mut cbp_luma = 0u8;
            for i_8x8 in 0..4 {
                let mut any_nonzero_8x8 = false;
                let block_idx_base = i_8x8 * 4;
                for sub in 0..4 {
                    let block_idx = block_idx_base + sub;
                    let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                    let mut block_res = [0i32; 16];
                    for k in 0..4 {
                        for kk in 0..4 {
                            block_res[k * 4 + kk] = residual_16x16[br * 4 + k][bc * 4 + kk];
                        }
                    }
                    let y = forward_4x4(&block_res);
                    let z = quantize_intra_4x4(&y, qp);
                    let has_nz = z.iter().any(|&v| v != 0);
                    if has_nz {
                        any_nonzero_8x8 = true;
                        any_nonzero_overall = true;
                    }
                    let mb_base = local_mb * 256;
                    let blk_off = block_idx * 16;
                    for k in 0..16 {
                        mb_luma_chunk[mb_base + blk_off + k] = z[k];
                    }
                }
                if any_nonzero_8x8 {
                    cbp_luma |= 1 << i_8x8;
                }
            }
            cbp_chunk[local_mb] = cbp_luma;
            skip_chunk[local_mb] = !any_nonzero_overall;

            for block_idx in 0..16 {
                let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                let mb_base = local_mb * 256;
                let blk_off = block_idx * 16;
                let mut z = [0i32; 16];
                for k in 0..16 {
                    z[k] = mb_luma_chunk[mb_base + blk_off + k];
                }
                let w = dequantize_intra_4x4(&z, qp);
                let mut pred_block = [0u8; 16];
                for k in 0..4 {
                    let row_off = (mb_r * 16 + br * 4 + k) * plane_w + mb_c * 16 + bc * 4;
                    for kk in 0..4 {
                        pred_block[k * 4 + kk] = reference[row_off + kk];
                    }
                }
                let recon_block = idct_add_4x4_h264(&w, &pred_block);
                // Write to the chunk's local slice. recon_chunk row offset
                // is relative to start_row.
                for k in 0..4 {
                    let row_off = (local_r * 16 + br * 4 + k) * plane_w + mb_c * 16 + bc * 4;
                    for kk in 0..4 {
                        recon_chunk[row_off + kk] = recon_block[k * 4 + kk];
                    }
                }
            }
        }
    }
}

/// Fused sub-pel P-frame transcoder. Replaces the two-step
/// `apply_motion_compensation` (u8 mc_ref) → `transcode_p_frame_static_mv0`
/// pipeline with a single pass that keeps the per-MB prediction
/// in `i32` end-to-end and only clips at the final recon, exactly
/// as the H.264 spec specifies (§8.5.14 `clip1Y` applies to
/// `pred + idct`, not to `pred` alone).
///
/// The two-step pipeline clips the sub-pel FIR output to u8 before
/// computing the residual, which is fine when the prediction fits
/// in `[0, 255]` but loses information when it overshoots — the
/// 6-tap FIR can produce small out-of-range values on high-contrast
/// edges, and the encoder/decoder then diverge by exactly the
/// clipping delta. Drift accumulates because each frame's recon is
/// the next frame's reference.
///
/// `mvs_qp` are quarter-pel MVs (`mvx_qp = int * 4 + frac`,
/// `frac ∈ 0..=3`, frac=0 = integer-pel). MV decomposition uses
/// `div_euclid` / `rem_euclid` so negative quarter-pel MVs split
/// correctly (mv=-5 → int=-2, frac=3).
///
/// Returns the same `(mb_luma, cbp, skip, recon)` tuple as
/// `transcode_p_frame_static_mv0` — callers can swap one for the
/// other on the strength of the `--subpel` flag.
pub fn transcode_p_frame_subpel_static(
    target: &[u8],
    reference: &[u8],
    mvs_qp: &[(i32, i32)],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    qp: i32,
) -> (Vec<i32>, Vec<u8>, Vec<bool>, Vec<u8>) {
    assert_eq!(target.len(), plane_w * plane_h);
    assert_eq!(reference.len(), plane_w * plane_h);
    assert_eq!(mvs_qp.len(), mb_w * mb_h);

    // Widen the reference plane to i32 once. Both the FIR
    // (which needs ≥21-bit headroom for the 6-tap intermediates)
    // and the integer-pel fast path read from this buffer.
    let ref_i32: Vec<i32> = reference.iter().map(|&b| b as i32).collect();

    let n_mbs = mb_w * mb_h;
    let mut mb_luma = vec![0i32; n_mbs * 256];
    let mut cbp_per_mb = vec![0u8; n_mbs];
    let mut skip_per_mb = vec![false; n_mbs];
    let mut recon = vec![0u8; plane_w * plane_h];

    let n_threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
        .min(mb_h);
    let rows_per_chunk = (mb_h + n_threads - 1) / n_threads;
    let luma_per_row = mb_w * 256;
    let mbs_per_row = mb_w;
    let recon_per_row = plane_w * 16;
    let mut luma_remaining: &mut [i32] = &mut mb_luma;
    let mut cbp_remaining: &mut [u8] = &mut cbp_per_mb;
    let mut skip_remaining: &mut [bool] = &mut skip_per_mb;
    let mut recon_remaining: &mut [u8] = &mut recon;
    let mut chunks: Vec<(usize, usize, &mut [i32], &mut [u8], &mut [bool], &mut [u8])> =
        Vec::with_capacity(n_threads);
    let mut row = 0;
    while row < mb_h {
        let last = (row + rows_per_chunk).min(mb_h);
        let n_rows = last - row;
        let (luma_chunk, luma_rest) = luma_remaining.split_at_mut(n_rows * luma_per_row);
        let (cbp_chunk, cbp_rest) = cbp_remaining.split_at_mut(n_rows * mbs_per_row);
        let (skip_chunk, skip_rest) = skip_remaining.split_at_mut(n_rows * mbs_per_row);
        let (recon_chunk, recon_rest) = recon_remaining.split_at_mut(n_rows * recon_per_row);
        luma_remaining = luma_rest;
        cbp_remaining = cbp_rest;
        skip_remaining = skip_rest;
        recon_remaining = recon_rest;
        chunks.push((row, last, luma_chunk, cbp_chunk, skip_chunk, recon_chunk));
        row = last;
    }

    let ref_i32_ref: &[i32] = &ref_i32;
    std::thread::scope(|scope| {
        for (start_row, end_row, luma_out, cbp_out, skip_out, recon_out) in chunks {
            scope.spawn(move || {
                transcode_p_frame_subpel_rows(
                    target,
                    reference,
                    ref_i32_ref,
                    mvs_qp,
                    plane_w,
                    plane_h,
                    mb_w,
                    start_row,
                    end_row,
                    qp,
                    luma_out,
                    cbp_out,
                    skip_out,
                    recon_out,
                );
            });
        }
    });

    (mb_luma, cbp_per_mb, skip_per_mb, recon)
}

fn transcode_p_frame_subpel_rows(
    target: &[u8],
    reference: &[u8],
    reference_i32: &[i32],
    mvs_qp: &[(i32, i32)],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    start_row: usize,
    end_row: usize,
    qp: i32,
    mb_luma_chunk: &mut [i32],
    cbp_chunk: &mut [u8],
    skip_chunk: &mut [bool],
    recon_chunk: &mut [u8],
) {
    let w = plane_w as i32;
    let h = plane_h as i32;
    let mut pred_i32 = [0i32; 256];

    for mb_r in start_row..end_row {
        let local_r = mb_r - start_row;
        for mb_c in 0..mb_w {
            let local_mb = local_r * mb_w + mb_c;
            let (mvx_qp, mvy_qp) = mvs_qp[mb_r * mb_w + mb_c];
            // Decompose quarter-pel MV: int_part = mv.div_euclid(4),
            // frac = mv.rem_euclid(4). div/rem_euclid handle negative
            // MVs without truncating-to-zero (mv=-5 → int=-2, frac=3).
            let int_dx = mvx_qp.div_euclid(4);
            let int_dy = mvy_qp.div_euclid(4);
            let x_frac = mvx_qp.rem_euclid(4) as u8;
            let y_frac = mvy_qp.rem_euclid(4) as u8;
            let int_x0 = (mb_c * 16) as i32 + int_dx;
            let int_y0 = (mb_r * 16) as i32 + int_dy;

            if x_frac == 0 && y_frac == 0 {
                // Integer-pel path — direct clamped copy out of the
                // i32 reference. Identical math to the two-step
                // pipeline since prediction is by definition in
                // [0, 255] (it's a byte from the reference plane).
                for yy in 0..16 {
                    let ry = (int_y0 + yy as i32).clamp(0, h - 1);
                    for xx in 0..16 {
                        let rx = (int_x0 + xx as i32).clamp(0, w - 1);
                        pred_i32[yy * 16 + xx] = reference_i32[(ry * w + rx) as usize];
                    }
                }
            } else {
                // Sub-pel path — vendored 6-tap FIR. Output stays
                // unclipped (i32) so the final recon clip after
                // residual addition matches the decoder bit-exact.
                crate::h264_inter_pred::interpolate_luma(
                    reference_i32,
                    plane_w,
                    plane_w,
                    plane_h,
                    int_x0,
                    int_y0,
                    x_frac,
                    y_frac,
                    16,
                    16,
                    /*bit_depth=*/ 8,
                    &mut pred_i32,
                    16,
                )
                .expect("interpolate_luma");
            }

            // 16×16 residual = target - pred_i32. Target is u8, pred is
            // i32 (possibly out of [0,255]). The residual is bounded by
            // the FIR's output range — ~±20 outside [-255, 255] in the
            // worst case for the j cross-term, which the 9-bit
            // quantiser tables handle without overflow.
            let mut residual_16x16 = [[0i32; 16]; 16];
            for r in 0..16 {
                let row_off = (mb_r * 16 + r) * plane_w + mb_c * 16;
                for c in 0..16 {
                    residual_16x16[r][c] = target[row_off + c] as i32 - pred_i32[r * 16 + c];
                }
            }
            let _ = reference; // silence unused warning for parity with sibling

            let mut any_nonzero_overall = false;
            let mut cbp_luma = 0u8;
            for i_8x8 in 0..4 {
                let mut any_nonzero_8x8 = false;
                let block_idx_base = i_8x8 * 4;
                for sub in 0..4 {
                    let block_idx = block_idx_base + sub;
                    let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                    let mut block_res = [0i32; 16];
                    for k in 0..4 {
                        for kk in 0..4 {
                            block_res[k * 4 + kk] = residual_16x16[br * 4 + k][bc * 4 + kk];
                        }
                    }
                    let y = forward_4x4(&block_res);
                    let z = quantize_intra_4x4(&y, qp);
                    let has_nz = z.iter().any(|&v| v != 0);
                    if has_nz {
                        any_nonzero_8x8 = true;
                        any_nonzero_overall = true;
                    }
                    let mb_base = local_mb * 256;
                    let blk_off = block_idx * 16;
                    for k in 0..16 {
                        mb_luma_chunk[mb_base + blk_off + k] = z[k];
                    }
                }
                if any_nonzero_8x8 {
                    cbp_luma |= 1 << i_8x8;
                }
            }
            cbp_chunk[local_mb] = cbp_luma;
            skip_chunk[local_mb] = !any_nonzero_overall;

            // Recon: dequant → IDCT-add with i32 prediction. The
            // i32-pred variant clips ONLY at the end (§8.5.14), so
            // out-of-range prediction samples survive until they're
            // combined with the residual — matching the decoder.
            for block_idx in 0..16 {
                let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                let mb_base = local_mb * 256;
                let blk_off = block_idx * 16;
                let mut z = [0i32; 16];
                for k in 0..16 {
                    z[k] = mb_luma_chunk[mb_base + blk_off + k];
                }
                let dq = dequantize_intra_4x4(&z, qp);
                let mut pred_block_i32 = [0i32; 16];
                for k in 0..4 {
                    for kk in 0..4 {
                        pred_block_i32[k * 4 + kk] = pred_i32[(br * 4 + k) * 16 + bc * 4 + kk];
                    }
                }
                let recon_block = idct_add_4x4_h264_i32pred(&dq, &pred_block_i32);
                for k in 0..4 {
                    let row_off = (local_r * 16 + br * 4 + k) * plane_w + mb_c * 16 + bc * 4;
                    for kk in 0..4 {
                        recon_chunk[row_off + kk] = recon_block[k * 4 + kk];
                    }
                }
            }
        }
    }
}

/// Variant of `intra_predict_and_quantise_slice` that only processes
/// MB rows in `[start_mb_row, end_mb_row)`. The first MB row in the
/// range treats top-neighbour samples as "unavailable" — matching
/// H.264's behaviour at slice boundaries (intra pred doesn't cross
/// slices). Returns mb_luma for just the rows in the range, length
/// `(end_mb_row - start_mb_row) * mb_w * 256`.
pub fn intra_predict_and_quantise_slice_range(
    target: &[u8],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    start_mb_row: usize,
    end_mb_row: usize,
    qp: i32,
) -> Vec<i32> {
    assert_eq!(target.len(), plane_w * plane_h);
    assert!(end_mb_row > start_mb_row);
    let n_mb_rows = end_mb_row - start_mb_row;
    let n_mbs = mb_w * n_mb_rows;
    let mut mb_luma = vec![0i32; n_mbs * 256];

    // Reconstruction plane covers only this slice's rows. Top
    // neighbour samples from the slice above are NOT available.
    let slice_rows = n_mb_rows * 16;
    let mut recon = vec![-1i16; plane_w * slice_rows];

    for local_r in 0..n_mb_rows {
        let mb_r = start_mb_row + local_r;
        for mb_c in 0..mb_w {
            let mb_idx = local_r * mb_w + mb_c;
            for i_8x8 in 0..4 {
                for &block_idx in SCAN_8X8[i_8x8].iter() {
                    let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                    let py = mb_r * 16 + br * 4;
                    let px = mb_c * 16 + bc * 4;
                    // Local-to-slice coords (recon plane is slice-
                    // sized; px is plane-x which is same as slice-x).
                    let recon_y = py - start_mb_row * 16;
                    let mut has_left = px > 0;
                    let mut has_top = recon_y > 0;
                    let mut left_sum = 0i32;
                    let mut top_sum = 0i32;
                    if has_left {
                        for k in 0..4 {
                            let v = recon[(recon_y + k) * plane_w + (px - 1)];
                            if v < 0 {
                                has_left = false;
                                break;
                            }
                            left_sum += v as i32;
                        }
                    }
                    if has_top {
                        for k in 0..4 {
                            let v = recon[(recon_y - 1) * plane_w + (px + k)];
                            if v < 0 {
                                has_top = false;
                                break;
                            }
                            top_sum += v as i32;
                        }
                    }
                    let pred = match (has_left, has_top) {
                        (true, true) => (left_sum + top_sum + 4) >> 3,
                        (true, false) => (left_sum + 2) >> 2,
                        (false, true) => (top_sum + 2) >> 2,
                        (false, false) => 128,
                    };

                    let mut residual = [0i32; 16];
                    for k in 0..4 {
                        let row_off = (py + k) * plane_w + px;
                        for kk in 0..4 {
                            residual[k * 4 + kk] = target[row_off + kk] as i32 - pred;
                        }
                    }
                    let y = forward_4x4(&residual);
                    let z = quantize_intra_4x4(&y, qp);
                    let w = dequantize_intra_4x4(&z, qp);
                    let pred_clamped = pred.max(0).min(255) as u8;
                    let pred_block = [pred_clamped; 16];
                    let recon_block = idct_add_4x4_h264(&w, &pred_block);

                    // Write recon back to local recon plane.
                    for k in 0..4 {
                        let row_off = (recon_y + k) * plane_w + px;
                        for kk in 0..4 {
                            recon[row_off + kk] = recon_block[k * 4 + kk] as i16;
                        }
                    }
                    // Write quantised Z into mb_luma (local row index).
                    let mb_base = mb_idx * 256;
                    let blk_off = block_idx * 16;
                    for k in 0..16 {
                        mb_luma[mb_base + blk_off + k] = z[k];
                    }
                }
            }
        }
    }
    mb_luma
}

/// Full intra-prediction + transform + quant + reconstruction loop
/// for a whole I-slice's luma plane. The Python script's main
/// per-MB-per-block hot loop, ported to Rust.
///
/// Inputs:
///   - `target`: the luma plane we want the decoder to reconstruct,
///     row-major, length = `plane_w * plane_h`. Values in 0..=255.
///   - `plane_w`, `plane_h`: dimensions of `target`.
///   - `mb_w`, `mb_h`: macroblock-grid dimensions. Caller must have
///     `mb_w * 16 == plane_w` and `mb_h * 16 == plane_h`.
///   - `qp`: slice QP.
///
/// Returns: flat mb_luma vector of length `mb_w * mb_h * 256` —
/// 16 quantised coefficients per 4×4 block, 16 blocks per MB, in
/// block_idx order (matching what the CABAC walker consumes).
pub fn intra_predict_and_quantise_slice(
    target: &[u8],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    qp: i32,
) -> Vec<i32> {
    assert_eq!(target.len(), plane_w * plane_h);
    assert_eq!(mb_w * 16, plane_w);
    assert_eq!(mb_h * 16, plane_h);

    let n_mbs = mb_w * mb_h;
    let mut mb_luma = vec![0i32; n_mbs * 256];
    // Reconstructed plane — mirrors what the decoder will produce.
    // -1 marks "not yet decoded" (we cast through i16 internally to
    // hold the sentinel). After encoding a block, values are 0..=255.
    let mut recon = vec![-1i16; plane_w * plane_h];

    for mb_r in 0..mb_h {
        for mb_c in 0..mb_w {
            let mb_idx = mb_r * mb_w + mb_c;
            for i_8x8 in 0..4 {
                for &block_idx in SCAN_8X8[i_8x8].iter() {
                    let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                    let py = mb_r * 16 + br * 4;
                    let px = mb_c * 16 + bc * 4;
                    // Neighbour availability — only check if the
                    // recon plane has a valid sample there.
                    let mut has_left = px > 0;
                    let mut has_top = py > 0;
                    let mut left_sum = 0i32;
                    let mut top_sum = 0i32;
                    if has_left {
                        for k in 0..4 {
                            let v = recon[(py + k) * plane_w + (px - 1)];
                            if v < 0 {
                                has_left = false;
                                break;
                            }
                            left_sum += v as i32;
                        }
                    }
                    if has_top {
                        for k in 0..4 {
                            let v = recon[(py - 1) * plane_w + (px + k)];
                            if v < 0 {
                                has_top = false;
                                break;
                            }
                            top_sum += v as i32;
                        }
                    }
                    let pred = match (has_left, has_top) {
                        (true, true) => (left_sum + top_sum + 4) >> 3,
                        (true, false) => (left_sum + 2) >> 2,
                        (false, true) => (top_sum + 2) >> 2,
                        (false, false) => 128,
                    };

                    // Residual = target - pred (16 samples).
                    let mut residual = [0i32; 16];
                    for k in 0..4 {
                        let row_off = (py + k) * plane_w + px;
                        for kk in 0..4 {
                            residual[k * 4 + kk] = target[row_off + kk] as i32 - pred;
                        }
                    }

                    // Forward DCT, quantise.
                    let y = forward_4x4(&residual);
                    let z = quantize_intra_4x4(&y, qp);

                    // Reconstruct via dequant + spec IDCT-add so our
                    // future predictors match what the decoder uses.
                    let w = dequantize_intra_4x4(&z, qp);
                    let mut pred_block = [0u8; 16];
                    for k in 0..16 {
                        pred_block[k] = pred.max(0).min(255) as u8;
                    }
                    let recon_block = idct_add_4x4_h264(&w, &pred_block);

                    // Write recon back to the running plane.
                    for k in 0..4 {
                        let row_off = (py + k) * plane_w + px;
                        for kk in 0..4 {
                            recon[row_off + kk] = recon_block[k * 4 + kk] as i16;
                        }
                    }

                    // Write quantised Z into the mb_luma buffer at
                    // block_idx position.
                    let mb_base = mb_idx * 256;
                    let blk_off = block_idx * 16;
                    for k in 0..16 {
                        mb_luma[mb_base + blk_off + k] = z[k];
                    }
                }
            }
        }
    }
    mb_luma
}

/// Same as `intra_predict_and_quantise_slice` but ALSO returns the
/// encoder-side reconstructed plane — the bit-exact plane the decoder
/// will produce from the same `mb_luma` coefficients.
///
/// Why this exists: at QP=0 our quantiser still loses ~0.21 mean-abs
/// per sample through the DCT round-trip. If the caller uses the
/// un-encoded `target` plane (or an `area_average_2to1` of the source)
/// as the IDR reference for subsequent P-frame motion estimation,
/// the encoder's MC will read from a plane the decoder never gets,
/// and every downstream P-frame compounds that offset. Returning the
/// correctly-reconstructed plane closes the loop.
pub fn intra_predict_and_quantise_slice_with_recon(
    target: &[u8],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    qp: i32,
) -> (Vec<i32>, Vec<u8>) {
    assert_eq!(target.len(), plane_w * plane_h);
    assert_eq!(mb_w * 16, plane_w);
    assert_eq!(mb_h * 16, plane_h);

    let n_mbs = mb_w * mb_h;
    let mut mb_luma = vec![0i32; n_mbs * 256];
    let mut recon = vec![-1i16; plane_w * plane_h];

    for mb_r in 0..mb_h {
        for mb_c in 0..mb_w {
            let mb_idx = mb_r * mb_w + mb_c;
            for i_8x8 in 0..4 {
                for &block_idx in SCAN_8X8[i_8x8].iter() {
                    let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
                    let py = mb_r * 16 + br * 4;
                    let px = mb_c * 16 + bc * 4;
                    let mut has_left = px > 0;
                    let mut has_top = py > 0;
                    let mut left_sum = 0i32;
                    let mut top_sum = 0i32;
                    if has_left {
                        for k in 0..4 {
                            let v = recon[(py + k) * plane_w + (px - 1)];
                            if v < 0 {
                                has_left = false;
                                break;
                            }
                            left_sum += v as i32;
                        }
                    }
                    if has_top {
                        for k in 0..4 {
                            let v = recon[(py - 1) * plane_w + (px + k)];
                            if v < 0 {
                                has_top = false;
                                break;
                            }
                            top_sum += v as i32;
                        }
                    }
                    let pred = match (has_left, has_top) {
                        (true, true) => (left_sum + top_sum + 4) >> 3,
                        (true, false) => (left_sum + 2) >> 2,
                        (false, true) => (top_sum + 2) >> 2,
                        (false, false) => 128,
                    };
                    let mut residual = [0i32; 16];
                    for k in 0..4 {
                        let row_off = (py + k) * plane_w + px;
                        for kk in 0..4 {
                            residual[k * 4 + kk] = target[row_off + kk] as i32 - pred;
                        }
                    }
                    let y = forward_4x4(&residual);
                    let z = quantize_intra_4x4(&y, qp);
                    let w = dequantize_intra_4x4(&z, qp);
                    let mut pred_block = [0u8; 16];
                    for k in 0..16 {
                        pred_block[k] = pred.max(0).min(255) as u8;
                    }
                    let recon_block = idct_add_4x4_h264(&w, &pred_block);
                    for k in 0..4 {
                        let row_off = (py + k) * plane_w + px;
                        for kk in 0..4 {
                            recon[row_off + kk] = recon_block[k * 4 + kk] as i16;
                        }
                    }
                    let mb_base = mb_idx * 256;
                    let blk_off = block_idx * 16;
                    for k in 0..16 {
                        mb_luma[mb_base + blk_off + k] = z[k];
                    }
                }
            }
        }
    }
    // All samples have been written above (every 4×4 block reconstructs
    // its 16 pixels). Narrow i16 → u8 unconditionally.
    let recon_u8: Vec<u8> = recon.into_iter().map(|v| v as u8).collect();
    (mb_luma, recon_u8)
}

/// Combined area-average + intra-predict + reconstruct, returning
/// both mb_luma and the encoder-side reconstructed plane. The recon
/// plane is what callers should hand to subsequent P-frame motion
/// estimation as the IDR reference — it's byte-exact with what the
/// decoder reconstructs from the same `mb_luma`.
pub fn transcode_2to1_luma_plane_with_recon(
    plane: &[u8],
    in_w: usize,
    in_h: usize,
    mb_w: usize,
    mb_h: usize,
    qp: i32,
) -> (Vec<i32>, Vec<u8>) {
    assert_eq!(plane.len(), in_w * in_h);
    let out_w = mb_w * 16;
    let out_h = mb_h * 16;
    assert_eq!(in_w, out_w * 2);
    assert_eq!(in_h, out_h * 2);
    let mut target = vec![0u8; out_w * out_h];
    area_average_2to1(plane, in_w, out_w, out_h, &mut target);
    intra_predict_and_quantise_slice_with_recon(&target, out_w, out_h, mb_w, mb_h, qp)
}

pub fn dequantize_intra_4x4(z: &[i32; 16], qp: i32) -> [i32; 16] {
    let qp_mod = (qp.rem_euclid(6)) as usize;
    let qp_div = qp / 6;
    let v = &V_TABLE[qp_mod];
    let mut w = [0i32; 16];
    // ITU-T §8.5.12.1, exact: LevelScale4x4 = weightScale(16) *
    // normAdjust(V_TABLE). For qP >= 24 the result is a pure left shift;
    // for qP < 24 it is a ROUNDED right shift (`+ 2^(3-qP/6)` then
    // `>> (4-qP/6)`). The previous `(z*v) << (qP/6)` form is the high-qP
    // path written without the *16 factor, and DROPS the low-qP rounding
    // offset — which only mattered on real textured residuals (the
    // synthetic gradients never hit the half-unit boundary), leaving a
    // +-1 in the inverse transform that propagated through I_NxN intra
    // prediction. This spec-exact form keeps the high-qP path identical
    // (so the bit-exact gradient cases stay bit-exact) and adds the
    // correct rounding for qP < 24.
    for k in 0..16 {
        let ls = 16 * v[k];
        w[k] = if qp_div >= 4 {
            (z[k] * ls) << (qp_div - 4)
        } else {
            (z[k] * ls + (1 << (3 - qp_div))) >> (4 - qp_div)
        };
    }
    w
}

const CF: [[f64; 4]; 4] = [
    [1.0, 1.0, 1.0, 1.0],
    [2.0, 1.0, -1.0, -2.0],
    [1.0, -1.0, -1.0, 1.0],
    [1.0, -2.0, 2.0, -1.0],
];

/// Cached numerical inverse of Cf. Built once.
static CF_INV: OnceLock<[[f64; 4]; 4]> = OnceLock::new();

fn cf_inv() -> &'static [[f64; 4]; 4] {
    CF_INV.get_or_init(|| invert_4x4(&CF))
}

/// 4×4 matrix inversion via Gauss–Jordan. Used once at startup
/// for the inverse-DCT operator.
fn invert_4x4(m: &[[f64; 4]; 4]) -> [[f64; 4]; 4] {
    let mut a = [[0.0f64; 8]; 4];
    for i in 0..4 {
        for j in 0..4 {
            a[i][j] = m[i][j];
        }
        a[i][i + 4] = 1.0;
    }
    for col in 0..4 {
        // Partial pivot.
        let mut pivot = col;
        for r in (col + 1)..4 {
            if a[r][col].abs() > a[pivot][col].abs() {
                pivot = r;
            }
        }
        if pivot != col {
            a.swap(col, pivot);
        }
        let p = a[col][col];
        assert!(p.abs() > 1e-12, "Cf is singular?!");
        for j in 0..8 {
            a[col][j] /= p;
        }
        for r in 0..4 {
            if r == col {
                continue;
            }
            let f = a[r][col];
            for j in 0..8 {
                a[r][j] -= f * a[col][j];
            }
        }
    }
    let mut inv = [[0.0f64; 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            inv[i][j] = a[i][j + 4];
        }
    }
    inv
}

/// Forward 4×4 H.264 integer DCT — `Y = Cf · X · Cfᵀ`. Integer
/// arithmetic exact (no rounding); output is raw transform
/// coefficients, NOT post-quantisation.
pub fn forward_4x4(x: &[i32; 16]) -> [i32; 16] {
    let mut t = [0i32; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0i32;
            for k in 0..4 {
                s += (CF[i][k] as i32) * x[k * 4 + j];
            }
            t[i * 4 + j] = s;
        }
    }
    let mut y = [0i32; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0i32;
            for k in 0..4 {
                s += t[i * 4 + k] * (CF[j][k] as i32);
            }
            y[i * 4 + j] = s;
        }
    }
    y
}

/// Inverse 4×4 transform via the numerical inverse of Cf. Returns
/// pixel values rounded to i32. `X = Cf⁻¹ · Y · (Cfᵀ)⁻¹`.
pub fn inverse_4x4(y: &[i32; 16]) -> [i32; 16] {
    inverse_4x4_f(y, |v| v.round() as i32)
}

/// Float-precision inverse, returning the raw f64 values without
/// rounding. Useful for the fold matrix construction.
fn inverse_4x4_f<F>(y: &[i32; 16], finalise: F) -> [i32; 16]
where
    F: Fn(f64) -> i32,
{
    let ci = cf_inv();
    let mut t = [0.0f64; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0.0f64;
            for k in 0..4 {
                s += ci[i][k] * (y[k * 4 + j] as f64);
            }
            t[i * 4 + j] = s;
        }
    }
    let mut x = [0i32; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0.0f64;
            for k in 0..4 {
                s += t[i * 4 + k] * ci[j][k];
            }
            x[i * 4 + j] = finalise(s);
        }
    }
    x
}

/// Float-domain forward DCT used internally when we want to feed a
/// non-integer block back through forward.
fn forward_4x4_f(x: &[f64; 16]) -> [f64; 16] {
    let mut t = [0.0f64; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0.0f64;
            for k in 0..4 {
                s += CF[i][k] * x[k * 4 + j];
            }
            t[i * 4 + j] = s;
        }
    }
    let mut y = [0.0f64; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0.0f64;
            for k in 0..4 {
                s += t[i * 4 + k] * CF[j][k];
            }
            y[i * 4 + j] = s;
        }
    }
    y
}

/// Float-domain inverse used internally.
fn inverse_4x4_pure_f(y: &[f64; 16]) -> [f64; 16] {
    let ci = cf_inv();
    let mut t = [0.0f64; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0.0f64;
            for k in 0..4 {
                s += ci[i][k] * y[k * 4 + j];
            }
            t[i * 4 + j] = s;
        }
    }
    let mut x = [0.0f64; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0.0f64;
            for k in 0..4 {
                s += t[i * 4 + k] * ci[j][k];
            }
            x[i * 4 + j] = s;
        }
    }
    x
}

/// Reference 4-to-1 fold: go through pixel domain. Slow but
/// correct. Pure float internally; rounded once at the end.
pub fn fold_4to1_via_pixels(
    tl: &[i32; 16],
    tr: &[i32; 16],
    bl: &[i32; 16],
    br: &[i32; 16],
) -> [i32; 16] {
    let f_tl = to_f(tl);
    let f_tr = to_f(tr);
    let f_bl = to_f(bl);
    let f_br = to_f(br);
    let p_tl = inverse_4x4_pure_f(&f_tl);
    let p_tr = inverse_4x4_pure_f(&f_tr);
    let p_bl = inverse_4x4_pure_f(&f_bl);
    let p_br = inverse_4x4_pure_f(&f_br);
    let tiled = tile_2x2_to_8x8_f(&p_tl, &p_tr, &p_bl, &p_br);
    let avg = area_average_8x8_to_4x4_f(&tiled);
    let coef_f = forward_4x4_f(&avg);
    let mut out = [0i32; 16];
    for i in 0..16 {
        out[i] = coef_f[i].round() as i32;
    }
    out
}

fn to_f(x: &[i32; 16]) -> [f64; 16] {
    let mut r = [0.0f64; 16];
    for i in 0..16 {
        r[i] = x[i] as f64;
    }
    r
}

fn tile_2x2_to_8x8_f(tl: &[f64; 16], tr: &[f64; 16], bl: &[f64; 16], br: &[f64; 16]) -> [f64; 64] {
    let mut out = [0.0f64; 64];
    for r in 0..4 {
        for c in 0..4 {
            out[r * 8 + c] = tl[r * 4 + c];
            out[r * 8 + (c + 4)] = tr[r * 4 + c];
            out[(r + 4) * 8 + c] = bl[r * 4 + c];
            out[(r + 4) * 8 + (c + 4)] = br[r * 4 + c];
        }
    }
    out
}

fn area_average_8x8_to_4x4_f(p: &[f64; 64]) -> [f64; 16] {
    let mut out = [0.0f64; 16];
    for r in 0..4 {
        for c in 0..4 {
            let sum = p[(2 * r) * 8 + (2 * c)]
                + p[(2 * r) * 8 + (2 * c + 1)]
                + p[(2 * r + 1) * 8 + (2 * c)]
                + p[(2 * r + 1) * 8 + (2 * c + 1)];
            out[r * 4 + c] = sum * 0.25;
        }
    }
    out
}

/// Precomputed DCT-domain fold matrix. Maps the 64-dim input
/// vector `[tl, tr, bl, br]` (concatenated 4 × 16 coefficients,
/// row-major within each block) to the 16-dim output vector.
///
/// Built once on first access: feed each of the 64 unit basis
/// vectors through `fold_4to1_via_pixels` (float-internal) and
/// record the output. Subsequent folds are a single 16×64 matvec.
static FOLD_MATRIX: OnceLock<[[f64; 64]; 16]> = OnceLock::new();

fn fold_matrix() -> &'static [[f64; 64]; 16] {
    FOLD_MATRIX.get_or_init(|| {
        let mut m = [[0.0f64; 64]; 16];
        for col in 0..64 {
            // Build unit input.
            let mut input = [0.0f64; 64];
            input[col] = 1.0;
            // Slice into four 4×4 blocks of f64.
            let mut tl = [0.0f64; 16];
            let mut tr = [0.0f64; 16];
            let mut bl = [0.0f64; 16];
            let mut br = [0.0f64; 16];
            tl.copy_from_slice(&input[0..16]);
            tr.copy_from_slice(&input[16..32]);
            bl.copy_from_slice(&input[32..48]);
            br.copy_from_slice(&input[48..64]);
            // Float-precision reference path.
            let p_tl = inverse_4x4_pure_f(&tl);
            let p_tr = inverse_4x4_pure_f(&tr);
            let p_bl = inverse_4x4_pure_f(&bl);
            let p_br = inverse_4x4_pure_f(&br);
            let tiled = tile_2x2_to_8x8_f(&p_tl, &p_tr, &p_bl, &p_br);
            let avg = area_average_8x8_to_4x4_f(&tiled);
            let out = forward_4x4_f(&avg);
            for row in 0..16 {
                m[row][col] = out[row];
            }
        }
        m
    })
}

/// Fast 4-to-1 fold via the precomputed matrix.
pub fn fold_4to1_via_matrix(
    tl: &[i32; 16],
    tr: &[i32; 16],
    bl: &[i32; 16],
    br: &[i32; 16],
) -> [i32; 16] {
    let m = fold_matrix();
    let mut input = [0.0f64; 64];
    for i in 0..16 {
        input[i] = tl[i] as f64;
        input[i + 16] = tr[i] as f64;
        input[i + 32] = bl[i] as f64;
        input[i + 48] = br[i] as f64;
    }
    let mut out = [0i32; 16];
    for row in 0..16 {
        let mut s = 0.0f64;
        for col in 0..64 {
            s += m[row][col] * input[col];
        }
        out[row] = s.round() as i32;
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn forward_constant_block_has_dc_only() {
        let x = [42i32; 16];
        let y = forward_4x4(&x);
        // For constant 42 input:
        //   Row sums of Cf: [4, 0, 0, 0]
        //   So Cf · X has all-zero rows except row 0 = [168, 168, 168, 168].
        //   Then (Cf · X) · Cfᵀ has [0][0] = 168 · 4 = 672, rest 0.
        assert_eq!(y[0], 672);
        for i in 1..16 {
            assert_eq!(y[i], 0, "non-DC coefficient {} should be 0", i);
        }
    }

    #[test]
    fn forward_inverse_round_trip_constant() {
        let x = [50i32; 16];
        let y = forward_4x4(&x);
        let x2 = inverse_4x4(&y);
        for i in 0..16 {
            let err = (x[i] - x2[i]).abs();
            assert!(err <= 1, "round-trip err at {}: {} vs {}", i, x[i], x2[i]);
        }
    }

    #[test]
    fn forward_inverse_round_trip_ramp() {
        let mut x = [0i32; 16];
        for i in 0..16 {
            x[i] = i as i32;
        }
        let y = forward_4x4(&x);
        let x2 = inverse_4x4(&y);
        for i in 0..16 {
            let err = (x[i] - x2[i]).abs();
            assert!(
                err <= 1,
                "ramp round-trip err at {}: {} vs {}",
                i,
                x[i],
                x2[i]
            );
        }
    }

    #[test]
    fn fold_constant_blocks_yields_constant_block() {
        let const_block = [80i32; 16];
        let y = forward_4x4(&const_block);
        let folded_coefs = fold_4to1_via_pixels(&y, &y, &y, &y);
        let folded_pixels = inverse_4x4(&folded_coefs);
        for i in 0..16 {
            let err = (folded_pixels[i] - 80).abs();
            assert!(
                err <= 1,
                "fold-constant err at {}: got {}",
                i,
                folded_pixels[i]
            );
        }
    }

    #[test]
    fn fold_matrix_matches_pixel_reference() {
        let tl: [i32; 16] = [120, -30, 5, 0, -10, 8, 2, 0, 3, 1, 0, 0, 0, 0, 0, 0];
        let tr: [i32; 16] = [115, 25, 4, 0, 12, 6, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0];
        let bl: [i32; 16] = [118, -20, 6, 0, -8, 5, 3, 0, 4, 1, 0, 0, 0, 0, 0, 0];
        let br: [i32; 16] = [122, 10, 3, 0, 5, 4, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0];

        let via_pixels = fold_4to1_via_pixels(&tl, &tr, &bl, &br);
        let via_matrix = fold_4to1_via_matrix(&tl, &tr, &bl, &br);

        for i in 0..16 {
            let err = (via_pixels[i] - via_matrix[i]).abs();
            assert!(
                err <= 1,
                "fold paths disagree at coef {}: pixels={}, matrix={}, err={}",
                i,
                via_pixels[i],
                via_matrix[i],
                err
            );
        }
    }

    #[test]
    fn fold_horizontal_ramp_preserves_shape() {
        // 8×8 horizontal ramp 0..7 — area-average gives
        // [0.5, 2.5, 4.5, 6.5] horizontally. After DCT/IDCT
        // round-trip this should be reasonably preserved.
        let mut p_top_left = [0i32; 16];
        let mut p_top_right = [0i32; 16];
        for r in 0..4 {
            for c in 0..4 {
                p_top_left[r * 4 + c] = c as i32;
                p_top_right[r * 4 + c] = (c + 4) as i32;
            }
        }
        let p_bot_left = p_top_left;
        let p_bot_right = p_top_right;

        let c_tl = forward_4x4(&p_top_left);
        let c_tr = forward_4x4(&p_top_right);
        let c_bl = forward_4x4(&p_bot_left);
        let c_br = forward_4x4(&p_bot_right);

        let folded = fold_4to1_via_pixels(&c_tl, &c_tr, &c_bl, &c_br);
        let folded_px = inverse_4x4(&folded);

        // Float-precision expected: per column [0.5, 2.5, 4.5, 6.5]
        // rounded to nearest int = [0 or 1, 2 or 3, 4 or 5, 6 or 7].
        for r in 0..4 {
            assert!(
                (folded_px[r * 4 + 0] - 0).abs() <= 1,
                "row {} col 0: {}",
                r,
                folded_px[r * 4 + 0]
            );
            assert!(
                (folded_px[r * 4 + 1] - 3).abs() <= 1,
                "row {} col 1: {}",
                r,
                folded_px[r * 4 + 1]
            );
            assert!(
                (folded_px[r * 4 + 2] - 5).abs() <= 1,
                "row {} col 2: {}",
                r,
                folded_px[r * 4 + 2]
            );
            assert!(
                (folded_px[r * 4 + 3] - 7).abs() <= 1,
                "row {} col 3: {}",
                r,
                folded_px[r * 4 + 3]
            );
        }
    }
}
