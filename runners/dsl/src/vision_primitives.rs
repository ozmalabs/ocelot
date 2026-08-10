//! Vision-pathway primitives — pure Rust functions, no graph state.
//!
//! Per CLAUDE.md, primitives in Rust + composition in graph. This
//! module is the dense-image generalization of `seeds/sensory_convolution.json`'s
//! `MaxOver(patches, Dot(kernel.weights, patch.vals))` primitive, which
//! operates one `Patch` node per window (fine for a handful of hand-
//! placed windows, too many nodes for a dense pixel grid). Here the
//! convolution runs directly over a flat `image: &[f64]` buffer and
//! returns a flat response buffer of the same row-major shape — no
//! per-window graph nodes.
//!
//! Per the frame/continuum invariant (CLAUDE.md 2026-07-08): a
//! convolution/change-detect RESPONSE is a continuous cross-frame map
//! (never in-frame integer coordinates), so its correct home is a
//! Rust Term (`term.rs::TermNode::ChangeDetect` / `Foveate`), not a
//! Python `cv2.filter2D` call. This module holds the arithmetic; the
//! `Term` variants in `term.rs` are the thin graph-composable wrapper
//! that reads Kernel/Image node attrs and calls into these functions.
//!
//! Per the 2026-07-16 developmental-vision refinement, `ChangeDetect`
//! is ONE spatiotemporal primitive with two faces:
//! - **spatial face** (`convolve`): a static image cross-correlated
//!   with a kernel — contrast / center-surround / DoG / oriented edges,
//!   depending on which kernel the agent has kept.
//! - **temporal face** (`temporal_diff`): the same primitive applied
//!   BETWEEN two frames (an event/motion/change stream) — matching
//!   retinal ganglion-cell biology, where "process deltas before
//!   pixels" makes the change stream primary.
//!
//! Nothing here touches the substrate graph. All graph mutation/read
//! happens in `term.rs`'s `ChangeDetect`/`Foveate` eval arms.

/// Valid (non-padded) 2D cross-correlation of a dense `image` (row-major,
/// `h` rows by `w` cols) against a `kernel` (row-major, `kh` by `kw`),
/// sampled every `stride` pixels in both dimensions. This is
/// cross-correlation (no kernel flip), matching `cv2.filter2D`'s
/// convention when the kernel is pre-flipped by the caller, and
/// matching the existing graph-native `Dot(kernel.weights, patch.vals)`
/// primitive exactly (`Dot` has no notion of flipping either — it is a
/// plain dot product over row-major-flattened window pixels).
///
/// Output is a dense buffer of shape `(out_h, out_w)` where
/// `out_h = (h - kh) / stride + 1` and `out_w = (w - kw) / stride + 1`
/// (both saturating to 0 if the kernel doesn't fit). Returns an empty
/// Vec if the kernel is larger than the image, `stride` is 0, or
/// `kernel.len() != kh * kw`.
///
/// This IS the spatial face of `ChangeDetect`: fed a center-surround
/// (DoG) kernel it yields lateral-inhibition contrast; fed an oriented
/// bar kernel it yields a V1-simple-cell-shaped edge response. Which
/// kernel is "kept" is an agent decision (`keep_discriminative_kernel`,
/// graph-native); this function is kernel-agnostic arithmetic.
pub fn convolve(image: &[f64], h: usize, w: usize, kernel: &[f64], kh: usize, kw: usize, stride: usize) -> Vec<f64> {
    if stride == 0 || kh == 0 || kw == 0 || h < kh || w < kw || kernel.len() != kh * kw || image.len() != h * w {
        return Vec::new();
    }
    let out_h = (h - kh) / stride + 1;
    let out_w = (w - kw) / stride + 1;
    let mut out = vec![0.0f64; out_h * out_w];
    for oy in 0..out_h {
        let y0 = oy * stride;
        for ox in 0..out_w {
            let x0 = ox * stride;
            let mut acc = 0.0f64;
            for ky in 0..kh {
                let row = (y0 + ky) * w;
                let krow = ky * kw;
                for kx in 0..kw {
                    acc += image[row + x0 + kx] * kernel[krow + kx];
                }
            }
            out[oy * out_w + ox] = acc;
        }
    }
    out
}

/// The temporal face of `ChangeDetect`: an elementwise event/motion
/// stream between two same-shaped observations (`a` = previous frame,
/// `b` = current frame). `b[i] - a[i]` per element — the simplest
/// possible "process deltas before pixels" primitive (event-camera /
/// DVS precedent: a pixel that hasn't changed emits nothing of
/// interest; a pixel that has emits a signed magnitude of change).
/// Returns an empty Vec if the two buffers aren't the same length
/// (a shape mismatch is a caller error, not something to silently pad).
pub fn temporal_diff(a: &[f64], b: &[f64]) -> Vec<f64> {
    if a.len() != b.len() {
        return Vec::new();
    }
    a.iter().zip(b.iter()).map(|(&av, &bv)| bv - av).collect()
}

