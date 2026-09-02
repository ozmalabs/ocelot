# Review of `01c_graphic_equalisation_cosmology_grounding.tex` (draft-2026-09-02.1, r6) — proposal for fixes

Scope: the whole file (351 lines, 6 pp), its log, and the companions it
attributes results to (00 r121, 01 r276, 01a r42, 04, 09). Line numbers
are r6. Nothing applied.

Compile: 0 undefined, 0 overfull, one cosmetic font warning. All nine
citations resolve and are correct (EGS 1968, Stoeger–Maartens–Ellis 1995,
Clarkson 2012, Maartens 2011, Guth 2007, Freivogel 2011, Bousso–Freivogel
2007, Feeney et al. 2011, Planck 2015 XVI). The paper is short by design and
says why; that division is sound and is not questioned below. The findings
are attribution, one consistency gap against 00, falsifier form, and one
error in 01 that this review's predecessor caused.

---

## A. The load-bearing result is attributed to the wrong companion

The spine of the paper (abstract l.38–41; `prop:measure` l.200–202) rests
on "the companion's **no-prior-free proposition** … the companion proves no
such thing is a member of the space". In this paper "the companion" is 01
(l.113 "The companion's frame is an instantiated boundary…"). But the
proposition is the **adaptability paper's** — `09_adaptability.tex`
`prop:no-prior-free`, "There is no prior-free measurement: a capability
cannot be measured against a prior-free baseline, because no such baseline
is a member of the space being measured." 01 has no such proposition. The
paper does say "the adaptability companion" at l.209 and l.265, so it knows;
the two load-bearing sites just say "the companion".

**Fix.** l.39–40 and l.200–201: "the adaptability paper's no-prior-free
proposition". Add `xr-hyper` with `\externaldocument[AD-]{09_adaptability}`
and cite `Proposition~\ref{AD-prop:no-prior-free}`; likewise `[GE-]` for 01
(`def:frame`, `prop:higher-frame`), `[PH-]` for 01a (`cor:nonlocal`,
`prop:past-hyp`, `prop:self-location`), `[IS-]` for 00 (`prop:cohere`), and
`[NV-]` for 04 (`rem:kappa-kinds`, the stipulated-conversion remark at
l.204–206). The paper makes about twelve by-description references to five
companions and names none of them in its draft box — add the short-name
sentence 01a/01b now carry, using 01's table names: *Is*, Graphic
Equalisation, the physics companion, *Narrativium*, the adaptability paper.

---

## B. `prop:totality` contradicts 00's posited case unless it says which object it means

`prop:totality` l.93–98: "There is no frame from which everything is the
relatum … whatever frame is offered as the totality is individuated by
something, which is then outside it. So *the universe as a whole* names no
object."

00 r121 `sec:one-way`: "The base is embedded in nothing, because it is
everything there is. So there is no container to instantiate a boundary …
What remains available is modelling." 00's whole paper *models* the
totality and says it has no frames and no container. 01c says every offered
totality has a container. Both are right about different objects — 00's base
is not a frame; 01c's "universe as a whole" is a frame someone offers as
total — but 01c cites 00's three degenerate readings in the same section
(l.87–90) and never says so. A reader of both sees "there is always one more
step outward" (01c) against "embedded in nothing" (00).

**Fix.** One sentence after `prop:totality`: "This is a claim about *frames*.
What *Is* posits — everything, with no container, modelled and not observed
— is not a frame and is not the object cosmology individuates; the
proposition says that no *individuated* universe is the totality, which is
the observed/modelled distinction of Section~\ref{sec:scope} doing the work
it was announced for." That discharges l.71–73's promise that the
distinction "does most of the work below", which nothing below currently
invokes by name.

---

## C. Falsifiers: unmarked, un-numbered, one is not a falsifier of this paper, one is missing

Every other paper in the set now carries `[shape]`/`[detail]` with 01's
definition sentence verbatim, in an enumerate. 01c has four italic
paragraphs with no marks.

1. **Adopt the form**: the definition sentence (copy from 01
   `sec:falsifiability`), then an enumerate.
2. **"An aperture wider than assumed"** — the item itself says a detection
   "refutes neither the account nor this paper's reading" but only "an
   assumption about the present aperture, which is about us rather than
   about the world". That is `[detail]`, and it should say what
   *changes* on refutation: the horizon section's l.139–141 claim that "no
   measurement inside discriminates" between values of the superframe
   dimension would be false for that dimension.
3. **"Convergence of measures"** — `[shape]`; correct and the paper's real
   exposure. Keep.
