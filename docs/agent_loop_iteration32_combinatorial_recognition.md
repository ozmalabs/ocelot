# Iteration 32 — COMBINATORIAL recognition over the channels (each its role; Bayes product)

> User: "there is no reason the result cannot be combinatorial." Builds on iter-26
> (concat-DTW diluted), iter-27 (one global weighted-SUM was config-sensitive/weak),
> iter-30/31 (the transition channel + recognition-through-transition), and
> `docs/research_speech_deficits.md` (the *what*-channel ⊥ *who*-channel are
> separable → combinable). Written INCREMENTALLY; runs captured to `/tmp`;
> `PYTHONUNBUFFERED=1`.

## The insight being acted on

iter-26 (CONCATENATE both channels, one distance) and iter-27 (one GLOBAL weighted
SUM) were WEAK combinations, not proof combination fails. Both fuse the two channels
into ONE shared measure, so the weak channel contaminates the strong (iter-26
regressed below the strong channel alone; iter-27 was config-sensitive and lost to
the best single channel at n=4). The recognition can be COMBINATORIAL: each channel
contributes its ROLE and the word is the one the channels JOINTLY pick out.

The two complementary channels, both read off the SAME grown patch bank:
- **SPECTRAL-DETAIL** = the grown-patch flat readout (`l2_flat`) — "what is this";
  the strongest SINGLE channel on the within-voice exemplar match (iter-31 1-NN flat).
- **TRANSITION** = the agent's order-1-over-time operator
  (`grown_representation.transition_channel`) — "which word across voices"; the
  cross-voice channel the iter-30 selector scores on.

Each is lossy ALONE; complementary TOGETHER.

## (1) The agent DERIVES the combination KIND — autonomous, no-donkey

`scripts/iter32_combinatorial_derive.py` registers iter-31's HONEST residual as a held
postulate (`fused_measure_frame`) — stated STRUCTURALLY: two complementary components,
each lossy alone, the prior rules fused them into ONE shared measure (concat / global
blend) which let the weak contaminate the strong; the right decision keeps each
component's OWN role and selects the unit BOTH point to. The residual text does NOT
name the fix (no "conjunction", "product", "agreement", "rank", "vote",
"combinatorial", "argmax", "recognition_graph", "both", "Bayes"). It then runs the
agent's OWN `synthesize_gaps` with the agent's OWN harvested shape-library (249 shapes).

**What the agent's shapes surfaced over the residual (verbatim, `/tmp/iter32_step1_derive.txt`):**

```
(B) take evidence from each observation by its reliability -> 1 gap(s)
    via ['rule_derived__Bayes_updates_beliefs'] (concept ['Bayes_updates_beliefs']):
        posterior P(H|E) ∝ P(E|H)·P(H)
```

(plus an order-1 `scale_cancellation`/speaker-normalisation gap the loop has seen
before.)

**Autonomous? YES.** The agent's own `Bayes_updates_beliefs` shape fired on the
residual and named the combination KIND: **take evidence from each channel SEPARATELY
and MULTIPLY it** — `posterior ∝ likelihood · prior`, i.e. a PRODUCT of per-channel
evidence. Not a concat, not a global weighted sum: each channel contributes its own
likelihood `P(w | channel)`; the channels' evidence is MULTIPLIED; the word the
channels JOINTLY make most probable wins. A channel uninformative for a contrast
multiplies in near-flat and cannot drag the channel that carries it. The agent derived
the KIND (product-of-evidence); it did NOT name the recognition_graph or the term.

## (2) The COMPOSED combinatorial recognizer — auditable: graph Term, no global weight, no fit

`domains/combinatorial_recognizer.py` composes the recognizer the derived Bayes shape
dictates, as the agent's recognition_graph Argmax-of-score (graph Term-tree, evaluated
natively via `substrate.evaluate` — verified synthetic: the Argmax-of-product picks the
candidate both channels jointly support):

```
P_c(w | s)  = softmax over candidates of -D_c(s,w)/T_c        (channel c's likelihood)
   D_c(s,w) = the channel's MIN cosine distance from s to any TRAIN exemplar of w
              (the channel's own 1-NN exemplar evidence — the harness's own metric)
   T_c      = the channel's OWN scale = median candidate distance (scale-free per
              channel; READ from the data per query, not searched)

score(s, w) = P_flat(w|s) · P_trans(w|s)        (the Bayes PRODUCT — the agent's shape)
predict(s)  = Argmax over candidate words w of score(s, w)     (graph Term, native eval)
```

