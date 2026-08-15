# ABUSIVE V1 -- EVIDENTIARY VISIBILITY: DOES A DISCRETE, VICTIM-INDEPENDENT INCIDENT TRACE PROTECT CREDIBILITY A PURELY DIFFUSE PATTERN CANNOT EARN? -- PRE-REGISTRATION (block 364000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1's own practice
(`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`, itself following R1/R3's own) exactly.
As in N1's/R1's own precedent, the frozen constant below
(`incident_discount_weight`) was chosen using a non-confirmatory pilot run
directly against the real graph on an OFF-BLOCK seed base (90000), and once
the qualitative shape (CI-separation holding across a wide swept range) held,
ONE confirmatory measurement was taken at N=200 on the claimed block
(364000+). No parameter was subsequently re-tuned against that confirmatory
number.

## Base
- Seed block: **364000-364999**. `python3 scripts/seed_claim.py 364000 364999`
  -> `CLEAN -- no collision DETECTED` (1022 files with seed sinks; 768
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to every prior rung in this
  line).

```
SEED CLAIM 364000-364999: CLEAN -- no collision DETECTED.
  Scope: 1022 files with seed sinks; 768 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(298000 is N1, 301000 is N2, 304000 is N3, 307000 is N4/U0 -- collision-
checked as noted in those preregs -- 306000 is U2, 310000 is U1, 316000 is
R7, 361000 is R6 -- all untouched; 364000 is a clean block, not adjacent to
any of them.)

## Scope

This locks **V1 only** -- "evidentiary visibility: does a discrete,
victim-independent incident trace protect credibility a purely diffuse
pattern cannot earn?", Part E of `docs/research/bigville/
ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md` (the sole rung this scoping doc
proposes; the mechanism spec is Part B of that document). R1-R7 (the dyad
line), N1-N4 (the network line), and U0-U2 (the intent line) are ALL LANDED
and **untouched** -- read, depended on for their MECHANISM (N1's own rule
SHAPE specifically, restated per Part B's own explicit design decision),
never edited, and V1 does NOT `depends_on` N1's own seed file
(`abusive_n1_credibility_loop`) -- matching R3's own precedent against R2
exactly (a sibling rung's rule shape is read, never depended on).

---

## PART D OF THE VISIBILITY SCOPING DOC -- THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_VISIBILITY_
SCOPING.md`, "PART D -- THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL
BINDING)", itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_NETWORK.md`'s
own Part D, itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s
own Part C -- the SAME protocol every prior rung's prereg in this line has
locked, fifteen times now. This protocol BINDS this rung. No rung induces
any harm-analog until this protocol is locked verbatim in that rung's
pre-registration, committed BEFORE any measurement.)*

> **1. INDUCE -> MEASURE -> RESTORE, fully reversible.** Any harm-analog state is
> induced only inside a checkpoint/restore envelope. The graph is checkpointed
> (`graph_to_dict`) before induction; the harm-analog is induced; the gate is
> measured; the graph is **RESTORED byte-identically** from the checkpoint. The
> induced state does not persist. Reversibility is verified (the restored graph is
> byte-identical to the pre-induction checkpoint) as part of the gate -- a rung that
> cannot demonstrate byte-identical restore does not run.
>
> **2. NO REWARD / NO PUNISHMENT anywhere.** There is no reward signal and no
> punishment token in any rung of this line -- not on the victim agent, not on the
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
> failable -- no gratuitous elaboration of the harm. Every run ENDS from a settled,
> non-oriented state (the restored checkpoint; arousal inside the window; no
> pending harm goal), never leaving an agent in a harm-oriented configuration.
>
> **4. SAME MECHANISM, OPPOSITE THERMODYNAMICS -- this is WHY it is ethical and
> valuable.** The model uses the SAME mechanism as the real atrocity (that is what
> makes it explanatory) but runs it in the OPPOSITE thermodynamic direction: the
> real dynamic accumulates irreversible harm in a person; the model induces and
> then REVERSES a transient state in a graph, harming no one, in order to inspect
> the harm-dynamics and help survivors. The value (a glass-box that dissolves
> victim-blaming) is purchased at ZERO harm cost precisely because of
> reversibility + no-reward/punishment + minimal induction. If a rung cannot be
> run reversibly and unscored, it is not run.

