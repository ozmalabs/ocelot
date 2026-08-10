"""test_prog_read_rust_lua_migrated — P2 gates for READING Rust + Lua into
the hub Program IR (PROGRAM_SYNTHESIS_PLAN.md §4-P2, PREREG §4; Rust+Lua
track). Companion to the P1 gates in tests/test_prog_ir_migrated.py.

Gates:

  FIXTURE CORPUS — ~10 rust + ~12 lua small functions
    (tests/fixtures/prog_ir_read_rs_lua/) covering the in-scope
    construction families; each is parsed by the mechanical tree-sitter
    world adapter (domains/ts_ingest), folded into hub IR by APPLYING the
    correspondence SEED (seeds/rust_correspondence.json /
    seeds/lua_correspondence.json via the table walkers), ProgEval'd on
    pinned inputs, and asserted against EXPECTED OUTPUTS verified
    out-of-band with the REAL toolchains (rustc 1.x -O, lua5.4 AND luajit
    — all present in this env; the verification transcript is recorded in
    PROGRAM_SYNTHESIS_P2_RUST_LUA.md §5).

  HONEST RESIDUAL — an out-of-scope construct per language (rust `match`,
    lua varargs / keyed-table part) reads as {ok: False, blockers: [...]}
    with the blocking cst kinds NAMED — never a silent partial emit.

  UNDECLARED-EXTERN TRAP — a call to an undeclared function emits fine
    and TRAPS at ProgEval (`extern:<name>`, halted False, no value) — the
    P1 oracle contract crossing the language frames unchanged.

  CROSS-FRAME LAW (the headline) — a semantically-identical function
    written in rust, lua, and python emits IR that ProgEval evaluates to
    the SAME result on the same inputs (three triples: max-of-two,
    sum-of-list-loop, count-matching). The python side uses the P2-Python
    track's domains/prog_ir_emit.py (present at run time).

  DETERMINISM — emitting a fixture twice (fresh substrates) yields
    byte-identical IR JSON.

  SEED LOADABILITY — both correspondence seeds load via the Rust
    load_seed_manifest with NO skipped rules/reflexes (the loader's
    warning channels) and land their CorrespondenceRow nodes.

  SOURCE-UPLOAD ROUTING — file_ingest classifies .py/.rs/.lua as
    `source`; an uploaded .lua file lands as CST graph + register facts +
    a graph-resident (reflected) hub-IR subgraph that ProgEval can run —
    not opaque metadata. Plain-text uploads are byte-unaffected
    (tests/test_file_ingest.py holds alongside).

Run (worktree engine discipline — the P1 note):
    pytest tests/test_prog_read_rust_lua_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs

FIX = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read_rs_lua")


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval", "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 10, "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip(
        "ProgEval Term not present in the installed substrate_rs binary — "
        "rebuild runners/dsl. Honest skip, not a fake pass.",
        allow_module_level=True)

try:
    import tree_sitter_lua  # noqa: F401
    import tree_sitter_rust  # noqa: F401
except ImportError:
    pytest.skip("tree_sitter_rust / tree_sitter_lua not installed — honest skip.",
                allow_module_level=True)


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
def _fixture(lang: str, name: str) -> str:
    ext = {"rust": ".rs", "lua": ".lua"}[lang]
    with open(os.path.join(FIX, lang, name + ext)) as f:
        return f.read()


def read_fixture(lang: str, name: str) -> dict:
    """Fresh substrate per read — determinism is a gate, not an accident."""
    from domains import prog_ir_lua, prog_ir_rust
    sub = srs.Substrate()
    reader = prog_ir_rust if lang == "rust" else prog_ir_lua
    return sub, reader.read_function(sub, _fixture(lang, name))


def run_prog(sub, prog, env=None, oracles=(), fuel=5000):
    L = lambda v: {"type": "Lit", "value": v}  # noqa: E731
    oc = None
    if oracles:
        items = []
        for o in oracles:
            items += [L(o), L("builtin")]
        oc = {"type": "MkDict", "items": items}
    envd = {"type": "Var", "name": "envd"} if env is not None else None
    out = sub._inner.evaluate(
        {"type": "ProgEval", "prog": prog, "env": envd, "oracles": oc,
         "fuel": fuel, "field": ""},
        {"envd": env} if env is not None else None)
    assert isinstance(out, dict)
    return out


def assert_runs_to(sub, ir, env, expected, oracles=()):
    out = run_prog(sub, ir, env=env, oracles=oracles)
    assert out["trap"] is None, f"unexpected trap: {out['trap']}"
    assert out["halted"] is True
    assert out["result"] == expected, (
        f"result {out['result']!r} != expected {expected!r} (toolchain-verified)")
    return out


# ---------------------------------------------------------------------------
# 1) FIXTURE CORPUS — expected values verified out-of-band (rustc / lua5.4 /
# luajit; transcript in PROGRAM_SYNTHESIS_P2_RUST_LUA.md §5).
# ---------------------------------------------------------------------------
RUST_CASES = [
    ("max_of_two", {"a": 7, "b": 3}, (), 7),
    ("max_of_two", {"a": 2, "b": 5}, (), 5),
    ("sum_list", {"xs": (1, 2, 3, 4)}, (), 10),
    ("count_matching", {"xs": (1, 2, 2, 3, 2), "t": 2}, (), 3),
    ("sum_range", {"n": 5}, ("range",), 10),
    ("while_countdown", {"n": 6}, (), 6),
    ("loop_break", {"n": 4}, ("range",), 4),
    ("abs_diff", {"a": 3, "b": 9}, (), 6),
    ("abs_diff", {"a": 9, "b": 3}, (), 6),
    ("vec_index", {}, (), 16),
]

LUA_CASES = [
    ("max_of_two", {"a": 7, "b": 3}, (), 7),
    ("max_of_two", {"a": 2, "b": 5}, (), 5),
    ("sum_list", {"xs": (1, 2, 3, 4)}, (), 10),
    ("count_matching", {"xs": (1, 2, 2, 3, 2), "t": 2}, ("range", "len"), 3),
    ("while_countdown", {"n": 6}, (), 6),
    ("repeat_until", {"n": 4}, (), 4),
    ("repeat_until", {"n": 0}, (), 1),   # repeat runs the body at least once
    ("concat", {"a": "x", "b": "y"}, (), "x-y"),
    ("for_step", {"n": 7}, ("range",), 16),
    ("for_step", {"n": 6}, ("range",), 9),   # inclusive-stop shift, odd grid
    ("table_index", {}, (), 20),             # 1-based -> 0-based shift
    ("bool_and", {"a": 2, "b": 3}, (), 1),
    ("bool_and", {"a": 2, "b": -1}, (), 0),
]


@pytest.mark.parametrize("name,env,oracles,expected",
                         RUST_CASES, ids=[f"{c[0]}-{i}" for i, c in enumerate(RUST_CASES)])
def test_rust_fixture_reads_and_runs(name, env, oracles, expected):
    sub, r = read_fixture("rust", name)
    assert r["ok"], f"blockers: {r['blockers']}"
    assert r["blockers"] == []
    assert_runs_to(sub, r["ir"], env or None, expected, oracles)


@pytest.mark.parametrize("name,env,oracles,expected",
                         LUA_CASES, ids=[f"{c[0]}-{i}" for i, c in enumerate(LUA_CASES)])
def test_lua_fixture_reads_and_runs(name, env, oracles, expected):
    sub, r = read_fixture("lua", name)
    assert r["ok"], f"blockers: {r['blockers']}"
    assert r["blockers"] == []
    assert_runs_to(sub, r["ir"], env or None, expected, oracles)


def test_rust_params_carry_type_annotations():
    """Types ride in the read-out record (the IR is untyped at P2)."""
    _sub, r = read_fixture("rust", "max_of_two")
    assert r["params"] == [{"name": "a", "ty": "i64"}, {"name": "b", "ty": "i64"}]
    _sub2, r2 = read_fixture("rust", "sum_list")
    assert r2["params"][0]["ty"] == "Vec<i64>"


# ---------------------------------------------------------------------------
# 2) HONEST RESIDUALS — out-of-scope constructs are named blockers.
# ---------------------------------------------------------------------------
def test_rust_match_is_an_honest_residual():
    _sub, r = read_fixture("rust", "residual_match")
    assert r["ok"] is False
    assert r["ir"] is None, "a blocked read must NEVER hand back partial IR"
    assert "match_expression" in r["blockers"]


def test_lua_varargs_is_an_honest_residual():
    _sub, r = read_fixture("lua", "residual_varargs")
    assert r["ok"] is False
    assert r["ir"] is None
    assert "varargs" in r["blockers"]


def test_lua_table_map_part_is_an_honest_residual():
    _sub, r = read_fixture("lua", "residual_map_table")
    assert r["ok"] is False
    assert r["ir"] is None
    assert "table_map_part" in r["blockers"]


# ---------------------------------------------------------------------------
# 2b) BOOL LITERALS READ CORRECTLY — the P5-B §6.1 bool_text defect,
#     owner-fixed in P6-B (domains/ts_ingest._leaf_value now reads the
#     node's FLAT text: tree-sitter's rust `boolean_literal` carries its
#     text on a token CHILD, so the old parent-text read made EVERY rust
#     bool literal come back Lit false).
# ---------------------------------------------------------------------------
def test_rust_boolean_literal_reads_as_the_right_lit():
    from domains import prog_ir_rust
    sub = srs.Substrate()
    r = prog_ir_rust.read_function(sub, "fn always_yes() -> bool { true }")
    assert r["ok"], f"blockers: {r['blockers']}"
    out = run_prog(sub, r["ir"])
    assert out["trap"] is None and out["halted"] is True
    # the discriminating direction: the defect returned Lit false for BOTH.
    assert out["result"] == True, out["result"]              # noqa: E712
    sub2 = srs.Substrate()
    r2 = prog_ir_rust.read_function(sub2, "fn always_no() -> bool { false }")
    assert r2["ok"], f"blockers: {r2['blockers']}"
    out2 = run_prog(sub2, r2["ir"])
    assert out2["trap"] is None and out2["halted"] is True
    assert out2["result"] == False, out2["result"]           # noqa: E712


def test_rust_boolean_literal_in_condition_branches_correctly():
    """A bool literal in decision position: with the defect, `if true`
    took the else branch. Toolchain truth: rustc on this source returns 1."""
    from domains import prog_ir_rust
    sub = srs.Substrate()
    r = prog_ir_rust.read_function(
        sub, "fn pick() -> i64 { if true { 1 } else { 2 } }")
    assert r["ok"], f"blockers: {r['blockers']}"
    out = run_prog(sub, r["ir"])
    assert out["trap"] is None and out["halted"] is True
    assert out["result"] == 1


# ---------------------------------------------------------------------------
# 3) UNDECLARED-EXTERN TRAP — the P1 oracle contract crosses the frames.
# ---------------------------------------------------------------------------
def test_rust_undeclared_extern_traps():
    sub, r = read_fixture("rust", "extern_trap")
    assert r["ok"], f"blockers: {r['blockers']}"   # the READ is fine
    out = run_prog(sub, r["ir"], env={"x": 1})     # no oracle declared
    assert out["halted"] is False
    assert out["trap"] == "extern:helper"
    assert out["result"] is None


def test_lua_undeclared_extern_traps():
    sub, r = read_fixture("lua", "extern_trap")
    assert r["ok"], f"blockers: {r['blockers']}"
    out = run_prog(sub, r["ir"], env={"x": 5})
    assert out["halted"] is False
    assert out["trap"] == "extern:print"
    assert out["result"] is None


def test_rust_method_call_is_recv_dotted_extern():
    """x.len() reads as ProgCallExtern{name, recv} and honours the P1
    recv contract (declared-but-method -> extern:unimplemented)."""
    from domains import prog_ir_rust
    sub = srs.Substrate()
    r = prog_ir_rust.read_function(
        sub, "fn f(xs: Vec<i64>) -> i64 { xs.len() }")
    assert r["ok"]
    out = run_prog(sub, r["ir"], env={"xs": (1, 2)}, oracles=("len",))
    assert out["trap"] == "extern:unimplemented:len"


# ---------------------------------------------------------------------------
# 4) CROSS-FRAME LAW — one program, three frames, one verdict.
# ---------------------------------------------------------------------------
_PY_TRIPLES = {
    "max_of_two": ("def max_of_two(a, b):\n"
                   "    if a > b:\n"
                   "        return a\n"
                   "    return b\n"),
    "sum_list": ("def sum_list(xs):\n"
                 "    total = 0\n"
                 "    for x in xs:\n"
                 "        total += x\n"
                 "    return total\n"),
    "count_matching": ("def count_matching(xs, t):\n"
                       "    c = 0\n"
                       "    for x in xs:\n"
                       "        if x == t:\n"
                       "            c += 1\n"
                       "    return c\n"),
}

_TRIPLE_RUNS = [
    ("max_of_two", {"a": 7, "b": 3}, ()),
    ("max_of_two", {"a": 2, "b": 5}, ()),
    ("sum_list", {"xs": (1, 2, 3, 4)}, ()),
    ("sum_list", {"xs": (5,)}, ()),
    ("count_matching", {"xs": (1, 2, 2, 3, 2), "t": 2}, ("range", "len")),
    ("count_matching", {"xs": (1, 3), "t": 2}, ("range", "len")),
]


@pytest.mark.parametrize("name,env,oracles", _TRIPLE_RUNS,
                         ids=[f"{c[0]}-{i}" for i, c in enumerate(_TRIPLE_RUNS)])
def test_cross_frame_law(name, env, oracles):
    """The headline: python-frame, rust-frame and lua-frame spellings of
    the SAME function ProgEval to the SAME result on the same inputs. The
    python IR comes from the P2-Python track's emitter
    (domains/prog_ir_emit.py — present at run time, checked late per the
    task order)."""
    from domains import prog_ir_emit
    sub_r, rust = read_fixture("rust", name)
    sub_l, lua = read_fixture("lua", name)
    py = prog_ir_emit.emit_prog_ir(_PY_TRIPLES[name])
    assert rust["ok"], f"rust blockers: {rust['blockers']}"
    assert lua["ok"], f"lua blockers: {lua['blockers']}"
    assert py["ok"], f"python blockers: {py.get('blockers')}"

    sub_p = srs.Substrate()
    results = {
        "rust": run_prog(sub_r, rust["ir"], dict(env), oracles),
        "lua": run_prog(sub_l, lua["ir"], dict(env), oracles),
        "python": run_prog(sub_p, py["ir"], dict(env), oracles),
    }
    for frame, out in results.items():
        assert out["trap"] is None, f"{frame} trapped: {out['trap']}"
        assert out["halted"] is True, f"{frame} did not halt"
    vals = {frame: out["result"] for frame, out in results.items()}
    assert vals["rust"] == vals["lua"] == vals["python"], (
        f"cross-frame law violated on {name}({env}): {vals}")


# ---------------------------------------------------------------------------
# 5) DETERMINISM — emit twice, byte-identical IR JSON.
# ---------------------------------------------------------------------------
_OK_FIXTURES = ([("rust", c[0]) for c in RUST_CASES]
                + [("lua", c[0]) for c in LUA_CASES]
                + [("rust", "extern_trap"), ("lua", "extern_trap")])


@pytest.mark.parametrize("lang,name", sorted(set(_OK_FIXTURES)),
                         ids=[f"{l}-{n}" for l, n in sorted(set(_OK_FIXTURES))])
def test_emission_is_deterministic(lang, name):
    _s1, r1 = read_fixture(lang, name)
    _s2, r2 = read_fixture(lang, name)
    assert json.dumps(r1["ir"], sort_keys=True) == json.dumps(r2["ir"], sort_keys=True)
    assert r1["blockers"] == r2["blockers"]


# ---------------------------------------------------------------------------
# 6) SEED LOADABILITY — the correspondence is inspectable graph data.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["rust", "lua"])
def test_correspondence_seed_loads_cleanly(lang):
    from domains import ts_ingest
    manifest = ts_ingest.load_correspondence_manifest(lang)
    assert manifest["id"] == f"{lang}_correspondence"
    sub = srs.Substrate()
    agent = sub.add_node("Agent", {})
    summary = sub._inner.load_seed_manifest(manifest, agent)
    # "without warnings": the loader's two skip/warn channels are empty.
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []
    assert summary["nodes"] == len(manifest["nodes"])
    rows = sub.nodes("CorrespondenceRow")
    assert len(rows) == len(manifest["nodes"])
    for n in rows:
        attrs = sub.node(n)["attrs"]
        assert attrs.get("lang") == lang
        assert attrs.get("cst_kind")
        assert attrs.get("emit") in ("term", "handler")


@pytest.mark.parametrize("lang", ["rust", "lua"])
def test_walker_table_comes_from_the_seed(lang):
    """The walkers apply THE SEED's rows — same file, same rows (the seed
    is the single source of truth the agent can inspect/repair)."""
    from domains import ts_ingest
    rows = ts_ingest.load_correspondence_rows(lang)
    manifest = ts_ingest.load_correspondence_manifest(lang)
    assert len(rows) == len(manifest["nodes"]) > 20
    handlers_named = {r["handler"] for r in rows if r.get("handler")}
    from domains import prog_ir_lua, prog_ir_rust
    registry = (prog_ir_rust if lang == "rust" else prog_ir_lua).HANDLERS
    missing = handlers_named - set(registry)
    assert not missing, f"seed rows name unregistered handlers: {missing}"


# ---------------------------------------------------------------------------
# 7) CST ingest is a faithful mechanical dump.
# ---------------------------------------------------------------------------
def test_cst_ingest_is_mechanical_and_typed():
    from domains import ts_ingest
    sub = srs.Substrate()
    rec = ts_ingest.ingest_source(sub, "local x = 1 + 2\n", "lua")
    assert rec["n_nodes"] > 5
    kinds = {sub.node(n)["attrs"]["kind"] for n in sub.nodes("CstNode")}
    assert {"chunk", "binary_expression", "number"} <= kinds
    for n in sub.nodes("CstNode"):
        attrs = sub.node(n)["attrs"]
        assert attrs["origin"] == "world_adapter_ts"
        assert "kind" in attrs and "child_index" in attrs and "field" in attrs
    # the operator token is a leaf with its text held verbatim.
    ops = [n for n in sub.nodes("CstNode")
           if sub.node(n)["attrs"].get("text") == "+"]
    assert ops, "anonymous operator leaves must be dumped with their text"


# ---------------------------------------------------------------------------
# 8) SOURCE-UPLOAD ROUTING (file_ingest) — source lands as code graph +
# register facts + runnable hub IR, not opaque metadata.
# ---------------------------------------------------------------------------
def test_classify_upload_source_kinds():
    import domains.file_ingest as fi
    assert fi.classify_upload("text/x-python", "tool.py") == "source"
    assert fi.classify_upload("", "lib.rs") == "source"
    assert fi.classify_upload("text/plain", "init.lua") == "source"
    # plain text routing is byte-unchanged.
    assert fi.classify_upload("text/plain", "readme.md") == "text"
    assert fi.classify_upload("application/octet-stream", "data.bin") == "binary"


def test_uploaded_lua_source_lands_as_graph_ir():
    import tempfile

    import domains.file_ingest as fi
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False,
                                     encoding="utf-8") as f:
        f.write(_fixture("lua", "count_matching"))
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="count_matching.lua")
    finally:
        os.unlink(path)

    assert out["kind"] == "source"
    assert out["language"] == "lua"
    assert out["n_functions"] == 1
    assert out["n_ir_ok"] == 1
    doc = out["document_id"]
    attrs = agent.s.node(doc)["attrs"]
    assert attrs.get("language") == "lua"
    # CST graph wired under the document.
    roots = list(agent.inner.neighbours(doc, "has_code_root"))
    assert roots, "the CST root must hang off the document"
    # hub IR is GRAPH-RESIDENT (a reflected Term subgraph) and RUNNABLE.
    ir_roots = list(agent.inner.neighbours(doc, "has_prog_ir"))
    assert len(ir_roots) == 1
    res = agent.inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "envd"},
         "oracles": {"type": "MkDict",
                     "items": [{"type": "Lit", "value": "range"},
                               {"type": "Lit", "value": "builtin"},
                               {"type": "Lit", "value": "len"},
                               {"type": "Lit", "value": "builtin"}]},
         "fuel": 5000, "field": ""},
        {"p": ir_roots[0], "envd": {"xs": (1, 2, 2, 3, 2), "t": 2}})
    assert res["trap"] is None and res["halted"] is True
    assert res["result"] == 3
    # register facts recorded (the code register's verdict, best-effort
    # but expected on a fully-booted agent).
    assert attrs.get("register") == "code", attrs.get("register")
