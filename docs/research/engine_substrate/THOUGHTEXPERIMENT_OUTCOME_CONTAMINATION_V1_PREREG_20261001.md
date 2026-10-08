# Thoughtexperiment outcome contamination v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does one false positive outcome attribution overturn the useful ranking effect of automatically persisted experience?

## Design

In each of three fresh workers, train the existing shape-axis correction through the production `scan_and_self_correct` hook. Fork two equivalent recurrence-task branches from the trained graph. The clean arm receives only the two authentic persisted outcomes. The contamination arm receives one deliberately injected positive `CorrectionOutcome` attributed to the tempting `episode_scoped_offer_guard` class, although that guard is known from the independent staged oracle to suppress the second valid candidate. This single-record perturbation is an explicit adversarial label-noise control; it is not presented as a naturally occurring event.

Both arms use the same graph-authored ranking Program, the same staged task, the same candidate generator, the same independent `[1, 1]` one-offer-per-candidate oracle, and native full-copy candidate branches. Record counts and rank traces are captured. Each branch must remain unchanged during candidate rehearsal. Source hashes and engine provenance are recorded.

## Gates

- Three fresh workers, stable relevant source hashes, and graph-authored rank Programs in both arms.
- Training uses production correction and persists exactly two authentic outcomes; clean arm inherits those records unchanged.
- Contamination arm adds exactly one positive outcome with the declared false attribution; clean arm receives no such record.
- Clean arm ranks `dedup_identity_fix` first and passes the independent oracle on trial one.
- Contamination effect is reported without post-hoc exclusion; record the first candidate, first oracle output, and trials to success in every worker.
- Both arms eventually pass the oracle and preserve their branch primaries.

## Interpretation limits

This is a deliberately severe one-record perturbation on an authored task and utility class. It measures sensitivity, not the prevalence of misattribution or the expected field error rate. A contaminated ranking failure would establish a concrete robustness gap; it would not show the whole substrate is unreliable. A null effect would apply only to this candidate pair and noise magnitude.
