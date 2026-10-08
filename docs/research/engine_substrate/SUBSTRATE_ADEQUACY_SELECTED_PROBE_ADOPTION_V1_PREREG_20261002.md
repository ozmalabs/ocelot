# Challenger-selected probe adoption gate v1 — preregistration

Date: 2026-10-02

## Question

Can the strict example-adoption boundary recompute and require a target-blind probe selection that separates the candidate from a supplied challenger, thereby refusing alias-only evidence before adoption?

## Gate

`WorldAdapter(require_discriminating_code_example_probe=True)` implies strict provider authentication. Before `_teach_shape`, the shared adoption function recomputes `select_disagreement_probe` from the candidate Term, challenger Terms, acquisition rows, admissible domain, and selector seed. It requires exact selection-record parity, positive prediction entropy, exactly one request probe equal to the selected input, and request acquisition/domain/seed hashes bound to the selection record. Provider signatures and the existing accepted-receipt check remain required.

## Conditions

Four conditions run in three fresh processes each:

- `honest_selected_square`: square candidate, identity challenger, domain `{x=0,x=2}`, truthful label at selected `x=2`; adopt and pass three held-outs.
- `alias_zero_entropy`: identity candidate, square challenger, domain `{x=0}`; truthful signed label and accepted receipt, but entropy is zero, so refuse adoption.
- `distinguishing_identity_truth`: identity candidate, square challenger, domain `{x=0,x=2}`, truthful label at selected `x=2`; receipt rejects identity, with no adoption.
- `selected_wrong_signer`: identity candidate, square challenger, broad domain `{x=0,x=2}`, trusted signer falsely labels selected `x=2` as 2; selection entropy is positive and the receipt accepts identity. This is expected to remain a false adoption, showing the boundary of the selection gate.

All conditions use a fixed square oracle, a test-only trusted key, and three fresh worker processes. The analyzer independently recomputes selections, verifies HMACs and receipts, checks typed code-shape deltas, and scores held-out inputs `x=3,4,5`.

## Limits

The challenger set and admissible domain are supplied by the caller. The gate only ensures separation from the supplied challengers within that supplied domain; it cannot establish challenger-set completeness, real-world domain coverage, provider truthfulness, or operator independence. The wrong-signer condition is adversarial and does not estimate natural error rates.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_selected_probe_adoption_v1.py
```
