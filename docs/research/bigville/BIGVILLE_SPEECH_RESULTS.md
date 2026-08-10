# BIGVILLE RUNG 2/3 — EMERGENT SPEECH — RESULTS (block 278000)

The decision to speak is now an EMERGENT ACTION, not a schedule. An agent, at an
encounter (or a trade), DECIDES whether / to whom / what KIND to speak — or to
STAY SILENT — by reading its held `Bond(A→B)` (rung 1) + conversational norms +
affect, with **NO clock term**. Built as a standalone mechanism-demo in the
`BigvilleBondWorld` style; the full town is NOT wired (a later rung).

Every DECISION is a seed RULE composing existing DSL Terms; the adapter only
ingests / arms / ticks / reads. ZERO new Rust. Pre-registration:
`BIGVILLE_SPEECH_PREREG.md`.

## Files

- `seeds/bigville_speech_decide.json` — 3 rules: `sp_choose_utterance` (the
  headline speech-act `Argmax`, extending `af_choose_action`), `sp_noticeable_absence`
  (silence-is-a-move snub node), `sp_set_chosen_loudness` (arousal → the landed
  `lo_choose_loudness`). `self_load_only`, off by default.
- `worlds/bigville_speech_world.py` — the standalone mechanism-demo adapter
  (composes `BigvilleBondWorld` + loads `bigville_loud_comm`). Mechanical I/O only.
- `tests/test_bigville_speech_migrated.py` — 15 gates. **15 passed** on the
  canonical engine.
- `BIGVILLE_SPEECH_PREREG.md` — pre-registration; seed-claim CLEAN.

## Seed-claim (before any measured number)

