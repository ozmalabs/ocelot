# Bigville social experiment #1 — RESULTS

Predictions registered in `scripts/bigville_social_experiment.py`'s own
header docstring, before running. **Belief-state predictions: 3/3
confirmed. Speech predictions: 1/1 confirmed — and it is the headline
finding, evidence of a missing system, not a null to explain away.**

**Rung 2 (§5 below) closes that finding.** The user's own correction
went deeper than "populate the coefficients": there should be no fixed
menu label at all — spontaneous speech should interface with real
free-text utterances. Fixed in `worlds/bigville_ocelot_adapter.py::
decide_speech` (routes its winner through the SAME `goal_utterance`
free-text pipeline) + `worlds/bigville_speech_world.py::SPEECH_MENU`
(bigville repo — real, non-zero `warm_aff`/`hostile_aff`/etc
coefficients, the originally-diagnosed missing data).

## 1. Cast

Four `BigvilleOcelotResident` instances (real graph-native Ocelot
cognition, `worlds/bigville_ocelot_adapter.py`), each a hand-authored
theory-testing archetype, all directed at one shared target (**Landlord**,
a neutral control) so the three attitudes are directly comparable:

- **Resentful** — seeded baseline resentment (`resentment_debt=1.0`,
  `regard=-0.5`) via `personality.social_dispositions`, then 2 negative
  incidents recorded via `record_hate_incident` (repeated grievances —
  mechanically the SAME primitive `HATE_ATTRIBUTION_PREREG.md` uses, a
  real recorded event, not a belief injection).
- **Grateful** — seeded baseline gratitude, then 2 positive incidents.
- **Envier** — seeded `deservingness_prior=-0.8`, then 3
  `record_peer_observation(peer_did_well=True)` calls about Landlord (an
  advantaged peer).
- **Landlord** — no seeded dispositions, the control.

## 2. Live run (`scripts/bigville_social_experiment.py`)

```
Resentful's held state about Landlord:
  regard_for:Landlord = -1.1
  removal_desire_for:Landlord = 1.08
  pity_for:Landlord = 0.0
  admiration_for:Landlord = 0.0
  devaluation_for:Landlord = 0.0
  controllability_for:Landlord = 0.0
  _pattern = {'crystallized': True, 'resentment_debt': 1.0, 'gratitude_debt': 0.0, 'incident_count': 2}
  consequence_route (from the crystallizing call) = 'removal'
PREDICTED: crystallized=True, consequence_route='removal', removal_desire_for > 0

Grateful's held state about Landlord:
  regard_for:Landlord = 1.1
  removal_desire_for:Landlord = 0.0
  pity_for:Landlord = 0.0
  admiration_for:Landlord = 1.62
  devaluation_for:Landlord = 0.0
  controllability_for:Landlord = 0.0
  _pattern = {'crystallized': True, 'resentment_debt': 0.0, 'gratitude_debt': 3.0, 'incident_count': 2}
  admiration_consequence_route (from the crystallizing call) = 'admiration'
PREDICTED: crystallized=True, consequence_route='admiration', admiration_for > 0, gratitude_debt > 0

Envier: relative_self_worth=-0.3863 deservingness=-0.8000 -> envy=malicious
PREDICTED: envy='malicious'

PREDICTED vs ACTUAL -- decide_speech toward Landlord
PREDICTED: all four characters choose the IDENTICAL speech kind, since SpeechOption's relational-affect coefficients are never set.
  Landlord   -> says toward Envier     kind=smalltalk  spoken=True
  Resentful  -> says toward Landlord   kind=smalltalk  spoken=True
  Grateful   -> says toward Landlord   kind=smalltalk  spoken=True
  Envier     -> says toward Landlord   kind=smalltalk  spoken=True

ISOLATION CHECK -- Landlord's own graph is unaffected by others' incidents
Concepts on Landlord's OWN substrate naming Resentful/Grateful as a target: NONE (expected)
```

## 3. Predictions

