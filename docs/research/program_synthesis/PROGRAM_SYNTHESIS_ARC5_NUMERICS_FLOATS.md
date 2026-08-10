# NO PROGRAM NEEDS FLOATS — tested on the strongest corpus available: this repo's own DSP stack

**Date:** 2026-08-01. `scripts/arc5_numerics_float_audit.py`, rows in
`results/arc5_numerics_float_audit.json`, gated by
`tests/test_arc5_numerics_audit_migrated.py` (19/19 green). Companion to
`PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md` /
`PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md`, which measured MBPP and
explicitly flagged its own limit: *"a numerics or signal-processing corpus
would very likely contain genuine in-frame reals... this result must not be
quoted as 'no program needs floats.'"* This is that test.

## The claim under test

The project author: **"No program needs floats. Many programs are specified
in ways that imply they need floats."** The substrate's own law (CLAUDE.md,
2026-07-08 frame/continuum invariant): in-frame is INTEGER; non-integer
structure is CROSS-FRAME, living in the map (`Hom(frame,frame)`), never as a
datum inside a frame; continuity is INTENSIONAL only (π is a rule you APPLY,
never a stored number); the identifiability guard — never encode precision
the steps cannot support.

## Verdict

# **UPHELD, WITH QUALIFICATION.**

Zero of 23 audited sites, across both corpora, are class **(D)** — a
genuinely irreducible in-frame real. The strong claim survives the strongest
test available (this project's own working DSP/vision/quantization stack,
not a toy benchmark). **But it is not vacuously true here**: three sites
(**c1-12**, **c1-14**, **c2-07**) are LIVE, currently-float, avoidable
in-frame quantities — the same "the spec implies a float, the problem does
not" pattern the MBPP audit found, now found inside this project's own code,
not just in a benchmark corpus. Report these as loudly as the confirmation:
**if this codebase is going to hold itself to its own invariant, these three
are where it currently doesn't.**

