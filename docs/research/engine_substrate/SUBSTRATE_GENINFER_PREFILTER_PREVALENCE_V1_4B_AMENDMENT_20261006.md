# GenInfer prefilter v1.4 prevalence — v1.4b amendment (2026-10-06)

Disclosed before the v1.4b capture; no gate is relaxed.

## What happened

The first capture under the v1.4 preregistration (`v1_4a`, native SHA-256
`08cd0a322be577851880cb4bd1e28744b8e42a22b2c4c35a7c34b9f6398a7c64`) passed
G4/G6 on all 910 jobs: 910/910 on/off parity, zero validation mismatches. It
also showed that the remaining full-cost path in production-shaped inputs is
frames without an identity prefix and with equal relation counts: the
`sdloop_vision` 0°/90° and 45°/135° bar pairs still took 17–27 s per call, and
34/300 Omniglot `prod` pairs took 0.17–0.44 s. That capture is preserved
unchanged as
`evaluation/reports/geninfer_prefilter_prevalence_v1_4a_20261006.json`
(SHA-256 `c5496faae91e2eb573762f66f3b4a582b554605e06289ea71d513af83a83e6c8`)
with its console log.

## Change

A third exact stage, tried when the row-factorized search falls back:
correspondence-complete candidate generation. For any matrix the enumerator
accepts, the structural check forces predicate-preserving alignment, and the
per-slot uniform-delta rule forces one translation per predicate block, so
three source rows with independent displacements in one block map to three
target rows of that block. Enumerating the `n_p^3` target triples of the
smallest full-rank block therefore yields a superset of every accepted
matrix; each distinct in-bound integral hypothesis is judged by the
enumerator's own validator and ranked by the same Occam key. Per-predicate
block-count mismatch is an unconditional no-candidate proof. Frames with no
full-rank predicate block, or non-integer target coordinates, still use the
enumerator.

## Additions to the measurement

- G2 census adds three constant-identity families (non-unique prefix), so the
  correspondence stage is compared with the enumerator on exact, predicate-shift
  and single-row-perturbed targets.
- Scale series: `sdloop_vision.bar_frame` at 8, 12, 24, 32, 48 cells per side,
  pairs 0°/90° and 45°/135° (prefilter-off arm where the `(2b+1)^4` bound is at
  most 3·10^6).
- Output: `evaluation/reports/geninfer_prefilter_prevalence_v1_4b_20261006.json`.
