# Review of `01b_graphic_equalisation_mind_and_self_grounding.tex` (draft-2026-09-02.1, r39) — proposal for fixes

Second pass. Scope: the whole file (1910 lines, 31 pp), its log and aux,
the r38 review and what r39 did with it, and the companions it refers to
(01 r278, 01a r42, 03 r29, 04 r20). Line numbers are r39. Nothing applied.

Compile: 0 warnings, 0 overfull, 77 bibitems all cited (two flagged by a
naive grep are cited via `\citet[…]{}` and `\citealp{}`), no `??`, all
`GE-` refs resolve, by-name check clean. r39 did what r38 asked: the two
compression remarks moved into their own section with the anchoring
fixed; `rem:reader` split and `sec:other-models` created with
`prop:other-model`; the Axiom −1 attributions corrected; `xr-hyper` to 01
at twelve sites; the evidence standard adopted once and the three ad-hoc
disclaimers removed; the tenfold fixture located and reported with its
numbers and limits; three influence falsifiers and three promoted
predictions added; item 8 split; the tags paragraph harmonised;
propositions separated from their arguments; the bibliography sorted;
Wolfram cited at first use. The citations spot-checked again hold. **What
this pass finds: the paper resolves 01 by number and still cites the
physics companion and *Narrativium* by description at nine sites and 01
at ten more; ten sites narrate the paper's own drafting, most of them in
the death section; the falsifiability preamble carries the "fast call"
sentence 01a also carried; and three results in the body have no
falsifier.**

Seven of 01b's labels are cited by other papers via `MS-`
(`prop:minimal-universe` ×2, `sec:minimal`, `rem:realisation`,
`rem:death-decoherence`, `prop:selfmodel`, `prop:one-influence`,
`prop:manipulation-structural`). All must survive under the same names
and kinds; 01 r279 (in flight) will add more.

---

## A. Cross-references by description, and one name off the table

`xr-hyper` resolves `GE-` only. Sites and targets (verified in the current
aux files unless marked):

| line | claim | target |
|---|---|---|
| 113–114 | "the physics companion develops this as why a rock has no time" | `PH-sec:dimensions` |
| 147–150 | the physics companion's contingent-not-necessary verdicts (dimensions, gauge group, constants, arrow, $c$) | `PH-sec:dimensions`, `PH-rem:gauge-contingent`, `PH-prop:dim-boundary` |
| 163–165 | the physics companion states the signature as succession against position | `PH-sec:dimensions` (the $3+1$ paragraph) |
| 1393–1394 | the physics companion's dissolutions: the special observer, the initial state | `PH-cor:observer`, `PH-prop:self-location` |
| 746 | "the overshoot remark of the Narrativium paper" | `NV-prop:overshoot` (04 l.354) or the remark at 04 l.345 — verify which carries "capacity beyond what its situation requires" |
| 1503–1504 | "the same risk as the Narrativium paper's 'no frame-free accounting'" | `NV-prop:no-sum` |
| 116 | Graphic Equalisation's self-similarity: a primitive is graph-that-runs at every scale | `GE-prop:runner-recursion` |
| 349 | Graphic Equalisation's dissolved pointer — you change yourself, the supergraph deforms you | `GE-prop:no-direct-self-alter` |
| 376 | "(Narrative momentum)" for retaining is free / altering is paid | `GE-prop:economics` (or `NM-def:free-continuation`) |
| 395 | Graphic Equalisation's distinction between the absent and the residual | `GE-def:aperture` + `GE-def:change-grammar` |
| 998 | rule-actions are pointers, work done once | `GE-prop:runner-recursion` (the pointer paragraph follows it) |
| 1184–1186, 1283–1286 | "Graphic Equalisation's founding axiom … every distinction, measurement and identity relation is made in some frame" | `GE-ax:no-view` |
| 1254, 1262 | the tombstone of Graphic Equalisation's account; already prices a tombstone | `GE-prop:vacated-three-states` |
| 1402 | Graphic Equalisation's Axiom −1 applied to observers | `GE-ax:no-view` |

**Fix.** `\externaldocument[PH-]{01a_…}` and `[NV-]{04_…}` (and `[NM-]{03_…}`
if the l.376 row goes to 03); each row a resolving `\ref` with the paper
named. Verify every target before use. **Naming:** "the Narrativium paper"
(l.746, 1504) → *Narrativium*, per 01's table; add *Narrativium* to the
box's naming sentence (it names only Graphic Equalisation and the physics
companion today). Compile order: 01, 01a, 04 before 01b; 01 r279 cites
`MS-`, so a second pass over 01 settles the cycle.

---

## B. Narrated drafting — ten sites, most in the death section

The set's rule since 7309f2b9: a paper is what it says now. Surviving
sites:

| line | phrase |
|---|---|
| 663 | "Both propositions are claims about a substrate, **so they were checked against one, and what follows is what that check compared and what it found**" |
| 841 | "Remark~\ref{rem:reader} **left one thread hanging**, and it is the one Section~\ref{sec:death} needs" |
| 1118 | "A second position **needed checking, and checking it moved the objection rather than confirming it**" |
| 1127 | "That **was expected to supply an objection** to the line drawn above and does not, for a reason worth recording" |
| 1136 | "The objection Parfit does pose is a different and larger one, **and this section has not engaged it**" |
| 1153–1154 | "One prior position is close enough to require engagement rather than a citation, **and this section cited it as an ally on a different point while leaving the disagreement unstated**" |
| 1181 | "the appearance of contradiction comes from leaving the drawing unstated, **which this section had done**" |
| 1199–1200 | "This section runs on coherence throughout **and has not said what that connects to, which is worth repairing**" |
| 1209 | "Two consequences that the general treatment supplies **and this section did not have**" |
| 1419–1422 | "**The marks were assigned in a single pass … the least-audited judgement in this document … a fast call**" |

