# The self-directed speech-learning world — the babble loop matured into the POLYGLOT

The agent self-directs a **3-axis curriculum** (granularity x source x language),
hears speech the WORLD plays, commits a **BLIND guess** in feature space, gets a
**COOKIE** iff right, **LEARNS** (banks the exemplar), **SAVES** itself, and
**REPORTS** held-out per-cell progress every 60s. It becomes multilingual by
self-directing across languages — the POLYGLOT ("people who speak many languages
are the machinery we need").

Working dir: `research/experiments/gamma-substrate`. Nothing committed; left in the
working tree for review.

## Files

- `domains/self_directed_speech_world.py` — the **SpeechWorld adapter** + the
  graph-resident loop pieces:
  - feature extraction (pure DSP: gammatone-flat + freq-sharp FFT ear + sharp
    all-pole spectral-envelope ear — three robust orthogonal channels the agent owns),
  - `blind_guess` = the agent's **many-settings Argmax-of-product** graph Term over
    BANKED exemplars (the cognition+hat in feature space, iter-46/49),
  - `bank_exemplar` = the cookie's effect (grow the cell's lexicon + exemplar bank),
  - `tts` (espeak-ng, any language) + corpora loaders (FSDD real human digits,
    TVTropes real text) + `inject_noise` (the hard source),
  - `install_speech_world_rules` = the **2 seeded GOALS** + the report/save **reflex
    Rules** + the curriculum **PICK_TERM** (a graph Argmax).
- `scripts/self_directed_speech_loop.py` — the **runner** (world adapter only):
  plays the world, advances the clock, ticks; the GRAPH decides everything.

## (1) The adapter + the graph-resident loop + the 2 goals (architecture audit)

**Python is adapter-only** (CLAUDE.md): it downloads/synthesises speech (espeak-ng),
loads corpora (FSDD, TVTropes), draws text, injects noise, turns audio into feature
mutations, delivers the cookie BIT, advances the clock, and writes the save file.
There is **no Python `if`/`else` that decides** what to drill, what the guess is, or
when to learn/report/save. Specifically:

| Decision | Where it lives (graph-resident) |
|---|---|
| 3-axis curriculum CHOICE | `PICK_TERM` — an `Argmax` over `CurriculumCell` of `deficit + explore_bonus`, evaluated by `substrate.evaluate` (same pattern the recognition Argmax uses). The adapter only READS the chosen cell. |
| BLIND GUESS | `GUESS_TERM = predict_many_settings_term` — `Argmax` over candidate word Concepts of the variadic `Times` of per-channel likelihoods. Evaluated natively. |
| LEARN (cookie -> bank) | `bank_exemplar` mints an `Exemplar` node + `has_exemplar` edge — the cookie's structural effect (admissibility feedback, NOT a gradient reward). |
| REPORT reflex | `speech_world_report_reflex` Rule: `where secs_since_report >= report_period_s -> set report_due=1, reset clock`. Fires on `tick()`. |
| SAVE reflex | `speech_world_save_reflex` Rule, same shape on the save clock. |
| 2 GOALS | `Goal` nodes `understand_voice` (maximise cookies across the 3 axes — drives the active curriculum via the deficit) and `report_progress` (the 60s reflex), `pursues`-linked from the `SpeechWorldRoot`. |

The COOKIE is FEEDBACK ("this structure is admissible" -> bank), not an RL reward.
The recognizer is the cognition+hat **in feature space** — it NEVER inverts the TTS
and NEVER uses the TTS / a neural net FOR recognition (no-donkey). The neural-ish
WORLD (espeak) only TEACHES; the agent grounds.

**One honest seam (flagged loudly):** the curriculum PICK and the GUESS are graph
**Terms** the adapter evaluates and reads the value of, rather than Rules whose
*effects* mutate the graph. This is the established project pattern
(`heldout_many_settings`, `recognition_graph`) — the *decision* is the graph Term;
Python performs no sort/conditional. A pure-Rule form was attempted but the rule
effect verbs (`set_attr`/`add_edge`) cannot write a Term-chosen *node* as an edge
target, so the Term-value-read form is used. The substantive decision is in the
graph; no Python branch chooses.

A second small seam: between 60s reports the pick is steered by a recency-weighted
**online** cookie-rate (`live_rate`, updated each step) so the curriculum rotates in
real time; it is **re-seeded from the authoritative held-out rate at each report**.
The held-out rate (never banked) remains the ungameable progress measure.

**Persistence note:** `graph_to_dict` serialises nodes/edges/attrs (the learned
exemplar banks + cells + goals persist) but not productions/Rules; the runner
re-installs those idempotently after `load_state`. Verified: a resumed run's first
report shows the retained banks (e.g. 29 exemplars, 1.000 held-out) — it picks up
exactly where it left off.

