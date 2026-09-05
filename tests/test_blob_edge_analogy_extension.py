"""BLOB_EDGE_ANALOGY_EXTENSION -- pins the correspondence-persistence
mechanism at `analogical_thinking.py::_pair_witness`'s real call site.

PREREG: `docs/research/engine_substrate/BLOB_EDGE_ANALOGY_EXTENSION_PREREG.md`.
RESULTS: `docs/research/engine_substrate/BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md`.

Extends the SAME `seeds/blob_edge_correspondence.json` recognize/mint rules
(`blob_mint`/`blob_recognize`/`blob_no_collapse`, unedited, reused verbatim)
the predecessor rung wired at `reflective_faculty.py::_run_math_bridge`, to
`_pair_witness`'s real operands here: two `Concept` graph nodes. The Gamma
extension (`seeds/blob_edge_concept_correspondence.json`) is additive-only.

NOTE (analogy-search migration): the SEARCH `find_analogies` used to run in
Python is now the first-class graph seed `seeds/analogy_search.json`
(`domains/analogy_search.py`), per `SHAPE_AUDIT.md` §2.4. This file exercises
the RETAINED `_legacy_find_analogies`, which is the unchanged pure-Python
`_compute_analogy`/`_pair_witness` faculty that still drives the
correspondence-persistence machinery under test here — so the call sites below
use `at._legacy_find_analogies`, not the public (now graph-delegating)
`at.find_analogies`.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from domains import analogical_thinking as at               # noqa: E402


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _mt(sub, name):
    return sub.add_node("Microtheory", {"name": name})


def _concept(sub, mt, name, definition, category="c"):
    c = sub.add_node("Concept", {"name": name, "definition": definition,
                                  "category": category})
    sub.add_edge(mt, "has_concept", c)
    return c


def _pair(results, sc, tc):
    for r in results:
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return r
    return None


# --------------------------------------------------------------------------- #
# 1. `_pair_witness` itself is byte-unchanged -- this rung is additive only.
# --------------------------------------------------------------------------- #

def test_pair_witness_return_value_is_unchanged(agent):
    sub = agent.s
    vec_a = [["role:scheduler", "x"], ["role:gate", at._ABSENT], ["category", "c"]]
    vec_b = [["role:scheduler", "x"], ["role:gate", "y"], ["category", "c"]]
    out = at._pair_witness(sub, vec_a, vec_b)
    assert set(out) == {"shared", "name_shared", "fixed_count", "transform"}
    assert out["fixed_count"] > 0
    assert ("role:scheduler", "x") in out["shared"]
    assert ("category", "c") in out["shared"]


# --------------------------------------------------------------------------- #
# 2. Mint fires once for a genuinely novel correspondence pattern found via
#    the REAL `find_analogies` call site -- a BlobEdge appears, linked to
#    both real Concept endpoints.
# --------------------------------------------------------------------------- #

def test_mint_fires_once_for_a_novel_pair_via_find_analogies(agent):
    sub = agent.s
    n_blob_before = len(sub.nodes("BlobEdge"))
    src, tgt = _mt(sub, "aext_src_1"), _mt(sub, "aext_tgt_1")
    _concept(sub, src, "aext_gate_unit", "aext a component of the machine")
    _concept(sub, tgt, "aext_gate_stage", "aext a stage of the machine")
    res = at._legacy_find_analogies(sub, "aext_src_1", ["aext_tgt_1"], order_n=2)
    r = _pair(res, "aext_gate_unit", "aext_gate_stage")
    assert r is not None
    assert r["struct_shared"] >= 1, "the pair must be structurally aligned for a Correspondence to be worth writing"

    corrs = sub.nodes("Correspondence")
    assert len(corrs) >= 1
    blobs = sub.nodes("BlobEdge")
    assert len(blobs) == n_blob_before + 1, "exactly one NEW BlobEdge for a genuinely novel pattern"
    new_blob = [b for b in blobs if b not in set()][-1]
    bat = sub.node(new_blob)["attrs"]
    # the minted BlobEdge links two Concept nodes (not ShapeSignature -- the
    # Gamma extension is what makes this admissible).
    concept_a = [n for n in sub.nodes("Concept") if sub.node(n)["attrs"].get("name") == "aext_gate_unit"][0]
    concept_b = [n for n in sub.nodes("Concept") if sub.node(n)["attrs"].get("name") == "aext_gate_stage"][0]
    linked = any(sub.has_edge(b, "links_a", concept_a) and sub.has_edge(b, "links_b", concept_b)
                 for b in blobs)
    assert linked, "the minted BlobEdge must link the two REAL Concept endpoints"


# --------------------------------------------------------------------------- #
# 3. Recognize fires (zero new BlobEdge) for a DIFFERENT pair that realises
#    the SAME held structural pattern.
# --------------------------------------------------------------------------- #

def test_recognize_fires_with_zero_blob_edge_growth_on_a_repeat_pattern(agent):
    sub = agent.s
    src, tgt = _mt(sub, "aext_src_2"), _mt(sub, "aext_tgt_2")
    _concept(sub, src, "aext_gate_unit", "aext a component of the machine")
    _concept(sub, tgt, "aext_gate_stage", "aext a stage of the machine")
    _concept(sub, src, "aext_widget_one", "aext this thing will gate the flow")
    _concept(sub, tgt, "aext_widget_two", "aext this other thing will gate the flow")
    at._legacy_find_analogies(sub, "aext_src_2", ["aext_tgt_2"], order_n=2)
    n_blob_after_first_call = len(sub.nodes("BlobEdge"))
    n_corr_after_first_call = len(sub.nodes("Correspondence"))
    assert n_blob_after_first_call >= 1

    # Same source/target Mts, same pairs -> the SAME transform_key(s) recur.
    at._legacy_find_analogies(sub, "aext_src_2", ["aext_tgt_2"], order_n=2)
    assert len(sub.nodes("BlobEdge")) == n_blob_after_first_call, \
        "a repeated correspondence pattern must RECOGNIZE, not re-mint"
    assert len(sub.nodes("Correspondence")) > n_corr_after_first_call, \
        "the witness computation itself still recomputes every call (Correspondence count grows)"


# --------------------------------------------------------------------------- #
# 4. Real-corpus, no-duplicate-key GO bar (PREREG Sec5/Sec9): every distinct
#    transform_key produces EXACTLY one BlobEdge, never more, even though
#    hundreds of `_pair_witness` calls happen inside ONE `find_analogies`
#    invocation. Uses the real `mathematics` Mt (112 real pair_witness calls
#    measured in the PREREG) -- smaller than `computer_architecture` (7970
#    calls, ~40s) to keep the suite fast; the full-scale number is reported
#    in RESULTS from a standalone run, not repeated here.
# --------------------------------------------------------------------------- #

def test_real_corpus_batch_has_no_duplicate_blob_edges(agent):
    sub = agent.s
    assert sub.nodes("Correspondence") == []
    assert sub.nodes("BlobEdge") == []
    res = at._legacy_find_analogies(sub, "mathematics", ["mathematics"], order_n=4)
    assert len(res) > 0
    blobs = sub.nodes("BlobEdge")
    keys = [sub.node(b)["attrs"].get("transform_key") for b in blobs]
    assert len(keys) == len(set(keys)), "every BlobEdge must carry a DISTINCT transform_key -- no duplicate mints"
    assert len(sub.nodes("Correspondence")) > len(blobs), \
        "at least one pair must have RECOGNIZED an already-minted pattern (real pooling)"


# --------------------------------------------------------------------------- #
# 5. Repeat-call demonstration: BlobEdge count flat on the second call;
#    Correspondence count grows; the RETURNED analogy list is byte-identical.
# --------------------------------------------------------------------------- #

def test_repeat_call_recognizes_and_decision_is_byte_identical(agent):
    sub = agent.s
    res1 = at._legacy_find_analogies(sub, "mathematics", ["mathematics"], order_n=4)
    n_corr_1 = len(sub.nodes("Correspondence"))
    n_blob_1 = len(sub.nodes("BlobEdge"))
    res2 = at._legacy_find_analogies(sub, "mathematics", ["mathematics"], order_n=4)
    n_corr_2 = len(sub.nodes("Correspondence"))
    n_blob_2 = len(sub.nodes("BlobEdge"))
    assert n_corr_2 == 2 * n_corr_1
    assert n_blob_2 == n_blob_1, "second call must recognize throughout -- zero BlobEdge growth"
    assert res1 == res2, "persistence must never change the analogy verdict"


# --------------------------------------------------------------------------- #
# 6. No real node id on one side -> degrades honestly, no exception, no write.
# --------------------------------------------------------------------------- #

def test_missing_node_id_degrades_without_persisting(agent):
    sub = agent.s
    n_corr_before = len(sub.nodes("Correspondence"))
    witness = {"shared": [("role:scheduler", "x")], "name_shared": 0,
               "fixed_count": 1, "transform": ()}
    out = at.record_pair_correspondence(sub, None, None, witness)
    assert out is None
    assert len(sub.nodes("Correspondence")) == n_corr_before
