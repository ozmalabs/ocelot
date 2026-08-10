"""arc_ls20_pixelseg_measure — RUNG 216000: pixel-segmentation PARITY.

THE COMMITMENT (seeing-not-oracle): the eye must SEE the game — derive the
segmentation from the RENDERED PIXELS only. The symbolic integer grid (arc3_grid)
is a SCORING ORACLE ONLY (as VizDoom depth/labels): it builds the golden trace and
grades IoU; it is NEVER fed to the pixel perception path.

This harness measures whether the PIXEL eye reproduces the ORACLE Region set from
the RENDER ALONE:

  ORACLE carve : cv2 connected-components (4-conn, per unique value) on the ORACLE
                 integer grid  -> golden-trace Regions (the spec of the native
                 `segment_and_track` / `_perceive_regions`).
  PIXEL  carve : _render_screen(grid) -> RGB pixels -> recover_grid_from_render
                 (palette-quantize + grid-register, pixels ONLY) -> the SAME cv2
                 carve on the RECOVERED grid -> pixel Regions.

Only difference between the two paths: oracle-grid vs recovered-from-pixels grid.
That isolates the perception delta. Metric: mean per-Region IoU + matched-Region
fraction (best-IoU >= 0.5), over N frames of real-protocol offline episodes AND a
synthetic ls20-shaped 64x64 sequence (real scale/density), with Wilson/normal CIs.
A robustness sweep degrades the render (Gaussian pixel noise) to find where the
pixel path breaks — the honest envelope.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_ls20_pixelseg_measure.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import cv2

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT))

from worlds.arc import _render_screen, recover_grid_from_render  # noqa: E402
import arc3_env as A3  # noqa: E402


# --------------------------------------------------------------------------
# THE CARVE — the spec of the native segment (cv2, 4-conn, per unique value).
# Used IDENTICALLY on the oracle grid and the pixel-recovered grid.
# --------------------------------------------------------------------------
def carve(grid):
    """[(value, frozenset{(r,c)})] — one component per 4-connected equal-value run."""
    arr = np.asarray(grid, dtype=np.int32)
    comps = []
    for val in np.unique(arr):
        mask = (arr == val).astype(np.uint8)
        n, labels, _stats, _c = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for k in range(1, n):
            ys, xs = np.where(labels == k)
            comps.append((int(val), frozenset(zip(ys.tolist(), xs.tolist()))))
    return comps


def score_frame(oracle_comps, pixel_comps):
    """Per oracle Region: best IoU against any unused pixel Region (position-set
    IoU, geometry only). Returns (list_of_best_ious, matched_count, n_oracle)."""
    used = set()
    ious = []
    matched = 0
    # greedy best-first assignment (oracle regions sorted large->small)
    order = sorted(range(len(oracle_comps)),
                   key=lambda i: -len(oracle_comps[i][1]))
    best_for = {}
    for oi in order:
        _ov, oc = oracle_comps[oi]
        best = 0.0
        bi = -1
        for i, (_pv, pc) in enumerate(pixel_comps):
            if i in used:
                continue
            inter = len(oc & pc)
            if inter == 0:
                continue
            iou = inter / len(oc | pc)
            if iou > best:
                best = iou
                bi = i
        best_for[oi] = best
        if best >= 0.5 and bi >= 0:
            matched += 1
            used.add(bi)
    for oi in range(len(oracle_comps)):
        ious.append(best_for[oi])
    return ious, matched, len(oracle_comps)


# --------------------------------------------------------------------------
# EPISODE SOURCES
# --------------------------------------------------------------------------
def offline_episode(env, actions):
    """Drive an offline arc3_env game; yield each frame's grid."""
    f = env.reset()
    grids = [f.grid]
    for a in actions:
        f = env.step(a)
        grids.append(f.grid)
    return grids


def offline_grids():
    """Real-protocol offline episodes across several games (the faithful ls20
    stand-in — same interaction contract; the private ls20 rules are unavailable
    without ARC_API_KEY). Returns [(label, [grid, ...]), ...]."""
    A1, A2, A3_, A4, A5, A6 = (A3.ACTION1, A3.ACTION2, A3.ACTION3,
                               A3.ACTION4, A3.ACTION5, A3.ACTION6)
    out = []
    # navigate — the ls20 NAVIGATION mechanic (avatar moved through a map to a goal)
    nav_actions = [A1, A1, A1, A4, A4, A4, A4, A4, A1, A3, A2, A2, A4, A1]
    out.append(("navigate", offline_episode(A3.NavigateEnv(), nav_actions)))
    # switches — coordinate clicks toggle cells
    sw = A3.SwitchesEnv()
    sw_actions = [(A6, (1, 1)), (A6, (4, 2)), (A6, (2, 4)), (A6, (1, 1))]
    f = sw.reset(); sg = [f.grid]
    for a, xy in sw_actions:
        f = sw.step(a, xy); sg.append(f.grid)
    out.append(("switches", sg))
    # collect — targets vanish on click (region births/deaths)
    try:
        col = A3.CollectEnv()
        f = col.reset(); cg = [f.grid]
        # click a few cells (mechanical sweep; some hit targets)
        for xy in [(2, 2), (3, 3), (4, 4), (1, 5), (5, 1)]:
            f = col.step(A6, xy); cg.append(f.grid)
        out.append(("collect", cg))
    except Exception:
        pass
    return out


