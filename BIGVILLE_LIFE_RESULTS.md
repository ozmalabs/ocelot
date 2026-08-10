# BIGVILLE R14 — THE LIFE CYCLE (block 262000, the KEYSTONE) — RESULTS

Base `95f8ef4fe3` (R1–R9 + R11 + R13 + R16 + R19). Additive, `self_load_only`, ZERO new
Rust. Pre-registration: `BIGVILLE_LIFE_PREREG.md` (committed BEFORE any number here).
Machine summary: `results/bigville_life/summary.json`. Gate:
`tests/test_bigville_life_migrated.py` — **18/18 green**.

The society becomes an ORGANISM: born → reared → come of age → aged → died → inherited.
Every life-cycle decision is a seed RULE (11 rules across three `self_load_only` seeds);
the adapter (`worlds/bigville_life_world.py`) mints nodes at ingest (birth is the honest
boundary), delivers world facts, arms one-shots, runs the Rust `run_rules` fixpoint, and
reads. The developmental substrate (233 Harlow / 239 window-of-tolerance + co-regulation)
is reused UNCHANGED — R14 wires it into the town.

## Gate outcomes (deterministic — no CIs; fully reproducible)

### G-rearing-sets-priors (HEADLINE — the developmental arc embodied) ✓
Two children, SAME inherited temperament (`nat_* = 0.5`); one WELL-REARED (regulated
caregiver present), one NEGLECTED (absent). Their three adult priors DIVERGE:

| child | world_safe | others_trust | self_worth | window half_width | safety_prior | widen/narrow |
|---|---|---|---|---|---|---|
| well-reared | **0.740** | **0.740** | **0.740** | 30 → **46** | 0.50 → **0.74** | 8 / 0 |
| neglected | **0.260** | **0.260** | **0.260** | 30 → **14** | 0.50 → **0.26** | 0 / 8 |

The three Bowlby priors are `clamp01(nat_prior + step·nurture)` with the care signal
`nurture = widen_count − narrow_count` PRODUCED by the reused 239000 rules — well-reared
→ SECURE, neglected → MIS-SET (the affective-disorder family). The 239000 `safety_prior`
moves the same direction as glass-box corroboration.

- **CONTROL (nurture load-bearing) ✓** — same nature + IDENTICAL care → priors IDENTICAL
  (no divergence). The divergence is caused by CARE, not the protocol/RNG.
- **NATURE+NURTURE ✓** — different inherited `nat_*` (0.6 vs 0.4), same good care → the
  higher-nature child ends higher on every axis (nature modulates the same nurture).
- **BIRTH ✓** — a child born of a parent inherits the parent's priors as its `nat_*`
  temperament (nature ~ parent).
- **COMING-OF-AGE ✓** — well-reared capability proxy 0.74 > neglected 0.26; `adult=1`.

### G-health-is-one-mechanism (aging = illness) ✓
One `health` variable on a `LifeState` node, two timescales:
- **Aging alone** (health 5, age_rate 1) → death in 5 periods, `death_cause=1` (age).
- **Illness is acute + RECOVERABLE** — health 100 →(illness 40)→ 60 →(care 30)→ 90 →
  capped at `max_health` (100). Aging and illness are the SAME rule shape (a health delta),
  differing only in magnitude/rate.
- **Routes** — a large acute event drives health ≤ 0 → DEATH, tagged by route (illness=2 /
  starvation=3 / exhaustion=4); all funnel through `bl_death` (health ≤ 0).
- **CONTROL ✓** — care slows the decline: the cared arm (aging + periodic care) survives
  more periods than the un-cared arm (aging alone).

### G-inheritance → intergenerational inequality ✓
On death the estate passes to the heir; Σ(Plot) CONSERVED (only `owns` edges move):
- LAND (4 plots) → the baron's heir; HOUSE → the heir; COIN (500 + 10) → 510 to the heir.
- **Class persists** — landed heir stays landed (4 plots), landless heir stays landless (0);
  the land-holding Gini is **0.5 → 0.5** across the generation (you inherit your class).
- **CONTROL (death OFF → immortal) ✓** — with `dead` never set, the estate NEVER transfers
  (the fixpoint is immortal); every `owns` edge + coin unchanged.

