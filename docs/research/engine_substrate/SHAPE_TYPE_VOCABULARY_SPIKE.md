# SHAPE-BEARING TYPE VOCABULARY — DESIGN SPIKE

**Status: SPIKE. No code, no seeds, no tests, no builds in this document.** Exactly one
file was added to the tree (this one). Matching
`docs/research/engine_substrate/decision_making_spike.md`'s status convention and
`RULES_AS_SHAPE_DESIGN_SPIKE.md`'s register: a first-person research journal, written
before any build, whose job is to make a design decision *legible and falsifiable*
rather than to make it.

**Charter, verbatim, from the creator:** *"in terms of shape matching, I think what we
need is a research spike into what edges and node types we should have. this wasnt
sufficiently planned."*

**Base:** `main` at `c439e4c` (`Merge rule-signature-production: structural fallback
wired for real, worst keywords_text site fixed`), verified with
`git log --oneline -1 main` before reading anything.

**Confidence convention**, following `RULES_AS_SHAPE_DESIGN_SPIKE.md`'s preamble:
claims I verified by reading source in this tree carry `file:line`. Claims I took from
another document in this tree carry that document's section number, and I say so rather
than restating them as my own. Claims I did not independently re-verify are marked
`[unverified]`. Derivations — things I concluded from source but did **not** execute —
are marked `[derived, not run]` and, where they are falsifiable, I name the exact test
that would refute them. **I ran no probe and executed no agent code**, per this rung's
constraint; every number below is either read from source, counted by a read-only
JSON/grep pass over `seeds/`, or cited from a landed results document.

**My one-line answer, up front, so a reader can stop here if that is all they want:**
today's ten-plus fixes **do** converge — on four fields and on one relation format — and
the convergence is real enough that I would not call this an ad-hoc pile. But the
convergence is *undeclared*, so nothing enforces it and three sites drifted off it; and
underneath the convergence sits a **genuinely forced split** in encoding that no shared
type can paper over, because `Covers` and `AntiUnify` have different, incompatible
semantics on `Set` versus `Tuple` versus `Dict` and each grain picked the container that
its own operator needed. So: **one vocabulary, two encodings, and the encoding choice is
derivable rather than arbitrary** — which is a much better position than "this wasn't
planned" implies, and a much worse position than "it's fine" implies, because the
derivation exists nowhere and has been re-derived, painfully, at least four times.

---

## 1. Method, and what I actually read

I read, in this order: `CLAUDE.md` in full (1,138 lines, including the
`SHAPE IS ACQUISITION, RULE IS EXECUTION` section at `:993-1138`);
`RULES_AS_SHAPE_DESIGN_SPIKE.md` (§§1-16 incl. both addenda);
`PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md`; `SHAPE_AUDIT.md`;
`RULE_SIGNATURE_SLICE_RESULTS.md` and `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`;
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md`; `SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md`;
`META_SHAPE_FIRST_CLASS_RESULTS.md`; `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md`; the
four Γ/rule-mirror docs (`GAMMA_REFLECTION_WIRING_RESULTS.md`,
`GAMMA_PYO3_REROUTE_RESULTS.md`, `GAMMA_LOAD_GROWTH_FIX_RESULTS.md`,
`IMPORT_RULES_NO_MIRROR_RESULTS.md`); and `BAICS_WORKSHOP_HARVEST.md`.

Then — and this is the part that changed the document — I read the **type mechanics**
themselves rather than only how they are used: `runners/dsl/src/graph.rs`,
`value.rs`, `sym.rs`, `grammar.rs`, `checker.rs`, `substrate.rs` (the four `add_*`
entry points), `reflect.rs`, `grammar_reflect.rs`, `graph_rules.rs`, `rewrite.rs`'s
effect layer, `term.rs`'s five shape-math operators and their three container arms, and
`shape_decode.rs`'s codebook loader. Plus the four Python signature functions
(`domains/rule_signature.py`, `domains/meta_shape.py`,
`domains/analogical_thinking.py`, and `induce_concern` in
`domains/reflective_faculty.py`).

The reading order matters because **§2 below is not in any of the documents**, and it
reframes the charter's question. I did not find it by reading the retrospective; I found
it by reading `graph.rs` and `checker.rs` back to back.

---

## 2. The foundational fact: this substrate has **half** a type system, and the defective half is the half with no schema

The charter asks "what node and edge types should we have." Before that can be answered
I had to establish what a node type and an edge type *are* here, structurally. The
answer is asymmetric, and the asymmetry predicts, almost perfectly, where every defect
in `SHAPE_AUDIT.md` lives.

### 2.1 A node type is a nominal string. There is no schema. Verified.

```rust
/// Per-node payload — type + Attrs.
#[derive(Clone, Debug)]
pub struct NodeData {
    pub type_: Sym,
    pub attrs: Attrs,
}
```
— `graph.rs:125-129`. `Sym` is an interned `u32` handle into a per-`Substrate` string
table (`sym.rs:19`, `sym.rs:33-37`). `Attrs` is `pub Vec<(Sym, Value)>` with linear-scan
lookup (`graph.rs:67-68`).

`Substrate::add_node` (`substrate.rs:1419-1435`) accepts any `type_: Sym` and any
`attrs: FxHashMap<Sym, Value>` and performs **no validation of any kind** — it bumps a
counter, optionally records the written keys for dirty-tracking, and calls
`graph.insert_node`. There is no declared-fields table, no required-attrs check, no
per-type constructor, no registry a type must be present in.

I searched for one specifically, because the charter told me to confirm this precisely
rather than assume it: `grep -rn "schema\|Schema\|required_attr\|declare_node_type\|
node_type_registry\|validate_node"` across `runners/dsl/src/*.rs` returns 20 hits, and I
read every one. None is a node schema. The two that look like it are not:

* `l2_graph_bridge.rs:71` `register_dispatcher_schema` — which turns out to be **three Γ
  productions**, not a node schema (`l2_graph_bridge.rs:90-104`). This is a real finding
  and I return to it in §2.2: when a Rust author in this tree reached for the word
  "schema," what they wrote was a grammar. Its own doc comment also records the dedup
  gap in passing — *"Idempotent-ish: re-calling will re-add the productions (the grammar
  accepts duplicates)"* (`l2_graph_bridge.rs:69-70`).
* `cognitive_tasks.rs:1949` — a comment (*"Task schemas are core runtime vocabulary"*)
  above an `add_edge` whose failure is handled by removing the orphan node. Again a Γ
  concern, not a node-shape concern.

**So: a node type is a name and nothing else. Two nodes of the same type need not share
a single attribute key.** This is the single most important fact for the charter,
because it means *"what node types should we have"* cannot be answered the way it would
be answered in a schema'd store. A node type here is not a contract; it is an index key
(`by_type`, `graph.rs:191`) and a rule-matching selector (`match_type`,
`graph_rules.rs:401-403`). Declaring `MetaShape{name, signature, support}` as "the type"
declares nothing the runtime will hold anyone to.

### 2.2 An **edge** type *is* schema'd, and Γ is the schema mechanism

```rust
if !self.grammar.knows_node_type(src_type) {
    return CheckOutcome::Type2VocabAbsent { missing: src_type };
}
if !self.grammar.knows_edge_type(edge_type) { ... }
if !self.grammar.knows_node_type(tgt_type) { ... }
let cand = self.grammar.candidates(src_type, edge_type, tgt_type);
if cand.is_empty() { return CheckOutcome::Type1NoProduction { ... }; }
```
— `checker.rs:66-85`. Every `Substrate::add_edge` (`substrate.rs:1437-1462`) routes
through this. The vocabulary `N ∪ E` is not declared anywhere separately: it is
**derived from the productions**, in `Grammar::add`:

```rust
pub fn add(&mut self, p: Production) -> ProdIdx {
    let key = (p.src.type_, p.edge_type, p.tgt.type_);
    let idx = ProdIdx(self.productions.len() as u32);
    self.node_types.insert(p.src.type_);
    self.node_types.insert(p.tgt.type_);
    self.edge_types.insert(p.edge_type);
    self.productions.push(p);
    self.index.entry(key).or_default().push(idx);
    idx
}
```
— `grammar.rs:71-80`. (Note in passing: this is a pure append with no equivalence check
— `SHAPE_AUDIT.md` §4.5's finding, confirmed here by direct reading. It is the same
absence §8 of this document is about.)

