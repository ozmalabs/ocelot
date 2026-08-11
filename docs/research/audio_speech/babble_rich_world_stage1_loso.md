# Babble stage-1 — rich generated world + LEARNED across-voice voice-shape library

Cross-speaker SC 40-speaker LOSO. Captured run: /tmp/babble_rich_world_stage1_loso.log

[split] bank 200 train clips, 200 seen-speaker probes, 400 cross-speaker LOSO probes
[CMVN              ] exemplars=200 words=10  seen 0.625  cross-speaker LOSO 0.570  gap +0.055
[LEARNED-FROM-TTS  ] exemplars=200 words=10  seen 0.480  cross-speaker LOSO 0.427  gap +0.052
[LEARNED-FROM-REAL ] exemplars=200 words=10  seen 0.400  cross-speaker LOSO 0.335  gap +0.065
BABBLE RICH WORLD — STAGE 1 — robust SC 40-speaker cross-speaker LOSO
  regime                   seen     LOSO  seen-LOSO gap   vs CMVN
  CMVN                    0.625    0.570          0.055    +0.000
  LEARNED-FROM-TTS        0.480    0.427          0.052    -0.142
  LEARNED-FROM-REAL       0.400    0.335          0.065    -0.235
  (c) LEARNED-FROM-REAL vs CMVN:   -0.235 (CMVN 0.570 -> REAL 0.335)  <- does a LEARNED across-voice shape beat CMVN?
  (b) LEARNED-FROM-TTS vs (c):     +0.092 (REAL 0.335 -> TTS 0.427)  <- does the TTS world TRANSFER to real?
  VERDICT 1 (learned-shape vs CMVN): NO (KILL): the LEARNED across-voice shape does NOT beat CMVN (-0.235). The across-voice learned template still can't disentangle the speaker linearly — the residual is deeper than a linear template and needs the full closed-loop babble. No rescue.
  VERDICT 2 (TTS world transfer): N/A: (c) did not beat CMVN, so transfer of the TTS world to a working learned-shape is moot — the across-voice template itself is the blocker.
  NOTE: this is STAGE 1 (the learned voice-shape library + predict-subtract); the full closed-loop self-spoken babble is later.
[MARKER] BABBLE_RICH_WORLD_STAGE1_LOSO_COMPLETE
