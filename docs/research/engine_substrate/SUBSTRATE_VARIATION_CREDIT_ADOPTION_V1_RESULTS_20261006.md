# Outcome-credited variation policy: held-out adoption gate v1 — results (2026-10-06)

Protocol: [preregistration](SUBSTRATE_VARIATION_CREDIT_ADOPTION_V1_PREREG_20261006.md). Raw: [`variation_credit_adoption_v1_20261006.json`](../../../evaluation/reports/variation_credit_adoption_v1_20261006.json).

## Outcome

All gates passed. The substrate's own variation policy, learned by graph
rules from the outcomes of earlier improvement experiments, made later
improvement episodes succeed with fewer experiments on held-out concerns.

| Gate | Result |
|---|---|
| ≥ 8/12 distributions improve | 9/12 |
| 0 harm | 0 |
| Aggregate mean Δ ≥ 5, lower CI > 0 | +39.4, lower CI 22.3 |
| Non-improve proposals roll back byte-identically | 3/3 |
| Sources stable during capture | yes |

| d | kind | pre | adopt | Δ | 95% CI | class |
|---|---|---:|---:|---:|---|---|
| 1 | reply_fix | 18.3 | 87.2 | +68.9 | 46.7–86.7 | improve |
| 2 | reply_fix | 20.6 | 91.1 | +70.6 | 57.8–80.6 | improve |
| 3 | performance | 33.9 | 90.6 | +56.7 | 46.7–64.4 | improve |
| 4 | performance | 48.3 | 81.7 | +33.3 | 22.2–43.3 | improve |
| 5 | comprehension | 60.6 | 90.6 | +30.0 | 25.0–33.9 | improve |
| 6 | comprehension | 27.2 | 70.6 | +43.3 | 20.6–65.0 | improve |
| 7 | instruction | 82.4 | 93.8 | +11.4 | 6.7–14.3 | improve |
| 8 | instruction | 18.6 | 97.6 | +79.0 | 69.0–85.7 | improve |
| 9 | reply_fix | 9.4 | 85.6 | +76.1 | 73.3–78.9 | improve |
| 10 | performance (uniform) | 52.2 | 50.0 | −2.2 | −8.9–3.3 | inconclusive |
| 11 | comprehension (default already right) | 87.8 | 91.7 | +3.9 | −1.7–10.0 | inconclusive |
| 12 | instruction (uniform) | 50.5 | 51.9 | +1.4 | −9.5–11.9 | inconclusive |

The three controls came out inconclusive, as preregistered.

## What changed

- `seeds/variation_ops.json` v1.5.0. `variation_pick` reads an optional
  `VariationPolicy` node. With none present, the choice is unchanged; the gate
  tests and `test_agent_authors_new_rule_migrated.py`'s pick tests pass.
- `seeds/variation_credit.json` (`self_load_only`, so it is not swept into
  full-corpus boots). It provides the policy node and two rules:
  - judged Experiments are credited to `VariationCredit{op, kind}`;
  - `trials`/`supports` are derived counts over the credited deltas.
- `_compose_experiment_rule` stamps `variation_op` and `concern_key` on each
  delta. This is a mechanical copy of the Program's verdict.
- `exclude_refuted` drops a family already refuted for the same concern.
  Without the policy, the existing pipeline would choose the same family
  again on a retry.
- Tests: `tests/test_variation_credit_migrated.py` (8 pass).

## Limits found

- **Stale credit hurts under a shift.** After training on d1 only, held-out
  d2 concerns (same kind, different fixing family) scored 8.9 adopted versus
  20.6 frozen. Training on d1 then d2 left d1 at 46.1 versus 18.3: still
  better than frozen, but half the benefit of d1-only training. Credit has no
  recency or context beyond concern kind, so this is real harm a deployed
  version must handle. It is a descriptive extra, not a preregistered gate.
- **The experiment world is authored.** Each concern has one hidden fixing
  family, and outcomes are exact. No child dispatch, real judge or noise is
  measured.
- **Not P3-E1.** This applies P3-E1's statistics only. Custody, independent
  evaluation, real toy domains and retention across sequential shifts are
  absent.
- The policy itself is authored graph data. The substrate learns credit
  values, not the form of the credit rule.
