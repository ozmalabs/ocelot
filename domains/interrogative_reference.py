"""Closed-class INTERROGATIVE PROFORM reference — the wh-word -> queried-role
fact, documented the same way function_word_reference documents the do-support
_AUX_TENSE closed-class fact.

A wh-word does ONE grammatical job: it marks WHICH SEMANTIC ROLE the question
queries. That mapping is a SMALL, CLOSED CLASS — there are only a handful of
interrogative proforms in a language and each names exactly one queried slot:

    who   -> participant   (agent / patient — resolved by the wh-gap logic)
    what  -> participant   (agent / patient — resolved by the wh-gap logic)
    where -> location
    when  -> time
    why   -> cause
    how   -> manner

This is the interrogative analogue of the do-support auxiliary fact: a closed
finite list, not a parser rule. The world adapter reads it to set the queried
slot on the comprehended frame; the order-N reasoner then queries that slot.

Two TYPES of proform, by what the queried role is:

  * PARTICIPANT proforms (who/what) query a core argument (agent / patient).
    WHICH core argument is NOT fixed by the wh-word — it depends on the clause
    (subject-wh "Who broke the vase?" -> agent; object-wh "Who does Mary love?"
    -> patient). So who/what keep the existing ``?WHO`` / ``?WHAT`` placeholders
    and the existing wh-GAP reconstruction decides agent-vs-patient from
    grounded cues (do-support inversion, case marker, personal-a). The proform
    itself only says "a participant is queried".

  * OBLIQUE proforms (where/when/why/how) query a NON-core role whose identity
    IS fixed by the wh-word (where ALWAYS queries location, when ALWAYS time,
    …). These need NO gap reconstruction: the proform's placeholder goes
    straight into its queried slot. "Where does John live?" -> location=?WHERE.

The placeholder strings (``?WHO`` … ``?HOW``) are the queried-slot markers the
downstream stack already keys on (conversation_world._queried_slot scans the
frame for a slot whose filler is one of these). Adding the oblique proforms is
therefore: (1) ground the surface word -> placeholder in the lexicon, (2) name
the placeholder's queried slot here, (3) have the parser drop the placeholder
into that slot. No new decision logic — a closed-class lookup.

Cross-lingual: the SAME placeholders are language-independent (meaning is). The
per-language surface forms (where/dónde/哪里/どこ, …) are lexicon entries that
map to the same placeholder; this module is the placeholder -> role half, which
is shared.

HONEST scope: only English surface forms are grounded by the stub teacher here
(the demos are English); the placeholder->role map is language-neutral and the
other languages slot in by adding their surface->placeholder lexicon entries.
"""
from __future__ import annotations

from typing import Optional


# The closed-class proform table. surface (lowercased) -> placeholder. English
# only in the stub; other languages add their surfaces mapping to the SAME
# placeholders (the placeholder is the language-neutral queried-slot marker).
_PROFORM_SURFACE: dict[str, dict[str, str]] = {
    "en": {
        "who": "?WHO", "what": "?WHAT", "whom": "?WHO",
        "where": "?WHERE", "when": "?WHEN", "why": "?WHY", "how": "?HOW",
    },
    "es": {
        "quién": "?WHO", "qué": "?WHAT",
        "dónde": "?WHERE", "cuándo": "?WHEN", "por qué": "?WHY", "cómo": "?HOW",
    },
    "ja": {
        "誰": "?WHO", "何": "?WHAT", "どの": "?WHAT",
        "どこ": "?WHERE", "いつ": "?WHEN", "なぜ": "?WHY",
        "どう": "?HOW",
    },
}

# Placeholder -> the semantic slot the question QUERIES. The participant
# proforms (?WHO/?WHAT) have NO fixed slot here (None) — the wh-gap logic picks
# agent-vs-patient. The oblique proforms name their slot directly.
_PLACEHOLDER_QUERIED_SLOT: dict[str, Optional[str]] = {
    "?WHO": None,        # participant — agent/patient via wh-gap
    "?WHAT": None,       # participant — agent/patient via wh-gap
    "?WHERE": "location",
    "?WHEN": "time",
    "?WHY": "cause",
    "?HOW": "manner",
}

# All interrogative placeholders — the set the downstream stack treats as
# "a queried (wh) slot filler". Exported so conversation_world / order_n_reasoning
# can extend their _WH tuple from one source of truth.
ALL_PLACEHOLDERS: tuple[str, ...] = tuple(_PLACEHOLDER_QUERIED_SLOT.keys())

# The OBLIQUE placeholders (fixed queried slot, no gap reconstruction needed).
OBLIQUE_PLACEHOLDERS: tuple[str, ...] = tuple(
    p for p, slot in _PLACEHOLDER_QUERIED_SLOT.items() if slot is not None)


def proform_placeholder(surface: str, language: str) -> Optional[str]:
    """The interrogative placeholder a surface word maps to, or None when the
    surface is not an interrogative proform. Closed-class lookup, no decision."""
    return _PROFORM_SURFACE.get(language, {}).get(surface.lower())


def queried_slot_for(placeholder: str) -> Optional[str]:
    """The semantic slot an OBLIQUE proform placeholder queries (location / time
    / cause / manner), or None for the participant proforms (?WHO/?WHAT — the
    wh-gap logic resolves their slot)."""
    return _PLACEHOLDER_QUERIED_SLOT.get(placeholder)


def is_oblique(placeholder: str) -> bool:
    return placeholder in OBLIQUE_PLACEHOLDERS


def lexicon_pairs(language: str) -> list[tuple[str, str]]:
    """Every (surface, placeholder) pair for a language — the lexicon entries a
    teacher/reference grounds so the parser can resolve interrogative proforms.
    Mechanical reference data, like function_word_reference's closed-class sets."""
    return list(_PROFORM_SURFACE.get(language, {}).items())


__all__ = [
    "ALL_PLACEHOLDERS", "OBLIQUE_PLACEHOLDERS",
    "proform_placeholder", "queried_slot_for", "is_oblique", "lexicon_pairs",
]
