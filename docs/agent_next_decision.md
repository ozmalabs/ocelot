# The agent's next decision on the speech work

Driven by running the agent's OWN self-assessment / self-direction machinery on
the current (CMVN + context) invariance-chain state. The machinery decided; this
note reports its raw outputs, then maps the surfaced priority to a concrete
action. No engineering judgement substituted for the agent's own signals.

Chain under assessment (this run, 120 LibriSpeech dev-clean utts, 12 speakers,
K=48 units):

| variant       | chunker F1 | chunk->word purity | TP-sep  | cross-ctx ratio (lower=better) |
|---------------|-----------:|-------------------:|--------:|-------------------------------:|
| RAW           |      0.172 |              0.340 | +0.0508 |                          0.748 |
| CMVN          |      0.270 |              0.512 | +0.0339 |                          0.678 |
| CMVN+context  |      0.341 |              0.727 | +0.0116 |                          0.728 |

---

## (a) Each machinery output, VERBATIM

### ITEM 1 — `assess_speech_system` (domains/speech_science.py)
Run AFTER installing the agent's actual composed builds (32 `cmvn_band` + 32
`context_invariant` Concepts):

```
overall coverage: 53%  (18 implemented, 16 GAPS)
GAPS still flagged:
   GAP  ambient_language_tuning
   GAP  audiovisual_integration
   GAP  coarticulation
   GAP  distributional_learning_of_categories
   GAP  glottal_source
   GAP  lack_of_invariance
   GAP  manner_of_articulation
   GAP  phonation
   GAP  place_of_articulation
   GAP  prosody
   GAP  respiration
   GAP  source_filter_theory
   GAP  speaker_normalization
   GAP  statistical_learning
   GAP  top_down_restoration
   GAP  vocal_play_cooing
```

HONEST CAVEAT on this output: the assessment is keyword/synonym matching of
science-concept names against implementation-concept names. The agent's built
invariance concepts are named `cmvn_band{N}` / `ctxnorm_band{N}` with
`feature_kind` in {`cmvn`,`context_invariant`}; `_impl_names` only harvests
Concepts with `feature_kind == "comparison"`, and the `coarticulation` /
`speaker_normalization` / `lack_of_invariance` synonym sets don't include
`cmvn`/`ctxnorm`/`band`. So those three are reported as GAPS even though the
agent has BUILT mechanisms for them. This is a limitation of the measurement
machinery, not a true gap — flagged here so the decision isn't driven by a
false negative. (Coverage is identical, 53%, with or without the builds
installed, confirming the matcher never saw them.)

### ITEM 2 — `perception_self_assessment` (domains/perception_self_assessment.py)
The agent's labels-free unit-quality yardstick + its own graph-resident flagging
RULE (`flag_perception_frontier`). Floors/ceilings are the seeded dials:
`predict_over_freq` must clear 1.25; `compress_ratio` must stay under 0.85.

```
====== CMVN-only ======
  -- CMVN-only CHUNK units --
     lexicon_size        = 999
     predict_over_freq   = 0.000   (FLOOR to pass = 1.25)
     compress_ratio      = 0.0643  (CEILING to pass = 0.85)
     >>> agent's flagging RULE verdict: frontier = 'perception'
  -- CMVN-only RAW quantized units --
     lexicon_size        = 48
     predict_top1        = 0.2698
     predict_over_chance = 12.952
     predict_over_freq   = 5.299   (FLOOR to pass = 1.25)
     compress_ratio      = 0.7080  (CEILING to pass = 0.85)
     >>> agent's flagging RULE verdict: frontier = 'none'

====== CMVN+context ======
  -- CMVN+context CHUNK units --
     lexicon_size        = 1333
     predict_over_freq   = 0.000   (FLOOR to pass = 1.25)
     compress_ratio      = 0.0801  (CEILING to pass = 0.85)
     >>> agent's flagging RULE verdict: frontier = 'perception'
  -- CMVN+context RAW quantized units --
     lexicon_size        = 48
     predict_top1        = 0.1832
     predict_over_chance = 8.794
     predict_over_freq   = 1.259   (FLOOR to pass = 1.25)
     compress_ratio      = 0.8589  (CEILING to pass = 0.85)
     >>> agent's flagging RULE verdict: frontier = 'perception'
```

