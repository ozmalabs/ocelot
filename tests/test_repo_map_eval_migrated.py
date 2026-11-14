"""test_repo_map_eval_migrated — deterministic, offline repo-map evaluation.

The fixture is a tiny repository with a frozen task file and a tiny dev-memory
snapshot. No real-repo indexing, no network, no LLM.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ocelot_dev_memory import build_index
from scripts.ocelot_repo_map_eval import (
    ARMS,
    baseline_listing,
    context_files,
    evaluate,
    load_tasks,
    render_markdown,
    source_files,
)


def _fixture(root: Path) -> Path:
    (root / "scripts").mkdir()
    (root / "tests").mkdir()
    (root / "scripts" / "alpha.py").write_text(
        '"""Alpha feature module."""\n'
        "\n"
        "def alpha_feature(x):\n"
        '    """Return x plus one."""\n'
        "    return x + 1\n"
        "\n"
        "def alpha_helper():\n"
        "    return alpha_feature(1)\n",
        encoding="utf-8")
    (root / "scripts" / "beta.py").write_text(
        '"""Beta module uses alpha."""\n'
        "\n"
        "from scripts.alpha import alpha_feature\n"
        "\n"
        "def beta_use():\n"
        "    return alpha_feature(2)\n",
        encoding="utf-8")
    (root / "scripts" / "unrelated.py").write_text(
        "def gamma_unrelated():\n"
        "    return 0\n",
        encoding="utf-8")
    (root / "tests" / "test_alpha.py").write_text(
        '"""Test alpha feature."""\n'
        "from scripts.alpha import alpha_feature\n"
        "\n"
        "def test_alpha_feature():\n"
        "    assert alpha_feature(1) == 2\n",
        encoding="utf-8")
    build_index(root, root / "var" / "ocelot_dev_graph.json",
                include_docs="none", include_git=False)
    tasks = {
        "version": 1,
        "description": "fixture tasks",
        "tasks": [
            {
                "id": "alpha-feature",
                "task": "Fix alpha_feature so alpha behavior is preserved.",
                "expected_files": ["scripts/alpha.py"],
                "notes": "The fixture's explicit ground truth.",
            },
            {
                "id": "unrelated-gamma",
                "task": "Change gamma_unrelated behavior.",
                "expected_files": ["scripts/unrelated.py"],
            },
        ],
    }
    path = root / "tasks.json"
    path.write_text(json.dumps(tasks), encoding="utf-8")
    return path


def _runs(report: dict, task_id: str, budget: int) -> dict[str, dict]:
    return {run["arm"]: run for run in report["runs"]
            if run["task_id"] == task_id
            and run["budget_tokens"] == budget}


def test_tasks_are_explicit_and_source_universe_is_sorted(tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    tasks = load_tasks(tasks_path, root=tmp_path)
    assert [t["id"] for t in tasks] == ["alpha-feature", "unrelated-gamma"]
    assert tasks[0]["expected_files"] == ["scripts/alpha.py"]
    assert source_files(tmp_path) == sorted(source_files(tmp_path))
    assert {"scripts/alpha.py", "tests/test_alpha.py"} <= set(
        source_files(tmp_path))


def test_recall_when_expected_file_is_ranked_and_budget_respected(
        tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    report = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500])
    assert report["ok"] is True
    assert report["arms"] == list(ARMS)
    runs = _runs(report, "alpha-feature", 500)
    assert list(runs) == list(ARMS)

    # The ranked map puts the task-named implementation first.
    assert runs["dev_repo_map"]["files"][0] == "scripts/alpha.py"
    assert runs["dev_repo_map"]["recall"] == 1.0
    assert runs["dev_context"]["recall"] == 1.0
    assert "scripts/alpha.py" in runs["both"]["files"]

    for arm in ("baseline", "dev_context", "dev_repo_map"):
        run = runs[arm]
        assert run["budget_respected"] is True
        assert run["estimated_tokens"] <= 500
        assert run["selected_count"] == len(run["files"])
        assert run["cache"]["applicable"] is (arm == "dev_repo_map")

    both = runs["both"]
    assert both["component_estimated_tokens"]["dev_context"] <= 500
    assert both["component_estimated_tokens"]["dev_repo_map"] <= 500
    assert both["components_within_budget"] is True
    assert both["estimated_tokens"] == (
        both["component_estimated_tokens"]["dev_context"]
        + both["component_estimated_tokens"]["dev_repo_map"])

    map_run = runs["dev_repo_map"]
    assert map_run["cache"]["parsed"] + map_run["cache"]["reused"] > 0


def test_baseline_listing_is_a_budgeted_path_prefix() -> None:
    files = [f"scripts/module_{i:03d}_with_a_long_name.py"
             for i in range(100)]
    listing = baseline_listing(files, 20)
    assert listing["files"]
    assert len(listing["files"]) < len(files)
    assert listing["files"] == files[:len(listing["files"])]
    assert listing["estimated_tokens"] <= 20


def test_context_files_uses_item_and_snippet_paths() -> None:
    result = {"items": [
        {"attrs": {"file": "scripts/alpha.py"},
         "snippet": {"path": "scripts/alpha.py"}},
        {"attrs": {"path": "seeds/example.json"},
         "snippet": {"path": "seeds/example.json"}},
        {"attrs": {}, "snippet": {}},
    ]}
    assert context_files(result) == [
        "scripts/alpha.py", "seeds/example.json"]


def test_output_is_deterministic_across_runs(tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    first = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500],
                     cache_path=tmp_path / "var" / "cache-a.json")
    second = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500],
                      cache_path=tmp_path / "var" / "cache-b.json")
    assert first["deterministic_fingerprint"] == \
        second["deterministic_fingerprint"]
    projection = lambda report: [
        [r["task_id"], r["budget_tokens"], r["arm"], r["files"],
         r["recall"], r["precision"], r["estimated_tokens"]]
        for r in report["runs"]]
    assert projection(first) == projection(second)
    assert first["aggregates"][0]["mean_recall_at_budget"] == \
        second["aggregates"][0]["mean_recall_at_budget"]


def test_markdown_labels_every_arm_and_task(tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    report = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500])
    markdown = render_markdown(report)
    assert "# Repo-map retrieval evaluation" in markdown
    assert "Mean recall@budget" in markdown
    for arm in ARMS:
        assert arm in markdown
    for task in report["tasks"]:
        assert task["id"] in markdown


def test_missing_expected_file_fails_loudly(tmp_path: Path) -> None:
    _fixture(tmp_path)
    bad = {
        "tasks": [{
            "id": "missing",
            "task": "Change a file that is not there.",
            "expected_files": ["scripts/not_present.py"],
        }]
    }
    path = tmp_path / "bad_tasks.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="does not exist"):
        evaluate(tmp_path, tasks_path=path, budgets=[500])
