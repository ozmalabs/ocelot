"""Mechanical UniMorph → graph morphology filler for LanguageWorld.

A world-adapter ingester, the SAME shape as ``dictionary_lexicon`` (the
WordNet ingester) and the TV-Tropes CSV ingestion: it translates an
external structured reference (UniMorph, a community-curated inflection
table) into substrate mutations, so an inflected surface form can be
reduced to its citation lemma WITHOUT a hand-authored conjugation
paradigm and WITHOUT a runtime ML lemmatizer.

This closes the verb-lemmatization gap the WordNet ingester left open:
WordNet keys on citation forms (``perseguir``, ``追いかける``), so an
inflected surface (``persiguió``, ``追いかけた``) never matches. UniMorph
is exactly a ``form → lemma`` table, so the lemma falls out of a
mechanical lookup, and THAT lemma is what WordNet then resolves.

Per CLAUDE.md this is allowed: the reference lookup is external I/O, so
it lives at the Python world-adapter boundary (a graph Rule can't fetch
a 50 MB TSV). It only GROUNDS graph data — an ``InflectionEntry`` node
recording surface→lemma — that the existing graph-resident rules /
dictionary layer then consume. There are NO agent decisions over graph
state here; the only parameterisation (slot→prefer-verb) is a mechanical
query preference, not a decision about which concept fills which slot.

Honest scope / known gaps (stated plainly, not hidden):
  * The MECHANISM is general: any inflected form present in the ingested
    UniMorph table reduces to its lemma with no per-language paradigm
    code (sentó→sentar, rompió→romper, comió→comer all resolve).
  * COVERAGE is bounded by the specific UniMorph dump. The es dump
    (~65k lemmas) lacks ``perseguir``; the ja dump is small (~107 verb
    lemmas) and lacks ``追いかける``. A missing form returns None — the
    caller falls through exactly as before, so this is purely additive.
  * Chinese (zh) is SKIPPED: Mandarin is isolating — verbs do not
    inflect — so there is no morphology table to ingest and nothing to
    lemmatize (追 is already its own citation form). See _UNIMORPH_LANG.
  * English (en) is left to WordNet's own ``morphy`` (chased→chase),
    which the dictionary layer already uses; en UniMorph is optional and
    not wired by default.
  * Even with a correct lemma, WordNet sense-1 may not be the intended
    sense (perseguir→quest_for, 追いかける→trace). That residual is SENSE
    SELECTION — a separate, already-documented gap — NOT lemmatization.
"""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Any, Optional

from . import reference_slab as slab

# Cache the downloaded TSVs under the gamma-substrate data/ dir (gitignored).
_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _ROOT / "data" / "unimorph"


# ---------------------------------------------------------------------------
# Language code map. The substrate uses ISO-639-1 (en/es/zh/ja); UniMorph
# repos are ISO-639-3 (eng/spa/jpn/...).
#
#   zh → None: Mandarin is an ISOLATING language. Verbs carry no inflection
#   (aspect is a separate particle 了/着/过, not a fused form), so there is
#   no form→lemma table to ingest — the surface IS the citation form. There
#   is no usable UniMorph Mandarin verb morphology for the same reason.
#   We map it to None and never attempt a fetch.
#
#   en → eng exists but is intentionally left out of the default fetch:
#   WordNet's morphy already lemmatizes English. Listed for completeness;
#   lemmatize() will use it only if explicitly asked.
# ---------------------------------------------------------------------------

_UNIMORPH_LANG: dict[str, Optional[str]] = {
    "en": "eng",
    "es": "spa",
    "zh": None,   # isolating — no inflectional morphology to ingest.
    "ja": "jpn",
}

# Languages we actually ingest by default (en deferred to WordNet morphy).
_DEFAULT_INGEST = {"es", "ja"}

_UNIMORPH_URL = "https://raw.githubusercontent.com/unimorph/{lang}/master/{lang}"

# COLD-REFERENCE store: the form→lemma table is held in an on-disk mmap'd
# SLAB (reference_slab), NOT an in-RAM dict — so query-time RSS is the
# working set, not the ~50 MB corpus (the substrate's own page_cache /
# cache_aside architecture). The slab value encodes the verb flag so the
# slot=="event" preference is preserved without a second structure:
#     value = "V<TAB>lemma"   (form's best mapping is a verb)
#             "N<TAB>lemma"   (form's best mapping is non-verb)
# Built once from the cached UniMorph TSV; query is a Slab.lookup.
_SLAB_SEP = "\t"
# Per-language "tried to build" memo so we don't re-stat every call.
_BUILT: dict[str, bool] = {}


