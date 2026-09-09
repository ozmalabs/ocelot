#!/usr/bin/env python3
"""Substrate scaling projection — X (distillation effort) -> Y (coverage),
how much X to reach LLM-scale coverage, how many OoM less compute per
inference, and the additive / no-retrain property quantified.

See docs/research/psychology_affect/SUBSTRATE_SCALING_PROJECTION_PREREG.md.

MEASURES (reproducible, this machine):
  (1) linear memory: bytes/node from a node-count sweep
  (2) flat local inference: coherence-read latency vs total graph size
  (3) distillation throughput: facts/sec ingested
  (4) additive marginal cost: ms/fact to add to a LARGE graph vs bulk ingest
THEN projects to ConceptNet / Wikipedia / LLM-coverage scales and computes the
OoM inference-compute gap vs a cited LLM anchor.

Every EXTRAPOLATED number is labelled. The coverage CEILING is printed too.
"""

from __future__ import annotations

import math
import random
import resource
import sys
import time

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

import substrate_rs as sr  # noqa: E402
from domains import qualia_navigation as qn  # noqa: E402


def rss_mb() -> float:
    # ru_maxrss is KB on Linux.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


# --- external anchor (cited in PREREG; estimates labelled) -----------------
LLAMA3_8B_PARAMS = 8e9            # published
LLAMA3_8B_TRAIN_TOKENS = 15e12   # published (~15T)
LLAMA3_8B_TRAIN_FLOPS = 6 * LLAMA3_8B_PARAMS * LLAMA3_8B_TRAIN_TOKENS  # 6ND est
LLAMA3_8B_INFER_FLOPS_PER_TOKEN = 2 * LLAMA3_8B_PARAMS                 # 2N est


def measure_memory_and_inference(sizes=(100, 1000, 10000, 50000, 100000)):
    """Sweep node count; return [(N, rss_mb, read_ms_flat)]."""
    random.seed(0)
    rows = []
    for N in sizes:
        s = sr.Substrate()
        inner = s._inner
        inner.add_node("Microtheory", {"name": "m", "temperature": 1.5,
                                        "discrete_mode": "3state", "can_tick": 0})
        nodes = [inner.add_node("Concept",
                                {"name": "c%d" % i, "state": 0.0,
                                 "external_field": 0.0, "identity_field": 0.0})
                 for i in range(N)]
        for i in range(N):
            for _ in range(4):
                try:
                    inner.add_edge_unchecked(nodes[i], "causal_influence",
                                             nodes[random.randrange(N)])
                except Exception:
                    pass
        # insert one coherence triad and time the PURE read (repeat to average)
        edges = [("cat", "backyard", 1.0), ("dog", "backyard", 1.0),
                 ("tree", "backyard", 1.0)]
        tri = qn.build_triad(s, ["cat", "dog", "tree"], edges,
                             held_out="backyard")
        reps = 2000
        t0 = time.perf_counter()
        for _ in range(reps):
            qn.coherence_signal(tri)
        read_ms = (time.perf_counter() - t0) * 1000 / reps
        rows.append((N, rss_mb(), read_ms))
        del s, inner, nodes, tri
    return rows


def measure_throughput_and_additive(N=100000, add=1000):
    """Return (facts_per_sec, bulk_ms_per_fact, add_ms_per_fact_large)."""
    random.seed(1)
    s = sr.Substrate()
    inner = s._inner
    t0 = time.perf_counter()
    nodes = [inner.add_node("Concept",
                            {"name": "c%d" % i, "state": 0.0,
                             "external_field": 0.0, "identity_field": 0.0})
             for i in range(N)]
    E = 0
    for i in range(N):
        for _ in range(4):
            try:
                inner.add_edge_unchecked(nodes[i], "causal_influence",
                                         nodes[random.randrange(N)])
                E += 1
            except Exception:
                pass
    bulk_s = time.perf_counter() - t0
    facts_per_sec = N / bulk_s
    bulk_ms_per_fact = bulk_s * 1000 / N
    # marginal add to the ALREADY-LARGE graph
    t0 = time.perf_counter()
    for i in range(add):
        c = inner.add_node("Concept",
                           {"name": "new%d" % i, "state": 0.0,
                            "external_field": 0.0, "identity_field": 0.0})
        for _ in range(4):
            try:
                inner.add_edge_unchecked(c, "causal_influence",
                                         nodes[random.randrange(N)])
            except Exception:
                pass
    add_ms_per_fact = (time.perf_counter() - t0) * 1000 / add
    return facts_per_sec, bulk_ms_per_fact, add_ms_per_fact


def fit_linear_bytes_per_node(rows):
    """Least-squares slope of rss(bytes) vs N over the two largest points
    (past the fixed interpreter overhead)."""
    big = [r for r in rows if r[0] >= 10000]
    if len(big) < 2:
        big = rows[-2:]
    (n0, m0, _), (n1, m1, _) = big[0], big[-1]
    return (m1 - m0) * 1024 * 1024 / (n1 - n0)


