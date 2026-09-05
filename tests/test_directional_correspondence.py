"""DIRECTIONAL_CORRESPONDENCE -- candidate bridge 2
(REASONING_FACILITY_BRIDGE_RESULTS.md Sec3, "analogical correspondence -> CAN
hypothesis", NO-GO-BY-DESIGN there because `_pair_witness`'s own
{shared, name_shared, fixed_count, transform} carries no directional signal.
This rung builds the real representational work that finding named: a
genuinely asymmetric signal (structural-elaboration richness) grounding a
NEW node type, `DirectionalCorrespondence`, plus an explicit, never-automatic
promotion into a real `knowledge_logical` schema.

PREREG: `docs/research/engine_substrate/DIRECTIONAL_CORRESPONDENCE_PREREG.md`.
RESULTS: `docs/research/engine_substrate/DIRECTIONAL_CORRESPONDENCE_RESULTS.md`.

NOTE (analogy-search migration): the analogy SEARCH is now the first-class
graph seed `seeds/analogy_search.json` (`domains/analogy_search.py`), per
`SHAPE_AUDIT.md` §2.4. This file exercises the RETAINED
`_legacy_find_analogies` — the unchanged Python faculty that drives the
`DirectionalCorrespondence` persistence under test — so call sites use
`at._legacy_find_analogies`, not the public graph-delegating `at.find_analogies`.
"""
from __future__ import annotations

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
from domains import propositional_deduction as pd           # noqa: E402
from domains import inference_generation as ig              # noqa: E402
from domains import situation_model_reader as smr           # noqa: E402


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


def _find_directional_corr(sub, node_a, node_b):
    for c in sub.nodes("DirectionalCorrespondence"):
        pair = set(sub.neighbours(c, "about_a")) | set(sub.neighbours(c, "about_b"))
        if {node_a, node_b} <= pair:
            return c
    return None


# --------------------------------------------------------------------------- #
# 1. `_axis_richness` -- plain arithmetic over an already-computed vector,
#    matching `_pair_witness`'s own `name_shared` idiom. Also pins the
#    reason `FixedCount` was NOT reused (measured wrong for this shape, per
#    the module comment in analogical_thinking.py).
# --------------------------------------------------------------------------- #

def test_axis_richness_counts_non_absent_entries():
    vec = [["role:scheduler", "x"], ["role:gate", at._ABSENT], ["category", "c"]]
    assert at._axis_richness(vec) == 2
    assert at._axis_richness([]) == 0


def test_fixedcount_reuse_was_measured_wrong_for_this_shape(agent):
    """Historical record: `FixedCount`'s wild-sentinel is wrapped in a
    1-tuple at the Rust call site because it recognises a wholly-wilded ROW
    (AntiUnify's own output convention), not an `_ABSENT` value sitting
    INSIDE an intact row. Calling it directly on a `_concept_shape_vector`
    (as an earlier design attempt did) silently ignores `_ABSENT` entirely."""
    sub = agent.s
    native = at._native_eval(sub)
    vec = [["role:scheduler", "x"], ["role:gate", at._ABSENT], ["category", "c"]]
    wrong = native.evaluate({"type": "FixedCount", "pattern": at._lit(vec),
                             "wild": at._ABSENT}, {})
    assert wrong == 2 * len(vec), (
        "FixedCount on a vector with an in-row _ABSENT sentinel counts BOTH "
        "leaves of every row (pred AND val) as fixed regardless of whether "
        "val is _ABSENT -- it is a CONSTANT (2*len(vec)), completely "
        "insensitive to which axes are evidenced, confirming it does not "
        "see the sentinel in this shape at all -- which is why "
        "_axis_richness uses plain Python counting instead")


# --------------------------------------------------------------------------- #
# 2. Real `find_analogies` call site: an asymmetric pair resolves a_source
#    (the richer concept is the source), never forced, never search-order.
# --------------------------------------------------------------------------- #

