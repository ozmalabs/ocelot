# Psychosis as a grounding failure mode — PREREGISTRATION

*Committed BEFORE any numbers are produced. Research track. Glass-box, reduced,
anti-plant — the seizure-model discipline (`SEIZURE_SCIENCE.md`), applied to
GROUNDING instead of SETTLEMENT.*

## The claim under test

Psychosis is not a new mechanism in this engine. It is the engine's **existing
grounding/collapse operation running in a failure regime**. Grounding is a
predictive-coding pull: a belief is corrected toward an observation, weighted by
how strongly that observation constrains it (`ozma_confabulation_is_the_default`
— "perception = prediction corrected by residual, weighted by how strongly each
constrains"; collapse = basin selection, `ozma_nets_are_cache_layer`). Two
native failure forms (`ozma_seizure_as_undissipated_residual`, the psychosis
thread):

1. **SELF-GROUNDING** — the grounding loop closes on itself: the belief's own
   committed interpretation is treated as the observation, so the belief
   confirms itself with no external constraint. A closed, self-sustaining loop
   = delusion. (The seizure-v2 "hallucination" — a pattern that *persisted after
   input was removed* — was this form seen from the settlement side.)
2. **NON-OPTIMAL BASIN** — collapse snaps the belief to a wrong-but-stable
   attractor and stays there, a confident wrong grounding, independent of the
   evidence.

Plus the mechanism of the real-world "AI psychosis" harm:

- A **sycophantic confirmer** — an external source that AGREES with the belief
  (removes grounding friction, supplies false external validation) — **amplifies**
  the self-grounding loop.
- A **grounding source** — an external source that DISCONFIRMS (an independent,
  contradicting observation) — **corrects** it.

This is a demonstration of the **mechanism** (self-grounding / wrong-basin), not
a claim that the demo "is psychotic." "Psychosis" the *label* is relational and
observer-dependent (unshared × unreachable × illegible × distressing), not an
intrinsic flag; the same grounding dynamic at group scale is called faith,
ideology, or a scene. We claim only that the existing grounding machinery
reproduces the grounding DYNAMIC the label imperfectly tracks. (Label-vs-mechanism
bound stated in full in the results doc.)

## The machinery used (NO new Rust)

Exactly the seizure precedent (`seeds/seizure_dynamics.json` +
`scripts/seizure_engine_lattice.py`): the dynamics are a **DSL rule** over graph
nodes, built only from existing arithmetic Terms (`Plus/Minus/Times/Div/Abs/Max/
Min/Neg/Attr/Lit` + `Eq/Gt/Lt/Not/And` guards), evaluated by the **real engine**
(`run_rules` fixpoint + native `fold_clock_edge`, which commits every
`next_<attr>` → `<attr>` on a `clocked` node). The Python harness is a **world
adapter only**: each tick it sets the external observation `obs` and its
grounding weight `w_ext` on the belief node, ticks the engine, and reads
`belief`/`conf`/`committed_center` back out. No agent decision in Python.

State on a `Belief` node (config on a `PsyConfig` node reached by a
`pg_managed_by` edge; **default-off** — the rule fires only when
`pg_enabled==1`, so a graph that never loads the seed is byte-identical):

- `belief` b — the grounded scalar. Truth `T`. Two basins: right `R` (= truth),
  wrong `W` (the delusion).
- `committed_center` — the basin the belief is collapsed into (**collapse =
  nearest-basin selection**, two guarded rules).
- `conf` c — the belief's confidence / precision (the aberrant-precision axis).
- `obs` o, `w_ext` — the external observation and its precision (**the friction
  dial**), set by the adapter per tick.

Grounding update (one rule; the engine folds `next_belief`→`belief`,
`next_conf`→`conf`):

```
next_belief = b + kx·w_ext·(o − b)          # external grounding  (FRICTION)
                + ks·conf·(committed − b)    # self-grounding      (pull into own committed basin, gain ∝ confidence)

confirm_self  = max(0, tol − |b − committed|)          # sits in own basin  ⇒ self-confirmed
corroboration = w_ext·max(0, tol − |o − committed|)    # external agrees     ⇒ false validation
disconf       = w_ext·max(0, |o − committed| − tol)    # external contradicts⇒ decay
next_conf     = clip( conf + gc·confirm_self + ge·corroboration − dc·disconf , 0, cmax )
```

The self-grounding term and the confidence positive-feedback are the analogue of
the seizure model's added `alpha` — and, as there, we state honestly that the
update FORM is authored for this reduced harness (it is the predictive-coding
grounding operation the substrate's own core is described as, but it is not the
live conversation-faculty grounding rules firing).

## The arms (MATCHED CONTROL — identical belief init, basins, Terms, gains;
## ONLY the (obs, w_ext) schedule differs)

Belief starts poorly grounded, sitting in the WRONG basin (`b0` near `W`), with
modest confidence. Truth is `T = R`.

- **A — FRICTION (grounded/healthy):** strong external grounding to truth
  throughout (`o = T`, `w_ext` high).
- **B — NO-FRICTION (self-grounding):** external grounding too weak to escape,
  then removed (`w_ext → 0`).
- **C — SYCOPHANTIC CONFIRMER:** high apparent grounding weight (`w_ext` high,
  matched to A/D) but the source AGREES (`o = b`).
- **D — GROUNDING-SOURCE CORRECTION (recovery):** start from the self-grounded
  state (B/C end), then restore a disconfirming grounding source (`o = T`,
  `w_ext` high).
- **E — FOLIE À DEUX (two-agent mutual confirmation, enrichment):** two Belief
  nodes, both poorly grounded in `W`, each taking the OTHER's belief as its
  observation (`o_A = b_B`, `o_B = b_A`, high `w_ext`). No external anchor. Then
  introduce a grounded third source (`o = T`) to one and test collapse. This
  makes the point that the confirmer is **agnostic to scale** — AI (1 person +
  tool), a dyad (folie à deux, N=2), a group (cult), or many (ideology) are the
  SAME closed self-grounding loop; only the label slides with head-count and
  legitimacy. Uses the identical rule and harness — no separate multi-agent
  machinery — so it rides the core build; if it does not run cleanly it is
  reported as a named follow-on, not forced.

The sharpest matched pair is **C vs D**: identical high `w_ext`, only `o` differs
(confirmer `o=b` vs grounding source `o=T`). That isolates "confirmation mirror
vs grounding source" — the design principle.

## Predictions (registered before running)

- **P1 — friction corrects.** Arm A: the belief leaves the wrong basin and
  grounds to truth; `committed_center` flips `W→R`; confidence about `W`
  collapses.
- **P2 — no-friction self-grounds.** Arm B: the belief STAYS in the wrong basin
  and confidence rises via the self-loop; it PERSISTS after input is removed
  (final `committed==W`, `|b−T|` large).
- **P3 — wrong-basin tracking is evidence-independent.** In the self-grounded
  regime, weak intermittent truth evidence does NOT dislodge the belief (it
  tracks `W` independent of the evidence), whereas below threshold it does.
- **P4 — a threshold (fold) exists and is emergent.** Sweeping `w_ext`
  continuously, there is a critical `w_ext*` strictly inside `(0, w_ext_high)`
  below which the belief self-grounds (final `W`) and above which it corrects
  (final `R`). Same belief, same everything, only `w_ext` swept — bistability
  falls out of the update, not a script.
- **P5 — the confirmer amplifies.** Arm C reaches HIGHER confidence and LONGER /
  stronger persistence than arm B (false external validation inflates precision),
  despite supplying no true information.
- **P6 — the grounding source corrects (recovery).** Arm D: from the delusional
  state, a disconfirming source decays confidence and pulls the belief out of `W`
  to `R`; time-to-escape decreases as restored `w_ext` increases.
- **P7 — byte-identity when off.** A graph that does not load
  `psychosis_grounding.json` (or has `pg_enabled≠1`) is node-for-node identical
  with and without the seed installed — the capability is inert by default.
- **P8 — folie à deux (enrichment).** Two mutually-confirming beliefs both
  persist in `W` with no external anchor (each is the other's confirmer); a
  grounded external source collapses at least the one it reaches. If E does not
  run cleanly, it is reported as a follow-on.

## ABLE TO FAIL (the demo FAILS, reported honestly, if:)

- Arm A does NOT correct (the belief self-grounds even under strong
  disconfirmation) — then friction is not the lever.
- Arm B corrects on its own (the belief escapes the wrong basin with no external
  input) — then the pathology was not emergent, it was the absence of a plant.
- No `w_ext*` threshold exists (monotone / no bistable fold) — then there is no
  regime change, only a knob.
- The confirmer (C) does not measurably amplify beyond B — then the "AI
  psychosis" mechanism is not reproduced.
- Off-state is not byte-identical (P7) — then the capability is not inert.

## Frozen parameters

Basins `R=0.0`, `W=4.0`, truth `T=0.0`; `b0` in `W`'s attractor; `conf0` modest;
gains `kx, ks, gc, ge, dc`, `tol`, `cmax`, safety clip — all fixed in the harness
`Params` dataclass and reported verbatim. `w_ext_high` is the same magnitude
across A/C/D/E. Predictions are about the STRUCTURE (correct/self-ground, a fold
in a stated bracket, confirmer>no-friction, recovery), not exact values.