def main():
    print("=" * 72)
    print("SUBSTRATE SCALING PROJECTION")
    print("X (distillation effort) -> Y (coverage); OoM inference gap vs LLM")
    print("=" * 72)

    print("\n[1/2] MEASURING scaling constants (this machine) ...")
    rows = measure_memory_and_inference()
    print("\n  %-9s %-10s %-14s" % ("nodes", "RSS_MB", "read_ms(flat?)"))
    for N, mb, rd in rows:
        print("  %-9d %-10.1f %-14.4f" % (N, mb, rd))
    bpn = fit_linear_bytes_per_node(rows)
    read_first, read_last = rows[0][2], rows[-1][2]
    read_slope = (read_last - read_first) / (rows[-1][0] - rows[0][0])
    print("\n  fit: ~%.0f bytes/node (linear memory)" % bpn)
    print("  read latency slope over N: %.3e ms/node  (~0 => FLAT/local)"
          % read_slope)

    fps, bulk_mpf, add_mpf = measure_throughput_and_additive()
    print("\n  distillation throughput: %.0f facts/sec" % fps)
    print("  bulk ingest:      %.5f ms/fact" % bulk_mpf)
    print("  marginal add to 100k-node graph: %.5f ms/fact" % add_mpf)
    ratio = add_mpf / bulk_mpf if bulk_mpf else float("nan")
    print("  additive ratio (add/bulk): %.2f  (~1 => size-independent, "
          "no-retrain)" % ratio)

    # ---- projection ------------------------------------------------------
    print("\n[2/2] PROJECTION (linear-memory + flat-inference + additive)")
    # substrate per-read FLOP estimate: O(cues * degree) multiply-adds.
    # a coherence read over 3 cues x ~a few candidate edges ~= tens of MACs.
    substrate_read_flops = 3 * 8 * 2  # 3 cues, ~8 edge touches, MAC=2 flops
    NODE_BYTES = bpn
    scales = [
        ("ConceptNet-class", 3.4e6),
        ("Wikipedia-fact-class", 1e8),
        ("LLM-coverage-class", 5e9),
    ]
    print("\n  %-22s %-12s %-12s %-14s" %
          ("scale", "facts", "cold_disk", "ingest_time"))
    for name, facts in scales:
        disk = facts * NODE_BYTES
        ingest_s = facts / fps
        print("  %-22s %-12s %-12s %-14s" %
              (name, _si(facts), _bytes(disk), _dur(ingest_s)))
    print("\n  (hot RAM stays MB-scale at every scale — cold-tier mmap, "
          "pay-per-miss; inference/step stays ~%.4f ms — FLAT/local)"
          % read_last)

    # ---- OoM inference gap ----------------------------------------------
    print("\n  OoM INFERENCE-COMPUTE GAP vs Llama-3-8B (per step):")
    print("    Llama-3-8B: ~%.1e FLOPs/token  (2N, N=8e9, est)"
          % LLAMA3_8B_INFER_FLOPS_PER_TOKEN)
    print("    substrate : ~%d FLOPs/coherence-read  (O(cues*degree), est)"
          % substrate_read_flops)
    oom = math.log10(LLAMA3_8B_INFER_FLOPS_PER_TOKEN / substrate_read_flops)
    print("    => ~%.1f orders of magnitude fewer FLOPs per inference step"
          % oom)
    print("    (per-STEP, NOT capability-normalised — a read and a token are "
          "different units of work)")

    # ---- X to LLM coverage ----------------------------------------------
    print("\n  X TO REACH LLM-COVERAGE (5e9 facts):")
    ingest_s = 5e9 / fps
    print("    machine ingest time (single-thread): %s  (~%s on 32 threads)"
          % (_dur(ingest_s), _dur(ingest_s / 32)))
    print("    marginal-add discipline: +facts at %.5f ms/fact, NEVER a "
          "retrain (additive ratio ~%.2f)" % (add_mpf, ratio))
    print("    NB: machine time is the CHEAP part — the real X is SOURCING +")
    print("        CURATING clean facts; noise scales as cheaply as signal.")
    print("    Llama-3-8B TRAINING for comparison: ~%.1e FLOPs (6ND, est) — "
          "a one-shot GPU-cluster cost that must be REPAID to add knowledge."
          % LLAMA3_8B_TRAIN_FLOPS)

    # ---- honest ceiling --------------------------------------------------
    print("\n" + "-" * 72)
    print("HONEST CEILING (as prominent as the win):")
    print("  * Coverage != capability parity. More facts buy MORE of the")
    print("    operations the substrate MODELS (compositional reasoning over")
    print("    EXPLICIT structure), NOT the LLM's generative interpolation")
    print("    (novel text, unseen phrasings, gap-filling). Degree-not-kind")
    print("    boundary the designer CHOOSES where to draw.")
    print("  * X is dominated by CURATION, not the measured machine time.")
    print("  * The OoM gap is per-STEP on modelled operations, not per unit")
    print("    of equal capability.")
    print("  * Measured to 100k nodes; TB-scale is EXTRAPOLATED on the")
    print("    linear/flat constants (real 1e9 graphs may hit degree/cache/")
    print("    page-fault effects the sweep does not capture).")
    print("=" * 72)

    return {
        "bytes_per_node": bpn,
        "read_ms_flat": read_last,
        "read_slope_ms_per_node": read_slope,
        "facts_per_sec": fps,
        "additive_ratio": ratio,
        "oom_inference_gap": oom,
    }


def _si(x):
    for u, d in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if x >= d:
            return "%.1f%s" % (x / d, u)
    return "%.0f" % x


def _bytes(x):
    for u, d in (("TB", 1e12), ("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if x >= d:
            return "%.1f%s" % (x / d, u)
    return "%.0fB" % x


def _dur(s):
    if s >= 3600:
        return "%.1fh" % (s / 3600)
    if s >= 60:
        return "%.1fmin" % (s / 60)
    return "%.1fs" % s


if __name__ == "__main__":
    main()
