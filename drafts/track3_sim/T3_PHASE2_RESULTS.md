# T3 PHASE 2 — RESULTS: elide dead post-loop `get_time_dropout` compute

**One line:** The profile-guided elision is CORRECT (H-T2a **ACCEPTED** — 65/65
regression green + byte-identical `trace.parquet` and `message_trace.parquet` on both
s012 and as06 + zero stylized-fact divergence) and gives a real, modest speedup
(H-T2b: **+8.45%** end-to-end on the official timer.py protocol; **+13.1%** on the
in-container `abides.run` wall the ranked events/sec is derived from). No trace byte
moved, so nothing was traded for the speed.

> Honest note (required): every number below is a **same-box CPU measurement** on this
> workstation. It is NOT the sealed SS-BENCH ranked number. The ranked events/sec is
> produced by the org Runner on sealed hardware and is not obtainable locally
> (RAW / not-a-rank-predictor). No number here is fabricated; where a measurement is a
> single run vs a median-of-4, it is labelled as such.

---

## What was changed (the surgical elision)

`ExchangeAgent.get_time_dropout` (`abides-markets/abides_markets/agents/exchange_agent.py:909`)
runs in `kernel_terminating` (POST event-loop, inside `abides.run`). It does
`pd.DataFrame(book_log2)` + `df.iterrows()` over the entire L2 book log — the slowest
pandas access pattern — solely to populate `self.metric_trackers[symbol]`
(a `MetricTracker` liquidity-dropout stat). The patch inserts a single early `return`
immediately after the existing `if len(book) == 0: return`, guarding the dead pandas
block. It:

- keeps `book_logging=True` and `book_log2` **fully populated and untouched** (the
  elision is downstream of the book log, not on it);
- does **not** disable any logging;
- leaves `self.metric_trackers[symbol]` as its default-initialized `MetricTracker`
  (created in `ExchangeAgent.__init__`), so the subsequent
  `metric_trackers[symbol].total_exchanged_volume` / `.last_trade` writes in
  `kernel_terminating` still succeed (no `KeyError`, no `AttributeError`);
- is RNG-neutral and ordering-neutral: it touches no `np.random` draw and no event.

**Patch file:** `drafts/track3_sim/exchange_time_dropout_elide.patch`
(installed at build time as `baselines/patches/exchange_time_dropout_elide.patch`).

**Build wiring:** `baselines/Dockerfile` applies it the same way as the four existing
build-time patches (`git -C /tmp/abides apply ...` against a fresh pinned clone), but
gated behind `ARG FAST_ELIDE_DROPOUT` (default `0`). This keeps
`track3-abides-baseline:latest` bit-for-bit reproducible (the baseline build ignores
the patch) while the fast image opts in:

```
docker build --platform=linux/amd64 --build-arg FAST_ELIDE_DROPOUT=1 \
    -t track3-abides-fast:latest baselines/
```

The pinned ABIDES checkout (`.bigtmp/abides`, commit
`f9cbe51342b7dedd9587e4e069040d68a5c6477f`) was **not** edited in place — the diff was
generated against it and immediately reverted; the patch was verified to
`git apply --check` cleanly against the pinned commit.

**Dead-path audit (re-confirmed this phase, not just assumed):** `grep` across
`qfbench2_track_simulation/`, `scoring/`, and `baselines/abides_fork/` finds **zero**
references to `metric_tracker`, `time_dropout`, `get_time_dropout`, or `no_liquidity`.
The scored `trace.parquet` / `message_trace.parquet` are built by
`abides_fork/trace.py` from the event log; the stylized-fact depth check reads
`QUOTE_UPDATE` rows from that trace (`semantics.depth_histogram`), not `book_log2` and
not `metric_trackers`.

---

## H-T2a — correctness invariant (THE GATE): **ACCEPTED**

### (1) Full public regression — 65/65 PASS

```
regression_suite/run_regression.py --candidate-image track3-abides-fast:latest
  --scenarios-dir regression_suite/scenarios --workers 4
=> Total: 65   Passed: 65   Failed: 0   Errored: 0
```

Every one of the 65 public scenarios passes both the semantic gate (Tier A exact
fill-sequence / Kendall-τ order; Tier B statistical proximity) **and** the
stylized-fact admissibility gate. Report: `drafts_prof/phase2_out/fast_regression/report.json`.

### (2) Byte-identity of the scored artifacts — **byte-identical on both scenarios**

Baseline vs fast, same fixed scenario seed, `--network none`, comparing both the
independent host `sha256sum` of the parquet bytes **and** the in-container
`events.json` sidecar sha. `cmp -s` confirms byte-for-byte identity.

