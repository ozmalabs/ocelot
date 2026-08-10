# Iteration 39 — the SLOW PATH (order-N analysis-by-synthesis replay-and-learn)

> User insight: "humans have a slow path — I play back speech in my head, parse it
> much better, learn the structure, and bank it; we need THAT machinery." This is
> the agent's OWN flagged missing structural component — order-N analysis-by-synthesis
> ([[ozma_order_n_analysis_by_synthesis]]). The FAST path (the cue-graph, iters 33-38)
> recognises in real time from the banked library; the SLOW path BUFFERS an utterance,
> REPLAYS it, PARSES it deliberately via ORDER-N AxS, LEARNS the structure, and BANKS
> it into the library. iter-35 built the SINGLE-PASS AxS as a fast node; the slow path
> WRAPS that in the order-N iteration + learn-and-bank.
>
> Written INCREMENTALLY; runs captured to /tmp; PYTHONUNBUFFERED=1. NO commit.
> Required suites green (32 + 95 DSL = 127). Builds on iter-35 (the single-pass AxS
> node) and iter-36 (AxS flips complementary on continuous).

## (1) The slow-path loop wired — the agent's owned order-N + AxS + library, no fit

`domains/slow_path.py` (the owned machinery) + `scripts/slow_path_accept.py` (the
world-adapter driver + the decisive tests). The loop:

1. **REPLAY.** Re-present a buffered utterance as its A1-patch trajectory — the SAME
   extraction the fast AxS node uses (`enriched_hvpt_accept.utterance_a1_trajectory`,
   ingest into a fresh substrate, read the AcousticSign trajectory). The buffer is the
   held utterance.
2. **ORDER-N AxS PARSE** (`slow_path.order_n_axs`). Pass 1 = the single-pass
   hypothesis (heard trajectory vs the per-word MEAN forward model — the iter-35 node,
   here the order-0 of the iteration). Each further pass RE-SYNTHESISES from the
   current best hypothesis adapted toward the heard signal: the candidate forward
   model is WARPED toward the buffered trajectory via a DAMPED step (`_voice_warp`,
   step=0.5) — boundary co-refinement (DTW-style linear re-grid to the heard length) +
   voice co-refinement (a GLOBAL affine gain+bias = level/spectral-scale = the voice
   channel, re-generating the hypothesis IN THE HEARD VOICE) — then the graph `DtwTo`
   synth-error is recomputed and re-ranked over candidates. The damped step makes it
   an ITERATED refinement that accumulates per candidate across passes; word + voice +
   boundary co-refine jointly each pass.
3. **STOP = the agent's order_n FIXED POINT.** The order-1 finite difference of the
   running best synth-error (`order1_diff`, mirroring `order_n_concepts.nth_order_terms`
   at order 1 on the scalar error sequence) falls within a convergence band, or n_max.
   **n scales to difficulty** — this IS "n passes scaling to difficulty."
4. **LEARN + BANK** (`slow_path.learn_and_bank`). The confidently-resolved trajectory
   becomes a new exemplar of its (self-parsed, UNSUPERVISED) word in the library; the
   forward model rebuilt from the grown library is what the fast path reads.
   Retain-don't-discard.

**No-fit / no-donkey audit (re-verifiable):**
- The AxS distance is the graph `DtwTo` Term (`recognition_graph.synth_error_term`,
  evaluated natively in Rust) — the SAME distance the fast AxS node uses.
- The forward model is the exemplar mean per word (no fit, no weight, no convergence net).
- The order-N iteration is the agent's order_n operator's order-1 fixed point — no
  trained stop. Verified `single_pass_axs == order_n_axs(max_n=1)` (identical path).
- The voice warp is a closed-form SINGLE affine over ONE utterance (no global fit
  across utterances; gain clipped to [0.5, 2.0] so it adapts the voice but cannot
  collapse a candidate onto the heard signal — verified `_voice_warp` changes the
  synthesis and preserves per-patch structure).
- The learn-and-bank retains the trajectory — no gradient, no net.
- The softmax is `many_settings_recognizer.likelihood_from_distances` (median-distance
  temperature, the identical no-fit softmax every channel uses).

## (2) TEST A — order-N vs single-pass + the n-vs-difficulty curve

