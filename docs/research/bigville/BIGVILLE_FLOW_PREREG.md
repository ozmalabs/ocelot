# PREREG — block 329000: intrinsic motivation → flow → generativity (C5)

`BIGVILLE_COGNITIVE_CAPABILITIES_PLAN.md` C5. Intrinsic motivation with a **flow** condition
(Csikszentmihalyi: engagement when *challenge ≈ skill*; boredom when too easy, anxiety when
too hard), where **sustained flow produces a generative act** — a named creation whose
**value is recognized** (block 324000's recognition primitive), not intrinsic. Grounded in
Self-Determination Theory (intrinsic motivation) and Csikszentmihalyi's flow. This is the
cognitive capability under DF's "strange mood → artifact."

## The mechanism (`bigville_flow.json`)

- **`fl_state`** — `gap = challenge − skill`; `flow = max(0, 1 − flow_gain·gap²)` (peaks when
  challenge matches skill); `flow_state = anxiety` if `gap > tol`, `boredom` if `gap < −tol`,
  else `flow` (Csikszentmihalyi's three-channel model).
- **`fl_streak`** — per step, `flow_streak += 1` while in flow, else resets to 0 — engagement
  must be *sustained*.
- **`fl_generate`** — once `flow_streak ≥ flow_needed`, a `Creation{quality}` is minted
  (encoding the maker's competence/state) and the streak resets — generativity **emerges from
  sustained intrinsic engagement**, not a one-shot.
- **`fl_worth`** — a creation's `worth = Count(appreciators)` — its value is the count of
  agents who **recognize** it, never a fixed intrinsic number (the recognition thesis applied
  to created objects).

## Gates (pass/fail, pre-registered) — the signature, not tuned numbers

1. **G-flow-at-challenge-equals-skill (HEADLINE):** sweeping challenge at fixed skill, flow
   **peaks when challenge ≈ skill** and falls when the gap grows either way.
2. **G-boredom-vs-anxiety:** challenge ≪ skill → `boredom`; challenge ≫ skill → `anxiety`;
   matched → `flow` (the three channels).
3. **G-generativity-under-sustained-flow (HEADLINE):** held in flow for `flow_needed` steps,
   the agent **produces a creation**; too few steps → none.
4. **G-value-is-recognized:** a creation with no appreciators has `worth = 0`; recognition
   from N agents makes its worth N — value is recognition, not intrinsic.
5. **G-off-flow-no-creation (falsifier):** an agent kept in sustained **boredom or anxiety**
   (never in flow) produces **no creation**, however long it runs.
6. **G-no-python-decision (source audit):** state/streak/generate/worth are the seed rules;
   the adapter sets skill/challenge, steps, wires appreciation, and reads.

## Scope / honesty
- Flow is a downward parabola in the challenge−skill gap with a three-channel state cutoff;
  the full flow model (skill *and* challenge must both be high; the widening channel) is a
  refinement, deferred. The creation encodes the maker's competence as a stand-in for C3's
  dominant active traces (the richer encoding is the C3+C5 integration).
- "Value is recognized" reuses the recognition idea (324000) locally (an appreciator count);
  wiring it to the full recognition faculty is the integration step.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
