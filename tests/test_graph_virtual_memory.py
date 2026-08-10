"""Gate for domains/graph_virtual_memory — OS-style demand paging of the grown
corpus to the reference_slab mmap store, under memory_bound + LRU + never_forget.

DISCRIMINATIVE, donkey=0 (no model; the whole loop is mechanical byte movement):
  · SMOOTH PAGE OUT/IN     — resident PLATEAUS at the budget while the mmap
                              corpus GROWS unbounded (the OS working).
  · PAGE-IN IS CORRECT     — a paged-out cluster round-trips BYTE-IDENTICAL.
  · MMAP, NOT JSON-HACK    — the corpus target is a reference_slab (.keys/.vals
                              mmap), not a heap of JSON files; kernel never paged.
  · RESIDENT BOUNDED       — N clusters under a small budget keeps resident <= cap.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

import substrate_rs as S
from domains.graph_virtual_memory import GraphVirtualMemory, canonicalize


def _fresh(tmp: Path, *, budget_nodes: int, corpus: str = "corpus_gate"):
    s = S.Substrate()
    # a never_forget KERNEL: the resident lexicon.
    for w in ("the", "of", "cat", "run", "volcano", "magma"):
        s.add_node("LexEntry", {"text": w})
    gvm = GraphVirtualMemory(s, corpus=corpus, budget_nodes=budget_nodes,
                             slab_dir=tmp / "slabs")
    return s, gvm


def _consume(gvm, i: int, n_concepts: int = 5):
    topic = f"article_{i}"
    concepts = [{"name": f"{topic}_c{j}", "definition": f"the {j}th part of {topic}",
                 "pos": "noun"} for j in range(n_concepts)]
    gvm.install_cluster(topic, concepts)
    gvm.enforce()
    return topic


# --------------------------------------------------------------------------- #

def test_smooth_page_out_in_resident_plateaus_corpus_grows():
    """HEADLINE: resident node count PLATEAUS at the budget (memory_bound +
    page-out holding it flat) while the mmap CORPUS SLAB GROWS unbounded."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        s, gvm = _fresh(tmp, budget_nodes=20)
        trace = []
        for i in range(60):
            _consume(gvm, i)
            st = gvm.stats()
            trace.append((st["resident_nodes"], st["corpus_records"]))

        residents = [r for r, _ in trace]
        corpus = [c for _, c in trace]

        # RESIDENT FLAT: once warmed, resident never exceeds the budget and
        # stops growing (plateau) — its spread over the back half is ~0.
        back = residents[len(residents) // 2:]
        assert max(back) <= gvm.budget_nodes, (max(back), gvm.budget_nodes)
        assert max(back) - min(back) <= 6, back  # one cluster's worth of jitter

        # CORPUS GROWS UNBOUNDED: strictly rising record count, ending large.
        assert corpus[-1] > corpus[len(corpus) // 2] > corpus[2], corpus[::10]
        assert corpus[-1] >= 40, corpus[-1]

        # the plateau is well below the corpus — the working set is a fraction.
        assert residents[-1] < corpus[-1]


def test_page_in_is_byte_identical():
    """A paged-OUT microtheory, paged back IN on foveation, round-trips
    BYTE-IDENTICAL (no data loss across page-out -> page-in)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        s, gvm = _fresh(tmp, budget_nodes=20)

        # capture the canonical fingerprint of article_1 while resident.
        _consume(gvm, 0)
        topic = _consume(gvm, 1)
        fp_before = gvm.cluster_fingerprint(topic)
        assert fp_before is not None

        # drive it cold: consume enough that article_1 pages out.
        for i in range(2, 30):
            _consume(gvm, i)
        assert not gvm._clusters[topic]["resident"], "expected article_1 paged out"

        # the stored slab value is byte-identical to the pre-page-out canonical.
        stored = gvm.stored_value(topic)
        assert stored == fp_before, "corpus bytes != pre-page-out canonical"

        # page it IN on foveation; the re-installed cluster re-canonicalizes to
        # the SAME bytes -> concepts/edges/attrs all survived.
        paged = gvm.foveate(topic)
        assert paged == 6, paged  # 1 microtheory + 5 concepts
        fp_after = gvm.cluster_fingerprint(topic)
        assert fp_after == fp_before, "round-trip not byte-identical"


def test_mmap_not_json_hack_and_kernel_never_paged():
    """The corpus page-out target is the reference_slab mmap store (.keys/.vals),
    mmap-read at page-in — NOT a heap of JSON files. The lexicon KERNEL
    (never_forget) is never paged out."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        s, gvm = _fresh(tmp, budget_nodes=16)
        kernel_before = len(s.nodes("LexEntry"))

        for i in range(40):
            _consume(gvm, i)

        # the corpus is a reference_slab: exactly a .keys + .vals pair.
        assert gvm.corpus_is_mmap_slab()
        slab_dir = tmp / "slabs"
        files = sorted(p.name for p in slab_dir.iterdir())
        assert files == ["corpus_gate.keys", "corpus_gate.vals"], files
        # NOT a heap of per-cluster JSON files.
        assert not any(p.suffix == ".json" for p in slab_dir.iterdir())

        # page-in reads THROUGH the mmap slab: foveate a paged-out topic and get
        # its bytes back from the mmap store (proves the read side is the slab).
        cold = next(t for t, c in gvm._clusters.items() if not c["resident"])
        assert gvm.stored_value(cold) is not None
        assert gvm.foveate(cold) == 6
        # kernel: every lexeme still resident (never registered, never evicted).
        assert len(s.nodes("LexEntry")) == kernel_before == 6
        # and none of the kernel ids were ever put in a cluster.
        for c in gvm._clusters.values():
            for kn in s.nodes("LexEntry"):
                kid = kn.value if hasattr(kn, "value") else int(kn)
                assert kid not in c["ids"]


def test_resident_bounded_under_load():
    """Consuming N microtheories under a small budget keeps resident <= budget
    the WHOLE time (does not OOM / grow unbounded)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        s, gvm = _fresh(tmp, budget_nodes=24)
        peak = 0
        for i in range(100):
            _consume(gvm, i)
            peak = max(peak, gvm.stats()["resident_nodes"])
        assert peak <= gvm.budget_nodes, (peak, gvm.budget_nodes)
        # 100 consumed, but only a handful resident; the rest are mmap'd.
        assert gvm.stats()["total_clusters"] == 100
        assert gvm.stats()["resident_clusters"] < 6
        assert gvm.corpus_records() >= 90


def test_canonicalize_is_id_independent():
    """The canonical wire form is independent of the live graph's global id
    counter — the property that makes the byte-identity round-trip hold."""
    nodes_a = [{"id": 0, "type": "Microtheory", "attrs": {"topic": "t"}},
               {"id": 1, "type": "Concept", "attrs": {"name": "a"}},
               {"id": 2, "type": "Concept", "attrs": {"name": "b"}}]
    edges_a = [{"src": 0, "type": "has_concept", "tgt": 1, "attrs": {}},
               {"src": 0, "type": "has_concept", "tgt": 2, "attrs": {}}]
    # same cluster, different global ids + different node order.
    nodes_b = [{"id": 92, "type": "Concept", "attrs": {"name": "b"}},
               {"id": 90, "type": "Microtheory", "attrs": {"topic": "t"}},
               {"id": 91, "type": "Concept", "attrs": {"name": "a"}}]
    edges_b = [{"src": 90, "type": "has_concept", "tgt": 91, "attrs": {}},
               {"src": 90, "type": "has_concept", "tgt": 92, "attrs": {}}]
    assert canonicalize(nodes_a, edges_a) == canonicalize(nodes_b, edges_b)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
