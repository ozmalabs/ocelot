# Graph dev tooling: now ozagia

The dev tooling for external coding agents (dev memory and its MCP server,
repo map, code search, symbol graph, graph-addressed edits, LSP bridge, the
retrieval and agent evals) moved to its own project, **ozagia**
(<https://github.com/ozmalabs/ozagia>, MIT). Its history moved with it.
`requirements-dev.txt` installs it from GitHub. To work on ozagia itself,
install a checkout in editable mode instead:

```
uv pip install --python .venv/bin/python -e <path to an ozagia checkout>
```

## What stays in Ocelot

| file | role |
|---|---|
| `.ozagia.toml` | Ocelot's layout for ozagia: source dirs, repo-map dirs, skips, docs, import roots, path prefixes, and the adapter. |
| `tools/ozagia_ocelot_adapter.py` | Seed manifests (`seeds/*.json`) as Seed, Rule, Concept, ... nodes; the `ir` edit engine (`scripts/ocelot_ir_edit.py`); the `dev_graph_query` MCP tool (`scripts/graph_interrogate.py`). |
| `scripts/ocelot_ir_edit.py` | IR edits; needs `domains/render_python` and the substrate. |
| `scripts/_ozagia_shim.py`, `scripts/ocelot_*.py` | Shims: every old module name is an alias of its ozagia module, so imports, `python -m scripts.ocelot_*` and existing MCP registrations keep working. The shim maps `OCELOT_DEV_*` to `OZAGIA_*` and sets `OZAGIA_ROOT` to this checkout. |
| `evaluation/agent_e2e/`, `evaluation/repo_map/` | Ocelot's task suites and results for the ozagia evals. |
| `tests/test_ozagia_adapter_migrated.py` | Config, adapter, shims and the shipped task sets. |

State moved from `var/ocelot_dev_*` to `.ozagia/` (gitignored): the tag cache,
edit backups and sessions. An explicit `OCELOT_DEV_DUMP` / `OZAGIA_DUMP` still
places the snapshot anywhere, so `var/ocelot_dev_graph.json` keeps working.

## Old name → new name

| old | ozagia |
|---|---|
| `scripts/ocelot_dev_memory.py` | `ozagia.core.memory` |
| `scripts/ocelot_dev_memory_mcp.py` | `ozagia.integrations.mcp.server` |
| `scripts/ocelot_dev_session.py` | `ozagia.core.session` |
| `scripts/ocelot_repo_map.py` | `ozagia.core.repo_map` |
| `scripts/ocelot_code_search.py` | `ozagia.core.search` |
| `scripts/ocelot_symbol_graph.py` | `ozagia.core.symbol_graph` |
| `scripts/ocelot_architecture.py` | `ozagia.core.architecture` |
| `scripts/ocelot_tag_languages.py` | `ozagia.index.tag_languages` |
| `scripts/ocelot_scip_import.py` | `ozagia.index.scip` |
| `scripts/ocelot_code_edit.py` | `ozagia.edit.code_edit` |
| `scripts/ocelot_edit_txn.py` | `ozagia.edit.txn` |
| `scripts/ocelot_edit.py` | `ozagia.edit.dispatch` |
| `scripts/ocelot_cst_edit.py` | `ozagia.edit.cst` |
| `scripts/ocelot_json_edit.py` | `ozagia.edit.json_edit` |
| `scripts/ocelot_markdown_edit.py` | `ozagia.edit.markdown` |
| `scripts/ocelot_lossless.py` | `ozagia.edit.lossless` |
| `scripts/ocelot_lsp.py` | `ozagia.lsp` |
| `scripts/ocelot_repo_map_eval.py` | `ozagia.eval.retrieval` |
| `scripts/ocelot_agent_eval.py` | `ozagia.eval.agent` |
| `scripts/ocelot_index_bench.py` | `ozagia.eval.bench` (`--preset ocelot` for the old queries) |

The design docs, plans and results (`DEV_MEMORY_MCP.md`, `DEV_TOOLING_V2_PLAN.md`,
`GRAPH_CODING_LANDSCAPE.md`, `AGENT_E2E_EVAL.md`, ...) are in ozagia's `docs/`.
