"""test_render_python_migrated — P5 track A gates: statement-grain PYTHON
rendering (hub Program-IR -> runnable source) as graph-resident RenderRules
(seeds/render_python_statements.json + domains/render_python.py), per
PROGRAM_SYNTHESIS_PLAN.md §4-P5 and PROGRAM_SYNTHESIS_PREREG.md §7 (H5).

Gates:

  SEED INTEGRITY — the seed file of record byte-equals the builder output
    (they can never drift silently); installing is idempotent per head and
    covers every P1 Prog* variant plus the P2 IR expression closure.

  THE ROUND-TRIP LAW (the phase gate) — for EVERY ok P2 fixture
    (tests/fixtures/prog_ir_read/) and six P4-shape synthesized programs:
    IR -> render -> ast.parse -> emit_prog_ir -> IR, canonically identical
    under the DOCUMENTED canonicalization set (render_python.canonical_ir:
    C1 null≡absent, C2 ProgSeq flattening, C3 boolop normal form, C4
    Neg(Lit), C5 variadic left-fold — enumerated in
    PROGRAM_SYNTHESIS_P5_PYTHON.md §3; nothing else may drift, and a
    sanity gate proves canonical_ir does NOT conflate distinct programs).

  EXECUTABLE EQUIVALENCE — exec(rendered source) agrees with ProgEval on
    the SAME inputs for the whole P2 semantic battery (result + the
    CPython original as the third witness) and for the synthesized suite.

  RENDER-GAP HONESTY — a variant with no rule (simulated by withholding
    ProgWhile at install) fires the established render_in_graph
    `render_gap:<head> in <language>` convention: an honest
    {"ok": False, "render_gaps": [...]} return, the agent._render_gaps
    question list, and a graph-resident deduped
    Impasse{reason:'render_gap'} node — not an exception, not silent None.

  RENDERABILITY REFUSALS — IR the rule set cannot honestly spell
    (f-string literal needing escapes, unknown aug op) is refused by name,
    never silently mis-rendered.

  DETERMINISM — rendering twice yields byte-identical source.

  P4 READ-OFF (end-to-end) — the real P4 pipeline's accepted max_of_two
    Program node renders (straight from the node, the Program{name,
    program} convention) to a runnable def whose exec matches ProgEval
    over the accepted ir_subgraph on held-out inputs, and the accepted IR
    round-trips through its own rendering.

Run (worktree engine discipline — the P1 note):
    PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest --confcutdir=. \
    tests/test_render_python_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import ast
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

from domains.prog_ir_emit import P1_VARIANT_SET, emit_prog_ir  # noqa: E402
from domains.render_python import (  # noqa: E402
    SEED_PATH, build_seed, canonical_ir, install_python_statement_renderer,
    load_seed, render_gap_check, render_ir, render_program,
    renderability_refusals)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read")


# ---------------------------------------------------------------------------
# engine guard (the P1 skip precedent — honest skip, never a fake pass)
# ---------------------------------------------------------------------------
def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval",
                           "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 5,
                           "field": ""}, {})
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
# mechanical helpers (the P2 gate conventions, reused)
# ---------------------------------------------------------------------------
def fixture_source(name: str) -> str:
    with open(os.path.join(FIXTURE_DIR, name + ".py")) as fh:
        return fh.read()


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


def canon_key(ir) -> str:
    return json.dumps(canonical_ir(ir), sort_keys=True)


def exec_def(source: str, name: str):
    g: dict = {}
    exec(compile(source, name + "_rendered.py", "exec"), g)  # noqa: S102
    return g[name]


OK_FIXTURES = ["arith_flow", "attr_record", "branchy", "comp_pipeline",
               "dotted_call", "fstring_is", "import_noop", "loop_ctl",
               "try_raise", "undeclared_extern", "unpack_containers",
               "while_gcd"]

# the P2 semantic battery (result-witness inputs), reused verbatim.
SEMANTIC_CASES = [
    ("arith_flow", {"a": 4, "b": 5}),
    ("arith_flow", {"a": 4, "b": 5, "k": 2}),
    ("branchy", {"x": 12, "name": "zed"}),
    ("branchy", {"x": 5, "name": ""}),
    ("branchy", {"x": -3, "name": "ann"}),
    ("loop_ctl", {"n": 10}),
    ("loop_ctl", {"n": 3}),
    ("while_gcd", {"a": 252, "b": 105}),
    ("unpack_containers", {"p": (3, 4)}),
    ("try_raise", {"x": -2}),
    ("try_raise", {"x": 6}),
    ("comp_pipeline", {"xs": (1, 2, 3, 4), "lo": 1}),
    ("fstring_is", {"v": None, "x": 7}),
    ("fstring_is", {"v": 3, "x": 7}),
    ("import_noop", {"z": 41}),
]

# P4-shape synthesized programs (the splice_binding ProgSeq[params, body…]
# artifact shape) — hand-built IR, never parsed from source, so the law is
# exercised on WRITE-side trees too.
_L = lambda v: {"type": "Lit", "value": v}                     # noqa: E731
_V = lambda n: {"type": "Var", "name": n}                      # noqa: E731
_P = lambda n, d=None: {"type": "ProgDefFnParam", "name": n,   # noqa: E731
                        "default": d}
_RET = lambda t: {"type": "ProgReturn", "value": t}            # noqa: E731

SYNTH_PROGRAMS = {
    "double_it": {"type": "ProgSeq", "stmts": [
        _P("a"), _RET({"type": "Plus", "items": [_V("a"), _V("a")]})]},
    "abs_diff": {"type": "ProgSeq", "stmts": [
        _P("a"), _P("b"),
        _RET({"type": "IfThenElse",
              "cond": {"type": "Gte", "a": _V("a"), "b": _V("b")},
              "then": {"type": "Minus", "a": _V("a"), "b": _V("b")},
              "other": {"type": "Minus", "a": _V("b"), "b": _V("a")}})]},
    "sum_of_list": {"type": "ProgSeq", "stmts": [
        _P("xs"),
        {"type": "ProgAssignVar", "name": "total", "value": _L(0)},
        {"type": "ProgForEach", "var": "x", "iter": _V("xs"),
         "body": {"type": "ProgAugAssign", "name": "total", "op": "add",
                  "value": _V("x")},
         "orelse": None},
        _RET(_V("total"))]},
    "clamp": {"type": "ProgSeq", "stmts": [
        _P("x"), _P("lo"), _P("hi"),
        {"type": "ProgIfStmt",
         "cond": {"type": "Lt", "a": _V("x"), "b": _V("lo")},
         "then": _RET(_V("lo")), "orelse": None},
        {"type": "ProgIfStmt",
         "cond": {"type": "Gt", "a": _V("x"), "b": _V("hi")},
         "then": _RET(_V("hi")), "orelse": None},
        _RET(_V("x"))]},
    "count_evens": {"type": "ProgSeq", "stmts": [
        _P("xs"),
        _RET({"type": "ProgCallExtern", "name": "len", "recv": None,
              "args": [{"type": "ProgComprehensionList", "var": "x",
                        "source": _V("xs"), "expr": _V("x"),
                        "cond": {"type": "Eq",
                                 "a": {"type": "Mod", "a": _V("x"),
                                       "b": _L(2)},
                                 "b": _L(0)}}]})]},
    "negate_or_default": {"type": "ProgSeq", "stmts": [
        _P("v", _L(None)),
        {"type": "ProgIfStmt",
         "cond": {"type": "ProgIsOp", "a": _V("v"), "b": _L(None),
                  "negated": False},
         "then": _RET({"type": "Neg", "arg": _L(1)}), "orelse": None},
        _RET({"type": "Neg", "arg": _V("v")})]},
}
SYNTH_INPUTS = {
    "double_it": [{"a": 7}, {"a": -2}],
    "abs_diff": [{"a": 3, "b": 9}, {"a": 9, "b": 3}],
    "sum_of_list": [{"xs": (2, 4, 6, 8, 10)}],
    "clamp": [{"x": 5, "lo": 0, "hi": 10}, {"x": -5, "lo": 0, "hi": 10},
              {"x": 15, "lo": 0, "hi": 10}],
    "count_evens": [{"xs": (1, 2, 3, 4, 6)}],
    "negate_or_default": [{"v": 4}, {}],
}
SYNTH_ORACLES = {"count_evens": ["len"]}


@pytest.fixture(scope="module")
def sub():
    """One installed substrate for the read-only render gates."""
    s = srs.Substrate()
    r = install_python_statement_renderer(s)
    assert r["skipped"] == []
    return s


def emit_fixture(name: str):
    r = emit_prog_ir(fixture_source(name), name=name)
    assert r["ok"], f"{name}: blockers={r.get('blockers')}"
    return r


def render_fixture(sub, name: str) -> str:
    r = emit_fixture(name)
    out = render_program(sub, r["ir"], name=name)
    assert out["ok"], (name, out)
    return out["source"]


# ---------------------------------------------------------------------------
# 1) SEED INTEGRITY
# ---------------------------------------------------------------------------
def test_seed_file_equals_builder_output():
    """The seed of record is the builder's output, byte-for-byte (JSON
    identity) — the two representations can never drift silently."""
    assert load_seed(SEED_PATH) == build_seed()


def test_seed_covers_every_p1_variant_and_the_expression_closure():
    heads = {r["head"] for r in load_seed()["render_rules"]}
    missing = {"Prog" + v for v in P1_VARIANT_SET} - heads
    assert missing == set(), f"P1 variants without a RenderRule: {missing}"
    # the P2 IR expression closure (PROGRAM_SYNTHESIS_P2_PYTHON.md §1)
    for h in ("Lit", "Var", "Plus", "Minus", "Times", "Div", "Mod", "Pow",
              "Neg", "Not", "Eq", "Lt", "Lte", "Gt", "Gte", "In",
              "IfThenElse", "And"):
        assert h in heads, f"expression head {h} missing"


def test_install_is_idempotent_per_head(sub):
    again = install_python_statement_renderer(sub)
    assert again["installed"] == []
    assert set(again["skipped"]) == {r["head"]
                                     for r in load_seed()["render_rules"]}


# ---------------------------------------------------------------------------
# 2) THE ROUND-TRIP LAW — every ok P2 fixture
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", OK_FIXTURES)
def test_round_trip_law_fixture(sub, name):
    """IR -> render -> ast.parse -> emit_prog_ir -> canonically identical
    IR (the documented canonicalization set; nothing else drifts)."""
    e1 = emit_fixture(name)
    source = render_fixture(sub, name)
    ast.parse(source)                       # real, parseable Python
    e2 = emit_prog_ir(source, name=name)
    assert e2["ok"], (name, e2.get("blockers"), source)
    assert canon_key(e1["ir"]) == canon_key(e2["ir"]), source
    # the extern surface survives the trip too (names verbatim)
    assert e2["externs"] == e1["externs"]


@pytest.mark.parametrize("name", sorted(SYNTH_PROGRAMS))
def test_round_trip_law_synthesized(sub, name):
    ir = SYNTH_PROGRAMS[name]
    out = render_program(sub, ir, name=name)
    assert out["ok"], out
    ast.parse(out["source"])
    e2 = emit_prog_ir(out["source"], name=name)
    assert e2["ok"], (name, e2.get("blockers"), out["source"])
    assert canon_key(ir) == canon_key(e2["ir"]), out["source"]


def test_canonicalization_does_not_conflate_distinct_programs():
    """'Nothing else drifts': canonical_ir is a comparison instrument, not
    a semantics eraser — distinct programs stay distinct."""
    a = {"type": "ProgSeq", "stmts": [_RET(_L(1))]}
    b = {"type": "ProgSeq", "stmts": [_RET(_L(2))]}
    assert canon_key(a) != canon_key(b)
    c = {"type": "ProgSeq", "stmts": [
        {"type": "ProgAssignVar", "name": "x", "value": _L(1)},
        _RET(_V("x"))]}
    d = {"type": "ProgSeq", "stmts": [_RET(_L(1))]}
    assert canon_key(c) != canon_key(d)
    # C2 flattens NESTED Seqs but never reorders / drops statements
    nested = {"type": "ProgSeq", "stmts": [
        {"type": "ProgSeq", "stmts": [c["stmts"][0]]}, c["stmts"][1]]}
    assert canon_key(nested) == canon_key(c)


def test_round_trip_with_docstring(sub):
    """A rendered docstring is peeled by the emitter (the P2 docstring
    peel), so the law holds with the docstring slot filled."""
    e1 = emit_fixture("while_gcd")
    out = render_program(sub, e1["ir"], name="while_gcd",
                         docstring="Euclid's gcd.")
    assert out["ok"]
    assert '"""Euclid\'s gcd."""' in out["source"]
    e2 = emit_prog_ir(out["source"], name="while_gcd")
    assert canon_key(e1["ir"]) == canon_key(e2["ir"])


