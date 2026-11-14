"""ocelot_index_bench — timing bench for the warm repo index (DEV TOOLING).

Measures, in one process, the cost of the repo-map tag cache, repo_map,
code_search and impact. The first call of each query may build a memo; the
second call shows the warm cost that the plan targets refer to.

    .venv/bin/python -m scripts.ocelot_index_bench --root . --cold --workers 4
    .venv/bin/python -m scripts.ocelot_index_bench --root .

Output is one JSON object on stdout. ``--cold`` deletes the tag cache first,
so the update step is a full cold index. Without it, the update reuses the
cache left by an earlier process. The bench writes only to ``--cache``
(default ``/tmp/ocelot_index_bench/tags.json``), never under a repo's
``var/``. ``--check`` exits 1 when a target is missed. The plan does not use
it as a gate: a missed target is a reported result.

Stdlib only. Not agent runtime.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

from scripts import ocelot_code_search as search_module
from scripts.ocelot_code_search import code_search, search_side_cache_path
from scripts.ocelot_repo_map import ROOT, impact, repo_map, update_tag_cache

DEFAULT_CACHE = Path("/tmp/ocelot_index_bench/tags.json")
REPO_MAP_TASKS = (
    "personalized pagerank repo map",
    "seed loader dependency closure",
    "lossless python cst edit",
)
SEARCH_QUERIES = (
    "tag cache fingerprint",
    "frozen core boot",
    "replace_body one-line def",
)
IMPACT_FILES = (
    "scripts/ocelot_repo_map.py",
    "substrate/seed_loader.py",
)
REPO_MAP_BUDGET = 1500
TARGETS = {
    "repo_map_warm_s": 1.0,
    "code_search_warm_s": 0.5,
    "impact_warm_s": 0.3,
    "cold_index_s": 30.0,
    "code_search_new_process_s": 10.0,
    "code_search_cold_first_s": 40.0,
}

# Runs one code_search in a fresh interpreter. Arguments: code dir, search
# root, tag cache, query. Prints one JSON line.
_CHILD = """
import json, sys, time
sys.path.insert(0, sys.argv[1])
from scripts import ocelot_code_search as m
root, cache, query = sys.argv[2], sys.argv[3], sys.argv[4]
start = time.perf_counter()
result = m.code_search(root, query, cache_path=cache)
seconds = time.perf_counter() - start
print(json.dumps({"seconds": round(seconds, 3), "n": result["n"],
                  "build": dict(m.LAST_BUILD)}, sort_keys=True))
