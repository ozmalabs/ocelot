# How I want to fix this — staged derivation, in my own terms

## The diagnosis first (why I collapse to Reset)

The babble→Reset collapse is not a missing faculty. It's a missing **carrier**. My control-discovery probe has a fixed babble budget (~6 frames). When that budget runs out *without* self being locked, there is no node in the graph that says "you are still on stage *locate-self*, keep probing." So action-selection falls through to its default, and the default rule that wins under "world unintelligible" is Reset. Curiosity minting the `unknown_world` CapabilityAxis is **inert** because nothing reads that axis and turns it into a *standing sub-goal that owns action emission*. Two things are therefore wrong: (a) no stage state persists across frames, and (b) the Reset default is allowed to fire while an unknown world is open.

## The fix in one line

Recognising the unknown world is the **same shape** as a faculty I already hold — the **investigation/escalation ladder** (staged, gated, advance-on-progress, confidence-driven). I don't invent a new mechanism. My intrinsic designer's **rung-1 analogy path** fires: `categorise_by_shape` sees "staged derivation under uncertainty" → `feedback_control` shape → it copies the ladder Frame and **rebinds its rungs** from {change-method, reframe, author-tool, re-prioritise} to my four held game faculties {locate-self, learn-consequence, infer-obstacles, navigate}. One Frame carries the stage; one guard kills the Reset default.

## The graph objects

**`DeriveProgram` Frame** (the carrier — this is the thing that was missing):
- attrs: `stage` ∈ {`locate_self`, `learn_consequence`, `infer_obstacles`, `navigate`}; `stage_entered_frame`; `progress`; `stall_count`; `last_frame` (the frame-guard idiom).
- edges: `--deriving--> WorldInstance`; `--from_axis--> CapabilityAxis{unknown_world}`; `--active_rung--> Faculty`.

The four rungs are already nodes/struct-rules. Each gets two tags I bind at instantiation: `derives` (which unknown it dissolves) and a `done_when` predicate (below).

## The rules (match / where / effect — all struct rules in `run_rules`)

**1. `open_derive_program`** — the coupling reflex (curiosity → composition):
- **match**: `CapabilityAxis{kind: unknown_world} ax` on a `WorldInstance w`.
- **where**: `Not(exists DeriveProgram deriving w)` — fire once per unknown world.
- **effect**: instantiate `DeriveProgram dp`; `dp.stage := locate_self` (dependency-first rung); `add_edge(dp, active_rung, control_discovery)`; `add_edge(dp, deriving, w)`; `add_edge(dp, from_axis, ax)`; `dp.stage_entered_frame := frame`. This is the analogy-copy of the ladder template with rungs rebound — no new primitive, the designer's rung-1.

**2. `derive_step`** — the loop body, and the **sole action source while a program is open**:
- **match**: open `DeriveProgram dp` with `stage S`, `active_rung F`.
- **where**: `Not(Eq(dp.last_frame, frame))` (frame-guard — one action per frame, no fixpoint blow-up).
- **effect**: `dp.last_frame := frame`; emit the action that **F's own probe policy** wants this frame:
  - `locate_self` → control-discovery's next varied control (keep acting, watch `respond_votes`). **No babble budget** — this is the rung that kills the 6-frame cutoff.
  - `learn_consequence` → move toward an *un-tasted* region-kind to manufacture a contact event.
  - `infer_obstacles` → keep the current heading so a death event reveals a wall (obstacles are read off death as it happens).
  - `navigate` → `plan_passable_step` toward the max-`reward_ema` reachable region.
  The emitted Action node is what the world adapter reads. The action now comes from the live rung, never the default.

**3. `advance_stage`** — the gate (advance *only* when the prior is derived). One parameterised rule reading a stage→`done_when` table:
- `locate_self` **done_when**: some Region has `respond_votes ≥ θ_self` and is tagged `is_self`. → set `stage := learn_consequence`, rebind `active_rung` to consequence-from-outcome.
- `learn_consequence` **done_when**: a non-self region-kind has `reward_ema` with `n_contacts ≥ k` AND a positive-reward kind exists (food found). → `stage := infer_obstacles`.
- `infer_obstacles` **done_when**: a death event has produced ≥1 `impassable` region-kind, OR the passability map already carries a non-trivial wall set. → `stage := navigate`.
- `navigate`: terminal/sustaining — exploit loop; the `unknown_world` axis is marked **dissolved** when the live measure banks a score gain.
- effect on advance also resets `stall_count := 0`, `stage_entered_frame := frame`. Linear enum + advance-only-on-predicate **enforces dependency order**: no stage is enterable without its predecessor's predicate true.

## What stops the Reset collapse (the load-bearing change)

Reset must stop being the silent default. I rewrite the existing default-Reset rule's **where-clause** using the held `set_rule_clause(rule_name, "where", term)` effect (rule-edits-rule, the path I already proved on the discriminator):

```
reset_default.where := Not(exists DeriveProgram dp where dp.deriving = w)
```

While any program is open on this world, the Reset rule **cannot fire** — `derive_step` owns action emission. Reset returns to availability only as the program's *own* escalation choice, never as a fall-through.

## Stall → escalate → impasse (so it can't get stuck either)

`derive_step` also banks `progress` per stage (respond_votes climbing / new contact / reward rising). A `stall` rule: if `progress` flat for `stall_count ≥ T`, escalate the current rung — first widen its probe (different control set / different target region). If a stage exhausts its escalation and `progress` is still flat, raise a **HumanImpasse to you** (intrinsic designer's rung-3) — "I cannot lock self / find a rewarding kind in world W." That is the *only* exit other than success, and it's deliberate, not a collapse.

## What drives advancement

Each stage advances on a **derived predicate**, not a timer. The whole program is kept/dropped by the live **prediction-minus-observation measure** (banking real score change) — Goodhart-safe because it's real play. The `navigate` rung's reward-banking is the global success signal that dissolves the `unknown_world` axis. Curiosity opens it; the live measure gates each rung; banked score closes it.

## Persistence

`teach` the bundle — the `DeriveProgram` template, the four rung bindings, `open_derive_program`, `derive_step`, `advance_stage`, and the Reset where-guard — into a namespaced seed (`seeds/generated/unknown_world_derivation.json`, unique ids/edges; generic ids collide across runs, learned 3×). After that, recognising *any* unknown world auto-opens the staged loop on a bare `master_tick; tick`.

---

**Net:** one Frame to carry the stage (the thing that didn't exist), one reflex coupling the curiosity-axis to instantiating it (analogy-copy of my held ladder), one rule sourcing each frame's action from the live rung, one gated advance rule per dependency edge, and one where-clause guard that removes Reset as a default. No new primitive, no external reasoner at play-time — my investigation ladder rebound onto my four game faculties.

Want me to build it? I'd implement in this order: the `DeriveProgram` Frame + `open_derive_program`/`derive_step`/`advance_stage` as a seed, then the `set_rule_clause` Reset-guard, then verify on raw snake (success = score rises, axis dissolves, zero touches inside the loop) before persisting.