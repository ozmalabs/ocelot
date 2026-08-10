"""Mechanical Wiktionary (kaikki) → graph lexicon filler for LanguageWorld.

A world-adapter ingester, the SAME shape as ``dictionary_lexicon`` (the
WordNet ingester) and ``morphology_reference`` (UniMorph): it translates
an external reference (Wiktionary, via the kaikki.org machine-readable
extracts) into substrate mutations, so a non-English content token
resolves to its English concept WITHOUT a per-language paradigm and
WITHOUT a runtime ML lemmatizer / translator.

Why Wiktionary on top of WordNet + UniMorph:
  * UniMorph's public dumps are sparse — the held-out test verbs
    (``perseguir`` / ``追いかける``) are simply absent, so the inflected
    surface never reduces to a lemma WordNet knows. Wiktionary's
    ``form_of`` data is a far broader inflected-surface → lemma table.
  * WordNet's cross-lingual index (OMW) is also sparse outside common
    nouns. Wiktionary carries direct word → English-translation data.

The COLD-REFERENCE discipline (CLAUDE.md + the substrate's own
architecture concepts: page_cache / mmap / cache_aside): the kaikki
extract is ~60–100 MB per language and almost entirely cold at query
time. We NEVER load it into a Python dict. Instead we stream-parse the
gz ONCE to BUILD three on-disk mmap'd SLABS (``reference_slab``) per
language; lookups then touch only the OS page_cache working set, so
query-time RSS is independent of corpus size. Grounded graph nodes are
the HOT tier; the slab is consulted only on a miss (cache_aside).

Slabs built per language ``<lang>`` (es / ja / ...):
  wikt_formof_<lang> : inflected_surface → lemma   (senses[].form_of[].word)
  wikt_xlate_<lang>  : word → English translations  (translations[].word
                       where the translation's lang label is English —
                       see _english_lang_labels: es labels it ``Inglés``,
                       ja labels it ``英語``; both with code=None)
  wikt_gloss_<lang>  : word → first gloss            (senses[].glosses[0])

Per CLAUDE.md this is allowed: the reference lookup is external I/O at
the Python world-adapter boundary; it only GROUNDS graph data (LexEntry
+ Concept) the existing graph-resident rules consume. NO agent decisions
over graph state — the only parameterisation (slot→POS preference when
picking among English translation candidates) is a mechanical query
preference, exactly as in the sibling modules.

Honest scope / known residuals (stated plainly, not hidden):
  * The MECHANISM is general: any surface with form_of / English-xlate
    data in the kaikki extract resolves with no per-language code.
  * A translation is a CHOICE, not ground truth: perseguir's Wiktionary
    English translations are {pursue, chase, follow, ...}. We prefer one
    WordNet knows with a POS matching the slot; which one surfaces is a
    translation choice, NOT a coverage gap — the test says so.
  * The kaikki ``ja`` extract is the JAPANESE-language Wiktionary, so its
    glosses are in Japanese (still useful as a sense key); its English
    translations are labelled ``英語``. Available — handled.
"""
from __future__ import annotations

import gzip
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Iterator, Optional

from . import reference_slab as slab

# Cache the downloaded kaikki extracts under the gitignored data/ dir.
_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _ROOT / "data" / "wiktionary"

_KAIKKI_URL = "https://kaikki.org/dictionary/downloads/{lang}/{lang}-extract.jsonl.gz"
# English is published under its own path (the by-code /downloads/en/ slot 404s);
# it is the full English Wiktionary extract, same kaikki schema (senses[].antonyms).
_KAIKKI_EN_URL = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz"


def _kaikki_url(language: str) -> str:
    return _KAIKKI_EN_URL if language == "en" else _KAIKKI_URL.format(lang=language)


# Wiktionary sense tags that mark a CONVENTIONALIZED non-literal sense — the figure grounders read these.
# 'metonymically'/'figuratively'/'broadly' feed the metaphor-vs-metonymy discriminator; 'idiomatic'
# marks a fixed multi-word phrase whose meaning isn't compositional (the idiom signal).
_FIG_TAGS = frozenset({"metonymically", "figuratively", "broadly", "idiomatic"})

# Languages we build slabs for by default. en is left to WordNet (its OMW
# index + morphy already cover English); zh is isolating (no inflection) and
# the kaikki zh extract is optional — not wired by default.
_DEFAULT_BUILD = ("es", "ja")

