"""enclosure_grain_measure -- WHAT IS `bo_bgflood` ACTUALLY COMPUTING?

Pre-registration: VISION_ENCLOSURE_GRAIN_PREREG.md. Seeds 108000-108999.

The grouping-ceiling rung measured post-hoc that the value flood produces
86/94/111/83 components of >=60 cells and that 1.2%/44.7%/0.0%/41.0% of them
survive `bo_bgflood`'s enclosure test.  It named the predicate -- "does not
touch the WINDOW" read as "is a FIGURE" -- and declined to start from it.

This is the CHEAP DIAGNOSTIC, run before any derivation.  It characterises
what enclosure does at EVERY grain that exactly tiles the standing frame, and
compares the observed survival against a COMPUTED geometric null: the share of
translations at which a component's own bounding box could avoid the window
edge.  The null has no fitted parameter and no chosen constant.

Everything here is a READ-OUT.  No rule, no flag, no seed byte, no Rust moves.
The component field is computed in numpy and RECONCILED against the
substrate's own `glabel` partition and `bg` flag -- at MORE THAN ONE GRAIN,
because the claim spans grains -- before any number from it is believed.

UNIT OF ANALYSIS IS THE FRAME, not the tile.  Tiles cut from one frame share
that frame's content and are not independent (s4).  This is STRICTER than the
predecessor's tile bootstrap, against this rung's own numbers.

NOTHING IN THIS MODULE COMPARES A MEASURED QUANTITY AGAINST A LITERAL (s13).
The grain ladder is the DIVISOR ENUMERATION of the standing GRID; the size
bands are the dyadic enumeration; the T ladder is a curve reported in full.
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
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

# ---- declared seeds (PREREG s2.4) ---------------------------------------
SEED_SPECKLE_BASE = 108000        # 108000-108099, the 100 speckle fields
SEED_BOOT = 108100                # the bootstrap resampler

# G72 -- the peer / wellposed / containment / grouping-ceiling configuration.
GRID = 72
REGION_PUBLISHED = 18
K_INCUMBENT = 16
FRAMES_PUBLISHED = (0, 25, 50, 75, 100, 125, 149)
FRAMES_WIDE = tuple(range(0, 150, 5))            # 30 frames (PREREG s2.6)
N_DECODE = 160
N_SPECKLE = 100
BOOT_N = 10000

# THE GRAIN LADDER IS AN ENUMERATION (PREREG s2.1): every divisor of GRID.
GRAINS = tuple(L for L in range(1, GRID + 1) if GRID % L == 0)

# The size-band ladder is the DYADIC enumeration up to the field's own size.
BANDS = tuple((1 << i, 1 << (i + 1)) for i in range(0, 14))

# The T curve, reported in full; no single T is load-bearing.
T_CURVE = (5, 10, 20, 40, 60, 100, 150, 300)

# THE PUBLISHED FLOOR, ASSERTED IN-RUN.  The run VOIDS if it does not
# reproduce (the grouping-ceiling rung's s6.1: verifying the PRODUCER is not
# verifying the PRODUCT).
PUBLISHED_ENCLOSED = {"C1": 5047, "C2": 3978}

CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))

# Reconciling a field through the substrate is O(cells) nodes + a run_rules
# fixpoint.  Which grains were reached is REPORTED, never assumed.
RECONCILE_GRAINS = (4, 6, 8, 9, 12, 18, 24, 36)
RECONCILE_PER_GRAIN = 6


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GC = _mod("gc_measure", os.path.join(ROOT, "scripts",
                                     "grouping_ceiling_measure.py"))
quantize = GC.quantize
label = GC.label
substrate_partition = GC.substrate_partition
same_partition = GC.same_partition


def loadavg():
    return [round(x, 2) for x in os.getloadavg()]


# --------------------------------------------------------------------------
# THE ENCLOSURE READ-OUT + THE COMPUTED GEOMETRIC NULL
# --------------------------------------------------------------------------
def components(lab, n):
    """Per component: size, bbox height/width, and whether it touches the
    field border.  `touches border` IS `bo_bgflood`'s ground condition: bg
    floods from every `frame` cell along equal-value adjacency, so a
    component is ground iff it contains a border cell."""
    H, W = lab.shape
    flat = lab.ravel()
    counts = np.bincount(flat, minlength=n)
    rows = np.repeat(np.arange(H), W)
    cols = np.tile(np.arange(W), H)
    rmin = np.full(n, H, int)
    rmax = np.full(n, -1, int)
    cmin = np.full(n, W, int)
    cmax = np.full(n, -1, int)
    np.minimum.at(rmin, flat, rows)
    np.maximum.at(rmax, flat, rows)
    np.minimum.at(cmin, flat, cols)
    np.maximum.at(cmax, flat, cols)
    border = np.zeros(n, bool)
    border[lab[0, :]] = True
    border[lab[-1, :]] = True
    border[lab[:, 0]] = True
    border[lab[:, -1]] = True
    idx = np.flatnonzero(counts > 0)
    return {
        "labels": idx,
        "size": counts[idx].astype(int),
        "bh": (rmax[idx] - rmin[idx] + 1).astype(int),
        "bw": (cmax[idx] - cmin[idx] + 1).astype(int),
        "enclosed": ~border[idx],
    }


def null_survival(bh, bw, L):
    """PREREG s2.3 -- EXACT, not an approximation.

    A translation of a shape keeps it inside an LxL window iff its bbox
    origin lies in [0, L-h] x [0, L-w], and keeps it CLEAR OF THE BORDER iff
    the origin lies in [1, L-1-h] x [1, L-1-w].  "Clear of the border" is a
    statement about the BBOX ALONE, so counting bbox origins is exact.

    Returns the share of in-window translations that are clear of the border:
    the survival a component of that extent would have if its position
    carried no information.
    """
    bh = np.asarray(bh, int)
    bw = np.asarray(bw, int)
    inside = (L - bh + 1).astype(float) * (L - bw + 1).astype(float)
    clear = (np.maximum(0, L - 1 - bh).astype(float)
             * np.maximum(0, L - 1 - bw).astype(float))
    out = np.zeros(bh.shape, float)
    np.divide(clear, inside, out=out, where=inside > 0)
    return out


def tiles_of(q, L):
    h, w = q.shape
    return [q[r0:r0 + L, c0:c0 + L]
            for r0 in range(0, h - h % L, L)
            for c0 in range(0, w - w % L, L)]


def frame_record(q, L):
    """PREREG s2.2, pooled over every tile of ONE frame at grain L.  The
    FRAME is the unit of analysis; its tiles are not independent of it."""
    sizes, encs, nuls, bhs = [], [], [], []
    enc_cells = gnd_cells = ncell = 0
    n_ground = 0
    largest_gnd = 0
    for t in tiles_of(q, L):
        lab, n = label(np.asarray(t, int), 0)
        c = components(lab, n)
        sz, en = c["size"], c["enclosed"]
        sizes.append(sz)
        encs.append(en)
        bhs.append(np.maximum(c["bh"], c["bw"]))
        nuls.append(null_survival(c["bh"], c["bw"], L))
        ncell += int(lab.size)
        enc_cells += int(sz[en].sum())
        g = sz[~en]
        gnd_cells += int(g.sum())
        n_ground += int(g.size)
        largest_gnd = max(largest_gnd, int(g.max()) if g.size else 0)
    size = np.concatenate(sizes)
    enc = np.concatenate(encs)
    nul = np.concatenate(nuls)
    return {
        "L": L, "n_cells": ncell, "n_tiles": len(sizes),
        "size": size, "enclosed": enc, "null": nul,
        "enc_cell_frac": enc_cells / ncell,
        "ground_cell_frac": gnd_cells / ncell,
        "n_ground": n_ground,
        "largest_ground_frac": largest_gnd / (L * L),
        "cellsize_median": float(np.median(np.repeat(size, size))),
        "enc_cellsize_median": (float(np.median(np.repeat(size[enc],
                                                          size[enc])))
                                if enc.any() else None),
    }


def dist(a):
    a = np.asarray(a, float)
    if a.size == 0:
        return {"n": 0, "median": None, "mean": None, "p90": None, "max": None}
    return {"n": int(a.size), "median": float(np.median(a)),
            "mean": float(a.mean()), "p90": float(np.percentile(a, 90)),
            "max": float(a.max())}


def boot_ratio(obs_per_frame, nul_per_frame, rng):
    """Bootstrap the OBSERVED/NULL survival ratio over FRAMES (s4)."""
    o = np.asarray(obs_per_frame, float)
    u = np.asarray(nul_per_frame, float)
    if o.size == 0 or u.sum() <= 0:
        return None
    idx = rng.integers(0, o.size, size=(BOOT_N, o.size))
    on = o[idx].sum(axis=1)
    un = u[idx].sum(axis=1)
    keep = un > 0
    if not keep.any():
        return None
    reps = on[keep] / un[keep]
    return {"ratio": float(o.sum()) / float(u.sum()),
            "lo": float(np.percentile(reps, 2.5)),
            "hi": float(np.percentile(reps, 97.5)),
            "n_frames": int(o.size)}


def _med(xs):
    a = [x for x in xs if x is not None]
    return float(np.median(a)) if a else None


def aggregate(recs, rng):
    """Pool per-FRAME records at one grain into the PREREG s2.2 row."""
    if not recs:
        return None
    L = recs[0]["L"]
    size = np.concatenate([r["size"] for r in recs])
    enc = np.concatenate([r["enclosed"] for r in recs])
    nul = np.concatenate([r["null"] for r in recs])

    surv = {}
    for T in T_CURVE:
        m = size >= T
        surv[str(T)] = {
            "n": int(m.sum()),
            "enclosed": int((m & enc).sum()),
            "share": (float((m & enc).sum()) / int(m.sum())) if m.any()
            else None,
            "null_share": float(nul[m].mean()) if m.any() else None,
            "boot": boot_ratio(
                [float(r["enclosed"][r["size"] >= T].sum()) for r in recs],
                [float(r["null"][r["size"] >= T].sum()) for r in recs], rng)
            if m.any() else None}

    bands = []
    for lo, hi in BANDS:
        if lo > int(size.max(initial=0)):
            break
        m_all = (size >= lo) & (size < hi)
        bands.append({
            "lo": lo, "hi": hi, "n": int(m_all.sum()),
            "obs_share": float(enc[m_all].mean()) if m_all.any() else None,
            "null_share": float(nul[m_all].mean()) if m_all.any() else None,
            "boot": boot_ratio(
                [float(r["enclosed"][(r["size"] >= lo)
                                     & (r["size"] < hi)].sum())
                 for r in recs],
                [float(r["null"][(r["size"] >= lo)
                                 & (r["size"] < hi)].sum())
                 for r in recs], rng) if m_all.any() else None})

    return {
        "L": L, "n_frames": len(recs), "n_tiles_per_frame": recs[0]["n_tiles"],
        "n_comps": int(size.size), "n_enclosed": int(enc.sum()),
        "enc_cell_frac": float(np.mean([r["enc_cell_frac"] for r in recs])),
        "ground_cell_frac": float(np.mean([r["ground_cell_frac"]
                                           for r in recs])),
        "n_ground_per_frame": float(np.mean([r["n_ground"] for r in recs])),
        "largest_ground_frac": float(np.mean([r["largest_ground_frac"]
                                              for r in recs])),
        "all_sizes": dist(size),
        "enc_sizes": dist(size[enc]),
        "cellsize_median": float(np.median([r["cellsize_median"]
                                            for r in recs])),
        "enc_cellsize_median": _med([r["enc_cellsize_median"] for r in recs]),
        "survival_curve": surv,
        "bands": bands,
        "overall_obs": float(enc.mean()),
        "overall_null": float(nul.mean()),
    }


# --------------------------------------------------------------------------
# CONTROLS
# --------------------------------------------------------------------------
def null_brute(bh, bw, L):
    """The same quantity by EXPLICIT ENUMERATION of every translation: place
    the bbox at every origin that keeps it inside the window, and ask of each
    whether it touches the border ring.  No formula."""
    inside = clear = 0
    for r0 in range(0, L - bh + 1):
        for c0 in range(0, L - bw + 1):
            inside += 1
            if r0 > 0 and c0 > 0 and r0 + bh - 1 < L - 1 and c0 + bw - 1 < L - 1:
                clear += 1
    return (clear / inside) if inside else 0.0


def control_null_positive(log):
    """PREREG s4, RESTATED AGAINST MYSELF.

    My pre-registered criterion said the null must return 1.0 for a 1x1
    component in a large window.  THAT IS WRONG, and the instrument caught
    me: a 1x1 shape has L*L placements of which (L-2)^2 are clear, so the
    correct value is (L-2)^2/L^2 = 0.9452 at L=72, not 1.0.  A point can
    still land on the border ring.

    The honest control is STRICTER than the one I registered: the closed form
    must agree EXACTLY with an explicit enumeration of every translation, for
    every (bbox, window) pair in the enumerated ladders -- and must be 0.0
    for a shape that spans the window.  This makes the measure sharper
    against this rung, which s5 permits and s1 demands."""
    rows = []
    ok = True
    for L in GRAINS:
        for bh in range(1, L + 1):
            for bw in range(1, L + 1):
                f = float(null_survival([bh], [bw], L)[0])
                b = null_brute(bh, bw, L)
                if abs(f - b) > 0.0:
                    ok = False
                    rows.append({"L": L, "bh": bh, "bw": bw,
                                 "formula": f, "brute": b})
    big = GRAINS[-1]
    point = float(null_survival([1], [1], big)[0])
    span = float(null_survival([big], [big], big)[0])
    log(f"[ctrl-null] closed form vs BRUTE ENUMERATION over every (bbox, "
        f"window) in the ladders: {'EXACT AGREEMENT' if ok else rows[:3]}")
    log(f"[ctrl-null] L={big}: 1x1 -> {point:.6f} "
        f"(analytic (L-2)^2/L^2 = {((big - 2) ** 2) / (big * big):.6f});  "
        f"{big}x{big} -> {span:.4f}")
    return {"brute_agrees_everywhere": ok, "mismatches": rows[:20],
            "L": big, "point": point, "spanning": span,
            "analytic_point": ((big - 2) ** 2) / float(big * big),
            "PREREG_CRITERION_WAS_WRONG": True,
            "PASSES": bool(ok and span == 0.0)}


def control_ideal_disc(log):
    """PREREG s4 -- a genuine isolated disc CLEAR of the border must read
    ENCLOSED at every grain that can contain it, and must read GROUND when
    translated to touch the edge.  The instrument must see the structure it
    exists to see, AND see it vanish for the stated reason.

    The radius is the LARGEST that fits clear of the border at that grain --
    derived from the window's own geometry, not chosen."""
    rows = []
    for L in GRAINS:
        cy = cx = L // 2
        r = min(cy - 1, L - 2 - cy)
        if r < 1:
            rows.append({"L": L, "skipped": "no disc fits clear of the border"})
            continue
        yy, xx = np.mgrid[0:L, 0:L]
        centred = (((yy - cy) ** 2 + (xx - cx) ** 2) <= r * r).astype(int)
        n_in = int(centred.sum())
        lab, n = label(centred, 0)
        c = components(lab, n)
        enc_c = sorted(c["size"][c["enclosed"]].tolist())
        edged = (((yy - r) ** 2 + (xx - cx) ** 2) <= r * r).astype(int)
        lab2, n2 = label(edged, 0)
        c2 = components(lab2, n2)
        enc_e = sorted(c2["size"][c2["enclosed"]].tolist())
        rows.append({"L": L, "radius": r, "disc_cells": n_in,
                     "centred_enclosed": enc_c, "edge_enclosed": enc_e,
                     "SEES_IT": bool(enc_c == [n_in]),
                     "LOSES_IT_AT_EDGE": bool(n_in not in enc_e)})
        log(f"[ctrl-disc] L={L:2d} r={r:2d} disc={n_in:4d} "
            f"centred_enc={enc_c} edge_enc={enc_e}")
    live = [r for r in rows if "skipped" not in r]
    return {"rows": rows,
            "PASSES": bool(live and all(r["SEES_IT"] and r["LOSES_IT_AT_EDGE"]
                                        for r in live))}