def test_asymmetric_pair_resolves_direction_from_richness_not_search_order(agent):
    sub = agent.s
    src, tgt = _mt(sub, "dc_src_asym"), _mt(sub, "dc_tgt_asym")
    rich = _concept(sub, src, "dc_rich_unit",
                    "this gate will schedule and buffer the flow through "
                    "the machine, a store of state")
    sparse = _concept(sub, tgt, "dc_sparse_unit",
                      "this gate is part of a stage in the machine")
    res = at._legacy_find_analogies(sub, "dc_src_asym", ["dc_tgt_asym"], order_n=2)
    r = [x for x in res if x["source_concept"] == "dc_rich_unit"]
    assert r and r[0]["struct_shared"] >= 1

    corr = _find_directional_corr(sub, rich, sparse)
    assert corr is not None
    direction = at.directional_hypothesis_for(sub, corr)
    assert direction["direction"] == "a_source"
    # The SOURCE is the richer concept BY NAME -- not "whichever _pair_witness
    # or find_analogies happened to visit first in its search loop" (the
    # exact defect REASONING_FACILITY_BRIDGE_RESULTS.md Sec3 found).
    assert direction["source_concept"] == "dc_rich_unit"
    assert direction["target_concept"] == "dc_sparse_unit"
    assert direction["confidence"]["richness_a"] != direction["confidence"]["richness_b"]


def test_richer_side_wins_regardless_of_about_a_about_b_write_order(agent):
    """Direct unit test of the rule ladder, independent of find_analogies'
    own search order: swapping which concept is passed as node_a/node_b
    must not change WHICH NAME wins -- only the richness comparison may."""
    sub = agent.s
    mt = _mt(sub, "dc_swap_mt")
    rich = _concept(sub, mt, "dc_swap_rich", "irrelevant definition text")
    sparse = _concept(sub, mt, "dc_swap_sparse", "irrelevant definition text")
    vec_rich = [["role:scheduler", "x"], ["role:gate", "y"], ["category", "c"]]
    vec_sparse = [["role:scheduler", at._ABSENT], ["role:gate", "y"], ["category", "c"]]
    witness = {"shared": [("role:gate", "y"), ("category", "c")],
               "name_shared": 0, "fixed_count": 2, "transform": ()}

    cid1 = at.record_directional_correspondence(sub, rich, sparse, vec_rich, vec_sparse, witness)
    d1 = at.directional_hypothesis_for(sub, cid1)
    assert d1["direction"] == "a_source"
    assert d1["source_concept"] == "dc_swap_rich"

    # Swap argument order -- the SAME two concepts, opposite about_a/about_b.
    cid2 = at.record_directional_correspondence(sub, sparse, rich, vec_sparse, vec_rich, witness)
    d2 = at.directional_hypothesis_for(sub, cid2)
    assert d2["direction"] == "b_source"
    assert d2["source_concept"] == "dc_swap_rich", (
        "the richer concept must win by NAME regardless of which side of "
        "about_a/about_b it was written to")


# --------------------------------------------------------------------------- #
# 3. Tied richness -> symmetric, the honest non-forced outcome.
# --------------------------------------------------------------------------- #

def test_tied_richness_resolves_symmetric_not_a_forced_direction(agent):
    sub = agent.s
    src, tgt = _mt(sub, "dc_src_tie"), _mt(sub, "dc_tgt_tie")
    samedef = "this gate will schedule the flow through the buffer"
    ca = _concept(sub, src, "dc_tie_alpha", samedef)
    cb = _concept(sub, tgt, "dc_tie_beta", samedef)
    res = at._legacy_find_analogies(sub, "dc_src_tie", ["dc_tgt_tie"], order_n=2)
    assert any(x["source_concept"] == "dc_tie_alpha" for x in res)

    corr = _find_directional_corr(sub, ca, cb)
    assert corr is not None
    direction = at.directional_hypothesis_for(sub, corr)
    assert direction["direction"] == "symmetric"
    assert direction["confidence"]["richness_a"] == direction["confidence"]["richness_b"]
    assert "source_concept" not in direction and "target_concept" not in direction


# --------------------------------------------------------------------------- #
# 4. No shared structure -> no_correspondence, never a fabricated direction.
# --------------------------------------------------------------------------- #

def test_no_shared_structure_resolves_no_correspondence(agent):
    sub = agent.s
    mt = _mt(sub, "dc_none_mt")
    ca = _concept(sub, mt, "dc_none_x", "a completely unrelated topic")
    cb = _concept(sub, mt, "dc_none_y", "an entirely different subject")
    witness = {"shared": [], "name_shared": 0, "fixed_count": 0, "transform": ()}
    cid = at.record_directional_correspondence(sub, ca, cb, [], [], witness)
    direction = at.directional_hypothesis_for(sub, cid)
    assert direction["direction"] == "no_correspondence"


# --------------------------------------------------------------------------- #
# 5. Promotion: refuses an unresolved direction, mints an elaborative-tier,
#    analogically-provenanced schema for a resolved one, idempotent.
# --------------------------------------------------------------------------- #

