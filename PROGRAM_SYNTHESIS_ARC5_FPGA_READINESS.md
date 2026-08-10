# FPGA READINESS — the cognitive core is already integer

**Date:** 2026-08-01. Mechanical count over `runners/dsl/src/*.rs` (comment
lines stripped; `\bf32\b|\bf64\b` occurrences). Companion to
`PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md`, which classified 23 numeric sites
and found **zero** irreducible in-frame reals.

## Why this matters for fabric

- An IEEE-754 multiply-add costs DSP slices plus hundreds of LUTs and carries a
  long critical path (normalise / round / denormal). Integer ops map to native
  fabric and close timing trivially.
- No FP IP cores: no area, latency or licensing cost.
- **Bit-exact verification.** An integer design can be proven identical to its
  software model. Any deviation is a *signal*, not plausible rounding — which is
  exactly the property the Pentium FDIV bug destroyed (nineteen months in the
  field, across multiple product releases, because a wrong answer was
  indistinguishable from float noise).
- Power: the thermodynamic argument, realised.

## Measurement — float density by architectural role

| role | LOC | f32/f64 | per kLOC |
|---|---|---|---|
| CORE reflect | 1,810 | **0** | 0.0 |
| CORE quantize (`space_quantize.rs`) | 912 | **0** | 0.0 |
| CORE shape | 810 | **0** | 0.0 |
| CORE cycle (cognitive_cycle + reflex_runtime) | 648 | **0** | 0.0 |
| CORE terms (`term_variants.rs`) | 429 | **0** | 0.0 |
| **CORE rules** (rewrite + graph_rules) | 2,672 | **4** | **1.5** |
| CORE grammar (Γ + checker) | 185 | 1 | 5.4 |
| CORE substrate | 3,506 | 53 | 15.1 |
| CORE graph | 1,067 | 17 | 15.9 |
| **COGNITIVE CORE (total)** | **12,039** | **75** | **6.2** |
| DSL terms (term/prog_eval/synth_enumerate/jsonio) | 13,840 | 250 | 18.1 |
| CODEC & other | 23,709 | 838 | 35.3 |
| **BOUNDARY — PyO3 edge** | 8,113 | 419 | 51.6 |
| **DSP / metric** | 14,124 | 1,407 | 99.6 |

Whole crate: 71,825 LOC; 34 modules (19,237 LOC, 26.8%) contain **no float at
all**, including `cabac.rs` (3,241), `reflect.rs`, `space_quantize.rs`, the
h264 inter-prediction and macroblock paths, `shape.rs`, and `cognitive_cycle.rs`.

## Reading

**The floats are where the invariant says they belong.** Density rises
monotonically from core (6.2/kLOC) → DSL (18.1) → codec (35.3) → Python boundary
(51.6) → DSP/metric (99.6). The two highest are precisely the cross-frame
regions: the host boundary and the comparator/transform layer — class A in the
numerics audit, permitted by the invariant, and the analogue of an ADC/DAC edge.

**The rule engine — the thing that IS the agent — carries four float mentions in
2,672 lines.** Reflection, quantization, shape and the cognitive cycle carry
none.

**Consequence:** an FPGA target is not a port. The fabric-side subsystem —
typed graph, rule matching, Γ admissibility, N-dimensional quantization,
reflection, the tick/cycle scheduler — is already integer. What is float-heavy
is the host boundary (which does not cross to fabric) and the audio front end
(the genuine analogue edge — and the numerics audit found even the transform has
an exact form: the Number-Theoretic Transform, error-free integer convolution
already deployed on FPGA for lattice cryptography).

## Honest limits

- This counts **type mentions**, not dynamic float *use*; a module with zero
  `f32`/`f64` is strongly indicative but a full synthesis audit is a different
  exercise.
- `substrate.rs` (53) and `graph.rs` (17) are the two core clusters that would
  need individual review; small enough to audit site-by-site, not a rework.
- The DSL numeric tower (250 mentions) carries the `Float` `Value` variant —
  arc-2 Q1 added it, and `PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md` measured
  that **zero** MBPP tasks require it. That is the clearest candidate for
  removal rather than porting.
- Comment stripping is line-based (`//` prefix), so block comments are counted;
  this inflates rather than deflates the float counts, so the reading is
  conservative.
