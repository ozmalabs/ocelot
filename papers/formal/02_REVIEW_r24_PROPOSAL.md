# Review of `02_seldon_manifolds_theory_referenced.tex` (draft-2026-09-02.1, r24) — proposal for fixes

Scope: the whole file (1491 lines, 27 pp), its log and aux, the two figure
bodies, and 01 r278 / 01a r42 for what is attributed to them. Line numbers
are r24. Nothing applied.

Compile: 0 undefined, 0 overfull, one cosmetic font warning. All 55
citations resolve; the control-theory, viability, aviation and economics
references were spot-checked (Aubin inertia principle / heavy viable
solutions, MacCready–Reichmann speed-to-fly, coffin corner, density
altitude, Becker–Murphy, Ben-Porath, Monderer–Tennenholtz
k-implementation, Heitzig terrain taxonomy) and hold. The paper's best
material — the one-dimensional glider case, the trap-defeats-inertia
result, and the "what is actually claimed" bookkeeping — is right and is
not questioned below.

---

## A. Two remarks numbered 0.1 and 0.2, before any section

`rem:already-in-use` (l.59) and `rem:underspecified` (l.86) sit between the
abstract and `\section{Scope}`. With `[section]` numbering they print as
**Remark 0.1 and 0.2** (aux confirms). They are 75 lines of standing-of-
the-paper material, and `sec:standing` (l.180, "Standing of the
construction") exists for exactly that purpose 100 lines later.

**Fix.** Make them the opening of a section. Either fold both into
`sec:standing` (retitled "What kind of object this is, and what is
claimed of it") and move it to first position, or give them their own
`\section{What is described}` before Scope. Either way no Remark 0.x.

Also in `rem:underspecified`: l.114 "One guard, and then a correction to a
guard that was drawn too tightly" and l.118 "That is too strong, and it
discards a signal worth having" narrate a redraft. State the guard and the
obviousness point directly.

---

## B. Attribution and naming

1. **`c` is attributed to 01.** `rem:no-dependent-clocks` l.1010: "the
   change-rate $c$ is the same in every frame (Graphic Equalisation, $c$ as
   the change-to-time rate)". 01 has no such section; it is the physics
   companion's `sec:c-rate`, and after 01a r42 the correct object is
   *unit* c (`def:three-c`), which is what "same in every frame" means.
   Fix the attribution and say "unit $c$".
2. **Seven names for companions, none declared.** "Graphic Equalisation"
   (17), "the foundational paper" (5), "the substrate paper" (2), "the
   companion" / "the companion paper" / "the companion law" / "the
   companion account" (7 — sometimes 01, sometimes 04), "the physics
   grounding", "the psychological grounding", "Narrative Momentum". The
   draft box (l.41–46) is the generic one with no companion sentence.
   Fix: the sentence 01a/01b/01c now carry, with 01's table names
   (Graphic Equalisation; the physics companion; *Narrativium*; the
   Narrative-momentum paper; the Seldon grounding; the applied paper),
   then use only those.
3. **`xr-hyper`.** By-description references to 01: well-formedness
   (l.105 → `GE-def:well-formed`), carvings result (l.127 →
   `GE-prop:convergence-observed`), Axiom on time (l.189, 1010 →
   `GE-ax:no-time`), four states (l.347 → `GE-def:states`),
   determinable/determined (l.389 → `GE-prop:determinable`), history
   principle (l.1020 → `GE-cor:history`), the present (l.363 →
   `GE-def:present`), aperture (l.231 → `GE-def:aperture`),
   GALS (l.1012 → `GE-rem:gals`), graph-law determinism (falsifier 5 →
   `GE-prop:determinism`). Add `\externaldocument[GE-]{01_…}` and
   `[PH-]{01a_…}` (for c and the change-budget).

---

## C. Two results restate 01's definitions as this paper's propositions

- `prop:present-limit` (l.363): "The present is $U_\Frame = 0$" — that is
  01's `def:present`, verbatim including the boxed equation. Here it is a
  *proposition* with a limit added.
- `def:unknown-count` (l.349): 01's $U_\Frame$ redefined with a horizon
  argument.

Neither says it is inherited. **Fix:** cite `GE-def:present` in both;
retitle `prop:present-limit` to what it adds ("$U_\Frame(h) \to 0$ as
$h \to 0$") and state the present itself as inherited. The same for
`rem:aperture` (l.230): 01's `def:aperture` already decomposes aperture
into *existence, grain, extent*; this remark's horizon / resolution /
dimension-set is that triple under other names. Say so in one sentence
rather than presenting the decomposition as this paper's.

---

## D. `prop:min-intervention` and the trap contradict unless the escape clause is named

`prop:min-intervention` (l.437): if the no-intervention continuation stays
acceptable, a positive-cost intervention "cannot dominate … solely by
preserving acceptability", given "no independent objective rewards
intervention itself". l.830–833: "a positive-cost intervention *can*
dominate no-intervention when the no-intervention continuation is a trap
lying wholly inside $\Goal$." A trap is inside $\Goal$ throughout, so the
proposition's antecedent holds — the two are reconciled only by reading
the capacity field as "an independent objective", which the proposition
does not say.

**Fix.** Add a corollary after `def:trap`: "A trap is the case in which
Proposition~\ref{prop:min-intervention}'s antecedent fails: the capacity
field is an objective independent of acceptability, and a frame carrying
it may pay to leave a region it is still permitted to occupy." Then l.830
points at the corollary.

---

## E. Falsifiability: the paper's own central commitment is not in the list

1. **The strong frame-relativity commitment is absent.** l.808–813 ("What
   is actually claimed"): "The commitment is that the fields are
   frame-relative in the strong sense: they exist only where a frame
   instantiates them, and there is no observer-free version of which a
   frame's version is a coarse reading." This is what the neighbouring
   formalisms decline (Kaelbling, Halpern) and what the paper says it
   contributes. No entry tests it. Add `[shape]`: fails if a grounding
   exhibits a field over reachable futures that two frames' fields are
   demonstrably coarse readings *of* — an observer-free referent from
   which both can be recovered by coarsening.
2. **The no-referent-grain interpretation is absent.** l.321–343: "no
   referent continuum stands behind the grain … that interpretation, not
   the refinement machinery, is what this construction adds." Add
   `[detail]`: fails if cell-splitting can be shown to require a finer
   signal arriving (a hidden variable) rather than incoherence at the
   held grain.
3. **Item 1 "Descent predicts trajectory" is `[shape]` on a pattern.**
   l.504–509 says the descent default is "a pattern the foundational paper
   holds at the strength the evidence supports rather than a universal".
   Same conflict 01 had with "Cost is the write"; re-mark `[detail]`.
4. **Items 2 and 5 carry their own caveats as italic parentheticals inside
   the item.** 01's fix was one sentence after the list. Do the same.
5. **"On the tags" paragraph (l.1149–1157)** is the old 01a text with "The
   substrate paper has carried these marks for some time…". Replace with
   01's harmonised sentence verbatim (grep 01 for "A \textsc{[detail]}
   failing is a revision") and cut the history. The "On a claimed class"
   paragraph before it is good and stays.
6. **`sec:competing`'s claims have no falsifier and no citations.** See F.

---

## F. `sec:competing` argues against game theory with no citations

l.912–972 (60 lines): the one-shot game abstracts away persistence;
repeated play "inverts the invariant"; "in most real encounters *playing
the game is the wrong move*"; sealed frames (sport, auction, tender) are
the exception. This is a strong, quotable position stated with zero
references in a paper that cites 55 works elsewhere and whose scope
section says its contribution is placement inside prior work.

The literature it is arguing with already contains most of it: the folk
theorem and repeated-game cooperation (Fudenberg–Maskin 1986; Axelrod
1984), reputation (Kreps–Wilson 1982), the "prisoners go back to prison"
objection is a standard one about the dilemma's payoff scoping, and
"situations are not games" is Binmore's own distinction between the model
and its application. **Fix:** (a) cite at least the folk theorem, Axelrod,
and Kreps–Wilson, and say what the section claims *beyond* them — which,
on the paper's own words, is the horizon-artefact reading (l.940–945) and
the persistence-of-players-not-games inversion (l.950–957); (b) soften
"in most real encounters playing the game is the wrong move" to what can
be defended (a decision procedure whose horizon ends at the payoff
systematically under-weights consequences that land past it), or mark it
as a hypothesis with a falsifier; (c) l.947–948 "The construction is named
for prisoners, and the one thing it removes is the prison" is a good line
and should stay.

---

## G. Structure

1. **The one-dimensional case** (l.621–786, 165 lines) is a `\subsection*`
   inside `sec:contours` and is the paper's strongest empirical section.
   Promote to `\section{The one-dimensional case}` with its own label, so
   the falsifiers and 02a can point at it.
2. **`sec:goal-direction`** (5 lines) and **`sec:downstream`** (3 lines) are
   sections. Fold the first into `sec:acceptable`; the second into
   `sec:contours`'s second-field subsection, where Narrativium is already
   introduced.
3. **`rem:second-field-prior`** l.569 "What is left after that is narrower
   than it first looks, and **two retractions follow**" — narrated. State
   the two negatives ("It is not that…") without calling them retractions.
4. **The NHC cone figure** (l.65–68): "sized so that the storm's centre has
   historically fallen inside it about two thirds of the time" — correct
   (the cone is drawn to the 67th percentile of historical track error)
   but uncited in a paper that cites everything else. Add the NHC
   definition page or a track-error verification report.
5. **Font warning** `T1/lmr/m/scit`: `\textsc{null}` inside the italic body
   of `def:contours` (l.475). `\textnormal{\textsc{null}}`. Also
   `\texorpdfstring` on the `\date` dashes for uniformity.
6. **`prop:min-intervention`'s untitled remark** (l.441) — give it a title
   and label ("No intervention is an alternative, not NULL").

---

## H. Prose (representative)

- l.418 "*A manifold is built and not found.*" sits in `sec:acceptable` but
  belongs with the standing remarks (A); move it there.
- l.704 "Soaring is accordingly the closest operational instance of this
  whole assembly that the author is aware of, and it is worth conceding as
  such" — "the author is aware of" is the only first-person-adjacent
  phrase in the set; "that this account has found".
- l.1046–1047 "the one a reader will substitute if the distinction is not
  drawn" — fine.
- l.1198 "The future, in this framework, is not primarily a destination.
  It is a reachable geometry." — good closing line; keep.
- Bibliography: `et al.` vs `et~al.` (Ames, Aubin et al., Carr, Delibes …)
  as in the other papers; matters for the statement generator if 02 ever
  gets one.

---

## What is right and should not be touched

- `sec:standing`'s three remarks (succession needs no observer; the
  horizon is doubly observer-relative; higher machinery is frame-relative)
  are exactly the right guards and are load-bearing for the falsifiers.
- The undetermined / undisclosed / blind-spot separation
  (`rem:two-deficits`, `def:blind-spot`) and its consequence that a
  projection mixing the two reports a width "no amount of observation
  could ever reduce".
- The glider section entire, including the fourth combination (free
  capacity gain in a thermal), the air-indexed vs ground-indexed
  manifolds, and the vertical-landing limit case.
- The bookkeeping against Salge, Israeli, Walker, Heitzig, Kaelbling and
  Halpern in "What is actually claimed" — this is the model for how the
  set should position itself.
- Aubin's inertia principle conceded in full, with the trap as the one
  place the fields buy something against it.

---

## Suggested order

1. **A** and **G.1–G.2** — the section map (Remark 0.x gone; glider
   section promoted; two stub sections folded).
2. **B** — attribution of c; naming sentence; `xr-hyper`.
3. **C** and **D** — inherited definitions marked; the trap corollary.
4. **E** — the two missing commitments, one re-mark, tags harmonised.
5. **F** — citations and a defensible strength for the game-theory
   section.
6. **G.3–G.6**, **H**.
