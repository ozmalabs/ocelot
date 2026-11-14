# LSP bridge and symbol-level impact

**Status:** Workstream A v1 (2026-11-14). The client and fake-server tests are
landed; the central integrator owns the MCP/CLI wiring. This module is dev
tooling, not agent runtime: it never edits, never boots the substrate and never
decides what a symbol means — it asks the language server that already knows.

## Why

The tree-sitter repo map (`scripts/ocelot_repo_map.py`) is fast and broad, but
its edges are syntactic: same-named symbols, shadowing, imports and dynamic
dispatch produce false or missing references. The P0 gap in
[`GRAPH_CODING_LANDSCAPE.md`](GRAPH_CODING_LANDSCAPE.md) is compiler-accurate
navigation and diagnostics. `scripts/ocelot_lsp.py` is that layer:

- definitions and references resolved by pyright, rust-analyzer or clangd;
- push diagnostics after an edit, without running a build;
- document symbols and hover;
- call hierarchy (callers/callees) for symbol-level impact;
- rename **preview** from the server's `WorkspaceEdit`, never an automatic
  write;
- honest refusal when the server binary or language is absent.

The file-level graph remains the fast/fallback path. This module complements
it; it does not replace the repo map, and it does not ingest SCIP (Workstream C
does that).

## Process and protocol model

- **One client per (root, language, command)** via `get_client`, or construct
  `LSPClient` directly. Construction is cheap; the server process starts on
  the first query.
- **stdio JSON-RPC 2.0 with `Content-Length` framing.** A reader thread
  dispatches responses by integer id, caches
  `textDocument/publishDiagnostics`, and answers server-to-client requests:
  `workspace/configuration` returns nulls, `workspace/applyEdit` is refused,
  capability registration/work-done requests return null.
- **Initialize once** with `rootUri`, `rootPath`, `workspaceFolders`, a
  conservative capability set (`definition.linkSupport`,
  `documentSymbol.hierarchicalDocumentSymbolSupport`, `hover.contentFormat`,
  `callHierarchy`, `publishDiagnostics.versionSupport`, UTF-16 positions),
  then the `initialized` notification.
- **Synchronize before querying:** `textDocument/didOpen` with the file text,
  then `didChange` (full text, incremented version) when the content hash
  changes. External edits between queries are therefore picked up. There is no
  didSave or file watcher.
- **Explicit close:** `shutdown` request, `exit` notification, bounded wait,
  then terminate/kill if needed. `close()` is idempotent. The child process is
  reaped only when you call `close()` or `close_all()`; process exit is not
  automatic.
- **Timeouts:** 20 s per request, 60 s for initialize, 5 s for the first
  diagnostics push, 5 s for close. Request/initialize/diagnostics timeouts are
  constructor options; `close(timeout=...)` takes its own. A timeout returns a
  dict; it does not kill the server. `$/cancelRequest` is not sent.

## Registry

The project venv (`.venv/bin`) is searched before `PATH`; the first available
candidate wins.

| Language | Candidate order | Notes |
|---|---|---|
| `python` | `pyright-langserver --stdio`, then `pylsp` | pyright is the intended server; pylsp is the fallback |
| `rust` | `rust-analyzer` | rustup shim must have the component installed |
| `c` / `cpp` | `clangd` | uses `compile_commands.json`/`compile_flags.txt` when present |
| `typescript` | `typescript-language-server --stdio` | absent in this environment |
| `javascript` | `typescript-language-server --stdio` | same server, JS language id |

Aliases (`py`, `rs`, `c++`, `cc`, `ts`, `tsx`, `js`, ...) are normalized.
`detect_language(path)` maps suffixes; `.h` maps to `c`, `.hpp`/`.cxx` to
`cpp`, `.tsx`/`.jsx` to their LSP language ids.

`server_candidates(language, root)` and `available_servers(root)` are
read-only registry snapshots. **`available` means the binary was found, not
that it can speak the protocol.** A broken rustup shim, for example, is found
on `PATH` but exits during initialize; the query then fails and
`server_status()["last_start_error"]` carries the stderr explanation.