| scenario | tier | seed | artifact | baseline sha256 | fast sha256 | identical? |
|---|---|---|---|---|---|---|
| **s012** `partial_fill_cancel_race`<br>(`a1b2c3d4-0012…`, n_events=202,291, n_msgs=178,236) | A | 1012 | `trace.parquet` | `259ef9b786471156e32cbfba678f279d6ad3a7991e0d03ed20a530f71e05887e` | `259ef9b786471156e32cbfba678f279d6ad3a7991e0d03ed20a530f71e05887e` | **YES ✓** |
| | | | `message_trace.parquet` | `4e1977ea5947ed2c8253dd540793eaf65e8e72269502d9a9a0023c71df0492e4` | `4e1977ea5947ed2c8253dd540793eaf65e8e72269502d9a9a0023c71df0492e4` | **YES ✓** |
| **as06** `throughput_fast`<br>(`a350b90c-0348…`, n_events=74,502, n_msgs=83,337) | B | 1040981657 | `trace.parquet` | `1e7761ee74ade7e23bb4f40410f8525705601f10cc9e6e855d5df798c3e94350` | `1e7761ee74ade7e23bb4f40410f8525705601f10cc9e6e855d5df798c3e94350` | **YES ✓** |
| | | | `message_trace.parquet` | `16f64ee89dd18988792dadc8c6ac3b02881e3d29fc5c80d4df19ae14fa738f77` | `16f64ee89dd18988792dadc8c6ac3b02881e3d29fc5c80d4df19ae14fa738f77` | **YES ✓** |

`n_events` and `n_messages` also match exactly for both scenarios. s012 was chosen as
the book-heavy Tier-A exact unit (the most demanding case for the matching engine);
as06 as the throughput unit. Both are `sha`-identical, confirming the elided metric is
not in the scored trace on either path.

### (3) The four stylized-fact numbers — unchanged (0.0 divergence)

Computed fast-vs-baseline through the exact scored code path
(`semantics.depth_histogram` + `qfbench2_common.scoring.stylized_facts.stylized_fact_report`):

| scenario | ks | acf_abs_l2 | hill_abs | depth_js |
|---|---|---|---|---|
| s012 | 0.0 | 0.0 | 0.0 | 0.0 |
| as06 | 0.0 | 0.0 | 0.0 | 0.0 |

All four divergences are exactly zero — necessarily, because the inputs (the traces)
are byte-identical.

**H-T2a verdict:** the elision leaves the scored path bit-identical. The correctness
gate is satisfied absolutely; nothing was traded for speed.

---

## H-T2b — speedup: **measured, real, modest (+8.45% end-to-end / +13.1% on the run wall)**

Protocol: `throughput/timer.py`, `--runs 5`, warm-up discarded, median of the 4 scored
runs — identical to the Phase-0 floor protocol. Scenario: `as06_throughput_fast`
(the Phase-0 floor unit). CPU-only box; `--cpus 4 --memory 16g` (timer defaults).

| image | median ev/s | mean | std | min | max |
|---|---:|---:|---:|---:|---:|
| `track3-abides-baseline:latest` | **11,174.7** | 11,168.8 | 34.9 | 11,114.9 | 11,210.6 |
| `track3-abides-fast:latest` | **12,118.7** | 12,101.6 | 62.9 | 11,999.0 | 12,170.0 |

- **Same-box speedup (fast ÷ baseline median): 1.0845× (+8.45%).**
- **vs the Phase-0 recorded floor (11,146 ev/s): fast = 1.0873×.** The baseline
  re-measured this session at 11,174.7 ev/s = **1.003×** the recorded floor, confirming
  same-box consistency (the floor reproduces).

Raw ev/s per run — baseline `[11442.8*, 11166.3, 11183.2, 11210.6, 11114.9]`,
fast `[12190.0*, 12170.0, 11999.0, 12124.1, 12113.4]` (`*` = discarded warm-up).
Files: `drafts_prof/phase2_out/timer_{baseline,fast}.json`.

### Why +8.45% and not the ~1.16× Amdahl expectation — honest reconciliation

The prereg's Amdahl estimate (~1.16× on as06) was against the **whole `simulate()`
wall** where the dropout metric profiled at ~14%. But `timer.py`'s `events_per_sec`
denominator is the in-container `wall_clock_sec` measured in `simulate.py` around
`abides.run(config)` **only** — which *includes* `kernel.terminate → get_time_dropout`
but *excludes* `extract_trace` / `to_parquet`. The docker-level wall the timer times
end-to-end additionally includes ~1.6 s of trace extraction + parquet writes + Python
import/startup + container teardown, all of which the patch does not touch.

Single-run in-container `events.json` (as06, from the byte-identity runs) makes the two
denominators explicit:

| denominator | baseline | fast | speedup |
|---|---:|---:|---:|
| in-container `abides.run` wall (run + terminate) | 4.0359 s → 18,460 ev/s | 3.5685 s → 20,878 ev/s | **1.131× (+13.1%)** |
| timer.py docker end-to-end wall (median) | 6.6733 s | 6.1482 s | **1.085× (+8.45%)** |

