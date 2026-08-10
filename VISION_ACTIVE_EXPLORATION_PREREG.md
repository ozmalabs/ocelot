# PRE-REGISTRATION — ACTIVE CURIOSITY-DRIVEN DOOM EXPLORATION (block 205000)

*Committed ALONE, before any number. Binding. Distilled from VISION_PROTOCOL.md.*

## Seed block

`205000–205999`, one generator seeded ONCE at the base `205000`
(`np.random.default_rng(205000)`), per the seed-claim unit convention.
`python3 scripts/seed_claim.py 205000 205999` → **CLEAN — no collision DETECTED**
(618 unresolved sink sites tree-wide; a clean result means "no collision
detected", never "none exists"). VISION_PROTOCOL.md is NOT edited (per rung
instruction); this file is the declaration of record.

## The claim (headline)

The Doom eye SEES (181000), reconstructs the level as a graph-native belief map
(161000 `doom_ingraph_map` / 203000 `doom_allocentric_surface`, unknown =
ABSENCE), and the map's FRONTIER (the unknown/absence border) drives quanta-nav
frontier-seeking (`seeds/quanta_navigation.json`, the `qf_*` rules writing
`game.chosen_action`). **This rung closes the perception→DECISION→ACTION loop:
the agent CHOOSES where to move — driven by curiosity (learning-progress,
202000) seeking frontiers on its OWN reconstructed map, with the commit-net
(202000) selecting/committing — and the map grows through ACTIVE exploration
rather than a fixed scripted pan.** Every where-to-go decision is a RULE/net;
the adapter only issues the motor command the graph chose (turn / move_forward)
and ingests the result.

## The loop (all graph-native decisions; adapter = motor I/O + ingest only)

```
eye SEES a frame (VizDoom depth range-vision + pose — mechanical sensor I/O)
  → belief map accumulates (dm_* / as_* rules; unknown = absence)      [161000/203000]
  → space_quantize → SpaceQuantum passable/portal/FRONTIER boxes        [Rust primitive]
  → frontier = unknown-absence border (qf_seed_frontier multi-source flood)   [quanta-nav]
  → LEARNING-PROGRESS curiosity PRIORITISES the highest-progress frontier     [202000 + NEW]
  → COMMIT-NET SELECTS one frontier and COMMITS/dwells (anti-thrash)          [202000 + NEW]
  → qf_frontier_goal commits it as Goal{pose}; qf_hop_* → game.chosen_action  [quanta-nav]
  → adapter issues chosen_action as a VizDoom motor command (turn/move_forward)
  → eye sees the RESULT → the map grows → repeat
```

**What is NEW (block 205000, all graph DATA):** a seed
`doom_active_exploration.json` whose rules (a) mint/maintain an LP `AttentionItem`
per candidate frontier (obs = local reconstruction signal — cells newly
reconstructed near it), reusing the 202000 `lp_*` machinery, so a frontier where
the map is STILL IMPROVING scores high interest and a resolved/dead-end frontier
decays; (b) select the committed exploration frontier by LP-prioritised interest
(Argmax interest, qdist tiebreak) instead of pure nearest; (c) gate re-selection
by a 202000 `Deliberation`/`cn_commit` commit-net so a committed frontier is
PURSUED (dwell) rather than re-picked every tick. The ONE existing rule that must
be gated (`qf_frontier_goal`, nearest-pick) gets a single guard clause
`Not(active_explore==1)` so with the flag OFF it fires exactly as today
(byte-identical; `test_quanta_navigation` never sets `active_explore`).

**`runners/dsl/src/term.rs` diff MUST be EMPTY.** All required DSL Terms
(`Abs/Minus/Plus/Times/IDiv/Ashr/Max/Min/Argmin/Argmax/IfThenElse/Lt/Gt/Gte/Eq/And/Not/Attr/NodesOfType/...`)
already exist (202000 + quanta-nav use them). If a new Term seems needed, STOP
and report why. Python is a mechanical world adapter (motor I/O + reveal/ingest)
/ seed builder / measure only — NO agent decision (the direction is CHOSEN by the
graph).

## Setting & baselines

**DECLARED PRIMARY: controlled-motor active exploration on REAL E1M1 geometry.**
This is chosen up front (not as a post-hoc fallback) for two concrete,
code-established reasons that make the full real-time VizDoom+eye loop both too
heavy AND confounded for THIS claim:

1. **Too heavy.** The 203000/161000 SEEN reconstruction is depth-from-MOTION
   (RGB optical flow), which `doom_ingraph_map_run.py` itself documents as
   **off-real-time** ("off-real-time flow — ties the scale wall"; the map build is
   OFFLINE). A real-time closed action loop across 3 arms × a long budget on that
   front-end is infeasible in one session.
2. **Confounded.** SEEN depth-from-motion only exists on FORWARD-translation
   frames (`action==forward` AND `T_world≥1`). Coupling the motor policy to the
   sensing quality would make the coverage comparison measure *who-moves-forward-
   more*, not *who-picks-frontiers-better* — destroying the isolation G1 needs.

