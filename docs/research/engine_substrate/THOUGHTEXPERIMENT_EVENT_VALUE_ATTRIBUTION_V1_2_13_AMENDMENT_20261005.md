# Thoughtexperiment event value attribution v1.2.13 amendment

## Change

Rule-write attribution now optionally retains value transitions at each authored effect boundary. An event-level snapshot still gives the first before-image and final after-image for the whole rule firing; `effect_snapshots` adds the indexed intermediate transitions. This distinguishes a firing that writes `0→1→2` from one that writes `0→2`, and preserves the effect index for each transition. Node additions/removals and edge additions/removals use `null` for an absent side.

Per-effect snapshots are opt-in through the existing thoughtexperiment event-attribution journal. They have independent cumulative caps of 4 MiB and 16,384 changed objects per report, plus 64 KiB and 512 objects per rule event. Truncation is reported through the aggregate `rule_write_effect_snapshots_truncated` counter and each effect's `values_truncated` flag. These limits bound retained snapshots; they do not cap all temporary work or establish a latency bound.

## Verification and limits

`cargo check --lib` passed. A focused Python/native smoke fixture wrote one node attribute twice and then deleted an edge. The event snapshot reported `0→2`; effect indices 0 and 1 reported `0→1` and `1→2`; effect index 2 recorded the edge removal. The report retained 128 estimated payload bytes and three objects with zero truncation. This checks API wiring and transition semantics on one small fixture only.

The initial implementation made effect tracing follow event attribution. The [v1.2.13 source-locked capture](THOUGHTEXPERIMENT_EVENT_EFFECT_COST_V1_RESULTS_20261005.md) then measured the combined event/effect observer and exposed substantial added cost on a deliberate high-fan-out case. The API has since been changed so endpoint attribution and effect-value tracing are separate opt-ins; the ordinary endpoint observer retains zero effect payload. The follow-up cost capture measures the separate modes. Its build is optimized (`opt-level=3`) but uses LTO disabled and 16 codegen units, rather than the repository default fat LTO / one codegen unit.

This extends observability for thoughtexperiment diagnosis. It does not make hypothesis induction cheaper, prove that a residual was caused by a specific effect, or demonstrate self-improvement.
