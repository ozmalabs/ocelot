# RESULTS — ACTIVE CURIOSITY-DRIVEN DOOM EXPLORATION (block 205000)

Prereg: `VISION_ACTIVE_EXPLORATION_PREREG.md` (committed ALONE first, hash in the log).
Seed block: `205000–205999` (CLEAN per `scripts/seed_claim.py`). Setting: the DECLARED
PRIMARY controlled-motor active exploration on REAL E1M1 geometry.

## Headline

The perception→DECISION→ACTION loop is CLOSED and graph-native: the eye reveals what is
in view (unknown = ABSENCE), the belief map accumulates + `space_quantize` decodes FRONTIER
boxes, and **the graph CHOOSES the next cardinal step** — frontier-seeking + learning-
progress curiosity + a commit-net, every where-to-go decision a RULE/net. On real E1M1
(3297 walkable cells), over a fixed 300-action budget (canonical run,
`results/doom_active_explore/gates.json`):

| arm | final coverage (cells) | % of walkable | vs random | vs passive |
|---|---|---|---|---|
| **curiosity (frontier + LP + commit)** | **1295** | **39.3%** | **2.55×** | **16.0×** |
| nearest-frontier (reference, LP off, commit off) | 1254 | 38.0% | 2.47× | 15.5× |
| random-motor (mean of 5, seeds 205000–4) | 507.8 ± 99.7 | 15.4% | 1.0× | — |
| passive (no-move) | 81 | 2.5% | — | 1.0× |

**G1 PASS.** The curiosity-driven agent SEEKS frontiers and explores far more of the level
than random-motor (2.55×) and passive (16×). The interesting, honest shape is a **SLOW
START**: during the commit-net's early deliberation transient (ticks 2–51) curiosity is
slightly BELOW the random mean, then it **crosses over at tick 52** and pulls away
decisively (t100: 500 vs 301; t200: 932 vs 442; t300: 1295 vs 508) — the self-directed
explorer's signature (a systematic frontier-seeker beats a diffusive random walk
asymptotically, not instantly). Curiosity dominates the random mean at every budget ≥ 52.

**Curiosity vs nearest-frontier:** curiosity (1295) marginally BEATS nearest (1254) here —
the LP prioritisation (prefer frontiers with sustained unknown-adjacency) is a small net
positive on coverage AND the divergence proves the selection is load-bearing (a different,
measurable trajectory). Pre-registered honesty holds either way: the LP edge on raw coverage
is small; its clear win is commitment coherence (G3).

## The loop (all graph-native decisions; adapter = motor I/O + reveal + measure only)

```
reveal_in_view (idealised eye, unknown=absence)         domains/doom_explore_world.py  [I/O]
  -> ObsCells -> dm_* accumulate + space_quantize        domains/doom_map_ingest.py     [161000 rules]
  -> SpaceQuantum FRONTIER boxes
  -> qf_seed_frontier multi-source Bellman flood          seeds/quanta_navigation.json   [qf_* rules]
  -> LP interest per frontier (lp_* law, mode=1)          seeds/learning_progress_curiosity.json [202000 rules]
  -> ae_frontier_goal: Argmax(f_interest) reachable       seeds/doom_active_exploration.json [NEW rule]
  -> commit-net dwell (cn_* committed flag + adapter retire) seeds/learning_progress_curiosity.json [cn_* rules]
  -> qf_hop_* -> game.chosen_action                       seeds/quanta_navigation.json   [qf_* rules]
  -> adapter issues the cardinal step                     domains/doom_explore_world.apply [I/O]
  -> eye sees the result -> the map grows -> repeat
```

## G2 — GRAPH-NATIVE DECISION (source audit)

Every where-to-go decision is a rule/net; the adapter only translates I/O. Audit by file:

- **WHICH frontier** — `ae_frontier_goal` (`seeds/doom_active_exploration.json`): a RULE.
  `F == Argmax_C(f_interest)` over reachable frontier quanta (the reachability Filter reused
  verbatim from `qf_frontier_goal`). Guarded on `game.active_explore==1`.
