# Ratio invariance semantic correction — 2026-09-26

This correction supersedes the operational interpretation of H-R2 P3 and the
H-R1 phrase “the induced map, applied, collapses the population”. The original
probe confirms recovery of planted **within-frame extent ratios** and checks
that those ratios are consistent across frames. It does not apply a minted
map, and therefore does not establish a collapse, transform, or reusable
population-invariant representation.

## Reproducible counterexample

Run:

```sh
PYTHONPATH=.:runners/dsl/python python3 scripts/substrate_ratioinduce_semantics_probe.py
```

The runner records engine provenance and writes
`evaluation/reports/substrate_ratioinduce_semantics_probe_20260926.json`. On the
3:2 fixture, `RatioInduce` returns the relation `[slot=2,num=3,den=2]` and the
matrix `[1,0,0,3]`. The native `apply_linear_once` semantics multiply the y
extent by 3, producing y:x = 9:2 from the input 3:2. The denominator is not an
input to that application. This is a concrete semantic mismatch, not merely an
unmeasured property.

## Population meaning

The fixture frames have extents `(2s,3s)` for `s ∈ {1,2,3,5}`. RatioInduce
returns their common within-frame aspect ratio 3:2. It does not return the
between-frame scale factors, select a canonical frame, or construct a map
between members. Thus the implemented computation is a consistency check for
coordinate proportions, not the claimed population-scale induction capability.

## Corrected capability statement

- **Confirmed narrowly:** exact within-frame ratio extraction and cross-frame
  equality checking on the authored synthetic fixtures; tested non-matching
  controls are refused.
- **Contradicted:** treating the emitted non-power-of-two matrix as an
  application of the full recovered rational ratio.
- **Unestablished:** actual common-scale quotient/canonicalization, power-of-two
  inter-frame scale induction, seed-level invocation, durable minting, and
  held-out reuse.

The next implementation decision is to state whether the target is a rational
within-frame map or common-scale factorization across frames. Those are
different operations and need distinct output contracts and end-to-end gates.
See the source-linked [substrate audit](../../docs/research/engine_substrate/SUBSTRATE_RATIOINDUCE_CAPABILITY_AUDIT_20260926.md).
