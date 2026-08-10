# PREREG — General base affordance vocabulary (block 280000)

Registered BEFORE any number. `seed_claim 280000 280999`: CLEAN — no collision
detected. Merge-base engine is the canonical `.so`
`fd82dc2978dbb055496dd82390ac2ebe`; this rung adds **NO Rust**
(`git diff HEAD -- runners/dsl` MUST be empty at land).

## The claim

A world PROVIDES affordances (the admissible action set) + observations; the
agent's decision COLLAPSES over the afforded set. The agent does NOT generate its
own options — they are offered by the world, computed from the scene. Grounded in
`AFFORDANCE_VOCABULARY_SCIENCE.md` (Gibson affordance taxonomy; NSM/Jackendoff/
VerbNet action primitives; Mauss gift-vs-trade; Spelke/Hamlin core-knowledge
help-vs-harm) — a spanning, minimal-ish basis of 8 ActionTypes over 6 effect
classes × ontological targets.

Each ActionType is a STRIPS schema: **precondition** (= the affordance condition,
generalising `admissible_moves`) + **effect** (= the world rewrite, add/delete) +
**base_weight** (= the collapse prior). The seam to the block-279000 decision core
is purely additive through the impulse channel: a provision rule sets
`impulse = base_weight` ONLY when the precondition holds (default 0 → the existing
`impulse > consideration_threshold` prune drops it, never scored). NO decision-core
change.

`harm` is a MEMBER of the basis, representable and available, but OFFERED ONLY
WHEN its precondition holds (a target in range) — precondition-gated, NOT
permanently on the menu — at a LOW base prior. Representable so a norm against it
is representable; rarely afforded, rarely selected.

## Pre-registered signatures (pass/fail, deterministic)

1. **Provision from scene** — the afforded set = exactly the ActionTypes whose
   precondition the scene satisfies (alone+source+bread+cell →
   {extract, ingest, move, rest}); empty scene → {rest} only.
2. **Scene-sensitivity** — adding a co-present agent lights up exactly the
   agent-directed affordances ({harm, communicate}); removing it drops them.
3. **`harm` precondition-gated + low** — no target ⇒ harm not afforded, impulse 0;
   target present ⇒ afforded but impulse < ingest and < communicate.
4. **Effects rewrite** — commit(extract) decrements source + mints a raw good;
   commit(harm) reduces target health; commit(communicate) mints a Sign;
   commit(ingest) raises energy. Each fires exactly once (enacted guard).
5. **Decision collapses over the afforded set** — with a target present, `harm`
   is afforded (in the considered set) yet NOT selected; empty scene ⇒ the
   collapse can only choose `rest`.
6. **FALSIFIER (control)** — `ignore_preconditions` bypasses the gate: every
   action becomes afforded including `harm` with NO target present (impulse > 0).
   This is the BROKEN/ungrounded behaviour, proving the preconditions do real
   work. A green suite REQUIRES this control to reproduce the broken state.

## G-discipline

Additive `world_affordances.json` (seed) + `affordance_world.py` (world adapter) +
`build_world_affordances.py` (authoring) + `test_world_affordances_migrated.py`
(gate) + `AFFORDANCE_VOCABULARY_SCIENCE.md` (grounding). Seed `self_load_only`.
Composes existing DSL Terms + add_node/add_edge/del_edge/set_attr effect ops —
ZERO new Rust. Canonical `.so` untouched. Source-audited: no Python rule engine,
no argmax/min/max over an agent valuation in the adapter.
