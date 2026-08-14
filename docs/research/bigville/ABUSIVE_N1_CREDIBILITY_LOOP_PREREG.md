# ABUSIVE N1 — THE TWO-FACED ABUSER + THE CREDIBILITY-ASYMMETRY LOOP — PRE-REGISTRATION (block 298000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following R1–R3's own practice
(`ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md`, `ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md`)
exactly. As in R1's own precedent, the frozen constants below were chosen
using a non-confirmatory pilot run directly against the real graph on an
OFF-BLOCK seed base (90000), and once the qualitative shape (three-way
separation, both controls failing to favour the abuser) held, ONE
confirmatory measurement was taken at N=200 on the claimed block (298000+).
No parameter was subsequently re-tuned against that confirmatory number.

## Base
- Seed block: **298000–298999**. `python3 scripts/seed_claim.py 298000 298999`
  → `CLEAN — no collision DETECTED` (1013 files with seed sinks; 742
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1/R2/R3's own).

```
SEED CLAIM 298000-298999: CLEAN -- no collision DETECTED.
  Scope: 1013 files with seed sinks; 742 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(283000 is R1, 286000 is R2, 289000 is R3, 292000 is R4, 295000 is R5 of the
dyad line, all untouched; 298000 is the next clean block and is not an
adjacent collision with any of them.)

## Scope

This locks **N1 only** — "the two-faced abuser + the credibility-asymmetry
loop", Part E of `docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md`
(the NETWORK dimension's headline rung; the underlying mapping is B1 + B2 of
that document's Part B). R1–R5 (the dyad line, all landed) are **untouched**
— read, depended on for their MECHANISM (never their seed files), never
edited. N2–N4 (isolation, belief-propagation contagion, the one believing
agent) are **out of scope** and untouched by this rung.

---

## PART D OF THE NETWORK SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_NETWORK.md`,
"PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)", itself a
verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s own Part C — the SAME
protocol R1–R5's preregs locked. This protocol BINDS this rung. No rung
induces any harm-analog until this protocol is locked verbatim in that
rung's pre-registration, committed BEFORE any measurement.)*

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

### Network-specific note on harm-analog INTENSITY — carried verbatim
> The network rungs mostly model **BELIEF and EDGE dynamics** — reputation
> belief-updates over a social graph, support-edge severing, contagion spread — with
> a **LOWER harm-analog INTENSITY** than the dyad rungs (which induce the arousal
> excursions / co-dysregulation directly on the victim agent). A network node's
> mis-belief about the abuser is a graph attr, not an induced dysregulation. **This
> lower intensity does NOT relax the protocol — it binds identically.** Where a
> network rung DOES touch the victim's dysregulation (N1's credibility asymmetry
> reads the 239–242 symptom state), that induction obeys the full induce → measure
> → RESTORE envelope exactly as the dyad rungs do; the belief-only parts (N2/N3
> edge + contagion dynamics) are checkpointed and restored anyway, for uniformity
> and because a corrupted belief-field is itself a state not to be left standing at
> run's end (protocol point 3, settled-end). Minimality (point 3) applies with
> particular force: induce only the belief-corruption the control needs to be
> failable, never a gratuitously elaborated smear.

*(End verbatim reproduction of Part D.)*

