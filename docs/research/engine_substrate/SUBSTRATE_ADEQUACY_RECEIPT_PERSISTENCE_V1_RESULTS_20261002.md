# Adequacy receipt persistence and replay v1 results

The confirmatory source-locked panel passed in three writer/reader process
pairs. All 18 independent analysis checks pass. In each pair, strict-mode
accepted teaching writes the augmented code-write construction seed; a
separate process boots against an overlay of the full seed corpus and restores
exactly one `taught_square` with identical attributes. Replaying the same
receipt in that restored graph succeeds without a second live node, a second
seed entry, or an epoch increment. Reusing it with changed source bytes or
changed request text is refused with no code-shape/epoch mutation. Manifest,
receipt, and source hashes remain stable across each pair.

| Measure | Median |
|---|---:|
| Writer full-seed boot | 16.672 s |
| Accepted teaching and durable write | 59.488 ms |
| Reader full-seed boot | 19.418 s |
| Restored-graph receipt replay | 32.779 ms |

The first source-locked capture passed persistence and restore but found a
duplicate live shape on receipt replay. The failure is preserved as a
[diagnostic capture](../../../evaluation/reports/substrate_adequacy_receipt_persistence_v1_initial_diagnostic_20261002.json).
The [v1.1 amendment](SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_1_AMENDMENT_20261002.md)
documents the fix: `teach()` now reuses an exact `(type, attrs)` match before
adding a node. The amended capture reruns the same preregistered gates under a
refreshed lock. This corrects an idempotency defect; it does not add receipt
authentication or one-shot/revocation semantics.

## Durable-teach cost follow-up

The v1.2 performance amendment added same-process, alternating measurements of
the full native rule export and the prefix-filtered export used by the
information-commitment gate. Median full export was 3.362 s; median prefix
export was 180.7 ms across three runs. The prefix measurement is order
sensitive: it took 0.155 ms when called first, but 180.7–224.5 ms after the
full export, which materializes the large rule store. Treat the unstratified
18.6× ratio as descriptive only. The actual gated durable-teach path now
measures 59.5 ms median; all persistence, restart, and replay gates still pass.

An earlier, failed-replay capture measured writer teach at 3.315 s median;
that capture correctly failed on duplicate live nodes and its lock did not
include a direct hash of `information_commitment.py`. It is diagnostic context,
not a preregistered paired speedup estimate. The confirmatory v1.2 lock now
includes the optimized source, every loaded seed manifest, native/Rust/Python
sources, and the performance amendment. The result supports a concrete local
cost reduction but does not claim a controlled end-to-end speedup factor.

This panel covers one authored arithmetic function on one host. The labels and
finite probe domain are harness supplied; exact replay only shows that this
candidate-bound receipt remains internally consistent across restart. It
does not establish acquisition quality, independent label provenance,
conflict behavior between distinct candidates, or broad learning benefit.

Artifacts:

- [Preregistration](SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_PREREG_20261002.md)
- [Amendment](SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_1_AMENDMENT_20261002.md)
- [Performance measurement amendment](SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_2_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_receipt_persistence_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_receipt_persistence_v1_lock_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_receipt_persistence_v1.py)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_receipt_persistence_v1_raw_20261002.json)
- [Export-probe diagnostic capture](../../../evaluation/reports/substrate_adequacy_receipt_persistence_v1_export_probe_diagnostic_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_receipt_persistence_v1_analysis_20261002.json)
