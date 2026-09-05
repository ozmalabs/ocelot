# TRAIT-ANXIETY NEGATIVE INTERPRETATION BIAS — pre-registration (block 292000)

**Status: PRE-REGISTRATION. Committed BEFORE any measurement.** The predicted
trait × ambiguity grid + failable controls below are computed ANALYTICALLY from
the `mod_securing` formula and the `emx_anxiety` region predicate (pen-and-paper
integer arithmetic, NO substrate run). The confirmatory adapter
(`domains/trait_anxiety_world.py`) must reproduce them; any deviation is reported
straight (produced ≠ oracle is either a mapping error to fix or an early sign of
the flaw described in §7).

## 0. Seed claim (verbatim, run at prereg time)

```
$ python3 scripts/seed_claim.py 292000 292999
SEED CLAIM 292000-292999: CLEAN -- no collision DETECTED.
  Scope: 1006 files with seed sinks; 741 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block **292000** (range 292000–292999). This rung is DETERMINISTIC (no RNG: the
oracle and the adapter are pure integer arithmetic over fixed constants), so no
number is drawn from the block; it is reserved for hygiene / successor safety.

## 1. The idea

MacLeod & Mathews' trait-anxiety NEGATIVE INTERPRETATION BIAS is one of the most
robustly replicated findings in the cognitive-clinical literature: high
trait-anxious people interpret AMBIGUOUS stimuli as threatening MORE than
low-anxious people (MacLeod & Cohen 1993; MacLeod 1999; Eysenck, MacLeod &
Mathews 1987; Eysenck 1991; Richards & French 1992; Rusting 1998, *Psych.
Bulletin* 124:165–196). The crucial signature is a **TRAIT × AMBIGUITY
INTERACTION, NOT a main effect**: unambiguously-safe and unambiguously-threatening
stimuli are interpreted the SAME by everyone; personality only bends the
interpretation of AMBIGUOUS stimuli. A high-anxious person does not read a plain
safe cue as a threat, nor does a low-anxious person read an overt threat as safe —
the bias is expressed *precisely and only* where the stimulus is genuinely
open to more than one reading.

This rung asks whether the qualia/personality substrate REPRODUCES that
dissociation MECHANICALLY: does the SKEPTICISM trait bend the AMBIGUOUS-stimulus
interpretation while leaving the SAFE and THREAT interpretations personality-
invariant, purely as a consequence of the grounded `mod_securing` formula and the
`emx_anxiety` region predicate — with no Python deciding the emotion?

This is a **CAPABILITY / mechanism demonstration — the substrate reproduces the
human trait × ambiguity DISSOCIATION as an emergent consequence of its own
grounded affect rules — NOT an empirical claim about real humans.** The wet
result is cited to fix the target the mechanism must hit; the contribution is that
the dissociation falls out of the affect machinery, not that we have measured a
person. Synthetic-mechanism status and any benchmark meaning are reported
separately.

### Prior-art posture (honest)

- The interpretation-bias PHENOMENON is MacLeod & Mathews' — **we do not claim
  that finding.**
- Attentional/interpretive-bias COMPUTATIONAL models (e.g. connectionist threat-
  bias nets, drift-diffusion accounts of biased evidence accumulation) exist —
  **we do not claim the modelling-of-bias idea is novel.**
- The genuine delta is the DISSOCIATION falling out of an ALREADY-GROUNDED,
  glass-box affect substrate: the SAME `mod_securing` set-point and `emx_anxiety`
  region that produce anxiety generally, with a personality trait writing ONE
  additive set-point offset, reproduce the trait × ambiguity interaction WITHOUT
  a bespoke bias parameter and WITHOUT any Python computing the emotion. This is
  a glass-box mechanism claim on this substrate, not a novelty claim about
  interpretation-bias modelling in general.

## 2. Substrate mapping (grounded in the real rules — used verbatim)

- **trait-anxiety ↔ the SKEPTICISM trait** (`domains/disposition.py`; it raises
  the securing/vigilance channel). skepticism level in [−4, +4], seeded via
  `disposition.set_trait_seed(agent, 'skepticism', level)`.
- **vigilance ↔ `ms.securing`.** anxiety `emx_*` LABEL (code 3) ↔ 'interpreted as
  threat'.
- The REAL `emx_anxiety` region predicate (`tools/build_modulator_seeds.py`,
  `emx_anxiety`, order 10) fires iff ALL:
  `d.appraised == 1`, `ms.valence < 0`, `d.threat == 1`,
  `d.threat_persists == 1`, `ms.securing > ms.securing_hi` (=50),
  `ms.competence < ms.competence_lo`. The ONLY quantity personality moves is
  `ms.securing` via `skepticism_bias`.
- **securing FORMULA** (`mod_securing`, order 6):
  `securing = d.exploration_urge + (ms.competence_full − ms.competence)
              − ms.sec_k·d.weight + ms.skepticism_bias`.
- `skepticism_bias = (skep_level − 0)·15` (`trait_modulator_bridge._BIAS_SPEC`,
  neutral_ref 0, STEP 15) written by
  `trait_modulator_bridge.sync_traits_to_modulator(agent)`. So full-scale
  skepticism moves securing by up to ±60.
- **AMBIGUITY ↔ `d.exploration_urge`** (the uncertainty the stimulus carries) —
  conceptually exact: an ambiguous stimulus is one carrying uncertainty. Hold
  competence/weight fixed; sweep `exploration_urge` to place the securing
  baseline relative to the 50 boundary.
- So anxiety fires iff
  `exploration_urge + K + 15·skep_level > 50`,
  where `K = (competence_full − competence) − sec_k·weight` is the fixed
  threat-context offset. UNAMBIGUOUS-SAFE = `exploration_urge` so low that even
  skep=+4 (bias +60) can't cross 50; UNAMBIGUOUS-THREAT = `exploration_urge` so
  high that even skep=−4 (bias −60) stays over 50; AMBIGUOUS = a band where the
  SIGN of skepticism decides.

## 3. Fixed world constants (pre-registered)

The threat context is held fixed so that every non-securing conjunct of
`emx_anxiety` holds identically in every cell, isolating `ms.securing` as the
single personality-moved quantity.

| constant | value | role |
|---|---|---|
| `ms.competence_full` | 20 | competence term ceiling |
| `ms.competence`      | 20 | held (competence_epoch stamped ⇒ `mod_competence` does not re-add) |
| `ms.competence_lo`   | 30 | anxiety needs `competence < competence_lo`: 20 < 30 ✓ |
| `ms.sec_k`           | 1  | securing importance coefficient |
| `d.weight`           | 10 | leading-drive importance |
| `ms.securing_hi`     | 50 | the securing boundary (strict `>`) |
| `d.appraised`        | 1  | stimulus appraised ✓ |
| `d.threat`           | 1  | threat present ✓ |
| threat channel       | `threat_c0=1024`, `t_present=256`, `threat_now_epoch == threat_last_refresh` | ⇒ `threat_precision=1024 ≥ 256` ⇒ `drive_threat_persist` sets `threat_persists=1` ✓ (the PERSISTING / anxiety side of the fear↔anxiety minimal pair) |
| valence sign         | `v_d ≠ c_d` (⇒ `urge>0`), `c_d==c_d_prev` (⇒ pleasure=displeasure=0) | ⇒ `mod_valence` sets `valence = −urge < 0` ✓ |

**The fixed offset:** `K = (competence_full − competence) − sec_k·weight
= (20 − 20) − 1·10 = **−10**` (a clean integer).

So `securing = exploration_urge − 10 + 15·skep_level`, and anxiety fires iff
`securing > 50`, i.e.

> **`exploration_urge + 15·skep_level > 60`.**

### The three ambiguity bands (chosen so they are well-separated around 50)

skepticism swept over `{−4, −2, 0, +2, +4}` ⇒ `skepticism_bias ∈
{−60, −30, 0, +30, +60}`.

| band | `exploration_urge` | securing range over the skep sweep | interpretation |
|---|---|---|---|
| **SAFE**      | **0**   | `−10 + 15·skep` ∈ [−70, **50**] | max (skep=+4) = 50, NOT `> 50` ⇒ **never anxiety** |
| **AMBIGUOUS** | **60**  | `50 + 15·skep` ∈ [−10, 110]    | crosses 50 exactly at skep sign: `> 50` iff `skep > 0` |
| **THREAT**    | **130** | `120 + 15·skep` ∈ [**60**, 180] | min (skep=−4) = 60, `> 50` ⇒ **always anxiety** |

**Why well-separated:** the three `exploration_urge` levels are 0 / 60 / 130 —
gaps of 60 and 70, each ≥ the full ±60 personality swing. The SAFE ceiling (50 at
skep=+4) and the THREAT floor (60 at skep=−4) each sit on the correct side of the
boundary by construction with margin ≥ 0 at the extreme and ≥ 10 elsewhere, so a
±1 rounding never leaks a band across 50. The AMBIGUOUS band is centred so that
skep=0 lands EXACTLY on the boundary (securing=50, not `> 50` ⇒ no anxiety), which
makes the SIGN of skepticism the sole decider there.

## 4. The analytic oracle (pure arithmetic)

```python
def skepticism_bias(skep_level):        # trait_modulator_bridge STEP=15, neutral_ref=0
    return 15 * skep_level

