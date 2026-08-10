"""code_writing — CODE-3: WRITING IS READING REVERSED.

CODE-1 (`domains/code_reading.py`) made code a READ register: a function's
compute-core decodes against a code-construction codebook and its Term
round-trips through the graph-resident renderer. CODE-2 (`domains/
ast_to_term.py`'s widened emitter) made understanding = PREDICTION: the
agent answers "what does f(x) return" by evaluating its own held Term-tree
model, never by exec-ing the real Python. CODE-3 completes the write half of
the user's directive ("write arbitrary code with full understanding and
comments") by the SAME law the reading arc discovered for text
(`READING_ARC.md`): **writing is reading reversed**.

  1. FUNCTION-GRAIN RENDERING (statement mode). `write_function` produces a
     REAL, runnable `def` from a held Term-tree: a signature from the
     function's own free vars (in argument order), and a BODY of honest
     STATEMENTS -- not just the single expression fragment CODE-1/2's
     renderer emits. The statement-level SCAFFOLDING (which lines, in what
     order: a `Let` peels off ONE assignment line and recurses on its body;
     a `Fold` becomes an init line + a for-loop; anything else is a bare
     `return`) is a FIXED, general structural walk (`_term_to_statements`)
     over the Term-tree's OWN shape -- the write-side twin of `ast_to_term.
     emit_let_chain` / `.emit_accumulation`'s READ-side peel, run in
     REVERSE, and the SAME legal status those functions already have as
     Term BUILDERS (CLAUDE.md: "seed/Term BUILDERS that emit graph data ...
     no agent decisions" -- a fixed map, the SAME for every construction,
     never a per-construction Python branch). Every EXPRESSION-level
     surface (an assignment's RHS, a fold step, the return value) is
     produced by the EXISTING graph-resident Python renderer (`agent.
     render`, Rust RenderRule-evaluated, unmodified by this module) -- this
     module never composes surface text itself, only assembles the lines
     the renderer hands back.

  2. LITERAL-QUOTING FAITHFULNESS (rung-4, the one Rust primitive this wave
     needed). CODE-1/2's `Lit` RenderRule bound `Slot("value")` straight
     into `Cat`, which coerces via Rust's `Debug`/`Display` -- a string Lit
     rendered UNQUOTED (invalid Python), a bool leaked `Bool(true)`
     (Rust's Debug format), a `None` Lit was a bare render gap. No
     graph-data RenderRule can fix this: the DSL has no Term that inspects
     a raw SCALAR Python value's type (`TypeOf` reads a graph NODE's type,
     a different domain). The fix is the minimal sanctioned primitive:
     `TermNode::LitRepr` (`runners/dsl/src/term.rs`, evaluator `python_repr`)
     -- a FAITHFUL Python `repr()` of a scalar Value (None/Bool/Int/Float/
     Str only; any other Value is an honest render gap, never approximated).
     `seed_python_renderer`'s `Lit` RenderRule now composes
     `LitRepr(value=Slot("value"))` in place of the bare Slot -- one-line
     graph-data change, the primitive itself does the type-aware work.

  3. COMMENTS FROM THE STRUCTURE'S OWN RATIONALE. The written function's
     docstring is the SAME text CODE-1's reading side already produces
     (`code_reading._ground_code`'s `what_does` readout) -- literally the
     same data, now flowing OUTWARD: the agent writes WHY because the WHY
     is already in the graph. Inline comments are equally structural, never
     freehand: a `Fold`'s accumulator-role comment is read straight off the
     Term's OWN `acc_name`/`var_name` fields; an `IfThenElse` used as the
     function's return gets a condition-meaning comment read off its own
     `cond`/`then`/`other` (rendered through the same existing renderer).

  4. ROUND-TRIP AS THE LAW. `self_consistency_check` proves
     `write(read(f))`: read a real function, write it back as a new
     commented function, READ THE WRITTEN FUNCTION BACK, and require the
     SAME construction, a canonically-EQUAL Term, and the re-reader's OWN
     docstring-agreement stratum = AGREE -- the written comment came from
     the structure, so the reader must find it self-consistent. This is
     the self-consistency gate the whole arc has been building toward.

  5. WRITE FROM AN NL REQUEST. `write_function_from_request` is the
     end-to-end proof: a request ("write a function that returns the
     larger of two numbers") is mechanically reduced to its CONTENT WORDS
     (`_content_tokens`, the write-side analogue of `code_reading.
     _split_identifier` / `._root_marker` -- fixed text prep, not a
     decision) and decoded against `seeds/code_write_constructions.json`
     via the SAME Rust `ShapeDecode` Term `code_reading.py` and
     `reflective_faculty.compose_design_for_goal` already run for code
     READING and English-clause reading. WHICH construction wins is
     ShapeDecode's call, never a Python if-ladder; the winning
     construction's `ground_template` names a Term-tree RECIPE (built from
     the SAME held DSL vocabulary CODE-1/2 already read/evaluate) which
     the function-grain renderer writes out, commented, then a mechanical
     sample-input check natively evaluates (never fabricated). A request
     outside the SMALL starter vocabulary (larger/smaller/sum/product/
     absolute-value/average of two numbers; total/count over a list)
     abstains honestly ("I don't hold a shape for that yet") -- growing
     the vocabulary is CODE-4's, not silently approximated here.
     `looks_like_write_request` is the "sanctioned surface" classifier
     `converse()` calls (`WorldAdapter._write_function_reply`) -- CLAUDE.
     md's own thin-I/O-boundary-classifier carve-out ("genuinely
     converting an opaque external form into the smallest graph token, AND
     there's no Rust primitive that can do the job"): it only recognises
     THAT a message is a code-write request (a write-verb word + a
     function/code word, both mechanical), never WHICH shape it wants --
     that decision stays ShapeDecode's, inside `compose_function_from_
     request`.

ARCHITECTURE (CLAUDE.md). No Python rule engine, no agent state, no
per-construction branch over MEANING. The only two DECISIONS in this
module -- which code_write_construction covers a request, and (upstream,
CODE-1) which code_construction covers a Return shape -- are both the
Rust `ShapeDecode` Term's, read off its own verdict. Everything else here
is mechanical: text prep (`_content_tokens`), a fixed structural walk over
a HELD Term-tree's own shape (`_term_to_statements`), and calls into the
EXISTING graph-resident renderer for every expression surface.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from domains import ast_to_term
from domains import code_reading as cdr
from domains import reflective_faculty as rf
from substrate.jsonio import term_from_json

_ROOT = cdr._ROOT


# --------------------------------------------------------------------------- #
#  codebook install (mechanical adapter I/O — no decision, mirrors
#  code_reading.ensure_codebook exactly).
# --------------------------------------------------------------------------- #
def ensure_write_codebook(agent) -> None:
    sub, _native, _ag = cdr._resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "code_write_constructions":
            return
    path = os.path.join(_ROOT, "seeds", "code_write_constructions.json")
    with open(path) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "code_write_constructions",
                          "version": manifest.get("version", "1.0.0")})


# --------------------------------------------------------------------------- #
#  MECHANICAL request text-prep — the write-side analogue of
#  code_reading._split_identifier / ._root_marker: a fixed, non-branching-
#  over-meaning map from surface text to marker tokens. WHICH construction
#  wins is ShapeDecode's call (below), never this step's.
# --------------------------------------------------------------------------- #
_STOPWORDS = {
    "a", "an", "the", "of", "that", "to", "write", "me", "please", "and",
    "is", "returns", "return", "function", "for", "two", "numbers",
    "number", "list", "items", "item", "in", "given", "takes", "with",
    "over", "from", "value",
}
_WRITE_VERBS = {"write", "create", "compose", "implement", "give", "make"}
_FUNCTION_NOUNS = {"function", "code", "def", "method"}
_STRIP = ".,?!;:()[]\"'"


def _content_tokens(text: str, agent=None) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace, drop the closed
    STOPWORD set -- mechanical text prep. Returns UPPERCASE tokens (the
    write codebook's own trigger-token case) in first-seen order, deduped.

    CODE-4: the request-CUE words (`_request_cue_sets` -- the held write-verb
    / function-noun Concepts, or their closed fallbacks) are dropped too:
    a cue word is request FRAMING the classifier already consumed, never
    request CONTENT the shape decode should have to cover. This closes the
    CODE-3 residual where a non-stopword write verb ('create', 'implement',
    or a TAUGHT one like 'author') poisoned the skeleton and blocked an
    otherwise-held shape."""
    verbs, nouns = _request_cue_sets(agent)
    out: list[str] = []
    for raw in text.split():
        w = raw.strip(_STRIP).lower()
        if not w or w in _STOPWORDS or w in verbs or w in nouns:
            continue
        u = w.upper()
        if u not in out:
            out.append(u)
    return out


