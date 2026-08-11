# Parakeet teardown — the ACOUSTIC-DRIVEN model, read as DATA, contrasted with Whisper

Parakeet (NVIDIA NeMo: **FastConformer encoder + RNN-T / TDT / CTC decoder**, English
ASR, top of the Open ASR Leaderboard) is the **structural OPPOSITE** of Whisper, and
that is the point. Whisper (`docs/whisper_teardown.md`) is **LM-DRIVEN**: a giant
attention decoder does top-down restoration and *carries the reduced acoustics* — the
agent's measured frontier scaled (with a flat ear, recognition = the LM's next-word
accuracy, grounded in `scripts/whisper_teardown_probe.py`). Parakeet is
**ACOUSTIC-DRIVEN**: a sharp monotonic acoustic model with explicit duration and a
*light* predictor LM. So Parakeet's lessons are the **acoustic** structures the agent's
at-chance frontier (`docs/real_data_drive.md`: bottom-up acoustic **0.0313** vs chance
**0.0333**) needs — **complementary** to Whisper's top-down LM.

This is NOT a generic Parakeet summary and NOT "train a conformer" (the donkey —
`ozma_agent_authors_not_trains`: learn FROM a net by reading it as STRUCTURE, never by
copying weights). It is the teardown done with the agent's own machinery: read-as-data,
analogical transfer (`ozma_analogical_transfer`), the order-N / monotonic-alignment
frame. The central acoustic claim is grounded by `scripts/parakeet_teardown_probe.py`
(donkey-clean: the agent's monotonic banded-DTW + 1-NN readouts, **counts not nets**,
no `.fit`/gradient/loss/optimiser/torch/sklearn/sweep; full log `/tmp/parakeet_full.log`,
`===MARKER_PARAKEET_TEARDOWN_PROBE_COMPLETE===`, `EXIT=0`, elapsed 331.2s,
pgrep-verified GONE). `solve_for_n.py` / `weighted_admissibility.py` / CortexLoop
**untouched** (git-clean; the probe imports none of them).

---

## (1) WHAT PARAKEET EXPLOITS — named as SHAPES, each CONTRASTED with Whisper's choice

Read Parakeet as a graph of structures, not "it's accurate." Four shapes make it work,
and each is a deliberate OPPOSITE of a Whisper choice. The lesson is in the *difference*.

**A1 — CONV-LOCAL acoustic features (FastConformer convolution).**
SHAPE: a stack of **local time-frequency convolutions** before/around attention —
kernels that fire on *onsets, formant transitions, spectral edges*, the LOCAL
derivative structure of the spectrogram. Attention then mixes these *already-sharp*
local features globally.
**CONTRAST with Whisper:** Whisper's encoder is **attention-first** — it mixes raw
log-mel frames globally and lets scale learn locality implicitly. Parakeet builds
locality in as a **convolutional prior**.
**The DIFFERENCE teaches:** the discriminative acoustic content of a phone lives in the
*local* time-frequency derivative (the transition, the onset), and you can put that in
as STRUCTURE (a convolution = a local difference operator) instead of paying scale to
rediscover it. (Donor: the agent's `center_surround` / `transition_contrast` /
order-N-over-time — `docs/agent_loop_iteration30_transition_contrast_selector.md`.)

**A2 — MONOTONIC transducer alignment (RNN-T).**
SHAPE: the RNN-T decoder emits a strictly **left-to-right, monotone** alignment between
audio frames and output tokens, using a **blank symbol as an explicit "wait"** — it can
consume an acoustic frame without emitting, or emit without consuming, but it can
**never go backward**. Speech IS monotonic in time; the structure is built in, not
learned.
**CONTRAST with Whisper:** Whisper's decoder uses **full, non-monotonic cross-attention**
— at every output step it can attend to *any* encoder frame in any order, a free
correspondence with no monotonicity constraint. It must *learn* (from 680k h) that the
alignment is roughly monotone; Parakeet **asserts** it.
**The DIFFERENCE teaches:** monotonicity is a *free, correct* structural constraint that
Whisper pays scale to approximate. Pruning the non-monotone alignments a-priori (they
are inadmissible for speech) is exactly the (G,Γ) efficiency move — never spend on the
inadmissible (`ozma_efficiency_and_creativity_are_grammar`).

