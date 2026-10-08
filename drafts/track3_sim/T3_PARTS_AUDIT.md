# Track 3 (Simulation) — OCELOT Parts Audit

**Task audited against `.bigtmp/track3`.** Goal: build a FASTER discrete-event
market simulator that reproduces ABIDES's traces (Tier A EXACT, Tier B
statistical), shipped as a Docker image with a `simulate` verb, ranked by
`events_per_sec` on a sealed scenario. Single failure = inadmissible.

Verdict tags: **EXISTS** (reuse as-is) / **PARTIAL** (adapt) / **ABSENT** (build new).
Every claim is grounded in a real `file:line`.

---

## 1. Discrete-event / reflex / tick kernel — **PARTIAL (nothing reusable as a DES kernel)**

CLAUDE.md advertises a "Reflex loop: stimulus → response, tick scheduling" and
`fire_reflexes`. The actual Rust shows this is **NOT a time-ordered
discrete-event engine**. What exists:

- **`run_rules` is a monotone fixpoint, not an event loop.** `rewrite.rs`
  (`RewriteRule`, the applier, the fixed-point runner — `runners/dsl/src/rewrite.rs:1-20`
  header, rule struct `:330-480`) runs a backtracking subgraph matcher to a
  fixpoint, dirty-tracked by read/write sets (`derive_access`,
  `runners/dsl/src/rewrite.rs:487-540`). There is **no simulated clock, no
  scheduled-wakeup queue, no time-ordered dispatch**. Rules re-fire until the
  graph stops changing; ordering is by rule `order` (reflex→deep continuum,
  `rewrite.rs:353-354`) and dirty bits, NOT by an event timestamp. A market
  kernel needs "process the earliest-timestamped message next"; this engine
  has no such notion.

- **Reflex dispatch is a linear scan, not a priority queue.**
  `reflex_runtime.rs` fires order-0 reflexes: `fire_autonomous`
  (`runners/dsl/src/reflex_runtime.rs:69`) and `next_ready`/`dispatch_next`
  (`:116`, `:126`) iterate a `Vec<NodeID>` of Reflex nodes in order, checking a
  refractory window against the agent's integer `tick` attr
  (`reflex_runtime.rs:150-165`). The "clock" is a single monotonically-bumped
  `tick` integer on the Agent node — a tick counter, not an event calendar.
  There is no "advance simulated time to the next scheduled event."

- **The closest thing to a priority-ordered event queue is the L2 EDF
  scheduler** (`runners/dsl/src/l2_dispatch.rs`), which DOES use a
  `BinaryHeap` ordered by earliest deadline (`l2_dispatch.rs:31-34`, `:58`)
  with a `Task { deadline: Instant, ... }` (`:81-84`). **But it is a REAL-TIME
  OS-thread work dispatcher keyed on wall-clock `Instant`** (`Task::in_micros`
  builds `Instant::now() + offset`, `l2_dispatch.rs:97-101`), pinned to physical
  cores, for hard-realtime reflexes. It is explicitly "not integrated with
  run_rules" (`l2_dispatch.rs:47-54`, deferred followups). A DES kernel needs a
  heap keyed on *simulated* time (`t_ns:int64`) advancing to the next event
  regardless of wall clock — the OPPOSITE of EDF's "complete by wall-clock
  deadline T." The `BinaryHeap<Reverse<...>>` *pattern* is reusable (10 lines),
  but the scheduler itself is not.

- **The Bellman flood in quanta-navigation is a graph relaxation fixpoint, not
  an ordered event queue** (`seeds/quanta_navigation.json:8`, `:18-20`
  `qf_seed_goal`, `:311` `qf_seed_frontier`): `qf_relax` propagates distances to
  a fixpoint over portals — no min-priority extraction, no event time.

**Mapping to Track 3:** ABSENT as a reusable DES kernel. The core loop of a
market simulator — a priority queue keyed on message-arrival time, "pop earliest
event, dispatch to agent/exchange, agent schedules future wakeups" — **must be
built new**. The `BinaryHeap`/`Reverse` idiom from `l2_dispatch.rs:57-58` is a
trivial template but carries none of the DES semantics.

---

## 2. Rust + PyO3 build/ship toolchain — **EXISTS (the strongest asset; reuse wholesale)**

