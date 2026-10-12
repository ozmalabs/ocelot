# Finite-key closure scale gate v1.1 — results (2026-09-26)

## Summary

The amended native scale gate passes all **54/54** N × topology × authored-signature × replicate cells. The independent analyzer also passes its 54-case inventory, terminal-state reconstruction, native-status, and bound checks. Each substrate reaches `fixed_point` in three completed passes. This supports the restricted finite-key termination argument across initial graph sizes through 64 and both tested topologies. It is not a general closure theorem or broad runtime result.

## Design and provenance

The matrix crosses N={4,16,64} initial nodes, a directed cycle or dense directed no-self-loop graph, M={1,2,4} authored literal mint signatures, and three freshly constructed native substrates per cell. Each positive edge-match rule performs `add_node_if_absent` with a `Witness{tag:literal}` then inserts an empty-attribute `link` edge. The complete initial graph is supplied before rule installation; the progress budget is 200,000.

The initial v1 capture is preserved at [raw v1](../../../evaluation/reports/mint_termination_scale_v1_20260926.json); all 18 M=4 cells failed an overly strict exact-node oracle. Source inspection showed this was a valid runtime-key equivalence: native `Value::PartialEq` intentionally matches Python semantics, including `Bool(true) == Int(1)`, and `AddNodeIfAbsent` uses that equality for attr subset matching. The static analyzer distinguishes the JSON spellings and counts four syntactic signatures, which safely overestimates actual unique minted nodes in this case. [V1.1 amendment](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_1_AMENDMENT_20260926.md) models the runtime coalescing and keeps the conservative static bound; the captures are not pooled.

V1.1 provenance is in [raw capture](../../../evaluation/reports/mint_termination_scale_v1_1_20260926.json). It records commit, runner/analyzer/prereg/amendment hashes, native binary hash, every graph, native closure report and analyzer result. [Independent analysis](../../../evaluation/reports/mint_termination_scale_v1_1_analysis_20260926.json) hashes the raw, rebuilds expected nodes/edges, and independently recomputes the upper bound. Sources: [runner](../../../scripts/verify_mint_termination_scale_v1_1.py), [analyzer](../../../scripts/analyze_mint_termination_scale_v1_1.py), [preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_PREREG_20260926.md), [v1.1 amendment](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_1_AMENDMENT_20260926.md).

## Bound and native outcome

With E=1 edge type and e₀ initial edge facts, the analyzer bound is `B = M + (N+M)² − e₀`, where M is the number of authored JSON-distinct literal mint signatures. It remains conservative when runtime equality collapses authored signatures.

| N | Initial topology | M authored | Distinct runtime witnesses | e₀ | B | Progress steps | Passes | Final edges |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 4 | cycle | 1 | 1 | 4 | 22 | 2 | 3 | 9 |
| 4 | cycle | 2 | 2 | 4 | 34 | 4 | 3 | 16 |
| 4 | cycle | 4 | 3 | 4 | 64 | 7 | 3 | 25 |
| 4 | dense | 1 | 1 | 12 | 14 | 2 | 3 | 17 |
| 4 | dense | 2 | 2 | 12 | 26 | 4 | 3 | 24 |
| 4 | dense | 4 | 3 | 12 | 56 | 7 | 3 | 33 |
| 16 | cycle | 1 | 1 | 16 | 274 | 2 | 3 | 33 |
| 16 | cycle | 2 | 2 | 16 | 310 | 4 | 3 | 52 |
| 16 | cycle | 4 | 3 | 16 | 388 | 7 | 3 | 73 |
| 16 | dense | 1 | 1 | 240 | 50 | 2 | 3 | 257 |
| 16 | dense | 2 | 2 | 240 | 86 | 4 | 3 | 276 |
| 16 | dense | 4 | 3 | 240 | 164 | 7 | 3 | 297 |
| 64 | cycle | 1 | 1 | 64 | 4,162 | 2 | 3 | 129 |
| 64 | cycle | 2 | 2 | 64 | 4,294 | 4 | 3 | 196 |
| 64 | cycle | 4 | 3 | 64 | 4,564 | 7 | 3 | 265 |
| 64 | dense | 1 | 1 | 4,032 | 194 | 2 | 3 | 4,097 |
| 64 | dense | 2 | 2 | 4,032 | 326 | 4 | 3 | 4,164 |
| 64 | dense | 4 | 3 | 4,032 | 596 | 7 | 3 | 4,233 |

The three replicates in each table row group agree exactly on statuses, counts, bounds and final normalized graph. The complete record preserves each replicate separately.

## Interpretation and limits

The largest exercised dense input has 64 initial nodes and 4,032 initial edges; after closure with four authored rules/signatures it has 68 nodes and 4,233 edges. The largest sparse-cycle bound is much looser because the theorem counts every possible directed typed edge, most of which are unreachable in that fixture. Both are consistent with the finite-graph argument: number of possible facts bounds progress, while actual matcher/pass work is a separate cost question.

This supports native termination and exact finite closure for a single positive rule schema, fixed rule order, literal scalar keys, one edge type, N≤64, and the two tested graph families. It does not test arbitrary rule-body shapes, multiple edge types, variable-count scaling, negative/guarded matches, deletion/replacement, external state, dynamic rule changes, clean-process replication, or CPU/memory costs. It does not establish runtime parser equivalence for every rule form the analyzer admits. No wall-time or general performance claim is made.

## Next gate

Expand the accepted-program matrix with different positive match arities, multiple edge types, multiple rule bodies, and rule-order permutations; compare native output with a separate monotone finite-universe oracle. Add parser/admission adversarial cases, including coercive scalar equality and attributed initial edges. Keep unsupported forms refused by the analyzer and leave unrestricted closure under explicit runtime budgets.
