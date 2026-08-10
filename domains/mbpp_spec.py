"""mbpp_spec — Arc 2 Q2: SPEC COMPREHENSION for benchmark prose.

PROGRAM_SYNTHESIS_ARC2_PLAN.md's Q2, `PROGRAM_SYNTHESIS_ARC2_PREREG.md`
(the three-way PRIMARY/SECONDARY-OFFICIAL/STRESS split protocol, §0; HQ2,
§4 — spec-EXTRACTION quality, not recognition, since recognition already
sits at 256/257 zero-shot per `scripts/mbpp_zero_shot_baseline.py` /
`PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md`), `PROGRAM_SYNTHESIS_ARC2_Q0_
BASELINE.md` (the assert-parseability taxonomy this module extends:
math_isclose 13 tasks / set_wrapper 3 / set_literal_value 2 — the three
named Q1/Q2-boundary gaps this module closes honestly).

This is the SHARED, MECHANICAL spec layer benchmark-prose comprehension
funnels through: asserts -> example rows, prompts -> request facts +
signature facts. It SUPERSEDES `scripts/mbpp_zero_shot_baseline.py`'s
`classify_assert`/`build_task_rows` as the parser both Q0-A's frozen
baseline (kept byte-identical, never touched by this track) and every
later arc-2 phase should call — this module is a strict SUPERSET of that
parser's supported forms (same rows on every form both support; gated by
`tests/test_mbpp_spec_migrated.py`'s cross-parser equivalence-on-overlap
test, which imports `mbpp_zero_shot_baseline` read-only).

ARCHITECTURE (CLAUDE.md). Every function here is MECHANICAL translation —
`ast.parse` + `ast.literal_eval` on CONSTANT sub-nodes only (never
`eval`/`exec` of benchmark text), fixed positional/text-prep extraction,
or a graph QUERY (reading held Concept nodes, never deciding from them).
There is exactly one Rust/graph-decision boundary this module respects:
`request_facts` computes FACTS (verb-frame tag, residual clause,
constraint-word hits) for a downstream cue RULE to consume; it makes no
routing decision itself, the same status `code_writing._content_tokens`
/ `code_writing._request_cue_sets` already have. `parse_asserts` and
`signature_facts` never read a task's `code` field (the reference
solution) — signature facts are derived ONLY from the parsed example
rows ("never from prose"), so this module is safe to call against a live
test-split task at synthesis run time, not just for offline measurement.

THREE Q1/Q2-BOUNDARY FORMS THIS MODULE ADDS over `mbpp_zero_shot_
baseline.classify_assert` (named in the prereg's §0 cross-parser honesty
note and §4 HQ2):

  1. `math.isclose(f(args), expected, rel_tol=tol)` -> a FLOAT row with an
     explicit `tol` field (the corpus's uniform shape: 2 positional args +
     one `rel_tol` keyword, verified against all 39 occurrences in the
     vendored fixture — no `abs_tol` variant observed). A consumer that is
     not tol-aware (does not read the `tol` key) silently falls back to
     EXACT float equality on that row -- honest, documented, never
     defaulted quietly to a wrong comparator without this note.
  2. `set(f(args)) == set(literal)` -> a row with `unordered: True`. The
     verdict-layer semantics this flag names: compare `expected` (a
     `frozenset`) against the candidate's output using Python SET
     equality (order-insensitive AND duplicate-insensitive, i.e. multiple
     copies of one element collapse to one) -- NOT multiset/bag equality.
     This is exactly what MBPP's own `set(...) == set(...)` assert idiom
     encodes, so this module reproduces it rather than inventing a
     stricter or looser comparator.
  3. A raw `set`/`frozenset` literal, anywhere in an arg or as `expected`
     -- PARSED AS A SET VALUE (a real Python `set`/`frozenset` in the
     row), never downgraded to a list (Q0-A's own stated reason for
     excluding these: "downgrading a set to a list would silently
     misrepresent set-equality as list-equality"). `ast.literal_eval`
     already produces genuine `set` objects for `{...}` nodes at any
     nesting depth once the (former) blanket set-rejection guard is
     removed, so no bespoke re-typing is needed here beyond flagging
     `unordered: True` when the TOP-LEVEL `expected` value itself is a
     set/frozenset (a nested set inside an argument is just data passed
     to the candidate -- it does not change the row's own verdict
     comparator, so it is carried through as-is with no flag).
     RESIDUAL, named honestly: a `set`/`frozenset`-valued row is not
     JSON-serializable via `json.dumps` (`domains.prog_synthesis.
     ingest_spec`'s `_add_example_row` calls `json.dumps(inputs,
     sort_keys=True)`), so an end-to-end feed of a set-valued row through
     `ingest_spec` will raise until Q1 lands native DSL Set support ("the
     Q1 engine speaks sets now" per the task brief) or a consumer performs
     its own JSON-safe conversion; Q2's job is honest EXTRACTION, not
     full pipeline wiring -- named in `PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md`.

CONTAMINATION. This module never reads a task's `code` field; `parse_
asserts`/`signature_facts` operate purely on `test_list` (asserts) and
`prompt` (request_facts only touches `prompt`). Measuring signature-fact
CORRECTNESS against the reference function's true parameter count (the
HQ2 bar) is a MEASUREMENT concern, sanctioned by `tests/fixtures/mbpp/
provenance.json`'s contamination_rule ("test-split ... code ... MAY be
read for MEASUREMENT ... they may NEVER enter any codebook entry, cue-
vocabulary token, bigram row, or taught shape") -- that measurement lives
in `tests/test_mbpp_spec_migrated.py`, never in this module.
"""
from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
#  assert -> example-row parsing (ast-based; NEVER eval/exec of task text).
# --------------------------------------------------------------------------- #
_ARG_NAMES = [chr(c) for c in range(ord("a"), ord("z") + 1)]  # a..z, 26 slots
_WRAP_NAMES_UNSUPPORTED = ("sorted", "list", "tuple")  # zero corpus hits, named honestly
_SCAN_WRAP_NAMES = {"set", "sorted", "list", "tuple", "str", "round", "abs",
                    "bool", "int", "float"}


