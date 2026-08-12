# Comparing physical shapes, concepts and formulas — a cross-domain design spike

**Status: SPIKE. No code, no seeds, no tests, no builds in this document.** Exactly
one file was added to the tree (this one); nothing else was touched. Matching the
status convention of `RULES_AS_SHAPE_DESIGN_SPIKE.md` and
`SHAPE_TYPE_VOCABULARY_SPIKE.md`: a first-person research journal, written before
any build, whose job is to make a design decision *legible and falsifiable* rather
than to make it.

**Charter, verbatim, from the project's creator:**

> "thinking about shapes, we need to be able to compare physical shapes, concepts,
> and formulas. the schema for this is in things like synesthesia."

Two mid-flight sharpenings from the creator, also verbatim, both of which changed
the document rather than being appended to it:

> "it is amazing that we can infer the schema of the brain from this - actually has
> anyone else done this specific work?"

> "also it wont just be in the brain, it will be visible in basically any large
> system allowed to iterate sufficiently to be close to optimal."

> "i suspect there is not one answer - but a shape."

The first added §6 (an AI/engineering prior-art search, distinct from the
neuroscience search). The second added §9 (the generalisation: this is a
convergent-optimisation phenomenon, not a brain fact) and §10 (the three-way
convergence, named). **The third rewrote §7.2**, which I had first drafted as a
binary-with-a-discriminator and which was wrong in exactly the way the sd loop's own
rung 2 exists to prevent — two things are not either identical or unrelated, they can
be related *by a parametrised transform*, and the parameter is the finding. §7.2 is
the corrected version and it is the document's actual deliverable.

**Base:** `main` at `ceecbc8` (`Merge cmp-value-surface-fix: computed strings no
longer silently collapse or lie`), verified with `git log --oneline -1 main` before
reading anything, and `git worktree list` checked (one unrelated detached baseline
worktree at `d239b7c`, untouched).

**Confidence convention**, following both prior spikes: claims I verified by reading
source in this tree carry `file:line`. Claims taken from another document in this
tree carry that document's section number and are attributed rather than restated as
mine. Literature claims carry the source I actually fetched and read; where I read
only an abstract or a fetched summary rather than the full paper I say so. Anything
I did not independently re-verify is marked `[unverified]`. **I ran no probe, booted
no agent and executed no code**; every count below is either read from source or
cited from a landed results document in this tree.

---

## 0. My one-line answer, up front

**The substrate already has *two* cross-domain bridges built, not zero — and they
are, structurally, exactly the two mechanisms the synesthesia literature spent
twenty-five years arguing between.** Neither is a mistake; the literature's own
resolution is that both are real and they answer different questions.

**But they are not two architectures to choose between. They are two points on one
family, and the family — not either endpoint — is the deliverable** (§7.2). The
parameter is *how much real structure the two domains share*; the ordering is MDL;
and the resulting ladder is, rung for rung, **the sd loop's own Occam ladder one
level up** — with co-presentation binding turning out to be the cross-domain
`sd_mint_quantum`: what you do when nothing held explains the relation.

Plus one genuinely missing piece the worked example in §7.3 exposes: **the substrate
can represent a physical rotation and it can represent a rotation formula, and it
currently has no object that says they are the same thing** — even though its own
frame/continuum invariant already says exactly what the relationship between them is.

The cost of the missing piece is small, its smallest testable slice is a
measurement I can specify precisely (§7.4), and — the finding I would flag second —
**a large shared-encoding migration is contraindicated by a measurement already in
this tree** (`CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`: merging pools *inside a
single domain* changed 261 of 502 verdicts; NO-GO on 15 of 15 candidates). Do not
read "one format" as "one pool."

---

## 1. Method — what I read, in what order, and why the order mattered

1. `CLAUDE.md` in full (1,139 lines), with attention to `SHAPE IS ACQUISITION, RULE
   IS EXECUTION` (`:993-1138`), the dynamic-quantization section (`:301-496`), and
   `BASE-AS-DIMENSION + the frame/continuum invariant` (`:497-564`).
2. `RULES_AS_SHAPE_DESIGN_SPIKE.md` (1,817 lines, incl. §15-16 addenda) and
   `SHAPE_TYPE_VOCABULARY_SPIKE.md` — for register, and because §4.2 of the second
   is the single most load-bearing prior finding for this document.
3. The cross-modal precedent the brief named: `scripts/jabberwock_cross_modal.py`
   and `seeds/cross_modal.json` (§2.1 — including a correction to the brief).
4. `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md`, `RULE_SIGNATURE_TO_RUST_RESULTS.md`,
   `CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md` — the three landed results that
   describe what a concept, a formula and a codebook pool *actually* are today.
5. The Rust: `term.rs`'s shape-math family and its three container arms;
   `strokes.rs`; `space_quantize.rs`; `shape_decode.rs`'s generator loader and
   codebook registry.
6. Only then the literature (§5-6).

The order mattered because **§2.3 is not in the brief and is not, as far as I can
find, named in any document in this tree as a cross-domain mechanism.** I found it
by grepping `seeds/` for `CodebookRegistry` while checking something else, and it
substantially changes the answer: the tree has already built and shipped a
cross-domain transfer path that goes from a *spatial* mechanism to a *symbolic* one.
Had I read the literature first I would have proposed building it.

---

## 2. Part 1 — the precedent that already exists

### 2.1 The cross-modal binding mechanism, read in full — and one correction to the brief

**Correction first.** The brief describes `research/experiments/gamma-substrate/
scripts/jabberwock_cross_modal.py` as living in "the creator's own private companion
repo." It does — and it has *also* already been ported into this tree. I fetched
both and diffed them:

```
diff seeds/cross_modal.json      <(gh api … research/experiments/gamma-substrate/seeds/cross_modal.json)   → SEED IDENTICAL
diff scripts/jabberwock_cross_modal.py <(gh api … scripts/jabberwock_cross_modal.py)                       → SCRIPT IDENTICAL
```

Both are byte-identical. So the precedent is not remote prior art to be imported —
it is **live in this repository**, and any design below can reference it as an
existing, loadable seed rather than as something to re-derive. Confidence: **high**
(I ran the diffs).

**The mechanism, precisely.** Two recognisers, one spine:

```python
GRAPH_PRED = _Pred(_Argmax(_NodesWhere("Concept", "is_grapheme", _Lit(1.0)), "w",
                           _Neg(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"),
                                              _Attr(_V("w"), "axs_synth_feat")))))
AUDIO_PRED = _Pred(_Argmax(_NodesWhere("Concept", "is_audio", _Lit(1.0)), "w",
                           _Neg(_dtw(_Attr(_V("s"), "axs_heard_feat"),
                                     _Attr(_V("w"), "axs_synth_feat")))))
```
— `scripts/jabberwock_cross_modal.py:54-57`. The module docstring states the design
in one line (`:3-4`): *"Both modalities use the shared AbS spine (argmax over
-Distance): a grapheme is a written Omniglot symbol matched by `PointSetDist`; a
phoneme is a spoken FSDD digit matched by `DtwTo` (real handwriting + real speech,
the same recognition shape, different distance)."*

**The critical architectural fact: nothing is translated.** Ink is never rendered as
audio; audio is never rendered as ink. Each modality is recognised **in its own
native metric** — a point-set distance for a 2-D pen trajectory, a dynamic-time-warp
for a spectral frame sequence — and what crosses the modality boundary is only the
**identity of the winner**, stamped as a `recognised_as` edge (`:127-132`).

The binding is three rules, and they are short enough to quote whole
(`seeds/cross_modal.json:10-33`):

```json
{"name": "bind_grapheme_phoneme",
 "match": [["gm","recognised_as","G"], ["pm","recognised_as","T"],
           ["T","of_phoneme","P"],     ["gm","co_modal","pm"]],
 "where": {"type":"Eq","a":{"type":"Count","source":{"type":"Neighbours",
            "node":{"type":"Var","name":"G"},"edge_type":"sounds_like"}},
           "b":{"type":"Lit","value":0}},
 "effects": [["add_edge","G","sounds_like","P"], ["add_edge","P","written_as","G"]]}
```

plus `read_aloud` (`:18-25`, a recognised grapheme mark gains a `speaks` edge to the
phoneme) and `listen_write` (`:26-33`, the mirror). The host's entire contribution
is `s.add_edge_unchecked(gm, "co_modal", am)` — one edge asserting *these two marks
occurred together* (`:140`, commented `# cross-modal ostension`).

**So the pattern is:** recognise natively, per domain, with whatever comparator that
domain actually needs → emit an identity → assert co-occurrence → let a rule bind
the two identities to one shared concept → recall in either direction through it.
The seed's own description names the generalisation payoff: *"recall generalises
across writers and speakers via the shared concept."* Generalisation is a property
of the **shared node**, not of either recogniser.

Confidence: **high** — read both files in full, diffed both against the private
originals.

### 2.2 What else is in the private repo, briefly

I listed the private repo's full tree (49,490 paths) and grepped for
`cross_?modal|synesth|synaesth|multimodal|multi_modal|amodal`. Five hits:

| path | what it is |
|---|---|
| `scripts/jabberwock_cross_modal.py` | §2.1, already ported |
| `scripts/jabberwock_multimodal_keyspace.py` | **not** cross-domain — "multimodal" here means a *multi-peaked distribution* of speakers; it clusters voices and navigates from the nearest cluster's local prior. Read the docstring; unrelated to this charter beyond the name. |
| `scripts/multimodal_referential_video.py` | **directly relevant.** Word-learning from real video: audio-word tokens and visual-object features are bound by **synchrony** (`bind_synchronous`'s ±tol co-occurrence), then comprehension recovers the visual referent from the audio word by a held Rust `Dot`-`Argmax`. Its docstring calls this *"exactly how a child learns 'ball' by hearing it WHILE an adult holds up a ball (ostensive naming)."* This is **the same co-presentation pattern as §2.1 with time as the co-presentation signal instead of an explicit host-stamped edge.** |
| `seeds/acquired/import_w00/american_synesthesia_association_microtheory.json` | an *acquired* microtheory — the agent read a Wikipedia article about the ASA and taught itself. Contains the correct textbook definition of synesthesia (*"stimulation in one sensory modality leads to experiences in a second, unstimulated modality"*) attached to some genuinely comic word-sense errors (`vilayanur_s` sense-resolved as "1/60 of a minute"). Evidence the agent has *heard of* synesthesia; not evidence it has a theory of it. |
| `seeds/acquired/import_w00/amodal_perception_microtheory.json` | same provenance: *"Amodal perception is the perception of the whole of a physical structure when only parts of it affect the sensory receptors."* Also acquired, also not connected to anything. |

The two acquired microtheories are worth one sentence of design significance:
**the agent holds the vocabulary for this charter and has never used it.** That is
the same shape as `RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.1's finding (the shape-math
algebra was built and never connected to the rule layer), one level up.

Confidence: **high** on the enumeration (I ran the grep over the full tree listing);
**medium** that nothing else relevant exists in that repo — the grep covers path
names, not file contents, and I did not use code search.

### 2.3 The second precedent — the one the brief did not name, and it is in THIS tree

`seeds/mechanism_index.json` declares a codebook of **held cross-domain mechanisms
indexed by meta-shape**, and `TransferDecode` (`runners/dsl/src/term.rs:1281-1310`)
is the Rust Term that consumes it. Two `Mechanism` nodes ship today:

```json
{"name":"spatial_foveation", "meta_shape":"selective_gating", "domain":"space",
 "slots":[{"role":"FIELD","cue":"scan","cue_kind":"verb","source":"space"},
          {"role":"FOCUS","cue":"to","cue_kind":"prep","source":"focus"},
          {"role":"UNIT","cue":"by","cue_kind":"prep","source":"quanta"}],
 "steps":[["quantize","FIELD","into","UNIT"],
          ["decode","only","FIELD","in","FOCUS"],
          ["index","FIELD","by","UNIT"]]}

{"name":"homeostatic_regulation", "meta_shape":"feedback_control",
 "domain":"thermoregulation", …
 "steps":[["measure","MEASURED"],["compare","MEASURED","to","SETPOINT"],
          ["correct","ACTUATOR","toward","SETPOINT"]]}
```

The seed's own description states the operation and its purpose exactly:

> *"`retrieve_and_transfer_mechanism` reads this index on a recognized shape and
> re-instantiates the mechanism's steps with the GOAL's fillers (space→rules,
> quanta→event-type, focus→focus) — real analogical transfer, not a lookup: the
> output plan is the goal domain's, structurally isomorphic to the source. The slot
> binding is DERIVED from the goal's own predicate/argument structure via the cues;
> the mechanism holds the ABSTRACT procedure, never the target fillers."*

`TransferDecode`'s own doc comment confirms the mechanics: *"RETRIEVE the
mechanism(s) indexed under the recognised shape, DERIVE each abstract slot's target
filler from the GOAL's own predicate/argument structure via the slot's cue,
RE-INSTANTIATE the mechanism's steps with those fillers"* (`term.rs:1299-1303`), the
codebook node-type being discovered from a graph-resident `CodebookRegistry`
declaration rather than passed as a Term argument
(`term.rs:1293-1297`, `shape_decode.rs:5281-5296`), and the meta-shape verdict
coming from `RecogniseShape` (`term.rs:1312-1329`) which the agent's own
`categorise_by_shape` also uses.

**Read the named example again: `space → rules`.** That is a *physical/spatial*
mechanism (foveated quantized flood over a map) being transferred into a *symbolic*
one (foveated scanning of the agent's own rule set). **This is the charter's
question, already answered once, already shipped, for one specific pairing.** It is
the "shared abstract code" architecture: neither domain is translated into the
other; both are independently classified into a domain-neutral vocabulary
(the eleven `MetaShape`s), and the *procedure* crosses.

Two honest limits on how much this establishes:

* The recogniser feeding it is a keyword scorer. `RecogniseShape` scores a shape by
  *"how many of its `has_principle` neighbours … carry a `keywords` entry that is a
  SUBSTRING of `text`"* (`term.rs:1319-1322`).
  `META_SHAPE_FIRST_CLASS_RESULTS.md` measured that this scorer decided **44 of 55
  meta-shape pairs by alphabetical tiebreak** before it was fixed, and
  `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §4.2 measured 42.5% of all vocabulary
  readings in a full boot as substring accidents. The *architecture* is right; the
  *entry point* has been the single most-repaired thing in the tree this month.
* Both shipped mechanisms are **procedures** (`steps`), not **structures**. Nothing
  in this path compares a physical *shape* to a formula's *shape*; it compares
  recognised shape-*labels* and transfers a step list. That is a real and important
  restriction, and §7.3 is where it bites.

Confidence: **high** on what exists (read the seed and both doc comments);
**medium** on "this has never been named as a cross-domain mechanism in the
docs" — I grepped `docs/` for `TransferDecode` and `mechanism_index` and found it
discussed as an analogical-transfer path, not as an answer to this charter, but I
did not read all 100+ docs.

### 2.4 So: the substrate has two bridges, and they are different bridges

| | §2.1 co-presentation binding | §2.3 shared abstract code |
|---|---|---|
| what crosses | an **identity** (which grapheme, which phoneme) | a **procedure** (the mechanism's steps) |
| what makes it work | the two things **co-occurred** | the two things **classify the same** |
| domain-specific part | the comparator (`PointSetDist` vs `DtwTo`) | the filler-derivation cues |
| domain-neutral part | the `Argmax(-Distance)` spine and the shared `Concept` node | the meta-shape vocabulary and the slot/step template |
| generalises via | the shared node | the shared label |
| needs the domains to share structure? | **no** — arbitrary pairings bind fine | **yes** — the transfer is vacuous otherwise |
| built where | `seeds/cross_modal.json` (3 rules) | `term.rs::TransferDecode` + `seeds/mechanism_index.json` |

**That table is the actual content of this document's Part 3**, and I want it on the
page before the literature, because §5.5 turns out to name the same two columns
independently, from neuroscience, with a criterion for when each applies.

---

## 3. Part 1 continued — what the three named domains actually look like today

The charter names three things to compare. I checked what each one *is*, as graph
data, right now.

### 3.1 Physical / spatial — and there are already TWO encodings here, not one

**Ink** (`runners/dsl/src/strokes.rs`). A pen path is quantized into a
`ShapeSignature`-compatible **relation-system**: `["seg", i, turn_q, len_q]` per
arc-length-resampled segment, plus four arity-2 pose relations
(`strokes.rs:7-10`, pushes at `:374` and `:411-414`, assembled into the `signature`
attr at `:425`). The `seg` rows are rotation/translation/scale-invariant *by
construction*; pose is factored out into separate single-slot relations
specifically so that "rotated" is a rung-1 per-dimension quantum delta the unchanged
`TransformDecode` reads for free (`strokes.rs:8-12`, and its own test
`invariant_only_omits_pose_relations` at `:977` asserts 2 segments → 2 relations
invariant-only, 6 relations with pose).

**Space** (`runners/dsl/src/space_quantize.rs`). A `SpaceQuantum` is **not** a
relation-system. It is `lo`/`hi` integer box bounds per dimension, `ndim`, `kind`,
`body_key`, `epoch`, plus `portal` **edges** carrying `dim`/`dir`/`span_lo`/
`span_hi`/`cost` (`space_quantize.rs:31-45`). The structure lives in the **edges**,
not in a signature attr.

**This is the first thing worth stating plainly: "physical shape" is not one
encoding in this substrate.** A stroke is a flat list of predicate-headed tuples; a
navigable region is a box-and-portal graph. Neither is wrong — each is what its own
operator needs — but any proposal of the form "encode physical shapes as X" has to
answer which of these two it means, and my read is that it cannot mean both.

### 3.2 Concepts — a fixed-arity, arity-2 relation vector over a sparse population

`domains/analogical_thinking.py:388-411`:

```python
def _concept_shape_vector(substrate, concept_node) -> list:
    """A concept as a fixed-arity relation vector over the held vocabulary.

    `[[axis:name, slots-or-absent], ..., ["category", cat-or-absent]]`, sorted
    and identical in length and position for every concept in the graph. Each
    relation is EXACTLY TWO elements for the reason `domains/meta_shape.py`
    documents: `anti_unify_values` generalises element-wise over equal-length
    tuples, so a 2-element relation keeps the PREDICATE fixed and wilds only
    the value.
    """
```

Note what that docstring is: **an encoding choice derived from an operator
constraint, written down at the site.** The arity-2 rule exists because
`anti_unify_values` requires equal-length tuples (§4.1), and the fixed-arity
alignment with an `_ABSENT` filler exists because two concepts must occupy the same
positions to be compared at all.

The population it runs over is the sobering part.
`ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1, measured on a full
`load_all_seeds` boot:

| | |
|---|---|
| `Concept` nodes | **10,775** |
| …with ≥1 outgoing edge of any type | **114 (1.06%)** |
| `Concept -*-> Concept` edges, whole graph | **190** |

and its verdict, which I am quoting rather than paraphrasing because it constrains
every proposal below: *"98.9% of the population has no edge to consult. Building
relational alignment here would be a no-op wearing the costume of a fix."*

**So a "concept," in this substrate today, is essentially a bag of vocabulary
readings, not a relational structure.** Any design that assumes concepts arrive with
relational structure to align is designing for a population that does not exist.

### 3.3 Formulas — three encodings, and the best-developed one is Program IR

The charter's "formula" has at least three live candidates:

1. **Program IR** — `Prog*` Terms executed by `ProgEval`. `term.rs:2019-2075`
   states the contract, quoted in `RULE_SIGNATURE_TO_RUST_RESULTS.md` §1:
   *"a program is a Term subgraph the agent can match, decode, render and repair,
   and `ProgEval` is the one pure Dict-in → Dict-out window onto its semantics."*
   That rung installed a real algorithm as 857 Term nodes in the graph, read it back
   out, executed it on `ProgEval`, and got byte-identity on 2,930 cases with the
   Python original — and it **survives a checkpoint** (§4.2 of that document). This
   is the substrate's answer to "a formula the graph holds."
2. **`chunk_rels`** — a program idiom flattened to a relation-system
   (`["ckstmt", i, label]` head rows plus `["ck", i, path, atom]`,
   `domains/prog_chunk_growth.py:137,157`). Positional index `i`; this is the
   encoding whose equal-length coupling `RULES_AS_SHAPE_DESIGN_SPIKE.md` §2.3
   diagnosed.
3. **The rule `where`-signature** — a `FrozenSet` of path-addressed rows,
   `("rt", path, variant)` / `("ra", path, field, atom)`
   (`domains/rule_signature.py`, computed since `RULE_SIGNATURE_TO_RUST_RESULTS.md`
   by the graph-resident program).

### 3.4 The convergence, and the divergence — both real

**They converge on a format.** A stroke's `["seg", i, turn_q, len_q]`, a concept's
`["axis:name", value]`, a chunk's `["ckstmt", i, label]`, a rule row's
`("rt", path, variant)` — all four are **predicate-headed tuples in a flat
collection**. That is not a coincidence and it is not a plan; four grains built
months apart landed on the same wire shape because it is what the shape math eats.
`SHAPE_TYPE_VOCABULARY_SPIKE.md` §4.1 measured the same convergence at the *field*
level (`{name, signature, support, provenance}` recurring at five grains) and called
it *"the strongest evidence in this document that a shared vocabulary is the right
call."*

**They do not converge on a container, and §4.2 of that same spike argues they
cannot.** Its table, which I am not going to re-derive because it is right:

| grain | container it correctly chose | why |
|---|---|---|
| `ShapeSignature` (sd loop) | list of relations | needs residual + open arity |
| `MetaShape` | `List` | needs WILD slots + residual |
| concept vector | fixed-arity `Tuple` + `_ABSENT` | needs WILD + residual + **paths** (for the parallelogram) |
| rule `where` | `FrozenSet` of rows | needs coverage + open arity, **and therefore cannot carry a WILD** |
| rule body, for transfer | raw nested `Dict`/`Tuple` | needs per-path witnesses |

with the verdict: *"A shared vocabulary is warranted at the level of fields, roles
and identity discipline. A shared **encoding** is not, and forcing one would break
either the mint path or the transfer path at every grain."*

I read that spike specifically looking for a reason to overturn it at cross-domain
scale, and did not find one. §4 explains why the constraint is mechanical.

---

## 4. Is the shape math domain-neutral? — verified against `term.rs`

The brief asks whether `AntiUnify`/`Covers`/`Substitute` have anything
domain-specific baked in. I read the implementations rather than the doc comments.

### 4.1 The algebra is domain-neutral. Confirmed.

`anti_unify_values` (`term.rs:3356-3418`) dispatches on **`Value` constructor
only**:

* empty → WILD (`:3357-3359`);
* all-equal → that value (`:3361-3363`);
* all `Dict` → recurse over the **intersected** keys (`:3365-3385`);
* all `Tuple`/`List` **of equal length** → element-wise (`:3387-3401`);
* all `Set`/`FrozenSet` → the **intersection** (`:3403-3416`);
* otherwise → WILD (`:3417`).

`covers_value` (`term.rs:3757-3785`) mirrors it: `Dict` → keys present and
recursively covered; `Tuple`/`List` → **`pt.len() == it.len()`** then element-wise
(`:3773`); `Set`/`FrozenSet` → **subset** (`:3781`); scalar → equality (`:3783`).
`AntiUnifyWitness` (`:3431+`) threads a path exactly parallel to `anti_unify_values`.
`StructSim` (`:3671`) is the same recursion with a graded numeric-vector leaf.

**There is not one line in any of them that knows what a stroke, a concept or a
program is.** No `if predicate == "seg"`, no domain enum, no type dispatch on node
type. The wildcard sentinel is the sole convention, and even it is a
constructor-agnostic content compare (`is_wild`, `:3347-3354`, which was *made*
content-comparing precisely because a `Tuple` sentinel round-tripping through Python
came back a `List` and silently stopped matching).

**So the answer to the brief's question is: yes, `AntiUnify` over a spatial
signature and a formula signature would find genuine shared structure — *if* both
were encoded compatibly.** The operators are indifferent. Confidence: **high** (read
all four implementations).

### 4.2 What IS domain-specific — and it is four things, none of them the algebra

1. **The container choice, which is forced per grain** (§3.4). This is the real
   constraint. `Tuple` gives you positional paths and costs you equal length;
   `FrozenSet` gives you open arity and subset coverage and costs you WILD and
   paths; `Dict` gives you keyed alignment and costs you order. A grain picks the
   one its own operation needs, and cross-domain comparison between a `Tuple`-encoded
   thing and a `FrozenSet`-encoded thing does not fail *gracefully* — it falls
   through `anti_unify_values`' final arm to bare WILD (`:3417`), i.e. it reports
   "these have nothing in common," which is a **false negative that looks like a
   result**.
2. **Equal length.** Two relation-systems of different arity never align
   element-wise. This is why the concept vector is fixed-arity with an explicit
   `_ABSENT` filler, and why `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.2
   registered a NO-GO on per-pair `AntiUnifyWitness` at concept grain: *"aligning by
   predicate makes the predicate correspondence the identity map."* Alignment is a
   precondition the algebra does not supply.
3. **The codebook POOL, which is the node type.**
   `CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`'s headline: *"a node type is the
   only mechanism that partitions a `ShapeDecode` candidate pool; `kind` is a
   pass-through label that nothing filters on."* Its measurement is the single most
   important empirical constraint on this whole charter, and I reproduce it in full
   because §7.1 turns on it:

   | merge | held signatures re-decoded | verdict **CHANGED** |
   |---|---|---|
   | the four **stroke** grains → one pool | 502 | **261** |
   | `ShapeSignatureCoarse` alone, effect on the primary fine pool | 237 | **147** |
   | `ShapeSignatureMid` alone, same | 237 | **46** |
   | the eight own-pool reading-faculty types → one pool | 51 | **1** |

   **Verdict: NO-GO on all fifteen.** Merging pools *within the ink domain alone*
   flipped 52% of verdicts. Whatever the cross-domain answer is, it is not "put
   everything in one pool."
4. **The comparator.** `CLAUDE.md`'s own run-16 reconciliation
   (`:478-495`) is the measured statement of this: *"earned quanta are the
   LEARNING/PROPOSAL layer … strong continuous geometry is the VERDICT layer —
   'bins propose, continuous decides,' measured"* — +51.5pp, CI-separated, from
   changing the comparator alone. §2.1's cross-modal script is the same fact stated
   architecturally: `PointSetDist` for ink, `DtwTo` for speech, **and no attempt to
   share the metric**.

### 4.3 Verdict

**The shape math is domain-neutral; the encoding discipline is not; and the
comparator should not be.** That is a three-part answer and each part points at a
different piece of the design in §7.

---

## 5. Part 2 — the synesthesia literature, read

I treated this as literature to check, not to recall. Where I could only reach an
abstract or a fetched summary I say so.

### 5.1 Cross-activation: the structural/proximity account

Ramachandran & Hubbard (2001) proposed that grapheme–colour synaesthesia arises from
**excess neural connections between anatomically adjacent regions** — the visual
word form area and colour area V4, both in the fusiform gyrus — surviving a
developmental pruning process that normally removes them. The 10-year review
(Hubbard, Brang & Ramachandran, *Journal of Neuropsychology* 2011) reports anatomical
differences in exactly the predicted regions (early visual areas, fusiform gyrus, and
the white matter underlying it), and a 2010 refinement in which *features* rather than
whole letters partially activate V4 early.

**Why this matters for the design:** cross-activation is fundamentally a claim about
**adjacency**. The domains connect because their representations happen to be
neighbours. There is no shared abstract code in this account at all — it is the
purest possible version of "domain A wired directly to domain B."

Confidence: **medium** — I read the search-result summaries and the abstract-level
description; the two full PDFs I tried (`sfu.ca` mirror, `daysyn.com`) failed to
fetch (binary PDF and a refused connection respectively). I have not read either
paper end to end. `[unverified]` on any specific quotation.

### 5.2 The evidence against pure cross-wiring: the inducer is the CONCEPT, not the form

This is where the literature turns, and it turns hard.

**Dixon, Smilek, Cudahy & Merikle, "Five plus two equals yellow," *Nature* 406:365
(2000).** A digit–colour synaesthete's photisms are triggered by the **result of a
mental arithmetic problem** — a digit never presented to any sense. The finding, as
reported in the sources I read: *"an externally presented inducing stimulus is not
necessary to trigger a photism … simply activating the concept of a digit is
sufficient."*

**Mroczko-Wąsowicz & Nikolić, "Semantic mechanisms may be responsible for developing
synesthesia," *Frontiers in Human Neuroscience* (2014)** — this one I fetched and
read. Its argument, with its own evidence:

* *"only the concurrents exhibit clear sensory-like properties, while the inducers
  take the form of concepts"* — one cannot *perceive* "June" or "Thursday", yet
  these are among the commonest inducers;
* the ambiguous-grapheme result: a glyph read as the letter V versus the Roman
  numeral V elicits **different colours** — the *interpretation*, not the retinal
  image, drives the concurrent;
* the Glagolitic-letter experiment (Mroczko et al. 2009): novel graphemes acquired
  colours **within minutes**, by semantic mapping onto familiar letters — *"too
  rapid … to be accounted for by low-level sensory cross-wiring"*;
* the conclusion: associations occur *"through a high-level of system organization,
  that enables associations … in a more elaborated, distributed and flexible manner
  than what can be accounted for by direct synaptic connections between sensory
  areas."*

This is the **ideasthesia** position (Nikolić): *sensing concepts*. The inducer is
semantic; only the concurrent is sensory.

Confidence: **high** for the Mroczko-Wąsowicz & Nikolić content (fetched and read
the full article via Frontiers); **medium-high** for Dixon 2000 (I could not get past
Nature's and PubMed's cookie walls; the finding is reported consistently in three
independent sources I did read, including the Frontiers paper's own citation of it).

### 5.3 Hub-and-spokes — and this is the direct architectural analogue

**Chiou & Rich, "The role of conceptual knowledge in understanding synaesthesia:
Evaluating contemporary findings from a 'hub-and-spokes' perspective," *Frontiers in
Psychology* (2014)** — fetched and read.

* **The spokes** are modality-specific cortical regions (colour areas, visual word
  form regions) — each representing its own perceptual content in its own terms.
* **The hub** is the anterior temporal lobe: *"the ATL acts as a 'hub' that works in
  tandem with modality-specific areas (spokes) to integrate various perceptually
  based content into a meaningful conceptual entity."*
* **The conclusion:** *"the ATL functions as a representational 'hub' that processes
  lexical meaning and associates the lexicon to synesthetic color representation at
  an abstract, conceptual level."* The paper argues against direct cross-wiring:
  the critical inducer→concurrent link happens **at the conceptual stage in the
  hub**, not along a sensory pathway.

**Put that next to §2.1 and the correspondence is not loose, it is structural.**

| hub-and-spokes | `seeds/cross_modal.json` |
|---|---|
| spoke: modality-specific representation | `axs_synth_feat` on `Concept{is_grapheme}` / `Concept{is_audio}` |
| spoke: modality-specific recognition | `Argmax(-PointSetDist)` / `Argmax(-DtwTo)` |
| hub: amodal conceptual node | the `Concept{is_phoneme}` node `P`, reached via `of_phoneme` |
| hub binds spoke to spoke | `bind_grapheme_phoneme` → `sounds_like` / `written_as` |
| generalisation lives in the hub | *"recall generalises across writers and speakers via the shared concept"* |

The `Concept` node in that seed **is** the ATL hub, in the precise sense Chiou &
Rich mean: the place where two independently-recognised modality-specific
identities become one entity, and the place generalisation comes from.

Confidence: **high** — fetched and read; quotations are from the fetched text.

### 5.4 SNARC, the mental number line, and ATOM — the "shared code" case, with its counter-evidence

**SNARC** (Dehaene, Bossini & Giraux 1993): in parity judgements, people respond
faster with the left hand to small numbers and the right hand to large ones, in
people who are *not* synaesthetes. Dehaene's account: number magnitude is
automatically accessed and *"bears a natural and seemingly irrepressible
correspondence with the left–right coordinates of external space."* Later work
extends the association to vertical and near/far space, i.e. it is not specifically
left-right.

**ATOM** (Walsh, "A theory of magnitude: common cortical metrics of time, space and
quantity," *Trends in Cognitive Sciences* 7:483-488, 2003): time, space and quantity
are *"part of a generalized magnitude system,"* linked by a common metric **for
action**. This is the strongest published form of "one genuinely shared abstract
code across domains."

**And the honest counter-evidence, which I went looking for specifically:** *"Number,
time, and space are not singularly represented: Evidence against a common magnitude
system beyond early childhood"* (*Psychonomic Bulletin & Review*, 2018) — the title
is the finding, and the qualifier "beyond early childhood" matters: it argues a
common system may exist early and **differentiate** with development. I could not get
past Springer's cookie wall for the full abstract; `[unverified]` beyond the title
and the search-result framing.

Also relevant and against the strongest reading: *"The SNARC effect does not imply a
mental number line"* (*Cognition*, 2008) — the effect is real; the inference to a
single spatial magnitude representation is contested.

**What I take from this cluster:** there is real evidence for shared structure
between an abstract domain (quantity) and a physical one (space), in the general
population, not just in synaesthetes — and there is real evidence that the shared
representation is **not a single undifferentiated code**. Both halves matter for §7.

Confidence: **medium-high** on SNARC and ATOM (read consistent summaries from
multiple sources including the TiCS listing and the Wikipedia SNARC article);
**low-medium** on the 2018 counter-paper (title and framing only).

### 5.5 The most useful thing in the whole literature: INTERFACE vs OVERLAP

**Myachykov, Chapman & Fischer, "Cross-representational interactions: Interface and
overlap mechanisms," *Frontiers in Psychology* 7:2028 (2017)** — fetched and read.
This paper does the exact job §2.4's table needs done, and does it from the
psychology side with a criterion.

Two mechanisms by which two co-activated representations can interact:

* **Interface** — the two representations interact **via a third-party mediating
  system** (typically attention or working memory), established in **online /
  situated contexts only**. Crucially: *"the mediator is not part of either
  concept's core semantic meaning."*
* **Overlap** — the representations **share permanent architectural features**
  (magnitude, affect, sequencing), so they interact **both online and offline**.

Their own assignment of phenomena: SNARC and number-space priming and past-left/
future-right temporal mappings are **interface**; grip-size × numerical magnitude,
weight × number, volume × number, and ATOM's generalized magnitude are **overlap**,
because magnitude is *"an integral semantic component"* of those representations.
Their summary sentence: *"interface-based interactions are limited to online or
situated contexts while overlap between representations is a feature of permanently
stored representations."*

**Map that onto §2.4 and it lands cell for cell.**

| Myachykov et al. 2017 | this substrate |
|---|---|
| **interface** — third-party mediator, online, not part of core meaning | **co-presentation binding** — the mediator is the `co_modal` co-occurrence stamp (or `bind_synchronous`'s ±tol window); it is not part of what a grapheme *is* |
| **overlap** — shared permanent architectural feature, works offline | **shared abstract code** — the meta-shape *is* part of what the mechanism is; `TransferDecode` fires with no co-occurrence at all |

I did not go looking for this paper; it surfaced while searching for ideasthesia's
computational connections. It is the single most directly useful literature hit in
this document, because it supplies **a discriminator, not just a taxonomy** — and
§7.2 adopts it.

Confidence: **high** — fetched and read; quotations from the fetched text.

### 5.6 Conceptual metaphor — and the finding that changes the design

Lakoff & Johnson's conceptual metaphor theory (TIME IS SPACE, ARGUMENT IS WAR) is
the canonical account of an abstract domain borrowing the relational structure of a
concrete one. **Boroditsky, "Metaphoric structuring: understanding time through
spatial metaphors," *Cognition* 75:1-28 (2000)** is the empirical test I checked,
and it has three findings, the third of which is the important one:

1. space and time **do** share conceptual structure;
2. spatial relational information is **just as useful** for thinking about time as
   temporal information is;
3. **"with frequent use, mappings between space and time come to be stored in the
   domain of time and so thinking about time does not necessarily require access to
   spatial schemas."**

Finding 3 is an architectural claim and it is the one I would put in a design
document: **a cross-domain mapping, used often, gets stored locally in the target
domain and stops being a cross-domain lookup.** That is a *consolidation* step
neither §2.1 nor §2.3 currently has — and it is exactly what `sd_recognize`'s
"recognise without re-minting" and the `has_transform`-edge mint-once guard do at a
different grain.

Confidence: **medium-high** — I read consistent summaries of the paper's three
findings from the search result and the ScienceDirect listing; I did not read the
full 28-page paper.

### 5.7 The caveat that applies specifically to "formula": structure-mapping FAILS in object-rich domains

**Schlimm, "Two Ways of Analogy: Extending the Study of Analogies to Mathematical
Domains," *Philosophy of Science* 75(2):178-200 (2008)** — fetched the abstract and
summary.

The argument: structure-mapping theory (Gentner/SME — the theory the whole
`analogical_thinking` faculty and §2.3's transfer path descend from) explains
analogies well in domains with **sparse relational structure**, and **fails in
"object-rich domains," which are prevalent in mathematics** — domains with many
concrete objects carrying specific properties. Schlimm's alternative for those is the
**axiomatic approach**: analogies are recognised by a **shared description in terms
of laws or axioms**, not by a structure-preserving object mapping. He argues the two
are complementary, each adequate for its own domain type, and that the axiomatic
route is what actually *facilitates the discovery* of new mathematical analogies.

**Why this is directly load-bearing:** the charter asks to compare a physical shape
to a **formula**, and this is a published argument that the substrate's dominant
analogical machinery — object-to-object structural alignment — is *the wrong tool
for exactly that pairing*, with a named alternative. It is also, unexpectedly, a
restatement of something this tree already knows: `RULE_SIGNATURE_TO_RUST_RESULTS.md`
§1 found that the shape-math family was **insufficient** to compute a rule's own
signature and that the right answer was to hold the *procedure* (Program IR)
instead. A law/axiom you *apply* is intensional; an object set you *align* is
extensional. Which brings us to §7.3.

Confidence: **medium-high** — fetched abstract and structured summary; did not read
the full paper.

### 5.8 Verdict on shared-vs-translated

Reading the four clusters together:

1. **Nobody credible defends pure translation** (domain A rendered into domain B's
   representation). Cross-activation is direct connection, not translation; every
   other account routes through something shared.
2. **The weight of post-2000 evidence is against direct sensory cross-wiring being
   the whole story** and for a **conceptual/amodal mediating stage** — §5.2's three
   independent lines (arithmetic-induced photisms, ambiguous graphemes, minutes-fast
   novel-grapheme transfer) and §5.3's hub.
3. **But "shared" does not mean "one code."** §5.4's counter-evidence and §5.5's
   interface/overlap split both say the shared thing is *partial and specific* — a
   shared *magnitude* component, a shared *conceptual entity*, not a universal
   representational medium.
4. **Is the shared code spatial specifically, or genuinely domain-neutral?** The
   honest answer from this reading is **neither cleanly**. Space has a privileged
   *scaffolding* role (SNARC, TIME IS SPACE, Boroditsky's finding 2), but
   Boroditsky's finding 3 says the borrowed structure gets **stored in the target
   domain** and stops needing the spatial source — so spatial privilege is
   developmental/acquisitional, not architectural. That is a much better answer for
   this substrate than either extreme, and §7.2 uses it.

---

## 6. Part 2b — has anyone used synesthesia as an ENGINEERING SCHEMA? (the creator's question)

The creator asked directly whether anyone else has done *this specific work*. I ran
six targeted searches, deliberately distinguishing "synesthesia is studied/modelled"
from "synesthesia's own theorised mechanism is used as the blueprint for how a
machine should compare across domains." Queries: `"synesthesia-inspired" OR
"synesthetic" computational model cross-modal representation learning`; `"amodal
representation" cognitive architecture cross-domain analogy shared abstract code
design principle AI system`; `"cross-modal binding" cognitive architecture
synesthesia inspired symbol grounding shared concept node graph agent`; `synesthesia
as design principle for artificial general intelligence cross-domain analogy shared
representational code proposal`; `ideasthesia OR "cross-activation" synesthesia
knowledge representation analogy engine symbolic AI schema blueprint`; plus a
structure-mapping/mathematical-domains query.

**What exists, in three clean categories, none of which is the thing:**

1. **Computational models OF synesthesia** — i.e. synesthesia as the *explanandum*.
   *"The Emergence of Synaesthesia in a Neuronal Network Model via Changes in
   Perceptual Sensitivity and Plasticity"* (PLOS Computational Biology, 2016);
   *"A Deep Learning Model of Perception in Color-Letter Synesthesia"* (2020).
   These model how synesthesia *arises*; they propose nothing about machine
   architecture.
2. **Sensor fusion branded "synesthesia"** — "Robot Synesthesia" (projecting tactile
   contact into a shared 3-D point cloud with visual depth; tri-modal vision/audio/
   touch fusion via ResNet encoders and multi-head attention); "Synesthesia of
   Machines (SoM)" (arXiv 2506.07647 — cross-modal generation of *communication
   channel* data). These are multimodal fusion with a metaphorical name. They share
   a **latent space**, which is the vector-analogy answer this project's own
   `shape_math_grounding.md` explicitly examined and declined: *"the vector offset
   is a FLAT, first-order difference … it CANNOT carry the relational graph."*
3. **Popular/positional pieces** — Sequoia's "On AI Synesthesia," Psychology Today's
   "The Importance of Synesthesia in Artificial Intelligence." Both say multimodal
   foundation models have a shared latent space and call that synesthesia. Neither
   is a mechanism proposal.

**And the honest null, which I am reporting as a finding rather than as a failure:**
I found **no work that takes synesthesia's own theorised mechanism — cross-activation,
or ideasthesia's semantic inducer, or Chiou & Rich's conceptual hub — and uses it as
the design schema for structural comparison across a physical, a conceptual and a
symbolic/formal domain in a machine.** The closest theoretical neighbours are
Barsalou's grounded-cognition programme (arguing grounding mechanisms should
*replace* amodal ones in cognitive architectures — the opposite direction to this
charter) and structure-mapping (SME/Gentner), which is domain-general by
construction but is not derived from synesthesia and does not reference it. One
search engine volunteered the negative itself: results *"did not specifically discuss
connections to analogy engines, symbolic AI, schema blueprints, or knowledge
representation systems in the computational sense."*

**Three honest limits on that null.** (a) Web search is not a literature review; I
did not search ACM DL, IEEE Xplore, PhilPapers or Google Scholar directly. (b) The
word "synesthesia" is heavily colonised by the sensor-fusion sense, which crowds
search results and could easily bury a genuine hit. (c) Absence of the *phrase* is
not absence of the *idea* — Chiou & Rich's hub-and-spokes is itself an import from
the semantic-cognition literature (Lambon Ralph et al.), so the architecture has
prior art even where the synesthesia framing does not. **What I am claiming is
narrow and I want it read narrowly: the specific move of using synesthesia as the
schema appears not to have been made. `[unverified]` beyond the six searches
above.**

---

## 7. Part 3 — the design

### 7.1 Question 1: is there a genuinely domain-neutral encoding available?

**Partly, and the part that is available is already in use.**

*What is already shared and should stay shared:* the **relation-system format** —
a flat collection of predicate-headed tuples (§3.4). Four grains built independently
converged on it. It is what `ShapeDecode`'s codebook loader reads, what
`StrokeQuantize` emits, what `chunk_rels` is, what a concept vector is. **No work is
needed to make this shared; it already is.**

*What is not available and should not be forced:* a shared **container**, a shared
**arity discipline**, and above all a shared **pool**.

The pool point is where I would push back hardest against the instinct the charter
invites. Take `CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`'s measurement seriously:
merging the four **stroke** codebooks — four grains of *the same domain*, ink,
sharing a predicate vocabulary — re-decoded 502 held signatures and **changed 261
verdicts**. Fifteen consolidation candidates were examined and **fifteen were
declined**, three of them *technically eligible* under the prereg's own decision rule
and declined anyway. A cross-*domain* pool merge is a strictly larger version of the
move that measurement rejected.

`SHAPE_TYPE_VOCABULARY_SPIKE.md` reached the same shape of answer one level down and
I am adopting its sentence verbatim as this document's answer to question 1:
**"unify the vocabulary, keep the families apart."**

So: **one format, many pools.** The genuinely missing piece is not an encoding — it
is a *declaration* of which pool means what, and §5.2 of that spike already proposes
the mechanism (`ShapeRole`, generalising the existing `CodebookRegistry` anchor at
`shape_decode.rs:5281-5296`). This document does not need to re-propose it; it needs
to note that **cross-domain comparison is the use case that makes that declaration
load-bearing rather than tidy**, because a cross-domain comparison is exactly the
operation that must know whether two signatures are in comparable encodings before
it runs `AntiUnify` on them and gets bare WILD (§4.2 item 1).

### 7.2 Question 2: shared encoding, or co-presentation binding? — the wrong question, and the family that replaces it

**I first wrote this section as a binary with a discriminator. That was wrong in a
specific and correctable way, and the creator named it: *"i suspect there is not one
answer - but a shape."* This subsection is the corrected version; §7.2.1 keeps the
discriminator, because it turns out to be the parameter, not the switch.**

The error is the exact one the sd loop's own rung 2 exists to prevent. Two things
are not either *identical* or *unrelated*: they can be related **by a transform**,
and the finding is the transform's parameter, not the endpoints. Applied here: the
question is not "shared encoding or co-presentation binding," it is **what governs
which one a system lands on** — and once asked that way, the answer is already
present in this document's own evidence and needs no new research.

**The parameter is the amount of real structure the two domains share. The ordering
is MDL (§9b). And the ladder that results is the sd loop's own growth ladder, one
level up.**

| shared structure | cross-domain relation | worked instance in this document | sd-loop rung it corresponds to |
|---|---|---|---|
| **the same map, two presentations** | identity of denotation; check by rendering both and comparing | rotation the `Transform` vs rotation the formula (§7.3) | **rung 1** — exact recognise |
| **the same shape modulo a per-dimension delta** | a `Transform{dim, delta}` — one held shape, stepped | a rotated stroke vs its canonical form (`strokes.rs`) | **rung 2** — transform in the existing basis |
| **an abstract axis that must be minted to see the sharing at all** | transfer a *procedure* over a shared axis; the axis is the finding | `spatial_foveation` → rule scanning, over `selective_gating` (§2.3) | **rung 3** — infer the dimension |
| **none — the pairing is pure convention** | bind the two *identities* at a shared node; record the fact | grapheme ↔ phoneme (§2.1); word ↔ visual referent (§2.2) | **rung 4** — mint |

Reading that table top to bottom: **co-presentation binding is the cross-domain
`sd_mint_quantum`.** It is what a system does when *nothing it holds explains the
relation* — so it records the relation itself as a new held fact. That is not a
lesser mechanism, and it is not a competitor to the others; it is the bottom rung of
one Occam-ordered ladder, and CLAUDE.md already says what the bottom rung is for:
*"mint novelty … only after BOTH rungs fail."*

Three things make me think this is a real correspondence and not a pleasing
coincidence:

1. **It is MDL-ordered for the same reason the sd loop is** (§9b). Each rung down
   costs more description length: identity is free, a delta is one integer, a minted
   axis is a new dimension, a bound convention is an irreducible new fact. Occam
   order falls out; it is not imposed.
2. **The two literatures agree on the *ends* and disagree about the *middle*,
   which is what a family predicts and a binary does not.** Myachykov et al.'s
   interface/overlap split (§5.5) is the bottom rung versus the top three, and the
   phenomena they had trouble assigning — SNARC as interface, magnitude-grip as
   overlap, the same *pair of domains* under different task demands — are exactly
   what "one family with a parameter" predicts you would find at the boundary.
3. **Boroditsky's finding 3 is movement ALONG the family, and it has a direction**
   (§5.6): a frequently-used mapping *"come[s] to be stored in the domain of time"* —
   i.e. a relation that started as a bound cross-domain fact becomes local structure.
   **A system under iteration pressure climbs this ladder.** That is the creator's
   §9 claim ("any large system allowed to iterate sufficiently to be close to
   optimal") stated as a trajectory rather than an endpoint, and it makes
   consolidation (§7.2.1, last paragraph but one) not an extra feature sitting beside
   the two bridges but *the ladder's own dynamics*.

**What this changes about the recommendation.** Not "pick the co-presentation
pattern." Rather: **the deliverable is the ladder, and the thing worth building is
whichever rung is missing.** Rungs 2 and 4 are built (`TransformDecode`;
`cross_modal.json`). Rung 3 is built but shallow (§2.3: two mechanisms, procedure
transfer only, keyword entry point). **Rung 1 — "these two descriptions denote the
same map" — does not exist at all**, which is precisely what §7.3 discovers
independently, from the other direction, by working the rotation example. Two routes
arriving at the same gap is the strongest signal in this section.

**And the honest limit, stated before anyone builds on it:** the sd-loop
correspondence is an analogy I am drawing between a measured ladder (the sd loop's,
which is gated and live) and a proposed one (this table's, which is not). The rungs
line up; **nothing measures that they line up.** I would not put the table in a
prereg without §7.4's slice first showing that rung 1 is even reachable.

### 7.2.1 The discriminator, kept — because it is the parameter's operational test

Myachykov et al.'s split (§5.5) survives the reframe intact, no longer as a
choice-of-architecture but as **the cheapest available test of where on the family a
given pair sits**, which is exactly what a parameter needs:

> **Use co-presentation binding (interface) when the two things merely CO-OCCUR.
> Use shared abstract code (overlap) when the two things SHARE STRUCTURE.**

Restated in this substrate's own terms, with the failure mode of each named:

* **Co-presentation binding** (`seeds/cross_modal.json`). Binds *identities*.
  Requires **no** structural commensurability at all: `PointSetDist` and `DtwTo` do
  not have to be comparable, and the grapheme "3" and the phoneme /θriː/ share no
  structure whatsoever — their relation is pure convention. **This is the correct
  and only available mechanism for arbitrary pairings**, and its correctness does
  not degrade as the domains get more distant. Its failure mode is that it
  generalises **only through the shared node**: it can tell you "this symbol is
  pronounced that way" and it can never tell you *why*, nor transfer anything to a
  third symbol.
* **Shared abstract code** (`TransferDecode` + `mechanism_index`). Transfers
  *procedures* between domains that classify the same. Requires the shared structure
  to be real. Its failure mode is the one measured twice this month: **the
  classifier answers anyway.** `META_SHAPE_FIRST_CLASS_RESULTS.md`'s core finding —
  *"a recognizer that always answers can never produce a residual, and a grain with
  no residual can never grow"* — is precisely the risk of the overlap route, and the
  fix it landed (delete the tiebreak) is precisely the guard cross-domain use needs.
  A cross-domain overlap claim that cannot come back **empty** is worthless.

**And the movement between them — consolidation — which the literature supplies and
this substrate does not have.** Boroditsky's finding 3 (§5.6): a frequently-used
cross-domain mapping gets *stored in the target domain* and stops requiring the
source. Under §7.2's reframe this is not a third mechanism sitting beside the other
two — **it is how a pair MOVES UP the ladder**, from rung 4 (a bound convention) to
rung 3 or higher (held structure that explains the binding). Neither §2.1 nor §2.3
does it: `TransferDecode` re-derives the transfer every time, and the cross-modal
binding stores an edge but stores nothing about *why*. The natural home is the sd
loop's own mint-once-then-recognise discipline, which is this exact pattern at a
different grain. **I am naming it, not proposing it** — it is downstream of rung 1
existing at all.

**Why I am still not recommending "one shared encoding," even under the family
reframe:** the family says a shared encoding is the *right* answer at the top rungs
and the *wrong* answer at the bottom — which is precisely why it cannot be adopted
globally. §7.1's measurement is the bottom-rung cost made concrete (261 of 502
verdicts flipped by merging pools that did not share enough structure to earn the
merge); §4.2 says a mismatched-container comparison fails *silently as a false
negative*; §3.2 says 98.9% of the concept population has no structure to share
anyway. The MDL statement of it, from §9b: **compression only wins where structure is
genuinely shared, and forcing it where it is not costs more than it saves.** That is
the parameter doing its job, and it is why "which rung is this pair on" is a better
question than "which architecture do we adopt."

### 7.3 Question 3: the worked example — a rotation, and the formula for a rotation

The brief proposes physical rotation versus its own formula as the sharpest possible
test. It is, and working it through changes my answer.

**What the substrate holds for a physical rotation.** Three objects, all graph data:

1. A `DimensionGenerator` codebook node. The five that ship
   (`seeds/shape_decode_loop.json`) are:
   ```
   {"name":"rotation90",   "kind":"rotation90", "coord_dims":[1,2], "params":[1,2,3]}
   {"name":"reflection_r", "kind":"reflection_r","coord_dims":[1,2], "params":[1,2]}
   {"name":"reflection_c", "kind":"reflection_c","coord_dims":[1,2], "params":[1,2]}
   {"name":"scale2",       "kind":"scale2",     "coord_dims":[1,2], "params":[1,2,3]}
   {"name":"cycle4",       "kind":"modular",    "coord_dims":[1],   "params":[1,2,3], "modulus":4}
   ```
2. A `Transform{dim: "latent:rotation90", delta: k}` node, minted per observation by
   `sd_recognize_dim`.
3. A `LatentDimension{name:"latent:rotation90", generator, k}` node — minted
   **once**, via `add_node_if_absent`, because (as
   `seeds/shape_decode_loop.json`'s own comment records, citing `SHAPE_AUDIT.md`
   §4.4) *"a Transform genuinely IS per-observation data, but a LatentDimension is a
   WORLD-MODEL FACT — 'latent:rotation90' is the same dimension whichever
   observation revealed it."*

**What the substrate holds for a formula.** A Program IR subgraph
(§3.3): `x' = x·cosθ − y·sinθ` would be `ProgAssignVar` / `ProgBinOp` / … Term nodes,
installed via `add_term_subgraph`, executed by `ProgEval`, and — per
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2 — surviving a checkpoint round-trip
byte-identically.

**Are these already secretly the same shape? No — and the reason is not a gap, it is
the substrate's own governing invariant.**

`CLAUDE.md:517-554` states it: *"In-frame is INTEGER… **Non-integer math is
CROSS-FRAME.** All real-valued structure — rotation by a real angle, real scale
ratios, π, Fourier … — lives in the MAP between frames (a generator / `Transform` /
base / comparator / rendering), NEVER in a frame's coordinates."* And the decision
procedure: *"is this value IN a frame, or BETWEEN frames?"*

Apply it:

| | in-frame or cross-frame? | what the substrate holds |
|---|---|---|
| the rotated tromino's coordinates | **in-frame**, integer | the observation's signature |
| `Transform{dim:"latent:rotation90", delta:2}` | **in-frame observable** of a cross-frame map — integer `k` | a `Transform` node, per observation |
| `rotation90` the generator | **cross-frame map** | a `DimensionGenerator` node, `kind` dispatching to Rust |
| `x' = x cosθ − y sinθ` | **cross-frame map**, real-valued, intensional | a Program IR subgraph |

**So the formula and the physical rotation are not two encodings of one object.
They are the same object described from the two sides of the frame/continuum
invariant: the formula is the *intensional* cross-frame map, and the `Transform` is
its *extensional*, stepped, integer-`k` rendering.** CLAUDE.md already says exactly
this in a sentence written for a different purpose: *"You can apply π, but any given
circle is stepped."*

**And here is the missing piece, stated precisely.** The substrate *already has* a
node type for the intensional cross-frame map: `DimensionGenerator`. It *already
has* one generator kind whose map is **defined by graph data rather than Rust
dispatch** — `kind: "linear"`, whose flattened row-major integer `matrix` field is
documented as *"the ONLY generator kind whose transform is DEFINED BY GRAPH DATA
rather than by a hardcoded Rust dispatch … This field is what makes a MINTED
generator (`GenInfer` → `sd_infer_generator`) participate in decode: the inferred
matrix rides in as data and `apply_linear_once` reads it — no new Rust dispatch arm
per discovered map"* (`shape_decode.rs:414-428`).

**What is missing is one edge.** There is no relation in the graph saying *this
`DimensionGenerator` is the same map as that Program IR subgraph*. A `linear`
generator's `matrix` and a rotation program's coefficients are the same
mathematical object held twice, in two encodings, with nothing connecting them and
no way to derive one from the other. Concretely, three things the substrate cannot
currently do, all of which are one edge away:

* **Read a formula, get a generator.** A taught rotation formula cannot become a
  `DimensionGenerator` the sd loop's rung 2 uses — even though `linear`'s matrix
  field was built to accept exactly such a thing from `GenInfer`.
* **Explain a generator with a formula.** `sd_infer_generator` can *mint* a matrix
  from observation; nothing can render that matrix as a formula, so the agent can
  recognise a rotation it cannot state.
* **Compare the two.** `AntiUnify` over `{a generator's matrix rows}` and
  `{a program's coefficient structure}` returns bare WILD today (§4.2 item 1) —
  different containers, different arities. Nothing in this comparison is
  *conceptually* hard; it is blocked at the encoding boundary.

**And per §5.7 (Schlimm), the right comparison here is probably not structural
alignment at all.** A formula is a **law you apply**, not an object set you align;
the axiomatic route says two things are analogous when they satisfy the same law.
The substrate's version of "satisfies the same law" is available and cheap: **apply
both and compare the renderings** — which is exactly the AbS discipline CLAUDE.md
already records as the measured winner (*"bins propose, continuous decides"*, +51.5pp
CI-separated). Do a formula and a generator agree? **Render both over the same
integer lattice and compare the stepped outputs.** That is a *behavioural*
equivalence check, it needs no shared encoding, and it is the same shape as SEER's
"external rewrite" pattern (`RULES_AS_SHAPE_DESIGN_SPIKE.md` §16.1): *check validity
and equivalence; do not require the thing to be symbolic.*

**What the example shows, in one line:** the hard part of comparing a physical shape
to a formula is not representational, it is that **the substrate has no object for
"these two descriptions denote the same map,"** and its own frame/continuum
invariant already says what that object is — a cross-frame map with two
presentations, intensional and extensional. That is a much smaller and much more
concrete finding than "unify three domains."

### 7.4 What this would cost, and the smallest slice that tests it

**Explicitly out of scope**, in the spirit of `RULES_AS_SHAPE_DESIGN_SPIKE.md` §11.1:

1. **Any unified cross-domain encoding.** §7.1. The measurement against it already
   exists and it is the strongest empirical fact in this document.
2. **Any codebook pool merge.** Same measurement, 15/15 NO-GO.
3. **Retrofitting concepts with relational structure.** §3.2: 190 edges over 10,775
   concepts. `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1 already called this
   *"a no-op wearing the costume of a fix."*
4. **Consolidation (§7.2's third mechanism).** Real, literature-supported, and
   downstream of everything else. Named, not proposed.
5. **Any claim that this moves a benchmark.** Per the standing rule, every claim in
   §7 is a mechanism claim with no number attached.

**The smallest slice that actually tests the hypothesis.** Under §7.2's family the
target picks itself: **rungs 2, 3 and 4 are built; rung 1 does not exist.** It is
also the only place in this whole document where I found something genuinely missing
rather than something already built (§2) or already measured as a bad idea (§7.1).
Two independent routes — the family, and the worked rotation example — arrive at the
same gap, so that is what the slice tests:

> **A physical transform and its formula are the same cross-frame map, and the
> substrate can be made to demonstrate that behaviourally with no new encoding.**

The slice:

* **Pick the pairing that already exists on both sides:** the `linear`
  `DimensionGenerator` kind (matrix in graph data, `apply_linear_once` reads it) and
  a Program IR subgraph computing the same map. Both mechanisms are built and gated;
  neither needs a new Term.
* **The test is a rendering comparison, not a structural one:** over a fixed set of
  integer lattice points, evaluate the generator (via the existing `DimInfer` path)
  and the program (via the existing `ProgEval`), and compare outputs. This is the
  §5.7/§16.1 "external equivalence check" and it writes nothing.
* **The single number nobody has:** on the five shipped generators, how many can be
  expressed in the P1 Program-IR subset at all? `RULE_SIGNATURE_TO_RUST_RESULTS.md`
  §1 measured exactly this class of question for a different algorithm
  (`emit_prog_ir` verdicts per function, with named blockers) and the same harness
  answers it. If the answer is "none of them, because the subset can't express a
  matrix multiply," that is a complete and valuable null and it kills the design
  cheaply.
* **Only then**, and only if the equivalence check passes, an edge type
  (`denotes_map` / `rendered_by`) linking a `DimensionGenerator` to a Program IR
  root — one edge type, zero new Terms, and per
  `RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2's own honest note, **it needs a real Γ
  production declared**, not an `add_edge_unchecked` (that document minted its
  `SignatureProgram` link as an *attr* specifically to avoid the unchecked-edge
  pattern, and named declaring the production as the honest follow-up it did not do).

Two things I want to say about this slice honestly. First, **it is small on
purpose**, and the reason is that everything larger in this space is either already
built (§2) or already measured as harmful (§7.1). Second — and this is the awkward
half, mirroring §11.2 of the rules spike — **I do not know how often the substrate
would actually use it.** A rotation and its formula are the *easiest* case; the
charter's harder cases (a physical shape vs a *concept*) run straight into §3.2's
190 edges. Designing the measurement that shows this capability is *used* is harder
than building it, and if I were writing the prereg I would spend most of it there.

---

## 8. What the two bridges do NOT cover, stated before the conclusions

Three gaps, so they are not discovered later as surprises:

1. **Nothing compares a physical shape to a concept, in either direction.**
   Co-presentation can *bind* them (a stroke co-presented with the word "three" —
   this is `multimodal_referential_video.py`'s exact operation). Shared abstract
   code can transfer a *procedure* between them. **Neither compares their
   structure**, and §3.2 says there is no concept-side structure to compare.
2. **The overlap route's entry point is a keyword scorer** (§2.3). Everything it
   does is downstream of `RecogniseShape`'s substring test, which
   `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §9 confirms still carries content
   defects anchoring cannot fix (*"`spatial_motion` carries the keywords `fixed` and
   `station`, so `reservation_station → fixed_point_stability` still comes back"*).
3. **`TransferDecode` transfers steps, not shapes.** A `Mechanism`'s `steps` are
   token lists (`["quantize","FIELD","into","UNIT"]`), not signatures. This is a
   procedure-transfer mechanism wearing a shape-transfer name, and while I think the
   procedure is the more useful thing to transfer, the distinction should be in the
   record.

---

## 9. The generalisation — why this should be the convergent answer anywhere, not just in brains

The creator's second sharpening: *"it wont just be in the brain, it will be visible
in basically any large system allowed to iterate sufficiently to be close to
optimal."* I think that is right, it is checkable, and there is a real formal account
of *why* rather than merely an observation that it keeps happening. Three grounds, in
increasing order of formality:

**(a) Convergent evolution — the general biological framing.** Independent lineages
under similar selective pressure arrive at similar structural solutions from
different starting material: flight in insects, birds, pterosaurs and bats;
camera eyes in vertebrates and cephalopods (same lens/iris/retina organisation,
*opposite* retinal orientation — the standard proof the two origins were
independent). The standard reading is that *"there is a limited set of optimal
designs or functional pathways that different lineages can independently arrive at."*
That is the exact shape of the creator's claim, one level more general than
synesthesia: the constraint, not the substrate, picks the answer.

**(b) The information-theoretic "why" — MDL, and it is already this tree's own
idiom.** A shared representation plus N cheap projections is shorter than N separate
representations **exactly when the domains share real structure**, and is longer
otherwise. This is not a metaphor here: `FixedCount`'s own doc comment defines it as
*"the MDL specificity of an induced pattern — how many leaf positions it FIXES … a
more-fixed rule is a stronger, more-compressive claim"* (`term.rs:805-812`);
`synth_enumerate.rs:80` enumerates *"by increasing SIZE (MDL/Occam: the shortest
program …)"*; CLAUDE.md's frame/continuum invariant states the identifiability guard
in MDL terms (*"never encode precision the steps cannot support (MDL)"*, `:535-537`);
and `COGNITION_IS_PHYSICS_LITERATURE.md:208` grounds it in Rissanen. **The sd loop's
whole growth ladder is an MDL argument**: recognise, else transform, else infer a
dimension, else — only then — mint. Minting is admitting the shared description does
not cover this, and paying for a new one.

The conditional in the MDL statement is the important half, and it is the same
conditional §7.2's discriminator turns on: **compression only wins where structure is
genuinely shared.** That is why "unify everything" is not the lesson and why
§7.1's 261-of-502 measurement is not a surprise — those four stroke pools were
merged *without* the shared structure being real at that grain, and MDL says the
merge should have cost something. It did.

**(c) A formal machine-learning version of the same theorem.** Baxter, *"A Model of
Inductive Bias Learning,"* JAIR 12:149-198 (2000), formalises learning a *bias* from
a family of related tasks and proves that a hypothesis space performing well on
enough training tasks also performs well on novel tasks in the same environment —
with the same conditional attached, which subsequent work sharpened: shared
representations improve learning **when the tasks are generated by a common feature
and the number of tasks is large.** That is the MDL argument with a sample-complexity
bound on it, and it carries the same "only if the structure is genuinely shared"
precondition. Confidence: **medium-high** — I read consistent summaries of the
theorem and the paper's framing, not the 50-page proof.

**So the claim generalises with a stated condition, which is the form worth
recording:** *any sufficiently-iterated large representational system whose domains
share real structure will find a shared representation, because the alternative is
strictly longer; and any such system whose domains do NOT share structure will not,
and forcing one on it will cost accuracy.* Both halves are measured in this tree —
the second one, at 261 verdicts out of 502.

**And note that this is §7.2's parameter, arrived at from the other end.** §7.2
reaches "how much structure is shared" by asking what governs which bridge a system
lands on; §9 reaches the same quantity by asking why the phenomenon should recur at
all. **The convergent-optimisation argument and the family are the same statement**
— MDL is what orders the rungs, iteration pressure is what moves a system up them
(Boroditsky's finding 3, §5.6), and the *condition* in the paragraph above is the
parameter's own threshold. That the generalisation and the design conclusion turn
out to be one object is the reason §7.2's answer is a shape and not a pick.

---

## 10. The convergence, named — three independent domains, one shape

Per the creator's instruction to name convergence explicitly if it holds, and to say
so plainly if it does not: **it holds, and it is three-way, not two-way.**

The shape all three land on: **domain-specific recognition in each domain's own
native terms, plus a shared node/structure at which independently-recognised
identities meet, with the shared thing carrying the generalisation.**

1. **Biological cognition.** Chiou & Rich's hub-and-spokes (§5.3): modality-specific
   spokes, an amodal ATL hub where the conceptual entity is formed, *"associates the
   lexicon to synesthetic color representation at an abstract, conceptual level."*
   Arrived at from lesion and imaging data in semantic cognition.
2. **Compiler optimisation.** An e-graph (SEER, ASPLOS 2024, read in
   `RULES_AS_SHAPE_DESIGN_SPIKE.md` §16) is a **shared representation of equivalent
   forms** — every reachable form held simultaneously in one structure, with the
   payoff coming from *"a representation DISCOVERED by one rewrite unlocking an
   optimization opportunity in a completely different, independently-reachable
   representation"* (§16.1). Arrived at purely under hardware-synthesis pressure,
   with no reference to cognition whatsoever. Its e-class is the hub; its distinct
   syntactic forms are the spokes; and its external-rewrite pattern — *call an
   opaque pass, check the result differs, union it in* — is precisely §2.1's
   "recognise natively, bind identities, don't require a shared internal
   representation."
3. **This substrate's own engineering constraints.** `seeds/cross_modal.json`
   (§2.1), arrived at from the practical fact that ink needs `PointSetDist` and
   speech needs `DtwTo` and there is no shared metric — and independently
   `TransferDecode` + `mechanism_index` (§2.3), arrived at from the practical fact
   that a spatial mechanism was wanted in the rule domain.

**Three independent pressures — natural selection, hardware-synthesis
super-optimisation, and this tree's own comparator constraints — landing on the same
architecture.** Per CLAUDE.md's own standard (a capability *independently re-derived*
in another body counting for more than the same body scoring higher), that is
stronger evidence for the architecture than any one of the three alone.

**And the honest non-convergence, which I want on the page next to it.** The three
do *not* agree about the second bridge:

* the brain has real **overlap** as well as interface — ATOM's shared magnitude code
  (§5.4) has no e-graph analogue at all;
* an e-graph has **no domain-specific recognisers** — everything inside it is
  already the same language, so it is a hub with no spokes;
* this substrate has both bridges but, uniquely among the three, **no
  consolidation** (§5.6 / §7.2).

A convergence claim that only reports the agreeing part is the count-shaped-baseline
error in another costume. The convergence is on the hub-and-spokes shape. It is
**not** on what else each system needs around it.

---

## 11. What this document does NOT establish

Stated plainly, in the order a reviewer is most likely to need them.

1. **It does not establish that any of this improves any measured outcome.** Every
   claim in §7 is a mechanism claim. No number is attached to any of them, and §7.4
   exists because that gap is real.
2. **It does not establish that the §7.2 discriminator is correct for this
   substrate.** It is correct *for the psychological phenomena Myachykov et al.
   studied*, and it maps cleanly onto two mechanisms this tree has. Mapping cleanly
   is not evidence. No probe was run.
3. **It does not establish §7.2's ladder — the document's own headline.** The
   four-rung family, and specifically the claim that it lines up rung-for-rung with
   the sd loop's measured Occam ladder, is an **analogy I drew**: one of those
   ladders is gated and live, the other is a table in a document. Each rung is
   instantiated by a real example from §2/§7.3, and the MDL ordering argument (§9b)
   is genuine, but **nothing measures that a cross-domain pair actually falls on the
   rung the parameter predicts.** The falsifier is cheap and specific: find a domain
   pair that shares substantial structure and where a shared encoding nonetheless
   loses. §7.1's 261/502 is arguably that measurement pointing the *other* way
   (pools that looked structurally close and were not) — encouraging, and not the
   same as a test.
4. **It does not establish that §7.3's missing edge is buildable.** The whole design
   assumes a rotation matrix is expressible in the P1 Program-IR subset, and
   `RULE_SIGNATURE_TO_RUST_RESULTS.md` §1 is a documented case of exactly that
   assumption failing (`ComprehensionDict`, `DefFn`, `RecvMethod:append`,
   `CompTargetComplex` blockers on four of five functions). **§7.4's first
   measurement is a real risk of a clean NO-GO**, and I would run it before
   anything else.
5. **The literature is read at abstract-and-summary depth in five of nine cases.**
   Fully fetched and read: Mroczko-Wąsowicz & Nikolić 2014; Chiou & Rich 2014;
   Myachykov, Chapman & Fischer 2017; Schlimm 2008 (abstract + structured summary).
   Read only as consistent multi-source summaries: Ramachandran & Hubbard 2001 (both
   PDF mirrors failed to fetch), Dixon et al. 2000 (Nature and PubMed cookie walls),
   Walsh 2003, Boroditsky 2000, Baxter 2000. **The three papers doing the most work
   in my argument (§5.3, §5.5, §5.6) are split 2 fetched / 1 summarised**, and the
   summarised one is Boroditsky, whose finding 3 I have leaned on hardest.
6. **§6's null is a web-search null, not a literature review.** Three named limits
   are in that section. I would not defend "nobody has done this" against a
   librarian; I would defend "six targeted searches found only three well-defined
   other things."
7. **It does not measure the live graph.** Every count is cited from a landed results
   document or read from source. I booted no agent, in keeping with the spike
   constraint — which means §3.2's 190-edge figure, §7.1's 261/502, and §2.3's
   claims about what `TransferDecode` does at runtime are all inherited, not
   reproduced.
8. **It does not check whether `TransferDecode` has ever actually fired in
   production.** §2.3 establishes that it is built and shipped with two mechanisms.
   Whether the `space → rules` transfer its seed describes has ever run on real
   input, I did not verify — and given
   `RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.4's precedent (a capture harness whose output
   does not exist anywhere reachable), that is a question worth asking before
   building on it. **`[unverified]`, and it is the first thing I would check.**
9. **It does not include the agent's own view.** Same objection §12.7 of the rules
   spike raised against itself: the creator's methodology is that the *agent* designs
   from grounding, and every design judgement in §7 is mine. The agent holds acquired
   microtheories for both `synesthesia` and `amodal_perception` (§2.2) and has never
   been asked about either. Running this charter through `induce_concern` /
   `categorise_by_shape` would be cheaper and more faithful than anything in §7.4.

---

## 12. Sources

**Code and documents in this tree** (all read directly): `CLAUDE.md`;
`runners/dsl/src/term.rs` (:803, :812, :822, :838, :849, :860, :874, :888,
:1281-1351, :3347-3418, :3671, :3757-3785); `runners/dsl/src/strokes.rs`
(:1-31, :374, :411-425, :977); `runners/dsl/src/space_quantize.rs` (:1-45);
`runners/dsl/src/shape_decode.rs` (:389-445, :5281-5296);
`domains/analogical_thinking.py` (:388-506); `domains/rule_signature.py`;
`domains/prog_chunk_growth.py` (:137, :157); `seeds/cross_modal.json`;
`seeds/mechanism_index.json`; `seeds/shape_decode_loop.json`;
`scripts/jabberwock_cross_modal.py`;
`docs/research/engine_substrate/RULES_AS_SHAPE_DESIGN_SPIKE.md`;
`SHAPE_TYPE_VOCABULARY_SPIKE.md`; `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md`;
`RULE_SIGNATURE_TO_RUST_RESULTS.md`; `CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`;
`META_SHAPE_FIRST_CLASS_RESULTS.md`.

**Private research repo** (`ozmalabs/internal`,
`research/experiments/gamma-substrate/`): `docs/shape_math_grounding.md`;
`scripts/jabberwock_cross_modal.py`; `seeds/cross_modal.json`;
`scripts/multimodal_referential_video.py`; `scripts/jabberwock_multimodal_keyspace.py`;
`seeds/acquired/import_w00/american_synesthesia_association_microtheory.json`;
`seeds/acquired/import_w00/amodal_perception_microtheory.json`.

**Literature** (fetch status noted in §11.4):

- Ramachandran, V.S. & Hubbard, E.M. (2001). Synaesthesia — a window into perception, thought and language. *Journal of Consciousness Studies*. [sfu.ca mirror](https://www.sfu.ca/~kathleea/colour/docs/Ram&Hub_2001.pdf)
- Hubbard, E.M., Brang, D. & Ramachandran, V.S. (2011). The cross-activation theory at 10. *Journal of Neuropsychology*. [Wiley](https://bpspsychub.onlinelibrary.wiley.com/doi/abs/10.1111/j.1748-6653.2011.02014.x) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/21923784/)
- Dixon, M.J., Smilek, D., Cudahy, C. & Merikle, P.M. (2000). Five plus two equals yellow. *Nature* 406:365. [Nature](https://www.nature.com/articles/35019148) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/10935623/)
- Mroczko-Wąsowicz, A. & Nikolić, D. (2014). Semantic mechanisms may be responsible for developing synesthesia. *Frontiers in Human Neuroscience*. [Frontiers](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2014.00509/full)
- Chiou, R. & Rich, A.N. (2014). The role of conceptual knowledge in understanding synaesthesia: evaluating contemporary findings from a "hub-and-spokes" perspective. *Frontiers in Psychology*. [PMC3949133](https://pmc.ncbi.nlm.nih.gov/articles/PMC3949133/)
- Myachykov, A., Chapman, A.J. & Fischer, M.H. (2017). Cross-representational interactions: interface and overlap mechanisms. *Frontiers in Psychology* 7:2028. [PMC5209390](https://pmc.ncbi.nlm.nih.gov/articles/PMC5209390/)
- Walsh, V. (2003). A theory of magnitude: common cortical metrics of time, space and quantity. *Trends in Cognitive Sciences* 7:483-488. [Cell](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(03)00230-4) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/14585444/)
- Dehaene, S., Bossini, S. & Giraux, P. (1993), via [SNARC overview](https://en.wikipedia.org/wiki/Spatial-numerical_association_of_response_codes); counter-argument: [The SNARC effect does not imply a mental number line, *Cognition* 2008](https://www.sciencedirect.com/science/article/abs/pii/S0010027708000309); [Number, time and space are not singularly represented, *Psychon. Bull. Rev.* 2018](https://link.springer.com/article/10.3758/s13423-018-1561-3)
- Boroditsky, L. (2000). Metaphoric structuring: understanding time through spatial metaphors. *Cognition* 75:1-28. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0010027799000736) · [PDF](https://lingwistyka.pbworks.com/f/boroditsky.pdf)
- Schlimm, D. (2008). Two ways of analogy: extending the study of analogies to mathematical domains. *Philosophy of Science* 75(2):178-200. [Cambridge Core](https://www.cambridge.org/core/journals/philosophy-of-science/article/abs/two-ways-of-analogy-extending-the-study-of-analogies-to-mathematical-domains/D13B30CA376B7605EA859712EB481CB8)
- Baxter, J. (2000). A model of inductive bias learning. *JAIR* 12:149-198. [JAIR](https://jair.org/index.php/jair/article/view/10253) · [arXiv](https://arxiv.org/abs/1106.0245)
- Structure-mapping engine (Falkenhainer, Forbus & Gentner). [Overview](https://en.wikipedia.org/wiki/Structure_mapping_engine)
- §6 prior-art candidates: [Emergence of synaesthesia in a neuronal network model, *PLOS Comput. Biol.* 2016](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1004959); [A deep learning model of perception in color-letter synesthesia](https://www.researchgate.net/publication/345004644_A_Deep_Learning_Model_of_Perception_in_Color-Letter_Synesthesia); [Synesthesia of Machines (SoM), arXiv 2506.07647](https://arxiv.org/html/2506.07647v1); [Robot Synesthesia](https://www.emergentmind.com/topics/robot-synesthesia); [On AI Synesthesia (Sequoia)](https://sequoiacap.com/article/on-ai-synesthesia/)
- §9 convergent evolution: [What does convergent evolution mean? *PMC4633856*](https://pmc.ncbi.nlm.nih.gov/articles/PMC4633856/)
