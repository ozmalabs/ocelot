"""test_code_search_migrated — lexical hybrid search over the repo-map cache.

BM25 over file paths, definition symbols, and source lines, fused with
repo-map PageRank by reciprocal rank fusion. No embeddings, network, or model.
"""
from __future__ import annotations

import importlib.util
import json
import marshal
import os
import subprocess
from pathlib import Path

import pytest

from scripts import ocelot_code_search as search_module
from scripts import ocelot_repo_map as repo_map_module
from scripts.ocelot_code_search import (
    BM25_B,
    BM25_K1,
    GRAPH_WEIGHT,
    MAX_SNIPPET_CHARS,
    RRF_K,
    _competition_ranks,
    code_search,
    search_side_cache_path,
)


def _write(root: Path, files: dict[str, str]) -> list[str]:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return sorted(files)


def _fixture(root: Path) -> list[str]:
    return _write(root, {
        "a.py": (
            "def alpha(x):\n"
            '    """Return a frobnicated value for the retry budget."""\n'
            "    return x\n"
            "\n"
            "def beta():\n"
            "    return alpha(1)\n"
        ),
        "b.py": (
            "def gamma():\n"
            "    return 2\n"
        ),
    })


def _fusion_fixture(root: Path) -> list[str]:
    files = {
        "hub.py": (
            "def hub_core():\n"
            "    # needle\n"
            "    return 1\n"
            "\n"
            "def hub_extra():\n"
            "    return 2\n"
        ),
        "plain.py": (
            "def plain():\n"
            '    needle = "needle " * 10\n'
            "    return needle\n"
        ),
        "aaa.py": (
            "def aaa():\n"
            "    return 3\n"
        ),
    }
    for i in range(6):
        files[f"user{i}.py"] = (
            "from hub import hub_core\n"
            "\n"
            f"def user{i}():\n"
            "    return hub_core()\n"
        )
    return _write(root, files)


def _cache(root: Path) -> Path:
    return root / "var" / "tags.json"


def _tie_fixture(root: Path) -> list[str]:
    """Two files with identical lexical content. Both defined names are
    referenced, and ``tie_b`` receives one more reference, so the graph is the
    only thing that separates the pair."""
    return _write(root, {
        "tie_a.py": (
            "def alpha_fn():\n"
            "    # needle\n"
            "    return 1\n"
        ),
        "tie_b.py": (
            "def beta_fn():\n"
            "    # needle\n"
            "    return 1\n"
        ),
        "hub.py": (
            "def hub_run():\n"
            "    return alpha_fn() + beta_fn()\n"
        ),
        "hub2.py": (
            "def hub_more():\n"
            "    return beta_fn()\n"
        ),
    })


def test_symbol_and_doc_comment_queries(tmp_path: Path) -> None:
    files = _fixture(tmp_path)

    symbol = code_search(tmp_path, "alpha", cache_path=_cache(tmp_path),
                         files=files)
    assert symbol["ok"] is True
    assert symbol["n"] >= 1
    top = symbol["results"][0]
    assert top["path"] == "a.py"
    assert "alpha" in {s["name"] for s in top["symbols"]}
    assert top["bm25"] > 0 and top["score"] > 0

    doc = code_search(tmp_path, "frobnicated", cache_path=_cache(tmp_path),
                      files=files)
    hit = doc["results"][0]
    assert hit["path"] == "a.py"
    assert hit["line"] == 2
    assert "frobnicated" in hit["snippet"]
    assert len(hit["snippet"]) <= MAX_SNIPPET_CHARS


def test_default_file_discovery_on_flat_fixture(tmp_path: Path) -> None:
    _fixture(tmp_path)
    result = code_search(tmp_path, "alpha", cache_path=_cache(tmp_path))
    assert result["ok"] is True
    assert result["results"]
    assert result["results"][0]["path"] == "a.py"


