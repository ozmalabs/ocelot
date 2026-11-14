# SCIP import — compiler-accurate symbols and references for the dev graph

**Status:** Workstream C v0 (2026-11-14). The JSON path is implemented and
tested; the optional `.scip` protobuf path is implemented behind an import
guard and is **not exercised** in this checkout because `protobuf`/`scip_pb2`
are not installed. It refuses honestly rather than guessing at the wire
format. The central integrator wires the module into the MCP/CLI surface; this
workstream does not edit shared files.

**Not agent runtime.** This is dev tooling. It reads a SCIP index and returns
plain JSON-safe dictionaries. It never edits source, never starts an agent,
and never prints.

## Why SCIP

The repo map is syntactic: tree-sitter tags produce file-level edges and can
confuse same-named symbols. SCIP is compiler/indexer output: a symbol string
is globally unique, and each occurrence says whether it is a definition or a
reference. Importing it gives the dev graph:

- precise symbol identities (not just names);
- cross-file definition → reference resolution;
- a fallback that does not require running a language server per query;
- compatible file edges for the existing repo-map PageRank.

## Supported input: SCIP JSON export

The primary path is the JSON emitted by the Sourcegraph SCIP CLI:

```bash
scip print --json index.scip > index.scip.json
```

`scip print --json` serializes the SCIP `Index` protobuf in protobuf-JSON
form. The loader accepts the standard lowerCamelCase spelling and the more
readable snake_case spelling used by several exporters:

```json
{
  "metadata": {
    "version": 0,
    "project_root": "file:///repo",
    "tool_info": {"name": "scip-python", "version": "0.1.0"}
  },
  "documents": [
    {
      "relative_path": "./src/app.py",
      "language": "python",
      "occurrences": [
        {
          "symbol": "scip-python python demo 0.1.0 `src/app.py`/alpha().",
          "symbol_roles": 1,
          "range": [4, 6, 4, 11]
        }
      ],
      "symbols": [
        {
          "symbol": "scip-python python demo 0.1.0 `src/app.py`/alpha().",
          "display_name": "alpha",
          "kind": "Function",
          "documentation": ["Does alpha."]
        }
      ]
    },
    {
      "relativePath": "src\\use.py",
      "occurrences": [
        {
          "symbol": "scip-python python demo 0.1.0 `src/app.py`/alpha().",
          "symbolRoles": "ReadAccess",
          "range": [2, 15, 2, 20]
        },
        {
          "symbol": "scip-python python demo 0.1.0 `src/app.py`/alpha().",
          "symbolRoles": ["ReadAccess"],
          "range": {
            "start": {"line": 5, "character": 12},
            "end": {"line": 5, "character": 17}
          }
        },
        {
          "symbol": "local 1",
          "symbol_roles": 8,
          "startLine": 8, "startCharacter": 4,
          "endLine": 8, "endCharacter": 9
        }
      ]
    }
  ],
  "external_symbols": [
    {
      "symbol": "scip-python python lib 1.0.0 `lib/remote.py`/remote().",
      "displayName": "remote_fn",
      "kind": 11
    }
  ]
}
```

### Accepted top-level shapes

- `{"documents": [...]}` (the standard export);
- `{"docs": [...]}` (alias);
- a bare array of document objects;
- a single document object;
- `{"index": <any of the above>}` (some wrappers add an `index` field);
- `documents` as an object keyed by document path, in addition to an array.

`metadata` is preserved as-is in the normalized index; it is not validated.
`external_symbols` / `externalSymbols` are used only to improve display names.

### Accepted document fields

| Meaning | Accepted spellings |
|---|---|
| repository-relative path | `relative_path`, `relativePath`, `path`, `file`, `filename`, `file_path`, `filePath`, `uri` |
| language label | `language` |
| occurrences | `occurrences` (array, or object of occurrence objects) |
| symbol metadata | `symbols`, `symbol_information`, `symbolInformation` (array or object keyed by symbol) |

### Accepted occurrence fields

| Meaning | Accepted spellings |
|---|---|
| symbol string | `symbol`, `symbol_string`, `symbolString` |
| role bit mask | `symbol_roles`, `symbolRoles`, `roles`, `role` |
| source range | `range`, or flat start/end fields (below) |

Role values may be:

- an integer bit mask (`1` = definition, `8` = read access, …);
- a numeric string (`"8"`);
- an enum name (`"Definition"`, `"ReadAccess"`, `"ForwardDefinition"`);
- a delimited string (`"Definition|ReadAccess"`, comma/space/semicolon/+);
- an array of names or integers.

Names are case-insensitive and tolerate a `SymbolRole_` / `SYMBOL_ROLE_`
prefix. Unknown role names or malformed ranges raise `ScipFormatError`; they
are not silently discarded.

### Accepted range spellings

1. Standard 4-integer SCIP range: `[start_line, start_char, end_line,
   end_char]`.
2. SCIP compact 3-integer single-line range: `[line, start_char, end_char]`.
3. Nested object:
   `{"start": {"line": 5, "character": 12}, "end": {"line": 5,
   "character": 17}}` (`char`/`column` are accepted).
4. Flat fields on the occurrence:
   `start_line`/`startLine`, `start_character`/`startCharacter`,
   `end_line`/`endLine`, `end_character`/`endCharacter`
   (`start_char`, `start_column`, `end_char`, `end_column` are accepted).

Ranges are **0-based** exactly as SCIP defines them. The normalizer keeps the
4-integer form and rejects negative values or an end before the start.
`position_encoding` is not converted; character offsets are preserved as
numbers (see limitations).

### Symbol strings

The parser implements the `scip.proto` symbol grammar:

```text
<scheme> ' ' <manager> ' ' <package-name> ' ' <version> <descriptors>...
# or
local <local-id>
```

Descriptor suffixes are understood: namespace `/`, type `#`, term `.`,
method `().`, type parameter `[T]`, parameter `(x)`, macro `!`, meta `:`.
Backtick-escaped identifiers are unescaped (`` `` `` becomes a literal
backtick). The normalized record uses:

- `name`: the last descriptor's readable name, or `display_name` when the
  index provides one;
- `qualname`: descriptor names joined with `.`;
- `local`: true for `local <id>` symbols.

Name parsing is best-effort for nonstandard/malformed symbol strings;
`display_name` always wins.

## Normalization rules