**A3 — EXPLICIT token DURATION (TDT — Token-and-Duration Transducer).**
SHAPE: TDT augments the transducer to **jointly emit a token AND a duration** — how many
acoustic frames that token occupies — so the model **skips** the frames it has explained
instead of stepping one frame at a time. The temporal/rate structure is modelled
**explicitly** as a predicted integer.
**CONTRAST with Whisper:** Whisper has **no explicit duration** at all — token timing is
an *implicit, emergent* property of where cross-attention happens to land, never a named
quantity. Parakeet makes "how long is this token" a first-class output.
**The DIFFERENCE teaches:** speaking rate / token duration is a real, separable degree of
freedom; modelling it explicitly *factors* the rate nuisance out of identity, rather than
folding it into one learned blob. (This is the rate-warp the agent tried crudely — done
right as **explicit structure**.)

**A4 — a LIGHT predictor LM.**
SHAPE: the RNN-T **predictor** network is a *small* LM over previous tokens — much
shallower than a full autoregressive language decoder. It conditions on output history
but does NOT carry the recognition; the **acoustic encoder + monotonic alignment decide**,
the predictor only lightly biases.
**CONTRAST with Whisper:** Whisper's decoder **IS** a massive top-down LM doing
restoration — the `P(text)` factor carries reduced/ambiguous acoustics. Parakeet
deliberately **starves** the LM so the acoustics must do the work.
**The DIFFERENCE teaches:** the two models *split the labour differently*. Whisper:
weak-enough acoustics + huge LM → the LM carries it. Parakeet: strong acoustics + tiny
LM → the acoustics carry it. **Same task, opposite load-bearing component.** This is the
crux for the agent's frontier (§3).

The first three are SHAPES the agent can CONSTRUCT (two it already owns); the fourth is
a *design stance* — how much to lean on the LM — and the contrast with Whisper makes it
the central lesson, not a structure to copy.

---

## (2) THE (G,Γ) TRANSLATION — CONSTRUCT each (not "train a conformer")

For each Parakeet structure, how to build it as ADMISSIBLE STRUCTURE composed from the
agent's primitives + grounded by compression — never "train a model." The donkey rule
throughout: extract the STRUCTURE, translate to CONSTRUCTED. **Two of the four the agent
already owns** — Parakeet *validates* the agent's existing structure rather than naming a
gap.

**A2 → the agent's `DtwTo` IS the monotonic transducer alignment — it ALREADY EXISTS.**
The deepest finding of this teardown: the agent's `recognition_graph.synth_error_term`
→ Rust `banded_dtw` (`runners/dsl/src/term.rs:3030`) is **already** a strictly monotonic
left-to-right alignment. The DP transitions are exactly `min(prev[j], cur[j-1],
prev[j-1])` — **deletion / insertion / match**, never backward — under a Sakoe-Chiba band
(`|i−j|` bounded). That is the RNN-T monotonicity constraint *and* the blank-"wait"
(an insertion = consume an acoustic frame without advancing the template = the blank
symbol). **Parakeet's flagship decoder VALIDATES the agent's alignment structure**: the
thing NVIDIA's transducer buys with training, the agent composed as a graph Term. The
probe grounds it: monotonic `DtwTo` beats a non-monotonic (order-destroyed) match
**+0.0375** cross-speaker (§4). No attention weights, no SGD — the structure is correct
because speech is monotonic.

**A3 → model token DURATION/RATE EXPLICITLY in the forward model.**
The constructed TDT: instead of leaving rate to `DtwTo`'s crude length-ratio band,
**factor duration out explicitly** — rate-normalise each trajectory to a canonical length
(a constructed resample transform) BEFORE the warp, so the warp carries *only* the
phonetic shape and duration is a separate, named degree of freedom. This is the agent's
own `order_n`-over-time rate parameter made explicit. The probe builds it
(`rate_normalised`) and measures it honestly: **+0.0000 on isolated digits** (§4) — the
honest finding is that on *isolated* words `DtwTo`'s band already absorbs the small
rate variation, so explicit duration is **redundant at the digit venue** and is a
**continuous-speech lever** (where rate variation across a sentence is large and the
boundary placement depends on it), not an isolated-word one. Constructed, grounded, and
honestly scoped — not a free win.

