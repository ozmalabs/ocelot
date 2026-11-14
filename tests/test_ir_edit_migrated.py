"""test_ir_edit_migrated — authored Python replacements are hub IR.

The replacement code is authored as `Prog*` Term-JSON, rendered by the
existing graph renderer (`domains.render_python`), and spliced into the
lossless Python CST span. The canonical record is the IR op list; the diff is
only a view. Comments/trivia outside the target span must survive exactly.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from scripts.ocelot_code_edit import CodeEditError, sha256_text
from scripts.ocelot_ir_edit import apply_ir_edit_script, fallback_check


def _renderer_available() -> bool:
    """Honest environment guard: the hub renderer needs substrate_rs + seed."""
    try:
        import substrate_rs as srs

        from domains.render_python import install_python_statement_renderer

        install_python_statement_renderer(srs.Substrate())
    except Exception:                                   # pragma: no cover
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _renderer_available(),
    reason="hub-IR renderer (substrate_rs + render_python seed) unavailable",
)

FIXTURE = (
    '"""Demo module."""\n'
    "# keep before\n"
    "def add(a, b):\n"
    "    # keep in body\n"
    "    return a + b  # keep trailing\n"
    "\n"
    "# keep after\n"
    "def scale(x):\n"
    "    return x * 2\n"
)

PLUS_IR = {"type": "Plus", "items": [{"type": "Var", "name": "a"},
                                     {"type": "Lit", "value": 1}]}
RETURN_TOTAL = [
    {"type": "ProgAssignVar", "name": "total",
     "value": {"type": "Plus", "items": [{"type": "Var", "name": "a"},
                                         {"type": "Var", "name": "b"}]}},
    {"type": "ProgReturn", "value": {"type": "Var", "name": "total"}},
]


def _fixture(root: Path, text: str = FIXTURE) -> Path:
    p = root / "mod.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _script(*ops: dict) -> dict:
    return {"file": "mod.py", "ops": list(ops)}


# --------------------------------------------------------------------------- #
#  1) Expression IR: preview, then lossless splice
# --------------------------------------------------------------------------- #
def test_expression_ir_preview_and_splice(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_expression_ir",
        "target": "body[1].body[0].value",
        "term": PLUS_IR,
    }))
    assert r["ok"] is True
    assert r["applied"] is False
    assert r["format"] == "python"
    assert r["engine"] == "hub_ir"
    assert r["blockers"] == []
    assert p.read_text() == FIXTURE                    # preview writes nothing
    assert "+    return (a + 1)  # keep trailing" in r["diff_view"]
    assert r["before"]["sha256"] == sha256_text(FIXTURE)
    assert r["new_sha256"] == r["after"]["sha256"]
    assert r["lossless"]["roundtrip"] is True
    assert r["lossless"]["outside_spans_unchanged"] is True
    assert r["graph_stale"] is False
    assert r["changes"][0]["op"] == "replace_expression_ir"
    assert r["diff_note"].startswith("a unified diff is a rendered view")


def test_dict_target_spelling_matches_code_edit(tmp_path: Path) -> None:
    _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_expression_ir",
        "target": {"path": "body[1].body[0].value"},
        "term": PLUS_IR,
    }))
    assert r["ok"] is True
    assert r["changes"][0]["target"] == "body[1].body[0].value"


def test_expression_apply_backup_and_comments(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_expression_ir",
        "target": "body[1].body[0].value",
        "term": {"type": "Times", "items": [{"type": "Var", "name": "a"},
                                            {"type": "Var", "name": "b"}]},
    }), write=True)
    assert r["ok"] is True and r["applied"] is True
    assert r["graph_stale"] is True
    after = p.read_text()
    ast.parse(after)
    compile(after, str(p), "exec")
    assert "    return (a * b)  # keep trailing\n" in after
    for comment in ("# keep before", "# keep in body", "# keep after"):
        assert comment in after
    backup = Path(r["backup"])
    assert backup.is_file()
    assert backup.read_text() == FIXTURE
    assert backup.parent == tmp_path / "var" / "ocelot_dev_edits" / "backups"
    assert r["before"]["sha256"] == sha256_text(FIXTURE)
    assert r["after"]["sha256"] == sha256_text(after)


# --------------------------------------------------------------------------- #
#  2) Statement body IR replaces only the body span
# --------------------------------------------------------------------------- #
def test_crlf_and_trivia_outside_span_survive_bytes(tmp_path: Path) -> None:
    """The splice is byte-exact: CRLF and comments outside the span survive."""
    raw = (b"# keep\r\n"
           b"def f(a):\r\n"
           b"    return a + 1  # trailing\r\n"
           b"# after\r\n")
    p = tmp_path / "mod.py"
    p.write_bytes(raw)
    r = apply_ir_edit_script(tmp_path, {
        "file": "mod.py",
        "base_sha256": hashlib.sha256(raw).hexdigest(),
        "ops": [{"op": "replace_expression_ir",
                 "target": "body[0].body[0].value",
                 "term": {"type": "Times",
                          "items": [{"type": "Var", "name": "a"},
                                    {"type": "Lit", "value": 2}]}}],
    }, write=True)
    assert r["ok"] is True
    assert p.read_bytes() == (
        b"# keep\r\n"
        b"def f(a):\r\n"
        b"    return (a * 2)  # trailing\r\n"
        b"# after\r\n"
    )


def test_body_statements_render_and_splice(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_body_ir",
        "target": "body[1]",
        "stmts": RETURN_TOTAL,
    }), write=True)
    assert r["ok"] is True and r["applied"] is True
    after = p.read_text()
    ast.parse(after)
    assert "    total = (a + b)\n" in after
    assert "    return total\n" in after
    # The comment sits before the first body statement, i.e. BEFORE the
    # replaced AST span, so the lossless splice preserves it. A comment
    # between two replaced statements is inside the span (next test).
    assert "# keep in body" in after
    assert "# keep before" in after
    assert "# keep after" in after
    assert "def scale(x):\n    return x * 2\n" in after
    assert r["changes"][0]["summary"].startswith("replace body of add")


def test_comment_inside_replaced_body_span_is_replaced(tmp_path: Path) -> None:
    p = _fixture(tmp_path,
                 "def f(a):\n"
                 "    x = a\n"
                 "    # inside the span\n"
                 "    return x\n"
                 "# after the function\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_body_ir",
        "target": "body[0]",
        "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "a"}}],
    }), write=True)
    assert r["ok"] is True
    after = p.read_text()
    assert "# inside the span" not in after
    assert "# after the function" in after
    assert after == "def f(a):\n    return a\n# after the function\n"


def test_body_empty_statements_render_pass(tmp_path: Path) -> None:
    _fixture(tmp_path, "def f():\n    return 1\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_body_ir", "target": "body[0]", "stmts": [],
    }))
    assert "+    pass" in r["diff_view"]


def test_body_on_one_line_function_expands_safely(tmp_path: Path) -> None:
    p = _fixture(tmp_path, "def f(): return 1\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_body_ir",
        "target": "body[0]",
        "stmts": [{"type": "ProgReturn", "value": {"type": "Lit", "value": 2}}],
    }), write=True)
    assert r["ok"] is True
    assert p.read_text() == "def f():\n    return 2\n"


def test_nested_method_body_indentation(tmp_path: Path) -> None:
    _fixture(tmp_path, "class C:\n    def m(self):\n        return 1\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_body_ir",
        "target": "body[0].body[0]",
        "stmts": [{"type": "ProgReturn", "value": {"type": "Lit", "value": 2}}],
    }))
    assert "+        return 2" in r["diff_view"]


# --------------------------------------------------------------------------- #
#  3) Whole-function IR and signature handling
# --------------------------------------------------------------------------- #
def test_function_ir_with_args(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_function_ir",
        "target": "body[1]",
        "args": ["a", "b", "c"],
        "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "c"}}],
    }), write=True)
    assert r["ok"] is True
    after = p.read_text()
    assert "def add(a, b, c):\n    return c\n" in after
    assert "# keep before" in after and "# keep after" in after
    ast.parse(after)


def test_function_ir_term_and_decorator_preserved(tmp_path: Path) -> None:
    p = _fixture(tmp_path, "@deco\ndef f(x):\n    return x\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_function_ir",
        "target": "body[0]",
        "term": {"type": "Lit", "value": 7},
    }), write=True)
    assert r["ok"] is True
    assert p.read_text() == "@deco\ndef f(x):\n    return 7\n"


def test_function_ir_without_args_keeps_signature(tmp_path: Path) -> None:
    p = _fixture(tmp_path, "def f(a, b=2, *args, **kwargs):\n    return a\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_function_ir",
        "target": "body[0]",
        "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "b"}}],
    }), write=True)
    assert r["ok"] is True
    assert p.read_text().startswith("def f(a, b=2, *args, **kwargs):\n")
    assert "    return b\n" in p.read_text()


def test_function_ir_preserves_return_annotation(tmp_path: Path) -> None:
    p = _fixture(tmp_path, "def f(a) -> int:\n    return a\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_function_ir",
        "target": "body[0]",
        "args": ["x"],
        "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "x"}}],
    }), write=True)
    assert r["ok"] is True
    assert p.read_text() == "def f(x) -> int:\n    return x\n"


def test_async_function_whole_replacement_is_blocked(tmp_path: Path) -> None:
    _fixture(tmp_path, "async def f():\n    return 1\n")
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_function_ir",
        "target": "body[0]",
        "stmts": [{"type": "ProgReturn", "value": {"type": "Lit", "value": 2}}],
    }))
    assert r["ok"] is False
    assert r["blockers"] == ["async_function"]


# --------------------------------------------------------------------------- #
#  4) Honest blockers vs invalid IR
# --------------------------------------------------------------------------- #
def test_render_gap_is_reported_and_nothing_is_written(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_expression_ir",
        "target": "body[1].body[0].value",
        "term": {"type": "BitAnd", "a": {"type": "Var", "name": "a"},
                 "b": {"type": "Lit", "value": 1}},
    }))
    assert r["ok"] is False
    assert r["applied"] is False
    assert r["blockers"] == ["render_gap:BitAnd in python"]
    assert r["diff_view"] == ""
    assert r["backup"] is None
    assert p.read_text() == FIXTURE


def test_renderability_refusal_is_reported(tmp_path: Path) -> None:
    _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "replace_expression_ir",
        "target": "body[1].body[0].value",
        "term": {"type": "ProgFString",
                 "parts": [{"type": "Lit", "value": "a{b}"}]},
    }))
    assert r["ok"] is False
    assert r["blockers"] == ["fstring_literal_unspellable"]


def test_blocked_construct_fallback_check_reports_blockers(
        tmp_path: Path) -> None:
    _fixture(tmp_path,
             "def blocked(p):\n"
             "    with open(p) as fh:\n"
             "        return fh.read()\n")
    r = fallback_check(tmp_path, _script({
        "op": "fallback_check", "target": "body[0]",
    }))
    assert r["ok"] is False
    assert r["renderable"] is False
    assert r["blockers"] == ["With"]
    assert r["rendered"] is None


@pytest.mark.parametrize("term, message", [
    ({"type": "Bogus"}, "unknown hub IR term type"),
    ({"type": "Plus"}, "invalid hub IR term"),
    ("a + b", "invalid hub IR term"),
    ({"type": "ProgSeq", "stmts": []}, "not an expression term"),
])
def test_invalid_ir_raises(tmp_path: Path, term, message: str) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match=message):
        apply_ir_edit_script(tmp_path, _script({
            "op": "replace_expression_ir",
            "target": "body[1].body[0].value",
            "term": term,
        }))


# --------------------------------------------------------------------------- #
#  5) Transaction refusals
# --------------------------------------------------------------------------- #
def test_fstring_part_target_refused(tmp_path: Path) -> None:
    _fixture(tmp_path, 'def f(x):\n    return f"hi {x}"\n')
    with pytest.raises(CodeEditError, match="f-string part"):
        apply_ir_edit_script(tmp_path, _script({
            "op": "replace_expression_ir",
            "target": "body[0].body[0].value.values[0]",
            "term": {"type": "Var", "name": "x"},
        }))
    check = fallback_check(tmp_path, _script({
        "op": "fallback_check",
        "target": "body[0].body[0].value.values[0]",
    }))
    assert check["ok"] is False
    assert check["blockers"] == ["fstring_part_target"]


def test_stale_base_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="stale base"):
        apply_ir_edit_script(tmp_path, {
            "file": "mod.py", "base_sha256": "0" * 64,
            "ops": [{"op": "replace_body_ir", "target": "body[1]",
                     "stmts": RETURN_TOTAL}],
        })


def test_raw_diff_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="raw 'diff'"):
        apply_ir_edit_script(tmp_path, {
            "file": "mod.py",
            "diff": "--- a/mod.py\n+++ b/mod.py\n",
            "ops": [{"op": "replace_body_ir", "target": "body[1]",
                     "stmts": RETURN_TOTAL}],
        })


def test_raw_text_inside_ir_op_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="raw 'text'"):
        apply_ir_edit_script(tmp_path, _script({
            "op": "replace_body_ir", "target": "body[1]",
            "stmts": RETURN_TOTAL, "text": "return 1",
        }))


def test_path_escape_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="escapes"):
        apply_ir_edit_script(tmp_path, {
            "file": "../outside.py",
            "ops": [{"op": "replace_body_ir", "target": "body[1]",
                     "stmts": RETURN_TOTAL}],
        })


def test_non_python_file_refused(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("# hi\n", encoding="utf-8")
    with pytest.raises(CodeEditError, match="Python"):
        apply_ir_edit_script(tmp_path, {
            "file": "notes.md",
            "ops": [{"op": "replace_body_ir", "target": "body[1]",
                     "stmts": RETURN_TOTAL}],
        })


def test_overlapping_edits_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    op = {"op": "replace_expression_ir",
          "target": "body[1].body[0].value", "term": PLUS_IR}
    with pytest.raises(CodeEditError, match="overlapping"):
        apply_ir_edit_script(tmp_path, _script(op, op))


# --------------------------------------------------------------------------- #
#  6) Multi-op transaction + fallback_check positives
# --------------------------------------------------------------------------- #
def test_multiple_expression_ops_apply_bottom_up(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script(
        {"op": "replace_expression_ir",
         "target": "body[1].body[0].value", "term": PLUS_IR},
        {"op": "replace_expression_ir",
         "target": "body[2].body[0].value",
         "term": {"type": "Times", "items": [{"type": "Var", "name": "x"},
                                             {"type": "Lit", "value": 3}]}},
    ), write=True)
    assert r["ok"] is True
    after = p.read_text()
    assert "return (a + 1)" in after
    assert "return (x * 3)" in after
    ast.parse(after)
    assert len(r["changes"]) == 2


def test_fallback_check_positive_for_function_and_expression(
        tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    fn = fallback_check(tmp_path, _script({
        "op": "fallback_check", "target": "body[1]",
    }))
    assert fn["ok"] is True and fn["renderable"] is True
    assert fn["grain"] == "function"
    assert fn["node_type"] == "FunctionDef"
    assert fn["ir"]["type"] == "ProgSeq"
    assert "def add(a, b):" in fn["rendered"]

    expr = fallback_check(tmp_path, _script({
        "op": "fallback_check", "target": "body[1].body[0].value",
    }))
    assert expr["ok"] is True and expr["renderable"] is True
    assert expr["grain"] == "expr"
    assert expr["ir"]["type"] == "Plus"
    assert expr["rendered"] == "(a + b)"

    stmts = fallback_check(tmp_path, _script({
        "op": "fallback_check", "stmts": RETURN_TOTAL,
    }))
    assert stmts["ok"] is True and stmts["renderable"] is True
    assert "total = (a + b)" in stmts["rendered"]
    assert p.read_text() == FIXTURE


def test_fallback_check_routes_through_public_api(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_ir_edit_script(tmp_path, _script({
        "op": "fallback_check", "target": "body[1]",
    }))
    assert r["ok"] is True and r["renderable"] is True
    assert r["applied"] is False and r["graph_stale"] is False
    assert p.read_text() == FIXTURE

    blocked = apply_ir_edit_script(tmp_path, _script({
        "op": "fallback_check",
        "term": {"type": "BitAnd", "a": {"type": "Var", "name": "a"},
                 "b": {"type": "Lit", "value": 1}},
    }))
    assert blocked["ok"] is False
    assert blocked["blockers"] == ["render_gap:BitAnd in python"]
    assert blocked["renderable"] is False


def test_fallback_check_is_read_only(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="read-only"):
        apply_ir_edit_script(tmp_path, _script({
            "op": "fallback_check", "target": "body[1]",
        }), write=True)
