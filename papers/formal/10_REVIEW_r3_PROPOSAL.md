# Review of `10_applied_graphic_equalisation.tex` (draft-2026-09-02.1, r3) — proposal for fixes

Scope: the whole file (1810 lines, 30 pp), its log and aux, and 09
(*Adaptability*) for the results it uses. Line numbers are r3. Nothing
applied. The 2026 empirical inputs (CBO, IIF, V-Dem, COFER, BIS, the
Reflecting Pool filings, the interceptor counts, the carrier deployment,
the Senate absence) are outside what this review can verify; the review
checks whether they are *citable*, which is the paper's own standard.

Compile: 0 warnings, 0 overfull, all 33 citations resolve. The paper's
method — price operations, license nothing, admit no testimony, name no
private individual — is stated once and honoured throughout, and its best
results (aimed artefacts bound and unaimed records estimate; transitions
are keyed on documents, not states; a certificate is the conversion
relation; sustaining is a threshold so a foreseen decline arrives as a
shock; a system that adapts on surprise is blind to predicted decline) are
genuine applications of the substrate. The findings are: references to 09
that were flattened into ungrammatical prose; a falsifiability section the
paper refers to and does not have; nine bibliography entries that are not
citations; and the heaviest narrated drafting in the set.

---

## A. Every reference to the adaptability paper has been flattened into a phrase

The paper was split out of 09 and its `\ref`s to 09's results were
replaced by descriptive noun phrases. The result is ungrammatical at
thirteen sites (sentences beginning lowercase "the companion's …") and
unreadable at several more:

- l.153 "the companion's two clocks's first clock"
- l.156, 366, 695, 1272 "the companion's account of rules stated from
  nowhere's basin / sense / plainest form"
- l.143 "the companion's contingency result found institutions…" (sentence
  opens lowercase)
- l.312 "Definition of well-formedness's fourth cost at institutional
  scale"
- l.1067 "the companion's auditability condition's condition"
- l.685 "the companion's no-prior-free proposition's neighbour"

Sixty-eight occurrences of "the companion" in all. Every one maps to a
label in 09's current aux:

| phrase in 10 | 09 label |
|---|---|
| account of rules stated from nowhere | `rem:nowhere` |
| two clocks | `rem:timing` |
| payment-schedule result | `rem:schedule` |
| conversion-rate result | `rem:exchange` |
| bounded-against-compounding result | `rem:race` |
| underdetermination result | `rem:method` (verify against text: "machinery and mapping inseparable by measurement") |
| interval over reachability | `rem:interval` |
| bound on individual capacity | `rem:individual` |
| result on the unit of measurement | `rem:unit` |
| result that building goes uncounted | `rem:building` |
| auditability condition | `rem:direction` |
| regime argument | `rem:plural` |
| ladder | `sec:ladder` |
| account of a phase change | `rem:phase` |
| treatment of restored scarcity | `rem:scarcity` |
| contingency result | `rem:contingent` |
| account of expertise as a codebook | `rem:expertise` |
| reconstruction result | `rem:reconstruct` |
| account of priors | `sec:priors` |
| no-prior-free proposition | `prop:no-prior-free` |
| Definition of well-formedness / theory companion's fourth cost | 01 `def:well-formed` |
| Narrativium companion's cross-frame prohibition / stipulated vs principled | 04 `prop:no-sum`, `rem:kappa-kinds` |
| Seldon manifold definition | 02 `def:seldon` |
| revocation at Δg = 0 | 01 `cor:frame-dimension` |

**Fix.** `xr-hyper` with `[AD-]{09_adaptability}`, `[GE-]{01_…}`,
`[NV-]{04_…}`, `[SM-]{02_…}`; every phrase becomes "the adaptability
paper's Remark~\ref{AD-rem:nowhere}" (or a short gloss plus the ref);
sentence-initial lowercase repaired. Draft-box naming sentence with 01's
table names (the adaptability paper; Graphic Equalisation; *Seldon*;
*Narrativium*). This is mechanical and it is the single largest
readability fix available.

---

## B. The paper refers to a falsifiability section it does not have

