# Finite-key closure checker hardening v1.1 results

**Run date:** 2026-09-26  
**Evidence grade:** locked checker/runtime parity probe; all 11 independent checks pass.

Source review found a fail-open edge case in `analyze_mint_termination_fragment.analyze`: empty non-list containers supplied as `rule_specs` or `initial_edges` could be iterated as empty and receive an accepted bound, although the contract requires lists. The analyzer now rejects non-list top-level values explicitly. Four controls cover `{}` and `""` for rules, and `{}` and `null` for edges.

The amended self-check preserves all 11 prior expected outcomes and adds the four malformed-container refusals (15 fixtures total). The recursive finite-key positive rule remains accepted. Under the locked native probe, that rule loads, has the expected access set, reaches `fixed_point`, performs two progressing firings, and yields exactly three nodes and three edges. The independent analyzer validates the fixture outcomes, graph/report semantics, lock stability, manifest/build freshness, native artifact hash, and console-log hash.

This repairs input validation for the analyzer's two top-level collections and confirms one accepted rule still agrees with the native parser/runtime. It does not validate every accepted syntax combination, establish completeness, or change the restricted finite-key closure theorem.

## Artifacts

- Protocol: [`SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_PROTOCOL_20260926.md`](SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_PROTOCOL_20260926.md)
- Checker: [`analyze_mint_termination_fragment.py`](../../../scripts/analyze_mint_termination_fragment.py)
- Locked runner and independent analyzer: [`verify_mint_termination_checker_hardening_v1_1.py`](../../../scripts/verify_mint_termination_checker_hardening_v1_1.py), [`analyze_mint_termination_checker_hardening_v1_1.py`](../../../scripts/analyze_mint_termination_checker_hardening_v1_1.py)
- Lock: [`mint_termination_checker_hardening_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/mint_termination_checker_hardening_v1_1_lock_20260926.json)
- Raw capture and analysis: [`raw`](../../../evaluation/reports/mint_termination_checker_hardening_v1_1_20260926.json), [`analysis`](../../../evaluation/reports/mint_termination_checker_hardening_v1_1_analysis_20260926.json)
