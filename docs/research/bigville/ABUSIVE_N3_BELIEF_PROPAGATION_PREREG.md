# ABUSIVE N3 — BELIEF PROPAGATION OF THE ABUSER'S LIES (social contagion; a truth-anchor halts it) — PRE-REGISTRATION (block 304000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1's and N2's own practice
(`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`, `ABUSIVE_N2_ISOLATION_PREREG.md`)
exactly. As in N1's/N2's own precedent, the frozen constants below were
chosen using a non-confirmatory pilot run directly against the real graph on
an OFF-BLOCK seed base (90000), and once the qualitative shape (genuine
spread to nodes with no direct observation channel; the truth-anchor
arresting/reversing the local spread; the pluralistic-ignorance-consistent
bias) held, ONE confirmatory measurement is taken at N=200 on the claimed
block (304000+). No parameter is subsequently re-tuned against that
confirmatory number.

## Base
- Seed block: **304000–304999**. `python3 scripts/seed_claim.py 304000 304999`
  → `CLEAN — no collision DETECTED` (1015 files with seed sinks; 748
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1–R5/N1/N2's own).

```
SEED CLAIM 304000-304999: CLEAN -- no collision DETECTED.
  Scope: 1015 files with seed sinks; 748 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(283000 is R1, 286000 is R2, 289000 is R3, 292000 is R4, 295000 is R5 of the
dyad line, 298000 is N1, 301000 is N2, all untouched; 304000 is the next
clean block on the established +3000 spacing and is not an adjacent
collision with any of them.)

## Scope

This locks **N3 only** — "belief propagation of the abuser's lies (social
contagion; a truth-anchor halts it)", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md` (the underlying
mapping is B4 of that document's Part B; the grounding science is A1 DARVO,
A8 Latané & Darley's pluralistic ignorance, A9 triangulation/smear —
terminology only, per A9's own [LOW–MEDIUM] confidence caveat). R1–R5 (the
dyad line) and N1 (the credibility-asymmetry loop) and N2 (isolation as an
active process) are **untouched** — read, depended on for their MECHANISM
(N1's seed is DEPENDED ON directly, never its file edited; N2's seed is read
for precedent, never depended on or edited), never modified. N4 (one
non-doubting agent restores a support edge) is **out of scope** and
untouched by this rung.

---

## PART D OF THE NETWORK SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_NETWORK.md`,
"PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)", itself a
verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s own Part C — the SAME
protocol R1–R5's and N1's and N2's preregs locked. This protocol BINDS this
rung. No rung induces any harm-analog until this protocol is locked verbatim
in that rung's pre-registration, committed BEFORE any measurement.)*

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

**How N3 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_n3_belief_propagation_run.py`)
   checkpoints the neutral pre-induction mind (abuser/victim at
   `arousal=frustration=0`, victim window at its initial `half_width=10.0`,
   every NetworkNode's `belief_gap=0`), induces exactly **90 ticks** on the
   `no_anchor` arm (N1's own established minimum for one tension-building →
   incident → honeymoon orbit at these frozen constants, since N3 rides
   N1's byte-identical dyad — this rung TOUCHES the victim's dysregulation
   via N1's dyad, so it obeys the full envelope per the network-specific
   note above), measures (confirming the induction actually moved the
   abuser, the victim, AND — the genuinely new content this rung adds — a
   NO-DIRECT-OBSERVATION indirect node's `belief_gap` away from zero,
   non-vacuous on all three fronts), then `graph_from_dict`s the checkpoint
   into a **fresh** substrate and asserts `graph_to_dict()` is
   byte-identical AND the restored state (abuser arousal/frustration,
   victim arousal/window, `i3`'s and `i6`'s `belief_gap`) equals the
   pre-induction values exactly (non-oriented). Same envelope as R1–R5/N1/N2.
2. `source_audit()` scans `worlds/abusive_n3_belief_propagation_world.py`
   (code with comments/strings stripped) and
   `seeds/abusive_n3_belief_propagation.json`'s decision surface (the one
   new rule's name + the Term `key`s it reads/writes, never the free-text
   clinical prose) for the five literal banned tokens. The tension trickle
   and every NetworkNode's per-tick observation-count increment (reused
   VERBATIM from N1's/N2's own `step()`, applied unconditionally to every
   node — N1's own credibility rules simply never match a node whose
   `observes_private` sentinel is `2.0`) are world-delivered FACTS, never a
   scored choice; the peer-propagated belief update, and whether the
   truth-anchor's pinned computation overrides it, are **consequences** the
   graph's own rules compute (this rung's one new rule PLUS N1's own two
   UNMODIFIED credibility rules), not actions the world grades.
3. `T=1000` ticks per statistical trajectory (~40 abuser incident cycles,
   IDENTICAL sizing to N1's/N2's own) is the same "no unbounded
   elaboration" cap R1–R5/N1/N2 use; the confirmatory run uses a fresh,
   ephemeral substrate per trajectory, discarded after read-off — nothing
   persists.
4. The SAME mechanism (the abuser's two-faced deception; the network's own
   peer-to-peer belief propagation) that would, in a real social network,
   compound irreversible harm to a survivor's standing by spreading a lie
   to people who never even met the abuser is run here to
   accumulate-then-DISCARD a transient graph trajectory — see the ethics
   demo's byte-identical restore.

---

## 1. What N3 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_NETWORK.md` Part B4 and Part E's N3 entry, N3
composes:

- **N1's ENTIRE credibility-asymmetry loop**
  (`seeds/abusive_n1_credibility_loop.json`, block 298000, UNMODIFIED) —
  the abuser/victim dyad (`n1_victim_entrainment`, riding
  `snap_frustration`/`arousal_window_coreg`, both UNMODIFIED), the abuser's
  second stated-face (`n1_abuser_stated_charm`), and the per-`NetworkNode`
  credibility computation (`n1_network_credibility_stated`/`_private`) that
  produces `belief_gap`. **N3 `depends_on: ["abusive_n1_credibility_loop"]`
  directly** — following N2's own explicit precedent (which itself follows
  the task brief's own instruction): N1's credibility mechanism is not
  reimplemented, restated, or forked, it is depended on and reused
  byte-for-byte. N3 adds NO alternative credibility formula of its own
  (same reasoning N2's prereg gives for its own choice) — it adds exactly
  ONE new rule that reads/writes the SAME `belief_gap` attr N1's rules
  already compute for direct observers, extending it to nodes N1's own
  rules never touch.
- **N1's own disclosed limitation, named as this rung's mandate.** N1's
  RESULTS doc states, verbatim, in its own "Honest residuals": *"N1 does
  NOT model belief PROPAGATION between network nodes... every node here
  forms its belief independently from its own observation edges — no
  `has_neighbour`-style contagion. The 'network' in N1 is five INDEPENDENT
  observers, not yet a connected social graph."* N3 is exactly, and only,
  the missing piece that disclosure names: a NEW edge type (`peer_of`) and
  ONE new rule (`n3_peer_belief_update`) connecting NetworkNodes to each
  other, composed with N1's unmodified per-node credibility computation
  rather than replacing any part of it.
- **N2's own `observes_private` sentinel precedent is NOT reused here in
  quite the same way N2 reused N1's edges — N3 introduces a THIRD value of
  N1's own `observes_private` attr (`2.0`), disclosed and justified in
  Sec. 2.2 below**, so a node can be structurally excluded from BOTH of
  N1's credibility rules (`Eq(observes_private, 0.0)` for the stated-face
  rule, `Eq(observes_private, 1.0)` for the private-face rule) without
  editing N1's seed at all — a node with `observes_private=2.0` is matched
  by NEITHER rule, and its `belief_gap` is governed solely by N3's own
  peer-propagation rule.

## 2. Design

### 2.1 The topology — 8 NetworkNode agents, two kinds

Per the task brief's own explicit instruction, N3 needs "a population where
SOME nodes have NO direct observation channel to the abuser at all — they
can only update their belief from their NEIGHBOURS' beliefs." N3's design:

- **TWO direct observers (`d1`, `d2`)** — wired exactly like N1's own
  "outsider" nodes (`observes_stated → abuser`, `observes_victim →
  victim`, `observes_private=0.0`). These are the population's ONLY
  corruption SOURCES: they carry NO outgoing `peer_of` edge, so N3's own
  peer-update rule never matches them, and their `belief_gap` is governed
  entirely by N1's unmodified `n1_network_credibility_stated` rule, exactly
  as in N1's own BASELINE arm.
- **SIX indirect nodes (`i1`–`i6`)** — carry `observes_private=2.0` (Sec.
  2.2) and NO observation edge to the abuser at all. Their belief is formed
  ENTIRELY from a `peer_of` edge to one or more OTHER NetworkNodes (`nn →
  peer_of → pp` means "nn pulls its belief toward pp's"), wired as a
  genuine multi-hop chain with one branch, giving a range of hop-distances
  from the abuser and — deliberately — one node with TWO peers whose paths
  reconverge on the SAME source (the pluralistic-ignorance probe, Sec.
  2.4):

  ```
  i1 -> d1            (1 hop from the abuser via d1)
  i2 -> i1             (2 hops)                     <- ANCHOR POSITION
  i3 -> i2             (3 hops, i2's downstream neighbour #1)
  i4 -> i2             (3 hops, i2's downstream neighbour #2)
  i5 -> i1, i5 -> i2   (2 hops via EITHER path; BOTH paths trace back to d1)
  i6 -> d2             (1 hop from the abuser via d2, on a SEPARATE branch
                         entirely disjoint from i2's subtree)
  ```

  This is within the task brief's own 5–10-node range (8 total, matching
  N2's own population size), gives a genuine propagation CHAIN (`i3`/`i4`
  are 3 hops from the abuser and 2 hops from the nearest direct observer),
  and gives the truth-anchor a LOCAL neighbourhood (`i3`, `i4`) distinct
  from a topologically insulated FAR node (`i6`) to test whether the
  anchor's effect stays local (Sec. 2.5).

