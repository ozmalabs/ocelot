# Code-write contract validation v1 — results

The four-worker source/native-locked panel completed with no worker errors and stable implementation fingerprints. In two aligned parity workers, the example was admitted, the new `taught_parity` construction was added, and native Term evaluation plus emitted Python matched five request-level contract observations each (10/10 total). In two same-arity mismatch workers, the parity source was attached to a square request. The first independent input/output contract row detected the mismatch; both acquisitions refused and neither worker added a write construction.

| Arm | Workers | Acquisition | Independent contract behavior | Construction growth |
|---|---:|---|---|---:|
| Aligned parity | 2 | Accepted | Native and Python exact on 10/10 cases | +1 per worker |
| Parity source for square request | 2 | Refused on first case | Both candidate outputs disagreed with square oracle | 0 |

Median full-seed boot was 17.95 s, peak RSS about 1.80 GB. Median acquisition time was 41.36 ms for aligned parity and 8.35 ms for the immediately rejected mismatch. These are small-panel measurements from one host; boot dominates the worker lifecycle.

## Interpretation and boundary

This validates an opt-in mechanism for preventing the measured semantic false transfer while retaining an aligned example. The caller supplies independent contract rows; the substrate checks exact argument keys and requires both native Term and rendered Python to match each expected output before grounding identifiers or teaching a reusable `ShapeSignature`. The task-specific protocol and analyzer keep the oracle outside the worker. The result does not establish that caller-supplied examples are correct or sufficiently discriminating, nor does it make contracts mandatory for existing callers. The earlier mismatch remains possible on the legacy no-contract route. Next measure contract selection/coverage and refusal tradeoffs over multiple independent task families, then decide which production surfaces can provide trustworthy contracts without simply moving all semantic work to an LLM.

## Artifacts

- [Preregistration](SUBSTRATE_CODE_WRITE_CONTRACT_VALIDATION_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_code_write_contract_validation_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_code_write_contract_validation_v1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_code_write_contract_validation_v1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/substrate_code_write_contract_validation_v1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_code_write_contract_validation_v1_analysis_20261001.json)