# ---------------------------------------------------------------------------
# 3) EXECUTABLE EQUIVALENCE — exec(rendered) ≡ ProgEval ≡ CPython original
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,inputs", SEMANTIC_CASES,
                         ids=[f"{n}-{i}" for i, (n, _) in
                              enumerate(SEMANTIC_CASES)])
def test_exec_equivalence(sub, name, inputs):
    e = emit_fixture(name)
    source = render_fixture(sub, name)
    rendered_fn = exec_def(source, name)
    original_fn = exec_def(fixture_source(name), name)
    got = rendered_fn(**dict(inputs))
    assert norm(got) == norm(original_fn(**dict(inputs)))
    pe = run_prog_eval(sub, e["ir"], env=dict(inputs),
                       oracles=e["native_oracles"])
    assert pe["trap"] is None and pe["halted"] is True
    assert norm(pe["result"]) == norm(got)


def test_exec_equivalence_attr_record(sub):
    """The record convention: rendered source runs on a real object twin;
    ProgEval runs the dict-record — results agree (the P2 twin gate)."""
    e = emit_fixture("attr_record")
    source = render_fixture(sub, "attr_record")
    got = exec_def(source, "attr_record")(types.SimpleNamespace(), 3)
    pe = run_prog_eval(sub, e["ir"], env={"r": {}, "k": 3})
    assert pe["trap"] is None and got == pe["result"] == 12


