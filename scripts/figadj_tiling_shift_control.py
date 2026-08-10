"""TILING-SHIFT CONTROL -- are the proto-objects SCENE structure or WINDOW artifact?

**POST-HOC. NOT PRE-REGISTERED.** Added after seeing the main run, because the
main run's ARM 2 cannot discriminate the confound this control targets, and
saying so without measuring it would leave the headline resting on an
unexamined assumption. It can only WEAKEN the rung's claim, never strengthen
it, and its result is reported whichever way it falls.

THE CONFOUND. The recommended G72 configuration tiles a 72x72 decode into 16
18x18 fields, and `border_ownership_world.add_field` sets `frame=1` on every
field's border. So EACH TILE independently asserts "my window edge is ground."
That is not a property of the scene: it manufactures enclosure at the window
boundary, and it is very likely why proto-objects appear at this configuration
when they did not at whole-frame lattices.

WHY ARM 2 CANNOT SEE IT. Cross-frame persistence is measured per tile position,
and the tile grid is FIXED across frames. A proto that is an artifact of the
window geometry is therefore PERFECTLY STABLE across frames and would beat both
registered floors -- including the arbitrary-partition floor, which randomises
the grouping but not the geometry. Persistence above those floors is consistent
with scene structure AND with window artifact; it does not separate them.

THE DISCRIMINATOR. Shift the tile grid by half a tile and re-decode the SAME
frame. Scene structure is indifferent to where the windows fall, so a real proto
should reappear under the shifted tiling. A window artifact is DEFINED by the
window, so it should not survive a shift that moves every boundary.

Read out: for each proto under tiling A, the best IoU against any proto under
tiling B (in shared 72x72 frame coordinates), against a size-matched
arbitrary-partition floor built the same way as the main run's FLOOR-B.

Seeds 83000-83999 (83300 block).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import scripts.figadj_replacement_measure as M                # noqa: E402

SEED_BLOCK = 83300
SHIFT = M.REGION // 2          # half a tile: every boundary moves
N_FRAMES = 10
K = M.K_MAIN


def origins_shifted(shift):
    """Tile origins offset by `shift`, keeping only tiles fully inside the
    frame. At shift=9 on a 72x72 field this is a 3x3 grid of 18x18 tiles whose
    every boundary lies where tiling A had tile INTERIOR."""
    return [(r0, c0)
            for r0 in range(shift, M.GRID - M.REGION + 1, M.REGION)
            for c0 in range(shift, M.GRID - M.REGION + 1, M.REGION)]


def protos_in_frame_coords(q, origins, arm):
    """Run every tile and lift each proto's support into 72x72 frame
    coordinates, so two different tilings are directly comparable."""
    out, enclosed = [], []
    for (r0, c0) in origins:
        r = M.run_one(M.tile(q, r0, c0), arm)
        for sup in r["support"].values():
            out.append([(r0 + rr, c0 + cc) for rr, cc in sup])
        enclosed += [(r0 + rr, c0 + cc) for rr, cc in r["enclosed_cells"]]
    return out, enclosed


def best_iou_list(a_supports, b_supports):
    if not a_supports:
        return None
    if not b_supports:
        return 0.0
    return float(np.mean([max(M.iou(p, q) for q in b_supports)
                          for p in a_supports]))


def main():
    print(f"[provenance] {M.ep.provenance_line()}", flush=True)
    oa = M.region_origins()
    ob = origins_shifted(SHIFT)
    print(f"[config] tiling A: {len(oa)} tiles at step {M.REGION} from 0; "
          f"tiling B: {len(ob)} tiles offset by {SHIFT}", flush=True)

    vp = M._vp()
    out = {"provenance": M.ep.provenance_line(),
           "post_hoc": True, "prereg": None,
           "shift": SHIFT, "n_frames": N_FRAMES, "k": K,
           "n_tiles_A": len(oa), "n_tiles_B": len(ob), "rows": []}

    for ci, cid in ((0, "C1"), (1, "C2")):
        spec = M.CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            M.N_DECODE, every=2, start_s=300, size=M.GRID,
            episode_index=spec["episode_index"])
        if not str(meta["episode_id"]).startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid} -- RUN VOID")

        for arm in M.ARMS:
            rng = np.random.RandomState(SEED_BLOCK + 10 * ci
                                        + (0 if arm == "incumbent" else 1))
            real, floor = [], []
            for t in range(N_FRAMES):
                q = M.quantize(frames[t], K)
                sa, _ = protos_in_frame_coords(q, oa, arm)
                sb, eb = protos_in_frame_coords(q, ob, arm)
                # restrict A's protos to the region tiling B actually covers,
                # so absence-of-coverage is not scored as disagreement
                cov = set(eb)
                sa_cov = [p for p in sa if cov.issuperset(set(p))]
                r = best_iou_list(sa_cov, sb)
                part = M.random_partition(eb, [len(x) for x in sb], rng)
                f = best_iou_list(sa_cov, list(part.values()))
                if r is None:
                    continue
                real.append(r)
                floor.append(f)
            row = {"corpus": cid, "arm": arm, "n_frames_scored": len(real),
                   "shifted_agreement": M.ci95(real),
                   "arbitrary_floor": M.ci95(floor),
                   "paired": M.paired_ci95(real, floor)}
            out["rows"].append(row)
            print(f"  [{cid}|{arm}] frames={len(real)} "
                  f"agree={row['shifted_agreement']['mean']} "
                  f"floor={row['arbitrary_floor']['mean']} "
                  f"paired_lo={row['paired']['lo']}", flush=True)

    rp = os.path.join(ROOT, "results", "figadj_tiling_shift.json")
    with open(rp, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[written] {rp}", flush=True)


if __name__ == "__main__":
    main()