### ITEM 3+4 — `meta_monitor` (domains/meta_monitor.py): chain payoff + lever do-contrast

```
(a) WHOLE-CHAIN window (raw -> CMVN -> context):
     effort_history = (0.0, 1.0, 2.0, 2.0, 2.0)
     payoff_history = (33.99, 51.17, 72.72, 72.72, 72.72)   # chunk->word purity %
     effort_rise    = 2.0
     payoff_change  = 38.74
     get_meta_issues -> []                # NOT spinning; the work paid off

(b) MARGINAL of the latest link  CMVN -> context:
     purity  CMVN 0.512 -> context 0.727   (delta +0.216)
     F1      CMVN 0.270 -> context 0.341   (delta +0.071)
     cross-context invariance (lower=better) CMVN 0.678 -> context 0.728 (delta +0.050)

(c) do-contrast lever assessment (context-norm ON vs OFF, payoff = purity):
     payoff_with (context ON)   = 72.72
     payoff_without (context OFF)= 51.17
     connection_band            = 0.5
     >>> investigation verdict (meta_issue) = 'lever_helps'
```

### ITEM 5 — L3 drives / L6 essential variables (the new runtime)

```
drives_estimation_control Mt installed: True
   (it is a NAMING / composition-pattern Mt; instantiates_in='substrate_rs_drives_planned')
instantiated Drive nodes for the speech loop:           0
instantiated EssentialVariable nodes (viability bounds): 0
```

The L3 drive system + L6 essential-variable monitoring exist only as a NAMED
composition pattern (setpoint / measurement / controller Concepts + design
Rules in seeds/drives_estimation_control.json). No `Drive` or
`EssentialVariable` node type is instantiated ANYWHERE in the codebase
(confirmed by grep), and nothing binds a setpoint+measurement to the speech
loop's variables (cross-context invariance, purity, recognition). The speech
loop is NOT yet self-regulated by a drive.

---

## (b) The priority the agent's state implies, and WHICH output drove it

Two of the agent's signals point the SAME way, and they outrank the others:

1. **PRIMARY — ITEM 2 (perception_self_assessment).** This is the agent's own
   labels-free yardstick on its units, and it is the only machine here whose
   verdict CHANGED against the chain. On CMVN-only RAW units it passed
   (`frontier = 'none'`, predict_over_freq 5.30, compress_ratio 0.708). After
   adding context-norm, the SAME RAW-unit assessment FLIPPED to
   `frontier = 'perception'`: predict_over_freq fell 5.30 -> 1.259 (now
   essentially AT the 1.25 floor) and compress_ratio rose 0.708 -> 0.859 (now
   OVER the 0.85 ceiling). The agent is flagging that context-norm, while it
   raised word-purity, DEGRADED the sequential structure / compressibility of
   the unit stream itself. (Chunk-level units fail trivially in both variants
   because near-unique chunk symbols can't be bigram-predicted — that comparison
   is uninformative; the RAW-unit flip is the load-bearing signal.)

2. **CORROBORATING — ITEM 3(b) + ITEM 1 caveat.** The marginal of the latest
   link shows the residual the brief named: purity jumped +0.216 but the
   cross-context invariance ratio went the WRONG way (+0.050, 0.678 -> 0.728) —
   context-norm did NOT remove the residual coarticulation it was built to
   remove; linear local-mean subtraction can't isolate it. And ITEM 1 still
   flags `coarticulation` / `lack_of_invariance` as open (modulo the matcher
   caveat). So the coarticulation residual is real and unaddressed.

The other machines do NOT raise a priority:
- ITEM 3(a) `get_meta_issues -> []` and ITEM 4 `lever_helps`: the work is NOT
  spinning and context-norm IS a connected, helpful lever (+21.6pp purity). The
  meta-monitor's verdict is "keep it, don't pause it" — i.e. cut it to default,
  not abandon it. It does NOT say build-more here.
