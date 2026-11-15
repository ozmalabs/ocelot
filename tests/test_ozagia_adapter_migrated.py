"""test_ozagia_adapter_migrated — Ocelot's side of the ozagia dev tooling.

The tooling itself (and its tests) lives in ozagia. These tests cover what only
Ocelot has: `.ozagia.toml`, the seed/IR/graph-query adapter in
`tools/ozagia_ocelot_adapter.py`, the `scripts/ocelot_*` shims, and the shipped
evaluation task sets under `evaluation/`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("ozagia")

from ozagia.adapters import registry  # noqa: E402
from ozagia.config import load_project_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".ozagia.toml"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_config_parses_and_names_the_ocelot_layout():
    cfg = load_project_config(ROOT)
    assert cfg.source == CONFIG.resolve()
    assert "runners/dsl/src" in cfg.source_dirs
    assert cfg.map_dirs[-1] == "tests"
    assert "var" in cfg.skip_dirs and ".git" in cfg.skip_dirs
    assert cfg.import_roots == ("runners/dsl/python",)
    assert cfg.adapters == ("tools.ozagia_ocelot_adapter:register",)


def test_adapter_loads_and_registers_its_extensions():
    reg = registry(ROOT, reload=True)
    assert reg.errors == []
    assert "tools.ozagia_ocelot_adapter:register" in reg.loaded
    assert len(reg.indexers) == 1
    assert "dev_graph_query" in reg.mcp_tools
    assert "ir" in reg.edit_engines


def test_seed_manifests_become_seed_and_rule_nodes(tmp_path, monkeypatch):
    monkeypatch.setenv("OZAGIA_CONFIG", str(CONFIG))
    from ozagia.core.memory import DevMemory, build_index
    _write(tmp_path / "seeds" / "demo.json", json.dumps({
        "id": "demo", "version": "1", "description": "Demo seed.",
        "depends_on": ["base"],
        "rules": [{"name": "demo_rule", "where": {"type": "Thing"}}],
        "concepts": [{"name": "demo_concept"}],
    }))
    _write(tmp_path / "tests" / "test_demo.py",
           "# loads seeds/demo.json\ndef test_demo():\n    assert True\n")
    out = tmp_path / "graph.json"
    build_index(tmp_path, out, include_docs="none", include_git=False)
    mem = DevMemory(out, tmp_path / "journal.jsonl", root=tmp_path)
    seed = mem.seed("demo")
    assert seed["ok"] is True
    assert mem.rule("demo_rule")["ok"] is True
    graph = json.loads(out.read_text(encoding="utf-8"))
    types = {n["type"] for n in graph["nodes"]}
    assert {"Seed", "Rule", "Concept"} <= types
    stub = [n for n in graph["nodes"]
            if n["type"] == "Seed" and n["attrs"].get("id") == "base"]
    assert stub and stub[0]["attrs"].get("stub") == 1
    assert any(e["type"] == "mentions_seed" for e in graph["edges"])


def test_ir_dispatch_and_journal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OZAGIA_CONFIG", str(CONFIG))
    from ozagia.core.memory import DevMemory, build_index
    _write(tmp_path / "domains" / "foo.py", '''"""Foo domain."""

from domains.bar import helper


class Widget:
    """A widget."""

    def size(self, n: int) -> int:
        """Return the widget size."""
        return helper(n) + 1


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')
    _write(tmp_path / "domains" / "bar.py",
           '"""Bar domain."""\n\n\ndef helper(n: int) -> int:\n    return n * 2\n')
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    mem = DevMemory(out, tmp_path / "var" / "journal.jsonl")
    r = mem.edit({
        "file": "domains/foo.py",
        "apply": True,
        "ops": [{
            "op": "replace_expression_ir",
            "target": "body[3].body[1].value",
            "term": {"type": "Plus",
                     "items": [{"type": "Var", "name": "a"},
                               {"type": "Lit", "value": 1}]},
        }],
    }, task="ir add one")
    assert r["ok"] is True and r["applied"] is True
    assert r["engine"] == "hub_ir"
    assert "return (a + 1)" in (tmp_path / "domains" / "foo.py").read_text()
    entry = mem.journal_recent(1)[0]
    assert entry["kind"] == "edit"
    assert entry["task"] == "ir add one"


def test_shims_alias_the_ozagia_modules():
    import scripts.ocelot_dev_memory as old
    import ozagia.core.memory as new
    assert old is new
    proc = subprocess.run([sys.executable, "-m", "scripts.ocelot_dev_memory", "--help"],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "build" in proc.stdout


def test_shipped_agent_task_file_is_well_formed():
    from ozagia.eval.agent import load_tasks
    spec = load_tasks(ROOT / "evaluation" / "agent_e2e" / "tasks.json")
    tasks = spec["tasks"]
    assert 6 <= len(tasks) <= 8
    assert len({t["id"] for t in tasks}) == len(tasks)
    assert len({t["area"] for t in tasks}) >= 3
    for task in tasks:
        assert (ROOT / "evaluation" / "agent_e2e" / task["break_patch"]).is_file()
        assert any("{workdir}" in a for a in task["check"]["argv"])
        assert task["check"]["timeout_s"] <= 60
        assert task["expected_files"]
        assert "tests/" in " ".join(task["check"]["argv"])


def test_shipped_retrieval_tasks_v2_meet_leakage_and_design_counts() -> None:
    from ozagia.core.repo_map import SOURCE_DIRS
    from ozagia.eval.retrieval import (AREAS, STYLES, leakage, load_tasks,
                                       task_set_summary)
    tasks = load_tasks(ROOT / "evaluation" / "repo_map" / "tasks_v2.json", root=ROOT)
    assert len(tasks) >= 30
    summary = task_set_summary(tasks)
    assert summary["tasks"] == len(tasks)
    for task in tasks:
        assert leakage(task) == [], task["id"]
    dev = [t for t in tasks if t["area"] == "dev_tooling"]
    assert len(dev) / len(tasks) <= 0.30
    rust = [t for t in tasks if t["area"] == "rust_engine"]
    assert len(rust) >= 5
    symptom = [t for t in tasks if t["style"] == "symptom"]
    assert len(symptom) >= 12
    for task in tasks:
        assert task["style"] in STYLES and task["area"] in AREAS, task["id"]
    for task in rust:
        assert all(p.startswith("runners/dsl/src/")
                   for p in task["expected_files"]), task["id"]
    for task in tasks:
        expected = task["expected_files"]
        assert 1 <= len(expected) <= 4, task["id"]
        for rel in expected:
            assert any(rel.startswith(d + "/") for d in SOURCE_DIRS), rel
            assert (ROOT / rel).is_file(), rel
        evidence = task["evidence"]
        assert evidence, task["id"]
        for item in evidence:
            assert item["command"].startswith("rg "), task["id"]
            assert 1 <= len(item["matches"]) <= 5, task["id"]
        for rel in expected:
            assert any(m.split(":")[0] == rel
                       for item in evidence for m in item["matches"]), (task["id"], rel)
        if task["style"] == "symptom":
            text = task["task"]
            assert not re.search(r"[A-Za-z0-9]_[A-Za-z0-9]", text), task["id"]
            assert "(" not in text and "()" not in text, task["id"]
            assert not re.search(r"\w\.\w", text), task["id"]
            assert not re.search(r"\.(py|rs|json|md|lua|sh)\b", text), task["id"]