This is the KNOWN, PROVEN asset and it is fully reusable.

- **maturin abi3 wheel path is real and measured.**
  `runners/dsl/Cargo.toml:8-10` sets `crate-type = ["cdylib", "rlib"]`;
  `Cargo.toml:12` uses `pyo3 = { version = "0.22", features =
  ["extension-module", "abi3-py39"] }`. One wheel
  (`substrate_rs-*-cp39-abi3-*.whl`, ~4.3 MB) runs on any CPython ≥3.9.

- **The whole Docker ship path already exists and was proven for Track 2.**
  `drafts/seldon_t2_text/docker/Dockerfile` and `docker/build.sh` build the
  abi3 wheel *outside* the image (`build.sh:35-39`, `maturin build --release`)
  and `COPY + pip install` it (`Dockerfile:82-84`), keeping the Rust toolchain
  out of the final image. Build time is MEASURED: LTO=fat + codegen-units=1
  "MEASURED at 2m41s on this machine" (`Dockerfile:34-38`). The Track 3
  `simulate` verb maps 1:1 onto Track 2's `forecast` launcher pattern (a bare
  script on PATH, no ENTRYPOINT — `Dockerfile:88-91`, `build.sh` app assembly
  `:47-60`). Swapping `forecast`→`simulate` and the arg contract is a
  half-day port, not a build-out.

- **`py.rs` is the one-line-handoff binding surface.**
  `runners/dsl/src/py.rs:1-20` documents the "one big Substrate PyClass, Term
  factories emit JSON" strategy; the file is 12,834 lines of thin PyO3 method
  bindings. A NEW Rust module (a market matching engine) can be added to the
  SAME `substrate_rs` crate and exposed via a handful of `#[pymethods]` in
  `py.rs`, reusing the identical build → wheel → Docker path. Seed-loading of
  Reflex/Rule subgraphs is already wired (`py.rs:1738-1751`).

- **Build constraints are documented.** `.cargo/config.toml:29` caps `jobs = 4`
  (30 GB RAM, swap-heavy, OOM at exit 137 with full parallelism); release
  profile is `lto="fat", codegen-units=1, opt-level=3` (`Cargo.toml` profile).
  Note the release build is slow (2m41s) — for a matching-engine dev loop,
  `maturin develop` (debug) is faster; ship the release wheel.

**Mapping to Track 3:** **EXISTS.** This is the reuse-first win. A new
`market_engine.rs` in the crate + a few `py.rs` handoffs + a `simulate`
launcher on the Track-2 Docker skeleton = the entire ship path, already proven.

---

## 3. Matching engine / order-book / priority-queue primitives — **ABSENT (LOB) / PARTIAL (pieces)**

No limit-order-book exists. The reusable *pieces* are thin.

- **No LOB, no price-time-priority match anywhere.** The only "exchange/market"
  code is the **bigville barter economy** — co-located buy + credit, emergent
  scarcity pricing — NOT an order book. `bigville_econ_exchange`'s `be_exchange`
  rule fires when a buyer and shopkeeper share a cell (`docs/research/bigville/
  BIGVILLE_ECON_PREREG.md:40-42`, `:70-74`); prices emerge from supply/demand
  imbalance rules `pr_scarce_raise`/`pr_glut_lower` (`BIGVILLE_DESIGN_REFERENCE.md:407`).
  This is agent-based economics on the rule-fixpoint, with **no bid/ask book, no
  price-time priority, no fill matching** — the wrong data structure for
  reproducing ABIDES order matching.

- **Sorted/heap structures exist but are incidental.** `BinaryHeap`+`Reverse`
  in `l2_dispatch.rs:57-58` (EDF, §1). `BTreeMap` used for event-column
  reduction in `cognitive_tasks.rs:772-773`, `:925-926` (sorting azimuth
  columns — not order-book price levels). None is a book. A LOB wants
  price→FIFO-queue maps (typically `BTreeMap<Price, VecDeque<Order>>` per side);
  that must be written.

