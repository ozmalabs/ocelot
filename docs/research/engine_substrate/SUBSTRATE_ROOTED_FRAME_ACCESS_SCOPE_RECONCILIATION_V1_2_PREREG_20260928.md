# Rooted-frame access-scope reconciliation v1.2 preregistration

Date: 2026-09-28
Status: preregistered before the ShapeDecode static-access repair replay

## Hypothesis and source change

Corrected v1.1 tracing isolates one substrate and reveals `sd_decode` runtime reads of codebook attributes and types that are absent from its finite static keys. Source inspection identifies the cause: `collect_term_reads()` conservatively marks graph-delegating Terms such as `TransformDecode`, `DimInfer`, and `GenInfer` as `reads_any`, but omits `ShapeDecode`. This amendment adds `ShapeDecode` to that existing wildcard-reader group. The change must not affect matching or mutation semantics; it may conservatively wake more rules during fixed-point execution.

## Frozen workload and baseline

Replay the same prompts and seed construction from rooted-frame access reconciliation v1.1, using its raw capture and lock as the immediate baseline and the accepted rooted-frame proposal panel v1.1 capture as the semantic/task baseline. Preserve the v1.1 trace-isolation positive/negative controls. Do not edit prompts, seed data, access-event mapping, or analysis formulas.

## Registered analyses

1. **Build and provenance:** release extension and build record correspond to the modified Rust source; all worker and post-run locks are stable.
2. **Task parity:** each replicate preserves the semantic graph digest, reply presence, route, and goal count from both accepted captures.
3. **Trace integrity:** three fresh PIDs, exact corrected trace parity among the three workers, zero dropped events, and weighted counts equal row-count sums. Traces need not equal v1.1 if conservative rule wake-ups change event multiplicity.
4. **Static access concordance:** independently analyze all observed trace events. The expected result is that every `sd_decode` ShapeDecode-derived attribute/type/index read is covered by `reads_any`; any remaining finite-key mismatch is reported and source-audited, not suppressed.
5. **Scope isolation:** tracing an empty substrate during a distinct populated substrate's request yields zero captured rows and zero drops without panic.

## Integrity gates and claim boundary

All five registered analyses must pass except that unexplained mismatches are recorded as an unresolved result, not an integrity-gate failure. This single-rule metadata repair and two-prompt replay do not establish complete static dependencies for every Term, trace completeness, general frame locality, scale, or a tractability theorem. Next audit all specialized graph-reading Terms against `collect_term_reads()` and direct helper traces before using these access sets for partition claims.