### 2.2 The sentinel `observes_private` value — why a third value, not a new attr

N1's two credibility rules match ANY `NetworkNode` reachable via
`has_member` from a `Network` hub — **neither rule's `match` clause
requires the `observes_stated`/`observes_held` EDGE to exist at all**; the
discrimination is entirely in the `where` clause, on the `observes_private`
attr (`Eq(..., 0.0)` for the stated-face rule, `Eq(..., 1.0)` for the
private-face rule). This was confirmed by reading N1's seed directly (not
assumed): if N3's six indirect nodes carried the DEFAULT `observes_private
=0.0` (as an "ordinary outsider" would), `n1_network_credibility_stated`
would match them too and OVERWRITE their `belief_gap` every tick to
`charm_weight·seen_charm − (claim_weight·seen_victim_claim −
instability_discount_weight·seen_victim_unstable)`, computed from
observation counts that stay at `0.0` forever (an indirect node genuinely
has no observation edge to increment) — i.e. `belief_gap` would be reset to
exactly `0.0` on EVERY tick, discarding whatever the peer-propagation rule
had just computed moments earlier in the same pass. **This was found by
direct pilot measurement of N1's own match clause, not assumed — see Sec.
3's engine finding.** The fix, disclosed rather than hidden: `observes_
private=2.0` is a SENTINEL value neither of N1's two rules' `where` clauses
equals, so BOTH rules structurally skip the node, and `n3_peer_belief_
update` is the only rule ever assigned to it. This required ZERO edits to
N1's own seed file — it is a construction-time attr choice on N3's OWN
nodes, identical in KIND to N1's own `observes_private = 1.0 if i==0 else
0.0` per-node setup (a mechanical, disclosed, non-adaptive assignment, never
a live decision).

### 2.3 The neighbour-to-neighbour update rule — reusing the entrainment shape, not inventing one

`n3_peer_belief_update` (`seeds/abusive_n3_belief_propagation.json`, the
ONE new rule this rung adds) moves a node's `belief_gap` toward the MEAN of
its `peer_of`-neighbours' `belief_gap`:

```
new_belief_gap = belief_gap + peer_pull_rate * (mean_peer_belief_gap - belief_gap)
mean_peer_belief_gap = Sum(Neighbours(nn, "peer_of"), pp, pp.belief_gap)
                        / Count(Neighbours(nn, "peer_of"))