def _cache_path(wn_lang: str) -> Path:
    return _CACHE_DIR / f"{wn_lang}.tsv"


def _ensure_download(wn_lang: str) -> Optional[Path]:
    """Download + cache the UniMorph TSV for ``wn_lang`` once. Returns the
    cached path, or None if offline and no cache exists. Streams the body
    to disk so we never hold the whole 50 MB in memory."""
    path = _cache_path(wn_lang)
    if path.exists() and path.stat().st_size > 0:
        return path
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        url = _UNIMORPH_URL.format(lang=wn_lang)
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        tmp = path.with_suffix(".tsv.part")
        with urllib.request.urlopen(req, timeout=60) as resp, \
                open(tmp, "wb") as out:
            # Stream in chunks — don't materialise the raw bytes wastefully.
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp, path)
        return path
    except Exception:
        # Offline / unreachable / write error — degrade gracefully.
        return None


def _slab_name(language: str) -> str:
    return f"unimorph_{language}"


def _iter_tsv_pairs(path: Path) -> Any:
    """Stream the UniMorph TSV → (form, "V|N<TAB>lemma") pairs.

    UniMorph rows are ``lemma <TAB> form <TAB> features``. We emit
    form→lemma. When a form maps to several lemmas we PREFER a verb-feature
    lemma (features contain a bare ``V`` tag) — the verb-lemmatization gap
    is what we're closing. To keep that preference in the slab (which
    groups by key) we encode the verb flag in the VALUE and rely on the
    slab keeping the first-seen value per (key,value): we therefore yield
    VERB rows first by buffering. The build de-dups, so emitting both a
    verb and non-verb mapping for one form is fine — lemmatize() picks the
    verb one when present. The slab stores ALL distinct mappings; the
    lookup applies the verb preference."""
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:                       # stream — one line at a time
            line = raw.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            lemma = parts[0].strip()
            form = parts[1].strip().lower()
            if not lemma or not form:
                continue
            feats = parts[2] if len(parts) > 2 else ""
            is_verb = "V" in feats.split(";")
            tag = "V" if is_verb else "N"
            yield form, f"{tag}{_SLAB_SEP}{lemma}"


def _ensure_slab(language: str):
    """Build (once) and open the form→lemma slab for ``language``.

    Returns an open Slab, or None when the language has no ingestable
    morphology (zh), isn't a default-ingest language, or the dump is
    unavailable offline (caller then finds no lemma + falls through)."""
    name = _slab_name(language)
    if not _BUILT.get(language):
        _BUILT[language] = True
        wn_lang = _UNIMORPH_LANG.get(language)
        if wn_lang and language in _DEFAULT_INGEST:
            path = _ensure_download(wn_lang)
            if path is not None:
                try:
                    slab.build_slab(name, _iter_tsv_pairs(path),
                                    source_path=path)
                except Exception:
                    pass
    return slab.open_slab(name)


# ---------------------------------------------------------------------------
# The lookup — surface (+ language, slot) → lemma | None.
# ---------------------------------------------------------------------------


def lemmatize(surface: str, language: str,
              slot: Optional[str] = None) -> Optional[str]:
    """Reduce an inflected ``surface`` to its UniMorph citation lemma.

    Lowercases/normalizes the surface, looks it up in the ingested
    form→lemma index. When ``slot == "event"`` we only return a lemma
    whose mapping carried a verb feature (so a noun form that collides
    with a verb surface doesn't masquerade as the event). Returns the
    lemma, or None when the form isn't in the table (the documented
    coverage gap) or the language has no morphology to ingest (zh)."""
    if not surface:
        return None
    sl = _ensure_slab(language)
    if sl is None:
        return None
    form = surface.strip().lower()
    entries = sl.lookup_list(form)   # ["V\tlemma", "N\tlemma", ...]
    if not entries:
        return None
    # Parse the tagged values; PREFER a verb mapping (the verb-lemma gap is
    # what we're closing). Mirrors the old in-RAM "verb wins" preference.
    verb_lemma: Optional[str] = None
    any_lemma: Optional[str] = None
    for ent in entries:
        if _SLAB_SEP in ent:
            tag, lemma = ent.split(_SLAB_SEP, 1)
        else:
            tag, lemma = "N", ent
        if any_lemma is None:
            any_lemma = lemma
        if tag == "V" and verb_lemma is None:
            verb_lemma = lemma
    if slot == "event":
        # Only a verb-tagged mapping is a valid event lemma.
        if verb_lemma is None:
            return None
        lemma = verb_lemma
    else:
        lemma = verb_lemma or any_lemma
    if lemma is None:
        return None
    if lemma.lower() == form:
        # Already the citation form — nothing gained, behave like a miss
        # so the caller doesn't ground a trivial self-mapping.
        return None
    return lemma


