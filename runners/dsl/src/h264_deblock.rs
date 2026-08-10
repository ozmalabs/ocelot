//! In-loop deblocking filter — ITU-T H.264 §8.7.
//!
//! This completes the agent's own I-frame decoder: after the CABAC
//! macroblock syntax + intra reconstruction produce the pre-filter
//! pixels, the deblocking filter smooths block-edge discontinuities.
//! Real H.264 streams have it ON, so it is REQUIRED for bit-exact
//! reconstruction of real content (and it removes the blocking
//! artefacts that make the raw reconstruction look chunky).
//!
//! Scope: the agent's decoder only emits I-slices (all intra), which
//! simplifies the boundary-strength derivation (§8.7.2.1):
//!
//!   * a macroblock-boundary edge with an intra MB on either side
//!     (always true here) has boundary strength bS = 4;
//!   * an internal block edge (not an MB boundary) with an intra MB
//!     has bS = 3.
//!
//! There are no inter / motion-vector / coded-block cases to consider
//! because every MB is intra. Chroma edges inherit the luma bS of the
//! co-located luma edge.
//!
//! The filter runs over the WHOLE picture in two passes per §8.7:
//! first all VERTICAL edges (left-to-right), then all HORIZONTAL
//! edges (top-to-bottom), macroblock by macroblock in raster order.
//! Within an MB the four vertical edges (x = 0,4,8,12) are filtered
//! left-to-right, then the four horizontal edges (y = 0,4,8,12)
//! top-to-bottom. The picture-boundary edges (x==0 of MB column 0,
//! y==0 of MB row 0) are skipped, as are edges disabled by the slice.

use crate::h264_cabac_mb::YuvFrame;

/// Per-macroblock info the deblocking filter needs.
#[derive(Clone, Copy)]
pub struct MbDeblockInfo {
    /// QPy of this macroblock (after mb_qp_delta accumulation).
    pub qp_luma: i32,
    /// QPc (chroma QP) of this macroblock.
    pub qp_chroma: i32,
    /// Always true for our I-slice decoder, but kept explicit.
    pub is_intra: bool,
}

/// α and β threshold tables, indexed by indexA / indexB (§8.7.2.2,
/// Table 8-16). 52 entries (one per clipped QP-derived index).
const ALPHA_TAB: [i32; 52] = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    4, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 17, 20, 22, 25, 28,
    32, 36, 40, 45, 50, 56, 63, 71, 80, 90, 101, 113, 127, 144, 162, 182,
    203, 226, 255, 255,
];
const BETA_TAB: [i32; 52] = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 6, 6, 7, 7, 8, 8,
    9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16,
    17, 17, 18, 18,
];
/// tC0 table (§8.7.2.3, Table 8-17), indexed by [bS-1][indexA].
/// Only bS = 1,2,3 use it (bS = 4 has its own strong filter).
const TC0_TAB: [[i32; 52]; 3] = [
    // bS = 1
    [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3,
        3, 3, 4, 4,
    ],
    // bS = 2
    [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
        1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6,
        6, 7, 8, 9,
    ],
    // bS = 3
    [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 6, 6, 7, 8,
        9, 10, 11, 13,
    ],
];

#[inline]
fn clip(v: i32, lo: i32, hi: i32) -> i32 { v.max(lo).min(hi) }

#[inline]
fn clip3(lo: i32, hi: i32, v: i32) -> i32 { v.max(lo).min(hi) }

/// Filter a single luma 4-sample line across an edge with bS < 4.
/// `p` = [p3,p2,p1,p0], `q` = [q0,q1,q2,q3] are the samples on either
/// side of the edge (p0/q0 adjacent to the edge). Returns the new
/// (p1,p0,q0,q1[,p2,q2]) in place. §8.7.2.4.
#[inline]
fn filter_luma_normal(
    p: &mut [i32; 4], q: &mut [i32; 4], alpha: i32, beta: i32, tc0: i32,
) {
    let (p0, p1, p2) = (p[3], p[2], p[1]);
    let (q0, q1, q2) = (q[0], q[1], q[2]);
    // Activity check (§8.7.2.1 filterSamplesFlag already gated by caller,
    // but the per-sample ap/aq below decide whether p1/q1 are filtered).
    let ap = (p2 - p0).abs();
    let aq = (q2 - q0).abs();
    let mut tc = tc0;
    if ap < beta { tc += 1; }
    if aq < beta { tc += 1; }
    let delta = clip3(-tc, tc, ((q0 - p0) * 4 + (p1 - q1) + 4) >> 3);
    let new_p0 = clip(p0 + delta, 0, 255);
    let new_q0 = clip(q0 - delta, 0, 255);
    p[3] = new_p0;
    q[0] = new_q0;
    if ap < beta {
        let dp = clip3(-tc0, tc0, (p2 + ((p0 + q0 + 1) >> 1) - 2 * p1) >> 1);
        p[2] = p1 + dp;
    }
    if aq < beta {
        let dq = clip3(-tc0, tc0, (q2 + ((p0 + q0 + 1) >> 1) - 2 * q1) >> 1);
        q[1] = q1 + dq;
    }
}