def _request_cue_sets(agent) -> tuple:
    """CODE-4 (item 3): read the write-request cue vocabulary off HELD
    Concept nodes (`seeds/code_write_request_cues.json` -- Concept{name,
    code_request_role:'write_verb'|'function_noun'}), the instruction_route /
    gap_awareness cue precedent, so a NEW request phrasing is LEARNED via
    teach() and never a Python edit. Mechanical graph query, no decision.
    Falls back to the retired closed sets when NO cue Concepts are held (a
    minimal boot without the seed classifies byte-identically)."""
    if agent is None:
        return _WRITE_VERBS, _FUNCTION_NOUNS
    try:
        sub = getattr(agent, "s", agent)
        verbs: set = set()
        nouns: set = set()
        for n in sub.nodes("Concept"):
            at = sub.node(n)["attrs"]
            role = at.get("code_request_role")
            if role == "write_verb" and at.get("name"):
                verbs.add(str(at["name"]).lower())
            elif role == "function_noun" and at.get("name"):
                nouns.add(str(at["name"]).lower())
        if verbs and nouns:
            return verbs, nouns
    except Exception:
        pass
    return _WRITE_VERBS, _FUNCTION_NOUNS


_IMPERATIVE_VERBS = {"write", "create", "implement", "compose"}
_IMPERATIVE_LEAD_PHRASES = (
    "as an exercise,", "as another exercise,", "then", "you should",
    "you might want to", "you may want to",
)
_EXERCISE_NUM_RE = re.compile(r"\bExercise\s*\d+\s+", re.IGNORECASE)
_VERB_SEARCH_WINDOW = 10
_NOUN_SEARCH_WINDOW = 8