# ---------------------------------------------------------------------------
# Tense feature of a closed-class AUXILIARY form (do-support).
#
# English do-support inserts a dummy auxiliary (do/does/did) that carries the
# clause TENSE while the lexical verb stays a bare infinitive. To recover the
# stranded tense we need the auxiliary form's tense FEATURE, not its lemma.
#
# Where it comes from, honestly:
#   * The CORRECT general source is the inflection reference itself: a UniMorph
#     row for `do` is `do <TAB> did <TAB> V;PST` (did = past) and
#     `do <TAB> does <TAB> V;3;SG;PRS` (does = 3sg present). If the en UniMorph
#     dump were ingested, the tense would be read straight off that feature
#     column — exactly the same mechanism as form→lemma.
#   * But en UniMorph is intentionally NOT in the default ingest set (see
#     _DEFAULT_INGEST / _UNIMORPH_LANG above — English is deferred to WordNet's
#     morphy, and the slab stores only the V/N flag + lemma, not the full
#     feature string). So at runtime there is no en feature table to query.
#   * Therefore the tense of the THREE do-support auxiliaries is stated here as
#     a minimal closed-class reference FACT — the same kind of small, closed,
#     enumerated reference the copula/auxiliary surface set in
#     function_word_reference._COPULA_AUX already is. `did` is the past form of
#     the verb `do`; `do`/`does` are present forms. This is a reference fact
#     about three words, not a parser heuristic over the lexical verb.
# ---------------------------------------------------------------------------

# Closed do-support auxiliary set → clause tense (reference fact: did = past
# of 'do'; do/does = present). Mirrors a UniMorph V;PST vs V;PRS feature read.
_AUX_TENSE = {
    "en": {"did": "past", "do": "present", "does": "present"},
}


def auxiliary_tense(surface: str, language: str) -> Optional[str]:
    """Return the clause TENSE carried by a do-support auxiliary surface
    (``did`` -> ``past``; ``do``/``does`` -> ``present``), or None when the
    surface is not one of the closed do-support auxiliaries.

    Reference-derived: in UniMorph this is the V;PST / V;PRS feature on the
    `do` paradigm. en UniMorph is not ingested at runtime (see module docstring
    + _DEFAULT_INGEST), so the tense of the three do-support auxiliaries is
    carried as the minimal closed-class reference table _AUX_TENSE — a fact
    about three words, not a heuristic over the lexical verb."""
    if not surface:
        return None
    return _AUX_TENSE.get(language, {}).get(surface.strip().lower())


# ---------------------------------------------------------------------------
# The ingester — ground the resolved surface→lemma mapping as graph data.
# ---------------------------------------------------------------------------


def ingest_inflection(world, surface: str, lemma: str,
                      language: str) -> str:
    """Ground a resolved inflection into ``world``'s graph as an
    ``InflectionEntry`` node and return the lemma.

    The node records {language, surface, lemma, source="unimorph"} so the
    mapping is cumulative + inspectable (the same way ``ingest_word``
    grounds a LexEntry). It's wired to the language's Lexicon via
    ``has_inflection`` so it sits alongside the lexical entries. Pure
    translation: no conditionals over graph STATE, only over the
    (already-resolved) reference result."""
    try:
        # Idempotent: skip if we already grounded this surface→lemma.
        for nid in world.s.nodes("InflectionEntry"):
            a = world.s.node(nid)["attrs"]
            if (a.get("language") == language and a.get("surface") == surface
                    and a.get("lemma") == lemma):
                return lemma
    except Exception:
        pass
    try:
        ent = world.s.add_node("InflectionEntry", {
            "language": language,
            "surface": surface,
            "lemma": lemma,
            "source": "unimorph",
        })
    except Exception:
        return lemma
    # Wire to the Lexicon so it's discoverable alongside lexical entries.
    try:
        lex_nid = world._get_or_create_lexicon(language)
        world.s.add_edge(lex_nid, "has_inflection", ent, None)
    except Exception:
        pass
    return lemma


__all__ = [
    "lemmatize",
    "auxiliary_tense",
    "ingest_inflection",
    "_UNIMORPH_LANG",
]