/// Filter a luma line across an edge with bS == 4 (strong filter).
/// §8.7.2.4. Modifies up to p2,p1,p0,q0,q1,q2.
#[inline]
fn filter_luma_strong(
    p: &mut [i32; 4], q: &mut [i32; 4], alpha: i32, beta: i32,
) {
    let (p0, p1, p2, p3) = (p[3], p[2], p[1], p[0]);
    let (q0, q1, q2, q3) = (q[0], q[1], q[2], q[3]);
    let ap = (p2 - p0).abs();
    let aq = (q2 - q0).abs();
    let small = (p0 - q0).abs() < ((alpha >> 2) + 2);
    if ap < beta && small {
        p[3] = (p2 + 2 * p1 + 2 * p0 + 2 * q0 + q1 + 4) >> 3;           // p0'
        p[2] = (p2 + p1 + p0 + q0 + 2) >> 2;                           // p1'
        p[1] = (2 * p3 + 3 * p2 + p1 + p0 + q0 + 4) >> 3;              // p2'
    } else {
        p[3] = (2 * p1 + p0 + q1 + 2) >> 2;                            // p0'
    }
    if aq < beta && small {
        q[0] = (q2 + 2 * q1 + 2 * q0 + 2 * p0 + p1 + 4) >> 3;          // q0'
        q[1] = (q2 + q1 + q0 + p0 + 2) >> 2;                          // q1'
        q[2] = (2 * q3 + 3 * q2 + q1 + q0 + p0 + 4) >> 3;             // q2'
    } else {
        q[0] = (2 * q1 + q0 + p1 + 2) >> 2;                           // q0'
    }
}

/// Filter a chroma line across an edge. §8.7.2.4. Chroma only ever
/// modifies p0,q0. bS==4 -> strong (averaging) form; bS<4 -> normal
/// with tc = tc0 + 1.
#[inline]
fn filter_chroma(
    p: &mut [i32; 2], q: &mut [i32; 2], _alpha: i32, _beta: i32, tc0: i32, bs4: bool,
) {
    let (p0, p1) = (p[1], p[0]);
    let (q0, q1) = (q[0], q[1]);
    if bs4 {
        p[1] = clip((2 * p1 + p0 + q1 + 2) >> 2, 0, 255);
        q[0] = clip((2 * q1 + q0 + p1 + 2) >> 2, 0, 255);
    } else {
        let tc = tc0 + 1;
        let delta = clip3(-tc, tc, ((q0 - p0) * 4 + (p1 - q1) + 4) >> 3);
        p[1] = clip(p0 + delta, 0, 255);
        q[0] = clip(q0 - delta, 0, 255);
    }
}

/// Whether the edge passes the §8.7.2.1 filterSamplesFlag gate:
/// |p0-q0| < α && |p1-p0| < β && |q1-q0| < β.
#[inline]
fn edge_active(p0: i32, p1: i32, q0: i32, q1: i32, alpha: i32, beta: i32) -> bool {
    (p0 - q0).abs() < alpha && (p1 - p0).abs() < beta && (q1 - q0).abs() < beta
}