4. **"Anisotropy that survives"** — this is not a falsifier of anything
   this paper argues. If isotropy fails, the inference to homogeneity fails
   *a fortiori*, and `prop:copernican` (which refuses that inference) is
   untouched. Reword as `[detail]`: what it costs is the sentence "isotropy
   is measured" and the surviving-leg framing of
   `sec:cosmological-principle`, not the proposition. Or drop it.
5. **"Derivation of a seed"** — belongs to 01a (`prop:past-hyp` carries it
   there). Keep as inherited, marked `[shape]`, with the `PH-` ref.
6. **Missing: `prop:typical`.** The anthropic section has no exposure. Add
   `[detail]`: fails if a typicality argument can be stated on a single
   reading of *universe* — either a countable ensemble with a
   frame-internal measure (which is item 3 again), or a relative universe
   with a reference class larger than one member — without sliding between
   them.
7. **Missing: `prop:beyond`'s positive claim.** "What lies beyond a horizon
   is real, related, and inaccessible." The inaccessibility is item 2; the
   *related through the superframe* half has no test stated. Either mark
   it as inherited from 01a `cor:nonlocal` or say it carries no separate
   exposure.

---

## D. Cross-paper error in 01, caused by the 01 review

01 r276 l.591 (`rem:only-g`): "reading it so would invalidate the
**cosmology companion's** result, which reasons from a rock's being a frame
to the universe's being one." That result is **01b's** `sec:minimal`
("A rock *is* a universe — the minimal one"), not 01c's. The 01 review
(item A.4) guessed 01c; the guess was wrong and the agent applied it.
**Fix in 01:** "the mind companion's result" (and a `\ref` to 01b's
`prop:minimal-universe` if 01 adopts an `[MS-]` external document; a name
is enough). Bump 01 to r277 when touched.

---

## E. Mechanical and prose

1. **Font warning** `T1/lmr/m/scit`: `\textsc{null}` inside `\emph` (l.44
   abstract) and inside the italic body of `prop:beyond` (l.127). Wrap as
   `\textnormal{\textsc{null}}`. `\texorpdfstring` on the `\date` dashes as
   the other papers now do (no hyperref warning here yet because no math in
   section titles, but keep the preamble uniform).
2. **Hubble tension has no citation** (`sec:tension`, l.262–263). Every
   other empirical claim in the paper is cited. Add one review (e.g. Di
   Valentino et al. 2021, *Class. Quantum Grav.* 38 153001, or Riess et al.
   2022, *ApJL* 934 L7) — check the reference before adding.
3. **The italic-opener device is used on ~45 of ~60 sentences-that-open-a-
   paragraph.** In a six-page paper that is nearly every paragraph, and the
   emphasis stops discriminating. Keep it for the four or five sentences that
   are the result (l.75–76, l.122, l.139, l.212, l.259) and unitalicise the
   rest. This is the largest single readability change available and it is
   mechanical.
4. l.106 "This is less revisionary than it sounds, and the practice already
   runs this way. Cosmological parameters are fitted to what is inside the
   horizon, and the fits do not degrade for want of what is outside." — the
   second clause is doing empirical work with no citation and is arguably
   false as stated: large-scale-structure fits carry super-horizon-mode
   assumptions (the cosmological principle itself). Soften to "the fits are
   made to what is inside the horizon" and drop the "do not degrade" claim,
   or cite.
5. l.171 "its realistic form \citep{stoeger1995} weakens exactness and not
   universality" — correct and well put; keep.
6. l.209 "The consequence is the same one the adaptability companion reaches
   for intelligence" — reads as if intelligence is the consequence; "reaches
   *about* intelligence".
7. Bibliography `{9}` width argument is fine for nine items; if the Hubble
   citation is added it becomes ten and the label width should be `{99}`.
8. Draft box lacks the "companion to … and inherits their definitions"
   sentence 01a/01b carry. Add, with the names from A.

---

## What is right and should not be touched

- The division of labour with 01a (in-frame questions there, boundary
  questions here) is principled and the paper says exactly why. Keep
  `sec:scope` as is apart from the naming.
- The EGS reading (`sec:cosmological-principle` l.168–181): that the
  Copernican step is the theorem's *antecedent*, not an addition to it, is
  the sharpest thing in the paper and is cosmology's own statement of the
  point. Keep verbatim.
- `rem:inflation`'s separation of inflation-as-physics from one malformed
  inference drawn from it.
- `sec:tension`'s refusal to say anything the field has not already done.

---

## Suggested order

1. **A** — attribution and the external-document setup (mechanical; also
   fixes the abstract).
2. **D** — the 01 line (one edit, one bump).
3. **B** — one sentence.
4. **C** — falsifier form and the two missing entries.
5. **E** — warning, Hubble citation, the italics pass, l.106.