def _imperative_cue_sets(agent) -> tuple:
    """WHOLE-CURRICULUM WAVE 2: the imperative-lead vocabulary the
    structural gate below reads -- write-verb Concepts NOT explicitly
    marked `imperative_lead: 0.0` (seeded false for 'give'/'make', too
    generic to head a bare imperative -- see `seeds/
    code_write_request_cues.json`'s wave-2 note) plus
    `imperative_lead_phrase` Concepts (exercise lead-in phrases like 'As
    an exercise,'). A newly taught write-verb defaults ELIGIBLE (attr
    absent == eligible), so the existing 'taught phrasing routes' parity
    is unaffected. Falls back to the closed sets when no agent / no cue
    Concepts are held -- the SAME parity status `_request_cue_sets` has."""
    if agent is None:
        return set(_IMPERATIVE_VERBS), _IMPERATIVE_LEAD_PHRASES
    try:
        sub = getattr(agent, "s", agent)
        imp_verbs: set = set()
        phrases: list = []
        any_verb = False
        for n in sub.nodes("Concept"):
            at = sub.node(n)["attrs"]
            role = at.get("code_request_role")
            if role == "write_verb" and at.get("name"):
                any_verb = True
                lead = at.get("imperative_lead", 1.0)
                if not (lead == 0 or lead == 0.0 or lead is False):
                    imp_verbs.add(str(at["name"]).lower())
            elif role == "imperative_lead_phrase" and at.get("name"):
                phrases.append(str(at["name"]).lower())
        if any_verb:
            return imp_verbs, tuple(phrases) if phrases else _IMPERATIVE_LEAD_PHRASES
    except Exception:
        pass
    return set(_IMPERATIVE_VERBS), _IMPERATIVE_LEAD_PHRASES


