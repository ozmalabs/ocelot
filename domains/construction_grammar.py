"""A GENERAL construction-application engine (construction grammar).

A construction is graph DATA: a surface PATTERN (literal tokens + `{slots}`)
paired with a MEANING template that binds the captured slots. The matcher here
is GENERAL — it applies whichever constructions are seeded; it knows nothing
about the copula specifically. Teaching a new construction = adding data to
seeds/constructions.json, not writing code. The copula/equative family maps onto
the seeded `relation` communication concept (see seeds/constructions.json).

Faithful to CLAUDE.md: this is a mechanical pattern->frame translator (a thin
boundary parser the same kind the speech-act classifier is), driven entirely by
graph-resident construction DATA — no per-construction Python decision.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_SEED = Path(__file__).resolve().parent.parent / "seeds" / "constructions.json"


def load_constructions(path: Path = _SEED) -> list[dict]:
    try:
        return json.loads(Path(path).read_text()).get("constructions", [])
    except Exception:
        return []


def _tok(text: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z0-9?]+", text or "")]


def _match(pattern: list[str], toks: list[str]) -> Optional[dict]:
    """Match a pattern (literals + '{slot}') against tokens (case-insensitive on
    literals). A slot captures one-or-more tokens up to the next literal. Returns
    {slot: captured-surface} on a FULL match, else None."""
    binds: dict[str, str] = {}
    i = 0
    for j, pt in enumerate(pattern):
        is_slot = pt.startswith("{") and pt.endswith("}")
        if is_slot:
            slot = pt[1:-1]
            nxt = None
            for k in range(j + 1, len(pattern)):
                if not (pattern[k].startswith("{") and pattern[k].endswith("}")):
                    nxt = pattern[k].lower()
                    break
            cap: list[str] = []
            while i < len(toks) and (nxt is None or toks[i].lower() != nxt):
                cap.append(toks[i])
                i += 1
            if not cap:
                return None
            binds[slot] = " ".join(cap)
        else:
            if i >= len(toks) or toks[i].lower() != pt.lower():
                return None
            i += 1
    if i != len(toks):
        return None
    return binds


def _fill(template: Any, binds: dict[str, str]) -> Any:
    if isinstance(template, str):
        m = re.fullmatch(r"\{(\w+)\}", template)
        return binds.get(m.group(1), template) if m else template
    if isinstance(template, dict):
        return {k: _fill(v, binds) for k, v in template.items()}
    if isinstance(template, list):
        # a coordination meaning fills to a LIST of frames (multiple facts).
        return [_fill(x, binds) for x in template]
    return template


# ---------------------------------------------------------------------------
# THE UNIVERSAL DEFINITION STRUCTURE — genus-differentia (Aristotle).
#
# ONE general parse, driven by the genus-differentia STRUCTURE the agent HOLDS
# as graph data (the `definition` communication-concept's `structure` attr —
# seeds/communication_concepts.json). It is NOT a list of surface forms: it
# realizes the held structure (a definition = FRAME? REGISTER? COPULA TERM, then
# a GENUS noun phrase up to a DIFFERENTIA marker) over ANY definitional sentence.
# The leading FRAME ('In <field>,') + REGISTER ('roughly speaking,'/'formally,')
# adjuncts are COMPREHENDED into {frame, register} — NOTHING is stripped: every
# part of the definition carries meaning (the frame = which Mt to ground in; the
# register = the epistemic-confidence band). A sentence with no extractable genus
# (no copula / a pronoun-only predicate) returns None — the honest remaining
# limit, not a faked parse.
#
# This is the permitted thin BOUNDARY parse (CLAUDE.md: a mechanical surface-
# structure translator, the same kind as the speech-act classifier): no
# per-concept decision, no LLM, no reasoning — it applies the one held structure.
# ---------------------------------------------------------------------------

# The genus-differentia structure as data, MIRRORING the seeded `definition`
# concept's `structure` (seeds/communication_concepts.json). load_definition_
# structure() reads the held graph version when a substrate is available; this
# is the fallback so the parse works in a bare world adapter too.
_DEFN_STRUCTURE: dict = {
    "copula": ["is", "are", "is defined as", "is called", "refers to", "means"],
    "article": ["a", "an", "the", "this", "that", "these", "those"],
    "pronoun_predicate": ["it", "this", "that", "these", "those", "they",
                          "them", "one", "something", "anything", "he", "she",
                          "i", "you", "we"],
    # The two leading-adjunct families. NOTHING is stripped: a FRAME adjunct
    # ('in <field>') is comprehended into frame=<field> (which Mt to ground in);
    # a REGISTER adjunct (hedge / exactness word) into register=approximate|exact
    # (the epistemic-confidence band). frame_phrase_skip are filler words inside
    # 'in the field of <field>' the frame extractor drops to reach the field head.
    "frame_markers": ["in", "within"],
    "frame_phrase_skip": ["the", "field", "of", "domain", "area", "context",
                          "study", "branch", "discipline", "subject"],
    "register_markers": {
        "roughly": "approximate", "informally": "approximate",
        "loosely": "approximate", "broadly": "approximate",
        "generally": "approximate", "intuitively": "approximate",
        "essentially": "approximate", "basically": "approximate",
        "simply": "approximate", "speaking": "approximate",
        "formally": "exact", "precisely": "exact", "technically": "exact",
        "strictly": "exact", "rigorously": "exact", "exactly": "exact"},
    "differentia_markers": ["that", "which", "who", "whom", "whose", "where",
                            "when", "used", "with", "for", "of", "in", "on",
                            "from", "to", "having", "containing", "consisting",
                            "characterized", "characterised", "defined",
                            "similar", "such", "whereby", "given", "about",
                            "concerned", "related", "called", "denoted",
                            "satisfying", "equipped", "endowed", "together",
                            "between", "among", "over", "under", "above",
                            "below"],
    "adjective_stop": [","],
    # ---- RESEARCH REGISTER (the dense "Let X be Y. A Z is a W ..." prose) ----
    # A PREAMBLE is the research-prose CONTEXT-SETTER: a leading "Let X be Y" /
    # "Given a W" / "Suppose ..." / "Fix ..." / "Consider ..." sentence (or
    # leading comma-clause) that BINDS objects for the definition to range over —
    # it is NOT the definition of the TERM. Comprehend it (the bindings ARE
    # context, not stripped) then look PAST it for the sentence that defines the
    # headword. preamble_markers lead such a clause/sentence; preamble_copula is
    # the binding copula inside it ('let X BE a ring' -> bind X is-a ring). The
    # connective_skip words ('then'/'thus'/'so'/'hence') lead the term definition
    # AFTER the preamble ('Fix C. THEN a poset is ...') — skipped to reach the term.
    "preamble_markers": ["let", "given", "suppose", "fix", "consider", "assume",
                         "take", "write", "denote"],
    "preamble_copula": ["be", "is", "are", "to be"],
    "connective_skip": ["then", "thus", "so", "hence", "therefore", "now"],
    # CONSTRUCTIVE / STRUCTURED definition forms (the research register's
    # non-copular definitions): "a <term> CONSISTS OF <parts>", "a <term> is a
    # <genus> TOGETHER WITH <structure>", "a <term> is a <genus> EQUIPPED WITH
    # ...". The constructive copula introduces the genus the same way 'is' does;
    # the parts/structure tail is the (constructive) differentia, kept not lost.
    "constructive_copula": ["consists of", "consist of", "is given by",
                            "is defined to be", "is defined as"],
    "constructive_markers": ["together", "equipped", "endowed", "consisting",
                             "comprising", "comprised", "consists", "with"],
    # A PARTITIVE HEDGE noun head ('a kind/sort/type of X'): genus = X (head PAST
    # the partitive) AND register = approximate (the partitive is a hedge).
    "partitive_hedges": {
        "kind": "approximate", "sort": "approximate", "type": "approximate",
        "form": "approximate", "variety": "approximate", "class": "approximate",
        "species": "approximate", "flavor": "approximate",
        "flavour": "approximate"},
    # The GENERATIVE MODEL: which slots are EXPECTED + how absence/difference
    # reads (mirrors the seed; absence/difference = SIGNAL, not a null).
    "expected_slots": {
        "frame": {"expected": True, "absent_means": "inherited",
                  "different_means": "sense_shift"},
        "register": {"expected": True, "absent_means": "canonical",
                     "hedge_means": "hedged"},
        "genus": {"expected": True, "different_means": "surprise"}},
    # register-class -> {status, confidence}. The UNMARKED case is 'canonical'.
    "register_band": {
        "canonical": {"status": "canonical", "confidence": 1.0},
        "exact": {"status": "exact", "confidence": 1.0},
        "technical": {"status": "exact", "confidence": 1.0},
        "approximate": {"status": "hedged", "confidence": 0.85},
        "informal": {"status": "hedged", "confidence": 0.8}},
    # marker word -> register CLASS (band key).
    "register_class": {
        "roughly": "approximate", "loosely": "approximate",
        "broadly": "approximate", "generally": "approximate",
        "essentially": "approximate", "basically": "approximate",
        "simply": "approximate", "speaking": "approximate",
        "informally": "informal", "intuitively": "informal",
        "formally": "exact", "precisely": "exact", "technically": "technical",
        "strictly": "exact", "rigorously": "exact", "exactly": "exact"},
    "domain_mt_map": {
        "math": "mathematics", "maths": "mathematics", "geometry": "mathematics",
        "topology": "mathematics", "algebra": "mathematics",
        "arithmetic": "mathematics", "calculus": "mathematics",
        "physics": "physics", "mechanics": "physics", "chemistry": "chemistry",
        "biology": "biology", "computing": "computer_science",
        "cs": "computer_science", "music": "music", "linguistics": "language",
        "grammar": "language"},
}


# ACQUIRED DEFINITIONAL CONSTRUCTIONS — research-register definitional
# construction-SHAPES the agent ACQUIRES (cmsg81) when its single-pass reader + the
# detect+brute-force keep FAILING on a recurring construction-TYPE its held
# genus-differentia structure does not recognise. The dominant un-cracked residual
# of cmsg80 is the PREDICATIVE / CONDITIONAL definition ('We say X is P if Q', 'We
# call X a P if Q') — a property-definition gated by a condition, the hallmark of
# research math. The held structure lacks (a) the 'we say / we call' definitional
# OPENER (so the whole 'we say X' became the term), and (b) the conditional
# TERMINATOR 'if / iff' that bounds the property-genus P (so the 'if Q' tail dragged
# into the genus). The agent ACQUIRES the construction by reading HOW it is written
# (its meta-description) OR abstracting the recurring shape from its failure-
# instances, minting the new markers as GRAPH DATA here. load_definition_structure
# MERGES them so extract_definition — and therefore the brute-force's
# comprehend_part — recognise the construction. The SAME merge pattern as _ACQUIRED
# for load_math_prose. Each acquired shape WIDENS what the brute force can crack
# (the meta-ability compounds).
_ACQUIRED_DEFN: dict = {
    # definitional OPENERS to SKIP past (a 'we say / we call' discourse-frame that
    # introduces the definiendum but is not itself part of the term). Merged into
    # the preamble-handling so the reader reaches the actual term.
    "definitional_openers": [],
    # additional COPULA surface forms the construction uses ('is said to be').
    "extra_copula": [],
    # additional DIFFERENTIA TERMINATORS that bound the genus (the property P) —
    # 'if'/'iff'/'whenever' end the property and begin the gating condition Q.
    "extra_differentia": [],
}


def _merge_acquired_defn(base: dict) -> dict:
    """MERGE the acquired definitional construction-shapes into a definition
    structure (the agent extends what its definition reader recognises by
    ACQUIRING new construction-types — graph data appended to _ACQUIRED_DEFN).
    Returns a NEW dict so the seed/base is not mutated. The SAME merge pattern
    load_math_prose uses for _ACQUIRED."""
    openers = _ACQUIRED_DEFN.get("definitional_openers", [])
    extra_cop = _ACQUIRED_DEFN.get("extra_copula", [])
    extra_diff = _ACQUIRED_DEFN.get("extra_differentia", [])
    if not (openers or extra_cop or extra_diff):
        return base
    s = dict(base)
    if openers:
        # a definitional opener ('we say', 'we call') is a discourse FRAME that
        # introduces the definiendum but is not part of the term — it is STRIPPED to
        # reach the actual term. Carried as graph data; extract_definition strips a
        # leading opener phrase before parsing (the SAME spirit as connective_skip,
        # one register wider — a multi-word opener phrase, not a single connective).
        s["definitional_openers"] = list(openers)
    if extra_cop:
        cop = list(s.get("copula", _DEFN_STRUCTURE["copula"]))
        for c in extra_cop:
            if c not in cop:
                cop = cop + [c]
        s["copula"] = cop
    if extra_diff:
        diff = list(s.get("differentia_markers",
                          _DEFN_STRUCTURE["differentia_markers"]))
        for d in extra_diff:
            if d not in diff:
                diff = diff + [d]
        s["differentia_markers"] = diff
    return s


def load_definition_structure(substrate=None) -> dict:
    """Return the genus-differentia STRUCTURE the agent HOLDS. Reads the
    `definition` Concept's `structure` attr from the graph when a substrate is
    given (the held understanding drives the application); else the in-module
    mirror of the seed. The ACQUIRED definitional construction-shapes
    (_ACQUIRED_DEFN — research-register construction-types the agent read/abstracted)
    are MERGED in so extract_definition recognises them. A pure graph/data read +
    the acquired-shape merge — no decision."""
    base = _DEFN_STRUCTURE
    if substrate is not None:
        try:
            for cid in substrate.nodes("Concept"):
                a = substrate.node(cid)["attrs"]
                if a.get("name") == "definition" and a.get("structure"):
                    s = json.loads(a["structure"])
                    if isinstance(s, dict) and s.get("differentia_markers"):
                        base = s
                        break
        except Exception:
            pass
    return _merge_acquired_defn(base)


def _parse_adjuncts(toks: list[str], copula: list[str],
                    frame_markers: set[str], frame_skip: set[str],
                    register_class: dict[str, str]
                    ) -> tuple[list[str], Optional[str], Optional[str]]:
    """COMPREHEND the leading adjuncts into structure — NOTHING is stripped /
    discarded. A leading comma-delimited segment that does not itself contain the
    copula is an adjunct the agent comprehends:

      · a FRAME adjunct (FIRST token a frame marker 'in'/'within',
        e.g. 'In mathematics,' / 'In the field of music,') -> frame=<field>:
        WHICH WORLD/MICROTHEORY the concept is grounded in (grounding is
        frame-relative — the frame says WHERE to ground). The field is the
        segment after the marker with the frame_skip filler words ('the field
        of') dropped.
      · a REGISTER adjunct (FIRST token a register marker 'roughly'/'formally'/…)
        -> a register CLASS ('approximate'/'informal'/'exact'/'technical'): HOW
        PRECISE/CONFIDENT the definition is (the epistemic-confidence band). A
        hedge lowers confidence; an exactness marker is full confidence.

    Returns (remaining tokens, frame, register_class). frame/register are None
    when no such adjunct is present (the unmarked case the caller reads as
    CANONICAL). Driven by the held markers — general, not a per-phrase list."""
    frame: Optional[str] = None
    register: Optional[str] = None
    cset = {c.split()[0] for c in copula}
    while True:
        try:
            comma = toks.index(",")
        except ValueError:
            break
        seg = toks[:comma]
        if not seg:
            toks = toks[comma + 1:]
            continue
        low = [t.lower() for t in seg]
        # an adjunct must not itself carry the copula (else it is the predicate).
        if any(w in cset for w in low):
            break
        first = low[0]
        if first in frame_markers:
            # FRAME adjunct: the field is what follows the marker, with the
            # 'the field of' / 'the domain of' filler words dropped.
            field_toks = [t for t in seg[1:] if t.lower() not in frame_skip]
            if field_toks:
                frame = " ".join(field_toks).strip()
                toks = toks[comma + 1:]
                continue
            break
        if first in register_class:
            # REGISTER adjunct: the epistemic band CLASS. The marker word carries
            # it ('roughly speaking' -> approximate via 'roughly').
            register = register_class[first]
            toks = toks[comma + 1:]
            continue
        break
    return toks, frame, register


# ---------------------------------------------------------------------------
# RESEARCH-REGISTER PREAMBLE — "Let X be Y. A Z is a W ..." prose.
#
# A PREAMBLE is the leading CONTEXT-SETTER of a research definition: "Let X be
# Y", "Given a W", "Suppose ...", "Fix ...", "Consider ..." — a clause/sentence
# that BINDS the objects the definition ranges over but is NOT itself the
# definition of the TERM. The genus-differentia grammar, finding the FIRST
# copula, mistook the preamble's predicate for the genus ('Let A be an abelian
# category. A spectral sequence is ...' -> grabbed 'abelian category'). The fix:
# COMPREHEND the preamble into BINDINGS (X is-a Y — context, not stripped), then
# look PAST it for the sentence that defines the headword term. The markers are
# graph DATA on the held `definition` structure (preamble_markers / _copula);
# this is the same thin boundary parse as the frame/register adjunct, one
# register deeper (a full clause/sentence, not a single adverbial).
# ---------------------------------------------------------------------------

_SENT_SPLIT = re.compile(r"(?<=[.;])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split a definition into sentences on '. ' / '; ' (the research-register
    'Let ... . A <term> is ... .' has the preamble as its own sentence). Keeps
    each sentence's surface; empties dropped."""
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s.strip()]


def _parse_preamble_clause(toks: list[str], preamble_markers: set[str],
                           preamble_copula: list[str], articles: set[str],
                           connective_skip: set[str]
                           ) -> tuple[list[str], list[dict]]:
    """COMPREHEND + SKIP a leading PREAMBLE clause/sentence within a token list,
    returning (remaining tokens, bindings). A preamble is a leading segment whose
    FIRST token is a preamble marker (let/given/suppose/fix/consider/...). It is
    consumed up to its clause boundary — the first comma at top level for a
    leading 'Given X,' clause, or the whole sentence for 'Let X be Y'. Each
    'Let/Given <subject> [be] <kind>' yields a BINDING {var, kind} (the context
    the definition ranges over — comprehended, NOT discarded). A leading
    connective ('Then'/'Thus') after the preamble is also skipped so the genus
    extractor reaches the term. Returns the tokens AFTER the preamble (+ any
    leading connective) and the list of bindings (possibly empty)."""
    bindings: list[dict] = []
    changed = True
    # iterate: a definition may stack several preambles ('Let R be a ring. Let M
    # be an R-module. ...') — each is bound + skipped in turn.
    while changed and toks:
        changed = False
        low = [t.lower() for t in toks]
        if low[0] not in preamble_markers:
            break
        # find this preamble's boundary: a top-level comma (for 'Given X, ...')
        # bounds a leading clause; absent a comma the preamble IS the sentence
        # (the sentence-splitter already isolated it) -> consume all of it.
        try:
            comma = low.index(",")
        except ValueError:
            comma = None
        seg = toks[1:comma] if comma is not None else toks[1:]
        # COMPREHEND the binding: '<subject> [be/is/are] <kind>' -> {var, kind}.
        # Split on the binding copula; left = the bound variable surface, right =
        # the kind it ranges over (with a leading article dropped).
        seg_low = [t.lower() for t in seg]
        cop_at = None
        for ci, w in enumerate(seg_low):
            if w in preamble_copula:
                cop_at = ci
                break
        if cop_at is not None:
            # 'Let X be a ring' / 'Suppose X is a group' -> {var:X, kind:ring}.
            var = " ".join(seg[:cop_at]).strip(" ,")
            kind_toks = seg[cop_at + 1:]
            if kind_toks and kind_toks[0].lower() in articles:
                kind_toks = kind_toks[1:]
            kind = " ".join(t for t in kind_toks if t != ",").strip()
            if kind:
                bindings.append({"var": var or None, "kind": kind})
        elif seg and seg[0].lower() in articles:
            # 'Given a 2-ring R' (no explicit copula) -> the introduced object IS
            # of the named kind (the article-led phrase, article dropped). Context
            # captured (var unknown without a copula) rather than discarded.
            kind = " ".join(t for t in seg[1:] if t != ",").strip()
            if kind:
                bindings.append({"var": None, "kind": kind})
        # consume the preamble.
        toks = toks[comma + 1:] if comma is not None else []
        changed = True
        # skip a leading connective ('Then'/'Thus'/'so') + a following article so
        # the term definition head is reached ('Then a poset is ...').
        while toks and toks[0].lower() in connective_skip:
            toks = toks[1:]
    return toks, bindings


def _defines_term(toks: list[str], headword: str, copula: list[str],
                  articles: set[str]) -> bool:
    """True iff a sentence's token list DEFINES the headword term: it contains a
    copula AND its subject (the tokens before the first copula, minus a leading
    article) mentions the headword. Used to PREFER the sentence about the TERM
    over a preamble's binding sentence ('Let R be a ring' does NOT define
    'module'; 'A module is finite type ...' does)."""
    if not headword:
        return False
    span = _find_copula(toks, copula)
    if span is None:
        return False
    subj = " ".join(t for t in toks[:span[0]] if t != ",").lower()
    hw = headword.replace("_", " ").lower().strip()
    head = hw.split()[-1] if hw else ""
    return bool((hw and hw in subj) or (head and head in subj))


def _find_copula(toks: list[str], copula: list[str]) -> Optional[tuple[int, int]]:
    """Find the FIRST copula in the token stream. Supports multi-word copulas
    ('is defined as', 'refers to'). Returns (start_index, end_index_exclusive)
    of the copula span, or None (no copula -> not a definitional sentence)."""
    low = [t.lower() for t in toks]
    # longest copulas first so 'is defined as' wins over 'is'.
    for cop in sorted(copula, key=lambda c: -len(c.split())):
        parts = cop.split()
        n = len(parts)
        for i in range(len(low) - n + 1):
            if low[i:i + n] == parts:
                return (i, i + n)
    return None


