"""test_markdown_edit_migrated — section-addressed Markdown edits.

Markdown is a block graph: headings own spans, bodies are text. Edits target a
section title/path; the leaves outside the edited section are byte-identical,
including HTML comments and trailing spaces.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ocelot_code_edit import CodeEditError
from scripts.ocelot_markdown_edit import (
    apply_markdown_edit_script,
    headings,
    outline_markdown,
)
from scripts.ocelot_lossless import LosslessText
from scripts.ocelot_dev_memory import DevMemory, build_index


SOURCE = '''# Title

Intro paragraph.  
<!-- keep this comment -->

## Alpha

Alpha body.
A second line.

### Alpha child

Nested text.

## Beta

Beta body.

## Gamma

Gamma body.
'''


def test_outline_and_headings() -> None:
    hs = headings(SOURCE)
    assert [(h.level, h.title) for h in hs] == [
        (1, "Title"), (2, "Alpha"), (3, "Alpha child"),
        (2, "Beta"), (2, "Gamma")]
    out = outline_markdown(SOURCE)
    assert "## Alpha" in out["text"]
    assert "### Alpha child" in out["text"]


def test_roundtrip_is_lossless() -> None:
    assert LosslessText.from_lines(SOURCE).render() == SOURCE


def test_preview_apply_and_lossless(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text(SOURCE, encoding="utf-8")
    r = apply_markdown_edit_script(tmp_path, {
        "file": "doc.md",
        "ops": [{"op": "replace_section_body", "section": "Alpha",
                 "text": "New alpha body.\n\nWith two paragraphs."}],
    })
    assert r["applied"] is False
    assert p.read_text() == SOURCE
    assert "<!-- keep this comment -->" not in "".join(
        ln for ln in r["diff_view"].splitlines() if ln.startswith(("+", "-")))
    assert "### Alpha child" not in "".join(
        ln for ln in r["diff_view"].splitlines() if ln.startswith(("+", "-")))
    assert "+New alpha body." in r["diff_view"]


def test_insert_and_delete_section(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text(SOURCE, encoding="utf-8")
    r = apply_markdown_edit_script(tmp_path, {
        "file": "doc.md",
        "ops": [
            {"op": "insert_section_after", "section": "Beta", "level": 2,
             "title": "Delta", "text": "Delta body."},
            {"op": "delete_section", "section": "Gamma"},
        ],
    })
    assert "## Delta" in r["diff_view"]
    assert "-## Gamma" in r["diff_view"]
    from scripts.ocelot_markdown_edit import _apply_ops
    new_source, _ = _apply_ops(SOURCE, r["ops"])
    assert "## Beta" in new_source
    assert "## Delta" in new_source
    assert "## Gamma" not in new_source


def test_frontmatter(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text("---\ntitle: Old\n---\n\n# Body\n", encoding="utf-8")
    r = apply_markdown_edit_script(tmp_path, {
        "file": "doc.md",
        "ops": [{"op": "replace_frontmatter",
                 "text": "title: New\ntags: [a, b]"}],
    })
    assert "+title: New" in r["diff_view"]
    assert "-title: Old" in r["diff_view"]


def test_apply_backup_and_journal(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text(SOURCE, encoding="utf-8")
    build_index(tmp_path, tmp_path / "var" / "g.json",
                include_docs="features", include_git=False,
                include_scripts=False)
    mem = DevMemory(tmp_path / "var" / "g.json",
                    tmp_path / "var" / "j.jsonl")
    r = mem.edit({
        "file": "doc.md", "apply": True,
        "ops": [{"op": "replace_section_body", "section": "Beta",
                 "text": "Changed beta."}],
    }, task="edit beta")
    assert r["applied"] is True
    assert "Changed beta." in p.read_text()
    assert Path(r["backup"]).read_text() == SOURCE
    assert mem.journal_recent(1)[0]["kind"] == "edit"


def test_refusals(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text(SOURCE, encoding="utf-8")
    import pytest
    with pytest.raises(Exception, match="raw 'diff'"):
        apply_markdown_edit_script(tmp_path, {
            "file": "doc.md", "diff": "x", "ops": []})
    with pytest.raises(Exception, match="no section"):
        apply_markdown_edit_script(tmp_path, {
            "file": "doc.md",
            "ops": [{"op": "delete_section", "section": "Nope"}]})
    with pytest.raises(Exception, match="must include the heading"):
        apply_markdown_edit_script(tmp_path, {
            "file": "doc.md",
            "ops": [{"op": "replace_section", "section": "Alpha",
                     "text": "x"}]})


# --------------------------------------------------------------------------- #
# edit transaction: CRLF and encoding (dt-w1a-edit-txn)
# --------------------------------------------------------------------------- #
def test_crlf_section_replace_and_append_match_lf_result(tmp_path: Path) -> None:
    import re
    lf_src = SOURCE
    crlf_src = SOURCE.replace("\n", "\r\n")
    (tmp_path / "crlf.md").write_bytes(crlf_src.encode("utf-8"))
    (tmp_path / "lf.md").write_bytes(lf_src.encode("utf-8"))
    ops = [
        {"op": "replace_section_body", "section": "Alpha", "text": "New alpha."},
        {"op": "append_to_section", "section": "Gamma", "text": "Appended."},
    ]
    r = apply_markdown_edit_script(tmp_path, {"file": "crlf.md", "ops": ops},
                                   write=True)
    apply_markdown_edit_script(tmp_path, {"file": "lf.md", "ops": ops}, write=True)
    data = (tmp_path / "crlf.md").read_bytes()
    assert r["newline"] == "crlf"
    assert re.search(rb"(?<!\r)\n", data) is None
    assert data.decode("utf-8") == (tmp_path / "lf.md").read_text(
        encoding="utf-8").replace("\n", "\r\n")
    assert "Appended.\r\n" in data.decode("utf-8")


def test_latin1_markdown_is_refused_with_utf8_message(tmp_path: Path) -> None:
    import pytest
    from scripts.ocelot_code_edit import CodeEditError
    (tmp_path / "doc.md").write_bytes(b"# T\n\xe9\n")
    with pytest.raises(CodeEditError, match="not valid UTF-8"):
        apply_markdown_edit_script(tmp_path, {"file": "doc.md", "ops": [
            {"op": "replace_section_body", "section": "T", "text": "x"}]})


def test_two_appends_to_one_section_keep_op_order(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text("# T\n\n## S\n\nbody\n", encoding="utf-8")
    apply_markdown_edit_script(tmp_path, {"file": "doc.md", "ops": [
        {"op": "append_to_section", "section": "S", "text": "one"},
        {"op": "append_to_section", "section": "S", "text": "two"}]},
        write=True)
    assert p.read_text(encoding="utf-8") == "# T\n\n## S\n\nbody\none\ntwo\n"


def test_crlf_frontmatter_is_replaced_in_place(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_bytes(b"---\r\ntitle: Old\r\n---\r\n# Body\r\n")
    apply_markdown_edit_script(tmp_path, {"file": "doc.md", "ops": [
        {"op": "replace_frontmatter", "text": "title: New"}]}, write=True)
    assert p.read_bytes() == b"---\r\ntitle: New\r\n---\r\n# Body\r\n"


def test_four_dashes_do_not_close_frontmatter(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text("---\ntitle: Old\n----\nkey: 1\n---\n# Body\n", encoding="utf-8")
    apply_markdown_edit_script(tmp_path, {"file": "doc.md", "ops": [
        {"op": "replace_frontmatter", "text": "title: New"}]}, write=True)
    assert p.read_text(encoding="utf-8") == "---\ntitle: New\n---\n# Body\n"


def test_frontmatter_closed_only_by_four_dashes_is_refused(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text("---\ntitle: Old\n----\n", encoding="utf-8")
    with pytest.raises(CodeEditError, match="not closed"):
        apply_markdown_edit_script(tmp_path, {"file": "doc.md", "ops": [
            {"op": "replace_frontmatter", "text": "title: New"}]})
