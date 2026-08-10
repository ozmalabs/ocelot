"""LaTeX MATH NOTATION — the agent READS LaTeX into the operator-tree it already
composes, and RENDERS symbol-bearing LaTeX to readable prose so the symbol-carried
research definitions SURVIVE into comprehension (instead of being STRIPPED — lossy).

LaTeX math is a NOTATION SYSTEM, and notation is LEARNABLE the SAME way as the
agent's other notations (construction_grammar.comprehend_notation_introduction /
acquire_notation): a piece of notation is introduced by prose, comprehended into a
construction (graph data), and then a formula written in it parses. This module is
the MECHANICAL world-adapter translator (CLAUDE.md: a thin surface->structure
parser, the same kind as the math-prose clause matcher) that applies the GRAPH-DATA
LaTeX grammar (seeds/latex_math_notation.json) — no decisions-over-graph-state, no
LLM, no Rust. The grammar + the order-N comprehension (comprehend_structure) are the
agent's; the LaTeX constructions are graph DATA.

TWO jobs:
  · render(latex)        — LaTeX (math fragments + `$...$` / `$$...$$` / `\\[..\\]`)
                           -> readable prose, the SYMBOLS SURVIVING ($M$ -> 'M',
                           \\mathbb{Z} -> 'Z', \\partial -> 'boundary', \\in ->
                           'in'). This is what the loaders call INSTEAD of dropping
                           the math: the symbol-carried subject reaches the reader.
  · parse_formula(latex) -> the OPERATOR-TREE (the SAME {op, args, held_runnable} /
                           {term, held} shape comprehend_structure composes),
                           mapping \\partial -> the HELD boundary_operator atom,
                           \\ker/\\im/\\frac (and '/') -> the un-held kernel/image/
                           modulo operators already named in math_prose_constructions.
                           The REAL homology LaTeX
                             H_n(X) = \\ker \\partial_n / \\operatorname{im} \\partial_{n+1}
                           parses into modulo(kernel(∂_n), image(∂_{n+1})) — the
                           structure the agent already COMPUTES in compute_homology.

HONEST residual (named, not over-claimed): the math-CORE constructions (super/
subscript, frac, the named operators, homology/cohomology, blackboard/Greek, set-
builder) cover the common research formulas. The LONG TAIL — every macro / package /
\\newcommand — is breadth (acquired by reading the next instance). The un-held
operations (kernel/image/modulo/tensor/...) are the acquirable residual already
named. Genuinely-visual content (a commutative diagram) reduces to its formal/prose
content only WHERE the source writes it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_SEED = Path(__file__).resolve().parent.parent / "seeds" / \
    "latex_math_notation.json"

_GRAMMAR: Optional[dict] = None

# ACQUIRED macros — LaTeX constructions the agent grounded by READING their
# introduction ('in LaTeX `\\ker` denotes the kernel'). They live alongside the
# seeded grammar; load_grammar MERGES them in so the parser uses them like any
# seeded macro. This is the notation-is-learnable machine, now on LaTeX: a new
# macro reading is graph DATA, appended here by acquire_latex_macro. BEFORE the
# read the macro is opaque (parse returns None on it); AFTER it parses.
_ACQUIRED: dict = {"operator_macros": [], "structure_macros": [],
                   "indexed_heads": []}


def load_grammar(path: Path = _SEED) -> dict:
    """Load the LaTeX-notation grammar (graph data), MERGING any acquired macros
    (read at runtime). Cached for the seed; the merge picks up acquisitions. A pure
    data read — no decision."""
    global _GRAMMAR
    if _GRAMMAR is None:
        try:
            _GRAMMAR = json.loads(Path(path).read_text())
        except Exception:
            _GRAMMAR = {}
    if not any(_ACQUIRED.values()):
        return _GRAMMAR
    # merge the acquired macros in (de-dup by latex token).
    g = dict(_GRAMMAR)
    for key, items in _ACQUIRED.items():
        if not items:
            continue
        existing = {m.get("latex") for m in g.get(key, [])}
        g[key] = list(g.get(key, [])) + [m for m in items
                                         if m.get("latex") not in existing]
    return g


def install_macro(macro: dict) -> bool:
    """INSTALL an acquired LaTeX macro into the runtime grammar (graph data appended
    to _ACQUIRED) so the parser uses it like any seeded macro. `kind` selects the
    bucket: 'operator' -> operator_macros, 'structure' -> structure_macros, 'head'
    -> indexed_heads. De-dup by the latex token (a later reading REPLACES). Returns
    True if installed."""
    bucket = {"operator": "operator_macros", "structure": "structure_macros",
              "head": "indexed_heads"}.get(macro.get("kind"))
    if bucket is None:
        return False
    entry = {k: v for k, v in macro.items() if k != "kind"}
    if macro.get("kind") == "operator":
        entry.setdefault("kind", "operator")
    for ex in _ACQUIRED[bucket]:
        if ex.get("latex") == entry.get("latex"):
            ex.clear()
            ex.update(entry)
            return True
    _ACQUIRED[bucket].append(entry)
    return True


# ---------------------------------------------------------------------------
# RENDER — LaTeX -> readable prose, the SYMBOLS SURVIVING (the loaders' fix).
#
# The loaders currently DROP `$...$` to nothing (lossy: the symbol-carried subject
# is deleted — '$M$ is finite if $M$ is finite' -> 'is finite if is finite'). Here
# the math is RENDERED to a short readable token PER symbol so the subject SURVIVES:
# `$M$` -> 'M', `$R$-module` -> 'R-module', `\mathbb{Z}` -> 'Z', `\partial` ->
# 'boundary', `\ker` -> 'kernel', `\in` -> 'in', `\to` -> 'to', `H_n(X)` ->
# 'H_n(X)' (kept compact). A mechanical surface translation driven by the grammar
# DATA — no meaning decision.
# ---------------------------------------------------------------------------

# the readable WORD a named-operator / structure / relation macro renders to (for
# prose rendering — distinct from the operator-tree name used in parse_formula).
_RENDER_WORDS = {
    "\\partial": "boundary", "\\ker": "kernel", "\\im": "image",
    "\\operatorname{im}": "image", "\\operatorname{ker}": "kernel",
    "\\dim": "dimension", "\\deg": "degree", "\\operatorname{coker}": "cokernel",
    "\\operatorname{rank}": "rank",
    "\\otimes": "tensor", "\\oplus": "direct sum", "\\times": "times",
    "\\cong": "isomorphic to", "\\simeq": "isomorphic to", "\\sim": "similar to",
    "\\to": "to", "\\rightarrow": "to", "\\longrightarrow": "to",
    "\\hookrightarrow": "into", "\\twoheadrightarrow": "onto",
    "\\sum": "sum", "\\prod": "product", "\\int": "integral",
    "\\bigoplus": "direct sum", "\\bigotimes": "tensor product",
    "\\bigcup": "union", "\\bigcap": "intersection",
}


def _flatten_braces(s: str) -> str:
    """Remove LaTeX grouping braces, keeping their content. Iterates so nested
    `{ {Spin} }` flattens. A surface op."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\{([^{}]*)\}", r"\1", s)
    return s


