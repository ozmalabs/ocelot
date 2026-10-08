# PREREG — real-text uplift for the Seldon-confidence T2 forecaster

**Committed BEFORE any number is produced.** Per the repo's PREREG-then-measure
discipline (`docs/CODE_MAP.md` §`scripts/`): a `*_PREREG.md` is committed before
the change/measurement, a script performs it, and a `*_RESULTS.md` reports what
happened — never edited after the fact. This file is the contract; nothing below
the "MEASUREMENT GATE" line may be softened once numbers exist.

Successor to `drafts/seldon_t2_poc/` (the synthetic-token PoC, ~6% uplift on a
**stubbed** text pipeline). This prereg replaces the stub's single hand-built
`TextToken{t, entity, incoming_regime, spurious}` with a REAL text→graph→signal
pathway and measures what survives.

---

## 0. What the PoC proved and what it stubbed (the gap this closes)

PROVED (kept, not re-litigated here):
- `crps.py` — exact CRPS on a stepped predictive distribution, cross-checked
  against the energy-score form. Reused verbatim (the scorer is not under test).
- `SeldonConfidenceForecaster` — a reachable-set + stepped-confidence forecast is
  CRPS-scorable and calibratable; conditioning the confidence mass on a clean
  regime signal reduces CRPS (~6% synthetic).

STUBBED (the gap):
- `data.TextToken(t, entity, incoming_regime, spurious)` is the OUTPUT of a
  complete NLP pipeline handed to the forecaster for free: already **dated** (`t`),
  already **entity-linked** (`entity`), already **event-extracted into a
  forecast-relevant claim** (`incoming_regime`). Every hard step was skipped; the
  PoC measured only the last mile (clean signal → confidence-mass shift).

This prereg builds the skipped steps from real machinery and measures the uplift
that survives real extraction + linking.

## 1. Architecture under test (what maps to what)

Five legs, each pinned to an EXISTING, cited substrate mechanism. The claim is
that only leg (ii) is a genuine ceiling; the rest are proven mechanisms or
adapted templates.

- (i) **Bulk document ingestion** — the `domains/arxiv_local.py` `_load()`
  pattern (one pass over on-disk files; structural markers `_ENV_RE` delimit
  typed items → `{kind, key, attribution, paper, text}`), re-pointed at a
  timestamped item corpus. Emits `CorpusItem{doc_id, tick, text,
  mention_surface, claim_kind}`.
- (ii) **Entity linking (THE CEILING)** — `seeds/intent.json`
  `rule_mention_resolves_to_concept` (local_id 990): `Mention.text == Concept.name`,
  **exact-lexical**. Widened by a pre-taught alias seed
  (`Concept{name, aliases:[...]}`). Still lexical; recall is the binding variable.
- (iii) **Claim → typed record** — the arxiv importer's `kind`/`attribution`
  capture is the template: structural position + a small typed vocabulary maps
  prose to `claim_kind` (the real analogue of `incoming_regime`).
- (iv) **Time as a minted coordinate dimension** — NOT a bespoke `valid_time`
  subsystem. `tick` is `coord:t`, the coordinate the corpus varies along, exactly
  the `dim_types` slot `TimeInfer`/`DimInfer` read. As-of cutoff = a bound on that
  coordinate (`tick <= cutoff`), the extensive-frontier bound; unknown = absence,
  first-class.
- (v) **Forward projection + confidence shift** — `TimeInfer`
  (`runners/dsl/src/shape_decode.rs::eval_time_infer`, `seeds/time_axis.json`
  v1.2.0), the embodiment-proven op (F-16 flight-path control
  `scripts/gen_f16_flight_path_control_seed.py`; scalar sensor channels
  `scripts/gen_surprise_promotion_seed.py`) that fits a transition generator over
  a tick-ordered sequence and rolls it forward to a horizon.

### 1.1 HONEST BOUNDARY on leg (v) — stated before measuring

