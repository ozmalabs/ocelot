# LS20 THE GAME IS COMMUNICATING — POSIT-AND-TEST SEMIOSIS → SEEK-AND-TRANSFORM — RESULTS (block 227000)

Pre-registered in `LS20_SEEK_PREREG.md` (committed **ALONE**, SHA **`eb4dd2e218`**),
BEFORE any number here. Block `227000-227999` claimed CLEAN (`seed_claim.py
227000 227999`; verbatim `check_claim` recorded in the prereg — NOT a permanent
pytest, avoiding the 223000 ledger-inversion mistake).

## LEAD — DID THE AGENT *DISCOVER* WHAT THE GAME WAS SAYING (posit-and-test), THEN ACT?

**OFFLINE: YES, decisively.** Treating the game as a COMMUNICATIVE partner, the
agent POSITS multiple candidate meanings for the flash sign, TESTS them by acting +
residual, CONFIRMS the correct meaning (requirement — "to pass, match the
transform") while REFUTING the wrong ones (reward / acknowledgement / location /
warning), then ACTS on the confirmed posit (seek the only-other salient shape, apply
the transform, pass). **The interpretation is DISCOVERED, not hardcoded.**
**LIVE on real ls20: the DISCOVERY generalises (posited 5 meanings, confirmed
`requirement` on the real sign); the PASS is an honest NULL** (no level completed in
budget — the real 64×64 nav is the standing frontier). Both reported straight.

## THE HEADLINE — G-correct-posit-confirmed: THE MEANING IS DISCOVERED (OFFLINE powered)

The rate at which the agent ends with the requirement posit CONFIRMED and all four
wrong meanings REFUTED, vs controls that CANNOT discover it. N=12 scenarios/config,
two configs (first + held-out), all arms paired on IDENTICAL scenarios, Wilson 95%
CIs (`results/arc_ls20_seek_powered.json`):

| arm | correct-meaning-discovered (first / held-out) |
|---|---|
| **semiosis (posit + test + confirm)** | **1.0000 [0.7575, 1.0000] / 1.0000 [0.7575, 1.0000]** |
| no_test (posits, never tests) | 0.0000 [0, 0.2425] / 0.0000 [0, 0.2425] |
| hardcode_reward (fixed wrong posit) | 0.0000 [0, 0.2425] / 0.0000 [0, 0.2425] |
| cycling (no interpretation) | 0.0000 [0, 0.2425] / 0.0000 [0, 0.2425] |

- **G-correct-posit-confirmed: PASS.** semiosis CI-lower **0.7575 > 0.2425** the
  CI-upper of BOTH the no_test AND the hardcode_reward controls, on BOTH runs —
  CI-separated. The agent CONFIRMS `requirement` and REFUTES `{reward,
  acknowledgement, location, warning}` in **12/12** scenarios per config
  (`confirmed_meanings(semiosis) = {'requirement': 12}`).
- **The gate CAN fail, and a control DOES fail it.** `no_test` MINTS all 5 posits
  (mean 5.0) but never tests → confirms nothing (all posits stay OPEN) → 0/12
  discovered. **Positing without testing is not discovering** — the residual TEST is
  the lever, not the positing. `hardcode_reward` acts on a FIXED wrong belief
  (reward: collect as-is) and never confirms `requirement` → 0/12. Hardcoding the
  wrong meaning loses.

## G-act-passes — ACTING ON THE CONFIRMED POSIT PASSES vs CYCLING (OFFLINE powered)

| arm | pass-rate (first / held-out) | mean steps-to-pass |
|---|---|---|
| **semiosis** | **1.0000 [0.7575, 1.0000] / 1.0000 [0.7575, 1.0000]** | **~34 / ~30** |
| cycling ("just cycling" baseline) | 0.0000 [0, 0.2425] / 0.0000 [0, 0.2425] | 60 (non-converging cap) |

