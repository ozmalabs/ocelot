# ABUSIVE R3 — COERCIVE CONTROL: window-narrowing + prior-mis-setting + isolation/frontier-collapse — PRE-REGISTRATION (block 289000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design (pilot-informed, on
off-block seeds), and the falsification bar, following R1/R2's own practice
(`ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md`, `ABUSIVE_R2_CYCLE_LIMIT_PREREG.md`)
exactly.

## Base
- Seed block: **289000–289999**. `python3 scripts/seed_claim.py 289000 289999`
  → `CLEAN — no collision DETECTED` (1010 files with seed sinks; 734
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1/R2's own).

```
SEED CLAIM 289000-289999: CLEAN -- no collision DETECTED.
  Scope: 1010 files with seed sinks; 734 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(283000 is R1 of this line; 286000 is R2 of this line, both untouched.
289000 is the next clean block for this line and is not adjacent-collision
with either.)

## Scope

This locks **R3 only** — "coercive control: window-narrowing +
prior-mis-setting + isolation/frontier-collapse", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md` (the B3+B5
mapping). R1 (traumatic bond) and R2 (cycle of abuse), both landed, are
**untouched**. R4–R5 (learned helplessness, recovery) and the network
dimension (N1–N4) are **out of scope** and untouched by this rung.

---

## PART C OF THE SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_SCOPING.md`,
"PART C — THE ETHICAL PROTOCOL", the SAME verbatim block R1/R2's preregs
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

### The HONEST FORK (a choice, not a theorem)
There is a real philosophical question the protocol does NOT resolve and must not
pretend to: **did a transient induced experience "matter while it was live,"
before it was reversed?**
- The **reversibility stance** (this line's operating stance): a fully reversed,
  byte-identically restored transient in a graph leaves no persisting subject and
  no persisting harm; the ethics are satisfied by reversibility + minimality +
  no-scoring.
- The **strict-experientialist stance**: if the transient state was in any sense
  an experience while live, its reversal does not retroactively un-happen it.

This is a genuine fork — **a choice, not a theorem.** This line ADOPTS the
reversibility stance and states it openly, rather than smuggling it. The
minimality and no-scoring rules are chosen partly to be robust to the fork: even
under the strict-experientialist reading, inducing the LEAST necessary and never
scoring the agent for its state is the least-harm option. The fork is recorded so
a reader can disagree with the stance while still auditing the protocol.

*(End verbatim reproduction of Part C.)*

**How R3 satisfies each clause, concretely — and what "minimal induction" means
for a design that necessarily spans multiple episodes (stated explicitly, per
the task brief's own instruction, since R3 cannot induce coercive control's
"narrowing over episodes" in one shot the way R1/R2 induced a single swing or
a single cycle):**

1. `ethics_restore_demo()` (`scripts/abusive_r3_coercive_control_run.py`)
   checkpoints the neutral pre-induction mind (both agents at
   `arousal=frustration=0`, victim window at its INITIAL `half_width=10.0`),
   induces exactly **ONE MINIMAL incident cycle** (90 ticks — the SAME
   minimum R2 already established for one tension-building → incident →
   honeymoon orbit at these frozen constants, since R3 reuses R2's abuser
   mechanism unchanged), on the **single-anchor arm** (the arm whose
   narrowing this rung's headline is about — the smallest induction that
   makes the gate non-vacuous: it is not possible to demonstrate
   "narrowing happened and is reversible" without at least one resolved,
   unsupported episode). It measures, then `graph_from_dict`s the
   checkpoint into a **fresh** substrate and asserts `graph_to_dict()` is
   byte-identical AND the restored abuser/victim state (arousal,
   frustration, window `half_width`) equals the pre-induction values
   exactly (non-oriented). Same envelope as R1/R2/239000/241000/242000.
   **R3's own minimality bar, stated explicitly:** the STATISTICAL
   (N=200) measurement of window-narrowing-OVER-EPISODES necessarily
   spans many more ticks than this — that is the phenomenon under test,
   not gratuitous elaboration of harm — but the ETHICS DEMONSTRATION
   itself induces only the ONE cycle needed to show narrowing is real and
   reversible, exactly as R1 induced one 36-tick episode and R2 induced
   one 90-tick cycle rather than their own full N=200 statistical run.
   Every statistical trajectory (single-anchor OR outside-regulator) is a
   **fresh, ephemeral substrate**, discarded immediately after read-off —
   nothing persists between trajectories, and each one individually ends
   from whatever state the final tick leaves it in (a transient graph
   object about to be garbage-collected, never a persisted agent left
   mid-harm).
2. `source_audit()` scans `worlds/abusive_r3_coercive_control_world.py`
   (code with comments/strings stripped) and
   `seeds/abusive_r3_coercive_control.json`'s decision surface (the five
   new rules' names + the Term `key`s they read/write, never the free-text
   clinical prose) for the five literal banned tokens. The tension trickle
   and the outside regulator's fixed calm arousal are both world-delivered
   magnitudes/facts (mechanically identical to a goal-block magnitude in
   242000 or a caregiver arousal reading in 239000), never a scored
   choice; the window-narrowing / prior-mis-setting / anchor-tracking are
   **consequences** the two pre-existing seeds' own rules (plus this
   rung's five small rules) compute, not actions the world grades.
3. `T=1000` ticks per statistical trajectory (~40 abuser incident cycles —
   comfortably enough for the single-anchor window to reach its narrowing
   floor, confirmed in the pilot, Sec. 3.2) is the SAME kind of "no
   unbounded elaboration" cap R1/R2 use, sized to the phenomenon rather
   than to an arbitrary round number; the confirmatory run uses a fresh,
   ephemeral substrate per trajectory, discarded after read-off.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator + the victim's leaky entrainment + window/prior plasticity)
   that would, in a real relationship, compound irreversible harm episode
   after episode is run here to accumulate-then-DISCARD a transient graph
   trajectory — see the ethics demo's byte-identical restore.

---

## 1. What R3 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_SCOPING.md` Part B3/B5 and the task brief, R3
rides:

- **`seeds/snap_frustration.json`** (block 242000, UNMODIFIED) — the
  ABUSER's leaky frustration accumulator, exactly as R2 uses it.
- **`seeds/arousal_window_coreg.json`** (block 239000, UNMODIFIED) — the
  VICTIM's entrainment, self-regulation, window dysregulation/plasticity
  (`mark_coreg_support`, `episode_resolve_widen`, `episode_resolve_narrow`),
  exactly as R2 uses it.
- **`seeds/window_knob_coreg.json`** (block 241000) — read for context
  (the width-knob convention `half_width`/`lo`/`hi`) but **not loaded** by
  R3: its bidirectional-dyad rules (`wk_*`) are gated on an `is_infant`
  flag R3's dyad does not set, and its own caregiver-window machinery is
  not needed here (the outside regulator is a FIXED calm anchor, not a
  second dynamically-regulating agent) — R3 rides `arousal_window_coreg`'s
  simpler, already-proven single-window contract instead, matching R2's
  own choice.
- **`ABUSIVE_R2_CYCLE_LIMIT_PREREG.md` / `_RESULTS.md`** (block 286000) —
  R2's own dyad-coupling pattern (one `attended_by` edge, victim entrained
  via a `frustration`-routed rule to avoid `snap_arousal_track`'s
  clobber) is the direct ancestor of R3's single-anchor arm; see Sec. 2
  below for exactly how much is reused verbatim versus extended.