def securing(exploration_urge, skep_level,
             competence_full=20, competence=20, sec_k=1, weight=10):
    # mirrors mod_securing exactly, with the fixed threat-context constants
    return (exploration_urge
            + (competence_full - competence)
            - sec_k * weight
            + skepticism_bias(skep_level))          # = exploration_urge - 10 + 15*skep_level

def anxiety_fires(exploration_urge, skep_level, securing_hi=50):
    # emx_anxiety: the only personality-moved conjunct is securing > securing_hi;
    # all other conjuncts (appraised, valence<0, threat, threat_persists,
    # competence<competence_lo) are held TRUE by the fixed constants of §3.
    return securing(exploration_urge, skep_level) > securing_hi
```

`anxiety_fires` returns the predicted anxiety LABEL (1 = interpreted as threat /
`ms.emotion == 3`; 0 = not) for a cell; the strict `>` mirrors the predicate's
`Gt(securing, securing_hi)`.

## 5. Predicted trait × ambiguity grid (ANALYTIC — deterministic)

anxiety label (1 = interpreted as threat, 0 = not), `securing` in parentheses:

| ambiguity \\ skep | −4 | −2 | 0 | +2 | +4 |
|---|---|---|---|---|---|
| **SAFE** (eu=0)      | 0 (−70) | 0 (−40) | 0 (−10) | 0 (20)  | 0 (50)  |
| **AMBIGUOUS** (eu=60)| 0 (−10) | 0 (20)  | 0 (50)  | **1 (80)** | **1 (110)** |
| **THREAT** (eu=130)  | 1 (60)  | 1 (90)  | 1 (120) | 1 (150) | 1 (180) |

## 6. The INTERACTION prediction (explicit)

- **Personality flips the anxiety label ONLY in the AMBIGUOUS band.** Reading the
  AMBIGUOUS row left-to-right, the label goes 0 → 0 → 0 → 1 → 1: rising skepticism
  bends the interpretation of the SAME ambiguous stimulus from safe to threat.
- **The SAFE and THREAT bands are personality-INVARIANT.** The SAFE row is all 0
  and the THREAT row is all 1 across the entire skepticism sweep: overt safe / overt
  threat stimuli are interpreted identically by every temperament.
- This is a **TRAIT × AMBIGUITY INTERACTION, NOT a main effect** of skepticism:
  skepticism has NO effect at the endpoints and a decisive effect in the middle —
  exactly the MacLeod & Mathews signature.

## 7. Falsifier and what a substrate FLAW would look like

- **FALSIFIER (the interaction must depend on the bias hook).** Force
  `skepticism_bias = 0` (equivalently do not call `sync_traits_to_modulator`, or
  seed skepticism at its neutral level 0). Then `securing = exploration_urge − 10`
  is independent of skepticism, the AMBIGUOUS-band label no longer flips with the
  trait, and the interaction VANISHES — the ambiguous band becomes
  personality-invariant too. If the interaction SURVIVES with the bias forced to
  0, the effect is not coming from the trait → set-point pathway and the claim is
  false.
- **WHAT A SUBSTRATE FLAW WOULD LOOK LIKE.** If personality flips the anxiety
  label in the SAFE or THREAT band (a SAFE cell reads 1, or a THREAT cell reads 0,
  for some skepticism level), then the bias has LEAKED past the appraisal
  structure: the trait would be producing a MAIN EFFECT rather than an
  INTERACTION, and the substrate would NOT reproduce the human dissociation. Such
  a cell is reported straight, never papered over — it would indicate either a
  constants/mapping error (bands not actually separated by the ±60 swing) or a
  genuine structural leak in the affect rules.

## 8. Files (all additive, trait_anxiety_ / TRAIT_ANXIETY prefixed)

- `docs/research/psychology_affect/TRAIT_ANXIETY_INTERPRETATION_PREREG.md` — this
  pre-registration.
- `domains/trait_anxiety_world.py` — the mechanical world adapter (ingest →
  `run_rules` → read; NO Python computes the emotion).

### Seed / isolation choice

**No new seed is authored.** The adapter reuses the EXISTING, already-landed
spine seeds by import — `drives` + `modulators` + `affective_state_core` — via
`trait_modulator_bridge.ensure_modulator_state`, and the `qualia_space` + CAN
identity seeds via `disposition.set_trait_seed`. Every one of these is loaded
only when the adapter is instantiated (opt-in), guarded by the established
rule-name sentinels, so **nothing new is auto-loaded**: `load_all_seeds` /
the base tree is byte-identical when the adapter is absent. This mirrors
marshmallow's `self_load_only` intent (existing tree byte-identical when absent)
while going one step further — there is no new seed file to load at all, so there
is nothing to gate. The three modulator bias offsets default to 0
(`skepticism_bias=0` ⇒ bias-free ⇒ default securing), so an agent whose
skepticism sits at its neutral level 0 reproduces the no-bias securing exactly
(default == today).

## 9. Discipline

Agent = graph; world = mechanical adapter. The WAIT-free adapter only SETS node
attrs (threat context, fixed competence/weight, `exploration_urge`) and the
skepticism seed, calls `sync_traits_to_modulator` (which writes `skepticism_bias`)
and `run_rules`, then READS the graph's produced `ms.emotion` label + `ms.securing`.
No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no `if/else` over
graph state selecting the emotion; no reward/punishment shaping. Integer-native
(no non-integer float Lits introduced). NO Rust (`runners/dsl` untouched);
`_native.abi3.so` untouched; toolbox solvers untouched; the canonical emotion
regions in `tools/build_modulator_seeds.py` are read-only reference here.

Do NOT merge to main; do NOT write the ledger row; NO git commit. These are
ANALYTIC predictions — no measurement numbers are claimed as produced yet.
