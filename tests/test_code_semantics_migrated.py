"""CODE-2: SEMANTICS AS TERM-TREES; UNDERSTANDING = EVALUATION.

CODE-1 (domains/code_reading.py) made code a READ register: real repo Python
ingests via `ast_to_term.ingest_ast`, decodes against a code-construction
codebook, and round-trips a NARROW arithmetic-only slice through the
teachable renderer. Its three named residuals are this wave's corridor:

  (1) COMPARE/COND/BOOLOP become Term-evaluable (`domains/ast_to_term.py`'s
      `emit_term` widened to Compare — incl. CHAINED comparisons, folded to
      And — BoolOp, IfExp, and UnaryOp:Not). FIELD (Attribute/Subscript)
      stays a DOCUMENTED residual: the held `Attr` Term reads a SUBSTRATE
      GRAPH NODE's attrs dict by key, a different domain than Python's
      general object.attribute access over an arbitrary argument value --
      mapping it would be an approximation, not a translation, so it is
      deliberately left un-mapped (see `ast_to_term.AstTermEmitter.emit_term`'s
      own EmitError message). Subscript has no general getitem Term either.
  (2) Skeleton granularity deepens beyond the Return root: a straight-line
      assignment body is the SEQUENTIAL-BINDING shape (`sequential_
      computation`, one 'LET' token) emitting nested Let bindings; an
      init/for-loop/accumulate-step/Return body is the FOUR-token
      'ASSIGN,FOR,AUGASSIGN,RETURN' `accumulation_loop` construction
      (construction-GUIDED emission into a native Fold) --
      `domains/code_reading.py::_multi_stmt_skeleton_and_kind`.
  (3) Understanding = PREDICTION (the AbS gate): `code_reading.predict_output`
      ingests, emits, and NATIVELY EVALUATES a real function's Term-tree —
      never execs the real Python. Verified live by a monkeypatch guard.

REAL REPO CORPUS used (grepped from this repository; verbatim function
bodies, see each SOURCE constant below for the exact file:line):
  * scripts/arc_archive/arc3_agent.py:81      grid_eq            (COMPARE)
  * domains/llvm_ir_interp.py:90              _shift_count       (CHAINED COMPARE + IFEXP)
  * domains/insight_naming.py:28              _direction_symbol  (IFEXP)
  * domains/context_model.py:74               _cadence_of        (NESTED IFEXP)
  * scripts/agent_dialogue_intertext.py:35    _sign              (NESTED IFEXP + NEG)
  * domains/name_variant_merge.py:136,141     _is_proper_token / _is_common_token
                                               (BOOLOP + tuple-unpack near-miss)
  * domains/scattering_feature.py:86          _descr_len_1d      (LET-CHAIN)
  * domains/continuous.py:69                  covariance_trace   (ACCUMULATION near-miss
                                               + docstring-divergence)

HONEST RESIDUAL: no in-repo accumulation-shape function is BOTH pure-
arithmetic-emittable AND carries a docstring (every real one either calls an
external function in its init/step, or has no docstring at all) — the
WORKING Fold-emission demonstrations (`sum_of_squares`, `total_weight`) and
the docstring-wording-divergence-on-a-predictable-function demonstration are
therefore SYNTHETIC, clearly labelled as such below, never presented as
"from the repo".

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_code_semantics_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from domains import ast_to_term                            # noqa: E402
from domains import code_reading as cdr                    # noqa: E402


@pytest.fixture()
def agent():
    return WorldAdapter()


def _exec_return(rendered: str, argnames: str) -> "callable":
    """Compile `def f(<argnames>): return <rendered>` and hand back f — the
    SAME round-trip idiom CODE-1's own gate file uses."""
    ns: dict = {}
    exec("def f(%s):\n    return %s\n" % (argnames, rendered), ns)
    return ns["f"]


# =========================================================================== #
#  (1) PURE-EXPRESSION WIDENING — COMPARE (incl. chained) / BOOLOP / COND.
# =========================================================================== #

# scripts/arc_archive/arc3_agent.py:81 — verbatim.
GRID_EQ_SOURCE = '''
def grid_eq(a, b):
    return a == b
'''