So the substrate's *actual* type system is: **a generative grammar over
`(src_type, edge_type, tgt_type)` triples, with an optional `where`-clause predicate on
the endpoints, gating every edge write.** That is a real, enforced, generative type
discipline — it is exactly the `Γ` half of the `(G, Γ, C)` foundation `CLAUDE.md`'s
SHAPES-NOT-NUMBERS section names as one of the two primitives new work must compose
with.

It is also, empirically, working: `META_SHAPE_FIRST_CLASS_RESULTS.md` §8 item 3 records
that the meta-shape rung's new edge was **rejected outright** until the seed declared
productions — *"`Γ rejects: type 'observed_shape' not in vocabulary (Type-2)`"* — and
correctly calls that *"a good failure — it is the admissibility grammar working."*

### 2.3 The consequence, measured

If the edge half is schema'd and the node-attribute half is not, then a defect
correlated with "shape held in an unchecked place" should concentrate in node
attributes. It does, overwhelmingly.

Reading `SHAPE_AUDIT.md`'s 40 confirmed sites for the type each involves: **roughly a
third involve no graph type at all** — `_EDIT_OPS` (§2.1 A4), the belief-attr pick (A5),
the `NATIVE_ORACLES` triple (§5.3), all eight §5.4 rows and most of §6 are Python
tables, constants and identifier strings that never entered the graph. Of the two
attributes carrying the largest share of the remainder, both are string bags standing in
for a structural signature: `keywords_text` (nine sites in §2.1 plus three more minters
in `domains/self_model.py`) and `capability_keys`/`Observation.key` (§3.1, feeding both
§2.6's operator pick and §2.1's Argmax).

**Not one of the 40 is a Type-1 or Type-2 admissibility failure.** The half with a
generative type discipline produced no findings; the half with none produced all of
them. I want to state that carefully, because it is nearly circular: the audit was
*looking for* string-where-structure-belongs, and Γ has no strings to look at. But the
non-circular version still holds and is the design-relevant one: **every place a "shape"
is currently carried, it is carried in an attribute, and attributes are the one part of
this substrate with no declaration mechanism whatsoever.**

A second measurement, over the seed corpus (read-only JSON pass over `seeds/*.json`,
893 dict-shaped manifests, 635 rule-carrying):

| quantity | count |
|---|---|
| distinct node types instantiated in seed `nodes` arrays | **354** |
| distinct edge types in seed `edges` arrays | 209 |
| Γ productions declared across all seeds | 1,572 |
| distinct node types appearing in some seed production (`N`, seed scope) | 708 |
| distinct edge types appearing in some seed production (`E`, seed scope) | 1,266 |
| distinct node types minted by rule `add_node*` effects | **427** |
| rule-effect mint sites using bare `add_node` | **1,011** |
| rule-effect mint sites using `add_node_if_absent` | **68 (6.3%)** |

The last two rows are §8's subject. The row worth pausing on here is 354 versus 427:
**more node types are minted at runtime by rules than are ever instantiated in a seed
manifest**, and the two sets are largely disjoint. Whatever "the right node types are"
is not a question about seed data; it is a question about what rules mint.

### 2.4 What this means for the charter's question

The charter asks what node and edge types we should have. Given §2.1-§2.3 the honest
reframing is:

* **"What edge types should we have"** is a well-posed question with an existing
  enforcement mechanism. An answer is a set of Γ productions, and the runtime will hold
  the tree to it. This is the *easy* half and it is largely not where the problem is.
* **"What node types should we have"** is, as literally posed, close to unanswerable
  here, because a node type carries no obligations. The answerable version is
  **"what fields must a node carry, and how does anything come to depend on that?"** —
  and since the runtime will not enforce it, the enforcement has to come from somewhere
  else: from a *reader* that fails loudly on a malformed node, or from a *declaration*
  the graph itself holds.

Both of those already exist in the tree, in exactly one place each, and neither is
generalised. That is §5.

---

## 3. The retrospective: what today actually built, as types

### 3.1 The running table

Every shape-bearing node type touched by the day's arc. "Signature field" is the attr the
shape math actually reads; "identity" is what decides two of these are the same thing.

