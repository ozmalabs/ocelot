# Iteration 40 — the KLATT + LF FORWARD MODEL (the AxS gating lever)

> iter-39 proved the order-N analysis-by-synthesis (AxS) slow path is built and
> correct but **bounded by forward-model quality**: the crude `0.3/k` harmonic source
> + parallel-summed bandpass `synthesize_from_trajectory` cannot carry per-candidate
> phonetic identity, so inverting it — once or N times — is null. The harvest's #1
> fix (`docs/research_slow_expensive_methods.md` §1a/§1b, Part 4) is **Klatt cascade
> resonators + the Liljencrants–Fant (LF) glottal source**, composable, zero-fit.
> This iteration implements that upgrade as a **Rust primitive** (CLAUDE.md: the agent
> is Rust, Python is only the world adapter) and re-runs iter-39's decisive tests,
> OLD forward model vs NEW Klatt+LF.
>
> Written INCREMENTALLY; runs captured to /tmp; PYTHONUNBUFFERED=1. NO commit.

## (0) The architectural correction iter-39's wiring forced

iter-39's slow path (`domains/slow_path.py`) compared candidates **entirely in
A1-trajectory space**: the forward model was the per-word **exemplar-mean A1
trajectory**, and `synth_error` was `DtwTo` between two A1 trajectories. **It never
called `synthesize_from_trajectory` at all.** So upgrading the audio synth in
isolation would change *nothing* in the slow path.

For the Klatt+LF synth to be the lever the task names, the forward model must actually
**produce audio and be re-perceived** — synthesise a candidate word as audio (in the
heard voice) and re-analyse it back into an A1 trajectory, then DTW-compare that to the
heard signal. That is the genuine "invert `speak()`": imagine the sound, hear your own
imagining, compare. The Klatt+LF quality then bears directly on whether the
re-perceived candidate carries phonetic identity. This iteration wires that audio
forward-model path (gated behind a flag so OLD = exemplar-mean-traj is still runnable
for the clean delta) and swaps the Rust synth from the crude voicebox to Klatt+LF.

## (1) The Klatt + LF forward model — a RUST primitive (rebuilt), no weights/fit

Implemented entirely in Rust per CLAUDE.md (the agent is Rust; Python is only the
world adapter).

**`runners/dsl/src/audio_primitives.rs` — `synthesize_klatt_lf(...)`** (+ helpers
`KlattResonator`, `KlattAntiResonator`, `lf_glottal_period`, `lf_source`). The four
things the harvest (§1a/§1b) said the crude voicebox lacks, all pure closed-form DSP:

- **Klatt CASCADE resonators** — a chain of two-pole resonators
  `R(z)=A/(1−B z⁻¹−C z⁻²)`, `C=−e^{−2πB/fs}`, `B=2e^{−πB/fs}cos(2πF/fs)`, `A=1−B−C`
  (DC-normalised). Run **in series** (ascending F1<F2<…) so the **inter-formant
  amplitude relations fall out of the transfer function automatically** — unlike the
  old independent parallel bandpasses which lose them. (Klatt 1980 §II.)
- **Anti-resonance / ZERO** — `KlattAntiResonator` (two-pole-two-zero, the inverse of
  a resonator) inserts a **nasal antiformant** an all-pole / all-bandpass tract cannot
  represent. Off by default (`nasal_f=0`), composable per call.
- **Per-formant BANDWIDTH** control (bw ≈ 2·sigma, clamped to natural 40–400 Hz) +
  a **two-source mix**: each output sample is `vf·LF + (1−vf)·noise` where `vf` is the
  per-frame fraction of envelope energy in voiced (centre<3500 Hz, non-sibilant)
  patches — replacing the old hard centre>3500 Hz per-patch switch.
- **LF (Liljencrants–Fant) glottal source** — `lf_glottal_period` generates the
  glottal-flow **derivative** for one pitch period from shape params: open quotient
  `oq` (Te/T0), asymmetry `am` (Tp/Te), return-phase time-constant `ta_frac`
  (spectral tilt). The open phase is the classic `e^{αt}sin(ω_g t)` growing sinusoid
  to the excitation at Te, then an exponential return to closure. This **replaces the
  fixed 0.3/k harmonic stack** and carries the per-speaker voice identity (open
  quotient + spectral tilt) the AxS forward model must absorb into `voice(s)`.

