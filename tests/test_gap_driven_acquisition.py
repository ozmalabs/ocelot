"""test_gap_driven_acquisition — GAP-DRIVEN KNOWLEDGE ACQUISITION (self-improvement #3).
DISCRIMINATIVE, donkey=0 (extraction is arithmetic over a real reference source, no LLM).

The earn-not-borrow loop pointed at the agent's OWN knowledge gaps: a thin/empty DIMENSION the
concept-graph edge-learner (`concept_graph`) cannot ground drives the agent to READ a source, EXTRACT
the region's concepts, TEACH the microtheory (persisted, reboot-proof), and RE-DECODE — coverage rises.
The SAME shape the external developer produced by hand (seeds/*_microtheory.json), now AGENT-DRIVEN.

Gates:
  1. AGENT-DRIVEN GROUNDING (headline): thin/anchored dimension -> read -> extract -> teach -> the
     region is now edge-BEARING (bag_size 0 -> N, region-cosine 0 -> positive) — coverage rises.
     Proven both on the REAL wiki source (skipif absent) and on an injected reference document.
  2. EARN NOT FABRICATE: every taught concept traces to the read source; a fabricated concept does
     NOT trace; a gap with NO readable source is an HONEST NULL (no microtheory minted, no seed).
  3. PERSISTENCE: a fresh reboot re-loads the taught microtheory.
  4. GAP SIGNAL FROM COVERAGE: the gap set is derived from concept_graph coverage, not hardcoded;
     a rich domain is not a gap; a CapabilityGap's knowledge subject is read off the node.
  5. GRAPH-NATIVE / DISCIPLINE audit: read_and_ground/wiki_local + teach + concept_graph, reused; no
     LLM, no fit/backward/torch, no hardcoded acquisition list.
  6. NO POLLUTION: teaching to an isolated dir does not perturb the globally-loaded graph.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import gap_driven_acquisition as gda
from domains import concept_graph as cg

# A REAL reference document (a factual enumeration — the extractor reads it, never invents). Plays the
# role of a fed reference slab so the core gates are deterministic + network-free. `cryptography` is a
# genuine gap on a bare boot (bag 0, region-cosine exactly 0), so the before->after is unambiguous.
CRYPTO_DOC = (
    "In cryptography, the main primitives are: cipher, key, plaintext, ciphertext, hash function, "
    "digital signature, key exchange, and message authentication code. Other concepts include: nonce, "
    "salt, initialization vector, and block cipher. A cipher transforms plaintext into ciphertext.")


@pytest.fixture()
def agent():
    pytest.importorskip("substrate_rs")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()
    return a


def _tmp():
    return tempfile.mkdtemp(prefix="gda_seed_")


# =========================================================================== #
#  1. AGENT-DRIVEN GROUNDING — the headline: thin -> read -> extract -> teach -> coverage rises.
# =========================================================================== #

def test_agent_driven_grounding_injected_source(agent):
    """HEADLINE (deterministic): a thin/anchored dimension the concept-graph cannot ground drives the
    agent to READ a reference document, EXTRACT the region's concepts, TEACH the microtheory, and the
    region becomes EDGE-BEARING — bag_size rises 0 -> N and the region-cosine rises from exactly 0 to a
    positive value (the learner now co-descends the region's own has_concept neighbourhood)."""
    domain = "cryptography"
    assert gda.is_knowledge_gap(agent, domain)                     # BEFORE: thin + ungrounded region
    before = gda.coverage(agent, domain)
    assert before["bag"] <= gda._THIN_BAG and before["best"] == 0.0

    r = gda.acquire_for_gap(agent, domain, source_text=CRYPTO_DOC, seeds_dir=_tmp())

    assert r["acquired"] is True and r["traced"] is True
    after = r["after"]
    assert after["bag"] > before["bag"] and after["bag"] >= 8       # coverage rose (edge-bearing now)
    assert after["best"] > 0.0                                      # region-cosine 0 -> positive
    # the extracted region names the cryptographic primitives the SOURCE listed (source-faithful).
    names = {c["name"] for c in r["extracted"]["concepts"]}
    assert {"cipher", "key", "plaintext", "ciphertext"} <= names, names


@pytest.mark.skipif(not __import__("domains.wiki_local", fromlist=["present"]).present(),
                    reason="local wikipedia reference slab not present")
def test_agent_driven_grounding_real_wiki_source(agent):
    """HEADLINE (real source): the agent reads the REAL Wikipedia 'Cryptography' article through the
    reference reader read_and_ground consults (wiki_local), extracts the region's concepts straight from
    the article, teaches the microtheory, and cryptography goes from EDGE-ABSENT (bag 0, region-cosine
    exactly 0 — the learner had nothing to read) to EDGE-BEARING (bag rises, cosine > 0). Every concept
    traces to the real article — earn, not fabricate."""
    domain = "cryptography"
    assert gda.is_knowledge_gap(agent, domain)
    before = gda.coverage(agent, domain)
    assert before["bag"] == 0 and before["best"] == 0.0

    r = gda.acquire_for_gap(agent, domain, source_title="Cryptography", seeds_dir=_tmp())

    assert r["acquired"] is True and r["traced"] is True
    assert r["after"]["bag"] >= 20 and r["after"]["best"] > 0.0     # coverage rose off the real read
    assert r["extracted"]["source"] and "wiki" in str(r["extracted"]["source"]).lower()


# =========================================================================== #
#  2. EARN NOT FABRICATE — traces to source; fabrication rejected; no-source honest null.
# =========================================================================== #

def test_extracted_concepts_trace_to_source(agent):
    """The taught concepts are ACTUALLY in the read source — every extracted surface is a substring of
    the source text. This is the honesty invariant: the microtheory is earned from the source."""
    src = gda.read_source(agent, "cryptography", source_text=CRYPTO_DOC)
    ex = gda.extract_microtheory("cryptography", src)
    assert not ex["thin"] and gda.traces_to_source(ex, src)
    low = CRYPTO_DOC.lower()
    for c in ex["concepts"]:
        assert c["surface"].lower() in low, c


def test_fabricated_concept_does_not_trace(agent):
    """THE NEGATIVE CONTROL: an invented concept (not in the source) fails the trace guard, so
    acquire_for_gap would refuse to teach it. The guard rejects fabrication, not just detects it."""
    src = {"text": CRYPTO_DOC}
    fabricated = {"domain": "x", "concepts": [{"name": "warp_core", "surface": "warp core"}]}
    assert gda.traces_to_source(fabricated, src) is False


def test_no_source_is_honest_null(agent):
    """A gap with NO readable source (a nonsense domain: no injected text, no slab page, no lead) is an
    HONEST NULL — acquire_for_gap returns acquired=False with a 'no readable source' reason, mints NO
    microtheory node, and writes NO seed file. The agent does not fabricate."""
    domain = "zzq_no_such_domain_qzz"
    seeds_dir = _tmp()
    n_mt_before = len(agent.s.nodes("Microtheory"))
    r = gda.acquire_for_gap(agent, domain, seeds_dir=seeds_dir)
    assert r["acquired"] is False and "no readable source" in r["reason"]
    assert len(agent.s.nodes("Microtheory")) == n_mt_before        # nothing minted
    assert not os.path.exists(os.path.join(seeds_dir, f"{domain}_microtheory.json"))  # nothing written


# =========================================================================== #
#  3. PERSISTENCE — a fresh reboot re-loads the taught microtheory.
# =========================================================================== #

def test_persistence_reboot(agent):
    """The taught microtheory persisted to a seed manifest — a FRESH agent that loads it (the exact
    seed-loader path, load_one_seed) re-installs the concepts, so the knowledge survives reboot."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds, load_one_seed
    domain = "cryptography"
    seeds_dir = _tmp()
    r = gda.acquire_for_gap(agent, domain, source_text=CRYPTO_DOC, seeds_dir=seeds_dir)
    assert r["acquired"] is True
    seed_path = os.path.join(seeds_dir, f"{domain}_microtheory.json")
    assert os.path.exists(seed_path)
    manifest = json.load(open(seed_path))
    assert manifest["microtheory"]["name"] == domain and len(manifest["concepts"]) >= 8

    # fresh boot: the domain is thin again (the taught seed is NOT in the global seeds dir) ...
    fresh = WorldAdapter(seeds=())
    load_all_seeds(fresh)
    cg._CACHE.clear()
    assert gda.is_knowledge_gap(fresh, domain)                     # gap again on a bare boot
    # ... until it RE-LOADS the persisted manifest -> the concepts are re-installed (reboot-proof).
    load_one_seed(fresh.s, f"{domain}_microtheory", seed_dir=seeds_dir)
    cg._CACHE.clear()
    assert cg.bag_size(fresh, domain) >= 8


# =========================================================================== #
#  4. GAP SIGNAL FROM COVERAGE — derived, not hardcoded.
# =========================================================================== #

def test_gap_signal_derived_from_coverage(agent):
    """The gap DECISION is read off concept_graph coverage: a thin+ungrounded domain is a knowledge
    gap; a RICH edge-grounded domain (machine_learning) is NOT. detect_knowledge_gaps filters a candidate
    pool by that coverage read — no hardcoded gap list."""
    assert gda.is_knowledge_gap(agent, "cryptography") is True
    assert gda.is_knowledge_gap(agent, "machine_learning") is False
    gaps = gda.detect_knowledge_gaps(agent, ["cryptography", "machine_learning", "philosophy"])
    got = {g["domain"] for g in gaps}
    assert "cryptography" in got                                    # thin -> flagged
    assert "machine_learning" not in got and "philosophy" not in got  # rich -> not a gap


def test_capability_gap_knowledge_subject_read_off_node(agent):
    """A minted CapabilityGap (self_capability_collapse) of the KNOWLEDGE kind carries a topic/domain;
    gap_domain_of reads that subject so the acquisition can target it. A faculty-only gap returns None."""
    assert gda.gap_domain_of(agent, {"topic": "cryptography"}) == "cryptography"
    assert gda.gap_domain_of(agent, {"domain": "robotics"}) == "robotics"
    assert gda.gap_domain_of(agent, {"faculty": "converse", "failure_class": "silence"}) is None


# =========================================================================== #
#  5. GRAPH-NATIVE / DISCIPLINE AUDIT — reused machinery, no LLM, no hardcoded list.
# =========================================================================== #

def test_graph_native_discipline_audit():
    """Source audit: the acquisition REUSES read_and_ground/wiki_local (read) + teach (persist) +
    concept_graph (the gap read + re-decode); it runs NO LLM, no fit/backward/torch, and carries NO
    hardcoded acquisition list (no big literal domain->concepts table)."""
    src = inspect.getsource(gda)
    for reused in ("read_and_ground", "wiki_local", "from domains.teach import teach",
                   "concept_graph", "cg.region_confidence", "cg.bag_size"):
        assert reused in src, reused
    for banned in (".fit(", ".backward(", "import torch", "import numpy", "sklearn",
                   "openai", "anthropic", "gemini", "llm("):
        assert banned not in src, banned
    # no hardcoded acquisition list: the concepts come from the source, not a literal per-domain table.
    assert "CONCEPTS = {" not in src and "ACQUIRE_LIST" not in src


# =========================================================================== #
#  6. NO POLLUTION — teaching to an isolated dir does not perturb the global graph.
# =========================================================================== #

def test_isolated_teach_does_not_pollute_global_graph(agent):
    """Teaching to an isolated seeds dir leaves the globally-loaded graph untouched: a fresh
    load_all_seeds agent still sees cryptography as a thin gap (the acquired seed is NOT in the globbed
    seeds/ dir). This is why the no-regression neighbours (compilers zero-edge, communication anchored)
    stay green — the demo output is isolated."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    gda.acquire_for_gap(agent, "cryptography", source_text=CRYPTO_DOC, seeds_dir=_tmp())
    fresh = WorldAdapter(seeds=())
    load_all_seeds(fresh)
    cg._CACHE.clear()
    assert gda.is_knowledge_gap(fresh, "cryptography") is True      # global graph unperturbed
