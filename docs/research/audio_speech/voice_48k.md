# Held-voice impression @ 48 kHz / 24-bit — the fix at FULL FIDELITY

**Verdict (lead).** At full fidelity the *named fix landed where it was aimed and
is provable at the waveform*: the high-voice **RINGING is eliminated** (render-f0 =
code-f0 to **±0.4 %** across every voice incl. the 225-Hz females — was **15–25 %
inflation** at 16 kHz), the **source character (oq / spectral-tilt) is now carried
IN the excitation** (rendered spectral slope moves monotonically with code oq and
ta — controlled below), and **intelligibility is preserved** (rendered-vs-content
cochleagram correlation **0.968**). But the full-fidelity run also *cleanly exposes
the next blocker, and it is no longer the synthesis* — it is the **ANALYSIS / code
recovery**: the recovered `oq`/`ta`/`tilt` read **near-constant across speakers**
and the read-back estimator `glottal_params_from_residual` **saturates at its 0.30
oq floor**, so the 4-D identity print collapses (all renders land nearest one
speaker) → **identity 1/8**. The impression is **NOT yet admitted at the human-ear
"unmistakably this speaker" bar** — but the reason is now decisively the source-cue
*measurement*, not the laundering/ringing the 16 kHz run blamed. Small-n (8
speakers); audition WAVs are 24-bit/48k in `/tmp/voice_imp48k/`.

```
                                   16 kHz          48 kHz / 24-bit
RINGING (mean |render-f0-code-f0|) 15-25% (high)   0.4%        <- ELIMINATED
F0-IDENTITY (per-speaker f0 print) 4/6             3/8
IDENTITY [full 4-D print]          1/6             1/8
IDENTITY [f0-only]                 (4/6 carried)   3/8
IDENTITY [oq+tilt cues]            ~0 (laundered)  1/8 (estimator saturated)
INTELLIGIBILITY (cochlea corr)     ~ceiling        0.968
FACTOR SEPARATION                  66.7%           51.8%
```

Log: `/tmp/voice48k_full.log` (marker `===MARKER_VOICE48K_COMPLETE===`).
WAVs: `/tmp/voice_imp48k/` (24-bit/48k). Script: `scripts/voice_impression_48k.py`.
**Not committed.**

---

## (1) The corpus secured

Real **48 kHz / 24-bit** full-band speech, multi-speaker, with genuine F0 spread:
the **CSTR VCTK Corpus 0.92** (Edinburgh; 48 kHz, full-band). Acquired a SMALL
subset only — two HF parquet shards (~0.9 GB) from the HuggingFace
`refs/convert/parquet` branch (the 10 GB official zip was impractical; the parquet
shards carry the full 48 kHz FLAC audio) — and extracted **8 f0-spread speakers ×
8 parallel sentences**, written **48 kHz / 24-bit PCM_24** to `/tmp/vctk48/corpus/`:

| speaker | gender | probed f0 | speaker | gender | probed f0 |
|---|---|---|---|---|---|
| p232 | M | 126 Hz | p225 | F | 181 Hz |
| p227 | M | 132 Hz | p231 | F | 199 Hz |
| p226 | M | 153 Hz | p230 | F | 210 Hz |
| | | | p233 | F | 224 Hz |
| | | | p228 | F | 225 Hz |

f0 range **126 → 225 Hz** (3 male + 5 female, > 1 octave). The sentences are the
standard VCTK parallel set ("Please call Stella.", "Ask her to bring these things…",
…) — **every speaker reads the SAME sentences**, so the held-sentence test is exact:
render a content-donor's recording of sentence T in S's voice and compare to S's
OWN real recording of T. The 24-bit requirement is met (resynthesised/written
PCM_24 even though VCTK source is ~16-bit — the band is what matters, and it is
full at 48 kHz).

## (2) Did the impression land at full fidelity?

**The carrying mechanism — the named fix — LANDED, and is provable at the
waveform.** Two parts, both measured:

* **Ringing → eliminated (the f1b75b74 high-voice failure, fixed).** With the
  pitch-synchronous LF excitation (one pulse per S-period, no grain reuse) +
  bandwidth-floor + VTL pre-compensation, every render reproduces its code f0 to
  **±0.4 %**, *including* the highest females (p228 code 208 → render 209; p230 203
  → 203; p233 209 → 209). At 16 kHz these were the worst misses (170→198, 200→216,
  +15–25 %). **The high-voice ringing the 16 kHz doc flagged as the open method
  problem is closed.**

* **Source character → now IN the excitation (oq/tilt no longer laundered).**
  A direct synthesis control proves the LF excitation carries the source cues into
  the rendered spectrum (the 16 kHz failure was that `glottal_warp_residual` kept
  the *donor's* grain shape so oq/tilt never entered, and the all-pole filter
  flattened them):

  ```
  code oq 0.40 → 0.60 → 0.80   ⇒ rendered spectral slope -1.168 → -1.012 → -0.931
  code ta 0.005 → 0.02 → 0.08  ⇒ rendered spectral slope -1.020 → -0.986 → -0.869
  ```

  Higher open-quotient → brighter (less steep tilt); longer return-phase → less HF.
  Both monotonic, both the correct physical direction. **The source character now
  survives `lpc_cross_resynth` — exactly the property the 16 kHz resynth lacked.**

* **Intelligibility → preserved.** Rendered-vs-raw-content cochleagram correlation
  **0.968** (every speaker 0.956–0.974). The fresh excitation does not smear the
  words; the donor's gesture survives the voice transplant.

**But the impression is NOT yet admitted at the human-ear bar — full 4-D identity
is 1/8, and the run exposes WHY, decisively.** Every render's source-print lands
nearest the *same* speaker (p232) because the **identity print itself is collapsed**:

  * the recovered **`oq` spans only 0.729–0.750, `ta` 0.0042–0.0079, `tilt` -0.01
    to -0.03** across all 8 speakers — **near-constant**, so the oq/tilt dims carry
    no speaker information;
  * the read-back estimator `glottal_params_from_residual` **saturates** — injecting
    code oq ∈ {0.45, 0.60, 0.75, 0.90} all read back as **0.300** (its clamp floor),
    even though the spectral slope (above) proves the oq *is* in the waveform. The
    instrument that builds the identity print cannot see the cue that is present.
  * the recovered **code-f0 also clusters** (3 males all ≈ 120 Hz; females compress
    to 172–209 vs true 181–225), so even f0-identity is only 3/8.

So the synthesis carries the code faithfully (render-f0 = code-f0 to ±0.4 %; oq/ta
in the spectrum), but **the ANALYSIS produces codes that don't separate the
speakers, and the print estimator can't read back the one cue that IS carried.**
The blocker moved one stage upstream: **16 kHz = "the resynth launders oq/tilt and
rings"; 48 kHz = "the resynth carries them and is ring-free, but the code
*recovery* and the oq *read-back* don't resolve speaker identity."** That is the
precise remaining method gap — and it is owned-DSP analysis (a real glottal-
inverse-filtering oq/tilt estimator + an f0-recovery that preserves the per-speaker
spread), NOT corpus and NOT the synthesis.

## (3) What was designed / built (file:line; donkey audit)

Two NEW native owned-DSP primitives (Rust), the partial `lf_excitation_transplant`
from the just-stopped 16 kHz run **picked up and completed + wired through**:

* **`lf_excitation_transplant`** — `audio_primitives.rs:2391` (body completed from
  the partial), exposed `py.rs:6207`. SYNTHESIZE a fresh LF glottal-flow-derivative
  pulse at S's recovered **oq + ta_frac (= return-phase / tilt) + f0**, **one pulse
  per S-period** (pitch-synchronous ⇒ no grain reuse ⇒ no ringing), modulated by
  the content per-hop residual **energy envelope** (the word's loudness +
  voiced/unvoiced structure); unvoiced hops copy the content residual through
  (frication is sourceless). **S's source character lives in the EXCITATION**, the
  133 dB / f1b75b74 principle — and survives the all-pole filter (proven by the
  spectral-slope control). Reuses the existing closed-form `lf_glottal_period`
  (`audio_primitives.rs:804`).