"""


def _new_process_search(cache: Path, root: Path) -> dict[str, Any]:
    """First code_search in a new interpreter, with the side cache present."""
    side = search_side_cache_path(cache)
    before = side.stat().st_size if side.exists() else None
    code_dir = str(Path(__file__).resolve().parents[1])
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD, code_dir, str(root), str(cache),
         SEARCH_QUERIES[0]],
        capture_output=True, text=True, cwd=code_dir)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()[-500:], "side_bytes_before": before}
    row = json.loads(proc.stdout.strip().splitlines()[-1])
    row["side_bytes_before"] = before
    row["side_bytes_after"] = side.stat().st_size if side.exists() else None
    return row


def _timed(fn: Callable[[], Any]) -> tuple[float, Any]:
    start = time.perf_counter()
    value = fn()
    return round(time.perf_counter() - start, 3), value


def _twice(fn: Callable[[], Any], summarise: Callable[[Any], dict[str, Any]]
           ) -> dict[str, Any]:
    first_s, first = _timed(fn)
    second_s, second = _timed(fn)
    row = {"first_s": first_s, "second_s": second_s}
    row.update(summarise(second))
    row["first_call_ok"] = bool(first.get("ok", True))
    return row


def _median(rows: dict[str, dict[str, Any]]) -> float | None:
    values = [row["second_s"] for row in rows.values()]
    return round(statistics.median(values), 3) if values else None


def _target(value: float | None, limit: float) -> dict[str, Any]:
    met = None if value is None else value <= limit
    return {"median_second_s": value, "target_s": limit, "met": met}


def run(root: Path, cache: Path, cold: bool) -> dict[str, Any]:
    if cold and cache.exists():
        cache.unlink()
    side = search_side_cache_path(cache)
    if cold and side.exists():
        side.unlink()
    update_s, (_view, update_stats) = _timed(
        lambda: update_tag_cache(root, cache_path=cache))
    update = {
        "seconds": update_s,
        "files": update_stats["files"],
        "parsed": update_stats["parsed"],
        "reused": update_stats["reused"],
        "failed": update_stats["failed"],
        "cached_files": update_stats["cached_files"],
        "parallel": update_stats["parallel"],
    }

    repo_rows: dict[str, dict[str, Any]] = {}
    for task in REPO_MAP_TASKS:
        repo_rows[task] = _twice(
            lambda task=task: repo_map(root, task=task,
                                       budget_tokens=REPO_MAP_BUDGET,
                                       cache_path=cache),
            lambda r: {"files": len(r["files"]),
                       "estimated_tokens": r["estimated_tokens"]})

    search_rows: dict[str, dict[str, Any]] = {}
    for query in SEARCH_QUERIES:
        search_rows[query] = _twice(
            lambda query=query: code_search(root, query, cache_path=cache),
            lambda r: {"results": r["n"]})
    search_build = dict(search_module.LAST_BUILD)
    first_search_s = search_rows[SEARCH_QUERIES[0]]["first_s"]

    impact_rows: dict[str, dict[str, Any]] = {}
    for rel in IMPACT_FILES:
        impact_rows[rel] = _twice(
            lambda rel=rel: impact(root, file=rel, cache_path=cache),
            lambda r: {"ok": r["ok"], "impacted": r.get("n")})

    new_process = _new_process_search(cache, root)
    side_bytes = side.stat().st_size if side.exists() else None

    repo_second = _median(repo_rows)
    search_second = _median(search_rows)
    impact_second = _median(impact_rows)
    cold_value = update_s if cold else None
    targets = {
        "repo_map": _target(repo_second, TARGETS["repo_map_warm_s"]),
        "code_search": _target(search_second, TARGETS["code_search_warm_s"]),
        "impact": _target(impact_second, TARGETS["impact_warm_s"]),
        "cold_index": {"seconds": cold_value,
                       "target_s": TARGETS["cold_index_s"],
                       "met": None if cold_value is None
                       else cold_value <= TARGETS["cold_index_s"]},
        "code_search_new_process": {
            "seconds": new_process.get("seconds"),
            "target_s": TARGETS["code_search_new_process_s"],
            "met": None if new_process.get("seconds") is None
            else new_process["seconds"] <= TARGETS["code_search_new_process_s"]},
        "code_search_cold_first": {
            "seconds": first_search_s if cold else None,
            "target_s": TARGETS["code_search_cold_first_s"],
            "met": None if not cold
            else first_search_s <= TARGETS["code_search_cold_first_s"]},
    }
    return {
        "root": str(root),
        "cache": str(cache),
        "side_cache": str(side),
        "side_cache_bytes": side_bytes,
        "mode": "cold" if cold else "warm",
        "workers_env": os.environ.get("OCELOT_INDEX_WORKERS"),
        "cpu_count": os.cpu_count(),
        "update": update,
        "repo_map": repo_rows,
        "code_search": search_rows,
        "code_search_build": search_build,
        "first_search_new_process_warm_side_cache": new_process,
        "impact": impact_rows,
        "targets": targets,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", default=str(ROOT),
                        help="repository root to index (default: this repo)")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE),
                        help="tag cache path; the bench writes only here")
    parser.add_argument("--cold", action="store_true",
                        help="delete the tag cache before the first update")
    parser.add_argument("--workers", type=int, default=None,
                        help="sets OCELOT_INDEX_WORKERS for this process")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 when any target is missed")
    args = parser.parse_args(argv)
    if args.workers is not None:
        os.environ["OCELOT_INDEX_WORKERS"] = str(args.workers)
    cache = Path(args.cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    report = run(Path(args.root).resolve(), cache, args.cold)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check:
        missed = [name for name, entry in report["targets"].items()
                  if entry.get("met") is False]
        if missed:
            print(f"targets missed: {', '.join(missed)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
