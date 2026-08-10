"""CODE-3: WRITING IS READING REVERSED (domains/code_writing.py).

Discriminative gates for the write half of the user's directive ("write
arbitrary code with full understanding and comments"):

  * FUNCTION-GRAIN RENDERING — a real, commented, runnable `def` (not just
    an expression fragment) for every emittable shape CODE-1/2 read:
    arithmetic / comparison / conditional / let-chain / accumulation.
    Re-exec'd, the written function reproduces the ORIGINAL function's
    outputs.
  * LITERAL-QUOTING FAITHFULNESS — the rung-4 `LitRepr` Rust primitive
    (runners/dsl/src/term.rs): a string/bool/None Lit now renders as valid,
    faithful Python source at function grain (the CODE-1/2 named residual).
  * COMMENTS FROM STRUCTURE — the docstring is the SAME `what_does` text
    CODE-1's reading side produces, now flowing outward; inline comments
    (a Fold's accumulator role, an IfThenElse guard's condition) are read
    off the Term's own fields, never freehand text.
  * THE ROUND-TRIP LAW — write(read(f)), then READ THE WRITTEN FUNCTION
    BACK: the SAME construction, a canonically-EQUAL Term, and the
    re-reader's OWN docstring-agreement stratum = AGREE (self-consistency:
    the written comment came from the structure, so the reader must find
    it consistent with itself).
  * WRITE FROM AN NL REQUEST, end-to-end through `converse()` — "Write a
    function that returns the larger of two numbers." produces a reply
    carrying a commented, runnable function; `predict_output`-style native
    evaluation confirms it against sample inputs. A request outside the
    held vocabulary abstains honestly, never fabricated.
  * NO REGRESSION — CODE-1/CODE-2's own gates and the pre-existing
    graph-resident renderer are untouched by this module's additive use.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_code_writing_migrated.py -p no:randomly -q
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
from substrate.jsonio import term_from_json                # noqa: E402
from domains import code_reading as cdr                    # noqa: E402
from domains import code_writing as cw                     # noqa: E402


@pytest.fixture()
def agent():
    return WorldAdapter()


# --------------------------------------------------------------------------- #
#  REAL / near-real REPO CORPUS — the SAME functions CODE-1/CODE-2's own
#  gates use (verbatim sources, see those files for provenance).
# --------------------------------------------------------------------------- #
MP3_SOURCE = '''
def _mp3_gain_to_db(global_gain: int) -> float:
    return 1.5051 * (global_gain - 210)
'''
_mp3_ref = lambda g: 1.5051 * (g - 210)  # noqa: E731

CYCLIC_SOURCE = '''
def _is_infinite_cyclic(n: int) -> bool:
    return n == 0
'''

RECT_AREA_SOURCE = '''
def rect_area(width, height):
    """A rectangle's area includes width and height."""
    return width * height
'''

DESCR_LEN_1D_SOURCE = '''
def _descr_len_1d(J, order2, pool):
    n1 = J
    n2 = (J * (J - 1)) // 2 if order2 else 0
    return (n1 + n2) * pool
'''
_descr_len_ref = lambda J, order2, pool: (J + ((J * (J - 1)) // 2 if order2 else 0)) * pool  # noqa: E731

TOTAL_WEIGHT_SOURCE = '''
def total_weight(weights):
    total = 0
    for w in weights:
        total += w
    return total
'''

SUM_OF_SQUARES_SOURCE = '''
def sum_of_squares(n):
    total = 0
    for i in range(n):
        total += i * i
    return total
