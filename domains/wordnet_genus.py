"""WordNet as the LEXICAL-GENUS reference reader — the genus-deepening source.

A world-adapter reference reader, the SAME shape as ``stacks_local`` /
``nlab_local`` (``_read_X_definition(name) -> Optional[copula lead]``):
it translates an external lexical reference (WordNet, via NLTK) into the
ONE copula sentence the agent's construction grammar reads as ``TERM is-a
GENUS``. NO meaning decision: WordNet NAMES the genus (the immediate
hypernym, the lexicographer's genus term); the agent COMPREHENDS it and
its OWN grounding recursion chains genus -> hypernym -> ... down to a held
seeded prime.

WHY this exists (the agent's own diagnosis): on abstract common nouns
(``number`` / ``state`` / ``condition`` / ``score`` / ``median`` /
``action``) the agent comprehends a genus (``mathematical object`` /
``condition``) but its OWN grounding reason is *"grounded the genus edge
but the cone does not yet reach a seeded primitive (genus is a bare leaf
— recurse deeper / seed the genus)"*. Wikipedia's lead for these terms is
a disambiguation page (``X may refer to:``) — no copula genus, so the
recursion cannot deepen. WordNet's hypernym ladder IS the genus chain the
agent asked to recurse down, and it bottoms out at the agent's held primes
(``number`` is-a ``magnitude`` is-a ``property``; ``action`` is-a ``act``
is-a ``event``; ``score`` / ``median`` / ``model`` is-a ... ``cognition``).

The COLD-REFERENCE discipline (CLAUDE.md): WordNet is the cheapest reader
in the stack (in-memory synset walk, µs) and is consulted only on a term
the higher-precision corpora + Wikipedia did not resolve — a cache_aside
miss path. It GROUNDS graph data the existing graph-resident grounding
productions consume; it makes NO decision over graph state.

Honest scope:
  * The genus is WordNet sense-1's immediate hypernym (the dominant
    lexical sense). A polysemous term takes its most-frequent sense — a
    lexical CHOICE, the same one the dictionary teacher already makes, not
    a coverage gap.
  * Proper nouns / paper-specific compounds (``mike knoop`` / ``kaggle
    abstraction``) have no synset -> None (the caller's honest residual).
  * ADJECTIVES (``random``) have an adjective synset but NO noun synset, so
    the noun-genus ladder has nothing to climb. The adjective-sense path
    bridges through WordNet's own attribute / derivationally-related-noun
    cross-reference to the nominalization (``random`` -> ``randomness``) and
    reads THAT noun's genus (``randomness`` is-a ``physical property`` is-a
    ... ``attribute``). WordNet NAMES the nominalization; no meaning decision.
  * The reader supplies ONE hop (term is-a immediate-genus); the agent's
    OWN read_and_ground recursion supplies the rest of the ladder by
    re-reading each genus through this same reader until a held prime.
"""
from __future__ import annotations

from typing import Optional


def present() -> bool:
    """True iff the WordNet corpus is reachable (lazy import succeeds)."""
    try:
        from .dict_teacher import _wordnet
        _wordnet()
        return True
    except Exception:
        return False


def _noun_genus_of(syn, surface: str) -> Optional[str]:
    """The immediate hypernym lemma of a NOUN/VERB synset (the lexicographer's
    genus term), lowercased with '_' -> ' '. None for a WordNet root or a
    self-hypernym. A pure lexical read."""
    hypers = syn.hypernyms() or syn.instance_hypernyms()
    if not hypers:
        return None
    genus = hypers[0].lemmas()[0].name().replace("_", " ").lower()
    if genus == surface:
        return None
    return genus


