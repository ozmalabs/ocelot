# SHAPE-BEARING NODE `kind` FIELD — DESIGN SPIKE, PREREG

**Status: PREREG. No code changes past this file. Predictions registered before the
decisive measurement is run.** Matching `RULE_SIGNATURE_SLICE_PREREG.md` and
`DIMGEN_PROGRAM_IR_PREREG.md`'s convention: falsifiable predictions first, then
`SHAPE_KIND_FIELD_RESULTS.md` measures and reports honestly, GO or NO-GO.

**Charter, verbatim, from the creator:** *"the other factor is also shape of shapes —
what type of thing is this thing."* Then: *"spike the kind field, do it."*

**Base:** `main` at `4bb1794` (`Merge dimgen-program-ir: DimensionGenerator <->
Program-IR, GO`), verified with `git log --oneline -1 main` before branching. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/shape-kind-field-spike`, branch
`shape-kind-field-spike`.

**What prompted this rung, precisely.** `SHAPE_TYPE_VOCABULARY_SPIKE.md` (committed
earlier in this arc, base `c439e4c`) proposed `{name, signature, support, provenance,
scope}` as the shared field set for shape-bearing nodes and explicitly has no `kind`
field. `DIMGEN_PROGRAM_IR_RESULTS.md` §5 item 6 (landed, commit `4bb1794`) named the gap
directly, from a live sharpening during that rung: *"a `DimensionGenerator` and a
Program IR root are both MAPs... that shared kind is why AR-1 was well-posed... Beyond
matching shape CONTENT, there is a second, orthogonal question: what CATEGORY of
shape-carrying thing a node IS,"* proposing the five-way split reproduced below, and
citing the private-repo `DOOR_SWITCH_RECOGNITION_RESULTS.md` precedent (coarse
family-match before fine label-match) as a possible mechanism analogue. It explicitly
deferred building anything: *"Not measured here, not built here."*

---

## 1. The working hypothesis under test

**H1 — the five-way kind split, as stated in `DIMGEN_PROGRAM_IR_RESULTS.md` §5 item 6:**

| kind | example node types | what characterises it |
|---|---|---|
| MAP | `DimensionGenerator`, `Transform`, `GammaProduction` | a function between frames/states; consumed downward via `Substitute`/application, not upward via `Covers` |
| OBJECT / IDENTITY | `Concept` | has a name and category but (per `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1) no relational/signature structure of its own to declare |
| RELATION-PATTERN | `ShapeSignature`, `MetaShape`, `ShapePrinciple` | a `signature` = list of relation tuples; consumed upward via `Covers`/`AntiUnify` as a recognizer |
| CODEBOOK | `CapabilityAxis` | a growable set of quanta; identity is a derived key over the covered predicate set, not a static signature |
| PROCEDURE | `Mechanism` | `steps` = an ORDERED token list, transferred via `TransferDecode`, not matched via `Covers` |

