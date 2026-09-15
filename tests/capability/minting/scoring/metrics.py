"""Shared scorer for the gated-minting capability suite — the PUBLISHED rubric
metrics, implemented in pure Python (no scipy) so the suite is self-contained and
every number is auditable.

Rubric A (arXiv:2505.17117):
  · RQ2  spearman_rho(order_a, order_b)      — item-order vs human typicality order.
  · RQ1  ami / nmi / ari(labels_a, labels_b) — cluster vs human category alignment.
  · RQ3  l_objective(items, clusters, embed) — I(X;C) + beta * within-cluster spread.

Rubric B (Carey readiness gate) + gate scoring:
  · gate_precision_recall(pred, gold)        — minted-right-axis-at-right-time P/R/F1.

Statistical spine (FLEX, arXiv:2107.07170):
  · bootstrap_ci(values)                     — nonparametric confidence interval.

All inputs are plain Python lists/dicts; nothing here touches the substrate or an
LLM — it only SCORES their emitted decisions.
"""
from __future__ import annotations

import math
import random
from typing import Any, Iterable, Optional, Sequence


# --------------------------------------------------------------------------- #
#  RQ2 — Spearman rank correlation (the fine-grained-fidelity metric)
# --------------------------------------------------------------------------- #
def _rankdata(xs: Sequence[float]) -> list[float]:
    """Fractional ranks (ties share the average rank) — the standard Spearman
    tie handling, so the rho below equals scipy.stats.spearmanr on the same data."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0          # 1-based average rank over the tie block
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Pearson r; None when a series is constant (undefined correlation)."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def spearman_rho(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Spearman rank correlation rho in [-1, 1]: Pearson over the fractional ranks.
    This is the exact metric Rubric A RQ2 reports (item-to-centroid similarity vs
    human typicality). None when undefined (constant series / n<2)."""
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    return pearson(_rankdata(xs), _rankdata(ys))


# --------------------------------------------------------------------------- #
#  RQ1 — clustering alignment (AMI / NMI / ARI)
# --------------------------------------------------------------------------- #
def _contingency(a: Sequence[Any], b: Sequence[Any]):
    la = sorted(set(a))
    lb = sorted(set(b))
    ia = {v: i for i, v in enumerate(la)}
    ib = {v: i for i, v in enumerate(lb)}
    tab = [[0] * len(lb) for _ in la]
    for x, y in zip(a, b):
        tab[ia[x]][ib[y]] += 1
    return tab, la, lb


def _entropy(counts: Iterable[int], n: int) -> float:
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / n
            h -= p * math.log(p)
    return h


def _mutual_information(tab, n) -> float:
    ai = [sum(row) for row in tab]
    bj = [sum(col) for col in zip(*tab)] if tab else []
    mi = 0.0
    for i, row in enumerate(tab):
        for j, nij in enumerate(row):
            if nij > 0:
                mi += (nij / n) * math.log(nij * n / (ai[i] * bj[j]))
    return mi


def nmi(a: Sequence[Any], b: Sequence[Any]) -> Optional[float]:
    """Normalized Mutual Information (arithmetic-mean normalization), in [0,1]."""
    n = len(a)
    if n == 0 or n != len(b):
        return None
    tab, _, _ = _contingency(a, b)
    ha = _entropy([sum(row) for row in tab], n)
    hb = _entropy([sum(col) for col in zip(*tab)], n)
    if ha == 0 and hb == 0:
        return 1.0
    mi = _mutual_information(tab, n)
    denom = (ha + hb) / 2.0
    return mi / denom if denom > 0 else 0.0


def _expected_mi(tab, n) -> float:
    """Expected MI under the hypergeometric model (for AMI's chance correction)."""
    ai = [sum(row) for row in tab]
    bj = [sum(col) for col in zip(*tab)] if tab else []

    def logfact(k):
        return math.lgamma(k + 1)

    emi = 0.0
    for i in range(len(ai)):
        for j in range(len(bj)):
            lo = max(1, ai[i] + bj[j] - n)
            hi = min(ai[i], bj[j])
            for nij in range(lo, hi + 1):
                term = (nij / n) * math.log(n * nij / (ai[i] * bj[j]))
                logp = (logfact(ai[i]) + logfact(bj[j]) + logfact(n - ai[i])
                        + logfact(n - bj[j]) - logfact(n) - logfact(nij)
                        - logfact(ai[i] - nij) - logfact(bj[j] - nij)
                        - logfact(n - ai[i] - bj[j] + nij))
                emi += term * math.exp(logp)
    return emi


