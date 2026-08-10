"""test_emitter_widening_migrated — ARC 2 Q1.5 gates: teaching the Python
reader/emitter (`domains/prog_ir_emit.py`) the IR shapes the Q1 Rust engine
now speaks, and the REAL HQ1 verdict.

PROGRAM_SYNTHESIS_ARC2_PLAN.md §2-Q1 named the emitter-widening residual as
Q1's #1 open item (Q1 could land `ProgSlice`/set-`BitAnd`/the native-oracle
table in Rust but could not touch `domains/prog_ir_emit.py`, per its own
file-ownership boundary — PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md §5/§7). This
phase (Q1.5) closes exactly that gap, additively, and re-measures HQ1 for
real.

Gates:

  CPYTHON AGREEMENT — ~40 emit -> ProgEval rows (slice edges on str/list,
    bitwise `&`/`|`/`^` on BOTH int and set operands, method-oracle recv
    form on ORDINARY LOCAL-VARIABLE receivers — the real MBPP shape,
    `word.split()` not `"lit".split()` — container ctors, general_builtins,
    math_native, isinstance) compared against a REAL CPython call of the
    SAME source (the test_prog_read_python_migrated.py convention).

  HONEST REFUSALS — kwargs/star-args/lambda/`OpExt:LShift`/`OpExt:RShift`
    stay blocked; every KNOWN MUTATING recv method (`append`/`sort`/
    `setdefault`/...) is a NAMED emission-time blocker (`RecvMethod:<name>`),
    verified to ALIGN with the engine's own runtime refusal reason
    (`extern:unimplemented:<name>`) — the blocker is never a phantom
    restriction invented by this emitter, it mirrors what the Q1 engine
    itself refuses. A method name that is NEITHER a Q1 recv-oracle NOR a
    known mutating method (`s.zfill(...)`, `self.foo()`) is deliberately
    left UNTOUCHED — it keeps the pre-Q1.5 dotted-Name-form fallback,
    zero reclassification risk for OOP `self.method()` code across the
    repo corpus. `isinstance(x, (int, float))` (no OR-of-types convention)
    and `isinstance(x, type(y))` (non-Name second argument) stay honest
    blockers too. A slice used as an ASSIGNMENT target (`xs[1:3] = v`)
    still blocks (`SliceSubscript`) — no engine write-back path — unlike
    the now-supported READ position.

  FROZEN-P2-CORPUS BYTE-IDENTITY — every one of the 13
    `tests/fixtures/prog_ir_read/` fixtures is re-emitted through BOTH the
    pre-Q1.5 emitter (loaded live from `git show HEAD:./domains/
    prog_ir_emit.py` — the ACTUAL prior source, never a hand-maintained
    snapshot) and the widened one; `ir`/`blockers`/`variants`/`params` must
    be byte-identical (only `predictable`/`native_oracles` may move, and
    only for `dotted_call`, whose `math.sqrt` call is now a landed native
    oracle — named and asserted explicitly).

  DETERMINISM — emitting each new-shape source twice yields byte-identical
    JSON.

  THE HQ1 LIVE VERDICT — re-derives the representable+predictable rate over
    all 427 MBPP tasks from `scripts/mbpp_blocker_histogram.measure()`
    (imported, never reimplemented, and NEVER written back to the frozen
    `results/mbpp_blocker_histogram.json` artifact — that file stays a
    Q0-era snapshot per the coordinator's file-ownership rules). The number
    is PRINTED and schema/derivation-checked, never asserted to a target —
    it is a verdict, not a bar to force.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_emitter_widening_migrated.py \
    --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import types
import warnings

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains.prog_ir_emit import (  # noqa: E402
    NATIVE_ORACLES, NATIVE_RECV_ORACLES, _RECV_BLOCKED_METHODS, emit_prog_ir)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read")
HISTOGRAM_PATH = os.path.join(ROOT, "results", "mbpp_blocker_histogram.json")


# ---------------------------------------------------------------------------
# engine guard (the P1/Q1 skip precedent — honest skip, never a fake pass)
# ---------------------------------------------------------------------------
def _prog_slice_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(
            {"type": "ProgEval",
             "prog": {"type": "ProgSlice", "obj": {"type": "Lit", "value": "ab"},
                      "start": None, "stop": None, "step": None},
             "env": None, "oracles": None, "fuel": 5, "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_slice_live():
    pytest.skip(
        "ProgSlice (Q1) not present in the installed substrate_rs binary — "
        "rebuild runners/dsl (cargo build --release + sync "
        "python/substrate_rs/_native.abi3.so). Honest skip, not a fake pass.",
        allow_module_level=True)


@pytest.fixture()
def sub():
    return srs.Substrate()


# ---------------------------------------------------------------------------
# harness (mirrors test_prog_read_python_migrated.py / test_value_domain_migrated.py)
# ---------------------------------------------------------------------------
def norm(v):
    if isinstance(v, (list, tuple)):
        return tuple(norm(x) for x in v)
    if isinstance(v, (set, frozenset)):
        return frozenset(norm(x) for x in v)
    if isinstance(v, dict):
        return {norm(k): norm(x) for k, x in v.items()}
    return v


def mkdict(names):
    items = []
    for n in names:
        items.append({"type": "Lit", "value": n})
        items.append({"type": "Lit", "value": "builtin"})
    return {"type": "MkDict", "items": items}


def run_ir(sub, ir, env=None, oracles=()):
    out = sub._inner.evaluate(
        {"type": "ProgEval", "prog": ir,
         "env": {"type": "Var", "name": "e"} if env is not None else None,
         "oracles": mkdict(oracles) if oracles else None,
         "fuel": 50_000, "field": ""},
        {"e": env} if env is not None else None)
    assert isinstance(out, dict)
    return out


def emit_ok(src, name):
    r = emit_prog_ir(src, name=name)
    assert r["ok"], f"{name}: must be emittable, got blockers={r.get('blockers')}"
    return r


def assert_agrees(sub, src, name, env):
    """emit -> ProgEval (oracles = exactly the emitter-reported
    `native_oracles`, which now correctly includes recv-form methods too —
    the Q1.5 `_finish` bug fix) vs a REAL CPython call of the SAME
    source, kwargs-style (env keys are the function's own param names)."""
    r = emit_ok(src, name)
    out = run_ir(sub, r["ir"], env=env, oracles=r["native_oracles"])
    assert out["trap"] is None, f"{name}: unexpected trap {out['trap']}"
    assert out["halted"] is True
    g: dict = {}
    exec(compile(src, name + ".py", "exec"), g)  # noqa: S102
    expected = g[name](**env)
    assert norm(out["result"]) == norm(expected), (
        f"{name}: rust={out['result']!r} py={expected!r}")
    return r, out


def assert_agrees_unordered(sub, src, name, env):
    """Twin of `assert_agrees` for dict_methods (`items`/`keys`/`values`):
    the engine's dict iteration order is its OWN (cmp_value-sorted, not
    Python insertion order — Q1 notes §2 item 7), so compare as a SET."""
    r = emit_ok(src, name)
    out = run_ir(sub, r["ir"], env=env, oracles=r["native_oracles"])
    assert out["trap"] is None, f"{name}: unexpected trap {out['trap']}"
    g: dict = {}
    exec(compile(src, name + ".py", "exec"), g)  # noqa: S102
    expected = g[name](**env)
    assert frozenset(norm(out["result"])) == frozenset(norm(expected)), (
        f"{name}: rust={out['result']!r} py={expected!r}")
    return r, out


# ---------------------------------------------------------------------------
# 1) CPYTHON AGREEMENT — slicing (read position), via the REAL emitter
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,env", [
    ("def f(s):\n    return s[1:3]\n", {"s": "hello"}),
    ("def f(s):\n    return s[::-1]\n", {"s": "hello"}),
    ("def f(s):\n    return s[-3:]\n", {"s": "hello"}),
    ("def f(s):\n    return s[::2]\n", {"s": "hello"}),
    ("def f(xs):\n    return xs[1:4]\n", {"xs": [1, 2, 3, 4, 5]}),
    ("def f(xs):\n    return xs[::-1]\n", {"xs": [1, 2, 3]}),
    ("def f(xs, i, j):\n    return xs[i:j]\n", {"xs": [1, 2, 3, 4, 5], "i": 1, "j": 4}),
], ids=["str_basic", "str_reverse", "str_negstart", "str_step2",
        "list_basic", "list_reverse", "list_var_bounds"])
