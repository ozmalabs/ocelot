"""THE K ARM — perceived resolution as a function of the CODEBOOK, not the SENSOR.

`VISION_RESOLUTION_SCALE_PREREG.md` section 4, committed at `1fa4fe6d` before
any headline of this rung had been computed. Seeds **79200-79399**.

HOLD INPUT RESOLUTION FIXED (GRID = 72, REGION = 6 -- the highest this rung
reaches, so the sensor is at its most generous) and VARY K.

READ-OUTS, defined in the pre-registration and not changed afterwards:
  (a) DECODED FRACTION OF THE FIELD -- the fraction of presented regions whose
      status is `is_held`.
  (b) PERCEPT FINENESS -- the number of DISTINCT codebook entries used to cover
      ONE frame, and the normalized entropy of that per-frame usage.

THE TWO CONFOUNDS, CONTROLLED (prereg 4.2):
  1. K IS A DRAW, NOT A SETTING. K is NOT swept by re-seeding. ONE growth run
     at ONE seed is truncated to NESTED PREFIXES of its own mint order, so
     every smaller codebook is a strict prefix of every larger one.
  2. A GROWN CODEBOOK RAISES ITS OWN MEASURED NOISE FLOOR, so decoded-fraction
     across K rides a moving criterion. Every presentation's RAW score
     (`is_max`) is recorded, so the analysis reports each K TWICE: at its own
     re-measured floor, and at a FIXED floor held constant across all K.
     **The hypothesis is credited only if the effect survives the fixed
     criterion.**

THE FIREWALL (prereg 4.3): this arm licenses NO change to the effective-n
verdict of section 3. It is a separate question about a different variable.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import engine_provenance as ep              # noqa: E402

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT. Must run before the
# first import that LOADS the engine, or it is a no-op on resolution.
ep.engine_preamble()                                     # noqa: E402

from domains import identity_seam_world as sw            # noqa: E402
from domains import video_accumulation_world as aw       # noqa: E402

SEED = 79200
GRID = 72          # FIXED. The sensor is held at this rung's best.
REGION = 6         # FIXED.
N_CALIB = 8
FRAME_CACHE = os.environ.get("RS_FRAME_CACHE", "")

CORPORA = {
    "C1": {"pin": "08630d4b7b215c469df19b9c42d7b617", "what": "cartoon"},
    "C2": {"pin": "119eca433329b36b19e5d69fef84966e", "what": "live-action"},
}


def set_resolution(grid, region):
    """Blind write of declared measurement constants. The seam world and the
    accumulation world re-export the same names, so both are set."""
    for m in (sw, aw):
        m.GRID = grid
        m.REGION = region


def load_frames(cid, grid):
    p = os.path.join(FRAME_CACHE, f"{cid}_{grid}.npy")
    meta = json.load(open(os.path.join(FRAME_CACHE, "meta.json"))).get(
        f"{cid}_{grid}", {})
    if meta.get("episode_id") != CORPORA[cid]["pin"]:
        raise SystemExit(f"EPISODE PIN MISMATCH {cid}@{grid} -- run is VOID")
    return [np.asarray(f, float) for f in np.load(p)], meta


def grow(order, qr, gr, seed, n_regions, log):
    """Present training frames. EVERY MINT IS THE GRAPH'S -- this loop reads
    `codebook_size()` only to RECORD that a mint happened, never to decide."""
    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(seed), N_CALIB)
    w.run()
    mints, traj = [], []
    t0 = time.time()
    for n, t in enumerate(order):
        k0 = w.codebook_size()
        for i in range(n_regions):
            kk = w.codebook_size()
            w.present(qr[t][i], gr[t][i], tag=f"{t}_{i}")
            w.run()
            if w.codebook_size() > kk:
                mints.append({"frame": int(t), "region": int(i),
                              "n_train": int(n + 1)})
        traj.append({"n_train": n + 1, "frame": int(t),
                     "minted": w.codebook_size() - k0, "K": w.codebook_size()})
        if n % 5 == 0:
            log(f"    grow n_train={n+1}/{len(order)} K={w.codebook_size()} "
                f"({time.time()-t0:.0f}s)")
    log(f"    grow done: {len(order)} frames -> K={w.codebook_size()} "
        f"({time.time()-t0:.0f}s)")
    return mints, traj, w.codebook_size()


def eval_pass(entries, qr, gr, held, seed, n_regions):
    """A frozen evaluation pass. Records the RAW score of every presentation so
    a FIXED criterion can be applied outside the graph (prereg 4.2)."""
    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(seed), N_CALIB)
    w.run()
    w.install_codebook(entries)
    w.freeze()
    per_frame = []
    for t in held:
        ids, scores, held_ok = [], [], []
        for i in range(n_regions):
            w.present(qr[t][i], gr[t][i], tag=f"ev_{t}_{i}")
            w.run()
            r = w.read_full()
            w.refreeze()
            ok = (r["status"] == "is_held")
            held_ok.append(1.0 if ok else 0.0)
            scores.append(float(r["is_max"]) if r["is_max"] is not None else float("nan"))
            ids.append(r["identity"] if ok else None)
        per_frame.append({"frame": int(t), "held_ok": held_ok,
                          "scores": scores, "ids": ids})
    k, f = w.assert_frozen()
    return {"K": k, "floor": (float(f) if f is not None else None),
            "per_frame": per_frame}


def main():
    cids = (sys.argv[1].split(",") if len(sys.argv) > 1 else ["C1", "C2"])
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    n_held = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    set_resolution(GRID, REGION)
    n_regions = (GRID // REGION) ** 2

    prov = ep.provenance_line()
    out = {"provenance": prov, "prereg": "VISION_RESOLUTION_SCALE_PREREG.md",
           "prereg_commit": "1fa4fe6d7f44b69980ad198cbac439ea284446aa",
           "arm": "K", "grid": GRID, "region": REGION,
           "n_regions": n_regions, "seed": SEED,
           "n_train": n_train, "n_held": n_held,
           "loadavg_start": os.getloadavg(), "corpora": {}}
    print(f"[provenance] {prov}", flush=True)
    print(f"[K arm] GRID={GRID} REGION={REGION} n_regions={n_regions} "
          f"(INPUT RESOLUTION FIXED)  loadavg {out['loadavg_start']}", flush=True)

    def log(m):
        print(m, flush=True)

    for ci, cid in enumerate(cids):
        frames, meta = load_frames(cid, GRID)
        train, held = aw.block_split(len(frames))
        train, held = train[:n_train], held[:n_held]
        q = [aw.quantize(f) for f in frames]
        qr = [aw.regions_of(x, region=REGION) for x in q]
        gr = [aw.grey_regions_of(f, region=REGION) for f in frames]
        assert len(qr[0]) == n_regions, f"{len(qr[0])} != {n_regions}"
        log(f"[{cid}] {meta.get('name')} train={len(train)} held={len(held)} "
            f"regions/frame={n_regions}")
        R = {"meta": meta, "train": train, "held": held}
        t0 = time.time()
        mints, traj, K = grow(train, qr, gr, SEED + ci, n_regions, log)
        R["mints"], R["traj"], R["K_final"] = mints, traj, K
        R["grow_wall_s"] = time.time() - t0

        # NESTED PREFIXES of the SAME growth run (confound 1).
        ladder = sorted({cp for cp in
                         (1, 2, 3, 5, 8, 12, 20, 30, len(train))
                         if cp <= len(train)})
        R["ladder"] = ladder
        R["rungs"] = {}
        for cp in ladder:
            sel = [m for m in mints if m["n_train"] <= cp]
            if not sel:
                log(f"  [{cid}] cp={cp}: K=0, skipped")
                continue
            ents = [(f"{m['frame']}_{m['region']}",
                     qr[m["frame"]][m["region"]], gr[m["frame"]][m["region"]])
                    for m in sel]
            t1 = time.time()
            r = eval_pass(ents, qr, gr, held, SEED + 400 + ci, n_regions)
            r["wall_s"] = time.time() - t1
            r["n_train_prefix"] = cp
            R["rungs"][str(cp)] = r
            acc = float(np.mean([np.mean(p["held_ok"]) for p in r["per_frame"]]))
            dist = float(np.mean([len({i for i in p["ids"] if i})
                                  for p in r["per_frame"]]))
            log(f"  [{cid}] cp={cp:3d} K={r['K']:4d} decoded={acc:.4f} "
                f"distinct/frame={dist:6.2f} floor="
                f"{r['floor'] if r['floor'] is None else round(r['floor'], 4)} "
                f"({r['wall_s']:.0f}s)")
        R["loadavg"] = os.getloadavg()
        out["corpora"][cid] = R

    out["loadavg_end"] = os.getloadavg()
    path = os.path.join(ROOT, "results", "resolution_k_arm.json")
    with open(path, "w") as fh:
        json.dump(out, fh)
    print(f"[done] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
