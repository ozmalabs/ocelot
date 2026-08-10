# EMOTIONS AS EMERGENT MODULATOR REGIONS — re-derive Bach/Dörner (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`6517f10e27`** (LEDGER
`MICROPSI_STUDY_AND_IMPORT.md` — the study + import plan this rung executes).
Engine canonical **`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`,
shared build; `provenance_stamp` verdict **`shared`** — Rust source fingerprint
identical to this worktree). This rung adds **NO Rust**, `term.rs` diff EMPTY,
whole `runners/dsl` diff EMPTY. Seed block **207000–207999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 207000 207999
SEED CLAIM 207000-207999: CLEAN -- no collision DETECTED.
  Scope: 905 files with seed sinks; 613 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 0. What this is — RE-DERIVE, not invent

This rung re-derives **Bach/Dörner's emergent-emotion mechanism**
(Dörner PSI, *Bauplan für eine Seele* 1999; Bach *Principles of Synthetic
Intelligence* 2009; Bach "A Framework for Emergent Emotions" IJSE 2012; Bach
"Modeling Motivation in MicroPsi 2" AGI 2015) on our integer substrate. **The
architecture is theirs.** Emotions are not modules — they are *regions in a
small space of global cognitive MODULATORS*, and the modulators are *set by a
small DRIVE system*. Our contribution is the same as always: the **integer,
glass-box, byte-identity-gated, shared-atom instantiation**, plus the concrete
**parameter drop** — the 204000 rung's **11 authored per-emotion appraisal
rules** are replaced by **~6 modulator update rules + ~13 region predicates over
the shared modulator axes**, with the directed/undirected blends (bliss, angst,
grief) falling out for free. No novelty is claimed for the idea.

Companion prior art: `MICROPSI_STUDY_AND_IMPORT.md` (the study + import plan,
§3 is the build spec, §3.4 is this gate), `VISION_CORE_EMOTIONS_RESULTS.md`
(204000 — the 11 authored emotions + emulation table this rung reproduces from
modulator configuration).

**FRAMING (standing project rule):** understanding, not judgment; the FUNCTIONAL
regulator (drive → modulator → region → action tendency), NOT a claim to felt
qualia.

## 1. WHAT WILL BE BUILT (integer-native, NO Rust, NO new Term)

Two new seeds, all rules over EXISTING integer Terms
(`Plus/Minus/Times/IDiv/Ashr/Abs/Max/Min/IfThenElse/Gt/Gte/Lt/Lte/And/Or/Not/Eq`
+ the aggregate `Sum`/`Neighbours` for the Σ-over-drives arousal; all present in
`term.rs` today):

1. **`seeds/drives.json`** — a `Drive` node type
   `{name, target v_d, current c_d, critical v_0, weight, decay, gain, loss,
   half_life, last_tend, ...}` plus the MicroPsi demand equations as rules:
   - `drive_urge`: `urge = Abs(v_d − c_d)`
   - `drive_urgency`: `urgency = IDiv(Abs(v_d − c_d)·SCALE, Max(1, Abs(v_d − v_0)))`
   - `drive_decay`: **reuse the 196000 scale2 atom** —
     `c_d = Ashr(c_d, IDiv(now − last_tend, half_life))` (a drive IS a decaying
     held quantity).
   - `drive_pleasure` / `drive_displeasure`: sign of `Δc_d` → the valence
     contributions.
   Seeded drives feeding all 11 target emotions: **`affiliation`, `competence`,
   `exploration/certainty`** (§3.2). Affiliation gets a `legitimacy_signal`
   ingest (praise → +gain scaled by source `social_weight`; reproach → −loss)
   and a `nurturing` complement whose ABSENCE is the 204000 `w_supergraph≈0`
   psychopathy knob (a convergent glass-box realisation).

2. **`seeds/modulators.json`** (depends on `drives` + `staleness_decay` +
   `learning_progress_curiosity`) — a `ModulatorState` node (one per
   `EmotionHub`) + the **6 modulator update rules** per §3.1:
   - `valence` = Σ pleasure − Σ displeasure − Σ active_urge
   - `arousal` = Σ_d (urge_d · urgency_d) over active drives (`Sum`/`Neighbours`)
   - `resolution` = `base + urgency(leading) − k·arousal` (global scope — NEW)
   - `sel_threshold` = `strength(leading)·urgency(leading) − k·(1 − competence)`
     (resist-switch half — NEW)
   - `securing` = `uncertainty + (1 − competence) − k·importance(leading)` (NEW)
   - `competence` = running accumulator seeded from learning-progress (NEW)
   then the **~13 region predicates** (§3.3) that read the modulator vector +
   the leading drive's object/directedness context and set `action_tendency` —
   these REPLACE the 204000 per-emotion appraisals. Directedness
   (fear/anger/grief at-an-object vs joy/bliss/angst undirected) comes from the
   bound drive's object flags, not the modulators alone.

