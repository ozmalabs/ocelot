# Task-graph structural census v1.3 amendment

Date: 2026-10-03

The v1.2 capture completed all 78 planned snapshots. Its analyzer exposed an identity collision: `concurrent_goals` occurs three times per connected-conversation replicate, while the v1.2 row key used only the case label. V1.3 adds each case's zero-based position in its source run to the case key and aligns source-run identities across the runner and independent analyzer. It retains v1.2 artifacts and its analyzer failure as provenance. The upstream graphs, 78 observations, graph projection, metrics, and claim boundary are unchanged. A fresh source lock covers these identity changes.
