# BIGVILLE R14 — THE LIFE CYCLE: birth → rearing → coming-of-age → health → death → inheritance (the KEYSTONE) — PRE-REGISTRATION

**Block 262000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.9 (THE LIFE CYCLE) + §3 R14 (block 262000, the
four gates). Builds ON R13 `bigville_land_world` (LAND / owns edges / council / the
conserved map) and R7 `bigville_fin_world` (BANK / House / owns_house / coin) — both
imported READ-ONLY (the R14 adapter SUBCLASSES `BigvilleLandWorld`). Reuses the DORMANT
developmental-emotion arc READ-ONLY: `arousal_window_coreg` (block 239000 —
window-of-tolerance + co-regulation, already loaded by the bigville time-world),
`harlow_attachment` (233000), `core_emotions` (204000), and the three foundational
priors (`bigville_townspeople_30` param convention: `prior_world_safe` /
`prior_others_trust` / `prior_self_worth`). Reuse ALL by import; **edit no tracked file.**

The society becomes an ORGANISM: born, reared, come of age, aged, died, inherited.
Every life-cycle decision — the shaping of a child's priors by care quality, the health
decline / death, and the transfer of the estate to heirs (or the commons) — is a seed
RULE (`bigville_life_rearing` / `bigville_life_health` / `bigville_life_inheritance`);
the adapter only mints nodes at ingest (birth is the honest boundary, like R11 arrival),
wires transient edges / arms one-shots, runs the Rust `run_rules` fixpoint, and reads.
**ZERO new Rust** (composes existing DSL Terms: Plus/Minus/Times/Min/Max/Eq/Gte/Lt/And/
Not/Abs — verified present in `runners/dsl/src/term.rs`). Three additive `self_load_only`
seeds — cannot regress any other suite.

## Seed-claim (verbatim `scripts/seed_claim.py 262 262`, run before anything)

