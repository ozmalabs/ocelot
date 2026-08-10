# LS20 PERFORM-THE-ACTION-ON-THE-CROSS — RESULTS (block 230000)

Pre-registered in `LS20_OPERATE_PREREG.md` (committed **ALONE**, SHA `da88b6ef1c`),
BEFORE any number here. Block `230000-230999` claimed CLEAN (`seed_claim.py 230000
230999`; verbatim `check_claim` recorded in the prereg — NOT a permanent pytest).

## THE OWNER INSIGHT (the point of this block)

Block 229's live run REACHED and "interacted with" the cross but observed **0 distal
change** — because "interacted" meant co-located / bumped; the agent NEVER issued the
game's ACTION (use / select) ON the cross. A switch fires when ACTUATED, not walked
into. Owner: *"it may need to perform the 'action' on the cross."*

**The fix EXTENDS the exhaustion principle from the OBJECT space (226/228 — go to the
only un-visited salient object) to the ACTION space:** at the reached salient object,
TRY EVERY available game action on it — the movement actions AND the interact/use/
select action (like block 210's `op_use`) — because "I've tried everything" is not
complete until it has tried *acting on* the thing, not just moving into it.
**DISCOVER which action actuates it** (the one that produces an observable remote
change) — NOT hardcode "ACTION5 = use". Then 229's observe-and-ground grounds the
effect the instant it appears.

## THE HEADLINE — G-discover-operate-action: THE ACTUATOR IS DISCOVERED BY EXHAUSTING THE ACTION SPACE

Pair-scored across Family A (exactly one NON-movement action actuates the object →
discover THAT action) ∧ Family B (no action actuates / inert object → discover
NOTHING). N=24/family, Wilson 95% CIs (`results/remote_operate_powered.json`):

| policy | pair-discover (A∧B) | Family A (discover the actuator) | Family A ground (via 229) | pass |
|---|---|---|---|---|
| **exhaust_actions** | **1.000 [0.862, 1.000]** | **1.000 [0.862, 1.000]** | **1.000 [0.862, 1.000]** | **1.000 [0.862, 1.000]** |
| movement_only (control) | 0.000 [0.000, 0.138] | 0.000 [0.000, 0.138] | 0.000 [0.000, 0.138] | 0.000 [0.000, 0.138] |

- **G-discover-operate-action: PASS.** `exhaust_actions` pair CI-lower **0.862 >
  0.138** the `movement_only` CI-upper — CI-separated. By exhausting the ACTION space
  on the object, the agent DISCOVERS the action that actuates it (produces an
  observable remote change). The `movement_only` control tries only the 4 movements /
  bumps the object → never issues the interact/use action → never actuates → observes
  no change → discovers NOTHING → cannot ground → cannot pass.
- **The actuator is DISCOVERED, not given.** The world's true operate action is a
  RANDOMIZED non-movement action per scenario (ACTION5 or ACTION6); the agent tries
  every action in ordinal order and reads the OBSERVED outcome. The discovered action
  EQUALS the true actuator and is minted as graph data
  `Operates{action, object, effect}` (`test_discovered_action_is_the_true_operate_action_and_non_movement`).
  Source-audit: `ro_discover_operate` reads `oc.remote_changed` + joins the action id
  as a Var attr — it names **NO Lit action id** and does **NOT read `is_movement`**
  (the actuator is discovered from the observed CHANGE, not its kind):
  `{'hardcoded_action_id_in_logic': [], 'discover_reads_observed_remote_changed':
  True, 'discover_joins_action_id_var': True, 'discover_reads_is_movement': False,
  'clean': True}`.
- **Family B refusal.** Exhausting the WHOLE action space on an inert object produces
  no remote change from ANY action → discovers nothing, grounds nothing (correct
  refusal) — `test_discovery_refuses_when_no_action_actuates`.

## G-exhaust-actions — "tried everything" now includes ACTING on the thing

The exhaustion → action-space extension, measured
(`results/remote_operate_powered.json`, `non_movement_issued_rate`):

| policy | issues the NON-movement (interact/use) action at the object |
|---|---|
| **exhaust_actions** | **1.000 [0.862, 1.000]** |
| movement_only (control) | 0.000 [0.000, 0.138] |

- **G-exhaust-actions: PASS**, CI-separated. `exhaust_actions` issues the non-movement
  interact/use action ON the object (rate 1.000); `movement_only` never does (0.000,
  `test_exhaust_actions_issues_the_non_movement_action_control_never_does`). The
  exhaustion covers the full action space in ordinal order — on Family B (nothing
  actuates) it issues ALL six actions `[ACTION1..4, ACTION5, ACTION6]`
  (`test_exhaustion_covers_the_full_action_space_in_order`). This is the direct tie to
  226/228 object-space exhaustion: the SAME "I've tried everything" principle, one
  level down — from the object space to the action space.

## G-elicits-and-grounds + G-pass — the full loop closes, composing 229 UNCHANGED

The 229 `remote_causal_ground` seed is loaded UNCHANGED alongside the 230
`remote_operate` seed on one Game node (arm="observe" drives 229; op_policy drives
230). When `exhaust_actions` issues the actuating action, the adapter writes the
`Observation{interact=1, remote_changed=1}` that 229's `rcg_ground` consumes → mints
`causes(object, effect)`; `rcg_knows_and_acts` → `rcg_pass` close the loop.

| policy | grounded (229) | win (route → operate → pass) |
|---|---|---|
| **exhaust_actions** | **1.000 [0.862, 1.000]** | **1.000 [0.862, 1.000]** |
| movement_only | 0.000 [0.000, 0.138] | 0.000 [0.000, 0.138] |

- **G-elicits-and-grounds: PASS**, CI-separated. Once the operate action is discovered
  and produces an observed change, 229 grounds the causal fact end-to-end (reach →
  exhaust actions → discover operate → elicit → ground → know).
- **G-pass: PASS**, CI-separated. With the discovered operate action + the grounded
  effect, `exhaust_actions` PASSES; the `movement_only` 229-null baseline never
  actuates → never grounds → never passes
  (`test_exhaust_actions_passes_movement_only_cannot`).

## G-live (REAL ls20) — THE OWNER'S HYPOTHESIS TESTED STRAIGHT: an HONEST NULL with per-action detail

`remote_operate_live.py --game ls20-9607627b --settle 6 --reps 2`
(`results/remote_operate_operate_live.json`). **FRESH-API** (not replay). Auth
verified BEFORE (`ARC_API_KEY` from the gitignored `.env`, NEVER printed/committed;
RESET `state=NOT_FINISHED`, grid 64×64, `available=[ACTION1..4]`). Unlike 229 (which
cycled ONLY the movement actions), 230 **issues each candidate action ON the cross —
the movements AND the interact ACTION5 AND the coordinate click ACTION6 (targeted at
the cross locus)** — and observes, per action, whether a DISTAL remote change appears.

The cross localised CONSISTENTLY to **(row 47, col 34)** (the 223/225/227/228/229
region). Per action (identical across both reps):

| action ON the cross | issued_ok (server accepted) | any change at all | distal (remote) change | onsets |
|---|---|---|---|---|
| ACTION1 (move) | true | **true** | false | 15 |
| ACTION2 (move) | true | **true** | false | 15 |
| ACTION3 (move) | true | **true** | false | 15 |
| ACTION4 (move) | true | **true** | false | 15 |
| **ACTION5 (interact/use)** | **true** | **FALSE** | false | **0** |
| **ACTION6 (click AT the cross locus)** | **true** | **FALSE** | false | **0** |

- **The honest verdict is case (b): NO action on the cross produced an observable
  remote change — and this is a DISTINCT, better-resolved finding than 229's null.**
  229 never tried the interact/use action; 230 did EXACTLY what the owner suggested.
  The result, measured straight: **the interact ACTION5 and the coordinate click
  ACTION6 (targeted directly at the cross) are ACCEPTED by the server but are
  completely INERT in this state — 0 onsets, 0 change, local or distal.** The movement
  actions change the frame locally (the agent moves, 15 onsets each) but produce no
  DISTAL change. So performing the game ACTION on the cross did **not** trigger an
  observable remote mechanic this budget → nothing to ground.
- **What this rules in / out (honest).** The owner's hypothesis — "issue the ACTION on
  the cross" — was the right thing to TRY, and it is now MEASURED: the specific
  mechanism (ACTION5/ACTION6-on-the-cross → remote change) does **not** hold on this
  game/budget; the interact actions do nothing observable here (not merely "not
  distal" — nothing at all). The ls20 mechanic is triggered some OTHER way. Two
  measured facts also worth recording: (1) ACTION5/ACTION6 are NOT in the game's
  reported `available_actions` (only ACTION1..4 are) yet the server ACCEPTS them as
  silent no-ops; (2) the grounding pipeline **would ground the instant a distal change
  is observed** (proven decisively offline) — it was not, this budget.
- **Residual (named, not patched).** ACTION5 (bare interact) was issued without a
  guarantee the agent BODY is co-located with the cross; ACTION6 clicks the cross
  locus DIRECTLY (location handled) and is still inert. The finer test — deliberately
  STEER the body onto the cross, THEN ACTION5 — is the standing frontier, but the
  location-targeted ACTION6-on-cross already tests "act AT the cross" and returns the
  null. Reported straight; MEASURED, not assumed.

## G-graph-native / SOURCE-AUDIT

`source_audit` = `{'banned_tokens_found': [], 'hardcoded_action_id_in_logic': [],
'discover_reads_observed_remote_changed': True, 'discover_joins_action_id_var': True,
'discover_reads_is_movement': False, 'clean': True}`:

- enumerate-try-discover + operate + ground are RULES; the adapter is mechanical
  (enumerate the available actions as `GameAction` nodes; issue the RULE-chosen
  `g.try_action` AT the object; perceive the real before→after; write the
  `ActionOutcome` + 229 `Observation`; mark the issued action `tried` — bookkeeping,
  not a decision);
- the rule logic names **NO** ls20/doom/cross/lever/door/rotation/shape constant AND
  **NO** action id (ACTION1..7) — the actuating action id + the effect kind are
  carried through from the OBSERVED `ActionOutcome`. The discovery reads
  `remote_changed`, not `is_movement`: the actuator is discovered from the observed
  CHANGE, never its kind (`test_discover_rule_reads_observed_outcome_not_hardcoded_action_id`).

## DISCIPLINE

- **Canonical `.so` md5 `330738ef…` UNCHANGED** (NO Rust; reuses the 210 operate
  seek/use, the 228 reach, the 229 ground, the 220 nav, the substrate's node/edge
  mint pattern). `runners/dsl` tracked diff EMPTY (`term.rs` included) — no tracked
  file modified; the rung is entirely NEW untracked files → existing suites are
  byte-identical BY CONSTRUCTION.
- **Default-OFF byte-identical:** every rule guarded on `game.operate_on==1`
  (`test_every_rule_guarded_on_operate_on`); a graph without the flag mints no
  Operates node and selects no action (`test_default_off_no_rule_fires`).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped, 0 failed** ==
  AFTER **214 passed, 10 skipped, 0 failed** (`results/operate_oracle_{before,after}.txt`).
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET **IDENTICAL**
  BEFORE == AFTER — **23 failed, 278 passed, 5 skipped** both runs; `diff` of the
  sorted node-id lists EMPTY (`results/operate_regress_{before,after}_ids.txt`).
  (These 23 are the pre-existing reds this environment carries; 230 touches none.)
- **New gates:** `tests/test_remote_operate_migrated.py` **15 passed**
  (discover-vs-movement-only; discovered==true-actuator + non-movement + Operates
  edge; refuse-on-inert; issues-non-movement-vs-control; full-space-in-order;
  elicits-and-229-grounds; movement-only-never-grounds; passes-vs-control;
  discover-reads-observed-not-hardcoded source-audit; no-domain-tokens;
  observe_change-is-a-real-diff; guarded-on-operate_on; default-off; seed-roundtrip
  source_match; manifest-shape).
- **Integer-native:** the outcomes are integer 0/1; the discovery verdict is exact
  equality on the observed `remote_changed`.
- **Seed round-trips:** `domains/remote_operate_seed.py` → `seeds/remote_operate.json`
  rebuilds byte-stable (`source_match = True`).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the EXHAUST-THE-ACTION-SPACE → DISCOVER-THE-
ACTUATOR MECHANISM decisively: the agent, at the reached object, tries EVERY available
action (the interact/use action too, vs `movement_only` which never does,
CI-separated), DISCOVERS the actuating action from the OBSERVED remote change (not a
hardcoded id; randomized actuator; source-audit clean), the elicited change flows into
229's UNCHANGED grounding (CI-separated vs the control), and the full loop PASSES (vs
the 229-null `movement_only`, CI-separated). The world is a clean action-discovery
world (only the true actuator, at the object, produces the observed change; the rules
produce the verdict). The LIVE half tests the OWNER'S HYPOTHESIS STRAIGHT on real
ls20: it issued the interact ACTION5 AND the coordinate click ACTION6 ON the cross —
the exact actions 229 never tried — and reports the honest null with per-action
detail: those actions are ACCEPTED but INERT (0 onsets, 0 change) and the movement
actions produce only local change, so no action on the cross elicited a remote change
this budget; the mechanic is triggered some other way. Both reported.

## FILES

- `LS20_OPERATE_PREREG.md` — pre-registration (committed alone, SHA `da88b6ef1c`).
- `domains/remote_operate_seed.py` → `seeds/remote_operate.json` — the
  action-exhaustion + discover-operate rules (domain-agnostic; default-OFF).
- `worlds/remote_operate.py` — the mechanical adapter + episode drivers (composes 230
  + the unchanged 229 on one Game node).
- `scripts/remote_operate_measure.py` — the powered offline gates + source-audit.
- `scripts/remote_operate_live.py` — the bounded LIVE half (exhaust the action space
  ON the cross, incl. ACTION5/ACTION6).
- `tests/test_remote_operate_migrated.py` — 15 gate tests.
- `results/remote_operate_{powered,operate_live}.json` — the measured numbers.
- `results/operate_{oracle,regress}_{before,after}*` — the discipline baselines.
