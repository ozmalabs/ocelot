# Tier-A exactness resolves below the model's own latency noise floor — the reference engine fails its own exact gate while passing its own realism gate on the same trace

## Good-faith framing

This is a benchmark-feedback issue, filed under the rules that explicitly protect
good-faith reports about the benchmark itself. It is **not** a submission, a score
dispute, or a claim that anything is broken in the code. It is a reproducible
observation about one gate's *well-posedness* with respect to the stated Track 3 goal —
"a faster simulator that still behaves like a real exchange" — together with a suggested
fix. Everything below runs against your own public repo, your own image, your own
reference cache, and your own gate functions. Please read it as "here is something we
measured, here is how to reproduce it, and here is one way it could be tightened," not as
a complaint. Happy to be told we've mismodelled something.

## The observation, stated plainly

Take the reference ABIDES baseline (`track3-abides-baseline:latest`, pinned
`f9cbe51`). Re-run it having re-drawn **only its latency stream** — a stream the scenario
itself declares to be random (`latency_config: {model: uniform | log_normal | pareto,
...}`) — while holding the agent decision RNG fixed. Score that trace against the
scenario's **own** reference-cache trace, through **both** of your own gates, on the
**same bytes**:

- **Tier-A (`semantics.check_tier_a`, exact)** rejects the re-drawn oracle on **60 / 60**
  stochastic re-seeds.
- **Tier-B (`semantics.check_tier_b`, tolerant)** admits **59 / 60** of those same traces.
- The **return-realism core** of the stylized-fact gate — return-distribution KS and
  volatility-clustering ACF, the two robust Cont facts — is invariant across the re-draw
  class: **58 / 60**.

So the canonical correct simulator, re-drawing a stream the scenario *declares* to be
random, is rejected by the exact gate on 100% of stochastic scenarios while being
admitted by its own calibrated tolerant gates on ~98% of the identical traces. On
**59 / 60** re-seeds, Tier-A fails **and** Tier-B (or the KS∧ACF core) passes on the very
same trace.

A latency model that draws nothing — the `eq_deterministic_baseline` control — is a true
no-op under the re-seed: **all 5 / 5** re-seeds pass every gate, all four stylized-fact
numbers exactly `0.000`. That control is the instrument's null and shows the re-seed is
surgical: reseeding a stream that isn't drawn changes nothing.

The reading we draw: **Tier-A is resolving finer than the noise floor of the model's own
declared stochastic-latency physics.** Your README itself concedes the tolerant ceiling
"comes from the natural run-to-run variation of correct simulations." A valid alternate
latency draw is exactly such a variation — the tolerant gate is calibrated to admit it as
one market, and does — yet Tier-A demands agreement on the exact-order coordinate that a
different-but-valid latency draw necessarily changes. On the stated goal, that measures
implementation identity, not simulation correctness.

## What causes it (one paragraph, mechanism)

The kernel event calendar is keyed on `(deliver_at, (sender_id, recipient_id, message))`,
and `deliver_at = sent_time + int(latency)` where `latency` is a per-message
`RandomState` draw. On a busy calendar the gap between neighbouring `deliver_at` values is
typically much smaller than the latency draw's own jitter, so a different valid latency
draw reorders near-ties at the book. Because the matching engine is order-sensitive
(who-crosses-whom depends on arrival order, and fills feed back into agent state), that
reorder rewrites the **event set** — not just timestamps. So a latency re-draw moves the
exact-order coordinate that Tier-A gates (event coverage + fill sequence + Kendall-τ),
while leaving the market statistics the tolerant gate reads (return KS, volatility-
clustering ACF, mean spread) inside their calibrated tolerances. The exact-order
coordinate carries the RNG entropy; the semantic coordinate does not.

## Exact reproduction

Everything is public. From a clean checkout of
`Agenthon-2026/track3-simulation-public`:

```bash
# 1. Build the reference baseline image (pinned ABIDES f9cbe51 + the abides_fork adapter)
docker build --platform=linux/amd64 -t track3-abides-baseline:latest baselines/

# 2. Build the local reference-trace cache the gate scores against
#    (git lfs pull first if the unit parquet files are still LFS pointers)
python regression_suite/build_reference_cache.py

# 3. In the Python 3.13 scoring environment that has this repo's
#    qfbench2_track_simulation + qfbench2_common installed, run the reproduction:
python reproduce.py                    # 13-scenario panel, 3 latency reseeds each
#   or, to reproduce the exact headline counts below (5 reseeds -> 60 stochastic runs):
python reproduce.py --reseeds 5 --json-out wellposed.json
```

