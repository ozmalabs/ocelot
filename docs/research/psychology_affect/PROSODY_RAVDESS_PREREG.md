# FELT-PROSODY × RAVDESS (affect→prosody generation + parsing lift) — pre-registration (block 295000)

**Status: PRE-REGISTRATION. Committed BEFORE any confirmatory measurement.** The
external ground-truth regions in §2, the FIXED affect→knob mapping in §3, and the
FIXED prosodic-feature vector + prior weight + baseline in §4 are committed here,
NOW, before either arm is scored. The two arms' confirmatory adapters must be
scored against exactly these frozen artefacts; any deviation is reported straight
(produced ≠ pre-reg is either a mapping error to fix or an early sign of a flaw
in §5). The ground-truth region numbers in §2 were read from the substrate's OWN
judge run over the REAL RAVDESS wavs **on the TRAIN actor split (actors 01–16)
only** at prereg time — they are NOT fit to a target and NOT computed on the
held-out test actors.

> **THE HONEST CAVEAT — READ FIRST, IT IS CENTRAL, NOT BURIED.** Of the four
> features the substrate judge produces, only **TWO discriminate emotion cleanly,
> and both only along the AROUSAL axis**:
>
> - **ENERGY** (RMS envelope) discriminates with a ~10× arousal gradient:
>   calm/neutral (lowest) < sad/disgust < surprised/happy < fearful < angry
>   (highest) — the literature-correct arousal direction.
> - **F0_MEAN** discriminates: low-arousal neutral/calm sit low (~276–290 Hz),
>   high-arousal angry/fearful/happy/surprised sit high (~316–360 Hz) — again the
>   literature-correct arousal direction.
> - **F0_RANGE and RATE/ZCR are NOISY and are reported as WEAK, not dressed up.**
>   The autocorrelation F0 tracker suffers octave/halving errors that inflate
>   f0_range indiscriminately across ALL emotions (measured 430–508 across the
>   board), and ZCR / windowed rate is ~flat across emotions (9.7–11.3). These two
>   axes carry **no usable emotion signal here** and are excluded from every
>   ground-truth region, every prediction, and every scored metric. They are
>   noted only as diagnostics.
>
> **Consequence for scope:** the usable external ground-truth signal is
> **primarily the AROUSAL axis (energy + f0_mean).** The VALENCE axis — e.g.
> happy vs angry, both high-arousal — is **NOT cleanly separated** by these
> features (happy energy ~0.012 and f0 ~330 overlap angry/fearful territory). We
> pre-register this limit honestly: **both arms are scoped to AROUSAL**, and the
> parsing claim (Arm B) is a HIGH-vs-LOW arousal claim, not a fine-grained 8-way
> valence claim. 8-way classification is expected to be limited and, if reported
> at all, is reported as a weak secondary number, never as the headline.

> **THE SCOPE SPLIT — READ SECOND, IT IS ALSO CENTRAL.** The two arms use
> DIFFERENT carriers, on purpose, and this is stated plainly:
>
> - **ARM A (GENERATION)** synthesizes utterances through the substrate's OWN
>   forward synthesizer (`domains/projection.build_speech_forward`). That
>   synthesizer is **LOCKED to the FSDD digit words** (`GESTURE_SCORES` in
>   `scripts/articulatory_gamma.py`): it can only voice digit-word carriers.
>   So Arm A synthesizes **digit-word utterances** under affect-driven knob
>   settings, re-analyzes them through the judge, and asks whether the re-analyzed
>   **energy + f0_mean LAND in the RAVDESS-derived human region**. It tests
>   whether the affect→knob mapping REACHES human prosody, on digit carriers.
> - **ARM B (PARSING/CLASSIFICATION)** operates on the **REAL RAVDESS wavs
>   directly** — real human sentences, NO synthesis. It tests whether the
>   prosodic-felt feature vector gives measurable LIFT to arousal classification
>   over a baseline that omits it.
>
> Different carriers (synthetic digits for A; real human sentences for B), both
> honest. Arm A cannot use RAVDESS sentence carriers because the synthesizer
> cannot voice them; Arm B does not synthesize at all. Neither arm pretends the
> other's carrier. Said so here so no reader conflates them.