'''

SIGN_SOURCE = '''
def _sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)
'''


def _exec_and_call(source: str, func_name: str, *args):
    ns: dict = {}
    exec(source, ns)
    return ns[func_name](*args)


# =========================================================================== #
#  (1) FUNCTION-GRAIN RENDERING — a real `def`, re-exec == original.
# =========================================================================== #
def test_write_function_arithmetic_is_a_real_def_reexec_matches(agent):
    written = cw.write_read_function(agent, MP3_SOURCE, "_mp3_gain_to_db")
    assert written["ok"], written
    src = written["source"]
    assert src.startswith("def _mp3_gain_to_db(global_gain):")
    assert '"""' in src and "return " in src
    for g in (0, 100, 210, 255):
        assert abs(_exec_and_call(src, "_mp3_gain_to_db", g) - _mp3_ref(g)) < 1e-6


def test_write_function_comparison_is_a_real_def_reexec_matches(agent):
    written = cw.write_read_function(agent, CYCLIC_SOURCE, "_is_infinite_cyclic")
    assert written["ok"], written
    src = written["source"]
    for n, expected in ((0, True), (1, False), (-3, False)):
        assert _exec_and_call(src, "_is_infinite_cyclic", n) == expected


def test_write_function_conditional_guard_comment_and_reexec(agent):
    written = cw.write_read_function(agent, SIGN_SOURCE, "_sign")
    assert written["ok"], written
    src = written["source"]
    # inline comment reads the IfThenElse's OWN cond/then/other, never
    # freehand text.
    assert "# returns" in src and "when" in src and "else" in src
    for x, expected in ((5, 1), (-5, -1), (0, 0)):
        assert _exec_and_call(src, "_sign", x) == expected


def test_write_function_let_chain_statements_and_reexec(agent):
    written = cw.write_read_function(agent, DESCR_LEN_1D_SOURCE, "_descr_len_1d")
    assert written["ok"], written
    src = written["source"]
    # a real multi-line body -- assignment statements, not a walrus fold.
    assert "n1 = " in src and "n2 = " in src and "return " in src
    assert ":=" not in src, "function-grain body must be honest statements"
    for J, order2, pool in ((4, True, 3), (4, False, 3), (7, True, 2)):
        got = _exec_and_call(src, "_descr_len_1d", J, order2, pool)
        assert abs(got - _descr_len_ref(J, order2, pool)) < 1e-9


def test_write_function_accumulation_list_arg_comment_and_reexec(agent):
    written = cw.write_read_function(agent, TOTAL_WEIGHT_SOURCE, "total_weight")
    assert written["ok"], written
    src = written["source"]
    assert "for w in weights:" in src
    assert "accumulates the running value over w" in src  # accumulator-role comment
    for weights in ([1, 2, 3], [], [5], [10, -2, 7, 0]):
        assert _exec_and_call(src, "total_weight", list(weights)) == sum(weights)


def test_write_function_accumulation_range_bakes_range_and_reexec(agent):
    written = cw.write_read_function(agent, SUM_OF_SQUARES_SOURCE, "sum_of_squares",
                                     range_bind={"n": 6})
    assert written["ok"], written
    src = written["source"]
    assert "range(6)" in src, "a materialised Vec-of-consecutive-ints domain " \
                             "renders back as range(...), not a list literal"
    # n stays the (now-unused) formal parameter -- the domain was baked at
    # emission time with THIS n, the same honest CODE-2 limitation
    # (ast_to_term.py has no deferred-materialisation range Term).
    assert _exec_and_call(src, "sum_of_squares", 6) == sum(i * i for i in range(6))


# =========================================================================== #
#  (2) LITERAL-QUOTING FAITHFULNESS — the rung-4 LitRepr primitive.
# =========================================================================== #
@pytest.mark.parametrize("value", [True, False, None, "hello", "it's",
                                   'has "both\' quotes', "line\nbreak", 3, 3.5, 1.0])
def test_lit_repr_round_trips_every_scalar_kind(agent, value):
    agent.seed_python_renderer()
    term = term_from_json({"type": "Lit", "value": value})
    rendered = agent.render(term, "python")
    assert rendered is not None, value
    ns: dict = {}
    exec("x = %s" % rendered, ns)
    if isinstance(value, float) and value != value:  # pragma: no cover (nan not in corpus)
        assert ns["x"] != ns["x"]
    else:
        assert ns["x"] == value, (value, rendered)


def test_lit_repr_bool_is_not_rust_debug_leak(agent):
    agent.seed_python_renderer()
    term = term_from_json({"type": "Lit", "value": True})
    rendered = agent.render(term, "python")
    assert rendered == "True", rendered
    assert "Bool(" not in rendered


def test_function_grain_write_with_string_literal_is_valid_python(agent):
    src = "def sign_word(x):\n    return 'positive' if x > 0 else 'non-positive'\n"
    reading = cdr.read_function(agent, src, "sign_word")
    assert reading["emit_error"] is None, reading
    written = cw.write_function(agent, "sign_word", reading["args"], reading["term"])
    assert "'positive'" in written and "'non-positive'" in written
    assert _exec_and_call(written, "sign_word", 5) == "positive"
    assert _exec_and_call(written, "sign_word", -5) == "non-positive"


# =========================================================================== #
#  (3) THE ROUND-TRIP LAW — write(read(f)), read the written function back:
#  same construction, canonically-equal Term, docstring agreement = AGREE.
# =========================================================================== #
@pytest.mark.parametrize("source,func_name,range_bind", [
    (MP3_SOURCE, "_mp3_gain_to_db", None),
    (CYCLIC_SOURCE, "_is_infinite_cyclic", None),
    (RECT_AREA_SOURCE, "rect_area", None),
    (DESCR_LEN_1D_SOURCE, "_descr_len_1d", None),
    (TOTAL_WEIGHT_SOURCE, "total_weight", None),
    (SUM_OF_SQUARES_SOURCE, "sum_of_squares", {"n": 6}),
    (SIGN_SOURCE, "_sign", None),
])
def test_self_consistency_round_trip_law(agent, source, func_name, range_bind):
    result = cw.self_consistency_check(agent, source, func_name, range_bind=range_bind)
    assert result["ok"], result
    assert result["construction_match"], result
    assert result["term_match"], result
    assert result["agreement_verdict"] == "agree", result


def test_self_consistency_reread_never_mints_a_second_construction(agent):
    """The written function's construction must be a HELD one -- writing
    back a recognised shape must never itself look like an unrecognised
    residual (no accidental re-mint on the write side)."""
    result = cw.self_consistency_check(agent, DESCR_LEN_1D_SOURCE, "_descr_len_1d")
    assert result["ok"]
    assert result["reread"]["minted"] is False


# =========================================================================== #
#  (4) WRITE FROM AN NL REQUEST — the end-to-end proof, through converse().
# =========================================================================== #
_VOCAB_REQUESTS = [
    ("Write a function that returns the larger of two numbers.",
     "max_of_two", {"a": 6, "b": 3}, 6),
    ("Write a function that returns the smaller of two numbers.",
     "min_of_two", {"a": 6, "b": 3}, 3),
    ("Write a function that returns the sum of two numbers.",
     "sum_of_two", {"a": 6, "b": 3}, 9),
    ("Write a function that returns the product of two numbers.",
     "product_of_two", {"a": 6, "b": 3}, 18),
    ("Write a function that returns the absolute value of a number.",
     "abs_value", {"a": -4}, 4),
    ("Write a function that returns the average of two numbers.",
     "average_of_two", {"a": 6, "b": 4}, 5),
    ("Write a function that returns the total of a list of numbers.",
     "total_of_list", {"items": [1, 2, 3, 4]}, 10),
    ("Write a function that returns the count of items in a list.",
     "count_of_list", {"items": [1, 2, 3, 4]}, 4),
]


@pytest.mark.parametrize("request_text,construction,sample,expected", _VOCAB_REQUESTS)
def test_write_function_from_request_composes_and_predicts(
        agent, request_text, construction, sample, expected):
    result = cw.write_function_from_request(agent, request_text)
    assert result["ok"], result
    assert result["construction"] == construction, result
    assert "def generated_function(" in result["source"]
    assert '"""' in result["source"], "must carry a docstring"
    # predict_output-style native evaluation confirms the composed Term.
    native_env = {k: v for k, v in sample.items() if k in result["args"]}
    from domains import code_reading as _cdr
    _sub, native, _ag = _cdr._resolve(agent)
    predicted = native.evaluate(result["term"], native_env)
    assert predicted == expected, (request_text, predicted, expected)
    # the written function itself, exec'd, agrees with the native prediction.
    ns: dict = {}
    exec(result["source"], ns)
    got = ns["generated_function"](*[native_env[a] for a in result["args"]])
    assert got == expected


@pytest.mark.parametrize("request_text,construction,sample,expected", _VOCAB_REQUESTS)
def test_write_function_from_request_flows_through_converse(agent, request_text, construction, sample, expected):
    reply = agent.converse(request_text)
    assert "def generated_function(" in reply, reply
    assert "Here is the function" in reply
    ns: dict = {}
    exec(reply.split("Here is the function:\n\n", 1)[1], ns)
    args = [sample[a] for a in
           cw.compose_function_from_request(agent, request_text)["args"]]
    assert ns["generated_function"](*args) == expected


def test_write_function_from_request_honestly_abstains_outside_vocabulary(agent):
    result = cw.write_function_from_request(agent, "Write a function that sorts a list of numbers.")
    assert result["ok"] is False
    assert "reason" in result


def test_converse_abstains_honestly_outside_vocabulary(agent):
    reply = agent.converse("Write a function that sorts a list of numbers.")
    assert "don't hold a shape" in reply


def test_converse_unrelated_turn_is_not_hijacked_by_write_classifier(agent):
    # a message with neither a write-verb nor a function/code noun must
    # never be claimed by _write_function_reply.
    assert cw.looks_like_write_request("What is the weather like today?") is False


# =========================================================================== #
#  (5) NO REGRESSION — CODE-1/CODE-2's own gates + the shared renderer.
# =========================================================================== #
def test_existing_arithmetic_renderer_unaffected_by_code_writing_use(agent):
    cw.write_read_function(agent, MP3_SOURCE, "_mp3_gain_to_db")
    term = term_from_json({"type": "Plus", "items": [{"type": "Lit", "value": 1},
                                                      {"type": "Lit", "value": 2}]})
    assert agent.render(term, "python") == "(1 + 2)"


def test_code1_reading_gate_construction_unaffected(agent):
    # the desc-text tweak to accumulation_loop's ground_template (made to
    # let its docstring round-trip through the English reading pipeline)
    # must not change the CONSTRUCTION verdict CODE-1/2's own gates assert.
    r = cdr.read_function(agent, TOTAL_WEIGHT_SOURCE, "total_weight")
    assert r["construction"] == "accumulation_loop"
    assert r["skeleton"] == [["ASSIGN"], ["FOR"], ["AUGASSIGN"], ["RETURN"]]
