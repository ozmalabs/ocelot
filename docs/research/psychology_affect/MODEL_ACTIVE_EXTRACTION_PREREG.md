# Model active extraction — graph pulls apart a generative LM — PREREG

**Block**: 305000

**Task**: The user's ask, extending block 304000 (weight→graph distillation):
*"do that — but also we should be able to extract more by running some of the
model. we should be able to start a graph and have it analyse the model and
pull apart parts of it to build the bits it needs."*

This registers three capabilities and their falsifiable tests:
- **(A) STATIC** — distil a real GENERATIVE LM (`gemma3:4b`, not just the
  MiniLM encoder) from its GGUF weights: embedding kNN graph + FFN
  concept-neurons, no inference.
- **(B) RUNNING THE MODEL** — extract MORE than the weights give by PROMPTING
  the model and parsing completions into typed relational edges.
- **(C) GRAPH-DRIVEN ACTIVE** — the graph scores its OWN gaps and targets the
  model to fill exactly those: it pulls apart the model to build the bits it
  needs.

## 1. The honest capability boundary (stated up front)

In this environment the only way to run the model is the ollama HTTP API,
which returns COMPLETIONS — not per-token logprobs, not hidden activations
(there is no torch / transformers / llama_cpp; only numpy). Therefore:

- **"Running the model" here means BEHAVIOURAL PROBING** (prompt → text),
  NOT activation tapping mid-forward-pass.
- Reading intermediate activations (the richer "pull apart the circuit"
  extraction) needs a framework not installed here and is a NAMED FOLLOW-ON,
  not built this rung.

This bound is registered so the result is not overclaimed: we extract the
model's BEHAVIOUR (what it says a relation is) and its STATIC weights (embedding
geometry + FFN concept directions), not its live internal activations.

## 2. What is extracted

**(A) Static** (reuses `domains.model_reader` + block-304000
`weight_distillation.distill`, no inference):
- embedding matrix (`gemma3:4b`: 262145×2560) → top-k cosine kNN graph over a
  frequency window (working vocab), the same lossy distiller as 304000, now on
  a generative LM's richer geometry.
- FFN value neurons (Geva et al. key-value memories): a neuron's value vector
  in `blk.L.ffn_down.weight`, projected through the embedding, names the tokens
  it PROMOTES — its concept. The `jabberwock_gemma_neurons` pattern, minted as
  a typed concept node.

**(B) Running the model**: relation templates (`IsA`, `AtLocation`, `UsedFor`,
`HasProperty`, `PartOf`) prompted with an instruction framing that yields a
bare one-word answer; the completion is parsed into a typed edge
(`subject --edge_type--> target`). The edge comes from the MODEL'S output.

**(C) Graph-driven active loop**: score each graph node by its RELATIONAL
degree (how many typed edges it already has — the graph's own measure of how
known it is); pick the SPARSEST nodes (targeted) and probe the model for their
missing relations; mint the returned edges; remeasure. The graph diagnoses its
own gaps and directs the extraction.

## 3. Falsifiable claims

1. **FFN neurons yield coherent typed concepts**: for seed concepts
   (animal, number, colour, …), the most-aligned FFN neuron promotes tokens
   that are COHERENT with the seed (a human-legible concept), above a random
   neuron's coherence.
2. **Running the model ADDS relational structure the static geometry lacks**:
   behavioural probing mints typed edges (`dog is_a mammal`,
   `knife at_location kitchen`) that the embedding kNN graph does NOT contain
   as explicit typed relations. Measured as net edges added, with correctness
   spot-checked against commonsense.
3. **Graph-driven targeting beats random probing**: at a fixed probe budget,
   targeting the graph's SPARSEST nodes raises the graph's total relational
   connectivity (or fills more previously-empty nodes) MORE than probing random
   nodes — the graph's self-diagnosis is useful, not decorative.

Each reported with its measured number; any that fail reported as failing.

## 4. Anti-faking bars

- **Edges from the model, not authored**: every relational edge is the parsed
  output of a model completion; no hand-written edge list. The templates are
  fixed and generic (not per-answer tuned).
- **Graph-not-matrix at test time** (inherited from 304000): the distilled
  embedding graph does not retain the dense matrix.
- **Targets measured, not cherry-picked**: the active loop picks nodes by
  MEASURED relational degree (sparsest first), not a hand-chosen "wins" list;
  the targeted-vs-random comparison uses the same budget and battery.
- **Bounded + reproducible**: small working vocab + small probe budget so the
  measure runs in bounded time; temperature 0 for deterministic completions.
- **Skips gracefully**: if ollama or the model is absent, the running-the-model
  parts SKIP (the static parts still run) — reported, not silently faked.
- **default == today**: a NEW module + script + docs; numpy for the weight
  math + urllib for the ollama HTTP call (NOT an inference engine linked into
  the substrate). `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN-internals / toolbox untouched.

## 5. What a positive / negative result means

- All three hold → the substrate can (i) distil a generative LM's static
  geometry, (ii) extract MORE by running it (behavioural relations), and
  (iii) direct that extraction from its own gaps — "start a graph and have it
  pull apart the model to build the bits it needs," within the behavioural-
  probing bound.
- Claim 2 failing → running the model adds nothing over the static weights
  (the probing is redundant); reported as such.
- Claim 3 failing → the graph's self-diagnosis does not help targeting;
  reported as such (extraction still works, just not usefully graph-directed).

## 6. Scope / honesty

- Behavioural probing, NOT activation tapping (Sec 1) — the deeper circuit
  extraction is a named follow-on.
- `gemma3:4b` static read uses a frequency-window working vocab (the full
  262145 is large); a demonstration scale.
- Relation-template extraction is a small fixed schema, not an open
  information-extraction system; the point is that running the model yields
  typed structure the geometry lacks, measured, not that it is exhaustive.
