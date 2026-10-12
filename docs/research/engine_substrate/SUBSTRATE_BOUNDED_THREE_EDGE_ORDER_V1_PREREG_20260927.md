# Bounded three-edge join-order estimator v1 preregistration

Date: 2026-09-27 local

## Question

How accurately can a capped sample of partial bindings estimate candidate expansion for a three-edge chain, and how often does it select the lowest-work installed order as successful paths become sparse among relation candidates?

## Fixture and factorial

Use `M={16,64}` true chains `a-left-x-middle-y-right-b`. For `D/M={0,4,16}`, add `D` one-sided, disconnected decoy edges to each of the three relation types. Each relation therefore has equal global cardinality `N=M+D`, while only `M` complete paths exist. Trigger and game clauses bind `a,b,g`. The matcher installer can realize four connected path orders; capture all four (`LMR`, `RML`, `LRM`, `RLM`) as exact native controls. Compare sampled estimators with caps `B={8,32,128}` candidate probes per level and three fresh-process replications. This yields 126 workers: 6 graph settings × 7 exact/sample arms × 3 replications.

The estimator starts from the trigger/game binding and simulates candidate access using the matcher’s current rules: source-bound uses outgoing adjacency, target-bound uses incoming adjacency, both-bound still enumerates outgoing adjacency then filters, and fully unbound uses the relation edge list. At each level it samples at most B parent/candidate expansions, extrapolates candidate work and surviving partial-binding count, and scores all four installed orders. A sample arm installs the selected order through the existing count-tie author-order behavior; exact-order arms establish native work for every candidate order. No production matcher code changes are part of this study.

Each worker runs audit-off and audit-on twins. Record installed order, exact candidate tests by rule/edge, sample predictions and selection, planner CPU/wall time, Python allocation peak from a separate repeated diagnostic pass, process peak RSS after plain closure, writer-rule install time, plain closure CPU/wall time, queue work, semantic parity, and source/native identity. The allocation diagnostic reruns the deterministic estimator under `tracemalloc` after closure and is excluded from primary planning and combined time; its own duration is recorded. Combined sample+writer-install+plain-closure wall time is reported separately from closure alone. Graph construction, target-rule installation, process startup, readback, and memory diagnostic are excluded from combined timing; the sampled plan’s full normal calculation across all four candidate orders is charged.

## Gates

- 126 unique fresh-process cells and stable full source/native lock.
- Exact set of M complete outputs; no decoy creates an extra match. Fixed point, zero overshoot, exact `M` enqueues/drains per deferred queue family, correct target effect, deleted trigger, and framebuffer output.
- Plain/audit graph and report parity within every worker; all exact-order and sample arms produce identical final graph for each `(M,D,replicate)`.
- `export_rules()` confirms every requested order was installed exactly; native candidate tests are conserved by writer rule and installed edge.
- Sample costs and selected orders are deterministic for fixed `(M,D,B,replicate)`; compare to all four native exact-order candidate totals without requiring a pass-rate threshold.
- Positive planning/installation/closure timers, positive separate memory-diagnostic duration, and recorded Python allocation/process peak-RSS measures.

## Claim boundary

This is a bounded-sampling diagnostic for one three-edge chain, four reachable connected orders, and synthetic disconnected decoys. It does not establish sample quality for arbitrary joins, task-derived programs, memory scaling, or a general optimizer. Report selection accuracy, prediction error, regret, and planning cost even if the estimator fails on low budgets; do not hide missed rare matches.
