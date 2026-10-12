// Motion estimation compute shader — SAD search per macroblock.
//
// Each workgroup is responsible for ONE macroblock (16×16 luma
// samples). Within the workgroup, threads cooperatively scan a
// rectangular search window centred on the MB's position and
// compute the sum-of-absolute-differences between the target MB
// and each candidate reference MB. The best (lowest SAD) candidate
// wins.
//
// Workgroup layout: 8×8 = 64 threads. Each thread scans a slice
// of the search window. Best-MV reduction is done via shared
// memory.
//
// Bindings:
//   0: target plane  (u32 storage buffer, 4 packed u8 per word)
//   1: reference plane (same packing)
//   2: params (struct with dimensions + search window)
//   3: output  — per-MB best (mv_x, mv_y, sad) as 3×i32

struct Params {
    plane_w: u32,
    plane_h: u32,
    // Macroblock counts along each axis (NOT pixel size).
    // H.264 MB pixel size is always 16; we use that literal.
    mb_count_x: u32,
    mb_count_y: u32,
    search_radius: u32,  // search ±radius in luma pixels
    _pad: u32,
};

@group(0) @binding(0) var<storage, read> target_plane: array<u32>;
@group(0) @binding(1) var<storage, read> reference_plane: array<u32>;
@group(0) @binding(2) var<uniform> params: Params;
@group(0) @binding(3) var<storage, read_write> mv_out: array<i32>;

// Shared SAD min per thread within a workgroup.
var<workgroup> sad_min: array<u32, 64>;
var<workgroup> mv_min: array<u32, 64>;  // packed (mv_y << 16) | mv_x_signed_bits

// Read a single luma sample at (x, y) of the plane, with clamp-to-
// border for off-plane positions.
fn read_sample(plane: u32, x: i32, y: i32, w: i32, h: i32) -> u32 {
    let xc = clamp(x, 0, w - 1);
    let yc = clamp(y, 0, h - 1);
    let idx = u32(yc) * u32(w) + u32(xc);
    let word = idx / 4u;
    let byte_idx = idx & 3u;
    var bytes: u32;
    if plane == 0u {
        bytes = target_plane[word];
    } else {
        bytes = reference_plane[word];
    }
    return (bytes >> (byte_idx * 8u)) & 0xFFu;
}

// Compute SAD between target MB at (mb_x, mb_y) and reference at
// (ref_x, ref_y). Both are absolute luma pixel coordinates.
fn sad_16x16(
    mb_px: i32, mb_py: i32,
    ref_px: i32, ref_py: i32,
    w: i32, h: i32,
) -> u32 {
    var s: u32 = 0u;
    for (var dy: i32 = 0; dy < 16; dy = dy + 1) {
        for (var dx: i32 = 0; dx < 16; dx = dx + 1) {
            let t = read_sample(0u, mb_px + dx, mb_py + dy, w, h);
            let r = read_sample(1u, ref_px + dx, ref_py + dy, w, h);
            let d = i32(t) - i32(r);
            // Branchless abs.
            let ad = u32((d ^ (d >> 31)) - (d >> 31));
            s = s + ad;
        }
    }
    return s;
}

// Workgroup-shared cache. Sized for the maximum supported search
// radius (16). At radius R the reference window is (16 + 2R)².
// For R=16: 48*48 = 2304 samples; target MB is always 256 samples.
// One sample per u32 entry — wasteful (4× memory) but simple.
const MAX_RADIUS: u32 = 16u;
const WIN_SIDE: u32 = 16u + 2u * MAX_RADIUS;     // 48
const WIN_SAMPLES: u32 = WIN_SIDE * WIN_SIDE;    // 2304

var<workgroup> ref_window: array<u32, 2304>;
var<workgroup> target_mb_cache: array<u32, 256>;

// Cooperatively load target MB (256 samples) + reference window
// (win_side² samples) from global memory into workgroup cache.
// Caller must issue workgroupBarrier() after.
fn load_caches(
    lid: u32, mb_px: i32, mb_py: i32, w: i32, h: i32,
    radius: i32, win_side: u32, win_samples: u32,
) {
    for (var k: u32 = lid; k < 256u; k = k + 64u) {
        let y = k / 16u;
        let x = k % 16u;
        target_mb_cache[k] = read_sample(0u, mb_px + i32(x), mb_py + i32(y), w, h);
    }
    for (var k: u32 = lid; k < win_samples; k = k + 64u) {
        let wy = k / win_side;
        let wx = k % win_side;
        let rx = mb_px - radius + i32(wx);
        let ry = mb_py - radius + i32(wy);
        ref_window[k] = read_sample(1u, rx, ry, w, h);
    }
}