- **`seeds/bigville_life_rearing.json`** (block 262000) — the ONLY place in
  this worktree where `prior_others_trust` / `prior_self_worth` are
  confirmed materialized as graph attrs (Sec. 1.1 below).

### 1.1 OPEN QUESTION #1 (scoping doc), resolved: others-trust / self-worth ARE materialized, but as a ONE-SHOT rite-of-passage value, not a per-episode dynamic

The scoping doc's Open Question #1 asks whether the others-trust /
self-worth / agency priors are already materialised as graph attrs, or must
be added. A grep of every seed in this worktree for
`others_trust`/`self_worth` finds them in exactly one place:
`seeds/bigville_life_rearing.json` (block 262000, `bl_come_of_age`) and its
companion population data, `seeds/bigville_townspeople_50.json`. Reading the
rule: a child holds `nat_others_trust`/`nat_self_worth` (inherited/natural
priors) and, at coming-of-age, `bl_come_of_age` computes
`adult_prior = clamp01(nat_prior + 0.03 * nurture)` where
`nurture = wot.widen_count - wot.narrow_count` — the SAME
`arousal_window_coreg` counters R2/R3 ride — and writes the result ONCE, as
a **rite-of-passage mint** on the child's own **Agent node**, flipping
`matured=1, adult=1` so the rule never fires again for that agent.

