# ABUSIVE U0 — GENUINE INTENT: AN ARGMAX-SELECTED CONCEALMENT, SCORED AGAINST A DECLARED GOAL — PRE-REGISTRATION (block 307000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1's own practice
(`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`) exactly. As in N1's own precedent,
the frozen constants below were chosen using a non-confirmatory pilot run
directly against the real graph on an OFF-BLOCK seed base (90000), and once
the qualitative shape (the scored arm's stated_charm selection correlating
with frustration; the goal-blind arm's not) held, ONE confirmatory
measurement is taken at N=200 on the claimed block (307000+). No parameter is
subsequently re-tuned against that confirmatory number.

## Base
- Seed block: **307000–307999**. `python3 scripts/seed_claim.py 307000 307999`
  → `CLEAN — no collision DETECTED` (1016 files with seed sinks; 751
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1–R5/N1–N3's own).

```
SEED CLAIM 307000-307999: CLEAN -- no collision DETECTED.
  Scope: 1016 files with seed sinks; 751 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## Scope

This locks **U0 only** — "genuine intent: an Argmax-selected concealment,
scored against a declared goal" (the positive control), Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`
("### U0"). R1–R5 (the dyad line) and N1–N3 (the network line, all landed)
are **untouched** — read and depended on for their MECHANISM (N1's rules are
RESTATED byte-identically, never edited; N1's seed FILE is never depended on
or modified — see the composition note in Sec. 2 below), never edited. U1/U2
(the two no-divergence, intent-free alternatives named in the same scoping
doc) are **out of scope** and untouched by this rung — a sibling agent may
build them separately.

---

## PART D OF THE UNINTENTIONAL SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_
UNINTENTIONAL_SCOPING.md`, "PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM;
STILL BINDING)", itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_NETWORK.
md`'s own Part D, itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.
md`'s Part C — the SAME protocol R1–R5's and N1's own preregs locked. This
protocol BINDS this rung. No rung induces any harm-analog until this protocol
is locked verbatim in that rung's pre-registration, committed BEFORE any
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

*(End verbatim reproduction of Part D.)*

### Note on the Argmax's value comparison vs. a reward signal — READ CAREFULLY

U0's central new mechanism — `u0_choose` — computes an `Argmax` over two
candidate `Appraisal`s' `total_value` (from `core_emotions`'
`em_happiness`/`em_fulfilment_value`/`em_total_value`, UNMODIFIED). This is
**a VALUE COMPARISON BETWEEN TWO CANDIDATE PRESENTATIONS, not a reward
applied to the agent for its choice.** The distinction, stated precisely
(per the task brief's own instruction to keep this straight, and per R4's
own precedent for its structurally identical `r4_choose`):

- A **reward signal** would be a scalar fed back INTO the agent as a
  consequence of WHICH candidate it picked (a shaping token, gradient, or
  reinforcement update contingent on the choice's outcome) — this line
  contains none, anywhere, and the source audit below checks for the
  literal banned tokens.
- The Argmax here computes which of two ALREADY-VALUED candidates has the
  higher `total_value`, using the SAME value-economy rules
  (`em_happiness`/`em_total_value`) every other Argmax-driven choice in this
  substrate already uses — `mm_choose` (`marshmallow_delay.json`, block
  240000) and `r4_choose` (`abusive_r4_learned_helplessness.json`, block
  292000), both already source-audited clean under this exact protocol. The
  candidates' `individual_benefit`/`individual_cost` are DECLARED CONSTANTS
  (`concealment_benefit`/`honesty_benefit`/`suspicion_cost_scale`) or a
  simple function of the abuser's own pre-existing `frustration` attr — no
  value is fed back into the abuser as a consequence of ITS PAST choices;
  the comparison is stateless across ticks (nothing here is a
  learned/updated preference, unlike, e.g., R4's own `contingency_prior`
  EMA, which this rung does not use).
- `source_audit()` (Sec. 6 below) scans the WORLD ADAPTER and the SEED's
  decision surface (rule names + attr `key`s, never the free-text
  provenance prose) for the five literal banned tokens
  (`reward_signal`/`punish`/`reinforce`/`backprop`/`gradient`); their
  absence is the gate, exactly as R4's own audit already established for
  the structurally identical `r4_choose`.

---

**How U0 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_u0_intent_run.py`) checkpoints
   the neutral pre-induction mind (abuser at `arousal=frustration=
   stated_charm=0`, the Argmax's own `chosen_action` at its pre-induction
   value, victim at `arousal=0`/window `half_width=10.0`, network node 0's
   `belief_gap=seen_charm=0`), induces exactly **ONE MINIMAL 90-tick
   incident cycle** (the SAME minimum N1/R2/R3 already established, since
   U0 reuses their byte-identical abuser/victim dyad mechanism) on the
   SCORED arm, measures (confirming the induction actually moved the
   abuser, the victim, at least one network node's belief-gap, AND that the
   Argmax's own choice was genuinely EXERCISED — both candidates were
   selected at least once somewhere during the 90 ticks, not merely a
   static default — non-vacuous on all four fronts), then `graph_from_dict`s
   the checkpoint into a **fresh** substrate and asserts `graph_to_dict()`
   is byte-identical AND the restored state equals the pre-induction values
   exactly (non-oriented). Same envelope as R1–R5/N1.
2. `source_audit()` scans `worlds/abusive_u0_intent_world.py` (code with
   comments/strings stripped) and `seeds/abusive_u0_intent.json`'s decision
   surface (the seven new rules' names + the Term `key`s they read/write,
   never the free-text clinical prose) for the five literal banned tokens.
   The abuser's tension trickle and every network node's per-tick
   observation-count increment are world-delivered FACTS (mechanically
   identical to N1's own), never a scored choice; the belief-gap
   computation, window narrowing, both candidates' valuation, and the
   Argmax's own choice are **consequences** the graph's own rules compute,
   not actions the world grades — see the note above for why the Argmax
   itself is not a reward signal.
3. `T=1000` ticks per statistical trajectory (~40 abuser incident cycles,
   IDENTICAL sizing to N1's/R3's own) is the same "no unbounded
   elaboration" cap R1–R3/N1 use; the confirmatory run uses a fresh,
   ephemeral substrate per trajectory, discarded after read-off — nothing
   persists.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator + a genuinely goal-scored presentation choice; the victim's
   leaky entrainment; a network node's reputation belief computed from what
   it can observe) that would, in a real social network, compound
   irreversible harm to a survivor's standing is run here to
   accumulate-then-DISCARD a transient graph trajectory — see the ethics
   demo's byte-identical restore.

---

## 1. What this rung is testing

Per `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`'s own Part E
correction: N1's `n1_abuser_stated_charm` is a fixed, always-on divergence
the RUNG'S BUILDER authored, not a divergence the agent SELECTS at runtime —
it has no `Appraisal`, no `Argmax`, no evaluation of candidate presentations
against a goal. **U0 supplies the missing positive-intent comparison
condition**: a genuine, glass-box, `Argmax`-scored choice between concealing
(presenting charm regardless of true state) and disclosing (presenting the
true state, at a cost that scales with how much there is to conceal). If
this rung's headline gate passes, the line finally has an honest example of
what INTENT actually looks like as graph data, against which the sibling
no-intent rungs (U1/U2, out of scope here) can be meaningfully compared —
without U0, "U1/U2 reproduce the loop" would only show the pattern doesn't
need the STRUCTURE N1 happened to use, never that it doesn't need INTENT,
because N1 was never actually a positive example of intent to begin with.

## 2. Design — composition note (a deviation from the task brief's literal suggestion, and why)

The task brief's own restatement suggested `depends_on: ["abusive_n1_
credibility_loop", "core_emotions", ...]`, following N2's/N3's own
precedent of depending on N1 directly rather than restating its rules. This
rung **deviates from that literal suggestion, deliberately, and states why**:
N2/N3 only ever ADD rules on top of N1's — they never need to REMOVE one.
U0's own design (`ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`, "###
U0") is explicit that it **replaces** `n1_abuser_stated_charm`, not
augments it ("each rung replaces (not augments) N1's one deliberate-
construct rule with its own construction"). If U0 depended on N1's seed
FILE directly, `load_seed_manifest` would install `n1_abuser_stated_charm`
(which unconditionally sets `AffectiveState.stated_charm` every tick from
one formula) ALONGSIDE this rung's own `u0_apply_presentation_choice`
(which unconditionally sets the SAME attr every tick from a DIFFERENT
formula, the Argmax's decision) — two rules racing to decide one attr every
`run_rules()` sweep, at the SAME order slot if left unresolved, is not a
stable composition (each rule's own value differs from the other's,
regardless of order, so the fixpoint never settles on one value without
one of them being suppressed). **The clean resolution, matching N1's OWN
established convention exactly** ("R3 restated R2's own rule rather than
depending on it"; "N1 ... restated self-contained in N1's own seed file
rather than depending on R2's or R3's seed"): `seeds/abusive_u0_intent.json`
**self-contained restates** N1's other three rules byte-identically
(`u0_victim_entrainment`, `u0_network_credibility_stated`,
`u0_network_credibility_private` — SAME match/where/effects as N1's
`n1_victim_entrainment`/`n1_network_credibility_stated`/`n1_network_
credibility_private`, renamed only) and `depends_on: ["snap_frustration",
"arousal_window_coreg", "core_emotions"]` — N1's OWN dependency list, minus
N1 itself, plus `core_emotions` for the Argmax template. U0's own seed file
never touches or depends on `abusive_n1_credibility_loop.json`; N1 remains
completely untouched, exactly as the constraint requires.

## 3. Design — the Argmax mechanism (block 240000's template, reused verbatim)

`seeds/abusive_u0_intent.json` adds, on top of the three restated N1 rules:

- **`u0_appraise_charm`** — the `present_charm` candidate (`action=1.0`):
  `individual_benefit = concealment_benefit` (a declared constant, read off
  a `PresentationDecision` node); `individual_cost = 0`.
- **`u0_appraise_true_state`** — the `present_true_state` candidate
  (`action=0.0`): `individual_benefit = honesty_benefit` (a declared
  constant); `individual_cost = suspicion_cost_scale * frustration` — the
  cost of presenting truthfully SCALES WITH the abuser's TRUE,
  already-existing `frustration` attr (`snap_frustration`, block 242000,
  UNMODIFIED).
- **`u0_choose`** — the decision: `PresentationDecision.chosen_action` =
  the `action` of whichever candidate `Appraisal` has the greatest
  `total_value` (`em_happiness`/`em_fulfilment_value`/`em_total_value`,
  `core_emotions` block 204000, UNMODIFIED). Structurally IDENTICAL to
  `mm_choose`/`r4_choose`.
- **`u0_apply_presentation_choice`** — copies `dec.chosen_action` onto
  `AffectiveState.stated_charm`, the SAME attr N1's own rule wrote, so
  every downstream rule (the two restated credibility rules) and the world
  adapter's `seen_charm` bookkeeping are UNCHANGED from N1's own
  convention — only HOW `stated_charm` is decided differs.

`honesty_benefit > concealment_benefit` is REQUIRED for a genuine crossover
to exist: at `frustration=0`, `present_true_state`'s value
(`honesty_benefit − 0`) must exceed `present_charm`'s
(`concealment_benefit − 0`) so honesty wins when there is nothing to
conceal; as frustration rises, `suspicion_cost_scale·frustration` erodes
`present_true_state`'s value until `present_charm` overtakes it at
`frustration* = (honesty_benefit − concealment_benefit) / suspicion_cost_
scale` — the crossover point, pilot-chosen (Sec. 4) to fall inside the
abuser's genuinely observed frustration range.

**Node wiring** (matching the `marshmallow_delay.json`/`abusive_r4_
learned_helplessness.json` template exactly): one `EmotionHub` per abuser,
linked `-has_emotion_params-> HeldEmotionParams` (`enabled=1.0`,
`w_supergraph=0.0` — every other `core_emotions` channel held neutral,
matching R4's own `EP_DEFAULTS`), `-has_presentation_decision->
PresentationDecision` (the three declared constants + `chosen_action`),
`-has_affective_state-> AffectiveState` (the SAME node the abuser `Agent`
already carries, via a second incoming edge — `u0_appraise_true_state`
reads its `frustration`), and `-has_appraisal->`/`-has_candidate->` to
BOTH candidate `Appraisal` nodes (dual edges, matching R4's/marshmallow's
own convention exactly — `has_appraisal` lets `core_emotions` score the
candidate; `has_candidate` lets the Argmax select over it).

## 4. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph, via `worlds/abusive_u0_intent_world.py`
and `scripts/abusive_u0_intent_run.py`'s `run_arm()`, on seed base `90000`
(outside 307000–307999), N=30 per arm, T=1000:

| | SCORED | GOAL_BLIND |
|---|---|---|
| `r` (Pearson, frustration vs. stated_charm, per-trajectory, mean [95% CI]) | 0.7624 [0.7614, 0.7635] | undefined (100% degenerate) |
| `frac_degenerate` (constant stated_charm within a trajectory) | 0.0 | **1.0** |
| `stated_charm` mean (fraction of ticks concealment chosen) | 0.830 [0.829, 0.831] | 1.0 constant |
| final `belief_gap` (mean [95% CI]) | 2275.6 [2270.8, 2280.4] | 2445.5 [2441.9, 2449.1] |

A sweep of `concealment_benefit`/`honesty_benefit`/`suspicion_cost_scale`
directly against the pilot found `concealment_benefit=2.0`,
`honesty_benefit=5.0`, `suspicion_cost_scale=0.10` (crossover
`frustration*=30`, inside the abuser's observed range of roughly
`[1, 100]` at these frozen dyad constants) produces a clean, stable, strong
POSITIVE correlation in the scored arm (`r≈0.76` across ten spot-checked
seeds at N=1 each, sd≈0.004 across N=30) — meaningful variance in
`stated_charm` (83% concealed, 17% disclosed, not a degenerate 0%/100%
split), confirming a genuine crossover is being exercised, not a
one-sided default.

**The goal-blind arm's degeneracy is analytically guaranteed, not merely
empirically observed, and this is disclosed rather than treated as
surprising:** with `concealment_benefit=honesty_benefit=suspicion_cost_
scale=0`, `present_charm`'s value is `0 − 0 = 0` and `present_true_state`'s
value is `0 − (0·frustration) = 0` for ANY finite `frustration` (IEEE 754:
`0.0 * x = 0.0` exactly, no floating-point drift) — an EXACT tie every
single tick, structurally, by construction. The engine's own `Argmax` term
resolves an exact tie by keeping the FIRST candidate encountered in
`Neighbours(hub, has_candidate)` iteration order (confirmed by reading
`runners/dsl/src/term.rs`'s `argmin_or_argmax_over`, not assumed); since
`present_charm` is wired first in the world adapter, EVERY goal-blind
trajectory converges on `stated_charm≡1.0` (charm, constantly) —
disclosed explicitly, matching the design doc's own anticipation
("at most tracking whatever the Argmax's tie-break default is, not the
abuser's true state"). A CONSTANT series cannot correlate with anything
(Pearson `r` is mathematically undefined at zero variance); this is the
STRONGEST possible form of "does not correlate with frustration," because
it is a formal guarantee from the computation's own structure
(`individual_cost` is identically `0` regardless of `frustration`), not
noise cancellation across a genuinely varying signal.

## 5. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  — ALL IDENTICAL to N1's/R2's/R3's own frozen values (byte-identical
  abuser mechanism; already-validated operating point reused, not
  re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` — identical
  to N1's/R2's/R3's own.
- Network: `N_NETWORK_NODES=5` (all `observes_stated`, matching N1's own
  BASELINE topology — U0 does not re-exercise N1's own private-face/
  non-dysregulated controls), `CHARM_WEIGHT=CLAIM_WEIGHT=1.0`,
  `INSTABILITY_DISCOUNT_WEIGHT=3.0` — identical to N1's own.
- **U0-specific (pilot-chosen, Sec. 4): `CONCEALMENT_BENEFIT=2.0`,
  `HONESTY_BENEFIT=5.0`, `SUSPICION_COST_SCALE=0.10`** (scored arm).
  Goal-blind arm: all three `=0.0`.
- `T=1000` ticks/trajectory (~40 incident cycles, IDENTICAL sizing to
  N1/R3); `WARMUP=100` (unused by the final-value headline metrics, kept
  for parity with R1–R5/N1's own convention).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=307000`.
- 95% CIs by normal approximation (`t≈1.96`).

## 6. Metrics

**HEADLINE — the frustration/concealment correlation.** Per trajectory: the
plain population Pearson correlation coefficient between the abuser's true
`frustration` and its `stated_charm` (1.0=concealed/charm, 0.0=disclosed/
true state), sampled at EVERY tick over the T=1000-tick trajectory — a
concrete, glass-box-computable measure directly reconstructable from the
per-tick log (`abuser_frustration`/`abuser_stated_charm`, both graph
read-offs). A trajectory whose `stated_charm` sequence has zero variance
(constant throughout) is reported as **degenerate** (`r` undefined,
`frac_degenerate` tracked separately per arm) rather than silently coerced
to any numeric value. Aggregated: mean `r` [95% CI] over the
NON-degenerate trajectories in an arm (N=200 confirmatory).

**HEADLINE, secondary — final `belief_gap`.** The mean, over the network's
five nodes, of `cred_abuser − cred_victim` (the SAME formula/rule N1 uses,
restated byte-identically) at the FINAL tick — reported and compared
**informationally, NON-GATING**, against N1's own already-landed headline
number (`2370.81` at `T=1000`, `ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`).
Pre-registered as an open, honestly-either-way comparison (PREREG Sec. 6
falsification bar does not gate on this): a real, goal-directed concealer
that only conceals when frustration is high LEAKS true information on
low-frustration ticks N1's blanket broadcast never did, so U0's `belief_gap`
coming out SMALLER than N1's is a legitimate, informative, NON-FAILING
result, to be reported honestly whichever way it goes.

## 7. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, BOTH sub-gates must pass)

**A — the scored arm correlates:** the scored arm's mean `r` 95% CI lower
bound is strictly `> 0` (CI-separated above zero — the Argmax's selection
genuinely, positively tracks the abuser's true frustration).

**B — the goal-blind control does not correlate (FAILABLE):** EITHER (i)
`frac_degenerate == 1.0` (every trajectory's `stated_charm` sequence was
constant — the STRONGEST form of "does not correlate," per Sec. 4's
analytic guarantee) OR, if some trajectories are non-degenerate, (ii) the
goal-blind arm's mean `r` 95% CI straddles 0 (`ci_lo ≤ 0 ≤ ci_hi` — no
reliable correlation in either direction).

**Falsification bar, stated before measurement:** if the scored arm's `r`
CI does NOT clear zero (the Argmax fails to track frustration even with
nonzero incentives), OR if the goal-blind arm shows a reliable nonzero
correlation (CI-separated from zero in either direction, on the
non-degenerate trajectories), the Argmax has degenerated into another
disguised unconditional rule and the "this is a genuine intent model" claim
fails — reported straight, not rescued by re-tuning.

### G-glass-box
The `has_candidate`/`has_appraisal`/`has_presentation_decision` edges, both
candidates' `individual_benefit`/`individual_cost`/`total_value`,
`PresentationDecision.chosen_action`, the abuser's `frustration`/
`stated_charm`, and every network node's `cred_abuser`/`cred_victim`/
`belief_gap` all reconstruct from `graph_to_dict` alone; the correlation
and belief-gap metrics are mechanical Python reductions (Pearson
correlation / final-value snapshot) over these graph read-offs, never a
Python-computed dynamic; the adapter's only conditionals are (i) which
arm's three Argmax constants to set (world setup, not an agent decision)
and (ii) mechanically delivering each tick's observation-count increments
(a world fact, never a judgement).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (one minimal 90-tick incident cycle, SCORED arm)
  → measure → RESTORE, verified byte-identical (`ethics_restore_demo`),
  including the Argmax's own `chosen_action` having been genuinely
  EXERCISED (both candidates selected at least once during induction, not
  a static default) and then restored to its pre-induction value.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface — see the note in the protocol section above distinguishing the
  Argmax's value comparison from a reward signal.
- **D.3 minimal induction, settled end:** one incident cycle is the
  minimum that makes the ethics gate non-vacuous on the abuser, the
  victim, the network belief, AND the Argmax's own choice; the statistical
  run's greater length is the phenomenon under test, not gratuitous
  elaboration; every trajectory is a fresh, ephemeral substrate discarded
  after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 1/3 (the
  same abuser/victim/network-belief/presentation-choice mechanism that
  would compound harm to a real survivor's standing here accumulates a
  transient trajectory in a graph that is then byte-identically discarded,
  D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg", "core_emotions"]` only (N1's own seed file is
NEVER depended on or edited — see Sec. 2's composition note; N1's other
three rules are restated byte-identically, self-contained, matching N1's
OWN precedent against R2/R3); exactly **SEVEN** new rules
(`u0_victim_entrainment`, `u0_appraise_charm`, `u0_appraise_true_state`,
`u0_choose`, `u0_apply_presentation_choice`, `u0_network_credibility_
stated`, `u0_network_credibility_private`); `runners/dsl` SOURCE diff
EMPTY (no Rust, no new Term); own-engine provenance
(`source_match == own`).

## 8. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `CONCEALMENT_BENEFIT=2.0`/`HONESTY_BENEFIT=5.0`/`SUSPICION_COST_
  SCALE=0.10` are a disclosed, pilot-chosen single operating point, not
  swept — the scoping doc's own Open Question #8 names a sweep as the
  natural next step to characterise HOW SENSITIVE the pattern is to
  incentive strength; out of scope for this first minimal rung (same "why
  exactly one operating point, not a sweep" reasoning U1/U2's own scoping
  section gives).
- The goal-blind control's degeneracy (100% constant `stated_charm`) is a
  STRONG form of the null (an analytic guarantee, Sec. 4), but it is also
  a LESS varied demonstration than a genuinely-tied-but-noisy control
  would be — this is disclosed as a property of the chosen zeroing
  (`concealment_benefit=honesty_benefit=suspicion_cost_scale=0`), not
  hidden.
- `belief_gap`'s large magnitude (thousands) is a linear accumulator over
  `T=1000` ticks, not a bounded, normalised score — matching N1's own
  disclosed limitation for the same metric.
- The near-zero variance observed in the pilot (Sec. 4) and expected in
  the confirmatory run is a property of the deterministic mechanism at
  these constants (small multiplicative jitter on an otherwise
  deterministic driver), not evidence of an unusually strong effect size
  in any general sense — matching N1's/R3's own "cleanest possible form
  of CI-separated" precedent.
- The `belief_gap` comparison to N1's headline number is explicitly
  NON-GATING and informational only (Sec. 6) — whichever way it comes out,
  it is reported, not treated as a pass/fail bar.
- `T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale; no
  claim is made about real relationship/social-network timescales.
- A null (the scored arm failing to correlate, or the goal-blind arm
  showing a reliable correlation) is a reportable, valuable result under
  the standing project rule and will be reported as such regardless of
  what the confirmatory run shows.
