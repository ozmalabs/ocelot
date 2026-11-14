"""test_markdown_edit_migrated — section-addressed Markdown edits.

Markdown is a block graph: headings own spans, bodies are text. Edits target a
section title/path; the leaves outside the edited section are byte-identical,
including HTML comments and trailing spaces.
"""
from __future__ import annotations

from pathlib import Path

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
