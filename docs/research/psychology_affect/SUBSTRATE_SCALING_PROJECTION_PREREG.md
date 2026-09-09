# Substrate scaling projection — PREREG

**Block**: 302000

**Task**: The user's framing — *"the point is that the coverage can be
distilled. … basically what would the estimated cost and capability be if it
was scaled up, and what would the cost of scaling be … investing X time and
effort results in Y capability — how much to get LLM-level capability, how
many OoM of power/compute less is it — and also it never needs to be
retrained, all improvements are additive."*

This registers a measured **scaling projection**: a model of
`X (distillation effort) → Y (coverage/capability)`, grounded in the
substrate's actual scaling CONSTANTS (measured, not asserted), used to project
(a) how much X to reach LLM-scale coverage, (b) how many orders of magnitude
(OoM) less compute/energy per inference, and (c) the additive / no-retrain
property quantified.

**Honesty is the whole point**: this is a PROJECTION built from measured
constants plus ONE external anchor. Every extrapolated number is labelled as
extrapolated; the coverage CEILING (what distillation does NOT buy) is stated
as prominently as the win.

## 1. What is measured (the constants the projection rests on)

Measured on this machine (Linux, single core, Python + the Rust `_native`
`.so`; `scripts/substrate_scaling_projection.py` reproduces):

- **Memory is linear in graph size**: from the 10k→50k node sweep,
  **~663 bytes per node** (a Concept node + ~4 `causal_influence` edges).
  Fixed interpreter+`.so` overhead ≈ 14 MB.
- **Inference cost is LOCAL and FLAT**: a coherence read
  (`domains.qualia_navigation.coherence_signal`) is **~0.0066 ms/call** and
  does NOT grow with total graph size — it is `O(cues × degree)`, touching
  only the active working set. Measured flat from 100 to 50,000 nodes.
- **Distillation throughput** (the X axis): **~127,000 facts/sec** ingested
  single-threaded (a "fact" = one node + ~4 edges; ~259k nodes/sec, ~993k
  edges/sec).
- **Marginal add is ADDITIVE and size-independent**: adding 1,000 facts to a
  100,000-node graph costs **~0.0084 ms/fact** — identical to bulk ingest,
  i.e. the cost of adding knowledge does NOT rise with existing graph size.
  No retraining, no gradient step, no catastrophic forgetting; defaults stay
  byte-identical.

## 2. The external anchor (LLM side)

ONE citable anchor, used only for the OoM comparison:

- **Llama 3 / 3.1 8B**: 8×10⁹ parameters, pre-trained on ~15×10¹² tokens
  ([Meta / HF Llama 3.1 release](https://huggingface.co/blog/llama31);
  [training token count](https://www.emergentmind.com/topics/llama-3-8b-model)).
  Content rephrased for compliance with licensing restrictions.
- **Training compute** (standard Chinchilla estimate `C ≈ 6·N·D`):
  `6 × 8e9 × 15e12 ≈ 7×10²³ FLOPs`. Extrapolated from the published N and D,
  labelled as an estimate.
- **Inference compute** (`≈ 2·N` FLOPs/token): `2 × 8e9 ≈ 1.6×10¹⁰
  FLOPs/token`. This is the per-step figure the substrate's per-read cost is
  compared against.

## 3. The projection model

`X → Y`:
- **X** = distillation effort = facts to ingest ÷ throughput, PLUS the
  (dominant, human/pipeline) cost of SOURCING + CURATING clean facts. The
  measured ingest rate bounds the machine cost; the curation cost is the real
  X and is stated as the honest bottleneck.
- **Y** = coverage = number of distilled facts (nodes+edges) reasoned over at
  the operations already built (coherence, analogy, CAN relaxation,
  knows-that/knows-what aperture).

Projected at three coverage scales, using the measured linear-memory /
flat-inference / additive constants:

| Scale | Facts | Cold disk | Hot RAM (working set) | Inference/step |
|---|---|---|---|---|
| ConceptNet-class | ~3.4×10⁶ | GB-scale | MB-scale | ~0.007 ms (flat) |
| Wikipedia-fact-class | ~10⁸ | tens of GB | MB-scale | flat |
| LLM-coverage-class | ~10⁹–10¹⁰ | ~TB-scale | MB-scale | flat |

The projected claims:
1. **Hot RAM stays MB-scale** at every coverage scale (cold-tier mmap; pay
   per-miss, not per-corpus) — the linear-memory constant applies to the HOT
   working set, disk is where linear growth lands.
2. **Per-inference compute stays ~flat** — the flat-local-read constant.
3. **Per-inference compute is many OoM below the LLM per-token figure** — the
   headline number, computed from measured read-FLOPs vs `2·N`.
4. **Scaling is additive**: reaching LLM-coverage is `+facts` at the measured
   size-independent marginal cost, never a retrain.

## 4. Falsifiable claims (this rung)

1. **Linear memory**: RSS grows linearly in node count; the per-node constant
   is stable across the sweep (report the fit + residual).
2. **Flat local inference**: coherence-read latency does NOT grow with total
   graph size (report latency at 100 … 100k nodes; slope ≈ 0).
3. **Additive marginal cost**: ms/fact to add to a large graph equals bulk
   ingest ms/fact (report both; ratio ≈ 1).
4. **OoM inference gap**: substrate per-read FLOPs vs Llama-3-8B `2·N`/token
   spans a stated number of OoM (report the estimate + how it's computed).

## 5. The honest ceiling (stated as prominently as the win)

- **Coverage ≠ capability parity.** Distilling 10¹⁰ facts buys MORE of the
  operations the substrate MODELS (compositional reasoning over EXPLICIT
  structure). It does NOT buy the LLM's generative interpolation — fluent
  novel text, robustness to unseen phrasings, filling gaps the graph does not
  contain. The substrate reasons over structure it HAS; the LLM generates
  plausible structure it does not. That is a degree-not-kind boundary the
  designer CHOOSES where to draw (the arc's own principle), not a free lunch.
- **X is dominated by curation, not machine time.** The 127k facts/sec is the
  CHEAP part. Sourcing clean, non-contradictory, well-typed facts at LLM-
  coverage scale is the real cost, and noise scales as cheaply as signal
  (exactly why the ConceptNet slab dropped `RelatedTo`). The projection bounds
  the MACHINE cost of scaling; it does not claim curation is free.
- **The OoM comparison is per-INFERENCE-step, not capability-normalised.** A
  substrate read and an LLM token are not the same unit of work. The honest
  claim is "orders of magnitude cheaper per operation ON THE OPERATIONS IT
  MODELS," not "N× cheaper for equal capability."
- **Extrapolation risk**: measured to 100k nodes; TB-scale is extrapolated on
  the linear/flat constants. Real graphs at 10⁹ may hit degree-distribution,
  cache, and page-fault effects the sweep does not capture. Labelled
  extrapolated.

## 6. Scope / method

- seed+python only; a measurement script + docs. NO Rust, NO CAN-internals,
  NO toolbox changes. `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`.
- The projection is a MODEL with measured inputs and one cited anchor, not a
  benchmark of a 10⁹-node graph (which is not built here). Reported as a
  projection with explicit assumptions, per the arc's honesty discipline.
