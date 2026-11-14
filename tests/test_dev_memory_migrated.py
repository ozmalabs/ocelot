"""test_dev_memory_migrated — the A-integration dev-memory index and MCP tools.

This is dev tooling, not agent cognition: it builds a separate typed-graph
snapshot of a source checkout and answers structural questions over it. The
tests use a tiny synthetic repo so they are fast and do not depend on the real
Ocelot tree.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ocelot_dev_memory import DevMemory, build_index
from scripts.ocelot_dev_memory_mcp import DevMemoryServer


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _fixture(root: Path) -> None:
    _write(root / "domains" / "foo.py", '''"""Foo domain."""

from domains.bar import helper


class Widget:
    """A widget."""

    def size(self, n: int) -> int:
        """Return the widget size."""
        return helper(n) + 1


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')
    _write(root / "domains" / "bar.py", '''"""Bar domain."""


def helper(n: int) -> int:
    """Double n."""
    return n * 2
''')
    _write(root / "tests" / "test_foo.py", '''# exercises seeds/demo.json
from domains.foo import add


def test_add() -> None:
    """add returns the sum."""
    assert add(1, 2) == 3


def test_add_negative() -> None:
    assert add(-1, 1) == 0
''')
    _write(root / "seeds" / "base.json", json.dumps({
        "id": "base",
        "version": "1.0.0",
        "depends_on": [],
        "description": "base seed",
        "nodes": [],
    }))
    _write(root / "seeds" / "demo.json", json.dumps({
        "id": "demo",
        "version": "1.2.0",
        "depends_on": ["base"],
        "description": "demo seed",
        "microtheory": {"name": "demo_mt", "description": "demo theory"},
        "nodes": [
            {"local_id": 1, "type": "Concept",
             "attrs": {"name": "widget", "description": "a widget"}},
        ],
        "rules": [
            {"name": "demo_rule", "match": [], "where": None, "effects": []},
        ],
    }))
    _write(root / "docs" / "features" / "demo.md", """# Demo feature

