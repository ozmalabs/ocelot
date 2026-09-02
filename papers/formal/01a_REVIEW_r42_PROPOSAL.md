# Review of `01a_graphic_equalisation_physics_grounding.tex` (draft-2026-09-02.1, r42) — proposal for fixes

Second pass. Scope: the whole file (1987 lines, 31 pp), its log and aux,
the r41 review and what r42 did with it, and the companions it refers to
(00 r122, 01 r278, 01b r39, 01d r1, 03 r29). Line numbers are r42.
Nothing applied.

Compile: 0 warnings, 0 overfull, 53 bibitems all cited, no `??`, all
`GE-` refs resolve, one by-name mention without a `\ref`. r42 did what
r41 asked: `def:three-c` before `prop:c-unit`; "theorem" → "definitional
consequence"; falsifier 1 in terms of observed c; the self-location
sentence deleted; items 10–11 re-tagged; the tautology in item 3
replaced; four falsifiers added; `rem:oneway` split into five results;
`prop:second-law` split; the Born note promoted and cited; the physics
flags (crossing estimate, one-time conjecture, third dilation channel,
inert-at-the-grain) all handled; `\texorpdfstring`; the arithmetic
checks. The physics in the paper holds on re-reading (phase-averaging
arithmetic, Paley–Wiener direction of the Khalfin argument, the
threshold-exponent relation, Ehrenfest, the metre definition, Hau).
**What this pass finds is small: the paper resolves only 01 by number and
cites four other companions by description; one companion name differs
from 01's table; the falsifiability preamble narrates its own drafting;
one falsifier is unfalsifiable by the paper's own Axiom; two paragraphs
01 r279 will need to cite carry no label; and one bibliography entry
conflates two papers.**

Seventeen of 01a's labels are cited by other papers via `PH-` (`sec:c-rate`,
`sec:budget`, `rem:oneway-rule` ×3 each; `cor:nonlocal` ×2; eleven more
×1). All must survive under the same names and kinds. 01 r279 (in flight)
will add more.

---

## A. Four companions cited by description; one name off the table

`xr-hyper` resolves `GE-` only. By-description sites and their targets
(verified in the current aux files unless marked):

| line | claim | target |
|---|---|---|
| 88–92, 746, 1402–1406 | the minimal-universe argument: a rock is a universe, the minimal universe does without time/gauge/constants/dimensions | `MS-prop:minimal-universe` (01b l.120, "What the rock shows is not compulsory") + `MS-sec:minimal` |
| 200 | a frame's aperture limit leaves no direct residual and is inferable from imposed change and trace (the mind companion) | 01b — find the label (grep 01b for "trace" / "imposed change"); if none, state on 01a's own terms |
| 361 | Graphic Equalisation, *Time is not a dimension of the substrate* | `GE-sec:time-not-primitive` |
| 437 | the impulse relation of the momentum paper, mass as the exchange rate | `NM-rem:impulse` (03 l.313) |
| 503–505 | *Is* holds that what stands in relation without transformation or grammar can be observed and cannot observe | `IS-prop:one-way` |
| 609–611 | the momentum paper's directional momentum $p=\phi_W(\mathcal N)\hat{\mathbf d}$ | `NM-def:narrative-momentum` (03 l.148; the boxed form is l.144) |
| 648–649 | the momentum of Narrative-momentum, free continuation | `NM-def:free-continuation` |
| 729, 737, 781–786 | the Born note: the axiom-by-axiom mapping; the genre-match rating; the OPT instantiation | `BN-sec:axioms`, `BN-prop:` (the crux-axiom proposition at 01d l.185), `BN-sec:level0` / `BN-prop:` (01d l.132), `BN-sec:residuals` |
| 782 | the momentum paper's first law | 03 — find the label (`sec:law` or a proposition inside it) |
| 893 | *Is*'s floor, made explicit there | `IS-sec:graph` |
| 998 | Graphic Equalisation's discrete sufficiency read at the resolution axis | `GE-hyp:discrete` (this is the one by-name mention the checker flags) |
| 1033 | the free-continuation default of Graphic Equalisation's momentum | `GE-rem:collapse-write` |
| 1172 | Graphic Equalisation's result that the unit of inferred time is a cycle and requires closure (inside `prop:decay`) | `GE-prop:cycle-unit` |

