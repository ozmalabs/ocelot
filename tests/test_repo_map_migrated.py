"""test_repo_map_migrated — tree-sitter tags, PageRank, incremental cache.

The map is a reading aid: definitions/references from the grammar's own
tags.scm, a file reference graph, task-weighted PageRank, and a three-tier
render inside a token budget. The tag cache is content-hash incremental.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import ocelot_repo_map as repo_map_module
from scripts.ocelot_repo_map import (
    clear_memos,
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


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_same_second_same_size_edit_is_not_served_stale(tmp_path: Path) -> None:
    # R1: same length, same second, same mtime_ns: only the content hash can
    # tell the two versions apart.
    a = tmp_path / "a.py"
    a.write_text("def foo():\n    return 1\n", encoding="utf-8")
    cache_path = tmp_path / "var" / "tags.json"
    pinned = a.stat().st_mtime_ns
    update_tag_cache(tmp_path, cache_path=cache_path, files=["a.py"])
    a.write_text("def bar():\n    return 1\n", encoding="utf-8")
    os.utime(a, ns=(pinned, pinned))
    cache, stats = update_tag_cache(tmp_path, cache_path=cache_path,
                                    files=["a.py"])
    names = {t["name"] for t in cache["files"]["a.py"]["tags"]}
    assert "bar" in names and "foo" not in names
    assert stats["parsed"] == 1


def test_backend_failure_is_not_cached(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n",
                                   encoding="utf-8")
    cache_path = tmp_path / "var" / "tags.json"
    real = repo_map_module.extract_tags_status
    calls = {"n": 0}

    def flaky(path, source):
        calls["n"] += 1
        if calls["n"] == 1:
            return [], "boom"
        return real(path, source)

    monkeypatch.setattr(repo_map_module, "extract_tags_status", flaky)
    cache, first = update_tag_cache(tmp_path, cache_path=cache_path,
                                    files=["a.py"])
    assert first["failed"] == 1 and first["parsed"] == 0
    assert first["errors"] == ["a.py: boom"]
    assert "a.py" not in cache["files"]
    if cache_path.exists():
        assert "a.py" not in json.loads(cache_path.read_text())["files"]
    cache, second = update_tag_cache(tmp_path, cache_path=cache_path,
                                     files=["a.py"])
    assert second["parsed"] == 1 and second["failed"] == 0
    assert any(t["name"] == "alpha" for t in cache["files"]["a.py"]["tags"])


def test_fingerprint_change_forces_reextract(tmp_path: Path,
                                             monkeypatch) -> None:
    _fixture(tmp_path)
    cache_path = tmp_path / "var" / "tags.json"
    update_tag_cache(tmp_path, cache_path=cache_path, files=["a.py"])
    _cache, same = update_tag_cache(tmp_path, cache_path=cache_path,
                                    files=["a.py"])
    assert same["parsed"] == 0 and same["reused"] == 1
    monkeypatch.setattr(repo_map_module, "extractor_fingerprint",
                        lambda _path: "fingerprint-changed")
    _cache, changed = update_tag_cache(tmp_path, cache_path=cache_path,
                                       files=["a.py"])
    assert changed["parsed"] == 1


def test_subset_call_does_not_shrink_cache(tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path)
    (tmp_path / "c.py").write_text("def gamma():\n    return 3\n",
                                   encoding="utf-8")
    cache_path = tmp_path / "var" / "tags.json"
    # Point the full scan at the fixture root instead of the repo's dirs.
    monkeypatch.setattr(repo_map_module, "SOURCE_DIRS", (".",))
    full, _ = update_tag_cache(tmp_path, cache_path=cache_path)
    assert set(full["files"]) == {"a.py", "b.py", "c.py"}
    subset, stats = update_tag_cache(tmp_path, cache_path=cache_path,
                                     files=["a.py"])
    on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
    assert len(on_disk["files"]) == 3
    assert set(subset["files"]) == {"a.py"}
    assert subset["root_hash"] != full["root_hash"]
    assert stats["reused"] == 1 and stats["parsed"] == 0


def test_mtime_refresh_is_saved_and_then_uses_fast_path(
        tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path)
    a = tmp_path / "a.py"
    cache_path = tmp_path / "var" / "tags.json"
    base = time.time_ns()
    clock = {"now": base}
    monkeypatch.setattr(repo_map_module.time, "time_ns", lambda: clock["now"])
    os.utime(a, ns=(base, base))
    update_tag_cache(tmp_path, cache_path=cache_path, files=["a.py"])
    # Same content, new mtime, one second later. The content is re-hashed,
    # the refreshed mtime is written to disk.
    touched = base - 5_000_000_000
    os.utime(a, ns=(touched, touched))
    clock["now"] = base + 1_000_000_000
    _cache, refresh = update_tag_cache(tmp_path, cache_path=cache_path,
                                       files=["a.py"])
    assert refresh["reused"] == 1 and refresh["parsed"] == 0
    on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
    assert on_disk["files"]["a.py"]["mtime_ns"] == touched
    # Outside the racy window (checked - mtime >= RACY_NS) the next call must
    # not read or hash the file.

    def no_hash(_text: str) -> str:
        raise AssertionError("fast path must not hash the file")

    monkeypatch.setattr(repo_map_module, "_sha256", no_hash)
    clock["now"] = base + 2_000_000_000
    _cache, fast = update_tag_cache(tmp_path, cache_path=cache_path,
                                    files=["a.py"])
    assert fast["reused"] == 1


def test_racy_entry_is_rehashed_before_window_elapses(
        tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path)
    a = tmp_path / "a.py"
    cache_path = tmp_path / "var" / "tags.json"
    base = time.time_ns()
    clock = {"now": base}
    monkeypatch.setattr(repo_map_module.time, "time_ns", lambda: clock["now"])
    os.utime(a, ns=(base, base))
    update_tag_cache(tmp_path, cache_path=cache_path, files=["a.py"])
    clock["now"] = base + 1_000_000_000
    hashed = {"n": 0}
    real_hash = repo_map_module._sha256

    def counting(text: str) -> str:
        hashed["n"] += 1
        return real_hash(text)

    monkeypatch.setattr(repo_map_module, "_sha256", counting)
    # Same mtime and size as the entry, but checked 1 s after the mtime: the
    # racy rule forces a hash even though the stat looks unchanged.
    _cache, racy = update_tag_cache(tmp_path, cache_path=cache_path,
                                    files=["a.py"])
    assert hashed["n"] == 1 and racy["reused"] == 1


def _write_graph_fixture(root: Path) -> None:
    (root / "base.py").write_text(
        "def shared_compute(value):\n    return value\n", encoding="utf-8")
    for i in range(8):
        (root / f"mod{i}.py").write_text(
            "from base import shared_compute\n\n"
            f"def job_{i}(value):\n"
            f"    return shared_compute(value) + helper_{i % 3}()\n\n"
            f"def helper_{i % 3}():\n"
            "    return Widget()\n\n"
            "class Widget:\n"
            f"    def run(self):\n        return job_{i}(1)\n",
            encoding="utf-8")


_DETERMINISM_SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[1])
from scripts.ocelot_repo_map import repo_map
root, cache, files = sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
result = repo_map(root, task="shared compute widget job", budget_tokens=800,
                  cache_path=cache, files=files)
print(json.dumps({"files": result["files"], "markdown": result["markdown"],
                  "graph": result["graph"]}, sort_keys=True))
"""


