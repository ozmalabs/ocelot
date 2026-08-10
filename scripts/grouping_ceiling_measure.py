"""grouping_ceiling_measure -- CHARACTERISE THE COMPONENT FIELD. NO MECHANISM.

Pre-registration: VISION_GROUPING_CEILING_PREREG.md. Seeds 103000-103999.

The peer-competition rung established that minting is a SELECTION over enclosed
components and that the component field's median member is ONE CELL. Four rungs
worked downstream of that ceiling. This rung goes upstream and asks the prior
question, with NO mechanism: what shape is the component-size distribution
across the WHOLE family of value-admissibility relations, and is a few-and-large
regime anywhere in it?

Everything here is a READ-OUT. No rule, no flag, no seed byte, no Rust moves.
The component field is computed in numpy and RECONCILED against the substrate's
own `glabel` partition before any number from it is believed -- a diagnostic
must not be computed by the component it checks.

NOTHING IN THIS MODULE COMPARES A MEASURED QUANTITY AGAINST A LITERAL (s13).
The k and tau ladders are SWEEP AXES reported in full; the target sizes T are a
CURVE, so no single target is load-bearing.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into   # noqa: E402
from domains import border_ownership_world as bow            # noqa: E402

# ---- declared seeds (PREREG s7) -----------------------------------------
SEED_SPECKLE_BASE = 103000        # 103000-103099, the 100 speckle fields
SEED_GRADED = 103100              # graded-exemplar noise draws

# G72 -- the peer / wellposed / containment configuration, verbatim.
GRID = 72
REGION = 18
K_INCUMBENT = 16
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)
N_DECODE = 160
MAX_STEPS = 200

# ---- THE SWEEP AXES (PREREG s2.1). Reported in full; none is selected. ---
K_LADDER = (2, 3, 4, 6, 8, 11, 16, 23, 32, 45, 64)      # ~sqrt(2), 5 octaves
TAU_LADDER = (0, 1, 2, 3, 4, 6, 8)                       # chaining at k=16
TARGETS = (10, 20, 40, 60, 100, 150)                     # PREREG s2.2 curve

CORPORA = {
    "C1": {"what": "cartoon", "episode_index": 0, "pin": "08630d4b"},
    "C2": {"what": "live-action", "episode_index": 3, "pin": "119eca43"},
}

N_RECONCILE_TILES = 32          # M0: live tiles put through the substrate
BOOT_N = 10000                  # bootstrap resamples over tiles


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def quantize(frame, k):
    """The incumbent quantizer, reproduced exactly (per-frame min/max)."""
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return np.zeros(f.shape, int)
    return np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)


def region_origins(shape=(GRID, GRID), region=REGION):
    h, w = shape
    return [(r0, c0)
            for r0 in range(0, h - h % region, region)
            for c0 in range(0, w - w % region, region)]


# --------------------------------------------------------------------------
# THE COMPONENT FIELD -- computed here, reconciled against the graph in M0.
# --------------------------------------------------------------------------
def label(q, tau=0):
    """4-connected components of `q` where two adjacent cells are the SAME
    region iff |q[a]-q[b]| <= tau.

    tau=0 is the incumbent's exact-value admissibility, byte-for-byte: the
    seed's `Eq(m.val, R.val)` over the 4-neighbour edges wired by add_field.
    tau>0 is CHAINING: the relation is applied per EDGE, so a component's
    total value range is unbounded -- which is the quantity H2 measures.
    """
    q = np.asarray(q, int)
    H, W = q.shape
    lab = -np.ones((H, W), int)
    nxt = 0
    stack = []
    for r0 in range(H):
        for c0 in range(W):
            if lab[r0, c0] >= 0:
                continue
            lab[r0, c0] = nxt
            stack.append((r0, c0))
            while stack:
                r, c = stack.pop()
                v = q[r, c]
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= rr < H and 0 <= cc < W and lab[rr, cc] < 0:
                        if abs(int(q[rr, cc]) - int(v)) <= tau:
                            lab[rr, cc] = nxt
                            stack.append((rr, cc))
            nxt += 1
    return lab, nxt


def field_stats(q, raw, tau=0):
    """Every per-field statistic of PREREG s2, for one admissibility relation.

    `raw` is the UNQUANTIZED luminance, used only for `vrange` (H2's
    discriminator) -- it never enters the labelling.
    """
    lab, n = label(q, tau)
    H, W = lab.shape
    ncell = H * W
    flat = lab.ravel()
    counts = np.bincount(flat, minlength=n)
    sizes = counts[counts > 0]

    # ENCLOSED == a component containing no border cell. Equivalent to the
    # seed's bg flood: bg spreads from the frame along ADMISSIBLE adjacency,
    # so a component is ground iff it touches the frame.
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    enclosed_labs = [i for i in range(n) if counts[i] > 0 and i not in border]
    enc_sizes = [int(counts[i]) for i in enclosed_labs]

    # size-biased: for each CELL, the size of the component it lives in.
    # Reported BOTH over all cells (which the ground dominates once it
    # percolates -- that domination IS the degeneracy signal) and over the
    # ENCLOSED cells only (the figure side, what minting selects from).
    cellsize = counts[flat]
    enc_set = set(enclosed_labs)
    enc_mask = np.array([x in enc_set for x in flat])
    cellsize_enc = cellsize[enc_mask]

    rawf = np.asarray(raw, float).ravel()
    order = np.argsort(flat, kind="stable")
    lab_sorted, raw_sorted = flat[order], rawf[order]
    bounds = np.flatnonzero(np.diff(lab_sorted)) + 1
    vrange = [float(seg.max() - seg.min())
              for seg in np.split(raw_sorted, bounds)]

    touch_edge = sum(1 for i in range(n) if counts[i] > 0 and i in border)
    return {
        "n_cells": ncell,
        "n_comps": int(len(sizes)),
        "sizes": [int(x) for x in sizes],
        "enc_sizes": enc_sizes,
        "n_enclosed_comps": len(enc_sizes),
        "n_enclosed_cells": int(sum(enc_sizes)),
        "cellsize_median": float(np.median(cellsize)),
        "cellsize": [int(x) for x in cellsize],
        "cellsize_enc": [int(x) for x in cellsize_enc],
        "cellsize_enc_median": (float(np.median(cellsize_enc))
                                if cellsize_enc.size else None),
        "giant": float(sizes.max()) / ncell,
        "giant_cells": int(sizes.max()),
        "vrange": vrange,
        "n_touch_edge": touch_edge,
    }


def dist(xs):
    if len(xs) == 0:
        return {"n": 0, "median": None, "mean": None, "p90": None,
                "p99": None, "max": None}
    a = np.asarray(xs, float)
    return {"n": int(a.size), "median": float(np.median(a)),
            "mean": float(a.mean()), "p90": float(np.percentile(a, 90)),
            "p99": float(np.percentile(a, 99)), "max": float(a.max())}


def boot_ci(per_tile, rng):
    """Bootstrap the MEDIAN OVER TILES. Unit of analysis is the tile (s4)."""
    a = np.asarray([x for x in per_tile if x is not None], float)
    if a.size == 0:
        return {"n_tiles": 0, "median": None, "lo": None, "hi": None}
    idx = rng.integers(0, a.size, size=(BOOT_N, a.size))
    reps = np.median(a[idx], axis=1)
    return {"n_tiles": int(a.size), "median": float(np.median(a)),
            "lo": float(np.percentile(reps, 2.5)),
            "hi": float(np.percentile(reps, 97.5))}


# --------------------------------------------------------------------------
# M0 -- RECONCILIATION AGAINST THE GRAPH
# --------------------------------------------------------------------------
def substrate_partition(tile_vals):
    """Boot the standing seed on one tile and read its OWN component field."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    handle = bow.add_field(s, tile_vals)
    bow.set_flag(s, bown=1.0, bown_own=1.0, bown_wp=1.0, bown_nest=0.0)
    bow.tick(s, max_steps=MAX_STEPS)
    idx = handle["index"]
    H, W = handle["H"], handle["W"]
    glab = np.zeros((H, W), float)
    bg = np.zeros((H, W), float)
    for r in range(H):
        for c in range(W):
            at = s.node(idx[(r, c)])["attrs"]
            glab[r, c] = float(at.get("glabel", 0.0))
            bg[r, c] = float(at.get("bg", 0.0))
    return glab, bg