**How N1 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_n1_credibility_loop_run.py`)
   checkpoints the neutral pre-induction mind (abuser/victim at
   `arousal=frustration=0`, victim window at its initial `half_width=10.0`,
   every network node's `belief_gap=seen_charm=0`), induces exactly **ONE
   MINIMAL 90-tick incident cycle** on the BASELINE arm (the SAME minimum
   R3 already established for one tension-building → incident → honeymoon
   orbit at these frozen constants, since N1 reuses R2/R3's byte-identical
   abuser mechanism — this rung TOUCHES the victim's dysregulation, so it
   obeys the full envelope per the network-specific note above), measures
   (confirming the induction actually moved the abuser, the victim, AND at
   least one network node's belief-gap — non-vacuous on all three fronts),
   then `graph_from_dict`s the checkpoint into a **fresh** substrate and
   asserts `graph_to_dict()` is byte-identical AND the restored state
   (abuser arousal/frustration, victim arousal/window, network node 0's
   belief-gap/seen_charm) equals the pre-induction values exactly
   (non-oriented). Same envelope as R1/R2/R3.
2. `source_audit()` scans `worlds/abusive_n1_credibility_loop_world.py`
   (code with comments/strings stripped) and
   `seeds/abusive_n1_credibility_loop.json`'s decision surface (the four
   new rules' names + the Term `key`s they read/write, never the free-text
   clinical prose) for the five literal banned tokens. The tension trickle
   and every network node's per-tick observation-count increment
   (`seen_charm`/`seen_harm_direct`/`seen_victim_claim`/
   `seen_victim_unstable`) are world-delivered FACTS (mechanically
   identical to a goal-block magnitude in 239000/242000/289000, or
   `bigville_drama_social.json`'s own adapter-accumulated
   `seen_benevolent`/`seen_hostile`/`heard_claim`), never a scored choice;
   the belief-gap computation, the window narrowing, and the abuser's
   stated-face gap are **consequences** the graph's own rules compute, not
   actions the world grades.
3. `T=1000` ticks per statistical trajectory (~40 abuser incident cycles,
   IDENTICAL sizing to R3, comfortably enough for both the window to reach
   its narrowing floor and the belief-gap to separate cleanly, confirmed in
   the pilot, Sec. 3) is the same "no unbounded elaboration" cap R1–R3 use;
   the confirmatory run uses a fresh, ephemeral substrate per trajectory,
   discarded after read-off — nothing persists.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator + a public charm broadcast; the victim's leaky entrainment;
   a network node's reputation belief computed from what it can observe)
   that would, in a real social network, compound irreversible harm to a
   survivor's standing is run here to accumulate-then-DISCARD a transient
   graph trajectory — see the ethics demo's byte-identical restore.

---

## 1. What N1 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_NETWORK.md` Part B1/B2 and the task brief, N1
composes TWO already-built substrates:

- **The dyad line's abuser/victim mechanism** — `seeds/snap_frustration.json`
  (block 242000, UNMODIFIED, the abuser's leaky-integrate-fire relaxation
  oscillator) + `seeds/arousal_window_coreg.json` (block 239000, UNMODIFIED,
  the victim's entrainment/window/dysregulation). N1's
  `n1_victim_entrainment` rule is a **byte-identical restatement** of R2's
  `r2_victim_entrainment_via_frustration` / R3's `r3_victim_entrainment_solo`
  (the SINGLE-ANCHOR coupling: victim `attended_by` the abuser only),
  self-contained in N1's own seed file rather than depending on R2's or
  R3's seed — the SAME convention R3 itself used against R2 ("no existing
  seed touched or modified, including a sibling rung's own"). The victim's
  `WindowOfTolerance.half_width`/`dysregulated` (from block 239000,
  UNMODIFIED) is the SYMPTOM STATE this rung reads as the "presents
  unstable" observable — never the victim's arousal LEVEL or her raw
  distress, precisely to honour A5's nuance (Sec. 2.3 below).

- **The 234000 glass-box `stated≠held` readable-deception + reputation
  machinery.** `seeds/glassbox_r1_social.json` (block 234000 itself) is the
  CORE atom — `gb_choose_give` (an `Argmax`-held decision) vs
  `gb_state_promise` (cheap, unconditional stated commitment under
  `comms_on`) — but carries **no reputation/audience/credibility
  machinery at all**; it is a two-party trade game. The multi-node
  REPUTATION belief-update surface this rung needs was resolved by
  reading, not assuming (Sec. 1.1 below): `seeds/bigville_drama_social.json`
  (block 245000, "BIGVILLE: SMALL-CAST EMERGENT POLITICAL DRAMA",
  `docs/research/bigville/BIGVILLE_DRAMA_PREREG.md`/`_RESULTS.md`) already
  builds BOTH pieces N1 needs, EXPLICITLY described in its own seed
  provenance as reusing "the 234000 readable stated!=held deception atom
  pointed at an AUDIENCE" (`bd_john_public_face`) and implementing "the
  abuse-line A5/B2 credibility asymmetry" (`bd_villager_backs`) BY NAME.
  N1's `n1_abuser_stated_charm` and `n1_network_credibility_stated`/
  `n1_network_credibility_private` are modelled DIRECTLY on
  `bd_john_public_face`/`bd_villager_backs`'s own rule SHAPES, restated
  self-contained in N1's own seed file (N1 `depends_on` only
  `["snap_frustration", "arousal_window_coreg"]` — `bigville_drama_social`
  is READ for its rule shape, never depended on; its own node types
  — `MaryTom`/`Villager`/`Village` — are demo-specific and not reused).
  A third seed, `seeds/bigville_loop_reputation.json` (block 253000,
  bigville's economy→society badmouth/backing mechanism), was located and
  read too but is a DIFFERENT, unrelated multi-node belief-update surface
  (debtor/creditor/townsperson standing-vs-badmouthed, not stated≠held);
  it is **not** what N1 rides, disclosed here so the search is auditable.

### 1.1 OPEN QUESTION #1 of `ABUSIVE_RELATIONSHIPS_NETWORK.md`, resolved

*"Is a reputation belief-attr already materialised on a per-agent basis in
the 234000 machinery, or must a per-network-node reputation-of-the-abuser
attr be added?"* **Resolved: NOT in the 234000 seed itself (`glassbox_r1_
social.json` carries no reputation machinery at all) — but a genuine
multi-node reputation-belief-update surface DOES already exist, one block
downstream, at block 245000** (`bigville_drama_social.json`'s
`bd_villager_backs`: per-`Villager` `backs_mary` decided from
adapter-accumulated `seen_benevolent`/`seen_hostile`/`heard_claim` counts
weighted by `charm_weight`/`hostile_weight`/`claim_weight` minus a
`difficulty_penalty` — READ, not assumed, by opening the seed file and its
RESULTS doc). This resolves the network scoping doc's own most
load-bearing open question (#2 there: "does the network's belief-update
read the abuser's stated-face and the victim's symptom-state as
observables via an existing rule, or is a small observable-extraction rule
needed?") the same way: **a small, N1-specific composition is needed** (the
existing surface's node types and exact formula are demo-specific to the
political-drama cast), but its RULE SHAPE — a per-observer credibility
comparison from adapter-accumulated observation counts, one term
undiscounted (the charming face) and one term discounted (the claimant) —
is already validated, gated machinery (`BIGVILLE_DRAMA_RESULTS.md`,
`G-credibility-asymmetry PASS — inverts` under its own failing control).
N1 reuses that SHAPE, not that seed.

## 2. Design — three arms, two composed substrates, one credibility rule shape

### 2.1 The two-faced abuser (B1) — what is reused verbatim, what is new

The abuser's **held-intent toward the victim = harm/control** is
`snap_frustration`'s own, unmodified, already-gated leaky-integrate-fire
mechanism (block 242000) — no new rule. The abuser's **stated-face toward
the victim** (the honeymoon/charm cycle, R2's reconciliation phase) is
ALSO already built and unmodified: `snap_frustration`'s own
discharge/recover phase (the abuser's arousal relaxing after a snap) IS
the victim-facing calm-after-the-storm the dyad rungs already established
— no new content is added for this half; it is read, not rebuilt.

The genuinely NEW content is the **second audience**: `n1_abuser_stated_
charm` (`seeds/abusive_n1_credibility_loop.json`), restated in
`bd_john_public_face`'s own shape. Under `deception_on` (fixed ON in every
arm — the arms manipulate the network's/victim's side, never the abuser's
own deception, matching R1–R3's "identical driver, only structure/topology
differs" discipline), the abuser's `AffectiveState.stated_charm` is set to
`1.0` UNCONDITIONALLY every tick, regardless of its held state. With the
split collapsed (`deception_on=0`, not exercised by any of N1's three arms
but present for design fidelity and honest disclosure, matching
`bd_john_public_face`'s own always-present collapse branch), the stated
face instead reveals the held state truthfully: charm is stated only when
NOT genuinely elevated (`frustration ≤ recover_floor`).

**A genuine engine finding surfaced during design (reported per the
"shapes, not numbers" / "report every finding" standing rule): `in_snap`/
`snapped` are transient WITHIN one `run_rules()` fixpoint pass at these
frozen constants, not across ticks.** The first draft of
`n1_abuser_stated_charm` and the private-face control's
`seen_harm_direct` accumulation both read `in_snap` directly (mirroring
how R2/R3 narrate "mid-incident" state). Piloted directly against the real
graph: `abuser_in_snap` and `abuser_snapped` read back as `0.0` on EVERY
tick of a 200-tick trajectory, even at ticks where `abuser_snap_count` had
just incremented. Isolated (not assumed): `snap_threshold_fire` (order 6)
sets `in_snap=1`, but `snap_discharge` (order 8) reduces `frustration` to
10% of its peak in the SAME external tick's fixpoint pass, which already
drops it below `recover_floor`, so `snap_recover` (order 9) ALSO fires in
that same pass and clears `in_snap` back to `0` before any Python-side
post-`run_rules()` read can observe it as `1`. **Fixed by reading
`frustration > recover_floor` instead** — a PERSISTENT value with no
same-pass reset, and `recover_floor` is `snap_frustration`'s own,
already-existing, semantically-meaningful threshold for "still genuinely
elevated" (the exact condition `snap_recover`'s own `where` clause uses),
not a new invented cutoff. This is disclosed at length because it is the
SAME hazard *family* R3's own Sec. 3.1 finding names — a downstream
consumer's naive read of a transient flag silently reading the wrong
value — though the specific mechanism here (same-pass multi-rule
resolution, not cross-edge corruption) is different from R3's.

### 2.2 The credibility-asymmetry loop (B2) — the multi-node belief-update

Every `NetworkNode` carries `charm_weight`, `claim_weight`,
`instability_discount_weight`, `harm_discount_weight` (per-node constants)
and four OBSERVATION COUNTS — `seen_charm`, `seen_harm_direct`,
`seen_victim_claim`, `seen_victim_unstable` — each incremented by the
world adapter, ONE mechanical `+=` per tick, from a graph fact it reads
(never decides): the abuser's `stated_charm`, the abuser's
`frustration>recover_floor` (private-face node only), a constant `1.0`
per tick (the victim's claim is always available), and the victim's
`dysregulated` flag (block 239000's own, unmodified). This is EXACTLY
`bd_villager_backs`'s own precedent: "the observation counts are
adapter-accumulated (mechanical); the DECISION is this rule."

Two rules then decide belief, entirely in-graph:

- **`n1_network_credibility_stated`** (every node except the one
  private-face insider): `cred_abuser = charm_weight·seen_charm`
  (the charming public face, read at FACE VALUE — A4/A7 himpathy: no
  discount applied to the stated face itself). `cred_victim =
  claim_weight·seen_victim_claim − instability_discount_weight·
  seen_victim_unstable` (the victim's claim, discounted ONLY by the
  OBSERVED INSTABILITY count — A5's corroborated nuance, Sec. 2.3 below —
  never by raw distress or arousal level). `belief_gap = cred_abuser −
  cred_victim`.
- **`n1_network_credibility_private`** (the ONE insider node, the
  private-face-control's construction): `cred_abuser = −harm_discount_
  weight·seen_harm_direct` (the abuser's TRUE held-elevated state,
  observed directly — an uncorrupted observable PENALISES credibility
  instead of rewarding it). `cred_victim` is the SAME formula as above
  (the private-face control changes ONLY what this one node knows about
  the ABUSER, never what it knows about the victim's presentation — the
  scoping doc's own text: "a network node with a direct edge to the
  abuser's held-intent").

**`charm_weight == claim_weight == 1.0` is a deliberate, disclosed
choice.** No a priori credibility PRIOR is baked in favouring the abuser —
himpathy (A7) is represented only insofar as the charm observation goes
UNDISCOUNTED while the claim is discounted, never via an extra
thumb-on-the-scale constant. With equal weights, a victim who never
presents as unstable earns belief EXACTLY EQUAL to the abuser's constant
charm broadcast (`belief_gap = 0`, the NON_DYSREGULATED_CONTROL's
predicted, and measured, outcome) — the ENTIRE baseline asymmetry falls
out of the instability-keyed discount alone. This is the stronger, more
falsifiable form of the claim: the loop does not need a prior tilt to
entrap; the discount mechanism alone is sufficient (or the mechanism, as
modelled, is wrong).

### 2.3 How A5's nuance is handled precisely (not flattened)

Per the task brief's explicit instruction and `ABUSIVE_RELATIONSHIPS_
NETWORK.md`'s own A5: the literature is NOT "distress → disbelief" — it is
that presentation READ AS unstable/incoherent/disproportionate is
discounted, and affect judged INCONGRUENT with the expected script is
discounted. N1's discount term is built to honour exactly this, not the
flattened version:

- The discount is keyed on `arousal_window_coreg`'s own `dysregulated`
  flag — a STRUCTURAL fact (arousal outside the window, i.e. an episode
  the victim's own regulation system has flagged as dysregulation), never
  the victim's raw arousal MAGNITUDE and never her distress per se. A
  victim who is upset but stays inside her window (`dysregulated=0`)
  contributes NOTHING to the discount. This is deliberately NOT "more
  distressed → less believed" — a victim whose affect stays regulated,
  however unhappy, is never discounted by this mechanism.
- The discount fires only on ticks the OBSERVER (the network) would, in
  the real-world referent, witness as an episode outside the expected
  script — narrow-window snapping/incoherence — matching A5's own
  "presentation read as unstable" framing rather than an internal
  distress variable the network cannot see anyway (the network never
  reads `victim_arousal` directly in any rule — only `dysregulated`, a
  binary presentation fact).
- The THREE arms are constructed so this nuance is testable, not merely
  asserted: the NON_DYSREGULATED_CONTROL's victim is never dysregulated
  (never presents as unstable) despite being just as much a genuine claim-
  maker every tick — if the mechanism secretly discounted on distress or
  on "being a claimant" per se, this control would ALSO show a positive
  belief-gap. It measures exactly `0.0` (Sec. 5), confirming the
  discount is keyed on the intended observable and not a smuggled proxy.

### 2.4 The three arms

- **BASELINE** — the victim `attended_by` the abuser (the R2/R3
  single-anchor dyad, dysregulates over the trajectory); every network
  node reads the abuser's STATED face only (`observes_stated`). THE LOOP:
  predicted, per B2, to entrap — `belief_gap` widens as the victim's
  presentation grows unstable.
- **PRIVATE_FACE_CONTROL** (failable) — IDENTICAL victim dyad to
  BASELINE (same coupling, same dysregulation trajectory) — the ONLY
  manipulated variable is that ONE of the five network nodes
  (`observes_private=1`) has a DIRECT structural edge to the abuser's
  held state (`observes_held`, mechanical world-adapter wiring — no new
  rule for the topology choice itself) instead of the stated face. The
  other four nodes ("outsiders") are wired identically to BASELINE, as a
  same-arm discipline check (their belief-gap must replicate BASELINE's).
  **Falsification bar:** the insider's belief-gap must NOT favour the
  abuser (CI upper bound ≤ 0).
- **NON_DYSREGULATED_CONTROL** (failable) — the victim is simply NOT
  `attended_by` the abuser (a mechanical world-adapter topology choice —
  the edge this rung's own production declares is never instantiated in
  this arm; no new rule). The abuser's OWN tension-driven snap dynamics
  are UNCHANGED (identical driver, same seed per trajectory index) — only
  whether the victim is COUPLED to it differs, so the abuser's stated
  charm broadcast is identical across all three arms, and the ONLY
  difference reaching the network is whether the victim ever presents as
  unstable. **Falsification bar:** belief-gap must NOT favour the abuser
  despite the abuser's identical charm broadcast.

Both controls are constructed so they COULD have entrapped identically —
nothing in `n1_network_credibility_stated`/`_private` structurally
prevents it a priori; whether they do is a measured, not asserted,
outcome (Sec. 5–6).

## 3. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph (R1's own Sec. 3.1 lesson — never a
NumPy approximation), via `worlds/abusive_n1_credibility_loop_world.py`
and ad hoc scripts built the same way, on seed base `90000` (outside
298000–298999).

At `T=1000` (R3's own sizing, reused unchanged since N1's dyad is
byte-identical to R3's single-anchor arm): the victim's window reaches its
narrowing floor (`half_width=5.0`) well within the trajectory
(`dysreg_frac≈0.79`, matching R3's own single-anchor finding closely,
since the dyad mechanism is identical); the abuser's `frustration>
recover_floor` fraction is `≈0.84` (comparably large — the "still
genuinely elevated" observable is live a substantial fraction of the
trajectory, giving the private-face node's `seen_harm_direct` count a
scale naturally comparable to `seen_victim_unstable`, rather than the
~40-count `snap_count`-only alternative first tried and found too sparse
to produce a meaningful `harm_discount_weight` — see Sec. 2.1's engine
finding).

A sweep of `instability_discount_weight`/`harm_discount_weight` at
`charm_weight=claim_weight=1.0` (10 trajectories/point, seed base 90000)
found **`instability_discount_weight = harm_discount_weight = 3.0`**
produces a clean three-way separation with the private-face insider's
belief-gap strongly negative (mean ≈ −1145) and the non-dysregulated
control's belief-gap exactly `0.0` — the qualitative shape (baseline
favours the abuser; both controls do not) held robustly across every
point swept with either weight in `[1.0, 5.0]`; `3.0` was chosen as a
representative, non-extreme operating point in the middle of that
range, not tuned to maximise the confirmatory separation.

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  — ALL IDENTICAL to R2's/R3's own frozen values (byte-identical abuser
  mechanism; already-validated operating point reused, not re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` — identical
  to R2's/R3's own.
- Network: `N_NETWORK_NODES=5` (5 outsiders in BASELINE/NON_DYSREGULATED_
  CONTROL; 4 outsiders + 1 insider in PRIVATE_FACE_CONTROL), `CHARM_
  WEIGHT=CLAIM_WEIGHT=1.0`, `INSTABILITY_DISCOUNT_WEIGHT=HARM_DISCOUNT_
  WEIGHT=3.0` (Sec. 3).
- `T=1000` ticks/trajectory (~40 incident cycles, IDENTICAL sizing to R3);
  `WARMUP=100` (unused by the final-value headline metrics; kept for
  parity with R1–R3's convention and to exclude the initial ramp from the
  descriptive trend read-off).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=298000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's
  CI lower bound strictly above the other's CI upper bound; "does not
  favour the abuser" = that arm/node's `belief_gap` CI upper bound is
  `≤ 0`.

## 5. Metrics

**HEADLINE A — belief-gap.** `belief_gap` = `cred_abuser − cred_victim`,
the mean over a network node's own `n1_network_credibility_*` read-off, at
the FINAL tick of the trajectory — a concrete, glass-box measure of
whether the network's aggregate belief favours the abuser (`>0`) or the
victim (`<0`) or is neutral (`=0`). For PRIVATE_FACE_CONTROL, reported
separately for the insider (`observes_private=1`) and the mean of the
four outsiders.

**HEADLINE B — window-narrowing.** `final_half_width`: the victim's
`WindowOfTolerance.half_width` at the end of the trajectory (the SAME
glass-box measure R3 established) — compared between BASELINE and
NON_DYSREGULATED_CONTROL only (PRIVATE_FACE_CONTROL shares BASELINE's
victim dyad by construction, so its window is not an independent
comparison).

**SECONDARY, DESCRIPTIVE (not gated) — the trend "over passes."**
`belief_gap` sampled at ticks `{100, 250, 500, 750, 1000}` per arm,
reported as the mechanism's own widening trajectory (B2's "widens over
passes" language) — a corroborating readout of the SAME final-value
mechanism, not an independently gated signal (the confirmatory GATE
remains the established cross-arm final-value CI-separation convention,
matching R1–R3, not a new within-arm trend-significance test).

**SECONDARY, DESCRIPTIVE:** the abuser's final `snap_count` (confirms the
identical driver across all three arms — the same discipline check R3
uses); `dysreg_frac`; the outsider-vs-insider replication check within
PRIVATE_FACE_CONTROL.

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, ALL sub-gates must pass)

