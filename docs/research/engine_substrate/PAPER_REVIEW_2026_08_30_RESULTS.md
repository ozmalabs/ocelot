# Review passes over the twelve formal papers — results

> **Two passes are recorded here.** §1–§7 describe the FIRST pass. **§8 records the
> second pass, which found two of the first pass's own repairs unsound and
> reversed them** — so where §1 and §8 disagree, §8 is current. The disagreement is
> left in place rather than edited away because it is the more useful record: it
> shows the standard running against the account rather than only for it.

**Date:** 2026-08-30 · **Draft set reviewed:** `draft-2026-08-30.4`
**Method:** five independent review lenses run in parallel over `papers/formal/`, plus a
mechanical pass. Every finding quoted below was re-verified against the source
before any edit; the two findings that did not survive re-verification are
recorded in §5 rather than dropped.

---

## 1. The headline: the ledger claim failed its own first audit

`rem:inherited` (written the same day) said paper 01 postulates **two** things
over paper 00 and that everything else is consequence. It invited a reader to
look for a hidden axiom, on the ground that finding one would be *"a real result
against the account's economy."*

**The audit found five postulates, not two (later an admission and no posits, §1.1) — and every one is demonstrated by 01
contradicting the remark in its own words elsewhere in the same file.** That is
the strongest available form of evidence for this kind of check, because it does
not depend on the reviewer's reading of any derivation.

| postulate | the paper's own words against the ledger |
|---|---|
| a valuation on writes | *"cost is not in the triple … a different cost model revises the economics throughout and leaves $(g,r,\Gamma)$, admissibility, residual and frames exactly as they were"* |
| a realisation operator | provenance section: collapse *"arrived by constraint"*, adopted from quantum measurement and generalised |
| no-copy | used for time's direction and the Landauer floor; appears 5×, defined 0× |
| the two gates (not a consequence) | *"optimisations … not constituents of graphhood"*, needing a selection pressure `sec:carvings` **declines to supply** |
| — plus a missing **third tier** | 4 hypotheses (incl. the Law of Graphic Equalisation, the title claim) + the cheap cut, *"an empirical posit and not a result of this account"* |

One correction ran the **other** way: `rem:one-substance` holds admissibility is
enforced by rules, so `Γ` is a configuration of `r` rather than a separate
postulate. It was first recorded and *not* taken — the ledger counted `Γ`
separately on the grounds that the economical reading is the one that flatters —
and then taken on the author's decision that **admissibility is a specific
instance of rules**.

A second fold followed from the same direction of argument: **a budget is forced
because something has to change, and if change is free there is no pressure.**
Under no-copy a change does not keep its predecessor, so retention costs a
further write, and a write spent on one thing is not spent on another — a budget
by *opportunity cost*, requiring no quota. So `prop:no-free-lunch` is no-copy
restated in the currency writes supply, and the valuation is not a separate
posit.

A third fold went furthest: **rules are forced because something has to do
something, a rule is the least something-that-does-something that can be, and it
is a graph because everything is.** So `r` follows from the admission that
anything happens rather than standing beside it — *a rule is a graph that does
something* — which is 00's own minimality method used one level along (00: least
structure that can *be* → relation; 01: least that can *do* → rule). It inherits
that method's limit too: least is established by removal against a candidate
list. The obvious candidate fails — a change occurring regardless of what is
present is a rule with an empty match condition, not a counterexample.

A fourth fold applied the account's own removal test to no-copy — *either it is
forced, or derived, or it is not pulling its weight* — and the answer **differs by
which use is tested**, which is why it is worth recording:

- **The economics use is derived.** For a predecessor to be present after a
  change, something must have put it there; putting structure anywhere is a rule
  firing. So retaining anything specific costs its own write, using only the
  admission and never a notion of cost — no circularity with the budget it
  grounds. This is also why the paper *prices* reversible operation rather than
  forbidding it: it was never a prohibition, it was the observation that keeping
  something is work.
- **The strong form does not survive, and was load-bearing.** *No change preserves
  its predecessor* is more than the derivation gives — an append-only rule
  preserves as a side effect. `ax:no-time` rested time's **direction** on exactly
  that, and now rests it on the **asymmetry of enablement**, which it had all
  along: if one change makes another possible, the second does not thereby make
  the first possible. Direction had been over-attributed.

