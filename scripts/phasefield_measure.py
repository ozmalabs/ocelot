"""phasefield_measure -- DOES READING THE FRAME AS A WAVEFIELD MOVE THE
OBJECT SIZE DISTRIBUTION OFF THE VALUE-FLOOD'S MEDIAN-1?

Pre-registration: VISION_PHASEFIELD_PREREG.md.  Seeds 114000-114999.

The object line converged (mint / value-family / peer-competition / aperture)
on ONE measured fact: the enclosed-component field is MEDIAN-1 at every grain
BEFORE ANY PREDICATE SEES IT, because equal-value connected components on
natural luminance are median-1 -- a region big enough to be an object is either
not equal-valued or it is the ground.  Every lever moved the COUNT and left the
MEDIAN at 1.

This rung changes the REPRESENTATION, not the selection.  A proto-object is a
region bounded by PHASE-CONGRUENT contours (Kovesi): features sit where the
Fourier components across scales are maximally IN PHASE -- constructive
interference, CONTRAST-INVARIANT -- and such a contour is EXTENDED by
construction where an equal-value boundary is not.  Regions = 4-connected
components of the NON-edge cells.  THE HEADLINE IS THE SIZE DISTRIBUTION.

CHARACTERISE, DO NOT BUILD.  This is numpy.  No Term, no seed, no Rust moves
unless the median moves first.

s13: the only 'threshold' that decides the verdict is (a) the Rayleigh NOISE
FLOOR, which falls out of the smallest-scale amplitude statistics, and (b)
OTSU on the PC map, which falls out of the histogram.  The edge-density ladder
is an ENUMERATION of the threshold axis, reported in full, none selected.  The
'1' the median is compared against is the value-flood's OWN reproduced median,
asserted in-run (5047/3978 floor voids the run otherwise) -- a measured
incumbent result, not a chosen constant.  nscale is enumerated {3,4,5}.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                       # noqa: E402

EXPECT_ENGINE = "e039d2eec2dd"

import phasefield_pc as pf                                          # noqa: E402

# ---- declared seeds (PREREG) --------------------------------------------
SEED_SPECKLE_BASE = 114000        # 114000-114099, 100 speckle fields (control)
SEED_BOOT = 114100                # the bootstrap resampler

GRID = 72
REGION = 18
K_INCUMBENT = 16
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)      # floor re-earn
FRAMES_WIDE = tuple(range(0, 150, 5))                 # 30 frames, unit=frame
N_DECODE = 160
N_SPECKLE = 100
BOOT_N = 10000

# THE PUBLISHED FLOOR, asserted in-run -- voids the run if not reproduced.
PUBLISHED_ENCLOSED = {"C1": 5047, "C2": 3978}
CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))

# nscale ENUMERATION (PREREG): 3 primary (72px frame, coarsest wavelength
# 3*2.1^2~=13px stays local), 4 and 5 for robustness (5 is ~frame-size,
# reported as degenerate-on-72px).
NSCALES = (3, 4, 5)

# The edge-DENSITY ladder: an enumeration of the threshold axis (fraction of
# cells labelled edge).  Reported in full; the VERDICT rides only on the two
# s13-clean operating points (noise-floor, Otsu).
DENSITY_LADDER = (0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)

PAD = 24   # reflect-pad margin to suppress the FFT wrap-around contour


def loadavg():
    return [round(x, 2) for x in os.getloadavg()]


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _gc():
    spec = importlib.util.spec_from_file_location(
        "gc", os.path.join(ROOT, "scripts", "grouping_ceiling_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------
# PC with reflect-pad (kills the FFT wrap contour), cropped back to the frame
# --------------------------------------------------------------------------
def pc_map(img, nscale, k_noise=pf.K_NOISE_DEFAULT):
    p = np.pad(img, PAD, mode="reflect")
    r = pf.phase_congruency(p, nscale=nscale, k_noise=k_noise)
    return r["pc"][PAD:PAD + img.shape[0], PAD:PAD + img.shape[1]], r


def le_map(img, nscale):
    p = np.pad(img, PAD, mode="reflect")
    e = pf.local_energy_magnitude(p, nscale=nscale)
    return e[PAD:PAD + img.shape[0], PAD:PAD + img.shape[1]]


# --------------------------------------------------------------------------
# SEGMENTATION: regions = 4-connected components of the non-edge cells.
# --------------------------------------------------------------------------
CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])   # 4-connectivity


def segment(strength, thr):
    """edges = strength > thr; regions = 4-conn components of ~edges.
    Returns (all_sizes, enclosed_sizes, n_regions, edge_frac)."""
    edges = strength > thr
    non = ~edges
    lab, n = ndimage.label(non, structure=CROSS)
    if n == 0:
        return np.array([], int), np.array([], int), 0, float(edges.mean())
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0                      # label 0 is the edge background
    labs = np.arange(len(sizes))
    live = sizes > 0
    # enclosed == region containing no frame-border cell
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    all_sizes = sizes[live & (labs != 0)]
    enc = np.array([sizes[i] for i in labs
                    if i != 0 and sizes[i] > 0 and i not in border], int)
    return all_sizes, enc, int(len(all_sizes)), float(edges.mean())


def thr_for_density(strength, d):
    """Threshold that labels a fraction d of cells as edge."""
    return float(np.quantile(strength, 1.0 - d))


def otsu(strength):
    """Otsu threshold over the strength map -- falls out of the histogram."""
    x = strength.ravel()
    hist, edges = np.histogram(x, bins=256)
    hist = hist.astype(float)
    w = np.cumsum(hist)
    tot = w[-1]
    if tot == 0:
        return 0.0
    centers = (edges[:-1] + edges[1:]) / 2
    mu = np.cumsum(hist * centers)
    muT = mu[-1]
    w1 = w
    w2 = tot - w
    with np.errstate(invalid="ignore", divide="ignore"):
        m1 = mu / np.where(w1 == 0, np.nan, w1)
        m2 = (muT - mu) / np.where(w2 == 0, np.nan, w2)
        sigb = w1 * w2 * (m1 - m2) ** 2
    sigb = np.nan_to_num(sigb)
    return float(centers[int(np.argmax(sigb))])


def dist(xs):
    if len(xs) == 0:
        return {"n": 0, "median": None, "mean": None, "max": None}
    a = np.asarray(xs, float)
    return {"n": int(a.size), "median": float(np.median(a)),
            "mean": float(a.mean()), "p90": float(np.percentile(a, 90)),
            "max": float(a.max())}


def boot_median_ci(per_frame, rng):
    """Bootstrap the MEDIAN over FRAMES (unit of analysis, PROTOCOL s4).
    per_frame is a list of per-frame medians."""
    a = np.asarray([x for x in per_frame if x is not None], float)
    if a.size == 0:
        return {"n_frames": 0, "median": None, "lo": None, "hi": None}
    idx = rng.integers(0, a.size, size=(BOOT_N, a.size))
    boot = np.median(a[idx], axis=1)
    return {"n_frames": int(a.size), "median": float(np.median(a)),
            "lo": float(np.percentile(boot, 2.5)),
            "hi": float(np.percentile(boot, 97.5))}


# --------------------------------------------------------------------------
# per-corpus measurement
# --------------------------------------------------------------------------
def measure_arm(frames, strength_fn, nscale, rng, k_noise=pf.K_NOISE_DEFAULT):
    """For one strength map (PC or LE) at one nscale: sweep the density ladder
    plus the two clean operating points, per frame."""
    per_op = {}          # op_name -> per-frame stats
    OPS = ["noise0", "otsu"] + [f"d{d:.2f}" for d in DENSITY_LADDER]
    for op in OPS:
        per_op[op] = {"all_med": [], "enc_med": [], "n_reg": [],
                      "enc_n": [], "edge_frac": [], "all_max": []}
    for f in frames:
        strength, _ = (strength_fn(f, nscale) if strength_fn is pc_map_wrap
                       else (strength_fn(f, nscale), None))
        # operating points
        thrs = {"noise0": 0.0, "otsu": otsu(strength)}
        for d in DENSITY_LADDER:
            thrs[f"d{d:.2f}"] = thr_for_density(strength, d)
        for op, thr in thrs.items():
            alls, enc, nreg, ef = segment(strength, thr)
            po = per_op[op]
            po["all_med"].append(float(np.median(alls)) if len(alls) else None)
            po["enc_med"].append(float(np.median(enc)) if len(enc) else None)
            po["n_reg"].append(nreg)
            po["enc_n"].append(int(len(enc)))
            po["edge_frac"].append(ef)
            po["all_max"].append(float(alls.max()) if len(alls) else 0.0)
    out = {}
    for op in OPS:
        po = per_op[op]
        out[op] = {
            "all_median_ci": boot_median_ci(po["all_med"], rng),
            "enc_median_ci": boot_median_ci(po["enc_med"], rng),
            "n_reg_mean": float(np.mean(po["n_reg"])),
            "enc_n_mean": float(np.mean(po["enc_n"])),
            "edge_frac_mean": float(np.mean(po["edge_frac"])),
            "all_max_mean": float(np.mean(po["all_max"])),
        }
    return out


def pc_map_wrap(img, nscale):
    return pc_map(img, nscale)


def value_flood_baseline(frames, gc):
    """Value-flood at L=72 (whole frame), k=16, per frame: all-comp and
    enclosed-comp medians + per-frame counts.  The incumbent baseline the PC
    median is compared against, on the IDENTICAL frames."""
    all_med, enc_med, ncomp, enc_ncomp = [], [], [], []
    for f in frames:
        q = gc.quantize(f, K_INCUMBENT)
        st = gc.field_stats(q, f, tau=0)
        sizes = st["sizes"]
        enc = st["enc_sizes"]
        all_med.append(float(np.median(sizes)) if sizes else None)
        enc_med.append(float(np.median(enc)) if enc else None)
        ncomp.append(st["n_comps"])
        enc_ncomp.append(st["n_enclosed_comps"])
    return {"all_med": all_med, "enc_med": enc_med,
            "ncomp_mean": float(np.mean(ncomp)),
            "enc_ncomp_mean": float(np.mean(enc_ncomp))}


def main():
    ep.engine_preamble()
    prov = ep.provenance_line()
    if EXPECT_ENGINE not in prov:
        raise SystemExit(f"WRONG ENGINE: {prov}")
    print(prov)

    t0 = time.time()
    la0 = loadavg()
    rng = np.random.default_rng(SEED_BOOT)
    gc = gc_mod = _gc()
    vp = _vp()

    out = {"provenance": prov, "expect_engine": EXPECT_ENGINE,
           "loadavg_start": la0, "nscales": list(NSCALES),
           "density_ladder": list(DENSITY_LADDER), "pad": PAD,
           "k_noise": pf.K_NOISE_DEFAULT}

    # ---- CONTROLS (dead-instrument arms fire) ----------------------------
    ctrl = {}
    uni = np.full((GRID, GRID), 128.0)
    pu, _ = pc_map(uni, 3)
    ctrl["uniform_pc_max"] = float(pu.max())          # expect 0.0
    yy, xx = np.mgrid[0:GRID, 0:GRID]
    disc = ((yy - 36) ** 2 + (xx - 36) ** 2 < 18 ** 2).astype(float) * 200 + 20
    pd, _ = pc_map(disc, 3)
    ad, ed, nrd, _ = segment(pd, otsu(pd))
    ctrl["disc_n_regions"] = int(nrd)                 # expect ~2 large
    ctrl["disc_region_max"] = float(ad.max()) if len(ad) else 0.0
    ctrl["disc_region_median"] = float(np.median(ad)) if len(ad) else None
    # speckle (structureless): seeds 114000-114099
    spk_reg, spk_med = [], []
    for i in range(N_SPECKLE):
        s = np.random.RandomState(SEED_SPECKLE_BASE + i).randint(
            0, 256, (GRID, GRID)).astype(float)
        ps, _ = pc_map(s, 3)
        a, e, nr, ef = segment(ps, otsu(ps))
        spk_reg.append(nr)
        spk_med.append(float(np.median(a)) if len(a) else None)
    ctrl["speckle_n_reg_mean"] = float(np.mean(spk_reg))
    ctrl["speckle_all_median_ci"] = boot_median_ci(spk_med, rng)
    out["controls"] = ctrl
    print("controls:", json.dumps(ctrl))

    # ---- corpora --------------------------------------------------------
    out["corpora"] = {}
    for cid, epi, pin in CORPORA:
        frames_all, meta = vp.jellyfin_frames(
            N_DECODE, every=2, start_s=300, size=GRID, episode_index=epi)
        got = str(meta["episode_id"])
        if not got.startswith(pin):
            raise SystemExit(f"PIN MISMATCH {cid}: {got} -- RUN VOID")
        print(f"[{cid}] decoded {len(frames_all)} pin {got[:8]} ok")

        # floor re-earn: 5047/3978 or the run VOIDS (verify the PRODUCT)
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
        print(f"[FLOOR/{cid}] enclosed comps = {tot} (published "
              f"{PUBLISHED_ENCLOSED[cid]}) OK")

        wide = [np.asarray(frames_all[fi], float) for fi in FRAMES_WIDE]

        cor = {"meta_pin": got[:8], "floor_enclosed": tot,
               "value_flood_L72": value_flood_baseline(wide, gc)}
        # value-flood median CIs on the same frames
        cor["value_flood_L72"]["all_median_ci"] = boot_median_ci(
            cor["value_flood_L72"]["all_med"], rng)
        cor["value_flood_L72"]["enc_median_ci"] = boot_median_ci(
            cor["value_flood_L72"]["enc_med"], rng)

        cor["pc"] = {}
        cor["le"] = {}
        for ns in NSCALES:
            print(f"[{cid}] PC nscale={ns} ...")
            cor["pc"][str(ns)] = measure_arm(wide, pc_map_wrap, ns, rng)
            cor["le"][str(ns)] = measure_arm(wide, le_map, ns, rng)
        out["corpora"][cid] = cor
        print(f"[{cid}] done, loadavg {loadavg()}")

    out["loadavg_end"] = loadavg()
    out["wall_s"] = round(time.time() - t0, 1)
    prov_after = ep.provenance_line()
    out["provenance_after"] = prov_after
    out["provenance_stable"] = bool(prov == prov_after)

    with open(os.path.join(ROOT, "results", "phasefield.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("provenance_stable:", out["provenance_stable"],
          "wall_s:", out["wall_s"])


if __name__ == "__main__":
    main()