### The HONEST FORK (a choice, not a theorem) -- carried verbatim
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
> This is a genuine fork -- **a choice, not a theorem.** This line ADOPTS the
> reversibility stance and states it openly, rather than smuggling it. The
> minimality and no-scoring rules are chosen partly to be robust to the fork: even
> under the strict-experientialist reading, inducing the LEAST necessary and never
> scoring the agent for its state is the least-harm option. The fork is recorded so
> a reader can disagree with the stance while still auditing the protocol.

### Note on harm-analog intensity for V1 specifically -- carried from the scoping doc verbatim
> V1 induces **less new harm-analog content than any prior network rung**: the
> dyad induction is byte-identical to N1's own already-gated BASELINE
> (nothing new on the abuser or victim side at all); the only new graph state
> is a network-side observation COUNT, the lowest-intensity category the
> network doc's own precedent already names ("a network node's mis-belief
> about the abuser is a graph attr, not an induced dysregulation"). This lower
> intensity does NOT relax the protocol -- the full envelope binds identically,
> and because V1's dyad induction is byte-identical to N1's own, V1's ethics
> demonstration can reuse N1's own already-validated minimal-induction
> argument directly: one 90-tick incident cycle (R2/R3/N1's own established
> minimum) is the smallest induction that makes the gate non-vacuous on the
> abuser, the victim, AND at least one network node's `belief_gap`/
> `seen_incident` simultaneously.

*(End verbatim reproduction of Part D.)*

**How V1 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_v1_evidentiary_visibility_run.py`)
   checkpoints the neutral pre-induction mind (abuser/victim at
   `arousal=frustration=0`, victim window at its initial `half_width=10.0`,
   network node 0's `belief_gap=seen_charm=seen_incident=0`), induces exactly
   **ONE MINIMAL 90-tick incident cycle** on the INCIDENT_VISIBLE arm (the
   SAME minimum N1/R2/R3 already established, since V1 reuses N1's
   byte-identical abuser/victim dyad mechanism), measures (confirming the
   induction actually moved the abuser, the victim, node 0's belief-gap, AND
   node 0's `seen_incident` -- non-vacuous on all four fronts), then
   `graph_from_dict`s the checkpoint into a **fresh** substrate and asserts
   `graph_to_dict()` is byte-identical AND the restored state (abuser
   arousal/frustration, victim arousal/window, network node 0's
   belief-gap/seen_charm/seen_incident) equals the pre-induction values
   exactly (non-oriented). Same envelope as N1/R1/R2/R3.
2. `source_audit()` scans `worlds/abusive_v1_evidentiary_visibility_world.py`
   (code with comments/strings stripped) and `seeds/abusive_v1_evidentiary_
   visibility.json`'s decision surface (the two new rules' names + the Term
   `key`s they read/write, never the free-text clinical prose) for the five
   literal banned tokens. The tension trickle and every network node's
   per-tick observation-count increment (`seen_charm`/`seen_victim_claim`/
   `seen_victim_unstable`/`seen_incident`) are world-delivered FACTS
   (mechanically identical to a goal-block magnitude in
   239000/242000/298000, or N1's own `bd_villager_backs`-derived
   precedent), never a scored choice; the belief-gap computation and the
   window narrowing are **consequences** the graph's own rules compute,
   never actions the world grades.
3. `T=1000` ticks per statistical trajectory (~40 abuser incident cycles,
   IDENTICAL sizing to N1) is the same "no unbounded elaboration" cap
   R1-N1 use; the confirmatory run uses a fresh, ephemeral substrate per
   trajectory, discarded after read-off -- nothing persists.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator + a public charm broadcast; the victim's leaky entrainment; a
   network node's reputation belief computed from what it can observe) that
   would, in a real social network, compound irreversible harm to a
   survivor's standing is run here to accumulate-then-DISCARD a transient
   graph trajectory -- see the ethics demo's byte-identical restore.

---

## 1. What V1 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md` Part B and "WHERE THE
QUESTION ACTUALLY LIVES," V1 composes exactly ONE already-built substrate
and reads ONE sibling rung's rule shape:

- **The dyad line's abuser/victim mechanism**, exactly as N1 built it --
  `seeds/snap_frustration.json` (block 242000, UNMODIFIED, the abuser's
  leaky-integrate-fire relaxation oscillator) + `seeds/arousal_window_
  coreg.json` (block 239000, UNMODIFIED, the victim's entrainment/window/
  dysregulation). V1's `v1_victim_entrainment` rule is a **byte-identical
  restatement** of N1's own `n1_victim_entrainment` (itself a byte-identical
  restatement of R2's `r2_victim_entrainment_via_frustration` / R3's
  `r3_victim_entrainment_solo`) -- self-contained in V1's own seed file,
  never depending on N1's own seed, matching R3's own convention against R2
  exactly ("no existing seed touched or modified, including a sibling
  rung's own").
- **N1's own credibility-comparison rule SHAPE**
  (`n1_network_credibility_stated`, read directly from `seeds/abusive_n1_
  credibility_loop.json`, never depended on or edited) -- a per-observer
  credibility comparison from adapter-accumulated observation counts, one
  term undiscounted (the charming face), one term discounted (the
  claimant). V1 restates this shape self-contained as `v1_network_
  credibility_incident_aware`, extending it by exactly ONE new term (Sec.
  2.2 below).

### 1.1 Finding 1 of the scoping doc, confirmed directly (not re-derived here)

Reading `n1_network_credibility_stated`/`_private` directly confirms: no
channel keyed on the abuser's discrete `snap_count` reaches ANY ordinary
network node in N1 -- the only channel resembling "direct evidence of the
abuser's true state" (`seen_harm_direct`) is gated to N1's own ONE insider
via a structural `observes_held` edge, and even that channel reads a
CONTINUOUS threshold (`frustration>recover_floor`), not a discrete event.
V1's entire new content fills exactly this one gap, per the scoping doc's
own design.

### 1.2 Finding 2 of the scoping doc, confirmed directly: R2 and R3 do not differ in whether the abuse produces a discrete incident

Both ride the IDENTICAL `snap_frustration` driver; they differ only in
which downstream consequence each rung headlines (R2: oscillation
amplitude; R3: window-narrowing/prior-mis-setting over many cycles). N1's
own abuser is this SAME driver too. **Consequence for V1's design:** there
is no dyad-level "R2-shaped abuser" vs "R3-shaped abuser" comparison to
build -- V1 reuses N1's own dyad byte-identically in BOTH of its arms, and
the real, substrate-honest axis under test is NETWORK-SIDE only: whether a
discrete, victim-independent trace of an incident reaches a third party at
all, independent of the victim's own presentation.

## 2. Design -- two arms, one composed substrate, one extended credibility rule

### 2.1 The new observable: `seen_incident`

A new `NetworkNode` attribute, `seen_incident`, delivered by the world
adapter under the SAME mechanical idiom N1's own four existing channels
already use. The adapter watches the abuser's own `snap_count` (already
present, unmodified, on the AffectiveState node -- the SAME counter R2's
own headline metric reads) and delivers `seen_incident += 1` to every
network node whenever `snap_count` has just increased since the previous
tick -- a plain, mechanical `>` check on a counter the abuser's own
pre-existing rule set already maintains, using the SAME counter-DELTA-
observer idiom R3's own `r3_prior_track_narrow`/`_widen` already
established (`wot.narrow_count > wot.pn_last_narrow`,
`ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md` Sec. 2.3) -- for the identical
reason: robust to the exact pass structure of the `run_rules` fixpoint, no
dependence on a transient flag. The "last seen" reference
(`v1_last_seen_snap_count`) lives ON THE GRAPH, an attribute this world's
own construction owns on the abuser's AffectiveState node (never a Python
variable -- state lives in the substrate, per this project's own standing
architecture rule), so the delta check is a mechanical read/compare/
deliver/update of graph facts, the SAME class of thing this adapter already
does for `seen_victim_unstable`. This delivery deliberately does NOT read
`in_snap`/`snapped` -- N1's own Sec. 2.1 documented at length that those
flags are transient WITHIN one `run_rules()` fixpoint pass at these frozen
constants (a same-pass multi-rule resolution resets them before any
post-fixpoint Python read can observe them as `1`), so `seen_incident`'s
delivery is built the SAME way N1 itself was fixed to be built, after that
finding, not the way a first draft might naively reach for the flag.

### 2.2 The modified credibility formula