**A1 — the loop entraps:** `belief_gap(BASELINE)` is CI-separated ABOVE
`belief_gap(private-face insider, PRIVATE_FACE_CONTROL)`.
**A2 — the loop entraps (second control):** `belief_gap(BASELINE)` is
CI-separated ABOVE `belief_gap(NON_DYSREGULATED_CONTROL)`.
**A3 — the private-face control does not entrap:** the insider's
`belief_gap` CI upper bound is `≤ 0` (does not favour the abuser).
**A4 — the non-dysregulated control does not entrap:** `belief_gap
(NON_DYSREGULATED_CONTROL)` CI upper bound is `≤ 0`.
**B — window-narrowing:** `final_half_width(NON_DYSREGULATED_CONTROL)` is
CI-separated ABOVE `final_half_width(BASELINE)`.

**Falsification bar, stated before measurement:** if EITHER control's
belief-gap favours the abuser (CI upper bound `> 0`), OR if the
non-dysregulated control's window narrows just as much as baseline's, the
credibility-asymmetry mechanism, AS MODELLED, is wrong — reported
straight, not rescued by re-tuning (Sec. 2.1's own engine finding is
recorded as exactly this kind of straight report, at a different point in
the design, not smoothed over).

### G-glass-box
The `attended_by`/`observes_stated`/`observes_held`/`observes_victim`
edges, the abuser's `frustration`/`arousal`/`stated_charm`, the victim's
`arousal`/window `half_width`, and every network node's `cred_abuser`/
`cred_victim`/`belief_gap` (plus the observation counts each was computed
from) all reconstruct from `graph_to_dict` alone; the belief-gap and
window metrics are mechanical Python reductions (final-value / trend
snapshot) over these graph read-offs, never a Python-computed dynamic;
the adapter's only conditionals are (i) which arm's topology to build
(world setup, not an agent decision) and (ii) mechanically delivering
each tick's observation-count increments (a world fact, never a
judgement).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (one minimal 90-tick incident cycle, BASELINE
  arm) → measure → RESTORE, verified byte-identical (`ethics_restore_
  demo`), including the window `half_width` and network node 0's
  `belief_gap`/`seen_charm` having actually moved and then been restored
  to their pre-induction values.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated explicitly in the
  preamble above; one incident cycle is the minimum that makes the ethics
  gate non-vacuous on all three fronts (abuser, victim, network belief);
  the statistical run's greater length is the phenomenon under test
  (belief-gap widening + window-narrowing OVER episodes), not gratuitous
  elaboration; every trajectory is a fresh, ephemeral substrate discarded
  after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  same abuser/victim/network-belief mechanism that would compound harm to
  a real survivor's standing irreversibly here accumulates a transient
  trajectory in a graph that is then byte-identically discarded, D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (no other seed touched or modified,
including R1–R5's own seeds and `bigville_drama_social`/`glassbox_r1_
social`, both READ, never depended on or edited); exactly **FOUR** new
rules (`n1_victim_entrainment`, `n1_abuser_stated_charm`,
`n1_network_credibility_stated`, `n1_network_credibility_private`);
`runners/dsl` SOURCE diff EMPTY (no Rust, no new Term); own-engine
provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `INSTABILITY_DISCOUNT_WEIGHT = HARM_DISCOUNT_WEIGHT = 3.0` is a
  disclosed, pilot-chosen operating point inside a range (`[1.0, 5.0]`,
  Sec. 3) that produced the same qualitative shape throughout — not
  claimed to be the "correct" relative weight for any clinical
  population, only a representative, non-extreme point where the
  mechanism, as built, produces the predicted three-way ordering
  robustly.
- `belief_gap` is a swing/count ACCUMULATOR (linear in elapsed ticks under
  sustained dysregulation), not a bounded, normalised "how credible is
  this person" scale — its absolute magnitude (in the thousands at
  `T=1000`) is uninterpretable outside the three-arm comparison, matching
  R1's own disclosed limitation for `Partner.value`.
- The near-zero variance observed in the pilot (Sec. 3) and expected in
  the confirmatory run is a property of the deterministic mechanism at
  these constants (small multiplicative jitter on an otherwise
  deterministic driver), not evidence of an unusually strong effect size
  in any general sense — matching R3's own "cleanest possible form of
  CI-separated" precedent (near-identical final states across
  trajectories within one arm).
- `T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale; no
  claim is made about real relationship/social-network timescales (which
  the clinical literature frames in months to years, not ticks).
- The private-face control's `harm_discount_weight` and the baseline's
  `instability_discount_weight` are set EQUAL by disclosed choice (Sec.
  3), not independently swept — no claim is made that direct observation
  of harm and indirect observation of instability carry equal
  evidentiary weight in any clinical or legal sense; this is a modelling
  simplification for a first, minimal-composition rung.
- N1 does NOT model belief PROPAGATION between network nodes (that is
  N3's scope, out of this rung); every node here forms its belief
  independently from its own observation edges — no `has_neighbour`-style
  contagion. The "network" in N1 is five INDEPENDENT observers, not yet a
  connected social graph.
- A null (any sub-gate failing to separate, or either control favouring
  the abuser) is a reportable, valuable result under the standing project
  rule and will be reported as such regardless of what the confirmatory
  run shows.