def reconcile(frames, cid, log):
    """PREREG s2.5 -- the instrument against the GRAPH, at MORE THAN ONE
    GRAIN.  Any disagreement VOIDS the run."""
    out = []
    q = quantize(frames[FRAMES_PUBLISHED[0]], K_INCUMBENT)
    for L in RECONCILE_GRAINS:
        t0 = time.time()
        checked = ok_p = ok_e = 0
        for t in tiles_of(q, L)[:RECONCILE_PER_GRAIN]:
            glab, bg = substrate_partition([[int(v) for v in row]
                                            for row in t])
            mine, n = label(t, 0)
            checked += 1
            if same_partition(glab, mine):
                ok_p += 1
            c = components(mine, n)
            enc_labels = c["labels"][c["enclosed"]]
            my_enc = np.isin(mine, enc_labels)
            if np.array_equal(my_enc, bg < 0.5):
                ok_e += 1
        row = {"L": L, "checked": checked, "partition_agree": ok_p,
               "enclosed_agree": ok_e, "secs": round(time.time() - t0, 1),
               "loadavg": loadavg()}
        out.append(row)
        log(f"[M0/{cid}] L={L:2d}: partition {ok_p}/{checked}  enclosed "
            f"{ok_e}/{checked}  ({row['secs']}s, load {row['loadavg']})")
    return {"rows": out, "grains": list(RECONCILE_GRAINS),
            "PASSES": bool(out and all(r["partition_agree"] == r["checked"]
                                       == r["enclosed_agree"] and r["checked"]
                                       for r in out))}