```
SEED CLAIM 262-262: CLEAN -- no collision DETECTED.
  Scope: 974 files with seed sinks; 683 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(R14 seeds NO RNG — every rule/attr is deterministic graph data; the rearing dynamics
reuse the pre-registered 239000 window machinery at FIXED constants — so the claim is a
discipline formality; the rung introduces no stochastic sink. The gate is fully
deterministic, no CIs required.)

## What R14 adds (graph-native, ZERO new Rust)

Three additive, `self_load_only` seeds, composing ONLY existing DSL Terms:

- **`bigville_life_rearing`** — REARING shapes the three foundational priors from the
  QUALITY OF CARE, and coming-of-age. The child holds the REUSED 239000 machinery (its
  own `AffectiveState.arousal` + a `WindowOfTolerance` band + a `Stressor`, `attended_by`
  a caregiver with its OWN affect). Rearing = the 239000 stress-episode loop, UNCHANGED:
  a regulated caregiver present → episodes resolve WIDEN (window widens, safety_prior
  rises); a neglected/dysregulated child → NARROW (window narrows, safety_prior falls).
  My NEW rule `bl_come_of_age` maps the 239-produced care signal
  `nurture := (widen_count − narrow_count)` to the three adult Bowlby priors, each
  `prior := clamp01(nature_prior + step·nurture)` — NATURE (inherited `nat_*`, set at
  birth from the parent) MODULATED by NURTURE (care). Coming-of-age also mints a
  `capability` attr as a rearing-quality PROXY (R18 school not built — see DEFERRALS),
  and flags `adult=1`.
- **`bigville_life_health`** — HEALTH is ONE variable, two timescales. `bl_age` (CHRONIC
  decline per period, tags `last_cause=1`), `bl_acute` (ACUTE drop — illness/injury/
  starvation/exhaustion, one rule, `illness_cause` opaque data 2/3/4 tags the route,
  RECOVERABLE), `bl_recover` (care/rest/doctor restores the SAME variable up to
  `max_health`), and the unifying decision `bl_death` (`health ≤ 0 ∧ ¬dead → dead=1`,
  `death_cause := last_cause`, `just_died=1`). Aging IS illness — same variable, differing
  only in magnitude/rate; the four routes all funnel through `health ≤ 0`.
- **`bigville_life_inheritance`** — on death (`just_died=1`) the estate passes: `bl_inherit_land`
  (each owned Plot's `owns` edge moves dead→heir, sequential to fixpoint — LAND CONSERVED,
  R13), `bl_inherit_house` (owns_house dead→heir, R7), `bl_inherit_coin` (lump coin
  dead→heir, once via `coin_bequeathed`). With NO heir (`has_heir=0`, a structural fact set
  at ingest), `bl_inherit_commons_land` / `bl_inherit_commons_house` revert the estate to
  the COUNCIL (`is_council=1`, R9 commons) — ties R13 conservation (land is transferred,
  never destroyed).

## The gates (each with its failable control)

### G-rearing-sets-priors (HEADLINE — the developmental arc embodied)
Two children with the SAME inherited temperament (`nat_*` identical): one WELL-REARED
(regulated caregiver present), one NEGLECTED (caregiver absent). Their three adult priors
(`prior_world_safe` / `prior_others_trust` / `prior_self_worth`) **DIVERGE** — the
well-reared child ends SECURE (each prior ↑), the neglected child MIS-SET (each ↓). The
239000 `safety_prior` (WOT) moves the same direction as glass-box corroboration.
- **CONTROL (nurture load-bearing):** ablate care-quality VARIATION — give BOTH children
  IDENTICAL care → their priors are IDENTICAL (no divergence). The divergence is caused by
  CARE, not the protocol.
- **NATURE+NURTURE:** two children with DIFFERENT inherited `nat_*`, SAME care → the
  higher-nature child ends higher (nature modulates the same nurture).
- **ABANDON if:** the well-reared and neglected priors do NOT separate, OR identical care
  produces divergent priors (would mean nature/RNG, not care, drives it).

### G-health-is-one-mechanism (aging = illness)
A HEALTH variable declines CHRONICALLY (`bl_age`) + ACUTELY (`bl_acute`); care/rest/doctor
restore (`bl_recover`); **DEATH at zero** (`bl_death`), tagged by route (age/illness/
starvation/exhaustion). Aging and illness are the SAME rule shape (a health delta).
- **CONTROL:** no acute events → death by AGING ALONE (`death_cause=1`); ablate care (no
  `bl_recover`) → FASTER decline (reaches 0 sooner) than the cared arm.
- **ABANDON if:** an acute drop is not recoverable by care, OR aging alone never reaches
  death, OR care does not slow the decline.

### G-inheritance → intergenerational inequality
On death the estate (LAND R13 / house R7 / coin) passes to the heir; land Σplots CONSERVED
throughout (only `owns` edges move). Across two generations: a LANDED parent's landed heir
STAYS LANDED; a LANDLESS parent's heir STAYS LANDLESS → the land-holding partition (and its
Gini) PERSISTS across the generation (you inherit your class).
- **CONTROL:** with death OFF (immortal — `dead` never set) the estate NEVER transfers (the
  fixpoint is immortal); Σplots and every `owns` edge are unchanged.
- **ABANDON if:** inheritance mints/destroys a Plot (conservation broken), OR the class
  partition does not persist across the generation.

### G-no-heir → commons
A dead owner with NO heir (`has_heir=0`) → the estate REVERTS to the council/commons
(`bl_inherit_commons_*`), never destroyed; Σplots conserved.
- **CONTROL:** the SAME dead owner WITH an heir → the estate goes to the HEIR, not the
  commons (the heir vs no-heir branch is the rule's decision).
- **ABANDON if:** a no-heir estate is destroyed rather than reverting.

### G-death-is-the-reset (ties R10 — PARTIAL, see DEFERRALS)
Death ON → a wealthy owner's death is a PERTURBATION: the estate DISPERSES (many heirs) or
CONCENTRATES (one heir). Death OFF (immortal) → no transfer. We build + measure the
perturbation (transfer-count ON vs OFF; disperse vs concentrate). The full R10 claim — the
immortal fixpoint DRIFTS to the DEAD attractor, the validity gate the punctuated
equilibrium NEEDS — requires R10 (NOT in this base). **We DEFER that fixpoint-drift claim
honestly** and demonstrate only the local perturbation mechanism.

## ETHICS — relational-ethics protocol (rearing-harm / death are harm-analogs)
Rearing a child under neglect and letting a person die are HARM-ANALOGS. This rung binds
the standing relational-ethics protocol: **induce → measure → RESTORE, NO reward /
punishment.**
- **NO reward/punishment tokens** anywhere in the adapter or seeds. Dysregulation, a
  mis-set prior, illness, and death are STATES, never a "badness" (Greene). The source
  audit FAILS on any `reward` / `punish` / `penalty` token.
- **RESTORE.** The neglect arm INDUCES mis-set priors; the rung then RESTORES the child by
  RE-REARING under good care (the 239000 window widens back, the priors recover toward
  secure) — a dedicated `test_ethics_restore`. Harm induced is harm reversed and measured.
- **Death** is modelled as a state transition (`dead=1`) that enables INHERITANCE (the
  estate is conserved and passed on), never a punishment of the deceased.

## Discipline (pre-committed)
- **Additive-only, ONE prefix `bigville_life_`.** NEW files only: `seeds/bigville_life_*.json`
  (×3), `worlds/bigville_life_world.py`, `scripts/bigville_life_gen_seeds.py` +
  `scripts/bigville_life_run.py`, `tests/test_bigville_life_migrated.py`, this prereg,
  `BIGVILLE_LIFE_RESULTS.md`, `results/bigville_life/summary.json`. **Edit NO existing
  tracked file.** All three seeds `self_load_only: true`.
- **ZERO new Rust.** `git diff <base> -- runners/dsl` MUST be empty.
- **CONSERVATION at the source level:** no rule mints or destroys a Plot / House node
  (`add_node`/`del_node` forbidden in inheritance effects — checked in the source audit);
  every estate transfer MOVES an edge. Birth mints a person node ONLY at adapter ingest
  (the honest boundary), never in a rule.
- **Own/shared engine provenance** (`source_match ∈ {own, shared}`); canonical shared `.so`
  md5 UNCHANGED; no `.so` committed; no hardcoded md5 in a test.
- **Source audit:** every life-cycle decision is a named seed rule; the adapter runs no
  Python rule engine and branches only on WORLD facts (care present? regulated? stress
  tick? has_heir?) — never computes a prior / health / inheritance outcome in Python.

## DEFERRALS (honest — needs UNBUILT rungs)
- **R18 (school) — coming-of-age capability graph.** The matured capability set should come
  from R18. R18 is NOT built. Coming-of-age therefore mints a `capability` attr as a
  REARING-QUALITY PROXY (derived from the same `nurture` care signal), recorded as a proxy,
  NOT a school-derived capability graph.
- **R17 (affect layer) — not required by the R14 gates.** The developmental affect machinery
  reused here is the STANDING 233/239/204 substrate, not R17. No R17 dependency; nothing
  deferred to it.
- **R10 (punctuated equilibrium) — the death-is-the-reset validity gate.** We build the
  local perturbation mechanism (estate disperses/concentrates on death; immortal → no
  transfer) but DEFER the full "immortal fixpoint drifts to the DEAD attractor" claim to R10.

## Gates to run (INLINE, no waiter)
- `python -m pytest tests/test_bigville_life_migrated.py -q` (the rung gate — all green)
- `python -m pytest tests/test_failure_baseline_migrated.py -q` (11/11 — additive, must not move)
- `python -m pytest tests/test_engine_provenance_migrated.py -q` (7/7 — own/shared engine)

The ~43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` are NOT run: an
additive `self_load_only` rung cannot regress other suites (per the 2026-07-29 directive);
the fast baseline gate + additive discipline + source audit are sufficient.
