# Discriminative Linear Transforms: Fisher's Criterion and Linear Discriminant Analysis

## Abstract

A nearest-neighbour recogniser over raw acoustic features fails on real speech when the
*within-word* variation (speaker, vocal-tract length, coarticulation, channel) is larger than the
*between-word* variation (the phonetic content). Normalisation (CMVN, VTLN) and unsupervised cue
selection cannot fix this, because they never use the class labels: they cannot know which
directions of feature variation are word-identity and which are nuisance. The remedy is a
**supervised discriminative transform** — a projection learned *from labelled exemplars* that
suppresses within-word scatter and amplifies between-word scatter. This note states Fisher's
criterion and Linear Discriminant Analysis (LDA), the closed-form optimal linear transform for
that objective. It requires no gradient descent: the transform is the solution of a generalised
eigenproblem over two scatter matrices, both of which are sums of outer products of the data.

## 1. The problem, stated as scatter

Let the labelled exemplars be vectors x with class (word) labels c. Define the per-class mean
mu_c, the global mean mu, and n_c the count in class c.

**Axiom 1 (Scatter decomposition).** The total scatter of the data decomposes into a within-class
part and a between-class part:
S_T = S_W + S_B, where
S_W = sum_c sum_{x in c} (x - mu_c)(x - mu_c)^T   (within-class: nuisance variation)
S_B = sum_c n_c (mu_c - mu)(mu_c - mu)^T            (between-class: the signal we want).

A 1-NN recogniser implicitly trusts every direction of S_T equally. But directions dominated by
S_W (speaker, coarticulation) carry no word identity; trusting them is exactly why the raw-feature
ear collapses on real speech.

## 2. Fisher's criterion and LDA

**Axiom 2 (Fisher's criterion).** A good discriminative projection W maximises the ratio of
projected between-class scatter to projected within-class scatter:
J(W) = trace( (W^T S_W W)^{-1} (W^T S_B W) ).
This rewards a W under which classes are far apart *relative to* their internal spread — the only
thing that matters for nearest-neighbour decisions.

**Theorem LDA (optimal linear discriminant).** The columns of the maximising W are the leading
generalised eigenvectors w solving S_B w = lambda S_W w. Equivalently: (i) whiten by W_w = S_W^{-1/2}
(so within-class scatter becomes identity), (ii) rotate to the principal axes of the whitened
between-class scatter W_w^T S_B W_w (ordinary PCA on the transformed class means). Keep the top k
eigenvectors (k <= #classes - 1). The recogniser then runs 1-NN / nearest-class-mean in the
projected space y = W^T x.

**Remark (why this is the missing capability).** CMVN/VTLN subtract a *fixed* nuisance term chosen
by acoustic theory. LDA *derives* the nuisance directions from the data's own within-class scatter
and projects them out — it uses the labels. It is the smallest step from "normalise / select cues"
to "*learn* a representation."

## 3. Construction without backprop

Every quantity is a sum of outer products and one eigendecomposition — no optimiser, no fit-to-loss:
- mu_c, mu: means over banked exemplars.
- S_W, S_B: accumulate outer products (the agent's matrix primitives).
- Solve S_B w = lambda S_W w: whiten with S_W^{-1/2} (symmetric eigendecomposition of S_W), then
  eigendecompose the whitened S_B. Regularise S_W <- S_W + epsilon*I for stability when exemplars
  are few (shrinkage LDA).
- Project: y = W^T x. Recognise by nearest class mean of {W^T mu_c} (NCM) or 1-NN in y-space.

## 4. The empirical claim to test

**Hypothesis speech-lda (discriminative projection lifts real-speech recognition).** Fitting an LDA
(or regularised/shrinkage LDA) transform on labelled real-speech word exemplars, then recognising in
the projected space, will lift nearest-neighbour word recognition above the raw-feature ceiling that
normalisation and cue-growth could not move — because LDA explicitly removes the within-word
(speaker/coarticulation) scatter the raw features retain. The lift will be largest for words with
several exemplars (so S_W is estimable) and bounded by how *linearly separable* the words are in the
feature space; residual error after LDA indicates the separation is non-linear and motivates a
learned non-linear embedding (see: learned discriminative embeddings).

## 5. Falsifiability

If LDA on labelled exemplars does **not** beat raw-feature 1-NN on held-out real speech, then the
word/nuisance structure is not linearly separable in the feature space, and the linear-transform
family is exhausted — the evidence then points to a non-linear learned embedding, not more linear
algebra. Either outcome is informative: it tells the agent whether its representation problem is
linear or non-linear.