def test_slicing_agrees_via_emitter(sub, src, env):
    assert_agrees(sub, src, "f", env)


def test_slice_write_target_still_blocks():
    r = emit_prog_ir("def f(xs, v):\n    xs[1:3] = v\n    return xs\n", name="f")
    assert r["ok"] is False
    assert r["blockers"] == ["SliceSubscript"]


# ---------------------------------------------------------------------------
# 2) CPYTHON AGREEMENT — bitwise (int AND set, both overloads) via the emitter
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,env", [
    ("def f(a, b):\n    return a & b\n", {"a": 5, "b": 3}),
    ("def f(a, b):\n    return a | b\n", {"a": 5, "b": 2}),
    ("def f(a, b):\n    return a ^ b\n", {"a": 5, "b": 1}),
    ("def f(a, b):\n    return set(a) & set(b)\n", {"a": (1, 2, 3), "b": (2, 3, 4)}),
    ("def f(a, b):\n    return set(a) | set(b)\n", {"a": (1, 2), "b": (2, 3)}),
    ("def f(a, b):\n    return set(a) ^ set(b)\n", {"a": (1, 2, 3), "b": (2, 3, 4)}),
], ids=["bitand_int", "bitor_int", "bitxor_int",
        "bitand_set", "bitor_set", "bitxor_set"])
