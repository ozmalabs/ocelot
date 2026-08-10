"""read_and_ground — the LIVE read-and-ground learning loop.

When the agent hits an UNGROUNDED concept (its graph-native coherence is low, so
it KNOWS it doesn't understand — domains/coherence_graph.py), instead of only
abstaining it GOES AND LEARNS: it READS the concept's definition, COMPREHENDS it
with its own construction grammar, GROUNDS it by composing built_from edges over
concepts it already holds (recursively, toward the seeded primitives), and the
caller RE-CHECKS coherence. The loop the whole stack was built toward:

    GAP (low coherence) -> READ (reference reader) -> COMPREHEND (constructions)
        -> GROUND (ground_concept) -> [recurse toward primitives] -> RE-COHERE

This module is a WORLD ADAPTER (CLAUDE.md): it FETCHES external definition text
and SEQUENCES the agent's OWN graph-resident machinery. It owns no reasoning and
makes no decision about WHAT a concept means — the MEANING comes from the agent's
construction grammar parsing the definition (graph DATA), and the GROUNDING is
grounded_representation.ground_concept (an admissible graph mutation). There is no
Python `if` that decides a concept's content, and no LLM.

The pieces it composes (all pre-existing — it wires them, does not rebuild them):
  · READ      domains/web_world.wikipedia_summary  (fetch the definition text),
              or an injected `definition_text` (a fed lead, e.g. a teacher).
  · COMPREHEND domains/construction_grammar.apply_constructions with the
              DEFINITIONAL constructions added to seeds/constructions.json
              ("a {term} is a {genus}" -> {construction:definition, term, genus}).
  · GROUND    domains/grounded_representation.ground_concept (+ open_grounding_
              productions so the Concept->Concept built_from edge is admissible)
              and grounding_reaches_primitives (does the cone reach a primitive).

HONEST scope (stated plainly, the named bottleneck):
  · The loop CLOSES on a definition the agent can COMPREHEND — a simple
    genus form "a X is a Y". The bottleneck is COMPREHENSION: a real complex
    definition (a relative clause / differentia the constructions can't parse)
    returns grounded=False with the honest reason, and the caller ABSTAINS. More
    definitional constructions = the additive next step; we prove the loop + name
    the limit, and never fake grounding a concept whose definition didn't parse.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from domains import construction_grammar as _cg
from domains import grounded_representation as _gr
from domains import coherence_graph as _cohg


# A bare Concept node minted by the PARSER for an unknown surface token (its
# only attr is the context-typing) is NOT a held concept — it is exactly the
# ungrounded placeholder the loop must learn. A GENUINE basis concept is one the
# agent was SEEDED with (a deliberate origin) or one it structurally grounded.
# This is the honest line between "I have a word-shaped node for it" and "I
# actually ground this out" — a graph read of how the node came to be, not a
# decision about its meaning.
def _name_norm(surface: str) -> str:
    """Normalise a surface phrase to the CONCEPT-NAME convention: lowercased,
    stripped, internal whitespace collapsed to single underscores. A multi-word
    genus head ('topological space') -> the multi-word concept name
    ('topological_space') the seed installs. Surface->name normalisation (the
    lexicon's convention), not a meaning decision."""
    return re.sub(r"\s+", "_", (surface or "").lower().strip())


def _is_sense_signal(substrate, concept_name: str, comp: dict,
                     index: Optional[dict] = None) -> bool:
    """True iff a comprehended definition `comp` of the already-held
    `concept_name` carries a PREDICTION-ERROR worth re-grounding for (the entity
    reading): a SENSE-SHIFT (its frame DIFFERS from the term's held frame — a
    homonym) or a SURPRISE (its genus DIFFERS from the term's held built_from).
    A pure graph read against the held node — no decision about meaning."""
    import re as _re
    cid = _gr._find_concept(substrate, _name_norm(concept_name), index)
    if cid is None:
        return False
    a = substrate.node(cid)["attrs"]
    held_frame = a.get("frame")
    new_frame = comp.get("frame")
    new_fname = (_re.sub(r"\s+", "_", new_frame.strip().lower())
                 if isinstance(new_frame, str) and new_frame else None)
    # SENSE-SHIFT: held grounding carries a DIFFERENT frame than this reading.
    if held_frame and new_fname and held_frame != new_fname:
        return True
    # SURPRISE: the new genus is not among the term's held built_from parts.
    new_genus = _name_norm(str(comp.get("genus") or ""))
    if new_genus:
        held_parts = {substrate.node(m)["attrs"].get("name")
                      for m in substrate.neighbours(cid, "built_from")}
        if held_parts and new_genus not in held_parts:
            return True
    return False


_PARSE_PLACEHOLDER_SOURCES = ("context_typed",)

# A bare GENUS LEAF minted by ground_concept's create_missing (origin=
# "grounded_representation", built_from nothing) is a PLACEHOLDER for an as-yet-
# ungrounded genus — NOT a seeded primitive. It is the deeper-grounding frontier
# the recursion must reach, not a genuine basis the cone may bottom out at. Gap 1
# exposes this: a complex definition now COMPREHENDS and grounds term built_from
# <genus>, but if <genus> is only such a bare-minted leaf the cone has NOT
# reached a real primitive (the honest 'genus is a bare leaf — recurse / seed it'
# limit). A seeded primitive (a deliberate origin) IS a genuine basis.
_GROUNDING_LEAF_ORIGINS = ("grounded_representation",)


def _is_basis_concept(substrate, cid) -> bool:
    """True iff the built_from-nothing Concept `cid` is a GENUINE basis concept
    the agent holds (a seeded primitive, or a concept it independently grounded),
    NOT a bare placeholder. Two placeholder kinds are NOT a basis:
      · a parser-minted unknown-surface node (source=='context_typed');
      · a bare genus leaf minted by ground_concept's create_missing
        (origin=='grounded_representation', built_from nothing) — an un-grounded
        genus frontier, not a real primitive.
    A graph read of HOW the node came to be — not a decision about its meaning."""
    a = substrate.node(cid)["attrs"]
    if a.get("source") in _PARSE_PLACEHOLDER_SOURCES:
        return False
    if a.get("origin") in _GROUNDING_LEAF_ORIGINS:
        return False
    return True


# A "held" concept the agent already grounds out: a Concept node that is either a
# GENUINE basis concept (a seeded primitive, built_from nothing AND not a parse
# placeholder) or one whose built_from cone reaches such a primitive. The
# recursion bottoms out on these.
def _is_held(substrate, name: str, *, index: Optional[dict] = None) -> bool:
    """True iff `name` is a Concept the agent already grounds out — a genuine
    basis concept (built_from nothing, not a parse placeholder) OR a concept
    whose built_from cone reaches such a basis. A pure graph read (no decision);
    the recursion stops here. A bare parse-placeholder Concept is NOT held — it
    is the ungrounded concept the loop learns."""
    cid = _gr._find_concept(substrate, name, index)
    if cid is None:
        return False
    if _gr.is_primitive(substrate, cid):
        return _is_basis_concept(substrate, cid)
    # built_from edges present -> structurally grounded iff the cone reaches a
    # genuine basis primitive (not a placeholder leaf).
    proof = _gr.grounding_reaches_primitives(substrate, cid)
    if not proof["grounded"]:
        return False
    # confirm at least one reached primitive is a genuine basis (not a parse
    # placeholder) — else the cone bottoms out at an ungrounded leaf.
    members = _gr.cone(substrate, cid)
    for m in members:
        if _gr.is_primitive(substrate, m) and _is_basis_concept(substrate, m):
            return True
    return False


def _concept_exists(substrate, name: str, *, index: Optional[dict] = None) -> bool:
    return _gr._find_concept(substrate, name, index) is not None


def _bedrock_head(substrate, genus_name: str, *,
                  index: Optional[dict] = None) -> Optional[str]:
    """If a MULTI-WORD genus ('fundamental_equivalence_relation',
    'geometrical_space', 'topological_space') is not itself held but its HEAD NOUN
    ('relation', 'space') IS a held SEEDED math primitive (the bedrock), return
    the head-noun primitive name — the descent BOTTOMS OUT there instead of
    climbing one hop further into a Wikipedia disambiguation page. None when the
    genus is single-word, already held, or its head is not a seeded primitive.

    The genus-differentia structure says the genus IS its head noun ('topological
    space' is-a 'space'); when the head is one of the agent's seeded math
    primitives, that head is the bedrock and the climb is done. Reuses the
    existing head-noun normalisation (the multi-word concept name's last token); a
    surface->primitive mapping, not a meaning decision. The HEAD must be a GENUINE
    basis concept (origin math_foundations / a seeded primitive), not a bare
    placeholder leaf — _is_held confirms that."""
    parts = (genus_name or "").replace("_", " ").split()
    if len(parts) <= 1:
        return None
    head = _name_norm(parts[-1])
    if head == _name_norm(genus_name):
        return None
    if _is_held(substrate, head, index=index):
        return head
    return None


def _genus_has_own_page(genus_name: str, conversation, substrate=None) -> bool:
    """True iff the multi-word genus phrase has a definition of its OWN to recurse
    into — a fed gloss (`_definition_feed`) OR an EXACT-title Wikipedia page (NOT a
    fuzzy search hit to a differently-named title). When True, the descent recurses
    on the genus normally and climbs through its real intermediate node
    ('topological space' has its own page -> recurse, keep the depth-2 chain). When
    False ('fundamental equivalence relation', 'geometrical space' — no own page;
    a fuzzy search would DRIFT to a different-named title and break the chain) the
    bedrock-head termination fires instead. A data-availability check (the same
    role as the existing no-page head-noun fallback), not a meaning decision."""
    g = (genus_name or "").replace("_", " ").strip()
    if not g:
        return False
    feed = getattr(conversation, "_definition_feed", None)
    if isinstance(feed, dict) and (g in feed or g.lower() in feed
                                   or genus_name in feed):
        return True
    # consult the genre conventions: an injected/fed-only world has no wiki.
    try:
        from domains import wiki_local as _wl
        su = _wl.summary(g)  # EXACT-title lookup (no fuzzy search drift)
        return su is not None and bool(su.get("extract"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# READ — fetch the definition text for a concept.
# ---------------------------------------------------------------------------

def _plainify_proofwiki(latex_prose: str) -> str:
    """Turn ProofWiki LaTeX-markup prose into the plain text the construction
    grammar reads: a `[[Definition:Genus|surface]]` wikilink -> its surface
    ('subset'), a bare `[[Definition:Genus]]` -> 'Genus', '''bold''' -> the bare
    term, `$...$` math -> dropped, newlines -> spaces. A mechanical markup->text
    translation (a world-adapter surface op), NOT a meaning decision — the genus
    the grammar extracts is the genus the source NAMED in its wikilink."""
    t = latex_prose or ""
    t = t.replace("\\n", "\n")
    # [[Definition:X|surface]] -> surface ; [[X|surface]] -> surface ; [[X]] -> X
    t = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\[\[(?:Definition:)?([^\]|]+)\]\]", r"\1", t)
    t = t.replace("'''", "").replace("''", "")
    t = re.sub(r"\$[^$]*\$", " ", t)            # drop inline math
    t = re.sub(r"\{\{[^}]*\}\}", " ", t)         # drop templates
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _naturalproofs_lead(concept_name: str, entry: dict) -> Optional[str]:
    """Build a COMPREHENSIBLE definitional lead ('the TERM is the GENUS ...') from
    a NaturalProofs/ProofWiki entry. ProofWiki definitions read 'Let ... The
    '''term''' ... is the [[Definition:genus|genus]] ...': we take the SENTENCE
    that defines the term (contains the term + a copula) and plainify its markup,
    so the agent's genus-differentia grammar extracts the genus the SOURCE named.
    None when no copula sentence is present (the honest un-comprehended case —
    e.g. a definition stated only as an equation)."""
    plain = _plainify_proofwiki(entry.get("text", ""))
    if not plain:
        return None
    name = (concept_name or "").replace("_", " ").strip().lower()
    # the term head (last word) — ProofWiki bolds the bare term ('kernel').
    head = name.split()[-1] if name else ""
    sentences = re.split(r"(?<=[.])\s+|\n+", plain)
    # prefer the sentence that mentions the term AND has an 'is a/the' copula.
    for sent in sentences:
        sl = sent.lower()
        if head and head in sl and re.search(r"\bis\s+(?:a|an|the)\b", sl):
            return sent.strip()
    # else the first 'X is a/the ...' copula sentence at all.
    for sent in sentences:
        if re.search(r"\bis\s+(?:a|an|the)\b", sent.lower()):
            return sent.strip()
    return None


def _read_naturalproofs_definition(concept_name: str) -> Optional[str]:
    """READ a concept's DEFINITION from the NaturalProofs corpus (the most-specific
    source for a mathematical definition). Returns a comprehensible definitional
    lead ('the kernel is the subset ...') the construction grammar can parse, or
    None when the corpus holds no definition for the name OR the definition has no
    copula sentence (honest miss -> the caller falls through to Wikipedia).
    Mechanical world-adapter I/O — no decision about meaning."""
    try:
        from domains import naturalproofs_local as _npl
        if not _npl.present():
            return None
        entry = _npl.definition(concept_name)
        if not entry:
            return None
        return _naturalproofs_lead(concept_name, entry)
    except Exception:
        return None


_PREAMBLE_LEAD = re.compile(r"^\s*(let|given|suppose|fix|consider|assume)\b",
                            re.IGNORECASE)


def _richer_if_preamble(lead: Optional[str], full: Optional[str],
                        headword: Optional[str] = None) -> Optional[str]:
    """If the corpus's chosen LEAD sentence is a research-register PREAMBLE ('Let
    X be Y' / 'Given a W' / 'Fix ...'), return a BOUNDED window = the leading
    preamble sentence(s) + the FIRST subsequent sentence that defines the TERM (or
    the first subsequent copula sentence), so the comprehension's preamble-binder
    can bind the preamble and find the term's definition WITHOUT pulling in the
    whole (TOC-laden, multi-paragraph) Idea prose. Otherwise return the lead
    unchanged — the common path is preserved EXACTLY. A mechanical world-adapter
    choice (which text to hand the grammar), not a meaning decision."""
    if not (lead and full and _PREAMBLE_LEAD.match(lead) and full != lead):
        return lead
    sents = _cg._split_sentences(full)
    if len(sents) < 2:
        return lead
    # leading preamble sentence(s).
    win: list[str] = []
    i = 0
    while i < len(sents) and _PREAMBLE_LEAD.match(sents[i]):
        win.append(sents[i])
        i += 1
    if not win:
        return lead
    hw = (headword or "").replace("_", " ").lower().strip()
    head = hw.split()[-1] if hw else ""
    # the first subsequent sentence that names the headword + has a copula; else
    # the first subsequent copula sentence.
    chosen = None
    for sent in sents[i:]:
        sl = sent.lower()
        if (hw and hw in sl or head and head in sl) and re.search(
                r"\bis\b|\bare\b|consists of|refers to|denotes", sl):
            chosen = sent
            break
    if chosen is None:
        for sent in sents[i:]:
            if re.search(r"\bis\b|\bare\b|consists of|refers to|denotes",
                         sent.lower()):
                chosen = sent
                break
    if chosen is None:
        return lead
    return " ".join(win + [chosen])


def _read_stacks_definition(concept_name: str) -> Optional[str]:
    """READ a concept's DEFINITION from the Stacks Project corpus (the rigorous
    research-tier source — 1,721 definitions in algebraic-geometry LaTeX). Returns
    the defining LEAD sentence the construction grammar can parse, or None when
    the corpus holds no definition OR the LaTeX plainified to no copula sentence
    (the dense-LaTeX honest miss -> the caller falls through to nLab). Mechanical
    world-adapter I/O — no decision about meaning. HONEST: the LaTeX-stripping is
    minimal/lossy (math dropped), so a formula-only definition yields thin prose."""
    try:
        from domains import stacks_local as _st
        if not _st.present():
            return None
        entry = _st.definition(concept_name)
        if not entry or not entry.get("lead"):
            return None
        # research register: if the lead is a 'Let ... ' preamble, hand the FULL
        # prose so the comprehension binds the preamble + finds the term sentence.
        return _richer_if_preamble(entry["lead"], entry.get("text"),
                                   headword=concept_name)
    except Exception:
        return None


def _read_nlab_definition(concept_name: str) -> Optional[str]:
    """READ a concept's DEFINITION from the nLab corpus (the research-MATH wiki —
    19,097 pages: classifying space / spectral sequence / cobordism / spin, the
    research tier the lower corpora LACKED). Returns the page's '## Idea' lead
    sentence the construction grammar can parse, or None when the corpus holds no
    page OR the instiki lead plainified to no readable prose (the dense-prose
    honest miss -> the caller falls through to Wikipedia). Mechanical world-adapter
    I/O — no decision about meaning. HONEST: the instiki-stripping is minimal/lossy
    (inline LaTeX dropped), so a formula-only Idea yields thin prose."""
    try:
        from domains import nlab_local as _nl
        if not _nl.present():
            return None
        entry = _nl.definition(concept_name)
        if not entry or not entry.get("text"):
            return None
        # research register: if the lead sentence is a 'Let/Given/Fix ...'
        # preamble, hand the FULL Idea prose (entry['lead']) so the comprehension
        # binds the preamble + finds the term-defining sentence.
        return _richer_if_preamble(entry["text"], entry.get("lead"),
                                   headword=concept_name)
    except Exception:
        return None


def _lead_is_definition(substrate, source: str) -> bool:
    """Does the agent's UNDERSTANDING of `source` say the LEAD sentence IS the
    definition? Reads the held genre CONVENTIONS (`lead_defines`) off the source
    concept (source_provenance.conventions_for_source) — so 'take the lead as the
    definition' is JUSTIFIED BY the held understanding of the encyclopedia genre,
    not an unexplained Python constant. Defaults True when no held conventions
    are reachable (the prior un-justified behaviour, preserved additively)."""
    try:
        from domains import source_provenance as _sp
        conv = _sp.conventions_for_source(substrate, source)
        if conv is not None:
            return bool(conv.get("lead_defines", True))
    except Exception:
        pass
    return True


def _first_disambiguation_sense(extract: str) -> Optional[str]:
    """A HIGH-PRECISION reading of a 'X may refer to:' disambiguation extract: only
    when the first sense is an ABBREVIATION EXPANSION ('an abbreviated form of
    administration', 'short for ...') do we return the expanded NOUN — the
    abbreviation grounds AS its expansion ('admin' -> 'administration'). We do NOT
    ground an arbitrary first sense (a proper-name / one-of-many reading would be
    noise); a bare stub or a non-abbreviation list returns None."""
    low = extract.lower()
    i = low.find("may refer to")
    tail = extract[i + 12:] if i >= 0 else extract
    for line in re.split(r"[\n\r]+", tail):
        s = line.strip().lstrip("-*•·.0123456789) ").strip()
        if len(s) < 8 or not re.search(r"[A-Za-z]{3,}", s):
            continue
        m = re.search(r"(?:abbreviat\w+|short|stands?|acronym|initialism)\b"
                      r"[^a-z]*(?:form\s+)?(?:of|for)?\s+(?:the\s+words?\s+)?"
                      r"([a-z][a-z]{3,})", s.lower())
        return m.group(1) if m else None   # only the first sense is consulted
    return None


def _read_definition(concept_name: str, conversation,
                     definition_text: Optional[str] = None,
                     substrate=None) -> Optional[str]:
    """READ: get the concept's DEFINITION text. Prefers an injected
    `definition_text` (a fed lead — a teacher / a test feed). Otherwise it does
    what a person does when they don't know a word: LOOK IT UP via the reference
    reader (web_world Wikipedia lead extract). Returns the text or None (web
    unreachable / no page) — mechanical world-adapter I/O, no decision.

    UNDERSTANDING-DRIVEN: that the LEAD sentence IS the definition is JUSTIFIED
    by the agent's HELD encyclopedia conventions (`lead_defines`, consulted via
    source_provenance), not an unexplained constant — a competent reader knows
    the genre. `substrate` (optional) lets the read consult those held
    conventions; without it the prior default (lead-defines) stands."""
    if definition_text:
        return definition_text.strip() or None
    # In-process definition feed (a host may stage definitions the agent reads
    # before any network, e.g. a teacher's gloss): conversation._definition_feed
    # maps concept-name -> definition text.
    feed = getattr(conversation, "_definition_feed", None)
    if isinstance(feed, dict):
        t = feed.get(concept_name) or feed.get(concept_name.lower())
        if isinstance(t, str) and t.strip():
            return t.strip()
    # THE READING STACK (the FULL stack — research-tier complete) — try the
    # MOST-SPECIFIC corpus first, falling through to the broad encyclopedia. The
    # precedence for a mathematical DEFINITION:
    #   1. NaturalProofs — FOUNDATIONAL defs WITH proofs (ProofWiki + textbooks:
    #      kernel / image / quotient / rank / boundary).
    #   2. Stacks Project — the RIGOROUS RESEARCH defs (1,721 algebraic-geometry
    #      definitions + 13,180 proofs — the rigorous derivation tier).
    #   3. nLab — the RESEARCH-MATH defs + context (19,097 pages: classifying
    #      space / spectral sequence / cobordism / spin — the research tier the
    #      LOWER corpora LACKED).
    #   4. Wikipedia — the BROAD fallback.
    # First-that-resolves a substantive definition; honest None if none. With nLab
    # + Stacks JOINED the prior named gap (the research-tier DEFINITIONS + PROOFS)
    # is now CLOSED — the corpus is data-complete to the research tier. HONEST: the
    # nLab/Stacks markup-stripping is minimal/lossy and the dense research prose
    # grounds only PARTIALLY (the named next frontier — comprehension depth).
    npd = _read_naturalproofs_definition(concept_name)
    if npd:
        return npd
    std = _read_stacks_definition(concept_name)
    if std:
        return std
    nld = _read_nlab_definition(concept_name)
    if nld:
        return nld
    # Else look it up in the external reference (Wikipedia lead extract). That
    # the FIRST sentence of the lead IS the definition is the agent applying its
    # held UNDERSTANDING of the encyclopedia genre (the `lead_defines`
    # convention — read off the held `wikipedia`/`encyclopedia` concept).
    try:
        from domains import web_world as ww
        titles = ww.wikipedia_search(concept_name, limit=1)
        summ = ww.wikipedia_summary(titles[0]) if titles else \
            ww.wikipedia_summary(concept_name)
        if summ and summ.get("extract"):
            # DISAMBIGUATION SKIP: a 'X may refer to:' lead is NOT a definition —
            # it is a list of senses. Return None (no definition) so the descent
            # treats it as un-comprehended and does NOT ground a bogus genus from
            # it. This is what stops the math descent climbing one hop too far
            # into the 'Space'/'Relation'/'Set' disambiguation pages: the genus
            # was already a seeded bedrock primitive, so the descent bottoms out
            # at it instead of poisoning the chain with a near-miss. (Cheap
            # lead-shape detector in wiki_local — no decision about meaning.)
            try:
                from domains import wiki_local as _wl
                if _wl.is_disambiguation(summ["extract"]):
                    # A 'X may refer to:' page is a list of SENSES, not a single
                    # definition — but the senses are often listed in the extract
                    # ('Admin: an abbreviated form of administration …'). Read the
                    # FIRST listed sense as the definition (the dominant reading a
                    # person takes), so an abbreviation/acronym grounds via it.
                    # None only when no sense is listed (a bare stub).
                    first = _first_disambiguation_sense(summ["extract"])
                    return (f"{concept_name} is {first}" if first else None)
            except Exception:
                pass
            if not _lead_is_definition(substrate, summ.get("source", "")):
                return summ["extract"].strip()  # genre says lead is not the def
            m = re.search(r"[.!?](?:\s|$)", summ["extract"])
            return (summ["extract"][: m.end()].strip() if m
                    else summ["extract"].strip())
    except Exception:
        return None
    return None


def _read_def(concept_name: str, conversation, definition_text=None,
              substrate=None) -> Optional[str]:
    """Call the (possibly monkeypatched) `_read_definition`, passing `substrate`
    when its signature accepts it (the real one does — for the held-conventions
    read) and falling back to the 3-arg form when a host has replaced it with a
    narrower reader (deep_recursive_grounding's `_wiki_read`). Keeps the
    understanding-driven read additive without breaking patched readers."""
    try:
        return _read_definition(concept_name, conversation, definition_text,
                                substrate=substrate)
    except TypeError:
        return _read_definition(concept_name, conversation, definition_text)


def _read_provenance(concept_name: str, conversation, substrate=None
                     ) -> Optional[dict[str, Any]]:
    """The PROVENANCE of the definition the agent READ for `concept_name` —
    WHERE/WHO/HOW/WHAT/WHEN it came from. A competent reader knows what it read;
    the source is part of the meaning. Returns the provenance dict, or None when
    the source is not a held/modeled one (a fed teacher gloss has no external
    source — provenance None, the grounding is then a taught fact not an
    attributed one).

    Mechanical world-adapter read: when the definition came from the reference
    reader (Wikipedia), the wiki_local summary already carries the provenance
    template (source/genre/who/how/where/when). We re-consult it for the title
    (the WHERE) and attach the agent's HELD epistemic understanding off the
    `wikipedia` concept via source_provenance. No meaning decision."""
    # A fed/in-process definition (teacher gloss / test feed) has no external
    # source — do NOT fabricate a Wikipedia provenance for it.
    if getattr(conversation, "_definition_feed", None) and \
            isinstance(conversation._definition_feed, dict) and \
            (concept_name in conversation._definition_feed or
             concept_name.lower() in conversation._definition_feed):
        return None
    try:
        from domains import web_world as ww
        titles = ww.wikipedia_search(concept_name, limit=1)
        summ = ww.wikipedia_summary(titles[0]) if titles else \
            ww.wikipedia_summary(concept_name)
    except Exception:
        return None
    if not summ:
        return None
    prov = summ.get("provenance")
    if isinstance(prov, dict):
        return dict(prov)
    # The summary came from a source without a provenance template — derive the
    # WHERE (title) and read the rest off the held source understanding.
    try:
        from domains import source_provenance as _sp
        return _sp.provenance_for_source(substrate, summ.get("source", ""),
                                         where=summ.get("title"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# COMPREHEND — APPLY the held genus-differentia structure to the definition.
#
# The COMPREHENSION boundary is no longer a list of clause markers screening a
# per-form match: the ONE general genus-extraction (construction_grammar.
# extract_definition) REALIZES the held genus-differentia structure — it
# COMPREHENDS the leading FRAME + REGISTER adjuncts (nothing stripped), finds the
# copula, and takes the genus head noun phrase, STOPPING at the differentia
# markers itself. The remaining honest limit is a sentence with no extractable
# genus (no copula / a pronoun-only predicate) -> None.
# ---------------------------------------------------------------------------


def _comprehend_definition(text: str, constructions: list[dict],
                           language: str = "en",
                           substrate=None,
                           headword: Optional[str] = None
                           ) -> Optional[dict[str, Any]]:
    """COMPREHEND: parse a definition sentence by APPLYING the agent's held
    genus-differentia STRUCTURE (the `definition` communication-concept — a
    linguistic universal held as graph data). ONE general genus-extraction
    (construction_grammar.extract_definition) realizes that structure over ANY
    surface form: COMPREHEND the leading FRAME adjunct ('In <field>,' -> frame:
    which Mt to ground in) and REGISTER adjunct ('roughly speaking,'/'formally,'
    -> register: how confidently) — NOTHING stripped — find the copula, take the
    HEAD NOUN of the genus noun phrase (stopping at a differentia marker
    that/which/used/with/for/of/whose/where/,), and return {term, genus,
    differentia, frame, register}. NO per-form pattern list — the same one
    structure parses 'a widget is a device', 'In mathematics, a manifold is a
    topological space that …', and the rest.

    Returns a meaning frame {construction:'definition', term, genus, differentia,
    frame, register, combination} when a genus is extractable, else None — the
    honest un-comprehended case (no copula / a pronoun-only predicate): the
    genuine remaining limit, never a faked parse. frame/register are the
    COMPREHENDED adjuncts (frame=None when no domain named; register='exact' by
    default) — the grounding step USES them (the Mt + the confidence).

    Faithful: the structure is the held UNDERSTANDING (graph data); the
    extraction is the permitted thin BOUNDARY parse applying it (CLAUDE.md), not
    a per-concept decision and no LLM."""
    if not text:
        return None
    # Pass the HEADWORD (the concept being defined / page title) so the research-
    # register comprehension can PREFER the sentence that defines the TERM over a
    # 'Let X be Y' preamble's binding sentence (the live fix).
    d = _cg.extract_definition(text, substrate=substrate, term=headword)
    if d is None:
        return None
    term = str(d.get("term") or "").strip()
    genus = str(d.get("genus") or "").strip()
    if not genus:
        return None
    # carry the expectation-based SIGNALS through (the entity reading): the
    # register STATUS (canonical | hedged), the resolved CONFIDENCE, and the
    # per-slot present|absent|different signals. The GROUND step consumes them
    # (sense-shift on a different frame; canonical-vs-hedged confidence).
    return {"construction": "definition", "term": term, "genus": genus,
            "differentia": d.get("differentia", ""),
            "frame": d.get("frame"), "register": d.get("register", "canonical"),
            "register_status": d.get("register_status", "canonical"),
            "confidence": d.get("confidence"),
            "signals": d.get("signals", {}), "slots": d.get("slots", {}),
            "combination": f"isa({_name_norm(term)}, {_name_norm(genus)})"}


# ---------------------------------------------------------------------------
# The LOOP — read -> comprehend -> ground -> recurse -> confirm.
# ---------------------------------------------------------------------------

# The DEFAULT descent depth: a REAL recursive descent toward the seeded
# primitives, not the shallow one-hop learn (the historical max_depth=2). A
# definitional chain bordism -> cobordism -> manifold -> topological_space ->
# … -> primitive is several hops; 6 climbs a deep real chain while bounding the
# work (with cycle-detection the bound is for runaway DEFINITION chains, not
# loops). This realises the agent's OWN derived principle: a compositional
# whole = its parts + combination rules, applied RECURSIVELY until the parts are
# primitives — grounding-to-primitives IS that recursion.
_DEFAULT_MAX_DEPTH = 6


def read_and_ground(substrate, concept_name: str, conversation, *,
                    depth: int = 0, max_depth: int = _DEFAULT_MAX_DEPTH,
                    definition_text: Optional[str] = None,
                    language: str = "en",
                    _index: Optional[dict] = None,
                    _visiting: Optional[set] = None) -> dict[str, Any]:
    """LEARN an ungrounded concept by a DEEP RECURSIVE DESCENT down its whole
    definitional chain — read, comprehend, ground EACH un-held ancestor, depth-
    first, until the chain bottoms out at seeded primitives (or honestly stalls
    where a definition won't comprehend).

    READ the concept's definition -> COMPREHEND it into a built_from genus via
    the construction grammar -> if the genus is itself UN-HELD and depth<max_depth
    and not already on the active path, RECURSE on the GENUS FIRST (depth-first
    toward the seeded primitives) -> then GROUND the term (ground_concept writes
    the built_from edge + the combination) -> confirm the term's cone now reaches
    a GENUINE basis primitive.

    `_visiting` is the CYCLE-DETECTION set: the concept names currently on the
    active recursion path. A definitional cycle (a -> b -> a, or a self-reference
    a -> a) is detected when a genus is already in `_visiting`; that branch
    returns ungrounded with the honest 'cycle' reason instead of recursing
    forever. `max_depth` bounds runaway (non-cyclic) definition chains.

    Returns {grounded, structure, trace, reason}:
      · grounded   — does concept_name now structurally ground (cone reaches a
                     genuine basis primitive)?
      · structure  — {term, genus, combination, primitives, depth} recovered.
      · trace      — the per-level READ->COMPREHEND->GROUND steps; the recursion's
                     sub-traces nest under 'recursed'.
      · reason     — on failure, the HONEST reason (the comprehension bottleneck:
                     'no definition text' / 'definition did not comprehend' /
                     'genus is a bare leaf' / 'cycle' / 'depth limit').

    Faithful: the MEANING is the construction grammar's (graph data); the GROUND
    is ground_concept (an admissible mutation); the traversal climbs the agent's
    own built_from graph. No Python decides what the concept means; no LLM."""
    index = _index if _index is not None else _gr._concept_by_name(substrate)
    constructions = getattr(conversation, "_constructions", None) or \
        _cg.load_constructions()
    visiting = _visiting if _visiting is not None else set()
    trace: dict[str, Any] = {"concept": concept_name, "depth": depth}

    # Already held? Usually nothing to learn — it grounds out as-is. BUT the
    # ENTITY reading: at the TOP level, if a NEW definition is available for a
    # held term, READ it against what's held — a DIFFERENT frame is a SENSE-SHIFT
    # (a homonym: a distinct sense, not the same concept) and a DIFFERENT genus is
    # a SURPRISE. Both are prediction-error SIGNAL the agent must comprehend
    # rather than blindly returning 'already grounded'. We only re-read at depth 0
    # (the recursion still bottoms out on held ancestors) and only when a reading
    # is actually available (a fed definition / text) — else the short-circuit
    # stands. The sense-shift/surprise handling lives in the GROUND step below.
    if _is_held(substrate, concept_name, index=index):
        peek = None
        if depth == 0:
            _t = _read_def(concept_name, conversation, definition_text,
                           substrate=substrate)
            if _t:
                peek = _cg.extract_definition(_t, substrate=substrate,
                                              term=concept_name)
        if not (peek and _is_sense_signal(substrate, concept_name, peek, index)):
            trace["step"] = "already_grounded"
            return {"grounded": True, "structure": None, "trace": trace,
                    "reason": "already grounded"}
        trace["reread_signal"] = peek.get("signals")

    # CYCLE DETECTION: this concept is already on the active recursion path (a
    # definitional cycle a -> … -> a). Bottoming out here is the honest stop — we
    # never recurse into a loop. (The caller already recursed on this name.)
    cname_norm = _name_norm(concept_name)
    if cname_norm in visiting:
        trace["step"] = "cycle"
        return {"grounded": False, "structure": None, "trace": trace,
                "reason": (f"cycle: '{concept_name}' is already on the active "
                           f"grounding path -> stop (no infinite descent)")}
    # DEPTH LIMIT: a runaway (non-cyclic) definition chain longer than max_depth.
    if depth > max_depth:
        trace["step"] = "depth_limit"
        return {"grounded": False, "structure": None, "trace": trace,
                "reason": (f"depth limit {max_depth} reached without bottoming "
                           f"out at a primitive (definition chain too deep)")}

    # READ.
    text = _read_def(concept_name, conversation, definition_text,
                     substrate=substrate)
    # HEAD-NOUN fallback (mechanical world-adapter I/O, not a meaning decision):
    # a multi-word genus NP often has no reference page of its own ('geometrical
    # space', 'algebraic curve') though its HEAD NOUN does ('space', 'curve').
    # The genus-differentia structure says the genus IS the head noun, so when
    # the full phrase has no definition of its own we comprehend it AS its head:
    # 'geometrical space' is-a 'space'. This grounds the phrase built_from its
    # head (an admissible edge) and lets the descent continue on the head — a
    # lookup retry on data availability, the same role as the search variants.
    head_norm = ""
    parts = concept_name.replace("_", " ").split() if concept_name else []
    if (not text and definition_text is None and len(parts) > 1):
        head = parts[-1]
        if _read_def(head, conversation, None, substrate=substrate):
            head_norm = _name_norm(head)
    trace["read"] = text or (f"(no page for {concept_name!r}; head noun "
                             f"{head_norm!r})" if head_norm else text)
    if not text and head_norm:
        # synthesize the trivial genus-differentia parse 'NP is-a HEAD' and let
        # the normal GROUND + recurse-on-genus path below take over (so the head
        # itself gets read+grounded toward a primitive).
        trace["head_noun_fallback"] = head_norm
        frame = {"construction": "definition",
                 "term": _name_norm(concept_name), "genus": head_norm,
                 "differentia": "", "frame": None, "register": "exact",
                 "combination": f"isa({_name_norm(concept_name)}, {head_norm})"}
    elif not text:
        trace["step"] = "no_definition"
        return {"grounded": False, "structure": None, "trace": trace,
                "reason": "no definition text (web unreachable / no page)"}
    else:
        frame = None  # filled by COMPREHEND below.

    # COMPREHEND — apply the held genus-differentia structure to the definition.
    # (Skipped when the head-noun fallback already synthesized the 'NP is-a HEAD'
    # frame above.)
    if frame is None:
        frame = _comprehend_definition(text, constructions, language,
                                       substrate=substrate,
                                       headword=concept_name)
    trace["comprehend"] = frame
    if frame is None:
        trace["step"] = "did_not_comprehend"
        return {"grounded": False, "structure": None, "trace": trace,
                "reason": ("definition did not comprehend (no definitional "
                           "construction matched — the comprehension bottleneck)")}

    # Normalise the term + genus surface to the CONCEPT-NAME convention (lower,
    # internal whitespace -> '_'): a multi-word genus head ('topological space')
    # is the multi-word concept 'topological_space' the seed installs. This is a
    # surface->name normalisation (the same the lexicon uses), NOT a meaning
    # decision — so a multi-word genus extracted by Gap 1's constructions grounds
    # onto the held multi-word primitive.
    term = _name_norm(str(frame.get("term") or concept_name))
    genus = _name_norm(str(frame.get("genus") or ""))
    combination = frame.get("combination") or f"isa({term}, {genus})"
    # The COMPREHENDED adjuncts + SIGNALS (the entity reading): the FRAME (which
    # Mt to ground in), the REGISTER class + its STATUS (canonical | hedged) and
    # the resolved CONFIDENCE band, and the per-slot present|absent|different
    # signals. These are MEANING, parsed into structure and USED below at GROUND
    # time — not stripped.
    frame_domain = frame.get("frame")
    register = frame.get("register") or "canonical"
    register_status = frame.get("register_status") or "canonical"
    confidence = frame.get("confidence")
    signals = frame.get("signals", {})
    structure = {"term": term, "genus": genus, "combination": combination,
                 "frame": frame_domain, "register": register,
                 "register_status": register_status, "confidence": confidence,
                 "signals": signals}
    trace["structure"] = structure
    if not genus:
        trace["step"] = "no_genus"
        return {"grounded": False, "structure": structure, "trace": trace,
                "reason": "comprehended but no genus constituent recovered"}

    # BEDROCK TERMINATION (head-noun -> seeded math primitive): a multi-word
    # genus the agent does not hold AND that has NO readable definition of its own
    # ('fundamental_equivalence_relation' — no page), whose HEAD NOUN is a seeded
    # math primitive ('relation'), BOTTOMS OUT there — re-point the genus to the
    # head primitive and ground onto the bedrock directly, instead of falling
    # through the head-noun fallback into the 'Relation' disambiguation page (the
    # one-hop-too-far stall). Gated on 'no readable genus definition' so a genus
    # that DOES have a page ('topological space') still recurses normally and
    # climbs through its real intermediates (topological_space -> space) — the
    # bedrock-head is a FALLBACK on data-unavailability, not a shortcut that
    # collapses legitimate hops. The genus-differentia structure says the genus IS
    # its head noun; when that head is the agent's seeded bedrock, the climb done.
    if not _is_held(substrate, genus, index=index):
        bh = _bedrock_head(substrate, genus, index=index)
        if bh and not _genus_has_own_page(genus, conversation,
                                          substrate=substrate):
            trace["bedrock_head"] = {"genus": genus, "head_primitive": bh}
            genus = bh
            combination = f"isa({term}, {genus})"
            structure["genus"] = genus
            structure["combination"] = combination

    # GROUND the genus FIRST (depth-first toward primitives): if the genus is not
    # yet a held concept and we have depth budget, RECURSE — read+ground IT, so
    # the term's cone bottoms out at a primitive rather than a bare leaf. The
    # current concept-name is pushed onto the CYCLE-DETECTION path before the
    # descent so a definitional loop (genus -> … -> this concept) is caught.
    recursed: Optional[dict[str, Any]] = None
    if not _is_held(substrate, genus, index=index):
        if depth < max_depth:
            recursed = read_and_ground(
                substrate, genus, conversation, depth=depth + 1,
                max_depth=max_depth, language=language, _index=index,
                _visiting=visiting | {cname_norm})
            trace["recursed"] = recursed["trace"]
    if recursed is not None:
        structure["genus_grounded"] = recursed["grounded"]

    # GROUND the term itself: ground_concept writes the built_from edge to the
    # genus + the combination (an admissible Concept->Concept mutation; the
    # grounding productions were opened by the caller's setup). The genus is
    # created as a Concept if it does not yet exist (a bare leaf) — but if it
    # could be grounded, the recursion above already did so.
    # GROUND with the comprehended FRAME + REGISTER (additive; both default to
    # the unchanged grounding when absent): attach the concept IN the frame's
    # Microtheory (grounding is frame-relative) AND set the grounding CONFIDENCE
    # from the register (approximate -> hedged/lower; exact/none -> full).
    # PROVENANCE — what the agent READ this from (WHERE/WHO/HOW/WHAT/WHEN), and
    # the EPISTEMIC STATUS the source lends (consensus/attested vs self-derived
    # vs conjecture), READ OFF the agent's held understanding of the source (the
    # `wikipedia` concept's reliability/conventions — graph data, not a Python
    # constant). A teacher gloss / fed definition has no external source ->
    # provenance None (a taught fact, not an attributed one). Knowledge is
    # source-relative: where it came from is part of what it means.
    prov = _read_provenance(concept_name, conversation, substrate=substrate)
    epi_status = None
    if prov:
        try:
            from domains import source_provenance as _sp
            epi_status = _sp.epistemic_status_for_source(
                substrate, prov.get("source", ""))
        except Exception:
            epi_status = None
    res = _gr.ground_concept(substrate, term, [genus], combination,
                             index=index, create_missing=True,
                             frame=frame_domain, register=register,
                             confidence=confidence,
                             register_status=register_status,
                             sense_aware=True,
                             provenance=prov, epistemic_status=epi_status)
    # SENSE-SHIFT: a different-frame reading grounded on a DISTINCT sense node
    # ('<term>__<frame>') rather than overwriting the held sense. The confirm
    # below must read THAT node, so the grounded name may differ from `term`.
    grounded_name = res.get("grounded_name") or term
    trace["ground"] = {"concept_created": res["concept"] is not None,
                       "edges_added": res["edges_added"],
                       "combination_set": res["combination_set"],
                       "frame_mt": res.get("frame_mt"),
                       "frame_recorded": res.get("frame_recorded"),
                       "frame_mt_name": res.get("frame_mt_name"),
                       "confidence": res.get("confidence"),
                       "register_status": res.get("register_status"),
                       "sense_shift": res.get("sense_shift"),
                       "sense_name": res.get("sense_name"),
                       "genus_surprise": res.get("genus_surprise"),
                       "provenance": res.get("provenance"),
                       "epistemic_status": res.get("epistemic_status")}
    structure["grounded_name"] = grounded_name
    structure["sense_shift"] = res.get("sense_shift")
    structure["sense_name"] = res.get("sense_name")
    structure["genus_surprise"] = res.get("genus_surprise")
    structure["provenance"] = res.get("provenance")
    structure["epistemic_status"] = res.get("epistemic_status")

    # CONFIRM: does the term now structurally ground (cone reaches a primitive)?
    cid = index.get(grounded_name) or _gr._find_concept(substrate, grounded_name, index)
    if cid is None:
        return {"grounded": False, "structure": structure, "trace": trace,
                "reason": "ground_concept did not create the concept node"}

    # ORDER (composition depth) — RECOGNITION: the read-and-ground tier-climb IS
    # order N -> N+1. This concept's combination composes over its (read-grounded)
    # genus one level deeper, so its ORDER = 1 + the genus's order. Computed via
    # the agent's order-N machinery (order_n_composition.compute_concept_order over
    # the built_from cone — the same iterate-to-N recursion, with the
    # function-composition rule), not a bespoke tier counter. The "acquire the next
    # tier by reading" step is order N -> N+1, made explicit on the node. Additive.
    try:
        from domains import order_n_composition as _onc
        _ord = _onc.compute_concept_order(substrate, cid)
        structure["order"] = _ord["order"]
        trace["order"] = _ord["order"]
    except Exception:
        pass
    proof = _gr.grounding_reaches_primitives(substrate, cid)
    structure["cone_size"] = proof["cone_size"]
    structure["depth"] = proof["depth"]
    # surface the comprehended-and-USED frame + confidence on the result so the
    # caller can see the concept is grounded IN the frame's Mt AT the register's
    # confidence — the adjuncts visibly drove the grounding.
    structure["frame_mt"] = res.get("frame_mt")
    structure["frame_recorded"] = res.get("frame_recorded")
    structure["confidence"] = res.get("confidence")
    # The cone must reach a GENUINE basis primitive (a seeded primitive / an
    # independently grounded leaf), NOT a bare genus leaf ground_concept just
    # minted (origin=='grounded_representation', built_from nothing). Gap 1 makes
    # a complex definition COMPREHEND + ground term built_from <genus>; but if
    # <genus> is only such a placeholder leaf, the cone has NOT bottomed out at a
    # real primitive — the honest 'recurse deeper / seed the genus' limit.
    basis_prims = [
        substrate.node(m)["attrs"].get("name")
        for m in _gr.cone(substrate, cid)
        if _gr.is_primitive(substrate, m) and _is_basis_concept(substrate, m)]
    structure["primitives"] = basis_prims
    grounded = bool(basis_prims)
    trace["step"] = "grounded" if grounded else "leaf_not_primitive"
    return {"grounded": grounded, "structure": structure,
            "trace": trace,
            "reason": ("grounded — cone reaches primitive(s) "
                       f"{basis_prims}" if grounded
                       else "grounded the genus edge but the cone does not yet "
                            "reach a seeded primitive (genus is a bare leaf — "
                            "recurse deeper / seed the genus)")}


def ground_recursively(substrate, concept_name: str, conversation, *,
                       depth: int = 0, max_depth: int = _DEFAULT_MAX_DEPTH,
                       definition_text: Optional[str] = None,
                       language: str = "en",
                       _index: Optional[dict] = None) -> dict[str, Any]:
    """DEEP RECURSIVE GROUNDING — the explicit entry the agent's derived
    principle names: climb the WHOLE definitional chain (concept -> genus ->
    genus-of-genus -> … -> seeded primitive), reading + comprehending + grounding
    each un-held ancestor depth-first, until the chain bottoms out at a primitive
    (or honestly stalls where a definition won't comprehend).

    This is the recursive application of the agent's own composition principle
    ("a COMPOSITIONAL system's WHOLE is determined by its PARTS plus a finite set
    of COMBINATION rules") — grounding-to-primitives IS that fold, applied until
    the parts are primitives.

    THE THIN INSTANCE: this entrypoint DELEGATES to the general ACQUIRE block
    (acquire.acquire_concept = acquire(...) under the concept-grounding parameter
    set) — the shared SOURCE -> COMPREHEND -> COMPOSE -> VERIFY pipeline lives ONCE
    in acquire.py. The genuinely per-kind machinery (the genus-differentia descent,
    the honest stop, the cycle-detection — read_and_ground, the recursive WORKER)
    is the VERIFY parameter acquire runs. We re-read the worker's full rich result
    (carried through the acquire VERIFY trace) so the public
    {grounded, structure, trace, reason} shape callers depend on is unchanged.

    The plain-target path stays available for a fed `definition_text` (a teacher
    gloss handed directly): acquire_concept's SOURCE reads the fed/feed/wiki form,
    so when `definition_text` is supplied we feed it through the same worker the
    block's VERIFY drives — identical to the old alias, now via acquire."""
    from domains import acquire as _acq
    if definition_text is not None:
        # a directly-fed gloss (not via the conversation feed): the block's SOURCE
        # does not see it, so drive the worker with it (the same per-kind machinery
        # acquire's VERIFY runs), preserving the fed-definition behaviour exactly.
        return read_and_ground(substrate, concept_name, conversation, depth=depth,
                               max_depth=max_depth,
                               definition_text=definition_text,
                               language=language, _index=_index, _visiting=set())
    ar = _acq.acquire_concept(substrate, concept_name, conversation,
                              index=_index, max_depth=max_depth)
    # the VERIFY step carried the worker's full {grounded, structure, trace, reason}
    # dict — return it verbatim (the general block ran the pipeline; this is the
    # instance reading its result back into the public shape).
    res = (ar.verify or {}).get("result")
    if res is not None:
        return res
    # acquire short-circuited BEFORE verify (no source / did-not-comprehend) — map
    # the block's honest boundary back to the public shape.
    return {"grounded": bool(ar.acquired),
            "structure": ar.structure, "trace": {"concept": concept_name,
                                                  "acquire_reason": ar.reason},
            "reason": ar.reason}


def relation_grounds(substrate, relation_name: str, conversation, *,
                     max_depth: int = _DEFAULT_MAX_DEPTH,
                     language: str = "en") -> bool:
    """Does the queried RELATION ground — is it a held concept, OR can the agent
    GROUND it by the deep recursive descent (its definition reaches a primitive)?

    Used by the coherence short-circuit fix: a `what is the {relation} of {owner}`
    construction match is only an instantiated KNOWN structure (coherence 1.0) if
    the queried relation actually grounds. A relation the agent neither holds NOR
    can ground (no definition / a definition that won't comprehend) does NOT
    license the short-circuit — the frame's real (low) coherence stands, and the
    agent abstains rather than confidently token-grabbing. A multi-word relation
    is normalised to the concept-name convention first."""
    if not isinstance(relation_name, str) or not relation_name.strip():
        return False
    name = _name_norm(relation_name)
    index = _gr._concept_by_name(substrate)
    if _is_held(substrate, name, index=index):
        return True
    try:
        res = ground_recursively(substrate, name, conversation,
                                 max_depth=max_depth, language=language,
                                 _index=index)
        return bool(res.get("grounded"))
    except Exception:
        return False


def learn_ungrounded_fillers(substrate, frame: dict[str, Any], conversation, *,
                             max_depth: int = _DEFAULT_MAX_DEPTH,
                             language: str = "en"
                             ) -> dict[str, Any]:
    """Try to LEARN every ungrounded content filler of a comprehended frame.

    Names the frame's content fillers (coherence_graph.content_fillers), and for
    each one that is NOT already a held Concept, runs read_and_ground. Returns
    {attempts:[{filler, grounded, reason, trace, structure}], any_grounded}.
    The caller (turn) then RE-COMPUTES coherence — if the learning closed the gap
    the agent proceeds (it LEARNED the concept live), else it abstains honestly."""
    fillers = _cohg.content_fillers(frame)
    index = _gr._concept_by_name(substrate)
    attempts: list[dict[str, Any]] = []
    any_grounded = False
    for f in fillers:
        if _is_held(substrate, f, index=index):
            continue  # already grounds out — not a gap.
        res = read_and_ground(substrate, f, conversation, depth=0,
                              max_depth=max_depth, language=language,
                              _index=index, _visiting=set())
        attempts.append({"filler": f, "grounded": res["grounded"],
                         "reason": res["reason"], "structure": res["structure"],
                         "trace": res["trace"]})
        any_grounded = any_grounded or res["grounded"]
        # the index may have grown — refresh so a later filler sees new concepts.
        index = _gr._concept_by_name(substrate)
    return {"attempts": attempts, "any_grounded": any_grounded,
            "fillers": fillers}


__all__ = ["read_and_ground", "ground_recursively", "relation_grounds",
           "learn_ungrounded_fillers"]
