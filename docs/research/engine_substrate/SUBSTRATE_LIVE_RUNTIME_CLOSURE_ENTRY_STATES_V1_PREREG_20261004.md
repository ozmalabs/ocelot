# Live runtime closure-entry states v1 preregistration

## Question

Do exact primary graph/rule states captured immediately before each native `run_rules` call provide enough information to reproduce the live per-rule work totals for the selected two-request route?

## Method

Reuse the locked v1.6 replicate-0, audit-on worker. At each request boundary, wrap only that adapter's serialized native-facade `run_rules` method. Before every call, export the current complete graph and rule table, canonicalize and hash the pair, and write one compressed payload per unique state. Record every call in order with its payload reference and exact progress cap. Delegate to the original facade method unchanged. Restore the facade method after each request. Preserve parent task, reply, graph-digest, and behavioral-counter parity gates.

In the replay phase, restore every captured call-entry graph/rule state independently using match-order-preserving rule installation, run the same progress cap once, and collect native per-rule counters. Aggregate by local rule index and compare with the parent request's per-rule totals for primary store ID 1. The state sequence itself represents intervening mutations: replay each call from its own recorded entry state, then sum costs without chaining replay outputs.

## Acceptance and interpretation

Require source-lock stability, nonempty call coverage for both requests, exact graph and semantic rule round-trip for every state, and parent route parity. Report exact replay parity separately for per-rule candidate tests, Term evaluations, rule enumerations, and the full metric-cell set. A mismatch is retained as evidence and attributed by slot/metric; it cannot be called successful replay. This captures Python-facade `run_rules` entries on the primary adapter. Native secondary/free-standing stores remain covered only by v1.2 state snapshots and the v1.1 fixed-point diagnostic.

## Scope

This is one authored route and one replicate. It measures whether primary store call-entry states explain the observed primary work; it does not establish general tractability or natural workload frequency.