**Default-OFF discipline:** every new rule guards on `ModulatorState.enabled`.
Absent that flag EVERY existing path is byte-identical. This is how "retire the
authored list" reconciles with byte-identity: the emergent path is a NEW
default-OFF path; the G-emerge test runs it in ISOLATION (emergent seeds loaded,
the 204000 `core_emotions.json` NOT loaded) and shows the table still
reproduces — proving the 11 authored rules are redundant WITHOUT deleting them.

## 2. THE GATES (measured by `scripts/modulator_emergence_measure.py`;
pinned by `tests/test_modulator_emergence_migrated.py`)

**G-emerge (the headline, falsifiable).** The 11-row 204000 emulation table
(`VISION_CORE_EMOTIONS_RESULTS.md` §2) reproduces from the MODULATOR
CONFIGURATION — drives set → modulators computed → region assigned — with the
204000 `core_emotions.json` seed NOT present in the test's seed set:
  - `action_tendency` (1–11) **byte-identical** for all 11 emotions;
  - **exactly one** region fires per canonical case (one-fire-each);
  - the **null** case (a ModulatorState with no active drive / no directedness)
    fires none;
  - the **valence sign** (−1 / 0 / +1) byte-identical to the 204000 table;
  - the **arousal band** byte-identical to the 204000 table, where the band is
    the pre-registered 3-way binning of the 204000 arousal numbers:
    **HIGH `≥ 600`, MID `[150, 599]`, LOW `< 150`**, giving the expected bands
    | surprise MID | fear LOW | anxiety HIGH | anger HIGH | frustration HIGH |
    disgust MID | joy MID | sadness LOW | curiosity MID | boredom LOW |
    fulfilment MID |.
  FALSIFIABLE: if any tendency, valence sign, arousal band, one-fire, or
  null-fires-none does NOT reproduce from the modulator configuration, the claim
  fails and the straight null is reported — the table will NOT be loosened to
  pass.

**G-blend (free states).** bliss (positive / low-arousal / high-resolution —
distinct from joy), angst (undirected anxiety), grief (directed sadness) each
fall out as a DISTINCT region of the SAME modulator space, adding NO new
modulator, atom, or drive (only a region boundary). Each is shown to be a
distinct region (its modulator/directedness coordinates differ from its nearest
named neighbour — joy for bliss, anxiety for angst, sadness for grief), NOT a
relabel.

**G-social (affiliation unlocks).** With the affiliation drive present, an
affiliation frustration (anti-legitimacy signal → displeasure) produces the
expected NEGATIVE-valence social appraisal that 204000 could not reach; and
nurturing-ABSENCE reproduces the 204000 psychopathy signature FROM the drive
side (the somatic brake on a supergraph-harmful act removed), a convergent
glass-box realisation.

**G-minimal-pair (preserved).** The 204000 discriminators still hold THROUGH the
modulators: **fear↔anxiety** by the 196000 half-life alone (the threat drive's
`threat_half_life` — a decaying precision → fear, a persisting one → anxiety);
**anger↔frustration** by `blocker_present` alone; **curiosity↔boredom** by the
sign of learning-progress alone.

**G-discipline (unchanged bar).**
  - integer-native: 0 float-producing ops (`Div/Times*/Exp/Log/Sqrt/Sin/Cos` —
    note `Times` is integer here, audited by value) in any rule, and every
    attribute produced across all cases is an exact integer (0 non-integer
    cells). (`Sum`/`Neighbours`/`Times` are integer aggregates; audited by
    produced-value integrality.)
  - default-OFF byte-identity: with no `ModulatorState` created, an eye is
    byte-identical whether or not the two new seeds are loaded (5-frame photon
    fingerprint equal); no modulator nodes created on the default path.
  - `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (recorded BEFORE:
    **214 passed, 10 skipped, 0 failed** in this data-less worktree).
  - `bash scripts/per_area_settlement_regression.sh`: the SET of failing node
    ids BEFORE == AFTER (recorded BEFORE: 23 pre-existing reds — conversation/
    self seeds needing a live-daemon reconcile + `test_cortices_tick` +
    `test_composer_driver` — none introduced or removed by this rung).
  - `term.rs` diff EMPTY; whole `runners/dsl` diff EMPTY; canonical `.so` md5
    stays `793ce09ed498a749abb79aeaea44b92e` (NO engine rebuild — two other
    rungs measure against this canonical).
  - `provenance_stamp` verdict reported (`own`/`shared`).

## 3. HONEST FRAMING TO LEAD THE RESULTS WITH

This RE-DERIVES Bach/Dörner's emergent-emotion mechanism (2009/2012/2015) on our
integer substrate. The architecture is theirs; the contribution is the
glass-box, gated, shared-atom instantiation + the parameter drop (11 authored
rules → 6 modulators + region predicates, blends free). **If G-emerge does NOT
reproduce byte-identically, the straight null is reported — the table will NOT
be loosened to pass.** If a region needs a parameter the modulators cannot
supply, that is stated as a real finding about the mechanism's limits (e.g. the
directedness dimension is supplied by the bound drive's object, NOT the
modulators — an expected, documented boundary, not a patch).

Deterministic; no wall-clock claim. Prereg committed ALONE before any code.
