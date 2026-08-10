"""THE INSTRUMENT THAT CHECKS INSTRUMENTS — audited with itself.

`scripts/gate_audit.py` claims to check §13's invariant in general rather than
in the spellings someone happened to think of. That claim is worth exactly
nothing until the thing has been shown to be ABLE to fail, so every test here
is by CONSTRUCTION: plant the defect, require the flag; plant the non-defect,
require silence.

THE STANDARD THIS SUITE IS HELD TO, and why it is this high: five gates in
this tree failed, and every one of them PASSED ITS OWN REVIEW. Three provenance
gates sat green for 51 commits and then all fired at once as false accusations.
A clean self-audit is precisely what a blind instrument reports (§12.2), so a
clean self-audit is not evidence here and is never quoted as such.

The seven SPELLINGS below are not a checklist -- they are the measured
falsification set. Four of them are INERT against the tree's existing flagship
§13 gate (`test_vision_floor_migrated.py::test_no_python_thresholds_...`),
established by injection in this rung. If a future edit makes this module inert
on any of them, that is the sixth spelling arriving and this suite is where it
gets caught.
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

from gate_audit import (audit_source, condition_tests, executable_body,  # noqa: E402
                        find_sinks, graph_decision_findings, resolve, trace,
                        _Binder)


def _authored(src: str) -> list:
    return audit_source(src, "<probe>")[0]


def _unresolved(src: str) -> list:
    return audit_source(src, "<probe>")[1]


# =========================================================================== #
#  SOURCE approximated by a TOKEN -- the name-bound literal and its relatives.
#  These are the spellings that walk through a literal-matching gate.
# =========================================================================== #

# Each entry is (name, source). EVERY one hides the same threshold -- 0.5
# reaching an ordering comparison -- behind a different indirection.
NAME_BOUND_SPELLINGS = [
    ("bare_literal",      "def f(x):\n    return x > 0.5\n"),
    ("bound_to_a_name",   "def f(x):\n    tau = 0.5\n    return x > tau\n"),
    ("module_constant",   "TAU = 0.5\ndef f(x):\n    return x > TAU\n"),
    ("default_argument",  "def f(x, tau=0.5):\n    return x > tau\n"),
    ("arithmetic",        "def f(x):\n    tau = 6 / 20\n    return x > tau\n"),
    ("two_hops",          "A = 0.5\ndef f(x):\n    tau = A\n    return x > tau\n"),
    ("negated",           "def f(x):\n    tau = -0.5\n    return x > tau\n"),
    ("cast_laundered",    "def f(x):\n    return x > float(0.5)\n"),
]


@pytest.mark.parametrize("name,src", NAME_BOUND_SPELLINGS, ids=[s[0] for s in NAME_BOUND_SPELLINGS])
def test_a_name_bound_to_a_literal_IS_a_literal(name, src):
    """A NAME BOUND TO A LITERAL IS A LITERAL. This is the newest recorded
    failure class and the most widespread, because binding a constant to a
    name is the natural way to 'clean it up' -- it reads as an improvement and
    it silences the gate.

    The fix is not more spellings, it is TRANSITIVE CLOSURE over bindings, so
    an indirection nobody has written yet is covered too."""
    found = _authored(src)
    assert found, f"{name}: the threshold walked through -- gate is BLIND here"
    assert any("0.5" in f.detail or "0.3" in f.detail or "6" in f.detail
               for f in found), f"{name}: flagged, but did not trace to the literal"


def test_the_trace_reports_the_whole_chain_not_just_the_hit():
    """A finding that names only the sink is a finding someone has to
    re-derive. The chain is the actionable part."""
    found = _authored("TAU = 0.5\ndef f(x):\n    t = TAU\n    return x > t\n")
    assert found
    assert "->" in found[0].detail, f"no binding chain reported: {found[0].detail}"


# =========================================================================== #
#  SINK approximated by a CONTEXT -- both directions of the error.
# =========================================================================== #

# The same threshold, in every syntactic host. A gate that enumerates hosts
# forgets one; this module does not enumerate hosts at all.
SINK_HOSTS = [
    ("if_statement",        "def f(x):\n    if x > 0.5:\n        return 1\n    return 0\n"),
    ("while_loop",          "def f(x):\n    while x > 0.5:\n        x -= 1\n    return x\n"),
    ("ternary",             "def f(x):\n    return 1 if x > 0.5 else 0\n"),
    ("comprehension_guard", "def f(xs):\n    return [a for a in xs if a > 0.5]\n"),
    ("returned_compare",    "def f(x):\n    return x > 0.5\n"),
    ("assert_statement",    "def f(x):\n    assert x > 0.5\n"),
    ("boolean_chain",       "def f(x, y):\n    return x > 0.5 and y\n"),
    ("assignment",          "def f(x):\n    flag = x > 0.5\n    return flag\n"),
    ("min_bound",           "def f(x):\n    return min(x, 0.5)\n"),
    ("max_bound",           "def f(x):\n    return max(0.5, x)\n"),
    ("nested_in_call",      "def f(x):\n    return sorted(a for a in x if a > 0.5)\n"),
    ("lambda_body",         "def f(xs):\n    return list(filter(lambda a: a > 0.5, xs))\n"),
]


@pytest.mark.parametrize("name,src", SINK_HOSTS, ids=[s[0] for s in SINK_HOSTS])
def test_every_syntactic_host_of_a_threshold_is_seen(name, src):
    """A gate that inspects only `ast.If` tests is blind to eleven of these
    twelve. The tree's flagship §13 gate is a regex over `if|elif|while` and
    was MEASURED INERT on `returned_compare`, `min_bound`, `default_argument`
    and the name-bound spelling."""
    assert _authored(src), f"{name}: threshold invisible in this host"


# A gate that cries wolf gets ROUTED AROUND, which is worse than no gate --
# so the false-positive direction is a first-class requirement, not politeness.
NOT_THRESHOLDS = [
    ("array_index",     "def f(xs):\n    return xs[3]\n"),
    ("slice_bounds",    "def f(xs):\n    return xs[1:4]\n"),
    ("range_bound",     "def f():\n    return [i for i in range(10)]\n"),
    ("nested_index",    "def f(xs, i):\n    return xs[i + 2]\n"),
    ("len_arity",       "def f(xs):\n    return len(xs) == 3\n"),
    ("exit_sentinel",   "def f(p):\n    return p.returncode == 0\n"),
    ("expected_count",  "def f(found, count=1):\n    return found != count\n"),
    ("rng_seed",        "def f(rng):\n    return rng.default_rng(102000)\n"),
    ("shape_arg",       "def f(np):\n    return np.zeros(64)\n"),
    ("identity_zero",   "def f(a):\n    return a.get('k', 0.0)\n"),
    ("bool_constant",   "def f(x):\n    return x > True\n"),
]


@pytest.mark.parametrize("name,src", NOT_THRESHOLDS, ids=[s[0] for s in NOT_THRESHOLDS])
def test_things_that_are_not_thresholds_are_not_flagged(name, src):
    """Array indices, arities, loop bounds, enum sizes, exit sentinels and
    RNG seeds are NOT decision thresholds. One recorded failure flagged 3 of 6
    sites falsely; its FIRST FIX WAS ALSO WRONG, because `ast.walk` cannot
    prune. This module classifies by parent context instead of pruning, which
    is why it needs no exemption list -- and an exemption list is what quieting
    a gate looks like."""
    assert not _authored(src), f"{name}: cried wolf on a non-threshold"


def test_a_threshold_INSIDE_a_slice_is_still_a_threshold():
    """The counterpart to the non-threshold list, and the reason the
    array-index skip-set was DELETED rather than kept as harmless belt-and-
    braces. `xs[i > 0.5]` is a real cut point that happens to sit inside a
    subscript; the skip-set suppressed it. A defence against false positives
    that manufactures a false NEGATIVE is a strictly bad trade."""
    assert _authored("def f(xs, i):\n    return xs[i > 0.5]\n"), \
        "a threshold inside a slice was suppressed -- the skip-set is back"


def test_the_ordering_narrowing_did_not_swallow_a_real_threshold():
    """`==`/`!=` were excluded as SENTINEL tests. That narrowing is only
    legitimate if ordering comparisons still bite -- otherwise it is quieting
    wearing precision's clothes."""
    for op in (">", "<", ">=", "<="):
        assert _authored(f"def f(x):\n    return x {op} 0.5\n"), f"{op} stopped biting"