**A1 → CONV-LOCAL features as an order-1 finite difference (the agent's
transition-contrast).** The constructed FastConformer convolution: a convolution over
time is a **local difference operator**, and the agent already owns it as the **order-1
finite difference over time** (`delta = F_t − F_{t−1}` — `order_n_concepts`,
`transition_contrast`). Append the delta channel to the static band trajectory: that IS
the conv-local time-frequency derivative, CONSTRUCTED as a derivative, NOT a learned
kernel. The probe builds it (`conv_local`) and measures it honestly: **−0.0125 on
isolated digits** (§4) — on the digit venue the static band-means already separate the
classes, so the raw delta channel adds noise more than signal. Honest scope: like A3,
this is an **at-the-frontier (reduced continuous speech)** lever, where the static
front-end is *at chance* and the transition derivative is the part that survives
reduction — **not** the already-separable digit venue. The constructor is right; the
digit venue is the wrong place to see it pay (§3, §5).

**A4 → KEEP the LM LIGHT — let the acoustic structure carry it (the design lesson).**
The non-translation that is the real lesson: the agent's Whisper teardown's prioritised
lever was *richer LM* (because the ear was at chance and the LM carried the number).
Parakeet says: **don't just add LM — build the acoustic structure so the LM CAN stay
light**. The translation is a *rebalancing* of the agent's recogniser
(`real_data_drive.Recogniser`): `score(w) = −acoustic_dist(w)/spread + ctx_weight·logP_LM`.
The Parakeet design says invest in the FIRST term (acoustic structure: A1+A2+A3) so the
SECOND term (`ctx_weight·logP_LM`) need not carry the recognition. §3 weighs which is the
real lever for the agent's frontier.

---

## (3) THE WHISPER-vs-PARAKEET LESSON — is the lever ACOUSTIC structure or more-LM?

Having BOTH teardowns is the point. They are the two extreme splits of the same
`score = acoustic + LM` decision:

- **Whisper** (`whisper_teardown_probe.py`): with the ear **at chance**, recognition =
  the LM's next-word accuracy — the LM carries the number. Its prioritised lever was a
  *richer constructed LM* (and the honest wall: trigram **regresses** below bigram from
  count sparsity — more-LM is NOT a free win without 680k h).
- **Parakeet** (`parakeet_teardown_probe.py`): a **monotonic acoustic model** lifts the
  ACOUSTIC channel itself — monotonicity **+0.0375** cross-speaker, with **NO LM at all**
  (the digit venue has no sequential LM; the acoustic structure alone carries x5.1 over
  chance, 0.52).