Each is a one-clause rewrite: state the result, drop the report of
having lacked it. l.663 → "Both propositions are claims about a
substrate; the comparison below is what the substrate shows." l.1118 →
"Parfit's causal condition is the position nearest the line above, and it
does not supply the objection it appears to." l.1153 → "One prior
position is close enough to require engagement rather than a citation."
And so on.

---

## C. The falsifiability preamble

l.1413–1422: 01's definition sentence is present and verbatim (good). Two
additions after it should go: "The distinction is the one
Section~\ref{sec:scope} rests its epistemic claim on" — 01b's `sec:scope`
makes no `[shape]`/`[detail]` claim (that clause was written for 01's
scope section; 00 r122 and 10 r5 dropped it); and the "assigned in a
single pass … fast call" sentence (B, last row). The list follows the
definition sentence directly, as in 08 r2 and 09 r92.

---

## D. Three results with no falsifier

1. **`prop:other-model`** (l.900–913) and the forward-direction prediction
   (l.933–937, "the claim here is *untested*"). The section says the test
   is the forward one: what an author would have made of something they
   never addressed, scored against the author. Add `[detail]` **A model
   of another is generative, not only discriminative.** Fails if readers
   who reliably discriminate an author's work from imitations are at
   chance on forward prediction of that author on unseen prompts scored
   against the author's own answers — which would make the model
   discriminative and the composition idle. Untested; the design is the
   Schwitzgebel one with the tell removed.
2. **`rem:boredom`** (l.745–777), "boredom is Narrative minus pressure":
   add `[detail]` fails if boredom is relieved by input that produces no
   residual — saturating, predictable input — or persists under input that
   does; that is, if what boredom tracks is quantity rather than residual.
3. **`rem:comm-calibrated`** (l.779–821), the trajectory measure: add
   `[detail]` fails if a calibrated supply and a resolving source are not
   separated by the cost-weighted net-to-gross ratio while every local
   signal reads alike — the fixture's own result, stated as the commitment
   it is, with the fixture's limits (synthetic, one run per arm, renewal
   schedule supplied) carried in the item.

Also item 17 (l.1503–1508) carries "(Axiom −1 in this paper's vocabulary,
and the same risk as the Narrativium paper's 'no frame-free accounting')"
as an italic parenthetical inside the item; after A it is
"(Graphic Equalisation's Axiom~\ref{GE-ax:no-view}; *Narrativium*'s
Proposition~\ref{NV-prop:no-sum} carries the same risk)".

---

## E. Smaller

1. `posix2017` is labelled "IEEE(2017)" and filed under P; file under I.
2. Bibitem labels use "et al." (`Alderson-Day et al.(2017)`, `Campbell et
   al.(2025)`, …); the set uses `et~al.`. Cosmetic, eleven entries.
3. l.525–529 (the `sec:compression` lead-in) explains where the two
   remarks sit and why: "Neither is a result about minds in particular,
   and neither is used by anything above; they are placed here because
   this is the paper that carries the aperture material they turn on."
   That is the right decision stated as a placement note. One clause
   suffices: "Both are about apertures, which is why they sit in this
   paper."
4. l.1516–1521 scope note: "This sits outside the list because nothing
   about the world could settle it: it is falsified by a misreading, which
   is a fact about a reader and not a result." The set's scope notes (08,
   09a, 10) carry the first sentence only. Trim.
5. `\texorpdfstring` on the `\date` dashes (l.17) — 01b is now one of two
   released papers without it.

---

## What is right and should not be touched

- `sec:minimal`'s rules-present-not-firing reading, the one-directional
  inference (l.128–131), and "the rock's inertness is not a defect in the
  example but the whole of its content".
- `prop:run-record`, `prop:free-will` and `rem:three-frames`:
  "foreknowledge is always post-run record-holding, never pre-run
  read-ahead".
- `rem:detection` (proxy dissociation, measured) and `prop:grounding`
  (anti-foundationalist without being flatly coherentist).
- `sec:selfmodel`'s three sources of incompleteness stated once, and
  `prop:selfmodel`'s expression/aperture split; `rem:transparency` as
  agreement-with-a-residual-disagreement; `rem:realisation`'s "the self as
  modelled did not change; the modelling did".
- `sec:communication` entire: the two propositions and their joint
  reading, `rem:comm-engine` as measurements with scope, `rem:comm-horizon`
  reciprocating 01, `rem:comm-calibrated`'s negative result (recurrence
  runs the wrong way), `rem:comm-prior`'s Austin correction.
- `sec:other-models`: Genette given the generativity in full; "so the
  generativity is prior art, fully; only the personification and the
  truth condition attaching to it are not"; the Porter–Machery
  below-chance result used correctly.
- `rem:parfit` and `rem:hofstadter` (threshold per coherence, gradient
  across coherences), `rem:death-decoherence`, `rem:death-computing`'s
  "an implementation is free to add rules to suit" and the
  reachability/re-runnability caution.
- `sec:prior-art`'s "tiny and different in kind … orthogonal to the
  sequence, not further along it".

---

## Suggested order

1. **A** — `xr-hyper` to 01a and 04, the extra 01 sites, the one name.
2. **B**, **C** — narration and the preamble.
3. **D** — three falsifiers.
4. **E**.
