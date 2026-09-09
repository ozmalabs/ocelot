# Between-layer extraction — the transformer's actual function — PREREG

**Block**: 307000

**Task**: The user's steering — *"the extraction should possibly focus on the
between-layer change"* and *"get torch/transformers"*. The static embedding
geometry (blocks 304-306) is what a model KNOWS; the BETWEEN-LAYER
transformation of the residual stream is what it DOES. This rung extracts that
FUNCTION from REAL forward passes — torch + transformers now installed in an
external venv, running on the GPU (GTX 1660 SUPER).

## 1. What "between-layer change" is

A decoder transformer maintains a residual stream `h`; each layer READS it,
computes a delta, and WRITES it back: `h_{L+1} = h_L + Δ_L`. The model's
computation IS the sequence of deltas `{Δ_L}`. Two readouts expose it:

- **Per-layer delta magnitude** `||h_{L+1} − h_L||` — how much work each layer
  does (where the model commits).
- **Logit lens** (nostalgebraist 2020): project the residual at each layer
  through the unembed and read the token distribution AS IT IS BEING BUILT.
  Watching the answer token climb to the top across depth IS the between-layer
  function made visible — and localises WHERE a fact/relation is computed.

## 2. Method (real activations, not weights-only)

`domains/between_layer_extraction.py` (external-tooling wrapper, lazy torch
import so the substrate import surface is unchanged when torch is absent):
- `load_traced(dir)` — HF causal LM with `output_hidden_states`, on GPU.
- `forward_trace(prompt)` — the residual `h_L` at every layer + per-layer
  delta magnitudes at the final token.
- `logit_lens(hidden)` — per-layer top tokens via the unembed.
- `answer_rank_by_layer(hidden, answer_id)` — rank of the answer token in each
  layer's logit-lens distribution (0 = top): the depth at which the model
  knows the answer.
- `layer_writes(prompt, concept_vec)` — projection of each layer's delta onto
  a concept direction: which layers WRITE a concept.

Models: Qwen3-1.7B (fits the 6 GB GPU). gemma3:4b / Qwen3.8-27B compared where
GPU/CPU budget allows (27B does not fit 6 GB — CPU or skipped, stated).

## 3. Falsifiable claims

1. **The between-layer function is recovered**: real per-layer deltas grow
   with depth and the logit-lens answer-rank DECREASES to 0 (answer becomes the
   top prediction) by the final layer, on a factual battery. (Confirmed in the
   probe: France→Paris rank 5734→0 across L18→L28.)
2. **Facts resolve at CHARACTERISTIC depths, not uniformly**: the layer at
   which the answer first reaches the top (the "resolution depth") is a
   specific mid-to-late band, and varies by relation type — factual recall is
   NOT smeared evenly across all layers. Reported per relation.
3. **The between-layer write is structure the static embedding LACKS**: the
   ordered depth-trajectory of a fact (where it is built) is information that
   the static embedding kNN graph (blocks 304-306) does not contain at all —
   the geometry says what's near what; the trajectory says WHEN/WHERE the model
   composes it.

Each reported with its measured outcome; failures reported as failures (e.g. a
relation whose answer never reaches the top, or resolves uniformly).

## 4. Anti-faking bars

- **Real activations, not a weights-only approximation**: the deltas and
  logit-lens come from an actual forward pass through the model, not from
  feeding a concept vector cold through one operator (which the earlier probe
  showed gives noise — the residual at layer L is not a raw embedding).
- **Held-out answer**: `answer_rank_by_layer` needs the answer token id to
  RANK it, but the forward pass and logit-lens do not see the answer — the
  answer is used only to SCORE where the model itself produced it.
- **Same battery / same readout** across models and relations.
- **default == today**: torch/transformers are an EXTERNAL venv under
  `/applications`, NOT linked into the substrate; the module imports them
  lazily. Importing `domains` does not require torch. The substrate `.so` md5
  stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched. venv + model weights live under `/applications` and are NOT
  committed to the repo.

## 5. Honest bounds

- torch/transformers/GPU are EXTERNAL analysis tooling, not part of the
  substrate — this rung ANALYSES a model, it does not add inference to the
  substrate.
- 6 GB GPU: Qwen3-1.7B fits in fp16; the 27B does not (CPU-only would be very
  slow) — the cross-model arm is best-effort, and its absence is reported, not
  faked.
- Logit lens is a KNOWN-imperfect probe (the unembed is calibrated for the
  final layer; early-layer projections are approximate) — it shows the
  trajectory qualitatively, not a calibrated per-layer probability. Stated.
- A small factual battery (demonstration), not a normed interpretability
  benchmark.
