"""test_repo_map_eval_migrated — deterministic, offline repo-map evaluation.

The fixture is a tiny repository with a frozen task file and a tiny dev-memory
snapshot. No real-repo indexing, no network, no LLM.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ocelot_code_search import code_search
from scripts.ocelot_dev_memory import build_index
from scripts.ocelot_repo_map import SOURCE_DIRS
from scripts.ocelot_repo_map_eval import (
    ARMS,
    AREAS,
    CONTENT,
    LISTING,
    ROOT,
    STYLES,
    _run_record,
    baseline_listing,
    code_search_listing,
    context_files,
    evaluate,
    grep_rankings,
    grep_terms,
    leakage,
    load_tasks,
    render_markdown,
    source_files,
    task_set_summary,
)

TASKS_V2 = ROOT / "evaluation" / "repo_map" / "tasks_v2.json"


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


# --------------------------------------------------------------------------- #
# v2: leakage, task-set rules, grep and code_search arms, tiers, staleness
# --------------------------------------------------------------------------- #
def _task(text: str, expected: list[str]) -> dict:
    return {"id": "x", "task": text, "expected_files": expected}


def test_leakage_flags_basename_stem_spaced_stem_and_directory() -> None:
    by_basename = leakage(_task("Update ocelot_repo_map.py to cache tags.",
                                ["scripts/ocelot_repo_map.py"]))
    assert any(r.startswith("basename 'ocelot_repo_map.py'") for r in by_basename)
    assert any(r.startswith("stem 'ocelot_repo_map'") for r in by_basename)

    by_spaced = leakage(_task("Improve the ocelot repo map output.",
                              ["scripts/ocelot_repo_map.py"]))
    assert any(r.startswith("spaced stem 'ocelot repo map'") for r in by_spaced)

    by_dir = leakage(_task("Change the runners loop so it stops.",
                           ["runners/dsl/src/rewrite.rs"]))
    assert any(r.startswith("directory 'runners'") for r in by_dir)
    assert not any(r.startswith("directory 'dsl'") for r in by_dir)

    clean = leakage(_task("A tag cache should notice same-second edits.",
                          ["scripts/ocelot_repo_map.py"]))
    assert clean == []
    # Whole-token matching: "term" inside "determinism" is not the stem term.rs.
    assert leakage(_task("Keep the determinism of the output.",
                         ["runners/dsl/src/term.rs"])) == []


def test_shipped_tasks_v2_meet_leakage_and_design_counts() -> None:
    tasks = load_tasks(TASKS_V2, root=ROOT)
    assert len(tasks) >= 30
    summary = task_set_summary(tasks)
    assert summary["tasks"] == len(tasks)

    # No-leak rule, per task.
    for task in tasks:
        assert leakage(task) == [], task["id"]

    # Area and style counts, per design 1.
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
            assert rel.split("/")[0] in {d.split("/")[0] for d in SOURCE_DIRS}
            assert any(rel.startswith(d + "/") for d in SOURCE_DIRS), rel
            assert (ROOT / rel).is_file(), rel

        # Evidence: recorded commands, real matches, each expected file named.
        evidence = task["evidence"]
        assert evidence, task["id"]
        for item in evidence:
            assert item["command"].startswith("rg "), task["id"]
            assert 1 <= len(item["matches"]) <= 5, task["id"]
        for rel in expected:
            assert any(m.split(":")[0] == rel
                       for item in evidence for m in item["matches"]), (
                task["id"], rel)

        if task["style"] == "symptom":
            text = task["task"]
            assert not re.search(r"[A-Za-z0-9]_[A-Za-z0-9]", text), task["id"]
            assert "(" not in text and "()" not in text, task["id"]
            assert not re.search(r"\w\.\w", text), task["id"]
            assert not re.search(r"\.(py|rs|json|md|lua|sh)\b", text), task["id"]
        else:
            # An identifier task names a function, class or value that is
            # defined in an expected file: snake_case, CamelCase, or Eq.
            names: set[str] = set()
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", task["task"]):
                for part in token.split("."):
                    if ("_" in part or re.search(r"[a-z][A-Z]", part)
                            or part == "Eq"):
                        names.add(part)
            assert names, task["id"]
            bodies = "\n".join((ROOT / rel).read_text(encoding="utf-8",
                                                      errors="replace")
                               for rel in expected)
            assert any(name in bodies for name in names), task["id"]


def test_grep_arm_ranks_distinct_terms_then_occurrences_then_path(
        tmp_path: Path) -> None:
    contents = {
        "a.py": "alpha alpha beta\n",           # distinct 2, total 3
        "b.py": "alpha alpha alpha\n",          # distinct 1, total 3
        "c.py": "alpha beta\n",                 # distinct 2, total 2
        "d.py": "alpha beta alpha beta\n",      # distinct 2, total 4
        "e.py": "gamma only\n",                 # distinct 0
        "f.py": "nothing here\n",               # distinct 0
        "g.py": "nothing here either\n",        # distinct 0
    }
    for rel, text in contents.items():
        (tmp_path / rel).write_text(text, encoding="utf-8")
    task = {"id": "rank", "task": "Alpha and beta behaviour should change.",
            "expected_files": ["a.py"]}

    assert grep_terms(task["task"]) == ["alpha", "beta", "behaviour"]
    ranked = grep_rankings(tmp_path, sorted(contents), [task])["rank"]
    assert ranked == ["d.py", "a.py", "c.py", "b.py", "e.py", "f.py", "g.py"]

    listing = baseline_listing(ranked, 10_000)
    assert listing["files"] == ranked

    # Tie-break on path alone: identical files sort by path ascending.
    (tmp_path / "h.py").write_text("alpha beta\n", encoding="utf-8")
    ranked2 = grep_rankings(tmp_path, sorted(contents) + ["h.py"], [task])["rank"]
    assert ranked2.index("c.py") < ranked2.index("h.py")


def test_code_search_arm_renders_snippets_within_budget_and_marks_content(
        tmp_path: Path) -> None:
    _fixture(tmp_path)
    result = code_search(tmp_path, "alpha feature",
                         cache_path=tmp_path / "var" / "search_tags.json",
                         limit=10)
    assert result["ok"] is True and result["results"]

    rendered = code_search_listing(result, 500)
    assert rendered["estimated_tokens"] <= 500
    assert rendered["files"], "a snippet line should fit a 500-token budget"
    assert rendered["files"][0] == result["results"][0]["path"]
    assert rendered["tiers"][rendered["files"][0]] == CONTENT
    first_line = rendered["text"].splitlines()[0]
    assert first_line.startswith(rendered["files"][0] + ":")
    assert ": " in first_line

    tiny = code_search_listing(result, 5)
    assert tiny["estimated_tokens"] <= 5
    assert tiny["files"] == []


def test_recall_content_differs_from_recall_for_a_listing_tier_hit() -> None:
    run = _run_record(
        task_id="t", budget=500, arm="dev_repo_map",
        selected=["a.py", "b.py"], expected=["a.py"],
        estimated_tokens=10, elapsed_seconds=0.1,
        tiers={"a.py": LISTING, "b.py": CONTENT})
    assert run["recall"] == 1.0
    assert run["recall_content"] == 0.0
    assert run["content_files"] == ["b.py"]

    both = _run_record(
        task_id="t", budget=500, arm="both",
        selected=["a.py", "b.py"], expected=["a.py", "b.py"],
        estimated_tokens=10, elapsed_seconds=0.1,
        tiers={"a.py": CONTENT, "b.py": LISTING})
    assert both["recall"] == 1.0
    assert both["recall_content"] == 0.5


def test_repo_map_full_tier_counts_as_content_on_fixture(tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    report = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500],
                      arms=("dev_repo_map",))
    run = _runs(report, "alpha-feature", 500)["dev_repo_map"]
    assert run["recall"] == 1.0
    assert run["recall_content"] == 1.0
    assert "scripts/alpha.py" in run["content_files"]
    assert report["memory_staleness"] is None


def _git_commit(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-q", "-m", message)


def test_stale_snapshot_raises_unless_allowed(tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    _git(tmp_path, "init", "-q")
    _git_commit(tmp_path, "one")
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=True, include_scripts=False)

    fresh = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500],
                     arms=("dev_context",), memory_path=out)
    assert fresh["memory_staleness"]["stale"] is False

    (tmp_path / "NOTES.md").write_text("second commit\n", encoding="utf-8")
    _git_commit(tmp_path, "two")

    with pytest.raises(RuntimeError, match="does not describe"):
        evaluate(tmp_path, tasks_path=tasks_path, budgets=[500],
                 arms=("dev_context",), memory_path=out)

    stale = evaluate(tmp_path, tasks_path=tasks_path, budgets=[500],
                     arms=("dev_context",), memory_path=out,
                     allow_stale=True)
    assert stale["allow_stale"] is True
    assert stale["memory_staleness"]["stale"] is True
    assert stale["memory_staleness"]["snapshot_head"] != \
        stale["memory_staleness"]["head"]
    assert "stale=True" in stale["markdown"]
    assert {r["arm"] for r in stale["runs"]} == {"dev_context"}


def test_report_fingerprint_is_identical_across_hash_seeds(
        tmp_path: Path) -> None:
    tasks_path = _fixture(tmp_path)
    fingerprints = []
    for seed in ("1", "2"):
        out_json = tmp_path / f"out_{seed}.json"
        env = {**os.environ, "PYTHONHASHSEED": seed,
               "PYTHONPATH": str(ROOT)}
        subprocess.run(
            [sys.executable, "-m", "scripts.ocelot_repo_map_eval",
             "--root", str(tmp_path), "--tasks", str(tasks_path),
             "--arms", "baseline,grep,code_search", "--budgets", "500",
             "--cache", str(tmp_path / "var" / f"cache_{seed}.json"),
             "--out-json", str(out_json), "--quiet"],
            cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["version"] == 2
        assert len(report["runs"]) == 2 * 3
        fingerprints.append(report["deterministic_fingerprint"])
    assert len(fingerprints[0]) == 64
    assert fingerprints[0] == fingerprints[1]


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)