@pytest.mark.parametrize("name", sorted(SYNTH_PROGRAMS))
def test_exec_equivalence_synthesized(sub, name):
    ir = SYNTH_PROGRAMS[name]
    out = render_program(sub, ir, name=name)
    fn = exec_def(out["source"], name)
    for env in SYNTH_INPUTS[name]:
        pe = run_prog_eval(sub, ir, env=dict(env) or None,
                           oracles=SYNTH_ORACLES.get(name, ()))
        assert pe["trap"] is None, (name, env, pe)
        assert norm(fn(**env)) == norm(pe["result"])


# ---------------------------------------------------------------------------
# 4) DETERMINISM
# ---------------------------------------------------------------------------
def test_render_is_deterministic(sub):
    for name in ("arith_flow", "branchy", "unpack_containers"):
        e = emit_fixture(name)
        s1 = render_program(sub, e["ir"], name=name)["source"]
        s2 = render_program(sub, e["ir"], name=name)["source"]
        assert s1 == s2


# ---------------------------------------------------------------------------
# 5) RENDER-GAP HONESTY — the established render_in_graph convention
# ---------------------------------------------------------------------------
def test_render_gap_fires_the_established_convention():
    s = srs.Substrate()
    install_python_statement_renderer(s, skip_heads={"ProgWhile"})
    e = emit_fixture("while_gcd")
    out = render_program(s, e["ir"], name="while_gcd")
    # honest structured refusal — not an exception, not silent None
    assert out == {"ok": False,
                   "render_gaps": ["render_gap:ProgWhile in python"]}
    # the question list (the drain_all_taught_threads teacher channel)
    assert getattr(s, "_render_gaps") == ["render_gap:ProgWhile in python"]
    # the graph-resident Impasse node, exact render_in_graph attrs, deduped
    imps = [s.node(i)["attrs"] for i in s.nodes("Impasse")]
    assert imps == [{"reason": "render_gap",
                     "render_gap_head": "ProgWhile",
                     "render_gap_lang": "python",
                     "question": "render_gap:ProgWhile in python"}]
    render_program(s, e["ir"], name="while_gcd")     # again: no duplicates
    assert len(s.nodes("Impasse")) == 1
    assert s._render_gaps == ["render_gap:ProgWhile in python"]
    # heads that ARE installed still render on this substrate
    assert render_program(s, emit_fixture("branchy")["ir"],
                          name="branchy")["ok"]


