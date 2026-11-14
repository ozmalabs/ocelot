"""test_symbol_graph_migrated — symbol-level callers, callees and impact (W2-C).

Fixtures are small real Python trees written to ``tmp_path`` and indexed with
``update_tag_cache(..., files=[...])``, so the tests exercise the same tag
cache path the tool uses.

``run`` is in ``_GENERIC_IDENTS``, so name-level resolution refuses it by
design. The two-class name test therefore uses ``process``. A ``run`` case
asserts the refusal.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import ocelot_symbol_graph as sg
from scripts.ocelot_repo_map import update_tag_cache

REPO_ROOT = Path(__file__).resolve().parents[1]

FIXTURE = {
    "pkg/__init__.py": "",
    "pkg/mod.py": "def helper():\n    return 1\n",
    "other.py": "def helper():\n    return 2\n",
    "use.py": ("from pkg.mod import helper\n"
               "\n"
               "def caller():\n"
               "    return helper()\n"),
    "use_top.py": ("from pkg.mod import helper\n"
                   "\n"
                   "VALUE = helper()\n"),
    "pkg/rel_use.py": ("from .mod import helper\n"
                       "\n"
                       "def go():\n"
                       "    return helper()\n"),
    "pkg/sub/deep_use.py": ("from ..mod import helper\n"
                            "\n"
                            "def go_deep():\n"
                            "    return helper()\n"),
    "pkg/loc.py": ("def a():\n"
                   "    return b()\n"
                   "\n"
                   "def b():\n"
                   "    return 1\n"),
    "pkg/classes_a.py": ("class A:\n"
                         "    def process(self):\n"
                         "        return 1\n"),
    "pkg/classes_b.py": ("class B:\n"
                         "    def process(self):\n"
                         "        return 2\n"),
    "pkg/x_caller.py": ("def use(x):\n"
                        "    return x.process()\n"
                        "\n"
                        "def use_run(x):\n"
                        "    return x.run()\n"),
    "pkg/selfcall.py": ("class A:\n"
                        "    def run(self):\n"
                        "        return self.step()\n"
                        "\n"
                        "    def step(self):\n"
                        "        return 1\n"
                        "\n"
                        "class B:\n"
                        "    def step(self):\n"
                        "        return 2\n"),
    "pkg/leaf_one.py": "def leaf_x():\n    return 1\n",
    "pkg/mid_one.py": "def mid_one_fn():\n    return leaf_x()\n",
    "pkg/mid_two.py": "def mid_two_fn():\n    return mid_one_fn()\n",
    "pkg/mid_two_twin.py": "def mid_two_fn():\n    return 3\n",
    "pkg/top.py": "def top_fn():\n    return mid_two_fn()\n",
}


def _write_fixture(root: Path, files: dict[str, str] | None = None) -> list[str]:
    files = FIXTURE if files is None else files
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return sorted(files)


@pytest.fixture()
def graph(tmp_path: Path) -> dict:
    rels = _write_fixture(tmp_path)
    cache, _ = update_tag_cache(tmp_path, cache_path=tmp_path / "tags.json",
                                files=rels)
    return sg.build_symbol_graph(cache)


def _edge(graph: dict, src: str, tgt: str) -> dict | None:
    for edge in graph["edges"]:
        if edge["src"] == src and edge["tgt"] == tgt:
            return edge
    return None


def _edges_from(graph: dict, src: str) -> list[dict]:
    return [e for e in graph["edges"] if e["src"] == src]


def test_import_resolution_yields_one_edge(graph: dict) -> None:
    edges = _edges_from(graph, "use.py::caller")
    assert [(e["tgt"], e["resolution"], e["confidence"]) for e in edges] == [
        ("pkg/mod.py::helper", "import", 1.0)]
    # other.py::helper is not a target, even though it is the same name.
    assert _edge(graph, "use.py::caller", "other.py::helper") is None


def test_relative_import_resolves_from_package(graph: dict) -> None:
    edge = _edge(graph, "pkg/rel_use.py::go", "pkg/mod.py::helper")
    assert edge is not None
    assert edge["resolution"] == "import"
    assert edge["confidence"] == 1.0
    deep = _edge(graph, "pkg/sub/deep_use.py::go_deep", "pkg/mod.py::helper")
    assert deep is not None and deep["resolution"] == "import"


def test_module_level_caller_uses_module_id(graph: dict) -> None:
    edge = _edge(graph, "use_top.py::<module>", "pkg/mod.py::helper")
    assert edge is not None and edge["resolution"] == "import"
    assert graph["nodes"]["use_top.py::<module>"]["qualname"] == "<module>"


def test_same_file_call_is_local(graph: dict) -> None:
    edge = _edge(graph, "pkg/loc.py::a", "pkg/loc.py::b")
    assert edge is not None
    assert edge["resolution"] == "local"
    assert edge["confidence"] == 1.0


def test_name_resolution_splits_confidence_across_candidates(graph: dict) -> None:
    left = _edge(graph, "pkg/x_caller.py::use", "pkg/classes_a.py::A.process")
    right = _edge(graph, "pkg/x_caller.py::use", "pkg/classes_b.py::B.process")
    assert left is not None and right is not None
    assert left["resolution"] == right["resolution"] == "name"
    assert left["confidence"] == right["confidence"] == 0.5


def test_generic_name_is_not_linked_by_name(graph: dict) -> None:
    # "run" is in _GENERIC_IDENTS; the attribute call x.run() stays unresolved.
    assert _edges_from(graph, "pkg/x_caller.py::use_run") == []
    assert graph["stats"]["unresolved"] >= 1


def test_self_method_call_resolves_locally_to_own_class(graph: dict) -> None:
    edge = _edge(graph, "pkg/selfcall.py::A.run", "pkg/selfcall.py::A.step")
    assert edge is not None
    assert edge["resolution"] == "local"
    assert edge["confidence"] == 1.0
    assert _edge(graph, "pkg/selfcall.py::A.run",
                 "pkg/selfcall.py::B.step") is None


def test_symbol_impact_depth_and_confidence_product(graph: dict) -> None:
    depth2 = sg.symbol_impact(graph, "pkg/leaf_one.py::leaf_x", depth=2)
    ids2 = {row["id"] for row in depth2["results"]}
    assert "pkg/top.py::top_fn" not in ids2
    assert "pkg/mid_one.py::mid_one_fn" in ids2

    depth3 = sg.symbol_impact(graph, "pkg/leaf_one.py::leaf_x", depth=3)
    rows = {row["id"]: row for row in depth3["results"]}
    top = rows["pkg/top.py::top_fn"]
    assert top["depth"] == 3
    assert top["confidence"] == pytest.approx(0.5)
    assert rows["pkg/mid_one.py::mid_one_fn"]["confidence"] == 1.0
    files = {row["file"]: row for row in depth3["files"]}
    assert files["pkg/top.py"]["min_depth"] == 3
    assert files["pkg/mid_one.py"]["min_depth"] == 1

    pruned = sg.symbol_impact(graph, "pkg/leaf_one.py::leaf_x", depth=3,
                              min_confidence=0.6)
    assert "pkg/top.py::top_fn" not in {r["id"] for r in pruned["results"]}


def test_callees_follow_forward_edges(graph: dict) -> None:
    result = sg.callees(graph, "pkg/top.py::top_fn", depth=2)
    ids = {row["id"] for row in result["results"]}
    assert ids == {"pkg/mid_two.py::mid_two_fn",
                   "pkg/mid_two_twin.py::mid_two_fn",
                   "pkg/mid_one.py::mid_one_fn"}


def test_ambiguous_resolve_returns_candidates(graph: dict) -> None:
    result = sg.symbol_impact(graph, "helper")
    assert result == {"ok": False,
                      "ambiguous": ["other.py::helper", "pkg/mod.py::helper"]}
    assert sg.resolve_symbol(graph, "pkg/mod.py::helper") == [
        "pkg/mod.py::helper"]
    assert sg.resolve_symbol(graph, "B.process") == ["pkg/classes_b.py::B.process"]


def test_unknown_symbol_is_error_dict(graph: dict) -> None:
    for fn in (sg.callers, sg.callees, sg.symbol_impact):
        result = fn(graph, "no_such_symbol_xyz")
        assert result["ok"] is False
        assert "unknown symbol" in result["error"]


def test_depth_must_be_positive(graph: dict) -> None:
    assert sg.callers(graph, "pkg/mod.py::helper", depth=0)["ok"] is False


def test_build_is_deterministic_and_memoised(tmp_path: Path) -> None:
    rels = _write_fixture(tmp_path)
    cache, _ = update_tag_cache(tmp_path, cache_path=tmp_path / "t.json",
                                files=rels)
    first = sg.build_symbol_graph(cache)
    assert sg.build_symbol_graph(cache) is first
    sg._GRAPH_MEMO.clear()
    second = sg._build(cache)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def _edges_under_seed(seed: str, root: Path, rels: list[str]) -> str:
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from scripts.ocelot_repo_map import update_tag_cache\n"
        "from scripts.ocelot_symbol_graph import build_symbol_graph\n"
        "root = Path(sys.argv[2])\n"
        "cache, _ = update_tag_cache(root, cache_path=root / 'seed.json',\n"
        "                            files=json.loads(sys.argv[3]))\n"
        "graph = build_symbol_graph(cache)\n"
        "print(json.dumps({'edges': graph['edges'], 'nodes': graph['nodes']},"
        " sort_keys=True))\n"
    )
    env = dict(os.environ, PYTHONHASHSEED=seed)
    done = subprocess.run(
        [sys.executable, "-c", script, str(REPO_ROOT), str(root),
         json.dumps(rels)],
        capture_output=True, text=True, env=env, check=True, timeout=120)
    return done.stdout


def test_edges_identical_across_hash_seeds(tmp_path: Path) -> None:
    rels = _write_fixture(tmp_path)
    one = _edges_under_seed("1", tmp_path, rels)
    two = _edges_under_seed("2", tmp_path, rels)
    assert one == two
    assert json.loads(one)["edges"]


def test_symbol_query_end_to_end_and_cli(tmp_path: Path, capsys) -> None:
    _write_fixture(tmp_path, {
        "scripts/a_mod.py": "def base_fn():\n    return 1\n",
        "scripts/b_use.py": ("def wrap_fn():\n"
                             "    return base_fn()\n"),
    })
    cache_file = tmp_path / "cache.json"
    result = sg.symbol_query(tmp_path, "callers", "base_fn",
                             cache_path=cache_file)
    assert result["ok"] is True
    assert [r["id"] for r in result["results"]] == [
        "scripts/b_use.py::wrap_fn"]
    assert result["stats"]["resolved_local"] == 0
    assert result["stats"]["resolved_name"] == 1
    assert set(result["timings"]) == {"update_seconds", "build_seconds",
                                      "query_seconds"}
    assert sg.symbol_query(tmp_path, "resolve", "nope_zz",
                           cache_path=cache_file)["ok"] is False

    code = sg.main(["impact", "base_fn", "--root", str(tmp_path),
                    "--cache", str(cache_file), "--depth", "2"])
    out = capsys.readouterr().out
    assert code == 0
    assert json.loads(out)["results"][0]["id"] == "scripts/b_use.py::wrap_fn"
