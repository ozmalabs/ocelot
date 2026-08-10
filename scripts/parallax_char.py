"""parallax_char — CHARACTERISATION (numpy-first, no Rust, no seed, no default moved).

THE INSIGHT UNDER TEST (rung 116000): objecthood lives in TEMPORAL coherence
(the closure rung's static null). The eye MOVES ITSELF by a KNOWN shift Δ
(efference copy). It predicts the reference-plane motion field that shift
causes and SUBTRACTS it; the residual is world structure. Over a scene WITH
DEPTH, the residual is PARALLAX: piecewise-constant, discontinuous exactly at
depth boundaries. Grouping the residual by common fate carves the scene into
surfaces (few + large). Over a FLAT scene, the shift is uniform, the residual
is ZERO everywhere, and nothing carves.

THE DISCRIMINATING CONTROL (the whole rigor): the STATIC frame `a` is
BYTE-IDENTICAL between DEPTH and FLAT (one periodic texture, no depth structure
visible statically). Only the post-shift frame `b` differs. So anything that
carves the identical static frame equally cannot be the discriminator; only
parallax vs uniform motion differs.

Stimulus: a single periodic texture `a` (toroidal, exact integer rolls, from
`motion_sensor_lib`). N vertical bands. DEPTH: band i rolled by its own integer
parallax shift s_i (∝ 1/depth). FLAT: the whole frame rolled by ONE shift
s_ref. Because all bands share ONE texture, `a` has NO band structure — the
depth planes are INVISIBLE in the static frame and appear ONLY in the motion.

Efference copy = the CHOSEN Δ_ref (the reference/fixation plane's shift), NEVER
estimated from pixels. Residual R = V - Δ_ref. Reference-band residual = 0
(space constancy). Grouping = spatially-connected regions of cells whose
velocity agrees within tolerance τ.

τ (§13): reported at the exact τ=0 (no number) AND the sensor's own
Otsu-within-aperture accuracy tolerance √5 ≈ 2.2361 (the norm of the integer
(1,2), MEASURED by the motion-sensor-gate rung 94000 — a boundary is a velocity
jump exceeding what the sensor produces by accuracy error). Neither is chosen
to make the answer look right; both are enumerated.
"""
from __future__ import annotations
import sys, os, json
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
import motion_sensor_lib as msl
from domains.motion_group_world import vector_field

SQRT5 = float(np.sqrt(5.0))   # 2.23607 — the sensor gate's Otsu-within-aperture split


def make_scene(rng, shifts, block, grid=msl.GRID, beta=1.0, contrast=32.0, ref_idx=None):
    """N vertical bands from ONE periodic texture.

    DEPTH: band i rolled horizontally by (0, shifts[i]).
    FLAT : the whole frame rolled by (0, shifts[ref_idx]) — uniform.

    Returns dict with a (static frame, byte-identical across conditions),
    b_depth, b_flat, ground-truth fields t_depth/t_flat, band owner per cell,
    mixed (seam) mask, and Δ_ref.
    """
    N = len(shifts)
    if ref_idx is None:
        ref_idx = N // 2
    a = msl.texture(rng, grid, beta=beta, contrast=contrast)
    edges = [round(i * grid / N) for i in range(N + 1)]

    # DEPTH: each band rolled by its own shift (horizontal parallax).
    b_depth = np.zeros_like(a)
    for i, s in enumerate(shifts):
        rolled = np.roll(a, int(s), axis=1)
        b_depth[:, edges[i]:edges[i + 1]] = rolled[:, edges[i]:edges[i + 1]]

    # FLAT: identical static frame, uniform shift (one depth).
    s_ref = shifts[ref_idx]
    b_flat = np.roll(a, int(s_ref), axis=1)

    nh, nw = grid // block, grid // block
    t_depth = np.zeros((nh, nw, 2))
    owner = np.zeros((nh, nw), dtype=int)
    mixed = np.zeros((nh, nw), dtype=bool)
    for c in range(nw):
        lo, hi = c * block, (c + 1) * block
        owners = set()
        for x in range(lo, hi):
            for i in range(N):
                if edges[i] <= x < edges[i + 1]:
                    owners.add(i)
        if len(owners) == 1:
            i = owners.pop()
        else:
            mixed[:, c] = True
            i = min(owners)
        owner[:, c] = i
        t_depth[:, c, 1] = float(shifts[i])
    t_flat = np.zeros((nh, nw, 2))
    t_flat[..., 1] = float(s_ref)
    return dict(a=a, b_depth=b_depth, b_flat=b_flat, t_depth=t_depth,
                t_flat=t_flat, owner=owner, mixed=mixed,
                delta_ref=np.array([0.0, float(s_ref)]), ref_idx=ref_idx,
                edges=edges, N=N, block=block, shifts=list(shifts))


