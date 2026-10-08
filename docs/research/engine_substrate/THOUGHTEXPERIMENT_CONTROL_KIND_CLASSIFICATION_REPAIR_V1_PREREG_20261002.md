# Control-kind classification repair v1 — preregistration

**Date:** 2026-10-02  
**Question:** Can the unchanged correction candidate generator repair a faulted graph-authored string-match classifier on held-out control names in a separate seeded domain?

## Task and split

The target is `classify_kind_family` from `seeds/control_kinds.json`. Its effect ranks matching `FamilySignal` nodes by specificity and writes the selected `family`. The injected fault reverses every comparison in the target rule's effects, making its string-index membership predicate reject present signal words. Candidate generation uses the unchanged `_default_candidates` implementation. Three fresh workers enumerate the candidate set and score every applicable variant on fresh, independently booted substrate instances.

Training names: `rotary dial` → `discrete_select`; `trackpad mouse` → `relative_pointer`. Held-out names: `steering wheel` → `continuous_rotation`; `trigger button` → `discrete_act`. Expected labels are fixed from the explicit signal-word/family/specificity table in the locked seed, with most-specific match winning and equal-specificity signals required to agree on family. The oracle is separate from the worker's candidate ordering. Each case runs in a fresh substrate; workers never receive held-out oracle values as graph records.

## Admission gates

- Three fresh workers with exact source/native lock parity.
- At least three unique applicable candidate bundles, with identical canonical descriptors across workers.
- Every candidate is scored on both training and both held-out cases.
- The unmodified source rule passes all cases and the faulted rule fails all cases.
- At least one candidate passes both held-out cases and at least one fails.
- Held-out names do not occur in the training split; candidate descriptors omit generated rule names before digesting.

A pass admits one additional task family for later ranker evaluation. This is a small, authored lexical classification task; it does not establish natural language coverage, open-ended concept learning, autonomous fault diagnosis, or broad self-improvement. Candidate generation remains host code, and full candidate branch/adoption costs are not measured here.
