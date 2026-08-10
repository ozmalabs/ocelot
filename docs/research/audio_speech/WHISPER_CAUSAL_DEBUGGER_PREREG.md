# Preregistration: Jabberwock causally diagnoses and repairs Whisper

Status: frozen before installing an instrumentable Whisper runtime, inspecting
per-head outcomes, or running any intervention.

Date: 2026-07-28 (Australia/Melbourne)

## Claim under test

A graph-native cognition engine can treat a published neural network as an
experimental object, autonomously select causal interventions, discover a
component-level explanation of a real failure, and author an inference-time
repair without optimizing or changing model weights.

This is deliberately stronger than the preceding encoder-grounding result.
That result supplies a reproducible phenotype and demonstrates additive
acoustic evidence. It does not establish autonomous causal reverse engineering
of Whisper.

## Hard architectural boundary

The instrument adapter may:

- enumerate Whisper's published module hierarchy;
- expose activation summaries and component metadata;
- enact exactly the intervention named by the graph;
- run inference and stamp measured outcomes;
- compile a graph-authored patch into a runtime hook.

The adapter may not rank components, choose an intervention, update a causal
hypothesis, choose a repair, or decide whether the repair succeeded. Those
decisions must be Terms and Rules loaded into the Rust substrate.

No optimizer, gradient, backpropagation, fine-tuning, trained classifier,
sparse autoencoder, or weight update is allowed. Forward passes, ablations,
activation replacement, deterministic descriptive statistics, and
graph-native causal contrasts are allowed.

## Model and failure phenotype

- Model: official OpenAI Whisper `base.en`, published pretrained weights,
  eval mode on CPU.
- Primary phenotype: fluent non-reference output on isolated FSDD digits.
- Null phenotype: non-empty output on same-duration silence or deterministic
  phase-scrambled audio.
- Preservation controls: isolated clips that baseline Whisper transcribes
  exactly.
- Text normalization and outcome definitions are inherited unchanged from
  `WHISPER_GROUNDING_PREREG.md`.

The instrumentable PyTorch model is separate from the prior faster-whisper
int8 runtime. Its baseline phenotype must therefore be reproduced before any
causal claim is evaluated.

## Frozen data split

The six-speaker FSDD Git corpus remains pinned at commit
`26eb9aaf76e81b692f806f9140c2d2777410d7a1`.

- Discovery pool: recording indices 0–9. These were used by the preceding
  study and are not confirmatory here.
- Prospective validation pool: indices 20–29. These recordings have not been
  decoded or inspected in the preceding study.
- Indices 10–19 may be used only to derive a conditional, non-learned runtime
  gate after a causal component has been selected.
- Indices 30–49 remain untouched for a later external replication rung.

The discovery intervention panel is assembled mechanically from baseline
phenotypes: up to 12 hallucinating speech clips, 12 correct speech clips, and
12 null clips, balanced across references and speakers where available. The
graph never sees reference labels when choosing which component to test; they
are used only by the mechanical outcome meter.

## Intervention grammar

The first rung is hierarchical and finite:

1. coarse interventions over each encoder and decoder block submodule
   (`self_attention`, `cross_attention` where present, and `mlp`);
2. head interventions only inside coarse components whose graph-measured
   causal utility is positive;
3. restoration controls for every selected component;
4. a same-cardinality random-component control chosen from a fixed
   deterministic ordering, not from observed outcomes.

An ablation replaces only the named component contribution with zero while
leaving its residual path intact. A restoration run removes that hook and must
recover the baseline output.

## Graph-native investigation

Every inspectable component is a `PublishedNetComponent`. The graph maintains:

- `CausalDebuggingStudy`;
- `NetworkIntervention`;
- `InterventionOutcome`;
- `ComponentCausalHypothesis`;
- `RuntimeNetworkPatch`.

The graph chooses one untested intervention at a time. Coarse components are
tested before their heads. Outcome evidence records:

- hallucination count before and under intervention;
- correct-control count before and under intervention;
- null false-transcript count before and under intervention;
- restoration agreement;
- sample counts and provenance.

The causal utility is the reduction in speech and null hallucinations minus
the loss of correct controls, each represented as counts over the same panel.
No fitted coefficient is permitted. A component becomes a causal candidate
only if hallucinations decrease, correct-control loss is smaller than the
benefit, and restoration reproduces baseline behavior.

The graph authors a patch by `Argmax` over admitted causal candidates. Python
may enact only the component named by the resulting `RuntimeNetworkPatch`.

## Primary gates

- G1 phenotype: official Whisper produces at least one fluent wrong isolated
  transcript and at least one null false transcript in the discovery pool.
- G2 autonomy: source and AST audits show no Python component ranking,
  experiment selection, causal admission, or patch choice.
- G3 causal discovery: at least one component intervention reduces the
  combined failure count, has positive graph-computed causal utility, and
  passes its restoration control.
- G4 prediction: the graph-authored component ranks above the deterministic
  random control on prospective validation.
- G5 repair: on prospective indices 20–29, the graph-authored no-weight-change
  patch reduces non-empty wrong speech transcripts by at least 50% and null
  false transcripts by at least 50%.
- G6 preservation: prospective exact-speech accuracy degrades by less than one
  percentage point. If no discovered unconditional patch meets this gate, the
  honest result is a diagnosis without a safe global repair.
- G7 no retraining: serialized weights are byte-identical before and after the
  study, and no gradient is allocated.
- G8 mechanistic specificity: removing the patch restores the failure and a
  same-cardinality random intervention does not match its joint repair and
  preservation score.

All gates and negative results will be reported. Failure of G6 must not be
hidden behind selective coverage.

## Related work firewall

Jabberwock is not seeded with the head identities, layer locations, or
intervention results reported by Calm-Whisper or subsequent activation
steering work. Those papers are used only for post-hoc comparison after the
graph has committed its causal model.