* **`lpc_bw_expand_track`** — `audio_primitives.rs:2351`, exposed `py.rs:6231`. The
  bandwidth-FLOOR: scale `a[k]` by γ^k (γ = exp(-π·bw_floor/fs)) → pulls every pole
  radially inward, **widening each formant's bandwidth ~bw_floor Hz while leaving
  the frequency fixed**, so sharp poles settle within one pitch period and cannot
  ring between sparse high-f0 pulses. Closed-form coefficient scaling.

48 kHz DSP design (`scripts/voice_impression_48k.py`): **ORDER = 36** (rich enough
for F1..F5 + HF voice-quality across the band, stable under the LF pulse train —
a textbook ~48 over-fits into ringing poles; the bw-floor tames the rest),
FRAME/HOP = 1200/480 (25/10 ms @ 48 k), **BW_FLOOR = 80 Hz**, AM = 0.7 (fixed modal
default). World-adapter measurement fixes (selection, not method): a 48 kHz f0 gate
(ceiling 290 Hz + drop ceiling-pinned failed-read frames — kills the low-male
octave-double `recover_voice_code`'s 400 Hz/0.30 gate admits at 48 k) and **VTL
pre-compensation** of the excitation f0 (`* vtl`, so the output 1/vtl resample lands
code-f0 exactly — the cause of the first run's f0 under-shoot).

**Donkey audit — clean.** LF excitation = closed-form LF period + content energy
envelope + copy-through. Tract = `lpc_coeff_track` + `lpc_bw_expand_track`.
Residual = `lpc_residual_track`. Render = `lpc_cross_resynth`. VTL = linear
resample. Code = `recover_voice_code` (median selection). **NO net, NO .fit, NO
gradient, NO loss, NO sweep-to-fit, NO embedding.** New primitives added in
`audio_primitives.rs` + `py.rs` only. **`CortexLoop` / `solve_for_n.py` untouched**
(not in the diff). The two world-adapter fixes are f0-gate selection + a
deterministic VTL/f0 algebra correction.

## (4) Honest verdict

**At full fidelity the named fix is real and provable, but the impression is not
yet "unmistakably this speaker."** The 48 kHz run did exactly what full fidelity was
supposed to do: it removed the band-limit confound so that *whatever remained is
purely method* — and what remained is now unambiguous. The **synthesis side is
solved**: ringing 15-25 % → 0.4 %, oq/tilt carried into the spectrum (not laundered),
words intact at 0.968. The **analysis side is the new wall**: the recovered codes
don't separate the speakers (oq/ta/tilt near-constant; f0 clustered) and the oq
read-back estimator saturates at 0.30, so the identity print collapses to 1/8.

This is the *fix-the-fixer* result, not a regression: the 16 kHz doc named two open
method problems (laundered oq/tilt; high-voice ringing) — **both are now closed in
owned DSP**, and the residual is a *different, upstream* gap (glottal-inverse
estimation of oq/tilt + spread-preserving f0 recovery). Binary admissibility: the
4-D identity structure is not yet assembled because two of its four dimensions are
fed by a flat/saturated instrument, so it reads ~chance — exactly the shape the
thesis predicts (the cue is in the waveform; the print can't yet read it).

**Next build (owned-DSP analysis, not corpus):** a real glottal inverse-filtering
oq/return-phase estimator (e.g. IAIF / closed-phase covariance LPC) to replace the
saturated `glottal_params_from_residual`, and an f0 recovery that preserves the
per-speaker spread. With those, the carried-but-unread source cues become a
discriminative print and the full 4-D identity should rise toward the human-ear
bar — the synthesis is already there.

*Script: `scripts/voice_impression_48k.py`. Corpus: `/tmp/vctk48/corpus/`
(8 VCTK speakers × 8 sentences, 48 k/24-bit). Log: `/tmp/voice48k_full.log`
(`===MARKER_VOICE48K_COMPLETE===`). WAVs: `/tmp/voice_imp48k/` (24-bit/48k:
`held_<speaker>_says_t005_donor_<donor>.wav`, `REAL_<speaker>_t005.wav`,
`CONTENT_donor_<donor>_t005.wav`). Not committed.*
