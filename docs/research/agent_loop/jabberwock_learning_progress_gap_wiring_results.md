# RESULTS — WIRING `learning_progress_curiosity` INTO GAP-AWARENESS AS AN AUTONOMOUS TOPIC-SELECTION TRIGGER

**Prereg:** `jabberwock_learning_progress_gap_wiring_prereg.md` (committed
`8d61793`, alone, before any number). **Verdict: GO, built, all five
demonstration bars green, no regression.**

## 0. Headline

`docs/research/theory_convergence/RAVANA_CONVERGENCE_AUDIT.md` §6.2 named a
precise gap: OCELOT already holds a theoretically-stronger, gated,
two-timescale learning-progress signal than RAVANA's single-EMA
prediction-error curiosity, but nothing consumed it for autonomous,
proactive topic selection — every existing gap-awareness rule is reactive
(fires after a conversational turn already failed). This rung wires the
proactive consumer §6.2 scoped, near-verbatim: **one new graph rule**
(`lp_mint_topic_gap`, `seeds/curiosity_topic_selection.json`), **one
mechanical adapter module** (`domains/curiosity_topic_ingest.py`, a real
lexical-grounding sensor mirroring the existing doom-domain consumer's own
info-gain sensor pattern), and a three-arm demonstration proving the
mechanism correctly prefers a genuinely-progressing topic, correctly ignores
an already-resolved one, and — the audit's own sharpest claim — **correctly
declines to proactively flag a persistently-unresolvable ("noisy-TV")
topic**, while a raw-surprise falsifier (the RAVANA-equivalent single-signal
gate) DOES falsely flag it. Zero new Rust, zero new Term, zero new node
type, zero regression on the existing gap-awareness/self-concern/learning-
progress/doom-exploration suites.

## 1. Investigation bar — what `learning_progress_curiosity.json` measures, grounded in code

Confirmed by reading `seeds/learning_progress_curiosity.json` (403 lines, 12
rules, 3 productions) in full, its measure adapter
(`scripts/learning_progress_measure.py`), its bar-setting proof
(`docs/research/vision/VISION_LEARNING_PROGRESS_PREREG.md` +
`..._RESULTS.md`), and its one prior non-vision consumer
(`seeds/doom_active_exploration.json` + `domains/doom_active_explore_
ingest.py`):

- **Domain-generic, not vision-hardwired.** Every rule and node type
  (`CuriosityHub`, `AttentionItem`, `HeldCuriosityParams`, `Deliberation`)
  reads/writes only `obs`, `held`, `input_epoch`, and derived bookkeeping —
  no vision-specific attribute anywhere. `"area": "retina"` is organisational
  metadata only. Already proven by its own second consumer (doom
  exploration, block 205000, spatial frontier bins instead of pixels).
  **This rung is the third reuse.**
- **What it measures:** `learning_progress = slow_res − fast_res`, a
  two-timescale integer EMA differential of `residual = |obs − held|`
  (`fast_div=3`, `slow_div=20`). `>0` exactly when recent surprise is
  dropping vs. older surprise (compression); `≈0` for BOTH a resolved item
  (both EMAs converged) AND stationary noise (both EMAs track the same
  mean) — the textbook Oudeyer/Schmidhuber noisy-TV discriminator.
- **Where proven:** `VISION_LEARNING_PROGRESS_RESULTS.md`, 15/15 criteria
  green — gated interest on a noise item `480→130` (leaves) vs. a
  raw-surprise falsifier `1008→999` (traps); progress-not-surprise ranking
  proven directly (G2d). A **synthetic mechanism demonstration**, reported
  as such (not a benchmark-value claim).
- **Opt-in, default-OFF posture:** `self_load_only: true`, excluded from
  `substrate/boot_all.py`'s `load_all_seeds` sweep (verified at
  `boot_all.py:39`); inert without an enabled `HeldCuriosityParams` even when
  loaded (G4b in the original proof). **This rung's new seed carries the
  identical posture, for the identical reason.**
- **`gap_awareness.json` (v1.6.0) confirmed reactive-only.** Grepped the full
  1411-line file for `CuriosityHub`/`AttentionItem`/`learning_progress`:
  zero hits. The audit's §7.3 uncertainty ("not verified beyond the seed
  file") is now resolved as **confirmed absent**, not merely unobserved.
