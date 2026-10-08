# Held-topic area-settlement structural parity v1.1 preregistration

Date: 2026-10-05  
Status: preregistered follow-up to the inconclusive ID-sensitive v1 digest.

## Question and arms

Repeat the global, barrier-area, and live-area full-settlement comparison from v1, with three fresh worker processes per arm and the same seven-turn held-topic workload. Preserve every rule and use the same explicit area assignments. The question is whether arm scheduling preserves graph structure and conversation outputs when node IDs differ.

## Capture and comparison

After every turn, record a raw graph digest and a four-round, ID-independent Weisfeiler–Lehman (WL) digest, plus node and edge counts, replies, and settlement reports. Retain the complete typed node and directed edge records, including IDs, attributes, edge attributes, and multiplicity, at the final turn of every worker in a compressed payload. If an intermediate-turn fingerprint differs across arms, rerun that checkpoint with a compressed snapshot before diagnosing it. This keeps the nine-worker capture bounded while preserving a direct diagnosis path. The WL fingerprint uses node attributes as initial colors and refines colors using incoming/outgoing edge labels and neighboring colors; edge multiplicity is retained.

The WL fingerprint is an ID-independent structural invariant, not a complete graph-isomorphism test. Matching WL fingerprints, node/edge counts, replies, and settlement outcomes supports structural parity but cannot alone rule out non-isomorphic graphs that WL refinement fails to distinguish. The retained snapshots make a follow-up exact labeled-graph comparison possible if needed. Do not describe WL equality as proof of graph isomorphism.

Before interpreting arm results, validate the fingerprint implementation on fixture graphs: same graph with permuted IDs must match; changing one node attribute, edge direction/type/attribute, or edge multiplicity must change the fingerprint. Preserve all v1 outcomes and artifacts.

## Gates

- Source lock stable across capture; nine distinct workers and seven turns each.
- Each per-area settlement call has zero final residual and does not hit its round cap.
- Replies, counts, and WL fingerprints repeat within arms and agree across arms at each turn.
- Task utility remains reported separately; the known copper clarification failure remains a limitation.
- Timings are descriptive. This is full settlement and does not test response-priority deferral or background continuation.

If WL and other invariants disagree, use retained snapshots to identify a minimal structural difference before making a semantic claim. If they agree, report the equivalence level precisely and design an exact comparison for unresolved duplicate-color groups before advancing to a response-priority API experiment.
