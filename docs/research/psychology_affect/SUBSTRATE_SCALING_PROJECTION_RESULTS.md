# Substrate scaling projection — RESULTS

**Block**: 302000. Pre-reg: `SUBSTRATE_SCALING_PROJECTION_PREREG.md`.
Measure/project: `scripts/substrate_scaling_projection.py`.

The user's question: *"investing X time and effort results in Y capability —
how much to get LLM-level capability, how many OoM of power/compute less is it
— and it never needs to be retrained, all improvements are additive."*

## Measured constants (this machine, single core)

| Constant | Value | Meaning |
|---|---|---|
| Memory per node | **~591 bytes/node** | linear in graph size (node + ~4 edges) |
| Fixed overhead | ~14 MB | interpreter + Rust `.so`, one-time |
| Inference latency | **~0.0065 ms/coherence-read** | flat 100→100k nodes |
| Inference slope vs N | **−3×10⁻⁹ ms/node ≈ 0** | LOCAL — does NOT grow with corpus |
| Distillation throughput | **~138,000 facts/sec** | single-thread ingest |
| Additive ratio (add/bulk) | **1.25 (~1)** | add-to-100k-graph ≈ bulk rate |

All four falsifiable claims **HOLD**:
1. **Linear memory** — stable ~591 B/node across the sweep.
2. **Flat local inference** — read latency slope ≈ 0; reasoning cost is
   `O(cues × degree)`, independent of total graph size.
3. **Additive marginal cost** — adding 1,000 facts to a 100k-node graph costs
   0.00906 ms/fact vs 0.00725 ms/fact bulk (ratio 1.25): size-independent, no
   retrain, no forgetting.
4. **OoM inference gap** — quantified below.

## The projection

Applying the linear-memory + flat-inference + additive constants:

| Scale | Facts | Cold disk | Hot RAM | Inference/step | Machine ingest |
|---|---|---|---|---|---|
| ConceptNet-class | 3.4M | 2.0 GB | MB-scale | ~0.007 ms | ~25 s |
| Wikipedia-fact-class | 100M | 59 GB | MB-scale | ~0.007 ms | ~12 min |
| LLM-coverage-class | 5B | 3.0 TB | MB-scale | ~0.007 ms | ~10 h (1 core) / ~19 min (32) |

**The decoupling is the result**: coverage grows linearly on COLD disk while
hot RAM stays MB-scale (cold-tier mmap, pay-per-miss) and per-inference cost
stays FLAT. In an LLM, coverage and per-token cost are welded into one dense
tensor; here they are separate axes.

## X → Y, and the OoM answer

**How many OoM less compute per inference:** Llama-3-8B ≈ 1.6×10¹⁰ FLOPs/token
(`2N`, estimate); a substrate coherence read ≈ 48 FLOPs (`O(cues × degree)`,
estimate). **≈ 8.5 orders of magnitude fewer FLOPs per inference step.**

**How much X to reach LLM-coverage (5×10⁹ facts):** machine ingest ≈ 10 h
single-thread (~19 min on 32 cores). But the honest X is **curation, not
machine time** — sourcing clean, non-contradictory, well-typed facts is the
real cost, and noise scales as cheaply as signal.

**Never retrained / additive:** reaching LLM-coverage is `+facts` at the
measured **size-independent 0.009 ms/fact**, never a retrain. Compare the
LLM anchor: absorbing new knowledge costs a fine-tune or a fresh training run
against the ~7.2×10²³ FLOPs (`6ND`, estimate) training budget. The substrate
adds knowledge with an append; the LLM repays a gradient bill.

## The honest ceiling (as prominent as the win)

- **Coverage ≠ capability parity.** Distilling 10¹⁰ facts buys MORE of the
  operations the substrate MODELS — compositional reasoning over EXPLICIT
  structure (coherence, analogy, CAN relaxation, knows-that/knows-what
  aperture). It does NOT buy the LLM's generative interpolation: fluent novel
  text, robustness to unseen phrasings, filling gaps the graph does not
  contain. The substrate reasons over structure it HAS; the LLM generates
  plausible structure it does not. This is a degree-not-kind boundary the
  designer CHOOSES where to draw — the arc's own principle — not a free lunch.
- **X is dominated by curation, not the measured machine time.** The 138k
  facts/sec bounds only the cheap machine cost.
- **The 8.5-OoM gap is per-STEP on modelled operations**, NOT
  capability-normalised. A coherence read and an LLM token are different units
  of work; the claim is "orders of magnitude cheaper per operation on the
  operations it models," not "N× cheaper for equal capability."
- **Extrapolation risk.** Measured to 100k nodes; the TB-scale rows are
  EXTRAPOLATED on the linear/flat constants. Real 10⁹-node graphs may hit
  degree-distribution, cache, and page-fault effects the sweep does not
  capture.

## Bottom line

The substrate today is a ~16 MB, sub-millisecond, deterministic, glass-box
reasoner. The measured constants project inference cost to stay **flat** and
per-step compute to sit **~8.5 OoM below** a small local LLM as coverage is
distilled up toward LLM-scale — so the efficiency win **widens** with scale
rather than closing, ON THE OPERATIONS THE SUBSTRATE MODELS, with all growth
ADDITIVE and no retrain. The catch, stated as plainly as the win: those
operations are compositional-over-explicit-structure, not the LLM's generative
manifold. The honest verdict is a radically cheaper reasoner over distilled
knowledge that COMPLEMENTS — not replaces — the generative model: spend the
expensive dense forward pass only when the cheap field read says a problem is
coherent and not yet localised.

## Verification
`.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246` (seed+python only, no Rust);
no CAN-internals / toolbox touched. This rung adds a pre-reg, a measurement/
projection script, and this RESULTS doc — no substrate behaviour changed.
