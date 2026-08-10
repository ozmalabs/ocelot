#!/usr/bin/env python3
"""mbpp_blocker_histogram.py — arc 2 Q0-B: the BLOCKER HISTOGRAM over MBPP
that picks Q1's op set and Q2's comprehension scope.

PROGRAM_SYNTHESIS_ARC2_PLAN.md §2-Q0. Deterministic, stdlib-ast-based
MEASUREMENT script — no network, no substrate boot, no agent logic, pure
corpus analysis (the same status as arc 1's `prog_ir_statement_histogram.py`,
whose method this script mirrors at MBPP-task grain instead of repo-function
grain). Every DECISION is a fixed, hand-audited rule over parsed AST /
`emit_prog_ir`'s REAL verdict; nothing is approximated or reimplemented.

CONTAMINATION NOTE (binding, from tests/fixtures/mbpp/provenance.json):
this script reads test-split reference `code` fields for STRUCTURAL FEATURE
COUNTING (ast shape, emit_prog_ir verdict) and test-split `test_list` asserts
for VALUE-TYPE counting. This is MEASUREMENT, not learning: the counts and
task_id lists this script emits never become a codebook entry, cue-vocabulary
token, bigram row, or taught shape anywhere downstream — they pick a SCOPE
(which types/ops Q1 implements; which comprehension forms Q2 targets), which
is a design decision made ONCE by a human/orchestrator reading this report,
not a runtime artifact the synthesis loop consumes. See
PROGRAM_SYNTHESIS_ARC2_PREREG.md's contamination section for the full
argument. The artifact this script writes carries NO verbatim code lines —
only derived feature names, counts, and task_id lists.

Method (per task, all 427 sanitized-MBPP tasks):

  1. PROGRAM-SIDE: resolve the entry function (the top-level def whose name
     is called in test_list — measured unique per task, see §"entry
     resolution" below), run the REAL `domains.prog_ir_emit.emit_prog_ir`
     against it (imported, never reimplemented), record ok/blockers/externs/
     recv_methods VERBATIM, plus an independent ast-walk sub-construct
     feature count over the entry function's own subtree (kwargs, star-args,
     slices-with-step, nested funcs, lambdas, class defs, imports, string
     methods by name, container-literal kinds, comprehension kinds,
     exception use, recursion, loop counts, multi-return).
  2. VALUE-DOMAIN: an independent ast-based assert parser (implemented
     without importing the sibling Q0-A baseline script — same measured
     forms, independent code) classifies each test_list assert's call
     arguments + expected value into a literal type tag (int/float/str/
     list[T]/dict/tuple/set/bool/none/mixed/nonliteral), peeling known
     wrap calls (set/sorted/list/tuple/str/round/...) around either side.
  3. PROMPT-SIDE: request-verb form (a fixed small set of observed prefixes)
     + a counted constraint-vocabulary hit list (no NLP).
  4. THREE GREEDY CUMULATIVE CURVES from the CURRENT-STACK FLOOR (arc 1's
     measured value-domain wall: int + list[int] only; the P1-emitter's
     current ok+predictable set for the op/feature axis):
       (a) value-domain curve — which type additions unlock the most
           ASSERT-TYPEABLE tasks;
       (b) op/feature curve — which Q1 op families (grouped from the REAL
           emit_prog_ir blockers + non-native externs + recv/dotted-method
           names) unlock the most REFERENCE SOLUTIONS (ok AND predictable);
       (c) JOINT curve — a task unlocks only when BOTH axes are covered
           (arc 1's registered lesson: single-axis curves over-predict by
           ~25pp; the joint curve is the honest ceiling line).

Output: results/mbpp_blocker_histogram.json — byte-deterministic (sorted
keys, sorted task-id lists, fixed DATE field): running this script twice
must produce byte-identical JSON (gated in
tests/test_mbpp_histogram_migrated.py).
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import warnings
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains.prog_ir_emit import emit_prog_ir  # noqa: E402 — the REAL emitter

DATE = "2026-07-31"
FIXTURE_DIR = os.path.join(_ROOT, "tests", "fixtures", "mbpp")
OUT_PATH = os.path.join(_ROOT, "results", "mbpp_blocker_histogram.json")

# The arc-1 measured value-domain wall (ARC_SUMMARY §0/§3): ProgEval +
# SynthEnumerate's current REACH is integers and integer lists. This is the
# "current stack's floor" both value-domain-adjacent curves start from.
VALUE_DOMAIN_FLOOR = frozenset({"int", "list[int]"})

# --------------------------------------------------------------------------- #
#  Split assignment (provenance.json's canonical MBPP task_id convention).
# --------------------------------------------------------------------------- #
def task_split(task_id: int) -> str:
    if 1 <= task_id <= 10:
        return "fewshot"
    if 11 <= task_id <= 510:
        return "test"
    if 511 <= task_id <= 600:
        return "val"
    if task_id >= 601:
        return "train"
    return "other"


# --------------------------------------------------------------------------- #
#  Entry-function resolution — the def whose name is called in test_list.
#  Measured unique-match over all 427 tasks (0 mismatches, 12 multi-def
#  tasks all resolve cleanly to exactly one calling name); this is the
#  DETERMINISTIC rule, with an honest fallback for the never-observed case.
# --------------------------------------------------------------------------- #
def called_names(test_list):
    names = set()
    for a in test_list:
        try:
            tree = ast.parse(a)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                names.add(n.func.id)
    return names


def resolve_entry(code: str, test_list):
    """-> (entry_name, tree, defs, error) — error is None on success."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return None, None, [], "code_parse_error: %s" % e
    defs = [n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not defs:
        return None, tree, [], "no_top_level_def"
    called = called_names(test_list)
    for d in defs:
        if d.name in called:
            return d.name, tree, defs, None
    # Fallback (never observed on the fixture, kept honest): last def.
    return defs[-1].name, tree, defs, "no_called_def_match_fallback_last"


# --------------------------------------------------------------------------- #
#  emit_prog_ir wrapping + blocker/extern family grouping (op/feature axis).
# --------------------------------------------------------------------------- #
_STRUCTURAL_FAMILY = {
    "OpExt:BitXor": "bitwise_ops", "OpExt:BitAnd": "bitwise_ops",
    "OpExt:BitOr": "bitwise_ops", "OpExt:LShift": "bitwise_ops",
    "OpExt:RShift": "bitwise_ops",
    "OpExt:FloorDiv": "floordiv_general",
    "SliceSubscript": "slicing",
    "CompTargetComplex": "comprehension_advanced",
    "CompMultiClause": "comprehension_advanced",
    "ComprehensionDict": "comprehension_advanced",
    "ComprehensionSet": "comprehension_advanced",
    "Lambda": "lambda",
    "KwargsCall": "kwargs", "StarArgsCall": "kwargs", "StarArgsParam": "kwargs",
    "InStrStatic": "str_substring_static", "StrArithStatic": "str_substring_static",
    "NestedUnpack": "nested_unpack",
    "TypedExcept": "typed_except",
    "FStringConversion": "fstring_conversion",
    "FStringFormatSpec": "fstring_conversion",
    "DictUnpack": "dict_unpack",
    "DefFn": "nested_def", "Decorator": "nested_def",
    "With": "with_stmt", "Assert": "assert_stmt", "Delete": "delete_stmt",
    "ClassDef": "class_def", "GlobalNonlocal": "global_nonlocal",
    "Yield": "generator_fn", "Await": "async_fn", "Match": "match_stmt",
    "ImportAsName": "import_alias",
}


def structural_family(blocker: str) -> str:
    if blocker in _STRUCTURAL_FAMILY:
        return _STRUCTURAL_FAMILY[blocker]
    if blocker.startswith("OpExt:"):
        return "misc_opext:%s" % blocker.split(":", 1)[1]
    if blocker.startswith("GraphRepr:"):
        return "graph_repr_gap"
    return "misc_structural:%s" % blocker


_KNOWN_MODULES = frozenset({
    "math", "re", "cmath", "itertools", "functools", "operator", "string",
    "heapq", "bisect", "statistics", "fractions", "datetime", "random",
    "collections"})

_CONTAINER_CTOR_BUILTINS = frozenset({"list", "set", "tuple", "dict", "frozenset"})
_MATH_NATIVE_BUILTINS = frozenset({"round", "pow", "ord", "chr", "divmod",
                                    "hex", "oct", "bin"})
_GENERAL_BUILTINS = frozenset({"isinstance", "type", "map", "filter", "all",
                                "any", "next", "enumerate", "zip", "reversed",
                                "iter"})
_COLLECTIONS_BUILTINS = frozenset({"Counter", "defaultdict", "OrderedDict",
                                    "namedtuple"})

_STRING_METHODS = frozenset({
    "join", "replace", "split", "rsplit", "isupper", "islower", "capitalize",
    "strip", "lstrip", "rstrip", "upper", "lower", "startswith", "endswith",
    "find", "rfind", "count", "format", "title", "zfill", "rjust", "ljust",
    "center", "swapcase", "translate", "isalpha", "isdigit", "isalnum",
    "isspace", "encode", "partition", "splitlines"})
_COLLECTION_METHODS = frozenset({
    "append", "add", "sort", "extend", "pop", "remove", "insert", "discard",
    "reverse", "clear", "copy", "index"})
_DICT_METHODS = frozenset({"items", "keys", "values", "get", "setdefault",
                            "update", "fromkeys"})
_REGEX_MATCH_METHODS = frozenset({"group", "start", "end", "span", "groups",
                                   "groupdict"})


def builtin_family(name: str) -> str:
    if name in _CONTAINER_CTOR_BUILTINS:
        return "container_ctor"
    if name in _MATH_NATIVE_BUILTINS:
        return "math_native"
    if name in _GENERAL_BUILTINS:
        return "general_builtins"
    if name in _COLLECTIONS_BUILTINS:
        return "collections_module"
    return "misc_builtin:%s" % name


def method_family(name: str) -> str:
    if name in _STRING_METHODS:
        return "string_methods"
    if name in _COLLECTION_METHODS:
        return "collection_methods"
    if name in _DICT_METHODS:
        return "dict_methods"
    if name in _REGEX_MATCH_METHODS:
        return "regex"
    return "misc_method:%s" % name


def extern_families(extern_names, recv_methods, native_oracles_set):
    """-> sorted set of op/feature families for the PREDICTABILITY gap
    (extern names not already in the current native-oracle set, plus every
    recv-form / accidental dotted-var method name)."""
    fams = set()
    for name in extern_names:
        if name in native_oracles_set:
            continue
        if "." in name:
            prefix, _, method = name.partition(".")
            if prefix in _KNOWN_MODULES:
                if prefix in ("math", "cmath"):
                    fams.add("math_native" if prefix == "math" else "complex_numbers")
                elif prefix == "re":
                    fams.add("regex")
                else:
                    fams.add("stdlib_misc:%s" % prefix)
            else:
                fams.add(method_family(method))
        else:
            fams.add(builtin_family(name))
    for name in recv_methods:
        fams.add(method_family(name))
    return fams


# --------------------------------------------------------------------------- #
#  Sub-construct feature counting — independent ast walk over the entry
#  function's own subtree (the arc-1 registered lesson: model sub-construct
#  features EXPLICITLY, not just statement/expression kind presence).
# --------------------------------------------------------------------------- #
def subconstruct_features(fn_node) -> Counter:
    feats: Counter = Counter()
    fn_name = fn_node.name
    for n in ast.walk(fn_node):
        if isinstance(n, ast.Call):
            if n.keywords:
                feats["kwargs_call"] += 1
            if any(isinstance(a, ast.Starred) for a in n.args):
                feats["star_args_call"] += 1
            if isinstance(n.func, ast.Name) and n.func.id == fn_name and n is not fn_node:
                feats["recursion"] += 1
            if isinstance(n.func, ast.Attribute):
                m = n.func.attr
                if m in _STRING_METHODS:
                    feats["string_method:%s" % m] += 1
                elif m in _COLLECTION_METHODS:
                    feats["collection_method:%s" % m] += 1
                elif m in _DICT_METHODS:
                    feats["dict_method:%s" % m] += 1
        elif isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Slice):
                feats["slice_any"] += 1
                if sl.step is not None:
                    feats["slice_with_step"] += 1
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not fn_node:
            feats["nested_function"] += 1
        elif isinstance(n, ast.Lambda):
            feats["lambda"] += 1
        elif isinstance(n, ast.ClassDef):
            feats["class_def"] += 1
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    feats["import:%s" % alias.name.split(".")[0]] += 1
            else:
                feats["import:%s" % (n.module or "")] += 1
        elif isinstance(n, ast.Dict):
            feats["dict_literal"] += 1
        elif isinstance(n, ast.Set):
            feats["set_literal"] += 1
        elif isinstance(n, ast.Tuple):
            feats["tuple_literal"] += 1
        elif isinstance(n, ast.Constant):
            if n.value is None:
                feats["none_literal"] += 1
            elif isinstance(n.value, bool):
                feats["bool_literal"] += 1
            elif isinstance(n.value, float):
                feats["float_literal"] += 1
        elif isinstance(n, ast.ListComp):
            feats["comprehension:list"] += 1
        elif isinstance(n, ast.SetComp):
            feats["comprehension:set"] += 1
        elif isinstance(n, ast.DictComp):
            feats["comprehension:dict"] += 1
        elif isinstance(n, ast.GeneratorExp):
            feats["comprehension:gen"] += 1
        elif isinstance(n, (ast.Try,)):
            feats["try_except"] += 1
        elif isinstance(n, ast.Raise):
            feats["raise_stmt"] += 1
        elif isinstance(n, ast.While):
            feats["while_loop"] += 1
        elif isinstance(n, ast.For):
            feats["for_loop"] += 1
        elif isinstance(n, ast.Return):
            feats["return_stmt"] += 1
    if feats.get("return_stmt", 0) > 1:
        feats["multiple_returns"] = 1
    return feats


