# Code-write example acquisition v1 — preregistration

## Question

Can the current code-reading and write-codebook growth path ingest an externally supplied function, add a reusable construction to a fresh substrate, select that construction for the same natural-language request, and transfer it to inputs not used by the codebook's internal sample check?

## Frozen panel

Run two families in five fresh processes each, in a deterministic randomized schedule (seed `20261017`):

1. **Parity:** request `Write a function that returns the parity of an integer.` External source: `def parity(value): return value % 2 == 0`.
2. **Clamp:** request `Write a function that clamps a value between lower and upper bounds.` External source: `def clamp_value(value, lower, upper): return lower if value < lower else (upper if value > upper else value)`.

Each worker boots a fresh `WorldAdapter(seeds=())` with the full seed set, and disables LLM calls and seed persistence. It first calls `write_function_from_request` before teaching (baseline control), then calls `teach_write_shape_from_example` with the externally supplied source and original request, then calls `write_function_from_request` again. The post-teaching construction must be a newly present `ShapeSignature` with `kind=code_write_construction`, provenance `taught_from=example`, and `taught_for` equal to the original request. The runner captures the resulting native Term and generated Python function on held-out inputs. It does not send expected held-out outputs to the substrate.

Held-out parity inputs are every integer from -20 through 20. Held-out clamp inputs are a frozen set of 20 `(value, lower, upper)` triples with `lower <= upper`, spanning negative/positive bounds, endpoints, interior values, and values outside each bound. These differ from `code_writing._sample_env`'s internal sanity checks. The independent analyzer supplies the analytic oracle: parity is `value % 2 == 0`; clamp is the supplied piecewise definition. It compares both native Term evaluation and execution of generated Python against those outputs.

## Gates and measurements

- Ten distinct fresh worker processes, five per task, with source/seed/native fingerprints unchanged across each worker.
- Baseline request does not produce a function from the starter codebook.
- Example reading and teaching report success; a new live shape is present with the required provenance.
- The original request selects that exact new shape after teaching and returns an executable function.
- Native-Term output and generated-Python output each match the independent oracle on every held-out input and match each other.
- Primary live codebook growth is recorded, along with boot, teach, composition, function generation, and held-out execution time, CPU, and peak RSS.

## Claim boundary

A pass establishes externally supervised codebook acquisition and exact transfer on two fixed integer families. The source example, task family, request, held-out inputs, and oracle are authored by the benchmark. The internal `teach_write_shape_from_example` validation compares generated code against the same Term it just read; that self-check is not the independent outcome oracle. This study does not show autonomous source generation, primitive invention, general natural-language understanding, broad code synthesis, or general self-improvement. The result must be described as learning from supplied executable examples.

## Artifacts and execution

- Runner: [`substrate_code_write_example_acquisition_v1.py`](../../../evaluation/substrate_capability/substrate_code_write_example_acquisition_v1.py)
- Analyzer: [`analyze_substrate_code_write_example_acquisition_v1.py`](../../../evaluation/substrate_capability/analyze_substrate_code_write_example_acquisition_v1.py)
- Pre-capture lock amendment: [`SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PRECAPTURE_AMENDMENT_20261001.md`](SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PRECAPTURE_AMENDMENT_20261001.md)
- Lock and raw/analysis captures are written under `evaluation/substrate_capability/` and `evaluation/reports/`.

From repository root: `python3 evaluation/substrate_capability/substrate_code_write_example_acquisition_v1.py --lock`, then run the runner and `python3 evaluation/substrate_capability/analyze_substrate_code_write_example_acquisition_v1.py`.
