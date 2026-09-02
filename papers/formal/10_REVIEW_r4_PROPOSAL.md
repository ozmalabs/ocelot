# Review of `10_applied_graphic_equalisation.tex` (draft-2026-09-02.1, r4) — proposal for fixes

Second pass. Scope: the whole file (2091 lines, 34 pp), its log and aux,
the r3 review and what r4 did with it, 09 r91 for every `AD-` target, 01
r278 and 04 r20 for the `GE-`/`NV-` targets. Line numbers are r4. Nothing
applied. As before, the 2026 empirical inputs are outside what can be
verified here; what is checked is citability, internal consistency
between the text and its own citations, and arithmetic.

Compile: 0 warnings, 0 overfull, 49 bibitems, all cited, all external
refs resolve, `{99}`, sorted. r4 did what r3 asked: the 09 references are
numbered and grammatical, the falsifiability section exists with eight
items, the nine uncitable entries became forty-nine citable ones with
URLs, the narrated drafting is gone, five results are numbered, the frog
is right, the Anthropocene vote is cited. **What this pass finds: one
remark whose causal ordering is contradicted by the dates in its own
bibliography; a discipline the text states and the bibliography breaks;
one mis-attributed cross-reference; four uncited figures; numbered
propositions that restate their remarks verbatim and carry no
falsifiers; and a dependency on a 09 remark that is being rewritten.**

---

## A. `rem:release`: the votes precede the announcement it says caused them

l.1344–1349: "A long-serving legislator announced he would not seek
re-election and had earlier stepped down from his leadership position;
**since then** he has been among the very few of his party to vote
against administration nominees … *What changed was the price of
dissent* … and it is what occurred."

The paper's own citations date the events the other way round.
`nominees2025` is dated **14 February 2025** and its title is "McConnell
voted against 3 Trump cabinet picks"; `retire2025` is dated **20 February
2025**. The three nominee votes (24 January, 12 and 13 February) all
precede the retirement announcement. So the within-person control, as
written, has the effect before the cause.

What the dates do support: the leadership step-down (announced February
2024, effective January 2025) is the price fall that precedes the votes;
the retirement announcement follows them and cannot be their cause. **Fix:**
rewrite the remark on the leadership exit as the price change, drop
"since then", and say explicitly that the later retirement announcement
is not used because it post-dates the behaviour — which is exactly the
announcement-date-versus-behaviour check the remark's own study design
(l.1359–1361) and falsifier 7 prescribe. Applied to this instance, that
check *fails one of the two candidate causes*, and reporting that is
worth more than the original claim.

