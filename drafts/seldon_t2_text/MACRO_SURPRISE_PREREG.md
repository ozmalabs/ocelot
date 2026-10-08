# PREREG — macro-release numeric-surprise mechanism (the H1 macro_release 0.0 residual)

**Committed BEFORE any number.** PREREG-then-measure + CLAUDE.md. Closes the one
coverage gap the induced-belief arc left open: H1 scored **0.0 on macro_release
snippets** (INDUCED_BELIEF_RESULTS.md) because the ToM decode types SPEECH-ACT
purpose, and a CPI/NFP print is not a speech act — it is a NUMBER whose
forecast-relevance is its SURPRISE vs expectation. F4 (tail/shock-from-text, 31
units) and the macro-carrying F2 cards lean on exactly this.

## What the real corpus/panel actually provides (verified, not assumed)

- **Bare release snippets carry released + prior, not consensus.** e.g.
  "The all items index rose 2.7 percent … after rising 2.6 percent" (CPI
  accelerating); "CPI-U rose 0.6 percent in August, after increasing 0.2 percent
  in July." Their study-set gold `direction` is `None` — the labelers correctly
  did NOT treat number-reading as a directional speech act.
- **The corpus DOES carry qualitative surprise language** elsewhere:
  "stronger-than-expected activity," "below their expectations," "weaker
  according to surveyed producers." This is a text-recoverable surprise cue.
- **The macro panel carries the numeric series** (`macro/releases_quarterly`:
  CPI_ALL, CPI_CORE, NFP, GDP as `[date, asset, value, panel_id]`), so a
  quantitative expectation baseline (trend) is derivable from the panel itself.

## The mechanism (two honest paths, one target)

Numeric surprise = released value vs EXPECTATION → sign → rate-band direction.
Expectation is derivable two ways, and the mechanism uses whichever is present:

- **QUANTITATIVE path (panel + text numbers):** the expectation is the series'
  own recent TREND baseline (last value / short MA from the macro panel, or the
  "after rising X" prior in the snippet). surprise = released − trend. Sign maps
  to a stance: hot inflation (CPI above trend) or strong labor (NFP above trend)
  → hawkish/up (+1); cool/weak → dovish/down (−1). This is the frame's causal
  semantics as TAUGHT DATA (a `MacroSurpriseSign` codebook keyed on series →
  which sign of surprise is hawkish), NOT a Python branch deciding it.
- **QUALITATIVE path (corpus surprise language):** "stronger/hotter/above
  expectations" → +surprise; "weaker/cooler/below expectations/missed" →
  −surprise. A small taught cue lexicon, same class as the ToM speech-act
  codebook. This path handles docs with no clean number.

Both paths emit the SAME shape as the ToM arm: the surprise becomes EVIDENCE
applied to the SAME `<stance>_stance_for:<market>` CAN Concept via
`concept_apply_evidence` (the reused belief-update primitive). So macro-surprise
COMPOSES with the ToM decode on one belief, rather than being a parallel
mechanism. Grounding-weighting and the GroundingGap guard apply unchanged (the
surprise read grounds transitively like any other; a read with no number and no
cue reaches no anchor → shifts ~0).

## Discipline (CLAUDE.md — non-negotiable)

- REUSE: `mint_target_concept` / `concept_apply_evidence` / the grounding-reach
  read / the ToM arm's decode→shift path. The macro path adds only (a) a
  `MacroSurpriseSign` codebook (taught data), (b) a surprise-cue lexicon (taught
  data), (c) a mechanical read of released-vs-trend from panel/text. NO new
  parallel belief mechanism; NO Python decision over graph state — which sign is
  hawkish is codebook DATA, the direction is read off the graph like the ToM arm.
- Numbers are parsed mechanically from text/panel (I/O), never a decision.
- If a seam blocks reuse, GENERALIZE the existing machinery (net-win gate:
  bigville/ToM paths stay green), never fork.

## Hypotheses (falsifiable, pre-declared)

- **H-M1 (recovery — headline):** on the macro_release snippets H1 scored 0.0 on,
  the surprise mechanism recovers a forecast-relevant direction (hot→up,
  cool→down) at accuracy materially > 0. Gold: derive the correct direction per
  macro snippet from released-vs-prior (CPI/NFP up vs prior with hawkish sign →
  up; etc.) — a small hand-labeled extension of the frozen study set, labeled
  BEFORE measuring. CONFIRMED iff macro-snippet directional accuracy > 0.5 (a
  coin flip is 0.5 on a binary up/down; 0.0 was the ToM arm's score). A null
  (still ~chance) means numeric surprise as framed does not carry direction on
  these prints — reported as headline.

- **H-M2 (composes, does not regress ToM):** adding the macro path does NOT
  change the ToM arm's H1 numbers on non-macro doc_types (fomc/cb_speech/8-K/COT
  stay byte-identical) — the macro path fires ONLY on macro reads. CONFIRMED iff
  the H1 per-doc_type table is unchanged except macro_release improves.

- **H-M3 (surprise → composite via the shift):** on the direction-aware proxy
  (H2_RESOLUTION's `make_realized_text_aware`, reused), a correctly-typed macro
  surprise applied as a graded shift lowers composite vs no_shift on macro-carrying
  units, same instrument as H2a. CONFIRMED iff composite(macro shift) <
  composite(no_shift) across the p_signal/e sweep. RAW_UNRANKABLE stated.

## What a null means (pre-committed)

- H-M1 null → numeric surprise on quarterly/monthly prints is too weak or
  ambiguous to type direction (e.g. a CPI beat is hawkish for rates but the sign
  depends on regime); the honest arm leaves macro reads to grounding→0 silence,
  and F4 tail coverage stays a known gap, not a fabricated signal.
- H-M2 regression → the macro path leaked into non-macro reads; reject, gate it
  strictly to macro doc_types.
- H-M3 null with H-M1 confirmed → the direction is recoverable but the shift does
  not convert it to composite on macro units (as H2b found the magnitude policy
  matters); localizes to the shift, not the surprise read.

## Deliverables

- `MACRO_SURPRISE_RESULTS.md` — H-M1 macro-snippet accuracy vs the 0.0 baseline,
  H-M2 non-regression table, H-M3 composite sweep, proven-vs-assumed ledger.
- `induced_belief/macro_surprise.py` (the read) + taught `MacroSurpriseSign`
  codebook + surprise-cue lexicon; wired into the arm behind the same text-arm
  flag, gated to macro doc_types; output still admissible g0–g3.
- a hand-labeled macro-direction extension of the study set, labeled before
  measuring (committed in the prereg's spirit — labels frozen before H-M1 runs).

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