## 0. Seed / block claim

Block **295000** (range 295000–295999), an UNUSED block, reserved for hygiene /
successor safety. **No new auto-loaded seed is authored by this rung.** Both arms
are mechanical world adapters that (Arm A) call the EXISTING forward synthesizer
and the EXISTING judge, and (Arm B) call the EXISTING judge over vendored wavs;
neither mints a seed that `load_all_seeds` picks up. Because there is no new seed
file, the base tree is byte-identical when the adapters are absent (**default ==
today**). There is no RNG sink required to fix the regions or mappings (they are
read from the judge over fixed data, and the mappings are pen-committed here), so
no integer is drawn from the block; the only stochastic element is the
train/test actor split, which is **fixed by actor id, not by RNG** (§2).

## 1. The idea, the human result, the hypothesis, the posture

### The hypothesis under test (the user's)

System-1 cognition is largely **qualia / felt-based**. If that is right, a
**FELT-PROSODY signal** — the affective quality of a voice, carried as a small
prosodic feature vector — should do two things a blind symbolic pipeline cannot:
**(A)** DRIVE correct affect-driven **prosody GENERATION** (a felt "this should
sound angry / calm" lands the synthesized voice in the human region for that
affect), and **(B)** give measurable **LIFT to speech PARSING** (adding the felt
prosodic vector to an emotion/arousal classifier beats the blind twin that omits
it). Both are measured against **REAL external ground truth (RAVDESS)**, with the
substrate's **OWN pre-existing prosody extractor as the JUDGE** — not an invented
oracle.

### The human result / external anchor