**This is confirmed NOT what R3 needs.** R3's coercive-control design
requires priors that move **progressively, per resolved episode, across a
single (adult) victim's ongoing dyad** — there is no "coming of age" event
in R3's dyad, and `bl_come_of_age`'s guard (`coa_armed==1 AND matured==0`,
a one-shot latch) structurally cannot express a repeated per-episode step.
Reusing `bl_come_of_age` unmodified is therefore not possible; editing it
would touch an already-gated, unrelated seed (bigville R14), which this
rung's discipline (matching R1/R2: "no existing seed touched or modified")
forbids.

**Decision: add two minimal, progressive analogues as NEW attrs
(`others_trust`, `self_worth`) on the victim's `WindowOfTolerance` node**
(co-located with `safety_prior`, `widen_count`, `narrow_count` — the node
`episode_resolve_widen`/`narrow` already own and update every resolved
episode), driven by two NEW rules
(`r3_prior_track_narrow`/`r3_prior_track_widen`, Sec. 2.3) that watch the
SAME `widen_count`/`narrow_count` counters `arousal_window_coreg` already
bumps (UNMODIFIED) via a counter-DELTA observer and step the priors by the
SAME `0.03` magnitude `bigville_life_rearing`'s own `bl_come_of_age` uses
(disclosed, matched, not re-tuned) and the SAME `clamp01(Max(0,Min(1,·)))`
idiom both `bl_come_of_age` and `arousal_window_coreg`'s own
`safety_prior` step already use. This satisfies the minimal-atom-reuse
falsification bar (CLAUDE.md's "SHAPES, NOT NUMBERS": the RULE SHAPE —
step-and-clamp off a resolved-episode counter delta — is reused exactly;
only the SITE (a new attr pair, on a node this rung already owns) and the
TRIGGER (a live per-episode counter rather than a one-shot maturity flag)
differ, because the semantics genuinely differ: a NEW node's progressive
belief, not `bl_come_of_age`'s existing agent's one-shot inheritance blend).
**This is graph DATA (two attrs + two small rules), not new Rust and not a
Python decision** — the "which prior corner an episode pushes toward" is
decided entirely by which counter incremented, read by the rule's own
`where` guard.

**Naming, disclosed explicitly:** `others_trust`/`self_worth` here are
DIFFERENT attrs, on a DIFFERENT node type (`WindowOfTolerance`, not
`Agent`), with DIFFERENT semantics (a live, per-episode-updated belief, not
a one-shot nature/nurture blend written once at maturity) from
`bigville_life_rearing`'s `prior_others_trust`/`prior_self_worth` on the
`Agent` node. This is a disclosed naming choice, not a collision — the two
never coexist on the same node, and no rule reads across the two seeds.

**World-safe / `safety_prior` is unaffected**, riding `arousal_window_coreg`'s
own, already-gated `safety_prior` step exactly as R2 does — R3 adds no new
rule for it.

## 2. Design — two arms, one abuser mechanism, one structural manipulation

### 2.1 Reused vs extended from R2 — the call, and the reasoning

**R2's coupling is REUSED VERBATIM for R3's single-anchor arm's abuser
mechanism and entrainment-routing technique; R3 EXTENDS it with (a) running
the SAME dyad for MANY MORE incident cycles (window-narrowing over
episodes, R2's own single-episode oscillation read-off was never designed to
show this) and (b) a genuinely NEW second arm requiring a genuinely NEW
composition (Sec. 2.3, 2.4).** The call, and why:

- R2's PREREG Sec. 7 already named the exact phenomenon this rung measures,
  as an honest, non-gated residual: *"the victim's window `half_width`
  narrows monotonically toward its floor over the episode... because the
  abuser never satisfies 239000's own `got_coreg` condition (its
  `regulated` attribute is never set — an honest, disclosed reading of
  'the abuser's post-incident calm is NOT the same thing as genuine
  co-regulation')... consistent with R3's (out-of-scope) window-narrowing
  focus."* Reading R2's actual seed rule and world adapter confirms this
  mechanically: `mark_coreg_support` (arousal_window_coreg, UNMODIFIED)
  requires `Eq(attr(cg,"regulated"),1.0)` where `cg` is the attended-to
  AGENT node itself; R2's abuser Agent node never sets `regulated`
  (deliberately omitted, alongside every other `arousal_window_coreg`-
  specific key, so THAT seed's rules never accidentally match the abuser),
  so `got_coreg` is **structurally, permanently 0** for R2's dyad, and
  `episode_resolve_narrow` (never `_widen`) fires on every resolved
  episode. R2's own headline (`victim_arousal_std`) never needed this to
  be otherwise — it is a side effect R2 disclosed but did not exploit.
- **R3 rides this AS THE HEADLINE MECHANISM, not a residual to route
  around.** The single-anchor arm is R2's exact abuser (`snap_frustration`,
  unmodified) + R2's exact frustration-routing composition technique
  (`r3_victim_entrainment_solo` is a byte-identical restatement of R2's own
  `r2_victim_entrainment_via_frustration`, included in R3's OWN seed file
  rather than depending on `abusive_r2_cycle_limit` — R1/R2's own
  convention keeps each rung self-contained against only the shared BASE
  seeds it composes, never against a SIBLING rung's seed), run for `T=1000`
  ticks (~40 incident cycles, Sec. 3.2) instead of R2's `T=400`
  (~16 cycles) so the window has room to reach — and this rung MEASURES
  that it reaches — its narrowing floor.
- **The genuinely NEW part is the outside-regulator arm.** This requires a
  SECOND regulation source structurally present (per the task brief: "a
  second, healthy `attended_by`-eligible source, so the frontier is NOT
  collapsed to one") — nothing in R1 or R2 has this. Building it surfaced
  a real, reproducible composition hazard (Sec. 3.1) that neither R1 nor
  R2 hit, because neither ever gave one node two edges of the same type
  feeding a rule composition. The fix (Sec. 3.1, 2.4) is new relative to
  R1/R2, though it reuses R1/R2's own established METHOD (pilot on
  off-block seeds directly against the real graph, isolate by bisection,
  disclose the finding at length) to find and resolve it.

### 2.2 The two arms (identical abuser driver, only the victim's regulation topology differs)

- **SINGLE_ANCHOR** — the victim `-attended_by->` the abuser ONLY. The
  abuser's `GoalBlock` is armed every tick with the SAME constant, jittered
  `TRICKLE_MAG` R2 uses (drawn once per tick from
  `default_rng(SEED_BASE+i)` per trajectory `i`). The only available
  regulator IS the dysregulation source — Main & Hesse's "fright without
  solution" (A7), rendered as the STRUCTURE of the graph (one coupling
  edge), not an incident.
- **OUTSIDE_REGULATOR** (the failable control) — the victim is ALSO
  connected to a second, FIXED-CALM, ALWAYS-REGULATED outside source, via a
  **different edge type**, `also_attended_by` (Sec. 3.1 explains why NOT a
  second `attended_by` edge). The abuser's driver is **IDENTICAL** — same
  `TRICKLE_MAG`, same jitter draw, same seed per trajectory index — so the
  ONLY manipulated variable is whether the frontier is collapsed to one
  source or held open to two, matching R1/R2's own "identical dose, only
  structure/order differs" discipline. **This arm COULD have entrapped
  identically** (nothing in `arousal_window_coreg` or `snap_frustration`
  structurally prevents the victim from being pulled toward the abuser
  regardless of what else is attached) — it is measured, not asserted
  (Sec. 6).

