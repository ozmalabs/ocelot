# PROGRAM SYNTHESIS ARC 4 — BUDGET, VERDICT, AND DATA DEPENDENCIES

> **REVISED 2026-08-01, before any execution.** The first version of this plan was written
> from a partial literature read and was titled *"The spec is language, the program is not."*
> Its centrepiece (S1: spec comprehension → structured Goal) is **withdrawn**: the completed
> spike explicitly does not recommend it, on our own evidence — MBPP spec **recognition is
> already 99.6%**, and arc 2's HQ2 verdict was verbatim *"recognition was never the
> bottleneck."* Building a comprehension layer on top of a 99.6% recognition rate would have
> been a fourth content arc wearing a new hat. The revised plan below follows the spike's
> ranked implications instead. The withdrawn version is preserved in git history at
> `ae05d6f68a`; §6 records what changed and why, because a plan that quietly re-aims is
> indistinguishable from one that was never wrong.

**Date:** 2026-08-01
**Launches from:** arc 3 complete (`a30d0ea5c2`), plus the two spike deliverables
`RESEARCH_CODE_IN_THE_BRAIN.md` (literature) and the language-stack inventory.
**Status:** PLAN.

## 0. The thesis, in one paragraph

The brief was *"code is a language, use that stack."* The completed spike answers: **partly,
and not where we assumed.** Code comprehension is carried by the domain-general multiple-demand
system **[A]**; the popular "and not the language network" corollary is only **[B]** and is
routinely quoted conditions-stripped (Ivanova's null is the *ScratchJr* contrast, β = 0.15,
p = 0.29, n = 19; in *Python* the language network responded well above the nonword floor,
β = 0.78, p < 0.001 — and Liu/Wilson/Bedny 2024 decoded `for` vs `if` from lateral temporal
**language** cortex better than anywhere else, earlier than fronto-parietal). Identifier
semantics, the one place we assumed language helps, is the cleanest *falsification* in the
literature (English-vs-Japanese identifiers β = 0.03, p = 0.84; undecodable in MVPA).

The findings that actually bear on our measured failures are not about language at all:

1. **Retrieved candidates cause fixation, and de-biasing does not work.** Sheridan & Reingold:
   8/17 experts *and* 8/17 novices chose the plausible-but-suboptimal familiar move; expertise
   gave no protection. Sergeyuk: **both** de-fixation interventions failed. Soloway: 66% of
   wrong answers took the plan-shaped form. **Implication: fix the budget, not the proposer.**
   Exactly our arc-2 decoy tax (24 `gapped:exhausted` rows, all cued; that class 0/257 in
   CONTENT-STRIPPED) and arc-3 task-17 preemption.
2. **Load is data-dependency tracking, not path stepping.** Peitek: McCabe (execution-path
   count) τ ≈ .04–.09 — essentially zero; **DepDegree (data flow) τ = .32–.41**. Crichton:
   ~7 variable/value pairs held, errors are **swaps not forgetting**, and the no-schema
   strategy traces **backward along data dependencies** — converging with Rist's focal
   expansion from an unrelated literature.
3. **Semantic cues lower COST, they do not add CAPABILITY.** Every beacon/plan/naming result
   is a latency effect; where correctness was tested it was n.s. (63% vs 66%). We have only
   ever measured content on an **accuracy** instrument — four times.
4. **Expert memory advantage survives scrambling** (Sala & Gobet meta-analysis, 24 studies,
   903 participants, programming r̄ = .36): **many small chunks, not few big plans.** Our arc-3
   escalation to whole-program grain ran *opposite* to the best-powered result in the review,
   and our own 4.67% oracle ceiling had already said so.

So arc 4 stops trying to make the proposer smarter and instead makes **being wrong cheap**
(budget isolation), **being right verifiable earlier** (verdict discrimination), and **search
better-aimed** (data-dependency backward ordering) — then closes the search-reach gap that
carries 55.3% of all failures and about which the neuroscience has, tellingly, nothing to say.

## 1. Hypotheses (bars set in S0, never before)

- **HA1 — budget isolation.** Cued/retrieved proposals cannot consume enumerator budget:
  `gapped:exhausted` → 0 across *all* classes (arc-3's R2.5 covered 17/24; the residual 7 are
  descend-applicable and need the general fix), and no task regresses. Paired ids.
- **HA2 — verdict discrimination.** `accepted_holdout_fail` (26.8% of MBPP outcomes; 55–60%
  trap mass at retrieval grain) falls CI-separated, by rejecting *before* accept using
  differential oracles we already own — four render frames with **zero measured toolchain
  disagreements** across arcs 1–3, i.e. an unused agreement signal — plus property checks
  derivable from the spec (type/arity/invariance), never from held-out rows.