def test_promotion_refuses_symmetric_and_no_correspondence(agent):
    sub = agent.s
    for status in ("symmetric", "no_correspondence", "pending"):
        out = pd.mint_logical_schema_from_analogy(
            agent, {"direction": status, "source_concept": "x",
                    "target_concept": "y", "node": 1})
        assert out["minted"] is False
        assert "not resolved" in out["reason"]


def test_promotion_mints_elaborative_analogical_schema_distinguishable_from_taught(agent):
    sub = agent.s
    src, tgt = _mt(sub, "dc_src_promo"), _mt(sub, "dc_tgt_promo")
    rich = _concept(sub, src, "dc_promo_rich",
                    "this gate will schedule and buffer the flow through "
                    "the machine, a store of state")
    sparse = _concept(sub, tgt, "dc_promo_sparse",
                      "this gate is part of a stage in the machine")
    at._legacy_find_analogies(sub, "dc_src_promo", ["dc_tgt_promo"], order_n=2)
    corr = _find_directional_corr(sub, rich, sparse)
    direction = at.directional_hypothesis_for(sub, corr)
    assert direction["direction"] == "a_source"

    promo = pd.mint_logical_schema_from_analogy(agent, direction)
    assert promo["minted"] is True
    node = promo["node"]
    attrs = sub.node(node)["attrs"]
    assert attrs["kind"] == "knowledge_logical"
    assert attrs["coherence"] == "elaborative"
    assert attrs["provenance"] == "analogical"
    assert sub.has_edge(node, "derived_from", corr)

    # Idempotent re-promotion.
    promo2 = pd.mint_logical_schema_from_analogy(agent, direction)
    assert promo2["minted"] is False
    assert promo2.get("already") is True
    assert promo2["node"] == node

    # Distinguishable from a directly-taught schema: no provenance attr,
    # blocking coherence, no derived_from edge.
    taught = pd.mint_logical_schema(agent, "if X is a mammal, X is warm blooded")
    assert taught["minted"] is True
    taught_attrs = sub.node(taught["node"])["attrs"]
    assert "provenance" not in taught_attrs
    assert taught_attrs["coherence"] == "blocking"
    assert list(sub.neighbours(taught["node"], "derived_from")) == []


# --------------------------------------------------------------------------- #
# 6. The full composition, live: the promoted hypothesis is a real candidate
#    for deduction, gated by standard_of_coherence -- not fired at shallow,
#    fired at deep, minting a genuinely new fact via the UNMODIFIED
#    situation_model_reader.ingest_predication.
# --------------------------------------------------------------------------- #

def test_live_end_to_end_promoted_hypothesis_fires_only_at_deep_coherence(agent):
    sub = agent.s
    src, tgt = _mt(sub, "dc_src_e2e"), _mt(sub, "dc_tgt_e2e")
    rich = _concept(sub, src, "dc_e2e_rich",
                    "this gate will schedule and buffer the flow through "
                    "the machine, a store of state")
    sparse = _concept(sub, tgt, "dc_e2e_sparse",
                      "this gate is part of a stage in the machine")
    at._legacy_find_analogies(sub, "dc_src_e2e", ["dc_tgt_e2e"], order_n=2)
    corr = _find_directional_corr(sub, rich, sparse)
    direction = at.directional_hypothesis_for(sub, corr)
    assert direction["direction"] == "a_source"
    assert direction["source_concept"] == "dc_e2e_rich"
    assert direction["target_concept"] == "dc_e2e_sparse"

    promo = pd.mint_logical_schema_from_analogy(agent, direction)
    assert promo["minted"] is True

    ent = smr._entity(agent, "dc_e2e_entity")
    sub.set_attr(ent, "dc_e2e_rich", 1)

    assert ig.coherence_depth(agent) == "shallow"
    gaps = ig.detect_implication_gaps(agent)
    gap = [g for g in gaps if g["entity"] == "dc_e2e_entity"
           and g["antecedent_attr"] == "dc_e2e_rich"][0]

    r_shallow = ig.resolve_implication_gap(agent, gap)
    assert r_shallow["minted"] is False
    assert "elaborative" in r_shallow["reason"]
    assert sub.node(ent)["attrs"].get("dc_e2e_sparse") != 1

    ig.set_coherence_depth(agent, "deep")
    r_deep = ig.resolve_implication_gap(agent, gap)
    assert r_deep["minted"] is True
    assert r_deep["supplies"] == {"relation": "is_a", "attr": "dc_e2e_sparse"}
    assert sub.node(ent)["attrs"].get("dc_e2e_sparse") == 1