# =========================================================================== #
#  REGION approximated by a SUBSTRING.
# =========================================================================== #

# DEFINITION ORDER IS LOAD-BEARING HERE, and getting it wrong is how this very
# test first passed for the wrong reason.
#
# The first version of this fixture defined `alpha` FIRST. A break-the-
# instrument probe replaced `child.name == part` with `part in child.name` --
# a substring selector, the exact recorded failure -- and the suite STAYED
# GREEN, because the broken selector happened to hit `alpha` first and return
# the right answer by luck.
#
# That is failure #3 reproduced inside the test written to catch failure #3:
# an injection test that PASSES when it should FAIL. `alpha_helper` is now
# defined FIRST, so a substring selector returns the WRONG function and the
# probe discriminates. Verified: with this ordering the break is CAUGHT.
_TWO_FUNCS = (
    "def alpha_helper(x):\n"
    "    return x\n"
    "\n"
    "def alpha(x):\n"
    "    return x > 0.5\n"
)


def test_region_selection_is_by_AST_identity_not_substring():
    """A substring selector matches `alpha` inside `alpha_helper` and silently
    selects the wrong subtree -- which is how a supervisor's own injection test
    PASSED when it should have FAILED. Resolution here is by definition-name
    equality on the AST, so the prefix collision cannot occur."""
    tree = ast.parse(_TWO_FUNCS)
    assert resolve(tree, "alpha").name == "alpha"
    assert resolve(tree, "alpha_helper").name == "alpha_helper"
    # The discriminating pair: the threshold lives in `alpha` ONLY. A substring
    # selector standing on this fixture returns `alpha_helper` for "alpha" --
    # so the first assertion is the one that reddens when selection degrades.
    assert audit_source(_TWO_FUNCS, "<p>", "alpha")[0], \
        "selecting 'alpha' did not reach alpha's threshold -- wrong subtree selected"
    assert not audit_source(_TWO_FUNCS, "<p>", "alpha_helper")[0], \
        "selecting 'alpha_helper' leaked alpha's threshold"