def _clause_tokens(s: str) -> list:
    return [w.strip(_STRIP).lower() for w in s.split() if w.strip(_STRIP)]


def _has_imperative_write_lead(text: str, verbs: set, phrases, nouns: set) -> bool:
    """WHOLE-CURRICULUM WAVE 2: the structural gate that distinguishes a
    genuine exercise-style write REQUEST ('Write a function called X
    that...', 'As an exercise, write a method...') from a prose sentence
    that merely MENTIONS writing/functions ('we can write the function
    more concisely', 'Functions can make a program smaller') -- the
    bag-of-words co-occurrence check above (`looks_like_write_request`'s
    own verb/noun intersection) cannot tell these apart at all, since it
    ignores WORD ORDER entirely; this is measured on a real book (Think
    Python 2e): the bag-of-words check alone filed 63 false-positive
    gaps out of 124, one for nearly every sentence that happened to
    mention a write-verb and a code-noun anywhere in the same sentence.

    A write-verb must HEAD its own clause: either the very FIRST word of
    the (bullet-marker-stripped) text, with a function/method noun
    reachable within the next few words (STRICT adjacency -- the general
    case, e.g. 'Write a function that...', 'Create a method that...');
    or the first verb reachable after a recognised exercise lead-in
    phrase ('Exercise 3 ...', 'As an exercise, ...', 'Then ...', 'You
    should ...') within a windowed search (these lead-ins are never seen
    heading ordinary prose in the source corpus, so a wider search is
    safe there) -- again with a noun reachable shortly after the verb.
    Mechanical text-shape scan (manual token walk, no regex over
    meaning) -- never a decision about what the request WANTS, only
    whether it reads as a directive at all."""
    stripped = text.strip()
    if stripped.startswith("- "):
        stripped = stripped[2:].lstrip()

    toks = _clause_tokens(stripped)
    if toks and toks[0] in verbs:
        if any(t in nouns for t in toks[1:1 + _NOUN_SEARCH_WINDOW]):
            return True

    anchors: list = []
    for m in _EXERCISE_NUM_RE.finditer(text):
        anchors.append(m.end())
    low = text.lower()
    for phrase in phrases:
        start = 0
        while True:
            idx = low.find(phrase, start)
            if idx < 0:
                break
            anchors.append(idx + len(phrase))
            start = idx + len(phrase)

    for end in anchors:
        rest = _clause_tokens(text[end:])
        for i, t in enumerate(rest[:_VERB_SEARCH_WINDOW]):
            if t in verbs:
                if any(t2 in nouns for t2 in rest[i + 1:i + 1 + _NOUN_SEARCH_WINDOW]):
                    return True
                break
    return False


def looks_like_write_request(text: str, agent=None) -> bool:
    """The thin I/O-boundary classifier CLAUDE.md's own carve-out sanctions:
    a message naming BOTH a write-verb and a function/code noun converts
    the opaque NL string into the smallest graph token ("this is a
    code-write request"). WHICH shape it wants is a separate, later,
    graph-native decision (`compose_function_from_request`'s ShapeDecode)
    -- never this check's job. CODE-4: with `agent`, the word sets are the
    HELD cue Concepts (`_request_cue_sets`), teachable via teach(); without
    (or when none are held), the original closed sets -- parity gated.

    WHOLE-CURRICULUM WAVE 2: the coarse co-occurrence check above is
    necessary but no longer sufficient -- it is ALSO gated on
    `_has_imperative_write_lead` (an IMPERATIVE-EXERCISE-SHAPE structural
    check, see its docstring), so a message must both co-occur a
    write-verb/function-noun pair AND read as an actual imperative
    directive, not merely mention writing/functions in passing."""
    verbs, nouns = _request_cue_sets(agent)
    words = {raw.strip(_STRIP).lower() for raw in text.split()}
    if not (bool(words & verbs) and bool(words & nouns)):
        return False
    imp_verbs, phrases = _imperative_cue_sets(agent)
    return _has_imperative_write_lead(text, imp_verbs, phrases, nouns)


