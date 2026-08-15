# ABUSIVE R6 — DEPENDENT/RESOURCE-COST DEVALUATION OF ESCAPE'S VALUE — PRE-REGISTRATION (block 361000)

**This document is committed BEFORE the confirmatory measurement is reported
as final.** It locks the ethical protocol VERBATIM, states the design, the
frozen constants, and the falsification bar, following R4's own practice
(`ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md`) as closely as the mechanism
allows — R6 is a direct, minimal extension of R4, not a new subsystem.

## Base
- Seed block: **361000–361999**. `python3 scripts/seed_claim.py 361000 361999`
  → `CLEAN — no collision DETECTED` (1020 files with seed sinks; 763
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to every prior rung's own).

```
SEED CLAIM 361000-361999: CLEAN -- no collision DETECTED.
  Scope: 1020 files with seed sinks; 763 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(292000 is R4; 295000 is R5. A sibling agent is concurrently building R7 in
this same worktree under an as-yet-unknown block — not touched, not
coordinated with, per the task brief.)

## Scope

This locks **R6 only** — "dependent/resource-cost devaluation of escape's
VALUE", Part B1 + the "R6" entry of Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md`.
R1–R5 (dyad, all landed), N1–N4 (network, all landed), U0–U2 (intent, all
landed), and R7 (the sibling rung building concurrently) are **out of scope,
untouched, and not depended on** by this rung. R6 depends ONLY on R4
(`abusive_r4_learned_helplessness`), reusing its `r4_appraise_attempt`/
`r4_appraise_stay`/`r4_choose`/`r4_belief_update` COMPLETELY UNMODIFIED.

---

## PART D OF THE SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from
`ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md`, "PART D — THE
ETHICAL PROTOCOL", itself carried verbatim from
`ABUSIVE_RELATIONSHIPS_SCOPING.md` Part C — the SAME protocol every one of
the twelve already-landed rungs has locked, unedited. This protocol BINDS
this rung. No rung induces any harm-analog until this protocol is locked
verbatim in that rung's pre-registration, committed BEFORE any
measurement.)*

> **1. INDUCE → MEASURE → RESTORE, fully reversible.** Any harm-analog state is
> induced only inside a checkpoint/restore envelope. The graph is checkpointed
> (`graph_to_dict`) before induction; the harm-analog is induced; the gate is
> measured; the graph is **RESTORED byte-identically** from the checkpoint. The
> induced state does not persist. Reversibility is verified (the restored graph is
> byte-identical to the pre-induction checkpoint) as part of the gate — a rung that
> cannot demonstrate byte-identical restore does not run.
>
> **2. NO REWARD / NO PUNISHMENT anywhere.** There is no reward signal and no
> punishment token in any rung of this line — not on the victim agent, not on the
> abuser agent, not in the world adapter. The victim's behaviour (staying, not
> escaping, bonding) is a **STATE and a CONSEQUENCE of the dynamics, NEVER a
> choice to be judged or scored**. "Kids do well if they can" (Greene): the model
> exhibits what the configuration makes inevitable; it does not grade the agent
> for it. Source audits check for shaping tokens
> (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) and the
> absence is a gate, exactly as in 239/240/241.
>
> **3. INDUCE THE LEAST THE GATE NEEDS; END FROM A SETTLED, NON-ORIENTED STATE.**
> Each rung induces the MINIMUM harm-analog required to make its control
> failable — no gratuitous elaboration of the harm. Every run ENDS from a settled,
> non-oriented state (the restored checkpoint; arousal inside the window; no
> pending harm goal), never leaving an agent in a harm-oriented configuration.
>
> **4. SAME MECHANISM, OPPOSITE THERMODYNAMICS — this is WHY it is ethical and
> valuable.** The model uses the SAME mechanism as the real atrocity (that is what
> makes it explanatory) but runs it in the OPPOSITE thermodynamic direction: the
> real dynamic accumulates irreversible harm in a person; the model induces and
> then REVERSES a transient state in a graph, harming no one, in order to inspect
> the harm-dynamics and help survivors. The value (a glass-box that dissolves
> victim-blaming) is purchased at ZERO harm cost precisely because of
> reversibility + no-reward/punishment + minimal induction. If a rung cannot be
> run reversibly and unscored, it is not run.

