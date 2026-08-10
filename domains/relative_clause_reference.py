"""RELATIVE-CLAUSE construction reference — the embedded-clause template that
lets a question NAME an entity by a fact about it instead of by its name:

    "the person [who/that/<zero>] Mary loves"   ==  the X such that love(Mary, X)

This is the bounded, recognizable template the capstone uses. A relative clause
modifying a GENERIC HEAD NOUN (person / one / thing — a placeholder head, not a
specific entity) followed by a SUBJECT NP and a VERB denotes the entity that
fills the verb's OPEN argument. Comprehension RESOLVES that entity by calling
the reasoner (order-1: the patient of love(Mary, ?)), substitutes it back into
the matrix clause, and then parses the matrix as a normal question — so the
matrix question runs order-N end-to-end on a resolved entity.

What is GROUNDED vs a CONSTRUCTION (honest):
  * GENERIC HEAD nouns + RELATIVE PRONOUNS are small closed-class sets (read
    here); the relative-clause attachment is the CONSTRUCTION (a grammatical
    template, like the comparative). We recognize the BOUNDED template
    "[the] HEAD (REL)? SUBJ VERB" — not arbitrary relativization.
  * The embedded entity is resolved by the SAME order-N operator the matrix
    question uses (onr.reason); the construction only locates the clause and
    hands its (subject, verb) to the operator.

HONEST BOUND (reported by the demo): only this template parses — a generic head
+ a transitive relative clause whose verb's subject is overt and whose object is
the gap. Stacked/again-embedded relatives, subject-gap relatives ("the person
who loves Mary"), and non-generic heads are NOT covered; documented, not faked.
"""
from __future__ import annotations


# Generic / light head nouns a relative clause can hang on as a placeholder for
# "the entity such that …". Closed set; a SPECIFIC head ("the dog Mary loves")
# is out of the bounded template's scope.
_GENERIC_HEADS: dict[str, set[str]] = {
    "en": {"person", "one", "thing", "people", "man", "woman"},
    "es": {"persona", "uno", "cosa"},
}

# Relative pronouns that may (optionally) introduce the clause. Zero-relative
# ("the person Mary loves") is also accepted — hence "optional".
_REL_PRONOUNS: dict[str, set[str]] = {
    "en": {"who", "whom", "that", "which"},
    "es": {"que", "quien", "quién"},
}


def is_generic_head(surface: str, language: str) -> bool:
    return surface.lower() in _GENERIC_HEADS.get(language, set())


def is_rel_pronoun(surface: str, language: str) -> bool:
    return surface.lower() in _REL_PRONOUNS.get(language, set())


__all__ = ["is_generic_head", "is_rel_pronoun"]