def _adjective_nominalization(wn, surface: str) -> Optional[str]:
    """The ADJECTIVE-SENSE PATH (the agent's named need for an adjective whose
    only synset is adjectival, so the noun-genus ladder has nothing to climb):
    WordNet's own lemma cross-references take the adjective to its NOUN
    nominalization (the quality/attribute it names) — 'random' -> 'randomness',
    'continuous' -> 'continuity'. The noun ladder then reads THAT noun's genus
    ('randomness' is-a 'physical property' is-a ... 'attribute' is-a
    'abstraction' is-a 'entity'). Two WordNet-named bridges, in precedence:
      1. attributes() — the noun whose VALUE this adjective is (e.g. 'wide' is
         a value of the attribute 'width');
      2. derivationally_related_forms() restricted to NOUN lemmas — the
         morphological nominalization the lexicon records.
    Returns the bridged noun's immediate GENUS, or None. A pure lexical read —
    WordNet NAMES the nominalization and its genus; no meaning decision."""
    adj_syns = wn.synsets(surface, pos="a") + wn.synsets(surface, pos="s")
    if not adj_syns:
        return None
    syn = adj_syns[0]  # dominant adjective sense.
    # (1) the attribute noun this adjective is a value of.
    for attr in syn.attributes():
        attr_surface = attr.lemmas()[0].name().replace("_", " ").lower()
        g = _immediate_genus(attr_surface)
        if g:
            return g
    # (2) the morphological nominalization (a derivationally related NOUN lemma).
    # Read the bridged NOUN by its SURFACE sense-1 — the same dominant-sense
    # ('dictionary teacher') choice the noun ladder uses everywhere else — rather
    # than the specific cross-referenced sense (which may be a minor reading), so
    # 'randomness' reads its dominant sense-1 ('a physical property') not a
    # peripheral 'deviant behavior' sense.
    for lem in syn.lemmas():
        for rel in lem.derivationally_related_forms():
            if rel.synset().pos() != "n":
                continue
            noun_surface = rel.name().replace("_", " ").lower()
            g = _immediate_genus(noun_surface)
            if g:
                return g
    return None


def _bridge_to_noun(wn, surface: str):
    """Find the NOUN whose hypernym ladder grounds `surface`, when `surface` has
    no noun sense of its own — so a verb / adjective / adverb / inflected form
    still climbs to `entity`. Returns (noun_surface, noun_synset) or None. Pure
    WordNet-named lexical reads, in precedence:

      1. LEMMATISE an inflected NOUN ('enzymes' -> 'enzyme') via morphy;
      2. an ADJECTIVE -> its nominalisation noun ('accurate' -> 'accuracy');
      3. an ADVERB -> its pertainym ADJECTIVE -> that adjective's nominalisation
         noun ('accurately' -> 'accurate' -> 'accuracy');
      4. a VERB (or its morphy lemma: 'accepts' -> 'accept') -> a derivationally
         related NOUN ('accept' -> 'acceptance', 'achieve' -> 'achievement').

    The bridged noun then carries the whole ladder to the bedrock. WordNet names
    every hop (morphy / attributes / pertainyms / derivationally_related_forms);
    no meaning decision."""
    # 1. inflected noun -> its lemma
    nl = wn.morphy(surface, "n")
    if nl and wn.synsets(nl, "n"):
        return nl, wn.synsets(nl, "n")[0]
    # 2. adjective -> nominalisation noun (the word itself or its adj lemma)
    for adj in (surface, wn.morphy(surface, "a")):
        if adj and (wn.synsets(adj, "a") or wn.synsets(adj, "s")):
            bn = _adjective_bridge_noun(wn, adj)
            if bn and wn.synsets(bn, "n"):
                return bn, wn.synsets(bn, "n")[0]
            break
    # 3. adverb -> pertainym adjective -> its nominalisation noun
    advs = wn.synsets(surface, "r")
    if advs:
        for lem in advs[0].lemmas():
            for per in lem.pertainyms():
                adj = per.name().replace("_", " ").lower()
                bn = _adjective_bridge_noun(wn, adj)
                if bn and wn.synsets(bn, "n"):
                    return bn, wn.synsets(bn, "n")[0]
    # 3b. -ly adverb MORPHOLOGY (even when not in WordNet as an adverb): strip
    #     '-ly' to the adjective ('adversarially' -> 'adversarial'; 'happily' ->
    #     'happy') and bridge THAT adjective to its noun.
    if surface.endswith("ly") and len(surface) > 4:
        stems = [surface[:-2]]
        if surface.endswith("ily"):
            stems.append(surface[:-3] + "y")
        for adj in stems:
            bn = _adjective_bridge_noun(wn, adj)
            if bn and wn.synsets(bn, "n"):
                return bn, wn.synsets(bn, "n")[0]
    # 4. verb (or its lemma) -> derivationally related noun
    for vb in (surface, wn.morphy(surface, "v")):
        if not vb:
            continue
        vs = wn.synsets(vb, "v")
        if not vs:
            continue
        for lem in vs[0].lemmas():
            for rel in lem.derivationally_related_forms():
                if rel.synset().pos() != "n":
                    continue
                nm = rel.name().replace("_", " ").lower()
                if wn.synsets(nm, "n"):
                    return nm, wn.synsets(nm, "n")[0]
        break
    # 5. MORPHOLOGICAL de-suffixing — even when the adjective is NOT in WordNet
    #    at all ('adversarial' -> 'adversary'): strip an adjective suffix to a
    #    held noun. Accepted only when the stem IS a noun, so it never misfires.
    stem = _adj_noun_stem(wn, surface)
    if stem and wn.synsets(stem, "n"):
        return stem, wn.synsets(stem, "n")[0]
    return None