@pytest.mark.parametrize("a,b", [(1, 1), (1, 2), ("x", "x")])
def test_compare_real_function_evaluates_and_renders(agent, a, b):
    r = cdr.read_function(agent, GRID_EQ_SOURCE, "grid_eq")
    assert r["construction"] == "comparison_predicate", r
    assert r["emit_error"] is None, r["emit_error"]
    native = agent.inner.evaluate(r["term"], {"a": a, "b": b})
    assert bool(native) == (a == b)
    f = _exec_return(r["rendered_python"], "a, b")
    assert f(a, b) == (a == b)


# domains/llvm_ir_interp.py:90 — verbatim (originally nested inside
# `interpret`; extracted standalone — it closes over nothing but its own
# param `b`, so nesting is irrelevant to its semantics).
SHIFT_COUNT_SOURCE = '''
def _shift_count(b):
    # 0..63 inclusive; otherwise the substrate convention returns 0.
    return b if 0 <= b < 64 else None
'''


@pytest.mark.parametrize("b", [-1, 0, 30, 63, 64, 100])
def test_chained_compare_and_ifexp_real_function(agent, b):
    r = cdr.read_function(agent, SHIFT_COUNT_SOURCE, "_shift_count")
    assert r["construction"] == "conditional_expression", r
    assert r["emit_error"] is None, r["emit_error"]
    ref = b if 0 <= b < 64 else None
    native = agent.inner.evaluate(r["term"], {"b": b})
    assert (native if native is not None else None) == ref
    # NOT asserted here: render -> re-exec. Pre-existing, out-of-CODE-2-scope
    # gap distinct from the string-Lit one above: the graph-resident "Lit"
    # RenderRule's Slot/attr binding does not round-trip a `None`-valued (or
    # boolean-valued) Lit through the render subgraph cleanly (`render()`
    # returns None for a term containing `Lit(None)`, verified directly
    # against `world_adapter.py`'s UNMODIFIED renderer). Native evaluation
    # (asserted above, and via the And/Lte/Lt/IfThenElse heads all
    # exercised) is unaffected -- this is a render-surface gap only.


# domains/insight_naming.py:28 — verbatim.
DIRECTION_SYMBOL_SOURCE = '''
def _direction_symbol(value):
    return "+" if value > 0 else "-"
'''


@pytest.mark.parametrize("value", [1.0, -1.0, 0.0])
def test_ifexp_real_function_native_eval(agent, value):
    r = cdr.read_function(agent, DIRECTION_SYMBOL_SOURCE, "_direction_symbol")
    assert r["construction"] == "conditional_expression", r
    assert r["emit_error"] is None, r["emit_error"]
    ref = "+" if value > 0 else "-"
    native = agent.inner.evaluate(r["term"], {"value": value})
    assert native == ref
    # NOT asserted here: render -> re-exec. Pre-existing, out-of-CODE-2-scope
    # gap: the graph-resident Python "Lit" RenderRule (world_adapter.py's
    # `seed_python_renderer`, unmodified by CODE-2) coerces a Lit's value via
    # Cat's plain `str()`, which does not requote a Python string literal
    # (str("+") == "+", not '"+"') -- valid for CODE-1's numeric corpus,
    # invalid Python source for a STRING Lit. Native evaluation (asserted
    # above) is unaffected; fixing the render rule needs a type-aware quoting
    # primitive the render Term system does not have (a new Rust Term, out of
    # this wave's scope) -- named here rather than silently worked around.


# domains/context_model.py:74 — verbatim.
CADENCE_OF_SOURCE = '''
def _cadence_of(nwords):
    return "short" if nwords <= 4 else "medium" if nwords <= 12 else "long"
'''


@pytest.mark.parametrize("nwords", [1, 4, 5, 12, 13, 100])
def test_nested_ifexp_real_function_native_eval(agent, nwords):
    r = cdr.read_function(agent, CADENCE_OF_SOURCE, "_cadence_of")
    assert r["construction"] == "conditional_expression", r
    assert r["emit_error"] is None, r["emit_error"]
    ref = "short" if nwords <= 4 else "medium" if nwords <= 12 else "long"
    native = agent.inner.evaluate(r["term"], {"nwords": nwords})
    assert native == ref
    # render round-trip not asserted: same string-Lit gap as _direction_symbol.


