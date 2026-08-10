# LS20 OBSERVE-AND-GROUND remote causality — RESULTS (block 229000)

Pre-registered in `LS20_GROUND_PREREG.md` (committed **ALONE**, SHA `3612a5ff9b`),
BEFORE any number here. Block `229000-229999` claimed CLEAN (`seed_claim.py 229000
229999`; verbatim `check_claim` recorded in the prereg — NOT a permanent pytest).

## THE CORRECTION THIS BLOCK MAKES (owner)

Block 228000 proved remote causation, but it established the causal link by running a
**probe WORLD-MODEL** to SIMULATE the act-vs-no-op counterfactual (`eff_act`/`eff_noop`
from re-running a deterministic world under (do) vs (no-op)). That is **model-based**
and works only offline where you can REWIND. **On the real game there is NO rewind**, so
228's live path ran the model-probe, got `eff_act=0`, and grounded NOTHING.

Owner: *"What it needs to do is OBSERVE the causality and ADD that grounded
understanding to the graph in the context, so it KNOWS that the cross causes rotation."*

**229 grounds the causal link FROM REAL OBSERVATION, not simulation:** the agent
interacts, OBSERVES the actual before→after remote change (perception), and if the
remote thing changed — AND the natural timeline shows it does NOT change on its own —
MINTS a persistent grounded `causes(cross, rotation)` fact into the graph. The no-op /
negative evidence is the **NATURAL TIMELINE** (real steps with no interaction and no
change), never a simulated counterfactual.

## THE HEADLINE — G-observe-and-ground: THE FACT IS GROUNDED FROM OBSERVATION

Pair-scored across Family A (the cross truly rotates the remote thing — change ONLY on
interact steps → ground it) ∧ Family B (the remote thing rotates SPONTANEOUSLY —
coincidence → refuse). N=24 pairs/flavour × 2 flavours = **48 pairs**, Wilson 95% CIs
(`results/remote_causal_ground_powered.json`):

| arm | pair-correct (A∧B) | Family A (ground the true cause) | Family B (spontaneous → refuse) |
|---|---|---|---|
| **observe (grounded from observation)** | **1.000 [0.926, 1.000]** | **1.000 [0.926, 1.000]** | **1.000 [0.926, 1.000]** |
| no_natural_timeline (ignores the no-op) | 0.000 [0.000, 0.074] | 1.000 [0.926, 1.000] | 0.000 [0.000, 0.074] |
| blind (never observes the effect) | 0.000 [0.000, 0.074] | 0.000 [0.000, 0.074] | 1.000 [0.926, 1.000] |

- **G-observe-and-ground: PASS.** `observe` pair CI-lower **0.926 > 0.074** the CI-upper
  of BOTH controls — CI-separated. The fact is minted from the OBSERVED before→after: a
  `CausalFact{cause, effect:"rotation", status:"grounded", source:"observation"}` node +
  a `causes` edge from the cross object to the fact, **absent before (0.000 grounded
  pre-timeline), present after, and it PERSISTS** (persist-rate **1.000 [0.926, 1.000]**;
  the mint-once `Not Exists` guard keeps it at exactly one fact across re-runs).
- **Each control fails for its PRINCIPLED reason.** `blind` (its perception of the effect
  is severed — `remote_changed` always 0) **never grounds → misses Family A**. It
  vacuously "passes" Family B (grounds nothing where nothing should be grounded), so it
  fails the PAIR. `no_natural_timeline` ignores the natural-timeline no-op → grounds on
  ANY co-observed interact→change → **confabulates on Family B** (a spontaneously-changing
  remote thing), so it fails the pair. Only reading the OBSERVED effect AND the
  natural-timeline no-op is correct on both families.
- **The effect kind is OBSERVED, not asserted.** `observe_change(before, after)` returns
  `"rotation"` iff `AFTER == rot90(BEFORE)` — a real array comparison (the offline twin of
  the live real-frame onset diff). The rule carries the observed kind through; it names no
  "rotation" constant.

## G-grounded-from-observation-not-simulation — THE CORRECTION, SOURCE-AUDITED

