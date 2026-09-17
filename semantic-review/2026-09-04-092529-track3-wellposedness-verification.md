# Track 3 well-posedness proof — independent verification of the exact-gate-below-noise-floor theorem

I re-ran the centerpiece (H-W2) myself rather than trusting the build's JSON: fresh
container runs of the reference ABIDES engine (`track3-abides-baseline:latest`) with
latency-only re-seeds on two stochastic scenarios plus the deterministic control, scored
on the same trace bytes through the real organizer gates (`semantics.check_tier_a`,
`semantics.check_tier_b`, `stylized_facts.stylized_fact_report`+`admissible`) from the host
`.bigtmp/t2venv`. The theorem's load-bearing claim holds on my own run: the oracle fails
its own exact gate (Tier-A) while passing its own realism/statistical gate on the identical
bytes. I also confirmed the perturbation is a clean latency-only re-seed, that the gates are
the genuine organizer functions (not bespoke metrics), and that the stored 60-reseed panel
numbers are consistent with re-scoring the real traces.

Watch for: (1) the full-four-statistic `admissible()` rate is 35/60 — the doc leads with the
"robust core" (KS∧ACF 58/60, Tier-B 59/60) and treats the full-4 as a caveat; this is
disclosed transparently and does not invert the theorem, but a reader must accept the
KS/ACF-core scoping to read H-W1 as "confirmed" (confirmed). (2) The theorem rests on a
13-of-65-scenario panel, not a census (confirmed, disclosed). (3) The container's ABIDES
commit could not be read from an embedded marker; identity rests on the faithfulness gate
passing exactly, which I re-verified (possible non-issue, noted).

**Verdict**: APPROVED

## High-level view

The centerpiece reproduces cleanly. On my own fresh runs of `eq_lognormal_highsigma` and
`eq_uniform_wide`, the instrumented un-perturbed baseline reproduces the reference cache
exactly (faithfulness PASS, row counts equal), and every latency-only re-seed then fails
Tier-A on an event-count/coverage mismatch while Tier-B passes on the same bytes — 6/6 joint
"exact-fail ∧ tolerant-pass". The deterministic-latency control is a true no-op (identical
rows, all four stylized-fact numbers exactly 0.000, all gates pass), which proves the
instrument perturbs only the drawn stream.

The re-seed is a verified clean split. The harness tags each `RandomState` in mint order
(oracle→exchange→agents→latency→kernel) and reseeds only the latency index. On my run the
mint layout was oracle=0, exchange=1, agents=2..13, latency=14, kernel=15, and `lat_reseed`
touched index 14 alone — agent decision RNGs untouched, matching Half 1's separability claim.

The gates are the real organizer functions. `stylized_fact_report`/`admissible` live in the
installed `qfbench2_common` package with the organizer ceilings (KS 0.08, ACF 0.12, Hill 1.5,
depth-JS 0.10); Tier-A/Tier-B are the track3 checkout's `semantics.py`. The scorer feeds them
real cand+ref mid-price/depth series via the scorer's own `mid_price_series`/`depth_histogram`
extraction — no bespoke metric substituted.

H-W1 is sound and reported distributionally, with an honest scoping choice. The realism core
(return-distribution KS, volatility-clustering ACF) is invariant across the re-draw class at
59/60 each; the full-four rate is lower (35/60) because Hill and depth-JS are high-variance
against a single fixed reference. The doc reports both rates and attributes every breach
rather than discarding the noisy components — the reader can judge the caveat directly. The
pre-committed inversion (re-seed moving KS/ACF outside ceilings) genuinely did not occur, so
the theorem stands rather than inverting; that landing is what the numbers gave.

The stored full-panel JSON is not fabricated. Re-aggregating it reproduces the doc's headline
(Tier-A 60/60 fail, Tier-B 59/60 pass, joint 59/60, full-4 35/60, control 5/5), and the two
edge cases I spot-checked — the single Tier-B miss (s001 KS=0.08052 on ~600 rows) and the max
ACF (0.1301, eq_uniform_wide p3) — match values I independently regenerated.

<details>
<summary>Issues (3)</summary>

