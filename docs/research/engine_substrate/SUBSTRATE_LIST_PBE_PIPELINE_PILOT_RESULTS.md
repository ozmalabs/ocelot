# Full P4 list PBE route diagnostic (2026-09-25)

**Run state:** discovery diagnostic on previously inspected task family; not confirmatory. Protocol note: [`SUBSTRATE_LIST_PBE_PIPELINE_PILOT_NOTE_20260925.md`](SUBSTRATE_LIST_PBE_PIPELINE_PILOT_NOTE_20260925.md). Corrected raw record: [`substrate_list_pbe_pipeline_instrumented_replication_20260925.json`](../../../evaluation/reports/substrate_list_pbe_pipeline_instrumented_replication_20260925.json). Initial instrumentation record: [`substrate_list_pbe_pipeline_pilot_20260925.json`](../../../evaluation/reports/substrate_list_pbe_pipeline_pilot_20260925.json).

## Result

The unmodified `synthesize_from_request` path ran each of the 22 tasks on a fresh main-arm substrate, with a descriptive request and four revealed examples. External scoring used the three held-out examples. The corrected report reproduces every task outcome from the initial run.

Thirteen tasks were accepted and exactly matched all held-out outputs (13/22, 59.1%; descriptive Wilson 95% interval 38.7–76.7%); three more were accepted but failed at least one held-out row; six ended in a gap. Thus the route accepted 16/22 (72.7%; descriptive Wilson 95% interval 51.8–86.8%) but its held-out exact-pass result was 13/22. This is descriptive only: the family and direct-search results were already known before this end-to-end diagnostic.

The read-back shows two operating paths. Thirteen tasks were accepted through exemplar retrieval: ten passed holdout and three overfit. The retrieval rung labels among those accepted were `a` (1), `c` (1), and `d` (11); the three holdout failures were all retrieval-rung `d`. Nine tasks reached `SynthEnumerate`: two filter tasks and the product task were accepted and passed holdout, while six tasks gapped at the 200,000-candidate cap. Three of those six also show a codebook construction attempt before enumeration; that attempt did not yield a held-out-validated solution.

Total end-to-end wall time was 5.42 s, including 0.62 s summed substrate/codebook boot and 4.70 s summed request-to-outcome route time. Per-task route latency had a 89.7 ms median, 591.5 ms p90, and 802.7 ms maximum. Process peak RSS was 340,364 KiB across imports and all tasks. The two false-accept sources are concrete: exemplar retrieval can select an example-compatible program that does not implement the stated task, and the route's accept verdict is based on revealed examples; held-out checks are external evaluation, not an in-path guard.

## Measurement correction and limits

The first harness pass omitted `retrieval` and `construction` read-back from its summary. Its raw record is preserved. The corrected harness added those existing `read_goal` fields and repeated the same 22 cases; all outcomes matched exactly. Its report carries hashes for the harness, suite, adapter, seed, native synthesizer, build, lockfile, and protocol. This post-observation correction is documented and does not turn the result into confirmatory evidence.

Compared with the direct-search pilot (14/22 typed-default, 16/22 fixed-grammar), the full route achieved 13/22 exact held-out passes. These are not a controlled causal comparison: the end-to-end arm includes request recognition, retrieval, codebook/rung policy, adapters, and a different effective grammar path. No conclusion about relative efficacy should be drawn from the raw score difference.

This experiment identifies capability and cost on a small list-PBE family. It does not establish task prevalence, residual frequency on natural workloads, mint/adoption, cross-task reuse, retention, general transfer, or scaling. The next E2 gate is a newly generated, independently frozen family and prompt set, with a pre-run lock and an explicit baseline/ablation plan; that confirmatory family should retain separate per-rung, holdout, and full acquisition-cost reporting.