`source_audit` (`{'banned_tokens_found': [], 'grounding_reads_observed_remote_changed':
True, 'grounding_reads_natural_timeline_noop': True,
'grounding_reads_simulated_eff_act_eff_noop': False, 'clean': True}`):

- the grounding rule `rcg_ground` reads `Observation.remote_changed` (the OBSERVED
  before→after) and the natural-timeline no-op (a `Not Exists` over Observations with
  `interact==0 AND remote_changed==1`) — it **NEVER reads `eff_act`/`eff_noop`** (the 228
  SIMULATED counterfactual keys);
- **the 228 model-probe CONTRAST reproduced.** The 228 `rc_confirm_interventional` reads
  `eff_act`/`eff_noop`, which only exist by running the world under (do) vs (no-op) — a
  REWIND. Fed a REAL observation with no simulated no-op available (`eff_act=0`, the 228
  live reality), the 228 path's posit goes to **`refuted`** — it **grounds NOTHING live**
  (`sim_path_confirmed_live=False`). The observation path grounds it from the real
  before→after. This is exactly WHY the correction is needed.
- the rules name NO ls20/doom/cross/lever/door/rotation/shape constant in their logic —
  the machinery is domain-agnostic by construction.

## G-knows-and-acts — THE GROUNDED FACT IS USABLE

With `causes(cross,rotation)` grounded, the agent reads it (`rcg_knows_and_acts`) → seeks
the cross → operates it → obtains the effect → passes (`rcg_pass`). N=24
(`results/remote_causal_ground_powered.json`):

| arm | grounded-rate | win-rate (route → operate → pass) |
|---|---|---|
| **observe** | **1.000** | **1.000 [0.862, 1.000]** |
| blind | 0.000 | 0.000 [0.000, 0.138] |

- **G-knows-and-acts: PASS.** `observe` win CI-lower 0.862 > `blind` CI-upper 0.138 —
  CI-separated. The grounded fact is USABLE: the agent that KNOWS `causes(cross,rotation)`
  acts on it and passes; the `blind` agent (never grounded the fact) has no knowledge to
  read → never seeks → never passes. Without the grounded fact there is no move
  (`test_without_grounded_fact_agent_cannot_act`).

## G-live (REAL ls20) — HONEST NULL, MEASURED STRAIGHT

`remote_causal_ground_live.py --game ls20-9607627b --steps 40`
(`results/remote_causal_ground_live.json`). **FRESH-API** (not deterministic replay).
Auth verified BEFORE measuring (`ARC_API_KEY` from the gitignored `.env`, NEVER
printed/committed; RESET returned `state=NOT_FINISHED`, grid 64×64,
`available=[ACTION1..4]`):

| metric (REAL ls20, 40 steps) | value |
|---|---|
| perception round-trip OK (216 eye) | **true** |
| onset fire rate | **1.0 (40/40)** |
| reached the salient object | **true** |
| interacted with it | **true** |
| **distal (remote) change frames OBSERVED** | **0** |
| natural-timeline no-interaction-and-distal-change frames | 0 |
| grounded `causes(cross,rotation)` | **false (HONEST NULL)** |
| levels_completed | 0 |

**The honest verdict is case (b): NO observable remote change in the budget.** The
interaction REGISTERED (onset 40/40, reached + interacted with the salient object,
localised CONSISTENTLY to rows ≈ 42-47, cols ≈ 29-34 — the same region 223/225/227/228
reported), but **NO distal (remote) change was OBSERVED** in the real before→after
transitions across the 40-step random-action budget → there was nothing to ground.