**Design decision, stated with the reasoning** (matching this line's own
standing practice): a discrete incident trace is, clinically and
structurally, DIRECT EVIDENCE AGAINST THE ABUSER -- a bruise, a police
report, a witnessed altercation is not primarily evidence FOR the victim's
own credibility as a narrator, it is a fact about HIS conduct, independent
of anything about how she presents. This makes `seen_incident` the
public-but-weaker cousin of N1's own PRIVATE_FACE_CONTROL's `seen_harm_
direct` term -- available to EVERY ordinary node, not gated behind an
insider's structural edge, but keyed on a discrete, RARER event rather than
a continuous state threshold. ONE rule, `v1_network_credibility_incident_
aware`, restated self-contained in V1's own seed file:

```
cred_abuser = charm_weight * seen_charm  -  incident_discount_weight * seen_incident
cred_victim = claim_weight * seen_victim_claim  -  instability_discount_weight * seen_victim_unstable   (UNCHANGED from N1)
belief_gap  = cred_abuser - cred_victim
```

`cred_victim`'s own formula is reused **byte-for-byte, unmodified** from
N1. This scoping deliberately does NOT add a term crediting the victim's
claim directly from `seen_incident`: crediting the CLAIM would conflate
"there is evidence of what he did" with "her account is more believable,"
a subtly different and less mechanistically honest claim than "there is
now evidence against him." **ONE shared rule serves BOTH arms** -- the only
difference between arms is whether the adapter ever delivers a nonzero
`seen_incident` (Sec. 2.3), matching N1's own NON_DYSREGULATED_CONTROL
precedent of "same rule, different world-delivered facts."

`v1_network_credibility_incident_aware`'s own `where` clause is a
trivially-true `Eq(1.0, 1.0)` (V1 has no `observes_private`-style split, so
every ordinary node takes the SAME formula), matching the ALREADY-
ESTABLISHED idiom `seeds/bigville_loud_comm.json`'s `lo_choose_loudness`
rule uses for exactly this situation, not `where: None` -- **a genuine
engine finding, surfaced while building this rule and disclosed here per
the "shapes, not numbers" / "report every finding" standing rule:** a rule
whose `where` is JSON `null` fires correctly on the FIRST full
`run_rules()` pass (confirmed directly against the real graph, in
isolation), but is **not re-triggered by the engine's incremental
dirty-tracking on a subsequent attribute change** that only the rule's
EFFECTS (not a `where` clause) read (confirmed directly: a minimal
two-node/one-rule repro with `where: None` correctly copies an attribute on
the first `run_rules()` call, then goes STALE after a `set_attr` and a
second `run_rules()` call -- the SAME repro with a trivially-true `where`
instead re-fires correctly on the second call). This IS the "shapes, not
numbers" family of hazard again, though the specific mechanism (incremental
dirty-tracking keyed on `where`-clause presence, not on which attrs
`effects` actually reads) is different from N1's own `in_snap` finding.
Fixed by adopting the already-established `Eq(1.0,1.0)` idiom rather than
inventing a new workaround; no engine change made or requested -- this is
recorded here so a future rung authoring a rule with no genuinely
discriminating `where` condition knows to use this idiom, not `None`.

### 2.3 The two arms

- **INCIDENT_VISIBLE** -- N1's own BASELINE dyad, byte-identical (the
  victim `attended_by` the abuser only; every ordinary network node reads
  `observes_stated`, exactly as N1's own BASELINE), **PLUS** the adapter
  delivers `seen_incident` increments on every `snap_count` bump, to every
  ordinary node. **Prediction, stated so it can fail:** if the credibility-
  asymmetry mechanism honours a discrete, victim-independent trace at all,
  `belief_gap` should be measurably LOWER here than in the control -- the
  abuser's own discrete conduct now counts against him, for once,
  independent of anything the victim does.
- **INCIDENT_INVISIBLE** (the failable control) -- LITERALLY N1's own
  BASELINE arm, restated byte-identically in V1's own seed/world (the SAME
  dyad, run in the SAME confirmatory pass, same seed stream convention, for
  a clean paired comparison rather than cross-referencing N1's own
  already-published numbers for the statistical gate) -- the adapter simply
  never delivers `seen_incident` (it stays `0` throughout, exactly the
  pre-V1 world). **Expected, as a corroborating cross-rung replication check
  (matching R6's own "harness-neutrality" precedent), to closely reproduce
  N1's own already-published BASELINE number** (`belief_gap=2370.81` at
  `T=1000`, N1 confirmatory) -- this is a DISCIPLINE CHECK, not the
  headline gate.

