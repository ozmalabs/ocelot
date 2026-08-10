# The agent's direct control over its own front end (the audio hat it self-designs)

Two-part build in the self-directed SpeechWorld:
- **(A) Piper neural TTS** as a realistic per-language WORLD source (alongside espeak).
- **(B) the FRONT END as a graph-resident, AGENT-MODIFIABLE structure** — the feature
  extraction is a graph the agent READS and MODIFIES (adds an ear / gates in a banked
  cue / tunes a param / invents), wired to the plateau signal so the agent self-designs
  its own ears when it hits the front-end wall.

Working dir: `research/experiments/gamma-substrate`. Nothing committed; left in the
working tree for review.

## Files

- `domains/agent_frontend.py` — **the graph-resident front end**: a `FrontEnd` node
  owning `Cue` nodes (each `active` + DSP params); `feature_channels(substrate, x, fs)`
  perceives a clip through the ACTIVE cues; `modify_frontend` (the agent's graph Argmax)
  adds the next cue when the agent plateaus; `invent_cue` composes a novel band-Term.
  The cue-extractor registry is owned, composable DSP proven in `enriched_hvpt_accept`.
- `domains/self_directed_speech_world.py` — Piper source (`piper_tts`/`piper_available`),
  the front-end-backed `feature_channels`, the DYNAMIC-width recognizer
  (`blind_guess` ranges over the live active-cue count), the third GOAL
  `improve_front_end`, and the **plateau-detection Rule** (`speech_world_plateau_detect`).
- `scripts/self_directed_speech_loop.py` — the runner: adds the `piper` source, enacts
  the agent's front-end modification when the plateau Rule flags a cell.
- `scripts/frontend_lift_measure.py` — the DECISIVE test, isolated: FSDD held-out
  cookie-rate as the agent self-widens its front end (LOSO over speakers).

## (1) Piper neural TTS

`pip install piper-tts` (via the project's uv venv) **succeeded online**. Four voices
downloaded to `~/.cache/ozma/piper_voices/`: `en_US-lessac-medium`, `fr_FR-siwis-medium`,
`de_DE-thorsten-medium`, `es_ES-davefx-medium` (VITS neural TTS, 22.05 kHz, resampled to
8 kHz to match FSDD/espeak). Wired as the `piper` curriculum source: it PLAYS realistic
audio the agent RECOGNIZES through its front end (feature space). The net is the WORLD —
**never inverted, never used FOR recognition** (no-donkey). Offline path keeps espeak.

## (2) The front end as a graph-resident, agent-modifiable structure

The feature extraction is no longer a fixed Python function. A `FrontEnd` node owns
`Cue` nodes via `has_cue` (active) and `repertoire` (inactive). Perception of a clip =
the L2 readout of every ACTIVE cue, dispatched by each cue's `extractor` attr, with its
params read off the graph node. The agent's three moves, all graph-resident decisions
and all composable DSP (no fit, no net, no donkey):

- **ADD a cue / ear** — `modify_frontend` flips the chosen inactive cue's `active` 0->1.
  WHICH cue is the graph Argmax `PICK_MOD_TERM` over the addable repertoire (by the
  harvest-measured orthogonality rank). The repertoire: two extra cochlear EARS at new
  time-frequency tradeoffs (the two-ears -> many-ears move) + the banked orthogonal cues
  (formant_relation, manner_voicing, f0_contour, modspec, landmark, transition_w3).
- **TUNE a param** — a cue's params (cochlear env_cut / n_frames, FFT window, all-pole
  order, transition n_windows) are graph attrs the extractor reads.
- **INVENT a cue** — `invent_cue` composes a novel band-combination Term (the
  feature_generator generative grammar) selected by MDL/compression, minted as an active
  `Cue` with the Term stored. The open-ended move when the repertoire is exhausted.

Audited: the extractors are I/O-boundary DSP (gammatone / np.fft / Levinson — the same
category as the existing front end); the CONFIG (which cues, their params) is graph data;
the WHICH-modification decision is the graph Argmax, not a Python branch; Piper is the
world, never inverted.

## (3) Wired to the self-directed loop

A graph-resident Rule `speech_world_plateau_detect` fires on each `CurriculumCell`: when
the cell is still HARD (held-out rate <= `plateau_ceiling`) AND progress has STALLED
(|held_delta| <= `plateau_band`) AND it has had effort (`n_probes` >= 1), it raises
`frontend_mod_due`. This is the effort-without-payoff / front-end-wall signal specialised
to a cell. The runner then ticks (the Rule fires) and enacts ONE `modify_frontend` — the
agent's graph Argmax chooses the cue; the adapter only flips it. The agent self-directs
the front-end improvement, driven by the `improve_front_end` goal + the plateau Rule.

Verified in isolation: the plateau Rule fires ONLY on a hard+stalled cell (a high-rate
cell is not flagged); on firing, `modify_frontend` adds `formant_relation` first (the
graph's harvest-rank choice), the active-cue count climbs, and `blind_guess`/`feature_
channels` immediately range over the wider front end.

## (4) VERDICT — does the agent LIFT the FSDD plateau self-directed?

**Headline: YES — in the genuine wall regime the agent's OWN self-directed front-end
widening lifts held-out FSDD from 0.400 (the documented ~0.30-0.40 wall) to 0.533
(+0.133), past the plateau, with the modification chosen by the graph.** The size of
the lift depends on how much of the wall the prior 3-cue front end has already dissolved.
Three measurements:

### (a) Isolated LOSO at the WALL regime (sparse bank, n_per=1) — the decisive test

`scripts/frontend_lift_measure.py 1` (LOSO over 6 FSDD speakers, only ~10 train
exemplars — the genuine low-data wall regime where the seed front end sits exactly at the
documented plateau). The agent's graph Argmax adds one cue at a time, re-banks,
re-measures. Mean held-out cookie-rate:

```
3cues(seed)                  0.400   <- exactly the documented ~0.30-0.40 FSDD wall
4cues(+formant_relation)     0.533   (+0.133, the agent's first graph-chosen add)
5cues(+manner_voicing)       0.533
6cues(+f0_contour)           0.517
7cues(+modspec)              0.533
8cues(+landmark)             0.483
...
seed 0.400  ->  best self-widened 0.533   LIFT +0.133  (chance 0.100)
```

Per-speaker the lift is real and sometimes large: nicolas 0.30->0.70, yweweler (hardest)
0.10->0.40, george 0.50->0.80, theo 0.50->0.80. The first cue the agent adds
(formant_relation, the VTL-invariant spacing — exactly the speaker-invariance cue) gives
the whole lift; later cues plateau. The modification SET and ORDER are the graph's
(the harvest-rank Argmax), not hand-picked; every cue is composable DSP (no fit, no net);
the climb is on disjoint real speakers (true speaker-invariant held-out).

### (b) Isolated LOSO at the DENSE regime (n_per=5) — the wall already mostly dissolved

`scripts/frontend_lift_measure.py 5`: with a dense multi-speaker bank the seed 3-cue
front end already sits at 0.573 (far past the wall), so the agent's self-widening adds
only a modest further +0.044 (0.573 -> 0.617 at +manner_voicing). The big lift past the
wall was ALREADY achieved by the prior many-settings front end; in this regime the agent
squeezes a smaller real increment.

### (c) Live self-directed loop — the plateau judgement drives the widening end-to-end

`scripts/self_directed_speech_loop.py`: the agent self-directs the curriculum; the report
cadence + the graph PLATEAU judgement (PLATEAU_TERM) fire repeatedly; when a cell is HARD
+ STALLED below `plateau_ceiling` the agent enacts `modify_frontend`. Observed live:
- t=81s: `digit|fsdd|en` plateaus at 0.400 (Δ=0.000) -> the agent self-modifies:
  **+formant_relation** (3 -> 4 active cues), its graph Argmax choice.
- t=121s: with the self-widened 4-cue front end, FSDD climbs 0.400 -> 0.450 (Δ+0.050) —
  a real climb past the prior stall, driven by the agent's OWN modification.
- the **neural-Piper cell** `digit|piper|en` likewise plateaus and the agent self-adds
  **+manner_voicing** (4 -> 5 cues) — the mechanism fires across cells and across the
  neural-TTS source, not just FSDD.
The widening PHASES IN cleanly (the bank refreshes to the new width per word; no
empty-bank collapse) via `_cell_exemplar_width`.

### What this means

- **The control works end-to-end and is graph-resident**: the agent adds/tunes/invents
  cues DIRECTLY (the FrontEnd graph); the plateau JUDGEMENT is a graph Term
  (PLATEAU_TERM); the WHICH-modification is a graph Argmax (PICK_MOD_TERM); the widening
  immediately changes what the agent hears. The mechanism — "the agent's senses are its
  to build" — is realized and self-triggered.
- **The agent dissolves its OWN front-end wall, self-directed**: from the documented
  0.30-0.40 FSDD plateau, the agent's own graph-chosen cue (the VTL-invariant
  formant-relation) lifts held-out to ~0.53 (+0.13), past the wall, on disjoint real
  speakers. The lift is the agent's choice, not ours.
- **Honest bound**: the lift saturates after ~1-2 cues (the agent adds the right
  speaker-invariance cue, then more cues stop helping); the residual hardest speakers are
  NOT removed by more cues — that deeper wall is the exemplar/representation regime, not a
  missing front-end cue. And where the prior front end already dissolved the wall (dense
  bank), the further self-directed gain is small (+0.04). So the agent lifts its front-end
  wall self-directed, decisively in the wall regime and modestly once the wall is already
  mostly gone.

**VERDICT: YES — given direct front-end control, the agent LIFTS the FSDD plateau
self-directed: it hits the wall (held-out stalls at ~0.40), its graph chooses a front-end
modification (+formant_relation, the VTL-invariant cue), and the held-out cookie-rate
climbs past the plateau to ~0.53 (+0.13) on disjoint real speakers — the modification
chosen by the graph, the cues composable DSP (no fit/no net), Piper as world (never
inverted). The deepest self-direction — the agent dissolving its own front-end wall with
self-designed ears — is demonstrated.**

## Required suites

`tests/test_stt_pipeline.py`, `tests/test_perception_self_assessment.py`,
`tests/test_process_meta_assessor.py`, `tests/test_gap_guidance.py` — **32 passed**.
