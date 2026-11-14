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
    GRAPH_WEIGHT,
    MAX_SNIPPET_CHARS,
    RRF_K,
    _competition_ranks,
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