```
$ python scripts/seed_claim.py 278 278
SEED CLAIM 278-278: CLEAN -- no collision DETECTED.
  Scope: 981 files with seed sinks; 704 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

## Glass-box evidence (read straight off the graph)

### EMERGENT — same rule, different state → different act (NO clock term)

```
confidant (aff3,tie4)          -> greeting      spoke=True    (warm greeting to a liked confidant)
confidant + salient event      -> share         spoke=True    (sharing TARGETED to the confidant, Rimé §1.4)
resented rival (resent3)       -> barb          spoke=True    (a cold/hostile kind from the Bond's resentment)
stranger (neutral)             -> stay_silent   spoke=False   (civil inattention — the rule DECLINES, §1.7)
greeting FPP (obligation)      -> greeting      spoke=True    (a greeting begets a greeting, §1.3)
question FPP (obligation)      -> answer        spoke=True    (a question begets an answer)
snub: obligation, taciturn     -> stay_silent   spoke=False   NoticeableAbsence minted / target-notices = True
trade (goal-present)           -> smalltalk     spoke=True    (a buy opens talk, §3.5)
```

- **EMERGENT (accept):** confidant → warm greeting / share; rival → barb. KIND
  reflects the Bond, not a schedule.
- **SILENCE (accept):** the stranger encounter → `stay_silent`. The encounter is
  an OCCASION, not a CAUSE — the rule can decline.
- **ADJACENCY (accept):** a greeting FPP → `greeting`; a question FPP → `answer`.
  When the obligation goes unmet (a withholding agent), a **legible
  `NoticeableAbsence` node is minted and the snubbed target `-notices->` it** —
  non-response is a first-class move, not a silent non-firing.
- **Sharing is NARROW:** the confide value is `tie_strength × share_salience`, so
  a low-tie acquaintance does not get the confidant-grade `share` from the same
  salient event (gated, §1.4 — not "aroused → talk to anyone").
- **Per-agent trait:** from the SAME neutral encounter a garrulous agent (low
  `loquacity_threshold`) speaks while a taciturn one stays silent (Mehl §3.2).

### LOUDNESS — arousal is a real term, not a constant (§3.4)

```
arousal=0.2 gain=0.6 -> eff_loudness=1.12
arousal=0.9 gain=0.6 -> eff_loudness=1.54     (higher arousal → louder)
arousal=0.2 gain=0.0 -> eff_loudness=1.00
arousal=0.9 gain=0.0 -> eff_loudness=1.00     (control: gain 0 → constant)
```

`sp_set_chosen_loudness` sets `chosen_loudness = base + gain·arousal`; the LANDED
`lo_choose_loudness` (composed from `bigville_loud_comm.json`) turns it into
`eff_loudness`.

### FALSIFIER — the control that proves emergence

`schedule=True` zeroes every coupling gain (affect / norm / occasion / goal /
arousal / civil) and drops the silence line below the base talk options:

```
confidant     -> smalltalk   (was: greeting)
rival         -> smalltalk   (was: barb)
stranger      -> smalltalk   (was: stay_silent)
greeting FPP  -> smalltalk   (was: greeting) ; no NoticeableAbsence ever minted
```

The SAME four encounters that produce four different behaviors under the emergent
rule ALL collapse to ONE fixed kind regardless of the Bond — the OLD forced
schedule. The affect / norm / occasion / civil layer is doing the work; remove it
and speech becomes a clock again. (Mirrors `af_choose_action`'s `affect_gain`.)

### EARNED bond (full composition with rung 1)

With NO hand-set affect, repeated cohabitation + care events move the Bond via the
rung-1 `bond_*` rules (`affect_affection = 3.0`, `tie_strength = 10.8`); the speech
rule then reads that EARNED affection and chooses `greeting`. The affect the
utterance reads is genuinely rule-produced.

## Discipline confirmations

- **Graph-native:** the utterance / silence / KIND / loudness / snub decisions are
  the three `sp_*` seed rules composing `Argmax / Plus / Times / Minus /
  IfThenElse / Attr / NodesOfType` — the exact `af_choose_action` /
  `lo_choose_loudness` / `bond_*` families. No exotic Term.
- **Source audit (gate):** `worlds/bigville_speech_world.py` contains none of
  `graph_rewrite` / `gr.run` / `_match(` / `_apply(` / `make_rule(`, and no if/else
  over an agent's graph valuation selects an utterance/kind/loudness. The only
  conditional is `schedule` — a world-config falsifier switch over config state.
- **NO Rust:** `git diff --name-only HEAD -- runners/dsl` is empty. No engine
  rebuild; ran against the present canonical `.so`. The seed is a COMPOSITION, as
  the science says (§5) — no new DSL Term was required.
- **Additive:** all new files prefixed `bigville_speech_` (+ the two doc files);
  no landed file edited. Rung 1 (`test_bigville_bond_migrated.py`) stays green
  (11 passed).

## Honest residuals (NOT patched — recorded for later rungs)

- **Integration deferred:** this is the mechanism in ISOLATION. Wiring it into the
  live town (real encounters from co-presence, real pending FPPs from the
  conversation seeds, feeding chosen utterances into `lo_deliver_content` /
  `lo_observe_act` reception) is the NEXT rung.
- **Preference organisation** (dispreferred SPPs carry delay/redress, §3.3) is not
  modelled — a later refinement; the hook (a marked dispreferred response) does
  not yet exist.
- **The affect magnitudes are stamped in most gates** (the Bond slots set as
  inputs) to isolate the speech decision from rung-1 update dynamics; one gate
  drives the EARNED path end-to-end to show the composition is real.
- **KIND granularity is coarse** (7 options). Real macroplanning (§1.1) composes
  the message from goal + recipient + prior turn; here KIND is a menu index the
  Bond/affect/adjacency terms select — sufficient for the initiation claim, not a
  full conceptualizer.
- **Menu magnitudes are soft knobs** (base_value / face_cost / the gains). The
  DIRECTION is the science; the magnitudes are tunable graph attrs, chosen so the
  pre-registered qualitative gates separate — not fit to a benchmark.
```
