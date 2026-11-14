"""test_json_edit_migrated — span-preserving JSON path edits.

A seed manifest is a document tree; editing it must not re-render the whole
file. These tests assert that only the target span changes and that the
surrounding long description/indentation is byte-identical.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ocelot_json_edit import apply_json_edit_script, outline_json
from scripts.ocelot_dev_memory import DevMemory, build_index


SOURCE = '''{
 "id": "demo",
 "version": "1.0.0",
 "description": "a long description that must not be reformatted",
 "nodes": [
  {
   "local_id": 1,
   "type": "Concept",
   "attrs": {
    "name": "alpha",
    "n": 1
   }
  },
  {
   "local_id": 2,
   "type": "Concept",
   "attrs": {
    "name": "beta"
   }
  }
 ],
 "rules": []
}
'''


def _fixture(root: Path) -> Path:
    p = root / "seeds" / "demo.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(SOURCE, encoding="utf-8")
    return p


def test_outline() -> None:
    out = outline_json(SOURCE)
    assert "version: 1.0.0" in out["text"]
    assert "nodes: list[2]" in out["text"]
    assert "rules: list[0]" in out["text"]


def test_set_and_merge_are_local(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    r = apply_json_edit_script(tmp_path, {
        "file": "seeds/demo.json",
        "ops": [
            {"op": "set", "path": ["version"], "value": "1.1.0"},
            {"op": "merge", "path": ["nodes", 0, "attrs"],
             "value": {"n": 2, "tag": "x"}},
        ],
    })
    assert r["applied"] is False
    assert p.read_text() == SOURCE
    # The untouched long description must not appear as a changed line.
    changed = [ln for ln in r["diff_view"].splitlines()
               if ln.startswith(("+", "-")) and "long description" in ln]
    assert changed == []
    assert '+ "version": "1.1.0"' in r["diff_view"]
    assert '+    "tag": "x"' in r["diff_view"]


def test_append_node_and_rule(tmp_path: Path) -> None:
    _fixture(tmp_path)
    r = apply_json_edit_script(tmp_path, {
        "file": "seeds/demo.json",
        "ops": [
            {"op": "append", "path": ["nodes"],
             "value": {"local_id": 3, "type": "Concept",
                       "attrs": {"name": "gamma"}}},
            {"op": "append", "path": ["rules"],
             "value": {"name": "demo_rule"}},
        ],
    })
    assert '"name": "gamma"' in r["diff_view"]
    assert '"name": "demo_rule"' in r["diff_view"]
    # The result is valid JSON with three nodes and one rule.
    # Reconstruct from the preview by applying it to the fixture in memory.
    from scripts.ocelot_json_edit import _apply_ops
    new_source, _ = _apply_ops(SOURCE, r["ops"])
    obj = json.loads(new_source)
    assert len(obj["nodes"]) == 3
    assert obj["rules"] == [{"name": "demo_rule"}]


def test_delete_node(tmp_path: Path) -> None:
    _fixture(tmp_path)
    r = apply_json_edit_script(tmp_path, {
        "file": "seeds/demo.json",
        "ops": [{"op": "delete", "path": ["nodes", 1]}],
    })
    from scripts.ocelot_json_edit import _apply_ops
    new_source, _ = _apply_ops(SOURCE, r["ops"])
    obj = json.loads(new_source)
    assert [n["attrs"]["name"] for n in obj["nodes"]] == ["alpha"]


def test_apply_backup_and_journal(tmp_path: Path) -> None:
    p = _fixture(tmp_path)
    build_index(tmp_path, tmp_path / "var" / "g.json",
                include_docs="none", include_git=False,
                include_scripts=False)
    mem = DevMemory(tmp_path / "var" / "g.json",
                    tmp_path / "var" / "j.jsonl")
    r = mem.edit({
        "file": "seeds/demo.json",
        "apply": True,
        "ops": [{"op": "set", "path": ["version"], "value": "1.2.0"}],
    }, task="bump demo")
    assert r["applied"] is True
    assert '"version": "1.2.0"' in p.read_text()
    assert Path(r["backup"]).read_text() == SOURCE
    recent = mem.journal_recent(1)[0]
    assert recent["kind"] == "edit"
    assert recent["task"] == "bump demo"


def test_refusals(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(Exception, match="raw 'diff'"):
        apply_json_edit_script(tmp_path, {
            "file": "seeds/demo.json", "diff": "x", "ops": []})
    with pytest.raises(Exception, match="stale base"):
        apply_json_edit_script(tmp_path, {
            "file": "seeds/demo.json", "base_sha256": "0" * 64,
            "ops": [{"op": "set", "path": ["version"], "value": "2"}]})
    with pytest.raises(Exception, match="no JSON key"):
        apply_json_edit_script(tmp_path, {
            "file": "seeds/demo.json",
            "ops": [{"op": "set", "path": ["missing"], "value": 1}]})


# --------------------------------------------------------------------------- #
# edit transaction: CRLF, BOM and encoding (dt-w1a-edit-txn)
# --------------------------------------------------------------------------- #
def test_crlf_set_and_merge_match_lf_result_and_stay_crlf(tmp_path: Path) -> None:
    import re
    crlf_src = SOURCE.replace("\n", "\r\n")
    (tmp_path / "crlf.json").write_bytes(crlf_src.encode("utf-8"))
    (tmp_path / "lf.json").write_bytes(SOURCE.encode("utf-8"))
    ops = [
        {"op": "set", "path": ["version"], "value": "2.0.0"},
        {"op": "merge", "path": ["nodes", 1, "attrs"], "value": {"tag": "b"}},
    ]
    r = apply_json_edit_script(tmp_path, {"file": "crlf.json", "ops": ops},
                               write=True)
    apply_json_edit_script(tmp_path, {"file": "lf.json", "ops": ops}, write=True)
    data = (tmp_path / "crlf.json").read_bytes()
    assert r["newline"] == "crlf"
    assert re.search(rb"(?<!\r)\n", data) is None
    assert data.decode("utf-8") == (tmp_path / "lf.json").read_text(
        encoding="utf-8").replace("\n", "\r\n")
    assert '"tag": "b"' in data.decode("utf-8")


def test_bom_json_keeps_bom_and_edits(tmp_path: Path) -> None:
    p = tmp_path / "demo.json"
    p.write_bytes(b"\xef\xbb\xbf" + SOURCE.encode("utf-8"))
    r = apply_json_edit_script(tmp_path, {"file": "demo.json", "ops": [
        {"op": "set", "path": ["version"], "value": "2.0.0"}]}, write=True)
    assert r["bom"] is True
    data = p.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    assert '"version": "2.0.0"' in data[3:].decode("utf-8")


def test_latin1_json_is_refused_with_utf8_message(tmp_path: Path) -> None:
    from scripts.ocelot_code_edit import CodeEditError
    (tmp_path / "demo.json").write_bytes(b'{"id": "\xe9"}\n')
    with pytest.raises(CodeEditError, match="not valid UTF-8"):
        apply_json_edit_script(tmp_path, {"file": "demo.json", "ops": [
            {"op": "set", "path": ["id"], "value": "x"}]})