// SAD between target_mb_cache and ref_window at MV offset (cx, cy)
// in luma pixels (relative to MB origin, within radius).
fn sad_cached(cx: i32, cy: i32, radius: i32, win_side: u32) -> u32 {
    let off_x = u32(cx + radius);
    let off_y = u32(cy + radius);
    var s: u32 = 0u;
    for (var dy: u32 = 0u; dy < 16u; dy = dy + 1u) {
        let win_row = (off_y + dy) * win_side + off_x;
        let tgt_row = dy * 16u;
        for (var dx: u32 = 0u; dx < 16u; dx = dx + 1u) {
            let t = target_mb_cache[tgt_row + dx];
            let r = ref_window[win_row + dx];
            let d = i32(t) - i32(r);
            let ad = u32((d ^ (d >> 31)) - (d >> 31));
            s = s + ad;
        }
    }
    return s;
}

@compute @workgroup_size(8, 8, 1)
fn me_main(
    @builtin(workgroup_id) wg: vec3<u32>,
    @builtin(local_invocation_index) lid: u32,
) {
    let mb_x = wg.x;
    let mb_y = wg.y;
    if mb_x >= params.mb_count_x || mb_y >= params.mb_count_y { return; }

    let mb_px = i32(mb_x * 16u);
    let mb_py = i32(mb_y * 16u);
    let w = i32(params.plane_w);
    let h = i32(params.plane_h);
    let radius = i32(params.search_radius);
    let win_side: u32 = 16u + 2u * u32(radius);
    let win_samples: u32 = win_side * win_side;
    load_caches(lid, mb_px, mb_py, w, h, radius, win_side, win_samples);
    workgroupBarrier();

    let search_w = 2 * radius + 1;
    let total_cands = u32(search_w * search_w);

    var best_sad: u32 = 0xFFFFFFFFu;
    var best_dx: i32 = 0;
    var best_dy: i32 = 0;
    var i: u32 = lid;
    loop {
        if i >= total_cands { break; }
        let cand_x = i32(i) % search_w - radius;
        let cand_y = i32(i) / search_w - radius;
        let s = sad_cached(cand_x, cand_y, radius, win_side);
        if s < best_sad {
            best_sad = s;
            best_dx = cand_x;
            best_dy = cand_y;
        }
        i = i + 64u;
    }

    // Pack (mv_y, mv_x) signed into one u32 — high 16 = y, low 16 = x.
    sad_min[lid] = best_sad;
    mv_min[lid] = (u32(best_dy & 0xFFFF) << 16u) | u32(best_dx & 0xFFFF);
    workgroupBarrier();

    // Tree reduction: 64 → 1.
    var stride: u32 = 32u;
    loop {
        if stride == 0u { break; }
        if lid < stride {
            if sad_min[lid + stride] < sad_min[lid] {
                sad_min[lid] = sad_min[lid + stride];
                mv_min[lid] = mv_min[lid + stride];
            }
        }
        workgroupBarrier();
        stride = stride / 2u;
    }

    if lid == 0u {
        let mb_idx = mb_y * params.mb_count_x + mb_x;
        let packed = mv_min[0];
        // Sign-extend 16→32.
        let dx_u16: u32 = packed & 0xFFFFu;
        let dy_u16: u32 = (packed >> 16u) & 0xFFFFu;
        var dx_i: i32 = i32(dx_u16);
        if dx_u16 >= 0x8000u { dx_i = dx_i - 0x10000; }
        var dy_i: i32 = i32(dy_u16);
        if dy_u16 >= 0x8000u { dy_i = dy_i - 0x10000; }
        mv_out[mb_idx * 3u + 0u] = dx_i;
        mv_out[mb_idx * 3u + 1u] = dy_i;
        mv_out[mb_idx * 3u + 2u] = i32(sad_min[0]);
    }
}

// --- Hex / diamond iterative refinement ---------------------------------
//
// Hex search: at each iteration evaluate the 6 hex-offset points
// around the current centre plus the centre itself; jump to the
// best; repeat until centre wins. Then a single diamond (4
// neighbours) refinement pass for the half-step pixel offsets.
//
// Quality is "good enough" for natural-content motion estimation —
// the SAD landscape is mostly smooth around true motion. For
// adversarial synthetic test content the parity test still uses
// the full-search pipeline above.
//
// Workgroup: 64 threads. Each iteration evaluates 7 candidates (6
// hex + centre). We assign ~9 threads per candidate; each thread
// processes 16x16/9 ≈ 28 pixels of the SAD then we reduce.
//
// For simplicity here, we have each thread independently compute
// the FULL 16×16 SAD for ONE candidate per iteration (so only the
// first 7 threads do work; the rest idle). This is 7× less
// parallel than the full-search shader but the iteration count is
// what dominates wall time — typically 4-8 iterations of 7 candidates
// = 28-56 SAD evaluations per MB vs 1089 for radius=16 full search.

