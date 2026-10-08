# RESULTS — Tier-A is ill-posed: the oracle fails its own exact gate while passing its own realism gate

**Measured against `T3_WELLPOSEDNESS_PREREG.md` (the contract). Nothing above that
file's MEASUREMENT GATE was edited once numbers existed.** This is a WELL-POSEDNESS
THEOREM about Track 3's exact gate; the output is INFORMATION (a held, transferable
shape), not a speed number. Both landings were pre-committed as valid; this reports the
one the numbers gave.

## HEADLINE — the theorem STANDS (with one honestly-scoped caveat)

**Does the reference simulator fail its own exact gate while passing its own realism
gate? YES.**

Under a valid latency-only re-seed (agent decision RNG held fixed — verified separable
in Half 1), scored on the SAME bytes against its OWN reference-cache trace through BOTH
organizer gates:

- **Tier-A (exact): the oracle FAILS 60 / 60 stochastic re-seeds.** (5/5 passes exist
  only on the deterministic-latency control, where the re-seed draws nothing — the
  instrument's own null.)
- **Tier-B (organizer's tolerant statistical gate): PASSES 59 / 60 of those SAME
  traces.** The one miss is KS = 0.08052 vs the 0.08000 ceiling on a 604-row
  micro-scenario — a 0.0005 overshoot at the ceiling, not a market difference.
- **Return-realism (the two robust Cont stylized facts — return-distribution KS and
  volatility-clustering ACF): PASSES 58 / 60**, uniformly across every family.

So the canonical correct simulator, re-drawing a stream the scenario DECLARES to be
random, is **rejected by Tier-A on 100% of stochastic scenarios while being admitted by
its own calibrated tolerant gates on ~98% of the identical traces.** Tier-A resolves
below the model's own declared noise floor. **It measures implementation identity, not
simulation correctness — ill-posed w.r.t. the stated goal.**

**The honest caveat (does NOT invert the theorem).** The *full* four-statistic
`admissible()` check passes only 35 / 60, because two of its four components are noisy:
the Hill tail-index (41/55 finite passes) and the depth Jensen-Shannon divergence
(47/60). Both breaches are **estimator variance and micro-scenario degeneracy, not the
market moving** (evidence in H-W1 below): 23 of the 25 realism failures still pass KS
AND ACF — the failure is confined to Hill/depth-JS. Those two are known high-variance
estimators; the re-seed's scatter against the *fixed* reference is the estimator's own
noise. The gate's calibrated semantic core — the part the README says the 0.08 tolerance
"comes from the natural run-to-run variation of correct simulations" — is invariant
across the re-draw class. The theorem holds on that core; we report the full-4 number so
the reader judges the caveat directly rather than being asked to trust a scoping choice.

---

## Provenance / discipline

- ABIDES pinned commit `f9cbe51342b7dedd9587e4e069040d68a5c6477f`; scored container
  `track3-abides-baseline:latest` (py3.11, numpy 1.26.4, pandas 1.5.3). The **REAL**
  gate functions, never a bespoke metric:
  `qfbench2_track_simulation.semantics.check_tier_a` (exact),
  `semantics.check_tier_b` (statistical),
  `qfbench2_common.scoring.stylized_facts.stylized_fact_report` + `admissible`
  (realism), with `semantics.mid_price_series` / `semantics.depth_histogram` for
  extraction (the scorer's own). Comparator runs on the host t2venv (py3.13).
- **Perturb via latency SEED only.** Latency `RandomState` re-`seed()`-ed in place after
  `build_config`; agent decision RNGs untouched (Half 1's verified stream split:
  minted `oracle→exchange→agents→latency→kernel` from one master seed). Scored checkout
  UNTOUCHED; all instrumentation is a runtime monkeypatch outside the image.
- **Faithfulness gate passed for all 13 panel scenarios:** the instrumented, un-perturbed
  baseline reproduces the reference-cache `trace.parquet` **exactly**
  (`check_tier_a` PASS, row counts equal). Every movement below is caused by the latency
  seed split, not the instrument.
- **≥3 re-seeds required; 5 run** per scenario (perturb salts p1..p5), the public family
  panel (13 scenarios spanning all six families + the full latency axis).
- PREREG-then-measure; whole distributions reported; no fabricated numbers; the
  inversion was a valid pre-committed landing and is NOT what the numbers gave.

### Organizer thresholds used (the real ones)
| gate | thresholds |
|---|---|
| Tier-A (exact) | timestamp ±1000 ns, Kendall-τ floor 0.999, exact event coverage + exact fill sequence |
| Tier-B (statistical) | mid-price return KS ≤ 0.08, mean-spread ±10 bps |
| realism `admissible` | KS ≤ 0.08, ACF\|r\| L2 ≤ 0.12, Hill\|α\| ≤ 1.5, depth-JS ≤ 0.10 |

---

## H-W1 — the LEMMA: is the realism content invariant across the re-draw class?

For each scenario, 5 latency-only re-seeds (agent RNG fixed) were extracted with the
scorer's own `mid_price_series` / `depth_histogram` and scored against the scenario's own
reference-cache trace. **Whole distributions across the 60 stochastic re-seeds** (the
deterministic control is excluded and reported separately as the instrument's null):

### Per-statistic pass rate + distribution (60 stochastic re-seeds)
| statistic | ceiling | pass rate | median | p90 | max |
|---|---:|---:|---:|---:|---:|
| **KS** (return distribution) | 0.08 | **59 / 60** | 0.0253 | 0.0460 | 0.0805 |
| **ACF\|r\|** (volatility clustering) | 0.12 | **59 / 60** | 0.0304 | 0.0993 | 0.1301 |
| Hill\|α\| (tail index) | 1.5 | 41 / 55 finite | 0.7100 | 2.1005 | 6.2773 |
| depth-JS (book depth) | 0.10 | 47 / 60 | 0.0060 | 0.2552 | 0.5422 |
| **Tier-B** (KS + spread) | — | **59 / 60** | — | — | — |
| **return-realism (KS ∧ ACF)** | — | **58 / 60** | — | — | — |
| full-4 `admissible` | — | 35 / 60 | — | — | — |

**Reading.** The realism gate's calibrated **semantic core is invariant** across the
re-draw class: return-distribution KS and volatility-clustering ACF each pass 59/60, and
jointly 58/60, uniformly across families. Tier-B passes 59/60. The re-drawn latency
stream produces *the same market* by every measure the tolerance was calibrated for.

The full-4 `admissible` rate is lower (35/60) purely because of the two noisy
components — and the failures are attributable, not semantic:

- **Realism-breach attribution across the 60 stochastic re-seeds:**
  Hill 14, depth-JS 13, KS 1, ACF 1. **23 of 25 realism-failing re-seeds still pass
  KS AND ACF** — the failure is Hill/depth-JS only.
- **Hill is a high-variance tail-index estimator.** Its |α_cand − α_ref| scatter against
  the *fixed* reference is the estimator's own noise, not a market change: e.g.
  `eq_pareto_heavytail` 0.71 / 1.95 / 2.05 (min/med/max over 5 re-seeds),
  `ca_baseline_calm` 0.78 / 1.67 / 4.94, `s012` 0.85 / 1.88 / 6.28. A ceiling of 1.5 on a
  finite-sample Hill difference is inside that estimator's run-to-run spread — the same
  scatter a second *correct* reference run would show.
- **depth-JS breaches concentrate in the matching-engine micro-scenarios** where the
  quote/depth stream is degenerate: `s001` (604 rows, Hill is literally NaN — the
  fill-price series is near-constant) and `s012` (fill-dominated). These are Tier-A-by-
  design families (family 1); the realism gate is not the intended arbiter there. Outside
  them, depth-JS medians are 0.001–0.011 — far under the 0.10 ceiling.

### Per-family (pass counts + stylized-fact medians)
| family | scen | Tier-A | Tier-B | full-4 realism | return-realism | ks(med) | acf(med) | hill(med) | js(med) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| matching-engine | 2 | 0/10 | 9/10 | 0/10 | 9/10 | 0.033 | 0.063 | NaN/degenerate | 0.257 |
| latency-profile* | 5 | 0/25 | 25/25 | 24/25 | 24/25 | 0.023 | 0.052 | 0.526 | 0.005 |
| agent-mix | 2 | 0/10 | 10/10 | 9/10 | 10/10 | 0.012 | 0.021 | 0.500 | 0.003 |
| stylized-facts | 2 | 0/10 | 10/10 | 4/10 | 10/10 | 0.038 | 0.020 | 0.745 | 0.016 |
| throughput-scale | 1 | 0/5 | 5/5 | 3/5 | 5/5 | 0.036 | 0.024 | 1.040 | 0.003 |

\*latency-profile excludes the deterministic control (reported below).

**Per-family reading.** In every family the return-realism core (KS ∧ ACF) holds at
≥9/10, and Tier-B at ≥9/10, while Tier-A is 0 everywhere stochastic. The full-4 realism
rate dips exactly where Hill/depth-JS are noisy (stylized-facts, throughput-scale) or
degenerate (matching-engine). **H-W1 is CONFIRMED on the gate's calibrated core; the
inversion condition (re-seed moves the return distribution / volatility clustering
outside ceilings) did NOT occur — KS and ACF stay in-tolerance 59/60.**

### The instrument's null (deterministic-latency control)
`eq_deterministic_baseline`: the latency model performs no draw, so a latency re-seed is
a true no-op. **All 5 re-seeds: Tier-A PASS, Tier-B PASS, realism PASS, all four stats
exactly 0.000.** Reseeding a stream that isn't drawn changes nothing — the split is
surgical and the movements elsewhere are caused by the draw, not the instrument.

---

## H-W2 — the COROLLARY (centerpiece): the oracle scored through BOTH gates on the SAME bytes

The reference ABIDES engine (canonical correct simulator, pinned commit) re-run with a
valid re-drawn latency seed, each output scored against its OWN reference-cache trace
through Tier-A AND the tolerant gates on the identical bytes:

| quantity | count |
|---|---|
| stochastic latency re-seeds scored | **60** |
| **Tier-A FAIL** (exact gate rejects the oracle) | **60 / 60** |
| **Tier-B PASS** on the SAME traces | **59 / 60** |
| return-realism (KS ∧ ACF) PASS on the SAME traces | 58 / 60 |
| **Tier-A FAIL ∧ (Tier-B ∨ return-realism) PASS on the same trace** | **59 / 60** |
| deterministic control (no draw): all gates PASS | 5 / 5 |

**The single joint exception** is `s001` perturb-1: Tier-A fail, Tier-B KS = 0.08052
(0.0005 over the 0.08 ceiling), on a 604-row micro-scenario — it fails Tier-B by a
rounding-scale margin, not because the market moved.

**H-W2 CONFIRMED.** On 59 of 60 stochastic re-seeds the ground-truth simulator
**violates the exactness gate on its own declared physics while its own tolerant gate
admits the very same trace.** This is the gate rejecting the oracle: the sharpest
possible evidence the question is ill-posed. (Half 1 already showed the 0/36 Tier-A
shatter; here it is stated explicitly and scored through BOTH gates on the same bytes,
adding the second half — that those same rejected traces are admitted as realistic.)

---

## H-W3 — the THEOREM

H-W1 (the realism gate's calibrated core is invariant across the latency re-draw class:
KS ∧ ACF 58/60, Tier-B 59/60) **and** H-W2 (the oracle fails Tier-A 60/60 while passing
its tolerant gate 59/60 on the same traces) both hold. Therefore:

> **Tier-A resolves below the model's own noise floor.** The valid latency re-draws form
> an equivalence class the realism/Tier-B tolerances are explicitly calibrated to admit
> as one market (the README concedes 0.08 "comes from the natural run-to-run variation of
> correct simulations"). Tier-A rejects all but one member of that class — it demands
> agreement on the exact-order coordinate that the model's DECLARED stochastic-latency
> physics leaves free. An exactness gate finer than the noise floor of its own stochastic
> physics measures **implementation identity, not simulation correctness.** With respect
> to the competition's stated goal — "a faster simulator that still behaves like a real
> exchange" — **Tier-A is ill-posed.**

The well-posed gate is the one that constrains the semantic invariants (which Tier-B and
the realism core already do) and tolerates the RNG-projected exact-order coordinate
(which Tier-A does not). This is a decided well-posedness result about the QUESTION, not
an opinion about benchmark design, and not the inversion — the inversion required the
return distribution / volatility clustering to move outside ceilings under the re-seed,
and they did not (59/60 in-tolerance).

---

## The transferable shape (stated plainly)

**For any declared-stochastic simulator graded by an exact-trace comparator against a
single reference realization:** the comparator is ill-posed w.r.t. a
"behaves-like-real" goal **iff** there exists a re-draw class of the declared randomness
such that (a) the exact gate rejects ~all of the class, while (b) the tolerant/semantic
gate — calibrated on that same run-to-run variation — admits ~all of it. When both hold,
the exact gate is resolving finer than the model's own noise floor and is testing
implementation identity, not correctness.

The single-line test to transfer: take the reference engine, re-draw ONE declared-random
stream (holding the others fixed), and score the output against its own reference through
BOTH the exact and the tolerant gate. **If exact fails and tolerant passes on the same
bytes, the exact gate is below the noise floor.** Track 3's latency stream satisfies this
at 59/60. The two structural preconditions (from Half 1, why it's this mechanism):
the draw→order map is near-injective in order (order-pivotal fraction 0.81–0.97, so the
re-draw rewrites the event SET, not just timestamps), yet the *market statistics* the
tolerant gate reads are order-insensitive at its calibrated resolution (KS/ACF/spread
invariant). The exact-order coordinate carries the RNG entropy; the semantic coordinate
does not; Tier-A gates the former, the goal lives in the latter.

The complement (the reducible / well-posed case, for completeness): if the re-draw class
were to move the semantic statistics outside their ceilings, the draws would be
semantically load-bearing, the exact gate would be well-formed, and "reproduce the
stream" would be justified. That is the inversion — measured for, not assumed — and it is
NOT this mechanism.

---

## Proven-vs-assumed ledger

| claim | status | evidence |
|---|---|---|
| Instrumented baseline reproduces reference exactly (faithfulness) | **PROVEN** | 13/13 `check_tier_a` PASS, row counts equal |
| Latency & agent RNGs are separable objects; latency-only re-seed is surgical | **PROVEN** (Half 1, re-confirmed) | deterministic control: latency re-seed = exact no-op (5/5 all gates pass, stats 0.000) |
| Oracle fails Tier-A on its own reference under latency re-seed | **PROVEN** | 60/60 stochastic re-seeds Tier-A FAIL |
| The SAME re-seeded traces pass the tolerant gate | **PROVEN** | Tier-B 59/60; return-realism (KS ∧ ACF) 58/60 |
| Oracle fails exact ∧ passes tolerant on the SAME bytes | **PROVEN** | 59/60 joint |
| Return-distribution + volatility-clustering realism is invariant across the re-draw class | **PROVEN** | KS 59/60 (med 0.025), ACF 59/60 (med 0.030) |
| Hill/depth-JS breaches are estimator variance / micro-scenario degeneracy, not market change | **ARGUED, well-supported** | reference is fixed → scatter is estimator noise; 23/25 realism-fails pass KS∧ACF; depth-JS fine (≤0.011 med) outside degenerate matching-engine micros; Hill NaN on 604-row s001 |
| Full-4 `admissible` invariance | **NOT proven** — 35/60 | Hill 14 + depth-JS 13 breaches; reported transparently, not scoped away |
| Tier-A is ill-posed w.r.t. the stated goal | **PROVEN** on the gate's calibrated core (Tier-B + KS/ACF) | H-W1 core ∧ H-W2 |
| Transfer to arbitrary declared-stochastic sims | **CONJECTURED** (mechanism-typed) | precondition test stated; verified only on ABIDES-class here |
| Panel is a census | **FALSE / assumed-representative** | 13 of 65 scenarios; spans all families + full latency axis; no counterexample to the core within the panel |

---

## Not measurable in-env / limits (marked honestly)

- **Panel, not census.** 13 of 65 public scenarios (spanning all six families + the full
  latency axis). Per-family n is small (1–2 outside latency-profile). The Tier-A-fail /
  tolerant-pass split is uniform with no counterexample, but a 65-scenario sweep was not
  run.
- **Hill and depth-JS are noisy/degenerate estimators**, so the *full-4* `admissible`
  rate (35/60) understates the semantic invariance. We report the robust core (KS ∧ ACF,
  58/60; Tier-B 59/60) alongside it and attribute every breach; we do NOT discard the
  noisy components silently. A reader who insists on all four sees 35/60 and the
  attribution and can weigh it.
- **Re-seed = independent alternate stream, not a per-message ±ε nudge.** This is the
  correct operationalization of "a different valid latency draw," consistent with Half 1.
- **Comparator stack skew.** Sims on the pinned container stack (numpy 1.26.4/pandas
  1.5.3); gates on the host t2venv (numpy 2.x/pandas 2.x). The gates read parquet + compute
  set-coverage/Kendall-τ/KS/ACF/Hill/JS, which are version-stable; the exact faithfulness
  gate passing on all 13 confirms no cross-stack artifact.
- **s001 Tier-B "fail"** (KS 0.08052 vs 0.08000) is at the ceiling on a 604-row micro; it
  is reported as a fail because the gate says so, not smoothed.

---

## What this means for the Track 3 submission (does NOT replace Phase 2)

- The exact gate (Tier-A) is **ill-posed for the stated goal**: it rejects the oracle's
  own valid re-draws (60/60) that its realism gate admits (59/60). A "faster simulator
  that behaves like a real exchange" is graded, under Tier-A, on implementation identity
  of an RNG-projected coordinate — not on behaving like a real exchange.
- This **does not make a faster submission win Tier-A** — Half 1 already proved Tier-A
  requires reproducing the numpy latency + agent streams bit-for-bit. The two halves
  together say: Tier-A is simultaneously (Half 1) irreducible for this mechanism and
  (Half 2) ill-posed for the goal. The reducible/safe scopes are unchanged: Tier-B
  families (statistical gate) and deterministic-latency scenarios (no draw to reproduce).
- The deliverable is the theorem, not a speed number. The theorem stands.

## Artifacts (scratch cleaned; env left in place)

Under `.bigtmp/track3_drawmap/` (outside the scored checkout, which is untouched):
- `harness.py` — Half-1 in-container margin monkeypatch + surgical stream reseed (reused
  unchanged; only `baseline` + `lat_reseed` modes used here).
- `score_w.py` — Half-2 orchestrator: re-seed → score every trace through BOTH gates on
  the same bytes against the scenario's own reference cache.
- `agg_w.py`, `agg_w2.py` — host-side aggregation (per-scenario/per-family distributions,
  per-stat pass rates, breach attribution).
- `out_w/wellposed_results.json` — the full per-scenario, per-reseed record behind every
  number above (Tier-A/Tier-B/realism outcomes + the four stylized-fact values).
