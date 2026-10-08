# COW value-shard write amplification v6 results

Date: 2026-10-06

## Result

The locked component profile confirms that branch-local first writes copy the
selected value shard. At N=50,771, the 64-shard map copies 793 entries for the
selected write; 128, 256, and 512 shards copy 397, 197, and 97 entries. The
expected root reference copies rise with shard count (64/128/256/512). Across
the three sizes, the COW fork-plus-delete median falls as shard count rises,
with a slight small-size reversal at 512 shards. At N=50,771 medians were
48.9, 14.9, 7.7, and 5.3 microseconds. Eager deep-copy-plus-delete medians
were 4.63–6.66 milliseconds in this isolated map workload.

| N | shards | estimated entries copied | COW fork + write | eager fork + write |
|---:|---:|---:|---:|---:|
| 7,164 | 64 | 111 | 4.8 µs | 559.8 µs |
| 7,164 | 128 | 56 | 2.5 µs | 543.8 µs |
| 7,164 | 256 | 27 | 1.3 µs | 575.7 µs |
| 7,164 | 512 | 14 | 1.9 µs | 578.2 µs |
| 16,384 | 64 | 256 | 12.4 µs | 1,310.8 µs |
| 16,384 | 128 | 127 | 5.0 µs | 1,389.5 µs |
| 16,384 | 256 | 63 | 3.0 µs | 1,241.1 µs |
| 16,384 | 512 | 34 | 2.8 µs | 1,372.7 µs |
| 50,771 | 64 | 793 | 48.9 µs | 4,630.7 µs |
| 50,771 | 128 | 397 | 14.9 µs | 6,656.5 µs |
| 50,771 | 256 | 197 | 7.7 µs | 4,832.9 µs |
| 50,771 | 512 | 97 | 5.3 µs | 5,705.4 µs |

The structural estimate matched the expected selected shard size after the
measurement setup was corrected to create a shared fork before reading it.
The initial invalid capture (which read zero copied entries) is overwritten;
only the corrected source-locked capture is analyzed. All worker checks
confirmed the branch misses the deleted key while the parent retains it.

## Interpretation and next gate

This identifies a real cost center in the component map and a clear
copy-amplification/metadata tradeoff. More shards reduce selected-shard clone
work, while the root pointer vector and map metadata grow. RSS is process-level
and page-granular, and this study does not measure graph mutation, closure,
query throughput, allocation bytes, or total engine memory. Therefore it does
not justify changing the production default. The next gate is to measure
candidate shard counts in the actual graph mutation panel and representative
closure workload, including query cost and memory, before any default change.

## Reproduction artifacts

Protocol: [preregistration](COW_VALUE_SHARD_WRITE_AMPLIFICATION_V6_PREREG_20261006.md).
Runner: [capture](../../../evaluation/substrate_capability/cow_value_shard_write_profile_v6.py).
Analyzer: [analysis script](../../../evaluation/substrate_capability/analyze_cow_value_shard_write_profile_v6.py).
Lock: [source and binary lock](../../../evaluation/substrate_capability/cow_value_shard_write_profile_v6_lock_20261006.json).
Data: [raw capture](../../../evaluation/reports/cow_value_shard_write_profile_v6_raw_20261006.json)
and [analysis](../../../evaluation/reports/cow_value_shard_write_profile_v6_analysis_20261006.json).
