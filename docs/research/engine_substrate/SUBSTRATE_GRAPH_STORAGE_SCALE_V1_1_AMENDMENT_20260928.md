# Native graph storage scale v1.1 amendment

Date: 2026-09-28, before the v1.1 capture.

The completed v1 panel reports correct chain construction and sampled reads through one million nodes, with two fresh workers per size. To measure the next scale directly, v1.1 adds N=10,000,000 to the same frozen workload and preserves N=10,000/100,000/1,000,000 as bridge controls. It keeps two fresh workers per size, the same node/edge semantics, measurements, and correctness gates. V1.1 uses distinct runner, analyzer, lock, summary, raw, and output paths so it cannot overwrite v1 evidence.

The added 10M case is fixed before its output is observed. If it exceeds available resources or fails, retain and report that outcome; do not substitute a smaller size. This remains a storage-construction envelope and does not imply closure, inference, or natural workload scaling.
