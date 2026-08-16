# Envy — RESULTS

Registered design: `ENVY_PREREG.md`. **All 5 predictions confirmed.**

## 1. Live run (`scripts/envy_demo.py`)

```
=== Prediction 1: no disadvantage means no envy, regardless of deservingness ===
read_envy(1.0, -5.0) = none
read_envy(0.0, -5.0) = none

=== Prediction 2: a deserved disadvantage produces benign envy ===
relative_self_worth (disadvantaged): -0.7918
deservingness=0.3000 -> envy=benign

=== Prediction 3: an undeserved disadvantage produces malicious envy ===
relative_self_worth=-0.7918 deservingness=-0.3000 -> envy=malicious

=== Prediction 4: the deservingness belief ALONE flips the verdict ===
fixed relative_self_worth=-0.7918
  deservingness=+0.3 -> benign
  deservingness=-0.3 -> malicious

=== Prediction 5: domain isolation ===
chess deservingness (3x undeserved): -0.9000
football deservingness (untouched): 0.0000
```

## 2. Predictions

1. **No disadvantage means no envy** — `PASS`, confirmed at both a
   strongly positive and an exactly-zero `relative_self_worth`, with a
   strongly negative deservingness value in both cases (proving
   deservingness alone cannot produce envy without a real disadvantage).
2. **A deserved disadvantage produces benign envy** — `PASS`.
3. **An undeserved disadvantage produces malicious envy** — `PASS`,
   confirmed at the SAME magnitude of disadvantage as prediction 2
   (`-0.7918` in both live runs).
4. **The deservingness belief alone flips the verdict** — `PASS`, the
   central claim. Holding `relative_self_worth` FIXED at exactly
   `-0.791759469228055`, only the deservingness value differs between
   the two calls, and the verdict flips `benign → malicious` — isolating
   the injustice appraisal's own causal role from the comparison itself.
5. **Domain isolation** — `PASS`. `football`'s deservingness belief
   reads exactly `0.0000` despite `chess` having accumulated 3 rounds of
   "undeserved" evidence on the same resident.

## 3. Honesty notes

**Does establish**: envy's benign/malicious split (Van de Ven, Zeelenberg
& Pieters 2009) as a genuine, isolated function of the deservingness
appraisal, reusing `relative_self_worth` (Festinger 1954's social
comparison, already built and tested by `RELATIVE_SELF_WORTH_
PREREG.md`) with ZERO changes to that mechanism. `read_envy` is proven a
pure function, not incidentally correlated with anything else in the
graph — prediction 4 holds the comparison term bit-identical across both
calls.

**Does NOT establish**: any downstream consequence Concept for either
envy type (hostility-toward-the-advantaged-peer for malicious envy,
self-improvement motivation for benign envy) — `read_envy`'s
classification is this rung's full scope, a named, deferred follow-on
mirroring `SELF_CONSCIOUS_CONSEQUENCE_PREREG.md`'s own eventual
consequence layer for shame/guilt. Does NOT make `deservingness_belief_
for` target-specific (peer-scoped) — a real, separate, un-built
refinement, domain-scoped by design here.

## 4. Files

- `docs/research/psychology_affect/ENVY_PREREG.md`
- `docs/research/psychology_affect/ENVY_RESULTS.md` (this file)
- `domains/envy.py` (new)
- `scripts/envy_demo.py` (new)
- `tests/test_envy.py` (7/7, new)
