# Deterministic engineering of published models

Jabberwock can now treat a published neural network as an inspectable
computational object rather than a black box to probe.

This is deliberately different from the earlier causal-debugging pipeline.
That pipeline asks which intervention changes a benchmark. The new faculty
asks what computation the model implements, which exact transformations its
algebra permits, what each transformation preserves, and whether a proposed
edit has enough structural evidence to compile safely. Behavioral validation
can still follow, but it is not used to discover or prove the edit.

## What is graph-native

The seed `published_model_engineering` gives the Rust rule engine an
intermediate representation for:

- published models, operators, parameters, containment, and content hashes;
- tensor partitions such as the contiguous input slice belonging to an
  attention head;
- semantic output classes and their exact affine weight rows and bias entries;
- source-level signals, guards, assignments, reads, writes, and ordering;
- mechanism explanations and exact engineering affordances;
- enhancement goals, algebraic derivations, typed proof obligations, and
  proof-carrying patches.

Rules assign semantic roles by graph joins, reconstruct control-flow
mechanisms, derive legal transformations from operator equations, discharge
each obligation against a typed witness, and author the final edit. Python is
the mechanical boundary: it reflects published PyTorch/source structure into
the graph and applies only an exact target already authored and proved there.

The adapter has no candidate ranking, loss, gradient, optimizer, behavioral
score, `argmin`, or `argmax`.

## Exact attention transformation

Whisper concatenates the outputs of its attention heads and applies an affine
output projection:

```text
y = W_o concat(h_0, ..., h_n) + b_o
  = sum_i W_i h_i + b_o
```

For a requested head `h`, scaling its contribution by `a` is therefore
identical for every possible input to scaling the corresponding columns of
`W_o`:

```text
y' = sum_(i != h) W_i h_i + W_h (a h_h) + b_o
   = y + (a - 1) W_h h_h
```

This turns a transient runtime hook into a permanent weight edit without
retraining. It also gives precise invariants:

- all non-target input columns are byte-identical;
- the output bias is byte-identical;
- the edit has all-input rather than sampled-example scope;
- saving the target column slice is sufficient for exact reversal;
- the parameter content hash prevents applying the proof to different
  weights.

The graph will not author this patch until four separately matched obligations
are proved: complete partition layout, affine dependence, source-parameter
identity, and reversible slice locality.

This theorem proves that the compiled edit implements the requested mechanism.
It does **not** prove that suppressing a particular head is desirable. A
semantic goal still needs a causal model, specification, or externally
supplied intent. Exact surgery and correct diagnosis are distinct claims.

## Exact classifier behavior permutation

For an affine classifier `y = W x + b`, swapping two semantic output classes
is not a retraining problem. If `P` is the permutation that swaps rows `a` and
`b`, then:

```text
y' = P y = (P W) x + P b
DeltaW = (e_a - e_b) (W_b - W_a)^T
```

The weight change is rank one. Treating the bias as an augmented input keeps
the whole update rank one. The graph now derives this transformation from the
published class-to-row mapping, proves distinct valid rows, affine output
semantics, exact parameter identities, and the permutation's involution, then
authors the patch. For every possible input—not merely test samples—the two
chosen logits exchange values and every other logit is unchanged. Applying
the same semantic swap again restores the original behavior.

This is the small, legible demonstration of deterministic network engineering:
the requested behavioral change, its exact tensor implementation, its
all-input preservation domain, its low-rank form, and its inverse all follow
from one equation.

## Deterministic Whisper reconstruction

The reproducible run is:

```bash
PYTHONPATH="$PWD/runners/dsl/python:$PWD" \
  /home/matt/ozma/internal/research/.venv/bin/python \
  scripts/jabberwock_understands_whisper.py \
  --model-dir /path/to/whisper-models
```

On the locally installed official `base.en`, the graph reconstructed:

| IR object | Count |
|---|---:|
| Operators | 189 |
| Parameters | 244 |
| Attention input partitions | 144 |
| Program signals | 148 |
| Program assignments | 95 |
| Exact engineering affordances | 144 |

From `transcribe.py` control and data dependencies, Jabberwock also derived the
mechanism:

```text
absence evidence first sets abstention;
a later content-confidence guard can force abstention false
```

It authored a local source transformation that preserves the prior abstention
decision, with independent program-order, semantic-role, and assignment-write
witnesses. This demonstrates deterministic program understanding, but it
should not be confused with the larger model-engineering faculty or presented
as the final Whisper repair.

For the previously identified
`encoder.blocks.1.attn.head.3`, a requested factor of zero produced the exact
weight edit:

```text
encoder.blocks.1.attn.out.weight[:, 192:256] *= 0
```

An arbitrary-tensor verification of the compiled theorem had maximum absolute
error `0.0`, and reversal restored the original whole-model hash. The run used
zero audio examples, gradients, candidate edits, or training steps, and did
not modify the installed source or checkpoint on disk.

The complete machine-readable derivation and receipts are in
`results/whisper_deterministic_engineering.json`.

## What this adds to Jabberwock

Jabberwock can now:

1. ingest a published network into explicit graph structure;
2. interrogate which internal components admit exact transformations;
3. explain a source-level failure mechanism from deterministic dependencies;
4. derive an algebraic model transformation and its preservation domain;
5. refuse compilation until typed proof obligations are discharged;
6. bind the proof to the exact parameter bytes;
7. compile, audit, and reverse the edit without retraining.

That is a reusable model-engineering loop. Whisper is the first concrete
subject, not a special procedural implementation of the method. Contextual
language-model behavior edits build on the same contract; see
`docs/contextual_model_editing.md`.

## Current boundary and next extensions

The present operator semantics cover published module structure, affine
attention partitions, affine output-class permutations, contextual
residual/output adapters, and Python assignment/guard control flow. Operators
classified as `composite_or_nonlinear` remain visible but opaque; the system
does not pretend to understand them.

The next deterministic extensions should be:

- ingest exported PyTorch dataflow so tensor producers and consumers are
  explicit rather than inferred from module containment;
- add algebra for residual sums, normalization, monotone nonlinearities,
  convolution, embedding lookup, and tied parameters;
- propagate shapes, intervals, error bounds, and invariants through the graph;
- represent functional specifications independently of implementations;
- add equivalence rules for affine folding, basis changes, low-rank
  factorization, neuron/channel permutations, and bounded quantization;
- use an SMT or proof-assistant boundary for obligations beyond the rule
  engine’s decidable structural witnesses;
- derive semantic targets from a graph causal theory of the task, keeping
  target selection out of Python and separate from transformation proof.

The central guardrail remains unchanged: external code may expose and enact,
but model understanding, goals, derivations, and decisions belong in the
graph.