# --------------------------------------------------------------------------- #
#  DECODE the request against the write codebook — ShapeDecode decides.
# --------------------------------------------------------------------------- #
def _write_template(sub, name: str) -> dict:
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name and at.get("kind") == "code_write_construction":
            tmpl = at.get("ground_template")
            if tmpl:
                try:
                    return json.loads(tmpl)
                except Exception:
                    pass
    return {}


def compose_function_from_request(agent, request_text: str) -> dict:
    """Decode `request_text` against the write codebook: content-word
    skeleton -> ShapeDecode (graph-native, `reflective_faculty.
    compose_design_for_goal` -- the SAME Rust Term `code_reading.py` uses
    to recognise a function's compute-core) -> the winning construction's
    Term-tree RECIPE. Returns {ok, construction, term, args, desc,
    shape_fit} or an honest {ok: False, reason, tokens} -- never a
    fabricated guess outside the held vocabulary."""
    ensure_write_codebook(agent)
    sub, _native, _ag = cdr._resolve(agent)
    tokens = _content_tokens(request_text, agent)
    if not tokens:
        return {"ok": False, "reason": "no content words in the request", "tokens": tokens}
    skeleton = [[t] for t in tokens]
    decode = rf.compose_design_for_goal(sub, skeleton)
    if not isinstance(decode, dict):
        decode = {"plan": [], "residual": list(skeleton)}
    # CODE-CURRICULUM finding: restrict the argmax to WRITE-side candidates
    # (`_winner`'s own `kind` filter) -- the flat ShapeSignature namespace
    # otherwise lets a READ-side (or other-domain) construction with no term
    # recipe win a write decode outright (observed live: a request matched a
    # construction whose `ground_template` carried no `term` at all -- an
    # impossible answer, not merely a wrong one). Same-kind collisions
    # between two write shapes remain a named, un-fixed residual.
    winner, fit = cdr._winner(decode, kind="code_write_construction")
    if winner is None or fit <= 0:
        return {"ok": False, "reason": "no held shape for this request",
               "tokens": tokens, "residual": decode.get("residual")}
    template = _write_template(sub, winner)
    if not template or not template.get("term"):
        return {"ok": False, "reason": "construction %r carries no term recipe" % winner,
               "tokens": tokens}
    return {"ok": True, "construction": winner, "term": template["term"],
           "args": list(template.get("args") or []), "desc": template.get("desc") or "",
           "tokens": tokens, "shape_fit": fit}


# --------------------------------------------------------------------------- #
#  FUNCTION-GRAIN RENDERING — writing is reading reversed. Statement-level
#  scaffolding is a FIXED structural walk over the Term-tree's own shape;
#  every expression surface goes through the EXISTING graph-resident
#  renderer (agent.render, unmodified) -- see module docstring (1)/(3).
# --------------------------------------------------------------------------- #
def _render_expr(agent, term_dict: dict) -> str:
    if agent.language("python") is None:
        agent.seed_python_renderer()
    term_obj = term_from_json(term_dict)
    rendered = agent.render(term_obj, "python")
    if rendered is None:
        raise ast_to_term.EmitError(
            "render gap: no RenderRule covers %r" % term_dict.get("type"))
    return rendered