def extract_definition(text: str, *, substrate=None,
                       structure: Optional[dict] = None,
                       term: Optional[str] = None) -> Optional[dict]:
    """THE ONE general genus-extraction — realize the held genus-differentia
    STRUCTURE over ANY definitional sentence.

    RESEARCH REGISTER (the dense "Let X be Y. A Z is a W ..." prose): a leading
    PREAMBLE ("Let X be Y" / "Given a W" / "Suppose ..." / "Fix ..." / a leading
    "Given X," clause / a "Then ..." connective after it) BINDS context and is
    NOT the definition of the TERM. It is COMPREHENDED into `bindings` (X is-a Y
    — context, never stripped) and SKIPPED; the genus is then extracted from the
    sentence that DEFINES the headword (`term`, the page title, when supplied —
    else the first non-preamble copula sentence). This is what stops the grammar
    grabbing the preamble's genus ('Let A be an abelian category. A spectral
    sequence is ...' -> binds A is-a abelian_category, extracts genus from the
    spectral-sequence sentence). The CONSTRUCTIVE forms ('consists of <parts>',
    'is a <genus> together with <structure>') are read like the copula — the
    genus extracted, the parts/structure kept as constructive differentia.

    COMPREHEND AGAINST EXPECTATIONS (the entity part). A competent reader holds a
    generative MODEL of a definition (expects FRAME, REGISTER, TERM is-a GENUS,
    DIFFERENTIA) and reads each slot PRESENT | ABSENT | DIFFERENT — absence and
    difference are SIGNAL (prediction-error = information), not a null default:
      · REGISTER ABSENT (unmarked) = the CANONICAL, asserted-as-fact case ->
        register 'canonical', status 'canonical', FULL confidence (a comprehended
        signal 'stated as definitional truth', not a missing value).
      · REGISTER a hedge ('roughly'/'loosely'/'informally', OR the partitive
        'a kind/sort/type of') = a DEVIATION -> register 'approximate'/'informal',
        status 'hedged', LOWER confidence.
      · FRAME ABSENT = inherited from the active discourse frame / universal.
      · GENUS is read as the HEAD past a PARTITIVE hedge ('a kind of X' -> X).

    Find the COPULA -> the term precedes it -> the GENUS NP follows: skip an
    inline adverbial / article, take the head noun phrase up to a DIFFERENTIA
    marker. Inline / post-copula register markers ('X is, roughly speaking, a Y',
    'X is informally a Y') are COMPREHENDED (scanned inside the predicate too,
    not only leading). Returns {term, genus, differentia, frame, register,
    register_status, confidence, signals, slots} — or None when there is no
    extractable genus (no copula / a pronoun-only predicate).

    `signals` / `slots` carry the present|absent|different STATUS per slot (the
    entity reading): the caller's grounding consumes them (sense-shift on a
    different frame; surprise on a different genus; canonical-vs-hedged confidence
    from the register). Driven by the ONE held structure (read from the
    `definition` concept), generalising across surface forms — NOT a per-form
    pattern."""
    if not text:
        return None
    st = structure or load_definition_structure(substrate)
    copula = st.get("copula", _DEFN_STRUCTURE["copula"])
    articles = set(st.get("article", _DEFN_STRUCTURE["article"]))
    frame_markers = set(st.get("frame_markers",
                               _DEFN_STRUCTURE["frame_markers"]))
    frame_skip = set(st.get("frame_phrase_skip",
                            _DEFN_STRUCTURE["frame_phrase_skip"]))
    # register_class: marker word -> register CLASS (band key). Back-compat: a
    # held structure may still only carry the older register_markers
    # (word -> 'approximate'|'exact'); fall through to the fallback class map.
    register_class = st.get("register_class")
    if not isinstance(register_class, dict):
        register_class = _DEFN_STRUCTURE["register_class"]
    register_band = st.get("register_band", _DEFN_STRUCTURE["register_band"])
    if not isinstance(register_band, dict):
        register_band = _DEFN_STRUCTURE["register_band"]
    partitive = st.get("partitive_hedges", _DEFN_STRUCTURE["partitive_hedges"])
    if not isinstance(partitive, dict):
        partitive = _DEFN_STRUCTURE["partitive_hedges"]
    diff_markers = set(st.get("differentia_markers",
                              _DEFN_STRUCTURE["differentia_markers"]))
    pronouns = set(st.get("pronoun_predicate",
                          _DEFN_STRUCTURE["pronoun_predicate"]))
    # research-register markers (graph data; back-compat fallbacks for an older
    # held structure that predates the research register).
    preamble_markers = set(st.get("preamble_markers",
                                  _DEFN_STRUCTURE["preamble_markers"]))
    preamble_copula = st.get("preamble_copula",
                             _DEFN_STRUCTURE["preamble_copula"])
    connective_skip = set(st.get("connective_skip",
                                 _DEFN_STRUCTURE["connective_skip"]))
    # ACQUIRED definitional OPENERS ('we say', 'we call') — a discourse frame that
    # introduces the definiendum; stripped to reach the term. Empty unless acquired.
    definitional_openers = [op.lower().split()
                            for op in st.get("definitional_openers", [])]
    constructive_copula = st.get("constructive_copula",
                                 _DEFN_STRUCTURE["constructive_copula"])
    # the genus-introducing copulas = the plain copula + the CONSTRUCTIVE ones
    # ('consists of', 'is given by') — both introduce the genus the same way.
    gen_copula = list(copula) + [c for c in constructive_copula
                                 if c not in copula]

    # RESEARCH-REGISTER PREAMBLE handling (the live fix). Split the definition
    # into sentences; COMPREHEND + SKIP any leading preamble sentence(s) ('Let X
    # be Y') into BINDINGS, and PREFER the sentence that DEFINES the headword
    # term over the preamble's binding sentence. NOTHING is stripped — the
    # bindings are returned as context. Falls through unchanged for a plain
    # one-sentence definition (no preamble marker -> bindings empty, same text).
    bindings: list[dict] = []
    preamble_seen = False
    sentences = _split_sentences(text)
    if len(sentences) > 1:
        # comprehend leading whole-sentence preambles into bindings + drop them,
        # keeping the remaining (definition-bearing) sentences.
        kept: list[str] = []
        for si, sent in enumerate(sentences):
            stoks = re.findall(r"[A-Za-z0-9'-]+|,", sent)
            slow = [t.lower() for t in stoks]
            is_pre = bool(slow) and slow[0] in preamble_markers
            # a preamble sentence that ALSO defines the headword is kept (rare:
            # 'Let X be the smallest ...' naming the term) — only skip it when it
            # does NOT define the term.
            if is_pre and not _defines_term(stoks, term or "", gen_copula,
                                            articles):
                _, b = _parse_preamble_clause(stoks, preamble_markers,
                                              preamble_copula, articles,
                                              connective_skip)
                bindings.extend(b)
                preamble_seen = True
                continue
            kept.append(sent)
        # CHOOSE the working sentence: PREFER one whose subject mentions the
        # headword term (the definition OF the term); else the FIRST kept
        # copula sentence; else the first kept sentence.
        chosen = None
        if term:
            for sent in kept:
                stoks = re.findall(r"[A-Za-z0-9'-]+|,", sent)
                if _defines_term(stoks, term, gen_copula, articles):
                    chosen = sent
                    break
        # an ACQUIRED definitional OPENER sentence ('We say X is P if Q') IS the
        # definition of the term — PREFER it over an earlier preamble/constructive
        # copula sentence (the predicative-definition construction the agent
        # acquired). Empty unless a definitional opener was acquired.
        if chosen is None and definitional_openers:
            for sent in kept:
                slow = [t.lower() for t in re.findall(r"[A-Za-z0-9'-]+", sent)]
                if any(slow[:len(op)] == op for op in definitional_openers):
                    chosen = sent
                    break
        if chosen is None:
            for sent in kept:
                stoks = re.findall(r"[A-Za-z0-9'-]+|,", sent)
                if _find_copula(stoks, gen_copula) is not None:
                    chosen = sent
                    break
        if chosen is None and kept:
            chosen = kept[0]
        if chosen is not None:
            text = chosen

    # tokenise keeping commas (they bound the leading adjuncts + adjective runs).
    # Underscore is kept INSIDE a token: an underscore-joined name
    # ('body_of_water', 'physical_entity') is a single LEXICAL UNIT (the WordNet
    # lemma / seeded-concept convention), not a genus head + 'of'-differentia to
    # split. This matches the acquired-construction tokenizer (which already
    # keeps '_'); the genus extractor was the inconsistent path.
    toks = re.findall(r"[A-Za-z0-9'_-]+|,", (text or "").strip())
    if not toks:
        return None

    # ACQUIRED DEFINITIONAL OPENER ('We say', 'We call', 'We say that') — a
    # discourse frame that introduces the definiendum but is NOT part of the term.
    # STRIP a matching leading opener phrase (+ a trailing 'that'/'an'/'a' the
    # opener carries) so the reader reaches the actual term. This is the
    # construction-shape the agent ACQUIRED (cmsg81); empty unless acquired.
    def _strip_opener(tk):
        if not definitional_openers:
            return tk, False
        # the opener may sit after a leading comma-bounded adjunct that carries no
        # copula ('For 0 <= ell <= infinity, we say X is P ...') — if so, drop that
        # leading segment first so the opener is reached (NOTHING definitional is
        # dropped: the segment has no copula, it is a quantifier-range adjunct).
        cand = tk
        if "," in [t.lower() for t in tk]:
            comma = [t.lower() for t in tk].index(",")
            seg = [t.lower() for t in tk[:comma]]
            cset = {c.split()[0] for c in gen_copula}
            after = tk[comma + 1:]
            if (after and not any(w in cset for w in seg)
                    and after[0].lower() in {o[0] for o in
                                             definitional_openers if o}):
                cand = after
        low_t = [t.lower() for t in cand]
        for opener in sorted(definitional_openers, key=lambda o: -len(o)):
            n = len(opener)
            if n and low_t[:n] == opener:
                cand = cand[n:]
                if cand and cand[0].lower() == "that":   # 'we say THAT X is'
                    cand = cand[1:]
                return cand, True
        return tk, False
    toks, _opened = _strip_opener(toks)
    if _opened:
        preamble_seen = True

    # A leading CONNECTIVE on the working sentence ('Then a poset is ...', 'Thus
    # its objects are ...') — strip it so the term definition head is reached. A
    # definitional sentence never legitimately opens with a discourse connective
    # ('then'/'thus'/'hence'/...): it is the tail of a preamble whose context-
    # setting sentence preceded it (often already dropped by the corpus reader).
    # Bounded: a leading run of held connective words, then stop. Flags the
    # preamble (the connective marks one was present) so the bound-as-context
    # signal fires.
    if toks and toks[0].lower() in connective_skip:
        while toks and toks[0].lower() in connective_skip:
            toks = toks[1:]
        preamble_seen = True
    # A leading PREAMBLE CLAUSE within the working sentence ('Given a 2-ring, a
    # 2-line over R is ...'): comprehend it into bindings + skip to the term
    # definition. Runs on the chosen sentence so a one-sentence 'Given X, a
    # <term> is ...' is also handled.
    if toks and toks[0].lower() in preamble_markers:
        preamble_seen = True
    toks, clause_binds = _parse_preamble_clause(
        toks, preamble_markers, preamble_copula, articles, connective_skip)
    bindings.extend(clause_binds)
    if not toks:
        return None

    # COMPREHEND the leading frame + register adjuncts (NOTHING stripped). The
    # leading register is a CLASS ('approximate'/'informal'/'exact'/'technical').
    toks, frame, register = _parse_adjuncts(
        toks, gen_copula, frame_markers, frame_skip, register_class)
    # a definitional opener can sit AFTER a leading 'For ...,' adjunct/preamble that
    # the steps above consumed ('For 0 <= ell <= infinity, we say X is P if Q') —
    # strip it again now that the leading clause is gone (the acquired construction).
    toks, _opened2 = _strip_opener(toks)
    if _opened2:
        preamble_seen = True
    span = _find_copula(toks, gen_copula)
    if span is None:
        return None  # no copula -> not a definitional sentence (honest None).
    ci, cj = span

    # TERM = the subject before the copula, minus a leading article. A pronoun-
    # only predicate (the GENUS side) is handled below; an empty term is honest
    # un-comprehension.
    term_toks = [t for t in toks[:ci] if t != ","]
    if term_toks and term_toks[0].lower() in articles:
        term_toks = term_toks[1:]
    term = " ".join(term_toks).strip()
    if not term:
        return None

    # PREDICATE = everything after the copula.
    pred = toks[cj:]
    # COMPREHEND an inline / post-copula adverbial register marker ('is, roughly
    # speaking, a geometrical space'): the comma-delimited segment right after the
    # copula. NOTHING dropped — if the segment is a register marker, it is read
    # into `register` (the deviation), then the segment is consumed.
    if pred and pred[0] == ",":
        try:
            close = pred.index(",", 1)
            seg = [t for t in pred[1:close] if t != ","]
        except ValueError:
            close = None
            seg = [t for t in pred[1:] if t != ","]
        if seg and seg[0].lower() in register_class:
            register = register or register_class[seg[0].lower()]
        pred = pred[close + 1:] if close is not None else pred[1:]
    # drop a leading article.
    if pred and pred[0].lower() in articles:
        pred = pred[1:]
    # COMPREHEND a NON-comma inline register marker right after the copula/article
    # ('is informally a device', 'is roughly a device'): the marker word leads the
    # predicate, optionally followed by another article. Read it into `register`,
    # consume the marker (+ a following article), so the genus head is reached.
    if pred and pred[0].lower() in register_class:
        register = register or register_class[pred[0].lower()]
        pred = pred[1:]
        if pred and pred[0].lower() in articles:
            pred = pred[1:]
    # drop a leading comma-separated ADJECTIVE run ('a smooth, projective,
    # algebraic curve' -> the genus head is 'curve'): strip any (word ,)* prefix.
    while len(pred) >= 2 and pred[1] == ",":
        pred = pred[2:]

    # GENUS span = head noun phrase up to the first DIFFERENTIA marker / comma.
    genus_toks: list[str] = []
    diff_start = len(pred)
    for k, t in enumerate(pred):
        tl = t.lower()
        if t == "," or tl in diff_markers:
            diff_start = k
            break
        genus_toks.append(t)
    differentia = " ".join(t for t in pred[diff_start:] if t != ",").strip()

    # PARTITIVE HEDGE: 'a kind/sort/type of X' -> the genus is X (HEAD PAST the
    # partitive), and the partitive itself is a hedge (register approximate). The
    # genus head word is a partitive noun and the differentia tail begins 'of …':
    # comprehend the head of that 'of'-phrase as the real genus, NOTHING dropped.
    partitive_hedge = False
    if (genus_toks and genus_toks[-1].lower() in partitive
            and differentia.lower().startswith("of ")):
        partitive_marker = genus_toks[-1].lower()
        of_rest = differentia[3:].strip()
        of_toks = of_rest.split()
        # the real genus = the of-phrase head NP up to the next differentia marker.
        real_genus: list[str] = []
        rest_after: list[str] = []
        crossed = False
        for w in of_toks:
            if not crossed and w.lower() not in diff_markers:
                real_genus.append(w)
            else:
                crossed = True
                rest_after.append(w)
        if real_genus:
            genus_toks = real_genus
            differentia = " ".join(rest_after).strip()
            # the partitive itself is the hedge -> register approximate (its held
            # mapping); a leading register adjunct, if any, already stands.
            register = register or partitive.get(partitive_marker, "approximate")
            partitive_hedge = True

    genus = " ".join(genus_toks).strip()
    if not genus:
        return None  # empty predicate -> honest un-comprehension.
    # a PRONOUN-only predicate ('X is it / this / that') names no genus the agent
    # can ground out -> honest un-comprehension (the genuine remaining limit).
    if all(g.lower() in pronouns for g in genus_toks):
        return None

    # READ-AGAINST-EXPECTATIONS: resolve the register CLASS -> {status, confidence}
    # band. ABSENT register (unmarked) = the CANONICAL asserted-as-fact case (a
    # comprehended signal, FULL confidence), not a missing value.
    reg_class = register or "canonical"
    band = register_band.get(reg_class) or register_band.get("canonical") \
        or {"status": "canonical", "confidence": 1.0}
    register_status = band.get("status", "canonical")
    confidence = float(band.get("confidence", 1.0))

    # The present|absent|different SIGNALS per slot (the entity reading). frame
    # and genus DIFFERENCE are resolved by the GROUNDING (which holds the term's
    # existing frame/genus); here we surface the locally-readable status.
    signals: dict[str, Any] = {}
    slots: dict[str, str] = {}
    # register: present (marked) vs absent (canonical/unmarked).
    if register is None:
        slots["register"] = "absent"
        signals["register"] = "canonical"  # asserted-as-fact (comprehended).
    else:
        slots["register"] = "present"
        signals["register"] = "hedged" if register_status == "hedged" \
            else "marked_exact"
    if partitive_hedge:
        signals["partitive_hedge"] = True
    # frame: present vs absent (inherited). DIFFERENT (sense-shift) is decided at
    # GROUND time against the term's held frame; flagged present here.
    slots["frame"] = "present" if frame else "absent"
    if not frame:
        signals["frame"] = "inherited"
    # genus is always present here (None-genus returned above); SURPRISE
    # (different from the held genus) is decided at GROUND time.
    slots["genus"] = "present"

    # PREAMBLE BINDINGS (the research-register context) carried through — NOT
    # discarded. The bindings are the 'Let X be Y' objects the definition ranges
    # over (X is-a Y); the grounding can use them as context. A present-but-empty
    # list = no preamble (the canonical plain definition). `preamble` flags that a
    # preamble was comprehended-and-bound (the live fix fired).
    if preamble_seen or bindings:
        slots["preamble"] = "present"
        signals["preamble"] = "bound" if bindings else "skipped"
    return {"term": term, "genus": genus, "differentia": differentia,
            "frame": frame, "register": reg_class,
            "register_status": register_status, "confidence": confidence,
            "signals": signals, "slots": slots, "bindings": bindings}


def apply_constructions(text: str, constructions: list[dict],
                        language: str = "en") -> Optional[dict]:
    """Return the MEANING frame of the first construction whose pattern fully
    matches ``text`` (slots bound), or None. Pure data-driven translation."""
    toks = _tok(text.rstrip("?.!"))
    if not toks:
        return None
    for c in constructions:
        if c.get("language", "en") != language:
            continue
        binds = _match(c.get("pattern", []), toks)
        if binds is not None:
            filled = _fill(c.get("meaning", {}), binds)
            # restore the interrogative force the pattern dropped
            if text.rstrip().endswith("?"):
                for fr in (filled if isinstance(filled, list) else [filled]):
                    if isinstance(fr, dict):
                        fr.setdefault("speech_act", "question")
            return filled
    return None


# ---------------------------------------------------------------------------
# EXTRACT A FUNCTION FROM PROSE — the agent reads a mathematical definition in
# natural language and comprehends it into the FORMAL function form (in the index
# variable `n`) that compute_grounding then grounds. Two paths, both the agent's
# grammar over graph data:
#   (a) CLAUSE constructions (seeds/math_prose_constructions.json) — a math-prose
#       phrase found WITHIN the definition ("number of divisors of n") maps to a
#       formal form (count{k in 1..n : k|n}).
#   (b) EMBEDDED FORMULA — a definition often states "a(n) = <expr>"; each '='
#       RHS segment is a candidate arithmetic formula (n*(n+1)/2, 2n, n!).
# Returns a LIST of candidate formal RHS forms; the SOURCE's ground-truth values
# (OEIS) then VERIFY + SELECT the correct one — the agent cannot fake reproducing
# the real sequence. This is the permitted thin boundary parse (clause-match +
# arithmetic normalisation); the patterns are graph data, not per-sequence code.
# ---------------------------------------------------------------------------

_MATH_PROSE = Path(__file__).resolve().parent.parent / "seeds" / \
    "math_prose_constructions.json"
_FACT_HARVEST = Path(__file__).resolve().parent.parent / "seeds" / \
    "math_fact_harvest.json"

# ACQUIRED constructions — comprehension constructions the agent grounded by
# READING their meta-definition ('read about how to read'). They live alongside
# the seeded grammar; load_math_prose MERGES them in so comprehend_recursive
# composes them like any seeded construction. This is the acquire() target: a new
# reading-construction is graph DATA, appended here by acquire_construction.
_ACQUIRED: dict = {"value_maps": [], "filters": [], "member_forms": [],
                   "aggregators": [], "clauses": [], "notations": []}


def load_math_prose(path: Path = _MATH_PROSE) -> dict:
    try:
        g = json.loads(Path(path).read_text())
    except Exception:
        g = {"clauses": []}
    # MERGE the acquired constructions in (the agent extends what it can read by
    # READING how to read — acquire_construction appends here).
    for key, items in _ACQUIRED.items():
        if items:
            g.setdefault(key, [])
            g[key] = list(g[key]) + list(items)
    return g


def _normalize_formula(expr: str) -> str:
    """Normalise an embedded arithmetic formula (in n) toward the compute parser
    surface: n! -> factorial(n); implicit mult 2n -> 2*n; x^k (small int k) ->
    repeated mult (n^2 -> n*n)."""
    e = expr.strip().rstrip(".")
    e = re.sub(r"\bn\s*!", "factorial(n)", e)            # n! -> factorial(n)
    e = re.sub(r"(\d)\s*([a-z])", r"\1*\2", e)            # 2n -> 2*n
    e = re.sub(r"(\d)\s*\(", r"\1*(", e)                  # 2(  -> 2*(

    def _pow(m):
        base, k = m.group(1), int(m.group(2))
        return "*".join([base] * k) if 2 <= k <= 6 else m.group(0)
    e = re.sub(r"([a-z0-9]+)\s*\^\s*(\d+)", _pow, e)      # n^2 -> n*n
    return re.sub(r"\s+", " ", e).strip()


def extract_function(prose: str) -> list[str]:
    """EXTRACT candidate FORMAL function forms (in `n`) from a prose definition —
    the agent's math-prose grammar. Returns a list of candidate RHS strings (the
    SOURCE's values select the verified one). Empty list = the honest
    un-extractable case (no clause / formula matches).

    THREE paths (the SOURCE's ground-truth values SELECT the verified one):
      (a) FLAT CLAUSE constructions — a math-prose phrase matched as a WHOLE.
      (b) EMBEDDED FORMULA — each '=' RHS segment is a candidate arithmetic form.
      (c) ORDER-N (recursive) COMPOSITION — comprehend_recursive composes
          constructions whose SLOTS are themselves comprehended (sum/number OVER a
          value-map OVER a member-set UNDER a filter), bottoming out at a member-
          form bedrock. This catches the COMPOSITIONAL prose the flat (a) path
          returns NONE on ('sum of squares of divisors of n', 'sum of divisors of
          n that are less than n'). It runs LAST + appends — the flat matcher is
          SUBSUMED, not replaced."""
    if not prose:
        return []
    norm = re.sub(r"\s+", " ", prose.lower()).strip()
    cands: list[str] = []
    # (a) CLAUSE constructions — a math-prose phrase within the definition.
    for c in load_math_prose().get("clauses", []):
        if c.get("clause") and c["clause"] in norm:
            cands.append(c["formula"])
    # (b) EMBEDDED FORMULA — each '=' RHS segment is a candidate arithmetic form.
    for seg in re.split(r"(?<![=<>!])=(?!=)", prose)[1:]:
        m = re.match(r"\s*([0-9n!\^\*\+\-\/\(\)\s\.]+)", seg)
        if not m:
            continue
        raw = m.group(1).strip()
        if "..." in raw or not re.search(r"n|\d", raw):
            continue
        f = _normalize_formula(raw)
        if f and re.search(r"[+\-*/]|factorial|\bn\b", f):
            cands.append(f)
    # (c) ORDER-N (recursive) COMPOSITION — the agent's order-N operator over the
    # construction grammar (comprehend a slot by sub-constructions, recursively).
    for f in comprehend_recursive(prose):
        cands.append(f)
    seen: set = set()
    out: list[str] = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# ORDER-N (RECURSIVE) COMPREHENSION — the agent's order-N operator