- The graph Term: `Argmax(NodesWhere Concept is_word, w, Times[Attr(w,p_flat),
  Attr(w,p_trans)])` — same Argmax-of-score shape as `recognition_graph.predict_term`
  / `predict_synth_term`; the score is the Bayes product over the two channels.
- The per-channel likelihoods are the channel's OWN 1-NN exemplar evidence (the SAME
  1-NN cosine the harness's `heldout_1nn` uses), turned into a scale-free [0,1]
  likelihood and written as graph attrs on the candidate word nodes; the DECISION is
  the graph Argmax-of-product evaluated natively.

**No-donkey:** NO global hand-tuned weight (the two likelihoods enter the product
symmetrically — the Bayes form), NO gradient fit, NO free parameter (each channel's
temperature is its OWN median distance — a scale normaliser read from the data, not a
search). The combination structure (the product) is the agent's derived Bayes shape.

### Where the wiring lives

- `domains/combinatorial_recognizer.py`: `predict_combinatorial_term` (the graph
  Term), `channel_likelihood` (the per-channel scale-free likelihood).
- `scripts/grown_representation_hvpt_accept.py`: `heldout_combinatorial(...)` —
  per-query, computes both per-channel likelihoods, writes them on the candidate word
  nodes, runs the agent's Argmax-product Term natively. Added `*_1nn_combo` for
  frozen / grown / no-warp / grown-all, plus the combo shuffle read and the
  combo-vs-each-single-channel head-to-head.

## (3) The runs — MULTI-METRIC + shuffle (captured to /tmp)

- `/tmp/iter32_step1_derive.txt` — the derivation (Step 1).
- `/tmp/iter32_smoke_n1.txt` — n=1 smoke (harness validity).
- `/tmp/iter32_n4_run.txt` — n=4, the reported LOSO run (authoritative).

### n=4 REAL-SPEAKER HVPT (LOSO over 6 FSDD speakers) — the MULTI-METRIC table

GROWN = NO cohort warp + accreted patches (transition selector); chance/unigram 0.100.

| metric (grown, mean over 6 LOSO folds) | value | vs |
|---|---|---|
| 1-NN pooled | 0.158 | |
| **1-NN flat (iter-31, spectral-detail channel ALONE)** | **0.517** | the strongest SINGLE channel |
| 1-NN TRANS (iter-31, transition channel ALONE) | 0.263 | the lossy cross-voice channel |
| **1-NN COMBO (iter-32, the Bayes product over BOTH)** | **0.454** | combinatorial |
| 1-NN COMBO — frozen front-end | 0.392 | combo on the baked-in cohort warp |
| 1-NN COMBO — no-warp + seed bank (ablation) | 0.408 | |
| 1-NN COMBO — no-warp + ALL candidates (control) | 0.392 | |

**Combinatorial vs each single channel (grown):**
COMBO 0.454 vs flat-only 0.517 (**Δ −0.063, LOSES**) vs trans-only 0.263 (Δ +0.192,
wins) vs frozen-combo 0.392 (Δ +0.063, wins). **→ COMBO does NOT beat BOTH single
channels** (it clearly beats the weak transition channel and the frozen baseline, but
LOSES to the strong flat channel).

**The decisive SHUFFLE control (real cross-voice structure vs shuffled voice labels):**

| | REAL | SHUFFLE |
|---|---|---|
| 1-NN COMBO (grown) | **0.454** | 0.392 |
| trans-margin (selector objective) | +0.336 | +0.294 |
| 1-NN TRANS | 0.263 | 0.258 |

**COMBO REAL 0.454 > SHUFFLE 0.392 → the combinatorial recognition is REAL, not an
artifact.** The selector also bites (trans-margin + 1-NN-trans both REAL > SHUFFLE).

**PERSONA HVPT (agent-generated voices, held-out persona).** Combo 0.850 vs flat-only
1.000 vs trans-only 0.700 — combo again loses to flat-only. (Caveat: persona flat-only
is a degenerate 1.000 because the persona set re-voices ONE source speaker, so the flat
channel trivially memorises content; the persona flat-only is not a meaningful
comparator. The real-speaker LOSO is authoritative.)

