# LS20 REMOTE CAUSATION — "the switch affects a remote thing" — RESULTS (block 228000)

Pre-registered in `LS20_REMOTE_PREREG.md` (committed **ALONE**, SHA `0f3c5ae909`),
BEFORE any number here. Block `228000-228999` claimed CLEAN (`seed_claim.py 228000
228999`; verbatim `check_claim` recorded in the prereg — NOT a permanent pytest,
avoiding the 223000 ledger-inversion mistake).

## LEAD — WHAT ACTIONS DOES THE AGENT TAKE TO FURTHER ITS POSITS?

**It goes to the CROSS (the only-other salient thing) out of EXHAUSTION, interacts,
and DISCOVERS by intervention that the switch affects a REMOTE thing — attributing
B's change ACROSS SPACE.** The chicken-and-egg the owner flagged is respected: the
go-to-cross decision is PRIOR to any causal model (you cannot posit "cross → remote
effect" before you have been to the cross). The loop is: exhaust the known option →
226 frustration breaks the futile cycle → seek the ONLY un-visited salient object
(visited+salience only, NO causal belief) → interact → the interventional do-contrast
(act→effect vs no-op→no-effect) BORNS + CONFIRMS the remote-causal link across space
→ act → pass. This closes the DEFERRED DOOM PROBLEM ("switch here → door there"): the
SAME rules attribute `cross → remote shape` on an ls20-shaped board AND `lever →
remote door` on a Doom-shaped board.

**OFFLINE: every gate PASSES, CI-separated.** **LIVE on real ls20: the exploration
loop RUNS (reaches + interacts with the salient object, mints a posit) but the remote
link + pass are an honest NULL** (no distal remote change observed in the bounded
random-action budget; the real steering/operate is the standing frontier). Both
reported straight.

## THE HEADLINE — G-remote-attribution: THE EFFECT IS ATTRIBUTED ACROSS SPACE

The rate at which the agent produces the CORRECT causal verdict, scored PER MATCHED
PAIR (a Family-A confounded-remote scenario ∧ a Family-B coincidence scenario, BOTH
correct — so a success requires BOTH spatial reach AND interventional discipline).
N=24 pairs/config × 2 flavours = **48 pairs**, two configs (first + held-out), Wilson
95% CIs (`results/remote_causal_powered.json`):

| arm | pair-correct (A∧B) | Family A (confounded remote) | Family B (coincidence) |
|---|---|---|---|
| **remote (interventional, full scope)** | **1.000 [0.926, 1.000]** | **1.000 [0.926, 1.000]** | **1.000 [0.926, 1.000]** |
| local_only (attributes only at B's location) | 0.000 [0.000, 0.074] | 0.000 [0.000, 0.074] | 1.000 [0.926, 1.000] |
| no_intervention (passive co-occurrence) | 0.000 [0.000, 0.074] | 0.000 [0.000, 0.074] | 0.000 [0.000, 0.074] |

- **G-remote-attribution: PASS.** remote pair CI-lower **0.926 > 0.074** the CI-upper
  of BOTH the local_only AND the no_intervention controls, on BOTH configs —
  CI-separated. The interventional contrast (act→effect vs no-op→no-effect) is the
  teeth.
- **Each control fails for its PRINCIPLED reason, and the decomposition shows where.**
  On **Family A** (a REMOTE cross truly controls B; a LOCAL distractor at B only
  co-occurs) the `local_only` control can only attribute at B's location → never
  posits the remote cross → **misses it (0.000)**; the `no_intervention` control
  confabulates the local distractor from passive co-occurrence → **false-positive
  (0.000)**. On **Family B** (B changes on its own, the cross is NOT causal)
  `no_intervention` confabulates the coincidental cross → **wrong (0.000)**, while the
  interventional `remote` (and `local_only`, by locality) correctly REFUSE the link
  (eff_act==eff_noop → refuted). Coincidence is not causation, and only the
  do-contrast tells them apart.
- **The interventional facts are OBSERVED, not asserted.** eff_act/eff_noop come from
  actually running the probe world-model under (do) vs (no-op); the RULES produce the
  confirm/refute verdict. `rc_confirm_interventional` fires iff `eff_act==1 ∧
  eff_noop==0`; `rc_refute_interventional` iff `eff_act==eff_noop`.

## G-exhaustion-drives-exploration — the go-to-cross is PRIOR to the causal model

Grid boards (genuinely-REMOTE: the transform provider is a remote SWITCH, no local
station), N=24/flavour × 2 = **48 boards** (`results/remote_causal_powered.json`):

| arm | reach-the-switch | pass-via-remote |
|---|---|---|
| **remote** | **1.000 [0.926, 1.000]** | **1.000 [0.926, 1.000]** |
| local_only | 1.000 [0.926, 1.000] | 0.000 [0.000, 0.074] |
| no_intervention | 1.000 [0.926, 1.000] | 1.000 [0.926, 1.000] |
| causal_prior | 0.000 [0.000, 0.074] | 0.000 [0.000, 0.074] |

- **G-exhaustion-drives-exploration: PASS.** remote reach-the-switch CI-lower 0.926 >
  causal_prior CI-upper 0.074 — CI-separated. The agent goes to the cross driven by
  EXHAUSTION + SALIENCE with NO prior causal model; the `causal_prior` control (only
  moves toward an object it ALREADY has a hypothesis for) never forms a hypothesis for
  the un-visited switch → **never goes (0.000)** → cycles forever. Confirmed on the
  trace: the agent enters explore_mode and heads to the switch BEFORE
  `attributed_remote` becomes 1 (`test_exploration_precedes_the_causal_model`).
- **G-pass-via-remote: PASS.** the full loop passes the genuinely-remote board (1.000)
  where the 227-style `local_only` model — which can only attribute the transform
  LOCALLY — CANNOT (0.000): it explores + reaches the switch, but its local-scope
  attribution never confirms the remote link, so it never operates the switch and
  never passes. (`no_intervention` passes THIS board because its confabulation happens
  to be right where the cross IS the cause — it is not the pass control; its
  confabulation fails on Family B above.)

## G-action-furthers-posit — the action IS interact-with-the-cross, not a local probe

From the `remote` trace (`action_trace`): known-probe of the block AS-IS at step 0 →
did NOT pass; exhausted → explore_mode; **navigated toward the ONLY un-visited salient
object (the remote switch) and interacted** (NOT a local block-probe); **attributed
B's change to the remote switch across space**; operated it → B matched → passed.
`action_is_interact_not_local_probe = True`; `confirmed = ['cross']`.

## G-general — the SAME rules close the deferred Doom problem

The SAME `remote_causal` RULES run on a Doom-shaped board (a LEVER → a remote DOOR),
N=24 (`results/remote_causal_powered.json`, per_flavour.doom):

| arm | doom attribution pair (A∧B) | doom reach-lever | doom pass |
|---|---|---|---|
| **remote** | **1.000 [0.862, 1.000]** | **1.000 [0.862, 1.000]** | **1.000 [0.862, 1.000]** |
| local_only | 0.000 [0.000, 0.138] | 1.000 [0.862, 1.000] | 0.000 [0.000, 0.138] |
| no_intervention | 0.000 [0.000, 0.138] | 1.000 [0.862, 1.000] | 1.000 [0.862, 1.000] |
| causal_prior | — | 0.000 [0.000, 0.138] | 0.000 [0.000, 0.138] |

- **G-general: PASS.** The remote-causal machinery is GENERAL — `lever → remote door`
  reproduces `cross → remote shape` byte-for-byte in behaviour. It is NOT an ls20 hack:
  the flavour changes only object LABELS; the graph structure + every rule are
  identical. Source-audit confirms the rules name NO ls20/doom/cross/lever/door/rotation
  constant (they operate on generic `SalientObject`/`RemoteCausalPosit` nodes with a
  spatial-separation flag `is_local` and the interventional observations).

## G-anti-cycle (226 tie-in) — exhaustion breaks the cycle, discovery does not

Feeding the two traces into the 226000 modulator: the **causal_prior** trace (never
explores → recurrent blind cycle, no understanding gain = FUTILE) is BROKEN at step 12
(frustration 52 ≥ threshold 20 → `break_now`); the **remote** trace (exhaustion →
explore → intervene → discover → act, genuine progress each step) is **NOT broken**
(frustration 0.0). **`anti_cycle_holds = True`** — frustration stops the futile loop;
exhaustion+salience points at the switch; the causal discovery follows on arrival.

## G-graph-native / SOURCE-AUDIT — NO hardcoded causal link, NO domain tokens

`source_audit` (`{'banned_tokens_found': [], 'explore_reads_only_visited_salience':
True, 'confirm_without_intervention_shortcut': [], 'clean': True}`):

- the rules' LOGIC (match/where/effects) names NO ls20/doom/cross/lever/door/switch/
  rotation constant — the machinery is domain-agnostic by construction;
- the go-to-cross decision (`rc_seek_novel_salient`) reads ONLY `visited` + `salient`
  (+ the explore_mode/symbol_matches_goal guards) — NEVER a causal attribute, NEVER a
  hardcoded "the cross is the switch";
- **NO rule confirms a link without the interventional (or, for the labelled control,
  passive) observation** — the causal link is DISCOVERED by intervention, never
  hardcoded. `rc_confirm_interventional` reads `eff_act`/`eff_noop`;
- the adapter (`worlds/remote_causal.py`) never decides the causal link or the move —
  it writes perception facts, runs the probes as world physics, steps toward the
  rule-chosen waypoint, and applies the remote effect on interact
  (`test_default_off_no_rule_fires`, `test_source_audit_no_domain_tokens_in_logic`).

## G-live (REAL ls20) — THE EXPLORATION LOOP RUNS; THE REMOTE LINK + PASS ARE HONEST NULLS

`remote_causal_live.py --game ls20-9607627b --steps 30` (`results/remote_causal_live.json`).
FRESH-API (not deterministic replay). Auth verified BEFORE measuring (`X-Api-Key` from
the gitignored `.env`, NEVER printed/committed; RESET returned `state=NOT_FINISHED`,
grid 64×64, `available=[ACTION1..4]`):

| metric (REAL ls20, 30 steps) | remote | no_intervention |
|---|---|---|
| perception round-trip OK (216 eye) | **true** | true |
| onset fire rate | **1.0 (30/30)** | 1.0 |
| reached the salient object | **true** | true |
| interacted with it | **true** | true |
| posits minted | **1** | 1 |
| distal (remote) change observed | **0 frames** | 0 |
| remote link confirmed / attributed across space | **NULL** | NULL |
| levels_completed | 0 | 0 |

- **The DISCOVERY loop RUNS on real ls20:** the general onset stream fires on 30/30
  real frames, localised CONSISTENTLY to **rows ≈ 42-47, cols ≈ 29-34** (the same
  region 223000/225000/227000 reported); the agent EXPLORES to the salient object,
  INTERACTS, and mints a `RemoteCausalPosit`. The exhaustion-first exploration
  transfers.
- **The remote link + the PASS are honest NULLS:** with the bounded random-action
  budget NO distal (remote) onset was observed (all onsets cluster in the flash
  region), so the do-contrast could not fire (eff_act=0 throughout) → the remote link
  was NOT confirmed and no level completed. **Reported straight: the exploration
  transfers; the interventional remote attribution + the pass do NOT yet** — the real
  steering-to-operate policy (actually triggering the remote effect) is the standing
  frontier, exactly 223000/225000/227000's named residual.

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (NO Rust; reuses
  the 227 posit/confirm/refute pattern + 210 operate seek/use + 220 nav step + 226
  frustration break + the substrate's hypothesis mint/confirm pattern).
- **`runners/dsl` tracked diff EMPTY** (`term.rs` included) — no tracked file modified;
  the rung is entirely NEW untracked files (seed builder, seed json, world adapter,
  measure, live, test, results) → existing suites are byte-identical BY CONSTRUCTION.
- **Default-OFF byte-identical:** every rule guarded on `game.remote_on==1`
  (`test_every_rule_guarded_on_remote_on`); a graph without the flag mints no posits
  and writes no waypoint (`test_default_off_no_rule_fires`).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped, 0 failed** == AFTER
  **214 passed, 10 skipped, 0 failed** (`results/remote_oracle_{before,after}.txt`).
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET **IDENTICAL** BEFORE
  == AFTER — **23 failed, 277 passed, 5 skipped** both runs, `diff` of the sorted node-id
  lists EMPTY (`results/remote_regress_{before,after}_ids.txt`).
- **New gates:** `tests/test_remote_causal_migrated.py` **16 passed** (headline
  attribution across space; local-only-misses-the-remote-cause; no-intervention-
  confabulates; interventional-do-contrast-decides; exhaustion-drives-exploration;
  causal-prior-never-explores; exploration-precedes-the-causal-model; pass-via-remote;
  action-is-interact-not-local-probe; generality-on-doom ×2; source-audit; seed-
  roundtrip; guarded-on-remote_on; default-off; manifest-shape).
- **Integer-native:** the interventional observations and spatial-separation flag are
  integer 0/1; the causal verdict is exact equality on the do-contrast.
- **Seed round-trips:** `domains/remote_causal_seed.py` → `seeds/remote_causal.json`
  rebuilds byte-stable (`source_match = True`).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the interventional remote-causal MECHANISM
DECISIVELY: the agent goes to the cross out of exhaustion with NO prior causal model
(vs `causal_prior`, CI-separated), DISCOVERS by intervention that the switch affects a
REMOTE thing and attributes B's change ACROSS SPACE (vs `local_only` AND
`no_intervention`, CI-separated 0.926 vs 0.074), and acts on the confirmed link to
pass a genuinely-remote board where the local model cannot — the SAME rules closing
the deferred Doom `lever → door` problem. The world is a CLEAN confounded
causal-discovery world (the interventional facts are OBSERVED by the probe world-model,
the rules produce the verdict); the perfect-vs-zero rates make the Wilson CIs cleanly
separated at N=48 pairs. The LIVE half reports the honest split: the exhaustion-first
exploration loop RUNS on real ls20 (reaches + interacts with the salient object, mints
a posit, onset 30/30) but the remote attribution + the pass are NULLS (no distal remote
change observed in budget; the real operate policy is the standing frontier). Both
reported.

## FILES

- `LS20_REMOTE_PREREG.md` — pre-registration (committed alone, SHA `0f3c5ae909`).
- `domains/remote_causal_seed.py` → `seeds/remote_causal.json` — the generic exhaustion→
  explore→intervene→attribute→act rules (domain-agnostic; default-OFF).
- `worlds/remote_causal.py` — the mechanical adapter + probe/episode drivers (ls20-shaped
  AND doom-shaped boards; the SAME rules).
- `scripts/remote_causal_measure.py` — the powered offline gates + source-audit + the
  226 frustration tie-in + the action trace.
- `scripts/remote_causal_live.py` — the bounded LIVE half.
- `tests/test_remote_causal_migrated.py` — 16 gate tests.
- `results/remote_causal_{powered,live}.json` — the measured numbers.
- `results/remote_{oracle,regress}_{before,after}*` — the discipline baselines.
