"""PILOT (burned seeds only) — does the STOCK sd loop accept pixel Observations?

Not a result. Establishes (a) that the wiring runs at all, (b) the mint rate the
stock loop produces on real frames, (c) the wall-clock cost as the codebook
grows. Used ONLY to fix n for the confirmatory pre-registration.
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


def _vp():
    spec = iu.spec_from_file_location("vp", str(HERE / "video_probe_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class StockSeamWorld:
    """ARM A: the STOCK sd loop, wired to pixels. No new rules at all.

    `shape_decode_loop` + `vision_sdloop` unmodified. An Observation carries the
    exact attrs the loop already reads (`signature`, `dim_types`, `key`,
    `status: pending`) plus `vq: 1`, which is the flag `vq_grow_quantum` already
    uses to install a minted quantum as a held ShapeSignature and bump
    `codebook_epoch`. Nothing here decides anything.
    """

    def __init__(self):
        from substrate.boot_core import boot_core
        from substrate.seed_loader import manifest_for
        from domains import reflective_faculty as rf

        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        rf._ensure_shape_decode_loop(self.s, self.native, self.ag)
        self.native.load_seed_manifest(manifest_for("vision_sdloop"), self.ag)
        self._obs = []

    def present(self, tile, *, tag: str):
        node = self.s.add_node("Observation", {
            "signature": cw.sig_of(tile),
            "key": [tag],
            "status": "pending",
            "dim_types": cw.DIM_TYPES,
            "vq": 1,
        })
        self.s.add_edge(self.ag, "observed", node)
        self._obs.append((node, tag))
        return node

    def run(self):
        self.native.run_rules()

    def codebook_size(self):
        return len(list(self.s.nodes("ShapeSignature")))

    def read_last(self):
        node, tag = self._obs[-1]
        at = self.s.node(node)["attrs"]
        return {
            "tag": tag,
            "status": at.get("status"),
            "covered_by": at.get("covered_by"),
            "covered_count": at.get("covered_count"),
            "residual_len": len(at.get("residual") or []),
        }


def main():
    vp = _vp()
    frames, meta = vp.jellyfin_frames(12, every=2, start_s=300, size=cw.GRID,
                                      episode_index=0)
    print("episode", meta.get("episode_id"))
    q = [cw.quantize(f) for f in frames]

    w = StockSeamWorld()
    rows = []
    t_start = time.time()
    for t in range(6):
        tiles = cw.regions_of(q[t])
        for i, tile in enumerate(tiles):
            t0 = time.time()
            w.present(tile, tag=f"{t}_{i}")
            w.run()
            dt = time.time() - t0
            r = w.read_last()
            r["frame"] = t
            r["region"] = i
            r["ms"] = round(dt * 1000, 1)
            r["K"] = w.codebook_size()
            rows.append(r)
        done = [r for r in rows if r["frame"] == t]
        minted = sum(1 for r in done if r["status"] == "minted")
        print(f"frame {t}: minted {minted}/16  K={w.codebook_size()}  "
              f"median ms={np.median([r['ms'] for r in done]):.0f}  "
              f"total {time.time()-t_start:.0f}s")

    out = ROOT / "results" / "identity_seam_pilot.json"
    out.write_text(json.dumps({"meta": meta, "rows": rows,
                               "provenance": ep.provenance_line()}, indent=1))
    print("statuses:", {r["status"] for r in rows})
    print("wrote", out)


if __name__ == "__main__":
    main()