def test_repo_map_output_is_identical_across_hash_seeds(tmp_path: Path) -> None:
    _write_graph_fixture(tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.py"))
    outputs = []
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        proc = subprocess.run(
            [sys.executable, "-c", _DETERMINISM_SCRIPT, str(REPO_ROOT),
             str(tmp_path), str(tmp_path / f"tags_{seed}.json"),
             json.dumps(files)],
            cwd=str(REPO_ROOT), env=env, capture_output=True, text=True,
            check=False)
        assert proc.returncode == 0, proc.stderr
        outputs.append(proc.stdout)
    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0])["files"]


def test_pagerank_ranks_sum_to_one_with_dangling_node() -> None:
    graph = {
        "defines": {}, "references": {}, "definitions": {},
        "edges": [
            {"src": "a.py", "tgt": "b.py", "weight": 1.0},
            {"src": "b.py", "tgt": "c.py", "weight": 1.0},
            {"src": "d.py", "tgt": "c.py", "weight": 2.0},
        ],
    }
    for task in ("", "alpha pagerank"):
        ranks = repo_map_module.personalized_pagerank(graph, task=task)
        assert set(ranks) == {"a.py", "b.py", "c.py", "d.py"}
        assert abs(sum(ranks.values()) - 1.0) < 1e-9