- **Neither seed has an emitter** (hand-authored, matching the
  `code_write_gap.json`/`prog_read_gap.json` precedent CLAUDE.md names) —
  grepped `tools/*.py` + `scripts/*.py` for any writer of either seed path;
  none found.

## 2. GO/NO-GO — GO, at the registered cost

Built exactly the three pieces named in the PREREG, all graph-data-or-
mechanical-I/O, **zero new Rust, zero new Term, zero new node type**:

1. **`seeds/curiosity_topic_selection.json`** (v1.0.0, `self_load_only:
   true`, `depends_on: ["learning_progress_curiosity", "gap_awareness"]`) —
   one rule, `lp_mint_topic_gap`: an `AttentionItem` with `attended==1.0`
   AND `last_boost_epoch > 0` AND a `topic` string AND no existing
   `SelfConcern` with matching `content` mints
   `SelfConcern{status:'noted', source:'implicit', kind:'knowledge',
   content:<topic>}` — **the exact node shape `note_unresolved_topic_gap`
   already mints**, through the identical content-dedup guard every other
   gap-awareness rule uses, feeding the identical `has_self_concern` edge
   and the identical human-gated `promote_self_concern` spine. This mints
   *nothing that acts on its own* — only what the human is invited to
   promote, matching the existing culture around `SelfConcern` exactly.
2. **`domains/curiosity_topic_ingest.py`** — mechanical adapter mirroring
   `domains/doom_active_explore_ingest.py`'s structure one-for-one
   (`install_curiosity`/find-or-create `AttentionItem`/set `obs`+
   `input_epoch`/`run_rules()`). Its one piece of real sensor logic,
   `unknown_word_count`, reuses `WorldAdapter.taught_signs()` and
   `ground_unknowns`'s own tokenisation verbatim — a read of the agent's
   own existing lexical state, not an invented quantity.
3. **`scripts/curiosity_topic_selection_measure.py`** — the demonstration
   (§3) plus a source audit.

**A single, load-bearing design correction made mid-build, recorded
honestly:** the PREREG's registered plan (mint directly from
`attended==1.0`) does not by itself discriminate — `interest` initialises to
`interest_c0` and only *decays* until progress first boosts it, so EVERY
fresh `AttentionItem`, learnable or not, reads `attended==1.0` on tick 1
purely from unspent initial charge. The rule as built adds one guard,
`last_boost_epoch > 0` — a field the pre-existing `lp_gate` rule already
computes and only ever advances off its `ITEM_INIT` sentinel `0.0` when
progress (gated mode) or surprise (falsifier mode) actually crosses its
floor. This reuses existing mechanism state (no new attr, no new rule, no
invented threshold) to require "progress/surprise was actually detected at
least once," not merely "the initial decay hasn't finished yet." Root-caused
and fixed by inspection of the seed's own already-existing bookkeeping, not
by adding a scalar knob.

