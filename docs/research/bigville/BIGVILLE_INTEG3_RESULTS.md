# BIGVILLE R10c — ACTIVATE THE DORMANT SOCIAL RUNGS — RESULTS

**Block 274000.** Base = `b7e7d772b0` (R10b BALANCE FIX). Additive-only, prefix
`bigville_integ3_` (+ one additive seed `bigville_journal_nightly`). **NO Rust**
(`git diff b7e7d772b0 -- runners/dsl` EMPTY). Own engine (canonical `.so` copied in for
import resolution, NOT committed). Run: `python scripts/bigville_integ3_run.py 1800 16
274000` → 1800 ticks = 50 days, 697 s (0.39 s/tick), living 16 (5 died, 5 born).

R10b assembled + balanced the town but its social life was LOADED-but-DORMANT. R10c
POPULATED the trigger entities + ARMED the periodic social events + EXPORTED the new
state — a populate/arm/export build, NOT decision-logic. **Every headline social rung
now FIRES.** The macro feed is the full town drama, not just deaths/evictions. The regime
MOVED (PUNCTUATED_WEAK → CLEAN_PERIODIC), and the move is honestly attributable to the
clock-scheduled cadences (below). Nothing was dialled to a regime.

## Per-rung fired/dormant table (measured)

| seed | status |
|---|---|
| `bigville_news_press` | **fired** — 7 Stories written→printed |
| `bigville_news_reach` | **fired** — 7 printings each informed ≥1 resident |
| `bigville_news_reach` (coalition) | **fired** — 7/7 coalitions formed |
| `bigville_council_gov` | **fired** — 7 councils convened (public address vs private held decision) |
| `bigville_council_board` | **fired** — 7 notices written→posted→read (10 residents each) |
| `bigville_school_learn` | **fired** — 100 pupil-lessons acquired (4 pupils × 25 class periods; skill 0→25) |
| `bigville_loud_comm` | **fired** — 16 street utterances (near hears content, far witness observes-only) |
| `bigville_loud_class` | **fired** — 16 classroom chatter→control beats (attending 1→0→1) |
| `bigville_drama_social` | **fired** — 7 drama beats (John undermines-while-benevolent; Mary infers hostile) |
| `bigville_journal_nightly` | **fired** — 800 JournalEntry nodes minted (16 residents × 50 nights) |
| `bigville_fisc_state` | dormant — not populated this rung (reported, not forced) |
| `bigville_goal_life` / `bigville_goal_dream` | dormant — not populated this rung |
| `bigville_coll_collect` | dormant — not populated this rung |
| `bigville_build_construct` | dormant — not populated this rung |
| `bigville_infant_care` | dormant — not populated this rung |

The six remaining siblings were left dormant honestly (their ingest lives on sibling
Python chains not on the integ MRO; a follow-on can populate them the same way). The
`bigville_news_press` SUPPRESSION path (`np_capture_suppresses`) is present but did NOT
fire: the council stayed responsive and the paper uncaptured, so every story printed — a
genuine read, not a suppressed one (capability present, condition never arose).

## The macro FEED is now the town drama (sample, verbatim)

```
t72   [school ] SCHOOL: class held, 4/4 pupils learned (skill levels 1,1,1,1)
t108  [loud   ] LOUD: Doreen Ferrety speaks (loud 8); near hearer content=1, far witness observes-only=0
t108  [loud   ] CLASS: pupil attending 1 -> chatter 0 -> teacher-control 1
t252  [paper  ] THE BIGVILLE TIMES printed: week 1 (informed 10/16 = 62%; COALITION FORMS)
t252  [council] COUNCIL convened: Mayor addressed 2.0, privately decided 1.0 (234 gap 1.0); noticeboard posts 1.5, 10 residents read it
t252  [drama  ] DRAMA: Mayor John held=undermine stated=benevolent (DECEPTIVE); Mary infers 'hostile'; 1/5 villagers back Mary
```

Feed event kinds over the run: `school 25, loud 32, paper 7, council 7, drama 7` (social)
+ `violence 17, death 5, eviction 5, foreclosure 2` (structural). R10b's feed was only the
last four; the social kinds are all new.

**THE ROOM WHERE IT HAPPENED (glass box).** WE hold what was said + every actor's state
even though residents only see the posted notice: the council's `public_address=2.0` vs
its `held_decision=1.0` (the 234 gap = 1.0) is opaque to townsfolk (the private tier is
occluded) but a LOOKUP for us; John's DECEPTIVE public face (stated benevolent, held
undermine) is the same atom pointed at the credibility network — and only 1/5 villagers
back Mary though her inference is correct (the "difficult-victim" credibility asymmetry).

## Journals — REAL per-resident nightly entries (verbatim, rendered from graph attrs)

The nightly journal is a new graph-native faculty: the additive seed
`bigville_journal_nightly`'s rule `jn_write_entry` MINTS a `JournalEntry` each night
capturing the resident's day FROM THEIR OWN GRAPH STATE (day/coin/grief/snap/wellbeing/
conflict/chosen-action/informed/backing, each copied by an `Attr` term); the export
RENDERS those attrs into a first-person line (a mechanical render, exactly as R10b's
`held` export formats reads — no prose authored in Python or the rule). Gate asserts the
recorded coin equals the live mover coin (a real read, not invented).