# (order_n_composition.iterate_to_n) applied to the CONSTRUCTION GRAMMAR.
#
# The flat matcher above matches a WHOLE string -> NONE on anything compositional.
# Here a construction's SLOT content is itself parsed by (sub-)constructions,
# RECURSIVELY, bottoming out at a comprehension-BEDROCK: a MEMBER-FORM leaf (an
# atomic 'divisors of n' / 'integers'). The COMBINATION rule (iterate_to_n's step)
# is "fill a slot by comprehending its content"; the BEDROCK test is "is this a
# member-form leaf". order-N = the recursion depth (a value-map over a member-set
# under a filter inside an aggregator = several composition tiers).
#
# The intermediate STRUCTURE a sub-construction comprehends to is a MEMBER-FORM:
# {value, predicate} over the binder k in 1..n —
#   · value     — the expression to accumulate for member k (k; k*k for squares).
#   · predicate — a multiplicative 0/1 mask selecting which k are members
#                 (k|n for divisors; *(k<n) ANDed by a 'less than n' filter).
# An AGGREGATOR (sum / number) wraps a member-form into the runnable
#   sum{k in 1..n : value*predicate}
# form compute_grounding then grounds + evaluates. So order-N comprehension feeds
# the EXISTING order-N computation.
#
# Faithful: the constructions are graph DATA (seeds/math_prose_constructions.json
# member_forms / value_maps / filters / aggregators); the recursion is the agent's
# iterate_to_n shape; the verifier is the source's ground-truth values. No LLM, no
# per-form code. Greedy + depth-bounded + cycle-detected (the honest residual:
# ambiguity is resolved greedily, longest-pattern-first).
# ---------------------------------------------------------------------------

_MAX_COMPREHEND_DEPTH = 8


def _slot_fill(template: str, inner: dict) -> str:
    """Fill a formula/value/predicate template's {slot.value}/{slot.predicate}
    references from a comprehended sub-structure (a member-form). This is the
    COMBINATION rule's substitution: the slot's content, already comprehended into
    {value, predicate}, is spliced into the parent template."""
    out = template
    for role in ("value", "predicate"):
        out = out.replace("{set." + role + "}", str(inner.get(role, "")))
        out = out.replace("{inner." + role + "}", str(inner.get(role, "")))
    return out


def _comprehend_member_form(toks: list[str], grammar: dict, depth: int,
                            seen: frozenset) -> Optional[dict]:
    """Comprehend a token list into a MEMBER-FORM {value, predicate} — the SLOT
    content of an aggregator. This is the RECURSIVE descent (the agent's order-N
    step): try the COMPOSING constructions (value_maps, with a recursively
    comprehended {inner} slot; pre/post filters narrowing an inner member-form),
    then bottom out at a BEDROCK member-form leaf. Returns None when nothing
    comprehends (the honest un-comprehension)."""
    if depth > _MAX_COMPREHEND_DEPTH or not toks:
        return None
    key = (depth, tuple(toks))
    if key in seen:                              # cycle guard.
        return None
    seen = seen | {key}
    low = [t.lower() for t in toks]

    # PRE-modifier filter: 'odd divisors of n' -> mask (k%2) ANDed onto the inner
    # member-form's predicate. The filter's pattern leads; the remainder is the
    # inner member-form (comprehended recursively — the slot fill).
    for filt in grammar.get("filters", []):
        if filt.get("position") != "pre":
            continue
        pat = [p.lower() for p in filt["pattern"]]
        if low[:len(pat)] == pat and len(low) > len(pat):
            inner = _comprehend_member_form(toks[len(pat):], grammar,
                                            depth + 1, seen)
            if inner is not None:
                return {"value": inner["value"],
                        "predicate": f"({inner['predicate']})*({filt['mask']})",
                        "order": inner.get("order", 0) + 1}

    # POST-modifier filter: '[member-form] that are less than n' -> narrow the
    # inner member-form's predicate by the trailing mask. Try the LONGEST trailing
    # filter match first (greedy), recursively comprehending the head as the inner.
    for filt in sorted(grammar.get("filters", []),
                       key=lambda f: -len(f["pattern"])):
        if filt.get("position") == "pre":
            continue
        pat = [p.lower() for p in filt["pattern"]]
        n = len(pat)
        if n < len(low) and low[-n:] == pat:
            inner = _comprehend_member_form(toks[:-n], grammar, depth + 1, seen)
            if inner is not None:
                return {"value": inner["value"],
                        "predicate": f"({inner['predicate']})*({filt['mask']})",
                        "order": inner.get("order", 0) + 1}

    # VALUE-MAP construction: 'squares of [{inner}]' -> map the inner member-form's
    # value v -> v*v; the {inner} slot is comprehended RECURSIVELY (the order-N
    # step). Longest pattern prefix first.
    for vm in sorted(grammar.get("value_maps", []),
                     key=lambda v: -len([p for p in v["pattern"]
                                         if not (p.startswith("{"))])):
        bound = _match_with_slot(low, [p.lower() for p in vm["pattern"]])
        if bound is None:
            continue
        inner_toks = bound  # the {inner} slot surface tokens.
        inner = _comprehend_member_form(inner_toks, grammar, depth + 1, seen)
        if inner is None:
            continue
        return {"value": _slot_fill(vm["value"], inner),
                "predicate": _slot_fill(vm["predicate"], inner),
                "order": inner.get("order", 0) + 1}

    # BEDROCK: a member-form LEAF ('divisors of n' / 'the integers'). The recursion
    # bottoms out here — the comprehension-bedrock (an atomic held set-member form).
    for mf in sorted(grammar.get("member_forms", []),
                     key=lambda m: -len(m["pattern"])):
        if low == [p.lower() for p in mf["pattern"]]:
            return {"value": mf["value"], "predicate": mf["predicate"],
                    "order": 0}
    return None


def _match_with_slot(toks: list[str], pattern: list[str]) -> Optional[list[str]]:
    """Match a pattern with a SINGLE trailing/embedded `{slot}` against tokens,
    returning the slot's captured token list (lower-cased surface). Used by the
    value-map constructions ('squares of {inner}'). The slot captures the rest
    after the literal prefix up to any literal suffix."""
    pre = []
    slot_at = None
    for i, p in enumerate(pattern):
        if p.startswith("{") and p.endswith("}"):
            slot_at = i
            break
        pre.append(p)
    if slot_at is None:
        return None
    suf = pattern[slot_at + 1:]
    if toks[:len(pre)] != pre:
        return None
    rest = toks[len(pre):]
    if suf:
        if rest[-len(suf):] != suf:
            return None
        rest = rest[:-len(suf)]
    return rest if rest else None


def comprehend_recursive(prose: str) -> list[str]:
    """ORDER-N comprehension: comprehend a COMPOSITIONAL math-prose form by
    RECURSIVELY composing constructions (the agent's iterate_to_n over the
    construction grammar). Returns a list of runnable formula candidates (in `n`)
    — the AGGREGATOR (sum/number) wrapping a recursively-comprehended member-form.
    Empty list = the form is not compositionally comprehensible (the honest
    residual — the recursion did not bottom out at member-form bedrock).

    The COMBINATION rule = 'fill a slot by comprehending its content'; the BEDROCK
    = a member-form leaf; the ORDER = the recursion depth. A FLAT clause that
    matched the whole string still wins via extract_function's path (a); this adds
    the compositional forms it returned NONE on."""
    if not prose:
        return []
    grammar = load_math_prose()
    norm = re.sub(r"\s+", " ", prose.lower()).strip()
    # tokenise the prose into the searchable token stream (keep n/k/words/digits).
    toks_all = re.findall(r"[a-z0-9]+", norm)
    out: list[str] = []
    seen_f: set = set()
    # AGGREGATOR is the TOP construction: its {set} slot is comprehended into a
    # member-form RECURSIVELY. Try each aggregator anchored at any position in the
    # stream (a definition embeds the clause: 'a(n) = sigma_2(n): sum of ...').
    for agg in sorted(grammar.get("aggregators", []),
                      key=lambda a: -len([p for p in a["pattern"]
                                          if not p.startswith("{")])):
        pat = [p.lower() for p in agg["pattern"]]
        lit_pre = [p for p in pat if not p.startswith("{")][:1]
        if not lit_pre:
            continue
        head = lit_pre[0]
        # find the aggregator's leading literal anywhere; the {set} slot is the
        # remainder (to end / up to a clause boundary), comprehended recursively.
        for i in range(len(toks_all)):
            if toks_all[i] != head:
                continue
            # the literal prefix of the aggregator pattern (before the slot).
            pre = []
            for p in pat:
                if p.startswith("{"):
                    break
                pre.append(p)
            if toks_all[i:i + len(pre)] != pre:
                continue
            set_toks = toks_all[i + len(pre):]
            if not set_toks:
                continue
            mf = _comprehend_member_form(set_toks, grammar, 0, frozenset())
            if mf is None:
                # the whole tail did not comprehend — try trimming a trailing
                # token (a definition tail like 'of n.' punctuation already gone;
                # this also lets a SHORTER member-form match before junk).
                for cut in range(1, min(4, len(set_toks))):
                    mf = _comprehend_member_form(set_toks[:-cut], grammar, 0,
                                                 frozenset())
                    if mf is not None:
                        break
            if mf is None:
                continue
            formula = agg["formula"]
            formula = _slot_fill(formula, mf)
            if formula not in seen_f:
                seen_f.add(formula)
                out.append(formula)
    return out


# ---------------------------------------------------------------------------
# READ ABOUT HOW TO READ — ACQUIRE A COMPREHENSION CONSTRUCTION BY READING its
# META-DEFINITION. The agent reads a prose explanation of HOW a math form maps to
# a structure/operation ('the cubes of a set means each member multiplied by
# itself three times') and GROUNDS it as a construction (graph data appended to
# _ACQUIRED) — the acquire() mechanism applied to COMPREHENSION:
#
#   SOURCE     = the meta-definition text ('read how to read X').
#   COMPREHEND = parse the 'PATTERN means STRUCTURE' meta-form into a construction
#                (a value-map / filter dict — the same shape the seeded grammar
#                holds), bottoming out at HELD constructions/ops (the bedrock).
#   BEDROCK    = the held constructions + ops (member-form value/predicate, the
#                arithmetic the structure-side composes over).
#   VERIFY     = the new construction correctly PARSES a given example (it now
#                comprehends a form it couldn't before).
#
# The meta-grammar covers the REGULAR 'PATTERN means STRUCTURE' forms (a value-map
# 'the <NAME> of a set means each member <ARITH-of-its-value>'; a post-filter
# '<NAME> means the members that are <CONDITION>'). The honest residual: a
# meta-definition that is not 'PATTERN means STRUCTURE'-shaped does not parse.
# No LLM, no per-form code — the meta-def is read, the construction is graph data.
# ---------------------------------------------------------------------------

# held STRUCTURE-side vocabulary the meta-definition's RHS composes over (the
# bedrock the meta-parse bottoms out on): how a prose phrase maps to a value
# expression over the member's own value placeholder `{v}`.
_META_VALUE_PHRASES = [
    (re.compile(r"itself (?:three|3) times|the cube of (?:itself|each)|"
                r"raised to the (?:third|3rd) power|cubed"),
     "({v})*({v})*({v})"),
    (re.compile(r"itself (?:twice|two times)|the square of (?:itself|each)|"
                r"raised to the (?:second|2nd) power|squared"),
     "({v})*({v})"),
]
# held CONDITION-side vocabulary a filter's meta-definition composes over (member
# k against n) -> a 0/1 multiplicative mask.
_META_CONDITION_PHRASES = [
    (re.compile(r"less than n|smaller than n|below n|strictly less than n"),
     "(k<n)"),
    (re.compile(r"greater than 1|more than 1|above 1"), "(k>1)"),
    (re.compile(r"\bodd\b"), "(k%2)"),
    (re.compile(r"\beven\b"), "(1-k%2)"),
]


def comprehend_meta_definition(meta: str) -> Optional[dict]:
    """COMPREHEND a 'PATTERN means STRUCTURE' meta-definition into a CONSTRUCTION
    dict (graph data — the same shape the seeded grammar holds). Two regular
    meta-forms (the structure-side bottoms out at HELD value/condition vocabulary):

      · VALUE-MAP:  'the <NAME> of a set means each member multiplied by itself
                     three times'  ->  a value_map construction
                     {pattern: ['<NAME>', 'of', '{inner}'],
                      value: '<held value over {inner.value}>',
                      predicate: '{inner.predicate}'}.
      · POST-FILTER: '<NAME...> means the members that are less than n'  ->  a
                     filter construction narrowing the inner predicate by a held
                     0/1 mask.

    Returns the construction dict (with a 'kind' key: 'value_map'|'filter') or
    None (the meta-def is not a regular 'PATTERN means STRUCTURE' form — the honest
    residual)."""
    if not meta:
        return None
    text = re.sub(r"\s+", " ", meta.strip().rstrip(".")).lower()
    m = re.search(r"\bmeans\b", text)
    if not m:
        return None
    lhs = text[:m.start()].strip()
    rhs = text[m.end():].strip()

    # VALUE-MAP meta-form: LHS is 'the <NAME> of [a set / X]'; RHS describes the
    # per-member value over its own value (the bedrock arithmetic vocabulary).
    lm = re.match(r"(?:the\s+)?([a-z]+)\s+of\b", lhs)
    if lm:
        name = lm.group(1)
        for rx, val_tmpl in _META_VALUE_PHRASES:
            if rx.search(rhs):
                value = val_tmpl.replace("{v}", "{inner.value}")
                return {"kind": "value_map", "name": f"acq_{name}",
                        "pattern": [name, "of", "{inner}"],
                        "value": value, "predicate": "{inner.predicate}"}

    # POST-FILTER meta-form: '<phrase> means the members that are <CONDITION>'. The
    # LHS phrase is the filter's surface pattern; the RHS condition the held mask.
    fm = re.search(r"members?\s+(?:of[^,]*?\s+)?that are\s+(.*)$", rhs) or \
        re.search(r"that are\s+(.*)$", rhs)
    if fm or "that are" in lhs:
        cond_text = fm.group(1) if fm else lhs
        for rx, mask in _META_CONDITION_PHRASES:
            if rx.search(cond_text):
                # the filter's surface pattern = the LHS tokens (e.g.
                # 'that are below n' -> pattern ['that','are','below','n']).
                pat = re.findall(r"[a-z0-9]+", lhs)
                # if the LHS is just a NAME, use the RHS condition phrase tokens.
                if pat and pat[0] != "that":
                    cph = re.search(r"that are\s+(.*)$", rhs)
                    if cph:
                        pat = ["that", "are"] + re.findall(r"[a-z0-9]+",
                                                           cph.group(1))
                return {"kind": "filter", "name": "acq_filter",
                        "pattern": pat, "mask": mask}
    return None


def install_construction(con: dict) -> bool:
    """INSTALL an acquired construction into the runtime grammar (graph data
    appended to _ACQUIRED) so comprehend_recursive composes it like any seeded
    construction. Returns True if installed."""
    kind = con.get("kind")
    bucket = {"value_map": "value_maps", "filter": "filters",
              "member_form": "member_forms", "aggregator": "aggregators",
              "notation": "notations"}.get(kind)
    if bucket is None:
        return False
    entry = {k: v for k, v in con.items() if k != "kind"}
    # NOTATIONS de-dup by the symbol they introduce (the symbol IS the key — a
    # later introduction of the same symbol REPLACES the earlier reading).
    if bucket == "notations":
        for ex in _ACQUIRED[bucket]:
            if ex.get("symbol") == entry.get("symbol"):
                ex.update(entry)
                return True
        _ACQUIRED[bucket].append(entry)
        return True
    # de-dup by pattern.
    for ex in _ACQUIRED[bucket]:
        if ex.get("pattern") == entry.get("pattern"):
            return True
    _ACQUIRED[bucket].append(entry)
    return True


def acquire_construction(form_name: str, meta_definition: str,
                         example: Optional[str] = None,
                         example_values: Optional[list] = None) -> dict:
    """ACQUIRE a comprehension construction by READING its meta-definition — the
    acquire() mechanism applied to COMPREHENSION ('read about how to read math').

    Delegates the SOURCE -> COMPREHEND -> COMPOSE -> VERIFY pipeline to the general
    acquire block (domains/acquire.acquire): SOURCE = the meta-def text; COMPREHEND
    = comprehend_meta_definition (parse 'PATTERN means STRUCTURE' -> a construction
    dict); COMPOSE = install the construction into the grammar (the bedrock = held
    constructions/ops); VERIFY = the new construction PARSES the given `example`
    (and, when `example_values` are supplied, the parsed formula REPRODUCES them).

    Returns {acquired, construction, before, after, reason}: `before` is whether
    the example comprehended BEFORE the acquire (the NONE), `after` whether it does
    AFTER (the parse) — the before->read-meta->after the proof wants."""
    from domains import acquire as _acq

    # BEFORE: does the example comprehend with the CURRENT grammar? (the NONE.)
    before = bool(comprehend_recursive(example)) if example else False

    def _source(_t):
        return meta_definition

    def _comprehend(form):
        return comprehend_meta_definition(form)

    def _verify(_t, ctx):
        con = ctx["structure"]
        if not con:
            return {"verified": False, "reason": "meta-def did not comprehend "
                    "as a 'PATTERN means STRUCTURE' construction"}
        install_construction(con)
        if not example:
            return {"verified": True, "construction": con,
                    "reason": "construction installed (no example to verify)"}
        forms = comprehend_recursive(example)
        if not forms:
            return {"verified": False, "construction": con,
                    "reason": "installed but the example still does not parse"}
        # optional stronger VERIFY: the parsed formula reproduces given values.
        if example_values is not None:
            from domains import compute_grounding as _cg
            from domains import reason as _reason
            for f in forms:
                comp = _cg.comprehend_computational_definition("a(n) = " + f)
                if not comp:
                    continue
                ok = True
                for i, want in enumerate(example_values):
                    try:
                        got = _reason.solve(comp["term"], {"n": i + 1})
                    except Exception:
                        ok = False
                        break
                    if int(got) != int(want):
                        ok = False
                        break
                if ok:
                    return {"verified": True, "construction": con,
                            "formula": f, "reason": "example parses + reproduces "
                            "the given values"}
            return {"verified": False, "construction": con, "forms": forms,
                    "reason": "example parses but no form reproduces the values"}
        return {"verified": True, "construction": con, "forms": forms,
                "reason": "the example now PARSES (it did not before)"}

    ar = _acq.acquire(form_name, source=_source, comprehend=_comprehend,
                      bedrock="held_constructions_and_ops", verify=_verify)
    after = bool(comprehend_recursive(example)) if example else ar.acquired
    return {"acquired": ar.acquired,
            "construction": (ar.verify or {}).get("construction"),
            "before": before, "after": after,
            "forms": (ar.verify or {}).get("forms"),
            "formula": (ar.verify or {}).get("formula"),
            "reason": ar.reason or (ar.verify or {}).get("reason", "")}


# ---------------------------------------------------------------------------
# ACQUIRE A DEFINITIONAL CONSTRUCTION-TYPE — the COMPOUNDING step (cmsg81). The
# detect+brute-force (cmsg80) cracks the SHAPED-LIKE-KNOWN dense claims (8.4% ->
# 13.1%); the un-cracked residual is dominated by ONE recurring construction-TYPE
# the held genus-differentia structure does not recognise: the PREDICATIVE /
# CONDITIONAL definition — 'We say X is P if Q', 'We call X a P if Q' (a property
# definition gated by a condition, the hallmark of research math). The agent
# ACQUIRES this construction-type the SAME way it acquires a math-prose construction
# or a notation: it reads HOW the construction is written (its meta-description) OR
# ABSTRACTS the recurring shape from its own FAILURE-INSTANCES (the failures ARE the
# teaching examples — analogy.abstract_patterns spirit), COMPREHENDS it into the new
# held markers (a definitional OPENER to skip + a conditional TERMINATOR that bounds
# the property), INSTALLS them as graph data (_ACQUIRED_DEFN), and VERIFIES the
# construction now PARSES an instance it returned None on before. Each acquired
# construction-type WIDENS what the brute force can crack — the meta-ability
# COMPOUNDS. Faithful: the meta-def / instances are READ; the markers are graph
# data; no LLM, no per-claim Python rule.
# ---------------------------------------------------------------------------

# the OPENER phrases a definitional-property construction uses (the discourse frame
# 'we say / we call' that introduces the definiendum). Held as the meta-vocabulary
# the meta-parse + the instance-abstraction recognise — a definitional opener is a
# small closed family in research register.
_DEFN_OPENER_VOCAB = ["we say", "we call", "one says", "one calls",
                      "we define", "is said to be", "we shall say"]
# the conditional TERMINATOR markers that bound the property-genus P and begin the
# gating condition Q ('X is P IF Q' / 'X is P IFF Q' / 'X is P WHENEVER Q').
_DEFN_CONDITION_VOCAB = ["if", "iff", "whenever", "provided"]