# scripts/agent_dialogue_intertext.py:35 — verbatim.
SIGN_SOURCE = '''
def _sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)
'''


@pytest.mark.parametrize("x", [5, -5, 0, 0.0001, -0.0001])
def test_nested_ifexp_with_neg_real_function_evaluates_and_renders(agent, x):
    r = cdr.read_function(agent, SIGN_SOURCE, "_sign")
    assert r["construction"] == "conditional_expression", r
    assert r["emit_error"] is None, r["emit_error"]
    ref = 1 if x > 0 else (-1 if x < 0 else 0)
    native = agent.inner.evaluate(r["term"], {"x": x})
    assert native == ref
    f = _exec_return(r["rendered_python"], "x")
    assert f(x) == ref


# =========================================================================== #
#  BOOLOP + the tuple-unpack NEAR-MISS (real function: recognised, honestly
#  abstains on Term emission -- CODE-1's `_is_infinite_cyclic` precedent).
# =========================================================================== #

# domains/name_variant_merge.py:136 — verbatim.
IS_PROPER_TOKEN_SOURCE = '''
def _is_proper_token(t, stats):
    cap, low = stats.get(t, (0, 0))
    return cap >= 1 and cap >= low            # dominantly capitalised => proper
'''


def test_boolop_tuple_unpack_real_function_reads_but_abstains(agent):
    r = cdr.read_function(agent, IS_PROPER_TOKEN_SOURCE, "_is_proper_token")
    # recognised: a straight-line-assignment-then-Return SHAPE (the tuple-
    # unpack target is still an `Assign` statement at the skeleton's
    # granularity -- shape recognition and emission are separate concerns).
    assert r["construction"] == "sequential_computation", r
    assert r["skeleton"] == [["LET"]], r
    assert r["term"] is None, "must never fabricate a Term for a tuple-unpack"
    assert r["emit_error"] and "Name" in r["emit_error"]
    assert "not yet Term-evaluable" in cdr.answer_return(r)


# =========================================================================== #
#  (2a) LET-CHAIN — a straight-line multi-assignment body, deepened skeleton.
# =========================================================================== #

# domains/scattering_feature.py:86 — verbatim.
DESCR_LEN_1D_SOURCE = '''
def _descr_len_1d(J, order2, pool):
    n1 = J
    n2 = (J * (J - 1)) // 2 if order2 else 0
    return (n1 + n2) * pool
'''


@pytest.mark.parametrize("J,order2,pool", [(4, True, 3), (4, False, 3), (7, True, 2)])
def test_let_chain_real_function_evaluates_and_renders(agent, J, order2, pool):
    r = cdr.read_function(agent, DESCR_LEN_1D_SOURCE, "_descr_len_1d")
    assert r["construction"] == "sequential_computation", r
    assert r["skeleton"] == [["LET"]], r
    assert r["emit_error"] is None, r["emit_error"]
    assert r["term"]["type"] == "Let"
    n1 = J
    n2 = (J * (J - 1)) // 2 if order2 else 0
    ref = (n1 + n2) * pool
    native = agent.inner.evaluate(r["term"], {"J": J, "order2": order2, "pool": pool})
    assert abs(float(native) - float(ref)) < 1e-9, (native, ref)
    f = _exec_return(r["rendered_python"], "J, order2, pool")
    assert abs(f(J, order2, pool) - ref) < 1e-9


def test_let_chain_sequential_rebind_shadows_not_mutates(agent):
    """`x = 1; x = x + 1; return x` -- the SAME name reassigned twice is
    honest shadowing via nested Let, never a Python-side mutation."""
    src = "def rebind(a):\n    x = a\n    x = x + 1\n    x = x * 2\n    return x\n"
    r = cdr.read_function(agent, src, "rebind")
    assert r["emit_error"] is None, r["emit_error"]
    for a in (0, 3, -2):
        ref = ((a + 1) * 2)
        native = agent.inner.evaluate(r["term"], {"a": a})
        assert native == ref, (a, native, ref)