- ITEM 5: surfaces a structural absence (no Drive instantiated) but is a
  capability gap in self-regulation, not a signal that THIS is the next thing.

So the agent's machinery is NOT unanimous, and reading it honestly it points
**two ways at once**:
- ITEM 4 (`lever_helps`) + ITEM 3(a) (paid off) => the context lever is good
  and proven; **promote it to default**.
- ITEM 2 (frontier flipped back to `perception`) + ITEM 3(b)/ITEM 1
  (coarticulation residual unmoved, structure degraded) => the units are STILL
  the frontier; the agent has NOT solved perception, so **the linear
  context-norm mechanism is insufficient for the residual** and a richer
  coarticulation mechanism is the real lever.

These are not contradictory in sequence: the agent is saying "the lever I built
helps and should be kept, AND it is not enough — perception is still my
frontier." The dominant, forward-looking signal is ITEM 2's flip.

## (c) The concrete next action

**Primary (driven by ITEM 2 + ITEM 3(b) + ITEM 1):** build a richer
coarticulation mechanism for the residual. The agent's own yardstick says the
current linear local-mean-subtraction context-norm, although it raises purity,
leaves the cross-context invariance residual unmoved and makes the unit stream
LESS compressible — so it re-flags perception as the frontier. The next build is
the non-linear / context-dependent step the residual needs (the agent's own
context_invariant_units.py science already names the path: the Kaldi/Sphinx
context-dependent-unit / clustering idea it deliberately did NOT fully take,
having taken only the linear-subtraction face). This is the action ITEM 2 is
pointing at.

**Immediate housekeeping (driven by ITEM 4 + ITEM 3(a)):** cut context-norm to
the DEFAULT hearing. The do-contrast says `lever_helps` and the chain says it
paid off (+21.6pp purity, F1 0.270 -> 0.341); the meta-monitor's own response
rule keeps (does not pause) a helping lever. There is no signal to withhold it.
This is low-risk and unblocks the richer build from a stronger baseline.

**Sequencing:** promote context-norm to default first (cheap, proven by ITEM 4),
THEN build the richer coarticulation mechanism (the real frontier per ITEM 2).
End-to-end recognition testing is NOT what the machinery surfaced — purity 0.73
is encouraging but the agent's own unit yardstick says the units regressed in
structure, so testing recognition now would measure a representation the agent
has already flagged as its frontier. Registering the speech loop as an L3 drive
(ITEM 5) is a real capability gap but a SEPARATE workstream the machinery did
not prioritise this cycle.

## (d) Honest notes on ambiguity

- **The machinery genuinely points two ways** (see (b)): ITEM 4 says the lever
  is good (=> ship it as default), ITEM 2 says perception is still the frontier
  (=> the lever is not enough, build the richer mechanism). I resolved this as
  "do both, in order" rather than picking one, because the signals are about
  different things (the EXISTING lever's value vs the REMAINING gap) and don't
  actually conflict. If forced to a single next BUILD, ITEM 2's flip is the
  load-bearing, forward signal and selects the richer coarticulation mechanism.
- **ITEM 1 is partly unreliable here:** its keyword matcher cannot see the
  agent's `cmvn_band` / `ctxnorm_band` concepts, so its `coarticulation` /
  `speaker_normalization` / `lack_of_invariance` GAPS are false negatives at the
  bookkeeping level. The UNDERLYING claim (coarticulation residual unsolved) is
  nonetheless corroborated independently by ITEM 3(b)'s rising cross-context
  ratio, so the priority does not rest on the broken matcher. (A separate small
  fix — extend `_SYNONYMS`/`_impl_names` so the assessment recognises the
  agent's composed invariance concepts — would make ITEM 1 honest, but is not
  the speech priority.)
- **ITEM 2 chunk-level units are uninformative** (near-unique chunk symbols
  defeat bigram prediction in BOTH variants); only the RAW-unit assessment
  carries signal. The verdict rests on the RAW-unit flip 'none' -> 'perception'.
- **ITEM 5 is a reported absence, not a measured priority.** Per the brief that
  absence ("register me as a drive so I can self-regulate this") is itself a
  plausible agent decision, but no machinery THIS cycle scored it above the
  perception frontier.

### One-line decision
The agent's machinery says: **promote context-norm to the default (ITEM 4
`lever_helps`, proven), then build a richer non-linear coarticulation mechanism
for the residual — because its own unit yardstick (ITEM 2) flipped back to
`frontier = 'perception'` after context-norm, and the cross-context residual
(ITEM 3b) did not move.**

