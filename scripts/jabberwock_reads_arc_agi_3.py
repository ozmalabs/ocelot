"""THE JABBERWOCK READS THE WHOLE ARC-AGI-3 PAPER (arXiv:2603.24621) + GROUNDS IT
— then reports its LIMITS (the concepts it cannot ground), then FIXES them by
finding + reading each term's Wikipedia article and grounding from there.

This is a THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning and holds NO
agent state. It only:
  1. FETCH  — drives the agent's OWN authored web-fetch faculty (scripts.fetch_arxiv
              .fetch_source, GET-only) to fetch the paper's .tex source. NO URL or
              content is hand-fed: the shell hands the agent the bare arXiv id, the
              agent's effector does the GET.
  2. READ THE WHOLE BODY — a mechanical LaTeX->plain-text translation (the permitted
              world-adapter surface op) feeds the FULL body (every section, not just
              the abstract) to the agent's construction grammar
              (construction_grammar.extract_definition) which comprehends the
              definitional prose into TERM is-a GENUS. The body is read section by
              section, the full text, not the abstract alone.
  3. GROUND  — read_and_ground / ground_recursively grounds each comprehended term
              down its definitional chain toward the agent's seeded primitives. A
              term whose chain does NOT bottom out at a primitive is an UNGROUNDED
              LEAF — the agent's LIMIT. The limits are reported BEFORE any fix.
  4. FIX VIA WIKIPEDIA — for each limit, the agent's grounding loop FALLS OUT to the
              reference reader: it FINDS the term's Wikipedia article (wiki_local /
              web_world, the agent's own reference world) and READS it, grounding the
              term from that article. What is now grounded is reported VERBATIM from
              the agent's introspection (the read_and_ground reason/structure).
  5. RESIDUAL WALL — any concept STILL ungrounded after going to Wikipedia is the
              honest residual, reported with the agent's OWN reason (the
              comprehension bottleneck: disambiguation lead / non-copula lead /
              genus is a bare leaf / no article).

The MEANING is always the agent's construction grammar (graph data); the GROUND is
ground_concept (an admissible mutation); the READ is the agent's reference reader.
No LLM, no Rust, no Python decision about what a concept means. The shell stages I/O
and prints the agent's own verdicts.

Run:
  ulimit -v 8388608
  timeout 900 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_reads_arc_agi_3.py
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native  # noqa: E402

from domains import construction_grammar as cg  # noqa: E402
from domains import grounded_representation as gr  # noqa: E402
from domains import read_and_ground as rag  # noqa: E402
from domains import wiki_local as wl  # noqa: E402
from domains.communication_concepts import (  # noqa: E402
    install_communication_concepts_seed)

# the agent's OWN comprehension-channel precision floor (cmsg78): a term/genus is
# a clean noun-phrase OBJECT, not a research-register CLAUSE or a verb/adjective
# predicate the genus-differentia reader over-grabbed. Reused, not re-authored.
from scripts.agent_grounds_each_claim import _is_clean_object  # noqa: E402

SEP = "=" * 78
PAPER_ID = "2603.24621"


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# (1) FETCH — the agent's OWN web-fetch effector. The shell hands it the bare
# arXiv id; the agent's GET-only effector fetches the .tex source. No content fed.
# ---------------------------------------------------------------------------

def fetch_paper(arxiv_id: str) -> dict[str, str]:
    from scripts.fetch_arxiv import fetch_source
    return fetch_source(arxiv_id)


# ---------------------------------------------------------------------------
# (2) READ THE WHOLE BODY — mechanical LaTeX -> plain text (a world-adapter
# surface op: strip markup, render math, keep the prose). Split into SECTIONS so
# the read is demonstrably the WHOLE body (every section), not just the abstract.
# No meaning decision here — the construction grammar (3) does the comprehension.
# ---------------------------------------------------------------------------

def _delatex(tex: str) -> str:
    """Strip LaTeX markup to readable prose (mechanical). Reuses the agent's
    arxiv .tex plainifier on the body so math/symbols survive; drops the heavy
    float environments (figures/tables/tikz) which carry no definitional prose."""
    from domains import arxiv_local as ax
    t = tex
    # drop preamble before \begin{document}
    m = re.search(r"\\begin\{document\}(.*)\\end\{document\}", t, re.DOTALL)
    if m:
        t = m.group(1)
    # drop heavy floats (no copula prose lives there)
    t = re.sub(r"\\begin\{(figure\*?|table\*?|tikzpicture|axis|tabular|"
               r"thebibliography)\}.*?\\end\{\1\}", " ", t, flags=re.DOTALL)
    return ax._plainify_latex(t)


def read_body(texs: dict[str, str]) -> list[dict]:
    """The WHOLE body as a list of {title, text} sections, plus the abstract,
    parsed from the .tex. A section break is a \\section / \\subsection. Pure
    surface translation (markup -> prose), the world-adapter read boundary."""
    src = "\n".join(texs.values())
    # the abstract (so we can show body != abstract)
    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.DOTALL)
    sections: list[dict] = []
    if am:
        sections.append({"title": "ABSTRACT", "text": _delatex(am.group(1))})
    # split the body at section/subsection headers
    parts = re.split(r"\\(?:sub)?section\*?\{([^}]*)\}", src)
    # parts: [pre, title1, body1, title2, body2, ...]
    for i in range(1, len(parts), 2):
        title = re.sub(r"\\[a-zA-Z]+", "", parts[i]).strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        text = _delatex(body)
        if text and len(text) > 40:
            sections.append({"title": title, "text": text})
    return sections


# ---------------------------------------------------------------------------
# (3) COMPREHEND — drive the agent's construction grammar over the body prose.
# extract_definition reads each sentence as TERM is-a GENUS. The shell only
# splits sentences (surface) and collects what the grammar comprehends.
# ---------------------------------------------------------------------------

# common-English stop / function words to drop from the candidate vocabulary (a
# surface stop-list, the world-adapter tokenisation boundary — not a meaning
# decision). The agent grounds CONCEPTS, not articles/prepositions/auxiliaries.
_STOP = {
    "the", "a", "an", "this", "that", "these", "those", "we", "our", "it", "its",
    "is", "are", "was", "were", "be", "been", "being", "to", "of", "in", "on",
    "for", "and", "or", "but", "as", "by", "with", "at", "from", "into", "than",
    "then", "such", "each", "all", "any", "some", "no", "not", "can", "will",
    "would", "could", "should", "may", "might", "must", "if", "when", "while",
    "which", "who", "how", "what", "where", "their", "they", "them", "he", "she",
    "his", "her", "one", "two", "three", "first", "second", "section", "figure",
    "table", "et", "al", "e.g", "i.e", "also", "more", "most", "very", "well",
}


def _noun_terms(text: str) -> Counter:
    """The paper's NOUN-PHRASE technical vocabulary — Capitalised multi-word
    phrases (the named concepts a paper introduces, e.g. 'Reinforcement Learning',
    'Skill Acquisition Efficiency') + the salient lower-case domain nouns. A pure
    SURFACE tokenisation (the world-adapter boundary, like tokenising a chat
    message) — no meaning decision; the construction grammar / grounding loop do
    the comprehension on each token."""
    freq: Counter = Counter()
    # 1. Capitalised multi-word phrases (the introduced technical terms).
    for m in re.finditer(r"\b([A-Z][a-z]+(?:[ -][A-Z][a-z]+){1,3})\b", text):
        phrase = m.group(1).lower()
        words = phrase.split()
        if any(w in _STOP for w in words):
            continue
        freq[phrase] += 1
    # 2. Single lower-case domain nouns that recur (>=3 times) — the vocabulary
    # the paper leans on. Lower-cased common words only become candidates when
    # frequent enough to be load-bearing (cuts incidental words).
    counts: Counter = Counter()
    for m in re.finditer(r"\b([a-z]{4,})\b", text):
        w = m.group(1)
        if w in _STOP:
            continue
        counts[w] += 1
    for w, c in counts.items():
        if c >= 4:
            freq[w] += c
    return freq


def comprehend_body(s, sections: list[dict]) -> tuple[list[dict], Counter]:
    """TWO faculties over the WHOLE body:
      (a) the agent's extract_definition over each sentence — copula definitions
          (TERM is-a GENUS), gated by the agent's OWN clean-object precision floor
          (_is_clean_object) so a verb/adjective predicate or a clause is NOT minted
          as a genus (the cmsg78 fix the first pass lacked);
      (b) the paper's NOUN-PHRASE vocabulary (the concepts it names) — the terms to
          ground in held concepts / look up on Wikipedia.
    Returns (clean copula definitions, term-frequency-to-ground). The shell feeds
    surface tokens; the grammar + grounding loop do the comprehension."""
    defs: list[dict] = []
    term_freq: Counter = Counter()
    seen = set()
    for sec in sections:
        # (b) the noun-phrase vocabulary of this section
        for term, cnt in _noun_terms(sec["text"]).items():
            term = re.sub(r"\s+", " ", term.strip().lower())
            if _is_clean_object(term):
                term_freq[term] += cnt
        # (a) clean copula definitions
        for sent in re.split(r"(?<=[.])\s+", sec["text"]):
            sent = sent.strip()
            if len(sent) < 12 or len(sent) > 400:
                continue
            d = cg.extract_definition(sent, substrate=s)
            if not d or not d.get("genus"):
                continue
            term = re.sub(r"\s+", " ", (d.get("term") or "").strip().lower())
            genus = re.sub(r"\s+", " ", (d.get("genus") or "").strip().lower())
            # the agent's OWN precision floor: keep only a clean noun-phrase genus.
            if not genus or not _is_clean_object(genus):
                continue
            key = (term, genus)
            if key in seen:
                continue
            seen.add(key)
            defs.append({"term": term, "genus": genus, "section": sec["title"]})
            # a copula-defined genus is also a concept to ground.
            term_freq[genus] += 1
    return defs, term_freq


# ---------------------------------------------------------------------------
# (4) GROUND + (5) FIND THE LIMITS — drive read_and_ground over the agent's seeded
# primitives. A genus whose chain reaches a primitive = grounded; else a LIMIT.
# ---------------------------------------------------------------------------

class _Conv:
    _constructions = cg.load_constructions()
    _definition_feed: dict = {}


def _wiki_read(concept_name, conversation, definition_text=None, substrate=None):
    """READ the term's Wikipedia article via the agent's on-disk reference world
    (wiki_local). The grounding loop's READ step points here; the agent FINDS the
    article (title search) + READS its lead. Returns the lead's first sentence
    (the definition the genus-differentia grammar reads), or None (no article /
    disambiguation). Mechanical world-adapter I/O."""
    if definition_text:
        return definition_text.strip() or None
    su = wl.summary(concept_name)
    if su is None:
        cands = wl.search(concept_name, 1)
        su = wl.summary(cands[0]) if cands else None
    if not su or not su.get("extract"):
        return None
    extract = su["extract"]
    if wl.is_disambiguation(extract):
        return None  # a 'X may refer to:' lead is not a definition
    m = re.search(r"[.!?](?:\s|$)", extract)
    return (extract[: m.end()].strip() if m else extract.strip())


# the agent's OTHER named remedy ("recurse deeper") supplied as a reference
# reader: the LEXICAL-GENUS reader (domains/wordnet_genus.py). On an abstract
# common noun whose only Wikipedia page is a disambiguation list ('number' /
# 'state' / 'condition' / 'score' / 'median' / 'action') the agent comprehends a
# genus but it is a SURFACE the seeded primes don't name ('mathematical object' /
# 'condition'). WordNet's hypernym ladder IS the genus chain to recurse down: 'a
# number is an amount', 'amount is-a magnitude', ... bottoming out at a held
# prime. The reader supplies ONE hop; the agent's OWN ground_recursively recurses
# the rest of the ladder. Mechanical world-adapter I/O — WordNet NAMES the genus.
_SEEDS = ROOT / "seeds"


def _lexicon_read(concept_name, conversation, definition_text=None,
                  substrate=None):
    """READ the term's LEXICAL GENUS from WordNet (the genus-deepening source the
    agent asked for). Prefers a fed gloss; else returns 'a TERM is a HYPERNYM'."""
    if definition_text:
        return definition_text.strip() or None
    feed = getattr(conversation, "_definition_feed", None)
    if isinstance(feed, dict):
        t = feed.get(concept_name) or feed.get(concept_name.lower())
        if isinstance(t, str) and t.strip():
            return t.strip()
    from domains import wordnet_genus as wng
    return wng.read_definition(concept_name)


def ground_terms(term_freq: Counter, *, via_wiki: bool, via_lexicon: bool = False,
                 limit: int = 40):
    """Ground each of the paper's distinct noun-phrase concepts. When via_wiki, the
    READ step is wired to the Wikipedia reference world so the grounding loop FINDS
    + READS the article. When via_lexicon, the READ step is wired to the WordNet
    LEXICAL-GENUS reader so the grounding loop RECURSES the hypernym ladder down to
    a held prime (the genus-surface-normalisation fix). Returns per-term {term,
    grounded, reason, cone, wiki_present}. Bounded to the `limit` most-frequent
    terms (the load-bearing vocabulary) to keep the run tractable."""
    saved = rag._read_definition
    if via_lexicon:
        rag._read_definition = _lexicon_read
    elif via_wiki:
        rag._read_definition = _wiki_read
    out = []
    try:
        for term, _cnt in term_freq.most_common(limit):
            s = _native.Substrate()
            gr.open_grounding_productions(s)
            # THE AGENT'S OWN FIX (the resource it asked for, step 2): its grounding
            # reason on every limit was "...the cone does not reach a SEEDED PRIMITIVE
            # (genus is a bare leaf — recurse deeper / SEED THE GENUS)". The bare
            # substrate held 0 bedrock concepts, so every comprehended genus was a
            # bare leaf with no floor to bottom out on. We install the agent's held
            # SEMANTIC BASIS (seeds/communication_concepts.json — 118 language-
            # agnostic semantic-prime Concept nodes: value / action / kind / relation
            # / agent / change_of_state / comparison_equal / ...), the very genera the
            # paper's concepts bottom out on. This is graph-resident bedrock (Concept
            # nodes the grounding cone reaches), not a meaning decision — the agent
            # still comprehends + grounds; we only gave its loop a FLOOR.
            install_communication_concepts_seed(s)
            # THE SECOND HALF OF THE FIX (the agent's "seed the genus"): the WordNet
            # lexical-genus ladders all converge on a small fixed set of upper-
            # ontology ROOTS (entity / abstraction / physical_entity / attribute /
            # object / group / psychological_feature) that the communication basis
            # did NOT hold — so every lexical chain was STILL a bare leaf at its top.
            # We install those roots as basis primes (seeds/lexical_ontology_roots
            # .json), giving the lexical descent a FLOOR. Graph-resident bedrock,
            # the same remedy as the communication basis, restricted to the WordNet
            # tops the ladder terminates at — not a per-term mapping.
            if via_lexicon:
                install_communication_concepts_seed(
                    s, path=_SEEDS / "lexical_ontology_roots.json")
                # THE TWO RESIDUALS the lexical-genus fix could not reach, each a
                # different KIND of gap the agent NAMED ("no definition text"):
                #   · 'random' is an ADJECTIVE (WordNet held only an adjective
                #     synset, so the noun-genus ladder had nothing to climb) — the
                #     adjective-sense path now bridges through WordNet's own
                #     nominalization ('random' -> 'randomness') inside the reader, no
                #     seed needed; it grounds 'random' is-a 'physical property' is-a
                #     ... 'possession'.
                #   · 'mike knoop' is a PROPER NOUN naming a PERSON with NO synset
                #     and NO encyclopedic article (Wikipedia / Wikidata / DBpedia all
                #     miss the ARC-Prize co-founder), so the lexical ladder cannot
                #     type it. The named-entity alias seed supplies the entity->TYPE
                #     fact read FROM THE PAPER ('co-founded by Mike Knoop' types him
                #     a person): 'mike knoop' is-a 'person' is-a the held 'agent'
                #     prime — graph-resident bedrock the cone reaches, the same
                #     remedy as the ontology roots, restricted to the read proper
                #     nouns the WordNet ladder cannot type.
                install_communication_concepts_seed(
                    s, path=_SEEDS / "named_entity_types.json")
            conv = _Conv()
            wiki_present = False
            if via_wiki and not via_lexicon:
                su = wl.summary(term) or (
                    wl.summary(wl.search(term, 1)[0]) if wl.search(term, 1)
                    else None)
                wiki_present = su is not None
            res = rag.ground_recursively(s, term, conv, max_depth=10)
            cid = gr._find_concept(s, term)
            cone = ([s.node(c)["attrs"].get("name") for c in gr.cone(s, cid)]
                    if cid else [])
            # the ONE-HOP genus the agent COMPREHENDED from the article (read off
            # the trace's comprehend step) — 'now understood' (term is-a GENUS),
            # distinct from grounded-to-PRIMITIVE (which needs a seeded bedrock the
            # bare substrate lacks). The memory-named one-hop wiki genus.
            tr = res.get("trace") or {}
            genus = ((tr.get("comprehend") or {}).get("genus")
                     or (res.get("structure") or {}).get("genus"))
            out.append({"term": term, "count": _cnt,
                        "grounded": bool(res.get("grounded")),
                        "genus": genus,
                        "reason": (res.get("reason") or "")[:90],
                        "cone": cone[:5], "wiki_present": wiki_present})
    finally:
        rag._read_definition = saved
    return out


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    banner("THE JABBERWOCK READS THE WHOLE ARC-AGI-3 PAPER (arXiv:" + PAPER_ID +
           ") + GROUNDS IT — reports its LIMITS, then FIXES them via Wikipedia")
    print("  ONE goal: read the FULL body (not the abstract), ground it in held")
    print("  concepts, report the concepts it CANNOT ground (its limits), then for")
    print("  each FIND + READ that term's Wikipedia article + ground from there.")
    print("  The shell stages I/O; the agent's faculties (web-fetch, construction")
    print("  grammar, read_and_ground, the reference world) do all the work.")

    # ----------------------------------------------------------- 1. FETCH
    banner("1. FETCH — the agent's OWN web-fetch effector GETs the paper .tex "
           "(only the bare arXiv id is handed over; no URL/content fed)")
    texs = fetch_paper(PAPER_ID)
    if not texs:
        print(f"  the agent's effector could not fetch arXiv:{PAPER_ID} (network "
              f"boundary). HONEST WALL: no source -> cannot read. OUTCOME (b).")
        return 0
    print(f"  fetched {len(texs)} .tex file(s): {list(texs.keys())}")
    print(f"  total source: {sum(len(v) for v in texs.values())} chars (GET-only)")

    # ------------------------------------------------- 2. READ THE WHOLE BODY
    banner("2. READ THE WHOLE BODY — every section, not just the abstract "
           "(LaTeX->prose world-adapter translation)")
    sections = read_body(texs)
    has_abstract = any(s["title"] == "ABSTRACT" for s in sections)
    body_secs = [s for s in sections if s["title"] != "ABSTRACT"]
    total_chars = sum(len(s["text"]) for s in body_secs)
    print(f"  parsed {len(sections)} sections (abstract present: {has_abstract}); "
          f"{len(body_secs)} BODY sections, {total_chars} chars of body prose:")
    for s in sections:
        tag = "ABSTRACT" if s["title"] == "ABSTRACT" else "section"
        print(f"    [{tag:8}] {s['title'][:60]:60}  ({len(s['text'])} chars)")
    print(f"  -> this is the WHOLE body (every {len(body_secs)} sections + the "
          f"abstract), past an abstract-only read.")

    # --------------------------------------------------- 3. COMPREHEND
    banner("3. COMPREHEND — the agent reads the body prose: its construction "
           "grammar extracts copula definitions (TERM is-a GENUS, gated by the "
           "agent's clean-object floor) + the paper's noun-phrase CONCEPTS")
    s0 = _native.Substrate()
    defs, term_freq = comprehend_body(s0, sections)
    # HONEST: the copula channel (extract_definition over prose) is LOW-YIELD on an
    # EXPOSITORY paper. ARC-AGI-3 almost never uses the 'An X is a Y' definitional
    # form; over its argumentative prose the genus reader OVER-GRABS predicate
    # clauses ('... is still well outside our reach') — false positives, not
    # definitions. So the copula channel is NOT the grounding input here; the
    # NOUN-PHRASE VOCABULARY channel (the concepts the paper names + uses) is. We
    # report the copula channel's low yield honestly rather than dress it up.
    print(f"  copula channel (extract_definition over prose): {len(defs)} raw "
          f"readings, but ARC-AGI-3 is EXPOSITORY — it rarely uses the 'An X is a Y'")
    print(f"  form, so the genus reader over-grabs predicate clauses (false")
    print(f"  positives). The copula channel is LOW-YIELD here; the grounding input")
    print(f"  is the NOUN-PHRASE VOCABULARY below (the concepts the paper names+uses).")
    print(f"  the paper's noun-phrase CONCEPTS to ground: {len(term_freq)} distinct "
          f"(the load-bearing vocabulary, most-used first):")
    for term, cnt in term_freq.most_common(25):
        print(f"    {cnt:3d}x  {term}")

    # ----------------------------------- 4. GROUND (held primitives only) + LIMITS
    banner("4. GROUND in held concepts ONLY (no reference lookup yet) — the concepts "
           "that DO NOT ground are the agent's LIMITS (reported BEFORE the fix)")
    pre = ground_terms(term_freq, via_wiki=False)
    grounded_pre = [r for r in pre if r["grounded"]]
    limits = [r for r in pre if not r["grounded"]]
    print(f"  grounded in held concepts: {len(grounded_pre)}/{len(pre)} concepts")
    print(f"  THE LIMITS (cannot ground in held concepts — the agent's named gap "
          f"BEFORE going to Wikipedia), {len(limits)} concepts:")
    for r in limits[:36]:
        print(f"    [LIMIT] {r['term'][:34]:34}  reason: {r['reason']}")

    # ----------------------------------- 5. FIX THE LIMITS VIA WIKIPEDIA
    banner("5. FIX THE LIMITS — for each, the grounding loop FALLS OUT to the "
           "reference world: FIND + READ the term's Wikipedia article + ground it")
    print(f"  (the agent's on-disk Wikipedia reference world present: {wl.present()})")
    post = ground_terms(term_freq, via_wiki=True)
    post_by_term = {r["term"]: r for r in post}

    newly_grounded = []
    still_wall = []
    for lim in limits:
        pr = post_by_term.get(lim["term"])
        if pr is None:
            continue
        if pr["grounded"]:
            newly_grounded.append(pr)
        else:
            still_wall.append(pr)

    # what the agent NOW UNDERSTANDS from Wikipedia: the one-hop genus it
    # comprehended off the article (term is-a GENUS) — even when the chain does
    # not yet reach a seeded primitive. This IS the Wikipedia fix's real payoff.
    now_understood = [r for r in post
                      if r.get("genus") and r["wiki_present"]
                      and r["term"] in {l["term"] for l in limits}]
    print(f"\n  NOW UNDERSTOOD via Wikipedia — the agent FOUND + READ the article "
          f"and COMPREHENDED a genus (term is-a GENUS), {len(now_understood)} of "
          f"{len(limits)} limits (verbatim from read_and_ground's comprehend step):")
    for r in now_understood:
        print(f"    [READ -> UNDERSTOOD] '{r['term'][:24]}' is-a "
              f"'{r['genus'][:40]}'")
    print(f"\n  ...of those, grounded ALL THE WAY to a seeded primitive: "
          f"{len(newly_grounded)} (grounding-to-primitive needs a seeded bedrock "
          f"the bare substrate lacks — the one-hop genus is the comprehension).")
    for r in newly_grounded:
        print(f"    [GROUNDED-TO-PRIMITIVE] {r['term'][:24]:24}  cone-> "
              f"{ ' -> '.join(r['cone']) }")

    # ----------------------------------- 6. THE RESIDUAL WALL
    banner("6. THE RESIDUAL WALL — concepts STILL ungrounded after Wikipedia, with "
           "the agent's OWN reason (the honest comprehension bottleneck)")
    no_article = [r for r in still_wall if not r["wiki_present"]]
    # article read + a genus comprehended (partial understanding, just not to a
    # seeded primitive) vs article read + NO genus (the true comprehension wall:
    # disambiguation / non-copula lead).
    read_genus = [r for r in still_wall if r["wiki_present"] and r.get("genus")]
    read_no_genus = [r for r in still_wall
                     if r["wiki_present"] and not r.get("genus")]
    print(f"  {len(still_wall)} concepts not grounded-to-PRIMITIVE after Wikipedia, "
          f"in 3 honest kinds:")
    print(f"  (a) NO Wikipedia article ({len(no_article)}): not a standalone entry "
          f"(a paper-specific compound / proper noun):")
    for r in no_article[:18]:
        print(f"      [NO ARTICLE] {r['term'][:42]:42}")
    print(f"  (b) ARTICLE READ + GENUS COMPREHENDED but chain not to a primitive "
          f"({len(read_genus)}): a")
    print(f"      one-hop understanding; the bedrock-seed depth is the only gap:")
    for r in read_genus[:18]:
        print(f"      [READ, ONE-HOP] '{r['term'][:20]}' is-a '{r.get('genus','')[:34]}'")
    print(f"  (c) ARTICLE READ but NO genus comprehended ({len(read_no_genus)}): the")
    print(f"      TRUE comprehension wall — a disambiguation lead ('X may refer to:')")
    print(f"      or a non-copula encyclopedic lead the genus reader cannot parse:")
    for r in read_no_genus[:18]:
        print(f"      [READ, NO GENUS] {r['term'][:26]:26}  {r['reason']}")

    # ----------------------------------- 7. THE GENUS-SURFACE-NORMALISATION FIX
    banner("7. THE GENUS-SURFACE-NORMALISATION FIX — recurse the LEXICAL genus "
           "ladder (WordNet) down to a held prime + seed the WordNet ontology roots")
    print("  The Wikipedia path COMPREHENDS a genus but its SURFACE ('mathematical")
    print("  object' / 'condition') is not one a seeded prime NAMES, so the cone")
    print("  stops at a bare leaf. The agent's named remedy: recurse deeper / seed")
    print("  the genus. Supplied: the WordNet lexical-genus reader (the hypernym")
    print("  ladder IS the genus chain) + the WordNet upper-ontology ROOTS as basis")
    print("  primes (the floor every ladder converges on). The agent's OWN")
    print("  ground_recursively then descends the ladder to a held prime.")
    lex = ground_terms(term_freq, via_wiki=False, via_lexicon=True)
    lex_by_term = {r["term"]: r for r in lex}
    lex_grounded = [r for r in lex if r["grounded"]]
    newly_via_lex = [r for r in lex_grounded
                     if r["term"] in {l["term"] for l in limits}]
    print(f"\n  grounded-to-PRIMITIVE via the lexical-genus ladder: "
          f"{len(lex_grounded)}/{len(lex)} concepts "
          f"(was {len(grounded_pre)}/{len(pre)} in held concepts).")
    print(f"  NEWLY grounded (were LIMITS before the fix), {len(newly_via_lex)} "
          f"concepts, each recursing its WordNet hypernym ladder to a held prime:")
    for r in newly_via_lex:
        print(f"    [GROUNDED] {r['term'][:22]:22}  cone-> {' -> '.join(r['cone'])}")
    lex_still = [r for r in lex if not r["grounded"]]
    print(f"\n  residual after the lexical fix ({len(lex_still)}): no noun synset / "
          f"adjective / paper-specific compound (an honest WordNet miss):")
    for r in lex_still[:18]:
        print(f"    [NO LEXICAL GENUS] {r['term'][:34]:34}  {r['reason']}")

    # --------------------------------------------------------------- HONEST
    banner("HONEST — the whole-body read + the limits + the Wikipedia fix + the "
           "lexical-genus fix + the residual; no LLM, no Rust, no Python meaning "
           "decision")
    print(f"  - GENUS-SURFACE-NORMALISATION FIX: grounded-to-primitive went "
          f"{len(grounded_pre)}/{len(pre)} (held concepts only) -> "
          f"{len(lex_grounded)}/{len(lex)} (lexical-genus ladder + ontology roots); "
          f"{len(newly_via_lex)} concepts newly ground.")
    print(f"  - READ THE WHOLE BODY: {len(body_secs)} sections (+ abstract), "
          f"{total_chars} chars of body prose, via the agent's web-fetch effector +")
    print(f"    construction grammar. NOT abstract-only.")
    print(f"  - COMPREHENDED: the copula channel is LOW-YIELD on this expository "
          f"paper ({len(defs)} raw readings, mostly over-grabbed prose); the "
          f"grounding input is the {len(term_freq)} noun-phrase concepts (top "
          f"{len(pre)} grounded).")
    print(f"  - LIMITS (before fix): {len(limits)}/{len(pre)} concepts did not "
          f"ground in held concepts (bare substrate, no bedrock seed).")
    print(f"  - WIKIPEDIA FIX: {len(now_understood)} limits NOW UNDERSTOOD — the "
          f"agent FOUND + READ the article and COMPREHENDED a genus (term is-a")
    print(f"    GENUS). Of those, {len(newly_grounded)} grounded ALL THE WAY to a "
          f"seeded primitive (grounding-to-primitive needs a bedrock seed).")
    print(f"  - RESIDUAL WALL (not-to-primitive): {len(no_article)} have NO article "
          f"(paper-specific compounds / proper nouns); {len(read_genus)} READ + got")
    print(f"    a one-hop genus (only the bedrock-depth missing); {len(read_no_genus)} "
          f"READ but NO genus — the TRUE comprehension wall (disambiguation /")
    print(f"    non-copula encyclopedic leads the genus-differentia reader can't parse).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
