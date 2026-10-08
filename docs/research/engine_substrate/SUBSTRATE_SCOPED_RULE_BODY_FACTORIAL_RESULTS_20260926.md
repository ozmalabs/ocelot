# Scoped rule body factorial results

**Protocol:** [`SUBSTRATE_SCOPED_RULE_BODY_FACTORIAL_PREREG_20260926.md`](SUBSTRATE_SCOPED_RULE_BODY_FACTORIAL_PREREG_20260926.md)  
**Runner:** [`substrate_scoped_rule_body_factorial_v1.py`](../../../scripts/substrate_scoped_rule_body_factorial_v1.py)  
**Independent analysis:** [`substrate_scoped_rule_body_factorial_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_rule_body_factorial_v1_20260926_analysis.json)

All 60 cells pass the registered integrity and semantic checks: exact active/slot counts, fixed point with zero progress, unchanged state, and zero candidate, Term, and audit work. Five fresh repeats were measured per cell.

Paired factorial contrasts show both dimensions matter, and both costs grow with active rule count. Raising match edges from one to eight adds a median 3.1, 10.1, and 19.8 μs/call at 64, 256, and 512 active rules. Raising effects from one to eight adds 5.5, 22.3, and 52.9 μs/call. The edge contrast's p10–p90 repeat range is 1.4–8.3, 7.3–10.5, and 14.0–22.2 μs; the effect contrast's is 2.0–10.7, 18.1–25.9, and 51.0–54.3 μs. The interaction median is positive (2.0, 10.8, 17.5 μs) but noisy, so do not treat it as established non-additivity.

The effect axis is the stronger setup-cost signal, consistent with work proportional to copied rule payload; the pattern axis also adds matcher setup. These contrasts still combine cloning, vector/reference construction, and matcher setup, and therefore are not clone-time measurements. At 512 rules, eight effects increase no-op time by about 53 μs/call over one effect, while eight edges add about 20 μs/call.

**Next:** add an isolated native timing diagnostic for the active-rule snapshot clone (with audit mode off in ordinary calls and no semantic path changes), compare its measured cost to the end-to-end effect-axis increment, and then decide whether snapshot reuse is worth mutation-invalidation complexity. The current evidence is synthetic and does not establish costs for the production rule-body distribution.
