# Live held-topic evidence v1.1 amendment (2026-09-26)

The initial v1 worker reached the first live answer but its post-turn structural analyzer called `out_edges` on the native `substrate_rs.Substrate` API, which does not expose that method. The worker failed before returning a raw payload; the parent runner also had not persisted completed workers incrementally. That attempt is excluded from result claims.

V1.1 retains the exact preregistered facts, prompts, route expectations, semantic gates, and work boundaries. It computes the task evidence-edge projection through the adapter's supported `neighbours`/`in_neighbours` API over the explicitly named task relation family and records that scope in every frame projection. Whole-graph node/edge counts still come directly from the native graph counters. The parent writes raw worker results after each completed process so a later worker or analyzer failure cannot erase earlier captures.

Before the locked three-worker run, one direct worker smoke attempt then failed while counting node types because `Substrate.nodes()` yields `NodeID`s, not typed node records. This attempt produced no worker payload and is excluded. The v1.1 runner now reads each node record through `Substrate.node(id)` for type counts; the locked confirmatory schedule starts only after this correction.