# The kaikki extract labels a translation's target language by NAME in the
# SOURCE language (with code=None), not by ISO code. So in the es extract
# English is ``Inglés``; in the ja extract it is ``英語``. Verified against the
# data. Map each substrate language to the label(s) its extract uses for
# English translations.
_ENGLISH_LABELS: dict[str, frozenset[str]] = {
    "es": frozenset({"Inglés", "inglés"}),
    "ja": frozenset({"英語"}),
}


def _english_lang_labels(language: str) -> frozenset[str]:
    return _ENGLISH_LABELS.get(language, frozenset({"English", "english"}))


def _cache_path(language: str) -> Path:
    return _CACHE_DIR / f"{language}.jsonl.gz"


def _ensure_download(language: str, timeout: int = 600) -> Optional[Path]:
    """Download + cache the kaikki extract gz for ``language`` once.

    Streams the body to disk (we keep the gz; never the decompressed
    corpus in RAM). Returns the cached path, or None if offline and no
    cache exists."""
    path = _cache_path(language)
    if path.exists() and path.stat().st_size > 0:
        return path
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        url = _kaikki_url(language)
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        tmp = path.with_suffix(".gz.part")
        with urllib.request.urlopen(req, timeout=timeout) as resp, \
                open(tmp, "wb") as out:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp, path)
        return path
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Build — stream the gz ONCE, yield (key, value) pairs into three slabs.
# ---------------------------------------------------------------------------