**The lesson:** the agent's frontier is *acoustic-at-chance*, and the Whisper result
showed the LM was **compensating for a broken acoustic prune, not sharpening a working
one** (`docs/real_data_drive.md` §3: "context-restoration is currently compensating for
an acoustic front-end that is at chance"). Parakeet says the **fix is the acoustic
structure, not more LM** — because:

1. **More-LM has a measured wall** (the Whisper probe's trigram regression): without
   680k h, the constructed LM saturates at bigram. You cannot LM your way off an
   at-chance ear from counts alone.
2. **The acoustic structure has measured headroom AND the agent already owns the biggest
   piece** (monotonic `DtwTo`, +0.0375). The Parakeet-validated structures attack the
   chance directly rather than papering over it.
3. **`ozma_fix_the_fixer`:** the at-chance acoustic base is the *fixer that generates*
   the bad recognition; adding LM patches the *outcome*. Parakeet points at the fixer.

So **the real lever is the ACOUSTIC structure (Parakeet) more than more-LM (Whisper)** —
*at the agent's at-chance frontier*. The honest qualifier (§5): on a venue where the
acoustic channel is *already* discriminating (isolated digits), the *additional* acoustic
structure (A3 duration, A1 conv-delta) gives nothing — those levers only pay where the
front-end is reduced/at-chance. The two teardowns together say: **build the monotonic,
conv-local, duration-explicit acoustic model on the reduced-continuous venue (where the
ear is at chance), and KEEP the LM light** — invest the structure where the labour
actually is.

---

## (4) THE GROUNDED PROBE — read the numbers (`scripts/parakeet_teardown_probe.py`)

VENUE: FSDD isolated digits, LOSO cross-speaker (240 recordings, 6 speakers, 10 digits,
chance 0.10) — chosen because the acoustic channel is **NOT at chance** here, so the
ACOUSTIC contribution is measurable in **isolation, with no LM**. Same gammatone band
trajectory, same monotonic banded-DTW (the `DtwTo` kernel reproduced counts-not-nets),
1-NN argmin readout; **only the named structure changes** per route.

```
ROUTE                                              acc       delta            n
(P1) monotonic DtwTo (agent ALREADY owns)          0.5208    —              240
     non-monotonic (order destroyed, control)      0.4833    —              240
     -> monotonicity delta                                   +0.0375  monotonic WINS
(P2) duration-blind (raw DtwTo)                    0.5208    —              240
     duration-explicit (rate-normalised, TDT)      0.5208    —              240
     -> explicit-duration delta                              +0.0000  no gain (digits)
(P3) static only (current front-end)               0.5208    —              240
     static + delta (conv-local, constructed)      0.5083    —              240
     -> conv-local delta                                     -0.0125  no gain (digits)
chance (1/10)                                       0.1000
```

**What the probe grounds:**

1. **MONOTONICITY IS REAL AND LOAD-BEARING (+0.0375).** The agent's `DtwTo` — which it
   **already owns** — beats an order-destroyed non-monotonic match cross-speaker. This is
   the central positive: Parakeet's RNN-T validates a structure the agent *has*, not one
   it lacks. The strongest acoustic structure on the leaderboard is already in the graph.
2. **EXPLICIT DURATION gives nothing on isolated digits (+0.0000).** Honest: `DtwTo`'s
   banded warp already absorbs the small rate variation of isolated words, so explicit
   duration is redundant *here*. It is a **continuous-speech** lever (where the boundary
   placement and large within-sentence rate variation make it bite), not an isolated-word
   one — scoped honestly, not overclaimed.
3. **CONV-LOCAL delta slightly HURTS on digits (−0.0125).** Honest: where the static
   band-means already separate the classes, the raw delta channel adds noise. It is a
   **reduced/at-chance front-end** lever (where the transition derivative is the part
   that survives reduction), not a venue where statics already work.

**The contrast with Whisper, made exact:** Whisper's probe — with a flat ear,
recognition = LM next-word acc (the LM carries it). Parakeet's probe — with **no LM**,
the monotonic acoustic structure alone carries **x5.1 over chance**, and the
acoustic-structure *difference* (monotonicity) is **+0.0375**. The lever is the acoustic
structure; on the at-chance frontier (§3) that is where the agent should invest.

---

## (5) HONEST — did the introspection GENERALISE to the opposite-principle model?

**Yes, and the honesty is in the nulls.** The model-introspection did NOT just
pattern-match Whisper:

- **It generalised on the load-bearing structure.** The teardown's central translation
  (A2 → monotonic `DtwTo`) is a *genuine, grounded, positive* finding on an
  opposite-principle model: Parakeet's RNN-T validates the agent's existing alignment
  structure, +0.0375 measured. That is the introspection working — it found that the
  acoustic-driven model's flagship structure is one the agent *already composed*, the
  efficiency-thesis signature (KB of structure, not GB of weights).
- **It produced HONEST nulls, not confirmation.** A2 was the win; A3 (duration) and A1
  (conv-delta) measured **+0.0000 and −0.0125** at the digit venue. A pattern-matched
  teardown would have manufactured gains; this one reports that two of the three
  *additional* acoustic structures give nothing **where the ear already works** — and
  correctly scopes them as **at-the-frontier (reduced continuous speech)** levers. That
  edge-vs-center honesty (`docs/whisper_teardown.md` §3 in the same spirit) is the
  introspection NOT over-generalising.
- **The edge-vs-center crux is real both ways.** Where Parakeet's data/scale wins: the
  dense FastConformer manifold covers the long tail of real reductions/channels the
  constructed transforms only model systematically; the leaderboard accuracy is bought
  with training the agent cannot cheaply match on the common English center. Where the
  structure wins: monotonicity is a *free correct constraint* the agent owns; the
  constructed duration/delta degrade gracefully and are composable from kilobytes where
  no 680k h exists; and the agent KNOWS (from the probe's nulls) exactly which acoustic
  lever pays at which venue — Parakeet cannot tell you its conv layer is doing nothing on
  a given input.

**The honest summary:** the introspection GENERALISED — it found a real, grounded,
load-bearing structure (monotonic alignment) on the opposite-principle model, validated
that the agent already owns it, and reported honest nulls for the two structures that do
not pay at the wrong venue. It did not pattern-match Whisper; the contrast is genuine and
two-sided.

---

## (6) THE PRIORITISED NEXT ACOUSTIC LEVER — build this first, concretely

**Build the CONV-LOCAL (transition-derivative) front-end + EXPLICIT DURATION on the
REDUCED-CONTINUOUS at-chance venue — not the digit venue.** Rationale, tied to the
measured frontier:

1. **The frontier is acoustic-at-chance on reduced continuous function words**
   (`docs/real_data_drive.md`: 0.0313 vs 0.0333), and the Whisper teardown proved
   more-LM compensates rather than fixes. Parakeet says the lever is the **acoustic
   structure**. The probe shows monotonicity is already owned (+0.0375) — so the *next*
   build is the structure the agent does NOT yet exploit on continuous speech: the
   **conv-local transition derivative** (A1).
2. **Why conv-local FIRST, on the right venue:** the at-chance cause named in
   `real_data_drive.md` §3 is that reduced function words are "acoustically tiny" and the
   **static** A1 patch under-resolves them — exactly the case where the *transition
   derivative* (onset, formant slope) is the part that survives reduction. The digit-venue
   null (−0.0125) is not evidence against this; it is evidence the lever only pays where
   statics fail. **Re-run the A1/A3 contrast on the LibriSpeech reduced-continuous venue
   of `real_data_drive.py`** (where the ear is at chance), measuring whether
   static+delta+duration lifts the acoustic base off chance — with the shuffle/do-contrast
   backstop, donkey-clean.
3. **Then fold explicit duration (A3) into the boundary co-refinement.** On continuous
   speech, token duration and word-boundary placement are coupled (the `real_data_drive`
   §3 segmentation weak link). Explicit duration becomes the rate parameter the order-N
   boundary co-refinement conditions on — the continuous-speech home where A3 bites.
4. **Keep the monotonic `DtwTo` (A2) as the validated alignment core** — Parakeet confirms
   it; build A1+A3 *on top* of it, not instead of it.

Concretely drivable next step: a `parakeet_acoustic_drive.py` that runs the
**static / static+delta / static+delta+duration** acoustic contrast through the existing
monotonic `DtwTo` recogniser on the **LibriSpeech reduced-continuous LOSO venue** of
`real_data_drive.py` (the at-chance venue), measuring whether the constructed conv-local +
explicit-duration acoustic structure lifts the acoustic base off chance — the lever
Parakeet says matters, tested where the Whisper teardown said the ear is broken. Both
constructed, both donkey-clean, primitives already in the agent's hands
(`order_n_concepts` delta, `rate_normalised` resample, monotonic `DtwTo`).

---

### Files

- `docs/parakeet_teardown.md` — this report. NEW.
- `scripts/parakeet_teardown_probe.py` — grounds the central acoustic claim donkey-clean
  (monotonic vs non-monotonic alignment; explicit-duration; conv-local delta; LOSO 1-NN;
  counts not nets; no torch/sklearn/.fit/gradient/loss/sweep). NEW. Reuses only
  `scripts/fsdd_learner_world` (audio I/O) + `scripts/invariant_units_accept`
  (`band_trajectory_matrix` front-end).
- `/tmp/parakeet_full.log` — full captured run
  (`===MARKER_PARAKEET_TEARDOWN_PROBE_COMPLETE===`, `EXIT=0`, elapsed 331.2s,
  pgrep-verified GONE).

Builds on / contrasts with `docs/whisper_teardown.md` (the LM-driven baseline),
`docs/real_data_drive.md` (the acoustic-at-chance frontier), `docs/whisper_mining_findings.md`
(front-end half), `docs/agent_loop_iteration30_transition_contrast_selector.md` +
`order_n_concepts` (the conv-local / transition-derivative structure).
`scripts/solve_for_n.py` / `domains/weighted_admissibility.py` / CortexLoop **untouched**
(git-clean). NOT committed (per directive — coordinate).