def _render_iterable(agent, term_dict: dict) -> str:
    """A Fold's `source`, rendered for a `for <var> in <source>:` header.
    `range(...)` detection (a Vec of consecutive int Lits) is `ast_to_term.
    _emit_range_domain`'s materialisation run IN REVERSE -- mechanical
    pattern detection over the Term's own shape (never a decision): a Vec
    that IS such a run renders as `range(...)`, so a written accumulation
    round-trips back through `_emit_iterable`'s own range(...) recognition.
    Any other Vec renders as an ordinary list literal via the unmodified
    existing renderer."""
    if term_dict.get("type") == "Vec":
        items = term_dict.get("items") or []
        if items and all(
                i.get("type") == "Lit" and isinstance(i.get("value"), int)
                and not isinstance(i.get("value"), bool) for i in items):
            vals = [i["value"] for i in items]
            lo = vals[0]
            if vals == list(range(lo, lo + len(vals))):
                hi = lo + len(vals)
                return "range(%d)" % hi if lo == 0 else "range(%d, %d)" % (lo, hi)
    return _render_expr(agent, term_dict)


_OP_SYMBOL = {"Plus": "+", "Minus": "-", "Times": "*", "Div": "/", "Mod": "%", "Pow": "**"}
_VARIADIC_OPS = {"Plus", "Times"}


def _fold_step_line(agent, acc: str, body_term: dict) -> str:
    """A Fold's `body` is always `{OP, items:[Var(acc), rhs]}` (variadic) or
    `{OP, a:Var(acc), b:rhs}` (binary) -- `ast_to_term.emit_accumulation`'s
    OWN construction (the accumulator is always the left/first operand).
    Render it back as Python AugAssign syntax (`acc OP= rhs`) -- not just
    semantically equivalent but STRUCTURALLY required for the written
    source to re-decode as the `accumulation_loop` construction on
    read-back (`code_reading._multi_stmt_skeleton_and_kind` keys the shape
    on AugAssign, the read side's own fixed classifier, unmodified here).
    Falls back to a plain assignment line for any OTHER body shape (never
    fabricated) -- an honest residual: such a function still WRITES
    correctly, it just will not re-decode as `accumulation_loop`."""
    op = body_term.get("type")
    symbol = _OP_SYMBOL.get(op)
    rhs = None
    if symbol:
        if op in _VARIADIC_OPS:
            items = body_term.get("items") or []
            if len(items) == 2 and items[0] == {"type": "Var", "name": acc}:
                rhs = items[1]
        else:
            if body_term.get("a") == {"type": "Var", "name": acc}:
                rhs = body_term.get("b")
    if rhs is not None:
        return "%s %s= %s" % (acc, symbol, _render_expr(agent, rhs))
    return "%s = %s" % (acc, _render_expr(agent, body_term))


def _branch_return_statements(agent, term: dict, depth: int, *, is_elif: bool) -> list:
    """WAVE 2: the STATEMENT-grain twin of the ternary-comment IfThenElse
    case below -- real `if`/`elif`/`else` lines, recursing into `other`
    when IT is itself an IfThenElse (an elif), so an N-deep branching
    return renders as one clean if/elif*/else chain rather than nested nested
    blocks. Every condition/value surface still goes through the existing
    renderer; this routine only assembles the FIXED scaffolding shape."""
    cond = _render_expr(agent, term["cond"])
    then = _render_expr(agent, term["then"])
    head = "elif %s:" % cond if is_elif else "if %s:" % cond
    out = [(depth, head), (depth + 1, "return %s" % then)]
    other = term["other"]
    if isinstance(other, dict) and other.get("type") == "IfThenElse":
        out.extend(_branch_return_statements(agent, other, depth, is_elif=True))
    else:
        out.append((depth, "else:"))
        out.append((depth + 1, "return %s" % _render_expr(agent, other)))
    return out


