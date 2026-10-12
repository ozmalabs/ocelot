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


# --------------------------------------------------------------------------- #
# Tranche 17 -- DEFINITIONAL GROUNDING of a held word with no WordNet sense.
#
# A held jargon word ("kubernetes", "microservice", "autopoiesis") usually
# carries the definition it was taught with. Its quale is then that DEFINITION:
# a `Quale{name:"definition:<word>", dimension:"lexical:definition", genus}`
# whose has_quale parents are the WordNet noun senses of the definition's
# GENUS (its head noun: "Container orchestrator: ..." -> orchestrator), exactly
# as a synset's parents are its hypernyms. So the word meets other words
# through what it was defined AS. A function word with no sense gets its
# closed-class role from the held function-word faculty. Only a word with
# neither keeps the honest identity quale.
# --------------------------------------------------------------------------- #
_DISAMBIG_RE = re.compile(r"\b(?:may (?:also )?refer to|can refer to|is the name of|may (?:also )?be:|"
                          r"is (?:a )?(?:sur|given )?name of:)", re.I)
_POS_TAG_RE = re.compile(r"^\(([a-z ]+)\)\s*")
_SEGMENT_RE = re.compile(r"\.\s|\.$|:|;|\n|\s[\u2014\u2013]\s|\s--\s")
_CLAUSE_CUT_RE = re.compile(r"[,(\[/+|=\u2014\u2013\"\u201c\u201d]")
_COPULA_LEAD_RE = re.compile(r"^(?P<lead>.{1,80}?)\s+(?:is|was|are|were)\s+(?:a|an|the)\s+(?P<rest>.+)$", re.I)
_COPULA_ANY_RE = re.compile(r"\s(?:is|was|are|were)\s", re.I)
_GENUS_SEGMENTS = 3
_PAREN_RE = re.compile(r"\([^()]*\)")
# a quoted dictionary gloss's bookkeeping segments ("synonyms: ...", "e.g. ...",
# "+3 other senses") are not the gloss
_GLOSS_META_RE = re.compile(r"^(?:synonyms?\b|e\.g\b|eg\b|\+\d+ other senses?|also\b|see also\b)", re.I)
_GLOSS_TAIL_RE = re.compile(r"[;,]?\s*(?:\bsynonyms?:|\be\.g\.|\+\d+ other senses?)", re.I)
_ANALOGUE_RE = re.compile(r"\bsubstrate analogue\b", re.I)
_RELATIVIZERS = frozenset({"that", "which", "who", "whom", "whose", "where", "when", "whereby"})
_EMPTY_HEADS = frozenset({"type", "types", "kind", "kinds", "sort", "sorts", "form", "forms",
                          "variety", "class", "species", "genus", "member", "group", "set"})


def function_role(word: str, definition=None):
    """The closed-class role of a word with no WordNet sense, read off held
    data: the POS tag its own definition carries ("(pronoun) ..."), else the
    function-word faculty (domains/function_word_reference). None when it is a
    content word."""
    try:
        from domains import function_word_reference as fw
    except Exception:  # noqa: BLE001
        return None
    if isinstance(definition, str):
        m = _POS_TAG_RE.match(definition.strip().lower())
        if m:
            role = fw._POS_FUNCTION.get(m.group(1).strip())
            if role:
                return role
    try:
        spec = fw.classify(word, "en")
    except Exception:  # noqa: BLE001
        spec = None
    return spec.get("function") if spec else None


def _postnominal_participle(cq, toks, i, p) -> bool:
    """A participle AFTER the head that opens its own phrase ("an officer
    HOLDING a rank", "an element BELONGING to") -- followed by a determiner, a
    preposition or nothing. A prenominal participle ("a RETIRED footballer",
    "a WIRING diagram", "Double-ENDED queue") is followed by a noun and is part
    of the head NP, so it does not cut."""
    t = toks[i]
    if not (t.endswith(("ing", "ed")) and "verb" in p):
        return False
    nxt = cq._function_of(toks[i + 1]) if i + 1 < len(toks) else None
    if nxt == "determiner":          # "an officer HOLDING a rank": a VP, whatever POS ranks first
        return True
    if p[:1] == ["noun"]:
        return False
    return i + 1 >= len(toks) or nxt == "preposition"


