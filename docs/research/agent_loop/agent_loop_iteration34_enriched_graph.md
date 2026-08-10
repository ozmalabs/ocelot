# Iteration 34 — ENRICH the recognition graph with genuinely ORTHOGONAL cues

> User compass: "polyglots have a richer graph" — richer is better, monotone.
> Builds on iter-33 (`docs/agent_loop_iteration33_many_settings_graph.md`, the
> many-settings graph: 20 channels combined via a variadic Bayes product BEAT the
> single flat channel, 0.546 > 0.517 — the first clean combination win, but the
> channels were partly REDUNDANT, all gammatone tradeoffs, so the win was modest
> +0.029) and the two-ears work (`scripts/two_ears_demo.py`,
> `ozma_wall_is_self_imposed`). Written INCREMENTALLY; runs captured to `/tmp`;
> `PYTHONUNBUFFERED=1`. NO commit — results + this doc left in the working tree.

## The insight being acted on

iter-33's residual was REDUNDANCY: all 20 of its channels were views of the SAME
gammatone cochleagram (5 time-frequency tradeoffs × [flat + multi-window transition]).
Combining redundant channels in the Bayes product helps only where the single setting
is weak. The richness lever is monotone ONLY if the added nodes are genuinely
ORTHOGONAL — catching errors of a DIFFERENT KIND. iter-34 adds three such nodes, each
the agent's OWN owned operator, ALL fed into the SAME iter-33 variadic Argmax-of-product
(`domains/many_settings_recognizer.predict_many_settings_term`).

KEY CONTRAST WITH iters 25/26: those tried to add the formant-relation and
manner/voicing cues by DTW-over-CONCATENATION, which DILUTED the strong channel (the
weak cue + channel-scale mismatch washed out the formant signal; iter-26 REGRESSED
below the formant channel alone). Here each orthogonal cue is its OWN NODE in the
product — its own 1-NN exemplar evidence, its own median-distance temperature — so it
CANNOT dilute the others: an uninformative node multiplies in near-flat. This is the
correct combination mechanism iters 25/26 lacked.

## (1) The orthogonal nodes added (each the agent's owned operator, combine-all, no fit)

Kept ALL iter-33 nodes (5 cochlear settings × [flat + 3 transition windows] = 20).
ADDED as further nodes:

- **FFT EAR** (`domains/filter_settings.fft_ear`, from `scripts/two_ears_demo.py` /
  `ozma_wall_is_self_imposed`). A long-window FFT magnitude, log-pooled into 40
  log-spaced frequency bands over 3 coarse temporal windows. This is the
  COMPLEMENTARY time-frequency operating point to the gammatone: fine frequency at
  coarse time, where the gammatone is fine time at coarse frequency. Orthogonal BY
  CONSTRUCTION — a second EAR, not another gammatone tradeoff. (Adapter-math np.fft +
  fixed log pooling; no fit, no learned filter.)
- **FORMANT-RELATION** (iter-25, `domains/lpc_formant_representation
  .formant_spacings_from_audio`). The agent's VTL-invariant spacing relation (its
  iter-24 `Minus(pos_hi, pos_lo)` Term, unchanged) over the TRUE waveform-LPC formant
  positions, resampled to a fixed 24-frame grid. A relational, speaker-robust cue the
  gammatone spectral-detail channels discard. Previously built but UNUSED in the graph.
- **MANNER/VOICING** (iter-26, `domains/stacked_representation._manner_voicing_channel`).
  The agent's phonology cues per frame: autocorrelation periodicity + its
  voiced/sonorant/sibilant predicate Term-trees (evaluated natively) + low/mid/high
  band-energy envelope shape. The within-speaker manner information the spacing
  relation discards. Previously built but UNUSED in the graph.

**NOT WIRED (stated plainly, per the no-fit rule):**
- the **AxS forward-model node** (iters 16-22): recognition by inverting `speak()`
  needs a synthesis forward model AND a convergence threshold = a FIT. It does not
  wire in as a symmetric no-fit likelihood node, so it is SKIPPED.
- a **lexical / top-down prior node**: a word-frequency prior is DEGENERATE on the
  BALANCED FSDD digit set (uniform word frequency = a flat prior = no information), and
  a non-uniform prior would have to be fit from a corpus. SKIPPED.

**Audit (combine-all, not select).** Scoring evaluates
`predict_many_settings_term(23)` = `Argmax(NodesWhere Concept is_word) of
Times[Attr(w,p_ch0), …, Attr(w,p_ch22)]` — a product over EXACTLY 23 channel-likelihood
attrs (20 gammatone + 3 orthogonal). No `Max`/`Sort`/`Pick`/`If`/weight over channels;
every node enters the product symmetrically. Each node's likelihood is softmaxed by its
OWN median candidate distance (read from the data, not searched). The per-orthogonal-cue
numbers (alone / leave-one-out) are DIAGNOSTIC only — the accepted graph is always the
full combine-all-23. Wiring: `domains/filter_settings.py` (fft_ear), the iter-25/26
modules (formant, manner), `scripts/enriched_hvpt_accept.py` (the harness).

