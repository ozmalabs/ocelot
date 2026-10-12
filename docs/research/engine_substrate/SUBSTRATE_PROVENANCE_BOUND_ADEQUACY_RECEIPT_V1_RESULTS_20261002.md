# Provenance-bound independent adequacy request/receipt v1 — results

## Result

The new `domains.independent_adequacy` API completed its source/input-locked panel with 24 candidate outcomes and six adversarial protocol controls. The independent analyzer reports zero errors. For each nonempty captured candidate, the API produced deterministic requests at budgets 1/2/4, bound each request to the candidate Term hash and acquisition trace hash, selected descriptors absent from acquisition/evaluation rows, and emitted receipts with per-probe provenance and residuals.

All 18 represented controls were accepted at all three budgets. The three cubic false singletons were rejected at every budget, beginning with the first fresh probe. Three empty absolute-value pools remained refused and did not produce candidate requests. The six protocol controls returned the preregistered results:

| Control | Receipt status |
|---|---|
| Two independent labels disagree | `ambiguous` |
| Requested probe omitted | `incomplete` |
| Audit source reused from acquisition | `invalid` |
| Descriptor altered | `invalid` |
| Request mutated without updating request ID | Fail closed with `ValueError` |
| One incorrect label | `rejected`, with prediction residual |

Across the 21 nonempty cases, total adjudication wall time was 2.12 ms at budget 1, 2.74 ms at budget 2, and 4.22 ms at budget 4. This includes request/evidence binding and receipt construction, but excludes the work needed to obtain labels.

## Interpretation and limits

This turns the previous harness-only check into a reusable, deterministic request and residual-record mechanism. It keeps acquisition evidence, requested probes, label-source declarations, model identity, and prediction residuals connected in one receipt. It does not install the candidate or authorize adoption. It also does not authenticate label sources: source IDs are caller declarations, and labels are supplied by the surrounding harness. The evaluation replays prior source-locked task captures and uses analytic/closure labelers; it is not a live external-provider, natural-task, noisy-world, or integration study. Probe-domain selection remains a seeded hash ordering over a caller-supplied finite domain, not a general adequacy guarantee.

The next engineering gate is to connect these receipts to the substrate's acquisition/adoption boundary, preserve them through Thoughtexperiment residual return, and measure how trusted evidence providers and adaptive probe selection affect false acceptance/refusal on independently authored tasks.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_PROVENANCE_BOUND_ADEQUACY_RECEIPT_V1_PREREG_20261002.md)
- API: [request and receipt implementation](../../../domains/independent_adequacy.py)
- Runner: [source/input locked runner](../../../evaluation/substrate_capability/substrate_provenance_bound_adequacy_receipt_v1.py)
- Analyzer: [independent replay analyzer](../../../evaluation/substrate_capability/analyze_substrate_provenance_bound_adequacy_receipt_v1.py)
- Lock: [source and parent-capture lock](../../../evaluation/substrate_capability/substrate_provenance_bound_adequacy_receipt_v1_lock_20261002.json)
- Capture: [raw outcomes](../../../evaluation/reports/substrate_provenance_bound_adequacy_receipt_v1_raw_20261002.json)
- Analysis: [machine-readable analysis](../../../evaluation/reports/substrate_provenance_bound_adequacy_receipt_v1_analysis_20261002.json)