# =========================================================================== #
#  (2b) ACCUMULATION — the FOUR-token 'ASSIGN,FOR,AUGASSIGN,RETURN' skeleton.
# =========================================================================== #

# domains/continuous.py:69 — verbatim. A REAL accumulation-shaped function:
# recognised (accumulation_loop, the deepened 4-token skeleton) but honestly
# ABSTAINS on emission (its init `Fraction(0)` is a Call the fixed map
# cannot translate) -- CODE-1's near-miss precedent, at the new skeleton
# depth. ALSO the docstring-technical-prose-diverges-in-wording example
# (its own real repo docstring, unmodified).
COVARIANCE_TRACE_SOURCE = '''
def covariance_trace(dists):
    """The trace of the covariance matrix of an INDEPENDENT random vector -- the
    sum of the component variances (off-diagonal covariances are 0)."""
    total = Fraction(0)
    for d in dists:
        total += _F(variance(d))
    return total
'''


def test_accumulation_near_miss_real_function_reads_but_abstains(agent):
    r = cdr.read_function(agent, COVARIANCE_TRACE_SOURCE, "covariance_trace")
    assert r["skeleton"] == [["ASSIGN"], ["FOR"], ["AUGASSIGN"], ["RETURN"]], r
    assert r["construction"] == "accumulation_loop", r
    assert r["term"] is None, "must never fabricate a Term across an un-translatable Call"
    assert r["emit_error"], r
    assert "not yet Term-evaluable" in cdr.answer_return(r)
    # the docstring-divergence stratum: real technical prose ("trace",
    # "covariance", "matrix", "independent", ...) shares no literal word with
    # the code's own names (dists/d/total) -- an HONEST divergence, exactly
    # CODE-1's sigma_star precedent, now demonstrated on the accumulation
    # construction too.
    assert r["agreement"]["verdict"] == "diverge", r["agreement"]
    why = cdr.answer_why(r)
    assert "diverge" in why


# SYNTHETIC (labelled): no in-repo accumulation-shape function is both
# pure-arithmetic-emittable and docstring-bearing (every real candidate
# either calls an external function or carries no docstring at all --
# `covariance_trace` above is the honest real-repo abstain case). This
# function demonstrates the WORKING Fold path over a `range(n)` iterable,
# with a docstring that is TRUE but diverges from the code's own parameter
# names in WORDING (the requirement CODE-1's sigma_star satisfies for the
# single-expression path; this is CODE-2's accumulation-path twin of it).
SUM_OF_SQUARES_SOURCE = '''
def sum_of_squares(n):
    """Accumulates the second moment of a bounded index run."""
    total = 0
    for i in range(n):
        total += i * i
    return total
'''

# SYNTHETIC: the list-arg (non-range) accumulation form -- the render here
# is a GENUINELY reusable Python function (source is Var(weights), a live
# reference to the function's own parameter), unlike the range(n) case
# below, whose renderer bakes the materialised domain at EMISSION time (see
# the note in the range(n) test).
TOTAL_WEIGHT_SOURCE = '''
def total_weight(weights):
    total = 0
    for w in weights:
        total += w
    return total
'''


@pytest.mark.parametrize("n", [0, 1, 5, 8])
def test_accumulation_range_synthetic_evaluates(agent, n):
    r = cdr.read_function(agent, SUM_OF_SQUARES_SOURCE, "sum_of_squares",
                          range_bind={"n": n})
    assert r["construction"] == "accumulation_loop", r
    assert r["emit_error"] is None, r["emit_error"]
    assert r["term"]["type"] == "Fold"
    ref = sum(i * i for i in range(n))
    native = agent.inner.evaluate(r["term"], {"n": n})
    assert native == ref, (n, native, ref)
    # the docstring diverges from the code's own names in wording.
    assert r["agreement"]["verdict"] == "diverge", r["agreement"]
    # render round-trip: the Fold render bakes the range(n) domain that was
    # MATERIALISED AT EMISSION TIME using this SAME n (range_bind) -- an
    # honest, pre-existing limitation this module inherits from
    # ast_to_term.py's own Sum-fold machinery (concrete-bind only, no Rust
    # `range` Term exists to defer materialisation to call time). The
    # rendered function is therefore only guaranteed correct for THIS n.
    f = _exec_return(r["rendered_python"], "n")
    assert f(n) == ref


