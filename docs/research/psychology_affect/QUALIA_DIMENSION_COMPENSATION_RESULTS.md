# QUALIA DIMENSION COMPENSATION — RESULTS (block 298000)

**Verdict: CONFIRMED.** Finer grain on a remaining axis recovered the
*reconstructable* discriminations while the *orthogonal* discrimination stayed
FAILED at **every** grain — an aperture-invariant residual deficit. And the
compensation was **meaningful, not trivial**: the recovery required a commitment
grain FINER than global (at global grain the compensated agent discriminated
none of the reconstructable pairs).

- Pre-reg (frozen before this run): `QUALIA_DIMENSION_COMPENSATION_PREREG.md`.
- Charter: `docs/research/theory_convergence/QUALIA_SPACE_VARIATION_CHARTER.md` §4.
- Rides on Stage 1: `docs/research/engine_substrate/QUALIA_APERTURE_GENERALISATION_PREREG.md`.
- Run: `python3 -m domains.qualia_aperture_world` → `results/qualia_dimension_compensation/results.json`.
- Test: `tests/test_qualia_dimension_compensation_migrated.py` (6 gates, all green).
- `_native.abi3.so` md5: `7efe75eba05b006cafd15dbb4b7da246` (unchanged; seed +
  Python only, no Rust). `git diff HEAD -- runners/dsl` empty.

## The three agents (as pre-registered)

The absent axis is `phenomenal:sharpness` (dark for both dark agents — the
aphantasia arm); the compensated axis is `dynamical:commitment` (source
`identity_field`, global quantum 0.25, half_width 4). All three agents resolve
`dynamical:commitment` and `dynamical:valence`; only sharpness existence and
commitment grain differ between them.

| agent | reads sharpness? | commitment grain |
|---|---|---|
| FULL | yes | global (0.25) |
| DARK-COMPENSATED | no (dark) | fine (0.10) |
| DARK-UNCOMPENSATED | no (dark) | global (0.25) |

## Base three-agent rates (compensated grain = 0.10)

| agent | reconstructable | orthogonal |
|---|---|---|
| **FULL** | **3/3** | **1** |
| **DARK-COMPENSATED** | **3/3** | **0** |
| **DARK-UNCOMPENSATED** | **0/3** | **0** |

FULL discriminates everything (it has the sharpness axis). DARK-COMPENSATED
matches FULL on the reconstructable battery — *without* sharpness, purely by the
finer commitment grain — yet fails the orthogonal pair. DARK-UNCOMPENSATED fails
both. This is the predicted P2/P3/P4 shape exactly.

## Glass-box: the ORTHOGONAL pair's signatures (dynamical coordinates)

The orthogonal pair's two concepts are identical on every attr except `sharpness`
(+1 vs −1). Printed by the run:

```
FULL  A dyn: [(dynamical:commitment,field,3), (dynamical:valence,field,1), (phenomenal:sharpness,field, 1)]
FULL  B dyn: [(dynamical:commitment,field,3), (dynamical:valence,field,1), (phenomenal:sharpness,field,-1)]
FULL  differ (sharpness coordinate separates): True
DARK  A dyn: [(dynamical:commitment,field,4), (dynamical:valence,field,1)]
DARK  B dyn: [(dynamical:commitment,field,4), (dynamical:valence,field,1)]
DARK  BYTE-EQUAL (sharpness was the only separator): True
```

Under FULL the only differing coordinate is `phenomenal:sharpness` (+1 vs −1) —
sharpness is the sole separator. Under a DARK agent that coordinate is gone and
the two signatures are **byte-EQUAL**: the pair is genuinely orthogonal to every
axis the dark agent has. (The dark commitment level reads 4 because at grain 0.1
the shared `identity_field` 0.8 → 8, clamped to half_width 4 — identical for both
members, so still byte-equal; sharpening commitment cannot separate a pair that
does not differ on commitment.)

## The swept-grain table (the falsifiable core)

