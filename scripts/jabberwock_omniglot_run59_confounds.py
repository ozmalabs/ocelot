"""OMNIGLOT RUN 59 -- THE CONFOUND-EXPLAINED-MISSES FALSIFIER (pure measurement, no minting).

Run 58 (aa95ed97) modelled the REALIZATION of a junction (does stroke-touch happen) and found the
signal WRITER-IDIOSYNCRATIC -- it separates in-distribution but does NOT transfer cross-writer. The
creator's reframe: the CLASS is the INTENT ("t" SHOULD cross); the realization may MISS; and the
intent->realization gap is caused by SPECIFIC, UNIVERSAL CONFOUNDS (physics/biomechanics/cognition),
not by writer style. If misses correlate with confound signatures measurable in DigiLeTs' rich
channels (x, y, PRESSURE, PEN_DOWN, TIMESTAMP), the gap is confound-explained and the intent is
recoverable -> licenses an intent-model (run 60). If misses are random wrt the channels, the confound
story is wrong on this data (or the channels are too coarse -- we say which).

This is PURE MEASUREMENT (the cheap-falsifier pattern of runs 33/46/50/57): no graph mutation, no
minting, no eval spend. Every function here is a deterministic measurement over raw pen channels.

================================================================================================
PRE-REGISTERED DEFINITIONS (fixed before looking at the confound results)
================================================================================================

INTENT (per class):
  A class QUALIFIES as multi-stroke if >= 50% of its instances have >= 2 pen-down strokes (run 58
  def). Among the multi-stroke instances of a qualifying class, the class carries a JUNCTION INTENT
  if >= 60% of them have AT LEAST ONE contacting stroke pair (junction_profile frac_none < 1.0,
  i.e. some pair is not ATTACH_NONE). This modal test self-selects the crossing/touching letters
  (t, x, k, 4, A, ...) and correctly EXCLUDES i/j (the dot never touches -> fCon ~ 0).

MISS / HIT (per instance of an intent class):
  MISS  = a multi-stroke instance of an intent class whose stroke pairs are ALL ATTACH_NONE
          (no contact anywhere) -- the intended junction did not realize.
  HIT   = a multi-stroke instance of an intent class with at least one contacting pair.

THE INTENDED-JUNCTION PAIR (measured identically for hits and misses -- count-matched, run-33):
  The NEAREST stroke pair (min point-to-point distance). For a hit this is a touching pair; for a
  miss it is the closest-but-disjoint pair = the junction that should have happened. A = the pair's
  earlier-drawn stroke (smaller stroke index), B = the later-drawn stroke.

CONFOUND SIGNATURES (creator's list -> DigiLeTs channels; each NORMALIZED PER WRITER as a robust-z
against THAT writer's own distribution over their intent-class instances; a confound is a deviation
from the writer's OWN norm -- the universal thing is the MECHANISM, measured relative to baseline):
  HAND-REPOSITION : raw = air-gap distance ||A_last_xy - B_first_xy|| (the pen's between-stroke jump).
                    flag if robust-z > +Z_BAR (moved farther than this writer usually does).
  DISTRACTION/PAUSE: raw = inter-stroke time gap t_ms[B_first] - t_ms[A_last].
                    flag if robust-z > +Z_BAR (paused longer than usual).
  EXTENSION-LIMIT : raw = distance from the junction location to the writer's used-area bbox EDGE,
                    normalized by the writer's bbox diagonal (junction near the edge = hand at reach
                    limit). flag if robust-z < -Z_BAR (nearer the edge than usual -- low edge-dist).
  INK/INITIATION  : raw = mean PRESSURE over B's first up-to-3 points (pen initiation of the second
                    stroke). flag if robust-z < -Z_BAR (lighter start than usual).
  Z_BAR = 1.0 (documented, not tuned -- ~1 robust-sigma into the writer's own tail).

THE TEST (count-matched; within-class shuffled null; run-33 discipline):
  Per confound: P(confound | miss) vs P(confound | hit), pooled over all intent instances; the LIFT
  = P|miss / P|hit; and a within-class label-shuffle null (permute miss/hit labels inside each class,
  B times, recompute pooled P(confound|miss)) giving the null mean, null 95th pct, and the observed
  value's z above null. Within-class shuffle matches the fact that misses concentrate in some classes.
  AGGREGATE: fraction of misses carrying >= 1 confound flag vs the same for hits, same null.

PRE-REGISTERED BARS:
  A confound is EXPLANATORY iff  P(conf|miss) > P(conf|hit)  AND  P(conf|miss) exceeds the within-
  class shuffled null 95th percentile (materially above chance).
  The gap is CONFOUND-EXPLAINED (-> LICENSED, build the intent-model in run 60) iff the AGGREGATE
  fraction-of-misses-with-any-confound is  (a) > 1.5x the hit baseline  AND  (b) above the shuffled
  null 95th pct. We additionally report whether > 50% of misses carry a confound (an absolute-size
  read). Otherwise NULL (misses random wrt channels -- confounds don't explain the gap here).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import pen_world as pw          # noqa: E402
from domains import discrimination as dc     # noqa: E402

Z_BAR = 1.0
MULTISTROKE_FRAC = 0.5      # class qualifies as multi-stroke if >= this frac of instances have >=2 strokes
INTENT_FRAC = 0.6           # class carries junction intent if >= this frac of MS instances have contact
N_SHUFFLE = 1000
SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "seeds", "stroke_shapes.json")

CONFOUNDS = ("reposition", "pause", "extension", "ink")


# ------------------------------------------------------------------------------------------------
#  PURE MEASUREMENT HELPERS (deterministic; unit-tested in tests/test_confounds_migrated.py)
# ------------------------------------------------------------------------------------------------
def strokes_as_lists(strokes):
    """Stroke arrays -> list-of-list points (discrimination._as_xy accepts only list/tuple rows,
    the standing numpy gotcha -- a bare (k,2) ndarray silently reads as EMPTY and every junction
    collapses to ATTACH_NONE)."""
    out = []
    for s in strokes:
        arr = np.asarray(s, dtype=float)
        out.append(arr.reshape(-1, arr.shape[-1]).tolist() if arr.size else [])
    return out


def instance_has_contact(strokes) -> bool | None:
    """None if not multi-stroke (<2 strokes); else True iff some stroke pair contacts."""
    if len(strokes) < 2:
        return None
    prof = dc.junction_profile(strokes_as_lists(strokes))
    return prof["frac_none"] < 1.0


def nearest_stroke_pair(strokes):
    """(i, j) indices (i<j) of the stroke pair with the minimum point-to-point distance, plus that
    distance. Returns (None, None, inf) if fewer than 2 non-empty strokes."""
    xs = [np.asarray(s, dtype=float).reshape(-1, 2) for s in
          (strokes_as_lists(strokes) if not isinstance(strokes[0], list) else strokes)]
    best = (None, None, float("inf"))
    n = len(xs)
    for i in range(n):
        if xs[i].shape[0] == 0:
            continue
        for j in range(i + 1, n):
            if xs[j].shape[0] == 0:
                continue
            d = np.linalg.norm(xs[i][:, None, :] - xs[j][None, :, :], axis=2)
            m = float(d.min())
            if m < best[2]:
                best = (i, j, m)
    return best


def instance_raw_metrics(sample):
    """The confound RAW metrics (pre-writer-normalization) for one intent-class instance, measured
    on the intended-junction pair (the nearest stroke pair). Returns a dict, or None if the instance
    is not usable (fewer than 2 non-empty strokes). Keys: reposition, pause, pressure_start,
    junction_xy (np(2,)). edge_dist is computed later (needs the writer bbox)."""
    strokes = sample["strokes"]
    i, j, mind = nearest_stroke_pair(strokes)
    if i is None:
        return None
    A = np.asarray(strokes[i], dtype=float).reshape(-1, 2)
    B = np.asarray(strokes[j], dtype=float).reshape(-1, 2)
    a_last, b_first = A[-1], B[0]
    reposition = float(np.hypot(*(a_last - b_first)))
    # nearest contact points -> junction location.
    d = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    ia, ib = np.unravel_index(int(np.argmin(d)), d.shape)
    junction_xy = 0.5 * (A[ia] + B[ib])
    # time gap: t_ms is per-point, continuous across the instance; stroke j starts after stroke i.
    # find the point indices of A_last and B_first in the full instance path.
    pen_down = sample.get("pen_down")
    t_ms = sample.get("t_ms")
    pause = float("nan")
    if t_ms is not None and pen_down is not None:
        starts = [k for k, v in enumerate(pen_down) if v == 1]
        if not starts or starts[0] != 0:
            starts = [0] + starts
        # stroke k spans [starts[k], starts[k+1]); B_first index = starts[j]; A_last index = starts[i+1]-1.
        if j < len(starts):
            b_first_idx = starts[j]
            a_last_idx = (starts[i + 1] - 1) if (i + 1) < len(starts) else (len(t_ms) - 1)
            if 0 <= a_last_idx < len(t_ms) and 0 <= b_first_idx < len(t_ms):
                pause = float(t_ms[b_first_idx] - t_ms[a_last_idx])
    # pressure at initiation of stroke B: mean over its first up-to-3 points.
    pressure = sample.get("pressure")
    pressure_start = float("nan")
    if pressure is not None and pen_down is not None:
        starts = [k for k, v in enumerate(pen_down) if v == 1]
        if not starts or starts[0] != 0:
            starts = [0] + starts
        if j < len(starts):
            b0 = starts[j]
            seg = np.asarray(pressure[b0:b0 + 3], dtype=float)
            if seg.size:
                pressure_start = float(seg.mean())
    return {"reposition": reposition, "pause": pause, "pressure_start": pressure_start,
            "junction_xy": junction_xy, "pair": (i, j)}


def writer_bbox(samples_of_writer):
    """(minx, miny, maxx, maxy, diag) over ALL of a writer's recorded points = their used area."""
    pts = np.vstack([np.asarray(s["pos_xy"], dtype=float).reshape(-1, 2) for s in samples_of_writer])
    lo, hi = pts.min(0), pts.max(0)
    diag = float(np.hypot(*(hi - lo))) or 1.0
    return float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1]), diag


