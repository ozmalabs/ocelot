# Symbol graph: callers, callees and impact

Status: W2-C of `DEV_TOOLING_V2_PLAN.md`. Dev tooling only. Nothing here edits
code or runs in the agent.

## Purpose

`ocelot_repo_map` ranks files. This module answers symbol questions: who calls
this function, what does it call, and what breaks transitively if it changes.
It reads the tag cache that the repo map already maintains, so it adds no
parser and no new dependency.

## Tag schema v2 (`scripts/ocelot_tag_languages.py`)

`TAGS_SCHEMA_VERSION = 2`. The bump changes the extractor fingerprint, so every
cached tag entry is re-extracted once.

| kind | keys |
|---|---|
| `def` | `name`, `kind`, `detail`, `line`, `end_line`, `qualname` |
| `ref` | `name`, `kind`, `detail`, `line`, `scope` |
| `import` (Python only) | `name`, `kind`, `detail`, `line`, `module`, `level`, `imported`, `scope` |

- `qualname`: dotted chain of enclosing definitions plus the name. A nested
  function inside `f` is `f.inner`. A method is `Class.method`.
- `scope`: `qualname` of the innermost enclosing definition of a reference,
  `""` at module level.
- `end_line`: last line of the definition.
- `import` tags exist only for Python. `import a.b` binds `a` (`imported` is
  `a.b`). `import a.b as c` binds `c`. `from .m import x as y` binds `y` with
  `level` 1 and `module` `m`. Star imports bind no name and are not tagged.
- Python decorators, default values, annotations, bases and keywords belong to
  the enclosing scope. Only the def body is a new scope.
- Tree-sitter languages nest by byte range: a def is inside another def when
  the other definition node's range contains it. Nesting is computed per file
  in O(n log n). Nesting depends on what the grammar's `tags.scm` captures. For
  Rust, `impl` blocks are not captured, so a method inside `impl` has no class
  in its qualname. A function inside `mod` nests under the module. Java
  classes and methods nest.

## Graph (`scripts/ocelot_symbol_graph.py`)

- Symbol id: `"<rel path>::<qualname>"`. Module-level code uses
  `"<rel path>::<module>"`.
- `build_symbol_graph(cache)` takes a tag-cache view and returns
  `{root_hash, nodes, edges, stats}`. The result is memoised in process by
  `root_hash` (last 4 graphs).
- Each edge is `{src, tgt, resolution, confidence, count}`. `count` is the
  number of references that produced the edge. Self edges are dropped.

### Resolution levels

Each reference is resolved at the first level that applies.

| level | rule | confidence |
|---|---|---|
| `local` | A definition with the same name exists in the same file. For `self.x()` inside `A.m`, the candidate `A.x` is preferred when `A` is a class. | `1 / number of candidates` (1.0 when unique or class-preferred) |
| `import` | The file has `from X import name` and `X` resolves to an indexed file. Edges go to that file's definition named `imported`. Relative imports resolve from the importing file's package. Module imports (`import a.b`) are skipped for bare names. | `1 / number of targets` |
| `name` | A global definition with this name exists, there are at most 5, the name is at least 3 characters, and it is not in `ocelot_repo_map._GENERIC_IDENTS` (for example `run`, `get`, `data`). | `1 / number of candidates` |

If a name is bound by a `from` import whose module is outside the index, the
reference is unresolved. The name-level fallback is skipped, so an external
`array()` does not link to a repo function called `array`.

A reference that matches no level is unresolved and counted in
`stats.unresolved`.

### Edge confidence and paths

For a path of several hops, the confidence is the product of the edge
confidences. `callers`, `callees` and `impact` keep the highest-confidence path
per symbol within the hop bound, and report that path's hop count as `depth`.

## API

```python
from scripts.ocelot_symbol_graph import (
    build_symbol_graph, resolve_symbol, callers, callees, symbol_impact, symbol_query)

result = symbol_query(root, "impact", "scripts/ocelot_repo_map.py::update_tag_cache",
                      depth=2, cache_path=None, min_confidence=0.0)
```

- `resolve_symbol(graph, query)`: `"path::qualname"` must be an exact id. A
  dotted query matches qualnames exactly. A bare name matches every definition
  with that name.
- `callers(graph, symbol, depth=1)`, `callees(graph, symbol, depth=1)`,
  `symbol_impact(graph, symbol, depth=3, min_confidence=0.0)`. Each result row
  is `{id, file, qualname, depth, resolution, confidence}`. `symbol_impact`
  adds `files`, grouped by file with `min_depth` and `symbols`.
- An ambiguous symbol returns `{"ok": False, "ambiguous": [ids]}`. An unknown
  symbol returns `{"ok": False, "error": "..."}`. Depth below 1 is an error.
- `symbol_query(root, op, symbol, *, depth, cache_path, min_confidence)` runs
  `update_tag_cache` for `root`, builds or reuses the graph, and runs `op`
  (`callers`, `callees`, `impact` or `resolve`). The default cache is
  `<root>/var/ocelot_dev_tags.json`. It returns `ok`, the op result, `stats`,
  `tag_cache` counts, and `timings` (`update_seconds`, `build_seconds`,
  `query_seconds`).

## CLI

```
python -m scripts.ocelot_symbol_graph {callers,callees,impact,resolve} SYMBOL \
    [--depth N] [--root R] [--cache C] [--min-confidence X]
```

Defaults: depth 1 for callers and callees, 3 for impact. Output is JSON. The
exit code is 0 on success and 1 otherwise.

## Limits

- Syntactic only. There is no type inference, so `obj.method()` resolves by
  name. Under the `name` level it links only when at most 5 global definitions
  share the name.
- Not followed: dynamic dispatch, `getattr`, re-exports through `__init__.py`
  star imports, `importlib` dynamic imports, and `sys.path` tricks.
- Duplicate qualnames in one file (for example a def inside `if`/`else`) keep
  the first definition. `stats.duplicate_defs` counts the rest.
- Python import tags are not used for Rust, Lua, Go, Java or C/C++ resolution.
  Those languages resolve through `local` and `name` only.
- LSP is the precise layer. W3-B wires optional LSP refinement; this module
  does not call a language server.

## Measured timings (real worktree tree, gate 3)

Run in one process from the worktree, with a cold cache at
`/tmp/ocelot_dt-w2c-symbol-graph/tags.json`. Details in
`/tmp/ocelot_dt-w2c-symbol-graph/logs/gate3_timings.json`.

Graph stats after the cold run: 6,804 files, 71,787 defs, 2,562,712 refs,
441,885 edges (186,966 local, 34,001 import, 352,578 name references resolved;
1,989,167 unresolved). Duplicate defs: 125.

| step | seconds |
|---|---|
| cold `update_tag_cache` (full parse) | 76.7 |
| first graph build | 6.2 |
| warm graph build (memo hit) | 0.0 |
| warm query, `callers update_tag_cache` | 0.0001 |
| warm query, `impact update_tag_cache` depth 2 | 0.0001 |
| warm query, `impact load_manifest_file` depth 2 | 0.0013 |
| warm `update_tag_cache` (stat scan, cache load) | 3.0 to 3.6 |

The warm update dominates. A standalone `json.loads` of the 267 MB cache takes
2.4 s, and `update_tag_cache` loads the whole file on each call. The graph
query itself is below 2 ms. The plan target (`symbol callers warm <= 0.3 s`) is
met only for the query and not for `symbol_query` end to end. Reducing the
cache load belongs to the repo-map cache work, not this module.