def render(latex: str) -> str:
    """RENDER a LaTeX string (math fragments + `$...$` / `$$...$$` / `\\[..\\]`
    delimited math) to readable prose, the SYMBOLS SURVIVING. The loaders call
    this INSTEAD of dropping the math, so the symbol-carried subject reaches the
    reader ('$M$ is finite if $M$ is finite as an $R$-module' -> 'M is finite if M
    is finite as an R-module'). Driven by the grammar DATA — a mechanical surface
    translation, no meaning decision."""
    if not latex:
        return ""
    g = load_grammar()
    t = latex

    # 1. unwrap the math DELIMITERS, rendering the inner math, keeping the rest.
    #    $$...$$ / \[..\] (display) and $...$ (inline). Process display first.
    def _render_math(m):
        return " " + _render_math_fragment(m.group(1), g) + " "
    t = re.sub(r"\$\$(.*?)\$\$", _render_math, t, flags=re.DOTALL)
    t = re.sub(r"\\\[(.*?)\\\]", _render_math, t, flags=re.DOTALL)
    t = re.sub(r"\\\((.*?)\\\)", _render_math, t, flags=re.DOTALL)
    t = re.sub(r"\$([^$]*)\$", _render_math, t)
    # collapse whitespace; tidy spacing around hyphens ('R -module' -> 'R-module').
    t = re.sub(r"\s+-\s*", "-", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _render_math_fragment(frag: str, g: dict) -> str:
    """Render the INSIDE of a math delimiter (no `$`) to readable tokens. The
    symbols survive: single letters stay, macros render to their word/symbol, sub/
    superscripts kept compact on a head, relations to words."""
    s = frag

    # NAMED-OPERATOR SYMBOLS (graph data: g['named_symbols']) -> their readable
    # prose name FIRST (before the generic font-wrapper unwrap would strip
    # \operatorname{Ker} to the bare token 'Ker'). This is the held reader reading
    # the symbolic shorthand structurally — `\operatorname{Ker}`/`Ker` -> 'kernel',
    # `h_*` -> 'the hurewicz map' — the SAME words the prose atoms/operators cover.
    # Longest-symbol-first so a multi-char symbol wins over its substring. The
    # symbols are matched as literal LaTeX (escaped); a function-name spelling like
    # 'Ker' is bounded so it does not fire inside a longer identifier.
    for ns in sorted(g.get("named_symbols", []),
                     key=lambda e: -len(e.get("symbol", ""))):
        sym = ns.get("symbol", "")
        word = ns.get("word", "")
        if not sym:
            continue
        if re.match(r"^[A-Za-z]", sym):
            # a bare function-name spelling ('Ker'): word-bounded so it does not
            # fire inside a longer token.
            s = re.sub(r"(?<![A-Za-z])" + re.escape(sym) + r"(?![A-Za-z])",
                       " " + word + " ", s)
        else:
            s = s.replace(sym, " " + word + " ")
    # named operators written as \operatorname{im}/{ker}/{coker}/... -> their word
    # FIRST (before the generic font-wrapper unwrap would strip them to 'im').
    s = re.sub(r"\\operatorname\s*\{\s*im\s*\}", " image ", s)
    s = re.sub(r"\\operatorname\s*\{\s*ker\s*\}", " kernel ", s)
    s = re.sub(r"\\operatorname\s*\{\s*coker\s*\}", " cokernel ", s)
    s = re.sub(r"\\operatorname\s*\{\s*rank\s*\}", " rank ", s)

    # blackboard + font wrappers + greek -> their readable token (longest-key
    # first so '\mathbb{Z}' beats a bare '\mathbb').
    for tex, rep in sorted(g.get("blackboard", {}).items(), key=lambda kv: -len(kv[0])):
        s = s.replace(tex, " " + rep + " ")
    # font wrappers: \mathcal{C} -> C, \mathrm{Spin} -> Spin, \text{...} -> text.
    for w in sorted(g.get("font_wrappers", []), key=lambda x: -len(x)):
        s = re.sub(re.escape(w) + r"\s*\{([^{}]*)\}", r" \1 ", s)
    for tex, rep in sorted(g.get("greek", {}).items(), key=lambda kv: -len(kv[0])):
        s = re.sub(re.escape(tex) + r"(?![A-Za-z])", " " + rep + " ", s)

    # set-builder \{ x \mid P \} / \{ x : P \} -> 'the set of x such that P'.
    s = re.sub(r"\\\{(.*?)\\(?:mid|;)?(.*?)\\\}",
               lambda m: " the set of " + m.group(1).strip()
               + (" such that " + m.group(2).strip() if m.group(2).strip() else "")
               + " ", s, flags=re.DOTALL)
    s = s.replace("\\{", " { ").replace("\\}", " } ")
    s = s.replace("\\mid", " such that ").replace("\\,", " ").replace("\\;", " ")
    s = s.replace("\\!", "").replace("\\quad", " ").replace("\\qquad", " ")

    # relation macros -> readable words.
    for rel in sorted(g.get("relation_macros", []),
                      key=lambda r: -len(r["latex"])):
        s = re.sub(re.escape(rel["latex"]) + r"(?![A-Za-z])",
                   " " + rel["word"] + " ", s)
    # structure macros that have a clean word: \frac{A}{B} -> 'A over B'.
    s = re.sub(r"\\d?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}",
               r" \1 over \2 ", s)
    # named-operator + structure macros -> their readable word.
    for tex, word in sorted(_RENDER_WORDS.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(re.escape(tex) + r"(?![A-Za-z])", " " + word + " ", s)

    # OPERATOR APPLICATION '<op-word> ( arg )' -> '<op-word> of arg' (the prose the
    # construction grammar's prefix-op constructions read: 'kernel of {x}'). A named
    # operator applied by PARENS (f(x)) is the SAME structure as 'f of x' — the held
    # reader renders the application to the prose form so the SAME prefix-op
    # construction fires. Driven by the operator NAMES the grammar holds (operator
    # macros + the named symbols), so it is general, not keyed to 'kernel'.
    op_words = {m.get("name") for m in g.get("operator_macros", [])
                if m.get("name")}
    op_words |= {ns.get("word") for ns in g.get("named_symbols", [])
                 if ns.get("word") and " " not in ns.get("word", "")}
    for w in sorted(op_words, key=lambda x: -len(x)):
        s = re.sub(r"(?<![A-Za-z])" + re.escape(w) + r"\s*\(", w + " of ( ", s)

    # remaining macros: \operatorname{Spec} already handled by font wrappers; a
    # bare leftover control word -> its name (drop the backslash) so it survives
    # as a token rather than vanishing.
    s = re.sub(r"\\([A-Za-z]+)", r" \1 ", s)
    # drop math spacing / alignment leftovers.
    s = s.replace("&", " ").replace("\\\\", " ")
    # keep sub/superscripts compact on their head: 'H _ { n }' -> 'H_n', but a
    # standalone braces group already flattened below.
    s = re.sub(r"\s*\^\s*\{([^{}]*)\}", lambda m: "^" + _flatten_braces(m.group(1)).strip(), s)
    s = re.sub(r"\s*_\s*\{([^{}]*)\}", lambda m: "_" + _flatten_braces(m.group(1)).strip(), s)
    s = re.sub(r"\s*\^\s*([A-Za-z0-9])", r"^\1", s)
    s = re.sub(r"\s*_\s*([A-Za-z0-9])", r"_\1", s)
    s = _flatten_braces(s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


# ---------------------------------------------------------------------------
# PARSE — LaTeX formula -> the OPERATOR-TREE (the SAME shape comprehend_structure
# composes): {op, args:[child...], held_runnable} for an operator, {term, held,
# index?} for an atomic bedrock term. The agent READS the LaTeX into the operator-
# tree it already holds; ∂ (\partial) maps to the HELD boundary_operator atom.
#
# The grammar is applied MECHANICALLY (mirroring how _comprehend_structure applies
# math_prose_constructions): tokenise the formula into LaTeX tokens, then recurse
#   QUOTIENT ('/' or \frac)  ->  modulo(left, right)
#   prefix operator (\ker X) ->  kernel(X)         [un-held]
#   indexed head  (H_n(X))   ->  homology(X)@n     [un-held]
#   \partial[_n]             ->  boundary_operator  [HELD atom, recursion bottom]
# bottoming out at a held atom / a named-term leaf. No decision over graph state.
# ---------------------------------------------------------------------------

_MAX_DEPTH = 12


def _macro_maps(g: dict) -> dict:
    """Build the lookup tables the parser uses from the grammar data."""
    ops = {m["latex"]: m for m in g.get("operator_macros", [])}
    struct = {m["latex"]: m for m in g.get("structure_macros", [])}
    heads = g.get("indexed_heads", [])
    return {"ops": ops, "struct": struct, "heads": heads}


def _tokenize(latex: str) -> list[str]:
    """Tokenise a LaTeX math formula into atoms the parser splits on: control
    sequences (\\partial, \\ker, \\operatorname{im}), braces, sub/superscript
    markers, parens, the quotient '/', and bare letters/digits. A surface op."""
    s = latex.strip()
    toks: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c == "\\":
            # a control sequence. \operatorname{im} keeps its brace arg ATTACHED
            # (the grammar key is the whole `\operatorname{im}`); every OTHER macro
            # (\frac, \binom, \dim, \lvert, ...) does NOT slurp a following brace —
            # its arguments are separate { } groups the parser splits off. (A bare
            # `\\[A-Za-z]+\{...\}` rule wrongly attached \frac's FIRST arg, breaking
            # the two-brace \frac{A}{B} / \binom{n}{k} structure.) Keyed on the macro
            # SYNTAX (\operatorname is the brace-name wrapper), not per-formula.
            m = re.match(r"\\(?:operatorname|mathrm|mathbf|mathcal|mathit|text)\{[^{}]*\}", s[i:])
            if m is None:
                m = re.match(r"\\[A-Za-z]+", s[i:])
            if m:
                toks.append(m.group(0))
                i += len(m.group(0))
                continue
            # \{ \} \, etc.
            toks.append(s[i:i + 2])
            i += 2
            continue
        if c in "{}()_^/+-*=|,;":
            # '|' is the cardinality/abs bar (|X|), a single-char token like a paren.
            # ',' and ';' are STRUCTURAL argument separators inside a functor's
            # argument list (H^n(G, M) / H_n(X; A)): the comma/semicolon splits the
            # compound object into its typed argument slots (space, coefficients),
            # so they are kept as tokens, NOT dropped as unmodelled punctuation.
            toks.append(c)
            i += 1
            continue
        # a run of letters/digits (a name / number).
        m = re.match(r"[A-Za-z0-9]+", s[i:])
        if m:
            toks.append(m.group(0))
            i += len(m.group(0))
            continue
        i += 1  # skip punctuation we do not model.
    return toks


def _split_top(toks: list[str], sep: str) -> Optional[tuple[list, list]]:
    """Split a token list on the FIRST top-level (brace/paren-depth-0) occurrence
    of `sep`, returning (left, right) or None. Used for the quotient '/'."""
    depth = 0
    for i, t in enumerate(toks):
        if t in "{(":
            depth += 1
        elif t in "})":
            depth -= 1
        elif depth == 0 and t == sep:
            return toks[:i], toks[i + 1:]
    return None


def _split_top_args(toks: list[str]) -> list[list]:
    """Split a functor's argument-group token list on its TOP-LEVEL (depth-0)
    argument separators ',' and ';' into one token-list per argument slot. The
    comma/semicolon between two operands of a homological-functor head (H^n(G, M),
    H_n(X; A), Ext^n(A, B)) separates the COMPOUND OBJECT into its typed slots
    (space, coefficients). Nested brackets are respected (a comma inside (...) /
    {...} stays in its sub-argument). With no top-level separator the whole group
    is one argument (the bare H_n(X) case)."""
    parts: list[list] = []
    depth = 0
    cur: list[str] = []
    for t in toks:
        if t in "{(":
            depth += 1
            cur.append(t)
        elif t in "})":
            depth -= 1
            cur.append(t)
        elif depth == 0 and t in (",", ";"):
            parts.append(cur)
            cur = []
        else:
            cur.append(t)
    parts.append(cur)
    return [p for p in parts if p]


def _split_top_last(toks: list[str], seps: tuple[str, ...]) -> Optional[tuple[list, str, list]]:
    """Split on the LAST top-level (depth-0) occurrence of any token in `seps`,
    returning (left, sep, right) — LEFT-associative parsing for an arithmetic chain.
    A leading sign (e.g. the '-' of '-1', or a unary '-' at position 0) is NOT a
    binary split: a sep at index 0 (no left operand) is skipped."""
    depth = 0
    found = None
    for i, t in enumerate(toks):
        if t in "{(":
            depth += 1
        elif t in "})":
            depth -= 1
        elif depth == 0 and t in seps and i > 0:
            found = i
    if found is None:
        return None
    return toks[:found], toks[found], toks[found + 1:]


def _parse_arith(toks: list[str], maps: dict, g: dict, depth: int) -> Optional[dict]:
    """Parse a GENERAL arithmetic chain over the infix_arith operators (+, -, *) with
    PRECEDENCE (+/- loosest, * tighter) and LEFT-associativity. The structure is read
    off the actual operator SYMBOLS — NOT a shape template. Returns the operator-tree
    node {op, args:[l, r], held_runnable} or None if no top-level arith operator."""
    arith = {tex: sm for tex, sm in maps["struct"].items() if sm.get("infix_arith")}
    if not arith:
        return None
    # precedence tiers, loosest first: split on +/-, then *.
    for tier in (tuple(t for t in ("+", "-") if t in arith),
                 tuple(t for t in ("*",) if t in arith)):
        if not tier:
            continue
        sp = _split_top_last(toks, tier)
        if sp is None:
            continue
        left_toks, sep, right_toks = sp
        if not left_toks or not right_toks:
            continue
        left = _parse(left_toks, maps, g, depth + 1)
        right = _parse(right_toks, maps, g, depth + 1)
        if left is None or right is None:
            return None
        sm = arith[sep]
        return {"op": sm["op"], "args": [left, right],
                "held_runnable": bool(sm.get("held_runnable", False))}
    return None


def _strip_outer_group(toks: list[str]) -> list[str]:
    """Strip a single fully-enclosing ( ) or { } pair."""
    if len(toks) >= 2 and toks[0] in "({" and toks[-1] in ")}":
        depth = 0
        for i, t in enumerate(toks):
            if t in "({":
                depth += 1
            elif t in ")}":
                depth -= 1
                if depth == 0:
                    return toks[1:-1] if i == len(toks) - 1 else toks
    return toks


def _parse(toks: list[str], maps: dict, g: dict, depth: int) -> Optional[dict]:
    """Recursively parse a LaTeX token list into an operator-tree node (the SAME
    shape comprehend_structure composes). Returns None on honest un-comprehension."""
    if depth > _MAX_DEPTH or not toks:
        return None
    toks = _strip_outer_group(toks)
    if not toks:
        return None

    # \sum-BINDER (the fold) — a leading \sum_{binder}^{range} (or \sum_binder)
    # consumes its bound + range + the recursively-parsed BODY into a Sum fold node.
    # The GENERAL big-operator construction (any \sum of any body), keyed on the
    # \sum SYNTAX, not a per-formula pattern.
    node = _parse_big_operator(toks, maps, g, depth)
    if node is not None:
        return node

    # QUOTIENT — top-level '/' is the homology quotient -> modulo(left, right).
    sp = _split_top(toks, "/")
    if sp is not None:
        left = _parse(sp[0], maps, g, depth + 1)
        right = _parse(sp[1], maps, g, depth + 1)
        if left is not None and right is not None:
            sm = maps["struct"].get("/", {})
            return {"op": sm.get("op", "modulo"), "args": [left, right],
                    "held_runnable": bool(sm.get("held_runnable", False))}

    # TWO-BRACE STRUCTURE MACRO leading the run — \frac{A}{B} (-> modulo/div),
    # \binom{n}{k} (-> binomial). The tokenizer keeps the macro token then two brace
    # groups; split them off and recursively parse each. The GENERAL braced-macro
    # construction (any \macro{A}{B} whose grammar entry says args==2), keyed on the
    # macro SYNTAX, not per-formula.
    if toks and toks[0] in maps["struct"] and \
            maps["struct"][toks[0]].get("args") == 2 and \
            maps["struct"][toks[0]].get("braced"):
        rest = toks[1:]
        grp1, after1 = _take_group(rest)
        grp2, after2 = _take_group(after1)
        if grp1 and grp2 and not after2:
            left = _parse(grp1, maps, g, depth + 1)
            right = _parse(grp2, maps, g, depth + 1)
            if left is not None and right is not None:
                sm = maps["struct"][toks[0]]
                return {"op": sm["op"], "args": [left, right],
                        "held_runnable": bool(sm.get("held_runnable", False))}

    # CARDINALITY / ABSOLUTE VALUE — |X| or \lvert X \rvert -> abs(X). The bars
    # enclose a recursively-parsed body. The GENERAL bar-delimiter construction,
    # keyed on the | / \lvert..\rvert SYNTAX. Held-runnable (the DSL Abs Term).
    bar = _parse_cardinality(toks, maps, g, depth)
    if bar is not None:
        return bar

    # INFIX ARITHMETIC (+, -, *) — the GENERAL arithmetic constructions, parsed with
    # PRECEDENCE + LEFT-ASSOCIATIVITY (not a per-formula template). +/- bind loosest
    # (split on the LAST top-level +/- so a - b + c reads as (a - b) + c), * binds
    # tighter. So b_0 - b_1 + b_2 - b_3 -> minus(plus(minus(b_0,b_1),b_2),b_3) and
    # (-1)^k * b_k -> times((-1)^k, b_k). The structure comes from the SYMBOLS, read
    # off the actual +/-/* operators — no shape label, no classification.
    node = _parse_arith(toks, maps, g, depth)
    if node is not None:
        return node

    # INFIX structure macro (A \otimes B, A \oplus B, A \cong B, A \to B) ->
    # op(A, B). Split on the FIRST top-level infix macro; comprehend both sides.
    for tex, sm in maps["struct"].items():
        if tex == "/" or sm.get("op") == "modulo" or sm.get("args") != 2 \
                or sm.get("infix_arith"):
            continue
        sp2 = _split_top(toks, tex)
        if sp2 is not None and sp2[0] and sp2[1]:
            left = _parse(sp2[0], maps, g, depth + 1)
            right = _parse(sp2[1], maps, g, depth + 1)
            if left is not None and right is not None:
                return {"op": sm["op"], "args": [left, right],
                        "held_runnable": bool(sm.get("held_runnable", False))}

    # POWER (x^k, (-1)^k) — a base (recursively parsed: a parenthesised group, a
    # bare symbol, a number) raised to an exponent -> pow(base, exp). The GENERAL
    # power construction (any base^exp), keyed on the ^ SYNTAX. Runs before the
    # indexed-symbol leaf so a COMPOUND base ((-1)) is parsed, not just a bare head.
    node = _parse_power(toks, maps, g, depth)
    if node is not None:
        return node

    # UNARY MINUS (-1, -b_k) — a leading '-' with no left operand -> neg(x). The
    # general unary-sign construction (the base of (-1)^k after the group strip).
    if toks and toks[0] == "-":
        inner = _parse(toks[1:], maps, g, depth + 1)
        if inner is not None:
            return {"op": "neg", "args": [inner], "held_runnable": True}

    # PREFIX operator macro (\ker X, \operatorname{im} X, \dim X) -> op(X).
    if toks and toks[0] in maps["ops"] and \
            maps["ops"][toks[0]].get("kind") == "operator":
        om = maps["ops"][toks[0]]
        inner = _parse(toks[1:], maps, g, depth + 1)
        if inner is not None:
            return {"op": om["name"], "args": [inner],
                    "held_runnable": bool(om.get("held_runnable", False))}

    # INDEXED HEAD (H_n(X), H^n(X), \pi_n(X)) -> homology/cohomology(X) @ degree n.
    node = _parse_indexed_head(toks, maps, g, depth)
    if node is not None:
        return node

    # an ATOM macro possibly subscripted (\partial_n, \partial_{n+1}, an acquired
    # \bd_n) -> the held/named atom, carrying the degree index. The recursion
    # bottoms out at a held atom (∂). Generic over all kind=='atom' operator macros.
    node = _parse_atom_macro(toks, maps, g)
    if node is not None:
        return node

    # JUXTAPOSITION (implicit product) — two adjacent FACTORS with no infix operator
    # between them ((-1)^k b_k, k b_k) -> times(factor1, factor2). The GENERAL
    # implicit-product construction: split the token run into its top-level factors
    # (a power-with-base, a parenthesised group, an indexed leaf) and Times them.
    # Runs AFTER the structural forms (indexed head H^n(X), prefix op, atom macro) so
    # an applied head/operator wins over a spurious product split.
    node = _parse_juxtaposition(toks, maps, g, depth)
    if node is not None:
        return node

    # SUBSCRIPTED / SUPERSCRIPTED SYMBOL LEAF (b_0, b_k, b_{n}, 1^k) — a bare name
    # token carrying a sub/superscript index is an INDEXED SYMBOL leaf, the index
    # read off the actual subscript. GENERAL (any letter/number + an index), NOT a
    # per-formula template: b_i is the i-th betti number, a_k the k-th coefficient.
    # The subscript -> `subscript`, the superscript -> `superscript` (a power).
    node = _parse_indexed_symbol(toks)
    if node is not None:
        return node

    # ATOM bedrock — a bare named token (X, A, a manifold name) is a held/leaf term.
    bare = [t for t in toks if t not in "{}()_^"]
    if bare and all(re.fullmatch(r"[A-Za-z0-9]+", t) for t in bare):
        return {"term": "".join(bare), "held": False}
    return None


def _take_one_factor(toks: list[str]) -> tuple[list, list]:
    """Take ONE self-contained factor off the front of a token list, returning
    (factor_toks, rest). A factor is a leading ATOM (a parenthesised ( ) group, a
    brace { } group, a leading unary '-' carrying its operand, a control sequence,
    or a bare letter/number head) PLUS any trailing _<idx> / ^<exp> sub/superscripts
    (each marker carrying its braced-or-single group). General — keyed on the
    bracket/script SYNTAX, no per-formula knowledge."""
    if not toks:
        return [], []
    out: list[str] = []
    rest = toks
    # a leading unary '-' binds to the following factor: -(...)^k, -1.
    sign: list[str] = []
    if rest and rest[0] == "-":
        sign = ["-"]
        rest = rest[1:]
    # the head atom.
    if rest and rest[0] == "(":
        grp, after = _take_paren(rest)
        out = ["("] + grp + [")"]
        rest = after
    elif rest and rest[0] == "{":
        grp, after = _take_group(rest)
        out = ["{"] + grp + ["}"]
        rest = after
    elif rest:
        out = [rest[0]]
        rest = rest[1:]
    else:
        return [], []
    # trailing sub/superscript markers, each with its (braced/single) group.
    while rest and rest[0] in ("_", "^"):
        marker = rest[0]
        grp, rest = _take_group(rest[1:])
        # re-wrap a multi-token index in braces so the factor re-parses cleanly.
        if len(grp) == 1:
            out += [marker] + grp
        else:
            out += [marker, "{"] + grp + ["}"]
    return sign + out, rest


def _split_factors(toks: list[str]) -> list[list]:
    """Split a token run into its top-level FACTORS (adjacent units with no infix
    operator between them). Returns the list of factor token-lists. A run of >= 2
    factors is an implicit product (juxtaposition). If any top-level token is an
    infix/relation/quotient operator, this is NOT a pure juxtaposition -> returns a
    single factor (the whole run) so the caller defers to the infix parsers."""
    factors: list[list] = []
    rest = list(toks)
    while rest:
        # an infix operator at the (post-first) top level means this is not a pure
        # juxtaposition: bail so the arith/structure parsers handle it.
        if rest[0] in ("+", "*", "/", "=", "_", "^") and factors:
            return [list(toks)]
        fac, rest = _take_one_factor(rest)
        if not fac:
            return [list(toks)]
        factors.append(fac)
    return factors


def _parse_juxtaposition(toks: list[str], maps: dict, g: dict,
                         depth: int) -> Optional[dict]:
    """Two+ adjacent FACTORS with no infix operator -> a left-nested times(...). The
    GENERAL implicit-product construction ((-1)^k b_k -> times((-1)^k, b_k); k b_k ->
    times(k, b_k)). Each factor is recursively parsed; the structure comes from the
    adjacency of the symbols, not a template."""
    factors = _split_factors(toks)
    if len(factors) < 2:
        return None
    nodes = []
    for fac in factors:
        n = _parse(fac, maps, g, depth + 1)
        if n is None:
            return None
        nodes.append(n)
    # left-nested binary times so the emitter's binary map applies uniformly.
    acc = nodes[0]
    for nxt in nodes[1:]:
        acc = {"op": "times", "args": [acc, nxt], "held_runnable": True}
    return acc


def _parse_cardinality(toks: list[str], maps: dict, g: dict,
                       depth: int) -> Optional[dict]:
    """|X| or \\lvert X \\rvert (cardinality / absolute value) -> abs(<body>). The
    bars enclose a recursively-parsed body. GENERAL (any body between the bars),
    keyed on the bar SYNTAX. The whole run must be the bracketed form (open bar,
    body, close bar) — a stray '|' inside a larger expression is not consumed here.
    Held-runnable: maps to the DSL Abs Term in the emitter."""
    if len(toks) < 3:
        return None
    open_tok = toks[0]
    if open_tok == "|":
        close = "|"
    elif open_tok == "\\lvert":
        close = "\\rvert"
    else:
        return None
    # the body is everything up to the matching CLOSING bar; the close must be the
    # LAST token (the whole run is the bar form). For '|' the closing is the last '|'.
    if toks[-1] != close:
        return None
    body_toks = toks[1:-1]
    if not body_toks or "|" in body_toks or "\\lvert" in body_toks \
            or "\\rvert" in body_toks:
        return None  # nested/unbalanced bars — not the simple cardinality form.
    body = _parse(body_toks, maps, g, depth + 1)
    if body is None:
        return None
    return {"op": "abs", "args": [body], "held_runnable": True}


def _parse_power(toks: list[str], maps: dict, g: dict,
                 depth: int) -> Optional[dict]:
    """A base raised to an exponent -> pow(base, exp). The base is the leading factor
    (a parenthesised group (-1), a bare symbol/number) up to a top-level '^'; the
    exponent is the braced/single group after it. GENERAL (any base^exp), keyed on
    the ^ syntax. Handles a COMPOUND base (parenthesised) the bare-leaf path cannot:
    (-1)^k -> pow(neg(1), k)."""
    if not toks or "^" not in toks:
        return None
    # the BASE atom only (NO trailing scripts) — a parenthesised group, a brace
    # group, or a single head — so the following '^' is the power marker.
    if toks[0] == "(":
        base_toks, rest = _take_paren(toks)
        base_toks = ["("] + base_toks + [")"]
    elif toks[0] == "{":
        inner, rest = _take_group(toks)
        base_toks = ["{"] + inner + ["}"]
    else:
        base_toks, rest = [toks[0]], toks[1:]
    # the base must be a COMPOUND base (parenthesised / braced); a bare head^k
    # (b^k / 1^k) is left to the indexed-symbol leaf path.
    if base_toks[0] not in ("(", "{"):
        return None
    # the factor must end exactly at a top-level '^' with an exponent following, and
    # consume the WHOLE run (else this is juxtaposition / something else).
    if not rest or rest[0] != "^":
        return None
    exp_grp, after = _take_group(rest[1:])
    if after:
        return None  # trailing tokens -> not a clean single power.
    base = _parse(base_toks, maps, g, depth + 1)
    exp = _parse(exp_grp, maps, g, depth + 1)
    if base is None or exp is None:
        return None
    return {"op": "power", "args": [base, exp], "held_runnable": True}


def _parse_big_operator(toks: list[str], maps: dict, g: dict,
                        depth: int) -> Optional[dict]:
    """A leading big-operator macro (\\sum, \\prod, ...) with a binder + range + a
    recursively-parsed BODY -> a fold node {op, binder, range, args:[body]}. The
    GENERAL binder construction: \\sum_{k=0}^{n} <body> -> the fold over k in [0..n];
    \\sum_k <body> -> the fold over k in the HELD default family (no explicit range).
    Keyed on the \\sum SYNTAX (any binder, any range, any body), not a template."""
    if not toks:
        return None
    bigops = {m["latex"]: m for m in g.get("quantifier_macros", [])}
    head = toks[0]
    if head not in bigops:
        return None
    bm = bigops[head]
    rest = toks[1:]
    binder = None
    lo = None
    hi = None
    # the subscript: either a bound assignment \sum_{k=0}^{n} or a bare \sum_k.
    if rest and rest[0] == "_":
        grp, rest = _take_group(rest[1:])
        # a "k = 0" assignment binds the var + the lower limit; a bare "k" the var.
        sp = _split_top(grp, "=")
        if sp is not None:
            binder = "".join(sp[0]).strip()
            lo = "".join(sp[1]).strip()
        else:
            binder = "".join(grp).strip()
    if binder is None:
        return None  # a \sum with no binder is not the fold form we model.
    # the superscript: the upper limit \sum^{n}.
    if rest and rest[0] == "^":
        grp, rest = _take_group(rest[1:])
        hi = "".join(grp).strip()
    # the BODY: everything remaining, recursively parsed (the general body).
    body = _parse(rest, maps, g, depth + 1)
    if body is None:
        return None
    node: dict[str, Any] = {"op": bm["op"], "binder": binder,
                            "args": [body],
                            "held_runnable": bool(bm.get("held_runnable", False))}
    # the range: [lo..hi] when explicit; None -> the held default family (0..dim).
    if lo is not None or hi is not None:
        node["range"] = {"lo": lo, "hi": hi}
    return node


def _parse_indexed_symbol(toks: list[str]) -> Optional[dict]:
    """A bare symbol token with a sub/superscript index (b_0, b_k, b_{n+1}, 1^k) ->
    an INDEXED-SYMBOL leaf {term, subscript?/superscript?, held:false}. GENERAL: any
    single name/number head + an index; the index read off the actual _/^ in the
    symbols. Not an indexed HEAD (those take a (X) argument) — a leaf quantity."""
    if not toks or toks[0] in "{}()_^/+-*=":
        return None
    if not re.fullmatch(r"[A-Za-z0-9]+", toks[0]):
        return None
    head = toks[0]
    rest = toks[1:]
    out: dict[str, Any] = {"term": head, "held": False}
    saw_index = False
    # consume a _<idx> and/or ^<idx> (either order); each index a flattened group.
    while rest and rest[0] in ("_", "^"):
        marker = rest[0]
        grp, rest = _take_group(rest[1:])
        idx = "".join(grp)
        out["subscript" if marker == "_" else "superscript"] = idx
        saw_index = True
    if rest:  # trailing tokens we did not consume -> not a clean leaf.
        return None
    if not saw_index:
        return None
    return out


def _take_group(toks: list[str]) -> tuple[list, list]:
    """Take a leading { ... } (or single token) group off a token list, returning
    (group_inner, rest)."""
    if not toks:
        return [], []
    if toks[0] == "{":
        depth = 0
        for i, t in enumerate(toks):
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
                if depth == 0:
                    return toks[1:i], toks[i + 1:]
        return toks[1:], []
    return [toks[0]], toks[1:]


def _read_index(toks: list[str]) -> tuple[Optional[str], list]:
    """Read a subscript/superscript index after a head: '_n' / '_{n+1}' / '^n'.
    Returns (index_string or None, remaining tokens)."""
    if toks and toks[0] in ("_", "^"):
        grp, rest = _take_group(toks[1:])
        return "".join(grp), rest
    return None, toks


def _parse_atom_macro(toks: list[str], maps: dict, g: dict) -> Optional[dict]:
    """An ATOM macro (\\partial, or an acquired alias \\bd), optionally subscripted
    (∂_n / ∂_{n+1}) -> the held/named atom carrying its degree index. The bottom of
    the recursion (a HELD atom like ∂). Generic over all kind=='atom' macros."""
    if not toks:
        return None
    atoms = {m["latex"]: m for m in g.get("operator_macros", [])
             if m.get("kind") == "atom"}
    head = toks[0]
    if head not in atoms:
        return None
    am = atoms[head]
    idx, rest = _read_index(toks[1:])
    if rest and any(t not in "{}()" for t in rest):
        return None  # trailing application we do not model -> clean form only.
    node: dict[str, Any] = {"term": am["name"], "held": bool(am.get("held"))}
    if idx is not None:
        node["index"] = idx
    return node


def _parse_indexed_head(toks: list[str], maps: dict, g: dict,
                        depth: int) -> Optional[dict]:
    """An indexed head H_n(X) / H^n(X) / \\pi_n(X) -> the homology/cohomology/...
    operator over X, in the indicated degree. The sub vs super script selects the
    role (homology vs cohomology) per the grammar."""
    if not toks:
        return None
    head_tok = toks[0]
    cand = [h for h in maps["heads"] if h["latex"] == head_tok]
    if not cand:
        return None
    idx, rest = _read_index(toks[1:])
    if idx is None:
        return None
    # which role: the script that was present. We re-read whether it was _ or ^.
    script = toks[1] if len(toks) > 1 and toks[1] in ("_", "^") else "_"
    chosen = None
    for h in cand:
        if script == "_" and h.get("sub_role"):
            chosen = h
            break
        if script == "^" and h.get("super_role"):
            chosen = h
            break
    if chosen is None:
        chosen = cand[0]
    # the argument: a following (X) application, else nothing (a bare H_n). The
    # argument group is a COMPOUND OBJECT: its top-level commas/semicolons split it
    # into the head's TYPED argument slots (space, coefficients) — so H^n(G, M) types
    # as a TWO-argument functor (the group/space slot + the coefficient module), NOT
    # a `times(G, M)` product. The slot ROLES come from the grammar DATA
    # (chosen["arg_slots"]); with fewer args than slots the extra slots are absent
    # (honest partial typing). Driven by the seed, no per-formula decision.
    arg_nodes: list = []
    if rest and rest[0] in "({":
        grp, after = _take_group(rest) if rest[0] == "{" else _take_paren(rest)
        if not after:
            for part in _split_top_args(grp):
                pn = _parse(part, maps, g, depth + 1)
                if pn is not None:
                    arg_nodes.append(pn)
    slots = chosen.get("arg_slots")
    node: dict[str, Any] = {"op": chosen["name"],
                            "args": arg_nodes,
                            "held_runnable": bool(chosen.get("held_runnable",
                                                             False)),
                            "index": idx}
    if slots:
        # name each present argument by its slot role (space/coefficients/...).
        node["arg_roles"] = slots[:len(arg_nodes)]
    return node


def _take_paren(toks: list[str]) -> tuple[list, list]:
    """Take a leading ( ... ) group, returning (inner, rest)."""
    if toks and toks[0] == "(":
        depth = 0
        for i, t in enumerate(toks):
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1
                if depth == 0:
                    return toks[1:i], toks[i + 1:]
    return [toks[0]] if toks else [], toks[1:] if toks else []


def _structure_repr(node: dict) -> str:
    """Render an operator-tree as op(args), with ∂'s degree index — e.g.
    modulo(kernel(boundary_operator_n), image(boundary_operator_n+1))."""
    if "term" in node:
        idx = node.get("index")
        sub = node.get("subscript")
        sup = node.get("superscript")
        base = str(node["term"])
        if sub is not None:
            base += f"_{sub}"
        if sup is not None:
            base += f"^{sup}"
        return f"{base}_{idx}" if idx else base
    # a BINDER fold (\sum / \prod / \min / \max) renders with its binder + range:
    # sum[k in 0..n](<body>), prod[k in default](<body>), min[k in 0..n](<body>).
    # General over any fold node carrying a `binder` (not keyed to 'sum').
    if "binder" in node:
        rng = node.get("range")
        if rng is None:
            span = "default"
        else:
            span = f"{rng.get('lo') if rng.get('lo') is not None else '?'}.." \
                   f"{rng.get('hi') if rng.get('hi') is not None else '?'}"
        body = _structure_repr(node["args"][0]) if node.get("args") else ""
        return f"{node['op']}[{node['binder']} in {span}]({body})"
    idx = node.get("index")
    head = f"{node['op']}" + (f"@{idx}" if idx else "")
    return head + "(" + ", ".join(_structure_repr(a)
                                  for a in node.get("args", [])) + ")"


def _unheld_ops(node: dict, out: Optional[list] = None) -> list:
    """The operations in the tree that are NOT held_runnable — the named residual
    (acquirable by reading), outermost-first. Mirrors construction_grammar."""
    out = [] if out is None else out
    if "term" in node:
        return out
    if not node.get("held_runnable") and node["op"] not in out:
        out.append(node["op"])
    for child in node.get("args", []):
        if isinstance(child, dict):
            _unheld_ops(child, out)
    return out


def _held_atoms(node: dict, out: Optional[list] = None) -> list:
    """The HELD atoms (∂) the recursion bottomed out at."""
    out = [] if out is None else out
    if "term" in node:
        if node.get("held"):
            out.append(node["term"])
        return out
    for child in node.get("args", []):
        if isinstance(child, dict):
            _held_atoms(child, out)
    return out


def parse_formula(latex: str) -> Optional[dict]:
    """READ a LaTeX FORMULA into the operator-tree the agent already composes.

    The real homology LaTeX
        H_n(X) = \\ker \\partial_n / \\operatorname{im} \\partial_{n+1}
    parses (taking the RHS of the '=') into
        modulo(kernel(boundary_operator_n), image(boundary_operator_n+1))
    — the SAME structure the agent already COMPUTES in compute_homology, with
    \\partial recognised as the HELD boundary_operator atom (the recursion bottom).

    Returns {structure, repr, unheld_ops, held_atoms, comprehends} or None (honest
    un-comprehension). The un-held ops (kernel/image/modulo) are the NAMED residual
    already named in math_prose_constructions — acquirable by reading the next
    instance. Driven by the GRAPH-DATA grammar; no decision over graph state."""
    if not latex:
        return None
    g = load_grammar()
    maps = _macro_maps(g)
    # strip math delimiters if present.
    s = latex.strip()
    s = re.sub(r"^\$+|\$+$", "", s)
    s = re.sub(r"^\\[\[(]|\\[\])]$", "", s).strip()
    # a definitional formula 'H_n(X) = <RHS>' — parse the RHS (the structure).
    eq = _split_top(_tokenize(s), "=")
    toks = eq[1] if eq is not None else _tokenize(s)
    node = _parse(toks, maps, g, 0)
    if node is None:
        return None
    return {"structure": node, "repr": _structure_repr(node),
            "unheld_ops": _unheld_ops(node), "held_atoms": _held_atoms(node),
            "comprehends": True}


__all__ = ["load_grammar", "render", "parse_formula"]
