# Access-trace blind-spot probe v1 results (2026-09-26)

## Result

The preregistered paired diagnostic runner passes all seven checks in the machine report. Each case uses a fresh native substrate, and trace-disabled/enabled semantics agree.

- `SetAttrIfDifferent`, unchanged target: fixed point, zero progress, final value remains `1`; the direct effect reads the old value and makes the equality decision, but the trace has zero target `effect_attr_write` events. The one total trace event is the successful pattern binding.
- `SetAttrIfDifferent`, changed target: fixed point after one progress step, final value becomes `1`; one target `effect_attr_write` event is recorded.
- `UseTool`: the independent Python handler counter records one call in both arms; the matched rule reaches fixed point with zero progress; the trace contains no tool-kind event (one pattern event only).
- All arms report zero dropped rows. This tiny fixture does not measure overhead or prevalence.

These results directly confirm that trace event counts omit the unchanged old-value read and the tool callback boundary. They do not show that every tool is graph-pure, or that every unchanged effect is otherwise visible. Cache-key scans, failed matcher candidates, scheduler/out-of-rule work, and general trace recall remain unresolved.

## Reproduction and provenance

Run:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_access_trace_blindspot_probe_v1.py
```

The runner writes the raw paired cells and shared run manifest to [`machine report`](../../../evaluation/reports/substrate_access_trace_blindspot_probe_v1_20260926.json), including current source/native hashes. Its design was frozen in the [preregistration](SUBSTRATE_ACCESS_TRACE_BLINDSPOT_PROBE_V1_PREREG_20260926.md); the [runner](../../../scripts/substrate_access_trace_blindspot_probe_v1.py) verifies the expected event asymmetry and semantic parity. The manifest references a hashed parent-process log at `evaluation/run_logs/substrate-access-trace-blindspot-probe-v1-20260926.stdout_stderr.log`.
