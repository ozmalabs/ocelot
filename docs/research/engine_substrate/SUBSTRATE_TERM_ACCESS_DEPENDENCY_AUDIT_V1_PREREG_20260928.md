# Term access-dependency audit v1 preregistration

Date: 2026-09-28
Status: preregistered before expanding conservative Term dependency declarations

## Question

After the ShapeDecode repair, do the Term variants that read graph state directly or through dynamic helpers have a sound declared dependency in `RewriteRule::derive_access()`? What is the operation-count cost of making identified dynamic readers conservative on the accepted two-prompt workload?

## Source-driven candidates

The source review follows `TermNode` evaluation arms and helper calls that receive `EvalCtx` or `TypedGraph`:

- **Finite-key reads:** `ParetoDominates` reads `value_edge`, `measure_edge`, `dimension_key`, `verified_key`, and `signed_value_key` directly in `eval_pareto_dominates`; declare these two edge and three attribute resources and recurse into the Term children.
- **Dynamic graph reads:** ShapeDecode-family helpers (ShapeDecode, TransformDecode, DimInfer, GenInfer, RatioInduce, TimeInfer, DepthInfer, BlinkBridge, GapAbduce, GapVerify, SupportInfer, TransferDecode, RecogniseShape, MetaShapeMint) scan codebook, cue, registry, mechanism, or observation nodes; declare `reads_any` until precise footprints exist.
- **Dynamic graph/reentrant paths:** `Join` can render Node values through graph-resident render rules; `ProgEval` can resolve a Node-backed program subgraph; `Call` evaluates a runtime-derived body not represented in its child walk; `Holds` evaluates a concept definition selected through `ConceptResolver`; and `UseTool` dispatches to an arbitrary registered handler. Conservatively mark these readers `reads_any`, while retaining their explicit child dependencies.

This is a targeted source review, not an exhaustive proof over all 237 Term variants. Each candidate is checked against its evaluator/helper implementation before the edit. Terms whose state is external to the substrate graph (for example `ReadFile`) remain a separate dependency-modeling gap and are not made graph wildcards by this protocol.

## Change and frozen replay

Apply only the listed `collect_term_reads()` changes. Rebuild and record the native extension. Replay the two prompts and seed construction from reconciliation v1.2 in three fresh workers; use v1.2 raw/lock as the immediate baseline and the accepted proposal-panel capture for task semantics. Do not alter prompts, seeds, runtime trace mapping, or task logic.

## Measurements and gates

1. Source record shows each listed evaluator's actual dynamic/finite graph dependency and the matching `collect_term_reads()` branch.
2. Three PIDs, stable source locks, zero trace drops, exact corrected trace parity among workers, and task/semantic parity to baseline.
3. The foreign-substrate isolation control still returns zero rows without panic.
4. Independent static-key analysis has no unexplained mismatches. Explicit finite-key `ParetoDominates` events must map to its declared keys; wildcard Terms may match any graph resource.
5. Compare aggregate `rule_enumerations`, candidate tests/pairs, Term evaluations/units, and per-prompt event counts against v1.2. Wall time is descriptive only. A changed count is not automatically a regression; report the exact delta and which newly wildcard terms were observed.

## Claim boundary

This audit covers source-identified dependency paths and one authored prompt pair. It does not prove every Term variant or external dependency is modeled, nor establish scheduler completeness, locality prevalence, or general tractability. Remaining source families must be selected from a generated crosswalk of enum variants, evaluator arms, helper calls, and runtime trace kinds.