def synthetic_ls20_grids(n_frames=12):
    """A synthetic ls20-SHAPED 64x64 sequence (real scale + density). Structure
    read from the repo's live-frame notes (worlds/arc.py, seeds/{projection,meter}):
    dark-grey field/walls=4, mid-grey rooms=3, a TWO-COLOUR avatar (blue 9 + yellow
    11) that navigates, a value-11 countdown METER bar that depletes, a red goal=8.
    Rendered LOSSLESSLY by _render_screen (cell_px=3 at 64x64) — so this measures
    the pipeline at ls20 scale, not real anti-aliasing (unavailable offline)."""
    H = W = 64
    grids = []
    for t in range(n_frames):
        g = [[4] * W for _ in range(H)]                 # dark-grey field/walls
        # three rooms (mid-grey 3), walled by the field
        for (r0, c0, r1, c1) in [(6, 6, 24, 26), (6, 34, 26, 58),
                                 (34, 10, 56, 40)]:
            for r in range(r0, r1):
                for c in range(c0, c1):
                    g[r][c] = 3
        # a goal target (red 8) in the third room
        g[45][35] = 8; g[45][36] = 8; g[46][35] = 8; g[46][36] = 8
        # the two-colour avatar (blue body 9 + yellow marker 11) walking right
        ar, ac = 15, 8 + t * 2
        if ac + 1 < W:
            g[ar][ac] = 9; g[ar + 1][ac] = 9
            g[ar][ac + 1] = 11
        # the countdown meter (yellow 11) depleting along the top
        mlen = max(1, 40 - t * 3)
        for c in range(2, 2 + mlen):
            g[2][c] = 11
        grids.append(g)
    return grids


