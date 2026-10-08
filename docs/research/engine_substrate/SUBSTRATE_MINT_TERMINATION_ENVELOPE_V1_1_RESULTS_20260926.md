# Recursive mint termination envelope v1.1 results

**Run date:** 2026-09-26  
**Evidence grade:** locked current-source fixture replay; all 9 independent checks pass.  
**Change from v1:** provenance capture and independent analysis; fixture, arms, sizes, repeats, and progress budget are preserved.

The 18-cell capture compares `add_node` with `add_node_if_absent` over 1, 2, and 4 initial path links, three replicates per cell, and a 32-step progress budget. All nine unrestricted-mint cells hit `progress_budget_reached`; the final graph sizes were 34, 67, and 133 nodes respectively. All nine keyed-deduplication cells reached exact fixture fixed points at 3, 4, and 6 nodes. Median measured closure time was 0.066 ms for unrestricted arms and 0.024 ms for keyed arms. These are tiny fixture timings, not a complexity comparison; the two arms stop at different semantic conditions.

The shared manifest records the current native build, source and protocol hashes, dirty-workspace summary, invocation/environment/hardware, and console log. The independent analyzer passes factorial completeness, the fixture-specific graph/status oracles, source-lock stability, manifest/build freshness, native hash, log hash, and timing sanity checks.

The data confirms that the native runner reports budget exhaustion for this expanding rule and that keyed node deduplication reaches a fixed point on this fixture. It does **not** prove that the unrestricted rule is mathematically nonterminating, that keyed effects terminate generally, or that a weak-acyclicity restriction is enforced. A static guard and a formal complexity/termination argument for the supported effect fragment remain open.

## Artifacts

- Original preregistration: [`SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md`](SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md)
- Amendment: [`SUBSTRATE_MINT_TERMINATION_ENVELOPE_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_MINT_TERMINATION_ENVELOPE_V1_1_AMENDMENT_20260926.md)
- Runner: [`substrate_mint_termination_envelope_v1_1.py`](../../../scripts/substrate_mint_termination_envelope_v1_1.py)
- Lock: [`mint_termination_envelope_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/mint_termination_envelope_v1_1_lock_20260926.json)
- Raw capture: [`substrate_mint_termination_envelope_v1_1_20260926.json`](../../../evaluation/reports/substrate_mint_termination_envelope_v1_1_20260926.json)
- Independent analyzer and analysis: [`analyze_substrate_mint_termination_envelope_v1_1.py`](../../../scripts/analyze_substrate_mint_termination_envelope_v1_1.py), [`analysis JSON`](../../../evaluation/reports/substrate_mint_termination_envelope_v1_1_analysis_20260926.json)
- Console log: [`substrate-mint-termination-envelope-v1-1-20260926.stdout_stderr.log`](../../../evaluation/run_logs/substrate-mint-termination-envelope-v1-1-20260926.stdout_stderr.log)
