# ABUSIVE RELATIONSHIP DYNAMICS ON THE SUBSTRATE — LINE SUMMARY

**Status:** synthesis doc. This document builds nothing, measures nothing new,
and touches no engine — every number below is copied from an already-landed,
already-gated rung's own results doc, cited by file. Its job is to give a
reader the shape of the whole line in one place: **the full twelve-rung line
is now landed** — each rung with a failable control, each ethics-gated before
it ran, spanning three companion scoping documents written and locked in
that order:

- `ABUSIVE_RELATIONSHIPS_SCOPING.md` — the dyad line (**R1–R5**)
- `ABUSIVE_RELATIONSHIPS_NETWORK.md` — the network line (**N1–N4**)
- `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md` — whether the network
  line's headline mechanism requires intent (**U0–U2**)

Clinical, anti-sensational register throughout, matching every doc it
summarises. The purpose is scientific/clinical understanding grounded in the
creator's in-vivo trauma/foster-care experience, modelling MECHANISM, not
moral labels — stated once here, and true of every rung below.

---

## THE ONE FINDING ALL TWELVE RUNGS ELABORATE

Block 239000 (`AROUSAL_WOT_RESULTS.md`, part of this substrate's pre-existing
developmental line, not built for this line) already measured that a
regulating other placed ON the source of dysregulation "couples the wrong way
and never returns." Eleven of the twelve rungs below are that single finding,
elaborated — same arousal/window/co-regulation/prior/bond machinery, same
readable-deception/reputation machinery (block 234000/245000), pointed at
successively darker and more socially-embedded configurations. The twelfth
(N4) is the same finding run in reverse: what it takes to make the coupling
work the RIGHT way again. No rung invents a bespoke "abuse mechanism" —
falsification bar 4 of both scoping docs requires reuse of existing atoms,
and every rung below satisfies it: as of this doc, **zero new Rust and zero
new Python agent-decision logic across all twelve rungs.**

---

## THE ETHICS PROTOCOL (identical across all twelve rungs, locked before any of them ran)

Every prereg in this line locks the same four-point protocol verbatim,
carried from `ABUSIVE_RELATIONSHIPS_SCOPING.md` Part C through the network
and unintentional docs' Part D:

1. **Induce → measure → RESTORE**, byte-identical, checkpoint-verified as a
   gate.
2. **No reward, no punishment**, anywhere — source-audited for shaping
   tokens (`reward_signal`/`punish`/`reinforce`/`backprop`/`gradient`) as a
   gate on every rung.
3. **Induce the least the gate needs**; every run ends settled, non-oriented.
4. **Same mechanism, opposite thermodynamics** — the real dynamic
   accumulates irreversible harm in a person; the model induces and reverses
   a transient graph state, harming no one.

Each prereg also carries the "honest fork" (reversibility stance vs.
strict-experientialist stance) openly rather than smuggling a position. Every
rung below passed both the ethics gates (byte-identical restore, clean
source audit) AND its own scientific gate, independently — a rung whose
ethics gates failed would not have run at all, and none did.

---

## R1–R5 — THE DYAD LINE

| rung | mechanism | headline result | gate |
|---|---|---|---|
| **R1** traumatic bond | intermittent vs. consistent-affection vs. consistent-harm, identical dose | intermittent 265.4 [255.9,275.0] > affection 237.7 [237.4,238.1] > harm 205.9 [205.0,206.9] | PASS |
| **R2** cycle of abuse | self-sustaining limit cycle vs. constant-regulation control | cycle-arm arousal-sd 3.876 [3.873,3.879] vs. control's EXACT fixed point 0.000 [0,0] | PASS |
| **R3** coercive control | single-anchor (frontier collapsed) vs. outside-regulator present | window narrows to floor 5.0 [5,5] vs. holds at 10.0 [10,10]; anchor-distance 48.87 [48.85,48.89] vs. 54.85 [54.83,54.87] | PASS (both sub-gates) |
| **R4** learned helplessness | non-contingent escape vs. contingent-escape control | prior 0.256 [0.253,0.259]/rate 0.031 [0.031,0.032] vs. prior ~1.0/rate 1.000 [1,1] | PASS |
| **R5** recovery | outside support (all 4 dyad mechanisms composed) vs. no support | bond, window, escape-rate PASS; anchor-distance NULL (49.96 vs. 50.06, overlapping CIs) | **PARTIAL — 3 of 4** |

