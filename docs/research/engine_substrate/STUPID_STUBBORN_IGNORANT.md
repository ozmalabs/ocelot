# Stupid, stubborn, ignorant — three different fields, not three degrees

From outside, all three present identically: *the agent does not get it.* The question is whether
the substrate can tell them apart.

**Answer after building the missing piece: two of the three, and not the two I first thought.**
Ignorance was already separable. Stubbornness was not, and now is — `feasible_selection` was built
for it (§"Stubborn… SOLVED"). Stupidity looked separable and **is not**: the field that was supposed
to carry it duplicates another one, which the build exposed (§"What building it falsified"). The
first draft of this document had that backwards and is corrected in place rather than rewritten.

## The record they live in

`runners/dsl/src/future_manifold.rs`'s `DeformationRecord` is per-candidate, and its comment is
emphatic about what it refuses to be:

> *"This is deliberately a RECORD, not a score. `μ` — the measure over a reachable deformation set —
> is grounding-open in the theory, and picking one here would install a scalar where a represented
> structure belongs."*

Fields: `support`, `resolved`, `loss`, `information_loss`, `retained_width`, `retained_dimensions`,
`earliest_decisive_tick`. Plus `DimensionNarrativium { reachable_deformations,
retained_deformations }` per dimension.

**That refusal is the whole reason the three terms separate.** Collapse this to one number — "how
much future can you reach" — and stupid, stubborn and ignorant are indistinguishable: all three read
*low capacity*. They are different only as a shape. This is the third time in this line of work that
`SHAPES, NOT NUMBERS` has turned out to be load-bearing rather than stylistic, and the first where it
paid off in code written before the question was asked.

## The mapping

| folk term | what is actually limited | field | recourse |
|---|---|---|---|
| **IGNORANT** | few candidates reachable at all — you hold little to project | low `reachable_deformations` | acquire parts; cheap, and it works |
| **STUPID** | you enumerate fine but cannot establish what stays in the tube | **none — `information_loss` duplicates `loss`, see below** | widen aperture — and if the limit is physiological, there is none |
| **STUBBORN** | the candidate is admissible, projectable, and never selected | `withheld_minimal` — **built this rung** | neither parts nor aperture; only selection |
| *(not a deficit)* | the audit could not run at all | `support: false`, fail-closed | not the agent's; someone else's or undefined |

Two corrections, both forced by building it.

> **RETRACTED by measurement — see §"What building it falsified" below.** This paragraph claimed
> `loss` and `information_loss` were different failures, on the strength of the field's doc comment.
> They are the same number: the audit increments them on the same line and nowhere else. The
> *distinction* is real and worth having; the *implementation* does not make it, so **stupidity has
> no field at the manifold** and the row below is aspirational, not descriptive.

**Ignorance fails closed, and that is correct.** `counting_narrativium_by_dimension` returns `None`
for an empty family or any unsupported candidate — *"fails closed rather than being reported as zero
capacity."* An agent that holds nothing does not report that no future is reachable; it reports that
reachability is **not established**. Honest ignorance is already the coded default here, in the same
shape as the seed-level `covered = None` versus `covered = 0` distinction.

## What building it falsified

`feasible_selection` (`future_manifold.rs`, 8 Rust tests, lib suite 800 passed) closes the stubborn
gap — and in the process falsified two of this document's own claims. Both are pinned as tests so
they cannot drift back.

**`information_loss` is numerically identical to `loss`.** The audit increments them on the same
line, and nowhere else. The field's doc says *"cells whose retention could not be established"*,
which is a genuinely different question from *"cells that left the tube"* — the code never asks it.
Gate: `information_loss_is_currently_a_duplicate_of_loss`.

**`resolved` carries no independent information.** `projection_field` sets `support = false` whenever
`audited < requested_horizon`; `resolved` is then false-if-unsupported, else
`audited >= requested_horizon` — which support already guaranteed. So `resolved == support`, always.

