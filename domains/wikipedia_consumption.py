"""wikipedia_consumption — a WIKIPEDIA CONSUMPTION PIPELINE (self-improvement #3, at BATCH scale).

Self-improvement #3 (domains/gap_driven_acquisition.py) proved the loop on ONE
article: perceive a knowledge gap -> READ a real Wikipedia article -> EXTRACT the
region's concepts (source-faithful) -> TEACH the microtheory (persisted) -> the
concept-graph edge-learner re-decodes and coverage rises. This module SCALES that
loop to a BATCH of real `wiki_local` articles and, per article, GROUNDS three
things — all EARNED from the article, ADMISSIBILITY-GATED, and SOURCE-TRACED:

    1. LEXICON — the article's key terms as GROUNDED Concepts: each term is
       POS-typed (the function-word / Wiktionary POS faculty), carries a
       definition (the article sentence that named it), and a lexical sense
       (the Wiktionary gloss of its head). Not a bare string — a grounded lexeme.
    2. ASSOCIATED MACHINERY — the relations that hold the lexicon together: each
       member concept is `part_of` the topic (the article enumerated it as a
       part), plus morphology (lemma, best-effort) and the POS above — grounded,
       not invented.
    3. MICROTHEORY — the article topic as a Microtheory with `has_concept` edges
       to its member concepts (the concept_graph structure), so the topic becomes
       EDGE-LEARNABLE (the same shape #3 produced, now at batch scale).

Every grounded object passes the ONE admissibility gate (domains/admissibility_
gate.gate_object — the meta-grammar collapse) before install: a lexeme is ADMITTED
only if its forward-model properties reproduce the problem's constraints (its
surface TRACES to the article, it has a grounded POS, it carries a definition). A
fabricated / ungrounded / garbage extraction BREAKS a constraint and is REJECTED,
not installed. Admitted lexemes are TAUGHT (persisted, reboot-proof) to an
ISOLATED seeds dir (`seeds/acquired/`) that `load_all_seeds` does NOT glob, so the
global boot graph is unperturbed.

WORLD-ADAPTER DISCIPLINE (CLAUDE.md). This module owns NO agent decision. It
REUSES, does not reimplement:
  · READ + EXTRACT + TRACE  — domains/gap_driven_acquisition (#3), which itself
    reads through domains/read_and_ground + the wiki_local slab.
  · POS + sense + morphology — the LANGUAGE FACULTIES: function_word_reference
    (POS classify), wiktionary_reference (POS + gloss), morphology_reference
    (lemma). The MEANING/POS is the faculty's, read as graph data.
  · GATE                     — domains/admissibility_gate.gate_object (the held
    manifold-collapse). This module builds the mechanical (label, got, want)
    constraints; the ADMIT decision is the gate's collapse, unchanged.
  · TEACH                    — domains/gap_driven_acquisition.teach_microtheory
    (the persisted seed manifest + live install) + domains/teach.teach (a
    provenance note). The install-enrichment (set the grounded POS/lemma/sense
    on the just-taught nodes) is mechanical `set_attr` — admissible adapter I/O.
The coverage read (the gap signal + the re-decode) is concept_graph, unchanged.
NO `if/else` decides what a term MEANS; NO LLM (donkey=0 — extraction is
arithmetic over the article, POS/gloss are reference lookups, the gate is the
held collapse).

EARN, NOT FABRICATE (the honesty guard, #2's not-fooling-itself discipline held).
Every taught concept/definition/relation traces to the read article
(gda.traces_to_source, re-asserted). A thin article grounds a THIN microtheory
(honest), not a padded one. The extraction is NOISIER than hand-curation — real
Wikipedia enumerations leak sentence fragments ('rather than water', 'thus
creating magma') alongside the genuine terms ('calvin cycle', 'carbon fixation').
That noise is REPORTED, not hidden; the gate's teeth are on FABRICATION (a surface
that does not trace) and UNGROUNDED lexemes (no POS), not on every fragment.

HONEST SCALE (stated plainly). `wiki_local` indexes the full structured-enwiki
snapshot (~7.6M titles). This pipeline consumes a BATCH of N of them — N is the
caller's choice; the demo uses a handful of genuine knowledge gaps so the
before->after growth is unambiguous. The offline morphology slab is not present in
this environment, so `lemma` is a best-effort NULL (the faculty is wired; the data
is absent) — reported, not faked.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from domains import gap_driven_acquisition as gda
from domains import concept_graph as cg
from domains import admissibility_gate as ag

_ROOT = Path(__file__).resolve().parent.parent
_SEEDS = _ROOT / "seeds"
# ISOLATED acquired-seeds dir — NOT globbed by load_all_seeds (it globs seeds/*.json,
# not seeds/acquired/*.json), so a consumed batch never perturbs the global boot.
ACQUIRED = _SEEDS / "acquired"

# A default batch of REAL wiki_local article titles that are genuine KNOWLEDGE GAPS
# on a bare boot (thin has_concept bag, ungrounded region) — so the before->after
# growth is unambiguous. Every title is a real article in the local slab; the
# caller may pass its own `titles`. These are NOT a concept table (no concepts are
# hardcoded — the concepts come from the articles); they are only WHICH articles to
# read, the pipeline's input.
DEFAULT_BATCH = [
    "Cryptography", "Photosynthesis", "Volcano", "Blockchain",
    "Guitar", "Democracy", "Glacier", "Antibiotic",
]

# content POS: a grounded lexeme should type to a content class (or a closed-class
# function label). Any grounded POS clears the gate's pos_grounded constraint; this
# set is only used to LABEL the lexeme's coarse class for the report.
_CONTENT_POS = frozenset({"noun", "name", "adj", "verb", "adv", "num", "proper noun"})


# =========================================================================== #
#  GROUND THE LEXICON — POS + definition + sense + morphology + relation, all
#  reusing the language faculties. No meaning decision here (the faculty decides).
# =========================================================================== #

def _head(surface: str) -> str:
    """The HEAD token of a (possibly multi-word / hyphenated) surface — the last
    word ('classical guitar' -> 'guitar', 'proof-of-work' -> 'work'). The
    genus-differentia convention: a compound noun phrase IS its head noun, so the
    head is what the POS/sense faculty types. Mechanical surface op, no meaning."""
    toks = surface.replace("-", " ").replace("_", " ").split()
    return toks[-1] if toks else surface


def ground_pos(surface: str, language: str = "en") -> tuple[Optional[str], Optional[str]]:
    """POS-TYPE a term via the LANGUAGE FACULTIES (reused, not reimplemented):
    first the closed-class function-word classifier (function_word_reference), then
    the Wiktionary POS reference (wiktionary_reference) on the head, then on the
    full phrase. Returns (pos, source) or (None, None) when the term types to no
    known POS (an ungrounded lexeme — the gate rejects it). No meaning decision:
    the POS is the faculty's, read back."""
    from domains import function_word_reference as fw
    from domains import wiktionary_reference as wr
    head = _head(surface)
    try:
        spec = fw.classify(head, language)
        if spec and spec.get("function"):
            return spec["function"], "function_word_reference"
    except Exception:
        pass
    try:
        pos = wr.wiktionary_pos(head, language)
        if pos:
            return pos[0], "wiktionary"
        pos = wr.wiktionary_pos(surface.replace("_", " "), language)
        if pos:
            return pos[0], "wiktionary"
    except Exception:
        pass
    return None, None


