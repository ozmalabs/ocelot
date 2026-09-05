# RAVDESS — vendored data attribution + license

**This directory holds the RAVDESS *speech* wavs (`Actor_01..24/*.wav`, 1440
files). The wavs themselves are NOT committed to git** — `data/` is gitignored
(see repo `.gitignore`), exactly as `data/fsdd/` is handled. Only this
attribution note is tracked. Fetch the corpus separately (see below) to reproduce
the measures.

## Dataset

**RAVDESS — The Ryerson Audio-Visual Database of Emotional Speech and Song.**

Livingstone SR, Russo FA (2018). *The Ryerson Audio-Visual Database of Emotional
Speech and Song (RAVDESS): A dynamic, multimodal set of facial and vocal
expressions in North American English.* PLoS ONE 13(5):e0196391.
https://doi.org/10.1371/journal.pone.0196391

Data DOI: https://doi.org/10.5281/zenodo.1188976

## License

**CC-BY-NC-SA 4.0** (Creative Commons Attribution — NonCommercial — ShareAlike
4.0 International). Vendored here for **research use only**; attribution retained
as required by the license. https://creativecommons.org/licenses/by-nc-sa/4.0/

## What is used

- Speech subset only: filenames follow the RAVDESS 7-part code
  `03-01-EE-II-SS-RR-AA.wav`, where part 3 `EE` is the emotion
  (`01 neutral, 02 calm, 03 happy, 04 sad, 05 angry, 06 fearful, 07 disgust,
  08 surprised`) and part 7 `AA` is the actor (01–24).
- 1440 files total: neutral has 96, the other seven emotions 192 each.
- Speaker-independent split used by this rung: **TRAIN actors 01–16**,
  **TEST actors 17–24** (fixed by actor id, no RNG).

## Fetch note (reproduction)

Download `Audio_Speech_Actors_01-24.zip` from the Zenodo record
(https://doi.org/10.5281/zenodo.1188976) and unzip into this directory so that
`data/ravdess/Actor_01/ ... Actor_24/` each contain the `*.wav` files. Read with
the Python stdlib `wave` module (int16/32768, channels mean-averaged,
`fs=getframerate`) — this rung does NOT depend on `soundfile`.

## Judge

Prosodic features are extracted by the substrate's OWN prosody extractor
(`runners/dsl/python/substrate_rs/communication.py`:
`_estimate_f0_per_window`, `_energy_envelope`, `_zero_crossing_rate`,
`_spectral_tilt`, wrapped by `compute_prosody`) — READ-ONLY (it is the JUDGE).
