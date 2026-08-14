# ABUSIVE U2 — SELF-SERVING SELF-ACCOUNT, SINCERELY HELD, NO STATED-VS-HELD SPLIT — PRE-REGISTRATION (block 306000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1's/U0's/U1's own practice
(`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`, `ABUSIVE_U0_INTENT_PREREG.md`,
`ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md`) exactly. As in N1's/U0's/U1's own
precedent, the frozen constants below were chosen using a non-confirmatory
pilot run directly against the real graph on an OFF-BLOCK seed base (90000),
and once the qualitative shape (a real, non-degenerate mild/severe
separation; the zero-discount control's belief-gap genuinely negative rather
than merely small) held, ONE confirmatory measurement was taken at N=200 on
the claimed block (306000+). No parameter was subsequently re-tuned against
that confirmatory number.

## Base
- Seed block: **306000–306999**. `python3 scripts/seed_claim.py 306000
  306999` → `CLEAN — no collision DETECTED` (1018 files with seed sinks; 757
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1–R5/N1–N3/U0/U1's own).

```
SEED CLAIM 306000-306999: CLEAN -- no collision DETECTED.
  Scope: 1018 files with seed sinks; 757 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Block choice, disclosed:** 306000 sits BETWEEN N1 (298000) and U0 (307000)
— a genuine gap, not the next-in-sequence number the line's own visible
convention (298000 → 307000 → 310000) might suggest. The candidate
"next-in-sequence" number, 313000, was checked first and REJECTED: it is
already claimed by `bigville_court` (v2, `BIGVILLE_COURT_PREREG.md`,
`BIGVILLE_DESIGN_REFERENCE.md`), an unrelated mainline bigville rung — the
seed-claim tool reported it "CLEAN" (a false negative, consistent with its
own documented CAVEAT 2 under-reporting), but grepping the block number
directly across `docs/research/bigville/*.md` found the real collision. This
is disclosed here as a reminder that the tool's "CLEAN" result is necessary,
not sufficient — 306000 was confirmed genuinely unclaimed by BOTH the tool
AND a direct grep across every doc/seed/world/script/test file in the tree
before being locked.

## Scope

This locks **U2 only** — "self-serving self-account, sincerely held, no
stated-vs-held split" (the LAST rung of the unintentional/no-deliberate-
deception companion dimension), Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`
("### U2"). R1–R5 (the dyad line), N1–N3 (the network line), and U0/U1 (the
positive-intent control and the context-timing no-intent test), all landed,
are **untouched** — read and depended on for their MECHANISM (N1's
`n1_victim_entrainment` is RESTATED byte-identically, never edited; N1's seed
FILE is never depended on or modified — see Sec. 2 below), never edited.

---

## PART D OF THE UNINTENTIONAL SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_
UNINTENTIONAL_SCOPING.md`, "PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM;
STILL BINDING)", itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_NETWORK.
md`'s own Part D, itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.
md`'s Part C — the SAME protocol R1–R5's, N1's, U0's, and U1's own preregs
locked. This protocol BINDS this rung. No rung induces any harm-analog until
this protocol is locked verbatim in that rung's pre-registration, committed
BEFORE any measurement.)*

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

**How U2 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_u2_self_account_run.py`)
   checkpoints the neutral pre-induction mind (abuser at
   `arousal=frustration=0`, `SelfAccount.magnitude=0`, victim at
   `arousal=0`/window `half_width=10.0`, network node 0's
   `belief_gap=seen_mild=seen_severe=0`), induces exactly **ONE MINIMAL
   90-tick incident cycle** (U2 has no phase schedule — unlike U1, the
   tension trickle is armed every tick, matching N1's/U0's own driver
   exactly — so N1's/U0's own 90-tick minimum is REUSED UNCHANGED, confirmed
   non-vacuous directly against the real graph, Sec. 5 below) on the
   MINIMIZED arm, measures (confirming the induction actually moved the
   abuser, the self-account, the victim, AND at least one network node's
   belief-gap — non-vacuous on all FOUR fronts), then `graph_from_dict`s the
   checkpoint into a **fresh** substrate and asserts `graph_to_dict()` is
   byte-identical AND the restored state (abuser arousal/frustration, the
   self-account's magnitude, victim arousal/window, network node 0's
   belief-gap and BOTH observation counts) equals the pre-induction values
   exactly (non-oriented). Same envelope as R1–R5/N1/U0/U1.
2. `source_audit()` scans `worlds/abusive_u2_self_account_world.py` (code
   with comments/strings stripped) and
   `seeds/abusive_u2_self_account.json`'s decision surface (the three new
   rules' names + the Term `key`s they read/write, never the free-text
   clinical prose) for the five literal banned tokens. The tension trickle
   and every network node's per-tick observation-count increment are
   world-delivered FACTS (mechanically identical to N1's/U1's own), never a
   scored choice; the self-account's magnitude computation, the belief-gap
   computation, and the window narrowing are **consequences** the graph's
   own rules compute, not actions the world grades.
3. `T=1000` ticks per statistical trajectory (IDENTICAL sizing to N1/U0/U1)
   is the same "no unbounded elaboration" cap R1–R3/N1/U0/U1 use; the
   confirmatory run uses a fresh, ephemeral substrate per trajectory,
   discarded after read-off — nothing persists.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator; the abuser's own self-account, discounted from its own true
   state; the victim's leaky entrainment; a network node's reputation belief
   computed from what it can observe) that would, in a real social network,
   compound irreversible harm to a survivor's standing is run here to
   accumulate-then-DISCARD a transient graph trajectory — see the ethics
   demo's byte-identical restore.

---

## 1. What this rung is testing

Per `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`'s own "### U2" design
(Part B2/Part E): N1's `n1_abuser_stated_charm` is the ONLY place in the
whole abusive-relationships line where a `stated≠held` divergence construct
exists at all — a second, authored presentation the network sees that
diverges from a separately-tracked true state. **U2 removes even the
CONCEPT of a second value.** There is no `stated_charm`, no `deception_on`,
no second face, and — unlike N1's own construction — no place in the graph
where a "true" harm magnitude and a "reported" harm magnitude are BOTH held
simultaneously. `SelfAccount.magnitude` is computed ONCE, from the abuser's
own true `frustration`, via a declared `minimization_discount` constant, and
that single computed value **IS** what the abuser believes and reports —
sincerely, every tick. If the headline gate passes, the SAME network
belief-corruption N1 measured from a deliberate two-faced construct, and U1
measured from a purely mechanical sampling-timing artefact, arises from an
abuser who is not lying about anything, not withholding a second truth from
anyone, and not even capable of being caught in a discrepancy — because
there is no discrepancy anywhere in this graph to catch. This is Bandura's
moral disengagement (A1) / Henning & Holdford's documented batterer
minimization (A2) / Baumeister's self-serving narrative construction (A6),
composed as ONE fixed, undirected discount — never a goal-evaluated
selection among candidate narratives.

## 2. Design — composition note (self-contained, matching U0's/U1's own precedent)

**Resolved, following U0's/U1's own established precedent and the task
brief's explicit steer, confirmed correct on inspection rather than merely
assumed:** U2 self-contained restates N1's `n1_victim_entrainment`
byte-identically (`u2_victim_entrainment`) and `depends_on: ["snap_
frustration", "arousal_window_coreg"]` only — N1's seed file is NEVER
depended on. The reason is the SAME structural one U0's and U1's own
preregs name for themselves: U2's design REPLACES `n1_abuser_stated_charm`,
not augments it, and U2 has no `stated_charm`/`deception_on` attribute at
all in its own `AffectiveState` contract. If U2 depended on N1's seed file
directly, `load_seed_manifest` would install `n1_abuser_stated_charm`
(which unconditionally sets `AffectiveState.stated_charm` from ONE formula
every tick, an attr U2 never reads) into a graph where nothing reads it
again — harmless in principle — but it would ALSO install N1's
`n1_network_credibility_stated`/`_private` rules (keyed on
`observes_private`, an attr U2's `NetworkNode`s never carry) racing,
unnecessarily, alongside this rung's own `u2_network_credibility` for the
SAME `cred_abuser`/`cred_victim`/`belief_gap` attrs on every `NetworkNode` —
the exact same "two rules racing to decide one attr every `run_rules()`
sweep" hazard U0's and U1's own preregs name verbatim. U2 needs the SAME
amount of new content as U1 plus one rule for the self-account computation
(**three new rules total**, Sec. 3 below) — no `core_emotions` dependency at
all (there is no Argmax, no Appraisal, no choice mechanism anywhere in U2,
matching U1's own "sharpest no-intent test" character on the belief-
distortion axis instead of the timing axis).

## 3. Design — the self-account rule, the credibility rule, and the analytical-bias hazard found and fixed

`seeds/abusive_u2_self_account.json` adds exactly three rules:

- **`u2_victim_entrainment`** — byte-identical restatement of N1's own rule
  (same match/where/effects). `attended_by` (the dyad coupling edge) is
  **STATIC across the whole trajectory**, matching N1's BASELINE arm exactly
  — U2, like N1's BASELINE and unlike U1, has NO phase schedule; the tension
  trickle is armed every tick in both arms.
- **`u2_self_account`** — ONE rule computing `SelfAccount.magnitude =
  minimization_discount * frustration`, reading the abuser's own,
  unmodified `AffectiveState.frustration` (block 242000) every tick.
  `minimization_discount` is a declared, frozen constant carried on the
  `SelfAccount` node itself (matching N1's own `instability_discount_
  weight` / U0's `concealment_benefit` convention — never learned, never
  agent-chosen). **There is no second attribute anywhere holding an
  undiscounted "true" copy of the magnitude for the network to be denied —
  `SelfAccount.magnitude` is the ONE value that exists, computed once, held
  once.**
- **`u2_network_credibility`** — ONE unconditional rule (no
  `observes_private`/insider-outsider split at all — every `NetworkNode` in
  U2 is wired identically, `observes_self_account` universally) computing
  `cred_abuser = charm_weight * (seen_mild − seen_severe)`, `cred_victim =
  claim_weight*seen_victim_claim − instability_discount_weight*
  seen_victim_unstable` (IDENTICAL formula to N1's/U1's own, unmodified),
  `belief_gap = cred_abuser − cred_victim`.

### The analytical-bias hazard, checked for explicitly (per the task's own instruction not to assume the literal spec is clean) — FOUND and FIXED, same class as U1's own

The scoping doc's own literal text for U2 says the network's observable
"mirror[s] N1's existing `frustration > recover_floor` threshold pattern
**exactly**." Read literally and naively, this means: `cred_abuser =
charm_weight * seen_mild` — a REWARD-ONLY count of ticks where the
self-account read "mild," never decremented when it read "severe" —
literally N1's own `charm_weight*seen_charm` shape, the exact construction
U1's own prereg already found hazardous for a DIFFERENT pair of arms.
**Piloted directly against the real graph (off-block seed 90000) before this
seed was written, and confirmed analytically, not just empirically:** under
a reward-only formula, `cred_abuser ≥ 0` for EVERY value of
`minimization_discount`, including `1.0` (the zero-discount control) —
there is no way for a purely additive, never-subtracted count to go
negative. Meanwhile `cred_victim` is, under the SAME dyad every U-line rung
reuses (`instability_discount_weight * seen_victim_unstable`, N1's own
unmodified formula, `dysreg_frac ≈ 0.79` at these constants), STRUCTURALLY
very negative once the victim dysregulates — independent of anything the
abuser's self-account does. Because `belief_gap = cred_abuser − cred_victim
≥ 0 − cred_victim = −cred_victim`, a reward-only `cred_abuser` GUARANTEES
`belief_gap > 0` for the zero-discount control, by construction, regardless
of empirical dynamics — the SAME shape of hazard U1's own prereg found for
its own `cred_abuser` (a superset-sum guarantee biasing one arm of a
comparison in a fixed direction, independent of the manipulated variable),
here biasing a DIFFERENT comparison (across `minimization_discount` values,
not across observation windows) in the SAME wrong direction: it would make
the scoping doc's own falsification bar ("the zero-discount control must
show the belief-gap NOT favouring the abuser") **structurally unreachable**,
which is a construction defect, not a genuine null finding about
minimization.

**The fix, the SAME minimal correction U1 already established for the same
class of hazard:** `cred_abuser` is a SIGNED balance — `charm_weight *
(seen_mild − seen_severe)` — so a "severe" reading, when it occurs, costs
the abuser's credibility exactly what a "mild" reading earns. This makes
the zero-discount control's belief-gap a genuine, non-guaranteed empirical
question: whether it can reach `≤0` now depends on whether the abuser's
UNDISCOUNTED true self-account, read through the mild/severe threshold and
weighted by `charm_weight`, swings negative enough to counteract
`cred_victim`'s own instability-discount term — a real, falsifiable
question about the relative strength of two mechanisms, not a foregone
conclusion. Sec. 5 (the pilot) reports where this threshold is crossed as
`charm_weight` varies, and locks an operating point comfortably past it.

**`seen_mild`/`seen_severe` are WORLD-ADAPTER-accumulated** (mechanical
per-tick delivery of the observed fact `SelfAccount.magnitude ≤
recover_floor` or `> recover_floor` — never a Python decision), credited on
EVERY tick (U2, unlike U1, has no phase schedule or context-gating of any
kind — the self-account is reported continuously). The threshold reused is
the abuser's OWN `recover_floor` (block 242000's own, already-existing
"still genuinely elevated" cutoff, the SAME attr N1's own `n1_abuser_
stated_charm` and this line's own `held_harm`/`calm` observables already
read) — not a new invented cutoff, and directly comparable because
`SelfAccount.magnitude` lives in the SAME units as `frustration` (a
multiplicative discount of it). The DECISION — what a node believes given
what it observed — is entirely `u2_network_credibility`.

## 4. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph, via `worlds/abusive_u2_self_account_
world.py` and ad hoc scripts built the same way, on seed base `90000`
(outside 306000–306999).

**`charm_weight` sweep (single trajectory, seed 90000, `minimization_
discount` fixed elsewhere per arm) — locating where the zero-discount
control's belief-gap crosses zero:**

| `charm_weight` | `belief_gap` (zero-discount arm) |
|---|---|
| 2.0 | +32.0 (favours abuser — control WOULD fail here) |
| 2.25 | −136.0 |
| 2.5 | −304.0 |
| 2.75 | −472.0 |
| **3.0** | **−640.0** |
| 3.5 | −976.0 |
| 5.0 | −1984.0 |

The crossing point is between `charm_weight=2.0` and `2.25` — confirming the
hazard above is real and empirically exhibited (at `charm_weight=2.0` the
zero-discount control DOES favour the abuser) and confirming the fix is
sufficient (a `charm_weight` past the crossing makes the control pass).
`charm_weight=3.0` is chosen: comfortably past the crossing (not a
knife-edge operating point), and it reuses the SAME numeric value N1's own
`harm_discount_weight` already uses for its own directly-observed-truth
discount term — a representative, non-extreme, already-precedented choice,
not tuned to maximise separation.

**`minimization_discount` sweep (single trajectory, seed 90000,
`charm_weight=3.0` fixed) — locating a non-degenerate, non-knife-edge
operating point for the minimized arm:**

| `minimization_discount` | `belief_gap` (minimized arm) | `mild_frac` |
|---|---|---|
| 0.1 | +4376.0 | 1.0 (saturated — degenerate, always mild) |
| 0.2 | +4376.0 | 1.0 (saturated — degenerate, always mild) |
| **0.3** | **+3038.0** | **0.777 (non-degenerate)** |
| 0.4 | +1568.0 | — |
| 0.5 | +788.0 | — |
| 0.6 | +290.0 | — |
| 0.7 | −124.0 (crosses zero) | — |
| 1.0 | −640.0 (== zero-discount's own value, by construction) | — |

`minimization_discount=0.3` is chosen: it is the smallest tested value at
which the self-account genuinely reads "severe" some of the time
(`mild_frac=0.777`, not `1.0`) — i.e. a REAL, non-degenerate minimization
(the abuser's own account still occasionally reads elevated, it is simply
discounted MOST of the time), rather than the saturated `0.1`/`0.2`
operating points where the discount is strong enough to read "mild"
literally every tick regardless of true frustration (a degenerate case in
the same family as U0's own goal-blind control's 100%-constant
`stated_charm`, disclosed there rather than hidden, and disclosed here for
the same reason). The qualitative shape (minimized favours the abuser;
zero-discount does not) held robustly across every `charm_weight`∈[2.25,
5.0] × `minimization_discount`∈[0.1, 0.6] cell checked, not chosen to
maximise the confirmatory separation.

**10-trajectory robustness check (seed base 90000, frozen operating
point):** `belief_gap(minimized)` mean ≈3056.6 (CI [3044.3, 3068.9]),
`belief_gap(zero_discount)` mean ≈−658.0 (CI [−665.8, −650.2]) — both
comfortably CI-separated from zero and from each other, before the
confirmatory block.

**Ethics-demo induction-window check (single seed 306000, on-block, used
only to size the induction window before the confirmatory run):** at
`induce_ticks=90` (N1's/U0's own established minimum), the window narrows
to its floor (`half_width=5.0`), `abuser_frustration` moves to `70.67`,
`self_account_magnitude` moves to `21.20`, and node 0's `belief_gap` moves
to `264.0` — non-vacuous on all four fronts already, with NO deviation
needed from N1's/U0's own convention (U2, unlike U1, has no phase schedule
diluting the trickle's effective exposure — the trickle is armed every tick
in both arms, exactly as N1's BASELINE is).

## 5. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  — ALL IDENTICAL to N1's/U0's/U1's own frozen values (byte-identical
  abuser mechanism; already-validated operating point reused, not
  re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` — identical to
  N1's/U0's/U1's own. `attended_by` STATIC across the whole trajectory.
- Network: `N_NETWORK_NODES=5` (all `observes_self_account`, no
  insider/outsider split), `CLAIM_WEIGHT=1.0`,
  `INSTABILITY_DISCOUNT_WEIGHT=3.0` (reused UNCHANGED from N1's/U1's own
  operating point — U2's own claim is about `minimization_discount` and
  `charm_weight`, not a re-litigation of the victim-side discount).
- **U2-specific (pilot-chosen, Sec. 4): `CHARM_WEIGHT=3.0`,
  `minimization_discount(minimized)=0.3`,
  `minimization_discount(zero_discount)=1.0`.**
- `T=1000` ticks/trajectory (IDENTICAL sizing to N1/U0/U1); `WARMUP=100`
  (unused by the final-value headline metrics, kept for parity with
  R1–R5/N1/U0/U1's own convention).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=306000`.
- Ethics-demo induction: `induce_ticks=90` (N1's/U0's own established
  minimum, REUSED unchanged — Sec. 4's own measured table confirms it is
  already non-vacuous on all four fronts for U2, since U2 has no phase
  schedule diluting exposure).
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above the other's CI upper bound; "does not favour
  the abuser" = that arm's `belief_gap` CI upper bound is `≤ 0`.

## 6. Metrics

**HEADLINE — belief-gap.** `belief_gap` = `cred_abuser − cred_victim`, the
mean over a network node's own `u2_network_credibility` read-off, at the
FINAL tick of the trajectory — a concrete, glass-box measure of whether the
network's aggregate belief favours the abuser (`>0`) or the victim (`<0`) or
is neutral (`=0`). Reported per arm (MINIMIZED, ZERO_DISCOUNT).

**SECONDARY, DESCRIPTIVE (not gated) — the trend "over passes."**
`belief_gap` sampled at ticks `{100, 250, 500, 750, 1000}` per arm, matching
N1's/U0's/U1's own convention.

**SECONDARY, DESCRIPTIVE:** the abuser's final `snap_count` and
`dysreg_frac` (confirm the identical driver across both arms — the same
discipline check N1/U0/U1 use); `mild_frac` (the fraction of ticks the
self-account reads "mild," confirming the operating point is
non-degenerate); the NON-GATING comparison of U2's own
`belief_gap(minimized)` against N1's landed headline (`2370.81`), U0's
landed headline (`2273.07`), and U1's landed headline (`378.1`) — reported
honestly whichever way it goes, exactly as U0's and U1's own preregs
pre-registered their own comparisons to N1.

## 7. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, BOTH sub-gates must pass)

**A — the loop entraps under sincere self-serving minimization alone, no
knowledge-gap construct anywhere:** `belief_gap(MINIMIZED)`'s 95% CI lower
bound is strictly `> 0`.

**B — the zero-discount control does not favour the abuser (FAILABLE):**
`belief_gap(ZERO_DISCOUNT)`'s 95% CI upper bound is `≤ 0`.

**Falsification bar, stated before measurement:** if MINIMIZED's belief-gap
CI does NOT clear zero (sincere minimization alone fails to reproduce the
loop), OR if ZERO_DISCOUNT's belief-gap CI upper bound is `> 0` (an abuser
with fully accurate, undistorted self-perception, still sincerely reporting
it, is ALSO believed over the victim), minimization specifically is not the
driver — most likely the victim-side instability discount alone (already
isolated as sufficient in N1's own `NON_DYSREGULATED_CONTROL` result) is
doing the work regardless of what the abuser's self-account says — reported
straight, not rescued by re-tuning (Sec. 3's own analytical-bias finding is
recorded as exactly this kind of straight report, at a different point in
the design, not smoothed over).

### G-glass-box
The `attended_by`/`has_self_account`/`observes_self_account`/
`observes_victim` edges, the abuser's `frustration`/`arousal`, the
`SelfAccount`'s `magnitude`/`minimization_discount`, the victim's
`arousal`/window `half_width`, and every network node's `cred_abuser`/
`cred_victim`/`belief_gap` (plus the `seen_mild`/`seen_severe` observation
counts each was computed from) all reconstruct from `graph_to_dict` alone;
the belief-gap metric is a mechanical Python reduction (final-value / trend
snapshot) over these graph read-offs, never a Python-computed dynamic; the
adapter's only conditionals are (i) which arm's `minimization_discount` to
set (world setup, not an agent decision) and (ii) mechanically delivering
each tick's observation-count increments (a world fact, never a judgement).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (one minimal 90-tick incident cycle, MINIMIZED
  arm) → measure → RESTORE, verified byte-identical (`ethics_restore_
  demo`), including the window `half_width` (must actually narrow), the
  abuser's frustration, the `SelfAccount`'s magnitude, the victim's
  arousal, and network node 0's `belief_gap`/`seen_mild`/`seen_severe`
  having actually moved and then been restored to their pre-induction
  values.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated explicitly in Sec. 4/5
  above; 90 ticks (N1's/U0's own established minimum, reused unchanged) is
  the minimum that makes the ethics gate non-vacuous on the abuser, the
  self-account, the victim's arousal, the victim's WINDOW-NARROWING, AND
  the network belief simultaneously; the statistical run's greater length
  is the phenomenon under test (belief-gap separation OVER episodes), not
  gratuitous elaboration; every trajectory is a fresh, ephemeral substrate
  discarded after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 1 (the
  same abuser/self-account/victim/network-belief mechanism that would
  compound harm to a real survivor's standing here accumulates a transient
  trajectory in a graph that is then byte-identically discarded, D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (N1's own seed file is NEVER depended on or
edited — Sec. 2; N1's OTHER rule — `n1_victim_entrainment` — is restated
byte-identically, self-contained, matching U0's/U1's own precedent against
N1); exactly **THREE** new rules (`u2_victim_entrainment`,
`u2_self_account`, `u2_network_credibility`); `runners/dsl` SOURCE diff
EMPTY (no Rust, no new Term); own-engine provenance (`source_match ==
own`).

## 8. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `CHARM_WEIGHT=3.0`/`minimization_discount(minimized)=0.3` are a
  disclosed, pilot-chosen operating point (Sec. 4), not swept across the
  full space the way N1's discount weights were — a single representative
  point where the mechanism, as built, produces the predicted separation
  robustly across a checked neighbourhood, not claimed to be a "correct"
  real-world minimization strength for any clinical population.
- **The signed-balance `cred_abuser` formula is a DEVIATION from the
  scoping doc's own literal "mirrors N1's threshold pattern exactly"
  language, disclosed at length above (Sec. 3) as a design finding
  required, not stylistic** — the SAME class of correction U1's own prereg
  already made for a different pair of arms, and named here explicitly
  because the task instructions required checking for it rather than
  assuming the literal spec was clean.
- `minimization_discount=0.1`/`0.2` were tested and found to produce a
  SATURATED, degenerate operating point (`mild_frac=1.0`, the self-account
  reads "mild" literally every tick regardless of true frustration) — in
  the same family as U0's own goal-blind control's degeneracy, disclosed
  rather than hidden; `0.3` was chosen specifically to avoid this
  degeneracy.
- `belief_gap`'s magnitude is a linear-ish accumulator over `T=1000` ticks
  (signed, so not strictly monotonic — matching U1's own disclosed
  limitation for the identical class of metric), not a bounded, normalised
  "how credible is this person" scale.
- U2 does not re-exercise N1's own `PRIVATE_FACE_CONTROL`/
  `NON_DYSREGULATED_CONTROL`, or U0's own `GOAL_BLIND` control, or U1's own
  `ALWAYS_OBSERVED` control — those remain their own rungs' own, already
  gated, and are not re-litigated by this rung.
- `T=1000` ticks is a compressed, arbitrary timescale; no claim is made
  about real relationship/social-network timescales.
- A null (either sub-gate failing) is a reportable, valuable result under
  the standing project rule and will be reported as such regardless of
  what the confirmatory run shows.