def _adjective_bridge_noun(wn, surface: str) -> Optional[str]:
    """The NOUN an adjective NAMES — its nominalization, so the hypernym ladder
    has something to climb. Same WordNet-named bridges as _adjective_nominalization
    (attribute the adjective is a value of, then a derivationally-related noun),
    but returns the NOUN SURFACE (a word that HAS a noun synset) rather than its
    genus — so hypernym_chain can start the pointer-walk from it and climb the
    whole ladder ('abnormal' -> 'abnormality' -> 'normality' -> 'quality' ->
    'attribute' -> 'abstraction' -> 'entity'). A pure lexical read."""
    adj_syns = wn.synsets(surface, pos="a") + wn.synsets(surface, pos="s")
    if not adj_syns:
        return _adj_noun_stem(wn, surface)   # no adj synset: try a morphological stem
    syn = adj_syns[0]  # dominant adjective sense.
    # (1) the attribute noun this adjective is a value of.
    for attr in syn.attributes():
        nm = attr.lemmas()[0].name().replace("_", " ").lower()
        if wn.synsets(nm, pos="n"):
            return nm
    # (2) a directly derivationally-related NOUN, or a pertainym NOUN
    #     ('administrative' -> 'administration').
    for lem in syn.lemmas():
        for rel in list(lem.derivationally_related_forms()) + list(lem.pertainyms()):
            if rel.synset().pos() == "n":
                nm = rel.name().replace("_", " ").lower()
                if wn.synsets(nm, pos="n"):
                    return nm
    # (3) adjective -> its derivational VERB -> that verb's nominalisation noun
    #     ('adaptive' -> 'adapt' -> 'adaptation').
    for lem in syn.lemmas():
        for rel in lem.derivationally_related_forms():
            if rel.synset().pos() != "v":
                continue
            vsyns = wn.synsets(rel.name(), pos="v")
            for vl in (vsyns[0].lemmas() if vsyns else []):
                for vr in vl.derivationally_related_forms():
                    if vr.synset().pos() == "n":
                        nm = vr.name().replace("_", " ").lower()
                        if wn.synsets(nm, pos="n"):
                            return nm
    # (4) MORPHOLOGICAL de-suffixing to a held noun ('additional' -> 'addition',
    #     'adversarial' -> 'adversary') — only accepted when the stem IS a noun.
    return _adj_noun_stem(wn, surface)


# adjective -> noun suffix transforms, longest/most-specific first; each candidate
# is accepted ONLY if it resolves to a real WordNet noun, so a wrong transform
# never fires. English adjective-forming morphology read backwards.
_ADJ_SUFFIX = [
    ("ational", "ation"), ("ative", "ation"), ("ative", "ate"),
    ("ical", "ic"), ("ical", "y"), ("ial", "y"), ("ial", "e"), ("ial", ""),
    ("ous", ""), ("ous", "y"), ("ary", ""), ("ary", "er"), ("ful", ""),
    ("ive", "ion"), ("ive", "e"), ("ic", "y"), ("ic", ""),
    ("al", ""), ("al", "e"), ("ed", ""), ("ic", "ics"),
]


def _adj_noun_stem(wn, surface: str) -> Optional[str]:
    """De-suffix an adjective to a NOUN stem ('additional' -> 'addition'). Tries
    English adjective->noun suffix transforms longest-first; returns the first
    candidate that is a held WordNet noun (so a wrong strip never fires)."""
    s = (surface or "").lower()
    for suf, rep in _ADJ_SUFFIX:
        if s.endswith(suf) and len(s) - len(suf) >= 3:
            cand = s[:-len(suf)] + rep
            if wn.synsets(cand, pos="n"):
                return cand
    return None