def test_a_missing_region_RAISES_rather_than_selecting_something_else():
    """The failure mode being prevented is silent mis-selection. A selector
    that cannot find its target must say so, not return a neighbour."""
    tree = ast.parse(_TWO_FUNCS)
    with pytest.raises(LookupError):
        resolve(tree, "no_such_function")


def test_prose_is_not_code_docstrings_are_stripped_by_POSITION():
    """A gate went RED ON A DOCSTRING because the string it matched appeared
    in prose. Docstrings are removed structurally -- first statement of a body,
    a bare string expression -- never by pattern, and never by the tree's
    current habit of dropping lines that `startswith('#')`, which removes
    comments and leaves docstrings entirely intact."""
    src = 'def f(x):\n    """We compare x > 0.5 here, in prose."""\n    return x\n'
    assert not _authored(src), "flagged a threshold that exists only in a docstring"
    fn = resolve(ast.parse(src), "f")
    assert len(executable_body(fn)) == 1


def test_the_docstring_strip_does_not_hide_a_real_threshold_below_it():
    """The complement, and the reason the previous test is not enough on its
    own: stripping prose must not strip the code after it."""
    src = 'def f(x):\n    """Prose mentioning 0.5."""\n    return x > 0.5\n'
    assert _authored(src)


def test_this_suite_does_not_match_its_own_source():
    """A substring assertion once MATCHED ITSELF -- inside the test written to
    warn about substring selectors. This suite audits ITS OWN FILE and requires
    the finding count to come from the file's real content, not from the
    probe strings its parametrize tables contain.

    The probe sources above live in STRING LITERALS. A string literal is not
    executable code, so a correct instrument sees none of them."""
    with open(__file__, encoding="utf-8") as fh:
        found, _ = audit_source(fh.read(), __file__)
    assert not found, (
        "this suite's own probe strings were mistaken for its executable code: "
        + "; ".join(f"{f.lineno}:{f.expr}" for f in found))