@pytest.mark.parametrize("weights", [[1, 2, 3], [], [5], [10, -2, 7, 0]])
def test_accumulation_list_arg_synthetic_evaluates_and_renders_generally(agent, weights):
    r = cdr.read_function(agent, TOTAL_WEIGHT_SOURCE, "total_weight")
    assert r["construction"] == "accumulation_loop", r
    assert r["emit_error"] is None, r["emit_error"]
    ref = sum(weights)
    native = agent.inner.evaluate(r["term"], {"weights": weights})
    assert native == ref, (weights, native, ref)
    # UNLIKE the range(n) case, this render is a genuinely reusable Python
    # function -- `source` is `Var(weights)`, a live reference to the
    # parameter, not a baked domain.
    f = _exec_return(r["rendered_python"], "weights")
    assert f(weights) == ref
    assert f([100]) == 100
    assert f([]) == 0


# --------------------------------------------------------------------------- #
#  A non-matching loop (early break) honestly abstains, and mints a new
#  (distinct, un-recognised-before) skeleton -- the self-growth proof at
#  this construction's depth.
# --------------------------------------------------------------------------- #
EARLY_BREAK_SOURCE = '''
def find_first_negative(nums):
    result = None
    for x in nums:
        if x < 0:
            result = x
            break
    return result
'''


def test_accumulation_non_matching_loop_honestly_abstains(agent):
    r = cdr.read_function(agent, EARLY_BREAK_SOURCE, "find_first_negative")
    assert r["skeleton"] == [["ASSIGN"], ["FOR"], ["IF"], ["RETURN"]], r
    # ShapeDecode does BEST-EFFORT partial covering (3 of 4 tokens overlap
    # `accumulation_loop`'s ASSIGN/FOR/RETURN), so RECOGNITION may label this
    # "accumulation_loop-like" with an honest non-empty residual naming the
    # ONE uncovered part -- that is the decode's own call, not this test's
    # concern. What MUST hold regardless (checked here): the residual is
    # non-empty (the IF is NOT silently absorbed), and TERM EMISSION -- a
    # separate, stricter, STRUCTURAL check independent of the decode's
    # label -- never approximates an early-break loop as a Fold.
    assert r["residual"] and r["residual"][0] == ["IF"], r
    assert r["term"] is None, "an early-break loop body must never be approximated as a Fold"
    assert r["emit_error"], r


# =========================================================================== #
#  NAMED-REFUSAL BOUNDARY — augmented assignment / attribute-subscript store
#  / while / try / with all remain EmitError with a reason string, never
#  silently dropped or approximated.
# =========================================================================== #
AUGASSIGN_OUTSIDE_LOOP_SOURCE = (
    "def add_one(x):\n    y = 0\n    y += x\n    return y\n")
ATTR_STORE_SOURCE = (
    "def bad_attr_store(obj, v):\n    obj.x = v\n    return obj.x\n")
SUBSCRIPT_STORE_SOURCE = (
    "def bad_subscript_store(d, v):\n    d[0] = v\n    return d[0]\n")
WHILE_SOURCE = (
    "def count_up(n):\n    i = 0\n    while i < n:\n        i += 1\n    return i\n")
TRY_SOURCE = (
    "def bad_try(x):\n    total = 0\n    try:\n        total += x\n"
    "    except Exception:\n        pass\n    return total\n")
WITH_SOURCE = (
    "def bad_with(path):\n    total = 0\n    with open(path) as f:\n"
    "        total = 1\n    return total\n")