```
Doreen Ferrety:  Day 50. I have 5 coin. Today I chose to work. Grief weighs on me (1.0).
                 I felt the urge to lash out (2.00). Wellbeing sits at 100. I read the
                 news and know what happened in town.
Adelina Frost:   Day 50. I have 43 coin. Today I chose to snap. Grief weighs on me (50.0).
                 I felt the urge to lash out (50.00). Wellbeing sits at 78. I am torn
                 (conflict 11.0). I read the news and know what happened in town.
Alderman Hogget Purlin: Day 50. I have 82 coin. Today I chose to snap. Grief weighs on me
                 (50.0). I felt the urge to lash out (50.00). Wellbeing sits at 66. I am
                 torn (conflict 17.0).
```

Every clause is a live graph read. The informed/uninformed divide (R18) even surfaces in
the diary: Doreen/Adelina end "I read the news…"; the Alderman does NOT (he is not a
reader) — the same `jn_informed` flag the reach rules set, read back per person.

## Collective action vs the 3.5% (Chenoweth) reference

7 printings, **7/7 formed a coalition** (`np_coalition_forms`: informed ≥ quorum). The
informed-share was **mean 0.733, max 0.909** — a printed story reaches most literate
townsfolk, far above the 3.5% threshold, so the shared grievance becomes common knowledge
and the coalition forms every week. **Honest small-N caveat:** at N=16 residents the
3.5% quorum rounds to 1 person, so the absolute threshold is degenerate; the informed
SHARE (73–91%) is the meaningful quantity, and it clears 3.5% by a wide margin. The
mechanism (informed-share → quorum → coalition) is what fired; the 3.5% is the reference,
not a tuned target. A larger cast (the R10 scale datum) would make the quorum a real
fraction — a natural follow-on.

## RE-MEASURED regime (R10's UNCHANGED classifier)

**Verdict: `CLEAN_PERIODIC`** (was PUNCTUATED_WEAK in R10b). Evidence:

| metric | value | note |
|---|---|---|
| `heavy_tail_ratio` | 6.0 | heavy-tailed cascades present (≥5.0) |
| `stable_fraction` | 0.964 | long dwells (max dwell 71, mean 44.5) |
| `activity_total` / `max` | 131 / 6 | |
| `acf_peak` @ lag | **0.614 @ 108** | the dominant periodic component → CLEAN_PERIODIC |
| `cost_first→last decile` | 9.6 → 30.2 | cost rose (drama seeds loaded; not a runaway — not EXPLODED) |
| `cost_transition_coincidence` | 0.0 | cost spikes do NOT coincide with activity transitions |

**The honest finding — clock-scheduled social events impose periodicity.** The classifier
locks onto a dominant autocorrelation peak (0.61) at **lag 108 = exactly 3 days** — the
`LOUD_EVERY_DAYS=3` cadence — with the weekly paper/council/drama beat (lag 252 = 7 days)
underneath. The dwells are long and the cascades heavy-tailed (both SOC-like), but the
FIXED cadences make the macro signal "too regular to be adaptive," which is precisely what
`CLEAN_PERIODIC` means. This is a real and expected consequence of the design choice made
here: R10's founding principle was **"NO scheduled shocks — punctuations arise from
accumulated stress crossing rule thresholds"**, and R10c deliberately added CLOCK-scheduled
social events (a populate/arm build on a cadence). Arming social life on a clock trades the
weak-punctuated signature for a periodic one. **Nothing was dialled to a regime** — the
cadences were pre-registered scheduling, and whatever regime they produce is reported. The
clear next lever (stated as the follow-on, NOT bolted on here): make the social triggers
ENDOGENOUS — the paper prints when a newsworthy event actually occurs, the council convenes
when stress crosses a threshold, gossip spreads on a real grievance — so periodicity is
replaced by stress-driven punctuation, testing whether the town then reads
PUNCTUATED_EQUILIBRIUM with the social rungs live.

## Conservation held (no leak introduced)

Σcoin **start 2594 → end 2594, Δ = 0, invariant = True**. Activating the social rungs
introduced NO coin leak — after fixing two record-vs-balance accounting bugs found en
route: (1) the JournalEntry recorded the resident's balance under `coin` (double-counted by
`system_coin`) → renamed to `coin_held`; (2) the schoolmaster was first a town mover paid
from a Treasury (an external injection the town economy then perturbed) → made a DEDICATED
isolated node so the school sub-ledger (Treasury ↔ Master salary) is closed. Both are honest
mechanism, not tuning.

## Discipline

- **Base commit:** `b7e7d772b0`.
- **NO Rust:** `git diff b7e7d772b0 -- runners/dsl` is EMPTY (term.rs untouched); engine not rebuilt.
- **No `.so` committed:** `git diff --name-only b7e7d772b0 | grep '\.so$'` is empty (canonical `.so` copied in for imports only, gitignored).
- **Additive-only:** new files `worlds/bigville_integ3_world.py`, `worlds/bigville_integ3_state.py`, `scripts/bigville_integ3_run.py`, `tests/test_bigville_integ3_migrated.py`, `seeds/bigville_journal_nightly.json` (`self_load_only`), `results/bigville_integ3/*`, this doc + the prereg. Edits NO tracked R10/R10b/landed-seed file.
- **Gates:** `tests/test_bigville_integ3_migrated.py` **9/9**; `tests/test_failure_baseline_migrated.py` **11/11**. The two ~43-min bench oracles skipped (relaxed-oracle protocol — additive/no-Rust rung).
- **Pre-existing provenance red** (`test_engine_provenance_migrated`, engine `ada5f2ae` stale) persists — NOT mine (I change no Rust), untouched.
- Prereg + seed-claim committed as commit 1; build + results as commit 2. NOT merged (the supervisor merges `--no-ff`).
