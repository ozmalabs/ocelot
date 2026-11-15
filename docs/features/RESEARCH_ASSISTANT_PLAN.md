# Ocelot research assistant: implementation plan

**Status:** v0 implemented; comparative held-out evaluation remains open (2026-11-14). See [usage and limits](RESEARCH_ASSISTANT.md) and the [exploratory pilot](../../evaluation/research_assistant/pilot_20261114/RUN.md). Intended users are researchers using an
existing LLM assistant to investigate a question, including questions about
GE and Ocelot themselves. The first deliverable is a local, inspectable
research helper with CLI and MCP interfaces; it is not an autonomous scientist.

## Goal and motivation

Make a research thread resumable and auditable across LLM sessions: locate
primary evidence, state the frame and assumptions, connect claims to evidence
and counterevidence, design discriminating checks, and carry a result through
preregistration, execution receipts and a scoped report. The LLM proposes and
interprets; the helper maintains explicit structure, checks mechanical
invariants, and makes missing evidence and unresolved decisions visible.

This extends the direction of [dev memory](DEV_MEMORY_MCP.md) and
[dev sessions](DEV_SESSION.md) from code changes to research. Those tools are
currently development-side snapshots and receipt graphs, not the agent runtime;
the session interface has not yet been integrated into MCP. Neither is an
existing scientific claim/evidence system. Reuse their interfaces and
persistence patterns where appropriate, not their development-specific state
machine. [Doing Science Research](../SCIENCE_RESEARCH.md) supplies Ocelot's
experimental rules. The sibling GE project's
`notes/GRAPHIC_EQUALISATION_FOR_LLMS.md` supplies the frame/state/rules/grammar
ledger and cautions against treating groundings as substrate theorems; its
`notes/experiments/ge_oracle_elimination/` archive demonstrates claim-evidence
mapping, independent checks, negative findings and reproducible provenance.
Those are inputs to a design, not evidence that this helper improves research.

## Concrete user experience

A researcher asks an assistant: “Does a total single-valued Boolean extension
make a residual CNF easier to solve?” The assistant calls `research_context`
with the question and configured GE and Ocelot roots. The helper returns
source-located excerpts, prior claims and counterexamples, source revision and
freshness, and an explicit incomplete GE ledger. The assistant reads the
sources, adds a bounded claim and competing hypothesis, and links a cited
hard-residual construction as counterevidence to the broad claim. It proposes a
small independent check and records its limitations. The helper shows which
claims lack source locators, which checks were actually run, and which broader
claims remain open. A report export distinguishes a mathematical argument from
a finite execution and does not convert a passing check into a proof.

For empirical Ocelot work, the same interface additionally tracks a prospective
preregistration, controls, seed claim, engine provenance and run receipts under
the applicable repository protocol. Exploratory investigations can start
without a preregistration; they must be labelled exploratory. Do not require
empirical RNG or power fields for a deductive or qualitative investigation
where they are inapplicable: record the reason and applicable checks instead.

## Research graph and evidence contract

Use a versioned, JSON-serializable, typed research graph, with stable IDs and
append-only events. Each investigation has a question and one or more frames;
each frame may record boundary, state `g`, rules `r`, grammar `Γ`, possible
continuations, realised event, residual, cost, grounding and a discriminating
test. Fields may be `unknown` or `not_applicable` with reasons. This is a
working representation supplied or reviewed by the researcher, not automatic
proof that the theory applies. Distinguish material outside the frame from
material admitted and rejected; capability from reachability; and source
claims from the assistant's inferences.

Minimum node and edge vocabulary:

- `Question`, `Frame`, `Claim`, `Assumption`, `Source`, `Evidence`,
  `Alternative`, `Prediction`, `Protocol`, `Run`, `Observation`, `Decision`
  and `Report`; edges include `scoped_by`, `assumes`, `supports`, `opposes`,
  `derived_from`, `tests`, `produced`, `supersedes` and `cites`.