# ---------------------------------------------------------------------------
# THE CONSTRUCTION-TYPE QUEUE VOCABULARY (the WALK — cmsg82). cmsg81 ranked the
# un-cracked residual into a QUEUE of missing construction-types; it acquired the
# predicative/conditional one. The agent now WALKS THE REST. Each entry names a
# construction-TYPE's recurring SURFACE MARKERS (the small closed family the agent
# reads off a meta-description OR abstracts from its own failure-instances — the
# SAME held meta-vocabulary as _DEFN_OPENER_VOCAB, one register wider). The `kind`
# records the agent's STRUCTURAL diagnosis the WALK will TEST, not assume:
#
#   · 'definitional' — the construction is an 'X is-a GENUS' DEFINITION (constructive
#     'a monoid consists of a SET ...', universal-property 'the product is the
#     TERMINAL OBJECT ...'): a clean object->genus the genus-differentia grounding
#     CAN lift. These markers feed the same opener/copula/condition machinery.
#
#   · 'logical' — the construction is a QUANTIFIED / LOGICAL CLAIM, NOT a definition:
#     existential ('there exists Z such that P'), universal ('for all X, P'), TFAE
#     ('the following are equivalent'), adjunction ('F is left adjoint to G'). These
#     have NO clean object->genus (the 'term' is a quantified clause, the 'genus' is
#     a property/relation) — acquiring their opener does NOT lift the genus-differentia
#     grounding. The WALK DISCOVERS this honestly: the agent's OWN precision floor
#     (_is_clean_object on the term+genus) REJECTS the quantified-clause parse, so the
#     VERIFY fails -> the acquire dries. This is a DIFFERENT KIND of claim needing a
#     non-genus-differentia grounding (the next-deeper frontier), NOT a failure.
#
# Faithful: this is HELD VOCABULARY (graph data, the same closed-family form the
# predicative openers already are); the WALK ATTEMPTS each, the VERIFY (a clean
# term+genus on a real instance) is the honest selector. No per-claim rule, no LLM.
CONSTRUCTION_TYPE_VOCAB: dict = {
    "constructive_definition": {
        "kind": "definitional",
        # a constructive definition INTRODUCES the genus via a structural copula
        # ('a monoid CONSISTS OF a set ...', 'a module is a group EQUIPPED WITH ...').
        "openers": [],
        "copulas": ["consists of", "consist of", "is given by"],
        "conditions": [],
    },
    "universal_property_definition": {
        "kind": "definitional",
        # a universal-property definition is a plain copula 'X is the TERMINAL/INITIAL
        # OBJECT ...' — the genus is the universal object; no extra opener needed, the
        # base copula already reads it (so the acquire is expected to be REDUNDANT).
        "openers": [],
        "copulas": [],
        "conditions": [],
    },
    # the LOGICAL/QUANTIFIED types carry their recurring opener under `quantifiers`
    # (NOT `openers`): a quantifier BINDS a variable / a relation — it does NOT
    # introduce a definiendum, so it must NOT be minted as a definitional opener (that
    # would mis-read a bound variable as a defined object — the over-grab the precision
    # floor exists to reject). The agent RECOGNISES the type by its quantifier but
    # mints NO definitional marker -> the honest dry-up (a DIFFERENT KIND of claim).
    "existential_claim": {
        "kind": "logical",
        # 'there exists Z such that P' — a quantified EXISTENCE claim. The opener is a
        # quantifier binding a NEW variable Z, not a definiendum; there is no
        # object->genus (the 'term' would be the bound variable / the such-that clause).
        "openers": [],
        "copulas": [],
        "conditions": [],
        "quantifiers": ["there exists", "there is", "there exist"],
    },
    "universal_claim": {
        "kind": "logical",
        # 'for all/every X, P' — a quantified UNIVERSAL claim. The opener binds a
        # RANGE, not a definiendum; the 'term' is the quantified clause -> no
        # object->genus.
        "openers": [],
        "copulas": [],
        "conditions": [],
        "quantifiers": ["for all", "for every", "for any", "for each"],
    },
    "tfae_claim": {
        "kind": "logical",
        # 'the following are equivalent' — a LOGICAL-EQUIVALENCE claim over a list of
        # conditions; no single object IS-A genus.
        "openers": [],
        "copulas": [],
        "conditions": [],
        "quantifiers": ["the following are equivalent",
                        "the following conditions are equivalent", "tfae"],
    },
    "adjunction_claim": {
        "kind": "logical",
        # 'F is left/right adjoint to G' — a RELATIONAL claim between two functors;
        # 'left adjoint' is a relation, not a genus the object is a kind of.
        "openers": [],
        "copulas": [],
        "conditions": [],
        # the relational markers the agent reads to RECOGNISE the type (it is a
        # relation, not a definition — surfaced so the WALK can name it).
        "quantifiers": ["left adjoint", "right adjoint", "adjoint to", "adjunction"],
    },
}


