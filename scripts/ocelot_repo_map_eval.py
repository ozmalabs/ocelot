"""ocelot_repo_map_eval — deterministic, offline retrieval evaluation.

This is the measurement instrument for the repo map. It answers one narrow
question: *given an explicit task and a token budget, which repository files do
the retrieval arms surface, and how many of the known-relevant files do they
recover?*

It does not run an LLM, call the network, edit source, or infer ground truth at
evaluation time. Ground truth is the explicit ``expected_files`` list in the
task file (``evaluation/repo_map/tasks.json`` for v1,
``evaluation/repo_map/tasks_v2.json`` for v2, or any file passed with ``--tasks``).

Arms per (task, budget):

  baseline      first source files by sorted path, rendered as a plain listing
  dev_context   scripts.ocelot_dev_memory.DevMemory.context(...)
  dev_repo_map  scripts.ocelot_repo_map.repo_map(...)
  both          union of the dev_context and dev_repo_map file sets
  grep          lexical baseline: files ranked by distinct task terms they contain
  code_search   scripts.ocelot_code_search.code_search(...) results with snippets

The two retrievers are executed once per (task, budget); ``both`` is their
union and its elapsed time/token cost is the sum of the two components. The
budget is therefore applied to each retrieval component, not to the union.

Every selected file carries a tier. ``content`` means the arm showed code for
that file (a code_search snippet, a dev_context item with snippet text, or a
repo-map ``full``/``outline`` entry). ``listing`` means the arm only named the
path. ``recall`` counts a hit at any tier; ``recall_content`` counts only
content-tier hits.

Usage:

    .venv/bin/python -m scripts.ocelot_repo_map_eval \\
        --tasks evaluation/repo_map/tasks_v2.json \\
        --memory var/ocelot_dev_graph.json \\
        --out-json evaluation/repo_map/results_v2.json \\
        --out-md evaluation/repo_map/RESULTS_V2.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS = ROOT / "evaluation" / "repo_map" / "tasks.json"
DEFAULT_BUDGETS = (500, 900, 1500)
ARMS = ("baseline", "dev_context", "dev_repo_map", "both", "grep",
        "code_search")
ARM_DESCRIPTIONS = {
    "baseline": "Plain source-file listing, sorted by path, truncated to budget.",
    "dev_context": "DevMemory.context items/snippets, executed at the budget.",
    "dev_repo_map": "Ranked repo map, executed at the budget.",
    "both": "Union of the dev_context and dev_repo_map file sets.",
    "grep": "Lexical baseline: files ranked by distinct task terms found in "
            "their text, then total occurrences, then path.",
    "code_search": "scripts.ocelot_code_search.code_search results, rendered "
                   "as path:line: snippet in result order, truncated to budget.",
}
STYLES = ("symptom", "identifier")
AREAS = ("dev_tooling", "rust_engine", "seeds_boot", "domains", "substrate",
         "worlds_or_tools")
CONTENT = "content"
LISTING = "listing"
# repo_map tiers that show code (signatures or full bodies) rather than paths.
REPO_MAP_CONTENT_TIERS = ("full", "outline")
CODE_SEARCH_LIMIT = 50
# Words of length >= 4 that carry no retrieval signal for the grep arm.
GREP_STOPWORDS = frozenset({
    "about", "across", "add", "adds", "after", "again", "against", "all",
    "also", "any", "are", "because", "been", "before", "between", "both",
    "but", "can", "change", "changed", "changes", "could", "does", "done",
    "each", "ensure", "every", "file", "files", "from", "function", "have",
    "into", "its", "just", "keep", "make", "makes", "more", "most", "must",
    "need", "needs", "only", "other", "our", "out", "over", "should", "some",
    "such", "than", "that", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "under", "until", "use", "used", "uses",
    "using", "want", "was", "were", "what", "when", "where", "which", "while",
    "will", "with", "within", "without", "would", "your", "code", "module",
    "fix", "fixed", "allow", "instead", "get", "gets", "set", "sets",
})


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


def _check_evidence(where: str, evidence: Any) -> list[dict[str, Any]]:
    if not isinstance(evidence, list):
        raise ValueError(f"{where}: evidence must be a list")
    out: list[dict[str, Any]] = []
    for j, item in enumerate(evidence):
        if (not isinstance(item, dict)
                or not isinstance(item.get("command"), str)
                or not isinstance(item.get("matches"), list)
                or not all(isinstance(m, str) for m in item["matches"])):
            raise ValueError(
                f"{where}: evidence[{j}] needs a string 'command' and a "
                "list of string 'matches'")
        out.append({"command": item["command"],
                    "matches": list(item["matches"])})
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
        if raw.get("style") is not None:
            if raw["style"] not in STYLES:
                raise ValueError(f"{where}: style must be one of {STYLES}")
            task["style"] = raw["style"]
        if raw.get("area") is not None:
            if raw["area"] not in AREAS:
                raise ValueError(f"{where}: area must be one of {AREAS}")
            task["area"] = raw["area"]
        if raw.get("evidence") is not None:
            task["evidence"] = _check_evidence(where, raw["evidence"])
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
# Leakage and task-set checks
# --------------------------------------------------------------------------- #
def _term_pattern(term: str) -> re.Pattern[str]:
    # Whole-token match, so "term" does not fire on "determinism" and
    # "persist" does not fire on "persistence". Underscore is a token char.
    return re.compile(r"(?<![a-z0-9_])" + re.escape(term) + r"(?![a-z0-9_])")


def leakage(task: dict[str, Any]) -> list[str]:
    """Names that give away an expected file inside the task text.

    For each expected file this checks the lower-cased task text for its
    basename, its stem, its stem with ``_`` replaced by a space, and every
    directory component longer than three characters. Returns an empty list
    for a clean task. Individual words of a stem are allowed.
    """
    text = str(task.get("task") or "").lower()
    found: dict[str, None] = {}
    for rel in task.get("expected_files") or []:
        path = PurePosixPath(str(rel))
        stem = path.stem.lower()
        candidates: list[tuple[str, str]] = [
            ("basename", path.name.lower()),
            ("stem", stem),
        ]
        if "_" in stem:
            candidates.append(("spaced stem", stem.replace("_", " ")))
        for part in path.parts[:-1]:
            if len(part) > 3:
                candidates.append(("directory", part.lower()))
        for kind, term in candidates:
            if _term_pattern(term).search(text):
                found[f"{kind} {term!r} in {rel}"] = None
    return list(found)


def task_set_summary(tasks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Counts by area and style, for the report and the shipped-set test."""
    rows = list(tasks)
    by_area = Counter(str(t.get("area") or "unspecified") for t in rows)
    by_style = Counter(str(t.get("style") or "unspecified") for t in rows)
    return {
        "tasks": len(rows),
        "by_area": {k: by_area[k] for k in sorted(by_area)},
        "by_style": {k: by_style[k] for k in sorted(by_style)},
        "expected_files_total": sum(len(t["expected_files"]) for t in rows),
    }


