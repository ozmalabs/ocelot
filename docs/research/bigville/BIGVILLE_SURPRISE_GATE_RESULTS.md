# RESULTS — Graph-native surprise gate (block 284000)

All five signatures reproduce. **`test_surprise_town_migrated.py` 6/6 + conduct-town
/ supergraph / scoping / baseline 28/28 unchanged = 34/34 on the canonical engine
`fd82dc2978dbb055496dd82390ac2ebe`**. `runners/dsl` diff EMPTY — ZERO new Rust.
Prereg `BIGVILLE_SURPRISE_GATE_PREREG.md`.

## What landed

- `seeds/bigville_surprise_gate.json` — 3 rules: `sg_surprise` (surprise = a `sees`
  with no matching `predicts_near`, sets `m.surprised`), `sg_absorb` (folds the new
  other into the prediction), `sg_provide_directed` (an option afforded iff its own
  target is seen). `self_load_only`.
- `worlds/bigville_surprise_town_world.py` — the supergraph town on a surprise
  clock: mints observation (`sees`) + the held prediction (`predicts_near`), runs
  the surprise gate + provision, and dispatches ONLY surprised residents to the
  282000 supergraph collapse (Bond-directed).

## The measured trace (one 3-tick run)

| tick | scene | outcome |
|---|---|---|
| t1 | A meets **predicted** B | all **no-ops** — no surprise, no collapse |
| t2 | **unpredicted** rival E appears near A | A surprised → collapse → **harm@E** (the resented rival); E surprised by A → **help@A** (neutral → prosocial); B (predicted A) → no-op |
| t3 | A re-sees now-**absorbed** E | **no-op** — the prediction held, no re-surprise |

Two decisions across three ticks — O(surprise), not O(residents × ticks). The
surprise rule fires only on the prediction residual, the collapse runs only when
surprised, and the conduct is Bond-directed.

## What this establishes

The 283000 clock is now graph-native. **Surprise is a RULE** (`sg_surprise`, using
the standard edge-absence form), not a Python conditional; the **held prediction is
graph-resident** (`predicts_near` edges) and updates by a rule (`sg_absorb`); and
the whole loop composes with the supergraph conduct collapse (282000) and the scoped
decision core (279000 v1.1.0). The adapter is a mechanical dispatcher on a
rule-computed flag — it mints observation and reads `m.surprised`, holding no rule
engine and no valuation argmax (source-audited). It is residual all the way:
`sg_surprise` gates *whether* to decide; the decision core's own residual gates *how
deep*; the no-op continuation between surprises is the habitual fast path.

## Honest residuals (NOT patched)

- **Presence-only prediction.** `predicts_near` is a set of bodies, not a
  trajectory; a predicted companion leaving is not yet modelled as (un)surprising —
  the demonstrated discriminator is the meeting (predicted vs not). Trajectory
  prediction + `vanished`-surprise is a later refinement.
- **Adapter still sets `input_vec` + arms the collapse per surprised resident.**
  The net-input load and the collapse arming are mechanical adapter I/O around the
  rule-based decision; folding the arm into a rule (`m.surprised → collapse_armed`)
  is a clean follow-up.
- **Movement is abstracted.** `tick(copresence)` takes co-presence directly; wiring
  it to the 283000 hop clock (proximity from real positions) + the live integ5 town
  + player viz is the remaining integration. Perf is clear (surprise + collapse are
  both sparse and local).