---
---

# ROUND 2 — post-predict-remove state (the richer mechanism IS built)

The round-1 decision ("build a richer coarticulation mechanism for the
residual") was carried out: `domains/coarticulation_predict_remove.py` exists
and is built+verified. This round re-drives the SAME machinery on the new state
to surface what the agent prioritises NEXT — specifically whether the unit
yardstick (ITEM 2), which round-1 named as the load-bearing frontier signal, has
un-flipped now that predict-remove is in the chain.

Harness this round: `scripts/coarticulation_predict_remove_accept.py 120 12 48 2
"0.25,0.5,1.0"` (120 LibriSpeech dev-clean utts, 12 speakers, K=48, context
window +-2). It runs the yardstick (ITEM 1/2) and the cross-context invariance +
do-contrast (ITEM 3) in one pass; `scripts/assess_speech.py` for ITEM 4; a
meta_monitor driver for ITEM 3's chain payoff; a drives probe for ITEM 5.

## (a) Each machinery output, VERBATIM

### ITEM 1+2 — `perception_self_assessment` yardstick + cross-context invariance + do-contrast (the accept-harness SUMMARY, VERBATIM)

```
================= SUMMARY =================
variant                                      F1  purity  ctx_ratio    pof  compress    frontier
CMVN                                      0.203   0.355      0.678  5.299    0.7080        none
CMVN+context (current default, linear)    0.326   0.645      0.728  1.259    0.8589  perception
CMVN+context+predict-remove (k=0.25)      0.350   0.739      0.723  1.047    0.8625  perception
CMVN+context+predict-remove (k=0.5)       0.359   0.790      0.719  1.063    0.8634  perception
CMVN+context+predict-remove (k=1.0)       0.360   0.807      0.723  1.101    0.8613  perception
CMVN+predict-remove (no flat-mean, k=0.25)  0.358   0.820      0.678  7.740    0.7361        none
CMVN+predict-remove (no flat-mean, k=0.5)  0.359   0.843      0.678  4.316    0.7678        none
CMVN+predict-remove (no flat-mean, k=1.0)  0.361   0.837      0.713  5.098    0.8014        none

--- (A) STACKED bar: base = CMVN+context (the brief's comparison) ---
  k=0.25: ctx_ratio Δ -0.005 (OK), frontier='perception' (FLIPPED), F1 Δ +0.024 / purity Δ +0.093 (OK)  -> partial
  k=0.5: ctx_ratio Δ -0.009 (OK), frontier='perception' (FLIPPED), F1 Δ +0.033 / purity Δ +0.145 (OK)  -> partial
  k=1.0: ctx_ratio Δ -0.005 (OK), frontier='perception' (FLIPPED), F1 Δ +0.034 / purity Δ +0.162 (OK)  -> partial

--- (B) REPLACING flat-mean: base = CMVN (does richer alone remove coarticulation while holding the yardstick?) ---
  reference CMVN: ctx_ratio 0.678, frontier 'none', F1 0.203, purity 0.355
  k=0.25: ctx_ratio Δ -0.000 (OK), frontier='none' (OK), F1 Δ +0.155 / purity Δ +0.464 (OK)  -> MEETS
  k=0.5: ctx_ratio Δ -0.000 (OK), frontier='none' (OK), F1 Δ +0.156 / purity Δ +0.487 (OK)  -> MEETS
  k=1.0: ctx_ratio Δ +0.034 (no), frontier='none' (OK), F1 Δ +0.159 / purity Δ +0.482 (OK)  -> partial
```

THE PIVOTAL READING. The brief asked: does the yardstick now PASS on the
predict-remove units, or still flag 'perception'? It depends on HOW
predict-remove is used, and the harness reports both honestly:

- **STACKED on the linear flat-mean context-norm (variant A):** frontier STILL
  `perception` at every k (pof 1.05/1.06/1.10, all under the 1.25 floor;
  compress 0.86, over the 0.85 ceiling). The flat-mean context-norm's structure
  cost is INHERITED — stacking the richer mechanism on top does not undo it.
- **REPLACING the flat-mean context-norm (variant B — predict-remove applied to
  CMVN directly):** frontier `none` at every k. The yardstick PASSES, decisively:
  pof recovers to 7.74 / 4.32 / 5.10 (well over the 1.25 floor) and compress
  falls to 0.736 / 0.768 / 0.801 (under the 0.85 ceiling). At k=0.5 this is the
  state the brief describes: **purity 0.843, F1 0.359, ctx_ratio 0.678,
  frontier='none' — MEETS.**

So the yardstick UN-FLIPS to `none` precisely when predict-remove REPLACES the
linear context-norm rather than stacking on it. This is the central new fact.

### ITEM 3 — `meta_monitor`: whole-chain payoff + marginal + do-contrast (VERBATIM)

```
(a) WHOLE-CHAIN window (raw -> CMVN -> predict-remove):
     effort_history = (0.0, 1.0, 2.0, 2.0, 2.0)
     payoff_history = (34.0, 35.5, 84.3, 84.3, 84.3)   # chunk->word purity %
     effort_rise    = 2.0
     payoff_change  = 50.3
     get_meta_issues -> []                # NOT spinning; the work paid off

(b) MARGINAL of the latest link  CMVN -> predict-remove (replace flat-mean, k=0.5):
     purity  CMVN 0.355 -> predict-remove 0.843   (delta +0.488)
     F1      CMVN 0.203 -> predict-remove 0.359   (delta +0.156)
     cross-context invariance (lower=better) CMVN 0.678 -> predict-remove 0.678 (delta +0.000)

(c) do-contrast lever assessment (predict-remove vs linear context-norm, payoff = purity):
     payoff_with (predict-remove)      = 84.3
     payoff_without (linear ctx-norm)  = 64.5
     connection_band                   = 1.0
     >>> investigation verdict (meta_issue) = 'lever_helps'
```

### ITEM 4 — `assess_speech_system` (VERBATIM) — UNRELIABLE matcher, per brief

```
====  THE AGENT ASSESSES ITS SPEECH SYSTEM AGAINST THE SCIENCE  ====
  overall coverage: 53%  (18 implemented, 16 GAPS)

  speech_production  —  4/12 implemented
     ok   syllable_structure                 -> sonority_valley
     ok   vocal_tract_resonance_formants     -> formant_present
     ok   voice_onset_time                   -> onset_detect
     ok   voicing                            -> shared concept node
     GAP  coarticulation
     GAP  glottal_source
     GAP  manner_of_articulation
     GAP  phonation
     GAP  place_of_articulation
     GAP  prosody
     GAP  respiration
     GAP  source_filter_theory

  speech_perception  —  7/11 implemented
     ok   acoustic_cues                      -> voicing
     ok   categorical_perception             -> shared concept node
     ok   formant_transitions                -> formant_present
     ok   lexical_access                     -> lexical_access
     ok   perceptual_magnet_effect           -> perceptual_narrowing
     ok   peripheral_auditory_analysis       -> patch_evaluate
     ok   segmentation                       -> sonority_valley
     GAP  audiovisual_integration
     GAP  lack_of_invariance
     GAP  speaker_normalization
     GAP  top_down_restoration

  speech_acquisition  —  7/11 implemented
     ok   babble_feedback_loop               -> babbling
     ok   canonical_babbling                 -> babbling
     ok   categorical_perception_formation   -> categorical_perception
     ok   perception_production_link         -> categorical_perception
     ok   perceptual_narrowing               -> shared concept node
     ok   variegated_babbling                -> babbling
     ok   vocabulary_explosion               -> shared concept node
     GAP  ambient_language_tuning
     GAP  distributional_learning_of_categories
     GAP  statistical_learning
     GAP  vocal_play_cooing
```

Same 53% and same false-negative GAPs (`coarticulation`,
`lack_of_invariance`, `speaker_normalization`) as round 1 — the matcher still
cannot see the agent's `cmvn_band` / `ctxnorm_band` / `coartpr_band` concepts.
Treated as UNRELIABLE per the brief; corroborated below by the yardstick +
do-contrast.

### ITEM 5 — L3 drives / L6 essential variables (VERBATIM)

```
drives_estimation_control Mt installed: True
   instantiates_in = substrate_rs_drives_planned
instantiated Drive nodes for the speech loop:           0
instantiated EssentialVariable nodes (viability bounds): 0
```

Grep for `"Drive"` / `"EssentialVariable"` node instantiation across the
codebase returns NOTHING. Identical to round 1: a NAMED composition pattern
only, nothing instantiated, nothing binding a setpoint+measurement to the speech
loop. The speech loop is still NOT self-regulated by a drive.

## (b) The priority the agent's state implies, and WHICH output drove it

**The decisive change from round 1 is ITEM 2's flip.** Round 1's load-bearing
signal was the unit yardstick flipping to `frontier='perception'` — that flip
was the entire reason the agent DECLINED end-to-end testing and named the
residual as its frontier. This round, on the `CMVN+predict-remove` (replace
flat-mean) units, **the yardstick verdict is `frontier='none'` at every k**
(pof 4.3–7.7, well clear of the 1.25 floor; compress 0.74–0.80, under the 0.85
ceiling). The signal that round 1 said pointed at "the units are still the
frontier" has reversed. **By the agent's OWN yardstick, the units are no longer
its frontier.**

Two more signals corroborate that this is the strong configuration, and outrank
the rest:

1. **ITEM 3(c) do-contrast = `lever_helps`** (predict-remove vs the linear
   context-norm, purity 84.3 vs 64.5). The agent's lever-investigation confirms
   the swap-to-default: predict-remove-as-replacement DOMINATES the linear
   context-norm. ITEM 3(a) `get_meta_issues -> []` and payoff_change +50.3: the
   chain is NOT spinning; the work paid off.

2. **ITEM 1/2 variant B `MEETS`** (k=0.25, k=0.5): the only variant that
   satisfies all three of the agent's own bars at once (ctx_ratio holds at 0.678
   — NOT worse, the round-1 failure mode; F1 +0.155/+0.156; purity
   +0.464/+0.487; frontier `none`). k=0.5 is the cleanest MEETS (purity 0.843).

