# Review of `01_law_of_graphic_equalisation_theory_referenced.tex` (draft-2026-09-02.1, r278) — proposal for fixes

Second pass. Scope: the whole file (3313 lines, 74 pp), its log and aux,
the r273 review and what r274–r278 did with it, and every companion 01
refers to (00 r121, 01a r42, 01b r39, 02 r26, 02a r11, 04 r20, 05 r9,
06 r27, A1 r6) for the by-description references. Line numbers are r278.
Nothing applied.

Compile: 2 underfull-hbox warnings (both the companion table, l.87 and
l.94), 0 overfull, 83 bibitems all cited, no `??`, every `GE-` label
cited by another paper resolves (62 distinct), by-name check clean, counts
generated. r274–r278 did what r273 asked: companion numbers via
`xr-hyper`, the second axiom numbered 1, the ledger as a table, the five
splits, `hyp:cheap-cut`, the labels, the narration sweep, the theorem
downgraded, the prose fixes. **What this pass finds: one place the paper
still rests evidence on the non-released construction paper, and it is a
place where the engine record contradicts the construction paper; the
companion-naming rule the paper states for itself is broken at about
thirty sites and the paper cites seven companions by description while
resolving only one by number; one falsifier is contradicted by a
corollary the last pass restricted; five proposition/remark pairs
restate each other verbatim; and four sites of narrated drafting
survive.**

Sixty-two of 01's labels are cited by other papers. All must survive under
the same names and kinds.

---

## A. The construction paper is still the evidence, at a site where the engine disagrees with it

l.486–487 (`rem:inherited`, the realisation-operator entry): "…residual …
cannot carry a joint incompatibility between two individually admissible
writes. **The constructive companion is the evidence:** its executor
refuses that case as an explicit incompatibility rather than
residualising it."

Three things are wrong with the sentence.

1. It cites A1 as evidence, against the standing rule (A1 is not
   circulated; evidence is the pre-registered record). l.62–65 and the
   table row at l.87 still *license* this ("cited as evidence that
   something was built and behaved as described"). That licence should
   go too: the record is the evidence, A1 is a realisation the reader
   cannot obtain.
2. The A1 review (`A1_REVIEW_r6_PROPOSAL.md`, headline finding, verified
   against `rewrite.rs`) found that A1 §6's "synchronous rounds,
   deterministic merge over compatible effects, explicit incompatibility
   otherwise" is **not what the engine implements**: `run_rules` applies
   rules sequentially in place and re-enumerates on progress. So "its
   executor refuses that case as an explicit incompatibility" is A1's
   specification, not the engine's behaviour, and it is unverified.
3. The paper contradicts itself through it. l.2064 (`prop:partial-order`
   discussion) says the opposite, and says it as the engine's actual
   regime: "a graph's state may be altered by another write while its own
   rules are mid-run … robustness is obtained by re-running to fixed
   point (**a raced deformation becomes residual and is re-encountered on
   the next pass**), not by locking." That is residualising the case
   l.487 says the executor refuses.

**Fix.** Delete the sentence at l.486–487. The argument it supports
(residual is per-rule, so a *joint* incompatibility is not a residual of
either rule) stands on the definition alone; if evidence is wanted, it is
l.2064's mechanism, stated from the record with the evidence-standard
sentence. Reconcile l.2064 and l.485: what the engine does with a raced
pair is re-run to fixpoint, and whether the second write sees the first
is the sequential semantics — say that once, and let A1's fix (its own
review, item on §6) describe the engine rather than the other way round.
Then l.62–65 → "cited where its *contents* are described, never as
evidence"; table row l.87 → "A realisation of the substrate, not
circulated; described where its contents bear on a claim, never cited as
evidence for one."

l.134 ("the construction paper's closing list of eleven distinctions")
describes contents and is fine under that rule.

---

## B. The paper's own naming rule, broken about thirty times; six companions cited by description only

l.61: "The short name in the middle column is the only form used below."
Census of forms actually used:

| form used | sites (representative) | table's short name |
|---|---|---|
| "the companion" for *Is* | l.101, 104, 223, 261, 279, 288, 327, 335, 368?, 430, 436, 467, 471, 474, 552, 651, 682, 692, 707, 745, 752, 760, 772, 780, 785, 798, 2755 | *Is* |
| "the companion on mind" / "the companion paper on mind" | l.644, 726, 1251, 1473, 1653, 2017 | the mind companion (used at l.591) |
| "the companion on assessment" | l.538, 1216, 2788, 2799 | the assessment companion (used at l.176, 89) |
| "the companion on frames" | l.368 | the frames companion |
| "the Seldon companion" (for *Seldon*, 02) | l.1951, 2003 | *Seldon* |
| "the Seldon companion" (for 02a) | l.236 | the Seldon grounding |
| "the Seldon paper" | l.1214, 2288 | *Seldon* |
| "the Narrativium companion" / "the Narrativium paper" | l.510, 980, 1213, 1436, 1598, 1982 | *Narrativium* |
| "the Narrative-momentum paper" | l.930 | the momentum paper |
| "the constructive companion" / "the companion construction paper" | l.486, 134 | the construction paper |
| "the companion physics-grounding paper" | l.2746 | the physics companion |

And the paper resolves only *Is* by number (four `IS-` refs). Every other
companion is cited by description. Targets located in the current aux
files (the agent must verify each before use; three could not be found
by grep and are marked):

| line | claim | target |
|---|---|---|
| 236 | Seldon grounding: nervous system implements the manifold in pieces | 02a — **not located by grep; find or drop the specific claim** |
| 461–463 | "The Seldon companion's own definition of a dimension" | `SM-def:` (a dimension definition in 02 — verify label) |
| 483–484 | physics companion's measurement account needs exactly one continuation realised | `PH-sec:measurement` |
| 511 | *Narrativium* locates the axiom's exposure in its own falsifier | `NV-sec:falsifiability` |
| 591 | the mind companion reasons from a rock's being a frame to the universe's being one | `MS-prop:minimal-universe` / `MS-sec:minimal` (verified) |
| 644 | "rules present and not firing is a third condition … the companion on mind names it directly" | 01b l.101–106 (verified text; find the enclosing label) |
| 726 | incompleteness results the companion on mind reports | 01b — find the self-model incompleteness label |
| 930 | the momentum paper names the Narrative | `NM-def:` (03's Narrative definition — verify) |
| 980 | *Narrativium* observes revocation at Δg = 0 | `NV-prop:conferral` (verified) |
| 1092 | physics companion: this universe's entry must come from outside | 01a — find label |
| 1213–1214 | *Narrativium* follows Sen; *Seldon*: a situation is a trap and a capability at once | 04 l.161/650 (find label); `SM-def:trap` + 02 l.823 (verified) |
| 1224 | *Narrativium* types the quantity as a capacity | `NV-rem:narrativium-standing` (verify) |
| 1436, 1598–1599 | spend-and-gain; iterated above unit gain | `NV-prop:spend-gain`, `NV-prop:overshoot` (verified in 04's label list) |
| 1473 | mind companion reads death as decoherence | `MS-rem:death-decoherence` (verified) |
| 1653, 2017 | presented-vs-produced divergence; honest and manipulative acts one operation | `MS-prop:one-influence` and the manipulation proposition at 01b l.618 (verified) |
| 1737 | physics companion's reading of the high-energy regime | `PH-rem:two-decoherences` (verify it is the site) |
| 1951, 2003 | *Seldon*'s "locally complete, generally incomplete" | 02 l.111 (find label) |
| 2203 | physics companion: negative frequency as phase | 01a r42's negative-frequency remark (verify label) |
| 2224, 2280, 2311 | physics companion: c as throughput, one-way speed, constants | `PH-` section labels (verify) |
| 2288 | *Seldon*'s dependent-clock remark | `SM-rem:no-dependent-clocks` (verified) |
| 368 | the frames companion "arrives at from the other direction" | `FR-rem:empty-limit` (05; needs a prefix — `FR-`) |
| 538, 2788, 2799 | assessment companion: the record of the ledger's corrections; what the account can risk; the implementation record | `AS-sec:turned`, `AS-sec:risk`, `AS-sec:implementation` |
| 1216–1217 | assessment companion's "capability is a shipped unit with its own tests" | **not located by grep in 06 r27; find or drop** |
| 2807 | assessment companion's "falsifiable, but not coherently so" | **not located by grep in 06 r27** (06 uses "coherently"? verify; if the phrase was edited out in 06 r27, quote 06's current form) |

**Fix.** `\externaldocument` for `PH-`, `MS-`, `SM-`, `NV-`, `NM-`, `FR-`,
`AS-` (hyperref already after xr-hyper); each row a resolving `\ref`;
every form in the census table normalised to the table's short name. Two
of the three "not located" claims are attributions to 06 of phrases 06
may no longer contain; this is the same defect as 09's "psychological
companion reports at length" and should be resolved the same way — quote
what the companion says now or drop the attribution.

Compile order becomes 00 → 01a/01b/02/02a/03/04/05/06 → 01 → (×3) — 01
already sits after 00; note that 01a, 01b, 05, 06 cite `GE-` labels, so
the cycle needs two full passes to settle. The build script should
encode it.

---

## C. Falsifier 12 is contradicted by the corollary it tests

Item 12 (l.2827) `[shape]` **Self-change is subset-change**: "Fails if …
**or if a graph can self-terminate without acting on the container**."

`cor:locked-in` (l.2036), as restricted in r274–r278 per r273 B.7: "The
restriction to container-supplied frames is not a hedge: termination
propagates along supply and not containment, so **a graph whose supply is
its own can stop itself by withdrawing it**, and the corollary says
nothing of that case."

So the paper now asserts the case the falsifier says would falsify it.
**Fix:** "…or if a *container-supplied* graph can self-terminate without
acting on the container (Corollary~\ref{cor:locked-in}); a self-supplied
graph stopping itself is not a counterexample, being the case that
corollary excludes." Item 25 (termination follows supply) already carries
the supply half correctly.

---

## D. Five proposition/remark pairs restate each other verbatim

Same defect 10 r4 had. The r273 review asked for numbered results; they
were added by copying the remark's sentences above it:

| proposition | remark | verbatim overlap |
|---|---|---|
| `prop:evaluation-writes` l.1338–1348 | `rem:evaluation-writes` l.1355–1367, 1375–1377 | "A read is an operation that returns a datum … the write is the return"; "Evaluation is a write in that plain sense…"; "reversibility is a structural fact about a map and cost is a fact about what supplies a primitive" |
| `prop:handler-relocates` l.1613–1622 | `rem:handler-abuse` l.1630–1651 | the whole proposition |
| `prop:termination-supply` l.1657–1666 | `rem:supply-not-containment` l.1684–1695 | "Termination propagates along the supply relation … three kinds rather than two…" |
| `prop:boundary-by-crossing` l.1714–1722 | `rem:failure-instrument` l.1727–1729, 1745–1747, 1749–1752 | "a frame that never fails discloses nothing…"; "the test and the change are the same operation…"; "every handler installed reduces what failure can teach…" |
| `prop:vacated-three-states` l.1757–1766 | `rem:vacated` l.1782–1794 | the three states, verbatim |

**Fix:** proposition states, remark argues. Cut the restated sentences
from each remark, keep the argument and the instances (Spectre, IEEE 754,
Chesterton, Paine, the accelerator), retitle the remark where it now
duplicates the proposition's title (`rem:supply-not-containment` has the
identical title), and open each remark with "Proposition~\ref{…} follows
from…". About a page.

