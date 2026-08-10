# iter-13: continuous-speech follow-through — per-speaker CMVN does NOT carry; the residual is CHUNK CONSISTENCY

The iter-12 cross-speaker-invariance lever (per-speaker CMVN) closed the gap on FSDD DIGITS
(isolated whole-word utterances): cross-speaker full-DTW 0.588->0.802, LOSO held-out-speaker
recognition 0.785. iter-13 tested whether it carries to the CONTINUOUS-SPEECH chunk->lexicon
(the original last link). It does NOT — and the reason re-locates the residual.

## Verified live (assistant's own clean run, /tmp/iter13_run.txt; LibriSpeech, 30 train / 10 test, 2 held-out speakers)
WITHIN/CROSS full-DTW on CONTINUOUS CHUNKS (chance 0.007):
- BEFORE (per-utterance invariant_transform): WITHIN 0.025  CROSS 0.013
- AFTER  (per-speaker CMVN, uVTLN+ps_CMVN+PR): WITHIN 0.000  CROSS 0.000
- shuffle 0.000

## The finding
The invariance fix is MOOT on continuous speech because the continuous chunks do not match even
WITHIN speaker (0.025, ~chance) — vs FSDD digits' 0.875 within-speaker. The continuous chunks of
the SAME word (same speaker) are not acoustically consistent: the chunker produces word-SCALE
chunks (iter-9 solved the count, 1.39 chunks/word) but not word-CONSISTENT chunks (the boundaries /
coarticulation vary, so the same word is chunked differently each time -> different chunk vectors ->
no match). per-speaker CMVN can't help features that don't correspond to consistent units.

## Honest split
- ISOLATED-WORD (FSDD) cross-speaker recognition: SOLVED (0.785, confirmed) — the hard ASR core
  (speaker invariance) closed on CONSISTENT units.
- CONTINUOUS-SPEECH recognition: blocked upstream by CHUNK CONSISTENCY (within-speaker), not by
  cross-speaker invariance. The same word must chunk to the same representation before any
  cross-speaker map can be learned.

## Next constraint
Continuous-speech chunk CONSISTENCY: the same word -> the same chunk representation within a speaker
(boundary/coarticulation-stable segmentation, or a chunk representation invariant to boundary jitter).
This is a distinct sub-issue from the over-segmentation count (solved iter-9) and from cross-speaker
invariance (solved iter-12 on isolated words).