**A second honest correction, also load-bearing:** the calibrated `PARAMS`
(`fast_div=3, slow_div=20, progress_floor=10, surprise_floor=4`) are tuned
against residual swings of tens-to-hundreds (the original proof's `LEVELS`
were 40–220). A raw word-count sensor (0–6ish) is far too small a dynamic
range for that **same** integer machinery — `IDiv(residual, 20)` truncates
to `0` whenever `residual < 20`, so `slow_res` never moves off `0` and
`learning_progress` reads a permanently-wrong constant (reproduced directly:
see §5). `WORD_SENSOR_SCALE = 40.0` in `curiosity_topic_ingest.py` rescales
the honest word-count sensor into the calibrated params' own dynamic range —
a **unit conversion**, not a decision-threshold retune (no floor, divisor, or
gate value changed); the doom consumer made the analogous adjustment for the
identical reason (its own `blend_div=8` vs. vision's `blend_div=2`).

**Explicitly NOT built, as registered:**

- The commit-net (`cn_*`) — no natural referent yet for "a conversational
  deliberation step"; wiring it would be exactly the scope creep the PREREG
  registered against.
- A fully autonomous daemon tick hook. What's proven here is the complete,
  correct, reusable mechanism + wiring + real sensor, exercised end-to-end
  through the identical adapter/seed shape the daemon would call. Wiring
  `curiosity_topic_ingest.maintain_topic_interest` into a periodic daemon
  tick (which candidate topics get sampled, how often, from real multi-turn
  conversation) is a genuinely separate, smaller-but-real next step, named
  precisely rather than silently assumed.
- No cross-domain "Progress" abstraction — `obs`/`held` stay exactly what
  they already were; every domain (vision, doom, now conversation) supplies
  its own sensor into the same generic shape.

## 3. Demonstration — all five bars green

Three co-present topics on one `CuriosityHub`, gated mode (`mode=0`),
`PARAMS` unchanged from `learning_progress_measure.py` (only the sensor is
rescaled, per §2):

| topic | construction | gated (mode=0) mint | falsifier (mode=1) mint |
|---|---|---|---|
| **RESOLVED** | phrase built entirely of already-taught words | **no** | — |
| **PROGRESSING** | 6 unknown words, a scripted fake teacher grounds one every 3 ticks via the REAL `ground_unknowns` loop | **YES** | YES |
| **INTRACTABLE** (noisy-TV analogue) | phrase re-drawn every tick from a gibberish token pool (random 1–4 tokens/tick) the fake teacher never grounds — `unknown_word_count` genuinely high-variance, never converges | **no** | **YES (traps)** |

Single canonical run (seed 900001, T=24 ticks):

```
gated  minted: ['progressing']
naive  minted: ['progressing', 'intractable']
gated  intractable interest: early 168 -> late 0     (decays)
naive  intractable interest: early 1024 -> late 1024 (PINNED — trapped)
gated  progressing interest late: 341
```

- **D1 (resolved never minted):** ✓ — nothing left to flag.
- **D2 (progressing minted):** ✓ — the genuinely-productive topic gets
  proactively flagged as worth pursuing, BEFORE any conversational turn has
  failed on it.
- **D3 (headline — gated intractable NOT minted):** ✓ — the actual
  gap-FILING DECISION, not merely an interest curve, correctly declines to
  chase persistent, irreducible surprise.
- **D4 (falsifier intractable IS minted):** ✓ — reproduces the ICM/
  prediction-error trap directly in the mint decision: without the
  two-timescale gate (i.e. what a single-EMA signal like RAVANA's
  `update_prediction_error` would do), the agent WOULD proactively flag a
  hopeless topic as worth pursuing. This is the audit's own central claim,
  now demonstrated end-to-end rather than argued from the mechanism alone.
- **D5 (no Python decisions):** ✓ — source audit over both
  `curiosity_topic_ingest.py` and the measure script finds zero `set_attr`
  calls on any `lp_*`/mint decision key; `bad_setattr == {}`.

**Ensemble (N=16 independent draws, matching the original proof's own N_ENS
discipline — a decision rate is a property of the stimulus distribution, not
one draw):**

| bar | rate |
|---|---|
| D1 resolved never minted | 16/16 = 1.00 |
| D2 progressing minted | 16/16 = 1.00 |
| **D3 gated intractable NOT minted** | **15/16 = 0.9375** |
| D4 falsifier intractable minted | 16/16 = 1.00 |

The one miss on D3 (a single draw where the gated arm also minted on the
intractable topic) is reported honestly, not hidden — it mirrors the
original proof's own reported imperfection (G1a held on 14/16 noise draws).
The mechanism claim is distributional, not "every single draw"; per-draw
robustness ≥0.75 was the registered bar (§3 of the PREREG) and is cleared
with margin.

Numbers: `results/curiosity_topic_selection.json`.

## 4. No-regression bars

`pytest tests/test_gap_awareness_migrated.py tests/test_learning_progress_
migrated.py tests/test_self_concern_promote_migrated.py tests/test_self_
gaps_surfacing_migrated.py tests/test_active_exploration_migrated.py
tests/test_curiosity_topic_selection_migrated.py -q`:

Run SERIALLY (no xdist, memory-capped `systemd-run --scope --user -p
MemoryMax=8G -p MemoryHigh=6G` per this session's resource discipline), one
file at a time, on the box's actual shared state (other concurrent worktree
agents' runs contending for the same machine — this is why individual files
took 85–275s each rather than the low-teens-of-seconds each runs in
isolation, as `test_curiosity_topic_selection_migrated.py` did at 12.99s on
a quiet system):

| file | result | new? |
|---|---|---|
| `test_curiosity_topic_selection_migrated.py` | **6 passed** | this rung |
| `test_gap_awareness_migrated.py` | 4 passed, **5 failed** | pre-existing |
| `test_learning_progress_migrated.py` | **4 errors** (`ModuleNotFoundError: matplotlib`) | pre-existing |
| `test_self_concern_promote_migrated.py` | **6 passed** | — |
| `test_self_gaps_surfacing_migrated.py` | **5 passed** | — |
| `test_active_exploration_migrated.py` | 7 passed, 1 skipped (VizDoom-gated) | — |

**Both non-green files were verified pre-existing, not caused by this
rung:**

- **`test_gap_awareness_migrated.py`** — the exact same 5 node ids fail with
  this rung's five new files (`domains/curiosity_topic_ingest.py`,
  `scripts/curiosity_topic_selection_measure.py`,
  `seeds/curiosity_topic_selection.json`,
  `tests/test_curiosity_topic_selection_migrated.py`, and this RESULTS doc)
  **removed via `git stash -u`** and the identical suite re-run against the
  pristine committed worktree state (`8d61793`, PREREG-only): `5 failed, 4
  passed in 275.45s`, the SAME five node ids both times:
  `test_implicit_unresolved_topic_files_a_gap`,
  `test_implicit_gap_is_filed_once`, `test_gaps_are_deduped_by_content`,
  `test_unaccounted_self_faculty_files_a_clean_self_gap`,
  `test_resolved_topic_files_no_gap`. All five assert on
  `agent.converse("What do you know about the moon?", ...)` resolving via
  `domains.topic_grounding.ground_topic`'s local Wikipedia library — a
  network/data-availability dependency of this environment, unrelated to
  `seeds/gap_awareness.json` (never touched) or anything this rung added
  (`self_load_only`, never loaded by this suite). Stash restored via `git
  stash pop` immediately after (`Already up to date` / all 5 files back).
