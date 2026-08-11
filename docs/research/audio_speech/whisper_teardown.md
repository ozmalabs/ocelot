# Whisper teardown — read it as DATA, extract the STRUCTURES, translate to CONSTRUCTED admissible structure

Whisper (OpenAI encoder–decoder ASR, ~680k h weakly-supervised) solves exactly
the frontier just measured at CHANCE in `docs/real_data_drive.md`: acoustic word
identity on real continuous reduced speech (the agent's bottom-up acoustic base
**0.0313** vs chance **0.0333**; the **bigram context prior carried** the measured
0.1096). This is NOT a generic Whisper summary and NOT "train a transformer" (the
donkey — `ozma_agent_authors_not_trains`: learn FROM a net by reading it as
STRUCTURE, never by copying weights). It is the teardown done with the agent's own
machinery: read-as-data, analogical transfer, the order-N / collapse frame.

A prior mine (`docs/whisper_mining_findings.md`) already settled the
**representation/front-end** question: Whisper's log-mel front-end is *worse* than
the agent's gammatone+patch (LOSO 0.29 vs 0.58 DTW), and its speaker-invariance is
**distributed, un-portable trained residue** in the 4 attention layers
(+0.10/layer, no single transform). That ruled OUT the cheap front-end fix. **This
teardown is the complementary, deeper half: the DECODER and the alignment** — the
top-down language structure and the soft analysis-by-synthesis that are where
Whisper actually wins on reduced continuous speech, and which the agent's frontier
result (context carrying the number) says is the live lever.

Central claim grounded by `scripts/whisper_teardown_probe.py` (donkey-clean: counts
not nets; full log `/tmp/whisper_full.log`, `===MARKER_WHISPER_TEARDOWN_PROBE_COMPLETE===`,
pgrep-verified GONE). `solve_for_n.py` / CortexLoop **untouched** (this is analysis;
the probe imports neither).

---

## (1) WHAT WHISPER ACTUALLY EXPLOITS — named as SHAPES (the agent's derivation)

Read Whisper as a graph of structures, not "it's big." Using the agent's held
speech-science + its ML/transformer concepts + analogical transfer, five structures
make it work on real continuous reduced speech. For each, the SHAPE:

