"""COMPARATIVE construction reference — the grammatical construction that
realizes a transitive ordering relation in natural language, plus the POLAR
(yes/no) question construction that asks about one.

This is a CONSTRUCTION, not a closed-class lexical fact (unlike the do-support
auxiliary or the interrogative proform). A comparative clause

    [NP_subject] is [ADJ-er] than [NP_standard]
    "the cat   is  bigger   than  the mouse"

asserts/queries a binary relation R(subject, standard) where R is the ordering
named by the comparative adjective (bigger -> the `bigger` relation). Two pieces
are GROUNDED rather than hardcoded:

  * the COMPARATIVE DEGREE — English marks it morphologically with the ``-er``
    suffix (bigger / taller / faster) or the periphrastic "more ADJ"; the
    relation concept is the adjective's lemma-as-relation (the stub grounds
    "bigger" -> concept "bigger"). The ``-er`` test is the same shape of
    surface-morphology probe as _event_tense_probe.
  * the STANDARD MARKER — the function word that introduces the standard of
    comparison (English "than", Spanish "que"). It is a GROUNDED FunctionWord
    (a preposition, per Wiktionary POS); the construction reads it to mark the
    following NP as the ``standard`` role. The marker SET is the closed-class
    part; reading the grounded node is the construction.

POLAR questions: a yes/no question has NO wh-word and is COPULA/AUXILIARY-
INITIAL (subject-aux inversion with nothing fronted): "Is the cat bigger than
the mouse?". The polar construction is detected from a grounded clause-initial
copula/auxiliary FunctionWord + the absence of any interrogative proform. A
polar comparative question -> reason_transitive (order-N transitive closure).

Honest scope: English + Spanish standard markers; English ``-er`` comparative
morphology (the demo uses "bigger"). Periphrastic "more ADJ" and irregular
comparatives (better/worse) are a later reference pass — documented, not faked.
"""
from __future__ import annotations

from typing import Optional


# Standard-of-comparison markers per language (the closed-class function words
# that introduce the standard NP). Read as a grounded FunctionWord at parse
# time; this set is the membership test.
_STANDARD_MARKER: dict[str, set[str]] = {
    "en": {"than"},
    "es": {"que"},
}

# Irregular English comparatives whose surface is not ADJ+er (the demo doesn't
# use these; listed so the probe can be honest about its coverage and extended).
_IRREGULAR_COMPARATIVE: dict[str, str] = {
    "bigger": "bigger",   # regular, but pre-listed so the stub concept matches
    "better": "better",
    "worse": "worse",
    "more": "more",
}


def is_standard_marker(surface: str, language: str) -> bool:
    """Is ``surface`` the standard-of-comparison marker (than / que)? Closed-class
    membership; the parser confirms the token also grounded as a FunctionWord."""
    return surface.lower() in _STANDARD_MARKER.get(language, set())


def comparative_relation(surface: str, concept: Optional[str],
                         language: str) -> Optional[str]:
    """If ``surface`` is a comparative-degree form, return the ORDERING RELATION
    it names (the concept), else None. English: the ``-er`` suffix (or an
    irregular comparative) marks comparative degree; the relation is the grounded
    concept the surface resolved to (bigger -> "bigger"). No-op for languages
    without ``-er`` morphology unless the surface is a known comparative."""
    s = surface.lower()
    if language == "en":
        if s in _IRREGULAR_COMPARATIVE:
            return concept or _IRREGULAR_COMPARATIVE[s]
        # Regular ``-er`` comparative (bigger/taller/faster). Require a grounded
        # concept so we don't mis-fire on nouns ending in -er (teacher/water);
        # the construction only treats it as a relation when it resolved to a
        # concept AND sits in the predicate slot of a comparative clause.
        if s.endswith("er") and concept is not None:
            return concept
    return None


__all__ = ["is_standard_marker", "comparative_relation"]