# --------------------------------------------------------------------------- #
#  Value-domain: an INDEPENDENT assert parser (implemented without importing
#  the sibling Q0-A baseline script — same measured forms, own code).
# --------------------------------------------------------------------------- #
_WRAP_FUNCS = frozenset({"set", "frozenset", "sorted", "list", "tuple", "str",
                          "round", "abs", "bool", "int", "float"})
_FULLY_PARSED_FORMS = frozenset({"eq_literal", "float_tolerance"})


def _seq_elem_tag(elts):
    if not elts:
        return "empty"
    tags = set()
    for e in elts:
        t = classify_literal(e)
        tags.add(t if t is not None else "nonliteral")
    if len(tags) == 1:
        return next(iter(tags))
    return "mixed"


def classify_literal(node):
    """AST literal expr -> a type tag string, or None if not a literal this
    classifier understands (Call/Name/BinOp/... -> None)."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)) \
            and isinstance(node.operand, ast.Constant) \
            and isinstance(node.operand.value, (int, float)) \
            and not isinstance(node.operand.value, bool):
        node = node.operand
    if isinstance(node, ast.Constant):
        v = node.value
        if v is None:
            return "none"
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, int):
            return "int"
        if isinstance(v, float):
            return "float"
        if isinstance(v, str):
            return "str"
        return None
    if isinstance(node, ast.List):
        return "list[%s]" % _seq_elem_tag(node.elts)
    if isinstance(node, ast.Tuple):
        return "tuple[%s]" % _seq_elem_tag(node.elts)
    if isinstance(node, ast.Set):
        return "set[%s]" % _seq_elem_tag(node.elts)
    if isinstance(node, ast.Dict):
        return "dict"
    return None


def _peel_wraps(node):
    wraps = []
    cur = node
    while isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name) \
            and cur.func.id in _WRAP_FUNCS and len(cur.args) >= 1:
        wraps.append(cur.func.id)
        cur = cur.args[0]
    return cur, wraps


# A CONTAINER-SHAPING wrap changes the compared value's own bracket kind
# (`set(f(...)) == set((4, 5))`: the RHS is syntactically a Tuple literal,
# but the value actually compared is a set — the SHAPE the outermost wrap
# produces, not the inner literal's own AST kind). `sorted` produces a
# list regardless of its argument's literal kind. Non-shaping wraps
# (round/str/abs/bool/int/float) are left as a recorded fact only (rare in
# this corpus; not worth a speculative re-typing rule).
_CONTAINER_WRAP_SHAPE = {"set": "set", "frozenset": "set",
                          "list": "list", "tuple": "tuple", "sorted": "list"}


def _typed_after_wraps(node):
    """Peel wraps, classify the innermost literal, then re-tag the RESULT
    by the OUTERMOST container-shaping wrap (if any) — the value actually
    produced by the wrap chain, not the bare innermost AST node's kind."""
    innermost, wraps = _peel_wraps(node)
    inner_tag = classify_literal(innermost)
    for w in wraps:  # outside-in order (wraps[0] is outermost / final shape)
        if w in _CONTAINER_WRAP_SHAPE:
            elem = inner_tag
            if elem is None:
                elem = "nonliteral"
            elif "[" in elem:
                elem = elem[elem.index("[") + 1:-1]
            return "%s[%s]" % (_CONTAINER_WRAP_SHAPE[w], elem), wraps
    return inner_tag, wraps