- A claim records its exact wording, scope, claim type (definition, theorem,
  empirical observation, hypothesis or inference), author/provenance, status
  (open, supported within scope, contradicted, superseded or unresolved),
  limitations and relevant assumptions. Status is a signed-off assessment,
  not a score automatically computed from graph links.
- A source locator records repository identity, revision, path, line/section
  or other stable locator, and a content hash of the referenced material.
  Record external source identifiers and access date when supplied; do not
  silently fetch or assume a moving URL is immutable. Source-backed excerpts
  must be distinguishable from generated summaries. On revision/hash mismatch,
  show stale or unavailable, preserving the historical citation.
- A run receipt records protocol version, source and dirty-tree state, exact
  command/selector, environment and dependencies, seeds if relevant, start/end,
  exit status, artifact paths and hashes, and Ocelot engine provenance when
  applicable. A manually entered receipt is an assertion, not proof of execution;
  distinguish captured execution from manual entry. Keep failed runs and nulls.
- The graph represents dependencies and disagreements; it does not infer truth
  from citations, count votes, or silently promote evidence to a theorem.
  Corrections append a superseding event, retaining prior state and rationale.

## Interfaces and boundaries

Implement a standalone `scripts/ocelot_research.py` domain layer with a thin
CLI and `scripts/ocelot_research_mcp.py` wrapper, using JSON requests/results.
Proposed operations (same names with `research_` prefix over MCP):

| Operation | Contract |
| --- | --- |
| `init` | Create investigation with question, roots and investigation mode. |
| `context` | Return bounded, cited research context, conflicts, missing fields and snapshot freshness. |
| `record` | Validate and append typed claim, frame, evidence, protocol, observation or decision events. |
| `link` | Add a typed, provenance-bearing edge; reject unknown IDs and invalid types. |
| `inspect` | Traverse claim → assumptions, support, opposition, runs and source locators. |
| `check` | Report mechanical completeness, stale citations, missing controls and protocol-specific blockers with reasons; never certify truth. |
| `export` | Produce a Markdown claim/evidence ledger and machine-readable bundle, including unresolved items and provenance. |

Reuse dev-memory search and `GraphInterrogator` for local structural lookup when
available, with explicit multi-root configuration and per-root indexes; the
current builder's default scope does not index the GE sibling or the full
research archive. Initially index explicit selected files and their headings,
links and locators; include the GE entry point, selected claim-evidence ledger,
Ocelot science guide and one prereg/results pair. Do not imply links extracted
from prose are validated support relations. Expand indexing only after retrieval
quality and cost are measured. Both repositories may be dirty: capture commit
and per-file hashes, and surface uncommitted content. Resolve paths against
explicit roots, prevent traversal/symlink escape and use read-only access to
source roots. Keep session artifacts under the configured writable workspace,
not in the sibling repository by default.

The v0 helper does not call an LLM, execute commands, access the network, edit
papers, or publish. The existing agent and its permission model handle those
operations; the helper records their results. A later captured-run adapter may
execute an explicitly supplied, allowlisted local command only after a separate
design and review. No claim that dev-memory's snapshot graph or JSON session
is already execution by the native Ocelot substrate: v0 uses the existing
inspectable graph tooling and is evaluated as such.

## Workflow and gates

1. **Orient:** create a question and frame; retrieve primary sources and record
   unavailable or stale material. Record competing explanations and what would
   distinguish them. The assistant must be able to leave fields unknown.
2. **Bound claims:** link each proposed claim to assumptions, exact source
   locations and evidence for and against. Flag unsupported inferences and
   missing counterevidence as prompts for review, not failures of truth.
