"""Block 327000 — tests for knowledge-seed extraction
(`domains/llm_knowledge_seed.py`). The seed BUILD + substrate QUERY are gated on
`substrate_rs` (PYTHONPATH=runners/dsl/python). Elicitation needs the model and
is exercised by the block-327 scripts, not here.
"""
from __future__ import annotations

import pytest

from domains import llm_knowledge_seed as ks


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return True
    except Exception:
        return False


_need_substrate = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs absent (run with PYTHONPATH=runners/dsl/python)")

SEEDS = ["seeds/can_native_reimplementation.json"]
# a small is-a chain: a -> b -> c -> d  (adjacent edges only)
CHAIN = [("a", "b"), ("b", "c"), ("c", "d"), ("x", "y")]


@_need_substrate
def test_build_knowledge_mt_creates_nodes_and_edges():
    from substrate_rs import _native
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, CHAIN, relation="isa")
    # one Concept per distinct entity
    assert set(n2n.keys()) == {"a", "b", "c", "d", "x", "y"}
    # the has_concept edges attach every entity to the Microtheory
    concepts = set(c.value for c in s.neighbours(mt, "has_concept"))
    assert concepts == set(n.value for n in n2n.values())


@_need_substrate
def test_query_direct_finds_stored_edge_not_multihop():
    from substrate_rs import _native
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, CHAIN, relation="isa")
    assert ks.query_direct(s, n2n, "a", "b") is True     # stored adjacent edge
    assert ks.query_direct(s, n2n, "a", "c") is False    # 2-hop: NOT stored
    assert ks.query_direct(s, n2n, "a", "d") is False    # 3-hop: NOT stored


@_need_substrate
def test_query_transitive_derives_multihop_entailment():
    from substrate_rs import _native
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, CHAIN, relation="isa")
    # substrate traversal DERIVES the >=2-hop entailments (not stored)
    assert ks.query_transitive(s, n2n, "a", "c")[0] is True
    assert ks.query_transitive(s, n2n, "a", "d")[0] is True
    assert ks.query_transitive(s, n2n, "b", "d")[0] is True
    # and does NOT connect disjoint chains
    assert ks.query_transitive(s, n2n, "a", "y")[0] is False
    assert ks.query_transitive(s, n2n, "x", "d")[0] is False


@_need_substrate
def test_shuffle_collapses_entailment():
    # permuting the edge targets (same nodes, scrambled relations) must break
    # the true a->b->c->d chain's entailment (this is the anti-lookup control).
    import numpy as np
    from substrate_rs import _native
    srcs = [e[0] for e in CHAIN]
    tgts = [e[1] for e in CHAIN]
    rng = np.random.default_rng(3)
    tgts_sh = list(tgts)
    # force a derangement of the chain edges so a->d entailment cannot survive
    while tgts_sh == tgts:
        rng.shuffle(tgts_sh)
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, list(zip(srcs, tgts_sh)),
                                    relation="isa")
    # at least one of the true multi-hop entailments should break under shuffle
    # (we cannot assert all, since a random shuffle could accidentally preserve
    # one; but the true chain a->b->c->d is destroyed with high probability)
    broke = (not ks.query_transitive(s, n2n, "a", "d")[0]) or \
            (not ks.query_transitive(s, n2n, "a", "c")[0])
    assert broke
