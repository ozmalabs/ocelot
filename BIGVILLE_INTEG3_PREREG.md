# BIGVILLE R10c — ACTIVATE THE DORMANT SOCIAL RUNGS + RE-MEASURE — PRE-REGISTRATION

**Block 274000. Pre-registered BEFORE any recorded number.** Base = worktree base
commit `b7e7d772b0` (the R10b BALANCE FIX, `bigville_integ2_*`, on top of the whole
ladder). Seed-claim: `python scripts/seed_claim.py 274 274` → **CLEAN — no collision
DETECTED**; also `python scripts/seed_claim.py 274000 274999` → **CLEAN** (with the
tool's standing caveats: the unit is the seed integer; CLEAN means "no collision
detected", never "no collision exists").

R10 assembled the town; R10b balanced it (Σcoin conserved, deaths rare & caused,
verdict **PUNCTUATED_WEAK**). But the town's SOCIAL life is LOADED-but-DORMANT: the
rich social/communication seeds' RULES are loaded (21 sibling seeds, 0 conflicts) yet
their TRIGGER ENTITIES are never populated and their PERIODIC EVENTS are never armed on
the clock — so the paper never prints, the council never convenes, no gossip/coalition
spreads, journals are null, and the macro feed is only deaths/evictions. R10c makes the
social rungs FIRE — a POPULATE + ARM + EXPORT build (all admissible mechanical adapter
work), NOT a decision-logic build — then RE-MEASURES the regime with R10's SAME
classifier. Additive-only, prefix `bigville_integ3_` (+ one additive journal seed),
edits no tracked R10/R10b/landed-seed file (imports read-only), **NO Rust**, own engine.

## What R10c activates (the RULES already exist; this POPULATES + ARMS them)

`BigvilleInteg3World(BigvilleInteg2World)` subclasses R10b. In `__init__` it POPULATES
the trigger entities; `integ_step` ARMS the periodic social events on cadence (set the
seed's trigger flag/entity, then `self._run()`), exactly the R10b `wsink_armed` /
`decide_armed` arming pattern. Every DECISION stays a seed rule.

- **THE PAPER (`bigville_news_press` + `bigville_news_reach`).** Mint a `Town` hub with
  `has_resident` edges to a civic-mirror `Resident` per living villager (literacy drawn
  from a distribution — population = distribution over seeds), a persistent `Paper` +
  `Reporter`. On a WEEKLY cadence (and on a newsworthy event — a foreclosure/eviction/
  death/council decision), mint an `Event` from the REAL town event + a `Story` (+
  `Minutes`), reset the residents' `knows_event_flag`, mint a fresh `Coalition`, and
  `self._run()` → the press rules WRITE/PRINT (or a captured paper SUPPRESSES), the reach
  rules propagate (`np_witness_knows`/`np_reader_learns`), `np_count_informed` counts the
  informed share, `np_coalition_forms` forms the coalition iff informed ≥ quorum. **The
  quorum is set to ~3.5% of the population** (the Chenoweth flagship) — the informed
  share vs that threshold is MEASURED and reported, never dialled.
- **THE TWO-TIER COUNCIL (`bigville_council_gov` + `bigville_council_board`).** Constitute
  a `Council` with `Member`s (backing-graph) + a `Mayor` (John) + a `Board`. On scheduled
  council-days, mint a `Meeting` (`armed=1`, `now_day`≡0 mod cadence) with the civic
  residents as attendees → `cm_convene`/`cm_public_address`/`cm_member_vote`/
  `cm_private_decision` fire (public address vs private held decision = the 234 gap), then
  `post_notice` mints a `Notice` the clerk writes and the board posts → residents read it
  (literacy+access-gated). The posted decision → a board readout the export reads.
- **DRAMA (`bigville_drama_social`, + its deps `core_emotions`/`spite_skill`).** ATTEMPT:
  additively load drama_social + deps on the town engine; populate John (mayor,
  `EmotionHub`) / Mary (pastor, `MaryTom` + disposition codebook) / a villager credibility
  network; step it per council cadence (John's spite-economy decision, Mary's abductive
  ToM inference, villager backing). If the additive load conflicts or the chain does not
  fire, report DORMANT honestly.
- **SCHOOL (`bigville_school_*`) + LOUD (`bigville_loud_*`).** ATTEMPT: mint a `School`
  staffed by a schoolmaster mover + pupils (Skill + the STANDING-239 window dyad), hold
  lessons on schooldays (`sc_acquire`); mint `Utterance`/`Reception` pairs between
  co-located movers (`lo_deliver_content`/`lo_observe_act`) and a classroom chatter/
  control dynamic (`lo_chatter_distracts`/`lo_control_restores`). Report fired/dormant.
- **REMAINING SIBLINGS** (`bigville_fisc_state`, `bigville_goal_*`, `bigville_coll_*`,
  `bigville_build_*`, `bigville_infant_care`) — ATTEMPT where cheap; REPORT per-rung which
  fired vs stayed dormant, honestly, never forced.

## NIGHTLY JOURNAL (an additive seed — the user explicitly wants it)

Build `bigville_journal_nightly.json`: a rule `jn_write_entry` that, when a mover is
armed for the night (`journal_armed==1`), MINTS a `JournalEntry` node capturing the
resident's day FROM THEIR GRAPH STATE (day, coin, grief, snap-pressure, wellbeing,
conflict, chosen action, backing — copied by `Attr` terms), wires `wrote_journal`, and
clears the flag. The export READS the latest `JournalEntry` and RENDERS its attrs into a
first-person line — a mechanical render of real graph state, exactly as R10b's `held`
export formats real reads. **NEVER author journal prose in Python.** The adapter only
arms `journal_armed=1` on each living mover once per night (mechanical), then `self._run()`
lets the rule decide + mint. If a faithful graph-native journal genuinely cannot be built
this rung, it is left honest-null and reported so — no fabrication.

## The RE-MEASURE (pre-registered criteria)

RUN LONG (target 1800 ticks = 50 days, cast=16, seed=274000) with the social rungs
ACTIVE, and classify with R10's UNCHANGED `scripts/bigville_integ_measure.classify_regime`
(the 7-regime classifier, pre-registered thresholds). Social events (paper printings,
council convenings/decisions posted, coalition-forms, drama backings, journal writes) are
counted into the per-tick `activity` stream so the regime reflects the richer dynamics.
Report the NEW verdict vs R10b's PUNCTUATED_WEAK — with evidence (heavy_tail_ratio,
activity head/tail, cost_transition_coincidence, dwell/cascade). RE-EXPORT the town-state
contract to `results/bigville_integ3/townstate.json` (now with a non-null paper feed,
board readout, informed-share/coalition metrics, and per-villager journals).

