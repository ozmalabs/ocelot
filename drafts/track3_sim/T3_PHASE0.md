# T3 PHASE 0 — ABIDES baseline stood up + the exact bar pinned

**Status: GREEN.** The baseline ran end-to-end locally: image built, 65/65 public
scenarios pass, stylized facts read 0.0 everywhere, throughput floor measured. This is
the load-bearing prerequisite the plan calls for — nothing downstream is blocked.

Everything below is what actually ran on this machine. No pass counts or throughput
numbers are estimated; where a number is disputed or unverifiable I say so explicitly.

---

## 1. Environment (what stood up, and what was already here)

| Item | Value |
|---|---|
| **ABIDES pinned commit** | `f9cbe51342b7dedd9587e4e069040d68a5c6477f` (canonical Track 3 baseline pin, per `baselines/README.md §1`) |
| ABIDES source | `github.com/jpmorganchase/abides-jpmc-public`, cloned to `.bigtmp/abides`, checked out at the pin (detached HEAD, verified `git rev-parse HEAD`) |
| Docker | 28.3.0 (build 38b7060) — host is fine; the image is `--platform=linux/amd64` |
| **Venv / Python** | **Reused `.bigtmp/t2venv`** (Python **3.13.5**). No fresh `t3venv` was needed. |
| Harness deps in t2venv | `qfbench2-common==2.3.1` (the exact pinned tag), `pandas 3.0.5`, `numpy 2.5.2`, `pyarrow 25.0.1`, `scipy 1.18.1`; `from enum import StrEnum` imports (so it is genuinely ≥3.13, not the 3.12 trap the README warns about) |
| git-lfs | **Was NOT installed.** Installed `git-lfs 3.4.1` via `sudo apt-get install -y git-lfs` (passwordless sudo was available). See §3. |

**On the venv split (important, not a mistake):** the ABIDES *engine* runs inside the
Docker image on Python **3.11** with the frozen `numpy==1.26.4 / pandas==1.5.3 /
scipy==1.17.1 / pyarrow==15.0.2 / coloredlogs==15.0.1` stack — this is the deliberate
exception the README documents (ABIDES needs pandas 1.x, which has no cp313 wheels, and
this is the exact stack that generated the reference traces). The **host t2venv (3.13)**
only ever *reads* the parquet the container writes and runs the scoring/semantics code,
which is exactly the split the README says is safe. So the qfbench2-common@v2.3.1 install
requirement is satisfied by t2venv; the ABIDES install requirement is satisfied inside the
image. The local non-Docker ABIDES checkout in `.bigtmp/abides` is patched (§2) and left in
place for Phase 1 profiling.

---

## 2. ABIDES install + the pomegranate-free patch

- The **baseline Docker image builds ABIDES itself** at build time: it does a fresh
  `git clone` + `git checkout <pin>`, applies **all four** `baselines/patches/*.patch`
  overlays, then `pip install --no-deps abides-core abides-markets`. So the image install
  needs no host ABIDES.
- Per the task, the **pomegranate-free patch was also applied to the local checkout**
  (`.bigtmp/abides`) so Phase 1 can profile ABIDES natively:
  `git apply baselines/patches/order_size_model.pomegranate-free.patch` → applied cleanly.
  Verified: `order_size_model.py` has **no live `import pomegranate`** afterward (the two
  remaining `pomegranate` hits are comments; the sampler is now a drop-in NumPy mixture).
- The four build-time patches (all applied inside the image, RNG-neutral by design):
  1. `order_size_model.pomegranate-free.patch` — drops the unbuildable pomegranate dep.
  2. `kernel_message_ledger.patch` — observation-only per-message send/recv/latency/
     causal_parent/seq metadata → the `message_trace.parquet` v2 schema. No RNG/ordering change.
  3. `exchange_protocol_stp.patch` — opt-in self-trade-prevention (default off; refs unchanged).
  4. `oracle_scheduled_jump.patch` — opt-in deterministic fundamental jump (default off).

---

## 3. Reference-trace cache — the git-lfs blocker, resolved

**This was a real blocker in the fresh clone and is worth recording precisely.**

- `.gitattributes` marks `*.parquet filter=lfs`. In the checkout the 190 unit parquet files
  were **131–132-byte LFS pointer stubs** (`version https://git-lfs.github.com/spec/v1`),
  and **git-lfs was not installed** — so `build_reference_cache.py` would have refused
  (it explicitly rejects pointer stubs via `is_lfs_stub`).