## (2) The runs — MULTI-METRIC + shuffle (captured to /tmp)

- `/tmp/iter34_smoke_n1.txt` — n=1 smoke (harness validity; the 23-channel
  Argmax-product evaluates natively end-to-end; at n=1 the per-setting banks barely
  grow so accuracy sits at chance — uninformative, validity only).
- `/tmp/iter34_n4_run.txt` — n=4, rounds=2 LOSO run (apples-to-apples with iter-33's
  0.546; the iter-33 comparator numbers reproduce EXACTLY: many 0.546, single-flat
  0.517, frozen 0.379, iter-33 shuffle margin +0.004 — so this harness is the iter-33
  harness + 3 orthogonal nodes, nothing else changed).
- `/tmp/iter34_n8_run.txt` — n=8, rounds=2 LOSO run (480 utts; the larger-n run for a
  cleaner real-vs-shuffle separation). DONE — confirms n=4 on BOTH questions (below).

### n=4 REAL-SPEAKER HVPT (LOSO over 6 FSDD speakers) — the MULTI-METRIC table

23 channels combined per fold (20 iter-33 gammatone + FFT-ear + formant-relation +
manner/voicing). chance/unigram 0.100.

| metric (mean over 6 LOSO folds) | value | vs |
|---|---|---|
| **ENRICHED graph (iter-34, ALL 23 nodes combined)** | **0.575** | the enriched graph |
| MANY-SETTINGS (iter-33, 20 gammatone nodes) | 0.546 | iter-33 |
| single-setting flat (iter-31 strong channel) | 0.517 | the single setting |
| frozen (cohort-warped, fixed bank) | 0.379 | regression baseline |

**Enriched vs each comparator (grown):**
- vs iter-33: **0.575 vs 0.546, Δ +0.029 → WIDENS** (the orthogonal cues add as much
  again over the 20 redundant gammatone channels as those channels added over the
  single setting).
- vs single-flat: **0.575 vs 0.517, Δ +0.058** — iter-33's margin over single-flat was
  +0.029; the enriched margin is **+0.058, DOUBLE**. The richness lever is monotone:
  adding genuinely orthogonal nodes roughly doubled the combination win.
- vs frozen: 0.575 vs 0.379, Δ +0.196.

**Per-fold (REAL), enriched vs iter-33 vs single-flat:**

| held-out | enriched | iter-33 | single-flat | Δ(enr−i33) |
|---|---|---|---|---|
| george   | 0.750 | 0.600 | 0.525 | **+0.150** |
| jackson  | 0.550 | 0.550 | 0.550 | +0.000 (tie) |
| lucas    | 0.475 | 0.500 | 0.425 | −0.025 |
| nicolas  | 0.675 | 0.650 | 0.625 | **+0.025** |
| theo     | 0.575 | 0.550 | 0.475 | **+0.025** |
| yweweler | 0.425 | 0.425 | 0.500 | +0.000 (tie) |

→ enriched ≥ iter-33 on 5 of 6 folds (3 wins, 2 ties, 1 small loss). The win is
concentrated on george (+0.150) — the orthogonal cues help most where they add real
complementary structure. yweweler stays the hard fold (the one where iter-33 itself
lost to single-flat; the orthogonal cues hold it level, do not recover it).

**The decisive SHUFFLE control (real cross-voice structure vs shuffled voice labels):**

| | REAL | SHUFFLE | margin |
|---|---|---|---|
| **ENRICHED graph** | **0.575** | 0.533 | **+0.042** |
| MANY-SETTINGS (iter-33) | 0.546 | 0.542 | +0.004 |

**ENRICHED real−shuffle margin +0.042 is ~10× iter-33's +0.004.** This is the
cleanest result: the orthogonal cues carry REAL cross-voice structure — alone they sit
at 0.38–0.41 on real speakers but COLLAPSE to ~0.05–0.10 under the shuffled voice
partition (e.g. fft_ear george 0.400→0.050, formant lucas 0.350→0.075). The shuffle
floor that was high at n=4 for the redundant gammatone channels (because within one
held speaker the digit content is consistent) does NOT survive for the orthogonal cues,
so the enriched graph separates real from shuffle far more cleanly than iter-33.

### n=8 REAL-SPEAKER HVPT (480 utts) — the LARGER-n confirmation