Driver: `scripts/slow_path_accept.py {digits,continuous}`. Two venues: FSDD digits
(EASY control — iter-35 found AxS redundant here) and continuous cross-speaker
gold-span words (HARD — iter-36 found AxS flips complementary). LOSO over speakers.
`max_n=10`, `conv_band=1e-4`. Captured to `/tmp/iter39_testA_{digits,continuous}.txt`.

### FSDD digits (EASY control, n_per=4, LOSO over 6 speakers, chance 0.10)

| measure | value |
|---|---|
| SINGLE-PASS AxS acc | **0.304** |
| ORDER-N AxS acc | **0.300**  (Δ −0.004, neutral) |
| pass-cap sweep (acc @ exactly k passes) | @1 0.304 · @2 0.308 · @4 0.300 · @8 0.300 |
| n-vs-difficulty (mean auto-stop passes) | HARD 4.66 vs EASY 4.45 → **harder uses MORE passes** |
| recover/break on single-pass failures | recovers 6/167 (0.036), breaks 7 → net **−1** |

### Continuous cross-speaker gold-span words (HARD, 8 speakers, 12-word vocab, chance 0.083)

vocab `and been for had his not that the was with would you` · 467 clips.

| measure | value |
|---|---|
| SINGLE-PASS AxS acc | **0.171** (2.1× chance) |
| ORDER-N AxS acc | **0.171**  (Δ +0.000, neutral) |
| pass-cap sweep | @1 0.171 · @2 0.176 · @4 0.169 · @8 0.169 |
| n-vs-difficulty | HARD 4.69 vs EASY 4.74 → no clean pass-scaling on auto-stop |
| recover/break on single-pass failures | recovers 8/387 (0.021), breaks 8 → net **+0** |
| per-fold order-N vs single | helps 5 folds (1462 +0.021, 2277 +0.014, 6313 +0.036, 777 +0.014, …), hurts 2 (2428 −0.034, 3081 −0.062) |

**TEST A verdict: order-N does NOT beat single-pass on EITHER venue (Δ −0.004 digits,
+0.000 continuous).** The n-scaling MECHANISM works (the order_n fixed-point DOES use
more passes on hard digits — 4.66 vs 4.45 — and the pass-cap sweep peaks at 2 passes,
showing the iteration is doing something), but the EXTRA passes do NOT convert: more
passes do not monotonically raise accuracy, and recoveries on single-pass failures are
balanced by breaks (net −1 / +0).

**WHY (the forward-model bound, made precise — diagnostic):** the global-affine warp
adapts ALL candidates' level/spectral-scale toward the heard voice EQUALLY, so it does
NOT differentially favour the true word. Measured on a held utterance: warping the
TRUE word's model RAISED its synth-error (0.0841 → 0.0845) — the affine shifts
level/scale but not the phonetic SHAPE that distinguishes words. This is exactly the
known order-N caveat: **AxS is bounded by the forward-model / `speak()` quality**
(iter-16 caveat #1; iter-35). The order-N iteration cannot extract phonetic identity
that the exemplar-mean forward model + a global affine warp do not carry. A genuine
articulatory re-synthesis in the heard voice (the babble-loop-calibrated forward model
the agent has long flagged) is the lever that would let order-N pay off — not present
here.

## (3) TEST B — the closed loop (does banking improve the fast path?)

Driver: `scripts/slow_path_accept.py loop`. Per LOSO fold the held-out speaker's
utterances split into a SLOW-LEARN half and a FAST-TEST half. The fast path's AxS
recognition is measured on the test half BEFORE banking (library = train exemplars
only) and AFTER the slow path replays the learn half via order-N AxS and BANKS the
confidently-resolved trajectories UNSUPERVISED (under its OWN parse label, gated by
parse confidence). Captured to `/tmp/iter39_testB_loop{,_gated}.txt`.

| config (FSDD n_per=4, LOSO over 6 speakers) | fast BEFORE | fast AFTER | Δ | banked | self-label purity |
|---|---|---|---|---|---|
| bank ALL parses (conf_thresh 0.0) | 0.358 | 0.300 | **−0.058** | 120/120 | 33/120 = 0.275 |
| confidence-GATED (conf_thresh 0.15) | 0.358 | 0.333 | **−0.025** | 40/120 | 18/40 = 0.450 |

**TEST B verdict: the loop does NOT close on FSDD — banking the slow path's parses
HURTS the fast path.** The confidence gate raises self-label purity (0.275 → 0.450)
and roughly halves the damage (−0.058 → −0.025), but even at 0.45 purity the banked
exemplars are >50% mislabelled, so they POLLUTE the per-word forward model rather than
sharpen it. The closed loop is bounded by the same thing as Test A: **slow-path PARSE
QUALITY.** Because the order-N parse is no better than single-pass (Test A) and only
~45% pure even when confident, unsupervised banking degrades the library. A loop that
banks correct structure REQUIRES a parse accurate enough that confident parses are
mostly right; that accuracy is the forward-model lever Test A also identified.

## (4) VERDICT

**The order-N AxS replay-and-learn MACHINERY is built and runs end-to-end** — the
agent's flagged missing structural component (order-N analysis-by-synthesis learning
machinery, [[ozma_order_n_analysis_by_synthesis]]) now EXISTS as owned, no-fit code:
REPLAY (re-ingest the buffered A1 trajectory) → ORDER-N AxS PARSE (the iter-35
single-pass AxS wrapped in the agent's order_n fixed-point iteration, co-refining
word + voice + boundary via the graph `DtwTo` Term, n scaling to difficulty) → LEARN
(self-parse a confident word) → BANK (retain the exemplar into the library the fast
path reads). The two-path wiring is complete; audited no-fit, no trained net, no
select-best, no global weight; single-pass == order-N@1 verified; required suites green.