BASE_COMMIT = "f88fcfda"


def _load_base_module(tmp_path: Path):
    """The pre-W2-B repo_map module, read from git history and imported under
    another name. It is the reference for output identity (gate 1a)."""
    try:
        source = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show",
             f"{BASE_COMMIT}:scripts/ocelot_repo_map.py"],
            capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip(f"base commit {BASE_COMMIT} is not available")
    path = tmp_path / "base_ocelot_repo_map.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("base_ocelot_repo_map", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _without_timing(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k != "cache"}


def test_output_matches_base_implementation(tmp_path: Path) -> None:
    base = _load_base_module(tmp_path / "base")
    _write_graph_fixture(tmp_path)
    _fixture(tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.py"))
    assert len(files) >= 10
    clear_memos()
    cases = [
        {"task": "", "budget_tokens": 1500},
        {"task": "shared compute widget job", "budget_tokens": 800},
        {"task": "change alpha behavior", "budget_tokens": 300,
         "focus_files": ["a.py"]},
        {"task": "widget", "budget_tokens": 2000,
         "focus_files": ["mod3.py"]},
    ]
    for i, kwargs in enumerate(cases):
        expected = base.repo_map(tmp_path, cache_path=tmp_path / f"base_{i}.json",
                                 files=files, **kwargs)
        actual = repo_map(tmp_path, cache_path=tmp_path / f"new_{i}.json",
                          files=files, **kwargs)
        assert _without_timing(actual) == _without_timing(expected), kwargs
    for i, (target, depth) in enumerate([("base.py", 1), ("base.py", 3),
                                         ("a.py", 2), ("missing.py", 2)]):
        expected = base.impact(tmp_path, file=target, depth=depth,
                               cache_path=tmp_path / f"ibase_{i}.json",
                               files=files)
        actual = impact(tmp_path, file=target, depth=depth,
                        cache_path=tmp_path / f"inew_{i}.json", files=files)
        assert _without_timing(actual) == _without_timing(expected), target


def test_graph_memo_reuses_until_content_changes(tmp_path: Path,
                                                 monkeypatch) -> None:
    _fixture(tmp_path)
    clear_memos()
    builds = {"n": 0}
    real_build = repo_map_module.build_reference_graph

    def counting_build(cache):
        builds["n"] += 1
        return real_build(cache)

    monkeypatch.setattr(repo_map_module, "build_reference_graph",
                        counting_build)
    cache_path = tmp_path / "var" / "tags.json"
    files = ["a.py", "b.py"]
    first = repo_map(tmp_path, cache_path=cache_path, files=files)
    assert builds["n"] == 1
    second = repo_map(tmp_path, cache_path=cache_path, files=files)
    assert builds["n"] == 1
    assert second["files"] == first["files"]

    (tmp_path / "a.py").write_text(
        "def alpha(x):\n    return x + 1\n\n"
        "def gamma_extra():\n    return alpha(3)\n", encoding="utf-8")
    third = repo_map(tmp_path, cache_path=cache_path, files=files)
    assert builds["n"] == 2
    assert "gamma_extra" in third["markdown"]
    impacted = impact(tmp_path, file="a.py", depth=2, cache_path=cache_path,
                      files=files)
    assert builds["n"] == 2
    assert [x["path"] for x in impacted["impacted"]] == ["b.py"]


def _strip_timing_fields(files: dict) -> dict:
    return {rel: {k: v for k, v in entry.items()
                  if k not in ("mtime_ns", "checked_ns")}
            for rel, entry in files.items()}


def test_parallel_cold_index_matches_serial(tmp_path: Path,
                                            monkeypatch) -> None:
    _write_graph_fixture(tmp_path)
    _fixture(tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.py"))
    monkeypatch.setenv("OCELOT_INDEX_WORKERS", "1")
    serial_path = tmp_path / "serial.json"
    _cache, serial = update_tag_cache(tmp_path, cache_path=serial_path,
                                      files=files)
    assert serial["parallel"] == 1

    monkeypatch.setattr(repo_map_module, "PARALLEL_MIN_FILES", 1)
    monkeypatch.setenv("OCELOT_INDEX_WORKERS", "2")
    parallel_path = tmp_path / "parallel.json"
    _cache, parallel = update_tag_cache(tmp_path, cache_path=parallel_path,
                                        files=files)
    assert parallel["parallel"] == 2
    assert parallel["parsed"] == serial["parsed"] == len(files)

    serial_doc = json.loads(serial_path.read_text(encoding="utf-8"))
    parallel_doc = json.loads(parallel_path.read_text(encoding="utf-8"))
    assert serial_doc["root_hash"] == parallel_doc["root_hash"]
    assert (_strip_timing_fields(serial_doc["files"])
            == _strip_timing_fields(parallel_doc["files"]))


def test_pool_failure_falls_back_to_serial(tmp_path: Path,
                                           monkeypatch) -> None:
    _write_graph_fixture(tmp_path)
    _fixture(tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.py"))
    monkeypatch.setattr(repo_map_module, "PARALLEL_MIN_FILES", 1)
    monkeypatch.setenv("OCELOT_INDEX_WORKERS", "2")

    class BrokenPool:
        def __init__(self, *args, **kwargs):
            raise OSError("no processes for you")

    monkeypatch.setattr(repo_map_module.concurrent.futures,
                        "ProcessPoolExecutor", BrokenPool)
    cache_path = tmp_path / "fallback.json"
    _cache, stats = update_tag_cache(tmp_path, cache_path=cache_path,
                                     files=files)
    assert stats["parallel"].startswith("fallback: OSError")
    assert stats["parsed"] == len(files) and stats["failed"] == 0
    doc = json.loads(cache_path.read_text(encoding="utf-8"))
    assert set(doc["files"]) == set(files)


SEARCH_BASE_COMMIT = "a6df57f0d4b594564d993495d6d38a1b1be3170f"


def _load_module_at(commit: str, rel_path: str, directory: Path,
                    module_name: str):
    """A module as it existed at `commit`, imported under `module_name`."""
    try:
        source = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{rel_path}"],
            capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip(f"commit {commit} is not available")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{module_name}.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_walk_fixture(root: Path) -> None:
    def put(rel: str, text: str = "x = 1\n") -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    put("pkg/a.py")
    put("pkg/Upper.PY")
    put("pkg/notes.txt")
    put("pkg/sub/deep/b.rs", "fn b() {}\n")
    put("pkg/sub/deep/z.py")
    put("pkg/__pycache__/c.py")
    put("pkg/build/d.py")
    put("pkg/.hidden/e.py")
    put("pkg/big.py", "x" * (2 * 1024 * 1024 + 1))
    put("outside/x.py")
    put("lib/lib1.py")
    put("lib/lib2.py")
    # Symlinks: a file pointing outside root, a file pointing inside root,
    # a directory pointing inside root, and a dangling link.
    os.symlink(root.parent / "outside" / "x.py", root / "pkg" / "escape.py")
    os.symlink(root / "lib" / "lib1.py", root / "pkg" / "alias.py")
    os.symlink(root / "lib", root / "pkg" / "linkdir")
    os.symlink(root / "missing.py", root / "pkg" / "dangling.py")


def test_source_files_matches_base_walk(tmp_path: Path, monkeypatch) -> None:
    base = _load_module_at(SEARCH_BASE_COMMIT, "scripts/ocelot_repo_map.py",
                           tmp_path / "base", "base_repo_map_a6")
    root = tmp_path / "repo"
    _write_walk_fixture(root)
    for dirs in (("pkg", "lib"), (".",)):
        monkeypatch.setattr(repo_map_module, "SOURCE_DIRS", dirs)
        monkeypatch.setattr(base, "SOURCE_DIRS", dirs)
        expected = base._source_files(root)
        actual = repo_map_module._source_files(root)
        assert actual == expected, dirs

    monkeypatch.setattr(repo_map_module, "SOURCE_DIRS", ("pkg", "lib"))
    files = repo_map_module._source_files(root)
    assert "pkg/a.py" in files
    assert "pkg/sub/deep/b.rs" in files
    assert "pkg/sub/deep/z.py" in files
    assert "lib/lib1.py" in files
    # The alias resolves inside root, so it is listed under its target.
    assert "lib/lib1.py" in files and "pkg/alias.py" not in files
    assert "pkg/Upper.PY" not in files
    assert "pkg/notes.txt" not in files
    assert "pkg/big.py" not in files
    assert "pkg/escape.py" not in files
    assert "pkg/dangling.py" not in files
    assert not any(f.startswith("pkg/linkdir/") for f in files)
    assert not any("__pycache__" in f or "/build/" in f for f in files)