/// Foveated (non-uniform) sampling of a dense image — cortical
/// magnification as data. `geometry` is a TWO-parameter buffer:
/// `geometry[0]` = `fovea_radius_frac` (fraction of `min(h,w)/2` — the
/// high-resolution central disc), `geometry[1]` = `periphery_stride`
/// (rows/cols OUTSIDE the fovea are kept every `stride`-th). Within
/// the foveal disc: full-rate (every row/col kept). Outside: strided.
/// Row and column selection are independent, so the output is a clean
/// rectangular sub-grid of the kept rows × kept cols.
///
/// This is the simplest correct foveation: the fovea is sharp (full
/// sampling) and the periphery is cheap (subsampled), matching the
/// biology's "process more detail where the eye points" without
/// committing to a particular blending kernel. `geometry` is graph
/// data the agent can revise (widen the fovea, coarsen the periphery)
/// — never a Python literal.
///
/// Returns `(sampled_values, out_h, out_w)`. Empty response (with
/// `out_h`/`out_w` = 0) on a degenerate input (zero-sized image or a
/// length-mismatched image buffer). Missing geometry fields default
/// to `fovea_radius_frac = 0.2`, `periphery_stride = 2`.
pub fn foveate(image: &[f64], h: usize, w: usize, geometry: &[f64]) -> (Vec<f64>, usize, usize) {
    if h == 0 || w == 0 || image.len() != h * w {
        return (Vec::new(), 0, 0);
    }
    let fov_frac = geometry.get(0).copied().unwrap_or(0.2).clamp(0.0, 1.0);
    let per_stride = geometry
        .get(1)
        .copied()
        .unwrap_or(2.0)
        .max(1.0)
        .round() as usize;
    let cy = (h as f64 - 1.0) / 2.0;
    let cx = (w as f64 - 1.0) / 2.0;
    let fov_r = fov_frac * (h.min(w) as f64) / 2.0;

    let mut sel_rows: Vec<usize> = Vec::with_capacity(h);
    for r in 0..h {
        let dr = (r as f64 - cy).abs();
        if dr <= fov_r || per_stride <= 1 || r % per_stride == 0 {
            sel_rows.push(r);
        }
    }
    let mut sel_cols: Vec<usize> = Vec::with_capacity(w);
    for c in 0..w {
        let dc = (c as f64 - cx).abs();
        if dc <= fov_r || per_stride <= 1 || c % per_stride == 0 {
            sel_cols.push(c);
        }
    }

    let out_h = sel_rows.len();
    let out_w = sel_cols.len();
    let mut out = Vec::with_capacity(out_h * out_w);
    for &r in &sel_rows {
        for &c in &sel_cols {
            out.push(image[r * w + c]);
        }
    }
    (out, out_h, out_w)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn convolve_identity_kernel_returns_input_center() {
        // 3x3 image, 1x1 identity kernel, stride 1 -> passthrough.
        let image = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0];
        let out = convolve(&image, 3, 3, &[1.0], 1, 1, 1);
        assert_eq!(out, image);
    }

    #[test]
    fn convolve_known_arithmetic_3x3_sum_kernel() {
        // 3x3 image, all-ones 3x3 kernel, stride 1 -> single output =
        // the sum of all 9 pixels (a known-input hand check).
        let image = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0];
        let kernel = vec![1.0; 9];
        let out = convolve(&image, 3, 3, &kernel, 3, 3, 1);
        assert_eq!(out, vec![45.0]);
    }

    #[test]
    fn convolve_center_surround_dog_matches_hand_computation() {
        // 4x4 image, a 3x3 centre-surround (DoG-shaped) kernel like
        // sensory_convolution.json's "centre_surround" Kernel node
        // (-1 ring, +8 centre), stride 1 -> 2x2 output. Hand-computed
        // against the same window arithmetic `Dot` would perform.
        #[rustfmt::skip]
        let image = vec![
            0.0, 0.0, 0.0, 0.0,
            0.0, 5.0, 5.0, 0.0,
            0.0, 5.0, 5.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
        ];
        #[rustfmt::skip]
        let kernel = vec![
            -1.0, -1.0, -1.0,
            -1.0,  8.0, -1.0,
            -1.0, -1.0, -1.0,
        ];
        let out = convolve(&image, 4, 4, &kernel, 3, 3, 1);
        assert_eq!(out.len(), 4); // 2x2
        // Top-left window (rows 0-2, cols 0-2): centre pixel (row1,col1)=5.0*8
        // minus the ring (row1,col2)=5.0 and (row2,col1)=5.0 and (row2,col2)=5.0.
        // window = [[0,0,0],[0,5,5],[0,5,5]]; centre=5 at (1,1).
        let expected_00 = 8.0 * 5.0 - (5.0 + 5.0 + 5.0);
        assert_eq!(out[0], expected_00);
    }

    #[test]
    fn convolve_stride_2_subsamples_output() {
        let image = vec![1.0; 16]; // 4x4 of ones
        let kernel = vec![1.0; 4]; // 2x2 ones
        let out = convolve(&image, 4, 4, &kernel, 2, 2, 2);
        // out_h = (4-2)/2+1 = 2, out_w = 2
        assert_eq!(out.len(), 4);
        assert!(out.iter().all(|&v| v == 4.0));
    }

    #[test]
    fn convolve_rejects_shape_mismatch() {
        let image = vec![1.0; 9];
        let kernel = vec![1.0; 4]; // says 2x2 but declared kh=3,kw=3 below
        assert!(convolve(&image, 3, 3, &kernel, 3, 3, 1).is_empty());
    }

    #[test]
    fn convolve_rejects_oversized_kernel() {
        let image = vec![1.0; 4]; // 2x2
        let kernel = vec![1.0; 9]; // 3x3, larger than image
        assert!(convolve(&image, 2, 2, &kernel, 3, 3, 1).is_empty());
    }

    #[test]
    fn temporal_diff_known_arithmetic() {
        let a = vec![1.0, 2.0, 3.0, 4.0];
        let b = vec![1.0, 5.0, 2.0, 4.0];
        let out = temporal_diff(&a, &b);
        assert_eq!(out, vec![0.0, 3.0, -1.0, 0.0]);
    }

    #[test]
    fn temporal_diff_zero_on_identical_frames() {
        let a = vec![9.0, 9.0, 9.0];
        let out = temporal_diff(&a, &a);
        assert_eq!(out, vec![0.0, 0.0, 0.0]);
    }

    #[test]
    fn temporal_diff_rejects_shape_mismatch() {
        let a = vec![1.0, 2.0];
        let b = vec![1.0, 2.0, 3.0];
        assert!(temporal_diff(&a, &b).is_empty());
    }

    #[test]
    fn foveate_full_fovea_keeps_whole_grid() {
        // fov_frac = 1.0 -> the foveal disc covers the whole image,
        // so every row/col is full-rate: passthrough.
        let image: Vec<f64> = (0..9).map(|x| x as f64).collect();
        let (out, out_h, out_w) = foveate(&image, 3, 3, &[1.0, 2.0]);
        assert_eq!((out_h, out_w), (3, 3));
        assert_eq!(out, image);
    }

    #[test]
    fn foveate_default_geometry_subsamples_periphery() {
        // 5x5 grid, fov_frac 0.1 -> fov_r = 0.1*5/2 = 0.25; only the
        // centre index (row/col 2, dr=0 <= 0.25) is foveal. Periphery
        // stride 2 keeps even indices (0,2,4). Selected rows/cols end
        // up {0,2,4} = 3 each — fovea adds index 2 (already kept by
        // stride too). Output is the 3x3 sub-grid at rows/cols {0,2,4}.
        let image: Vec<f64> = (0..25).map(|x| x as f64).collect();
        let (out, out_h, out_w) = foveate(&image, 5, 5, &[0.1, 2.0]);
        assert_eq!((out_h, out_w), (3, 3));
        let sel = [0usize, 2, 4];
        let mut expect = Vec::new();
        for &sr in &sel {
            for &sc in &sel {
                expect.push(image[sr * 5 + sc]);
            }
        }
        assert_eq!(out, expect);
    }

    #[test]
    fn foveate_stride_1_keeps_whole_grid() {
        // periphery_stride = 1 -> periphery kept at full rate too,
        // so the whole grid is kept regardless of fovea size.
        let image: Vec<f64> = (0..16).map(|x| x as f64).collect();
        let (out, out_h, out_w) = foveate(&image, 4, 4, &[0.0, 1.0]);
        assert_eq!((out_h, out_w), (4, 4));
        assert_eq!(out, image);
    }

    #[test]
    fn foveate_rejects_empty_image() {
        let (out, out_h, out_w) = foveate(&[], 0, 0, &[1.0, 2.0]);
        assert!(out.is_empty());
        assert_eq!((out_h, out_w), (0, 0));
    }

    #[test]
    fn foveate_rejects_length_mismatch() {
        let image = vec![1.0; 4]; // says 2x2 but len != 2*2*... here 4 == 2*2 ok
        // 3x3 declared but image only has 4 values -> mismatch -> empty.
        let (out, out_h, out_w) = foveate(&image, 3, 3, &[1.0, 2.0]);
        assert!(out.is_empty());
        assert_eq!((out_h, out_w), (0, 0));
    }
}