1. **Resentful crystallizes hate, routes to removal** — `PASS`. Only 2
   negative incidents (not the full `HATE_STABILITY_THRESHOLD+3`
   headroom) were needed because the SEEDED baseline
   (`resentment_debt=1.0`) already counted toward the confirm streak —
   itself a confirmation that `personality.social_dispositions` and
   live-recorded incidents compose on the SAME ledger, not two separate
   tracks.
2. **Grateful crystallizes admiration, gratitude_debt accumulates** —
   `PASS`, same 2-incident finding for the identical reason (seeded
   `gratitude_debt=1.0` baseline).
3. **Envier reads as malicious envy** — `PASS`. `relative_self_worth=
   -0.39` (Landlord repeatedly observed doing well, 3/3) combined with
   the seeded negative `deservingness_prior=-0.8` → `read_envy` →
   `"malicious"`, exactly Smith & Kim (2007) / Van de Ven, Zeelenberg &
   Pieters (2009)'s predicted combination (disadvantage + perceived
   unfairness → hostility toward the advantaged party, not aspiration).
4. **decide_speech is insensitive to disposition — `PASS`, and this is
   the headline finding.** All four residents — from a resident who has
   just crystallized hate toward Landlord to one who has just
   crystallized admiration — choose the IDENTICAL speech kind
   (`"smalltalk"`) toward them. Traced to source, not just observed:
   `worlds/bigville_speech_world.py`'s `SPEECH_MENU` sets only `kind_code`/
   `is_silence`/`talk_aff`/`base_value` per option; it never sets
   `warm_aff`/`hostile_aff`/`hedge_aff`/`confide_aff`/`greet_answer_aff`/
   `q_answer_aff`/`goal_aff`/`face_cost` for ANY option, so every term in
   `sp_choose_utterance` (the seeded rule, `bigville_speech_decide.json`)
   that multiplies the Bond's relational-affect state by an option
   coefficient evaluates to zero regardless of that state. What remains
   is a fixed per-option `base_value` constant, and `smalltalk`'s
   (`0.5`) is the highest of any non-silence option — so `smalltalk` wins
   the argmax UNCONDITIONALLY. This was predicted from reading the seed
   rule and the menu data BEFORE running (`sp_choose_utterance`'s own
   comment even names the intended coupling: *"resentment->barb,
   affection->warm greeting, ... neutral->smalltalk"* — the intent is
   real and documented; the wiring to realize it is absent), then
   confirmed empirically.
5. **Isolation** — `PASS`. Landlord's own substrate holds zero Concepts
   about Resentful or Grateful — each resident's incidents live only on
   their own graph, exactly matching the "actors only engage through the
   world" constraint (nothing here injected a belief onto ANOTHER
   resident's substrate).

## 4. Diagnosis — missing system, not emergence, on the speech axis

Per the framing this experiment was built to test against: this is
**evidence of a missing system**, cleanly localized. The BELIEF layer
(regard/trust/hate/envy/admiration — everything built in Phases A–G plus
`RESIDENT_TRUST_PREREG.md`/`SELF_EFFICACY_PREREG.md`/`ENVY_PREREG.md`) is
real, correctly wired through `BigvilleOcelotResident.seed_character` →
`_apply_social_aspects`, and responds exactly as predicted to both seeded
backstory AND live-recorded incidents. The SPEECH-CHOICE layer
(`decide_speech`) reads a real Bond (correctly projected from that SAME
belief state via `_speech_bond`) but the SpeechOption menu it argmaxes
over has never had its relational-affect coefficients populated — a data
gap in `worlds/bigville_speech_world.py::SPEECH_MENU`, not a design flaw
in `sp_choose_utterance` (whose formula already correctly multiplies by
those coefficients) and not a gap in the Ocelot-side belief mechanisms
tested here. **Fixing it means adding real, per-option
`warm_aff`/`hostile_aff`/etc values to `SPEECH_MENU`** (e.g. `barb` should
carry a nonzero `hostile_aff`, `greeting`/`thanks` a nonzero `warm_aff`)
— a bigville-repo, world-adapter-side data fix, not an Ocelot change.
This is a DIFFERENT, more specific gap than the "nothing perceives an
utterance back into belief" finding named before this experiment ran
(that gap — closing the OTHER direction, hearing something updating
belief — remains separately unaddressed and is still Stage 2, unbuilt).