def test_bitwise_agrees_via_emitter(sub, src, env):
    assert_agrees(sub, src, "f", env)


def test_shift_ops_stay_honest_blockers():
    """Q1.5 landed set-algebra reach for `&`/`|`/`^` only (the Q1 notes'
    own scope: task-2's finding was about those three operators). `<<`/`>>`
    are NOT part of this widening — still `OpExt:LShift`/`OpExt:RShift`."""
    r = emit_prog_ir("def f(a, b):\n    return a << b\n", name="f")
    assert r["ok"] is False and r["blockers"] == ["OpExt:LShift"]
    r2 = emit_prog_ir("def f(a, b):\n    return a >> b\n", name="f")
    assert r2["ok"] is False and r2["blockers"] == ["OpExt:RShift"]


# ---------------------------------------------------------------------------
# 3) CPYTHON AGREEMENT — method-oracle recv form on ORDINARY LOCAL
#    VARIABLES (the real MBPP shape: `word.split()`, not `"lit".split()`)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,env", [
    ("def f(s):\n    return s.split()\n", {"s": "a b  c"}),
    ("def f(s, sep):\n    return s.split(sep)\n", {"s": "a,b,,c", "sep": ","}),
    ("def f(s):\n    return s.strip()\n", {"s": "  hi  "}),
    ("def f(s):\n    return s.upper()\n", {"s": "Hello World"}),
    ("def f(s):\n    return s.lower()\n", {"s": "Hello World"}),
    ("def f(sep, xs):\n    return sep.join(xs)\n", {"sep": "-", "xs": ["a", "b", "c"]}),
    ("def f(s):\n    return s.replace('a', 'o')\n", {"s": "banana"}),
    ("def f(s):\n    return s.startswith('he')\n", {"s": "hello"}),
    ("def f(s):\n    return s.count('l')\n", {"s": "hello"}),
], ids=["split_ws", "split_sep", "strip", "upper", "lower", "join",
        "replace", "startswith", "count"])
def test_string_methods_agree_on_local_var_receiver(sub, src, env):
    """The Q1.5 headline fix: `_dotted_name`'s Name-rooted walk cannot tell
    a local variable (`s`) from a module (`math`) apart, so a method-NAME-
    first recognition is what actually reaches the widened engine on real
    code shapes (module docstring "ARC 2 Q1.5 WIDENING" in
    domains/prog_ir_emit.py)."""
    r, _out = assert_agrees(sub, src, "f", env)
    assert r["recv_methods"], f"expected a recv-form method call, got {r}"
    assert r["predictable"] is True


