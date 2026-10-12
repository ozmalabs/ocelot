# Native seed projection integration results

Date: 2026-09-25  
Status: release build current; contract matrix and four full-corpus parity workers pass

## Implemented boundary

`PySubstrate::load_seed_manifest` now builds a shallow Python dict containing only the ten top-level fields read by the Rust loader, then sends that projection through the existing `pyobj_to_json` and JSON parser. All nested values inside consumed fields follow the previous serialization and parse route. The caller's manifest remains unchanged. Unknown top-level metadata is intentionally ignored by this API, whether or not that unused value is itself JSON-serializable. The Python facade now documents this field contract. Direct `_inner` callers receive the same behavior because projection is at the underlying PyO3 method.

## Gates

- The sanctioned release build completed and wrote current build provenance.
- Twenty-eight contract probes cover presence/absence of all ten consumed keys, unknown JSON and non-JSON metadata, root type errors, malformed node/edge inputs, and resilient malformed production/rule/reflex inputs. The original root and malformed-node ValueError class/messages are preserved; caller dictionaries remain unchanged.
- Four fresh full-corpus boots (two cold, two warm) match one another and the frozen 737-ID baseline exactly across the complete load report, graph, grammar, exported rule store, rule access/order, active rules, and counts. The stable report has 726 loaded IDs and 11 load failures.
- Cold median wall is 14.33 s, warm median 11.65 s; median process CPU is 15.38 s cold and 12.77 s warm. Peak RSS is about 1.67 GiB in all four workers, without the manifest-retention instrumentation used in the projection experiment.

## Limits

The parity baseline is exact, but its provenance differs in several Python source files from this integration run; therefore this is a compatibility gate, not a controlled production speed comparison. The separate same-run projection intervention remains the evidence for conversion-cost reduction (68–70% fewer boundary JSON bytes and 18–22% lower median CPU/wall under equal instrumentation). The new release path's timings are an operating envelope on one machine, not a general scale claim. The contract probes are a bounded schema matrix, not exhaustive adversarial JSON or every application caller's runtime path.

## Artifacts

- Protocol: [`integration preregistration`](SUBSTRATE_NATIVE_SEED_PROJECTION_INTEGRATION_PREREG_20260925.md)
- Caller audit: [`caller audit`](SUBSTRATE_NATIVE_SEED_CALLER_AUDIT.md)
- Runtime and contract runner: [`integration probe`](../../../scripts/substrate_native_seed_projection_integration_probe_v1.py)
- Source/build lock, raw report, and independent validation: [`lock`](../../../evaluation/substrate_capability/native_seed_projection_integration_lock_20260925.json), [`raw`](../../../evaluation/reports/substrate_native_seed_projection_integration_v1_20260925.json), [`analysis`](../../../evaluation/reports/substrate_native_seed_projection_integration_v1_analysis_20260925.json), [`analyzer`](../../../scripts/analyze_substrate_native_seed_projection_integration_v1.py)
- Excluded harness attempts: [`fingerprint encoding attempt`](../../../evaluation/reports/substrate_native_seed_projection_integration_v1_harness_attempt1_20260925.json), [`incomplete optional-ID probe attempt`](../../../evaluation/reports/substrate_native_seed_projection_integration_v1_harness_attempt2_20260925.json), [`runner-lock omission attempt`](../../../evaluation/reports/substrate_native_seed_projection_integration_v1_harness_attempt3_20260925.json)