Sweeping the DARK-COMPENSATED agent's commitment grain coarse → fine, existence
(sharpness dark) held fixed:

| commitment grain | reconstructable rate | orthogonal rate |
|---|---|---|
| 0.25 (global) | 0/3 | **0** |
| 0.20 | 0/3 | **0** |
| 0.15 | **3/3** | **0** |
| 0.12 | **3/3** | **0** |
| 0.10 | **3/3** | **0** |

And the test sweeps further still — 0.10, 0.05, 0.02, 0.01, 0.005 — with the
orthogonal discrimination **never** recovering.

- **Reconstructable RECOVERS as grain sharpens** (0/3 → 3/3, crossing at grain
  0.15). The correlated commitment structure the reconstructable pairs carry
  becomes resolvable once the grain is fine enough — the compensated agent
  reconstructs the discrimination from a *remaining* axis, exactly as the charter
  predicts.
- **Orthogonal stays 0 at EVERY grain.** No aperture setting manufactures the
  missing sharpness dimension. This is the **aperture-invariant residual
  deficit** the charter's falsifier targets. It did not falsify.

## Was the compensation meaningful or trivial?

**Meaningful.** At global grain 0.25 the DARK-COMPENSATED agent discriminates
**0/3** reconstructable pairs — identical to DARK-UNCOMPENSATED — because every
reconstructable pair's commitment gap (identity_field 0.14/0.24, 0.16/0.26,
0.14/0.28) collapses to the same level at global grain. The recovery to 3/3
appears only once the grain is finer than global (from 0.15 down). So the freed
budget is doing real discriminative work; the compensated agent is not merely
reading a difference that was already present globally. Compensation is REAL
(`comp > uncomp`: 3/3 vs 0/3) and MEANINGFUL (needed the finer grain).

## Tie to the charter and the aphantasia shape

This is precisely the §4 claim, mechanised. The dimension-lacking agent
(DARK-COMPENSATED) is **behaviourally near-normal** — matching the full agent on
the reconstructable battery via a finer aperture on a surviving axis — and its
deficit surfaces **only in the very specific circumstance** that requires a
discrimination *orthogonal* to every remaining axis. That maps onto the observed
aphantasia shape: ~1% of people with no voluntary visual imagery (an entire felt
dimension *absent*, not weak; *Nature Sci. Rep.* 2020; imagery extremes and their
developmental character, Cell/*TICS* 2024) are largely functional through
verbal/spatial/semantic compensation and fail specifically on tasks that
genuinely require imagery. The residual deficit is confined to exactly those
tasks, and here it is **aperture-invariant** — no amount of sharpening a remaining
axis substitutes for the missing one. *(References rephrased for compliance with
licensing restrictions.)*

## Honest scope (charter §5 ledger, unchanged)

We tested compensation as a **consequence** of hand-configured agents (§2 of the
pre-reg). We did NOT show the substrate performs budget reallocation, enforces a
quantum budget, or carries a per-agent axis codebook — those remain conceptual
(charter §5). The `resolves` (existence) and `grain` (resolution) knobs are real
Observer-node state read by the Stage-1 generalised aperture; the *coupling*
between dropping sharpness and sharpening commitment was imposed by the
experimenter exactly as pre-registered. The result confirms the charter's
falsifiable *prediction*; it does not upgrade the charter's flagged gaps.

## Anti-faking (as pre-registered)

- Discrimination is READ from signature byte-equality, never decided by a branch.
  Source-audit of `domains/qualia_aperture_world.py`: no `graph_rewrite.run` /
  `_match` / `_apply` / `make_rule`, and no `if/else` selecting a discrimination
  outcome (the only conditionals count rates / bound loops).
- The orthogonal pair is orthogonal BY CONSTRUCTION (differs on sharpness and
  nothing else) — proven byte-equal-when-dark in the glass-box print and the test.
- The reconstructable gap is sub-threshold at global grain — proven by the 0/3
  global row — so compensation cannot be reading an already-visible difference.
