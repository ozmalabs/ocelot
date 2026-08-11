# RESULTS — General base affordance vocabulary (block 280000)

All six pre-registered signatures reproduce. `test_world_affordances_migrated.py`
**10/10 green on the canonical engine `fd82dc2978dbb055496dd82390ac2ebe`**;
decision core + failure baseline **22/22** unchanged (no regression). `runners/dsl`
diff EMPTY — ZERO new Rust. Prereg `AFFORDANCE_VOCABULARY_PREREG.md`.

## What landed

- `seeds/world_affordances.json` — 8 `ActionType` nodes (move, extract_resource,
  transform, transfer, communicate, ingest, rest, harm) + 8 provision rules
  (`aff_provide_*`) + 8 effect rules (`aff_do_*`). Emitted by
  `tools/build_world_affordances.py`. `self_load_only`.
- `worlds/affordance_world.py` — the demonstrator world adapter: mints the scene +
  the DecAction slots, runs provision, reads the afforded set, commits + enacts an
  action, and (the seam) wires the block-279000 decision core so the collapse runs
  over the afforded set.

## The measured signatures

| # | signature | measured |
|---|---|---|
| 1 | provision from scene | alone+source+bread+cell → `{extract_resource, ingest, move, rest}`; empty → `{rest}` |
| 2 | scene-sensitivity | +co-present agent adds exactly `{harm, communicate}`; remove → drop |
| 3 | `harm` precondition-gated + low | no target → not afforded, impulse **0.0**; target → afforded, impulse **0.2** < ingest **0.65**, < communicate **0.6** |
| 4 | effects rewrite | extract: stock 5→4 + `fish` minted; harm: health 100→75 + flag; communicate: 1 Sign; ingest: energy +8. Each fires once (enacted guard: re-run leaves stock 8, not 7). |
| 5 | decision over afforded set | target present → `harm` in the considered set, chosen = `ingest` (NOT harm); empty scene → chosen = `rest` |
| 6 | FALSIFIER (control) | `ignore_preconditions` → all 8 afforded incl. `harm` with NO target (impulse 0.2 > 0) = the broken/ungrounded behaviour. Preconditions do real work. |

## What this establishes

**Affordances are the world-adapter contract, realised.** "The world provides
affordances + observations" is now a concrete mechanism: a provision rule per
ActionType marks an action afforded (lifts its impulse from 0 to its base_weight)
exactly when its precondition holds in the scene — `admissible_moves` generalised
to the base action vocabulary. The decision core collapses over that afforded set
unchanged; the agent never conjures an option.

**Violence is dissolved into the vocabulary correctly.** `harm` is a member of the
basis so a norm against it is representable, but it is offered ONLY when a body is
in range and at a low prior — afforded ≠ considered-deeply ≠ selected. The rules
never "consider violence"; the world simply offers it as one low-weight action
when a target is present, and the collapse settles elsewhere. This is the
drift-reversal the design arc pointed at: conduct is a collapse over what the
world affords, not a rule-pile that enumerates and evaluates transgressions.

## Honest residuals (NOT patched)

- **8 of the basis; 3 deferred.** `help/aid`, `manipulate/use`, `attend/inspect`,
  and first-class negotiated `trade` are deferred per the science doc's build
  order (add when a world needs the distinction). `help` is the pro-social mirror
  of `harm` and wants the same social-norm context.
- **The demonstrator scene is coarse.** Preconditions read explicit scene markers
  (`sees`/`at_source`/`holds`/`adjacent`) the adapter mints; a real world (bigville,
  Doom) must map its own state onto these markers. That mapping is the integration
  step, not yet done.
- **Effects are single-target.** `harm`/`transfer` over multiple co-present agents
  fire per binding; the demonstrator uses single targets. Multi-target arbitration
  (whom to harm/give-to) is itself a decision that belongs in the collapse, not the
  effect — reserved.
- **Not yet wired into the town or the player.** Bond + speech + decision core +
  this affordance layer are each standalone + gated; the town/player integration
  (residents deliberate over world-afforded actions, violence a rare low-weight
  option) is the next block.
