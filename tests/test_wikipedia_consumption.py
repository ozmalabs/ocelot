"""test_wikipedia_consumption — the WIKIPEDIA CONSUMPTION PIPELINE (self-improvement #3, at batch scale).
DISCRIMINATIVE, donkey=0 (extraction is arithmetic over the article; POS/sense are reference lookups;
the gate is the held collapse — no LLM).

Self-improvement #3 grounded ONE microtheory from ONE Wikipedia article. This scales the SAME loop to a
BATCH of real wiki_local articles and, per article, grounds three things — LEXICON (POS-typed + defined
concepts), ASSOCIATED MACHINERY (part_of relations + POS + morphology), and a MICROTHEORY (topic +
has_concept edges) — all EARNED from the article, ADMISSIBILITY-GATED, and SOURCE-TRACED, to an ISOLATED
seeds dir so the global boot is unperturbed.

Gates:
  1. CONSUMES A BATCH (headline): N articles -> the lexicon grows by M grounded concepts + K microtheories,
     each grown topic is now EDGE-LEARNABLE (bag 0 -> N, region-cosine 0 -> positive). Real source
     (skipif absent) + a deterministic injected-doc batch.
  2. GROUNDED LEXICON: a sample of new concepts carries POS + a definition + a part_of relation traced to
     source — a grounded lexeme, not a bare string; verified against the article.
  3. EARN NOT FABRICATE: every taught concept traces to the article; a fabricated one fails; a thin
     article -> a thin (not padded) microtheory.
  4. ADMISSIBILITY TEETH: a fabricated / ungrounded lexeme BREAKS a gate constraint and is REJECTED, not
     installed. Pinned.
  5. BOOT UNPERTURBED: the global boot graph is unchanged (the acquired seed is isolated). Pinned.
  6. DISCIPLINE audit: reuses gda (read/extract/trace/teach) + the language faculties (POS) + the gate +
     concept_graph; no LLM, no fit/backward/torch, no hardcoded concept table.
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

from domains import wikipedia_consumption as wc
from domains import gap_driven_acquisition as gda
from domains import concept_graph as cg
from domains import admissibility_gate as ag

# REAL reference documents (factual enumerations — the extractor reads, never invents). Deterministic,
# network-free — the injected-doc twin of the real wiki read (gda.read_source honours source_text). Both
# topics are genuine gaps on a bare boot (bag 0, region-cosine exactly 0), so before->after is unambiguous.
CRYPTO_DOC = (
    "In cryptography, the main primitives are: cipher, key, plaintext, ciphertext, hash function, "
    "digital signature, key exchange, and message authentication code. Other concepts include: nonce, "
    "salt, initialization vector, and block cipher. A cipher transforms plaintext into ciphertext.")
OPTICS_DOC = (
    "In optics, the core components are: lens, mirror, prism, aperture, and diffraction grating. Key "
    "phenomena include: refraction, reflection, dispersion, interference, and polarization. A lens "
    "focuses light through refraction.")


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
    return tempfile.mkdtemp(prefix="wc_seed_")


# =========================================================================== #
#  1. CONSUMES A BATCH — the headline: N articles -> M concepts + K microtheories, coverage rises.
# =========================================================================== #

def test_consumes_a_batch_injected(agent):
    """HEADLINE (deterministic): consume a BATCH of two articles (injected reference docs). The lexicon
    grows by M grounded concepts and K=2 microtheories are minted; each topic goes from a GAP (bag 0,
    region-cosine 0) to EDGE-BEARING (bag rises, cosine > 0). before->after growth is measured."""
    seeds_dir = _tmp()
    assert gda.is_knowledge_gap(agent, "cryptography")
    assert gda.is_knowledge_gap(agent, "optics")
    before = wc._snapshot(agent)

    r1 = wc.consume_article(agent, "Cryptography", source_text=CRYPTO_DOC, seeds_dir=seeds_dir)
    r2 = wc.consume_article(agent, "Optics", source_text=OPTICS_DOC, seeds_dir=seeds_dir)
    after = wc._snapshot(agent)

    assert r1["consumed"] and r2["consumed"]
    # K microtheories minted, M grounded concepts installed.
    assert after["microtheories"] - before["microtheories"] == 2
    assert after["concepts"] - before["concepts"] >= 12
    # each topic is now EDGE-BEARING: bag rose 0 -> N, region-cosine 0 -> positive.
    for r in (r1, r2):
        assert r["before"]["bag"] == 0 and r["before"]["best"] == 0.0
        assert r["after"]["bag"] >= 5 and r["after"]["best"] > 0.0     # rose 0 -> edge-bearing
    # source-faithful: the region names the primitives the source LISTED.
    names = {lex["name"] for lex in r1["admitted"]}
    assert {"cipher", "key", "plaintext", "ciphertext"} <= names, names


@pytest.mark.skipif(not __import__("domains.wiki_local", fromlist=["present"]).present(),
                    reason="local wikipedia reference slab not present")
def test_consumes_a_batch_real_wiki(agent):
    """HEADLINE (real source): consume a BATCH of real wiki_local articles through the reference reader
    #3 consults (wiki_local). The lexicon grows by many grounded concepts across K microtheories; each
    consumed topic that was a GAP is now edge-bearing. Every concept traces to its real article."""
    batch = ["Cryptography", "Photosynthesis", "Volcano", "Guitar"]
    before = wc._snapshot(agent)
    rep = wc.consume(agent, titles=batch, seeds_dir=_tmp())
    after = wc._snapshot(agent)

    assert rep["n_articles"] == 4
    assert len(rep["microtheories_grown"]) >= 3           # most are genuine gaps -> minted
    assert rep["growth"]["concepts"] >= 40                # M grounded concepts across the batch
    assert rep["growth"]["microtheories"] >= 3
    assert after["concepts"] > before["concepts"]
    # each consumed article rose from bag 0 to edge-bearing.
    for r in rep["results"]:
        if r["consumed"]:
            assert r["after"]["bag"] > r["before"]["bag"] and r["after"]["best"] > 0.0


# =========================================================================== #
#  2. GROUNDED LEXICON — POS + definition + relation traced to source (not a bare string).
# =========================================================================== #

def test_grounded_lexicon_pos_definition_relation(agent):
    """A sample of new concepts is a GROUNDED lexeme, not a bare string: each carries a POS (from the
    language faculty), a DEFINITION (the article sentence that named it), and a part_of RELATION to the
    topic — all traced to the source. Verified against the injected article."""
    seeds_dir = _tmp()
    r = wc.consume_article(agent, "Cryptography", source_text=CRYPTO_DOC, seeds_dir=seeds_dir)
    assert r["consumed"]
    by_name = {lex["name"]: lex for lex in r["admitted"]}
    low = CRYPTO_DOC.lower()
    # spot-audit a few known primitives.
    for name in ("cipher", "key", "plaintext"):
        lex = by_name[name]
        assert lex["pos"] is not None and lex["pos_source"] in ("wiktionary", "function_word_reference")
        assert lex["definition"] and lex["definition"].strip()
        assert lex["surface"].lower() in low                 # definition/surface trace to source
        assert lex["part_of"] == "cryptography"              # the machinery relation
    # 'cipher' POS-types to a content class via the reference faculty.
    assert by_name["cipher"]["pos"] in ("noun", "name", "verb")
    # the live graph carries the grounding (set_attr enriched the taught node).
    sub = agent.s
    mt = next(n for n in sub.nodes("Microtheory") if sub.node(n)["attrs"].get("name") == "cryptography")
    cids = {sub.node(c)["attrs"].get("name"): c for c in sub.neighbours(mt, "has_concept")}
    cipher_node = sub.node(cids["cipher"])["attrs"]
    assert cipher_node.get("pos") is not None and cipher_node.get("part_of") == "cryptography"


def test_grounding_persisted_reboot_visible(agent):
    """The grounded lexicon is persisted reboot-visible: the manifest concept entries carry pos + sense +
    part_of alongside the source-traced definition (the base microtheory is gda's, enriched)."""
    seeds_dir = _tmp()
    r = wc.consume_article(agent, "Cryptography", source_text=CRYPTO_DOC, seeds_dir=seeds_dir)
    m = json.load(open(r["seed_path"]))
    cipher = next(c for c in m["concepts"] if c["name"] == "cipher")
    assert cipher.get("pos") is not None and cipher.get("part_of") == "cryptography"
    assert cipher.get("definition") and cipher["definition"].strip()


# =========================================================================== #
#  3. EARN NOT FABRICATE — traces to source; fabrication rejected; thin article -> thin microtheory.
# =========================================================================== #

def test_every_taught_concept_traces_to_source(agent):
    """Every admitted+taught concept's surface is a substring of the read article — the earn-not-fabricate
    invariant, re-asserted on the whole batch. No invented concept is installed."""
    seeds_dir = _tmp()
    r = wc.consume_article(agent, "Cryptography", source_text=CRYPTO_DOC, seeds_dir=seeds_dir)
    low = CRYPTO_DOC.lower()
    for lex in r["admitted"]:
        assert lex["surface"].lower() in low, lex
        assert lex["traces"] is True


def test_thin_article_thin_microtheory(agent):
    """A THIN article (no enumerable concepts) grounds a THIN microtheory — an honest null, not a padded
    one: consume returns consumed=False with the thin reason, mints no microtheory, writes no seed."""
    seeds_dir = _tmp()
    n_mt_before = len(agent.s.nodes("Microtheory"))
    r = wc.consume_article(agent, "Nothing", source_text="A short prose stub with no list of parts.",
                           seeds_dir=seeds_dir)
    assert r["consumed"] is False and "thin" in r["reason"]
    assert len(agent.s.nodes("Microtheory")) == n_mt_before
    assert not os.path.exists(os.path.join(seeds_dir, "nothing_microtheory.json"))


def test_no_source_is_honest_null(agent):
    """An article with NO readable source is an honest null — nothing minted, nothing written."""
    seeds_dir = _tmp()
    n_mt_before = len(agent.s.nodes("Microtheory"))
    r = wc.consume_article(agent, "Zzq No Such Article Qzz", seeds_dir=seeds_dir)
    assert r["consumed"] is False and "no readable source" in r["reason"]
    assert not os.path.exists(os.path.join(seeds_dir, "zzq_no_such_article_qzz_microtheory.json"))
    assert len(agent.s.nodes("Microtheory")) == n_mt_before


# =========================================================================== #
#  4. ADMISSIBILITY TEETH — a fabricated / ungrounded lexeme is REJECTED by the gate, not installed.
# =========================================================================== #

def test_gate_rejects_fabricated_lexeme():
    """THE NEGATIVE CONTROL: a fabricated lexeme (surface NOT in the article) BREAKS the gate's traces
    constraint and is INADMISSIBLE — the gate rejects fabrication, it does not merely flag it."""
    fabricated = {"name": "warp_core", "surface": "warp core", "definition": "invented",
                  "pos": "noun", "traces": False}
    gr = wc.gate_lexeme(fabricated)
    assert gr.admitted is False and not gr.collapsed


def test_gate_rejects_ungrounded_lexeme():
    """An UNGROUNDED lexeme (no POS — a garbage token the faculty cannot type) BREAKS the pos_grounded
    constraint and is rejected, even though its surface traces."""
    ungrounded = {"name": "zzqxxyy", "surface": "zzqxxyy", "definition": "present",
                  "pos": None, "traces": True}
    gr = wc.gate_lexeme(ungrounded)
    assert gr.admitted is False


def test_gate_teeth_on_real_extraction(agent):
    """On a REAL article, the gate REJECTS ungrounded extractions (proper names / fragments the POS
    faculty cannot type) rather than installing them. Every ADMITTED lexeme has a grounded POS + traces;
    the rejected ones are reported (honest extraction quality)."""
    if not __import__("domains.wiki_local", fromlist=["present"]).present():
        pytest.skip("local wikipedia reference slab not present")
    r = wc.consume_article(agent, "Cryptography", seeds_dir=_tmp())
    assert r["consumed"]
    # admitted lexemes all cleared the gate (pos grounded + traces).
    for lex in r["admitted"]:
        assert lex["pos"] is not None and lex["traces"] is True
    # the gate had teeth: a rejected lexeme is reported, none of them installed.
    installed = {lex["name"] for lex in r["admitted"]}
    for rej in r["rejected"]:
        assert rej["name"] not in installed


# =========================================================================== #
#  5. BOOT UNPERTURBED — teaching to the isolated acquired dir leaves the global graph unchanged.
# =========================================================================== #

def test_boot_unperturbed(agent):
    """Consuming a batch to the isolated acquired seeds dir leaves the globally-loaded graph untouched: a
    fresh load_all_seeds agent still sees the topics as thin gaps (the acquired seeds are NOT in the
    globbed seeds/ dir). ACQUIRED lives under seeds/acquired/, which load_all_seeds does not glob."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    wc.consume_article(agent, "Cryptography", source_text=CRYPTO_DOC, seeds_dir=_tmp())
    wc.consume_article(agent, "Optics", source_text=OPTICS_DOC, seeds_dir=_tmp())
    fresh = WorldAdapter(seeds=())
    load_all_seeds(fresh)
    cg._CACHE.clear()
    assert gda.is_knowledge_gap(fresh, "cryptography") is True
    assert gda.is_knowledge_gap(fresh, "optics") is True
    # the default acquired dir is under seeds/ but NOT the globbed root pattern (seeds/acquired/*.json).
    assert wc.ACQUIRED.name == "acquired" and wc.ACQUIRED.parent.name == "seeds"


# =========================================================================== #
#  6. DISCIPLINE AUDIT — reused machinery, no LLM, no hardcoded concept table.
# =========================================================================== #

def test_graph_native_discipline_audit():
    """Source audit: the pipeline REUSES gda (read/extract/trace/teach) + the language faculties (POS via
    function_word_reference / wiktionary_reference) + the admissibility gate + concept_graph; it runs NO
    LLM, no fit/backward/torch, and carries NO hardcoded concept table (concepts come from the articles)."""
    src = inspect.getsource(wc)
    for reused in ("gap_driven_acquisition", "gda.read_source", "gda.extract_microtheory",
                   "gda.traces_to_source", "gda.teach_microtheory", "admissibility_gate",
                   "function_word_reference", "wiktionary_reference", "concept_graph"):
        assert reused in src, reused
    for banned in (".fit(", ".backward(", "import torch", "import numpy", "sklearn",
                   "openai", "anthropic", "gemini", "llm("):
        assert banned not in src, banned
    # no hardcoded concept table: DEFAULT_BATCH is article TITLES (input), not a concept->def map.
    assert "CONCEPTS = {" not in src and "ACQUIRE_LIST" not in src
