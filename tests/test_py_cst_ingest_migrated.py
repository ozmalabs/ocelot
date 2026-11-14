"""test_py_cst_ingest_migrated — Python joins the substrate's lossless CST.

`ts_ingest` already defines the contract for Rust/Lua: `CstNode` leaves carry
text, `flat_text` reconstructs the source. This test pins the Python bridge and
the AST overlay spans that make semantic targets addressable on that CST.
"""
from __future__ import annotations

import ast
from pathlib import Path

from substrate_rs import Substrate

from domains import ast_to_term
from domains.py_cst_ingest import flat_text, ingest_source, python_cst_leaves
from domains.ts_ingest import TableWalker
from scripts.ocelot_lossless import LosslessText


SOURCE = '''"""Module doc."""

# a leading comment
x = "é"  # trailing comment

def add(a, b):
    # body comment
    return a + b  # keep me


# final comment (no trailing newline)'''


def test_python_cst_is_byte_exact() -> None:
    leaves = python_cst_leaves(SOURCE)
    assert flat_text(leaves) == SOURCE
    assert any(leaf["kind"] == "COMMENT" for leaf in leaves)
    assert any(leaf["kind"] == "trivia" for leaf in leaves)
    assert any("é" in leaf["text"] for leaf in leaves)


def test_cst_substrate_flat_text() -> None:
    s = Substrate()
    out = ingest_source(s, SOURCE)
    assert out["language"] == "python"
    assert out["n_nodes"] == len(python_cst_leaves(SOURCE)) + 1
    walker = TableWalker(s, [], {})
    assert walker.flat_text(out["root"]) == SOURCE


def test_ast_overlay_has_spans() -> None:
    s = Substrate()
    ast_to_term.open_ast_productions(s)
    ast_to_term.ingest_ast(s, SOURCE, root_label="m")
    got = {}
    for nid in s.nodes("AstNode"):
        a = s.node(nid)["attrs"]
        if a.get("ast_type") in ("FunctionDef", "Return"):
            got[a["ast_type"]] = a
    assert "lineno" in got["FunctionDef"]
    assert got["FunctionDef"]["end_lineno"] >= got["FunctionDef"]["lineno"]
    assert got["Return"]["lineno"] > got["FunctionDef"]["lineno"]


def test_lossless_edit_preserves_comments() -> None:
    doc = LosslessText.from_python(SOURCE)
    start = SOURCE.index("return a + b")
    end = start + len("return a + b")
    doc.replace(start, end, "return a + b + 1")
    out = doc.render()
    assert "return a + b + 1" in out
    assert "# a leading comment" in out
    assert "# body comment" in out
    assert "# keep me" in out
    assert "# final comment" in out
    assert out.endswith("# final comment (no trailing newline)")
    ast.parse(out)
    assert LosslessText.from_python(out).render() == out


def test_code_edit_uses_lossless_cst(tmp_path: Path) -> None:
    from scripts.ocelot_code_edit import apply_edit_script
    p = tmp_path / "mod.py"
    p.write_text(SOURCE, encoding="utf-8")
    r = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "replace_body", "symbol": "add",
                 "text": "return a * b"}],
    })
    assert r["lossless"]["python_cst"] is True
    assert "# body comment" in r["diff_view"]
    assert "# keep me" in r["diff_view"]
    # The comment inside the replaced body is legitimately gone; comments
    # outside it survive.
    assert "# a leading comment" not in "".join(
        ln for ln in r["diff_view"].splitlines()
        if ln.startswith("-") and "a leading" in ln)
