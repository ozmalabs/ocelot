"""test_repo_map_migrated — tree-sitter tags, PageRank, incremental cache.

The map is a reading aid: definitions/references from the grammar's own
tags.scm, a file reference graph, task-weighted PageRank, and a three-tier
render inside a token budget. The tag cache is content-hash incremental.
"""
from __future__ import annotations

from pathlib import Path

from scripts.ocelot_repo_map import (
    extract_tags,
    impact,
    repo_map,
    update_tag_cache,
)


def _fixture(root: Path) -> None:
    (root / "a.py").write_text(
        "def alpha(x):\n"
        "    return x + 1\n"
        "\n"
        "def beta():\n"
        "    return alpha(1)\n",
        encoding="utf-8")
    (root / "b.py").write_text(
        "from a import alpha\n"
        "\n"
        "def use():\n"
        "    return alpha(2)\n",
        encoding="utf-8")


def test_python_tags() -> None:
    tags = extract_tags("a.py",
                        "def alpha(x):\n    return x + 1\n"
                        "def beta():\n    return alpha(1)\n")
    defs = {t["name"] for t in tags if t["kind"] == "def"}
    refs = {t["name"] for t in tags if t["kind"] == "ref"}
    assert {"alpha", "beta"} <= defs
    assert "alpha" in refs


def test_rust_and_lua_tags() -> None:
    rust = extract_tags("x.rs", "fn add(a: i32, b: i32) -> i32 { a + b }\n"
                                "fn main() { let x = add(1, 2); }\n")
    assert any(t["kind"] == "def" and t["name"] == "add" for t in rust)
    assert any(t["kind"] == "ref" and t["name"] == "add" for t in rust)
    lua = extract_tags("x.lua", "function add(a, b)\n  return a + b\nend\n"
                                "local n = add(1, 2)\n")
    assert any(t["kind"] == "def" and t["name"] == "add" for t in lua)
    assert any(t["kind"] == "ref" and t["name"] == "add" for t in lua)


def test_incremental_cache(tmp_path: Path) -> None:
    _fixture(tmp_path)
    cache_path = tmp_path / "var" / "tags.json"
    files = ["a.py", "b.py"]
    _cache, first = update_tag_cache(tmp_path, cache_path=cache_path,
                                     files=files)
    assert first["parsed"] == 2 and first["reused"] == 0
    _cache, second = update_tag_cache(tmp_path, cache_path=cache_path,
                                      files=files)
    assert second["parsed"] == 0 and second["reused"] == 2
    # Content change re-parses exactly one file.
    (tmp_path / "a.py").write_text("def alpha(x):\n    return x + 2\n",
                                   encoding="utf-8")
    _cache, third = update_tag_cache(tmp_path, cache_path=cache_path,
                                     files=files)
    assert third["parsed"] == 1 and third["reused"] == 1


def test_repo_map_ranks_task_file_and_respects_budget(tmp_path: Path) -> None:
    _fixture(tmp_path)
    r = repo_map(tmp_path, task="change alpha behavior", budget_tokens=300,
                 cache_path=tmp_path / "var" / "tags.json",
                 files=["a.py", "b.py"])
    assert r["ok"] is True
    assert r["files"]
    assert r["files"][0]["path"] == "a.py"
    assert r["estimated_tokens"] <= 300 or len(r["files"]) == 1
    assert "alpha" in r["markdown"]


def test_impact(tmp_path: Path) -> None:
    _fixture(tmp_path)
    cache = tmp_path / "var" / "tags.json"
    r = impact(tmp_path, file="a.py", depth=2, cache_path=cache,
               files=["a.py", "b.py"])
    assert r["ok"] is True
    assert [x["path"] for x in r["impacted"]] == ["b.py"]
    assert r["impacted"][0]["depth"] == 1
