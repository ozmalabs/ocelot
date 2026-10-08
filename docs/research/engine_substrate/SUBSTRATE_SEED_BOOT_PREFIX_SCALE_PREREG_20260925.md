# Full seed-loader prefix scale preregistration

Date: 2026-09-25  
Status: locked exploratory scale envelope

## Question

How do unprofiled full `load_all_seeds` startup time, CPU time, and process RSS grow over nested, dependency-safe prefixes of the canonical full seed load order?

## Design

- Freeze the V1.7 baseline corpus and verify every manifest against its 833-file corpus lock. The loader index contains 737 bulk-loadable seed IDs: 95 `self_load_only` files and one non-dict file are part of the physical corpus but do not enter the bulk index.
- Derive prefixes of 128, 256, 512, and 737 seed IDs from `_topo_order` over the full seed index. Materialize only the canonical indexed path for each ID in smaller points; the maximum point retains all 833 physical files so it reproduces full-corpus hashing and skip behavior. Abort unless each subset reorders to exactly the corresponding full-order prefix and contains no symlink.
- For each size, run two cold and two warm fresh processes; use cold/warm, then warm/cold order across the two replicates. Cold removes the per-subset seed-index cache; warm builds it before launch and verifies its bytes remain unchanged through boot.
- Time `WorldAdapter(seeds=())` construction plus full `load_all_seeds`; imports are excluded. Record peak RSS, manifest totals/loaded/failed, graph nodes/edges, active rule count/order, and graph/grammar/rule/access fingerprints.
- Require exact full-state equality across replicates within each size. Require all sources/build inputs and frozen snapshot bytes to remain unchanged.

## Claim boundary

This is an exploratory single-host curve over one authored corpus, with two repetitions per size/cache state. Prefix composition follows canonical seed order and is dependency-safe, but later points naturally include different seed families; the maximum point also scans 96 physical files excluded from the bulk index. It does not isolate any one module's complexity, establish asymptotics, or claim commodity-scale performance. Treat wall/CPU/RSS as measured points only; report indexed ID count and physical manifest count separately.