The same absolute saving (~0.47 s in-container / ~0.53 s docker-wall) is a larger
fraction of the smaller run wall (+13.1%, matching the Phase-1 ~14% dropout share
cleanly) and a smaller fraction of the larger docker wall diluted by fixed,
unchanged overhead (+8.45%). Both numbers are real and mutually consistent; neither is
fabricated. On the book-heavier s012 (21% dropout share in Phase 1) the in-container
saving is proportionally larger, but s012 is a Tier-A correctness unit, not the
throughput floor unit, so it is reported for correctness (byte-identity) not for the
ranked ev/s.

**H-T2b verdict:** not rejected. A material, honestly-measured speedup — modest at the
end-to-end docker level (+8.45%), squarely at the Phase-1 profile prediction on the
run+terminate wall the metric is derived from (+13.1%). This is the single largest safe
RNG-free slice; the fmt_ts round-trip (~6.6%) and trace extraction (~15%) remain as
further Phase-1-identified RNG-free targets if more is wanted.

---

## Proven-vs-assumed ledger

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | `get_time_dropout` output (`metric_trackers`) is referenced nowhere in the scorer / adapter | **PROVEN** | grep of `qfbench2_track_simulation/`, `scoring/`, `baselines/abides_fork/` → 0 hits |
| 2 | Eliding it keeps the scored `trace.parquet` byte-identical | **PROVEN** | sha256 identical baseline==fast on s012 + as06 (host `sha256sum` + in-container sidecar + `cmp -s`) |
| 3 | Eliding it keeps `message_trace.parquet` byte-identical | **PROVEN** | sha256 identical baseline==fast on s012 + as06 |
| 4 | The four stylized-fact numbers are unchanged | **PROVEN** | ks/acf_abs_l2/hill_abs/depth_js all 0.0 fast-vs-baseline, both scenarios (and implied by byte-identity) |
| 5 | All 65 public scenarios still pass | **PROVEN** | `run_regression.py` → 65/65, 0 failed, 0 errored |
| 6 | `book_log2` / `book_logging` unchanged | **PROVEN (by construction + byte-identity)** | patch guards only the metric computation after the book log is read; QUOTE_UPDATE-derived trace bytes are identical |
| 7 | The elision is RNG/ordering-neutral | **PROVEN (by construction + byte-identity)** | it is post-loop, touches no draw; identical fill sequence ⇒ identical event ordering (Tier-A green + sha-identical) |
| 8 | Baseline image remains reproducible after wiring the patch | **PROVEN** | patch gated behind `ARG FAST_ELIDE_DROPOUT=0`; baseline build path is byte-unchanged; baseline re-measured at 1.003× the Phase-0 floor |
| 9 | Speedup ≈ the profiled dropout share on the run wall | **PROVEN (this box)** | +13.1% on `abides.run` wall vs Phase-1 ~14% |
| 10 | End-to-end throughput improves above the Phase-0 floor | **PROVEN (this box)** | fast median 12,118.7 ev/s = 1.0873× the 11,146 floor |
| 11 | This equals the SS-BENCH ranked number | **NOT CLAIMED / not obtainable locally** | same-box CPU proxy only; ranked number is sealed-hardware RAW |
| 12 | Speedup generalizes to the full eval mix | **ASSUMED (bounded)** | measured on as06 (throughput unit) + implied larger on book-heavy units; the eval mix is not locally runnable |

---

## Artifacts (left in place)

- `drafts/track3_sim/exchange_time_dropout_elide.patch` — the patch (copy of the one
  installed as `baselines/patches/exchange_time_dropout_elide.patch`).
- `baselines/patches/exchange_time_dropout_elide.patch` — build-time install location.
- `baselines/Dockerfile` — wired with `ARG FAST_ELIDE_DROPOUT` (default 0 = baseline).
- `track3-abides-fast:latest` — the rebuilt fast image (left in place).
- `track3-abides-baseline:latest` — unchanged, reproducible, left in place.
- `drafts_prof/phase2_out/fast_regression/report.json` — the 65/65 regression report.
- `drafts_prof/phase2_out/timer_{baseline,fast}.json` — the H-T2b throughput runs.
- `drafts_prof/phase2_sha/compare_sha.sh`, `sf_check.py`, and the `{s012,as06}/` output
  trees — the byte-identity + stylized-fact evidence.

## Discipline note

PREREG-then-measure honored: the elision was written and the correctness gate
(H-T2a) proven **before** any speedup number was accepted, and the gate is absolute —
had any trace sha moved, this would have been an immediate revert and an H-T2a
rejection (a valid, plan-saving finding). It did not move. The speedup is reported
exactly as measured, with the denominator caveat stated rather than hidden.
