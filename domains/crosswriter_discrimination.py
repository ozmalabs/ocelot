"""crosswriter_discrimination -- RUN 58b: THE CROSS-WRITER-ROBUST DISCRIMINATION FIX.

Run 57 built the discrimination faculty (`domains/discrimination.py`): precision = FISHER
discriminability (between-class-var / within-class-var). Run 58 applied it to pen data (DigiLeTs)
and found the junction relation `frac_none` (do two strokes touch?) separates classes with Fisher
1.328 -- 8x mouse's arrangement max -- and orthogonal to geometry. It LICENSED, but the held-out
CROSS-WRITER eval HARMED -8.2pp. THE DIAGNOSIS: run 58's Fisher measured within-class variance over
a POOLED background population, so it captured structure that is WRITER-CORRELATED-with-class
(a held-out writer's stroke-touch / segmentation choices are their own STYLE) -- background Fisher
OVERESTIMATED recognition value, and the in-distribution background-sanity gate PASSED (+0.5pp) while
eval collapsed. The bug is general: background-calibrated discriminability != held-out
discriminability when the separating signal is writer-idiosyncratic.

THE FIX (BPL's move -- learn what is class-defining vs stylistic FROM MANY WRITERS):

1. CROSS-WRITER FISHER (`crosswriter_fisher`). A WRITER-BLOCKED variance decomposition: the unit of
   replication WITHIN each class is the WRITER, not the instance. Each (writer, class) contributes
   ONE mean (its writer weighted EQUALLY -- a prolific writer cannot dominate the class centroid the
   way pooled instance-counting lets it). Then

       between-class var = spread of the class centroids (means of the per-writer class means)
       within-class var  = spread of the per-writer class means AROUND their class centroid
                           == the BETWEEN-WRITER scatter within a class
       fisher            = between / within.

   A feature whose class-distinction is CONSISTENT across writers (every writer's class-A mean sits
   near the class-A centroid) has small within -> high Fisher -> TRANSFERABLE / trusted. A feature
   that VARIES by writer for the same class (writer-idiosyncratic style, or a separation driven by a
   handful of prolific writers) has large between-writer scatter -> large within -> LOW Fisher ->
   distrusted. This is exactly the run-58 failure case, and it is precisely what pooled Fisher
   (`discrimination.fisher_ratio` over instances pooled across writers) does NOT penalize: pooled
   Fisher weights by instance count, so a prolific writer's idiosyncratic value inflates the
   between-class separation and shrinks the apparent within-class variance.

   `pooled_fisher` is kept alongside as the exact run-58 comparator for the side-by-side falsifier.

2. CROSS-WRITER-HELD-OUT SANITY (`split_writers`). The background-sanity gate must itself HOLD OUT
   WRITERS: calibrate discriminability on background writers A, sanity-check accuracy on DIFFERENT
   background writers B. A non-transferable signal then FAILS sanity BEFORE the held-out eval is
   ever spent -- closing the exact hole run 58 fell through (its sanity calibrated and tested on the
   SAME pooled writers, so an in-distribution +0.5pp masked a cross-writer -8.2pp).

This module is PURE STATISTICS + a deterministic writer split -- the SAME class of mechanical
reduction `discrimination.fisher_ratio` / `unified_verdict.part_precision` already are (a variance
ratio over already-collected residuals, never a ranking DECISION). The verdict ranking stays the
held `Argmin`; only the PRECISION VALUES it is fed change, and they are stored as graph-resident
`log_weight` edges via the UNCHANGED `discrimination.install_part_precisions` (run 30/57 pattern).
"""
from __future__ import annotations

import numpy as np

from domains import discrimination as disc

_VAR_EPS = 1e-9


# --------------------------------------------------------------------------------------------- #
#  CROSS-WRITER (WRITER-BLOCKED) FISHER. Within-class variance = BETWEEN-WRITER scatter of the
#  per-writer class means, each writer weighted equally. Penalizes writer-idiosyncratic separation.
# --------------------------------------------------------------------------------------------- #
def _writer_means(per_writer_values: dict) -> list:
    """`{writer: [values...]}` -> `[per-writer mean, ...]` over writers with >= 1 value. Averaging
    each writer's instances collapses within-writer instance noise so the surviving spread is
    purely BETWEEN-writer -- the transferability signal."""
    return [float(np.mean(v)) for v in per_writer_values.values()
            if v is not None and len(v) > 0]


def crosswriter_fisher(per_class_writer_values: dict, min_writers: int = 2) -> float:
    """Writer-blocked multi-class Fisher. `per_class_writer_values` = `{class: {writer: [values]}}`.
    Each (writer, class) contributes ONE mean (equal weight per writer). A class is included only if
    it has >= `min_writers` writers (cross-writer replication is required to measure transferability
    at all). Fewer than two such classes -> 0.0.

        between = sum_c n_c (centroid_c - grand)^2 / N       (n_c = number of WRITERS in class c)
        within  = sum_c sum_w (writer_mean_{c,w} - centroid_c)^2 / N   (between-writer scatter)
        fisher  = between / max(within, eps).

    A feature whose per-writer class means agree (small within) but whose class centroids differ
    (large between) SEPARATES CLASSES ACROSS WRITERS -> high Fisher -> transferable. A feature whose
    per-writer class means scatter (writers disagree on that class's value) -> large within -> low
    Fisher -> distrusted, EVEN when pooled Fisher rates it high."""
    class_writer_means = {}
    for c, byw in per_class_writer_values.items():
        wm = _writer_means(byw)
        if len(wm) >= min_writers:
            class_writer_means[c] = wm
    if len(class_writer_means) < 2:
        return 0.0
    ns = {c: float(len(wm)) for c, wm in class_writer_means.items()}
    centroids = {c: float(np.mean(wm)) for c, wm in class_writer_means.items()}
    total_n = float(sum(ns.values()))
    grand = float(sum(ns[c] * centroids[c] for c in ns) / total_n)
    between = float(sum(ns[c] * (centroids[c] - grand) ** 2 for c in ns) / total_n)
    within = float(sum(sum((m - centroids[c]) ** 2 for m in class_writer_means[c])
                       for c in ns) / total_n)
    return between / max(within, _VAR_EPS)


