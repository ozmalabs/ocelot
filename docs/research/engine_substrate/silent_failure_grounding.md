# The silent-failure grounding check — the final brick of 'the assistant out of the loop'

## VERDICT (lead)

**The grounding check CLOSES the silent-failure residual for MEASURABLE claims — it
catches an internally-consistent silent failure the internal stack STRUCTURALLY could
not — and it bottoms out HONESTLY where the agent has no world-access.** A high-stakes
conclusion fires the check on STAKES ALONE (regardless of surprise), the agent's OWN
speak→hear→recognise round-trip MEASURES it against the world, the contradiction is found,
and the verdict REOPENs. Where no world-machinery reaches the ground truth, the check names
the residual ("needs world-contact / acquisition I lack") rather than faking a pass.

Run captured to `/tmp/silentground_full.log` (`EXIT=0`,
`===MARKER_SILENT_FAILURE_GROUNDING_COMPLETE===`, pgrep-verified gone — the only pgrep hits
are the grep shell itself, no python replay process). The killer test:
`scripts/silent_failure_grounding_replay.py`. The module: `domains/silent_failure_grounding.py`.
The round-trip realises **0.900** world accuracy (n=40, chance 0.10) on the agent's OWN
synthesized speech — real machinery, no FSDD, no nets. **Not committed (coordinate).**

| case | internal hat | grounding check | world (round-trip) vs claim | decision | result |
|---|---|---|---|---|---|
| **1 — measurable silent failure** | weight **−0.0000** → GLANCE/COMMIT (cannot feel it) | fire-on-stakes **True** | **0.750** vs **0.95** (rel Δ **0.211** > tol 0.15) | **REOPEN** | **CLOSES** — caught what the internal stack committed; banked as a shape |
| **control — true silent claim** | — | fire **True** | 1.000 vs 1.000 (no contradiction) | **COMMIT** | no over-fire — grounds a TRUE claim |
| **3 — residual-of-the-residual** | — | fire **True** (high stakes) | **no world_measure** (no access) | **UNGROUNDED** | bottoms out HONESTLY ("needs acquisition") |

`ALL THREE: True`.

## (1) Does the grounding check CATCH a measurable silent failure the internal stack could not? — YES, the numbers

The killer Case 1 is a recognition claim that is **internally consistent**: it asserts ~0.95
round-trip self-recognition on a digit, and its claimed_support equals its realised_support
(it FEELS right — no internal prediction-error). This is exactly the silent shape the
existing stack misses:

- **The internal `self_check_hat` GLANCES.** Handed the same silent claim, the hat computes
  surprise ≈ 0 → uncertainty ≈ 0 → `weight = uncertainty × stakes` = **−0.0000** < threshold
  0.30 → GLANCE → COMMIT. A louder internal check cannot help: there is **no internal signal
  to hear**. (This is the hat's own documented control row — high-stakes + clean = weight
  0.000, does not fire.) The generative skeptic also bottoms out
  (`residual = novel_failure_no_matching_shape`).
- **The grounding check CATCHES it.** It fires on **stakes alone** (native `T_STAKES_FIRE =
  Gt(stakes, 0.70)` — it does not read surprise at all), then runs the EMPIRICAL world
  measurement: the agent SPEAKS the digit across 4 personas via its owned articulatory synth,
  HEARS it, RECOGNISES it via the native DtwTo Argmin. The world realises **0.750**, not the
  claimed **0.95** — relative delta **0.211 > tol 0.15** → native `T_CONTRADICTION` fires →
  **REOPEN**. The grounded silent failure is then **banked** as a shape
  (`grounded__silent_recog_grounded__world_contradiction`) for the skeptic, keyed on the
  EXTERNAL measurement (not a localized surprise the silent failure does not have).

So: internal weight −0.0000 (commit) vs world-measured 0.750 ≠ claimed 0.95 (reopen). The
grounding check catches precisely what the internal stack commits. This is the residual the
internal stack could not catch — closed for a measurable claim.

The **control** proves it does not over-fire: a TRUE high-stakes silent claim (a digit the
world recognises at 1.000) fires on stakes, the world AGREES (no contradiction), → COMMIT. It
grounds a true silent claim instead of reflexively rejecting it.

## (2) The honest RESIDUAL-OF-THE-RESIDUAL — a silent failure the agent CANNOT measure