def test_graph_prior_breaks_ties_but_not_a_lexical_lead(tmp_path: Path) -> None:
    files = _fusion_fixture(tmp_path)
    result = code_search(tmp_path, "needle", cache_path=_cache(tmp_path),
                         files=files)
    by_path = {item["path"]: item for item in result["results"]}
    assert set(by_path) == {"hub.py", "plain.py"}

    # The repeated literal leads lexically. The referenced hub leads on
    # PageRank, but the graph term is weighted, so the lexical leader stays
    # first.
    assert by_path["plain.py"]["bm25"] > by_path["hub.py"]["bm25"]
    assert by_path["hub.py"]["graph"] > by_path["plain.py"]["graph"]
    assert by_path["plain.py"]["bm25_rank"] == 1
    assert by_path["hub.py"]["bm25_rank"] == 2
    assert by_path["hub.py"]["graph_rank"] == 1
    assert result["results"][0]["path"] == "plain.py"

    plain_graph_rank = by_path["plain.py"]["graph_rank"]
    assert plain_graph_rank is not None and plain_graph_rank >= 2
    expected = round(1.0 / (RRF_K + 1)
                     + GRAPH_WEIGHT / (RRF_K + plain_graph_rank), 6)
    assert result["results"][0]["score"] == expected
    assert result["fusion"] == {"rrf_k": RRF_K, "graph_weight": GRAPH_WEIGHT}
    scores = [item["score"] for item in result["results"]]
    assert scores == sorted(scores, reverse=True)

    # Second fixture: two files tie on BM25. Only the graph term separates
    # them, so the file with the higher PageRank ranks first.
    tie_files = _tie_fixture(tmp_path / "tie")
    tied = code_search(tmp_path / "tie", "needle",
                       cache_path=tmp_path / "tie" / "var" / "tags.json",
                       files=tie_files)
    tie_by_path = {item["path"]: item for item in tied["results"]}
    assert tie_by_path["tie_a.py"]["bm25"] == tie_by_path["tie_b.py"]["bm25"]
    assert tie_by_path["tie_b.py"]["graph"] > tie_by_path["tie_a.py"]["graph"]
    assert tied["results"][0]["path"] == "tie_b.py"


def test_equal_bm25_scores_share_a_rank(tmp_path: Path) -> None:
    files = _tie_fixture(tmp_path)
    result = code_search(tmp_path, "needle", cache_path=_cache(tmp_path),
                         files=files)
    by_path = {item["path"]: item for item in result["results"]}
    assert by_path["tie_a.py"]["bm25"] == by_path["tie_b.py"]["bm25"]
    assert by_path["tie_a.py"]["bm25_rank"] == by_path["tie_b.py"]["bm25_rank"]
    assert by_path["tie_a.py"]["bm25_rank"] == 1


def test_competition_ranks_share_positions_on_ties() -> None:
    ranks = _competition_ranks({"w": 3.0, "x": 2.0, "y": 2.0, "z": 1.0})
    assert ranks == {"w": 1, "x": 2, "y": 2, "z": 4}
    noisy = _competition_ranks({"x": 0.5, "y": 0.5 + 1e-15})
    assert noisy["x"] == noisy["y"] == 1


def test_empty_query_is_a_clear_result(tmp_path: Path) -> None:
    files = _fixture(tmp_path)
    result = code_search(tmp_path, "   \n\t ", cache_path=_cache(tmp_path),
                         files=files)
    assert result["ok"] is True
    assert result["empty"] is True
    assert result["results"] == []
    assert result["n"] == 0
    assert "empty" in result["note"].lower()


def test_deterministic_across_repeats_and_file_order(tmp_path: Path) -> None:
    files = _fixture(tmp_path)
    first = code_search(tmp_path, "alpha retry", cache_path=_cache(tmp_path),
                        files=files)
    second = code_search(tmp_path, "alpha retry", cache_path=_cache(tmp_path),
                         files=files)
    assert json.dumps(first, sort_keys=True) == json.dumps(second,
                                                           sort_keys=True)

    # A different cache built from the reversed file list must not change the
    # ranking, scores, or snippets.
    other_cache = tmp_path / "var" / "tags_reversed.json"
    reversed_result = code_search(tmp_path, "alpha retry",
                                  cache_path=other_cache,
                                  files=list(reversed(files)))
    assert json.dumps(first, sort_keys=True) == json.dumps(
        reversed_result, sort_keys=True)