**S1 — The decoder is a massive top-down LANGUAGE MODEL doing restoration.**
SHAPE: `argmax_W P(text | audio) = argmax_W P(audio | text)·P(text)` — an
autoregressive `P(w_t | w_<t, audio)` where the `P(text)` factor, learned over
680k h, is an enormous prior that *restores* the word the acoustics under-determine.
On reduced function words (`the/of/to/a`) the acoustic likelihood is nearly flat;
the decoder's language prior carries the identity. This is the **same shape as the
agent's measured frontier**, scaled: bottom-up acoustic at chance, the context
prior carrying the number. Whisper's decoder is the agent's bigram prior taken to a
deep, high-order, lexical limit. (Analogical donor: `machine_learning:autoregressive`
/ the agent's own `top_down_restoration` postulate.)

**S2 — Cross-attention is a SOFT, ITERATIVE analysis-by-synthesis ALIGNMENT.**
SHAPE: at each decoder step the model computes a soft distribution over encoder
frames (`softmax(Q·Kᵀ)`) — a *differentiable, re-weightable* correspondence between
the hypothesised word and the acoustic evidence, refined token-by-token jointly with
the emerging hypothesis. This is the soft cousin of the agent's **hard `DtwTo`
alignment**: where DtwTo commits to one monotone warp, cross-attention keeps a
weighted admissibility over alignments and lets the language hypothesis *steer*
which acoustic frames to attend — perception by inverting/aligning a forward model,
exactly the agent's analysis-by-synthesis loop, made soft and joint. (Donor:
`control:forward_inverse`, the agent's own AbS.)

**S3 — A reduction / coarticulation-ROBUST acoustic representation.** SHAPE:
the encoder maps the acoustically *degenerate* reduced form to a region of
embedding space that the decoder can still disambiguate — invariance to the
*reduction itself*, not just to speaker. A schwa-collapsed `to` and a citation
`to` land close enough that the language prior can pick between them. The agent's
frontier names this precisely: reduced function words are "acoustically tiny," the
A1 patch under-resolves them. Whisper's encoder is robust to reduction because it
saw every reduction 680k h worth of times. (Donor: `machine_learning:learned_invariance`.)

**S4 — JOINT acoustic+language+alignment refinement (one objective).** SHAPE:
beam search over the decoder co-refines, in a single pass, *word identity +
boundary placement + acoustic alignment* — there is no separate segmenter; the LM,
the acoustics, and the alignment are settled together, each constraining the others.
This is the agent's **order-N co-refinement** (`solve_for_n`: hypothesise →
synthesise → match → refine, n passes, back-fitting all components jointly) — the
agent already HAS this shape; Whisper does it with one trained network instead of an
explicit loop. (Donor: the agent's order-N analysis-by-synthesis loop itself.)

**S5 — Learned invariances from SCALE (the interpolator).** SHAPE: 680k h of
(audio, text) pairs let SGD memorise a dense manifold of how-words-sound-in-context;
inference is interpolation on that manifold. This is the one structure that is *not*
a discrete mechanism — it is the trained residue the prior mine already identified
(distributed +0.10/attention-layer, no extractable transform). It is real, it is
load-bearing for the clean center, and it is the honest **edge-vs-center** crux (§3).

The first four are SHAPES the agent can construct. The fifth is the thing scale
buys that structure cannot cheaply match — named honestly, not waved away.

---

## (2) THE (G,Γ) TRANSLATION — CONSTRUCT each, don't learn it from 680k h

For each exploited structure, how to build it as ADMISSIBLE STRUCTURE (composed
from the agent's primitives + grounded by compression), not interpolated from data.
The donkey rule throughout: extract the STRUCTURE, translate to CONSTRUCTED; never
"train a model."

**S1 → a RICHER constructed top-down language structure than the bigram.**
The agent's recogniser already has the exact readout shape
(`real_data_drive.Recogniser.recognise`):
`score(w) = -acoustic_dist(w)/spread + ctx_weight·logP_LM(w | history)`.
The frontier result PROVES the acoustic term is flat (at chance) and the LM term is
carrying it — so this is the **single highest-leverage** translation. Whisper's
decoder = this LM term, deep and high-order. The constructed path is NOT to fit a
net but to make `logP_LM` a **structured** prior the agent composes as graph data:
higher-order counts (trigram/4-gram with backoff), **class-based** smoothing
(syntactic categories — function-word slots, "DET→NOUN", "PREP→DET") so the prior
generalises beyond seen n-grams without seeing 680k h, and the agent's own
transitional-probability / sequence structure (the `sentence_learning` TP machinery
it already built). The counts are graph data (a count, not a fitted parameter); the
argmax is the native readout. **The probe (`whisper_teardown_probe.py`) measures
this directly**: with the ear flat, recognition = the LM's held-out next-word top-1.

**S2 → the agent's ORDER-N loop is the soft alignment — it already exists.**
Replace/augment the hard `DtwTo` with the order-N analysis-by-synthesis collapse
the agent built (`solve_for_n` engine + `weighted_admissibility` collapse): keep a
WEIGHTED admissibility over alignments (the soft excluder, not one hard warp), let
the language hypothesis (S1) re-weight which acoustic frames are admitted, iterate
n passes to convergence. This is cross-attention's "soft, hypothesis-steered,
iterative" shape constructed as the agent's own collapse manifold — no attention
weights, no SGD. The agent OWNS every piece (`scripts/solve_for_n.py`,
`domains/weighted_admissibility.py`, `iterate_to_n`).

**S3 → model COARTICULATION/REDUCTION in the FORWARD MODEL (the key move).**
The deepest translation: a reduced word IS the forward model run *with reduction*.
Instead of needing an encoder that learned reduction-invariance from data, make the
agent's owned forward model (`analysis_by_synthesis_accept.synth_feats`,
`forward_model_drive`) GENERATE the reduced form — apply the reduction/coarticulation
transform (schwa-centralisation, duration-shortening, neighbour carryover —
constructed from the agent's `formant_transitions` / `coarticulation predict-remove`
postulate) to the citation exemplar, THEN match. The heard reduced token now matches
a *synthesised reduced* exemplar. This is analysis-by-synthesis doing what Whisper's
encoder does with scale, but as a CONSTRUCTED generative transform: invariance to
reduction comes from *modelling the reduction*, not memorising 680k h of it. (This
is the agent's own `mathematics:removable_context` shape applied forward.)

**S4 → co-refine segmentation + identity + context in the order-N loop.**
The agent's frontier named segmentation (sonority-valley cuts) as the weak link —
fragments and merges. The translation: don't segment first then recognise; fold the
word boundary into the order-N collapse as another component to co-refine, so the
LM prior (S1), the acoustic match (S2/S3), and the boundary settle jointly — exactly
Whisper's no-separate-segmenter joint beam, constructed as the agent's back-fitting
pass. The agent has the loop; this wires the boundary into it as a refined parameter
rather than a fixed pre-cut.

**S5 → do NOT try to construct the interpolator.** The honest non-translation:
the 680k-h dense manifold is not a structure to compose — it is interpolation. The
constructed answer does not match it on the clean center (§3); it wins elsewhere.

---

## (3) THE HONEST EDGE-vs-CENTER — where scale wins, where structure wins

Weighted, not triumphalist. Both directions are real.

**Where Whisper's SCALE genuinely wins (the clean CENTER — and the agent cannot
cheaply construct it):**

- **The dense reduction manifold (S5).** 680k h memorises *every* coarticulatory
  realisation of every word in every context. The agent's constructed reduction
  transform (S3) models the *systematic* part (schwa, shortening, regular
  carryover); it will NOT capture the long tail of idiosyncratic, dialectal,
  channel-specific realisations that the interpolator covers for free. On clean,
  in-distribution, common English the interpolator simply has more of the answer
  already stored. Structure cannot cheaply match this.
- **The high-order lexical LM, robustly.** The probe shows the honest wall:
  uni 0.1734 → bi **0.2271** → tri **0.1950** — trigram counts *regress* on ~8981
  tokens because n-gram sparsity bites. Whisper's decoder buys an effectively
  infinite-order, smooth LM from 680k h that does NOT suffer this sparsity. The
  agent's constructed LM (S1) climbs at bigram but cannot reach Whisper's lexical
  depth from counts alone — it needs the *structured* (class/syntactic) prior to
  generalise, and even then won't match a 680k-h decoder on the common center.
- **Breadth of vocabulary/language.** Whisper covers ~99 languages and an open
  vocabulary from scale; the constructed approach is admissible only where the agent
  has built the structure (binary admissibility — capability is present or zero).

**Where the (G,Γ) frame wins (the EDGE — the interpolator breaks, the constructor
doesn't):**

- **Out-of-distribution / novel reductions the manifold never saw.** A reduction the
  training set lacks is *outside* Whisper's interpolation hull → it hallucinates
  (Whisper's known failure mode: confident fabricated text on novel/degraded input).
  The constructed forward model (S3) *generates* the reduced form from the
  generative transform, so a never-heard reduction of a known word is still
  synthesisable and matchable. The constructor degrades gracefully; the interpolator
  fabricates.
- **Low-resource / no 680k h.** Where the data does not exist, Whisper cannot be
  built at all; the constructed LM + forward model are composable from kilobytes of
  structure (the agent's whole thesis — capability is KB-of-structure, not GB-of-weights).
- **Inspectability + honest uncertainty.** The constructed score is a readable sum
  of an acoustic distance and a counted log-prior; when the acoustic term is flat the
  system KNOWS it is the prior carrying the number (the frontier reported exactly
  this). Whisper's confidence is uncalibrated on OOD and it cannot tell you the ear
  was at chance — it just emits fluent text. The agent's shuffle control splits
  restoration from frequency *in the same breath as the measurement*; Whisper has no
  such internal honesty backstop.
- **The closed-set edge it already nears.** On the sharp-ear isolated-digit venue the
  constructed top-down recovery already closed **76%** of the blunt→sharp gap
  (`docs/topdown_recovery.md`) — where the structure is admissible, the constructor
  is competitive *without* the 680k h.

**The honest summary:** Whisper wins the dense common center by interpolation the
agent cannot cheaply construct (S5, and the robust high-order LM). The constructed
(G,Γ) approach wins the edge — OOD reductions, low-resource, inspectability, honest
uncertainty — and is competitive wherever the language/forward structure is
admissible. This is `ozma_beat_model_asr_at_the_edge`, measured-consistent, not asserted.

---

## (4) THE PRIORITISED NEXT LEVER — build this first, concretely

**Build a RICHER CONSTRUCTED TOP-DOWN LM (S1), structured not just higher-order —
then fold it into the order-N loop (S4).** Rationale, tied to the just-measured frontier:

1. **The frontier says the acoustic channel is at chance and context carries the
   number.** With a flat ear the recogniser argmax IS the LM argmax — so the LM is
   *literally* the recognition number right now. Improving the LM moves the measured
   result the most, immediately, with the least new machinery (the readout already
   exists in `real_data_drive.Recogniser`).
2. **The probe grounds both the promise and the wall.** Order-dependent restoration
   is real and shuffle-collapsing (bigram +0.0582, trigram +0.0549 above shuffle) —
   it is genuine sequential restoration, the Whisper-decoder structure in miniature.
   BUT raw trigram (0.1950) regresses below bigram (0.2271): **higher-order counts
   are NOT a free win** — sparsity bites. So the lever is NOT "crank n"; it is
   **structure the prior so it generalises** without 680k h:
   - **class-based / syntactic backoff** (function-word slot categories: DET, PREP,
     PRON, AUX) so unseen n-grams fall back to a *grammatical* prediction, not a
     unigram — this is the agent composing admissible grammatical structure (G,Γ
     proper), the exact thing scale fakes by interpolation;
   - **fold the boundary into the loop (S4)** so the prior conditions on correctly-cut
     history, not on the lossy sonority-valley fragments the frontier flagged.
3. **Why this over S3 (reduction-in-forward-model) FIRST:** S3 is the higher-ceiling
   lever for the *acoustic* base (it attacks the chance directly) and is the right
   SECOND build — but the LM lever is cheaper, the readout exists, the frontier
   proves it is currently load-bearing, and it sharpens the venue so that when S3
   lifts the acoustic base off chance, the LM compounds on a real prune rather than
   carrying a broken one. Order: **(a) structured top-down LM + boundary-in-loop
   now; (b) reduction-modelling in the forward model next.** Both constructed, both
   donkey-clean, both already have their primitives in the agent's hands.

Concretely drivable next step: extend `real_data_drive.py`'s prior from add-1 bigram
to a **class-backoff** prior (the agent's syntactic categories as graph data) +
condition the history on the order-N co-refined boundary, and re-run the same
three-route do-contrast with the shuffle backstop — measuring whether structured
backoff beats raw trigram (the probe's regression) on the same held-out tokens.

---

### Files

- `docs/whisper_teardown.md` — this report. NEW.
- `scripts/whisper_teardown_probe.py` — grounds the central claim donkey-clean
  (LM next-word accuracy by order, LOSO, shuffle control; counts not nets; no
  torch/sklearn/.fit/gradient/loss). NEW. Reuses only `sentence_learning.gather_pairs`
  (the world-adapter corpus walk).
- `/tmp/whisper_full.log` — full captured run
  (`===MARKER_WHISPER_TEARDOWN_PROBE_COMPLETE===`, pgrep-verified GONE).

Builds on `docs/whisper_mining_findings.md` (front-end/representation half — ruled
OUT the cheap front-end fix), `docs/real_data_drive.md` (the acoustic-at-chance
frontier), `docs/topdown_recovery.md` + `docs/jabberwock_human_bad_ears.md` (the
top-down compensation the structures translate INTO). `solve_for_n.py` / CortexLoop
UNTOUCHED. NOT committed (per directive — coordinate).
