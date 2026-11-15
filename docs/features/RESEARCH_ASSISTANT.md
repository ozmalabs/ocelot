# Research helper in Ozagia

The research implementation has moved to `ozagia.research`. Ocelot keeps
compatibility entry points under `scripts/`, plus its engine/seed provenance
adapter and existing examples. In Ozagia use `ozagia-mcp --mode research` or
`--mode combined` to expose research tools alongside coding tools; the default
mode remains coding. The installed Ozagia checkout must include research mode.
See the Ozagia checkout's `docs/research.md` for portable setup and limitations.

The research helper gives an LLM assistant a local, persistent investigation
ledger and a small cited source index. It records the researcher's claims and
relationships; it does not decide whether they are true. It is development-side
tooling, not the Rust agent runtime or a proof checker.

Start the MCP server with `python -m scripts.ocelot_research_mcp --workspace
/path/to/writable-workspace`. It exposes `research_init`, `research_context`,
`research_record`, `research_link`, `research_inspect`, `research_check` and
`research_export`. It uses newline JSON-RPC and supports Content-Length
framing. The CLI offers the same operations as
`python -m scripts.ocelot_research_service OP --workspace PATH --args 'JSON'`.
The returned `investigation_id` is the `session_id` for subsequent calls.
New sessions live under `WORKSPACE/.ozagia/research/<id>.json` (or the
configured `OZAGIA_STATE_DIR`). Legacy `WORKSPACE/var/ocelot_research` sessions
are read in place and copied to the configured state directory on first write;
the original remains intact.

Initialize with a question, a mode (`exploratory`, `confirmatory`, `empirical`,
`deductive`, or `qualitative`) and explicitly selected source roots. For
example, `research_init` accepts:

```json
{"question":"Does a total single-valued Boolean extension eliminate arbitrary residual difficulty?",
 "mode":"deductive",
 "roots":[
  {"root_id":"ocelot","path":"/applications/data/projects/ocelot","files":["docs/SCIENCE_RESEARCH.md"]},
  {"root_id":"ge","path":"/applications/data/projects/graphic-equalisation","files":["notes/GRAPHIC_EQUALISATION_FOR_LLMS.md","notes/experiments/ge_oracle_elimination/PAPER_CLAIM_EVIDENCE.md"]}
 ]}
```

Then call `research_context` with `session_id` and `query`. The lexical index
returns selected passages, line locators, full-file hashes, revisions where
available, dirty state and coverage. Reopen and read the actual source; lexical
matches and links in prose are not evidence edges. A `Source` record can store
a result's `citation` object as `fields.locator`; `research_check` compares it
with the current file hash. Paths are constrained to their configured roots.
Roots are user-supplied local paths: configure only sources the assistant may
read. The source index is rebuilt on context/check; large manifests cost time.

Call `research_record` with `kind` and `fields` to add `Frame`, `Claim`,
`Evidence`, `Alternative`, `Assumption`, `Protocol`, `Run`, `Observation`,
`Decision` and other typed nodes. For example a claim's fields can include
`wording`, `scope`, `claim_type`, `author`, `status`, and `limitations`.
Use `research_link` with `src`, `relation`, `tgt` and optional `fields`
containing `provenance` and `rationale`. Supported relations include
`supports`, `opposes`, `assumes`, `scoped_by`, `tests`, `cites` and
`supersedes`. Relations are authored assertions, not inferred from documents.
Use a new node and `supersedes` for corrections; the prior event remains.
`research_inspect` without a node ID returns the full graph; with `node_id`
it returns the node and adjacent relationships. `research_export` returns a
Markdown ledger, JSON bundle and mechanical checks.

For a deductive or qualitative investigation, put
`empirical_exemption_reason` on a `Frame` record. For a finite mathematical
check, record a `Run` with `finite_check: true`, `domain`, `bounds`,
`oracle_independent`, `oracle_description` and `verification_label`.
Confirmatory records use a `Protocol` with the fields returned by the check;
a `Run` references its `revision` with `protocol_revision`. A protocol
recorded after a run's stated start cannot be treated as prospective. The
helper has no execution capture or immutable-revision verification adapter:
all run receipts and protocol metadata are assertions, and the integrated
check blocks a confirmatory eligibility label for manual receipts. Verify
engine provenance, seed allocation, actual preregistration and controls using
the repository's existing tools and primary artifacts. A passed checklist
is not proof, source validation, or a successful experiment.

The graph is append-only at the application level and persisted atomically,
with a single writer assumed. There is no locking or independent tamper-proof
log. It does not run arbitrary commands, call a model, access the network, or
write to source repositories; `check_lean` invokes only the local Lean compiler. Citations can become stale; hashes and status expose
that rather than preserving a copy of the original source. Graph checks are
mechanical and incomplete: researchers must review claim scope, evidence,
contradictions and the appropriateness of the GE frame themselves. Evaluation
of research benefit is still pending; see
[the evaluation design](../research/research_assistant/EVALUATION_DESIGN.md).

