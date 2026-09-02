# Review of `05_frames_relation_and_the_empty_limit.tex` (draft-2026-09-02.1, r8) — proposal for fixes

Scope: the whole file (247 lines, 4 pp), its log, and 00 r121 / 01 r278 /
01a r42 for what it restates or depends on. Line numbers are r8. Nothing
applied.

Compile: 0 warnings, 0 overfull, all six citations resolve and are
accurately characterised (Nagel's contentful limit; Williams's absolute
conception with his reservations placed correctly; Ladyman–Ross as a
proponent of one horn; Esfeld's moderate position; Mac Lane §III.2 with
the naturality caveat). The Yoneda remark is the best short treatment of
that misuse in the set and is not questioned. The paper is four pages by
design and 01 says why ("the weakest instance of this argument rather than
a representative one"). The findings are that it restates *Is* and 01
without citing either, narrates its own origin twice, and has one
falsifier clause that is not a falsifier.

---

## A. `sec:relation` restates *Is* and never names it

l.112–116: "To exist, in this substrate, is to stand in a relation. What
survives every attempted removal is structure with relations among its
parts, and nothing more: rules running is what a world in which anything
*happens* costs, not the condition of there being anything at all."

That is *Is*'s Proposition 1 plus 01's `rem:only-g`, in 01's own words,
presented as this paper's premise. *Is* is not mentioned anywhere in 05 —
not in the box, the scope, or the text — although it is the paper that
argues the claim this section rests on, and the paper whose `sec:prior`
already carries `rem:relation-prior`'s three citations (Ladyman–Ross,
Esfeld, Nāgārjuna) with the same characterisations.

**Fix.** Open `sec:relation` with the dependency: "*Is* holds that to be
is to stand in relation and to cohere in it (`IS-prop:is`,
`IS-prop:cohere`), and Graphic Equalisation that rules running is what a
world in which anything happens costs (`GE-rem:only-g`). What is added
here is confined to the *priority* question, which neither settles."
Reduce `rem:relation-prior` to one sentence pointing at *Is*'s prior-art
section (`IS-sec:prior`) for the positions, keeping only what 05 adds:
that Madhyamaka is an ally for the negative half and not the positive.

Also say how 05's answer sits against 00's. 00 takes relational
determinacy as *a commitment, the one place to disagree* (00 `sec:claim`),
and says the *constructive* priority of relata is unavailable here because
there is no time for an order of construction to run in (00 `sec:prior`).
05 says the *metaphysical* priority is underdetermined and relation-first
is the better-formed assumption. These are compatible, but a reader of 05
alone cannot see that the base paper has already committed, on its own
argument (weak discernibility; the one-relatum and empty cases), to the
horn 05 calls "licensed". One sentence closes it.

---

## B. The empty limit is stated in three papers; 05 is the one 01 points at, and cites neither

`rem:empty-limit` (l.83–88): the only object with no particularity is the
empty set, which is not a frame. 00 `sec:one-not-enough`: "the empty set
is the only perfect thing and … to exist is to be imperfect"; and the
"two zeros" reading. 01 `rem:everything-nothing`: "the totality and the
empty set meet at zero bits, which is also where this programme's own
empty limit sits" — and 01 `rem:companions` names 05 as where "the limit
of that direction is empty" is carried. So 01 sends the reader here, and
here sends them nowhere. **Fix:** after the remark, one sentence: "This is
the empty end of *Is*'s two zeros (`IS-sec:one-not-enough`), reached from
the direction of well-formedness rather than of relation; Graphic
Equalisation's zero-bits reading (`GE-rem:everything-nothing`) is the same
point measured."

---

## C. Dependencies stated as if free-standing

1. l.62–67 "frames doing the same work grow more alike as each is better
   formed" — that is `GE-prop:convergence-observed`, which rests on the
   near-uniqueness posit `GE-hyp:cheap-cut`. 05's falsifier 1
   ("Convergence is purpose-relative") inherits that posit and should say
   so.
2. l.76–79 "No level is self-transparent … A frame's measurement of its
   own throughput returns its own unit" — two of the three clauses of 01's
   `prop:prohibition` (now numbered, 15.1). Cite it; the third obstacle
   (strip the purpose and there is no criterion) is this paper's own and
   should be marked as the addition.
