# Exact inference under a shared separator: proposition and evidence

## Proposition

Let variables be partitioned into a shared boundary `B` and disjoint frame interiors `I₁,…,I_F`. Assume:

1. each variable has a finite domain of size at most `d`;
2. the objective decomposes as `E(b,i₁,…,i_F) = φ_B(b) + Σ_f φ_f(b,i_f)`;
3. no factor couples private variables from different interiors;
4. each interior has at most `m` variables and its local objective can be evaluated in at most `q` factor/term operations per assignment (with bounded factor representation and access cost).

Then an exact global MAP state can be found by enumerating each boundary assignment and independently minimizing each frame conditional on that assignment:

`min_b [ φ_B(b) + Σ_f min_{i_f} φ_f(b,i_f) ]`.

For uniform bounds, a direct exhaustive implementation takes

`O(d^k [q_B + F·d^m·(m+q) + F·m])`

factor/assignment operations, where `k=|B|` and `q_B` bounds evaluation of boundary-only terms. With fixed `d`, `m`, and local factor-work bound `q`, this is `O(F·d^k)` as the number of frames grows. For pairwise dense local factors, `q=O(m(k+m))`; thus the simpler `O(F·d^k)` conclusion additionally requires bounded `k` and `m`. The direct implementation stores at most the input model plus a candidate/argmin assignment of `O(k+Fm)` variables; a table-based message implementation has different memory constants and should be counted separately.

The result does **not** follow from a bounded separator alone. Large interiors, dense or high-arity local factors, or cross-frame factors can restore exponential work. For a general exact junction tree with maximum bag scope `w+1`, the familiar bound is exponential in `w` (roughly `O(M·d^{w+1})` time for `M` bags, with memory tied to stored bag/message tables), not in boundary size alone.

## Proof sketch

Fix any boundary assignment `b`. By the factorization assumption, the remaining objective is a sum of terms whose private variables belong to exactly one `I_f`. Therefore minimizing each `φ_f(b,·)` independently and adding `φ_B(b)` yields the exact minimum conditional on `b`. Enumerating every `b∈D^B` includes the boundary part of every global assignment; selecting the best conditional solution therefore gives the global MAP. The operation bound counts at most `d^k` boundaries, `d^m` local assignments per frame per boundary, bounded local evaluation work, and boundary/frame result assembly. The exponential dependence is explicit in `k+m` and domain size; linearity in `F` is conditional on bounded per-frame work.

## Current-source replay

The [locked replay protocol](SUBSTRATE_CAN_SEPARATOR_FACTORIZATION_REPLAY_PREREG_20260926.md) reruns the existing 96-model grid in three fresh processes: `F∈{2,4,8}`, `m∈{2,4}`, `k∈{0,1,2,3}`, and `d∈{2,3}`. This yields 288 captures, six timings per structural configuration (two deterministic model draws × three processes), and three timings per fixed seeded model.

The independent analyzer passes all ten checks: current source/native provenance, all model extraction checks, exact global-junction-tree versus conditional-frame MAP agreement, the width identity `k+m−1` (or `m−1` for disconnected `k=0` frames), exact boundary/local assignment counts, and independently reconstructed factor-touch counts. For `m=4,d=3,k=1`, conditional local-assignment work and median conditional time scale with `F=2/4/8` as `486/972/1,944` and `7.26/15.05/30.23 ms`. At `k=3`, they scale as `4,374/8,748/17,496` and `74.36/149.01/311.70 ms`. This is consistent with the proposition's linear-in-frame-count behavior at fixed local dimensions and its exponential boundary cost.

## Implementation boundary

Both exact algorithms in this replay are Python-side inference routines. Native graph storage is used to build and extract the factor models; the replay does not show that the substrate discovers separators, maintains a frame hierarchy, or schedules native rule closure with separator messages. The frames and shared separator are constructed by the experiment. This proposition is a tractability result for a specified model decomposition and algorithm, not yet an end-to-end substrate theorem.

Evidence artifacts: [runner](../../../scripts/substrate_can_separator_factorization_replay_v1.py), [independent analyzer](../../../scripts/analyze_substrate_can_separator_factorization_replay_v1.py), [lock](../../../evaluation/substrate_capability/can_separator_factorization_replay_v1_lock_20260926.json), [raw capture](../../../evaluation/reports/can_separator_factorization_replay_v1_20260926.json), and [analysis](../../../evaluation/reports/can_separator_factorization_replay_v1_analysis_20260926.json). The earlier exploratory result remains at [`SUBSTRATE_CAN_SEPARATOR_FACTORIZATION_RESULTS.md`](SUBSTRATE_CAN_SEPARATOR_FACTORIZATION_RESULTS.md).

## Next proof obligations

- Establish frame assignment and boundary-factor completeness against independently traced reads/writes, including dynamic term reads.
- Repeat the exact comparison on cuts discovered from loaded runtime task graphs, not only cuts supplied by construction.
- Account for frame discovery, updates, message exchange, native allocations, and invalidation under mutation.
- Extend the single-separator identity to a tree hierarchy by charging each bag/message table at its actual scope; bounded boundary size without bounded interior/treewidth is insufficient.