def _immediate_genus(name: str) -> Optional[str]:
    """The lexical GENUS of `name`: WordNet sense-1's immediate hypernym
    lemma (the lexicographer's genus term), lowercased with '_' -> ' '.
    None when `name` has no noun/verb synset or no hypernym (a WordNet
    root). A pure lexical read — WordNet names the genus.

    ADJECTIVE-SENSE PATH: when `name`'s only synset is an ADJECTIVE (no noun
    hypernym to climb — WordNet adjectives have no hypernymy), bridge through
    WordNet's own attribute/nominalization cross-reference to the NOUN it names
    ('random' -> 'randomness') and read that noun's genus instead."""
    try:
        from .dict_teacher import _wordnet
        wn = _wordnet()
    except Exception:
        return None
    surface = (name or "").replace("_", " ").strip().lower()
    if not surface:
        return None
    syns = wn.synsets(surface)
    if not syns:
        # multi-word phrase: try the head noun (last token).
        toks = surface.split()
        if len(toks) > 1:
            syns = wn.synsets(toks[-1])
        if not syns:
            return None
    syn = syns[0]  # dominant (sense-1) reading — the dictionary teacher's choice.
    genus = _noun_genus_of(syn, surface)
    if genus:
        return genus
    # The dominant sense had no hypernym to climb. If that is because the term is
    # ADJECTIVAL (no noun synset at all), take the adjective-sense path: bridge to
    # the noun nominalization WordNet names and read its genus.
    if not wn.synsets(surface, pos="n"):
        return _adjective_nominalization(wn, surface)
    return None


def read_definition(concept_name: str) -> Optional[str]:
    """READ a concept's lexical GENUS from WordNet as a copula lead the
    construction grammar parses: ``a TERM is a GENUS.`` (term is-a genus).
    Returns the lead, or None when WordNet holds no synset / no hypernym
    for the name (the honest miss -> the caller falls through). Mechanical
    world-adapter I/O — WordNet names the genus, no meaning decision."""
    genus = _immediate_genus(concept_name)
    if not genus:
        return None
    term = (concept_name or "").replace("_", " ").strip().lower()
    article = "an" if genus[:1] in "aeiou" else "a"
    return f"a {term} is {article} {genus}."


def _lead(term: str, genus: str) -> str:
    """The copula lead the construction grammar parses: 'a TERM is a GENUS.'"""
    article = "an" if genus[:1] in "aeiou" else "a"
    return f"a {term} is {article} {genus}."


def hypernym_chain(concept_name: str, *, max_links: int = 40) -> list[str]:
    """The SENSE-CONSISTENT lexical-genus ladder for `concept_name`: walk
    WordNet's hypernym POINTERS from the dominant (noun-preferred) synset, link
    by link, to the root — instead of re-looking-up each genus WORD (which hops
    senses: 'act' -> 'legal_document'). Returns the lemma chain
    [term, genus1, genus2, …, 'entity'] in WordNet LEMMA form (underscores
    PRESERVED, lowercased), or [] when WordNet holds no synset for the term.

    Underscores preserved on purpose: a multi-word WordNet lemma
    ('body_of_water', 'commercial_enterprise') is a SINGLE lexical unit — the
    dictionary already knows it is one concept. Keeping the underscore keeps it
    one TOKEN, so the genus-differentia grammar reads it whole instead of
    splitting it on 'of' (a differentia marker) into the head 'body' + a
    differentia 'of water' — which would drop off the chain and wander. The
    lexical compound IS the genus; we don't re-split what WordNet lexicalised.

    Carrying the synset is what makes it sense-consistent: every noun chain
    provably terminates at the unique-beginner 'entity', so the descent bottoms
    out at the seeded lexical_ontology_roots bedrock. A pure lexical read —
    WordNet names the pointers; no meaning decision."""
    try:
        from .dict_teacher import _wordnet
        wn = _wordnet()
    except Exception:
        return []
    surface = (concept_name or "").replace("_", " ").strip().lower()
    if not surface:
        return []
    lemma = surface.replace(" ", "_")            # the lexical-unit (token) form
    # CHOOSE the START synset (a NOUN, so the hypernym ladder climbs to entity),
    # building the chain PREFIX up to it:
    #   1. the word's own noun sense;
    #   2. an ADJECTIVE bridged to its nominalization NOUN ('abnormal' ->
    #      'abnormality' -> … -> entity) — the noun goes on the chain as the
    #      adjective's genus, so read_and_ground grounds the adjective through it;
    #   3. a multi-word phrase's head noun;
    #   4. last resort: any synset (an adjective with no bridge has no hypernyms,
    #      so the chain stays short and the word stays frontier — the honest miss).
    prefix = [lemma]
    noun_syns = wn.synsets(surface, pos="n")
    if noun_syns:
        cur = noun_syns[0]
    else:
        bridged = _bridge_to_noun(wn, surface)
        if bridged:
            noun_surface, cur = bridged
            prefix.append(noun_surface.replace(" ", "_"))
        else:
            toks = surface.split()
            head = wn.synsets(toks[-1], pos="n") if len(toks) > 1 else []
            anyz = wn.synsets(surface)
            if head:
                cur = head[0]
            elif anyz:
                cur = anyz[0]
            else:
                return []
    chain = list(prefix)
    seen = set(prefix)
    for _ in range(max_links):
        hypers = cur.hypernyms() or cur.instance_hypernyms()
        if not hypers:
            break
        cur = hypers[0]
        name = cur.lemmas()[0].name().lower()   # WordNet lemma: underscores kept
        if name in seen:   # WordNet hypernymy is a DAG; never loop
            break
        chain.append(name)
        seen.add(name)
    return chain


