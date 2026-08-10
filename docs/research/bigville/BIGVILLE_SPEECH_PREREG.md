# BIGVILLE RUNG 2/3 — EMERGENT SPEECH — PRE-REGISTRATION (block 278000)

**Written BEFORE any measured number.** The claim: an utterance is an EMERGENT
ACTION — an agent at an encounter (or trade) DECIDES whether / to whom / what
KIND to speak, or to STAY SILENT, by reading its held `Bond(A→B)` (rung 1,
block 277000) + conversational norms + affect, with **NO clock term**. This is a
standalone mechanism-demo world in the exact style of `BigvilleBondWorld`, proving
speech-initiation in isolation reading a Bond. Integration into the town is a
LATER rung and is NOT built here.

## Seed-claim (run before this line was filled in)

```
$ python scripts/seed_claim.py 278 278
SEED CLAIM 278-278: CLEAN -- no collision DETECTED.
  Scope: 981 files with seed sinks; 704 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block 278000 is clean. (This build draws no RNG seeds — it is deterministic
rule-firing — so the claim is a courtesy declaration of the block, per the
ledger discipline.)

## The design (from BIGVILLE_SPEECH_SCIENCE.md §2–§3, settled)

The decision is a **communicative-intention** event (Levelt conceptualizer,
§1.1). It EXTENDS the existing value-decision pattern — `af_choose_action`'s
`Argmax` over `Action` nodes (`seeds/bigville_affect_decide.json`) — into a
speech-act `Argmax` over a global menu of `SpeechOption` nodes that INCLUDES a
`stay_silent` option. Value (§2):

```
value(opt) = IfThenElse(opt.is_silence == 1,
                        enc.loquacity_threshold,          # per-agent trait (Mehl §1.5/§3.2)
                        talk_value(opt))
talk_value(opt) =  opt.base_value
                 + occasion_gain · occasion · talk_aff             # §1.7 encounter = OCCASION
                 + norm_gain · obligation · (greet_answer_aff·fpp_is_greeting
                                            + q_answer_aff·fpp_is_question)  # §1.3 adjacency, STRONGEST
                 + affect_gain · (affection·warm_aff
                                 + resentment·hostile_aff
                                 + fear·hedge_aff)                  # §3.4 relational affect → KIND
                 + affect_gain · confide_aff · tie_strength · share_salience  # §1.4 targeted sharing
                 + goal_gain · goal_pressure · goal_aff             # §3.1 goal
                 + arousal_gain · speaker_arousal · hostile_aff     # §1.4 arousal lowers hostile threshold
                 − face_cost · face_weight                          # §1.5 Brown&Levinson Wx
                 − civil_gain · stranger · talk_aff                 # §1.7 civil inattention suppressor
```

`chosen_speech_code = Argmax_opt value(opt).kind_code`. **No term reads a tick
counter or schedule** — firing is entirely a function of state (affect ×
relationship × norm × goal × occasion) over a per-agent threshold. THAT is what
makes it emergent (§3.2), and the control below is the falsifier.

KIND is DERIVED, not fixed (§3.2): adjacency-first (a pending FPP routes the
norm term to the matching option), else the affect coupling makes
resentment→barb, affection→warm greeting, fear→hedged, salient-event+high-tie→
share, neutral→smalltalk. Menu kinds:
`0 stay_silent · 1 greeting · 2 smalltalk · 3 barb · 4 hedged · 5 share · 6 answer`.

**Non-response is a MOVE (§1.3/§3.3):** when an obligation existed
(`obligation==1`) and the chosen code is silence (`0`), a legible
`NoticeableAbsence` node is MINTED and the snubbed target is wired
`-notices->` it. Silence is NOT the mere non-firing of a rule.

**Loudness (§3.4):** a distinct delivery gate — `sp_set_chosen_loudness` sets
`chosen_loudness = base_loudness + loud_arousal_gain·speaker_arousal`, then the
LANDED `lo_choose_loudness` (`seeds/bigville_loud_comm.json`, loaded and composed)
turns it into `eff_loudness`. Arousal is a real TERM, not a constant.

**Trade (§3.5):** a buy is a high-occasion, high-ratification, goal-present
encounter — the adapter mints a trade encounter with `goal_pressure>0` toward a
ratified shopkeeper, reliably opening talk.

## Pre-registered GATES (pass = the mechanism is real)

Every DECISION is a seed rule composing existing DSL Terms
(`Argmax/Plus/Times/Minus/Max/Min/IfThenElse/Attr/NodesOfType`, exactly the
`af_choose_action`/`lo_choose_loudness`/`bond_*` families). The adapter ONLY
mints agents/Bonds/menu/encounters, stamps inputs, arms flags, ticks
`run_rules()`, and reads back. ZERO new Rust.

1. **G-emergent-confidant** — encounter with a liked confidant (high tie +
   positive affect, no obligation) → chooses to SPEAK, KIND ∈ {greeting, share};
   with a salient event present the KIND is `share` (targeted to the confidant),
   without it `greeting`.
2. **G-emergent-rival** — encounter with a resented rival (high resentment) →
   chooses to SPEAK, KIND = `barb` (a cold/hostile kind reflecting the Bond).
3. **G-silence** — encounter with a stranger (no tie, no affect, no obligation)
   → chooses `stay_silent` (civil inattention). Proves the rule can DECLINE.
4. **G-adjacency** — a greeting FPP directed at A (`obligation=1`,
   `fpp_is_greeting=1`) → A responds, KIND = `greeting` (a greeting begets a
   greeting); a question FPP → KIND = `answer`.
5. **G-noticeable-absence** — an obligation exists but A stays silent (a very
   taciturn / withholding agent) → a legible `NoticeableAbsence` node is minted
   and the target `-notices->` it.
6. **G-loudness** — higher `speaker_arousal` → strictly higher `eff_loudness`;
   with `loud_arousal_gain=0` loudness is constant across arousal (the term does
   the work).
7. **G-trade** — a trade/buy encounter toward a ratified shopkeeper
   (`goal_pressure>0`) opens talk (not silence).
8. **G-falsifier (THE control)** — `schedule=True` zeroes every coupling gain
   (affect/norm/occasion/goal/arousal/civil = 0) and drops the silence line
   below the base talk options: the SAME confidant / rival / stranger / greeting
   encounters ALL collapse to ONE fixed kind (`smalltalk`) regardless of the
   Bond — the OLD forced-schedule behavior — and no `NoticeableAbsence` is ever
   minted. Emergence is proven by the contrast with gates 1–5.
9. **G-source-audit** — `worlds/bigville_speech_world.py` holds no Python rule
   engine (`graph_rewrite`/`gr.run`/`_match`/`_apply`/`make_rule`) and no if/else
   over an agent's graph valuation that selects an utterance/kind/loudness.
10. **G-discipline** — `git diff runners/dsl` is empty (zero new Rust); the seed
    composes only existing Term names (no `ShapeDecode`/`TransformDecode`/
    `DimInfer`/`space_quantize`).

## Tunable knobs (DIRECTION is the science, MAGNITUDE is soft; every one is a graph attr the rules read)

`norm_gain=3.0` (adjacency strongest, §1.3) · `affect_gain=1.0` · `occasion_gain=1.0` ·
`goal_gain=1.0` · `arousal_gain=1.0` · `civil_gain=1.0` · `face_weight=0.3` ·
`loquacity_threshold=1.0` (normal; taciturn ↑, garrulous ↓) · `loud_arousal_gain=0.6`.
The falsifier knob-set is the coupling gains; zeroed → schedule.