- **HA3 — data-dependency ordering.** Re-indexing hole derivation and enumerator ordering on
  **backward data dependencies from the goal's output** beats current ordering on accepts and
  attempts-per-accept. (Also promotes P7-B's registered blocker — acc-dependent fold bodies —
  on external evidence.)
- **HA4 — search reach.** Targeted enumerator widening (the `gapped:enumerate_failed` 55.3%
  class: mutating-method write-back, comprehensions, kwargs — sized from the Q0 joint curve)
  yields the largest single movement of the arc. *No neuro support and none needed; ranked by
  our own taxonomy.*
- **HA5 (single, bounded, honesty-flagged) — the cost instrument.** Held content is re-measured
  ONCE on **cost** (attempts, screen evaluations, wall-steps to first accept) rather than
  accuracy, with a preregistered bar. Finding 3 says this is the instrument the human effect
  actually lives on. Flagged in the spike as its most just-so-story-prone recommendation:
  it gets **one** shot, a preregistered bar, and no follow-up if null.
- **Registered fourth-null rule (carried forward):** if HA5 nulls too, the proposal-content
  line ends permanently — including on the cost instrument — and remaining effort goes to
  verdict + search + protocol.

## 2. Phases

### S0 — Measure first (the R0 discipline, which has now correctly predicted two arcs)
- Enumerate the current `gapped:exhausted` residual by class (which are descend-applicable,
  which are cued, which are neither) — HA1's target list, as ids.
- Trap anatomy for HA2: of the 55–60% trap mass, how many are killable by (a) cross-frame
  render disagreement, (b) type/arity property violation, (c) invariance property (permuting
  irrelevant input structure), (d) nothing available — the honest residual.
- Data-dependency probe for HA3: for arc-3's failures with a known oracle solution, does
  backward-from-output ordering reach it in fewer enumerator steps? Offline, no build.
- Search-reach sizing for HA4 from the Q0 joint curve + current blocker taxonomy.
- `PROGRAM_SYNTHESIS_ARC4_PREREG.md` with every bar derived from the above, HA5's preregistered
  cost bar, and the falsifiers from research §8.5.

### S1 — Budget isolation (HA1)
Every non-search proposal source (codebook, chunk, retrieval, NL-derived) draws from a
**separate, bounded proposal budget**; the enumerator's budget is reserved and untouchable.
Generalises R2.5's screen from "engage when pool ≥ budget" to "always isolate" — which also
covers the 7 descend-applicable rows R2.5 honestly could not. All in the seed rules.

### S2 — Verdict discrimination (HA2)
Reject-before-accept using owned signals: cross-frame render agreement (python/rust/lua/llvm —
a disagreement is a defect signal we currently never consult), spec-derived property checks,
and metamorphic/invariance checks. **Held-out rows stay untouched** — the protocol's isolation
is not negotiable; these are *additional* pre-accept filters, not a peek.

### S3 — Data-dependency backward ordering (HA3)
Build the def-use graph over hub IR (mechanical), then: hole ordering and enumerator variable
ordering proceed **backward from the output role's producers**. Rist's focal expansion and
Crichton's backward tracing arrive at the same policy from different literatures; DepDegree
says this is the axis that actually carries load.

### S4 — Search reach (HA4)
The mass-carrying enumerator/emitter gaps, in Q0-joint-curve order: mutating-method write-back
(the largest single named residual since arc 2), comprehension forms, kwargs. Engine work where
it is genuinely engine work; everything else in rules.

### S5 — The one cost measurement (HA5) + powered endgame + arc summary
Arms: FULL-A / NO-ISOLATION / NO-DISCRIMINATION / NO-BACKWARD / arc-3 continuity, on MBPP
PRIMARY (OFFICIAL row for comparability), both denominators, Wilson/Newcombe CIs, paired
identity lists, twin-run determinism. HA5's cost instrument runs once, here, on the frozen
content layers. Summary in the standing pattern; apply the fourth-null rule if it triggers.

## 3. Explicitly NOT in this arc