@pytest.mark.parametrize("source,name", [
    (AUGASSIGN_OUTSIDE_LOOP_SOURCE, "add_one"),
    (ATTR_STORE_SOURCE, "bad_attr_store"),
    (SUBSCRIPT_STORE_SOURCE, "bad_subscript_store"),
    (WHILE_SOURCE, "count_up"),
    (TRY_SOURCE, "bad_try"),
    (WITH_SOURCE, "bad_with"),
])
def test_named_refusal_boundary_never_fabricates(agent, source, name):
    r = cdr.read_function(agent, source, name)
    assert r["term"] is None, (name, r)
    assert r["emit_error"], (name, "must carry a reason string")


# =========================================================================== #
#  (4) UNDERSTANDING = PREDICTION — the AbS gate. `predict_output` answers
#  from the MODEL, never by exec-ing the real Python (monkeypatch-guarded).
# =========================================================================== #
def test_predict_output_matches_real_execution_across_shapes(agent):
    cases = [
        (GRID_EQ_SOURCE, "grid_eq", {"a": 3, "b": 3}, True),
        (GRID_EQ_SOURCE, "grid_eq", {"a": 3, "b": 4}, False),
        (SHIFT_COUNT_SOURCE, "_shift_count", {"b": 40}, 40),
        (SHIFT_COUNT_SOURCE, "_shift_count", {"b": 90}, None),
        (SIGN_SOURCE, "_sign", {"x": -8}, -1),
        (DESCR_LEN_1D_SOURCE, "_descr_len_1d", {"J": 4, "order2": True, "pool": 3}, 30.0),
        (SUM_OF_SQUARES_SOURCE, "sum_of_squares", {"n": 6}, sum(i * i for i in range(6))),
        (TOTAL_WEIGHT_SOURCE, "total_weight", {"weights": [1, 2, 3, 4]}, 10),
    ]
    for source, name, args, expected in cases:
        predicted = cdr.predict_output(agent, source, name, args)
        if isinstance(expected, float):
            assert abs(float(predicted) - expected) < 1e-9, (name, predicted, expected)
        else:
            assert predicted == expected, (name, args, predicted, expected)


def test_predict_output_never_executes_the_real_function(agent, monkeypatch):
    """The monkeypatch guard: patch the REAL repo function (imported from its
    real module) to explode if called, then prove `predict_output` -- fed an
    independent copy of the SAME source text -- still returns the correct
    answer. If `predict_output` executed the real Python anywhere, this
    would raise; it never touches the module at all (it only `ast.parse`s
    the source string handed to it and evaluates the derived Term)."""
    import domains.insight_naming as insight_naming

    def _boom(value):
        raise AssertionError("predict_output executed the REAL Python function")

    monkeypatch.setattr(insight_naming, "_direction_symbol", _boom)
    # sanity: the patch really is live on the real module.
    with pytest.raises(AssertionError):
        insight_naming._direction_symbol(1.0)

    predicted = cdr.predict_output(agent, DIRECTION_SYMBOL_SOURCE,
                                   "_direction_symbol", {"value": 5.0})
    assert predicted == "+"
    predicted2 = cdr.predict_output(agent, DIRECTION_SYMBOL_SOURCE,
                                    "_direction_symbol", {"value": -5.0})
    assert predicted2 == "-"


def test_predict_output_raises_named_error_never_fabricates(agent):
    with pytest.raises(ast_to_term.EmitError):
        cdr.predict_output(agent, COVARIANCE_TRACE_SOURCE, "covariance_trace",
                           {"dists": []})


# =========================================================================== #
#  CODE-1 REGRESSION — the existing gates' skeleton/construction shapes are
#  untouched by this module's additive multi-statement path.
# =========================================================================== #
def test_code1_single_expression_path_unaffected(agent):
    mp3 = '''
def _mp3_gain_to_db(global_gain: int) -> float:
    return 1.5051 * (global_gain - 210)
'''
    r = cdr.read_function(agent, mp3, "_mp3_gain_to_db")
    assert r["construction"] == "arithmetic_expression", r
    assert r["skeleton"] == [["ARITH"]], r
    assert r["emit_error"] is None, r["emit_error"]