# --------------------------------------------------------------------------
# STATS
# --------------------------------------------------------------------------
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def mean_ci(xs, z=1.96):
    n = len(xs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    m = sum(xs) / n
    if n == 1:
        return (m, m, m)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    se = sd / math.sqrt(n)
    return (m, m - z * se, m + z * se)


# --------------------------------------------------------------------------
# MEASURE
# --------------------------------------------------------------------------
def measure(sequences, noise_sigma=0.0, rng=None):
    """Run oracle-vs-pixel parity over every frame of every sequence. Returns a
    pooled result dict. `noise_sigma` > 0 adds Gaussian pixel noise to the render
    BEFORE recovery (robustness probe)."""
    all_ious = []
    frame_matched = 0
    frame_regions = 0
    reg_recovered_exact = 0     # frames where recovered grid == oracle grid exactly
    n_frames = 0
    per_seq = {}
    for label, grids in sequences:
        s_ious = []
        s_matched = 0
        s_regions = 0
        for grid in grids:
            h = len(grid); w = len(grid[0]) if h else 0
            screen = _render_screen(grid, h, w).astype(np.int16)
            if noise_sigma > 0:
                noise = (rng.normal(0.0, noise_sigma, size=screen.shape)
                         if rng is not None else
                         np.random.normal(0.0, noise_sigma, size=screen.shape))
                screen = np.clip(screen + noise, 0, 255)
            screen = screen.astype(np.uint8)
            recovered = recover_grid_from_render(screen)
            oracle_comps = carve(grid)
            pixel_comps = carve(recovered)
            ious, matched, n_oracle = score_frame(oracle_comps, pixel_comps)
            all_ious.extend(ious); s_ious.extend(ious)
            frame_matched += matched; s_matched += matched
            frame_regions += n_oracle; s_regions += n_oracle
            if (np.asarray(recovered, dtype=np.int32).shape == np.asarray(grid, dtype=np.int32).shape
                    and np.array_equal(np.asarray(recovered), np.asarray(grid))):
                reg_recovered_exact += 1
            n_frames += 1
        per_seq[label] = {
            "frames": len(grids),
            "n_regions": s_regions,
            "mean_iou": mean_ci(s_ious),
            "matched_fraction": wilson(s_matched, s_regions),
        }
    return {
        "noise_sigma": noise_sigma,
        "n_frames": n_frames,
        "n_regions": frame_regions,
        "grid_exact_recovery_frames": reg_recovered_exact,
        "mean_per_region_iou": mean_ci(all_ious),
        "matched_region_fraction": wilson(frame_matched, frame_regions),
        "per_sequence": per_seq,
    }


# --------------------------------------------------------------------------
# PRE-REGISTERED GATES (ARC_LS20_PIXELSEG_PREREG.md, seed 216000)
#   G-parity (headline): clean render mean IoU >= 0.99 AND matched >= 0.99
#   G-robust (teeth)   : at sigma=16 render noise, mean IoU >= 0.95 AND matched >= 0.95
# --------------------------------------------------------------------------
GATE_PARITY_IOU = 0.99
GATE_PARITY_MATCHED = 0.99
GATE_ROBUST_SIGMA = 16.0
GATE_ROBUST_IOU = 0.95
GATE_ROBUST_MATCHED = 0.95


def check_gates(headline, robustness):
    p_iou = headline["mean_per_region_iou"][0]
    p_match = headline["matched_region_fraction"][0]
    g_parity = p_iou >= GATE_PARITY_IOU and p_match >= GATE_PARITY_MATCHED
    r16 = next((r for r in robustness if abs(r["noise_sigma"] - GATE_ROBUST_SIGMA) < 1e-6), None)
    g_robust = (r16 is not None
                and r16["mean_per_region_iou"][0] >= GATE_ROBUST_IOU
                and r16["matched_region_fraction"][0] >= GATE_ROBUST_MATCHED)
    return {"G_parity": g_parity, "G_robust": g_robust}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=216000,   # in the declared 216000-216999 block
                    help="rng seed for the noise sweep (held-out confirmation uses a fresh in-block one)")
    ap.add_argument("--synth-frames", type=int, default=12)
    ap.add_argument("--nav-len", type=int, default=0,
                    help="extra navigate actions (held-out confirmation extends the episode)")
    ap.add_argument("--tag", default="first")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    seqs = offline_grids()
    if args.nav_len > 0:                        # extend the navigate episode (held-out frames)
        A1, A2, A3_, A4 = A3.ACTION1, A3.ACTION2, A3.ACTION3, A3.ACTION4
        cyc = [A4, A2, A3_, A1, A1, A4, A4, A2, A3_, A3_]
        extra = (cyc * ((args.nav_len // len(cyc)) + 1))[:args.nav_len]
        seqs.append(("navigate_heldout", offline_episode(A3.NavigateEnv(), extra)))
    sequences = seqs + [("synthetic_ls20_64", synthetic_ls20_grids(args.synth_frames))]

    # round-trip sanity: recover_grid_from_render is the exact inverse on a clean render
    rt_ok = True
    for _lbl, grids in sequences:
        for grid in grids:
            h = len(grid); w = len(grid[0]) if h else 0
            rec = recover_grid_from_render(_render_screen(grid, h, w))
            if not np.array_equal(np.asarray(rec), np.asarray(grid)):
                rt_ok = False
                break

    headline = measure(sequences, noise_sigma=0.0)
    robustness = []
    for sig in (2.0, 4.0, 8.0, 16.0, 24.0, 32.0, 48.0):
        robustness.append(measure(sequences, noise_sigma=sig, rng=rng))

    gates = check_gates(headline, robustness)
    result = {
        "rung": 216000,
        "tag": args.tag,
        "seed": args.seed,
        "commitment": "seeing-not-oracle: pixel eye derives Regions from the "
                      "RENDER ALONE; arc3_grid is scoring-oracle only",
        "roundtrip_exact_inverse": rt_ok,
        "headline_clean_render": headline,
        "robustness_noise_sweep": robustness,
        "gates": gates,
        "note": "offline arc3_env = faithful ls20 PROTOCOL stand-in (private ls20 "
                "rules need ARC_API_KEY, absent); _render_screen is a LOSSLESS block "
                "render (no anti-aliasing) — clean-render parity is near-trivial by "
                "construction; the honest frontier is the real 64x64 anti-aliased "
                "browser render, probed here via the Gaussian-noise sweep.",
    }
    out = _ROOT / "results" / f"arc_ls20_pixelseg_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    def fmt(ci):
        return f"{ci[0]:.4f} [{ci[1]:.4f}, {ci[2]:.4f}]"

    print("=== RUNG 216000 — pixel-segmentation parity (oracle vs pixel eye) ===")
    print(f"roundtrip exact inverse (clean render): {rt_ok}")
    h = headline
    print(f"\nCLEAN RENDER  frames={h['n_frames']}  oracle-regions={h['n_regions']}")
    print(f"  grid exact-recovery frames : {h['grid_exact_recovery_frames']}/{h['n_frames']}")
    print(f"  mean per-Region IoU        : {fmt(h['mean_per_region_iou'])}")
    print(f"  matched-Region fraction    : {fmt(h['matched_region_fraction'])}")
    print("  per-sequence:")
    for lbl, d in h["per_sequence"].items():
        print(f"    {lbl:20s} frames={d['frames']:2d} regions={d['n_regions']:3d} "
              f"IoU={fmt(d['mean_iou'])} matched={fmt(d['matched_fraction'])}")
    print("\nROBUSTNESS (Gaussian pixel noise on the render before recovery):")
    print(f"  {'sigma':>6} {'meanIoU':>9} {'matched':>9} {'exactGrids':>11}")
    for r in robustness:
        print(f"  {r['noise_sigma']:6.1f} {r['mean_per_region_iou'][0]:9.4f} "
              f"{r['matched_region_fraction'][0]:9.4f} "
              f"{r['grid_exact_recovery_frames']:5d}/{r['n_frames']:<5d}")
    print(f"\nGATES (pre-registered): G_parity={gates['G_parity']}  G_robust={gates['G_robust']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