### G-no-heir → commons ✓
A heirless owner's death reverts the estate to the COUNCIL / commons: LAND → council, HOUSE
→ council, COIN (99) → council; Σ(Plot) conserved (reverted, never destroyed) — ties R13.
- **CONTROL (heir beats commons) ✓** — the SAME dead owner WITH an heir → the estate goes
  to the heir, and the commons receives nothing (the branch is the rule's disjoint decision).

### G-death-is-the-reset (ties R10 — PARTIAL) ◐
Death ON transfers the estate (a perturbation: `owner_of(e)` = kid); death OFF (immortal) →
no transfer. The local perturbation mechanism is BUILT + measured. **DEFERRED to R10:** the
full "immortal fixpoint drifts to the DEAD attractor / punctuated-equilibrium validity gate"
claim needs R10 (not in this base).

## ETHICS — induce → measure → RESTORE, NO reward/punishment ✓
The neglect arm INDUCES a mis-set (narrow window 14, safety 0.26). RESTORE by re-rearing
under a regulated caregiver widens the window BACK (half_width 14 → 38, safety 0.26 → 0.62)
— harm induced is harm reversed and measured. Source audit: NO `reward`/`punish`/`penalty`
token in the adapter or the rule logic of any seed. A mis-set prior, illness, and death are
STATES, never a badness (Greene). Death is a state transition enabling INHERITANCE, never a
punishment of the deceased.

## Discipline ✓
- **Rung gate:** `tests/test_bigville_life_migrated.py` 18/18.
- **Additive-only, prefix `bigville_life_`.** New files only; NO existing tracked file
  edited. Three seeds `self_load_only: true` — cannot regress another suite.
- **11 named rules:** `bl_come_of_age` (rearing); `bl_age` / `bl_acute` / `bl_recover` /
  `bl_death` (health); `bl_inherit_{land,house,coin}` + `bl_inherit_commons_{land,house,coin}`
  (inheritance). NO `add_node`/`del_node` in any inheritance rule — the estate is CONSERVED,
  only edges move.
- **ZERO new Rust** — `git diff <base> -- runners/dsl` empty. Composes existing DSL Terms
  (Plus/Minus/Times/Min/Max/Eq/Gte/Gt/Lt/Lte/And/Not/Abs).
- **Engine provenance** `source_match = shared` (canonical `.so`, unchanged md5); no `.so`
  committed; no hardcoded md5 in a test.
- **Source audit:** the adapter runs no Python rule engine and branches only on WORLD facts
  (care present? regulated? stress tick? aging period? illness amount? has_heir?) — never
  computes a prior / health / inheritance outcome in Python.

## DEFERRALS (honest — needs UNBUILT rungs)
- **R18 (school):** coming-of-age capability is a REARING-QUALITY PROXY, not a school-derived
  capability graph. When R18 lands, the capability comes from it (the generational-hinge).
- **R17 (affect layer):** not required by the R14 gates; the developmental affect machinery
  reused here is the standing 233/239/204 substrate.
- **R10 (punctuated equilibrium):** the local death-perturbation is built + measured; the
  immortal-fixpoint-drift validity claim is deferred to R10.

## Honest residuals
- **Rearing dynamics run at FIXED 239000 constants** (the pre-registered stress_mag=100 /
  half_width0=30). The full-power N=60 co-regulation CIs live in the STANDING 239000 result
  (`results/arousal_wot.json`); R14 reuses that proven machinery deterministically rather
  than re-measuring it. The R14 numbers are MECHANISM demonstrations, not a benchmark.
- **The dysregulated-caregiver rearing condition is a THIRD (stuck) outcome** — episodes
  stay open (censored), so neither widen nor narrow resolves (widen=narrow=0 → priors track
  nature only). The two clean poles used in the gate are cared (present+regulated) vs
  neglect (absent). Recorded, not hidden.
- **The `capability` proxy and the priors share one care signal** (`widen − narrow`) — an
  honest simplification until R18 supplies an independent capability graph.
- **SYNTHETIC, not clinical/benchmark** — a glass-box model of the life-cycle mechanism,
  grounded in the creator's in-vivo experience with 21 foster children; mechanism-proven,
  not an outcome number.