l.1190–1191: "The only defence is to register the commitments before they
resolve, **which is what the falsifiability section exists for** and is
the reason it is not decorative." l.1163–1165: "both were produced under
pressure rather than declared in advance, and a retrofitted falsifier is
worth less than a pre-registered one — which this programme states
elsewhere and does not get to forget here." There is no falsifiability
section. The draft box omits the set's "Sections marked as falsifiability
commitments are the intended points of attack" sentence, which every
other paper carries.

**Fix.** Add `\section{Falsifiability commitments}` with 01's
`[shape]`/`[detail]` sentence verbatim, carrying what the body already
states as tests:

- `[shape]` **Amplitude runs inversely to deliberation** (`rem:lapse`):
  fails if, across an arrangement's channels ordered by the deliberation
  each requires, the change carried does not fall with that ordering.
- `[shape]` **Load goes where it is cheapest to place** (`rem:load`):
  fails if load is observed to find slack rather than low friction where
  the two diverge.
- `[detail]` **Lock-in, not preference** (`rem:steelman` l.1261–1270): the
  reserve share declines slowly and one-directionally with no fast exit;
  fails on a stable or rising share over a long horizon, or on a fast
  exit by any holder.
- `[detail]` **The rate condition on capability gains** (l.1135–1139):
  only gains propagating faster than frames absorb them widen the
  two-clock distance; fails if gains absorbed at the frame's own speed
  produce the same signature.
- `[detail]` **Sustaining is a threshold** (`rem:prop`): fails if an
  externally supported arrangement's transition is observed to be
  gradual rather than discontinuous.
- `[detail]` **Publicity converts efficiently into damage and
  inefficiently into repair** (`rem:counterfactual`): the named study —
  referrals, hearings, terminations, debarments per comparable public
  event, then against now — is specified and not run; state it as such.
- `[detail]` **The voicing filter is measurable** (`rem:release`): the
  legislature-wide study named and not run.
- The four **registered predictions** of `rem:open`, dated, as the
  paper's one pre-registration.

And the box gets the standard sentence.

---

## C. Nine bibliography entries are not citations

`rem:testimony` (l.1048–1050): "This one falls only if the counts,
filings, prices and procedural records are wrong, **and all of them are
checkable by anyone**." Nine entries make that false as stated:

| key | entry |
|---|---|
| `bonds2026` | "Reporting on long-dated United States Treasury auctions and yields, August 2026. *CNBC*, *Axios* and the Committee for a Responsible Federal Budget." |
| `mcconnell2026` | "Reporting on the retirement announcement and subsequent nomination votes… *NPR* and associated coverage." |
| `iran2026` | "Reporting on Iranian political reaction… *Iran International* and associated coverage." |
| `navy2026` | "Reporting on extended United States carrier deployments… *Military Times*, *CNN* and *Task & Purpose*, including congressional correspondence…" |
| `pool2026` | "Reporting on damage to the Lincoln Memorial Reflecting Pool and the subsequent prosecutions… *NPR*, *PBS NewsHour* and *Fox 5 Washington*." |
| `proof2026` | "Reporting on office-released imagery… *France 24*, *Mediaite* and associated coverage." |
| `unseen2026` | "Reporting on a senatorial absence… *Al Jazeera*, *The Hill*, *NBC News* and associated coverage." |
| `equity2026` | "Global and United States equity market capitalisation, 2026. Market-capitalisation compilations, 2026." (no source at all) |
| `deathtiming` | "RFE/RL … 2016; with standard accounts of the 1975 Spanish and 1953 Soviet successions." |

No titles, no dates beyond a month, no URLs, "and associated coverage".
A reader cannot check these, and the Reflecting Pool case in particular
rests on "the court filings" (l.656, 731) that are never cited. **Fix:**
each becomes one or more entries with author or outlet, exact title, date,
and URL (the set does not use DOIs but news needs URLs; add
`\usepackage{url}` or `\href`); the court filings get a docket citation;
`equity2026` gets a real source (SIFMA or World Federation of Exchanges)
or the sentence loses that clause; `deathtiming`'s "standard accounts"
become two named references (Preston on Franco; a standard Stalin
biography). Where an article cannot be located, the claim it supports is
softened or removed. This is the paper's own standard applied to its own
apparatus.

