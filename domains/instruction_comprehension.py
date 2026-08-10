"""instruction_comprehension — GRAPH-NATIVE comprehension of an operational
instruction. Understanding intent from text is COGNITION, not I/O: NO REGULAR
EXPRESSIONS. The only I/O is raw text -> a chain of Token nodes (mechanical
whitespace split + char-level punctuation, the ChatWorld/Mention precedent).
EVERYTHING after — which connective is a real clause boundary, whether a clause
is a verb-headed imperative, where a conditional / for-each opens — is the agent
UNDERSTANDING, and lives in the GRAPH as Terms over the Token nodes + the held
POS faculty.

THE CLEAN SPLIT (mirrors language_faculty_ops' nominal_head_term):

  I/O (Python, mechanical): `tokenize` — raw text -> InstrToken node chain.
    str.split() on whitespace + char-level punctuation peeling (str/char methods,
    NOT regex): a Token per word carrying {text, pos (held-faculty POS list),
    verb (1/0 = has a verb reading), fn (1/0 = is a function word), sent, idx} +
    `next` edges. Attaching POS is a HELD-FACULTY CALL (wiktionary_reference +
    function_word_reference) — the same lexical reference language_faculty_ops
    reads. This is the admissible ingest: opaque external text -> the smallest
    graph tokens.

  COGNITION (graph-resident, THE DECISIONS): the recognition Terms below, each a
    pure Term over a Token node's measured attrs, run by the Rust evaluator:
      · imperative_head_term — the boundary CRUX: a token opens a VERB-HEADED
        imperative clause iff it has a 'verb' POS reading AND is not a function
        word (And(In('verb', tok.pos), Not(tok.fn))). The twin of
        nominal_head_term — a verb-head DECISION as a graph Term over POS attrs.
      · text_in_term(tok, set) — connective / control recognition: a token is a
        boundary candidate / conditional opener / for-each head / sequence marker
        iff its `text` attr is In the closed set (a graph In match on the token
        attr, NOT a regex `\band\b`).
    A candidate connective ('and' / ',' / 'then') is a REAL clause boundary IFF
    BOTH the closing (left) clause head AND the opening (right) clause head are
    verb-headed imperatives — decided by imperative_head_term. So 'do A and do B'
    (two verb heads) splits; 'report A and which gaps were fixed' (right side no
    imperative verb) does NOT. ';' is a structural separator regardless, and it
    splits BEFORE if/for-each detection.

  WALK (Python, mechanical): the comprehension functions walk the Token chain and
    READ each recognition Term's verdict (native.evaluate) to assemble a Unit tree
    — exactly the run_plan / match_capability precedent: the DECISION is the Term's,
    Python only sequences + reads. NO Python string-parsing decides structure.

The Unit tree (kind ∈ act / stop / ifthen / foreach; nested `body`) is consumed by
operational_planning.parse_instruction, which mints the Plan/PlanStep graph +
binds each act clause to a capability via the (unchanged) capability_match Argmax.

CONTROL-FLOW COVERAGE: SEQUENCE (coordinate imperative clauses), IF-THEN (if/when
opener + condition/body split), FOR-EACH (for each + source/body split), STOP.
RESIDUALS (honest): if-ELSE / while / until are not yet control kinds; deeper NL
(subordinate clauses beyond one comma, relative-clause conditions) parses to the
nearest supported shape; the held POS faculty is a lexical lookup, so a genuinely
novel imperative verb absent from Wiktionary reads as non-verb-headed. donkey=0.
"""
from __future__ import annotations

from typing import Any, Optional


# ===========================================================================
# TERM BUILDERS — the graph vocabulary (Eq / In / And / Not / Gt / Attr / Var).
# NO regex; these are the same raw-dict Term form native_cognition builds.
# ===========================================================================
def _var(n: str) -> dict:
    return {"type": "Var", "name": n}


def _lit(v: Any) -> dict:
    return {"type": "Lit", "value": v}


def _attr(node: dict, key: str) -> dict:
    return {"type": "Attr", "node": node, "key": key}


def _eq(a: dict, b: dict) -> dict:
    return {"type": "Eq", "a": a, "b": b}


def _in(member: dict, container: dict) -> dict:
    return {"type": "In", "member": member, "container": container}


def _and(items: list) -> dict:
    return {"type": "And", "items": items}


def _not(arg: dict) -> dict:
    return {"type": "Not", "arg": arg}