**Prediction P1:** reading the actual node-type definitions and seed data for these five
(plus any others with "shape" semantics found by a broad grep of `runners/dsl/src/*.rs`
and `seeds/*.json`) will either (a) confirm the five-way split holds with no
contradicting counter-example, (b) require a refinement (a sixth kind, a merge, or a
type that doesn't fit any of the five), or (c) show the split doesn't hold at all
(multiple types straddle categories in ways that make the split useless). I do not know
which in advance; all three are reportable outcomes.

**Prediction P1b (falsifiable, narrow):** the word `"kind"` is very likely ALREADY an
attribute name in live use on `ShapeSignature` (per `SHAPE_TYPE_VOCABULARY_SPIKE.md`
§3.4(a)/the corrected addendum) and possibly on `DimensionGenerator`
(`shape_decode.rs:389-396` documents a `kind` attr dispatching to a built-in generator
primitive, e.g. `"linear"`/`"rotation90"`/`"modular"`). If both are confirmed live, a
NEW `kind` field carrying MAP/OBJECT/RELATION-PATTERN/CODEBOOK/PROCEDURE semantics would
be a THIRD, incompatible meaning for the same attribute name on nodes that already use
it for something else — a naming collision worth flagging explicitly, not silently
overloading further.

---

## 2. The load-bearing question: would a `kind` field change any decision?

**H2 — there exists a live call site where `AntiUnifyWitness`/`Covers`/`AntiUnify`/
`StructSim` (`term.rs`) is invoked with two operands of genuinely mismatched category
(per H1's split), and today's code produces a WRONG or MEANINGLESS result (a nonzero
"match" with no real correspondence) rather than a clean refusal.**

Two candidate live sites, found by reading `domains/reflective_faculty.py` and
`domains/analogical_thinking.py` (not yet run against the native evaluator — that is
the decisive measurement):

**Site A — `learn_term_for_concern` (`domains/reflective_faculty.py:1074-1158`), the
CapabilityAxis-residual fallback path (`:1101-1113`).** When no held `Concept` names a
surfaced concern, the function falls back to a `CapabilityAxis` node's
`residual_predicates` attr, reshaped as `[[p] for p in preds]` — a CODEBOOK-kind node's
residual, in H1's terms — and hands it to `_shared_shape` (`:7137-7154`) to compare
against `ShapeSignature{kind:'faculty'}` nodes (RELATION-PATTERN-kind) from
`seeds/math_capability_shapes.json`, with **no kind check anywhere in the path**.

**Prediction P2a (falsifiable):** because `_shared_shape` truncates both signatures to
`min(len(a), len(b))` rows and feeds them to a bare `AntiUnify` Term, and because a
`CapabilityAxis`-residual row is always 1 element (`[p]`) while every seeded
`ShapeSignature{kind:'faculty'}` row is 2-4 elements (measured below in §3), the
per-row `AntiUnify` on the `Tuple`/`List` arm requires equal length and collapses to
WILD otherwise (`term.rs:3367-3375`, per `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.3's
table). **Prediction: `_shared_shape(cap_axis_residual, faculty_sig)` returns
`fixed == 0` for every real pairing** — i.e., the arity mismatch that is itself a
SYMPTOM of the two operands being different kinds already acts as an accidental,
unplanned guard, and a `kind` field would change nothing here because the current
behaviour is already a clean non-match.

**Site B — the same `_shared_shape`, called on two SAME-kind (both RELATION-PATTERN)
operands with no shared axis anchor.** `author_signature`
(`reflective_faculty.py:7112-7134`) builds a `Concept`'s signature by scanning a fixed
`RelationCue` lexicon (`seeds/relation_vocabulary.json`) in **seed-declaration order**
and appending each cue's relation tuple whose keyword fires — there is no vocabulary-
sorted axis anchor the way `analogical_thinking._concept_shape_vector` deliberately
builds one (`analogical_thinking.py:362-368`, `:388-411`). Two semantically unrelated
`Concept`s can therefore have their unrelated relation rows line up at the same list
INDEX purely by which cues fired in which order, and the shared placeholder tokens the
`RelationCue` vocabulary reuses across unrelated relations (`"NEW"`, `"SELF"`,
`"PART"`, `"to"`, `"by"`, ...) can produce a genuine but MEANINGLESS positional match.

**Prediction P2b (falsifiable):** a constructed pair of `author_signature`-shaped
vectors for two concepts with NO real shared structure, but with same-arity rows at the
same index, will produce `fixed > 0` from `_shared_shape` — a live, reproducible
nonsense match. **This, if confirmed, is evidence AGAINST H2 in its cross-kind form**
(both operands are the SAME kind under H1 — both RELATION-PATTERN) and FOR a different,
narrower defect (axis-anchoring / row-ordering) that a `kind` tag cannot fix, because
tagging both operands `RELATION-PATTERN` would not stop the comparison — it already
passes any conceivable kind guard.

**The registered decision rule:** if P2a confirms (clean refusal already exists at the
one live cross-kind site) AND P2b confirms (the live nonsense match found is same-kind,
not cross-kind), then **H2 is refuted in the form the charter asked me to test it in**
— there is no live site where a `kind` guard would change a wrong answer into a
refusal, because the one cross-kind site is already accidentally safe and the one real
defect is orthogonal to kind. That is a NO-GO on the specific slice (a `kind`-guard on
`AntiUnifyWitness`/`Covers`), reported as a complete, valuable null per `CLAUDE.md`'s
own standing instruction that a localised, generalised null outranks an unforced pass.

If instead a genuine cross-kind wrong-result IS found (P2a or a similar site refuted),
that is the live demonstration the charter asked for, and §3 of `SHAPE_KIND_FIELD_RESULTS.md`
proceeds to size the minimal guard.

---

## 3. Reproduce (predictions only; run in RESULTS)

```bash
cd /home/matt/ozmadev/ocelot-worktrees/shape-kind-field-spike
python3 -c "
import json
d = json.load(open('seeds/math_capability_shapes.json'))
for n in d.get('nodes', []):
    a = n['attrs']
    if a.get('kind') == 'faculty':
        sig = json.loads(a['signature'])
        print(a['name'], [len(r) for r in sig])
"
# P2a / P2b: the native-evaluator repro (AntiUnify + FixedCount over constructed
# CapabilityAxis-residual vs faculty-ShapeSignature, and Concept-vs-Concept, vectors)
python3 scripts/shape_kind_probe.py   # written for RESULTS, not yet present
```

---

## 4. GO / NO-GO bar, stated before measuring

- **GO** on building a `kind` field + one guard iff: a genuine cross-kind pairing (per
  H1's split) is found at a LIVE call site producing a wrong/meaningless nonzero match
  today, AND the guard (a `where`-clause or a Python-side kind check before the
  `AntiUnifyWitness`/`Covers`/`AntiUnify` call) demonstrably prevents exactly that
  match with no other behaviour change (paired before/after).
- **NO-GO** iff either (a) no live cross-kind wrong-result site is found (the sd-loop's
  existing node-type/`codebook_type` partition and/or an accidental arity guard already
  cover it), or (b) the only live nonsense-match found is same-kind and therefore not
  fixable by a `kind` tag at all.
- A **NO-GO is a complete, reportable result.** Per `CLAUDE.md`'s standing rule, a null
  that localises the cause and generalises the lesson outranks a forced pass.

---

## 5. Explicitly out of scope (restated from the task)

Retrofitting existing nodes wholesale with `kind`; any benchmark claim; any new Rust
Term; a full kind taxonomy/hierarchy beyond the flat five-ish candidates in H1 unless
concrete evidence says otherwise; forcing the `DOOR_SWITCH_RECOGNITION_RESULTS.md`
precedent to "transfer" if the actual mechanism (integer L1 distance over quantized
pixel descriptors, tiered by geometric proximity) doesn't match what a graph-node kind
tag would do (a symbolic equality/type check, no distance metric) — thematic
resonance ("cheap check before expensive check") is not the same claim as mechanism
transfer, and §2 of `SHAPE_KIND_FIELD_RESULTS.md` judges that honestly rather than
assuming it.