**Named, not forced to pass.** Case 3 is the Dvorak claim ("the Dvorak layout reduces finger
travel for English text") — fluent, internally consistent, and the agent has **no world-access
to its ground truth**: no keyboard-ergonomics corpus, no finger-travel simulator, no round-trip
that reaches it. The grounding check **fires** (high stakes) but finds `world_measure = None`,
so it **bottoms out honestly**: DECISION = **UNGROUNDED**, reason = *"NEEDS WORLD-CONTACT /
ACQUISITION I LACK … the check does NOT fake a pass."*

This is one level deeper than the internal stack's residual. The internal stack's residual was
the silent failure itself (no internal signal). The grounding check closes that for *measurable*
claims by reaching outside to the world. Its OWN residual is the claim the agent has no world-
machinery to measure — the irreducible floor is **acquisition**, not a missing check. A check
cannot manufacture world-contact it lacks; it can only name the gap, which it does.

## (3) What was built (file:line) — fire-on-stakes + the empirical grounding measurement

A single NEW module + a NEW seed dial + a NEW killer test. **ADDITIVE** — nothing pre-existing
modified.

- **`domains/silent_failure_grounding.py`** — the grounding check. Native Term-trees +
  world-adapter glue only:
  - `T_STAKES_FIRE` (`:78`) — the NEW channel: `IfThenElse(Gt(stakes, stakes_floor), 1, 0)`.
    It does **NOT** read surprise/uncertainty — that is the whole point; a silent failure has
    none, so the internal `weight = uncertainty × stakes` cannot reach it. Rust-evaluated.
  - `T_ABS_DELTA` / `T_REL_DELTA` (`:88`/`:90`) — the claim-vs-world departure, native
    `Abs(Minus(measured, claimed))` / relative.
  - `T_CONTRADICTION` (`:96`) — `IfThenElse(Gt(rel_delta, tol), 1, 0)`: the world DISAGREES
    beyond tolerance. The contradiction decision is a Term, not a Python `if`.
  - `gate_on_stakes` (`:131`) — FIRE-ON-STAKES: marshal the claim onto a `GroundCheck` node,
    evaluate `T_STAKES_FIRE`.
  - `ground_against_world` (`:170`) — the EMPIRICAL measurement: run the agent's OWN
    `world_measure` callable (round-trip / held-out / computable quantity), evaluate the native
    contradiction Term. The ONLY world-I/O. `world_measure=None` → honest bottom-out.
  - `resolve` (`:213`) — bounded REOPEN (fired + world contradicts) / COMMIT (fired + world
    agrees, OR low stakes) / UNGROUNDED (fired + no world-access).
  - `grounding_check` (`:240`) — the whole reflex in one call; optional `bank_on_catch` banks a
    grounded silent failure via `autonomous_curation.bank`, keyed on the EXTERNAL measurement.
- **`seeds/silent_failure_grounding.json`** — the two dials (`stakes_floor: 0.70`, `tol: 0.15`),
  seeded not hard-coded; declares `depends_on: [self_check_hat, generative_skeptic]`.
- **`scripts/silent_failure_grounding_replay.py`** — the killer test. The world measurement is
  the agent's OWN owned round-trip: SPEAK each digit via `projection.build_speech_forward` (Rust
  Klatt synth, NO TTS net, NO .fit), HEAR it, RECOGNISE it via `InvariantInverse` (native DtwTo
  Argmin) against prototypes built from the agent's OWN synthesized speech. Fully self-contained
  (no FSDD, no data). Real measurement, not a heuristic.

### Donkey / architecture audit

- **ADDITIVE.** `git status`: only `?? domains/silent_failure_grounding.py`,
  `?? scripts/silent_failure_grounding_replay.py`, `?? seeds/silent_failure_grounding.json`.
- **Core untouched.** `self_check_hat.py`, `autonomous_curation.py`, `generative_skeptic.py`,
  `meta_monitor.py`, `projection.py`, the Stage-4 harnesses, `order_n_postulates.py`,
  `speech_science.py`, `cortex_loop.py`, `solve_for_n.py` — **none dirty** (verified). All READ
  as references; the module plugs into the self_check_hat at the STAKES channel by extension
  (a new module), not by modifying it.
- **NATIVE where the cognition lives.** The fire decision, the claim-vs-world delta, and the
  contradiction decision are native Term-trees (`Gt`/`Abs`/`Minus`/`IfThenElse`,
  Rust-evaluated). Python is world-adapter glue only: marshal the claim's numbers onto a graph
  node, RUN the agent's own world-measure callable (world-I/O), evaluate the native Terms.
- **REAL measurement, not a heuristic.** The world measure is the agent's own
  speak→hear→recognise round-trip (0.900 realised, n=40). The check measures the conclusion
  against the WORLD, not the internal do-contrast — exactly the empirical/external contact a
  silent failure requires.
- **NO net, NO .fit, NO gradient, NO loss, NO sweep** — grep of the cognition module finds none
  (only the audit lines in the docstring). The forward model is the owned articulatory synth.

## Is the silent-failure residual closed?

**Yes, for MEASURABLE claims — the agent grounds its own conclusions against the world, fire-on-
stakes, and 'needs acquisition' is the irreducible floor.** The grounding check is the channel
the internal stack lacked: it does not depend on an internal signal (the silent failure has
none), it fires on stakes and reaches outside to the world's verdict. Where the agent can
measure (a recognition round-trip, a held-out test, a computable quantity), the internally-
consistent-but-externally-wrong claim is caught and reopened — demonstrated against the agent's
OWN round-trip (world 0.750 ≠ claimed 0.95 → REOPEN, the internal hat's weight was −0.0000).
Where it cannot measure, it bottoms out honestly, naming the residual-of-the-residual: the
floor is world-contact/acquisition, which a check cannot manufacture. The final brick is in.

*Log: `/tmp/silentground_full.log` (`===MARKER_SILENT_FAILURE_GROUNDING_COMPLETE===`, EXIT=0).
Harness: `scripts/silent_failure_grounding_replay.py`. Module: `domains/silent_failure_grounding.py`.
Not committed (coordinate).*
