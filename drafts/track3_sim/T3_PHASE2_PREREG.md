# PREREG — Track 3 Phase 2: elide dead post-loop compute (profile-guided, RNG-free)

**Committed BEFORE any speedup number.** PREREG-then-measure. Phase 1
(T3_PHASE1.md) verdict: the sim loop is RNG-entangled (a Rust rewrite breaks
Tier-A), but ~35–40% of wall-clock is RNG-free bookkeeping AROUND the loop. This
phase takes the single largest, safest slice of that, verified dead on the
scored path.

## The target (verified, not assumed)

`ExchangeAgent.analyse_order_book` → `get_time_dropout` runs in
`kernel_terminating` (POST-loop) and:
- costs **21% (s012) / 14% (as06) of wall-clock** (Phase 1 profile), via
  `pd.DataFrame(book_log2)` + `df.iterrows()` over the whole book log (the
  slowest pandas pattern);
- writes ONLY `self.metric_trackers[symbol]` (a MetricTracker liquidity-dropout
  stat);
- that output is referenced **NOWHERE** in `qfbench2_track_simulation`
  (grep-confirmed: no `metric_tracker`/`get_time_dropout`/`time_dropout` in the
  scorer). The scored `trace.parquet` is built by `abides_fork/trace.py` from the
  event log, not from `metric_trackers`.
- The stylized-fact **depth check reads `QUOTE_UPDATE` rows from the scored
  trace** (`semantics.py:187 depth_histogram`), NOT `book_log2` and NOT
  `metric_trackers` — so eliding the dropout metric cannot move any of the four
  stylized-fact numbers.

So `get_time_dropout` is dead compute on the scored path.

## Hypotheses (falsifiable, pre-declared)

- **H-T2a (correctness invariant — the gate):** eliding the `get_time_dropout`
  computation leaves `trace.parquet`, `message_trace.parquet`, and the four
  stylized-fact numbers **byte/bit-identical** to the baseline. PROVEN iff all 65
  public scenarios still pass `run_regression.py` AND each output
  `trace_sha256` equals the baseline's. Any single trace-sha change =
  the elision touched a scored quantity = REJECT (it was not dead after all).
- **H-T2b (speedup):** wall-clock drops by ≈ the profiled dropout share.
  Measured `events_per_sec` on `as06_throughput_fast` (the Phase-0 floor unit,
  ~14% dropout) rises materially above the Phase-0 floor (11,146 ev/s).
  Report the measured speedup; the Amdahl expectation is ~1/(1−0.14) ≈ 1.16×
  on as06, larger (~1.27×) on book-heavy Tier-A units. No fabricated number.

## Implementation constraint (safety-first)

- The elision must NOT disable `book_logging` (that could change other behavior);
  it must skip ONLY the `get_time_dropout` computation (or its `iterrows` body),
  keeping `book_log2` intact. Minimal, surgical: a build-time patch to
  `analyse_order_book` (or a config flag the adapter sets) that no-ops the
  dropout metric. Same shape as ABIDES's existing build-time patches
  (`baselines/patches/`).
- If ABIDES's `analyse_order_book` cannot be patched without touching the pinned
  upstream, add the patch to `baselines/patches/` the way the pomegranate-free
  patch is applied at image build — never edit the pinned checkout in place.
- Re-run `run_regression.py` (65/65 + stylized facts) after the change. Correctness
  gate first, speed second. A single regression = revert.

## What a null / rejection means

- H-T2a rejected (a trace sha changes) → `get_time_dropout` was NOT dead on that
  scenario (it must feed something we missed); revert, re-audit the dependency,
  report the surprise. The correctness gate is absolute — never ship a trace
  change for speed.
- H-T2b tiny → the dropout share is smaller than profiled on the eval mix; report
  the honest measured speedup, and move to the next RNG-free slice (fmt_ts round
  trip 6.6%, trace extraction ~15%) only if worth it. The Amdahl ceiling for the
  whole RNG-free zone is ~1.6×; this phase captures the biggest single slice.

## Deliverables

- `T3_PHASE2_RESULTS.md` — H-T2a (65/65 + sha-identical Y/N), H-T2b (measured
  ev/s before/after + speedup), proven-vs-assumed ledger.
- the patch (in `baselines/patches/`-style) + the rebuilt image + a
  regression-green log.
- honest note: this is a same-box CPU measurement; the ranked number is on the
  sealed SS-BENCH and is not obtainable locally (RAW / not-a-rank-predictor).

## Discipline
No fabricated numbers. Correctness (H-T2a) gates everything — a trace-sha change
is an immediate revert, not a tradeoff. Reuse the ABIDES build-time patch
mechanism; do not edit the pinned checkout. PREREG-then-measure; the null
(elision not safe, or speedup tiny) is a valid finding.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
