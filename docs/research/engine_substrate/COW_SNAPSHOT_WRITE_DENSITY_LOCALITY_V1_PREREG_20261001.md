# Copy-on-write branch write density and locality v1 preregistration

Date: 2026-10-01

## Question

At fixed base graph size, how do branch-local write density and the placement of writes across graph pages affect shared-page CoW versus eager branch time and whole-process memory? This tests when the immutable-base sharing advantage survives mutation, rather than extrapolating from a one-write branch.

## Frozen workload

- Native `Substrate` ring graphs with 10,771 and 50,771 nodes, and exactly one ring edge per node in every cell. `N` is fixed within each size; for each row, exactly the chosen fraction is `active_input`, and the rest are same-count `filler_input` edges.
- One native one-edge rule matches `active_input` and adds `write_output` between the same endpoints. Every branch must add exactly K output edges, retain all N base edges, and reach fixed point. This real AddEdge effect is not `batch_safe`; no within-rule batching is claimed.
- Write densities are 1%, 10%, 50%, and 100%, with K=floor(N*density). For 1%, 10%, and 50%, active source nodes are either a contiguous prefix (page-local) or evenly spaced around the ring (page-spread). At 100%, use one canonical all-active pattern.
- Compare a reusable shared-graph-page snapshot with a reusable eager full-copy base. For each size × density × pattern × five repeats, measure serial and simultaneous Rust-thread branch execution at fanout 4, then sample one-live-branch and fanout-live PSS plus post-drop PSS. Each cell/repeat uses a fresh worker process; arm order alternates by repeat.
- Keep the primary and both base controls resident. Check primary revision/counts and empty output type after branch execution, and verify a later fork from both bases sees the untouched source graph.
- Complete the full factorial: two graph sizes × seven density/pattern combinations × five fresh repeats = 70 worker processes. No performance or memory threshold is imposed.

## Measurements and interpretation

Report fork, closure, and batch wall time, with paired CoW/eager outcomes and live/drop PSS deltas. The density and locality labels describe the selected input edges, not a formal measurement of physical page placement; report them as graph-index locality treatments. This is a synthetic ring workload on one host. PSS is whole-process proportional accounting, not object-level ownership or proof of allocator reclamation. Results do not establish natural workload frequency, concurrent writes to one substrate, serving integration, or vLLM KV-block compatibility.

## Decision use

Use the observed density/locality interaction to choose the next representation work: retain current sharing where sparse writes help; profile and reduce touched adjacency/index/page copies where gains disappear. Keep the abstract immutable-base/branch lifecycle separate from any graph storage policy or future shared-prefix serving adapter.