## (4) VERDICT — does the combinatorial recognition beat BOTH single channels and generalise cleanly?

**PARTIAL — and the SAME structural shape iter-27 found, with a cleaner combiner.**

- **vs the weak (transition) channel: YES, decisively** — COMBO 0.454 vs trans-only
  0.263 (+0.192). The product correctly keeps the strong channel's say; the weak
  channel cannot drag it to the weak channel's level (unlike iter-26's concat, which
  regressed *below* the strong channel). This is the property the product form was
  derived to have.
- **vs the frozen baseline: YES** — COMBO 0.454 vs frozen-combo 0.392 (+0.063); and
  the grown flat channel (0.517) clears the frozen flat (0.379, +0.138), so dropping
  the cohort warp + growing the bank is real.
- **vs the strong (flat / spectral-detail) channel: NO** — COMBO 0.454 < flat-only
  0.517 (−0.063). The flat channel ALONE is already the strongest, and multiplying in
  the much-weaker transition likelihood (0.263) pulls the joint Argmax off flat's
  correct pick on the folds where flat is already strong (per-fold: combo ≈ flat where
  flat ≤ 0.45, e.g. lucas combo 0.475 > flat 0.425; combo < flat where flat ≥ 0.5,
  e.g. george/theo). Net: the transition channel is too weak a likelihood source to
  add value to a strong flat channel.
- **shuffle: CLEAN** — COMBO REAL 0.454 > SHUFFLE 0.392. The combination is real
  signal, not warp-driven artifact. (flat + pooled move together with the selector;
  the trans-margin + 1-NN-trans bite.)

**So: the combinatorial recognition WORKS as derived (the agent's recognition_graph
Argmax of the Bayes product, no global weight, no fit, shuffle-clean), and it FIXES
the iter-26/iter-27 dilution failure (the weak channel no longer drags the strong
*below* the strong-alone level — combo 0.454 is between trans 0.263 and flat 0.517,
never below the weak one and never regressing below frozen). But it does NOT beat the
BEST single channel, because the transition channel is simply too lossy as a
likelihood: a near-2× weaker channel multiplied into a strong one nudges the joint
decision off the strong channel's correct pick more often than it rescues a wrong one.**

This is the iter-27 finding re-confirmed with a stronger combiner: **the residual is
not the COMBINATION STRUCTURE (the product is the right combinatorial form — it keeps
each channel's role, dilutes neither below its own level, and is shuffle-clean) but
the TRANSITION CHANNEL's WEAKNESS as a per-candidate likelihood.** A combinatorial
decision can only beat the best single channel when BOTH channels carry comparable,
complementary discrimination; here flat ≈ 2× trans, so the product is dragged toward —
but cannot exceed — the flat channel. The next lever is a STRONGER second channel
(a transition / cross-voice readout whose per-candidate accuracy approaches the flat
channel's), not a different way to combine.

### What was tried for the combination form (no-donkey, no sweep)

The combination is the agent's DERIVED Bayes product (§1) — `P_flat(w|s)·P_trans(w|s)`,
each channel's likelihood scale-normalised by its OWN median candidate distance
(scale-free, read from the data, not searched). No global weight, no per-contrast
hand-tuning, no gradient: the two likelihoods enter symmetrically. Tuning the relative
channel temperatures to down-weight the weak transition channel would be exactly the
search-the-negative-space move the project forbids (and would collapse the
combinatorial decision back toward flat-only); the derived symmetric product stands
and the result is reported as-is.

## Reproduce

```
python scripts/iter32_combinatorial_derive.py            # Step 1: the derivation
                                                          #   (/tmp/iter32_step1_derive.txt)
python -m scripts.grown_representation_hvpt_accept 1      # n=1 smoke (harness validity)
                                                          #   (/tmp/iter32_smoke_n1.txt)
python -m scripts.grown_representation_hvpt_accept 4      # n=4 authoritative LOSO
                                                          #   (/tmp/iter32_n4_run.txt)
```

Required suites green (32): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance. No commit — results + this doc left in
the working tree for re-verification.