def _is_call(n) -> bool:
    return isinstance(n, ast.Call)


def _literal_args(call: ast.Call) -> Tuple[Optional[List[Any]], Optional[str]]:
    """ast.literal_eval each positional arg of `call`. Returns (args, None)
    on success or (None, reason) naming the first unsupported shape hit —
    starred args, kwargs, or a non-literal argument."""
    if call.keywords:
        return None, "call_has_kwargs"
    args: List[Any] = []
    for a in call.args:
        if isinstance(a, ast.Starred):
            return None, "starred_args"
        try:
            args.append(ast.literal_eval(a))
        except (ValueError, TypeError, SyntaxError):
            return None, "non_literal_args"
    return args, None


def _classify_math_isclose(call: ast.Call) -> Dict[str, Any]:
    """`math.isclose(candidate(args), expected, rel_tol=tol)` -> a FLOAT
    row carrying an explicit tolerance. `math.isclose`'s own default
    `rel_tol` (1e-09) is used when no `rel_tol` keyword is present (never
    observed in this corpus, but the fallback is `math.isclose`'s real
    documented default, not a made-up number)."""
    if len(call.args) < 2:
        return {"ok": False, "reason": "math_isclose_shape"}
    inner, other = call.args[0], call.args[1]
    if not isinstance(inner, ast.Call):
        return {"ok": False, "reason": "math_isclose_lhs_not_call"}
    func = inner.func
    if not isinstance(func, ast.Name):
        return {"ok": False, "reason": "attribute_call"}
    args, bad = _literal_args(inner)
    if bad is not None:
        return {"ok": False, "reason": bad}
    try:
        expected = ast.literal_eval(other)
    except (ValueError, TypeError, SyntaxError):
        return {"ok": False, "reason": "non_literal_expected"}
    tol = 1e-09
    for kw in call.keywords:
        if kw.arg == "rel_tol":
            try:
                tol = float(ast.literal_eval(kw.value))
            except (ValueError, TypeError, SyntaxError):
                return {"ok": False, "reason": "math_isclose_nonliteral_tol"}
    return {"ok": True, "func_name": func.id, "args": args, "expected": expected,
            "tol": tol}


