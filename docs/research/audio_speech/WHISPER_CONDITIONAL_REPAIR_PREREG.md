# Preregistration: graph-authored conditional Whisper repair

Status: frozen after the unconditional replication rejection and before
decoding or inspecting any recording with index 40--49.

Date: 2026-07-28 (Australia/Melbourne)

## Fixed causal target

The preceding autonomous study selected
`encoder.blocks.1.self_attention.head.3`. On untouched indices 30--39 its
unconditional ablation reduced null false transcripts from 15 to 5 and beat
the fixed control (14), but was rejected because it reduced exact speech
accuracy from 35 to 33 and increased wrong speech from 23 to 26.

The component identity and its random control
(`encoder.blocks.0.self_attention.head.0`) are now frozen. This study may not
search another component.

## Conditional mechanism

Whisper already publishes `no_speech_prob` in its decoded segments. The host
may mechanically expose the maximum segment value from an unmodified first
pass. It may not choose a threshold or decide whether to rerun.

The Rust graph must test, in fixed order, thresholds:

`0.40, 0.50, 0.60, 0.70, 0.80`

For a graph-requested threshold, the host performs a second pass with the
frozen head ablated exactly when:

- the first-pass normalized transcript is non-empty; and
- the exposed `no_speech_prob` is greater than or equal to the threshold.

Otherwise the unmodified first-pass output is retained. This is a
no-retraining, two-pass inference patch. It uses a published internal signal
and the already graph-discovered causal component.

## Calibration and graph choice

Calibration uses a deterministic balanced 60-speech/60-phase-null sample from
indices 10--19. It is not a confirmatory fold.

For each threshold, raw counts include speech hallucinations removed/added,
null false transcripts removed/added, and correct speech controls lost. The
graph computes:

`removed speech + removed null - added speech - added null - correct lost`

A gate is admissible only with positive utility, zero added speech
hallucinations, zero added null hallucinations, and zero lost correct speech.
The graph authors the maximum-utility admissible threshold. No fitted model,
gradient, learned probe, or weight update is allowed.

## Final untouched fold

Indices 40--49 are decoded once after the graph commits its threshold. The
same gate is applied to the discovered head and the previously graph-authored
control head.

The graph-native success gates are unchanged:

- at least 50% reduction in wrong non-empty speech transcripts;
- at least 50% reduction in null false transcripts;
- less than one percentage point exact-speech accuracy loss;
- fewer combined failures than the gated random-head control;
- byte-identical weights and no allocated gradients.

All gates will be reported. If no calibration threshold is admissible, or if
the final fold rejects it, the result remains a causal diagnosis and partial
null repair rather than a general repair.
