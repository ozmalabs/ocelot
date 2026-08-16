# Hate passion × resentment-debt coupling — RESULTS

Registered design: `HATE_RESENTMENT_PASSION_COUPLING_PREREG.md`. **All 4
predictions confirmed.** Building this rung surfaced and fixed a real
effect-ordering bug — reported honestly in Sec3.

## 1. Live run (`scripts/hate_resentment_passion_coupling_demo.py`)

```
=== Prediction 3 (residue check): resentment_debt matches the residue exactly ===
streak after exception=0.5000 resentment_debt=0.5000 (should match)

=== Prediction 4: resentment_debt accumulates across multiple exceptions ===
after exception 1: resentment_debt=1.0000
after exception 2: resentment_debt=2.0000 (should be roughly double)

=== Predictions 1/2/3: effective_removal_alpha, zero vs nonzero debt (arousal held equal) ===
zero resentment_debt: effective_removal_alpha=0.6000 (expect base_alpha*(1+arousal)=0.6000)
resentment_debt=1.0:  effective_removal_alpha=1.2000 (expect base_alpha*(1+arousal)*(1+debt)=1.2000)
```

## 2. Predictions

1. **At zero `resentment_debt`, `effective_removal_alpha` is unchanged**
   from the arousal-only (`v1.1.0`) formula — `PASS`. `0.6000` matches
   `base_alpha*(1+arousal)` exactly.
2. **A history WITH accumulated `resentment_debt` produces a HIGHER
   `effective_removal_alpha`, holding crystallization-time arousal
   equal** — `PASS`. `1.2000 > 0.6000`, same arousal (`1.0`) in both
   runs, isolating `resentment_debt`'s own contribution.
3. **The formula matches exactly** — `PASS`. `1.2000` matches
   `base_alpha*(1+arousal)*(1+debt) = 0.3*2.0*2.0` to 4 decimal places.
4. **`resentment_debt` accumulates across multiple `specific_act`
   incidents** — `PASS`. Two identical exceptions leave `1.0000` then
   `2.0000` — monotonically accumulating, never decremented, per-target
   isolation confirmed separately in the test suite.

## 3. A real bug found and fixed before finalizing

The first live check of `resentment_debt` produced `0.25` where the
formula predicted `0.5` (`confirm_streak(1.0) * retained_fraction(0.5)`).
**Root cause**: `derive_hate_attribution`'s effects list applies
progressively, not as a single atomic snapshot-computed batch — an
effect later in the list can see an EARLIER effect's already-written
value within the SAME rule firing (the identical affordance this
codebase's `identity_field <- identity_field + 1` precedent already
relies on intentionally elsewhere). `resentment_debt`'s own effect was
listed AFTER `confirm_streak`'s effect, so its residue read saw
`confirm_streak` ALREADY overwritten to its post-reset value (`0.5`),
computing `0.5 * 0.5 = 0.25` instead of the intended `1.0 * 0.5 = 0.5`.

**Fixed** by reordering the two effects — `resentment_debt`'s update now
runs BEFORE `confirm_streak`'s, so its residue read sees the correct
pre-reset value. Verified directly: `resentment_debt == confirm_streak`
after a single exception from a zero-debt start, exactly as the shared
residue formula requires. This is a real instance of the SAME
ordering-sensitivity class of issue this arc already found once before
(`HATE_THRESHOLD_LOWER_BOUND_COUPLING_RESULTS.md`'s arousal-update
ordering bug) — caught here by measuring before finalizing rather than
trusting the formula's algebra alone.

## 4. Honesty notes

**Does establish**: the crystallizing incident's removal motive is now
amplified by TWO independent channels — momentary arousal (Sternberg's
passion) and accumulated, never-decaying resentment (McCullough, Fincham
& Tsang 2003's unforgiveness persistence) — composed multiplicatively,
each confirmed to contribute its own measurable, isolated amplification.
Also surfaced a second real instance of effects-list order-sensitivity in
this rule family, fixed and documented rather than patched around.

**Does NOT establish**: any decay for `resentment_debt` — a deliberate
reading of the cited literature (unforgiveness does not fade the way
ordinary affect does), not an oversight; a future rung could register a
separate, much slower decay if warranted. Does NOT independently
validate the multiplicative (rather than additive) composition of the
two channels against real data beyond the citations' structural claims.

## 5. Files

- `docs/research/psychology_affect/HATE_RESENTMENT_PASSION_COUPLING_PREREG.md`
- `docs/research/psychology_affect/HATE_RESENTMENT_PASSION_COUPLING_RESULTS.md` (this file)
- `domains/hate_attribution.py` (edited: `resentment_debt` init + read, two-channel `effective_removal_alpha`)
- `scripts/_build_hate_attribution_seed.py` (edited: `_new_resentment_debt_term`, `_residue_term` factored out, effect-order fix, v1.5.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/hate_resentment_passion_coupling_demo.py` (new)
- `tests/test_hate_resentment_passion_coupling.py` (5/5, new)