| | n |
|---|---|
| Total sites audited | 23 |
| Corpus 1 (this repo's DSP/shape/quantization stack) | 16 |
| Corpus 2 (classic numerics, named algorithms) | 7 |
| **(A) cross-frame / map — permitted** | **19** |
| **(B) in-frame datum — would refute** | **0** |
| **(C) avoidable in-frame float — defect, not requirement** | **4** |
| **(D) genuinely irreducible — WOULD refute** | **0** |

All 23 site-citations were mechanically re-verified against the actual
source text by the audit script itself (`results/arc5_numerics_float_audit.json`
→ `unverified_site_ids: []`) and independently spot-checked again in the
test file against raw file contents (not the script's own verifier) —
see the "Spot-checks" section below.

## Corpus 1 — this repo's own DSP / shape-verdict / quantization stack

### (A) Cross-frame maps — permitted, and mostly self-documented as such

| id | site | why it's a map, not a frame |
|---|---|---|
| c1-01 | `gammatone_band` (audio_primitives.rs:19) | filter render, sample array in/out, never a stored coordinate |
| c1-02 | `lpc_autocorr`/`levinson_durbin` (audio_primitives.rs:1451) | agent's own docstring calls this class "adapter-math (numeric DSP), NOT a composable DSL Term" |
| c1-03 | `cochleagram` (audio_primitives.rs:3709) | "a numerical primitive at the I/O boundary"; only a downstream *learned* artifact persists |
| c1-04 | `f0_yin` (audio_primitives.rs:3261) | pitch measurement — a rendering of samples to a scalar |
| c1-05 | `synthesize_klatt_lf` (audio_primitives.rs:891) | speech synthesis — textbook rendering |
| c1-06 | `DtwTo`/`PointSetDist`/`MahalFull`/`SmoothDeformDist`/`TpsDeformDist`/`ShapeContextDist`/`XCorrPeak`/`Whiten` (term.rs:6435) | comparator family — computed fresh per rule eval, consumed immediately by Argmin/Argmax, never `set_attr`'d |
| c1-07 | `TermNode::Rotate` (term.rs:6748) | rotates by a real angle; seed's own comment: "the cross-frame generator carrying the real angle as a Float, NEVER an in-frame coordinate" |
| c1-08 | `cp_angles` (seeds/continuous_pose.json:15) | a Float *parameter set* (the rotation grid), not an object position |
| c1-09 | `df_eps` (seeds/vision_deformation.json:15) | `sqrt(2)/2 / R` — an irrational constant intensionally applied, cached as a node attr **as a comparator tolerance**, not an identity coordinate |
| c1-11 | `quantize_signed_angle`/`quantize_bucket` (strokes.rs:112) | internal f64 geometry; every persisted relation is `.round() as i64` before it reaches a graph relation |
| c1-13 | `_peak_term` (formant_features.py:24) | order-only `Gt` predicate — invariant under any monotonic re-encoding, never exercises float *precision* |
| c1-15 | LPC/all-pole formant landmarks (lpc_formant_representation.py) | agent's own classification: "adapter-math... NOT a composable DSL Term"; only the peak's **integer band-index** persists, the continuous envelope is discarded |
| c1-16 | `warped_band_centres` (formant_frontend.py:21) | filter centre-frequency generator — a map parameter, like `cutoff_hz`/`sigma` |

**The single cleanest confirmation in the corpus: `runners/dsl/src/space_quantize.rs`
contains ZERO `f32`/`f64` literals or types** (independently re-grepped by
the test suite, not just claimed). The entire N-dimensional, foveated,
body-conditional quantization/flood/portal engine — the load-bearing spatial
reasoning of this whole project — is 100% integer. That is the invariant, in
production, at scale, with nothing held back.

### (C) Avoidable in-frame floats — the honest qualification

**c1-10 — `SpaceQuantum.qdist` typed `Value::Float`.** The one float in an
otherwise float-free file is a sentinel: `qdist` is a Bellman shortest-path
distance, always the sum of integer hop costs (`seeds/quanta_navigation.json`'s
own comment: *"cost (Int, always 1)"*), typed as Float purely to get a
`-1.0 = unset` sentinel distinct from a valid distance of `0`. An `Int` with
a `-1` sentinel would be identical in every observed run. Minor, cosmetic,
free to fix — flagged for completeness, not because it does any work a
float is needed for.

**c1-12 — acoustic band-energy attrs (`domains/acoustic_resolution.py:120`,
`substrate.set_attr(sign, f"band{n}_{i}", v)`).** This is the sharpest
candidate for a real counterexample in the corpus: raw mean cochlear-patch
energies, computed by NumPy as Python floats, are written **directly** as
node attributes on `AcousticSign` — an in-frame object — and read back by
predicate Term-trees (`domains/formant_features.py`'s peak detector,
`domains/discriminative_invention.py`'s Fisher rule) to decide **word
identity**. This is exactly the kind of continuous, ungrounded observation
the frame invariant says should be quantized (the way `StrokeQuantize`
quantizes ink pose into integer bins, or `TransformDecode` quantizes
rotation into an integer delta) — and it currently isn't. It survives as
class **C, not D or B**, for two reasons: (1) its only consumers are
**order-only** comparators (`Gt` for peaks; a ratio compared to a
threshold) that are invariant under any monotonic quantization — the exact
integer-bin treatment already given to pose/rotation elsewhere in this
codebase would work here unchanged; (2) the underlying quantity (a mean of
a bounded-precision digitized signal) is exactly representable as a
rational/fixed-point number with zero loss. Nothing about the *task*
(word discrimination) needs unbounded precision; the *implementation*
just hasn't been migrated to the discipline the rest of the perception
stack already uses.

**c1-14 — the Fisher-discriminant `sqrt` (`domains/discriminative_invention.py`).**
The sharpest live example found anywhere in this audit. `_stats` computes
`var ** 0.5` — a genuine square root, generically irrational even for
exactly-rational input data — and **persists it** as a `ConfusionBand` float
attribute. The agent's own graph-native Rule then evaluates it:

```python
fisher = Div(
    a=Abs(Minus(a=Attr(CB, "a_mean"), b=Attr(CB, "b_mean"))),
    b=Plus(items=(Attr(CB, "a_std"), Attr(CB, "b_std"), Lit(1e-6))))
...
Gt(a=fisher, b=Attr(Var("R"), "min_separation"))
```

This is a graph-resident Rule (fully CLAUDE.md-compliant as a *decision*)
making an in-frame identity decision — "is this acoustic band
discriminative" — off a persisted, individually-irrational quantity. It is
classified **C, not D**, because the *decision* the Fisher-style test makes
is an order test on a ratio, and the well-known reformulation that avoids
`sqrt` entirely,

```
(mean_a − mean_b)² · k²  >  var_a + var_b   (scaled appropriately)
```

makes the identical class of separability decision using only sums and
products of *variances* — exactly rational for rational inputs. `sqrt` here
is a **specification choice** (this particular Fisher-ratio formula), not a
requirement of "is this band discriminative." It is the MBPP `3.1415`
finding, reborn inside this project's own signal-processing code: the
*written test* implies a float; an *equivalent exact test* does not.

## Corpus 2 — classic numerics, judged by algorithm structure

| id | algorithm | verdict |
|---|---|---|
| c2-01 | Newton's method / root-finding (incl. **MBPP #246**, the Babylonian √, already live in this project's own measured corpus) | (A) — closed over ℚ at every step; the limit is an intensional Cauchy generator, never a stored real |
| c2-02 | Trapezoid / Simpson integration | (A) — a finite rational-weighted sum; precision-on-demand when f is transcendental |
| c2-03 | LU decomposition | (A) — Gaussian elimination is **closed over ℚ**: a rational input matrix has exactly-rational LU factors |
| c2-04 | QR (Gram-Schmidt) vs. `LDLᵀ` | (A) — Gram-Schmidt's `sqrt` is a *specification* choice (orthoNORMAL); `LDLᵀ` (Cholesky *without* the square root — a standard numerical-linear-algebra technique built specifically to avoid it) solves the identical problem over ℚ |
| c2-05 | FFT (complex roots of unity) vs. Number-Theoretic Transform | (A) — the fast-convolution *algorithm* doesn't need reals; the NTT computes the identical O(N log N) convolution over a finite field with **zero** floating-point error. The transcendental root is needed only when the genuine intent is cross-frame (sampling the continuous Fourier transform) |
| c2-06 | RK4 (ODE step) | (A) — a fixed rational-weighted sum of `f` at 4 rational points; closed over ℚ for rational `f` |
| c2-07 | Mean / variance / standard deviation | (C) — mean and variance are exactly rational; `sqrt` (std) is avoidable exactly as in c1-14 |

The Number-Theoretic Transform (c2-05) is worth dwelling on: it is the
single clearest existing proof, independent of this project entirely, that
"FFT needs floats" conflates an algorithm (fast structured convolution)
with one particular instantiation of it (sampling with transcendental roots
of unity). NTTs run in production today, error-free, throughout exact
polynomial arithmetic and cryptography.

## The sharp question, answered directly

**Does error accumulation over many iterative steps (Newton, FFT
butterflies, filter recursions) make in-frame REALS necessary, or does it
make PRECISION TRACKING necessary?**

**Precision tracking — not in-frame reals.** Every iterative algorithm
examined (Newton/Babylonian c2-01, RK4 c2-06, the LPC/Levinson-Durbin
recursion c1-02, the YIN/cepstral pitch search c1-04) is, at each step, a
closed rational operation on the previous rational state. What it converges
toward may be irrational, but the algorithm only ever needs the **sign of a
comparison** (has it converged; which side of a threshold) at some finite,
boundable precision — never the completed irrational value itself.

IEEE floating point answers that comparison with a fixed-precision bit
pattern and **no attached uncertainty** — a wrong answer is bit-for-bit
indistinguishable from a rounding-noise-perturbed correct one. This is
precisely the operational signature of the **1994 Pentium FDIV bug**: five
empty entries in a 1066-entry SRT lookup table produced wrong quotients at
the 4th–10th significant digit — exactly where float rounding error already
lives — and it shipped in millions of units for months because a wrong
result was statistically indistinguishable from ordinary float noise. It
was caught only because Thomas Nicely was computing twin-prime reciprocals,
a context with an **independent exact ground truth** to compare against.
Interval arithmetic (or exact rationals, or Boehm's constructive reals)
would have caught it immediately: a result outside the tracked interval, or
an exactly-wrong rational, is *obviously* wrong rather than plausible.

**Worked example, from this audit, of exactly this shape:** the
Fisher-discriminant site (c1-14) computes `std = sqrt(variance)` — one
Newton/Babylonian-style iterative square root — and persists it as a graph
attribute, then makes an in-frame identity decision
(`Gt(fisher, min_separation)`) off it. Rewritten in variance form, the
*identical* decision is made with **zero `sqrt` calls and zero irrational
intermediates**. The iteration was never necessary for the decision — only
for the (avoidable) std-shaped way the test happened to be written. Error
accumulation was never the reason a stored real was needed, because **no
stored real was needed at all.**

## Does this codebase itself track tolerance, or discard it like IEEE?

Asked directly, and answered honestly: **split.** The core DSP layer
(`audio_primitives.rs`'s gammatone/LPC/FFT/cepstral/YIN chain) uses only ad
hoc numerical-stability floors — `eps = 1e-10f32`, `1e-3f32` — guarding
divide-by-zero or log-of-zero. These are **not** tracked uncertainty; they
are IEEE-style, and a wrong F0 or formant estimate from this layer would be
indistinguishable from ordinary float noise, the same failure shape as
FDIV.

The vision/shape-decode **verdict** layer is different, and better:
`df_eps`/`cp_angles`'s `sqrt(2)/2` lattice-half-diagonal bound (c1-08/c1-09)
is a genuine, principled, *derived* tolerance — an explicit acceptance
interval falling out of the observation's own quantization grain — used not
just to accept but to **abstain**: `df_refused`, `ca_abstained`,
`"abstain_reason": "prior_invalidated"` are real, reachable graph states
(`seeds/vision_deformation.json`, `seeds/vision_cut_abstention.json`). That
*is* the interval-arithmetic discipline the FDIV story recommends, already
present in this codebase's newest layer. The older DSP layer has not
adopted it.

## Spot-checks (independent of the audit script's own verifier)

`tests/test_arc5_numerics_audit_migrated.py` re-derives, directly from raw
file contents (not trusting `verify_site`), four of the report's central
claims:

- `space_quantize.rs` really does have **zero** `f32`/`f64` occurrences
  besides the `qdist` sentinel (re-grepped independently in the test).
- `discriminative_invention.py` really does compute `var ** 0.5` and feed
  it through a `Div`/`Abs`-based Term-tree gated by
  `Gt(a=fisher, b=Attr(Var("R"), "min_separation"))`.
- `acoustic_resolution.py` really does `set_attr` a raw NumPy-mean float
  (not an already-quantized value) onto a graph node.
- `term.rs`'s `Rotate` evaluator really does return `Value::Float` pairs,
  and `continuous_pose.json`'s own comment really does call it
  "NEVER an in-frame coordinate."

19/19 tests pass; 0 unverified site citations.

## Honest limits

- Classification is a judgment call made by reading real code — this is an
  audit, not a decidable static analysis. What *is* mechanically checked:
  every cited file/line is real (re-verified against source, twice — once
  by the audit script, once independently by the test file), the class
  partition is exhaustive, and the (D) list is derived from the site table
  rather than hand-curated separately.
- Corpus 1 does not cover every numeric line in this ~37k-line Rust tree —
  it covers the DSP primitives, the shape/verdict comparator family, and
  the two quantization modules (`space_quantize.rs`, `strokes.rs`) the
  brief named, plus the Python-side sites where their outputs get
  persisted onto the graph (the acoustic band / Fisher pipeline). A
  differently-scoped sweep could surface more (C) sites; nothing found so
  far suggests a (D) site is hiding in the unswept remainder — the
  algorithmic pattern (closed-form rational recurrence; sqrt as an
  avoidable specification choice) recurs everywhere this audit looked.
- Corpus 2 sites are judged by algorithm structure and grounded in
  well-established results (ℚ-closure of Gaussian elimination; NTT as an
  exact FFT twin) rather than by inspecting an implementation in this
  repo, except where MBPP #246 (Babylonian √) already provides a live
  instance in this project's own prior measurement.
- "No genuinely irreducible in-frame real found" is a **negative result
  under a finite, honestly-scoped search**, not a proof that none exists
  anywhere in numerics. The strongest available corpus in this project —
  its own working DSP/vision stack — was searched specifically because
  that is where the author's claim would be expected to break if it were
  going to. It didn't. It came closest to breaking at c1-14, and even
  there, it was the SPECIFICATION (Fisher's classic sqrt-based ratio) that
  implied the float, not the underlying discrimination problem — the same
  finding, one level up, as the MBPP audit's `3.1415`.
