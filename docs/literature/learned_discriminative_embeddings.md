# Learned Discriminative Embeddings for Speech: Metric Learning and the x-vector

## Abstract

A linear discriminant (LDA) removes *linear* nuisance directions, but speaker identity,
vocal-tract length and coarticulation warp the acoustic features *non-linearly*, so the words are
not linearly separable. The modern remedy is a **learned non-linear embedding**: a neural network
f_theta that maps a variable-length utterance to a fixed vector in which same-word (or same-class)
inputs are close and different-word inputs are far, and which **generalises to classes and speakers
unseen in training** (open set). This is the representation that hand-features and selection cannot
produce, because it is *fit to the discrimination objective itself*. Two ingredients make it work:
a temporal **statistics-pooling** layer (variable length -> fixed vector) and a **discriminative
training objective** (classification bottleneck, or a metric loss). This is the x-vector recipe.

## 1. From frames to a fixed embedding

**Axiom 1 (Statistics pooling).** A frame-level network g_theta produces a per-frame feature
h_t = g_theta(x_t); a pooling layer aggregates the frames into a fixed-length utterance vector by
concatenating their **mean and standard deviation** over time:
p = [ mean_t h_t ; std_t h_t ].
Mean+std pooling is permutation- and length-invariant and captures both the average spectral
content and its dynamics — the statistics that survive across renditions of the same word.

## 2. The discriminative objective

**Axiom 2 (Discrimination by bottleneck or margin).** Two equivalent ways to force p to be
word-discriminative and speaker-invariant:
- **Classification bottleneck (x-vector).** Stack a small MLP on p ending in a softmax over the
  *training* words; train to classify. After training, discard the softmax and read the
  **penultimate layer** as the embedding e. The bottleneck forces e to encode whatever separates
  words while discarding nuisance.
- **Metric / triplet loss.** Sample an anchor a, a same-word positive p+, a different-word negative
  n-, and minimise max(0, ||e(a)-e(p+)||^2 - ||e(a)-e(n-)||^2 + margin). Directly shapes the metric:
  same-word close, different-word far.

**Theorem embedding-generalisation (open-set transfer).** An embedding trained to classify a *fixed*
set of training words separates words and speakers **never seen in training**: the bottleneck cannot
memorise test classes, so to lower training loss it must learn a *transferable* discriminative
representation. Hence recognition of a new word is possible from a single enrolled exemplar by
nearest-embedding (cosine) — the property a raw-feature 1-NN lacks.

## 3. Assembling the net (write, then optionally fit)

The agent assembles f_theta from its own net constructors (ReLU layers as composed CPWL gadgets;
mean+std pooling is a composable reduction). Two routes for the weights:
- **Write-not-train initialisation.** Compose the frame network from derived gadgets (local
  polynomial lifts, predictive-residual taps) as a strong non-linear featuriser; fit only the final
  linear readout in closed form (ELM / least-squares ridge readout over the pooled embedding). No
  backprop, fully auditable.
- **Train the embedding.** If the closed-form readout is insufficient, fit f_theta end-to-end by
  gradient descent on the classification or triplet loss (mini-batches of labelled word segments).
  This is the standard x-vector training; it is the point at which the agent moves from
  *composing* a representation to *learning* one.

**Method (recipe).** frame-MLP g_theta (2-3 ReLU layers over a context window of cochleagram /
formant features) -> statistics pooling [mean;std] -> embedding MLP -> (softmax head for training).
Recognise held-out utterances by cosine nearest-neighbour over enrolled embeddings.

## 4. The empirical claim to test

**Hypothesis speech-xvector (learned embedding breaks the real-speech ceiling).** A small
frame-network + statistics-pooling + discriminative head, assembled by the agent and fit on labelled
real-speech words, produces utterance embeddings whose nearest-neighbour recognition exceeds both the
raw-feature ceiling and the LDA ceiling on real multi-speaker, coarticulated speech, and recognises
words with few or unseen exemplars (open-set), because the embedding is *learned to discriminate*
rather than *selected to normalise*.

## 5. Why this is the right next capability

Every earlier attempt — CMVN, VTLN, cue-growth — kept the representation *fixed* and chose among
*given* features. None used the labels to *learn* a new representation. The embedding does exactly
that. It is also the bridge to the agent's existing net-authoring machinery: statistics pooling and
ReLU layers are composable, and the only genuinely new ingredient is *fitting* — a closed-form ridge
readout first, gradient training only if needed. The transition from "select cues" to "learn an
embedding" is the architectural step the real-speech ceiling has been pointing at all along.

## 6. Falsifiability

If a learned embedding, properly fit, does **not** beat LDA and raw-feature 1-NN on held-out real
speech, then the limit is data (too few labelled exemplars per word to fit a net) rather than
representation — and the next lever is more labelled data (the whisper-teacher transcribing more
hours), not a bigger model.
