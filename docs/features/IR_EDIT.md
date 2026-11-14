# IR-native Python edits (`scripts/ocelot_ir_edit.py`)

**Status:** v0 (Workstream B of `GRAPH_EDIT_AND_SESSION_PLAN.md`).
**Owner files:** `scripts/ocelot_ir_edit.py`, `tests/test_ir_edit_migrated.py`,
this note.

## What this is

`ocelot_ir_edit` is the IR-native path for **authored** Python replacements.
The replacement code is a hub `Prog*` Term-JSON tree. It is rendered by the
existing graph renderer — `domains.render_python.render_ir` /
`render_program` over the graph-resident RenderRules in
`seeds/render_python_statements.json` — and then spliced into the target's
exact source span through `scripts.ocelot_lossless.LosslessText`.

There is **one** renderer. This module does not spell Python, does not build a
second emitter, and does not fall back to a text patch. The AST-path table,
span arithmetic, lossless splice, hashing and atomic write are mechanical host
operations; the DECISION (which address, which IR) belongs to the caller
(the dev-session graph / agent). Execution/verification is deliberately not
this adapter's job: the transaction guarantees render + parse + compile, and
the caller's verify step runs tests (or `ProgEval`) afterwards.

Python only in v0. The Rust/Lua path is `scripts/ocelot_cst_edit.py`; whole
files are refused here rather than half-edited.

## Public API

```python
from scripts.ocelot_ir_edit import apply_ir_edit_script

result = apply_ir_edit_script(root, script, write=False)   # preview
result = apply_ir_edit_script(root, script, write=True)    # apply + backup
```

`script` is the shared edit-script shape:

```json
{
  "file": "domains/foo.py",
  "base_sha256": "<optional; staleness guard>",
  "ops": [ ... ]
}
```

The result is the shared transaction contract (all fields present):

```json
{
  "ok": true,
  "file": "domains/foo.py",
  "applied": false,
  "format": "python",
  "engine": "hub_ir",
  "renderer": "domains.render_python",
  "base_sha256": "...",
  "new_sha256": "...",
  "before": {"lines": 10, "sha256": "..."},
  "after":  {"lines": 10, "sha256": "..."},
  "ops": [ ... ],
  "changes": [ {"op": "...", "target": "...", "summary": "..."} ],
  "diff_view": "...",
  "diff_note": "a unified diff is a rendered view; the op list is canonical",
  "backup": null,
  "lossless": {"python_cst": true, "roundtrip": true,
                "outside_spans_unchanged": true,
                "spans": [[start, end]], "leaves": 41},
  "graph_stale": false,
  "blockers": []
}
```

Refusals raise `scripts.ocelot_code_edit.CodeEditError` with a specific
reason: raw `diff`/`patch` input, a raw `text` key inside an IR op, a stale
`base_sha256`, a path escaping the repo root, a non-`.py` file, an unknown
op, a malformed/invalid hub Term, a bad AST path, overlapping edits, or a
result that would not parse/compile.

A well-formed script whose IR the renderer cannot spell is **not** an
exception: it returns `ok: false`, a populated `blockers` list, an empty
`diff_view`, `applied: false`, and leaves the file untouched. This is the
dispatcher's signal to use the CST fallback.

## Ops (v0)

| op | fields | effect |
| --- | --- | --- |
| `replace_expression_ir` | `target`, `term` | replace an expression at an AST path, e.g. `body[3].body[1].value` |
| `replace_body_ir` | `target`, `stmts` | replace a function/method body with a list of hub-IR statements |
| `replace_function_ir` | `target`, `stmts` or `term`, optional `args` | replace the `def` header + body; `term` means `return <term>`; decorators are preserved; `args` may be `ProgDefFnParam` terms or plain identifier strings |
| `fallback_check` | `target` or `term` or `stmts` | read-only coverage probe; never writes |

AST paths use the same structural grammar as `ocelot_code_edit`:
`body[3].body[1].value`, `body[0].args.args[1]`, etc. They are stable for one
base version; pair an edit with `base_sha256`.

`fallback_check` returns the same contract plus:

```json
{"check": "fallback_check", "renderable": false, "grain": "function",
 "node_type": "FunctionDef", "ir": null, "rendered": null,
 "blockers": ["With"]}
```

`ok` is the answer (`ok == renderable`). A target can be a function, an
expression, or a statement; `term`/`stmts` check a supplied Term-JSON tree.
It is read-only: `write=True` is refused.

## How rendering uses the graph

A fresh minimal substrate is created per transaction (`substrate_rs.
Substrate()`) and `domains.render_python.install_python_statement_renderer`
installs the seed's `Language` + `RenderRule` nodes. Then:

* expression terms → `render_ir(sub, term, indent="")`;
* statement lists → `{"type": "ProgSeq", "stmts": [...]}` through
  `render_ir(sub, ir, indent=<body indent>)` — the renderer's first line is
  unindented by contract, so the placing container prefixes the body indent;
* function parameters → `render_ir` on each `ProgDefFnParam`;
* function coverage in `fallback_check` → `render_program(sub, ir,
  name=<name>)`, plus `render_gap_check` and `renderability_refusals`.

Fresh-per-transaction is deliberate: the render-gap convention records
`Impasse{reason: "render_gap"}` nodes and a `_render_gaps` question list on the
substrate, and one transaction must never inherit another transaction's gap
evidence.

