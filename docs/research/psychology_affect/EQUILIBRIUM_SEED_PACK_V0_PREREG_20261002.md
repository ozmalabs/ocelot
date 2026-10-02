# EQUILIBRIUM SEED PACK v0 — PREREG (DRAFT)

**Date:** 2026-10-02. **Status: DRAFT, not yet frozen.** It becomes binding when it is committed *before* the sealed validation split is opened. Base `main @ 8bac3e90`. Worktree `/home/matt/ozmadev/ocelot/.worktrees/t3`, branch `t3/equilibrium-seed-pack-v0`. Design: [`EQUILIBRIUM_SEED_PACK_V0_DESIGN_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_DESIGN_20261002.md). Spec: Equilibrium `DESIGN.md` §16.7 risks 1–4, §21 harness, §23 Phase 9. Not merged to main, not pushed — left for the orchestrator's independent re-verification.

**HEADLINE (predicted, checked in the RESULTS doc):**
1. The sidecar base revision is byte-identical after 10,000 synthetic messages in every shipped frozen mode.
2. Frozen-reload (F1) mode does **not** reach the 4,000 msgs/s pool target on one host. Fork mode, if available, is faster than F1 per batch.
3. Sealioning and goalpost shifting reach the §Q bar on validation and will be re-checked on test. Even if they pass, they stay `shadow` until Equilibrium's R15 fairness audit.

## D. Data

* Corpus: Equilibrium §16.9 (accessed Equilibrium-side only; Ocelot never stores text).
* Splits are UTC half-open:
  * train `[2026-01-01T00:00:00Z, 2026-08-01T00:00:00Z)`
  * validation `[2026-08-01T00:00:00Z, 2026-09-01T00:00:00Z)`
  * test `[2026-09-01T00:00:00Z, 2026-10-02T00:00:00Z)`
* The Equilibrium T7 prereg found that exporter-local dates produced the §16.9 counts. The per-split counts under the UTC bounds are recorded in the authoring receipt and may differ from §16.9. That difference is reported, not reconciled.
* The authoring receipt must show `max_ts_seen < 2026-08-01T00:00:00Z` and carry the `seed_pack_sha256` of the evaluated pack. A missing receipt voids the evaluation.
* Validation is opened once, after this doc is frozen. Test is opened once, after the pack hash is frozen post-validation.

## P. Pre-fixed parameters (frozen on train, before validation)

* Pattern window bounds (design default 50 msgs / 72 h) are fixed on train only.
* Lexicon contents are fixed at the receipt's `seed_pack_sha256`.
* No changes are allowed between validation and test except those listed in a validation addendum committed before test opens.

## Q. Quality (risk 4)

* Human labels come from Equilibrium annotators, blinded to Ocelot output, ≥ 2 per item. Report Cohen's/Krippendorff's κ. A label is *unevaluable* if κ < 0.4.
* Sample: stratified by guild and by register stratum (below). n ≥ 200 windows per v0 pattern label and n ≥ 500 messages for msg labels per split.
* Bar for proposing `enabled` (Ocelot pack status): precision ≥ 0.80 with a 95% Wilson lower bound ≥ 0.70, and recall reported (no bar in v0). Per-stratum precision is reported. Any stratum whose precision lower bound is < 0.60 blocks `enabled`.
* Baseline: Equilibrium's structure-only signals, compared using `evaluation/comparative_release_gate.py` scorecards.

## F. Fairness strata (reported, not gated here; R15 gate is Equilibrium Phase 10)

The strata are dialect/register (terse, formal, slang-heavy), self-declared or detected non-native English, non-English script (`_detect_language`), help-channel newcomer vs regular, and timezone band (for selective non-response, later). The registered red-team evasions from DESIGN §1.2 are run as a synthetic adversarial set with reported miss rates.

## M. Systems measurements (risks 1–2)

* **Base unchanged:** strong digest of `graph_to_dict(base)` before and after a 10,000-message replay (100/batch), plus zero files written outside tmpfs. Prediction: identical.
* **Throughput:** msgs/s at concurrency 1, 2, 4, N cores, batch 100, on synthetic messages length-matched to the train length distribution (counts only). Measured for F1, F2 and fork (if WI-0 lands). Report median and p95 batch latency. Prediction: F1 < 4,000 msgs/s on one host.
* **Memory:** peak RSS with the pack loaded at each concurrency. Prediction: F1 with concurrency ≥ 3 exceeds 384 MB.
* The COW figures cited by Equilibrium are treated as unverified priors and are not used as the comparison.

## X. Exclusions and stopping

Messages without a parseable UTC timestamp are excluded and counted. If κ < 0.4 for a pattern label, that label is reported unevaluable and stays `shadow`. There is no re-annotation round within v0.