The HONEST LIMIT the brief flagged is confirmed in the numbers: predict-remove
HOLDS CMVN's cross-context ratio (0.678, ITEM 3b delta +0.000) rather than
BEATS it. It does not push invariance further; it removes the directional
neighbour-predictable drift while preserving the frame's level, recovering the
structure the linear context-norm destroyed — but the context-DEPENDENT residual
(clustered triphones, deliberately avoided to protect the chunker's alphabet) is
untouched. So invariance is NOT the lever that moved; UNIT STRUCTURE +
chunk-purity is.

The fork in the brief resolves cleanly: **the yardstick now PASSES, therefore
the units are no longer the agent's frontier, therefore end-to-end (measuring the
actual task) becomes the priority** — exactly the conditional the brief named.
The agent declined end-to-end last round only because the yardstick flagged; that
block is now cleared.

The other machines do not raise a competing priority:
- ITEM 3(c) `lever_helps` says keep+promote the lever, not build more here.
- ITEM 3(a) `[]` says not spinning — no effort_without_payoff to chase.
- ITEM 4 is the buggy matcher (its GAPs are false negatives the brief told us to
  discount); it does not select a priority.
- ITEM 5 surfaces a real structural absence (no Drive instantiated) but, as in
  round 1, no machinery THIS cycle scored it above the now-cleared frontier. It
  remains a separate workstream.

