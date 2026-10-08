# Native query-eligibility scaling v1 results

## Result

The corrected 25-worker capture passes all eight capture checks. The independent analyzer passes all eight checks, including current source lock, exact seed/panel accounting, regenerated eligible-set digests, selected-node/rank replay, and finite cost records. All 512–8,192-example workers produced exact eligibility and selection parity.

## Cost curve

| Probe examples | Median eligible count | Eligibility closure median / p90 | Argmin selection median | Graph build median | Worker CPU median | Peak RSS median |
|---:|---:|---:|---:|---:|---:|---:|
| 512 | 256 | 3.45 / 4.27 ms | 0.074 ms | 3.42 ms | 58.85 ms | 35.5 MiB |
| 1,024 | 512 | 17.67 / 20.29 ms | 0.189 ms | 6.30 ms | 77.01 ms | 35.8 MiB |
| 2,048 | 1,024 | 55.56 / 62.27 ms | 0.231 ms | 14.13 ms | 124.25 ms | 36.9 MiB |
| 4,096 | 2,048 | 203.16 / 215.97 ms | 0.410 ms | 29.97 ms | 290.11 ms | 39.5 MiB |
| 8,192 | 4,096 | 852.06 / 898.73 ms | 0.852 ms | 53.39 ms | 978.04 ms | 42.8 MiB |

Increasing the probe population 16× raises median eligibility closure about 247×, while selection closure rises about 11.5×. This is consistent with a quadratic matching cost in the current rule shape; five sizes do not prove an asymptotic class. The selector is a much smaller cost than eligibility at every measured size. The likely cause is match order: the rule binds the full probe population before joining each vote back to its example, potentially constructing a large intermediate match set.

## Limits and next gate

This is a synthetic graph-level benchmark of the v1.3 eligibility and selection rules, not a natural workload or end-to-end application result. Process RSS includes the interpreter and native runtime. Graph construction is separately reported. The relation population and positive fraction are controlled; no task labels are exposed to ranking.

Next compare the current join order against an equivalent rule that binds family vote, vote-to-example, then checks episode probe membership. Use paired seeds and the same population sizes. Require exact eligible identity and selected node parity before comparing timing. If that order reduces the curve while retaining outputs, validate it on the full v1.3 task workload before treating it as an engine improvement.

## Reproduction

See the [preregistered protocol](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V1_PREREG_20261005.md), [implementation amendment](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V1_AMENDMENT_20261005.md), [runner](../../../evaluation/substrate_capability/native_query_eligibility_scale_v1.py), [source lock](../../../evaluation/substrate_capability/native_query_eligibility_scale_v1_lock_20261005.json), [raw capture](../../../evaluation/reports/native_query_eligibility_scale_v1_20261005.json), and [independent analysis](../../../evaluation/reports/native_query_eligibility_scale_v1_analysis_20261005.json). Reproduce by running:

```sh
python3 evaluation/substrate_capability/native_query_eligibility_scale_v1.py --run
python3 evaluation/substrate_capability/analyze_native_query_eligibility_scale_v1.py
```

