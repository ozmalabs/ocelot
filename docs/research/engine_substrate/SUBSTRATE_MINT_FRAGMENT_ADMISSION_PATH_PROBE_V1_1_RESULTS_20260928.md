# Finite-key fragment admission-path probe v1.1 results

**Run date:** 2026-09-28  
**Evidence grade:** source-locked, three-worker runtime path probe; runner gates and all 10 independent analysis checks pass.  
**Question:** do four current rule creation/revision paths enforce the finite-key termination fragment before a rule becomes live?

## Result

The independent finite-key checker rejects the fixture in every worker because it uses fresh `add_node`. The native runtime nevertheless accepts it through every tested path:

| Route | Accepted by runtime | Repeats | Observed outcome |
|---|---:|---:|---|
| Direct `add_rule` authoring | Yes | 3/3 | One live rule installed |
| `import_rules` checkpoint load | Yes | 3/3 | One live rule restored |
| Rule-patch revision | Yes | 3/3 | Valid revision/hash CAS advances the effect body from safe `add_node_if_absent` to fresh `add_node`, revision 0→1 |
| Graph-resident `SetRuleClause("__mint__")` self-mint | Yes | 3/3 | One out-of-fragment rule compiled into the live struct rule store |

The self-minted rule has a deliberately absent match edge. The explicit `graph_then_struct` cycle reports one progressing step for the minter, while the forbidden fresh-node effect itself is never run. Three fresh PIDs produce identical route coverage; each worker and the parent retain the same 15-file source/native lock. The native build manifest reports no stale Rust inputs.

## Interpretation

This confirms an admission gap on these four concrete paths: passing the standalone checker is not a precondition for direct authoring, restore, valid CAS revision, or graph self-mint. The probe does not execute closure on an out-of-fragment program, show that any route causes nontermination, or exhaustively enumerate every low-level Rust constructor. Revision/hash CAS still supplies stale-write protection; it does not preserve finite-key membership. A future admission guard must validate the final rule body after parsing or revision and before it becomes live, and must cover imports and self-mint in addition to direct authoring.

## Capture history and limitations

V1's failed capture is retained. Direct authoring, import, and patch each accepted in 3/3 workers, but its graph-self-mint arm used the default cycle plan on a no-seed substrate and therefore did not dispatch graph-resident rules. V1.1 changes only this arm to the explicit `graph_then_struct` plan; v1 is not counted as confirmatory evidence. One v1.1 setup worker was also retained as an unscored pilot. Its first output accidentally included hashes of all 307,510 seed JSON files even though the fixture passes `seeds=()`; it is gzip-preserved and excluded. The locked v1.1 result hashes only the route-relevant boot, parser, cycle, engine, checker, protocol, runner, analyzer, build manifest, and native extension inputs.

## Reproduction and custody

- Base preregistration and v1.1 correction: [`preregistration`](SUBSTRATE_MINT_FRAGMENT_ADMISSION_PATH_PROBE_V1_PREREG_20260928.md), [`amendment`](SUBSTRATE_MINT_FRAGMENT_ADMISSION_PATH_PROBE_V1_1_AMENDMENT_20260928.md)
- Runner: [`substrate_mint_fragment_admission_path_probe_v1_1.py`](../../../scripts/substrate_mint_fragment_admission_path_probe_v1_1.py)
- Independent analyzer: [`analyze_substrate_mint_fragment_admission_path_probe_v1_1.py`](../../../scripts/analyze_substrate_mint_fragment_admission_path_probe_v1_1.py)
- Lock: [`mint_fragment_admission_path_probe_v1_1_lock_20260928.json`](../../../evaluation/substrate_capability/mint_fragment_admission_path_probe_v1_1_lock_20260928.json)
- Raw capture: [`substrate_mint_fragment_admission_path_probe_v1_1_20260928.json`](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_20260928.json)
- Independent analysis: [`substrate_mint_fragment_admission_path_probe_v1_1_analysis_20260928.json`](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_analysis_20260928.json)
- Failed v1 raw/analysis and compressed unscored pilot are linked in the v1.1 amendment.
