# LS20 UNDERSTANDING — RESULTS (block 221000)

**Winning is a SIDE EFFECT of understanding. The true victory is knowledge.**

Pre-registered in `LS20_UNDERSTANDING_PREREG.md` (committed ALONE, SHA in the log
below). Block `221000` claimed CLEAN (`seed_claim.py 221000 221999`, exit 0). All
gates PASS at the pre-registered powered n. **Lead with the understanding result,
not the win count.**

## THE UNDERSTANDING RESULT (headline — the true victory)

The agent DISCOVERS the ls20 mechanic (which station applies which transform) by
its own **curiosity + predict-and-residual**, and its model CONVERGES. Powered run
`--episodes 25 --levels 200 --noise 0 8 16 --noise-episodes 6`
(`results/arc_ls20_understanding_powered.json`):

**G-understanding (convergence, clean sigma=0):**

| cycle t | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **surprise** (predict-residual) | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **0.0** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| **model accuracy** (vs truth) | .17 | .33 | .50 | .67 | .83 | **1.0** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

- Surprise DROPS 1.0→0.0 the moment every station is modelled; model accuracy RISES
  0→1.0 by cycle S; **confirmed hypotheses 6.000 [6.000, 6.000]** (min 6 — every
  station's transform correctly RE-predicted); frac_model_complete **1.000
  [0.867, 1.000]**; median complete-cycle 5. The curiosity `Argmin(visits)` covers
  all S stations in S cycles, then confirms in S more — **DETERMINISTIC (zero
  variance across 25 episodes**: the sd-loop recognition is deterministic).
- **The mechanic is LEARNED, not hardcoded:** each station's transform is
  recognised by the general 217000 sd-loop (rot90:k / refl / recolour) and minted
  as a `Hypothesis{key, conf}` — named hypotheses, a named surprise (predict vs
  observe residual), discovered by investigation. THIS is the deliverable.

**Gate teeth (the metric CAN fail — instrument discipline):** at sigma=8 the curve
is identical (219000 parity envelope); at **sigma=16** perception breaks →
**accuracy 0.0, confirmed 0, frac_complete 0.000 [0.000, 0.390]**. Note the honest
subtlety the gate catches: under heavy noise **surprise still self-converges to
0** (the agent confidently re-predicts its own WRONG recognition), but **accuracy
vs ground truth detects the failure**. Surprise-only convergence would mask it;
the accuracy gate has teeth.

## WIN AS A SIDE EFFECT (logged, never optimised)

`G-win-as-side-effect`: the delivery arm consults the LEARNED model
(`uh_deliver_route`: the station whose hypothesis key == the recognised required
transform — a model lookup, never a goal search). On 200 held-out levels:

- understand held-out **win-rate 1.000 [0.981, 1.000]**; model_complete_cycle **5**;
  **wins before model-complete: 0** (structural — a win cannot precede modelling the
  required transform). Winning FOLLOWS understanding, never precedes it.

## THE CONTROL THAT EARNS THE REFRAME (`G-vs-win-bound`, reported STRAIGHT)

`win_bound` (`wb_*`) optimises goal-reach directly (`wb_probe_pick` = the station
nearest the goal), holds NO persistent model → re-searches every level:

| arm | held-out win-rate | applies / level | investigation |
|---|---|---|---|
| **understand** (curiosity+model) | **1.000 [0.981, 1.000]** | 1.000 [1.000, 1.000] | 2S probes ONCE |
| win_bound **B=1** (tight budget) | **0.155 [0.111, 0.212]** | 1.000 | none (re-search) |
| win_bound **B=S** (loose budget) | 1.000 [0.981, 1.000] | **3.510 [3.274, 3.746]** | re-paid EVERY level |

- **Understanding GENERALISES; win-binding is BRITTLE under a tight budget:**
  understand 1.000 vs win_bound(B=1) 0.155 — **CI-separated** (win_bound upper
  0.212 < understand lower 0.981). Without the model, optimising goal-reach with
  one try is ≈ 1/S guessing.
- **Amortisation (reported straight):** with a loose budget win_bound also reaches
  1.000 — BUT at **3.51 applies/level, re-paid on EVERY level**, vs understand's
  ONE 2S-probe investigation then ~1 apply/level. Total-cost crossover ≈ K==S:
  understand `2S + K` vs win_bound `~3.5·K`. Understanding pays once and reuses;
  win-binding pays per level and learns nothing.

## GRAPH-NATIVE + SOURCE-AUDIT (`G-graph-native`)

The drive is curiosity/surprise/hypothesis RULES (`seeds/ls20_understanding.json`:
`uh_probe_pick` Argmin-visits curiosity; `uh_predict`/`uh_mint`/`uh_confirm`/
`uh_revise` predict-and-residual; `uh_deliver_route` model lookup). The adapter
(`worlds/arc_ls20_understanding.py`) is mechanical (perceive → stamp → tick → read
action → apply → log). ONE persistent agent per arm — the model carries across
levels (that IS the reframe); the world only presents observances + affordances
(`present_level`), never resets agent state from Python (the agent clears its own
attention on a `level_start` observation via `uh_level_start`).

`scripts/arc_ls20_understanding_audit.py` (source_match) — PASS:

```
pick rule uh_probe_pick   (DRIVE)   SELECTS BY: visits/novelty
pick rule wb_probe_pick   (CONTROL) SELECTS BY: goal-proximity
uh_* DRIVE rules that SELECT by goal-proximity: []   (MUST be [])
wb_* CONTROL rules that select by goal-proximity (by design): ['wb_probe_pick']
```

The `banned_tokens` = goal coords inside a SELECTION (`Argmin`/`Argmax` value). The
understanding drive selects by NOVELTY only; the win-objective lives ONLY in the
`wb_*` control. (`uh_deliver_goal` routes to the goal cell to DELIVER an
already-correct symbol — a `set_attr wp_r <- goal_r` assignment, the established
218000 `plan_deliver` pattern — which is a terminal act, not a selection objective.)

## LIVE HALF (real ARC-AGI-3 ls20 — honest, bounded n)

Auth + connectivity verified BEFORE measuring (key from `.env`, NEVER printed/
committed; `.so` gitignored, NEVER committed). RESET returned a live 64×64 frame
(ACTION1-4, palette [0,1,3,4,5,8,9,11,12]). `arc_ls20_understanding_live.py --game
ls20-9607627b --steps 40` (`results/arc_ls20_understanding_live.json`):

- **Perception survives on REAL live frames:** round-trip through the 216000 pixel
  eye exact on all 40 frames (219000 replicated).
- **The surprise signal is real:** held-prediction (order-0) next-frame residual
  mean **0.0127** (≈ 52 of 4096 cells change per action) — actions demonstrably do
  something; the predict-and-residual signal the offline loop runs on is present
  live.
- **Per-action effect model converges:** per-action prediction residual **0.0**
  (each action's aggregate change-magnitude is regular; the minted per-action
  hypothesis is confirmed after one observation — the live twin of the offline
  mint→confirm).
- **Win as a side effect:** `levels_completed = 0` (final_state NOT_FINISHED) —
  logged honestly. Bounded n; the OFFLINE station→transform understanding is the
  deliverable. The full live mechanic is NOT claimed learned in bounded n (a
  richer per-cell live model is future work).

## DISCIPLINE

- **Canonical `.so`:** md5 `793ce09ed498a749abb79aeaea44b92e` **UNCHANGED** (no Rust).
- **`runners/dsl` diff EMPTY** (`term.rs` included) — `git diff --stat` empty.
- **Default-OFF byte-identical:** `test_arc_ls20_planning_migrated.py` (7) +
  `test_arc_ls20_mapnav_migrated.py` (5) = **12 passed** — the 218000/220000
  behaviour is unchanged with `understand_on` absent, and the shared
  `recognise_required_key` change (`_see` hook + a pure-function memo keyed on the
  SEEN signatures) is output-identical.
- **Oracle `rung7_vision_bench`:** BEFORE (220000 baseline) **214 passed, 10
  skipped** == AFTER **214 passed, 10 skipped**.
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET **IDENTICAL**
  to the 220000 baseline (`results/mapnav_regress_before.txt`, 23 ids) — `diff`
  **empty** (23 failed / 277 passed / 5 skipped, same set). Per the standing rule
  the baseline is the LIST of node ids, not a count.
- **Integer-native:** the shapes are the integer lattice; the transform key is a
  categorical token; the sd-loop's continuous verdict is a cross-frame map, not an
  in-frame coordinate.

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The powered convergence + generalisation are on ls20-SHAPED offline scenarios (the
real ls20 palette, SEEN through the 216000 pixel eye; the transform recogniser is
the general 217000 sd-loop). They prove the MECHANISM — understanding the mechanic
by curiosity + predict-and-residual, and winning falling out — and MEASURE the
reframe (understanding generalises; win-binding overfits/costs). The LIVE half
confirms perception + the surprise signal run on REAL content but does NOT learn
the full live mechanic in bounded n. Both reported.

## FILES

- `LS20_UNDERSTANDING_PREREG.md` — pre-registration (committed alone).
- `domains/ls20_understanding_seed.py` → `seeds/ls20_understanding.json` — the
  `uh_*` curiosity/predict-residual/hypothesis drive + `wb_*` control rules.
- `worlds/arc_ls20_understanding.py` — the mechanical adapter + episode driver.
- `scripts/arc_ls20_understanding_measure.py` — the powered offline measure.
- `scripts/arc_ls20_understanding_audit.py` — the source_match (no win-objective).
- `scripts/arc_ls20_understanding_live.py` — the bounded live half.
- `worlds/arc_ls20_scenario.py` — `recognise_required_key` gained a `_see` hook +
  a pure-function memo (output-identical; the 12 migrated tests confirm).
- `results/arc_ls20_understanding_{powered,live}.json` — the measured numbers.
