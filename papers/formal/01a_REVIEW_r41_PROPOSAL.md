# Review of `01a_graphic_equalisation_physics_grounding.tex` (draft-2026-09-02.1, r41) — proposal for fixes

Scope: the whole file (1885 lines, 30 pp), its log, the companion texts it
attributes claims to (00 r120, 01 r275, 01b), and the repo for the
"unpublished note" it cites. Line numbers are r41. Nothing applied.

Compile: 0 undefined, 0 overfull, all cites/refs resolve. Two cosmetic
warnings (D.1). The physics citations were spot-checked and hold (Khalfin,
Rothe, Wilkinson, Hau, Hensen, Malament, Ali Ahmad, Brukner, Frauchiger–
Renner, Höhn, Müller, Selby, Masanes–Müller, Ehrenfest, Gleason dim ≥ 3);
the phase-averaging arithmetic at l.631–637 is correct. The findings are
about consistency and structure.

---

## A. The three c's arrive 100 lines after the proposition that needs them

`rem:c-indirect` l.195–202 separates **runner c** (the rate the substrate
actually runs; never readable), **unit c** (1 by construction; definitional,
"carries no risk and no content"), and **observed c** (measured, retained,
inferred; contingent). That split is the paper's best tool and it is
introduced *after* everything that conflates them:

- l.94–96 opens by defining c as runner c ("the fixed rate at which change
  is realised — per unit of the substrate's throughput").
- `prop:c-unit` l.101–106 then says "c is each frame's own base rate, its
  change-throughput, so every frame measures its own c as the unit, 1" —
  runner c being read as unit c, which l.197 says never happens.
- The abstract and `cor:reconcile` call the invariance "a theorem"; l.133–137
  says it "does not make c-invariance an empirical prediction … a frame
  counting its own cycles will read 1 whatever the substrate does".
- Falsifier 1 (l.1542–1546): "Fails if two frames in relative motion can be
  exhibited reading *different* c for the same signal" — by the paper's own
  l.164–166, two frames each reading their own unit cannot read differently,
  so the first clause cannot fire. `rem:c-indirect` l.185–186 already states
  the falsifiable form: two frames taking the *indirect* route cannot reach
  different answers for one signal. The list does not use it.

**Fix.** Promote l.195–202 to `\begin{definition}[Three things called $c$]
\label{def:three-c}` placed before `prop:c-unit`. Restate `prop:c-unit`
about unit c only ("a frame's own closure rate is its unit; a unit is read as
1; the invariance of *unit* c is definitional"). Rewrite falsifier 1 in
terms of observed c: "Fails if two frames, each obtaining c by the indirect
route (measurement, retention, inference), are exhibited reaching different
values for one signal." Replace "theorem" with "definitional consequence"
in the abstract (l.42, 52), `cor:reconcile` title and body (l.427–432), and
l.742–743 — the paper's own l.199 calls it definitional, and 01 has just
been through the same downgrade for its own two theorems.

Also: the "budget" of `sec:budget` is runner throughput per cycle, not unit
c. l.140 "The fixed throughput c splits" conflates again. Call the budget
the throughput and say c is its unit.

---

## B. Self-location paragraph contradicts the composition falsifier and 00's new stance

l.1289–1293: "It is the same move as being surprised that the Graph Law
applies to everything: it applies because that *is* what everything,
measured, is — a constitutive identity, not a contingent breadth, the
discriminator being independent re-derivation (Graphic Equalisation's
composition falsifier)."

- 01's composition claim is a *bet* with a falsifier (artefact of
  description); calling it a constitutive identity in the same sentence that
  cites the falsifier is self-undercutting.
- 00 r120 was just corrected to *refuse* "everything is a graph" as a result
  ("the least ontology this account may retain … not what the world is shown
  to lack"). This sentence reinstates the ontic reading one paper over.

**Fix.** Delete the sentence. The self-location argument does not need it;
the preceding sentence ("the observer is what those constants produce")
carries the inversion on its own.

---

## C. Falsifiability: tags, tautologies, and four tests stated in the body but not in the list

1. **Eleven of twelve are `[shape]`**, and the note at l.1533–1538 admits
   they are "the least-audited judgement in this document". By the paper's
   own criterion (shape = loses *reach*), at least these are `[detail]`:
   - **Item 10, Born.** The body calls it "a candidate, not a derivation"
     (l.591), "an attempt, flagged as such" (l.597), "recovered, not forced"
     (l.728). Losing a candidate costs a mechanism. The grounding was
     "brought here" for shapes; Born is "the one place a number is reached"
     (l.72–73).
   - **Item 11, interference.** Depends on item 10's machinery plus
     admissibility-not-armour; a mechanism.
   - **Item 2, one budget two dilations.** Arguably shape. Leave.
2. **Item 3 first clause is a tautology.** "Fails if a genuinely
   dimensionless constant can be set to 1 by unit choice" — dimensionless
   means it cannot. Replace with the body's real test at l.857–859: "Fails on
   exhibition of a dimensionless constant that is a ratio of nothing —
   irreducibly standalone, not expressible as one quantity against another
   even in principle."
3. **Four tests the body states and the list omits.** Add:
   - **One-way speed** (l.367–370): fails on a determination of the one-way
     speed in this universe resting on no synchrony stipulation; what fails
     is the claim that our rules supply no unlocked counter, not the cycle
     unit. `[detail]`.
   - **Decay tail exponent** (l.1241–1245): fails if the long-time exponent
     is universal across systems with different threshold structure; the
     substrate fixes that there is a tail, not its exponent. `[detail]`.
   - **Spectrum floor** (l.1188–1223, l.1247–1251): fails if in-frame energy
     is not a count of quanta for interacting systems — the paper says
     "nothing above survives if that identification fails". `[shape]` for
     that section.
   - **Constancy tracks denominator size** (l.911–917): a measurable
     variation, when found, appears first in constants with the smallest
     denominators against available perturbations, not in the "most
     fundamental" ones. `[detail]`, and the paper's one genuinely novel
     search-strategy prediction — it should be in the list.
4. **Harmonise the `[shape]`/`[detail]` definition** across 00, 01, 01a.
   Three papers now each define it in their own words (01 l.2732; 00 r120;
   01a l.1530–1533). One sentence, verbatim in all three, or defined in 01
   and referenced.

---

## D. Mechanical

1. **Compile warnings.** `T1/lmr/m/scit` ×2: `\textsc{null}` inside the
   italic bodies of `prop:mixed` (l.528) and `prop:second-law` (l.1036).
   Wrap as `\textnormal{\textsc{null}}`. Hyperref "Token not allowed" ×2:
   `$c$` in the section title l.88 and `\textemdash`/`\textbullet` in
   `\date`. Use `\texorpdfstring` as 01 now does.
2. **Five names for paper 01.** "Graphic Equalisation" (29, the declared
   short name at l.29–30), "the substrate paper" (5), "the theory paper"
   (2), "the companion paper" (1), "the companion's" (1). And "the companion
   on the base" (l.487), "the companion's floor" (l.843) for 00, which is
   never named. Fix: one short-name table like 01's, or a sentence at
   l.29–32 naming 00 ("*Is*"), 01 ("Graphic Equalisation"), 01b ("the mind
   companion"), 03 ("the Narrative-momentum paper"); then use those only.
3. **Cross-references to 01 are all by description.** "the cycle-unit
   proposition", "the leak proposition", "the decoherence remark", "the
   no-start-end result", "higher-frame first-class structure", "the
   nothing-compulsory principle", "the no-frame-free-identity theorem",
   "the missing-denominator result", "the well-formedness definition" —
   fourteen sites. 01 and 01s now use `xr-hyper`; do the same here:
   `\externaldocument[GE-]{01_law_of_graphic_equalisation_theory_referenced}`
   and `Proposition~\ref{GE-prop:cycle-unit}` etc. The labels exist
   (`prop:cycle-unit`, `prop:leak`, `prop:decoherence-one`,
   `prop:no-start-end`, `prop:higher-frame`, `rem:nothing-compulsory`,
   `thm:no-frame-free`, `rem:no-denominator`, `def:well-formed`,
   `prop:economics`, `rem:phase-not-time`, `prop:self-governance`,
   `ax:no-view`). Note `thm:no-frame-free` is still a theorem in 01 r275
   (the other one was downgraded); "the no-frame-free-identity theorem" at
   l.1339 stays correct.
4. **Attribution slips.**
   - l.1338–1339 "Axiom −1 holds that two things with no difference that
     makes a difference are the same" — Axiom −1 says there is no operational
     view from nowhere; the identity claim is 01's *consequence* of it
     (sec:scope, "functional identity") and `thm:no-frame-free`. Say so.
   - l.1352–1354 `prop:gibbs`: "entropy is what a frame *distinguishes*" —
     `def:entropy` l.1021 says what it does *not* distinguish. The sentence's
     logic is inverted; rewrite: "mixing entropy counts arrangements the
     frame can tell apart, and an exchange of identical particles is not
     one".
   - l.624 "the no-privilege thesis of the mind companion" — 01b does carry
     it (55 mentions), but the thesis originates as 01's Axiom −1; cite both
     or the origin.
5. **The "unpublished companion note on the Born recovery" (l.719).** It
   exists: `papers/outreach/born_recovery_note.md`, with the axiom mapping
   at `docs/research/engine_substrate/BORN_HILBERT_AXIOM_MAPPING.md`.
   Neither is in the formal set. Decide: (a) promote the note into the
   formal set as a numbered appendix/paper and cite it by short name, (b)
   fold its OPT instantiation (convex states, affine effects, transformation
   monoid, composition — l.717–725) into `sec:amplitudes` as a subsection,
   or (c) keep "unpublished" and say what it contains in two sentences so
   the reader can weigh it. (b) is smallest; (a) is cleanest. Not (c) if
   the note is releasable.
6. **Bibliography.** `khalfin1957` labelled (1958), `minkowski1908`
   labelled (1909): key/label year mismatch, cosmetic. Minkowski "Raum und
   Zeit" *Phys. Z.* 10:104–111; 75–88 is the *Jahresbericht DMV* printing.
   `et al.` vs `et~al.` as in 01.

---

## E. Structure: the mega-remark, the mega-proposition, the twice-told mapping

1. **`rem:oneway` is 165 lines (l.205–371).** Same defect 01 had. It holds
   six separable results. Split:
   - `remark[The one-way speed is an absent quantity, not a hard one]`
     l.207–228 (the known result + closure reason).
   - `remark[The inaccessibility is rule content, not a theorem]`
     l.230–265 (the N-steps-per-cycle qualification + economic reason).
   - `proposition[Closure sorts three cases]` l.265–290 — two-way closes;
     absolute one-way does not; the same-path ratio closes at the
     comparison. This is a *result* and should be numbered.
   - `remark[Reichenbach and Malament are the two halves]` l.313–339.
   - `remark[One move: removing primitive time]` l.341–370 (the family +
     sizing + falsifier).
   l.292–311 (Bell/no-signalling) belongs in `sec:entanglement`, not here.
2. **`prop:second-law` is 40 lines** with an 8-line parenthetical in its
   first sentence and three "separations" inside the statement. Statement =
   three sentences (discarding writes demote structure below the aperture;
   the arrow is no-copy; free continuation is the neutral case). Then
   `remark[Absence is not residual]` (l.1049–1054),
   `remark[The increase is one-sided accounting]` (l.1056–1063),
   `remark[A relocation of the arrow's source, not a new arrow]`
   (l.1065–1070).
3. **`prop:spectrum-floor` (35 lines) and `prop:decay`** carry their
   arguments inside the statement ("That is the claim, and the
   qualification is load-bearing"). Statement, then proof/argument outside
   the environment, as 01 now does.
4. **The reconstruction mapping is told twice.** l.674–693 ("The framework
   *appears* to supply those axioms … *If* that mapping holds") and
   l.695–737 ("the mapping has *now* been worked axiom by axiom … with a
   result worth stating"). The second supersedes the first and narrates the
   drafting ("has now been"). Merge into one status statement.
5. **"Honest boundary" ×5, "honest residual" ×2.** Each is a residual list
   for its section. Collect `sec:amplitudes`' four residuals into one
   enumerated paragraph: (i) uncoupled → additivity + unitarity rigour; (ii)
   complex-over-real is self-located, not forced; (iii) GPT hygiene
   conditions; (iv) the OPT instantiation (D.5).
6. **`sec:collapse` is 12 lines** and `sec:relativity-collapse` content is
   restated at l.739–757. Fold `sec:collapse` into the reconciliation
   subsection or vice versa.

---

## F. Physics-side flags (not errors; places a physicist presses)

1. **l.1178 "seven to ten [lifetimes] for β between ½ and 1, on the exact
   threshold form".** Solving e^{−x} = x^{−2(1+β)} without the tail's
   prefactor gives ~4.5 to ~8.6, and the real prefactor (∝ (Γ/ΔE)^k ≪ 1)
   pushes the crossing later. The paper's own rule is "anything with a
   number is weak" (l.382). Either show the estimate with its prefactor or
   say "many lifetimes in, of order ten as observed".
2. **`prop:one-time` "decoherence and stability" selects one time axis**
   (l.1315–1316) — asserted, no citation, and unlike the N = 3 case there is
   no Ehrenfest-style result to lean on. Either cite (e.g. the
   ultrahyperbolic-instability literature, Tegmark 1997) or mark it a
   conjecture.
3. **Equivalence principle "coincides by construction" (l.424–425).** Fair
   as shape, but the falsifier for item 2 asks for the two dilations to "be
   exhibited as the same budget" — say what would count as exhibiting.
   Concretely: the paper predicts no third dilation channel; a clock slowed
   by something that is neither motion nor change-load falsifies it.
4. **`sec:dimensions` l.1299–1307 and l.1334.** "a rock is a universe, and
   the minimal universe does without [time, gauge group, constants,
   dimensions]" leans on 01b. 01 r275 `rem:rock` now says explicitly that
   nothing there claims a grain at which nothing runs. 01a's "its rules
   exist but are inert" is the *fires-no-r* reading 01 allows, so it is
   consistent — but say "inert at the grain at which it is a rock" so the
   reader does not hear a floor 01 has withdrawn.

---

## G. Prose (representative)

- l.1033–1045: the parenthetical inside the proposition (E.2).
- l.265: one 60-word sentence beginning "The failure to guard against…";
  split.
- l.287: "closing it off by adding that nothing here supplies an outside
  would be wrong, and wrong against this paper's own machinery" — the
  sentence argues against an edit nobody sees; state the positive only.
- l.360 "Sized honestly, because the parts of this that are old are most of
  it" — fine, keep; it is the right register for the set.
- l.1123 "The last step is the one that earns the proposition" — after a
  proposition with no numbered steps.

---

## Suggested order

1. **A** — the three-c definition first, then the proposition, abstract,
   corollary, and falsifier 1 fall into line. One section.
2. **B** — one sentence deleted.
3. **C** — re-tag, fix item 3, add four falsifiers, harmonise the
   definition across 00/01/01a.
4. **D.2–D.3** — names and `xr-hyper` (mechanical, and stops the next
   drift).
5. **D.5** — decide what to do with the Born note.
6. **E**, then **D.1/D.4/D.6**, **F**, **G**.