**This is a DISTINCT, better finding than 228's live null, and it is reported straight.**
228 grounded nothing because it needed a SIMULATED no-op rewind (`eff_act=0` — a
model-probe artifact). 229 grounds nothing because **no distal change was OBSERVED** — a
genuine OBSERVATIONAL null: under a bounded random-action policy the interaction does not
produce a visible remote change. The observation path **would ground the instant a distal
change is observed** (proven decisively offline). The measured meaning: the random-action
interaction is not triggering an observable remote mechanic — the **real
steering-to-operate policy** (deliberately operating the cross to elicit the remote
effect) is the standing frontier, exactly 223/225/227/228's named residual. MEASURED, not
assumed.

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (NO Rust; reuses
  the 216/217 perception, the 227 posit/confirm pattern, the 210 operate seek/use, the
  220 nav step, and the substrate's node/edge mint pattern).
- **`runners/dsl` tracked diff EMPTY** (`term.rs` included) — no tracked file modified;
  the rung is entirely NEW untracked files (seed builder, seed json, world adapter,
  measure, live, test, results) → existing suites are byte-identical BY CONSTRUCTION.
- **Default-OFF byte-identical:** every rule guarded on `game.ground_on==1`
  (`test_every_rule_guarded_on_ground_on`); a graph without the flag mints no fact and
  writes no waypoint (`test_default_off_no_rule_fires`).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped, 0 failed** == AFTER
  **214 passed, 10 skipped, 0 failed** (`results/ground_oracle_{before,after}.txt`).
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET **IDENTICAL** BEFORE
  == AFTER — **23 failed, 277 passed, 5 skipped** both runs; `diff` of the sorted node-id
  lists EMPTY (`results/ground_regress_{before,after}_ids.txt`). (These 23 are the
  pre-existing reds this environment carries; 229 touches none.)
- **New gates:** `tests/test_remote_causal_ground_migrated.py` **13 passed**
  (observe-grounds-controls-do-not; absent-before/present-after/persists;
  persist+mint-once; refuse-on-spontaneous-natural-timeline; reads-observed-not-simulated
  source-audit; observe_change-is-a-real-diff; grounded-fact-usable-agent-acts;
  without-fact-cannot-act; no-domain-tokens; guarded-on-ground_on; default-off;
  seed-roundtrip source_match; manifest-shape).
- **Integer-native:** the observed facts are integer 0/1; the grounding verdict is exact
  equality on the observed before→after + the natural-timeline no-op.
- **Seed round-trips:** `domains/remote_causal_ground_seed.py` →
  `seeds/remote_causal_ground.json` rebuilds byte-stable (`source_match = True`).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the OBSERVE-AND-GROUND MECHANISM decisively: the
agent grounds `causes(cross,rotation)` from the REAL observed before→after (vs `blind`,
which never observes the effect, CI-separated; and vs `no_natural_timeline`, which
ignores the natural-timeline no-op and confabulates on coincidence, CI-separated 0.926 vs
0.074 on the pair), the fact PERSISTS and is USABLE (the agent reads it and passes; vs
`blind`, CI-separated), and it is grounded FROM OBSERVATION not simulation (source-audit
clean; the 228 model-probe path grounds nothing without a rewind). The world is a clean
observed causal world (the before→after change is a real array diff; the rules produce the
verdict). The LIVE half reports the honest split: the perception + interaction transfer to
real ls20 (round-trip OK, onset 40/40, reached + interacted), but NO distal remote change
was OBSERVED in the bounded random-action budget → nothing to ground (an honest
observational null, distinct from 228's model-probe null). The real steering-to-operate
policy is the standing frontier. Both reported.

## FILES

- `LS20_GROUND_PREREG.md` — pre-registration (committed alone, SHA `3612a5ff9b`).
- `domains/remote_causal_ground_seed.py` → `seeds/remote_causal_ground.json` — the
  observe-and-ground rules (domain-agnostic; default-OFF).
- `worlds/remote_causal_ground.py` — the mechanical adapter + episode drivers (the remote
  thing's before→after is OBSERVED via a real array diff).
- `scripts/remote_causal_ground_measure.py` — the powered offline gates + source-audit +
  the 228 model-probe contrast + knows-and-acts.
- `scripts/remote_causal_ground_live.py` — the bounded LIVE half.
- `tests/test_remote_causal_ground_migrated.py` — 13 gate tests.
- `results/remote_causal_ground_{powered,live}.json` — the measured numbers.
- `results/ground_{oracle,regress}_{before,after}*` — the discipline baselines.
