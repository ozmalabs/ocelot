# LS20 PERFORM-THE-ACTION-ON-THE-CROSS — PRE-REGISTRATION (block 230000)

Committed **ALONE**, BEFORE any measurement. This file fixes the mechanism, the
gates, the controls, and the discipline. Numbers land only in
`LS20_OPERATE_RESULTS.md`.

## SEED CLAIM (verbatim `check_claim`, recorded here — NOT a permanent pytest)

```
$ python scripts/seed_claim.py 230000 230999
SEED CLAIM 230000-230999: CLEAN -- no collision DETECTED.
  Scope: 945 files with seed sinks; 646 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block `230000-230999` claimed CLEAN.

## THE OWNER INSIGHT (the point of this block)

Block 229's live run REACHED and "interacted with" the cross but observed **0
distal change** — because "interacted" meant co-located / bumped; the agent
NEVER issued the game's ACTION (use / select) ON the cross. A switch fires when
ACTUATED, not walked into.

Owner: *"it may need to perform the 'action' on the cross."*

**The fix EXTENDS the exhaustion principle from the OBJECT space (226/228 — go to
the only un-visited salient object) to the ACTION space:** at the reached salient
object, TRY EVERY available game action on it — the movement actions AND the
interact/use/select action (like block 210's `op_use`) — because "I've tried
everything" is not complete until it has tried *acting on* the thing, not just
moving into it. **DISCOVER which action actuates it** (the one that produces an
observable remote change) — NOT hardcode "ACTION5 = use". Then 229's
observe-and-ground grounds the effect the instant it appears.

## THE MECHANISM (graph-native; every decision a rule; no Rust)

At the reached object: enumerate the AVAILABLE game actions (adapter writes a
`GameAction{action_id, ordinal, is_movement, tried}` node per available action —
`is_movement` is a mechanical property of the ARC-AGI-3 action set: ACTION1-4 are
directional moves, ACTION5/6 are interact/select/click). TRY each on the object;
the adapter issues the rule-chosen action AT the object, OBSERVES the real
before→after remote change, and writes an `ActionOutcome{action_id,
remote_changed, effect_kind}` (all OBSERVED) plus a 229 `Observation{interact,
remote_changed, cause_id, effect_kind}`.

New seed `remote_operate` (default-OFF on `game.operate_on==1`), composed WITH the
unchanged 229 `remote_causal_ground` seed on ONE Game node:

- `ro_try_action` (policy `exhaust_actions`) — exhaust the ACTION space: match the
  min-ordinal UNTRIED `GameAction` (a `Not Exists` "no untried action with smaller
  ordinal" guard makes exactly ONE fire per pass), set `g.try_action`, mark it
  tried. Tries the interact/use action too.
- `ro_try_movement` (policy `movement_only`, the CONTROL) — same, but restricted to
  `is_movement==1` actions: it NEVER issues the non-movement interact/use action.
- `ro_discover_operate` (HEADLINE) — an `ActionOutcome` with `remote_changed==1`
  (an OBSERVED remote change) → mint `Operates{action, object, effect}` node +
  `operates` edge + set `g.operate_action = <the action id from the outcome>`,
  `g.discovered=1`. The actuating action is **DISCOVERED from the observed
  outcome**, never a hardcoded action id (mint-once guard).

The 229 rules are REUSED UNCHANGED: the `Observation` the adapter writes when the
use action actuates (`interact=1, remote_changed=1`) is consumed by 229's
`rcg_ground` → mints the persistent `causes(object, effect)` fact; `rcg_knows_and_acts`
→ `rcg_pass` close the loop. The `movement_only` policy never issues the use action
→ never observes a remote change → 230 discovers nothing AND 229 grounds nothing →
never passes.

The world's GROUND TRUTH is which action actuates (a per-scenario NON-movement
action, RANDOMIZED across ACTION5/ACTION6 so the agent must DISCOVER it, not read a
constant). The world actuates the remote thing iff the issued action == the true
operate action AND the agent is at the object. The agent never sees the truth; it
tries and reads the OBSERVED outcome.

## GATES (pre-registered; measure-first; Wilson 95% CIs; CI-separation = lower>upper)

- **G-discover-operate-action (HEADLINE):** by exhausting the action space on the
  object, the `exhaust_actions` policy DISCOVERS the action that actuates it
  (produces an observable remote change), CI-separated above the `movement_only`
  control (tries only movements → never actuates → no change → discovers nothing).
  Pair-scored across Family A (exactly one non-movement action actuates → discover
  THAT action) ∧ Family B (no action actuates / inert object → discover NOTHING).
  Source-audit: `ro_discover_operate` names NO action id — the id flows from the
  OBSERVED `ActionOutcome`.
- **G-exhaust-actions (the exhaustion → action-space extension):** "tried
  everything" includes issuing the non-movement interact/use action ON the object.
  Measured: the `exhaust_actions` policy issues the non-movement action at the
  object (rate 1.0); the `movement_only` control never does (rate 0.0). Ties to
  226/228 object-space exhaustion.
- **G-elicits-and-grounds (composes with 229):** once the operate action is
  discovered and produces an observed change, 229's `rcg_ground` grounds
  `causes(object, effect)` — the full loop closes (reach → exhaust actions →
  discover operate → elicit → ground → know). Measured end-to-end (Family A).
- **G-pass:** with the discovered operate action + grounded effect, the
  `exhaust_actions` agent PASSES vs the 229-null baseline (`movement_only`, never
  actuates → never grounds → never passes). CI-separated.
- **G-live (the real test of the owner's hypothesis, HONEST):** on real
  ARC-AGI-3 ls20 — does issuing the interact/use action (the non-movement ACTION)
  on the cross produce an OBSERVABLE remote change (which 229 then grounds)?
  Reported STRAIGHT: (a) some action actuates the cross → observable change →
  grounded (hypothesis CONFIRMED); OR (b) NO available action on the cross produces
  any observable change in budget → that NULL + EXACTLY what each action did (the
  mechanic is triggered some other way — a distinct honest finding). MEASURE which
  action, if any, actuates it — do NOT assume. Auth verified BEFORE; `ARC_API_KEY`
  from the gitignored `/home/matt/ozma/internal/.env`, NEVER printed/committed;
  `.so` never committed; STOP+report if API unreachable; NEVER fabricate. State
  fresh-API vs replay.
- **G-graph-native / source-audit:** enumerate-try-discover + operate + ground are
  RULES; the adapter is mechanical (issue the rule-chosen action, perceive the
  result, write facts). Source-audit: NO hardcoded operate-action id in the rule
  logic; NO Python deciding the actuator; NO domain token (cross/rotation/ls20/
  doom/lever/door) in the `remote_operate` rule where/effects.
- **G-discipline:** integer-native (outcomes are 0/1; discovery is exact equality
  on the observed `remote_changed`); **default-OFF byte-identical** (every rule
  guarded on `game.operate_on==1`; a graph without it fires nothing); **canonical
  `.so` md5 `330738ef…` UNCHANGED** (reuse 210 operate + 228 reach + 229 ground +
  220 nav — NO new Rust Term; if one is truly needed, STOP+report); `term.rs` +
  whole `runners/dsl` tracked diff EMPTY; oracle `rung7_vision_bench`
  BEFORE==AFTER; 34-file `per_area_settlement_regression` BEFORE==AFTER (failing
  node-id SET identical); `source_match` (seed builder → seed json byte-stable)
  reported.

## FALSIFICATION BAR

The operate action is DISCOVERED by exhausting the action space (not hardcoded);
GENERAL (the same "try acting on it, incl. use" as 210's `op_use` — any object /
game, not an ls20 hack; the true actuator is randomized so no constant can encode
it); the discovery + elicitation + grounding + pass must be MEASURED vs the
`movement_only` control; and whether a real ls20 action actuates the cross must be
reported straight either way (confirmed OR honest null with exactly what each
action did).

## STRUCTURE

Build the exhaust-actions → discover-operate → elicit → ground loop + power the
discover-vs-movement-only ablation OFFLINE (the headline), THEN run LIVE on real
ls20 to test whether an action actuates the cross (the honest real test). If the
API is down, the offline ablation is the deliverable.

## FILES (to be created)

- `LS20_OPERATE_PREREG.md` (this file; committed alone).
- `domains/remote_operate_seed.py` → `seeds/remote_operate.json` — the
  action-exhaustion + discover-operate rules (domain-agnostic; default-OFF).
- `worlds/remote_operate.py` — the mechanical adapter + episode drivers.
- `scripts/remote_operate_measure.py` — the powered offline gates + source-audit.
- `scripts/remote_operate_live.py` — the bounded LIVE half.
- `tests/test_remote_operate_migrated.py` — gate tests.
- `results/remote_operate_{powered,live}.json` — measured numbers.
- `results/operate_{oracle,regress}_{before,after}*` — discipline baselines.