## Public API

```python
from scripts.ocelot_lsp import (
    LSPClient,          # root, language, command=None, *, timeout, ...
    get_client,         # shared per (root, language, command)
    close_all,          # close every shared client
    detect_language,    # path suffix -> registry language | None
    server_candidates,  # registry + availability, no spawn
    available_servers,  # all languages, no spawn
    LSPError, LSPTimeout, LSPUnavailable,
)
```

### Positions

All `line`/`character` arguments and all location fields are **LSP-native**:
0-based lines and UTF-16 code-unit characters. MCP and CLI surfaces that show
1-based editor lines should add/subtract 1 at that boundary. No conversion of
astral-plane characters is performed.

### Queries

Every query returns a plain JSON-shaped dict. Failures are
`{"ok": False, "error": ..., "available": bool, "running": bool, ...}`, never
an exception. Paths inside the root are repository-relative POSIX paths;
locations outside the root (stdlib, external packages) keep an absolute path
and always carry the `file://` URI.

| Method | Result (besides `ok`/`method`) |
|---|---|
| `definition(path, line, character)` | `locations`, `count`, `found` |
| `references(path, line, character, include_declaration=False, retry_empty=True)` | `locations`, `count`, `include_declaration`, `attempts`, `retried` |
| `document_symbols(path)` | `symbols` (nested `children`), `count`, `top_level` |
| `hover(path, line, character)` | `contents` (text), `markup_kind`, `found`, `range` |
| `diagnostics(path)` | `diagnostics`, `count`, `cached`, `waited`, `published`, `version` |
| `prepare_call_hierarchy(path, line, character)` | `items`, `count` |
| `incoming_calls(path, line, character)` | `calls`, `count`, `direction="incoming"`, `items` |
| `outgoing_calls(path, line, character)` | `calls`, `count`, `direction="outgoing"`, `items` |
| `rename_preview(path, line, character, new_name)` | `files`, `file_count`, `total_edits`, `resource_operations`, `applied=False`, `writes=False` |
| `symbol_impact(path, line, character, include_declaration=False, retry_empty=True)` | grouped `files`, `file_count`, `total`, `symbol`, `attempts`, `written=False`, `read_only=True` |
| `server_status()` | availability, running/pid/return code, command/candidates, opened docs, diagnostics counts, capabilities, server info, stderr tail, protocol errors |
| `request(method, params=None, timeout=None)` | generic `{ok, result}` escape hatch (advanced use) |

**Cold-index retry.** A cold pyright can answer the first workspace-wide
`references` request with an empty list before its file scan completes. When
the answer is empty, `references` (and therefore `symbol_impact`) retries after
0.2 s and 0.5 s by default; `attempts` and `retried` report what happened. Pass
`retry_empty=False` for a strictly single request. This is a bounded
mitigation, not a readiness barrier: a rename or call hierarchy issued
immediately after startup can still be incomplete. A warm-up
`definition`/`document_symbols` query, or the first reference query on a real
symbol, gives the server time to index.

A location has:

```json
{
  "uri": "file:///repo/a.py",
  "path": "a.py",
  "line": 2, "character": 4,
  "end_line": 2, "end_character": 9,
  "start": {"line": 2, "character": 4},
  "end": {"line": 2, "character": 9}
}
```

`LocationLink` responses are normalized to the selection range and also carry
`target_range`; `SymbolInformation` and hierarchical `DocumentSymbol` responses
are both accepted.

### Diagnostics cache

`textDocument/publishDiagnostics` is a notification, so the client caches it
per normalized file URI and document version. A `diagnostics(path)` call waits
for a publish when the cache is empty (up to the diagnostics timeout); once a
publish has arrived, later calls are served from the cache without touching the
server. A content change clears the cache and sends `didChange`.

An empty list is a legitimate published diagnostic set; `published` and
`received` distinguish "server said clean" from "nothing arrived before the
timeout". Stale publishes (older document version) are ignored.

### Symbol impact

`symbol_impact` calls `textDocument/references` and groups locations by file:

