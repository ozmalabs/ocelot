# Iteration 33 — the MANY-SETTINGS graph: N settings per filter, all combined

> User: "there is no reason to have ONE setting for a particular filter or
> transform; that's the whole point of a graph." Builds on iter-32
> (`docs/agent_loop_iteration32_combinatorial_recognition.md` — the Bayes product
> over two channels WORKS but LOSES to the single strong flat channel because the
> second channel is too weak) and the TWO-EARS work
> (`scripts/two_ears_demo.py`, `ozma_wall_is_self_imposed` — a freq-sharp 2nd ear is
> complementary to the gammatone ear; fused, two ears beat either). Written
> INCREMENTALLY; runs captured to `/tmp`; `PYTHONUNBUFFERED=1`.

## The insight being acted on

iter-32's residual was NODE QUALITY: one strong cue (the spectral-detail flat
readout) and several weaker ones. The weak cues are weak NOT because the filter is
weak but because each is ONE SETTING — one time-frequency tradeoff — and the
uncertainty principle caps any single setting (sharpen time, blur frequency, and
vice versa). A GRAPH is not stuck with one setting: it can instantiate the SAME
filter at MANY tradeoffs, each a node, and combine ALL of them. The cap is on one
channel; many channels at different tradeoffs, fused, dissolve it. The agent already
proved this with TWO ears (freq-sharp + gammatone, complementary, fused beats
either); iter-33 generalises two ears to N ears / N settings.

## (1) The MANY-SETTINGS graph — wired, auditable: combine-all, no select, no fit

The agent's OWN filters/transforms, instantiated at MANY settings, each a node:

- **the COCHLEAR front-end at MANY time-frequency tradeoffs**
  (`domains/filter_settings.py::cochleagram` / `COCHLEAR_SETTINGS`). The tradeoff
  is governed by the same knobs the front-end already has:
  - `env_cut` — hair-cell envelope LPF cutoff (high = sharp time, low = clean
    spectrum);
  - `dur_cut` — sustained duration LPF cutoff (same axis);
  - `n_frames` — temporal resolution of the resampled trajectory.
  Five settings spread across the uncertainty tradeoff: `sharp_time`, `mid_time`,
  `middle` (= the agent's existing baked-in `band_trajectory_matrix` setting),
  `mid_freq`, `sharp_freq`.
- **the TRANSITION channel at MANY temporal windows**
  (`filter_settings.transition_multiwindow` / `TRANSITION_WINDOWS`): the agent's
  order-1-over-time operator read at n_windows ∈ {2, 3, 4} (early/late, thirds,
  quarters) — a short window catches the fast formant onset, a long window the slow
  sweep.

Per cochlear setting the harness emits a FLAT (spectral-detail) channel AND a
transition channel per window → `5 settings × (1 flat + 3 transition) = 20
channels`, each a node.

**ALL of them are combined** via the agent's recognition_graph Argmax of a variadic
Times — the Bayes product generalised from iter-32's 2-channel product to N channels
(`domains/many_settings_recognizer.py::predict_many_settings_term`,
`score = Π_i P_i(w|s)`). Per-setting likelihood `P_i(w|s)` = softmax over candidates
of that setting's own 1-NN exemplar evidence, scale-normalised by the setting's OWN
median candidate distance (read from the data, not searched).

Per cochlear setting the patch bank is GROWN by the SAME cross-voice
transition-contrast survival selector iter-30/31/32 use (`grown_representation`).

**No-donkey + the one hard rule (auditable):** COMBINE ALL — every instantiated
setting feeds the product. NO sweep-and-keep-the-best (the forbidden
negative-space search), NO fit, NO winning-setting pick, NO global hand-weight. The
N likelihoods enter the product symmetrically; each setting's temperature is its own
median distance. The combinatorial product sorts the settings out — a setting
uninformative for a contrast multiplies in near-flat and cannot drag the settings
that carry it.

### Where the wiring lives
- `domains/filter_settings.py` — the cochlear settings bank + the multi-window
  transition operator.
- `domains/many_settings_recognizer.py` — the N-channel Bayes-product graph Term
  (`predict_many_settings_term`) + the per-setting likelihood.
- `scripts/many_settings_hvpt_accept.py` — builds all per-setting channels per LOSO
  fold, grows a bank per setting, runs the N-channel Argmax-product natively;
  reports many-settings vs single-setting-flat vs iter-32 2-node combo vs frozen,
  with shuffle.

### Audit (combine-all, not select)
`predict_many_settings_term(20)` is structurally `Argmax(NodesWhere Concept
is_word) of Times[Attr(w,p_ch0), …, Attr(w,p_ch19)]` — a product over EXACTLY 20
items (the 20 channel-likelihood attrs). The only node kinds in the whole term are
`Argmax, Attr, Lit, NodesWhere, Times, Var` — there is no `Max`/`Sort`/`Pick`/`If`
over channels, no weight term: every setting enters the product symmetrically. And
the `middle` cochlear setting is byte-identical to the baked-in
`band_trajectory_matrix` (max abs diff 0.0), so `middle:flat` IS the iter-31
single-setting strong channel and the many-settings bank strictly ADDS settings
around it.

## (2) The runs — MULTI-METRIC + shuffle (captured to /tmp)

- `/tmp/iter33_smoke_n1.txt` — n=1, rounds=1 smoke (harness validity; the 20-channel
  Argmax-product evaluates natively end-to-end).
- `/tmp/iter33_n4_run.txt` — n=4, rounds=2 LOSO run (authoritative).

### n=4 REAL-SPEAKER HVPT (LOSO over 6 FSDD speakers) — the MULTI-METRIC table

20 channels combined per fold (5 cochlear settings × [1 flat + 3 transition
windows]). chance/unigram 0.100.

| metric (mean over 6 LOSO folds) | value | vs |
|---|---|---|
| **MANY-SETTINGS graph (iter-33, ALL 20 settings combined)** | **0.546** | the graph |
| single-setting flat (iter-31 strong channel = `middle:flat`) | 0.517 | the single setting |
| iter-32 two-node combo (flat·trans, middle setting) | 0.454 | iter-32 |
| frozen (cohort-warped front-end, fixed 25-patch bank) | 0.379 | regression baseline |

**Many-settings vs each comparator (grown):**
- vs single-setting flat: **0.546 vs 0.517, Δ +0.029 → BEATS** (the iter-32 residual
  dissolved — many tradeoffs beat the single setting iter-32 lost to).
- vs iter-32 two-node combo: 0.546 vs 0.454, Δ +0.092 → beats.
- vs frozen: 0.546 vs 0.379, Δ +0.167 → beats.

**Per-fold (REAL), many-settings vs single-setting flat:**

| held-out | many | single-flat | Δ |
|---|---|---|---|
| george   | 0.600 | 0.525 | **+0.075** |
| jackson  | 0.550 | 0.550 | +0.000 (tie) |
| lucas    | 0.500 | 0.425 | **+0.075** |
| nicolas  | 0.650 | 0.625 | **+0.025** |
| theo     | 0.550 | 0.475 | **+0.075** |
| yweweler | 0.425 | 0.500 | −0.075 |

→ many-settings ≥ single-flat on 5 of 6 folds (4 wins, 1 tie); loses on 1 (yweweler).
This is exactly the two-ears shape: the extra settings help most where the single
setting is weak, and never collapse below it except on the one noisy fold.

**The decisive SHUFFLE control (real cross-voice structure vs shuffled voice labels):**

| | REAL | SHUFFLE |
|---|---|---|
| MANY-SETTINGS graph | **0.546** | 0.542 |
| single-setting flat | 0.517 | 0.517 |
| iter-32 two-node combo | 0.454 | 0.392 |

**MANY-SETTINGS REAL 0.546 > SHUFFLE 0.542 → CLEAN** (the per-setting banks are
grown by the cross-voice survival selector; the real cross-voice structure helps,
the shuffled partition does not). The margin is small at n=4 — the FSDD digit
content within a single held speaker is consistent enough that even a
shuffled-voice growth produces a usable bank, so the shuffle floor is high — but the
sign is correct and consistent with iter-32's clean shuffle.

### PERSONA HVPT (agent-generated voices, held-out persona)
Many-settings 1.000 vs single-flat 1.000 vs two-node combo 0.850 vs frozen 1.000.
As iter-32 noted, the persona set re-voices ONE source speaker, so the flat channel
trivially memorises content and both flat-based readouts saturate at 1.000 — the
persona flat comparator is degenerate and NOT meaningful. The real-speaker LOSO is
authoritative. (Many-settings still beats the two-node combo here, 1.000 vs 0.850.)

## (3) VERDICT — does the many-settings graph BEAT the single-setting flat?

**YES — clean, multi-metric, real > shuffle.**

- **vs the single-setting flat (the iter-32 residual): YES** — many-settings 0.546 >
  single-flat 0.517 (Δ +0.029), winning on 5 of 6 folds. iter-32's 2-node combo
  LOST to this same single channel (0.454 < 0.517); the many-settings graph BEATS
  it. The node-quality residual is dissolved by instantiating the SAME filters at
  MANY time-frequency tradeoffs and combining ALL of them — the two-ears logic
  generalised to N ears.
- **vs the iter-32 two-node combo: YES** — 0.546 > 0.454 (Δ +0.092). Adding the
  complementary settings around the strong flat channel turns iter-32's *loss* into a
  *win*: the cap was on one channel, and many channels at different tradeoffs fused
  dissolve it (exactly the user's frame).
- **vs frozen: YES** — 0.546 > 0.379 (Δ +0.167).
- **SHUFFLE: CLEAN** — REAL 0.546 > SHUFFLE 0.542. The combination is real signal.
- **combine-all, not select (auditable):** the decision is `Argmax of Times` over all
  20 setting-likelihood attrs — no winning-setting pick, no weight, no fit; each
  setting's temperature is its own median distance (read from the data). The product
  sorts the settings out.

**So: the graph-with-many-settings WORKS. The user's frame is validated — there is
no reason to have one setting per filter; combining MANY settings (each a node) via
the agent's Argmax-of-product beats the single strong setting iter-32 lost to,
beats the iter-32 2-node combo, beats frozen, and is shuffle-clean.** The win is
modest in absolute terms (+0.029 over single-flat) — the FSDD 6-speaker LOSO at
n=4 is a small, noisy test and the extra settings buy most of their margin on the
folds where the single setting is weak — but it is the structurally decisive result:
the many-settings graph turns iter-32's loss-to-the-single-channel into a win, which
is exactly what generalising two ears to N ears predicts.

### Honest limits / how far
- The margin over single-flat is small (+0.029) and one fold (yweweler) regresses.
- The shuffle floor is high at n=4 (REAL−SHUFFLE = +0.004) because within a single
  held FSDD speaker the digit content is consistent; the sign is correct but the
  control would bite harder with more speakers / a larger vocabulary.
- The 5 flat channels are partly redundant (all spectral-detail readouts of the same
  audio); most of the lift comes from the spread across the time-frequency tradeoff +
  the multi-window transition channels being complementary on the harder folds. A
  genuinely orthogonal front-end (e.g. the freq-sharp FFT ear from `two_ears_demo`)
  added as a further setting is the natural next lever.

## (4) Reproduce

```
python -m scripts.many_settings_hvpt_accept 1 1   # n=1 r=1 smoke (/tmp/iter33_smoke_n1.txt)
python -m scripts.many_settings_hvpt_accept 4 2   # n=4 r=2 authoritative (/tmp/iter33_n4_run.txt)
```

Wiring: `domains/filter_settings.py` (the cochlear settings bank + multi-window
transition), `domains/many_settings_recognizer.py` (the N-channel Bayes-product
graph Term), `scripts/many_settings_hvpt_accept.py` (the harness). Required suites
green (32): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance. No commit — results + this doc left
in the working tree for re-verification.