def published_floor(frames, cid, log):
    """The published enclosed-component total, on THE SWEEP'S OWN CODE PATH.
    Raises rather than reports (s6.1)."""
    tot = 0
    for fi in FRAMES_PUBLISHED:
        q = quantize(frames[fi], K_INCUMBENT)
        for t in tiles_of(q, REGION_PUBLISHED):
            lab, n = label(t, 0)
            tot += int(components(lab, n)["enclosed"].sum())
    want = PUBLISHED_ENCLOSED[cid]
    log(f"[floor/{cid}] enclosed components at G72/REGION=18/k=16, 7 frames: "
        f"{tot} (published {want})")
    if tot != want:
        raise SystemExit(f"PUBLISHED FLOOR DID NOT REPRODUCE for {cid}: "
                         f"{tot} != {want} -- RUN VOID")
    return {"measured": tot, "published": want}


def xcheck_floor(frames, cid, log):
    """The grouping-ceiling rung's POST-HOC cross-check, re-earned across the
    grain change -- over the WHOLE T curve, so no single T is load-bearing.
    Its T=60 row is the one that reproduces the published 86/94/111/83."""
    out = {}
    for grain, L in (("tile", REGION_PUBLISHED), ("whole", GRID)):
        sizes, encs = [], []
        for fi in FRAMES_PUBLISHED:
            q = quantize(frames[fi], K_INCUMBENT)
            for t in tiles_of(q, L):
                lab, n = label(t, 0)
                c = components(lab, n)
                sizes.append(c["size"])
                encs.append(c["enclosed"])
        size = np.concatenate(sizes)
        enc = np.concatenate(encs)
        curve = {}
        for T in T_CURVE:
            m = size >= T
            curve[str(T)] = {"produced": int(m.sum()),
                             "enclosed": int((m & enc).sum()),
                             "share": (float((m & enc).sum()) / int(m.sum()))
                             if m.any() else None}
        out[grain] = curve
        log(f"[xcheck/{cid}/{grain}] " + "  ".join(
            f"T{T}:{curve[str(T)]['produced']}/{curve[str(T)]['enclosed']}"
            for T in T_CURVE))
    return out