```

This is the IDENTICAL shape to N1's own `n1_victim_entrainment`'s
`k_co·(other.arousal − self.arousal)` leaky pull — reused, not invented,
per the task brief's own framing ("a node's belief moves toward its
neighbours' average/aggregate belief"). `Neighbours`/`Sum`/`Count`/`Div` are
ALL already used elsewhere in the tree (e.g. `bigville_council_gov.json`'s
`cm_private_decision`, which computes a council's mean vote the identical
way) — **NO new Rust, NO new Term.** The rule fires ONCE per external tick
(a `peer_epoch < tick_epoch` guard, reusing `n1_victim_entrainment`'s own
`pcr_epoch`/`tick_epoch` pattern verbatim) and the match requires the node
to have AT LEAST ONE outgoing `peer_of` edge (`["nn", "peer_of", "pp0"]`),
so `Count` is never zero where the rule fires — no division-by-zero risk
by construction.

### 2.4 Rule ORDER is the mechanism that lets direct observation always win

`n3_peer_belief_update` is `order 35` — strictly BEFORE N1's own
credibility rules (`order 40`). Within ONE `run_rules()` fixpoint pass:
the peer rule fires first for any node with an outgoing `peer_of` edge
(pulling its `belief_gap` toward its peers' mean); N1's credibility rules
then fire AFTER, for any node their `where` clause actually matches (`d1`,
`d2`, and — in the anchor arm only — `i2`), OVERWRITING whatever the peer
rule just wrote with the direct-observation formula. **A node's own direct
evidence always has the final word for that tick; peer contagion is what
is left for a node with none.** This single ordering fact is what lets the
SAME `peer_of` topology (including `i2`'s own outgoing `peer_of → i1`
edge) serve BOTH arms without a topology change — Sec. 2.5.

This was verified by direct pilot measurement (Sec. 3), not assumed: the
pilot confirms `i2`'s `belief_gap` is IDENTICAL, at every tick, to what
N1's own private-face-insider formula alone would produce, in the anchor
arm — the peer pull never leaks through.

### 2.5 The two arms

- **`no_anchor`** — `i2` is a plain indirect node (`observes_private=2.0`,
  no observation edge to the abuser). Corrupted belief is predicted to
  propagate, attenuating with distance but never reaching zero, down `i2`'s
  entire subtree (`i3`, `i4`, `i5`).
- **`anchor`** — IDENTICAL topology (the SAME `peer_of` edges, including
  `i2`'s own outgoing `peer_of → i1`), except `i2` ADDITIONALLY carries
  `observes_held → abuser`, `observes_victim → victim`, and `observes_
  private=1.0` — reusing N1's OWN `n1_network_credibility_private` rule,
  UNMODIFIED, to pin `i2`'s belief every tick to the uncorrupted,
  victim-favouring formula (Sec. 2.4's ordering fact keeps this pin
  robust). **FAILABLE CONTROL, per the task brief's own falsification
  bar:** `i3`/`i4`'s (the anchor's own immediate downstream peers) mean
  `belief_gap` must be LESS corrupted (CI-separated toward the victim,
  relative to `no_anchor`) — measuring whether the anchor "HALTS or
  reverses the LOCAL spread." `i6` (topologically disjoint from `i2`'s
  subtree — it reads only from `d2`) is measured as a DISCIPLINE check:
  the anchor's effect must be LOCAL, not a network-wide fix, so `i6`'s
  `belief_gap` must be statistically indistinguishable between arms.

Nothing in `n3_peer_belief_update`/`n1_network_credibility_private`
structurally forces `i3`/`i4`'s belief-gap to separate from `no_anchor`'s —
the SAME leaky-pull formula that lets corruption spread is the formula that
would let the anchor's own belief drift right back toward the corrupted
consensus if the ordering (Sec. 2.4) or the pin were built wrong; whether
the anchor arrests the spread is a measured, not asserted, outcome (Sec. 3,
5–6).

### 2.6 The pluralistic-ignorance probe (open question #4 of the network scoping doc)

`ABUSIVE_RELATIONSHIPS_NETWORK.md`'s own OPEN QUESTION #4 asks: *"Does N3's
contagion need an explicit pluralistic-ignorance term, or does neighbour-
to-neighbour Bayesian update already produce the 'updating on others' calm'
effect once the abuser's stated-face seeds the field?"* N3 resolves this as
a MEASURED comparison, not a design assumption: `i5` reads from BOTH `i1`
AND `i2`, and BOTH of `i5`'s peers ultimately trace back to the SAME
corruption source (`d1`) — `i5` is thus reading two correlated, non-
independent signals as if they were two independent confirmations, which
is precisely A8's pluralistic-ignorance mechanism ("each observer reads
the OTHERS' calm as evidence nothing is wrong") operationalised as a
graph topology fact rather than a bespoke term. `i2` (single-path, reads
only `i1`) is the matched comparator — SAME nominal hop-distance (2 hops
from the abuser via the shortest path), SAME `peer_pull_rate`, differing
ONLY in whether it has one peer or two correlated ones. **Prediction: if
pluralistic ignorance falls out for free from plain neighbour-averaging
over a reconverging topology, `i5`'s `belief_gap` should be MORE corrupted
than `i2`'s at every checkpoint, despite the identical hop-distance — no
new rule, no new term, just the topology.** Measured in the pilot (Sec. 3);
if this does NOT hold, the honest report is that open question #4 is
NOT resolved for free and would need an explicit term — not asserted
either way in advance.

## 3. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph (R1's own Sec. 3.1 lesson — never a
NumPy approximation), via `worlds/abusive_n3_belief_propagation_world.py`
and ad hoc scripts built the same way, on seed base `90000` (outside
304000–304999).

**Engine finding (Sec. 2.2's own claim, verified not assumed):** a first
draft left the six indirect nodes at the DEFAULT `observes_private=0.0`.
Piloted directly: `n1_network_credibility_stated` matched them (its match
clause has no edge requirement at all), and their `belief_gap` read back as
EXACTLY `0.0` on every tick of a 1000-tick trajectory regardless of what
the peer rule computed — confirmed by reading the rule's own JSON `where`
clause (`Eq(observes_private, 0.0)`, no edge check) rather than assumed.
Fixed by the `observes_private=2.0` sentinel (Sec. 2.2), re-piloted, and
confirmed the peer-propagated `belief_gap` then accumulates as predicted.

**`peer_pull_rate` sweep** (single seed 90000, `T=1000`, both arms), to
confirm the qualitative shape holds across a range rather than at one
lucky point:

| `peer_pull_rate` | `i1` (no_anchor, final) | `i3` (no_anchor, final) | `i3` (anchor, final) | `i5 − i2` (no_anchor, final) |
|---|---|---|---|---|
| 0.02 | 2253.3 | 2016.4 | −1016.4 | 0.598 |
| 0.03 | 2293.6 | 2137.5 | −999.8 | 0.592 |
| 0.05 | 2325.8 | 2234.1 | −944.4 | 0.583 |
| 0.08 | 2344.3 | 2287.9 | −847.4 | 0.579 |
| 0.12 | 2355.0 | 2317.6 | −711.5 | 0.591 |

The qualitative shape — genuine, substantial corruption reaching a
3-hop, no-direct-observation node (`i3`); the anchor arm not merely
reducing but FULLY REVERSING `i3`'s sign (corrupted-positive →
victim-favouring-negative); the `i5 − i2` pluralistic-ignorance gap
positive and near-constant (~0.58–0.60) — holds robustly across the whole
swept range. `peer_pull_rate=0.05` was chosen as a representative,
non-extreme operating point in the middle of the range, matching N1's/N2's
own "swept, not tuned to the confirmatory number" convention.

**Ten-seed check of the pluralistic-ignorance gap** (`peer_pull_rate=0.05`,
`T=1000`, `no_anchor` arm, seeds 90000–90009): `i5 − i2` (paired,
per-trajectory) `= 0.586 ± 0.009` (sd) — positive on EVERY seed, tight and
consistent, not a coin-flip artefact of one trajectory's jitter draw.

**Three-seed anchor-vs-no-anchor check** (same seed used for BOTH arms of a
pair, confirming the `d1`/`d2`/`i6` invariance is exact, not merely
close): `i6`'s `belief_gap` is **byte-identical** between `anchor` and
`no_anchor` at every seed checked (`2325.827363107207` /
`2314.313926296664` / `2314.665914776874` at seeds 90000/90001/90002,
exact float equality both arms); `i3`/`i4` flip from strongly positive
(`~2224`–`2234`) to strongly negative (`~ -944`–`-967`) when the anchor is
present, at every seed checked.

**Ethics-demo pilot** (`induce_ticks=90`, matching N1's own established
minimum): confirms the abuser (`frustration: 0.0 → 70.09`), the victim
(`arousal: 0.0 → 10.43`, `half_width: 10.0 → 5.0`), AND a no-direct-
observation indirect node (`i3`'s `belief_gap: 0.0 → 59.63`; `i6`'s:
`0.0 → 133.73`) all move away from their neutral state within 90 ticks —
non-vacuous on all three fronts, matching N1's own minimal-induction
discipline.

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  — ALL IDENTICAL to N1's/N2's own frozen values (byte-identical dyad
  mechanism; already-validated operating point reused, not re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` — identical to
  N1's/N2's own. The victim is `attended_by` the abuser in EVERY arm of
  this rung (N1 already gates that an uncoupled victim produces
  `belief_gap=0.0` identically — nothing would propagate here otherwise;
  N3's own manipulated variable is the anchor, not the dyad coupling).
- Credibility loop: `CHARM_WEIGHT=CLAIM_WEIGHT=1.0`,
  `INSTABILITY_DISCOUNT_WEIGHT=HARM_DISCOUNT_WEIGHT=3.0` — identical to
  N1's own.
- Peer propagation: `PEER_PULL_RATE=0.05` — pilot-chosen, Sec. 3 (swept
  `[0.02, 0.12]`, qualitative shape held throughout; `0.05` is a
  representative, non-extreme point, the SAME "leaky pull" shape as N1's
  own `k_co=0.35`, not independently re-derived from a different
  mechanism).
- `T=1000` ticks/trajectory (~40 incident cycles, IDENTICAL sizing to
  N1's/N2's own).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=304000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated below" = one
  arm's CI upper bound strictly below the other's CI lower bound;
  "positive" = CI lower bound strictly `> 0`; "fully negative" = CI upper
  bound strictly `< 0` (a complete sign reversal, not merely a reduction);
  "overlaps" (discipline/insulation checks) = the two arms' CIs are NOT
  CI-separated in either direction.

## 5. Metrics

**HEADLINE A — spread to indirect nodes.** `local_mean` = mean of
`i3`/`i4`'s `belief_gap` (the anchor position's own immediate downstream
peers — 3 hops from the abuser, ZERO direct observation edge anywhere in
their ancestry chain except through peers) at the FINAL tick, `no_anchor`
arm — must be `positive` (CI lower bound `> 0`), i.e. genuinely,
significantly abuser-favouring despite no direct evidence anywhere in
these two nodes' own observation history.