A fifth fold took the last one. **A realisation operator is not required; it is a
specific type of rule.** The argument that had defended it — `Γ` generates the
*set*, `r` produces deltas, neither yields a single successor — **reifies `Poss`**,
and `Poss` is not that kind of thing: `def:admissible` fixes membership by an
*iff*, and the text after it says no construction algorithm is required. There is
no collection in the graph awaiting reduction. A rule fires and writes a delta;
the firing *is* the realisation. Single-valuedness then rests on rules being
determinate in their antecedents, which is `prop:determinism` and is closer to
what *rule* means here than to a wager.

**This partly answers §6's determinism finding (C1)** rather than leaving it open:
the *"variation observed only from a frame that omits determining dimensions"*
clause reads as an unfalsifiable escape, and on this reading it is **the content**
— an omitted dimension is exactly the case where the pattern missed what mattered.
That **relocates** the empirical risk rather than dissolving it, onto a claim the
paper already carries: the Law itself, which bets that realised dynamics admit a
rule-description at all. Closeable in the ordinary way, and where a doubter should
press.

**The ledger settles at one admission (things happen), NO further posits, and
Axiom −1** — against the five the audit found and the two originally claimed. The
third tier is untouched: the hypotheses remain bets. **This is more exposure, not
less** — an account resting on fewer things has fewer places where a failure could
be contained.

Of the two survivors, single-valued realisation is a bet **against a rival that
is not cheaper**, and the remark now prices it: retaining every continuation
needs a structure holding all branches as realised *and* a measure over them to
recover what is observed — and a measure over branches is a selection principle
written somewhere else, so the trade is a relocation, not a saving. The work
branches are usually wanted for is already done by `Poss(G_t)`, which this
account has: interference and superposition live in *possibility* without
promoting possibility to realised history. It stays a postulate because the
preference is methodological rather than forced. Its falsifier is sharpened
accordingly — a rival must predict what this account predicts **without adding a
measure**, or it has moved the selection rather than removed it.

Folding it removed an assertion rather than renaming one. `prop:two-gates` had to
claim the aperture and change grammars are *"two faces of one grammar on one
boundary edge"* — an identity asserted across a distinction the definitions drew,
since `Γ` was defined to govern *graph-originated* transformations while `Γ_a`
gates *inbound* container deformation. If admissibility is just rules, `Γ_a` and
`Γ_c` are rules with different scopes, which needs no unification claim. **One of the two objections to that proposition dissolves outright; the other is
halved.** The *budget* the gates optimise against is forced, so calling them
optimisations no longer smuggles in an uncounted posit — but their *accretion* is
not forced, and `sec:carvings` is right to decline a selection principle. A
budget supplies a differential, not an enforcement: a graph that gates cheaply
does more per write, and nothing compels any graph to be that kind.

Consequences that followed forcibly once the ledger was corrected:

- *Cost is the write* was `[detail]`; a declared postulate cannot be a mechanism
  the account could swap out. Now `[shape]`.
- **Two postulates had no falsifier anywhere in 01** — worse than a mis-tag,
  since an uncommitted postulate is not graded wrongly but *unexposed*. Added:
  *Realisation is single-valued* and *No-copy*.
- *"Two of the above are not closeable"* was stale; it is four.
- 00's abstract and `papers/README.md` both still advertised *"exactly one
  thing."* Both corrected, both recording that they said one until the audit.

---

## 2. Factual errors — sources that do not say what they were cited for

Found by the citation lens, which machine-checked 369/370 unique keys against
Crossref and independently verified 26 attributions against primary sources.

1. **IEEE 754** — cited for *"NaN propagates through every operation containing
   it — weak Kleene, in hardware."* It does not: `pow(x,±0)=1` for any `x`
   **including NaN**, `hypot(±Inf,NaN)=+Inf`, `minimumNumber` returns the number.
   **Correcting this improved the passage**: a mostly-infectious value with a
   schedule of deliberate exemptions is a better instance of the paper's own
   "handlers are installed policy" claim than a cleanly infectious one would be.
2. **Scott & Strachey 1971** — cited for ⊥ propagating *"through any compound
   containing it."* The monograph restricts function spaces to the **continuous
   and explicitly not the strict**; a lazy conditional has `f(⊥) ≠ ⊥`.
   Load-bearing: it was offered as an instance of `prop:compression-convergence`,
   which requires the *forcing* to be shared.
3. **Maynard Smith & Szathmáry 1995** — first two transitions in the wrong order,
   and **no cost-comparison criterion exists in that book**. The ladder is theirs;
   the *when* is Coase's alone.
4. **Hau et al. 1999** — *"slowed to walking pace"*; 17 m/s ≈ 61 km/h. Wrong by
   >10×, and it **understated** a result that needed no help.
5. **Shannon 1948** cited for the parsimony norm — contains no model selection and
   treats redundancy as *useful* on a noisy channel. The norm is Rissanen's.