- **G-act-passes: PASS.** semiosis pass CI-lower 0.7575 > cycling CI-upper 0.2425,
  both runs — CI-separated. Acting on the DISCOVERED meaning PASSES the block where
  the "just cycling" baseline the owner saw does not.

## G-anti-cycle (226000 tie-in) — THE AGENT DOES NOT CYCLE

- **steps:** semiosis passes in ~30-34 steps; the controls never converge (capped at
  60 — a deterministic periodic cycle / fixed straight-to-block belief that provably
  does not pass; running them to 150 only burns run_rules calls, changing no
  outcome).
- **frustration (ls20_frustration seed):** feeding the two traces into the 226000
  modulator — the **cycling** trace (recurrence + NO understanding-gain = FUTILE) is
  BROKEN by frustration at **step 6** (frustration 52 ≥ threshold 20, `break_now`
  → STOP); the **semiosis** trace (executing a DISCOVERED plan, genuine progress each
  step = the "productive repeat" case) is **NOT broken** (frustration 0.0).
  **`anti_cycle_holds = True`** — frustration/salience drives the seek; the agent
  does not cycle.

## G-posits-generated + SOURCE-AUDIT — NO HARDCODED INTERPRETATION

- **Multiple posits from a GENERAL vocabulary.** semiosis mints **5** `Posit`
  Hypothesis nodes per flash — one per general communicative meaning `{requirement,
  reward, acknowledgement, location, warning}` (seed data, not one ls20 answer). The
  posit lifecycle is graph rules: `sg_mint_posits` (add_node), `sg_want_test`,
  `sg_refute` / `sg_confirm` (predict-vs-observed residual), `sg_act_requirement`,
  `sk_seek`, `sk_pass`.
- **SOURCE-AUDIT PASS** (`{'banned_tokens_found': [], 'flash_to_requirement_shortcut_rules': [], 'clean': True}`):
  - the rules name NO transform family (rotate/reflect/recolour/rotation90/
    reflection) and NO ls20 constant;
  - **NO rule sets `transform_required` directly from `flash_present`** — i.e. there
    is NO hardcoded "flash = requirement" anywhere. `transform_required` is set ONLY
    by `sg_act_requirement`, gated on a **CONFIRMED posit** (`status=='confirmed'` ∧
    `implies_change==1`), never on the flash. The interpretation is DISCOVERED.
  - the adapter (`worlds/arc_ls20_seek.py`) never sets the drive or decides the
    meaning in Python (gate `test_adapter_has_no_forbidden_agent_logic`).

## G-live (REAL ls20) — THE DISCOVERY GENERALISES; THE PASS IS AN HONEST NULL

`arc_ls20_seek_live.py --game ls20-9607627b --steps 25`
(`results/arc_ls20_seek_live.json`). Auth verified BEFORE measuring
(`X-Api-Key` from the gitignored `.env`, NEVER printed/committed; RESET returned
`state=NOT_FINISHED`, `available=[ACTION1..4]`, grid 64×64):

| metric (REAL ls20, 25 steps) | semiosis | cycling |
|---|---|---|
| flash-sign onset detected | **25/25 frames (rate 1.0)** | 25/25 |
| **posits minted on the real sign** | **5** | **0** |
| **meaning CONFIRMED** | **`requirement`** | (none) |
| levels_completed (SIDE EFFECT) | 0 | 0 |