## ANTI-TUNING COMMITMENT (absolute, binding on the verdict)

I POPULATE trigger entities + ARM periodic events + EXPORT the new social state. I do
**NOT** tune coefficients/thresholds/cadences to manufacture self-organized criticality,
a coalition crossing the 3.5% line, or any regime. Cadences (weekly paper, scheduled
council days, schooldays) are pre-registered scheduling, NOT dials on a result. **Whatever
regime, informed-share, and coalition outcome emerge after the honest activation are
REPORTED** — a coalition that does or does not form, a regime that moves or does not, are
all valid findings. Every social DECISION is a seed rule; if any decision content is
genuinely missing a rule I build it AS A SEED (graph data composing existing DSL Terms),
never as Python prose.

## Acceptance evidence to report

- **Per-rung fired/dormant table** — for EACH social seed: did its rules FIRE (with a
  count — N Stories printed, M councils convened, K residents informed, coalition y/n,
  pupils learned, chatter/control events, drama backings) or stay DORMANT (why).
- **The macro FEED** now contains social events (paper printings, council decisions
  posted, gossip/coalition, drama) — sample entries shown, not just deaths/evictions.
- **Journals** — REAL per-resident `JournalEntry` reads (2–3 verbatim, confirmed to
  render graph state), or honest-null with the reason.
- **RE-MEASURED regime** — the R10-classifier verdict + heavy_tail_ratio + activity
  head/tail + cost_transition_coincidence; informed-share vs the 3.5% threshold if a
  coalition path fires.

## Discipline

Own engine (canonical `.so` copied in for import resolution, NEVER committed —
`git diff --name-only b7e7d772b0 | grep '\.so$'` empty). **NO Rust**
(`git diff b7e7d772b0 -- runners/dsl` empty, incl. `term.rs`). Additive-only; NEW files
prefixed `bigville_integ3_` (+ the additive `bigville_journal_nightly` seed),
`self_load_only` where possible; edits no tracked R10/R10b/landed-seed file. Gates:
`tests/test_bigville_integ3_migrated.py`; `tests/test_failure_baseline_migrated.py`
(must stay 11/11). The pre-existing canonical-stale provenance red
(`test_engine_provenance_migrated`, engine `ada5f2ae` stale vs a peer's committed Rust) is
NOT mine (I change no Rust) — it persists, untouched. Two commits: (1) this prereg +
seed-claim, (2) the build + results. DO NOT merge (the supervisor merges `--no-ff`).