- Resolution: installed git-lfs 3.4.1, `git lfs install`, `git lfs pull` in `.bigtmp/track3`.
  After pull: **0 stubs remain**, all 190 parquet files are real data (287 MB total).
- `python regression_suite/build_reference_cache.py` → **built 65 scenario references**
  (symlinked into `regression_suite/reference_traces/`); the 6 `t3-gbatch-*` batch units are
  intentionally not bridged (different shape), matching the script's documented behavior.

So: the units carry **real trace.parquet via LFS, not permanent stubs** — the content was
retrievable, it just needed git-lfs + `git lfs pull`. Not a hard blocker in this environment
(network + sudo were available); it *would* be a blocker in a sandbox without either.

---

## 4. Baseline Docker image

- `docker build --platform=linux/amd64 -t track3-abides-baseline:latest baselines/` →
  **built OK.** Image `sha256:93ed48c2d5d0…`, **561 MB**.
- Only warning is cosmetic (`FromPlatformFlagConstDisallowed` on the pinned `--platform`).
- Smoke test: `docker run --rm track3-abides-baseline:latest simulate --help` prints the
  expected `--config/--out/--seed` usage. The `simulate` verb works.

---

## 5. Public regression suite — **65 / 65 PASS**

Ran exactly the documented command (via t2venv python, `PYTHONPATH=<repo root>`, 4 workers):

```
python regression_suite/run_regression.py \
    --candidate-image track3-abides-baseline:latest \
    --scenarios-dir regression_suite/scenarios/ \
    --reference-dir regression_suite/reference_traces/ \
    --output-dir run_outputs/ --workers 4
```

**Result: Total 65 · Passed 65 · Failed 0 · Errored 0.** Every scenario shows
`semantic_pass=PASS` and `stylized_pass=PASS`, no failure labels. Both tiers present
(≈40 Tier-A, ≈25 Tier-B). Exit code 0.

This confirms the environment is sound: the baseline reproduces its own reference traces
exactly, so any future divergence is a real regression in our accelerator, not an env problem.

> The per-scenario `events_per_sec` printed in that table (≈12,200–20,100) is the adapter's
> **self-reported** number and is NOT the ranked quantity. The ranked/floor number is the
> organizer timer's own measurement (§7).

---

## 6. Stylized-fact readings — 0.0 everywhere (as expected)

All **65** `run_outputs/<scenario_id>/stylized_fact_report.json` read **exactly**:

```json
{"ks": 0.0, "acf_abs_l2": 0.0, "hill_abs": 0.0, "depth_js": 0.0}
```