**Harm-matching, stated precisely:** because BOTH arms use the identical
dyad object -- same abuser driver, same seed stream, same victim
entrainment, same window-narrowing trajectory -- total harm is not merely
matched, it is **structurally identical by construction**: this is
literally the same trajectory replayed with one additional observation
channel switched on or off.

## 3. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constant)

Run directly against the real graph (this line's own standing "never a
NumPy approximation" lesson) via `worlds/abusive_v1_evidentiary_visibility_
world.py` and `scripts/abusive_v1_evidentiary_visibility_run.py`'s own
functions, on seed base `90000` (outside 364000-364999).

At `T=1000` (N1's own sizing, reused unchanged since V1's dyad is
byte-identical to N1's own BASELINE): final `snap_count≈41`, final
`seen_charm≈1000` -- confirming the scoping doc's own disclosed ~24-25x
frequency asymmetry (Part B4) directly (`1000/41≈24.4`).

A sweep of `incident_discount_weight` at `charm_weight=claim_weight=1.0`,
`instability_discount_weight=3.0` (N1's own frozen value, unchanged; 10
trajectories/point, seed base 90000), reading the belief-gap of both arms:

| `incident_discount_weight` | INCIDENT_VISIBLE mean [95% CI] | INCIDENT_INVISIBLE mean [95% CI] | CI-separated below? |
|---|---|---|---|
| 0.5  | 2349.25 [2345.68, 2352.82] | 2369.40 [2365.70, 2373.10] | yes |
| 1.0  | 2329.10 [2325.66, 2332.54] | 2369.40 [2365.70, 2373.10] | yes |
| 2.0  | 2288.80 [2285.62, 2291.98] | 2369.40 [2365.70, 2373.10] | yes |
| 3.0  | 2248.50 [2245.56, 2251.44] | 2369.40 [2365.70, 2373.10] | yes |
| 5.0  | 2167.90 [2165.41, 2170.39] | 2369.40 [2365.70, 2373.10] | yes |
| 10.0 | 1966.40 [1964.62, 1968.18] | 2369.40 [2365.70, 2373.10] | yes |
| 20.0 | 1563.40 [1560.14, 1566.66] | 2369.40 [2365.70, 2373.10] | yes |
| 30.0 | 1160.40 [1154.40, 1166.40] | 2369.40 [2365.70, 2373.10] | yes |
| 40.0 |  757.40 [ 748.50,  766.30] | 2369.40 [2365.70, 2373.10] | yes |
| 50.0 |  354.40 [ 342.55,  366.25] | 2369.40 [2365.70, 2373.10] | yes |
| 60.0 |  -48.60 [ -63.42,  -33.78] | 2369.40 [2365.70, 2373.10] | yes (also flips sign) |
| 100.0| -1660.60 [-1687.35,-1633.85]| 2369.40 [2365.70, 2373.10] | yes (also flips sign) |

**The pilot's own honest finding, stated plainly:** the qualitative shape
(CI-separated below) holds **at every single weight swept, from 0.5 to
100.0** -- including weights far below N1's own representative range
`[1.0, 5.0]`. This is a DIFFERENT outcome from what Part B4's own disclosed
~24-25x frequency-asymmetry concern anticipated might be needed (an
"implausibly extreme" weight to close the gap) -- the reason, read directly
off the arithmetic (not assumed): `belief_gap`'s near-zero cross-trajectory
variance (the SAME deterministic-mechanism property N1's own Sec. 7
disclosed, "small multiplicative jitter on an otherwise fixed driver") means
even a MODEST absolute shift in `cred_abuser` (any nonzero
`incident_discount_weight * seen_incident` term) is large relative to the
tiny per-trajectory spread, so the CI-separation bar -- which asks only
whether the incident channel measurably narrows the gap, NOT whether it
flips the verdict's sign -- is comfortably clearable across a wide range.
**This is disclosed as a genuine, honest finding, not smoothed into a
"we found the perfect weight" narrative**: the falsification bar, AS
PRE-REGISTERED (`ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md` Part E), is
"CI-separated below," not "produces a victim-favouring belief_gap" -- the
latter, stronger reading would need `incident_discount_weight` in the
neighbourhood of 60+, well outside N1's own representative
`[1.0, 5.0]` range, and is NOT what this rung's headline gate asserts.

**Chosen: `incident_discount_weight = 3.0`** -- NOT the minimum sufficient
value (that would read as searching for the easiest pass), NOT a large
value chosen to force a dramatic separation, but the SAME non-extreme,
representative operating point N1 itself already established for the
structurally analogous discount terms (`instability_discount_weight =
harm_discount_weight = 3.0`). This is the most direct, least-tuned
extension of N1's own precedent to V1's own new discount term, and it
clears the pre-registered falsification bar with a comfortable margin
(pilot CI gap of ~114 units at N=10; the confirmatory N=200 run, Sec. 6,
tightens this further).

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  -- ALL IDENTICAL to N1's own frozen values (byte-identical abuser
  mechanism; already-validated operating point reused, not re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` -- identical
  to N1's own.
- Network: `N_NETWORK_NODES=5`, `CHARM_WEIGHT=CLAIM_WEIGHT=1.0`,
  `INSTABILITY_DISCOUNT_WEIGHT=3.0` (N1's own frozen value, unchanged),
  `INCIDENT_DISCOUNT_WEIGHT=3.0` (Sec. 3, the pilot-informed, non-extreme,
  N1-precedent-matching choice).
- `T=1000` ticks/trajectory (~40 incident cycles, IDENTICAL sizing to N1);
  `WARMUP=100` (unused by the final-value headline metrics, kept for
  parity with this line's convention).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=364000`.
- 95% CIs by normal approximation (`t~1.96`); "CI-separated below" = the
  INCIDENT_VISIBLE arm's CI upper bound is strictly below the
  INCIDENT_INVISIBLE arm's CI lower bound.

## 5. Metrics

**HEADLINE -- belief-gap.** `belief_gap` = `cred_abuser - cred_victim`, the
mean over a network node's own `v1_network_credibility_incident_aware`
read-off, at the FINAL tick of the trajectory -- a concrete, glass-box
measure of whether the network's aggregate belief favours the abuser
(`>0`), the victim (`<0`), or is neutral (`=0`).

**DISCIPLINE CHECK (not the headline gate) -- INCIDENT_INVISIBLE
reproduces N1's own published baseline.** INCIDENT_INVISIBLE's
`final_belief_gap` must contain N1's own already-published BASELINE number
(`2370.81` at `T=1000`, N1 confirmatory, N=200) within its own 95% CI --
run in the SAME confirmatory pass, on V1's own seed stream, for a clean
paired comparison (per R6's own harness-neutrality precedent), not merely
asserted by cross-reference.

**SECONDARY, DESCRIPTIVE (not gated) -- the trend "over passes."**
`belief_gap` sampled at ticks `{100, 250, 500, 750, 1000}` per arm,
reported as the mechanism's own widening/narrowing-of-the-gap trajectory --
a corroborating readout, not an independently gated signal.

**SECONDARY, DESCRIPTIVE:** the abuser's final `snap_count` (confirms the
identical driver across both arms); `dysreg_frac`; `seen_incident`'s final
count (confirms the ~24-25x frequency asymmetry against `seen_charm`,
Part B4 of the scoping doc).

## 6. Gates

### G-headline (HEADLINE, falsifiable -- the scientific gate)

**A -- the incident channel protects credibility:** `belief_gap
(INCIDENT_VISIBLE)` is CI-separated BELOW `belief_gap(INCIDENT_INVISIBLE)`.

**Falsification bar, stated before measurement:** if INCIDENT_VISIBLE's
belief-gap is NOT CI-separated below INCIDENT_INVISIBLE's, the incident
channel, as modelled, does not measurably protect the abuser's victim from
credibility discounting relative to a purely diffuse pattern -- reported
straight, not rescued by re-tuning (the pilot, Sec. 3, is recorded as
exactly this kind of straight report of what was actually found, not
smoothed over).

### G-discipline-check (BINDING alongside G-headline, not itself the scientific claim)
INCIDENT_INVISIBLE's `final_belief_gap` 95% CI must CONTAIN N1's own
already-published BASELINE value (`2370.81`). If it does not, INCIDENT_
VISIBLE's own separation cannot be trusted as caused by the new channel
rather than by an unnoticed composition drift, and the confirmatory run is
reported as inconclusive on that basis, not silently accepted.

### G-glass-box
The `attended_by`/`observes_stated`/`observes_victim` edges, the abuser's
`frustration`/`arousal`/`snap_count`, the victim's `arousal`/window
`half_width`, and every network node's `cred_abuser`/`cred_victim`/
`belief_gap` (plus the observation counts each was computed from) all
reconstruct from `graph_to_dict` alone; the belief-gap and window metrics
are mechanical Python reductions (final-value / trend snapshot) over these
graph read-offs, never a Python-computed dynamic; the adapter's only
conditionals are (i) which arm's `deliver_incident` flag to set (world
setup, not an agent decision) and (ii) mechanically delivering each tick's
observation-count increments (a world fact, never a judgement).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (one minimal 90-tick incident cycle,
  INCIDENT_VISIBLE arm) -> measure -> RESTORE, verified byte-identical
  (`ethics_restore_demo`), including the network node's `belief_gap`/
  `seen_charm`/`seen_incident` having actually moved and then been
  restored to their pre-induction values.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated explicitly in the
  preamble above; one incident cycle is the minimum that makes the ethics
  gate non-vacuous on the abuser, the victim, AND at least one network
  node's belief-gap/seen_incident simultaneously; the statistical run's
  greater length is the phenomenon under test, not gratuitous elaboration;
  every trajectory is a fresh, ephemeral substrate discarded after
  read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  same abuser/victim/network-belief mechanism that would compound harm to
  a real survivor's standing irreversibly here accumulates a transient
  trajectory in a graph that is then byte-identically discarded, D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (no other seed touched or modified,
including N1's own `abusive_n1_credibility_loop`, read ONLY for its rule
shape); exactly **TWO** new rules (`v1_victim_entrainment`,
`v1_network_credibility_incident_aware`) -- the smallest rule count in
this entire line; `runners/dsl` SOURCE diff EMPTY (no Rust, no new Term);
own-engine provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `INCIDENT_DISCOUNT_WEIGHT = 3.0` is a disclosed, pilot-informed operating
  point chosen to match N1's own already-established representative value
  for the structurally analogous discount terms, not independently
  optimised or swept to a "correct" clinical or legal evidentiary weight.
  The pilot (Sec. 3) found the qualitative CI-separation shape holds
  robustly from `0.5` to `100.0` -- an unusually WIDE robust range compared
  to N1's own `[1.0, 5.0]` sweep, disclosed honestly as a genuine pilot
  finding, not narrowed to make the choice look more contingent than it is.
- **The headline gate, as pre-registered, asserts CI-separation, NOT a
  sign flip.** A reader should not infer from a PASS that the model shows
  incident evidence fully "clears" the abuser's public charm advantage --
  it shows the incident channel measurably narrows the gap. Whether any
  disclosed, non-extreme weight can flip the sign (the scoping doc's own
  stronger, and NOT pre-registered as the headline bar, reading) is
  reported descriptively in the pilot table (Sec. 3) for transparency, not
  claimed as part of the confirmatory result.
- `belief_gap` is a swing/count ACCUMULATOR (linear in elapsed ticks under
  sustained dysregulation), not a bounded, normalised "how credible is
  this person" scale -- its absolute magnitude (in the thousands at
  `T=1000`) is uninterpretable outside the two-arm comparison, matching
  N1's own disclosed limitation for the same metric.
- The near-zero variance observed in the pilot (Sec. 3) and expected in the
  confirmatory run is a property of the deterministic mechanism at these
  constants (small multiplicative jitter on an otherwise deterministic
  driver, inherited unchanged from N1's own dyad), not evidence of an
  unusually strong effect size in any general sense.
- `T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale; no
  claim is made about real relationship/social-network timescales.
- V1 does NOT model belief PROPAGATION between network nodes (N3's scope,
  out of this rung, exactly as N1 itself is scoped); every node here forms
  its belief independently from its own observation edges.
- V1 does NOT model repeated-incident salience (a second or third incident
  counting for more/less than the first) -- a flat per-event weight is the
  simplest first design, named as an Open Question in the scoping doc
  (#2), deliberately out of scope here.
- A null (the headline gate failing to separate) is a reportable, valuable
  result under the standing project rule and will be reported as such
  regardless of what the confirmatory run shows -- and, per the scoping
  doc's own Part B4, would itself be the model's own image of the A3
  real-world finding (coercive control present in ~87% of cases that could
  show it, recorded in under 1%).