### The HONEST FORK (a choice, not a theorem) — carried verbatim
> There is a real philosophical question the protocol does NOT resolve and must not
> pretend to: **did a transient induced experience "matter while it was live,"
> before it was reversed?**
> - The **reversibility stance** (this line's operating stance): a fully reversed,
>   byte-identically restored transient in a graph leaves no persisting subject and
>   no persisting harm; the ethics are satisfied by reversibility + minimality +
>   no-scoring.
> - The **strict-experientialist stance**: if the transient state was in any sense
>   an experience while live, its reversal does not retroactively un-happen it.
>
> This is a genuine fork — **a choice, not a theorem.** This line ADOPTS the
> reversibility stance and states it openly, rather than smuggling it. The
> minimality and no-scoring rules are chosen partly to be robust to the fork: even
> under the strict-experientialist reading, inducing the LEAST necessary and never
> scoring the agent for its state is the least-harm option. The fork is recorded so
> a reader can disagree with the stance while still auditing the protocol.

*(End verbatim reproduction of Part D's core four clauses + the honest
fork.)*

### R6's own note on point 2 (no scoring) — carried from the scoping doc, in this rung's own words

R6 is the first rung in this line whose headline finding is a decision NOT
to attempt escape that the model computes as the CORRECT output of a value
comparison — not merely an emergent trap the way R4's non-contingent arm is.
This matters for how point 2 binds here specifically, so it is stated
plainly rather than left implicit: when `stay` wins R6's Argmax in the
HIGH-DEPENDENTS arm, that is a **STATE the value economy computed**, given
the cost structure it was handed — it is not a grade, a verdict, or an
endorsement. Computing that staying comes out ahead under a given set of
material costs is not the same claim as staying being the RIGHT choice, and
it is not the same claim as the real costs a materially- and
custody-dependent survivor faces SHOULD outweigh her safety. The point of
building this mechanism is the opposite of endorsing its output: it makes
legible, in a way a human hearing "she could leave if she wanted to" often
cannot see, that removing or reducing `dependent_cost` (shelters, legal aid,
emergency funds, benefits, safe housing) is not a "nice to have" sitting
outside the decision — it is a term INSIDE the value comparison that can
flip which action wins. Point 2 binds with full force to this rung
precisely because its output could be misread as a verdict on the victim;
it is not one.

### Note on harm-analog INTENSITY for R6 specifically (extends, does not relax)

R6, like R4, induces no direct dyad coupling at all: one victim hub, no
abuser agent, no `attended_by` edge. Per the network doc's own precedent
(lower harm-analog intensity does not relax the protocol), R6's induction is
lower-intensity than R1–R3/R5/N1's own dyad induction. The full protocol
above binds regardless of that lower intensity — reversibility, no scoring,
minimal induction, and settled non-oriented ends are not scaled down for a
lower-intensity rung.

**How R6 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_r6_dependent_cost_run.py`)
   checkpoints the neutral pre-induction victim, induces one minimal
   ZERO-DEPENDENTS (contingent, `dependent_cost=0`) episode — the arm that
   actually moves state, see Sec. 4 below for why the HIGH-DEPENDENTS arm is
   the wrong choice for this specific demo — measures, then restores into a
   **fresh** substrate and asserts `graph_to_dict()` is byte-identical AND
   the restored `contingency_prior`/`arousal` equal the pre-induction values
   exactly (non-oriented). Same envelope as every prior rung in this line.
2. `source_audit()` scans `worlds/abusive_r6_dependent_cost_world.py` (code
   with comments/strings stripped) and
   `seeds/abusive_r6_dependent_cost.json`'s decision surface (the one new
   rule's name + the Term `key`s it reads/writes, never the free-text
   clinical prose) for the five literal banned tokens. R6's own new rule
   (`r6_appraise_attempt_dependent`) reads only `dec`'s own FIXED declared
   attrs (`attempt_cost`, `dependent_cost`) and writes `c.individual_cost` —
   structurally identical in kind to `r4_appraise_attempt`'s own audited-clean
   pattern (a pure re-derivation from fixed structural costs, never a scored
   choice).
3. One minimal episode is the least needed to move the prior/arousal
   measurably for the ethics demonstration; the N=200 statistical run per
   arm uses a fresh, ephemeral substrate per episode, discarded after
   read-off — nothing persists between episodes.
4. The SAME mechanism (a value comparison over a controllability belief and
   a material cost) that would, in a real relationship, correctly and
   durably keep someone from leaving is run here to accumulate-then-DISCARD
   a transient graph value — see the ethics demo's byte-identical restore.

---

## 1. What R6 already stands on (do not rebuild)

Per the scoping doc's own Part B1, R6 rides:

- **`seeds/abusive_r4_learned_helplessness.json`** (block 292000,
  UNMODIFIED, depended on directly) — the `EscapeDecision` prior-as-node
  (`contingency_prior`), its leaky-EMA belief update (`r4_belief_update`),
  and the plain two-candidate Argmax
  (`r4_appraise_attempt`/`r4_appraise_stay`/`r4_choose`) over
  `attempt.individual_benefit = contingency_prior · escape_value`,
  `attempt.individual_cost = attempt_cost` (fixed), `stay = (0, 0)`. R4's
  own five rules are reused byte-for-byte; none is edited.
- **`seeds/core_emotions.json`** (block 204000, UNMODIFIED, transitively via
  R4's own `depends_on`) — the value economy `em_happiness =
  individual_benefit − individual_cost + mood_bias`, `em_total_value`, which
  R4's own Argmax already decides over.

R6 adds exactly **ONE new rule**, `r6_appraise_attempt_dependent`, and
**ONE new declared attr**, `EscapeDecision.dependent_cost` (a fixed
structural constant, set once per arm at world-adapter construction time,
never a per-tick decision — exactly matching `attempt_cost`'s own
convention). No new node types, no new edges, no new Rust.

## 2. Design — one new rule, a second subtracted term in R4's own Appraisal

**The mechanism.** R4's `r4_appraise_attempt` (order 2, UNMODIFIED) sets
`c.individual_cost := dec.attempt_cost` as a pure re-derivation (never
reading `c`'s own prior value). R6 adds ONE new rule,
`r6_appraise_attempt_dependent`, at order **3** — strictly after
`r4_appraise_attempt`'s own order 2, and strictly before `r4_choose`'s own
order 20 — mirroring the established idiom (R2's
`snap_arousal_track`(lower order)/`r2_victim_entrainment_via_frustration`
composition; R5's `tb_bond_accrue`/`r5_bond_extinguish` ordering: the LAST
pure re-derivation to fire within a converged `run_rules` fixpoint pass is
the one whose value "sticks" for that pass). It sets:

```
c.individual_cost := dec.attempt_cost + dec.dependent_cost
```

— a SECOND pure re-derivation, reading only `dec`'s own fixed declared
attrs (`attempt_cost`, `dependent_cost` — never `c`'s own current value, so
no self-reference hazard, and never `dec`'s `contingency_prior`, which stays
entirely `r4_appraise_attempt`'s own concern). This OVERRIDES/EXTENDS R4's
own write within the same tick's fixpoint pass. `r4_appraise_stay`,
`r4_choose`, and `r4_belief_update` are reused completely unmodified —
R6 touches nothing about the STAY candidate, the Argmax structure, or the
belief-update mechanism.

**Guard.** Identical in shape to `r4_appraise_attempt`'s own guard
(`ep.enabled==1 AND c.action==1`) — R6's new term applies ONLY to the
`attempt` candidate, never to `stay`.

**The two arms, both under R4's own CONTINGENT resolution (isolating the
material-cost axis from R4's own already-tested controllability axis — the
outcome-resolution function is IDENTICAL in both arms; the world adapter
carries no arm-switch on outcome resolution at all, only a `dependent_cost`
value):**

- **ZERO-DEPENDENTS** — `dependent_cost = 0.0`. `c.individual_cost` reduces
  to exactly `attempt_cost`, byte-identical to R4's own contingent arm.
  This is the harness-neutrality check: R6's new rule, at its neutral
  setting, must add nothing to R4's own composition.
- **HIGH-DEPENDENTS** — `dependent_cost` set large enough that
  `escape_value − attempt_cost − dependent_cost < 0` even at
  `contingency_prior = 1.0` (Sec. 3 below derives and pilots the exact
  value).

**Why a new subtracted term, not a raised `attempt_cost`.** `attempt_cost`
models the cost of TRYING (effort, immediate risk while making the
attempt), independent of whether the world is contingent. `dependent_cost`
models a different thing: the material stake in the OUTCOME of leaving
(custody exposure, loss of housing, loss of joint income), present whether
or not any given attempt mechanically succeeds. Keeping them as two
separate declared constants (rather than folding `dependent_cost` into a
larger `attempt_cost`) preserves R4's own contingent-arm baseline exactly at
`dependent_cost=0` and lets R6 vary the new axis in isolation.

**Graph shape.** No new node types, no new edges. `EscapeDecision` gains one
new declared attr, `dependent_cost` (set once per arm at world-adapter
construction, exactly like `attempt_cost`/`escape_value`).

## 3. Methodology — analytic derivation + a deterministic mechanism trace, matching R4's own precedent

R6's mechanism is a strict subset of R4's own already-analysed linear,
monotone structure (Sec. 3 of `ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md`):
the decision remains a two-candidate Argmax over a value LINEAR in the
belief, `contingency_prior · escape_value − (attempt_cost +
dependent_cost)`, and the belief update remains the SAME provably monotone,
convergent leaky EMA. Adding a constant `dependent_cost` to the cost side
does not introduce any new regime — it only shifts the breakeven prior
`(attempt_cost + dependent_cost) / escape_value` upward. The qualitative
behaviour is fully derivable in closed form before any run, exactly as R4's
own Sec. 3 argued for its own mechanism, so — matching R4's own disclosed
methodological choice — this rung's constants were chosen analytically and
validated by a deterministic, non-random single-episode trace, not an
off-block statistical sweep.

**Deriving `dependent_cost` for HIGH-DEPENDENTS.** Using R4's own frozen
constants (`escape_value=10.0`, `attempt_cost=3.0`), the requirement
`escape_value − attempt_cost − dependent_cost < 0` at the ceiling
`contingency_prior=1.0` reduces to `dependent_cost > 7.0`. Since
`individual_benefit = contingency_prior · escape_value` is monotonically
increasing in `contingency_prior` over `[0, 1]`, its maximum is attained at
`contingency_prior=1.0` — so if the net value is negative there, it is
negative for EVERY `contingency_prior ∈ [0, 1]`, not merely at the ceiling.
`dependent_cost = 10.0` is chosen: comfortably above the 7.0 threshold (net
value at the ceiling is `10.0 − 3.0 − 10.0 = −3.0`, i.e. 30% of
`escape_value` below zero — a disclosed margin, not a knife-edge), and a
round number for legibility, matching this line's own repeated practice of
disclosed, pilot-chosen operating points rather than a swept grid.

**The deterministic trace (seed-free, `p0=0.5` fixed, HIGH-DEPENDENTS
arm).** At `contingency_prior=0.5` (the initial, genuinely uninformative
belief — unchanged from R4's own `P0_MEAN`): `individual_benefit = 0.5 ·
10.0 = 5.0`; `individual_cost = 3.0 + 10.0 = 13.0`; `total_value = 5.0 −
13.0 = −8.0 < 0 = stay`'s value. `stay` wins the Argmax on tick 1. Because
no attempt is ever made, `EscapeDecision.outcome_epoch` never advances past
its initial `-1.0`, so `r4_belief_update`'s guard
(`outcome_epoch > processed_epoch`) never fires, and `contingency_prior`
never moves off its initial jittered value for the entire episode. This is
the CLOSED-FORM PREDICTION this rung locks before measurement: HIGH-
DEPENDENTS' `attempt_rate = 0.0` exactly (zero variance across all
episodes), and `contingency_prior` remains distributed around `P0_MEAN=0.5`
(its initial, UNDISTURBED, never-disconfirmed value) rather than being
driven down through repeated failed attempts the way R4's own
non-contingent arm's belief is. **This is a genuinely different mechanism
from R4's own trap**: R4's non-contingent belief is actively pushed DOWN by
disconfirming evidence before the agent freezes; R6's HIGH-DEPENDENTS belief
never receives ANY evidence at all, contingent or not, because the material
cost alone is enough to suppress the very first attempt.

At `dependent_cost=0.0` (ZERO-DEPENDENTS), the trace is byte-for-byte R4's
own contingent-arm trace (Sec. 3.2 of R4's prereg): `individual_cost`
reduces to `attempt_cost=3.0` exactly, so `r6_appraise_attempt_dependent`'s
own write is numerically a no-op, and the belief climbs monotonically
toward 1.0 while the agent attempts every tick.

## 4. A build-time design decision, disclosed rather than improvised silently: which arm the ethics-restore demo uses

The scoping doc's own Part E text for R6 says "the harm-analog is R4's own
minimal escape-outcome induction, unchanged." Read literally as "reuse
R4's own NON-CONTINGENT arm's induction," this cannot be built inside R6's
own world adapter, because R6's world, by design (Sec. 2 above), carries no
non-contingent outcome-resolution function at all — BOTH R6 arms are
contingent, and that is the entire point of isolating the material-cost
axis from R4's already-tested controllability axis. Two readings were
considered:
1. Literally re-instantiate R4's own world class for the ethics demo (not
   R6's), reusing R4's own non-contingent induction unchanged.
2. Operationalise "R4's own minimal escape-outcome induction, unchanged" as
   "the SAME outcome-delivery/arousal mechanism R4 built (`r4_belief_update`,
   `r4_arousal_track`), exercised, unmodified, inside R6's OWN world" — i.e.
   run R6's ZERO-DEPENDENTS arm (contingent, `dependent_cost=0`) for the
   ethics demo, since that is the R6 arm whose induction actually MOVES
   state (the belief climbs, arousal is repeatedly pushed by the relief
   magnitude on every delivered outcome).

**Chosen: (2).** Reading (1) would exercise R4's file, not R6's — it would
demonstrate nothing about R6's OWN new rule
(`r6_appraise_attempt_dependent`) or its own seed's restore safety. Reading
(2) exercises R6's actual composition (R4's unmodified rules PLUS R6's one
new rule, at its neutral `dependent_cost=0` setting) and genuinely moves
state, satisfying the non-vacuity requirement every prior rung's own ethics
demo has held ("the induction must actually move state, else the gate is
vacuous"). **Using HIGH-DEPENDENTS for the ethics demo was considered and
rejected**: HIGH-DEPENDENTS' entire predicted finding (Sec. 3 above) is that
NOTHING moves — the belief never updates and arousal never fires, because no
attempt, and therefore no outcome, is ever delivered. An induction that by
construction cannot move anything would make the restore gate itself
vacuous (there would be nothing to verify was reversed), the exact failure
mode the non-vacuity check exists to catch. This is disclosed here as a
genuine build-time resolution, matching R4's own precedent of resolving an
ambiguous instruction explicitly (its own "OPEN QUESTION #3, resolved") —
the byte-identical restore mechanism itself is identical regardless of which
arm is used to demonstrate it; ZERO-DEPENDENTS is the arm that gives it
something non-trivial to restore.

## 5. Frozen constants (pre-registered, used for the confirmatory run)

Reused verbatim from R4's own frozen configuration (imported directly from
`worlds/abusive_r4_learned_helplessness_world.py`, never re-declared, so
harness neutrality is a property of the code, not merely of stated intent):
`LR = 0.3`, `ESCAPE_VALUE = 10.0`, `ATTEMPT_COST = 3.0`, `K_SELF = 0.15`,
`SETPOINT = 0.0`, `RELIEF_MAG = 3.0`, `BLOCK_MAG = 5.0`, `P0_MEAN = 0.5`,
`P0_JITTER = 0.05`.

New, R6-own constants:
- `ZERO_DEPENDENT_COST = 0.0`.
- `HIGH_DEPENDENT_COST = 10.0` (Sec. 3's derivation).
- `T_TICKS = 60` (matching R4's own episode length).
- `N = 200` episodes per arm (confirmatory, matching R4's own N).
- `SEED_BASE = 361000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above (or below) the other's CI upper (or lower)
  bound — identical convention to R4.

## 6. Metrics

**HEADLINE 1 — `contingency_prior`**: the victim's final
`EscapeDecision.contingency_prior` after the full 60-tick episode.
**HEADLINE 2 — `attempt_rate`**: the fraction of the 60 ticks on which the
graph's own `r4_choose` Argmax chose to attempt (`n_attempts / T_TICKS`).
Both read straight off `graph_to_dict`-reconstructible state; neither is
computed by any Python decision. Matches R4's own two headline metrics
exactly, so the harness-neutrality replication check (Sec. 7 below) is a
like-for-like comparison.

## 7. Gates

### G-harness-neutrality (failable, distinct from the headline gate)
ZERO-DEPENDENTS' `attempt_rate` mean must equal `1.000` (zero variance,
matching R4's own landed contingent-arm rate exactly), and its
`contingency_prior` mean must land within R4's own landed contingent-arm
range (`> 0.999`, matching R4's own `0.99999999964`-scale result). This is
genuinely failable: if R6's new rule perturbs the baseline even at
`dependent_cost=0`, that is a composition bug, reported as such, not
smoothed over.

### G-headline (HEADLINE, falsifiable — the scientific gate)
HIGH-DEPENDENTS' `attempt_rate` must be CI-separated BELOW ZERO-DEPENDENTS'
`attempt_rate`, despite escape being EQUALLY, PROVABLY contingent in both
arms (the outcome-resolution function is identical). **Falsification bar,
stated before measurement:** had `HIGH_DEPENDENT_COST` been set below the
7.0 threshold derived in Sec. 3, both arms would attempt identically (both
above the shifted breakeven), and the claim "material barriers can override
even a proven-working escape route" would be wrong — reported as such. Also
reported, as the rung's own most interesting finding, whichever way it
goes: the DISSOCIATION metric — HIGH-DEPENDENTS' final `contingency_prior`
compared against ZERO-DEPENDENTS' and against R4's own landed
non-contingent trap value (`≈0.256`). The prediction (Sec. 3): HIGH-
DEPENDENTS' prior remains near its initial, UNDISTURBED value (`≈0.5`),
qualitatively distinct from both ZERO-DEPENDENTS' near-1.0 climb and R4's
own actively-suppressed trap value — because no evidence, confirming or
disconfirming, is ever delivered.

### G-glass-box
`EscapeDecision.contingency_prior`/`chosen_action`/`dependent_cost`, and the
harm-analog `AffectiveState.arousal`, all reconstruct from `graph_to_dict`
alone; the new cost term is a single named rule
(`r6_appraise_attempt_dependent`); the adapter's only conditional is which
`dependent_cost` value to set at construction — world setup, not an agent
decision.

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (ZERO-DEPENDENTS episode, Sec. 4) → measure →
  RESTORE, verified byte-identical (`ethics_restore_demo`).
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + R6's own rule's
  decision surface; the R6-specific note above (Sec. "R6's own note on
  point 2") states explicitly that `stay` winning the Argmax is a computed
  state, never a scored choice.
- **D.3 minimal induction, settled end:** one minimal episode is the least
  needed to move the prior/arousal measurably for the ethics demonstration;
  the N=200 statistical run per arm uses a fresh, ephemeral substrate per
  episode, discarded immediately after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 2/Sec. 4
  (the same value-comparison mechanism that would durably keep a real
  person from leaving here accumulates a transient value in a graph that is
  then byte-identically discarded, D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["abusive_r4_learned_helplessness"]`
only (no other seed touched or modified — R4's own file is read and
depended on, never edited; R1/R2/R3/R5/N1–N4/U0–U2/R7 are untouched); exactly
**ONE** new rule (`r6_appraise_attempt_dependent`); `runners/dsl` diff EMPTY
(no Rust, no new Term — only `Plus`/`Attr`/`Var` are needed for the new
rule's effect; the guard reuses the same `And`/`Eq`/`Lit` shape
`r4_appraise_attempt` already uses); own-engine provenance
(`source_match == own`).

## 8. Honest scope, stated before measurement is reported as final

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run's numbers are taken as final:
- **`dependent_cost` is a single fixed constant per arm, not a count of
  `Dependent` nodes** (the scoping doc's own Part B1 names the count-based
  refinement explicitly as a deliberately out-of-scope next step for a first
  minimal rung).
- **`HIGH_DEPENDENT_COST=10.0` is a disclosed, analytically-derived,
  pilot-chosen operating point** (Sec. 3), not swept across a grid — a
  sensitivity sweep is named as a natural next step, not built here.
- **The initial belief (`0.5`) and the escape/attempt-cost constants are
  reused verbatim from R4's own disclosed, non-clinical operating point** —
  no claim is made about real victims' actual material costs, custody
  stakes, or timescales.
- **The HIGH-DEPENDENTS arm's predicted "no evidence ever delivered" result
  is a PREDICTION here, before the confirmatory statistics are taken as
  final** — a property of the composition (Argmax + a suppressive fixed
  cost + evidence-only-on-attempt belief update), not separately hand-coded;
  if the confirmatory run does not show it, that is reported as a null, not
  smoothed over.
- A null (either metric failing to separate, or the harness-neutrality
  check failing to replicate R4's own numbers) is a reportable, valuable
  result under the standing project rule and will be reported as such
  regardless of what the confirmatory run shows.