def ground_sense(surface: str, language: str = "en") -> Optional[str]:
    """The lexical SENSE (Wiktionary gloss of the head) — a reference lookup, the
    lexeme's dictionary meaning. None when the head has no gloss. Reused faculty."""
    from domains import wiktionary_reference as wr
    try:
        return wr.wiktionary_gloss(_head(surface), language)
    except Exception:
        return None


def ground_lemma(surface: str, language: str = "en") -> Optional[str]:
    """The morphological LEMMA of the head (best-effort) — reused morphology
    faculty. None when the offline slab is absent (honest) or the surface is
    already a lemma."""
    from domains import morphology_reference as mr
    try:
        return mr.lemmatize(_head(surface), language)
    except Exception:
        return None


def ground_lexeme(concept: dict, src: dict, topic: str,
                  language: str = "en", *, context_sense: bool = False,
                  cache=None, agent=None) -> dict:
    """Turn one EXTRACTED concept (name + surface + source-sentence definition)
    into a GROUNDED lexeme: attach its POS (faculty), its lexical sense (Wiktionary
    gloss), its lemma (morphology, best-effort), and its ASSOCIATED-MACHINERY
    relation — the article enumerated it as a PART OF the topic, so `part_of` the
    topic, traced to the enumeration sentence. Also records `traces` (surface is a
    substring of the article) — the earn-not-fabricate property the gate reads.

    The concept's DEFINITION stays the ARTICLE sentence that named it (source-
    traced); the Wiktionary gloss is a SEPARATE lexical `sense` (reference-traced).
    Nothing is invented — every field is a faculty read or a source substring."""
    surface = concept["surface"]
    text_low = (src.get("text", "") or "").lower()
    pos, pos_source = ground_pos(surface, language)
    # SENSE — the SELF-IMPROVEMENT-CYCLE fix (context_sense=True): score each
    # candidate WordNet sense by FIT to the concept's own definition sentence and
    # argmax (consumption_quality.sense_in_context -> dictionary_lexicon.pick_sense,
    # the graph-resident selection rule). Off by default -> the legacy context-blind
    # Wiktionary first-gloss, byte-identical.
    sense_synset = None
    sense_rank = None
    if context_sense:
        from domains import consumption_quality as cq
        sr = cq.sense_in_context(surface, concept.get("definition", ""),
                                 slot="patient", extra=[topic], language=language,
                                 cache=cache, agent=agent)
        sense = sr.get("sense")
        sense_source = sr.get("source")
        sense_synset = sr.get("synset")
        sense_rank = sr.get("rank")
    else:
        sense = ground_sense(surface, language)
        sense_source = "wiktionary" if sense else None
    lemma = ground_lemma(surface, language)
    return {
        "name": concept["name"],
        "surface": surface,
        # the concept's definition: the ARTICLE sentence that enumerated it.
        "definition": concept["definition"],
        "pos": pos,
        "pos_source": pos_source,
        "pos_class": "content" if (pos in _CONTENT_POS) else ("function" if pos else None),
        "sense": sense,
        "sense_source": sense_source,
        "sense_synset": sense_synset,
        "sense_rank": sense_rank,
        "lemma": lemma,
        # ASSOCIATED MACHINERY — the relation, traced to the source sentence.
        "part_of": topic,
        "relation_traced_sentence": concept["definition"],
        # earn-not-fabricate property (read by the gate).
        "traces": surface.lower() in text_low,
    }


