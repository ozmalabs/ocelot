# Contextual model editing without retraining

## What this demonstrates

Jabberwock can make a non-trivial, state-dependent change to a published
language model from an explicit understanding of its computation. The first
demonstration gives Gemma 4 E2B-IT a more profane informal register while:

- leaving every base parameter unchanged;
- leaving the tied input embedding unchanged;
- constraining the adapter to zero along formal, code-only, and safety-refusal
  response prefixes;
- using no gradient steps, fine-tuning, candidate-adapter search, or behavioral
  gate;
- producing a small, independently removable low-rank artifact.

This is not a claim that safety alignment is a separable layer, nor an attempt
to remove it. Gemma's post-training changes are distributed through the model.
The experiment instead selects an unmistakable harmless behavior and asks
whether Jabberwock can derive an exact intervention at the correct architectural
boundary.

## Why this is not token biasing

A constant vocabulary bias would make the selected words more likely in every
context. A prompt wrapper would change the input rather than the model. A
classifier gate would merely select between two hand-authored policies.

This edit is a function of Gemma's own final residual state:

```text
base pre-softcap logits:       l(h) = W h
adapter:                       a(h) = A B h
modified pre-softcap logits:  l'(h) = W h + A B h
```

The same factors are active at every decoding step, but their effect changes
with `h`. Informal target states receive graph-derived shifts that make the
requested token the greedy winner. Captured protected states receive an
exactly zero desired-output vector; the serialized float32 factors must
reproduce it within the graph's numerical tolerance.

## The architectural inference

Gemma 4 E2B has a 1,536-dimensional text residual and a 262,144-token
vocabulary. Its language-model output weight is tied to its input embedding.
Overwriting output rows would therefore also change how the same tokens are
read at the input.

The graph records that alias and derives a stricter affordance: attach an
additive adapter to the result of the output projection. The hook sees the
final normalized residual, changes pre-softcap logits, and never mutates the
shared weight. Removing the hook restores the exact base computation.

## Closed-form construction

For `n` named residual states, put their vectors into columns of:

```text
H in R^(hidden_width x n)
```

Put the graph-derived output deltas into matching columns of:

```text
D in R^(vocabulary_width x n)
```

For an informal target, the boundary reports the target token's pre-softcap
logit and the maximum competing logit. Given requested winning margin `m`, the
graph derives:

```text
target_delta = max_competing_logit - target_logit + m
```

Adding that delta makes the target the unique greedy winner. This is stronger
than boosting it relative to one chosen alternative: the first real run showed
that an exact pairwise preference can still lose to a third token. For a
protected state, the entire desired-delta column is zero.

When `H` has full column rank, its Moore-Penrose right inverse satisfies:

```text
pinv(H) H = I
```

The graph derives and authorizes:

```text
D = U S V^T
A = U S
B = V^T pinv(H)
DeltaW = A B = D pinv(H)
DeltaW H = D
rank(DeltaW) <= n
```

This is interpolation by an algebraic right inverse, not an optimization
procedure. The desired examples specify the edit; they are not a set of
candidates from which the host selects a successful patch.

## What the graph owns

The Rust graph and seed data own the cognitive work:

1. represent the published residual/output interface and tied-weight alias;
2. represent target and protected behavioral constraints;
3. derive the output-only low-rank form;
4. create and discharge structural proof obligations;
5. authorize the exact compiler;
6. inspect the compiler's rank, hash, finiteness, target-error, and
   protected-error witnesses;
7. author a proof-carrying patch only after those witnesses pass.

Python is the mechanical boundary. It captures tensors, executes
`D pinv(H)`, records numerical witnesses, installs the graph-authored hook, and
runs observations. It cannot authorize an unproved patch.

The implementation is in:

- `domains/contextual_model_edit.py`
- `seeds/contextual_model_edit.json`
- `scripts/jabberwock_edits_gemma4_style.py`
- `tests/test_contextual_model_edit_migrated.py`

## Protected-prefix argument

A single zero-effect control state is weak. The demonstration therefore
captures each residual state along a baseline greedy response prefix for three
control roles:

- formal factual language;
- literal code-only output;
- a safety refusal.

At step zero the adapter produces zero delta, so the greedy next token is
unchanged. Given that same token, the next residual is the captured step-one
state, where the adapter again produces zero delta. Repeating this establishes
by induction that the whole captured greedy prefix is unchanged, subject to
deterministic execution.

This proof does **not** establish global preservation. It covers the named
states and their captured deterministic prefixes. Behavior on new residual
states is empirical and is labelled as such in the patch.

## Running the experiment

The official checkpoint is deliberately kept under gitignored `data/`.

```bash
PYTHONPATH=/absolute/path/to/this/worktree/research/experiments/gamma-substrate \
  /home/matt/ozma/internal/research/.venv/bin/python \
  scripts/jabberwock_edits_gemma4_style.py
```

The runner writes:

- low-rank factors to
  `data/gemma4/contextual-profane-register.safetensors`;
- graph proof attributes, numerical witnesses, and before/after observations
  to `results/gemma4_contextual_style_edit.json`.

## Result on the official checkpoint

The graph compiled 19 linearly independent constraints into a rank-2 adapter:
three informal target states and sixteen states along three protected greedy
response prefixes. There were no gradient or search steps.

| Context | Gemma 4 baseline | With adapter |
| --- | --- | --- |
| third deployment failure | `Ugh…` | `Damn.` |
| cache-deleting bug | `Ugh.` | `Fuck.` |
| supposedly fixed build | `Ugh, seriously?!` | `Damn! …` |
| formal factual prefix | `The boiling point of water at` | identical |
| code-only prefix | `x + y` | identical |
| safety-refusal prefix | `I cannot provide instructions for dangerous` | identical |

For the actual serialized float32 factors, the maximum absolute target
interpolation error was `3.21e-7`; the maximum adapter delta on protected
states was `1.38e-7`, both below the graph's `1e-6` acceptance bound. All three
protected greedy token prefixes were identical. Exact rank factorization
reduced the adapter to 527,360 factor values versus the untouched published
model, and removing its hook restores the original computation.

## Honest interpretation

The strong result is mechanistic editability:

- Jabberwock noticed an architectural alias that makes the obvious weight edit
  semantically unsafe.
- It derived a different intervention site from the model's computation.
- It translated semantic constraints into a finite-rank algebraic update.
- It proved exact behavior on specified residual states and exact reversibility.

The result alone does not show that Jabberwock has identified a universal
"profanity direction", nor that protected behavior is preserved outside the
proved trajectories. Generalization requires a separate, preregistered
evaluation. Keeping that distinction explicit is part of the method.

## Model sources

- [Gemma 4 model overview and model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [Official Gemma 4 E2B instruction checkpoint](https://huggingface.co/google/gemma-4-E2B-it)
- [Gemma 4 technical report](https://arxiv.org/abs/2607.02770)
