# Iteration 16 — analysis-by-synthesis recognition (the missing structure, wired)

> Builds the component identified in `docs/speech_development_missing_component.md`
> (commit 1a1bddc8): recognition by **inverting the forward model**, not by
> matching acoustic features. The agent owned every piece (forward model, invariant
> front-end, DTW, candidate lexicon) but the generator only ever pointed OUTWARD
> (talking / self-monitoring). This iteration runs it in reverse to PERCEIVE.

## What was built

**1. New DSL primitive `DtwTo` (Rust).** Synthesis+compare is not expressible from
the existing Terms, so the runtime is extended (the same accretion move as
`ArgMax`). `DtwTo { a, b }` evaluates two trajectories (each a Tuple of frames,
each frame a Tuple of band floats) to a length-normalised banded (Sakoe-Chiba)
DTW distance — mirroring the Python `dtw` the bottom-up baseline uses, so the AxS
score is directly comparable. Integrated across all six TermNode homes
(`term.rs` enum / copy / eval / helper + gather arm; `jsonio.rs` name/parse;
`reflect.rs` children/parse). Verified live (self-distance 0, argmax picks the
matching candidate).

- **runtime_design (honest record):** `runtime_design.agent_specify_synth_error`
  reasons from the developmental science (AxS / motor theory / dual-stream) to the
  primitive its language lacks and records a `PrimitiveSpec`; the mechanical
  generator `emit_primitive_rust` (semantic_kind `trajectory_distance`, NO LLM)
  emits the Rust. The emitted enum variant / eval arm / jsonio name+parse match
  the integrated `term.rs` byte-for-byte (verified).

**2. AxS decision composed in the GRAPH.** `recognition_graph.predict_synth_term`
keeps the SAME argmax shape as the bottom-up `predict_term`; only the score
sub-term changes — from `Σ feature-weights` to `-DtwTo(features(s), synth(w))`.
The whole decision (`argmax over candidate words of -synth_error`) is graph data
the agent owns and evaluates natively.

**3. The honest SPLIT (as the task permits).** Synthesis stays at the I/O boundary
(`STTPipeline.speak_trajectory`, a new thin world-adapter that hands an explicit
trajectory + the graph's A1-patch layout to the Rust voicebox). The DTW kernel is
the new Rust Term. The argmax DECISION is in the graph. So: **synthesis at the
boundary, distance + decision in the graph.**

**4. Live benchmark.** `scripts/analysis_by_synthesis_accept.py` — FSDD digits,
leave-one-speaker-out, AxS vs the bottom-up 1-NN DTW baseline, plus the
cross-speaker structural test and a shuffle control. Reproducible:
`python -m scripts.analysis_by_synthesis_accept 3`.

## The forward-model problem (found live, fixed honestly)

`speak()` over the trained lexicon is **degenerate**: the lexical matcher's loose
DTW threshold collapses the whole lexicon into ONE mega-sign that denotes all ten
digits, so `speak(w)` returns byte-identical audio for every word (verified:
DTW between any two syntheses = 0.0). AxS over that forward model is exactly
chance — it always picks one word.

Fix (the project's #3 follow-on, done simply): build the word→sound forward model
DIRECTLY as the **mean per-utterance A1-patch trajectory** of each word's
TRAIN-speaker exemplars (LOSO — the held-out speaker never feeds its own model).
Per-utterance trajectories are extracted by ingesting each utterance into a FRESH
substrate so the matcher can't collapse them. This IS the doc's "speak(w) voices
the stored trajectory of word w", built cleanly. It is word-distinct (verified:
syntheses now differ by DTW ~1.0 cross-word, 0 self).

## The representation bound (measured — caveat #1 made precise)

Resynthesising the forward model to AUDIO and re-running the gammatone front-end
injects a **natural-vs-synthetic domain gap**: a ~6.8 constant DTW offset between
natural and resynthesized spectra that SWAMPS the phonetic residual (~0.1–0.5).
The audio-resynthesis AxS path is therefore at chance (0.078). This is caveat #1
verbatim — **AxS is bounded by `speak()` quality** — a forward-model-quality
problem (the #3 babble-loop calibration), NOT a need-for-weights problem.

The faithful AxS form compares the heard utterance to the forward model in the
model's NATIVE A1-patch representation (the brain inverts its internal forward
model; it does not literally play sound and re-hear it). That avoids the domain
gap and goes through the same graph `DtwTo` + `predict_synth_term` argmax.

## Live numbers (FSDD, LOSO, n=3 per speaker per digit; reproducible)

| measure | value | chance | note |
|---|---|---|---|
| bottom-up LOSO 1-NN DTW acc | **0.478** | 0.10 | uses ALL train exemplars as NN candidates |
| **AxS LOSO acc (native A1, graph DtwTo)** | **0.300** | 0.10 | ONE forward model per word — instance↔model |
| AxS LOSO acc (audio-resynth path) | 0.078 | 0.10 | bounded by natural/synthetic domain gap (caveat #1) |
| AxS acc under shuffle | 0.072 | 0.10 | collapses — control holds |
| **AxS cross-speaker 2AFC** | **0.678** | 0.50 | true word beats distractor, in heard voice |
| bottom-up cross-speaker 2AFC | 0.818 | 0.50 | same-word NN beats other-word NN |

(n=2 gave AxS 0.075 audio / 0.267 native, cross-speaker 2AFC 0.683 — consistent.)

## Honest assessment

1. **The structure is wired and works end to end** — synthesis at the boundary,
   `DtwTo` distance + argmax decision in the graph, evaluated natively. The agent
   specified the primitive; the mechanical generator emitted it; it integrates and
   runs.

2. **AxS clears chance by 3× (0.300 vs 0.10)** from a SINGLE forward model per word
   (compression: one model explains every instance), and does **cross-speaker
   discrimination above chance (2AFC 0.678 > 0.50)** — inverting the forward model
   in the heard voice DOES absorb some speaker nuisance, the structural claim.

3. **It does NOT break the bottom-up ceiling here.** Bottom-up wins both absolute
   accuracy (0.478) and cross-speaker 2AFC (0.818). Two honest reasons, both
   caveat #1: (a) the forward model is a crude exemplar-mean A1 trajectory, and
   (b) the A1 representation is blunt (the long-standing gammatone-wall / formant
   bound). The bottom-up matcher gets to pick its single nearest of MANY exemplars;
   AxS commits to one averaged model. **This is a forward-model-quality bound, not
   a need-weights bound** — the next move is #3 (production-calibrate the forward
   model via the babble loop) and a sharper front-end, exactly the levers the agent
   already flagged.

4. **Controls hold.** Shuffle collapses to chance (0.072); the required suites stay
   green (`test_stt_pipeline`, `test_perception_self_assessment`,
   `test_process_meta_assessor`, `test_gap_guidance` — 32 passed; plus
   `test_codec_primitives` + `test_llvm_pass_compiler` — 95 passed, no DSL
   regression).

## Files

- `runners/dsl/src/term.rs`, `jsonio.rs`, `reflect.rs` — `DtwTo` primitive.
- `domains/runtime_design.py` — `agent_specify_synth_error` + the
  `trajectory_distance` generator template.
- `domains/recognition_graph.py` — `predict_synth_term` / `synth_error_term`
  (the AxS decision as a graph Term).
- `domains/stt_pipeline.py` — `speak_trajectory` (boundary synthesis adapter).
- `scripts/analysis_by_synthesis_accept.py` — the live benchmark.