`rem:actuarial` l.1390–1394 ("the events that lower the price of speaking
— a retirement announced …") and falsifier 7 inherit the fix.

---

## B. "It names no private individuals" — the bibliography names everyone

`sec:scope` l.70–72: "It names no private individuals. Where a case
involves people the mechanism is described and the participants are not,
because a document that named them would be a different kind of document
carrying different obligations." r3's fix (citable citations) made the
bibliography name every participant the text withholds: the legislator
(six entries by name in titles, two in URLs), the deceased member (title),
the awarding principal (URL), the prosecuting official (title), the
president (two titles). The text says "the awarding principal", "a
long-serving legislator", "a member"; the reference list, forty lines
later, says who.

This is not fixable by anonymising citations — a citation that cannot be
found is the r3 defect. **Fix:** state the discipline as what it actually
is. The participants are public office-holders acting in office, not
private individuals; the *argument* is conducted over mechanism and not
over persons, so the text names none; the sources cited name whom they
name, and citing them is not naming. Three sentences at l.70–72, and the
"different kind of document" rationale becomes a rationale for the
argument's form rather than a claim about the document's contents. Also
`rem:delegate` l.601–602 repeats the claim ("It also names no one") and
should point at `sec:scope` instead of restating it.

---

## C. One mis-attributed cross-reference

`rem:announce` l.553–554: "Graphic Equalisation already prices that
operation: revocation occurs at $\Delta g = 0$
(Corollary~\ref{GE-cor:frame-dimension})". That corollary in 01 r278 is
"Frame and dimension are one edge type in two roles" and says nothing
about $\Delta g$. The $\Delta g = 0$ result is *Narrativium*'s
**Proposition `NV-prop:conferral`** (Conferral and revocation), which is
also what 09 `rem:nowhere` cites for it. `rem:pool` l.706 uses the same
figure without a reference. **Fix:** both sites → "*Narrativium*'s
Proposition~\ref{NV-prop:conferral}"; keep the 01 corollary only if the
sentence wants the frame-is-a-dimension reading, which it does not.

Also "Axiom $-1$" at l.221, 1697, 1722 is unattributed — "Graphic
Equalisation's Axiom~\ref{GE-ax:no-view}" at first use.

---

## D. Four figures without a citation, against the paper's own rule

`rem:testimony` l.1100–1101: "This one falls only if the counts, filings,
prices and procedural records are wrong, and all of them are checkable by
anyone." Four are not:

1. l.471–474: FDA "lost 3,859 staff in 2025 and several hundred more into
   2026"; FCC "records continued reduction through retirements, the
   deferred-resignation route, and ordinary attrition". No citation. These
   carry the "attrition requires nothing at all" rung of the ordering.
2. l.963–966 (`rem:wait`): the refusal to resume talks, and the two
   attributed rationales including "January 2029" — `hormuz2026` is cited
   for the memorandum's expiry, not for the refusal or the rationales. The
   datum the remark says it rests on ("talks available are not being held")
   is uncited.
3. l.1331–1332: "Gold overtaking Treasuries in official reserves,
   valuation-driven though it was" — uncited, and the claim needs its
   comparator stated (gold at market value against foreign official
   holdings of Treasuries, on whose figures, at what date).
4. l.654–656: "the longest continuous run for a modern carrier of its
   class; a second carrier the same year drew comparable concerns" — the
   two navy entries cover the conditions and the letter; verify they cover
   the record claim and the second carrier, or drop those clauses.

Cite each or remove the claim. Also `korte2026` is the one news entry
without a URL.

---

## E. Numbered propositions restate their remarks, and carry no falsifiers

r3 asked for numbered results. r4 added five propositions and one
corollary — but by copying the remark's text above it:

| proposition | remark | overlap |
|---|---|---|
| `prop:narrative-copies` l.609–616 | `rem:propagate` l.622–631 | near-verbatim, same title |
| `prop:documents-not-states` l.1573–1580 | `rem:document` l.1586–1606 | near-verbatim, **identical title** |
| `cor:certificate-conversion` l.1615–1623 | `rem:certificate` l.1633–1638 | near-verbatim |
| `prop:amplitude-deliberation` l.455–461 | `rem:lapse` l.476–480 | verbatim sentence, same title |
| `prop:aimed-unaimed` l.1505–1512 | `rem:selected` l.1525–1539 | near-verbatim |

**Fix:** the proposition states, the remark argues. Cut the restated
sentences from each remark (keep the argument and the instance), give
each remark a title that differs from its proposition's, and let the
remark open "Proposition~\ref{…} follows from …". Saves about a page.

Falsifiers: three numbered results have none.

- `prop:blind-to-predicted` — `[shape]`: fails if a residual-driven system
  is shown acting on a foreseen, on-schedule decline without an asserted
  novelty as trigger.
- `prop:documents-not-states` — `[detail]`: fails on an institution whose
  transition is triggered by a state of the world with no record —
  automatic vacancy on a fixed number of certified absences, say — which
  would make the document-keying a design choice rather than constitutive.
- `prop:aimed-unaimed` — `[shape]`: fails if, in a matched sample, aimed
  artefacts are shown to estimate a distribution's centre as well as
  unaimed records do.

Items 3 and 4 both attach to `rem:steelman`; with the propositions
cleaned up, item 1 should attach to the proposition (it does) and item 5
likewise (it does) — fine.

---

## F. Internal consistency

1. **Weeks.** l.1477 "some eleven weeks", l.1516 "an eleven-week absence",
   l.1629 "determinate for eleven weeks"; l.1544–1545 "last reported
   independent sighting is of 11 June … passed eighty days by the
   beginning of September". 11 June → 2 September is 83 days, twelve
   weeks. Use one figure, dated ("over eighty days as of 2 September").
2. **GDP denominators.** `rem:carry` quotes deficit \$1.9T = 5.8% of output
   (⇒ output ≈ \$32.8T) and outlays \$7.4T = 23.3% (⇒ ≈ \$31.8T), and net
   interest \$1.0T = 3.2% (⇒ ≈ \$31.3T). Three implied denominators from
   one CBO report; the figures are probably fiscal-year vs calendar-year
   or rounded, but a paper whose point in `rem:observables` is that
   denominators conceal things should not quote three inconsistent ones
   from one source. State each as CBO gives it, or give one.
3. **Interest line.** l.350 "net interest is \$1.0 trillion … rises to
   \$2.1 trillion by fiscal 2036" and l.402 "more than doubles across the
   period" — consistent; l.395 "interest grows 9.8" is a one-year rate
   from `crfb2026`; fine.
4. **"Caught three times already above"** (l.1183): the cross-frame-sum
   error is caught at `rem:carry` l.370, `rem:pool` l.726–729, and
   `rem:prop` l.949–954 — three; correct.
5. `rem:load` l.654: a ship that "sailed in November 2025" and is "into a
   ninth month" in mid-August is consistent; "two hundred days at sea
   without a port call" is a different quantity from the deployment length
   and the sentence should not let a reader merge them.

---

## G. Dependency on 09, and one thing to re-check after 09 r92

09 r91 `rem:exchange` is being rewritten (09 review §B): it currently
refers to "the interceptor stocks", "the seven-year contract" and "the
buffers named above", none of which exist in 09 — they are this paper's
`rem:governance`. After the rewrite, the eight `AD-rem:exchange` citations
here (l.336, 371, 665, 728, 769, 926, 978, 1635) must be re-read against
the new text; the ones that lean on the *general* claim (money converts at
a rate; no rate into individual capacity; stipulated vs principled) will
survive, and any that lean on the interceptor instance should cite this
paper's own `rem:governance` instead. Likewise `AD-rem:chollet` ×7 for
the underdetermination result (correct target; r3 had guessed
`rem:method`).

The reverse dependency is clean: 09 cites nothing in 10.

---

## H. Mechanical and style

- 176 `\emph{…}` lead sentences remain over 34 pages (r3 asked for one per
  remark). Not blocking, but the device has stopped marking anything.
- `sec:falsifiability` l.1742: "The distinction is the one
  Section~\ref{sec:scope} rests its epistemic claim on" — `sec:scope`
  makes no epistemic claim about `[shape]`/`[detail]`; that sentence was
  written for 01's scope section. Drop it; the definition sentence stands
  alone in every other paper.
- `rem:steelman` is 200 lines; `rem:carry` 72. The steelman contains four
  objections and four replies plus the memory/voicing argument; a
  `\paragraph{}` per objection would let a reader find the reply to the
  one they hold.
- Bibliography: the `equity2026` URL path (`2025/07/…2026-Edition.pdf`)
  should be checked; `cborecon` needs a report number or date; the
  institutional entries without URLs (CBO ×2, CRS ×2, ECB, IIF, OECD,
  PPS, SWIFT, V-Dem) are findable by title and are fine.

---

## What is right and should not be touched

- `sec:scope` and `rem:testimony` (with B applied), `rem:bias`, and
  `rem:weight`'s "remove both … every conclusion above is unchanged".
- `rem:built`: "the depletion is not wear, it is demonstration" and the
  asset/instrument identity.
- `rem:observables`: the household-vs-aggregate disagreement as the
  signature; the coupling of the three observables honestly reducing
  their count.
- `rem:lapse` → `rem:announce` → `rem:delegate` → `rem:propagate` as a
  sequence, and "publication needs nothing and precedes all of them".
- `rem:pool` and `rem:counterfactual`: the bypass costing zero so nothing
  hardens; the natural experiment with the input pinned at maximum.
- `rem:frog` as corrected: the confinement as the third term the popular
  version discards, and the prescriptive error following from the
  descriptive one.
- `rem:steelman`'s memory-is-residual-driven argument and the voicing
  filter's three marks; `rem:release`'s corollary (dissent affordable
  exactly as it becomes ineffective) — survives A, since the leadership
  exit lowers both price and influence the same way.
- `rem:document` / `rem:certificate`: filings not states; the certificate
  as the $\kappa$.
- The falsifiability section's closing: no date registered, and why.

---

## Suggested order

1. **A** — the dates (a factual error in a result the paper leans on).
2. **B** — the naming discipline stated truthfully.
3. **C**, **D** — attribution and the four uncited figures.
4. **E** — propositions vs remarks; three falsifiers.
5. **F**, **G** (after 09 r92 lands), **H**.