# =========================================================================== #
#  THE UNRESOLVED BUCKET -- counted, never discarded.
# =========================================================================== #

def test_untraceable_values_are_COUNTED_not_silently_called_clean():
    """`seed_claim`'s posture, and the only honest one: a CLEAN result means
    'nothing was TRACED to a sink', never 'nothing reaches one'. A tool that
    drops what it cannot resolve reports confident absence -- §12.1's error,
    which produced a briefed-twice claim that turned out to be false."""
    src = "def f(x, cfg):\n    return x > cfg.threshold\n"
    assert not _authored(src)
    assert _unresolved(src), "an untraceable operand vanished instead of being counted"


def test_an_augmented_assignment_binds_the_WHOLE_expression_not_its_operand():
    """`x -= 1` binds x to `x - 1`, not to `1`. Binding it to the bare RHS was
    a real bug, and its consequence was the worst kind available here: in
    `while x > 0.5: x -= 1`, `x` traced to `literal 1`, so BOTH operands read
    as authored, the comparison was discarded as constant-folded dead code,
    and A REAL THRESHOLD VANISHED. A false negative produced by a false trace
    is worse than a miss, because the output still looks clean.

    Pinned here directly rather than left to the `while_loop` host test: a
    break-the-instrument probe showed that test stays green under several
    OTHER ways of breaking the binding, so it does not actually hold this
    property down."""
    src = "def f(x):\n    while x > 0.5:\n        x -= 1\n    return x\n"
    binder = _Binder()
    binder.visit(ast.parse(src))
    assert binder.bindings["x"], "no binding recorded for an augmented assignment"
    assert trace(binder.bindings["x"][0], binder).verdict != "AUTHORED", \
        "x resolved to the augmenting literal -- the whole expression was lost"
    assert _authored(src), "the threshold vanished through a false trace"


def test_a_cyclic_binding_terminates_and_reports_unresolved():
    """Termination is structural, not capped by a hand-placed recursion bound
    -- the bound this module used to carry was flagged by this module and
    DELETED rather than tuned (§13: ask what it falls out of; the answer was
    nothing)."""
    src = "def f(x):\n    t = 1\n    t = t + 1\n    return x > t\n"
    audit_source(src, "<p>")  # must return, not recurse forever


# =========================================================================== #
#  THE ACCUMULATOR -- source approximated by the FIRST binding.
#
#  `trace` used to resolve a REBOUND name to its FIRST binding, so an
#  accumulator (`x = 0` then `x += ...`) graded AUTHORED off its `= 0` init.
#  Then `audit_source`'s "both sides authored => dead code" branch SUPPRESSED a
#  real threshold on an accumulated quantity, and the same init-0 produced a
#  FALSE POSITIVE on `max(acc, ...)`. This is failure-class SOURCE-by-token
#  (the widest hole), in a spelling the enclosure-grain rung MEASURED the gate
#  blind on (VISION_ENCLOSURE_GRAIN_RESULTS.md §5.2): the gate bit 3/5 and was
#  blind on 2/5. The fix is proper transitive dataflow -- an accumulation
#  (a binding that reads the name itself) is ACCUMULATED, never AUTHORED --
#  NOT a sixth spelling in a checklist.
# =========================================================================== #