## Provenance and examples

A `Protocol` may include `prereg_git: {"root_id": "ocelot", "path":
"...", "commit_oid": "<full commit hash>"}` for a file selected in its
root manifest. `research_check` inspects the immutable Git blob, compares it
with the working file and reports the commit timestamp as metadata. Set
`check_seed_claim: true` on that protocol to run the existing seed-claim scan
against the **current** Ocelot tree; it may take time. A `Run` with
`uses_ocelot: true` optionally supplies `engine_stamp` and checks the engine
loaded by the helper process against current sources and that stamp. These
checks cannot prove a historical run's engine, execution, or registration
time. A current seed conflict may reflect legitimate use after the run; a clean
scan means only no collision detected within the scanner's limits. Check
results do not turn manually entered receipts into captured execution.

Two reproducible examples create sessions only in the specified writable
workspace and print an export:

```bash
python -m scripts.ocelot_research_example --workspace /tmp/research-demo \
  --ge-root ../graphic-equalisation > /tmp/ge-example.json
python -m scripts.ocelot_research_example --workspace /tmp/research-demo \
  --historical --ocelot-root . > /tmp/historical-example.json
```

The historical example imports a preregistration and results report as source
references; it does not certify their chronology or claim to have replayed the
run. `research_inspect` accepts `transitive: true` to return the connected
component, and loading a session replays and checks the persisted event log.

## Executable derivation chains and Lean

Research nodes can carry the same native Term JSON used by the substrate. A
node's `bindings` map names used in `EvalSubgraph` terms to other research node
IDs; record a `derived_from` edge from the node to each dependency. For example,
create a claim with `term: {"type":"Var","name":"x"}`, then a second claim
with `term: {"type":"Not","arg":{"type":"EvalSubgraph","node":{"type":"Var","name":"prior"}}}`
and `bindings: {"prior":"claim-0001"}`, and link the second claim to the
first with `derived_from`. Use the IDs actually returned by `record`.

`research_trace(session_id, node_id)` walks the directed dependency graph,
including branches; it returns nodes, links, paths, and cycle/bound statuses.
`research_execute(session_id, node_id, env={"x":false})` materializes the
terms with the native `add_term_subgraph` API, checks reflection, and computes
the target with `EvalSubgraph`. Bindings share the native environment; reuse a
binding alias only for the same node and do not use `target_term`. The result
includes the engine provenance stamp and a trace. A missing term, unsupported
native expression, conflicting binding, cycle, resource bound, or unresolved
value is reported rather than accepted as a result. These operations are also
available as CLI verbs `trace` and `execute` using `--args` JSON.

`research_export_lean(session_id, node_id)` emits Lean 4 definitions for the
explicit Boolean portion of the chain. It supports Boolean literals and inputs,
`And`, `Or`, `Not`, `Eq`, and graph-bound `EvalSubgraph` terms; unsupported
terms are rejected. The output preserves research node IDs and binding
metadata, and external inputs become Boolean parameters. It provides formal
syntax to inspect and extend in Lean; it does not translate natural-language
claims into theorems or prove the source-to-Lean translation faithful. The
export reports `kernel_checked: false`; use `research_check_lean` to check the
generated declarations with the local compiler.

To write a `.lean` file from the CLI, use the same session and target IDs:

```bash
python -m scripts.ocelot_research_service export_lean --workspace . \
  --args '{"session_id":"SESSION_ID","node_id":"claim-0002"}' \
  --lean > derivation.lean
```

## Read a paper into research claims

Configure the paper's `.tex` or Markdown source as a selected file in an
investigation root. `research_paper_preview(session_id, root_id, path)` uses
the existing arXiv LaTeX environment reader or Markdown paper reader, then
runs the construction grammar on each recognized statement. It returns exact
source hashes and line locators, raw passages, candidate interpretations,
references and unresolved material without writing the investigation.
`research_paper_ingest` records source-linked claims and references, plus
source-located displayed and inline math candidates as Evidence nodes. Formula
candidates are not automatically treated as claims. `max_formula_candidates`
and `formula_offset` page through candidates; the returned `formula_next_offset`
and `formula_has_more` describe remaining work. Overlapping pages reuse existing
candidates. Repeating a completed page is detected; an interrupted import is
reported separately.
For a separately generated LaTeXML XML file selected in the same source-root
manifest, `latexml_path` adds a supplemental document structure report and
bounded equation candidates to the preview. Its hash is recorded alongside the selected TeX hash, but their
correspondence and converter version are not verified; XML elements are not
used to create claims or source locators. No LaTeXML process is invoked.
The matching CLI operations are `paper_preview` and `paper_ingest`.

