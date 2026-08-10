"""reference_route — a WIKIPEDIA reference RESOLVER for the epistemic_access
REFERENCE route, plus the chained ``reference_lookup`` the conversation world
hands to the resolver.

Where this sits. ``epistemic_access`` decides (graph-resident) that a gap is
RESOLVABLE_VIA_ROUTE via a *reference* route and holds knowing_where_vs_what:
it has the ROUTE (an external store + a lookup key), not the ANSWER. This module
is the mechanical I/O at the boundary that the taught 'reference' route NAMES: it
FETCHES from the store (Wikipedia, via the existing ``web_world`` adapter) and
mechanically EXTRACTS a short candidate answer. No LLM, no Rust — a fetch + a
first-sentence / salient-value extraction.

The unit of resolution is ``wikipedia_answer(surface, question_text=None)``:

  * wikipedia_search(surface) -> the best matching page TITLE;
  * wikipedia_summary(title)  -> the lead extract (cached);
  * EXTRACT a short answer: the summary's LEAD SENTENCE, or — when the question
    text gives a definitional cue ("what is the capital of X") — a salient VALUE
    pulled mechanically from the lead (a capital, a proper-noun value). String
    in; short answer string out; None when the web is unreachable or the page
    has no usable extract.

The chained ``reference_lookup(store, key)`` is what the conversation world hands
to ``epistemic_access.resolve_banked_gaps`` and to the in-turn auto-resolver: it
tries ConceptNet FIRST (the cheap, local, offline commonsense store), then falls
through to this Wikipedia resolver. ConceptNet returns None for a non-ConceptNet
store; this module returns None for a non-Wikipedia store — so the chain is
purely additive and each link is graceful.

HONEST scope (stated plainly, not hidden):
  * This converts the LOOKUPABLE / DEFINITIONAL subset — "what is the capital of
    France", "what is the Euler characteristic of a sphere" — when Wikipedia's
    lead extract carries the answer. It is a mechanical first-sentence /
    salient-value pull, NOT deep reading.
  * It does NOT convert research-math HLE answers: those are not summary-
    extractable (the answer is a number/structure a research paper derives, not
    a value in an encyclopedia lead). Those stay unresolved. Measured, not hidden.
  * Web unreachable -> None everywhere; the caller falls back to the existing
    bank/ask behaviour unchanged.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from domains import web_world as ww

# The store LABEL this resolver answers for (the route-finder tags a Wikipedia
# reference route with a label containing 'wikipedia' / 'web').
_WIKI_STORE_HINTS = ("wikipedia", "web")

# A definitional cue word in the question -> we try to pull the SALIENT VALUE
# (a proper-noun answer) from the lead, not just echo the lead sentence. Coarse,
# mechanical: these are the 'what is the <X> of <Y>' question kinds whose answer
# is a named value sitting in the encyclopedia lead.
_VALUE_CUES = ("capital", "currency", "population", "author", "director",
               "inventor", "discoverer", "president", "language", "continent")


# ---------------------------------------------------------------------------
# Mechanical extraction — first sentence / salient value. No LLM.
# ---------------------------------------------------------------------------

def _lead_sentence(extract: str) -> str:
    """The lead SENTENCE of a Wikipedia extract — a mechanical split on the
    first sentence terminator that is not an abbreviation. Coarse: split on
    '. ' / '? ' / '! ' and take the first chunk, restoring the terminator."""
    text = (extract or "").strip()
    if not text:
        return ""
    m = re.search(r"[.!?](?:\s|$)", text)
    if m:
        return text[: m.end()].strip()
    return text


_PROPER = r"[A-Z][\w'-]+(?:\s+[A-Z][\w'-]+){0,2}"


def _salient_value(extract: str, cue: str) -> Optional[str]:
    """Pull a salient NAMED VALUE for a 'what is the <cue> of X' question
    (capital / currency / author / ...) from the WHOLE extract. Mechanical
    pattern: for each cue occurrence, skip an immediately-following 'of <Entity>'
    (the relation's OWNER, not the value) and any linking verb ('is'/'has
    been'/'was'/'are'), then take the nearest following Capitalised proper-noun
    run as the VALUE. Returns the value string or None (the caller then falls
    back to the lead sentence). Searches the full extract because the value
    often sits in the SECOND sentence ('...capitals of France. The capital of
    France has been Paris...')."""
    text = (extract or "")
    if not text or not cue:
        return None
    low = text.lower()
    start = 0
    while True:
        idx = low.find(cue, start)
        if idx < 0:
            return None
        start = idx + len(cue)
        tail = text[idx + len(cue):idx + len(cue) + 200]
        # skip 'of <Entity>' (the owner) + a linking verb, then take the value.
        m = re.match(
            rf"\s+of\s+{_PROPER}\s+(?:has\s+been|have\s+been|is|are|was|were)\s+"
            rf"({_PROPER})",
            tail)
        if m:
            return m.group(1).strip()


def _extract_answer(extract: str, question_text: Optional[str]
                    ) -> Optional[tuple[str, str]]:
    """Mechanically extract a short answer from a Wikipedia lead extract, tagged
    with its KIND.

    Returns ``(answer, kind)`` or None (empty extract). ``kind`` is:
      · "value"      — the question carried a value-cue ('what is the CAPITAL of
                       France') and a salient named VALUE was pulled from the
                       lead: this answer FILLS the queried property/slot.
      · "definition" — no value-cue matched, so the lead SENTENCE is returned as
                       the definitional answer for 'what is an X'. This is the
                       ENTITY's definition; it does NOT fill a queried property.

    The kind is the graph-native distinction Gap 2 reads: an answer that fills
    the queried slot (a value) coheres with what was asked; the entity's
    definitional lead does not."""
    if not extract:
        return None
    q = (question_text or "").lower()
    for cue in _VALUE_CUES:
        if cue in q:
            val = _salient_value(extract, cue)
            if val:
                return (val, "value")
            break
    lead = _lead_sentence(extract)
    return (lead, "definition") if lead else None


# ---------------------------------------------------------------------------
# wikipedia_answer — the resolver unit. surface (+ question) -> short answer.
# ---------------------------------------------------------------------------

def wikipedia_answer(surface: str,
                     question_text: Optional[str] = None
                     ) -> Optional[dict[str, Any]]:
    """Resolve a queried surface to a short ANSWER from Wikipedia, or None.

    surface  — the concept/entity to look up (e.g. 'France', 'sphere').
    question_text — the full question (optional), used only to pick a salient
                    value over the lead sentence for a 'what is the <cue> of X'.

    Returns ``{answer, title, extract, url, source}`` on a hit, or None when the
    web is unreachable / no page matches / the extract is empty. Mechanical
    fetch (web_world) + mechanical extract; no LLM. Graceful on every failure."""
    if not surface:
        return None
    cue = _question_value_cue(question_text)
    summ: Optional[dict[str, Any]] = None
    # VALUE question ('what is the CAPITAL of France') — search the RELATION
    # PHRASE (the cleaned question) first: it lands on the page that holds the
    # value ('capital of France' -> 'List of capitals of France', whose lead
    # carries 'Paris'), not just the entity's own page.
    if cue:
        phrase = _relation_phrase(question_text)
        if phrase:
            titles = ww.wikipedia_search(phrase, limit=3)
            if titles:
                summ = ww.wikipedia_summary(titles[0])
    # The surface may BE a title; else search for the best matching page.
    if summ is None:
        summ = ww.wikipedia_summary(surface)
    if summ is None:
        titles = ww.wikipedia_search(surface, limit=3)
        if titles:
            summ = ww.wikipedia_summary(titles[0])
    if summ is None:
        return None
    extract = summ.get("extract") or ""
    got = _extract_answer(extract, question_text)
    if not got:
        return None
    answer, kind = got
    return {"answer": answer, "kind": kind, "title": summ.get("title", ""),
            "extract": extract, "url": summ.get("url", ""),
            "source": "wikipedia"}


def _question_value_cue(question_text: Optional[str]) -> Optional[str]:
    """The value cue word present in the question ('capital'/'currency'/...), or
    None. Mechanical substring scan over the cue list."""
    q = (question_text or "").lower()
    for cue in _VALUE_CUES:
        if cue in q:
            return cue
    return None


def _relation_phrase(question_text: Optional[str]) -> Optional[str]:
    """Clean a question into a search phrase for the relation page: strip the
    leading 'what is the' / 'what is a' / 'what are the' wh-frame and the
    trailing '?'. 'What is the capital of France?' -> 'capital of France'."""
    q = (question_text or "").strip().rstrip("?").strip()
    if not q:
        return None
    low = q.lower()
    for pre in ("what is the ", "what is a ", "what is an ", "what are the ",
                "what was the ", "what is "):
        if low.startswith(pre):
            return q[len(pre):].strip() or None
    return q


# ---------------------------------------------------------------------------
# reference_lookup(store, key) — the resolver callable for resolve_banked_gaps
# and the in-turn auto-resolver. Handles ONLY the Wikipedia store; None else.
# ---------------------------------------------------------------------------

def reference_lookup(store: str, key: str,
                     question_text: Optional[str] = None) -> Optional[str]:
    """The Wikipedia link of the chained ``reference_lookup``: resolve a banked
    Wikipedia reference gap (``store`` names a wikipedia/web store, ``key`` is
    the surface to look up). Returns the short answer string, or None for a
    non-Wikipedia store / a miss (so the chain falls through gracefully)."""
    if not key:
        return None
    low = (store or "").lower()
    if not any(h in low for h in _WIKI_STORE_HINTS):
        return None
    hit = wikipedia_answer(key, question_text)
    if hit is None:
        return None
    return hit["answer"]


def chained_reference_lookup(*resolvers):
    """Build a chained ``reference_lookup(store, key)`` that tries each resolver
    in order and returns the first non-None answer. Each resolver is a callable
    ``(store, key) -> Optional[str]`` that returns None for a store it does not
    handle (ConceptNet first, then Wikipedia) — so the chain is additive and
    graceful: any one returning None passes to the next; all-None -> None."""
    def _lookup(store: str, key: str) -> Optional[str]:
        for r in resolvers:
            try:
                val = r(store, key)
            except Exception:
                val = None
            if val:
                return str(val)
        return None
    return _lookup


__all__ = [
    "wikipedia_answer",
    "reference_lookup",
    "chained_reference_lookup",
]
