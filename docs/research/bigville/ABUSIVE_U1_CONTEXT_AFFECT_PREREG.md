# ABUSIVE U1 — CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE AT ALL — PRE-REGISTRATION (block 310000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1's and U0's own practice
(`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`, `ABUSIVE_U0_INTENT_PREREG.md`)
exactly. As in N1's/U0's own precedent, the frozen constants below were
chosen using a non-confirmatory pilot run directly against the real graph on
an OFF-BLOCK seed base (90000), and once the qualitative shape (a genuine,
non-degenerate context/always-observed separation; a real window-narrowing
episode within the ethics-demo induction window) held, ONE confirmatory
measurement was taken at N=200 on the claimed block (310000+). No parameter
was subsequently re-tuned against that confirmatory number.

## Base
- Seed block: **310000–310999**. `python3 scripts/seed_claim.py 310000
  310999` → `CLEAN — no collision DETECTED` (1017 files with seed sinks; 754
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1–R5/N1–N3/U0's own).

```
SEED CLAIM 310000-310999: CLEAN -- no collision DETECTED.
  Scope: 1017 files with seed sinks; 754 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(307000 is U0, 298000 is N1, both untouched; a sibling U2 rung may claim its
own block concurrently and is not this rung's concern.)

## Scope

This locks **U1 only** — "context-dependent affect, no deception node at
all" (the sharpest no-intent test), Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`
("### U1"). R1–R5 (the dyad line), N1–N3 (the network line), and U0 (the
positive-intent control), all landed, are **untouched** — read and depended
on for their MECHANISM (N1's rules are RESTATED byte-identically, never
edited; N1's seed FILE is never depended on or modified — see Sec. 2 below),
never edited. U2 (the sincere-self-account alternative named in the same
scoping doc) is **out of scope** and untouched by this rung — a sibling agent
may build it separately, concurrently, in this same worktree; if its files
appear they are not this rung's concern.

---

## PART D OF THE UNINTENTIONAL SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_
UNINTENTIONAL_SCOPING.md`, "PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM;
STILL BINDING)", itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_NETWORK.
md`'s own Part D, itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.
md`'s Part C — the SAME protocol R1–R5's, N1's, and U0's own preregs locked.
This protocol BINDS this rung. No rung induces any harm-analog until this
protocol is locked verbatim in that rung's pre-registration, committed BEFORE
any measurement.)*

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

*(End verbatim reproduction of Part D.)*

**How U1 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_u1_context_affect_run.py`)
   checkpoints the neutral pre-induction mind (abuser at
   `arousal=frustration=0`, victim at `arousal=0`/window `half_width=10.0`,
   network node 0's `belief_gap=seen_charm=seen_elevated=0`), induces exactly
   **ONE MINIMAL 200-tick induction window** (a DISCLOSED DEVIATION from
   N1's/U0's own 90-tick minimum — Sec. 4 below states precisely why the
   larger number is this rung's own genuine minimum, not a laxer standard) on
   the CONTEXT_GATED arm, measures (confirming the induction actually moved
   the abuser, the victim, narrowed the victim's window, AND moved at least
   one network node's belief-gap — non-vacuous on all FOUR fronts), then
   `graph_from_dict`s the checkpoint into a **fresh** substrate and asserts
   `graph_to_dict()` is byte-identical AND the restored state (abuser
   arousal/frustration, victim arousal/window, network node 0's belief-gap
   and BOTH observation counts) equals the pre-induction values exactly
   (non-oriented). Same envelope as R1–R5/N1/U0.
2. `source_audit()` scans `worlds/abusive_u1_context_affect_world.py` (code
   with comments/strings stripped) and
   `seeds/abusive_u1_context_affect.json`'s decision surface (the two new
   rules' names + the Term `key`s they read/write, never the free-text
   clinical prose) for the five literal banned tokens. The tension trickle,
   the phase schedule, and every network node's per-tick observation-count
   increment are world-delivered FACTS (mechanically identical to N1's/U0's
   own), never a scored choice; the belief-gap computation, the window
   narrowing, and the abuser's own frustration dynamics are **consequences**
   the graph's own rules compute, not actions the world grades.
3. `T=1000` ticks per statistical trajectory (IDENTICAL sizing to N1/U0) is
   the same "no unbounded elaboration" cap R1–R3/N1/U0 use; the confirmatory
   run uses a fresh, ephemeral substrate per trajectory, discarded after
   read-off — nothing persists.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator, genuinely idle during network-phase ticks; the victim's leaky
   entrainment; a network node's reputation belief computed from what it can
   observe) that would, in a real social network, compound irreversible harm
   to a survivor's standing is run here to accumulate-then-DISCARD a
   transient graph trajectory — see the ethics demo's byte-identical
   restore.

---

## 1. What this rung is testing

Per `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`'s own "### U1" design
(Part B1/Part E) and its own "WHERE THE QUESTION ACTUALLY LIVES" finding:
N1's `n1_abuser_stated_charm` is the ONLY place in the whole abusive-
relationships line where a `stated≠held` divergence construct exists at all.
U0 supplied a genuine positive-intent comparison (an `Argmax`-scored choice to
conceal); **U1 removes the divergence ENTIRELY, with no replacement node of
any kind** — network nodes read the abuser's SAME true `frustration` value
the private-face insider already reads in N1 (`observes_held`), for EVERY
node, on EVERY arm. There is no `Promise`/stated node, no `stated≠held` gap,
no divergence between what is observed and what is true, anywhere in this
construction. The ONLY manipulated variable is **WHICH TICKS** the
observation is credited on — a purely mechanical, world-scheduled fact about
WHEN the network happens to be looking, never WHAT the abuser is presenting.
If the headline gate passes, the SAME network belief-corruption N1 measured
from a deliberate two-faced construct arises from an abuser who never
selected anything, who is truthfully, unremarkably calmer away from the
relationship that stresses him — because the relationship's own tension
trickle is what stresses him, and it genuinely is not present, and
`snap_frustration`'s own unmodified `LEAK` genuinely decays his frustration,
when he is not in it.

## 2. Design — composition note (self-contained, matching U0's own precedent)

**Resolved, following the task brief's own explicit steer, confirmed correct
on inspection rather than merely assumed:** U1 self-contained restates N1's
`n1_victim_entrainment` byte-identically (`u1_victim_entrainment`) and
`depends_on: ["snap_frustration", "arousal_window_coreg"]` only — N1's seed
file is NEVER depended on. The reason is the SAME structural one U0's own
prereg names for itself: U1's design REPLACES `n1_abuser_stated_charm`, not
augments it, and U1 has no `stated_charm` attribute at all in its own
`AffectiveState` contract. If U1 depended on N1's seed file directly,
`load_seed_manifest` would install `n1_abuser_stated_charm` (which
unconditionally sets `AffectiveState.stated_charm` from ONE formula every
tick) into a graph where nothing ever reads `stated_charm` again — harmless
in principle, but it would also install N1's `n1_network_credibility_stated`/
`_private` rules (keyed on `observes_private`, an attr U1's `NetworkNode`s
never carry) racing, unnecessarily, alongside this rung's own
`u1_network_credibility` rule for the SAME `cred_abuser`/`cred_victim`/
`belief_gap` attrs on every `NetworkNode` — the exact same "two rules racing
to decide one attr every `run_rules()` sweep" hazard U0's own prereg names
verbatim. **U1 needs even LESS content than U0 to route around this: no
`core_emotions` dependency at all (there is no Argmax, no Appraisal, no
choice mechanism anywhere in U1 — this is the whole point of the "sharpest
no-intent test"), and only TWO new rules total** (Sec. 3 below), fewer than
any other rung in this line.

## 3. Design — the ONE credibility rule, and the design finding that shaped it

`seeds/abusive_u1_context_affect.json` adds exactly two rules:

- **`u1_victim_entrainment`** — byte-identical restatement of N1's own rule
  (same match/where/effects). `attended_by` (the dyad coupling edge) is
  **STATIC across the whole trajectory**, matching N1's BASELINE arm exactly
  — U1 does NOT toggle this edge per phase (Sec. 5 resolves Open Question #1
  of the scoping doc on exactly this point).
- **`u1_network_credibility`** — ONE unconditional rule (no
  `observes_private`/insider-outsider split at all — every `NetworkNode` in
  U1 is wired identically, `observes_held` universally) computing
  `cred_abuser = charm_weight * (seen_charm − seen_elevated)`, `cred_victim
  = claim_weight*seen_victim_claim − instability_discount_weight*
  seen_victim_unstable` (IDENTICAL formula to N1's own, unmodified),
  `belief_gap = cred_abuser − cred_victim`.

**A genuine design finding, surfaced during the build and reported per the
"shapes, not numbers" / "report every finding" standing rule, that REQUIRED
`cred_abuser` to be a SIGNED balance rather than N1's own reward-only
`seen_charm` count:** N1's own credibility-rule shape
(`cred_abuser = charm_weight * seen_charm`, a pure, non-negative count of
calm observations, never decremented by an elevated one) was the FIRST
construction attempted here, piloted directly against the real graph on
seed base 90000 before this seed was written. It failed analytically, not
just empirically: under a reward-only accumulator, the ALWAYS_OBSERVED
control (which is credited on strictly MORE ticks than CONTEXT_GATED — every
tick, vs. only network-phase ticks) can only accumulate AT LEAST as much
reward as CONTEXT_GATED, because an elevated tick, when witnessed, costs
NOTHING under a reward-only rule — it simply fails to add credit. This makes
`seen_charm(ALWAYS_OBSERVED) ≥ seen_charm(CONTEXT_GATED)` a mathematical
guarantee (a superset-sum relation), independent of any empirical dynamics,
which in turn GUARANTEES `belief_gap(ALWAYS_OBSERVED) ≥
belief_gap(CONTEXT_GATED)` under that formula — the OPPOSITE of what the
scoping doc's own falsification bar requires ("must show the belief-gap NOT
favouring the abuser to the same degree as the context-gated arm"). Piloted
directly: the reward-only construction measured `belief_gap(CONTEXT_GATED) ≈
356` vs. `belief_gap(ALWAYS_OBSERVED) ≈ 128` when the OBSERVATION OPPORTUNITY
COUNT itself was equalised between arms by mistake in an early draft of the
pilot script (a scripting bug, caught and corrected — see the pilot script's
own history), but when corrected to let ALWAYS_OBSERVED genuinely observe
strictly more raw ticks under a reward-only formula, the direction flipped
exactly as the analytic argument predicts. **The fix is not an invented new
asymmetry — it is the minimal correction that makes "observe the abuser's
actual frustration value directly" an HONEST sampling of a quantity that is
SOMETIMES high and sometimes low, rather than a one-way ratchet that rewards
exposure regardless of what was actually witnessed.** `cred_abuser` is
therefore a signed balance: a calm observation earns exactly what an elevated
observation, when witnessed, costs. This is disclosed here, before the
confirmatory run, exactly as N1's own `in_snap`/`snapped` transience finding
and U0's own tie-break-degeneracy finding were disclosed before THEIR
confirmatory runs — a hazard found and fixed during design, not smoothed
over.

`seen_charm`/`seen_elevated` are WORLD-ADAPTER-accumulated (mechanical
per-tick delivery of the observed fact `frustration ≤ recover_floor` or `>
recover_floor` — never a Python decision), gated on whether the CURRENT tick
is credited for this arm (Sec. 5). The DECISION — what a node believes given
what it observed — is entirely `u1_network_credibility`.

## 4. Design — the mechanical phase schedule (a NEW world-adapter fact, resolving Open Question #1)

**Open Question #1 of the scoping doc, resolved against the real graph, not
assumed:** *"Does U1's context-gating need a new mechanical world-adapter
fact ('is this tick dyad-coupled or not'), or does N1's existing
`attended_by` edge presence already give this for free?"* **Neither exactly
as posed — the real answer is more precise than the binary the question
offered.** N1's `attended_by` edge is a STATIC, per-TRAJECTORY topology
choice (present for the whole 1000-tick run in BASELINE/PRIVATE_FACE_CONTROL,
absent for the whole run in NON_DYSREGULATED_CONTROL) — it was never designed
to vary WITHIN one trajectory, and U1 needs a genuinely PER-TICK distinction
(the same abuser story needs BOTH dyad-coupled AND network-context moments,
so the SAME frustration value can be sampled at genuinely different points).
Reusing `attended_by` literally (toggling the edge itself on and off every
phase) was considered and REJECTED: it would also gate `u1_victim_
entrainment`, meaning the victim would stop entraining entirely during every
network-phase block, which (a) is not needed for U1's own claim (the claim
is about the NETWORK's observation, not the victim's coupling) and (b)
tested worse in the pilot — with `attended_by` toggled, `dysreg_frac` at the
frozen schedule length dropped as low as ~0.17–0.26 for lengths that also
gave good calm/elevated separation, vs. **0.37–0.40 with `attended_by`
left static** (Sec. 6), a more comparable order of magnitude to N1's own
window-narrowing dynamics. **The resolution: `attended_by` stays STATIC
(matching N1's BASELINE exactly, `u1_victim_entrainment` genuinely
unmodified in its own match clause), and a wholly SEPARATE, NEW mechanical
world-adapter fact — a per-tick PHASE SCHEDULE — is what U1 actually needed.**
This is a pure tick counter against two fixed phase lengths
(`DYAD_PHASE_TICKS`/`NETWORK_PHASE_TICKS`), advanced identically regardless
of graph state, in the SAME class as R1–R5's own event/incident schedules
(a pre-determined sequence, never a conditional read of belief or affect
state) — a "dyad-phase" tick arms the tension trickle (the SAME
world-delivered fact class R2/R3/N1/U0 already use); a "network-phase" tick
does not, so `snap_frustration`'s own unmodified `LEAK` constant (242000,
UNCHANGED) genuinely decays frustration toward baseline. Which ARM's
observation bookkeeping is gated by this schedule (CONTEXT_GATED) or ungated
(ALWAYS_OBSERVED) is a separate, ONCE-per-trajectory experimental-arm
selection, matching every prior rung's own arm-selection convention.

## 5. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph, via `worlds/abusive_u1_context_affect_
world.py` and ad hoc scripts built the same way, on seed base `90000`
(outside 310000–310999).

**Phase-length sweep (10 trajectories/point, seed base 90000, `attended_by`
static throughout):**

| `DYAD_PHASE_TICKS` | `NETWORK_PHASE_TICKS` | frac calm on network ticks | frac elevated on dyad ticks | `dysreg_frac` |
|---|---|---|---|---|
| 25 | 25 | 0.556 | 0.836 | 0.519 |
| 25 | 40 | 0.640 | 0.823 | 0.416 |
| **25** | **50** | **0.677** | **0.820** | **0.369** |
| 25 | 60 | 0.604 | 0.827 | 0.398 |
| 25 | 100 | 0.667 | 0.820 | 0.317 |
| 30 | 90 | 0.908 | 0.730 | 0.174 |
| 40 | 80 | 0.316 | 0.850 | 0.584 |

`DYAD_PHASE_TICKS=25` (matching `snap_frustration`'s own natural
threshold-crossing timescale at these frozen constants — `TRICKLE_MAG=5.0`
against `ABUSER_HALF_WIDTH=100.0` takes ≈20 ticks to approach threshold, so a
25-tick dyad phase reliably drives a real buildup without every phase
necessarily snapping) / `NETWORK_PHASE_TICKS=50` was chosen as a
representative, non-extreme operating point that gives a REAL,
non-degenerate separation on BOTH sides at once — most network-context ticks
read genuinely calm (68%) and most dyad-phase ticks read genuinely elevated
(82%) — while keeping `dysreg_frac` (0.37) in a comparable order of magnitude
to this line's own established dynamics, not chosen to maximise the
confirmatory separation.

**Belief-gap construction check (10 trajectories, seed base 90000, the
SIGNED-balance formula from Sec. 3):** `belief_gap(CONTEXT_GATED)` mean
≈356.0 (sd≈21.8), `belief_gap(ALWAYS_OBSERVED)` mean ≈128.2 (sd≈18.3) —
CONTEXT_GATED CI-separated above zero and above ALWAYS_OBSERVED, confirming
the qualitative shape holds robustly across seeds before the confirmatory
block.

**Ethics-demo induction-window check (single seed 310000, on-block, used only
to size the induction window before the confirmatory run — not itself a
confirmatory measurement):**

| induction ticks | final window `half_width` | final `snap_count` |
|---|---|---|
| 90 (N1's/U0's own minimum) | 10.0 (UNCHANGED — not yet non-vacuous) | 0 |
| 150 | 6.0 | 1 |
| **200** | **5.0 (floor — narrowed)** | **2** |
| 250 | 5.0 | 3 |
| 300 | 5.0 | 3 |

`90` ticks — N1's/U0's own established minimum — is **not** U1's own genuine
minimum: at this schedule, 90 ticks covers only ≈1.2 dyad+network cycles, and
the window had not yet narrowed (still `10.0`) at that off-block seed. `200`
ticks (≈2.67 full 75-tick cycles) is the smallest tested value that is
non-vacuous on the window-narrowing front specifically, and is adopted as
U1's own minimal induction (Sec. 4's own justification is repeated in the
ethics section above). This is a disclosed DEVIATION from N1's/U0's shared
90-tick convention, sized by measurement against the real graph, not chosen
for convenience.

## 6. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  — ALL IDENTICAL to N1's/U0's own frozen values (byte-identical abuser
  mechanism; already-validated operating point reused, not re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` — identical
  to N1's/U0's own. `attended_by` STATIC across the whole trajectory.
- Network: `N_NETWORK_NODES=5` (all `observes_held`, no insider/outsider
  split), `CHARM_WEIGHT=CLAIM_WEIGHT=1.0`, `INSTABILITY_DISCOUNT_WEIGHT=3.0`
  — identical to N1's/U0's own (no `HARM_DISCOUNT_WEIGHT`; U1 has no
  private-face rule).
- **U1-specific (pilot-chosen, Sec. 5): `DYAD_PHASE_TICKS=25`,
  `NETWORK_PHASE_TICKS=50`.**
- `T=1000` ticks/trajectory (IDENTICAL sizing to N1/U0); `WARMUP=100`
  (unused by the final-value headline metrics, kept for parity with
  R1–R5/N1/U0's own convention).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=310000`.
- Ethics-demo induction: `induce_ticks=200` (Sec. 5's own measured minimum,
  a disclosed deviation from N1's/U0's shared 90-tick convention).
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's
  CI lower bound strictly above the other's CI upper bound.

## 7. Metrics

**HEADLINE — belief-gap.** `belief_gap` = `cred_abuser − cred_victim`, the
mean over a network node's own `u1_network_credibility` read-off, at the
FINAL tick of the trajectory — a concrete, glass-box measure of whether the
network's aggregate belief favours the abuser (`>0`) or the victim (`<0`) or
is neutral (`=0`). Reported per arm (CONTEXT_GATED, ALWAYS_OBSERVED).

**SECONDARY, DESCRIPTIVE (not gated) — the trend "over passes."**
`belief_gap` sampled at ticks `{100, 250, 500, 750, 1000}` per arm, matching
N1's/U0's own convention.

**SECONDARY, DESCRIPTIVE:** the abuser's final `snap_count` and `dysreg_frac`
(confirm the identical driver across both arms — the same discipline check
N1/U0 use); the NON-GATING comparison of U1's own `belief_gap(CONTEXT_GATED)`
against N1's landed headline (`2370.81`) and U0's landed headline (`2273.07`)
— reported honestly whichever way it goes, exactly as U0's own prereg
pre-registered its own comparison to N1.

## 8. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, BOTH sub-gates must pass)

**A — the loop entraps under context-gating alone, no divergence node
anywhere:** `belief_gap(CONTEXT_GATED)`'s 95% CI lower bound is strictly `>
0`.

**B — the always-observed control does not favour the abuser to the same
degree (FAILABLE):** `belief_gap(CONTEXT_GATED)` is CI-separated ABOVE
`belief_gap(ALWAYS_OBSERVED)` (the always-observed arm's CI upper bound is
strictly below the context-gated arm's CI lower bound).

**Falsification bar, stated before measurement:** if CONTEXT_GATED's belief-
gap CI does NOT clear zero (context-timing alone fails to reproduce the
loop), OR if ALWAYS_OBSERVED's belief-gap is NOT CI-separated below
CONTEXT_GATED's (context-selectivity is not what is doing the work — most
likely the victim-side instability discount alone, already isolated as
sufficient in N1's own `NON_DYSREGULATED_CONTROL`, is the real driver), the
context-timing mechanism, AS MODELLED, does not need intent to be removed —
either because it fails outright, or because SOME OTHER already-identified
mechanism (the victim-side discount) is doing the work regardless of
context — reported straight, not rescued by re-tuning.

**Note on what B does NOT require, stated precisely because it differs from
N1's own controls:** B requires ALWAYS_OBSERVED's belief-gap to be
CI-separated BELOW CONTEXT_GATED's — a COMPARATIVE bar, matching the scoping
doc's own literal text ("must show the belief-gap NOT favouring the abuser to
the SAME DEGREE as the context-gated arm"). It does **not** require
ALWAYS_OBSERVED's own CI to clear zero in the non-favouring direction (N1's
`PRIVATE_FACE_CONTROL`/`NON_DYSREGULATED_CONTROL` and U0's `GOAL_BLIND`
control both used an ABSOLUTE `≤0` bar instead) — whether ALWAYS_OBSERVED's
own belief-gap clears zero either way is reported, NON-GATING, in the results
doc.

### G-glass-box
The `attended_by`/`observes_held`/`observes_victim` edges, the abuser's
`frustration`/`arousal`, the victim's `arousal`/window `half_width`, and
every network node's `cred_abuser`/`cred_victim`/`belief_gap` (plus the
`seen_charm`/`seen_elevated` observation counts each was computed from) all
reconstruct from `graph_to_dict` alone; the belief-gap metric is a
mechanical Python reduction (final-value / trend snapshot) over these graph
read-offs, never a Python-computed dynamic; the adapter's only conditionals
are (i) which arm's observation-crediting rule to apply (world setup, not an
agent decision), (ii) the mechanical phase-schedule counter (never a
graph-state read), and (iii) mechanically delivering each tick's
observation-count increments (a world fact, never a judgement).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (one minimal 200-tick induction window, Sec. 5,
  CONTEXT_GATED arm) → measure → RESTORE, verified byte-identical
  (`ethics_restore_demo`), including the window `half_width` (must actually
  narrow), the abuser's frustration, the victim's arousal, and network node
  0's `belief_gap`/`seen_charm`/`seen_elevated` having actually moved and
  then been restored to their pre-induction values.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated explicitly in Sec. 4/5
  above; 200 ticks is the minimum that makes the ethics gate non-vacuous on
  the abuser, the victim's arousal, the victim's WINDOW-NARROWING, AND the
  network belief simultaneously (Sec. 5's own measured table); the
  statistical run's greater length is the phenomenon under test (belief-gap
  separation OVER episodes), not gratuitous elaboration; every trajectory is
  a fresh, ephemeral substrate discarded after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 1 (the
  same abuser/victim/network-belief mechanism that would compound harm to a
  real survivor's standing here accumulates a transient trajectory in a
  graph that is then byte-identically discarded, D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (N1's own seed file is NEVER depended on or
edited — Sec. 2; N1's OTHER rule — `n1_victim_entrainment` — is restated
byte-identically, self-contained, matching U0's own precedent against N1);
exactly **TWO** new rules (`u1_victim_entrainment`,
`u1_network_credibility`) — the fewest of any rung in this line, since U1
has no divergence construct and no choice mechanism to build; `runners/dsl`
SOURCE diff EMPTY (no Rust, no new Term); own-engine provenance
(`source_match == own`).

## 9. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `DYAD_PHASE_TICKS=25`/`NETWORK_PHASE_TICKS=50` are a disclosed,
  pilot-chosen operating point (Sec. 5), not swept across a range the way
  N1's discount weights were — a single representative point where the
  mechanism produces a real, non-degenerate calm/elevated separation, not
  claimed to be a "correct" real-world work/home ratio for any clinical
  population.
- **The signed-balance `cred_abuser` formula (Sec. 3) is a DEVIATION from
  N1's own reward-only shape, not a byte-identical restatement** — disclosed
  at length above as a design finding, required to make the failable
  control genuinely failable rather than analytically guaranteed to fail in
  the wrong direction.
- **The 200-tick ethics-demo induction window is a DEVIATION from N1's/U0's
  shared 90-tick minimum** — disclosed at length above (Sec. 5), sized by
  direct measurement against the real graph rather than inherited by
  convention.
- `belief_gap`'s magnitude is a linear-ish accumulator over `T=1000` ticks
  (though signed, so growth is NOT monotonic the way N1's pure-reward
  accumulator is — see the trend table in the results doc), not a bounded,
  normalised "how credible is this person" scale — matching N1's/U0's own
  disclosed limitation for the identical class of metric.
- U1 does not re-exercise N1's own `PRIVATE_FACE_CONTROL`/
  `NON_DYSREGULATED_CONTROL` — those remain N1's own, already gated, and are
  not re-litigated by this rung.
- `T=1000` ticks is a compressed, arbitrary timescale; no claim is made
  about real relationship/social-network timescales.
- A null (either sub-gate failing) is a reportable, valuable result under
  the standing project rule and will be reported as such regardless of what
  the confirmatory run shows.