def _find_target_call(node, entry_name):
    """Peel wraps looking for a Call to entry_name. -> (call_node, wraps) or
    (None, wraps_seen_before_giving_up)."""
    wraps = []
    cur = node
    while isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name):
        if cur.func.id == entry_name:
            return cur, wraps
        if cur.func.id in _WRAP_FUNCS and len(cur.args) >= 1:
            wraps.append(cur.func.id)
            cur = cur.args[0]
            continue
        return None, wraps
    return None, wraps


def parse_one_assert(assert_src: str, entry_name: str):
    """-> dict describing one assert's parsed shape. Always returns a dict
    (never raises) — an unparseable form is an honest datum, not an error."""
    try:
        tree = ast.parse(assert_src)
        node = tree.body[0]
    except (SyntaxError, IndexError):
        return {"form": "syntax_error"}
    if not isinstance(node, ast.Assert):
        return {"form": "not_assert"}
    test = node.test

    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
        left, right = test.left, test.comparators[0]
        call, wraps = _find_target_call(left, entry_name)
        other, target_side = right, "left"
        if call is None:
            call, wraps = _find_target_call(right, entry_name)
            other, target_side = left, "right"
        if call is None:
            return {"form": "target_not_found"}
        arg_tags = [classify_literal(a) for a in call.args]
        if any(isinstance(a, (ast.Starred,)) for a in call.args) or call.keywords:
            return {"form": "call_nonliteral_shape", "wraps": sorted(set(wraps))}
        if any(t is None for t in arg_tags):
            return {"form": "arg_nonliteral", "wraps": sorted(set(wraps))}
        ret_tag, other_wraps = _typed_after_wraps(other)
        if ret_tag is None:
            return {"form": "expected_nonliteral", "arg_types": arg_tags,
                    "wraps": sorted(set(wraps) | set(other_wraps))}
        return {"form": "eq_literal", "arg_types": arg_tags, "return_type": ret_tag,
                "wraps": sorted(set(wraps) | set(other_wraps)), "target_side": target_side}

    if isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute) \
            and test.func.attr == "isclose":
        # `math.isclose(candidate(...), expected, rel_tol=...)` — the MBPP
        # float-tolerance verdict idiom (measured: every non-Name-func Call
        # test in the corpus is exactly this form, 13 tasks / 39 asserts,
        # all `math.isclose`). A DISTINCT, well-defined form — not garbage —
        # because ProgEval floats need a tolerance comparator, not exact Eq.
        args = test.args
        bad_kw = [kw for kw in test.keywords if kw.arg not in ("rel_tol", "abs_tol")]
        if len(args) < 2 or bad_kw:
            return {"form": "float_tolerance_unusual_shape"}
        call, wraps = _find_target_call(args[0], entry_name)
        other = args[1]
        if call is None:
            call, wraps = _find_target_call(args[1], entry_name)
            other = args[0]
        if call is None:
            return {"form": "target_not_found"}
        if call.keywords or any(isinstance(a, ast.Starred) for a in call.args):
            return {"form": "call_nonliteral_shape", "wraps": sorted(set(wraps))}
        arg_tags = [classify_literal(a) for a in call.args]
        if any(t is None for t in arg_tags):
            return {"form": "arg_nonliteral", "wraps": sorted(set(wraps))}
        ret_tag, other_wraps = _typed_after_wraps(other)
        if ret_tag is None:
            return {"form": "expected_nonliteral", "arg_types": arg_tags,
                    "wraps": sorted(set(wraps) | set(other_wraps))}
        return {"form": "float_tolerance", "arg_types": arg_tags, "return_type": "float",
                "wraps": sorted(set(wraps) | set(other_wraps)), "target_side": "isclose"}

    if isinstance(test, ast.Call) and isinstance(test.func, ast.Name):
        call, wraps = _find_target_call(test, entry_name)
        if call is None:
            return {"form": "target_not_found"}
        if call.keywords or any(isinstance(a, ast.Starred) for a in call.args):
            return {"form": "call_nonliteral_shape", "wraps": sorted(set(wraps))}
        arg_tags = [classify_literal(a) for a in call.args]
        if any(t is None for t in arg_tags):
            return {"form": "arg_nonliteral", "wraps": sorted(set(wraps))}
        return {"form": "eq_literal", "arg_types": arg_tags, "return_type": "bool",
                "wraps": sorted(set(wraps)), "target_side": "bare_truthy"}

    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        call, wraps = _find_target_call(test.operand, entry_name)
        if call is None:
            return {"form": "target_not_found"}
        if call.keywords or any(isinstance(a, ast.Starred) for a in call.args):
            return {"form": "call_nonliteral_shape", "wraps": sorted(set(wraps))}
        arg_tags = [classify_literal(a) for a in call.args]
        if any(t is None for t in arg_tags):
            return {"form": "arg_nonliteral", "wraps": sorted(set(wraps))}
        return {"form": "eq_literal", "arg_types": arg_tags, "return_type": "bool",
                "wraps": sorted(set(wraps)), "target_side": "bare_falsy"}

    return {"form": "other_unparseable:%s" % type(test).__name__}


