"""BLOB_EDGE_SD_LOOP -- pins the correspondence-persistence mechanism.

PREREG: `docs/research/engine_substrate/BLOB_EDGE_SD_LOOP_PREREG.md`.
RESULTS: `docs/research/engine_substrate/BLOB_EDGE_SD_LOOP_RESULTS.md`.

`domains.reflective_faculty._shared_shape` (UNCHANGED by this rung) already
collapses two signatures onto shared held `RelationCue` structure. This file
pins the NEW layer on top: `record_correspondence` mints a `BlobEdge` the
first time a distinct `transform_key` is seen and RECOGNIZES (no new node)
every subsequent correspondence sharing that same key -- the sd loop's
recognize/mint duality reapplied to correspondence persistence, gated at
collapse time (not a recurrence threshold), per `seeds/blob_edge_correspondence.json`'s
`blob_mint`/`blob_recognize`/`blob_no_collapse` rules.
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
from domains import reflective_faculty as rf                # noqa: E402


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def cues():
    rv = json.load(open(os.path.join(ROOT, "seeds", "relation_vocabulary.json")))
    return {c["attrs"]["name"]: json.loads(c["attrs"]["relation"]) for c in rv.get("nodes", [])
            if c.get("type") == "RelationCue"}


def _mk_shape_signature(agent, name, sig, kind="math"):
    sub = agent.s
    return sub.add_node("ShapeSignature", {
        "name": name, "kind": kind, "signature": json.dumps(sig),
    })


# --------------------------------------------------------------------------- #
# 1. `_shared_shape` itself is byte-unchanged -- this rung is additive only.
# --------------------------------------------------------------------------- #

def test_shared_shape_return_value_is_unchanged(agent, cues):
    sig_a = [cues["build_from_prior"], cues["self_reference"], cues["base_case"]]
    sig_b = [cues["self_reference"], cues["bounded"], cues["build_from_prior"]]
    res, fixed = rf._shared_shape(agent, sig_a, sig_b)
    assert fixed > 0
    assert list(cues["self_reference"]) in res


# --------------------------------------------------------------------------- #
# 2. Mint fires exactly once for a genuinely novel correspondence pattern;
#    a BlobEdge appears, linked to both real endpoints.
# --------------------------------------------------------------------------- #

def test_mint_fires_once_for_a_novel_pattern(agent, cues):
    sub = agent.s
    assert sub.nodes("BlobEdge") == []
    na = _mk_shape_signature(agent, "probe_a", [cues["self_reference"], cues["build_from_prior"]])
    nb = _mk_shape_signature(agent, "probe_b", [cues["self_reference"], cues["build_from_prior"], cues["bounded"]])
    corr = rf.record_correspondence(agent, na, [cues["self_reference"], cues["build_from_prior"]],
                                     nb, [cues["self_reference"], cues["build_from_prior"], cues["bounded"]])
    assert corr["persisted"] is True
    assert corr["status"] == "minted"
    blobs = sub.nodes("BlobEdge")
    assert len(blobs) == 1
    at = sub.node(blobs[0])["attrs"]
    assert at["transform_key"] == corr["transform_key"]
    # mechanical structural check: the minted BlobEdge is edged to BOTH real endpoints
    assert sub.has_edge(blobs[0], "links_a", na)
    assert sub.has_edge(blobs[0], "links_b", nb)
    receipts = [sub.node(n)["attrs"] for n in
                sub.nodes("NativeReflectiveFacultyReceipt")
                if sub.node(n)["attrs"].get("cluster") ==
                "reflective_faculty.correspondence_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


# --------------------------------------------------------------------------- #
# 3. Recognize fires on a repeat of the SAME transform_key -- zero new BlobEdge.
# --------------------------------------------------------------------------- #

def test_recognize_fires_with_zero_blob_edge_growth_on_a_repeat(agent, cues):
    sub = agent.s
    na = _mk_shape_signature(agent, "probe_c", [cues["self_reference"], cues["build_from_prior"]])
    nb = _mk_shape_signature(agent, "probe_d", [cues["self_reference"], cues["build_from_prior"], cues["bounded"]])
    sig_a = [cues["self_reference"], cues["build_from_prior"]]
    sig_b = [cues["self_reference"], cues["build_from_prior"], cues["bounded"]]
    first = rf.record_correspondence(agent, na, sig_a, nb, sig_b)
    assert first["status"] == "minted"
    n_blobs_after_first = len(sub.nodes("BlobEdge"))

    # A DIFFERENT pair, same shared axes -> the SAME transform_key.
    nc = _mk_shape_signature(agent, "probe_e", [cues["self_reference"], cues["build_from_prior"], cues["base_case"]])
    nd = _mk_shape_signature(agent, "probe_f", [cues["self_reference"], cues["build_from_prior"]])
    second = rf.record_correspondence(agent, nc, [cues["self_reference"], cues["build_from_prior"], cues["base_case"]],
                                       nd, [cues["self_reference"], cues["build_from_prior"]])
    assert second["transform_key"] == first["transform_key"]
    assert second["status"] == "recognized"
    assert len(sub.nodes("BlobEdge")) == n_blobs_after_first, "recognize must not grow BlobEdge count"


# --------------------------------------------------------------------------- #
# 4. No shared axis at all -> no_collapse, no BlobEdge, no error.
# --------------------------------------------------------------------------- #

def test_no_collapse_for_a_genuinely_disjoint_pair(agent):
    sub = agent.s
    na = sub.add_node("ShapeSignature", {"name": "probe_disjoint_a", "kind": "math",
                                          "signature": json.dumps([["scan"], ["gate"]])})
    nb = sub.add_node("ShapeSignature", {"name": "probe_disjoint_b", "kind": "faculty",
                                          "signature": json.dumps([["focus"], ["route"]])})
    corr = rf.record_correspondence(agent, na, [["scan"], ["gate"]], nb, [["focus"], ["route"]])
    assert corr["persisted"] is True
    assert corr["status"] == "no_collapse"
    assert sub.nodes("BlobEdge") == []


# --------------------------------------------------------------------------- #
# 5. Real-corpus end-to-end: `_run_math_bridge` wiring, called twice.
# --------------------------------------------------------------------------- #

def test_real_bridge_call_persists_and_second_call_recognizes(agent):
    sub = agent.s
    assert sub.nodes("Correspondence") == []
    assert sub.nodes("BlobEdge") == []
    res1 = rf._run_math_bridge(agent, None)
    n_corr_1 = len(sub.nodes("Correspondence"))
    n_blob_1 = len(sub.nodes("BlobEdge"))
    assert n_corr_1 > 0
    assert n_blob_1 > 0
    res2 = rf._run_math_bridge(agent, None)
    n_corr_2 = len(sub.nodes("Correspondence"))
    n_blob_2 = len(sub.nodes("BlobEdge"))
    assert n_corr_2 == 2 * n_corr_1, "the witness computation itself still recomputes every call"
    assert n_blob_2 == n_blob_1, "the SECOND call must recognize, not re-mint -- zero BlobEdge growth"
    assert res1["connection"] == res2["connection"], "the decision itself is unaffected by persistence"


# --------------------------------------------------------------------------- #
# 6. No real node id on one side -> degrades honestly, no exception.
# --------------------------------------------------------------------------- #

def test_missing_node_id_degrades_without_persisting(agent, cues):
    sig_a = [cues["self_reference"]]
    sig_b = [cues["self_reference"], cues["build_from_prior"]]
    corr = rf.record_correspondence(agent, None, sig_a, None, sig_b)
    assert corr["persisted"] is False
    assert corr["fixed"] >= 0  # `_shared_shape`'s own honest value, still returned