Max absolute value across all four metrics over all 65 scenarios = **0.0** (zero non-zero
readings). This is precisely what the README predicts for the unmodified baseline scored
against its own references, and it is the correct "before you change anything" reading — the
four admissibility ceilings (KS ≤ 0.08, ACF ≤ 0.12, Hill ≤ 1.5, depth-JS ≤ 0.10) are all
cleared with full margin. It confirms the stylized-fact math is wired and computing (not
silently no-op'ing).

---

## 7. Baseline throughput — **THE FLOOR = 11,146 events/sec** (measured)

Ran the canonical timer (5 runs, warm-up discarded, median — the committed protocol):

```
python throughput/timer.py --image track3-abides-baseline:latest \
    --scenario regression_suite/scenarios/as06_throughput_fast.json
```

| Metric | Value (events/sec) |
|---|---|
| **median (the floor to beat)** | **11,146.27** |
| mean | 11,106.00 |
| std | 171.44 (tight; ~1.5%) |
| min / max | 10,835.87 / 11,295.60 |
| runs | 5, warm-up discarded, 4 scored |

Wall-clock per scored run ≈ 6.6–6.9 s; host peak memory ≈ 263 MB; `host_gpu_seconds = null`
(CPU-only, no GPU on this box). Full JSON saved at
`drafts/track3_sim/phase0_throughput.json`.

**This 11,146 ev/s is the Phase-0 floor Phase 3 must beat, measured on THIS machine.**

**Honest caveat on the number's meaning.** It is below both figures in `baselines/README.md`
(the disputed ~65,000 and the 13,793 geomean of the shipped `events.json`). That is consistent
with — not contradicted by — the README, which states in bold that *none* of its throughput
figures were measured on the evaluation fleet and that 65,000 is "the number least likely to be
right." Three things also make a direct comparison invalid: (a) this is one specific scenario
(`as06_throughput_fast`, a Tier-B unit `a350b90c…`), not a geomean over the roster; (b) it is
this dev box's CPU, not the sealed B200 host; (c) the README's 13,793 covers only the sim loop
whereas `timer.py` times the whole container. **Use 11,146 as the local, same-box, apples-to-
apples floor** — the only number that matters for measuring our own speedup — and do not treat
any README figure as a target. Local throughput is a directional guide, never the leaderboard rank.

---

## 8. THE EXACT TIER-A REPRODUCTION CONTRACT

Pinned verbatim from `.bigtmp/track3/qfbench2_track_simulation/semantics.py::check_tier_a`
(+ `semantic_regression_pass` wiring, + the module constants). This is the correctness gate
the whole task is built around. A single breach anywhere ⇒ `t3.semantic_regression_fail`
⇒ inadmissible. There is **no majority rule** — every scenario is graded on its own.

**Which scenarios are Tier A.** `TIER_A_FAMILIES = {1, 3, 6, 7, 8}` (families 7 exchange-
protocol and 8 reactive-agent are explicitly listed so a tier-less card cannot fall back to the
weaker Tier B). A card may override the tier, but absent an override, family decides.

**The identity key of an event** = the 6-tuple
`KENDALL_KEY_COLUMNS = (order_id, msg_type, agent_id, side, price, size)`. Keys are compared
by **value, not dtype** (`_canonical_key_matrix`): an integral float `100.0` renders to `"100"`
so an int64→float64 promotion from a pandas round-trip does not spuriously fail; a non-integral
value keeps full `repr` precision, so the normalization does not loosen the check.

Tier A passes **iff ALL of the following hold** (each is an independent breach):

0. **Exact row count.** `len(candidate) == len(reference)`. The scenario is deterministic
   given its seed, so a faithful run emits *exactly* as many rows. Extra rows are also refused
   because the row count is the ranked events/sec numerator — padding must not pay.

1. **Exact fill count.** Fills = rows with `msg_type ∈ {ORDER_FILLED, PARTIAL_FILL}`
   (`FILL_MSG_TYPES`). `len(candidate_fills) == len(reference_fills)`.

2. **Exact fill sequence, positionally.** Taking fills in trace order and comparing index-by-
   index, candidate and reference must be **identical** in `order_id`, `price`, and `size`
   at every fill position. (Any mismatch reports the first offending index.)

3. **Per-fill timestamp tolerance = ±1 µs.** `DEFAULT_TIMESTAMP_TOLERANCE_NS = 1_000`
   nanoseconds. For every fill position, `|cand.t_ns − ref.t_ns| ≤ 1000 ns`. This ±1 µs is
   the *only* numeric tolerance anywhere in Tier A. (It is a per-scenario card value threaded
   through `semantic_regression_pass`; 1000 ns is the default.)

4. **Exact bidirectional event coverage (the multiset match, BOTH directions).** Build, for
   each trace, the multiset of `(identity-key, per-key occurrence-index)` pairs over the WHOLE
   trace (`_file_order_positions`, **no truncation** — the old 50k-event window is gone).
   Then:
   - `n_missing` = reference pairs absent from the candidate — must be **0**.
   - `n_extra`  = candidate-only pairs not in the reference — must be **0**.
   A missing event *and* an extra event are each a breach. (The old code intersected the key
   sets, which made candidate-only rows invisible; that hole is closed.)

5. **Kendall-τ ≥ 0.999 on event ordering, over the whole trace.**
   `DEFAULT_KENDALL_TAU_FLOOR = 0.999`. Over the events common to both traces (which, once 0
   and 4 pass, is every event), take each event's file-order position in reference vs candidate
   and compute Kendall-τ between the two position vectors; require `τ ≥ 0.999`. A non-finite τ
   is raised as an organizer fault (`NonfiniteStatistic`), not charged to the submission.

**In one sentence:** a Tier-A candidate must emit the **same number of rows**, the **same
multiset of (order_id, msg_type, agent_id, side, price, size) events with the same per-key
multiplicity in both directions (no missing, no extra)**, the **same fills in the same order at
the same order_id/price/size**, each fill's timestamp **within ±1 µs**, and an overall event
ordering with **Kendall-τ ≥ 0.999** — with the only numeric slack being that ±1 µs.

**Why this pins the plan.** This contract is exactly why the plan's PRIMARY scope is "keep the
numpy agents (and their `np.random.RandomState` draws) in place and accelerate only an RNG-free
hot loop." Any acceleration that reorders events, changes a draw, or perturbs a timestamp by
>1 µs on a fill fails 0/2/3/4/5 immediately. Tier A leaves essentially no slack to approximate.

### Companion gates that ride alongside Tier A (context, not part of `check_tier_a` itself)
Most units (`requires_message_ledger = true` on **59 of 72** cards, read from
`[scoring.params]`) also require a `message_trace.parquet` checked by
`check_message_semantics` (latency identity `t_recv−t_send==latency_ns`, `latency ≥ 0`,
`seq` a contiguous `0..N-1` permutation, causal parent delivered-before-child, `AGENT_WAKEUP`
= self / zero-latency / no send time) and, against the reference, `check_message_reference`
(realized-latency KS ≤ 0.08, endogenous wakeup count within ±5%, candidate ledger ≥ 90% of the
reference's sent-message count). Family-7 adds `check_protocol_fidelity` (g3.5): exec-report
count-by-type must match exactly and exec-report latency KS ≤ 0.08. These are not optional for
those units and must be preserved by any accelerator.

### Tier B (families 2,4,5), for completeness
`check_tier_b`: mid-price log-return two-sample **KS ≤ 0.08** (same calibrated ceiling as the
stylized-fact gate) and time-averaged **spread within ±10 bps**. Tier-B scenarios must *also*
satisfy Tier-A fill semantics (the harness runs Tier A on them too: `semantic_pass = tier_a and
tier_b`). Prices/sizes must be strictly positive and finite (sanity gate runs first on both sides).

---

## 9. What is proven locally vs what remains unverifiable here

**Proven on this machine (green):**
- ABIDES stands up at the exact pin; the pomegranate-free patch applies cleanly.
- Reference cache builds from real LFS-backed traces (0 stubs).
- Baseline image builds and runs `simulate`.
- **65/65** public scenarios pass; stylized facts **0.0** everywhere.
- Baseline throughput floor **measured: 11,146 ev/s** (median, canonical protocol).
- The full Tier-A contract is read directly from the scorer source and pinned above.

**Not verifiable in this environment (by design of the task, not a failure):**
- The **sealed** scenarios (count unpublished), their sealed reference traces, and
  **SS-BENCH** — none are distributed; can only be exercised in the org's eval environment.
- The **leaderboard rank / fleet throughput** — the README states no throughput figure on the
  page was measured on the B200 + gVisor fleet; our 11,146 is a dev-box CPU number, useful only
  as a same-box baseline for measuring our own speedup, not as a predictor of rank.
- **GPU** paths — this box reports `host_gpu_seconds = null` (no GPU); B200/CUDA behavior can't
  be checked here.
- The 6 **batch** (`t3-gbatch-*`) units and the `simulate-batch` verb were not exercised in
  Phase 0 (Phase 3 territory); only the 65 single-scenario units were run.

**One environment change made:** installed `git-lfs 3.4.1` via `sudo apt`. No other system
mutation.

---

## 10. Artifacts left in place for Phase 1 (do NOT delete)
- `.bigtmp/abides` — ABIDES at the pin, pomegranate-free patch applied (for native profiling).
- `.bigtmp/t2venv` — the Python 3.13 harness venv (qfbench2-common 2.3.1).
- `.bigtmp/track3/regression_suite/reference_traces/` — the built cache (65 symlinked refs).
- `.bigtmp/track3/units/*` — real LFS-pulled parquet (287 MB).
- `track3-abides-baseline:latest` — the built Docker image.
- `.bigtmp/track3/run_outputs/` — 65 traces + stylized reports + report.json.
- `drafts/track3_sim/phase0_throughput.json` — the raw floor measurement.

## Phase 0 verdict
**GREEN — baseline reproduces itself 65/65, floor = 11,146 ev/s, Tier-A contract pinned.**
Phase 1 (profile `abides.run` to find a hot, RNG-free inner loop) is unblocked.
