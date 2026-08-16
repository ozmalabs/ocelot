# Shared arousal / excitation transfer — RESULTS

Registered design: `SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md`. **All 4
predictions confirmed.**

## 1. Live run (`scripts/shared_arousal_demo.py`)

```
=== Prediction 1: hostility spikes arousal, amplifies desire update ===
after hostile incident: arousal_level=0.800
desire incident RIGHT AFTER: effective_alpha=0.540 external_field=0.540

=== control: same desire incident, no prior arousal ===
control: effective_alpha=0.300 external_field=0.300

=== Prediction 2: symmetry -- desire-driven arousal amplifies a later hostility incident ===
hostility incident after a desire spike: effective_alpha=0.540 (vs control base_alpha=0.3)

=== Prediction 3: arousal decays without fresh spikes ===
tick 0 (post-spike): level=0.8000
tick 1 (zero-intensity incident, decay-only): level=0.5600
tick 2 (zero-intensity incident, decay-only): level=0.3920
tick 3 (zero-intensity incident, decay-only): level=0.2744
tick 4 (zero-intensity incident, decay-only): level=0.1921

=== Prediction 4: arousal is per-target, not global ===
Sam's desire incident, unaffected by Alex's hostility spike: effective_alpha=0.300 (expect 0.3)
```

## 2. Predictions

1. **Elevated arousal strictly amplifies a co-target incident's effect** —
   `PASS`. `0.300 → 0.540`, a +80% amplification purely from shared
   arousal, zero change to the evidence itself.
2. **Symmetry — works regardless of which relation fires first** — `PASS`.
   Desire-driven arousal (`intensity=0.8`) amplifies a subsequent
   hostility incident to the identical `effective_alpha=0.540` measured in
   prediction 1 — confirms the pool is valence-blind (Schachter-Singer),
   not a one-way "hate boosts desire" special case.
3. **Arousal decays without fresh spikes** — `PASS`. Fixed multiplicative
   decay (`×0.7`/call) takes level `0.8000 → 0.5600 → 0.3920 → 0.2744 →
   0.1921`, monotonically toward 0, confirmed via `record_targeted_incident`
   itself (`intensity=0.0` calls), not just a manual formula check —
   closes the loose end named after the initial ad hoc verification.
4. **Arousal is per-target, not global** — `PASS`. Alex's hostility spike
   (`level=0.8`) leaves Sam's arousal at its baseline `0`; Sam's desire
   incident gets exactly `effective_alpha=0.300`, unaffected — matches
   Dutton & Aron's own design requirement that misattribution needs the
   SAME person present, not any arousing stimulus plus any nearby target.

## 3. Honesty notes

**Does establish**: a working, regression-tested excitation-transfer
mechanism — arousal connected to a target is a single shared,
valence-blind pool read by every belief update about that target, exactly
as Zillmann's theory and the Dutton & Aron bridge study predict. Checked
explicitly against this arc's own retracted `belief_plasticity` 1/n
anti-pattern before registering (`PREREG.md` Sec2) and confirmed
structurally different: `decay` is a fixed multiplicative constant toward
a bounded quantity (real autonomic arousal), not a count-divided rate
trying to track an unboundedly-refining statistic.

**Does NOT establish**: the full "hate" attribution mechanism named in
the prior discussion (`regard_for:<target>` reaching a stable
global-negative low-plasticity state via the attribution-locus machinery)
— out of scope here, named and deferred, same as the PREREG says. Does
NOT independently validate `decay=0.7` against real autonomic-arousal
decay curves — a documented, un-fitted constant, same honesty class as
this arc's other constants (`base_coupling=0.6`, `k=3.0`). Produces no
narrative or depictive content anywhere — every artifact is a scalar, a
Concept name, or a Term formula.

## 4. Files

- `docs/research/psychology_affect/SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md`
- `docs/research/psychology_affect/SHARED_AROUSAL_EXCITATION_TRANSFER_RESULTS.md` (this file)
- `domains/shared_arousal.py` (new)
- `scripts/_build_shared_arousal_seed.py` (new)
- `seeds/shared_arousal.json` (new, generated)
- `scripts/shared_arousal_demo.py` (new)
- `tests/test_shared_arousal_excitation_transfer.py` (7/7, new)
