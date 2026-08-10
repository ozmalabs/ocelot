"""closure_measure -- DOES MDL CONTOUR CLOSURE PRODUCE A KNEE where value/wave
did not?  VISION_CLOSURE_PREREG.md.  Seeds 115000-115999.

The discriminator is the KNEE, not the median (s3): CONFIRM needs a STABLE
regime, robust across sigma^2*lambda, where ALL THREE hold -- enclosed median
in the OBJECT DECADE (>=10), count FEW-BUT-PLURAL (3-40), largest region NOT
most of the frame (<50%).  FALSIFY = the same monotone giant-ground<->fragment
trade-off with no knee.  AMBIGUOUS = a knife-edge knee or one condition fails.

CHARACTERISE, DO NOT BUILD.  numpy only; no Term, no seed, no Rust unless the
knee lands (index 180 reserved).  The value-flood floor 5047/3978 and the
enclosed median 1[1,1] are reproduced on the IDENTICAL frames and asserted
in-run (the run VOIDS otherwise).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                          # noqa: E402
import closure_lib as cl                                             # noqa: E402
import phasefield_pc as pf                                           # noqa: E402

EXPECT_ENGINE = "e039d2eec2dd"
SEED_BOOT = 115100

GRID = 72
REGION = 18
K_INCUMBENT = 16
PAD = 24
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)
FRAMES_WIDE = tuple(range(0, 150, 5))                # 30 frames, unit=frame
N_DECODE = 160
BOOT_N = 10000

PUBLISHED_ENCLOSED = {"C1": 5047, "C2": 3978}
CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))

# PC operating points (edge density) -- ENUMERATION, sparse where the flood
# leaks (phasefield's one-98%-blob regime).  None selected for the verdict.
DENSITY_LADDER = (0.03, 0.05, 0.10)
# sigma^2*lambda ROBUSTNESS axis (s2): scale multiplies the boundary/model
# COST; +-1 decade around the derived scale=1.0, extended to 100x.
SCALE_LADDER = (0.1, 1.0, 10.0, 100.0)
# candidate-gap CAP sweep -- to EXPOSE whether the cap is load-bearing (does
# MDL provide an intrinsic completion scale, or does it bridge to the cap?).
CAP_LADDER = (10, 20, 30, 40)


def loadavg():
    return [round(x, 2) for x in os.getloadavg()]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "scripts", f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pc_map(img, nscale=3):
    p = np.pad(img, PAD, mode="reflect")
    r = pf.phase_congruency(p, nscale=nscale)
    return r["pc"][PAD:PAD + img.shape[0], PAD:PAD + img.shape[1]]


def boot_median_ci(per_frame, rng):
    a = np.asarray([x for x in per_frame if x is not None], float)
    if a.size == 0:
        return {"n": 0, "median": None, "lo": None, "hi": None}
    idx = rng.integers(0, a.size, size=(BOOT_N, a.size))
    boot = np.median(a[idx], axis=1)
    return {"n": int(a.size), "median": float(np.median(a)),
            "lo": float(np.percentile(boot, 2.5)),
            "hi": float(np.percentile(boot, 97.5))}


def summarise(rows, rng):
    """rows: list of per-frame closure dicts -> the three discriminator stats."""
    enc_med = [r["enc_median"] for r in rows]
    n_enc = [r["n_enclosed"] for r in rows]
    largest = [r["largest_frac"] for r in rows]
    maxlen = [r["max_bridge_len"] for r in rows]
    nbr = [r["n_bridges"] for r in rows]
    return {
        "enc_median_ci": boot_median_ci(enc_med, rng),
        "n_enclosed_ci": boot_median_ci([float(x) for x in n_enc], rng),
        "largest_frac_ci": boot_median_ci(largest, rng),
        "max_bridge_len_mean": float(np.mean(maxlen)),
        "n_bridges_mean": float(np.mean(nbr)),
    }


def value_flood_baseline(frames, gc, rng):
    """Enclosed median 1[1,1] baseline -- the '1' the median compares against."""
    enc_med = []
    for f in frames:
        q = gc.quantize(f, K_INCUMBENT)
        st = gc.field_stats(q, f, tau=0)
        enc = st["enc_sizes"]
        enc_med.append(float(np.median(enc)) if enc else None)
    return boot_median_ci(enc_med, rng)


def main():
    ep.engine_preamble()
    prov = ep.provenance_line()
    if EXPECT_ENGINE not in prov:
        raise SystemExit(f"WRONG ENGINE: {prov}")
    print(prov)
    t0 = time.time()
    la0 = loadavg()
    rng = np.random.default_rng(SEED_BOOT)
    gc = _load("grouping_ceiling_measure")
    vp = _load("video_probe_measure")

    out = {"provenance": prov, "expect_engine": EXPECT_ENGINE,
           "loadavg_start": la0, "density_ladder": list(DENSITY_LADDER),
           "scale_ladder": list(SCALE_LADDER), "cap_ladder": list(CAP_LADDER),
           "corpora": {}}

    for cid, epi, pin in CORPORA:
        frames_all, meta = vp.jellyfin_frames(
            N_DECODE, every=2, start_s=300, size=GRID, episode_index=epi)
        got = str(meta["episode_id"])
        if not got.startswith(pin):
            raise SystemExit(f"PIN MISMATCH {cid}: {got} -- RUN VOID")
        print(f"[{cid}] decoded {len(frames_all)} pin {got[:8]} ok")

        # FLOOR re-earn -- VOIDS otherwise (verify the PRODUCT)
        origins = gc.region_origins()
        tot = 0
        for fi in SAMPLED_FRAMES:
            q = gc.quantize(frames_all[fi], K_INCUMBENT)
            for (r0, c0) in origins:
                st = gc.field_stats(q[r0:r0 + REGION, c0:c0 + REGION],
                                    frames_all[fi][r0:r0 + REGION,
                                                   c0:c0 + REGION], tau=0)
                tot += st["n_enclosed_comps"]
        if tot != PUBLISHED_ENCLOSED[cid]:
            raise SystemExit(f"FLOOR MISMATCH {cid}: {tot} != "
                             f"{PUBLISHED_ENCLOSED[cid]} -- RUN VOID")
        print(f"[FLOOR/{cid}] enclosed comps = {tot} OK")

        wide = [np.asarray(frames_all[fi], float) for fi in FRAMES_WIDE]
        pcs = [pc_map(im) for im in wide]

        cor = {"meta_pin": got[:8], "floor_enclosed": tot}
        cor["value_flood_enc_median_ci"] = value_flood_baseline(wide, gc, rng)
        cor["sigma_mean"] = float(np.mean([cl.noise_sigma(im) for im in wide]))

        # --- SCALE sweep at the primary sparse density, fixed cap ---
        cor["scale_sweep"] = {}
        for sc in SCALE_LADDER:
            rows = []
            for im, pc in zip(wide, pcs):
                thr = float(np.quantile(pc, 1.0 - 0.05))
                rows.append(cl.mdl_close(im, pc > thr, scale=sc, dist_cap=20))
            cor["scale_sweep"][str(sc)] = summarise(rows, rng)
            print(f"[{cid}] scale={sc} done {loadavg()}")

        # --- CAP sweep at derived scale=1.0 (is the cap load-bearing?) ---
        cor["cap_sweep"] = {}
        for cap in CAP_LADDER:
            rows = []
            for im, pc in zip(wide, pcs):
                thr = float(np.quantile(pc, 1.0 - 0.05))
                rows.append(cl.mdl_close(im, pc > thr, scale=1.0, dist_cap=cap))
            cor["cap_sweep"][str(cap)] = summarise(rows, rng)
            print(f"[{cid}] cap={cap} done {loadavg()}")

        # --- DENSITY enumeration at scale=1.0, cap=20 ---
        cor["density_sweep"] = {}
        for d in DENSITY_LADDER:
            rows = []
            for im, pc in zip(wide, pcs):
                thr = float(np.quantile(pc, 1.0 - d))
                rows.append(cl.mdl_close(im, pc > thr, scale=1.0, dist_cap=20))
            cor["density_sweep"][f"{d:.2f}"] = summarise(rows, rng)
            print(f"[{cid}] density={d} done {loadavg()}")

        out["corpora"][cid] = cor
        print(f"[{cid}] complete, loadavg {loadavg()}")

    out["loadavg_end"] = loadavg()
    out["wall_s"] = round(time.time() - t0, 1)
    prov_after = ep.provenance_line()
    out["provenance_after"] = prov_after
    out["provenance_stable"] = bool(prov == prov_after)
    with open(os.path.join(ROOT, "results", "closure.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("provenance_stable:", out["provenance_stable"], "wall_s:", out["wall_s"])


if __name__ == "__main__":
    main()