**Fix.** `\externaldocument[IS-]{00_is}`, `[MS-]{01b_…}`, `[NM-]{03_…}`,
`[BN-]{01d_…}`; each row a resolving `\ref` with the paper named. Verify
every target before use. Compile order: 00, 01, 01b, 01d, 03 before 01a;
01 and 01c cite `PH-`, so a second pass over them settles the cycle.

**Naming.** The box (l.36–38) says "the Narrative-momentum paper"; 01's
companion table, which is the set's canonical list, says **"the momentum
paper"**. Six sites (l.37, 437, 609, 648, 782, and the box). Use the
table's name. Everything else in the box matches the table.

---

## B. The falsifiability preamble narrates its own drafting

l.1608–1613: "Graphic Equalisation has carried these marks for some time
and the groundings did not, which had the discipline applied where the
risk is smallest … **They were assigned in a single pass under the rule
just stated, and are the least-audited judgement in this document** — a
reader who thinks one is marked in the flattering direction is
disagreeing with a fast call, not an argued position."

That is the review record's sentence, not the paper's, and it undercuts
the list it introduces. The tags have now been audited twice (r41 C.1
re-tagged two). **Fix:** keep 01's definition sentence (l.1603–1607,
already verbatim) and the scope-caveat sentence (l.1614–1615); delete
l.1608–1613.

---

## C. Falsifier 9 cannot fail, by the paper's own Axiom

Item 9 (l.1659–1664) `[shape]` **The initial state is a seed, answered by
self-location.** "Fails if 'why this seed / constant / gauge group' can
be posed from a trans-frame standpoint that could have obtained a
different one — if there is an observer-independent 'we' separable from
the seed."

Axiom −1 denies that standpoint; so the falsifier asks for the thing the
account's base axiom rules out, which is the pattern 01 handles by
listing such claims *after* its falsifier list as "consequences rather
than wagers" (01 l.2846–2848). `prop:self-location` is a consequence of
Axiom −1 plus frame-relative identity, and `prop:past-hyp` (the Past
Hypothesis is a seed) is the wager that could actually fail. **Fix:**
split. Item 9 becomes `[detail]` **The Past Hypothesis is a seed**: fails
if the low-entropy initial condition is derived from within — from the
dynamics without a boundary condition imposed from a container
(`prop:past-hyp`). Self-location moves to a one-sentence paragraph after
the list, marked as a consequence rather than a wager, as 01 does for
"admissibility is not armour".

---

## D. Two paragraphs 01 r279 needs to cite carry no label

The 01 review (`01_REVIEW_r278_PROPOSAL.md` §B) asks 01 to resolve its
references to this paper by number. Two of 01's targets are unlabelled
prose here:

- l.388–397, the accelerator paragraph ("energy is the price of forced
  concurrency, and forced concurrency is frame decoherence") — 01 l.1737
  cites "the physics companion's reading of the high-energy regime".
  Make it `\begin{remark}[Energy is the price of forced concurrency]
  \label{rem:forced-concurrency}`.
- l.1268–1283, the sign-is-orientation paragraph ("Negative time does not
  exist and phase does … one premise applied twice") — 01 l.2203 cites
  "the physics companion carries the worked case: a negative frequency".
  Make it `\begin{remark}[The sign of a frequency is an orientation, not a
  rate]\label{rem:sign-is-phase}`, leaving `prop:spectrum-floor` and the
  count paragraph as they are.

Also 01 l.1092 cites "the physics companion: this universe's entry must
come from outside" → `sec:cosmology` l.1322–1329 carries it; a label on
the paragraph (`rem:entry-from-outside`) or the existing `sec:cosmology`
both work, and the 01 agent has been told to look. Adding the two remarks
above is the useful part.

---

## E. `sec:collapse` is still told twice

r41 E.6 asked for the 12-line `sec:collapse` (l.453–464) to be folded
into the reconciliation subsection or vice versa. r42 left both: the
map/event seam is stated at l.454–461 and again at l.793–796 ("Quantum
collapse and relativity … are already the in-frame *event* and the
cross-frame *map* of one change-substrate joined at $c$"). `prop:wigner`
(l.479) cites `sec:collapse`. **Fix:** keep `sec:collapse` (it is the
first statement and is cited), and reduce l.793–796 to the cross-reference
plus the one new clause (Born on the same primitives). Three lines.

---

## F. Bibliography

1. `duff2002`: the entry gives arXiv:hep-th/0208093 (Duff's solo
   "Comment on time-variation of fundamental constants", 2002) and then
   parenthetically names the Duff–Okun–Veneziano "Trialogue on the number
   of fundamental constants", which is a different paper (JHEP 03 (2002)
   023, arXiv:physics/0110060). The text at l.927 and l.979 attributes
   the position to "Duff's position in the Duff–Okun–Veneziano exchange".
   Cite the Trialogue as its own entry (`duff2002trialogue`) at l.979 and
   the Comment at l.927, or one of them consistently.
2. `ignatowsky1911`: *Physikalische Zeitschrift* 11:972–976 is the
   **1910** volume. Verify and correct the year in label and entry.
3. Ordering: `hoehnwever2017` (Höhn and Wever) is placed before
   `hoehn2017` (Höhn); alphabetical-by-label puts the single author
   first. Cosmetic.

---

## G. Smaller

1. l.581–584 "So 'impossible' was the wrong word twice over" — 06 r27
   cites this line as its `PH-` target for "impossible was the wrong word
   twice over" (06 review §D.2). Give the paragraph (l.572–584) a label
   (`rem:ascent-different-somewhere`) so 06 can resolve it; the sentence
   itself is fine.
2. l.1240 "many lifetimes in, of order ten as observed: Rothe report the
   crossing around ten" — "\citet{rothe2006} report" is missing the
   verb's subject article style used elsewhere; minor. And "The exact
   crossing depends on the tail's prefactor and is not estimated here" is
   exactly right.
3. Item 12 (`[shape]`, l.1680–1686) carries a five-line parenthetical
   listing what is *not* claimed and what the mind companion carries.
   Move the parenthetical to the scope note after the list; keep the
   falsifier to its one clause.
4. `prop:decay` (l.1169–1177) body contains the by-description reference
   (A, l.1172); after A it becomes a `\ref` inside a proposition, which
   is fine.

---

## What is right and should not be touched

- `def:three-c` and `prop:c-unit` as restated, and the paragraph at
  l.139–159 on what is and is not stipulated (the Gorard contrast, and
  "the invariance costs nothing to assume because it is a fact about
  self-measurement, and the variation in cycle length … carries the
  physics").
- `rem:c-indirect` (a clock cannot time its own tick; the indirect route
  is three centuries old; the metre definition).
- `rem:oneway` → `rem:oneway-rule` → `prop:closure-three` →
  `rem:reichenbach-malament` → `rem:one-move` as a sequence; especially
  "definable is not measurable, and unmeasurable is not arbitrary".
- `rem:two-decoherences`: einselection imported, not recovered.
- `sec:amplitudes`: "recovery, not derivation, is the honest verb", the
  four residuals collected, and complex-over-real as self-located.
- `prop:dim-boundary` and the constancy-tracks-denominator search
  strategy.
- `sec:decay` entire as reworked: the deviation required rather than
  tolerated; the exponent principled-not-fixed; the "one identification
  is doing the work" boundary.
- `rem:spin-stat`: the identity argument does not select fermions.
- `sec:prior-art`: D'Ariano–Tosini and Knuth–Bahreyni given their
  priority; Müller 2020 as "the most direct competitor"; QBism as the
  foil; constructor theory as competition on the Born rule.

---

## Suggested order

1. **A** — `xr-hyper` to four companions and the one name.
2. **D** — the two labels 01 r279 needs (coordinate with the 01 agent:
   it will cite `sec:` labels if the remarks do not exist yet).
3. **B**, **C** — the preamble and item 9.
4. **E**, **F**, **G**.