def _classify_set_wrapper(left: ast.Call, right: ast.Call) -> Dict[str, Any]:
    """`set(candidate(args)) == set(literal)` -> an UNORDERED row. LHS
    must wrap exactly one nested Call (the candidate); RHS must wrap
    exactly one literal container (list/tuple/set/frozenset), re-typed as
    a `frozenset` (set-equality semantics, never list-equality)."""
    if len(left.args) != 1 or len(right.args) != 1:
        return {"ok": False, "reason": "set_wrapper_shape"}
    inner = left.args[0]
    if not isinstance(inner, ast.Call):
        return {"ok": False, "reason": "set_wrapper_lhs_not_call"}
    func = inner.func
    if not isinstance(func, ast.Name):
        return {"ok": False, "reason": "attribute_call"}
    args, bad = _literal_args(inner)
    if bad is not None:
        return {"ok": False, "reason": bad}
    try:
        expected_container = ast.literal_eval(right.args[0])
    except (ValueError, TypeError, SyntaxError):
        return {"ok": False, "reason": "non_literal_expected"}
    if not isinstance(expected_container, (list, tuple, set, frozenset)):
        return {"ok": False, "reason": "set_wrapper_rhs_not_container"}
    return {"ok": True, "func_name": func.id, "args": args,
            "expected": frozenset(expected_container), "unordered": True}


def classify_assert(stmt: str) -> Dict[str, Any]:
    """Classify one `test_list` entry. Returns either
    `{"ok": True, "func_name", "args", "expected", ["tol"], ["unordered"]}`
    or `{"ok": False, "reason": "<named unsupported form>"}`. A strict
    superset of `mbpp_zero_shot_baseline.classify_assert`'s supported
    forms (gated equivalence-on-overlap): every form that parser accepts,
    this one accepts identically; this one ALSO accepts the three named
    Q1/Q2-boundary forms (module docstring) that parser named-excludes."""
    try:
        tree = ast.parse(stmt, mode="exec")
    except SyntaxError:
        return {"ok": False, "reason": "syntax_error"}
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assert):
        return {"ok": False, "reason": "not_single_assert_stmt"}
    node = tree.body[0].test

    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) \
                and func.value.id == "math" and func.attr == "isclose":
            return _classify_math_isclose(node)
        return {"ok": False, "reason": "boolean_expression:bare_call"}
    if isinstance(node, ast.BoolOp):
        return {"ok": False, "reason": "boolean_expression:boolop"}
    if isinstance(node, ast.UnaryOp):
        return {"ok": False, "reason": "boolean_expression:unaryop"}
    if not isinstance(node, ast.Compare):
        return {"ok": False, "reason": "other_test_shape:%s" % type(node).__name__}
    if len(node.ops) != 1 or len(node.comparators) != 1:
        return {"ok": False, "reason": "chained_compare"}
    op = node.ops[0]
    left, right = node.left, node.comparators[0]
    if not isinstance(op, ast.Eq):
        return {"ok": False, "reason": "non_eq_compare:%s" % type(op).__name__}

    if _is_call(left) and _is_call(right):
        lf, rf = left.func, right.func
        if isinstance(lf, ast.Name) and isinstance(rf, ast.Name) and lf.id == rf.id:
            if lf.id == "set":
                return _classify_set_wrapper(left, right)
            if lf.id in _WRAP_NAMES_UNSUPPORTED:
                return {"ok": False, "reason": "%s_wrapper" % lf.id}
        return {"ok": False, "reason": "multi_call"}
    if _is_call(left) and not _is_call(right):
        call, other = left, right
    elif _is_call(right) and not _is_call(left):
        call, other = right, left
    else:
        return {"ok": False, "reason": "no_call_in_compare"}

    func = call.func
    if not isinstance(func, ast.Name):
        return {"ok": False, "reason": "attribute_call"}
    args, bad = _literal_args(call)
    if bad is not None:
        return {"ok": False, "reason": bad}
    try:
        expected = ast.literal_eval(other)
    except (ValueError, TypeError, SyntaxError):
        return {"ok": False, "reason": "non_literal_expected"}
    row: Dict[str, Any] = {"ok": True, "func_name": func.id, "args": args,
                           "expected": expected}
    if isinstance(expected, (set, frozenset)):
        row["unordered"] = True
    return row


