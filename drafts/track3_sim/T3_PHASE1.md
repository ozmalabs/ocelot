# T3 PHASE 1 — Profile ABIDES, find the hot loop, decide GO/NO-GO

**VERDICT: NO-GO for the plan's PRIMARY scope as originally framed ("port the hottest
RNG-free *inner sim loop* to Rust and inherit Tier-A for free"), but a QUALIFIED GO on a
narrower, genuinely-safe target that the profile actually surfaces.** The hot inner loop
(matching + event dispatch + agent stepping) is *individually* RNG-free in its arithmetic
but **RNG-entangled by data dependency**: every event's ordering flows from a per-message
`np.random.RandomState` latency draw and per-wakeup agent draws, so a Rust kernel that
re-implements the loop cannot preserve the exact draw *consumption order* without also
re-implementing the numpy agents — which breaks Tier-A. HOWEVER, ~35–40% of wall-clock is
**post-/around-loop, provably RNG-free bookkeeping** (timestamp string-formatting, per-event
log serialization, an end-of-run book-dropout metric, and trace/parquet extraction) that
touches no draw and no event ordering. That is the only safe Rust target, and its Amdahl
ceiling is bounded (see §6). The plan's honest-risk clause fires: the big, hot machinery is
entangled; the safe machinery is real but capped. Details, measured, below.

Everything here is **measured**, not static, except where a line is explicitly marked
`[static]`. Two independent profilers (cProfile deterministic + py-spy sampling) agree.

---

## 1. How this was profiled (and the one honest caveat)

**Primary = cProfile INSIDE the baseline Docker image** (`track3-abides-baseline:latest`),
i.e. the exact scored engine on the **pinned stack** the reference traces were generated on:
Python 3.11.16, **numpy 1.26.4 / pandas 1.5.3 / scipy 1.17.1 / pyarrow 15.0.2**, all four
build-time patches applied. Driven through the real scored path
`abides_fork.simulate.simulate()` → `build_config` → `abides.run` → `extract_trace` →
parquet, exactly as the harness runs it. Driver: `drafts_prof/profile_driver.py`; raw
`.pstats` + text in `.bigtmp/track3/drafts_prof/out/`.

**Cross-check = py-spy 0.4.2 sampling** (250 Hz, speedscope, `--subprocesses`) on the same
in-container scored path, looped ×4 (15,887 samples / 63.5 s). Leaf-frame self-time
proportions corroborate cProfile within noise (§4).