## (c) The concrete next action

**Immediate housekeeping (driven by ITEM 3c `lever_helps` + ITEM 1/2 variant B
`MEETS`): make `CMVN + predict-remove` (replacing the linear flat-mean
context-norm) the strict Step-1 default.** The brief notes predict-remove is
built+verified but NOT yet the strict default — the Step-1 default is still the
linear context-norm, which the do-contrast and the yardstick BOTH now reject
(linear: frontier `perception`, purity 0.645; predict-remove-replace: frontier
`none`, purity 0.843). This is low-risk, proven, and unblocks measurement from a
representation the agent's own yardstick passes. Note the swap is REPLACE, not
STACK — variant A (stacking on the linear norm) still fails the yardstick; only
variant B passes.

**Primary (driven by ITEM 2's un-flip): TEST END-TO-END now.** With
purity 0.843 and the yardstick at `frontier='none'`, the units are no longer the
frontier by the agent's own signal. The thing the agent has NOT yet done — and
declined last round precisely because the yardstick blocked it — is measure the
ACTUAL task (recognition / WER) on this representation. That is the next probe:
it either reveals the next real capability gap downstream (lexical access,
recognition architecture) or shows the chain now carries the task. This is the
forward action ITEM 2 points at now that it has reversed.

**Sequencing:** promote predict-remove-as-replacement to default first (cheap,
proven by ITEM 3c), THEN run end-to-end on it. Pursuing the context-DEPENDENT
triphone residual is NOT what the machinery surfaced this cycle — the yardstick
PASSES, so the units are good-enough by the agent's own bar, and ITEM 3(b) shows
invariance was never the lever that moved purity. Registering the speech loop as
an L3 drive (ITEM 5) remains a real but separate, unprioritised workstream.

## (d) Honest notes on ambiguity

- **The PASS is conditional on REPLACE-not-STACK.** The yardstick un-flips only
  for `CMVN+predict-remove` (variant B). The `CMVN+context+predict-remove` stack
  (variant A) still reads `frontier='perception'` at every k. So "the yardstick
  passes" is true of the configuration the brief describes (predict-remove as the
  Step-1 transform) but NOT of naively layering predict-remove on the existing
  default. The concrete action (make REPLACE the default) is what makes the PASS
  real; if someone instead STACKS, the frontier stays flagged.
