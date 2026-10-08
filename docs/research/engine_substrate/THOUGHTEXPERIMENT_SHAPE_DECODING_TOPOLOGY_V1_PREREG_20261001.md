# Shape-decoding Thoughtexperiment topology v1 — preregistration

**Question:** Does branch and prediction cost depend on unrelated-graph topology or aperture boundary size, even at fixed 100k noise nodes?

Compare five graph constructions at the same unrelated-node count: existing path; disconnected star; disconnected grid; deterministic sparse random graph with approximately four endpoints per node; and an observation-spoke stress graph connecting each noise node to one of the three focus observations. The last condition deliberately makes the focus boundary scale with graph size. Use 100k noise nodes × five topologies × scoped full-copy/shared pages × sequential/concurrent fanout 8 × three fresh processes (60 total). Each process runs positive `dedup_identity_fix` and negative `add_match_guard(control)` waves, alternating arm order. Record resulting node/edge counts, branch and prediction phases, CPU/wall, outcomes, primary isolation, and provenance.

**Gates:** 60 unique processes and every topology/backend/mode cell; positive and negative task oracle; exact parity across backends and modes within each topology/arm; primary revision, graph, and rules unchanged; source/native lock/build freshness; phase/timing nonnegative; resulting node/edge counts stable across repeat/backend/mode for each topology.

**Interpretation:** Compare disconnected topologies at near-equal edge count to identify sensitivity to degree/distribution; compare observation-spoke against disconnected graph to assess high-aperture cost. One synthetic task and one host do not establish natural graph distributions or a general treewidth law. No asymptotic complexity claim.