**The DIRECT non-Docker Python path was ALSO validated to run** in the host venv
(`.bigtmp/t2venv`, Python 3.13.5, numpy 2.5.2 / pandas 3.0.5): `abides_core`,
`abides_markets`, and `abides_fork.simulate` all import and `abides.run` is callable there
after installing `coloredlogs` (the one missing runtime dep). I did **not** use the native
path as the primary profile for two concrete reasons, both worth recording:
  1. **The local `.bigtmp/abides` checkout is only partially patched.** Phase 0 applied only
     the pomegranate-free patch to it; the other three build-time patches (STP, ledger,
     oracle-jump) are applied *inside the image*, not to the local checkout. A native run of
     `s012` fails with `ExchangeAgent.__init__() got an unexpected keyword argument
     'stp_policy'` — the local engine is not the scored engine.
  2. **pandas-3.0 API drift.** `build_config` does `int(pd.to_datetime(_DATE).to_datetime64())`,
     which raises under numpy 2.x (can't `int()` a µs-unit `datetime64`). This is a pure
     market-clock-origin conversion — RNG-neutral, ordering-neutral — but it confirms the
     native host stack is *not* the reference stack.

So: the profile numbers are from the **authoritative pinned container**. The native path is
reported as runnable (per the task's fallback instruction) but is explicitly NOT the stack
that grades, so it was not used for the load-bearing numbers. **No profile number is
fabricated; none is static unless tagged `[static]`.**

**Scenarios profiled** (as instructed — a mid-size Tier-A exact unit + a Family-6 throughput
unit; there is no numbered "family 1/3/6" field in the public cards, so I map by the
`scenario_family` string that the Tier-A families {1,3,6,7,8} correspond to):

| unit | `scenario_family` | tier | agents | horizon | n_events | n_msgs | role |
|---|---|---|---|---|---|---|---|
| `s012_partial_fill_cancel_race` | matching-engine-semantics | **A (exact)** | 7 | 5 s | 202,291 | 178,236 | the Tier-A exact hot-path unit (fills/partials/cancels) |
| `as06_throughput_fast` | agent-mix | B | 20 | 20 s | 74,502 | 83,337 | the Family-6 throughput unit (== the Phase-0 floor unit) |

`s012` was chosen over the smaller `s001` (4 agents) because it stresses the matching engine
hardest (partial-fill + cancel race), i.e. the most favorable case for a matching-engine port.

---

## 2. Wall-clock attribution by component (MEASURED, cProfile self-time)

Self-time sums to total runtime, so **% self-time == % wall-clock** — this is the honest
Amdahl denominator. (cProfile inflates absolute wall ~1.5× vs untimed — s012 ran 15.85 s
untimed under py-spy vs 24.4 s under cProfile — but the *proportions* are what matter and are
stable across both profilers.)

### `s012_partial_fill_cancel_race` (Tier-A exact) — total 24.410 s

| component | self-time | % wall | RNG status |
|---|---:|---:|---|
| **other_python** (isinstance, `maybe_convert_objects`, str.format, len, id…) | 6.678 | **27.4%** | RNG-free (mostly trace/log glue) |
| **pandas_trace_io** (Series/DataFrame build in log→trace) | 4.419 | **18.1%** | RNG-free (trace extraction) |
| **matching_engine** (order_book + price_level + orders obj) | 3.145 | **12.9%** | RNG-free arithmetic, **order-entangled** |
| **kernel_dispatch** (kernel.py + PriorityQueue + get_latency) | 2.690 | **11.0%** | **RNG-ENTANGLED** (latency draw sets delivery time) |
| **agent_logic** (trading_agent/exchange_agent/abides_fork agents) | 1.747 | 7.2% | **RNG-ENTANGLED** (agents draw on wakeup) |
| **fmt_ts** timestamp→string | 1.601 | **6.6%** | **RNG-free bookkeeping** |
| numpy_generic (clip, vstack, fromnumeric wrappers) | 1.568 | 6.4% | RNG-free (mostly `clip` inside get_latency + trace) |
| **trace_extraction** (parse_logs_df + abides_fork/trace.py) | 1.447 | 5.9% | RNG-free bookkeeping |
| deepcopy (order/log deepcopy for logEvent) | 0.988 | 4.0% | RNG-free bookkeeping |
| parquet_write | 0.126 | 0.5% | RNG-free |
| oracle_rng | 0.001 | 0.0% | RNG (tiny) |
| **— of which: raw RNG draw self-time (`mtrand` methods)** | **0.255** | **1.04%** | the actual draws |

### `as06_throughput_fast` (Family-6 throughput) — total 9.967 s

| component | self-time | % wall | RNG status |
|---|---:|---:|---|
| other_python | 2.985 | 29.9% | RNG-free |
| pandas_trace_io | 1.298 | 13.0% | RNG-free |
| kernel_dispatch | 1.109 | 11.1% | RNG-entangled |
| matching_engine | 1.088 | 10.9% | RNG-free arith, order-entangled |
| agent_logic | 0.854 | 8.6% | RNG-entangled |
| deepcopy | 0.847 | 8.5% | RNG-free bookkeeping |
| fmt_ts | 0.644 | 6.5% | RNG-free bookkeeping |
| trace_extraction | 0.640 | 6.4% | RNG-free bookkeeping |
| numpy_generic | 0.460 | 4.6% | RNG-free |
| parquet_write | 0.038 | 0.4% | RNG-free |
| **— raw RNG draw self-time** | **0.156** | **1.56%** | the actual draws |

**The single most consequential number in this whole phase: the RNG draws themselves are
~1% of wall-clock (1.04% s012, 1.56% as06).** ABIDES spends essentially no time *drawing*
random numbers; it spends its time on Python-object matching, message dispatch, and — above
all — turning every event into a formatted-timestamp log record and later parsing that back
into a DataFrame.

---

## 3. Phase decomposition — where the loop ends and bookkeeping begins (MEASURED, cumulative)

This is the decomposition that makes the GO/NO-GO decidable. Each marker is called once;
cumulative time = the whole subtree.

### `s012` (total 24.410 s)
| phase | cum s | % wall | what it is | RNG? |
|---|---:|---:|---|---|
| `simulate()` (whole) | 24.52 | 100% | the scored path | mixed |
| └ `abides.run`→`kernel.run` | 20.51 | 84.0% | sim + terminate | mixed |
| &nbsp;&nbsp;└ **`kernel.runner`** (event loop) | 15.06 | **61.7%** | THE sim loop: dispatch+match+agents+per-event logging | **entangled** |
| &nbsp;&nbsp;└ **`kernel.terminate`** | 5.45 | **22.3%** | post-loop | **RNG-free** |
| &nbsp;&nbsp;&nbsp;&nbsp;└ `get_time_dropout`/`analyse_order_book` | 5.13 | **21.0%** | pandas iterrows over the L2 book-log for a liquidity-dropout metric | **RNG-free** |
| └ `extract_trace` | 2.50 | 10.2% | log→trace.parquet DataFrame | RNG-free |
| └ `extract_message_trace` | 1.31 | 5.4% | log→message_trace.parquet | RNG-free |
| &nbsp;&nbsp;(within those: `parse_logs_df`) | 1.77 | 7.3% | un-nest per-agent logs | RNG-free |

### `as06` (total 9.967 s)
| phase | cum s | % wall | RNG? |
|---|---:|---:|---|
| `kernel.runner` (event loop) | 6.74 | **67.6%** | entangled |
| `kernel.terminate` → `get_time_dropout` | 1.58 / 1.40 | 15.8% / 14.0% | **RNG-free** |
| `extract_trace` + `extract_message_trace` | 1.01 + 0.59 | 10.2% + 5.9% | RNG-free |

**Read this carefully:** the event loop is 62–68% of wall, but a large fraction of *even that*
is RNG-free per-event logging (`logEvent`→`to_dict`→`fmt_ts`+deepcopy) baked into the loop.
And **22% (s012) / 16% (as06) is `terminate`** — a pure post-loop pandas metric
(`get_time_dropout`) that isn't even part of the scored `trace.parquet`. Plus ~15–18% trace
extraction. So **~35–40% of total wall-clock is RNG-free work that happens *around* the
matching/agent logic, not inside it.**

---

## 4. py-spy sampling cross-check (independent confirmation)

Leaf-frame (self-time proxy) shares from 15,887 samples of the in-container scored loop,
which independently reproduce the cProfile ranking:

| leaf frame (file:line) | py-spy self % | cProfile self % | component |
|---|---:|---:|---|
| `fmt_ts` [utils.py:78] | 10.7% | 6.6% | fmt_ts bookkeeping |
| pandas `convert`/`maybe_convert_platform`/list-of-dict→arrays | ~9% | (pandas_trace_io 18%) | trace extraction |
| `Order.__init__` / `__deepcopy__` / `total_quantity` [orders/price_level] | ~7% | (matching 12.9%) | matching engine |
| `_clip` [numpy _methods] | 3.4% | 2.7% | inside `get_latency` |
| `parse_logs_df` + `trace.py` listcomp | ~5% | 5.9% | trace extraction |
| `send_message` [exchange_agent:900] / `get_latency` [config:102] | ~3% | (kernel 11%) | kernel dispatch |
| `append_book_log2` [order_book:634] | 1.2% | — | book-log for terminate metric |

By component the py-spy leaf split is: pandas_trace_io ~26%, matching_engine ~17%, fmt_ts
~11%, kernel_dispatch ~10%, trace_extraction ~9%, agent_logic ~8%. **Same story as cProfile.**

> One sampling artifact worth stating: py-spy reported **0.00% of samples with an RNG draw
> anywhere on the stack.** That is NOT evidence RNG is absent — it is evidence the draws are
> so fast (sub-microsecond C calls) that a 250 Hz sampler essentially never lands inside one.
> It *reinforces* the cProfile finding that drawing randoms is ~1% of the cost. The
> entanglement is about *data dependency*, not *time spent drawing* (§5).

---

## 5. RNG-free vs RNG-entangled — classification of every hot component

The plan's crux. "RNG-free" here means the strict test the plan requires: **can this
component be re-implemented in Rust without changing which `np.random.RandomState` draw is
consumed, in what order, to produce what value — i.e. without perturbing the event sequence
or any fill timestamp beyond ±1 µs?** A component can be RNG-free in its own arithmetic yet
*entangled* if its inputs/outputs sit in the draw-ordering chain.

### (a) Matching engine / order-book insert-cancel-match — `abides_markets/order_book.py`
Hottest fns: `handle_limit_order` [order_book.py:75], `execute_order` [:194], `enter_order`
[:329], `cancel_order` [:408]; order objects `Order.to_dict/__str__/__deepcopy__`
[orders.py:82/129/153]; `price_level.total_quantity` [price_level.py:260]. **12.9% / 10.9%.**
- **Its arithmetic is RNG-free** — grep confirms *zero* `random_state`/`np.random` calls in
  the matching path (the one hit, order_book.py:960, is inside `pretty_print`, a debug method
  with `sigma_n=0`, never on the hot path). Price-time priority matching is deterministic.
- **BUT it is RNG-ENTANGLED by data dependency and by interleaving.** What matches against
  what depends entirely on the *order arrival sequence*, and that sequence is produced by
  agents' RNG draws (order size/side/price) delivered at RNG-drawn latencies. A Rust order
  book would have to be driven by the *same* interleaved stream, event-by-event, re-entering
  Python for every agent notification (`send_message(OrderAcceptedMsg/ExecutedMsg…)`) that
  in turn triggers the next agent draw. You cannot lift the matching engine out of the
  Python event loop without also lifting the agents (which draw) — the two are co-routined
  through the kernel queue. **Verdict: RNG-free code, RNG-entangled placement. Not safely
  portable in isolation.**

### (b) Kernel message queue / event dispatch / wakeup scheduling — `abides_core/kernel.py`
Hottest fns: `runner` [kernel.py:275] (the loop), `send_message` [kernel.py:528], the
`queue.PriorityQueue` `put`/`get`. **11.0% / 11.1%.**
- The queue operations and the dispatch branch logic are RNG-free.
- **BUT `send_message` computes `deliver_at = sent_time + int(latency)` where `latency =
  agent_latency_model.get_latency(sender, recipient)` — a per-message `RandomState.lognormal/
  uniform/pareto` draw** (`abides_fork/config.py:102`). The delivery time IS the
  PriorityQueue key, so **the RNG draw literally determines the global event ordering** that
  Tier-A grades (Kendall-τ, fill sequence, per-fill timestamp ±1 µs). This is the single most
  entangled hot component. A Rust kernel that owned the queue would own the point at which
  each latency draw is consumed; reproducing numpy `RandomState` lognormal/pareto bit-for-bit
  in Rust is exactly the highest-risk item the audit said OCELOT contributes nothing to.
  **Verdict: RNG-ENTANGLED. Off-limits for a drop-in Rust kernel under Tier-A.**

### (c) Agent stepping / decision logic — `abides_fork/agents.py` + `abides_markets/agents/*`
`ScheduledAgent.act/receive_message` [agents.py:63/145], `trading_agent.receive_message`
[:268], `exchange_agent.receive_message` [:308]. **7.2% / 8.6%.**
- **RNG-ENTANGLED, by construction.** `NoiseTrader.act` draws 3× per wakeup
  (`random_state.normal` size, `randint` buy/sell, `randint` offset — agents.py:111/115/116);
  `ValueTrader.act` draws via `oracle.observe_price(..., self.random_state, ...)`
  (a `normal`). (`MarketMaker` and `MomentumTrader.act` are individually RNG-free, but they
  interleave with the RNG agents through the shared queue, so their *timing* is entangled.)
  These draws are the ones that fix the Tier-A event multiset. **Must stay in numpy. Off-limits.**

### (d) numpy RNG draws — `mtrand` methods, `np.clip` around them
The draws themselves (`lognormal`, `normal`, `randint`, `uniform`, `pareto`, `exponential`)
= **1.04% / 1.56% of wall.** Plus `np.clip` in `get_latency` (~2.7%). **RNG by definition, and
cheap.** Porting these to Rust is both pointless (1% ceiling) and the exact thing that breaks
exactness. Off-limits.

### (e) Trace extraction / logging / parquet + the terminate metric — **THE RNG-FREE ZONE**
This is the one clean bucket, and it is large:
- `fmt_ts` [utils.py:78] — `pd.Timestamp(ns).strftime(...)` called **329,529×** on s012.
  **6.6% / 6.5%.** Invoked from `Order.to_dict` [orders.py:82] and `Order.__str__`
  [orders.py:129], which run inside `logEvent` [agent.py:144] on **every** ORDER_SUBMITTED/
  ACCEPTED/EXECUTED/CANCELLED. It converts an int-ns timestamp to a string that
  `parse_logs_df` later parses **back** to an int. Pure, wasteful, RNG-free bookkeeping.
- `parse_logs_df` [utils.py:120] + `abides_fork/trace.py` `extract_trace`/`extract_message_trace`
  + the pandas `Series/DataFrame` construction + `maybe_convert_objects` — the log→parquet
  materialization. **~18% + ~6%.** RNG-free; runs entirely after the loop.
- `deepcopy` of order objects for `logEvent` [copy.py:128] — **4.0% / 8.5%.** RNG-free.
- `get_time_dropout`/`analyse_order_book` [exchange_agent.py:909/904] at `kernel_terminating`
  — **21.0% / 14.0%**, pure pandas `iterrows` over the accumulated L2 `book_log2`
  (`append_book_log2` [order_book.py:634]) to compute a liquidity-dropout metric that **is
  not part of the scored `trace.parquet` at all.** RNG-free, post-loop, and arguably pure
  overhead for the scored path.

**Verdict for (e): genuinely RNG-free, no event-ordering dependency, safely portable /
elidable.** This is the only place a Rust (or even a pure-Python) optimization can touch
without risking Tier-A.

---

## 6. GO / NO-GO

### The plan's PRIMARY hypothesis is REJECTED (NO-GO as framed)
> "Replace ONLY the hottest, RNG-free inner machinery (matching engine / order-book ops /
> message dispatch) with a Rust module, keeping the numpy agents' draws in place → inherit
> Tier-A for free."

The profile says the hottest *inner* machinery — matching (13%), dispatch (11%), agent step
(8%) — is **not separable from the RNG stream**:
- The kernel queue's ordering key is a **per-message RNG latency draw** (§5b). Owning the
  loop in Rust means owning where numpy draws are consumed → the exact numpy-`RandomState`
  reproduction problem the audit flagged as OCELOT's zero-contribution, highest-risk item.
- The matching engine, though RNG-free in isolation, is **co-routined with the drawing agents
  through that queue** (§5a). Each fill sends a message that wakes an agent that draws. You
  cannot pull matching into Rust without either (i) pulling the agents too (they draw — breaks
  Tier-A), or (ii) crossing the Python/Rust boundary per event to let numpy agents draw —
  which adds FFI overhead per event and is very unlikely to beat in-process Python on a
  ~200k-event run, while adding enormous bit-exactness risk.

Trying to force Phase 2 on the matching engine or kernel would put the 65/65 Tier-A green
directly at risk for, at best, a fraction of a ~24% (matching) or ~11% (kernel) slice — and
realistically *negative* speedup once per-event FFI + numpy-draw-callback overhead is paid.
**This is exactly the "null is a finding" case the plan's Discipline section names.** Do not
force it.

### QUALIFIED GO — the one safe, measured target: the RNG-free trace/bookkeeping zone (§5e)
There IS a real, RNG-free, hot target — it just isn't the matching engine. It is the
**event-logging + trace-materialization + terminate-metric machinery**, which is provably
outside the draw-ordering chain:

| safe target | file:line | s012 % | as06 % | why safe |
|---|---|---:|---:|---|
| `fmt_ts` string-format churn | `abides_core/utils.py:78` (via `orders.py:82/129`, `agent.py:144`) | 6.6% | 6.5% | int-ns→str→int round-trip; RNG-free; result re-parsed |
| `get_time_dropout` terminate metric | `exchange_agent.py:909` + `append_book_log2` `order_book.py:634` | 21.0% | 14.0% | post-loop pandas metric NOT in scored trace |
| trace/message-trace extraction | `abides_fork/trace.py:104/233` + `parse_logs_df` `utils.py:120` | ~15% | ~16% | post-loop log→parquet; RNG-free |
| logEvent deepcopy | `copy.py:128` via `agent.logEvent` `agent.py:144` | 4.0% | 8.5% | bookkeeping copy; RNG-free |

**Amdahl ceilings (max achievable speedup, honest):**
- The RNG-free trace/bookkeeping zone totals **≈ 40% (s012) / ≈ 38% (as06)** of wall-clock.
  If a Rust module made *all* of it free, Amdahl caps end-to-end speedup at
  **1/(1−0.40) ≈ 1.67× (s012)** and **1/(1−0.38) ≈ 1.61× (as06)**. That is the ceiling for
  the whole safe zone combined, and it is an upper bound (Rust won't make it literally free).
- The **single cleanest, lowest-risk sub-target** is the `fmt_ts`/`to_dict` round-trip
  (6.6% of s012) — a pure int↔string reformatting that ABIDES does per event only to parse
  it back. Much of this can be *eliminated in Python alone* (store the int ns and skip the
  `strftime`, adjusting `parse_logs_df`/`extract_trace` to read the int) — no Rust required —
  for a ~6–7% win at essentially zero Tier-A risk (it changes only a log field's string
  representation, not any draw or ordering). Ceiling on fmt_ts alone: **≈ 1.07×.**
- The **largest single safe slice** is `get_time_dropout` (21% s012 / 14% as06). It computes
  a liquidity-dropout metric that is not in the scored `trace.parquet`; if the scored path
  does not need it, gating/removing it (or porting the `iterrows` to vectorized numpy / Rust)
  is the highest-value RNG-free win. **This needs a correctness check** that no downstream
  scored artifact consumes `metric_trackers` — flagged as the first Phase-2 task.

**Recommended target to port/optimize in Phase 2 (in priority order):**
1. **Elide/port the `get_time_dropout` + `append_book_log2` book-log metric** (21%/14%) —
   biggest RNG-free slice; first verify it's not scored, then vectorize-or-Rust or gate it.
2. **Kill the `fmt_ts` round-trip** (6.6%/6.5%) — store int-ns in the log, drop the
   `strftime`+re-parse. Pure Python change, ~1.07× alone, near-zero risk.
3. **Rust-accelerate `parse_logs_df`/trace extraction** (~15%) if 1–2 don't saturate.

Because these are RNG-free and *outside* the event loop, they inherit Tier-A trivially
(they never touch a draw or an ordering key) — which is the plan's original goal, achieved on
a different, safe surface. **Combined realistic ceiling ≈ 1.5–1.6×**, not the order-of-magnitude
a matching-engine port might have promised. Phase 2 should proceed **only** on §5e targets,
re-running `run_regression.py` (65/65 must stay green) after each change, and must **not**
touch the kernel queue, `get_latency`, the matching engine, or the agents.

### If §5e proves too small to matter → fall to the SECONDARY scope
Per the plan, if the safe ≈1.5–1.6× ceiling isn't worth the engineering, **re-scope to
Tier-B statistical families (2,4,5)** where OCELOT's own deterministic RNG suffices and
bit-exactness is not required — there a from-scratch Rust engine can own the whole loop
(including its own latency/agent draws) because Tier-B grades on KS≤0.08 / spread±10bps, not
on the exact numpy stream.

---

## 7. Hottest functions, with file:line (installed source, MEASURED)

Ranked by cProfile self-time on `s012` (the Tier-A unit); path prefix
`/usr/local/lib/python3.11/site-packages/` in the image, mirrored at `.bigtmp/abides/` locally.

1. `abides_core/utils.py:78` `fmt_ts` — 1.601 s (6.6%), 329,529 calls — timestamp→string. **RNG-free.**
2. `{pandas._libs.lib.maybe_convert_objects}` — 1.132 s (4.6%) — trace DataFrame build. **RNG-free.**
3. `abides_core/kernel.py:284` `runner` (self) — 0.802 s (3.3%) — event-loop overhead. entangled loop.
4. `abides_core/utils.py:120` `parse_logs_df` — 0.731 s (3.0%) — log un-nest. **RNG-free.**
5. `copy.py:128` `deepcopy` — 0.680 s (2.8%) — logEvent order copies. **RNG-free.**
6. `numpy/core/_methods.py:90` `_clip` — 0.669 s (2.7%) — inside `get_latency`. RNG-adjacent.
7. `{builtins.isinstance}` — 0.658 s (2.7%) — dispatch/pandas glue. RNG-free.
8. `abides_core/kernel.py:572` `send_message` (self) — 0.533 s (2.2%) — **calls `get_latency` (RNG). ENTANGLED.**
9. `abides_markets/agents/exchange_agent.py:308` `receive_message` — 0.399 s (1.6%) — dispatch. entangled.
10. `abides_markets/orders.py:129` `__str__` / `:82` `to_dict` — 0.278 s + 0.142 s — via logEvent. **RNG-free.**
11. `abides_markets/order_book.py:75` `handle_limit_order` — 0.211 s self / 2.785 s cum — matching. RNG-free arith, order-entangled.
12. `{RandomState.lognormal}` — 0.250 s (1.0%) — the actual per-message latency draw. **RNG.**

The end-of-run `abides_markets/agents/exchange_agent.py:915` `get_time_dropout` is 0.166 s
self but **5.125 s cumulative (21%)** — the single largest RNG-free reclaimable block.

---

## 8. Artifacts (left in place)
- `.bigtmp/track3/drafts_prof/profile_driver.py` — in-container cProfile driver.
- `.bigtmp/track3/drafts_prof/loop_run.py` — in-container py-spy loop target.
- `.bigtmp/track3/drafts_prof/native_run.py` — native (host-venv) runner + RNG-neutral date shim (documents the native path; not used for the numbers).
- `.bigtmp/track3/drafts_prof/analyze.py`, `phases.py`, `pyspy_agg.py` — the aggregators.
- `.bigtmp/track3/drafts_prof/out/{s012,as06}.{pstats,txt}` — raw cProfile output.
- `.bigtmp/track3/drafts_prof/out/s012_pyspy.speedscope.json` — 15,887-sample py-spy trace.
- One env change: `pip install coloredlogs py-spy` into `.bigtmp/t2venv` (host). Container
  gets `py-spy` at runtime only (not baked into the image).

## Phase 1 verdict (one line)
**NO-GO on porting the matching engine / kernel (RNG-entangled through the per-message
latency draw and the queue-coupled drawing agents); QUALIFIED GO on the RNG-free
trace/bookkeeping zone (fmt_ts round-trip + the post-loop `get_time_dropout` metric +
trace extraction, ≈40% of wall, Amdahl ceiling ≈1.6×) — proceed to Phase 2 on THAT target
only, or fall to Tier-B if ≈1.6× isn't worth it.**
