# Synthesis acquisition/application economics results

**Status:** descriptive F3 pilot; all three registered task cells pass. Results cover direct native `SynthEnumerate` and native `Substrate._inner.evaluate` on the exact returned Term. They do not cover reflected Program IR through `ProgEval` or the full P4 orchestration path.

## Measurements

Three direct acquisitions per task found the same canonical term each time and passed the held-out example. Median acquisition wall time and candidate work varied sharply with the selected search burden:

| Task | Candidates | Median acquisition | Application cost per call (100–10,000 batch) |
|---|---:|---:|---:|
| `pbe_001` reverse string | 59 | 0.08 ms | 2.60–2.64 µs |
| `pbe_010` first word | 125,344 | 72.76 ms | 4.46–4.61 µs |
| `pbe_024` trap capitalize/reverse/slice | 198,949 | 101.60 ms | 4.93–5.04 µs |

The 2- and 5-use direct acquire-and-use batches took 140/370 ms for `pbe_010` and 188/494 ms for `pbe_024`. Reusing one acquired program and applying it 2/5 times took about 72.77/72.78 ms and 101.61/101.62 ms respectively. These are same-runtime, repeated-identical-spec comparisons with substrate creation excluded from both sides. For `pbe_001`, acquisition is shorter than timer/call overhead at this resolution; its 2/5-use repeated-search batches (0.37/0.48 ms) are too noisy to support a useful ratio.

The larger-task result shows a concrete, narrow amortization profile: on these fixed tasks, repeated use is several microseconds per held-out call after a one-time 73–102 ms search, while repeating acquisition repeats the search cost. The arithmetic comparison crosses at reuse count 2 by construction for a repeated identical specification; no natural reuse frequency or general break-even distribution was measured. The 10,000-call application batches and costs beyond them are observed over this Term-evaluator path, not end-to-end serving latency. This is not the reflected Program IR / `ProgEval` application path used elsewhere in program synthesis.

## Provenance and limits

The preregistered task IDs were chosen from the existing direct-PBE recheck based on previously observed candidate counts. They are a deliberately selected low/moderate/high search-cost set, not a random sample. Search uses the fixed declared operator and constant pools and `max_size=15` with the engine's default candidate limit. The evaluator is called through the native extension, but each call crosses the Python binding; this is not an isolated Rust instruction-time measurement. Import, substrate creation, full adapter boot, held-out verification cost during acquisition, maintenance/update cost, and long-term retained-state cost are outside the acquisition timer. `pbe_024` belongs to the registered memorization-trap stratum and passes its declared held-out check, but this small sample cannot estimate false-acceptance rates.

Protocol: [preregistration](SUBSTRATE_SYNTHESIS_ACQUISITION_APPLICATION_PREREG_20260925.md). Runner: [measurement script](../../../scripts/substrate_synthesis_acquisition_application.py). Inputs: [frozen lock](../../../evaluation/substrate_capability/synthesis_acquisition_application_lock_20260925.json). Raw results: [JSON](../../../evaluation/reports/substrate_synthesis_acquisition_application_20260925.json).
