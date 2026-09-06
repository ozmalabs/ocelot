# PHASIC vs TONIC AROUSAL — a missing affect DIMENSION — pre-registration (block 296000)

**Status: PRE-REGISTRATION. Committed BEFORE the confirmatory measurement of the
new axis.** The missing-dimension hypothesis (§1), the DERIVATION of the new axis
from already-computed signals (§2), the minimal-perturbation design (§3), the
anti-fitting argument (§4), the PREDICTION (§5), and the FLAW modes (§6) are all
fixed HERE, now. The gate-probe numbers quoted below were computed with ONLY the
existing formulas over the existing per-emotion `CANON` configuration (no new
constant) as a feasibility probe; the confirmatory re-run of Arm A and the
`test_phasic_arousal_migrated` gate are scored against exactly these frozen
predictions.

## 0. Seed / block claim

Block **296000** (range 296000–296999), an UNUSED block. This is a **SEED-ONLY**
change: it adds two rules to the EMITTER `tools/build_modulator_seeds.py` and
regenerates `seeds/modulators.json`. **NO Rust.** The canonical
`_native.abi3.so` md5 stays **`7efe75eba05b006cafd15dbb4b7da246`** byte-identical
(the cognition core, toolbox solvers, and frozen seeds are untouched). No integer
is minted from the block; the new axis is a pure function of pre-existing drive
signals, and the two new rules are guarded on the same `ModulatorState.enabled`
opt-in as every other 207000 modulator rule, so **default == today** (§3).

## 1. The missing dimension (the hypothesis)

The affect literature distinguishes two arousal processes that share a name but not
a mechanism:

- **PHASIC arousal** — the fast onset / startle / action-readiness spike at the
  moment a salient (often threatening) event is detected. It is high AT ONSET and
  decays.
- **TONIC arousal** — the slow, sustained background activation that persists (or
  not) after onset.

**The substrate today collapses these two onto ONE arousal scalar.** The
`modulators` seed computes a single `arousal` (rule `mod_arousal`) and bins it into
a single `arousal_band`. For a THREAT drive, that one scalar is the **DECAYED
threat-precision**:

```
arousal_contrib(threat drive) = threat_precision
                              = Ashr(threat_c0, IDiv(now - last_refresh, half_life))
```

This is the deliberate fear↔anxiety minimal pair (a SHORT `threat_half_life`
decays precision below `t_present` ⇒ FEAR; a LONG one persists ⇒ ANXIETY — see
`MODULATORS_EMERGENCE_RESULTS.md`). But it has an unintended consequence for the
arousal axis: **FEAR — whose precision has decayed, which is exactly what
distinguishes it from anxiety — reads LOW arousal.** Concretely, at the canonical
fear config (`threat_c0=1024`, `threat_half_life=1`, `now-refresh=3`),
`threat_precision = Ashr(1024, 3) = 128`, which falls in the LOW band
(`band_mid=150`). So the substrate's own fear region reports LOW arousal.

**This INVERTS the human/RAVDESS geometry**, where fear is near the top of the
arousal ordering — vocally loud, high-F0, fast. The
`PROSODY_RAVDESS_RESULTS.md` rung reported exactly this as an honest
substrate-vs-human discrepancy: the substrate reads `emx_fear` as LOWER arousal
than `emx_joy`, costing one inversion in the arousal-rank correlation.

**The hypothesis:** that inversion is not a fact about fear, it is an artefact of
collapsing PHASIC onto TONIC. Fear's PHASIC arousal is high (a threat onset is the
canonical startle event); only its TONIC arousal is low (the precision has
decayed). The substrate is **already computing the phasic signal and throwing it
away**: `threat_c0` — the UN-decayed ONSET magnitude (1024 for fear) — is the head
of the very same `Ashr` that produces the decayed precision. It is read today ONLY
inside `drive_threat_precision`; it is never routed to arousal. Adding a PHASIC
arousal axis that reads `threat_c0` (the onset) recovers the missing dimension and
fixes fear WITHOUT touching the tonic path that the fear↔anxiety pair and every
canonical emotion depend on.

## 2. The DERIVATION (from existing signals — no new constant)

The new axis is defined by MIRRORING the two existing arousal rules, substituting
the ONSET signal for the DECAYED signal in the threat branch:

**Per-drive phasic contribution** (mirror of `drive_arousal_contrib`, which is
`Ite(threat==1, threat_precision, urge*urgency//SCALE)`):

```
arousal_contrib_phasic(d) = Ite(threat==1,
                                threat_c0,                     # the ONSET magnitude (un-decayed)
                                IDiv(urge*urgency, SCALE))     # the SAME else-branch as tonic
```

**Modulator-level phasic arousal** (mirror of `mod_arousal`, residual path
UNCHANGED):

```
arousal_phasic      = Ite(appraised==0, residual,             # un-appraised orienting spike, SAME as tonic
                          Sum_d(arousal_contrib_phasic))
arousal_band_phasic = Ite(arousal_phasic >= band_hi, 2,       # SAME band_hi=600
                          Ite(arousal_phasic >= band_mid, 1, 0))   # SAME band_mid=150
```