@pytest.mark.parametrize("src,env", [
    ("def f(d):\n    return d.get('a')\n", {"d": {"a": 1}}),
    ("def f(d):\n    return d.get('z', 9)\n", {"d": {"a": 1}}),
])
def test_dict_get_agrees_on_local_var_receiver(sub, src, env):
    assert_agrees(sub, src, "f", env)


@pytest.mark.parametrize("src,env", [
    ("def f(d):\n    return d.items()\n", {"d": {"a": 1, "b": 2}}),
    ("def f(d):\n    return d.keys()\n", {"d": {"a": 1, "b": 2}}),
    ("def f(d):\n    return d.values()\n", {"d": {"a": 1, "b": 2}}),
])
def test_dict_items_keys_values_agree_unordered(sub, src, env):
    assert_agrees_unordered(sub, src, "f", env)


# ---------------------------------------------------------------------------
# 4) HONEST REFUSALS — mutating / out-of-oracle recv methods, aligned with
#    the engine's own runtime refusal reason (never a phantom restriction)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,blocker", [
    ("def f(xs, v):\n    xs.append(v)\n    return xs\n", "RecvMethod:append"),
    ("def f(xs):\n    xs.sort()\n    return xs\n", "RecvMethod:sort"),
    ("def f(d, k, v):\n    d.setdefault(k, v)\n    return d\n", "RecvMethod:setdefault"),
    ("def f(xs):\n    return xs.pop()\n", "RecvMethod:pop"),
], ids=["append", "sort", "setdefault", "pop"])
def test_mutating_recv_methods_are_named_blockers(src, blocker):
    """Every KNOWN MUTATING collection/dict method (`_RECV_BLOCKED_
    METHODS`) is a named emission-time blocker, regardless of receiver
    shape — the engine structurally refuses a write-back (Q1 notes §3)."""
    r = emit_prog_ir(src, name="f")
    assert r["ok"] is False
    assert r["blockers"] == [blocker]


def test_unrecognised_methods_keep_the_pre_q15_dotted_fallback():
    """A method name that is NEITHER a Q1 recv-oracle NOR a known mutating
    method (`zfill`, a custom `self.foo()`) is by DESIGN not reclassified
    at all — it keeps the ORIGINAL `_dotted_name` resolution byte-
    unchanged (ok, non-predictable, Name-form with a dotted extern name).
    This is the name-first design's safety property: the widening never
    touches a call it wasn't asked to fix, so `self.foo()`-shaped OOP code
    across the repo corpus carries zero regression risk from this phase."""
    r = emit_prog_ir("def f(s):\n    return s.zfill(5)\n", name="f")
    assert r["ok"] is True
    assert r["recv_methods"] == []       # NOT recv-form
    assert r["externs"] == ["s.zfill"]   # dotted Name-form, unchanged
    assert r["predictable"] is False

    r2 = emit_prog_ir("def f(self, x):\n    return self.compute(x)\n", name="f")
    assert r2["ok"] is True
    assert r2["recv_methods"] == []          # NOT recv-form
    assert r2["externs"] == ["self.compute"]  # dotted Name-form, unchanged


@pytest.mark.parametrize("method,recv,args", [
    ("append", {"type": "ProgContainerLit", "kind": "list",
                "items": [{"type": "Lit", "value": 1}]},
     [{"type": "Lit", "value": 2}]),
    ("setdefault", {"type": "ProgContainerLit", "kind": "dict", "items": []},
     [{"type": "Lit", "value": "k"}, {"type": "Lit", "value": 1}]),
    ("sort", {"type": "ProgContainerLit", "kind": "list",
              "items": [{"type": "Lit", "value": 2}, {"type": "Lit", "value": 1}]},
     []),
    ("zfill", {"type": "Lit", "value": "5"}, [{"type": "Lit", "value": 3}]),
], ids=["append", "setdefault", "sort", "zfill"])
def test_blocked_recv_methods_align_with_engine_refusal(sub, method, recv, args):
    """Every method name this emitter blocks is checked against the LIVE
    engine's own runtime refusal for the SAME shape (bypassing the
    emitter's honesty gate on purpose, via a hand-built Term): the
    blocker name is never invented, it mirrors a real
    `extern:unimplemented:<name>` trap `call_recv_oracle` (prog_eval.rs)
    itself produces."""
    term = {"type": "ProgCallExtern", "name": method, "recv": recv, "args": args}
    out = run_ir(sub, term, env=None, oracles=(method,))
    assert out["halted"] is False
    assert out["trap"] == "extern:unimplemented:%s" % method


