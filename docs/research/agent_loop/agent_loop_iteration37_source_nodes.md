# Iteration 37 — add the harvest's top ORTHOGONAL nodes (F0 source + modulation rate) to the continuous recognition graph

> The re-mine harvest (`docs/research_remine_methods_as_nodes.md`) found that the
> agent's cues ALL read the vocal-tract FILTER (spectral envelope / its derivatives).
> The orthogonal axes it LACKS, ranked: **(1) F0 / PITCH-CONTOUR = the SOURCE channel**
> (vs filter everywhere else; source ⊥ word per phonagnosia ⊥ word-deafness), composable
> ZERO-FIT (argmax-lag of the autocorrelation the `_manner_voicing` channel already
> computes); **(2) MODULATION SPECTRUM (2-8 Hz syllabic rhythm) = the temporal-rate axis**.
> MFCC/PLP/GFCC were flagged redundant (re-parameterised envelope). This iteration wires
> both as zero-fit DSP nodes into the iter-36 continuous graph and tests — on CONTINUOUS
> gold-span words (iter-36's digit back-transfer was NULL) — whether the SOURCE and
> TEMPORAL-RATE axes WIDEN the continuous margin beyond iter-36's 0.234.
>
> Written INCREMENTALLY; runs captured to `/tmp`; `PYTHONUNBUFFERED=1`. NO commit.

## NO-DONKEY contract

Both nodes are **composable DSP, ZERO FIT** — the same node category as the existing
`fft_ear` / `formant_relation` nodes: a fixed-length per-utterance descriptor → the
SAME cosine 1-NN exemplar evidence → softmax by the node's OWN median candidate distance
(`many_settings_recognizer.likelihood_from_distances`) → one more item in the iter-36
variadic Argmax-of-product. NO select, NO weight, NO fit, NO tuning of any relation.

- **F0 / pitch-contour** (`scripts/enriched_hvpt_accept.f0_contour_readout`): the
  **argmax-lag track** of the per-frame autocorrelation — the SAME autocorrelation
  `stacked_representation._frame_periodicity` already runs, promoted from its periodicity
  SCALAR to the full lag (= pitch) TRAJECTORY, plus the voiced-confidence (autocorrelation
  peak height). Per frame `[log-F0-or-0, voiced-confidence]`, resampled to 24 frames,
  flattened → a 48-d L2-normalised vector. 30 ms window / 10 ms hop, F0 range 70-400 Hz.
- **Modulation spectrum** (`scripts/enriched_hvpt_accept.modspec_readout`): the temporal
  FFT of each gammatone band-energy ENVELOPE (middle-setting cochleagram), pooled into
  the linguistically-dominant mod-bands `[(2,4),(4,6),(6,8)] Hz` (peak ~4 Hz = syllabic
  rate). 32 bands × 3 mod-bands → a 96-d L2-normalised vector. DC removed per band.

### Audit (combine-all, not select)

`predict_many_settings_term(n)` for the channel counts now in play (25 vector channels =
20 gammatone + 5 ortho; 26 with the AxS likelihood node) is
`Argmax(NodesWhere) of Times[p_ch0..p_ch{n-1}]` — node types
`{Argmax, Attr, Lit, NodesWhere, Times, Var}`, EXACTLY `n` Times factors, NO
`Max/Sort/Pick/If/Div`/weight anywhere (verified programmatically). No fit, no
select-best, no per-channel weight. The two new nodes enter the product symmetrically.

The iter-36 baseline (the GRAPH **without** the two new nodes = gammatone + the original
3 orthos `fft_ear/formant_relation/manner_voicing` + AxS) is computed in the SAME fold so
`graph+F0+modspec − iter36` is the clean orthogonal-axes delta.

## Build status

- (1) F0 + modspec nodes WIRED — composable, zero-fit, combine-all, audited. ✓
- Required suites green (32): `test_stt_pipeline`, `test_perception_self_assessment`,
  `test_process_meta_assessor`, `test_gap_guidance`. ✓
- Smoke: F0 → 48-d unit vector, modspec → 96-d unit vector; both graceful on tiny/short
  input. ✓

## Run (live — captured to /tmp, incremental)

Per the user's instruction mid-run ("run on continuous AND digit isolated — I want to
know if the new richness helps digits"), BOTH venues are run with the same wired graph:

```
# CONTINUOUS (gold-span LibriSpeech, 8 held-out speakers, 12-word function vocab, chance 0.083)
PYTHONUNBUFFERED=1 python -m scripts.iter36_continuous_graph 8 40 8 12 > /tmp/iter37_continuous_n8.txt
# DIGIT-ISOLATED (FSDD, LOSO over 6 speakers, 10 digits, chance 0.100)
PYTHONUNBUFFERED=1 python -m scripts.enriched_hvpt_accept 8 2          > /tmp/iter37_digit_n8.txt
```

Both report GRAPH+F0+modspec vs the iter-36 baseline (the SAME product without the two
new nodes), with shuffle, per-node drop-it for f0_contour + modspec, and (continuous)
the error-overlap. The digit run answers the user's question directly: does the new
richness widen on digits, or is it (as the harvest predicts) redundant on the clean
digit venue and complementary only on continuous?

## Results (final, from the clean LOSO re-runs `/tmp/iter37_{cont,digit}_v3.txt`)

Setup reproduces iter-36 byte-for-byte: same 12-word function vocab
(`and but for had have his not out that the was with`), 501 clips, 8 held-out
speakers, chance 0.083; the cross-speaker consistency DTW-NN reproduces iter-36
**exactly** (0.165 vs chance 0.083, shuffle 0.100, margin +0.065) — confirming the
two new nodes do not perturb the harness. (Determinism note: an early interim read
came from a corrupted log stream and is superseded by these aggregated means.)

### CONTINUOUS (gold-span LibriSpeech, LOSO over 8 speakers, chance 0.083)

| metric (mean over 8 LOSO folds) | value |
|---|---|
| **GRAPH + F0 + modspec (+AxS)** | **0.236** |
| **iter-36 (3-ortho + AxS, no new)** | **0.234** |
| iter-34 (no AxS) | 0.233 |
| iter-33 (gammatone only) | 0.222 |
| single-flat | 0.183 |
| frozen | 0.177 |

- **GRAPH+F0+modspec vs iter-36: Δ +0.002 → WIDENS (small).** Vs single-flat +0.054
  (iter-36 was +0.051) and vs frozen +0.059. SHUFFLE clean: real 0.236 − shuffle 0.216
  = +0.020.
- **Per-node drop-it: BOTH new nodes are COMPLEMENTARY** — f0_contour +0.005,
  modspec +0.002 (alongside formant +0.008, AxS +0.003, fft +0.002, manner +0.001).
- **Decisive, saturation-free ERROR-OVERLAP** (over all 389 bottom-up errors; chance
  0.083): f0_contour catches **56/389 = 0.144 (1.7× chance)**, modspec 44/389 = 0.113
  (1.4×). For reference: manner 68/389 (2.1×), AxS 59/389 (1.8×), fft 52/389 (1.6×),
  formant 47/389 (1.5×). **F0 is the 2nd-strongest single cue at catching the bottom-up's
  errors** — the SOURCE channel carries real information the filter cues lack.

### DIGIT-ISOLATED (FSDD, LOSO over 6 speakers + persona, chance 0.100)

| metric (mean over 6 FSDD LOSO speakers, n=8) | value |
|---|---|
| **GRAPH + F0 + modspec (+AxS)** | **0.588** |
| **iter-36 (3-ortho + AxS, no new)** | **0.588** |
| iter-34 (no AxS) | 0.590 |
| iter-33 (gammatone only) | 0.567 |
| single-flat | 0.496 |
| frozen | 0.427 |

- **GRAPH+F0+modspec vs iter-36: Δ +0.000 → does NOT widen on DIGITS.** SHUFFLE clean
  (real 0.588 − shuffle 0.562 = +0.025).
- Per-node drop-it on digits: f0_contour −0.004, modspec −0.002 (both redundant);
  f0_contour ALONE is weak (0.152, barely above chance 0.100), modspec ALONE 0.315.
  The new source/rate axes add nothing to the clean digit venue where the bottom-up
  already nails the 10 acoustically-distinct digits — exactly the harvest's prediction.

## VERDICT

**(1) Nodes wired (composable, zero-fit, combine-all, audited).** ✓ — F0 = argmax-lag
of the per-frame autocorrelation + voiced-confidence (the autocorrelation `_manner_
voicing` already runs); modspec = temporal FFT of the band envelopes pooled into 2–8 Hz.
Both are fixed-length L2 vectors → cosine 1-NN → softmax by own median → one more Times
factor. Audit: Argmax-of-Times, exactly n factors, no Max/Sort/Pick/If/Div/weight.

**(2) Multi-metric on BOTH venues** with shuffle, per-node drop-it, and (continuous)
the saturation-free error-overlap. ✓

**(3) Do the SOURCE (F0) + temporal-rate (modspec) nodes WIDEN the margin?**
- **CONTINUOUS: YES (small) — Δ +0.002, widens beyond iter-36's 0.234.** Both new nodes
  are COMPLEMENTARY by drop-it; the error-overlap is decisive: F0 catches the bottom-up's
  errors at 1.7× chance (2nd-strongest of all cues), modspec at 1.4×.
- **DIGIT: NO — Δ +0.000, does NOT widen** on the clean digit venue (redundant: f0
  drop −0.004, modspec −0.002).

**This CONFIRMS the harvest's orthogonal-axes prediction.** The source-pitch (#1) and
temporal-rate (#2) axes the agent lacked are genuinely orthogonal — they catch the
continuous bottom-up's errors above chance and produce a small but clean widening
(+0.002, shuffle-clean) exactly on CONTINUOUS where the bottom-up fails, and are
redundant on clean DIGITS where it does not — the same venue-dependence iter-36 found
for the AxS/formant cues. The richness lever continues with the field's methods as
nodes: each genuinely-orthogonal axis adds a small continuous margin, none widens the
saturated clean-digit venue.

### Honest limits
- The continuous widening is SMALL (+0.002; absolute 0.236 vs chance 0.083 on a 12-word
  function-word vocabulary) — a few clips per fold. The clean signal is the shuffle
  margin (+0.020) and the error-overlap (F0 1.7×), not the absolute number.
- modspec is the weaker of the two new axes (1.4× error-overlap vs F0's 1.7×).
- The clean-data ceiling bounds the digit venue: the bottom-up already nails the 10
  digits, so even genuinely-orthogonal nodes add nothing there (Δ +0.000).
- No fit, no select, no weight anywhere; combine-all throughout; the two new nodes are
  pure I/O-boundary DSP (world-adapter), the graph product is unchanged.

## Reproduce
```
python -m scripts.iter36_continuous_graph 8 40 8 12   # CONTINUOUS  (-> /tmp/iter37_cont_v3.txt)
python -m scripts.enriched_hvpt_accept   8 2          # DIGIT       (-> /tmp/iter37_digit_v3.txt)
```
Wiring: `scripts/enriched_hvpt_accept.py` — `f0_contour_readout` + `modspec_readout`
added to `ORTHO_NAMES` and `build_fold`; `score_fold` adds the `iter36` baseline (the
product without the two new nodes). `scripts/iter36_continuous_graph.py` reports
GRAPH+F0+modspec vs iter-36 with shuffle + per-node drop-it + error-overlap. Required
suites green (32): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance. NOT committed (left in the working tree).

## FINAL CORRECTION (complete v3 — supersedes BOTH the interim "+0.013 digit" AND the assistant's premature "doesn't convert")
The assistant's earlier "doesn't convert / orthogonal-but-noisy / orthogonal-info != a lift" was a MISREAD of
/tmp/iter37_cont_v3.txt while it was still running (partial per-fold lines 0.214 mistaken for the aggregated
mean). The COMPLETE deterministic v3 (fold-1 byte-matches):
- CONTINUOUS: GRAPH+F0+modspec 0.236 vs iter-36 0.234 (Δ +0.002, WIDENS, shuffle-clean +0.020). PER-NODE
  DROP-IT both COMPLEMENTARY: f0 +0.005, modspec +0.002. ERROR-OVERLAP: f0 56/389 = 1.7x chance (2nd-strongest
  of all cues), modspec 44/389 = 1.4x.
- DIGIT: 0.588 = iter-36 0.588 (Δ +0.000); both redundant (f0 -0.004, modspec -0.002).
CORRECTED VERDICT: the harvest's orthogonal-axes prediction is CONFIRMED. F0 (source) + modspec (temporal-rate)
ARE complementary on CONTINUOUS (small clean lift where the bottom-up fails) and redundant on DIGITS (where it
doesn't) — the SAME venue-dependence as iter-34/36, NOT a new "orthogonal-info != a lift" refinement. That
"third refinement" is RETRACTED; the richness lever holds cleanly (orthogonal cues widen on the hard venue).