def _flag(tok_var: str, key: str) -> dict:
    """Graph-native truthiness of a 1.0/0.0 flag attr — Gt(attr+0, 0.5), the SAME
    shape language_faculty_ops._flag uses so a missing attr never errors."""
    return {"type": "Gt",
            "a": {"type": "Plus", "items": [_attr(_var(tok_var), key), _lit(0)]},
            "b": _lit(0.5)}


# The closed recognition sets — graph DATA matched by an In over the token `text`
# attr. (A conditional opener is if/when; a for-each is 'for' followed by
# each/every; a boundary candidate is and / ; / , / then; a sequence marker is
# then/finally/first/next/also.) These are sets, not regex alternations.
BOUNDARY_CANDIDATES = ["and", ";", ",", "then"]
COND_OPENERS = ["if", "when"]
SEQUENCE_MARKERS = ["then", "finally", "first", "next", "also"]
FOREACH_HEADS = ["each", "every"]
COND_BODY_DELIMS = [",", "then"]


def imperative_head_term(tok_var: str = "tok") -> dict:
    """THE BOUNDARY CRUX — True iff the token bound to `tok_var` opens a VERB-HEADED
    imperative clause: it carries a 'verb' POS reading AND is not a function word.
    A pure Term over the token's measured POS attrs — the verb-head DECISION the
    comprehension chains, run by the Rust evaluator. The twin of
    language_faculty_ops.nominal_head_term (nominal-vs-clause), here
    imperative-clause-vs-not."""
    return _and([_in(_lit("verb"), _attr(_var(tok_var), "pos")),
                 _not(_flag(tok_var, "fn"))])


def text_in_term(tok_var: str, options: list) -> dict:
    """A token's `text` attr is In the closed `options` set — the graph match that
    recognizes a connective / opener / marker (NOT a regex)."""
    return _in(_attr(_var(tok_var), "text"), _lit(list(options)))


# Precomputed recognition Terms (built once; evaluated per token in the walk).
_IMPERATIVE_HEAD = imperative_head_term("tok")
_IS_BOUNDARY = text_in_term("tok", BOUNDARY_CANDIDATES)
_IS_COND_OPENER = text_in_term("tok", COND_OPENERS)
_IS_SEQ_MARKER = text_in_term("tok", SEQUENCE_MARKERS)
_IS_FOREACH_HEAD = text_in_term("tok", FOREACH_HEADS)
_IS_COND_DELIM = text_in_term("tok", COND_BODY_DELIMS)
_IS_FOR = _eq(_attr(_var("tok"), "text"), _lit("for"))
_IS_STOP = _eq(_attr(_var("tok"), "text"), _lit("stop"))
_IS_SEPARATOR = _eq(_attr(_var("tok"), "text"), _lit(";"))


# ===========================================================================
# HELD-FACULTY CALLS — the POS lookup boundary (external lexical I/O). No Term
# reads Wiktionary; the same faculty language_faculty_ops reads.
# ===========================================================================
def _pos_of(word: str, language: str = "en") -> list:
    from domains import wiktionary_reference as wr
    try:
        return wr.wiktionary_pos(word, language) or []
    except Exception:
        return []


def _fn_of(word: str, language: str = "en") -> Optional[str]:
    from domains import function_word_reference as fw
    try:
        return (fw.classify(word, language) or {}).get("function")
    except Exception:
        return None


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


# Char classes for punctuation peeling — a terminal ENDS a sentence (bumps the
# sentence index, not emitted as a token); a separator (';' / ',') is EMITTED as
# its own token (it is a connective candidate the graph recognizes). Char
# membership tests, NOT regex.
_TERMINALS = ".!?"
_SEPARATORS = ";,"