# =========================================================================== #
#  ADMISSIBILITY GATE — every grounded lexeme collapses against its constraints.
# =========================================================================== #

def gate_lexeme(lexeme: dict, *, substrate=None) -> ag.GateResult:
    """Route a grounded lexeme through the ONE admissibility gate
    (admissibility_gate.gate_object). The lexeme's forward-model PROPERTIES must
    reproduce the STATED constraints of a grounded lexeme:

      · traces        — its surface is a substring of the read article (earn-not-
                        fabricate). A fabricated concept BREAKS this.
      · pos_grounded  — it types to a known POS (a grounded lexeme, not a bare
                        garbage token). An un-typeable token BREAKS this.
      · defined       — it carries a (source-traced) definition.

    ADMIT iff every constraint reproduces (full collapse); one broken constraint =>
    inadmissible BY CONSTRUCTION. The DECISION is the gate's held collapse; this
    only marshals the (got, want) properties. Mechanical."""
    props = {
        "traces": bool(lexeme.get("traces")),
        "pos_grounded": bool(lexeme.get("pos")),
        "defined": bool((lexeme.get("definition") or "").strip()),
    }
    stated = {"traces": True, "pos_grounded": True, "defined": True}
    return ag.gate_object(object_props=props, stated_props=stated,
                          substrate=substrate)


# =========================================================================== #
#  TEACH THE GROUNDED MICROTHEORY — reuse gda.teach_microtheory + enrich live.
# =========================================================================== #