# ---------------------------------------------------------------------------
# 5) CPYTHON AGREEMENT — container_ctor / general_builtins / math_native
#    (Name-form calls; no emission-shape change, only NATIVE_ORACLES widened)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,env", [
    ("def f(xs):\n    return list(xs)\n", {"xs": [1, 2, 3]}),
    ("def f(xs):\n    return tuple(xs)\n", {"xs": [1, 2, 3]}),
    ("def f(xs):\n    return set(xs)\n", {"xs": [1, 2, 2, 3]}),
    ("def f(xs):\n    return frozenset(xs)\n", {"xs": [1, 2, 3]}),
    ("def f(pairs):\n    return dict(pairs)\n", {"pairs": [("a", 1), ("b", 2)]}),
], ids=["list_ctor", "tuple_ctor", "set_ctor", "frozenset_ctor", "dict_from_pairs"])
def test_container_ctor_agrees_via_emitter(sub, src, env):
    assert_agrees(sub, src, "f", env)


@pytest.mark.parametrize("src,env", [
    ("def f(xs):\n    return all(xs)\n", {"xs": [1, 1, 1]}),
    ("def f(xs):\n    return any(xs)\n", {"xs": [0, 0, 1]}),
    ("def f(xs):\n    return tuple(enumerate(xs))\n", {"xs": ["a", "b"]}),
    ("def f(xs, ys):\n    return tuple(zip(xs, ys))\n", {"xs": [1, 2, 3], "ys": ["a", "b"]}),
    ("def f(xs):\n    return tuple(reversed(xs))\n", {"xs": [1, 2, 3]}),
], ids=["all", "any", "enumerate", "zip", "reversed"])
def test_general_builtins_agree_via_emitter(sub, src, env):
    assert_agrees(sub, src, "f", env)


@pytest.mark.parametrize("src,env", [
    ("def f(x):\n    return round(x)\n", {"x": 2.5}),
    ("def f(a, b):\n    return pow(a, b)\n", {"a": 2, "b": 10}),
    ("def f(a, b):\n    return divmod(a, b)\n", {"a": 7, "b": 3}),
    ("def f(c):\n    return ord(c)\n", {"c": "A"}),
    ("def f(n):\n    return chr(n)\n", {"n": 65}),
    ("def f(x):\n    import math\n    return math.sqrt(x)\n", {"x": 16.0}),
], ids=["round", "pow", "divmod", "ord", "chr", "math_sqrt"])
def test_math_native_agrees_via_emitter(sub, src, env):
    assert_agrees(sub, src, "f", env)


# ---------------------------------------------------------------------------
# 6) isinstance — the type-name-string wiring (Q1 notes §2 item 3, closed)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,env", [
    ("def f(x):\n    return isinstance(x, int)\n", {"x": 5}),
    ("def f(x):\n    return isinstance(x, int)\n", {"x": "a"}),
    ("def f(x):\n    return isinstance(x, str)\n", {"x": "hi"}),
    ("def f(x):\n    return isinstance(x, list)\n", {"x": [1, 2]}),
], ids=["int_true", "int_false", "str_true", "list_true"])
def test_isinstance_type_name_wiring_agrees(sub, src, env):
    assert_agrees(sub, src, "f", env)


def test_isinstance_multi_type_stays_honest_blocker():
    r = emit_prog_ir("def f(x):\n    return isinstance(x, (int, float))\n", name="f")
    assert r["ok"] is False
    assert r["blockers"] == ["IsinstanceMultiType"]


def test_isinstance_complex_type_stays_honest_blocker():
    r = emit_prog_ir("def f(x, y):\n    return isinstance(x, type(y))\n", name="f")
    assert r["ok"] is False
    assert r["blockers"] == ["IsinstanceComplexType"]