def test_snippet_is_bounded(tmp_path: Path) -> None:
    long_line = "# " + "needle " * 120
    files = _write(tmp_path, {
        "long.py": "def long_line():\n    " + long_line + "\n    return 1\n",
    })
    result = code_search(tmp_path, "needle", cache_path=_cache(tmp_path),
                         files=files)
    hit = result["results"][0]
    assert hit["path"] == "long.py"
    assert hit["line"] == 2
    assert len(hit["snippet"]) <= MAX_SNIPPET_CHARS
    assert hit["snippet"].endswith("...")
    assert "needle" in hit["snippet"]

    without = code_search(tmp_path, "needle", cache_path=_cache(tmp_path),
                          files=files, include_snippet=False)
    assert "snippet" not in without["results"][0]
    assert "line" not in without["results"][0]


def test_bm25_defaults_and_configuration(tmp_path: Path) -> None:
    assert (BM25_K1, BM25_B, RRF_K) == (1.5, 0.75, 60)
    files = _fixture(tmp_path)
    result = code_search(tmp_path, "alpha", cache_path=_cache(tmp_path),
                         files=files, k1=1.2, b=0.3, rrf_k=10)
    assert result["bm25"] == {"k1": 1.2, "b": 0.3}
    assert result["rrf_k"] == 10
    assert result["n"] >= 1


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "a6df57f0d4b594564d993495d6d38a1b1be3170f"
IDENTITY_QUERIES = ("alpha", "frobnicated retry", "needle", "widget compute",
                    "gamma beta")


def _load_base_search(directory: Path):
    """code_search as it was at BASE_COMMIT, under its own module name."""
    try:
        source = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show",
             f"{BASE_COMMIT}:scripts/ocelot_code_search.py"],
            capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip(f"base commit {BASE_COMMIT} is not available")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "base_ocelot_code_search.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("base_ocelot_code_search",
                                                  path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _identity_fixture(root: Path) -> list[str]:
    files = {}
    for i in range(12):
        body = (f"def widget_{i}_compute(x):\n"
                f"    # widget compute step {i}\n"
                f"    return helper_{i % 3}(x) + {i}\n")
        files[f"mod{i:02d}.py"] = body
    files["helpers.py"] = (
        "def helper_0(x):\n    return x\n\n"
        "def helper_1(x):\n    return alpha_fn(x)\n\n"
        "def helper_2(x):\n    # needle in a comment\n    return x\n")
    files["alpha.py"] = (
        "def alpha_fn(x):\n"
        '    """Frobnicated retry budget."""\n'
        "    return x\n")
    return _write(root, files)


def _run_queries(module, root: Path, cache_path: Path,
                 files: list[str]) -> list[dict]:
    """Run every query with memos cleared, as separate sessions would."""
    repo_map_module.clear_memos()
    module._INDEX_CACHE.clear()
    return [module.code_search(root, q, cache_path=cache_path, files=files)
            for q in IDENTITY_QUERIES]


def _side(cache_path: Path) -> Path:
    return search_side_cache_path(cache_path)


def test_search_matches_base_cold_warm_and_partially_stale(
        tmp_path: Path) -> None:
    base = _load_base_search(tmp_path / "base")
    root = tmp_path / "repo"
    files = _identity_fixture(root)
    new_cache = root / "var" / "new_tags.json"
    base_cache = root / "var" / "base_tags.json"

    # Cold: no side file yet.
    expected = _run_queries(base, root, base_cache, files)
    actual = _run_queries(search_module, root, new_cache, files)
    assert actual == expected
    assert search_module.LAST_BUILD["side_cache"] == "absent"
    assert _side(new_cache).exists()

    # Warm: same tree, side file present, nothing tokenized.
    repo_map_module.clear_memos()
    search_module._INDEX_CACHE.clear()
    warm = search_module.code_search(root, IDENTITY_QUERIES[0],
                                     cache_path=new_cache, files=files)
    assert search_module.LAST_BUILD["side_cache"] == "loaded"
    assert search_module.LAST_BUILD["tokenized"] == 0
    assert warm == expected[0]

    # Partially stale: one file edited, the other side rows are reused.
    (root / "helpers.py").write_text(
        "def helper_0(x):\n    return x * 2\n\n"
        "def helper_9(x):\n    return needle_extra(x)\n", encoding="utf-8")
    expected = _run_queries(base, root, base_cache, files)
    actual = _run_queries(search_module, root, new_cache, files)
    assert actual == expected
    assert search_module.LAST_BUILD["tokenized"] == 1
    assert search_module.LAST_BUILD["reused"] == len(files) - 1


