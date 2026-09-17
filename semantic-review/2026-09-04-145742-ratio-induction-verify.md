# Independent verification: population-ratio-induction rung (`RatioInduce`)

Independent re-run of the `build-ratio-induction` stage against
`drafts/ratio_invariance/RATIO_INVARIANCE_PREREG.md` and CLAUDE.md's
frame/continuum invariant. I read the op's source myself, rebuilt the crate,
re-ran the existing regression gates, and re-executed all three harnesses on my
own machine. Every claim in `RATIO_INVARIANCE_RESULTS.md` reproduced — the
load-bearing H-R2 price check holds on my own read of the code, H-R1 recovers a
genuinely-planted ratio, H-R3 CASE A is a real audio body, the crate builds, and
the existing dim_infer/gen_infer/transform/provenance tests stay green (41
passed / 1 skipped). No invariant violation, no overclaim, no fabricated number.

**Watch for:** nothing blocking. One environment caveat (confirmed): `cargo test`
cannot link the Rust `#[cfg(test)]` unit tests in this tree because
`Cargo.toml` sets pyo3 `extension-module` unconditionally — a documented
pre-existing property, not introduced by this rung. The Rust op is exercised
through the shipped wheel via the Python migrated gates instead, which is the
stronger place (it tests the path that produces the numbers).

**Verdict: APPROVED**

## High-level view

H-R2 is the crux and it holds on a direct read. `eval_ratio_infer`
(`shape_decode.rs:3267`) reads every per-frame extent through `coord_ints`,
which still returns `None` on any `Float` slot; a float population therefore
returns `explained=false, n_frames=0` — refused, never induced from. All
arithmetic is `i64`/`i128` integer (gcd reduction + cross-multiplication, no
division, no float). The op never writes a coordinate back — frames are
byte-identical after the call. The induced object is a reduced integer pair
`num:den` reported as ratio triples, minted as `latent:scale2` (power-of-two) or
a diagonal integer `kind:"linear"` matrix that `apply_linear_once` already reads
— zero new dispatch arm. The continuous ratio lives intensionally in the pair;
the observable is the stepped integer rendering. The op does NOT store any
continuous in-frame state to work, so the price is near-zero and the invariant
is respected. H-R2 does not fail.

The invariant's enforcement point (`coord_ints`, `shape_decode.rs:643`) is
untouched: the only diff vs `main` is a rustfmt reflow of an `else` block; the
`Some(Value::Int(i)) => … _ => return None` body is byte-identical.

H-R1's ground truth is genuinely planted, not fitted-then-declared. The harness
constructs each frame's extents as `scale·ratio_den` (x) and `scale·ratio_num`
(y) with random per-frame scales and random interior fill, and hands the op only
the raw integer frames — never the ratio, never the scale. On my re-run all 5/5
planted ratios recovered exactly and scale-cancelled; the extent-break and
independent-axis controls floor (`explained=false`). Not rigged.

H-R3 CASE A is a real body: real synthesized glottal complexes, carrier F0
measured by the real Rust `f0_autocorr`, harmonic peaks independently peak-picked
from a real rFFT spectrum (not `k·F0` by hand), fed as integer frames. The op
recovers 2:1 across six speakers (F0 98→262 Hz) with the carrier cancelled. CASE
B (vowel formant F2:F1 via real Rust `allpole_ear` LPC) floors and is reported
honestly as the price boundary — front-end reliability (LPC jitter + an octave
error in `f0_autocorr` on one speaker), not the invariant.

Reuse is disciplined: the rung lives on the existing crate/wheel path (built via
`scripts/engine_build.sh`, engine `5ede696882e7`), wired as a Term exactly like
`GenInfer`/`TimeInfer` through `term.rs`, `term_variants.rs`, `jsonio.rs`,
`reflect.rs`; `py.rs` carries no `RatioInduce` reference (generic
`term_from_json` handoff). No fork.

<details>
<summary>Issues (2)</summary>

1. **`cargo test` unrunnable (pre-existing, not a regression)** — the Rust
   `#[cfg(test)]` unit tests can't link because pyo3 `extension-module` is set
   unconditionally in `runners/dsl/Cargo.toml`. This is documented in
   `scripts/scale_split_measure.py` and predates this rung. Rust behavior is
   covered through the shipped wheel by the Python migrated gates. No action
   required; noted so the green result isn't mistaken for a Rust-unit-test pass.
2. **Doc/harness scope for H-R4 (informational)** — H-R4 (EEG) is stated, not
   run, exactly as the prereg pre-committed (HBN-EEG unreachable). Not a defect;
   flagged only so a reader doesn't expect an EEG number.

</details>

<details>
<summary>Details</summary>

### H-R2 — the price check, on my own read of the op

The question the prereg gates on: does inducing-from-population REQUIRE storing
continuous in-frame state? If yes, H-R2 fails and the price is a
foundational-invariant violation. It does not.

Reading `eval_ratio_infer` (`shape_decode.rs:3267`) line by line:

- Extents are read via a closure that calls `coord_ints(frame, idx)` and returns
  `max − min` (`shape_decode.rs:3631`). `coord_ints` (`:643`) returns `None` on
  any non-`Int` slot, so a single `Float` coordinate makes the whole population
  inapplicable and the op returns the `unexplained` dict with `n_frames=0`. The
  float refusal is inherited, not re-implemented.
- The ratio is read as `gcd`-reduced integer pair from the frame with the
  largest reference extent (best-resolved observation), then VERIFIED across
  every frame by integer cross-multiplication `row[j]·den − row[ref]·num`
  compared against an integer tolerance `resolution·(num+den)` in `i128`. No
  float, no division producing a stored value.
- Frames are never mutated. There is no `set_coord` call in the op; the input
  `population` is only read. My P1 run confirms the frames are byte-identical
  after the call.