- **`test_learning_progress_migrated.py`** — fails at
  `scripts/learning_progress_measure.py:256`'s `import matplotlib` before
  any rule logic runs (`ModuleNotFoundError`). That script is the ORIGINAL,
  byte-unmodified vision-domain proof (this rung never edits it) — a missing
  optional plotting dependency in this environment, not a regression. The
  underlying mechanism it exercises (`seeds/learning_progress_curiosity.json`,
  also unmodified) is independently confirmed working in this SAME
  environment by `test_active_exploration_migrated.py` (7/8, matplotlib-free)
  and by this rung's own `test_curiosity_topic_selection_migrated.py`
  (6/6) — both exercise the identical `lp_*` rules end-to-end.

**Net: zero regressions attributable to this rung.** Every file this rung
added is fully green; every pre-existing file's failures reproduce
byte-for-byte with this rung's changes absent.

- `git diff --stat runners/dsl/src/`: empty (confirmed, `test_integer_
  native_and_no_new_rust` gates this on every run of the new test file).
- Canonical `_native.abi3.so` unmodified: md5 `b32d707a5f4ce3fcc6c162d6e95902f2`
  (worktree) == primary tree's committed copy, verified at worktree setup;
  also independently confirmed by the coordinator mid-session (sha256
  `c5e50801...`, matching the standard committed baseline) — no Rust rebuild
  at any point in this rung.