def _enrich_installed(agent, taught: dict, admitted: list) -> int:
    """After gda.teach_microtheory installs the microtheory + has_concept edges +
    base concept nodes, ENRICH each live Concept node with its grounded lexeme
    fields (pos / pos_source / sense / lemma / part_of) via set_attr — mechanical
    adapter I/O, no decision. Returns how many nodes were enriched."""
    sub = agent.s
    by_name = {}
    for cid in sub.neighbours(taught["mt"], "has_concept"):
        nm = sub.node(cid)["attrs"].get("name")
        if nm is not None:
            by_name[nm] = cid
    n = 0
    for lex in admitted:
        cid = by_name.get(lex["name"])
        if cid is None:
            continue
        for key in ("pos", "pos_source", "pos_class", "sense", "sense_source",
                    "lemma", "part_of"):
            v = lex.get(key)
            if v is not None:
                try:
                    sub.set_attr(cid, key, v)
                except Exception:
                    pass
        n += 1
    return n


def _persist_grounding(seed_path: str, admitted: list) -> None:
    """Patch the persisted seed manifest gda.teach_microtheory wrote so each
    concept entry carries its grounded lexeme fields (reboot-visible). Mechanical
    JSON I/O — the base manifest is gda's; this only adds the grounded fields."""
    p = Path(seed_path)
    if not p.exists():
        return
    m = json.loads(p.read_text())
    by_name = {lex["name"]: lex for lex in admitted}
    for c in m.get("concepts", []):
        lex = by_name.get(c.get("name"))
        if not lex:
            continue
        for key in ("pos", "pos_source", "sense", "sense_source", "lemma", "part_of"):
            if lex.get(key) is not None:
                c[key] = lex[key]
    p.write_text(json.dumps(m, indent=1))


# =========================================================================== #
#  CONSUME ONE ARTICLE — read -> extract -> ground -> gate -> teach.
# =========================================================================== #

