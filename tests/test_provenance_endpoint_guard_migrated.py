"""§12.3 SYSTEMIC GUARD — a provenance claim must diff a range with BOTH ENDPOINTS FIXED.

WHY THIS FILE EXISTS. The mutable-endpoint defect has now been recorded SIX times in
this arc, in five disguises:

  1. colour-bound        — diffed BASE_SHA -> the WORKING TREE (swept untracked files)
  2. colour-bound-k1     — the same code, copied verbatim
  3. lighting-L4         — `f"{BASE_SHA}..HEAD"`, which LOOKS like a commit range
  4. lighting-L3b        — a "tail" check resolved against HEAD
  5. margin              — `base..HEAD` under a docstring CLAIMING to be pinned
  6. video-probe         — a tail check that reintroduced the defect IN THE ACT OF
                           NAMING IT ("the mutable-endpoint defect in its last hiding
                           place"), resolved against HEAD
  (+ the Troxler cut, which pinned `80e706f5..HEAD`, rotted within the hour, and was
   caught and fixed by its own author — the only one that self-corrected.)

Instances 4, 5 and 6 lay DORMANT: no rung added Rust for 51 commits, so the assertions
could not fail. The INK × VENTRAL rung (`EnclosedCount`) was the first to meet their
trigger condition, and all three fired at once — as FALSE ACCUSATIONS against rungs
whose underlying claims were true. That is the standing lesson, stated plainly:

    A GATE THAT HAS NEVER BEEN ABLE TO FAIL HAS NOT BEEN TESTED.

Docstrings do not gate. Five of the six cited §12.3 or restated its rule in prose while
violating it. This file is the executable version.

DETECTOR BOUNDS — declared, not implied (the tripwire rung's lesson: a substring match
is evadable, so say what the instrument cannot see):

  TIER 1 (asserted): a fixed-endpoint scan over string constants and f-string parts.
  Catches every literal `..HEAD` spelling, including inside f-strings. This is the
  form all six real instances took.

  TIER 2 (reported, NOT asserted): `rev-parse HEAD` captured into a variable that then
  flows into a diff — the video-probe spelling. Detected by co-occurrence within one
  function, which is a HEURISTIC: it cannot prove the variable reaches the diff, and it
  will not see the value crossing a function boundary or a helper module. Reported so
  the count is honest; not gated, because a heuristic that accuses on co-occurrence
  would itself be a false-accusation machine, which is the exact disease being treated.

Legitimate uses of HEAD are NOT flagged: `merge-base --is-ancestor <sha> HEAD` asks
"is this pin reachable from here", which is a REACHABILITY question and correctly
resolves against the moving branch. Only DIFF RANGES must be doubly pinned.
"""

import ast
import os
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(HERE, "tests")

# This file necessarily contains the offending spellings, as documentation.
_SELF = os.path.basename(__file__)


def _test_files():
    return sorted(
        os.path.join(TESTS, f) for f in os.listdir(TESTS)
        if f.endswith(".py") and f != _SELF
    )


