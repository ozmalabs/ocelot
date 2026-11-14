"""ocelot_repo_map_eval — deterministic, offline retrieval evaluation.

This is the measurement instrument for the repo map. It answers one narrow
question: *given an explicit task and a token budget, which repository files do
the retrieval arms surface, and how many of the known-relevant files do they
recover?*

It does not run an LLM, call the network, edit source, or infer ground truth at
evaluation time. Ground truth is the explicit ``expected_files`` list in
``evaluation/repo_map/tasks.json`` (or any task file passed with ``--tasks``).

Arms per (task, budget):

  baseline      first source files by sorted path, rendered as a plain listing
  dev_context   scripts.ocelot_dev_memory.DevMemory.context(...)
  dev_repo_map  scripts.ocelot_repo_map.repo_map(...)
  both          union of the dev_context and dev_repo_map file sets

The two retrievers are executed once per (task, budget); ``both`` is their
union and its elapsed time/token cost is the sum of the two components. The
budget is therefore applied to each retrieval component, not to the union.

Usage:

    .venv/bin/python -m scripts.ocelot_repo_map_eval \\
        --tasks evaluation/repo_map/tasks.json \\
        --json-out /tmp/repo_map_eval.json \\
        --markdown-out evaluation/repo_map/RESULTS.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS = ROOT / "evaluation" / "repo_map" / "tasks.json"
DEFAULT_BUDGETS = (500, 900, 1500)
ARMS = ("baseline", "dev_context", "dev_repo_map", "both")
ARM_DESCRIPTIONS = {
    "baseline": "Plain source-file listing, sorted by path, truncated to budget.",
    "dev_context": "DevMemory.context items/snippets, executed at the budget.",
    "dev_repo_map": "Ranked repo map, executed at the budget.",
    "both": "Union of the dev_context and dev_repo_map file sets.",
}


# --------------------------------------------------------------------------- #
# Task loading and mechanical path helpers
# --------------------------------------------------------------------------- #
def _normalise_rel(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    path = value.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path or None


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        path = _normalise_rel(value)
        if path is None or path in seen:
            continue
        seen.add(path)
        out.append(path)
    return out


def _load_task_document(path: str | Path) -> tuple[list[dict[str, Any]],
                                                   dict[str, Any]]:
    task_path = Path(path)
    try:
        data = json.loads(task_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read task file {task_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in task file {task_path}: {exc}") from exc

    if isinstance(data, dict):
        raw_tasks = data.get("tasks")
        meta = {k: v for k, v in data.items() if k != "tasks"}
    else:
        raw_tasks = data
        meta = {}
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError(f"{task_path}: expected a non-empty 'tasks' list")

    tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_tasks):
        where = f"{task_path}: tasks[{index}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{where}: task entry must be an object")
        task_id = str(raw.get("id") or "").strip()
        text = raw.get("task") or raw.get("text")
        expected = raw.get("expected_files")
        if not task_id:
            raise ValueError(f"{where}: missing id")
        if task_id in seen_ids:
            raise ValueError(f"{where}: duplicate id {task_id!r}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{where}: missing task text")
        if not isinstance(expected, list) or not expected:
            raise ValueError(f"{where}: expected_files must be a non-empty list")
        expected_files = _unique(expected)
        if not expected_files:
            raise ValueError(f"{where}: expected_files contains no valid paths")
        for rel in expected_files:
            if rel.startswith("/") or ".." in rel.split("/"):
                raise ValueError(
                    f"{where}: expected path must be repository-relative: {rel!r}")
        task = {"id": task_id, "task": text.strip(),
                "expected_files": expected_files}
        if isinstance(raw.get("notes"), str) and raw["notes"].strip():
            task["notes"] = raw["notes"].strip()
        seen_ids.add(task_id)
        tasks.append(task)
    return tasks, meta


def load_tasks(path: str | Path, *, root: str | Path | None = None) -> list[dict[str, Any]]:
    """Load and validate explicit tasks. Never derives ``expected_files``."""
    tasks, _meta = _load_task_document(path)
    if root is not None:
        base = Path(root).resolve()
        for task in tasks:
            for rel in task["expected_files"]:
                if not (base / rel).is_file():
                    raise ValueError(
                        f"task {task['id']!r}: expected file does not exist: {rel}")
    return tasks


def source_files(root: str | Path = ROOT) -> list[str]:
    """The same source-file universe the repo map indexes, globally sorted."""
    from scripts.ocelot_repo_map import _source_files
    return sorted(set(_source_files(Path(root).resolve())))


# --------------------------------------------------------------------------- #
# Arms
# --------------------------------------------------------------------------- #
def baseline_listing(files: Iterable[str],
                     budget_tokens: int) -> dict[str, Any]:
    """A plain file listing: first paths by sorted order, inside the budget."""
    budget = max(1, int(budget_tokens))
    selected: list[str] = []
    for rel in files:
        trial = selected + [str(rel)]
        text = "\n".join(trial)
        if len(text) // 4 > budget:
            break
        selected = trial
    text = "\n".join(selected)
    return {"files": selected, "text": text,
            "estimated_tokens": len(text) // 4}


def context_files(result: dict[str, Any]) -> list[str]:
    """File set from DevMemory.context items and snippets, in item order."""
    values: list[str] = []
    for item in result.get("items") or []:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attrs") or {}
        snippet = item.get("snippet") or {}
        if isinstance(attrs, dict):
            values.extend([attrs.get("path"), attrs.get("file")])
        if isinstance(snippet, dict):
            values.append(snippet.get("path"))
    return _unique(v for v in values if isinstance(v, str))


def _score_files(expected: Iterable[str],
                 selected: Iterable[str]) -> dict[str, Any]:
    expected_files = _unique(expected)
    selected_files = _unique(selected)
    selected_set = set(selected_files)
    expected_set = set(expected_files)
    hits = [rel for rel in expected_files if rel in selected_set]
    misses = [rel for rel in expected_files if rel not in selected_set]
    expected_n = len(expected_files)
    selected_n = len(selected_files)
    return {
        "expected_count": expected_n,
        "selected_count": selected_n,
        "hits": hits,
        "misses": misses,
        "recall": round(len(hits) / expected_n, 6) if expected_n else 0.0,
        "precision": round(len(hits) / selected_n, 6) if selected_n else 0.0,
    }


def _cache_record(result: dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        return {"applicable": False, "parsed": None, "reused": None,
                "cached_files": None}
    cache = result.get("cache") or {}
    return {
        "applicable": True,
        "parsed": int(cache.get("parsed") or 0),
        "reused": int(cache.get("reused") or 0),
        "cached_files": int(cache.get("cached_files") or 0),
    }


def _run_record(*, task_id: str, budget: int, arm: str,
                selected: Iterable[str], expected: Iterable[str],
                estimated_tokens: int, elapsed_seconds: float,
                cache: dict[str, Any] | None = None,
                extra: dict[str, Any] | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "task_id": task_id,
        "budget_tokens": int(budget),
        "arm": arm,
        "files": _unique(selected),
        "estimated_tokens": int(estimated_tokens),
        "elapsed_seconds": round(float(elapsed_seconds), 4),
        "budget_respected": int(estimated_tokens) <= int(budget),
        "cache": cache or {"applicable": False, "parsed": None,
                           "reused": None, "cached_files": None},
        **_score_files(expected, selected),
    }
    if extra:
        record.update(extra)
    return record


def _parse_budgets(values: Iterable[int] | str) -> tuple[int, ...]:
    if isinstance(values, str):
        raw = [part.strip() for part in values.split(",") if part.strip()]
        try:
            parsed = [int(part) for part in raw]
        except ValueError as exc:
            raise ValueError(f"invalid --budgets value: {values!r}") from exc
    else:
        parsed = [int(v) for v in values]
    if not parsed:
        raise ValueError("at least one budget is required")
    if any(v <= 0 for v in parsed):
        raise ValueError("budgets must be positive integers")
    return tuple(sorted(set(parsed)))


def _parse_arms(values: Iterable[str] | str) -> tuple[str, ...]:
    if isinstance(values, str):
        wanted = {part.strip() for part in values.split(",") if part.strip()}
    else:
        wanted = {str(part).strip() for part in values}
    unknown = sorted(wanted - set(ARMS))
    if unknown:
        raise ValueError(f"unknown arms: {', '.join(unknown)}")
    if not wanted:
        raise ValueError("at least one arm is required")
    return tuple(arm for arm in ARMS if arm in wanted)


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def _fingerprint(runs: Iterable[dict[str, Any]]) -> str:
    payload = [
        [run["task_id"], run["budget_tokens"], run["arm"], run["files"],
         run["recall"], run["precision"], run["estimated_tokens"]]
        for run in runs
    ]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def aggregate(runs: Iterable[dict[str, Any]], budgets: Iterable[int],
              arms: Iterable[str]) -> list[dict[str, Any]]:
    """Mean retrieval metrics per (budget, arm), with deterministic rows."""
    run_list = list(runs)
    rows: list[dict[str, Any]] = []
    for budget in budgets:
        for arm in arms:
            group = [r for r in run_list
                     if r["budget_tokens"] == int(budget) and r["arm"] == arm]
            if not group:
                continue
            n = len(group)
            mean = lambda key: round(sum(float(r[key]) for r in group) / n, 6)
            rows.append({
                "budget_tokens": int(budget),
                "arm": arm,
                "tasks": n,
                "mean_recall_at_budget": mean("recall"),
                "mean_precision": mean("precision"),
                "mean_selected_files": round(
                    sum(r["selected_count"] for r in group) / n, 4),
                "mean_estimated_tokens": round(
                    sum(r["estimated_tokens"] for r in group) / n, 2),
                "mean_elapsed_seconds": round(
                    sum(r["elapsed_seconds"] for r in group) / n, 4),
                "cache_parsed": sum(
                    int(r["cache"].get("parsed") or 0) for r in group
                    if r["cache"].get("applicable")),
                "cache_reused": sum(
                    int(r["cache"].get("reused") or 0) for r in group
                    if r["cache"].get("applicable")),
                "budget_respected_runs": sum(
                    1 for r in group if r["budget_respected"]),
                "recall_1_tasks": sum(
                    1 for r in group if float(r["recall"]) >= 1.0),
            })
    return rows


def evaluate(
    root: str | Path = ROOT,
    *,
    tasks_path: str | Path = DEFAULT_TASKS,
    budgets: Iterable[int] | str = DEFAULT_BUDGETS,
    arms: Iterable[str] | str = ARMS,
    cache_path: str | Path | None = None,
    memory_path: str | Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Run the deterministic evaluation and return the JSON report."""
    started = time.perf_counter()
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError(f"root is not a directory: {base}")
    tasks, meta = _load_task_document(tasks_path)
    if limit is not None:
        if int(limit) <= 0:
            raise ValueError("--limit must be positive")
        tasks = tasks[:int(limit)]
    for task in tasks:
        for rel in task["expected_files"]:
            if not (base / rel).is_file():
                raise ValueError(
                    f"task {task['id']!r}: expected file does not exist: {rel}")

    budget_list = _parse_budgets(budgets)
    arm_list = _parse_arms(arms)
    files = source_files(base)
    file_set = set(files)
    universe_misses = sorted({
        rel for task in tasks for rel in task["expected_files"]
        if rel not in file_set
    })

    cache = Path(cache_path) if cache_path is not None else (
        base / "var" / "ocelot_repo_map_eval_tags.json")
    memory = Path(memory_path) if memory_path is not None else (
        base / "var" / "ocelot_dev_graph.json")
    needs_context = any(a in arm_list for a in ("dev_context", "both"))
    needs_map = any(a in arm_list for a in ("dev_repo_map", "both"))

    mem = None
    if needs_context:
        from scripts.ocelot_dev_memory import DevMemory
        if not memory.is_file():
            raise RuntimeError(
                f"no dev-memory snapshot at {memory}; run "
                "`.venv/bin/python -m scripts.ocelot_dev_memory build`")
        mem = DevMemory(dump=memory,
                        journal=memory.with_name("ocelot_dev_journal.jsonl"))

    repo_map_fn = None
    if needs_map:
        from scripts.ocelot_repo_map import repo_map as repo_map_fn

    runs: list[dict[str, Any]] = []
    for task in tasks:
        task_id = task["id"]
        text = task["task"]
        expected = task["expected_files"]
        for budget in budget_list:
            context_result: dict[str, Any] | None = None
            context_selected: list[str] = []
            context_tokens = 0
            context_elapsed = 0.0
            if needs_context:
                t0 = time.perf_counter()
                context_result = mem.context(text, budget_tokens=budget)
                context_elapsed = time.perf_counter() - t0
                context_selected = context_files(context_result)
                context_tokens = int(
                    (context_result.get("budget") or {}).get("estimated_tokens")
                    or 0)

            map_result: dict[str, Any] | None = None
            map_selected: list[str] = []
            map_tokens = 0
            map_elapsed = 0.0
            if needs_map:
                t0 = time.perf_counter()
                map_result = repo_map_fn(
                    base, task=text, budget_tokens=budget,
                    cache_path=cache, files=files)
                map_elapsed = time.perf_counter() - t0
                map_selected = [f["path"] for f in map_result.get("files") or []]
                map_tokens = int(map_result.get("estimated_tokens") or 0)

            for arm in arm_list:
                if arm == "baseline":
                    t0 = time.perf_counter()
                    listing = baseline_listing(files, budget)
                    elapsed = time.perf_counter() - t0
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=listing["files"], expected=expected,
                        estimated_tokens=listing["estimated_tokens"],
                        elapsed_seconds=elapsed))
                elif arm == "dev_context":
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=context_selected, expected=expected,
                        estimated_tokens=context_tokens,
                        elapsed_seconds=context_elapsed,
                        extra={"items": len(
                            (context_result or {}).get("items") or [])}))
                elif arm == "dev_repo_map":
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=map_selected, expected=expected,
                        estimated_tokens=map_tokens,
                        elapsed_seconds=map_elapsed,
                        cache=_cache_record(map_result),
                        extra={"map_files": len(map_selected)}))
                else:
                    component_tokens = {
                        "dev_context": context_tokens,
                        "dev_repo_map": map_tokens,
                    }
                    components_within = all(
                        tokens <= budget
                        for tokens in component_tokens.values())
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=context_selected + map_selected,
                        expected=expected,
                        estimated_tokens=context_tokens + map_tokens,
                        elapsed_seconds=context_elapsed + map_elapsed,
                        cache=_cache_record(map_result),
                        extra={
                            "component_estimated_tokens": component_tokens,
                            "components_within_budget": components_within,
                        }))

    aggregates = aggregate(runs, budget_list, arm_list)
    report: dict[str, Any] = {
        "ok": True,
        "tool": "ocelot_repo_map_eval",
        "version": 1,
        "root": str(base),
        "tasks_path": str(Path(tasks_path).resolve()),
        "task_set": meta,
        "task_count": len(tasks),
        "source_files": len(files),
        "budgets": list(budget_list),
        "arms": list(arm_list),
        "arm_descriptions": {arm: ARM_DESCRIPTIONS[arm] for arm in arm_list},
        "cache_path": str(cache),
        "memory_path": str(memory) if needs_context else None,
        "expected_files_outside_source_universe": universe_misses,
        "total_elapsed_seconds": round(time.perf_counter() - started, 3),
        "deterministic_fingerprint": _fingerprint(runs),
        "tasks": tasks,
        "aggregates": aggregates,
        "runs": runs,
    }
    report["markdown"] = render_markdown(report)
    return report