def ami(a: Sequence[Any], b: Sequence[Any]) -> Optional[float]:
    """Adjusted Mutual Information (chance-corrected), matching sklearn's AMI with
    arithmetic-mean normalization. This is the headline Rubric A RQ1 metric."""
    n = len(a)
    if n == 0 or n != len(b):
        return None
    tab, _, _ = _contingency(a, b)
    ha = _entropy([sum(row) for row in tab], n)
    hb = _entropy([sum(col) for col in zip(*tab)], n)
    if ha == 0 and hb == 0:
        return 1.0
    mi = _mutual_information(tab, n)
    emi = _expected_mi(tab, n)
    denom = (ha + hb) / 2.0 - emi
    if abs(denom) < 1e-12:
        return 0.0
    return (mi - emi) / denom


def ari(a: Sequence[Any], b: Sequence[Any]) -> Optional[float]:
    """Adjusted Rand Index (chance-corrected), in [-1,1]; 1 = perfect agreement."""
    n = len(a)
    if n == 0 or n != len(b):
        return None
    tab, _, _ = _contingency(a, b)

    def comb2(k):
        return k * (k - 1) // 2

    sum_ij = sum(comb2(nij) for row in tab for nij in row)
    ai = sum(comb2(sum(row)) for row in tab)
    bj = sum(comb2(sum(col)) for col in zip(*tab))
    total = comb2(n)
    if total == 0:
        return 1.0
    expected = ai * bj / total
    maxidx = (ai + bj) / 2.0
    if abs(maxidx - expected) < 1e-12:
        return 0.0
    return (sum_ij - expected) / (maxidx - expected)


# --------------------------------------------------------------------------- #
#  RQ3 — the L objective (compression + distortion)
# --------------------------------------------------------------------------- #
def l_objective(labels: Sequence[Any], embeddings: Sequence[Sequence[float]],
                beta: float = 1.0) -> dict:
    """The Rubric A RQ3 objective:
        L = I(X;C) + beta * (1/|X|) * sum_c sum_{i in c} || e_i - centroid_c ||^2 .
    Complexity = I(X;C) = log2|X| - (1/|X|) sum_c |c| log2 |c|  (bits).
    Distortion = mean squared distance to the cluster centroid.
    Lower L = more 'efficient' (LLMs sit low, over-compressed; humans higher/richer).
    Returns {complexity, distortion, L}. Pure geometry over the supplied embeddings —
    which embedding space is used (substrate signature coords, or LLM vectors) is the
    caller's honest choice."""
    n = len(labels)
    if n == 0 or n != len(embeddings):
        return {"complexity": None, "distortion": None, "L": None}
    # complexity in bits
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for lab, e in zip(labels, embeddings):
        groups[lab].append(list(map(float, e)))
    complexity = math.log2(n)
    for c, es in groups.items():
        complexity -= (len(es) / n) * math.log2(len(es))
    # distortion
    total = 0.0
    for c, es in groups.items():
        dim = len(es[0])
        centroid = [sum(e[d] for e in es) / len(es) for d in range(dim)]
        for e in es:
            total += sum((e[d] - centroid[d]) ** 2 for d in range(dim))
    distortion = total / n
    return {"complexity": complexity, "distortion": distortion,
            "L": complexity + beta * distortion}


# --------------------------------------------------------------------------- #
#  Rubric B — the accommodation-gate scoring (precision / recall / F1)
# --------------------------------------------------------------------------- #
def gate_precision_recall(predicted_mints: Iterable[Any],
                          gold_should_mint: Iterable[Any]) -> dict:
    """Score the accommodation gate as a retrieval task: over a set of candidate
    gap-events, how well do the system's ACTUAL mints match the events that SHOULD
    have minted (persistent gaps), while NOT minting the ones that should not
    (transient / duplicate). Returns {tp,fp,fn,tn?,precision,recall,f1}. Sets are
    keyed by an opaque event id."""
    pred = set(predicted_mints)
    gold = set(gold_should_mint)
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if not gold else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4)}


# --------------------------------------------------------------------------- #
#  FLEX — nonparametric bootstrap confidence interval
# --------------------------------------------------------------------------- #
def bootstrap_ci(values: Sequence[float], *, iters: int = 2000,
                 alpha: float = 0.05, seed: int = 12345) -> dict:
    """Percentile bootstrap CI for the mean of `values` (FLEX-style reporting, so a
    score is an interval not a bare point). Deterministic given `seed`."""
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    rng = random.Random(seed)
    n = len(vals)
    means = []
    for _ in range(iters):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int((alpha / 2) * iters)]
    hi = means[min(iters - 1, int((1 - alpha / 2) * iters))]
    return {"mean": round(sum(vals) / n, 4), "lo": round(lo, 4),
            "hi": round(hi, 4), "n": n}


# Published LLM reference points from arXiv:2505.17117 (for side-by-side reporting).
LLM_REFERENCE = {
    "rq2_spearman_decoder_typical": 0.15,   # most decoder LLMs fall below ~0.15-0.2
    "rq2_spearman_bert": 0.38,              # BERT static-layer typicality rho
    "rq1_ami_human_aligned": 0.55,          # peak human-aligned AMI band
    "rq1_ami_encoder_peak": 0.60,           # encoder models peak
}