### 2.3 The prior-tracking rules (`r3_prior_track_narrow` / `r3_prior_track_widen`)

Two new rules, both matching only `["victim","has_window","wot"]` (no
abuser/outside binding needed — they ride the counters, not the coupling
directly):

- **`r3_prior_track_narrow`** (order 10): fires when
  `wot.narrow_count > wot.pn_last_narrow` (a NEW bookkeeping attr this rule
  owns) — i.e., exactly once per genuine narrow-count increment, regardless
  of how many internal `run_rules()` passes it takes to observe it (a
  counter-DELTA observer, robust to the exact pass structure of the
  fixpoint — the SAME robustness principle R2's own epoch-guards use, just
  applied to a monotonic counter instead of a tick clock). Steps
  `others_trust`/`self_worth` DOWN by `0.03` each, clamped to `[0,1]`.
- **`r3_prior_track_widen`** (order 10): the mirror image, on
  `widen_count`, stepping UP.

### 2.4 The outside-regulator's got_coreg attribution (`r3_mark_coreg_support_outside`)

Because the outside regulator is connected via `also_attended_by` (Sec.
3.1), `arousal_window_coreg`'s own `mark_coreg_support` (which matches
specifically on the `attended_by` edge type) cannot see it. R3 adds ONE
more small rule, `r3_mark_coreg_support_outside` — a literal edge-type
substitution of `mark_coreg_support`'s own match/where/effect shape (same
"smallest possible reader" precedent as R1's OPEN QUESTION #2 resolution
and R2's Sec. 3.0 rule), never editing the original. It reads `regulated`
directly off the attended-to AGENT node (confirmed by reading the
unmodified `mark_coreg_support` rule, not assumed — `cg` binds straight
from the edge target, never hops through a `has_affective_state` edge to an
AffectiveState node), so the outside regulator's `regulated=1.0` is set on
its Agent node to match that convention.

## 3. Pilot (non-confirmatory, on off-block seed 90000+, informs the frozen constants and the composition fixes)

All of Sec. 3 was run directly against the REAL graph (R1's own Sec. 3.1
lesson — never a NumPy approximation) on off-block seeds (`90000+`), via
`scripts/abusive_r3_coercive_control_run.py`'s own functions and ad hoc
substrate scripts built the same way.

### 3.1 The significant finding: a second same-TYPE `attended_by` edge corrupts a downstream rule's cross-node reads, whenever `arousal_window_coreg`'s `selfreg_pull` is also loaded

The FIRST attempt at the outside-regulator arm connected the outside source
via a SECOND `attended_by` edge (`victim -attended_by-> abuser`,
`victim -attended_by-> outside`), with the DYAD entrainment rule's match
binding both targets in one instance (guarded by an `is_abuser` role
attribute so the two edges could not cross-bind — Sec. 2 of this section's
predecessor design). Piloted directly: the DYAD rule's own effect —
computed inside the SAME rule instance that had JUST correctly evaluated
its `where` clause (confirmed: the rule fires exactly once per tick,
verified via a debug counter attribute) — read `attr(aaff,"arousal")` (the
abuser's OWN, directly-queried arousal) as **`0.0`**, even when the raw
graph, queried directly, showed the abuser's arousal at `4.9` and climbing.
The victim's `frustration` consequently computed to `0.0` and stayed
`0.0` forever.

**Isolated by bisection** (loading `affective_state_core` + `snap_frustration`
+ a hand-filtered SUBSET of `arousal_window_coreg`'s nine rules, one rule at
a time): the corruption appears if and only if BOTH (a) the victim has TWO
`attended_by` edges of the same type, AND (b) `arousal_window_coreg`'s
`selfreg_pull` rule is loaded — `selfreg_pull`'s own match
(`has_affective_state` + `has_window`, no attended_by needed at all)
structurally matches the victim regardless of the outside regulator's
presence, for its OWN unrelated purpose (window self-regulation). Ruled
OUT, empirically, not by assumption:
- **Not about whether `selfreg_pull` actually fires.** Poisoning its own
  epoch guard (`sr_epoch`) to `1e15` — which should make its
  `Lt(sr_epoch, tick_epoch)` guard permanently false, i.e. permanently
  UNABLE to fire, for any realistic tick count — does **NOT** fix the
  corruption. Only physically EXCLUDING the rule from the loaded rule set
  fixes it.
- **Not a variable-name collision.** Renaming every variable in the dyad
  rule to be globally unique (no name shared with the SOLO rule or with
  `selfreg_pull`) does **NOT** fix it either.
- **Not about which victim-side attribute the rule reads as its "current
  arousal."** Substituting `Plus(setpoint,frustration)` (an attribute
  ONLY `snap_frustration`'s own rules and this rung's rules ever touch,
  never `coreg_pull`/`selfreg_pull`) for the direct `arousal` read does
  **NOT** fix it — the cross-node `aaff`/`oaff` reads still return `0.0`.
