# LLM transport anonymous-separator solver v1.3 amendment

Date: 2026-10-03

V1.2 shows every minimum separator candidate is exact, but it spends time solving both. V1.3 solves only the lexicographically first minimum separator; any valid separator is sufficient for exact conditional decomposition, so energy comparison across candidates is unnecessary. It uses one opaque worker-specific node permutation across all 20 cells and caches proposals only by the exact anonymous `(node set, edge set)` signature. Any changed topology triggers a fresh exhaustive search. The runner reports proposal work and per-cell solve work separately. The v1 sample, exactness checks, and claim boundary remain unchanged. V1.2 remains the valid uncached/all-candidates comparison.