def _genus_of_segment(seg: str, word: str):
    """The head noun of one definition segment, by the held POS faculty
    (consumption_quality) and the sense table (compounds): the same steps as
    reading_collapse._clean_head, plus a cut at the first verb-primary token
    after a noun (a participle differentia: "Planet ORBITING another star")."""
    from domains import consumption_quality as cq
    from domains import wordnet_table as wt
    seg = _CLAUSE_CUT_RE.split(_PAREN_RE.sub(" ", seg), 1)[0]
    toks = [t.strip("'.") for t in cq._tokens(re.sub(r"[^a-z'\- ]", " ", seg.lower()))]
    toks = [t for t in toks if t]
    # an EMPTY head ("a TYPE OF lichen", "a FORM OF the given name") names
    # the genus by its of-complement, as a dictionary gloss does.
    for i, t in enumerate(toks[:5]):
        if t in _EMPTY_HEADS and i + 1 < len(toks) and toks[i + 1] == "of":
            toks = toks[i + 2:]
            break
        p = cq._pos(t)
        if p and p[0] in ("noun", "verb") or not p:
            break        # the head came first ("a person who lacks any sort of")
    if not toks:
        return None
    # a held "X of Y" compound is one head ("a BODY OF WATER", "point of view"):
    # merge it before the preposition cut reads "of" as a postmodifier.
    merged, i = [], 0
    while i < len(toks):
        if i + 2 < len(toks) and toks[i + 1] == "of" and wt.synsets("%s_of_%s" % (toks[i], toks[i + 2])):
            merged.append("%s_of_%s" % (toks[i], toks[i + 2]))
            i += 3
        else:
            merged.append(toks[i])
            i += 1
    toks = merged

    def prim(t):
        p = cq._pos(t)
        return p[0] if p else ""

    seen_noun = seen_any_noun = closed_by_clause = False
    for i, t in enumerate(toks):
        p = cq._pos(t)
        fn = cq._function_of(t)
        if (seen_noun and (fn in ("preposition", "conjunction") or t in _RELATIVIZERS
                           or (p and p[0] == "verb"))) or (seen_any_noun and (
                t in _RELATIVIZERS or _postnominal_participle(cq, toks, i, p))):
            closed_by_clause = t in _RELATIVIZERS or _postnominal_participle(cq, toks, i, p)
            toks = toks[:i]
            break
        if fn is None and (not p or "noun" in p):
            seen_any_noun = True
            if not p or p[0] == "noun":
                seen_noun = True
    end = len(toks)
    while end > 1 and (prim(toks[end - 1]) in ("verb", "adv", "conj", "det")
                       or cq._function_of(toks[end - 1]) in ("determiner", "conjunction")):
        end -= 1
    core = toks[:end]

    def is_head(t, any_noun=False):
        # the head is a noun by its PRIMARY reading (or an out-of-vocabulary
        # technical token), not a proper name, a closed-class word or a stray
        # letter ("C. elegans").
        p = cq._pos(t)
        ok = ("noun" in p) if any_noun else (not p or p[0] == "noun")
        return ok and cq._function_of(t) is None and len(t) >= 3

    heads = [i for i in range(len(core) - 1, -1, -1) if is_head(core[i])]
    if not heads and closed_by_clause and core and is_head(core[-1], any_noun=True):
        heads = [len(core) - 1]   # "a CRIMINAL who takes": the clause names its head
    # the rightmost candidate that IS a held noun; a verb-form candidate with
    # no noun sense is skipped ("a hollow device MADE of" -> "device"), an
    # unheld noun stops the search. The longest held compound ending at the
    # head wins.
    for head_i in heads:
        for start in range(0, head_i + 1):
            key = "_".join(core[start:head_i + 1])
            if key == word:
                continue
            syns = sorted({s for s in wt.synsets(key) if s.split(".")[-2] == "n"})
            if syns:
                return key, syns
        if "verb" not in cq._pos(core[head_i]):
            return None          # an unheld noun head ("... reference ENCODER"): no genus
    return None


