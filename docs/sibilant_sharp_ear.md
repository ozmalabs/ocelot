# Sibilant / fricative discrimination — a sharp high-frequency ear vs the
# blurred gammatone vs a partial-deaf (high-freq rolled-off) ear

**Claim under test** (`ozma_wall_is_self_imposed`): *"the agent's senses are its
to build."* A capability gap caused by a **sensory** limitation — high-frequency
partial deafness — should be closed by composing a **sharper sense** (composable
DSP, no fit, no net), not treated as a binding ceiling. The phonemes where this
bites hardest are the sibilants / fricatives: `/s/ /z/ /ʃ/ /f/ /θ/ /v/`. Their
only distinguishing cue is fine high-frequency spectral shape (/s/ peak ~5-8 kHz,
/ʃ/ ~2-4 kHz, /f/ & /θ/ flat-low), at 4-8 kHz, brief and low-energy.

Script: `scripts/sibilant_sharp_ear.py`. Probe set (Speech Commands, /tmp/sc):
`three (/θ/), four (/f/), five (/f/), six (/s/), seven (/s/), zero (/z/)`.
Cross-speaker LOSO: 150 train speakers, 50 disjoint held-out (clips NEVER banked).
Chance 0.167.

## The three ears (composable boundary DSP — donkey-audited)

A structural fact drives the design: the seed world adapter downsamples SC's
native **16 kHz** to **8 kHz** (Nyquist 4 kHz) *before perception begins*, so the
seed cochlea **physically cannot see the >4 kHz /s/ band** — a partial deafness
baked into the pipeline. The probe loads the **native 16 kHz** so a sharp ear can
reach 4-8 kHz.

- **(a) SHARP-HF** — a 4096-pt FFT on the native 16 kHz signal, finely log-pooled
  into 48 bands across **1.5-7.8 kHz** (the fricative region), 6 temporal windows
  so the brief onset frication is its own frame. Fine frequency at 4-8 kHz.
- **(b) GAMMATONE** — the seed cochlea exactly: 32 log-band gammatone cochleagram
  on the 8 kHz world signal (Nyquist 4 kHz, broad ERB filters). The blurred ear —
  loses the whole >4 kHz band and blurs the fine shape below it.
- **(c) PARTIAL-DEAF** — the SHARP-HF ear's **identical** DSP, but the 16 kHz
  signal first passes a high-frequency roll-off (full sensitivity <3 kHz,
  raised-cosine ramp 3→4 kHz, −45 dB floor above 4 kHz) — a moderate-to-severe
  high-frequency sensorineural loss. Only the high-frequency band differs from (a),
  so the comparison isolates the cost of the deafness.

Recognizer = the agent's own `channel_likelihood` (1-NN cosine exemplar evidence)
→ argmax — the identical kernel `blind_guess` uses per channel. Fusion = the
agent's many-settings **product** of two ears' per-word likelihoods (exactly
`blind_guess`'s Argmax-of-product across channels). No fit, no learned weight, no
net. The roll-off is a fixed physical filter, not a tuned knob.

## Results — cross-speaker LOSO accuracy (300 held-out probes, chance 0.167)

| ear / fusion                  | LOSO acc | vs chance |
|-------------------------------|---------:|----------:|
| SHARP-HF (fine 4-8 kHz only)  |   0.373  |  +0.207   |
| GAMMATONE (blurred cochlea)   |   0.453  |  +0.287   |
| PARTIAL-DEAF (HF rolled off)  |   0.320  |  +0.153   |
| **FUSE gammatone + SHARP-HF** | **0.510**|  +0.343   |
| FUSE gammatone + PARTIAL-DEAF |   0.493  |  +0.327   |

Derived contrasts:

- **sharp-only over deaf-only: +0.053** (deaf 0.320 → sharp 0.373) — the lost
  4-8 kHz band carries real fricative information; removing it costs accuracy.
- **fusing sharp-HF onto the cochlea: +0.057** (gammatone 0.453 → fused 0.510) —
  the high-freq ear *adds* discrimination the broadband cochlea lacks.
- **lost-band fused contribution: +0.017** (deaf-fused 0.493 → sharp-fused 0.510)
  — the marginal value of the true 4-8 kHz band *once the cochlea already supplies
  the low-frequency cues*.

### The honest, important finding: complementary, not a replacement

The high-freq-**only** SHARP ear (0.373) is **worse** than the broadband cochlea
(0.453) — it discards the vocalic F1/F2/F3 and onset-timing cues that also
distinguish these words. So a sharper sense alone is *not* the win. The win is
**fusion**: gammatone + sharp-HF (0.510) beats the cochlea alone (+0.057) — the
best regime. This reproduces the memory's actual finding (`two_ears_demo`: "neither
dominates; together they cover what neither covers alone"). The fricative cue and
the vocalic cue are complementary; the sharp ear is added, not swapped in.

### Where the sharp ear helps in the confusion matrix

Fusing the sharp ear lifts the sibilant rows most: `five` recall 0.62→0.66,
`four` 0.42→0.60, `six` 0.50→0.52, `three(/θ/)` 0.48→0.56. The residual confusion
concentrates on **seven (/s/) ↔ zero (/z/)** (seven recall only 0.34; zero 0.38,
heavily cross-firing into seven) — the voiced/voiceless sibilant pair `/s/` vs
`/z/`, whose distinction is **voicing** (a low-frequency periodicity cue), not
high-frequency shape. The sharp high-freq ear correctly does *not* fix that pair —
consistent with the phonetics.

## Verdict

**PARTIAL — the claim holds in its complementary form.** The lost 4-8 kHz band
carries real, recoverable fricative discrimination (sharp-only **+0.053** over
deaf-only; fusing the sharp ear onto the cochlea **+0.057** over the cochlea
alone, reaching the best LOSO 0.510). The sensory limitation is genuinely the
agent's to dissolve by composing a sharper sense — but the right move is to
**fuse** the sharp high-freq ear with the broadband cochlea, not to replace it
(sharp-only underperforms because it throws away the vocalic cues). The marginal
value of the *exact* 4-8 kHz band, once the cochlea supplies the rest, is small
(+0.017) — much of the fricative information also lives in the 2-4 kHz region the
cochlea already partly sees, so the deaf-fused ear (which keeps <4 kHz) is only
slightly behind.

**Honest residual.** Best regime LOSO 0.510 (chance 0.167) — still 0.490 from
solved. The fricative set stays a hard cross-speaker discrimination; the sharp
sense **moves** it, does not **close** it. The dominant remaining confusion is the
voiced/voiceless sibilant pair seven(/s/)↔zero(/z/), which is a low-frequency
**voicing** cue the high-freq ear is not expected to resolve — a manner/voicing
channel, not a sharper frequency channel, would be the next lever there. The
8 kHz world downsample is a real self-imposed deafness this probe confirms costs
fricative accuracy; reading native 16 kHz (or fusing a 16 kHz high-freq ear into
ingest) is the concrete fix.

## Reproduce

```
python -m scripts.sibilant_sharp_ear 150 50 25 20240609
```

Output captured at `/tmp/sibilant_sharp_ear.out` (ends `[MARKER]
SIBILANT_SHARP_EAR_COMPLETE`). Required suites green: `test_stt_pipeline`,
`test_perception_self_assessment`, `test_process_meta_assessor`,
`test_gap_guidance`, `test_frontend_effect_gate` (36 passed).
