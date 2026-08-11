# The DTW temporal-alignment recognizer is the biggest single cross-speaker jump

**Question.** The cue levers are exhausted (`docs/dynamic_invariant_loso.md`,
`docs/allpole_vtl_loso.md`): CMVN + the sharp all-pole VTL formant + the order-N
dynamic land real 40-speaker cross-speaker LOSO at **~0.42** (chance 0.10), and the
absolute rate is still far from solved. That doc **named the next structure** — NOT a
richer per-frame feature, but the **RECOGNIZER**: the per-frame readout collapses each
clip to an unordered **bag** of feature values and throws the **temporal STRUCTURE**
away. The gesture is a **TRAJECTORY** (a path), not a bag — the way F2 sweeps into a
vowel, the way the spectrum moves through the word, is a speaker-invariant **motion**
matched by **alignment**, not by an order-free descriptor. So the next lever is a
**DTW alignment** over the trajectory, which "is where order-N-over-time wants to
live."

This run builds exactly that and A/Bs it on the **identical** robust SC split.

**Verdict: YES — the DTW temporal-alignment recognizer is the largest single
cross-speaker lift measured, and it is the recognizer ARCHITECTURE, not a new
feature.** Aligning the source-normalized (CMVN) spectral trajectory as a *path*
instead of reading it as a per-frame bag lifts real 40-speaker cross-speaker LOSO from
**0.417 → 0.570 (+0.152 absolute)** — bigger than CMVN (+0.043), the sharp VTL
(+0.005), and the order-N dynamic (+0.008) **combined**. The lift is **purely the
alignment**: on the **identical** trajectory feature read as an unordered bag the rate
is 0.420 (no better than the 6-cue bag), and adding *only* the DTW path-alignment
takes it to 0.570 (**+0.150 isolated**). The per-frame bag was leaving the single
biggest piece of cross-speaker structure — the temporal ORDER of the gesture — on the
floor. It does **not** solve recognition (0.570, residual 0.430 from 1.0), but it is
the structural jump the doc predicted, and it is the recognizer, not the ears.

---

## (1) The DTW recognizer is the agent's GRAPH-RESIDENT decision (donkey-audited)

The agent already owns a DTW primitive: **`DtwTo`** — a Rust Term
(`runners/dsl/src/term.rs`: `TermNode::DtwTo` → `banded_dtw`, the Sakoe-Chiba banded
alignment cost, the same kernel `recognition_graph.predict_synth_term` composes for
analysis-by-synthesis). It takes two trajectory attrs (each a tuple-of-frames, frame =
tuple-of-channels), aligns them under a banded warp, and returns the path cost
normalised by length — accepting **variable-length** sequences (the warp is what makes
that work). Verified directly: a warped-but-identical pair → 0.0, a far pair → 6.57.

The recognition DECISION is composed entirely from the agent's owned ops and evaluated
**natively**:

```
predict(query) = Argmin  over  w ∈ is_word Concepts  of
                   MinOver  e ∈ has_exemplar(w)  of  DtwTo(query_traj, traj(e))
```

`DtwTo` (the alignment), `MinOver` (the nearest banked exemplar of the word), `Argmin`
(the word decision), over the agent's OWN word Concepts and banked Exemplars — one
`substrate.evaluate` call per query, the whole recognizer in Rust. This is the same
shape as `blind_guess`'s Argmax-of-product and `recognition_graph.predict_term`'s
Argmax-of-score; only the per-word distance changed from "1-NN cosine over a bag" to
"min-DTW over the trajectory."

**Donkey boundary (audited).** The DECISION is the graph Term above (no Python
recognizer — the query/exemplar trajectories are written as graph attrs and the
Argmin-of-MinOver-DtwTo Term picks the word). The TRAJECTORY is the agent's
composable-DSP **feature**: `agent_frontend.cmvn_track` is the SAME per-utterance
CMVN cochleagram the dominant `cmvn_ear` cue is built from (per-band mean-and-variance
normalization), kept as an **ordered** per-frame sequence (each frame L2-normalized to
its spectral shape) instead of L2-flattened into a patch bag;
`agent_frontend.vtl_formant_track` is the SAME sharp LPC-root formant + `F_i -
mean(F1..F3)` VTL invariant the dynamic cue uses, kept ordered (+ order-1 velocity
channels). NO fit, NO trained net, NO learned weight. SC load + the speaker split are
world-adapter mechanics; LOSO is the ungameable yardstick; **held-out speakers' clips
are NEVER banked**.