| # | node type | signature field | encoding | identity / key | dedup on mint | the specific structural defect |
|---|---|---|---|---|---|---|
| 1 | `ShapeSignature` (+ 14 sibling types, §3.4) | `signature` | `Value::List` of relations, **or** a JSON string parsed at read | `name` (string) | at **read**: `by_name.insert`, last-write-wins, silent | `SHAPE_AUDIT.md` §3.1b: `grow_part_library` skips by *name*, so two differently-named parts with the same relation skeleton both install; the `covered_by` Argmax then tie-breaks arbitrarily, and each duplicate bumps `codebook_epoch` re-arming every decoded observation |
| 2 | `MetaShape` + `ShapePrinciple` | `signature` (WILD-bearing lgg), `keywords` | `Value::List` of 2-element `[pred, arg]` | `name` = `"ms_" + "_".join(sorted(pred set))` | rule guard: `Not Exists` a `MetaShape` with this name | *before today*: no signature at all, scored over `" ".join(attrs.values())` with keys and the node type discarded, ties broken alphabetically by the shape's own name — 44/55 pairwise contests (`META_SHAPE_FIRST_CLASS_RESULTS.md` §2.2). *After today*: fixed; the residual arity constraint is §3.3 |
| 3 | `CapabilityAxis` / `Observation` | `signature`; `key`/`capability_keys` | `Value::List` of relations; key is a `_`-joined string | `"induced_" + "_".join(preds[:3])` → now `sorted(preds)` untruncated | rule guard: `capability_keys == obs.key` equality | truncated at 3 **and** order-dependent → a genuinely novel observation routed to `sd_dedup_existing`, whose only effect is `status="recognized_duplicate"` — *a growth failure presenting as successful recognition*. Fixed today (`SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` §1). **A residual collision survives the fix — §7.2** |
| 4 | `RuleSummary` | `where_signature_json` (new today) | JSON **string** of a `FrozenSet` of path-addressed rows | `name` (not enforced — 2,208 nodes for 2,166 rule slots) | none; `ensure_where_signature` upgrades in place | the rule *body* was `rule_json`, an opaque string; selection was `Sum(StringIndexOf(keywords_text, w) >= 0)` over `name.replace("_"," ")`. Nine sites (`SHAPE_AUDIT.md` §2.1 A1-A9); two wired to the structural fallback today, seven still live |
| 5 | `Rule` (graph-resident) | `match`, `where`, `effect` | three attrs holding nested `Value` blobs | `id` string + `rule_uid` int | `import_rules` refuses a non-empty store | `where` is one nested `Value::Dict` under one attr key — *"There is no `Term.Exists` node, no `Term.Attr` node, no `child.predicate` edge"* (`RULES_AS_SHAPE_DESIGN_SPIKE.md` §2.1). **No graph mirror exists at all**: `Substrate::add_rule` (`substrate.rs:2480-2633`) never writes a node |
| 6 | `GammaProduction` / `GammaNodePattern` / `GammaGrammar` | `where_`/`weight` as real `Term.*` subgraphs | typed subgraph, `pattern.*` edges | **none — no content key at all** | **none** — `production_to_subgraph` mints fresh every call | unbounded checkpoint growth, +261 nodes/cycle, no convergence (`GAMMA_PYO3_REROUTE_RESULTS.md` §2.5). Fixed by *suppressing the mirror on the replay path*, not by canonicalising it |
| 7 | `Concept` | `name`, `category`, `definition` | scalars; `definition` is a `Term.*` subgraph | `name`, via an out-of-graph Python index | per-site Python find-or-create (today) | 10,775 nodes, **114 with any outgoing edge, 190 `Concept→Concept` edges total** (`ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1). Plus two duplicate-mint bugs, fixed today |
| 8 | chunk `Observation` / `ShapeSignature{kind:code_write_construction}` | `chunk_key`, `chunk_rels` | `chunk_key` = canonical JSON **string**; `chunk_rels` = flat **positional** list, `["ckstmt", i, label]` / `["ck", i, path, atom]` | `chunk_key` | Argmin survivor per pass | positional ⇒ row count is a function of statement count ⇒ *"two chunks with a different STATEMENT COUNT can never `Covers`-match, however similar their meaning"* (`PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` §1) |
| 9 | `Transform{dim,delta}` / `LatentDimension` | `dim`, `delta`; `name = "latent:<gen>"` | scalars | `name` | `Transform`: `has_transform` per-observation guard. `LatentDimension`: **the same guard, which is the wrong one** | `SHAPE_AUDIT.md` §4.4: the guard is a fixpoint-termination guard, not a dedup. A `Transform` genuinely is per-observation; a `LatentDimension` is a world-model fact, so N frames mint N byte-identical nodes |
| 10 | `SelfConcern` | `content` | free NL string | exact string equality | rule guard: `Not Exists` same `content` | `SHAPE_AUDIT.md` §3.2: exact string equality on natural language — two gaps expressing the same deficiency in different words are two gaps |

### 3.2 The four signature functions, side by side

Four independent functions compute a "signature" today. Three of them converged; one is
deliberately different. This is the clearest single view of whether the day was ad hoc.

| | `meta_shape.item_signature` | `analogical_thinking._concept_shape_vector` | `induce_concern`'s observation | `rule_signature.rule_signature` |
|---|---|---|---|---|
| source | `domains/meta_shape.py:60-79` | `domains/analogical_thinking.py:388-411` | `domains/reflective_faculty.py:1296` | `domains/rule_signature.py:113-170` |
| unit | `[predicate, value]` | `[axis:name, slots-or-ABSENT]` | `[predicate, value]` | `("rt", path, type)` / `("ra", path, field, atom)` |
| arity per row | **exactly 2** | **exactly 2** | 2 (caller-supplied) | **3 or 4 — mixed** |
| ordering | sorted by predicate | sorted, fixed positions | caller's | unordered |
| container | list | list, **fixed arity over the whole vocabulary**, `_ABSENT = "-"` filler | list | **`FrozenSet`** |
| stored as | native `Value` | in-memory only | native `Value` | **JSON string**, re-parsed on read |
| variable handling | n/a | n/a | n/a | **alpha-renamed positionally**, `?0`, `?1`, … |

Three of the four agree on a convention nobody wrote down as a convention:
**a relation is a 2-element `[predicate, value]` pair; a signature is those pairs sorted
by predicate.** And the agreement is *documented as inheritance*, not coincidence —
`meta_shape.py`'s module docstring explains why 2 elements
(*"`anti_unify_values` generalises element-wise only over EQUAL-LENGTH tuples, so
fixed-arity relations keep the predicate FIXED and wild only the value"*), and
`_concept_shape_vector`'s docstring cites `meta_shape.py` by name for exactly that
reason (`analogical_thinking.py:392-396`). That is convergence with a paper trail.

The fourth is different in every column, and the difference is principled: a rule's
`where` clause is a **tree**, so a flat 2-tuple cannot address it; it needs paths. But
the difference has a consequence nobody has stated, and it is the sharpest technical
finding in this document.

### 3.3 What the shape math actually operates on, and the container-semantics table

All five shape-math operators take `Value`, not subgraphs, not node ids, not Term trees:

```rust
pub(crate) fn anti_unify_values(vals: &[Value], wild: &Value) -> Value      // term.rs:3337
pub(crate) fn covers_value(pat: &Value, inst: &Value, wild: &Value) -> bool // term.rs:3738
fn struct_sim_value(a: &Value, b: &Value, wild: &Value) -> f64              // term.rs:3652
fn anti_unify_witness_values(vals: &[Value], wild: &Value)
    -> (Value, Vec<Vec<(Value, Value)>>)                                    // term.rs:3412
```

This has a consequence the retrospective documents circle but never state as one
sentence: **the graph-mirror direction and the shape-math direction are two different,
non-interoperating representations of the same object.** `term_to_subgraph`
(`reflect.rs:45-121`) produces `Term.<Variant>` nodes joined by `child.<field>` edges —
addressable, matchable by rules, and *completely invisible to `Covers`*, which cannot
read a subgraph. Conversely a `where_signature_json` `FrozenSet` is exactly what `Covers`
wants and is a single opaque attr as far as the graph is concerned.

So `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §5's verdict — build no `rule_reflect.rs`,
because *"the algebra runs on `Value` trees, not graph nodes"* — is not a scheduling
convenience. It is a type fact. **Any design that says "make the rule body an
addressable subgraph so the shape math can see it" is confused**, and I nearly wrote one
before reading `term.rs`.

Now the table that everything in §4 and §5 rests on. Read directly from
`term.rs:3337-3395` (`anti_unify_values`), `:3738-3766` (`covers_value`), and
`:3412-3500` (`anti_unify_witness_values`):

| container | `Covers(pattern, instance)` | `AntiUnify` / witness |
|---|---|---|
| `Dict` | pattern's keys must all be present and recursively covered; instance **may carry extra keys** (`:3744-3751`) | generalises over **shared keys only** — instance-only keys **vanish from both template and witness** (`:3345-3364`) |
| `Tuple` / `List` | **equal length required** (`pt.len() == it.len()`, `:3754`), then element-wise recursive | element-wise **only if all lengths equal**; otherwise the whole thing collapses to `WILD` (`:3367-3375`) |
| `Set` / `FrozenSet` | subset test, members compared with `==`, **no recursion into members** (`ps.iter().all(\|m\| is.iter().any(\|x\| x == m))`, `:3757-3763`) | **intersection** |
| scalar | equality | equality, else `WILD` |

Four properties a shape-bearing signature might want, and which containers give them:

| property | `Dict` | `Tuple` (fixed arity) | `Set` |
|---|---|---|---|
| **WILD slots** (a codebook of generalised patterns) | ✅ | ✅ | ❌ — a `WILD` inside a set member is just a different member |
| **residual capture** (what the mint path needs) | ❌ — shared-keys-only loses instance-only structure | ✅ (as witness at the WILD path) | ✅ (the set difference) |
| **length-free / open-arity** | ✅ | ❌ | ✅ |
| **stable per-path addressing** (what transfer needs) | ✅ | ✅ | ❌ |

**Every cell of that table was learned the hard way by a different rung, and the table
was never assembled.** `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §1.1 measured
exactly the top-left and middle-right cells live — encoding B (a marked SLOT row in a
set) fails because the set arm does not recurse; encoding C (a `Dict` of path→atom with
WILD) covers correctly but **loses the residual entirely**, so *"an sd loop on encoding C
would report zero residual for genuinely novel structure and `sd_mint_quantum` would
never fire."* `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` §1 measured the
`Tuple` equal-length cell at the chunk grain and called it the root cause of residual #8.
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §2.3 found the `Set` escape hatch and noted it had not
been named anywhere. And `analogical_thinking.py:362-368` states the fixed-arity
requirement in a docstring, for its own site only:

> *"Fixed arity and fixed position is what makes `AntiUnifyWitness` applicable at all: it
> generalises element-wise over EQUAL-LENGTH tuples. Two concepts laid out on the same
> axes are positionally aligned by construction."*

Read the table together and the design constraint falls out in one line, and I believe
this is the single most useful sentence in this document:

> **No single container gives you WILD slots *and* residual capture *and* open arity.
> `Set` gives residual and open arity but no WILD. `Dict` gives WILD and open arity but
> no residual. `Tuple` gives WILD and residual — and buys them by fixing the arity.**

That is not a defect in the engine. It is a genuine three-way trade, and it is why the
four signature functions of §3.2 differ. **They were not being inconsistent; they were
each paying a different one of the three prices**, and each one discovered the price
independently.

#### 3.3.1 A derived prediction about the meta-shape grain, and the test that would refute it

`META_SHAPE_FIRST_CLASS_RESULTS.md` §3(b) makes rung 1 at the meta-shape grain a
`Covers` test over WILD-bearing lgg patterns — verified in the seed:
`msg_recognize`'s `where` is `Covers(pattern=Attr(cms,"signature"),
instance=Attr(obs,"signature"))` (`seeds/meta_shape_growth.json`, rule `msg_recognize`).
Both operands are lists of `[pred, value]` pairs written from Python
(`meta_shape.item_signature`, `:60-79`), which cross the PyO3 boundary as `Value::List`.

Therefore they land on `covers_value`'s `Tuple | List` arm, and
`term.rs:3754` requires `pt.len() == it.len()`.

**Prediction `[derived, not run]`: a minted `MetaShape` whose signature has *k*
relations can only ever cover an observation with *exactly k* relations.** An item
carrying all *k* of the shape's relations *plus one more attribute* fails rung 1 and
falls through to the keyword prior. This is the same structural defect as
chunk-equivalence's residual #8, one grain over, in code that landed today.

The rung's own evidence does not test it: the near-variant that rung-1 recognised
(`TradeRecord{buyer:erin, seller:frank, lot:11}`, §4) has exactly the same four
predicates as the minted shape, so arity is held constant across every observation in
that probe.

**The test that would refute me in one line:** observe
`TradeRecord{buyer:x, seller:y, lot:n, note:"anything"}` after the mint and check
whether `msg_recognize` fires. If it does, I am wrong and I would want to know why. If
it does not, the fix is the §5 fixed-arity discipline or a move to `Set` at that grain,
and it is cheap either way. **I am flagging this rather than filing it, because I did not
run it**, and because a prediction I could have tested and didn't should not be dressed
as a finding.

### 3.4 Two divergences that are *not* principled

Everything above is a forced trade. These two are not, and they are the parts of the
current vocabulary I would actually change.

**(a) The codebook is partitioned two different ways at once.** `ShapeSignature` carries
a `kind` attr *and* there are separate node types for the same job. Counted over
`seeds/*.json`:

```
399  ShapeSignature            10  ShapeSignatureFineChild     3  ShapeSignatureThroughline
185  ShapeSignatureCoarse        8  ShapeSignatureCoherence     3  ShapeSignatureStoryBoundary
 44  ShapeSignatureMid           6  ShapeSignatureRegister      3  ShapeSignatureSemanticTrope
                                 6  ShapeSignatureNarrative     2  ShapeSignatureMetaTheme
                                 5  ShapeSignatureMeter         1  ShapeSignatureSpanningTheme
                                 4  ShapeSignatureFormat        3  ShapeSignatureTrope
```

(Counts are **node declarations** in seed `nodes` arrays, per §12's script. A raw
`grep '"type": "ShapeSignature"'` returns 403 instead of 399, because four hits are
inside rule bodies rather than node declarations — worth stating because the two numbers
differ and the grep is the more obvious thing to run.)

Fifteen node types, plus a `kind` attr, plus 87 seed sites naming
`"codebook_type": "ShapeSignature"` and ~30 more naming other types entirely
(`MetaShape`, `ConceptSignature`, `HumanoidBodyShapeSignature`, `XfSignature`,
`VdSignature`, …). The stated reason for at least one split is real —
`seeds/coherence_relations.json:5` says `ShapeSignatureCoherence` is *"kept in their OWN
codebook_type so they never compete with the clause-construction `ShapeSignature`
pool"* — and that is a legitimate need. But it is the **same need** `kind` exists to
serve, and the tree serves it both ways with nothing saying which to use when. This is
`SHAPE_AUDIT.md`'s sixth pattern (*"the same enumeration written twice, with nothing
deriving one from the other"*) applied to the codebook's own partition.

**(b) A `LatentDimension` is dedup'd by a guard designed for a `Transform`.**
`SHAPE_AUDIT.md` §4.4 states the distinction exactly right and I want to promote it,
because it is the general discriminator §8 needs: *"A `Transform` genuinely is
per-observation data. A `LatentDimension` is a world-model fact: `latent:rotation90` is
the same dimension whichever observation revealed it."* Two node types with genuinely
different **scopes**, sharing one guard.

---

## 4. Part 2 — do the shapes converge, or are they incompatible?

Both, and the split is clean enough to state as a verdict.

### 4.1 They converge on four fields, and the fifth is missing everywhere

Laying the ten types of §3.1 side by side, the fields that recur are:

1. **a name** — present on all ten. Universally the identity key, and in nine of ten it
   is *also* the human-readable label. (`GammaProduction` is the exception: it has
   neither.)
2. **a signature** — the structure the shape math reads. Present on 1, 2, 3, 4, 8; the
   thing whose absence *was* the defect on 2 (before today) and 5.
3. **a support count** — `MetaShape.support`, `ShapeSignature`'s mined `support`,
   chunk support (`support 166`, `support 142`). Present wherever the type can be
   *mined*; absent wherever it is only authored.
4. **provenance** — `GammaProduction.provenance`, `RuleSummary.from_seed`,
   `ShapeSignature`'s `concept`/`faculty` (read as one `source_val` at
   `shape_decode.rs:314-317`), `MetaShape.minted`.
5. **the missing fifth: a scope.** Nothing anywhere records whether a node is an
   observation-scoped datum or a world-model fact. That absence is §3.4(b)'s bug and
   §8.3's proposal.

So the answer to "is there already a coherent pattern" is **yes, four-fifths of one**,
arrived at independently, with the fifth field's absence being a live defect. I did not
expect this — I expected to find genuine incoherence — and the fact that
`{name, signature, support, provenance}` recurs at five grains built months apart is the
strongest evidence in this document that a shared vocabulary is the right call.

### 4.2 They do **not** converge on encoding, and cannot

Per §3.3, the encoding choice is forced by which of the three properties a grain needs:

| grain | needs | container it correctly chose |
|---|---|---|
| `ShapeSignature` (sd loop) | residual (to mint), open arity | list of relations — *and this is the one that pays the equal-length price without needing to* |
| `MetaShape` | WILD slots (codebook of lgg patterns), residual | `List` — fixed-arity by accident, §3.3.1 |
| concept vector | WILD slots + residual + paths (for the parallelogram) | fixed-arity `Tuple` with `_ABSENT` filler — **the only site that paid the price knowingly** |
| rule `where` | residual, open arity, coverage | `FrozenSet` of rows — **and therefore cannot carry a WILD**, which is exactly what `RULE_REFERENCE_LAYER_SIZING` §1.2 concluded when it ruled that *"a slot must be an ABSENCE, not a marked row"* |
| rule body, for transfer | per-path witnesses | the **raw nested `Dict`/`Tuple` rule JSON**, which is what RR4's parallelogram actually anti-unified over (paths like `where.a.items.0.key`) |

The last two rows are the same object in two encodings, and **neither subsumes the
other**: the `FrozenSet` gives coverage-with-residual and no paths; the raw tree gives
paths and loses the residual. That is not sloppiness. It is the `Dict`-vs-`Set` row of
§3.3's table, and a rule needs both operations.

### 4.3 The verdict, stated plainly

**A shared vocabulary is warranted at the level of fields, roles and identity discipline.
A shared *encoding* is not, and forcing one would break either the mint path or the
transfer path at every grain.**

This is the same shape as `RULES_AS_SHAPE_DESIGN_SPIKE.md` §9.3's finding about Rules
and Γ Productions — *"a different family, and the difference is directional, not
structural"* — one level down. There the discriminator was direction of travel through
the lattice (generate vs fire-on-match). Here it is **which of `Covers`' three container
arms the grain's own operation needs**. In both cases the correct answer is "unify the
vocabulary, keep the families apart," and in both cases the reason is mechanical rather
than aesthetic.

---

## 5. Part 3.1 — is there a general "shape-bearing" node interface?

### 5.1 What it can and cannot be, given §2.1

It cannot be a schema, because there is no schema mechanism and adding one is a change to
`insert_node`, the hottest write path in the substrate. It cannot be a Rust trait,
because these are graph nodes, not Rust structs.

What it *can* be is the thing the tree already invented once and used once. From
`shape_decode.rs:5093-5095`:

```rust
/// The ONE irreducible well-known anchor: the graph node-TYPE under which
/// codebook-type registry declarations are held. This is the single fixed
/// point — WHICH codebook node-type serves a given role is read FROM the graph
/// (a `CodebookRegistry` node's `node_type` attr), never a Term arg or Python
/// literal.
const CODEBOOK_REGISTRY_TYPE: &str = "CodebookRegistry";
```

That is a **graph-resident declaration that a node type plays a role**, resolved at
read time by `codebook_type_from_registry` (`shape_decode.rs:5100-5122`). It ships in
exactly one seed (`seeds/mechanism_index.json:13`) and serves exactly one role
(`"mechanism_transfer"`).

**This is the general mechanism, already built, at 1/40th of its natural scope.** I did
not go looking for it; it was in the file I read for `ShapeSignature`'s layout.

### 5.2 The proposal: conformance as a declared role, not a type

The shape-bearing "interface" should be a `CodebookRegistry`-style declaration that says,
for a node type: *which attr carries the signature, what encoding it is in, what the
identity key is, and what its scope is.* Something of the form:

```
ShapeRole{ role: "sd_codebook", node_type: "ShapeSignature",
           signature_attr: "signature", encoding: "relation_list",
           key: "name", scope: "world_fact", support_attr: "support" }
```

Three properties make this the right shape for *this* substrate specifically, and I want
to be explicit that they are the argument — I am not proposing it because declarations
are tidy:

1. **It is graph data, so the agent can read it, vary it, and repair it.** `CLAUDE.md`'s
   *"self-repair ⟺ graph-native"* boundary applies directly: a vocabulary encoded as a
   Python convention is in the blind spot; one encoded as nodes is not.
2. **It replaces a Term argument with a graph read**, which is the move
   `shape_decode.rs` already made once and documented as the reason
   (*"never a Term arg or Python literal"*). `ShapeDecode`'s `codebook_type` argument
   and the fifteen `ShapeSignature*` types of §3.4(a) both become declarations rather
   than literals.
3. **It is enforceable by the reader, which is where enforcement can actually live.**
   `load_parts` already panics loudly on a malformed node — and the panic text was
   improved *this month* precisely because a bare panic could not be acted on:
   `shape_decode.rs:289-295` records that *"it took two crashed 145-trial runs and two
   checkpoint scans to fail to identify the offender."* A declaration gives that check a
   spec to check against instead of a hardcoded field list.

### 5.3 The five fields, and what each means

| field | meaning | precedent it generalises |
|---|---|---|
| `signature_attr` | which attr the shape math reads | `load_parts`' hardcoded `"signature"` (`shape_decode.rs:259`) |
| `encoding` | which of §3.3's three containers, so a reader knows whether WILD/residual/paths are available | today: guessed from the `Value` variant at read (`shape_decode.rs:280-309`) |
| `key` | the identity discipline (§7) | today: `name`, everywhere, unstated |
| `scope` | `observation` vs `world_fact` (§8.3) | today: absent — the `LatentDimension` bug |
| `support_attr` | where the mined-recurrence count lives, if the grain can be mined | `MetaShape.support`, mined `ShapeSignature.support` |

`name` and `provenance` do not need declaring; they are already universal and already
read positionally.

### 5.4 Where a shared interface would be **wrong**

Following §9.3's discipline of naming the cases that should stay apart:

* **`Rule` should not be made to conform.** Its `where` needs *two* encodings
  simultaneously (§4.2) and the interface above assumes one `signature_attr`. A rule's
  correct shape-bearing form is a `RuleSummary`-side `where_signature_json`
  (`FrozenSet`, for coverage/mint) **plus** the raw body (`Dict`, for transfer), and
  declaring one of them "the" signature would silently disable the other. If a
  declaration is ever wanted here it needs a *list* of roles, which is a bigger design.
* **`GammaProduction` should not be made to conform, for §9.3's reason.** It is a
  constructor, consumed downward via `Substitute`; the interface above is written for
  recognisers consumed upward via `Covers`. The spike's own §11.1 item 5 already ruled
  unifying Rules and Productions out of scope and I am not reopening it.
* **`Concept` should not be made to conform**, because §6 shows it has no signature to
  declare — and manufacturing one for conformance's sake is exactly the "no-op wearing
  the costume of a fix" `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1 warns about.

So the interface covers grain-level codebooks — `ShapeSignature` and its fifteen
siblings, `MetaShape`, `CapabilityAxis`, chunk entries, stroke quanta, `SpaceQuantum` —
and stops there. **That is six to eight populations, not everything.**

---

## 6. Part 3.2 — what edge types are missing?

### 6.1 The `Concept` graph, and why "add the edges" is the wrong answer

The charter asks what edge types would make `Concept`-to-`Concept` relational reasoning
work, given 190 edges across 10,775 nodes. Having read the rung that measured it, I think
the question as posed has a *measured* negative answer and the rung deserves to have it
restated rather than re-litigated. `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1:

> *"`SHAPE_AUDIT.md` §2.4's charge — 'never consults a concept's edges' — is a **correct
> diagnosis of the code and a dead end as a prescription.** 98.9% of the population has
> no edge to consult. Building relational alignment here would be a no-op wearing the
> costume of a fix. **Saying so is the result.**"*

What that rung did instead is the answer to the charter's question, and it is a better
one: it built a **derived signature** (`_concept_shape_vector`, `analogical_thinking.py:
388-411`) — a fixed-arity vector over the held `FunctionalRole`/`ShapePrinciple`/
`MetaShape` vocabulary, where each cell records *which slot of the concept evidenced this
axis*. That is a relational structure computed from what the concepts actually carry
(name, category, definition) rather than from edges that do not exist. And it worked:
8,575 claims → 321, with 78 corroborated by a shared witness across pairs.

**The generalisable lesson for a type-vocabulary spike: a missing edge type is sometimes
better answered by a derived signature than by an authored edge**, because a signature
can be computed for 10,775 nodes and an edge has to be put there by someone. I would not
have predicted this and I think it is the most important thing §6 has to say.

### 6.2 The edges that *are* worth adding, and by what mechanism

Two families, and only two, survive that test.

**(a) The shape-attachment edges — `Rule → ShapeSignature`.** These are the four
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §6.2 already proposed (`match_shape` / `where_shape` /
`effect_shape` / `binding`, plus a `Binding{role, value}` node). I have nothing to add to
that design except one correction it has already received by measurement: its
accompanying `SLOT`-row notation is **wrong** and was measured wrong —
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §1.1 encoding B, because
`covers_value`'s set arm does not recurse into members (`term.rs:3757-3763`). The
corrected form is §1.2's: *"A slot must be an ABSENCE, not a marked row… CLAUDE.md's own
'unknown = absence, first-class' principle arriving from the other direction."* Anyone
picking up §6.2 should take the vocabulary table and drop the `SLOT` rows.

Worth stating plainly: **the vocabulary the charter asks for partly exists already**, in
§6.2, and it is small (one new node type, four new edge types). This document's job at
that point is not to invent a second one but to say which parts of it survived contact
with measurement. The vocabulary survived; the row grammar's `SLOT` did not.

**(b) A `covered_by` / `recognised_as` edge, at every grain, uniformly.** Today the
outcome of a decode is written as an *attribute* (`covered_by`, `status`), not an edge.
That is why `META_SHAPE_FIRST_CLASS_RESULTS.md` §5 could only report consumer effects by
re-running readers, and why the mined-shape population cannot be queried by "what does
this shape explain?" without a scan. Making it an edge costs one Γ production per grain
and makes recognition history a first-class, traversable relation — and per §2.2, the
production *is* the declaration, so the vocabulary gets checked for free.

I am deliberately not proposing `Concept → Concept` semantic edges (`is_a`,
`part_of`, …). The measured population says they would have to be *mined*, the mining
mechanism would be the sd loop over `_concept_shape_vector`s, and that is a rung with its
own hypothesis and its own oracle — not a vocabulary decision.

---

## 7. Part 3.3 — how should identity and keying work?

### 7.1 Four schemes in use

| scheme | where | property |
|---|---|---|
| bare `name`, author-supplied | `ShapeSignature`, `Concept`, `RuleSummary`, `SelfProcess` | no collision handling at all; `RuleSummary` is measurably over-complete (2,208 nodes / 2,166 rule slots) |
| derived string join | `CapabilityAxis` (`"induced_" + "_".join(...)`), `MetaShape` (`"ms_" + ...`) | canonical after today's fixes — **but see §7.2** |
| content hash | `Substrate::rule_content_hash` | all-or-nothing: *"two rules that differ in one literal hash completely differently"* (spike §2.2) |
| structural equality | `AddNodeIfAbsent`'s attr-subset scan (`rewrite.rs:1693-1740`) | the only *structural* identity in the tree |

### 7.2 A collision that survives today's `CapabilityAxis` fix — reported, not filed

`SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` §1 fixed the key to
`"induced_" + "_".join(sorted(preds))` — sorted and untruncated, which correctly closes
both of the audit's two failure directions.

**The separator is still ambiguous, because predicates contain `_`.** Two different
predicate multisets can join to the same key:

```
sorted(["a_b", "c"])  ->  "induced_a_b_c"
sorted(["a", "b_c"])  ->  "induced_a_b_c"
```

This is not hypothetical about the alphabet: predicates in this tree *are* snake_case
attribute keys. `meta_shape.py`'s own docstring example uses `multiplier_factor`
(`domains/meta_shape.py:66`), and `induce_concern` takes predicates straight from the
observation's relation heads (`reflective_faculty.py:1297`).

Consequence: it is the audit's **failure direction 2** — the dangerous one — surviving
its own fix in a narrower form. A colliding pair routes to `sd_dedup_existing`, whose
only effect is `status = "recognized_duplicate"`, i.e. a novel observation silently
recorded as recognised.

**Honest scoping, because this is exactly the shape of claim `CLAUDE.md` says to
condition:** the mechanism is arithmetic and I am confident in it. The *prevalence* is
unmeasured — I did not count how often two live observations' predicate multisets
collide under `_`-joining, and it may well be zero. `[derived, not run]`. The audit
itself flagged prevalence as unmeasured for the original bug and the fix rung did not
change that (`SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` §6).

**What it argues for generally:** a derived string key is a *lossy encoding of a
structural key*, and every lossy encoding needs an escape or a separator that cannot
occur in the payload. The tree already has the non-lossy version two files away —
`build_candidate` sorts both sides with `cmp_value` and compares relation **sets**
(`shape_decode.rs:1581-1595`), and `AddNodeIfAbsent` compares attrs structurally. The
string key exists because a rule guard needed an `Eq`-able scalar, which is a real
constraint, not a lazy one.

### 7.3 The general rule, and where it genuinely varies

**One rule holds everywhere:** *if identity is a derived string, it must be canonically
ordered, untruncated, and built with a separator that cannot appear in a component.*
Two-thirds of that is today's fix; the third is §7.2.

**But the choice of key genuinely varies by grain, and it varies with `scope`:**

* A **world-model fact** (a `LatentDimension`, a minted `MetaShape`, a codebook entry)
  should be keyed **structurally** — by its signature, not by a name — because two
  independently-discovered nodes with the same structure *are* the same fact. This is
  `SHAPE_AUDIT.md` §3.1b's finding: `ShapeSignature` keyed by name is why two
  differently-named parts with the same relation skeleton both install.
* An **observation-scoped datum** (a `Transform`, an `Observation`) should be keyed by
  its *occasion*, not its content, because two identical transforms observed at
  different times are two events.
* An **authored artefact** (a `Rule`, a seed-shipped `Concept`) is correctly keyed by
  name, because the name is a human-facing handle with independent meaning, and
  structural dedup would merge things an author deliberately kept apart.

That three-way split is the same `scope` field §5.3 proposes, arriving from the other
direction — which is the main reason I believe it is real rather than invented.

---

## 8. Part 3.4 — dedup on mint

### 8.1 Four occurrences of one absence, four site-local patches, zero shared primitive

Reading the four Γ/rule-mirror documents plus the Pattern-C fixes end to end, the
pattern is unmistakable:

| occurrence | patch |
|---|---|
| `GammaProduction` mirror re-minted on every checkpoint replay (+261 nodes/cycle) | `add_production_no_mirror` — **suppress the mirror on one caller**. Content-dedup was explicitly evaluated and rejected: *"more machinery than the problem needs"* (`GAMMA_LOAD_GROWTH_FIX_RESULTS.md` §1 candidate b) |
| mirror nodes corrupting `detect_god_object`'s population statistic | a module-level `_GAMMA_MIRROR_TYPES` **type-name exclusion list** |
| `learn_word` / `learn_recursive_concept` minting duplicate `Concept`s | **per-site Python find-or-create**, twice, differently |
| `CapabilityAxis` key collisions | **fix the key computation** at the one writing site |

Four sites, four mechanisms, nothing shared. And a fifth is queued: `Substrate::add_rule`
(`substrate.rs:2480-2633`) writes no graph node today, so there is nothing to dedup yet
— which is why `IMPORT_RULES_NO_MIRROR_RESULTS.md` landed a **source comment** rather
than code, saying that when a rule mirror is built it must be split from the replay path
*pre-emptively*, because Rules have one call layer where Γ had two.

### 8.2 The primitive exists. It is at exactly one layer.

```rust
// Scan the typed-node index for the first existing node
// whose attrs include EVERY (k, v) pair we're about to
// insert. Subset semantics: existing nodes may carry
// additional attrs the AddNodeIfAbsent author didn't
// mention; the author's attrs ARE the dedup key.
```
— `rewrite.rs:1701-1706`, implementation at `:1693-1740`, parser at
`graph_rules.rs:261-277`.

This is a real, structural, find-or-create with a declared key. It is available **only in
the rule-effect layer**. It is not available in `Substrate::add_node`, not in
`term_to_subgraph`, not in `production_to_subgraph`, not in `add_rule`, not in
`load_seed_manifest`, and not in any Python world adapter — which is to say, it is
absent from all four sites where the four defects occurred.

Adoption, measured over `seeds/*.json`:

| | count |
|---|---|
| rule-effect mint sites using bare `add_node` | **1,011** |
| rule-effect mint sites using `add_node_if_absent` | **68 (6.3%)** |
| node types minted *only* via bare `add_node` | 389 |
| node types minted via `add_node_if_absent` | 38 |
| node types minted **both** ways | **7** |

The last row is the interesting one: seven node types are minted with dedup in some rules
and without it in others. `[unverified]` whether any of those seven is a live duplicate
source — I counted the seeds, I did not boot an agent.

### 8.3 The discriminator that decides whether dedup applies at all

`SHAPE_AUDIT.md` §4.4's `Transform`-vs-`LatentDimension` distinction, promoted to a
general rule:

> **Dedup-on-mint is correct exactly when the node is a world-model fact, and wrong when
> it is an observation-scoped datum.** A `Transform{dim, delta}` observed twice is two
> events; a `LatentDimension{name:"latent:rotation90"}` discovered twice is one
> dimension.

This is the `scope` field of §5.3, and it explains why a blanket "dedup everything"
policy would be as wrong as today's "dedup nothing": both of the current failure
directions — duplicate world facts, and fixpoint-termination guards mistaken for dedup —
are the same missing distinction, seen from two sides.

### 8.4 What I would propose, and what I would not

**Propose:** make `scope` a declared field (§5.3) and give the *mint* path a uniform
find-or-create keyed by the declared `key`, exactly as `AddNodeIfAbsent` already does for
attrs. Concretely, one new effect variant or one flag, plus the declaration — the
mechanism is written; what is missing is that it is reachable from one layer only.

**Would not propose:** hash-consing `TermArena::add` (`term.rs:2244-2248` — three lines,
a pure `push`). The spike's §11.1 item 1 already ruled it out on the correct grounds
(`TermIdx` identity semantics are assumed by `ShapeCache` and `copy_subtree`), and
nothing I read changes that. The Γ-mirror explosion is not caused by arena duplication;
it is caused by `term_to_subgraph` (`reflect.rs:45-121`) calling `insert_node`
unconditionally, which is a *graph*-level absence and can be fixed at the graph level
without touching arena identity at all.

---

## 9. Part 3.5 — where "hold open" fits in a type design

`RULES_AS_SHAPE_DESIGN_SPIKE.md` §16.2 already derived the criterion, from two
independent vision-rung corrections, and I am not going to improve on it:

> *hold multiple representations open only when the correct resolution genuinely depends
> on information not yet available at decision time, AND the thing being modeled is not
> itself something that provably commits immediately.*

The charter asks what that implies *structurally*. Three observations.

**(a) The current vocabulary is one-canonical-form-per-shape, and the commitment is at
mint.** A minted `MetaShape` has one `signature`; a `ShapeSignature` has one; a chunk has
one `chunk_key`. §16.1's diagnosis of why chunk-equivalence found zero payoff — *"that
rung tested one rewrite, once, in isolation, hashed the result, and checked for a
coincidental match"* — is a direct consequence of that commitment.

**(b) An e-class-shaped alternative would be a *new node type and one new edge type*,
and no change to any existing one.** Structurally: a grouping node (call it a
`ShapeClass`) holding zero fields of its own, with `member` edges to N candidate
signature nodes, one flagged canonical. The sd loop's rules would decode against the
class's canonical member and the mint path would attach a new member rather than a new
class when the residual is explained by an *equivalence* rather than a novelty. That is
additive: existing single-signature nodes are the degenerate one-member case.

**(c) Two of the ingredients already exist, which is why I think this is worth naming
rather than dismissing.** `support` is already a per-entry count, and `codebook_epoch`
already re-arms every decoded observation when the codebook grows
(`seeds/shape_decode_loop.json`'s `codebook_epoch`; `meta_shape.py:53` deliberately
gives the meta-shape grain its own `meta_codebook_epoch` to avoid cross-grain churn).
**Epoch-triggered re-decode is the substrate's existing equivalent of e-graph
re-saturation** — a later mint causing earlier observations to be re-examined is exactly
SEER's *"one rewrite's discovery unlocking a different representation's opportunity."*
The tree has the loop; what it lacks is the ability for a re-decode to conclude
"these two held entries are the same shape" rather than only "this observation now
matches."

**Whether to build it is an empirical question per corpus, exactly as §16.2 says, and
this document does not resolve it.** I note only that the *type* change is small and
additive, which is not what I expected before working it through, and that it should not
be conflated with the vocabulary work — the vocabulary is worth doing whether or not the
e-graph question ever gets a yes.

---

## 10. Part 4 — sizing, honestly

### 10.1 Foundational migration, or incremental? Incremental — and the reason is structural, not optimistic

I expected to conclude "foundational." The reason it is not is §2.1: **because a node
type carries no obligations, adding a declaration cannot break a node that does not
conform.** A `ShapeRole` node that nothing reads is inert. A reader that consults it
falls back to today's hardcoded field names when no declaration is present — which is
precisely how `codebook_type_from_registry` already behaves: *"`None` when no registry
(or no mechanism-transfer entry) is held — the no-op: default boot names no codebook
type, so nothing transfers"* (`shape_decode.rs:5104-5107`).

That is the whole argument for incrementality, and it is the same argument
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §11.1 item 4 made for not retrofitting seeds: *"A design
that requires rewriting every seed is a design that will not land."*

Two things are genuinely *not* incremental and I want them separated out:

* **`scope` + uniform mint dedup (§8.4)** changes node counts. Per §2.3 that is the
  hazard class with a measured precedent: `GAMMA_PYO3_REROUTE_RESULTS.md` §2.4's
  `detect_god_object` corruption, and `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §2.2's
  190 at-risk files. Any rung touching mint counts owes the same enumerated at-risk list
  those rungs produced.
* **Anything that moves a signature computation from Python into Rust.** Three of the
  four signature functions of §3.2 are Python. `rule_signature.py` is explicitly
  measurement-only (its own docstring: *"MEASUREMENT / INVESTIGATION CODE, not agent
  decision logic"*), but `where_signature_json` is now read by production selection
  (`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` Part 1). **Under `CLAUDE.md`'s
  architecture rule, a signature the agent's own decisions depend on wants to be a Rust
  Term, and it is not one.** I flag this as the largest unpriced item in the whole arc —
  not as a violation today (computing a signature is arguably mechanical translation,
  and the *decision* is a graph-resident Term), but as the thing that makes the
  signature un-self-repairable, which is the payoff the migration exists for.

### 10.2 Rough cost, by piece

| piece | files | rough size | risk |
|---|---|---|---|
| `ShapeRole` declaration + reader in `load_parts` | `shape_decode.rs`, one seed | ~60 Rust lines, generalising `codebook_type_from_registry` | low — inert without a declaration |
| collapse the 15 `ShapeSignature*` types onto `kind` + declarations | ~15 seeds, `shape_decode.rs` | mechanical but broad | **medium-high** — every `codebook_type` literal is a live reference; needs an enumerated at-risk list first |
| `scope` field + uniform mint dedup | `rewrite.rs` or `graph_rules.rs`, seeds | ~80 Rust lines + per-grain seed edits | **high** — changes node counts, 190-file precedent |
| `recognised_as` edges + their Γ productions | seeds only | ~1 production per grain | low — Γ rejects loudly if wrong |
| §7.2 separator fix | `reflective_faculty.py`, one line | trivial | low, but **changes every derived key's string value**, as today's fix already did |
| move a signature computation to a Rust Term | `term.rs`, `jsonio.rs`, `reflect.rs`, `term_variants.rs` | a language-extension rung | **high** — and `NUM_TERM_VARIANTS` is a hard array length (`term_variants.rs:15`; `META_SHAPE_FIRST_CLASS_RESULTS.md` §8 item 2) |

### 10.3 The smallest slice that tests whether a shared vocabulary is right

Mirroring §11.2's discipline: state the hypothesis in one sentence and build only what
tests it.

**The hypothesis: a grain-agnostic reader driven by a graph-resident declaration behaves
identically to today's hardcoded readers, and makes at least one currently-impossible
question askable.**

The slice:

* **Build only** the `ShapeRole` declaration and teach `load_parts` to consult it,
  falling back to today's hardcoded `name`/`signature`/`kind`/`concept`/`faculty`/
  `dim_types` when absent — i.e. exactly the `codebook_type_from_registry` pattern,
  one level in.
* **Declare exactly two grains**: `ShapeSignature` (the 399-node default) and
  `ShapeSignatureCoherence` (the 8-node one that exists *specifically* to avoid pool
  collision, `seeds/coherence_relations.json:5`). Two, because one proves nothing about
  grain-agnosticism and fifteen is a migration.
* **Measure one thing, byte-for-byte**: that every existing decode produces an identical
  verdict with the declaration present and absent. This is the `META_SHAPE_FIRST_CLASS`
  §5 discipline — read the consumers before and after and require identity.
* **Then measure the one new thing**: can a rule now ask "which codebook does this
  node belong to" without a hardcoded type literal? If yes, the declaration bought
  something; if the answer is only "the same as before, with more indirection," the
  vocabulary is not worth generalising and this document's §5 should be dropped.

That is a few dozen lines of Rust, additive, with a byte-identity gate — and it produces
the one fact nobody has: **whether grain-agnosticism is real or whether `load_parts`
being "grain-agnostic" (`META_SHAPE_FIRST_CLASS_RESULTS.md` §3, confirmed by reading) is
grain-agnostic only across grains that happen to share field names.**

**A second, independent, cheaper slice I would run first if I could only run one:** the
§3.3.1 arity test. One observation, one assertion, no build. It either confirms a live
defect in code that landed today or removes a claim from this document. Cost is minutes;
information is high either way; and per `CLAUDE.md`'s standing rule about powered gates,
a single deterministic structural test *is* adequately powered because the mechanism is
deterministic — this is not an effect-size question.

### 10.4 Explicitly out of scope

1. **Hash-consing `TermArena`.** §8.4; already ruled out by spike §11.1 item 1 on
   grounds nothing here changes.
2. **A node-attribute schema in `insert_node`.** §2.1. It is the hottest write path;
   the enforcement point that is actually available is the *reader* (§5.2 property 3),
   and using it costs nothing on the write side.
3. **Making Rules conform to the shape-bearing interface.** §5.4 — a rule needs two
   encodings and the interface assumes one.
4. **Unifying Rules and Γ Productions.** §9.3's verdict stands; reopening it here would
   double the blast radius for no test-of-hypothesis value.
5. **Authoring `Concept → Concept` semantic edges.** §6.1. The measured population says
   they must be mined, and mining is its own rung with its own oracle.
6. **The e-graph / hold-open build.** §9. The criterion exists; the empirical question it
   gates does not have an answer, and §16.2 is explicit that it is per-corpus.
7. **Any claim that this improves a benchmark.** Per `CLAUDE.md`'s standing rule
   (*"synthetic-proven mechanism ≠ benchmark value, report both"*), every claim in §5-§9
   is a mechanism claim with no number attached, and §11 below says so again.

---

## 11. What this document does NOT establish

Stated plainly, in the order a reviewer is most likely to need them.

1. **It does not establish that a shared vocabulary improves any measured outcome.**
   §4.1's four-field convergence is an observation about five populations; it is not
   evidence that declaring the convergence changes any verdict. §10.3 exists because that
   gap is real.
2. **§3.3.1's arity prediction is derived from source, not run.** I read
   `covers_value`'s `Tuple` arm and traced the operands' provenance; I did not observe a
   5-relation item failing to match a 4-relation minted shape. If someone runs it and it
   passes, the corresponding paragraph should be struck, not softened.
3. **§7.2's separator collision is arithmetic, but its prevalence is unmeasured** — and
   may be zero on live data. I did not count colliding predicate multisets. This is the
   same limit `SHAPE_AUDIT.md` §3.1 and the fix rung both recorded for the original bug.
4. **I did not boot an agent or run a single probe.** Every count in §2.3 and §8.2 is a
   read-only pass over `seeds/*.json` on `main` at `c439e4c`. Live populations differ
   from seed populations, sometimes by a lot — `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`
   §2.4 measured the storage profile overstating the live rule population by ~22×, and
   nothing here is immune to that.
5. **The 354/427/708 vocabulary counts are seed-scope only.** Γ's `N` and `E` are
   populated at runtime from every production the substrate ever sees, including ones
   declared in Rust (`register_dispatcher_schema` and its kin) and by
   `declare_*` PyO3 calls. My "257 seed node types not in a seed production" observation
   is therefore **not** a claim that 257 types would be rejected at runtime, and I have
   deliberately not stated it as one.
6. **It does not establish that `load_parts` is grain-agnostic in the strong sense.**
   `META_SHAPE_FIRST_CLASS_RESULTS.md` §3 established it by reading, for one new grain
   that shares its field names. Whether it is agnostic across grains that *don't* is the
   thing §10.3's slice is designed to find out, and I am not assuming the answer.
7. **It does not include the agent's own view.** `RULES_AS_SHAPE_DESIGN_SPIKE.md` §12
   item 7 made this criticism of itself and it applies here verbatim: the creator's own
   methodology is that *the agent* should design from grounding, and every design
   judgement in §5-§9 is mine. `seeds/question_targets.json` routes "what shape are you"
   to the agent's own `self_shape` faculty; asking it "how are your codebooks organised"
   with §3.1's table as the framing would be a cheaper and more faithful next step than
   anything I have proposed.
8. **It does not re-verify the external literature.** DeepGAR's Tiered Identicality,
   MarT's Abduction→Mapping→Induction, and Segert et al.'s relaxation are quoted from
   `RULES_AS_SHAPE_DESIGN_SPIKE.md` §15 and `BAICS_WORKSHOP_HARVEST.md` as those
   documents read them. `[unverified]` for all of it. One thing worth carrying, from the
   harvest's own reading: **Segert et al.'s formalism is an untyped adjacency matrix
   with no node-type or edge-type vocabulary at all** — which makes it a poor source for
   a vocabulary design and an interesting counterpoint on exactly the axis §3.3 finds
   `Covers` lacks (its third case study is a deliberately *size-mismatched*, many-to-one
   match). That relationship is my inference, not either document's claim.
9. **The "40" in `SHAPE_AUDIT.md` is a floor claim, not an index.** The document numbers
   its findings by section, not 1-40, and its own §9 item 7 records a measured error rate
   on sweep-sourced findings. §2.3's "roughly a third involve no graph type" is a
   characterisation of what I read, and per `CLAUDE.md`'s retracted-baseline rule a
   characterisation is exactly the thing that should not later be quoted as a count.

---

## 12. Reproduce

Every number in this document comes from one of three places. No build, no agent boot,
no test run is required to check any of it.

```bash
cd /home/matt/ozmadev/ocelot
git log --oneline -1 main            # c439e4c

# §2.1 — no node schema (read every hit; none is one)
grep -rn "schema\|Schema\|required_attr\|declare_node_type\|validate_node" \
  runners/dsl/src/*.rs

# §2.2 — Γ is the edge schema
sed -n '60,90p'   runners/dsl/src/checker.rs      # Type-2 / Type-1
sed -n '69,80p'   runners/dsl/src/grammar.rs      # N ∪ E derived from productions
sed -n '1419,1462p' runners/dsl/src/substrate.rs  # add_node unchecked / add_edge checked
sed -n '2480,2500p' runners/dsl/src/substrate.rs  # add_rule writes no graph node

# §3.3 — the container-semantics table
sed -n '3337,3395p' runners/dsl/src/term.rs       # anti_unify_values
sed -n '3738,3766p' runners/dsl/src/term.rs       # covers_value, all three arms

# §3.1 / §5.1 — the codebook reader and the one existing role declaration
sed -n '239,326p'   runners/dsl/src/shape_decode.rs   # load_parts
sed -n '5093,5122p' runners/dsl/src/shape_decode.rs   # CodebookRegistry

# §8.2 — the existing dedup primitive
sed -n '1693,1740p' runners/dsl/src/rewrite.rs

# §2.3 / §3.4 / §8.2 — the seed-corpus counts (read-only JSON pass)
python3 - <<'PY'
import json, glob, collections
nt=collections.Counter(); minted=collections.Counter(); ops=collections.Counter()
gn=set(); ge=set(); prods=0; rule_seeds=0; seeds=0
for f in glob.glob('seeds/*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    if not isinstance(d, dict): continue
    seeds+=1
    if d.get('rules'): rule_seeds+=1
    for p in (d.get('productions') or []):
        prods+=1
        if isinstance(p, dict):
            for k in ('src','tgt'):
                v=p.get(k)
                t = v.get('type') if isinstance(v,dict) else v
                if t: gn.add(t)          # drop the None a malformed src/tgt would add
            if p.get('edge_type'): ge.add(p['edge_type'])
    for n in (d.get('nodes') or []):
        if isinstance(n,dict) and n.get('type'): nt[n['type']]+=1
    for r in (d.get('rules') or []):
        for e in (r.get('effect') or r.get('effects') or []):
            if isinstance(e,list) and e and str(e[0]).startswith('add_node'):
                ops[e[0]]+=1
                if len(e)>2 and isinstance(e[2],str): minted[e[2]]+=1
print('seeds',seeds,'rule-carrying',rule_seeds,'productions',prods)
print('seed node types',len(nt),'| Gamma N',len(gn),'| Gamma E',len(ge))
print('rule-minted node types',len(minted),'| mint ops',dict(ops))
print('ShapeSignature family:',
      {k:v for k,v in nt.items() if k.startswith('ShapeSignature')})
PY
```

---

## 13. The four sentences I would want a reviewer to take away

1. **This substrate schemas its edges and not its nodes**, and every shape-matching
   defect found this month lives on the unschema'd side — so "what node types should we
   have" has to be re-posed as "what fields, declared where, read by whom."
2. **Today's fixes converged on `{name, signature, support, provenance}` at five grains
   built months apart**, with a documented paper trail between two of them — that is a
   real, undeclared vocabulary, not an ad hoc pile.
3. **They diverged on encoding because they had to**: `Set`, `Dict` and fixed-arity
   `Tuple` each give exactly two of {WILD slots, residual capture, open arity}, and each
   grain paid a different one of the three prices without anyone ever writing the table
   down.
4. **The missing field is `scope`** — observation-scoped datum versus world-model fact —
   and it independently explains the `LatentDimension` dedup bug, the right keying
   discipline per grain, and why a blanket dedup policy would be as wrong as today's
   blanket absence of one.
