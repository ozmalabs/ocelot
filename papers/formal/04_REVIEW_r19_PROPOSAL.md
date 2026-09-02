# Review of `04_narrativium_theory_referenced.tex` (draft-2026-09-02.1, r19) — proposal for fixes

Scope: the whole file (920 lines, 17 pp), its log and aux, and 01 r278 /
02 r26 / 03 r28 for what it attributes to or duplicates from them. Line
numbers are r19. Nothing applied.

Compile: 0 warnings, 0 overfull, all 39 citations resolve. The
palaeontology and evolutionary citations were spot-checked and hold
(Coates–Clack 1990/1991, Cloutier 2020, Dickson 2021, Sanchez 2016,
Stewart 2022 *Qikiqtania*, Bicknell 2022, Lamsdell 2016, Avise 1994, Nong
2021, Lehman–Stanley 2011, Gould–Vrba, Schluter, de Vries). The core of
the paper — measurement is not expenditure, no conservation law,
spend-and-gain gated by feasibility, conversion is a stated κ with an
invariance test, the horizon as a controllability boundary — is tight and
is not questioned. The findings are a 160-line remark that duplicates 03,
one contradiction with 01, one stale falsifier note, one non-releasable
citation, and cross-reference hygiene.

---

## A. `rem:overshoot` is 160 lines and a third of it belongs to 03

l.342–504. Contents in order: overshoot as rate carried past the balance
point; three modes of spending excess (exaptation, niche construction,
niche choice); agency as accumulated unspent capacity (a position in a
live dispute, stated as such — good); equilibrium is a limit not a state;
the horseshoe-crab case; the tetrapod case (*Acanthostega*, *Elpistostege*,
*Qikiqtania*); natural selection is half of evolution; arrival of the
fittest; **evolutionary momentum (Kirkpatrick–Lande, McAdam–Boutin,
Thorne)**; need does not generate structure; novelty search; three
qualifications; a caution on stasis.

The evolutionary-momentum paragraph (l.458–472) is 03's `sec:evolutionary`
restated with the same three citations, and ends: "no remaining novelty is
claimed here, **the momentum paper's own having been withdrawn**" — a
sentence narrating another paper's revision history. 03 r29 (in progress)
carries this grounding with its limits; 04 should point at it, not
duplicate it.

**Fix.** Split into numbered pieces and delete the duplicate:
- `\begin{proposition}[Overshoot is loop gain above unity]\label{prop:overshoot}` —
  from `rem:supercritical`'s definition (l.292–295) + the first paragraph
  of `rem:overshoot`: overshoot is change whose products exceed their
  cause; it produces capacity in excess of requirement; that excess is
  spendable at three removes.
- `remark[Equilibrium is a limit, not a state]` — l.378–393.
- `remark[Two cases: the horseshoe crab and the tetrapod limb]` —
  l.394–433, with the stasis caution (l.500–503) attached.
- `remark[Arrival of the fittest: where this account sits]` — l.435–457 +
  l.474–491, stating the EES position as a position.
- **Delete** l.458–472 and replace with one sentence: "The
  continued-change-after-selection-ceases case is the Narrative-momentum
  paper's evolutionary grounding (`NM-sec:evolutionary`), with its limits
  stated there."
- The three qualifications (l.492–499) attach to the cases remark.

Also `rem:overshoot-lead` (l.324–340) opens "The remark that follows
arrived in the theory paper's section on classification, which was the
wrong home for it … It is reproduced here unchanged in substance" —
narrated drafting about where a remark used to live. Cut the first
paragraph. The second paragraph (the rate reconciliation) duplicates 01's
`rem:no-denominator`, which already carries the provenance/type
resolution; reduce to one sentence citing `GE-rem:no-denominator`.

---

## B. Contradiction with 01 on the subset-change claim

l.617 (`sec:cross-frame-deformation`): "Graphic Equalisation carries as a
falsifiable commitment, **a pattern rather than a strict universal
restriction**, that there is no reach across a gap, outward effect being
propagation from one's own subset."

01 r278 `rem:writeability` l.1397: "The *structural* claim — that a graph
affects its container as a subset of it and not by some other route — is
**a strict restriction and is committed to as one**." What 01 carries as a
pattern is the *distribution of costs*, not the subset-change claim. 04 has
the two halves swapped. **Fix:** "Graphic Equalisation commits to this as
a strict restriction (`GE-prop:no-direct-self-alter`; its falsifier
*Self-change is subset-change*); what it carries as a pattern is which
writes are free and which are paid."

---

## C. Falsifier 5's note is now false

l.677–680: "*(This is Axiom −1 in this paper's vocabulary. Worth noting
that the substrate paper carries no commitment for that axiom directly, so
the axiom's exposure lives in entries like this one…)*" 01 r278 carries
`[shape]` **The relativity of grounding is a consequence, and can fail as
one**. Replace the parenthetical with one sentence after the list: "Item 5
is Axiom −1 in this paper's vocabulary; 01 carries the axiom's own
exposure (*The relativity of grounding is a consequence*), and this entry
and the mind companion's *No frame is privileged* are the same risk stated
where it bites."

