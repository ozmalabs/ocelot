"""test_architecture_migrated — deterministic architecture summaries.

The report is built on the repo map's tag cache and file reference graph. The
tests use a small synthetic checkout so they never depend on the real Ocelot
tree and never touch its cache:

    a.py  -> b.py      (alpha uses helper)
    b.py  -> a.py      (via_alpha uses alpha)      => 2-file Tarjan cycle
    c.py  -> a.py      (gamma uses alpha)          => leaf consumer
    tests/test_a.py -> a.py                        => test file

``a.py`` is the hub (three inbound edges); ``c.py`` has no inbound edge and is
the single dead-code candidate outside tests.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.ocelot_architecture import architecture_report


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(root: Path) -> list[str]:
    """The canonical fixture: a<->b cycle, c leaf consumer, one test."""
    _write(root / "a.py",
           "def alpha(x):\n"
           "    return helper(x) + 1\n")
    _write(root / "b.py",
           "def helper(x):\n"
           "    return x * 2\n"
           "\n"
           "def via_alpha():\n"
           "    return alpha(3)\n")
    _write(root / "c.py",
           "from a import alpha\n"
           "\n"
           "def gamma():\n"
           "    return alpha(4)\n")
    _write(root / "tests" / "test_a.py",
           "from a import alpha\n"
           "\n"
           "def test_alpha():\n"
           "    assert alpha(1) == 3\n")
    return ["a.py", "b.py", "c.py", "tests/test_a.py"]


def _report(root: Path, **kwargs):
    files = kwargs.pop("files", None)
    if files is None:
        files = ["a.py", "b.py", "c.py", "tests/test_a.py"]
    return architecture_report(
        root, cache_path=root / "var" / "tags.json", files=files, **kwargs)


def test_report_shape(tmp_path: Path) -> None:
    _fixture(tmp_path)
    report = _report(tmp_path)
    assert report["ok"] is True
    assert set(report) == {"ok", "summary", "markdown", "json"}
    summary = report["summary"]
    assert set(summary) == {
        "files", "edges", "languages", "hubs", "cycles", "coupling",
        "modules", "dead_code_candidates", "test_source_ratio",
    }
    assert summary["files"] == 4
    assert summary["edges"] == 4
    assert summary["languages"] == {"python": 4}
    assert json.loads(report["json"]) == summary


def test_cycle_detection(tmp_path: Path) -> None:
    _fixture(tmp_path)
    summary = _report(tmp_path)["summary"]
    assert summary["cycles"] == [
        {"size": 2, "files": ["a.py", "b.py"], "truncated": False}]


def test_hub_ordering_uses_pagerank_then_in_degree(tmp_path: Path) -> None:
    _fixture(tmp_path)
    hubs = _report(tmp_path)["summary"]["hubs"]
    assert [hub["path"] for hub in hubs[:2]] == ["a.py", "b.py"]
    assert [hub["rank"] for hub in hubs] == [1, 2, 3, 4]
    assert hubs[0]["in_degree"] == 3
    assert hubs[0]["out_degree"] == 1
    # 0.47966178 > 0.44533822 > 0.0375; a hub is not just a degree count.
    assert hubs[0]["pagerank"] > hubs[1]["pagerank"] > hubs[2]["pagerank"]
    assert hubs[2]["pagerank"] == hubs[3]["pagerank"]
    assert hubs[2]["path"] == "c.py"  # tie broken by path
    assert sum(hub["pagerank"] for hub in hubs) > 0.99


def test_coupling_degrees(tmp_path: Path) -> None:
    _fixture(tmp_path)
    coupling = _report(tmp_path)["summary"]["coupling"]
    assert coupling["files_with_inbound"] == 2
    assert coupling["files_with_outbound"] == 4
    assert coupling["max_in_degree"] == 3
    assert coupling["max_out_degree"] == 1
    assert coupling["top"] == [
        {"path": "a.py", "in_degree": 3, "out_degree": 1,
         "total_degree": 4},
        {"path": "b.py", "in_degree": 1, "out_degree": 1,
         "total_degree": 2},
        {"path": "c.py", "in_degree": 0, "out_degree": 1,
         "total_degree": 1},
        {"path": "tests/test_a.py", "in_degree": 0, "out_degree": 1,
         "total_degree": 1},
    ]


def test_modules_and_cross_module_edges(tmp_path: Path) -> None:
    _fixture(tmp_path)
    modules = _report(tmp_path)["summary"]["modules"]
    assert modules["count"] == 2
    assert modules["by_module"] == [
        {"module": "(root)", "files": 3},
        {"module": "tests", "files": 1},
    ]
    assert modules["cross_edges"] == [
        {"src": "tests", "tgt": "(root)", "edges": 1}]
    assert modules["cross_edge_count"] == 1
    assert modules["intra_module_edge_count"] == 3


def test_dead_code_candidate_and_test_ratio(tmp_path: Path) -> None:
    _fixture(tmp_path)
    summary = _report(tmp_path)["summary"]
    # c.py is a leaf consumer: no file references gamma. The test file is
    # excluded even though it also has no inbound references.
    assert summary["dead_code_candidates"] == ["c.py"]
    assert summary["test_source_ratio"] == {
        "tests": 1, "source": 3, "ratio": 0.3333}


def test_dead_code_excludes_scripts_entrypoints_and_tests(
        tmp_path: Path) -> None:
    _write(tmp_path / "solo.py", "def lonely():\n    return 1\n")
    _write(tmp_path / "main.py", "def main():\n    return 0\n")
    _write(tmp_path / "scripts" / "cli.py", "def cli():\n    return 0\n")
    _write(tmp_path / "__init__.py", "VALUE = 1\n")
    _write(tmp_path / "tests" / "test_nothing.py",
           "def test_nothing():\n    assert True\n")
    report = _report(
        tmp_path,
        files=["solo.py", "main.py", "scripts/cli.py", "__init__.py",
               "tests/test_nothing.py"])
    assert report["summary"]["dead_code_candidates"] == ["solo.py"]


def test_markdown_sections(tmp_path: Path) -> None:
    _fixture(tmp_path)
    markdown = _report(tmp_path)["markdown"]
    for heading in (
        "## Hubs",
        "## Cycles (Tarjan SCC > 1)",
        "## Coupling",
        "## Modules",
        "## Dead-code candidates (heuristic)",
        "## Test-to-source ratio",
        "## Method and limits",
    ):
        assert heading in markdown
    assert "`a.py`" in markdown
    assert "2 files: `a.py`, `b.py`" in markdown
    assert "Cross-module edges: 1" in markdown
    assert "ratio: 0.3333" in markdown
    assert "Tarjan" in markdown


def test_markdown_bounds_large_cycle_members(tmp_path: Path) -> None:
    _write(tmp_path / "d.py", "def d_fn():\n    return e_fn()\n")
    _write(tmp_path / "e.py", "def e_fn():\n    return f_fn()\n")
    _write(tmp_path / "f.py", "def f_fn():\n    return d_fn()\n")
    markdown = _report(tmp_path, files=["d.py", "e.py", "f.py"],
                       top=1)["markdown"]
    assert "3 files: `d.py` _... and 2 more in this component_" in markdown


def test_top_caps_ranked_lists(tmp_path: Path) -> None:
    _fixture(tmp_path)
    summary = _report(tmp_path, top=1)["summary"]
    assert len(summary["hubs"]) == 1
    assert len(summary["coupling"]["top"]) == 1
    # Cycle components are all reported; their member lists are capped.
    assert summary["cycles"] == [
        {"size": 2, "files": ["a.py"], "truncated": True}]


def test_deterministic_output(tmp_path: Path) -> None:
    _fixture(tmp_path)
    first = _report(tmp_path)
    second = _report(tmp_path)
    assert first["json"] == second["json"]
    assert first["markdown"] == second["markdown"]
    assert first["summary"] == second["summary"]
    # No absolute checkout path or timestamp leaks into the report.
    assert str(tmp_path) not in first["json"]
    assert str(tmp_path) not in first["markdown"]


def test_three_file_cycle_and_sorted_components(tmp_path: Path) -> None:
    # d -> e -> f -> d is a 3-cycle; g <-> h is a 2-cycle.
    _write(tmp_path / "d.py",
           "def d_fn():\n    return e_fn()\n")
    _write(tmp_path / "e.py",
           "def e_fn():\n    return f_fn()\n")
    _write(tmp_path / "f.py",
           "def f_fn():\n    return d_fn()\n")
    _write(tmp_path / "g.py",
           "def g_fn():\n    return h_fn()\n")
    _write(tmp_path / "h.py",
           "def h_fn():\n    return g_fn()\n")
    files = ["d.py", "e.py", "f.py", "g.py", "h.py"]
    summary = _report(tmp_path, files=files)["summary"]
    assert summary["cycles"] == [
        {"size": 3, "files": ["d.py", "e.py", "f.py"], "truncated": False},
        {"size": 2, "files": ["g.py", "h.py"], "truncated": False},
    ]


def test_no_cycles(tmp_path: Path) -> None:
    _write(tmp_path / "one.py", "def one():\n    return 1\n")
    _write(tmp_path / "two.py", "def two():\n    return 2\n")
    summary = _report(tmp_path, files=["one.py", "two.py"])["summary"]
    assert summary["cycles"] == []
    assert summary["edges"] == 0
    assert summary["dead_code_candidates"] == ["one.py", "two.py"]


def test_empty_repo(tmp_path: Path) -> None:
    summary = _report(tmp_path, files=[])["summary"]
    assert summary["files"] == 0
    assert summary["edges"] == 0
    assert summary["hubs"] == []
    assert summary["cycles"] == []
    assert summary["dead_code_candidates"] == []
    assert summary["test_source_ratio"]["ratio"] is None