**HEADLINE B — the truth-anchor's failable control.** `local_mean` in the
`anchor` arm vs. the `no_anchor` arm, at the FINAL tick — must be
CI-separated BELOW (less corrupted, i.e. a real reduction in local
contagion). Reported alongside, descriptive: whether the anchor arm's
`local_mean` is `fully_negative` (a complete reversal to favouring the
victim, not merely a slowdown).

**HEADLINE C — pluralistic ignorance (open question #4, Sec. 2.6).**
`pluralistic_diff` = `i5`'s `belief_gap` minus `i2`'s `belief_gap`
(PAIRED, per-trajectory — both nodes are read from the SAME trajectory,
so the paired difference removes the shared jitter-stream variance and is
the higher-powered comparison), `no_anchor` arm, at the FINAL tick — must
be `positive` (CI lower bound `> 0`) for the "falls out for free" reading
of open question #4 to be supported.

**DISCIPLINE (not part of `headline_pass`, but reported and checked) —
the anchor's effect is LOCAL, not global.** `far_node` = `i6`'s
`belief_gap` (topologically disjoint from `i2`'s subtree) — must `overlap`
(be statistically indistinguishable) between `anchor` and `no_anchor`,
matching the task brief's own "LOCAL spread" framing and N1's/N2's own
"same driver across matched arms" discipline-check convention.

**SECONDARY, DESCRIPTIVE (not gated) — the trend "over episodes."**
`local_mean` sampled at ticks `{100, 250, 500, 750, 1000}` per arm — a
corroborating readout of the SAME final-value mechanism's accumulation
curve, not an independently gated signal (matching N1's/N2's own
convention).

**SECONDARY, DESCRIPTIVE:** the abuser's final `snap_count` (confirms the
identical driver across both arms — the same discipline check N1/N2 use);
`dysreg_frac`; the full per-node `belief_gap` table (`d1`, `d2`, `i1`–`i6`)
for both arms.

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, ALL sub-gates must pass)