def _iter_entries(path: Path) -> Iterator[dict]:
    """Stream-decode the gz extract one JSON object per line. Never
    materialises the whole corpus."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def build_language_slabs(language: str, timeout: int = 600,
                         force: bool = False) -> bool:
    """Build the three Wiktionary slabs for ``language`` from its cached
    kaikki extract. Streams the gz ONCE, emitting pairs into three
    in-build accumulators that ``build_slab`` then sorts to disk.

    Returns True if it built (or the slabs already existed), False if the
    extract is unavailable. Skips work when the slabs are newer than the
    extract (mtime via build_slab)."""
    path = _ensure_download(language, timeout=timeout)
    if path is None:
        # Already-built slabs are still usable offline.
        return slab.slab_exists(f"wikt_xlate_{language}")

    formof_name = f"wikt_formof_{language}"
    xlate_name = f"wikt_xlate_{language}"
    gloss_name = f"wikt_gloss_{language}"
    # Part-of-speech slabs: native (this language's words) and the English
    # entries this extract incidentally carries (lang_code == "en"). The
    # source-language Wiktionary tags every entry with a POS and a lang_code,
    # so an es/ja extract gives us BOTH the native POS index AND an English
    # POS index for free — no separate (huge) en extract download. This is
    # the reference the function-word grounding reads to IDENTIFY function
    # words mechanically (article / prep / postp / conj / particle / pron /
    # aux), instead of a hand-authored stoplist.
    pos_name = f"wikt_pos_{language}"
    pos_en_name = "wikt_pos_en"
    # English antonym index (word -> [antonym, ...]), shared across extracts like
    # pos_en: the en extract is the populated source, but any extract's incidental
    # en entries contribute. Read by the figure-grounding opposition fusion as the
    # curated, per-sense witness (trust 0.8) — the coverage lever over WordNet.
    ant_en_name = "wikt_antonym_en"
    # English figurative/metonymic sense index (the metaphor-vs-metonymy discriminator). Shared like
    # the other en slabs: word -> ["tag,tag\x01gloss", ...] for senses Wiktionary tags non-literal.
    figsense_en_name = "wikt_figsense_en"

    # Fast path: if all are newer than the extract, skip the parse.
    if not force:
        src_m = path.stat().st_mtime
        names = (formof_name, xlate_name, gloss_name, pos_name, pos_en_name)
        if all(slab.slab_exists(n) for n in names):
            keys = [slab._paths(n)[0] for n in names]
            if all(k.stat().st_mtime >= src_m for k in keys):
                return True

    eng_labels = _english_lang_labels(language)

    # Stream the gz ONCE, accumulating the pair-lists. We hold short
    # (key,value) tuples transiently to feed build_slab's sort — that's the
    # one-time build cost the architecture explicitly permits; the QUERY
    # path never does. The corpus itself is never resident as a dict.
    formof_pairs: list[tuple[str, str]] = []
    xlate_pairs: list[tuple[str, str]] = []
    gloss_pairs: list[tuple[str, str]] = []
    pos_pairs: list[tuple[str, str]] = []
    pos_en_pairs: list[tuple[str, str]] = []
    ant_en_pairs: list[tuple[str, str]] = []
    figsense_en_pairs: list[tuple[str, str]] = []

    for e in _iter_entries(path):
        word = e.get("word")
        if not word:
            continue
        # POS index, keyed by the entry's lang_code so a word's POS is the
        # POS of the entry FOR THAT LANGUAGE (es "en" is a prep; the same
        # surface in other languages is filtered out by lang_code). One
        # word → several POS records (article AND noun) — build_slab groups
        # them; the grounder reads the union and tests membership.
        lc = e.get("lang_code")
        pos = e.get("pos")
        if pos:
            if lc == language:
                pos_pairs.append((word, str(pos)))
            elif lc == "en":
                pos_en_pairs.append((word, str(pos)))
        senses = e.get("senses") or []
        # form_of: inflected surface (this entry's word) → lemma(s).
        for s in senses:
            for fo in (s.get("form_of") or []):
                lemma = fo.get("word") if isinstance(fo, dict) else None
                if lemma and lemma != word:
                    formof_pairs.append((word, lemma))
        # gloss: first available gloss for the word.
        for s in senses:
            gl = s.get("glosses")
            if gl:
                gloss_pairs.append((word, str(gl[0])))
                break
        # translations: word → English translation word(s).
        for t in (e.get("translations") or []):
            if not isinstance(t, dict):
                continue
            if t.get("lang") in eng_labels:
                tw = t.get("word")
                if tw:
                    xlate_pairs.append((word, str(tw)))
        # antonyms (English only): the curated, per-sense opposition witness. kaikki
        # carries antonyms both top-level and per-sense as [{word: ...}]. Index every
        # listed antonym surface; the fusion's membership test is direction-symmetric.
        if lc == "en":
            def _ants(container):
                for an in (container.get("antonyms") or []):
                    aw = an.get("word") if isinstance(an, dict) else None
                    if aw and aw != word:
                        ant_en_pairs.append((word, str(aw)))
            _ants(e)
            for s in senses:
                _ants(s)
            # figurative/metonymic sense index (the shape discriminator): senses Wiktionary tags
            # as metonymically / figuratively / by-extension. Value = "tag,tag\x01gloss" so the
            # grounder reads BOTH the tag (metonymy vs figurative) and the gloss (to match the target).
            for s in senses:
                tags = [t for t in (s.get("tags") or []) if t in _FIG_TAGS]
                gl = s.get("glosses") or []
                if tags and gl:
                    figsense_en_pairs.append((word, ",".join(tags) + "\x01" + str(gl[0])[:160]))

    slab.build_slab(formof_name, formof_pairs, source_path=path, force=force)
    slab.build_slab(xlate_name, xlate_pairs, source_path=path, force=force)
    slab.build_slab(gloss_name, gloss_pairs, source_path=path, force=force)
    slab.build_slab(pos_name, pos_pairs, source_path=path, force=force)
    # The en POS slab is shared across extracts (es and ja both feed it).
    # Don't overwrite a populated slab with the rarer en hits from a small
    # extract: only (re)build it when missing or forced.
    # For the EN extract pos_name IS "wikt_pos_en" (already built from pos_pairs above),
    # so skip the pos_en build to avoid clobbering it with the empty incidental list.
    if pos_en_name != pos_name and (force or not slab.slab_exists(pos_en_name)):
        slab.build_slab(pos_en_name, pos_en_pairs, source_path=path,
                        force=force)
    # The en antonym slab is shared like pos_en: only (re)build it when the
    # extract actually carried en antonyms (the en extract; an es/ja extract
    # yields none), so a small extract never clobbers a populated slab.
    if ant_en_pairs and (force or not slab.slab_exists(ant_en_name)):
        slab.build_slab(ant_en_name, ant_en_pairs, source_path=path, force=force)
    if figsense_en_pairs and (force or not slab.slab_exists(figsense_en_name)):
        slab.build_slab(figsense_en_name, figsense_en_pairs, source_path=path, force=force)
    return True


# ---------------------------------------------------------------------------
# Query — slab-backed lookups (mmap, cold). No in-RAM dict.
# ---------------------------------------------------------------------------


def _xlate_slab(language: str):
    return slab.open_slab(f"wikt_xlate_{language}")


def _formof_slab(language: str):
    return slab.open_slab(f"wikt_formof_{language}")


def _gloss_slab(language: str):
    return slab.open_slab(f"wikt_gloss_{language}")


def _safe_lookup(slab_name: str, key: str) -> list:
    """Look up a key in a slab, tolerating a missing or empty (0-record) slab — the
    slab infra raises on mmap of an empty file, so guard it here."""
    try:
        sl = slab.open_slab(slab_name)
        if sl is None:
            return []
        return list(sl.lookup_list(key))
    except (ValueError, OSError):
        return []


def wiktionary_antonym(a: str, b: str) -> bool:
    """True iff English Wiktionary lists b as an antonym of a (or a of b). Reads the
    mmap'd wikt_antonym_en slab; direction-symmetric. Empty/missing slab -> False."""
    if not a or not b or a == b:
        return False
    a = a.strip().lower(); b = b.strip().lower()
    if b in {x.lower() for x in _safe_lookup("wikt_antonym_en", a)}:
        return True
    return a in {x.lower() for x in _safe_lookup("wikt_antonym_en", b)}


