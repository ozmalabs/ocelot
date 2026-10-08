# Exact-linear GenInfer prefilter v1.1 high-bound results (2026-10-06)

## Result

The amended high-bound stress pair passes. It uses the cubic out-of-family
condition from v2.2, a seven-relation training frame whose transformed
coordinate extent previously expanded the matrix bound to 64. The two workers
use the same v1.1 native binary with the prefilter runtime gate on: one
audit-off worker for timing and one audit-on worker for the proof counters.
Both finish in under 0.4 seconds wall time; native training closure is under
1.2 ms.

The audit-on worker records two prefilter attempts, both proven no-fit, no
fallbacks, and zero matrix attempts. The quadratic learner runs twice and has
zero survivors. There are no linear or quadratic generator payloads after
training or held-out transfer. The worker reports a generic `minted` status
and one added `CapabilityAxis`, but its `DimensionGenerator` payload lists are
empty; thus the relevant generator codebook remains unchanged.

This outcome follows a failed preliminary build. Before the amendment, a
high-bound worker using binary SHA-256
`1e1f3059ca331af38e55fa037903dc4bcab23e992fd289a551b4de632812da23` remained
in training closure until a 300-second timeout and required SIGKILL. Inspection
then found that the exact validator rejects every matrix immediately when
relation counts differ, while the prefilter had treated that case as uncertain
and enumerated. The v1.1 amendment permits this unconditional proof and the
resulting code skips that enumeration. The amended build is not evidence for
the earlier binary.

## Artifacts and limits

- Amendment: [`SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_AMENDMENT_20261006.md`](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_AMENDMENT_20261006.md)
- Runner: [`geninfer_exact_linear_prefilter_highbound_v1_1.py`](../../../evaluation/substrate_capability/geninfer_exact_linear_prefilter_highbound_v1_1.py)
- Analyzer: [`analyze_geninfer_exact_linear_prefilter_highbound_v1_1.py`](../../../evaluation/substrate_capability/analyze_geninfer_exact_linear_prefilter_highbound_v1_1.py)
- Raw pair: [`geninfer_exact_linear_prefilter_highbound_v1_1_20261006.json`](../../../evaluation/reports/geninfer_exact_linear_prefilter_highbound_v1_1_20261006.json), SHA-256 `612061ec6de500b7fedef5dc0795929bbe78b17f0c821b079987c495daed75bc`
- Analysis: [`geninfer_exact_linear_prefilter_highbound_v1_1_analysis_20261006.json`](../../../evaluation/reports/geninfer_exact_linear_prefilter_highbound_v1_1_analysis_20261006.json), SHA-256 `60f209be394ed0b470f04037328eb3cb76c688290713d51866f2426391636a8c`
- Native binary: `/tmp/ocelot-prefilter-highbound-v1_1.so`, SHA-256 `2d57086c640a0cbb1b8170ca261df4a40c0ba463800b9b73bc6263e3ccdbaec1`.

The source manifest, timeout, build command, audit counters, worker payloads,
and both full worker records are embedded in the raw capture. The captured
source predates the v1.2 integer-only coordinate guard, which does not alter
this all-integer stress input. The native binary was preserved at the path
listed above after the shared temporary build output was reused. This is one
high-bound control on one feature-enabled binary, not the matched three-build
main panel and not a general tractability result. The v1 oracle and main-panel
negative controls remain outstanding.