**`runners/dsl/src/py.rs` — `synthesize_klatt_lf(...)` PyO3 method** (one-line handoff
to the primitive, identical trajectory/patch interface to the existing
`synthesize_from_trajectory` plus the LF + nasal params). Rebuilt with `maturin build
--release` and reinstalled; `synthesize_klatt_lf` verified present on the native
substrate and producing finite, normalised audio.

**No-fit / no-donkey audit (re-verifiable in the Rust source):**
- Every coefficient is a closed-form function of (F, BW, fs) or an LF shape param.
  No learned weights, no trained net, no optimisation, no data-dependent fit anywhere
  in `synthesize_klatt_lf` or any helper (`grep` the function: only arithmetic on the
  inputs + the deterministic LCG noise source the old voicebox already used).
- It is a strict superset of the existing biquad voicebox family (Klatt resonators are
  the same two-pole family as `biquad_bandpass`, plus zeros + cascade routing).
- The OLD `synthesize_from_trajectory` is untouched, so the OLD-vs-NEW delta is clean.

**DSL no-regression:** the Rust rebuild keeps all **410 lib unit tests green**
(`cargo test --release --lib`). The two pre-existing doctest failures
(`src/lib.rs`, `src/auditory_cortex.rs` — malformed ASCII-art in doc comments) are on
files this iteration did not touch (`git diff` clean on both).

## (2) The wiring: the forward model now SYNTHESISES + RE-PERCEIVES