---

## E. Narrated drafting, surviving sites

| line | phrase |
|---|---|
| 112–113 | "a quarter of this paper's opening section was assessment material until it was moved to the companion written for it" |
| 203–212 | "It has now been measured for the second twice, the second time by a reader trying to cut it: five passes over presentation removed about eleven hundred words … two attempts on content were withdrawn on measurement, and the recommendation that a section's content was one sentence turned out to be false of the section … The first measurement was blunter…" |
| 556–557 | "It was moved out and, until now, was pointed at by nothing, which made it unfindable" (flagged in the 05 review as a cut for 01's next touch) |
| 688 | "The question is basic and the papers had not answered it." |
| 2067 | "Any earlier phrasing suggesting the substrate is *entirely* asynchronous should be read in this sharper form." |

l.203–212 is the one with content: the installation-vs-accumulation
discriminator and the measured result (no argument removable without
losing one) are worth one sentence; the review history is the review
record's. **Fix:** "The discriminator is whether the length is
installation or accumulation, and it has been measured: passes that
removed presentation found no argument removable without losing an
argument. What remains is installation." Delete the rest of each site.

---

## F. Smaller

1. l.2852–2853: "Two commitments below expose the two postulates the
   ledger counts --- the realisation operator, and the destroy/preserve
   distinction, whose falsifier is the no-copy entry since what it tests
   is whether the discarding class is the general one, **which is more
   serious than a mis-tag: an unexposed commitment is not merely graded
   wrongly.**" The final clause has lost its antecedent (it was "an
   unexposed postulate is more serious than a mis-tagged one"). Split:
   the two postulates and their falsifiers; then "An unexposed postulate
   is more serious than a mis-tagged one, so both keep their falsifiers…".
2. The hazard definition is stated four times: l.1229–1231 (forward
   pointer), l.1814–1816 (section opener), l.1829–1836 (`def:info-hazard`),
   l.1978–1979 (naming remark). Keep the definition and the forward
   pointer; the opener and the naming remark should `\ref` it.
3. Item 21 (l.2836) cites `Section~\ref{sec:crossings}` for the
   capability/accessibility distinction; it is `Definition~\ref{def:capability}`
   in `sec:interface`.
4. Unlabelled sections other papers cannot cite: "The minimal graph"
   (l.561), "Discrete sufficiency", "Admissible possibility", "The
   antecedent-state principle", "Recursion and reflection", "First-class
   higher-frame quantities", "Conclusion", and the Axiom −1 section
   (l.214). Add `sec:minimal-graph`, `sec:discrete`, `sec:admissible`,
   `sec:antecedent`, `sec:reflection`, `sec:higher-frame`,
   `sec:conclusion`, `sec:axiom-minus-one`.
5. Underfull boxes at l.87 and l.94 are the companion table's A1 and
   geopolitical rows; `\raggedright` in the `p{}` columns (`>{\raggedright\arraybackslash}p{…}`)
   removes both.
6. "Axiom~$-1$" literal ×~40 vs `Axiom~\ref{ax:no-view}` ×~12. Either is
   fine in 01; pick one. `\ref` survives a renumbering.
7. l.1213 "the Narrativium paper does so following Sen" — 04's citation
   is Sen 1985 (*Commodities and Capabilities*), while 01 cites Sen 1999
   at l.1968; both are right, but the reader who follows 04 finds a
   different Sen. Say "following Sen's capability approach" and let each
   paper's citation stand.

---

## What is right and should not be touched

- `sec:scope`'s evidence-standard sentence (l.65–68), now the set's
  template, and the "why separate documents" argument's *reason*
  (l.99–109).
- `rem:axiom-in-bits` as corrected: the graph "follows as what such an
  account may carry, and not as a demonstration that nothing richer could
  exist"; and the ledger's "Not postulated, a consequence" row now
  matching 00.
- `rem:mdl-ontic`: "the method was never evidence, and calling its loss a
  cost gets the sign wrong."
- `rem:self-edge` and `rem:cohere` as reworked, including the frame-
  relative form ("what does not cohere in a frame does not exist in it")
  and the boundary that keeps it from proving too much.
- `rem:types-forced`: "distinctness is forced; sameness is not", and the
  true-but-derived import being the dangerous case.
- `def:frame` / `cor:frame-dimension` / `def:states` in their new order.
- `rem:funding-category`: category-preservation, not closure.
- `def:capability`, `rem:aperture-purchased` with the Mani/Mullainathan
  evidence, `rem:third-cost`.
- `prop:decoherence-one` and the six remarks split out of it, especially
  `rem:handler-prior-art`'s Scott/Bochvar correction and
  `rem:criticality`.
- `sec:crossings` consolidated: `def:info-hazard`, `rem:admissible-sign`,
  `prop:hazard-threshold` with Crump, `rem:naming-economics` (capability
  uplift drifting to the negative).
- `rem:empirical-instance` with the pre-registration and the bound.
- `sec:prohibition`'s four qualifications on the formal analogue.
- `rem:evolution-compression` as reworked (Ohta, constructive neutral
  evolution, Lynch, the appendix), and "convergent evolution is
  Proposition 20.3 with a name biology gave it first".
- The falsifier list's closing: four entries as one risk, and "the marks
  themselves are revisable".

---

## Suggested order

1. **A** — the A1 sentence, the licence at l.62–65/l.87, and the
   reconciliation with l.2064.
2. **C** — one clause.
3. **B** — the naming census and `xr-hyper` to seven companions (the
   largest item; the three "not located" attributions decided).
4. **D** — five pairs.
5. **E**, **F**.
