#!/usr/bin/env python3
"""THE TRUNCATED APERTURE — H3 instrumentation + H4 positional selection bias.

Pre-registration: `VISION_APERTURE_FIX_PREREG.md`, committed BEFORE this ran at
`f48ef9944fe9134e148e279185ebfd30ebabf8de`. Seeds 71040-71199.

Two measurements, both declared in advance:

  H3  Instrument the UNMODIFIED landed call paths and COUNT the windows whose
      shape is not (6,6). An enumeration, not an argument.
  H4  In the configuration where truncation IS reachable (24x24 source,
      pad=rho, d>0), measure what the truncation does to WHICH region is
      selected -- reported as four separate statistics (S1 score, S2 selection
      disagreement, S3 directional edge-vs-interior bias, S4 the blindness
      demonstration).

USAGE: PYTHONPATH=runners/dsl/python:. python scripts/aperture_fix_measure.py
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np                                    # noqa: E402

import domains.seed_registry                          # noqa: F401,E402
from domains import invariant_comparator_world as iw  # noqa: E402

SEED_BLOCK = 71000
RHO = 2                       # the measured knee; NOT swept (prereg §2 H4)
DISPLACEMENTS = (1, 2, 3, 4, 6)
N_SYNTH = 40                  # seeds 71100-71139
N_PHOTOS = 24
REGION, GRID = iw.REGION, iw.GRID
ORIGINS = iw.region_origins()
EDGE = {(r, c) for (r, c) in ORIGINS if r == GRID - REGION or c == GRID - REGION}
T975 = {23: 2.0687, 39: 2.0227}


def t_ci(xs, df=None):
    n = len(xs)
    if n < 2:
        return (float(xs[0]) if xs else 0.0, 0.0, 0.0)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    t = T975.get(df if df is not None else n - 1, 1.984)
    h = t * sd / math.sqrt(n)
    return (m, m - h, m + h)


# --------------------------------------------------------------------------- #
#  The FROZEN pre-fix window function -- verbatim as it stood at 64a9641b.
# --------------------------------------------------------------------------- #
def orbit_windows_PREFIX(qsrc_padded, origin, rho, region=REGION):
    r0, c0 = origin
    out = []
    for j, (dr, dc) in enumerate(iw.orbit_offsets(rho)):
        rr, cc = r0 + rho + dr, c0 + rho + dc
        out.append((j, qsrc_padded[rr:rr + region, cc:cc + region]))
    return out


def synth(seed):
    return np.asarray(np.random.RandomState(seed).randint(
        0, iw.K_LEVELS, (GRID, GRID)), int)


def photo_crops(n=N_PHOTOS):
    """The 24x24 CENTRE crop of each BSDS photo -- a real-image corpus at the
    geometry where the padding is the binding constraint."""
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    out, names = [], []
    for p in bsds_paths("train")[:n]:
        q = iw.quantize(np.asarray(Image.open(p).convert("L"), np.float32))
        h, w = q.shape
        ar, ac = (h - GRID) // 2, (w - GRID) // 2
        out.append(np.asarray(q[ar:ar + GRID, ac:ac + GRID], int))
        names.append(os.path.basename(p))
    return out, names


# --------------------------------------------------------------------------- #
#  H3 — instrument the LANDED call paths
# --------------------------------------------------------------------------- #
def run_h3(out):
    """Count short windows on every landed call site, at its OWN geometry, with
    the PRE-FIX arithmetic. A zero here means the defect was never reached."""
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    sites = {}

    # C3: the full photo, grid at the centre, d in {0,1,2,3,4,6} axis + diag.
    n_short, n_tot = 0, 0
    for p in bsds_paths("train")[:N_PHOTOS]:
        q = iw.quantize(np.asarray(Image.open(p).convert("L"), np.float32))
        h, w = q.shape
        ar, ac = (h - GRID) // 2, (w - GRID) // 2
        origins = [(ar + r, ac + c) for r, c in ORIGINS]
        for _cid, _enc, rho in iw_comparators():
            padded = iw.pad_edge(q, rho)
            for d in (0, 1, 2, 3, 4, 6):
                for (dr, dc) in ((0, d), (d, d)):
                    for (r0, c0) in origins:
                        for _j, t in orbit_windows_PREFIX(
                                padded, (r0 + dr, c0 + dc), rho):
                            n_tot += 1
                            n_short += int(t.shape != (REGION, REGION))
    sites["C3"] = {"n_windows": n_tot, "n_short": n_short,
                   "why": "source is the FULL 321x481 photo; the grid is taken "
                          "at the centre, so the photo's own ~150px margin -- "
                          "not pad_edge -- bounds every window",
                   "escapes_via": "source size, NOT the d=0 no-op"}

    # video: genuine 24x24 frames, every probe at offset (0,0).
    n_short, n_tot = 0, 0
    for s in range(71040, 71050):
        src = synth(s)
        for _cid, _enc, rho in iw_comparators():
            padded = iw.pad_edge(src, rho)
            for (r0, c0) in ORIGINS:
                for _j, t in orbit_windows_PREFIX(padded, (r0, c0), rho):
                    n_tot += 1
                    n_short += int(t.shape != (REGION, REGION))
    sites["video_C1_C2"] = {"n_windows": n_tot, "n_short": n_short,
                            "why": "24x24 frames -- the padding IS binding here "
                                   "-- but every probe is presented at offset "
                                   "(0,0)",
                            "escapes_via": "zero displacement"}

    # the migrated test file: 42x42 random source, grid centred (margin 9).
    n_short, n_tot = 0, 0
    for s in range(71050, 71055):
        src = np.asarray(np.random.RandomState(s).randint(
            0, iw.K_LEVELS, (42, 42)), int)
        ar = (42 - GRID) // 2
        origins = [(ar + r, ar + c) for r, c in ORIGINS]
        for rho in (0, 1, 2, 3):
            padded = iw.pad_edge(src, rho)
            for d in (0, 1, 2, 3):
                for (r0, c0) in origins:
                    for _j, t in orbit_windows_PREFIX(padded, (r0, c0 + d), rho):
                        n_tot += 1
                        n_short += int(t.shape != (REGION, REGION))
    sites["tests_migrated"] = {"n_windows": n_tot, "n_short": n_short,
                               "why": "42x42 source with the 24x24 grid centred "
                                      "(margin 9)",
                               "escapes_via": "source size"}

    # THE REACHABLE CASE, for contrast -- 24x24 source WITH displacement.
    n_short, n_tot = 0, 0
    for s in range(71055, 71065):
        src = synth(s)
        padded = iw.pad_edge(src, RHO)
        for d in DISPLACEMENTS:
            for (r0, c0) in ORIGINS:
                for _j, t in orbit_windows_PREFIX(padded, (r0, c0 + d), RHO):
                    n_tot += 1
                    n_short += int(t.shape != (REGION, REGION))
    sites["REACHABLE_24x24_with_displacement"] = {
        "n_windows": n_tot, "n_short": n_short,
        "why": "the configuration the defect actually bites in -- shown here so "
               "the three zeros above are known not to be an inert instrument",
        "escapes_via": None}
    out["h3"] = sites
    for k, v in sites.items():
        print(f"  [H3 {k}] {v['n_short']}/{v['n_windows']} short", flush=True)


def iw_comparators():
    return (("Q0", "cell", 0), ("Q1", "cell", 1), ("Q2", "cell", 2),
            ("Q3", "cell", 3))


# --------------------------------------------------------------------------- #
#  H4 — the positional selection bias
# --------------------------------------------------------------------------- #
def choice_from_orbit(orbit, codebook, encoder="cell"):
    """The 16-way choice as `max over (region, shift) of covered_count`. This is
    `iw.reference_choice`, which the incumbent's own gate asserts is EXACTLY
    what the graph computes (`icg_max == nn_score`, all rows)."""
    return iw.reference_choice(orbit, codebook, encoder)


def run_h4(out, corpus_name, sources, df):
    rows = []
    for si, src in enumerate(sources):
        codebook = [src[r:r + REGION, c:c + REGION] for r, c in ORIGINS]
        trunc_pad = iw.pad_edge(src, RHO)
        for d in DISPLACEMENTS:
            full_pad = iw.pad_edge(src, RHO + d)
            for i, (r0, c0) in enumerate(ORIGINS):
                o_t = orbit_windows_PREFIX(trunc_pad, (r0, c0 + d), RHO)
                o_f = iw.orbit_windows(full_pad, (r0, c0 + d), RHO,
                                       pad=RHO + d)
                ti, ts, tn = choice_from_orbit(o_t, codebook)
                fi, fs, fn = choice_from_orbit(o_f, codebook)
                n_cells_t = [int(np.asarray(t).size) for _j, t in o_t]
                rows.append({
                    "corpus": corpus_name, "src": si, "d": d, "truth": i,
                    "truth_is_edge": (r0, c0) in EDGE,
                    "trunc_idx": ti, "trunc_score": ts, "trunc_ties": tn,
                    "full_idx": fi, "full_score": fs, "full_ties": fn,
                    "trunc_idx_is_edge": ORIGINS[ti] in EDGE,
                    "full_idx_is_edge": ORIGINS[fi] in EDGE,
                    "min_cells_trunc": min(n_cells_t),
                    "mean_cells_trunc": float(np.mean(n_cells_t)),
                    "any_short": bool(min(n_cells_t) < REGION * REGION)})
        if si % 10 == 0:
            print(f"  [H4 {corpus_name}] source {si}/{len(sources)}", flush=True)

    # --- S1: score change --------------------------------------------------- #
    per_src_t = {}
    per_src_f = {}
    for r in rows:
        per_src_t.setdefault(r["src"], []).append(r["trunc_score"])
        per_src_f.setdefault(r["src"], []).append(r["full_score"])
    s1 = {
        "mean_score_trunc": float(np.mean([r["trunc_score"] for r in rows])),
        "mean_score_full": float(np.mean([r["full_score"] for r in rows])),
        "mean_cells_compared_trunc": float(
            np.mean([r["mean_cells_trunc"] for r in rows])),
        "mean_cells_compared_full": float(REGION * REGION),
        "frac_trials_with_a_short_window": float(
            np.mean([r["any_short"] for r in rows])),
    }
    diffs = [float(np.mean(per_src_f[s]) - np.mean(per_src_t[s]))
             for s in sorted(per_src_t)]
    m, lo, hi = t_ci(diffs, df)
    s1["paired_score_delta_full_minus_trunc"] = {
        "mean": m, "lo": lo, "hi": hi, "excludes_zero": bool(lo > 0.0),
        "n_units": len(diffs)}

    # --- S2: selection disagreement ----------------------------------------- #
    per_src_dis = {}
    for r in rows:
        per_src_dis.setdefault(r["src"], []).append(
            r["trunc_idx"] != r["full_idx"])
    dis = [sum(v) / len(v) for v in per_src_dis.values()]
    m2, lo2, hi2 = t_ci(dis, df)
    s2 = {"frac_trials_selection_differs": float(
              np.mean([r["trunc_idx"] != r["full_idx"] for r in rows])),
          "per_source_mean": m2, "lo": lo2, "hi": hi2, "n_units": len(dis)}

    # --- S3: DIRECTIONAL edge-vs-interior bias ------------------------------ #
    # P(TRUNC picks interior | FULL picked edge) - P(TRUNC picks edge | FULL
    # picked interior). Positive = the truncation drags the answer INWARD.
    a_num = [not r["trunc_idx_is_edge"] for r in rows if r["full_idx_is_edge"]]
    b_num = [r["trunc_idx_is_edge"] for r in rows if not r["full_idx_is_edge"]]
    per_src_bias = {}
    for r in rows:
        if r["full_idx_is_edge"]:
            per_src_bias.setdefault(r["src"], []).append(
                1.0 if not r["trunc_idx_is_edge"] else 0.0)
        else:
            per_src_bias.setdefault(r["src"], []).append(
                -1.0 if r["trunc_idx_is_edge"] else 0.0)
    bias = [float(np.mean(v)) for v in per_src_bias.values()]
    m3, lo3, hi3 = t_ci(bias, df)
    # accuracy split by whether the TRUE region is an edge one
    def acc(pred):
        per = {}
        for r in rows:
            if pred(r):
                per.setdefault(r["src"], []).append(r["trunc_idx"] == r["truth"])
        return {s: sum(v) / len(v) for s, v in per.items()}
    def accf(pred):
        per = {}
        for r in rows:
            if pred(r):
                per.setdefault(r["src"], []).append(r["full_idx"] == r["truth"])
        return {s: sum(v) / len(v) for s, v in per.items()}
    edge_t, edge_f = acc(lambda r: r["truth_is_edge"]), accf(lambda r: r["truth_is_edge"])
    int_t, int_f = acc(lambda r: not r["truth_is_edge"]), accf(lambda r: not r["truth_is_edge"])
    us = sorted(set(edge_t) & set(edge_f))
    em, elo, ehi = t_ci([edge_f[u] - edge_t[u] for u in us], df)
    us2 = sorted(set(int_t) & set(int_f))
    im, ilo, ihi = t_ci([int_f[u] - int_t[u] for u in us2], df)
    s3 = {
        "P_trunc_interior_given_full_edge": float(np.mean(a_num)) if a_num else None,
        "n_full_edge": len(a_num),
        "P_trunc_edge_given_full_interior": float(np.mean(b_num)) if b_num else None,
        "n_full_interior": len(b_num),
        "directional_bias_per_source": {"mean": m3, "lo": lo3, "hi": hi3,
                                        "excludes_zero": bool(lo3 > 0.0 or hi3 < 0.0),
                                        "n_units": len(bias)},
        "acc_edge_truth_trunc": float(np.mean(list(edge_t.values()))),
        "acc_edge_truth_full": float(np.mean(list(edge_f.values()))),
        "acc_edge_paired_full_minus_trunc": {"mean": em, "lo": elo, "hi": ehi,
                                             "excludes_zero": bool(elo > 0.0)},
        "acc_interior_truth_trunc": float(np.mean(list(int_t.values()))),
        "acc_interior_truth_full": float(np.mean(list(int_f.values()))),
        "acc_interior_paired_full_minus_trunc": {"mean": im, "lo": ilo, "hi": ihi,
                                                 "excludes_zero": bool(ilo > 0.0)},
    }

    # --- per-displacement breakdown ----------------------------------------- #
    by_d = {}
    for d in DISPLACEMENTS:
        sel = [r for r in rows if r["d"] == d]
        by_d[str(d)] = {
            "n": len(sel),
            "frac_short": float(np.mean([r["any_short"] for r in sel])),
            "acc_trunc": float(np.mean([r["trunc_idx"] == r["truth"] for r in sel])),
            "acc_full": float(np.mean([r["full_idx"] == r["truth"] for r in sel])),
            "sel_differs": float(np.mean([r["trunc_idx"] != r["full_idx"] for r in sel])),
            "mean_cells_trunc": float(np.mean([r["mean_cells_trunc"] for r in sel])),
        }

    out["h4"][corpus_name] = {"n_rows": len(rows), "n_sources": len(sources),
                              "S1_score": s1, "S2_selection": s2,
                              "S3_directional_bias": s3, "by_displacement": by_d}
    with open(os.path.join(ROOT, "results",
                           f"aperture_fix_rows_{corpus_name}.json"), "w") as fh:
        json.dump(rows, fh)
    print(f"  [H4 {corpus_name}] S2 selection differs "
          f"{s2['frac_trials_selection_differs']:.4f}; S3 bias {m3:+.4f} "
          f"[{lo3:+.4f},{hi3:+.4f}]", flush=True)


# --------------------------------------------------------------------------- #
#  S4 — THE BLINDNESS DEMONSTRATION, on the actual graph
# --------------------------------------------------------------------------- #
def run_s4(out):
    """The incumbent's central cross-check is `icg_max == nn_score`. Run the
    REAL substrate on TRUNCATED windows and show that check passes PERFECTLY on
    data the fix proves wrong -- so the defect is invisible to it, by
    construction and by measurement."""
    agree, n, accs = [], 0, []
    for s in range(71160, 71170):
        src = synth(s)
        codebook = [src[r:r + REGION, c:c + REGION] for r, c in ORIGINS]
        rng = random.Random(s)
        order = list(range(16))
        rng.shuffle(order)
        w = iw.InvComparatorWorld()
        w.hold(codebook, order, encoder="cell")
        trunc_pad = iw.pad_edge(src, RHO)
        for d in (2, 3, 4):
            for i, (r0, c0) in enumerate(ORIGINS):
                w.present(orbit_windows_PREFIX(trunc_pad, (r0, c0 + d), RHO),
                          truth=i, tag=f"t|d{d}|{i}")
        w.run()
        for r in w.read():
            n += 1
            agree.append(r["icg_max"] == r["nn_score"])
            accs.append(r["said_idx"] == r["truth"])
    out["s4_blindness"] = {
        "n_rows": n,
        "score_agreement_with_outside_reference": float(np.mean(agree)),
        "accuracy_on_truncated_windows": float(np.mean(accs)),
        "reading": "the graph and the outside reference agree on the score for "
                   "every truncated row -- the cross-check that guards this "
                   "rung is blind to the defect by construction, because both "
                   "sides count over the SAME short window",
    }
    print(f"  [S4] score agreement {np.mean(agree):.4f} on {n} truncated rows",
          flush=True)


def main():
    prov = provenance_line()
    out = {"provenance": prov,
           "prereg": "VISION_APERTURE_FIX_PREREG.md",
           "prereg_commit": "f48ef9944fe9134e148e279185ebfd30ebabf8de",
           "constants": {"seed_block": SEED_BLOCK, "rho": RHO,
                         "displacements": list(DISPLACEMENTS),
                         "n_synth": N_SYNTH, "n_photos": N_PHOTOS,
                         "region": REGION, "grid": GRID,
                         "n_edge_origins": len(EDGE),
                         "n_interior_origins": len(ORIGINS) - len(EDGE)},
           "h3": {}, "h4": {}}
    print(f"[provenance] {prov}", flush=True)
    t0 = time.time()
    run_h3(out)
    run_h4(out, "synthetic",
           [synth(s) for s in range(71100, 71100 + N_SYNTH)], 39)
    photos, names = photo_crops()
    out["corpora"] = {"bsds_centre_crops": names}
    run_h4(out, "bsds_crops", photos, 23)
    run_s4(out)
    out["elapsed_s"] = time.time() - t0
    path = os.path.join(ROOT, "results", "aperture_fix.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path} in {out['elapsed_s']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
