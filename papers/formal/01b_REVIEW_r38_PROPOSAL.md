# Review of `01b_graphic_equalisation_mind_and_self_grounding.tex` (draft-2026-09-02.1, r38) — proposal for fixes

Scope: the whole file (1789 lines, 29 pp), its log, 01 r275 for the results
it attributes, and the repo for the implementation evidence it calls
"unpublished". Line numbers are r38. Nothing applied.

Compile: 0 warnings, 0 overfull, all cites/refs resolve. Citations
spot-checked (Dijkstra–Fleming, Fleming 2024, Schwitzgebel, Porter–Machery,
Yildirim, Nijhof–Willems, Watanabe, Hassabis, Cerullo, Genette, Rabinowitz,
Walton, Nichols–Stich, Gendler, Massimi, Metzinger 2020, Bench–Lench,
Eastwood) and hold. Findings are structure, attribution, and evidence
standing.

---

## A. Two remarks refer to material that is not in this paper

`rem:cognition-compression` (l.392) and `rem:public-aperture` (l.415) sit
inside `sec:freewill` and belong to neither it nor this paper:

- l.416 "The **evolutionary claims above** read very differently depending
  on who is reading them" — there are no evolutionary claims above. The
  material is 01's `rem:evolution-compression` ("Evolution under the same
  treatment", 01 l.2451).
- l.423 "the argument **the previous remark takes a side in**" — the previous
  remark is about brain energy budgets, not evolution.
- l.449 "the evolutionary material is addressed to the working aperture" —
  again, none here.
- The title "Cognition under the same treatment" is the sibling of 01's
  "Evolution under the same treatment"; the pair was evidently drafted
  together and split across papers without re-anchoring.

**Fix.** Either (a) move both remarks back to 01 after
`rem:evolution-compression` — they are compression/convergence results, not
mind results — or (b) keep `rem:cognition-compression` here as the
cognition instance of 01's convergence proposition, with a `GE-` reference
to it, and move `rem:public-aperture` to 01 (it is about evolution's popular
reception and predicts something about *fields*, not about minds). (b) is
smaller. Either way, neither belongs in the free-will section.

---

## B. `rem:reader` is a 178-line essay on a different subject

l.213–390. It opens as the reply to an objection about the reader's two
frames (l.213–238, and that part is good), then becomes an essay on the
implied author, generative author-models, Genette's matrix of imitation,
pigeon stylometry, the Schwitzgebel experiment, caricature, and mentalizing
trade-offs. None of that is about free will. It *is* the substrate for
`prop:identity`'s record-gradient argument 600 lines later (l.964–1000:
"a model of someone's voice or style … carries enough to produce novel
output").

**Fix.** Split:
- `rem:reader` keeps l.213–238 (Currie, Rabinowitz, Nichols–Stich, Gendler,
  Walton, Wolf) and l.374–389 (the two qualifications).
- New `\section{Models of others: the implied author and generative
  fidelity}` placed before `sec:death`, holding l.240–372, with a
  `proposition[A model of another is a generator inferred from output]`
  stating the composition claim (l.295–312) and the honest status
  (components supported, composition this paper's, forward direction
  untested — l.314–345). `prop:identity` then references it instead of
  restating the gradient.
- Narrated drafting to remove while moving: l.267–269 "the check did not
  confirm the claim but reduced it twice, the second time on reading the
  source rather than a summary of it"; l.326–328 "A sweep of the indexes
  returns…"; l.341–345 "attributing to a consensus a position he argued
  against in print would have been citing him against himself".

---

## C. Attribution slips against 01

1. **l.169 "The open frontier of Axiom −1"** and **l.1348 "coherent under
   Axiom −1"** (falsifier 2). Axiom −1 is no-view-from-nowhere. The open
   frontier / no intrinsic last is 01's `prop:no-start-end`; the future being
   determinable-not-determined is `prop:determinable`. Fix both.
2. **l.90, 98, 404, 656, 660, 677, 1335 "the substrate paper"; l.1122,
   1138, 1174, 1177, 1181 "the theory paper"; l.1106, 1202 "the substrate
   account"** — while the draft box declares "Graphic Equalisation". Same
   drift 01a had. One name, and `xr-hyper` (`\externaldocument[GE-]{01_…}`)
   so the by-description references become numbers: `prop:no-start-end`,
   `prop:determinable`, `rem:types-forced` (l.656), `rem:self-edge`
   (l.660), `def:well-formed` (l.677), `prop:decoherence-one` (l.1122),
   `rem:vacated` (l.1138), `rem:supply-not-containment` (l.1177),
   `prop:self-governance` (l.1163), `prop:runner-recursion` (l.103, 404),
   `rem:space-test` (l.98), `def:self-identity`/`def:supergraph-identity`
   (l.944–946).