def _term_to_statements(agent, term: dict, depth: int = 0, *,
                        branch_style: bool = False) -> list:
    """The write-side twin of `ast_to_term.emit_let_chain` /
    `.emit_accumulation`'s READ-side peel, run in reverse: a `Let` peels
    off ONE assignment line and recurses on its `body`; a terminal `Fold`
    renders as an init line, an ACCUMULATOR-ROLE comment read straight off
    the Fold's own `acc_name`/`var_name` fields (never freehand text), a
    for-loop header, and an indented accumulate line; a terminal
    `IfThenElse` gets EITHER a CONDITION-MEANING comment + a one-line
    ternary return (the CODE-1/2 default -- byte-identical to before
    WAVE-2) OR, when `branch_style` says this Term came from a REAL
    if/elif/else return chain (`code_reading`'s `branching_return`
    construction, not a ternary `IfExp`), real if/elif/else STATEMENT
    lines (`_branch_return_statements`) -- the Term shape is identical
    either way (a branching return and a ternary chain are the same
    meaning), so the caller's own construction name is what picks the
    surface, never a guess from the Term alone. Any other terminal
    expression is the function's `return`. ONE fixed routine for every
    construction -- never a per-construction branch. Returns a list of
    (indent_depth, line_text) pairs."""
    t = term.get("type")
    if t == "Let":
        expr = _render_expr(agent, term["value"])
        out = [(depth, "%s = %s" % (term["name"], expr))]
        out.extend(_term_to_statements(agent, term["body"], depth,
                                       branch_style=branch_style))
        return out
    if t == "Fold":
        acc, var = term["acc_name"], term["var_name"]
        init_expr = _render_expr(agent, term["init"])
        src_expr = _render_iterable(agent, term["source"])
        step_line = _fold_step_line(agent, acc, term["body"])
        return [
            (depth, "%s = %s" % (acc, init_expr)),
            (depth, "# %s accumulates the running value over %s" % (acc, var)),
            (depth, "for %s in %s:" % (var, src_expr)),
            (depth + 1, step_line),
            (depth, "return %s" % acc),
        ]
    if t == "IfThenElse":
        if branch_style:
            return _branch_return_statements(agent, term, depth, is_elif=False)
        cond = _render_expr(agent, term["cond"])
        then = _render_expr(agent, term["then"])
        other = _render_expr(agent, term["other"])
        return [
            (depth, "# returns %s when %s, else %s" % (then, cond, other)),
            (depth, "return %s" % _render_expr(agent, term)),
        ]
    return [(depth, "return %s" % _render_expr(agent, term))]


def write_function(agent, name: str, args: list, term: dict, *,
                   docstring: Optional[str] = None,
                   branch_style: bool = False) -> str:
    """Render a REAL, commented, runnable Python function definition from
    `term` (a held Term-tree) -- the function-grain write. Signature from
    `args` (the function's own free-var order); body from
    `_term_to_statements` (statement scaffolding, general over every
    construction) + the existing graph-resident renderer (every
    expression surface). `branch_style` (WAVE 2, additive, default False
    == byte-identical CODE-1/2 behaviour): render a root/nested
    `IfThenElse` as real if/elif/else statements rather than a
    ternary-plus-comment line -- pass True when the Term was read off a
    genuine `branching_return` construction (see `write_read_function`)."""
    lines = ["def %s(%s):" % (name, ", ".join(args))]
    if docstring:
        lines.append('    """%s"""' % docstring)
    for depth, text in _term_to_statements(agent, term, branch_style=branch_style):
        lines.append("    " * (depth + 1) + text)
    return "\n".join(lines) + "\n"


def _docstring_from_desc(desc: Optional[str]) -> Optional[str]:
    if not desc:
        return None
    d = desc[0].upper() + desc[1:]
    if not d.endswith("."):
        d += "."
    return d