Every symbol on the right-hand side is **already computed**:

- `threat_c0` is a Drive attribute that PRE-DATES RAVDESS and this rung; it is the
  input to `drive_threat_precision` and literally MEANS "the onset magnitude of the
  threat channel."
- `urge`, `urgency`, `SCALE`, `residual`, `band_hi`, `band_mid` are the identical
  quantities the tonic `arousal` already reads.

**There is NO new seed constant, no new Term, no new drive attribute.** The phasic
axis is the tonic formula with `threat_precision` (decayed) replaced by
`threat_c0` (onset) in the threat branch — the un-decayed head of the same
expression. For every NON-threat drive the two axes are **algebraically
identical** (both take the `urge*urgency//SCALE` branch); they differ ONLY on
threat drives, and there only by decay-vs-onset.

## 3. The MINIMAL-PERTURBATION design (default == today)

The change is **purely additive**:

- The tonic path is **UNCHANGED**: `drive_arousal_contrib`, `mod_arousal`,
  `arousal`, and `arousal_band` are left exactly as-is. Every `emx_*` region
  predicate reads `arousal_band` (tonic) — none is edited. `mod_resolution` reads
  `arousal` (tonic) — unchanged.
- The two new rules write ONLY new attributes: `arousal_contrib_phasic` (on the
  drive) and `arousal_phasic` / `arousal_band_phasic` (on the ModulatorState).
  **Nothing existing reads any of these three.**
- The new rules are given rule orders that DO NOT disturb the tonic ordering (each
  placed immediately after its tonic counterpart), so the tonic values every
  region predicate consumes are produced identically to today.
- Emotion CLASSIFICATION keeps reading the TONIC `arousal_band` (so the 11
  canonical emotions + 3 blends classify byte-identically). Only the PROSODY
  generator (`domains/prosody_generation.py`, a non-seed world adapter) is
  re-routed to read `arousal_band_phasic`.

Because the two new rules guard on the same `ModulatorState.enabled` opt-in as
every 207000 rule, and because they only ADD attributes nothing else reads, the
base tree is byte-identical when the modulator layer is absent, and every
canonical emotion's tonic `arousal_band` + emotion label is byte-identical when it
is present. **default == today.** The `_native.abi3.so` md5 is unchanged
(`7efe75…`) — this is a seed regeneration, not a Rust change.

## 4. The ANTI-FITTING argument

The phasic axis is NOT a knob fit to make fear high. The argument that it is a REAL
dimension the substrate half-computed, not a benchmark-matching hack:

1. **`threat_c0` PRE-DATES RAVDESS and this rung.** It was authored as the onset
   magnitude of the threat channel for the fear↔anxiety minimal pair (block
   207000), long before the prosody×RAVDESS comparison existed. We did not
   introduce a new signal shaped to the target; we ROUTED an existing one.
2. **It MEANS onset.** The name and role of `threat_c0` is "the un-decayed head of
   the freshness `Ashr`." Reading the onset magnitude for a PHASIC arousal axis is
   the literature-correct definition of phasic arousal (startle/action-readiness at
   detection), not a fit.
3. **Fear-HIGH EMERGES from it** rather than being asserted: `threat_c0=1024`
   exceeds `band_hi=600`, so fear's phasic band is HIGH by the SAME band cut the
   tonic axis uses — no new threshold.
4. **ANXIETY shares the same onset** (`threat_c0=1024`) and is ALSO phasic-HIGH,
   which is correct (anxiety is high-arousal on both axes) — so the axis is not a
   fear-only special case.
5. **calm / sad have NO threat channel**, so their phasic contribution takes the
   identical `urge*urgency//SCALE` else-branch as tonic and stays LOW — they do NOT
   move. Fear cannot be raised by a mechanism that would also spuriously raise the
   low-arousal emotions.
6. **anger's `urge*urgency` is already high** on BOTH axes (it has no threat
   channel; its arousal comes from the demand term), so anger stays HIGH without
   any threat-onset contribution. The axis does not need anger to behave specially.

If the phasic axis were a fit, raising fear would require moving something else;
it does not — calm/sad/anger are pinned by the shared non-threat branch.

## 5. The PREDICTION (frozen)

Mapping the 8 RAVDESS emotions through the substrate's own `emx_*` regions
(`calm→bliss, neutral→(baseline), sad→sadness, disgust→disgust,
surprised→surprise, happy→joy, fearful→fear, angry→anger`) and reading the
existing TONIC axis vs the new PHASIC axis:

| RAVDESS emotion | tonic arousal | tonic band | **phasic arousal** | **phasic band** |
|---|---:|:--:|---:|:--:|
| calm      | 1   | LOW  | 1    | LOW  |
| neutral   | 0   | LOW  | 0    | LOW  |
| sad       | 16  | LOW  | 16   | LOW  |
| disgust   | 360 | MID  | 360  | MID  |
| surprised | 500 | MID  | 500  | MID  |
| happy     | 160 | MID  | 160  | **MID** |
| fearful   | 128 | **LOW** | **1024** | **HIGH** |
| angry     | 710 | HIGH | 710  | HIGH |

