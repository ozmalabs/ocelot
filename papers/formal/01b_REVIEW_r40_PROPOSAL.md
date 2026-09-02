# Review of `01b_graphic_equalisation_mind_and_self_grounding.tex` (draft-2026-09-02.1, r40) — proposal for fixes

Third pass. Scope: the whole file (1937 lines, 31 pp), its log and aux,
the r39 review and what r40 did with it, and the companions it cites (01
r280, 01a r43, 03 r30, 04 r21). Line numbers are r40. Nothing applied.

Compile: 0 warnings, 0 overfull, 77 bibitems all cited, no `??`, all
`GE-`/`PH-`/`NM-`/`NV-` refs resolve, by-name check clean,
`\texorpdfstring` on the date. r40 did everything r39 asked: `xr-hyper`
to 01a, 03 and 04 with fourteen sites resolved and the paper named; the
ten narration sites rewritten; the preamble reduced to the definition
sentence; three falsifiers added (other-model, boredom, calibrated
supply); item 17's parenthetical resolved by number; `posix2017` filed
under I; `et~al.`; the compression lead-in reduced to one clause. The
substance holds on a third reading. **What remains: six propositions that
argue at length rather than state; the tags sentence off 01's verbatim by
one word; the list unnumbered where the set numbers; the scope note in
the old form; three references by description with targets; one
reference to "horizon material" that exists nowhere in the set; and
three results without a falsifier.**

Eight of 01b's labels are cited by other papers via `MS-`
(`prop:minimal-universe` ×5, `sec:minimal` ×3, `prop:selfmodel` ×2,
`sec:falsifiability`, `rem:realisation`, `rem:death-decoherence`,
`prop:one-influence`, `prop:manipulation-structural`). All must survive
under the same names and kinds.

---

## A. Six propositions argue; the set's rule is that propositions state

Each proposition below keeps its label and its statement; the argument
moves into a titled remark directly after it (or into the prose that
already follows). No content is deleted.

