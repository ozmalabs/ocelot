# When the language prior outruns the ear

## A preregistered, graph-native acoustic guard for Whisper on isolated speech

### Abstract

We reproduced a historical failure found by the Jabberwock cognition engine:
Whisper can emit fluent but wrong text when asked to transcribe very short,
decontextualized speech. On a hash-pinned three-speaker release of the Free
Spoken Digit Dataset (FSDD; n=300), faster-whisper `base.en` produced 127
non-empty wrong transcripts (42.3%) and seven omissions (2.3%). It also emitted
text for 43 of 60 silence or phase-scrambled controls (71.7%).

We tested a preregistered acoustic grounding guard. Whisper's free decoder
remained the proposal generator. Its final encoder supplied a mean-pooled
acoustic vector. Digit prototypes and class-specific admission radii were
derived only from training speakers. A Rust-executed graph Program—not Python
control flow—selected the nearest prototype and accepted, corrected, or
abstained according to whether the candidate lay inside its training-support
radius. The guard reduced non-empty wrong transcripts to 30/300 (10.0%;
76.4% relative reduction), increased exact accuracy from 55.3% to 70.7%, and
reduced null false transcripts to 7/60 (11.7%). A separately pinned
six-speaker historical corpus replicated the pattern: wrong transcripts fell
from 217/600 (36.2%) to 50/600 (8.3%), and exact accuracy rose from 61.7% to
86.3%.

The intervention did not pass every preregistered gate. Correction precision
was 70.0% and 77.0%, below the 90% target. The result supports encoder
grounding as a useful selective-oversight mechanism, but not as an unrestricted
automatic rewrite policy. We also invalidate an earlier project result:
CTranslate2 prompt scores had been misread as candidate-token likelihoods, and
an object-identity embedding cache could reuse evidence across clips. Both
paths are repaired and regression-tested.

### 1. Background

Whisper was trained as a sequence-to-sequence model over large, weakly
supervised audio-text data. Its decoder necessarily combines acoustic evidence
with a learned token and language prior; the original Whisper paper explicitly
describes multitask sequence prediction rather than an isolated-word
classifier [1]. The official transcription implementation also exposes
fallback and no-speech decisions involving average log probability and a
no-speech probability [2]. Faster-whisper adds VAD and hallucination-related
controls, but those controls do not turn a free decoder into a calibrated
closed-vocabulary acoustic classifier [3].

The failure is not unique to this project. Controlled work has induced Whisper
hallucinations with non-speech audio [4], and recent mitigation work likewise
uses internal model evidence to identify unreliable decoding [5]. Our question
is narrower: can acoustic evidence already present in Whisper's encoder ground
or refuse its decoder proposal on very short, closed-vocabulary speech?

This operational study calls every non-empty, non-reference transcript a
“hallucination/substitution.” That definition is deliberately broad and
task-specific. It does not claim that all ASR substitutions share one cause or
have the same clinical significance.

### 2. Historical recovery and validity corrections

The project commit `37036af3ca` reported poor Whisper recognition of isolated
content words and proposed that the contextual plaintext prior dominated when
context was removed. The qualitative diagnosis survives replication, but two
later implementation details did not survive audit.

#### 2.1 The “forced-decode” score did not score the candidate

Commit `fcc4262a65` appended a candidate word to a CTranslate2 generation
prompt and requested `return_scores=True`. CTranslate2 treats prompt tokens as
initial context. They are not generated and the returned sequence score is for
the continuation *after* the prompt. Direct inspection produced prompts such
as `one`, followed by a generated continuation equivalent to `THE THE THE`;
the recorded scalar therefore could not be interpreted as
`log P(one | audio)`. The tokenizer also inserted special tokens around the
word while the implementation manually prepended another start/task prompt.

The old API now raises `InvalidForcedDecodeScoring`. The historical gate exits
with a retirement explanation instead of reproducing a misleading milestone.

#### 2.2 The embedding cache was keyed by object identity

The encoder adapter stored embeddings under `id(audio)`. Once a NumPy array is
reclaimed, CPython may reuse that integer identity for a different array. A
long evaluation could therefore return an earlier clip's embedding for a new
clip. The replacement key hashes the contiguous float32 shape, dtype, and
content with BLAKE2b and uses a bounded LRU. Tests verify same-content reuse,
different-content separation, and eviction.

Earlier results that depended on either path should not be treated as valid
evidence until independently rerun.

### 3. Preregistered method

The protocol was committed as `ae452fc1f1` before confirmatory inference. Its
full hypotheses and definitions are in `WHISPER_GROUNDING_PREREG.md`.

#### 3.1 Data provenance and an observed protocol deviation

The primary archive is the official FSDD v1.0.8 Zenodo artifact [6], MD5
`54f48186ecb1d5ac4e971143086d529b`. After download and before inference, we
found that it contains 1,500 clips from three speakers, not the six speakers
assumed by the preregistration and by old project documents. The deviation was
committed separately before evaluation (`c221e50297`). The primary test
therefore uses indices 0–9 for ten digits and three speakers (n=300), with
three leave-one-speaker-out folds.