def same_partition(a, b):
    """Do two labellings induce the SAME partition (label names irrelevant)?"""
    a, b = np.asarray(a).ravel(), np.asarray(b).ravel()
    fwd, rev = {}, {}
    for x, y in zip(a.tolist(), b.tolist()):
        if fwd.setdefault(x, y) != y or rev.setdefault(y, x) != x:
            return False
    return True


def reconcile(frames, log, cid):
    """PREREG M0. Any disagreement VOIDS the run."""
    origins = region_origins()
    checked = ok_part = ok_enc = 0
    for fi in SAMPLED_FRAMES[:2]:
        q = quantize(frames[fi], K_INCUMBENT)
        for (r0, c0) in origins:
            if checked >= N_RECONCILE_TILES:
                break
            t = q[r0:r0 + REGION, c0:c0 + REGION]
            glab, bg = substrate_partition([[int(v) for v in row]
                                            for row in t])
            mine, n = label(t, 0)
            checked += 1
            if same_partition(glab, mine):
                ok_part += 1
            # ENCLOSED agreement: my "touches no border" vs the seed's bg flag
            border = set(mine[0, :]) | set(mine[-1, :]) | \
                set(mine[:, 0]) | set(mine[:, -1])
            my_enc = np.array([[mine[r, c] not in border
                                for c in range(REGION)]
                               for r in range(REGION)])
            if np.array_equal(my_enc, bg < 0.5):
                ok_enc += 1
    log(f"[M0/{cid}] partition {ok_part}/{checked}  enclosed {ok_enc}/{checked}")
    return {"tiles_checked": checked, "partition_agree": ok_part,
            "enclosed_agree": ok_enc,
            "PASSES": bool(ok_part == checked == ok_enc and checked > 0)}


