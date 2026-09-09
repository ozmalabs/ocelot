#!/usr/bin/env python3
"""Newer models are more graph-like — measure across models of increasing recency.

See docs/research/psychology_affect/NEWER_MODELS_MORE_GRAPHLIKE_PREREG.md.

Runs the SAME graph-likeness battery (FFN concept alignment+purity, kNN
reciprocity, distillation survival under vector quantisation) on every
available model — identical work-vocab window, seed concepts, k, bit-depths,
RNG seed — and prints a side-by-side table with the recency order.

Models (older -> newer):
  gemma3:4b        (ollama GGUF)
  Qwen3-1.7B       (local HF safetensors)
  Qwen3.8-27B      (local HF safetensors, Aug 2026, hybrid SSM/attention)

Any model absent is skipped (reported). n=3 is a directional data point, NOT a
trend; size/tokenizer confounds are NOT controlled — stated in the verdict.
"""

from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

from domains import model_active_extraction as mae  # noqa: E402

WORK_DIR = "/applications/data/model_graph_work"
CONCEPTS = {
    "animal": ["dog", "cat", "animal", "pet"],
    "number": ["one", "two", "three", "number"],
    "colour": ["red", "blue", "green", "colour"],
    "food": ["bread", "fruit", "meat", "food"],
    "country": ["france", "germany", "japan", "country"],
}
WORK_VOCAB = 15000

# (label, spec, recency_rank) — spec is an ollama tag or a local dir.
MODELS = [
    ("gemma3:4b", "gemma3:4b", 1),
    ("Qwen3-1.7B", os.path.join(WORK_DIR, "Qwen3-1.7B"), 2),
    ("Qwen3.8-27B", os.path.join(WORK_DIR, "Qwen3.8-27B"), 3),
]


def _available(spec):
    if os.path.isdir(spec):
        # HF dir is usable once the index + all shards are present
        idx = os.path.join(spec, "model.safetensors.index.json")
        if not os.path.isfile(idx):
            return os.path.isfile(os.path.join(spec, "model.safetensors"))
        import json
        shards = set(json.load(open(idx))["weight_map"].values())
        return all(os.path.isfile(os.path.join(spec, s)) for s in shards)
    return mae.resolve_gguf_blob(spec) is not None


def main():
    print("=" * 74)
    print("NEWER MODELS ARE MORE GRAPH-LIKE — graph-likeness battery")
    print("=" * 74)

    reports = []
    for label, spec, rank in MODELS:
        if not _available(spec):
            print("\n[%s] SKIPPED (not fully present)" % label)
            continue
        print("\n[%s] loading + measuring ..." % label)
        t0 = time.perf_counter()
        try:
            lm = mae.load_model(spec, work_vocab=WORK_VOCAB)
            rep = mae.graphlike_report(lm, CONCEPTS, rng=random.Random(0))
        except Exception as e:
            print("  FAILED: %s" % e)
            continue
        rep["_label"] = label
        rep["_rank"] = rank
        reports.append(rep)
        print("  done in %.0fs" % (time.perf_counter() - t0))

    if len(reports) < 2:
        print("\nNeed >=2 models present to compare. Have %d." % len(reports))
        return {"reports": reports}

    reports.sort(key=lambda r: r["_rank"])

    # ---- side-by-side table --------------------------------------------
    print("\n" + "=" * 74)
    print("SIDE-BY-SIDE (older -> newer)")
    cols = [r["_label"] for r in reports]
    print("  %-22s %s" % ("metric", "  ".join("%12s" % c for c in cols)))

    def row(name, getter, fmt="%12.3f"):
        vals = [getter(r) for r in reports]
        print("  %-22s %s" % (name, "  ".join(fmt % v for v in vals)))
        return vals

    a = row("ffn_alignment", lambda r: r["ffn_alignment"])
    p = row("ffn_purity", lambda r: r["ffn_purity"])
    rec = row("knn_reciprocity", lambda r: r["knn_reciprocity"])
    s8 = row("distill_survival@8b", lambda r: r["distill_survival"].get(8, 0))
    s4 = row("distill_survival@4b", lambda r: r["distill_survival"].get(4, 0))
    s3 = row("distill_survival@3b", lambda r: r["distill_survival"].get(3, 0))

    print("\n  --- ENCODED STRUCTURE (codec-independent; LOWER = more "
          "concentrated / graph-like) ---")
    prd = row("pr_over_d", lambda r: r["structure"]["pr_over_d"])
    erd = row("erank_over_d", lambda r: r["structure"]["erank_over_d"])

    # ---- verdict: is each metric monotone with recency? ----------------
    print("\n" + "-" * 74)
    print("MONOTONE-WITH-RECENCY (newer >= older across the ordered models)?")

    def monotone(vals):
        return all(vals[i] <= vals[i + 1] + 1e-9 for i in range(len(vals) - 1))

    metrics = [("ffn_alignment", a), ("ffn_purity", p), ("knn_reciprocity", rec),
               ("distill_survival@8b", s8), ("distill_survival@4b", s4),
               ("distill_survival@3b", s3)]
    n_mono = 0
    for name, vals in metrics:
        m = monotone(vals)
        n_mono += int(m)
        print("  %-22s %s  %s" % (name, "MONOTONE ↑" if m else "not monotone",
                                  [round(v, 3) for v in vals]))

    print("\n" + "=" * 74)
    print("VERDICT: %d/%d graph-likeness metrics increase monotonically with "
          "recency" % (n_mono, len(metrics)))
    print("  (n=%d models — a DIRECTIONAL data point, NOT a trend; size / "
          "tokenizer / training-corpus confounds are NOT controlled.)"
          % len(reports))
    print("=" * 74)
    return {"reports": reports, "n_monotone": n_mono, "n_metrics": len(metrics)}


if __name__ == "__main__":
    main()
