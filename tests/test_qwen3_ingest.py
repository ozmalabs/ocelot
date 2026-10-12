"""Block 333000 — ingesting the reaped qwen3 knowledge gives the entity
capability it lacked, with the epistemic guard intact: a qwen3-only claim sits
below the solo-assert bar and an attested source overrides it.
"""
from __future__ import annotations

import json
import os

import pytest

CAN_SEED = "seeds/can_native_reimplementation.json"
REAPED = "domain_data/llm_harvest/qwen3_reaped_knowledge.json"
SOLO_ASSERT_BAR = 0.8


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return os.path.isfile(CAN_SEED) and os.path.isfile(REAPED)
    except Exception:
        return False


_need = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs / seeds absent (run with PYTHONPATH=runners/dsl/python)")


def _fresh():
    from substrate_rs import _native
    from substrate.seed_loader import engine_rules_only
    s = _native.Substrate()
    s.load_seed_manifest(engine_rules_only(json.load(open(CAN_SEED))))
    return s


@_need
def test_ingest_gives_capability_delta_with_provenance():
    from domains import llm_knowledge_seed as ks
    from domains import source_provenance as sp
    d = json.load(open(REAPED))
    triples = [(e["subject"], e["object"]) for e in d["edges"]]

    # a real >=2-hop entailment in the reaped graph
    from collections import defaultdict
    adj = defaultdict(list)
    for a, b in triples:
        adj[a].append(b)

    def two_hop():
        for a in adj:
            seen, fr = set(), [(a, 0)]
            while fr:
                n, dd = fr.pop(0)
                for k in adj.get(n, []):
                    if k not in seen and k != a:
                        seen.add(k)
                        if dd + 1 >= 2:
                            return a, k
                        fr.append((k, dd + 1))
        return None
    q = two_hop()
    assert q is not None
    subj, obj = q

    # bare graph cannot answer; after ingest the substrate derives it
    bare = _fresh()
    _, n0 = ks.build_knowledge_mt(bare, [CAN_SEED], [], relation="isa")
    assert ks.query_transitive(bare, n0, subj, obj)[0] is False

    s = _fresh()
    _, n2n = ks.build_knowledge_mt(s, [CAN_SEED], triples, relation="isa")
    assert ks.query_transitive(s, n2n, subj, obj)[0] is True     # capability delta
    # NOT a stored edge — it is DERIVED (the anti-lookup check)
    assert ks.query_direct(s, n2n, subj, obj) is False

    # provenance / epistemic weight of the reaped source is readable + calibrated
    s.add_node("Concept", {"name": "qwen3", "reliability": "self_published_calibrated"})
    epi = sp.epistemic_status_for_source(s, "qwen3")
    assert epi["status"] == "self_published"
    assert epi["confidence"] == d["trust"]                       # edge trust == source band


@_need
def test_outgrow_the_witness_guard():
    from domains import source_provenance as sp
    s = _fresh()
    s.add_node("Concept", {"name": "qwen3", "reliability": "self_published_calibrated"})
    s.add_node("Concept", {"name": "wikipedia", "reliability": "consensus_tertiary"})
    q = sp.epistemic_status_for_source(s, "qwen3")["confidence"]
    w = sp.epistemic_status_for_source(s, "wikipedia")["confidence"]
    # a qwen3-only claim is BELOW the solo-assert bar (must corroborate)
    assert q < SOLO_ASSERT_BAR
    # an attested source clears the bar and outweighs a contrary qwen3 edge
    assert w >= SOLO_ASSERT_BAR
    assert w > q