def test_gap_heals_by_installing_the_missing_rule():
    """The teach-seam shape: install the withheld rule -> the SAME IR now
    renders (the render-gap -> teach -> re-render loop's mechanical half)."""
    s = srs.Substrate()
    install_python_statement_renderer(s, skip_heads={"ProgWhile"})
    e = emit_fixture("while_gcd")
    assert render_program(s, e["ir"], name="while_gcd")["ok"] is False
    install_python_statement_renderer(s)      # fills exactly the gap
    out = render_program(s, e["ir"], name="while_gcd")
    assert out["ok"], out
    assert exec_def(out["source"], "while_gcd")(252, 105) == 21


# ---------------------------------------------------------------------------
# 6) RENDERABILITY REFUSALS — refused by name, never silently mis-rendered
# ---------------------------------------------------------------------------
def test_fstring_literal_needing_escapes_is_refused(sub):
    ir = {"type": "ProgSeq", "stmts": [
        _RET({"type": "ProgFString",
              "parts": [_L('has "quote" and {brace}'), _V("x")]})]}
    assert renderability_refusals(ir) == ["fstring_literal_unspellable"]
    out = render_program(sub, ir, name="f")
    assert out == {"ok": False, "refusals": ["fstring_literal_unspellable"]}


def test_unknown_aug_op_is_refused(sub):
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgAugAssign", "name": "x", "op": "matmul",
         "value": _L(1)}]}
    out = render_program(sub, ir, name="f")
    assert out == {"ok": False, "refusals": ["aug_op_unknown:matmul"]}