So the controlled-motor setting DECOUPLES sensing from policy to isolate the
DECISION under test. Concretely: E1M1's walkable occupancy is extracted ONCE from
VizDoom (real level geometry, ground truth); the avatar starts at E1M1's fixed
player start; **reveal-in-view** partial observability (cells within FOV + range,
un-occluded by walls, become known-floor belief; unknown = ABSENCE) is the
idealised eye; the motor is an idealised cell-step / turn in the same discretised
pose space. **The agent's DIRECTION is still chosen entirely by the graph** (the
real space_quantize frontiers + quanta-nav qf_* rules + the new LP-curiosity +
commit-net); only sensing and motor EXECUTION are idealised. The 203000
depth-from-motion geometric-fidelity bound carries as the named boundary.

Three arms, each over a fixed action budget from the SAME fixed E1M1 start:

- **CURIOSITY-DRIVEN** — the full graph-native loop (frontier + LP-curiosity +
  commit + nav-intent), `active_explore=1`.
- **RANDOM-motor** — `chosen_action` replaced by a uniform random admissible
  motor command each tick (`rng(205000)`), same map ingest.
- **PASSIVE (no-move)** — the eye ingests but no motor command is issued (the
  agent stays put — a strict no-move floor; coverage = whatever the initial view
  reveals).
- **NEAREST-FRONTIER (reference)** — the existing quanta-nav nearest-frontier
  policy (LP off, commit off): the pre-205000 explorer, for context.

**Optional end-to-end confirmation (not gating).** If time permits, a SHORT
real-VizDoom smoke test that `chosen_action` issued through `doom_world`'s motor
API actually drives the marine and the belief grows — proving the motor closure
physically closes — with a small budget and the named heaviness boundary. The
headline claim is gated on the controlled-motor arms above.

## Gates (pre-registered BEFORE any number)

- **G1 — ACTIVE EXPLORATION (headline).** Over a fixed action budget, the
  curiosity-driven agent explores MORE of the level (map coverage = reconstructed
  passable cells / SpaceQuantum passable area) than BOTH random-motor and passive.
  Deliverable: the coverage-vs-actions curve for all three arms. **PASS** iff
  curiosity's final coverage > random's AND > passive's, and the curve dominates
  (curiosity ≥ random at essentially every budget). A measured NEGATIVE (curiosity
  does not beat random) is reported straight and is a valid landing. Nearest-
  frontier (LP off, commit off) is reported as a reference arm; curiosity is NOT
  required to beat nearest on raw coverage (its edge is coherence/information, G3).
- **G2 — GRAPH-NATIVE DECISION.** Source-audit that frontier-selection +
  LP-prioritisation + commit are RULES/nets (seed JSON), and the adapter only
  translates the chosen nav intent into a VizDoom motor command — no Python `if`
  decides direction. Depth/pose are oracle sensor input (mechanical I/O; labels
  are oracles only), exactly as the reused ingest front-end uses them.
- **G3 — COMMIT-NET COHERENCE (anti-paralysis / anti-thrash).** The commit-net
  ALWAYS picks (no paralysis: an action is issued every tick a route exists) and
  COMMITS to a frontier and pursues it (dwell) rather than oscillating every tick.
  Deliverable: commit dwell length / re-decision cadence (mean ticks a committed
  frontier goal is held) for curiosity WITH vs WITHOUT the commit-net; the
  no-commit control must thrash (short dwell / high goal-flip rate) or the
  commit-net makes no difference (also reported straight).
- **G4 — DECAYING RECONSTRUCTION UNDER MOTION + compute ∝ surprise.** The map
  stays a DECAYING reconstruction under active motion (203000 carries: dwelt
  regions super-resolve, long-unseen demote, revisit promotes) — verified by the
  freshness/tier attributes moving under the active loop; and compute ∝ surprise
  (novel exploration ticks cost more work than re-treading known area — measured
  as rules-fired / cells-touched per tick, novel vs revisit).
- **G5 — INTEGER-NATIVE + DEFAULT-OFF byte-identity.** All new decision values are
  in-frame integers (the continuum stays in the cross-frame verdict/metric).
  With the active-explore flag OFF, the existing scripted-pan / quanta-nav / eye
  paths are BYTE-IDENTICAL (the single `qf_frontier_goal` guard is inert when
  `active_explore != 1`). Audited by a toggle-diff.

## Discipline commitments

- **term.rs diff EMPTY** (reuse only). Canonical `.so` stays `793ce09e` (seed +
  Python only; the worktree binary is the copied canonical binary, md5 verified).
- **Measure module IMPORT-INERT** (a scoped context manager only; no top-level
  side effects).
- **Engine-semantics gate set (ONE synchronous session) only if the engine is
  touched** — not planned (seed + Python only). The regression guard is the eye
  suite + `test_quanta_navigation` + `test_learning_progress` +
  `test_doom_allo_surface` + `test_held_surface` + a new
  `test_active_exploration_migrated`, all green.
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER.
  **`source_match` own/shared.** **Commit before report.** Do NOT merge to main;
  do NOT touch VISION_PROTOCOL.md.

## Falsifiers (what would sink each claim)

- G1: curiosity coverage ≤ random, or the curve does not dominate → NEGATIVE,
  reported straight (curiosity-driven frontier-seeking gives no coverage edge).
- G2: any Python branch reads graph state and picks a direction → the decision
  is not graph-native; STOP.
- G3: the commit-net never fires / dwell == 1 tick (thrash) even with it on, or
  it stalls (paralysis, no action while a route exists) → commit-net incoherent.
- G5: any non-byte-identical diff with the flag OFF → default-OFF violated.