# --------------------------------------------------------------------------- #
# Arms
# --------------------------------------------------------------------------- #
def _listing(paths: Iterable[str], budget_tokens: int) -> dict[str, Any]:
    """Paths in order, inside the token estimate (chars // 4)."""
    budget = max(1, int(budget_tokens))
    selected: list[str] = []
    for rel in paths:
        trial = selected + [str(rel)]
        text = "\n".join(trial)
        if len(text) // 4 > budget:
            break
        selected = trial
    text = "\n".join(selected)
    return {"files": selected, "text": text,
            "estimated_tokens": len(text) // 4,
            "tiers": {rel: LISTING for rel in selected}}


def baseline_listing(files: Iterable[str],
                     budget_tokens: int) -> dict[str, Any]:
    """A plain file listing: first paths by sorted order, inside the budget."""
    return _listing(files, budget_tokens)


def grep_terms(task_text: str) -> list[str]:
    """Distinct lower-cased words of length >= 4, minus GREP_STOPWORDS."""
    terms: list[str] = []
    for word in re.findall(r"[a-z0-9_]+", str(task_text).lower()):
        if (len(word) < 4 or word.isdigit() or word in GREP_STOPWORDS
                or word in terms):
            continue
        terms.append(word)
    return terms


def grep_rankings(root: str | Path, files: Iterable[str],
                  tasks: Iterable[dict[str, Any]]) -> dict[str, list[str]]:
    """Rank every file for every task in one pass that reads each file once.

    Sort key per (task, file): distinct terms present (desc), total term
    occurrences (desc), path (asc). Occurrences are case-insensitive substring
    counts over the file text.
    """
    base = Path(root).resolve()
    term_map = {task["id"]: grep_terms(task["task"]) for task in tasks}
    rows: dict[str, list[tuple[int, int, str]]] = {
        task_id: [] for task_id in term_map}
    for rel in files:
        try:
            text = (base / rel).read_text(
                encoding="utf-8", errors="replace").lower()
        except OSError:
            text = ""
        for task_id, terms in term_map.items():
            counts = [text.count(term) for term in terms]
            distinct = sum(1 for c in counts if c)
            rows[task_id].append((-distinct, -sum(counts), rel))
    return {task_id: [rel for *_, rel in sorted(items)]
            for task_id, items in rows.items()}


