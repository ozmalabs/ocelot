# Stupid, stubborn, ignorant — three different fields, not three degrees

From outside, all three present identically: *the agent does not get it.* The question is whether
the substrate can tell them apart.

**Answer, after two rungs: all three, and the route there was not the one this document first
claimed.** Ignorance was already separable. Stubbornness was not — `feasible_selection` was built for
it. Stupidity *looked* separable, was found not to be when the selector exposed that its field was a
duplicate, and is now separable because `projection_field` was fixed to ask the second question. Both
corrections are left visible below rather than rewritten away, because the intermediate state — a
field whose doc comment described a distinction the code did not make — is the more useful thing to
have on record.

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
| **STUPID** | you enumerate fine but cannot establish what stays in the tube | `information_loss` + `resolved == false` — **fixed this rung** | widen aperture, or spend more budget; if the limit is physiological, there is none |
| **STUBBORN** | the candidate is admissible, projectable, and never selected | `withheld_minimal` — **built this rung** | neither parts nor aperture; only selection |
| *(not a deficit)* | the audit could not run at all | `support: false`, fail-closed | not the agent's; someone else's or undefined |

Two corrections, both forced by building it.

> **RETRACTED, THEN REPAIRED.** This paragraph originally claimed `loss` and `information_loss` were
> different failures, on the strength of the field's doc comment. Building `feasible_selection`
> showed they were the same number — incremented on the same line, nowhere else. Rather than soften
> the claim, the next rung made it true: `projection_field` now counts them separately. The
> distinction below is therefore descriptive again, but it was aspirational for as long as this
> document existed, and a doc comment is not evidence that code does what it says.

**Ignorance fails closed, and that is correct.** `counting_narrativium_by_dimension` returns `None`
for an empty family or any unsupported candidate — *"fails closed rather than being reported as zero
capacity."* An agent that holds nothing does not report that no future is reachable; it reports that
reachability is **not established**. Honest ignorance is already the coded default here, in the same
shape as the seed-level `covered = None` versus `covered = 0` distinction.

## What building it falsified

`feasible_selection` (`future_manifold.rs`, 8 Rust tests, lib suite 800 passed) closes the stubborn
gap — and in the process falsified two of this document's own claims. Both are pinned as tests so
they cannot drift back.

**`information_loss` was numerically identical to `loss`.** The audit incremented them on the same
line and nowhere else, while the field's doc said *"cells whose retention could not be
established"* — a genuinely different question from *"cells that left the tube"*, which the code
never asked.

**`resolved` carried no independent information.** `projection_field` set `support = false` whenever
`audited < requested_horizon`; `resolved` was then false-if-unsupported, else
`audited >= requested_horizon` — which support already guaranteed. So `resolved == support`, always.

Together these meant an under-resourced projection read as **unsupported** — *the audit could not
run* — never as *ran, and could not tell*.

## The fix — `projection_field` asks the second question

Three changes, each following from the last:

1. **`loss` no longer increments `information_loss`.** A cell that left the tube WAS assessed; its
   retention is established, as false. `information_loss` now counts only cells inside the requested
   horizon that the budget never reached — *"could not be assessed at all"*, literally.
2. **A budget shortfall no longer falsifies `support`.** `support` asks whether the audit is
   WELL-POSED (shapes, finiteness, geometry); `resolved` asks whether it COMPLETED. Separating them
   is what gives `resolved` independent meaning and makes the supported-but-undecided state exist at
   all. Its `termination_code` is `3.0` — not a new code, but the one the sibling implementation
   already uses for exactly this (`motor_compose.rs`: `if support { 3.0 } else { 4.0 }`).
3. **A truncated audit may no longer claim retention.** `retained_by_dim` stayed `true` for
   dimensions over ticks nobody looked at — a latent false claim, masked only because a short audit
   used to falsify `support` outright. Removing that mask would have made the bug live, so it is
   fixed in the same change, and it is what keeps every downstream gate closed (below).

**Fail-closed is preserved, and was checked rather than assumed.** `counting_narrativium_by_dimension`
and `feasible_selection` now require `resolved`, not merely `support`. The only other consumers are
two gates in `speech.py`: the alignment gate already tested `resolved` explicitly, and the `retained`
gate — which does *not* — is protected by `retained_width`, now `0` for any unfinished audit. One
shipped test asserted the old contract (`support == 0` on budget exhaustion) and was updated to the
sharper one, with assertions pinning every gate that keeps an unfinished projection unusable.

Gates: `information_loss_counts_what_was_not_assessed_not_what_failed`,
`resolved_is_no_longer_derivable_from_support`,
`ignorant_stupid_and_stubborn_all_have_distinct_signatures`. Rust lib suite 801 passed; manifold
Python suites 42 passed.

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
the puncture test (`APERTURE_PATHOLOGIES.md` §5: two true parts, one distinguishable). All three rows are **now producible at the manifold** and are gated together in
`ignorant_stupid_and_stubborn_all_have_distinct_signatures`: an empty family fails closed
(ignorant), a starved budget yields supported-unresolved candidates with non-zero
`information_loss` and an empty feasible set (stupid), and a withheld candidate stays minimal and
unselected while nothing is unestablished (stubborn). No two are confusable, and the test asserts
each one's *absence* of the others' signatures rather than only its own presence.

What remains open, precisely: the seed-level and manifold-level versions have still never been run
as **one** design. That needs a candidate family generated from an agent's own aperture — nothing
does that yet, and until something does, "widen aperture cures stupidity" is measured at seed level
(the puncture test) and merely *representable*, not demonstrated, at the manifold.