def _row_from_call(args: List[Any], expected: Any) -> Dict[str, Any]:
    """Positional args -> named inputs, letter-per-position ('a', 'b', ...) —
    byte-identical convention to `mbpp_zero_shot_baseline._row_from_call`
    and the write codebook's own templates (`seeds/code_write_
    constructions.json`: args=["a","b"])."""
    if len(args) > len(_ARG_NAMES):
        names = ["a%d" % i for i in range(len(args))]  # honest overflow, unseen in MBPP
    else:
        names = _ARG_NAMES[:len(args)]
    return {"inputs": dict(zip(names, args)), "expected": expected}


def parse_asserts(task: Dict[str, Any]) -> Dict[str, Any]:
    """Parse every `test_list` entry of `task` (mechanical, ast-based).
    Returns `{"rows": [...], "unparseable": [{"form", "assert_text"}]}` in
    ORIGINAL `test_list` order. A row is `{"inputs", "expected"}` plus
    `"tol"` (float, `math.isclose` rows only) and/or `"unordered"` (True,
    set-comparison rows only) when applicable — see the module docstring
    for the verdict-layer semantics those two fields carry. Never reads
    `task["code"]`."""
    rows: List[Dict[str, Any]] = []
    unparseable: List[Dict[str, Any]] = []
    for stmt in task.get("test_list", []):
        form = classify_assert(stmt)
        if not form["ok"]:
            unparseable.append({"form": form["reason"], "assert_text": stmt})
            continue
        row = _row_from_call(form["args"], form["expected"])
        if "tol" in form:
            row["tol"] = form["tol"]
        if form.get("unordered"):
            row["unordered"] = True
        rows.append(row)
    return {"rows": rows, "unparseable": unparseable}


# --------------------------------------------------------------------------- #
#  the three preregistered split protocols (PROGRAM_SYNTHESIS_ARC2_PREREG.md
#  §0, arc-wide, binding). `rows` is `parse_asserts(task)["rows"]` — the
#  PARSEABLE rows in original test_list order; this function makes no
#  parsing decision, only the reveal/hold-out split named by `protocol`.
# --------------------------------------------------------------------------- #
_PROTOCOLS = ("primary", "official", "stress")


def split_rows(rows: List[Dict[str, Any]], protocol: str) -> Dict[str, Any]:
    """`protocol` in {"primary", "official", "stress"} (prereg §0):

      primary  — reveal every parseable row EXCEPT THE LAST; the last is
                 the one held-out row. Needs >=2 parseable rows to be
                 runnable (arc-wide anchor protocol, every HQ bar anchors
                 here).
      official — reveal ALL parseable rows; held_out = the SAME rows (no
                 genuine hold-out — the published-MBPP-style pass@1
                 analog). Flagged `protocol_distinct: True` so a caller
                 never silently merges this into a PRIMARY aggregate
                 (the arc-1 REPAIR-ORACLE precedent). Needs >=1 parseable
                 row to be runnable.
      stress   — reveal only the FIRST parseable row; hold out the rest
                 (Q0-A's own original rule, kept verbatim as the
                 one-shot generalization probe). Needs >=2 parseable rows
                 to be runnable, same shape as PRIMARY's threshold.

    Returns `{"protocol", "revealed", "held_out", "runnable", [
    "excluded_reason"], ["protocol_distinct"]}`."""
    if protocol not in _PROTOCOLS:
        raise ValueError("unknown protocol %r (must be one of %r)" % (protocol, _PROTOCOLS))
    n = len(rows)
    if protocol == "official":
        if n == 0:
            return {"protocol": protocol, "revealed": [], "held_out": [],
                    "runnable": False, "excluded_reason": "no_parseable_rows",
                    "protocol_distinct": True}
        return {"protocol": protocol, "revealed": list(rows), "held_out": list(rows),
                "runnable": True, "protocol_distinct": True}
    # primary / stress both need >=2 parseable rows to be runnable.
    if n == 0:
        return {"protocol": protocol, "revealed": [], "held_out": [],
                "runnable": False, "excluded_reason": "no_parseable_rows"}
    if n == 1:
        return {"protocol": protocol,
                "revealed": list(rows) if protocol == "stress" else [],
                "held_out": [], "runnable": False,
                "excluded_reason": "insufficient_holdout"}
    if protocol == "primary":
        return {"protocol": protocol, "revealed": rows[:-1], "held_out": rows[-1:],
                "runnable": True}
    return {"protocol": protocol, "revealed": rows[:1], "held_out": rows[1:],
            "runnable": True}  # stress


