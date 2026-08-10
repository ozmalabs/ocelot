# PREREG — block 327000: attention as a bounded, arousal-modulated resource (C2)

`BIGVILLE_COGNITIVE_CAPABILITIES_PLAN.md` C2. A finite `focus` that (a) rises and falls
with arousal on the **Yerkes–Dodson inverted-U** (performance is best at moderate arousal,
worse when under- or over-aroused), (b) multiplies task outcome quality, and (c) **bounds**
which tasks the agent can complete (a demanding task needs a focus level to be met — a
working-memory-capacity proxy). Grounded in Yerkes & Dodson (1908) and working-memory
capacity limits (Cowan/Baddeley); arousal is fed by C1's unmet-drive pressure.

## The mechanism (`bigville_attention.json`)

- **`at_focus`** — `arousal = baseline_arousal + unmet_pressure`; `focus = max(0, 1 −
  overload_gain·(arousal − arousal_opt)²)` — the **inverted-U**: focus peaks at
  `arousal_opt` and falls on both sides (under- and over-arousal). Unmet drives (C1) push
  arousal up, degrading focus.
- **`at_complete`** — a task the agent attempts completes **iff `focus ≥ task.demand`**
  (bounded capacity — an unfocused agent cannot do demanding work), and its `outcome =
  base_skill · focus` (focus as a competence multiplier).

## Gates (pass/fail, pre-registered) — the qualitative signature, not tuned numbers

1. **G-Yerkes–Dodson-inverted-U (HEADLINE):** sweeping arousal from low to high, focus
   **rises to a peak (near `arousal_opt`) then falls** — under-arousal and over-arousal both
   yield lower focus than the moderate optimum.
2. **G-focus-multiplies-outcome:** on the same `base_skill`, a focused agent's task outcome
   exceeds an unfocused agent's — focus is a competence multiplier.
3. **G-drives-degrade-focus (ties to C1):** raising `unmet_pressure` (unmet drives) pushes
   arousal past the optimum and **lowers focus and outcome** — the motivational core costs
   attention.
4. **G-capacity-is-bounded:** a high-`demand` task **fails** under low focus and **completes**
   under good focus — attention is a finite resource that gates what can be done.
5. **G-unbounded-falsifier:** with `overload_gain = 0` focus is flat at 1 across all arousal —
   the inverted-U disappears (proving the overload term is what produces the curve).
6. **G-no-python-decision (source audit):** focus/complete are the seed rules; the adapter
   sets arousal/pressure (world I/O), gives tasks, ticks, and reads.

## Scope / honesty
- The inverted-U is modelled as a downward parabola in arousal (peak at `arousal_opt`); the
  Hebbian task-difficulty interaction (hard tasks peak at lower arousal than simple ones) is
  a documented refinement, deferred — this rung gates the core rise-then-fall signature.
- `focus ≥ demand` is a threshold capacity proxy for a graded working-memory limit; a
  chunk-count model (≈4 items) is a later refinement.
- `arousal = baseline + unmet_pressure` couples to C1 conceptually; the demonstrator sets
  both directly rather than loading the full C1 seed.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