# --------------------------------------------------------------------------- #
#  Prompt-side features.
# --------------------------------------------------------------------------- #
_REQUEST_FORMS = [
    ("write_a_python_function_to", re.compile(r"^\s*write a python function to\b", re.I)),
    ("write_a_function_to", re.compile(r"^\s*write a function to\b", re.I)),
    ("write_a_function_that", re.compile(r"^\s*write a function that\b", re.I)),
    ("write_a_function_which", re.compile(r"^\s*write a function which\b", re.I)),
]

CONSTRAINT_VOCAB = sorted({
    "sorted", "unique", "prime", "palindrome", "balanced", "maximum", "minimum",
    "largest", "smallest", "odd", "even", "sum", "count", "difference",
    "product", "reverse", "common", "positive", "negative", "square", "power",
    "binary", "digits", "contains", "equal", "sort", "area", "pairs",
    "natural", "nth", "index", "duplicate", "duplicates", "consecutive",
    "rotate", "matrix", "factorial", "armstrong", "perfect", "triangle",
    "substring", "vowel", "vowels", "uppercase", "lowercase", "camel",
    "snake", "frequency", "divisible", "kth", "sublist", "sublists",
    "length", "tuple", "dictionary", "convert"})


def request_form(prompt: str) -> str:
    for tag, rx in _REQUEST_FORMS:
        if rx.match(prompt):
            return tag
    return "other"