def edge_distance(junction_xy, bbox) -> float:
    """Normalized distance from a junction point to the nearest side of the writer's used bbox
    (0 = on the edge; larger = deeper inside). Normalized by the bbox diagonal so it is comparable
    across writers with different-sized used areas."""
    minx, miny, maxx, maxy, diag = bbox
    x, y = float(junction_xy[0]), float(junction_xy[1])
    d = min(x - minx, maxx - x, y - miny, maxy - y)
    return d / diag


def robust_z(x, values) -> float:
    """(x - median) / (1.4826 * MAD), falling back to std then 0 when the spread is degenerate.
    NaNs in `values` are dropped; NaN `x` -> 0.0 (no flag)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0.0
    vals = np.asarray([v for v in values if not (isinstance(v, float) and np.isnan(v))], dtype=float)
    if vals.size == 0:
        return 0.0
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826
    if mad > 1e-9:
        return (float(x) - med) / mad
    sd = float(vals.std())
    if sd > 1e-9:
        return (float(x) - med) / sd
    return 0.0


def confound_flags(z):
    """Per-confound boolean flags from the four robust-z values (pre-registered directions/bar)."""
    return {
        "reposition": z["reposition"] > Z_BAR,
        "pause": z["pause"] > Z_BAR,
        "extension": z["extension"] < -Z_BAR,
        "ink": z["ink"] < -Z_BAR,
    }


# ------------------------------------------------------------------------------------------------
#  BUILD THE INTENT/MISS/CONFOUND TABLE
# ------------------------------------------------------------------------------------------------
def build_instances(samples):
    """Returns (records, class_summary). Each record: dict with class, symbol, writer, is_miss,
    raw metrics, and per-writer-normalized flags. class_summary: per intent class stats."""
    by_cls = defaultdict(list)
    for s in samples:
        by_cls[s["class"]].append(s)
    by_writer = defaultdict(list)
    for s in samples:
        by_writer[s["writer_id"]].append(s)
    bboxes = {w: writer_bbox(ss) for w, ss in by_writer.items()}

    # 1. intent classes + miss/hit labels.
    intent_records = []      # (sample, is_miss)
    class_summary = []
    for cls, insts in sorted(by_cls.items()):
        ms = [s for s in insts if len(s["strokes"]) >= 2]
        if len(ms) / len(insts) < MULTISTROKE_FRAC:
            continue
        contacts = [(s, instance_has_contact(s["strokes"])) for s in ms]
        contacts = [(s, c) for s, c in contacts if c is not None]
        if not contacts:
            continue
        fcon = float(np.mean([c for _, c in contacts]))
        is_intent = fcon >= INTENT_FRAC
        n_miss = sum(1 for _, c in contacts if not c)
        class_summary.append({"symbol": pw.DIGILETS_SYMBOLS[cls], "n": len(insts), "n_ms": len(ms),
                              "fcon": fcon, "intent": is_intent, "n_used": len(contacts),
                              "n_miss": n_miss, "cls": cls})
        if not is_intent:
            continue
        for s, c in contacts:
            intent_records.append((s, (not c)))

    # 2. raw metrics per instance.
    recs = []
    for s, is_miss in intent_records:
        raw = instance_raw_metrics(s)
        if raw is None:
            continue
        bbox = bboxes[s["writer_id"]]
        recs.append({
            "cls": s["class"], "symbol": s["symbol"], "writer": s["writer_id"], "is_miss": is_miss,
            "reposition": raw["reposition"], "pause": raw["pause"],
            "pressure_start": raw["pressure_start"],
            "extension": edge_distance(raw["junction_xy"], bbox),
        })

    # 3. per-writer robust-z per metric -> flags. (extension uses edge_distance; ink uses pressure_start)
    metric_key = {"reposition": "reposition", "pause": "pause", "extension": "extension",
                  "ink": "pressure_start"}
    by_w = defaultdict(list)
    for r in recs:
        by_w[r["writer"]].append(r)
    for w, rs in by_w.items():
        pools = {c: [r[metric_key[c]] for r in rs] for c in CONFOUNDS}
        for r in rs:
            z = {c: robust_z(r[metric_key[c]], pools[c]) for c in CONFOUNDS}
            r["z"] = z
            r["flags"] = confound_flags(z)
            r["any"] = any(r["flags"].values())
    return recs, class_summary


# ------------------------------------------------------------------------------------------------
#  THE TEST: P(conf|miss) vs P(conf|hit), lift, within-class shuffled null
# ------------------------------------------------------------------------------------------------
def _pooled_p_miss(flag_arr, miss_arr):
    m = miss_arr.sum()
    return float(flag_arr[miss_arr].mean()) if m else 0.0


def shuffled_null(flag_arr, miss_arr, cls_arr, n=N_SHUFFLE, seed=20260706):
    """Permute miss labels WITHIN each class, recompute pooled P(flag|miss). Returns the null
    samples array."""
    rng = np.random.default_rng(seed)
    out = np.empty(n, dtype=float)
    idx_by_cls = {c: np.where(cls_arr == c)[0] for c in np.unique(cls_arr)}
    for b in range(n):
        perm_miss = miss_arr.copy()
        for c, idx in idx_by_cls.items():
            perm = rng.permutation(idx)
            perm_miss[idx] = miss_arr[perm]
        out[b] = _pooled_p_miss(flag_arr, perm_miss)
    return out


def run_test(recs):
    miss_arr = np.asarray([r["is_miss"] for r in recs], dtype=bool)
    cls_arr = np.asarray([r["cls"] for r in recs])
    n_miss = int(miss_arr.sum())
    n_hit = int((~miss_arr).sum())
    results = {}
    for c in list(CONFOUNDS) + ["any"]:
        if c == "any":
            flag_arr = np.asarray([r["any"] for r in recs], dtype=bool)
        else:
            flag_arr = np.asarray([r["flags"][c] for r in recs], dtype=bool)
        p_miss = _pooled_p_miss(flag_arr, miss_arr)
        p_hit = float(flag_arr[~miss_arr].mean()) if n_hit else 0.0
        lift = (p_miss / p_hit) if p_hit > 0 else float("inf")
        null = shuffled_null(flag_arr, miss_arr, cls_arr)
        null_mean = float(null.mean())
        null_95 = float(np.percentile(null, 95))
        null_sd = float(null.std())
        z_vs_null = (p_miss - null_mean) / null_sd if null_sd > 1e-9 else 0.0
        p_perm = float((null >= p_miss).mean())      # one-sided permutation p-value
        explanatory = (p_miss > p_hit) and (p_miss > null_95)
        results[c] = {"p_miss": p_miss, "p_hit": p_hit, "lift": lift, "null_mean": null_mean,
                      "null_95": null_95, "z_vs_null": z_vs_null, "p_perm": p_perm,
                      "explanatory": explanatory, "n_flag_miss": int(flag_arr[miss_arr].sum())}
    return results, n_miss, n_hit


# ------------------------------------------------------------------------------------------------
def seed_md5():
    with open(SEED_PATH, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="falsifier")
    ap.add_argument("--limit-writers", type=int, default=None)
    args = ap.parse_args()

    md5_before = seed_md5()
    print(f"[seed-guard] stroke_shapes.json md5 BEFORE = {md5_before}", flush=True)
    print(f"[pre-reg] Z_BAR={Z_BAR} MULTISTROKE_FRAC={MULTISTROKE_FRAC} INTENT_FRAC={INTENT_FRAC} "
          f"N_SHUFFLE={N_SHUFFLE}", flush=True)
    t0 = time.time()

    samples = pw.load_digilets_samples(limit_writers=args.limit_writers)
    print(f"[load] {len(samples)} DigiLeTs instances, {len({s['writer_id'] for s in samples})} "
          f"writers in {time.time()-t0:.1f}s", flush=True)

    recs, class_summary = build_instances(samples)
    intent = [c for c in class_summary if c["intent"]]
    print(f"\n[intent classes] {len(intent)} of {len(class_summary)} multi-stroke classes carry a "
          f"junction intent (fcon>={INTENT_FRAC}):", flush=True)
    print(f"  {'sym':>4}{'nMS':>6}{'fCon':>7}{'nUsed':>7}{'nMiss':>7}{'missRate':>10}", flush=True)
    tot_miss = tot_used = 0
    for cs in intent:
        mr = cs["n_miss"] / cs["n_used"] if cs["n_used"] else 0
        print(f"  {cs['symbol']:>4}{cs['n_ms']:>6}{cs['fcon']:>7.2f}{cs['n_used']:>7}"
              f"{cs['n_miss']:>7}{mr:>10.3f}", flush=True)
        tot_miss += cs["n_miss"]; tot_used += cs["n_used"]
    print(f"  [overall] miss rate = {tot_miss}/{tot_used} = {tot_miss/tot_used:.3f}", flush=True)
    print(f"  [records with usable junction pair] {len(recs)} "
          f"(miss={sum(r['is_miss'] for r in recs)}, hit={sum(not r['is_miss'] for r in recs)})",
          flush=True)

    results, n_miss, n_hit = run_test(recs)
    print(f"\n[TEST] n_miss={n_miss} n_hit={n_hit}  (within-class shuffled null, "
          f"{N_SHUFFLE} perms)\n", flush=True)
    hdr = (f"  {'confound':>12}{'P|miss':>9}{'P|hit':>9}{'lift':>7}{'nullMean':>10}"
           f"{'null95':>9}{'zVsNull':>9}{'pPerm':>8}{'EXPL':>6}")
    print(hdr, flush=True)
    for c in list(CONFOUNDS) + ["any"]:
        r = results[c]
        lift = f"{r['lift']:.2f}" if np.isfinite(r["lift"]) else "inf"
        print(f"  {c:>12}{r['p_miss']:>9.3f}{r['p_hit']:>9.3f}{lift:>7}{r['null_mean']:>10.3f}"
              f"{r['null_95']:>9.3f}{r['z_vs_null']:>9.2f}{r['p_perm']:>8.3f}"
              f"{str(r['explanatory']):>6}", flush=True)

    # aggregate verdict.
    agg = results["any"]
    frac_hit = agg["p_hit"]
    licensed = (agg["p_miss"] > 1.5 * frac_hit) and (agg["p_miss"] > agg["null_95"])
    explanatory_confounds = [c for c in CONFOUNDS if results[c]["explanatory"]]
    print(f"\n[AGGREGATE] fraction of MISSES with >=1 confound = {agg['p_miss']:.3f}  vs  "
          f"hit baseline {frac_hit:.3f}  (lift {agg['lift']:.2f}, null95 {agg['null_95']:.3f}, "
          f"pPerm {agg['p_perm']:.3f})", flush=True)
    print(f"[AGGREGATE] > 50% of misses carry a confound? "
          f"{agg['p_miss'] > 0.5}  ({agg['p_miss']:.3f})", flush=True)
    print(f"[EXPLANATORY CONFOUNDS] {explanatory_confounds or 'NONE'}", flush=True)

    verdict = "LICENSED" if licensed else "NULL"
    print(f"\n==================================================================", flush=True)
    print(f"  VERDICT: {verdict}", flush=True)
    if licensed:
        print("  Intent-misses ARE confound-correlated -> the intent is recoverable ->", flush=True)
        print("  build the intent-model (run 60).", flush=True)
    else:
        print("  Intent-misses are NOT materially confound-correlated above the within-class", flush=True)
        print("  null -> confounds do not explain the gap on this data (or channels too coarse).", flush=True)
    print(f"==================================================================", flush=True)

    md5_after = seed_md5()
    print(f"\n[seed-guard] stroke_shapes.json md5 AFTER = {md5_after}", flush=True)
    assert md5_before == md5_after, "SEED MUTATED -- guard failed!"
    print(f"[seed-guard] OK (unchanged)  |  total {time.time()-t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
