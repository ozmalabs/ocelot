"""lexical_qualia -- every held word links to one or more qualia.

The quale index is native graph data (seeds/lexical_qualia.json, emitted by
scripts/gen_lexical_qualia_index.py): `Quale` nodes plus one edge type,
`has_quale`, running word -> sense quale -> broader quale. A word's quale
closure is `ReachableFrom(word, "has_quale")`. Matching two words is the
intersection of their closures at an aperture (which dimensions are resolved,
how general a shared quale may be) -- fuzzy by shared meaning, exact at the
grain: Quale node identity and integer `extent` counts.

This module is MECHANICAL I/O only (CLAUDE.md):
  * `install_word_links(agent)` -- boot pass: install the persisted
    word->sense links onto held Concepts via the Concept.name index.
  * `ground_word(agent, word)` -- the I/O boundary for a word the agent has
    not held before: the persisted WordNet sense table
    (domain_data/wordnet_senses.sqlite via domains/wordnet_table) is external
    data a graph rule cannot query, so the adapter translates the word's
    senses into Quale nodes + has_quale edges (reusing
    existing Quale nodes), mints the held Concept, and increments `extent` on
    the word's closure so the index statistic stays an exact count. A word
    with no sense and no closed-class role gets its identity quale (the
    honest degenerate quale until it is grounded).
Neither decides anything about what a turn means or which concern it names;
the graph rules that read the index do.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[1]
_SEED = _ROOT / "seeds" / "lexical_qualia.json"
EDGE = "has_quale"
_WORD_RE = re.compile(r"^[a-z][a-z'-]*$")
_CLOSED: Optional[dict] = None


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None) or getattr(sub, "_inner", sub)
    return sub, native


def _word_table() -> dict:
    """{word: [quale names]} from the persisted seed. Read per install and NOT
    retained: the parsed 4.5 MB manifest is ~tens of MB of Python objects
    (measured RSS), and the graph already holds the Quale nodes."""
    d = json.loads(_SEED.read_text())
    by_local = {n["local_id"]: n["attrs"]["name"] for n in d["nodes"] if n["type"] == "Quale"}
    table = {w: [by_local[i] for i in ids] for w, ids in d.get("word_qualia", {}).items()}
    del d, by_local
    return table


def _closed_class() -> dict:
    global _CLOSED
    if _CLOSED is None:
        d = json.loads((_ROOT / "domain_data" / "reading_constructions.json").read_text())
        out = {}
        for n in d.get("nodes", []):
            if n.get("type") == "ClosedClass":
                role = n.get("attrs", {}).get("role")
                for f in n.get("attrs", {}).get("forms") or []:
                    out.setdefault(str(f).lower(), set()).add(str(role))
        _CLOSED = out
    return _CLOSED


def _quale(native, name: str):
    try:
        hits = native.nodes_where("Quale", "name", name)
    except Exception:  # noqa: BLE001
        hits = []
    return hits[0] if hits else None


def _has_edge(sub, src, tgt) -> bool:
    try:
        return sub.has_edge(src, EDGE, tgt)
    except Exception:  # noqa: BLE001
        return False


def install_word_links(agent) -> dict:
    """Boot pass: link every held word Concept to its persisted sense qualia.
    Idempotent. Returns counts."""
    sub, native = _resolve(agent)
    try:
        if not list(sub.nodes("QualiaIndex")):
            return {"installed": 0, "skipped": "lexical_qualia seed not loaded"}
    except Exception:  # noqa: BLE001
        return {"installed": 0, "skipped": "no QualiaIndex type"}
    try:
        native.declare_attr_index("Quale", "name")
    except Exception:  # noqa: BLE001
        pass
    table = _word_table()
    installed = words = 0
    qcache: dict = {}
    for word, qnames in table.items():
        try:
            concepts = native.nodes_where("Concept", "name", word)
        except Exception:  # noqa: BLE001
            concepts = []
        if not concepts:
            continue
        words += 1
        for qn in qnames:
            q = qcache.get(qn)
            if q is None:
                q = qcache[qn] = _quale(native, qn)
            if q is None:
                continue
            for c in concepts:
                if not _has_edge(sub, c, q):
                    native.add_edge_unchecked(c, EDGE, q)
                    installed += 1
    # Unheld words are grounded later from the persisted on-disk sense table
    # (domains/wordnet_table, sqlite): no in-process WordNet corpus, so no
    # boot warm-up and no cold load on a turn's ingress path.
    del table, qcache
    import gc
    gc.collect()
    return {"installed": installed, "words_linked": words}


def _ensure_sense(sub, native, name: str, minted: list):
    """Quale node for a WordNet synset name, reusing an existing one; mints the
    hypernym chain above it on demand from the persisted sense table."""
    q = _quale(native, name)
    if q is not None:
        return q
    from domains import wordnet_table as wt
    q = sub.add_node("Quale", {"name": name, "dimension": "lexical:sense", "extent": 0})
    minted.append(q)
    for p in wt.hypernyms(name):
        pq = _ensure_sense(sub, native, p, minted)
        native.add_edge_unchecked(q, EDGE, pq)
    return q


def _named_quale(sub, native, name, dimension, lemma, minted):
    q = _quale(native, name)
    if q is None:
        q = sub.add_node("Quale", {"name": name, "dimension": dimension, "extent": 0})
        minted.append(q)
    return q


def held_qualia(agent, concept) -> list:
    sub, native = _resolve(agent)
    try:
        return list(native.neighbours(concept, EDGE))
    except Exception:  # noqa: BLE001
        return []


def ground_word(agent, word: str, *, allow_identity: bool = False):
    """The I/O boundary for a word with no held Concept: mint the Concept and
    link it to its qualia (WordNet senses, else its closed-class role, else its
    identity quale). Returns the Concept node, or None for a non-word token.
    Increments `extent` exactly on every quale in the new word's closure."""
    if not isinstance(word, str) or not _WORD_RE.match(word):
        return None
    sub, native = _resolve(agent)
    if not list(sub.nodes("QualiaIndex")):
        return None
    try:
        existing = native.nodes_where("Concept", "name", word)
    except Exception:  # noqa: BLE001
        existing = []
    if existing:
        return existing[0]
    minted: list = []
    roles = _closed_class().get(word)
    if roles:
        sense_q = [_named_quale(sub, native, "closed_class:" + r, "closed_class", r, minted) for r in sorted(roles)]
    else:
        from domains import wordnet_table as wt
        syns = sorted(set(wt.synsets(word))) if wt.available() else []
        if syns:
            sense_q = [_ensure_sense(sub, native, s, minted) for s in syns]
        elif allow_identity:
            sense_q = [_named_quale(sub, native, "identity:" + word, "lexical:identity", word, minted)]
        else:
            return None
    c = sub.add_node("Concept", {"name": word, "source": "lexical_qualia"})
    try:
        agent_node = getattr(agent, "agent", None)
        if agent_node is not None:
            native.add_edge_unchecked(agent_node, "knows_concept", c)
    except Exception:  # noqa: BLE001
        pass
    for q in sense_q:
        native.add_edge_unchecked(c, EDGE, q)
    # extent: +1 on every quale in this word's closure (exact count update)
    closure, stack = set(), list(sense_q)
    while stack:
        q = stack.pop()
        if q in closure:
            continue
        closure.add(q)
        stack.extend(native.neighbours(q, EDGE))
    for q in closure:
        at = sub.node(q)["attrs"]
        sub.set_attr(q, "extent", int(at.get("extent") or 0) + 1)
    for n in sub.nodes("QualiaIndex"):
        at = sub.node(n)["attrs"]
        sub.set_attr(n, "words", int(at.get("words") or 0) + 1)
        sub.set_attr(n, "qualia", int(at.get("qualia") or 0) + len(minted))
    return c


__all__ = ["EDGE", "install_word_links", "ground_word", "held_qualia"]