The demo seed lives in `seeds/demo.json` and is exercised by
`tests/test_foo.py`. The implementation is `domains/foo.py`.
""")
    _write(root / "results" / "failure_baseline.json", json.dumps({
        "entries": [{
            "node": "tests/test_foo.py::test_add_negative",
            "file": "tests/test_foo.py",
            "kind": "FAILED",
            "message": "assert 0 == 1",
            "class": "UNCLASSIFIED",
        }],
    }))
    _write(root / "README.md", "# Fixture repo\n\n`seeds/demo.json`.\n")


def test_build_and_query(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    report = build_index(tmp_path, out, include_docs="features",
                         include_git=False, include_scripts=False)
    assert out.is_file()
    assert report["nodes"] > 0
    assert report["edges"] > 0

    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    stats = mem.stats()
    for typ in ("Repo", "File", "Symbol", "Test", "Seed", "Rule", "Doc",
                "Failure"):
        assert stats["types"].get(typ, 0) >= 1, typ

    # Search finds the seed by its normalized identifier.
    hits = mem.search("demo")
    assert any(h["type"] == "Seed" and h["label"] == "demo" for h in hits)

    # File view: symbols, tests, imports.
    f = mem.file("domains/foo.py")
    assert f["ok"]
    assert {s["label"] for s in f["symbols"]} >= {"add", "Widget"}
    assert any(t["label"] == "test_add" for t in f["tests"])
    assert any(i["label"] == "domains/bar.py" for i in f["imports"])

    # Docs are ordinary File nodes too.
    d = mem.file("docs/features/demo.md")
    assert d["ok"]
    assert any(x["label"] == "docs/features/demo.md"
               for x in d["related"].get("defines", []))

    # Symbol view carries a real snippet and the defining file.
    s = mem.symbol("add")
    assert s["ok"]
    assert s["matches"][0]["file"] == "domains/foo.py"
    assert "def add" in s["matches"][0]["snippet"]["text"]

    # Seed view: dependency, items, tests, docs.
    seed = mem.seed("demo")
    assert seed["ok"]
    assert seed["attrs"]["version"] == "1.2.0"
    assert {n["label"] for n in seed["depends_on"]} == {"base"}
    assert any(i["label"] == "demo_rule" for i in seed["items"])
    assert any(i["label"] == "widget" for i in seed["items"])
    assert any(t["label"] == "test_add" for t in seed["tests"])
    assert any(d["label"] == "docs/features/demo.md" for d in seed["docs"])

    # Tests-for: module import and seed mention.
    t = mem.tests_for("domains/foo.py")
    assert t["ok"]
    assert {x["test"]["label"] for x in t["tests"]} >= {"test_add",
                                                       "test_add_negative"}
    t2 = mem.tests_for("demo")
    assert t2["ok"]
    assert any(x["test"]["label"] == "test_add" for x in t2["tests"])

    # Outline mode: signatures/docstrings, never bodies.
    out = mem.outline_target("domains/foo.py")
    assert out["ok"]
    assert "def add" in out["text"] and "class Widget" in out["text"]
    assert "return a + b" not in out["text"]
    so = mem.outline_target("add")
    assert so["ok"]
    assert "def add(a, b) -> int:" in so["text"]
    assert "Add two numbers." in so["text"]
    assert "return a + b" not in so["text"]

    # Token-budgeted context: outline mode stays compact.
    ctx_budget = mem.context("add a rule to demo", mode="outline",
                             budget_tokens=250)
    assert ctx_budget["budget"]["mode"] == "outline"
    assert ctx_budget["budget"]["estimated_tokens"] <= 250 or         len(ctx_budget["items"]) >= 1
    assert all(i["snippet"].get("estimated_tokens", 0) > 0
               for i in ctx_budget["items"])

    # Pre-loaded brief: deterministic, citation-backed, optionally written.
    brief = mem.brief("add a rule to demo", write=True)
    assert brief["ok"]
    assert "# Ocelot repo brief" in brief["markdown"]
    assert "## Layout" in brief["markdown"]
    assert "## Key docs" in brief["markdown"]
    assert "## Task context: add a rule to demo" in brief["markdown"]
    assert brief["estimated_tokens"] > 0
    assert brief["path"] and Path(brief["path"]).is_file()

    # Context anchors on the seed named by the task, before fuzzy hits.
    ctx = mem.context("add a rule to demo")
    assert ctx["items"]
    assert ctx["items"][0]["node"]["type"] == "Seed"
    assert ctx["items"][0]["node"]["label"] == "demo"
    assert "demo seed" in ctx["items"][0]["attrs"].get("description", "")

    # Failure is linked to the exact test node.
    fail = [n for n in mem.nodes.values() if n["type"] == "Failure"][0]
    related = mem.related(int(fail["id"]))
    assert any(x["label"] == "test_add_negative"
               for x in related.get("refers_to", []))


def test_changed(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    # Not a git repo yet: the tool reports that honestly.
    assert mem.changed()["ok"] is False
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    changed = mem.changed()
    assert changed["ok"] is True
    paths = {f["path"] for f in changed["files"]}
    assert "domains/foo.py" in paths
    assert "seeds/demo.json" in paths
    assert "docs/features/demo.md" in paths


def test_cst_dispatch(tmp_path: Path) -> None:
    from scripts.ocelot_edit import apply_edit_script
    source = "let x = 1;\n"
    (tmp_path / "lib.rs").write_text(source, encoding="utf-8")
    graph = {
        "kind": "source_file",
        "children": [{
            "kind": "let_declaration",
            "children": [
                {"kind": "keyword", "text": "let "},
                {"kind": "identifier", "text": "x"},
                {"kind": "eq", "text": " = "},
                {"kind": "integer_literal", "text": "1"},
                {"kind": "semicolon", "text": ";\n"},
            ],
        }],
    }
    r = apply_edit_script(tmp_path, {
        "file": "lib.rs",
        "cst_graph": graph,
        "ops": [{"op": "replace_node", "path": "child[0].child[3]",
                 "text": "2"}],
    })
    assert r["ok"] is True
    assert r["format"] == "rust"
    assert r["applied"] is False
    assert "+let x = 2;" in r["diff_view"]
    assert r["lossless"]["roundtrip"] is True


def test_ir_dispatch_and_journal(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    r = mem.edit({
        "file": "domains/foo.py",
        "apply": True,
        "ops": [{
            "op": "replace_expression_ir",
            "target": "body[3].body[1].value",
            "term": {"type": "Plus",
                     "items": [{"type": "Var", "name": "a"},
                               {"type": "Lit", "value": 1}]},
        }],
    }, task="ir add one")
    assert r["ok"] is True and r["applied"] is True
    assert r["engine"] == "hub_ir"
    assert "return (a + 1)" in (tmp_path / "domains" / "foo.py").read_text()
    entry = mem.journal_recent(1)[0]
    assert entry["kind"] == "edit"
    assert entry["task"] == "ir add one"


def test_journal(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    e = mem.journal_append("verification", "test add",
                           "pytest tests/test_foo.py -q",
                           files=["tests/test_foo.py"], exit_code=0)
    assert e["kind"] == "verification"
    recent = mem.journal_recent(5)
    assert recent[-1]["task"] == "test add"
    assert recent[-1]["exit_code"] == 0


def test_mcp_protocol(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="features",
                include_git=False, include_scripts=False)
    server = DevMemoryServer(DevMemory(out, tmp_path / "var" / "journal.jsonl"))

    init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {}})
    assert init["result"]["serverInfo"]["name"] == "ocelot-dev-memory"
    assert "tools" in init["result"]["capabilities"]

    tools = server.handle({"jsonrpc": "2.0", "id": 2,
                           "method": "tools/list", "params": {}})
    names = {t["name"] for t in tools["result"]["tools"]}
    assert {"dev_context", "dev_brief", "dev_search", "dev_file",
            "dev_symbol", "dev_outline", "dev_ast", "dev_edit",
            "dev_tests", "dev_seed", "dev_rule", "dev_record",
            "dev_changed", "dev_repo_map", "dev_impact",
            "dev_architecture", "dev_scip", "dev_code_search",
            "dev_lsp_status", "dev_definition", "dev_references",
            "dev_callers", "dev_callees", "dev_symbol_impact",
            "dev_rename_preview", "dev_diagnostics", "dev_hover",
            "dev_document_symbols", "dev_session_start", "dev_session_record",
            "dev_session_state", "dev_session_next", "dev_session_finish",
            "dev_session_list"} <= names

    call = server.handle({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "dev_seed", "arguments": {"seed_id": "demo"}},
    })
    assert call["result"]["isError"] is False
    payload = json.loads(call["result"]["content"][0]["text"])
    assert payload["ok"] is True
    assert payload["attrs"]["id"] == "demo"

    brief = server.handle({
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "dev_brief", "arguments": {}},
    })
    assert brief["result"]["isError"] is False
    assert "# Ocelot repo brief" in brief["result"]["content"][0]["text"]

    outline = server.handle({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {"name": "dev_outline",
                   "arguments": {"target": "domains/foo.py"}},
    })
    assert outline["result"]["isError"] is False
    op = json.loads(outline["result"]["content"][0]["text"])
    assert op["ok"] and "def add" in op["text"]
    assert "return a + b" not in op["text"]

    ast_out = server.handle({
        "jsonrpc": "2.0", "id": 11, "method": "tools/call",
        "params": {"name": "dev_ast",
                   "arguments": {"file": "domains/foo.py",
                                 "max_nodes": 40}},
    })
    assert ast_out["result"]["isError"] is False
    ap = json.loads(ast_out["result"]["content"][0]["text"])
    assert ap["ok"] and "body[2]" in ap["text"]
    assert "def add" in ap["text"]

    edit = server.handle({
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": "dev_edit", "arguments": {
            "file": "domains/foo.py",
            "ops": [{"op": "replace_body", "symbol": "add",
                     "text": "return a + b + 1"}],
            "apply": False,
        }},
    })
    assert edit["result"]["isError"] is False
    ep = json.loads(edit["result"]["content"][0]["text"])
    assert ep["ok"] and ep["applied"] is False
    assert "+    return a + b + 1" in ep["diff_view"]

    res = server.handle({"jsonrpc": "2.0", "id": 8,
                         "method": "resources/list", "params": {}})
    assert res["result"]["resources"][0]["uri"] == "ocelot://brief"
    read = server.handle({"jsonrpc": "2.0", "id": 9,
                          "method": "resources/read",
                          "params": {"uri": "ocelot://brief"}})
    assert "# Ocelot repo brief" in read["result"]["contents"][0]["text"]

    rmap = server.handle({
        "jsonrpc": "2.0", "id": 21, "method": "tools/call",
        "params": {"name": "dev_repo_map", "arguments": {
            "task": "add one", "budget_tokens": 500}},
    })
    assert rmap["result"]["isError"] is False
    rp = json.loads(rmap["result"]["content"][0]["text"])
    assert rp["ok"] and rp["files"]
    assert "domains/foo.py" in rp["markdown"] or "domains/bar.py" in rp["markdown"]

    imp = server.handle({
        "jsonrpc": "2.0", "id": 22, "method": "tools/call",
        "params": {"name": "dev_impact", "arguments": {
            "file": "domains/bar.py", "depth": 1}},
    })
    assert imp["result"]["isError"] is False
    ip = json.loads(imp["result"]["content"][0]["text"])
    assert ip["ok"] is True
    assert any(x["path"] == "domains/foo.py" for x in ip["impacted"])

    lsp = server.handle({
        "jsonrpc": "2.0", "id": 26, "method": "tools/call",
        "params": {"name": "dev_lsp_status", "arguments": {}},
    })
    assert lsp["result"]["isError"] is False
    lp = json.loads(lsp["result"]["content"][0]["text"])
    assert lp["ok"] is True and "languages" in lp

    lsp_def = server.handle({
        "jsonrpc": "2.0", "id": 27, "method": "tools/call",
        "params": {"name": "dev_definition", "arguments": {
            "file": "domains/foo.py", "line": 0, "character": 4,
            "language": "go"}},
    })
    assert lsp_def["result"]["isError"] is False
    ldp = json.loads(lsp_def["result"]["content"][0]["text"])
    assert ldp["ok"] is False

    search = server.handle({
        "jsonrpc": "2.0", "id": 25, "method": "tools/call",
        "params": {"name": "dev_code_search",
                   "arguments": {"query": "add", "limit": 5}},
    })
    assert search["result"]["isError"] is False
    sp = json.loads(search["result"]["content"][0]["text"])
    assert sp["ok"] is True
    assert any(r["path"] in ("domains/foo.py", "domains/bar.py")
               for r in sp["results"])

    scip_path = tmp_path / "index.scip.json"
    scip_path.write_text(json.dumps({
        "documents": [{
            "relative_path": "domains/foo.py",
            "language": "python",
            "occurrences": [{
                "symbol": "scip-python python demo 0.1 `domains/foo.py`/add().",
                "symbol_roles": 1,
                "range": [3, 0, 3, 3],
            }],
        }],
    }), encoding="utf-8")
    scip = server.handle({
        "jsonrpc": "2.0", "id": 24, "method": "tools/call",
        "params": {"name": "dev_scip",
                   "arguments": {"path": "index.scip.json"}},
    })
    assert scip["result"]["isError"] is False
    sp = json.loads(scip["result"]["content"][0]["text"])
    assert sp["ok"] is True
    assert sp["totals"]["definitions"] == 1

    arch = server.handle({
        "jsonrpc": "2.0", "id": 23, "method": "tools/call",
        "params": {"name": "dev_architecture", "arguments": {"top": 5}},
    })
    assert arch["result"]["isError"] is False
    ap = json.loads(arch["result"]["content"][0]["text"])
    assert ap["ok"] is True
    assert "hubs" in ap["summary"]
    assert "# Architecture" in ap["markdown"]

    start = server.handle({
        "jsonrpc": "2.0", "id": 12, "method": "tools/call",
        "params": {"name": "dev_session_start", "arguments": {
            "task": "touch demo", "max_attempts": 3}},
    })
    assert start["result"]["isError"] is False
    sp = json.loads(start["result"]["content"][0]["text"])
    sid = sp["state"]["session_id"]
    assert sp["next"]["action"] == "orient"

    plan = server.handle({
        "jsonrpc": "2.0", "id": 13, "method": "tools/call",
        "params": {"name": "dev_session_record", "arguments": {
            "session_id": sid, "kind": "plan",
            "fields": {"steps": ["one", "two"]}}},
    })
    assert plan["result"]["isError"] is False
    pp = json.loads(plan["result"]["content"][0]["text"])
    assert pp["next"]["action"] == "plan_step"

    step = server.handle({
        "jsonrpc": "2.0", "id": 14, "method": "tools/call",
        "params": {"name": "dev_session_record", "arguments": {
            "session_id": sid, "kind": "step"}},
    })
    assert step["result"]["isError"] is False
    assert json.loads(step["result"]["content"][0]["text"])["next"]["action"] == "act"

    edit = server.handle({
        "jsonrpc": "2.0", "id": 15, "method": "tools/call",
        "params": {"name": "dev_session_record", "arguments": {
            "session_id": sid, "kind": "edit",
            "fields": {"files": ["domains/foo.py"]}}},
    })
    assert edit["result"]["isError"] is False
    assert json.loads(edit["result"]["content"][0]["text"])["next"]["action"] == "verify"

    ver = server.handle({
        "jsonrpc": "2.0", "id": 16, "method": "tools/call",
        "params": {"name": "dev_session_record", "arguments": {
            "session_id": sid, "kind": "verification",
            "fields": {"passed": False, "command": "pytest x", "exit_code": 1}}},
    })
    assert ver["result"]["isError"] is False
    assert json.loads(ver["result"]["content"][0]["text"])["next"]["action"] == "diagnose"

    nxt = server.handle({
        "jsonrpc": "2.0", "id": 17, "method": "tools/call",
        "params": {"name": "dev_session_next", "arguments": {"session_id": sid}},
    })
    assert json.loads(nxt["result"]["content"][0]["text"])["next"]["action"] == "diagnose"

    st = server.handle({
        "jsonrpc": "2.0", "id": 18, "method": "tools/call",
        "params": {"name": "dev_session_state", "arguments": {"session_id": sid}},
    })
    assert st["result"]["isError"] is False
    assert json.loads(st["result"]["content"][0]["text"])["state"]["counts"]["Edit"] == 1

    fin = server.handle({
        "jsonrpc": "2.0", "id": 19, "method": "tools/call",
        "params": {"name": "dev_session_finish", "arguments": {
            "session_id": sid, "outcome": "abandoned"}},
    })
    assert fin["result"]["isError"] is False
    assert json.loads(fin["result"]["content"][0]["text"])["state"]["status"] == "closed"

    lst = server.handle({
        "jsonrpc": "2.0", "id": 20, "method": "tools/call",
        "params": {"name": "dev_session_list", "arguments": {}},
    })
    assert lst["result"]["isError"] is False
    assert any(s["session_id"] == sid
               for s in json.loads(lst["result"]["content"][0]["text"])["sessions"])

    rec = server.handle({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "dev_record", "arguments": {
            "kind": "decision", "task": "touch demo",
            "summary": "use demo seed", "files": ["seeds/demo.json"]}},
    })
    assert rec["result"]["isError"] is False
    recent = server.handle({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "dev_recent", "arguments": {"n": 5}},
    })
    entries = json.loads(recent["result"]["content"][0]["text"])["entries"]
    assert entries[-1]["task"] == "touch demo"


def _git(root: Path, *args: str) -> None:
    import subprocess
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)


def test_process_root_override_acts_on_that_checkout(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    _fixture(snap)
    out = snap / "var" / "dev_graph.json"
    build_index(snap, out, include_docs="none",
                include_git=False, include_scripts=False)
    other = tmp_path / "other"
    _fixture(other)
    _write(other / "domains" / "only_here.py", "def only_here():\n    return 1\n")
    snap_foo = (snap / "domains" / "foo.py").read_text(encoding="utf-8")

    mem = DevMemory(out, tmp_path / "journal.jsonl", root=other)
    assert mem.raw_repo_root == str(other.resolve())
    assert mem.ast("domains/only_here.py")["ok"] is True
    with pytest.raises(ValueError, match="not a Python file"):
        DevMemory(out, tmp_path / "journal2.jsonl").ast("domains/only_here.py")

    res = mem.edit({**ADD_EDIT_OPS, "apply": True})
    assert res["applied"] is True
    assert "return a + b + 1" in (other / "domains" / "foo.py").read_text(
        encoding="utf-8")
    assert (snap / "domains" / "foo.py").read_text(encoding="utf-8") == snap_foo

    _git(other, "init", "-q")
    _git(other, "add", "-A")
    _git(other, "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-q", "-m", "base")
    _write(other / "domains" / "new_module.py", "x = 1\n")
    changed = mem.changed(limit=50)
    assert changed["ok"] is True
    assert "domains/new_module.py" in [f["path"] for f in changed["files"]]
    assert "snapshot" in changed


ADD_EDIT_OPS = {"file": "domains/foo.py",
                "ops": [{"op": "replace_body", "symbol": "add",
                         "text": "return a + b + 1"}]}


def test_edit_rejects_non_boolean_apply(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    with pytest.raises(ValueError, match="apply must be a boolean"):
        mem.edit({**ADD_EDIT_OPS, "apply": "maybe"})
    assert "return a + b + 1" not in (tmp_path / "domains" / "foo.py").read_text(
        encoding="utf-8")


def test_staleness_reports_moved_head(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-q", "-m", "one")
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=True, include_scripts=False)

    fresh = DevMemory(out, tmp_path / "var" / "journal.jsonl").staleness()
    assert fresh["stale"] is False
    assert fresh["snapshot_head"] is not None
    assert fresh["snapshot_head"] == fresh["head"]

    _write(tmp_path / "NOTES.md", "second commit\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-q", "-m", "two")
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    stale = mem.staleness()
    assert stale["stale"] is True
    assert stale["snapshot_head"] != stale["head"]
    assert "snapshot" in mem.brief()
    assert "WARNING: snapshot is stale" in mem.brief()["markdown"]


def test_read_returns_new_content_after_file_changes(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    assert "def add" in mem._read("domains/foo.py")
    first = mem._read("domains/foo.py")
    _write(tmp_path / "domains" / "foo.py", first + "\n\nVALUE = 42\n")
    assert "VALUE = 42" in mem._read("domains/foo.py")


def test_scip_path_must_stay_inside_repo(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    with pytest.raises(ValueError, match="scip_path escapes the repo root"):
        mem.impact("domains/bar.py", scip_path="../x.json")
    with pytest.raises(ValueError, match="no such SCIP index"):
        mem.impact("domains/bar.py", scip_path="missing.scip.json")


def _stamp(p: Path) -> tuple[int, int] | None:
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns)


def test_index_tools_write_cache_under_process_root(tmp_path: Path) -> None:
    from scripts.ocelot_dev_memory import ROOT
    real_cache = ROOT / "var" / "ocelot_dev_tags.json"
    before = _stamp(real_cache)
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl", root=tmp_path)
    mem.repo_map("add")
    mem.impact("domains/bar.py")
    mem.code_search("helper")
    mem.architecture()
    assert (tmp_path / "var" / "ocelot_dev_tags.json").is_file()
    assert _stamp(real_cache) == before


def test_cli_root_flag_selects_the_checkout_that_is_edited(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.ocelot_dev_memory import main as dev_memory_main
    snap_root = tmp_path / "a"
    _fixture(snap_root)
    out = snap_root / "var" / "dev_graph.json"
    build_index(snap_root, out, include_docs="none",
                include_git=False, include_scripts=False)
    target = tmp_path / "b"
    _fixture(target)
    a_before = (snap_root / "domains" / "foo.py").read_text(encoding="utf-8")
    ops = json.dumps([{"op": "replace_body", "symbol": "add",
                       "text": "return a + b + 1"}])
    rc = dev_memory_main(["--dump", str(out),
                          "--journal", str(tmp_path / "journal.jsonl"),
                          "edit", "--file", "domains/foo.py",
                          "--ops-json", ops, "--apply",
                          "--root", str(target)])
    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["applied"] is True
    assert "return a + b + 1" in (target / "domains" / "foo.py").read_text(
        encoding="utf-8")
    assert (snap_root / "domains" / "foo.py").read_text(
        encoding="utf-8") == a_before


def _commit_all(root: Path) -> None:
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-q", "-m", "base")


def test_staleness_follows_the_working_tree(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _git(tmp_path, "init", "-q")
    _commit_all(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    journal = tmp_path / "var" / "journal.jsonl"
    build_index(tmp_path, out, include_docs="none",
                include_git=True, include_scripts=False)
    fresh = DevMemory(out, journal).staleness()
    assert fresh["stale"] is False
    assert fresh["tree_changed"] is False

    foo = tmp_path / "domains" / "foo.py"
    _write(foo, foo.read_text(encoding="utf-8") + "\n# local edit\n")
    edited = DevMemory(out, journal).staleness()
    assert edited["stale"] is True
    assert edited["tree_changed"] is True
    assert edited["snapshot_head"] == edited["head"]

    _git(tmp_path, "checkout", "--", "domains/foo.py")
    restored = DevMemory(out, journal).staleness()
    assert restored["stale"] is False
    assert restored["tree_changed"] is False


def test_staleness_sees_new_untracked_source_file(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _git(tmp_path, "init", "-q")
    _commit_all(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=True, include_scripts=False)
    _write(tmp_path / "domains" / "new_module.py", "x = 1\n")
    stale = DevMemory(out, tmp_path / "var" / "journal.jsonl").staleness()
    assert stale["tree_changed"] is True
    assert stale["stale"] is True


def test_snapshot_without_git_records_digest_error(tmp_path: Path) -> None:
    _fixture(tmp_path)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    repo = next(n for n in json.loads(out.read_text(encoding="utf-8"))["nodes"]
                if n["type"] == "Repo")
    assert "tree_digest" not in repo["attrs"]
    assert repo["attrs"]["tree_digest_error"]
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    assert mem.staleness()["tree_changed"] is False
