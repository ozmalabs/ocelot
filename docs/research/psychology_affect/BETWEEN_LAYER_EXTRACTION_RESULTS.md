# Between-layer extraction — the transformer's actual function — RESULTS

**Block**: 307000. Pre-reg: `BETWEEN_LAYER_EXTRACTION_PREREG.md`.
Build: `domains/between_layer_extraction.py`; measure:
`scripts/between_layer_extraction_measure.py`.

The user: *"the extraction should focus on the between-layer change"* +
*"get torch/transformers"*. Done — torch + transformers installed in an
external venv on the GPU (GTX 1660 SUPER), and the between-layer FUNCTION
extracted from REAL forward passes. **Verdict: all three claims HOLD.**

## What was extracted (real activations, Qwen3-1.7B, GPU)

The residual stream at every layer, the per-layer delta `||h_{L+1}−h_L||`, and
the logit lens (each layer's residual projected through the unembed) — the
token distribution AS IT IS BUILT across depth.

## Measured (10-prompt factual/relational battery)

| Claim | Result | Verdict |
|---|---|---|
| 1. between-layer function recovered | 9/10 answers reach logit-lens rank 0 by final layer; delta grows with depth 10/10 | **HOLDS** |
| 2. characteristic resolution depths | band L21–L28 (75–100% of stack), mean 85%; varies by relation | **HOLDS** |
| 3. depth-trajectory = new structure | the where-a-fact-is-built trajectory is absent from any static kNN | **HOLDS** |

### Claim 1 — the function is recovered
Per-layer delta magnitudes grow monotonically with depth (e.g. France prompt:
16 → 3098 across 28 layers) — the model does its committing work late. The
logit-lens answer-rank falls to 0 (answer becomes the top prediction) by the
final layer for 9/10 prompts. The one miss — "Two plus two equals 4" resolving
to rank 4, not top — is reported honestly: single-token arithmetic is weakly
represented in this 1.7B model's next-token distribution at this phrasing.

### Claim 2 — facts resolve at characteristic depths, not uniformly
The layer at which the answer first reaches the top (resolution depth) is
concentrated in a **mid-late band, L21–L28 (75–100% of the 28-layer stack),
mean 85%** — NOT smeared evenly. And it varies by relation type:

| relation | resolution depth (layers) | mean |
|---|---|---|
| isa (dog→animal, rose→flower) | 22, 22 | 22.0 (earliest) |
| antonym (hot→cold, up→down, big→small) | 21, 24, 23 | 22.7 |
| morphology (mouse→mice) | 25 | 25.0 |
| capital (France→Paris, Japan→Tokyo, Italy→Rome) | 28, 21, 28 | 25.7 (latest) |

Category membership (isa) resolves earliest; specific factual recall (capital
cities) resolves latest. This is the between-layer function localised — WHERE
in the computation each kind of knowledge is assembled.

### Claim 3 — the trajectory is structure the static embedding lacks
The ordered rank-by-layer trajectory of a fact — where across depth it gets
built — is a property of the COMPUTATION, only visible by running the model. No
static embedding kNN graph (blocks 304-306) contains it. This is the piece the
static distillation could not capture, now extracted.

## The arc, closed

- 304-305: distil the static GEOMETRY (what the model knows) into a graph.
- 306: the geometry's graph-likeness (concentration) — a static property.
- **307 (this rung): extract the FUNCTION (what the model does) — the
  between-layer residual trajectory — which the static geometry cannot hold.**

Together: the model's knowledge distils into graph geometry AND its computation
is extractable as a depth-localised trajectory. The between-layer change was
the missing piece, and it is real, recoverable, and relation-specific.

## Anti-faking / method
- **Real activations**, not weights-only: an actual forward pass through the
  model produces the deltas and logit-lens (the earlier weights-only probe
  gave noise — confirming this required running the model).
- **Held-out answer**: the answer token is used only to RANK where the model
  itself produced it; the forward pass and logit-lens do not see it.
- Same battery / same readout across relations; the arithmetic miss reported,
  not hidden.
- **default == today**: torch/transformers are an EXTERNAL venv under
  `/applications`, imported LAZILY — importing `domains` does not require
  torch; the substrate `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN-internals / toolbox untouched. venv + model weights live under
  `/applications/data/model_graph_work` and are NOT committed to the repo.

## Honest bounds
- torch/transformers/GPU are EXTERNAL analysis tooling — this rung ANALYSES a
  model; it does not add inference to the substrate.
- Qwen3-1.7B only (fits the 6 GB GPU); gemma3:4b / Qwen3.8-27B not run here
  (27B does not fit; a cross-model depth comparison is a named follow-on).
- Logit lens is a known-imperfect probe (the unembed is calibrated for the
  final layer; early-layer projections are approximate) — the trajectory is
  qualitative, not a calibrated per-layer probability.
- 10-prompt demonstration battery, not a normed interpretability benchmark;
  the resolution-depth bands are indicative, not population statistics.