Together these mean an under-resourced projection reads as **unsupported** — *the audit could not
run* — never as *ran, and could not tell*. **There is currently no way to be stupid at the manifold:
only absent, wrong, or stubborn.** Starving the projection budget was my intended way to produce a
stupid agent; it fails the selection closed instead, which the test now asserts, with the assertion
message naming what a future fix would look like.

So the corrected count is: ignorance and stubbornness are separable today; **stupidity is not**, and
the reason is a one-line collapse in the audit rather than anything deep. Fixing it means asking the
second question — which cells could not be assessed, as distinct from which were assessed and
failed — and that is a change to `projection_field`, not to the selector.

## Stubborn: the substrate could not see it, said so — now BUILT

Stubbornness at manifold level is precisely *admissible, projectable, never selected* — and the
source names that gap in the same breath as the distinction:

> *"The theory distinguishes sharply between what is admissible and what is actually selectable: 'an
> always-admissible but never-selected candidate contributes no realised reachability.' Selecting
> requires the feasible-set machinery — a joint feasible family over subsets, a represented
> valuation, and a set-tie rule — none of which exists in this substrate today."*

`GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` lists it: *Feasible-set selection, SET-TIE — LACKS, zero
hits.* So `reachable_deformation_set` returns an **upper bound**, and a caller treating it as
realised reachability *"is overstating its own capability."*

**That was the state before this rung. It is now built.** `feasible_selection` applies the substrate's
own decision rule — `CLAUDE.md`'s *"minimum sufficient action/intervention that keeps the projected
tube inside it; goals break equal-intervention ties"*, read literally and in that order — and
publishes `withheld_minimal`: candidates that were established, feasible, minimal under the
represented valuation, and best under goals, and were **still not taken**. The theory's
*"always-admissible but never-selected candidate contributes no realised reachability"* is now a
countable set rather than a sentence.

Three properties worth stating because they were choices:

* **set-valued.** `minimal` and `selected` are families and `tie_breadth` is published. A selector
  returning one candidate would re-impose the single fixpoint an admissibility grammar exists to
  avoid.
* **goals never buy a more expensive candidate.** They order only what intervention left equal —
  gated by `minimum_sufficient_intervention_wins_and_goals_only_break_ties`.
* **fails closed on an unrepresented valuation.** "Minimum sufficient" over an unrepresented cost is
  not a smaller number, it is not a question; ranking such a candidate as free would launder the gap
  exactly the way a scalar narrativium would.

The substrate does not decide that withholding is a pathology. It makes the difference between what
would have worked and what was taken legible, and leaves the reading to the caller.

Stubbornness *does* have a cheap form that is already measured, one level down:
`APERTURE_PATHOLOGIES.md` §1 — an agent keeps exactly the chosen frames under which it has no
residual, because the widening rule only drops frames that leave one. That is stubbornness as *frame
retention*, and it is real. It is not the same thing as never selecting an admissible candidate, and
conflating them would be the same error as conflating `loss` with `information_loss`.

## The measurable prediction, not yet run

The three should separate on intervention exactly as the two folie-à-deux aetiologies did:

| | supply parts | widen aperture |
|---|---|---|
| ignorant | **corrects** | inert |
| stupid | inert | **corrects** |
| stubborn | inert | inert |

The first row is already measured at seed level —
`test_acquiring_a_part_RE_ARMS_the_decode` is literally ignorance being cured by acquisition, and
the pauper fixture is ignorance failing to be cured by anything else. The second row's inertness is
the puncture test (`APERTURE_PATHOLOGIES.md` §5: two true parts, one distinguishable). The third row is **now runnable at the manifold** and is gated there
(`ignorant_and_stubborn_separate_but_STUPID_HAS_NO_FIELD_YET`) — a withheld candidate stays minimal
and unselected under every intervention, because neither parts nor aperture touch selection.

What remains open, precisely: the **stupid** row cannot be produced at the manifold at all until
`information_loss` asks its own question, so the 2×2's middle row is exercised only at seed level
(the puncture test) and not in the manifold audit. And the seed-level and manifold-level versions
have still never been run as one design — that would need a candidate family generated from an
agent's own aperture, which nothing does yet.