3. **l.98–99** "Where the substrate paper credits this companion with naming
   that condition directly, this is the naming." Correct today (01
   `rem:space-test` says so) — keep, but as a `GE-` ref so it stays true.
4. **l.1209–1215 and 01 l.1254.** 01 r275 `rem:cost-to-zero` says of the
   horizon-shortening under stress: "That paper [mind] gives its own
   account of the shortening … the two have not been reconciled." 01b's
   `rem:comm-horizon` gives that account (window → horizon → manipulability)
   with no reciprocal pointer. Add one sentence: 01's is capacity-consumed →
   aperture narrows; this one is window → horizon; both predict the same
   direction; reconciliation open.

---

## D. Evidence standing: "the engineering record … unpublished"

Three places report implementation findings and disclaim them:

- `rem:comm-engine` l.760–792: byte-identical conceal-harm / wait-for-reward
  rules; the beneficiary audit; the commit gate; the Gricean maxims.
- `rem:comm-horizon` l.816–819: "measured separately in the engineering
  record, which is not published alongside these papers and so cannot be
  checked by a reader".
- `rem:comm-calibrated` l.880–882: "roughly tenfold in a fixture of the
  engineering record — again unpublished here, so the figure is an assertion".

01 r275 now has a standard for exactly this (sec:scope: "a measurement
reported from the programme's own record … pre-registered implementation
record … not circulated … a claim a reader may decline to credit"), and
`rem:empirical-instance` as the worked example: protocol, result, bound, no
implementation identifiers.

**Fix.**
1. Adopt 01's standard sentence once, in `sec:scope`, and drop the three
   ad-hoc disclaimers.
2. `rem:comm-engine`: the beneficiary-audit finding has a results document in
   the repo (`docs/research/engine_substrate/DEFORMATION_BENEFICIARY_RESULTS.md`);
   the conceal/wait rule identity comes from the bigville abusive-relationship
   and delay-of-gratification lines. Restate as measurements (what was
   compared, what was found, the scope limit at l.789–791 kept) and remove
   the narrated drafting: l.761–762 "the check corrected this section twice",
   l.775 "That was wrong within the day", l.780–781 "this section's
   propositions were reorganised to match it rather than the reverse".
3. `rem:comm-calibrated` l.880–882: the "roughly tenfold" fixture could not be
   located in `docs/research` by search. Either find it and report it as a
   measurement, or drop the number and keep the mechanism ("the separation
   is large on that measure").
4. `rem:comm-horizon` l.810–819: keep as a prediction; state it under the
   scope-level standard rather than re-disclaiming inline.

---

## E. Falsifiability: one section has no entry, ten of ten are `[shape]`, one is counted twice

1. **`sec:communication` has no falsifier.** Two propositions, five remarks,
   zero entries. Add:
   - `[shape]` **No dedicated primitive for influence.** Fails if a substrate
     that supports persuasion, teaching and warning requires an operation
     conditioned on an act's being deceptive (`prop:one-influence`).
   - `[detail]` **Manipulation is presented/produced divergence.** Fails on a
     manipulative act with no divergence between claimed and produced
     beneficiary, or an honest act with one (`prop:manipulation-structural`).
   - `[detail]` **Stress makes a frame manipulable structurally.** Fails if
     horizon length is unaffected by window width, or if service becomes
     measurable at shorter horizons under stress (`rem:comm-horizon`).
2. **Predictions stated in the body and absent from the list.**
   - `rem:realisation` l.685–690: a frame after a realisation can identify
     prior unread occasions; one that received new evidence cannot.
     `[detail]`.
   - `rem:detection` l.505–506: misclassification exactly where strength
     matches and grounding differs. Already measured; `[detail]`.
   - `rem:public-aperture` l.436–442 if it stays: the lay/expert gap tracks
     daily residual exposure, not education. `[detail]`.
3. **Re-marks.** All ten are `[shape]`; the note calls them "the least-audited
   judgement". Under the definition given:
   - Item 8 "Self-models are incomplete but calibratable" is two claims:
     incompleteness (`[shape]`) and the calibratability/inside-beats-outside
     mechanism (`[detail]`). Split.
   - Item 3 "The future is unrun, not unfixed" — the irreducibility
     shortcut clause is `[detail]` (a rule could be reducible; the account
     survives).
4. **Item 10 says itself it overlaps item 6** ("one exposure stated twice").
   01 handled the same case by keeping separate entries and saying failing
   them is one result; do the same in one sentence, not a parenthetical
   inside the item.
5. **The "On the tags" paragraph (l.1332–1340) is verbatim 01a's**, including
   "The substrate paper has carried these marks for some time and the
   groundings did not" — narrated drafting. The 01a fix (in progress)
   harmonises the definition sentence across 00/01/01a; apply the same
   sentence here and cut the history.
6. **Scope note l.1399–1400** "counting it as a commitment inflated the list
   by one" — narrated drafting. Cut.

---

## F. Structure: propositions carrying their arguments

1. `prop:free-will` (l.175–194): 20 lines, argument inside. Statement = first
   three sentences; the story demonstration and the randomness/responsibility
   points follow outside.
2. `prop:selfmodel` (l.564–589): contains the Kruger–Dunning discussion and
   its hedge. Statement = l.565 + the expression/aperture split; the
   metacognition and Kruger material is prose after.
3. `prop:identity` (l.942–1006): ~65 lines. Statement = the two identities +
   the four cases (l.943–961). Then `remark[Records carry the generator to
   varying degrees]` (l.961–976), `remark[Behavioural fidelity is not
   structural capture]` (l.978–1000, with Chalmers), and the closing two
   sentences back in the proposition.
4. `prop:death` (l.912–940): statement = l.913–924; "What ends is only the
   self's own run…" is a remark.
5. **Two incompleteness reasons, six lines apart.** l.545–548 "not merely a
   consequence of the aperture being finite … but of the model being a proper
   part"; l.551 "It is incomplete, because it is built under a finite
   aperture". Plus l.660–664 gives a third (self-edge: informative ⇔
   lesser). State all three once, as three sources, and make l.551 agree.
6. **Bibliography is unsorted** (attwell, sterling, posix, adler,
   aldersonday, austin, porter, hassabis, sandberg, chalmers, …). Manual
   `thebibliography` does not sort; sort alphabetically by label. Also
   `wang2025persona` labelled "2025a" with no "2025b".

---

## G. Prose

- l.705–709 "this paper **commits** the opposite inference elsewhere" —
  reads as confessing an error; it means the paper *makes* the valid
  inference elsewhere. "makes".
- l.143–150: the metric-signature reading (− lived, + held) is a physics
  claim stated here and differently in 01a (succession/position). One
  should reference the other; 01a is the physics paper, so point there.
- l.152–156: computational irreducibility is used before Wolfram is cited
  (l.1223). Cite at first use.
- l.600: one 140-word paragraph as a single sentence-chain; split at "So the
  familiar case".
- l.1104–1109: "One thing should not be read as a concession extracted under
  pressure, because it was settled before the dispute arose" — argues
  against a reading nobody has yet made. Keep the axiom point, drop the
  defensive frame.
- l.1148 title "The computing grounding, which was built without any of this
  in view" — fine, but l.1149 "Everything the preceding two remarks asserts"
  → "assert".

---

## What is right and should not be touched

- `sec:minimal`'s choice of the *rules-present-not-firing* reading, stated
  against 01's stronger sense and matching 01 r275's `rem:rock` withdrawal
  exactly.
- `rem:parfit` and `rem:hofstadter`: threshold-per-coherence, gradient-
  across-coherences is the right resolution and is argued from Axiom −1
  rather than asserted.
- `rem:death-decoherence` and `rem:death-computing`: the handler/tombstone/
  supply-vs-containment mapping is exact and correctly marked as convergence,
  not necessity; the reachability ≠ re-runnability caution is the kind of
  thing that prevents a later misreading.
- `rem:comm-prior`'s Austin correction (illocutionary/perlocutionary as a
  structural distinction among acts of influence) is the honest move and
  should stay prominent.

---

## Suggested order

1. **A** and **B** — relocate the three misplaced remarks; this changes the
   section map, so do it first.
2. **C** — attributions and `xr-hyper`.
3. **D** — adopt 01's evidence standard, restate the implementation findings
   as measurements, locate or drop the tenfold figure.
4. **E** — falsifiers (add three for influence, promote three predictions,
   split item 8, fold item 10, harmonise the tags paragraph).
5. **F**, **G**.
