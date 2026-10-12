# Exact-linear GenInfer prefilter pilot v1 results (2026-10-06)

## Scope

This is a paired engineering pilot for runtime plumbing and local work reduction.
It is not the preregistered v1 admission experiment in
[`SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006.md`](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006.md).
It covers one seven-relation linear-positive training frame and six disjoint
held-out relations, with ten fresh-worker repeats, prefilter gate off/on, and
scale audit off/on. Each worker call creates a fresh substrate but calls were
run serially in one Python process, so this is not process-isolated replication.
Both arms use the same feature-enabled native binary;
only `agent.gen_linear_exact_enabled` changes. The binary also has the
quadratic feature, and the quadratic runtime gate is held enabled in both arms.

## Result

All 20 paired comparisons preserve the complete selected linear payload,
training residual, reload payload, held-out `DimInfer` result, and transform
receipts. Audit-on/off semantic outputs also match for each repeat and gate.
The linear generator is acquired and recognized on transfer in every worker.
The prefilter counter identity
`attempts = solved + proven_no_fit + fallback` holds in every audit-on row.

In the ten audit-on runs per gate, the median matrix attempts per closure fell
from 39,360 to 19,683 (49.99% fewer). The prefilter handled three of six
eligible base evaluations in each closure and conservatively fell back on the
other three; no proven-no-fit case occurred. Across ten runs this totals 60
attempts, 30 solved, 30 fallbacks, and zero proven no-fits.

Audit-off median training closure was 75.49 ms with the prefilter gate off and
27.31 ms with it on. This is a 2.76x pilot ratio for this particular
linear-positive frame. It is not a general speedup estimate: the frame is
small, there is one condition, the baseline is the same feature-on binary
under a runtime gate, and the number of repeats is ten. The feature-off and
quadratic-only source-matched arms, negative controls, source-frame parity
panel, and high-bound stress test have not run.

## Integrity and artifacts

- Runner: [`geninfer_exact_linear_prefilter_pilot_v1.py`](../../../evaluation/substrate_capability/geninfer_exact_linear_prefilter_pilot_v1.py)
- Analyzer: [`analyze_geninfer_exact_linear_prefilter_pilot_v1.py`](../../../evaluation/substrate_capability/analyze_geninfer_exact_linear_prefilter_pilot_v1.py)
- Raw capture: [`geninfer_exact_linear_prefilter_pilot_v1_20261006.json`](../../../evaluation/reports/geninfer_exact_linear_prefilter_pilot_v1_20261006.json), SHA-256 `842346dd68f283b953f755746d8d44d21d4a3be397580e620b0286f1540ea818`
- Analysis: [`geninfer_exact_linear_prefilter_pilot_v1_analysis_20261006.json`](../../../evaluation/reports/geninfer_exact_linear_prefilter_pilot_v1_analysis_20261006.json), SHA-256 `87c187fe5272b7c197e3404827e68443b05d927db8739fff6cb19f4d34bd6102`
- Native binary: `/tmp/ocelot-prefilter-pilot-v1.so`, SHA-256 `1e1f3059ca331af38e55fa037903dc4bcab23e992fd289a551b4de632812da23`
- Build command and source SHA-256 manifest are embedded in the raw capture.

The pilot source manifest predates the v1.1 relation-count proof and v1.2
integer-only coordinate check; that source drift is expected. Its raw capture
retains the point-in-time source hashes and the corrected path of the
preserved binary.

## Decision

The pilot supports two narrow conclusions: runtime gate plumbing works through
training, reload, transfer and counters; and on this case the prefilter removes
about half of the matrix attempts without changing semantics. It does not
qualify the prefilter for default enablement or establish general tractability.
Continue with the preregistered three-build differential corpus, counter
accounting, semantic/refusal panel, and separate high-bound stress worker.