# --------------------------------------------------------------------------
# CONTROLS 2 + 3 -- the ideal exemplar and the graded exemplar
# --------------------------------------------------------------------------
def disc_mask(T):
    """Offsets of the ~T-cell disc; the ACTUAL count is reported, never
    assumed equal to T."""
    r = np.sqrt(T / np.pi)
    rr = int(np.ceil(r))
    offs = [(dy, dx) for dy in range(-rr, rr + 1) for dx in range(-rr, rr + 1)
            if dy * dy + dx * dx <= r * r]
    return offs


def ideal_exemplar(T, contrast, noise_amp, rng):
    """A genuine T-cell region of one value on a ground of another, with
    internal noise of amplitude `noise_amp` (control 3's graded arm).
    Returns the RAW field; the caller quantizes it as the pipeline does."""
    offs = disc_mask(T)
    fld = np.zeros((REGION, REGION), float)
    cy = cx = REGION // 2
    for dy, dx in offs:
        y, x = cy + dy, cx + dx
        if 0 <= y < REGION and 0 <= x < REGION:
            fld[y, x] = contrast
    n_in = int((fld > 0).sum())
    if noise_amp > 0:
        fld = fld + rng.uniform(-noise_amp / 2.0, noise_amp / 2.0,
                                fld.shape)
    return fld, n_in