# --------------------------------------------------------------------------- #
#  signature facts — derived ONLY from parsed example rows, never prose or
#  the reference `code` field.
# --------------------------------------------------------------------------- #
def _iter_calls(node: ast.AST):
    """Pre-order DFS over every `ast.Call` reachable from `node`, in
    source (left-to-right) order — an outer wrapping call (`set(...)`,
    `math.isclose(...)`) is yielded BEFORE the call it wraps."""
    if isinstance(node, ast.Call):
        yield node
    for child in ast.iter_child_nodes(node):
        yield from _iter_calls(child)


def _first_assert_func_name(task: Dict[str, Any]) -> Optional[str]:
    """The candidate function's name, from the FIRST `test_list` entry's
    call — mechanical AST scan, independent of that assert's own
    parseability (a task whose first assert is e.g. a `math.isclose` or
    `set(...)`-wrapped form still yields a name here). Skips known WRAP
    names (`set`/`sorted`/`list`/`tuple`/`str`/`round`/`abs`/`bool`/
    `int`/`float`) and any Attribute-call (`math.isclose` itself) to reach
    the innermost genuine candidate call."""
    tl = task.get("test_list") or []
    if not tl:
        return None
    try:
        tree = ast.parse(tl[0], mode="exec")
    except SyntaxError:
        return None
    for call in _iter_calls(tree):
        func = call.func
        if isinstance(func, ast.Name) and func.id not in _SCAN_WRAP_NAMES:
            return func.id
    return None


def signature_facts(task: Dict[str, Any]) -> Dict[str, Any]:
    """Arg count + per-arg/output types, derived from `parse_asserts`'s
    rows (never from prose or `task["code"]`); function name is the
    FIRST assert's call name (`_first_assert_func_name`, mechanical).
    `complete` is True iff every parsed row agrees on arity (arg count)
    AND that arity is > 0 — the HQ2 "signature facts complete" bar reads
    this field. Type-consistency across rows is reported separately
    (`consistent_types`) since a task MAY legitimately vary an arg's
    concrete literal type row-to-row (e.g. an int vs a float in the same
    numeric slot) without that being an extraction defect — only arity
    agreement is load-bearing for "complete"."""
    parsed = parse_asserts(task)
    rows = parsed["rows"]
    func_name = _first_assert_func_name(task)
    if not rows:
        return {"func_name": func_name, "arg_count": None, "arg_types": None,
                "return_type": None, "consistent_arity": False,
                "consistent_types": False, "complete": False, "n_rows_used": 0}
    arg_names = list(rows[0]["inputs"].keys())
    arg_count = len(arg_names)
    consistent_arity = all(len(r["inputs"]) == arg_count for r in rows)
    arg_types = [type(rows[0]["inputs"][n]).__name__ for n in arg_names]
    return_type = type(rows[0]["expected"]).__name__
    consistent_types = all(
        [type(r["inputs"][n]).__name__ for n in arg_names] == arg_types
        and type(r["expected"]).__name__ == return_type
        for r in rows if len(r["inputs"]) == arg_count)
    complete = bool(consistent_arity and arg_count > 0)
    return {"func_name": func_name, "arg_count": arg_count, "arg_types": arg_types,
            "return_type": return_type, "consistent_arity": consistent_arity,
            "consistent_types": consistent_types, "complete": complete,
            "n_rows_used": len(rows)}