Related internal inconsistency: the reserve share is "about 57 per cent"
at l.71 and l.1107 and "about fifty-eight" at l.1267. Pick one and date it.

---

## D. Narrated drafting, the heaviest in the set

The set's rule ("a paper is what it says now") was applied across 00–05.
10 has at least seventeen sites where the text reports having been wrong
earlier in the same document, sometimes about text that is no longer
there:

| line | phrase |
|---|---|
| 205 | "which this paper names elsewhere **and failed to notice in its own citation**" |
| 211 | "recording that is **the cost of having said otherwise first**" |
| 488 | "**The declination just entered was misapplied**, and the correction is more useful than the hedge was" |
| 689–692 | "**Which retracts what was said here twice.** Calling this checkability encouraging … committed two paragraphs after naming it" — the retracted text is not in the paper |
| 885–887, 897–898 | "**written against a record that has since moved** … tested by events within a day of being written" |
| 1053 | "not from caution, **as it may have read**" |
| 1141 | "stating it that way **repeated an error this section had already corrected once**" |
| 1163–1165 | "**both were produced under pressure rather than declared in advance**" (kept as content in B, dropped as narration here) |
| 1253 | "for a reason **its author should have seen**" |
| 1257–1258 | "the objection **made this section's recurring error once more**" |
| 1282–1284 | "This section **had not cited** the reserve position **at all until the objection was sought deliberately**" |
| 1355 | "**The preceding remark asked the wrong question.**" |
| 1384 | "**The correction stands as the finding.**" |
| 1423 | "**reaching for them twice was the error**" |
| 1504–1507 | "Searching this case returned material from an earlier episode… **It was excluded.**" |
| abstract l.38–40 | "was separated from the adaptability companion because it had grown to dominate…" |
| 1618–1620 (`rem:weight`) | fine — this one is content |

Several of these carry a real result *inside* the narration (l.192–199
the GDP-denominator point; l.689–693 "checkability without consequence is
documentation"; l.1355–1386 capacity absent inside a fully staffed
institution). **Fix:** keep every such result stated positively; delete
the report of having said otherwise. The abstract keeps the reason for
separation (an application should be attackable on its own evidence) and
drops the history. `rem:latest` (l.885–911) is entirely a "since writing"
update; fold its one substantive point (a split conducted in the open is
suppression failing, in *that* frame, not nettable against another) into
`rem:prop` and delete the remark.

---

## E. Thirty pages of remarks and no numbered result

Eleven sections; every one contains only remarks. The paper's results are
remark titles. At minimum these are propositions the rest of the set
could cite:

- **Aimed artefacts bound; unaimed records estimate** (`rem:selected`,
  with the criterion from `rem:testimony`: prefer inputs produced for
  reasons other than your reading of them). This is a methodological
  result the whole set uses and should be citable by number.
- **Amplitude runs inversely to deliberation** (`rem:lapse`).
- **Institutional transitions are keyed on documents, not states**
  (`rem:document`), with **a certificate is the conversion relation**
  (`rem:certificate`) as its corollary.
- **Sustaining is a threshold, so a suppressed decline arrives
  discontinuously** (`rem:prop`).
- **A system that adapts on residual is blind to predicted decline**
  (`rem:surprise`).
- **Narrative copies; Narrativium does not** (`rem:propagate`).

Promote each to a `proposition` with the argument left in the remark
beneath it, as 01 did for its decoherence material. The falsifiers in B
then attach to numbered results.

Also: the `\emph{…}` lead-sentence device is used on nearly every
paragraph for thirty pages (several hundred occurrences). It was cut in
01c to the result sentences; do the same here — one italic sentence per
remark at most, the one that is the claim.

---

## F. Claims to verify or soften