def consume_article(agent, title: str, *, seeds_dir: Path = ACQUIRED,
                    language: str = "en", max_concepts: int = 30,
                    gate: bool = True, source_text: Optional[str] = None,
                    quality: bool = True, cache=None, timing=None,
                    reading_collapse: bool = False) -> dict:
    """Consume ONE real wiki_local article, end to end:

      1. snapshot BEFORE coverage (concept_graph — the gap signal);
      2. READ the article (reuse gda.read_source -> wiki_local slab, or an
         injected `source_text` — a fed reference doc, for a deterministic test);
      3. EXTRACT the region's concepts (reuse gda.extract_microtheory, source-
         faithful); honest-null on no source / thin source / un-traced extraction;
      4. GROUND each concept's lexicon+machinery (POS/sense/lemma/relation);
      5. GATE each grounded lexeme (admissibility_gate) — reject fabrication /
         ungrounded lexemes;
      6. TEACH the admitted grounded microtheory (reuse gda.teach_microtheory,
         persist to the ISOLATED seeds_dir) + enrich the live nodes;
      7. snapshot AFTER coverage -> the re-decode.

    Returns a per-article report {consumed, reason, domain, title, before, after,
    n_admitted, n_rejected, admitted, rejected, delta, seed_path}."""
    # TIMING SENSOR (visibility fix): when a LoadTimer is passed, each load stage
    # surfaces its latency as a LatencyObservation graph node the agent HOLDS. The
    # default NULL_TIMER records nothing / mints no node — un-instrumented calls
    # stay byte-identical. The clock read is host I/O (an admissible sensor).
    from domains.load_timing import NULL_TIMER
    timing = timing if timing is not None else NULL_TIMER
    domain = gda._name_norm(title) if hasattr(gda, "_name_norm") else \
        title.strip().lower().replace(" ", "_")
    before = gda.coverage(agent, domain)
    with timing.stage("read_source", article=title):
        src = gda.read_source(agent, domain, source_text=source_text, source_title=title)
    # EXACT-ARTICLE requirement: a consumption pipeline consumes THIS article — the
    # injected doc or the exact wiki_local page. gda.read_source's last fallback is
    # read_and_ground's FUZZY reference reader, which for a missing title drifts to
    # an unrelated article (a title 'Zzq...' resolves to some other page). Consuming
    # that would mint a topic microtheory whose concepts don't belong to the topic.
    # So a fuzzy-reader-only read is treated as NO readable source (honest null) —
    # we never consume a drifted article. (fed_document / local_wiki / wikipedia are
    # the exact-source reads; reference_reader is the fuzzy fallback.)
    exact = src["found"] and src.get("source") in ("fed_document", "local_wiki", "wikipedia")
    if not exact:
        return {"consumed": False, "reason": "no readable source — no exact article "
                "(honest null; the fuzzy reference reader's drift is not consumed)",
                "domain": domain, "title": title, "before": before, "after": before,
                "n_admitted": 0, "n_rejected": 0, "admitted": [], "rejected": [],
                "delta": {}, "seed_path": None}

    # QUALITY (the self-improvement-cycle fixes, on by default): the NOMINAL filter
    # drops clause fragments at extraction; the CONTEXT-SENSE picker + grounding
    # CACHE ground each surviving concept below.
    with timing.stage("extract_microtheory", article=title):
        extracted = gda.extract_microtheory(domain, src, max_concepts=max_concepts,
                                            nominal_filter=quality,
                                            collapse_agent=(agent if reading_collapse else None))
    if extracted["thin"]:
        return {"consumed": False, "reason": "source named no extractable concepts "
                "(thin article -> thin, not padded)", "domain": domain, "title": title,
                "before": before, "after": before, "n_admitted": 0, "n_rejected": 0,
                "admitted": [], "rejected": [], "delta": {}, "seed_path": None}

    if not gda.traces_to_source(extracted, src):
        return {"consumed": False, "reason": "extracted concepts did not trace to the "
                "article — refusing to teach (earn-not-fabricate guard)", "domain": domain,
                "title": title, "before": before, "after": before, "n_admitted": 0,
                "n_rejected": 0, "admitted": [], "rejected": [], "delta": {},
                "seed_path": None}

    # GROUND + GATE every concept. This is the ~86%-of-load stage: ground_lexeme
    # -> sense_in_context -> pick_sense -> _enumerate_features (WordNet). Its FIRST
    # call in a cold process pays the one-time WordNet corpus init (~1.4s); the
    # timer tags this stage cold (WordNet not yet warm) vs warm, so the perception
    # surfaces that the "bottleneck" is one-time init, not a per-concept cost.
    admitted: list = []
    rejected: list = []
    with timing.stage("ground_lexeme", article=title,
                      n_items=len(extracted["concepts"])):
        for c in extracted["concepts"]:
            lex = ground_lexeme(c, src, domain, language,
                                context_sense=quality, cache=cache, agent=agent)
            if gate:
                gr = gate_lexeme(lex, substrate=None)
                if not gr.admitted:
                    rejected.append({"name": lex["name"], "surface": lex["surface"],
                                     "reason": gr.reason})
                    continue
            admitted.append(lex)

    if not admitted:
        return {"consumed": False, "reason": "no lexeme passed the admissibility gate "
                "(all rejected — honest, nothing installed)", "domain": domain,
                "title": title, "before": before, "after": before, "n_admitted": 0,
                "n_rejected": len(rejected), "admitted": [], "rejected": rejected,
                "delta": {}, "seed_path": None}

    # TEACH — reuse gda.teach_microtheory for the microtheory + has_concept + base
    # manifest + provenance note; the admitted grounded lexemes carry name +
    # (source-traced) definition, so the base install is exactly gda's.
    to_teach = {**extracted, "concepts": [
        {"name": lex["name"], "surface": lex["surface"],
         "definition": lex["definition"]} for lex in admitted]}
    taught = gda.teach_microtheory(agent, to_teach, seeds_dir=seeds_dir)
    # ENRICH the live nodes + the persisted manifest with the grounded lexicon.
    _enrich_installed(agent, taught, admitted)
    _persist_grounding(taught["seed_path"], admitted)
    cg._CACHE.clear()

    after = gda.coverage(agent, domain)
    delta = {"bag": after["bag"] - before["bag"],
             "best": round(after["best"] - before["best"], 4)}
    return {"consumed": True, "reason": "grounded — read, extracted, grounded the "
            "lexicon+machinery+microtheory, gated, taught; concept_graph now edge-"
            "learns the region", "domain": domain, "title": title, "before": before,
            "after": after, "n_admitted": len(admitted), "n_rejected": len(rejected),
            "admitted": admitted, "rejected": rejected, "delta": delta,
            "seed_path": taught["seed_path"],
            "dropped_fragments": extracted.get("dropped_fragments", [])}