```json
{
  "ok": true,
  "symbol": {"path": "a.py", "uri": "file:///repo/a.py",
             "line": 0, "character": 4},
  "file_count": 2,
  "total": 3,
  "files": [
    {"path": "b.py", "uri": "file:///repo/b.py", "count": 2,
     "references": [
       {"line": 3, "character": 4, "end_line": 3, "end_character": 9},
       {"line": 5, "character": 8, "end_line": 5, "end_character": 13}
     ]},
    {"path": "a.py", "uri": "file:///repo/a.py", "count": 1,
     "references": [{"line": 2, "character": 4,
                     "end_line": 2, "end_character": 9}]}
  ],
  "attempts": 1,
  "retried": false,
  "written": false,
  "writes": false,
  "read_only": true
}
```

Files are ordered by reference count descending, then path; references by
position. `include_declaration` defaults to false, so the definition is not
counted unless the caller asks and the server honors it. `attempts`/`retried`
show whether the cold-index retry ran. This is the symbol-level counterpart to
the file-level `impact` in `scripts/ocelot_repo_map.py`; it never edits.

### Rename preview

`rename_preview` sends `textDocument/rename` and normalizes the server's
`WorkspaceEdit` (`changes` and `documentChanges`) into per-file text edits. It
**does not apply anything** and does not read back or write files. Resource
operations (create/rename/delete file) are listed under `resource_operations`
but are not executed. Applying a rename remains the job of the semantic edit
transaction (`scripts/ocelot_code_edit.py`), which is currently Python-only
and file-scoped; cross-file/multi-language rename application is a future
integration step.

## Honest failure and status

- Missing binary: `server_status()` has `ok=False`, `available=False`,
  `error="language server binary not found: ..."`; queries fail the same way
  without raising or spawning.
- Unsupported language: `supported=False`, `error="unsupported language ..."`.
- Server exits during initialize: query error includes the exit code and tail
  of stderr; `server_status()["last_start_error"]` retains it.
- Timeout: `ok=False`, `timeout=True`, `error="... timed out after Ns"`; the
  client remains usable for later requests.
- After a crash the client does **not** auto-restart (opened-document state
  would be lost). Close it and create a new client/`get_client` entry.
- `server_status()` never starts a server and never raises.

No public function prints. The CLI/MCP wrappers own rendering.

## Tests

`tests/test_lsp_migrated.py` runs a generated fake stdio server (a real
subprocess) that implements initialize/initialized/didOpen/didChange,
definition, references, documentSymbol, hover, prepareCallHierarchy,
incoming/outgoing calls, rename and shutdown; it deliberately ignores one
method so the client timeout path is exercised.

The default suite proves:

- `Content-Length` framing (the fake logs each frame header and body length)
  and unique request ids, including a non-ASCII source body framed by UTF-8
  bytes;
- initialize ordering and `didOpen` before the first query;
- shared-client reuse via `get_client` and process cleanup via `close_all`;
- definition/location normalization, document symbols, hover;
- references and `symbol_impact` grouping without writes, including the
  empty-first-answer cold-index retry (`attempts=2`) and its bounded delay;
- diagnostics cache hits and `didChange` invalidation;
- call hierarchy item round-trip (`data` preserved);
- rename preview grouping and unchanged files;
- timeout honesty and continued usability;
- server error responses (`-32601`) reported as failures, not exceptions;
- absent-binary and unsupported-language failure dicts;
- explicit idempotent close and `shutdown`/`exit`.

Live smoke tests are gated by `OCELOT_LIVE_LSP=1` and skip when a server is
absent, cold or unable to answer; they are not part of the default gate. The
fake server proves our protocol handling, not server-specific compatibility.

Verification in this tree on 2026-11-14:

```text
.venv/bin/python -m pytest tests/test_lsp_migrated.py -q
14 passed, 2 skipped in 1.04s

OCELOT_LIVE_LSP=1 .venv/bin/python -m pytest tests/test_lsp_migrated.py -q -rs
15 passed, 1 skipped in 2.35s
# live pyright definition passed; rust-analyzer skipped:
# "Unknown binary 'rust-analyzer' in official toolchain"
```

