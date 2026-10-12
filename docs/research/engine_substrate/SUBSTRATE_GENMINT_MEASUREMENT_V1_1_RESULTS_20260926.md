# GenMint measurement v1.1 results

**Run date:** 2026-09-26  
**Evidence grade:** current-source, locked full-seed experiment with shared provenance; all six registered semantic gates and 14 independent integrity/semantic checks pass.  
**Change from v1:** provenance and log capture only. The experiment conditions and claim boundary are unchanged.

The v1.1 run reproduced the bounded v1 result: three distinct held-out integer-linear maps were acquired; one six-member shear orbit used one generator and zero quanta versus six quanta with induction disabled; the declared token proxy was 24 versus 12; 400 fixed seeded color assignments minted no linear generators; a held rotation did not induce a generator; a minted generator changed the later unseen member from `minted` to `recognized_transformed`; and a quadratic warp remained outside the linear inducer.

The shared run manifest records the repository and dirty-workspace fingerprints, explicit input hashes, loaded native artifact and build freshness, Python/toolchain/hardware/environment, exact invocation, and parent console-log path/hash/size. The independent analyzer checks the run manifest, matching locked pre/post inputs, log integrity, native/source hashes, and all six outcome gates. Experiment body runtime was **16.1 seconds**; this excludes interpreter/module startup and is not per-case latency or a memory measurement.

This remains end-to-end evidence for an authored 2-D integer-linear family. The MDL value uses the runner's token accounting, and the 400 controls are one finite color-substitution family. No claim follows about natural-task prevalence, general false-mint rates, induction outside this hypothesis class, or acquisition tractability at useful scale.

## Artifacts

- Amendment: [`SUBSTRATE_GENMINT_MEASUREMENT_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_GENMINT_MEASUREMENT_V1_1_AMENDMENT_20260926.md)
- Runner: [`substrate_genmint_measure_v1_1.py`](../../../scripts/substrate_genmint_measure_v1_1.py)
- Lock: [`genmint_measurement_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/genmint_measurement_v1_1_lock_20260926.json)
- Raw capture: [`substrate_genmint_measurement_v1_1_20260926.json`](../../../evaluation/reports/substrate_genmint_measurement_v1_1_20260926.json)
- Independent analyzer: [`analyze_substrate_genmint_measurement_v1_1.py`](../../../scripts/analyze_substrate_genmint_measurement_v1_1.py)
- Analysis: [`substrate_genmint_measurement_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_genmint_measurement_v1_1_analysis_20260926.json)
- Console log: [`substrate-genmint-measurement-v1-1-20260926.stdout_stderr.log`](../../../evaluation/run_logs/substrate-genmint-measurement-v1-1-20260926.stdout_stderr.log)
