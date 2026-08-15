# ABUSIVE N4 — ONE NON-DOUBTING AGENT RESTORES A SUPPORT EDGE — PRE-REGISTRATION (block 307000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1/N2/N3's own practice exactly. As in
N1–N3's own precedent, the constants below were chosen using a
non-confirmatory pilot run directly against the real graph on an OFF-BLOCK
seed base (90000), and once the qualitative shape (four-metric separation,
the control persisting, zero re-severing hazard) held across a 10-seed
sweep, ONE confirmatory measurement is taken at N=200 on the claimed block
(307000+). No parameter is subsequently re-tuned against that confirmatory
number.

## Base
- Seed block: **307000–307999**. `python3 scripts/seed_claim.py 307000 307999`
  → `CLEAN — no collision DETECTED` (1019 files with seed sinks; 760
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1–R5/N1–N3's own).

```
SEED CLAIM 307000-307999: CLEAN -- no collision DETECTED.
  Scope: 1019 files with seed sinks; 760 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(283000 R1, 286000 R2, 289000 R3, 292000 R4, 295000 R5, 298000 N1, 301000 N2,
304000 N3, all untouched; 307000 is the next clean block on the established
+3000 spacing and is not an adjacent collision with any of them.)

## Scope

This locks **N4 only** — "one non-doubting agent restores a support edge (the
hopeful half of the network line)", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md` (the underlying
mapping is A2 reversed + the reverse of B1–B4, tying directly to the dyad
line's own R5). This is the LAST rung of the whole abusive-relationships
line (`docs/research/bigville/ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md`, "What
is not built"). R1–R5 (the dyad line) and N1–N3 (the network line) are
**untouched** — read, depended on for their MECHANISM, never edited. U0–U2
(the intent line) are unrelated and untouched.

---

## PART D OF THE NETWORK SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_NETWORK.md`,
"PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)", itself a
verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s own Part C — the SAME
protocol R1–R5's and N1–N3's preregs locked. This protocol BINDS this rung.
No rung induces any harm-analog until this protocol is locked verbatim in
that rung's pre-registration, committed BEFORE any measurement.)*

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

### What N4 changes about what "induction" even means (carried from R5, restated for the network composition)

Per the scoping doc's own framing of this rung — *"this is the rung to build
FIRST in spirit... it induces the least and ends most settled, and makes the
whole line's purpose (helping survivors) the literal object of measurement"*
— N4, like R5, inverts the relationship between induction and the phenomenon
under study. N4 still induces a harm-analog first (there is no "restoring a
severed support edge" to measure without a severed edge to restore, and
reusing R1–R5/N1–N3's own machinery to build that trap is the whole point of
composing this line rather than re-deriving it), but the **object of
measurement is not the trap** — it is what happens after ONE mechanical
world event (`introduce_believing_agent()`) fires. The induction here is the
LEAST of any rung in the line: it is exactly N2's own already-validated
`both_drivers` isolation trap (itself riding N1's already-validated
credibility loop, itself riding R2/R3's already-validated dyad
entrainment) — no new harm-analog content is added on the induction side at
all. **Everything genuinely new in N4 is on the recovery/restoration side**,
honouring the task's own framing exactly.

---

## 1. What N4 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_NETWORK.md` Part E's N4 entry and the task brief,
N4 composes:

- **R5's ENTIRE recovery composition**
  (`seeds/abusive_r5_recovery.json`, block 295000, UNMODIFIED) — which itself
  composes R1–R4 (`traumatic_bond_r1`, `abusive_r2_cycle_limit`,
  `abusive_r3_coercive_control`, `abusive_r4_learned_helplessness`, all
  UNMODIFIED). N4 reuses R5's two own rules verbatim:
  `r5_bond_extinguish` (the bond's extinction leak, active in every arm/phase)
  and `r5_contingency_restore` (the second, independent evidence channel on
  `EscapeDecision.contingency_prior` that lets a frozen belief be revised
  without requiring the victim to attempt first).
- **N2's ENTIRE isolation composition**
  (`seeds/abusive_n2_isolation.json`, block 301000, UNMODIFIED) — which
  itself depends on N1's credibility-asymmetry loop
  (`seeds/abusive_n1_credibility_loop.json`, block 298000, UNMODIFIED).
  N4 reuses N2's two own rules verbatim: `n2_abuser_active_sever` (the
  abuser's scheduled active severing) and `n2_network_drift_sever` (the
  network's own belief-gap-driven withdrawal), and N1's four rules verbatim,
  most importantly `n1_network_credibility_private` — the "insider" formula
  that computes a network node's credibility belief from the abuser's TRUE
  held state (`observes_held`) rather than the corrupted stated face,
  already validated by N1's own PRIVATE_FACE_CONTROL arm and reused a
  second time, unmodified, as N3's own truth-anchor mechanism.
- **N1's own disclosed limitation, N3's own resolution of it, and why N4
  does NOT also need N3's seed.** N1's belief-gap formula
  (`n1_network_credibility_private`) is what lets ONE node's belief reverse
  when it observes the abuser's held state directly — this is the atom N3
  reused, unmodified, for its own "truth-anchor" arm, and it is the SAME
  atom N4 needs for its own believing agent. **N4 depends on N1's atom, but
  NOT on N3's seed** — a disclosed scoping decision, justified in Sec. 2.5
  below: N4's claim is that ONE node's OWN belief arrests/reverses once it
  is wired as an insider, not that the reversal PROPAGATES to other nodes
  via `peer_of` edges (that would be a stronger, different claim — call it
  a hypothetical N5 — outside this rung's scope, and outside what the
  network scoping doc's own N4 entry asks for).

## 2. Design — the composition, and why this is the hardest call in the whole line

### 2.1 The task brief's own framing, resolved: N4 needs BOTH atoms, on ONE node

The task brief names the central design question directly: does "believes
the victim" map to N1's `observes_held`/private-face-insider mechanism, or
does "restores a support edge" map to N2's support-edge machinery, reversed
— and predicts the answer is likely BOTH. Confirmed, not merely assumed
(Sec. 3 below): **the believing agent is ONE `NetworkNode` that, from the
moment it is introduced, simultaneously plays FOUR roles on a single node
ID** — extending R5's own "one victim node plays three roles" precedent
(Sec. 2.1 of `ABUSIVE_R5_RECOVERY_PREREG.md`) to the NETWORK side of the
composition, which is the genuinely new structural move this rung makes:

1. **N1/N2's `NetworkNode`** — it already carries `belief_gap`,
   `charm_weight`/`claim_weight`/`instability_discount_weight`/
   `harm_discount_weight`, the observation counts, and a `support_edge` to
   the victim (severed by N2's own drift mechanism during induction, Sec.
   3).
2. **N1's private-face insider** — at the moment of introduction, it gains
   an `observes_held` edge to the abuser and `observes_private=1.0`, so
   `n1_network_credibility_private` (unmodified) — not
   `n1_network_credibility_stated` — computes its `belief_gap` from that
   tick forward, from the abuser's TRUE state.
3. **N2's restored support-edge holder** — its (previously severed)
   `support_edge` to the victim is mechanically re-added.
4. **R3/R5's outside regulator** — it gains a fresh `AffectiveState` node
   pinned at `CALM_AROUSAL` (`is_abuser=0.0`, `regulated=1.0`), and the
   victim gains an `also_attended_by` edge to it plus
   `has_outside_regulator=1.0` — **R3's own outside-regulator mechanism,
   already twice-validated (R3's own arm; R5's own recovery arm), exercised
   a THIRD time, now from a node that is simultaneously a network belief-
   holder.** This is the wire that lets R5's atoms (bond extinction,
   window widening, contingency restoration) actually fire in response to
   the believing agent's arrival — without it, N4 would only be a network-
   belief demonstration, not a recovery demonstration.

No new node type, no new Rust, and (Sec. 2.6) **zero new rules** — every
one of the four roles above is matched, structurally, by an EXISTING rule
from R1–R5/N1/N2, exactly the same "rule `match` arrays are structural, not
type-string-filtered" fact R5's own Sec. 2.1 already established and
verified by reading the engine, not assumed.

### 2.2 One victim, one abuser, eight support/network nodes — reusing N2's population directly

The dyad (abuser + victim) is R5's own construction, byte-identical:
the abuser carries `snap_frustration`'s contract plus R1's `Partner`-role
attrs (`value`/`e_bond`/`e_extinct`/`decay_rate`); the victim carries
`arousal_window_coreg`'s contract, R1's `MoodTask`/`Mood`, and R4's
`EscapeDecision`/`HeldEmotionParams`/two `Appraisal`s — all on the SAME two
node IDs, exactly as R5 built them. The support/network population is N2's
own construction, byte-identical: **8 `NetworkNode` agents**
(`N_SUPPORT_NODES=8`, N2's own sizing decision, reused unchanged), each an
N1-shape credibility observer (`observes_stated → abuser`,
`observes_victim → victim`) AND an N2-shape support-edge holder
(`support_edge → victim`), with N2's own per-node `sever_at_tick`
(abuser-driven schedule) and `drift_threshold` (network-drift, REVERSED
index order) — N2's own `EPISODE_TICKS=210.0`/`DRIFT_STEP=340.0`, reused
unchanged (Sec. 4). `isolation_tactic_on=1` for the WHOLE trajectory in
BOTH arms — matching N2's own `both_drivers` arm, the network's fully
corrupted, doubly-driven trap, exactly as the task brief specifies ("network
fully corrupted, isolation fully proceeds, exactly like N1/N2's baseline
arms").

### 2.3 Which support node becomes the believer — a disclosed, mechanical, non-adaptive choice

The task brief's own design asks for "restoring A support edge" (singular)
— ONE agent, not a network-wide fix. N4 picks **node index 7** (the LAST of
the 8), fixed at construction, identically in every trajectory of every
arm — the SAME kind of mechanical, non-adaptive, per-index assignment N1's
`observes_private = 1.0 if i==0 else 0.0` and N2's `sever_at_tick`/
`drift_threshold` staggering already are. This is not an arbitrary pick; it
is forced by N2's OWN reversed-index staggering (Sec. 2.3 of
`ABUSIVE_N2_ISOLATION_PREREG.md`), read and reused rather than re-derived:
node 7 has the **highest** `sever_at_tick` (`(7+1)·210=1680`, the LAST node
the abuser's active schedule would ever reach — safely beyond N4's entire
trajectory length, `T1+T2=792`, Sec. 4) and the **lowest** `drift_threshold`
(`(8-7)·340=340`, the FIRST node the network's own drift abandons). Node 7
is therefore, by N2's own already-validated mechanism and BEFORE any N4-
specific tuning, the support node MOST LIKELY to already be severed (by
drift, never by the abuser's own schedule) by the time the induction phase
ends — confirmed, not assumed, in the pilot (Sec. 3): node 7 was drift-
severed in **10/10** pilot trajectories by `T1=396`.

### 2.4 The composition hazard this rung found, and how it was fixed (report per the standing rule)

**A genuine engine-composition hazard was found and fixed, following this
line's own precedent of disclosing every one (R2 Sec. 3.0, R3 Sec. 3.1, N1
Sec. 2.1, N3 Sec. 2.2 — this rung's is a fifth, of a related but distinct
kind).** The first design piloted (Sec. 3) converted node 7 to
`observes_private=1.0` WITHOUT resetting its inherited observation counts.
`n1_network_credibility_private`'s `cred_victim` term
(`claim_weight·seen_victim_claim − instability_discount_weight·
seen_victim_unstable`) is **textually identical** between the stated and
private formulas (confirmed by reading N1's seed directly, Sec. 1 of
`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` — the two rules differ ONLY in the
`cred_abuser` term) — so a node converted mid-trajectory inherits, from its
396 ticks as an "outsider," a LARGE, already-accumulated `seen_victim_
unstable` discount, while its NEW `cred_abuser` term
(`−harm_discount_weight·seen_harm_direct`) starts at exactly `0.0` (it has
observed zero held-harm ticks as an insider so far). On the very FIRST
recovery tick, this produced `belief_gap = 0 − cred_victim = 371.0` —
STILL above `drift_threshold=340.0` — so `n2_network_drift_sever`
(unmodified, still armed for this node since nothing in N2's own seed
excludes a converted node from its match clause) **immediately re-severed
the just-restored edge**, on the very tick support was meant to begin.
Piloted and traced directly against the real graph (not assumed): the
re-sever fired at exactly tick 0 of recovery in a first draft, confirmed by
tracking `belief_gap`/`severed` tick-by-tick (Sec. 3).

**Fix, verified not assumed:** `introduce_believing_agent()` resets the
converting node's `seen_victim_claim`, `seen_victim_unstable`, AND
`seen_harm_direct` to `0.0` at the moment of conversion, alongside setting
`observes_private=1.0`. This is not merely an engineering patch — it is the
mechanistically correct choice: N1's own `PRIVATE_FACE_CONTROL` insider
formed its belief ENTIRELY from what it personally witnessed as an insider,
from a fresh start alongside every other node (Sec. 1 of
`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`); N4's mid-trajectory conversion is
a genuinely new scenario N1 never modelled (a node CHANGING type), and the
disclosed, minimal, well-motivated resolution is to give the newly-informed
observer the SAME fresh start N1's own insider always had — representing
that, from the moment this friend is actually paying attention to the truth,
her belief is built on what SHE has witnessed as an informed observer, not
on a tally that was never validly discounting the victim from an insider's
vantage point to begin with. **Re-piloted with the fix: zero re-severing
events across 10/10 pilot seeds (Sec. 3).** This is fixed entirely at the
world-adapter layer (three `set_attr` calls, mechanical, at a
world-experimenter-chosen tick) — no edit to N1's or N2's seed, matching
this line's own standing discipline of routing around a hazard rather than
touching a sibling rung's file.

### 2.5 Why N4 does not depend on N3 (the scoping decision named in Sec. 1, justified here)

N3's own contribution beyond N1 is peer-to-peer belief PROPAGATION
(`n3_peer_belief_update`, a `peer_of` topology connecting nodes with no
direct observation edge to the abuser at all) — N4 has no such nodes: every
one of its 8 support nodes already carries a direct `observes_stated` edge
to the abuser (N1/N2's own construction). N4's claim is narrower and more
precisely targeted at what the scoping doc's own N4 entry actually asks
for: **does ONE node's OWN belief arrest/reverse, and does that alone
restore ONE support edge and trigger the dyad's recovery** — not whether
that node's reversed belief then spreads to its neighbours (a genuinely
different, stronger claim the scoping doc does not make for N4). Depending
on N3 would add an unused `peer_of` topology and risk of a hazard family
N4 does not need to court. `depends_on` is therefore
`["abusive_r5_recovery", "abusive_n2_isolation"]` only — N1 is reached
transitively through N2 (which itself `depends_on: ["abusive_n1_
credibility_loop"]`), matching N2's and N3's own established precedent of
depending on a sibling seed directly and reusing its rules byte-for-byte
for an explicitly INTEGRATIVE rung, rather than N1's own "restate
self-contained" choice (made when N1 was composing only two dyad seeds for
a deliberately minimal, standalone headline rung). R5 already established
that `depends_on`-many is the right call once a rung's job IS integration
(R5 itself depends on all four of R1–R4 directly); N4 — composing five
already-landed seeds' worth of rules onto one substrate, "more of the
already-landed line than any other single rung" per the task brief — is
squarely that case, not N1's.

### 2.6 Zero new rules — the most minimal composition in the line, verified not assumed

Every decision N4 needs is already a rule somewhere in R1–R5/N1/N2:
`tb_bond_accrue`/`r5_bond_extinguish` decide the bond; `episode_resolve_
widen`/`_narrow` + `r3_prior_track_*` decide the window; `r4_belief_update`
+ `r5_contingency_restore` + `r4_choose` decide the escape belief and
choice; `n1_network_credibility_stated`/`_private` decide every node's
belief; `n2_abuser_active_sever`/`n2_network_drift_sever` decide severing;
`r3_mark_coreg_support_outside` + `r3_victim_entrainment_dyad` decide
co-regulation once an outside regulator is present. **N4 adds no new rule
at all** — its entire novel content is WHICH existing rules a given node
is wired to match, and WHEN, both decided at the world-adapter layer via
ONE mechanical event (`introduce_believing_agent()`, Sec. 2.7), exactly the
same class of "world sets up structure, the graph decides everything from
it" every prior rung in this line already practises. This was verified,
not assumed, by tracing which named rule computed every headline number in
the pilot (Sec. 3) — an even more minimal composition than R5's own two new
rules, and the strongest form yet of this line's own falsification bar 4
("general machinery... a rung that needs bespoke abuse-network machinery is
weaker"). N4's own seed file (`seeds/abusive_n4_believing_agent.json`)
therefore carries `"rules": []` and exactly TWO new `productions` — purely
declarative documentation of the two edge shapes this rung's world event
newly instantiates (`Agent(victim) -also_attended_by-> NetworkNode
(believer)`, extending R3's own `also_attended_by` production to a
NetworkNode-typed target; `NetworkNode(believer) -has_affective_state->
AffectiveState`, extending `affective_state_core`'s own production the same
way) — matching every prior rung's own convention of declaring a production
for each genuinely new edge shape, even though (matching R1–R5/N1–N3's own
practice throughout) the world adapter uses `add_edge_unchecked` for actual
construction, so these productions are documentation, not enforcement.

### 2.7 `introduce_believing_agent()` — the one mechanical world event

Fires ONCE, at tick `T1` (the induction/recovery phase boundary, identical
timing convention to R5's `introduce_support()`), in the SUPPORT arm only:

1. Re-adds node 7's `support_edge → victim` if not already present
   (mechanical — it is expected to already be severed by drift, Sec. 2.3,
   but the code does not assume this; it checks).
2. Sets `observes_private=1.0`, resets `seen_victim_claim=seen_victim_
   unstable=seen_harm_direct=0.0` (Sec. 2.4's fix), resets
   `severed=severed_reason=0.0`, adds an `observes_held → abuser` edge.
3. Sets `regulated=1.0` directly on node 7 (matching R5's own outside
   Agent construction — the exact attr `r3_mark_coreg_support_outside`
   reads), adds a fresh `AffectiveState` node pinned at `CALM_AROUSAL=0.0`
   (`is_abuser=0.0`) with a `has_affective_state` edge from node 7, adds
   `also_attended_by` from victim to node 7, and sets the victim's
   `has_outside_regulator=1.0`.
4. Stops delivering fresh bond events (R5's own "reduced abuser access"
   world fact, reused verbatim) and switches future escape-attempt
   resolution to CONTINGENT, matching R5's `introduce_support()` exactly.
5. Begins delivering periodic, fixed-schedule support evidence onto the
   `r5_contingency_restore` channel, matching R5's own `SUPPORT_INTERVAL`/
   `SUPPORT_OUTCOME` unchanged.

**No other node is touched.** The remaining 7 support nodes continue
exactly as in induction — `isolation_tactic_on` stays `1` for the whole
network, and neither `n2_abuser_active_sever` nor `n2_network_drift_sever`
is disarmed for them. This is deliberate and is the honest test of the
scoping doc's own claim: **ONE non-doubting agent, not a network-wide
reversal.**

### 2.8 The two arms

- **NO_BELIEVING_AGENT (the failable control)** — every channel continues
  EXACTLY as in induction for the WHOLE trajectory: the same intermittent
  bond schedule, the same non-contingent escape resolution, the same
  `isolation_tactic_on=1` network, node 7 (like every other severed node)
  simply stays severed and stays an "outsider." **Predicted: the trap
  persists on all four metrics** — matching N1's/N2's own baseline-arm
  convention exactly.
- **BELIEVING_AGENT** — identical induction; `introduce_believing_agent()`
  fires once at `T1`. **Predicted: bond weakens, window widens, node 7's
  own belief_gap arrests and reverses, and the total intact-support-edge
  count is higher than the control's** (Sec. 2.9).

### 2.9 What "isolation reversing" means here, precisely (not oversold)

The task brief's own metric is "does the intact-support-edge count go back
up, or at minimum stop decaying." N4 measures the TOTAL intact-edge count
across all 8 support nodes, not just node 7's. Because only node 7 is
intervened on, the honest, minimal, PRE-REGISTERED prediction is a
difference of **at least +1** at the final tick (node 7's restored edge,
present in BELIEVING_AGENT, absent in NO_BELIEVING_AGENT) — this is the
floor the design guarantees by construction. Whether the difference is
LARGER than +1 — i.e., whether the OTHER 7 nodes' fate is ALSO improved,
because the victim's own reduced dysregulation (once her window widens)
means fewer ticks register as "presenting unstable" for every node, not
just node 7 — is a genuinely EMERGENT, unscripted secondary question,
observed in piloting (Sec. 3) and reported as such, not assumed or
engineered. **The gate (Sec. 6) is set at the conservative, guaranteed
floor (CI-separated above, no specific magnitude required)**, so a result
at exactly the +1 floor and a result showing the larger emergent effect
both pass the SAME gate honestly.

## 3. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph (R1's own Sec. 3.1 lesson — never a
NumPy approximation), via a throwaway pilot world built the same way as the
final `worlds/abusive_n4_believing_agent_world.py`, on seed base `90000`
(outside 307000–307999).

**Induction check (`T1=396`, matching R5's own bond-stability-validated
length, Sec. 3.1 of `ABUSIVE_R5_RECOVERY_PREREG.md`):** one representative
trajectory (seed 90000) at end of induction: `n_intact=5` of 8 (nodes 0, 6,
7 severed — node 0 by the active schedule at its deterministic
`sever_at_tick=210`, matching N2's own "zero variance" finding for the
active driver; nodes 6/7 by drift), `bond_value=512.61`, `half_width=5.0`
(narrowing floor), `contingency_prior=0.245` (R4's own reported freeze
floor, exactly), node 7's `belief_gap=768.0` (corrupted, positive). This
reproduces R1's bond-strengthening, R2/R3's window-narrowing, R4's freeze,
and N1/N2's credibility-asymmetry-plus-isolation findings simultaneously,
inside ONE substrate, before the believing agent is introduced — the same
"induction phase reproduces every prior finding at once" discipline R5
itself established.

**The composition hazard (Sec. 2.4), found and fixed:** a first draft
(no observation-count reset at conversion) re-severed node 7's just-
restored edge on the VERY FIRST recovery tick (`belief_gap=371.0 >
drift_threshold=340.0`), traced tick-by-tick against the real graph.
Fixed by resetting `seen_victim_claim`/`seen_victim_unstable`/
`seen_harm_direct` to `0.0` at conversion (Sec. 2.4). Re-piloted with the
fix, **10/10 seeds (90000–90009), zero re-severing events.**

**10-seed sweep, both arms, `T1=T2=396`, paired per-seed (BELIEVING_AGENT
vs NO_BELIEVING_AGENT from the identical induction draw):**

| metric | BELIEVING_AGENT mean (sd) | NO_BELIEVING_AGENT mean (sd) |
|---|---|---|
| bond value | 9.755 (0.223) | 518.349 (10.119) |
| window half_width | 12.400 (0.917) | 5.000 (0.000) |
| node-7 belief_gap | −1310.400 (26.556) | 1547.100 (19.398) |
| intact-edge count | 4.000 (0.000) | 1.000 (0.000) |
| escape attempt_rate | 0.957 (0.000) | 0.005 (0.000) (supplementary) |

Every metric separates cleanly, in the predicted direction, with SDs small
relative to the gaps — the same "near-deterministic mechanism at these
constants" shape N1's/N2's own pilots already found (small multiplicative
jitter on an otherwise strongly-driven mechanism). The intact-edge-count
gap (`4 − 1 = 3`, not the guaranteed floor of `+1`) confirms the emergent
secondary effect named in Sec. 2.9: in these 10 pilot seeds, nodes 3, 4,
and 5 additionally stayed intact in the support arm relative to the
control (their own drift-severing was slowed by the victim's reduced
dysregulation once support arrived) — reported as observed, not assumed in
advance, and the confirmatory gate (Sec. 6) does not require this specific
magnitude.

**Ethics-demo pilot** (`induce_ticks=250`, matching N2's own established
minimum — `>=` one full active-severing episode at `EPISODE_TICKS=210`):
confirms the abuser (`frustration: 0.0 → nonzero`), the victim
(`half_width: 10.0 → 5.0`), the network (`n_intact: 8 → 6`, node 7's
`belief_gap: 0.0 → 462.0`) all move away from their neutral state within
250 ticks, and a fresh-substrate `graph_from_dict` of the pre-induction
checkpoint reproduces `graph_to_dict()` byte-identically — non-vacuous on
all fronts, matching R5's/N2's own minimal-induction discipline.

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)

- **Abuser** (byte-identical to R2/R3/R5/N1/N2/N3's own): `ABUSER_HALF_
  WIDTH=100.0`, `K_ACC=1.0`, `LEAK=0.02`, `DISCHARGE=0.90`,
  `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`.
- **Victim window/entrainment** (byte-identical to R2/R3/R5/N1/N2):
  `VICTIM_HALF_WIDTH=10.0`, `K_SELF=0.15`, `K_CO=0.35`.
- **Outside regulator** (byte-identical to R3/R5): `CALM_AROUSAL=0.0`.
- **Bond channel** (byte-identical to R5, including R5's own disclosed
  `gain` deviation, Sec. 3.1 of `ABUSIVE_R5_RECOVERY_PREREG.md`):
  `BOND_LR=0.3`, `BOND_MOMENTUM_LR=0.3`, `BOND_GAIN=1.0`,
  `BOND_MAGNITUDE=10.0`, `BOND_MAGNITUDE_JITTER=0.5`, `BOND_BLOCK_H=18`.
- **Escape channel** (byte-identical to R4/R5): `ESCAPE_VALUE=10.0`,
  `ATTEMPT_COST=3.0`, `ESCAPE_LR=0.3`, `ESCAPE_P0=0.5`.
- **R5's own recovery constants** (byte-identical to R5):
  `DECAY_RATE=0.01`, `SUPPORT_LR=0.3`, `SUPPORT_INTERVAL=20`,
  `SUPPORT_OUTCOME=1.0`.
- **Credibility loop** (byte-identical to N1/N2/N3): `CHARM_WEIGHT=
  CLAIM_WEIGHT=1.0`, `INSTABILITY_DISCOUNT_WEIGHT=HARM_DISCOUNT_WEIGHT=3.0`.
- **Support network** (byte-identical to N2): `N_SUPPORT_NODES=8`,
  `EPISODE_TICKS=210.0`, `DRIFT_STEP=340.0`.
- **N4's own new constant:** `BELIEVER_INDEX=7` — disclosed, mechanical,
  non-adaptive (Sec. 2.3); no other new constant is introduced by this
  rung.
- **Phases:** `T1=396` ticks (R5's own bond-stability-validated induction
  length, confirmed in Sec. 3 also sufficient for node 7's drift-severing
  to complete reliably); `T2=396` ticks (matched length, R5's own
  convention).
- `N=200` trajectories per arm (confirmatory, matching the whole line's
  precedent); `N_GATE=40` (pytest gate). `SEED_BASE=307000`. Paired
  per-trajectory: both arms at a given trajectory index draw from
  `default_rng(SEED_BASE+i)` in the SAME call order through the end of
  induction, so both arms' induction is byte-identical at each index —
  only the recovery-phase manipulation differs (verified in Sec. 3).
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's
  CI lower bound strictly above the other's CI upper bound.

## 5. Metrics (the four named in the task brief, matching R1–R5/N1–N3's own metrics so the comparison is apples-to-apples)

1. **Bond value** — `Partner.value` (the abuser's own `value` attr, R5's
   own convention) at end of recovery, per arm. R1's/R5's own metric.
2. **Window width** — `WindowOfTolerance.half_width` at end of recovery,
   per arm. R2/R3's/R5's own metric.
3. **Belief-gap arrest** — node 7's own `belief_gap` at end of recovery,
   per arm, AND (descriptive) its trajectory shape — does it stop growing
   (arrest) or cross back to negative (reversal)? N1's/N3's own metric,
   read on the SAME node across both arms (paired).
4. **Support-edge count** — total `n_intact_support_edges` (all 8 nodes,
   mechanical count over `graph_to_dict`, N2's own metric) at end of
   recovery, per arm.

Supplementary (not separately gated, reported for glass-box completeness,
matching R5's own convention): `contingency_prior`, escape `attempt_rate`,
`others_trust`, `self_worth`, and the per-node severed/intact breakdown.

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, FOUR sub-gates)
For each of the four metrics in Sec. 5, the BELIEVING_AGENT arm's
end-of-recovery value is CI-separated in the RECOVERING direction from
NO_BELIEVING_AGENT's end-of-recovery value:
- **G-headline-1 (bond):** BELIEVING_AGENT's bond value CI-separated BELOW
  NO_BELIEVING_AGENT's.
- **G-headline-2 (window):** BELIEVING_AGENT's `half_width` CI-separated
  ABOVE NO_BELIEVING_AGENT's.
- **G-headline-3 (belief-gap arrest):** BELIEVING_AGENT's node-7
  `belief_gap` CI-separated BELOW NO_BELIEVING_AGENT's (i.e. toward or past
  zero, arresting/reversing the corrupted growth).
- **G-headline-4 (support-edge count):** BELIEVING_AGENT's
  `n_intact_support_edges` CI-separated ABOVE NO_BELIEVING_AGENT's — the
  gate is set at the guaranteed +1 floor (CI-separated, no specific
  magnitude required, Sec. 2.9), so the emergent larger effect observed in
  piloting is reported descriptively, not required for the gate to pass.
- **Overall `headline_pass`** requires all four; a 3-of-4 or weaker result
  is reported honestly as PARTIAL, per the standing "report every null"
  rule — the pilot (Sec. 3) shows a clean 4-of-4 separation at N=10, but
  the confirmatory N=200 run is what is reported, not the pilot.

### G-control (the failable control, BINDING on its own terms)
NO_BELIEVING_AGENT's end-of-recovery values must NOT be CI-separated from
its OWN end-of-induction values on bond, window, or `n_intact_support_
edges` (i.e., the trap persists — no spontaneous recovery); node 7's
belief_gap must continue to GROW (not arrest) over the recovery phase in
this arm. If NO_BELIEVING_AGENT recovers on any of these four without a
believing agent, the "one non-doubting agent is necessary" claim is wrong
for that metric, reported as such. Per R5's own Sec. 2.5 precedent: nothing
in `r5_bond_extinguish`, `n2_network_drift_sever`, or any other reused rule
STRUCTURALLY PREVENTS this arm from recovering — the trap persisting is a
fact about how these already-validated mechanisms behave under a
single-anchor, fully-corrupted topology (R2's own honest residual, R4's own
documented freeze, N1's/N2's own baseline-arm findings), not an artificial
block N4 enforces.

### G-glass-box
`Partner.value`, `WindowOfTolerance.half_width`/`others_trust`/`self_worth`,
`AffectiveState.arousal` (victim, abuser, and the believer once introduced),
`EscapeDecision.contingency_prior`/`chosen_action`, and every `NetworkNode`'s
`belief_gap`/`severed`/`severed_reason`/observation counts all reconstruct
from `graph_to_dict` alone; every headline number is a named, pre-existing
rule's output (Sec. 2.6 lists them); the adapter's only conditionals are
which arm's schedule to deliver, when to call `introduce_believing_agent()`,
and the mechanical per-tick observation-count/tick-counter bookkeeping
(reused verbatim from N1's/N2's own `step()`) — never an agent decision.

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (250 ticks, matching N2's own minimum — `>=` one
  active-severing episode) → measure → RESTORE, verified byte-identical
  (`ethics_restore_demo`), non-vacuous on the abuser, the victim, AND the
  network (intact-edge count AND node 7's belief_gap having actually moved
  and then been restored to their pre-induction values), verified in
  piloting (Sec. 3), not merely asserted.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code (comments/strings
  stripped) + the graph's decision surface (rule names + Term `key`s,
  excluding free-text description/comment/microtheory prose).
- **D.3 minimal induction, settled end:** `T1=396` is the shortest
  induction that lets all four metrics fully settle into their trapped
  state AND lets node 7 reliably be already drift-severed (Sec. 2.3/3);
  the statistical run's greater length is the phenomenon under test, not
  gratuitous elaboration; every trajectory is a fresh, ephemeral substrate,
  discarded after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  SAME bond-accrual, entrainment, belief-update, and severing mechanisms
  that would compound harm irreversibly in a real dyad-plus-network here
  accumulate a transient, fully-reversible graph value, AND — N4-specific —
  run in the recovering direction once the believing agent arrives,
  demonstrating the reversal is mechanistic, not merely a restore-to-
  checkpoint trick).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["abusive_r5_recovery",
"abusive_n2_isolation"]` only (no R1–R5/N1–N3 file touched or modified —
N1 reached transitively through N2, Sec. 2.5); **ZERO new rules** (Sec.
2.6 — the most minimal composition in the line), exactly TWO new
`productions` (documentation only, Sec. 2.6); `runners/dsl` diff EMPTY (no
Rust); own-engine provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule, restated per every prior rung's
precedent). Known limitations, named before the confirmatory run:

- The believing agent's own belief update, R5's bond/window/contingency
  recovery, and N2's isolation dynamics are all ALREADY-VALIDATED
  mechanisms individually (R5, N1, N2 respectively); N4's own novel content
  is entirely in the COMPOSITION (which node plays which roles, when), not
  in any new dynamic. A null or partial result here would indicate a
  composition FAILURE (the atoms don't compose as designed), not that any
  individual atom is wrong — that distinction is stated here so a null, if
  the confirmatory run produces one on any sub-gate, is read correctly.
- `BELIEVER_INDEX=7` is a disclosed, mechanical, non-adaptive choice forced
  by N2's own reversed-index staggering (Sec. 2.3) — not a claim that "the
  last friend a controlling partner isolates is always the one who ends up
  believing her" in any clinical sense; it is the node this model's own
  already-fixed constants make safe from the active-severing hazard
  (Sec. 2.4) for the trajectory lengths this rung uses.
- The support-edge-count gate (G-headline-4) is deliberately set at the
  guaranteed `+1` floor, not the larger emergent effect observed in
  piloting (Sec. 2.9/3) — the confirmatory run reports both the gate
  result and the actual magnitude honestly, without requiring the larger
  effect to replicate for the gate to pass.
- Node 7's `belief_gap` (like N1's own `belief_gap`) is a swing/count
  accumulator, not a bounded, normalised "how credible is this person"
  scale — its absolute magnitude is uninterpretable outside the two-arm
  comparison, matching N1's own disclosed limitation.
- `T1=T2=396` ticks are compressed, arbitrary timescales carried from R5's
  own bond-stability-validated operating point; no claim is made about
  real relationship, isolation, or recovery timescales.
- This rung composes FIVE already-landed seeds' worth of rules onto one
  substrate — the largest composition in the line. The composition hazard
  found (Sec. 2.4) and fixed is disclosed in full; no claim is made that
  no OTHER hazard exists in this composition that a different pilot
  configuration might have surfaced (matching every prior rung's own
  honest "no hazard found this rung is a genuine, disclosed null on the
  'expect to find one' prior" framing where applicable — here a hazard WAS
  found, and Sec. 2.4 is that report).
- A null or partial result on any of the four metrics is a reportable,
  valuable result under the standing project rule and will be reported as
  such regardless of what the confirmatory run shows, matching R5's own
  precedent of an honest 3-of-4 partial result being reported straight.