def group_common_fate(vfield, tau):
    """Spatially-connected regions whose velocity agrees within τ (4-neighbour).

    A boundary is a velocity discontinuity: two adjacent cells join iff
    ‖v_i − v_j‖ ≤ τ. τ=0 is exact equality (no number). Returns (labels, nlab).
    """
    nh, nw = vfield.shape[0], vfield.shape[1]
    lab = -np.ones((nh, nw), dtype=int)
    nxt = 0
    for r0 in range(nh):
        for c0 in range(nw):
            if lab[r0, c0] >= 0:
                continue
            stack = [(r0, c0)]
            lab[r0, c0] = nxt
            while stack:
                r, c = stack.pop()
                v = vfield[r, c]
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < nh and 0 <= cc < nw and lab[rr, cc] < 0:
                        if np.hypot(*(vfield[rr, cc] - v)) <= tau:
                            lab[rr, cc] = nxt
                            stack.append((rr, cc))
            nxt += 1
    return lab, nxt


def size_dist(lab, nlab):
    sizes = np.array([(lab == k).sum() for k in range(nlab)])
    total = lab.size
    return dict(count=int(nlab),
                median=float(np.median(sizes)),
                largest=int(sizes.max()),
                largest_frac=float(sizes.max() / total),
                sizes=sorted(sizes.tolist(), reverse=True))


def field_discontinuity(vfield):
    """Max adjacent-cell velocity jump — proves whether a field CARRIED a
    boundary to segment on (guards against a vacuous null)."""
    nh, nw = vfield.shape[:2]
    m = 0.0
    for r in range(nh):
        for c in range(nw):
            for dr, dc in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < nh and cc < nw:
                    m = max(m, float(np.hypot(*(vfield[rr, cc] - vfield[r, c]))))
    return m


def run_one(rng, shifts, block, tau, beta=1.0, contrast=32.0, use_sensor=True):
    sc = make_scene(rng, shifts, block, beta=beta, contrast=contrast)
    # byte-identical static frame is guaranteed by construction (same `a`);
    # assert it anyway.
    assert np.array_equal(sc["a"], sc["a"])   # trivially; the point is ONE `a`
    delta = sc["delta_ref"]

    out = {}
    for cond, bkey, tkey in (("DEPTH", "b_depth", "t_depth"),
                             ("FLAT", "b_flat", "t_flat")):
        b = sc[bkey]
        t = sc[tkey]
        # --- ground-truth field (by construction) ---
        R_gt = t - delta
        # --- sensed field (real SAD sensor) ---
        if use_sensor:
            V = vector_field(sc["a"], b, block)
            R_se = V - delta
        else:
            V = t.copy(); R_se = R_gt.copy()
        rec = {}
        for tag, R in (("gt", R_gt), ("se", R_se)):
            lab, nl = group_common_fate(R, tau)
            rec[tag] = size_dist(lab, nl)
            rec[tag]["disc"] = field_discontinuity(R)
        # space constancy: residual on the reference band
        refmask = (sc["owner"] == sc["ref_idx"]) if cond == "DEPTH" else np.ones_like(sc["owner"], bool)
        rec["ref_resid_gt_max"] = float(np.abs(R_gt[refmask]).max())
        if use_sensor:
            rec["ref_resid_se_max"] = float(np.abs(R_se[refmask]).max())
            rec["sensor_err_max"] = float(np.abs(V - t).max())
        out[cond] = rec
    out["shifts"] = list(shifts); out["block"] = block; out["tau"] = tau
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(116900)   # PILOT seed (reserved; not confirmatory)
    print("=== EXACT-TO-PIXEL EFFERENCE-COPY SUBTRACTION CHECK (ground truth) ===")
    sc = make_scene(rng, [1, 3, 5], 4)
    R = sc["t_depth"] - sc["delta_ref"]
    refmask = sc["owner"] == sc["ref_idx"]
    print("reference-band residual max |R| (ground truth):", float(np.abs(R[refmask]).max()),
          "  (space constancy: expect EXACTLY 0.0)")
    print("static frame `a` is ONE array shared by DEPTH and FLAT (byte-identical):",
          "b_depth != b_flat where? cells:",
          int((sc['b_depth'] != sc['b_flat']).any(axis=0).sum()), "columns differ")

    print("\n=== PILOT SWEEP: size distribution DEPTH vs FLAT (sensed field) ===")
    for block in (4, 8):
        for shifts in ([1, 3, 5], [0, 3, 6], [0, 2, 4], [0, 4, 8], [1, 4]):
            for tau in (0.0, SQRT5):
                rng = np.random.default_rng(116900)
                r = run_one(rng, shifts, block, tau)
                d, f = r["DEPTH"], r["FLAT"]
                print(f"block={block} shifts={shifts} tau={tau:.2f} | "
                      f"DEPTH se: n={d['se']['count']:2d} med={d['se']['median']:5.1f} "
                      f"lgst={d['se']['largest_frac']:.2f} disc={d['se']['disc']:.2f} "
                      f"refres={d.get('ref_resid_se_max',0):.1f} serr={d.get('sensor_err_max',0):.0f} || "
                      f"FLAT se: n={f['se']['count']:2d} med={f['se']['median']:5.1f} "
                      f"lgst={f['se']['largest_frac']:.2f} disc={f['se']['disc']:.2f}")
