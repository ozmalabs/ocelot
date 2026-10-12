# Finite-key closure rule interaction v2 results

Date: 2026-10-04

## Result

The current-source 126-case replay passed all runner checks. The independent analyzer also passed all 126 exact terminal-graph comparisons, finite-fragment admissions, progress bounds, budget checks, and source-lock checks. Terminal semantics are invariant across ABC, CBA, and BCA installation order in all 14 size/topology cells. The source lock remained stable through capture.

The panel crosses initial size N={4,8,16,32,64,128,256}, directed cycle versus directed path, three fixed rule orders, and three fresh constructions per cell. The rules comprise one link matcher that emits A, a two-edge link/rel matcher that emits B, and a join over A and B that emits C. The conservative fact-progress bounds range from 240–242 at N=4 to 334,896–334,898 at N=256; every native case reports three progressing facts and three completed passes. Median setup, closure, and graph-export wall time rises from 0.404 ms (cycle) / 0.399 ms (path) at N=4 to 3.508 / 3.573 ms at N=256. These times are descriptive, include setup and export, and cover this single sparse rule family only.

## Interpretation and limits

This is direct evidence that one interacting three-rule positive program settles exactly and consistently on two sparse topologies through 256 initial nodes. It does not establish unrestricted termination, analyzer-runtime equivalence for all admitted syntax, performance on dense or high-degree graphs, natural-task prevalence, a general asymptotic exponent, or polynomial cost for arbitrary fixed programs. In particular, the coarse finite-fact bound grows much faster than the observed work; this panel does not tighten that theorem envelope.

## Artifacts

- [Preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_RULE_INTERACTION_V2_PREREG_20261004.md)
- [Runner](../../../scripts/verify_mint_termination_interaction_v2.py)
- [Independent analyzer](../../../scripts/analyze_mint_termination_interaction_v2.py)
- [Source lock](../../../evaluation/substrate_capability/mint_termination_interaction_v2_lock_20261004.json)
- [Compressed raw capture](../../../evaluation/reports/mint_termination_interaction_v2_20261004.json.gz), SHA-256 `e476523e976702fc94cb081f54b80ba9d48b25ae71e83f190f746f103382553d`
- [Independent analysis](../../../evaluation/reports/mint_termination_interaction_v2_analysis_20261004.json)

