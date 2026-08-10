# Jabberwock autonomously debugs Whisper

## Result in one sentence

Jabberwock reproduced a real Whisper `base.en` hallucination phenotype,
selected and executed 94 hierarchical causal interventions without an LLM
choosing components, discovered a head ablation that reduced held-out
non-speech hallucinations by 66.7% without changing weights, and then
correctly rejected it as a general repair when speech preservation failed.

A subsequent graph-authored conditional repair reduced final-fold null
hallucinations by 69.2% and improved speech accuracy, but a gated random-head
control matched its combined score. The final graph verdict was therefore
also rejection: the gate was useful; the selected head was not specifically
responsible for the conditional gain.

That negative control is the most important result. It prevents a plausible,
publishable-looking but false mechanistic claim.

## What was autonomous

The official OpenAI PyTorch `base.en` model was treated as an experimental
object. Python performed only laboratory mechanics:

- enumerate the published encoder/decoder/block/head hierarchy;
- install or remove the exact hook requested by the graph;
- run forward inference;
- stamp raw before/intervention/restoration counts;
- expose Whisper's published `no_speech_prob`;
- compile and enact the patch and gate already authored by the graph.

The Rust substrate graph performed:

- intervention selection;
- hierarchical expansion from coarse components to heads;
- causal-utility calculation;
- candidate admission and rejection;
- repair authorship;
- deterministic control selection;
- conditional-gate threshold selection;
- prospective success or failure judgment.

The mechanical adapter is AST-audited against Python `min`, `max`, `sorted`,
`argmin`, `argmax`, and `argsort` component choice. The experiment trace
records every tested component, including null and harmful results.

## Protocol chronology

The chronology matters because each document was committed before its
corresponding untouched fold was inspected.

1. `WHISPER_CAUSAL_DEBUGGER_PREREG.md`
   froze the initial no-retraining hierarchical study.
2. The initial balanced run on discovery indices 0--9 selected
   `decoder.blocks.2.self_attention.head.0`. Indices 20--29 rejected it:
   the head preserved exact speech but increased null false transcripts from
   19 to 28.
3. `WHISPER_CAUSAL_DEBUGGER_REPLICATION_PREREG.md`
   froze two corrections learned from that rejection:
   new-null errors became an explicit harm channel, and every
   positive-utility coarse attention parent opened its heads.
4. On calibration indices 10--19, Jabberwock ran 30 coarse interventions and
   64 head interventions. It authored
   `encoder.blocks.1.self_attention.head.3`.
5. Untouched indices 30--39 rejected the unconditional repair despite a
   strong null result.
6. `WHISPER_CONDITIONAL_REPAIR_PREREG.md`
   froze a five-threshold graph-native calibration over Whisper's published
   `no_speech_prob`, keeping both the discovered head and its graph-authored
   control fixed.
7. Untouched indices 40--49 rejected the strong component-specific claim
   because the control matched the conditional patch.

The earlier lexicographically concentrated smoke panel was diagnosed before
confirmatory interpretation and is not evidence. The runner now uses a fixed
Latin-square traversal over speaker and digit.

## Exact results

### Unconditional replication, indices 30--39

| Measure | Baseline | Discovered head | Random head |
|---|---:|---:|---:|
| Exact speech correct / 60 | 35 | 33 | 33 |
| Wrong non-empty speech / 60 | 23 | 26 | 24 |
| Non-empty phase-null / 60 | 15 | 5 | 14 |

The discovered encoder head reduced null hallucinations by 10/15 (66.7%) and
was much stronger than the random head on nulls. It failed preservation and
speech-repair gates. Weights remained byte-identical:

`f86fa385665591ec53bf953b7b7e1657bdd002fad929e987a7a4174f371a621e`

No parameter acquired a gradient.

### Conditional final fold, indices 40--49

The graph tested fixed thresholds `0.40, 0.50, 0.60, 0.70, 0.80`.
Threshold `0.40` was rejected during calibration because it introduced two
speech errors and lost two correct controls. Thresholds `0.50`, `0.60`, and
`0.70` tied at utility 9 with no measured harm; fixed experiment order chose
`0.50`.

| Measure | Baseline | Gated discovered head | Gated random head |
|---|---:|---:|---:|
| Exact speech correct / 60 | 37 | 39 | 38 |
| Wrong non-empty speech / 60 | 21 | 19 | 19 |
| Non-empty phase-null / 60 | 13 | 4 | 4 |

The conditional patch improved rather than degraded exact speech and reduced
null hallucinations by 9/13 (69.2%). It nevertheless failed two frozen gates:

- wrong-speech reduction was 9.5%, not 50%;
- its combined failure count equalled the gated random-head control.