`research_formula_parse_candidates(session_id, formulas)` is a separate,
opt-in parser adapter. It accepts up to 256 LaTeX strings and returns one
candidate record per input with `adapter`, `status`, `verified`, `is_claim`,
`semantics`, `limitations`, and `parser_versions`. A parsed result contains
`expression_repr`; an ambiguous Lark parse contains bounded `alternatives` and
sets `has_alternative_parse_tree`; failures contain a bounded `reason` and
`exception_type`. SymPy and its Lark backend are optional;
unavailable dependencies and parse failures are returned as statuses. A parsed
expression remains an unverified interpretation candidate. This operation does
not add graph records, execute a formula, or run automatically during paper
preview, ingest, or native formula translation. The CLI operation is
`formula_parse_candidates` with `--args` JSON.

A recognized theorem, definition or other statement is a paper assertion, not
an established fact. Grammar output is a proposed interpretation: check it
against the original text, especially for nested quantifiers, LaTeX macros,
formulae, and cross-file references. Author-written proof references create
traceable links labelled as syntactic references, not verified dependencies.
The reader does not yet extract arbitrary prose claims or read PDF directly;
convert to a selected local source file first. An empty extraction or unresolved
reference is reported rather than treated as a complete paper understanding.

`research_model_candidate` connects an imported claim or sourced formula
Evidence node to an explicitly supplied native Term. Provide `claim_id`, `term`, `residuals`, `reviewer` and
`review_note`; optional `bindings` and `assumption_ids` connect the model to
other recorded nodes. The result keeps the source reference, interpretation,
assumptions and unresolved gaps alongside a candidate term. Use the returned
node ID with `research_trace`, `research_execute`, and `research_export_lean`.
The construction grammar does not automatically turn arbitrary prose or math
into executable code: an assistant or researcher must supply and review that
mapping. Native execution checks the supplied model, not whether it faithfully
represents the paper or proves its claim. Lean export remains limited to the
supported Boolean terms and requires a separate Lean check.

`research_native_graph(session_id)` projects the investigation into a fresh
native substrate graph using the same typed-node, typed-edge and Γ-production
mechanism as the paper representation work. It returns the snapshot and the
mapping from research IDs to native node IDs; this is a projection, so edits
to a later native graph do not automatically update the research ledger.
Optionally supply a native DSL `query` and `env` to evaluate against that
projection. The native snapshot is checked for changes after the query. The
source excerpts, proposed readings, links and residuals remain attributed data.

For example, initialize a session with a selected local source:

```bash
python -m scripts.ocelot_research_service init --workspace . --args \
  '{"question":"What does this paper claim?","roots":[{"root_id":"ge","path":"/absolute/path/to/graphic-equalisation","files":["papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex"]}]}'
```

Use the returned investigation ID in both calls:

```bash
python -m scripts.ocelot_research_service paper_preview --workspace . --args \
  '{"session_id":"SESSION_ID","root_id":"ge","path":"papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex"}'
python -m scripts.ocelot_research_service paper_ingest --workspace . --args \
  '{"session_id":"SESSION_ID","root_id":"ge","path":"papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex"}'
python -m scripts.ocelot_research_service native_graph --workspace . --args \
  '{"session_id":"SESSION_ID","query":{"type":"NodesOfType","node_type":"Claim"}}'
```

The projected snapshot uses the substrate's own tagged JSON wire encoding for
nested values; load it with `graph_from_dict` to recover native attributes.

Scoped mathematical vocabulary can be recorded in this same ledger using
`MathematicalSymbol` and `MathematicalDefinition` nodes. A `defines` edge links
a definition to its symbol; `uses_symbol` links another node to a symbol;
`constrains` links an assumption to a symbol. Existing `scoped_by` edges attach
these records to a `Frame`. These links can be authored directly; the source
reader also proposes some links as described below. It does not generally
infer definitions or validate mathematical types.

Paper ingestion also records bounded, source-located TeX macro declarations,
explicit domain declarations and definition excerpts as graph context. Local
declarations in the same recognized statement share a child Frame; it inherits
the paper Frame's notation without importing sibling scopes. Where no enclosing
statement is recognized, scope is limited to the declaration. These are source-derived candidates, not
verified mathematical semantics. Parsing covers only selected declaration
forms, and a TeX macro may have narrower scope than the source reader detects.

`research_formula_resolve` takes `session_id`, `formula`, and `scope_id`. It
queries scoped symbols and parent Frames through the native substrate and
returns graph-supported single-symbol and product interpretations, source macro evidence,
competing readings, unresolved tokens, and the graph query provenance. A
unique supported product is a defeasible selection: the graph may be incomplete.
To use that selection, call `research_formula_model` with the source formula
Evidence node as `claim_id` and its directly linked `context_scope_id`, plus the
usual reviewer and review note. The resulting executable candidate traces to
the context symbols and definitions. Ambiguous or incomplete context returns
without recording a model. A specifically sourced `\NN` macro expanding to
`\mathbb{N}` is also supported; a natural-number minimum must still be supplied
as `domain_assumptions.natural_minimum`. Native execution remains bounded to
signed i64. Function applications and general macro expansion remain unresolved.