# --------------------------------------------------------------------------- #
#  request facts — mechanical MBPP verb-frame normalization + constraint-
#  word hits. NO decision: which shape a request wants stays ShapeDecode's
#  call (downstream); which cue rule (if any) fires on `constraint_hits`
#  is a later phase's rule, not this function's.
# --------------------------------------------------------------------------- #
# Closed fallback — byte-identical to `seeds/mbpp_request_cues.json`'s
# initial vocabulary (both earned from the 120 TRAIN-split prompts,
# task_id >= 601, per `PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md`'s provenance
# table). Used only when no agent / no `mbpp_verb_frame` Concepts are held
# — a minimal boot without this seed normalizes identically (the `code_
# write_request_cues` parity precedent).
_MBPP_VERB_FRAMES_FALLBACK = (
    "write a python function which",
    "write a python function to",
    "write a function which",
    "write a function that",
    "write function to",
    "write a function to",
)
_MBPP_CONSTRAINT_WORDS_FALLBACK = frozenset({
    "area", "balanced", "binary", "common", "consecutive", "contains",
    "convert", "count", "difference", "digits", "dictionary", "divisible",
    "duplicates", "equal", "even", "index", "largest", "length", "lowercase",
    "matrix", "maximum", "minimum", "natural", "nth", "odd", "pairs",
    "perfect", "power", "prime", "product", "reverse", "rotate", "smallest",
    "sort", "sorted", "square", "sublist", "sublists", "sum", "triangle",
    "tuple", "uppercase", "vowel", "vowels",
})

_WORD_RE = re.compile(r"[a-z']+")


def _mbpp_cue_sets(agent) -> Tuple[List[str], set]:
    """Read `mbpp_verb_frame` / `mbpp_constraint_word` Concept nodes off
    `agent` (`seeds/mbpp_request_cues.json`), the SAME held-Concept
    pattern `code_writing._request_cue_sets` already uses. Falls back to
    the closed sets above when `agent` is None or no such Concepts are
    held — a mechanical graph query, never a decision."""
    if agent is not None:
        try:
            sub = getattr(agent, "s", agent)
            frames: List[str] = []
            words: set = set()
            for n in sub.nodes("Concept"):
                at = sub.node(n)["attrs"]
                role = at.get("code_request_role")
                if role == "mbpp_verb_frame" and at.get("name"):
                    frames.append(str(at["name"]).lower())
                elif role == "mbpp_constraint_word" and at.get("name"):
                    words.add(str(at["name"]).lower())
            if frames and words:
                return frames, words
        except Exception:
            pass
    return list(_MBPP_VERB_FRAMES_FALLBACK), set(_MBPP_CONSTRAINT_WORDS_FALLBACK)


def request_facts(prompt: str, agent=None) -> Dict[str, Any]:
    """Mechanical normalization of an MBPP-style request. Returns
    `{"verb_frame", "request_body", "constraint_hits"}`:

      verb_frame      — the matched frame's tag (its held/fallback text
                        with spaces replaced by underscores), or "other"
                        when no held/fallback frame prefixes `prompt`
                        (case-insensitively).
      request_body    — the ORIGINAL-CASE residual text after the matched
                        frame prefix (a fixed string slice); the whole
                        prompt, unchanged, when no frame matched.
      constraint_hits — sorted list of held/fallback constraint-vocabulary
                        words present in `prompt` as WHOLE tokens (the
                        same `[a-z']+` tokenization `scripts/mbpp_
                        blocker_histogram.py`'s `constraint_hits` uses).

    No decision is made here — a cue RULE (not yet built; Q3+ territory)
    is what would act on `constraint_hits`; this function only produces
    the facts."""
    frames, words = _mbpp_cue_sets(agent)
    low = prompt.lower()
    matched: Optional[str] = None
    body = prompt
    for frame in sorted(frames, key=len, reverse=True):
        if low.startswith(frame):
            matched = frame
            body = prompt[len(frame):].strip()
            break
    verb_frame = matched.replace(" ", "_") if matched else "other"
    tokens = set(_WORD_RE.findall(low))
    hits = sorted(words & tokens)
    return {"verb_frame": verb_frame, "request_body": body, "constraint_hits": hits}