def controls(log):
    out = {}
    rng = np.random.default_rng(SEED_GRADED)

    # --- CONTROL 2: the IDEAL exemplar. The instrument must SEE it. -------
    ideal = []
    for T in TARGETS:
        fld, n_in = ideal_exemplar(T, 255.0, 0.0, rng)
        plateau = []
        for k in K_LADDER:
            st = field_stats(quantize(fld, k), fld, 0)
            enc = st["enc_sizes"]
            plateau.append({"k": k, "n_enclosed": len(enc),
                            "max_enclosed": max(enc, default=0),
                            "finds_it": bool(len(enc) == 1
                                             and max(enc, default=0) == n_in)})
        ideal.append({"T": T, "disc_cells": n_in, "sweep": plateau,
                      "k_finding_it": [p["k"] for p in plateau
                                       if p["finds_it"]]})
        log(f"[ctrl2/T={T}] disc={n_in} cells; found exactly at k="
            f"{[p['k'] for p in plateau if p['finds_it']]}")
    out["control2_ideal"] = ideal

    # --- CONTROL 3: the GRADED exemplar -- the instrument's own units -----
    # Internal noise rises against a FIXED boundary contrast. Where the
    # plateau dies is the resolving limit, in spread/contrast units. M5
    # measures natural frames in exactly these units.
    graded = []
    contrast = 255.0
    # The pre-registered ladder, PLUS a POST-HOC refinement (marked as such in
    # the results): the pre-registered rungs straddled the analytic limit --
    # a disc survives only while its internal spread fits inside ONE
    # quantizer bin, i.e. ratio < 1/k -- and could not resolve it. The
    # refinement makes the control MORE informative about my own claim; it
    # rescues nothing (s5).
    PREREG_LADDER = (0.0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
    POSTHOC_REFINE = (0.015625, 0.03125, 0.046875, 0.0625, 0.09375)
    for ratio in tuple(sorted(PREREG_LADDER + POSTHOC_REFINE)):
        noise = ratio * contrast
        hit = 0
        trials = 20
        for _ in range(trials):
            fld, n_in = ideal_exemplar(60, contrast, noise, rng)
            st = field_stats(quantize(fld, K_INCUMBENT), fld, 0)
            enc = st["enc_sizes"]
            if max(enc, default=0) >= n_in:
                hit += 1
        graded.append({"spread_over_contrast": ratio, "trials": trials,
                       "recovered": hit, "rate": hit / trials,
                       "prereg": ratio in PREREG_LADDER})
        log(f"[ctrl3] spread/contrast={ratio:.3f} recovered {hit}/{trials}")
    out["control3_graded"] = graded
    return out


# --------------------------------------------------------------------------
# THE SWEEP (M1/M2/M3) over a set of fields
# --------------------------------------------------------------------------
def sweep_fields(make_fields, n_fields, rng, log, tag):
    """`make_fields(k)` yields (q, raw) pairs for ONE admissibility level.

    IT IS A CALLBACK AND NOT A LIST OF RAWS FOR A LOAD-BEARING REASON,
    FOUND BY MEASUREMENT: the pipeline quantizes PER FRAME (min/max over the
    whole 72x72 frame) and THEN cuts tiles. Quantizing each 18x18 tile against
    its OWN min/max is a different -- and more permissive -- representation,
    and it inflated the C1 enclosed-component count 5047 -> 6331 in this
    script's first version. The M0 reconciliation used the correct per-frame
    path and therefore PASSED while the sweep used the wrong one; the caller
    now owns the quantization so both paths are the same path.
    """
    arms = [("BIN", k, 0) for k in K_LADDER] + \
           [("CHAIN", K_INCUMBENT, t) for t in TAU_LADDER]
    rows = []
    for mode, k, tau in arms:
        per_tile_cellsize, per_tile_giant, per_tile_cs_enc = [], [], []
        sizes, enc_sizes, vranges, cellsizes = [], [], [], []
        cellsizes_enc = []
        n_comps, touch = [], []
        for q, raw in make_fields(k):
            st = field_stats(q, raw, tau)
            per_tile_cellsize.append(st["cellsize_median"])
            per_tile_cs_enc.append(st["cellsize_enc_median"])
            per_tile_giant.append(st["giant"])
            sizes.extend(st["sizes"])
            enc_sizes.extend(st["enc_sizes"])
            vranges.extend(st["vrange"])
            cellsizes.extend(st["cellsize"])
            cellsizes_enc.extend(st["cellsize_enc"])
            n_comps.append(st["n_comps"])
            touch.append(st["n_touch_edge"])
        row = {
            "mode": mode, "k": k, "tau": tau,
            "n_fields": n_fields,
            "sizes": dist(sizes),
            "enc_sizes": dist(enc_sizes),
            "cellsize": dist(cellsizes),
            "cellsize_enc": dist(cellsizes_enc),
            "cellsize_enc_per_tile": boot_ci(per_tile_cs_enc, rng),
            "cellsize_per_tile": boot_ci(per_tile_cellsize, rng),
            "giant_per_tile": boot_ci(per_tile_giant, rng),
            "n_comps": dist(n_comps),
            "vrange": dist(vranges),
            "n_touch_edge": dist(touch),
            "frac_cells_in_ge_T": {
                str(T): float(np.mean(np.asarray(cellsizes) >= T))
                for T in TARGETS},
            "frac_enc_cells_in_ge_T": {
                str(T): (float(np.mean(np.asarray(cellsizes_enc) >= T))
                         if cellsizes_enc else None)
                for T in TARGETS},
            "size_hist": {str(a): int(b) for a, b in
                          sorted(Counter(sizes).items())[:40]},
        }
        rows.append(row)
        log(f"  [{tag}|{mode} k={k} tau={tau}] comps/f={row['n_comps']['mean']:.1f} "
            f"size med={row['sizes']['median']} max={row['sizes']['max']} | "
            f"CELLSIZE med={row['cellsize']['median']} "
            f"enc_med={row['cellsize_enc']['median']} | "
            f"giant={row['giant_per_tile']['median']:.4f} "
            f"[{row['giant_per_tile']['lo']:.4f},{row['giant_per_tile']['hi']:.4f}] | "
            f"vrange med={row['vrange']['median']}")
    return rows


# --------------------------------------------------------------------------
# M5 -- THE MATERIAL
# --------------------------------------------------------------------------
def material(frames, log, cid):
    """For each disc of ~T cells: the RAW luminance spread inside it, against
    the adjacent-pair step distribution of the same frame."""
    out = []
    for T in TARGETS:
        offs = disc_mask(T)
        rr = max(abs(d) for o in offs for d in o)
        spreads, kreqs, ratios = [], [], []
        for fi in SAMPLED_FRAMES:
            f = np.asarray(frames[fi], float)
            H, W = f.shape
            rng_val = float(f.max() - f.min())
            dh = np.abs(np.diff(f, axis=0)).ravel()
            dw = np.abs(np.diff(f, axis=1)).ravel()
            steps = np.concatenate([dh, dw])
            p95 = float(np.percentile(steps, 95))
            ys = np.arange(rr, H - rr, 2)
            xs = np.arange(rr, W - rr, 2)
            YY, XX = np.meshgrid(ys, xs, indexing="ij")
            stack = np.stack([f[YY + dy, XX + dx] for dy, dx in offs], axis=0)
            sp = (stack.max(axis=0) - stack.min(axis=0)).ravel()
            spreads.extend(sp.tolist())
            ratios.extend((sp / p95 if p95 > 0
                           else np.full(sp.shape, np.nan)).tolist())
            with np.errstate(divide="ignore"):
                kreqs.extend(np.where(sp > 0, rng_val / np.where(sp > 0, sp, 1),
                                      np.inf).tolist())
        finite = [x for x in kreqs if np.isfinite(x)]
        row = {"T": T, "disc_cells": len(offs),
               "spread": dist(spreads),
               "spread_over_step_p95": dist(ratios),
               "frac_ratio_gt_1": float(np.mean(np.asarray(ratios) > 1.0)),
               "k_required": dist(finite),
               "n_infinite_kreq": len(kreqs) - len(finite)}
        out.append(row)
        log(f"[M5/{cid}/T={T}] disc={len(offs)} spread med={row['spread']['median']:.2f} "
            f"ratio med={row['spread_over_step_p95']['median']:.3f} "
            f"frac>1={row['frac_ratio_gt_1']:.3f} "
            f"k_req med={row['k_required']['median']:.2f}")
    return out


def main():
    t0 = time.time()
    prov = ep.provenance_line()
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    logf = open(os.path.join(ROOT, "results", "grouping_ceiling.log"), "w")

    def log(m):
        print(m, flush=True)
        logf.write(m + "\n")
        logf.flush()

    log("== PROVENANCE (printed from INSIDE the measuring process) ==")
    log(prov)
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    rng = np.random.default_rng(SEED_SPECKLE_BASE)
    out = {"provenance": prov, "prereg": "VISION_GROUPING_CEILING_PREREG.md",
           "seed_block": [103000, 103999],
           "config": {"GRID": GRID, "REGION": REGION,
                      "k_incumbent": K_INCUMBENT,
                      "K_LADDER": list(K_LADDER), "TAU_LADDER": list(TAU_LADDER),
                      "TARGETS": list(TARGETS),
                      "sampled_frames": list(SAMPLED_FRAMES)}}

    # ---- CONTROLS 2 + 3 run BEFORE any natural-frame number -------------
    out["controls"] = controls(log)
    if not any(e["k_finding_it"] for e in out["controls"]["control2_ideal"]):
        raise SystemExit("IDEAL EXEMPLAR NOT FOUND AT ANY k -- INSTRUMENT BLIND")

    # ---- CONTROL 1: the random-input floor, same sweep -------------------
    speckle = [np.random.RandomState(SEED_SPECKLE_BASE + i)
               .randint(0, 256, (REGION, REGION)).astype(float)
               for i in range(100)]
    log("== CONTROL 1: iid uniform speckle, identical sweep ==")
    out["speckle_sweep"] = sweep_fields(
        lambda k: [(quantize(f, k), f) for f in speckle],
        len(speckle), rng, log, "speckle")

    vp = _vp()
    origins = region_origins()
    out["corpora"] = {}
    for cid in ("C1", "C2"):
        spec = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            N_DECODE, every=2, start_s=300, size=GRID,
            episode_index=spec["episode_index"])
        got = str(meta["episode_id"])
        if not got.startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid}: {got} -- RUN VOID")
        log(f"[{cid}] {spec['what']} decoded {len(frames)} @ {GRID}x{GRID} "
            f"pin {got[:8]} ok")

        rec = reconcile(frames, log, cid)
        if not rec["PASSES"]:
            raise SystemExit(f"M0 RECONCILIATION FAILED ({cid}) -- RUN VOID")

        wholes = [np.asarray(frames[fi], float) for fi in SAMPLED_FRAMES]

        def tiles_at(k, _wholes=wholes):
            """QUANTIZE THE FRAME, THEN CUT -- the pipeline's own order."""
            out_ = []
            for f in _wholes:
                q = quantize(f, k)
                for (r0, c0) in origins:
                    out_.append((q[r0:r0 + REGION, c0:c0 + REGION],
                                 f[r0:r0 + REGION, c0:c0 + REGION]))
            return out_

        n_tiles = len(wholes) * len(origins)
        log(f"== {cid}: TILED sweep, {n_tiles} tiles ==")
        tiled = sweep_fields(tiles_at, n_tiles, rng, log, cid)

        # M4 -- THE APERTURE: identical computation, whole frame
        log(f"== {cid}: WHOLE-FRAME sweep (M4 aperture), {len(wholes)} frames ==")
        whole = sweep_fields(
            lambda k, _w=wholes: [(quantize(f, k), f) for f in _w],
            len(wholes), rng, log, cid + "/whole")

        # ---- THE PUBLISHED FLOOR, RE-EARNED ON THE SWEEP'S OWN PATH ------
        # The peer-competition rung's committed enclosed-component totals.
        # These are PRIOR PUBLISHED RESULTS being reproduced, not tuned
        # parameters (s13): the run VOIDS if the sweep's incumbent arm does
        # not reproduce them. The first version of this script passed M0 and
        # still missed this, because M0 exercised a different quantization
        # path than the sweep -- verify on the PRODUCT, not the producer.
        PUBLISHED_ENCLOSED = {"C1": 5047, "C2": 3978}
        inc = [r for r in tiled if r["mode"] == "BIN"
               and r["k"] == K_INCUMBENT][0]
        got = inc["enc_sizes"]["n"]
        log(f"[FLOOR/{cid}] enclosed comps at BIN k={K_INCUMBENT}: {got} "
            f"(peer rung published {PUBLISHED_ENCLOSED[cid]})")
        if got != PUBLISHED_ENCLOSED[cid]:
            raise SystemExit(f"FLOOR NOT RE-EARNED ({cid}): {got} != "
                             f"{PUBLISHED_ENCLOSED[cid]} -- RUN VOID")

        out["corpora"][cid] = {
            "floor_enclosed_components": {
                "measured": got, "published": PUBLISHED_ENCLOSED[cid]},
            "what": spec["what"], "episode_id": got,
            "M0_reconcile": rec,
            "M1_M2_M3_tiled": tiled,
            "M4_whole_frame": whole,
            "M5_material": material(frames, log, cid),
        }

    out["elapsed_s"] = time.time() - t0
    path = os.path.join(ROOT, "results", "grouping_ceiling.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"[written] {path}  ({out['elapsed_s']:.1f}s)")


if __name__ == "__main__":
    main()