6. **Nāgārjuna** — *"without an observer edge anywhere in it"* is an absolute the
   secondary literature does not license.
7. **Rovelli 1996** at 01a — RQM relativises to interacting physical **systems**,
   never to descriptive rule sets; *"already holds"* claimed absent agreement.
   Every other `rovelli1996` use in the corpus verified correct.
8. **Schrödinger** wrote *negative entropy*; *negentropy* is Brillouin's coinage.
9. **`wolfram2020` resolved to two different works** — the Wolfram Media book in
   01, the *Complex Systems* monograph in 01a. Causal invariance lives in the
   monograph.
10. **D. C. vs Bernard Williams** — 00 cited *Descartes: The Project of Pure
    Enquiry* for the **bundle tradition**. 06's use of the same key is correct
    (Bernard Williams did propose the absolute conception), so one key was serving
    two doctrines.

---

## 3. Arguments that did not go through

All four were introduced in the `.4` additions — the expected place for defects,
and the reason new text was reviewed as a separate lens.

- **`prop:is` read as verificationism.** Its second clause was given as
  *equivalent* to the first and phrased as a distinction *"not available to be
  drawn"* — availability implies somebody to whom something is available, and the
  base of this account has **no observers, no frames and no views at all**. Now
  contrapositive and structural. The paper states outright that it owes nothing to
  verificationism and could not use it: *a tree falling unobserved is exactly as
  related to its forest as one that is watched.*
- **The candidate list claimed to have removed the axiom the argument needs.**
  Removed: any rule about where a distinction may be made *from*. **Retained and
  load-bearing:** that a distinction *is* a relation. A reader who denies that
  should reject the paper at that sentence, not several pages downstream.
- **"The ideal information shape is a graph"** was argued from *"a description
  shorter than its subject's structure has lost something"* — a picture theory
  that **contradicts 00's own MDL accounting two sections earlier**. The shortest
  description of $K_{10^6}$ is a phrase naming the relation and the count, not
  $5\times10^{11}$ pairs. Repaired to a claim about the **vocabulary** the
  generator is written in, which is what was wanted and what survives.
- **The licensing argument overreached.** *Derivation-length is not
  commitment-length* is right about reasoning and wrong about **vocabulary**:
  aperture, change grammar, residual and frame are terms, and terms sit on the
  generator's side however well motivated. Both papers now state the comparative
  form and concede the fraction covered is unmeasured.
- **"Each removal is a test with a determinate outcome"** was contradicted eight
  paragraphs later by *"only survival."* The outcome is determinate in **one
  direction**: a successful removal exhibits an inspectable account; a failed one
  records only that nobody has yet seen how.

---

## 4. Cross-document and structural defects

- **07 had zero sections** — 7,759 words, three `\paragraph` heads, the third
  spanning 466 of 621 lines. Now eight labelled sections.
- **07 carried 13 self-references pointing at 01**, residue of the split. The
  worst was the closing line before the bibliography: *"the commitments below…"*
  — promising a list into empty space.
- **01b sourced three claims to the constructive companion**, which contains no
  results, no fixture and no numbers; 07 says so explicitly while insisting the
  engineering record is not in this corpus. Now named as the engineering record
  and marked as uncheckable assertions.
- **"Rock" meant two things.** 01 uses it for `g` with `r,Γ` **absent**; 01b for
  rules **present but not firing** — which 01 says is a distinct third condition
  while crediting "the companion on mind" with naming it. 01b now carries the
  distinction.