## 5. Rung 2 — the fix: real free text, not a menu label

User's correction: *"there should not be a speech menu, it should
interface with the free text utterances."* Investigated (2 Explore
agents) before touching either repo — see the approved plan for full
findings. Two changes, both landed:

- **`worlds/bigville_speech_world.py::SPEECH_MENU`** (bigville repo) —
  gave each option real, non-zero coefficients matching its actual
  emotional character (`barb`/`complaint` → `hostile_aff`; `greeting`/
  `smalltalk`/`thanks`/`offer`/`promise`/`farewell` → `warm_aff`;
  `hedged` → `hedge_aff`; `share` → `confide_aff`; `request`/`offer`/
  `question`/`promise` → `goal_aff`). Confirmed zero live blast radius in
  bigville's own runtime (its `load_seed_manifest` never executes rules
  at all — bigville-side suite stayed 208/208 green, unchanged).
- **`worlds/bigville_ocelot_adapter.py::decide_speech`** (this repo) —
  the chosen `kind` (still selected by the SAME seeded Argmax, now with
  real coefficients) is renamed via a new `KIND_TO_PREDICATE` table into
  `_speech_frame`'s existing alias vocabulary and fed through
  `goal_utterance` — the SAME free-text pipeline `goal_utterance`'s own
  direct callers already used. The old `_speech_utterance`-only path
  (loudness attrs, no meaning, no text) is now only half the story:
  loudness delivery is kept (a real, separate, tested mechanism,
  Schegloff/arousal-coupling) and REAL rendered text is added alongside
  it. A per-call occasion nonce (`"spontaneous_%d_%s"`) avoids
  `add_communicative_goal`'s meaning-key dedup silently going silent on
  a repeated speech-act shape (the gotcha the Explore agent found).

**Live re-run of this experiment's OWN speech section, post-fix**
(`scripts/bigville_social_experiment.py`, updated to call `decide_speech`
spontaneously — no pending greeting FPP — so disposition, not adjacency,
drives the choice):

```
SPONTANEOUS (no pending greeting/question):
  Landlord   -> toward Envier     kind=barb       act=complaint  spoken=True text='I complain Envier.'
  Resentful  -> toward Landlord   kind=barb       act=complaint  spoken=True text='I complain Landlord.'
  Grateful   -> toward Landlord   kind=greeting   act=greeting   spoken=True text='I greet Landlord.'
  Envier     -> toward Landlord   kind=barb       act=complaint  spoken=True text='I complain Landlord.'

CONTROL -- WITH a pending greeting FPP (adjacency should dominate):
  Landlord   -> toward Envier     kind=greeting   act=greeting   spoken=True text='I greet Envier.'
  Resentful  -> toward Landlord   kind=greeting   act=greeting   spoken=True text='I greet Landlord.'
  Grateful   -> toward Landlord   kind=greeting   act=greeting   spoken=True text='I greet Landlord.'
  Envier     -> toward Landlord   kind=greeting   act=greeting   spoken=True text='I greet Landlord.'
```

**The original prediction (all four identical) FLIPS as predicted for
Resentful vs. Grateful** — Resentful (real seeded resentment) routes
hostile (`barb`/`complaint`, real rendered text); Grateful (real seeded
warmth) routes to `greeting`. The CONTROL run confirms the adjacency norm
term still correctly dominates a real pending greeting regardless of
disposition (Sacks-Schegloff-Jefferson: a greeting obligates a return
greeting) — both regimes now behave as designed.

