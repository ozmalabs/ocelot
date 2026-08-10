"""salience_rescore_analyse — the pre-registered analysis of
VISION_SALIENCE_RESCORE_PREREG.md.

Mechanical: reads the preserved per-trial rows and the salience field, applies
the pre-registered stratification and verdict rule, and writes the numbers out.
No decision about the agent; this is measurement over stored results.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

SEED = 58000            # this rung's block: bootstrap RNG only
N_BOOT = 10_000
N_BASE = 50
DELTAS = (1, 5, 25)
COMPARATORS = ("Q0", "Q1", "Q2")
GRID_N = 4              # 4x4 region grid


# --------------------------------------------------------------------------- #
#  Loading
# --------------------------------------------------------------------------- #
def load_rows(rows_dir, cid, cmp_name):
    with open(os.path.join(rows_dir,
                           f"invariant_comparator_rows_{cid}_{cmp_name}.json")) as fh:
        return json.load(fh)


def outcome(r):
    if not r["true_is_max"]:
        return "MISID"
    if r["said_idx"] != r["truth"]:
        return "TIEBREAK"
    return "CORRECT"


def terciles(values):
    """Pre-registered 5/6/5 within-frame split by rank; ties by region index.

    `values` is indexed by region index. Returns a list of 'LOW'/'MID'/'HIGH'.
    """
    order = sorted(range(len(values)), key=lambda i: (values[i], i))
    band = {}
    for rank, i in enumerate(order):
        band[i] = "LOW" if rank < 5 else ("MID" if rank < 11 else "HIGH")
    return [band[i] for i in range(len(values))]


# --------------------------------------------------------------------------- #
#  Cluster bootstrap over base frames
# --------------------------------------------------------------------------- #
def cluster_bootstrap(per_base, stat, n_boot=N_BOOT, seed=SEED):
    """`per_base` maps base -> payload; `stat` maps a list of payloads -> float
    (or None when undefined). Returns (point, lo, hi, n_valid_draws)."""
    bases = sorted(per_base)
    point = stat([per_base[b] for b in bases])
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(bases), len(bases))
        v = stat([per_base[bases[i]] for i in pick])
        if v is not None and np.isfinite(v):
            draws.append(v)
    if not draws:
        return point, None, None, 0
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi), len(draws)


def band_rate_stat(band_hi, band_lo):
    """MISID rate in HIGH minus MISID rate in LOW, over a list of per-base
    payloads. Each payload is a dict band -> (n_misid, n_total)."""
    def f(payloads):
        h = [0, 0]
        l = [0, 0]
        for p in payloads:
            a = p.get(band_hi, (0, 0))
            b = p.get(band_lo, (0, 0))
            h[0] += a[0]; h[1] += a[1]
            l[0] += b[0]; l[1] += b[1]
        if h[1] == 0 or l[1] == 0:
            return None
        return h[0] / h[1] - l[0] / l[1]
    return f


def rate_stat(band):
    def f(payloads):
        k = n = 0
        for p in payloads:
            a = p.get(band, (0, 0))
            k += a[0]; n += a[1]
        return None if n == 0 else k / n
    return f


# --------------------------------------------------------------------------- #
#  Core: build per-base band payloads for one (corpus, cmp, delta, label, key)
# --------------------------------------------------------------------------- #
def payloads(rows, sal_by_base, label, *, cmps, deltas):
    """Returns base -> {band: (n_label, n_total)} over the selected A1 rows."""
    out = {b: {} for b in range(N_BASE)}
    for cmp_name, rs in rows.items():
        if cmp_name not in cmps:
            continue
        for r in rs:
            parts = r["tag"].split("|")
            if parts[0] != "A1":
                continue
            d = int(parts[1][1:])
            if d not in deltas:
                continue
            b = r["base"]
            band = sal_by_base[b][r["truth"]]
            cell = out[b].setdefault(band, [0, 0])
            cell[1] += 1
            if outcome(r) == label:
                cell[0] += 1
    return {b: {k: tuple(v) for k, v in d.items()} for b, d in out.items()}


# --------------------------------------------------------------------------- #
#  Adjacency (secondary), with a GEOMETRY-derived chance baseline
# --------------------------------------------------------------------------- #
def rc(i):
    return i // GRID_N, i % GRID_N


def n4(i):
    r, c = rc(i)
    return sum(1 for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
               if 0 <= r + dr < GRID_N and 0 <= c + dc < GRID_N)


def n8(i):
    r, c = rc(i)
    return sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
               if (dr or dc) and 0 <= r + dr < GRID_N and 0 <= c + dc < GRID_N)


def cheb(i, j):
    (r1, c1), (r2, c2) = rc(i), rc(j)
    return max(abs(r1 - r2), abs(c1 - c2))


def mean_cheb_chance(i):
    return float(np.mean([cheb(i, j) for j in range(GRID_N * GRID_N) if j != i]))


def adjacency_payloads(rows, *, cmps, deltas):
    """base -> list of (is4, is8, cheb, chance4, chance8, cheb_chance) per MISID row."""
    out = {b: [] for b in range(N_BASE)}
    for cmp_name, rs in rows.items():
        if cmp_name not in cmps:
            continue
        for r in rs:
            parts = r["tag"].split("|")
            if parts[0] != "A1" or int(parts[1][1:]) not in deltas:
                continue
            if outcome(r) != "MISID":
                continue
            t, s = r["truth"], r["said_idx"]
            if s is None or s == t:
                continue
            out[r["base"]].append((
                1.0 if cheb(t, s) == 1 and abs(rc(t)[0] - rc(s)[0]) + abs(rc(t)[1] - rc(s)[1]) == 1 else 0.0,
                1.0 if cheb(t, s) == 1 else 0.0,
                float(cheb(t, s)),
                n4(t) / 15.0, n8(t) / 15.0, mean_cheb_chance(t)))
    return out


def adj_stat(idx, chance_idx):
    def f(payloads_list):
        obs, ch, n = 0.0, 0.0, 0
        for lst in payloads_list:
            for row in lst:
                obs += row[idx]; ch += row[chance_idx]; n += 1
        return None if n == 0 else (obs - ch) / n
    return f


def adj_raw(idx):
    def f(payloads_list):
        obs, n = 0.0, 0
        for lst in payloads_list:
            for row in lst:
                obs += row[idx]; n += 1
        return None if n == 0 else obs / n
    return f


# --------------------------------------------------------------------------- #
def main():
    rows_dir, field_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    field = json.load(open(field_path))
    result = {"seed": SEED, "n_boot": N_BOOT, "corpora": {}}

    # --- C3 d=0 negative control, from rows alone -------------------------- #
    ctrl = {}
    for cmp_name in ("Q0", "Q1", "Q2", "Q3", "R", "H"):
        p = os.path.join(rows_dir, f"invariant_comparator_rows_C3_{cmp_name}.json")
        if not os.path.exists(p):
            continue
        rs = json.load(open(p))
        sel = [r for r in rs if r["tag"].startswith("A1|axis|d0|")
               or r["tag"].startswith("A1|axis|0|")]
        if not sel:                       # tag spelling varies; fall back
            sel = [r for r in rs if r["tag"].startswith("A1|axis")
                   and r["tag"].split("|")[2] in ("d0", "0")]
        ctrl[cmp_name] = {"n": len(sel),
                          "misid": sum(1 for r in sel if not r["true_is_max"]),
                          "tiebreak": sum(1 for r in sel if r["true_is_max"]
                                          and r["said_idx"] != r["truth"])}
    result["C3_d0_control"] = ctrl

    for cid in ("C1", "C2"):
        rows = {c: load_rows(rows_dir, cid, c) for c in COMPARATORS}
        corp = {}
        for key in ("csal", "lsal"):
            for mode in ("rgb", "hpe"):
                if key == "lsal" and mode == "hpe":
                    continue
                fld = field["corpora"][cid][mode]
                sal_by_base = {row["base"]: terciles(row[key]) for row in fld}
                raw_by_base = {row["base"]: row[key] for row in fld}

                # instrument diagnostic: is the field degenerate?
                distinct = [len(set(raw_by_base[b])) for b in range(N_BASE)]
                spread = [max(raw_by_base[b]) - min(raw_by_base[b])
                          for b in range(N_BASE)]

                tag = f"{key}_{mode}"
                entry = {"distinct_values_per_frame_mean": float(np.mean(distinct)),
                         "distinct_values_per_frame_min": int(np.min(distinct)),
                         "frames_with_fewer_than_3_distinct":
                             int(sum(1 for d in distinct if d < 3)),
                         "within_frame_spread_mean": float(np.mean(spread)),
                         "cells": {}, "pooled": {}}

                for label in ("MISID", "TIEBREAK"):
                    # pooled over comparators and deltas
                    pl = payloads(rows, sal_by_base, label,
                                  cmps=COMPARATORS, deltas=DELTAS)
                    d, lo, hi, _ = cluster_bootstrap(pl, band_rate_stat("HIGH", "LOW"))
                    hi_r = cluster_bootstrap(pl, rate_stat("HIGH"))
                    mid_r = cluster_bootstrap(pl, rate_stat("MID"))
                    lo_r = cluster_bootstrap(pl, rate_stat("LOW"))
                    flat = cluster_bootstrap(
                        pl, lambda ps: (sum(v[0] for p in ps for v in p.values())
                                        / max(1, sum(v[1] for p in ps for v in p.values()))))
                    entry["pooled"][label] = {
                        "delta_sal": d, "ci": [lo, hi],
                        "HIGH": hi_r[:3], "MID": mid_r[:3], "LOW": lo_r[:3],
                        "flat": flat[:3]}
                    # per (comparator, delta) cell
                    for cmp_name in COMPARATORS:
                        for dd in DELTAS:
                            p2 = payloads(rows, sal_by_base, label,
                                          cmps=(cmp_name,), deltas=(dd,))
                            v, l2, h2, _ = cluster_bootstrap(
                                p2, band_rate_stat("HIGH", "LOW"))
                            f2 = cluster_bootstrap(
                                p2, lambda ps: (sum(x[0] for p in ps for x in p.values())
                                                / max(1, sum(x[1] for p in ps for x in p.values()))))
                            entry["cells"][f"{label}|{cmp_name}|d{dd}"] = {
                                "delta_sal": v, "ci": [l2, h2], "flat": f2[0],
                                "n_misid": sum(x[0] for p in p2.values() for x in p.values()),
                                "n": sum(x[1] for p in p2.values() for x in p.values())}

                # salience-weighted MISID rate (weights = within-frame csal,
                # normalised to mean 1) vs flat -- reported unconditionally so
                # it cannot be a post-hoc addition.
                wsum = {b: (np.mean(raw_by_base[b]) or 0.0) for b in range(N_BASE)}
                wpay = {b: [] for b in range(N_BASE)}
                for cmp_name, rs in rows.items():
                    for r in rs:
                        parts = r["tag"].split("|")
                        if parts[0] != "A1" or int(parts[1][1:]) not in DELTAS:
                            continue
                        b = r["base"]
                        m = wsum[b]
                        w = (raw_by_base[b][r["truth"]] / m) if m > 0 else 1.0
                        wpay[b].append((w, 1.0 if outcome(r) == "MISID" else 0.0))

                def wstat(ps):
                    num = den = 0.0
                    for lst in ps:
                        for w, y in lst:
                            num += w * y; den += w
                    return None if den == 0 else num / den
                wv, wlo, whi, _ = cluster_bootstrap(wpay, wstat)
                entry["salience_weighted_misid"] = {"value": wv, "ci": [wlo, whi]}

                corp[tag] = entry

        # --- adjacency secondary (independent of salience) ----------------- #
        ap = adjacency_payloads(rows, cmps=COMPARATORS, deltas=DELTAS)
        adj = {}
        for name, idx, cidx in (("adj4", 0, 3), ("adj8", 1, 4), ("cheb", 2, 5)):
            o = cluster_bootstrap(ap, adj_raw(idx))
            df = cluster_bootstrap(ap, adj_stat(idx, cidx))
            ch = cluster_bootstrap(ap, adj_raw(cidx))
            adj[name] = {"observed": o[:3], "chance": ch[0],
                         "diff": df[0], "diff_ci": [df[1], df[2]]}
        adj["n_misid_rows"] = sum(len(v) for v in ap.values())
        corp["adjacency"] = adj
        result["corpora"][cid] = corp

    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=1, default=float)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