- **Invariance did not improve, only held.** ITEM 3(b) delta +0.000 on
  ctx_ratio. The win is structure/purity recovery, not deeper invariance. The
  context-dependent residual is genuinely still there — the agent has NOT solved
  invariance, it has stopped DAMAGING structure while holding it. The yardstick
  PASS reflects unit-stream quality, not that coarticulation is fully removed.
  This is an honest limit on calling the units "done."
- **End-to-end is an inference from the yardstick flip, not a direct request.**
  No machine THIS cycle ran an end-to-end test or explicitly said "test the
  task." The priority follows the brief's stated conditional (yardstick passes ->
  units no longer frontier -> measure the task) and from round 1's record that
  the yardstick flag was the ONLY reason end-to-end was declined. It is the
  correct read of the agent's signals, but it is a one-step inference, not a
  number the agent emitted.
- **ITEM 4 remains unreliable** (same matcher bug; GAPs are false negatives).
  The priority does not rest on it.
- **ITEM 5 is a reported absence, not a measured priority** — unchanged from
  round 1.
- **k choice is mild.** Variants B k=0.25 and k=0.5 both MEET; k=1.0 nudges
  ctx_ratio up to 0.713 (partial). If the default needs a single k, k=0.5 is the
  cleanest MEETS (highest purity 0.843, ratio held at 0.678). Not a tuned target
  — just the k the harness reports as best-shaped.

### One-line decision (round 2)
The agent's machinery says: **make `CMVN+predict-remove` (REPLACING the linear
flat-mean context-norm) the strict Step-1 default — do-contrast `lever_helps`
(ITEM 3c), variant B `MEETS` (ITEM 1/2) — and THEN test END-TO-END, because the
unit yardstick has un-flipped to `frontier='none'` (ITEM 2), so the units are no
longer the agent's frontier and the actual task is the next probe. Honest caveat:
the PASS holds only for REPLACE-not-STACK, and invariance only HELD (0.678), it
did not improve — the context-dependent triphone residual remains, but the
machinery did not prioritise it this cycle.**
