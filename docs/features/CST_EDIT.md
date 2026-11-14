# CST edit — graph-addressed Rust/Lua edits

**Status:** Workstream A v0 (2026-11-14). The adapter exists and is tested; it
is not yet wired into the shared dispatcher. This note is the contract the
central integration in `docs/features/GRAPH_EDIT_AND_SESSION_PLAN.md` binds to.

**Not agent runtime.** This is dev tooling. It consumes the substrate's
`CstNode` graph (parsed by `ts_ingest` when tree-sitter is available), applies
an op list against graph addresses, and writes the result as a transaction. It
does not boot the agent, mutate the live substrate, or decide what to edit.

## Why a CST and not a text patch

A unified diff is a lossy rendering. The canonical change is an **op list
against graph targets**; the diff is emitted only so a human can review it.
Raw `diff`/`patch` input is refused outright.

The byte owner is the concrete syntax tree, not the semantic AST:

- `domains/ts_ingest.py` already parses Rust/Lua with tree-sitter and ingests
  every CST node as a `CstNode` under `child` edges.
- Leaves carry exact `text`; interior nodes do not.
- `child_index` orders siblings; every anonymous token (braces, operators,
  semicolons) keeps its place.
- Rendering the leaves in document order reproduces the source byte-for-byte,
  including comments, blank lines, indentation, trailing spaces and line
  endings.

`scripts/ocelot_cst_edit.py` consumes that graph. It is the same `CstNode`
contract `TableWalker.flat_text` in `ts_ingest` uses, not a second parser.

## Public API

```python
from scripts.ocelot_cst_edit import (
    CstEditError,          # subclass of scripts.ocelot_code_edit.CodeEditError
    CstGraph,              # read-only view over CstNode attrs + child edges
    apply_cst_edit_script, # the transaction entry point
    cst_backend_status,    # honest tree-sitter availability report
    cst_graph_from_nested, # test/offline helper: nested text tree -> CstGraph
    parse_cst_path,        # "child[2].child[0]" -> [2, 0]
    tree_sitter_available, # bool for the real parse/ingest path
)
```

```python
result = apply_cst_edit_script(root, script, write=False)
```

`write=False` is a pure preview. `write=True` backs up the original, writes
atomically, and reports the transaction. Refusals raise `CstEditError`, a
subclass of `CodeEditError`, with a specific reason. There is no silent
text-patch fallback.

## Graph addresses

A path is child positions from the root:

```text
child[2]                  the 3rd child of the root
child[2].child[0]         its 3rd child's 1st child
```

Each `child[N]` selects the N-th child **after sorting by `child_index`**.
`""`, `"."`, `"root"` and `"$"` address the root. `root.child[2]`, `children[2]`
and `[2]` are also accepted for convenience.

A node's range is computed by walking its leaves in `child_index` order. The
root's range must cover the whole file; the adapter refuses a graph that does
not reconstruct the file exactly. That refusal is the lossless contract, not a
warning.

## Ops (v0)

| Op | Fields | Effect |
|---|---|---|
| `replace_node` | `path`, `text` | replace the subtree's exact source range with raw CST text |
| `insert_before_node` | `path`, `text` | insert raw text at the node's first character |
| `insert_after_node` | `path`, `text` | insert raw text at the node's last character |
| `delete_node` | `path` | delete the subtree; for statement-like nodes also consume the line and one trailing blank line when unambiguous |
| `wrap_node` | `path`, `prefix`, `suffix` | replace the range with `prefix + old_text + suffix`; raw text, no indentation magic |
| `replace_span` | `text` plus one of: `start`/`end` (characters), `start_byte`/`end_byte` (UTF-8), or `start_line`/`start_col`/`end_line`/`end_col` | explicit span fallback |

`prefix`/`suffix`/`text` are raw CST text. Insertions do not re-indent: pass the
newline and indentation you want as part of `text`. This is deliberate — the
adapter must not invent layout that the op list did not state.

`delete_node` never deletes the CST root. Its whole-line cleanup only runs when
the target owns its line (nothing but indentation before it, nothing but
whitespace after it); otherwise only the subtree is removed, and a trailing
comment stays where it is.

`replace_span` byte offsets are UTF-8 byte offsets and must land on character
boundaries; line numbers are 1-based and columns are 0-based character columns,
matching the Python/JSON adapters.

## Script shape

```json
{
  "file": "domains_rs/src/lib.rs",
  "base_sha256": "optional expected file hash",
  "ops": [
    {"op": "replace_node",
     "path": "child[3].child[1]",
     "text": "let total = a + b;"}
  ]
}
```

`base_sha256`, when present, must equal the current file hash, otherwise the
edit is refused as stale. `file` is resolved under `root`; a path that escapes
the root and a non-`.rs`/`.lua` file are both refused.

## Graph sources

### Real tree-sitter path

When `tree_sitter`, the language grammar and `substrate_rs` are importable, the
adapter calls:

```python
from domains.ts_ingest import ingest_source
info = ingest_source(Substrate(), source, "rust")  # or "lua"
```

and wraps the returned root as a `CstGraph`. The result records
`lossless.cst_backend == "tree_sitter"`.

### Synthetic path (offline/caller-supplied graphs)

`tree-sitter` + the Rust/Lua grammars are installed in this `.venv`
(`tree-sitter 0.26.1`), so the real path is the default. The adapter also
accepts a caller-provided graph in `script["cst_graph"]` (aliases `cst` and
`synthetic_cst` are accepted):

