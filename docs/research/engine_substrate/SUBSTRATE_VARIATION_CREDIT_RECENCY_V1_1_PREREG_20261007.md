# Variation credit v1.1 (recency window): sequential-shift panel — preregistration (2026-10-07)

Follows [v1 results](SUBSTRATE_VARIATION_CREDIT_ADOPTION_V1_RESULTS_20261006.md). Those results found stale credit hurt held-out concerns after a same-kind shift (8.9 adopted vs 20.6 frozen).

## Change under test

`seeds/variation_credit.json` v1.1.0. Each credit is stamped with a sequence number. `VariationCredit.trials`/`supports` count only the last `VariationPolicy.window` credits of that (op, kind). The seed default is `window = 4`; an absent window gives the v1.0.0 behaviour (unbounded history).

`variation_pick` is unchanged.

## Same authored experiment world as v1

Each concern has one hidden fixing family; a trial is supported iff it tries that family. Family menus, scoring (`S = 100·(1 − (k−1)/(M−1))`, 0 if unfixed) and the harness are unchanged.

## Panel A — sequential shift (primary)

Four same-kind shift pairs, using v1's distributions: d1→d2 (reply_fix), d3→d4 (performance), d5→d6 (comprehension), d7→d8 (instruction).

For each pair, 30 paired replicate sequences (seed 20261007). Each sequence runs one substrate through:

- 8 episodes from A;
- then 8 from B (adaptation);
- then 4 from A again (return).

Arms, paired on the identical sequence of hidden fixing families:

- **frozen:** `use_credit = 0`
- **unbounded:** v1 credit, window absent
- **window4:** v1.1 default

Per sequence, record the mean score in each phase.

**Gates (all must hold):**

- **G1 (adaptation).** Phase-B mean, window4 − unbounded, pooled across the 4 pairs (120 sequences): paired mean Δ > 0, with 10,000-resample paired-bootstrap lower CI > 0.
- **G2 (no shift harm).** Phase-B mean, window4 − frozen: paired bootstrap upper CI > 0. The point estimate need not be positive, but window4 must not be confidently worse than frozen.
- **G3 (whole-sequence benefit).** Mean over all 20 episodes, window4 − frozen: lower CI > 0.

Reported, not gated: the same comparisons per pair, and phase-A′ retention.

## Panel B — v1 held-out gate repeated with window4

Rerun v1's 12-distribution gate unchanged, except the adopt arm uses window4 (`evaluation/substrate_capability/variation_credit_adoption_v1.py` logic, new output file). The gate is the same as v1's: ≥ 8/12 improve, 0 harm, aggregate Δ ≥ 5 with lower CI > 0, byte-identical rollback.

## Not tested

Context conditioning. The authored world has no concern features beyond kind, so the shift is unobservable and only recency can help.