def wiktionary_fig_senses(word: str):
    """English Wiktionary senses tagged non-literal (metonymically / figuratively / broadly), as a list
    of (tags:set, gloss:str). The metaphor-vs-metonymy discriminator reads these: a 'metonymically'
    sense whose gloss names the figurative target is conventional metonymy. Empty on miss."""
    out = []
    for v in _safe_lookup("wikt_figsense_en", str(word).strip().lower()):
        if "\x01" in v:
            tags, gloss = v.split("\x01", 1)
            out.append((set(tags.split(",")), gloss))
    return out


def wiktionary_has_en(word: str) -> bool:
    """Is ``word`` an entry in the English Wiktionary extract? Used by the opposition
    fusion to tell a definite no (both words known, no antonym link) from an abstain
    (out of vocabulary). Presence via the en POS index (every en entry carries a POS)."""
    if not word:
        return False
    return bool(_safe_lookup("wikt_pos_en", word.strip().lower()))


def wiktionary_lemmatize(surface: str, language: str,
                         slot: Optional[str] = None) -> Optional[str]:
    """Reduce an inflected ``surface`` to its Wiktionary citation lemma via
    the form_of slab. Returns the lemma, or None when the surface has no
    form_of entry (it may already be a citation form, or simply absent)."""
    if not surface:
        return None
    sl = _formof_slab(language)
    if sl is None:
        return None
    lemma = sl.lookup(surface)
    if lemma and lemma != slab.normalize_key(surface):
        return lemma
    return None


def wiktionary_translate_to_en(word: str, language: str,
                               slot: Optional[str] = None,
                               context_words: Optional[list[str]] = None
                               ) -> Optional[str]:
    """Translate ``word`` to an English concept via the xlate slab, picking
    the candidate that best fits the SENTENCE CONTEXT.

    Wiktionary gives several English translations for a word (perseguir →
    follow / pursue / chase / harass / stalk / prosecute). Instead of "first
    WordNet-typeable", we hand the FULL candidate list to
    ``dictionary_lexicon.pick_best_concept`` — the SAME context-fit scorer used
    for word-sense selection — which scores every candidate's POS-constrained
    senses against ``context_words`` (slot-category fit + Lesk gloss overlap +
    bounded freq/rank tiebreak) and returns the globally best (concept, synset).
    So the choice among synonyms is no longer arbitrary: wrong-CATEGORY
    candidates (harass/stalk/prosecute take human/abstract patients) get
    down-ranked when the context patient is an object, and a genuinely separable
    set (banco → bank/bench) flips with the context.

    With no context (or no discriminating signal) the stable candidate-order
    tiebreak falls back to the first typeable translation — the old behaviour,
    so the common case is unchanged. Returns the chosen English concept name,
    or None when there are no candidates / none are POS-typeable (caller keeps
    its graceful fallback)."""
    if not word:
        return None
    sl = _xlate_slab(language)
    if sl is None:
        return None
    cands = sl.lookup_list(word)
    cands = [c for c in cands if c]
    if not cands:
        return None
    # Lazy import to avoid a cycle at module load (mirrors ingest_wiktionary).
    from . import dictionary_lexicon as dlex
    picked = dlex.pick_best_concept(cands, slot or "patient",
                                    context_words, "en")
    if picked is not None:
        concept, _syn = picked
        return concept
    # No candidate has a POS-typeable sense — keep the old graceful fallback
    # (first translation; the downstream WordNet typing may still miss).
    return cands[0]