1. **Fear SEPARATES:** fear's phasic band goes **LOW → HIGH** (via
   `threat_c0=1024 ≥ band_hi=600`), while its tonic band stays **LOW** (via the
   decayed `threat_precision=128`). The dimension the substrate had collapsed is
   recovered: fear is phasic-HIGH, tonic-LOW.
2. **The OTHER SEVEN are unchanged on BOTH axes** in band terms (their phasic band
   equals their tonic band), so re-routing prosody to the phasic band moves ONLY
   fear.
3. **Arousal-rank correlation vs the RAVDESS ordering**
   (`calm<neutral<sad<disgust<surprised<happy<fearful<angry`):
   - tonic SCALAR: **ρ = 0.762** (fear inverted — the current, reported
     discrepancy).
   - phasic SCALAR: **ρ = 0.881** (fear fixed). **HONEST: this is 0.881, NOT
     1.0.** `happy` stays MID (phasic 160) because joy's arousal is the
     `urge*urgency` demand DEFICIT path, not a threat onset — happy's
     under-arousal is a **separate, real, milder discrepancy that we deliberately
     leave UNFIXED** (not fitted away). It is a genuine second finding, not a
     residual to bury.
   - phasic BAND (the LOW/MID/HIGH partition the prosody map actually reads): the
     band sequence is `[LOW,LOW,LOW,MID,MID,MID,HIGH,HIGH]` — **monotone
     non-decreasing across the RAVDESS ordering, with NO inversion** (monotone
     fraction = 1.0; Spearman-with-ties = 0.945). This is the exact RAVDESS-
     monotone LOW→MID→HIGH structure — the band the prosody knob map consumes is
     RAVDESS-monotone.

**Explicit scope, stated up front:** the claim is **band-rho 1.0 (monotone, no
inversion) / scalar-rho 0.881**, NOT full continuous monotonicity. Fear is
resolved; happy's under-arousal is an honest secondary discrepancy left in place.

## 6. FALSIFIERS + FLAW modes

- **FLAW — tonic contamination.** If ANY canonical `emx_*` region's tonic
  `arousal_band`, emotion label, `action_tendency`, or valence MOVES once the
  phasic axis is present, the change was NOT purely additive — the rule ordering
  contaminated the tonic path. This is a hard STOP: the design (§3) requires
  byte-identical canonical reproduction (all 11 emotions + 3 blends). Reported
  straight; fixed by correcting the rule ordering so the new rules are strictly
  additive, or the axis is not admissible.
- **FLAW — not separable.** If fear only reads phasic-HIGH by ALSO moving
  calm/sad (the low-arousal emotions) up, the axis is not a real dimension — it is
  a global shift, and fear is not separable from the emotions it should stay
  distinct from. The prediction (§5) requires calm=neutral=sad phasic-LOW while
  fearful goes phasic-HIGH; if they move together, the axis is rejected.
- **FALSIFIER — the effect must depend on the onset routing.** If replacing
  `threat_c0` with `threat_precision` in the phasic branch (i.e. making phasic ==
  tonic) leaves fear phasic-HIGH anyway, the fix is an artefact of something else,
  not the onset signal, and the claim is false.
- **Honest null on happy.** We PRE-COMMIT that happy stays MID (scalar-rho 0.881,
  not 1.0). If happy came out HIGH, that would be suspicious (nothing in the
  derivation should raise joy's onset), and we would audit for contamination
  rather than celebrate a rho=1.0.

## 7. Files (all additive)

- `docs/research/psychology_affect/PHASIC_AROUSAL_DIMENSION_PREREG.md` — this file.
- `tools/build_modulator_seeds.py` — the EMITTER: add
  `drive_arousal_contrib_phasic` + `mod_arousal_phasic` (tonic rules untouched).
- `seeds/modulators.json` — regenerated by the tool (a SEED, not the `.so`/`.rs`).
- `domains/prosody_generation.py` — the AROUSAL read re-routed to
  `arousal_band_phasic`; the honest substrate-primary blend `0.6·band + 0.4·fallback`
  restored (now reading the phasic band).
- `tests/test_phasic_arousal_migrated.py` (new) + `tests/test_prosody_ravdess_migrated.py`
  (stronger, honest bar) + `docs/research/psychology_affect/PROSODY_RAVDESS_RESULTS.md`
  (fear inversion RESOLVED via the phasic dimension).

## 8. Discipline

**SEED-ONLY.** NO Rust (`runners/dsl/src/*.rs` untouched); canonical
`_native.abi3.so` md5 **`7efe75eba05b006cafd15dbb4b7da246` UNCHANGED**; CAN
cognition internals, toolbox solvers, and frozen seeds untouched. The tonic path
is byte-identical (default == today); the new axis is additive and read only by the
prosody world adapter. Integer-native, no new Term, no new constant. Block
**296000** (unused).