def constraint_hits(prompt: str):
    words = set(re.findall(r"[a-z']+", prompt.lower()))
    return sorted(words & set(CONSTRAINT_VOCAB))


# --------------------------------------------------------------------------- #
#  Generic greedy cumulative-coverage curve (the P0 precedent, at task
#  grain): a task unlocks only when its ENTIRE remaining requirement set is
#  covered by chosen candidates; ties break alphabetically for determinism.
# --------------------------------------------------------------------------- #
def greedy_curve(task_requirements: dict, floor_unlocked: set, total_denominator: int):
    remaining = {tid: set(reqs) for tid, reqs in task_requirements.items() if reqs}
    unlocked = set(floor_unlocked) | {tid for tid, reqs in task_requirements.items() if not reqs}
    steps = [{
        "step": 0, "added": None,
        "newly_unlocked_count": len(unlocked),
        "newly_unlocked_ids": sorted(unlocked),
        "cumulative_unlocked": len(unlocked),
        "cumulative_pct": round(100.0 * len(unlocked) / total_denominator, 2),
    }]
    step = 0
    while remaining:
        pool = set()
        for reqs in remaining.values():
            pool |= reqs
        if not pool:
            break
        best_cand, best_gain, best_newly = None, -1, []
        for cand in sorted(pool):
            newly = [tid for tid, reqs in remaining.items() if reqs <= {cand}]
            gain = len(newly)
            if gain > best_gain:
                best_cand, best_gain, best_newly = cand, gain, newly
        step += 1
        for reqs in remaining.values():
            reqs.discard(best_cand)
        for tid in best_newly:
            del remaining[tid]
        unlocked |= set(best_newly)
        steps.append({
            "step": step, "added": best_cand,
            "newly_unlocked_count": len(best_newly),
            "newly_unlocked_ids": sorted(best_newly),
            "cumulative_unlocked": len(unlocked),
            "cumulative_pct": round(100.0 * len(unlocked) / total_denominator, 2),
        })
    return steps