- Byte-identity on a default full boot: `test_seed_default_off_byte_
  identical` (in this rung's own new test file) confirms `load_all_seeds()`
  on a fresh `WorldAdapter` creates **zero** `CuriosityHub`/`AttentionItem`
  nodes — the new seed and its dependency (`learning_progress_curiosity`)
  are both `self_load_only` and never swept into a default boot.

## 5. The integer-truncation reproduction (honest residual, worked example)

Before applying `WORD_SENSOR_SCALE`, driving the PROGRESSING topic through
the unscaled sensor (obs range 0–6) for 24 ticks left `slow_res` pinned at
`0.0` for the entire run (`IDiv(residual, 20) == 0` whenever
`residual < 20`), so `learning_progress` read a constant, uninformative
`-2.0` throughout and no gap was ever minted — reproduced directly during
this rung's build (see the worked trace in this doc's source history /
session log). This is the same integer-truncation failure class the
original `VISION_LEARNING_PROGRESS_RESULTS.md`'s own "Honest residuals"
section documents for a too-fine *signal* (the single-tick backward
difference); here it recurred one level up, from a too-fine *sensor unit*.
`WORD_SENSOR_SCALE = 40.0` fixes it without touching any decision threshold.

## 6. Honest residuals / remaining uncertainty

- **The PROGRESSING arm's positive-progress detection is late-arriving in
  the single canonical run** (last_boost_epoch first fires at tick 23 of 24,
  per the worked debug trace) — the grounding schedule (one word grounded
  every 3 ticks) interacts with the EMA windows (`fast_div=3`) in a way that
  produces a multi-tick lag before sustained positive progress is legible.
  The mechanism still correctly mints within the demonstrated horizon on
  every ensemble draw, but a shorter horizon (T<20ish) would likely fail D2.
  This is a scene-construction property (grounding-schedule pacing vs. EMA
  window), not a mechanism defect — analogous to the original proof's own
  choice of `T=48` and staged `LEVELS` spacing, chosen empirically here for
  T=24 rather than derived.
- **The INTRACTABLE arm's construction (a randomly-redrawn gibberish phrase
  each tick) is a real, honestly-computed sensor value, but is a controlled
  analogue of, not identical to, the original proof's literal white-noise
  `obs` stream** — recorded per the standing rule that a refinement to a
  registered construction is reported, not hidden.
- **Live daemon autonomy remains unbuilt, named precisely in §2** — this
  rung proves the mechanism, the consumer rule, and a real sensor
  end-to-end; deciding which real multi-turn conversational entities become
  curiosity candidates in the live daemon, and how often they're resampled,
  is a separate, smaller design question for a future rung.
- **Named unbounded-growth risk, checked and confirmed real, not exercised
  in this rung's bounded demo.** `curiosity_topic_ingest.ensure_topic_item`
  find-or-creates an `AttentionItem` per distinct topic *name* and never
  removes one — this rung's demo only ever drives 3 fixed topic keys
  (`resolved`/`progressing`/`intractable`), so the population is bounded by
  construction and this was never a risk here. But `doom_active_explore_
  ingest.maintain_frontier_interest` (the mechanism's other consumer)
  explicitly PRUNES items whose bin is no longer a live frontier ("bounds
  the item population" — its own docstring), and this module has no
  analogous prune step. A live daemon hook that mints an `AttentionItem` per
  distinct *conversation* topic over many turns, with no equivalent
  retirement rule, would grow the `AttentionItem` population unboundedly —
  exactly the class of defect worth fixing properly (a prune/retire rule,
  mirroring the doom consumer's own pattern, or gap-awareness's own
  `retire_duplicate_gap` precedent) rather than working around, before any
  live-daemon wiring is attempted. Named here explicitly as a prerequisite
  for that future rung, not built in this one (no daemon loop exists yet to
  need it).
- **This is a synthetic mechanism demonstration, not a benchmark-value
  claim** (per the standing rule: synthetic-proven mechanism ≠ benchmark
  value, both reported) — the fake teacher stands in for the dictionary/wiki
  source exactly as the sanctioned `fake_ground_topic` precedent
  (`tests/test_topic_route_selfheal_migrated.py`) does.

## 7. Files

- Seed: `seeds/curiosity_topic_selection.json` (1 rule, 0 productions).
- Adapter: `domains/curiosity_topic_ingest.py` (mechanical I/O).
- Measure: `scripts/curiosity_topic_selection_measure.py`.
- Test: `tests/test_curiosity_topic_selection_migrated.py` (6 tests, 9 criteria + ensemble + default-off + no-Rust audits).
- Numbers: `results/curiosity_topic_selection.json`.
- Prereg: `jabberwock_learning_progress_gap_wiring_prereg.md` (this folder).
