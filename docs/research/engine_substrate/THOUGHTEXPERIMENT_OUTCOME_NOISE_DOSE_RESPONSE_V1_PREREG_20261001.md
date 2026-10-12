# Thoughtexperiment outcome noise dose-response v1 — preregistration

**Date:** 2026-10-01  
**Question:** How do false-positive and false-negative outcome records affect cross-family candidate ranking and held-out task utility?

## Design

Three fresh workers each train once through production `scan_and_self_correct`, producing the same authentic graph-resident records. From this trained state, create five isolated evaluation branches: **clean** (no change), **one false positive** (one fabricated positive for the known-bad episode guard), **two false positives** (two independent such rows), **one false negative** (flip the authentic candidate-scoped repair's positive utility to zero), and **mixed** (one false positive plus the false negative). The staged recurrence task, graph-authored policy, candidate generator, and independent one-offer-per-candidate oracle are otherwise identical.

Each arm records inherited rows, candidate rank trace, first oracle output, trials to oracle, final outcome, and primary-state preservation. The false positive is an intentional controlled corruption. The false negative is a branch-local label mutation of actual production evidence. Neither intervention estimates natural noise prevalence.

## Gates

- Three fresh workers; relevant sources remain hash-stable; production correction adopts and persists the authentic records.
- Clean branch exactly inherits authentic evidence and ranks the candidate-scoped repair first, passing on trial one.
- Perturbed branches contain exactly their preregistered false-positive/false-negative changes and preserve the untouched training primary.
- Capture all five arms' first candidate, rank counts, oracle output, and trials to success; do not drop adverse outcomes.
- Every arm eventually passes the independent oracle through bounded candidate fallback.

## Interpretation limits

This is a five-condition sensitivity panel on one authored task and candidate pair. Repeated injected copies probe whether the current aggregate is dose-sensitive after the first decisive record; they are not independent task replications. No noise-rate, natural-task utility, or general learning claim follows.
