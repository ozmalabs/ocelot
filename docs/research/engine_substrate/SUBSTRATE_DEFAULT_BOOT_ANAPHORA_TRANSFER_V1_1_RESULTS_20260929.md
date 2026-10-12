# Default-boot anaphora transfer panel v1.1 results

## Result

Ten fresh, source-locked workers ran five frozen cases each through default
`WorldAdapter()`, `receive_utterance`, and `comprehend`. The independent
analysis passes **13/13 gates**, including all 50 case rows, 10 distinct
processes, unchanged before/after input fingerprints, repeatable complete
graph digests per case, separate adapter timing, and exact semantic controls.
Each positive case passes 10/10: the three-turn `it` chain, `this`, and `that`
all resolve to `question`, with `question` propagated into Intent. Both
negative cases pass 10/10: an unknown antecedent does not bind and a first-turn
`it` remains unresolved.

| Case | Median receive + comprehend wall time | Median adapter initialization |
|---|---:|---:|
| Three-turn `it` chain | 33.29 ms | 29.99 ms |
| `this` transfer | 8.69 ms | 27.56 ms |
| `that` transfer | 8.69 ms | 27.44 ms |
| Unknown-antecedent negative | 8.60 ms | 32.43 ms |
| First-turn unresolved negative | 8.19 ms | 26.96 ms |

Across workers, median total in-process wall time is 261.11 ms, CPU time is
262.20 ms, and peak RSS is 51,628 KiB. The largest final case graph has 1,240
nodes and 1,202 edges. Process launch and source fingerprinting are excluded.
These timing figures include the Python/native API work in each receive and
comprehend call; they are not a native-rule-only latency measure.

## Interpretation and limits

The result extends the earlier two-turn profile from one `it` example to two
additional pronouns, an intermediate-pronoun chain, and explicit non-binding
controls. It supports repeatable operation of this held-structure production
route across these five fixture-derived cases. The cases come from the existing
integration-test family, are not independently authored or held out, and are
not a natural dialogue sample. It does not measure general language
understanding, acquisition, frame locality, or the prevalence of successful
anaphora tasks. Per-case cost is descriptive at this small graph size.

V1's capture is preserved separately. It also passed the semantic oracles, but
combined adapter initialization with case cost; only v1.1 meets the preregistered
timing separation gate.

## Reproducibility

- Protocol: [`SUBSTRATE_DEFAULT_BOOT_ANAPHORA_TRANSFER_V1_PREREG_20260929.md`](SUBSTRATE_DEFAULT_BOOT_ANAPHORA_TRANSFER_V1_PREREG_20260929.md)
- Timing amendment: [`SUBSTRATE_DEFAULT_BOOT_ANAPHORA_TRANSFER_V1_1_AMENDMENT_20260929.md`](SUBSTRATE_DEFAULT_BOOT_ANAPHORA_TRANSFER_V1_1_AMENDMENT_20260929.md)
- Runner and analyzer: [`runner`](../../../scripts/substrate_default_boot_anaphora_transfer_v1_1.py), [`analyzer`](../../../scripts/analyze_substrate_default_boot_anaphora_transfer_v1_1.py)
- Lock: [`input lock`](../../../evaluation/substrate_capability/default_boot_anaphora_transfer_v1_1_lock_20260929.json)
- Raw capture and analysis: [`raw`](../../../evaluation/reports/default_boot_anaphora_transfer_v1_1_raw_20260929.json), [`analysis`](../../../evaluation/reports/default_boot_anaphora_transfer_v1_1_analysis_20260929.json)
