# Preregistration: encoder-grounded oversight of Whisper on isolated words

Status: frozen before the confirmatory FSDD download and evaluation.

Date frozen: 2026-07-28 (Australia/Melbourne)

## Question

Can a graph-native, acoustically grounded admission rule reduce fluent wrong
transcripts from Whisper on very short, decontextualized speech without
pretending that abstentions are successful recognition?

This is a correction and extension of the Jabberwock's historical Whisper
investigation. Commit `37036af3ca` reported that Whisper performed poorly on
isolated content words and attributed the failure to a contextual plaintext
prior dominating weak acoustic evidence. Commit `fcc4262a65` subsequently
claimed to improve the teacher with closed-vocabulary "forced decoding".
Inspection before this preregistration found that the latter implementation is
invalid: candidate tokens were supplied to CTranslate2 as an *unscored prompt*,
and the returned score belongs to the continuation generated after that
prompt. The tokenizer also inserted its own special tokens, duplicating parts
of the manually constructed prompt. Those historical forced-decode results
will not be used as evidence.

Inspection also found that encoder embeddings were cached by `id(audio)`.
Python can reuse an object's identity after reclamation, allowing a new clip
to receive an unrelated old embedding. The cache will be replaced with a
bounded, content-addressed cache before measurement.

## Frozen method

### Model and data

- Model: `faster-whisper` `base.en`, CPU `int8`, language `en`, beam size 5.
- Primary dataset: Free Spoken Digit Dataset v1.0.8, pinned to the official
  Zenodo archive with MD5 `54f48186ecb1d5ac4e971143086d529b`.
- Task vocabulary: `zero` through `nine`.
- Evaluation set: recordings numbered 0 through 9 for every available digit
  and all six FSDD speakers (expected n=600).
- Evaluation: leave one speaker out. In each of six folds, five speakers form
  the support set and the held-out speaker is used only for evaluation.
- Audio is converted mechanically to mono float32 at 16 kHz before inference.

The archive contents and package/model versions will be recorded in the result
artifact. Missing or malformed files will be listed and excluded; no example
will be excluded because of its prediction.

### Baseline transcript and outcome definitions

Whisper free-decodes each clip independently. Its text is lower-cased and
stripped of punctuation. A digit glyph is mapped to its English word. No
fuzzy matching is used.

- correct: the normalized output is exactly the reference digit word;
- omission: normalized output is empty;
- hallucination/substitution: any non-empty output that is not exactly the
  reference digit word.

The last category deliberately uses the broad operational meaning relevant to
this experiment. It does not claim that every ASR substitution has the same
clinical or mechanistic origin.

### Encoder-grounded oversight

The borrowed Whisper encoder is an external sensor. For each fold:

1. L2-normalize one mean-pooled final-layer encoder vector per support clip.
2. L2-normalize the mean support vector for each digit to obtain its prototype.
3. Set a digit's admission radius to the maximum cosine distance between that
   prototype and any of its support examples. This radius is derived only from
   the support fold; it is not tuned on held-out outputs.
4. For a held-out clip, mechanically lay one graph candidate per digit with its
   cosine distance, support radius, and whether it matches the normalized free
   transcript.
5. A graph Program selects the minimum-distance candidate and emits only when:
   the baseline was non-empty and the winner lies within its own support
   radius. It records `accept` when the winner agrees with Whisper, `correct`
   when it disagrees, and `abstain` otherwise.

The adapter may compute encoder vectors and cosine distances because those are
external feature extraction. Candidate selection, admission, correction, and
abstention must execute as graph Terms/Rules in the Rust substrate. The guard
never invents a transcript when Whisper emitted nothing.

### Null controls

For recording index 0 of every speaker/digit pair (expected n=60), construct:

- a same-duration all-zero signal;
- a deterministic phase-scrambled version preserving the clip's Fourier
  magnitude and duration.

The random phase seed is derived from the relative file path. Null inputs have
no digit reference; any non-empty transcript is a false transcript. The guard
will be evaluated using the fold that holds out the corresponding speaker.

### Primary predictions

All are tested once on the frozen evaluation.

- H1 — reproduction: Whisper produces at least one non-empty wrong transcript
  on held-out isolated speech.
- H2 — mitigation: among speech clips, the guard reduces the number of
  non-empty wrong transcripts by at least 50% relative to baseline.
- H3 — correction precision: at least 90% of outputs changed by the guard are
  changed to the reference word.
- H4 — null safety: the guard does not increase the number of non-empty
  transcripts on null inputs.
- H5 — non-trivial selectivity: coverage is at least 30%, and the exact
  accuracy among emitted guarded outputs exceeds exact accuracy among
  non-empty baseline outputs.
- H6 — architectural validity: regression tests demonstrate content-addressed
  caching, rejection of the invalid forced-score API, graph-native selection
  and admission, and abstention on an empty baseline or an out-of-radius
  candidate.

Failure of any prediction is reported as such. No threshold or feature will be
changed after observing confirmatory results.

### Statistics and reporting

The report will include counts and Wilson 95% intervals for exact accuracy,
hallucination rate, omission rate, coverage, selective accuracy, correction
precision, and null false-transcript rate. Baseline-versus-guard changes will
also be reported as a paired 2x2 table and an exact two-sided McNemar/binomial
test over discordant correctness outcomes.

Omissions and abstentions remain visible. The headline will not use an
accuracy denominator that silently removes them.

## Secondary historical replication

The original Piper setup is retained only as a qualitative, synthetic
replication. A fresh post-freeze set of cached voices not used in exploratory
pilots (`arctic`, `aru`, `semaine`, and `danny`, where available) will speak
all ten digit words at pitch settings 37 and 63. Synthesis failures are
reported. This secondary set cannot replace the independent FSDD result.

## Frozen implementation constraints

- No Python `min`, `max`, sorting, or conditional may choose the candidate
  label or final action in the inference adapter.
- Every inference records proposal, winning evidence, radius, action,
  provenance kind, model, and fold.
- The invalid `ForcedDecodeTeacher` path must fail loudly rather than return a
  scientifically misleading rank.
- Evaluation outputs are machine-readable and the publication draft must name
  both discovered historical validity bugs.