| proposition | lines | what stays as the statement | what moves |
|---|---|---|---|
| `prop:run-record` | 187–198 | "A block is only ever of the past. What has been run can be recorded; what has not been run cannot, because there is nothing yet to record: the future is determinable by the rules but uncomputed. The openness is unrun-ness, not indeterminism." | the two `GE-` attributions and "you must run it" → prose after |
| `prop:imagination-real` | 292–313 | "Every frame that runs is real graph data really running; there is no non-actual frame. The only difference between an imagined frame and a perceived one is frame-relative grounding: what the frame is anchored to, relative to another frame." | the dragon/plan/character examples, "is it real? is malformed", why imagination does work, and the death sentence → `remark[What follows for fiction, planning and death]` |
| `prop:grounding` | 351–373 | "Grounding is frame-relative all the way down; there is no self-grounding frame beneath the rest. One grounding is privileged relationally and not absolutely: observation is a frame's contact with its supergraph, the boundary where the container deforms it with changes it does not author." | the chair/dragon, reality-testing as pushback, sanity as a grounding-tag problem, hallucination, "anti-foundationalist without being coherentist" → `remark[Reality-testing is supergraph-pushback]` (item 6 of the list already carries the pushback claim) |
| `prop:selfmodel` | 398–412 | "Every self-model is incomplete, and no frame escapes this by effort. A limit of expression leaves residual and is inferable from trace; a limit of aperture leaves nothing and is reached by metacognition. The operative distinction is therefore calibrated against uncalibrated, not complete against incomplete." | the two `GE-` definitions and the "weaker evidence" clause → the paragraph after (l.414 already continues the argument) |
| `prop:other-model` | 909–922 | "A frame's model of another frame is a generator, inferred from that frame's output and runnable forward on inputs its subject never addressed." | "This is not a new posit but a composition of three things…" and the conditional-generator step → `remark[The composition, and the one step that is this paper's]` |
| `prop:death` | 990–1003 | "Death is the rules within a self ceasing to be re-runnable in the same coherent self. A pause is a stop whose rules remain re-runnable as that self; death is the stop that does not resume." | the identity-criterion sentence (which is `prop:identity`'s) and the rock/record close → prose after |
| `prop:identity` | 1023–1046 | "The self is its internal coherence (Graphic Equalisation's SELF identity, Definition~\ref{GE-def:self-identity}); an instance of it running at a position in the container is a supergraph node (its SUPERGRAPH identity, Definition~\ref{GE-def:supergraph-identity}). The internal self persists exactly as long as a re-runnable full coherence-snapshot exists somewhere; the death of a node is one instance stopping, and the death of the self is that re-runnability being gone everywhere." | gradual replacement, backup, fission, teleporter, partial record → `remark[The standard cases on one axis]` |

`prop:minimal-universe`, `prop:free-will`, `prop:one-influence`,
`prop:manipulation-structural` already state; leave them.

---

## B. The tags sentence, the list form, the scope note

1. l.1432: "something **the account** is claimed to require or to
   permit" — 01's sentence (and every other paper's copy) reads "the
   substrate". One word; restore it.
2. l.1434–1537: the list is `itemize`; every other paper's is
   `enumerate`, and the note after it (l.1539) has to say "The last entry
   and the grounding-has-no-bedrock entry" because the items have no
   numbers. → `enumerate`, and the note reads "Items 6 and 20 are
   falsified by the same object…"
3. l.1544–1548 scope note: "… none is offered. **This sits outside the
   list because nothing about the world could settle it.**" The set's
   form (08 r2, 09 r92, 10 r5, 01b's own item in the r39 review) is the
   claim without the trailing sentence. Drop it.

---

## C. References by description, and one with no referent

| line | claim | target (verified in the current aux files) |
|---|---|---|
| 91–92 | "a *promoted* constraint exposed to falsification, in the manner of Graphic Equalisation's collapse bridge" | `GE-rem:qm-provenance` (01 l.2705 calls it "the conditional collapse bridge (Remark~\ref{rem:qm-provenance})") — verify the remark is the bridge and not only its provenance; if not, `GE-sec:collapse-law` |
| 582–583 | "it persists for exactly the reason the horseshoe crab's form does — nothing is forcing a write. The working picture is the overshooting case" | `NV-rem:two-cases` for the crab; `NV-prop:overshoot` is already cited at l.755, cite it here too |
| 876 | "the $+1$ direction of the level stack, run on a person rather than a container" | `NM-rem:level-stack` (the momentum paper's "inferred, carried, read") |
| 731–732 | "This account does not derive planning horizon from a window of tolerance, and what follows stands on **that horizon material** rather than on anything established here." | **No paper in the set contains "window of tolerance"** (grep over all `.tex`); the only occurrence is this sentence. The remark is leaning on material that does not exist in the corpus. |

**Fix for the last row.** State it as this remark's own conjecture: "This
account does not derive planning horizon from a window of tolerance; the
step from window width to horizon length is conjectured here and not
established anywhere in the set. Taken at that strength…" Item 10 of the
list (*Stress makes a frame manipulable structurally*) already carries
the exposure; its text should say the window→horizon step is the
untested half.

---

## D. Three results without a falsifier

1. `rem:transparency` (l.441–487): "transparency is contingent on how a
   graph is built, which is why it varies, and why it is the kind of
   thing that can be built differently." Add `[detail]` **Transparency
   varies with formation.** Fails if a frame high on the axes named
   (meta-model, residual parsing, boundary representation) is
   nevertheless transparent to itself — if transparency is a property of
   self-models as such rather than of a configuration.
2. `rem:cognition-compression` (l.540–562): the two named constraints
   (conduction delay, scarce bandwidth) land cognition on the same
   arrangements as distributed engineering over the region they touch.
   Add `[detail]` **Cognition converges with distributed engineering only
   where the two constraints bind.** Fails if arrangements shared by
   brains and distributed systems are found outside the region those two
   constraints touch, or if arrangements inside it diverge with no third
   constraint to account for the divergence.
3. `rem:death-decoherence` (l.1223–1227): "A self cannot install a
   handler for its own termination … the residual of a death is
   necessarily disposed of by the container." Add `[shape]` **No frame
   handles its own stop.** Fails if a frame's own rules are shown to
   dispose of the residual of that frame's termination — a handler
   running in a frame that has stopped.

Items 1–20 keep their positions; the new items go at the end.

---

## E. Smaller

1. l.446–448 "(The account has since been developed in terms of
   self-modelling epistemic spaces…)" — about Metzinger's literature,
   not this draft; "was later developed" reads the same without the
   drafting tense.
2. l.1280 `\texttt{fork}` — the operating-system call, in the computing
   grounding, cited to POSIX; not an implementation identifier of this
   project. Fine.
3. `rem:comm-engine` l.709–712 "Scope. The seeds carrying the
   near-identical decision rules are research demonstrations,
   default-disabled and not loaded by the running agent" — "seed" is the
   record's generic term and names nothing; fine under the evidence
   standard of l.94–101.

---

## What is right and should not be touched

- `sec:minimal` and the one-directional inference; "the rock's inertness
  is not a defect in the example but the whole of its content".
- `rem:three-frames`, `rem:reader` with its two qualifications.
- `rem:detection` (proxy dissociation) and the perspectival-realism
  paragraph.
- `rem:transparency` (as an agreement with a residual disagreement) and
  `rem:realisation`.
- `sec:communication` entire, including `rem:comm-calibrated`'s negative
  result and `rem:comm-prior`'s Austin correction.
- `sec:other-models`: Genette given the generativity in full;
  Porter–Machery used correctly; Schwitzgebel's tell.
- `rem:parfit`, `rem:hofstadter` ("threshold per coherence, gradient
  across coherences"), `rem:death-computing`'s "an implementation is free
  to add rules to suit".
- `sec:prior-art`'s "tiny and different in kind".

---

## Suggested order

1. **A** — seven propositions reduced, seven remarks/paragraphs created.
2. **B** — three mechanical.
3. **C**, **D**, **E**.