# Every entry HIDES the same threshold -- 0.42 reaching an ordering comparison
# or a saturation bound -- BEHIND AN ACCUMULATOR, which used to make the whole
# comparison read as constant-folded dead code and vanish. Bare and name-bound.
ACCUMULATOR_SPELLINGS = [
    ("aug_bare_compare",
     "def f(xs):\n    x = 0\n    for e in xs:\n        x += 5\n    if x > 0.42:\n        return 1\n    return 0\n"),
    ("plain_bare_return",
     "def f(xs):\n    x = 0\n    for e in xs:\n        x = x + 5\n    return x > 0.42\n"),
    ("running_max_bound",
     "def f(xs):\n    x = 0\n    for e in xs:\n        x = max(x, 0.42)\n    return x\n"),
    ("aug_name_bound_step",
     "def f(xs):\n    C = 5\n    x = 0\n    for e in xs:\n        x += C\n    if x > 0.42:\n        return 1\n    return 0\n"),
    ("ratio_of_two_accumulators",
     "def f(xs):\n    enc = 0\n    ncell = 0\n    for e in xs:\n        enc += e\n        ncell += 1\n    return enc / ncell > 0.42\n"),
]


@pytest.mark.parametrize("name,src", ACCUMULATOR_SPELLINGS,
                         ids=[s[0] for s in ACCUMULATOR_SPELLINGS])
def test_a_threshold_on_an_ACCUMULATED_value_is_still_a_threshold(name, src):
    """The threshold `0.42` must be FLAGGED and it must trace to the LITERAL
    0.42 -- NOT to the accumulator's `= 0` initialiser, and NOT be swallowed as
    dead code. If any of these goes silent, the first-binding trace bug is back
    and a tuned cut point on an accumulated value ships undetected -- the worst
    failure available to this instrument, since the output still looks clean."""
    found = _authored(src)
    assert found, f"{name}: the accumulated threshold walked through -- gate is BLIND here"
    assert any("0.42" in f.detail for f in found), \
        f"{name}: flagged, but did not trace to the real literal 0.42: {[f.detail for f in found]}"
    assert not any(f.detail.rstrip().endswith("literal 0") for f in found), \
        f"{name}: reported the accumulator's zero-init as the threshold (masks the real one)"


def test_the_running_max_of_two_measurements_is_NOT_a_threshold():
    """The FALSE-POSITIVE direction, same cause. `max(largest, running)` with
    NO literal -- a running maximum of measured values -- reported
    `largest -> literal 0` because the accumulator resolved to its `= 0` init.
    A gate that cries wolf on an accumulator's initialiser gets ROUTED AROUND.
    An accumulated value is ACCUMULATED, not AUTHORED, so there is nothing to
    flag."""
    src = ("def f(xs):\n    largest = 0\n    for e in xs:\n"
           "        run = g(e)\n        largest = max(largest, run)\n    return largest\n")
    assert not _authored(src), \
        "cried wolf on a running-max accumulator's zero initialiser"


def test_an_accumulator_grades_ACCUMULATED_not_AUTHORED():
    """The mechanism, pinned directly rather than left to the spellings above:
    an accumulator is a DERIVED quantity (init-plus-steps), so its provenance
    is ACCUMULATED -- never AUTHORED (which would resolve it to its initialiser
    and let the dead-code branch swallow the real threshold)."""
    binder = _Binder()
    binder.visit(ast.parse("def f(xs):\n    x = 0\n    for e in xs:\n        x += 5\n    return x\n"))
    # x has bindings [0, (x + 5)] -- the second reads x, so x is an accumulator.
    name = ast.Name(id="x", ctx=ast.Load())
    assert trace(name, binder).verdict == "ACCUMULATED", \
        "an accumulator resolved to its first binding -- the first-binding bug is back"


