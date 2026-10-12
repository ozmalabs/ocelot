# Thoughtexperiment effect-level value attribution v1.2.13 preregistration

## Question

Do bounded effect-level snapshots preserve intermediate graph values within one rule firing, and what incremental runtime and retained-memory costs appear on the existing attribution fixtures?

## Arms and cases

Use the prior v1.2.12 fixture set and four arms: plain closure; endpoint event attribution; exact whole-graph snapshot diff; and combined sparse residual plus endpoint/effect attribution. The current API enables effect-level snapshots together with endpoint event attribution, so there is no separate effect-only arm. The same-event fixture writes one node attribute `0→1→2` and deletes an edge in effect 2. The report-cap fixture exercises cumulative object pressure. Each arm receives the same progress budget and fixture graph; each isolated measurement starts in a fresh process after graph construction.

Run three independent full-matrix workers and three isolated repetitions for each of the direct, same-event, and report-cap fixtures across the four arms (36 isolated processes). Record wall and CPU time, RSS/PSS before and after settlement, event serialization size, endpoint snapshot budgets, and effect snapshot bytes/objects/truncation. Keep source and loaded native binary hashes stable from lock through capture.

## Gates

The analyzer independently replays event endpoint values and checks final graph parity. The same-event case must retain event endpoints `0→2`, effect-index transitions `0→1` and `1→2`, and edge deletion at effect index 2. Combined and event-only event streams must match. Effect bytes and object counts must remain within the declared 4 MiB / 16,384-object report caps, with truncation explicit under the report-cap fixture. Three worker outputs and isolated-arm semantics must replicate. Timings and RSS/PSS are descriptive workload-specific measurements; no universal speed or memory threshold is claimed.

## Claim limit

Passing establishes bounded trace semantics and costs on these authored fixtures. It does not establish causal necessity, useful diagnosis, natural workload frequency, general tractability, or self-improvement. The optimized build uses opt-level 3 with fat LTO disabled and 16 codegen units because the repository default release profile did not finish within the observed build window; record this deviation with the capture.