- **Fixed, cleanly and reproducibly, by giving the outside regulator a
  DIFFERENT edge type** (`also_attended_by` instead of a second
  `attended_by`) — no other change. With this fix, the SAME rule, same
  variable names, same formula, correctly reads the abuser's live arousal
  and computes the expected entrained value (piloted across 5 consecutive
  ticks: frustration tracked the hand-derived expected value at every
  tick, e.g. tick 1: `0.35*4.9 = 1.715` exactly, matching).

**This is disclosed at length, and reported straight, per the "shapes, not
numbers" / "report every engine finding" standing rule** (matching R2's own
Sec. 3.0 disclosure of the `snap_arousal_track` clobber): it is the SAME
hazard FAMILY the codebase's own prior engine-gotcha note names
elsewhere (the writer-dimensions residual in CLAUDE.md's history: *"two
same-type incoming edges on one node can break `run_rules` matching for
that edge type"*) — R3's variant is two same-type OUTGOING edges from one
node, and the corruption is not merely "the second edge doesn't match," it
actively corrupts a DIFFERENT rule's cross-node attribute reads. The
mechanism was **not identified at the Rust level** — this rung's
resolution is architectural (avoid the hazardous shape entirely) rather
than a Rust fix, consistent with the task brief's instruction to report
back rather than build a unilateral Rust change; **this rung did not need
one**, because the avoidance (a different edge type) is itself graph data
(a production declaration), not a Python decision or a new Term.

### 3.2 Sweep / sizing (T, WARMUP)

Using R2's own frozen abuser constants unchanged (`TRICKLE_MAG=5.0`,
`ABUSER_HALF_WIDTH=100.0`, `RECOVER_FLOOR=25.0`, inter-snap interval
`~24–25` ticks, confirmed identically reproducible here since the abuser
mechanism is byte-identical to R2's), a pilot sweep on seed `90000` at
`T=1000` showed: the single-anchor arm's window reaches its floor
(`half_width=5.0`, `min_half_width`) within the first ~15 incident cycles
and stays there (narrow_count climbing steadily, `others_trust`/
`self_worth` reaching `0.0` by roughly tick 500); the outside-regulator
arm's window never leaves its initial `half_width=10.0` at these
constants — the victim's entrained arousal, pulled by an EQUAL-gain
(`k_co=0.35`) contribution from both the abuser and the calm outside
source plus its own self-regulation pull toward setpoint, never crosses
the window's `hi=10.0` (peak observed ≈4.3–4.5 across pilot seeds), so
`WARMUP=100`/`T=1000` gives the single-anchor arm ~35 more cycles to
settle at its floor after the initial narrowing (comfortable margin) while
keeping runtime practical (~30s for the full N=200×2-arm confirmatory run,
measured).

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)
- `ABUSER_HALF_WIDTH = 100.0`, `LEAK = 0.02`, `K_ACC = 1.0`,
  `DISCHARGE = 0.90`, `RECOVER_FLOOR = 25.0`, `TRICKLE_MAG = 5.0`, jitter
  `±10%` — all IDENTICAL to R2's own frozen values (the abuser mechanism is
  byte-identical to R2's, so its own already-validated operating point is
  reused rather than re-swept).
- `VICTIM_HALF_WIDTH = 10.0` (initial), `min_half_width = 5.0`,
  `widen_delta = narrow_delta = 2.0` — `arousal_window_coreg`'s own
  convention, identical to R2's.