3. **Design:** choose deductive, empirical or exploratory mode. For a
   confirmatory Ocelot experiment, check the applicable preregistration
   requirements in `SCIENCE_RESEARCH.md` and `VISION_PROTOCOL.md`: hypothesis,
   readout, justified sample size, independent unit, seed allocation, controls,
   decision rule and fixed analysis. Require an immutable prereg revision before
   classifying the run as confirmatory; amendments and deviations remain visible.
   For finite mathematical checks, require domain/bounds, oracle independence
   and explicit distinction between verification and proof.
4. **Observe:** record exact results, provenance, failed controls and deviations.
   Unavailable engine or unverified receipt cannot appear as a validated run.
5. **Assess and export:** a researcher records the interpretation and its
   scope, including unresolved alternatives, negative results and next tests.
   Export links back to source and run artifacts; no generated conclusion is
   silently treated as an accepted result.

These gates constrain the helper's *labels and reports*, not the user's freedom
to explore. Missing information returns a reason and a next action. A newly
recorded document cannot retroactively become a preregistration for a run.

## Delivery and acceptance

1. **Schema and vertical slice.** Add `scripts/ocelot_research.py`, a versioned
   schema and fixtures; implement init/record/link/inspect/check/export, atomic
   persistence, stable IDs, reload and revision events. Build the Boolean
   extension example using small synthetic fixtures and selected real GE source
   locators. Test contradictory evidence, missing fields, stale locators,
   supersession, invalid edges and replay. Exit: a new assistant can reconstruct
   the bounded claim and its unresolved alternatives from the exported bundle.
2. **Source discovery.** Add explicit root manifests and a small reproducible
   index; reuse dev-memory where its assumptions fit. Return citations, reasons,
   coverage and freshness, with no fabricated support edges. Test two roots,
   dirty sources, moved/missing files and path escapes. Exit: known relevant
   passages are returned and each locator can be reopened at its recorded hash.
3. **Science workflow.** Add protocol-specific checklists and immutable prereg
   references, run receipts, engine/seed provenance adapters and honest
   exploratory labels. Reuse existing seed/provenance tools as read-only checks;
   do not replace them. Test stale engine, reused seed verdict, post-run prereg,
   missing control, failed run and a non-empirical exemption. Exit: a historical
   prereg → run → results example exports with all caveats intact.
4. **Agent integration.** Add CLI and MCP wrappers and a concise operating guide;
   use the dev-memory server's transport patterns without assuming session MCP
   integration exists. Test protocol framing and end-to-end reload from a fresh
   process. Exit: an ordinary MCP client can orient, inspect, record and export
   without granting execution or write access to the source repositories.
5. **Prospective evaluation.** Before claiming benefit, freeze a mixed task set
   and scoring rubric with source-grounded answer keys and deliberately planted
   contradictions. Compare the same model and source access with helper off/on,
   including a source-access-only control, randomized task order, independent
   blinded scoring, fixed budget and predeclared analysis. Measure claim/source
   accuracy, contradiction and limitation recall, unsupported assertions,
   reproducibility of citations, task completion, tokens and elapsed time;
   report failures and overhead. Use a pilot to size a separate held-out test,
   not a retrospective success threshold. Record actual model, prompts, seeds
   where available and provider nondeterminism. A null or worse result stops
   claims of benefit and guides revision.

## Open decisions and later substrate research

- Start with human/LLM-authored typed relationships; automated extraction may
  propose candidates later, with provenance and explicit review.
- Single-writer sessions are acceptable for the first slice. Add optimistic
  version checks and locking before concurrent writers; atomic rename alone
  does not prevent lost updates.
- Treat the schema and adapters as a testable operationalisation of the GE
  ledger, not a proof of GE or an assertion that every research problem fits it.
  Compare against a generic claim/evidence ledger and an unstructured notes
  baseline before attributing any gain to GE-specific fields.
- A later, separately evaluated stage can map the research graph and workflow
  to native substrate rules, testing whether those rules are load-bearing via
  ablation and checking execution provenance. Keep any LLM proposer distinct
  from the substrate evaluator and independent external oracles; finite native
  checks do not establish universal mathematical results.
