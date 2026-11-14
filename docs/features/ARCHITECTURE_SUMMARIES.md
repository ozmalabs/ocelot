# Architecture summaries — Workstream E

**Status:** v0, landed 2026-11-14. Dev tooling, not agent runtime.

`scripts/ocelot_architecture.py` turns the repo map's file reference graph
into a compact, deterministic architecture report: hubs, cycles, coupling,
module boundaries, dead-code candidates and the test-to-source ratio. It is a
reading aid for orientation and `dev_brief`, not a correctness oracle.

The report is built entirely on
`scripts/ocelot_repo_map.py`:

- `update_tag_cache(root, cache_path=..., files=...)` supplies the
  content-hash incremental tags (Python AST; tree-sitter `tags.scm` for
  Rust/Lua);
- `build_reference_graph(cache)` supplies `defines`/`references` and the
  `referencer -> definer` file edges.

No new index is stored. A warm tag cache makes a report cheap; the first cold
index is dominated by tag extraction, exactly like the repo map.

## API

```python
from scripts.ocelot_architecture import architecture_report

report = architecture_report(
    root=".",
    cache_path=None,   # default: <root>/var/ocelot_dev_tags.json
    files=None,        # default: repo_map source roots; explicit list for a subset
    top=15,            # hubs / coupling / cycle members / markdown (1..200)
)

# {
#   "ok": True,
#   "summary": {...},     # structured metrics, JSON-safe
#   "markdown": "...",    # human report
#   "json": "...",        # pretty, key-sorted JSON of summary + newline
# }
```

`summary` has exactly these keys:

| Key | Shape | Meaning |
|---|---|---|
| `files` | int | indexed files (the graph's node universe) |
| `edges` | int | distinct **non-self** dependency edges |
| `languages` | `{name: count}` | histogram by suffix (`.py`→python, `.rs`→rust, …; unknown→`other`) |
| `hubs` | list | top files by PageRank with `rank`, `path`, `pagerank`, `in_degree`, `out_degree` |
| `cycles` | list | `{size, files, truncated}` for each Tarjan SCC of size > 1; `files` is capped to `top` members |
| `coupling` | object | `top` rows with `in_degree`, `out_degree`, `total_degree`; `files_with_inbound`, `files_with_outbound`, `max_in_degree`, `max_out_degree` |
| `modules` | object | `by_module` counts; `cross_edges` `{src, tgt, edges}`; `cross_edge_count`; `intra_module_edge_count` |
| `dead_code_candidates` | list[str] | sorted files with zero inbound non-self edges, minus tests/scripts/entrypoints |
| `test_source_ratio` | object | `{tests, source, ratio}`; `ratio` is `null` when there are no source files |

`json` is `json.dumps(summary, indent=2, sort_keys=True) + "\n"`, so
`json.loads(report["json"]) == report["summary"]`.

## Algorithms

### Graph normalization

The repo map emits weighted `src -> tgt` edges plus weak self-edges for
definitions nobody references. The report:

1. drops self-edges (a file referencing its own symbol is not a cross-file
   dependency and would inflate both in-degree and PageRank);
2. drops endpoints outside the indexed file set;
3. sums duplicate `(src, tgt)` pairs (several symbol names can create the
   same file pair);
4. sorts the final `(src, tgt, weight)` list.

Node universe = every file in the tag cache, including files with no edges, so
isolated files still appear in coupling and dead-code analysis.

### Hubs — deterministic weighted PageRank

The report computes its own uniform-restart PageRank rather than reusing the
task-personalized rank from `repo_map.personalized_pagerank`, because a global
architecture summary must not be biased toward a task, focus files or test
down-weighting.

For node `v`:

```text
PR(v) = (1-d)/N + d*D/N + d * Σ_{u->v} w(u,v) / W_out(u)
```

- `d = 0.85`, `N =` indexed files, `D =` total rank on dangling nodes
  (nodes with no outgoing non-self edge), redistributed uniformly;
- at most 50 iterations, stop when the L1 change is below `1e-12`;
- ranks are normalized to sum to 1 and rounded to 8 decimals in the report.

Ordering: PageRank descending, then in-degree descending, then path. This is
deterministic and keeps hubs stable when two files have near-equal rank.
`pagerank` is centrality in the reference graph, not a quality, ownership or
risk score.

### Cycles — iterative Tarjan SCCs

`_tarjan_sccs` is an **iterative** Tarjan implementation (no recursion limit on
large repos) over the non-self file edges. Only strongly connected components
with more than one file are reported: a self-referencing symbol is not a
file-level cycle. Components are sorted internally, then by size descending,
then lexicographically.

A cycle means "these files reference each other's names", not "these modules
are inseparable by design". Name collisions can create a false cycle, and
runtime-only cycles are invisible. A syntactic collision can also merge
thousands of files into one SCC; each component's `files` list is therefore
capped to `top` members and marked `truncated` when members were omitted
(`size` remains the true component size). The markdown renderer shows the same
bounded sample.

### Coupling

Per-file `in_degree` / `out_degree` count distinct dependency edges (not
reference occurrences). `coupling.top` reports the `top` most coupled files
ordered by total degree, then in-degree, then path, with each file's in/out
degree. `files_with_inbound` / `files_with_outbound`, `max_in_degree` and
`max_out_degree` summarize the rest without inflating the report. This is a
summary, not a full per-file table; use the repo-map graph for that.

### Modules

A module is the first path component; files at the repository root use
`(root)`. `by_module` counts files per module. `cross_edges` aggregates
dependency edges whose endpoints are in different modules; `edges` is the
number of distinct file pairs, not their weights. Intra-module edges are
counted separately. This is a coarse *directory* boundary, not a language
package graph.

### Dead-code candidates — explicitly a heuristic

A candidate is an indexed file with **zero inbound non-self edges** after
excluding:

- tests: any `tests/` path component, `test_*.py`, `*_test.py`,
  `conftest.py`;
- dev scripts/command surfaces: `scripts/`, `tools/`, `bin/`,
  `runners/dsl/src/bin/`;
- conventional entrypoints (`main.py`, `__main__.py`, `main.rs`, `app.py`,
  `manage.py`, `setup.py`, …);
- package markers: `__init__.py`, `__init__.rs`, `__init__.lua`.

False positives are expected: dynamically imported modules, plugin registries,
public APIs, CLI verbs discovered by convention, and framework entrypoints may
have no syntactic inbound edge. False negatives are also possible: any single
name reference from anywhere keeps a file off the list. The report labels this
section **heuristic**; it is not a deletion recommendation.

### Test-to-source ratio

Test files use the same path/name test heuristic as above; source is every
other indexed file. The ratio is `tests / source`, rounded to 4 decimals. It
counts files, not coverage, assertions or runtime.

## Determinism

- All node/edge/module lists are sorted before computation and output.
- PageRank iterates in sorted order; ranks are rounded.
- Top-k lists and capped cycle member lists are cut from sorted sequences, so
  `top` changes the report size, never the ordering.
- No timestamp, cache statistics, absolute root path or random ordering enters
  `summary`, `markdown` or `json`.
- The cache's `updated_at` is internal to `update_tag_cache` and is not
  reported.
- Two calls on unchanged files return byte-identical `markdown` and `json`.

The report itself is read-only. `update_tag_cache` may write the cache file,
as it does for the repo map; pass a dedicated `cache_path` when analyzing a
subset, because the cache prunes entries outside the scanned `files` list.

## Integration notes (central integrator)

The shared MCP/CLI files are intentionally not edited here.

**MCP** — add `dev_architecture` alongside `dev_repo_map` / `dev_impact`:

```python
from scripts.ocelot_architecture import architecture_report

def dev_architecture(top: int = 15) -> dict:
    report = architecture_report(ROOT, cache_path=DEFAULT_CACHE, top=top)
    return {"ok": report["ok"], "markdown": report["markdown"],
            "summary": report["summary"]}
```

Return `markdown` for a compact orientation answer and `summary` when the
agent needs structured fields (for example `summary["cycles"]`,
`summary["modules"]["cross_edges"]`, or `summary["hubs"]`). Add a one-line
tool description that says **file-level, syntactic, dead-code is a
heuristic**. `summary` still grows with the number of cycles and dead-code
candidates (cycle *members* are capped); if a client has a tight token
budget, return `markdown` by default and `summary` only on request.

**CLI** — a verb mirroring the module:

```bash
.venv/bin/python -m scripts.ocelot_dev_memory architecture --top 15
.venv/bin/python -m scripts.ocelot_dev_memory architecture --json
```

**`dev_brief`** — after the existing repo brief, add a compact architecture
section using `summary` rather than the whole markdown:

```text
Architecture: 4 files, 4 edges
Hubs: a.py (in 3), b.py (in 1)
Cycles: a.py, b.py
Modules: (root) 3, tests 1; cross-module edges: 1
Dead-code candidates (heuristic): c.py
Tests/source: 1/3 = 0.3333
```

The report is cheap on a warm tag cache, so `dev_brief` can call it with
`top=5` without a second index build. Do not persist the report; regenerate
it so it tracks the checkout.

## Files

- `scripts/ocelot_architecture.py` — report API, PageRank, iterative Tarjan,
  module/coupling/dead-code/ratio metrics, markdown renderer.
- `tests/test_architecture_migrated.py` — synthetic-repo tests.
- `docs/features/ARCHITECTURE_SUMMARIES.md` — this document.

## Tests

```bash
.venv/bin/python -m pytest tests/test_architecture_migrated.py -q
# 14 passed in 0.20s
```

Covered: summary shape and JSON round-trip; a<->b cycle detection; hub
ordering by PageRank then in-degree; top coupling degrees and aggregate counts;
module counts and cross-module edges; the `c.py` dead-code candidate;
test/source ratio; script/entrypoint/test exclusions; all markdown sections;
`top` capping including bounded cycle members; byte-level determinism without
absolute paths; a 3-file cycle plus a 2-file cycle sorted
by size; a no-cycle graph; and the empty-repository case.

## Honest limits

- **Syntactic, not semantic.** Python tags are AST name/attribute loads, not
  scope-resolved; Rust/Lua tags come from grammar queries. Same-named symbols
  across files can create false edges, and aliases/dynamic dispatch can hide
  real ones.
- **File-level.** There is no symbol-level call graph, no type resolution and
  no ownership information. Symbol-level impact remains the LSP/SCIP layer.
- **Imports are not dependency edges by themselves.** An edge requires a
  reference tag to a name defined elsewhere. `from x import y` with no use of
  `y` contributes nothing.
- **External libraries are out of scope.** The graph only contains files under
  the repo map's source roots; vendored/generated trees and site-packages are
  not represented.
- **Cycle edges are name-based.** A cycle can be a false positive from a
  collision, or a false negative when a cycle exists only at runtime.
- **Dead-code is a hint.** Dynamic loading, plugin registries, public APIs and
  convention-based entrypoints are invisible; never delete from this list
  without checking callers and runtime wiring.
- **PageRank is centrality, not importance.** It ranks participation in the
  reference graph, not business criticality or failure risk.
- **The test ratio is file counting.** It says nothing about coverage,
  assertion quality or flakiness.
- **Not evaluated yet.** There is no benchmark showing the summary improves an
  agent's decisions; it is an orientation instrument.

## Source

- `scripts/ocelot_repo_map.py` — tag cache, reference graph, PageRank, repo
  map and impact.
- `scripts/ocelot_dev_memory.py` — snapshot/brief integration point.
- `docs/features/DEV_MEMORY_MCP.md` — MCP/CLI surface conventions.
- `docs/features/GRAPH_CODING_LANDSCAPE.md` — P3 architecture-summaries gap
  (ckg, Codebase-Memory, arbor).