# --------------------------------------------------------------------------- #
# 7. Graceful degradation -- no exception, no write.
# --------------------------------------------------------------------------- #

def test_missing_node_id_degrades_without_persisting(agent):
    sub = agent.s
    n_before = len(sub.nodes("DirectionalCorrespondence"))
    witness = {"shared": [("role:scheduler", "x")], "name_shared": 0,
               "fixed_count": 1, "transform": ()}
    out = at.record_directional_correspondence(sub, None, None, [], [], witness)
    assert out is None
    assert len(sub.nodes("DirectionalCorrespondence")) == n_before


def test_promotion_refuses_when_concept_names_missing(agent):
    out = pd.mint_logical_schema_from_analogy(
        agent, {"direction": "a_source", "source_concept": None,
                "target_concept": "y", "node": 1})
    assert out["minted"] is False


# --------------------------------------------------------------------------- #
# 8. `_sub_token` -- the id(sub)-reuse fix found while combining this rung's
#    own suite with sibling test files in one pytest process (RESULTS.md's
#    "a real new failure appeared" section): `_CONCEPT_READING_CACHE`/
#    `_METASHAPE_COUNT_CACHE`/`_VOCAB_KEYS_CACHE` are module-level caches
#    that PRE-DATE this rung; keying them by raw `id(sub)` is unsafe once
#    many Substrate objects are created and freed in one process (CPython
#    can recycle a freed object's address), which measurably corrupted this
#    rung's own richness comparison when run alongside
#    tests/test_blob_edge_analogy_extension.py. Fixed via a WeakKeyDictionary
#    token whose lifetime is tied to the object, never reused.
# --------------------------------------------------------------------------- #

def test_sub_token_is_stable_for_one_live_object():
    class Dummy:
        pass
    d = Dummy()
    assert at._sub_token(d) == at._sub_token(d)


def test_sub_token_differs_for_two_simultaneously_live_objects():
    class Dummy:
        pass
    a, b = Dummy(), Dummy()
    assert at._sub_token(a) != at._sub_token(b)


def test_sub_token_never_repeats_even_under_forced_id_reuse():
    """The actual property that matters: `_SUB_TOKENS` is a
    `WeakKeyDictionary` keyed by object IDENTITY (Python's weakref
    machinery), never by the raw `id()` integer the OLD code used directly
    -- so even if CPython reuses a freed object's memory address for an
    unrelated new object (the real hazard, allocator-dependent and not
    reliably forceable from pure Python), the new object still gets a
    FRESH token from the monotonic counter, never the stale one. This is
    demonstrated by exhausting many short-lived objects (encouraging real
    address reuse) and asserting every token handed out is unique, which
    would NOT hold under the old `key = (id(sub), ...)` scheme if two of
    these objects happened to share an address (verified separately, live,
    by the combined-suite run in DIRECTIONAL_CORRESPONDENCE_RESULTS.md)."""
    class Dummy:
        pass
    seen = set()
    for _ in range(500):
        d = Dummy()
        tok = at._sub_token(d)
        assert tok not in seen, "a token repeated -- _sub_token is no longer collision-safe"
        seen.add(tok)
        del d  # encourage the allocator to reuse this address next iteration


def test_richness_cache_survives_object_churn_across_many_substrates(agent):
    """Integration-level regression for the actual bug: build many
    short-lived, BARE (no full seed boot -- kept cheap so this stays a fast
    unit test) substrates interleaved with the real one under test,
    encouraging address reuse of the KIND that corrupted
    `_vocabulary_keys`/`_concept_reading` before the `_sub_token` fix, and
    confirm richness stays internally consistent throughout."""
    import substrate_rs

    sub = agent.s
    mt = _mt(sub, "dc_churn_mt")
    rich = _concept(sub, mt, "dc_churn_rich",
                    "this gate will schedule and buffer the flow through "
                    "the machine, a store of state")
    sparse = _concept(sub, mt, "dc_churn_sparse", "irrelevant text")
    for _ in range(200):
        churn = substrate_rs.Substrate()
        cn = churn.add_node("Concept", {"name": "churn_c", "definition": "x"})
        at._concept_reading(churn, cn)   # populate the SAME module caches
        del churn                        # then let it (and its address) go

    va = at._concept_shape_vector(sub, rich)
    vb = at._concept_shape_vector(sub, sparse)
    assert at._axis_richness(va) > at._axis_richness(vb), (
        "richness comparison must stay correct for THIS substrate's own "
        "concepts even after many other substrates were created and freed")