def pooled_fisher(per_class_writer_values: dict, min_writers: int = 2) -> float:
    """Run 58's Fisher for the side-by-side falsifier: pool EVERY writer's instances of a class
    into one group and take `discrimination.fisher_ratio` (instance-weighted within-class variance).
    Restricted to the SAME classes `crosswriter_fisher` uses (>= `min_writers`) so the two numbers
    are directly comparable. This is the comparator that OVERESTIMATES a writer-idiosyncratic
    feature's separating power."""
    groups = []
    for c, byw in per_class_writer_values.items():
        wm = _writer_means(byw)
        if len(wm) >= min_writers:
            pooled = [float(x) for v in byw.values() if v for x in v]
            if pooled:
                groups.append(pooled)
    return disc.fisher_ratio(groups)


def crosswriter_slot_fisher(per_slot_class_writer_values: dict, min_writers: int = 2) -> dict:
    """Per-SLOT cross-writer Fisher. `{slot: {class: {writer: [values]}}}` -> `{slot: fisher}`. The
    cross-writer twin of `discrimination.slot_discriminability`."""
    return {slot: crosswriter_fisher(cw, min_writers=min_writers)
            for slot, cw in per_slot_class_writer_values.items()}


def pooled_slot_fisher(per_slot_class_writer_values: dict, min_writers: int = 2) -> dict:
    """Per-SLOT pooled (run-58) Fisher over the same structure -- for the side-by-side drop table."""
    return {slot: pooled_fisher(cw, min_writers=min_writers)
            for slot, cw in per_slot_class_writer_values.items()}


def crosswriter_part_discriminability(true_by_writer: dict, false_by_writer: dict,
                                      min_writers: int = 2) -> float:
    """Recognition-time TWO-class cross-writer Fisher over a part-type's residuals, blocked by the
    QUERY writer. `true_by_writer` / `false_by_writer` = `{query_writer: [residuals...]}`. The
    cross-writer drop-in for `discrimination.part_discriminability`: it distrusts a part whose
    true-vs-false separation is driven by particular writers rather than holding across writers.
    When there are too few writers to block, it degrades to a pooled two-class Fisher (so it never
    silently returns 0 for a real single-writer diagnostic)."""
    cw = crosswriter_fisher({"true": true_by_writer, "false": false_by_writer},
                            min_writers=min_writers)
    if cw > 0.0:
        return cw
    true_all = [float(x) for v in true_by_writer.values() if v for x in v]
    false_all = [float(x) for v in false_by_writer.values() if v for x in v]
    return disc.part_discriminability(true_all, false_all)


def normalize_weights(slot_fisher: dict, slots) -> dict:
    """Turn per-slot cross-writer Fisher into `relational_distance`-compatible weights (mean 1 over
    `slots`, matching `relational_variation.slot_weights`' scale). A slot whose cross-writer Fisher
    is ~0 (non-transferable) keeps ~0 weight -> the arrangement residual IGNORES it; the transferable
    slots carry the residual. Mechanical arithmetic (a normalization, not a decision)."""
    raw = {s: float(slot_fisher.get(s, 0.0)) for s in slots}
    mean_w = float(np.mean(list(raw.values()))) if raw else 0.0
    if mean_w <= 0.0:
        return {s: 1.0 for s in slots}
    return {s: raw[s] / mean_w for s in slots}


# --------------------------------------------------------------------------------------------- #
#  CROSS-WRITER-HELD-OUT SANITY: a deterministic disjoint writer split. Calibrate on A, sanity on B.
# --------------------------------------------------------------------------------------------- #
def split_writers(writers, frac_calib: float = 0.5, seed: int = 0) -> tuple:
    """Deterministically partition `writers` into (calibration writers, sanity writers) with NO
    overlap and full coverage. Calibrate discriminability on the first group, sanity-check accuracy
    on the second -- so a signal that does not TRANSFER between two disjoint sets of background
    writers fails sanity before any held-out eval is spent. Seeded shuffle-and-slice (the same
    mechanical form as `pen_world.digilets_writer_split`)."""
    ws = sorted(set(writers))
    if len(ws) < 2:
        return ws, []
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(ws))
    n_cal = max(1, min(len(ws) - 1, int(round(frac_calib * len(ws)))))
    cal = sorted(ws[i] for i in order[:n_cal])
    san = sorted(ws[i] for i in order[n_cal:])
    return cal, san


__all__ = ["crosswriter_fisher", "pooled_fisher", "crosswriter_slot_fisher", "pooled_slot_fisher",
           "crosswriter_part_discriminability", "normalize_weights", "split_writers"]
