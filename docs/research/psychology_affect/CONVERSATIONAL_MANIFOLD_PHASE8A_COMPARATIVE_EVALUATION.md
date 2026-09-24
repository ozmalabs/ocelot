# Phase 8A comparative evaluation and release-gate scaffold

Phase 8A defines the measurement contract for comparing the conversational
manifold against five reference classes:

- ELIZA floor
- small LLM
- modern LLM
- base human
- advanced human

The target and every reference are scored on the same fixed cognition
dimensions:

`interpretation`, `grounding`, `action`, `repair`, `memory`, `learning`,
`calibration`, `provenance`, and `cost`.

This increment is a scaffold, not a benchmark result. It intentionally does
not fabricate scores for models or people, or claim that the target has been
measured when the live corpus runner has not completed. A scorecard is valid only when it
contains all nine dimensions, a fixed protocol identifier, a sample count, a
95% interval, a raw-metric description, and provenance references to the
underlying cases or annotations.

## Measurement semantics

Capability scores are normalized to `[0, 1]`, with higher meaning better. The
`cost` score means cost-effectiveness; raw latency, memory, tokens, energy, or
money must remain in the referenced evidence. The gate never silently
inverts an unlabelled cost number.

Comparisons use interval separation:

- `above`: target lower bound is above the reference upper bound;
- `below`: target upper bound is below the reference lower bound;
- `indeterminate`: intervals overlap.

Indeterminate is not failure and is not superiority. It identifies where the
protocol needs more samples or better measurement precision.

The report scaffold can be generated without running any system:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m evaluation.phase8_corpus_runner \
  --scaffold --output evaluation/reports/phase8_corpus_report_scaffold.json
```

The scaffold binds exactly 74 Phase 0 events, marks the target `not_run`, marks
all five external baselines `unavailable`, and must remain `blocked`. A live
target report is only produced by omitting `--scaffold`; baseline scorecards
remain unavailable until those systems are actually run under this protocol.

The v2 report envelopes also contain `comparison_summary`. This is an availability envelope,
not an additional score: `measured` means interval comparison is eligible,
`unavailable` means the reference was not collected, `missing` means no
scorecard was supplied, and `not_comparable` means the target or reference
cannot support a comparison. Unavailable baselines have empty dimension
comparisons and are never represented as zero performance or superiority.

Each reference class also has a runnable envelope generator:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m evaluation.reference_protocol \
  modern_llm --output evaluation/reports/modern_llm_reference_scaffold.json
```

The envelope records the adapter entrypoint, collection mode, annotation
source, all 74 case IDs, raw observation slots, and an unavailable scorecard.
It does not score absent model or human observations. The five reference
protocols are ELIZA floor, small LLM, modern LLM, base human, and advanced
human; their collection specifications are exposed by
`comparative_release_gate.protocol_contract()`.

## Release rule

The gate reports `ready` only when all six scorecards (target plus five
references) are complete, every dimension has evidence, and no target
dimension is below a baseline. Missing or unproven evidence produces
`blocked`; it does not receive a conversational fallback or an assumed score.

Run the focused scaffold tests with:

```text
PYTHONPATH=runners/dsl/python:. .venv/bin/python -m pytest -q --tb=short tests/test_phase8a_comparative_release_gate.py
```

The next Phase 8 increments should bind this contract to the fixed Phase 0
event corpus, preregister case-level annotation rules, collect repeated
baseline observations, and publish a dated report with confidence intervals
and failure slices. Until then, Gate G8.1 remains open.