## IR coverage (honest limits)

Renderable is exactly what the python RenderRule seed can spell:

* Statements: `ProgSeq`, `ProgAssignVar`, `ProgAugAssign`,
  `ProgTupleUnpack`, `ProgIfStmt`, `ProgForEach`, `ProgWhile`, `ProgLoopCtl`,
  `ProgReturn`, `ProgTryOr`, `ProgRaise`, `ProgImportStmt`,
  `ProgSubscript`, `ProgSubscriptSet`, `ProgAttrGet`, `ProgAttrSet`,
  `ProgContainerLit`, `ProgComprehensionList`, `ProgComprehensionGen`,
  `ProgFString`, `ProgIsOp`, `ProgCallExtern`, `ProgDefFnParam`.
* Expressions: `Lit`, `Var`, `Eq/Gt/Gte/Lt/Lte`, `Mod/Minus/Pow/Div`,
  `Plus/Times/And/Or`, `Not/Neg`, `IfThenElse`, `In`, and the expression-shaped
  `Prog*` forms above.

Known blockers / gaps observed in this adapter:

* Hub Term types with no python RenderRule: `ProgSlice`, `BitAnd`, `BitOr`,
  `BitXor`, `Shl`, `Lshr`, `Ashr`, `Sqrt`, … → `render_gap:<head> in python`.
* Renderability refusals from the seed: an f-string literal part that needs
  escaping (`fstring_literal_unspellable`), an unknown aug-assign op, a
  malformed dict literal, etc. → reported verbatim.
* Source constructs the emitter does not cover (`fallback_check` on an
  existing function): `With`, `Match`, `Lambda`, `Yield`, `Await`,
  typed/multiple `except`, `try/finally`, star args/kwargs, mutating
  recv-method calls, etc. → the emitter's blocker names.
* Whole-function replacement of an `async def` is refused
  (`blockers: ["async_function"]`). Replacing a *body* of an async function is
  allowed (the header is untouched; the authored IR contains no `await`).
* Comments inside a replaced body/function span are replaced with the
  construct. Comments outside the span are preserved byte-for-byte.

No partial emit: if one op in a multi-op script is blocked, all ops are
discarded and the file is untouched.

## Splicing and lossless guarantees

The span comes from `ocelot_code_edit.ast_node_table`; the replacement is
applied to `LosslessText.from_python(source)`. Every leaf outside the target
range is left byte-identical, and the module mechanically verifies that all
characters outside the declared spans are unchanged
(`lossless.outside_spans_unchanged`). The result is parsed with `ast.parse`
and compiled before it is returned. A function replacement starts at the
`def` line, so decorators are preserved; a body replacement starts at the
first body statement and keeps the header and signature exactly.

Files are read and written as bytes (UTF-8), so text-mode newline translation
cannot silently normalize the file. `base_sha256` / `new_sha256` are the
SHA-256 of those bytes (for pure-ASCII/LF files this is identical to the other
adapters' text hash; for CRLF files it is the exact on-disk hash, which is the
point of the byte-for-byte splice).

## Transaction semantics

* Default is preview: `write=False`, `applied=false`, `graph_stale=false`.
* Apply: copy to `var/ocelot_dev_edits/backups/<timestamp>_<sha12>_<name>`,
  write a temp file, `os.replace`, return `backup`, `before.sha256`,
  `after.sha256`, `applied=true`, `graph_stale=true`.
* `base_sha256`, when supplied, must match the current file exactly.
* Raw `diff`/`patch`/`unified_diff`/`hunk` keys are refused at the script
  level; `text` and the diff keys are refused inside an IR op.
* Overlapping edits in one script are refused rather than merged.

## Tests

```bash
.venv/bin/python -m pytest tests/test_ir_edit_migrated.py -q
```

Covers expression + statement rendering, body/function replacement, comment
preservation outside the span and replacement inside it, one-line expansion,
nested method indentation, decorator/annotation preservation, render gaps and
renderability refusals, `fallback_check` positives/negatives, invalid IR,
preview/apply/backup, stale base, raw diff/text, path escape and non-Python
refusals, and multi-op bottom-up application.

## Integration notes (`scripts/ocelot_edit.py`)

The central dispatcher can route by explicit intent:

```python
from scripts.ocelot_ir_edit import apply_ir_edit_script

def _is_ir_op(op) -> bool:
    return isinstance(op, dict) and (
        str(op.get("op", "")).endswith("_ir")
        or op.get("op") == "fallback_check")

if Path(file).suffix == ".py" and (
        script.get("engine") == "ir"
        or any(_is_ir_op(op) for op in script.get("ops", []))):
    return apply_ir_edit_script(root, script, write=write)
return apply_python_edit(root, script, write=write)   # existing CST path
```

`fallback_check` is also routed by `apply_ir_edit_script` itself, so a
dispatcher may call the single entry point for every IR-intent script.
`engine` is not part of the canonical op list (it is a routing hint only); the
op list remains the canonical record. The default `.py` route stays the CST
editor: IR is for authored replacements, CST is the general fallback.

The MCP/dev-memory layer only needs to record the returned transaction
(`base_sha256`/`new_sha256`/`backup`/`diff_view`) as it already does for the
other adapters.
