# EMOTIONS AS EMERGENT MODULATOR REGIONS — re-derive Bach/Dörner (RESULTS)

*Prereg (committed ALONE, before any number): `MODULATORS_EMERGENCE_PREREG.md`,
commit **`79be306a2a6c10a59f39bf4087bd18d7b7972657`**. Seed block **207000–207999**
(`SEED CLAIM 207000-207999: CLEAN`). Off `main` HEAD **`6517f10e27`**. Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED (seed + Python only;
`term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY; `provenance_stamp` verdict
**`shared`** — Rust source fingerprint identical). Raw:
`results/modulator_emergence.json`, `results/modulator_emergence/modulator_emergence.png`.*

## 0. What this is — RE-DERIVE, not invent

This rung **re-derives Bach/Dörner's emergent-emotion mechanism** (Dörner PSI,
*Bauplan für eine Seele* 1999; Bach *Principles of Synthetic Intelligence* 2009;
Bach "A Framework for Emergent Emotions" IJSE 2012; Bach "Modeling Motivation in
MicroPsi 2" AGI 2015) on our integer substrate. **The architecture is theirs.**
Emotions are not modules — they are **regions in a small space of global
cognitive MODULATORS**, and the modulators are **set by a small DRIVE system**.
Our contribution is the same as always: the **integer, glass-box,
byte-identity-gated, shared-atom instantiation**, plus the concrete **parameter
drop** — the 204000 rung's **11 authored per-emotion appraisal rules** are
replaced by **6 modulator update rules + 14 region predicates over the shared
axes**, with the directed/undirected blends (bliss, angst, grief) falling out for
free. No novelty is claimed for the idea.

**FRAMING (standing project rule):** understanding, not judgment; the FUNCTIONAL
regulator (drive → modulator → region → action tendency), NOT a claim to felt
qualia.

## 1. The mechanism as graph data (two seeds, 32 rules, zero Rust)

- **`seeds/drives.json`** (9 rules) — a `Drive` node
  `{name, target v_d, current c_d, critical v_0, weight, decay, gain, loss,
  half_life, ...}` with the MicroPsi demand equations as rules: `drive_urge`
  (`urge = |v_d − c_d|`), `drive_urgency`
  (`= |v_d − c_d|·SCALE / max(1,|v_d − v_0|)`), `drive_decay`
  (`c_d ← Ashr(c_d, IDiv(now − last_tend, half_life))` — **the 196000
  staleness_decay scale2 atom verbatim**; a drive IS a decaying held quantity),
  `drive_pleasure` / `drive_displeasure` (sign of `Δc_d`, the reinforcers), the
  threat channel (`drive_threat_precision`/`_persist`, again the 196000 atom),
  and the affiliation `legitimacy_signal` ingest.
- **`seeds/modulators.json`** (23 rules; `depends_on` **drives +
  staleness_decay + learning_progress_curiosity**) — a `ModulatorState` node
  (one per `EmotionHub`) + the **6 modulator update rules** (valence, arousal,
  resolution, selection-threshold, securing-rate, competence) + the **14 region
  predicates** (`emx_*`) + read-off. The regions read the modulator vector + the
  leading drive's object/directedness and set `action_tendency` — they REPLACE
  204000's 11 `em_*` appraisals (which are ABSENT from this seed set).

Every rule guards on `ModulatorState.enabled`; absent that flag every existing
path is byte-identical.

## 2. G-emerge (HEADLINE) — the 204000 table reproduced FROM modulator config

Each row is produced by setting a motivational **CONFIGURATION** (drive state +
knobs) — NOT a per-emotion rule — then letting the generic drive→modulator→region
machinery classify it, with **`core_emotions.json` NOT loaded**. Valence is
`sign(Σ pleasure − Σ displeasure − Σ urge)`; the arousal band is the
pre-registered 3-way binning (HIGH `≥600`, MID `[150,599]`, LOW `<150`).

| emotion | expected tendency | got | valence (got/exp) | arousal (band) | 204000 band |
|---|---|---|---|---|---|
| surprise | ORIENT | ORIENT | +0 / +0 | 500 (MID) | MID |
| fear | AVOID | AVOID | −1 / −1 | 128 (LOW) | LOW |
| anxiety | VIGILANCE | VIGILANCE | −1 / −1 | 1024 (HIGH) | HIGH |
| anger | APPROACH_BLOCK | APPROACH_BLOCK | −1 / −1 | 710 (HIGH) | HIGH |
| frustration | PERSIST | PERSIST | −1 / −1 | 710 (HIGH) | HIGH |
| disgust | REJECT | REJECT | −1 / −1 | 360 (MID) | MID |
| joy | REINFORCE | REINFORCE | +1 / +1 | 160 (MID) | MID |
| sadness | DISENGAGE | DISENGAGE | −1 / −1 | 16 (LOW) | LOW |
| curiosity | ENGAGE | ENGAGE | +1 / +1 | 160 (MID) | MID |
| boredom | LEAVE | LEAVE | −1 / −1 | 16 (LOW) | LOW |
| fulfilment | CONTRIBUTE | CONTRIBUTE | +1 / +1 | 160 (MID) | MID |

**11/11 tendencies byte-identical; 11/11 valence signs match; 11/11 arousal bands
match the 204000 binning; exactly one region fires per case; the null
configuration (enabled ModulatorState + appraised drive, no object) fires none.**
This is the falsifiable claim discharged: **the 11 authored appraisal rules are
redundant — the same table falls out of 6 modulator axes + region predicates,
without them present.** The fear↔anxiety arousal split (LOW 128 / HIGH 1024) is
NOT re-authored — it falls out of the **196000 half-life** on the threat drive
(short → precision decays below present → fear; long → persists → anxiety),
reproducing the exact 204000 numbers.

## 3. G-blend (free states) — bliss / angst / grief are distinct regions

| blend | code | valence | arousal (band) | resolution | fires | core hits |
|---|---|---|---|---|---|---|
| bliss (pos / LOW-arousal / HIGH-resolution) | 21 | +1 | 16 (LOW) | 524 | [bliss] | 0 |
| angst (undirected anxiety — no threat object) | 22 | −1 | 16 (LOW) | 614 | [angst] | 0 |
| grief (sadness DIRECTED at a loss object) | 23 | −1 | 16 (LOW) | 584 | [grief] | 0 |

Each fires ONLY its own region and NO core emotion, adding **no new modulator,
atom, or drive** — only a region boundary over the SAME axes. Distinctness (not a
relabel): **bliss** occupies (valence+, arousal LOW, resolution HIGH) where **joy**
does NOT fire (joy requires arousal ≥ MID); **angst** is undirected (no threat
object) where **anxiety** requires a persisting threat object; **grief** adds a
loss object where plain **sadness** is undirected. The generative win: more
affective states than 204000's 11, from fewer parameters.

## 4. G-social (affiliation unlocks) — reached FROM the drive side

- **Affiliation frustration.** A reproach (`legitimacy = −1`, scaled by the
  source `social_weight = 3`) drives `c_d` 1000 → 700, a **displeasure of 300**,
  producing **valence = −1** — the negative-valence social appraisal 204000
  explicitly named as a gap. Praise (`legitimacy = +1`) is the reward mirror
  (`c_d` 400 → 700, **pleasure 300**).
- **Psychopathy = nurturing-absence, from the drive/knob side.** On a
  supergraph-HARMFUL but individually-GOOD act (individual valence-raw +700,
  supergraph value −800): the **healthy** agent (`w_supergraph = 1`) nets
  `700 + (−800) = −100` → **declines** (somatic brake intact); the
  **nurturing-absent** agent (`w_supergraph = 0`) nets `700 + 0 = +700` →
  **endorses** (brake removed). This is the same mechanism 204000 landed on the
  value side (`VISION_CORE_EMOTIONS_RESULTS.md` §5), now realised from the
  motivational drive side — a convergent glass-box.

## 5. G-minimal-pair (preserved) — discriminators hold THROUGH the modulators

- **fear ↔ anxiety** by the **196000 `threat_half_life` alone** (1 vs 1,000,000,
  same epoch): precision decays below `t_present` (fear) or persists (anxiety).
- **anger ↔ frustration** by **`blocker_present` alone** (1 vs 0).
- **curiosity ↔ boredom** by **the sign of learning-progress alone**.

Each flips the classification across the boundary — now automatic consequences of
the shared modulator axes + one directedness flag, not bespoke per-emotion rules.

## 6. G-discipline (unchanged bar)

- **Competence is a running accumulator.** Fed a stream of learning-progress
  (+20/tick, carried `competence → competence_base`), general competence rises
  monotonically **20 → 40 → 60 → 80 → 100** — the MicroPsi general-competence
  heuristic.
- **Integer-native.** Zero float-producing ops (`Div/Exp/Log/Sqrt/Sin/Cos/Pow`)
  across all 32 rules (`Sum`/`Neighbours`/`Times`/`IDiv`/`Ashr` are integer
  aggregates); every attribute produced across all 11 canonical cases is an exact
  integer (0 non-integer cells).
- **Default-OFF byte-identity.** With no `ModulatorState` created, a 5-frame
  photon eye is byte-identical whether or not the two 207000 seeds are loaded; no
  `ModulatorState`/`Drive` nodes created on the default path. **No existing file
  modified** (the two seeds + measure + test + authoring tool are all new).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER
  (**214 passed, 10 skipped, 0 failed** — data-less worktree; unchanged).
- **Regression** `bash scripts/per_area_settlement_regression.sh`: the SET of
  failing node ids BEFORE == AFTER (23 pre-existing reds — conversation/self
  seeds needing a live-daemon reconcile + `test_cortices_tick` +
  `test_composer_driver`; none introduced or removed).
- **`term.rs` diff EMPTY; whole `runners/dsl` diff EMPTY; canonical `.so`
  `793ce09e…` UNCHANGED** (no engine rebuild).
- Gate: `tests/test_modulator_emergence_migrated.py` — **18/18**.

## 7. Honest situating, boundaries, and residuals

- **Re-derivation, not invention.** The architecture (drives → 6 modulators →
  emotions-as-regions) is Bach/Dörner's (2009/2012/2015). The contribution is the
  integer glass-box instantiation on the shared 196000/198000/202000 atoms + the
  parameter drop (11 authored appraisal rules → 6 modulator updates + 14 region
  predicates, blends free) + byte-identity to the prior gate's table.
- **Directedness is supplied by the bound drive, NOT the modulators — by design,
  and this is a documented finding about the mechanism, not a patch.** The
  modulator vector alone cannot express "anger *about someone*" or "grief *over a
  loss*"; the object/directedness flags (threat, blocker, contamination,
  loss_object, …) come from the leading drive the emotion is bound to. This is
  exactly MicroPsi's directed-vs-undirected split (§1.3 of the study), not a
  shortcut.
- **The arousal claim is BAND, not exact value.** The generic arousal
  (`Σ_d urge·urgency`, threat drives contributing their 196000-decayed precision)
  reproduces the 204000 *band* per emotion, not its idiosyncratic per-emotion
  read-off number (joy 448 vs our 160 — both MID; anger 800 vs 710 — both HIGH).
  The pre-registered binning (HIGH ≥ 600 / MID [150,599] / LOW < 150) is the
  claim, and it is met 11/11. The exact-number reproduction is NOT claimed and
  was not pre-registered.
- **The canonical cases are constructed to be separable** (as 204000's were); the
  contribution is that ONE generic modulator+region machinery classifies all 11
  with one-fire and passes the minimal-pair discriminators — not a claim that
  every real-world configuration is this clean. Off-diagonal robustness beyond the
  three discriminator pairs is not measured here.
- **Functional, not phenomenal.** Every claim is about the regulator (drive →
  modulator → region → tendency / value). No claim about felt qualia.
- **The 204000 authored rules are NOT deleted** — they remain in the default
  seed set. G-emerge proves them redundant by reproducing the table WITHOUT them,
  which is how "retire the authored list" reconciles with byte-identity: the
  emergent path is a NEW default-OFF path, not a mutation of the existing one.