3. l.92–95 "description length is machine-relative up to a constant" — 01
   `rem:mdl-ontic` accepts that objection as a thesis ("the constant is the
   frame"). Cite it rather than restate.
4. l.133–136 "the same form of answer the physics companion gives to the
   choice of a synchronisation convention — and the recurrence of that form
   across a physical and a metaphysical question is the most interesting
   thing in this paper." The physics companion's form is now numbered
   (01a r42 `rem:oneway-rule`, the better-formed-hence-assumed argument;
   `rem:reichenbach-malament`). Cite, and either give the recurrence a
   `[detail]` falsifier (fails if the two cases turn out to rest on
   different licences — one on cost, one on something else) or drop "the
   most interesting thing in this paper", which currently carries no
   exposure.
5. "What the account contributes is a mechanism for a gradient" (abstract,
   l.106–107): the mechanism is `GE-def:well-formed`'s cost of held
   structure. Cite at first use.

---

## D. Narrated origin, twice, plus one retraction

- Box l.36–38: "separated from it deliberately: the material here is more
  speculative than that paper's, and **was cut from its conclusion** rather
  than allowed to borrow that paper's standing."
- Scope l.56–58: "**The material was written as part of that paper's
  conclusion and moved here** because a conclusion is not where speculative
  metaphysics should acquire the standing of the work it concludes."
- `sec:chicken` l.171–172: "**The earlier claim that the question
  presupposes such a boundary was wrong.**"

The *reason* for separation (speculative material must not borrow
standing) is worth keeping once. The history is not. **Fix:** box and
scope each keep the reason and drop "was cut / was written as part of /
moved here"; the chicken sentence goes, leaving the positive claim
(invariance under precisification does not require a sharp boundary).

Deferred to 01: `rem:companions` says of 05 "It was moved out and, until
now, was pointed at by nothing, which made it unfindable" — the same
narration on 01's side. One clause to cut when 01 is next touched.

---

## E. Falsifiers

1. **"On the tags" (l.187–195)** is the pre-harmonisation text and calls
   this paper "this grounding" — it is not a grounding. Replace with 01's
   sentence verbatim (trailing clauses dropped), and drop "this grounding".
2. **Item 3's second clause is not a falsifier.** "Fails in the other
   direction if the argument of Remark~\ref{rem:underdetermined} can be
   shown not to presuppose its conclusion, in which case the stronger
   unknowability claim is recoverable." Recovering a *stronger* claim does
   not falsify the weaker one the paper makes; it supersedes it. Either
   drop the clause or move it to a sentence after the list ("What would
   strengthen rather than falsify item 3: …").
3. **Item 1** should name its inherited posit (C.1).
4. **Missing:** the recurrence claim (C.4) if kept as "the most interesting
   thing"; and `rem:yoneda`'s negative ("an object is its relations" is
   false as stated) carries none and needs none — say so in the after-list
   sentence, as 02 did for its consequences-not-wagers.

---

## F. Naming, cross-references, mechanical

1. "the theory paper" (3), "the substrate paper" (1), "Graphic
   Equalisation" (2), "the physics companion" (1); *Is* absent. Add the
   naming sentence (Graphic Equalisation; *Is*; the physics companion) with
   the "inherits its definitions…" clause.
2. `xr-hyper` with `\externaldocument[GE-]{01_…}`, `[IS-]{00_is}`,
   `[PH-]{01a_…}`; targets: `GE-def:frame` (l.54), `GE-def:well-formed`
   (l.55, 64), `GE-prop:prohibition` (l.55, 76), `GE-rem:only-g` (l.113),
   `GE-prop:convergence-observed` + `GE-hyp:cheap-cut` (l.65),
   `GE-rem:mdl-ontic` (l.93), `GE-rem:everything-nothing` (B),
   `IS-prop:is`, `IS-prop:cohere`, `IS-sec:one-not-enough`, `IS-sec:prior`,
   `PH-rem:oneway-rule`, `PH-rem:reichenbach-malament`. All present in the
   current aux files.
3. Preamble carries 01's unused macros (`\Poss`, `\Coll`, `\Hist`) and five
   unused theorem environments; only `remark` is used. Strip.
   `\texorpdfstring` on the `\date` dashes.
4. Section reference style: `\S\ref{sec:direction}` (l.115, 179) against
   the set's `Section~\ref`.

---

## What is right and should not be touched

- `sec:direction`'s core: objectivity is a direction, the limit of
  well-formedness is a shared somewhere (the optimum for the work), and
  stripping the purpose removes the criterion along with it.
- `rem:underdetermined`: the argument for unknowability presupposes one
  horn, so what survives is underdetermination by *this* substrate — a
  self-correction that is exactly the right size.
- `rem:nowhere-prior`: Nagel as target rather than predecessor; Williams's
  reservations located correctly.
- `rem:yoneda` entire.
- The disambiguation of *egg* as where the chicken puzzle's force lives.

---

## Suggested order

1. **A** and **B** — the dependencies on *Is* stated; two sentences and
   one remark shortened.
2. **F.1–F.2** — names and `xr-hyper` (makes C's citations possible).
3. **C** — five citations, one decision on the "most interesting thing".
4. **D**, **E**, **F.3–F.4**.