To reproduce the old project's actual six-speaker venue, we separately pinned
the official GitHub repository [7] at commit
`26eb9aaf76e81b692f806f9140c2d2777410d7a1`, archive SHA-256
`beaca4fb849cad13103b2cffba913b3d7fdb5f15222da4ddd07187b3c38a757a`.
That replication uses the same indices and six leave-one-speaker-out folds
(n=600). Results are not pooled.

#### 3.2 Baseline and outcome definitions

Each clip was resampled to mono float32 at 16 kHz and independently decoded by
faster-whisper 1.2.1 `base.en`, CPU int8, English, beam size 5. Lowercase exact
normalization removed punctuation and mapped a digit glyph to its English
word. There was no fuzzy matching.

- Correct: normalized output equals the one-word reference.
- Omission: normalized output is empty.
- Hallucination/substitution: normalized output is non-empty and unequal to
  the reference.

#### 3.3 Acoustic geometry

For each fold, the borrowed model produced a mean-pooled, L2-normalized final
encoder vector \(z\) for each clip. For class \(k\), normalized training
vectors formed the normalized centroid

\[
c_k = \frac{\sum_i z_{ki}}{\left\|\sum_i z_{ki}\right\|_2}.
\]

Its admission radius was the farthest support-fold member under cosine
distance:

\[
r_k = \max_i \left(1 - z_{ki}^{\mathsf T}c_k\right).
\]

No held-out output selected a feature, threshold, radius, or class.

For test vector \(z\), the adapter laid all ten candidates into the graph with
\(d_k=1-z^{\mathsf T}c_k\), \(r_k\), support count, label, and decoder-match
evidence. The graph Program computed

\[
k^\* = \arg\min_k d_k.
\]

It admitted the proposal only when the free decoder was non-empty and
\(d_{k^\*}\le r_{k^\*}\). Agreement produced `accept`; disagreement produced
`correct`; failure produced `abstain`. Empty decoder output always produced
`abstain`. Every result retained its winner distance, radius, fold, model, and
decision provenance.

This division is architectural: Python mechanically extracts an external
feature and lays graph evidence. Rust evaluates the graph-native `Argmin`,
`Lte`, and Rules that decide identity and action.

#### 3.4 Null controls

For index 0 of every digit/speaker pair, we evaluated a same-duration zero
signal and a deterministic phase-scrambled signal preserving Fourier
magnitude and duration. Any non-empty output was a false transcript. The
phase seed was derived from the source path.

### 4. Results

#### 4.1 Primary: official Zenodo v1.0.8

| Metric | Whisper baseline | Graph guard |
|---|---:|---:|
| Exact accuracy, all 300 | 166/300 (55.3%) | 212/300 (70.7%) |
| Omission / abstention | 7/300 (2.3%) | 58/300 (19.3%) |
| Non-empty wrong transcript | 127/300 (42.3%) | 30/300 (10.0%) |
| Coverage | 293/300 (97.7%) | 242/300 (80.7%) |
| Accuracy among emitted outputs | 166/293 (56.7%) | 212/242 (87.6%) |
| False transcript on nulls | 43/60 (71.7%) | 7/60 (11.7%) |
| Precision of graph corrections | — | 70/100 (70.0%) |

The relative reduction in non-empty wrong transcripts was 76.4%. The paired
correctness table contained 70 guard-only correct cases and 24
baseline-only correct cases (exact two-sided McNemar/binomial
\(p=2.20\times10^{-6}\)).

Speaker effects were substantial. Baseline/guard exact counts were 71/87 for
Jackson, 30/46 for Nicolas, and 65/79 for Theo. This reinforces the small
speaker sample limitation.

#### 4.2 Six-speaker historical replication

| Metric | Whisper baseline | Graph guard |
|---|---:|---:|
| Exact accuracy, all 600 | 370/600 (61.7%) | 518/600 (86.3%) |
| Omission / abstention | 13/600 (2.2%) | 32/600 (5.3%) |
| Non-empty wrong transcript | 217/600 (36.2%) | 50/600 (8.3%) |
| Coverage | 587/600 (97.8%) | 568/600 (94.7%) |
| Accuracy among emitted outputs | 370/587 (63.0%) | 518/568 (91.2%) |
| False transcript on nulls | 89/120 (74.2%) | 37/120 (30.8%) |
| Precision of graph corrections | — | 167/217 (77.0%) |

The relative reduction in non-empty wrong transcripts was 77.0%. There were
167 guard-only correct cases and 19 baseline-only correct cases
(\(p=9.63\times10^{-31}\)).

Errors were often fluent rather than empty. Examples include reference
`three` decoded as “Good to see you,” “Thank you very much,” or “Good
afternoon”; `zero` decoded as “Needle,” “Vito,” or “Little”; and silence
decoded repeatedly as “You.” These examples make the practical distinction
between decoder plausibility and acoustic grounding visible.

#### 4.3 Synthetic check

