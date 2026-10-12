# Vision settling single-sweep structural scale probe v1 preregistration

Date: 2026-09-27

## Question

On full, single-sheet runtime graphs, how do one batched `st_settle` application's matcher and Term-evaluation counts grow with sheet size, and how much global-factor dependency crosses a fixed row-frame partition? Does a root-scoped equivalent preserve the one-sweep outputs while changing the measured work?

This is an independently sourced vision workload, contrasting with the conversation task projection. It measures one rule application, not fixpoint settling or a task-quality outcome.

## Workload and protocol

Build a complete degenerate-channel `settle_lib.build_sheet` Retina sheet for each `n_side` in `{3,8,10}` and seeds `{11,29,47}`. The size set is capped by `settle_lib.lattice_centres`' maximum valid anatomy (16×16 retina, RF 7); a rejected n=12 diagnostic attempt is documented in the v1.1 amendment. Run paired arms using the authored global `NodesOfType(SUnit)` fold and a cloned rule whose two SUnit fold sources are changed to the matched Retina root's `has_sunit` members. Keep all other graph state and rule effects identical. Remove every rule except `st_settle` and `st_commit`; apply only `st_settle` once using the native whole-binding-set `apply_rule_batch` entry point. (`apply_rule_once` is intentionally single-binding and is not used.) Initialize an identical deterministic afferent/activity state within each pair and force an `act_next` write with a negative sentinel.

For every arm, record full graph sizes, root membership, exact `act_next` vector, one instrumented application's per-rule/per-clause/global scale counters, and five audit-disabled one-application timings. Confirm the rule is batched and the only two retained rules are the expected settle and commit rules. The timing is one native batch application after graph setup; it excludes boot, graph construction, commit, and multi-sweep settling.

The seed contains two `NodesOfType(SUnit)` folds in the settle effect and one `NodesOfType(SettleParams)` lookup per matched unit. Therefore the independently predicted global-fold `NodesOfType` work units are `2N² + N` in the global arm and `N` in the root-scoped arm; the one-per-unit rule matcher should report N candidate tests. Root scoping is not predicted to reduce within-sheet all-to-all dependence: the matched root still owns all N units. It only makes the population choice explicit and avoids graph-global inclusion of other sheets.

Define a declared spatial partition by contiguous row blocks over the builder's row-major unit sequence, with one lattice row per frame. Verify each frame contains `n_side` units. For the global fold, independently calculate the exact number of directed output/input dependencies crossing these row frames, `N*(N-n_side)` for `N=n_side^2`; record local-neighbor graph edges crossing the same partition separately. These row frames are measurement-defined and are not learned substrate frames.

Run three fresh worker processes. Lock protocol, runner, analyzer, relevant Python source closure, seed manifest, native source/build/extension hashes, and engine provenance before capture. Require identical semantic output/counter structures for equal `(n_side, seed, arm)` across workers, exact paired output parity, complete root membership, the expected counter attribution to `st_settle`, and stable source fingerprints through all workers.

## Interpretation boundary

This probes a single-sheet authored global competition rule. A quadratic global-fold access count is evidence against assuming spatial row frames are cheap cuts for this operation; it is not a substrate-wide complexity result. Root-scoped parity on one sweep does not establish full fixed-point, orientation-task, or learning equivalence. One-rule application timing is not end-to-end task latency. No natural-task prevalence or learned-frame performance is estimated.


## Replication amendment

The v1 capture retained identical semantic outputs and integer operation counts across workers, but its exact full-snapshot repeatability check failed because `deferred_queue:fb_samples:drain_ns` differs between runs. This field is elapsed time, not an operation count. V1.1 keeps each timing sample in the raw record and excludes only global counter keys ending in `_ns` from structural counter equality; all per-rule/per-clause counts and all other global counters must still repeat exactly. The anatomy-size correction and its rejected n=12 diagnostic are documented in the separate size amendment.


## Trace extension

V1.2 adds the default-off native runtime access trace around the instrumented batch application. It aggregates only `term_edge_read` and `term_type_read` counts by rule resource, retains no concrete graph IDs, and requires zero dropped events. Independently enumerate graph edge-type totals and check `Neighbours` traversal events: `sunit_neighbour` is visited twice per directed local edge (fold plus denominator), and the root-scoped arm visits `has_sunit` twice per ordered root-member pair (fold plus denominator). In the global arm, the two SUnit type-index folds must each return N items per binding; the existing term-unit counter predicts `2N²+N` total `NodesOfType` items including the `SettleParams` lookup. Timings are collected only with tracing disabled.


## Relevant-source lock amendment

V1.2 retained a broad repository-wide Python source closure. During its capture, unrelated `domains/comprehend_text.py` and `substrate/world_adapter.py` edits invalidated that gate even though both workers that bracketed the capture and all native/semantic gates showed no change in the vision workload. V1.3 replaces that broad lock with a dynamic closure of project Python modules actually imported by the vision builder and boot path, plus the transitive seed-manifest closure of built-in core seeds and the vision seed roots, explicitly named builder files, native source files, binary/build manifest, protocol, runner, and analyzer. The lock is computed after importing all registered workload modules and is checked before/after each worker and after the capture. This is a source-scope correction, not an outcome-dependent gate change.