# =========================================================================== #
#  IS THIS GATE ABLE TO FAIL? -- the question three provenance gates in this
#  tree could not answer for 51 commits.
# =========================================================================== #

def test_the_gate_is_ABLE_to_fail():
    """A gate that has never been shown to fail has not been tested. If this
    assertion ever needs deleting, the instrument has stopped working."""
    assert _authored("def f(x):\n    return x > 0.5\n"), \
        "the instrument cannot detect the simplest possible threshold"
    assert not _authored("def f(xs):\n    return xs[3]\n"), \
        "the instrument flags everything, which is the same as flagging nothing"


def test_the_instrument_audits_ITSELF_clean():
    """Reported LAST and deliberately so. On its own this proves nothing --
    a blind instrument audits everything clean, including itself (§12.2). It
    is meaningful only standing on every aliveness test above it, and it is
    quoted only alongside them.

    Two real findings came out of running this: a hand-placed recursion bound
    in `gate_audit.py` (deleted, not tuned) and two sentinel-comparison false
    positives in `gate_inject.py` (which justified narrowing the sink type to
    ORDERING comparisons -- recorded at the narrowing site, per the rule that
    a gate made less strict ships with the false positive that justified it).

    For the record, this module does NOT audit itself to zero findings, and
    saying so is the honest form. `gate_audit.py:len(pairs) > 1` is a real
    finding, graded T3 CARDINALITY -- a count compared against a small integer.
    The assertion is therefore on T1 (chosen cut points), which is the claim
    §13 actually makes. Asserting `not found` at every tier would have been the
    stricter-looking choice and the wrong one: it would have pushed me to
    delete or disguise a correctly-graded T3 to keep a green number, which is
    §5's metric surgery pointed at my own instrument.
    """
    for mod in ("scripts/gate_audit.py", "scripts/gate_inject.py"):
        with open(os.path.join(HERE, mod), encoding="utf-8") as fh:
            found, _ = audit_source(fh.read(), mod)
        cuts = [f for f in found if f.tier == "T1"]
        assert not cuts, f"{mod}: T1 cut points {[(f.lineno, f.expr) for f in cuts]}"


# =========================================================================== #
#  THE SECOND INVARIANT -- "no path runs from a GRAPH READ to a CONDITION".
#
#  This is the architecture rule's gate, and it failed the same three ways the
#  §13 gates did. `tests/test_verdict_comparator_migrated.py`'s adapter gate
#  tested `"node(" in ast.dump(node)`, and that substring CANNOT OCCUR IN
#  `ast.dump` OUTPUT FOR ANY PROGRAM -- so the predicate had never been able to
#  fire, while carrying a five-name exemption list that says its author
#  believed it had.
# =========================================================================== #

#: Every spelling of "the adapter branches on graph state". The first is the
#: one the incumbent predicate was WRITTEN for; the rest are the indirections
#: that a token proxy cannot see. They are not a checklist of observed
#: failures -- they are the syntactic hosts Python's grammar HAS, which is why
#: a seventh spelling does not walk past them.
GRAPH_DECISION_SPELLINGS = [
    ("direct_if",   'def f(s, n):\n    if s.node(n)["attrs"]["k"]:\n        return 1\n    return 0\n'),
    ("name_bound",  'def f(s, n):\n    v = s.node(n)["attrs"]["k"]\n    if v > 0.5:\n        return 1\n    return 0\n'),
    ("ternary",     'def f(s, n):\n    return 1 if s.node(n)["attrs"]["k"] else 0\n'),
    ("while_loop",  'def f(s, n):\n    while s.node(n)["attrs"]["k"]:\n        break\n    return 0\n'),
    ("comp_guard",  'def f(s, ns):\n    return [n for n in ns if s.node(n)["attrs"]["k"]]\n'),
    ("assert_test", 'def f(s, n):\n    assert s.node(n)["attrs"]["k"]\n'),
    ("get_attr",    'def f(s, n):\n    if s.get_attr(n, "k"):\n        return 1\n    return 0\n'),
    ("two_hops",    'def f(s, n):\n    a = s.node(n)\n    b = a["attrs"]\n    if b:\n        return 1\n    return 0\n'),
]