- **Integer-tick numeric handling is GENUINELY favorable.** CLAUDE.md's
  load-bearing invariant "**In-frame is INTEGER**" — `shape_decode.rs::coord_ints`
  returns `None` on Float slots by design (CLAUDE.md §"BASE-AS-DIMENSION",
  ~line 520+), and space_quantize boxes use integer `lo`/`hi` bounds
  (`runners/dsl/src/space_quantize.rs:31-33`). Track 3's trace is
  integer-priced (`price:int64`, `size:int64`, `t_ns:int64`). The tree's
  entire ethos ("non-integer math is CROSS-FRAME, never IN-frame") aligns
  perfectly with an integer-tick LOB — this is a cultural/design fit, not
  reusable code, but it de-risks the numeric design.

**Mapping to Track 3:** the **LOB matching engine must be built new.** OCELOT
offers integer-tick design alignment and the `BinaryHeap`/`BTreeMap` idioms, but
zero LOB code. This is one of the two genuinely-new build items.

---

## 4. Deterministic RNG / replay — **ABSENT (numpy-RandomState-compatible) — this is the Tier-A crux**

- **No `rand` crate; only hand-rolled xorshift/LCG.** `runners/dsl/Cargo.toml`
  has NO random-number dependency (confirmed: no `rand`, `rand_chacha`,
  `rand_xoshiro`). Every "RNG" in the crate is a bespoke deterministic
  xorshift64* or LCG for a *local* purpose: `apc.rs:112-118`
  (`rng ^= rng<<13; ...`), `gpu_me.rs:597-603`, `audio_primitives.rs:607-615`
  and `:923-927` (LCG seeded from patch centres). These are reproducible
  *within Rust* but **produce a completely different bit-stream from numpy's
  `np.random.RandomState`** (Mersenne-Twister MT19937 with numpy's specific
  Gaussian/exponential/uniform transforms).

- **Determinism/replay culture is strong, but it is graph-parity, not
  RNG-stream parity.** The tree gates on parity fixtures and seeded runs, but
  "seed" there means graph-construction seeds and deterministic fixpoint
  ordering — NOT reproducing an external PRNG's numeric draw sequence.

- **numpy `RandomState` is used only in Python analysis scripts**, never in the
  engine: `scripts/investigation_runners.py:123` (`np.random.RandomState(0)`),
  and `default_rng` in several `jabberwock_*` scripts. These are host-side
  data-splitting utilities, not a reimplementation of the MT19937 stream in
  Rust.