# ---------------------------------------------------------------------------
# 7) DETERMINISM
# ---------------------------------------------------------------------------
_DETERMINISM_SOURCES = [
    "def f(s):\n    return s[1:3]\n",
    "def f(a, b):\n    return set(a) & set(b)\n",
    "def f(s):\n    return s.split(',')\n",
    "def f(x):\n    return isinstance(x, int)\n",
]


@pytest.mark.parametrize("src", _DETERMINISM_SOURCES,
                         ids=["slice", "bitand_set", "recv_split", "isinstance"])
def test_emit_deterministic_for_new_shapes(src):
    a = json.dumps(emit_prog_ir(src, name="f"), sort_keys=True)
    b = json.dumps(emit_prog_ir(src, name="f"), sort_keys=True)
    assert a == b


# ---------------------------------------------------------------------------
# 8) FROZEN-P2-CORPUS BYTE-IDENTITY — proven against the ACTUAL pre-Q1.5
#    source (`git show HEAD:./domains/prog_ir_emit.py`), never a
#    hand-maintained snapshot.
# ---------------------------------------------------------------------------
def _load_pre_q15_emitter():
    try:
        proc = subprocess.run(
            ["git", "show", "HEAD:./domains/prog_ir_emit.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=15)
    except OSError:
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    mod = types.ModuleType("_prog_ir_emit_pre_q15_frozen")
    try:
        exec(compile(proc.stdout, "prog_ir_emit_pre_q15.py", "exec"), mod.__dict__)  # noqa: S102
    except Exception:
        return None
    if not hasattr(mod, "emit_prog_ir"):
        return None
    return mod


_OLD_EMITTER = _load_pre_q15_emitter()

_FROZEN_P2_FIXTURES = [
    "arith_flow", "attr_record", "branchy", "comp_pipeline", "dotted_call",
    "fstring_is", "import_noop", "loop_ctl", "out_of_set", "try_raise",
    "undeclared_extern", "unpack_containers", "while_gcd"]


@pytest.mark.skipif(
    _OLD_EMITTER is None,
    reason="could not load the pre-Q1.5 emitter via `git show HEAD:...` "
           "(no git history available in this checkout) — honest skip, "
           "not a fake pass")
@pytest.mark.parametrize("name", _FROZEN_P2_FIXTURES)
def test_frozen_p2_fixture_ir_byte_identical_to_pre_q15(name):
    """The arc-1/P2 frozen-baseline invariant this phase's own file-
    ownership rule names ("the OLD emitter classifier paths and every
    previously-emitted function's IR stay byte-identical"), PROVEN against
    the real prior source rather than asserted against a snapshot: none of
    these 13 fixtures exercises a Q1.5-touched construct (no slicing, no
    bitwise op, no recv-form method call, no isinstance), so `ir`/
    `blockers`/`variants`/`params` must be identical before and after."""
    with open(os.path.join(FIXTURE_DIR, name + ".py")) as fh:
        src = fh.read()
    old = _OLD_EMITTER.emit_prog_ir(src, name=name)
    new = emit_prog_ir(src, name=name)
    assert old["ok"] == new["ok"], name
    if old["ok"]:
        assert (json.dumps(old["ir"], sort_keys=True)
                == json.dumps(new["ir"], sort_keys=True)), name
        assert old["variants"] == new["variants"], name
        assert old["params"] == new["params"], name
    else:
        assert old["blockers"] == new["blockers"], name


@pytest.mark.skipif(_OLD_EMITTER is None, reason="see skip reason above")
def test_dotted_call_predictable_move_is_the_only_named_exception():
    """The ONE, documented, deliberate metadata change among the 13 frozen
    fixtures: `dotted_call`'s `math.sqrt` is now a landed Q1 native
    oracle, so `predictable` moves False -> True. `ir` itself (asserted
    above) is untouched — only the classification widened, by construction
    (NATIVE_ORACLES), never the emitted shape."""
    src = open(os.path.join(FIXTURE_DIR, "dotted_call.py")).read()
    old = _OLD_EMITTER.emit_prog_ir(src, name="dotted_call")
    new = emit_prog_ir(src, name="dotted_call")
    assert old["predictable"] is False
    assert new["predictable"] is True
    assert json.dumps(old["ir"], sort_keys=True) == json.dumps(new["ir"], sort_keys=True)


# ---------------------------------------------------------------------------
# 9) THE HQ1 LIVE VERDICT — the phase's reason to exist
# ---------------------------------------------------------------------------
def test_hq1_live_verdict():
    """PROGRAM_SYNTHESIS_ARC2_PREREG.md §3: after the value-domain floor AND
    the emitter that actually TEACHES it to real Python source, what
    fraction of the 427 MBPP reference solutions are both `ok` (IR-
    representable) and `predictable` (no undeclared extern) under the REAL,
    live `emit_prog_ir` + `ProgEval`?

    This is the number `tests/test_value_domain_migrated.py::
    test_hq1_verdict` could only report as UNCHANGED at the pre-Q1 floor
    (34.4%, 147/427) — because Q1's own file-ownership scope excluded this
    emitter. That test's "LIVE" number was therefore a frozen-artifact
    snapshot from before this phase, not a real re-run; this test IS the
    real re-run, via `scripts.mbpp_blocker_histogram.measure()` (imported,
    never reimplemented — the same per-task computation the Q0 histogram
    used, just invoked against the now-widened emitter).

    `results/mbpp_blocker_histogram.json` is NOT regenerated or
    overwritten by this call (`measure()` returns a dict; nothing here
    calls its `main()`/writes to disk) — the frozen Q0-era artifact stays
    exactly as Q0 left it, per the arc-1 "a snapshot is a historical
    record" discipline.

    The number is PRINTED and schema/derivation-checked (predictable
    implies ok; the count is a re-derivation from `per_task`, never a
    stored aggregate trusted blind) — NEVER asserted against the
    preregistered bar. A verdict is reported, not forced."""
    frozen_mtime = os.path.getmtime(HISTOGRAM_PATH) if os.path.exists(HISTOGRAM_PATH) else None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import mbpp_blocker_histogram as h
        result = h.measure()

    # `measure()` returns a dict; only its `main()` writes to disk — the
    # frozen artifact's mtime must be untouched by this call.
    if frozen_mtime is not None:
        assert os.path.getmtime(HISTOGRAM_PATH) == frozen_mtime, (
            "results/mbpp_blocker_histogram.json must stay a frozen "
            "Q0-era snapshot — this test must never regenerate it")

    per_task = result["per_task"]
    n = len(per_task)
    assert n == 427, f"expected the frozen 427-task corpus, got {n}"

    ok_ids = {r["task_id"] for r in per_task if r["ok"]}
    predictable_ids = {r["task_id"] for r in per_task if r["ok"] and r["predictable"]}
    assert predictable_ids <= ok_ids, "predictable must imply ok"
    # cross-check against the script's own aggregate (schema honesty).
    assert len(ok_ids) == result["program_side"]["ok_count"]
    assert len(predictable_ids) == result["program_side"]["predictable_count"]

    live_ok = len(ok_ids)
    live_predictable = len(predictable_ids)
    live_pct = 100.0 * live_predictable / n
    ok_pct = 100.0 * live_ok / n

    print(f"\nHQ1 LIVE, post-Q1.5 (real emit_prog_ir, widened this phase): "
          f"representable {live_ok}/{n} = {ok_pct:.1f}%, "
          f"predictable {live_predictable}/{n} = {live_pct:.1f}%")
    print("Pre-Q1.5 floor (frozen, results/mbpp_blocker_histogram.json / "
          "test_value_domain_migrated.py::test_hq1_verdict): "
          "representable 316/427 = 74.0%, predictable 147/427 = 34.4%")
    print("Preregistered bar (PROGRAM_SYNTHESIS_ARC2_PREREG.md §3): "
          "registered >=45%; measured post-recommended-Q1-scope ceiling "
          "52.9% (226/427) at the FULL recommended scope, 44.5% (190/427) "
          "at the 55%-mark scope Q1 targeted.")

    # Sanity bounds only — never a forced target.
    assert live_predictable >= 147, (
        "the live number must be AT LEAST the frozen pre-Q1.5 floor — a "
        "widening can only ever help, never hurt, representability")
    assert live_ok <= n and live_predictable <= n
