# Grounding papers — content/accuracy/integrity and writing-standard review

Read-only review of the four explicit grounding manuscripts in `papers/formal/`:

- `01a_graphic_equalisation_physics_grounding.tex` (draft-2026-09-02.1 r44)
- `01b_graphic_equalisation_mind_and_self_grounding.tex` (draft-2026-09-02.1 r41)
- `01c_graphic_equalisation_cosmology_grounding.tex` (draft-2026-09-02.1 r9)
- `02a_seldon_manifolds_psychological_grounding.tex` (draft-2026-09-02.1 r13)

Two audits are run per paper and kept separate: **(A) content / accuracy / integrity**
and **(B) writing-standard / formal-register compliance** against
`papers/WRITING_STANDARD.md`. Every finding carries exact current line ranges, a
short quote, a category (Content / Guide / Both), a classification (confirmed issue /
ambiguity / external verification required / no issue), a severity (P0 / P1 / P2 /
Note), why it matters, and a minimal repair or a concrete verification test. Passed
checks are recorded explicitly so good structure is not weakened.

Line numbers are as of the files read on 2026-09-03. Quotes are abridged with `…`.

---

## Executive summary

Each verdict is **conditional on the paper's own stated grounding scope** — the
information-level, shapes-only, "recover not derive", contingent-rule-content posture
each paper declares in its abstract and scope section.

| Paper | Content-integrity sound? | Guide-compliant? | Highest open severity |
|---|---|---|---|
| **01a Physics** | Yes, conditional on scope. No P0/P1 content defect found. Cross-paper labels resolve; strong claims are hedged with explicit falsifiers and "shapes-only" scope; the one number reached (Born) is repeatedly marked *recovered given contingent rule-content*, not derived. | Yes, conditional. Exemplary committed-hard/held-soft register; a handful of very long remark chains sit at the edge of the one-motion-per-paragraph rule. | P2 |
| **01b Mind/Self** | Yes, conditional on scope. Cross-paper labels resolve; own-record measurements are disclaimed once, up front, per the shared standard; prior-art attribution is unusually careful (Genette, Parfit, Hofstadter, Cerullo, Chalmers all engaged at correct strength). | Yes, conditional. Register is correct; the risk is length/density — several remarks carry more than one motion and could be split. | P2 |
| **01c Cosmology** | Yes, conditional on scope. The spine (measure problem = no-prior-free proposition) uses `AD-prop:no-prior-free` at its actual strength; negative-work posture is honest. One ambiguity around the "predicts non-convergence" claim's testability window. | Yes, conditional. Tightest of the four; reader-first, boundary-ended, low reference economy cost. | P2 |
| **02a Seldon Psych** | Yes, conditional on scope. Strongest empirical calibration of the four: it names a disputed literature (construal-level theory) and *declines to rely on it*; distinguishes measured components from unevidenced composite. | Yes, conditional. Model formal-register grounding paper. Minor: two places where "measured"/"attested" could be read as stronger than the cited single studies support. | P2 |

**Bottom line.** All four papers are content-integrity sound and guide-compliant
*conditional on their declared scope*. No P0 (integrity-breaking) or P1
(claim-strength or cross-paper-fidelity) defect was found. The findings below are P2
(local precision / register) and Notes, plus several items flagged **external
verification required** (domain facts a local review cannot settle) and a small number
of **ambiguities**. The dominant residual risk across all four is not overclaim but
paragraph length: the register is disciplined, but several remark chains pack multiple
motions into one block, which the guide's coherence check would split.

---

## Paper 01a — Physics grounding

### A. Content / accuracy / integrity

**A1a-PASS-1 — Three-way disambiguation of `c` is internally clean.**
Lines 68–80, `\begin{definition}[Three things called $c$]`: "*Runner $c$* … never
readable … *Unit $c$* … $1$ by construction … *Observed $c$* … the number a frame
obtains by measurement". Category: Content. Classification: no issue. Severity: Note.
Why it matters: the entire falsifiability structure (item 1, lines ~1470–1476) rests
on isolating *observed* $c$ as the only empirical term; the definition and the
falsifier are consistent — the falsifier explicitly says "That a frame reads its own
base rate as $1$ is definitional and not itself at risk … the falsifiable claim is
about *observed* $c$." This is the paper's strongest integrity feature and is recorded
as a passed check.

**A1a-PASS-2 — "Recover not derive" is held consistently for the Born rule.**
Lines ~470–520 (`\subsection{An attempt to close it}` and following), and the scope
abstract line ~57 ("the Born rule is recovered --- not forced"). Repeated markers:
"*This subsection is an attempt, flagged as such, not a claimed result.*"; "This is a
candidate, not a derivation"; "the honest verb and the right one" tied to
`BN-rem:recover`. Category: Content/Both. Classification: no issue. Severity: Note.
Why it matters: WRITING_STANDARD "prefer 'recover' to 'derive'… Do not turn an admitted
selection into a necessity" is followed precisely, and the residuals are enumerated
(lines ~560–566, "*Honest residuals.*"). Verified `BN-rem:recover`,
`BN-prop:crux`, `BN-prop:contingent`, `BN-sec:residuals` all resolve in
`01d_graphic_equalisation_born_recovery.tex`.