def curve_mark(steps, pct):
    """First step whose cumulative_pct >= pct (the earliest cumulative
    variant set reaching the mark), or the final step if never reached."""
    for s in steps:
        if s["cumulative_pct"] >= pct:
            return s
    return steps[-1]


# --------------------------------------------------------------------------- #
#  Top-N helper — feature counters -> {feature: count} + {feature: task_ids}
#  for the top 20 by count (name tiebreak), never verbatim code.
# --------------------------------------------------------------------------- #
def top_n_with_ids(feature_to_tasks: dict, n=20):
    ordered = sorted(feature_to_tasks.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:n]
    return {
        "counts": {k: len(v) for k, v in ordered},
        "task_ids": {k: sorted(v) for k, v in ordered},
    }


# --------------------------------------------------------------------------- #
#  Main measurement pass.
# --------------------------------------------------------------------------- #
def measure(tasks_override=None):
    """tasks_override lets a caller (the determinism gate) run the exact
    same measurement over a SLICE of tasks without touching the on-disk
    fixture — the per-task computation is identical either way."""
    if tasks_override is not None:
        tasks = tasks_override
    else:
        with open(os.path.join(FIXTURE_DIR, "sanitized-mbpp.json")) as f:
            tasks = json.load(f)
    with open(os.path.join(FIXTURE_DIR, "provenance.json")) as f:
        provenance = json.load(f)

    per_task = []
    split_counts = Counter()

    blocker_to_tasks = Counter()
    blocker_task_ids: dict = {}
    structural_family_to_tasks: dict = {}
    extern_family_to_tasks: dict = {}
    subfeat_to_tasks: dict = {}
    type_tag_to_tasks: dict = {}
    return_type_to_tasks: dict = {}
    assert_form_to_tasks: dict = {}
    request_form_to_tasks: dict = {}
    constraint_to_tasks: dict = {}

    ok_count = 0
    predictable_count = 0

    value_domain_reqs = {}     # task_id -> set(type tags) needed beyond floor
    type_coverable_ids = set()
    non_type_coverable_ids = set()

    op_feature_reqs = {}       # task_id -> set(op/feature families) needed
    op_feature_unlocked = set()

    for t in tasks:
        tid = t["task_id"]
        split = task_split(tid)
        split_counts[split] += 1
        code = t["code"]
        test_list = t["test_list"]
        prompt = t["prompt"]

        entry_name, tree, defs, resolve_err = resolve_entry(code, test_list)

        row = {"task_id": tid, "split": split, "source_file": t["source_file"],
               "n_asserts": len(test_list)}

        # ---- program-side: emit_prog_ir (REAL) ----
        emit_err = None
        emit_res = None
        if entry_name is not None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    emit_res = emit_prog_ir(code, name=entry_name)
            except Exception as e:  # noqa: BLE001 — honest non-count, recorded
                emit_err = "%s: %s" % (type(e).__name__, str(e)[:160])
        row["entry_resolve_error"] = resolve_err
        row["entry_function"] = entry_name
        row["emit_error"] = emit_err

        req_families = set()
        if emit_res is None:
            row["ok"] = False
            row["predictable"] = False
            row["blockers"] = ["EMIT_FAILED"] if emit_err or resolve_err else []
            row["structural_families"] = sorted({structural_family(b) for b in row["blockers"]})
            row["extern_families"] = []
        elif emit_res["ok"]:
            ok_count += 1
            row["ok"] = True
            row["blockers"] = []
            row["structural_families"] = []
            predictable = emit_res["predictable"]
            row["predictable"] = predictable
            row["externs"] = emit_res["externs"]
            row["recv_methods"] = emit_res["recv_methods"]
            native_set = set(emit_res["native_oracles"]) | (
                set(emit_res["externs"]) & set(emit_res["native_oracles"]))
            # NATIVE_ORACLES itself (fixed P1 set) — recompute from prog_ir_emit.
            from domains.prog_ir_emit import NATIVE_ORACLES
            fams = extern_families(emit_res["externs"], emit_res["recv_methods"],
                                    NATIVE_ORACLES)
            row["extern_families"] = sorted(fams)
            req_families = fams
            if predictable:
                predictable_count += 1
                op_feature_unlocked.add(tid)
        else:
            row["ok"] = False
            row["predictable"] = False
            row["blockers"] = emit_res["blockers"]
            fams = {structural_family(b) for b in emit_res["blockers"]}
            row["structural_families"] = sorted(fams)
            row["extern_families"] = []
            req_families = fams

        for b in row["blockers"]:
            blocker_to_tasks[b] += 1
            blocker_task_ids.setdefault(b, set()).add(tid)
        for fam in row["structural_families"]:
            structural_family_to_tasks.setdefault(fam, set()).add(tid)
        for fam in row.get("extern_families", []):
            extern_family_to_tasks.setdefault(fam, set()).add(tid)

        op_feature_reqs[tid] = req_families

        # ---- program-side: sub-construct features (independent ast walk) ----
        subfeats = {}
        if entry_name is not None:
            fn_node = next((d for d in defs if d.name == entry_name), None)
            if fn_node is not None:
                subfeats = dict(subconstruct_features(fn_node))
        row["subconstruct_features"] = subfeats
        for feat in subfeats:
            subfeat_to_tasks.setdefault(feat, set()).add(tid)

        # ---- value-domain: assert parsing (independent) ----
        assert_rows = []
        arg_type_union = set()
        return_type_union = set()
        n_fully_parsed = 0
        wrap_union = set()
        for a in test_list:
            pr = parse_one_assert(a, entry_name if entry_name else "__none__")
            assert_rows.append(pr)
            assert_form_to_tasks.setdefault(pr["form"], set()).add(tid)
            if pr["form"] in _FULLY_PARSED_FORMS:
                n_fully_parsed += 1
                arg_type_union.update(pr["arg_types"])
                return_type_union.add(pr["return_type"])
                wrap_union.update(pr.get("wraps", []))
        row["assert_forms"] = [pr["form"] for pr in assert_rows]
        row["arg_types"] = sorted(arg_type_union)
        row["return_types"] = sorted(return_type_union)
        row["n_asserts_fully_parsed"] = n_fully_parsed
        row["assert_wraps"] = sorted(wrap_union)

        for tg in arg_type_union:
            type_tag_to_tasks.setdefault(tg, set()).add(tid)
        for tg in return_type_union:
            return_type_to_tasks.setdefault(tg, set()).add(tid)

        if n_fully_parsed > 0:
            type_coverable_ids.add(tid)
            all_types = arg_type_union | return_type_union
            value_domain_reqs[tid] = set(all_types) - VALUE_DOMAIN_FLOOR
        else:
            non_type_coverable_ids.add(tid)

        # ---- prompt-side ----
        rf = request_form(prompt)
        row["request_form"] = rf
        request_form_to_tasks.setdefault(rf, set()).add(tid)
        hits = constraint_hits(prompt)
        row["constraint_hits"] = hits
        for w in hits:
            constraint_to_tasks.setdefault(w, set()).add(tid)

        per_task.append(row)

    per_task.sort(key=lambda r: r["task_id"])
    all_ids = [r["task_id"] for r in per_task]
    total = len(all_ids)

    # ---- curves ----
    vd_floor_unlocked = {tid for tid in type_coverable_ids if not value_domain_reqs.get(tid)}
    vd_denominator = len(type_coverable_ids)
    value_domain_steps = greedy_curve(
        {tid: value_domain_reqs[tid] for tid in type_coverable_ids},
        vd_floor_unlocked, vd_denominator) if vd_denominator else []

    op_denominator = total
    op_feature_steps = greedy_curve(op_feature_reqs, op_feature_unlocked, op_denominator)

    # Joint: only over type-coverable tasks (the honest ceiling denominator —
    # a task that can never be typed can never be jointly unlocked either).
    joint_reqs = {}
    for tid in type_coverable_ids:
        joint_reqs[tid] = set(value_domain_reqs.get(tid, set())) | set(op_feature_reqs.get(tid, set()))
    joint_floor_unlocked = {tid for tid in type_coverable_ids if not joint_reqs.get(tid)}
    joint_denominator = len(type_coverable_ids)
    joint_steps = greedy_curve(joint_reqs, joint_floor_unlocked, joint_denominator) if joint_denominator else []

    # Q1-SCOPED joint curve (derived view, drives the prereg's Q1 op-set
    # recommendation): the plan explicitly excludes regex/new-object-model
    # work (§1 "out of scope" + risk #5 "no regex"); families this script
    # only discovered as a same-corpus helper-function extern
    # (`misc_builtin:<other_mbpp_fn_name>`) are a declared-oracle/multi-
    # function concern, not a Q1 value-domain op. A task needing an
    # OUT-OF-SCOPE family can never unlock under this view (excluded from
    # its own denominator, honestly), so the scoped curve is the REACHABLE
    # ceiling for Q1+the value-domain floor, not the unrestricted one above.
    def _out_of_scope(fam: str) -> bool:
        if fam in ("regex", "complex_numbers", "collections_module", "graph_repr_gap"):
            return True
        return fam.split(":", 1)[0] in ("stdlib_misc", "misc_builtin", "misc_method",
                                         "misc_structural", "misc_opext")

    scoped_reqs = {}
    scoped_excluded = set()
    for tid in type_coverable_ids:
        reqs = joint_reqs.get(tid, set())
        if any(_out_of_scope(f) for f in reqs):
            scoped_excluded.add(tid)
            continue
        scoped_reqs[tid] = reqs
    scoped_floor_unlocked = {tid for tid, reqs in scoped_reqs.items() if not reqs}
    scoped_denominator = len(scoped_reqs)
    scoped_steps = greedy_curve(scoped_reqs, scoped_floor_unlocked, scoped_denominator) if scoped_denominator else []

    result = {
        "meta": {
            "date": DATE,
            "script": "scripts/mbpp_blocker_histogram.py",
            "n_tasks": total,
            "split_counts": dict(sorted(split_counts.items())),
            "value_domain_floor": sorted(VALUE_DOMAIN_FLOOR),
            "contamination_note": (
                "test-split code/test_list read for structural feature "
                "counting and emit_prog_ir verdicts only; no codebook, cue "
                "vocabulary, bigram table, or taught shape is written by "
                "this script; see PROGRAM_SYNTHESIS_ARC2_PREREG.md"),
            "provenance": provenance,
        },
        "program_side": {
            "ok_count": ok_count,
            "predictable_count": predictable_count,
            "blocked_count": total - ok_count,
            "blocker_counts": dict(sorted(blocker_to_tasks.items())),
            "blocker_top20": top_n_with_ids(blocker_task_ids, 20),
            "structural_family_top20": top_n_with_ids(structural_family_to_tasks, 20),
            "extern_family_top20": top_n_with_ids(extern_family_to_tasks, 20),
            "subconstruct_feature_top20": top_n_with_ids(subfeat_to_tasks, 20),
        },
        "value_domain": {
            "type_coverable_count": len(type_coverable_ids),
            "non_type_coverable_count": len(non_type_coverable_ids),
            "non_type_coverable_ids": sorted(non_type_coverable_ids),
            "arg_type_top20": top_n_with_ids(type_tag_to_tasks, 20),
            "return_type_top20": top_n_with_ids(return_type_to_tasks, 20),
            "assert_form_counts": {k: len(v) for k, v in sorted(assert_form_to_tasks.items())},
            "assert_form_task_ids": {k: sorted(v) for k, v in sorted(assert_form_to_tasks.items())},
        },
        "prompt_side": {
            "request_form_top": top_n_with_ids(request_form_to_tasks, 20),
            "constraint_vocab_top20": top_n_with_ids(constraint_to_tasks, 20),
        },
        "curves": {
            "value_domain_curve": {
                "denominator": vd_denominator,
                "denominator_note": ("type-coverable tasks only (>=1 fully "
                                      "parsed assert); non-type-coverable "
                                      "tasks are an assert-comprehension gap, "
                                      "Q2 scope, not a value-domain gap"),
                "floor": sorted(VALUE_DOMAIN_FLOOR),
                "steps": value_domain_steps,
            },
            "op_feature_curve": {
                "denominator": op_denominator,
                "denominator_note": "all 427 tasks (representability/predictability is code-side, independent of assert parseability)",
                "steps": op_feature_steps,
            },
            "joint_curve": {
                "denominator": joint_denominator,
                "denominator_note": ("type-coverable tasks only, AND op/feature "
                                      "covered — the honest ceiling per the "
                                      "arc-1 single-axis-over-predicts lesson"),
                "steps": joint_steps,
            },
            "joint_curve_q1_scoped": {
                "denominator": scoped_denominator,
                "denominator_note": ("type-coverable tasks EXCLUDING any task "
                                      "that needs an out-of-plan-scope family "
                                      "(regex, complex_numbers, "
                                      "collections_module, a same-corpus "
                                      "helper-function extern, or any other "
                                      "un-named misc:* tail family) — the "
                                      "REACHABLE ceiling for the Q1 op set "
                                      "this prereg recommends, not the "
                                      "unrestricted joint_curve above"),
                "excluded_out_of_scope_count": len(scoped_excluded),
                "excluded_out_of_scope_ids": sorted(scoped_excluded),
                "steps": scoped_steps,
            },
        },
        "per_task": per_task,
    }
    return result


def main():
    result = measure()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print("wrote %s (%d tasks)" % (OUT_PATH, result["meta"]["n_tasks"]))


if __name__ == "__main__":
    main()