- **06 carried the superseded minimum** (*"what survives every removal is that
  rules run"*), which `rem:only-g` corrected and which 00 exists to deny.
- **36 build artefacts tracked in git**, no LaTeX ignore rules. Untracked.
- **Two boxed displays overflowed the margin** by 55pt and 80pt.
- **The statement generator could not see new commitments at all** —
  `parse_falsifiers` scanned only the *first* `enumerate` after the section
  header, reporting items in a second block as MISSING while they sat in the
  paper. Fixed; the statement went 15 → 19 falsifiers, and it had been omitting
  *Cost is the write* while carrying all three propositions it defends.

---

## 5. Method notes, including this pass's own error rate

**A reviewer's finding is not a finding until re-verified.** Two did not survive:

1. A lens reported that no paper includes any figure, on a grep for
   `\includegraphics`. **Wrong** — 02 includes two figures via
   `\input{../figures/…-body}`, and `papers/README.md`'s claim was accurate as
   written. *This was my error, not the lens's.*
2. An earlier audit had flagged 14 `\bibitem` entries as missing their
   author-year argument. **False positive** — they use natbib's *extended* form
   `[Short(Year)Full list]`, which `plainnat.bst` itself emits.

**Clean on mechanical checks:** 0 dangling citations across 526 instances
(cross-confirmed against LaTeX's own `Citation undefined` warnings), 0 dangling
or duplicate `\ref`/`\label` across twelve files, 0 compile errors, 0 unresolved
reference warnings.

---

## 6. Named, then fixed

*The first pass closed with fourteen findings named and not fixed. They were then
worked through. What each turned into:*

| finding | resolution |
|---|---|
| `Graph-law determinism` unfalsifiable | **Partly dissolved.** The "omits determining dimensions" clause is not an escape but the content — a rule is a pattern plus a change, so one pattern giving two changes means the pattern missed what mattered. Risk **relocates** onto the Law itself, which is closeable. |
| Four commitments, one observation | **Declared.** The four are kept as separate places to look, and the list now says failing any is the single prohibition failing — one result, not four. `A swallowed failure` re-marked `[shape]`, an inconsistency rather than a judgement. |
| 07 carries no commitments | **Three added**, including the one it named as worth testing — with the modelling choice that made it ambiguous **fixed in advance**, which is the whole repair. |
| 61 untagged grounding commitments | **All 59 tagged** (two were Scope items, not commitments) under a stated rule, and marked as the least-audited judgement in each document. |
| `01s` has no bibliography | **Generator emits one**, lifted verbatim from the long paper. 17 entries. |
| Rate: cross-frame vs in-frame | **Resolved, neither side conceding.** In-frame in *provenance*, cross-frame in *type* — a ratio of two integers is not an integer, and a frame's coordinates are the integer lattice. |
| 07's prohibitions include cost | **Removed from the list.** Since the ledger correction the retention cost is *derived*, so it is neither prohibition nor postulate but consequence. |
| 00's second falsifier rigged | **Unrigged.** The unsatisfiable *"and that does not reduce to them"* clause is gone; what is asked is that a field **keep** the primitive in the formalism it teaches and computes with. |
| 00's yield-rate uncommitted | **Committed** — and the commitment says the base rate is reconstructed rather than recorded, and that the paper owes the ledger before the claim should be granted. |
| Parallel postulate exemplar | **Removed**, and inverted: it is the canonical *independent, non-eliminable* axiom, so it is a picture of what the ledger would look like **if one of its entries were wrong**. |
| Duplicate commitments across papers | **Marked in place** as inherited or entailed — 01≡03 twice, determinism across four documents, Axiom −1 in two groundings while 01 carries none for it. |
| `claimed class` indexing | **Closed.** A class counts as claimed once it appears in a grounding section; nothing may be added or removed in response to a result. |
| 00 and 06 orphaned | **`rem:companions` added to 01.** 06 had been pointed at by nothing since its material was moved out of 01's conclusion. |
| No systematic no-copy sweep | **Run.** One site found: 01a's `rem:arrows` unified three arrows into no-copy. Two are one asymmetry; the **causal** arrow is enablement and agrees without being them. |

**Still open, and deliberately:** the self-congratulatory register in the newest
passages. It was flagged as concentrated in exactly the passages where support is
thinnest, and several of those have since been rewritten for other reasons — so it
cannot be closed by inspection and would need a fresh read to assess honestly.

## 7. Standing rules this pass earned

1. **A claim that invites an audit will get one, and the audit's result belongs in
   the paper.** `rem:inherited` failed on its first use, in the flattering
   direction, and saying so in place is worth more than the claim was.
2. **A value maintained by hand at several sites drifts.** 01's footer carried
   `r152` while its title block said `r155`. Now checked by
   `tools/check_draft_consistency.py` on every bump.
3. **A claim about a set that is never executed goes stale.** The README said
   *eight papers* when there were twelve, and named a draft string two bumps old.
4. **Verify the reviewer.** Two findings this pass did not survive re-checking,
   one of them mine. §5 exists so the pass's own error rate is on the record.

---

## 8. Second pass — what it overturned

Five fresh lenses, run after the first pass's repairs. It found the first pass had
been **too kind to the account in exactly the places the account was being
reduced**, which is the direction that matters.

### 8.1 Two of the five ledger folds were unsound and are withdrawn

| fold | verdict |
|---|---|
| `Γ` into `r` | **holds** |
| `r` into the admission | **holds**, with the candidate list now stated and the partly-analytic concession made |
| the valuation into no-copy | **CIRCULAR — withdrawn** |
| no-copy into `r` | withdrawn with the valuation |
| the realisation operator into rules | **MISQUOTED ITS SOURCE — withdrawn** |

**The valuation's fold derived the weak form of no-copy from the strong form the
same paragraph had just conceded was unavailable.** And `prop:economics` says
outright that *continuation is free and change is paid*, so a predecessor a change
does not touch persists at no cost — the derivation was refuted by the proposition
it was offered as grounding. Independently, *each write does one thing* is a
unit-of-account convention, not a scarcity premise; `prop:partial-order` and
`rem:gals` make unrelated collapses concurrent, so nothing is forgone.

**The realisation fold misquoted the line it was built on.** `def:admissible`'s
follow-on says no ***particular*** algorithm is required and names itself
***extensional*** — which keeps the family as an object independent of any
constructor, the opposite of what was concluded from it.

**Ledger as it now stands: the admission, a valuation, a realisation operator,
Axiom −1.**

### 8.2 The objection that outranks the count

Every fold has the form *X is a special case of Y*, and the licensing criterion —
*selecting is doing something, doing something is what a rule is* — applies to
**anything this account posits**. If admissibility turned out not to be a species
of rule, `Γ` returns to the list and **not one proposition, falsifier or prediction
changes**. So a count driven to zero is a theorem of the vocabulary, not a
measurement of the economy. `rem:inherited` now says this. What a surviving fold
*does* buy: two things cannot be varied independently, which constrains what a
grounding may do. It does not reduce the ways the account can be wrong.

### 8.3 The systemic defect, named

**Corrections applied at the site of the objection and not swept.** The papers
narrated a repair where the objection landed and left the repaired claim
load-bearing elsewhere. Measured instances: a no-copy sweep that was run, reported,
and missed two sites inside the same remark; a fold withdrawn in the ledger while
two falsifiers still cited it as made; `07` retracting an item from its prohibitions
140 lines after the enumeration that contained it; `00` §1 asserting what §2
corrects. **This is one defect, not five.**

### 8.4 Corrections that damaged the text

The first pass added **66 in-place self-corrections**, 20 in paper 01. A lens
classified all of them: **~13 load-bearing, ~12 belong in a footnote or here, ~43
bookkeeping.** Two structural rules came out of it and are now enforced: **no
revision history inside an axiom, definition, proposition, or falsifier entry**,
and **the generated statement carries none at all**. One sentence in `01b` had been
rendered **unparseable** by two nested corrections stacked before its main verb.

### 8.5 Also found and fixed

- **Seven flattering `[detail]`→`[shape]` mis-tags**, including three of the four
  quantum results `01a`'s abstract sells, `01b`'s death criterion (listed under its
  own *"the strong claims are structural"*), and `06`'s underdetermination, which is
  a third of that paper.
- `00`'s falsifiability section header said **"Two commitments"** over a list of three.
- `00`'s compression commitment was **refuted by its own worked example** — an arity
  and a count are neither relata nor relations. Narrowed to the *bearer of
  distinctions*.
- `07`'s **"in advance" was false of the document it appears in**: the numbers are on
  the preceding page, so the definition is prospective only.
- **Ten of `07`'s prose pointers** were aimed at the wrong sections after it gained
  eight of them; `07` uses `\ref` nowhere, so none of them failed loudly.
- My `rem:inherited` rewrite **deleted the Axiom −1 and third-tier paragraphs** and
  **duplicated the `Γ` fold**. Both restored/removed.
- All twelve now carry **zero margin overflows**, and the draft checker gained a
  fourth check for them — **verified by planting one**.

### 8.6 Still open

- **Free continuation: a write, or the absence of one?** `01a` says it *is* a write
  from which the predecessor is recoverable; `01` and `03` say it is the absence of
  an event. `01a` is internally split on it. Load-bearing for `prop:second-law`.
- **Is a rule-less structure a frame?** `01` says yes and calls the contrary *"wrong"*;
  `00` says *"nothing here is a frame"* and infers a load-bearing conclusion from it.
- **Can a rock measure?** `00`'s `prop:one-way` says it cannot observe; `01a`'s
  `cor:observer` says a rock measures. A grain qualifier probably resolves it and is
  stated at neither site.
- **"Capability"** means the gates in `01` and reach in `02` and `04`; `01`'s caution
  names only the Sen-following companion, so `02` is uncovered.
- **Narrativium as a stock**: `07`'s *"paid out of their Narrativium"* against `04`'s
  *"Narrativium is not a tank."*
- **The self-congratulatory register**, carried over from the first pass and now
  joined by a self-flagellating one — a *"X rather than quietly Y-ing"* formula
  appears six times across four papers.