# --------------------------------------------------------------------------- #
#  ROUND-TRIP AS THE LAW — write(read(f)).
# --------------------------------------------------------------------------- #
def write_read_function(agent, source: str, func_name: Optional[str] = None, *,
                        range_bind: Optional[dict] = None) -> dict:
    """write(read(f)) -- read a real function's held Term-tree
    (`code_reading.read_function`) and write it BACK as a new commented
    function, its docstring FLOWING OUTWARD from the SAME `what_does`
    readout the reading side already produces (reading reversed,
    literally the same data). Returns {ok, source, reading, docstring} or
    an honest {ok: False, reason} when the read side itself has no
    emittable Term."""
    reading = cdr.read_function(agent, source, func_name, range_bind=range_bind)
    if reading.get("term") is None:
        return {"ok": False, "reason": reading.get("emit_error") or reading.get("note"),
               "reading": reading}
    docstring = _docstring_from_desc(reading.get("what_does"))
    # WAVE 2: a genuine if/elif/else return chain (as opposed to a ternary
    # IfExp, which shares the SAME IfThenElse Term shape -- see
    # _term_to_statements' docstring) writes back as real statements, read
    # off the reading's OWN construction name, never guessed from the Term.
    branch_style = reading.get("construction") == "branching_return"
    written = write_function(agent, reading["name"], reading["args"], reading["term"],
                             docstring=docstring, branch_style=branch_style)
    return {"ok": True, "source": written, "reading": reading, "docstring": docstring}


def self_consistency_check(agent, source: str, func_name: Optional[str] = None, *,
                           range_bind: Optional[dict] = None) -> dict:
    """The round-trip LAW, checked: write(read(f)), then READ THE WRITTEN
    FUNCTION BACK and report whether the reader finds the SAME
    construction, a Term canonically equal to the original, and its OWN
    docstring-agreement stratum -- the self-consistency gate (the written
    comment came from the structure, so the reader must find it
    consistent). Returns the full evidence dict; callers assert on it."""
    written = write_read_function(agent, source, func_name, range_bind=range_bind)
    if not written["ok"]:
        return {"ok": False, "reason": written["reason"]}
    reread = cdr.read_function(agent, written["source"], written["reading"]["name"])
    return {
        "ok": True,
        "written_source": written["source"],
        "original_reading": written["reading"],
        "reread": reread,
        "construction_match": reread.get("construction") == written["reading"].get("construction"),
        "term_match": reread.get("term") == written["reading"].get("term"),
        "agreement_verdict": (reread.get("agreement") or {}).get("verdict"),
    }


# --------------------------------------------------------------------------- #
#  WRITE FROM AN NL REQUEST — the end-to-end proof.
# --------------------------------------------------------------------------- #
_SAMPLE_ARGS_BY_ARITY = {2: {"a": 6, "b": 3}, 1: {"a": -4}}


def _sample_env(args: list) -> dict:
    if args == ["items"]:
        return {"items": [1, 2, 3, 4]}
    preset = _SAMPLE_ARGS_BY_ARITY.get(len(args))
    if preset is not None and list(preset)[: len(args)] == args:
        return dict(preset)
    return {a: i + 2 for i, a in enumerate(args)}


def write_function_from_request(agent, request_text: str, *,
                                name: str = "generated_function") -> dict:
    """The end-to-end write-from-request proof: NL request -> decode
    (ShapeDecode over the write codebook, graph-native) -> a Term-tree
    from held vocabulary -> the function-grain renderer, commented -> a
    mechanical sample-input sanity check (native evaluation, never a
    fabricated guess) -> {ok, source, ...}. Outside the held vocabulary:
    an honest abstain (compose_function_from_request's own {ok: False,
    reason}), never approximated."""
    compose = compose_function_from_request(agent, request_text)
    if not compose["ok"]:
        return compose
    docstring = _docstring_from_desc(compose["desc"])
    source = write_function(agent, name, compose["args"], compose["term"],
                            docstring=docstring)
    _sub, native, _ag = cdr._resolve(agent)
    sample = _sample_env(compose["args"])
    try:
        sample_result = native.evaluate(compose["term"], sample)
        sample_ok = True
    except Exception:
        sample_result = None
        sample_ok = False
    return {"ok": True, "source": source, "construction": compose["construction"],
           "args": compose["args"], "term": compose["term"], "desc": compose["desc"],
           "docstring": docstring, "sample_env": sample, "sample_result": sample_result,
           "sample_ok": sample_ok}


__all__ = ["ensure_write_codebook", "looks_like_write_request",
          "compose_function_from_request", "write_function", "write_read_function",
          "self_consistency_check", "write_function_from_request"]