def definition_genus(word: str, definition):
    """{genus, senses, segment} for a held definition, or None. A
    disambiguation stub ("X may refer to:") names no genus. Segments are read
    in order (a leading citation like "Gibson." has no sense; the gloss after
    it does); a copula gloss "X is a Y ..." is read from Y; a segment that
    predicates something else of the word ("Robur is Latin for ...") is not a
    genus gloss and is skipped."""
    if not isinstance(definition, str) or not definition.strip():
        return None
    text = definition.strip()
    if _DISAMBIG_RE.search(text[:240]):
        return None
    text = _POS_TAG_RE.sub("", text)
    # the held self-model gloss ("Substrate analogue: ...") is commentary on
    # the agent, not part of the word's definition
    cut = _ANALOGUE_RE.search(text)
    if cut:
        text = text[:cut.start()]
    meta = _GLOSS_TAIL_RE.search(text)
    if meta:
        text = text[:meta.start()]
    segs = [s.strip() for s in _SEGMENT_RE.split(text) if s and s.strip()]
    segs = [s for s in segs if not _GLOSS_META_RE.match(s)]
    for seg in segs[:_GENUS_SEGMENTS]:
        m = _COPULA_LEAD_RE.match(seg)
        if m and word in m.group("lead").lower():
            seg = m.group("rest")
        elif _COPULA_ANY_RE.search(seg) and seg.lower().startswith(word):
            continue
        got = _genus_of_segment(seg, word)
        if got:
            return {"genus": got[0], "senses": got[1], "segment": seg[:120]}
    return None


def definition_genus_by_reading(agent, word: str, definition):
    """The genus by the AGENT'S OWN READER: the first definition sentence is
    read as the clause "<word> is <sentence>" (or as written, when it already
    predicates the word with a copula) by reading_collapse.read_clause_order_n,
    whose definitional construction names the is_a genus with a clean head.
    No write, no learning. {genus, senses, segment} or None."""
    if not isinstance(definition, str) or not definition.strip():
        return None
    text = definition.strip()
    if _DISAMBIG_RE.search(text[:240]):
        return None
    text = _POS_TAG_RE.sub("", text)
    cut = _ANALOGUE_RE.search(text)
    if cut:
        text = text[:cut.start()]
    segs = [s.strip() for s in _SEGMENT_RE.split(text) if s and s.strip()]
    if not segs:
        return None
    seg = segs[0]
    if _COPULA_ANY_RE.search(" " + seg[:90] + " ") and word in seg[:90].lower():
        clause = seg
    else:
        clause = "%s is %s" % (word, seg[0].lower() + seg[1:])
    try:
        from domains import reading_collapse as rc
        out = rc.read_clause_order_n(agent, clause, write=False, learn=False)
    except Exception:  # noqa: BLE001 -- an unreadable clause names no genus
        return None
    genus = out.get("genus")
    if not isinstance(genus, str) or not genus or genus == word:
        return None
    genus = genus.lower()
    from domains import wordnet_table as wt
    senses = sorted({s for s in wt.synsets(genus) if s.split(".")[-2] == "n"})
    if not senses:
        return None
    return {"genus": genus, "senses": senses, "segment": seg[:120]}


