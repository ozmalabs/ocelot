# Model active extraction — graph pulls apart a generative LM — RESULTS

**Block**: 305000. Pre-reg: `MODEL_ACTIVE_EXTRACTION_PREREG.md`.
Build: `domains/model_active_extraction.py`; measure:
`scripts/model_active_extraction_measure.py`.

The user's ask: *"extract more by running some of the model … start a graph and
have it analyse the model and pull apart parts of it to build the bits it
needs."* **Verdict: all three capabilities confirmed on the real `gemma3:4b`
generative LM — within the behavioural-probing bound.**

## The honest capability boundary (stated first)

"Running the model" here is the ollama HTTP API, which returns COMPLETIONS —
NOT per-token logprobs, NOT hidden activations (no torch / transformers /
llama_cpp; only numpy). So this rung extracts the model's BEHAVIOUR (what it
says a relation is) and its STATIC weights (embedding geometry + FFN concept
directions), **not** its live internal activations. Activation-tapping — the
richer "pull apart the circuit" extraction — needs a framework not installed
here and is a named follow-on.

## Measured (gemma3:4b, work_vocab=12000, seed=0)

| Claim | Result | Verdict |
|---|---|---|
| 1. FFN neurons → coherent typed concepts | animal 0.39 / number 0.60 / colour 0.50 coherence vs random-neuron ~0.06 | **HOLDS** |
| 2. running the model adds relational edges the geometry lacks | 20 probes → 20 edges (0→20 on seed nodes), correct commonsense | **HOLDS** |
| 3. graph-driven targeting ≥ random probing | targeted filled 3/5 vs random 2/5 empty nodes | **HOLDS (directional, underpowered)** |

### Claim 1 — FFN neurons are coherent typed concepts (static, no inference)
Searching `blk.20.ffn_down.weight` for the neuron most aligned with a concept
direction (mean seed-word embedding), and projecting it through the embedding:
- **animal** → neuron#315 promotes animals/animal/dog/bird/mouse (coherence
  0.39 vs random neuron 0.09)
- **number** → neuron#2159 promotes three/four/five/six/two (0.60 vs 0.04)
- **colour** → neuron#6831 promotes yellow/pink/black/blue/orange (0.50 vs 0.06)

Clean, human-legible concepts read straight from the weights, far above a
random neuron's coherence. This is richer than the MiniLM rung (block 304000):
a generative LM with a 262145-token vocab and explicit FFN concept-neurons, not
just an encoder's embedding.

### Claim 2 — running the model extracts structure the geometry lacks
Behavioural probing with 5 relation templates minted 20 typed edges from 20
probes (100% parse yield, 6.1s), taking the seed nodes from 0 → 20 relational
edges. The edges are correct commonsense the embedding kNN graph does NOT carry
as typed relations:
- `dog` → is_a mammal, at_location house, used_for companionship, has_property
  loyal, part_of family
- `knife` → is_a tool, at_location kitchen, used_for cutting, has_property
  sharp, part_of kitchen

The embedding geometry knows dog is *near* puppy/animal; it does NOT encode
"dog **is_a** mammal" as a directed typed edge. Running the model surfaces that
relational layer. The edges come from the model's outputs, not authored.

### Claim 3 — the graph directs the extraction from its own gaps
With half the nodes pre-seeded with an edge (so "sparsest" is meaningful),
targeting the graph's sparsest nodes filled 3/5 previously-empty nodes at a
fixed budget vs 2/5 for random probing. The graph's self-diagnosis (relational
degree) usefully directs the model — it pulls apart exactly the bits it lacks.

**Honesty**: this margin (3 vs 2 on a 5-node battery) is DIRECTIONALLY
positive but statistically UNDERPOWERED. The mechanism is sound (the smoke test
showed targeting cleanly skipping a pre-connected node and hitting the sparse
ones), but the measured advantage is small on this scale and should not be
read as a strong effect. Registered as such.

## Verdict on the user's ask

**Confirmed, within the behavioural bound.** The substrate can:
1. distil a real generative LM's STATIC geometry (embedding kNN + FFN
   concept-neurons) mechanically from the weights, no inference;
2. extract MORE by RUNNING it — typed relational edges the geometry lacks,
   from the model's own completions; and
3. DIRECT that extraction from its own diagnosed gaps (targeted > random,
   directionally).

This is "start a graph and have it pull apart the model to build the bits it
needs" — realised as behavioural probing plus static weight reads. It closes
the arc: 304000 distilled the geometry; 305000 shows the graph can then run the
model to fill the relational structure the geometry cannot hold, and can aim
that effort itself.

## Anti-faking bars — all honoured
- **Edges from the model, not authored**: every edge is a parsed model
  completion; templates fixed and generic, temperature 0.
- **Graph-not-matrix** (inherited 304000): distilled embedding graph does not
  retain the dense matrix.
- **Targets measured, not cherry-picked**: the active loop picks nodes by
  measured relational degree; targeted-vs-random uses the same budget/battery.
- **Skips gracefully**: static parts run without ollama; running-the-model
  parts skip if ollama/model absent (reported, not faked).
- **default == today**: NEW module + script + docs; numpy (weight math) +
  urllib (ollama HTTP), NOT an inference engine in the substrate. `.so` md5
  stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched.

## Honest scope / ceiling
- Behavioural probing, NOT activation tapping — the deep-circuit extraction is
  a named follow-on needing a framework not present here.
- Claim 3 is underpowered (5-node battery); the mechanism holds, the effect
  size is not established.
- The relation schema is a small fixed set (5 relations); the point is that
  running the model yields typed structure the geometry lacks, measured, not
  that the extraction is exhaustive.
- gemma3:4b static read uses a 12000-token frequency window; a demonstration
  scale, not the full 262145 vocab.