def comprehend_definitional_construction(
        meta: Optional[str] = None,
        instances: Optional[list[str]] = None,
        vocab: Optional[dict] = None) -> Optional[dict]:
    """COMPREHEND a construction-TYPE into the held marker-shape (graph data) — TWO
    acquisition routes, both the agent's:

      (A) READ-HOW-TO-READ (meta-description): a prose sentence describing HOW the
          construction is written, e.g. 'a property is defined by writing we say X
          is P if Q, where X is the object, P the property, and Q the condition'.
          The OPENER ('we say'/'we call') + the CONDITION word ('if') are read off
          the meta-description against the held opener/condition vocabulary.

      (B) ABSTRACT-FROM-INSTANCES: the recurring shape abstracted from the agent's
          OWN failure-instances (the cmsg80 un-cracked claims) — the analogy.
          abstract_patterns spirit applied to surface construction-shape. The
          recurring leading OPENER phrase + the recurring conditional CONNECTIVE are
          the abstracted shape (a marker is kept only when it recurs across several
          instances — the abstraction, not a single-instance fit).

    `vocab` (the WALK — cmsg82) supplies the construction-TYPE's marker FAMILIES
    (openers / copulas / conditions) the abstraction reads against — a held
    CONSTRUCTION_TYPE_VOCAB entry. Default = the predicative/conditional families
    (_DEFN_OPENER_VOCAB / _DEFN_CONDITION_VOCAB) so the existing cmsg81 acquire is
    unchanged. A type whose markers are present yields its shape; a type whose
    markers do NOT recur (or whose recognised opener is a quantifier that does not
    introduce a definiendum) yields no DEFINITIONAL shape -> the VERIFY downstream
    decides whether a clean object->genus follows (the honest definitional-vs-logical
    discrimination, not assumed here).

    Returns {kind:'definitional_construction', openers:[...], extra_differentia:[...],
    extra_copula:[...], evidence} or None (no construction-shape comprehended — the
    honest residual). The markers are the GRAPH DATA install_construction installs."""
    opener_vocab = (list(vocab.get("openers", [])) if vocab is not None
                    else list(_DEFN_OPENER_VOCAB))
    copula_vocab = (list(vocab.get("copulas", [])) if vocab is not None else [])
    cond_vocab = (list(vocab.get("conditions", [])) if vocab is not None
                  else list(_DEFN_CONDITION_VOCAB))
    # QUANTIFIER markers (the logical/quantified types) — RECOGNISED so the agent can
    # name the construction-type, but NOT minted as definitional markers (a quantifier
    # binds a variable / a relation; it does not introduce a definiendum). Recording
    # them lets the WALK report "recognised as a quantified claim -> no object->genus".
    quant_vocab = (list(vocab.get("quantifiers", [])) if vocab is not None else [])
    openers: list[str] = []
    extra_diff: list[str] = []
    extra_cop: list[str] = []
    evidence: dict = {}
    recognised_quantifiers: list[str] = []

    # ROUTE (A): read the meta-description against the held vocabulary.
    if meta:
        m = re.sub(r"\s+", " ", meta.lower())
        for op in opener_vocab:
            if op in m:
                if op == "is said to be":
                    extra_cop.append(op)
                else:
                    openers.append(op)
        for cop in copula_vocab:
            if cop in m and cop not in extra_cop:
                extra_cop.append(cop)
        for cond in cond_vocab:
            if re.search(r"\b" + re.escape(cond) + r"\b", m):
                extra_diff.append(cond)
        for q in quant_vocab:
            if q in m and q not in recognised_quantifiers:
                recognised_quantifiers.append(q)
        evidence["meta"] = meta

    # ROUTE (B): abstract the recurring shape from the failure-instances. A marker
    # is acquired only when it RECURS (>= recur_min instances) — the abstraction
    # over the teaching examples, not a one-off surface match.
    if instances:
        recur_min = max(2, len(instances) // 25)
        op_hits: dict[str, int] = {}
        cop_hits: dict[str, int] = {}
        cond_hits: dict[str, int] = {}
        quant_hits: dict[str, int] = {}
        for ins in instances:
            low = re.sub(r"\s+", " ", (ins or "").lower()).strip()
            for op in opener_vocab:
                if op == "is said to be":
                    continue
                if low.startswith(op + " "):
                    op_hits[op] = op_hits.get(op, 0) + 1
            # RECOGNISE (do NOT mint) a quantifier marker — surfaces that the type IS
            # a quantified/logical claim (the agent names it), no definitional marker.
            for q in quant_vocab:
                if (" " + q + " ") in (" " + low + " "):
                    quant_hits[q] = quant_hits.get(q, 0) + 1
            # a structural COPULA introducing the genus ('a monoid CONSISTS OF a
            # set ...') — recurring anywhere in the instance.
            for cop in copula_vocab:
                if (" " + cop + " ") in (" " + low + " "):
                    cop_hits[cop] = cop_hits.get(cop, 0) + 1
            # a CONDITIONAL definition has a copula FOLLOWED by a condition word
            # ('... is <property> if ...') — the recurring conditional terminator.
            for cond in cond_vocab:
                if re.search(r"\bis\b[^.]{1,60}?\b" + re.escape(cond) + r"\b", low):
                    cond_hits[cond] = cond_hits.get(cond, 0) + 1
        for op, n in op_hits.items():
            if n >= recur_min and op not in openers:
                openers.append(op)
        for cop, n in cop_hits.items():
            if n >= recur_min and cop not in extra_cop:
                extra_cop.append(cop)
        for cond, n in cond_hits.items():
            if n >= recur_min and cond not in extra_diff:
                extra_diff.append(cond)
        for q, n in quant_hits.items():
            if n >= recur_min and q not in recognised_quantifiers:
                recognised_quantifiers.append(q)
        evidence["instance_opener_counts"] = op_hits
        evidence["instance_copula_counts"] = cop_hits
        evidence["instance_condition_counts"] = cond_hits
        evidence["instance_quantifier_counts"] = quant_hits
        evidence["recur_min"] = recur_min

    evidence["recognised_quantifiers"] = recognised_quantifiers
    if not (openers or extra_diff or extra_cop):
        # NO definitional marker minted. When a QUANTIFIER was recognised, this is the
        # honest LOGICAL-claim diagnosis (the agent names the type but it has no
        # object->genus to ground) — return the diagnosis so the WALK can report it,
        # with empty definitional markers (nothing installs -> the honest dry-up).
        if recognised_quantifiers:
            return {"kind": "logical_claim", "openers": [],
                    "extra_differentia": [], "extra_copula": [],
                    "quantifiers": list(dict.fromkeys(recognised_quantifiers)),
                    "evidence": evidence}
        return None
    return {"kind": "definitional_construction",
            "openers": list(dict.fromkeys(openers)),
            "extra_differentia": list(dict.fromkeys(extra_diff)),
            "extra_copula": list(dict.fromkeys(extra_cop)),
            "evidence": evidence}


def install_definitional_construction(con: dict) -> bool:
    """INSTALL an acquired definitional construction-type into the runtime
    definition structure (graph data appended to _ACQUIRED_DEFN) so
    load_definition_structure merges it and extract_definition — and therefore the
    brute-force's comprehend_part — recognise the construction. De-dup per marker.
    Returns True if anything new was installed."""
    if not con or con.get("kind") != "definitional_construction":
        return False
    changed = False
    for op in con.get("openers", []):
        if op not in _ACQUIRED_DEFN["definitional_openers"]:
            _ACQUIRED_DEFN["definitional_openers"].append(op)
            changed = True
    for d in con.get("extra_differentia", []):
        if d not in _ACQUIRED_DEFN["extra_differentia"]:
            _ACQUIRED_DEFN["extra_differentia"].append(d)
            changed = True
    for c in con.get("extra_copula", []):
        if c not in _ACQUIRED_DEFN["extra_copula"]:
            _ACQUIRED_DEFN["extra_copula"].append(c)
            changed = True
    return changed


def acquire_definitional_construction(
        form_name: str, *, meta_definition: Optional[str] = None,
        instances: Optional[list[str]] = None,
        example: Optional[str] = None,
        example_term: Optional[str] = None,
        vocab: Optional[dict] = None) -> dict:
    """ACQUIRE a PREDICATIVE/CONDITIONAL definitional construction-type — the
    acquire() mechanism (SOURCE -> COMPREHEND -> COMPOSE/install -> VERIFY) applied
    to a research-register construction-TYPE. SOURCE = the meta-description AND/OR
    the failure-instances; COMPREHEND = comprehend_definitional_construction (read
    how-to-read OR abstract-from-instances -> the held markers); COMPOSE = install
    the markers as graph data (_ACQUIRED_DEFN); VERIFY = a previously-uncomprehended
    EXAMPLE instance now extracts a CLEAN term + genus (it did not before).

    Returns {acquired, construction, before, after, reason}: `before`/`after` are
    whether the `example` extracts a clean definition BEFORE vs AFTER the acquire —
    the before(None)->read/abstract->after(clean) the compounding proof wants. The
    VERIFY uses the agent's OWN precision floor on the term+genus."""
    from domains import acquire as _acq

    def _clean(s):
        # the agent's comprehension-channel precision floor (the brute-force uses
        # the SAME _is_clean_object from agent_grounds_each_claim — mirrored here as
        # a noun-phrase shape check so this module has no cross-import cycle).
        if not _plausible_object(s):
            return False
        t = re.sub(r"\s+", " ", (s or "").strip().lower())
        w = re.findall(r"[a-z0-9'^_/().-]+", t)
        if not w or len(w) > 6:
            return False
        openers_flat = {o.split()[0] for o in _DEFN_OPENER_VOCAB}
        if w[0] in openers_flat or w[0] in {"we", "one"}:
            return False
        if w[-1] in ("if", "iff"):
            return False
        return True

    def _extract_clean(ex):
        d = extract_definition(ex, term=example_term)
        if (d and d.get("term") and d.get("genus")
                and _clean(d["term"]) and _clean(d["genus"])):
            return d
        return None

    before = bool(_extract_clean(example)) if example else False

    def _source(_t):
        return {"meta": meta_definition, "instances": instances}

    def _comprehend(form):
        return comprehend_definitional_construction(
            meta=form.get("meta"), instances=form.get("instances"),
            vocab=vocab)

    def _verify(_t, ctx):
        con = ctx["structure"]
        if not con:
            return {"verified": False, "reason": "no definitional construction-"
                    "shape comprehended (neither the meta-description nor the "
                    "failure-instances yielded a recurring marker)"}
        install_definitional_construction(con)
        if not example:
            return {"verified": True, "construction": con,
                    "reason": "construction installed (no example to verify)"}
        d = _extract_clean(example)
        if not d:
            return {"verified": False, "construction": con,
                    "reason": "installed but the example still does not extract a "
                    "clean term+genus"}
        return {"verified": True, "construction": con,
                "term": d["term"], "genus": d["genus"],
                "reason": f"the example now extracts a CLEAN definition "
                f"(term={d['term']!r} genus={d['genus']!r}) — it did not before"}

    ar = _acq.acquire(form_name, source=_source, comprehend=_comprehend,
                      bedrock="held_definition_structure", verify=_verify)
    after = bool(_extract_clean(example)) if example else ar.acquired
    return {"acquired": ar.acquired,
            "construction": (ar.verify or {}).get("construction"),
            "before": before, "after": after,
            "term": (ar.verify or {}).get("term"),
            "genus": (ar.verify or {}).get("genus"),
            "reason": ar.reason or (ar.verify or {}).get("reason", "")}


# ---------------------------------------------------------------------------
# NOTATION IS A LEARNABLE SYMBOLIC LANGUAGE — acquired by READING its
# introduction, the SAME acquire-by-reading mechanism. A piece of notation `SYM`
# (σ(n), φ(n), d(n), n!) is INTRODUCED by a prose sentence that DEFINES it
# ("σ(n) denotes the sum of the divisors of n", "let d(n) denote the number of
# divisors of n", "n! means the factorial of n"). The agent:
#   1. READS the introduction (the SOURCE),
#   2. COMPREHENDS it as 'SYMBOL means MEANING' (the same meta-definition parse
#      used for 'cubes of') — the MEANING side is itself comprehended ORDER-N
#      (extract_function over 'the sum of the divisors of n' -> the composed
#      sum-form), bottoming out at HELD constructions,
#   3. GROUNDS a NOTATION construction mapping the symbol-form to the meaning,
#   4. now COMPREHENDS a FORMULA written in that notation (σ(12)) -> grounds +
#      computes + VERIFIES vs ground-truth (OEIS).
#
# Faithful: notation's MEANING is prose; a notation-construction is GRAPH DATA
# acquired via the agent's acquire() / comprehend_meta_definition mechanism. The
# symbol is read like any other token; the argument substitutes for the index
# variable `n` and the existing compute chain grounds it. No LLM, no Rust, no
# per-symbol Python rule — one symbol = one piece of read data.
#
# The HONEST residual: genuinely VISUAL/diagrammatic content (a commutative
# diagram, a geometric picture) whose meaning, while statable in prose/equations,
# is NOT delivered AS prose in the source; and tacit/unwritten intuition. These
# reduce to their formal/prose content WHERE it is written — the residual is
# breadth + the truly-unwritten, NOT a non-learnable layer.
# ---------------------------------------------------------------------------

# the INTRODUCTION copulas that DEFINE a symbol (the prose that says 'this symbol
# means that meaning'). Longest-first so 'is defined as' wins over 'is'. Held as
# data, mirroring the definitional copula family — a symbol-introduction IS a
# definition whose definiendum is a piece of notation.
_NOTATION_COPULAS = ["is defined as", "is defined to be", "is the", "denotes",
                     "denote", "means", "stands for", "represents",
                     "is", "are"]

# the index-variable a one-argument symbol's meaning is written in (σ(n) -> the
# meaning is a function of n). The argument of a formula substitutes for it.
_NOTATION_INDEX_VARS = ["n", "m", "k", "x"]


def comprehend_notation_introduction(intro: str) -> Optional[dict]:
    """COMPREHEND a SYMBOL INTRODUCTION ('σ(n) denotes the sum of the divisors of
    n' / 'let d(n) denote the number of divisors of n' / 'n! means the factorial
    of n') into a NOTATION construction (graph data — the same shape the seeded
    grammar holds). The same 'PATTERN means STRUCTURE' meta-form, with the PATTERN
    a piece of NOTATION (a symbol applied to an index variable, or a postfix like
    n!) and the STRUCTURE its MEANING — comprehended ORDER-N via extract_function,
    bottoming out at HELD constructions.

    Returns {kind:'notation', symbol, arg_var, postfix, meaning_prose, formula} —
    `symbol` the notation token (σ / φ / d / !), `arg_var` the index variable the
    meaning is written in (n), `formula` the runnable form (in `n`) the meaning
    comprehends to. Returns None when the sentence is not a symbol-introduction,
    OR the meaning prose does not itself comprehend to a runnable form (the honest
    residual — a symbol introduced in terms the agent cannot yet read)."""
    if not intro:
        return None
    text = re.sub(r"\s+", " ", intro.strip().rstrip(".")).strip()
    # drop a leading 'let' / 'where' / 'here' introducer ('let σ(n) denote …').
    text = re.sub(r"^(?:let|where|here|the symbol|recall that|suppose)\s+",
                  "", text, flags=re.IGNORECASE)

    # find the INTRODUCTION copula -> LHS = the notation, RHS = the meaning prose.
    low = text.lower()
    cut = None
    for cop in _NOTATION_COPULAS:
        m = re.search(r"(?<![A-Za-z])" + re.escape(cop) + r"(?![A-Za-z])", low)
        if m:
            if cut is None or m.start() < cut[1]:
                cut = (cop, m.start(), m.end())
    if cut is None:
        return None
    lhs = text[:cut[1]].strip()
    rhs = text[cut[2]:].strip()
    # the RHS may itself lead with an article the meaning grammar also reads; keep
    # it (extract_function tolerates 'the sum of …'). A leading 'the symbol that
    # gives' style is the meaning prose verbatim.
    if not lhs or not rhs:
        return None

    # COMPREHEND the LHS NOTATION — two regular forms:
    #   · APPLIED:  '<SYM>(<arg>)'  e.g. σ(n), phi(n) — symbol + index argument.
    #   · POSTFIX:  '<arg><SYM>'    e.g. n! — index then a postfix operator symbol.
    symbol = None
    arg_var = None
    postfix = False
    m_app = re.match(r"^(.+?)\s*\(\s*([A-Za-z])\s*\)$", lhs)
    m_post = re.match(r"^([A-Za-z])\s*([^A-Za-z0-9\s()]+)$", lhs)
    if m_app:
        symbol = m_app.group(1).strip()
        arg_var = m_app.group(2).strip().lower()
    elif m_post and m_post.group(1).lower() in _NOTATION_INDEX_VARS:
        # 'n!' — the postfix symbol applied to the index var.
        arg_var = m_post.group(1).strip().lower()
        symbol = m_post.group(2).strip()
        postfix = True
    else:
        return None
    if not symbol or arg_var not in _NOTATION_INDEX_VARS:
        return None

    # COMPREHEND the MEANING prose ORDER-N (the agent's existing math-prose
    # comprehension) into a runnable formula in the index var. The meaning is
    # written in `arg_var`; normalise it to `n` (the grammar's index var) so the
    # held constructions match, then the formula is in `n`.
    meaning = rhs
    if arg_var != "n":
        meaning = re.sub(r"(?<![A-Za-z])" + re.escape(arg_var) + r"(?![A-Za-z])",
                         "n", meaning)
    forms = extract_function(meaning)
    if not forms:
        return None  # the meaning prose itself does not comprehend (honest None).

    return {"kind": "notation", "symbol": symbol, "arg_var": "n",
            "postfix": postfix, "meaning_prose": rhs, "formula": forms[0],
            "formulas": forms}


def _notation_by_symbol() -> dict:
    """The acquired notations, keyed by symbol (the lookup the formula reader
    uses). Pure data read — no decision."""
    return {nt["symbol"]: nt for nt in _ACQUIRED.get("notations", [])
            if nt.get("symbol")}


def comprehend_formula(formula: str) -> Optional[dict]:
    """COMPREHEND a FORMULA written in ACQUIRED notation -> a runnable form (in
    `n`-free, fully numeric when the argument is a literal; or in `n` when the
    argument is the index var). The SAME order-N comprehension: a formula
    composes acquired notation tokens like any construction.

      · ATOMIC : 'σ(12)'   -> substitute 12 for the meaning's index var -> the
                 runnable formula 'sum{k in 1..12 : (k)*((k|12))}'.
      · ATOMIC : 'σ(n)'    -> the meaning formula in `n` (left symbolic).
      · POSTFIX: '12!'     -> the postfix symbol's meaning at 12.
      · COMPOSED: 'σ(n) + φ(n)' / 'σ(12)/d(12)' — each notation atom is
                 comprehended, then the arithmetic composes them (order-N over the
                 acquired symbols). The arithmetic is the held compute tower.

    Returns {formula, expanded, symbols, arg, all_held} where `expanded` is the
    runnable string compute_grounding grounds, `symbols` the acquired notation
    tokens it used. Returns None when the formula uses a symbol the agent has NOT
    acquired (BEFORE the read = NONE — the proof's before-state), or is not a
    recognisable notation formula."""
    if not formula:
        return None
    notations = _notation_by_symbol()
    if not notations:
        return None
    text = formula.strip()

    used: list[str] = []
    arg_seen: Optional[str] = None

    def _expand_atom(sym: str, arg: str) -> Optional[str]:
        nt = notations.get(sym)
        if nt is None:
            return None
        used.append(sym)
        nonlocal arg_seen
        arg_seen = arg
        f = nt["formula"]
        # substitute the formula's index var (n) with the supplied argument.
        return "(" + re.sub(r"(?<![A-Za-z0-9_])n(?![A-Za-z0-9_])",
                            "(" + arg + ")", f) + ")"

    # build a regex that matches any acquired APPLIED symbol 'SYM(arg)' or POSTFIX
    # 'arg SYM'. Symbols may be non-ASCII (σ, φ) — match them literally.
    applied = [re.escape(s) for s, nt in notations.items() if not nt.get("postfix")]
    postfx = [re.escape(s) for s, nt in notations.items() if nt.get("postfix")]

    out = text
    matched_any = False
    # APPLIED: SYM ( arg ) — arg is a literal number or the index var.
    if applied:
        app_re = re.compile(r"(" + "|".join(applied) +
                            r")\s*\(\s*([A-Za-z0-9]+)\s*\)")

        def _sub_app(m):
            nonlocal matched_any
            rep = _expand_atom(m.group(1), m.group(2))
            if rep is None:
                return m.group(0)
            matched_any = True
            return rep
        out = app_re.sub(_sub_app, out)
    # POSTFIX: arg SYM (e.g. 12!).
    if postfx:
        post_re = re.compile(r"([A-Za-z0-9]+)\s*(" + "|".join(postfx) + r")")

        def _sub_post(m):
            nonlocal matched_any
            rep = _expand_atom(m.group(2), m.group(1))
            if rep is None:
                return m.group(0)
            matched_any = True
            return rep
        out = post_re.sub(_sub_post, out)

    if not matched_any:
        return None
    # any leftover acquired-symbol-looking token means a symbol was un-acquired in
    # a position we could not expand — but matched_any already gates that. The
    # expanded form is now pure compute-tower syntax.
    return {"formula": text, "expanded": out, "symbols": used,
            "arg": arg_seen, "all_held": True}


def acquire_notation(symbol_name: str, introduction: str,
                     example: Optional[str] = None,
                     example_values: Optional[list] = None,
                     example_offset: int = 1) -> dict:
    """ACQUIRE a piece of NOTATION by READING its introduction — the acquire()
    mechanism applied to NOTATION (a symbolic language whose symbols are
    introduced in prose). The SAME SOURCE -> COMPREHEND -> COMPOSE -> VERIFY
    pipeline as acquire_construction, with the COMPREHEND being
    comprehend_notation_introduction (read 'SYM means MEANING' -> a notation
    construction) and the VERIFY being 'a FORMULA written in the symbol now
    PARSES + COMPUTES + (when values are supplied) REPRODUCES the ground truth'.

    Returns {acquired, notation, before, after, expanded, reason}: `before` is
    whether `example` (a formula like 'σ(12)') comprehended BEFORE the read (the
    NONE), `after` whether it does AFTER (the parse) — the before->read->after the
    proof wants. The honest residual surfaces as acquired=False (the introduction
    is not 'SYM means MEANING'-shaped, or the meaning prose does not itself
    comprehend)."""
    from domains import acquire as _acq

    before = bool(comprehend_formula(example)) if example else False

    def _source(_t):
        return introduction

    def _comprehend(form):
        return comprehend_notation_introduction(form)

    def _verify(_t, ctx):
        nt = ctx["structure"]
        if not nt:
            return {"verified": False, "reason": "the introduction did not "
                    "comprehend as a 'SYMBOL means MEANING' notation construction "
                    "(or its meaning prose did not comprehend to a runnable form)"}
        install_construction(nt)
        if not example:
            return {"verified": True, "notation": nt,
                    "reason": "notation installed (no example formula to verify)"}
        comp = comprehend_formula(example)
        if not comp:
            return {"verified": False, "notation": nt,
                    "reason": "installed but the example formula still does not "
                    "parse"}
        # stronger VERIFY: the expanded formula REPRODUCES the source's values.
        if example_values is not None:
            from domains import compute_grounding as _cg
            from domains import reason as _reason
            cc = _cg.comprehend_computational_definition(
                "a(n) = " + comp["expanded"])
            if not cc:
                return {"verified": False, "notation": nt, "expanded":
                        comp["expanded"], "reason": "expanded formula did not "
                        "comprehend as a computation"}
            # a literal-argument formula (σ(12)) evaluates to ONE number; check it
            # against the matching ground-truth value. A symbolic σ(n) evaluates
            # over the offset.. window.
            try:
                arg = comp.get("arg")
                if arg is not None and re.fullmatch(r"\d+", str(arg)):
                    idx = int(arg) - example_offset
                    want = int(example_values[idx])
                    got = int(_reason.solve(cc["term"], {"n": int(arg)}))
                    ok = (got == want)
                    detail = f"{example} = {got} (ground truth {want})"
                else:
                    ok = True
                    for i, w in enumerate(example_values):
                        g = int(_reason.solve(cc["term"],
                                              {"n": example_offset + i}))
                        if g != int(w):
                            ok = False
                            break
                    detail = f"reproduces the source's values"
            except Exception as e:
                return {"verified": False, "notation": nt, "reason":
                        f"evaluation error: {e}"}
            if ok:
                return {"verified": True, "notation": nt,
                        "expanded": comp["expanded"], "value_detail": detail,
                        "reason": f"formula parses + computes + verifies "
                        f"({detail})"}
            return {"verified": False, "notation": nt, "expanded":
                    comp["expanded"], "reason": f"formula parses but does not "
                    f"reproduce the ground truth ({detail})"}
        return {"verified": True, "notation": nt, "expanded": comp["expanded"],
                "reason": "the formula now PARSES + COMPUTES (it did not before)"}

    ar = _acq.acquire(symbol_name, source=_source, comprehend=_comprehend,
                      bedrock="held_constructions_and_ops", verify=_verify)
    after_comp = comprehend_formula(example) if example else None
    return {"acquired": ar.acquired,
            "notation": (ar.verify or {}).get("notation"),
            "before": before, "after": bool(after_comp),
            "expanded": (ar.verify or {}).get("expanded"),
            "value_detail": (ar.verify or {}).get("value_detail"),
            "reason": ar.reason or (ar.verify or {}).get("reason", "")}


# ---------------------------------------------------------------------------
# LATEX IS LEARNABLE THE AGENT'S WAY — acquire a LaTeX macro by READING its
# introduction, the SAME acquire-by-reading mechanism as prose notation. A LaTeX
# macro `\SYM` is INTRODUCED by a prose sentence ("in LaTeX `\ker` denotes the
# kernel", "the macro `\partial` is the boundary operator", "`H_n(X)` denotes the
# n-th homology of X"). BEFORE the read the macro is OPAQUE (parse_formula returns
# None on a formula using it); AFTER, it parses into the operator-tree. The core
# grammar is SEEDED (seeds/latex_math_notation.json); FURTHER macros are ACQUIRED
# by reading — the notation-is-learnable machine, now on LaTeX.
#
# Faithful: the introduction's MEANING is prose (it names a held operator/atom or
# an op name); the acquired macro is GRAPH DATA installed into the LaTeX grammar
# (latex_notation.install_macro). The parse is the agent's; the macro is data. No
# LLM, no Rust, no per-macro Python rule.
# ---------------------------------------------------------------------------

# the introduction copulas that DEFINE a macro (longest-first). Mirrors the prose
# notation copulas — a macro-introduction IS a definition whose definiendum is a
# piece of LaTeX.
_LATEX_INTRO_COPULAS = ["is defined as", "is defined to be", "denotes the",
                        "denotes", "denote", "stands for", "represents",
                        "is the", "means", "is", "are"]

# the held atoms / known op-names a LaTeX macro's MEANING can resolve to (the
# bedrock the meta-parse bottoms out on). Read off the prose grammar's atoms +
# the operator constructions so 'the boundary operator' -> the held ∂, 'the
# kernel' -> the (un-held) kernel op, etc. — the SAME vocabulary both grammars share.
_LATEX_MEANING_TO_OP = {
    "boundary operator": ("boundary_operator", "atom", True),
    "boundary": ("boundary_operator", "atom", True),
    "kernel": ("kernel", "operator", False),
    "image": ("image", "operator", False),
    "cokernel": ("cokernel", "operator", False),
    "dimension": ("dimension", "operator", False),
    "rank": ("rank", "operator", False),
    "tensor product": ("tensor", "structure", False),
    "tensor": ("tensor", "structure", False),
    "direct sum": ("direct_sum", "structure", False),
    "quotient": ("modulo", "structure", False),
    "homology": ("homology", "head", False),
    "cohomology": ("cohomology", "head", False),
}


def comprehend_latex_introduction(intro: str) -> Optional[dict]:
    """COMPREHEND a LaTeX MACRO introduction ('in LaTeX `\\ker` denotes the kernel',
    'the macro `\\partial` is the boundary operator', '`H_n(X)` denotes the n-th
    homology of X') into a LaTeX-macro construction (graph data — the shape
    latex_notation.install_macro installs). The same 'SYM means MEANING' meta-form,
    with the SYM a LaTeX macro (a `\\macro` or an indexed head like `H_n`) and the
    MEANING naming a held atom / known operator.

    Returns {kind, latex, name|op, held|held_runnable, ...} or None when the
    sentence is not a macro-introduction OR the meaning does not name a known
    op/atom (the honest residual — a macro defined in terms the agent cannot map)."""
    if not intro:
        return None
    text = re.sub(r"\s+", " ", intro.strip().rstrip("."))
    # find the LaTeX macro token: a backtick-quoted `\macro` / `H_n(X)`, else a
    # bare leading \macro. Prefer the backtick form (the explicit citation).
    m_tok = re.search(r"`([^`]+)`", text)
    if m_tok:
        latex = m_tok.group(1).strip()
        rest = (text[:m_tok.start()] + " " + text[m_tok.end():]).strip()
    else:
        m_bs = re.search(r"(\\[A-Za-z]+(?:\{[^{}]*\})?)", text)
        if not m_bs:
            return None
        latex = m_bs.group(1).strip()
        rest = (text[:m_bs.start()] + " " + text[m_bs.end():]).strip()
    low = rest.lower()
    # find the introduction copula -> the MEANING is the tail after it.
    cut = None
    for cop in _LATEX_INTRO_COPULAS:
        i = low.find(cop)
        if i >= 0 and (cut is None or i < cut[1]):
            cut = (cop, i, i + len(cop))
    if cut is None:
        return None
    meaning = rest[cut[2]:].strip().lower()
    meaning = re.sub(r"^(the|a|an|its)\s+", "", meaning).strip()
    meaning = re.sub(r"^n-?th\s+", "", meaning).strip()
    meaning = re.sub(r"\s+of\s+.*$", "", meaning).strip()  # drop 'of X' tail.

    # resolve the meaning to a held atom / known op (the bedrock).
    resolved = None
    for phrase, spec in sorted(_LATEX_MEANING_TO_OP.items(),
                               key=lambda kv: -len(kv[0])):
        if phrase in meaning:
            resolved = spec
            break
    if resolved is None:
        return None
    name, kind, held = resolved

    # is the LaTeX an INDEXED HEAD ('H_n', 'H_n(X)')? -> a head macro.
    head_m = re.match(r"^(\\?[A-Za-z]+)\s*([_^])", latex)
    if kind == "head" or (head_m and kind in ("head",)):
        base = re.match(r"^(\\?[A-Za-z]+)", latex).group(1)
        role = "sub_role" if (head_m and head_m.group(2) == "_") else "super_role"
        return {"kind": "head", "latex": base, "name": name,
                role: "degree", "held_runnable": False}
    if kind == "atom":
        return {"kind": "operator", "latex": latex, "name": name,
                "_atom": True, "held": held}
    if kind == "operator":
        return {"kind": "operator", "latex": latex, "name": name,
                "arity": 1, "held_runnable": held}
    if kind == "structure":
        return {"kind": "structure", "latex": latex, "op": name, "args": 2,
                "held_runnable": held}
    return None


def acquire_latex_macro(macro_name: str, introduction: str,
                        example: Optional[str] = None) -> dict:
    """ACQUIRE a LaTeX MACRO by READING its introduction — the acquire() mechanism
    (notation-is-learnable) applied to LaTeX. SOURCE -> COMPREHEND -> COMPOSE ->
    VERIFY: SOURCE = the introduction; COMPREHEND = comprehend_latex_introduction
    ('SYM means MEANING' -> a macro construction); COMPOSE = install into the LaTeX
    grammar (latex_notation.install_macro); VERIFY = a formula using the macro now
    PARSES (it did not before).

    Returns {acquired, macro, before, after, repr, reason}: `before`/`after` are
    whether `example` (a LaTeX formula using the macro) parses BEFORE vs AFTER the
    read — the before(opaque)->read->after(parses) the proof wants."""
    from domains import acquire as _acq
    from domains import latex_notation as _lx

    before = bool(_lx.parse_formula(example)) if example else False

    def _source(_t):
        return introduction

    def _comprehend(form):
        return comprehend_latex_introduction(form)

    def _verify(_t, ctx):
        mac = ctx["structure"]
        if not mac:
            return {"verified": False, "reason": "the introduction did not "
                    "comprehend as a 'MACRO means MEANING' LaTeX construction "
                    "(or its meaning did not name a known operator/atom)"}
        # the atom variant installs as an operator_macro with kind 'atom'.
        if mac.pop("_atom", False):
            mac = {"kind": "operator", "latex": mac["latex"], "name": mac["name"],
                   "held": mac.get("held", False)}
            # an atom macro is stored with kind 'atom' on the macro entry so the
            # parser's atom path (\partial) recognises it.
            _lx.install_macro({"kind": "operator", "latex": mac["latex"],
                               "name": mac["name"], "held": mac["held"]})
            # mark it as an atom in the stored entry.
            for e in _lx._ACQUIRED["operator_macros"]:
                if e.get("latex") == mac["latex"]:
                    e["kind"] = "atom"
        else:
            _lx.install_macro(mac)
        if not example:
            return {"verified": True, "macro": mac,
                    "reason": "macro installed (no example formula to verify)"}
        parsed = _lx.parse_formula(example)
        if not parsed:
            return {"verified": False, "macro": mac,
                    "reason": "installed but the example formula still does not "
                    "parse"}
        return {"verified": True, "macro": mac, "repr": parsed["repr"],
                "reason": f"the formula now PARSES into {parsed['repr']} "
                f"(it did not before)"}

    ar = _acq.acquire(macro_name, source=_source, comprehend=_comprehend,
                      bedrock="held_latex_grammar_and_ops", verify=_verify)
    after = bool(_lx.parse_formula(example)) if example else ar.acquired
    return {"acquired": ar.acquired,
            "macro": (ar.verify or {}).get("macro"),
            "before": before, "after": after,
            "repr": (ar.verify or {}).get("repr"),
            "reason": ar.reason or (ar.verify or {}).get("reason", "")}


# ---------------------------------------------------------------------------
# GENERIC OPERATOR-TREE COMPREHENSION — order-N over RESEARCH prose whose
# OPERATIONS are not yet held as runnable primitives. Where comprehend_recursive
# produces a runnable number-theory formula, this produces a STRUCTURE TREE
# (op(args) nested), composing operator constructions RECURSIVELY (a slot is
# filled by comprehending its content), bottoming out at an ATOMIC TERM (a held
# concept / named object). It is the SAME order-N operator (iterate_to_n over the
# grammar); the difference is the BEDROCK (atomic terms) + the result (a structure
# tree, since the ops are un-held). It NAMES the un-held operations precisely — the
# residual the agent acquires the same way by reading (the next instance).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# GENERIC OBJECT-ATOM bedrock — the OBJECT-SLOT widener (the bucket-B fix).
# An invariant operator types fine but its `{x}` object slot used to bottom out
# at a tiny hand-atom list, so 'rank of E' / 'genus of the Neron-Severi group of
# X' / 'Euler characteristic of the quotient stack [U/G]' returned None. This
# recogniser types an unmatched object-slot token-run as a GENERIC OBJECT when it
# has a recognised OBJECT FORM — GENERALLY (the seeded object_type_nouns /
# notation_symbols / object_connectives vocabulary, not a regex per question):
#   (a) OBJECT-TYPE-NOUN head: the run contains a seeded object-type-noun
#       ('group'/'space'/'stack'/'manifold'/'curve'/'subgroup'/...) -> typed as
#       that object-type (longest/most-specific head wins). The tail (a notation
#       like 'pi_3(X)' or an 'of Y' qualifier) is the object's parameters; it does
#       not need to type — the HEAD noun fixes the object kind.
#   (b) PURE NOTATION/SYMBOL run: every token is a notation symbol (a single-letter
#       atom, a digit, a Greek name) or an object connective ('times'/'oplus') —
#       e.g. 'pi 3 x' / 'h 2 g m' / 'u g' / 'e q' / 't times t' — typed as a
#       notation object (term 'object', notation surface kept).
# PRECISION (zero false-positive lever): a run with a non-symbol, non-type-noun
# WORD does NOT type (arbitrary prose stays an honest miss). The object types ->
# the clause types -> it flows to the held stack; where the stack has no compute
# for that object, it is an HONEST type-but-stall, now correctly TYPED.
# ---------------------------------------------------------------------------

def comprehend_object_atom(toks: list[str], grammar: dict) -> Optional[dict]:
    """Type an object-slot token-run as a GENERIC OBJECT by its OBJECT FORM (the
    bucket-B object-slot widener). Returns {term, held, object_type, notation,
    generic_object:True} when the run is a recognised object form, else None.
    General (seeded vocabulary), precise (non-object prose -> None)."""
    low = [t.lower() for t in toks if t]
    if not low:
        return None
    # (a) OBJECT-TYPE-NOUN head — the run CONTAINS a seeded object-type-noun as a
    # contiguous sub-run (longest head first, most-specific wins: 'homotopy group'
    # over 'group'). The type-noun fixes the object kind; the rest is parameters.
    type_nouns = sorted(grammar.get("object_type_nouns", []),
                        key=lambda b: -len(b.get("head", [])))
    for tn in type_nouns:
        head = [h.lower() for h in tn.get("head", [])]
        if not head:
            continue
        h = len(head)
        for i in range(len(low) - h + 1):
            if low[i:i + h] == head:
                return {"term": "object", "held": False,
                        "object_type": tn["type"],
                        "notation": " ".join(low), "generic_object": True}
    # (b) PURE NOTATION/SYMBOL run — every token is a notation symbol (single-letter
    # atom / Greek name), a digit, or an object connective. No bare WORD that is not
    # a symbol/connective (that would be un-typed prose -> stay a miss).
    symbols = {s.lower() for s in grammar.get("notation_symbols", [])}
    connectives = {c.lower() for c in grammar.get("object_connectives", [])}
    ok = True
    saw_symbol = False
    for t in low:
        if t.isdigit():
            continue
        if t in connectives:
            continue
        if t in symbols:
            saw_symbol = True
            continue
        # a single alphabetic letter not in the symbol table is still a bare
        # variable (E, J, ...) — admit it as a symbol; anything longer that is not
        # a seeded symbol/connective is prose -> reject (precision).
        if len(t) == 1 and t.isalpha():
            saw_symbol = True
            continue
        ok = False
        break
    if ok and saw_symbol:
        return {"term": "object", "held": False, "object_type": "notation",
                "notation": " ".join(low), "generic_object": True}
    return None


def _comprehend_structure(toks: list[str], grammar: dict, depth: int,
                          seen: frozenset,
                          env: Optional[dict] = None) -> Optional[dict]:
    """Comprehend a token list into a STRUCTURE TREE node:
        {op, args:[child...], held_runnable}  for an operator construction, or
        {term, held}                          for an atomic bedrock term.
    Operator slots are comprehended RECURSIVELY (the order-N step). Returns None
    (honest un-comprehension) when nothing matches. A possessive 'its <X>' in an
    infix's right slot resolves to the SAME operand the left slot's head reads
    (so 'kernel of ∂ modulo its image' -> image(∂)).

    `env` — the LOCAL TYPED ENVIRONMENT (a stem's bound symbols). An atom-slot
    token run is resolved against it FIRST (a stem-introduced object), before the
    seeded global atoms. This is what lets Δ_k bottom out as a typed object."""
    env = env or {}
    if depth > _MAX_COMPREHEND_DEPTH or not toks:
        return None
    key = (depth, tuple(toks))
    if key in seen:
        return None
    seen = seen | {key}
    low = [t.lower() for t in toks]

    # POSTFIX TYPING QUALIFIER ('[head] as a free group') — a TRAILING literal
    # sequence that RE-TYPES the head it modifies (rank -> free_rank). Try it FIRST
    # (longest-pattern-first) so the qualifier is read as part of the structure: the
    # head (everything before the trailing pattern) is comprehended recursively, then
    # its ROOT op is re-typed per the qualifier's `retype` map. An UNQUALIFIED phrase
    # never matches here (no trailing qualifier) -> the head's op stands (the generic
    # `rank`), so the discrimination free_rank-vs-rank is the GRAMMAR'S, by the
    # qualifier. The qualifier only re-types a head it names; a non-matching head op
    # is left unchanged.
    for q in sorted(grammar.get("qualifiers", []),
                    key=lambda x: -len(x["pattern"])):
        pat = [p.lower() for p in q["pattern"]]
        n = len(pat)
        if n < len(low) and low[-n:] == pat:
            head = _comprehend_structure(toks[:-n], grammar, depth + 1, seen, env)
            if head is None or "op" not in head:
                continue
            retype = q.get("retype", {})
            new_op = retype.get(head["op"], head["op"])
            out = dict(head)
            out["op"] = new_op
            return out

    # INFIX operators ('[a] modulo [b]') — split on the infix literal, comprehend
    # both sides. Longest-literal first (greedy). Try each split point.
    for op in grammar.get("operators", []):
        pat = [p.lower() for p in op["pattern"]]
        # an infix pattern is {a} LIT {b}: find the single literal token.
        lits = [p for p in pat if not (p.startswith("{") and p.endswith("}"))]
        if len(lits) != 1 or len(pat) != 3 or pat[1] != lits[0]:
            continue
        lit = lits[0]
        for i in range(1, len(low) - 1):
            if low[i] != lit:
                continue
            left = _comprehend_structure(toks[:i], grammar, depth + 1, seen, env)
            if left is None:
                continue
            right_toks = toks[i + 1:]
            right = _resolve_possessive(right_toks, left, grammar, depth + 1,
                                        seen)
            if right is None:
                right = _comprehend_structure(right_toks, grammar, depth + 1,
                                              seen, env)
            if right is None:
                continue
            return {"op": op["op"], "args": [left, right],
                    "held_runnable": bool(op.get("held_runnable", False))}

    # INDEXED operators ('the n-th homology of [x]', 'the second betti number of
    # [x]') — the SAME prefix construction, one register wider: the pattern carries
    # an `{index}` slot the uniform index-reader reads (ordinal / symbolic / number)
    # into the typed tree's `index`, then the object slot `{x}` is comprehended
    # recursively. Tried before the plain-prefix loop so an indexed pattern wins
    # over a shorter bare one. Longest pattern first (greedy). The mechanism is
    # GENERAL: ANY operator with `indexed: true` + an `{index}`/`{x}` pattern reads
    # the index the same way — adding an indexed operator is a DATA ROW, not a
    # per-operator branch.
    for op in sorted([o for o in grammar.get("operators", [])
                      if o.get("indexed") and "{index}" in o.get("pattern", [])],
                     key=lambda o: -len(o["pattern"])):
        m = _match_indexed_operator(op, low, grammar, depth, seen, env, toks)
        if m is not None:
            return m

    # PREFIX operators ('kernel of [x]', 'image of [x]') — match the literal
    # prefix, comprehend the slot recursively. INDEXED operators are handled by the
    # dedicated indexed loop above (their `{index}` slot is not a plain prefix), so
    # skip them here to avoid the plain loop reading the index literal as the head.
    for op in sorted([o for o in grammar.get("operators", [])
                      if not o.get("indexed")],
                     key=lambda o: -len(o["pattern"])):
        pat = [p.lower() for p in op["pattern"]]
        if pat and pat[0].startswith("{"):
            continue   # infix handled above.
        pre = []
        for p in pat:
            if p.startswith("{"):
                break
            pre.append(p)
        if low[:len(pre)] != pre or len(low) <= len(pre):
            continue
        inner = _comprehend_structure(toks[len(pre):], grammar, depth + 1, seen,
                                      env)
        if inner is None:
            continue
        return {"op": op["op"], "args": [inner],
                "held_runnable": bool(op.get("held_runnable", False))}

    # ATOM bedrock — resolve the LOCAL TYPED ENVIRONMENT FIRST (a stem-introduced
    # object: Δ_k -> simplicial_complex because the stem bound it), then the
    # seeded global atoms ('the boundary operator'). The env resolution is the
    # cmsg-gap-1 fix: a bound symbol's token run bottoms out as its typed object.
    bound = env.get(tuple(low))
    if bound is not None:
        return {"term": bound["term"], "held": bool(bound.get("held", False)),
                "bound": True, "type": bound.get("type")}
    for at in sorted(grammar.get("atoms", []), key=lambda a: -len(a["pattern"])):
        if low == [p.lower() for p in at["pattern"]]:
            return {"term": at["term"], "held": bool(at.get("held", False))}
    # GENERIC OBJECT-ATOM fallback (the bucket-B object-slot widener) — tried LAST,
    # only when no seeded atom / bound symbol matched. Types the run as a generic
    # object by its OBJECT FORM (a recognised object-type-noun head, or a pure
    # notation/symbol run). Precise: non-object prose returns None and stays a miss.
    obj = comprehend_object_atom(toks, grammar)
    if obj is not None:
        return obj
    return None


def _read_index(toks: list[str], grammar: dict) -> Optional[dict]:
    """Read an INDEXED operator's {index} slot surface into a value, GENERALLY
    (the same reader for EVERY indexed operator — not a per-operator case).
    Recognises, against the seeded DATA tables:
      · an ORDINAL word  ('second' -> 2)                  [grammar.index_words]
      · a SYMBOLIC index ('n', 'k', optionally with a trailing ordinal suffix the
        tokeniser split off: 'n-th' -> ['n','th']) -> the symbol  [index_symbols]
      · a BARE NUMBER token ('2') -> the int
    Returns {value, symbolic} or None (unreadable surface). The {index} slot is a
    short run (one ordinal/symbol, perhaps + a split-off 'th'); we read the FIRST
    meaningful token and tolerate a trailing ordinal-suffix token."""
    low = [t.lower() for t in toks if t]
    if not low:
        return None
    suffixes = {s.lower() for s in grammar.get("index_ordinal_suffixes", [])}
    # tolerate a trailing ordinal-suffix token the tokeniser split off ('n','th').
    core = list(low)
    if len(core) >= 2 and core[-1] in suffixes:
        core = core[:-1]
    if len(core) != 1:
        # the index slot should resolve to a single ordinal/symbol/number token
        # (after dropping a split-off suffix); anything longer is not an index.
        return None
    tok = core[0]
    # ORDINAL word -> integer.
    for iw in grammar.get("index_words", []):
        if tok == str(iw.get("surface", "")).lower():
            return {"value": int(iw["value"]), "symbolic": False}
    # BARE NUMBER -> integer.
    if tok.isdigit():
        return {"value": int(tok), "symbolic": False}
    # SYMBOLIC index ('n', 'k', ...) -> the symbol.
    if tok in {s.lower() for s in grammar.get("index_symbols", [])}:
        return {"value": tok, "symbolic": True}
    return None


def _match_indexed_operator(op: dict, low: list[str], grammar: dict, depth: int,
                            seen: frozenset, env: dict,
                            toks: list[str]) -> Optional[dict]:
    """Match an INDEXED operator pattern (literals + an `{index}` slot + a final
    `{x}` object slot), GENERALLY. The pattern splits into: [pre-literals]
    {index} [mid-literals] {x}. We match the pre-literals, read the {index} run up
    to the next literal via the uniform _read_index, match the mid-literals, then
    comprehend the {x} object slot recursively. Returns the typed node
    {op, args:[object], index, held_runnable} or None. No per-operator code: the
    pattern + index DATA drive it; a new indexed operator is a row."""
    pat = [p.lower() for p in op["pattern"]]
    # locate the {index} and {x} slots; everything else is a literal.
    if "{index}" not in pat:
        return None
    # walk the pattern, consuming `low`, capturing slot runs up to the next literal.
    i = 0  # cursor into low
    index_node = None
    object_node = None
    for j, pt in enumerate(pat):
        is_slot = pt.startswith("{") and pt.endswith("}")
        if not is_slot:
            if i >= len(low) or low[i] != pt:
                return None
            i += 1
            continue
        # a slot: capture up to the next LITERAL token in the pattern (or end).
        nxt = None
        for k in range(j + 1, len(pat)):
            if not (pat[k].startswith("{") and pat[k].endswith("}")):
                nxt = pat[k]
                break
        start = i
        if nxt is None:
            i = len(low)
        else:
            while i < len(low) and low[i] != nxt:
                i += 1
        run = toks[start:i]
        if not run:
            return None
        if pt == "{index}":
            index_node = _read_index(run, grammar)
            if index_node is None:
                return None
        else:  # the object slot {x} (or any other) — comprehend recursively.
            object_node = _comprehend_structure(run, grammar, depth + 1, seen, env)
            if object_node is None:
                return None
    if i != len(low) or object_node is None:
        return None
    out = {"op": op["op"], "args": [object_node],
           "held_runnable": bool(op.get("held_runnable", False))}
    if index_node is not None:
        out["index"] = index_node["value"]
        out["index_symbolic"] = bool(index_node["symbolic"])
    return out


def _resolve_possessive(toks: list[str], sibling: dict, grammar: dict,
                        depth: int, seen: frozenset) -> Optional[dict]:
    """Resolve a possessive 'its <OP>' (e.g. 'modulo its image') against the
    SIBLING operand: the possessive refers to the same atomic operand the sibling
    operates on. 'its image' with sibling kernel(∂) -> image(∂)."""
    low = [t.lower() for t in toks]
    if not low or low[0] != "its":
        return None
    # the referenced operand = the deepest atomic term under the sibling.
    operand = _deepest_atom(sibling)
    if operand is None:
        return None
    op_toks = toks[1:]
    op_low = [t.lower() for t in op_toks]
    for op in grammar.get("operators", []):
        pat = [p.lower() for p in op["pattern"]]
        if pat and pat[0].startswith("{"):
            continue
        # 'its image' -> the prefix-op whose literal head matches (image/kernel).
        lits = [p for p in pat if not p.startswith("{")]
        if lits and op_low[:1] == lits[:1]:
            return {"op": op["op"], "args": [dict(operand)],
                    "held_runnable": bool(op.get("held_runnable", False))}
    return None


def _deepest_atom(node: dict) -> Optional[dict]:
    """The atomic operand a structure node ultimately operates on (for possessive
    resolution): descend args to the first {term} leaf."""
    if not isinstance(node, dict):
        return None
    if "term" in node:
        return node
    for child in node.get("args", []):
        a = _deepest_atom(child)
        if a is not None:
            return a
    return None


def _structure_repr(node: dict) -> str:
    """Render a structure tree as op(args) — modulo(kernel(boundary_operator),
    image(boundary_operator))."""
    if "term" in node:
        return str(node["term"])
    args = ", ".join(_structure_repr(a) for a in node.get("args", []))
    if "index" in node:
        # an INDEXED operator renders its index in the slot: homology(space, 2).
        return f"{node['op']}({args}, {node['index']})"
    return f"{node['op']}({args})"


def _unheld_ops(node: dict, out: Optional[list] = None) -> list:
    """The OPERATIONS in a structure tree that are NOT held_runnable — the precise
    residual (acquirable by reading, the next instance). Order: outermost-first."""
    out = [] if out is None else out
    if "term" in node:
        return out
    if not node.get("held_runnable") and node["op"] not in out:
        out.append(node["op"])
    for child in node.get("args", []):
        _unheld_ops(child, out)
    return out


def _resolve_appositive(toks: list[str]) -> list[str]:
    """Resolve an APPOSITIVE coreference 'the <noun> <Var> = <definiens>' — a named
    object RESTATED by '=' (e.g. 'the kernel K = kernel of the hurewicz map'). The
    '=' binds the head noun-phrase-plus-variable to the definiens: they DENOTE the
    same object, so the head ('the kernel K') is READ AS the definiens ('kernel of
    the hurewicz map'). Returns the token list with the head-plus-'='-plus-LHS span
    collapsed to the definiens — the SAME 'Let X be Y' binding the preamble reader
    does, on the '=' surface. No '=' -> the tokens are returned unchanged.

    Tokens are the comprehend_structure tokenisation (lowercased word tokens; the
    '=' survives as a literal). The definiens runs from after '=' to the end of the
    token window (the window-slicer already trimmed any trailing aside)."""
    if "=" not in toks:
        return toks
    eq = toks.index("=")
    # the LHS head is the noun-phrase before '=' (ending in a bound variable like a
    # single letter); the definiens is everything after '='. Replace the entire
    # 'head = definiens' span with the definiens (the coreference resolution). We
    # keep any tokens BEFORE the head noun phrase that the '=' does not bind — here
    # the head noun phrase is the maximal 'the <noun> <var>' run ending at '='; we
    # find its start as the last article ('the'/'a'/'an') before '='.
    articles = {"the", "a", "an"}
    start = 0
    for i in range(eq - 1, -1, -1):
        if toks[i] in articles:
            start = i
            break
    definiens = toks[eq + 1:]
    return toks[:start] + definiens


# ---------------------------------------------------------------------------
# DEFINITION-BINDING — read a STEM's object INTRODUCTIONS into a LOCAL TYPED
# ENVIRONMENT (the cmsg-gap-1 fix). A stem introduces its objects ('Let X be a
# <type>', 'Let X denote the <type>', 'We denote by X the <type>'); the reader
# binds each symbol to a TYPED object. The invariant's `{object}` slot then
# RESOLVES against this environment — Δ_k types as an object because the STEM
# introduced it as one, NOT because Δ_k is in a global atom list. GENERAL: any
# introduced object (K_k a complete_graph, a fresh 'Let G be a group') binds the
# SAME way. The binding-clause patterns + the type vocabulary are graph DATA
# (seeds/math_prose_constructions.json binding_clauses / binding_types); this
# function only applies them (the SAME mechanical pattern->frame translation the
# rest of the grammar is). No regex per question, no hand-atom-list.
# ---------------------------------------------------------------------------

def _sym_tokens(surface: str) -> list[str]:
    """The comprehend_structure token form of a bound SYMBOL surface. A bound
    symbol like 'K_k' / 'Delta_k' tokenises (under the structure tokeniser
    r'[a-z0-9]+') to ['k', 'k'] / ['delta', 'k'] — the SAME token run the object
    slot will present. We store the symbol by that token tuple so the slot
    resolves by the reader's own tokenisation (not a raw-string compare)."""
    return re.findall(r"[a-z0-9]+", (surface or "").lower())


def _normalise_binding_type(type_surface: str, grammar: dict) -> Optional[str]:
    """Normalise a binding clause's <type> surface to a STRUCTURAL object-type by
    matching a HEAD type-noun from the seeded `binding_types` (longest head first).
    'abstract simplicial complex defined as follows' -> simplicial_complex;
    'complete graph on k vertices' -> complete_graph. A trailing qualifier ('on k
    vertices', 'defined as follows') is ignored — the head type-noun drives. Graph
    data, not a per-question rule. Returns the type, or None (un-typed head)."""
    low = _sym_tokens(type_surface)
    if not low:
        return None
    bts = sorted(grammar.get("binding_types", []),
                 key=lambda b: -len(b.get("head", [])))
    for bt in bts:
        head = [h.lower() for h in bt.get("head", [])]
        if not head:
            continue
        # the head type-noun must appear as a contiguous run anywhere in the type
        # surface (the surface is '<adjs> <head-noun> <trailing qualifier>').
        n = len(head)
        for i in range(len(low) - n + 1):
            if low[i:i + n] == head:
                return bt["type"]
    return None


def comprehend_definitions(stem: str) -> dict[tuple, dict]:
    """Read a STEM's binding clauses into a LOCAL TYPED ENVIRONMENT. Applies the
    seeded `binding_clauses` patterns over each sentence of the stem; each match
    binds a SYMBOL (by its structure-token tuple) to a typed object (the
    normalised `binding_types`). Returns {sym_token_tuple -> {term, held, type,
    surface, type_surface}}. GENERAL: every 'Let X be/denote a/the <type>' and
    'We denote by X the <type>' in the stem binds, not just Δ_k. The environment
    is what comprehend_structure resolves the object slot against."""
    env: dict[tuple, dict] = {}
    if not stem:
        return env
    grammar = load_math_prose()
    clauses = grammar.get("binding_clauses", [])
    for sent in _split_sentences(stem) or [stem]:
        toks = _tok(sent)
        if not toks:
            continue
        # try each binding pattern (longest pattern first so 'be the' wins over
        # 'be a' where both could fit). The generic _match captures the {sym} +
        # {type} slots; we then normalise the type to a structural object-type.
        for c in sorted(clauses, key=lambda x: -len(x["pattern"])):
            binds = _match_prefix(c["pattern"], toks)
            if binds is None:
                continue
            sym_surface = binds.get(c.get("sym", "sym"), "")
            type_surface = binds.get(c.get("type", "type"), "")
            otype = _normalise_binding_type(type_surface, grammar)
            if otype is None:
                continue
            key = tuple(_sym_tokens(sym_surface))
            if not key:
                continue
            # the bound object's `term` IS its structural type — the object slot
            # bottoms out here (held=False: a NAMED introduced object, like the
            # seeded `space` atom, not a held-runnable computed object).
            env.setdefault(key, {
                "term": otype, "held": False, "type": otype,
                "surface": sym_surface.strip(),
                "type_surface": re.sub(r"\s+", " ", type_surface).strip()})
    return env


def _match_prefix(pattern: list[str], toks: list[str]) -> Optional[dict]:
    """Match a binding pattern as a PREFIX of the sentence's tokens (the binding
    clause leads the sentence: 'Let X denote the <type> defined as follows: ...').
    A trailing '{type}' slot captures the rest of the sentence up to a clause
    boundary the type normaliser then trims to its head noun. Reuses the generic
    slot semantics of _match, but allows tokens to remain after the last slot."""
    binds: dict[str, str] = {}
    i = 0
    for j, pt in enumerate(pattern):
        is_slot = pt.startswith("{") and pt.endswith("}")
        if is_slot:
            slot = pt[1:-1]
            nxt = None
            for k in range(j + 1, len(pattern)):
                if not (pattern[k].startswith("{") and pattern[k].endswith("}")):
                    nxt = pattern[k].lower()
                    break
            cap: list[str] = []
            if nxt is None:
                # the LAST slot captures to the end (the type runs to the clause
                # boundary; the normaliser trims to the head noun).
                while i < len(toks):
                    cap.append(toks[i]); i += 1
            else:
                while i < len(toks) and toks[i].lower() != nxt:
                    cap.append(toks[i]); i += 1
            if not cap:
                return None
            binds[slot] = " ".join(cap)
        else:
            if i >= len(toks) or toks[i].lower() != pt.lower():
                return None
            i += 1
    return binds


def comprehend_structure(prose: str,
                         env: Optional[dict] = None) -> Optional[dict]:
    """ORDER-N comprehension of RESEARCH prose into a STRUCTURE TREE — composing
    operator constructions recursively, bottoming out at atomic held terms. The
    flat matcher returns NONE on such prose; here it COMPOSES the structure (and
    NAMES the un-held operations — the residual). An APPOSITIVE coreference
    ('the kernel K = kernel of the hurewicz map') is resolved first (the '=' binding
    — the held coreference, not a bespoke pattern).

    `env` — an optional LOCAL TYPED ENVIRONMENT (comprehend_definitions output):
    symbol-token-tuple -> typed object. The object slot resolves a BOUND symbol
    against it FIRST (the stem introduced it), before the seeded global atoms.
    This is the cmsg-gap-1 fix: Δ_k types because the stem bound it. Returns
        {structure, repr, unheld_ops, atoms_held, comprehends}
    or None (un-comprehended)."""
    if not prose:
        return None
    grammar = load_math_prose()
    toks = re.findall(r"[a-z0-9]+|=", prose.lower())
    toks = _resolve_appositive(toks)
    node = _comprehend_structure(toks, grammar, 0, frozenset(), env or {})
    if node is None:
        return None
    return {"structure": node, "repr": _structure_repr(node),
            "unheld_ops": _unheld_ops(node),
            "atoms_held": _deepest_atom(node) is not None
            and _deepest_atom(node).get("held", False),
            "comprehends": True}


# ---------------------------------------------------------------------------
# HARVEST OBJECT-LEVEL FACTS — the agent's construction grammar mining the
# COMPUTED-INVARIANT + IDENTIFICATION facts HLE needs out of frontier (arXiv)
# prose. This is the SAME machinery shape as the math-prose / definition
# constructions: the patterns are graph DATA (seeds/math_fact_harvest.json), the
# harvester applies whichever patterns are seeded — NO hand-coded per-fact rule,
# NO LLM. Teaching a new fact shape = adding a pattern (data), not code.
#
# What it captures (the detail nLab LACKED — 147 computed-invariant pages of
# 19,097; now flowing from arXiv at a measured rate):
#   · COMPUTED INVARIANTS: 'H_n(X) isomorphic to Z' / 'the homology group of X
#     is G' / 'the rank of H_2 is 3' -> {object, invariant_kind, value}.
#   · IDENTIFICATIONS: 'X is homeomorphic/diffeomorphic/isomorphic/equivalent to
#     Y' / 'X is the classifying space of G' -> {object, relation, target}.
# These feed the analysis-by-synthesis math_hat LIBRARY (object -> properties /
# invariants) + the derivation engine's knowledge + the read_and_ground stack.
#
# HONEST: the patterns are ANCHORED (a named homology/homotopy operator on the
# object side; a copula/iso marker; a concrete group/value on the value side) to
# FAVOUR precision over recall — author prose is noisy (hypotheses, variable
# invariants). The precision is the measured residual; report it, do not fake.
# ---------------------------------------------------------------------------


def load_fact_harvest(path: Path = _FACT_HARVEST) -> dict:
    """Load the fact-harvest PATTERNS (graph data). {invariants:[...],
    identifications:[...]}; empty families on a read miss."""
    try:
        g = json.loads(Path(path).read_text())
    except Exception:
        return {"invariants": [], "identifications": []}
    return {"invariants": g.get("invariants", []),
            "identifications": g.get("identifications", [])}


def _clean_slot(s: str) -> str:
    """Tidy a captured object/value surface: collapse whitespace, strip stray
    punctuation/brackets, drop a leading article + a leading discourse
    connective ('Then'/'Thus'/'Every'/...) the greedy match dragged in. A
    surface-normalisation (the lexicon convention), NOT a meaning decision."""
    t = re.sub(r"\s+", " ", (s or "")).strip().strip(" ,.;:").strip()
    # drop a leading discourse connective + article the left-object grab pulled in
    # ('Then M^4' -> 'M^4'; 'Every leaf of' handled by the dangling-prep reject).
    t = re.sub(r"^(?:then|thus|so|hence|therefore|now|moreover|indeed|"
               r"clearly|every|each|the|a|an|that|this)\s+", "", t,
               flags=re.IGNORECASE)
    t = re.sub(r"^(the|a|an)\s+", "", t, flags=re.IGNORECASE)
    return t.strip()


# value-shapes a CONCRETE computed invariant takes (the value side of an
# object->invariant fact): a group (Z / Z/2 / Z_2 / Z^r / Q / Z times Z / 0), a
# number, a named space. A QUALITATIVE predicate ('computable' / 'nilpotent' /
# 'finitely generated' / 'trivial'-as-adjective) is NOT a concrete computed value
# — it is a property, rejected so the harvested INVARIANT rows are real values
# (the precision lever; the qualitative residual is named, not faked).
_QUALITATIVE_VALUES = {
    "computable", "effectively", "finitely", "generated", "nilpotent",
    "bounded", "free", "abelian", "cyclic", "torsion", "nontrivial",
    "nondegenerate", "smooth", "compact", "connected", "simply", "class",
    "above", "below", "infinite", "unbounded", "constant", "well", "defined",
    "surjective", "injective", "bijective", "continuous", "open", "closed"}


def _concrete_value(v: str) -> bool:
    """True iff a captured invariant VALUE is a CONCRETE computed answer (a group
    / number / named object), not a qualitative property word. '0', 'Z_2', 'Z^r',
    'Z times Z', 'Q' pass; 'computable', 'finitely generated' fail."""
    t = _clean_slot(v)
    if not t:
        return False
    words = [w for w in re.findall(r"[A-Za-z]+", t.lower())]
    if words and all(w in _QUALITATIVE_VALUES for w in words):
        return False
    # a bare number, or a value carrying a group/space symbol, is concrete.
    if re.fullmatch(r"-?\d+", t):
        return True
    if re.search(r"[ZQRCNzZ0-9/^_]|times|oplus|otimes|wedge|sphere|"
                 r"ball|torus|space|P\^|S\^|R\^|C\^", t):
        return True
    return False


def _plausible_object(s: str) -> bool:
    """A captured slot is a plausible math OBJECT/value: non-empty, not pure
    filler, balanced brackets, not a mid-token fragment, has an alphanumeric
    token. The anchored honest floor — a noisy capture (only stop-words, a
    fragment starting mid-expression like ')^n-orbit', or an unbalanced-paren
    grab) is REJECTED. This is the precision lever: prefer a clean object over a
    truncated one (recall traded for precision, the honest residual)."""
    t = _clean_slot(s)
    if not t or len(t) > 80:
        return False
    if not re.search(r"[A-Za-z0-9]", t):
        return False
    # a capture that OPENS with a closing bracket / stray operator is a
    # mid-expression fragment (the greedy-match residual) — reject it.
    if t[0] in ")]}^_/,;:":
        return False
    # balanced (round) brackets — an unbalanced grab ran past / short of a
    # delimiter; the object boundary is wrong.
    if t.count("(") != t.count(")"):
        return False
    # reject a capture that is ONLY connective/filler words.
    filler = {"is", "are", "and", "or", "the", "a", "an", "of", "to", "be",
              "this", "that", "it", "we", "such", "some", "any", "then",
              "where", "which", "for", "if", "with", "so", "thus", "hence",
              "note", "one", "groups", "let", "given", "above", "below",
              "bounded"}
    words = [w for w in re.findall(r"[A-Za-z0-9]+", t.lower())]
    if not words:
        return False
    if all(w in filler for w in words):
        return False
    # a phrase ending in a dangling preposition/connective is a truncated grab.
    if words[-1] in {"of", "to", "in", "on", "the", "a", "an", "over", "for",
                     "with", "and", "or"}:
        return False
    # a clausal connective INSIDE the capture ('... such that ...', '... to X
    # ...') means the grab crossed a clause boundary — a fragment, reject.
    low = " " + t.lower() + " "
    if re.search(r"\b(such that|to which|in which|so that|note that)\b", low):
        return False
    # a left/right object should not OPEN with a bare lower-case word fragment
    # whose first letters look truncated ('ssociated', 'estricted') — heuristic:
    # a single long lower-case opening word that is not a known math token and
    # not in a small math-word whitelist is likely a chopped word. Conservative:
    # only reject when the WHOLE capture is one lower-case alpha word > 6 chars.
    if (len(words) == 1 and t.islower() and t.isalpha() and len(t) > 6
            and t not in {"boundary", "manifold", "cohomology", "homology",
                          "homotopy", "spectrum", "spectra", "category",
                          "morphism", "operator", "subspace", "subgroup"}):
        return False
    # the OPENING word must not be a SUFFIX-fragment of a relation/connective
    # keyword the regex matched mid-word ('...is iSOMORPHIC to' -> 'somorphic';
    # '...aSSOCIATED to' -> 'ssociated'). A chopped opener = a fragment grab.
    first = words[0]
    _CHOP = ("somorphic", "omorphic", "morphic", "iffeomorphic", "ffeomorphic",
             "quivalent", "uivalent", "ssociated", "ssociate", "estricted",
             "efined", "enoted", "iven", "ndowed", "quipped")
    if first in _CHOP:
        return False
    return True


def harvest_invariants(prose: str, patterns: Optional[list] = None) -> list[dict]:
    """Harvest COMPUTED-INVARIANT facts from a prose statement via the seeded
    invariant patterns. Returns [{object, invariant_kind, value, pattern}], the
    object->invariant->value rows. Each pattern is graph data: an object_re
    anchor (a homology/homotopy/rank operator on a space), an optional joiner_re
    (the iso/equality marker), and a value_re (the concrete group/number). Empty
    list = no anchored invariant found (the honest miss)."""
    if not prose:
        return []
    pats = patterns if patterns is not None else load_fact_harvest()["invariants"]
    text = re.sub(r"\s+", " ", prose)
    out: list[dict] = []
    seen: set = set()
    for p in pats:
        obj_re = p.get("object_re")
        val_re = p.get("value_re")
        if not obj_re or not val_re:
            continue
        join = p.get("joiner_re", "")
        full = obj_re + join + val_re
        try:
            rx = re.compile(full)
        except re.error:
            continue
        for m in rx.finditer(text):
            grps = [g for g in m.groups() if g is not None]
            if not grps:
                continue
            # the LAST captured group is the value; the rest are object parts.
            value = _clean_slot(grps[-1])
            obj_parts = [_clean_slot(g) for g in grps[:-1] if _clean_slot(g)]
            obj = " ".join(obj_parts).strip()
            kind = p.get("kind", "invariant")
            # a templated kind ('{group_kind}') resolves to the first captured
            # object part (the invariant-kind word, e.g. 'homology').
            if kind.startswith("{") and obj_parts:
                kind = obj_parts[0].lower()
                obj = " ".join(obj_parts).strip()
            if not _plausible_object(obj) or not _plausible_object(value):
                continue
            # the value of a COMPUTED invariant must be a concrete answer (a
            # group / number / named object), not a qualitative property word.
            if not _concrete_value(value):
                continue
            key = (obj.lower(), kind, value.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append({"object": obj, "invariant_kind": kind,
                        "value": value, "pattern": p.get("name", "")})
    return out


def harvest_identifications(prose: str,
                            patterns: Optional[list] = None) -> list[dict]:
    """Harvest IDENTIFICATION facts (object IS homeomorphic / diffeomorphic /
    isomorphic / equivalent / identified-with / classifying-space-of another
    object) via the seeded identification patterns. Returns [{object, relation,
    target, pattern}]. Empty list = no anchored identification (honest miss)."""
    if not prose:
        return []
    pats = (patterns if patterns is not None
            else load_fact_harvest()["identifications"])
    text = re.sub(r"\s+", " ", prose)
    out: list[dict] = []
    seen: set = set()
    for p in pats:
        left_re = p.get("left_re")
        right_re = p.get("right_re")
        if not left_re or not right_re:
            continue
        try:
            rx = re.compile(left_re + right_re)
        except re.error:
            continue
        for m in rx.finditer(text):
            grps = [g for g in m.groups() if g is not None]
            if len(grps) < 2:
                continue
            left = _clean_slot(grps[0])
            right = _clean_slot(grps[-1])
            if not _plausible_object(left) or not _plausible_object(right):
                continue
            rel = p.get("relation", "identified_with")
            key = (left.lower(), rel, right.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append({"object": left, "relation": rel, "target": right,
                        "pattern": p.get("name", "")})
    return out


def harvest_facts(prose: str) -> dict:
    """Harvest BOTH families from one statement's prose. Returns
    {invariants:[...], identifications:[...]} — the object-level facts the agent's
    construction grammar mined. The harvest entry point the arXiv pipeline calls
    over each parsed statement."""
    return {"invariants": harvest_invariants(prose),
            "identifications": harvest_identifications(prose)}


# ---------------------------------------------------------------------------
# THE CLAIM REPRESENTATION — ground a LOGICAL/QUANTIFIED statement AS A CLAIM
# (the frontier the WALK named: a NON-genus-differentia grounding for the
# existential/universal/TFAE/adjunction residual the definition-metric got 0 on).
#
# The agent NAMED the structure (cmsg82): a CLAIM grounds into a TYPED structure,
# NOT 'object IS-A genus' —
#   · QUANTIFIER     — forall / exists / TFAE / a RELATION (left-adjoint), READ off
#                      the agent's HELD CONSTRUCTION_TYPE_VOCAB quantifier markers
#                      (the SAME recognition the WALK uses to NAME the type).
#   · BOUND VARIABLE — the variable the quantifier binds (X, Z, n) — the token(s)
#                      right after the quantifier marker, before the DOMAIN/PREDICATE.
#   · DOMAIN         — what the variable ranges over ('in C', 'in 1..n', 'finite
#                      groups') — the 'in/of' restrictor following the variable.
#   · PREDICATE      — the property/relation asserted, RECURSIVELY comprehended by
#                      the SAME reader stack (harvest_facts for object->invariant /
#                      identification content; extract_definition for an inner
#                      'is-a'). The predicate is the comprehended sub-structure.
#
# This composes the agent's OWN held pieces (the quantifier recognition + the
# harvester/recursive comprehension); it MINTS no new surface vocabulary. The KEY
# property the representation buys: the claim is INSTANTIABLE — bind the variable
# to a specific object and the predicate becomes a goal the derivation engine
# evaluates (the bridge to the library/engine). Returns None when no held
# quantifier marker is present (the honest non-claim case).
# ---------------------------------------------------------------------------

# quantifier marker -> the canonical KIND. Read off the held CONSTRUCTION_TYPE_VOCAB
# (the agent's own quantifier recognition) so this stays one source of truth: the
# logical types' `quantifiers` lists are exactly the markers the WALK recognises.
def _quantifier_markers() -> list[tuple[str, str]]:
    """(marker, kind) pairs from the held logical CONSTRUCTION_TYPE_VOCAB entries —
    the agent's OWN quantifier recognition, longest-marker-first so 'for every'
    wins over 'for'. kind = forall / exists / tfae / adjunction (the vocab key
    stem). NOT a new list — a read of the held vocab."""
    kind_of = {"universal_claim": "forall", "existential_claim": "exists",
               "tfae_claim": "tfae", "adjunction_claim": "adjunction"}
    out: list[tuple[str, str]] = []
    for key, kind in kind_of.items():
        for q in CONSTRUCTION_TYPE_VOCAB.get(key, {}).get("quantifiers", []):
            out.append((q.lower(), kind))
    return sorted(out, key=lambda t: -len(t[0]))


# domain restrictor markers: the variable's range follows one of these ('for all X
# IN C', 'for every n >= 1', 'for all finite groups G'). A held closed family (the
# same register as the differentia markers); no per-claim decision.
_DOMAIN_MARKERS = ("in", "of", "over", "on", "with", "from")


def _split_var_domain(tail: str) -> tuple[str, str]:
    """Split the post-quantifier tail into (bound VARIABLE, DOMAIN). The variable is
    the leading noun phrase; the domain is the 'in/of/over ...' restrictor that
    follows it (or, for 'for all <kind> X', the kind is the domain and the trailing
    symbol the variable). A surface split (the same shape as the genus/differentia
    boundary), NOT a meaning decision."""
    t = re.sub(r"\s+", " ", (tail or "")).strip().strip(",")
    if not t:
        return "", ""
    low = t.lower().split()
    # 'for all X in <domain>' / 'for all X with <domain>' -> var before, domain after.
    for i, w in enumerate(low[1:], start=1):
        if w in _DOMAIN_MARKERS:
            var = " ".join(t.split()[:i]).strip(" ,")
            dom = " ".join(t.split()[i + 1:]).strip(" ,")
            return var, dom
    # 'for all n >= 1' / 'for all n > 0' — the variable then a numeric range domain.
    m = re.match(r"^([A-Za-z][A-Za-z0-9_'^]*)\s*([<>=].*)$", t)
    if m:
        return m.group(1), m.group(2).strip()
    # 'for all finite groups G' — a multi-word KIND then a trailing 1-2 char symbol:
    # the kind is the domain, the symbol the variable.
    toks = t.split()
    if len(toks) >= 2 and re.fullmatch(r"[A-Za-z][A-Za-z0-9_'^]?", toks[-1]):
        return toks[-1], " ".join(toks[:-1]).strip(" ,")
    # bare variable, no explicit domain (the range is inherited / universe).
    return toks[0], ""


def extract_claim(text: str, *, term: Optional[str] = None) -> Optional[dict]:
    """COMPREHEND a logical/quantified statement INTO the CLAIM REPRESENTATION the
    agent named — {quantifier, kind, variable, domain, predicate} — composing the
    agent's HELD quantifier-recognition + harvester + recursive comprehension. The
    predicate is itself comprehended (harvest_facts -> object->invariant /
    identification rows; extract_definition -> an inner is-a) so the asserted
    content is structured, not raw text. Returns None when no held quantifier
    marker is present (the honest non-claim case — a plain definition or un-read
    prose). The KEY property: the result is INSTANTIABLE (bind `variable` -> the
    predicate becomes a goal the derivation engine evaluates)."""
    if not text:
        return None
    # work over the claim's statement sentence(s); a quantifier can lead any one.
    # The WHOLE text is tried FIRST so a TFAE/adjunction marker is not split across
    # the '; ' / ': ' sentence boundary inside its own list of conditions.
    sents = [re.sub(r"\s+", " ", text).strip()] + (_split_sentences(text) or [text])
    markers = _quantifier_markers()
    for sent in sents:
        norm = re.sub(r"\s+", " ", sent).strip()
        mlow = norm.lower()
        for marker, kind in markers:
            # the marker must sit on a word boundary (start-or-space before, and
            # space/colon/comma/end after) — so 'for' inside 'before' never matches
            # but 'the following are equivalent:' does.
            mi = -1
            for m in re.finditer(re.escape(marker), mlow):
                a, b = m.start(), m.end()
                before_ok = a == 0 or mlow[a - 1] == " "
                after_ok = b >= len(mlow) or mlow[b] in " :,.;"
                if before_ok and after_ok:
                    mi = a
                    break
            if mi < 0:
                continue
            after = norm[mi + len(marker):].strip(" ,")
            # the PREDICATE is the assertion body — for forall/exists it follows the
            # variable's range (after the first comma OR the 'such that'); for TFAE /
            # adjunction the whole clause is the predicate (a list / a relation).
            variable, domain, predicate = "", "", after
            if kind in ("forall", "exists"):
                # the predicate begins after 'such that' (existential) or the first
                # top-level comma (universal) — the variable+domain precede it.
                cut = None
                st_pos = after.lower().find(" such that ")
                if st_pos >= 0:
                    cut = (st_pos, st_pos + len(" such that "))
                else:
                    cpos = after.find(",")
                    if cpos >= 0:
                        cut = (cpos, cpos + 1)
                if cut is not None:
                    head, predicate = after[:cut[0]], after[cut[1]:].strip()
                    variable, domain = _split_var_domain(head)
                else:
                    variable, domain = _split_var_domain(after)
                    predicate = after
            elif kind == "adjunction":
                # 'F is left adjoint to G' — the relation is the quantifier; the two
                # functors are the related objects (the predicate's content).
                predicate = norm
            elif kind == "tfae":
                predicate = norm   # a list of conditions; the claim is over the list.

            # RECURSIVELY COMPREHEND the predicate's content (the agent's harvester +
            # definition reader) — the asserted structure, not raw text.
            pfacts = harvest_facts(predicate)
            pdef = extract_definition(predicate, term=term)
            pred_struct = {
                "text": re.sub(r"\s+", " ", predicate).strip(),
                "invariants": pfacts["invariants"],
                "identifications": pfacts["identifications"],
            }
            if pdef and pdef.get("term") and pdef.get("genus"):
                pred_struct["isa"] = {"term": pdef["term"], "genus": pdef["genus"]}

            variable = _clean_slot(variable) if variable else ""
            domain = re.sub(r"\s+", " ", domain).strip(" ,") if domain else ""
            # a quantifier with NO readable bound variable AND no predicate content is
            # not a usable claim grounding (honest miss) — TFAE/adjunction excepted
            # (their structure is the list/relation, not a single bound variable).
            if kind in ("forall", "exists") and not variable:
                continue
            return {
                "kind": kind, "quantifier": marker,
                "variable": variable or None,
                "domain": domain or None,
                "predicate": pred_struct,
                "statement": norm,
            }
    return None


# ---------------------------------------------------------------------------
# GAP AS PART OF SPEECH — when no full construction matches, do NOT throw the
# sentence away. POS-type every token from the agent's OWN faculty (the grounded
# function-word classifier + Wiktionary POS slabs), disambiguated by LEFT CONTEXT
# (after a determiner/adjective -> noun; after a nominal/verbal head -> verb), and
# carry the content/unknown spans as TYPED GAPS (parts of speech) the agent can
# ground and reason over. A wh-word is the interrogative FOCUS. This is the gap-
# carrying parse the narrow whole-sentence matcher lacks; no hand-authored stoplist.
# ---------------------------------------------------------------------------
_WH_FOCUS = {"why": "reason", "what": "thing", "how": "manner", "when": "time",
             "where": "place", "which": "selection", "who": "agent", "whom": "agent"}
_CLOSED_POS = {"det": "determiner", "article": "determiner", "prep": "preposition",
               "postp": "postposition", "conj": "conjunction", "pron": "pronoun",
               "particle": "particle"}
_CONTENT_POS = ("noun", "verb", "adj", "adv")


def _wikt_posset(low: str) -> list:
    try:
        from . import wiktionary_reference as _wikt
        return _wikt.wiktionary_pos(low, "en") or []
    except Exception:
        return []


def _wikt_dom(low: str) -> Optional[str]:
    ps = _wikt_posset(low)
    return ps[0] if ps else None


def _typed_modal_word(substrate: Any, low: str) -> bool:
    """Read graph modal metadata when a surface has a content-POS homograph."""
    if substrate is None:
        return False
    agent = substrate if callable(getattr(substrate, "_concept_by_name", None)) else None
    graph = getattr(substrate, "s", substrate)
    inner = getattr(substrate, "inner", None) or getattr(graph, "_inner", None)
    try:
        if agent is not None:
            concept = agent._concept_by_name(low)
            attrs = dict(graph.node(concept)["attrs"]) if concept is not None else {}
        else:
            concepts = inner.nodes_where("Concept", "name", low) if inner else []
            if not concepts:
                concepts = [node for node in graph.nodes("Concept")
                            if str(graph.node(node)["attrs"].get(
                                "name") or "").lower() == low]
            typed = [node for node in concepts
                     if graph.node(node)["attrs"].get("semantic_role")
                     or graph.node(node)["attrs"].get("modality")]
            node = (typed or concepts or [None])[0]
            attrs = dict(graph.node(node)["attrs"]) if node is not None else {}
    except Exception:
        return False
    definition = (str(attrs.get("definition") or "") + " "
                  + str(attrs.get("description") or "")).lower()
    role = str(attrs.get("semantic_role") or attrs.get("modality") or "").lower()
    return (role in {"permission", "permission_modality", "ability_permission",
                     "ability", "epistemic_possibility"}
            or "modal" in definition or "deficiency cue" in definition)


def _pos_token(low: str, prev: Optional[str], nxt: Optional[str] = None,
               prev_low: Optional[str] = None,
               substrate: Any = None) -> tuple[str, Optional[str]]:
    """(role, pos) for one token from the agent's own POS faculty + left/right context."""
    if low in _WH_FOCUS:
        return ("focus", _WH_FOCUS[low])
    if low == "that":                                     # demonstrative / relativizer / determiner — by context
        nps = _wikt_posset(nxt) if nxt else []
        ndom = nps[0] if nps else None
        # RELATIVIZER first: after a nominal, "that" heading a clause whose next word CAN be a verb (or is a
        # subject pronoun/verb) is a relativizer — "a thing that moves", "the wall that you hit". This must
        # beat the determiner reading, because a noun/verb-ambiguous head like "moves" has noun as its
        # dominant Wiktionary sense and would otherwise mis-read "that" as a determiner ("that moves").
        if prev in ("noun", "pronoun") and ("verb" in nps or ndom in ("pron", "pronoun", "verb")):
            return ("function", "conjunction")            # relativizer
        if ndom == "noun":
            return ("function", "determiner")             # "that wall"
        return ("function", "pronoun")                    # demonstrative: "is that a failure"
    try:
        from . import function_word_reference as _fw
        c = _fw.classify(low, "en")
    except Exception:
        c = None
    cf = c.get("function") if c else None
    if cf in ("copula", "auxiliary", "aux"):          # is / was / are ... grammatical, not a content gap
        return ("function", cf)
    if cf in ("preposition", "postposition"):
        # the FUNCTION-WORD classifier (function_word_reference.classify) already resolves a
        # polysemous surface toward its role-bearing closed-class reading (_FUNCTION_PRIORITY
        # prefers preposition over conjunction/etc); trust that over Wiktionary's raw DOMINANT
        # (first-listed) sense below, which for some prepositions ('near': ['adj','adv','prep',
        # 'verb','noun','name']) lists a CONTENT sense first and would otherwise mis-type a real
        # preposition as a content adj/verb/noun (found on 'near' while grounding a spatial
        # constraint clause — "find the page ... NEAR the diagram" needs 'near' typed preposition
        # so its governed nominal is a constraint, not a stray content word). Narrow, ordering-only
        # fix to the SAME faculty parse_with_gaps already calls — no new tagger.
        return ("function", cf)
    # An interjection the vocabulary base holds as closed-class ("oh", "ah",
    # "hey" -- Brown UH) is typed before Wiktionary, whose first-listed sense
    # for some is a proper name ("Oh" -> name) and would make the turn's head a
    # noun ("Oh, cool." read as the command "cool").
    try:
        from . import vocabulary_base as _vb0
        _e0 = _vb0.lookup(low, substrate)
    except Exception:
        _e0 = None
    if _e0 and _e0.get("klass") == "closed" and _e0.get("pos") == "interjection":
        return ("function", "interjection")
    try:
        from . import wiktionary_reference as _wikt
        posset = _wikt.wiktionary_pos(low, "en") or []
    except Exception:
        posset = []
    if ("verb" in posset
            and (cf == "particle" or "noun" in posset or "adj" in posset)
            # Modal metadata licenses the auxiliary reading only where the
            # clause can syntactically host one. Inside a determiner/adjective
            # phrase the same homograph is nominal/adjectival (e.g. "the gap";
            # the graph may also describe gaps as a deficiency cue).
            and prev not in ("determiner", "adj")
            and _typed_modal_word(substrate, low)):
        return ("function", "auxiliary")
    dom = posset[0] if posset else None
    if dom in _CLOSED_POS:                             # you->pron, into->prep, the/your->det, if/or->conj
        return ("function", _CLOSED_POS[dom])
    if dom in _CONTENT_POS or dom == "name":          # the substantive ("name" = a proper noun)
        p = "noun" if dom == "name" else dom
        verb_context = (prev in ("noun", "pronoun", "verb", "auxiliary")
                        or (prev == "conjunction" and prev_low == "that")
                        or (prev == "preposition" and prev_low == "to"))
        adjective_context = prev in ("determiner", "adj")
        if ("verb" in posset
                and ("noun" in posset or "adj" in posset
                     or (prev == "preposition" and prev_low == "to"))
                and (verb_context or adjective_context)):
            # Ambiguous content words resolve from LEFT context. The earlier
            # noun/verb-only check missed adjective/verb homographs such as
            # participles: a verb after a subject pronoun is the matrix head
            # ("I learned ..."), while the same form before a nominal can
            # remain adjectival ("the learned skill"). Keep this a POS/syntax
            # decision; semantic disposition is still selected downstream.
            # A lexically ambiguous modifier in determiner/adjective context
            # remains adjectival. This uses only already-read left context and
            # avoids a second vocabulary lookup for every ambiguous token.
            if dom == "adj" and adjective_context:
                p = "adj"
            elif prev in ("determiner", "adj"):
                p = "noun"
            elif prev == "verb":
                # After a lexical predicate, a noun/verb homograph is the
                # direct complement unless syntax says otherwise. Auxiliary
                # chains are handled separately by their function-word POS;
                # infinitives after "to" are handled by the preposition case
                # below. Treating every post-verb homograph as another verb
                # loses ordinary objects ("needs power").
                p = "noun" if "noun" in posset else p
            elif prev in ("noun", "pronoun") or (prev == "conjunction" and prev_low == "that"):
                p = "verb"                                # subject precedes a verb; relativizer "that" heads one
            elif prev == "preposition" and prev_low == "to" and "verb" in posset:
                p = "verb"                                # infinitival "to run"
            elif prev in ("auxiliary", "aux") and "verb" in posset:
                p = "verb"                                # finite/modal auxiliary + verb
        return ("content", p)
    if cf:                                             # e.g. "a": Wiktionary's dominant sense is the letter;
        return ("function", cf)                        # the grounded classifier still knows it's a determiner
    # VOCABULARY BASE (seeds/vocabulary_base_en.json, 2026-10-10): a token no
    # other source typed -- a contraction ("i'm", "what's"), an interjection
    # ("wow", "hmm"), or any word on a checkout without the POS slab -- is
    # typed from the agent's held vocabulary before it becomes an untyped gap.
    try:
        from . import vocabulary_base as _vb
        entry = _vb.lookup(low, substrate)
    except Exception:
        entry = None
    if entry:
        pos = str(entry.get("pos") or "")
        if pos == "contraction":
            head = low.split("'")[0]
            if head in _WH_FOCUS:                      # "what's" = wh-focus + auxiliary
                return ("focus", _WH_FOCUS[head])
            parts = list(entry.get("expands") or [])
            # type a contraction by its FIRST part, the clause position it fills:
            # "i'm" / "it's" / "you're" open a declarative with a subject pronoun.
            # An auxiliary-first contraction ("don't", "can't", "isn't") is a
            # negated auxiliary, deliberately not the bare `auxiliary` that
            # speech_act_classify reads as polar-question inversion: "Don't
            # worry" is not a question; a real one ends in '?'.
            first = parts[0] if parts else "contraction"
            if first in ("auxiliary", "modal"):
                return ("function", "negated_auxiliary" if "negation" in parts else "contraction")
            return ("function", first)
        if _vb.is_function_word(entry):
            return ("function", "auxiliary" if pos == "modal" else pos)
        if pos in _CONTENT_POS:
            return ("content", pos)
    return ("gap", "by-position")                      # no POS anywhere -> a gap typed only by position


def parse_with_gaps(text: str, substrate: Any = None) -> dict:
    """Parse a sentence the held constructions did not cover into a frame of TYPED elements: an interrogative
    FOCUS + a function-word skeleton + the content/unknown spans carried as TYPED GAPS (parts of speech). The
    gaps are first-class objects the agent grounds and reasons over — not a wall handed back to a human."""
    toks = [t for t in text.replace("?", " ?").split() if t and t != "?"]
    lows = [t.lower().strip("?.!,;:") for t in toks]
    elements, focus, gaps, prev, prev_low = [], None, [], None, None
    for i, t in enumerate(toks):
        low = lows[i]
        nxt = lows[i + 1] if i + 1 < len(lows) else None
        role, pos = _pos_token(low, prev, nxt, prev_low, substrate)
        elements.append({"surface": t, "role": role, "pos": pos})
        if role in ("content", "function"):
            prev = pos
            prev_low = low
        if role == "focus" and focus is None:
            focus = pos
        elif role in ("content", "gap"):
            gaps.append({"surface": t, "pos": pos})
    # In an auxiliary-inversion polar question, keep a determiner-headed
    # object NP intact after the matrix verb. Local POS dominance can otherwise
    # turn its final noun/verb homograph into a second predicate ("Should we
    # use the north route?"). This is a clause-role repair, not topic or answer
    # selection; later cognition still requires graph grounding.
    if (text.strip().endswith("?") and elements
            and elements[0].get("role") == "function"
            and elements[0].get("pos") in ("auxiliary", "aux", "copula")):
        first_verb = next((i for i, item in enumerate(elements[1:], 1)
                           if item.get("role") == "content"
                           and item.get("pos") == "verb"), None)
        if first_verb is not None:
            determiner = next((i for i in range(first_verb + 1, len(elements))
                               if elements[i].get("role") == "function"
                               and elements[i].get("pos") == "determiner"), None)
            if determiner is not None:
                for index in range(determiner + 1, len(elements)):
                    item = elements[index]
                    if item.get("role") != "content":
                        continue
                    options = _wikt_posset(str(item.get("surface") or "")
                                           .strip(".,;:?!").lower())
                    if item.get("pos") == "verb" and "noun" in options:
                        item["pos"] = "noun"
                        previous = next((elements[j] for j in range(index - 1,
                                          determiner, -1)
                                         if elements[j].get("role") == "content"),
                                        None)
                        if previous is not None:
                            previous_options = _wikt_posset(
                                str(previous.get("surface") or "")
                                .strip(".,;:?!").lower())
                            if "adj" in previous_options:
                                previous["pos"] = "adj"
                        break
    # A wh-selection clause can end with an adverb that scopes the event
    # rather than filling the predicate's object slot ("Which rule fired
    # last?"). Resolve this from clause position and the lexicon's POS set;
    # do not let the temporal modifier become a nominal object and erase the
    # event-selection relation. The downstream graph still needs actual
    # event-history evidence before it can answer.
    if focus == "selection":
        selected_nominal = next((i for i, item in enumerate(elements)
                                 if item.get("role") == "content"
                                 and item.get("pos") == "noun"), None)
        predicate_index = next((i for i, item in enumerate(elements)
                                if selected_nominal is not None
                                and i > selected_nominal
                                and item.get("role") == "content"
                                and item.get("pos") == "verb"), None)
        trailing = next((i for i in range(len(elements) - 1,
                                          (predicate_index or -1), -1)
                         if elements[i].get("role") == "content"), None)
        if (predicate_index is not None and trailing is not None
                and trailing > predicate_index
                and elements[trailing].get("pos") in {"noun", "adj"}):
            trailing_options = _wikt_posset(
                str(elements[trailing].get("surface") or "")
                .strip(".,;:?!").lower())
            if "adv" in trailing_options:
                elements[trailing]["pos"] = "adv"
    # `that` opens a finite complement only when a subject nominal occurs
    # before the next predicate. This distinguishes a complementizer from a
    # determiner/demonstrative without sentence templates or lexical verb
    # lists; the language adapter supplies the POS sequence, cognition sees
    # only the resulting clause relation.
    for i, element in enumerate(elements):
        if (element["surface"].lower().strip(",.;:?!") != "that"
                or i == 0 or elements[i - 1].get("pos") != "verb"):
            continue
        rest = elements[i + 1:]
        predicate_index = next((j for j, item in enumerate(rest)
                                if (item.get("role") == "content"
                                    and item.get("pos") == "verb")
                                or (item.get("role") == "function"
                                    and item.get("pos") in ("copula", "auxiliary"))),
                               None)
        if predicate_index is not None and any(
                _is_nominal(item) for item in rest[:predicate_index]):
            element["role"], element["pos"] = "function", "complementizer"
    gaps = [{"surface": element["surface"], "pos": element["pos"]}
            for element in elements if element.get("role") in ("content", "gap")]
    return {"parsed": True, "focus": focus, "elements": elements, "gaps": gaps}


# ---------------------------------------------------------------------------
# DIRECTIVE GOVERNANCE — for a "find X near Y" style directive, POS-type every
# token (the SAME _pos_token classifier parse_with_gaps uses) plus a LEFT-CONTEXT
# GOVERNANCE walk: for each content NOUN, which preposition (if any) most recently
# introduced it, skipping only transparent determiners. This is a POSITIONAL /
# SYNTACTIC fact (nearest-preposition-before, the same left-context style
# _pos_token itself already uses to disambiguate noun/verb) — NOT a decision about
# what the preposition MEANS (target-describing 'about' vs constraining 'near' is
# the agent's authored rule's call, reading `gov_prep` off held vocabulary). The
# mechanical ingest boundary stamps this onto Mentions, the same way it stamps POS.
# ---------------------------------------------------------------------------
def parse_directive_elements(text: str) -> list[dict]:
    """POS-type (parse_with_gaps) + GOVERNANCE-stamp a directive's tokens. Returns
    parse_with_gaps' `elements` list, each content-noun element additionally
    carrying `gov_prep` (the governing preposition's lowercased surface, or None
    for a bare/direct-object nominal — 'find the PAGE about volcanoes' -> page's
    gov_prep is None, volcanoes' is 'about')."""
    elements = parse_with_gaps(text).get("elements", [])
    gov: Optional[str] = None
    for e in elements:
        role, pos = e.get("role"), e.get("pos")
        if role == "function" and pos in ("preposition", "postposition"):
            gov = e["surface"].lower().strip(",.;:?!")
            continue
        if role == "content" and pos in ("verb", "adj", "adv"):
            gov = None            # a new predicate/modifier head closes the governance span
            continue
        if role == "content" and pos == "noun":
            e["gov_prep"] = gov
    return elements


# ---------------------------------------------------------------------------
# COMPOSE THE FOCUS OVER THE GAPS — turn the typed-gap frame into a RELATION among
# the (now grounded) concepts: a predicate (the main content verb, else the copula)
# with its SUBJECT (the nearest nominal before it) and OBJECT / OBLIQUE (the nominal
# after it, direct vs after-a-preposition). The wh FOCUS is the query over that
# relation. This consumes the typed gaps natively (constituents delimited by the
# function-word skeleton) — the structured comprehension the 7-pattern matcher gave
# only for its fixed shapes, now for an arbitrary one. Single-clause; a multi-clause
# sentence needs the recursive composer (comprehend_recursive) — reported, not faked.
# ---------------------------------------------------------------------------
def _is_nominal(e: dict) -> bool:
    return (e["role"] == "content" and e["pos"] == "noun") or \
           (e["role"] == "function" and e["pos"] == "pronoun")


_SUBORDINATORS = {"when", "if", "because", "so", "although", "while", "since",
                  "unless", "after", "before", "though", "as", "whereas"}


_COORDINATORS = {"and", "or", "but", "nor"}


def _segment_clauses(els: list) -> list:
    """Split into clause spans at a SUBORDINATING/relativizing conjunction or a trailing comma — but NOT at a
    COORDINATOR (and/or/but/nor), which coordinates WITHIN a clause (so "model or plan" stays one clause). A
    clause that BEGINS with a subordinator carries it (so the matrix can be told from a subordinate clause)."""
    clauses, cur = [], []
    for e in els:
        surf = e["surface"].lower().strip(",.;:?!")
        is_boundary = (e["role"] == "function" and e["pos"] == "complementizer") or \
            surf in _SUBORDINATORS or (
        e["role"] == "function" and e["pos"] == "conjunction"
        and surf not in _COORDINATORS and surf != "that")   # "that" relativizer stays in-clause (handled
        #                                                          by _extract_relatives, not a clause split)
        if is_boundary and cur:
            clauses.append(cur); cur = [e]
        else:
            cur.append(e)
        if e["surface"].rstrip().endswith(","):
            clauses.append(cur); cur = []
    if cur:
        clauses.append(cur)
    return [c for c in clauses if c]


def _is_subordinate(clause: list) -> bool:
    if not clause:
        return True
    s0 = clause[0]["surface"].lower().strip(",.;:?!")
    return s0 in _SUBORDINATORS or (clause[0]["role"] == "function" and clause[0]["pos"] in ("conjunction", "complementizer"))


def _clause_focus(clause: list) -> str:
    for e in clause:
        if e["role"] == "focus":
            return e["pos"]
    return "polar"                                       # a yes/no (or disjunctive) matrix with no wh head


def _compose_clause(clause: list, focus: Optional[str]) -> dict:
    """Predicate (main content verb, else copula) + subject (nearest nominal before) + object/oblique."""
    pred_i, predicate = None, None
    for i, e in enumerate(clause):
        if e["role"] == "content" and e["pos"] == "verb":
            pred_i, predicate = i, e
    if predicate is None:
        # A copula plus a predicative adjective expresses a unary property
        # ("the gate is open"). Prefer that lexical complement to the
        # grammatical copula, including when a negator causes contextual POS
        # disambiguation to mark the adjective rather than the homographic
        # verb ("is the gate not open?"). The adapter records the selected
        # property predicate; native cognition still requires a matching
        # accepted graph proposition before answering.
        copula_i = next((i for i, e in enumerate(clause)
                         if e["role"] == "function"
                         and e["pos"] == "copula"), None)
        if copula_i is not None:
            pred_i = next((i for i, e in enumerate(clause)
                           if i > copula_i and e["role"] == "content"
                           and e["pos"] == "adj"), None)
            if pred_i is not None:
                predicate = clause[pred_i]
    if predicate is None:
        for i, e in enumerate(clause):
            if e["role"] == "function" and e["pos"] in ("copula", "auxiliary"):
                pred_i, predicate = i, e
                break
    subject, objects, obliques = None, [], []
    if pred_i is not None:
        for e in reversed(clause[:pred_i]):              # subject = nearest nominal before the predicate
            if _is_nominal(e):
                subject = e
                break
        prep_seen = False
        for e in clause[pred_i + 1:]:                    # after: direct objects, and obliques after prepositions
            if e["role"] == "function" and e["pos"] in ("preposition", "postposition"):
                prep_seen = True
                continue
            if _is_nominal(e):
                (obliques if prep_seen else objects).append(e)
                prep_seen = False                        # each preposition governs its own oblique (coordination)
        # INVERSION ("is that a failure ...") — subject is post-copula. ONLY for a genuine POLAR question; in a
        # wh clause ("what was wrong with your plan") the wh IS the queried element, so the post-copula nominal
        # stays the complement/oblique (else we'd mistake "plan" for the subject of a bare "what is plan").
        if subject is None and focus == "polar" and predicate["role"] == "function" \
                and predicate["pos"] in ("copula", "auxiliary"):
            if objects:
                subject = objects.pop(0)
            elif obliques:
                subject = obliques.pop(0)
    return {"focus": focus, "predicate": predicate, "subject": subject,
            "object": objects[0] if objects else None, "objects": objects,
            "oblique": obliques[0] if obliques else None, "obliques": obliques}


_RELATIVIZERS = {"that", "which", "who", "whom", "whose"}


def _is_relative(clause: list) -> bool:
    if not clause:
        return False
    s0 = clause[0]["surface"].lower().strip(",.;:?!")
    return s0 in _RELATIVIZERS and clause[0]["role"] == "function" \
        and clause[0]["pos"] in ("conjunction", "pronoun")


def _last_nominal(clause: list) -> Optional[dict]:
    for e in reversed(clause):
        if _is_nominal(e):
            return e
    return None


def _np_start(e: dict) -> bool:                          # a token that can START a new NP subject
    return e["role"] == "function" and e["pos"] in ("pronoun", "determiner")


def _extract_relatives(els: list) -> list:
    """Pull RELATIVE clauses out of the element stream and attach each as a sub-relation on its antecedent noun,
    with a real BOUNDARY: the relative spans from its trigger through its OWN verb (up to the NEXT, matrix verb),
    so the matrix predicate that resumes after it is NOT swallowed. Triggers: an explicit relativizer "that"
    (tagged a conjunction by context) OR a REDUCED relative (a new NP-subject right after a noun, no relativizer:
    "a wall you hit"). Returns the matrix element stream (relative spans removed, antecedents carry .modifier)."""
    matrix, k, n = [], 0, len(els)
    while k < n:
        e = els[k]
        surf = e["surface"].lower().strip(",.;:?!")
        is_relzr = surf == "that" and e["role"] == "function" and e["pos"] == "conjunction"
        prev = matrix[-1] if matrix else None
        prev_noun = bool(prev) and prev["role"] == "content" and prev["pos"] == "noun"
        reduced = (not is_relzr) and prev_noun and _np_start(e)
        if (is_relzr or reduced) and matrix:
            ante = _last_nominal(matrix)
            start = k + 1 if is_relzr else k             # drop the relativizer; a reduced relative has none
            j = next((x for x in range(start, n)
                      if els[x]["role"] == "content" and els[x]["pos"] == "verb"), None)
            if ante is not None and j is not None:
                m = next((x for x in range(j + 1, n)     # the NEXT predicate (verb OR copula) is the matrix's
                          if (els[x]["role"] == "content" and els[x]["pos"] == "verb")
                          or (els[x]["role"] == "function" and els[x]["pos"] == "copula")), n)
                ante["modifier"] = _compose_clause(els[start:m], "rel")
                k = m
                continue
        matrix.append(e); k += 1
    return matrix


def compose_relation(frame: dict) -> dict:
    """Compose {focus, predicate, subject, object, oblique}, selecting the MAIN clause of a multi-clause
    sentence: the matrix interrogative is a wh head with SUBJECT-AUX INVERSION (wh + verb/aux); otherwise the
    matrix is the clause NOT introduced by a subordinator, and the focus is polar. A RELATIVE clause (that/
    which/who ...) is composed as a SUB-RELATION and attached to the noun it modifies (its antecedent), so an
    argument can carry a nested relation ("the wall that you hit" -> wall[hit(you)])."""
    # segment clauses FIRST (so a comma separates subordinate from matrix), then extract relatives WITHIN each
    # clause (bounded spans attached to their antecedent) — order matters: a reduced relative must not reach
    # across the comma into the matrix.
    clauses = [_extract_relatives(c) for c in _segment_clauses(frame.get("elements", []))]
    for c in clauses:                                    # a wh head + inversion = the matrix question
        if c and c[0]["role"] == "focus" and len(c) > 1 and (
                (c[1]["role"] == "content" and c[1]["pos"] == "verb") or
                (c[1]["role"] == "function" and c[1]["pos"] in ("copula", "auxiliary"))):
            return _compose_clause(c, c[0]["pos"])
    embedded = [c for c in clauses if c and c[0].get("pos") == "complementizer"]
    cand = [c for c in clauses if not _is_subordinate(c)]  # else the matrix (non-subordinate) clause
    if cand:
        main = max(cand, key=len)
        relation = _compose_clause(main, _clause_focus(main))
        if embedded:
            relation["embedded_relations"] = [
                _compose_clause(c[1:], _clause_focus(c[1:]))
                for c in embedded
            ]
        return relation
    main = max(clauses, key=len) if clauses else []
    relation = _compose_clause(main, frame.get("focus"))
    if embedded:
        relation["embedded_relations"] = [
            _compose_clause(c[1:], _clause_focus(c[1:])) for c in embedded
        ]
    return relation


def render_relation(rel: dict) -> str:
    """A readable composed proposition: focus( predicate(subject, object/oblique) ); coordinated args joined |;
    a nominal carrying a relative-clause modifier renders nested ("wall[hit(you)]")."""
    def s(e):
        if not e:
            return "?"
        base = e["surface"].strip(",.;:?!")
        mod = e.get("modifier")
        if mod and mod.get("predicate"):
            mp = mod["predicate"]["surface"].strip(",.;:?!")
            ms = mod["subject"]["surface"].strip(",.;:?!") if mod.get("subject") else "?"
            return f"{base}[{mp}({ms})]"
        return base
    arglist = rel.get("obliques") or rel.get("objects") or []
    arg2 = "|".join(s(e) for e in arglist) if arglist else s(rel.get("oblique") or rel.get("object"))
    return f"{rel.get('focus') or 'ask'}( {s(rel.get('predicate'))}({s(rel.get('subject'))}, {arg2}) )"


def relation_key(rel: dict) -> str:
    """A canonical signature of a composed relation: focus:predicate(subject,arg2). The key a learned answer is
    filed under, so a re-ask of the same relation (any phrasing) resolves to what was taught."""
    def s(e):
        return (e["surface"].strip(",.;:?!").lower() if e else "?")
    arglist = rel.get("obliques") or rel.get("objects") or []
    a2 = "|".join(s(e) for e in arglist) if arglist else s(rel.get("oblique") or rel.get("object"))
    return f"{rel.get('focus') or 'ask'}:{s(rel.get('predicate'))}({s(rel.get('subject'))},{a2})"


def learn_frontier_answer(substrate: Any, question_text: str, answer: str) -> str:
    """TEACH the answer to a posed frontier: compose the question's relation and FILE the answer under its key
    via the TEACH facility — so it is held LIVE and PERSISTED to seeds/resolved_queries.json (a future boot
    holds it too). A later re-ask of the same relation resolves to it. Returns the key learned."""
    rel = compose_relation(parse_with_gaps(question_text, substrate))
    key = relation_key(rel)
    attrs = {"key": key, "focus": rel.get("focus") or "ask", "answer": answer}
    try:
        from domains.teach import teach
        teach(type("_TeachAgent", (), {"s": substrate})(), "ResolvedQuery", attrs, category="resolved_queries")
    except Exception:
        substrate.add_node("ResolvedQuery", attrs)        # fallback: at least hold it live
    return key


def load_resolved_queries(substrate: Any) -> int:
    """Load PERSISTED ResolvedQuery nodes (taught frontier answers) from seeds/resolved_queries.json into a
    fresh boot, so learning survives a reboot. Mechanical (read the manifest, add the nodes)."""
    import json
    path = Path(__file__).resolve().parent.parent / "seeds" / "resolved_queries.json"
    if not path.exists():
        return 0
    try:
        m = json.loads(path.read_text())
    except Exception:
        return 0
    n = 0
    for node in m.get("nodes", []):
        if node.get("type") == "ResolvedQuery":
            substrate.add_node("ResolvedQuery", node.get("attrs", {})); n += 1
    return n


def _lookup_learned(substrate: Any, key: str) -> Optional[str]:
    if substrate is None:
        return None
    try:
        for n in substrate.nodes("ResolvedQuery"):
            a = substrate.node(n)["attrs"]
            if a.get("key") == key:
                return a.get("answer")
    except Exception:
        return None
    return None


def _find_concept(substrate: Any, name: str) -> Any:
    name = (name or "").lower()
    if not name:
        return None
    for t in ("Concept", "WorldInstance", "LexEntry", "Microtheory"):
        try:
            for n in substrate.nodes(t):
                if (substrate.node(n)["attrs"].get("name") or "").lower() == name:
                    return n
        except Exception:
            pass
    return None


def _held_relation(substrate: Any, owner: str, rel_name: str) -> Optional[str]:
    """The agent's structured knowledge: owner --rel_name--> value (a held edge). Returns the value's name."""
    if substrate is None:
        return None
    n = _find_concept(substrate, owner)
    if n is None:
        return None
    try:
        for m in substrate.neighbours(n, rel_name):
            v = substrate.node(m)["attrs"].get("name")
            if v:
                return v
    except Exception:
        return None
    return None


def resolve_focus(rel: dict, subgoals: list, substrate: Any = None) -> Optional[str]:
    """Resolve the focus over the composed relation. In order: (1) a LEARNED answer (taught for this relation's
    key); (2) a HELD RELATION among grounded concepts ("what is the <R> of <owner>" -> owner --R--> value, the
    agent's structured knowledge — an EDGE, not just a definition); (3) a bare-definitional what/which over a
    grounded TOPIC ("what is <topic>"). Otherwise None — a well-posed FRONTIER the caller emits, never faked."""
    learned = _lookup_learned(substrate, relation_key(rel))
    if learned:
        return learned
    focus = rel.get("focus")
    pred = rel.get("predicate")
    is_copula = bool(pred) and pred["role"] == "function" and pred["pos"] in ("copula", "auxiliary")
    if focus in ("thing", "selection") and is_copula and rel.get("object") and rel.get("oblique"):
        R = rel["object"]["surface"].strip(",.;:?!").lower()       # "what is the <R> of <owner>"
        owner = rel["oblique"]["surface"].strip(",.;:?!").lower()
        v = _held_relation(substrate, owner, R)
        if v:
            return f"the {R} of {owner} is {v}"               # held EDGE, not a definition
    if focus == "polar" and rel.get("subject") and rel.get("predicate"):  # "does X <pred> Y" -> the held edge
        sj = rel["subject"]["surface"].strip(",.;:?!").lower()
        pr = rel["predicate"]["surface"].strip(",.;:?!").lower()
        tg = rel.get("oblique") or rel.get("object")
        if tg and _held_relation(substrate, sj, pr) == tg["surface"].strip(",.;:?!").lower():
            return f"yes — {sj} {pr} {tg['surface'].strip(',.;:?!').lower()} (held)"
    if focus not in ("thing", "selection") or not is_copula or rel.get("oblique"):
        return None                                       # relational / causal / non-definitional -> frontier
    topic = rel.get("subject") or rel.get("object")
    if topic is None:
        return None
    tn = topic["surface"].strip(",.;:?!").lower()
    for sg in (subgoals or []):
        tgt = getattr(sg, "target", None)
        if tgt and getattr(tgt, "know_concept", None) == tn and not getattr(sg, "is_wall", True):
            ka = getattr(sg, "know_answer", None) or {}
            g = ka.get("genus") or ka.get("definition") or ka.get("answer") or ka.get("concept")
            if g:
                return f"{tn} is {g}"
    return None
