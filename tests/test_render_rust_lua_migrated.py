"""test_render_rust_lua_migrated — P5 track B gates: statement-grain RUST +
LUA rendering of the hub Program IR as graph-resident RenderRules
(PROGRAM_SYNTHESIS_PLAN.md §4-P5, PREREG §7; seeds/render_rust_statements.json
+ seeds/render_lua_statements.json via domains/render_rust_lua.py).

Gates:

  ROUND-TRIP LAW — for every ok P2 fixture (tests/fixtures/prog_ir_read_rs_lua):
    read -> hub IR -> render -> tree-sitter re-read -> BYTE-IDENTICAL IR JSON
    (zero canonicalization deltas needed on this corpus; the deltas that CAN
    occur are enumerated in PROGRAM_SYNTHESIS_P5_RUST_LUA.md's ledgers).

  TOOLCHAIN TRUTH — every rendered fixture compiles with rustc AND runs
    printing the P2-pinned expected outputs; rendered lua runs under BOTH
    lua5.4 and luajit with the pinned outputs (subprocess runs are admissible
    world I/O in tests; one batched compile/run per toolchain).

  CROSS-FRAME HEADLINE — the P4-accepted max_of_two + sum_of_list Programs
    (produced live by the synthesis pipeline) render to BOTH rust and lua,
    compile/run, and agree with ProgEval on held-out inputs: one graph
    program, three executable surfaces (python is the sibling track's).

  RENDER-GAP HONESTY — a head with no RenderRule renders {ok: False, gaps:
    [head]} and files a graph-resident Impasse (`render_gap:<head> in
    <lang>`), deduped; an engine-level template guard (non-list container)
    gaps honestly too.

  TEACH LOOP (the living-proof gate) — statement-grain lua rules acquired
    LIVE through the standing render-gap -> self-teacher ->
    install_render_rule loop (tests/test_teach_lua_renderer_migrated.py
    precedent) on a fresh WorldAdapter with NO seeded renderer: the taught
    renderer emits runnable lua (verified under lua5.4). The measured
    boundary: canonical statement templates that need IfThenElse /
    ToJsonString / TypeOf / AttrByName exceed `_spec_to_renderer_term`'s
    grammar (KeyError) — those rules ship as seed data; the delta is
    recorded per-rule in the seeds (`teachable` / `teach_spec`).

  DETERMINISM — rendering twice is byte-identical.

Run (worktree engine discipline):
    pytest tests/test_render_rust_lua_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read_rs_lua")


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval",
                           "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 10, "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip("ProgEval Term not present in the installed substrate_rs binary — "
                "rebuild runners/dsl. Honest skip.", allow_module_level=True)

try:
    import tree_sitter_lua  # noqa: F401
    import tree_sitter_rust  # noqa: F401
except ImportError:
    pytest.skip("tree_sitter_rust / tree_sitter_lua not installed — honest skip.",
                allow_module_level=True)

from domains import prog_ir_lua, prog_ir_rust  # noqa: E402
from domains import render_rust_lua as rl  # noqa: E402

_READER = {"rust": prog_ir_rust, "lua": prog_ir_lua}


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
def _fixture(lang: str, name: str) -> str:
    ext = {"rust": ".rs", "lua": ".lua"}[lang]
    with open(os.path.join(FIX, lang, name + ext)) as f:
        return f.read()


def read_fixture(lang: str, name: str) -> dict:
    return _READER[lang].read_function(srs.Substrate(), _fixture(lang, name))


def render_fixture(lang: str, name: str) -> dict:
    rec = read_fixture(lang, name)
    assert rec["ok"], f"read blockers: {rec['blockers']}"
    out = rl.render_function(srs.Substrate(), rec, lang)
    assert out["ok"], f"render gaps: {out['gaps']}"
    return {"rec": rec, "source": out["source"]}


def _need(exe: str):
    if shutil.which(exe) is None:
        pytest.skip(f"{exe} not on PATH — honest skip (toolchain truth needs it)")


def _run(cmd, timeout=120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


# The ok-fixture corpora + the P2-pinned toolchain expectations
# (PROGRAM_SYNTHESIS_P2_RUST_LUA.md §5 transcript; re-verified here live).
RUST_OK = ["abs_diff", "count_matching", "extern_trap", "loop_break",
           "max_of_two", "sum_list", "sum_range", "vec_index", "while_countdown"]
LUA_OK = ["bool_and", "concat", "count_matching", "extern_trap", "for_step",
          "max_of_two", "repeat_until", "sum_list", "table_index", "while_countdown"]

# (fixture, call-expression, expected stdout line). extern_trap is excluded
# from toolchain runs (its callee is deliberately undeclared) but round-trips.
RUST_CASES = [
    ("max_of_two", "max_of_two(7, 3)", "7"),
    ("max_of_two", "max_of_two(2, 5)", "5"),
    ("sum_list", "sum_list(vec![1, 2, 3, 4])", "10"),
    ("count_matching", "count_matching(vec![1, 2, 2, 3, 2], 2)", "3"),
    ("sum_range", "sum_range(5)", "10"),
    ("while_countdown", "while_countdown(6)", "6"),
    ("loop_break", "loop_break(4)", "4"),
    ("abs_diff", "abs_diff(3, 9)", "6"),
    ("abs_diff", "abs_diff(9, 3)", "6"),
    ("vec_index", "vec_index()", "16"),
]
LUA_CASES = [
    ("max_of_two", "max_of_two(7, 3)", "7"),
    ("max_of_two", "max_of_two(2, 5)", "5"),
    ("sum_list", "sum_list({1, 2, 3, 4})", "10"),
    ("count_matching", "count_matching({1, 2, 2, 3, 2}, 2)", "3"),
    ("while_countdown", "while_countdown(6)", "6"),
    ("repeat_until", "repeat_until(4)", "4"),
    ("repeat_until", "repeat_until(0)", "1"),
    ("concat", 'concat("x", "y")', "x-y"),
    ("for_step", "for_step(7)", "16"),
    ("for_step", "for_step(6)", "9"),
    ("table_index", "table_index()", "20"),
    ("bool_and", "bool_and(2, 3)", "1"),
    ("bool_and", "bool_and(2, -1)", "0"),
]


# ---------------------------------------------------------------------------
# 1) ROUND-TRIP LAW — IR -> render -> tree-sitter read -> identical IR.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang,name",
                         [("rust", n) for n in RUST_OK] + [("lua", n) for n in LUA_OK],
                         ids=[f"rust-{n}" for n in RUST_OK] + [f"lua-{n}" for n in LUA_OK])
def test_round_trip_is_byte_identical(lang, name):
    r = render_fixture(lang, name)
    rec2 = _READER[lang].read_function(srs.Substrate(), r["source"])
    assert rec2["ok"], (f"re-read blocked: {rec2['blockers']}\n--- rendered:\n"
                        f"{r['source']}")
    assert (json.dumps(r["rec"]["ir"], sort_keys=True)
            == json.dumps(rec2["ir"], sort_keys=True)), (
        f"round-trip IR drifted on {lang}/{name}\n--- rendered:\n{r['source']}")
    assert [p["name"] for p in r["rec"]["params"]] \
        == [p["name"] for p in rec2["params"]]


# ---------------------------------------------------------------------------
# 2) TOOLCHAIN TRUTH — rendered source compiles/runs with pinned outputs.
# ---------------------------------------------------------------------------
def test_rendered_rust_compiles_and_runs_pinned():
    _need("rustc")
    fns = {n: render_fixture("rust", n)["source"]
           for n in sorted({c[0] for c in RUST_CASES})}
    main = ("fn main() {\n"
            + "\n".join('    println!("{}", %s);' % call for _, call, _ in RUST_CASES)
            + "\n}\n")
    src = "\n\n".join(fns.values()) + "\n\n" + main
    with tempfile.TemporaryDirectory() as d:
        rs = os.path.join(d, "batch.rs")
        with open(rs, "w") as f:
            f.write(src)
        exe = os.path.join(d, "batch")
        cp = _run(["rustc", "-O", "-o", exe, rs])
        assert cp.returncode == 0, f"rustc rejected the render:\n{cp.stderr}\n{src}"
        out = _run([exe], timeout=30)
        assert out.returncode == 0, out.stderr
        assert out.stdout.split() == [e for _, _, e in RUST_CASES], (
            f"toolchain truth failed: {out.stdout.split()} != expected")


@pytest.mark.parametrize("exe", ["lua5.4", "luajit"])
def test_rendered_lua_runs_pinned(exe):
    _need(exe)
    fns = {n: render_fixture("lua", n)["source"]
           for n in sorted({c[0] for c in LUA_CASES})}
    script = ("\n\n".join(fns.values()) + "\n\n"
              + "\n".join("print(%s)" % call for _, call, _ in LUA_CASES) + "\n")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "batch.lua")
        with open(p, "w") as f:
            f.write(script)
        out = _run([exe, p], timeout=30)
        assert out.returncode == 0, f"{exe} rejected the render:\n{out.stderr}\n{script}"
        assert out.stdout.splitlines() == [e for _, _, e in LUA_CASES]


# ---------------------------------------------------------------------------
# 3) CROSS-FRAME HEADLINE — P4 accepted Programs -> rust + lua -> toolchains
# agree with ProgEval on held-out inputs.
# ---------------------------------------------------------------------------
def _shape_decode_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                           "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                           "wild_objects": False}, {"g": [["p", "x"]]})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


def _accept(text, rows):
    from domains import prog_synthesis as psy
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    m = psy.ingest_spec(s, ag, text, rows)
    psy.pump(s, ag)
    r = psy.read_goal(s, s.in_neighbours(m, "about_message")[0])
    assert r["status"] == "accepted", f"P4 pipeline did not accept: {r['status']}"
    return s, r


def _prog_eval(ir, env):
    s = srs.Substrate()
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": ir, "env": {"type": "Var", "name": "e"},
         "oracles": None, "fuel": 10000, "field": ""}, {"e": env})
    assert out["trap"] is None and out["halted"] is True, out
    return out["result"]


def test_cross_frame_headline_one_program_three_surfaces():
    """The P4-accepted max_of_two + sum_of_list Programs render to BOTH rust
    and lua, compile/run under the real toolchains, and agree with ProgEval
    on held-out inputs (never in the spec rows)."""
    if not _shape_decode_live():
        pytest.skip("ShapeDecode not in installed binary — honest skip.")
    _need("rustc")
    _need("lua5.4")
    _need("luajit")
    _s1, rmax = _accept(
        "write a function max_of_two that returns the larger of two numbers",
        [({"a": 2, "b": 9}, 9), ({"a": 7, "b": 3}, 7), ({"a": 4, "b": 4}, 4)])
    _s2, rsum = _accept(
        "write a function sum_of_list that returns the tally of a list of numbers",
        [({"items": [1, 2, 3, 4]}, 10), ({"items": [5]}, 5), ({"items": []}, 0)])

    held_out = [
        ("max_of_two", rmax["ir"], {"a": 11, "b": 5}, "max_of_two(11, 5)"),
        ("max_of_two", rmax["ir"], {"a": -3, "b": 4}, "max_of_two(-3, 4)"),
        ("sum_of_list", rsum["ir"], {"items": (2, 4, 6, 8, 10)},
         None),  # per-frame list spelling below
    ]
    expected = [str(_prog_eval(ir, dict(env)))
                for _, ir, env, _ in held_out]

    rust_fns = {n: rl.render_function(srs.Substrate(), ir, "rust", name=n)
                for n, ir in (("max_of_two", rmax["ir"]), ("sum_of_list", rsum["ir"]))}
    lua_fns = {n: rl.render_function(srs.Substrate(), ir, "lua", name=n)
               for n, ir in (("max_of_two", rmax["ir"]), ("sum_of_list", rsum["ir"]))}
    for n, o in list(rust_fns.items()) + list(lua_fns.items()):
        assert o["ok"], f"{n} render gapped: {o['gaps']}"

    with tempfile.TemporaryDirectory() as d:
        rs = os.path.join(d, "cross.rs")
        with open(rs, "w") as f:
            f.write(rust_fns["max_of_two"]["source"] + "\n\n"
                    + rust_fns["sum_of_list"]["source"] + "\n\n"
                    + "fn main() {\n"
                      '    println!("{}", max_of_two(11, 5));\n'
                      '    println!("{}", max_of_two(-3, 4));\n'
                      '    println!("{}", sum_of_list(vec![2, 4, 6, 8, 10]));\n'
                      "}\n")
        exe = os.path.join(d, "cross")
        cp = _run(["rustc", "-O", "-o", exe, rs])
        assert cp.returncode == 0, cp.stderr
        out = _run([exe], timeout=30)
        assert out.stdout.split() == expected, (
            f"rust surface disagrees with ProgEval: {out.stdout.split()} != {expected}")

        lua_path = os.path.join(d, "cross.lua")
        with open(lua_path, "w") as f:
            f.write(lua_fns["max_of_two"]["source"] + "\n\n"
                    + lua_fns["sum_of_list"]["source"] + "\n\n"
                    + "print(max_of_two(11, 5))\n"
                      "print(max_of_two(-3, 4))\n"
                      "print(sum_of_list({2, 4, 6, 8, 10}))\n")
        for lua_exe in ("lua5.4", "luajit"):
            out = _run([lua_exe, lua_path], timeout=30)
            assert out.returncode == 0, out.stderr
            assert out.stdout.splitlines() == expected, (
                f"{lua_exe} surface disagrees with ProgEval: "
                f"{out.stdout.splitlines()} != {expected}")


# ---------------------------------------------------------------------------
# 4) RENDER-GAP HONESTY — missing rule -> gap FILED, never a partial render.
# ---------------------------------------------------------------------------
_TRYOR_IR = {"type": "ProgSeq", "stmts": [
    {"type": "ProgTryOr",
     "body": {"type": "ProgReturn", "value": {"type": "Lit", "value": 1}},
     "exc_var": "", "handler": None}]}


@pytest.mark.parametrize("lang", ["rust", "lua"])
def test_missing_rule_files_a_render_gap(lang):
    sub = srs.Substrate()
    out = rl.render_function(sub, _TRYOR_IR, lang, name="f")
    assert out["ok"] is False
    assert out["source"] is None, "a gapped render must NEVER hand back source"
    assert "ProgTryOr" in out["gaps"]
    imps = [n for n in sub.nodes("Impasse")
            if sub.node(n)["attrs"].get("render_gap_head") == "ProgTryOr"
            and sub.node(n)["attrs"].get("render_gap_lang") == lang]
    assert len(imps) == 1, "the gap must land as ONE graph-resident Impasse"
    assert sub.node(imps[0])["attrs"]["question"] == f"render_gap:ProgTryOr in {lang}"
    # dedup: rendering again files nothing new.
    rl.render_function(sub, _TRYOR_IR, lang, name="f")
    imps2 = [n for n in sub.nodes("Impasse")
             if sub.node(n)["attrs"].get("render_gap_head") == "ProgTryOr"
             and sub.node(n)["attrs"].get("render_gap_lang") == lang]
    assert len(imps2) == 1


@pytest.mark.parametrize("lang", ["rust", "lua"])
def test_declared_gap_heads_have_no_rule(lang):
    """The seed's own render_gaps list is honest: every listed head really
    lacks a rule (the per-frame gap LIST the prereg asks for lives in the
    seed manifests — ownership keeps it out of results/)."""
    seed = rl.load_render_seed(lang)
    rule_heads = {r["head"] for r in seed["render_rules"]}
    for h in seed["render_gaps"]:
        assert h not in rule_heads, f"{h} is declared a gap but has a rule"


def test_engine_level_guard_gaps_on_non_list_container():
    """A template guard (ContainerLit kind != list) yields an engine-level
    gap — honest None, filed, never a wrong render."""
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgReturn",
         "value": {"type": "ProgContainerLit", "kind": "dict", "items": []}}]}
    sub = srs.Substrate()
    out = rl.render_function(sub, ir, "rust", name="f")
    assert out["ok"] is False
    assert out["source"] is None


# ---------------------------------------------------------------------------
# 5) THE SEED IS GRAPH DATA — Language + RenderRule + template subgraphs.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["rust", "lua"])
def test_renderer_is_graph_resident(lang):
    sub = srs.Substrate()
    lang_node = rl.install_renderer(sub, lang)
    seed = rl.load_render_seed(lang)
    rules = list(sub._inner.neighbours(lang_node, "has_rule"))
    assert len(rules) == len(seed["render_rules"])
    heads = set()
    for r in rules:
        attrs = sub.node(r)["attrs"]
        heads.add(attrs["head"])
        tmpl = list(sub._inner.neighbours(r, "template"))
        assert len(tmpl) == 1, "every RenderRule carries ONE template subgraph"
    assert heads == {r["head"] for r in seed["render_rules"]}
    # idempotent: installing again adds nothing.
    rl.install_renderer(sub, lang)
    assert len(list(sub._inner.neighbours(lang_node, "has_rule"))) == len(rules)


# ---------------------------------------------------------------------------
# 6) LITERALS — the old rust renderer's integer-only gap is CLOSED.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang,value,expected", [
    ("rust", True, "true"), ("rust", False, "false"),
    ("rust", 7, "7"), ("rust", 1.5, "1.5"), ("rust", 2.0, "2.0"),
    ("rust", "hi", '"hi"'),
    ("lua", True, "true"), ("lua", False, "false"),
    ("lua", 7, "7"), ("lua", 1.5, "1.5"), ("lua", "x-y", '"x-y"'),
], ids=lambda v: repr(v) if not isinstance(v, str) or len(v) < 8 else v[:8])
def test_literal_spelling_is_type_aware(lang, value, expected):
    out = rl.render_body(srs.Substrate(), {"type": "Lit", "value": value}, lang)
    assert out["ok"]
    assert out["text"] == expected


# ---------------------------------------------------------------------------
# 7) DETERMINISM.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang,name", [("rust", "count_matching"), ("rust", "loop_break"),
                                       ("lua", "sum_list"), ("lua", "repeat_until")],
                         ids=["rust-count", "rust-loop", "lua-sum", "lua-repeat"])
def test_render_is_deterministic(lang, name):
    a = render_fixture(lang, name)["source"]
    b = render_fixture(lang, name)["source"]
    assert a == b


# ---------------------------------------------------------------------------
# 8) THE TEACH LOOP — statement-grain rules taught LIVE (the Lua precedent,
# one level up), plus the measured spec-grammar boundary.
# ---------------------------------------------------------------------------
def test_lua_statement_rules_taught_live_through_the_loop():
    """Fresh WorldAdapter, NO seeded renderer: the while_countdown fixture's
    statement IR renders only after the render-gap -> self-teacher ->
    install_render_rule loop absorbs the teachable rule set — and the taught
    renderer's output RUNS under lua5.4. Statement grain through the SAME
    loop that taught the original expression-grain Lua renderer."""
    _need("lua5.4")
    from substrate.world_adapter import WorldAdapter

    rec = read_fixture("lua", "while_countdown")
    assert rec["ok"]

    specs = rl.teachable_specs("lua")
    asked = []

    def teacher(q):
        m = re.search(r"render_gap:(\w+) in lua", q)
        if m is None:
            return None
        asked.append(m.group(1))
        spec = specs.get(m.group(1))
        if spec is None:
            return None
        return {"answer": None, "learn": [{"rule": spec}]}

    wa = WorldAdapter()
    wa.set_self_teacher(teacher)
    out = rl.render_via_teach_loop(wa, rec, "lua")
    assert out["ok"], f"teach loop never converged; last gaps: {out['gaps']}"

    # statement-grain heads arrived THROUGH the loop.
    assert {"ProgSeq", "ProgWhile", "ProgAssignVar", "ProgReturn"} <= set(asked)

    # the taught rules are graph data on the Language node.
    lua = wa.language("lua")
    assert lua is not None
    heads = {wa.s.node(r)["attrs"]["head"]
             for r in wa.inner.neighbours(lua, "has_rule")}
    assert {"ProgSeq", "ProgWhile", "ProgAssignVar", "ProgReturn"} <= heads

    # toolchain truth for the TAUGHT renderer.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "taught.lua")
        with open(p, "w") as f:
            f.write(out["source"] + "\nprint(while_countdown(6))\n")
        run = _run(["lua5.4", p], timeout=30)
        assert run.returncode == 0, run.stderr
        assert run.stdout.strip() == "6"


def test_teach_spec_grammar_boundary_is_measured():
    """The measured delta: every seed rule marked teachable converts through
    the adapter's _spec_to_renderer_term; the canonical statement templates
    that branch (IfThenElse) or spell literals (ToJsonString) are BEYOND the
    teach grammar — KeyError, so those rules must ship as seed data. This is
    the honest boundary of 'the writer arrives through the loop'."""
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=()) if _wa_accepts_empty_seeds() else WorldAdapter()
    for lang in ("rust", "lua"):
        for head, spec in rl.teachable_specs(lang).items():
            wa._spec_to_renderer_term(spec["template"])  # must not raise
    with pytest.raises(KeyError):
        wa._spec_to_renderer_term(["IfThenElse", ["Slot", "decl"],
                                   ["Cat"], ["Cat"]])
    with pytest.raises(KeyError):
        wa._spec_to_renderer_term(["ToJsonString", ["Slot", "value"]])


def _wa_accepts_empty_seeds() -> bool:
    import inspect
    from substrate.world_adapter import WorldAdapter
    try:
        return "seeds" in inspect.signature(WorldAdapter.__init__).parameters
    except (TypeError, ValueError):
        return False
