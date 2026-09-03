# Review of `01a_graphic_equalisation_physics_grounding.tex` (draft-2026-09-02.1, r43) — proposal for fixes

Third pass. Scope: the whole file (2008 lines, 32 pp), its log and aux, the r42
review and what r43 did with it, the Born note (01d r2) in full and the
division of labour agreed in `01d_REVIEW_r1_PROPOSAL.md` §B, and the four
companions 01a now resolves against. Line numbers are r43. Nothing applied.

Compile: 0 LaTeX warnings, 0 overfull, 0 underfull, no `??`; 54 bibitems, all
cited, none uncited, sorted by label, `et~al.` throughout, `\texorpdfstring` on
both `\date` dashes. `check_paper_refs.py` reports 0 unreferenced by-name
mentions. All five `\externaldocument` prefixes are declared (GE-, IS-, MS-,
NM-, BN-) and **every one of the 30 external refs resolves in its target's
aux** — 15 GE-, 2 IS-, 3 MS-, 5 NM-, 5 BN- — verified against
`01_…aux`, `00_is.aux`, `01b_…aux`, `03_…aux`, `01d_…aux`. No implementation
identifiers, no A1, no narrated drafting, no off-table companion names, and the
paper calls itself "this paper" throughout (r42's loose end (d) is closed).
r42's A–G all landed: the four `\externaldocument`s, "the momentum paper", the
preamble narration deleted, falsifier 9 split with self-location moved after
the list, `sec:collapse` reduced to one cross-reference, `rem:forced-concurrency`
and `rem:sign-is-phase` labelled, `ignatowsky1910`, `duff2002trialogue`, the
Höhn ordering, `rem:ascent-different-somewhere`. **What this pass finds:
one physics error that also contradicts the paper's own second-law proposition;
the two subsections the Born note points at by name still carry no label
because they are starred; the collected-residuals list restates the Born note's
ledger with two sentences verbatim; the change-budget is stated in a form
whose obvious reading is the wrong one; three defects in the spectrum-floor
argument; and five propositions that argue.**

Labels cited by other papers: 27 distinct `PH-` labels are cited 43 times from
nine files (01, 01b, 01c, 01d, 02, 03, 04, 05, 06) — heaviest `PH-sec:budget`
(×6), `PH-sec:dimensions` and `PH-cor:nonlocal` (×4), `PH-sec:c-rate`,
`PH-rem:oneway-rule`, `PH-prop:self-location`, `PH-prop:born` (×3). All 27
resolve today. All must survive under the same names and kinds; §B below adds
two rather than moving any.

---

## A. The demon corollary prices the wrong operation, and contradicts `prop:second-law`

l.1148–1153: "Landauer's $k_{\mathrm B}T\ln 2$ … is the price of \emph{resolving}
one bit --- dragging one distinction up out of the un-distinguished, or erasing
one back down. Maxwell's demon is exorcised by exactly this: **it must pay to
distinguish**, and that payment is the entropy it thought it removed for free
\citep{bennett1982}. **There is no free distinction**, hence no free entropy
reduction."

That is the pre-Bennett resolution (Szilard, Brillouin) attributed to Bennett,
who argued the opposite. Landauer's bound prices *logically irreversible*
operations — erasure. Bennett's 1982 contribution was precisely that
*measurement can in principle be performed reversibly and therefore for free*,
which is why the demon's cost had to be relocated into the resetting of its
memory. "There is no free distinction" is the claim Bennett refuted; citing him
for it inverts the source.

It is also inconsistent with this paper's own mechanism. `prop:second-law`
(l.1098–1106) says "Every \emph{write} of the discarding class discards its
predecessor … Change therefore accumulates entropy, because change forgets by
default and forgetting is exactly this demotion", and falsifier 4 (l.1646–1649)
prices "predecessor-discarding writes, which are the only priced ones." Under
the paper's own account the demon pays to *discard*, not to distinguish. The
corollary is the one place the paper prices the non-discarding half.

**Fix.** Rewrite the first three sentences of `cor:demon-life`:

> Landauer's $k_{\mathrm B}T\ln 2$ (Section~\ref{sec:constants}) is the price of
> \emph{erasing} one bit --- pushing one distinction back down into the
> un-distinguished, which is the discarding write of
> Proposition~\ref{prop:second-law}. Maxwell's demon is exorcised by exactly
> this: a demon with finite memory must erase to keep operating, and that
> erasure is the entropy it thought it removed for free \citep{bennett1982}.
> Acquiring the distinction need not cost --- a copy into blank structure
> discards nothing --- which is why the cost sits in the reset and not in the
> observing, and why on this account it is the \emph{no-copy} asymmetry and not
> the act of distinguishing that carries the arrow.

The rest of the corollary (minting is a write, hence paid; Landauer heat
exported; life as the second law with a subsidy) stands unchanged and is
strengthened: it now names the same priced operation the proposition does.

Two knock-on sites, both one word. l.883–885, the $k_{\mathrm B}$ bullet, is
already neutral ("one bit's change converted from the information frame into
the energy frame") and needs nothing. l.1609–1611, `sec:prior-art`: "the
resolution of Maxwell's demon by the cost of information is Landauer's and
Bennett's" → "by the cost of *erasing* information".

---

## B. The two subsections the Born note points at by name carry no label, because they are starred

`xr-hyper` is declared both ways, but two of the Born note's five pointers into
this paper cannot be made to resolve, because their targets are `\subsection*`:

| 01a | 01d site | what 01d says |
|---|---|---|
| l.644 `\subsection*{An attempt to close it}` | l.246, l.353, l.402 (three times) | "the physics companion (its Proposition~\ref{PH-prop:born} **and the argument following it**)" |
| l.805 `\subsection*{The reconciliation: Born, SR, and GR on one substrate}` | l.329–330 | "the reconciliation is that companion's, **argued in its subsection on Born, SR and GR**" |

`PH-prop:born` (l.630–639) is only the conjugate-pair *candidate*; the paper
itself says immediately after it "This is a candidate, not a derivation"
(l.641). The phase-averaging selection, the Gleason step and the Hilbert-posit
step — which is what 01d's three citations actually need — all live in the
starred subsection. So the note's most-repeated reference resolves to a
proposition that does not carry the argument, plus a by-name gesture at an
unnumbered heading.

A `\label` after a starred sectioning command picks up the previous counter and
would resolve to the wrong number, so the fix is to unstar. This is consistent
with the paper's own style: `sec:collapse` (l.462) is already a numbered
subsection.

**Fix.**

- l.644 → `\subsection{An attempt to close it}\label{sec:born-attempt}`
- l.805 → `\subsection{The reconciliation: Born, SR, and GR on one substrate}\label{sec:born-sr-gr}`

Then 01d's three citations become "its Proposition~\ref{PH-prop:born} and
Section~\ref{PH-sec:born-attempt}", and l.329–330 becomes
"Section~\ref{PH-sec:born-sr-gr}". Both new labels join the surviving-`PH-` set.
(Coordinate with the 01d agent: the note's r3 is where those four call sites
change.)

---

## C. "Honest residuals, collected" restates the Born note's ledger, twice verbatim

l.782–803 is a four-item list; 01d `sec:residuals` (l.334–368) is a five-item
list. Item-by-item:

| 01a item | 01d item | relation |
|---|---|---|
| 1, Uncoupled to additive (l.784–787) | 2, The linearity step | same claim; **"the linearity of the imposed supergraph map is not handed over for free"** and **"This is the one posit the recovery rests on"** are both verbatim |
| 2, Complex over real is self-located (l.788–790) | `prop:contingent` + `rem:misframing` | 01a restates the verdict; no `\ref` to either |
| 3, The hygiene conditions (l.791–793) | 1, Level 0 hygiene | 01a lists the three conditions *and then* points at `BN-sec:residuals` for the same three |
| 4, The OPT instantiation (l.794–802) | `prop:opt` / `sec:level0` | already a pointer, wrapped in a restatement of the argument it points at |

Per the division agreed in `01d_REVIEW_r1_PROPOSAL.md` §B, the note carries the
rated residuals; this paper carries the physics. The list as it stands is the
note's ledger written out a second time, in a paper that already cites the
ledger three lines further down.

**Fix.** Replace l.782–803 with one paragraph and one item:

> \emph{Honest residuals.} The recovery rests on one posit of this paper's own:
> the rigorous step from ``uncoupled'' to full additivity and norm-preservation
> is not made here, and the linearity of the imposed supergraph map is not
> handed over for free --- the mechanism motivates linearity and does not prove
> it. The remaining residuals belong to the mapping rather than to the physics,
> and the Born note holds them rated, item by item, in its
> Section~\ref{BN-sec:residuals}: the Level-0 hygiene conditions, the reach of
> the phase-average selection against Gleason, the composition seam, and the
> genre-match ratings.

Item 2 is not lost: the complex-over-real verdict is stated at l.762–770 in the
body, which is where this paper carries it (§D of the same agreement). It
should acquire the `\ref` it currently lacks — see the Smaller list.

---

## D. The change-budget splits in squares, and mass reserves nothing

l.170–178: "That fixed throughput splits between \emph{spatial motion} and
\emph{internal change} (proper time), and a speed is the fraction spent on
motion. At rest the whole budget is internal change … at $c$ the whole budget is
motion and no proper time remains. **Mass is the budget \emph{reserved} for
internal change, so a massive graph can never put all of it into motion.**"

Two problems, one of which the paper has already answered in its own
parenthesis three lines later.

1. *The split.* Stated bare, "splits between" invites a linear reading, on
   which the two shares sum to the budget. That reading is wrong: the shares
   are $(\mathrm d\tau/\mathrm dt)^{2}+(v/c)^{2}=1$, a Pythagorean split, which
   is exactly the constant-magnitude four-velocity the paper cites at
   l.185–187. The paper has the right object and does not say which addition it
   is under. One clause fixes it and costs no number the scope disclaims.
2. *"Reserved".* Nothing is held back at any finite speed. A massive graph's
   internal-change share is $\sqrt{1-v^{2}/c^{2}}$, which tends to zero: it can
   put asymptotically all of the budget into motion, and what mass does is make
   the internal share nonzero at *every* finite speed, so the motion share
   reaches $1$ only in the limit. "Reserved" states a fixed withheld fraction,
   which there is not — and it is load-bearing, since `prop:sr-gr` (l.434–442)
   reuses it ("mass is throughput tied up in internal change").

**Fix.** l.170–178:

> That fixed throughput splits between \emph{spatial motion} and \emph{internal
> change} (proper time) --- in squares, the two shares summing to one, which is
> the constant-magnitude four-velocity below --- and a speed is the share spent
> on motion. At rest the whole budget is internal change and the clock ticks
> fully; increasing speed moves budget to motion, leaving less for internal
> change, so the clock slows --- time dilation as budget re-allocation --- and
> at $c$ the whole budget is motion and no proper time remains. Mass is what
> holds the internal share \emph{above zero at every finite speed}: a massive
> graph's motion share approaches one and never reaches it, so it asymptotes to
> $c$ and the energy to approach diverges, while a massless one has no internal
> share at all and \emph{is} at $c$, with no proper time.

In `prop:sr-gr`, "mass is throughput tied up in internal change" then reads
correctly as the change-load half and needs no edit.

---

## E. Three defects in the spectrum-floor argument

The argument itself is right and is the best-worked new material in the paper.
Three things sit around it.

**E.1 The "bridge" is asserted, not built.** l.1261–1264: "The gap is that the
constant hazard here is a claim about what the \emph{nucleus} retains, while
the deviation comes from the \emph{composite} spectrum being bounded below.
Those are different objects. **The bridge is the floor itself**, and the
substrate does supply it." `prop:spectrum-floor` then states a floor for "a
frame's spectrum" — which is a per-frame fact and therefore holds of the
composite *and* of the nucleus. That is what makes the two objects stop being a
problem, and the paper never says it. As written, "the bridge is the floor
itself" is a promise the next six paragraphs do not redeem, and what they
actually establish is a *reconciliation* rather than a bridge: the constant
hazard is a fact about what the nucleus retains, the required deviation is a
fact about the container, and the two are compatible because the floor is a
fact about any frame at all. **Fix:** replace the last sentence of l.1263–1264
with "What reconciles them is that the floor is a fact about \emph{any} frame,
so it holds of the composite and of the nucleus alike: the constant hazard is
what the nucleus retains, the required deviation is what the container's floor
imposes, and neither is a claim about the other." Then, after l.1316, add one
sentence: "So the leading behaviour is exponential because nothing is retained,
and the departure is required because a floor exists --- two facts about two
objects, not one derivation across them."

**E.2 `prop:dim-boundary` is cited for something it does not say.** l.1304–1305:
"The zero of energy is an offset and offsets are frame-units
(Proposition~\ref{prop:dim-boundary})". That proposition says "a constant is a
ratio or it is a unit artefact, and there is no third kind" — a claim about
*units*, not about *origins*. An additive offset is neither a ratio nor a unit;
it is a choice of zero, which the proposition's own dichotomy has no slot for.
**Fix:** either drop the cite and ground the sentence where it belongs — "The
zero of energy is a choice of origin, and an origin is read in-frame exactly as
a unit is (Section~\ref{sec:constants})" — or widen `prop:dim-boundary` by one
clause to cover origins as well as units. The first is cheaper and does not
touch a label six other papers cite.

**E.3 The spectrum condition is not $H\ge 0$ in one frame.** l.1311–1312: "That
is the \emph{spectrum condition} --- positivity of the energy, an axiom where
it is usually found \citep{streater1964} --- arriving as a consequence rather
than a postulate." The Wightman spectrum condition is that the joint spectrum
of $P^{\mu}$ lies in the closed forward cone; it is equivalent to $H\ge 0$ *in
every frame*, not in one. The argument here does reach the stronger form —
every frame reads its own floor, and no frame is privileged — but the step is
unstated, so the citation currently claims more than the sentence before it
delivers. **Fix:** "That is the \emph{spectrum condition} --- positivity of the
energy in every frame, which is where it is usually taken as an axiom
\citep{streater1964} --- arriving as a consequence rather than a postulate:
each frame floors its own spectrum for the same reason, and none is
privileged."

The rest holds on re-reading. The Khalfin/Paley–Wiener direction is stated
correctly (Lorentzian ⇒ support on the whole line; ground state ⇒ support on a
half-line ⇒ no exact exponential); $t^{-2(1+\beta)}$ from a
$(E-E_{\min})^{\beta}$ threshold density is right, and $\beta=\tfrac12$ giving
$t^{-3}$ for the free-particle $s$-wave is the standard value; `rem:sign-is-phase`
is consistent with 01's position (negative time does not exist; negative
frequency is opposite phase) and cites `GE-rem:phase-not-time` and
`GE-prop:cycle-unit` for exactly the two halves it uses; "one premise applied
twice" survives inspection, the second application being to the rate rather
than to the sign.

---

## F. Five propositions and corollaries that argue

**F.1 `prop:one-time` (l.1394–1407)** is the clearest. Its body motivates ("self-change
gives a reason it tends that way"), then withdraws ("But this is a tendency,
not a theorem"), then contrasts with a companion case and grades its own
evidence ("unlike the $N=3$ case, which has Ehrenfest's stability result behind
it, no comparable result is cited for the time axis and none is claimed"). That
is three moves a remark makes. **Fix:** the proposition states —

> Every observed time is one-dimensional, and one succession is what self-change
> lays down: a frame's own changes are strictly ordered and none are concurrent.
> Independent successions are not prohibited; the single observed axis is
> selected, not forced, and time itself is optional, absent from every inert
> frame.

— and everything from "what selects the single observed time axis is
conjectured here" to "none is claimed" becomes
`\begin{remark}[The selection of one time axis is conjectured, not derived]\label{rem:one-time-conjecture}`
immediately after it, keeping the Ehrenfest contrast where the paragraph on
$N=3$ (l.1409–1420) can pick it up.

**F.2 `cor:observer` (l.508–525)** carries four things: any coupling is a
measurement; a reconciliation with *Is*'s one-way proposition, argued
("and that is consistent with this, because …"); definiteness and the pointer
basis; and a forward exception for superframe forcing that exists to support
`cor:doubleslit` two sections later. **Fix:** the corollary keeps the first and
third. l.511–517 ("\emph{Measure} here is the coupling itself … A rock does the
second and not the first") becomes
`\begin{remark}[Measuring is not observing]\label{rem:measure-not-observe}` —
it is an argued reconciliation with a companion, and 00 and 05 are the papers
likeliest to want it by number. l.521–524 (the superframe exception) moves to
`sec:interference`, just before `prop:interference`, where it is used.

**F.3 `prop:dim-boundary` (l.895–903)** opens with a back-reference ("This
dissolves the \emph{dimensional} constants and touches the \emph{dimensionless}
ones not at all") and argues its own significance ("It is not silent about
their \emph{type}, and that is not nothing"). Six other papers cite this label,
so the statement should not move — only the framing. **Fix:** "A dimensional
constant is a frame-unit and reads as $1$ in its own terms; a dimensionless one
--- the fine-structure constant $\alpha\approx1/137$, the mass ratios --- cannot
be set to $1$ by any unit choice, being a genuine cross-frame \emph{ratio}. The
framework says nothing about their values. About their type it says: a constant
is a ratio or it is a unit artefact, and there is no third kind. There are no
magic numbers --- standalone quantities that simply are, attached to nothing."
The "not nothing" beat belongs in the paragraph at l.905, which already makes
it.

**F.4 `prop:momentum-cons` (l.1045–1052)** turns on a contrast — "**But**
momentum conservation is already the free-continuation default …". A
proposition should not concede. **Fix:** "Space-translation symmetry --- the
rules the same everywhere --- produces no residual under translation, and
momentum is conserved. Momentum conservation is the free-continuation default
Graphic Equalisation states (its Remark~\ref{GE-rem:collapse-write}): the
un-rewritten Narrative, Newton's first law, continuation costing nothing.
Noether's momentum case and inertia are one statement." Note the naming as
well: "Graphic Equalisation's momentum" (l.1048) reads as the momentum paper's
name attached to the wrong document; the target is 01's own remark and resolves
correctly, so only the phrase needs changing.

**F.5 `cor:pauli` (l.1450–1457)** ends with a hedge and a forward pointer ---
"though the argument does not by itself select fermions over bosons, for which
see the remark below" --- which `rem:spin-stat` then states in full, three lines
later. **Fix:** end the corollary at "Exclusion is on this reading consistent
with the arithmetic of identity rather than a force." and let the remark carry
the limit, which is what it is titled to do.

---

## G. One of this paper's own sections is attributed to Graphic Equalisation

l.463–464: "Relativity also reconciles with the collapse picture of quantum
measurement, by a division **Graphic Equalisation already carries**
(Section~\ref{sec:c-rate}): the continuous in the maps between frames, the
discrete in a frame's own states."

`sec:c-rate` is this paper's Section 2. The sentence names the companion and
then points at itself. The continuous/discrete division is stated at l.136–138
here, as this paper's reading of the cross-frame comparison — it is not 01's.
This is the only site of its kind (checked mechanically across all 24 internal
refs that sit within 260 characters of a companion name; the other three are
correct, each naming a companion *and* citing it separately).

**Fix.** "Relativity also reconciles with the collapse picture of quantum
measurement, by the division of Section~\ref{sec:c-rate}: the continuous in the
maps between frames, the discrete in a frame's own states." If the division is
meant to be inherited rather than made here, the alternative is to cite 01 for
it — `GE-rem:no-denominator` is the nearest target and is already used at
l.109, but it is about the absence of a rate in substrate-time, not about where
the continuum lives, so the first fix is the accurate one.

---

## H. One promoted claim has no falsifier, and one falsifier's title promises two things

**H.1.** Every proposition and corollary is covered: 1→`prop:c-unit`/`def:three-c`,
2→`prop:sr-gr`/`cor:reconcile`, 3→`prop:dim-boundary`, 4→`def:entropy`/
`prop:second-law` and (its second clause) `cor:demon-life`, 5→`prop:gibbs`/
`cor:pauli`, 6→`prop:wigner`/`cor:observer`, 7→`prop:mixed`/`cor:nonlocal`,
8→`prop:momentum-cons`/`prop:energy-cons`, 9→`prop:past-hyp`, 10→`prop:born`,
11→`prop:interference`/`cor:doubleslit`, 12→`prop:one-time`, 13→
`prop:closure-three`, 14→`prop:decay`, 15→`prop:spectrum-floor`, 16→the
denominator strategy; `prop:self-location` is explicitly placed after the list
as a consequence (l.1718–1723). That accounting is sound and the list is in
good order.

What is *not* covered is a claim the abstract (l.55–57) and `sec:scope`
(l.78–79) both promote in the same breath as the ones that are: "the
uncertainty principle is the finite-aperture floor … quantization the aperture
cell". `sec:constants` l.878–883 states it as an identification —
$\Delta x\,\Delta p\ge\hbar/2$ *is* the finite-aperture budget stated as a
bound — and nothing in the list exposes it. Item 3 covers only whether $\hbar$
is absorbable into a frame's units, which is the weaker half.

**Fix.** Add after item 3:

> \item \textsc{[shape]}~\textbf{The uncertainty principle is the finite-aperture
> floor.} Fails if the conjugate trade is not an aperture budget --- if a frame
> can be exhibited resolving two conjugate dimensions jointly past the floor
> without a compensating loss elsewhere, or if the bound must be postulated
> independently of the finiteness of internal-change throughput rather than read
> off it (Section~\ref{sec:constants}). ($\hbar$'s \emph{value} is not claimed;
> that it is the cell's quantum is.)

The Planck-scale claim is then covered as a consequence of this item together
with item 3, and saying so in the scope note is cheaper than a seventeenth
falsifier.

**H.2.** Item 12 (l.1691–1692) is titled "**Time is optional; the observed time
is one-dimensional**" and its whole failure condition is "Fails if an inert
frame (no firing rules) nonetheless has an in-frame succession" — which tests
only the first half. The one-dimensionality is then disclaimed in the scope note
(l.1726–1727), correctly, since the paper marks it as selected rather than
forced. **Fix:** retitle the item **Time is optional** and leave the 1-D content
where the scope note already puts it.

---

## I. Two remarks past forty lines carry several arguments each

**I.1 `rem:c-indirect`, l.189–231, 43 lines.** Four arguments: $c$ is not
directly readable because the measurement is funded by the throughput it would
read; the indirect route exists and is three centuries old (Rømer, Fizeau, and
the mind companion's parallel); knowing $c$ has a price and that price is what
makes the claim empirical; and metrology has already acted on the conclusion
(the 1983 metre, the 2019 revision). **Fix:** split at l.200 ("It does not
follow that $c$ is unknowable"). The first part keeps `rem:c-indirect` and its
title. The second becomes
`\begin{remark}[The indirect route is available, and it is priced]\label{rem:c-inferred}`,
carrying l.200–226 (the three-centuries paragraph, the two-things-follow
paragraph, and the metrology paragraph, which is the same argument's evidence).
The closing pointer at l.228–231 stays with the second. `PH-rem:c-indirect` is
not cited by any other paper, so the split costs nothing outside this file.

**I.2 `rem:oneway-rule`, l.259–299, 41 lines.** Three arguments: the
inaccessibility is rule content and not a theorem (the $N$-steps-per-closure
counter); there is an economic and minimum-description reason to *expect* the
locked case; and the failure to guard against is the promotion of a
well-founded assumption to a theorem. **Fix:** split at l.286 ("There is an
economic reason to expect the locked case"). The first keeps
`rem:oneway-rule` — **this label is cited three times from other papers and
must not move or change kind**. The remainder becomes
`\begin{remark}[The locked case is the cheaper hypothesis, which is not a proof]\label{rem:locked-cheaper}`,
carrying l.286–299 including the closing guard, which is the punchline of the
economic argument and not of the rule-content one.

---

## J. "the base paper" is not a name on the set's list

l.39–41, the draft box: "The other documents of the programme named below carry
short names too, and **those are the only forms used**: \emph{Is} (the base
paper), the mind companion …". 01's companion table (its l.83–104), which is the
set's canonical list, gives *Is* the short name *Is*. "The base paper" is a
second form offered in the same sentence that declares there is only one, and
it appears nowhere else in the file — the two body citations at l.512 and l.911
both say "\emph{Is}".

**Fix.** Delete the parenthesis: "\emph{Is}, the mind companion (\emph{\ldots\
Mind and Self Grounding}), the momentum paper, and the Born note
(\emph{\ldots\ Born Recovery})."

---

## Smaller

1. **The complex-over-real numbers have no `\ref` to the note that tabulates
   them.** l.754–755 ($K=4$ vs $K=3$), l.763 ($K_{AB}=16$), l.765 ($K_{AB}=10$)
   are the numbers of 01d's Hardy-$K$ table (its l.259–271) and its
   `prop:contingent` (l.286–293), and the sentence at l.768–769 ("seeking to
   force complex over real would contradict the framework's own stance") is
   01d's `rem:misframing` (l.295–306) compressed. Under the agreed division this
   paper carries the verdict and the note carries the table. **Fix:** at l.765
   add "(the Born note tabulates the fiducial counts and states the verdict as
   its Proposition~\ref{BN-prop:contingent})", and cut l.768–769, which the
   preceding two sentences already say.
2. **`rem:recover` is said in both papers.** l.774–775 "Recovery, not
   derivation, is the honest verb and the right one: a contingent law is
   recovered given its rule-content, never derived as compelled" is 01d's
   `rem:recover` (l.106–120) title plus its closing sentence. This paper's
   version is the conclusion of an argument it has just made, so it keeps the
   clause; add "(the Born note holds this as its Remark~\ref{BN-rem:recover})"
   so the two do not read as independent findings.
3. **The inner-product identification is also doubled**: l.751–752 "So the inner
   product is not imported structure but the framework's own cross-frame
   reading" is 01d's `rem:identifications` (l.335–345). This paper argues it
   (l.746–758) and should keep it; the note is the one that should cite.
4. **The concluding line repeats the proposition verbatim.** l.1302 "With both,
   $H=\sum_k n_k\hbar\omega_k\ge 0$ term by term" is l.1268–1269 word for word.
   **Fix:** "That is both premises, and the proposition follows."
5. **01a and 01d cite different targets for the same first law.** l.797–799
   attributes "a frame carries its present structure forward until a write" to
   `NM-rem:momentum-delta` and `NM-prop:historical-sufficiency`; 01d's
   `prop:opt` (l.144–151) attributes the same law to `NM-sec:law` and
   `GE-cor:history`. All four resolve. §C's rewrite removes this site from 01a,
   which settles it; if the paragraph is kept instead, match the note's targets.
6. l.1256 "\citet{rothe2006} report the crossing at around ten" — "at around
   ten" wants its unit said: "at around ten lifetimes", since the preceding
   clause introduces "many lifetimes in" and the number is otherwise bare.

---

## What is right and should not be touched

- `def:three-c` and `prop:c-unit`, and the two paragraphs at l.139–165 on what
  is and is not stipulated — the Gorard contrast, and "the invariance costs
  nothing to assume because it is a fact about self-measurement, and the
  variation in cycle length … carries the physics". This is the sharpest thing
  in the paper.
- The one-way sequence entire as a sequence: `rem:oneway` → `rem:oneway-rule` →
  `prop:closure-three` → `rem:reichenbach-malament` → `rem:one-move`, and
  especially "Definable is not measurable, and unmeasurable is not arbitrary"
  and the three-case sort with the Hau ratio as the positive case.
- `rem:two-decoherences`: einselection imported, not recovered, and the relation
  offered as a shape rather than an identity.
- `sec:amplitudes`'s arithmetic: the phase-average identity, the quartic
  overshoot, the linear $4/\pi\neq2$, and Gleason's dimension-$\ge3$ scope. All
  check.
- `prop:dim-boundary`'s consequences: the ratio/label dichotomy, "only a ratio
  can vary", the $\Delta\alpha/\alpha$-not-$\Delta c$ observation, and the
  denominator-size search strategy with its own falsifier.
- `sec:decay` as reworked: the deviation required rather than tolerated, the
  exponent principled-not-fixed, and "one identification is doing the work"
  named rather than buried.
- `rem:spin-stat`: the identity argument does not select fermions, said plainly.
- `sec:prior-art`: D'Ariano–Tosini and Knuth–Bahreyni given their priority,
  Müller 2020 as "the most direct competitor", Höhn's rebits as independent
  support for the paper's own contingency verdict, QBism as the foil,
  constructor theory as competition on the explanandum rather than on the
  derivation.
- The falsifiability list's structure: 01's definition sentence verbatim,
  self-location moved out as a consequence, the scope note in short form after.

---

## Suggested order

1. **A** — the demon corollary; it is a physics error and an internal
   contradiction, and the fix is four sentences.
2. **B** — the two labels, coordinated with the 01d agent (four call sites move
   in the note).
3. **C**, Smaller 1–3 — the Born-note division, all in one pass over
   `sec:amplitudes`.
4. **D**, **E** — the two substantive physics passages.
5. **F**, **G**, **H**.
6. **I**, **J**, remaining Smaller.