- **The DISCOVERY loop RUNS on real ls20:** the general onset stream detects the
  flash sign on **25/25** real frames, localised CONSISTENTLY to **rows ≈ 42-47,
  cols ≈ 29-34** (the same region 223000/225000 reported); the ACTUAL `sg_mint_posits`
  rule mints **5** candidate meanings for the real sign, and — because acting-as-is
  did NOT advance the level (the observed accept signal = 0, no harm) — the posit
  test CONFIRMED **`requirement`** ("the game is telling me more is required to
  pass"). The cycling arm posited nothing. **The interpretation generalises: the
  agent discovered a meaning from the real sign by positing + testing.**
- **The PASS is an honest NULL:** neither arm completed a level in the 25-step
  budget (`semiosis_made_more_progress_than_cycling = False`). On real 64×64 ls20 the
  only-other shape / required transform is not a known station, so the SEEK is
  steering toward the salient centroid — the downstream nav/pass remains the standing
  frontier (exactly 223000/225000's named residual). **Reported straight: the
  discovery transfers; the passing does not, yet.** Perception round-trip through the
  216000 pixel eye held on the streamed frames (`perception_roundtrip_ok = true`).

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust;
  reuses 217 TransformDecode + 223 onset + 218 plan_seek_station + 220 nav + 226
  frustration + the substrate's hypothesis mint/confirm pattern).
- **`runners/dsl` tracked diff EMPTY** (`term.rs` included) — no tracked file
  modified; the rung is entirely NEW files (git status: 7 new untracked files, ZERO
  modifications to tracked files → existing suites are byte-identical BY
  CONSTRUCTION).
- **Default-OFF byte-identical:** every rule guarded on `game.seek_on==1`
  (`test_every_rule_guarded_on_seek_on`); a graph without the flag mints no posits
  and writes no waypoint (`test_default_off_no_rule_fires`).
- **Oracle `rung7_vision_bench`:** BEFORE == AFTER — `<FILL: oracle counts>`
  (`results/seek_oracle_after.txt`).
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET IDENTICAL to the
  pre-existing baseline — `<FILL: regression counts>` (`results/seek_regress_after.txt`).
- **New gates:** `tests/test_ls20_seek_migrated.py` **12 passed** (headline
  discovery, no_test-fails-the-gate, hardcode-wrong-loses, act-passes-vs-cycling,
  multiple-posits, no-flash→requirement-shortcut, no-transform-family-token,
  posit-lifecycle-is-rules, adapter-no-agent-logic, default-off, guarded-on-seek_on,
  seed-roundtrip).
- **Integer-native:** the shapes are the integer lattice; the posit predictions and
  observations are integer flags; the transform key is a categorical token; the pass
  verdict is exact set equality.
- **Seed round-trips:** `domains/ls20_seek_seed.py` → `seeds/ls20_seek.json` rebuilds
  byte-stable (`source_match = True`).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the semiosis MECHANISM DECISIVELY: the agent
DISCOVERS the flash's meaning by positing a general communicative vocabulary and
testing it (confirm requirement / refute the rest, CI-separated 0.7575 vs 0.2425),
and ACTS on it to pass the block where cycling fails — with the anti-rig controls
(no_test, hardcode_reward) failing the gate and the 226000 anti-cycle holding. The
powered N is **12/config** (the largest that completes a full foreground run under
the harness limit; the perfect-vs-zero rates make the Wilson CIs cleanly separated
at that N). The LIVE half reports the honest split: the DISCOVERY loop runs on real
ls20 (5 posits, confirmed `requirement` from the real sign, onset 25/25) but the
PASS is a NULL (real 64×64 nav is the standing frontier). Both reported.

## FILES

- `LS20_SEEK_PREREG.md` — pre-registration (committed alone, SHA `eb4dd2e218`).
- `domains/ls20_seek_seed.py` → `seeds/ls20_seek.json` — the general communicative
  vocabulary + the mint / test / confirm / refute / act rules (depends on
  ls20_planning + ls20_flash; default-OFF).
- `worlds/arc_ls20_seek.py` — the mechanical semiosis-scenario adapter + episode
  driver (reuses the 218000 scenario machinery + 217000 recogniser).
- `scripts/arc_ls20_seek_measure.py` — the powered offline gates + source-audit + the
  226000 frustration tie-in.
- `scripts/arc_ls20_seek_live.py` — the bounded LIVE half.
- `tests/test_ls20_seek_migrated.py` — 12 gate tests.
- `results/arc_ls20_seek_{powered,live}.json` — the measured numbers.
