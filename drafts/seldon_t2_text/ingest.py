"""
ingest — legs (i) + (iii): the arxiv_local `_load()` pattern re-pointed at the
timestamped news corpus (prereg §1).

Leg (i) BULK INGESTION: a single mechanical pass over the corpus items, exactly
the shape of `domains/arxiv_local._load()` — structural position delimits items,
each becomes a typed record. No reasoning (CLAUDE.md world-adapter discipline);
this only supplies the structured record the linking + typing legs consume.

Leg (iii) CLAIM -> TYPED RECORD: the arxiv importer's `kind`/`attribution`
capture is the template. Here the typed vocabulary is the T2 event taxonomy
{regime->0 (down), regime->1 (up), none}, recovered from prose by a SMALL fixed
directional-cue lexicon (the real analogue of the PoC's free `incoming_regime`).
This is the precision-limited step; it reads ONLY the rendered text, never the
ground-truth struct.

  CorpusItem{doc_id, tick, text, mention_surface, claim_kind}

`mention_surface` is the candidate entity surface pulled from the sentence (the
leg-(ii) linker resolves it to a panel Concept). `claim_kind` in
{"down","up","none"} is the typed claim. Both are BEST-EFFORT reads of prose;
their recall/precision against ground truth is a measured secondary (prereg §6),
not assumed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# Directional cue lexicon (leg iii, FIXED). Deliberately small + surface — the
# honest, precision-limited claim typer. Maps a cue word to a regime band.
_DOWN_CUES = {"cut", "softens", "soften", "decline", "downturn", "weak", "lower"}
_UP_CUES = {"raise", "surge", "expand", "sharply", "strong", "upward", "higher"}
# Neutral / distractor cues that should type as "none" even though they name a
# direction-adjacent word — the spurious-item trap.
_NEUTRAL_CUES = {"routine", "reaffirmed", "mixed", "ambiguous", "debated", "no change"}


@dataclass
class CorpusItem:
    doc_id: str
    tick: int
    text: str
    mention_surface: str | None   # candidate entity surface (leg ii input)
    claim_kind: str               # "down" | "up" | "none" (leg iii output)


def _tokens(text: str) -> list[str]:
    """Lowercased alnum tokens (mechanical, no NLP lib)."""
    return re.findall(r"[a-zA-Z][a-zA-Z0-9.]*", text.lower())


def _extract_mention_surface(text: str) -> str | None:
    """The candidate entity surface: the LEADING capitalised span of the
    sentence (news items name the subject first), OR a leading all-caps ticker.
    Mechanical surface read — the linker decides what it refers to.

    Handles: 'Acme Corp is ...', 'ACME is ...', 'Analysts expect Juno. to ...',
    'Traders debated Umbra Corp after ...'. When the sentence opens with a
    non-entity lead word (Analysts/Traders/Nobody), take the first capitalised
    span AFTER that lead word."""
    # strip a leading commentary lead ("Analysts see", "Traders debated",
    # "Analysts expect") so the entity span that follows is found.
    lead_re = re.compile(r"^(analysts?|traders?)\b\s+\w+\s+", re.IGNORECASE)
    m = lead_re.match(text)
    rest = text[m.end():] if m else text

    # a capitalised span: one or more Capitalised words (allowing a trailing '.'
    # as part of a ticker-ish surface like 'Juno.'), or an all-caps token.
    span_re = re.compile(r"([A-Z][A-Za-z]*\.?(?:\s+[A-Z][A-Za-z]*)*)")
    m2 = span_re.search(rest)
    if not m2:
        return None
    surface = m2.group(1).strip()
    # trim a trailing lowercase-triggering word that got glued (defensive)
    return surface or None


def _type_claim(text: str) -> str:
    """Leg (iii): type the claim from directional cues. 'none' when neutral cues
    dominate or no directional cue is present. Precision-limited by design."""
    toks = set(_tokens(text))
    low = text.lower()
    if any(cue in low for cue in _NEUTRAL_CUES):
        return "none"
    n_down = len(toks & _DOWN_CUES)
    n_up = len(toks & _UP_CUES)
    if n_down == 0 and n_up == 0:
        return "none"
    if n_down > n_up:
        return "down"
    if n_up > n_down:
        return "up"
    return "none"  # tie -> unresolved, honest


def ingest_item(news_item) -> CorpusItem:
    """One pass: a rendered NewsItem -> a typed CorpusItem. Reads text + tick
    only (never the gt_* struct fields)."""
    surface = _extract_mention_surface(news_item.text)
    kind = _type_claim(news_item.text)
    return CorpusItem(
        doc_id=news_item.doc_id, tick=int(news_item.tick),
        text=news_item.text, mention_surface=surface, claim_kind=kind,
    )


def ingest_corpus(items) -> list:
    """Leg (i): mechanical bulk pass over the corpus items (arxiv _load shape)."""
    return [ingest_item(it) for it in items]


# claim_kind -> incoming regime band {0,1}, or None for "none". The bridge from
# the typed claim to the panel's regime index the forecaster shifts toward.
def claim_to_regime(kind: str) -> int | None:
    return {"down": 0, "up": 1}.get(kind)


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from corpus_gen import generate_corpus

    c = generate_corpus(seed=1)
    ci = ingest_corpus(c.items)
    # measured secondary preview: type precision/recall vs ground truth
    hit_surface = 0
    hit_type = 0
    n_real = 0
    for it, item in zip(ci, c.items):
        if item.gt_surface and it.mention_surface and \
                item.gt_surface.rstrip(".").lower() in it.mention_surface.rstrip(".").lower():
            hit_surface += 1
        if not item.gt_spurious:
            n_real += 1
            if claim_to_regime(it.claim_kind) == item.gt_incoming_regime:
                hit_type += 1
    print(f"ingested {len(ci)} items")
    print(f"surface-extract hit (surface substring recovered): "
          f"{hit_surface}/{len(ci)} = {hit_surface/len(ci)*100:.1f}%")
    print(f"claim-type recall on real-switch items: "
          f"{hit_type}/{n_real} = {hit_type/max(1,n_real)*100:.1f}%")
    for it in ci[:6]:
        print(f"  t={it.tick:3d} surface={it.mention_surface!r:20s} "
              f"kind={it.claim_kind:5s} :: {it.text}")
