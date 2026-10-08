# RESULTS — the draw→order map: how much of ABIDES's RNG entanglement is OBSERVABLE through Tier-A?

**Measured against `T3_DRAW_ORDER_PREREG.md` (the contract). Nothing above that
file's MEASUREMENT GATE was edited once numbers existed.** This is the real Track 3
investigation: the output is INFORMATION about the shape of the draw→trace map, not a
speed number.

## HEADLINE (pre-committed interpretation — it landed NULL / dense)

**H-D1 is NULL. The entanglement is dense, and Tier-A exactness is irreducible for the
ABIDES latency mechanism.** Across every public scenario with a stochastic latency
model, **81–97% of latency draws are order-pivotal** (their delivery-time margin to the
nearest live queue neighbor is smaller than the draw's own typical jitter), and a
**latency-only re-draw — agent decision RNG held fixed — fails the REAL Tier-A comparator
on 100% of stochastic scenarios (0 / 36 stochastic latency-only re-draws pass, out of
39 total; the only 3 passes are the deterministic-latency control, where reseeding draws
nothing).** The latency draw is not
a benign timestamp jitter absorbed by the ±1 µs tolerance: reordering near-ties changes
which orders match which at the book, which rewrites the fill/quote stream, which wakes
agents differently — so a latency re-draw changes the observable **event SET**, not just
its order.

This JUSTIFIES the audit's "AVOID owning the loop" **with evidence** instead of
inheriting it as an assumption. The norm's phrasing ("reproduce MT19937 bit-for-bit")
is *operationally* correct here, but the *reason* is now measured and stated precisely:
it is not that the draws matter as numbers — it is that the draw→order projection is
**not a heavy projection**. It is near-injective on the observable trace for this
mechanism. The transferable shape (below) is a real result about ABIDES-class
discrete-event sims under a tolerance comparator, not a benchmark artifact.

The one place the reducible hypothesis survives — a genuinely deterministic latency model
(`eq_deterministic_baseline`) — is exactly the degenerate case where there are no latency
draws to reproduce, so it is not a counterexample to the NULL; it is the control that
proves the instrument.

---

## Provenance / discipline

- ABIDES pinned commit `f9cbe51342b7dedd9587e4e069040d68a5c6477f`; scored container
  `track3-abides-baseline:latest` (py3.11, numpy 1.26.4, pandas 1.5.3, scipy 1.17.1 —
  the pinned stack the reference cache was generated on). Comparator run on the host
  (`.bigtmp/t2venv`) against the **REAL** gate
  `qfbench2_track_simulation.semantics.check_tier_a` (never a bespoke metric).
- **Perturb via SEED, never by editing the engine's math.** The scored checkout is
  UNTOUCHED. Instrumentation is a runtime monkeypatch of
  `abides_core.kernel.Kernel.send_message` (margin logging) plus an in-place `.seed()` of
  the targeted `RandomState` object(s) applied *after* `build_config` (stream split).
- **Faithfulness gate passed for all 13 panel scenarios:** the instrumented, un-perturbed
  baseline reproduces the reference-cache `trace.parquet` **exactly** (`check_tier_a`
  PASS, row counts equal). The monkeypatch perturbs nothing; every reported movement is
  caused by the seed split, not by the instrument.
- PREREG-then-measure; whole distributions reported, not cherry-picked scalars; the NULL
  is the finding. No fabricated numbers.

### The mechanism, re-confirmed from the container's actual code
`send_message` computes `deliver_at = sent_time + int(latency)` (kernel.py:619), where
`latency = agent_latency_model.get_latency(...)` is a per-message `RandomState` draw
(`ScenarioLatencyModel.get_latency`, `abides_fork/config.py`: `lognormal` / `uniform` /
`pareto`, clipped to `[min_ns, max_ns]`). The event calendar is a `queue.PriorityQueue`
(kernel.py:68) ordered on `(deliver_at, (sender_id, recipient_id, message))`; the pop at
kernel.py:306 is the event order. The tiebreak on equal `deliver_at` is
`(sender_id, recipient_id, …)` — **deterministic, draw-independent** — so a draw changes
observable order ONLY when it moves `deliver_at` across a neighboring **distinct**
`deliver_at`. Wakeups are scheduled via `set_wakeup(requested_time)` (kernel.py:719), which
draws nothing; confirmed empirically (0 wakeup messages routed through `send_message`).

---

## H-D2 stream-separability finding (measured FIRST, as the PREREG requires)

**The latency `RandomState` and the agents' decision `RandomState`s are SEPARATE objects,
but all are minted from one master seed.** `build_config` calls `np.random.seed(seed)`
once, then `_draw_random_state()` mints each component's own
`np.random.RandomState(seed=np.random.randint(...))` in a **fixed order**:
`oracle → exchange(id 0) → agents(id 1..N) → latency_model → kernel`
(verified live via the mint layout, e.g. s001: `n_minted=8`, latency at index 6, kernel 7).

Consequence for the experiment: because they are distinct objects, the latency stream **can**
be perturbed independently of the agent streams by re-`seed()`-ing only `minted[latency_idx]`
after build — which is exactly what the `lat_reseed` mode does. **The split is therefore
NOT bounded by a shared RandomState** (the PREREG's worst case did not occur). The bound
that *does* exist is downstream and is itself the finding: perturbing the latency stream
alone still changes the event SET, because the SET is not causally upstream of latency —
it is co-determined with it through the matching engine (below).

**Control that proves the split is surgical:** `eq_deterministic_baseline` uses a constant
latency model that performs no draw. There, `lat_reseed` is a **true no-op** —
`check_tier_a` PASS, Kendall-τ = 1.000, row counts equal — while `agent_reseed` still
fails (τ ≈ 0.64). Reseeding a stream that isn't drawn changes nothing; reseeding one that
is drawn changes everything. The instrument is clean.

---

## H-D1a — ANALYTIC MARGIN (per family, whole distributions)

For each message enqueued with delivery time `d`, the **margin** is
`min |d − d'|` over all OTHER distinct `deliver_at` values `d'` live in the
PriorityQueue at enqueue time (faithful to the PREREG definition, computed by wrapping
`self.messages.put` so the logged key is the real one). The **order-pivotal fraction** is
the fraction of latency-drawn messages whose margin is below the draw's own typical
jitter (the latency distribution's IQR).

### Baseline margin & pivotal fraction (n = messages sent = latency draws)

| scenario | family | lat model | nMsg | median margin (ns) | latency IQR (ns) | **pivotal (margin<IQR)** | pivotal (margin<median) | margin<1µs tol |
|---|---|---|---:|---:|---:|---:|---:|---:|
| s001_price_time_priority | matching-engine | uniform | 580 | 149 | 896 | **0.910** | 0.943 | 0.933 |
| s012_partial_fill_cancel_race | matching-engine | log_normal | 172,688 | 54 | 325 | **0.853** | 0.909 | 0.913 |
| eq_deterministic_baseline | latency-profile | *deterministic* | 15,750 | 250,000 | 0 | **0.000** | 0.093 | 0.038 |
| eq_uniform_tight | latency-profile | uniform | 15,808 | 95 | 962 | **0.972** | 0.977 | 0.974 |
| eq_uniform_wide | latency-profile | uniform | 15,792 | 91,629 | 1,010,629 | **0.974** | 0.974 | 0.009 |
| eq_lognormal_lowsigma | latency-profile | log_normal | 15,765 | 401 | 2,366 | **0.896** | 0.971 | 0.740 |
| eq_lognormal_highsigma | latency-profile | log_normal | 15,821 | 2,293 | 17,986 | **0.815** | 0.646 | 0.339 |
| eq_pareto_heavytail | latency-profile | pareto | 15,841 | 111 | 669 | **0.847** | 0.868 | 0.890 |
| as01_base_mix | agent-mix | log_normal | 25,865 | 22 | 205 | **0.937** | 0.989 | 0.999 |
| as06_throughput_fast | agent-mix | log_normal | 72,515 | 21 | 204 | **0.936** | 0.988 | 0.999 |
| sf_01_baseline_regime | stylized-facts | log_normal | 61,123 | 481 | 5,633 | **0.876** | 0.868 | 0.665 |
| gb_base_30agent_30s | throughput-scale | log_normal | 73,193 | 21 | 343 | **0.960** | 0.977 | 0.995 |
| ca_baseline_calm | stylized-facts | log_normal | 36,183 | 217 | 5,295 | **0.964** | 0.961 | 0.825 |

### Margin distribution quantiles (ns) — the whole shape, per scenario

| scenario | p1 | p5 | p25 | p50 | p75 | p95 | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| s001 | 2 | 7 | 54 | 149 | 413 | 1,089 | 1,708 |
| s012 | 1 | 4 | 20 | 54 | 156 | 998,110 | 999,243 |
| eq_deterministic | 60 | 249,860 | 250,000 | 250,000 | 250,050 | 65,666,566 | 66,416,616 |
| eq_uniform_tight | 2 | 7 | 36 | 95 | 238 | 758 | 1,545 |
| eq_uniform_wide | 1,166 | 5,567 | 34,426 | 91,629 | 230,844 | 757,216 | 1,592,016 |
| eq_lognormal_lowsigma | 5 | 25 | 147 | 401 | 1,047 | 3,862 | 7,406 |
| eq_lognormal_highsigma | 17 | 89 | 603 | 2,293 | 10,109 | 182,813 | 65,993,232 |
| eq_pareto_heavytail | 2 | 6 | 38 | 111 | 349 | 3,018 | 66,639,424 |
| as01_base_mix | 1 | 2 | 8 | 22 | 58 | 236 | 505 |
| as06_throughput_fast | 1 | 2 | 8 | 21 | 57 | 241 | 526 |
| sf_01_baseline_regime | 6 | 27 | 165 | 481 | 1,613 | 1,980,894 | 1,995,693 |
| gb_base_30agent_30s | 1 | 2 | 8 | 21 | 54 | 288 | 749 |
| ca_baseline_calm | 3 | 12 | 75 | 217 | 631 | 3,907 | 13,665 |

**Reading of H-D1a.** The margin distribution is **dominated by tiny gaps**: outside the
deterministic control, median margins are 21–481 ns while the draws that set them have
IQRs of 200 ns–18 µs. The pivotal fraction is high everywhere (0.81–0.97), and — this is
the load-bearing point — it stays high *even for wide latency* (`eq_uniform_wide`:
median margin 92 µs, but IQR ~1 ms, so still 97% pivotal). **A wider draw does not buy
larger relative margins**, because the queue fills up proportionally to the spread: more
dispersion spreads the events out, but it spreads the neighbors out too, so the margin
relative to the jitter stays small. The `margin<1µs` column shows the tolerance escape
hatch only bites when the *absolute* gaps are sub-µs (as06/as01/gb: 0.99+), and evaporates
when the model is wide (`eq_uniform_wide` 0.009, `eq_lognormal_highsigma` 0.339) — so the
±1 µs tolerance cannot rescue reducibility across families. Zero-margin exact-ties are
absent (`m=0` ≈ 0.000 everywhere), so the deterministic tiebreak almost never gets to act;
nearly every ordering decision is a genuine, draw-set distinct-time comparison.

---

## H-D1b — EMPIRICAL PERTURBATION via the REAL Tier-A comparator (per family)

Each scenario re-run under three seed splits (`lat_reseed` = latency RNG only;
`agent_reseed` = agent decision RNGs only; `both_reseed`), at three perturbation seeds
(p1,p2,p3; medians shown). Where the scenario is non-disruptive-leaning the three seeds
agree tightly (`eq_uniform_wide` latency-only τ ∈ {0.135, 0.065, 0.167}, `as06`
τ ∈ {0.363, 0.385, 0.368}); for the more disruptive scenarios they can spread widely
(`ca_baseline_calm` latency-only τ ∈ {0.822, 0.004, −0.18}, ordered → anti-correlated —
the table reports the median, 0.004), but **all three perturb seeds fail Tier-A in every
stochastic scenario regardless of the spread**, so the NULL is robust to it. `tierA` = did
ANY perturbed run pass the real gate; `tau_med` = median Kendall-τ on the shared-key event
order;
`cov` = fraction of the reference event SET still present; `mv>1µs` = fraction of matched
events whose timestamp moved beyond the ±1 µs tolerance.

| scenario | mode | tierA | τ (med) | coverage | fill count = | fill-seq Δ | events mv>1µs | events mv at all |
|---|---|---|---:|---:|---|---:|---:|---:|
| s001 | lat_reseed | **False** | 0.577 | 0.194 | False | 0.919 | 0.709 | 1.000 |
| s001 | agent_reseed | False | 0.509 | 0.101 | False | 0.942 | 0.638 | 0.810 |
| s001 | both_reseed | False | 0.389 | 0.073 | False | 0.963 | 0.843 | 1.000 |
| s012 | lat_reseed | **False** | 0.936 | 0.276 | False | 0.954 | 0.767 | 1.000 |
| s012 | agent_reseed | False | 0.906 | 0.184 | False | 0.993 | 0.968 | 1.000 |
| eq_deterministic | **lat_reseed** | **True** | **1.000** | **1.000** | **True** | **0.000** | **0.000** | **0.000** |
| eq_deterministic | agent_reseed | False | 0.641 | 0.005 | False | 0.996 | 0.571 | 0.619 |
| eq_uniform_tight | lat_reseed | **False** | 0.242 | 0.067 | False | 0.993 | 0.980 | 1.000 |
| eq_uniform_tight | agent_reseed | False | 0.237 | 0.030 | False | 0.998 | 0.959 | 0.977 |
| eq_uniform_wide | lat_reseed | **False** | 0.135 | 0.068 | False | 0.988 | 1.000 | 1.000 |
| eq_uniform_wide | agent_reseed | False | 0.144 | 0.035 | False | 0.998 | 0.989 | 0.989 |
| eq_lognormal_lowsigma | lat_reseed | **False** | 0.147 | 0.093 | False | 0.982 | 0.992 | 1.000 |
| eq_lognormal_highsigma | lat_reseed | **False** | 0.478 | 0.076 | False | 0.988 | 0.998 | 1.000 |
| eq_pareto_heavytail | lat_reseed | **False** | 0.155 | 0.086 | False | 0.987 | 0.981 | 1.000 |
| as01_base_mix | lat_reseed | **False** | 0.096 | 0.099 | False | 0.985 | 0.972 | 1.000 |
| as01_base_mix | agent_reseed | False | 0.241 | 0.038 | False | 0.997 | 0.969 | 0.987 |
| as06_throughput_fast | lat_reseed | **False** | 0.368 | 0.230 | False | 0.992 | 0.986 | 1.000 |
| as06_throughput_fast | agent_reseed | False | 0.038 | 0.034 | False | 1.000 | 0.979 | 0.995 |
| sf_01_baseline_regime | lat_reseed | **False** | 0.358 | 0.146 | False | 0.976 | 0.998 | 1.000 |
| gb_base_30agent_30s | lat_reseed | **False** | 0.186 | 0.056 | False | 0.996 | 0.993 | 1.000 |
| gb_base_30agent_30s | agent_reseed | False | 0.061 | 0.022 | False | 1.000 | 0.994 | 0.996 |
| ca_baseline_calm | lat_reseed | **False** | 0.004 | 0.047 | False | 0.990 | 0.995 | 1.000 |
| ca_baseline_calm | agent_reseed | False | 0.524 | 0.089 | False | 0.996 | 0.993 | 0.997 |

*(both_reseed rows omitted for brevity; they track the more-disruptive of the two singles
and never pass — full data in `results.json`.)*

### Per-family aggregate

| family | n scenarios | median pivotal (margin<IQR) | latency-only Tier-A pass rate |
|---|---:|---:|---:|
| agent-mix | 2 | 0.937 | 0 / 6 |
| calibration-stylized-facts | 2 | 0.920 | 0 / 6 |
| latency-profile | 6 | 0.871 | 3 / 18 *(all 3 = the deterministic control)* |
| matching-engine-semantics | 2 | 0.882 | 0 / 6 |
| throughput-scale | 1 | 0.960 | 0 / 3 |

**Reading of H-D1b — this is the decisive evidence for NULL.**

1. **Latency-only re-draw fails Tier-A on every scenario that actually draws latency**
   (0 / 36 stochastic latency-only re-draws, out of 39 total; the 3 passes are the no-draw
   deterministic control). The
   fraction of Tier-A-relevant structure that is *invariant* to the latency draws is
   effectively zero on the gate's own terms.

2. **The failure is not a benign timestamp jitter.** If latency draws only jittered
   delivery times within tolerance, we would see fill *count* preserved, coverage ≈ 1.0,
   and only `mv>1µs` moving. Instead **coverage collapses to 0.05–0.28** — the event SET
   keys `(order_id, msg_type, agent_id, side, price, size)` themselves change. Direct
   inspection of `s001` under `lat_reseed` (agent seeds fixed) shows the signature of a
   reorder, not a jitter: the **fill *count* is preserved** (`fill_count_equal=True`,
   176 = 176 — the agents submitted and executed the same *number* of orders), yet the
   **first fill already differs in order_id and price (position 0) and size (position 1)**,
   and **coverage of the reference event SET is only 0.19** — i.e. the same orders were
   submitted but crossed in a different order. (The equal-submitted-orders direction is
   confirmed by the retained fill-count equality + coverage collapse; an earlier draft's
   specific "ORDER_SUBMITTED = 120" was a live-inspection observation and is not a retained
   figure in `results.json`, which stores fill counts + coverage, not per-msg-type submit
   counts.) The latency re-draw reordered which resting order
   a marketable order crossed; the fills changed; the executed-order messages woke agents
   in a different state; the trace diverged globally. **The event SET is co-determined with
   the latency order through the matching engine — it is not upstream of it.**

3. **`fill-seq Δ` ≈ 0.92–1.00 and `events moved at all` ≈ 1.0** everywhere stochastic:
   essentially every observable is touched by a single-stream re-draw.

---

## H-D2 — which stream moves the observables more?

Latency-only and agent-only perturbations are **both catastrophic and of comparable
magnitude** (median τ: latency-only 0.004–0.936, agent-only 0.038–0.906; coverage
collapses to single-digit % under either). There is **no regime in which the event SET is
agent-determined while latency merely jitters timestamps** — the hoped-for asymmetry in
the PREREG's H-D2 ("reproduce the agent SET, enjoy freedom on the latency jitter") **does
not hold** for this mechanism. Neither stream is the "cheap" one to skip.

- In some scenarios latency-only is *more* disruptive than agent-only (`ca_baseline_calm`:
  τ 0.004 vs 0.524; `s001`: 0.577 is higher-τ than agent 0.509 but both fail), in others
  agent-only is (`as06`: agent τ 0.038 vs latency 0.368; `gb_base`: 0.061 vs 0.186).
  Which dominates is scenario-specific and **both are individually sufficient to fail
  Tier-A.** The takeaway is symmetric: a fast engine must reproduce **both** streams'
  effects exactly, because each alone rewrites the SET.

The separability *of the RandomState objects* is real and clean (H-D2 setup verified); the
separability *of the observable consequences* is what fails — the two draw streams are
fused by the order-sensitive matching engine into a single high-dimensional trace.

---

## H-D3 — effective dimension / projection gap

**Method (coarse, honest, stated).** *Consumed* order-relevant entropy is bounded by the
empirical Shannon entropy of the realized latency at the kernel's 1 ns rounding
resolution, times the number of draws: `H_consumed = n_draws × H(latency@1ns)`.
*Observable* order entropy that can pass through Tier-A is bounded above by
`n_pivotal × 1 bit` — a pivotal draw contributes at most one bit ("did it cross its nearest
neighbor?"); a non-pivotal draw contributes ~0 (its order is fixed regardless of the
draw's value). The gap `H_consumed − H_observable_upper` is the projection strength.

| scenario | n draws | H/draw (bits) | H_consumed (bits) | n pivotal | pivotal frac | H_obs upper (bits) | gap (bits) | **obs/consumed** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| s001 | 580 | 8.92 | 5,171 | 528 | 0.910 | 528 | 4,643 | 0.102 |
| s012 | 172,688 | 9.94 | 1,716,659 | 147,378 | 0.853 | 147,378 | 1,569,281 | 0.086 |
| eq_deterministic | 15,750 | 0.00 | 0 | 0 | 0.000 | 0 | 0 | 0.000 |
| eq_uniform_tight | 15,808 | 10.81 | 170,822 | 15,360 | 0.972 | 15,360 | 155,462 | 0.090 |
| eq_uniform_wide | 15,792 | 13.94 | 220,136 | 15,377 | 0.974 | 15,377 | 204,759 | 0.070 |
| eq_lognormal_lowsigma | 15,765 | 12.33 | 194,396 | 14,121 | 0.896 | 14,121 | 180,275 | 0.073 |
| eq_lognormal_highsigma | 15,821 | 12.96 | 205,092 | 12,896 | 0.815 | 12,896 | 192,196 | 0.063 |
| eq_pareto_heavytail | 15,841 | 10.43 | 165,299 | 13,410 | 0.847 | 13,410 | 151,889 | 0.081 |
| as01_base_mix | 25,865 | 9.24 | 238,955 | 24,236 | 0.937 | 24,236 | 214,719 | 0.101 |
| as06_throughput_fast | 72,515 | 9.26 | 671,361 | 67,884 | 0.936 | 67,884 | 603,477 | 0.101 |
| sf_01_baseline_regime | 61,123 | 13.62 | 832,565 | 53,526 | 0.876 | 53,526 | 779,039 | 0.064 |
| gb_base_30agent_30s | 73,193 | 9.98 | 730,146 | 70,247 | 0.960 | 70,247 | 659,899 | 0.096 |
| ca_baseline_calm | 36,183 | 13.38 | 484,258 | 34,864 | 0.964 | 34,864 | 449,394 | 0.072 |

**Reading of H-D3 — and the honest caveat that makes it point to NULL, not reducibility.**
Numerically, only 6–10% of the *magnitude* entropy of the draw stream survives as
order-relevant bits — a large-looking projection *ratio*. **But this ratio is a trap, and
we say so plainly:** the surviving bits are not a small, *reproducible-elsewhere-free*
subspace. They number `n_pivotal` ≈ 0.85–0.97 × `n_draws` — i.e. **almost every draw
contributes an order-relevant bit.** The projection throws away the draws' *precise
values* (the high-entropy mantissa) but keeps their *ordering decisions*, and there is
one ordering decision per draw. So the "effective dimension through the gate" is
≈ `n_pivotal` ≈ the number of draws — **not** a small characterizable set. The map is a
projection in *magnitude* but is *near-injective in order*, which is precisely the
condition under which exactness is irreducible. A fast engine cannot "live on a
lower-dimensional observable manifold" because that manifold has essentially full
per-draw dimension.

---

## The transferable shape (stated plainly)

**In any discrete-event simulator whose event calendar is keyed on a per-event random
delay and whose observable trace is graded under a tolerance comparator, latency-draw
exactness is reducible to a small pivot set IF AND ONLY IF the per-event margin to the
nearest neighboring event time is typically LARGE relative to the draw's jitter AND the
downstream dynamics are order-insensitive. ABIDES-class market sims violate both:**

1. **Margins are typically small relative to the jitter** (median margin ≪ latency IQR),
   because a busy event calendar packs neighbors as densely as the draw spreads them —
   widening the draw does not widen the *relative* margin. → the order-pivotal fraction is
   near 1, so there is no small pivot set.
2. **The downstream is order-sensitive** (a matching engine: who-crosses-whom depends on
   arrival order, and fills feed back into agent state). → an order change is not confined
   to a timestamp; it rewrites the event SET. So even the ±tolerance escape hatch (which
   forgives sub-tolerance *timestamp* moves) cannot forgive the *content* changes the
   reorder induces.

The corollary, which transfers: **a tolerance comparator constrains only the projection
(the trace), but when the draw→order map is near-injective in order and the dynamics are
order-sensitive, the projection is faithful — the pre-image (the draw stream) is
recoverable up to the deterministic tiebreak, and exactness is irreducible.** The
reducible case is real and worth checking for (it is why this rung had to be measured, not
assumed) — it just is not this mechanism. The single-line test to transfer to another sim:
compute the order-pivotal fraction (margin<jitter) and run one latency-only seed split
through the real gate; if pivotal≈1 and the split fails on coverage (not just on
`mv>1µs`), the sim is dense and its norm's "reproduce the stream" is correct **with
evidence**.

## What this means for the Track 3 submission (does NOT replace Phase 2)

- **Owning the ABIDES loop in Rust and deferring to numpy "only at pivots" is NOT viable**
  for Tier-A: there is no small pivot set (pivotal≈1), and a latency re-draw changes the
  SET, so an engine must reproduce the numpy latency stream **and** the agent streams
  bit-for-bit — exactly the audit's highest-risk item, now confirmed necessary by
  measurement rather than inherited.
- Phase 2's RNG-free trace/bookkeeping elision (fmt_ts round-trip + post-loop
  `get_time_dropout`, ≈1.6× Amdahl ceiling) **stands as the safe floor** and is untouched
  by this result — it lives entirely outside the draw-ordering chain.
- The reducible path re-opens only under **Tier-B** families (statistical gate, no exact
  stream needed) or a **deterministic-latency** scenario (no draw to reproduce) — both are
  already the known-safe scopes, not a new opening.

---

## Not measurable in-env / limits (marked honestly)

- **Panel, not census.** 13 of 65 public scenarios, chosen to span every family and the
  full latency axis (deterministic → uniform-tight → uniform-wide → lognormal
  low/high-σ → pareto). Per-family n is small (1–6); the pivotal-fraction and
  latency-only-fail findings are uniform across the panel with no counterexample outside
  the no-draw control, so the NULL is not fragile — but a full 65-scenario sweep was not
  run (each scenario is 10 container runs; the panel is 130 runs / ~cost-bounded). The
  margin instrumentation (cheap) could be extended to all 65 if a census is wanted.
- **Perturbation = reseed, not re-draw-in-place.** `lat_reseed` replaces the latency
  stream with an independent one (a "plausible alternate world"), which is the correct
  operationalization of "would a different draw reorder this." It is a *global* alternate
  stream, not a per-message ±ε nudge; a per-message infinitesimal-perturbation sensitivity
  (which would isolate exactly the marginal pivots) is a finer measurement not run here.
  The analytic H-D1a margin distribution is the ε-level complement to the finite
  H-D1b reseed, and the two agree (small margins ↔ high reseed sensitivity).
- **H-D3 entropy is an order-of-magnitude estimate**, not an exact channel capacity: the
  consumed side uses empirical 1 ns-resolution Shannon entropy of the realized latencies
  (a bound on order-relevant consumed bits, not the draws' full float entropy); the
  observable side uses the ≤1-bit-per-pivotal-draw bound. Both are stated so the ratio is
  interpretable, not authoritative to the bit.
- **Comparator stack skew.** Sims run on the pinned container stack (numpy 1.26.4 /
  pandas 1.5.3); the `check_tier_a` comparator runs on the host t2venv (numpy 2.5.2 /
  pandas 3.0.5). The comparator only reads parquet and computes set-coverage + Kendall-τ,
  which are version-stable; the faithfulness gate (instrumented baseline == reference,
  exact) passing on all 13 confirms no cross-stack artifact.

## Artifacts (scratch cleaned; env left in place)

The instrumentation and harness are retained under `.bigtmp/track3_drawmap/` (outside the
scored checkout, which is untouched):
- `harness.py` — in-container `send_message` margin monkeypatch + surgical stream reseed.
- `analyze.py` — host-side margin / pivotal / Tier-A-sensitivity / entropy computation.
- `run_experiment.py` — panel orchestrator.
- `out/results.json` — the full per-scenario, per-mode, per-perturb record behind every
  number above.


---

**REVIEW FIXES (accuracy only; no verdict/NULL/backed-number changed):** (1) corrected the latency-only run denominators to the retained counts — 0/36 stochastic pass out of 39 total lat_reseed runs (was "0/48" in headline, "0/45 stochastic" in H-D1b); (2) sourced the s001 finding to retained evidence (fill_count_equal=True 176=176, coverage 0.19, first fill differs at position 0/1) and marked the specific "ORDER_SUBMITTED = 120" as live-inspection-only, not a retained figure; (3) scoped "the three perturb seeds agreed tightly" to where it holds (eq_uniform_wide, as06) and noted ca_baseline_calm lat_reseed τ spans {0.822, 0.004, −0.18}, with all seeds failing Tier-A so the NULL is robust to the spread.