def wiktionary_translation_candidates(word: str,
                                      language: str) -> list[str]:
    """The raw English translation candidate list for ``word`` (for
    provenance / inspection). Empty on a miss."""
    if not word:
        return []
    sl = _xlate_slab(language)
    if sl is None:
        return []
    return [c for c in sl.lookup_list(word) if c]


def wiktionary_gloss(word: str, language: str) -> Optional[str]:
    sl = _gloss_slab(language)
    if sl is None:
        return None
    return sl.lookup(word)


# A small CURATED English POS override — the same pattern as
# `function_word_reference._COPULA_AUX`: a closed, hand-listed table for words the
# built Wiktionary extract does not (yet) carry, so the parser tags them correctly
# regardless of which incidental es/ja extract happens to be installed (or, as in a
# fresh checkout, none at all — `wikt_pos_en` is a gitignored cold-reference slab).
# THESE are the concern-framing STEER verbs `conversation_action._CONCERN_FRAMING_VERBS`
# routes on: without them tagging as verbs, a natural-language steer ("hold both open;
# decide where they differ") POS-parses its leading word as an untyped by-position gap,
# never reaches `kind="instruction"`, and dies in the "I don't know 'Hold'" repair
# instead of the agent's self-authoring loop. HONEST FRONTIER (named, not hidden): the
# by-the-book fix is graph-TEACHABLE POS — thread the substrate the parser already
# accepts into the POS choke point so a taught lexical node is consulted before the
# slab, making vocabulary growable data (`teach`) rather than a curated constant. This
# table is the closed stopgap that unblocks the live NL front-door until then.
_POS_OVERRIDE_EN: dict[str, list[str]] = {
    "hold": ["verb"], "compare": ["verb"], "contrast": ["verb"],
    "distinguish": ["verb"], "differentiate": ["verb"], "discriminate": ["verb"],
    "separate": ["verb"], "notice": ["verb"], "attend": ["verb"],
    "weigh": ["verb"], "judge": ["verb"], "decide": ["verb"],
    "learn": ["verb"], "focus": ["verb"],
}


def wiktionary_pos(word: str, language: str) -> list[str]:
    """The set of Wiktionary parts-of-speech for ``word`` in ``language``.

    Reads the ``wikt_pos_<language>`` slab (native entries) for es/ja/zh; for
    English it reads the shared ``wikt_pos_en`` slab that the es/ja extracts
    populate incidentally (their English entries carry lang_code=="en"). Each
    surface may carry several POS tags (e.g. es "sobre" → prep/noun/verb);
    the full list is returned so the caller can test for a function-word POS
    in the set. Empty list on a miss (no extract built, or word absent).

    The curated `_POS_OVERRIDE_EN` table wins for English before the slab — see its
    own comment for why (the closed stopgap for the steer verbs)."""
    if not word:
        return []
    if language == "en" and word in _POS_OVERRIDE_EN:
        return list(_POS_OVERRIDE_EN[word])
    name = "wikt_pos_en" if language == "en" else f"wikt_pos_{language}"
    sl = slab.open_slab(name)
    if sl is None:
        return []
    return [p for p in sl.lookup_list(word) if p]


# ---------------------------------------------------------------------------
# The ingester — ground the resolved chain as graph data (cache-aside HOT).
# ---------------------------------------------------------------------------