`reproduce.py` (attached) imports **only** public code — `qfbench2_track_simulation.semantics`,
`qfbench2_common.scoring.stylized_facts`, and (inside the baseline image only) the public
`abides_fork` adapter. The latency-only re-seed is a ~20-line monkeypatch of
`abides_fork.config._draw_random_state`, written to a temp file and bind-mounted read-only
into your image, so the image and the checkout are both untouched. For each scenario it
(a) runs the baseline at its native seed, (b) confirms the faithfulness gate (the
instrumented baseline reproduces the reference-cache trace exactly), (c) re-seeds the
latency `RandomState` only, and (d) scores every re-seeded trace through Tier-A,
Tier-B, and `stylized_fact_report` / `admissible` on the same bytes, printing the table
below.

## Headline numbers

From `python reproduce.py --reseeds 5` (13 scenarios × 5 latency re-seeds; 60 stochastic +
5 deterministic-control runs). The faithfulness gate passes on all 13 scenarios, so every
movement is caused by the latency re-seed, not by instrumentation.

| scenario | latency | Tier-A (exact) | Tier-B (tolerant) | realism KS∧ACF | realism full-4 | KS med | ACF med |
|---|---|---:|---:|---:|---:|---:|---:|
| s001_price_time_priority | uniform | 0/5 | 4/5 | 4/5 | 0/5 | 0.070 | 0.099 |
| s012_partial_fill_cancel_race | log_normal | 0/5 | 5/5 | 5/5 | 0/5 | 0.012 | 0.006 |
| **eq_deterministic_baseline** (control) | deterministic | **5/5** | **5/5** | **5/5** | **5/5** | 0.000 | 0.000 |
| eq_uniform_tight | uniform | 0/5 | 5/5 | 5/5 | 4/5 | 0.031 | 0.075 |
| eq_uniform_wide | uniform | 0/5 | 5/5 | 4/5 | 4/5 | 0.022 | 0.099 |
| eq_lognormal_lowsigma | log_normal | 0/5 | 5/5 | 5/5 | 5/5 | 0.019 | 0.049 |
| eq_lognormal_highsigma | log_normal | 0/5 | 5/5 | 5/5 | 4/5 | 0.026 | 0.046 |
| eq_pareto_heavytail | pareto | 0/5 | 5/5 | 5/5 | 2/5 | 0.025 | 0.056 |
| as01_base_mix | log_normal | 0/5 | 5/5 | 5/5 | 5/5 | 0.017 | 0.021 |
| as06_throughput_fast | log_normal | 0/5 | 5/5 | 5/5 | 4/5 | 0.009 | 0.021 |
| sf_01_baseline_regime | log_normal | 0/5 | 5/5 | 5/5 | 2/5 | 0.026 | 0.013 |
| gb_base_30agent_30s | log_normal | 0/5 | 5/5 | 5/5 | 3/5 | 0.036 | 0.024 |
| ca_baseline_calm | log_normal | 0/5 | 5/5 | 5/5 | 2/5 | 0.041 | 0.022 |

**Aggregate, stochastic scenarios only (the deterministic control is separated out):**

| quantity | count |
|---|---|
| Tier-A (exact) **fail** | **60 / 60** |
| Tier-B (tolerant) pass on the same traces | **59 / 60** |
| return-realism core (KS ≤ 0.08 ∧ ACF ≤ 0.12) pass | **58 / 60** |
| Tier-A FAIL **and** (Tier-B ∨ KS∧ACF) PASS on the **same** trace | **59 / 60** |
| deterministic-latency control (no draw): all gates pass | **5 / 5** |

Per-statistic, across the 60 stochastic re-seeds: KS **59/60** (median 0.025), ACF
**59/60** (median 0.030). The single Tier-B miss is `s001` perturb-1 at KS = **0.08052**
vs the 0.08000 ceiling — a 0.0005 overshoot on a 604-row micro-scenario, reported as a
fail because the gate says so, not because the market moved.

## Honest caveat (reported transparently, not scoped away)

The **full four-statistic** `admissible()` check passes only **35 / 60**, and we report
that number in the table above rather than hiding it. The gap is confined to the two
high-variance components, not to the market:

- Per-statistic finite pass rates over the 60 stochastic re-seeds: **KS 59/60, ACF
  59/60**, but **Hill tail-index 41/55 finite, depth-JS 47/60**.
- **23 of the 25** full-4 realism failures still pass **both** KS and ACF — i.e. the
  failure is Hill and/or depth-JS only, never the return distribution or volatility
  clustering.
- The reference is fixed, so the Hill scatter against it is the estimator's own run-to-run
  noise: e.g. `eq_pareto_heavytail` |α_cand − α_ref| ranges 0.71 / 1.95 / 2.05 (min/med/max
  over 5 re-seeds), `ca_baseline_calm` 0.78 / 1.67 / 4.94 — a 1.5 ceiling sits inside the
  finite-sample Hill spread a second *correct* reference run would show.
- depth-JS breaches concentrate in the degenerate matching-engine micro-scenarios (`s001`
  is 604 rows and its fill-price series is near-constant, so Hill is literally NaN);
  outside those, depth-JS medians are ≈ 0.001–0.011, far under the 0.10 ceiling.

So we make the narrower, defensible claim: the theorem holds on the gate's **calibrated
semantic core** (Tier-B 59/60; KS∧ACF 58/60), and we hand you the full-4 number (35/60)
plus the attribution so you can weigh the caveat directly. We do **not** claim full-4
invariance — it isn't there, because two of its four estimators are noisy against a single
fixed reference.

## Suggested well-posed fix

The tolerant gates already constrain the semantic invariants a "behaves-like-real" goal
cares about (return distribution, volatility clustering, mean spread). The exact gate adds
a constraint on the RNG-projected exact-order coordinate that the model's *declared*
stochastic-latency physics leaves free. A well-posed gate would:

1. **Gate exactness only where the model is deterministic.** The `eq_deterministic_baseline`
   control shows Tier-A is exactly right when there is no latency draw to reproduce — there,
   the exact-order coordinate *is* determined by the seed. For scenarios whose
   `latency_config.model` is stochastic (`uniform` / `log_normal` / `pareto`), the exact
   fill-sequence / Kendall-τ requirement is finer than the model's own noise floor.
2. **Tolerate the RNG-projected exact-order coordinate** for those scenarios, and instead
   constrain the semantic invariants the tolerant gates already check (which, per this
   report, are invariant across the valid re-draw class). Matching-engine families that are
   genuinely exact-by-design (deterministic tie-break, no latency draw) keep Tier-A.

Concretely: the family → tier mapping (`TIER_A_FAMILIES`) could be made conditional on
whether the scenario declares a stochastic latency model, rather than assigning Tier-A by
family alone. That keeps the exact gate where it is well-formed and lets the tolerant gate
arbitrate where the physics is stochastic.

We are not attached to this particular fix — the point is the diagnostic (exact fails +
tolerant passes on the same bytes ⇒ the exact gate is below the model's noise floor), and
we'd defer to whatever the organizers judge cleanest.

## Honest limits

- **Panel, not census.** 13 of the 65 public scenarios, chosen to span every family and the
  full latency axis (deterministic → uniform tight/wide → lognormal low/high-σ → pareto).
  Per-family n is small (1–2 outside latency-profile). The split is uniform with no
  counterexample to the core within the panel, but we did not run a full 65-scenario sweep.
  `reproduce.py --scenarios ...` extends to any subset if you want the census.
- **Re-seed = independent alternate latency stream**, not a per-message ±ε nudge. This is
  our operationalization of "a different valid latency draw"; a per-message infinitesimal-
  perturbation sensitivity is a finer measurement we did not run.
- **Transfer is conjectured, not proven.** The mechanism (order-pivotal near-injective
  draw→order map + order-sensitive dynamics) should recur in other declared-stochastic
  discrete-event sims graded by an exact comparator, but we verified it only on this
  ABIDES-class baseline here.
- **Stack note.** Sims run on the pinned baseline image (numpy 1.26.4 / pandas 1.5.3); the
  gates run on the 3.13 scoring stack. The gate functions only read parquet and compute
  set-coverage / Kendall-τ / KS / ACF / Hill / JS, which are version-stable, and the exact
  faithfulness gate passing on all 13 scenarios confirms no cross-stack artifact.

## Attachment

`reproduce.py` — the self-contained reproduction described above. It depends only on
`track3-abides-baseline:latest`, the reference cache, the shipped scenarios, and the public
`qfbench2_track_simulation` / `qfbench2_common` gate functions.
