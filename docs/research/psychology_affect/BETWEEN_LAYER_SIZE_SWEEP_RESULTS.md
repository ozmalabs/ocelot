# Between-layer function across scale — CPU size sweep — RESULTS

**Block**: 308000. Pre-reg: `BETWEEN_LAYER_SIZE_SWEEP_PREREG.md`.
Measure: `scripts/between_layer_extraction_measure.py --sweep`.

The user: *"do it on the CPU — it is fine at this scale."* Done — the
between-layer extraction ran across the Qwen3 size sweep (0.6B/1.7B/4B) on CPU.
**Split verdict: claim 1 (fractional band scale-invariant) HOLDS; claim 2
(per-relation ordering scale-invariant) FAILS.** The honest negative on claim 2
is the important part.

## Measured (Qwen3 family, CPU fp32, same 10-prompt battery)

| Model | layers | resolved | resolution-frac band (mean) | delta-growth | time |
|---|---|---|---|---|---|
| Qwen3-0.6B | 28 | 8/10 | 0.82–1.00 (0.96) | 74.8× | 16 s |
| Qwen3-1.7B | 28 | 9/10 | 0.75–1.00 (0.85) | 189.3× | 25 s |
| Qwen3-4B | 36 | 9/10 | 0.81–1.00 (0.90) | 77.3× | 90 s |

CPU handled all three comfortably (faster load than GPU — no CUDA init).

### Claim 1 — the fractional resolution band is scale-invariant: **HOLDS**
Across 0.6B → 4B, facts resolve in the same mid-late FRACTIONAL band
(0.75–1.00 of the stack, mean 0.85–0.96), regardless of the absolute layer
count (28 vs 36). Delta-growth is large at every size (75–189×). So the SHAPE
of the between-layer function — little committed early, most committed in the
last ~15–25% of depth — is a stable fractional structure that does not depend
on model size. This is the robust finding.

### Claim 2 — per-relation ordering is scale-invariant: **FAILS**
The ordering of relation types by resolution depth DISAGREES across sizes:

| Model | ordering (earliest → latest resolving) |
|---|---|
| Qwen3-0.6B | capital < antonym < isa |
| Qwen3-1.7B | isa < antonym < morphology < capital |
| Qwen3-4B | morphology < isa < capital < antonym |

The neat "category-membership early, specific-recall late" ordering seen at
1.7B alone (block 307000) does NOT generalise — 0.6B puts isa LAST, 4B puts
antonym last. **Reported as a falsified claim**, not smoothed over. On this
tiny battery (1–3 prompts per relation) the ordering is not a stable
scale-invariant; the block-307000 ordering was a single-model artifact and
should not be over-read.

## Verdict

The between-layer function has a **scale-invariant SHAPE** (work committed
late, as a fraction of depth — claim 1) but its **fine structure (which
relation resolves when) is NOT scale-stable** (claim 2). The extractable,
robust cross-scale property is the fractional-depth commitment profile; the
per-relation depth ordering is model-specific and battery-sensitive.

This tempers block 307000 honestly: the depth-localisation of a fact is real
and recoverable per model, but "isa resolves before capital" is not a law — it
varied with size. The stable claim is the coarser one.

## Anti-faking / method
- Identical battery, readout, CPU device, fp32, across all three sizes — only
  size varies.
- Resolution depth as a FRACTION of the stack (comparable across layer counts).
- Both claims reported with outcomes; claim 2 reported FAILED.
- **default == today**: reuses block-307000's lazy-import external-venv torch;
  `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals /
  toolbox untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- ONE family (Qwen3), 3 sizes — within-family scale sweep, not a
  cross-architecture law (gemma gated/inaccessible).
- Small 10-prompt battery: per-relation orderings are 1–3 prompts each —
  underpowered, which is exactly why claim 2's instability should be read as
  "not established as stable," not "proven unstable."
- Logit lens is a qualitative trajectory probe, not calibrated per-layer
  probability.
