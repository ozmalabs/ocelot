# Describe faculty first use and reuse v1 preregistration (2026-09-27)

## Question

How much of the live `describe what you see` request cost is paid while lazily constructing describe faculty, and how does that compare with cached calls and explicit preconstruction? Does moving construction earlier preserve the same observable capability?

## Design

Use fresh full-seed processes and the established three-percept scene fixture. Run three replicates in each of two arms, in alternating arm order:

- **lazy:** time two sequential identical requests; the first request reaches `_ensure_describe` with an empty cache and the second reuses the resulting faculty.
- **prebuilt:** explicitly call `_ensure_describe` after seed boot and scene attachment, recording its wall/CPU time; then time two identical requests against the warm faculty.

Measure boot, faculty construction where separately exposed, each request wall and process CPU, current RSS at phase boundaries, and peak RSS. The runner records native rule counts before and after construction and each request, but enables no access trace, scale audit, or graph readback in the measured intervals. It then checks both public replies and request-bound Goal lifecycle evidence. Source and native inputs are hashed before and after each worker. Keep all six workers in the report, including failures or lock drift.

## Interpretation and limits

This is a controlled route-level decomposition, not a natural-task frequency estimate, causal ablation, or scaling curve. The two arms have the same total work if explicit preconstruction succeeds; the comparison tests when cost is paid and whether the cache changes request behavior. Identical prompts test reuse, not transfer to an independent task family. Python-level wall/CPU measurements include normal adapter work. Rule-count reads are the only added instrumentation during measured phases.

## Gates

- Six unique fresh processes, three per arm, with identical source locks and no lock drift.
- Every worker boots the full seed profile and attaches the same fixture.
- Each worker completes two expected replies; each inbound has exactly one resolved Goal with selection, execution, and action-result events.
- Lazy arm constructs faculty on the first request and adds no faculty rules on request two; prebuilt arm constructs before request one and adds no faculty rules on either request.
- Report every replicate and per-arm median/range for boot, faculty setup, request wall/CPU, current RSS, and peak RSS. A failed gate censors capability claims but remains reported.

## Artifacts

Runner, source lock, raw report, analyzer, and results document are recorded alongside this preregistration after execution.
