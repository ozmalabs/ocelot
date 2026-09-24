# Phase 7 native substrate measurement

This is the bounded Phase 7 native-integration increment for substrate
performance measurement. It measures the Rust cycle boundary directly and
does not import conversation topic, discourse, or production runtime code.

## Protocol

`evaluation/native_cycle_measurement.py` constructs two identical native
substrates for each bounded profile. The profiles are `fast` (one transition),
`deep` (24-stage propagation), `recovery` (twelve two-stage detect/close
transitions), `long_dialogue` (32 linked event nodes), and `dense_graph` (12
candidates with 44 native-visible edges). The first substrate
is run for a bounded number of native cycles; the second is replayed with the
same schedule. The harness records native reports, graph residence, bounded
wall latency, peak RSS, and explicit step/graph/replay resource assertions.
Wall-clock measurements are excluded from replay equality.

Run with:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m evaluation.native_cycle_measurement
```

Select a stress profile with `--profile deep`, `--profile recovery`,
`--profile long_dialogue`, or `--profile dense_graph`; the default is `fast`.

The maximum accepted request is 256 measured cycles and 64 warm-up cycles.
This prevents an evaluation invocation from becoming an unbounded workload.

## Acceptance evidence

The focused test suite verifies:

- native cycle reports are returned and bounded;
- the graph-authored transition occurs in the native cycle;
- node and edge residence are observable;
- a fresh replay produces identical native reports and graph state;
- latency and peak RSS are recorded as measurements rather than used to select
  a cognitive outcome.
- deep, recovery, and long-dialogue profiles remain within fixed native step
  and graph ceilings and replay identically.
- dense-graph execution remains within the same fixed ceiling, and every
  resolved candidate is evidenced by the native trace rather than a Python
  outcome-selection step;
- the authority audit records the pre-cycle graph, native trace/step alignment,
  and post-cycle graph mutation, making the native trace the authoritative
  execution evidence at the Python I/O boundary.

This closes the bounded Phase 7 performance-envelope increment. Full Phase 7
exit remains dependent on native-authority coverage for remaining cognitive
decisions and broader resource envelopes outside these fixed profiles.