/// Run the full in-loop deblocking filter over an I-slice frame.
///
/// `mb_info[mby*mb_w + mbx]` carries the per-MB QPs. `mb_w`/`mb_h` are
/// the macroblock grid dims. `alpha_off`/`beta_off` are the slice
/// FilterOffsetA / FilterOffsetB (= 2 * slice_alpha_c0_offset_div2 etc).
/// `disable_idc` follows the slice header: 1 = filter off entirely.
pub fn deblock_i_frame(
    frame: &mut YuvFrame,
    mb_info: &[MbDeblockInfo],
    mb_w: usize,
    mb_h: usize,
    alpha_off: i32,
    beta_off: i32,
    disable_idc: i32,
) {
    if disable_idc == 1 {
        return;
    }
    // Per §8.7 the filter processes macroblocks in raster order; for
    // each MB it filters its left vertical edges then its top
    // horizontal edges, reading the (already-filtered) neighbour
    // samples. We iterate the grid and for each MB do vertical edges
    // (x = 0,4,8,12) then horizontal edges (y = 0,4,8,12).
    for mby in 0..mb_h {
        for mbx in 0..mb_w {
            let info = mb_info[mby * mb_w + mbx];
            // ---- LUMA vertical edges ----
            for e in 0..4 {
                let x = mbx * 16 + e * 4;
                if x == 0 { continue; } // picture left boundary
                let is_mb_edge = e == 0;
                if is_mb_edge && mbx == 0 { continue; }
                let bs = if is_mb_edge { 4 } else { 3 };
                // QP averaged with the left neighbour for MB-boundary
                // edges (§8.7.2.2 qPav). Internal edges use this MB's QP.
                let qp = if is_mb_edge {
                    let l = mb_info[mby * mb_w + (mbx - 1)].qp_luma;
                    (info.qp_luma + l + 1) >> 1
                } else {
                    info.qp_luma
                };
                filter_vert_luma(frame, x, mby * 16, qp, bs, alpha_off, beta_off);
            }
            // ---- LUMA horizontal edges ----
            for e in 0..4 {
                let y = mby * 16 + e * 4;
                if y == 0 { continue; }
                let is_mb_edge = e == 0;
                if is_mb_edge && mby == 0 { continue; }
                let bs = if is_mb_edge { 4 } else { 3 };
                let qp = if is_mb_edge {
                    let t = mb_info[(mby - 1) * mb_w + mbx].qp_luma;
                    (info.qp_luma + t + 1) >> 1
                } else {
                    info.qp_luma
                };
                filter_horiz_luma(frame, mbx * 16, y, qp, bs, alpha_off, beta_off);
            }
            // ---- CHROMA edges ----
            // 4:2:0 -> 8x8 chroma per MB; only edges at chroma x/y in
            // {0,4} (= luma {0,8}) are filtered. The internal luma edge
            // at x=8 maps to chroma x=4 (an internal chroma edge, bS=3);
            // the MB-boundary luma edge x=0 maps to chroma x=0 (bS=4).
            for (is_cb, _c) in [(true, ()), (false, ())] {
                // vertical chroma edges at chroma-x 0 (MB edge) and 4 (internal)
                for (cx_off, is_mb_edge) in [(0usize, true), (4usize, false)] {
                    let cx = mbx * 8 + cx_off;
                    if cx == 0 { continue; }
                    if is_mb_edge && mbx == 0 { continue; }
                    let bs = if is_mb_edge { 4 } else { 3 };
                    let qp = if is_mb_edge {
                        let l = mb_info[mby * mb_w + (mbx - 1)].qp_chroma;
                        (info.qp_chroma + l + 1) >> 1
                    } else { info.qp_chroma };
                    filter_vert_chroma(frame, cx, mby * 8, qp, bs, alpha_off, beta_off, is_cb);
                }
                for (cy_off, is_mb_edge) in [(0usize, true), (4usize, false)] {
                    let cy = mby * 8 + cy_off;
                    if cy == 0 { continue; }
                    if is_mb_edge && mby == 0 { continue; }
                    let bs = if is_mb_edge { 4 } else { 3 };
                    let qp = if is_mb_edge {
                        let t = mb_info[(mby - 1) * mb_w + mbx].qp_chroma;
                        (info.qp_chroma + t + 1) >> 1
                    } else { info.qp_chroma };
                    filter_horiz_chroma(frame, mbx * 8, cy, qp, bs, alpha_off, beta_off, is_cb);
                }
            }
        }
    }
}

#[inline]
fn alpha_beta_tc0(qp: i32, bs: i32, alpha_off: i32, beta_off: i32) -> (i32, i32, i32) {
    let idx_a = clip(qp + alpha_off, 0, 51) as usize;
    let idx_b = clip(qp + beta_off, 0, 51) as usize;
    let alpha = ALPHA_TAB[idx_a];
    let beta = BETA_TAB[idx_b];
    let tc0 = if bs >= 1 && bs <= 3 { TC0_TAB[(bs - 1) as usize][idx_a] } else { 0 };
    (alpha, beta, tc0)
}

