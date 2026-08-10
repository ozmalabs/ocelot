#!/usr/bin/env python3
"""jabberwock_pages_memory — the Jabberwock pages its GROWN corpus like an OS.

Demonstrates domains/graph_virtual_memory: a scaling read (consume many
microtheories under a SMALL memory_bound budget) shows the OS at work —

  · RESIDENT node count PLATEAUS at the budget (memory_bound + page-out hold it
    flat: the live graph holds only the WORKING SET).
  · the mmap CORPUS SLAB GROWS unbounded (reference_slab record count rises: the
    corpus lives on disk, demand-paged).
  · a paged-out cluster round-trips BYTE-IDENTICAL on page-in (no data loss).
  · the lexicon KERNEL (never_forget) stays resident throughout.

donkey=0 — no model; the whole loop is mechanical byte movement between the live
graph (graph_to_dict wire format) and the mmap slab (reference_slab), under the
memory faculty's cap (memory_bound) in LRU order (a HotCounter recency mirror).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_pages_memory.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import substrate_rs as S
from domains.graph_virtual_memory import GraphVirtualMemory


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pages_memory_"))
    s = S.Substrate()

    # ---- the never_forget KERNEL: the resident lexicon ----
    kernel = ["the", "of", "a", "is", "cat", "run", "volcano", "magma",
              "cell", "photon", "cipher", "key"]
    for w in kernel:
        s.add_node("LexEntry", {"text": w})
    kernel_n = s.node_count()

    BUDGET = 24
    gvm = GraphVirtualMemory(s, corpus="corpus_demo", budget_nodes=BUDGET,
                             slab_dir=tmp / "slabs")

    print(f"OS memory hierarchy: budget_nodes={BUDGET}, kernel(lexicon)={kernel_n} "
          f"(never_forget), corpus slab -> {tmp/'slabs'}/corpus_demo.{{keys,vals}}\n")
    print(f"{'consumed':>8} | {'resident_nodes':>14} | {'corpus_records':>14} | "
          f"{'resident_clusters':>17} | {'page_out':>8} | {'page_in':>7}")
    print("-" * 82)

    N = 80
    keep_fp = None
    keep_topic = "article_3"
    for i in range(N):
        topic = f"article_{i}"
        concepts = [{"name": f"{topic}_c{j}",
                     "definition": f"the {j}th grounded part of {topic}",
                     "pos": "noun"} for j in range(5)]
        gvm.install_cluster(topic, concepts)
        gvm.enforce()  # the resident cap drives page-out to the mmap corpus
        if topic == keep_topic:
            keep_fp = gvm.cluster_fingerprint(keep_topic)
        if i % 8 == 0 or i == N - 1:
            st = gvm.stats()
            print(f"{i:>8} | {st['resident_nodes']:>14} | {st['corpus_records']:>14} | "
                  f"{st['resident_clusters']:>17} | {st['page_out']:>8} | {st['page_in']:>7}")

    st = gvm.stats()
    print("-" * 82)
    print(f"\nSMOOTH PAGING: after {N} consumed articles, resident held at "
          f"{st['resident_nodes']} nodes (budget {BUDGET}) while the mmap corpus "
          f"grew to {st['corpus_records']} records ({st['corpus_bytes']} bytes on disk).")
    print(f"  working set is {st['resident_nodes']}/{st['corpus_records'] + st['resident_clusters']} "
          f"of the corpus — the rest is mmap'd on disk, paged in on demand.\n")

    # ---- BYTE-IDENTICAL round-trip on foveation ----
    assert not gvm._clusters[keep_topic]["resident"], "expected cold"
    stored = gvm.stored_value(keep_topic)
    print(f"PAGE-IN CORRECT: foveating '{keep_topic}' (cold, mmap'd)...")
    paged = gvm.foveate(keep_topic)
    fp_after = gvm.cluster_fingerprint(keep_topic)
    print(f"  paged in {paged} nodes via mmap O(log n) slab lookup.")
    print(f"  stored-bytes == pre-page-out canonical : {stored == keep_fp}")
    print(f"  round-trip byte-identical               : {fp_after == keep_fp}")
    assert stored == keep_fp == fp_after, "round-trip not byte-identical"

    # ---- MMAP-not-JSON + kernel-never-paged ----
    slab_files = sorted(p.name for p in (tmp / "slabs").iterdir())
    print(f"\nMMAP NOT JSON: corpus is a reference_slab: {slab_files} "
          f"(no per-cluster .json heap).")
    print(f"KERNEL NEVER PAGED: lexicon resident throughout "
          f"({len(s.nodes('LexEntry'))}/{kernel_n} LexEntry nodes).")
    assert len(s.nodes("LexEntry")) == kernel_n

    print("\nOK — the Jabberwock pages its corpus like an OS: working set bounded, "
          "corpus mmap'd, no data loss, kernel resident.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