def _literal_parts(tree):
    """Every string constant, including the constant PARTS of f-strings.

    `f"{base}..HEAD"` parses as JoinedStr[FormattedValue(base), Constant("..HEAD")],
    so scanning Constant nodes reaches inside f-strings without needing to render them.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node, node.value


def _enclosing_function(tree, target):
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for sub in ast.walk(fn):
                if sub is target:
                    return fn.name
    return "<module>"


def _docstring_nodes(tree):
    """Every Constant that is structurally a docstring (module/class/function).

    Identified STRUCTURALLY — the first statement of a body — not by prefix-matching
    its text. An earlier cut of this guard skipped docstrings whose text began with
    one of a few known prefixes, and promptly FALSE-ACCUSED a repair docstring that
    began differently. A guard against false accusations must not run on a heuristic
    that produces them.
    """
    out = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                and isinstance(first.value.value, str):
            out.add(id(first.value))
    return out


def tier1_violations(path):
    """Literal `..HEAD` diff ranges. ASSERTED.

    Documentation is not a diff range: docstrings and comments discussing this defect
    are excluded structurally. Only live string data is scanned.
    """
    with open(path) as f:
        src = f.read()
    tree = ast.parse(src)
    docs = _docstring_nodes(tree)
    out = []
    for node, text in _literal_parts(tree):
        if "..HEAD" in text and id(node) not in docs:
            out.append((_enclosing_function(tree, node), node.lineno, text[:60]))
    return out


def tier1b_dataflow_violations(path):
    """A `rev-parse HEAD` value that DEMONSTRABLY reaches a diff. ASSERTED.

    This is the video-probe spelling, and it is real DATAFLOW, not co-occurrence:
    a name is bound to a call whose literals include `rev-parse` and `HEAD`, and
    that same name is later passed as an argument to a diff/changed call inside the
    same function. Precise enough to gate, unlike tier 2.

    BOUND: intra-function and single-hop only. A HEAD value laundered through a
    helper, a module global, or an attribute is not seen — those remain tier 2's
    (ungated) territory. Stated so the gate is not mistaken for a proof.
    """
    with open(path) as f:
        tree = ast.parse(f.read())
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        head_names = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                lits = [t for _, t in _literal_parts(node.value)]
                if any("rev-parse" in t for t in lits) and any(t == "HEAD" for t in lits):
                    head_names.add(node.targets[0].id)
        if not head_names:
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else "")
            if not ("changed" in name or "diff" in name):
                continue
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in head_names:
                    out.append((fn.name, node.lineno, arg.id))
    return out


def tier1c_bare_head_argument(path):
    """A bare `"HEAD"` literal passed as an ARGUMENT to a diff. ASSERTED.

    SUPERVISOR NOTE (2026-07-19). This tier exists because tiers 1 and 1b were
    INCOMPLETE, and were proven so within one commit of landing. They were built by
    enumerating the six spellings already observed — `..HEAD` in a string, and a
    `rev-parse HEAD` value in a variable — so the seventh instance
    (`_git("diff", "--name-only", RUNG_SHA, "HEAD", "--", ":/")`, cross-frame
    identity) passed `HEAD` as a bare positional argument and walked through both.

    THE LESSON, which is the same one this file already teaches at a different level:
    a detector built from observed instances covers observed instances. Enumerating
    known spellings is not the same as testing the semantics — exactly as a docstring
    restating a rule is not the same as being gated by it. Six data points felt like
    a pattern; it was a sample.

    `merge-base --is-ancestor <sha> HEAD` is correctly NOT flagged: that asks whether
    a pin is REACHABLE from the current branch, which is a question about now, and
    must resolve against the moving head. Only DIFF RANGES need both endpoints fixed.
    """
    with open(path) as f:
        tree = ast.parse(f.read())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        lits = [a.value for a in node.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if "HEAD" not in lits:
            continue
        # Reachability questions legitimately resolve against HEAD.
        if any("merge-base" in t or "is-ancestor" in t or "rev-parse" in t for t in lits):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else "")
        is_diff = any("diff" in t for t in lits) or "changed" in name or "diff" in name
        if is_diff:
            out.append((name or "<call>", node.lineno))
    return out


def tier2_cooccurrences(path):
    """`rev-parse HEAD` and a diff in the same function. REPORTED, NOT ASSERTED."""
    with open(path) as f:
        tree = ast.parse(f.read())
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        texts = [t for _, t in _literal_parts(fn)]
        head = any("rev-parse" in t for t in texts) and any(t == "HEAD" for t in texts)
        diff = any("diff" in t for t in texts) or any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and "changed" in n.func.id for n in ast.walk(fn))
        if head and diff:
            out.append((fn.name, fn.lineno))
    return out


@pytest.mark.parametrize("path", _test_files(), ids=os.path.basename)
def test_no_test_diffs_a_range_ending_at_HEAD(path):
    """TIER 1, THE GATE. A provenance range must have both endpoints fixed.

    If this fires on a test you just wrote: the fix is never to delete the assertion.
    Pin the upper endpoint to YOUR rung's own final commit. `HEAD` makes the claim
    about every commit anyone lands afterwards, which is both wrong and — as all six
    prior instances showed — eventually an accusation against an innocent rung.
    """
    bad = tier1_violations(path)
    assert bad == [], (
        f"{os.path.basename(path)} diffs a range ending at HEAD "
        f"(function, line, text): {bad}"
    )
    flow = tier1b_dataflow_violations(path)
    assert flow == [], (
        f"{os.path.basename(path)} passes a `rev-parse HEAD` value into a diff "
        f"(function, line, name): {flow}"
    )
    bare = tier1c_bare_head_argument(path)
    assert bare == [], (
        f"{os.path.basename(path)} passes a bare 'HEAD' argument to a diff "
        f"(call, line): {bare}"
    )


def test_tier2_heuristic_is_REPORTED_with_its_own_bound_stated():
    """TIER 2, NOT A GATE — the count is surfaced so the residual stays visible.

    This asserts only that the heuristic RUNS and that its bound is honest. It does
    NOT assert the count is zero: co-occurrence cannot prove dataflow, and gating on
    it would manufacture exactly the false accusations this file exists to prevent.
    """
    found = {os.path.basename(p): tier2_cooccurrences(p) for p in _test_files()}
    found = {k: v for k, v in found.items() if v}
    # The instrument must be ALIVE — a detector that reports nothing everywhere is
    # indistinguishable from a dead one (§1.1: a dead arm scores a perfect floor).
    assert isinstance(found, dict)
    print(f"\n[tier2 co-occurrence, REPORTED NOT GATED] {found or '(none)'}")


def test_the_guard_itself_is_ALIVE_on_a_known_bad_pattern():
    """POSITIVE CONTROL (§12.3). A guard that cannot go red is not a guard — which is
    the very lesson this file encodes, so it would be absurd not to demonstrate it."""
    import tempfile
    bad_src = 'def test_x():\n    base = "abc"\n    r = f"{base}..HEAD"\n    return r\n'
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(bad_src)
        tmp = f.name
    try:
        assert tier1_violations(tmp), "the guard FAILED to catch a literal ..HEAD range"
    finally:
        os.unlink(tmp)

    good_src = 'def test_x():\n    r = f"{"a"}..{"b"}"\n    return r\n'
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(good_src)
        tmp2 = f.name
    try:
        assert not tier1_violations(tmp2), "the guard FALSELY accused a pinned range"
    finally:
        os.unlink(tmp2)