**New, honestly-reported residual, found live, not tuned away**: a
COMPLETELY NEUTRAL resident (Landlord and Envier, whose Bond toward the
other carries zero affect either way) ALSO routes to `barb`/`complaint`
in the spontaneous case. Traced to source: `sp_choose_utterance` has a
SECOND, separate `hostile_aff`-weighted term — `arousal_gain ×
speaker_arousal × hostile_aff` — independent of the Bond's actual
`affect_resentment`. `decide_speech`'s own default `arousal=0.4` alone
is enough, via this channel, to make `barb`'s total value (`base_value
0.2 + 0.4`) beat `smalltalk` (`0.5 + 0`) and `greeting` (`0.3 + 0`) even
with zero resentment. This is a REAL design tension (Schachter-Singer
excitation-transfer says baseline arousal SHOULD lean speech hostile in
principle) rather than a bug in the fix just landed, but the DEFAULT
magnitude (0.4) reads too strong for an ordinary calm encounter. Left
UNTUNED here — changing a weight post-hoc specifically to make a neutral
character look calmer is exactly the "move the goalpost" pattern this
project's own discipline forbids. Named as a concrete follow-up, not
silently smoothed over. The new regression test
(`test_decide_speech_diverges_by_disposition_not_always_smalltalk`)
sidesteps this confound deliberately by calling with `arousal=0.0`.

## 5b. Rung 3 — bucket-familiarity prior (Tajfel/Zajonc, not tuned to flip the outcome)

User's read of the rung-2 residual: the hostile default is CORRECT for a
genuinely unclassified stimulus, but almost nothing real is genuinely
unclassified — bucket-matching (role/class/SES-tier) is near-instant, and
bucket membership ALONE (mere exposure, Zajonc 1968; an arbitrary shared
category needs no real content, Tajfel, Billig, Bundy & Flament 1971)
should read as mild warmth, not stranger-zero. Landed:
`bigville/game.py::_shared_bucket_count` (mechanical role/klass/group
attr comparison, exposed on `nearby_residents` alongside `tie_strength`/
`band_code`) + `worlds/bigville_ocelot_adapter.py::_speech_bond`'s new
THIRD branch (neither live `relationship` nor seeded `social_
dispositions` present, but `shared_bucket_count>0`): `affect_affection =
min(FAMILIARITY_CAP=0.3, personality.get("ingroup_affinity", 0.4) *
shared_bucket_count/3)`. A target sharing NOTHING still falls through to
hard zero — rung 2's finding for a TRULY unclassified stranger is
unchanged by design. A real seeded/live disposition still wins outright
(mutually exclusive branches — familiarity never blends in or dilutes an
actual relationship, confirmed by
`test_shared_bucket_familiarity_never_beats_a_real_seeded_disposition`).

**Live re-run, Landlord↔Envier (the genuinely neutral pair from rung 2,
no `social_dispositions` either way)**:

```
shared_bucket_count=0 -> affect_affection=0.0000 kind=barb  act=complaint text='I complain Envier.'
shared_bucket_count=3 -> affect_affection=0.3000 kind=barb  act=complaint text='I complain Envier.'
```

**Honestly reported, not adjusted**: `shared_bucket_count=0` reproduces
rung 2 exactly (unchanged, as predicted). `shared_bucket_count=3` DOES
NOT flip the winner — hand-computed: `greeting = 0.3 (base) + 1.0
(warm_aff) × 0.3 (affection) = 0.6`; `barb = 0.2 (base) + 1.0 (hostile_
aff) × 0.4 (arousal_gain × speaker_arousal, the rung-2 channel) = 0.6` —
an EXACT TIE at these default parameters (`arousal=0.4`,
`ingroup_affinity` default `0.4`, `FAMILIARITY_CAP=0.3`), and the
Argmax's tiebreak lands on `barb`. The fix genuinely NARROWS the margin
(rung 2: barb beat greeting outright, `0.6` vs `0.3`; rung 3: dead heat)
rather than cleanly flipping it. Raising `FAMILIARITY_CAP` specifically
to force a flip here would be tuning a registered constant to make a
demonstration look nicer — not done. The margin-narrowing itself IS the
real, honest result: bucket-sharing measurably counteracts the
undifferentiated-arousal channel, exactly as the theory predicts, without
fully overriding a channel that (per rung 2) reflects a real, separately-
justified mechanism (Schachter-Singer arousal-as-undifferentiated). A
higher `shared_bucket_count` (the plan capped tracked buckets at 3;
`workplace_kind` was explicitly deferred) or a resident with an
above-default seeded `ingroup_affinity` would likely flip it — not
measured here, named as a natural follow-up rather than pre-answered.

## 5c. Rung 4 — the arousal channel itself retired
(`AROUSAL_CHANNEL_RETIREMENT_PREREG.md`/`_RESULTS.md`, full detail there)

The `arousal_gain × speaker_arousal × hostile_aff` term that CAUSED
rung 3's exact tie is deleted — `seeds/affect_coupling.json`'s
`arousal_hostile` channel now carries this coupling, gated by each
resident's own `hostile_gain` disposition (armed only when
`coupling_on=1`, still off by default everywhere in this experiment).
The tie is gone, not narrowed further: `shared_bucket_count=0` now
resolves to `smalltalk` (no hostile term left to contend with
`base_value` at all); `shared_bucket_count=3` resolves to `greeting`
(the pre-existing `FAMILIARITY_CAP` warm contribution, now visible
without a competing universal hostile default). Neither number was
tuned to produce this — it is the mechanical consequence of removing the
term rung 2 originally diagnosed as the defect.

## 6. Honesty notes

**Does establish**: a real, hand-authored cast of theory-testing
archetypes, driven through actual Ocelot cognition, whose belief
mechanisms (hate/admiration crystallization, envy) behave exactly as this
session's own PREREGs predict, including composing correctly with
`BigvilleOcelotResident`'s newly-built `social_dispositions` seeding path
(built for an unrelated Monopoly cognition-provider effort, confirmed to
generalize cleanly to this social-village use). Localizes, with a source
citation, a real and specific "missing system" — AND closes it (§5):
`SPEECH_MENU`'s relational-affect coefficients were unset, so spontaneous
speech was disposition-blind; now it isn't, and real free text is
produced via the same pipeline `goal_utterance` already used.

**Does NOT establish**: the OTHER known gap (perception → belief update
from a heard utterance) — this experiment only fed EXPERIMENTER-supplied
incidents (matching the "actors only engage through the world"
convention: a real recorded event, applied via the same primitive a
genuine interaction would use), it did not run a live two-actor
conversation through `BigvilleGame.step()`. Does NOT test physical
`major_action` affordance selection (`decide()`/`replace_options()`) at
all. Does NOT touch `worlds/bigville_world.py`'s own SEPARATE, parallel
`BigvilleOcelotActor`/`_speech_goal` implementation (bigville's default
non-Ocelot NPC cognition) — explicitly out of scope, named in both plans.
Does NOT wire `OcelotBackend`/`BigvilleGame` to seed a cast-100 resident's
own identity/personality automatically (named, separate gap, still open).
Does NOT extend bucket-tracking to `workplace_kind` (not currently a live
actor attr). Does NOT tune `FAMILIARITY_CAP`/the rung-2 arousal channel to
force rung 3's exact tie into a clean flip (§5b) — reported as measured.

## 7. Files

- `scripts/bigville_social_experiment.py` (new, later edited for the
  spontaneous-vs-adjacency split and the rung-3 bucket-familiarity
  probe — the harness; predictions are registered in its own header
  docstring)
- `docs/research/bigville/BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md` (this file)
- `worlds/bigville_speech_world.py` (bigville repo, edited — real
  `SPEECH_MENU` coefficients)
- `worlds/bigville_ocelot_adapter.py` (edited — `decide_speech` routes
  through `goal_utterance`; new `KIND_TO_PREDICATE`, `_speech_occasion`,
  `FAMILIARITY_CAP`, `_speech_bond`'s bucket-familiarity branch)
- `tests/test_bigville_ocelot_adapter.py` (edited — text/act assertions;
  new `test_decide_speech_diverges_by_disposition_not_always_smalltalk`,
  `test_shared_bucket_count_gives_familiarity_warmth_not_stranger_zero`,
  `test_shared_bucket_familiarity_never_beats_a_real_seeded_disposition`)
- `bigville/game.py` (bigville repo, edited — `_shared_bucket_count`,
  `nearby_residents` gains `klass`/`group`/`shared_bucket_count`)
- `tests/test_bigville_game_api.py` (bigville repo, edited — updated key
  set; new `test_shared_bucket_count_counts_matching_role_klass_group`,
  `test_shared_bucket_count_zero_when_a_bucket_is_unset`)