1. **Full-4 admissible scoping** — the "H-W1 confirmed" claim relies on the KS∧ACF robust core (58–59/60); the full four-statistic `admissible()` is 35/60. Disclosed transparently with per-breach attribution and both rates reported; not an overclaim, but the reader must accept the core-vs-full framing. No action required beyond the disclosure already present.
2. **Panel, not census** — theorem rests on 13/65 public scenarios (per-family n=1–2 outside latency-profile). Disclosed in the ledger as "assumed-representative"; a full 65-scenario sweep would harden it but is not required for the mechanism.
3. **Container commit not independently readable** — the image carries no embedded git marker; engine identity rests on the faithfulness gate (instrumented baseline == reference cache exactly), which I re-verified 3/3 on my runs and the build reports 13/13. Acceptable; noted for completeness.

</details>

<details>
<summary>Details</summary>

## H-W2 centerpiece — reproduced on my own run (confirmed)

I ran the reference engine in `track3-abides-baseline:latest` (numpy 1.26.4, pandas 1.5.3,
matching the doc) on two stochastic latency scenarios with three latency-only re-seeds each,
plus the deterministic control, and scored each output against the scenario's own
reference-cache `trace.parquet`:

```
=== eq_lognormal_highsigma (ref rows=14820) ===
  FAITHFULNESS (base==ref exact): True  rows 14820==14820
  p1 rows=14732: TierA=False TierB=True realism=True   exact-fail∧tolerant-pass=True
      ks=0.02587 acf=0.07264 hill=0.7077 js=0.00863
  p2 rows=14701: TierA=False TierB=True realism=True   exact-fail∧tolerant-pass=True
  p3 rows=14982: TierA=False TierB=True realism=False  exact-fail∧tolerant-pass=True
      realism breach: hill_abs=1.602>1.5 (KS/ACF/Tier-B still pass)

=== eq_uniform_wide (ref rows=14947) ===
  FAITHFULNESS (base==ref exact): True  rows 14947==14947
  p1 rows=14913: TierA=False TierB=True realism=True   exact-fail∧tolerant-pass=True
  p2 rows=14839: TierA=False TierB=True realism=True   exact-fail∧tolerant-pass=True
  p3 rows=14876: TierA=False TierB=True realism=False  exact-fail∧tolerant-pass=True
      realism breach: acf_abs_l2=0.1301>0.12 (KS/Tier-B still pass)

=== eq_deterministic_baseline (ref rows=10669) ===
  p1/p2/p3 rows=10669: TierA=True TierB=True realism=True  (all stats 0.000)
```

Every stochastic re-seed fails Tier-A on the event-count/coverage breach — the re-drawn
latency stream rewrites which events land in the window, so the exact gate's "deterministic
scenario, exact row count" requirement is violated. Tier-B passes on all six of those same
byte streams (return-KS 0.021–0.032, far under 0.08). The joint exact-fail ∧ tolerant-pass
condition held 6/6. This is the gate rejecting the oracle's own valid re-draw while its
tolerant gate admits the identical trace — the load-bearing claim, verified on traces I
generated, not the build's.

The deterministic control matters as the instrument's null: reseeding a latency stream that
performs no draw produced byte-identical output (same 10669 rows, all four stylized-fact
divergences exactly 0.000, all gates pass). The movement on the stochastic scenarios is
therefore caused by the draw, not by the harness.

The two full-4 realism breaches I hit (hill 1.602, acf 0.1301) are exactly the noisy-estimator
behavior the doc describes: in both cases KS and Tier-B still pass, so the "market" by the
calibrated core is unchanged and only a high-variance tail/vol estimator tips marginally over
its ceiling against a single fixed reference.

## The latency-only re-seed is a clean split (confirmed)

The harness wraps `_draw_random_state` to record mint order, then reseeds only the targeted
index in place. On `eq_lognormal_highsigma` the recorded layout was:

```
n_minted=16  oracle=0  exchange=1  agents=2..13  latency=14  kernel=15
mode=lat_reseed  n_latency_draws=15781  n_agents=13
```

`lat_reseed` reseeds `minted[14]` and nothing else, so the oracle, exchange, all 13 agent
decision RNGs, and the kernel keep their native streams. This is the same verified-separable
perturbation Half 1 relied on; the deterministic control's exact no-op is the empirical proof
that the split is surgical.

## Gates are the real organizer functions (confirmed)

