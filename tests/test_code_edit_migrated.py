"""test_code_edit_migrated — graph-addressed edits, not text patches.

The canonical artifact is an op list against symbol/definition targets. A diff
is only a rendered view; raw diff input is refused.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ocelot_code_edit import (
    CodeEditError,
    apply_edit_script,
    sha256_text,
    symbol_table,
)
from scripts.ocelot_dev_memory import DevMemory, build_index


def _fixture(root: Path) -> Path:
    p = root / "mod.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        '"""Demo module."""\n'
        "import os\n"
        "\n"
        "class Widget:\n"
        "    def size(self, n):\n"
        "        return n\n"
        "\n"
        "def add(a, b):\n"
        '    """Add two numbers."""\n'
        "    return a + b\n",
        encoding="utf-8",
    )
    return p


def test_symbol_table() -> None:
    source = _fixture_source = (
        "class A:\n"
        "    def m(self, x):\n"
        "        return x\n"
        "\n"
        "@decorator\n"
        "def f(a, b=1):\n"
        "    return a + b\n"
    )
    table = symbol_table(source)
    assert set(table) == {"A", "A.m", "f"}
    assert table["f"].start_line == 6  # decorator line, not `def`
    assert table["A.m"].body_indent == "        "


def test_preview_is_not_apply(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    before = p.read_text()
    script = {
        "file": "mod.py",
        "ops": [
            {"op": "replace_body", "symbol": "add",
             "text": "return a + b + 1"},
            {"op": "insert_import", "module": "typing", "names": ["Any"]},
        ],
    }
    r = apply_edit_script(tmp_path, script)
    assert r["ok"] and r["applied"] is False
    assert p.read_text() == before
    assert "from typing import Any" in r["diff_view"]
    assert "return a + b + 1" in r["diff_view"]
    assert r["diff_note"].startswith("a unified diff is a rendered view")


def test_apply_backup_and_journal(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    build_index(tmp_path, tmp_path / "var" / "g.json",
                include_docs="none", include_git=False,
                include_scripts=False)
    mem = DevMemory(tmp_path / "var" / "g.json",
                    tmp_path / "var" / "j.jsonl")
    before = p.read_text()
    r = mem.edit({
        "file": "mod.py",
        "apply": True,
        "ops": [{"op": "replace_body", "symbol": "add",
                 "text": "return a + b + 1"}],
    }, task="add one")
    assert r["applied"] is True
    assert "return a + b + 1" in p.read_text()
    assert r["backup"] and Path(r["backup"]).is_file()
    assert Path(r["backup"]).read_text() == before
    assert r["before"]["sha256"] == sha256_text(before)
    assert r["after"]["sha256"] == sha256_text(p.read_text())
    recent = mem.journal_recent(1)[0]
    assert recent["kind"] == "edit"
    assert recent["task"] == "add one"
    assert recent["new_sha256"] == r["new_sha256"]


def test_stale_base_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="stale base"):
        apply_edit_script(tmp_path, {
            "file": "mod.py",
            "base_sha256": "0" * 64,
            "ops": [{"op": "replace_body", "symbol": "add",
                     "text": "return 0"}],
        })


def test_raw_diff_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="raw 'diff'"):
        apply_edit_script(tmp_path, {
            "file": "mod.py", "diff": "--- a/mod.py\n+++ b/mod.py\n",
            "ops": [],
        })


def test_replace_symbol_and_delete(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "replace_symbol", "symbol": "Widget.size",
                 "text": "    def size(self, n):\n        return n * 2\n"}],
    })
    assert "return n * 2" in r["diff_view"]
    r2 = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "delete_symbol", "symbol": "Widget"}],
    })
    after_diff = r2["diff_view"].split("+++ b/mod.py")[1]
    assert "-class Widget" in after_diff
    assert "+class Widget" not in after_diff


def test_generic_ast_node_ops(tmp_path: Path) -> None:
    _fixture(tmp_path)
    # Replace a return expression: body[3] is `add`, body[1] is `return`.
    r = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "replace_node",
                 "target": "body[3].body[1].value",
                 "text": "a * b"}],
    })
    assert "+    return a * b" in r["diff_view"]

    # Insert a statement before the return, at the right indentation.
    r2 = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "insert_before_node",
                 "target": "body[3].body[1]",
                 "text": "print(a)"}],
    })
    assert "+    print(a)" in r2["diff_view"]

    # Wrap an expression in place.
    r3 = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "wrap_node",
                 "target": "body[3].body[1].value",
                 "prefix": "(", "suffix": ") * 2"}],
    })
    assert "+    return (a + b) * 2" in r3["diff_view"]

    # Delete an argument: the comma cleanup keeps the signature valid.
    r4 = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "delete_node",
                 "target": "body[3].args.args[1]"}],
    })
    assert "+def add(a):" in r4["diff_view"]

    # Replace a whole statement with another statement.
    r5 = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "replace_node",
                 "target": "body[3].body[1]",
                 "text": "raise ValueError('no')"}],
    })
    assert "+    raise ValueError('no')" in r5["diff_view"]
    assert "-    return a + b" in r5["diff_view"]


def test_generic_ops_preserve_comments(tmp_path: Path) -> None:
    p = tmp_path / "mod.py"
    p.write_text(
        '"""Doc."""\n'
        "# keep before\n"
        "def f(a):\n"
        "    # keep in body\n"
        "    return a  # keep trailing\n"
        "# keep after\n",
        encoding="utf-8",
    )
    r = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "replace_node", "target": "body[1].body[0].value",
                 "text": "a + 1"}],
    })
    assert "+    return a + 1  # keep trailing" in r["diff_view"]
    for comment in ("# keep before", "# keep in body", "# keep after"):
        assert comment not in "".join(
            ln for ln in r["diff_view"].splitlines()
            if ln.startswith(("-", "+")) and comment in ln)


def test_generic_delete_removes_decorator_with_definition(tmp_path: Path) -> None:
    p = tmp_path / "mod.py"
    p.write_text(
        "@deco\ndef f():\n    return 1\n\n\ndef g():\n    return 2\n",
        encoding="utf-8",
    )
    r = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "delete_node", "target": "body[0]"}],
    })
    # Both the decorator and the decorated function are gone.
    assert "-@deco" in r["diff_view"]
    assert "-def f():" in r["diff_view"]
    from scripts.ocelot_code_edit import _apply_ops
    new_source, _ = _apply_ops(p.read_text(), r["ops"])
    import ast
    ast.parse(new_source)
    assert "def f" not in new_source


def test_rename_is_lexical_and_reported(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_edit_script(tmp_path, {
        "file": "mod.py",
        "ops": [{"op": "rename_symbol", "symbol": "add",
                 "new_name": "sum_two"}],
    })
    assert "sum_two" in r["diff_view"]
    assert r["changes"][0]["summary"].startswith("renamed 'add'")
    # A rename cannot be silently combined with span ops in v0.
    with pytest.raises(CodeEditError, match="only op"):
        apply_edit_script(tmp_path, {
            "file": "mod.py",
            "ops": [
                {"op": "rename_symbol", "symbol": "add", "new_name": "x"},
                {"op": "delete_symbol", "symbol": "Widget"},
            ],
        })


def test_syntax_error_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="would not parse"):
        apply_edit_script(tmp_path, {
            "file": "mod.py",
            "ops": [{"op": "replace_body", "symbol": "add",
                     "text": "return ("}],
        })


def test_path_escape_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="escapes"):
        apply_edit_script(tmp_path, {
            "file": "../outside.py",
            "ops": [{"op": "replace_body", "symbol": "add",
                     "text": "return 0"}],
        })