Other falsifier items:
1. **"On the tags" (l.662–670)** is the pre-harmonisation text. Replace
   with 01's sentence verbatim (trailing clauses dropped); keep "On a
   claimed class".
2. **Missing:** the supercritical regulation constraint ("a compounding
   loop with no slow fraction cannot be regulated, only contained or
   allowed", l.301–302) — `[detail]`, fails on a regulated compounding
   loop with no slow fraction; "Equilibrium is a limit, not a state" —
   `[detail]`, fails on a coupled frame observed at zero forcing over an
   interval; `prop:cross-frame-asymmetry` — `[shape]`, fails if a contained
   frame can hold its container whole; `hyp:delayed-failure` ✓ has one.
3. Item 9's wording paragraph is right and should stay.

---

## D. The construction paper is cited for a claim

l.271: "This is the same gauge condition **the companion construction
paper** imposes on relative weighting, applied one level up." Same defect
03 has. A1 is not releasable. **Fix:** "This is a gauge condition — the
conclusion must be invariant under the admissible choices of κ — applied
one level up from the choice of basis."

---

## E. Cross-references and naming

1. **Names**: "Graphic Equalisation" (7), "the substrate paper" (4), "the
   theory paper" (3), "the foundational paper", "the companion
   construction paper", "Seldon Manifolds", "Narrative Momentum", "the
   momentum paper", "the Narrative Momentum companion", "the physics
   companion", "the mind companion". Draft box generic. Add the naming
   sentence (Graphic Equalisation; *Seldon*; the momentum paper — 01's
   table name; the physics companion; the mind companion) with the
   "inherits their definitions…" clause; collapse the rest.
2. **`xr-hyper`**, all targets present: to 01 — founding axiom (l.215 →
   `GE-ax:no-view`), higher-frame principle (l.630 → `GE-prop:higher-frame`),
   cost of the write (l.197 → `GE-prop:economics`), minting is a rule
   (l.625 → `GE-cor:mint-is-grammar`), residual result (l.684 →
   `GE-prop:residual-inadmissible`), Γ_Wc (l.617 → `GE-prop:two-gates`),
   criticality (l.297 → `GE-rem:criticality`, which already points back
   here), handler (l.302 → `GE-prop:handler-relocates`), missing
   denominator (l.330 → `GE-rem:no-denominator`), self-change
   (`GE-prop:no-direct-self-alter`, B). To 02 — dimension/value typing
   (l.85, 102 → `SM-def:dimension`), standing remarks (l.70 →
   `SM-rem:optional-machinery`), Muchness (l.134 → `SM-def:muchness`). To 03
   — two currencies (l.264 → `NM-rem:currencies`), evolutionary grounding
   (A), narrative revision (l.510 → `NM-def:narrative-revision`). To 01a —
   change-budget (l.619 → `PH-sec:budget`).
3. **The term itself is uncredited.** "Narrativium" is Pratchett's
   (*The Science of Discworld*, Pratchett, Stewart and Cohen, 1999), and
   nowhere in the set is the borrowing acknowledged. One sentence in
   `sec:dependencies` and a bibitem. The word is doing real work here and
   the source is a fact a reader will know.

---

## F. Structure and mechanical

1. `rem:supercritical` (l.286–322) and `rem:overshoot` state the loop-gain
   idea twice; after A, `prop:overshoot` carries the definition and both
   remarks reference it.
2. Untitled remark l.125 — title ("Discrete measure, continuous
   grounding") and label.
3. Bibliography is two blocks: the evolutionary entries alphabetical, then
   Aubin/Bourdieu/Coleman/Goldstein/Holling/Kalman/Sen appended unsorted.
   Sort as one list. Key/label year mismatches: `bicknell2021` (2022),
   `love2021` (2022), `difriscogawne2024` (2025). Two entries with "and
   colleagues" as the author list (`castellano2025`, `nong2021`) —
   complete or use `et~al.` with the first three.
4. `\texorpdfstring` on the `\date` dashes; `et al.` → `et~al.`.
5. l.333 "this is an quantity" → "a quantity".

---

## What is right and should not be touched

- `sec:measurement-expenditure` through `sec:feasibility`: $c > 0
  \nRightarrow N_{\text{after}} < N_{\text{before}}$, no conservation, no
  path integration, spend-and-gain gated by $c \preceq N$ — the
  bootstrapping structure stated in four short results.
- `sec:cross-frame`: no frame-free sum, conversion as a stated κ,
  principled vs stipulated, $E = mc^2$ as the worked principled case with
  the invariance test run "as a matter of course", and the prohibition
  narrowed to "convert if you must, but state κ, and check whether the
  conclusion survives changing it".
- `rem:supercritical`'s import of the delayed-fraction constraint and its
  refusal to re-derive the constants.
- The tetrapod case: structure preceding effective use, *Qikiqtania* as
  the evidence against reading a direction into it, and the juvenile
  caveat on *Acanthostega*.
- The conclusion's "not a tank — which denies the vessel and not the
  charge".

---

## Suggested order

1. **A** — the split and the deletion (waits on 03 r29's aux for the
   `NM-sec:evolutionary` label; 03's agent is running now).
2. **B**, **C**, **D** — three single-site corrections.
3. **E** — names, `xr-hyper`, Pratchett.
4. **F**.