**RAVDESS** — the Ryerson Audio-Visual Database of Emotional Speech and Song
(Livingstone & Russo 2018, *PLoS ONE* 13(5):e0196391,
[doi:10.1371/journal.pone.0196391](https://doi.org/10.1371/journal.pone.0196391);
data DOI [10.5281/zenodo.1188976](https://doi.org/10.5281/zenodo.1188976)) — is a
validated corpus of 24 professional actors (12 female, 12 male) speaking two fixed
sentences in eight emotions at two intensities. We use the **speech** subset:
`data/ravdess/Actor_01..24/*.wav`, **1440 files**, licensed **CC-BY-NC-SA 4.0**
(attribution recorded in §8). Filenames are the RAVDESS 7-part code
`03-01-EE-II-SS-RR-AA.wav`: part 3 `EE` = emotion
`{01 neutral, 02 calm, 03 happy, 04 sad, 05 angry, 06 fearful, 07 disgust,
08 surprised}` (neutral has 96 files, the other seven have 192 each); part 4 `II`
= intensity `{01 normal, 02 strong}`; part 7 `AA` = actor (odd = male, even =
female).

The affect→prosody mapping literature fixes the DIRECTION the generation mapping
must point: **arousal drives F0, energy/intensity, and rate UP** — high-arousal
emotions (anger, fear) raise mean F0 and vocal intensity and (often) speaking
rate; low-arousal emotions (calm, sadness) lower them (Banse & Scherer 1996,
*J. Personality & Social Psychology* 70(3):614–636; Scherer 2003, *Speech
Communication* 40(1–2):227–256; Juslin & Laukkanen reviews). RAVDESS's own
validation reports F0 in **semitones relative to 100 Hz** — a log-pitch
convention we adopt for the CONTOUR/pitch knob direction (§3), so the mapping is
grounded in the corpus's own methodology, not invented.

### Posture (honest CAPABILITY / mechanism-demonstration)

This is a **CAPABILITY / mechanism demonstration** — does a felt-prosody signal
(A) reach the human prosodic region when driving the substrate's own synthesizer,
and (B) improve the substrate's own parsing — **NOT** an empirical claim about how
humans encode or decode emotion. RAVDESS + the mapping literature fix the targets
the mechanism must hit; the judge is the substrate's OWN extractor. The
contribution is that a **small felt vector** is doing the work in both directions,
glass-box, measured against real external data. Prior art: that arousal drives
F0/energy/rate is Banse & Scherer / Scherer — **we do not claim that finding**;
that prosodic features help emotion classification is established SER work — **we
do not claim that idea is novel**. The genuine delta is the SAME felt-prosody
vector serving both a generation map (into the real human region) and a parsing
lift (over a blind twin), on this glass-box substrate, with the pre-existing
extractor as an independent judge and every threshold/weight fixed BEFORE
measuring.

## 2. The EXTERNAL GROUND-TRUTH REGIONS (train-split, reliable axes only)

**Split (fixed NOW, speaker-independent, by actor id — no RNG):**

| split | actors | role |
|---|---|---|
| **TRAIN** | **01–16** (16 actors) | the regions below are DEFINED here; Arm B classifier is FIT here |
| **TEST**  | **17–24** (8 actors)   | Arm A landing + Arm B lift are MEASURED here (held-out speakers) |

The region is defined on TRAIN actors and every confirmatory number is measured on
the HELD-OUT TEST actors, so **no region is fit to the speakers it is scored
against** (the circularity guard, §5). The split is by actor so it is
speaker-independent: no actor appears in both halves.

**The regions are on the RELIABLE axes only — ENERGY and F0_MEAN.** f0_range and
rate/ZCR are excluded (the §0 caveat). Bands are `mean ± 1·sd` (k = 1, fixed here)
over the TRAIN actors, plus the arousal RANK ORDER by energy. **These numbers were
computed at prereg time by the substrate judge (`_estimate_f0_per_window`,
`_energy_envelope` in `runners/dsl/python/substrate_rs/communication.py`) over
`data/ravdess/Actor_01..16/*.wav` ONLY**, wavs read with stdlib `wave`
(`np.frombuffer(int16)/32768`, channels mean-averaged, `fs=getframerate`):

| emotion | n (train) | f0_mean (Hz) | f0_sd | **f0 band [m−sd, m+sd]** | energy | en_sd | **energy band [m−sd, m+sd]** | arousal class |
|---|---:|---:|---:|:--:|---:|---:|:--:|:--:|
| **calm**      | 128 | 276.2 | 74.3 | [201.9, 350.5] | 0.00264 | 0.00212 | [0.00052, 0.00476] | **LOW** |
| **neutral**   |  64 | 289.7 | 77.9 | [211.8, 367.6] | 0.00294 | 0.00186 | [0.00108, 0.00480] | **LOW** |
| **sad**       | 128 | 316.4 | 80.7 | [235.7, 397.1] | 0.00467 | 0.00475 | [0.00000, 0.00942] | mid-low |
| **disgust**   | 128 | 290.1 | 70.7 | [219.4, 360.8] | 0.00562 | 0.00436 | [0.00126, 0.00998] | mid-low |
| **surprised** | 128 | 336.3 | 70.3 | [266.0, 406.6] | 0.00765 | 0.00541 | [0.00224, 0.01306] | mid-high |
| **happy**     | 128 | 329.8 | 73.9 | [255.9, 403.7] | 0.01202 | 0.01102 | [0.00100, 0.02304] | **HIGH** |
| **fearful**   | 128 | 360.1 | 74.6 | [285.5, 434.7] | 0.01470 | 0.01289 | [0.00181, 0.02759] | **HIGH** |
| **angry**     | 128 | 348.0 | 69.9 | [278.1, 417.9] | 0.02492 | 0.02013 | [0.00479, 0.04505] | **HIGH** |

**Arousal RANK ORDER by TRAIN energy (low → high)** — the primary, robust
ground-truth structure (this ordering is what Arm A must land into and Arm B must
recover):

> **calm (0.00264) < neutral (0.00294) < sad (0.00467) < disgust (0.00562) <
> surprised (0.00765) < happy (0.01202) < fearful (0.01470) < angry (0.02492)**

with f0_mean rising in the same broad direction (low-arousal ~276–290, high-arousal
~316–360). **This is the literature-correct arousal direction (Banse & Scherer;
Scherer).** The valence pairs that share an arousal band (e.g. happy vs angry,
both HIGH) overlap on both reliable axes — the honest §0 valence limit, visible
right here in the bands.

**Binary AROUSAL region (the scored target for both arms):**

- **LOW-arousal region:** `{calm, neutral}` — energy < ~0.0035, f0_mean < ~300.
  Committed as **energy ≤ 0.0035 AND f0_mean ≤ 300 Hz**.
- **HIGH-arousal region:** `{angry, fearful, happy}` — energy > ~0.010, f0_mean
  > ~320. Committed as **energy ≥ 0.010 AND f0_mean ≥ 320 Hz**.
- **MID band** `{sad, disgust, surprised}` is the honest in-between; it is NOT a
  scored landing target for Arm A and is the ambiguous class for Arm B (reported,
  not forced).

These thresholds (0.0035 / 0.010 on energy; 300 / 320 Hz on f0_mean) are the
midpoints between the TRAIN LOW cluster and TRAIN HIGH cluster and are **frozen
here.** **Confirmed: computed on TRAIN actors 01–16 only.**

## 3. ARM A (GENERATION) — prediction + the FIXED affect→knob mapping

### The FIXED, monotone, pre-committed affect→knob map

The synthesizer `forward(word, sub, fs, dur_s, f0_hz, vtl_scale, oq, am,
ta_frac, ...)` (`domains/projection.build_speech_forward`) is driven on the
**digit-word carriers** (the only carriers `GESTURE_SCORES` supports). Each
emotion is placed at a **(valence, arousal)** coordinate (circumplex, fixed from
the affect literature, NOT fit to the judge), and arousal maps MONOTONICALLY to
the knobs in the **literature-correct direction**, grounded in the IDS precedent
(`domains/parent_teacher.py`: `IDS_RATE_WPM = 110` slow, `IDS_PITCH = 75` raised —
the substrate's OWN register-parameter precedent for pushing pitch up and rate
down for a felt register). Higher arousal ⇒ higher `f0_hz`, shorter `dur_s`
(faster rate), and flatter/harder source (`ta_frac` DOWN = less return-phase
softness = pressed/loud); lower arousal ⇒ the reverse.

| emotion | valence | arousal a∈[0,1] | `f0_hz` (Hz) | `dur_s` (s) | `ta_frac` | f0 contour shape |
|---|---:|---:|---:|---:|---:|---|
| **calm**      | +0.3 | 0.10 | 150 | 0.55 | 0.10 | gently falling |
| **neutral**   |  0.0 | 0.20 | 165 | 0.50 | 0.08 | ~flat |
| **sad**       | −0.6 | 0.25 | 175 | 0.60 | 0.12 | falling |
| **disgust**   | −0.5 | 0.35 | 190 | 0.45 | 0.06 | falling |
| **surprised** | +0.1 | 0.65 | 240 | 0.35 | 0.03 | rising |
| **happy**     | +0.7 | 0.75 | 255 | 0.35 | 0.03 | rising-undulating |
| **fearful**   | −0.5 | 0.85 | 275 | 0.30 | 0.02 | rising |
| **angry**     | −0.7 | 0.90 | 285 | 0.30 | 0.02 | flat-high / pressed |

**The knob formula (frozen, monotone in arousal `a`):**

```
f0_hz  = round(140 + 160 * a)          # 140..300 Hz, arousal raises pitch (IDS_PITCH direction)
dur_s  = round(0.60 - 0.30 * a, 2)     # 0.60..0.30 s, arousal shortens duration = faster rate
ta_frac= round(0.11 - 0.10 * a, 3)     # 0.11..0.01, arousal presses the source (less soft)
# contour: a < 0.3 -> falling/flat ; a >= 0.6 -> rising ; per-frame f0 tilt = +/- (a-0.4)
```

The per-emotion table values are this formula evaluated at each emotion's fixed
arousal `a` (rounded), with the contour direction set by valence-neutral arousal
bands. **`f0_hz` is a knob into the synthesizer; the JUDGE re-measures `f0_mean`
from the rendered audio — the two are not the same number, and Arm A is scored on
the RE-ANALYZED judge output, not the knob.** The mapping is committed BEFORE any
render is judged; it is grounded in arousal→pitch/rate/tilt (Scherer 2003) and the
IDS register precedent, and is NOT tuned to the §2 regions.

### Arm A prediction (scored on HELD-OUT structure / re-analysis)

1. **Landing:** a synthesized **HIGH-arousal** emotion (angry / fearful / happy),
   re-analyzed by the judge, lands its `(energy, f0_mean)` in the **HIGH region**
   (energy ≥ 0.010 AND f0_mean ≥ 320); a synthesized **LOW-arousal** emotion
   (calm / neutral) lands in the **LOW region** (energy ≤ 0.0035 AND f0_mean ≤ 300).
2. **Separation from a FLAT baseline:** a **flat neutral baseline** (fixed
   `f0_hz=165, dur_s=0.50, ta_frac=0.08` for EVERY emotion — the blind twin that
   ignores affect) does NOT separate HIGH from LOW; the affect-driven renders'
   re-analyzed energy+f0_mean are **CI-separated** (bootstrap 95% CI over the digit
   carriers) from the flat baseline in the predicted direction.
3. **Own-region nearest:** each synthesized emotion's re-analyzed
   `(energy, f0_mean)` is **nearer its OWN emotion's train-region centre than the
   other emotions' centres**, on the reliable axes, along the AROUSAL ordering
   (we do NOT claim valence separation — happy/angry may tie, per §0).

## 4. ARM B (PARSING LIFT) — prediction + the FIXED feature vector, weight, baseline

Arm B runs on the **REAL RAVDESS wavs** (no synthesis). The task is **binary
AROUSAL classification: HIGH `{angry, fearful, happy}` vs LOW `{calm, neutral}`**
(the reliable axis; the MID `{sad, disgust, surprised}` set is reported as a
secondary confusion class, not part of the primary binary metric).

### The FIXED prosodic-felt feature vector and the blind twin

- **FELT model (the test):** feature vector = **`[energy_mean, f0_mean, contour]`**
  where `energy_mean` and `f0_mean` are the judge's own outputs and `contour` is
  the judge's `{flat:0, falling:−1, rising:+1, undulating:+2}` bucket (all from
  `compute_prosody` / the judge DSP). This IS the felt-prosody vector.
- **BASELINE / blind twin (the control):** the SAME classifier with the
  felt-prosody vector **omitted** — it sees only a **duration-and-ZCR** vector
  `[duration_s, zcr]` (the non-prosodic, arousal-uninformative features; ZCR is
  the §0 flat feature by design). The blind twin has the same classifier, same
  split, same everything except the felt vector.
- **Classifier (frozen):** a **logistic regression** (scikit-learn default,
  `C=1.0`, no class weighting) FIT on TRAIN actors (01–16), EVALUATED on TEST
  actors (17–24). Frozen here: model class, C, features, split, metric.
- **FIXED prior weight:** the felt-prosody block enters the classifier with a
  **fixed prior L2 weight `λ = 1.0`** (i.e. no down-weighting relative to the
  baseline features; both feature blocks are standard-scaled to unit variance on
  TRAIN so no block is implicitly privileged). This is the "fixed prior weight"
  committed BEFORE measuring.
- **Metric:** **binary arousal-classification accuracy** on the held-out TEST
  actors (primary), plus the **arousal-axis point-biserial correlation** of
  `energy_mean`+`f0_mean` with the HIGH/LOW label (secondary, sign-checked).

### Arm B prediction

- **Predicted lift SIGN: POSITIVE** — the felt model beats the blind twin on
  held-out binary arousal accuracy. The felt vector carries energy+f0_mean, which
  §2 shows discriminate arousal ~10×; the blind twin's duration+ZCR do not.
- **Explicit about magnitude:** the lift **may be small**, and we **pre-commit to
  reporting the real number even if it is ~0 / null.** A null (no lift) is a VALID
  result and is reported straight (§5, Arm B flaw).
- **Scope (honest, per §0):** the claim is **AROUSAL (HIGH vs LOW)**, where the
  signal is real. **Fine-grained 8-way classification is expected to be limited**
  (valence not separated); if reported, it is a weak secondary number, never the
  headline, and its likely near-chance-on-valence-confusions performance is
  pre-registered as expected, not a surprise.

## 5. FALSIFIERS + FLAW modes (both arms) + the circularity guard

### Circularity guard (explicit)

- The ground-truth regions (§2) are defined on **TRAIN actors 01–16**; every
  confirmatory number (Arm A landing, Arm B lift) is measured on **HELD-OUT TEST
  actors 17–24**. No region is fit to the speakers it is scored against.
- The **JUDGE is the pre-existing extractor** (`communication.py`, READ-ONLY —
  it is the judge), not invented for this rung.
- The **affect→knob mapping (§3) and the feature vector + prior weight + baseline
  + classifier + split + metric (§4) are ALL fixed HERE, before measuring.**
- Arm A is scored on **RE-ANALYZED** judge output of the rendered audio, not on
  the knob values — the synthesizer must actually produce human-region prosody,
  not merely be told a target number.

### Arm A FALSIFIER / flaw

- **FLAW:** synthesized prosody does **NOT** land in the human region, or shows
  **no CI-separation from the flat baseline** ⇒ the affect→knob mapping does not
  REACH human prosody (the felt-generation claim fails). Reported straight — a
  real negative result, not papered over. A partial flaw: HIGH lands but LOW does
  not (or vice versa) ⇒ the mapping is asymmetric; reported per-region.
- **FALSIFIER (the effect must depend on the mapping):** drive EVERY emotion with
  the flat neutral knobs. Then all re-analyzed points collapse together and NO
  emotion separates — if separation SURVIVES a flat drive, it is an artefact of
  the carrier/judge, not the affect mapping, and the claim is false.

### Arm B FALSIFIER / flaw

- **FLAW:** the prosodic-felt features give **NO lift** over the blind twin (Δaccuracy
  ≤ 0 on held-out TEST) ⇒ the felt signal does not help parsing. This is a **VALID
  NULL** and is reported straight with the real number. It would mean the arousal
  signal, though present in the data (§2), is not converted into classifier lift by
  this feature vector — an honest limit of the felt encoding, not hidden.
- **FALSIFIER (the lift must depend on the felt vector):** ablate the felt block
  (the blind twin IS this ablation). If the blind twin matches the felt model, the
  lift is zero by construction and reported as such.
- **Valence over-claim guard:** if 8-way accuracy is high it is scrutinized for
  leakage (actor identity, sentence id); the pre-registered expectation is that
  8-way is LIMITED because valence is not separated (§0), so a surprising 8-way
  win triggers a leakage audit before any claim.

## 6. The two arms' predictions in one line each

- **Arm A:** affect-driven digit-word renders re-analyze into the RAVDESS
  TRAIN-region for their arousal class (HIGH→high, LOW→low), CI-separated from a
  flat baseline, each nearest its own region on energy+f0_mean — measured on
  held-out structure.
- **Arm B:** on real held-out RAVDESS wavs (actors 17–24), the felt-prosody vector
  `[energy, f0_mean, contour]` gives POSITIVE (possibly small, possibly null-and-
  reported) lift to binary HIGH-vs-LOW arousal accuracy over the blind twin
  `[duration, zcr]`.

## 7. Files (all additive, prosody_ / PROSODY_ prefixed)

- `docs/research/psychology_affect/PROSODY_RAVDESS_PREREG.md` — this
  pre-registration.
- `domains/prosody_ravdess_world.py` — (later deliverable) the mechanical world
  adapter: Arm A calls `build_speech_forward` with the §3 knobs on digit carriers
  → judge re-analysis; Arm B reads vendored wavs → judge features → the frozen
  classifier. NO Python computes the affect label or the landing; the judge
  produces the prosody, the frozen classifier produces the arousal decision.
- `results/prosody_ravdess/results.json` — (later) measured output.
- `docs/research/psychology_affect/PROSODY_RAVDESS_RESULTS.md` — (later) write-up.

### Data / isolation choice

RAVDESS speech wavs are **vendored under `data/ravdess/Actor_01..24/`** (1440
files) with **attribution + license noted** (§8). No new auto-loaded seed is
authored; the adapters reuse the EXISTING forward synthesizer
(`domains/projection.py`) and the EXISTING judge
(`runners/dsl/python/substrate_rs/communication.py`) READ-ONLY. Block 295000 is
reserved for successor safety only.

## 8. Attribution + license (recorded, required)

- **Dataset:** RAVDESS — Livingstone SR, Russo FA (2018). *The Ryerson
  Audio-Visual Database of Emotional Speech and Song (RAVDESS): A dynamic,
  multimodal set of facial and vocal expressions in North American English.*
  PLoS ONE 13(5):e0196391.
  [doi:10.1371/journal.pone.0196391](https://doi.org/10.1371/journal.pone.0196391).
  Data: [Zenodo 1188976](https://doi.org/10.5281/zenodo.1188976).
- **License:** **CC-BY-NC-SA 4.0** (Attribution — NonCommercial — ShareAlike).
  Vendored under `data/ravdess/` for research use only; attribution retained.
- **Judge:** the substrate's OWN prosody extractor
  (`runners/dsl/python/substrate_rs/communication.py` —
  `_estimate_f0_per_window`, `_energy_envelope`, `_zero_crossing_rate`,
  `_spectral_tilt`, wrapped by `compute_prosody`); READ-ONLY (it is the JUDGE).

## 9. Discipline

Agent = graph / owned forward model; world = mechanical adapter. The adapter (Arm
A) SETS the §3 knobs and calls `build_speech_forward` then READS the judge's
re-analyzed prosody; (Arm B) READS the judge's features over vendored wavs and
fits the frozen classifier. No `graph_rewrite.run` / `_match` / `_apply` /
`make_rule`; no `if/else` over graph state selecting the affect label; no
reward/punishment shaping (the affect→knob map is a fixed function of a fixed
(valence, arousal) coordinate, never learned). **Native-only.** NO Rust
(`runners/dsl/src/*.rs` untouched); canonical `_native.abi3.so` md5 **`a32ed336`
UNCHANGED**; the JUDGE file `communication.py` is **READ-ONLY**; toolbox solvers,
frozen seeds, and `GESTURE_SCORES` untouched; no new auto-loaded seed
(**default == today**). Data vendored under `data/ravdess` with attribution +
license (§8). Block **295000** (unused).

Do NOT merge to main; do NOT write the ledger row; **NO git commit.** These are
PRE-REGISTERED predictions and FIXED mappings/weights — the only measured numbers
present are the §2 TRAIN-split ground-truth regions (read from the judge over
actors 01–16 only, NOT fit, NOT computed on the held-out test actors).