def code_search_listing(result: dict[str, Any],
                        budget_tokens: int) -> dict[str, Any]:
    """Render code_search results as ``path:line: snippet`` inside the budget.

    A result with a snippet is content tier; a result without one is listed by
    path alone (listing tier).
    """
    budget = max(1, int(budget_tokens))
    lines: list[str] = []
    selected: list[str] = []
    tiers: dict[str, str] = {}
    for item in result.get("results") or []:
        if not isinstance(item, dict):
            continue
        rel = _normalise_rel(item.get("path"))
        if rel is None or rel in tiers:
            continue
        snippet = item.get("snippet")
        if isinstance(snippet, str) and snippet.strip():
            line = f"{rel}:{item.get('line')}: {snippet.strip()}"
            tier = CONTENT
        else:
            line = rel
            tier = LISTING
        trial = lines + [line]
        if len("\n".join(trial)) // 4 > budget:
            break
        lines = trial
        selected.append(rel)
        tiers[rel] = tier
    text = "\n".join(lines)
    return {"files": selected, "text": text,
            "estimated_tokens": len(text) // 4, "tiers": tiers}


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


def context_tiers(result: dict[str, Any]) -> dict[str, str]:
    """Tier per context path: content if any item for it carries snippet text."""
    tiers: dict[str, str] = {}
    for item in result.get("items") or []:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attrs") or {}
        snippet = item.get("snippet") or {}
        values: list[Any] = []
        has_text = False
        if isinstance(attrs, dict):
            values.extend([attrs.get("path"), attrs.get("file")])
        if isinstance(snippet, dict):
            values.append(snippet.get("path"))
            has_text = bool(str(snippet.get("text") or "").strip())
        tier = CONTENT if has_text else LISTING
        for value in values:
            rel = _normalise_rel(value)
            if rel is None:
                continue
            if tiers.get(rel) != CONTENT:
                tiers[rel] = tier
    return tiers


def repo_map_tiers(map_result: dict[str, Any] | None) -> dict[str, str]:
    """Tier per repo-map file: full and outline show code, listing does not."""
    tiers: dict[str, str] = {}
    for entry in (map_result or {}).get("files") or []:
        rel = _normalise_rel(entry.get("path"))
        if rel is None:
            continue
        tiers[rel] = (CONTENT if entry.get("tier") in REPO_MAP_CONTENT_TIERS
                      else LISTING)
    return tiers


def merge_tiers(*maps: dict[str, str]) -> dict[str, str]:
    """Union of tier maps; content wins over listing for the same path."""
    out: dict[str, str] = {}
    for tiers in maps:
        for rel, tier in tiers.items():
            if out.get(rel) != CONTENT:
                out[rel] = tier
    return out


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


def _run_record(*, task_id: str, budget: int, arm: str,
                selected: Iterable[str], expected: Iterable[str],
                estimated_tokens: int, elapsed_seconds: float,
                cache: dict[str, Any] | None = None,
                tiers: dict[str, str] | None = None,
                extra: dict[str, Any] | None = None) -> dict[str, Any]:
    files = _unique(selected)
    tier_map = {rel: (tiers or {}).get(rel, LISTING) for rel in files}
    score = _score_files(expected, files)
    expected_n = score["expected_count"]
    content_hits = [rel for rel in score["hits"]
                    if tier_map.get(rel) == CONTENT]
    record: dict[str, Any] = {
        "task_id": task_id,
        "budget_tokens": int(budget),
        "arm": arm,
        "files": files,
        "estimated_tokens": int(estimated_tokens),
        "elapsed_seconds": round(float(elapsed_seconds), 4),
        "budget_respected": int(estimated_tokens) <= int(budget),
        "cache": cache or {"applicable": False, "parsed": None,
                           "reused": None, "cached_files": None},
        **score,
        "recall_content": (round(len(content_hits) / expected_n, 6)
                           if expected_n else 0.0),
        "content_files": [rel for rel in files if tier_map[rel] == CONTENT],
    }
    if extra:
        record.update(extra)
    return record


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def _fingerprint(runs: Iterable[dict[str, Any]]) -> str:
    payload = [
        [run["task_id"], run["budget_tokens"], run["arm"], run["files"],
         run["recall"], run["recall_content"], run["precision"],
         run["estimated_tokens"]]
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
                "mean_recall_content_at_budget": mean("recall_content"),
                "mean_precision": mean("precision"),
                "mean_selected_files": round(
                    sum(r["selected_count"] for r in group) / n, 4),
                "mean_content_files": round(
                    sum(len(r.get("content_files") or []) for r in group) / n, 4),
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


def _staleness_error(memory: Path, base: Path, staleness: dict[str, Any]) -> str:
    return (
        f"dev-memory snapshot {memory} does not describe {base}: "
        f"stale=True (root_mismatch={staleness.get('root_mismatch')}, "
        f"snapshot_head={staleness.get('snapshot_head')}, "
        f"head={staleness.get('head')}). Rebuild it with "
        f"`.venv/bin/python -m scripts.ocelot_dev_memory build --root {base} "
        f"--out {memory}`, or pass --allow-stale to evaluate the stale "
        "snapshot anyway.")


def evaluate(
    root: str | Path = ROOT,
    *,
    tasks_path: str | Path = DEFAULT_TASKS,
    budgets: Iterable[int] | str = DEFAULT_BUDGETS,
    arms: Iterable[str] | str = ARMS,
    cache_path: str | Path | None = None,
    memory_path: str | Path | None = None,
    limit: int | None = None,
    allow_stale: bool = False,
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
    memory_staleness: dict[str, Any] | None = None
    if needs_context:
        from scripts.ocelot_dev_memory import DevMemory
        if not memory.is_file():
            raise RuntimeError(
                f"no dev-memory snapshot at {memory}; run "
                "`.venv/bin/python -m scripts.ocelot_dev_memory build`")
        mem = DevMemory(dump=memory,
                        journal=memory.with_name("ocelot_dev_journal.jsonl"),
                        root=base)
        memory_staleness = mem.staleness()
        if memory_staleness["stale"] and not allow_stale:
            raise RuntimeError(_staleness_error(memory, base, memory_staleness))

    repo_map_fn = None
    if needs_map:
        from scripts.ocelot_repo_map import repo_map as repo_map_fn

    code_search_fn = None
    if "code_search" in arm_list:
        from scripts.ocelot_code_search import code_search as code_search_fn

    grep_orders: dict[str, list[str]] = {}
    grep_share = 0.0
    if "grep" in arm_list:
        t0 = time.perf_counter()
        grep_orders = grep_rankings(base, files, tasks)
        grep_share = (time.perf_counter() - t0) / max(1, len(tasks))

    runs: list[dict[str, Any]] = []
    for task in tasks:
        task_id = task["id"]
        text = task["task"]
        expected = task["expected_files"]

        code_result: dict[str, Any] | None = None
        code_elapsed = 0.0
        if code_search_fn is not None:
            t0 = time.perf_counter()
            code_result = code_search_fn(
                base, text, limit=CODE_SEARCH_LIMIT, cache_path=cache,
                files=files)
            code_elapsed = time.perf_counter() - t0

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
                        elapsed_seconds=elapsed,
                        tiers=listing["tiers"]))
                elif arm == "grep":
                    t0 = time.perf_counter()
                    listing = _listing(grep_orders[task_id], budget)
                    elapsed = grep_share + (time.perf_counter() - t0)
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=listing["files"], expected=expected,
                        estimated_tokens=listing["estimated_tokens"],
                        elapsed_seconds=elapsed,
                        tiers=listing["tiers"],
                        extra={"terms": len(grep_terms(text))}))
                elif arm == "code_search":
                    t0 = time.perf_counter()
                    rendered = code_search_listing(code_result or {}, budget)
                    elapsed = code_elapsed + (time.perf_counter() - t0)
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=rendered["files"], expected=expected,
                        estimated_tokens=rendered["estimated_tokens"],
                        elapsed_seconds=elapsed,
                        tiers=rendered["tiers"],
                        extra={"results": len(
                            (code_result or {}).get("results") or [])}))
                elif arm == "dev_context":
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=context_selected, expected=expected,
                        estimated_tokens=context_tokens,
                        elapsed_seconds=context_elapsed,
                        tiers=context_tiers(context_result or {}),
                        extra={"items": len(
                            (context_result or {}).get("items") or [])}))
                elif arm == "dev_repo_map":
                    runs.append(_run_record(
                        task_id=task_id, budget=budget, arm=arm,
                        selected=map_selected, expected=expected,
                        estimated_tokens=map_tokens,
                        elapsed_seconds=map_elapsed,
                        tiers=repo_map_tiers(map_result),
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
                        tiers=merge_tiers(context_tiers(context_result or {}),
                                          repo_map_tiers(map_result)),
                        cache=_cache_record(map_result),
                        extra={
                            "component_estimated_tokens": component_tokens,
                            "components_within_budget": components_within,
                        }))

    aggregates = aggregate(runs, budget_list, arm_list)
    report: dict[str, Any] = {
        "ok": True,
        "tool": "ocelot_repo_map_eval",
        "version": 2,
        "root": str(base),
        "tasks_path": str(Path(tasks_path).resolve()),
        "task_set": meta,
        "task_set_summary": task_set_summary(tasks),
        "task_count": len(tasks),
        "source_files": len(files),
        "budgets": list(budget_list),
        "arms": list(arm_list),
        "arm_descriptions": {arm: ARM_DESCRIPTIONS[arm] for arm in arm_list},
        "cache_path": str(cache),
        "memory_path": str(memory) if needs_context else None,
        "memory_staleness": memory_staleness,
        "allow_stale": bool(allow_stale),
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
    staleness = report.get("memory_staleness")
    if staleness is not None:
        lines.append(
            f"- Dev-memory snapshot: stale={staleness.get('stale')} "
            f"(snapshot head `{staleness.get('snapshot_head')}`, HEAD "
            f"`{staleness.get('head')}`, root mismatch "
            f"{staleness.get('root_mismatch')}, allow_stale="
            f"{report.get('allow_stale')})")
    lines.append(f"- Deterministic fingerprint: "
                 f"`{report['deterministic_fingerprint']}`")
    lines.append(f"- Wall time: {report['total_elapsed_seconds']} s")
    if report.get("expected_files_outside_source_universe"):
        lines.append("- Warning: expected files outside the indexed source "
                     "universe: " + ", ".join(
                         f"`{p}`" for p in
                         report["expected_files_outside_source_universe"]))
    lines.extend(["", "## Aggregate metrics", ""])
    lines.append("| Budget | Arm | Tasks | Mean recall@budget | "
                 "Mean recall (content tier) | Mean precision | "
                 "Mean files | Mean content files | Mean tokens | Mean s | "
                 "Cache parsed | Cache reused |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregates"]:
        lines.append(
            f"| {row['budget_tokens']} | {row['arm']} | {row['tasks']} | "
            f"{row['mean_recall_at_budget']:.3f} | "
            f"{row.get('mean_recall_content_at_budget', 0.0):.3f} | "
            f"{row['mean_precision']:.3f} | "
            f"{row['mean_selected_files']:.1f} | "
            f"{row.get('mean_content_files', 0.0):.1f} | "
            f"{row['mean_estimated_tokens']:.0f} | "
            f"{row['mean_elapsed_seconds']:.2f} | "
            f"{row['cache_parsed']} | {row['cache_reused']} |")
    lines.extend(["", "## Recall by task", "",
                  "Each cell is `recall (recall_content)`.", ""])
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
                cells.append(
                    f"{run['recall']:.2f} ({run.get('recall_content', 0.0):.2f})"
                    if run else "-")
            lines.append(f"| {_cell(task['id'])} | " + " | ".join(cells) + " |")
        lines.append("")
    lines.extend(["## Task set", "",
                  "| Task | Style | Area | Expected files | Notes |",
                  "|---|---|---|---|---|"])
    for task in report["tasks"]:
        expected = "<br>".join(f"`{_cell(p)}`" for p in task["expected_files"])
        lines.append(f"| {_cell(task['id'])} | {_cell(task.get('style', ''))} | "
                     f"{_cell(task.get('area', ''))} | {expected} | "
                     f"{_cell(task.get('notes', ''))} |")
    lines.extend(["", "## Reading these numbers", "",
                  "- This is a **retrieval instrument**, not an end-to-end "
                  "coding benchmark: it measures whether known-relevant files "
                  "are selected, not whether an agent completes a change.",
                  "- `baseline` is a sorted-path file-listing control, not a "
                  "semantic retriever. `grep` is a lexical control: it counts "
                  "distinct task words found in each file's text.",
                  "- `recall` counts a hit at any tier. `recall_content` counts "
                  "only hits whose file the arm showed as code (code_search "
                  "snippet, dev_context item with snippet text, or repo-map "
                  "`full`/`outline` tier). A listing-tier hit tells the reader "
                  "the path exists, not what it contains.",
                  "- Token estimates are each module's own ~4-chars/token "
                  "heuristic. Cache counts apply only to repo-map arms.",
                  "- `both` is the literal union of the two retrievers run at "
                  "the same budget; its token cost and latency are the sum of "
                  "the components, so its budget is per component (up to 2x "
                  "the nominal budget). Compare it as a cost/recall trade-off, "
                  "not as an equal-token arm.",
                  "- `code_search` runs once per task; its elapsed time is the "
                  "same call's time at every budget.",
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
                        help="explicit task JSON (default: evaluation/repo_map/tasks.json; "
                             "v2 is evaluation/repo_map/tasks_v2.json)")
    parser.add_argument("--budgets", default=",".join(map(str, DEFAULT_BUDGETS)),
                        help="comma-separated token budgets (default: 500,900,1500)")
    parser.add_argument("--arms", default=",".join(ARMS),
                        help="comma-separated arms: " + ",".join(ARMS))
    parser.add_argument("--cache", default=None,
                        help="repo-map tag cache path (default: <root>/var/ocelot_repo_map_eval_tags.json)")
    parser.add_argument("--memory", default=None,
                        help="dev-memory snapshot path (default: <root>/var/ocelot_dev_graph.json)")
    parser.add_argument("--allow-stale", action="store_true",
                        help="evaluate dev_context/both even when the dev-memory "
                             "snapshot is stale (the report records it)")
    parser.add_argument("--limit", type=int, default=None,
                        help="evaluate only the first N tasks (deterministic)")
    parser.add_argument("--out-json", "--json-out", dest="json_out", default=None,
                        help="write the full JSON report to this path")
    parser.add_argument("--out-md", "--markdown-out", dest="markdown_out",
                        default=None,
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
            limit=args.limit, allow_stale=args.allow_stale)
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