`TimeInfer.predicted` = `G^K(f0)` is a SINGLE exact-orbit POINT projection under a
rigid generator, verified by exact equality with no residual slack. It is a
deterministic reachable-set **center + order-fit**, NOT itself a stepped credence
distribution. Therefore:

- `TimeInfer` supplies the reachable-set **center** (and, at the measured order,
  the curvature the linear reading throws away) **graph-natively**.
- The stepped confidence **MASS** still comes from the empirical innovation kernel
  (the PoC's `_propagate` convolution), centered on / widened around the
  `TimeInfer` projection.

We will NOT claim `TimeInfer` replaces the whole `_propagate`. The graph-native
contribution measured is: does centering the confidence mass on the `TimeInfer`
forward projection (vs. the PoC's raw last-value point mass) change CRPS at all?
This is a SEPARATE, smaller claim from the text uplift and is reported separately
(see H3).

## 2. Corpus honesty — real vs. synthetic

The PoC used synthetic-with-known-DGP because a text-uplift study needs text that
PROVABLY carries signal (so a null means "the mechanism failed", not "the text was
uninformative"). We keep a known DGP for the PANEL and the *ground-truth events*,
but the TEXT the pipeline actually reads is REAL natural-language prose, not a
struct. Concretely:

- The panel + true regime-switch schedule are generated exactly as
  `drafts/seldon_t2_poc/data.py` (regime-switching AR(1), integer cells).
- Each real switch (subject to `text_recall`) emits a **surface-form news item**:
  a natural-language sentence naming the entity (by a name/alias/ticker sampled
  from an alias table) and describing the incoming regime in prose, timestamped at
  `t_switch - lead`. Spurious items (subject to `text_noise`) are emitted with no
  switch behind them. The sentence templates + alias table are FIXED and committed
  in this prereg's `corpus_gen.py`; the forecaster never sees the struct — it sees
  only the rendered prose + its `tick`, and must ingest → link → type it back.

This isolates the exact thing under test: the DGP guarantees the text is
informative; any uplift LOST relative to the PoC's ~6% is attributable to
ingestion/linking/typing loss, which is what we want to measure. A separate
"oracle-link" arm (H2) upper-bounds that loss.

## 3. Metric

CRPS (lower better) on the stepped predictive distribution, `crps.crps_stepped`,
reused verbatim from the PoC. Rolling-origin evaluation: at each cutoff, forecast
every entity at horizons h=1..H, score against the realised value.

## 4. Arms (all emit the SAME stepped-distribution object)

1. `climatology` — text-blind baseline A (empirical history distribution).
2. `gauss_ar1` — text-blind baseline B (AR(1) predictive, discretised). The
   standard statistical baseline T2 demands uplift over.
3. `seldon_notext` — reachable-set + confidence, no text.
4. `seldon_text_real` — leg (i)–(v) full real pipeline: ingest prose → link →
   type → as-of-bounded confidence shift.
5. `seldon_text_oracle` — IDENTICAL to arm 4 but linking + typing use the
   ground-truth struct (the PoC's clean path). Upper bound; isolates leg-(ii)/(iii)
   loss.
6. `seldon_text_real_tinfer` — arm 4 with the confidence mass CENTERED on the
   `TimeInfer` forward projection instead of the last-value point mass. Tests H3.

## 5. Hypotheses (falsifiable, with pre-declared decision rules)

- **H1 (headline): real-text uplift is positive.**
  `seldon_text_real` has lower mean CRPS than `seldon_notext`.
  Decision: paired bootstrap (10k resamples, per-(entity,horizon,cutoff) paired
  deltas) 95% CI on `(notext - text_real)/notext` uplift %. **CONFIRMED** iff CI
  lower bound > 0. Pre-registered plausible range: **1–8%**; a CI overlapping 0 is
  a **NULL** and is reported as the headline finding (per CLAUDE.md: a localising
  null beats a hidden pass).

- **H2 (ceiling attribution): the loss is in linking/typing, not the mechanism.**
  Report `seldon_text_oracle` uplift and `seldon_text_real` uplift side by side.
  Pre-declared reading: if `oracle` recovers ≈ the PoC's ~6% and `real` is
  materially lower, the gap IS the leg-(ii)/(iii) tax and we report the measured
  **link recall** as its proximate cause. No pass/fail; this is attribution.

- **H3 (graph-native projection, SEPARATE + smaller): centering on `TimeInfer`
  does not hurt.** `seldon_text_real_tinfer` vs `seldon_text_real`.
  Decision: CI on the CRPS difference. **NEUTRAL-OR-BETTER** iff the CI upper
  bound on `(tinfer - real)` CRPS is ≤ a pre-set epsilon (0.5% of baseline CRPS).
  We do NOT predict an improvement — the PoC `_propagate` already centers well on
  a mean-reverting DGP; the claim is only that the graph-native projection is not
  a regression, establishing the substrate op is usable here.

- **H4 (as-of discipline holds): no future leakage.**
  A leakage probe: re-run arm 4 with the as-of coordinate bound DISABLED
  (`tick <= cutoff` removed). Pre-declared: the no-bound arm MUST score better
  (it cheats). If it does NOT, the pipeline is not actually using the text and H1
  is suspect regardless of its CI. This is a validity check on H1, not a feature.

## 6. Measured secondary quantities (reported, not gated)

- **Link recall** — fraction of emitted real-switch items whose `mention_surface`
  resolved to the correct panel-entity `Concept`, with and without the alias seed.
  This is the proximate cause behind any H1/H2 gap.
- **Type precision/recall** — fraction of items whose `claim_kind` matched the
  ground-truth incoming regime.
- **Calibration** — randomised PIT histogram for `seldon_text_real` (reused from
  the PoC's `calibration.py`); T2 has a calibration gate, so an uplift on a
  miscalibrated forecast is not a win.
- **Multi-seed spread** — H1 uplift across ≥10 seeds (mean/sd/min/max, n positive),
  per the PoC's `multiseed.py`, so the headline is not one lucky seed (STANDING
  RULE: power the gate before the endgame).

## 7. What a null means (pre-committed interpretation)

- H1 CI overlaps 0 with HIGH link recall → the mechanism (v) does not convert a
  real-but-noisy signal into CRPS gain even when linking works. A real mechanism
  null. Report as headline.
- H1 CI overlaps 0 with LOW link recall → the ceiling is leg (ii) exact-lexical
  linking (as pre-judged). H2's oracle arm confirms the mechanism is fine; the
  finding is "entity linking caps the number," and the next lever is linking, not
  the forecaster.
- H3 CI exceeds epsilon → the graph-native projection is a regression here; report
  it, keep `_propagate` centering, and note `TimeInfer`'s exact-orbit rigidity is
  the wrong shape for a noisy mean-reverting series (a localising null about the
  op, not about time-as-dimension).

## 8. Files (this draft)

- `corpus_gen.py` — panel + REAL-prose timestamped corpus (fixed templates/alias
  table committed here); the struct is hidden from the forecaster.
- `ingest.py` — leg (i)+(iii): arxiv-`_load()`-pattern reader over the corpus →
  `CorpusItem`.
- `linking.py` — leg (ii): `mention_surface` → panel-entity via the referent rule
  + alias seed; reports recall.
- `forecast_text.py` — legs (iv)+(v): as-of-bounded confidence shift; optional
  `TimeInfer` centering.
- `run_gate.py` — the measurement gate (§4 arms, §5 hypotheses, §6 secondaries);
  runs the CRPS correctness gate first, aborts on failure.
- `T2_TEXT_UPLIFT_RESULTS.md` — written ONLY after `run_gate.py` produces numbers.

## 9. Reuse (verbatim, not re-implemented)

`crps.py`, `calibration.py`, the panel DGP in `data.py`, and the arm-scoring /
bootstrap scaffolding in `run_poc.py` / `multiseed.py` are imported from
`drafts/seldon_t2_poc/` unchanged where possible. Only the text half is new.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