- **Paths** become repo-relative POSIX paths: `\` → `/`, `./` and duplicate
  slashes collapsed, `..` escapes rejected. Absolute paths are accepted only
  when a `root` argument or the index's `project_root` metadata contains them.
  Documents are sorted by `(path, language)`.
- **Role filtering.** `symbol_roles & Definition` → a definition record;
  everything else with a symbol → a reference record. Import, read-access and
  write-access roles mark references. Generated/test/forward-definition are
  modifiers retained in `roles`, not filters. If one occurrence carries both
  the definition bit and a read/write bit, it is listed as a definition and
  its `roles` list preserves the full mask.
- **Dedup.** Occurrences are merged by `(path, symbol, range, kind)`; the
  role masks are OR-ed and the roles recomputed. An exact duplicate
  occurrence appears once. Two different ranges remain two records. This also
  merges duplicate documents for the same path.
- **Empty symbols are dropped.** SCIP permits occurrences without a symbol
  for syntax-only data; they carry no reference information.
- **Local symbols are kept as records** but never become cross-file edges.
- **External symbols** are not definitions in this repo; they enrich display
  names only and produce no repo-map edges.

## Public API

Import from `scripts.ocelot_scip_import`. All functions are deterministic and
do not print.

### `load_scip_json(path, *, root=None) -> dict`

Read a JSON file (or an already-parsed mapping/list) and return the normalized
index:

```python
{
    "format": "scip-json",
    "metadata": {...},                    # as supplied
    "documents": [
        {
            "path": "src/app.py",
            "language": "python",
            "position_encoding": "UTF8CodeUnitOffsetFromLineStart",
            "occurrences": [
                {"symbol": "...", "role_mask": 1,
                 "roles": ["definition"], "range": [4, 6, 4, 11]}
            ],
            "symbols": [
                {"symbol": "...", "display_name": "alpha",
                 "kind": "Function", "documentation": ["..."],
                 "enclosing_symbol": ""}
            ],
        }
    ],
    "external_symbols": [...],
}
```

`load_scip_json` preserves occurrence multiplicity; `scip_records` performs
the dedup. It raises `ScipFormatError` for unreadable JSON or invalid schema.

### `scip_records(document, *, root=None) -> {"definitions": [...], "references": [...]}`

The normalized per-document (or whole-index) records. A whole normalized
index, a raw index, a document, a document array, or records already produced
by this function are accepted.

Each record:

```python
{
    "path": "src/use.py",             # repo-relative POSIX
    "symbol": "scip-python ...",      # full SCIP symbol
    "name": "alpha",                  # display_name or parsed last descriptor
    "qualname": "src/app.py.alpha",  # parsed descriptor path
    "kind": "reference",              # "definition" | "reference"
    "symbol_kind": "Function",        # from SymbolInformation, may be ""
    "roles": ["read_access"],         # canonical lower-case names
    "role_mask": 8,
    "range": [2, 15, 2, 20],          # 0-based, SCIP order
    "line": 3,                        # 1-based start line for repo maps
    "character": 15,
    "end_line": 3,                    # 1-based
    "end_character": 20,
    "local": False,
}
```

### `scip_to_repo_map_edges(records, *, root=None) -> list[dict]`

Repo-map-compatible edges:

```python
[{"src": "src/use.py", "tgt": "src/app.py", "weight": 2.0}]
```

`src` references a symbol defined in `tgt`. Only cross-file, non-local
references to defined symbols produce edges. `weight` is the number of
distinct reference occurrences (duplicates already removed). External and
undefined symbols produce no edge. Isolated definitions get no self-edge;
the integrator may add one if PageRank needs it.

### `scip_to_graph_records(records, *, root=None) -> dict`

A stable payload suitable for a CLI response, graph ingestion, or a file:

```python
{
    "ok": True,
    "format": "scip-graph-records",
    "version": 1,
    "documents": 2,
    "definitions": [...],
    "references": [...],
    "edges": [...],
    "files": [...],
    "totals": {
        "files": 2,
        "definitions": 1,
        "references": 4,
        "local_definitions": 0,
        "local_references": 1,
        "symbols": 2,            # unique non-local symbols, defs + refs
        "defined_symbols": 1,
        "edges": 1,
    },
}
```

`scip_graph_records` is an alias.

### `scip_file_summary(records, *, root=None) -> dict`

Same file rows and totals without the records (`scip_summary` is an alias):

```python
{
    "ok": True,
    "format": "scip-file-summary",
    "version": 1,
    "documents": 2,
    "files": [
        {
            "path": "src/app.py",
            "language": "python",
            "definitions": 1,
            "references": 0,
            "local_definitions": 0,
            "local_references": 0,
            "unique_symbols": 1,
            "incoming_edges": 1,
            "outgoing_edges": 0,
        }
    ],
    "totals": {...},             # same keys as scip_to_graph_records
}
```

### `scip_import(path, *, root=None) -> dict`

One-shot load + graph payload for a CLI/MCP handler. It adds:

```python
{"source": "/path/to/index.scip.json", "input_format": "scip-json"}
```

### `scip_dumps(payload, *, indent=2) -> str`

Deterministic JSON (`sort_keys=True`, UTF-8 preserved). The same input yields
byte-identical output, so snapshots/tests can diff it.

### Helpers

- `normalize_path(path, *, root=None)` — path normalization alone.
- `parse_scip_symbol(symbol)` / `scip_symbol_name(symbol)` — symbol grammar.
- `role_mask_names(mask)` — role names for a bit mask.
- `scip_protobuf_status()` — `{"available", "module", "error"}`.

### Errors

All errors derive from `ScipImportError`:

- `ScipFormatError` (also a `ValueError`) — bad JSON/schema/range/role.
- `ScipProtobufUnavailableError` (also a `RuntimeError`) — protobuf path
  requested without the optional bindings. Aliases:
  `ScipProtobufUnavailable`, `SCIPProtobufUnavailable`.

## Optional `.scip` protobuf path

`load_scip(path)` dispatches `.json` files to the JSON loader and
`.scip`/`.scip.gz`/`.pb`/`.bin` files to `load_scip_protobuf`. Unknown
suffixes sniff for a leading `{`/`[` and otherwise take the protobuf path.

`load_scip_protobuf` imports `scip_pb2` (then `scip.scip_pb2`). If neither is
importable it raises:

```text
SCIP protobuf ingestion is unavailable: protobuf/scip_pb2 is not installed.
Install the Sourcegraph SCIP protobuf bindings (protobuf + scip_pb2) and
retry, or export JSON with `scip print --json <index.scip>` and use
load_scip_json().
```

It does **not** contain a hand-written protobuf decoder.

### Enabling real `.scip` later

No source change is needed once the optional dependency exists:

1. Install the protobuf runtime (`protobuf`) in the dev environment. The
   central integrator owns `requirements-dev.txt`; this workstream does not
   edit it.
2. Make the generated SCIP Python bindings importable as `scip_pb2` (generate
   from Sourcegraph's `scip.proto` with `protoc --python_out=...`, or install a
   package that ships the bindings).
3. Check `scip_protobuf_status()["available"] is True`.
4. Call `load_scip("index.scip")` or `scip_import("index.scip")`.

The conversion reads `Index.documents[].occurrences[]` (`symbol`,
`symbol_roles`, `range`), `Document.symbols[]`, `Index.external_symbols`,
and basic `Metadata`/`ToolInfo`, then feeds the same normalizer as JSON.
Gzip-compressed `.scip` payloads are accepted. The protobuf path remains
unguaranteed until it has a live test with the real bindings.

## Integration notes (central integrator)

- **MCP:** add `dev_scip` with input `{path, root?, summary_only?}`. Call
  `scip_import(path, root=root)` for the full payload, or
  `scip_file_summary(load_scip_json(path))` for the compact report. Return it
  as JSON; no printing in this module.
- **CLI:** add a `scip` verb to the shared dev-memory CLI that calls
  `scip_import` and prints `scip_dumps(payload)`. Keep the verb out of this
  module so the central integrator owns argument parsing.
- **Repo map:** append `payload["edges"]` to `build_reference_graph` output, or
  feed them to the existing PageRank code. SCIP weights are occurrence counts,
  the same unit as the tree-sitter graph, so no rescaling is required. Add a
  self-edge only if the integrator wants isolated files ranked.
- **Graph memory:** create one `Symbol` node per non-local definition with
  attributes `name`, `qualname`, `kind`, `file`, `start_line`, `end_line`,
  `scip_symbol`; link `File -defines-> Symbol`. Keep references as records
  until a target symbol is resolved; then add a `references` edge. External
  symbols can later become library nodes; today they are name metadata only.
- **Filtering:** callers can drop records whose `roles` contain `generated` or
  `test`, or whose `local` is true. The importer does not hide them.
- **Snapshot/cache:** SCIP indexes are generated externally and are not part of
  the repo-map tag cache. The integrator decides where to persist the index or
  payload (`var/` is the natural place); this module has no cache and no I/O
  beyond reading the input file.

## Limitations

- No protobuf dependency is installed here. The `.scip` code path is guarded
  and tested only for honest refusal; real protobuf parsing is not yet
  verified.
- JSON export must be produced by `scip print --json` or an equivalent
  indexer/exporter. This module does not run an indexer.
- `position_encoding` (UTF-8/UTF-16/UTF-32 character offsets) is preserved on
  the normalized document but not converted into records. `line` values are
  safe; consumers that slice source by `character` must account for the
  document encoding.
- Name parsing is heuristic for nonstandard symbol strings; `display_name`
  from `SymbolInformation` is preferred when present. The qualname is a
  best-effort join of descriptor names.
- External symbols only improve names. There is no cross-repo or
  package-version resolution; references to libraries produce no edge.
- Local symbols are records but produce no edges.
- Single-occurrence role precedence: an occurrence with both definition and
  read/write bits is classified as a definition, with the full role list
  preserved. Two separate occurrences at the same range would produce both a
  definition and a reference record.
- Dedup is exact identity `(path, symbol, range, kind)`. Overlapping or
  adjacent ranges are not merged, and same-named symbols stay distinct
  because the full SCIP symbol is the key.
- `SymbolInformation.relationships`, syntax kinds, override documentation,
  signatures, and implementation/inheritance data are ignored.
- No self-edges for isolated definitions, no incremental cache, and no
  language-specific symbol rewriting. The repo-map integrator owns those
  policies.
- Metadata is passed through without validation; a malformed `project_root`
  can only affect absolute-path normalization.

## Tests

```bash
.venv/bin/python -m pytest tests/test_scip_import_migrated.py -q
```

The fixture has two documents, one definition, duplicate and distinct
references, local and external symbols, three range spellings, two role
spellings, and path variants. It asserts records/dedup/role filtering, paths,
edges, file totals, deterministic JSON, the one-shot CLI payload, and the
honest protobuf refusal. Last run in this checkout: **8 passed**.