1. **The frog** (`rem:frog`, l.822–827): "an intact frog in slowly heated
   water shows unease at about twenty-five degrees, grows steadily more
   agitated … struggles unavailingly to get out, and dies near forty-two
   in rigid tetanus." Goltz 1869 is cited. The standard summary of Goltz
   is that the *intact* frog attempted to escape at ~25 °C and the
   *brainless* frog did not; whether the intact frog died depends on the
   vessel, and the later "stayed and died" results (Heinzmann 1872,
   Fratscher 1875) used intact frogs heated very slowly. The remark's
   whole argument ("It notices. It escalates. It dies anyway") rests on
   which of these Goltz reported. Verify against the primary or Sedgwick
   1888, and state exactly what was observed; if the intact frog escaped
   in Goltz's own trials, the remark needs a different citation or a
   different claim.
2. **`rem:pool`** attributes an award to "the awarding principal" and
   quotes his "own earlier account" — the paper's rule is that
   self-accounts are events not evidence; here the changed account is
   used as an event (correct) but "by the awarding principal's own
   earlier account, worked on his private swimming pool" is used as a
   fact. Either cite a record (the filings) for the prior relationship or
   mark it as the earlier of two accounts, neither relied on.
3. **`rem:governance`** l.252–259 gives a conflict timeline (28 February,
   April ceasefire, June memorandum, July supplemental) on one CRS report
   dated 26 March and one CSIS note dated 13 July. The June and post-July
   events have no citation. Add or cut.
4. **`rem:actuarial`** l.1322–1323 "Critical roles were held through
   episodes of illness" and `rem:proof` l.1416 "a second member of the
   same body died suddenly" — both uncited. Add.
5. **`rem:how`** l.1588–1590: the Anthropocene's formal standing "was
   declined rather than granted" — correct (ICS, March 2024) but uncited.
   Add the IUGS/ICS statement.
6. l.1643 `zhou2026` (arXiv 2604.08224) and l.1636 "the companion's
   reconstruction result" are the paper's two thinnest supports by its
   own account; fine, but the "migration reported above" (l.1603) is
   reported in 09, not here — say so.

---

## G. Mechanical

- `\texorpdfstring` on the `\date` dashes; `thebibliography{9}` → `{99}`
  (33 entries); `et al.` → `et~al.`; bibliography unsorted (Treasury,
  CRS, BIS, SWIFT, Eichengreen, ECB…) — sort by label.
- Bibitem labels of the form "Treasury market reporting(2026)" and
  "Senate reporting(2026)" render as author-year citations in the text
  ("Treasury market reporting, 2026"), which is what a reader sees at
  l.976 and l.1295. C fixes this.
- The `mcconnell2026` key names the person the text does not; keys are
  invisible in the PDF, so this is only a repository-hygiene note.

---

## What is right and should not be touched

- `sec:scope`'s three disciplines and `rem:testimony`'s five admissible
  input kinds with the aimed/unaimed criterion — the strongest
  methodological statement in the set, and it is honoured.
- `rem:cog`: the justification for the frame expires at the rate the
  centrality erodes, "and a justification that did not expire would be
  suspicious".
- `rem:carry`, `rem:channel`, `rem:lapse` as a sequence: reachable
  quarter, two attempts on one manifold, amplitude inversely to
  deliberation — the manifold "says in advance which reaches".
- `rem:counterfactual`'s natural-experiment reading with the input
  pinned at maximum, and the finding that one mechanism converts
  efficiently into damage and inefficiently into repair.
- `rem:steelman` engaging the four objections and the base-rate argument
  (memory is residual-driven; a correct warning acted on erases its own
  evidence) — the reflexive application at l.1188–1191 is exactly right
  and is why B matters.
- `rem:bias`: "deniable by attacking the selection just admitted; what it
  is not is deniable by attacking the author."
- `rem:document` and `rem:certificate` entire.

---

## Suggested order

1. **A** — restore the 09 references (mechanical, largest readability
   gain, fixes thirteen ungrammatical sentences).
2. **B** — the falsifiability section the paper says it has.
3. **C** — citable citations; the 57/58 figure.
4. **D** — narrated drafting; delete `rem:latest`.
5. **E** — six propositions; the italics pass.
6. **F**, **G**.