**Mapping to Track 3 — the honest crux:** Tier A ("same multiset of events,
exact fill sequence, Kendall-tau ≥ 0.999, ~1µs timestamp tolerance",
`.bigtmp/track3/qfbench2_track_simulation/semantics.py:265` `check_tier_a`,
exact row-count + fill-count equality `:288-300`) requires the fast engine to
reproduce ABIDES's background agents' draws **bit-for-bit**. ABIDES agents draw
from `np.random.RandomState` (MT19937). To match Tier A from a Rust engine you
must **reimplement MT19937 AND numpy's exact distribution transforms**
(`standard_normal` via numpy's ziggurat/Box-Muller variant, `exponential`,
`randint`, `permutation`, `choice`) so the k-th draw is identical. This is
**ABSENT and is the single hardest, highest-risk build item.** It is doable
(MT19937 is well-specified; numpy's transforms are open source) but it is exact,
unforgiving reverse-engineering: any divergence in draw order, discard behavior,
or transform reorders the entire event stream and fails the exact multiset/fill
gate. Event *ordering* (deterministic tie-breaks in the message/latency model,
`baselines/abides_fork/config.py`) must also match exactly.

---

## 5. Existing simulation / world-adapter experiments — **PARTIAL (agent-sims exist; none is a market DES)**

Substantial simulation infrastructure exists, but none is a discrete-event
market simulator and none reproduces an external engine's trace.

- **Bigville is a large agent-based town/economy sim on the rule-fixpoint.**
  Economy modules: `bigville_econ_exchange` (`be_exchange`/`be_credit`),
  `bigville_econ_production`, `bigville_econ_supply`, `bigville_econ_debt`,
  `bigville_prices` (emergent scarcity), `bigville_labour`, `bigville_econloop`
  (closed supply+price+labour loop), `bigville_fin_bank`
  (`docs/research/bigville/BIGVILLE_DESIGN_REFERENCE.md:407-415`). Adapter
  `worlds/bigville_econ_world.py` "only ingests, arms a one-shot flag, ticks the
  Rust run_rules fixpoint, and reads state" (`BIGVILLE_ECON_RESULTS.md:7-9`).
  This proves OCELOT can run a many-agent economic simulation — but it is
  **tick-fixpoint barter with emergent prices, not a timestamped order-matching
  DES**, and it does not target trace reproduction. Reusable as evidence of
  "multi-agent economy works"; NOT reusable as a market kernel.

- **LangSim is a trade-decision sim** (`worlds/langsim_world.py:1-11`,
  `:175-178`): N agents on a ring, trade mediated by utterances,
  `TradeDecision` nodes — again agent-decision-on-fixpoint, not order matching.

- **Real-world DES-shaped loops exist as tick loops, not event calendars.**
  Doom (`domains/doom_pattern_eye.py`, timed in `scripts/doom_realtime_ceiling_measure.py`),
  Conway (`domains_rs/conway.py`), the F-16/walker sims — all are fixed-tick
  step loops (`substrate.tick()` per frame), NOT next-event-time schedulers.
  Their step drivers are not reusable as an event calendar.

- **No ABIDES mention anywhere in OCELOT** (only in `.bigtmp/track3`, the task
  spec). No prior market-microstructure work.

**Mapping to Track 3:** PARTIAL. Bigville proves the multi-agent-economy pattern
and the ingest→tick→read adapter shape (directly reusable as the `simulate`
adapter skeleton). But no existing sim is event-driven-by-timestamp or
trace-reproducing; the DES kernel + LOB are net-new.

---

## 6. Throughput / profiling / bench harness — **EXISTS (measurement culture; adaptable) / PARTIAL (Rust bench)**

- **Strong Python throughput-measurement culture, directly reusable for
  `events_per_sec`.** The tree already benches the Rust substrate in
  events/sec-style units: `scripts/ask_jabberwock_about_perf_next.py:8-12`
  reports "Bench 1 graph mutations 1.25×", "Bench 2b WorkStealing 6.07 M/s",
  "Bench 3b 4-dim Kalman 8.5×" — i.e. there is a PREREG-then-measure bench
  program producing M-ops/sec numbers. `time.perf_counter()` micro-timing
  harnesses are everywhere (`scripts/doom_realtime_ceiling_measure.py:118-141`,
  `scripts/bench_pframe_gpu_me.py:165-171`, `scripts/g5_responsiveness_sweep.py:135-142`).
  A Track-3 `events_per_sec` timer is a trivial adaptation of this idiom.

- **No `criterion` / `cargo bench`.** `Cargo.toml` has no `[dev-dependencies]`
  criterion and no `[[bench]]` targets; Rust perf is measured from Python via
  the wheel + `time.perf_counter`, or via Rust `#[test]`s with
  `std::time::Instant`. So Rust-native micro-benchmarking of the matching engine
  would need criterion added (cheap) OR reuse the existing Python-over-wheel
  timing pattern (zero new deps, consistent with the tree).

**Mapping to Track 3:** EXISTS for the `events_per_sec` speed-rank measurement
(reuse the `time.perf_counter` + PREREG/RESULTS pattern). PARTIAL for
Rust-native bench (add criterion if wanted; not required).

---

## REUSE-vs-BUILD verdict

### Genuinely REUSABLE (reuse-first wins)
1. **The entire PyO3 / maturin abi3 / Docker ship path** (§2) — proven for
   Track 2 in `drafts/seldon_t2_text/docker/`, measured (2m41s release build,
   ~4.3 MB wheel). A new `market_engine.rs` in the same `substrate_rs` crate,
   exposed via `py.rs` one-line handoffs, ships on the identical
   `build.sh`→`Dockerfile` skeleton with `forecast`→`simulate`. **This is the
   biggest lever and it is already done.**
2. **The integer-tick design invariant** (§3) — CLAUDE.md's "in-frame is
   INTEGER" ethos aligns exactly with `price/size/t_ns:int64`; de-risks the LOB
   numeric design (culture, not code).
3. **The throughput-measurement harness pattern** (§6) — `time.perf_counter`
   over the wheel, PREREG/RESULTS discipline, existing M-ops/sec benches → the
   `events_per_sec` speed-rank timer.
4. **The ingest→tick→read world-adapter skeleton** (§5, bigville_econ_world.py)
   — the `simulate` verb's scenario.json → run → trace.parquet adapter reuses
   this shape.
5. **Trivial idioms**: `BinaryHeap<Reverse<..>>` (§1), `BTreeMap` price-level
   maps (§3) — templates, not implementations.

### Must be BUILT NEW
1. **The discrete-event kernel** (§1) — a simulated-time event calendar
   (min-heap on `t_ns`, pop-earliest, dispatch, agents schedule future
   wakeups). OCELOT's `run_rules` fixpoint and reflex scan do NOT provide this;
   the EDF heap is wall-clock, not sim-time.
2. **The LOB matching engine** (§3) — price-time-priority book, fills, cancels.
   Zero LOB code exists.
3. **numpy-`RandomState`-exact RNG** (§4) — MT19937 + numpy's exact distribution
   transforms, reproducing the k-th draw bit-for-bit. **The Tier-A crux.**

### Brutally honest scope recommendation

**A from-scratch fast engine that passes Tier A EXACT is HIGH-RISK, and OCELOT's
parts do NOT reduce the risk of the two hardest items (the LOB and the
numpy-RNG-exact reproduction) — it only reduces the ship-path and
measurement cost.** The reusable assets (Docker/wheel path, integer-tick
alignment, bench harness) are all *peripheral* to the two things that actually
decide Tier A admissibility. The crux items are net-new and unforgiving:

- Tier A demands EXACT row-count, EXACT fill sequence, Kendall-tau ≥ 0.999
  (`semantics.py:265`, `:288-300`). A single mis-ordered `RandomState` draw or a
  latency-model tie-break that differs from `abides-core` cascades into a total
  ordering failure → inadmissible.
- Nothing in OCELOT reproduces an external PRNG stream (§4); the engine has no
  MT19937 and no numpy-transform code. That reimplementation is the dominant
  risk and effort, independent of any OCELOT reuse.

**Recommended scope, in priority order:**

1. **PRIMARY (best expected value): accelerate ABIDES's actual hot loop
   in-place, profile-guided, behind the PROVEN PyO3 path — do NOT replace the
   engine for Tier A.** Profile `baselines/abides_fork` (kernel event loop +
   `abides-markets` order book) to find the hot loop; lift THAT into a
   `market_engine.rs` in the `substrate_rs` crate, keeping ABIDES's Python
   agents (and therefore their `np.random.RandomState` draws) UNCHANGED. This
   sidesteps the RNG-exact crux entirely — the draws still come from real numpy
   — while capturing the speed rank via a native matching engine / event queue.
   This is the scope OCELOT's parts genuinely support: the ship path (§2) and
   bench harness (§6) are exactly what a "drop a Rust hot-loop into the crate and
   wheel it" plan needs, and it inherits Tier-A exactness for free because the
   stochastic surface is untouched.

2. **SECONDARY (if a full rewrite is pursued): scope it to Tier B statistical
   families (2,4,5) first.** Tier B only needs return-KS ≤ 0.08 and spread
   ±10 bps — a Rust engine with its OWN deterministic RNG (any xorshift, §4) can
   plausibly hit those distributional targets WITHOUT reproducing numpy's exact
   stream. This is where a from-scratch fast engine is realistic. Attempt Tier A
   only after Tier B is admissible and the LOB + kernel are proven correct.

3. **AVOID as an opening move: a from-scratch engine aiming directly at Tier A
   EXACT.** The numpy-`RandomState`-exact reproduction (§4) is a multi-week,
   error-prone reverse-engineering task that OCELOT contributes nothing toward,
   and one bit of divergence fails the gate. Do this last, if at all.

**The localising finding:** the LOB and the sim-time event kernel are ABSENT,
the numpy-RNG-exact stream is ABSENT and is the Tier-A crux, and OCELOT's real
contribution is the *packaging* (proven PyO3/maturin/Docker ship path +
integer-tick design fit + bench culture), not the *engine internals*. Therefore
the OCELOT-supported path is **"accelerate ABIDES's hot loop as a Rust module in
the existing crate/wheel/Docker pipeline, keeping numpy agents in place"** for
Tier A, and **"a from-scratch Rust engine targeting Tier B statistical
families"** as the only realistic full-rewrite scope. A from-scratch Tier-A-EXACT
engine is not what OCELOT's parts support.