# --------------------------------------------------------------------------
def main():
    t_start = time.time()
    logf = open(os.path.join(ROOT, "results", "enclosure_grain.log"), "w")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()

    prov = ep.provenance_line()
    log(prov)
    log(f"[load] at start: {loadavg()}")
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    rng = np.random.default_rng(SEED_BOOT)
    out = {"provenance": prov, "loadavg_start": loadavg(),
           "grains": list(GRAINS), "t_curve": list(T_CURVE),
           "frames_wide": list(FRAMES_WIDE), "n_speckle": N_SPECKLE,
           "controls": {}, "corpora": {}, "speckle": {}}

    out["controls"]["null_positive"] = control_null_positive(log)
    out["controls"]["ideal_disc"] = control_ideal_disc(log)

    vp = _mod("vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))

    for cid, epi, pin in CORPORA:
        frames, meta = vp.jellyfin_frames(N_DECODE, every=2, start_s=300,
                                          size=GRID, episode_index=epi)
        if not str(meta["episode_id"]).startswith(pin):
            raise SystemExit(f"PIN MISMATCH {cid} -- RUN VOID")
        log(f"=== {cid}  pin {pin} OK  load {loadavg()}")

        c = {"pin": pin}
        c["published_floor"] = published_floor(frames, cid, log)
        c["xcheck_floor"] = xcheck_floor(frames, cid, log)
        c["reconcile"] = reconcile(frames, cid, log)
        if not c["reconcile"]["PASSES"]:
            raise SystemExit(f"M0 RECONCILIATION FAILED for {cid} -- RUN VOID")

        qs = [quantize(frames[fi], K_INCUMBENT) for fi in FRAMES_WIDE]
        c["by_grain"] = {}
        for L in GRAINS:
            t0 = time.time()
            agg = aggregate([frame_record(q, L) for q in qs], rng)
            agg["secs"] = round(time.time() - t0, 1)
            agg["loadavg"] = loadavg()
            c["by_grain"][str(L)] = agg
            log(f"[{cid}] L={L:2d} frames={agg['n_frames']:3d} "
                f"comps={agg['n_comps']:7d} enc={agg['n_enclosed']:7d} "
                f"encfrac={agg['enc_cell_frac']:.4f} "
                f"obs={agg['overall_obs']:.4f} null={agg['overall_null']:.4f} "
                f"gnd/frame={agg['n_ground_per_frame']:8.1f} "
                f"lgnd={agg['largest_ground_frac']:.3f} "
                f"maxsz={agg['all_sizes']['max']:.0f} "
                f"({agg['secs']}s load {agg['loadavg']})")
        out["corpora"][cid] = c

    # ---- M3: THE SPECKLE ARM, re-earned AT EVERY GRAIN -------------------
    log(f"=== SPECKLE  seeds {SEED_SPECKLE_BASE}-"
        f"{SEED_SPECKLE_BASE + N_SPECKLE - 1}  load {loadavg()}")
    sp = [quantize(np.random.RandomState(SEED_SPECKLE_BASE + i)
                   .uniform(0.0, 255.0, (GRID, GRID)), K_INCUMBENT)
          for i in range(N_SPECKLE)]
    for L in GRAINS:
        agg = aggregate([frame_record(q, L) for q in sp], rng)
        agg["loadavg"] = loadavg()
        out["speckle"][str(L)] = agg
        log(f"[speckle] L={L:2d} frames={agg['n_frames']:3d} "
            f"comps={agg['n_comps']:7d} encfrac={agg['enc_cell_frac']:.4f} "
            f"obs={agg['overall_obs']:.4f} null={agg['overall_null']:.4f} "
            f"maxsz={agg['all_sizes']['max']:.0f}")

    out["loadavg_end"] = loadavg()
    out["secs_total"] = round(time.time() - t_start, 1)
    out["provenance_after"] = ep.provenance_line()
    log(f"[load] at end: {out['loadavg_end']}  total {out['secs_total']}s")
    log(f"[provenance after] {out['provenance_after']}")

    path = os.path.join(ROOT, "results", "enclosure_grain.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, default=lambda o: (
            o.tolist() if isinstance(o, np.ndarray) else float(o)))
    log(f"[written] {path}")
    logf.close()


if __name__ == "__main__":
    main()
