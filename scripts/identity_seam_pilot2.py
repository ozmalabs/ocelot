"""PILOT 2 (burned seeds only) — IS THE STOCK MINT GATE VACUOUS?

Pilot 1 showed the stock loop mints on frame 0 and then never again, with every
region resolving to its own frame-0 counterpart. That LOOKS like perfect
cross-frame identity. This pilot asks the question that distinguishes learning
from a vacuous gate:

  after the codebook is built from video, does a GENUINELY NOVEL region
  (a BSDS photograph tile; uniform noise; a value-shuffled tile) get MINTED,
  or is it force-matched to a held video identity?

`sd_recognize` fires on `Count(residual) == 0`, and residual is the uncovered
part of a COMPOSITIONAL decode over the whole parts library. If a large enough
library can compose any 36-cell tile, the gate is satisfied by everything and
minting stops for a reason that has nothing to do with recognition.

Not a result. Fixes n and the arm set for the pre-registration.
"""
from __future__ import annotations

import importlib.util as iu
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains import crossframe_world as cw  # noqa: E402
from scripts.identity_seam_pilot import StockSeamWorld, _vp  # noqa: E402


def bsds_tiles(n_photos=2):
    """Genuinely novel regions: natural photographs, a different corpus."""
    from PIL import Image
    from domains import vision_corpus as vc
    out = []
    for p in vc.bsds_paths("train")[:n_photos]:
        g = np.asarray(Image.open(p).convert("L"), float)
        h, w = g.shape
        crop = g[h // 2 - 60:h // 2 + 60, w // 2 - 60:w // 2 + 60]
        small = vc.area_downsample(crop / 255.0, cw.GRID) * 255.0
        out.extend(cw.regions_of(cw.quantize(small)))
    return out


def main():
    vp = _vp()
    frames, meta = vp.jellyfin_frames(12, every=2, start_s=300, size=cw.GRID,
                                      episode_index=0)
    q = [cw.quantize(f) for f in frames]

    w = StockSeamWorld()
    k0 = w.codebook_size()
    print(f"codebook at boot (before any pixel): K={k0}")

    # Build the codebook from 6 frames of video, exactly as pilot 1.
    for t in range(6):
        for i, tile in enumerate(cw.regions_of(q[t])):
            w.present(tile, tag=f"{t}_{i}")
            w.run()
    k_video = w.codebook_size()
    print(f"after 6 frames x 16 regions = 96 observations: K={k_video} "
          f"(minted {k_video - k0})")

    # ---- THE DECISIVE PROBES -------------------------------------------
    rng = np.random.RandomState(55001)          # burned block (crossframe rung)
    probes = []
    for j, tile in enumerate(bsds_tiles(2)):
        probes.append((f"bsds_{j}", tile))
    for j in range(8):
        probes.append((f"noise_{j}",
                       rng.randint(0, cw.K_LEVELS, (cw.REGION, cw.REGION))))
    for j, tile in enumerate(cw.regions_of(q[0])[:8]):
        probes.append((f"shuf_{j}", cw.shuffle_arrangement(tile, rng)))

    rows = []
    for tag, tile in probes:
        k_before = w.codebook_size()
        t0 = time.time()
        w.present(tile, tag=f"probe_{tag}")
        w.run()
        r = w.read_last()
        r["kind"] = tag.split("_")[0]
        r["minted_a_signature"] = w.codebook_size() > k_before
        r["ms"] = round((time.time() - t0) * 1000, 1)
        rows.append(r)

    print()
    for kind in ("bsds", "noise", "shuf"):
        sub = [r for r in rows if r["kind"] == kind]
        n_mint = sum(1 for r in sub if r["minted_a_signature"])
        print(f"{kind:6s} n={len(sub):2d}  MINTED {n_mint}/{len(sub)}  "
              f"statuses={sorted({r['status'] for r in sub})}  "
              f"covered_by={[r['covered_by'] for r in sub][:5]}")

    out = ROOT / "results" / "identity_seam_pilot2.json"
    out.write_text(json.dumps(
        {"meta": meta, "k_boot": k0, "k_video": k_video, "rows": rows,
         "provenance": ep.provenance_line()}, indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
