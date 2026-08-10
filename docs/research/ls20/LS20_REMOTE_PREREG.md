# LS20 REMOTE CAUSATION — "the switch affects a remote thing" — PRE-REGISTRATION (block 228000)

Committed **ALONE**, BEFORE any number. Block `228000-228999` claimed CLEAN.
`check_claim` output recorded verbatim below (NOT a permanent pytest — it inverts
once the ledger row lands; avoiding the 223000 ledger-inversion mistake).

## THE PROBLEM (owner)

Block 227000 proved the agent DISCOVERS the flash's meaning (posit-and-test
semiosis → "requirement"). But its ACTIONS are all LOCAL: `sg_want_test` probes the
block as-is; `sk_seek` routes to the other shape and applies the transform as a
LOCAL op. It models NO remote causation. The real ls20 mechanic: the only-other
salient thing is a CROSS = a SWITCH; interacting with it affects a REMOTE thing (the
avatar's carried shape / a block elsewhere). This is the DEFERRED DOOM PROBLEM
("switch here → door opens there"). It is why 227's live run discovered "requirement"
but passed 0 levels — it had no non-local link `interact-cross → my-shape-rotates →
pass-block`.

## THE CHICKEN-AND-EGG FIX (owner refinement, folded in BEFORE measuring)

You CANNOT posit "cross → remote effect" before you have been to the cross and
interacted with it. So EXPLORATION must come FIRST, driven by EXHAUSTION + SALIENCE,
independent of any causal hypothesis. The corrected loop:

1. **Exhaustion-driven exploration (the driver — NO causal model needed).** The agent
   tries its known options (probe the block as-is); they fail / stop yielding
   understanding; the futile cycle is broken by 226 frustration; it enumerates
   remaining SALIENT things and the cross is the ONLY unexplored salient option → GO
   THERE. This decision reads ONLY exhaustion + salience-novelty (least/never-visited
   salient object), NEVER a prior belief about what the cross does.
2. **On arrival, intervene → discover the remote-causal link (the 228 core).** Interact
   with the cross → observe the remote effect at B → POSIT + CONFIRM the remote-causal
   link BY INTERVENTION (act→effect vs no-op→no-effect), attributing B's change to the
   remote action A ACROSS SPACE. The causal model is BORN here, from the interaction —
   it was not required to get here.
3. **Act on the confirmed link → pass.** Interact with the cross to obtain the needed
   rotation → B matches → pass the block.

## THE MECHANISM (interventional causal discovery ACROSS SPACE; graph-native)

Generic, domain-agnostic graph nodes (rules name NO ls20/doom constant):
- `SalientObject{obj_id, r, c, is_local, visited, interacted, eff_act, eff_noop,
  passive_cooccur, link_status}` — a thing that can be sought and acted on. `is_local`
  is a PERCEPTUAL fact (co-located with the remote target B, or spatially separated);
  it is NOT a causal label.
- `RemoteCausalPosit` — a posited link `SalientObject → B` (a Hypothesis), minted only
  AFTER interaction.
- The remote target B is the block/door; its change is observed as `eff_*`.

The INTERVENTIONAL do-contrast (the teeth): for a candidate C the adapter runs two
real probes and OBSERVES B —
- `eff_act[C]`  = did B change when the agent INTERVENED on C (do(C))?
- `eff_noop[C]` = did B change when the agent did NOT intervene on C (world otherwise ran)?
A link C→B is CONFIRMED iff `eff_act==1 ∧ eff_noop==0` (intervention makes the
difference — rules out coincidence and local confounds); REFUTED iff `eff_act==eff_noop`
(no difference → C does not control B). Location-agnostic by construction: the remote
cross is confirmed ACROSS SPACE.

Every decision is a RULE (`remote_causal.json`, built by `domains/remote_causal_seed.py`):
`rc_exhausted` (→ explore_mode), `rc_seek_novel_salient` (→ waypoint to the unvisited
salient object; visited+salience only), `rc_posit_link`, `rc_confirm_interventional`,
`rc_refute_interventional`, `rc_confirm_passive` (no-intervention control),
`rc_act_seek_confirmed` (→ seek the confirmed remote cause), `rc_pass`, plus the control
rules. Guarded on `game.remote_on==1` (default-OFF, byte-identical) + `game.arm`. The
adapter (`worlds/remote_causal.py`) only writes perception facts, runs the probes as
world physics, steps toward the rule-chosen waypoint, and applies the remote effect on
interact. NO Python decides the causal link or the move.

## ARMS

- `remote` — the full treatment: exhaustion-driven explore + interventional attribution
  (full spatial scope) + act.
- `local_only` — same explore + interact, but attribution restricted to LOCAL-scope
  candidates (`is_local==1`): it can only attribute B's change to something at B's
  location, so it NEVER posits the remote cross → cannot attribute/act across space.
  (Also serves as the 227-style local model for G-pass-via-remote.)
- `no_intervention` — explores and reaches the cross but performs NO do-probe; attributes
  by passive co-occurrence (`passive_cooccur`) → confabulates a link without intervention.
- `causal_prior` — does NOT do exhaustion-driven exploration; only moves toward an object
  it ALREADY has a causal hypothesis for. It never forms a hypothesis for an un-visited
  object → never goes → cycles forever.

## SCENARIO FAMILIES (a proper confounded causal-discovery world)

- **Family A (confounded remote):** the REMOTE cross A truly controls B; a LOCAL distractor
  L at B's location spuriously CO-OCCURS with B's change but does NOT control it. Correct
  verdict = confirm A→B (remote, across space) AND NOT confirm L→B.
- **Family B (coincidence):** B changes on its own; the cross is present but NOT causal.
  Correct verdict = confirm NOTHING (refuse the link).

The `eff_act/eff_noop/passive_cooccur` are OBSERVED by the adapter running real probes on
a tiny world-physics model of the family's ground truth — not hand-written verdicts.

## GATES (pre-registered; measure-first)

- **G-exhaustion-drives-exploration (NEW):** `remote` navigates to the only-remaining-salient
  object after exhausting its known options, WITH NO prior causal model, CI-separated ABOVE
  `causal_prior` (which never forms a hypothesis for the un-visited object → never goes).
  Predict: reach-cross rate `remote` = 1.0 vs `causal_prior` = 0.0, CI-separated.
- **G-remote-attribution (HEADLINE — the deferred-Doom crux):** `remote` correctly attributes
  the remote effect at B to the interaction at A across space — CI-separated ABOVE a
  LOCAL-ONLY control AND a no-intervention/coincidence control. Scored PER MATCHED PAIR
  (Family A instance ∧ Family B instance both correct — requires BOTH spatial reach AND
  interventional discipline). Predict: `remote` = 1.0 vs `local_only` = 0.0 (fails Family A —
  misses the remote cause) vs `no_intervention` = 0.0 (fails Family B — confabulates),
  CI-separated on TWO configs (first + held-out). Per-family decomposition also reported.
- **G-action-furthers-posit:** the action taken to further/confirm the posit is INTERACTING
  WITH THE CROSS + observing the remote effect (measured: `remote` navigates to the cross,
  interacts, attributes the remote change) — NOT a local block-probe.
- **G-pass-via-remote:** the full loop (exhaust → explore → intervene → discover → act) PASSES
  on a genuinely-REMOTE board (the transform provider is a remote SWITCH, no local station),
  vs the 227-style `local_only` model which CANNOT pass when the effect is non-local.
  Predict: pass `remote` = 1.0 vs `local_only` = 0.0, CI-separated.
- **G-general (close the deferred Doom problem):** the SAME `remote_causal` RULES attribute
  `switch → remote effect` on BOTH an ls20-shaped board (cross → shape rotation) AND a
  Doom-shaped board (lever → remote door), demonstrating domain-agnosticism. Source-audit:
  the rules name NO ls20/doom/cross/lever/door/rotation constant.
- **G-graph-native:** the exploration decision, the remote-causal posit, the interventional
  attribution, and the act are RULES; the adapter is mechanical. Source-audit: NO hardcoded
  `cross→rotation`, no Python deciding the causal link or the move; the go-to-cross decision
  reads ONLY visited/salience/exhaustion state.
- **G-discipline:** integer-native; default-OFF byte-identical (all rules guarded on
  `remote_on==1`; a graph without the flag fires nothing); canonical `.so` md5
  `793ce09ed498a749abb79aeaea44b92e` UNCHANGED (NO Rust — reuse 227 posit + sd-loop + 220
  nav + 210 operate + 226 frustration; if a new Rust Term is truly needed, STOP + report);
  `term.rs` + whole `runners/dsl` tracked diff EMPTY; oracle `rung7_vision_bench` BEFORE==AFTER;
  34-file `per_area_settlement_regression` failing NODE-ID SET identical BEFORE==AFTER;
  `source_match` (seed builder → json round-trips) reported.
- **G-live (real ls20, honest):** does the agent interact with the cross, attribute the remote
  effect, and make progress / pass? Report the real number or an honest NULL + what it DID do
  (navigate to the cross? posit + confirm the remote link?). Auth verified BEFORE; `ARC_API_KEY`
  in `.env` — NEVER printed/committed; `.so` never committed; STOP+report if API unreachable;
  NEVER fabricate. State fresh-API vs deterministic-replay.

## FALSIFICATION BAR

Remote causation is GENERAL (interventional cause→effect across SPACE — the same structure
as Doom lever→door, the deferred problem — not an ls20 hack); the causal link is DISCOVERED by
intervention (not hardcoded); attribution across space is MEASURED vs a local-only control AND
a no-intervention control; and the go-to-cross is driven by exhaustion+salience with NO prior
causal model (measured vs `causal_prior`). If the treatment cannot beat BOTH attribution
controls CI-separated, OR the go-to-cross needs a prior causal hypothesis, OR the machinery is
ls20-specific (fails on the Doom board), the block FAILS.

## check_claim (verbatim, recorded at prereg time — NOT a pytest)

```
$ python3 scripts/seed_claim.py 228000 228999
SEED CLAIM 228000-228999: CLEAN -- no collision DETECTED.
  Scope: 938 files with seed sinks; 638 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
  exit 0
```

## FILES (to be created)

- `LS20_REMOTE_PREREG.md` — this pre-registration (committed alone).
- `domains/remote_causal_seed.py` → `seeds/remote_causal.json` — the generic exhaustion→
  explore→intervene→attribute→act rules (default-OFF).
- `worlds/remote_causal.py` — the mechanical adapter + probe/episode drivers (ls20-shaped
  AND doom-shaped boards; same rules).
- `scripts/remote_causal_measure.py` — the powered offline gates + source-audit + 226 tie-in.
- `scripts/remote_causal_live.py` — the bounded LIVE half.
- `tests/test_remote_causal_migrated.py` — the gate tests.
- `results/remote_causal_{powered,live}.json`, `results/remote_{oracle,regress}_{before,after}*`.
