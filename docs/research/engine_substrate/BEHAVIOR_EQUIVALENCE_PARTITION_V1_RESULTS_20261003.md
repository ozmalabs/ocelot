# Finite behavior-partition API and cost study v1 results

## API and correctness

`domains.contract_query.partition_hypotheses_by_behavior` now groups
hypotheses by typed Term outputs on a caller-provided finite probe set. It
returns class membership, probe count and SHA-256 digest. Term evaluation
failures use the same separate bucket as active-query selection. The API
explicitly limits its claim to the supplied probes.

The source-locked measurement passes all five gates. Its partitions match an
independent reference grouping on all 50 original/zero-aware survivor sets.
A controlled input verifies that `True`, integer `1`, and an evaluation error
remain three distinct classes. The analyzer confirms exactly H×P evaluator
calls for every invocation and independently reconstructs all scaling
partitions.

## Cost

On the 50 captured panels with 64 probes, median evaluator work is 64 calls;
median partition latency is 0.80 ms on zero-aware sets and 0.90 ms on original
sets. The synthetic scaling matrix runs H={1,2,4,8,16,32,64} candidates and
P={4,8,16,32,64} probes. At H=64,P=64, the utility performs 4,096 evaluations
and takes 36.55 ms median across the five task-specific workers; H=1,P=64
performs 64 evaluations and takes 0.81 ms. These are descriptive timings on
one host. When H exceeds the distinct source Terms, the benchmark repeats Terms
with unique IDs, so those cells measure grouping volume, not candidate
hypothesis diversity.

## Meaning and next step

This turns the finite behavior-class readout into a reusable query-layer API
with deterministic grouping and a locked H×P cost curve. It does not prove
that two Terms are equivalent beyond the probe set, choose a useful probe set,
or decide when a class is safe to return. The next policy study should compare
continued zero-aware probes, returning a probe-qualified class, and external
help on the same frozen panels. Score harmful ambiguity and false confidence
on broader, independently sampled holdouts, and report help calls and label
costs separately.

## Reproduction artifacts

- [Preregistration](BEHAVIOR_EQUIVALENCE_PARTITION_API_V1_PREREG_20261003.md)
- [API source](../../../domains/contract_query.py)
- [Measurement runner](../../../evaluation/substrate_capability/behavior_equivalence_partition_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_behavior_equivalence_partition_v1.py)
- [Source and input lock](../../../evaluation/substrate_capability/behavior_equivalence_partition_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/behavior_equivalence_partition_v1_20261003.json)
- [Independent analysis](../../../evaluation/reports/behavior_equivalence_partition_v1_analysis_20261003.json)