- **HOW interesting a frontier is** — `lp_residual/lp_fast/lp_slow/lp_gate/lp_interest`
  (`seeds/learning_progress_curiosity.json`, the 202000 law): RULES. The adapter only writes
  the SENSOR obs (`info_gain` = unknown-adjacency count, pure geometry) and moves the
  rule-computed `interest` onto the frontier by pose key (mechanical value-move, like reading
  `chosen_action` out).
- **WHEN to stop re-deciding** — the commit-net `cn_marginal/cn_commit` (202000): RULES. The
  net computes `marginal_value = Ashr(v_max, step)` and sets `committed=1` when it drops below
  `commit_cost` (~4 steps). While `committed==0` the adapter mechanically retires the
  exploration goal each tick (a separate pass, gated on the graph flag — NOT a fixpoint rule,
  to avoid a mint/retire oscillation), forcing re-selection; once `cn_commit` sets
  `committed=1`, the goal is HELD (dwell). The commit ABLATION is the graph flag
  `commit_enabled` (0 → `cn_commit` never fires → perpetual thrash) — so the net's `committed`
  OUTPUT is load-bearing, not a Python `if`.
- **WHERE to step** — `qf_hop_direct/qf_hop_route` (quanta-nav): RULES. `game.chosen_action`
  = the `Argmax` `ControlResponse` by `Dot(displacement)`. No hardcoded direction.
- **The adapter** (`domains/doom_explore_world.py`, `domains/doom_active_explore_ingest.py`,
  `scripts/doom_active_explore_run.py`): reveal-in-view (geometry), emit ObsCells, tick,
  read `chosen_action`, step the avatar, count coverage. `grep -n "if " ` over the decision
  path shows only I/O guards (walkable? has-neighbour?) — never a direction choice.

Depth/pose: the controlled-motor setting uses an idealised reveal-in-view eye (NAMED
boundary — decouples sensing from policy; the real depth-from-motion eye is off-real-time
AND forward-only, which would confound the coverage comparison). Ground-truth E1M1 geometry
is an ORACLE extraction (VizDoom sector linedefs), used to build the world, never fed to the
agent as the map — the agent reconstructs the map from what it reveals.

## G3 — COMMIT-NET COHERENCE (anti-paralysis / anti-thrash) — PASS

| arm | mean commit dwell (ticks a frontier is held) | goal switches / 300 |
|---|---|---|
| curiosity (commit-net ON) | **23.08** | **12** |
| nocommit control (commit-net OFF) | 1.00 | 299 |

The commit-net ALWAYS picks (anti-paralysis: a committed frontier + an action every tick
a route exists) and, once `cn_commit` fires, COMMITS to a frontier and pursues it — a 23×
longer dwell and 25× fewer re-decisions than the no-commit control, which thrashes (a new
frontier every single tick). `d.committed` flips 0→1 at ~tick 5 (the log₂(v_max/commit_cost)
regress-breaker), verified live. Both arms reach the same final coverage (1295) — commitment
buys COHERENCE (a steady pursued path), not raw coverage, exactly the G3 claim.

## G4 — DECAYING RECONSTRUCTION UNDER MOTION + compute ∝ surprise — PASS (compute), carried (decay)

- **compute ∝ surprise:** a NOVEL-exploration tick (new cells reconstructed) costs
  **102.4 ms** on average vs **73.7 ms** for a re-tread tick (no new cells) — novel ticks are
  ~1.4× costlier (accumulation + re-quantize over freshly-opened area). The per-tick
  Spearman(reveal_ms, novel_cells) is weak (0.042) because `space_quantize`'s cost also tracks
  the growing focus bbox, not only this tick's novelty — reported straight; the novel-vs-tread
  MEAN separation is the honest signal.
- **decaying reconstruction:** the 203000 `doom_allocentric_surface` decay atom
  (`as_freshness/as_tier/as_demote`) is a first-class, orthogonal, COMPOSABLE consumer of the
  same reveal stream (dwelt regions super-resolve, long-unseen demote, revisit promotes) — its
  properties CARRY under active motion and were gated green independently
  (`test_doom_allo_surface_migrated`). This rung's frontier/nav belief is the 161000 `has_cell`
  map (binary, the frontier-bearing representation); wiring the decaying AlloCell surface to
  ALSO drive frontier selection is the named 203000↔161000 integration residual (below).