# --------------------------------------------------------------------------- #
# Markdown report
# --------------------------------------------------------------------------- #
def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    """Render a compact, deterministic human report."""
    lines: list[str] = ["# Repo-map retrieval evaluation", ""]
    lines.append(f"- Root: `{report['root']}`")
    lines.append(f"- Tasks: {report['task_count']} "
                 f"(`{report['tasks_path']}`)")
    lines.append(f"- Source-file universe: {report['source_files']}")
    lines.append("- Budgets: " + ", ".join(
        str(b) for b in report["budgets"]) + " tokens")
    lines.append("- Arms: " + ", ".join(report["arms"]))
    lines.append(f"- Deterministic fingerprint: "
                 f"`{report['deterministic_fingerprint']}`")
    lines.append(f"- Wall time: {report['total_elapsed_seconds']} s")
    if report.get("expected_files_outside_source_universe"):
        lines.append("- Warning: expected files outside the indexed source "
                     "universe: " + ", ".join(
                         f"`{p}`" for p in
                         report["expected_files_outside_source_universe"]))
    lines.extend(["", "## Aggregate metrics", ""])
    lines.append("| Budget | Arm | Tasks | Mean recall@budget | Mean precision | "
                 "Mean files | Mean tokens | Mean s | Cache parsed | Cache reused |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregates"]:
        lines.append(
            f"| {row['budget_tokens']} | {row['arm']} | {row['tasks']} | "
            f"{row['mean_recall_at_budget']:.3f} | "
            f"{row['mean_precision']:.3f} | "
            f"{row['mean_selected_files']:.1f} | "
            f"{row['mean_estimated_tokens']:.0f} | "
            f"{row['mean_elapsed_seconds']:.2f} | "
            f"{row['cache_parsed']} | {row['cache_reused']} |")
    lines.extend(["", "## Recall by task", ""])
    for budget in report["budgets"]:
        lines.append(f"### {budget} tokens")
        lines.append("")
        lines.append("| Task | " + " | ".join(report["arms"]) + " |")
        lines.append("|---|" + "|".join("---:" for _ in report["arms"]) + "|")
        for task in report["tasks"]:
            cells = []
            for arm in report["arms"]:
                run = next((r for r in report["runs"]
                            if r["task_id"] == task["id"]
                            and r["budget_tokens"] == budget
                            and r["arm"] == arm), None)
                cells.append(f"{run['recall']:.2f}" if run else "-")
            lines.append(f"| {_cell(task['id'])} | " + " | ".join(cells) + " |")
        lines.append("")
    lines.extend(["## Task set", "",
                  "| Task | Expected files | Notes |",
                  "|---|---|---|"])
    for task in report["tasks"]:
        expected = "<br>".join(f"`{_cell(p)}`" for p in task["expected_files"])
        lines.append(f"| {_cell(task['id'])} | {expected} | "
                     f"{_cell(task.get('notes', ''))} |")
    lines.extend(["", "## Reading these numbers", "",
                  "- This is a **retrieval instrument**, not an end-to-end "
                  "coding benchmark: it measures whether known-relevant files "
                  "are selected, not whether an agent completes a change.",
                  "- `baseline` is a sorted-path file-listing control, not a "
                  "semantic retriever.",
                  "- Token estimates are each module's own ~4-chars/token "
                  "heuristic. Cache counts apply only to repo-map arms.",
                  "- `both` is the literal union of the two retrievers run at "
                  "the same budget; its token cost and latency are the sum of "
                  "the components, so its budget is per component (up to 2x "
                  "the nominal budget). Compare it as a cost/recall trade-off, "
                  "not as an equal-token arm.",
                  "- Ground truth is frozen in the task JSON. Re-run the "
                  "scoped tests after moving or renaming an expected file.",
                  ""])
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic, offline repo-map retrieval evaluation.")
    parser.add_argument("--root", default=str(ROOT),
                        help="repository root to evaluate (default: ocelot)")
    parser.add_argument("--tasks", default=str(DEFAULT_TASKS),
                        help="explicit task JSON (default: evaluation/repo_map/tasks.json)")
    parser.add_argument("--budgets", default=",".join(map(str, DEFAULT_BUDGETS)),
                        help="comma-separated token budgets (default: 500,900,1500)")
    parser.add_argument("--arms", default=",".join(ARMS),
                        help="comma-separated arms: " + ",".join(ARMS))
    parser.add_argument("--cache", default=None,
                        help="repo-map tag cache path (default: <root>/var/ocelot_repo_map_eval_tags.json)")
    parser.add_argument("--memory", default=None,
                        help="dev-memory snapshot path (default: <root>/var/ocelot_dev_graph.json)")
    parser.add_argument("--limit", type=int, default=None,
                        help="evaluate only the first N tasks (deterministic)")
    parser.add_argument("--json-out", default=None,
                        help="write the full JSON report to this path")
    parser.add_argument("--markdown-out", default=None,
                        help="write the markdown report to this path")
    parser.add_argument("--json", action="store_true",
                        help="print JSON instead of markdown when no output path is given")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress stdout")
    args = parser.parse_args(argv)

    try:
        report = evaluate(
            args.root, tasks_path=args.tasks, budgets=args.budgets,
            arms=args.arms, cache_path=args.cache, memory_path=args.memory,
            limit=args.limit)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"repo-map-eval: {exc}", file=sys.stderr)
        return 2

    markdown = report["markdown"]
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        out = Path(args.markdown_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")

    if not args.quiet:
        if args.json:
            print(json.dumps(report, indent=2))
        elif args.json_out is None and args.markdown_out is None:
            print(markdown)
        else:
            print(f"repo-map-eval: tasks={report['task_count']} "
                  f"runs={len(report['runs'])} "
                  f"fingerprint={report['deterministic_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