## (2) The A/B on the SAME robust SC LOSO — VERDICT

`scripts/dtw_trajectory_loso.py` reuses `sc_loso_frontend_norm.build_split` / `bank` /
`measure` verbatim (120 train / 40 held-out **disjoint** speakers, 200 banked
exemplars, 200 seen-speaker probes, 400 cross-speaker LOSO probes, full-lexicon). Three
regimes:

- **BAG(6-cue)** — the per-frame `blind_guess` on the static+dynamic best front end
  (CMVN + sharp-allpole VTL + the order-N dynamic), the **~0.42 baseline** from
  `docs/dynamic_invariant_loso.md`. UNCHANGED.
- **TRACK-BAG** — the SAME trajectory feature the DTW recognizer reads, but COLLAPSED
  into the per-frame **bag** (resample each channel to fixed length, L2-flatten, 1-NN)
  — the **feature-matched control** that isolates temporal alignment from feature
  choice.
- **DTW-TRAJECTORY** — the agent's `Argmin MinOver DtwTo` recognizer over the ordered
  trajectory.

### The decisive run — the CMVN spectral trajectory (the rich feature the bag wins on)

```
                                          (10-way, chance 0.100)
  regime          seen    LOSO   seen-LOSO gap
  BAG(6-cue)     0.450   0.417       +0.033     (per-frame blind_guess, static+dynamic best)
  TRACK-BAG      0.405   0.420       −0.015     (SAME trajectory feature, order discarded)
  DTW-TRAJECTORY 0.625   0.570       +0.055     (Argmin MinOver DtwTo over the trajectory)
```

Reading the decisive comparisons:

- **DTW vs the SAME feature as a bag: +0.150 LOSO** (0.420 → 0.570). This is the
  **isolated temporal-alignment effect** — same per-frame features, the ONLY
  difference is that DTW aligns them as a *path* while TRACK-BAG reads them
  order-free. The temporal ORDER of the spectral gesture carries +0.150 of
  cross-speaker structure the bag cannot see.
- **DTW vs the 6-cue per-frame bag (absolute): +0.152 LOSO** (0.417 → 0.570). The DTW
  recognizer over the single CMVN trajectory **beats the full 6-cue fusion** — it is
  the **biggest single lift in the whole programme**, larger than CMVN (+0.043) + sharp
  VTL (+0.005) + dynamic (+0.008) **combined** (those three are static cues over the
  bag; this is the bag itself replaced by alignment).
- **TRACK-BAG ≈ BAG.** The CMVN trajectory read as a bag (0.420) is no better than the
  6-cue bag (0.417): as an unordered descriptor the rich spectral trajectory carries
  no more than the existing cues. **All** of its extra power is in the temporal order
  — which only the DTW alignment unlocks. This is the cleanest possible statement that
  the lever was the **recognizer**, not the feature.

### The formant trajectory (a thinner feature) — alignment helps, feature too thin

The same A/B over the VTL formant trajectory (3 formants + velocity = 6 channels)
instead of the ~50-band CMVN spectrum:

```
  regime          seen    LOSO   seen-LOSO gap
  BAG(6-cue)     0.450   0.417       +0.033
  TRACK-BAG      0.145   0.158       −0.013     (formant trajectory as a bag)
  DTW-TRAJECTORY 0.300   0.253       +0.047     (formant trajectory aligned)
```

