"""test_prog_read_python_migrated — P2 (python frame) gates for the NEW
additive hub-IR emission path (`domains/prog_ir_emit.py`), per
PROGRAM_SYNTHESIS_PREREG.md §4 and the P2 task card.

Gates:

  SEMANTIC — every fixture under tests/fixtures/prog_ir_read/ is emitted
    (`emit_prog_ir` -> hub-IR Term-JSON) and executed by `ProgEval` (the P1
    Rust interpreter) against sample inputs; the RESULT and the CPython
    locals (captured at return via a mechanical tracer) must agree with a
    CPython call of the SAME source. Oracles declared = exactly the
    emitter-reported native externs — nothing smuggled.

  HONEST TRAP — an undeclared extern is representable but traps
    `extern:<name>` (halted False, result None), and a dotted extern name
    is captured verbatim (`math.sqrt`).

  HONEST RESIDUAL — an out-of-P1-set function returns
    {ok: False, blockers: [...]} with the exact expected blocker names and
    NO partial IR.

  REFLECT ROUND-TRIP — every emitted IR JSON survives
    `add_term_subgraph` -> `term_subgraph_json` canonically identical and
    idempotent (the P1 reflect law, applied to EMITTED trees).

  DETERMINISM — emitting twice yields byte-identical JSON.

  VARIANT SPAN — the ok-fixtures jointly exercise the FULL P1 variant set
    (all 23 Prog* statement/expression variants).

  GRAPH-MODE PARITY — the AstNode-subgraph entry emits byte-identical IR
    to the ast entry on a representative fixture, and blocks HONESTLY
    (`GraphRepr:fstring_conversion`) where the graph representation cannot
    carry a needed fact.

The frozen CODE-arc emitter path is pinned by
tests/test_code_synthesis_baseline_migrated.py (run alongside; this file
deliberately never imports the old emitter).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest --confcutdir=. \
     tests/test_prog_read_python_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import copy
import json
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains.prog_ir_emit import (  # noqa: E402
    NATIVE_ORACLES, P1_VARIANT_SET, emit_prog_ir, emit_prog_ir_from_graph)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read")


# ---------------------------------------------------------------------------
# engine guard (the P1 skip precedent — honest skip, never a fake pass)
# ---------------------------------------------------------------------------
def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval", "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 5, "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip("ProgEval Term not present in the installed substrate_rs "
                "binary — rebuild runners/dsl. Honest skip, not a fake pass.",
                allow_module_level=True)


# ---------------------------------------------------------------------------
# mechanical helpers
# ---------------------------------------------------------------------------
def fixture_source(name: str) -> str:
    with open(os.path.join(FIXTURE_DIR, name + ".py")) as fh:
        return fh.read()


def load_fixture_fn(name: str):
    g: dict = {}
    exec(compile(fixture_source(name), name + ".py", "exec"), g)  # noqa: S102
    return g[name]


def call_capture_locals(fn, kwargs):
    """Call fn(**kwargs) and capture its frame locals at return — the
    CPython side of the env-agreement gate (mechanical tracer)."""
    captured: dict = {}

    def tracer(frame, event, arg):
        if event == "call" and frame.f_code is fn.__code__:
            def local(frame, event, arg):  # noqa: ARG001
                if event == "return":
                    captured.update(frame.f_locals)
                return local
            return local
        return None

    sys.settrace(tracer)
    try:
        result = fn(**kwargs)
    finally:
        sys.settrace(None)
    return result, captured


def norm(v):
    if isinstance(v, (list, tuple)):
        return tuple(norm(x) for x in v)
    if isinstance(v, (set, frozenset)):
        return frozenset(norm(x) for x in v)
    if isinstance(v, dict):
        return {norm(k): norm(x) for k, x in v.items()}
    return v


def mkdict(d):
    items = []
    for k, v in d.items():
        items.append({"type": "Lit", "value": k})
        items.append({"type": "Lit", "value": v})
    return {"type": "MkDict", "items": items}


def run_prog_eval(sub, ir, env=None, oracles=(), fuel=200_000):
    out = sub._inner.evaluate(
        {"type": "ProgEval", "prog": ir,
         "env": {"type": "Var", "name": "e"} if env else None,
         "oracles": mkdict({n: "builtin" for n in oracles}) if oracles else None,
         "fuel": fuel, "field": ""},
        {"e": env} if env else None)
    assert isinstance(out, dict)
    return out


def _canon(d):
    """null ≡ absent, recursively (the P1 reflect-dialect canonicalisation)."""
    if isinstance(d, dict):
        return {k: _canon(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [_canon(x) for x in d]
    return d


def emit_fixture(name: str):
    r = emit_prog_ir(fixture_source(name), name=name)
    assert r["ok"], f"{name} must be emittable, got blockers={r.get('blockers')}"
    return r


# ---------------------------------------------------------------------------
# the semantic fixture battery: (fixture, inputs, env_keys)
#   env_keys None -> compare every CPython-captured local that is not a
#   module/callable (import_noop pins its own list: `sep` is a plain str
#   the IR's no-op ImportStmt legitimately does not bind).
# ---------------------------------------------------------------------------
SEMANTIC_CASES = [
    ("arith_flow", {"a": 4, "b": 5}, None),          # default k binds
    ("arith_flow", {"a": 4, "b": 5, "k": 2}, None),  # env overrides default
    ("branchy", {"x": 12, "name": "zed"}, None),
    ("branchy", {"x": 5, "name": ""}, None),          # `or` operand semantics
    ("branchy", {"x": -3, "name": "ann"}, None),
    ("loop_ctl", {"n": 10}, None),                    # break path
    ("loop_ctl", {"n": 3}, None),                     # for-else path
    ("while_gcd", {"a": 252, "b": 105}, None),
    ("unpack_containers", {"p": (3, 4)}, None),
    ("try_raise", {"x": -2}, None),                   # raise -> caught
    ("try_raise", {"x": 6}, None),                    # clean path
    ("comp_pipeline", {"xs": (1, 2, 3, 4), "lo": 1}, None),
    ("fstring_is", {"v": None, "x": 7}, None),
    ("fstring_is", {"v": 3, "x": 7}, None),
    ("import_noop", {"z": 41}, ["z", "w"]),
]

OK_FIXTURES = sorted({c[0] for c in SEMANTIC_CASES}
                     | {"attr_record", "undeclared_extern", "dotted_call"})


@pytest.fixture()
def sub():
    return srs.Substrate()


# ---------------------------------------------------------------------------
# 1) SEMANTIC — emit -> ProgEval ≡ CPython (result + env)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,inputs,env_keys",
                         SEMANTIC_CASES,
                         ids=[f"{n}-{i}" for i, (n, _, _) in enumerate(SEMANTIC_CASES)])
def test_semantic_agreement(sub, name, inputs, env_keys):
    r = emit_fixture(name)
    out = run_prog_eval(sub, r["ir"], env=dict(inputs),
                        oracles=r["native_oracles"])
    assert out["trap"] is None, f"{name}: unexpected trap {out['trap']}"
    assert out["halted"] is True

    fn = load_fixture_fn(name)
    expected, py_locals = call_capture_locals(fn, dict(inputs))
    assert norm(out["result"]) == norm(expected), (
        f"{name}: result disagreement rust={out['result']!r} py={expected!r}")

    if env_keys is None:
        env_keys = [k for k, v in py_locals.items()
                    if not isinstance(v, (types.ModuleType, types.FunctionType,
                                          types.BuiltinFunctionType, type))]
    for k in env_keys:
        assert k in out["env_out"], f"{name}: env missing {k!r}"
        assert norm(out["env_out"][k]) == norm(py_locals[k]), (
            f"{name}: env disagreement on {k!r}: "
            f"rust={out['env_out'][k]!r} py={py_locals[k]!r}")


def test_semantic_attr_record(sub):
    """AttrGet/AttrSet: ProgEval records are Dicts (the documented P1 record
    convention); the CPython twin uses a real object. Results must agree."""
    r = emit_fixture("attr_record")
    out = run_prog_eval(sub, r["ir"], env={"r": {}, "k": 3})
    assert out["trap"] is None and out["halted"] is True

    fn = load_fixture_fn("attr_record")
    expected = fn(types.SimpleNamespace(), 3)
    assert norm(out["result"]) == norm(expected)
    # the record mutation is visible in env_out (rebuild-along-path, no alias)
    assert out["env_out"]["r"] == {"count": 6}


# ---------------------------------------------------------------------------
# 2) HONEST TRAPS — undeclared extern; dotted name verbatim
# ---------------------------------------------------------------------------
def test_undeclared_extern_traps(sub):
    r = emit_fixture("undeclared_extern")
    assert r["externs"] == ["helper_quantity"]
    assert r["predictable"] is False
    out = run_prog_eval(sub, r["ir"], env={"x": 5})   # no oracles declared
    assert out["halted"] is False
    assert out["trap"] == "extern:helper_quantity"
    assert out["result"] is None
    assert "y" not in out["env_out"]
    with pytest.raises(NameError):
        load_fixture_fn("undeclared_extern")(5)


def test_dotted_extern_name_verbatim(sub):
    """NECESSARY CORRECTION (Q1.5, not a regression): `math.sqrt` is now
    a LANDED native oracle (PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md
    math_native), so `dotted_call` is now ProgEval-predictable and no
    longer traps when its oracle is declared — the emitter's own
    `NATIVE_ORACLES` table was widened to say exactly that (module
    docstring "ARC 2 Q1.5 WIDENING"). The property this test exists to
    pin — a dotted extern name is captured VERBATIM and traps HONESTLY
    when its oracle is withheld, regardless of native-oracle status
    (`declared` is checked against the CALLER's oracle dict, never the
    engine's own native-oracle table) — is unchanged and re-demonstrated
    below instead of via non-nativeness."""
    r = emit_fixture("dotted_call")
    assert "math.sqrt" in r["externs"]
    assert "abs" in r["native_oracles"]
    assert "math.sqrt" in r["native_oracles"]
    assert r["predictable"] is True
    out = run_prog_eval(sub, r["ir"], env={"x": 9}, oracles=r["native_oracles"])
    assert out["trap"] is None
    assert out["halted"] is True
    assert norm(out["result"]) == (3.0, 9)
    # Verbatim dotted-name capture, still an honest trap when the extern
    # is NOT declared by the caller (independent of native-oracle status).
    out2 = run_prog_eval(sub, r["ir"], env={"x": 9}, oracles=("abs",))
    assert out2["halted"] is False
    assert out2["trap"] == "extern:math.sqrt"


# ---------------------------------------------------------------------------
# 3) HONEST RESIDUAL — out-of-set function: exact blocker names, no IR
# ---------------------------------------------------------------------------
def test_out_of_set_residual():
    r = emit_prog_ir(fixture_source("out_of_set"), name="out_of_set")
    assert r["ok"] is False
    assert r["blockers"] == ["Assert", "Delete", "Lambda", "With"]
    assert "ir" not in r, "a blocked function must NEVER carry a partial IR"


def test_expression_grain_residuals():
    """The semantics-pinned refusals (module docstring): floordiv outside
    the liftable form (extern-bearing operand; non-literal divisor; While
    test), statically-string arithmetic. `xs[1:3]` (Q1.5: NECESSARY
    CORRECTION, not a regression — plain read-position slicing now emits
    `ProgSlice`, see `test_slicing_agrees_via_emitter` in
    tests/test_emitter_widening_migrated.py) is REMOVED from this
    residual list; `d = xs[1:3]` no longer blocks."""
    src = ("def h(a, s, xs, b0):\n"
           "    b = len(xs) // 2\n"       # operand carries an extern
           "    e = a // b0\n"            # divisor not a positive literal
           "    while a // 2 > 1:\n"      # While test: per-iteration, no lift
           "        a -= 1\n"
           "    c = 'pre' + s\n"
           "    return (b, c, e)\n")
    r = emit_prog_ir(src, name="h")
    assert r["ok"] is False
    assert r["blockers"] == ["OpExt:FloorDiv", "StrArithStatic"]


def test_slice_still_blocks_as_an_assignment_target():
    """A slice WRITE target has no engine write-back path (Q1 notes §3
    "the mutating-recv-call gap" argument applies identically here) —
    `xs[1:3] = v` stays the honest `SliceSubscript` blocker, unlike the
    now-supported READ position pinned above."""
    src = "def h(xs, v):\n    xs[1:3] = v\n    return xs\n"
    r = emit_prog_ir(src, name="h")
    assert r["ok"] is False
    assert r["blockers"] == ["SliceSubscript"]


def test_floordiv_lift_is_exact():
    """Floordiv by a positive literal lifts to the composite prelude
    `__u = a - (a % b); __u //= b` — CPython-exact incl. NEGATIVE
    dividends (the engine's bare aug-floordiv truncates; the composite
    floors), int in / int out. The OLD emitter's FloorDiv->Div
    approximation is refused, not repeated. Also covers the
    conditional-branch position (the _descr_len_1d shape)."""
    src = ("def fd(a, flag):\n"
           "    x = a // 2\n"
           "    y = (a * (a - 1)) // 2 if flag else 0\n"
           "    return (x, y)\n")
    r = emit_prog_ir(src, name="fd")
    assert r["ok"], r
    g: dict = {}
    exec(src, g)  # noqa: S102
    s = srs.Substrate()
    for a in (7, -7, 17, -17, 8, 0):
        for flag in (True, False):
            out = run_prog_eval(s, r["ir"], env={"a": a, "flag": flag})
            assert out["trap"] is None
            expected = g["fd"](a, flag)
            assert norm(out["result"]) == norm(expected), (a, flag, out)
            assert all(isinstance(x, int) for x in out["result"])


# ---------------------------------------------------------------------------
# 4) REFLECT ROUND-TRIP — emitted IR through the graph and back, canonical
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", OK_FIXTURES)
def test_reflect_round_trip(sub, name):
    r = emit_fixture(name)
    nid = sub._inner.add_term_subgraph(r["ir"])
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert _canon(c1) == _canon(r["ir"]), f"{name}: reflect drifted"
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c2 == c1, f"{name}: second round-trip drifted"


# ---------------------------------------------------------------------------
# 5) DETERMINISM — emit twice, byte-identical
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", OK_FIXTURES)
def test_emit_deterministic(name):
    src = fixture_source(name)
    a = json.dumps(emit_prog_ir(src, name=name), sort_keys=True)
    b = json.dumps(emit_prog_ir(src, name=name), sort_keys=True)
    assert a == b


# ---------------------------------------------------------------------------
# 6) VARIANT SPAN — the fixtures jointly exercise the FULL P1 variant set
# ---------------------------------------------------------------------------
def test_fixtures_span_full_p1_variant_set():
    used: set = set()
    for name in OK_FIXTURES:
        used |= set(emit_fixture(name)["variants"])
    missing = P1_VARIANT_SET - used
    assert not missing, f"P1 variants not exercised by any fixture: {sorted(missing)}"
    assert used <= P1_VARIANT_SET | {"Seq"}, "emitter used out-of-set variants"


# ---------------------------------------------------------------------------
# 7) GRAPH-MODE — parity on the AstNode-subgraph entry + honest repr gap
# ---------------------------------------------------------------------------
class _Shim:
    """The histogram script's mechanical graph container (node/neighbours
    contract), local so this suite has no coupling to scripts/."""

    def __init__(self):
        self._nodes = []
        self._out = {}

    def add_node(self, ntype, attrs):
        self._nodes.append({"type": ntype, "attrs": dict(attrs)})
        return len(self._nodes) - 1

    def add_edge(self, src, etype, tgt):
        self._out.setdefault((src, etype), []).append(tgt)

    def node(self, nid):
        return self._nodes[nid]

    def neighbours(self, nid, etype):
        return list(self._out.get((nid, etype), []))


def _ingest_fixture(name):
    from domains import ast_to_term
    shim = _Shim()
    ast_to_term.ingest_ast(shim, fixture_source(name), root_label=name)
    froot = next(i for i, n in enumerate(shim._nodes)
                 if n["attrs"].get("ast_type") == "FunctionDef")
    return shim, froot


@pytest.mark.parametrize("name", ["arith_flow", "while_gcd", "loop_ctl",
                                  "unpack_containers"])
def test_graph_mode_parity(name):
    shim, froot = _ingest_fixture(name)
    rg = emit_prog_ir_from_graph(shim, froot)
    ra = emit_prog_ir(fixture_source(name), name=name)
    assert rg["ok"] and ra["ok"]
    assert json.dumps(rg["ir"], sort_keys=True) == \
        json.dumps(ra["ir"], sort_keys=True), f"{name}: graph/ast divergence"


def test_graph_mode_honest_repr_gap():
    """The ingested AstNode graph does not carry the f-string conversion
    flag; graph-mode emission must refuse by name, never guess."""
    shim, froot = _ingest_fixture("fstring_is")
    rg = emit_prog_ir_from_graph(shim, froot)
    assert rg["ok"] is False
    assert "GraphRepr:fstring_conversion" in rg["blockers"]


# ---------------------------------------------------------------------------
# 8) SOURCE AUDIT — emitted IR carries no silent extras: every ok fixture's
#    IR references only P1 Prog* variants + the documented DSL expression set
# ---------------------------------------------------------------------------
_ALLOWED_DSL = {"Lit", "Var", "Plus", "Minus", "Times", "Div", "Mod", "Pow",
                "Neg", "Not", "Eq", "Lt", "Lte", "Gt", "Gte", "In",
                "IfThenElse", "And"}


def _types_in(term, acc):
    if isinstance(term, dict):
        t = term.get("type")
        if t:
            acc.add(t)
        for v in term.values():
            _types_in(v, acc)
    elif isinstance(term, (list, tuple)):
        for x in term:
            _types_in(x, acc)
    return acc


def test_ir_type_closure():
    allowed = {"Prog" + v for v in P1_VARIANT_SET} | _ALLOWED_DSL
    for name in OK_FIXTURES:
        types_used = _types_in(emit_fixture(name)["ir"], set())
        extra = types_used - allowed
        assert not extra, f"{name}: unexpected Term types {sorted(extra)}"