/// Filter the 16 luma lines of a vertical edge at column `x`, rows
/// `y0..y0+16`.
fn filter_vert_luma(
    frame: &mut YuvFrame, x: usize, y0: usize, qp: i32, bs: i32,
    alpha_off: i32, beta_off: i32,
) {
    let (alpha, beta, tc0) = alpha_beta_tc0(qp, bs, alpha_off, beta_off);
    if alpha == 0 { return; }
    let w = frame.w;
    for r in 0..16 {
        let y = y0 + r;
        if y >= frame.h { break; }
        let base = y * w + x;
        // p3..p0 are at x-4,x-3,x-2,x-1; q0..q3 at x,x+1,x+2,x+3.
        let mut p = [
            frame.y[base - 4] as i32, frame.y[base - 3] as i32,
            frame.y[base - 2] as i32, frame.y[base - 1] as i32,
        ];
        let mut q = [
            frame.y[base] as i32, frame.y[base + 1] as i32,
            frame.y[base + 2] as i32, frame.y[base + 3] as i32,
        ];
        if !edge_active(p[3], p[2], q[0], q[1], alpha, beta) { continue; }
        if bs == 4 {
            filter_luma_strong(&mut p, &mut q, alpha, beta);
        } else {
            filter_luma_normal(&mut p, &mut q, alpha, beta, tc0);
        }
        frame.y[base - 3] = p[1] as u8;
        frame.y[base - 2] = p[2] as u8;
        frame.y[base - 1] = p[3] as u8;
        frame.y[base]     = q[0] as u8;
        frame.y[base + 1] = q[1] as u8;
        frame.y[base + 2] = q[2] as u8;
    }
}

fn filter_horiz_luma(
    frame: &mut YuvFrame, x0: usize, y: usize, qp: i32, bs: i32,
    alpha_off: i32, beta_off: i32,
) {
    let (alpha, beta, tc0) = alpha_beta_tc0(qp, bs, alpha_off, beta_off);
    if alpha == 0 { return; }
    let w = frame.w;
    for c in 0..16 {
        let x = x0 + c;
        if x >= w { break; }
        let base = y * w + x;
        let mut p = [
            frame.y[base - 4 * w] as i32, frame.y[base - 3 * w] as i32,
            frame.y[base - 2 * w] as i32, frame.y[base - 1 * w] as i32,
        ];
        let mut q = [
            frame.y[base] as i32, frame.y[base + 1 * w] as i32,
            frame.y[base + 2 * w] as i32, frame.y[base + 3 * w] as i32,
        ];
        if !edge_active(p[3], p[2], q[0], q[1], alpha, beta) { continue; }
        if bs == 4 {
            filter_luma_strong(&mut p, &mut q, alpha, beta);
        } else {
            filter_luma_normal(&mut p, &mut q, alpha, beta, tc0);
        }
        frame.y[base - 3 * w] = p[1] as u8;
        frame.y[base - 2 * w] = p[2] as u8;
        frame.y[base - 1 * w] = p[3] as u8;
        frame.y[base]         = q[0] as u8;
        frame.y[base + 1 * w] = q[1] as u8;
        frame.y[base + 2 * w] = q[2] as u8;
    }
}

fn filter_vert_chroma(
    frame: &mut YuvFrame, cx: usize, cy0: usize, qp: i32, bs: i32,
    alpha_off: i32, beta_off: i32, is_cb: bool,
) {
    let (alpha, beta, tc0) = alpha_beta_tc0(qp, bs, alpha_off, beta_off);
    if alpha == 0 { return; }
    let cw = frame.w / 2;
    let ch = frame.h / 2;
    let plane = if is_cb { &mut frame.u } else { &mut frame.v };
    for r in 0..8 {
        let y = cy0 + r;
        if y >= ch { break; }
        let base = y * cw + cx;
        let mut p = [plane[base - 2] as i32, plane[base - 1] as i32];
        let mut q = [plane[base] as i32, plane[base + 1] as i32];
        if !edge_active(p[1], p[0], q[0], q[1], alpha, beta) { continue; }
        filter_chroma(&mut p, &mut q, alpha, beta, tc0, bs == 4);
        plane[base - 1] = p[1] as u8;
        plane[base]     = q[0] as u8;
    }
}

fn filter_horiz_chroma(
    frame: &mut YuvFrame, cx0: usize, cy: usize, qp: i32, bs: i32,
    alpha_off: i32, beta_off: i32, is_cb: bool,
) {
    let (alpha, beta, tc0) = alpha_beta_tc0(qp, bs, alpha_off, beta_off);
    if alpha == 0 { return; }
    let cw = frame.w / 2;
    let plane = if is_cb { &mut frame.u } else { &mut frame.v };
    for c in 0..8 {
        let x = cx0 + c;
        if x >= cw { break; }
        let base = cy * cw + x;
        let mut p = [plane[base - 2 * cw] as i32, plane[base - 1 * cw] as i32];
        let mut q = [plane[base] as i32, plane[base + 1 * cw] as i32];
        if !edge_active(p[1], p[0], q[0], q[1], alpha, beta) { continue; }
        filter_chroma(&mut p, &mut q, alpha, beta, tc0, bs == 4);
        plane[base - 1 * cw] = p[1] as u8;
        plane[base]          = q[0] as u8;
    }
}
