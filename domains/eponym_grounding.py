"""eponym_grounding — the agent grounds an EPONYM by reading its own prose.

A technical eponym ('Ackermann function', "Amdahl's law", 'Anfinsen dogma',
'Shannon entropy', 'Nyquist limit') is a thing named after the PERSON who found
it. The word 'ackermann' is in no dictionary — but the agent's prose USES it, and
its shape in the prose says what it is: a Capitalized name (often possessive)
modifying a technical concept noun. That is the eponym pattern; the name denotes a
PERSON. So the agent reads its prose, recognises the eponym, and grounds it as a
person — which chains to the bedrock through the dictionary (person -> … -> entity).

A thin world-adapter read of the corpus (the distributional STATISTIC of the
shape), exactly like forward_segmentation / morpheme_decomposition: the prose
pattern parameterises the rule; grounding is the agent's read_and_ground.
"""
from __future__ import annotations

import re

# Technical concept nouns an eponym attaches to (the "<Name> <thing>" shape).
_THING = (r"(?:function|law|theorem|lemma|dogma|number|space|algorithm|conjecture"
          r"|inequality|distribution|process|transform|constant|equation|principle"
          r"|effect|limit|criterion|bound|entropy|rule|series|cipher|code|machine"
          r"|model|test|notation|hierarchy|coding|filter|encoding|condition|paradox"
          r"|identity|formula|method|measure|metric|matrix|operator|map|graph)")

_EPONYM_RE = re.compile(r"\b([A-Z][a-z]{3,})(?:['’]s)?\s+" + _THING + r"\b")
_NAMED_AFTER_RE = re.compile(
    r"(?:named after|due to|introduced by|discovered by|invented by|proposed by)\s+"
    r"(?:[A-Z][a-z]+\s+)?([A-Z][a-z]{3,})")


def detect_eponyms(prose_texts) -> set[str]:
    """The lower-cased eponym (person) names the prose attests: a Capitalized,
    NON-dictionary name in the eponym shape ('<Name> <technical-thing>' or
    'named after <Name>'). Filtering to non-dictionary names drops the
    sentence-start common words ('The function', 'Modern code')."""
    from domains.dict_teacher import _wordnet
    wn = _wordnet()
    cand: set[str] = set()
    for text in prose_texts:
        for m in _EPONYM_RE.finditer(text):
            cand.add(m.group(1))
        for m in _NAMED_AFTER_RE.finditer(text):
            cand.add(m.group(1))
    # a real eponym is a PROPER NAME — not a common dictionary word nor a
    # determiner/pronoun capitalised at a sentence start ('This rule', 'These …').
    _FUNC = {"this", "that", "these", "those", "their", "there", "then", "thus",
             "such", "each", "some", "many", "most", "more", "both", "what",
             "when", "where", "which", "while", "with", "from", "they", "them"}
    out = set()
    for name in cand:
        low = name.lower()
        if len(low) < 4 or low in _FUNC:
            continue
        if wn.synsets(low):          # a common word capitalised at sentence start
            continue
        out.add(low)
    return out


class EponymReader:
    """Reader for read_and_ground: an eponym grounds AS A PERSON, and 'person'
    (and any other sub-genus) chains via lazy WordNet — so the descent reaches the
    bedrock (person -> … -> entity)."""

    def __init__(self, name: str):
        from domains import wordnet_genus as wg
        feed = wg._HybridFeed(name)        # lazy WordNet for sub-genera
        # SENSE-CONSISTENT 'person' ladder (pointer-following, person -> organism
        # -> … -> entity) instead of the lazy per-word re-lookup, which WANDERS
        # ('organism' -> 'situation' -> …) and can miss the bedrock within the
        # depth bound. Pre-loading the deterministic chain makes the eponym ground
        # robustly regardless of environment.
        feed.update(wg.chain_definition_feed("person"))
        lead = f"{name.replace('_', ' ')} is a person"
        feed[name] = lead
        feed[name.replace("_", " ")] = lead
        self._definition_feed = feed