The correct claim is therefore:

> Jabberwock autonomously localized causal Whisper components and discovered
> an effective training-free conditional null-hallucination mitigation, but
> falsified the claim that its selected head specifically caused the
> conditional improvement.

## What the model diagnosis says

The intervention landscape separates three phenomena:

1. **Global language disruption.** Many encoder or decoder block ablations
   remove hallucinations by also destroying correct speech.
2. **Component-local null sensitivity.** Individual heads such as encoder
   block 1 head 3 and decoder block 1 head 6 selectively suppress many
   calibration null outputs.
3. **An output-policy mismatch.** Whisper can assign a high internal
   `no_speech_prob` while still emitting fluent text. A conditional
   intervention driven by that signal generalizes, but its benefit is not
   specific to the selected head.

The third observation is consistent with a decoder that possesses usable
abstention evidence but does not always let that evidence dominate a
high-confidence language continuation. The experiment supports this as a
behavioral/causal inference; it does not establish a complete circuit.

## Relation to prior work

Whisper was introduced as a weakly supervised multitask model trained on
680,000 hours of audio, including an explicit no-speech prediction task:
[Radford et al., 2022](https://cdn.openai.com/papers/whisper.pdf).

[Calm-Whisper](https://arxiv.org/abs/2505.12969) also performs head-wise masks,
on Whisper large-v3, and reports that a small number of decoder heads account
for much of its non-speech hallucination. Its deployed improvement fine-tunes
those heads on non-speech data. Our intervention family is related, but our
model, head identities, data, graph-native selection, no-retraining
constraint, and negative-control conclusion differ.

[Zhang and Nanda, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html)
show that activation-patching localization can change substantially with
metrics and corruption choices. Our first rejection is a concrete example:
counting removed null errors without counting newly created null errors
selected a non-generalizing head.

[Aparin et al., 2026](https://arxiv.org/abs/2606.07473) use raw encoder
representations and learned sparse autoencoder latents to detect and steer
Whisper hallucinations. That is stronger mitigation on their datasets, but it
uses learned representation machinery excluded by this protocol.

[Silence-Conditional Output Suppression, 2026](https://analemma.ai/papers/714445d0-dc84-4ce4-b6df-6cdba8b7be7c/)
independently reports that thresholding Whisper's internal no-speech signal
can reduce hallucinations and that suppression policy, rather than decoder
head masking, drives the improvement. This closely matches our final control.
The mitigation itself is therefore not novel.

The publishable novelty to evaluate is the **method**: a graph-native
cognition engine independently inspects a published network, chooses
interventions, revises its causal design after falsification, authors a
no-retraining repair, and refuses its own attractive mechanistic explanation
when the preregistered control catches it.

## Reproduction

Use the project-local virtual environment and official model weights:

```bash
export PYTHONPATH="$PWD/runners/dsl/python:$PWD"

/home/matt/ozma/internal/research/.venv/bin/python \
  scripts/jabberwock_diagnoses_whisper.py \
  --data-dir /path/to/pinned-fsdd/recordings \
  --model-dir data/whisper-models \
  --output results/whisper_causal_debugger_replication.json \
  --discovery-quota 12 \
  --discovery-start 10 --discovery-end 20 \
  --validation-start 30 --validation-end 40 \
  --protocol WHISPER_CAUSAL_DEBUGGER_REPLICATION_PREREG.md

/home/matt/ozma/internal/research/.venv/bin/python \
  scripts/jabberwock_gates_whisper_repair.py \
  --data-dir /path/to/pinned-fsdd/recordings \
  --model-dir data/whisper-models \
  --output results/whisper_conditional_repair.json
```

Dataset revision:
`26eb9aaf76e81b692f806f9140c2d2777410d7a1`.

The official `base.en` model state hash before and after every study must be:
`f86fa385665591ec53bf953b7b7e1657bdd002fad929e987a7a4174f371a621e`.

## Strong next experiment

Do not tune another component on indices 40--49. The next publishable rung
needs a new external corpus and model scale:

- UrbanSound8K or AudioSet non-speech, plus LibriSpeech speech preservation;
- `base.en` replication followed by a preregistered larger Whisper model;
- a no-op conditional control in addition to same-cardinality head controls;
- repeated folds with graph-native aggregation rather than one candidate
  panel;
- circuit tests that replace or patch activations, not only zero ablations;
- an explicit distinction between detecting absence of speech, suppressing
  decoder continuation, and preserving intelligible but difficult speech.

The current result is ready to present as an autonomous causal-debugging
method with a successful falsification and a useful partial mitigation. It is
not evidence for a general Whisper repair.