## Integration notes (MCP / CLI, owner: central integrator)

1. Import lazily and share clients:
   `from scripts.ocelot_lsp import get_client, close_all, detect_language`.
   Key by root + language; let `get_client` reuse the server across calls.
   Do not create a client per request.
2. Map tools:
   `dev_definition`, `dev_references`, `dev_diagnostics`,
   `dev_callers` -> `incoming_calls`, `dev_callees` -> `outgoing_calls`,
   `dev_rename_preview`, and a symbol-level branch of `dev_impact`.
   Keep `dev_repo_map`/`dev_impact` as the syntactic fallback.
3. Tool arguments: accept repo-relative paths and 1-based editor lines at the
   MCP boundary, subtract 1 before calling this module, and add 1 back when
   rendering locations. Convert the returned dict directly; do not re-wrap the
   location fields.
4. Diagnostics after an edit: call the edit transaction first, then
   `diagnostics(path)` on the same shared client. The content hash triggers
   `didChange` and a fresh publish. Treat `published=False` as "no diagnostic
   result", not "clean".
5. Symbol impact: prefer `symbol_impact(path, line, character)`. If it returns
   `ok=False` with `available=False`, fall back to the file-level
   `ocelot_repo_map.impact`. Never infer a symbol from a bare name.
6. Rename: show `rename_preview` to the caller. Do not apply it automatically.
   For same-file Python, translate the preview into an
   `ocelot_code_edit` op list and go through its preview/write transaction;
   cross-file or non-Python application is not implemented yet.
7. Status: `server_status()` (or `available_servers()`) is safe to call on
   every MCP status request; it never spawns a server. Surface
   `last_start_error` rather than claiming the server works.
8. Shutdown: MCP server exit and CLI teardown should call `close_all()`.
   Daemon threads are not a substitute for reaping child processes.
9. Suggested CLI verbs: `lsp-status`, `definition`, `references`,
   `diagnostics`, `callers`, `callees`, `rename-preview`, `symbol-impact`.
   Print `json.dumps(result)` and use a non-zero exit only when
   `result["ok"]` is false due to an invalid request; an absent server is a
   reported status, not a crash.
10. Language selection: `detect_language(path)` first; allow an explicit
    `language` override. Unsupported/absent servers are honest failures, not
    silent tree-sitter substitutions inside this module.

## Limitations

- Cold start and project configuration are real: pyright may index, rust-analyzer
  needs a Cargo project and a working rustup component, clangd wants
  `compile_commands.json`/`compile_flags.txt`. The client times out honestly
  rather than inventing answers.
- This environment has pyright and clangd; rust-analyzer is a rustup shim
  without the component, and no TypeScript server is installed. Availability
  means "binary found".
- Call hierarchy depends on server support and on a hierarchy item at the
  exact position. An empty `items` list is reported, not guessed.
- Cold indexing is not a readiness barrier. References retry an empty answer,
  but a rename preview or call-hierarchy query issued immediately after
  startup can still be incomplete. Warm the server with a query on a real
  symbol before a destructive-looking preview.
- `references` retries only an empty list; a partial answer cannot be detected.
  A legitimate zero-reference symbol pays up to 0.7 s of retry delay unless
  `retry_empty=False` is passed.
- Positions are UTF-16 code units. A caller using Python string indices on
  lines containing astral characters must convert.
- Push diagnostics only: no pull diagnostics, no workspace diagnostics, no
  related-document aggregation. A publish can lag an edit; the first query
  waits, later queries use the cache.
- `rename_preview` is a preview. It does not resolve conflicts, apply resource
  operations or feed the edit journal; that is the integration gap.
- No restart after a server crash; close and rebuild the client.
- Timeouts abandon the request id but do not cancel the server-side work.
- No cross-repo/external-library graph; that is the SCIP workstream.
- The fake-server tests prove protocol correctness, not language-server
  compatibility. The live tests are optional and skip aggressively.
- No new dependencies; stdlib only (`subprocess`, `threading`, `json`, ...).