# ===========================================================================
# INGEST — raw text -> InstrToken node chain. Mechanical (str.split + char
# punctuation). The ONLY I/O. POS attrs via the held faculty.
# ===========================================================================
def tokenize(agent, text: str) -> list:
    """Translate raw `text` into an ordered chain of InstrToken nodes (the only
    I/O). str.split() on whitespace; peel leading/trailing punctuation with char
    membership (NOT regex): a terminal ('.'/'!'/'?') bumps the sentence index, a
    separator (';'/',') is emitted as its own token. Each word token carries its
    held-faculty POS features. Returns the ordered token node ids."""
    sub, native = _resolve(agent)
    tokens: list = []
    prev = None
    sent = 0
    idx = 0

    def emit(word: str, is_word: bool) -> None:
        nonlocal prev, idx
        if is_word:
            pos = _pos_of(word)
            verb = 1.0 if "verb" in pos else 0.0
            fn = 1.0 if _fn_of(word) else 0.0
        else:
            pos, verb, fn = [], 0.0, 0.0
        t = sub.add_node("InstrToken", {"text": word, "pos": pos, "verb": verb,
                                        "fn": fn, "sent": float(sent),
                                        "idx": float(idx)})
        if prev is not None:
            native.add_edge_unchecked(prev, "next", t)
        prev = t
        idx += 1
        tokens.append(t)

    for raw in text.split():
        core = raw
        # collect trailing punctuation (in order) mechanically.
        trailing: list = []
        while core and core[-1] in (_TERMINALS + _SEPARATORS):
            trailing.append(core[-1])
            core = core[:-1]
        trailing.reverse()
        # strip any leading punctuation (rare — quotes/parens already dropped).
        while core and core[0] in (_TERMINALS + _SEPARATORS):
            core = core[1:]
        word = core.lower()
        if word:
            emit(word, True)
        bump = 0
        for ch in trailing:
            if ch in _SEPARATORS:
                emit(ch, False)          # a connective-candidate token
            elif ch in _TERMINALS:
                bump = 1                 # sentence ends after this word
        sent += bump
    return tokens


# ===========================================================================
# COMPREHEND — walk the Token chain, READ the recognition Terms' verdicts,
# assemble the Unit tree. The DECISIONS are the Terms'; the walk only sequences.
# ===========================================================================
def _ev(agent, term: dict, tok) -> bool:
    _, native = _resolve(agent)
    try:
        return bool(native.evaluate(term, {"tok": tok}))
    except Exception:
        return False


def _text_of(agent, toks: list) -> str:
    sub, _ = _resolve(agent)
    return " ".join(sub.node(t)["attrs"].get("text", "") for t in toks).strip()


def _find_first(agent, toks: list, term: dict) -> Optional[int]:
    for i, t in enumerate(toks):
        if _ev(agent, term, t):
            return i
    return None


def _strip_seq_markers(agent, toks: list) -> list:
    """Drop leading sequence markers (then/finally/first/next/also) — a graph
    recognition per token, not a regex prefix strip."""
    i = 0
    while i < len(toks) and _ev(agent, _IS_SEQ_MARKER, toks[i]):
        i += 1
    return toks[i:]


def _segment(agent, tokens: list) -> list:
    """Split the token chain into structural SEGMENTS: at a sentence boundary
    (the ingest-set `sent` index, mechanical I/O) OR at a ';' structural
    separator (a graph Term). ';' tokens are dropped. This runs BEFORE if/for-each
    detection, so pre-';' acts become their own steps."""
    sub, _ = _resolve(agent)
    segs: list = []
    cur: list = []
    cur_sent = None
    for t in tokens:
        sent = sub.node(t)["attrs"].get("sent")
        if _ev(agent, _IS_SEPARATOR, t):        # graph decision: ';' splits
            if cur:
                segs.append(cur)
                cur = []
            cur_sent = None
            continue
        if cur_sent is not None and sent != cur_sent and cur:
            segs.append(cur)
            cur = []
        cur_sent = sent
        cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def _parse_coordinate(agent, toks: list) -> list:
    """Split a plain segment into coordinate imperative clauses at REAL boundaries.
    A boundary candidate (and / , / then) is a real boundary IFF the closing clause
    head AND the opening clause head are BOTH verb-headed imperatives (the
    imperative_head_term graph decision on both sides). Otherwise the connective
    stays inside the clause (e.g. 'report ... and which gaps were fixed')."""
    clauses: list = []
    cur: list = []
    n = len(toks)
    for i, t in enumerate(toks):
        if _ev(agent, _IS_BOUNDARY, t):
            right = toks[i + 1] if i + 1 < n else None
            left_head = cur[0] if cur else None
            if (left_head is not None and right is not None
                    and _ev(agent, _IMPERATIVE_HEAD, left_head)
                    and _ev(agent, _IMPERATIVE_HEAD, right)):
                clauses.append(cur)
                cur = []
                continue                          # drop the boundary connective
            cur.append(t)                         # not a boundary -> keep it
        else:
            cur.append(t)
    if cur:
        clauses.append(cur)

    units: list = []
    for cl in clauses:
        cl = _strip_seq_markers(agent, cl)
        if not cl:
            continue
        if _ev(agent, _IS_STOP, cl[0]):
            units.append({"kind": "stop", "text": _text_of(agent, cl),
                          "cond_text": _text_of(agent, cl[1:])})
        else:
            units.append({"kind": "act", "text": _text_of(agent, cl)})
    return units


