# Scoped/full closure parity with distinct writes and dependent rules v2 preregistration

Date: 2026-10-01

## Question

Does the scoped all-binding drain repair preserve exact full-closure results when each join binding writes to a distinct graph target and those writes enable a separate active rule?

## Design

Repeat the source-locked `R={1,8,32}`, `M={1,4,16}`, three fresh-process factorial from v1. Keep all five deferred queue families. Add one verifier rule before the writer rules. The verifier matches `anchor --handled_mid--> middle` and writes `middle --verified_by--> anchor`. Each writer binding emits its own `handled_mid` edge for a distinct middle node; this gives the second rule R×M independent activations. The writer trigger remains shared per writer and is deleted after the binding snapshot is collected. Compare direct full closure, scoped-only closure, and scoped closure followed by global fallback on independently built identical graphs. Capture operation-work traces and scale counters separately per phase.

The Microtheory directly owns each anchor, so every writer/verifier binding touches an owned node. Verifier rules are installed first, before any writer, to require a later settlement iteration after writer mutations. Full versus scoped-plus-fallback exact graph equality remains the primary oracle; the distinct verifier-edge count additionally checks that every join binding's write is consumed.

## Expected invariants

- Direct full and scoped-plus-fallback reports settle at fixed point and produce byte-for-byte equal final graph dictionaries.
- Both settled arms contain exactly `R×M` `handled_mid` edges and `R×M` `verified_by` edges; they contain `R` target `seen_i` edges, `4R` framebuffer cells, and no trigger edges.
- Scoped-only reports deferred effects pending and is not considered settled. It may already contain `R×M` verified edges because graph-local dependent rules can settle while deferred effects remain pending.
- Queue enqueue/drain totals remain identical to v1: RulePatch is R through shared-patch deduplication; other four families are R×M. Scoped-only drains none; fallback drains the queued items.
- Per-phase operation-work queue rows exactly reconcile to scale-audit counters, with zero dropped rows.
- The 27-worker lock is stable before and after all workers.

## Limits

This adds distinct graph writes and one simple dependent rule family, but does not establish arbitrary inter-rule scheduling equivalence, rules whose writes alter later bindings in the same drain, projection-key equivalence, cross-frame scope completeness, or natural-task prevalence. It measures semantic parity, not a general complexity bound.
