"""arc_ls20_live_measure — RUNG 219000: the FIRST LIVE perceive-on-real-render.

216000 measured pixel-segmentation parity on OFFLINE + SYNTHETIC ls20-shaped
grids. This harness pulls REAL LIVE ls20 frames from the ARC-AGI-3 API and runs
the SAME 216000 pipeline on them:

  ORACLE carve : cv2 4-conn per unique value on the SYMBOLIC live grid (the API's
                 integer frame — SCORING ORACLE ONLY, never fed to perception).
  PIXEL  carve : _render_screen(live_grid) -> RGB pixels -> recover_grid_from_render
                 (palette-quantize + lattice-register, pixels ONLY) -> same carve.

Metric: mean per-Region IoU + matched-Region fraction (best IoU >= 0.5) +
exact-grid-recovery frames, pooled over the REAL frames, Wilson/normal CIs. Plus
the Gaussian-noise degradation sweep on the real frames (where perception breaks
on real content vs the 216000 synthetic envelope).

HONEST CAVEAT: _render_screen is a LOSSLESS block render (no anti-aliasing), so
clean-render parity is near-1.0 BY CONSTRUCTION even on real frames; the value is
the source-audit + that it holds on REAL dense content + the degradation envelope.
The real anti-aliased browser render is unavailable via the API (symbolic grids).

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_live_measure.py \
        --game ls20-9607627b --frames 32
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT))

from worlds.arc import _render_screen, recover_grid_from_render  # noqa: E402
# Reuse the EXACT 216000 grader (carve / score_frame / measure / stats).
from arc_ls20_pixelseg_measure import carve, score_frame, measure, wilson, mean_ci  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402


def collect_live_frames(game_id: str, n_frames: int):
    """RESET the live game then cycle the server-legal directional actions,
    collecting each real symbolic grid. Bounded by n_frames (== API calls + 1).
    Returns (label, [grid, ...]) and the final GameState value + score."""
    from arc3_live_env import Arc3LiveEnv
    env = Arc3LiveEnv(game_id)
    f = env.reset()
    grids = [f.grid]
    states = [f.state.value]
    # cycle through whatever the server says is legal this frame (ls20 = ACTION1..4)
    i = 0
    while len(grids) < n_frames:
        avail = list(env.available_actions) or []
        if not avail:
            break
        act = avail[i % len(avail)]
        f = env.step(act)
        grids.append(f.grid)
        states.append(f.state.value)
        i += 1
        if f.state.value in ("WIN", "GAME_OVER"):
            # keep whatever we have; the live game ended
            break
    sc = env.close_scorecard()
    return ("ls20_live", grids), states, (f.score, f.state.value, sc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--frames", type=int, default=32,
                    help="number of REAL live frames to collect (== API calls)")
    ap.add_argument("--seed", type=int, default=219000,   # in the declared 219000-219999 block
                    help="rng seed for the noise sweep")
    ap.add_argument("--tag", default="live")
    args = ap.parse_args()

    if not load_arc_api_key():
        print("could not load ARC_API_KEY — aborting (NO number without auth)")
        return 1

    print(f"=== RUNG 219000 — LIVE perceive-on-real-render ({args.game}) ===")
    (label, grids), states, (final_score, final_state, scorecard) = \
        collect_live_frames(args.game, args.frames)
    print(f"collected {len(grids)} REAL live frames; final state={final_state} "
          f"levels_completed={final_score}")

    # density facts on the real frames (honesty: how much richer than synthetic)
    dens = []
    for g in grids:
        arr = np.asarray(g, dtype=np.int32)
        dens.append(int((arr != 0).sum()))
        vals = sorted(int(v) for v in np.unique(arr))
    print(f"real-frame non-empty cells: min={min(dens)} max={max(dens)} "
          f"mean={sum(dens)/len(dens):.0f} of 4096; palette values seen (last frame)={vals}")

    sequences = [(label, grids)]

    # round-trip sanity on the REAL frames
    rt_ok = True
    for grid in grids:
        h = len(grid); w = len(grid[0]) if h else 0
        rec = recover_grid_from_render(_render_screen(grid, h, w))
        if not np.array_equal(np.asarray(rec), np.asarray(grid)):
            rt_ok = False
            break

    rng = np.random.default_rng(args.seed)
    headline = measure(sequences, noise_sigma=0.0)
    robustness = []
    for sig in (2.0, 4.0, 8.0, 16.0, 24.0, 32.0, 48.0):
        robustness.append(measure(sequences, noise_sigma=sig, rng=rng))

    # locate the break point (first sigma where matched-fraction < 0.95)
    break_sigma = None
    for r in robustness:
        if r["matched_region_fraction"][0] < 0.95:
            break_sigma = r["noise_sigma"]
            break

    result = {
        "rung": 219000,
        "tag": args.tag,
        "game": args.game,
        "seed": args.seed,
        "commitment": "seeing-not-oracle on REAL LIVE ls20 frames; symbolic grid "
                      "is scoring-oracle only, never fed to pixel perception",
        "n_live_frames": len(grids),
        "final_state": final_state,
        "final_levels_completed": final_score,
        "real_frame_density": {"min": min(dens), "max": max(dens),
                               "mean": sum(dens) / len(dens), "of": 4096},
        "roundtrip_exact_inverse_on_live": rt_ok,
        "headline_clean_render": headline,
        "robustness_noise_sweep": robustness,
        "break_sigma_matched_below_0.95": break_sigma,
        "note": "_render_screen is a LOSSLESS block render (no anti-aliasing); "
                "clean-render parity near-1.0 by construction. Value: source-audit "
                "+ holds on REAL dense content + degradation envelope. Real "
                "anti-aliased browser render unavailable via API (symbolic grids).",
    }
    out = _ROOT / "results" / f"arc_ls20_live_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    def fmt(ci):
        return f"{ci[0]:.4f} [{ci[1]:.4f}, {ci[2]:.4f}]"

    h = headline
    print(f"\nroundtrip exact inverse on live frames: {rt_ok}")
    print(f"CLEAN RENDER  frames={h['n_frames']}  oracle-regions={h['n_regions']}")
    print(f"  grid exact-recovery frames : {h['grid_exact_recovery_frames']}/{h['n_frames']}")
    print(f"  mean per-Region IoU        : {fmt(h['mean_per_region_iou'])}")
    print(f"  matched-Region fraction    : {fmt(h['matched_region_fraction'])}")
    print("\nROBUSTNESS (Gaussian pixel noise on the live render before recovery):")
    print(f"  {'sigma':>6} {'meanIoU':>9} {'matched':>9} {'exactGrids':>11}")
    for r in robustness:
        print(f"  {r['noise_sigma']:6.1f} {r['mean_per_region_iou'][0]:9.4f} "
              f"{r['matched_region_fraction'][0]:9.4f} "
              f"{r['grid_exact_recovery_frames']:5d}/{r['n_frames']:<5d}")
    print(f"\nbreak sigma (matched < 0.95): {break_sigma}")
    print(f"scorecard: {scorecard}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
