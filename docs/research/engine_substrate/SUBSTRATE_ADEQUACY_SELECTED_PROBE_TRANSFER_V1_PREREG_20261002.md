# Selected-probe adoption transfer v1 — preregistration

Date: 2026-10-02

## Question

Does the live selected-probe adoption gate transfer from square/identity to independently authored parity and three-argument clamp families, and does it distinguish informative from aliasing admissible domains in each family?

## Conditions

Each of the following six conditions runs in three fresh processes:

- `parity_correct_broad`: correct parity candidate, always-false challenger, broad signed-integer domain; the selector should choose an even value where predictions differ, adoption should pass all held-outs.
- `parity_alias_wrong`: always-false candidate, parity challenger, odd-only domain; receipt accepts the matching labels, but zero entropy should block adoption.
- `parity_distinguish_wrong`: always-false candidate, parity challenger, mixed domain; a selected even probe should make the truthful label reject the candidate.
- `clamp_correct_broad`: correct three-argument clamp candidate, identity challenger, domain includes below/inside/above-bound values; adoption should generalize.
- `clamp_alias_wrong`: identity candidate, clamp challenger, in-bound-only domain; accepted receipt with zero entropy should not adopt.
- `clamp_distinguish_wrong`: identity candidate, clamp challenger, domain includes out-of-bound values; truthful selected label should reject identity.

All evidence passes through `WorldAdapter.converse` with both authenticated-provider and discriminating-probe policies enabled. The runner uses the independent task oracle and a single test-only provider key. The analyzer independently recomputes selections, signatures, receipts, and held-out oracle scores. Parity and clamp are task families separate from the earlier square/identity gate study; the controls within each family use the same target function and change candidate/domain conditions.

## Limits

This tests transfer across two authored scalar task families on one host. The candidate and challenger Terms, admissible domains, and independent oracle are harness supplied. It does not establish autonomous challenger generation, domain completeness, natural-task coverage, provider truthfulness, or general capability beyond these families.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_selected_probe_transfer_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_selected_probe_transfer_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_selected_probe_transfer_v1.py
```