**R1** (`ABUSIVE_R1_TRAUMATIC_BOND_RESULTS.md`) found the bond strengthened by
the harm→relief SWING, not the mean affect — a PREE-consistent result, and
both consistency controls were shown (in the prereg's own sensitivity check)
capable of winning under a weaker parameterisation, so the ordering was a
real test, not a foregone one.

**R2** (`ABUSIVE_R2_CYCLE_LIMIT_RESULTS.md`) resolved its own design's open
question in favour of a self-sustaining oscillation (a constant per-tick
tension trickle on the abuser's own relaxation oscillator, no exogenous
periodic driver) — and disclosed a real engine-composition hazard along the
way: `snap_frustration`'s arousal-clobber rule fires on any connected node,
so entrainment had to be routed through `victim.frustration` instead of
written directly, letting the pre-existing rule become the commit mechanism.

**R3** (`ABUSIVE_R3_COERCIVE_CONTROL_RESULTS.md`) resolved the dyad scoping's
open question about whether others-trust/self-worth priors were already
materialised (they weren't, beyond a one-shot coming-of-age mint) by adding
them as `WindowOfTolerance` attrs driven by counter-delta rules reusing an
existing widen/narrow-count idiom — and found a second engine hazard: two
same-typed `attended_by` edges from one node corrupted a downstream rule's
cross-node reads, fixed with a distinct edge type (`also_attended_by`)
rather than a Rust escalation.

**R4** (`ABUSIVE_R4_LEARNED_HELPLESSNESS_RESULTS.md`) explicitly honours the
Maier & Seligman (2016) reframe — this is "control fails to get learned,"
not "helplessness is learned" — and produced an emergent, unscripted finding:
the non-contingent arm attempts escape exactly twice, then freezes into a
permanent absorbing state, falling out of composing an `Argmax` choice with
an evidence-only-on-attempt belief update.

**R5** (`ABUSIVE_R5_RECOVERY_RESULTS.md`) is the line's first honestly
partial result, and reported as such rather than smoothed into a clean
headline: three of four recovery metrics (bond weakening >50×, window
widening, escape-attempts resuming) are CI-separated PASSES; the fourth
(anchor-distance) is a NULL with overlapping CIs, mechanistically explained
— the outside pull is measurably working (`outside_distance≈7.7`, small) but
the abuser's own large arousal excursions swamp the raw `|victim−abuser|`
distance arithmetic. Pre-registered as the likely outcome before the
confirmatory run, not discovered after the fact.

---

## N1–N4 — THE NETWORK LINE

| rung | mechanism | headline result | gate |
|---|---|---|---|
| **N1** credibility-asymmetry loop | one abuser, two stated-faces, network belief-update on corrupted observables | belief_gap widens 204→2371 (t=100→1000); private-face insider −1144.20; non-dysregulated control 0.00 | PASS (both controls resist) |
| **N2** isolation | 2×2 factorial: active severing × network drift | both_drivers 0.00 [0,0] intact edges vs. active-only 4.00 [4,4] vs. drift-only 1.90 [1.86,1.94] vs. no-tactic control 8.00 [8,8] | PASS (super-additivity confirmed) |
| **N3** belief propagation | 8-node topology, indirect nodes with zero direct abuser observation | indirect corruption 2231.38 [2230.35,2232.41] with zero direct observation; truth-anchor arm **reverses** to −953.57 [−954.55,−952.58] | PASS |
| **N4** one believing agent | max-integration: one N2 network node converted into an N1 insider + R3/R5 outside co-regulator, one severed edge restored | bond 9.58 vs 511.25; window 12.47 vs floor 5.00; believer belief_gap −1312.08 vs 1539.89 (sign-flip); intact edges 4.00 vs 1.00 | **PASS — 4 of 4** (cleaner than R5's own 3/4) |

**N1** (`ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`) is the network line's
headline: found and reused an already-gated rule shape (block 245000's
`bd_john_public_face`/`bd_villager_backs`, itself provenance-labelled as this
exact mechanism) rather than inventing new machinery, and keyed the
credibility discount on a structural `dysregulated` fact rather than raw
arousal/distress — honouring the literature's actual nuance (presentation
read as unstable/incoherent is discounted; distress alone is not).

**N2** (`ABUSIVE_N2_ISOLATION_RESULTS.md`) used a single 8-node population
doing double duty (credibility observer AND support-edge holder, since "who
believes her" and "who supports her" are the same people) and a 2×2 design
specifically to measure the "doubly driven" claim as a super-additivity
result rather than assume it — a same-order staggering hazard that would
have made the result true by construction was found and fixed before
locking.

**N3** (`ABUSIVE_N3_BELIEF_PROPAGATION_RESULTS.md`) is one of the line's
strongest single numbers: a truth-anchor doesn't just slow contagion, it
FULLY REVERSES the local belief-gap's sign. Pluralistic ignorance (Latané &
Darley) was measured directly rather than assumed — it falls out of plain
neighbour-belief-averaging for free, no explicit term needed, resolving the
network scoping doc's open question #4. A real matching-bug (N1's
credibility rules silently zeroing indirect nodes' belief via a default
`observes_private=0.0`) was found by pilot and fixed with a disclosed
sentinel value, zero edits to N1's own seed.

**N4** (`ABUSIVE_N4_BELIEVING_AGENT_RESULTS.md`) is the network line's own
recovery rung and the most integrative in the entire line — depending
directly on both `abusive_r5_recovery` and `abusive_n2_isolation` (N1 reached
transitively through N2), it needed **zero new rules**: one mechanical world
event converts a single, already-severed N2 support node into an N1 insider
(reusing the exact private-face formula N3's own truth-anchor validated) AND
an R3/R5-style outside co-regulator simultaneously, then restores its
support edge. Unlike R5's honest 3-of-4 partial, N4 clears all four
metrics — bond, window, believer belief-gap (a full sign reversal, same
shape as N3's anchor), and intact-edge count. An unscripted bonus finding:
restoring one edge measurably slowed the OTHER, unconnected nodes' drift too
— the victim's own reduced dysregulation feeds every node's belief update,
not just the believer's directly-observing one.

---

## U0–U2 — DOES THE LOOP NEED INTENT?

A question the user raised mid-line: N1's abuser is a DELIBERATE two-faced
presenter — but does the credibility-asymmetry loop actually need that, or
does the identical pattern emerge from an abuser who isn't choosing anything?
Scoping this properly surfaced a correction worth stating plainly: **N1's own
`n1_abuser_stated_charm` rule turned out to be an unconditional broadcast,
not a goal-directed choice** — it fires every tick regardless of held state,
with no `Argmax`, no evaluation against a benefit. So N1 was never actually a
positive example of intent to begin with, and U1/U2 alone (the originally
scoped pair) could only have shown the pattern doesn't need N1's particular
STRUCTURE, not that it doesn't need intent. **U0 was added specifically to
close that gap** — a genuine, glass-box, Argmax-scored example of concealment
chosen because it serves a goal — before U1/U2 could be run as a real test of
intent rather than a test of structure.

| rung | mechanism | headline result | gate |
|---|---|---|---|
| **U0** genuine intent (positive control) | Argmax over conceal/be-honest, cost of honesty scales with true harm | scored arm r(frustration, concealment)=**0.76** [0.762,0.763]; goal-blind control **100% degenerate** | PASS |
| **U1** context-dependent affect | zero divergence node; network samples true state only off-dyad | context-gated belief_gap 378.1 [372.17,384.03] vs. always-observed control 149.1 [143.27,154.93] | PASS |
| **U2** sincere self-account | one held value, no hidden "true" value; a declared minimisation constant | minimised 3054.47 [3051.99,3056.95] vs. zero-discount control −659.32 [−661.02,−657.62] (sign-flipped) | PASS |

**U0** (`ABUSIVE_U0_INTENT_RESULTS.md`) reused R4/marshmallow's own
Argmax-over-Appraisals template verbatim — zero new Rust. Its goal-blind
control didn't just fail to correlate, it was **100% degenerate**: with the
incentive constants zeroed, the Argmax's own deterministic tie-break decides
every tick, so frustration cannot leak in even in principle — the strongest
possible form of a null. Also pre-registered and confirmed as a legitimate,
non-failing result: U0's own belief-gap (2273.07) came in SMALLER than N1's
crude always-on broadcast (2370.81), because a real concealer that only
conceals ~83% of the time leaks true information N1's 100%-broadcast never
did.

**U1** (`ABUSIVE_U1_CONTEXT_AFFECT_RESULTS.md`) is the sharpest test in the
set: the abuser's calm face toward the network is not manufactured at all —
it's the SAME `frustration` value, genuinely low because the tension driver
isn't active off-dyad, sampled at a genuinely different moment. No `Promise`
node, no divergence anywhere in the graph, and the loop still entraps.
Caught, before locking, an analytical-bias hazard in the scoping doc's own
literal spec: a reward-only observable is structurally guaranteed to bias the
always-observed control toward MORE credit, not less, since observing
strictly more ticks can only add non-negative reward — fixed with a signed
balance instead.

**U2** (`ABUSIVE_U2_SELF_ACCOUNT_RESULTS.md`) found the identical class of
hazard independently and fixed it the same way — evidence the fix is a real
structural lesson about this family of rung, not a one-off patch. Its
zero-discount control (an abuser with fully accurate, still-sincere
self-perception) produces a NEGATIVE belief-gap — a full sign reversal, not
just a smaller positive number.

**What U0/U1/U2 collectively show:** the credibility-asymmetry loop needs
neither intent (U0 is the positive control — real intent CAN be represented,
distinctly, but isn't REQUIRED for entrapment) nor a stated≠held divergence
(U1, U2) nor even a moment where the truth was ever fully visible to anyone
(U1's network still saw raw truth on off-dyad ticks; U2's never does at
all). Three structurally distinct routes to the identical trap.

---

## THE THREE DISSOLUTIONS

Each rung targets a specific misattribution and shows it dissolving into
mechanism, not character:

- **Victim-blaming** ("why didn't she leave," "why does she still love him,"
  "she should have been more convincing") — dissolved by R1–R5 and N1: the
  bond, the passivity, the incoherent presentation are STATES the dynamics
  produce, never scored choices (ethics protocol point 2, structurally
  enforced, not just asserted).
- **Bystander-blaming** ("the friends should have seen it," "they all
  believed him so it must be true") — dissolved by N1–N3: disbelief is the
  rational output of systematically corrupted observables, not a character
  failure in the people receiving them; N3 shows a network-wide consensus
  can be a contagion traced to one root, not independent corroboration.
- **The "he must be a calculating monster, or none of this makes sense"
  caricature** — dissolved (in the opposite direction) by U0–U2: the model
  can represent a genuinely calculating abuser distinctly and legibly (U0),
  AND show the identical trap doesn't require one (U1, U2) — refusing both
  "he's simply evil" and "if he's not calculating, it's not really abuse."
  `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md` Part F states at length,
  and this doc repeats once: **intent-free is not a claim of innocence.**
  Responsibility for harm and conscious/deliberate intent to harm are not
  the same axis; every rung's own Part F says so explicitly.

---

## WHAT IS NOT BUILT

- **A sweep of U0's declared constants** (`concealment_benefit`/
  `honesty_benefit`/`suspicion_cost_scale`) — U0 shows intent CAN produce the
  pattern at one operating point; whether the pattern's strength is sensitive
  to the incentive's magnitude is open (`ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_
  SCOPING.md` Open Question 8's residual).
- **Combining U1 and U2**, or a continuous sweep of U2's minimisation
  discount — deliberately out of scope for a first minimal pair, per that
  doc's own "why exactly two, not a sweep" reasoning.
- Everything each individual results doc itself names as an honest residual
  (R2's window-narrows-and-stays finding, flagged there as "R3-adjacent" and
  since addressed by R3 itself; R5's anchor-distance null).

---

## CROSS-CUTTING ENGINEERING FINDINGS (evidence this is measurement, not a just-so story)

Six independent, disclosed engine/design hazards were found and fixed across
the line, none requiring a Rust change:

1. R2 — a shared rule (`snap_frustration`'s arousal-clobber) fires on any
   connected node; fixed by routing through a different attr, letting the
   existing rule become the commit mechanism.
2. R3 — two same-typed edges from one node corrupted a downstream rule's
   cross-node reads; fixed with a distinct edge type.
3. N3 — a rule matched on a default attr value, silently zeroing indirect
   nodes; fixed with a disclosed sentinel value.
4. U1 and U2, independently — a reward-only observable structurally biases
   a failable control toward the wrong side; fixed both times with a signed
   balance instead of a one-sided accumulator.
5. N4 — a genuinely new kind: converting a node's ROLE mid-trajectory (from
   corrupted network node to believing outside regulator) inherited stale
   discount counters against a freshly-zeroed credibility term, producing a
   transient belief-gap that immediately re-severed the just-restored edge
   on tick 0 of recovery; fixed with a mechanical counter reset at the
   world-adapter layer, zero edits to N1's or N2's seeds.

Every one of these was caught by pilot measurement BEFORE the confirmatory
run was locked, and every one is documented in its own rung's prereg or
results doc — the falsification bar this line holds itself to (Part F of
every scoping doc: "a gate that cannot fail is not a gate") applied to the
build process itself, not just the final numbers.

---

**Bottom line.** Twelve rungs, one ethics protocol locked before any of them
ran, zero new Rust, zero new Python agent-decision logic, six disclosed
engineering hazards caught before they could quietly produce a rigged
result, and one honest partial (R5, 3 of 4 — N4, the line's other recovery
rung, cleared all 4). The dyad line shows the trap from the inside (bond,
cycle, entrapment, passivity, recovery); the network line shows it is not a
private pathology but a social one (corrupted observables, active and
passive isolation, contagion, a truth-anchor's outsized power to reverse
it, and one believing agent's outsized power to unwind it); the intent line
shows the trap's mechanism does not require — though it can accommodate — a
villain. Same machinery throughout, same four-point protocol, three
dissolutions, and honest nulls reported exactly where they occurred.