# =========================================================================== #
#  CONSUME A BATCH — the headline: N real articles -> M concepts + K microtheories.
# =========================================================================== #

def _snapshot(agent) -> dict:
    """A cheap graph snapshot for the before->after growth measure: the total
    Concept + Microtheory node counts (the global-boot-unperturbed / growth read)."""
    sub = agent.s
    return {"concepts": len(sub.nodes("Concept")),
            "microtheories": len(sub.nodes("Microtheory"))}


def consume(agent, *, titles: Optional[list] = None, articles: int = 8,
            seeds_dir: Path = ACQUIRED, language: str = "en",
            max_concepts: int = 30, gate: bool = True, gvm=None,
            quality: bool = True, cache=None, timing=None, warm: bool = True) -> dict:
    """CONSUME A BATCH of real wiki_local articles — the headline. Iterate `titles`
    (or the first `articles` of DEFAULT_BATCH), consuming each (read -> ground
    lexicon+machinery+microtheory -> gate -> teach). Measures the graph BEFORE and
    AFTER: the lexicon grows by M grounded concepts, K microtheories are minted,
    and each grown topic is now EDGE-LEARNABLE by concept_graph (coverage rose).

    Returns {n_articles, before, after, growth, results, admitted_total,
    rejected_total, microtheories_grown}. The taught content is written to the
    ISOLATED seeds_dir, so the global boot graph is unperturbed.

    When `gvm` (a graph_virtual_memory.GraphVirtualMemory) is supplied, each
    consumed microtheory FLOWS THROUGH DEMAND PAGING: its cluster enters the
    working set, then pages OUT to the mmap corpus slab when over `memory_bound`,
    and pages IN on foveation. Thin, additive wiring — the coverage re-decode is
    read BEFORE any paging (registration is post-batch), so gvm=None (the default)
    leaves the pipeline byte-identical."""
    batch = list(titles) if titles is not None else DEFAULT_BATCH[:articles]
    before = _snapshot(agent)
    # WARM-ONCE (the honest 'make loading faster' fix, on by default): pay the
    # one-time WordNet corpus init NOW, before article 1, so EVERY article grounds
    # WARM. This moves the ~1.4s cold init OUT of article 1's ground stage and into
    # boot — the steady-state per-article rate is then the true (warm) rate. It is
    # NOT a cache: nothing is memoized, the corpus is simply resident. When a
    # LoadTimer is passed, the boot init is itself surfaced as a `boot_warm_wordnet`
    # LatencyObservation so the moved cost is VISIBLE, not hidden.
    if warm and quality:
        from domains import dictionary_lexicon as dl
        warm_ms = dl.warm_wordnet(language)
        if timing is not None and warm_ms > 0.0:
            timing.record("boot_warm_wordnet", warm_ms, phase="boot", n_items=1)
    # ONE shared grounding cache across the batch (the CACHE fix): a word that
    # recurs across articles is a HIT on the second article, not a cold re-read.
    if cache is None and quality:
        from domains.consumption_quality import GroundingCache
        cache = GroundingCache()
    results = [consume_article(agent, t, seeds_dir=seeds_dir, language=language,
                               max_concepts=max_concepts, gate=gate,
                               quality=quality, cache=cache, timing=timing)
               for t in batch]
    if gvm is not None:
        from domains.graph_virtual_memory import page_consumed
        for r in results:
            if page_consumed(gvm, agent, r):
                gvm.enforce()  # the resident cap pages cold clusters to the corpus
    after = _snapshot(agent)
    consumed = [r for r in results if r["consumed"]]
    admitted_total = sum(r["n_admitted"] for r in results)
    rejected_total = sum(r["n_rejected"] for r in results)
    return {
        "n_articles": len(batch), "articles": batch,
        "before": before, "after": after,
        "growth": {"concepts": after["concepts"] - before["concepts"],
                   "microtheories": after["microtheories"] - before["microtheories"]},
        "results": results,
        "admitted_total": admitted_total, "rejected_total": rejected_total,
        "microtheories_grown": [r["domain"] for r in consumed],
    }


__all__ = [
    "ACQUIRED", "DEFAULT_BATCH", "ground_pos", "ground_sense", "ground_lemma",
    "ground_lexeme", "gate_lexeme", "consume_article", "consume",
]
