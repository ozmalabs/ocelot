# Adequacy receipt adoption integration v1 results

The frozen integration panel passed in three fresh processes. Across all 18
adjudication/adoption checks, rejected, ambiguous, incomplete, invalid-source,
and missing receipts left the code-write ShapeSignature inventory and
`write_codebook_epoch` unchanged. A matching accepted receipt taught exactly
one new shape and advanced the epoch by one in every process. Source hashes
matched the pre-run lock before and after each worker.

The initial capture did not pass: its incomplete-evidence control was encoded
as a requested row with empty labels and therefore correctly adjudicated
`invalid`. The [v1.1 amendment](SUBSTRATE_ADEQUACY_RECEIPT_ADOPTION_V1_1_AMENDMENT_20261002.md)
records the fixture correction to submit zero rows; the confirmatory capture
uses a refreshed source lock and is the sole result reported below.

| Measure | Median |
|---|---:|
| Full-seed boot wall time | 17.568 s |
| Rejected receipt path | 3.393 ms |
| Ambiguous receipt path | 5.206 ms |
| Incomplete receipt path | 4.851 ms |
| Invalid provenance path | 5.830 ms |
| Missing receipt path | 5.639 ms |
| Accepted teach/adoption path | 32.669 ms |

The gate is now exercised at the actual `teach()` boundary through a seeded
`WorldAdapter`, not only through receipt-object validation. Its strict mode is
opt-in (`require_adequacy_receipt=True`); legacy callers that omit the strict
flag remain ungated. Hash and candidate checks establish internal consistency,
not label-provider identity or label truth. The example, finite probe domain,
and labels are authored by this harness. Three processes on one host do not
estimate natural-task prevalence, acquisition reliability, broad generality,
or full learning costs. Full-seed boot dominates this particular path.

Artifacts:

- [Preregistration](SUBSTRATE_ADEQUACY_RECEIPT_ADOPTION_V1_PREREG_20261002.md)
- [Amendment](SUBSTRATE_ADEQUACY_RECEIPT_ADOPTION_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_receipt_adoption_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_receipt_adoption_v1_lock_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_receipt_adoption_v1.py)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_receipt_adoption_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_receipt_adoption_v1_analysis_20261002.json)