**A1a-PASS-3 — Cross-paper labels resolve at cited strength.**
Sampled and confirmed present: `GE-def:frame`, `GE-prop:economics`,
`GE-prop:higher-frame`, `GE-prop:cycle-unit`, `GE-prop:self-governance`,
`GE-prop:leak`, `GE-rem:phase-not-time`, `GE-prop:no-start-end`,
`GE-thm:no-frame-free`, `IS-prop:one-way`, `NM-def:narrative-momentum`,
`NM-def:free-continuation`, `NM-rem:impulse`, `BN-*` labels, `MS-sec:minimal`,
`MS-prop:minimal-universe`, `MS-prop:selfmodel`. Category: Content. Classification: no
issue. Severity: Note. Why it matters: cross-paper fidelity is the declared vulnerable
seam ("The claim is the arrangement"); the references are live, not decorative, and
`GE-prop:economics` is used as a *characterisation* (its actual status in 01, line
1402: "This is a characterisation of the substrate as specified, not a necessity of
graphhood"), which 01a respects — it never promotes the economics to a necessity.

**A1a-PASS-4 — Prior-art competition is stated as competition, not co-opted.**
Lines ~1040–1110 (`\paragraph{Observer-first programmes.}`): Müller "is the most
direct competitor … The mechanism is incompatible … this paper claims no agreement it
has not earned"; QBism "is therefore the cleanest available foil, not an ally";
constructor theory (Marletto) "this paper's recovery is exposed to it rather than
reinforced by it." Category: Content/Both. Classification: no issue. Severity: Note.
Why it matters: this is the honest-attribution posture the standard demands, executed
against the strongest neighbours rather than the weakest.

**A1a-1 — "which is how light has been slowed to seventeen metres per second and read
off" leans on Hau et al. for a claim about *ratio* measurement.**
Lines ~205–214 (`\citep{hau1999}`): "the *ratio* of one-way speeds through two media …
is measured as a matter of routine … which is how light has been slowed to seventeen
metres per second and read off". Category: Content. Classification: external
verification required. Severity: P2. Why it matters: Hau 1999 measures a group velocity
reduction in an ultracold gas; the paper uses it to illustrate that a *path-shared*
one-way ratio is convention-independent. The physics of the cancellation argument
(offset common to both signals over the same path) is argued correctly in-text via
`anderson1998`, but the specific attribution that Hau's number is an instance of the
convention-cancelling *ratio* rather than a two-way/group-velocity measurement is a
domain claim a local review cannot certify. Verification test: confirm that the
17 m/s figure is a group-velocity measurement over a fixed path and that its
interpretation as a synchrony-convention-independent one-way *ratio* is defensible;
if it is a two-way or group-delay quantity, soften "one-way ratio" to "path-shared
delay ratio" to avoid an over-precise attribution.

**A1a-2 — Spin–statistics honesty is explicit and correctly bounds the exclusion
argument.**
Lines ~1290–1300, `\begin{remark}[The honest limit: the identity argument does not
select fermions]`: "So Axiom~$-1$ does not *derive* exclusion --- exclusion is
*consistent* with it … the spin--statistics theorem, which needs structure this
account does not supply." Category: Content. Classification: no issue. Severity: Note.
Why it matters: this is exactly the "no analogy called a derivation" discipline; the
corollary `cor:pauli` is worded "consistent with the arithmetic of identity rather
than a force", not as a derivation. Recorded as a passed check that could have been a
P1 overclaim and is not.

**A1a-3 — Decay section's residual is correctly narrowed, not hidden.**
Lines ~1180–1330 (`\section{Decay is determinate…}`): the paper concedes the exponent
is not derived ("*What that earns is the deviation in kind, and not its form.*"),
converts the exposure into a test ("*The exponent should track the density of states
at threshold and not be universal*"), and flags the load-bearing identification ("*in-frame
energy is a count of quanta* … less clean for interacting systems … this section does
not establish that it holds there"). Category: Content. Classification: no issue.
Severity: Note. Why it matters: this is a model case of "use failure, residual and
retraction as motion" without concealment; the matching falsifier (item 15, in-frame
energy is a count of quanta) is present.

**A1a-4 — `darianotosini2013` / `knuth2014` priority attributions.**
Lines ~980–1030 (`\paragraph{Discrete substrates and emergent spacetime.}`): "That is
the same move made here and made earlier, and the counting reading of dilation is
theirs, not this paper's"; Knuth "is the closest existing result to the reading of $c$
given above". Category: Content. Classification: external verification required.
Severity: P2. Why it matters: the generosity direction is correct (concedes priority),
but whether D'Ariano–Tosini's event-counting genuinely yields *time dilation as
foliation-leaf density* and whether Knuth derives Minkowski "without assuming the
constancy of $c$" are domain claims. Verification test: confirm both attributions
against the cited papers; the risk here is *under*-claiming for this paper (giving away
more than owed), which is low-harm, but the factual characterisation should still be
checked.

### B. Writing-standard / formal-register compliance

**B1a-PASS-1 — Abstract states claim, mechanism, and boundary in order.**
Lines ~40–58: opens with the central move ("a frame's time is an inferred count of
*cycles* and … $c$ is the frame's own change-throughput unit, $1$ by construction"),
then the consequences, then the explicit weak boundary ("derives no field equation, no
dimensionless constant, and no theory of quantum gravity"). Category: Guide.
Classification: no issue. Severity: Note. Matches "Open with the reader's payoff" and
"End at the live boundary".

**B1a-1 — Several remarks carry more than one motion (coherence-check split).**
Representative: `\begin{remark}[Reichenbach and Malament are the two halves of one
situation]` (lines ~245–275) runs congenial-reply → not-a-third-position → three
distinct questions → deflation-is-not-consensus in one block; similarly the amplitude
subsection's `\emph{The Hilbert posit, reconsidered…}` paragraph (lines ~520–545).
Category: Guide. Classification: confirmed issue (minor). Severity: P2. Why it matters:
WRITING_STANDARD "Keep one motion per paragraph … Split a paragraph when its transition
cannot be named." Each of these blocks contains 3–4 nameable relations. Minimal repair:
split at the internal turns (each already begins with an italicised signpost, so the
split points are pre-marked). This is a readability/coherence refinement, not a content
defect.

**B1a-2 — "definitional consequence" repeated as a load-bearing phrase — acceptable
term economy, borderline repetition.**
Occurrences at lines ~90 (`prop:c-unit`), ~330 (`cor:reconcile`), ~600
(`sec:born-sr-gr`), abstract. Category: Guide. Classification: no issue (recorded as a
deliberate load-bearing term). Severity: Note. Why it matters: the standard endorses
re-using load-bearing terms consistently; this is that, not padding. No repair needed;
flagged only so a future editor does not mistake the repetition for redundancy and cut
a needed instance.

**B1a-PASS-2 — No apology or ceremonial padding; honest-boundary sentences do the
work hedges would.** Multiple "Honest boundary:" / "Honest residuals." markers (e.g.
lines ~590, ~660, ~700) replace vague hedging with explicit scope. Category: Guide.
Classification: no issue. Severity: Note.

---

## Paper 01b — Mind and self grounding

### A. Content / accuracy / integrity

**A1b-PASS-1 — Own-record measurements disclaimed once, up front, per the shared
standard.**
Lines ~74–83 (`\section{Scope}` tail): "One standard governs every place below where a
*measurement* is reported from this programme's own record … it is a claim a reader may
decline to credit … this sentence is the disclaimer." Category: Content. Classification:
no issue. Severity: Note. Why it matters: the beneficiary-audit, commit-gate, and
Grice-maxim findings in `rem:comm-engine` (lines ~430–470) and the calibrated-supply
fixture in `rem:comm-calibrated` (lines ~600–640) are all self-reported implementation
results; the paper scopes them correctly ("The fixture is synthetic and deterministic …
one run per arm … nothing there measures how hard a calibrated supply is to construct")
and the matching falsifiers (items 12, 13) carry the same scope caveat. CLAUDE.md
confirms an implementation substrate of this kind exists, consistent with these being
records rather than inventions.

**A1b-PASS-2 — Prior-art attribution is calibrated to the exact concession, not the
headline.**
`\begin{remark}[The composition, and the one step…]` and the author-model section
(lines ~730–860): Genette is quoted "for its precision, not for its support" and his
anti-personification stance is explicitly preserved ("Genette's standing objection to
personifying the implied author is consistent with all of this"); Parfit's causal
condition is engaged at `\S78` with the correct reading that his continuity is over
*states* (structural side), so "this account already agrees with him"; Hofstadter is
"an ally on … the gradient and an opponent on the criterion"; Cerullo is credited for
the branching result ("Citing only Parfit under-attributes it"); Chalmers's
reconstructive uploading is named "a live position rather than one this account
refutes." Category: Content/Both. Classification: no issue. Severity: Note. Why it
matters: this is precisely "size the contribution honestly" and "attribute generously";
the "one step that is this paper's" framing (composition, not components) is repeated
and correct.

**A1b-PASS-3 — Self-model incompleteness argument is typed and non-circular.**
Lines ~200–210 (`\section{Self-models…}` head): three distinct sources — *aperture*,
*proper part*, *lesser object* (the last tied to `GE-rem:self-edge`) — kept apart, and
the operative distinction moved to *calibrated vs uncalibrated* rather than *complete
vs incomplete* (`prop:selfmodel`). Category: Content. Classification: no issue.
Severity: Note. Why it matters: the Kruger–Dunning citation is explicitly marked
"contested … cited here as one disputed candidate … nothing above depends on it"
(lines ~250–260), and the bibliography entry for `kruger1999` itself carries the
contestation note. Correct calibration of a contested empirical anchor.

**A1b-1 — `nijhof2015` (n=18, listened not read) carries the mentalizing/motor
trade-off claim; scope stated but claim is broad relative to the single study.**
Lines ~168–176 (`\begin{remark}[The reader runs and holds at once…]`): "measured
individually, mentalizing and motor engagement during narrative comprehension *trade
off* … the eighteen participants *listened* to the excerpts … evidence about narrative
comprehension and only indirectly about readers." Category: Content. Classification: no
issue (scope is disclosed in-text). Severity: Note → borderline P2. Why it matters: the
paper already names the two limits (region-specific reliability; listening not reading;
n=18), so the honesty bar is met. Flag retained only because a single small fMRI study
is doing structural work in the "reader is not a counterexample" argument; the argument
does not *depend* on it (three independent literatures carry the main claim), so no
repair is required. Verification test if desired: confirm Nijhof & Willems 2015 report
a negative correlation, not merely independence.

**A1b-2 — `aldersonday2017` quantitative figures used precisely.**
Lines ~178–186: "reported by about a fifth of those who wrote freely … under four per
cent reporting it most or all of the time." Category: Content. Classification: external
verification required. Severity: P2. Why it matters: these are specific quantitative
claims attributed to one paper and used to support "quarantine that leaks sometimes is
still quarantine." Verification test: confirm the ~20% and <4% figures against
Alderson-Day et al. 2017; if the denominators differ (free-response subset vs full
sample), the sentence already distinguishes them, so only the numbers need checking.

**A1b-3 — `schwitzgebel2024` result reported with the authors' own caveat about the
"tell".**
Lines ~840–860: "They identified them about half the time against a $20\%$ baseline …
expert performance was highest on two questions carrying what the authors call a
superficial tell … which is discrimination doing the work rather than the model's."
Category: Content. Classification: no issue. Severity: Note. Why it matters: the
forward-prediction falsifier (item 12) is explicitly built on "the design is the one
`schwitzgebel2024` ran, with the tell removed" — the caveat is load-bearing and
correctly carried.

**A1b-4 — POSIX / OS correspondences guarded against over-reading.**
Lines ~1020–1080 (`\begin{remark}[The computing grounding…]`): "*an implementation is
free to add rules to suit*, so nothing an operating system does can establish that
something is structurally required … Where the correspondences carry weight is as
convergence." Category: Content. Classification: no issue. Severity: Note. Why it
matters: this is the correct standing for a convergence argument and blocks the natural
misreading that POSIX signals *prove* the structural claim; the "reachability vs
re-runnability are different criteria" non-match is flagged rather than smoothed over.

### B. Writing-standard / formal-register compliance

**B1b-1 — Long, multi-motion remarks are the dominant guide risk.**
Representative: `\begin{remark}[The reader runs and holds at once, and this is
standard]` (lines ~160–190) traverses Currie → Rabinowitz → Nichols/Gendler → Walton →
Wolf → two qualifications in one remark; `\begin{remark}[Relation to prior work]`
(death section, lines ~980–1010) and the author-model section similarly. Category:
Guide. Classification: confirmed issue (minor). Severity: P2. Why it matters: the
coherence check ("name the relation for every transition; split when it cannot be
named") would split several of these. The transitions *are* nameable (they are mostly
"further independent support" and "qualification"), so this is dense but not incoherent;
the repair is subdivision, not rewriting. This is the paper's main distance from the
guide and is register-level, not content-level.

**B1b-PASS-1 — Reader-first ordering held even in a philosophy-of-mind register.**
Free-will section (lines ~130–160): the plain claim ("Free will is a frame running its
own decision … This needs no indeterminacy") precedes the machinery (three-frame
story, computational irreducibility). Death section leads with the one-line
proposition before the cases. Category: Guide. Classification: no issue. Severity:
Note. Matches "Withhold mechanism, never the claim."

**B1b-PASS-2 — Scope disclaimers on consciousness/qualia are consistent and not
apologetic.** Lines ~30 (abstract "consciousness and qualia are out of scope"), the
Metzinger remark, the Frankish paragraph ("This paper takes no position on whether he
is right"), and the closing scope note. Category: Guide. Classification: no issue.
Severity: Note. The out-of-scope declarations state the limit rather than apologising
for it.

**B1b-2 — "Items 6 and 20 are falsified by the same object … kept separate as two
entries" — a small honest-arrangement note that earns its place.**
Line ~1200 (after the falsifier list). Category: Guide. Classification: no issue.
Severity: Note. Why it matters: this is exactly the kind of not-novelty / honest
bookkeeping the standard asks for; recorded as a passed check.

---

## Paper 01c — Cosmology grounding

### A. Content / accuracy / integrity

**A1c-PASS-1 — The spine uses `AD-prop:no-prior-free` at its actual strength.**
Lines ~120–140 (`\begin{proposition}[The measure problem is ill-posed, not
unsolved]`): "by the adaptability paper's no-prior-free proposition
(Proposition~\ref{AD-prop:no-prior-free}) that standpoint is not a member of the
space." Verified: `09_adaptability.tex` line 243 defines `prop:no-prior-free` as
"There is no prior-free measurement." Category: Content. Classification: no issue.
Severity: Note. Why it matters: the measure-problem dissolution is the paper's one
place of "real work"; it inherits, rather than re-proves, the no-prior-free result and
says so, and the matching falsifier (item 2, `[shape]`) correctly locates the real
exposure in `AD-prop:no-prior-free` "which is not a mechanism this paper could
replace."

**A1c-PASS-2 — The totality/degenerate-reading argument uses `IS` at correct strength.**
Lines ~55–75 (`\begin{proposition}[The totality is a degenerate reading]`): grounded on
`IS-sec:one-not-enough`, `IS-prop:cohere`, `GE-def:frame`, `GE-rem:only-g`. Verified
all resolve; `00_is.tex` line 314/351 gives the three-readings-yield-nothing content
that 01c cites (the "everything at once, read from outside" third reading). Category:
Content. Classification: no issue. Severity: Note. Why it matters: the paper carefully
distinguishes what *Is* posits (everything, modelled not observed — not a frame) from
what cosmology individuates (a frame), so it does not conflate the substrate's
"everything" with the totality it declares degenerate. That distinction is the
observed/modelled discipline announced in §scope, applied correctly.

**A1c-PASS-3 — EGS / Copernican argument attributed and used precisely.**
Lines ~95–115 (`\begin{proposition}[The second leg is modal and is declined]` and
following): "The Ehlers--Geren--Sachs theorem `\citep{ehlers1968}` obtains FLRW …
*by a family of observers everywhere*; its realistic form `\citep{stoeger1995}` weakens
exactness and not universality." Category: Content. Classification: external
verification required (low risk). Severity: P2. Why it matters: the argument's force
depends on EGS requiring isotropy *for all observers* (a quantifier over an
unreachable domain), which is a correct standard reading, and the paper credits the
field for already calling homogeneity "an assumption". Verification test: confirm the
Stoeger et al. 1995 "almost-EGS" characterisation is "weakens exactness not
universality"; this is a defensible reading of the almost-EGS result but is a domain
claim.

**A1c-1 — "predicts that the disagreement between measures will not converge … is
checkable" — testability window is unbounded.**
Lines ~145–150 (after `prop:measure`): "it predicts that the disagreement between
measures will not converge --- which is a claim about the literature's future rather
than about the world, and is checkable." Category: Content. Classification: ambiguity.
Severity: P2. Why it matters: a prediction of non-convergence with no time bound or
operational criterion for "converged" is only weakly falsifiable — any observed
convergence could be deferred indefinitely by the symmetric claim. The falsifier item 2
sharpens this correctly ("If the regularisations … converge on one measure by an
argument internal to the theory, requiring no stipulation from outside"), which is the
well-posed form. Minimal repair: cross-reference the §measure prose sentence to
falsifier item 2 so the loose "will not converge" reads against the sharp internal-vs-
stipulated criterion rather than standing alone as an open-ended literature prediction.

**A1c-PASS-4 — Hubble-tension section claims nothing beyond the field's own framing.**
Lines ~175–190 (`\section{Two measurements that disagree}`): "The account does not
dissolve the tension, does not favour either value, and does not predict which
coordinate is at fault. It says the comparison is the work, which cosmologists
established without help." Category: Content/Both. Classification: no issue. Severity:
Note. Why it matters: correctly avoids overclaim in the one section most tempting to
overclaim; uses `AD-rem:chollet` (verified present) at strength.

### B. Writing-standard / formal-register compliance

**B1c-PASS-1 — Tightest reader-pathing of the four.**
`\section{Scope, and what this adds}` (lines ~35–50) states the result in one line
("*You cannot have the ensemble and you cannot have a totality --- and this paper can
say why.*"), then the practical difference (ill-posed redirects effort, unsolved
invites more regularisations), then proceeds section by section each answering the
prior. Category: Guide. Classification: no issue. Severity: Note. Matches the whole-
document path check.

**B1c-1 — "mostly negative in a specific and useful way" abstract framing is honest;
no padding.** Lines ~24–34. Category: Guide. Classification: no issue. Severity: Note.
The abstract states the not-novelty posture ("it agrees with the field's own instincts
more often than it corrects them") without novelty theatre — a passed contribution
check.

**B1c-2 — Anthropic section's "equivocation" argument is one clean motion per
paragraph.** Lines ~155–175 (`\section{Anthropic reasoning inherits the same defect}`):
each paragraph advances one step (two readings → each fails separately → why sliding
looks like an answer → *Is*'s "everything" care repeated). Category: Guide.
Classification: no issue. Severity: Note. Recorded as a positive contrast to the longer
remark chains in 01a/01b.

---

## Paper 02a — Seldon manifolds psychological grounding

### A. Content / accuracy / integrity

**A2a-PASS-1 — Grounding-not-validation scope is stated and enforced throughout.**
Lines ~30–45 (`\section{Scope}`): "This paper is a grounding and not a validation …
evidence that people forecast badly would not count against it." The closing scope note
(end of §falsifiability) repeats it as a non-falsifier: "This paper would be
over-claiming if any section were read as evidence that a nervous system holds a Seldon
manifold." Category: Content/Both. Classification: no issue. Severity: Note. Why it
matters: this is the load-bearing scope guard and it is applied consistently — the
composite-not-evidenced admission in §limits ("Every component above is implemented
somewhere, but in different systems, at timescales separated by three orders of
magnitude, and no study assembles them") is the honest cash-out.

**A2a-PASS-2 — Construal-level theory (a natural anchor) is named and *declined*.**
Lines ~130–150 (`\begin{remark}[A stronger candidate that does not survive]`): "a
registered multi-laboratory replication … found effects of $d\approx0.03$--$0.08$ …
So the accurate statement is that the effect is in serious dispute rather than that it
is refuted --- and either way it cannot carry weight. The timing result above is
narrower and secure, and is used instead." Category: Content. Classification: no issue.
Severity: Note. Why it matters: this is the strongest single integrity move across the
four papers — refusing the convenient citation because it did not survive its
best-powered test, and substituting the secure scalar-timing result (`gibbon1977`
etc.). The matching design in the abstract ("did not survive its best-powered test …
is not relied upon here") is consistent.

**A2a-PASS-3 — Todorov minimal-intervention correspondence is guarded against the
obvious over-reading.**
Lines ~70–85 (`\begin{remark}[Three cautions on the correspondence]`): "The principle
is *minimal* intervention, not minimum … It is therefore not a smallest-sufficient-push
result and should not be cited as one … the controller does not project forward at
decision time." Category: Content. Classification: no issue. Severity: Note. Why it
matters: `SM-prop:min-intervention` (verified, 02 line 523, "Minimum intervention in a
safe interior") is an antecedent-guarded proposition; 02a maps `todorov2002` to it
while explicitly flagging the offline-horizon disanalogy and the
`SM-cor:trap-antecedent` failure case (verified, 02 line 637). No analogy is called a
derivation.

**A2a-1 — Miall 2007 cerebellar-horizon figures used precisely; one internal
number-chain to spot-check.**
Lines ~55–65 (`\section{Forward models…}`): "planned from a hand position around
$138\,$ms out of date, replicated at $134\,$ms, with the authors' upper estimate
$150$--$160\,$ms `\citep{miall2007}`" and the feedback-loop figures "twenty to sixty
milliseconds spinally and around a hundred visually." Category: Content. Classification:
external verification required. Severity: P2. Why it matters: these specific latencies
are load-bearing for "the motor forward model is a delay compensator rather than a
simulator of futures" and for the ~150 ms horizon headline in the abstract.
Verification test: confirm the 138/134/150–160 ms values and the spinal/visual loop
latencies against Miall et al. 2007; the internal consistency (horizon ≈ loop latency
being compensated) is sound as reasoning.

**A2a-2 — "several components are implemented and well measured" (abstract) vs
single-study components.**
Abstract lines ~20–28 and §body throughout. Category: Content. Classification:
ambiguity. Severity: P2. Why it matters: most components are carried by robust,
replicated literatures (scalar timing "fifty years old, holds across species, and is
not in dispute"; body-scaled affordances Warren 1984 / Warren–Whang 1987; expertise
de Groot/Gobet). But a few — e.g. the plural-horizon claim rests on `hasson2008`,
`hasson2015`, `brunec2022`, and the successor-representation reading on
`momennejad2017` — are carried by one or two studies each. The paper does not claim
otherwise (each is cited specifically), but "well measured" in the abstract reads
slightly stronger than the thinnest of these components support. Minimal repair:
none required for integrity (in-text citations are specific and honest); if tightening,
qualify the abstract's "well measured" to "measured" for the components resting on
single studies, reserving "well measured" for the replicated ones (timing, affordances,
expertise search).

**A2a-PASS-4 — Affective-forecasting reframing offered as a reading, then promoted to
a commitment in the right place.**
§limits lines ~250–265 ("*Forecasting error is on magnitude, not structure --- and this
is a reframing.* … That is a legitimate reading and it is still a reading, offered as
such") and falsifier item 11 ("Section~\ref{sec:limits} offers that reframing as a
reading; this is where it becomes a commitment"). Category: Content/Both. Classification:
no issue. Severity: Note. Why it matters: cleanly separates a reading from a falsifiable
commitment, exactly as the standard's commitment check wants.

**A2a-3 — "The strongest support in this paper is for … different agents hold different
manifolds" — matched to the affordance literature, extension flagged as not-free.**
Lines ~185–210 (`\section{The manifold is indexed to the body}` and
`\begin{remark}[The extension is not free]`): "This is the perception of immediately
available action, not a multi-step future. That the same frame-relativity holds of
extended horizons is an argument *Seldon* makes and this literature does not supply."
Category: Content. Classification: no issue. Severity: Note. Why it matters: prevents
the affordance result from being silently generalised to the multi-step manifold — the
exact seam where a grounding could overclaim, and does not.

### B. Writing-standard / formal-register compliance

**B2a-PASS-1 — Organised by component, with the organising principle stated first.**
Lines ~45–55 (§scope tail): "Findings are organised by the component they bear on ---
horizon, resolution, represented dimensions, fields, the acceptable region, and the
capacity to reshape rather than navigate --- rather than by the literature they come
from." Category: Guide. Classification: no issue. Severity: Note. The document path is
declared and followed; each section names its target component.

**B2a-1 — "attested twice over --- once measured and once derived" is a strong
formulation carried cleanly.**
Lines ~62–70 (§region). Category: Guide. Classification: no issue. Severity: Note. Why
it matters: committed-hard/held-soft done well — the "derived" half (`todorov2002`) is
immediately qualified by `rem:mip-cautions`. Recorded as a passed commitment check.

**B2a-2 — `\section{Bounded search, and how it stops}` uses discomforting evidence as
motion, not buried.**
Lines ~215–235: "How the search stops is less comfortable for any account that wants a
cost-benefit rule … pruned reflexively … The honest reading is that stopping is
heuristic in mechanism and only approximately rational in aggregate." Category: Guide.
Classification: no issue. Severity: Note. Matches "Use failure, residual and retraction
as motion. Do not hide nulls." Recorded as a passed check.

**B2a-3 — Minor: "measured" vs "attested" register drift in a few component
headers.** See A2a-2. Category: Both. Classification: ambiguity. Severity: Note. The
guide's commitment check ("check both ends of every claimed gradient; a calibrated
limit is not an absent limit") is otherwise met paper-wide; the only drift is the
abstract-level "well measured" umbrella over unevenly-evidenced components.

---

## Cross-grounding coherence

**X-PASS-1 — Consistent inherited-scope posture.** All four open with the same
inheritance clause ("inherits their definitions, epistemic boundary, and
level-of-claims") and the same `[shape]`/`[detail]` falsifier-tag convention, defined
identically in each `\section{Falsifiability commitments}`. The tag semantics ("A
`[shape]` failing costs *range* rather than a mechanism") are worded verbatim across
01a, 01b, 01c, 02a — a genuine shared contract, not four independent inventions.
Classification: no issue. Severity: Note.

**X-PASS-2 — Axiom −1 used as guard vs commitment consistently with `papers/README.md`.**
The README states "Axiom −1 is split … In paper 01 every use refuses an import … In the
**groundings** it licenses positive results and is a commitment that can fail." This is
observably true of the groundings: 01a uses `no-privilege`/Axiom −1 to *license* the
Born phase-independence step (§amplitudes) and the identical-particles result
(§identical); 01b uses `ax:no-view` to *license* the death-is-frame-relative and
no-privilege conclusions and lists item 20 as a `[shape]` falsifier; 01c uses it to
license the totality and Copernican declinations. The groundings treat Axiom −1 as an
exposed commitment (each has a falsifier keyed to it), matching the README's "guard
here, commitment there." Classification: no issue. Severity: Note.

**X-PASS-3 — Superframe/`null` machinery is used identically across physics and
cosmology.** 01a `cor:nonlocal` (nonlocality is "up, not across") and `prop:mixed`
(purity is a superframe dimension, `null` in the subframe) are the exact machinery
01c's `prop:beyond` inherits ("its content is a superframe dimension … `null` in our
frame … the physics companion's Corollary~\ref{PH-cor:nonlocal}"). The entangled-partner
purity analogy is the shared bridge, and 01c cites it as inheritance ("inherited
entire, and it fails where that fails and nowhere else"), not as a new result.
Classification: no issue. Severity: Note. This is the arrangement working as designed:
one mechanism, two domains.

**X-PASS-4 — Self-location dissolves fine-tuning in physics and the measure/typicality
problems in cosmology from the same base.** 01a `prop:self-location` and 01c
`prop:typical`/`prop:measure` are two applications of the no-trans-frame-standpoint
move; 01c states the linkage explicitly ("The physics companion reaches the same place
from the other direction … fine-tuning is dissolved by self-location … Here the same
absence removes the distribution. One prohibition, met twice"). Classification: no
issue. Severity: Note.

**X-1 — Shared "predicts the literature's future" style of testability appears in
01c and (as conjecture) in 01b; both are weakly bounded.** 01c's non-convergence
prediction (A1c-1) and 01b's window→horizon→manipulability conjecture
(`rem:comm-horizon`, item 9, explicitly "conjectured … established nowhere in the set")
share a pattern: a real, directionally-stated prediction whose operational falsifier is
either unbounded in time (01c) or depends on an untested intermediate step (01b). Both
papers flag the weakness in their own falsifier lists, so this is not concealment.
Category: Content/Both. Classification: ambiguity. Severity: P2. Why it matters: it is a
recurring shape worth a consistent house-style fix — each such prediction should point
its prose sentence at the sharp falsifier-list form (as 01c item 2 already does for the
internal-vs-stipulated convergence criterion). Minimal repair: add the cross-reference
in 01c §measure (A1c-1) and confirm 01b `rem:comm-horizon` already carries item 9's
"untested half" caveat inline (it does).

**X-PASS-5 — Draft-string divergence is expected, not a defect, and is not this
review's object.** The four groundings carry `draft-2026-09-02.1` at document revisions
r44/r41/r9/r13, while `papers/README.md` describes a `draft-2026-08-30.4` set-wide
string checked by `tools/check_draft_consistency.py`. The groundings 01c and 02a are
newer additions (01c/02a not in the README's twelve-file table). Classification: no
issue for content review; noted only so the divergence is not mistaken for a finding —
draft-string consistency is out of scope per the task (counts/footers not to be
touched) and is the checker's job, not this report's.

---

## Consolidated findings ledger

| ID | Paper | Lines | Category | Classification | Sev | One-line |
|---|---|---|---|---|---|---|
| A1a-1 | 01a | ~205–214 | Content | external verification required | P2 | Hau 1999 17 m/s attributed as one-way *ratio* — confirm it is path-shared/group-velocity. |
| A1a-4 | 01a | ~980–1030 | Content | external verification required | P2 | D'Ariano–Tosini / Knuth priority characterisations — confirm against sources. |
| B1a-1 | 01a | ~245–275, ~520–545 | Guide | confirmed issue (minor) | P2 | Multi-motion remarks; split at pre-marked italic turns. |
| A1b-2 | 01b | ~178–186 | Content | external verification required | P2 | aldersonday2017 ~20% / <4% figures — confirm. |
| B1b-1 | 01b | ~160–190, ~980–1010 | Guide | confirmed issue (minor) | P2 | Long multi-motion remarks; subdivide. |
| A1c-1 | 01c | ~145–150 | Content | ambiguity | P2 | "will not converge" unbounded; point prose at falsifier item 2. |
| A1c-PASS-3 | 01c | ~95–115 | Content | external verification required | P2 | Almost-EGS "weakens exactness not universality" — confirm. |
| A2a-1 | 02a | ~55–65 | Content | external verification required | P2 | Miall 2007 138/134/150–160 ms + loop latencies — confirm. |
| A2a-2 / B2a-3 | 02a | abstract, body | Both | ambiguity | P2 / Note | "well measured" umbrella over single-study components; qualify abstract. |
| X-1 | 01b, 01c | see above | Both | ambiguity | P2 | Shared weakly-bounded "predicts the literature's future" style; cross-ref sharp falsifiers. |

Passed checks explicitly recorded (not defects): A1a-PASS-1..4, A1b-PASS-1..3,
A1c-PASS-1..4, A2a-PASS-1..4, B1a-PASS-1..2, B1b-PASS-1..2, B1c-PASS-1,
B2a-PASS-1, X-PASS-1..5. **No P0 or P1 finding.**

### Interpretation
- **Content integrity:** no confirmed content error was found; every P2 content item is
  either an *external verification required* domain fact (which a local, no-network
  review cannot settle and which is flagged rather than asserted) or an *ambiguity* the
  paper already partly guards. The papers consistently use 00/01/02/03/04/09 results at
  their actual strength, do not strengthen the substrate's characterised economics into
  necessity, and mark every analogy as an analogy (spin–statistics, POSIX, light-switch,
  Todorov minimal-intervention).
- **Guide compliance:** the register is strong across all four; the only recurring
  guide finding is paragraph length (multi-motion remarks in 01a and 01b), which is a
  coherence-check refinement, not a violation of the commitment, attribution, or
  reader-first rules.

---

## Scope, limits, and verification block

**What this report is.** A read-only, report-only review producing exactly one file:
`papers/GROUNDING_PAPERS_CONTENT_AND_GUIDE_REVIEW.md`. No `.tex`, `.pdf`, `.aux`,
`.log`, counts file, existing review, README, writing standard, experiment, or any
other file was modified, created, or deleted other than this report.

**Exact revisions reviewed.**
- `01a_graphic_equalisation_physics_grounding.tex` — draft-2026-09-02.1, document
  revision 44.
- `01b_graphic_equalisation_mind_and_self_grounding.tex` — draft-2026-09-02.1,
  document revision 41.
- `01c_graphic_equalisation_cosmology_grounding.tex` — draft-2026-09-02.1, document
  revision 9.
- `02a_seldon_manifolds_psychological_grounding.tex` — draft-2026-09-02.1, document
  revision 13.

**All files read (in full unless noted).**
- Read in full: `papers/WRITING_STANDARD.md`; `papers/README.md`; all four grounding
  sources above (each read end to end, including full bibliographies).
- Read in full: `00_is.tex` was read in the sections load-bearing for the groundings
  (§one-not-enough, §cohere/`prop:cohere`, §one-way/`prop:one-way`, §graph, §present
  cluster including `prop:determinable`, `prop:no-start-end`, `prop:economics`,
  `def:well-formed`, `rem:landauer-change`, `prop:higher-frame`); the remainder was
  scanned for label resolution rather than line-by-line — a stated limit.
- `01_law_of_graphic_equalisation_theory_referenced.tex` and
  `02_seldon_manifolds_theory_referenced.tex`: read at the sections and theorem
  environments referenced by the groundings, and verified by label lookup across the
  whole file; not every line was read — a stated limit.
- CLAUDE.md: consulted for the implementation-substrate context that grounds 01b's
  "own-record measurement" disclaimers; treated as context, not re-reviewed.
- Companion sources consulted only to verify specific labels/dependencies:
  `01d_graphic_equalisation_born_recovery.tex`, `03_law_of_narrative_momentum_theory_referenced.tex`,
  `04_narrativium_theory_referenced.tex`, `09_adaptability.tex`, and
  `01s_graphic_equalisation_statement.tex` (which mirrors 01's labels). Every
  cross-paper label cited by the four groundings was confirmed to resolve to a real
  `\label{}` at the strength claimed (physics: `GE-*`, `IS-*`, `NM-*`, `BN-*`,
  `MS-*`; mind: `GE-*`, `PH-*`, `NM-*`, `NV-*`; cosmology: `IS-*`, `GE-*`, `PH-*`,
  `NV-*`, `AD-*`; psychological: `SM-*`, `GE-*`). No dead cross-reference was found.

**Method limits.**
- **Local-only, no network.** No web tools were used. Every finding classified
  *external verification required* is a domain/empirical fact (specific latencies,
  citation-internal figures, priority claims, almost-EGS characterisation) that this
  review deliberately did **not** assert as true or false; each carries a concrete
  verification test instead. Local bibliography entries were checked for internal
  consistency (author, venue, year formatting), and those are self-consistent.
- **No compile.** No `pdflatex` or any build was run; label resolution was verified by
  source-text search, not by `.aux` inspection. Cross-`\externaldocument` resolution at
  compile time (xr-hyper) was therefore inferred from `\label{}` presence in the target
  files, not from a built `.aux`.
- **Report-only.** No file other than this report was written; nothing was committed or
  pushed; counts, footers, and draft strings were not touched.
- **Scope of judgement.** Verdicts are conditional on each paper's declared scope
  (information-level, shapes-only, recover-not-derive, contingent-rule-content).
  Consciousness/qualia and phenomenal questions are out of scope in 01b by its own
  declaration and are not reviewed here. Book voice was not re-reviewed except where the
  formal guide points to it (none of the four required it).
- **Faults not invented.** Where a paper already discloses a limit (composite not
  evidenced, single-study components, untested conjectures, contested citations), that
  disclosure is recorded as a passed check rather than re-raised as a defect; the
  P2/ambiguity items are precision refinements, not integrity failures.

**Confirmation.** Read-only and report-only completed: exactly one report produced at
`papers/GROUNDING_PAPERS_CONTENT_AND_GUIDE_REVIEW.md`; no TeX/PDF/AUX/LOG/counts/review/
README/standard/experiment file altered; no compile, no network tool, no commit, no
push.