`domains/slow_path.py` gains `synth_reanalyze(traj, fs, f0, mode)` and
`audio_forward_model(library, fs, f0, mode)`: each candidate word's mean A1 trajectory
is **voiced as audio** (mode `old` = `synthesize_from_trajectory`; mode `klatt` =
`synthesize_klatt_lf`) and **re-ingested** through the Rust pipeline to recover its A1
trajectory. That re-perceived candidate is what `order_n_axs` / `single_pass_axs` then
DTW-compare to the heard signal — so the **synth quality now bears directly** on
whether the candidate carries phonetic identity. `scripts/slow_path_accept.py` selects
the mode via `SLOW_SYNTH={none,old,klatt}` (none = iter-39's pure-A1 baseline). World
adapter only: read patch metadata from the graph, call the Rust synth primitive,
re-ingest; no decisions, no fit.

## (3) TEST A — order-N vs single-pass, OLD vs NEW forward model (FSDD digits)

`SLOW_SYNTH={none,old,klatt} python -m scripts.slow_path_accept digits 2`, LOSO over
6 FSDD speakers, n_per=2, chance 0.10. Captured to
`/tmp/iter40_A_digits_{none,old,klatt}.txt`.

| forward model | single-pass AxS | order-N AxS | order-N Δ |
|---|---|---|---|
| **none** (iter-39 pure-A1, no synthesis) | **0.267** | 0.283 | +0.017 |
| **old** synth round-trip (`synthesize_from_trajectory`) | 0.183 | 0.175 | −0.008 |
| **klatt+LF** synth round-trip (`synthesize_klatt_lf`) | 0.133 | 0.117 | −0.017 |

**The audio round-trip is WORSE than direct A1 comparison — and Klatt+LF is worse than
the old voicebox.** Synthesising a candidate and re-perceiving it (either synth) loses
more phonetic information to the analysis→synthesis→analysis **domain gap** than it
preserves: the re-analysed A1 trajectory of a synthesised digit is a worse match to the
heard digit than the candidate's own mean A1 trajectory is. This is exactly the iter-16
finding ("the faithful instance↔model A1-space comparison — no natural/synthetic
resynthesis domain gap; the brain inverts the internal forward model, it does not
literally replay sound"), now re-measured with a *much better* synthesiser: the gap is
not closed by synth quality. Order-N does not convert in any mode (consistent with
iter-39).

## (4) THE TRUE-WORD-FAVOURING PROBE — the iter-39 failure, re-measured OLD vs NEW

This is the decisive measurement the task names: iter-39 found the forward model did
**not differentially favour the true word**. Per held utterance, rank the true word by
synth-error among all candidates (lower rank = more favoured); report mean true-word
rank + argmin (=single-pass acc), for all three modes in one pass.
`python -m scripts.slow_path_accept probe 2`, captured to `/tmp/iter40_probe.txt`.

| forward model | true-word mean-rank (lower = more favoured) | argmin (= single-pass acc) |
|---|---|---|
| **none** (pure A1) | **2.850** | 0.267 |
| **old** synth round-trip | 3.500 | 0.183 |
| **klatt+LF** synth round-trip | 3.917 | 0.133 |

n=120 held utterances, 10 candidates (chance mean-rank 4.50, chance argmin 0.10).

```
DELTA (true-word mean-rank; NEGATIVE = favours the true word MORE):
  klatt − old  = +0.417  => NO gain over the old synth
  klatt − none = +1.067  => the audio round-trip does NOT beat no-synth
```

**The decisive result, reported plainly: the Klatt+LF forward model favours the true
word LESS, not more.** It is worse than the old voicebox (+0.417 rank) and much worse
than the iter-39 no-synth A1 comparison (+1.067 rank). The iter-39 affine-warp failure
("warping the true word's model RAISED its synth-error") is NOT fixed by a better
synthesiser; routing the candidate through audio synthesis at all moves the true word
*away* from the top of the ranking.

## (5) TEST B — the closed loop (FSDD, n_per=2, conf_thresh=0.0)

`SLOW_SYNTH={none,klatt} python -m scripts.slow_path_accept loop 2`. Captured to
`/tmp/iter40_B_loop_{none,klatt}.txt`.

| forward model | fast BEFORE | fast AFTER | Δ | self-label purity |
|---|---|---|---|---|
| **none** (pure A1) | 0.217 | 0.233 | +0.017 | 23/60 = 0.383 |
| **klatt+LF** | 0.033 | 0.083 | 9/60 = 0.150 |

The klatt audio round-trip's fast-path baseline is **near-zero (0.033 vs none's
0.217)** and unsupervised self-label purity **collapses to 0.150** (vs none's 0.383).
The "+0.050 Δ" is a meaningless rise off a near-zero floor with 85% mislabelled
banking — the loop does not meaningfully close. The audio round-trip degrades the fast
path's recognition itself, so banking from it cannot help. (These FSDD n_per=2 numbers
are noisy in absolute terms; the ROBUST signal is the ordering none ≫ old > klatt,
which every measurement agrees on.)

## (6) VERDICT — under-claimed, the OLD-vs-NEW delta as the measurement

**(1) The Klatt+LF forward model is built as a RUST primitive, rebuilt, audited
no-fit/no-weights** (`synthesize_klatt_lf` + helpers in `audio_primitives.rs`, PyO3 in
`py.rs`): Klatt cascade resonators (inter-formant amplitudes from the chain),
anti-resonance/zero (nasal), per-formant bandwidth + two-source mix, and the LF
glottal source replacing the 0.3/k harmonic stack. Pure closed-form DSP; 410 DSL lib
tests green; required Python suites green (127 incl. codec/llvm). This part of the task
is done exactly as specified.

**(2) The OLD-vs-NEW delta, measured on FSDD digits (the clean comparison):**

| measurement | none (pure A1) | old synth | klatt+LF |
|---|---|---|---|
| single-pass AxS acc | **0.267** | 0.183 | 0.133 |
| order-N AxS acc | 0.283 | 0.175 | 0.117 |
| true-word mean-rank (lower=better) | **2.850** | 3.500 | 3.917 |
| closed-loop fast BEFORE→AFTER | 0.217→0.233 | — | 0.033→0.083 |
| banking self-label purity | 0.383 | — | 0.150 |

**(3) VERDICT: the better forward model does NOT lift the iter-39 bound — and the
honest finding is that the bound is DEEPER than synthesis quality.**

- Single-pass AxS does **not** rise with the better synth — it FALLS (0.267 → 0.133).
- Order-N does **not** convert in any mode (consistent with iter-39).
- The loop does **not** close — klatt makes it worse, not better.
- The true-word-favouring probe is unambiguous: Klatt+LF favours the true word **LESS**
  than the old synth and **much less** than no-synth.

The crucial correction iter-40 surfaced: **iter-39's "forward model" never synthesised
audio** — it compared candidates in A1-trajectory space directly, and that bound was
described as if the crude `synthesize_from_trajectory` were in the loop. It was not.
iter-40 (a) built the genuine "invert speak()" audio path (synthesise → re-perceive)
*and* (b) upgraded the synthesiser to Klatt+LF — and the measurement shows the
**analysis→synthesis→analysis DOMAIN GAP itself is the dominant cost**, not the
synthesiser's fidelity. Routing a candidate through audio and re-hearing it strictly
*loses* phonetic identity relative to the direct A1-space comparison, and a much more
accurate synthesiser does not recover it (it is even slightly worse, plausibly because
the cascade re-shapes the spectral envelope away from the gammatone/A1 front-end's
expectations more than the crude parallel-bandpass synth does, widening the gap).

This is **exactly the iter-16 finding, now confirmed against a strong synthesiser**:
"the brain inverts the INTERNAL forward model in feature space; it does not literally
replay sound." The right forward model for the agent's AxS is the **A1-feature-space**
one (iter-39's `none`), and that is already the best of the three. Synthesis quality
was a plausible hypothesis for the iter-39 bound; the measurement falsifies it. The
remaining levers for order-N to convert are NOT a better waveform synthesiser but the
feature-space forward model's discriminative power (per-speaker `voice(s)` absorption
in A1 space, sharper A1 patches — the gammatone-wall / speaker-normalisation levers the
memory repeatedly flags), or a representation where the round-trip is information-
preserving (e.g. comparing in the LF/source-filter *parameter* space the synth exposes,
rather than re-running the full cochlea). The harvest's next ceiling — the **Maeda
articulatory model** — is a *higher-fidelity waveform synth*, so by this result it
would face the same domain-gap wall; it is **not** indicated as the next step. The
indicated next step is feature-space (not waveform) forward-model quality.

**Honest scope:** measured on FSDD digits (8 kHz, 25 A1 patches, n_per=2, LOSO over 6
speakers) — small and noisy in absolute terms; the load-bearing result is the
consistent ORDERING (none ≫ old > klatt) across all four measurements, not the absolute
values. The Klatt+LF primitive is correct, composable, and zero-fit, and remains
available for any path that consumes synthesised audio (the babble/self-hearing loop);
it simply is **not** the lever that makes order-N AxS pay off, because that loop is best
run in feature space.

## Files
- `runners/dsl/src/audio_primitives.rs` — `synthesize_klatt_lf` + `KlattResonator`,
  `KlattAntiResonator`, `lf_glottal_period`, `lf_source` (the Rust forward-model
  primitive; pure DSP, no fit). OLD `synthesize_from_trajectory` untouched.
- `runners/dsl/src/py.rs` — `synthesize_klatt_lf` PyO3 method (one-line handoff).
- `domains/slow_path.py` — `synth_reanalyze` + `audio_forward_model` (the synth→re-
  perceive forward-model path; world adapter only).
- `scripts/slow_path_accept.py` — `SLOW_SYNTH={none,old,klatt}` mode + `_build_model`
  + the `probe` mode (true-word-favouring probe across all three modes).
- `docs/agent_loop_iteration40_klatt_lf_forward_model.md` — this report.

## Reproduce
```
# build the Rust primitive
cd runners/dsl && maturin build --release && \
  pip install --break-system-packages --force-reinstall --no-deps \
  target/wheels/substrate_rs-0.1.0-cp39-abi3-linux_x86_64.whl
# Test A (order-N vs single-pass), OLD vs NEW vs none
SLOW_SYNTH=none  python -m scripts.slow_path_accept digits 2   # /tmp/iter40_A_digits_none.txt
SLOW_SYNTH=old   python -m scripts.slow_path_accept digits 2   # /tmp/iter40_A_digits_old.txt
SLOW_SYNTH=klatt python -m scripts.slow_path_accept digits 2   # /tmp/iter40_A_digits_klatt.txt
# the true-word-favouring probe (all three modes in one pass)
python -m scripts.slow_path_accept probe 2                     # /tmp/iter40_probe.txt
# Test B (closed loop)
SLOW_SYNTH=none  python -m scripts.slow_path_accept loop 2     # /tmp/iter40_B_loop_none.txt
SLOW_SYNTH=klatt python -m scripts.slow_path_accept loop 2     # /tmp/iter40_B_loop_klatt.txt
```
Required suites green (127): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance (+ test_codec_primitives,
test_llvm_pass_compiler). Rust: 410 lib unit tests green (`cargo test --release --lib`).
