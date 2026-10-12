# Order-sensitive scoped/full continuation v3 preregistration

Date: 2026-10-01

## Question

Do the edge insertion-order differences found in v2 change a downstream rule result, or are they only a serialization difference for this workload?

## Design

Repeat the same locked R×M five-queue, distinct-write, dependent-verifier factorial. Add one shared sink owned by the Microtheory and connect every writer anchor to it. After the writer and verifier rules, install an order-sensitive rule matching each `anchor --handled_mid--> middle` plus `anchor --has_sink--> sink` pair, guarded by `Not(Eq(Attr(sink, "probe_done"), true))`. Its effects write the matched `middle` NodeID into the shared sink's `selected_mid` attribute and set `probe_done=true`. Binding collection snapshots all admissible matches before effects, so every binding in the first firing is applied; the marker then prevents repeat firings on subsequent scheduler passes. The final selected NodeID reflects matcher binding order without causing an endless oscillating rule. Capture the sink's final attribute in each arm and compare direct full with scoped-plus-fallback. The probe rule runs within the closure, so it observes each arm's actual edge/index order.

Retain the v2 exact graph wire comparison and all prior semantic/queue gates. Also compare the order-sensitive `selected_mid` value across settled arms; a mismatch is direct evidence that insertion order changes observable continuation state. Three fresh-process replicates per R×M cell.

## Expected invariants

- Existing distinct handled/verified edges and five-queue totals remain correct.
- Full and scoped-plus-fallback reach fixed point.
- If edge ordering has no operational effect for this scoped rule, both settled arms select the same `selected_mid` for every cell; if any differ, retain the mismatch and report the order as observable.
- The raw trace and source/native lock are stable; no sorting or canonicalization is used in the runtime probe.

## Limits

The shared-sink last-match rule is intentionally order-sensitive and adversarial. A mismatch demonstrates order observability, not that ordinary workloads depend on it. A match does not prove order is irrelevant for all consumers or rule shapes. The fixture remains synthetic and does not estimate natural frequency.
