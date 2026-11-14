"""test_edit_txn_migrated — the shared read/hash/write transaction.

DEV TOOLING, NOT AGENT RUNTIME. These tests cover `scripts/ocelot_edit_txn.py`
directly, plus the cross-adapter guarantees that do not belong to one format:
newline detection, UTF-8/BOM/encoding refusal, the TOCTOU re-check before
replace, unique backups, and the rule that no adapter keeps a private write
path. Adapter-specific CRLF/BOM/encoding cases live in the adapter test files.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import scripts.ocelot_edit_txn as txn
from scripts.ocelot_code_edit import CodeEditError, apply_edit_script
from scripts.ocelot_edit_txn import (
    detect_newline,
    normalize_newlines,
    read_source,
)

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ADAPTERS = (
    "ocelot_code_edit.py",
    "ocelot_json_edit.py",
    "ocelot_markdown_edit.py",
    "ocelot_cst_edit.py",
    "ocelot_ir_edit.py",
)
BOM = b"\xef\xbb\xbf"
PY_SRC = "import os\nx = 1\n"


# --------------------------------------------------------------------------- #
# newline detection and normalisation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("text, expected", [
    ("a\r\nb\r\nc\n", "\r\n"),          # 2 CRLF vs 1 LF
    ("a\nb\nc\r\n", "\n"),              # 2 LF vs 1 CRLF
    ("a\rb\rc", "\r"),                  # lone CR only
    ("a\r\nb\nc\n", "\n"),              # 2 LF vs 1 CRLF
    ("a\r\nb\n", "\n"),                 # tie between CRLF and LF
    ("a\r\r\nb\rc\r\n", "\n"),          # 2 lone CR vs 2 CRLF: tie, so LF
    ("no newline", "\n"),
    ("", "\n"),
])
def test_detect_newline(text: str, expected: str) -> None:
    assert detect_newline(text) == expected


def test_detect_newline_counts_mixed_input() -> None:
    assert detect_newline("a\r\nb\r\nc\r\nd\n") == "\r\n"
    assert detect_newline("a\rb\rc\r\n") == "\r"


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_normalize_newlines_converts_every_line_end(newline: str) -> None:
    out = normalize_newlines("a\r\nb\rc\nd", newline)
    assert out == f"a{newline}b{newline}c{newline}d"


def test_normalize_newlines_keeps_text_without_newlines() -> None:
    assert normalize_newlines("plain", "\r\n") == "plain"


# --------------------------------------------------------------------------- #
# read_source: bytes, BOM, encoding refusal
# --------------------------------------------------------------------------- #
def test_read_source_records_bytes_bom_and_newline(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(BOM + b"x = 1\r\n")
    src = read_source(tmp_path, "a.py", suffixes=(".py",),
                      max_bytes=1024, error_cls=CodeEditError)
    assert src.bom is True
    assert src.text == "x = 1\r\n"
    assert src.newline == "\r\n"
    assert src.raw == BOM + b"x = 1\r\n"
    assert src.sha256 == hashlib.sha256(src.raw).hexdigest()


def test_read_source_refuses_escape_suffix_and_size(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "big.py").write_text("x = 1\n" * 100, encoding="utf-8")
    kw = dict(suffixes=(".py",), error_cls=CodeEditError)
    with pytest.raises(CodeEditError, match="escapes"):
        read_source(tmp_path, "../outside.py", max_bytes=1024, **kw)
    with pytest.raises(CodeEditError, match="not supported"):
        read_source(tmp_path, "a.txt", max_bytes=1024, **kw)
    with pytest.raises(CodeEditError, match="exceeds 10 bytes"):
        read_source(tmp_path, "big.py", max_bytes=10, **kw)
    with pytest.raises(CodeEditError, match="no such file"):
        read_source(tmp_path, "missing.py", max_bytes=1024, **kw)


def test_read_source_refuses_latin1_bytes(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(b"x = '\xe9'\n")
    with pytest.raises(CodeEditError, match="not valid UTF-8"):
        read_source(tmp_path, "a.py", suffixes=(".py",), max_bytes=1024,
                    error_cls=CodeEditError)


@pytest.mark.parametrize("cookie", [
    b"# -*- coding: latin-1 -*-\n",
    b"#!/usr/bin/env python\n# coding=cp1252\n",
])
def test_read_source_refuses_declared_non_utf8_encoding(
        tmp_path: Path, cookie: bytes) -> None:
    (tmp_path / "a.py").write_bytes(cookie + b"x = 1\n")
    with pytest.raises(CodeEditError, match="declares encoding"):
        read_source(tmp_path, "a.py", suffixes=(".py",), max_bytes=1024,
                    error_cls=CodeEditError)


def test_read_source_accepts_utf8_cookie(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(b"# -*- coding: utf-8 -*-\nx = 1\n")
    src = read_source(tmp_path, "a.py", suffixes=(".py",), max_bytes=1024,
                      error_cls=CodeEditError)
    assert src.bom is False


# --------------------------------------------------------------------------- #
# write path: TOCTOU, backups, base hash
# --------------------------------------------------------------------------- #
def test_toctou_change_between_read_and_replace_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "mod.py"
    p.write_text(PY_SRC, encoding="utf-8")
    real_current = txn._current_bytes

    def concurrent_rewrite(path: Path) -> bytes:
        path.write_bytes(b"concurrent = True\n")
        return real_current(path)

    monkeypatch.setattr(txn, "_current_bytes", concurrent_rewrite)
    with pytest.raises(CodeEditError, match="changed on disk"):
        apply_edit_script(tmp_path, {
            "file": "mod.py",
            "ops": [{"op": "replace_span", "start_line": 2, "start_col": 0,
                     "end_line": 3, "end_col": 0, "text": "x = 2\n"}],
        }, write=True)
    assert p.read_bytes() == b"concurrent = True\n"
    leftovers = [q.name for q in tmp_path.iterdir()
                 if q.name.endswith(".ocelot_tmp")]
    assert leftovers == []


def test_two_writes_in_one_second_keep_distinct_backups(tmp_path: Path) -> None:
    p = tmp_path / "mod.py"
    p.write_text("x = 1\n", encoding="utf-8")
    v0 = p.read_bytes()

    def set_x(value: int, base: str) -> dict:
        return {"file": "mod.py", "base_sha256": base, "ops": [
            {"op": "replace_span", "start_line": 1, "start_col": 0,
             "end_line": 2, "end_col": 0, "text": f"x = {value}\n"}]}

    first = apply_edit_script(tmp_path, set_x(2, hashlib.sha256(v0).hexdigest()),
                              write=True)
    v1 = p.read_bytes()
    second = apply_edit_script(tmp_path, set_x(3, first["new_sha256"]),
                               write=True)
    assert p.read_bytes() == b"x = 3\n"
    assert first["backup"] != second["backup"]
    assert Path(first["backup"]).read_bytes() == v0
    assert Path(second["backup"]).read_bytes() == v1


def test_base_sha_is_hash_of_bytes_on_disk(tmp_path: Path) -> None:
    p = tmp_path / "mod.py"
    p.write_bytes(PY_SRC.encode("utf-8"))
    r = apply_edit_script(tmp_path, {"file": "mod.py", "ops": [
        {"op": "replace_span", "start_line": 1, "start_col": 0,
         "end_line": 2, "end_col": 0, "text": "import sys\n"}]})
    assert r["base_sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert r["before"]["sha256"] == r["base_sha256"]
    with pytest.raises(CodeEditError, match="stale base"):
        apply_edit_script(tmp_path, {"file": "mod.py", "base_sha256": "0" * 64,
                                     "ops": [{"op": "replace_span",
                                              "start_line": 1, "start_col": 0,
                                              "end_line": 2, "end_col": 0,
                                              "text": "x\n"}]})


def test_bom_file_base_sha_covers_bom(tmp_path: Path) -> None:
    p = tmp_path / "mod.py"
    p.write_bytes(BOM + PY_SRC.encode("utf-8"))
    r = apply_edit_script(tmp_path, {"file": "mod.py", "ops": [
        {"op": "replace_span", "start_line": 1, "start_col": 0,
         "end_line": 2, "end_col": 0, "text": "import sys\n"}]})
    assert r["base_sha256"] == hashlib.sha256(BOM + PY_SRC.encode()).hexdigest()
    assert r["bom"] is True


# --------------------------------------------------------------------------- #
# no adapter keeps a private write path
# --------------------------------------------------------------------------- #
def test_adapters_write_only_through_the_txn_helper() -> None:
    for name in ADAPTERS:
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "from scripts.ocelot_edit_txn import" in text, name
        assert "os.replace(" not in text, name
        assert ".ocelot_tmp" not in text, name
        assert "shutil.copy2(" not in text, name
        assert "path.read_text(" not in text, name
        assert "path.read_bytes(" not in text, name


def test_read_source_refuses_lone_cr_line_endings(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(b"import os\rx = 1\r")
    with pytest.raises(CodeEditError, match="lone CR"):
        read_source(tmp_path, "a.py", suffixes=(".py",), max_bytes=1024,
                    error_cls=CodeEditError)


def test_code_edit_refuses_lone_cr_file_instead_of_crashing(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(b"import os\rdef f(a):\r    x = 1\r")
    with pytest.raises(CodeEditError, match="lone CR"):
        apply_edit_script(tmp_path, {"file": "a.py", "ops": [
            {"op": "replace_body", "symbol": "f", "text": "y = 2"}]})


# --------------------------------------------------------------------------- #
# dt-w4-fixes-b (review 5): PEP 263 cookie check applies to Python only
# --------------------------------------------------------------------------- #
def test_cookie_text_in_markdown_heading_is_not_an_encoding_declaration(
        tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_bytes(b"# Secure coding: rules\n\nBody.\n")
    src = read_source(tmp_path, "doc.md", suffixes=(".md",), max_bytes=1024,
                      error_cls=CodeEditError)
    assert src.text.startswith("# Secure coding: rules")


def test_cookie_like_line_in_json_is_not_an_encoding_declaration(
        tmp_path: Path) -> None:
    (tmp_path / "doc.json").write_bytes(b'{"note": "coding: x"}\n')
    src = read_source(tmp_path, "doc.json", suffixes=(".json",), max_bytes=1024,
                      error_cls=CodeEditError)
    assert src.text == '{"note": "coding: x"}\n'
    (tmp_path / "hash.json").write_bytes(b"# coding: x\n{}\n")
    src = read_source(tmp_path, "hash.json", suffixes=(".json",), max_bytes=1024,
                      error_cls=CodeEditError)
    assert src.text == "# coding: x\n{}\n"


def test_python_latin1_cookie_is_still_refused(tmp_path: Path) -> None:
    (tmp_path / "a.pyi").write_bytes(b"# -*- coding: latin-1 -*-\nx: int\n")
    with pytest.raises(CodeEditError, match="declares encoding"):
        read_source(tmp_path, "a.pyi", suffixes=(".pyi",), max_bytes=1024,
                    error_cls=CodeEditError)
