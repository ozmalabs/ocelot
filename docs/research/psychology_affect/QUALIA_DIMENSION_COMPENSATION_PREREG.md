# QUALIA DIMENSION COMPENSATION — aperture mostly covers a missing felt axis, but leaves an aperture-invariant residual deficit on orthogonal discriminations — PRE-REGISTRATION (block 298000)

**This document is committed BEFORE any measurement.** It states the design, the
frozen constants, the exact stimulus values, the grain arithmetic, the predicted
outcomes, and the failable controls. No number below is a measurement — every
outcome stated as "predicted" is a PREDICTION. This is the falsifiable core of
`docs/research/theory_convergence/QUALIA_SPACE_VARIATION_CHARTER.md` §4, carved
off as the charter promised.

Status: frozen before the confirmatory implementation and run.

Date frozen: 2026-07-29 (Australia/Melbourne).

Pre-registration block: **298000**.

## 0. What is being tested (from the charter)

The charter (`QUALIA_SPACE_VARIATION_CHARTER.md`) states two axes of qualia
variation — **aperture** (grain/granularity, = the per-axis `quantum`) and
**dimensionality** (a felt axis present vs absent, = the axis in/out of the
observer's `resolves`) — and one falsifiable prediction, **compensation**:

> When a felt axis is ABSENT, the GRAIN of the remaining axes expands to *mostly*
> compensate. The dimension-lacking agent is near-normal on discriminations
> *reconstructable* from correlated structure on the remaining axes (finer grain
> there, funded by the freed budget), and fails ONLY on discriminations
> *orthogonal* to every remaining axis — where no aperture can help, because
> aperture cannot manufacture a dimension.

The charter's falsifier: **if expanding the remaining axes' grain ever recovers
the orthogonal discrimination, the theory is wrong** — aperture would be
substituting for a dimension. The theory predicts an **aperture-invariant
residual deficit** confined to the orthogonal case.

This is the aphantasia clinical shape: aphantasics (~1% with no voluntary visual
imagery — an entire felt dimension *absent*, not weak; Cell/*TICS* 2024's imagery
extremes, and the *Nature Sci. Rep.* 2020 framing of aphantasia as *absence*) are
largely functional through verbal/spatial/semantic compensation and fail
specifically on tasks that *genuinely require* imagery. We reproduce that shape
mechanically.

## 1. The substrate this rides on (Stage 1, already frozen)

This experiment consumes the **generalised APERTURE primitive** frozen in
`docs/research/engine_substrate/QUALIA_APERTURE_GENERALISATION_PREREG.md` (block
297000): `domains/analogy_search.concept_signature(sub, concept, edge_types=None,
*, overlay=False, observer=None)` consults `_observer_aperture(sub, observer)`,
which reads the SAME Observer node's `resolves` (EXISTENCE — the set of qualia
dimension NAMES it distinguishes, or `None` = all) and `grain` ({dim_name →
quantum} RESOLUTION), REUSING `seeds/observer_aperture.json`'s own state (no
parallel per-agent quantum holder). Per dynamical axis: if `resolves` is not
`None` and the axis's dimension name ∉ `resolves` ⇒ **DARK** (no coordinate);
else `q = grain.get(dim, global_quantum)`; `k = _round_to_vocab(raw, q,
half_width)`. `observer=None` ⇒ byte-identical to pre-Stage-1 behaviour.

The relevant qualia axes (full `family:name`, from `seeds/qualia_space.json`):
- `phenomenal:sharpness` — source `field:sharpness`, quantum **1.0**, half_width
  **1** ⇒ a bipolar SIGN axis {−1, 0, +1}. **This is the axis we make ABSENT** for
  the two dark agents (the aphantasia arm — a felt crossmodal scalar that is
  either present or dark).
- `dynamical:commitment` — source `field:identity_field`, global quantum **0.25**,
  half_width **4** ⇒ a GRADED axis. **This is the remaining axis whose grain we
  sharpen** in the compensated agent (the Pareto move: freed budget → finer
  grain elsewhere).
- `dynamical:valence` — source `field:state`, quantum **1.0**, half_width **1** ⇒
  a coarse SIGN axis. Held resolved by all three agents at global grain.

## 2. The three observers (hand-configured; the charter's §5 honest ledger)

The charter is explicit that the substrate does NOT spontaneously reallocate a
budget; we configure the three agents BY HAND and test the *consequence*, not the
dynamic. All three RESOLVE every non-sharpness dynamical axis (so only sharpness
existence, and commitment grain, vary between them):

| agent | `resolves` (existence) | `grain` (commitment) | reads sharpness? |
|---|---|---|---|
| **FULL** | ALL (incl. `phenomenal:sharpness`) | global (0.25) | yes |
| **DARK-COMPENSATED** | omits `phenomenal:sharpness`; keeps `dynamical:commitment`, `dynamical:valence` | FINE (`{'dynamical:commitment': 0.1}`) | **no (dark)** |
| **DARK-UNCOMPENSATED** | omits `phenomenal:sharpness`; keeps `dynamical:commitment`, `dynamical:valence` | global (0.25) | **no (dark)** |

FULL is set up as an explicit `resolves` list of ALL dynamical + sharpness dims
(not `resolves=None`) so the three agents differ ONLY in the sharpness membership
and the commitment grain — nothing else.

## 3. The discrimination mechanic (read, not decided)

Two stimuli are **DISCRIMINABLE** to an agent iff their `concept_signature`s read
through that agent's observer DIFFER (as frozensets); **INDISCRIMINABLE** iff
EQUAL. The outcome is byte-equality of two signatures — there is NO Python
`if/else` that decides discriminability, and NO `graph_rewrite`/`_match`/`_apply`/
`make_rule` call. Each stimulus is a `Concept` node carrying the source attrs
(`sharpness`, `identity_field` for commitment, `state` for valence).

## 4. The battery (exact frozen values + grain arithmetic)

`_round_to_vocab(x, q, hw)` = `round(x/q)` clamped to ±hw, `None` at 0. Python's
`round` is banker's rounding; the values below were chosen so the arithmetic is
unambiguous and, crucially, so **no reconstructable pair clamps at any swept
grain** (values ≤ 0.28, and 0.28/0.1 = 2.8 ⇒ level 3 ≤ hw 4).

### 4a. RECONSTRUCTABLE pairs (3) — differ on sharpness AND a small correlated commitment gap

Each pair's two concepts share `name` and `category` (so nothing but the two
felt axes can separate them) and differ on BOTH `sharpness` (±1) AND
`identity_field` (a gap SIZED to need finer-than-global grain). The commitment
gap is INVISIBLE at global grain 0.25 (both round to the same level) but VISIBLE
at fine grain — so a DARK agent can only tell the pair apart via the finer
commitment grain, i.e. by RECONSTRUCTION from a correlated remaining axis, not by
the missing sharpness axis. Frozen values and the level table
(`k = round(identity_field / q)`, clamp ±4):

| pair | `identity_field` A / B | sharpness A / B | q0.25 (global) | q0.20 | q0.15 | q0.12 | q0.10 |
|---|---|---|---|---|---|---|---|
| **R1** | 0.14 / 0.24 | +1 / −1 | 1 / 1 **same** | 1 / 1 same | 1 / 2 **diff** | 1 / 2 diff | 1 / 2 diff |
| **R2** | 0.16 / 0.26 | +1 / −1 | 1 / 1 **same** | 1 / 1 same | 1 / 2 **diff** | 1 / 2 diff | 2 / 3 diff |
| **R3** | 0.14 / 0.28 | +1 / −1 | 1 / 1 **same** | 1 / 1 same | 1 / 2 **diff** | 1 / 2 diff | 1 / 3 diff |

At global grain 0.25 all three commitment gaps COLLAPSE (both members → level 1):
the gap is genuinely sub-threshold globally. From grain 0.15 down, all three
SEPARATE. This is what makes compensation **meaningful, not trivial**: the
compensated agent needs a grain FINER than global to reconstruct the pair — the
freed budget is doing real work, not reading a difference already present at
global grain.

### 4b. ORTHOGONAL pair (1) — sharpness is the ONLY separator

Two concepts IDENTICAL on every attr (same `name`, same `category`, same
`identity_field` = 0.8 ⇒ commitment level 3 at global grain, same `state`, same
edges) EXCEPT `sharpness` (+1 vs −1). VERIFY BY CONSTRUCTION: with sharpness dark,
the two signatures are **BYTE-EQUAL** (sharpness is the only differing coordinate,
and it is gone). FULL discriminates (its sharpness coordinate differs: +1 vs −1).
BOTH dark agents cannot, **at any commitment grain** — they are identical on every
resolvable axis, so sharpening commitment cannot manufacture the sharpness axis.

## 5. Predictions (frozen — the numbers to hold or falsify)

Let *reconstructable-rate* = fraction of the 3 R-pairs an agent discriminates;
*orthogonal-rate* = 1 if it discriminates the O-pair else 0.

- **P1 (default==today, the Stage-1 guard).** `observer=None` is byte-identical
  to pre-Stage-1 `concept_signature` on the qualia + analogy surface (re-asserted
  on a couple of signatures). *Falsifier:* any drift ⇒ the generalisation changed
  existing behaviour and is rejected.
- **P2 (FULL discriminates both).** FULL reconstructable-rate = 3/3 (via
  sharpness), orthogonal-rate = 1.
- **P3 (DARK-UNCOMPENSATED discriminates neither).** reconstructable-rate = 0/3
  (global grain misses every commitment gap AND sharpness is dark),
  orthogonal-rate = 0.
- **P4 (DARK-COMPENSATED reconstructs but not the orthogonal).**
  reconstructable-rate = 3/3 at grain 0.1 (finer commitment grain resolves every
  gap WITHOUT sharpness), orthogonal-rate = **0** (no grain manufactures the
  missing axis).
- **P5 (COMPENSATION REAL + MEANINGFUL).** DARK-COMPENSATED discriminates ≥ 1
  reconstructable pair that DARK-UNCOMPENSATED misses — and because global grain
  0.25 collapses all three gaps (§4a), the recovery REQUIRED the finer grain
  (meaningful, not trivial).
- **P6 (APERTURE-INVARIANT RESIDUAL — the charter's falsifiable core).** Sweeping
  the DARK-COMPENSATED agent's commitment grain coarse → fine
  (0.25 → 0.20 → 0.15 → 0.12 → 0.10): reconstructable-rate RECOVERS
  (0/3 → 0/3 → 3/3 → 3/3 → 3/3) as grain sharpens; orthogonal-rate stays **0 at
  EVERY grain**. **If any finer grain ever recovers the orthogonal discrimination,
  the charter is FALSIFIED** — report honestly.

## 6. The anti-faking construction (why this is not rigged)

- The discrimination is **read from signature byte-equality**, never decided by a
  branch. Source-audit: no `graph_rewrite.run`/`_match`/`_apply`/`make_rule`, and
  no `if/else` selecting the discrimination outcome.
- The orthogonal pair is **orthogonal BY CONSTRUCTION**: its two concepts differ
  on `sharpness` and NOTHING else, so with sharpness dark the two signatures are
  byte-EQUAL — proven in the run's glass-box print (FULL: differ; a dark agent:
  byte-equal) and re-asserted in the test.
- The reconstructable gap is **sub-threshold at global grain** (§4a table): the
  compensated agent cannot be reading a difference already visible globally — it
  must use the finer grain. This forecloses the trivial-compensation reading.
- The three agents differ ONLY in sharpness existence and commitment grain (§2):
  everything else is held identical, so any behavioural difference is attributable
  to exactly the manipulated knobs.

## 7. Honest scope (inherited from the charter §5 ledger)

We test compensation as a **consequence** of hand-configured agents. We do NOT
claim the substrate performs budget reallocation, enforces a quantum budget, or
carries a per-agent axis codebook — those remain conceptual (charter §5). The
`resolves`/`grain` knobs are real substrate state on the Observer node; the
*coupling* between dropping sharpness and sharpening commitment is imposed by the
experimenter, as pre-registered here.

## 8. Confirmatory artefacts (frozen)

- `domains/qualia_aperture_world.py` — configures the three observers + the
  battery, reads discriminations via `concept_signature`, sweeps the compensated
  grain, prints the orthogonal pair's FULL-vs-dark signatures (glass-box), writes
  `results/qualia_dimension_compensation/results.json`.
- `tests/test_qualia_dimension_compensation_migrated.py` — (a) default==today;
  (b) FULL discriminates the O-pair, both dark agents do not; (c)
  aperture-invariant: sweep fine→finer, O never recovers; (d) compensation
  real+meaningful: DARK-COMPENSATED gets ≥1 R-pair DARK-UNCOMPENSATED misses; (e)
  orthogonality: dark ⇒ the O-pair's two signatures byte-EQUAL.
- Green set kept: this test + `test_qualia_space_migrated` +
  `test_qualia_cross_family` + `test_qualia_schema` + `test_analogy_search_migrated`
  + `test_bouba_kiki_sound_symbolism_migrated` + `test_observer_aperture_migrated`
  + `test_disposition`.
- `_native.abi3.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (seed +
  Python only; no Rust).

## 9. References (rephrased for compliance with licensing restrictions)

- Aphantasia as *absence* of voluntary visual imagery (~1% tail), functional
  except in circumstances that genuinely require imagery; the imagery extremes
  (aphantasia / hyperphantasia) and their developmental/familial character
  (*Nature Sci. Rep.* 2020; Cell/*Trends in Cognitive Sciences* 2024). Cited as
  the predicted HUMAN SHAPE the compensation prediction reproduces: near-normal
  by compensation, residual deficit confined to the orthogonal (imagery-requiring)
  case.