**But neither decisive measurement pays off — reported plainly, under-claimed:**
- **(A) order-N does NOT parse better than single-pass** (digits Δ −0.004, continuous
  Δ +0.000). The n-passes-scaling mechanism functions (harder digits use more passes;
  the pass-cap sweep peaks at 2), but the extra passes do not convert to accuracy.
- **(B) the closed loop does NOT close** (banking hurts the fast path: −0.058 ungated,
  −0.025 gated) because the slow-path parse is not accurate/pure enough to bank.

**The single bound behind both (the honest residual):** the order-N iteration is
**bounded by forward-model quality**, exactly the long-flagged AxS caveat (iter-16
#1, iter-35). The forward model is an exemplar-mean A1 trajectory and the "re-generate
in the heard voice" step is a global affine warp; measured, that warp shifts
level/scale EQUALLY across candidates and does NOT differentially favour the true word
(it even raised the true-word error on the probed utterance). So inverting THIS
forward model — once or N times — cannot recover phonetic identity it does not carry,
and iterating it adds nothing. The lever is a better forward model (the
babble-loop-calibrated, articulatory `speak()` the agent has repeatedly flagged), not
more iterations and not weights. Until the forward model improves, order-N AxS and the
learn-bank loop are built and correct but flat.

This is the faithful instance↔model A1-space comparison (no natural/synthetic domain
gap), the agent's owned operators throughout. The two-path ARCHITECTURE is in place
and the slow-path machinery is real; its PAYOFF awaits the forward-model quality it is
bounded by — stated as the residual, not spun.

## Files
- `domains/slow_path.py` — the slow path: owned forward model + graph `DtwTo` AxS
  distance + order_n fixed-point iteration (`order_n_axs`) + voice/boundary warp +
  `learn_and_bank` + `build_library` / `forward_model`. No agent decisions in Python
  (it composes the agent's owned Terms / operators; the iteration is the order_n
  operator's order-1 fixed point).
- `scripts/slow_path_accept.py` — the world-adapter driver + the two decisive tests
  (A: order-N vs single-pass on digits + continuous, with the pass-cap sweep and the
  n-vs-difficulty curve; B: the closed loop, before/after fast-path accuracy with
  unsupervised confidence-gated banking).
- `docs/agent_loop_iteration39_slow_path.md` — this report.

## Reproduce
```
python -m scripts.slow_path_accept digits 4                  # /tmp/iter39_testA_digits.txt
python -m scripts.slow_path_accept continuous 8 30 6 12      # /tmp/iter39_testA_continuous.txt
python -m scripts.slow_path_accept loop 4                    # /tmp/iter39_testB_loop.txt (ungated)
python -m scripts.slow_path_accept loop 4 0.15              # /tmp/iter39_testB_loop_gated.txt
```
Required suites green (127): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance (+ test_codec_primitives,
test_llvm_pass_compiler — no DSL regression).