- The mint is a reduced integer pair reported in `ratios`; `latent:scale2` when
  the whole set is power-of-two (`scale_pow2_once` reads it), else a diagonal
  integer matrix routed through the existing `kind:"linear"` arm. The diagonal
  carries the numerator only — the denominator lives in the intensional ratio
  relation, consistent with "continuity is intensional only; its observable is
  the stepped rendering."

`apply_generator_once` diff vs `main` is a rustfmt signature reflow only — no
new `match` arm. So the "zero new dispatch arm" claim is verified, not just
asserted.

My re-run of `hr2_price.py`:

```
P1 relation-not-coordinate : True   (ratios=[2,3,2]; frames unchanged=True)
P2 in-frame stays integer  : True   (float pop -> explained=False, n_frames=0)
P3 ratio applied on read   : True   (3:2 -> latent:ratio matrix [1,0,0,3] all int; 4:1 -> latent:scale2)
P4 map is intensional      : True   (term re-evaluates to same ratio, no coord payload)
```

H-R2 PASSED on my own read and re-run. The build uses the invariant, it does not
fight it.

### H-R1 — planted ratio, on my own re-run

The plant is genuine: `make_frame(scale, ratio_num, ratio_den, seed)` builds a
box whose x-extent is `scale·ratio_den` and y-extent is `scale·ratio_num`, plus
random interior fill that does not change the extent. Per-frame scales are a
fixed list, random interior via seeded RNG. `induce()` passes only
`{"type":"RatioInduce","population":{"Lit": frames}}` — the op receives raw
frames, never the ratio or the scale. `apply_cancels_scale` verifies in integer
arithmetic that after mapping y through the recovered ratio every frame reduces
to a single per-frame scalar (the cancelled scale). This is a real recovery
check, not a re-declaration.

My re-run: 5/5 recovered exactly ((3,2),(5,1),(4,1)→scale2,(2,1)→scale2,(7,3)),
all scale-cancelled. Extent-break control → `explained=false`; independent-axis
control → `explained=false`; pure-translation stays explained with the same
ratio (the origin-normalized extent is translation-invariant by construction —
a common-mode shift is a nuisance a ratio should cancel, asserted explicitly as
a feature). Not a null; the confirmation is real.

### H-R3 — real audio body (CASE A) + honest price boundary (CASE B)

CASE A is not a synthetic in disguise. `synth_harmonic` builds a real glottal
complex; `N.f0_autocorr` (real Rust autocorrelation F0, `audio_primitives.rs:1771`)
measures the carrier; `spectral_peaks` reads the two lowest peaks from a real
Hanning-windowed rFFT magnitude spectrum and quantizes to a 10 Hz grid — it does
NOT compute `k·F0`. The op sees only the two integer peak frequencies per
speaker. My re-run recovered 2:1 across six speakers (F0 98.2→262.3 Hz measured),
`latent:scale2`, carrier cancelled — matching the RESULTS table peak-for-peak.

CASE B uses the real Rust `allpole_ear` (Levinson all-pole LPC,
`audio_primitives.rs:4194`) for formants. It floors (`explained=false`) and is
reported as the price boundary: the F2/F1 spread 1.757–1.850 plus a genuine
octave error in `f0_autocorr` on spk3 (92.5 Hz measured for a 185 Hz source)
exceed the observation resolution. The RATIO MACHINERY is sound (CASE A proves
it on a clean real signal); the cost is a noisy feature front-end, which is the
composed system's boundary, not the invariant's. Negative controls (mixed
ratios, different vowels) floor. This is honest usefulness-at-a-price in shape.

### Reuse discipline, build, regression

Built via `bash scripts/engine_build.sh` on the maturin/wheel path — engine
`5ede696882e7`, source fingerprint matches the RESULTS provenance line. The crate
compiles clean (warnings only, no errors). `RatioInduce` is wired as a Term
exactly like `GenInfer`/`TimeInfer`: `term.rs` (enum + doc + evaluate arm at
`:9888` + copy_subtree + child-collect), `term_variants.rs` (name + discriminant
167), `jsonio.rs` (type-name + to/from), `reflect.rs` (encode + reconstruct).
`py.rs` has zero `RatioInduce` references — the generic handoff carries it, as
claimed. No fork. `coord_ints` / `apply_generator_once` untouched but for
rustfmt.

Existing gates re-run by me on the rebuilt engine:

```
tests/test_dimension_inference_migrated.py
tests/test_gen_infer_migrated.py
tests/test_transform_decode_migrated.py
tests/test_engine_provenance_migrated.py
-> 41 passed, 1 skipped
```

Matches the claimed count exactly. No existing behavior moved.

</details>

<details>
<summary>File map</summary>

- `runners/dsl/src/shape_decode.rs` — new `eval_ratio_infer` (`:3267`); the
  invariant enforcement point `coord_ints` (`:643`) unchanged but for rustfmt.
- `runners/dsl/src/term.rs` — `RatioInduce` enum variant + evaluate dispatch to
  `eval_ratio_infer` + copy_subtree + child-collection.
- `runners/dsl/src/term_variants.rs` — name list + discriminant 167 (regenerated).
- `runners/dsl/src/jsonio.rs` — type-name + to_json + from_json.
- `runners/dsl/src/reflect.rs` — encode + reconstruct.
- `runners/dsl/src/py.rs` — no `RatioInduce` reference (generic handoff).
- `drafts/ratio_invariance/hr1_synthetic.py` / `hr2_price.py` / `hr3_audio.py` —
  the three harnesses, re-run and reproduced.
- `drafts/ratio_invariance/RATIO_INVARIANCE_RESULTS.md` — claims reconcile with
  my re-run.

</details>
