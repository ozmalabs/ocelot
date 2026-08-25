# Stupid, stubborn, ignorant — three different fields, not three degrees

From outside, all three present identically: *the agent does not get it.* The question is whether
the substrate can tell them apart. Two of the three it already can, in fields that exist today and
were built for other reasons. The third it **cannot**, and it knows exactly why.

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
| **STUPID** | you enumerate fine but cannot establish what stays in the tube | high **`information_loss`** | widen aperture — and if the limit is physiological, there is none |
| **STUBBORN** | the candidate is admissible, projectable, and never selected | **no field — see below** | — |
| *(not a deficit)* | the audit could not run at all | `support: false`, fail-closed | not the agent's; someone else's or undefined |

Two things worth pulling out.

**`loss` and `information_loss` are different failures, and only one of them is stupidity.** `loss`
counts cells that left the allowed tube — you projected correctly and the news is bad. That is
accurate pessimism, not a deficit. `information_loss` counts cells *whose retention could not be
established*. **Knowing-that versus knowing-what, at the manifold**, which is the same split as the
mystic's detectable-but-unresolvable residual (`ONE_LOOP_MANY_GRAINS.md`) and the aperture-gated
reality channel (`APERTURE_AETIOLOGY_CROSSOVER_RESULTS.md`) — third independent occurrence of one
shape, in three subsystems built separately.

**Ignorance fails closed, and that is correct.** `counting_narrativium_by_dimension` returns `None`
for an empty family or any unsupported candidate — *"fails closed rather than being reported as zero
capacity."* An agent that holds nothing does not report that no future is reachable; it reports that
reachability is **not established**. Honest ignorance is already the coded default here, in the same
shape as the seed-level `covered = None` versus `covered = 0` distinction.

## Stubborn is the one the substrate cannot see, and it says so

Stubbornness at manifold level is precisely *admissible, projectable, never selected* — and the
source names that gap in the same breath as the distinction:

> *"The theory distinguishes sharply between what is admissible and what is actually selectable: 'an
> always-admissible but never-selected candidate contributes no realised reachability.' Selecting
> requires the feasible-set machinery — a joint feasible family over subsets, a represented
> valuation, and a set-tie rule — none of which exists in this substrate today."*

`GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` lists it: *Feasible-set selection, SET-TIE — LACKS, zero
hits.* So `reachable_deformation_set` returns an **upper bound**, and a caller treating it as
realised reachability *"is overstating its own capability."*

**Consequence, stated plainly: at the manifold the substrate can currently distinguish ignorant from
stupid, and can distinguish neither from stubborn.** A stubborn agent and a capable one produce the
same admissible bound, because the bound never asks what was chosen. That is a real limitation and
it has a named location rather than being a mystery.

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
the puncture test (`APERTURE_PATHOLOGIES.md` §5: two true parts, one distinguishable). **The third
row cannot be run**, because producing a stubborn agent requires a selection step the substrate does
not have.

So this document claims exactly one thing beyond the mapping: the diagnostic 2×2 is two-thirds
already-measured and one-third blocked on a gap that predates the question. It has not been run as a
single design, and the manifold-level version has not been run at all — everything above about
`DeformationRecord` is read off the source and its own comments, not measured.