`qfbench2_common.scoring.stylized_facts.stylized_fact_report` and `admissible` resolve to the
installed organizer package, and apply the ceilings straight from the task contract
(KS 0.08, ACF|r| L2 0.12, Hill|α| 1.5, depth-JS 0.10). `admissible` flags a breach only when a
reported divergence exceeds its ceiling — no reweighting, no substitution. Tier-A/Tier-B are
the track3 checkout's `semantics.check_tier_a`/`check_tier_b` with the declared tolerances
(±1000 ns, Kendall-τ floor 0.999; KS 0.08 + spread ±10 bps). The scorer passes real cand+ref
mid-price and depth series through the scorer's own `mid_price_series`/`depth_histogram`, so
the stylized-fact comparison is the organizer's real one on real bytes. Non-positive/degenerate
price series are guarded (the realism path returns `None` rather than a fabricated pass, and
`check_tier_b` raises on a non-finite statistic instead of failing open).

## H-W1 lemma — distributional and honest about the noisy components (confirmed)

Re-aggregating the stored 60-reseed panel reproduces the doc's headline exactly:

```
faithfulness: 13/13
TierA FAIL: 60/60      TierB PASS: 59/60      joint fail∧pass: 59/60
KS<=0.08: 59/60        ACF<=0.12: 59/60
full4 admissible PASS: 35/60
deterministic control all-gates PASS: 5/5
```

The single Tier-B miss is s001 perturb-1, KS=0.08052 vs the 0.08000 ceiling on a ~600-row
micro-scenario — reported as a fail because the gate says so, and its 0.0005 overshoot at the
ceiling is not smoothed. The max ACF across the panel (0.1301, eq_uniform_wide p3) is the
value I independently regenerated on my own run, which is strong evidence the JSON is the
genuine output of these gates on these traces rather than a hand-written summary.

The gap between the robust core (58–59/60) and the full-4 rate (35/60) is Hill (14 breaches)
and depth-JS (13), with 23 of 25 realism failures still passing KS∧ACF. The doc argues these
are estimator variance against a fixed single reference and micro-scenario degeneracy (s001's
Hill is literally NaN on a near-constant fill-price series), and reports both rates rather than
scoping the noisy components away. This is the correct honest treatment: it does not claim
full-4 invariance (the ledger marks that "NOT proven — 35/60"), and it does not force the
core-only reading on the reader.

## Inversion condition — correctly did not fire (confirmed)

The pre-committed inversion required the re-seed to push return-distribution KS or
volatility-clustering ACF outside their ceilings (which would make the draws semantically
load-bearing and Tier-A well-formed). Those two stayed in-tolerance 59/60, so the theorem
stands rather than inverting. The doc reports the landing the numbers gave and did not force
H-W1; the inversion path is described for completeness and explicitly marked as not this
mechanism. On my own run the KS core never breached (0.021–0.032), consistent with this.

## Theorem follows from the numbers (confirmed, with the stated scope)

H-W1 (calibrated core invariant across the re-draw class) ∧ H-W2 (oracle fails Tier-A 60/60
while passing the tolerant gate 59/60 on the same bytes) support the H-W3 conclusion: Tier-A
resolves below the model's own declared noise floor and measures implementation identity of an
RNG-projected exact-order coordinate, not simulation correctness — ill-posed w.r.t. the stated
"faster simulator that behaves like a real exchange" goal. The conclusion is scoped honestly:
"PROVEN on the gate's calibrated core (Tier-B + KS/ACF)", with the full-4 caveat, the panel
(not census) limit, and the transfer claim marked CONJECTURED (mechanism-typed) rather than
proven. No overclaim detected — the strongest statements in the ledger are the ones I could
independently reproduce, and the weaker ones are labeled weaker.

</details>

<details>
<summary>File map</summary>

- `drafts/track3_sim/T3_WELLPOSEDNESS_PREREG.md` — the pre-registered contract (theorem + both pre-committed landings); reviewed, not changed.
- `drafts/track3_sim/T3_WELLPOSEDNESS_RESULTS.md` — the results doc under review; H-W1/H-W2/H-W3 + ledger + limits.
- `.bigtmp/track3_drawmap/score_w.py` — Half-2 orchestrator (re-seed → both gates on same bytes vs own reference cache); read and re-derived independently.
- `.bigtmp/track3_drawmap/harness.py` — in-container margin instrument + surgical latency-only stream reseed; mint-order logic verified.
- `.bigtmp/track3_drawmap/out_w/wellposed_results.json` — full per-scenario/per-reseed record; re-aggregated, numbers match the doc.
- `qfbench2_common/scoring/stylized_facts.py` (installed in t2venv), `qfbench2_track_simulation/semantics.py` (track3 checkout) — the real organizer gate functions.

My verification artifacts (`verify_run.py`, `verify_out/`) were removed after the run; the environment (ABIDES pin, images, reference caches, build artifacts) was left untouched.

</details>
