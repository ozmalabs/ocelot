# Stage 3 — SPEAKER INVARIANCE (the dynamic gesture), clean 16 kHz

The agent executed **Stage 3** of its own self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"speaker invariance — the
VTL-invariant formant ratio AND the order-N-over-time coarticulatory gesture,
shared across speakers even when absolute formants differ by vocal-tract length."*

Run: `scripts/stage3_invariance_clean16k.py` → `/tmp/stage3_full.log`
(marker `===MARKER_STAGE3_INVARIANCE_CLEAN16K_COMPLETE===`, exit 0, pgrep-clean).
Corpus: clean 16 kHz Google Speech Commands digits, **1752 tokens, 30 speakers**
(`scripts/clean16k_corpus.py`, NOT downsampled — intact frication).

---

## 1. The stage + what the agent composed

**The prerequisite (commit `5ff04a2e`).** Stage 1's coarse squint separated 71.8 %
of the clean-16k tokens but its standardized cross-speaker cluster gap shrank to
**d'=0.096** under the 30-speaker diversity (5× FSDD). The coarse 3-band-mean
trajectory drifts with the speaker — vocal-tract length scales the whole spectrum.

**What Stage 3 swaps in — the agent's OWN owned tools (no new representation code):**

- **Speaker normalisation (the VTL invariant the agent derived,
  memory `ozma_speaker_normalization`).** Per-frame log-formants
  `F_i − mean(F1,F2,F3)`. VTL scales all formants multiplicatively = an additive
  shift in log-Hz; subtracting the per-frame log-formant mean **cancels** it, so the
  representation's LEVEL is speaker-(VTL)-invariant by construction.
  (`domains/agent_frontend.py:467` `vtl_formant_track`, steps 1+2 at `:505–512`.)

- **The dynamic gesture (T7, order-N-over-time).** The order-1 difference of the
  VTL-normalised log-formant track = how the formants MOVE (the coarticulatory
  transition). The articulatory gesture is the same motion in every mouth, only
  scaled; the order-1 difference is speaker-stable AND removes any residual
  per-utterance constant offset. Appended as the velocity channels.
  (`domains/agent_frontend.py:526–529`; the order-N operator
  `domains/order_n_concepts.py`.) Result: a 6-channel/frame trajectory
  `[F1-mean .. F3-mean | velocity]`.

- **The SAME native decision the Stage-1 gate used** — T2 `DtwTo` trajectory
  alignment (absorbs the gesture-timing warp across speakers), evaluated by the
  Rust substrate (`substrate.evaluate`), NOT a re-implemented Python distance.
  (`domains/native_cognition.py:76` `_DtwTo`; structural harness reused VERBATIM
  from `scripts/stage1_coarse_recognition_check.py`.)

**Donkey audit (file:line).** NO net / `.fit` / gradient / loss / sweep-to-fit /
swept knob. Representation = the agent's owned `vtl_formant_track`
(`agent_frontend.py:467`) built on the native `_native_lpc_roots_formants`
Levinson-Durbin chain (`:81`) + the order-N `Minus`-tree
(`order_n_concepts.py`). Cross-speaker prototype = the **medoid** over the
proto-speaker pool selected by the native `DtwTo`
(`scripts/stage3_invariance_clean16k.py:130–160`) — pure selection, no learned /
averaged / fitted template. Decision = native graph `DtwTo`
(`native_cognition.py:76`). Gate = the STRUCTURAL cross-speaker cluster gap d',
NOT a held-out LOSO accuracy. CortexLoop / `solve_for_n` / runners UNTOUCHED; no
Rust changed; 16 kHz NOT downsampled.

---

## 2. The readiness gate — cross-speaker structural invariance (numbers, not boolean)

The IDENTICAL structural harness ran on each representation: a cross-speaker
prototype per digit (medoid over 3 held proto-speakers), then every token from the
**other 27 speakers** (1565 tokens) scored by native `DtwTo` against all 10 digit
prototypes. Within-word = distance to its own digit's prototype (a *different*
speaker); between-word = mean distance to the other digits. The standardized gap
`d' = (between.mean − within.mean) / pooled_sd` is the SAME metric the Stage-1
gate read.

| Representation | within (cross-spk) | between | sep frac | **d'** | residual speaker var |
|---|---|---|---|---|---|
| Stage-1 coarse squint (baseline, same harness) | 0.0238 | 0.0253 | 0.676 | **0.075** | 0.365 |
| **Stage-3 VTL-norm + dynamic gesture** | 0.5785 | 0.6048 | 0.658 | **0.278** | **0.209** |
| Stage-3 dynamic gesture alone (velocity) | 0.3491 | 0.3552 | 0.556 | 0.102 | 0.146 |

Read-the-numbers:

- **d' rises 0.075 → 0.278 (+0.203)** on the identical cross-speaker harness, and
  clears the Stage-1-coarse **0.096** reference outright. The coarse baseline,
  re-measured under this *stricter* cross-speaker medoid harness, reads d'=0.075
  (consistent with the 0.096 the looser single-proto-speaker Stage-1 gate reported
  — same property, harder measurement). The like-for-like comparison is 0.075 vs
  0.278; the absolute-reference comparison is 0.096 vs 0.278. Both clear.
- **Residual speaker variance removed: 0.365 → 0.209** (−0.156). The fraction of
  within-word cross-speaker variance explained by *which speaker* drops by ~43 %:
  the VTL normalisation + gesture cancels speaker dependence the coarse squint left
  in. The gesture-alone representation removes the most speaker variance (0.146),
  confirming the order-1 motion is the most speaker-stable component — but it is
  too thin to separate the words on its own (d'=0.102), so the combined
  level+motion descriptor (d'=0.278) is the right invariant.
- The combined representation's within-word cross-speaker scatter is larger in raw
  DtwTo units (0.107 vs 0.021) only because the 6-channel log-formant trajectory
  lives on a different scale than the 3-band squint — d' is scale-free (it
  standardizes by pooled sd), which is why d' is the gate, not raw distance.

---

## 3. VERDICT

**STAGE 3 COMPLETE — the gate fires.** The speaker-invariant representation
(VTL-normalisation + the order-N dynamic gesture, aligned by the native `DtwTo`)
makes the same word admit the same structure across the 30 speakers
**substantially more** than the coarse squint: the standardized cross-speaker
cluster gap rises from d'=0.075 (same harness) / 0.096 (Stage-1 reference) to
**d'=0.278**, while the residual speaker variance drops 0.365 → 0.209. The
invariant transform has a clean signal under it (the sharp Stage-0 native formant)
and it raises cross-speaker coherence — exactly the Stage-3 readiness signal, read
structurally, not from a banked accuracy.

**Honest qualifiers (the precise frontier within / after Stage 3):**

- d'=0.278 is a clear *separation of clusters* but a modest absolute gap — the
  structure is admitted, not saturated. The gesture-alone channel removes the most
  speaker variance yet separates words weakly; the level channel separates words
  but carries more residual speaker variance. A future refinement is fusing them by
  measured reliability (T8 weighted-admissibility) rather than concatenation.
- The residual 0.209 speaker-variance fraction is the remaining cross-speaker
  scatter — the next within-invariance lever (sharper formant tracking / register
  normalisation), not a blocker for proceeding.
- Per the curriculum's discipline, this is the STRUCTURAL readiness gate only; the
  held-out LOSO accuracy test belongs AFTER the curriculum, never as the per-stage
  gate, and was deliberately not banked here.

Next stage (per the agent's order): **Stage 4 — close the grounding loop, then
babble-refine** (the inverse is now speaker-robust enough to be worth grounding).
