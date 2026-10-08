# Scaled solver-alternative panel v1 amendment

Date: 2026-10-01

The initial serial v1 panel was interrupted before it wrote an aggregate raw capture. No partial output was retained as result evidence. A standalone 256-node banded worker took approximately 58 seconds, revealing that the serial 18-worker orchestration was unnecessarily slow for this panel. V1.1 preserves every preregistered size, topology, replicate, candidate, and semantic gate, but runs at most three independent fresh workers concurrently. The result is based only on v1.1's new source/native lock and raw capture; see [v1.1 preregistration](COW_SOLVER_ALTERNATIVES_SCALE_V1_1_PREREG_20261001.md) and [results](COW_SOLVER_ALTERNATIVES_SCALE_V1_1_RESULTS_20261001.md).