1. a `CstGraph` instance;
2. a nested text tree:

   ```python
   {
       "kind": "source_file",
       "children": [
           {"kind": "whitespace", "text": "  "},
           {"kind": "identifier", "text": "x"},
       ],
   }
   ```

   Leaves must carry `text`; interior nodes must not. `kind` is required.
   `field`, `child_index`, `named` and other attrs are optional; missing
   `child_index` values default to the child's position.

3. a serialized node/edge graph (`{"root": ..., "nodes": [...], "edges": [...]}`),
   or `{"substrate": <Substrate>, "root": <NodeID>}` for a live graph (recorded
   as `cst_backend == "substrate"`).

`cst_graph_from_nested(...)` is the small helper the tests use. This is not a
fake parser: it is the same `CstNode` graph contract with the caller as the
world adapter.

## Transaction contract

Every successful result has the shared shape:

```json
{
  "ok": true,
  "file": "domains_rs/src/lib.rs",
  "applied": false,
  "format": "rust",
  "base_sha256": "...",
  "new_sha256": "...",
  "before": {"lines": 10, "sha256": "..."},
  "after": {"lines": 10, "sha256": "..."},
  "ops": [ ... ],
  "changes": [ {"op": "...", "path": "...", "node_kind": "...", "summary": "..."} ],
  "diff_view": "...",
  "diff_note": "a unified diff is a rendered view for humans; the canonical record is the op list above",
  "backup": null,
  "lossless": {
    "roundtrip": true,
    "language": "rust",
    "cst_backend": "tree_sitter | substrate | synthetic",
    "nodes": 123,
    "leaves": 98,
    "reparse": {"checked": true, "ok": true, "reason": ""}
  },
  "graph_stale": false
}
```

On apply, the backup is written under
`var/ocelot_dev_edits/backups/<timestamp>_<sha12>_<name>`; the new text goes to
a temporary file and is moved into place with `os.replace`. `graph_stale` is
true only when the file changed.

## Validation and honesty

1. **CST round-trip.** Reconstruct the old source from the leaves and compare it
   to the file. Any difference refuses the edit; `lossless.roundtrip` is true
   only after the comparison succeeds.
2. **Leaf preservation.** Edits are applied bottom-up through
   `scripts/ocelot_lossless.LosslessText` built from the CST leaves. A leaf
   outside an edited span is byte-identical after the edit; an overlapping leaf
   is split only at the edit boundary.
3. **Overlap refusal.** Two ops with overlapping ranges (including two
   insertions at the same position, or an insertion on the boundary of a
   replacement) are refused as ambiguous, not merged.
4. **UTF-8.** The edited source must encode as valid UTF-8.
5. **Re-parse.** When the grammar is importable, the edited source is parsed
   again. A tree with `ERROR` nodes refuses an **apply**; a preview still
   returns the rendered view and records `reparse.ok = false` honestly. When
   the grammar is absent, the result records `reparse.checked = false` and the
   real reason; it does not claim a parse check it did not run.

## Limitations

- **Tree-sitter is installed in this `.venv`** (`tree-sitter`,
  `tree-sitter-rust`, `tree-sitter-lua`). The real parse/ingest/re-parse path
  runs; the test that skips is the synthetic-fallback control, not the parser.
  `cst_backend_status()` still reports an honest reason if a grammar is absent
  in another environment.
- Symbol/definition addressing does not exist for Rust/Lua yet. Ops address CST
  paths, which are stable only for one base version; pair scripts with
  `base_sha256`.
- `insert_*` and `wrap_node` do no indentation or formatting magic. The caller
  owns the raw text.
- `delete_node`'s blank-line cleanup is a small formatting heuristic, not a
  parse decision.
- The adapter is wired into `scripts/ocelot_edit.py` (`.rs`/`.lua`) and the MCP
  `dev_edit` tool; see `docs/features/GRAPH_EDIT_AND_SESSION_PLAN.md`.
- Rust/Lua grammar versions are whatever `tree_sitter_rust` /
  `tree_sitter_lua` are installed. Node kind names in scripts should be read
  from the graph rather than guessed.

## Integration notes for `scripts/ocelot_edit.py`

The dispatcher only needs the format branch; the transaction contract and the
script shape are already aligned with the Python/Markdown/JSON adapters:

```python
if suffix in (".rs", ".lua"):
    from scripts.ocelot_cst_edit import apply_cst_edit_script
    return apply_cst_edit_script(root, script, write=write)
```

`adapter_for(".rs")` should become `"rust"` and `adapter_for(".lua")` `"lua"`
instead of `"source-refused"`. Pass the script through unchanged; a synthetic
`cst_graph` key is only needed when the parser backend is unavailable. The
dev-memory journal should record the returned `base_sha256`/`new_sha256` and
`changes` exactly as it does for Python edits.

## Tests

```bash
.venv/bin/python -m pytest tests/test_cst_edit_migrated.py -q
```

Result in this environment (2026-11-14): `20 passed, 1 skipped` (the skipped
test is the synthetic-fallback control; the real tree-sitter backend test
passes now that the grammars are installed).

Covered: synthetic CST round-trip with comments/whitespace leaves; replace,
insert-before/after, delete (including two adjacent statements in one script),
wrap, char/byte span edits, and multiple disjoint edits applied bottom-up;
preview vs apply; backup content and location; stale base; raw diff refusal;
path-escape and non-source refusal; overlapping/bad paths; serialized-graph and
live-substrate input; CRLF byte preservation; outside-target preservation
(exact source comparison, not only the diff view); and honest backend/re-parse
reporting.
