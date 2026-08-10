# Order-N predictive peel — cross-speaker LOSO

**Spec (the user):** "order n find signal in noise, process and subtract." Iterated
predictive peeling — n passes, each FINDs the dominant predictable structure in the
current residual, adaptively PREDICTs it (owned linear prediction), SUBTRACTs
(residual = current − expected). The speaker (vocal-tract envelope + glottal source,
roughly constant within an utterance) is maximally predictable ⇒ should land in the
peel; the word (fast articulatory motion) is least predictable ⇒ should survive in
the residual. Recognise on the residual; cross-speaker invariance as a byproduct.

## Build (donkey-audited)

- `domains/order_n_peel.py` — the order-N FIND-PROCESS-SUBTRACT loop.
  - **PROCESS** = LPC residual. The agent's OWNED linear-prediction primitive (the
    SAME `_autocorr` + `_levinson` Levinson-Durbin recursion `lpc_formant_representation`
    derived): fit the order-p all-pole inverse filter A(z) to each frame's own
    autocorrelation (least-squares-optimal on THIS frame — adaptive, **not** a static
    synth), apply A(z) to get the residual e = x − prediction. Owned linear algebra,
    **no fit, no net, no learned weight** — the coefficients are the closed-form
    solution to the frame's normal equations.
  - **SUBTRACT/iterate** = the agent's order-N operator: re-run the residual pass n
    times with a progressively LONGER predictor order `(2, 10, 20)` — short captures
    the carrier/tilt, longer the vocal-tract envelope (bulk of the speaker), longer
    still the pitch-period/glottal source. Schedule read off the peel-order science,
    **not tuned** to a target; n swept {1,2,3}.
  - Framing + Hann overlap-add = mechanical I/O DSP (same category as the gammatone /
    np.fft front end). Per-pass unit-RMS renorm only.
- `scripts/order_n_peel_loso.py` — RAW vs PEEL-n on the SAME robust SC 40-speaker
  LOSO split (`build_split`/`bank` reused). Recognition = the agent's graph-resident
  **DtwTo** trajectory recognizer (Argmin MinOver DtwTo). The only thing that changes
  between regimes is the waveform the trajectory is extracted from (raw vs n-peeled).
  Held-out speakers' clips NEVER banked; LOSO ungameable. Two readouts probed
  (`PEEL_TRAJ`): the thin VTL **formant** trajectory and the full **cmvn** cochleagram
  trajectory.

## Results (120 train / 40 held-out speakers, 20/word, seed 20240608; chance 0.100)

**CMVN cochleagram trajectory** (the strong recognizer):

| regime | seen | LOSO | gap | LOSO lift |
|--------|------|------|-----|-----------|
| RAW    | 0.625 | 0.570 | +0.055 | +0.000 |
| PEEL-1 | 0.565 | 0.482 | +0.082 | −0.087 |
| PEEL-2 | 0.255 | 0.198 | +0.057 | −0.372 |
| PEEL-3 | 0.225 | 0.122 | +0.103 | −0.447 |

**VTL formant trajectory** (the weak recognizer):

| regime | seen | LOSO | gap | LOSO lift |
|--------|------|------|-----|-----------|
| RAW    | 0.300 | 0.253 | +0.047 | +0.000 |
| PEEL-1 | 0.305 | 0.287 | +0.018 | **+0.035** |
| PEEL-2 | 0.095 | 0.083 | +0.012 | −0.170 |
| PEEL-3 | 0.130 | 0.135 | −0.005 | −0.117 |

## VERDICT — honest, mixed; net NO at the frontier

- **The prediction is confirmed in the narrow case.** On the weak formant readout, a
  SINGLE predictive-subtract pass (PEEL-1) genuinely lifts cross-speaker LOSO
  +0.035 (0.253 → 0.287) AND tightens the seen-vs-cross gap −0.030 (+0.047 → +0.018).
  Some speaker really is in the peel: removing the gross spectral tilt/carrier leaves a
  residual whose formant track generalises slightly better across speakers, with the
  seen-vs-cross gap closing — exactly the predicted shape.

- **But it does NOT advance the frontier.** The best peeled result (formant PEEL-1,
  0.287) is far below the best UN-peeled recognizer (cmvn RAW, 0.570). On the strong
  cochleagram recognizer, peeling strictly HARMS at every n (0.570 → 0.482 → 0.198 →
  0.122), and the gap does not tighten. Peeling buys cross-speaker generalisation only
  where the recognizer was already weak, and the absolute level it buys is worse than
  not peeling at all.

- **Iterating past pass 1 always collapses** (PEEL-2/3 → near chance on both readouts).
  LPC whitening removes exactly the all-pole spectral envelope — which is *where the
  word lives* (formants, vowel identity). By pass 2 the residual is whitened past the
  point where word structure survives; the speaker comes off, but so does the word.
  The peel cannot separate "predictable = speaker" from "predictable = the word's own
  resonant structure," because the vowel formants are themselves highly predictable
  all-pole structure. So order-N iteration over a single whitening operator does not
  isolate the speaker — it strips spectral structure indiscriminately, speaker and word
  together.

**Net:** the FIND-PROCESS-SUBTRACT loop is wired and works as specified; a single pass
peels a little speaker (confirmed on the weak readout), but iterated predictive peeling
does NOT lift the cross-speaker LOSO frontier — the predictable layers an LPC residual
strips carry the word's own resonances along with the speaker, and on the strong
recognizer peeling only removes word information. The speaker is not cleanly in the
peel under a whitening predictor; recognising on the residual loses the word. KILL,
honestly, with the one positive corner reported.

Captured: `/tmp/peel_loso_cmvn.log`, `/tmp/peel_loso_formant.log` (both end
`[MARKER] ORDER_N_PEEL_LOSO_COMPLETE`).
