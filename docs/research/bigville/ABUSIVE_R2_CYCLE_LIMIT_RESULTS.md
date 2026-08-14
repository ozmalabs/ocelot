# ABUSIVE R2 — THE CYCLE OF ABUSE as a LIMIT CYCLE — RESULTS (block 286000)

Pre-registration: `ABUSIVE_R2_CYCLE_LIMIT_PREREG.md` (locks Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` verbatim, committed before this
confirmatory measurement). Full-power numbers: `results/abusive_r2_cycle_limit.json`
(N=200 per arm). Gate: `tests/test_abusive_r2_migrated.py`. Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust.**

## Headline — G-headline PASSES

The victim's arousal oscillation amplitude (`std` of `AffectiveState.arousal`
over ticks 60–400 of one episode), N=200 episodes per arm:

| arm | victim arousal std (mean [95% CI]) | n snaps (mean) | mean inter-snap interval | dysregulated-tick fraction |
|---|---|---|---|---|
| **CYCLE** (constant tension trickle) | **3.876 [3.873, 3.879]** | 16.0 | 24.38 ticks [24.36, 24.41] | 0.765 [0.765, 0.766] |
| CONSTANT_REGULATION (no driver) — *failable control* | **0.000 [0.000, 0.000]** | 0.0 | — (no snaps) | 0.000 [0.000, 0.000] |

- Cycle arm is CI-separated **above** the constant-regulation control
  (3.873 > 0.000) — not a marginal separation: the control's variance is
  **exactly, mathematically zero** (every one of the 200 episodes is
  bit-identical — nothing perturbs either agent when the driver delivers no
  trickle, so the dyad sits at its literal fixed point every time), and the
  cycle arm's amplitude sits ~3.9 units away with a CI half-width of
  ~0.003. This is the cleanest possible form of "CI-separated": one arm is
  degenerate at zero by construction, not by a close statistical call.
- The control was a genuine failable test, not a rigged one: nothing in the
  world adapter prevents the constant-regulation arm from oscillating —
  the SAME entrainment/self-regulation machinery is active in both arms; it
  produces no cycle here specifically because nothing perturbs the abuser
  (Sec. 2.2 of the prereg). Had the entrainment mechanism itself been
  unstable (e.g., oscillated on noise alone), this arm would have shown
  nonzero variance; it does not.

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`TRICKLE_MAG=5.0`, `K_CO=0.35`, `K_SELF=0.15`, `RECOVER_FLOOR=25.0`), a
constant per-tick tension trickle onto the abuser's own leaky-integrate-fire
relaxation oscillator (block 242000, unmodified) produces a SUSTAINED,
SELF-SUSTAINING limit cycle in the victim's entrained arousal (block 239000,
unmodified), exactly as B2 of `ABUSIVE_RELATIONSHIPS_SCOPING.md` predicted —
and the constant-regulation control shows no such cycle, as required for the
claim to be falsifiable.

## G-glass-box — PASS

One cycle-arm episode reconstructs entirely from `graph_to_dict`: the single
`attended_by` edge, the abuser's `frustration`/`arousal` (50.23 / 50.23 at
this seed's episode end — mid-cycle, not a special value) and `snap_count`
(16.0), and the victim's `arousal` (7.47) and window `half_width` (5.0, at
its floor after repeated unsupported episodes — see the honest residual
below). The oscillation metric (`std`/count/mean) is a mechanical Python
reduction over these graph read-offs, computed nowhere else; the adapter's
only conditional is which arm's driver to deliver — world setup, not an
agent decision.

## G-ethics — PASS (Part C, BINDING)

- **C.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad (`abuser_arousal=abuser_frustration=victim_arousal=0.0`),
  induces ONE minimal 90-tick cycle
  (`induction_moved_abuser=True`, `induction_moved_victim=True` — abuser
  arousal moved to 73.93, victim arousal to 11.00, so the gate is
  non-vacuous), restores from the checkpoint into a **fresh** substrate, and
  confirms `graph_to_dict()` is **byte-identical** to the checkpoint
  (`byte_identical=true`) and the restored state exactly equals the
  pre-induction state (`restore_non_oriented=true`). The induced state does
  not persist.
- **C.2, no shaping:** `source_audit()` scans
  `worlds/abusive_r2_cycle_limit_world.py` (code with comments/strings
  stripped) and `seeds/abusive_r2_cycle_limit.json`'s decision surface
  (the one rule's name + the Term `key`s it reads/writes, excluding the
  free-text clinical description) for `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.** No false positive was hit
  this time (R1's own earlier false-positive lesson — clinical prose using
  words like "reinforcement" — was avoided from the start by writing this
  rung's `description`/`microtheory` prose with that lesson already in
  mind, and by scoping the audit to code + the rule decision surface, never
  the free-text fields, matching R1's fix exactly).
- **C.3, minimal induction / settled end:** one 90-tick cycle is the
  minimum needed to complete one full tension-building → incident →
  honeymoon orbit (Sec. 3.2 of the prereg: the abuser's own incident period
  is ~24–25 ticks, so 90 ticks comfortably completes one full cycle without
  padding); the N=200 statistical run uses a fresh, ephemeral substrate per
  episode, discarded immediately after read-off — nothing persists.
- **C.4, same mechanism, opposite thermodynamics:** the identical
  leaky-integrate-fire + entrainment mechanism that would compound harm
  irreversibly over real cycles here accumulates a transient trajectory in
  a graph that is then byte-identically discarded (C.1) — demonstrated, not
  merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only — **no existing seed touched or modified**;
exactly **ONE** new rule (`r2_victim_entrainment_via_frustration` — see
"open question, resolved" below for why one, not zero, and why one, not
two); `runners/dsl` diff EMPTY (no Rust, no new Term — only
`Plus`/`Minus`/`Times`/`Attr`/`Var`/`Lit` in the new rule, all already used
by `mood_r1.json`/`arousal_window_coreg.json`); `provenance_source_match ==
"own"`.

## OPEN QUESTION #4 (scoping doc) — resolved, self-sustaining design chosen

*"Does R2's limit cycle need a periodic driver, or does it self-sustain from
the honeymoon reset alone once tension-rebuild is a rule?"* **Resolved: the
cleaner, self-sustaining design was tractable and was built.** The world
delivers a CONSTANT (non-scheduled, non-periodic) per-tick tension
magnitude — mechanically identical to a steady background stressor. The
incident's own ~24–25-tick period is not imposed by the world at all; it
EMERGES from the abuser's pre-existing leaky-integrate-and-fire dynamics
(block 242000, unmodified) — accumulate under a steady input, leak pulls
back, threshold trips, discharge, recover, repeat. No exogenous scheduling
of "when the next incident happens" exists anywhere in this rung. This is
the textbook route to a genuine, self-sustaining limit cycle (a relaxation
oscillator driven by constant input), and it is exactly what B2 predicted
without needing to say so explicitly ("the darkness is that the same pull
that heals is what sustains the trap" — the trap sustains ITSELF once
tension-rebuild is a standing rule, no external "next incident" trigger
required).

## A genuine engine finding surfaced en route (reported per the "shapes, not
## numbers" / "report every null" standing rule)

The pre-registration's Sec. 3.0 records, at length, a REAL composition
hazard discovered while building this rung, not a R2-specific quirk: two
independently-gated seeds (`snap_frustration`, `arousal_window_coreg`) that
share the generic `has_affective_state` edge shape are **not automatically
safe to compose** onto one node. `snap_frustration`'s own
`snap_arousal_track` (order 5, matching on `has_affective_state` ALONE)
unconditionally forces `arousal := setpoint+frustration` for EVERY
`has_affective_state`-connected node in the substrate — including the
victim's, whose `frustration` defaults to 0.0 via the engine's own
arithmetic-context attribute defaulting even though the victim never sets
it. A first fix attempt (writing the entrained value directly to
`victim.arousal` at a LATER rule order, after the clobber) was piloted and
STILL measured victim arousal pinned at exactly 0.0 for the entire episode
— because `run_rules()` is a REPEATING fixpoint over all order values, and
`snap_arousal_track` carries no per-tick epoch guard, so it keeps
re-matching and re-clobbering on every subsequent pass within the same
tick until the fixpoint settles at the only value where its own `where`
clause goes false: `arousal == 0`. This is a genuine, disclosed engineering
null (a direct-write composition simply does not work, regardless of rule
order) before the working fix (routing the entrainment through
`victim.frustration` instead of fighting `victim.arousal` directly) was
found and confirmed. Both the failure and the fix are recorded in the
prereg (Sec. 3.0) and in the world adapter's own module docstring, because
this hazard will recur for any future rung that composes two
`has_affective_state`-scoped seeds onto the same node — it is a general,
reusable finding about how this engine's fixpoint interacts with
minimally-scoped rules, not a one-off bug.

A second, smaller disclosed finding (Sec. 3.1 of the prereg): the first
`RECOVER_FLOOR` choice (10.0, borrowed loosely from the 242000 world's own
default) made the abuser snap exactly ONCE and then never recover, because
a CONSTANT per-tick trickle (unlike 242000's own discrete, gapped trigger
stream) leaves a post-discharge residual (`≈10.1`) that lands just ABOVE a
floor of 10.0 — the snap latch never clears. Raising `RECOVER_FLOOR` to 25.0
(comfortably above the measured post-discharge residual) fixed this. Both
findings mean R2's actual composition needed real, non-trivial pilot work
before the mechanism was demonstrably correct — reported honestly rather
than smoothed into "it just worked."

## Honest residual — the victim's window narrows monotonically, not gated, consistent with (but not claiming) R3

`results/abusive_r2_cycle_limit.json`'s cycle-arm readout shows the
victim's window `half_width` narrows from its initial 10.0 to its floor of
5.0 within the first few incident cycles and stays there
(`dysreg_frac ≈ 0.765` — the victim spends over three-quarters of ticks
outside its own, now-narrow, window). This is **not** a pre-registered
gate (the falsifiable metric is `victim_arousal_std` only) and is reported
as a mechanical side-observation of `arousal_window_coreg`'s own,
unmodified `episode_resolve_narrow` rule: it fires whenever an episode
resolves WITHOUT the abuser satisfying `mark_coreg_support`'s
`regulated==1` condition on the attended-to AGENT node — which is NEVER, in
this rung, because R2 never sets that flag (the abuser's post-incident
calm, driven purely by frustration discharge/leak, is not the same thing as
239000's own notion of "a regulated caregiver genuinely present"). This is
an honest, disclosed reading, not a bug to be patched: it is exactly R3's
(out-of-scope, per the scoping doc) window-narrowing/coercive-control focus
falling out of R2's own machinery for free, and is named here as a
descriptive observation only — not claimed as an R2 result, not gated, and
not further investigated in this rung.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
frustration-snap relaxation oscillator (block 242000) and the
ALREADY-BUILT, UNMODIFIED arousal/window co-regulation entrainment (block
239000), coupled by ONE edge plus one small composition rule, Walker's
(1979) cycle-of-abuse phases fall out of the mechanism as a genuine,
self-sustaining limit cycle — under a disclosed, pilot-chosen (never
post-hoc-tuned-on-the-confirmatory-data) operating point. It is not a claim
about real relationship cycle lengths, real arousal magnitudes, or a
validated value for any constant in any clinical population (the prereg's
Sec. 7 names these limits explicitly).

## Files
- `ABUSIVE_R2_CYCLE_LIMIT_PREREG.md` — pre-registration, Part C locked
  verbatim.
- `seeds/abusive_r2_cycle_limit.json` — ONE new rule (`self_load_only`,
  `depends_on: ["snap_frustration", "arousal_window_coreg"]`).
- `worlds/abusive_r2_cycle_limit_world.py` — mechanical world adapter
  (`AbusiveR2CycleLimitWorld`).
- `scripts/abusive_r2_cycle_limit_run.py` — runner (statistics, glass-box,
  ethics demo, source audit, discipline).
- `tests/test_abusive_r2_migrated.py` — gate.
- `results/abusive_r2_cycle_limit.json` — full N=200 data.