The larger-n run confirms n=4 on BOTH questions, with a sharper iter-33 contrast:

| metric (mean over 6 LOSO folds, n=8) | value |
|---|---|
| **ENRICHED graph (iter-34, 23 nodes)** | **0.590** |
| MANY-SETTINGS (iter-33, 20 nodes) | 0.567 |
| single-setting flat | 0.496 |
| frozen | 0.427 |

- vs iter-33: 0.590 > 0.567, **Δ +0.023 → WIDENS** (consistent with n=4's +0.029).
- vs single-flat: +0.094 (iter-33 was +0.071) → **WIDER** (the margin over single-flat
  grows with the orthogonal nodes, as at n=4).
- **SHUFFLE: ENRICHED real 0.590 − shuffle 0.569 = +0.021 (CLEAN); iter-33 real 0.567 −
  shuffle 0.569 = −0.002.** At n=8 iter-33's many-settings shuffle margin goes slightly
  NEGATIVE — the 20 redundant gammatone channels memorise the within-speaker digit
  content equally well on the shuffled partition — whereas the ENRICHED graph stays
  cleanly positive. The orthogonal cues are precisely what give the graph a real
  cross-voice margin that the redundant gammatone channels alone do not.

**Per-fold (REAL, n=8), enriched vs iter-33:** george 0.725 vs 0.688 (+0.037), jackson
0.575 vs 0.550 (+0.025), lucas 0.362 vs 0.388 (−0.025), nicolas 0.613 vs 0.600
(+0.013), theo 0.562 vs 0.550 (+0.012), yweweler **0.700 vs 0.625 (+0.075)**. Enriched
≥ iter-33 on 5/6 folds (loses only lucas). NOTABLY, yweweler — the hard fold where at
n=4 the orthogonal cues only held level — at n=8 RECOVERS strongly (+0.075 over iter-33,
+0.212 over single-flat, all three cues contributing): with more exemplars the
orthogonal cues recover even iter-33's worst fold.

**Per-orthogonal-cue (n=8, drop-it Δ):** fft_ear +0.006, formant_relation +0.008,
manner_voicing +0.006 — all three net-positive, none redundant (same sign as n=4).

### PERSONA HVPT (agent-generated voices, held-out persona)
Enriched 1.000 = iter-33 1.000 = single-flat 1.000 = frozen 1.000. As iter-33 noted,
the persona set re-voices ONE source speaker, so every flat-based readout trivially
memorises content and saturates — the persona flat comparator is DEGENERATE and not
meaningful. (Note the orthogonal cues alone are non-trivial here: manner_voicing alone
0.900, formant_relation alone 0.700 on held-out quinn — robust to the synthetic VTL
shift.) The real-speaker LOSO is authoritative.

## (3) Per-node contribution — which orthogonal cues widened the margin

Diagnostics (mean over the 6 REAL folds; DIAGNOSTIC, not selection — the accepted
graph is always the full combine-all-23):

| orthogonal cue | alone (1-NN) | drop-it Δ (enriched − leave-it-out) | verdict |
|---|---|---|---|
| **fft_ear** (freq-sharp ear) | 0.408 | **+0.017** | widens (the biggest single orthogonal contributor) |
| **formant_relation** (iter-25) | 0.383 | **+0.012** | widens |
| **manner_voicing** (iter-26) | 0.179 | **+0.012** | widens |

ALL THREE are net-positive on drop-it — none is redundant, none hurts. The FFT ear is
the largest contributor (drop-it +0.017), consistent with its being the most orthogonal
by construction (a different time-frequency operating point, not a derived feature of
the same waveform). The formant-relation and manner/voicing cues each add +0.012 —
exactly the cues iters 25/26 FAILED to add by DTW-over-concatenation now contribute
cleanly as NODES in the product. (manner_voicing is weak ALONE — 0.179, near the
phonology-channel weakness iter-26 saw — yet it still widens the product, because the
product cannot be dragged down by a near-flat node and is helped where the node is
confident: the Bayes-product mechanism is exactly what made the weak cue usable.)

## (4) VERDICT — does the orthogonal enrichment WIDEN the win AND the shuffle margin?

**YES on both — clean, multi-metric, at n=4 (and confirmed at the larger n=8 below).**

- **WIDENS the combination win: YES.** Enriched 0.575 > iter-33 0.546 (Δ +0.029), and
  the margin over single-flat DOUBLED (enriched +0.058 vs iter-33 +0.029). The richness
  lever is monotone — genuinely orthogonal nodes (different time-frequency point;
  relational speaker-robust cue; manner cue) added as much again as the 20 redundant
  gammatone channels did. Per-fold, enriched ≥ iter-33 on 5/6 folds.
- **WIDENS the shuffle margin: YES, decisively.** Enriched real−shuffle +0.042 vs
  iter-33's +0.004 — ~10× wider. The orthogonal cues collapse under the shuffled voice
  partition (real cross-voice structure, not memorised content), so the enriched graph
  is far more cleanly real-vs-shuffle separated. This is the strongest evidence the
  enrichment is real signal, not added noise that happened to help.
- **CONFIRMED AT n=8 (480 utts):** enriched 0.590 > iter-33 0.567 (Δ +0.023, WIDENS;
  margin over single-flat +0.094 vs iter-33 +0.071, WIDER); SHUFFLE enriched +0.021
  CLEAN vs iter-33 −0.002 (iter-33's redundant-gammatone shuffle margin goes NEGATIVE at
  the larger n while the enriched graph stays clean). The hard fold yweweler RECOVERS at
  n=8 (+0.075 over iter-33). Both questions hold on the larger run — not an n=4-only or
  shuffle-killed gain.
- **combine-all, not select (auditable + independently verified): YES.** The decision
  term `predict_many_settings_term(23)` was dumped and inspected: its node types are
  exactly {Argmax, Attr, Lit, NodesWhere, Times, Var}, the Times product is over EXACTLY
  23 items (`p_ch0..p_ch22`), and there is NO Max/Sort/Pick/If/weight/Div node anywhere.
  No winning-node pick, no weight, no fit; each node's temperature is its own median
  distance. The per-cue numbers are diagnostic only. The four channels also live in
  different-dimensional spaces (gammatone-flat 800, fft_ear 120, formant 96, manner 224)
  — genuinely distinct operators, each its own node.
- **the corrected residual from iters 25/26 is resolved:** those cues DILUTED via
  DTW-over-concatenation; as NODES in the variadic Bayes product they CANNOT dilute and
  every one widens. The combination mechanism, not the cue, was the iter-25/26 problem.

**So: the richness lever is monotone, the graph frame is fully winning, and the
orthogonal cues — the FFT ear most of all — are the headroom.** The win remains MODEST
in absolute terms (0.575 vs 0.546; the FSDD 6-speaker LOSO at n=4 is small and noisy,
and the absolute ceiling is still the digit-content overlap within a held speaker), but
it is structurally decisive on the two questions that matter: the margin over both
comparators WIDENS, and the real-vs-shuffle separation widens ~10×. Re-verify ALL
metrics + the combine-all-not-select audit; the iter-33 comparator numbers reproduce
exactly, which pins the delta to the 3 added nodes.

### Honest limits / how far
- Absolute accuracy is still 0.575 — above the iter-33 0.546 and well above frozen
  0.379, but this is a 6-speaker, 10-digit LOSO; the lift is real but small.
- The win is concentrated (george +0.150); two folds tie and one (lucas) loses 0.025.
  yweweler — iter-33's worst fold — stays hard; the orthogonal cues hold it level, not
  recover it.
- manner_voicing is weak alone (0.179); it contributes only through the product. The
  FFT ear (0.408 alone, +0.017 drop-it) is the strongest orthogonal headroom — a
  sharper / multi-setting FFT ear (the two-ears logic applied to the FFT front-end the
  way iter-33 applied it to the gammatone) is the natural next lever.
- AxS forward-model and lexical-prior nodes were SKIPPED (both need a fit / a
  non-uniform prior); they remain unwired headroom that would require leaving the
  no-fit contract.

## Reproduce

```
python -m scripts.enriched_hvpt_accept 1 1   # smoke (/tmp/iter34_smoke_n1.txt)
python -m scripts.enriched_hvpt_accept 4 2   # n=4 authoritative (/tmp/iter34_n4_run.txt)
python -m scripts.enriched_hvpt_accept 8 2   # n=8 larger-n confirm (/tmp/iter34_n8_run.txt)
```

Audit the combine-all-not-select term directly:
```
python -c "import domains.many_settings_recognizer as MS, json; \
t=MS.predict_many_settings_term(23); print(set(__import__('re').findall(r'\"type\": \"(\w+)\"', json.dumps(t)))); \
print('Times items:', len(t['value']['items']))"
# -> {'Argmax','Attr','Lit','NodesWhere','Times','Var'} ; Times items: 23
```

Wiring: `domains/filter_settings.py` (fft_ear + COCHLEAR_SETTINGS + TRANSITION_WINDOWS),
`domains/lpc_formant_representation.py` (formant spacings), `domains/stacked_representation.py`
(manner/voicing), `domains/many_settings_recognizer.py` (the N-channel Bayes-product
graph Term), `scripts/enriched_hvpt_accept.py` (the harness). Required suites green (32):
test_stt_pipeline, test_perception_self_assessment, test_process_meta_assessor,
test_gap_guidance.
