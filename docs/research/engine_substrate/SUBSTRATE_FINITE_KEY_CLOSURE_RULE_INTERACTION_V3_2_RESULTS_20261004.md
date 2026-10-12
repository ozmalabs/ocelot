# Finite-key closure rule interaction v3.2 results

Date: 2026-10-04

## Confirmatory replay

The current-source locked runner passed all 180 cases, and the indexed independent monotone-closure analyzer passed all 180 exact normalized node/edge comparisons. All cases were admitted by the finite-key checker with M=3 and E=5, reached native fixed point without budget overshoot, stayed within the computed finite-fact bound, and produced order-invariant terminal graphs across ABC/CBA/BCA in all 20 N/degree cells. Source hashes were stable before and after the runner.

The panel crosses N={32,64,128,256}, circulant out-degree d={1,2,4,8,16}, three rule orders, and three fresh repeats per order. At N=256, median end-to-end time (setup, closure, export) is 3.642, 5.328, 10.223, 29.133, and 108.713 ms for d=1,2,4,8,16. The B-rule join has exactly N·d² matching bindings by construction: 256 through 65,536 across those degrees. This count is independently derivable from the input schema but is not a native candidate counter. Across sizes at d=16, medians are 10.321, 21.306, 40.124, and 108.713 ms for N=32,64,128,256. Progress remains three inserted facts in three passes; that counter does not represent candidate bindings. Some three-repeat tails are noisy (for example, N=256,d=1 has a 32.332 ms maximum against a 3.642 ms median), so timings should guide follow-up design rather than support a wall-time exponent.

## Interpretation and limits

This confirms exact rule interaction on a controlled sparse regular family and quantifies how a growing two-edge join affects observed total runtime. It does not establish a general complexity law, unrestricted closure termination, arbitrary graph behavior, or prevalence of these degree profiles in live workloads. The v3 and v3.1 captures are retained as pilots: v3's initial oracle was impractically slow, and v3.1 had an incorrect expected case-ID template. V3.2 corrects the oracle indexing and factorial assertion under a fresh preregistered source lock; only v3.2 is confirmatory.

## Artifacts

- [Preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_RULE_INTERACTION_V3_2_PREREG_20261004.md)
- [Runner](../../../scripts/verify_mint_termination_interaction_v3_2.py)
- [Independent analyzer](../../../scripts/analyze_mint_termination_interaction_v3_2.py)
- [Source lock](../../../evaluation/substrate_capability/mint_termination_interaction_v3_2_lock_20261004.json)
- [Compressed raw capture](../../../evaluation/reports/mint_termination_interaction_v3_2_20261004.json.gz), SHA-256 `0f5c609ac724796ee9bfcbef48d581092505530969b66de5fa832b696dfee4d0`
- [Independent analysis](../../../evaluation/reports/mint_termination_interaction_v3_2_analysis_20261004.json)