- `K_SELF = 0.15`, `K_CO = 0.35` — identical to R2's; used SYMMETRICALLY
  for both the abuser's and the outside regulator's pull in the dyad
  formula (a disclosed choice, Sec. 7: NOT split/diluted between the two
  sources, because "a second regulator being genuinely available" means
  more total support, not the same support divided).
- `CALM_AROUSAL = 0.0` (== the victim's own `setpoint`) — the outside
  regulator's fixed arousal; deliberately the victim's OWN resting point,
  not an artificially soothing extreme.
- `TRUST_STEP = WORTH_STEP = 0.03` — matches `arousal_window_coreg`'s own
  `safety_step` (0.03) and `bigville_life_rearing`'s own coming-of-age step
  magnitude (0.03); disclosed, not re-tuned. `PRIOR_INIT = 0.5` (neutral).
- `T = 1000` ticks/trajectory (~40 incident cycles); `WARMUP = 100` ticks
  excluded from the tracking-distance read-off.
- `N = 200` trajectories per arm (confirmatory); `N_GATE = 40` (pytest
  gate). `SEED_BASE = 289000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above the other's CI upper bound.

## 5. Metrics

**HEADLINE A — window-narrowing.** `final_half_width`: the victim's
`WindowOfTolerance.half_width` at the end of the `T`-tick trajectory — a
concrete, glass-box measure of whether the window has narrowed toward
(`5.0`) or held/widened away from (`10.0`+) its floor. A genuinely
collapsed frontier narrows monotonically to the floor and stays there
(R2's own disclosed residual); a genuinely open frontier holds or widens.

**HEADLINE B — safety-anchor inversion.** `abuser_proximity`: the mean
`|victim_arousal − abuser_arousal|` over ticks `WARMUP..T` within one
trajectory — a concrete, glass-box amplitude measure of how closely the
victim's entrained arousal tracks the abuser's specifically (not the
outside source, not its own setpoint). A LOW value means the anchor has
inverted onto the abuser (the victim's state is regulated BY and TOWARD
the dysregulation source); a CI-separated HIGHER value in the
outside-regulator arm means the anchor has NOT inverted — the victim's
state tracks the abuser LESS closely once an alternative regulator is
structurally available.

**SECONDARY, DESCRIPTIVE (not gated):** the abuser's final `snap_count`
(confirms the identical driver across arms); the victim's
`dysreg_frac` (fraction of ticks spent outside its own window); the
outside-regulator arm's `outside_proximity` (mean `|victim_arousal −
outside_arousal|`, corroborating); the final `others_trust`/`self_worth`
values (Sec. 1.1's progressive priors — mechanically coupled to the SAME
narrow/widen counters the headline window metric already reads, so
reported honestly as a corroborating readout of the SAME underlying
mechanism, not an independent confirmatory signal); `final_widen_count`/
`final_narrow_count` (the raw counters both the window and the priors
ride).

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, BOTH sub-gates must pass)

**A — window-narrowing:** `final_half_width(outside_regulator)` is
CI-separated ABOVE `final_half_width(single_anchor)`.
**B — anchor inversion:** `abuser_proximity(outside_regulator)` is
CI-separated ABOVE `abuser_proximity(single_anchor)`.

**Falsification bar, stated before measurement:** if the outside-regulator
arm's window narrows just as much as the single-anchor arm's, OR its
victim tracks the abuser just as closely, the coercive-control mechanism,
AS MODELLED, is wrong — reported straight, not rescued by re-tuning
(Sec. 3.1's own composition-hazard finding is recorded as exactly this
kind of straight report, at a DIFFERENT point in the design, not smoothed
over).

### G-glass-box
The `attended_by`/`also_attended_by` edges, the abuser's
`frustration`/`arousal`/`snap_count`, and the victim's
`arousal`/window `half_width`/`others_trust`/`self_worth` all reconstruct
from `graph_to_dict` alone; the window-narrowing and anchor-tracking
metrics are mechanical Python reductions (final-value / mean) over these
graph read-offs, never a Python-computed dynamic; the adapter's only
conditional is which arm's structural topology to build (world setup, not
an agent decision).

### G-ethics (BINDING, Part C)
- **C.1 restore:** induce (one minimal incident cycle, single-anchor arm)
  → measure → RESTORE, verified byte-identical (`ethics_restore_demo`),
  including the window `half_width` having actually narrowed and then
  been restored to its pre-induction value.
- **C.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **C.3 minimal induction, settled end:** stated explicitly in the
  preamble above (Sec. "How R3 satisfies each clause") — one incident
  cycle is the minimum that makes the ethics gate non-vacuous; the
  statistical run's greater length is the phenomenon under test
  (window-narrowing OVER episodes), not gratuitous elaboration; every
  trajectory is a fresh, ephemeral substrate discarded after read-off.
- **C.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  same leaky-integrate-fire + entrainment + window/prior-plasticity
  mechanism that would compound harm irreversibly over real episodes here
  accumulates a transient trajectory in a graph that is then
  byte-identically discarded, C.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (no other seed touched or modified,
including R1/R2's own seeds); exactly **FIVE** new rules
(`r3_victim_entrainment_solo`, `r3_victim_entrainment_dyad`,
`r3_mark_coreg_support_outside`, `r3_prior_track_narrow`,
`r3_prior_track_widen` — the smallest composition found, per Sec. 3.1's
engine finding: two entrainment rules gated by role/arm facts, one
edge-type-substituted reader, two counter-delta prior trackers);
`runners/dsl` SOURCE diff EMPTY (no Rust, no new Term — the compiled
`.so`/`_native.build.json` reflect a pre-existing staleness catch-up to
HEAD's own already-committed Rust source from before this rung began, not
any change made by this rung — verified via `git diff -- runners/dsl/src`,
empty); own-engine provenance (`source_match == own`).

## 7. Honest scope, stated before measurement
This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:
- `K_CO=0.35` applied SYMMETRICALLY (not split) between the abuser and the
  outside regulator (Sec. 4) is a disclosed design choice, not a swept
  parameter — no claim is made that this is the "correct" relative
  coupling strength for any clinical population.
- At the frozen constants, the outside-regulator arm's victim **never
  actually crosses into dysregulation** (pilot: `dysreg_frac=0.0`,
  `widen_count=narrow_count=0` throughout) — the window "holds" because
  the outside source's presence prevents the episode from ever opening,
  not because `r3_mark_coreg_support_outside`/`episode_resolve_widen` are
  repeatedly EXERCISED and repair an opened episode. This is reported
  honestly as a stronger-than-minimally-required protective result (full
  prevention, not active repair) and satisfies the task brief's own
  "holding/widening" wording, but the WIDENING half of the built machinery
  is not exercised at this specific operating point — a genuine, disclosed
  residual, not smoothed over.
- `T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale; no
  claim is made about real relationship episode counts or durations
  (which the clinical literature — Stark's coercive control, A5 — frames
  in months to years, not ticks).
- The progressive `others_trust`/`self_worth` priors (Sec. 1.1) are
  MECHANICALLY COUPLED, 1:1, to the SAME `narrow_count`/`widen_count`
  counters the window-narrowing headline already reads — they are reported
  as a corroborating readout of the SAME underlying mechanism (the
  frontier-collapse dynamic), not an independent confirmatory signal, and
  are not separately gated.
- The safety-anchor-inversion metric (`abuser_proximity`) measures TRACKING
  DISTANCE, not a first-class "attention weight" or edge-weight attribute
  — no such attribute was added (Sec. 2.4 explains why `regulated` lives on
  the Agent node, matching the existing unmodified rule's own convention,
  rather than inventing a new weighted-edge mechanism); this is a disclosed
  scope choice — the mechanism's STRUCTURE (which edge types exist) is the
  first-class graph fact; the tracking-distance number is a Python
  reduction that reveals what that structure produces, not a separate
  graph-resident belief about "who I trust more."
- A null (either sub-gate failing to separate) is a reportable, valuable
  result under the standing project rule and will be reported as such
  regardless of what the confirmatory run shows.