Only `danny` of the four frozen post-pilot Piper names was locally available.
Across two pitch settings and all ten digits, baseline Whisper produced
13/20 exact outputs and 7/20 non-empty wrong outputs, including `one` as
“Bye” or “Fine,” `two` as “Ew,” and `five` as “Bye.” This is qualitative
support only and does not substitute for either real-speech evaluation.

#### 4.4 Preregistered hypothesis disposition

| Hypothesis | Primary | Six-speaker |
|---|---:|---:|
| H1: at least one non-empty wrong transcript | Pass | Pass |
| H2: at least 50% reduction | Pass (76.4%) | Pass (77.0%) |
| H3: correction precision at least 90% | **Fail (70.0%)** | **Fail (77.0%)** |
| H4: null false transcripts do not increase | Pass | Pass |
| H5: coverage at least 30% and selective accuracy improves | Pass | Pass |
| H6: architectural and regression gates | Pass (8/8 tests) | Same implementation |

The study therefore does **not** pass all primary hypotheses.

### 5. Interpretation

Three observations jointly support the proposed mechanism.

First, the free decoder generated grammatical text unrelated to the one-word
task. Second, the same decoder frequently generated text for physically null
or speech-destroyed controls. Third, a decision based on its own encoder
geometry removed about three quarters of non-empty wrong outputs in two
corpora. The parsimonious interpretation is not that Whisper “has no acoustic
knowledge.” Its encoder retains useful word identity, while a generative
decoder can turn uncertain evidence into a plausible token sequence.

The guard is also diagnostically incomplete. A maximum support radius encloses
every training exemplar, including outliers. It models class inclusion but
does not model local ambiguity between classes, null exposure, or the
probability that a rewrite is correct. The failed 90% correction-precision
gate is exactly the consequence one would expect from that broad admission
geometry.

For the cognition engine, the safe interpretation is System 1/System 2
oversight:

1. the decoder supplies a fast learned default;
2. encoder evidence supplies bottom-up grounding;
3. agreement inside known support can be accepted rapidly;
4. disagreement or out-of-support evidence should raise uncertainty and
   support abstention/escalation;
5. a correction proposal should not become an unrestricted autonomous rewrite
   until a separately calibrated gate reaches the required precision.

### 6. Limitations and next experiment

- This is a ten-class isolated-digit task, not open-vocabulary ASR.
- FSDD is small, clean, 8 kHz, English-only, and demographically narrow.
- The primary release has only three speakers; the six-speaker analysis is a
  later Git revision, not the preregistered Zenodo artifact.
- Whisper's `base.en` CPU-int8 implementation and exact defaults are part of
  the measured system; other sizes and decoders may differ.
- Mean pooling discards temporal structure.
- The maximum-support radius is sensitive to training outliers.
- Null signals expose decoder behavior but are not a naturalistic noise
  distribution.

The next fix should be prospectively preregistered, not tuned on these rows:
split training speakers into prototype and calibration roles; calibrate an
encoder margin or nonconformity score against held acoustic and null examples;
require agreement with an independently learned Jabberwock acoustic channel
for automatic correction; and route residual disagreement to graph-native
System 2 escalation. Correction precision, null false-transcript rate, and
open-vocabulary abstention must remain separate endpoints.

### 7. Reproduction

Machine-readable outputs:

- `results/whisper_grounding_zenodo_v1.0.8.json`
- `results/whisper_grounding_github_26eb9aaf.json`
- `results/whisper_grounding_piper.json`

Core implementation:

- `domains/whisper_grounding_guard.py`
- `seeds/whisper_grounding_guard.json`
- `domains/whisper_teacher_adapter.py`
- `scripts/whisper_grounding_measure.py`
- `tests/test_whisper_grounding_guard_migrated.py`

Run:

```bash
PYTHONPATH=runners/dsl/python:. ../../.venv/bin/python \
  scripts/whisper_grounding_measure.py \
  --data-dir data/fsdd \
  --dataset-kind zenodo-v1.0.8 \
  --output results/whisper_grounding_zenodo_v1.0.8.json
```

### References

1. Radford et al. [Robust Speech Recognition via Large-Scale Weak
   Supervision](https://arxiv.org/abs/2212.04356), 2022.
2. OpenAI. [Whisper transcription implementation](https://github.com/openai/whisper/blob/main/whisper/transcribe.py).
3. SYSTRAN. [faster-whisper transcription implementation](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py).
4. Barański et al. [Investigation of Whisper ASR Hallucinations Induced by
   Non-Speech Audio](https://arxiv.org/abs/2501.11378), 2025.
5. [Calm-Whisper: Reduce Whisper Hallucination On Non-Speech by Calibrating
   Internal Learning](https://arxiv.org/abs/2505.12969), 2025.
6. Jackson et al. [Free Spoken Digit Dataset v1.0.8](https://zenodo.org/records/1342401), 2018.
7. Jackson et al. [Free Spoken Digit Dataset repository](https://github.com/Jakobovski/free-spoken-digit-dataset).
