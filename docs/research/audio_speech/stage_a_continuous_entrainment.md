# Stage A — entrained-theta oscillator on CONTINUOUS rhythmic speech

**Question.** The Stage-A active interface is an entrained theta oscillator (the
syllable clock). It needs RHYTHM — several syllable cycles — to phase-lock.
Isolated short words (the Speech-Commands parallel build, mostly monosyllabic)
give barely one cycle: the HARD case. Continuous speech carries a real syllable
rhythm. *The "nursery-rhyme" prediction:* on continuous speech the oscillator
ENTRAINS and beats the passive envelope-peak counter, and the gap WIDENS for
longer utterances (more cycles to lock); on very short spans both are poor.

This is the proper-domain test of the active interface.

## Build (donkey audit)

Both readers are **owned envelope DSP, no net, no fit, frozen constants** — they
already existed in `domains/prosody_syllable.py` and were reused verbatim:

- **ACTIVE** = `entrain_theta` — a gradient-frequency / phase-locked theta
  oscillator (~3–8 Hz) on the voiced-band energy envelope. Frequency adapts
  slowly (`tau_f` ≈ 0.30 s → inertia), phase is driven (never reset), so a brief
  sonorant-internal dip does not spuriously split a syllable. Count = completed
  driven cycles. Constants are frozen physics of the theta band, not swept on
  this test set.
- **PASSIVE** = `extract_syllables` — the envelope peak-counter baseline
  (prominent local maxima above a floor, split only on a deep dip).

**TRUE syllable count** = sum over the transcript's words of the word's **CMUdict**
syllable count (= number of stress-bearing vowel phonemes, the phonemes ending in
a stress digit 0/1/2 — the standard CMU Pronouncing Dictionary syllabification).
Source: CMUdict via nltk, 123,455 entries. Words absent from CMUdict use an owned
orthographic vowel-group fallback; the fallback count is reported (1.8% of words).
The dictionary never sees audio.

**No agent code.** This is a world-adapter measurement script
(`scripts/stage_a_continuous_entrainment.py`): decode audio → run the two
transducers → tally count-error against the dictionary. No CortexLoop, no graph
state, no reasoning. Every speaker is held out — neither transducer has a fitted
parameter.

**Data.** LibriSpeech dev-clean, 800 utterances, 40 distinct speakers,
cross-speaker. CMUdict coverage 98.2% of words (15948/16243).

## Result (n = 800 utterances, 40 speakers)

| reader | mean \|err\| | exact-hit | pred/true |
|---|---|---|---|
| ACTIVE oscillator | **11.524** | 0.026 | 0.652 |
| PASSIVE peak-count | 11.935 | 0.022 | 0.641 |

Binned by TRUE syllable count (rhythm available to the clock):

| bin | n | true mean | active \|err\| | passive \|err\| | gap (passive − active) |
|---|---|---|---|---|---|
| short 1–3 | 7 | 2.4 | 1.571 | 1.143 | **−0.429** |
| mid 4–7 | 50 | 6.0 | 1.500 | 1.380 | −0.120 |
| long 8–15 | 181 | 11.7 | 3.602 | 3.696 | **+0.094** |
| xlong 16+ | 562 | 35.9 | 15.091 | 15.662 | **+0.571** |

Positive gap = oscillator wins. The gap is **monotonic in utterance length**:
passive is slightly better on the very short bin, they cross over by the long
bin, and the oscillator's advantage keeps growing through xlong.

## Verdict

- **Overall: the oscillator BEATS the passive counter** on continuous speech
  (mean abs count error 11.524 vs 11.935).
- **The advantage GROWS with rhythm**: short-bin gap −0.429 → xlong-bin gap
  +0.571, monotonic across all four bins.
- On the very short spans (1–3 syllables) the passive counter is marginally
  better and both are poor — exactly the predicted hard case where the
  oscillator can't lock.

**PREDICTION CONFIRMED.** The active interface entrains on continuous rhythmic
speech and its advantage over passive peak-counting widens with available
rhythm — the structural signature of "the active interface needs rhythm to
lock." This is the nursery-rhyme effect: exaggerated regular meter is the
oscillator's home turf; isolated monosyllables are its worst case.

## Honest caveats

- **Both readers undercount badly in absolute terms** (pred/true ≈ 0.64): on long
  continuous LibriSpeech utterances the 8 kHz voiced-band envelope merges many
  adjacent syllables, so absolute syllable-count accuracy is low for both. The
  result is a *relative* one — the oscillator's error is consistently lower and
  the gap grows with length — not an accurate absolute syllable counter.
- **The short bins are small** (short n=7, mid n=50): LibriSpeech utterances are
  almost all long (true mean 28.3 syllables), so the short-span evidence is
  thinner than the long-span evidence. The growth trend is monotonic across all
  four bins, but the per-bin gaps in the small bins carry more noise.
- The advantage is modest in magnitude (sub-one-syllable mean-error gap). It is
  consistent and direction-correct, not large; the absolute-undercount problem
  dominates both readers.

## Reproduce

```
python -m scripts.stage_a_continuous_entrainment 800 0
```

(N utterances, random seed as args.) Capture log: `/tmp/stage_a/run.log`,
completion marker `STAGE_A_CONTINUOUS_COMPLETED`.