def ingest_wiktionary(world, surface: str, language: str,
                      slot: Optional[str] = None,
                      context_words: Optional[list[str]] = None
                      ) -> Optional[str]:
    """Resolve ``surface`` via Wiktionary and ground it as graph data.

    Chain (all mechanical reference lookups, no graph decisions):
      1. form_of: surface → lemma (if inflected). Ground an
         InflectionEntry recording surface→lemma (source=wiktionary).
      2. translate the lemma (or the surface itself) → an English word.
      3. type that English word with WordNet (via the existing
         dictionary_lexicon layer) to a canonical concept + category +
         sense, grounding Concept + LexEntry on the original surface.

    Returns the concept name, or None on a miss (caller falls through to
    the next reference / context-typing — purely additive). The grounded
    nodes are the HOT tier; this slab consult only happened because the
    hot lookup missed (cache_aside)."""
    # Lazy import to avoid a cycle (dictionary_lexicon imports nothing from
    # us; this is just to reuse its WordNet typing of the English word).
    from . import dictionary_lexicon as dlex

    # 1. form_of → lemma.
    lemma = wiktionary_lemmatize(surface, language, slot)
    base = lemma or surface
    if lemma and lemma != surface:
        try:
            from . import morphology_reference as morph  # reuse the grounder
            morph.ingest_inflection(world, surface, lemma, language)
        except Exception:
            pass

    # 2. translate base → English concept, picking the candidate that best
    # fits the sentence context (same scorer as word-sense selection). Thread
    # the SAME context bag the WordNet sense selection uses.
    xlate_key = base
    english = wiktionary_translate_to_en(base, language, slot, context_words)
    if english is None and base != surface:
        xlate_key = surface
        english = wiktionary_translate_to_en(surface, language, slot,
                                             context_words)
    if english is None:
        return None
    # Record the candidate list that fed the pick (for provenance).
    xlate_cands = wiktionary_translation_candidates(xlate_key, language)

    # 3. type the English word via WordNet → canonical concept. The English
    # word is now monolingual, so dictionary_lookup resolves it in "en".
    entry = dlex.dictionary_lookup(english, slot or "patient", "en",
                                   context_words=context_words)
    if entry is None:
        return None
    concept = entry["concept"]
    source = "wiktionary+wordnet"

    # Ground Concept (enrich attrs mechanically) — mirror ingest_word.
    cid = world._get_or_create_concept(concept)
    try:
        attrs = dict(world.s.node(cid)["attrs"])
        if not attrs.get("category"):
            world.s.set_attr(cid, "category", entry["category"])
        if entry.get("definition") and not attrs.get("definition"):
            world.s.set_attr(cid, "definition", entry["definition"])
        if "source" not in attrs:
            world.s.set_attr(cid, "source", source)
        if entry.get("sense") and not attrs.get("sense"):
            world.s.set_attr(cid, "sense", entry["sense"])
            world.s.set_attr(cid, "sense_rank", entry.get("sense_rank", 0))
        # Translation-pick provenance — the candidate list and the
        # context-chosen English word, so the unified pick is inspectable
        # graph data (which translation context selected, out of which set).
        if len(xlate_cands) > 1 and not attrs.get("translation_candidates"):
            world.s.set_attr(cid, "translation_candidates",
                             ",".join(xlate_cands))
            world.s.set_attr(cid, "translation_chosen", english)
            world.s.set_attr(cid, "translation_source", "wiktionary+context")
    except Exception:
        pass
    hyp = entry.get("hypernym")
    if hyp and hyp != concept:
        try:
            hid = world._get_or_create_concept(hyp)
            world.s.add_edge(cid, "is_a", hid, None)
        except Exception:
            pass
    # LexEntry on the ORIGINAL surface → concept (the surface is what the
    # parser sees). Confirmed — a dictionary fact, not a context guess.
    world._add_lex_entry(language, surface, concept,
                         tentative=False, weight=1.0, source=source)
    return concept


def ensure_built(languages=_DEFAULT_BUILD, timeout: int = 600) -> dict[str, bool]:
    """Build the default-language slabs if needed. Returns {lang: ok}."""
    out: dict[str, bool] = {}
    for lang in languages:
        out[lang] = build_language_slabs(lang, timeout=timeout)
    return out


__all__ = [
    "build_language_slabs",
    "ensure_built",
    "wiktionary_lemmatize",
    "wiktionary_translate_to_en",
    "wiktionary_translation_candidates",
    "wiktionary_gloss",
    "wiktionary_pos",
    "ingest_wiktionary",
    "_ENGLISH_LABELS",
    "_DEFAULT_BUILD",
]