# ---------------------------------------------------------------------------
# 7) P4 READ-OFF — the accepted Program artifact renders and runs
# ---------------------------------------------------------------------------
def _p4_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(
            {"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
             "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
             "wild_objects": False}, {"g": [["p", "x"]]})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


@pytest.mark.skipif(not _p4_live(), reason="ShapeDecode absent — the P4 "
                    "loop cannot run on this engine. Honest skip.")
def test_p4_accepted_program_renders_to_a_runnable_def():
    from domains import prog_synthesis as psy
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    r = psy.synthesize_from_request(
        s, ag, "write a function max_of_two that returns the larger of "
               "two numbers",
        [({"a": 3, "b": 9}, 9), ({"a": 7, "b": 2}, 7),
         ({"a": -1, "b": -4}, -1)])
    assert r["status"] == "accepted" and r["program"] is not None
    install_python_statement_renderer(s)
    # straight from the Program NODE (the Program{name, program} convention)
    out = render_program(s, r["program"])
    assert out["ok"] and out["name"] == "max_of_two"
    fn = exec_def(out["source"], "max_of_two")
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert len(roots) == 1
    for env in ({"a": 11, "b": 5}, {"a": -3, "b": 4}, {"a": 0, "b": 0}):
        pe = s._inner.evaluate(
            {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
             "env": {"type": "Var", "name": "e"}, "oracles": None,
             "fuel": 10_000, "field": ""}, {"e": dict(env), "p": roots[0]})
        assert pe["trap"] is None and pe["halted"] is True
        assert fn(**env) == pe["result"]
    # the accepted IR obeys the round-trip law through its own rendering
    ir = json.loads(s.node(r["program"])["attrs"]["program"])
    e2 = emit_prog_ir(out["source"], name="max_of_two")
    assert e2["ok"] and canon_key(ir) == canon_key(e2["ir"])


# ---------------------------------------------------------------------------
# 8) statement-grain indentation is graph-side (the registered hard bit)
# ---------------------------------------------------------------------------
def test_indentation_is_threaded_graph_side(sub):
    """Nested blocks indent 0/4/8/12 via the Let-threaded indent binding;
    render_ir at a nonzero base indent shifts uniformly — no Python
    depth-walker anywhere on the path."""
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgForEach", "var": "i", "iter": _V("xs"),
         "body": {"type": "ProgIfStmt", "cond": _V("i"),
                  "then": {"type": "ProgForEach", "var": "j",
                           "iter": _V("i"),
                           "body": {"type": "ProgAssignVar", "name": "t",
                                    "value": _V("j")},
                           "orelse": None},
                  "orelse": None},
         "orelse": None}]}
    assert render_ir(sub, ir) == (
        "for i in xs:\n"
        "    if i:\n"
        "        for j in i:\n"
        "            t = j")
    shifted = render_ir(sub, ir, indent="        ")
    # first-line-unindented contract; inner lines carry base + own depth
    assert shifted == (
        "for i in xs:\n"
        "            if i:\n"
        "                for j in i:\n"
        "                    t = j")