- **DTW vs the same formant-feature bag: +0.095 LOSO** (0.158 → 0.253). Alignment
  helps here too — the temporal order of the *formant* gesture is real cross-speaker
  structure (the order-N dynamic doc's intuition, now matched as a path).
- **But the formant-only trajectory is too thin** to beat the 6-cue bag: DTW 0.253 vs
  BAG 0.417 (−0.165 absolute). 3 formants + velocity is a far sparser feature than the
  full CMVN spectrum, and the LPC formant track is noisy on 8 kHz SC clips (the
  `dynamic_invariant_loso` doc's bound: "many frames find < 3 clean poles"). The lever
  is the recognizer **applied to a rich enough trajectory** — alignment over the CMVN
  spectrum, not over a thin formant triple.

The two together make the point precisely: **DTW alignment lifts the same feature
whatever the feature** (formant +0.095, CMVN +0.150), but it only beats the 6-cue bag
when the aligned trajectory is the rich CMVN spectrum the bag already used.

### Does it solve cross-speaker recognition?

**No — it is the biggest single jump toward it, and it identifies the recognizer as
the remaining lever, but a large residual stands.** DTW-trajectory LOSO is **0.570**
(chance 0.100); the residual to solved (1.0) is **0.430**. What the run proves is that
the per-frame bag — every front-end run so far — was discarding the single largest
piece of cross-speaker structure (the temporal order of the gesture), and recovering it
by alignment is worth more (+0.152) than every static source-normalization cue
combined. What remains beyond temporal alignment of one trajectory: (1) **richer /
fused trajectories** aligned jointly (CMVN + formant-dynamic as a multi-stream DTW, not
one or the other); (2) a **sharper trajectory** (pitch-synchronous framing, a real
formant *tracker*) so the path the DTW aligns is less blurry; (3) the deeper
cross-speaker variation (lexical / register / coarticulation diversity) that no
single-utterance exemplar bank fully cancels. The next structure is no longer "the
recognizer throws away order" — that is now fixed — but **what trajectory** the agent
aligns and **how many exemplars** define each word's manifold.

## (3) Why the alignment is worth so much (honest)

The per-frame bag (1-NN cosine over an L2-flattened, time-resampled descriptor) sees a
clip as an unordered cloud of frame-features. Two speakers saying the same digit
produce the same **sequence of spectral states** but at different rates, with different
absolute timing and different per-frame detail; the bag's fixed-length resample +
cosine smears those into a blurry average where cross-speaker nuisance and
phonetic identity are entangled. DTW instead finds the **optimal monotone alignment**
between the two paths — it warps out the rate/timing nuisance and scores the residual
**shape of the gesture**, which is exactly the speaker-invariant part (the articulatory
trajectory is the same motion in every mouth, only re-timed). That is a classical
pre-HMM ASR result (template DTW beats raw template cosine); the finding here is that
on the agent's own source-normalized trajectory, in its own graph-resident `DtwTo`
recognizer, on real held-out speakers, it is the **dominant** cross-speaker lever — and
that the whole front-end-cue programme had been measuring against a recognizer that was
the bottleneck.

The donkey boundary held throughout (section 1): the trajectory is the agent's owned
DSP, the DTW + Min + Argmin decision is the agent's graph Term evaluated in Rust, and
the held-out speakers are never banked.

## Reproduce

```
python -m scripts.dtw_trajectory_loso                       # formant trajectory (120/40/20)
DTW_TRAJ=cmvn python -m scripts.dtw_trajectory_loso         # the CMVN trajectory (the +0.152 run)
DTW_TRAJ=cmvn python -m scripts.dtw_trajectory_loso 12 6 5  # fast smoke run
```

Full captured output: `/tmp/dtw_trajectory_loso.txt` (formant) and
`/tmp/dtw_trajectory_cmvn_loso.txt` (CMVN, the decisive run). Both end with the
`[MARKER] DTW_TRAJECTORY_LOSO_COMPLETE` line; both runs were pgrep-verified to
completion. Required suites green (`test_stt_pipeline test_perception_self_assessment
test_process_meta_assessor test_gap_guidance test_frontend_effect_gate` — 36 passed).
Nothing committed; `agent_frontend.cmvn_track` / `agent_frontend.vtl_formant_track` +
the A/B script are left in the working tree.