def chain_definition_feed(concept_name: str) -> dict[str, str]:
    """Build a DEFINITION FEED staging the whole sense-consistent hypernym
    ladder for `concept_name` (hypernym_chain): {Xi: 'a Xi is a Xi+1.'} for each
    consecutive link. Handed to read_and_ground as a `conversation`'s
    `_definition_feed`, it makes the grounding recursion follow ONE consistent
    chain down to the seeded root — not re-disambiguate each word. The seed's
    own bedrock (lexical_ontology_roots) is where the chain bottoms out.

    Mechanical world-adapter staging: WordNet decides the ladder; this just
    lays it out as the prose the agent reads."""
    chain = hypernym_chain(concept_name)
    feed: dict[str, str] = {}
    for a, b in zip(chain, chain[1:]):
        # The lead keeps the LEXICAL-UNIT (underscore) form of both term and
        # genus so the genus tokenizer reads a multi-word lemma whole
        # ('body_of_water'), not split on 'of'.
        lead = _lead(a, b)
        # Key BOTH surface forms: depending on the path, the descent may re-read
        # a genus by its underscore lexical form OR its spaced form — key both so
        # the recursion never misses the feed and falls through to the broad
        # reader (which hops senses).
        feed.setdefault(a, lead)
        feed.setdefault(a.replace("_", " "), lead)
    return feed


class ChainReader:
    """A dictionary world-adapter reader for read_and_ground: stages the
    sense-consistent WordNet hypernym ladder for one concept as its
    `_definition_feed`. The agent reads + grounds; the reader only walks
    WordNet's pointers. No meaning decision, no agent state."""

    def __init__(self, concept_name: str):
        self._definition_feed = chain_definition_feed(concept_name)


class _HybridFeed(dict):
    """The top concept's sense-consistent WordNet chain PLUS, for ANY other word
    the descent asks about, that word's OWN sense-consistent chain (staged
    lazily). So a WordNet-MISS word grounds through its Wikipedia lead
    (read_and_ground's fallback) AND the SUB-GENERA in that lead ('admin' ->
    'administration' -> …) chain to the bedrock.

    DETERMINISM: a sub-genus is read via its full hypernym-POINTER chain
    (chain_definition_feed), NOT a single-hop synset[0] RE-LOOKUP — the latter
    re-disambiguates each word and WANDERS ('organism' -> 'situation' ->
    'administrative_district' -> …), a long detour whose reaching of `entity`
    within the depth bound depended on hash-seed-dependent traversal order (the
    'flaky across processes' grounding). Staging the pointer chain makes every
    descent deterministic. A word WordNet doesn't know returns None -> the descent
    falls through to Wikipedia for it too."""

    def __init__(self, concept_name: str):
        super().__init__(chain_definition_feed(concept_name))

    def get(self, key, default=None):
        if dict.__contains__(self, key):
            return dict.get(self, key)
        chain = chain_definition_feed(key)   # key's SENSE-CONSISTENT pointer chain
        if chain:
            self.update(chain)               # stage it -> sub-genera stay consistent
            return dict.get(self, key, default)
        return default

    def __contains__(self, key):
        return dict.__contains__(self, key) or bool(chain_definition_feed(key))


class HybridChainReader:
    """ChainReader + a lazy WordNet feed for sub-genera — the reader for grounding
    over a MIXED vocabulary (WordNet hits, WordNet misses that ground via
    Wikipedia, and the WordNet sub-genera those leads name). The campaign reader."""

    def __init__(self, concept_name: str):
        self._definition_feed = _HybridFeed(concept_name)