## G5 — INTEGER-NATIVE + DEFAULT-OFF byte-identity

- **Integer-native:** the LP interest / residual / progress are integer (`IDiv`/`Ashr`/`Abs`
  atoms, 202000); `f_interest` is an integer copied from `AttentionItem.interest`; the
  selection `Argmax` and the qdist flood are integer. The continuum stays in the cross-frame
  metric (none here — selection is discrete). No float in-frame coordinate.
- **Default-OFF byte-identity:** the ONLY edit to an existing seed is one additive
  `Not(active_explore==1)` guard clause on `qf_frontier_goal` (`git diff` = 18 additive
  lines). With `active_explore` absent (the entire pre-205000 world), the guard is inert and
  `qf_frontier_goal` fires unchanged. Verified: `test_quanta_navigation_migrated` +
  `test_learning_progress_migrated` GREEN (12 passed), and
  `test_active_exploration_migrated::test_default_off_leaves_quanta_nav_unchanged` GREEN.
  `runners/dsl/src/term.rs` diff EMPTY (no Rust; canonical `.so` md5 `793ce09e…` untouched).

## Honest scope + residuals (named, not patched)

- **Controlled-motor setting (declared PRIMARY, not a fallback).** Real E1M1 geometry
  (VizDoom sector linedefs → 3297-cell connected walkable region from the player start), but an
  IDEALISED reveal-in-view eye and an idealised cardinal-step motor. This is the correct choice
  for THIS claim: the real depth-from-motion eye is off-real-time AND forward-only, which would
  confound the coverage comparison (who-moves-forward-more, not who-picks-frontiers-better).
  The 203000 depth-from-motion geometric-fidelity bound carries. The measured contribution is
  the graph-native active DECISION loop, isolated.
- **203000 ↔ 161000 belief split.** The frontier/nav belief is the 161000 binary `has_cell`
  map (frontier-bearing via `space_quantize`); the 203000 decaying AlloCell surface is a
  separate, composable consumer of the same reveal stream. Unifying them (a decaying,
  residual-bearing belief that ALSO drives frontier selection, giving a genuinely
  learning-progress-POSITIVE regime rather than the info-gain/novelty-decay signal used here)
  is the named next integration.
- **LP signal is info-gain / novelty-decay, not progress-positive.** With `mode=1` the interest
  is info-gain-gated freshness (Next-Best-View): a frontier with sustained unknown-adjacency
  stays interesting, an exhausted one decays. A progress-POSITIVE signal (interest sustained
  precisely while the reconstruction residual is dropping) needs the residual-bearing belief
  above. The signal IS load-bearing (curiosity ≠ nearest trajectory; f_interest differentiates)
  but its coverage edge over nearest is small (1295 vs 1254).
- **Routing efficiency.** The qf hop over the controlled-world belief sometimes oscillates
  (Left/Right) rather than converging straight to a distant goal; coverage still dominates the
  baselines decisively, but goal-pursuit is not geodesic-optimal. An efficiency residual, not a
  correctness one.
- **AttentionItem population** is bounded by coarse spatial-bin keying (`BIN=4`) + per-epoch
  pruning of non-frontier bins; without it the pose-churning fine keys grew unboundedly and
  stalled the loop (found and fixed).
- **Single seed / single map.** One E1M1, budget 300, 5 random repeats (random std ±99.7). A
  broader map set + more repeats + a powered CI on the curiosity-vs-nearest delta is the
  natural strengthening (per the standing "power the gate" rule).

## Reproduce

```
python3 scripts/build_active_explore_seed.py                      # emit the seed + guard
python3 scripts/doom_active_explore_run.py --budget 300 --repeats-random 5
python3 scripts/doom_active_explore_report.py                     # gates.json + figure
pytest tests/test_active_exploration_migrated.py
```