def _parse_cond(agent, toks: list) -> dict:
    """An if/when segment -> an ifthen Unit. Condition = tokens after the opener up
    to the first ',' / 'then' delimiter (a graph recognition); body = the rest,
    recursively parsed."""
    rest = toks[1:]
    k = _find_first(agent, rest, _IS_COND_DELIM)
    if k is None:
        cond, body = rest, []
    else:
        cond, body = rest[:k], rest[k + 1:]
    return {"kind": "ifthen", "text": _text_of(agent, toks),
            "cond_text": _text_of(agent, cond),
            "body": _parse_segment_units(agent, body)}


def _parse_foreach(agent, toks: list) -> dict:
    """A 'for each/every ...' segment -> a foreach Unit. Source = tokens after the
    head up to the first ',' delimiter; body = the rest, recursively parsed."""
    rest = toks[2:]
    k = _find_first(agent, rest, _IS_COND_DELIM)
    if k is None:
        source, body = rest, []
    else:
        source, body = rest[:k], rest[k + 1:]
    return {"kind": "foreach", "text": _text_of(agent, toks),
            "source_text": _text_of(agent, source),
            "body": _parse_segment_units(agent, body)}


def _parse_segment_units(agent, toks: list) -> list:
    """Parse ONE segment (or a control body) into a list of Units. Recognizes
    for-each / conditional / stop openers (graph Terms on the head token), else
    splits coordinate imperative clauses."""
    toks = _strip_seq_markers(agent, toks)
    if not toks:
        return []
    head = toks[0]
    if (_ev(agent, _IS_FOR, head) and len(toks) > 1
            and _ev(agent, _IS_FOREACH_HEAD, toks[1])):
        return [_parse_foreach(agent, toks)]
    if _ev(agent, _IS_COND_OPENER, head):
        return [_parse_cond(agent, toks)]
    if _ev(agent, _IS_STOP, head):
        return [{"kind": "stop", "text": _text_of(agent, toks),
                 "cond_text": _text_of(agent, toks[1:])}]
    return _parse_coordinate(agent, toks)


def comprehend(agent, text: str) -> dict:
    """COMPREHEND an instruction into a Unit tree (graph-native). Ingest the text
    into an InstrToken chain (the only I/O), split into structural segments (';' +
    sentence), then recognize each segment's control structure + coordinate
    clauses via the recognition Terms. Returns {tokens, units}. The STRUCTURE is
    the graph Terms' decision; the walk only sequences + reads."""
    tokens = tokenize(agent, text)
    units: list = []
    for seg in _segment(agent, tokens):
        units.extend(_parse_segment_units(agent, seg))
    return {"tokens": tokens, "units": units}


# ===========================================================================
# INSPECTION — verbatim views for the ledger / proofs (mechanical graph reads).
# ===========================================================================
def token_view(agent, tokens: list) -> str:
    """A printable view of the InstrToken chain + POS/verb/fn attrs."""
    sub, _ = _resolve(agent)
    lines = []
    for t in tokens:
        at = sub.node(t)["attrs"]
        lines.append(f"  tok[{int(at.get('idx') or 0)}] sent={int(at.get('sent') or 0)} "
                     f"text={at.get('text')!r:14} verb={int(at.get('verb') or 0)} "
                     f"fn={int(at.get('fn') or 0)} pos={at.get('pos')}")
    return "\n".join(lines)


def unit_view(units: list, depth: int = 0) -> str:
    """A printable view of the comprehended Unit tree."""
    pad = "  " * depth
    lines = []
    for u in units:
        kind = u.get("kind")
        extra = ""
        if kind == "ifthen":
            extra = f"  cond={u.get('cond_text')!r}"
        elif kind == "foreach":
            extra = f"  source={u.get('source_text')!r}"
        elif kind == "stop":
            extra = f"  cond={u.get('cond_text')!r}"
        lines.append(f"{pad}{kind:8} text={u.get('text')!r}{extra}")
        if u.get("body"):
            lines.append(unit_view(u["body"], depth + 1))
    return "\n".join(l for l in lines if l.strip())


__all__ = [
    "tokenize", "comprehend", "imperative_head_term", "text_in_term",
    "token_view", "unit_view", "BOUNDARY_CANDIDATES", "COND_OPENERS",
    "SEQUENCE_MARKERS", "FOREACH_HEADS",
]