## (2) End-to-end runs — the per-cell held-out learning curve

`PYTHONUNBUFFERED=1 python -m scripts.self_directed_speech_loop [--stage2] [--seconds N] [--report-every S]`

**STAGE 1** (granularity={digit,word}, language={en}, source={espeak, noise, fsdd}),
40s, reports every 13s — held-out cookie-rate (never banked), first -> last report:

```
digit|espeak|en   0.100 -> 1.000  [CLIMB]
digit|fsdd|en     0.000 -> 0.400  [CLIMB]    <- real human speech (hardest)
digit|noise|en    0.000 -> 1.000  [CLIMB]
word|espeak|en    0.000 -> 0.875  [CLIMB]
word|noise|en     0.000 -> 1.000  [CLIMB]
MEAN              0.020 -> 0.855  (5/5 cells climbed)  => YES, held-out climbs
```

The active curriculum self-directed to its WORST cell: `digit|fsdd|en` drew **469
live attempts** vs ~12-23 for the saturating synthetic cells — the agent concentrates
effort on what it understands least, exactly the "understand_voice" goal in action.

**STAGE 2** (+ languages fr/de/es, + TVTropes real-text WORD source), 60s — **18
cells across 4 languages, all 18 climb**, mean **0.006 -> 0.856**:

```
digit|espeak|{de,en,es,fr}   -> 1.000 / 1.000 / 0.700 / 1.000
digit|fsdd|en                -> 0.300            <- again the hardest; 261 attempts
digit|noise|{de,en,es,fr}    -> 0.900 each
word|espeak|{de,en,es,fr}    -> 0.875 / 1.000 / 1.000 / 0.750
word|noise|{de,en,es,fr}     -> 1.000 / 0.875 / 0.875 / 0.875
word|tvtropes|en             -> 0.550            <- real corpus text
POLYGLOT: cells span languages ['de', 'en', 'es', 'fr']
```

## (3) VERDICT

**Does the agent LEARN self-directed (held-out cookie-rate climbs) with the
architecture clean? YES.** Every cell's held-out (ungameable) cookie-rate climbs from
~chance to high; the curriculum self-directs to the cell it is worst at (real human
FSDD digits), driven by the `understand_voice` goal's deficit through the graph
`PICK_TERM`. The recognizer is the cognition+hat in feature space (never TTS
inversion, never a net for recognition); the cookie is admissibility feedback, not a
gradient reward; the decisions are graph Terms/Rules, not Python branches.

**Does multilingual self-direction begin the POLYGLOT? YES.** Stage 2 spans en/fr/de/es
with per-(language) lexicons that all climb under one self-directing mind. The
cross-language structure is real at the curriculum level: the agent allocates its own
effort across languages by the same deficit signal. (The deeper polyglot claim — a
*shared, language-general representation* — is NOT yet demonstrated: each cell keeps
its own exemplar bank, so what is shown is multilingual self-direction over separate
lexicons, the first rung. The language-general representation is the next step.)

### Honest qualifiers

- **The synthetic (espeak) cells saturate to ~1.0 trivially** because espeak is
  deterministic: the same text -> near-identical audio, so a banked exemplar nearly
  matches its held-out probe. The genuinely informative cell is **`digit|fsdd|en`**
  (real human speakers): it plateaus ~0.30-0.40, consistent with the project's known
  FSDD speaker-invariance wall (~0.44). The climb there is real but bounded by the
  front-end, not by this world. The synthetic cells prove the LOOP; the FSDD cell is
  the honest difficulty probe — and the curriculum correctly pours effort into it.
- **The held-out probes for TTS cells are drawn from the same synthesiser**, so
  "held-out" there means held-out *instances*, not held-out speakers. For FSDD the
  probes are disjoint real recordings (a stronger held-out). This is stated, not hidden.
- **No download was needed** beyond what was present: espeak-ng (installed), ffmpeg
  (installed), FSDD (`/tmp/fsdd/recordings`, 3000 wavs), TVTropes index
  (`~/.cache/ozma/tvtropes_index.json`). **Piper neural TTS was NOT installed**
  (not present; not pip-installable offline here) — espeak-ng is the working fallback
  and is sufficient as the WORLD (in-thesis: the TTS teaches, the agent grounds).
  LibriSpeech sentence/paragraph granularities were left for a later widening; the
  3-axis STRUCTURE supports them (granularity is a free axis) but Stage 1/2 ran on
  digit/word to keep the loop fast and the climb legible.
- **NO-DONKEY throughout:** the recognizer is the agent's owned Argmax-of-product over
  exemplars in feature space; the TTS is never inverted and never consulted for the
  guess.

### Required suites

`tests/test_stt_pipeline.py`, `tests/test_perception_self_assessment.py`,
`tests/test_process_meta_assessor.py`, `tests/test_gap_guidance.py` — **32 passed**.