## Translate a supplied formula

`research_formula_translate` accepts a formula and emits native Term JSON,
variables, inferred input/result sorts, equality constraints and residual
assumptions. `research_formula_model` translates it and records a model
candidate connected to a sourced claim or formula Evidence node; it also reports
whether the supplied formula appears verbatim in that node's recorded excerpt. Both are available
as CLI operations `formula_translate` and `formula_model` with `--args` JSON.
For example, after ingesting a paper and obtaining a claim ID:

```bash
python -m scripts.ocelot_research_service formula_model --workspace . --args \
  '{"session_id":"SESSION_ID","claim_id":"claim-0001","formula":"x + 1 = 2","reviewer":"researcher","review_note":"Interpret x as an integer."}'
```

Execute the returned candidate with `research_execute` and an environment such
as `{"x": 1}`. For translated formulas, the helper checks input sorts and finite numeric values,
and reports unresolved for zero divisors, non-finite intermediates, and signed-i64
integer overflow. Directly authored native terms do not receive these checks. This check is conservative and may refuse an expression with
an unsafe intermediate even when a Boolean branch would not use it. Floating
calculations use native floating-point semantics, not exact real arithmetic.

The current subset covers finite scalar set membership (such as
`\epsilon,\mu\in\{0,1\}`), Boolean logic; integer and finite decimal literals;
addition, subtraction, multiplication, division, non-negative integer-literal
powers, `abs`, `min`, `max`, and single comparisons. It recognizes common Unicode and LaTeX operators
and `\frac{...}{...}`. `forall(x, D, predicate)` and `exists(x, D, predicate)`
range only over the supplied finite collection `D`, with a bounded evaluation
budget. Finite quantified addition, subtraction and multiplication are checked
conservatively for integer overflow; other quantified arithmetic is refused.
The forms `forall x in D: (predicate)`, `∀ x ∈ D: (predicate)`, and their
existential equivalents are supported. Unbounded quantifiers,
other functions, symbolic sets, dynamic indexing, variable or negative powers,
chained comparisons and unrecognized notation are also refused. Static
subscripts such as `x[2]` and `x_{i}` are mapped to scalar names `x_2` and
`x_i`, not collection indexing; the result records this modelling assumption. The strict formula
front end parses the entire expression; it does not use the broader existing
LaTeX reader as an acceptance test because that reader can discard parts of a
formula. A successful translation is a candidate interpretation, not proof
that it preserves the paper's intended meaning.

Lean export supports Boolean and signed-i64 arithmetic terms, but not division,
floating-point or finite quantifier terms. Integer Lean definitions model native
wrapping while helper execution refuses overflow; a Lean result needs explicit
overflow-free assumptions to match accepted helper executions. The Lean source
is checked only when `research_check_lean` is explicitly called. A successful
check verifies the generated Lean declarations; it does not prove that they
faithfully formalize the paper.

## Local Lean installation

Lean 4.33.1 is installed at `var/tools/lean/lean-4.33.1-linux/bin/lean`
for this checkout; `.venv/bin/lean` and `.venv/bin/lake` link to it. The release archive's SHA-256 is
`890afd185370f85666025b883914ab4f4b339136f8c96167b69cfb62aecaf235`.
`research_check_lean` uses that compiler by default, or the executable named
by `OCELOT_LEAN`, and reports its version, source hash and acceptance status.
The installation is local and gitignored; other checkouts need their own Lean
installation or a configured executable.

The first real-paper sample was rerun after these changes. It is a fixed, small
regression sample, not an accuracy estimate; see the comparative report in
`evaluation/research_assistant/real_papers_20261115_after/RESULTS.md`.

Explicit finite scalar membership, for example `\epsilon,\mu\in\{0,1\}`,
can be translated and executed directly. For `m,n\in\NN` or
`m,n\in\mathbb{N}`, pass `"domain_assumptions":{"natural_minimum":0}`
(or `1`) to `formula_translate` or `formula_model`. The assumption is recorded;
the native model covers only signed-i64 inputs and does not establish that the
paper uses the selected convention. Unknown or paper-specific macros still
require review.

Adjacent letters are not automatically treated as multiplication. For a
source expression such as `E_0=mc^2`, a caller who has reviewed the notation
can pass `"domain_assumptions":{"implicit_products":{"mc":["m","c"]}}`.
The resulting model means `E_0 = m * (c^2)` and records the supplied mapping
as a residual; it does not infer units or establish the physical claim.
