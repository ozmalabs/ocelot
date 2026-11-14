"""test_code_search_migrated — lexical hybrid search over the repo-map cache.

BM25 over file paths, definition symbols, and source lines, fused with
repo-map PageRank by reciprocal rank fusion. No embeddings, network, or model.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.ocelot_code_search import (
    BM25_B,
    BM25_K1,
    MAX_SNIPPET_CHARS,
    RRF_K,
    code_search,
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


def test_fusion_flips_bm25_order_with_graph_centrality(tmp_path: Path) -> None:
    files = _fusion_fixture(tmp_path)
    result = code_search(tmp_path, "needle", cache_path=_cache(tmp_path),
                         files=files)
    by_path = {item["path"]: item for item in result["results"]}
    assert set(by_path) == {"hub.py", "plain.py"}

    # Lexically the repeated literal wins; structurally the referenced hub
    # wins. RRF must put the hub first.
    assert by_path["plain.py"]["bm25"] > by_path["hub.py"]["bm25"]
    assert by_path["hub.py"]["graph"] > by_path["plain.py"]["graph"]
    assert result["results"][0]["path"] == "hub.py"

    # Hub is BM25 rank 2 and PageRank rank 1 in this fixture.
    expected = round(1.0 / (RRF_K + 2) + 1.0 / (RRF_K + 1), 6)
    assert result["results"][0]["score"] == expected
    scores = [item["score"] for item in result["results"]]
    assert scores == sorted(scores, reverse=True)


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