fn hex_offset(i: u32) -> vec2<i32> {
    switch (i) {
        case 0u: { return vec2<i32>(-2,  0); }
        case 1u: { return vec2<i32>(-1, -2); }
        case 2u: { return vec2<i32>( 1, -2); }
        case 3u: { return vec2<i32>( 2,  0); }
        case 4u: { return vec2<i32>( 1,  2); }
        case 5u: { return vec2<i32>(-1,  2); }
        default: { return vec2<i32>(0, 0); }
    }
}
fn diamond_offset(i: u32) -> vec2<i32> {
    switch (i) {
        case 0u: { return vec2<i32>(-1,  0); }
        case 1u: { return vec2<i32>( 1,  0); }
        case 2u: { return vec2<i32>( 0, -1); }
        case 3u: { return vec2<i32>( 0,  1); }
        default: { return vec2<i32>(0, 0); }
    }
}

var<workgroup> centre_x: i32;
var<workgroup> centre_y: i32;
var<workgroup> centre_sad: u32;
var<workgroup> cand_sads: array<u32, 7>;
var<workgroup> any_improved: u32;

@compute @workgroup_size(8, 8, 1)
fn me_hex(
    @builtin(workgroup_id) wg: vec3<u32>,
    @builtin(local_invocation_index) lid: u32,
) {
    let mb_x = wg.x;
    let mb_y = wg.y;
    if mb_x >= params.mb_count_x || mb_y >= params.mb_count_y { return; }

    let mb_px = i32(mb_x * 16u);
    let mb_py = i32(mb_y * 16u);
    let w = i32(params.plane_w);
    let h = i32(params.plane_h);
    let radius = i32(params.search_radius);
    let win_side: u32 = 16u + 2u * u32(radius);
    let win_samples: u32 = win_side * win_side;

    // Load target MB + reference window into workgroup cache once;
    // every iteration's SAD evaluation reads from shared memory.
    load_caches(lid, mb_px, mb_py, w, h, radius, win_side, win_samples);
    workgroupBarrier();

    if lid == 0u {
        centre_x = 0;
        centre_y = 0;
        centre_sad = sad_cached(0, 0, radius, win_side);
    }
    workgroupBarrier();

    // Hex refinement — up to log2(radius)+a few iterations.
    let max_iter: u32 = 12u;
    var iter: u32 = 0u;
    loop {
        if iter >= max_iter { break; }
        // Evaluate 6 hex points (threads 0..5).
        if lid < 6u {
            let off = hex_offset(lid);
            let cx = centre_x + off.x;
            let cy = centre_y + off.y;
            if abs(cx) > radius || abs(cy) > radius {
                cand_sads[lid] = 0xFFFFFFFFu;
            } else {
                cand_sads[lid] = sad_cached(cx, cy, radius, win_side);
            }
        }
        if lid == 0u {
            any_improved = 0u;
        }
        workgroupBarrier();
        if lid == 0u {
            var best_sad = centre_sad;
            var best_idx: i32 = -1;
            for (var i: u32 = 0u; i < 6u; i = i + 1u) {
                if cand_sads[i] < best_sad {
                    best_sad = cand_sads[i];
                    best_idx = i32(i);
                }
            }
            if best_idx >= 0 {
                let off = hex_offset(u32(best_idx));
                centre_x = centre_x + off.x;
                centre_y = centre_y + off.y;
                centre_sad = best_sad;
                any_improved = 1u;
            }
        }
        workgroupBarrier();
        if any_improved == 0u { break; }
        iter = iter + 1u;
    }

    // Diamond refinement (4 neighbours, single pass) for the tighter
    // half-step neighbourhood the hex pattern can skip over.
    if lid < 4u {
        let off = diamond_offset(lid);
        let cx = centre_x + off.x;
        let cy = centre_y + off.y;
        if abs(cx) > radius || abs(cy) > radius {
            cand_sads[lid] = 0xFFFFFFFFu;
        } else {
            cand_sads[lid] = sad_cached(cx, cy, radius, win_side);
        }
    }
    workgroupBarrier();
    if lid == 0u {
        var best_sad = centre_sad;
        var best_idx: i32 = -1;
        for (var i: u32 = 0u; i < 4u; i = i + 1u) {
            if cand_sads[i] < best_sad {
                best_sad = cand_sads[i];
                best_idx = i32(i);
            }
        }
        if best_idx >= 0 {
            let off = diamond_offset(u32(best_idx));
            centre_x = centre_x + off.x;
            centre_y = centre_y + off.y;
            centre_sad = best_sad;
        }
        let mb_idx = mb_y * params.mb_count_x + mb_x;
        mv_out[mb_idx * 3u + 0u] = centre_x;
        mv_out[mb_idx * 3u + 1u] = centre_y;
        mv_out[mb_idx * 3u + 2u] = i32(centre_sad);
    }
}