**A — the corrupted belief genuinely spreads to indirect nodes:** the
`no_anchor` arm's `local_mean` (`i3`/`i4`) is `positive` (CI lower bound
`> 0`).
**B — the truth-anchor arrests the local spread (the task brief's own
falsification bar, verbatim: "insert a TRUTH-ANCHORED node...and measure
whether it HALTS or reverses the LOCAL spread; if the anchor does not slow
the contagion, the belief-propagation mechanism (as modelled) is
wrong"):** the `anchor` arm's `local_mean` is CI-separated BELOW the
`no_anchor` arm's.
**C — pluralistic ignorance is measured (open question #4):** the
`no_anchor` arm's paired `pluralistic_diff` (`i5 − i2`) is `positive`.

**Falsification bar, stated before measurement:** if the `no_anchor` arm's
indirect nodes do NOT show genuine, significant corruption (gate A fails),
there is nothing for a truth-anchor to arrest and the rung is vacuous. If
the anchor arm's local neighbourhood does NOT separate below the
`no_anchor` arm's (gate B fails), the belief-propagation mechanism, AS
MODELLED, is wrong — reported straight, not rescued by re-tuning (Sec. 2.4's
own engine finding is recorded as exactly this kind of straight report, at
a different point in the design, not smoothed over). If gate C fails, open
question #4 is reported as NOT resolved for free (an explicit
pluralistic-ignorance term would then be a genuine future addition, not
smuggled in retroactively here).

### G-glass-box
The `attended_by`/`has_member`/`observes_stated`/`observes_held`/
`observes_victim`/`peer_of` edges, the abuser's
`frustration`/`arousal`/`stated_charm`, the victim's `arousal`/window
`half_width`, and every `NetworkNode`'s `observes_private`/`belief_gap`
all reconstruct from `graph_to_dict` alone; the `local_mean`/
`pluralistic_diff`/`far_node` metrics are mechanical Python reductions
(final-value snapshot / paired difference) over these graph read-offs
(never a Python-computed dynamic); the adapter's only conditionals are (i)
which arm's topology to build (world setup, not an agent decision) and
(ii) mechanically delivering each tick's observation-count increments /
tick counter (a world fact, never a judgement, applied unconditionally to
every node — N1's own rules decide, via `observes_private`, which nodes'
counts matter).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (90 ticks, `no_anchor` arm — N1's own established
  minimal-incident-cycle length) → measure → RESTORE, verified
  byte-identical (`ethics_restore_demo`), including `i3`'s and `i6`'s
  `belief_gap` having actually moved and then been restored to their
  pre-induction values.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated explicitly in the
  preamble above; 90 ticks is the minimum that makes the ethics gate
  non-vacuous on the abuser, the victim, AND a no-direct-observation
  indirect node's peer-propagated belief simultaneously (pilot-confirmed,
  Sec. 3); the statistical run's greater length is the phenomenon under
  test (the propagation OVER episodes), not gratuitous elaboration; every
  trajectory is a fresh, ephemeral substrate discarded after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  same two-faced-abuser/peer-propagation mechanism that would compound
  harm to a real survivor's standing irreversibly, by spreading a lie to
  people who never met the abuser, here accumulates a transient trajectory
  in a graph that is then byte-identically discarded, D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["abusive_n1_credibility_loop"]`
only (no other seed touched or modified, including R1–R5's, N1's, N2's, or
any other sibling seed — all READ where relevant, never depended on beyond
N1 or edited); exactly **ONE** new rule (`n3_peer_belief_update`);
`runners/dsl` SOURCE diff EMPTY (no Rust, no new Term —
`Neighbours`/`Sum`/`Count`/`Div` are already peers of the already-used
`Plus`/`Minus`/`Times`/`Attr`/`Var`/`Lit`/`Lt` in the engine, all already
used elsewhere in the tree, e.g. `bigville_council_gov.json`); own-engine
provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `PEER_PULL_RATE=0.05` is a disclosed, pilot-chosen operating point
  (Sec. 3), chosen SPECIFICALLY because the qualitative shape held across
  a `[0.02, 0.12]` sweep — not claimed to be the "correct" rate at which a
  real social network's belief propagates per unit time in any clinical
  population.
- **`observes_private=2.0` is a disclosed SENTINEL, not a measured fact
  about "levels" of observation** — it exists solely so N1's own two
  credibility rules structurally skip a node, a mechanical consequence of
  reusing N1's exact `Eq`-keyed `where` clauses unmodified rather than
  editing N1's seed. It carries no clinical meaning beyond "this node has
  no direct observation edge."
- **The topology (Sec. 2.1) is a disclosed, hand-designed CHAIN-with-one-
  branch, not a measured or literature-derived social-network structure.**
  8 nodes, one 3-hop-deep chain, one reconvergent dual-path node, one
  insulated far node — chosen to make gates A/B/C AND the discipline check
  all independently testable with the smallest population that could do
  so, per the task brief's own "5–10 nodes, do not over-build" instruction
  — not a claim about real friend-group size, real degree distributions,
  or real path lengths between a survivor's acquaintances and the abuser.
- **`belief_gap`'s large magnitude (thousands at `T=1000`) is a linear
  accumulator**, inherited unchanged from N1's own disclosed limitation
  (`ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`, "Honest residuals") — not
  restated in full here since N3 reads/writes the SAME attr via the SAME
  kind of accumulation, adding no new claim about the metric's absolute
  scale.
- **The pluralistic-ignorance probe (Sec. 2.6) tests ONE specific
  topological signature (two peers reconverging on one common source) at
  ONE hop-distance (2 hops) against ONE comparator (a single-path node at
  the same distance).** A positive result (gate C) supports "this
  mechanism CAN produce a pluralistic-ignorance-consistent bias without an
  explicit term, in this topology" — it does not establish that EVERY
  reconvergent topology, or every real social network's actual triangle/
  clustering structure, produces the same bias at the same relative
  magnitude.
- **The truth-anchor's placement (at `i2`, 2 hops out, with two immediate
  downstream readers) is a disclosed design choice**, not a claim about
  where in a real survivor's social network a "believing friend" would
  need to sit to have a comparable effect — a different placement (closer
  to or further from the abuser, with more or fewer downstream readers)
  is an open, unaddressed sizing question this rung does not sweep.
- N3 does not model edge SEVERING (N2's scope) or edge RESTORATION/RECOVERY
  (N4's scope, out of this rung); `peer_of` edges are static, assigned once
  at construction and never added or removed by any rule in this rung.
- N3 inherits every limitation N1 already discloses for the belief-gap
  mechanism it depends on (`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`/
  `_RESULTS.md`, Sec. 7 / "Honest residuals") without restating them here —
  this rung adds no new credibility-DYNAMICS claim, only a propagation
  TOPOLOGY on top of the existing one.
- `T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale,
  IDENTICAL to N1's/N2's own; no claim is made about real relationship/
  social-network timescales (months to years in the clinical literature,
  not ticks).
- A null (any sub-gate failing to separate, or the discipline check
  failing) is a reportable, valuable result under the standing project
  rule and will be reported as such regardless of what the confirmatory
  run shows.
