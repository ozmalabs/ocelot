"""acronym_context — the agent expands a technical acronym BY CONTEXT.

An acronym ('AAC', 'TCP', 'ALAC') is in no dictionary and its prose never spells
it out. But its letters are the initials of a phrase, and Wikipedia's
disambiguation page lists the candidate expansions ('AAC: Advanced Audio Coding /
Alaskan Air Command / …'). WHICH one is right is fixed by CONTEXT: the agent reads
the words around the acronym in its own prose (audio, coding, compression) and
picks the expansion whose words overlap that context. Then the acronym grounds via
the expansion's head noun ('AAC' -> 'coding' -> … -> entity).

High precision: an expansion is taken only when its context-overlap clears a
threshold, so a near-miss (a wrong-domain sense sharing one word) is REFUSED, not
grounded — an honest miss beats a wrong meaning. A world-adapter read: the prose
context + the disambiguation list are the statistic; read_and_ground grounds.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

_STOP = set("the a an of to in on for and or is are be by with as at from that which "
            "this these those its per via both than then thus use uses used need".split())


def acronym_contexts(prose_texts) -> dict[str, Counter]:
    """{acronym(lower) -> Counter of context words} for every 2–6 letter ALL-CAPS
    token the prose uses (the candidate acronyms + the words around them)."""
    text = " ".join(prose_texts)
    ctx: dict[str, Counter] = {}
    for m in re.finditer(r"(?<![A-Za-z])([A-Z]{2,6})(?![A-Za-z])", text):
        acr = m.group(1).lower()
        lo, hi = max(0, m.start() - 90), m.end() + 90
        window = text[lo:hi]
        c = ctx.setdefault(acr, Counter())
        for w in re.findall(r"[a-z]{4,}", window.lower()):
            if w != acr and w not in _STOP:
                c[w] += 1
    return ctx


def _candidate_expansions(acr: str, wiki_text: str) -> list[str]:
    """Phrases in `wiki_text` whose word-initials spell `acr` (skipping
    of/the/and/for/de) — the disambiguation senses, as written."""
    if not wiki_text:
        return []
    pat = (r"\b" + r"[A-Za-z]*\s+(?:of |the |and |for |de )?".join(
        "[" + c.upper() + "]" for c in acr.lower()) + r"[A-Za-z]*")
    return list(dict.fromkeys(re.findall(pat, wiki_text)))


def expand_acronym(acr: str, context: Counter, min_score: int = 2) -> Optional[str]:
    """The HEAD NOUN of the context-best expansion of `acr`, or None. Reads the
    full Wikipedia disambiguation text, scores each candidate expansion by overlap
    with the prose `context`, and returns the head noun of the best — only when the
    overlap clears `min_score` (else an honest None)."""
    try:
        from domains import wiki_local as wl
        s = wl.summary(acr)
    except Exception:
        return None
    cand = _candidate_expansions(acr, s.get("text", "") if s else "")
    best, best_score = None, 0
    for e in cand:
        ews = {w.lower() for w in re.findall(r"[a-z]{4,}", e.lower())}
        score = (sum(context.get(w, 0) for w in ews)
                 + sum(1 for w in ews if any(w[:4] == cw[:4] for cw in context)))
        if score > best_score:
            best, best_score = e, score
    if best is None or best_score < min_score:
        return None
    words = re.findall(r"[A-Za-z]{3,}", best)
    if len(words) < 2:                 # a real expansion is multi-word
        return None
    head = words[-1].lower()
    # the head must itself GROUND (a real noun whose ladder reaches the bedrock) —
    # this drops junk heads ('true', 'all') AND guarantees the acronym we claim
    # actually grounds.
    try:
        from domains import wordnet_genus as wg
        chain = wg.hypernym_chain(head)
        if not (chain and chain[-1] == "entity"):
            return None
    except Exception:
        return None
    return head


def build_acronym_heads(prose_texts, min_score: int = 3) -> dict[str, str]:
    """{acronym(lower) -> expansion head noun} for every prose acronym (3+ letters)
    that expands confidently by context. Computed once; the campaign uses it."""
    out: dict[str, str] = {}
    for acr, ctx in acronym_contexts(prose_texts).items():
        if len(acr) < 3:              # 2-letter 'acronyms' match too spuriously
            continue
        head = expand_acronym(acr, ctx, min_score=min_score)
        if head:
            out[acr] = head
    return out


class AcronymReader:
    """Reader for read_and_ground: the acronym grounds via its context-chosen
    expansion's HEAD NOUN ('aac' -> 'coding'), and that noun chains through lazy
    WordNet to the bedrock."""

    def __init__(self, acr: str, head: str):
        from domains import wordnet_genus as wg
        feed = wg._HybridFeed(acr)
        article = "an" if head[:1] in "aeiou" else "a"
        feed[acr] = f"{acr} is {article} {head}"
        self._definition_feed = feed