def test_side_cache_version_key_and_corruption_are_ignored(
        tmp_path: Path) -> None:
    base = _load_base_search(tmp_path / "base")
    root = tmp_path / "repo"
    files = _identity_fixture(root)
    cache = root / "var" / "tags.json"
    expected = _run_queries(base, root, root / "var" / "base.json", files)
    _run_queries(search_module, root, cache, files)
    side = _side(cache)
    good = marshal.loads(side.read_bytes())

    cases = {
        "version": {**good, "version": good["version"] + 1},
        "key": {**good, "key": "0" * 64},
    }
    for name, doc in cases.items():
        side.write_bytes(marshal.dumps(doc))
        actual = _run_queries(search_module, root, cache, files)
        assert actual == expected, name
        assert search_module.LAST_BUILD["side_cache"] == (
            "ignored: version or key mismatch"), name
        assert search_module.LAST_BUILD["tokenized"] == len(files), name
        # The rebuild rewrote a valid side file.
        assert marshal.loads(side.read_bytes())["key"] == good["key"]

    side.write_bytes(b"\x00not marshal data\xff")
    actual = _run_queries(search_module, root, cache, files)
    assert actual == expected
    assert search_module.LAST_BUILD["side_cache"] == "ignored: unreadable"
    assert search_module.LAST_BUILD["tokenized"] == len(files)


def test_parallel_tokenization_matches_serial(tmp_path: Path,
                                              monkeypatch) -> None:
    root = tmp_path / "repo"
    files = _identity_fixture(root)
    monkeypatch.setenv("OCELOT_INDEX_WORKERS", "1")
    serial_cache = root / "var" / "serial.json"
    serial = _run_queries(search_module, root, serial_cache, files)
    assert search_module.LAST_BUILD["parallel"] == 1

    monkeypatch.setattr(search_module, "SEARCH_PARALLEL_MIN_FILES", 1)
    monkeypatch.setattr(search_module, "SEARCH_PARALLEL_CHUNK", 4)
    monkeypatch.setenv("OCELOT_INDEX_WORKERS", "2")
    parallel_cache = root / "var" / "parallel.json"
    parallel = _run_queries(search_module, root, parallel_cache, files)
    assert search_module.LAST_BUILD["parallel"] == 2
    assert search_module.LAST_BUILD["tokenized"] == len(files)
    assert parallel == serial
    assert (search_module._load_side(_side(parallel_cache))
            == search_module._load_side(_side(serial_cache)))


def test_pool_failure_falls_back_to_serial_for_search(tmp_path: Path,
                                                      monkeypatch) -> None:
    root = tmp_path / "repo"
    files = _identity_fixture(root)
    serial = _run_queries(search_module, root, root / "var" / "s.json", files)
    monkeypatch.setattr(search_module, "SEARCH_PARALLEL_MIN_FILES", 1)
    monkeypatch.setenv("OCELOT_INDEX_WORKERS", "2")

    class BrokenPool:
        def __init__(self, *args, **kwargs):
            raise OSError("no processes for you")

    monkeypatch.setattr(search_module.concurrent.futures,
                        "ProcessPoolExecutor", BrokenPool)
    fallback = _run_queries(search_module, root, root / "var" / "f.json",
                            files)
    assert search_module.LAST_BUILD["parallel"].startswith("fallback: OSError")
    assert fallback == serial


def test_full_scan_prunes_side_rows_for_removed_files(tmp_path: Path,
                                                      monkeypatch) -> None:
    root = tmp_path / "repo"
    files = _identity_fixture(root)
    cache = root / "var" / "tags.json"
    monkeypatch.setattr(repo_map_module, "SOURCE_DIRS", (".",))
    search_module.code_search(root, "alpha", cache_path=cache)
    assert "helpers.py" in search_module._load_side(_side(cache))

    # A subset call keeps rows for files outside its subset.
    repo_map_module.clear_memos()
    search_module.code_search(root, "alpha", cache_path=cache,
                              files=["alpha.py"])
    assert "helpers.py" in search_module._load_side(_side(cache))

    # A full scan drops rows for files that no longer exist.
    (root / "helpers.py").unlink()
    repo_map_module.clear_memos()
    search_module.code_search(root, "alpha", cache_path=cache)
    rows = search_module._load_side(_side(cache))
    assert "helpers.py" not in rows
    assert "alpha.py" in rows
    assert search_module.LAST_BUILD["side_cache"] == "loaded"