- **No spec-comprehension layer** (withdrawn; recognition 99.6%, HQ2: *"never the bottleneck"*).
- **No identifier-semantics proposal** (β = 0.03, p = 0.84; 6.9% inter-developer naming
  agreement — the spike's explicit non-recommendation).
- **No decomposition routed into the language stack** (no evidence; global aphasics retain
  bracketed arithmetic with operator-order sensitivity, formal reasoning, and chess **[A]**).
- **No new pattern/chunk/exemplar content layer** — three accuracy nulls; HA5 is the single
  bounded exception and it is a *cost* measurement, not a new layer.
- **No abstraction-from-static-reading.** If abstraction is revisited it must be Pennington's
  inversion (derived from pre/post-**modification** execution diffs) — deferred to a possible
  arc 5, not smuggled in here.

## 4. Boundaries (unchanged)

Decisions in rules/Terms; adapters mechanical (no-Python-decision audit is a standing gate);
frozen artifacts append-only; contamination list-gate green every phase; drifted pins
reconciled only in the improvement direction, dated; every claim carries its denominator;
power the gate before the endgame.

## 5. What would make this arc a failure worth reporting

If HA1 and HA2 both land and the pass rate still does not move CI-separated, then cheapness and
early rejection are not the binding constraint either, and the honest conclusion is that this
architecture's ceiling on MBPP is set by **search reach alone** — a clean, publishable negative
that would redirect all remaining effort to HA4-class work and to the engine floor.

## 6. Revision log

**v2 (2026-08-01, pre-execution).** Withdrew S1 spec-comprehension and the HS1/HS4/HS5
hypotheses built on it after the full literature spike landed: recognition is already 99.6% and
arc 2's own HQ2 verdict said recognition was never the bottleneck, so the v1 plan would have
spent an arc improving a solved input. Retained from v1: the annotation/bind layer and focal
expansion — but **focal expansion is re-founded on data dependencies** (DepDegree τ = .32–.41
vs McCabe τ ≈ .04–.09) rather than on control flow, which is the sharper and better-evidenced
version, and the **annotation/bind layer is deferred to arc 5** because its own falsifier
(research §8.5: "if bind-completeness does not correlate with synthesis failure it is
bookkeeping") is untested and S0 has no budget to test it alongside four ranked implications.
Two corrections were also applied to `RESEARCH_CODE_IN_THE_BRAIN.md`: the MD-vs-language
grading (I had written the conditions-stripped [A] form; it is [A] for MD-carries-it, [B] for
not-language), and the gated-check figure (neither "~1,900" nor "~3,000" was ever derived;
measured = **832 collected node ids** across the 27 arc suites).

---

## 7. Revision log v3 (2026-08-01, post-S0, pre-build)

S0 measured before building, and changed two phases. Both changes are *reductions*.

**S3 (data-dependency backward ordering) is CUT.** HA3's probe drove the **real**
`SynthEnumerate` Term (not a simulation) over 18 known-solution tasks plus 2 hand-built
multi-hop dependency chains: **zero backward-wins, anywhere.** The reason is structural
rather than a tuning failure — MBPP-native solutions are overwhelmingly flat
single-return expressions with no assignment chain, so only 2/17 tasks could even
*reorder* (every referenced variable ties at dependency depth 0). The research doc's
own registered falsifier (§8.5: "focal expansion may not transfer — the human result is
partly about working memory we do not share") fires, and it fires for an even simpler
reason than predicted: **our programs lack the dependency depth the ordering exploits.**
Recorded as a measured null; not built. HA3 is withdrawn from the endgame's hypothesis
set and reported as an S0 result.

**S4 (search reach) is RE-AIMED, and the plan's stated priority was wrong.** Freshly
recomputed sizing (the arc-2 histogram is **stale on the mutating-method axis** — found
and documented by S0-B) ranks the levers by exclusive mass:
`comprehension_forms 16 > mutating_method 12 > kwargs 8 > map_lambda 6 > regex 5 (oos)`.
More importantly: **all five levers together cap at 47/139 = 33.8%** of the
`gapped:enumerate_failed` population, while the dominant **85/139 = 61.2% already emit
fine and need none of them.** Those tasks fail because the **enumerator cannot reach
list/iteration programs**, which is a search-reach problem in the engine's composition
depth and op inventory — not an emitter-coverage problem, and outside the scope S4 was
written with. S4 therefore targets the 61.2% bucket first (enumerator reach over
list/iteration composition), with the emitter levers second and sized honestly at ≤33.8%.

**Unchanged:** S1 (budget isolation) — S0-A proved its target is the *complete* residual
(17/17, classes (c)/(d) structurally empty). S2 (verdict discrimination) — with its bar
now pinned to the measured 30.3% killable / 69.7% honest-residual split, and three
concrete defects to fold in (permissive-interpreter vs faithful-render divergence;
the lua truthy-zero renderer bug; `_row_cmp_ok`'s bool-vs-numeric blindness).