@pytest.mark.parametrize("name,src", GRAPH_DECISION_SPELLINGS,
                         ids=[s[0] for s in GRAPH_DECISION_SPELLINGS])
def test_a_graph_read_reaching_a_condition_is_SEEN(name, src):
    """Break the transitive closure and `name_bound` / `two_hops` go green.
    Narrow the sink back to `ast.If` and `ternary`, `while_loop`, `comp_guard`
    and `assert_test` go green -- four of eight, which is the measure of how
    much an `ast.If`-only enumeration misses."""
    assert graph_decision_findings(src), f"{name}: a graph decision was not seen"


NOT_GRAPH_DECISIONS = [
    # A conditional on a value that is NOT graph state. Flagging this is the
    # CRIES-WOLF direction, and the incumbent's whole-subtree `ast.dump` form
    # committed it: `ast.dump` of an `ast.If` includes its BODY.
    ("plain_arith",   'def f(x):\n    if x > 0.5:\n        return 1\n    return 0\n'),
    ("read_inside",   'def f(s, n, flag):\n    if flag:\n        v = s.node(n)\n        return v\n    return None\n'),
    ("count_test",    'def f(xs):\n    if len(xs) > 1:\n        return 1\n    return 0\n'),
    ("read_no_cond",  'def f(s, n):\n    return s.node(n)["attrs"]["k"]\n'),
]


@pytest.mark.parametrize("name,src", NOT_GRAPH_DECISIONS,
                         ids=[s[0] for s in NOT_GRAPH_DECISIONS])
def test_a_condition_on_a_NON_graph_value_is_not_flagged(name, src):
    """The negative control. `read_inside` is the measured false positive that
    justified scoping the check to the condition's TEST rather than the whole
    `if` subtree -- a narrowing of POSITION (structural), shipped here with the
    case that justifies it, per the rule that a loosening without its false
    positive is a gate that was QUIETED rather than made precise."""
    assert not graph_decision_findings(src), \
        f"{name}: flagged something that is not a decision over graph state"


def test_the_incumbent_substring_predicate_CANNOT_MATCH_recorded_by_construction():
    """The record of WHY the verdict-comparator gate was dead, kept as an
    executable fact rather than a claim in a results document.

    `ast.dump` renders `s.node(x)` as ``Attribute(..., attr='node')``. The
    substring `node(` is therefore unreachable in its output, for every
    program. A gate whose predicate is unsatisfiable is not strict; it is
    absent, and it reads as strict."""
    for src in ("s.node(x)", "a.get_attr(b)", "node(1)", "x.node", "s.nodes()"):
        dumped = ast.dump(ast.parse(f"if {src}: pass").body[0])
        assert "node(" not in dumped, f"{src}: the premise of this record is wrong"
    # ... and the ONE half that could match is absent from the audited file,
    # which is why neither disjunct could fire on it.
    with open(os.path.join(HERE, "domains", "verdict_comparator_world.py"),
              encoding="utf-8") as fh:
        assert "get_attr" not in fh.read()


def test_every_conditional_construct_the_grammar_has_is_a_sink():
    """SINK typed by POSITION, not by an enumeration someone remembered. If a
    construct is dropped from `condition_tests`, the corresponding spelling
    above goes green -- this test names the count so a silent deletion is
    loud."""
    src = ('def f(s, n, ns):\n'
           '    if n:\n        pass\n'
           '    x = 1 if n else 0\n'
           '    while n:\n        break\n'
           '    assert n\n'
           '    return [i for i in ns if i]\n')
    fn = ast.parse(src).body[0]
    assert len(condition_tests(fn)) == 5, \
        "a conditional construct was dropped from the sink typing"