def qualia_plan(word: str, definition=None, *, allow_identity: bool = True):
    """What a word's qualia ARE, in precedence order -- the one rule the
    offline index generator and the runtime grounding both apply:
      closed_class  (reading_constructions ClosedClass role)
      sense         (WordNet senses)
      function      (closed-class role by the function-word faculty)
      definition    (the held definition's genus senses)
      identity      (the honest degenerate quale; only if allow_identity)
    Returns {"via", "qualia": [(name, dimension, extra_attrs, sense_parents)]}
    or None."""
    roles = _closed_class().get(word)
    if roles:
        return {"via": "closed_class", "qualia": [
            ("closed_class:" + r, "closed_class", {}, []) for r in sorted(roles)]}
    from domains import wordnet_table as wt
    syns = sorted(set(wt.synsets(word))) if wt.available() else []
    if syns:
        return {"via": "sense", "qualia": [(s, "lexical:sense", {}, None) for s in syns]}
    role = function_role(word, definition)
    if role:
        return {"via": "function", "qualia": [("closed_class:" + role, "closed_class", {}, [])]}
    g = definition_genus(word, definition) if wt.available() else None
    if g:
        return {"via": "definition", "genus": g["genus"], "qualia": [(
            "definition:" + word, "lexical:definition", {"genus": g["genus"]}, g["senses"])]}
    if allow_identity:
        return {"via": "identity", "qualia": [("identity:" + word, "lexical:identity", {}, [])]}
    return None


def _link_plan(agent, concept, plan) -> list:
    """Install a qualia_plan on `concept`: reuse or mint each Quale (and the
    sense chain above it), link concept -has_quale-> quale, and increment
    `extent` exactly on the new closure. Returns the minted Quale nodes."""
    sub, native = _resolve(agent)
    minted: list = []
    heads = []
    for name, dim, extra, parents in plan["qualia"]:
        if dim == "lexical:sense":
            q = _ensure_sense(sub, native, name, minted)
        else:
            q = _quale(native, name)
            if q is None:
                attrs = {"name": name, "dimension": dim, "extent": 0}
                attrs.update(extra)
                q = sub.add_node("Quale", attrs)
                minted.append(q)
                for p in parents or []:
                    native.add_edge_unchecked(q, EDGE, _ensure_sense(sub, native, p, minted))
        heads.append(q)
    for q in heads:
        if not _has_edge(sub, concept, q):
            native.add_edge_unchecked(concept, EDGE, q)
    closure, stack = set(), list(heads)
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
    return minted


def ensure_qualia(agent, concept) -> bool:
    """The invariant "every held word links to one or more qualia" for a held
    Concept minted at runtime by a path that does not know about the index
    (teach_microtheory, dictionary ingest, learn_word, ...). Called at the
    mention I/O boundary for each referent; a no-op when the Concept already
    has qualia or its name is not a single word. Returns True iff it linked."""
    sub, native = _resolve(agent)
    try:
        if list(native.neighbours(concept, EDGE)):
            return False
        at = sub.node(concept)["attrs"]
    except Exception:  # noqa: BLE001
        return False
    word = at.get("name")
    if not isinstance(word, str) or not _WORD_RE.match(word):
        return False
    try:
        if not list(sub.nodes("QualiaIndex")):
            return False
    except Exception:  # noqa: BLE001
        return False
    plan = qualia_plan(word, at.get("definition"), allow_identity=True)
    if plan is None:
        return False
    _link_plan(agent, concept, plan)
    return True


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
    plan = qualia_plan(word, None, allow_identity=allow_identity)
    if plan is None:
        return None
    c = sub.add_node("Concept", {"name": word, "source": "lexical_qualia"})
    try:
        agent_node = getattr(agent, "agent", None)
        if agent_node is not None:
            native.add_edge_unchecked(agent_node, "knows_concept", c)
    except Exception:  # noqa: BLE001
        pass
    _link_plan(agent, c, plan)
    return c


__all__ = ["EDGE", "install_word_links", "ground_word", "held_qualia",
           "ensure_qualia", "qualia_plan", "definition_genus", "function_role"]
